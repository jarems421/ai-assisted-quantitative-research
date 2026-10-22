"""Graph research operators. Each returns a structured, explainable result; none writes anything.

Every suggestion is SUGGESTION_ONLY with an explicit match basis from model.MATCH_STRENGTH, the
evidence it rests on, what remains unverified, and the statement that no new work is authorised.
"""
from __future__ import annotations

from collections import defaultdict, deque

from src.research.discovery import records as R
from src.research.graph import connections as K
from src.research.graph import model as M
from src.research.graph import rules as G
from src.research.spec import digest

JOINABLE = ('IDENTIFIED', 'ARCHIVE_PATH_IDENTIFIER')
ARCHIVE_CAVEAT = 'that the archive-path CIK in historical memory is the same economic entity (listing, securities and group structure not established)'
AUTHORITY = 'NONE: suggestion only. Earlier dispositions, historical verdicts and source stops stand; any work needs separate authority.'
CLAIM_EDGES = ('PREDICTS_WITH', 'OUTCOME_FROM', 'RELIES_ON', 'EXPOSES')
STRENGTH = {b: i for i, b in enumerate(M.MATCH_STRENGTH)}
# Timing and source-qualification provenance (receipts, publication records, version notes) is not economic content;
# two records sharing a retrieval receipt are not thereby connected.
NON_CONTENT_ROLES = ('history', 'revision_policy', 'publication_clock', 'access')


def content_citation(edge):
    role = edge['attrs'].get('role', '')
    return edge['kind'] == 'CITES' and not role.startswith('clocks.') and role not in NON_CONTENT_ROLES


def reused_record_citation(*edges):
    """Evidence copied from another ledger record (reused_from names a record, e.g. FROZEN_PACKET/OBS-P-1), as opposed to a
    repository receipt path. Two citations of the same copied evidence are one record restated, not a document match."""
    return any((e['attrs'].get('reused_from') or '') and not str(e['attrs'].get('reused_from')).startswith('docs/') for e in edges)


def doc_basis(identity, *edges):
    if reused_record_citation(*edges):return 'REUSED_CITATION'
    return 'EXACT_DOCUMENT_HASH' if identity == 'CONTENT_HASH' else 'SAME_LOCATOR_ONLY'


class NotFound(ValueError):
    pass


def result(g, operator, token, view, **fields):
    out = {'banner': M.BANNER, 'operator': operator, 'input': token, 'mode': g.mode,
           'known_at': g.known_at.isoformat() if g.known_at else None, 'view': view.describe() if view else None,
           'results': [], 'abstentions': [], 'notes': []}
    out.update(fields)
    return out


def abstain(code, reason):
    return {'code': code, 'reason': reason}


def resolve(g, token):
    """Exact node id, or an unambiguous short form (DLC-X, OBS-1, OBS-1@2, HIST-F01, CIK:..., REQ_...)."""
    if token in g.nodes:return token
    for prefix in ('campaign:', 'history:', 'entity:', 'requirement:', 'blocker:'):
        if prefix + token in g.nodes:return prefix + token
    version = None
    if '@' in token:token, version = token.rsplit('@', 1)
    hits = [k for k, n in g.nodes.items() if ('/' + token + '@' in k or k.split(':', 1)[-1].startswith(token + '@'))
            and (k.endswith('@' + version) if version else not n['superseded'])]
    if len(hits) == 1:return hits[0]
    if not hits:raise NotFound(f'no node matches {token!r}; try search')
    raise NotFound(f'{token!r} is ambiguous: {sorted(hits)[:8]}; use a full node id')


def owner(g, nid):
    o = g.nodes[nid]['origin']
    if o.get('campaign'):return 'campaign:' + o['campaign']
    if o.get('investigation'):return 'history:' + o['investigation']
    return None


def linked(g, nid, kinds, direction=None):
    return [(e, o) for e, o, d in g.neighbours(nid) if e['kind'] in kinds and (direction is None or d == direction)]


def claims_using(g, nid):
    """Claim nodes (Discovery Lab or historical) that use or concern a record or entity."""
    if g.nodes[nid]['kind'] == 'history':return sorted(c for _, c in linked(g, nid, ('RECORDS',), 'out'))
    out = {o for e, o in linked(g, nid, CLAIM_EDGES, 'in') if g.nodes[o]['kind'] == 'claim'}
    for e, o in linked(g, nid, ('CONCERNS', 'CITES'), 'in'):
        if g.nodes[o]['kind'] == 'history':out |= {c for _, c in linked(g, o, ('RECORDS',), 'out')}
    return sorted(out)


def claim_status(g, nid):
    n = g.nodes[nid]
    if n['kind'] == 'claim':
        d = n['attrs']['dispositions']
        return d[-1]['decision'] if d else 'NO_DISPOSITION'
    hist = nid.split('/claim-')[0]
    return g.nodes[hist]['attrs']['verdict']['text'] if hist in g.nodes else 'UNKNOWN'


def is_open(g, nid):
    n = g.nodes[nid]
    return n['kind'] == 'claim' and not n['superseded'] and claim_status(g, nid) not in ('REJECT',)


def entity_of(g, obs):
    hits = [o for _, o in linked(g, obs, ('DESCRIBES',), 'out')]
    return hits[0] if hits else None


def records_of(g, nid):
    """Record nodes covered by an input: a campaign's contents, an investigation's memory, or one record."""
    n = g.nodes[nid]
    if n['kind'] == 'campaign':return sorted(o for _, o in linked(g, nid, ('CONTAINS',), 'out') if not g.nodes[o]['superseded'])
    if n['kind'] == 'history':
        out = {nid} | {o for _, o in linked(g, nid, ('RECORDS', 'HAS_FINDING'), 'out')}
        return sorted(out | {f for c in list(out) for _, f in linked(g, c, ('HAS_FINDING',), 'out')})
    return [nid]


def suggestion(operator, target, match, bases, **details):
    bases = sorted(set(bases), key=lambda b: STRENGTH.get(b, 99))
    sid = 'SUG-' + digest({'operator': operator, 'target': target, 'match': match, 'bases': bases})[:12]
    out = {'suggestion_id': sid, 'status': M.SUGGESTION_ONLY, 'target': target, 'match': match, 'match_bases': bases,
           'strength': bases[0] if bases else 'NONE'}
    out.update(details); out['authority'] = AUTHORITY
    return out


def keyword_overlap(g, a, b):
    return sorted(M.keywords(g.nodes[a]['label']) & M.keywords(g.nodes[b]['label']))


# -- basic inspection -----------------------------------------------------------------------------

SEARCH_FIELDS = ('statement', 'why_informative', 'mechanism', 'population', 'identifier', 'names', 'units', 'family', 'finding_kind',
                 'definition', 'locators', 'quantity')


def searchable(n):
    parts = [n['id'], n['label']]
    for k, v in n['attrs'].items():
        if k in SEARCH_FIELDS or k in ('verdict', 'citation', 'predictor', 'outcome'):parts.append(str(v))
    return ' '.join(parts).lower()


def search(g, text, view, limit=M.MAX_NODES):
    terms = [t for t in M.tokens(text, 2)] or [text.lower()]
    out = result(g, 'search', text, view)
    order = {k: i for i, k in enumerate(M.KINDS)}
    for nid in sorted(g.nodes, key=lambda k: (order.get(g.nodes[k]['kind'], 99), k)):
        n = g.nodes[nid]
        if all(t in searchable(n) for t in terms) and G.visible(g, nid, view)[0]:
            out['results'].append({'node': nid, 'kind': n['kind'], 'label': n['label'], 'status': g.display_status(nid),
                                   'fixture': n['fixture'], 'origin': n['origin'].get('campaign') or n['origin'].get('investigation')})
    if len(out['results']) > limit:
        out['notes'].append(f"{len(out['results'])} matches; showing {limit}. Refine the query."); out['results'] = out['results'][:limit]
    if not out['results']:out['abstentions'].append(abstain('NO_USEFUL_SUGGESTION', 'no visible node contains every query term'))
    return out


def show(g, token, view):
    nid = resolve(g, token); n = g.nodes[nid]
    out = result(g, 'show', nid, view)
    edges = defaultdict(list)
    for e, other, d in g.neighbours(nid):edges[f"{e['kind']}:{d}"].append(other)
    shown, hidden = {}, 0
    for key, others in sorted(edges.items()):
        shown[key] = sorted(others)[:M.MAX_NODES]; hidden += max(0, len(others) - M.MAX_NODES)
    out['results'].append({'node': nid, 'kind': n['kind'], 'label': n['label'], 'status': g.display_status(nid), 'reasons': n['reasons'],
                           'fixture': n['fixture'], 'origin': n['origin'], 'attrs': n['attrs'], 'restrictions': n['restrictions'],
                           'evidence': G.evidence_refs(g, nid, clocks=True), 'edges': shown, 'degree': g.degree(nid)})
    if hidden:out['notes'].append(f'{hidden} further incident edges not listed (high-degree node).')
    visible, reason = G.visible(g, nid, view)
    if not visible:out['notes'].append(f'This node is hidden by the current view: {reason}.')
    return out


def neighbourhood(g, token, view, semantic=1, limit=M.MAX_NODES):
    start = resolve(g, token); semantic = max(0, min(int(semantic), M.MAX_SEMANTIC_HOPS))
    out = result(g, 'neighbourhood', start, view)
    seen, edges, collapsed = {start: 0}, set(), []
    queue = deque([(start, 0, 0)])
    while queue:
        node, depth, hops = queue.popleft()
        if node != start and not G.bridge_allowed(g, node, (start,)):
            collapsed.append({'node': node, 'degree': g.degree(node), 'reason': 'HUB_SUPPRESSED' if g.degree(node) > M.HUB_DEGREE
                              else 'NOT_A_BRIDGE (' + g.nodes[node]['kind'] + ')'}); continue
        if depth >= 2 * semantic + 2:continue
        for i in g.adj.get(node, []):
            e = g.edges[i]; other = e['dst'] if e['src'] == node else e['src']
            if not G.visible(g, other, view)[0]:continue
            more = hops + int(g.nodes[other]['kind'] == 'relationship')
            if more > semantic:continue
            if other not in seen:
                if len(seen) >= limit:out['notes'].append(f'Truncated at {limit} nodes.'); queue.clear(); break
                seen[other] = depth + 1; queue.append((other, depth + 1, more))
            edges.add(i)
    out['results'].append({'nodes': sorted(seen), 'edges': sorted(edges), 'collapsed': sorted(collapsed, key=lambda c: c['node'])})
    return out


def trace(g, token, view=None):
    nid = resolve(g, token); n = g.nodes[nid]
    out = result(g, 'trace', nid, view)
    if n['kind'] in ('history', 'history_claim', 'history_finding'):
        hist = nid.split('/')[0] if n['kind'] != 'history' else nid
        h = g.nodes[hist]; claims = [o for _, o in linked(g, hist, ('RECORDS',), 'out')]
        out['results'].append({'investigation': hist, 'verdict': h['attrs']['verdict'], 'citation_status': h['attrs']['citation_status'],
                               'historical_closure': h['attrs']['historical_closure'],
                               'claims': [{'node': c, 'object': g.nodes[c]['label'], **g.nodes[c]['attrs'],
                                           'reformulation_of': [o for _, o in linked(g, c, ('REFORMULATES',), 'out')],
                                           'findings': [{'node': f, 'kind': g.nodes[f]['attrs']['finding_kind'], 'text': g.nodes[f]['label'],
                                                         'requirement': g.nodes[f]['attrs']['requirement'], 'citation': g.nodes[f]['attrs']['citation']}
                                                        for _, f in sorted(linked(g, c, ('HAS_FINDING',), 'out'), key=lambda x: x[1])]}
                                          for c in sorted(claims)],
                               'investigation_findings': [o for _, o in linked(g, hist, ('HAS_FINDING',), 'out')],
                               'entities': [{'node': o, 'identity': e['attrs']['identity_basis']} for e, o in linked(g, hist, ('CONCERNS',), 'out')],
                               'documents': [o for _, o in linked(g, hist, ('CITES',), 'out')], 'restrictions': h['restrictions']})
        return out
    if n['kind'] != 'claim':raise NotFound('trace takes a claim or historical investigation')
    lineage = [nid]
    while True:
        prev = [o for _, o in linked(g, lineage[0], ('SUPERSEDES',), 'out')]
        if not prev:break
        lineage.insert(0, prev[0])
    while True:
        nxt = [o for _, o in linked(g, lineage[-1], ('SUPERSEDES',), 'in')]
        if not nxt:break
        lineage.append(nxt[0])
    for c in lineage:
        a = g.nodes[c]['attrs']
        out['results'].append({
            'claim': c, 'superseded': g.nodes[c]['superseded'], 'revision_kind': a['revision_kind'], 'claim_class': a['claim_class'],
            'post_outcome': a['post_outcome'], 'revision_reason': a['revision_reason'], 'frozen': a['frozen'],
            'predictor': [{'node': o, 'status': g.display_status(o), 'source': [s for _, s in linked(g, o, ('OBSERVED_IN',), 'out')],
                           'documents': [d['document'] for d in G.evidence_refs(g, o) if 'document' in d]}
                          for _, o in linked(g, c, ('PREDICTS_WITH',), 'out')],
            'outcome': a['outcome'], 'outcome_records': [o for _, o in linked(g, c, ('OUTCOME_FROM',), 'out')],
            'relationships': [{'node': o, 'status': g.display_status(o), 'allocation': g.nodes[o]['attrs']['allocation_status'],
                               'period': g.nodes[o]['attrs']['period']} for _, o in linked(g, c, ('RELIES_ON',), 'out')],
            'company': a['company'], 'exposure': a['exposure'], 'blockers': {k: v for k, v in a['blockers'].items() if v},
            'human_m': a['human_m'], 'human_h': a['human_h'], 'reviews': a['reviews'], 'dispositions': a['dispositions'],
            'related_claims': sorted({o for _, o in linked(g, c, ('RELATED_CLAIM',))})})
    return out


# -- discovery operators --------------------------------------------------------------------------

def shared(g, token, view):
    """Operator A: other campaigns/investigations citing the same document hash or stable entity."""
    nid = resolve(g, token); out = result(g, 'shared', nid, view)
    inputs = records_of(g, nid); scope = {owner(g, x) for x in inputs} | {nid}
    groups = defaultdict(lambda: {'matches': [], 'kinds_there': set()})
    for x in inputs:
        for e, doc in linked(g, x, ('CITES',), 'out'):
            if not content_citation(e):continue
            identity = g.nodes[doc]['attrs']['content_identity']
            for e2, other in linked(g, doc, ('CITES',), 'in'):
                o = owner(g, other)
                if o in scope or not content_citation(e2) or not G.visible(g, other, view)[0]:continue
                groups[o]['matches'].append({'basis': doc_basis(identity, e, e2), 'via': doc, 'here': x, 'there': other})
        for e, ent in linked(g, x, ('DESCRIBES', 'SUBJECT', 'OBJECT', 'EXPOSES', 'CONCERNS'), 'out'):
            if g.nodes[ent]['attrs']['identity_status'] not in JOINABLE:continue
            for e2, other in linked(g, ent, ('DESCRIBES', 'SUBJECT', 'OBJECT', 'EXPOSES', 'CONCERNS'), 'in'):
                o = owner(g, other)
                if o in scope or not G.visible(g, other, view)[0]:continue
                groups[o]['matches'].append({'basis': 'EXACT_ENTITY_ID', 'via': ent, 'here': x, 'there': other,
                                             'hub': g.degree(ent) > M.HUB_DEGREE,
                                             'identity': 'ARCHIVE_PATH_UNCORROBORATED' if 'SEC_ARCHIVE_PATH_IN_RECORDED_LOCATOR' in
                                             (e['attrs'].get('identity_basis'), e2['attrs'].get('identity_basis')) else g.nodes[ent]['attrs']['identity_status']})
                groups[o]['kinds_there'].add(g.nodes[other]['kind'])
    here_kinds = {g.nodes[x]['kind'] for x in inputs}
    for o in sorted(groups):
        m = groups[o]; bases = [x['basis'] for x in m['matches']]
        entity_matches = [x for x in m['matches'] if x['basis'] == 'EXACT_ENTITY_ID' and not x.get('hub')]
        if not entity_matches:classification = 'SAME_SOURCE_REUSE' if bases else 'NONE'
        elif m['kinds_there'] - here_kinds & {'relationship', 'observation'}:classification = 'POTENTIALLY_COMPLEMENTARY'
        else:classification = 'SHARED_ENTITY_ONLY'
        others = sorted({x['there'] for x in m['matches']})
        claims = sorted({c for x in others for c in claims_using(g, x)} | ({c for c in others if g.nodes[c]['kind'] in ('claim', 'history_claim')}))
        best = sorted(m['matches'], key=lambda x: (STRENGTH.get(x['basis'], 99), x['there']))[0]
        out['results'].append(K.annotate(g, suggestion('shared', nid, o, bases, classification=classification,
                                         matches=sorted(m['matches'], key=lambda x: (STRENGTH.get(x['basis'], 99), x['there'])),
                                         scope_and_period={x: g.nodes[x]['attrs'].get('period') or g.nodes[x]['attrs'].get('clocks', {}).get('economic_occurrence')
                                                           for x in others if g.nodes[x]['kind'] in ('relationship', 'observation')},
                                         dispositions={c: claim_status(g, c) for c in claims},
                                         independence='SOURCE_INDEPENDENCE_UNKNOWN: shared or different hashes are not certified independent'),
                                          best['here'], best['there'], bases, [best['via']]))
    out['results'].sort(key=lambda r: K.order_key(r, STRENGTH))
    out['results'] = out['results'][:M.MAX_SUGGESTIONS]
    out['notes'].append('A shared company alone is not a novel economic discovery; reuse of one source is not corroboration.')
    if not out['results']:out['abstentions'].append(abstain('NO_USEFUL_SUGGESTION', 'no other campaign or investigation shares a document hash or identified entity'))
    return K.summarise(out)


def similar_entities(g, ent):
    return sorted({x for i in g.issues if i['code'] == 'IDENTITY_QUESTION' and ent in i['entities'] for x in i['entities'] if x != ent})


def keyword_only(g, target, candidates, excluded, view, cap=5):
    out = []
    for c in candidates:
        if c in excluded or owner(g, c) == owner(g, target) or not G.visible(g, c, view)[0]:continue
        common = keyword_overlap(g, target, c)
        if common:out.append({'node': c, 'code': 'ONLY_SHARED_KEYWORD', 'shared_words': common[:5],
                              'reason': 'Words in common without a shared identifier, document or documented relationship.'})
    return sorted(out, key=lambda x: x['node'])[:cap]


def complements(g, token, view):
    """Operator B: independently recorded relationships/observations that may supply missing context."""
    obs = resolve(g, token); out = result(g, 'complements', obs, view)
    if g.nodes[obs]['kind'] != 'observation':raise NotFound('complements takes an observation')
    ent = entity_of(g, obs); here = owner(g, obs); occurred = G.occurrence(g.nodes[obs])
    rejected = [{'node': x, 'code': 'ONLY_NAME_SIMILARITY', 'reason': 'similar name, different identifier: identity unproven'}
                for x in similar_entities(g, ent)]
    if g.nodes[ent]['attrs']['identity_status'] != 'IDENTIFIED':
        out['abstentions'].append(abstain('NO_VERIFIED_IDENTITY', f"{ent} is {g.nodes[ent]['attrs']['identity_status']}; no cross-campaign join is made"))
        out['rejected'] = rejected; return K.summarise(out, rejected)
    used = {ent}
    for e, rel in linked(g, ent, ('SUBJECT', 'OBJECT'), 'in'):
        r = g.nodes[rel]; used.add(rel)
        if owner(g, rel) == here or not G.visible(g, rel, G.View(history=view.history, exclude_retrospective=view.exclude_retrospective))[0]:continue
        inside = G.period_check(r, occurred)
        if r['status'] != M.DOCUMENTED_RELATIONSHIP:
            rejected.append({'node': rel, 'code': 'SOURCE_DEPTH_INSUFFICIENT', 'reason': f"relationship is {g.display_status(rel)} {r['reasons']}"}); continue
        if inside is None:rejected.append({'node': rel, 'code': 'PERIOD_UNRESOLVED', 'reason': f"period {r['attrs']['period']} vs observation {occurred}"}); continue
        if inside is False:rejected.append({'node': rel, 'code': 'PERIOD_INCOMPATIBLE', 'reason': f"period {r['attrs']['period']} excludes observation date {occurred}"}); continue
        far = [o for _, o in linked(g, rel, ('SUBJECT', 'OBJECT'), 'out') if o != ent]
        claims = claims_using(g, rel)
        out['results'].append(K.annotate(g, suggestion('complements', obs, rel, ['EXACT_ENTITY_ID', 'DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD'],
            connection=f"{g.nodes[obs]['label']} concerns {ent}, which {r['label']} documents ({r['attrs']['direction']})",
            relationship={'status': r['status'], 'period': r['attrs']['period'], 'allocation': r['attrs']['allocation_status'],
                          'evidence': G.evidence_refs(g, rel)},
            linked_entities=far, claims={c: {'status': claim_status(g, c), 'missing_variables': g.nodes[c]['attrs'].get('missing_variables', []),
                                             'requirements': sorted({o for e2, o in linked(g, c, ('REQUIRES',), 'out')})} for c in claims},
            still_required=[x for x in [
                'documented allocation of the quantity to the counterparty' if r['attrs']['allocation_status'] == 'ALLOCATION_UNVERIFIED' else None,
                'quantified listed-company exposure and materiality', 'check whether the issuer or a specialist already explained it',
                None if g.nodes[obs]['attrs']['first_public_certified'] else 'first-public time of the observation (UNKNOWN)',
                'a frozen Discovery Lab claim and human M/H review'] if x]),
            obs, rel, ['EXACT_ENTITY_ID', 'DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD'], [ent, rel]))
    for e, other in linked(g, ent, ('DESCRIBES',), 'in'):
        used.add(other)
        if other == obs or owner(g, other) == here or not G.visible(g, other, view)[0]:continue
        out['results'].append(K.annotate(g, suggestion('complements', obs, other, ['EXACT_ENTITY_ID'],
            connection='another recorded observation of the same identified object',
            other_observation={'status': g.display_status(other), 'occurred': G.occurrence(g.nodes[other]), 'value': g.nodes[other]['attrs']['value'],
                               'units': g.nodes[other]['attrs']['units']},
            note='Different periods or populations are not contradictions; compare units before combining.',
            still_required=['confirm same quantity definition and units', 'a frozen Discovery Lab claim and human review']),
            obs, other, ['EXACT_ENTITY_ID'], [ent]))
    for e, hist in linked(g, ent, ('CONCERNS',), 'in'):
        used.add(hist)
        caveat = [ARCHIVE_CAVEAT] if e['attrs'].get('identity_basis') == 'SEC_ARCHIVE_PATH_IN_RECORDED_LOCATOR' else []
        out['results'].append(K.annotate(g, suggestion('complements', obs, hist, ['EXACT_ENTITY_ID'], connection='historical investigation concerned the same identifier',
                                         verdict=g.nodes[hist]['attrs']['verdict']['text'],
                                         still_required=caveat + ['read the cited report; the historical verdict stands']),
                                         obs, hist, ['EXACT_ENTITY_ID'], [ent]))
    others = [k for k, n in g.nodes.items() if n['kind'] in ('observation', 'relationship') and not n['superseded']]
    out['rejected'] = rejected + keyword_only(g, obs, others, used, view)
    out['results'] = sorted(out['results'], key=lambda r: K.order_key(r, STRENGTH))[:M.MAX_SUGGESTIONS]
    if not out['results']:out['abstentions'].append(abstain('NO_USEFUL_SUGGESTION', 'no identified, period-compatible complementary record'))
    return K.summarise(out, out['rejected'])


def same_gap(g, token, view):
    """Operator C: claims blocked by the same requirement class or mechanical blocker."""
    nid = resolve(g, token); n = g.nodes[nid]
    if n['kind'] not in ('requirement', 'blocker'):raise NotFound('same-gap takes a requirement (REQ_...) or blocker code')
    out = result(g, 'same-gap', nid, view, definition=n['attrs'].get('definition'), does_not_mean=n['attrs'].get('does_not_mean'))
    rows = defaultdict(list)
    for e, other in linked(g, nid, ('REQUIRES', 'BLOCKED_BY'), 'in'):
        if not G.visible(g, other, view)[0]:continue
        claim = other if g.nodes[other]['kind'] in ('claim', 'history_claim') else None
        if claim is None:continue
        rows[claim].append({'basis': e['attrs'].get('basis', 'MECHANICAL_BLOCKER'), 'detail': e['attrs'].get('detail')})
    for claim in sorted(rows):
        bases = sorted({r['basis'] for r in rows[claim]})
        out['results'].append({'claim': claim, 'origin': owner(g, claim), 'fixture': g.nodes[claim]['fixture'], 'status': claim_status(g, claim),
                               'link_bases': bases, 'candidate_only': bases == ['AUTHOR_TAG_CANDIDATE'],
                               'why_blocked': [r['detail'] for r in rows[claim]],
                               'evidence': [g.nodes[f]['attrs']['citation'] for _, f in linked(g, claim, ('HAS_FINDING',), 'out')
                                            if g.nodes[f]['attrs']['requirement'] == nid.split(':', 1)[1]],
                               # Same-gap is methodological reuse by construction: the shared item is the missing measurement.
                               'connection_class': K.WARNING, 'warning': K.warn(g, nid, claim, bases, [nid] if nid.startswith('requirement:') else [])})
    out['leads'] = [{'observation': o, 'basis': 'AUTHOR_TAG_CANDIDATE', 'status': g.display_status(o),
                     'note': 'Author tag says it may measure this requirement; not shown to measure it.'}
                    for e, o in linked(g, nid, ('MAY_MEASURE',), 'in') if G.visible(g, o, view)[0]]
    out['notes'].append('A shared blocker is an opportunity to reuse investigative knowledge, not proof of an economic relationship.')
    out['notes'].append('Every same-gap result is a METHODOLOGICAL_WARNING: claims blocked by the same requirement share no established economic exposure.')
    if not out['results']:out['abstentions'].append(abstain('NO_USEFUL_SUGGESTION', 'no visible claim is blocked by this requirement'))
    return K.summarise(out)


def explain(g, a, b, view, semantic=M.DEFAULT_SEMANTIC_HOPS):
    """Operator D: shortest bounded explanations, each with its first unsupported economic leap."""
    a, b = resolve(g, a), resolve(g, b)
    out = result(g, 'explain', f'{a} -> {b}', view)
    paths, bounds = G.find_paths(g, a, b, view, semantic)
    out['bounds'] = bounds
    out['results'] = [G.explain_path(g, p) for p in paths]
    if not paths:
        out['abstentions'].append(abstain('NO_PATH_WITHIN_BOUNDS', f"no visible path within {bounds['semantic_limit']} semantic and "
                                                                     f"{bounds['structural_limit']} structural steps; hubs and campaign nodes are not bridges"))
    out['notes'].append('A path is connectivity only. It never certifies transmission, allocation, materiality, causality or exposure.')
    return out


def changes(g, view=None):
    """Operator E: mechanically supportable changes and conflicts."""
    out = result(g, 'changes', None, view)
    for i in g.issues:out['results'].append(dict(i))
    for nid, n in sorted(g.nodes.items()):
        if n['status'] == M.CONTRADICTED:out['results'].append({'code': 'CONTRADICTED_RECORD', 'node': nid, 'note': 'retained for inspection'})
        if n['superseded']:
            newer = [o for _, o in linked(g, nid, ('SUPERSEDES',), 'in')]
            out['results'].append({'code': 'SUPERSEDED', 'node': nid, 'by': newer,
                                   'reason': g.nodes[newer[0]]['attrs'].get('revision_reason') if newer else None})
        refs = n['attrs'].get('freeze_references') if n['kind'] == 'claim' else None
        for rid, v in (refs or {}).items():
            camp = n['origin']['campaign']
            for kind in ('observation', 'relationship'):
                latest = [k for k, x in g.nodes.items() if k.startswith(f'{kind}:{camp}/{rid}@') and not x['superseded']]
                if latest and not latest[0].endswith(f'@{v}'):
                    out['results'].append({'code': 'REFERENCE_REVISED_AFTER_FREEZE', 'node': nid, 'reference': rid, 'frozen_version': v, 'now': latest[0]})
    out['excluded_inputs'] = g.excluded
    out['notes'].append('Different values for different periods or populations are not reported as contradictions.')
    return out


def revisit(g, token, view):
    """Operator F: earlier claims whose recorded gap a new observation might address. Never reopens them."""
    nid = resolve(g, token); n = g.nodes[nid]
    targets = [x for x in records_of(g, nid) if g.nodes[x]['kind'] == 'observation'] if n['kind'] == 'campaign' else [nid]
    if not targets or any(g.nodes[t]['kind'] != 'observation' for t in targets):raise NotFound('revisit takes a campaign or an observation')
    out = result(g, 'revisit', nid, view); rejected = []
    for obs in targets:
        o = g.nodes[obs]; here = owner(g, obs); ent = entity_of(g, obs); bases = defaultdict(set); via = defaultdict(list)
        caveats = defaultdict(set)
        for e, doc in linked(g, obs, ('CITES',), 'out'):
            if g.nodes[doc]['attrs']['content_identity'] != 'CONTENT_HASH' or not content_citation(e):continue
            for e2, other in linked(g, doc, ('CITES',), 'in'):
                if owner(g, other) == here or not content_citation(e2):continue
                for c in ([other] if g.nodes[other]['kind'] == 'claim' else claims_using(g, other)):
                    bases[c].add(doc_basis('CONTENT_HASH', e, e2)); via[c].append(doc)
        identified = g.nodes[ent]['attrs']['identity_status'] == 'IDENTIFIED'
        if identified:
            for e, other in linked(g, ent, ('SUBJECT', 'OBJECT', 'DESCRIBES', 'EXPOSES', 'CONCERNS'), 'in'):
                if owner(g, other) == here:continue
                for c in ([other] if g.nodes[other]['kind'] == 'claim' else claims_using(g, other)):
                    bases[c].add('EXACT_ENTITY_ID'); via[c].append(ent)
                    if e['attrs'].get('identity_basis') == 'SEC_ARCHIVE_PATH_IN_RECORDED_LOCATOR':caveats[c].add(ARCHIVE_CAVEAT)
                    if g.nodes[other]['kind'] == 'relationship':
                        inside = G.period_check(g.nodes[other], G.occurrence(o))
                        if g.nodes[other]['status'] == M.DOCUMENTED_RELATIONSHIP and inside:
                            bases[c].add('DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD'); via[c].append(other)
        rejected += [{'node': x, 'code': 'ONLY_NAME_SIMILARITY', 'observation': obs,
                      'reason': 'similar name, different identifier: never treated as the same object'} for x in similar_entities(g, ent)]
        for req in o['attrs']['measures_tags']:
            for e, c in linked(g, f'requirement:{req}', ('REQUIRES',), 'in'):
                if g.nodes[c]['kind'] in ('claim', 'history_claim') and owner(g, c) != here:
                    # The observation side is an author tag, so the match can never exceed a candidate.
                    bases[c].add('AUTHOR_TAG_CANDIDATE'); via[c].append(f'requirement:{req}')
        for t in o['attrs']['unknown_tags']:rejected.append({'node': obs, 'code': 'UNKNOWN_TAG', 'tag': t, 'reason': 'tag not in the requirement vocabulary'})
        for c in sorted(bases):
            if not G.visible(g, c, view)[0] or g.nodes[c]['superseded']:continue
            out['results'].append(K.annotate(g, evaluate_lead(g, obs, c, bases[c], via[c], caveats[c]), obs, c, bases[c], via[c]))
        claims = [k for k, x in g.nodes.items() if x['kind'] in ('claim', 'history_claim') and not x['superseded']]
        rejected += keyword_only(g, obs, claims, set(bases), view)
    # Grounded candidates always rank above warnings: a requirement-tag match can never outrank a grounded connection.
    out['results'].sort(key=lambda r: K.order_key(r, STRENGTH))
    out['results'] = out['results'][:M.MAX_SUGGESTIONS]
    out['rejected'] = rejected
    if not out['results']:out['abstentions'].append(abstain('NO_USEFUL_SUGGESTION', 'no earlier claim shares a document hash, identified object or requirement'))
    return K.summarise(out, rejected)


def evaluate_lead(g, obs, claim, bases, via, caveats=()):
    o, c = g.nodes[obs], g.nodes[claim]
    historical = c['kind'] == 'history_claim'
    unverified = sorted(caveats)
    if o['status'] != M.ORIGINAL_FIELD_OBSERVED:unverified.append(f"field not visible in an original ({g.display_status(obs)} {o['reasons']})")
    if not o['attrs']['first_public_certified']:unverified.append('historical availability (first-public time UNKNOWN)')
    tag_only = set(bases) <= {'AUTHOR_TAG_CANDIDATE'}
    if tag_only:unverified.append('that this observation measures the requirement (author tag only)')
    unverified += ['units and population match', 'identity of the linked economic object' if historical else 'allocation and exposure along the relationship']
    if historical:
        evidence = [g.nodes[f]['attrs']['citation']['quote'] for _, f in linked(g, f"{claim.split('/claim-')[0]}", ('HAS_FINDING',), 'out')
                    if g.nodes[f]['attrs']['finding_kind'] == 'EVIDENCE_TO_CHANGE']
        evidence += [g.nodes[f]['attrs']['citation']['quote'] for _, f in linked(g, claim, ('HAS_FINDING',), 'out')
                     if g.nodes[f]['attrs']['finding_kind'] == 'EVIDENCE_TO_CHANGE']
        units = {'claim_object': c['label'], 'financial_basis': c['attrs']['financial_basis']}
    else:
        evidence = [c['attrs']['falsification']]
        units = {'claim_predictor_units': c['attrs']['predictor']['units'], 'claim_population': c['attrs']['population']}
    return suggestion('revisit', obs, claim, bases, via=sorted(set(via)),
                      why_matched=sorted(set(bases), key=lambda b: STRENGTH.get(b, 99)),
                      field_visible=o['status'] == M.ORIGINAL_FIELD_OBSERVED, observation_depth=o['attrs']['depth'],
                      units_and_population={'observation_units': o['attrs']['units'], 'observation_denominator': o['attrs']['denominator'], **units},
                      identity='EXACT_IDENTIFIER' if 'EXACT_ENTITY_ID' in bases else 'NOT_ESTABLISHED',
                      time={'observation_occurred': G.occurrence(o), 'first_public': o['attrs']['clocks']['first_public']['value']},
                      not_yet_verified=unverified, minimum_evidence_to_resolve=evidence,
                      previous_status=claim_status(g, claim), previous_status_stands=True, candidate_only=tag_only)


def gaps(g, token, view=None):
    """Operator G: the specific links that remain unverified. Never fills them."""
    nid = resolve(g, token); n = g.nodes[nid]; out = result(g, 'gaps', nid, view)
    if n['kind'] == 'history_claim' or n['kind'] == 'history':
        hist = nid.split('/claim-')[0]
        findings = [f for x in ([nid] if n['kind'] == 'history_claim' else []) + [hist] for _, f in linked(g, x, ('HAS_FINDING',), 'out')]
        for f in sorted(set(findings)):
            a = g.nodes[f]['attrs']
            if a['finding_kind'] in ('MEASUREMENT_GAP', 'SOURCE_OMISSION', 'ACCESS_BLOCKED', 'RETROSPECTIVE_ONLY', 'IDENTITY_LIMIT'):
                out['results'].append({'link': g.nodes[f]['label'], 'state': a['finding_kind'], 'requirement': a['requirement'], 'citation': a['citation']})
        out['notes'].append('Recorded historical gaps are shown as cited; the graph does not fill or re-judge them.')
        return out
    if n['kind'] != 'claim':raise NotFound('gaps takes a claim')
    a = n['attrs']
    for _, o in linked(g, nid, ('PREDICTS_WITH',), 'out'):
        st = g.display_status(o)
        out['results'].append({'link': f'predictor {o}', 'state': 'VERIFIED' if G.verified_assertion(g.nodes[o]) else 'UNVERIFIED', 'detail': st})
        ent = entity_of(g, o)
        if g.nodes[ent]['attrs']['identity_status'] != 'IDENTIFIED':
            out['results'].append({'link': f'identity {ent}', 'state': 'UNVERIFIED', 'detail': g.nodes[ent]['attrs']['identity_status']})
    if not linked(g, nid, ('PREDICTS_WITH',), 'out'):out['results'].append({'link': 'predictor observation', 'state': 'MISSING', 'detail': 'NO_PREDICTOR_OBSERVATION'})
    for _, r in linked(g, nid, ('RELIES_ON',), 'out'):
        rn = g.nodes[r]
        out['results'].append({'link': f'relationship {r}', 'state': 'VERIFIED' if G.verified_assertion(rn) else 'UNVERIFIED', 'detail': g.display_status(r)})
        if rn['attrs']['allocation_status'] == 'ALLOCATION_UNVERIFIED':
            out['results'].append({'link': f"allocation along {r}", 'state': 'UNVERIFIED', 'detail': f"ALLOCATION_UNVERIFIED ({rn['attrs']['allocation_method']})"})
    x = a['exposure']
    out['results'].append({'link': f"exposure of {a['company']}", 'state': 'UNVERIFIED' if a['blockers']['financial_bridge'] else 'NO_MECHANICAL_BLOCKER',
                           'detail': {'claim_basis': x['claim_basis'], 'gross': x['gross'], 'net': x['net'], 'blockers': a['blockers']['financial_bridge']}})
    out['results'].append({'link': 'independent outcome', 'state': a['outcome']['status'], 'detail': a['blockers']['separate_outcome']})
    for req, codes in a['blockers'].items():
        for code in codes:out['results'].append({'link': req, 'state': 'BLOCKED', 'detail': code})
    out['notes'].append('Missing links are never filled by proportional arithmetic or model inference.')
    return out


def next_questions(g, view):
    """Operator H: reusable decisive checks across open claims, ordered categorically. Never authorises work."""
    out = result(g, 'next', None, view)
    open_claims = [k for k in sorted(g.nodes) if is_open(g, k) and G.visible(g, k, view)[0]]
    by_req = defaultdict(set)
    for c in open_claims:
        for e, r in linked(g, c, ('REQUIRES',), 'out'):by_req[r].add(c)
    history = defaultdict(set)
    for k, n in g.nodes.items():
        if n['kind'] == 'history_claim' and G.visible(g, k, view)[0]:
            for e, r in linked(g, k, ('REQUIRES',), 'out'):history[r].add(k.split('/claim-')[0])
    rows = []
    for req in sorted(set(by_req) | set(history)):
        claims = sorted(by_req.get(req, ()))
        proposals = [d['verify'] for c in claims for d in g.nodes[c]['attrs']['dispositions'] if d['verify']]
        rows.append({'requirement': req, 'open_claims': claims, 'open_claim_count': len(claims),
                     'historical_investigations': sorted(history.get(req, ())), 'decisive_checks': [g.nodes[c]['attrs']['falsification'] for c in claims],
                     'recorded_verify_proposals': proposals, 'has_specific_route': bool(proposals),
                     'connection_class': K.WARNING,
                     'meaning': 'A recurring research requirement; the claims and investigations listed are not thereby economically related.',
                     'authority': 'PROPOSAL_ONLY: a recommended check is not authorisation to perform it.'})
    rows.sort(key=lambda r: (-r['open_claim_count'], not r['has_specific_route'], -len(r['historical_investigations']), r['requirement']))
    out['results'] = rows[:M.MAX_SUGGESTIONS]
    out['notes'].append('Ordering is categorical (open claims sharing the requirement, then a recorded route, then historical recurrence); '
                        'no probability or expected value is computed.')
    if not open_claims:out['abstentions'].append(abstain('NO_OPEN_CLAIMS', 'no open Discovery Lab claim; historical recurrence is shown as reusable knowledge only'))
    return K.summarise(out)


def failures(g, view):
    out = result(g, 'failures', None, view)
    for k in sorted(g.nodes):
        n = g.nodes[k]
        if not G.visible(g, k, view)[0]:continue
        if n['kind'] == 'claim' and not n['superseded'] and n['attrs']['dispositions']:
            d = n['attrs']['dispositions'][-1]
            if d['decision'] in ('REJECT', 'HOLD'):
                out['results'].append({'node': k, 'decision': d['decision'], 'reason_type': d['reason_type'], 'scope': d['scope'],
                                       'requirements': sorted({o for _, o in linked(g, k, ('REQUIRES',), 'out')}), 'class': n['attrs']['claim_class']})
        if n['kind'] == 'history':
            out['results'].append({'node': k, 'decision': n['attrs']['verdict']['text'], 'status_class': n['attrs']['verdict']['status_class'],
                                   'scope': n['attrs']['verdict']['scope'],
                                   'requirements': sorted({o for c in [k] + [c for _, c in linked(g, k, ('RECORDS',), 'out')]
                                                           for _, o in linked(g, c, ('REQUIRES',), 'out')})})
    out['notes'].append('A negative research result is bounded to its scope; it is not proof that the economic proposition is false.')
    return out


def orphans(g, view):
    out = result(g, 'orphans', None, view)
    for k in sorted(g.nodes):
        n = g.nodes[k]
        if n['kind'] != 'observation' or n['superseded'] or not G.visible(g, k, view)[0]:continue
        if linked(g, k, ('PREDICTS_WITH', 'OUTCOME_FROM'), 'in'):continue
        ent = entity_of(g, k)
        rels = [r for _, r in linked(g, ent, ('SUBJECT', 'OBJECT'), 'in')]
        out['results'].append({'node': k, 'label': n['label'], 'status': g.display_status(k), 'entity': ent,
                               'state': 'CONNECTED_BUT_UNUSED' if rels else 'STANDALONE_RETAINED'})
    out['notes'].append('Standalone observations are retained so later evidence can connect to them.')
    return out
