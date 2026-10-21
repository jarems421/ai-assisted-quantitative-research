"""Deterministic, read-only graph projection over replay-validated Discovery Lab ledgers and the
historical-memory catalogue.

Nothing here writes to a ledger, a report or the catalogue. Every ledger is loaded through
``Ledger.load`` (hash chain plus full rule replay); a failing ledger refuses the whole build.
Record identities are campaign-namespaced because Discovery Lab IDs are unique only per ledger.
"""
from __future__ import annotations

import copy
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.research.discovery import records as R
from src.research.discovery.ledger import Ledger, State, fold, totals
from src.research.discovery.review import checklist, source_next
from src.research.graph import catalogue as C
from src.research.graph import model as M
from src.research.spec import digest

ROOT = Path(__file__).resolve().parents[3]
LEDGER_ROOT = ROOT / 'docs/strategy/discovery'
ADMITTED = {'memory': ('LIVE', 'RETROSPECTIVE_INSPECTED'), 'prospective': ('LIVE',), 'synthetic': ('SYNTHETIC',)}


class GraphError(ValueError):
    """The graph refuses to build from invalid or ambiguous authoritative inputs."""


def parse_time(value):
    """ISO date (read as the end of that UTC day) or timezone-aware datetime."""
    if value is None:return None
    text = str(value)
    if len(text) == 10:return datetime.fromisoformat(text + 'T23:59:59+00:00')
    parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if parsed.tzinfo is None:raise GraphError('times must carry a timezone')
    return parsed


def norm_locator(locator):
    text = str(locator).strip()
    if '://' in text:
        scheme, rest = text.split('://', 1); host, _, path = rest.partition('/')
        text = f'{scheme.lower()}://{host.lower()}/{path}'
    return text.rstrip('/')


def entity_node_id(identifier, scope):
    """Identified entities join across campaigns; NAME: entities are confined to their own scope."""
    return f'entity:NAME:{scope}/{identifier[5:]}' if identifier.startswith('NAME:') else f'entity:{identifier}'


def identity_status(identifier):
    if identifier.startswith('NAME:'):return 'NAME_ONLY'
    if identifier.startswith('TICKER:'):return 'TICKER_ONLY'
    return 'IDENTIFIED'


class Graph:
    def __init__(self, mode, known_at):
        self.mode, self.known_at = mode, known_at
        self.nodes, self.edges, self.issues, self.inputs, self.excluded = {}, [], [], [], []
        self.adj = defaultdict(list)
        self.catalogue = None
        self.requirements = []

    def node(self, nid, kind, label, **fields):
        if nid in self.nodes:return self.nodes[nid]
        n = {'id': nid, 'kind': kind, 'label': label, 'origin': fields.pop('origin', {'type': 'DERIVED'}),
             'fixture': fields.pop('fixture', None), 'status': fields.pop('status', None), 'reasons': fields.pop('reasons', []),
             'superseded': fields.pop('superseded', False), 'attrs': fields.pop('attrs', {}), 'restrictions': fields.pop('restrictions', [])}
        if fields:raise GraphError(f'unknown node fields {sorted(fields)}')
        self.nodes[nid] = n
        return n

    def edge(self, kind, src, dst, **attrs):
        self.edges.append({'kind': kind, 'src': src, 'dst': dst, 'attrs': attrs})

    def finish(self):
        for n in self.nodes.values():
            for key, value in list(n['attrs'].items()):
                if isinstance(value, set):n['attrs'][key] = sorted(value)
        unique = {}
        for e in self.edges:unique.setdefault((e['kind'], e['src'], e['dst'], digest(e['attrs'])), e)
        self.edges = [unique[k] for k in sorted(unique)]
        for i, e in enumerate(self.edges):
            self.adj[e['src']].append(i); self.adj[e['dst']].append(i)
        self.issues = sorted(self.issues, key=lambda x: digest(x))

    def neighbours(self, nid):
        """(edge, other node id, direction) for every incident edge."""
        for i in self.adj.get(nid, []):
            e = self.edges[i]
            yield e, (e['dst'] if e['src'] == nid else e['src']), ('out' if e['src'] == nid else 'in')

    def degree(self, nid):
        return len(self.adj.get(nid, []))

    def display_status(self, nid):
        n = self.nodes[nid]
        return M.SUPERSEDED if n['superseded'] else n['status']

    def digest(self):
        return digest({'rules': M.RULES, 'mode': self.mode, 'known_at': self.known_at.isoformat() if self.known_at else None,
                       'nodes': [self.nodes[k] for k in sorted(self.nodes)], 'edges': self.edges, 'issues': self.issues,
                       'inputs': self.inputs, 'excluded': self.excluded})


def discover_ledgers(root=LEDGER_ROOT):
    root = Path(root)
    return sorted(root.rglob('*.jsonl')) if root.is_dir() else []


def state_at(full, known_at):
    """Prefix replay: the ledger as it stood when its events up to ``known_at`` had been appended."""
    if known_at is None:return full
    s = State()
    for e in full.events:
        if parse_time(e['recorded_at_utc']) > known_at:break
        fold(e['type'], copy.deepcopy(e['record']), e['derived'], s); s.events.append(e)
    return s if s.campaign else None


def evidence_items(kind, r):
    """(role, evidence item) pairs for every evidence list in a record."""
    if kind == 'source':
        for i, q in enumerate(r['quantities']):
            for ev in q['evidence']:yield f'quantities[{i}]', ev
        for i, q in enumerate(r['identifiers']):
            for ev in q['evidence']:yield f'identifiers[{i}]', ev
        for key in ('history', 'revision_policy', 'publication_clock', 'access'):
            for ev in r[key]['evidence']:yield key, ev
    elif kind == 'observation':
        for ev in r['evidence']:yield 'evidence', ev
        for name in R.CLOCKS:
            for ev in r['clocks'][name]['evidence']:yield f'clocks.{name}', ev
    elif kind == 'relationship':
        for ev in r['evidence']:yield 'evidence', ev
        for ev in r['quantity_transfer']['evidence']:yield 'quantity_transfer', ev
    elif kind == 'candidate':
        for ev in r['outcome']['evidence']:yield 'outcome', ev
        for ev in r['closest_substitute']['evidence']:yield 'closest_substitute', ev
        for dim, j in r['joins'].items():
            for ev in j['evidence']:yield f'joins.{dim}', ev


def add_document(g, ev, holder, role, scope_fixture):
    if ev.get('sha256'):
        nid, identity = f"document:sha256:{ev['sha256']}", 'CONTENT_HASH'
    else:
        nid, identity = f"document:locator:{norm_locator(ev['locator'])}", 'LOCATOR_ONLY'
    d = g.node(nid, 'document', ev['locator'], attrs={'content_identity': identity, 'locators': set(), 'depths': set(),
                                                    'fixtures': set(), 'independence': 'NOT_ASSESSED'})
    d['attrs']['locators'].add(ev['locator']); d['attrs']['depths'].add(ev['depth']); d['attrs']['fixtures'].add(scope_fixture)
    g.edge('CITES', holder, nid, role=role, depth=ev['depth'], evidence_kind=ev['kind'], passage=ev['passage'][:240],
           synthetic=ev['synthetic'], reused_from=ev['reused_from'])


def add_entity(g, e, scope, mention, fixture):
    nid = entity_node_id(e['id'], scope)
    n = g.node(nid, 'entity', e['name'], attrs={'identifier': e['id'], 'identity_status': identity_status(e['id']),
                                              'types': set(), 'names': set(), 'mentions': set(), 'fixtures': set()},
               restrictions=['An entity node proves nothing about any linked financial proposition.'])
    n['attrs']['types'].add(e['type']); n['attrs']['names'].add(e['name']); n['attrs']['mentions'].add(mention)
    n['attrs']['fixtures'].add(fixture)
    if e['id'].startswith('TICKER:'):
        n['restrictions'] = sorted(set(n['restrictions']) | {'A ticker is not a permanent legal-entity identity.'})
    return nid


def tags(text, vocabulary, prefix):
    found, unknown = set(), set()
    for kind, value in M.TAG.findall(text or ''):
        if kind != prefix:continue
        (found if value in vocabulary else unknown).add(value)
    return found, unknown


def project_campaign(g, s, ledger_name, vocabulary, blocker_map, mappings):
    cid, fixture = s.campaign['id'], s.fixture
    seq = {}
    for e in s.events:
        r = e['record']
        key = (e['type'], r.get('id', r.get('candidate_id')), r.get('version'))
        seq[key] = (e['seq'], e['recorded_at_utc'])

    def origin(kind, rid, version):
        number, at = seq.get((kind, rid, version), (None, None))
        return {'type': 'DISCOVERY_LEDGER', 'campaign': cid, 'record': rid, 'version': version, 'ledger': ledger_name,
                'event_seq': number, 'appended_at_utc': at}

    camp = f'campaign:{cid}'
    g.node(camp, 'campaign', s.campaign['title'], fixture=fixture,
           origin={'type': 'DISCOVERY_LEDGER', 'campaign': cid, 'ledger': ledger_name, 'event_seq': 0,
                   'appended_at_utc': s.events[0]['recorded_at_utc']},
           attrs={'method': s.campaign['method'], 'question': s.campaign['question'], 'authority': s.campaign['authority'],
                  'acquisition_authorized': s.campaign['acquisition_authorized'], 'budget': s.campaign['budget'],
                  'effort': totals(s.efforts), 'events': len(s.events)})
    nid = lambda prefix, rid, v: f'{prefix}:{cid}/{rid}@{v}'

    for rid, versions in s.versions['source'].items():
        for r in versions:
            n = nid('source', rid, r['version'])
            rung, why = source_next(r)
            g.node(n, 'source', r['name'], fixture=fixture, origin=origin('source', rid, r['version']), superseded=r is not versions[-1],
                   attrs={'publisher': r['publisher'], 'locator': r['locator'], 'access': r['access']['status'], 'revision_reason': r['revision_reason'],
                          'quantities': [{k: q[k] for k in ('field', 'meaning', 'units', 'denominator', 'depth')} for q in r['quantities']],
                          'omissions': r['omissions'], 'misleading_proxies': r['misleading_proxies'], 'next_rung': rung, 'next_why': why},
                   restrictions=['A source passport is a discovery aid, not an evidence level.'])
            g.edge('CONTAINS', camp, n)
            for role, ev in evidence_items('source', r):add_document(g, ev, n, role, fixture)
            if r['version'] > 1:g.edge('SUPERSEDES', n, nid('source', rid, r['version'] - 1))

    for rid, versions in s.versions['observation'].items():
        for o in versions:
            n = nid('observation', rid, o['version'])
            reasons = []
            if o['as_of_status'] == 'CONTRADICTED':status = M.CONTRADICTED
            elif o['depth'] == 'VERIFIED_ORIGINAL_FIELD':status = M.ORIGINAL_FIELD_OBSERVED
            elif o['depth'] == 'VERIFIED_ORIGINAL_RECORD':status, reasons = M.ORIGINAL_DOCUMENT_REFERENCED, ['DOCUMENT_SEEN_FIELD_NOT_VERIFIED']
            else:status, reasons = M.RECORDED_UNVERIFIED, [M.DEPTH_REASON[o['depth']]]
            text = ' '.join([o['statement'], o['why_informative'], *o['missing_evidence']])
            measures, unknown = tags(text, vocabulary, 'MEASURES')
            for t in sorted(unknown):g.issues.append({'code': 'UNKNOWN_TAG', 'node': n, 'tag': f'MEASURES:{t}'})
            fp = o['clocks']['first_public']
            g.node(n, 'observation', o['statement'], fixture=fixture, origin=origin('observation', rid, o['version']), status=status,
                   reasons=reasons, superseded=o is not versions[-1],
                   attrs={'kind': o['kind'], 'value': o['value'], 'units': o['units'], 'denominator': o['denominator'], 'depth': o['depth'],
                          'as_of_status': o['as_of_status'], 'clocks': {k: {'value': o['clocks'][k]['value'], 'basis': o['clocks'][k]['basis']}
                                                                       for k in R.CLOCKS},
                          'first_public_certified': fp['value'] != R.UNKNOWN, 'outcome_independent': o['outcome_independent'],
                          'why_informative': o['why_informative'], 'missing_evidence': o['missing_evidence'], 'source_id': o['source_id'],
                          'measures_tags': sorted(measures), 'unknown_tags': sorted(unknown), 'revision_reason': o['revision_reason']},
                   restrictions=['An observation records what a source shows; it is not a financial consequence.'])
            g.edge('CONTAINS', camp, n)
            src = s.latest('source', o['source_id'])
            g.edge('OBSERVED_IN', n, nid('source', o['source_id'], src['version']))
            g.edge('DESCRIBES', n, add_entity(g, o['entity'], cid, n, fixture))
            for role, ev in evidence_items('observation', o):add_document(g, ev, n, role, fixture)
            for t in sorted(measures):g.edge('MAY_MEASURE', n, f'requirement:{t}', basis='AUTHOR_TAG_CANDIDATE')
            if o['version'] > 1:g.edge('SUPERSEDES', n, nid('observation', rid, o['version'] - 1))

    for rid, versions in s.versions['relationship'].items():
        for r in versions:
            n = nid('relationship', rid, r['version'])
            reasons = []
            if r['status'] == 'CONTRADICTED':status = M.CONTRADICTED
            elif r['status'] == 'VERIFIED' and r['basis'] == 'DOCUMENTED':status = M.DOCUMENTED_RELATIONSHIP
            else:
                status = M.RECORDED_UNVERIFIED
                reasons = [{'NAME_MATCH_ONLY': 'NAME_MATCH_ONLY', 'INFERRED': 'INFERRED_ONLY'}.get(r['basis'], 'UNVERIFIED')]
            q = r['quantity_transfer']
            allocation = {'VERIFIED': 'VERIFIED_ALLOCATION', 'NOT_APPLICABLE': 'NOT_APPLICABLE'}.get(q['status'], 'ALLOCATION_UNVERIFIED')
            label = f"{r['source_entity']['name']} -[{r['type']}]- {r['target_entity']['name']}"
            g.node(n, 'relationship', label, fixture=fixture, origin=origin('relationship', rid, r['version']), status=status, reasons=reasons,
                   superseded=r is not versions[-1],
                   attrs={'type': r['type'], 'direction': r['direction'], 'basis': r['basis'], 'record_status': r['status'],
                          'period': r['period'], 'scope': r['scope'], 'allocation_status': allocation, 'allocation_method': q['method'],
                          'allocation_note': q['note'], 'limitations': r['limitations'], 'alternatives': r['alternatives'],
                          'revision_reason': r['revision_reason']},
                   restrictions=['A documented relationship is a connection, not a quantified or allocated financial exposure.'])
            g.edge('CONTAINS', camp, n)
            g.edge('SUBJECT', n, add_entity(g, r['source_entity'], cid, n, fixture))
            g.edge('OBJECT', n, add_entity(g, r['target_entity'], cid, n, fixture))
            for role, ev in evidence_items('relationship', r):add_document(g, ev, n, role, fixture)
            if r['version'] > 1:g.edge('SUPERSEDES', n, nid('relationship', rid, r['version'] - 1))

    pending = []
    for rid, versions in s.versions['candidate'].items():
        for c in versions:
            n = nid('claim', rid, c['version'])
            d = s.derived[('candidate', rid, c['version'])]
            freeze = s.frozen(rid, c['version'])
            ck = checklist(s, rid, c['version'])
            reviews = [r for r in s.reviews if r['candidate_id'] == rid and r['version'] == c['version']]
            dispositions = [x for x in s.dispositions if x['candidate_id'] == rid and x['version'] == c['version']]
            g.node(n, 'claim', c['predictor']['quantity'], fixture=fixture, origin=origin('candidate', rid, c['version']),
                   status='HYPOTHESIS_RECORDED', superseded=c is not versions[-1],
                   attrs={'method': c['method'], 'population': c['population'], 'mechanism': c['mechanism'],
                          'predictor': c['predictor'], 'exposure': {k: c['exposure'][k] for k in ('claim_basis', 'allocation_required', 'gross', 'net', 'materiality')},
                          'company': c['exposure']['company']['id'], 'outcome': {k: c['outcome'][k] for k in ('quantity', 'units', 'route', 'status')},
                          'revision_kind': d['revision_kind'], 'claim_class': d['claim_class'], 'post_outcome': d['post_outcome'],
                          'revision_reason': c['revision_reason'], 'frozen': bool(freeze),
                          'freeze_references': freeze['references'] if freeze else None,
                          'missing_variables': c['missing_variables'], 'falsification': c['falsification'],
                          'closest_substitute': {'description': c['closest_substitute']['description'], 'checked': c['closest_substitute']['checked']},
                          'selection': c['selection'], 'recommendation': c['recommendation'],
                          'blockers': {k: v['blockers'] for k, v in ck['requirements'].items()},
                          'human_m': {k: v['human_judgment'] for k, v in ck['requirements'].items()}, 'human_h': ck['h_human_judgment'],
                          'h_gaps': ck['h_gaps'], 'gaps': ck['gaps'], 'software_certifies_M': False,
                          'reviews': [{'id': r['id'], 'kind': r['kind'], 'role': r['role'], 'reviewer': r['reviewer']['kind'],
                                       'result': (r['judgments'].get('verdict') or r['judgments'].get('judgment')
                                                  or {k: j['judgment'] for k, j in r['judgments'].items()}),
                                       'not_checked': sorted({x['category'] for x in r['not_checked']})} for r in reviews],
                          'dispositions': [{'id': x['id'], 'decision': x['decision'], 'reason_type': x['reason_type'], 'reason': x['reason'],
                                            'scope': x['scope'], 'decided_by': x['decided_by']['kind'],
                                            'verify': x['verify']} for x in dispositions],
                          'efforts': [e['id'] for e in s.efforts if e['candidate_id'] == rid]},
                   restrictions=['A claim is a hypothesis record; the graph never decides M, H or a disposition.'])
            g.edge('CONTAINS', camp, n)
            refs = freeze['references'] if freeze else {}
            for oid in c['predictor']['observation_ids']:
                g.edge('PREDICTS_WITH', n, nid('observation', oid, refs.get(oid, s.latest('observation', oid)['version'])))
            for oid in c['outcome']['derived_from_observations']:
                g.edge('OUTCOME_FROM', n, nid('observation', oid, refs.get(oid, s.latest('observation', oid)['version'])))
            for rel in c['exposure']['relationship_ids']:
                g.edge('RELIES_ON', n, nid('relationship', rel, refs.get(rel, s.latest('relationship', rel)['version'])))
            g.edge('EXPOSES', n, add_entity(g, c['exposure']['company'], cid, n, fixture))
            for role, ev in evidence_items('candidate', c):add_document(g, ev, n, role, fixture)
            if c['version'] > 1:g.edge('SUPERSEDES', n, nid('claim', rid, c['version'] - 1))
            for req, codes in ck['requirements'].items():
                for code in codes['blockers']:
                    head = code.split('=')[0]
                    base = head.split(':')[0]
                    g.node(f'blocker:{base}', 'blocker', base, restrictions=['A shared blocker is reusable knowledge, not an economic relationship.'])
                    g.edge('BLOCKED_BY', n, f'blocker:{base}', requirement=req, detail=code)
                    mapped = blocker_map.get(head) or blocker_map.get(base)
                    if mapped:g.edge('REQUIRES', n, f'requirement:{mapped}', basis='MECHANICAL_BLOCKER', detail=code)
            found, unknown = tags(' '.join(c['missing_variables']), vocabulary, 'REQ')
            for t in sorted(found):
                text = next(v for v in c['missing_variables'] if f'[REQ:{t}]' in v)
                g.edge('REQUIRES', n, f'requirement:{t}', basis='AUTHOR_TAG_CANDIDATE', detail=text)
            for t in sorted(unknown):g.issues.append({'code': 'UNKNOWN_TAG', 'node': n, 'tag': f'REQ:{t}'})
            for m in mappings:
                if m['claim'] == f"{cid}/{rid}@{c['version']}":
                    g.edge('REQUIRES', n, f"requirement:{m['requirement']}", basis='CURATED_MAPPING', detail=m['note'])
            for ref in c['selection']['prior_related_claims']:pending.append((n, cid, ref))
    return pending


def resolve_related(g, pending):
    for n, cid, ref in pending:
        qualified = ref if '/' in ref else f'{cid}/{ref}'
        matches = sorted(k for k, v in g.nodes.items() if v['kind'] == 'claim' and k.startswith(f'claim:{qualified}@') and not v['superseded'])
        if matches:g.edge('RELATED_CLAIM', n, matches[-1], reference=ref)
        else:g.issues.append({'code': 'UNRESOLVED_RELATED_CLAIM', 'node': n, 'reference': ref})


def project_history(g, cat):
    recorded = cat['recorded_at_utc']
    for inv in cat['investigations']:
        iid = inv['id']; hid = f'history:{iid}'; citation = cat['_citation_status'][iid]
        origin = {'type': 'HISTORICAL_CATALOGUE', 'investigation': iid, 'report': inv['report'], 'catalogue_recorded_at_utc': recorded}
        restrictions = ['Historical conclusion cited verbatim; not a Discovery Lab disposition, review or freeze.',
                        'Known to the graph only from catalogue recording time, not from the original investigation date.']
        if citation != 'CURRENT':restrictions.append(f'CITATION {citation}: re-read the cited report before relying on this memory.')
        g.node(hid, 'history', inv['title'], fixture='HISTORICAL_MEMORY', origin=origin, status=M.HISTORICAL_CONCLUSION,
               attrs={'family': inv['family'], 'verdict': inv['verdict'], 'historical_closure': inv['historical_closure'],
                      'citation_status': citation, 'related': inv['related'], 'mapping_review': cat['mapping_review']},
               restrictions=restrictions)
        for c in inv['claims']:
            cn = f'{hid}/claim-{c["id"]}'
            g.node(cn, 'history_claim', c['object'], fixture='HISTORICAL_MEMORY', origin=dict(origin, claim=c['id']), status=M.HISTORICAL_CONCLUSION,
                   attrs={k: c[k] for k in ('version', 'financial_basis', 'reformulates', 'post_outcome', 'counts_as_original', 'recorded_status')},
                   restrictions=restrictions[:1] + (['Reformulated after observation; never an original-claim success.'] if c['reformulates'] else []))
            g.edge('RECORDS', hid, cn)
            if c['reformulates']:g.edge('REFORMULATES', cn, f"{hid}/claim-{c['reformulates']}")
        for f in inv['findings']:
            fn = f'{hid}/{f["id"]}'
            g.node(fn, 'history_finding', f['text'], fixture='HISTORICAL_MEMORY', origin=dict(origin, finding=f['id']), status=M.HISTORICAL_CONCLUSION,
                   attrs={'finding_kind': f['kind'], 'citation': f['citation'], 'requirement': f['requirement'], 'claim': f['claim']},
                   restrictions=['A recorded gap is bounded to its investigation; it is not proof the quantity does not exist.'])
            g.edge('HAS_FINDING', f"{hid}/claim-{f['claim']}" if f['claim'] else hid, fn)
            if f['requirement']:
                g.edge('REQUIRES', fn, f"requirement:{f['requirement']}", basis='CURATED_HISTORICAL_MAPPING', detail=f['text'])
                if f['claim']:g.edge('REQUIRES', f"{hid}/claim-{f['claim']}", f"requirement:{f['requirement']}",
                                     basis='CURATED_HISTORICAL_MAPPING', detail=f['text'])
        for e in inv['entities']:
            en = add_entity(g, e, iid, hid, 'HISTORICAL_MEMORY')
            g.edge('CONCERNS', hid, en, identity_basis=e['identity_basis'])
        for d in inv['documents']:
            ev = {'sha256': d['sha256'], 'locator': d['locator'], 'depth': 'VERIFIED_ORIGINAL_RECORD' if d['http_status'] == 200 else 'ACCESS_BLOCKED',
                  'kind': 'ORIGINAL_DOCUMENT', 'passage': d['role'], 'synthetic': False, 'reused_from': d['receipt']}
            add_document(g, ev, hid, 'historical_receipt', 'HISTORICAL_MEMORY')
            g.nodes[f"document:sha256:{d['sha256']}"]['attrs'].setdefault('receipt_status', set()).add(
                f"{d['http_status']}{'' if d['complete'] else ' INCOMPLETE_PREFIX'}")


def derive_issues(g):
    for nid, n in g.nodes.items():
        if n['kind'] == 'entity' and len(n['attrs']['types']) > 1:
            g.issues.append({'code': 'ENTITY_TYPE_CONFLICT', 'node': nid, 'types': sorted(n['attrs']['types'])})
    by_locator = defaultdict(set)
    for nid, n in g.nodes.items():
        if n['kind'] == 'document' and n['attrs']['content_identity'] == 'CONTENT_HASH':
            for loc in n['attrs']['locators']:by_locator[norm_locator(loc)].add(nid)
    for loc, docs in sorted(by_locator.items()):
        if len(docs) > 1:g.issues.append({'code': 'SOURCE_HASH_CHANGED_AT_LOCATOR', 'locator': loc, 'documents': sorted(docs)})
    entities = sorted((nid, n) for nid, n in g.nodes.items() if n['kind'] == 'entity')
    keys = {nid: {frozenset(M.tokens(name, 2)) for name in n['attrs']['names']} for nid, n in entities}
    for i, (a, _) in enumerate(entities):
        for b, _ in entities[i + 1:]:
            if any(x and y and (x <= y or y <= x) for x in keys[a] for y in keys[b]):
                g.issues.append({'code': 'IDENTITY_QUESTION', 'entities': [a, b],
                                 'note': 'Similar names, different identifiers: never merged; establish identity from originals.'})


def build(ledgers=None, catalogue_path=C.CATALOGUE_PATH, mode='memory', known_at=None, with_memory=True):
    """Build the projection. Raises GraphError on any invalid authoritative input."""
    if mode not in M.MODES:raise GraphError(f'mode must be one of {M.MODES}')
    cutoff = parse_time(known_at) if known_at else None
    g = Graph(mode, cutoff)
    cat = None
    if catalogue_path is not None:
        try:cat, issues = C.load(catalogue_path)
        except C.CatalogueError as error:raise GraphError(f'catalogue refused: {error}') from error
        g.issues += issues; g.requirements = C.requirement_ids(cat)
    vocabulary = set(g.requirements)
    for r in (cat['requirements'] if cat else []):
        g.node(f"requirement:{r['id']}", 'requirement', r['label'], attrs={'definition': r['definition'], 'does_not_mean': r['does_not_mean']},
               restrictions=['A requirement match is a retrieval aid; it never shows that a requirement is met.'])
    seen, pending = {}, []
    for path in (discover_ledgers() if ledgers is None else [Path(p) for p in ledgers]):
        try:full = Ledger(path).load()
        except ValueError as error:raise GraphError(f'{path.name}: ledger failed replay, refusing build: {error}') from error
        cid, fixture = full.campaign['id'], full.fixture
        if fixture not in ADMITTED[mode]:
            g.excluded.append({'ledger': path.name, 'campaign': cid, 'reason': f'{fixture} records are not admitted in {mode} mode'}); continue
        if cid in seen:raise GraphError(f'duplicate campaign id {cid} in {seen[cid]} and {path.name}')
        seen[cid] = path.name
        s = state_at(full, cutoff)
        if s is None:
            g.excluded.append({'ledger': path.name, 'campaign': cid, 'reason': 'campaign not yet recorded at known-at time'}); continue
        g.inputs.append({'ledger': path.name, 'campaign': cid, 'fixture': fixture, 'events_used': len(s.events),
                         'events_total': len(full.events), 'head_hash': s.events[-1]['hash']})
        pending += project_campaign(g, s, path.name, vocabulary, cat['blocker_requirements'] if cat else {}, cat['claim_mappings'] if cat else [])
    resolve_related(g, pending)
    if cat:
        use = mode == 'memory' or (mode == 'synthetic' and with_memory)
        if use and cutoff and parse_time(cat['recorded_at_utc']) > cutoff:
            g.excluded.append({'catalogue': str(Path(catalogue_path).name), 'reason': 'catalogue recorded after known-at time'}); use = False
        if mode == 'prospective':g.excluded.append({'catalogue': str(Path(catalogue_path).name), 'reason': 'historical memory is not admitted in prospective mode'})
        if use:
            project_history(g, cat); g.catalogue = {'recorded_at_utc': cat['recorded_at_utc'], 'investigations': len(cat['investigations'])}
    derive_issues(g)
    g.finish()
    return g
