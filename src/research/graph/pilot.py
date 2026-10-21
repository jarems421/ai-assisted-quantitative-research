"""Prospective-pilot support: frozen packet snapshots, arm-scoped query visibility, blinded adjudication,
budget accounting and paired reporting.

PROPOSED PILOT, NOT ACTIVE. Nothing here fetches a source, creates authority or runs a campaign; the
rehearsal in ``pilot_dryrun`` uses synthetic ledgers in a temporary directory.

Visibility. A packet snapshot, written once before either arm starts, pins the frozen prior knowledge:
the packet ledger as an exact prefix (event count and head hash), the historical catalogue by SHA-256 and
the private packet bundle by file hashes. At a query time an arm sees exactly that prior knowledge plus
its own ledger as appended by the query time. The other arm's ledger, other packets, earlier pilot
ledgers and anything appended after the query time are never inputs, and a future query time is refused.
A single global ``--known-at`` cannot express this: set to the campaign start it hides the arm's own new
observations; set later it would admit whatever else had been appended by then.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

from src.research.discovery import records as R
from src.research.discovery.ledger import Ledger, totals
from src.research.discovery.review import covered
from src.research.graph import catalogue as C
from src.research.graph import model as M
from src.research.graph.baseline import content_hashes, unjoinable
from src.research.graph.project import build, cut_state, parse_time
from src.research.spec import digest

VERSION = 'GRAPH_PILOT_SNAPSHOT_V001'
BLIND_VERSION = 'GRAPH_PILOT_BLIND_V001'
ARMS = ('S', 'G')
NOT_VISIBLE = ('the other arm\'s ledger, notes and connection log', 'every other packet and every earlier pilot ledger, of either arm',
               'records appended after the query time', 'ledger discovery under docs/strategy (inputs are listed, never discovered)')
S_OPERATORS = ('baseline-search', 'reading')
G_OPERATORS = S_OPERATORS + ('revisit', 'complements', 'suggestions', 'shared', 'same-gap', 'gaps', 'explain', 'trace', 'next', 'search',
                             'show', 'neighbourhood', 'changes', 'failures', 'orphans')
CATEGORIES = ('SOURCE_SEARCH', 'READING', 'RECORDING', 'BASELINE_SEARCH', 'GRAPH_QUERY', 'SUGGESTION_REVIEW', 'FREEZE_PREP', 'AVOIDED_REPEAT')
GRAPH_CATEGORIES = ('GRAPH_QUERY', 'SUGGESTION_REVIEW')
CATEGORY_TAG = re.compile(r'\[PILOT:([A-Z_]+)\]')
DECISIVE_TAG = re.compile(r'\[DECISIVE:([A-Z]+-[A-Za-z0-9_.-]+)\]')
CEILINGS = {'analyst_minutes': 120, 'source_starts': 6, 'searches': 10, 'bytes': 8 * 2 ** 20}

CONNECTION_KEYS = ('connection_id', 'arm', 'kind', 'operator', 'found_via', 'source_record', 'target_record', 'basis', 'arm_decision',
                   'analyst_minutes', 'discovery_lab_record', 'recorded_at_utc', 'notes')
CONNECTION_KINDS = ('CONNECTION', 'AVOIDED_REPEAT')
FOUND_VIA = ('GRAPH_ONLY', 'BASELINE_SEARCH_DISCOVERABLE', 'ANALYST_READING', 'BOTH')
ARM_DECISIONS = ('ACCEPTED', 'DECLINED', 'UNRESOLVED')
OUTCOMES = ('CONFIRMED_AGAINST_ORIGINALS', 'PLAUSIBLE_UNVERIFIED', 'REJECTED_FALSE', 'REJECTED_TRIVIAL')
MEANING = ('MEANINGFUL', 'NOT_MEANINGFUL', 'UNCLEAR')
ADJUDICATION_KEYS = ('blind_id', 'outcome', 'economic_meaning', 'checked_evidence', 'adjudicator', 'adjudicator_kind', 'adjudicator_minutes',
                     'recorded_at_utc', 'notes')
HIDDEN_FROM_ADJUDICATOR = ('arm', 'connection_id', 'operator', 'found_via', 'basis', 'arm_decision', 'analyst_minutes', 'discovery_lab_record',
                           'recorded_at_utc', 'notes', 'arm campaign ids', 'graph explanations and match strengths')


class PilotError(ValueError):
    """A pilot input, log or query that would break equivalence, isolation or blinding."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def write_new(path, value):
    """Pilot artefacts are written once; an existing file is never overwritten."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:f.write((json.dumps(value, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))
    return sha256(path)


def utc(value=None):
    return parse_time(value) if value else datetime.now(timezone.utc)


def connection_id(source, target, basis):
    """Deterministic id for a connection an arm forms itself (graph suggestions keep their SUG- ids)."""
    return 'CON-' + digest({'from': source, 'to': target, 'basis': sorted(basis)})[:12]


# -- frozen packet snapshot -------------------------------------------------------------------------

def make_snapshot(out, packet, packet_ledger, arms, bundle=None, catalogue=C.CATALOGUE_PATH, frozen_at=None, now=None):
    """Freeze one packet's prior knowledge. ``arms`` maps S and G to (ledger path, campaign id); neither ledger may exist yet."""
    out, now = Path(out), utc(now)
    frozen = utc(frozen_at) if frozen_at else now
    if frozen > now:raise PilotError('a snapshot cannot be frozen in the future')
    s = Ledger(packet_ledger).load()
    if parse_time(s.events[-1]['recorded_at_utc']) > frozen:raise PilotError('the packet ledger has events after the freeze time')
    try:cat_rel = Path(catalogue).resolve().relative_to(C.ROOT).as_posix()
    except ValueError as error:raise PilotError('the historical catalogue must be a repository file') from error
    cat = C.load(catalogue)[0]
    if parse_time(cat['recorded_at_utc']) > frozen:raise PilotError('the catalogue was recorded after the freeze time')
    if set(arms) != set(ARMS):raise PilotError(f'a snapshot names exactly the arms {ARMS}')
    paths = {a: Path(arms[a][0]) for a in ARMS}
    if len({p.resolve() for p in paths.values()} | {Path(packet_ledger).resolve()}) != 3:raise PilotError('the packet and each arm need distinct ledgers')
    if len({arms['S'][1], arms['G'][1], s.campaign['id']}) != 3:raise PilotError('the packet and each arm need distinct campaign ids')
    for a, p in paths.items():
        if p.exists():raise PilotError(f'arm {a} ledger already exists; arms start only after the snapshot is frozen')
    files = sorted(f for f in Path(bundle).rglob('*') if f.is_file()) if bundle else []
    rel = lambda p: Path(os.path.relpath(Path(p).resolve(), out.parent.resolve())).as_posix()
    snap = {'version': VERSION, 'packet': packet, 'fixture': s.fixture, 'frozen_at_utc': frozen.isoformat(),
            'prior': {'packet_ledger': {'path': rel(packet_ledger), 'campaign': s.campaign['id'], 'method': s.campaign['method'],
                                        'events': len(s.events), 'head_hash': s.events[-1]['hash']},
                      'catalogue': {'path': cat_rel, 'sha256': sha256(catalogue), 'recorded_at_utc': cat['recorded_at_utc']},
                      'bundle': [{'path': f.relative_to(bundle).as_posix(), 'sha256': sha256(f), 'bytes': f.stat().st_size} for f in files]},
            'arms': {a: {'ledger': rel(paths[a]), 'campaign': arms[a][1]} for a in ARMS},
            'not_visible_to_either_arm': list(NOT_VISIBLE)}
    return snap, write_new(out, snap)


def load_snapshot(path, bundle=None):
    """Verify a snapshot against the packet ledger, the catalogue and (when given) a copy of the packet bundle."""
    path = Path(path); snap = json.loads(path.read_text(encoding='utf-8'))
    if snap.get('version') != VERSION:raise PilotError(f'not a {VERSION} snapshot')
    prior, base = snap['prior'], path.parent
    packet = base / prior['packet_ledger']['path']
    full = Ledger(packet).load()
    if len(full.events) != prior['packet_ledger']['events'] or full.events[-1]['hash'] != prior['packet_ledger']['head_hash']:
        raise PilotError('the packet ledger changed after the snapshot was frozen')
    catalogue = C.ROOT / prior['catalogue']['path']
    if sha256(catalogue) != prior['catalogue']['sha256']:raise PilotError('the historical catalogue differs from the frozen snapshot')
    if bundle is not None:
        found = {f.relative_to(bundle).as_posix(): sha256(f) for f in sorted(Path(bundle).rglob('*')) if f.is_file()}
        want = {b['path']: b['sha256'] for b in prior['bundle']}
        if found != want:raise PilotError(f'the packet bundle differs from the frozen snapshot: {sorted(set(found) ^ set(want)) or "changed bytes"}')
    return {'snapshot': snap, 'sha256': sha256(path), 'base': base, 'packet_ledger': packet, 'catalogue': catalogue,
            'bundle_verified': bundle is not None}


def verify_summary(path, bundle=None):
    """What an arm checks before it starts: the same summary for both arms proves identical starting inputs."""
    v = load_snapshot(path, bundle); p = v['snapshot']['prior']
    return {'snapshot_sha256': v['sha256'], 'packet': v['snapshot']['packet'], 'frozen_at_utc': v['snapshot']['frozen_at_utc'],
            'packet_ledger': {k: p['packet_ledger'][k] for k in ('campaign', 'events', 'head_hash')},
            'catalogue_sha256': p['catalogue']['sha256'], 'bundle_digest': digest(p['bundle']), 'bundle_files': len(p['bundle']),
            'bundle_verified': v['bundle_verified']}


# -- arm-scoped visibility --------------------------------------------------------------------------

def arm_view(snapshot, arm, query_at=None, now=None):
    """The exact inputs one arm may see at a query time, with an auditable visibility receipt."""
    if arm not in ARMS:raise PilotError(f'arm must be one of {ARMS}')
    v = load_snapshot(snapshot); snap = v['snapshot']; now = utc(now)
    t, frozen = (utc(query_at) if query_at else now), parse_time(snap['frozen_at_utc'])
    if t > now:raise PilotError('the query time is in the future; knowledge appended later cannot be admitted')
    if t < frozen:raise PilotError('the query time precedes the packet snapshot')
    own = v['base'] / snap['arms'][arm]['ledger']
    if not own.is_file():raise PilotError(f"arm {arm} ledger {snap['arms'][arm]['ledger']} does not exist")
    full = Ledger(own).load()
    if full.campaign['id'] != snap['arms'][arm]['campaign']:raise PilotError(f"{own.name} is not the arm {arm} campaign {snap['arms'][arm]['campaign']}")
    if full.fixture != snap['fixture']:raise PilotError(f'the arm ledger is {full.fixture}; the snapshot is {snap["fixture"]}')
    if parse_time(full.events[0]['recorded_at_utc']) < frozen:raise PilotError('the arm campaign began before its packet snapshot was frozen')
    pk = snap['prior']['packet_ledger']
    ledgers = [str(Path(v['packet_ledger'])), str(Path(own))]
    cuts = {ledgers[0]: {'events': pk['events'], 'head_hash': pk['head_hash'], 'role': 'FROZEN_PRIOR_PACKET'},
            ledgers[1]: {'until': t, 'role': f'OWN_ARM_{arm}_AS_OF_QUERY'}}
    state = cut_state(full, cuts[ledgers[1]])[0]
    if state is None:raise PilotError(f'arm {arm} had not started at the query time')
    receipt = {'snapshot_sha256': v['sha256'], 'packet': snap['packet'], 'arm': arm, 'frozen_at_utc': snap['frozen_at_utc'], 'query_at_utc': t.isoformat(),
               'frozen_prior': {'packet_ledger': {k: pk[k] for k in ('campaign', 'events', 'head_hash')},
                                'catalogue_sha256': snap['prior']['catalogue']['sha256']},
               'own_ledger': {'campaign': full.campaign['id'], 'events_visible': len(state.events), 'events_total': len(full.events),
                              'head_hash_visible': state.events[-1]['hash']},
               'not_visible': list(NOT_VISIBLE)}
    return {'ledgers': ledgers, 'cuts': cuts, 'catalogue': v['catalogue'], 'mode': 'memory' if snap['fixture'] == 'LIVE' else 'synthetic',
            'receipt': receipt, 'snapshot': snap}


def arm_graph(snapshot, arm, query_at=None, now=None):
    """Graph v1 over exactly the arm's visible inputs. Only the graph arm uses it."""
    view = arm_view(snapshot, arm, query_at, now)
    g = build(view['ledgers'], catalogue_path=view['catalogue'], mode=view['mode'], with_memory=True, cuts=view['cuts'])
    if g.excluded or len(g.inputs) != 2 or not g.catalogue:raise PilotError(f'arm inputs incomplete: {g.excluded}')
    view['receipt']['graph_digest'] = g.digest()
    return g, view


# -- arm connection logs ----------------------------------------------------------------------------

def validate_connections(path, arm):
    """Every connection or avoided repeat an arm considered, as the arm logged it during the campaign."""
    rows, seen = read_jsonl(path), set()
    for n, r in enumerate(rows, 1):
        w = f'{Path(path).name} line {n}'
        if tuple(sorted(r)) != tuple(sorted(CONNECTION_KEYS)):raise PilotError(f'{w}: fields must be exactly {CONNECTION_KEYS}')
        if r['arm'] != arm:raise PilotError(f'{w}: logged by arm {r["arm"]}, expected {arm}')
        if not re.fullmatch(r'(SUG|CON)-[0-9a-f]{12}', r['connection_id']) or r['connection_id'] in seen:raise PilotError(f'{w}: invalid or repeated id')
        seen.add(r['connection_id'])
        if r['kind'] not in CONNECTION_KINDS or r['found_via'] not in FOUND_VIA or r['arm_decision'] not in ARM_DECISIONS:
            raise PilotError(f'{w}: invalid kind, found_via or arm_decision')
        if r['operator'] not in (S_OPERATORS if arm == 'S' else G_OPERATORS):raise PilotError(f'{w}: operator {r["operator"]} is not available to arm {arm}')
        if arm == 'S' and (r['connection_id'].startswith('SUG-') or r['found_via'] in ('GRAPH_ONLY', 'BOTH')):
            raise PilotError(f'{w}: the structured arm has no graph suggestions')
        if r['found_via'] in ('GRAPH_ONLY', 'BOTH') and r['operator'] in S_OPERATORS:raise PilotError(f'{w}: a graph attribution needs a graph operator')
        if not r['basis'] or not all(isinstance(b, str) and b for b in r['basis']):raise PilotError(f'{w}: basis lists the stated grounds')
        if r['kind'] == 'AVOIDED_REPEAT' and not any(b.startswith('AVOIDED:') for b in r['basis']):
            raise PilotError(f'{w}: an avoided repeat states the avoided action as AVOIDED: ...')
        if not (r['analyst_minutes'] == R.UNKNOWN or (isinstance(r['analyst_minutes'], (int, float)) and r['analyst_minutes'] >= 0)):
            raise PilotError(f'{w}: analyst_minutes must be a non-negative number or UNKNOWN')
        if (r['arm_decision'] == 'ACCEPTED') != bool(r['discovery_lab_record']):
            raise PilotError(f'{w}: an accepted connection, and only one, names the Discovery Lab record that holds it')
        if not r['source_record'] or not r['target_record'] or r['source_record'] == r['target_record']:raise PilotError(f'{w}: two distinct endpoints')
    return rows


# -- blinded adjudication ---------------------------------------------------------------------------

def ref_key(ref):
    """'observation:DLC-X/OBS-1@2' or 'DLC-X/OBS-1' -> 'DLC-X/OBS-1'; 'history:HIST-F01/claim-v1' -> 'HIST-F01/claim-v1'."""
    text = ref.split(':', 1)[1] if re.match(r'^[a-z_]+:', ref) else ref
    return text.rsplit('@', 1)[0]


def tags_in(text):
    return sorted({v for _, v in M.TAG.findall(text or '')})


def ledger_endpoint(s, rid, label):
    for kind in R.VERSIONED:
        r = s.latest(kind, rid)
        if r is None:continue
        if kind == 'source':
            return {'kind': 'source', 'campaign': label, 'record': rid, 'text': f"{r['name']} ({r['publisher']})", 'entities': [],
                    'evidence': [{'locator': r['locator'], 'sha256': None, 'depth': 'SOURCE_PASSPORT'}], 'tags': []}
        if kind == 'observation':
            ents, text = [r['entity']], ' '.join([r['statement'], r['why_informative'], *r['missing_evidence']])
            extra = {'value': r['value'], 'units': r['units'], 'occurred': r['clocks']['economic_occurrence']['value'], 'depth': r['depth']}
        elif kind == 'relationship':
            ents, text = [r['source_entity'], r['target_entity']], r['direction']
            extra = {'type': r['type'], 'period': r['period'], 'basis': r['basis'], 'status': r['status']}
        else:
            ents, text = [r['exposure']['company']], ' '.join([r['mechanism'], r['predictor']['quantity'], *r['missing_variables']])
            extra = {'outcome': r['outcome']['quantity']}
        evidence = r['evidence'] if kind != 'candidate' else r['outcome']['evidence'] + r['closest_substitute']['evidence']
        if kind == 'relationship':evidence = evidence + r['quantity_transfer']['evidence']
        return {'kind': kind, 'campaign': label, 'record': rid, 'text': text, 'entities': [{'id': e['id'], 'name': e['name']} for e in ents],
                'evidence': [{'locator': ev['locator'], 'sha256': ev['sha256'], 'depth': ev['depth']} for ev in evidence],
                'tags': tags_in(text), **extra}
    raise PilotError(f'{label}/{rid} is not a recorded source, observation, relationship or candidate')


def catalogue_endpoint(cat, key):
    hid, _, part = key.partition('/')
    inv = next((i for i in cat['investigations'] if i['id'] == hid), None)
    if inv is None:raise PilotError(f'{hid} is not in the frozen catalogue')
    base = {'kind': 'historical_investigation', 'campaign': 'HISTORICAL_MEMORY', 'record': key,
            'entities': [{'id': e['id'], 'name': e['name']} for e in inv['entities']],
            'evidence': [{'locator': d['locator'], 'sha256': d['sha256'], 'depth': f"RECEIPT_HTTP_{d['http_status']}"} for d in inv['documents']]}
    if not part:return {**base, 'text': f"{inv['title']}. Verdict: {inv['verdict']['text']}", 'tags': sorted({f['requirement'] for f in inv['findings'] if f['requirement']})}
    if part.startswith('claim-'):
        c = next((c for c in inv['claims'] if c['id'] == part[6:]), None)
        if c is None:raise PilotError(f'{key} is not a catalogued claim')
        reqs = sorted({f['requirement'] for f in inv['findings'] if f['claim'] == c['id'] and f['requirement']})
        return {**base, 'kind': 'historical_claim', 'text': c['object'], 'tags': reqs}
    f = next((f for f in inv['findings'] if f['id'] == part), None)
    if f is None:raise PilotError(f'{key} is not a catalogued finding')
    return {**base, 'kind': 'historical_finding', 'text': f['text'], 'tags': [f['requirement']] if f['requirement'] else [],
            'evidence': [{'locator': f['citation']['path'], 'sha256': None, 'depth': 'REPORT_QUOTE', 'passage': f['citation']['quote']}]}


def shared_structure(a, b):
    """One mechanical comparison for every endpoint pair, whichever arm logged it."""
    ids = lambda x: {e['id'] for e in x['entities'] if not unjoinable(e['id'])}
    hashes = lambda x: {e['sha256'] for e in x['evidence'] if e['sha256']}
    out = {'same_identified_entity': sorted(ids(a) & ids(b)), 'shared_document_hashes': sorted(hashes(a) & hashes(b)),
           'shared_requirement_tags': sorted(set(a['tags']) & set(b['tags'])),
           'name_or_ticker_only_entities': sorted({e['id'] for x in (a, b) for e in x['entities'] if unjoinable(e['id'])})}
    rel, other = (a, b) if a['kind'] == 'relationship' else (b, a)
    if rel['kind'] == 'relationship' and other['kind'] == 'observation':
        moment = R.when(other['occurred'], 'occurrence') if other['occurred'] != R.UNKNOWN else None
        inside = covered(rel['period'], moment) if moment else None
        out['relationship_period_covers_observation'] = {True: 'YES', False: 'NO', None: 'UNRESOLVED'}[inside]
    return out


def blind(snapshot, logs, salt, blind_out, key_out):
    """Prepare the adjudicator's export: shuffled, arm-hidden items with identical provenance rendering for both arms.

    Run by a session that is neither arm, after both arms of the packet finish. The key (blind id -> arm and
    connection id, plus the salt) is written separately and its hash recorded in the export, so it cannot be
    changed once adjudication begins."""
    if not salt or len(salt) < 16:raise PilotError('the blinding salt needs at least 16 characters, chosen by the preparer and kept in the key')
    v = load_snapshot(snapshot); snap = v['snapshot']; cat = C.load(v['catalogue'])[0]
    packet = cut_state(Ledger(v['packet_ledger']).load(), {'events': snap['prior']['packet_ledger']['events'],
                                                         'head_hash': snap['prior']['packet_ledger']['head_hash']})[0]
    items, key = [], {}
    for arm in ARMS:
        own = Ledger(v['base'] / snap['arms'][arm]['ledger']).load()
        labels = {own.campaign['id']: (own, 'CURRENT_ARM_CAMPAIGN'), packet.campaign['id']: (packet, 'FROZEN_PACKET')}

        def endpoint(ref):
            k = ref_key(ref)
            if k.startswith('HIST-'):return catalogue_endpoint(cat, k)
            campaign, _, rid = k.partition('/')
            if campaign not in labels:raise PilotError(f'{ref} is outside the arm {arm} inputs (packet, own ledger, catalogue)')
            return ledger_endpoint(labels[campaign][0], rid, labels[campaign][1])

        for r in validate_connections(logs[arm], arm):
            held = r['discovery_lab_record']
            if held and held.startswith(own.campaign['id'] + '/'):held = held.split('/', 1)[1].rsplit('@', 1)[0]  # own-campaign-qualified form
            if held and not (any(own.latest(k, held) for k in R.VERSIONED) or any(held in own.ids(k) for k in ('review', 'disposition', 'effort'))):
                raise PilotError(f"{r['connection_id']}: {r['discovery_lab_record']} is not in the arm {arm} ledger")
            a, b = endpoint(r['source_record']), endpoint(r['target_record'])
            bid = 'ADJ-' + hashlib.sha256(f"{salt}|{arm}|{r['connection_id']}".encode()).hexdigest()[:10]
            item = {'blind_id': bid, 'kind': r['kind'], 'from': a, 'to': b, 'shared_structure': shared_structure(a, b)}
            if r['kind'] == 'AVOIDED_REPEAT':item['avoided_action'] = [x[8:].strip() for x in r['basis'] if x.startswith('AVOIDED:')]
            items.append(item); key[bid] = {'arm': arm, 'connection_id': r['connection_id']}
    items.sort(key=lambda i: i['blind_id'])
    random.Random(int(hashlib.sha256(f"{salt}|{v['sha256']}".encode()).hexdigest()[:16], 16)).shuffle(items)
    key_sha = write_new(key_out, {'version': BLIND_VERSION, 'snapshot_sha256': v['sha256'], 'salt': salt, 'items': dict(sorted(key.items()))})
    export = {'version': BLIND_VERSION, 'packet': snap['packet'], 'fixture': snap['fixture'], 'snapshot_sha256': v['sha256'], 'key_sha256': key_sha,
              'hidden_from_adjudicator': list(HIDDEN_FROM_ADJUDICATOR),
              'instructions': ['Adjudicate every item once, against the cited originals, without consulting arm ledgers, logs or sessions.',
                               'CONFIRMED_AGAINST_ORIGINALS must list the evidence identifiers (sha256 or locator) you checked.',
                               'Economic meaning: does the connection link an observed quantity or documented relationship to a listed '
                               "company's documented exposure, or to a claim's required measurement?"],
              'items': items}
    write_new(blind_out, export)
    return export


def validate_adjudications(blind_path, adjudication_path):
    """Each blinded item adjudicated exactly once by a human (a labelled fixture stand-in only in a synthetic rehearsal)."""
    export = json.loads(Path(blind_path).read_text(encoding='utf-8'))
    items = {i['blind_id']: i for i in export['items']}; seen = {}
    for n, r in enumerate(read_jsonl(adjudication_path), 1):
        w = f'{Path(adjudication_path).name} line {n}'
        if tuple(sorted(r)) != tuple(sorted(ADJUDICATION_KEYS)):raise PilotError(f'{w}: fields must be exactly {ADJUDICATION_KEYS}')
        if r['blind_id'] not in items or r['blind_id'] in seen:raise PilotError(f'{w}: unknown or repeated blind id')
        if r['outcome'] not in OUTCOMES or r['economic_meaning'] not in MEANING:raise PilotError(f'{w}: invalid outcome or economic_meaning')
        allowed = ('HUMAN', 'SYNTHETIC_FIXTURE') if export['fixture'] == 'SYNTHETIC' else ('HUMAN',)
        if r['adjudicator_kind'] not in allowed or not r['adjudicator'] or r['adjudicator'].lower().startswith(('claude', 'assistant')):
            raise PilotError(f'{w}: adjudication is a human decision')
        if r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS':
            item = items[r['blind_id']]
            evidence = {x for end in (item['from'], item['to']) for e in end['evidence'] for x in (e['sha256'], e['locator']) if x}
            if not r['checked_evidence'] or not set(r['checked_evidence']) <= evidence:
                raise PilotError(f'{w}: a confirmation lists the cited evidence it was checked against')
        if not (r['adjudicator_minutes'] == R.UNKNOWN or (isinstance(r['adjudicator_minutes'], (int, float)) and r['adjudicator_minutes'] >= 0)):
            raise PilotError(f'{w}: adjudicator_minutes must be a non-negative number or UNKNOWN')
        seen[r['blind_id']] = r
    if set(seen) != set(items):raise PilotError(f'{len(set(items) - set(seen))} blinded items are not adjudicated')
    return seen


def unblind(packet_dir):
    """Join adjudications to arm logs through the sealed key, after adjudication is complete and committed."""
    d = Path(packet_dir)
    export = json.loads((d / 'blind.json').read_text(encoding='utf-8'))
    if sha256(d / 'key.json') != export['key_sha256']:raise PilotError('the key does not match the hash sealed in the blinded export')
    key = json.loads((d / 'key.json').read_text(encoding='utf-8'))
    adjudications = validate_adjudications(d / 'blind.json', d / 'adjudications.jsonl')
    logs = {arm: {r['connection_id']: r for r in validate_connections(d / f'connections-{arm}.jsonl', arm)} for arm in ARMS}
    rows = []
    for bid, ref in key['items'].items():
        r, a = logs[ref['arm']][ref['connection_id']], adjudications[bid]
        rows.append({'blind_id': bid, **{k: r[k] for k in ('arm', 'connection_id', 'kind', 'operator', 'found_via', 'arm_decision', 'analyst_minutes')},
                     **{k: a[k] for k in ('outcome', 'economic_meaning', 'adjudicator_minutes')}})
    if len(rows) != sum(len(x) for x in logs.values()):raise PilotError('every logged connection must appear in the blinded export')
    return rows


# -- budget accounting and outcomes -----------------------------------------------------------------

def account(ledger, arm):
    """Effort by pilot category against the per-campaign ceilings. Unknown minutes stay UNKNOWN, never zero."""
    s = ledger if not isinstance(ledger, (str, Path)) else Ledger(ledger).load()
    by, violations = {c: 0 for c in CATEGORIES}, []
    for e in s.efforts:
        found = CATEGORY_TAG.findall(e['description'])
        cat = found[0] if len(found) == 1 and found[0] in CATEGORIES else None
        if cat is None:violations.append({'effort': e['id'], 'code': 'UNCATEGORISED_EFFORT'})
        elif e['analyst_minutes'] != R.UNKNOWN:by[cat] += e['analyst_minutes']
        if arm == 'S' and cat in GRAPH_CATEGORIES:violations.append({'effort': e['id'], 'code': 'GRAPH_TIME_IN_STRUCTURED_ARM'})
        if e['kind'] == 'SEARCH' and cat != 'SOURCE_SEARCH':violations.append({'effort': e['id'], 'code': 'SEARCH_NOT_CATEGORISED_SOURCE_SEARCH'})
    t = totals(s.efforts)
    used = {'analyst_minutes': t['analyst_minutes']['known'], 'source_starts': t['source_starts']['known'],
            'searches': sum(e['kind'] == 'SEARCH' for e in s.efforts), 'bytes': t['bytes']['known']}
    for k, limit in CEILINGS.items():
        if used[k] > limit:violations.append({'code': 'OVER_CAMPAIGN_CEILING', 'field': k, 'used': used[k], 'ceiling': limit})
    unknown = {k: t[k]['unknown_entries'] for k in ('analyst_minutes', 'source_starts', 'bytes')}
    return {'campaign': s.campaign['id'], 'arm': arm, 'minutes_by_category': by, 'graph_minutes': sum(by[c] for c in GRAPH_CATEGORIES),
            'used': used, 'ceilings': dict(CEILINGS), 'unknown_entries': unknown, 'violations': violations}


def decisive_minutes(s):
    """Per REJECT/HOLD disposition naming its decisive record ([DECISIVE:ID]): analyst minutes logged before that record."""
    first, out = {}, {}
    for e in s.events:
        if e['type'] in R.VERSIONED:first.setdefault(e['record']['id'], e['seq'])
    efforts = [(e['seq'], e['record']['analyst_minutes']) for e in s.events if e['type'] == 'effort']
    for d in s.dispositions:
        if d['decision'] not in ('REJECT', 'HOLD'):continue
        m = DECISIVE_TAG.search(d['reason'])
        if not m or m.group(1) not in first:out[d['candidate_id']] = 'NOT_NAMED'; continue
        before = [x for seq, x in efforts if seq < first[m.group(1)]]
        out[d['candidate_id']] = R.UNKNOWN if R.UNKNOWN in before else sum(before)
    return out


def original_m_passes(s):
    return sum(1 for d in s.dispositions if d['decision'] == 'M_PASSED' and s.frozen(d['candidate_id'], d['version'])
               and s.derived[('candidate', d['candidate_id'], d['version'])]['claim_class'] == 'ORIGINAL'
               and not s.derived[('candidate', d['candidate_id'], d['version'])]['post_outcome'])


def median(values):
    known = [v for v in values if v not in (R.UNKNOWN, 'NOT_NAMED')]
    return statistics.median(known) if known else None


def per_hour(count, minutes):
    return round(count / (minutes / 60), 3) if minutes else None


def arm_metrics(s, arm, rows):
    acc = account(s, arm); minutes = acc['used']['analyst_minutes'] if not acc['unknown_entries']['analyst_minutes'] else None
    mine = [r for r in rows if r['arm'] == arm]; conn = [r for r in mine if r['kind'] == 'CONNECTION']
    confirmed = lambda r: r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS' and r['economic_meaning'] == 'MEANINGFUL'
    verified = [r for r in conn if r['arm_decision'] == 'ACCEPTED' and confirmed(r)]
    graph_items = [r for r in conn if r['connection_id'].startswith('SUG-')]
    m = original_m_passes(s); falsify = decisive_minutes(s)
    return {'campaign': s.campaign['id'], 'analyst_minutes_all': minutes, 'graph_minutes': acc['graph_minutes'],
            'verified_connections': len(verified), 'verified_connections_per_hour': per_hour(len(verified), minutes),
            'graph_only_verified': sum(r['found_via'] == 'GRAPH_ONLY' for r in verified),
            'false_or_premature_joins_made': sum(r['arm_decision'] == 'ACCEPTED' and r['outcome'] in ('REJECTED_FALSE', 'PLAUSIBLE_UNVERIFIED') for r in conn),
            'false_joins_declined': sum(r['arm_decision'] == 'DECLINED' and r['outcome'] == 'REJECTED_FALSE' for r in conn),
            'true_connections_declined': sum(r['arm_decision'] != 'ACCEPTED' and confirmed(r) for r in conn),
            'median_minutes_per_connection': median([r['analyst_minutes'] for r in conn]),
            'median_minutes_to_decisive_falsification': median(falsify.values()), 'decisive_falsification': falsify,
            'duplicate_research_avoided': sum(r['kind'] == 'AVOIDED_REPEAT' and r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS' for r in mine),
            'review_burden_items': len(mine), 'adjudicator_minutes': sum(r['adjudicator_minutes'] for r in mine if r['adjudicator_minutes'] != R.UNKNOWN),
            'suggestion_review_minutes': acc['minutes_by_category']['SUGGESTION_REVIEW'],
            'graph_suggestions_false_or_trivial': [sum(r['outcome'] in ('REJECTED_FALSE', 'REJECTED_TRIVIAL') for r in graph_items), len(graph_items)],
            'original_frozen_m_passes': m, 'original_frozen_m_passes_per_hour': per_hour(m, minutes),
            'h_plausible_human': sum(1 for r in s.reviews if r['kind'] == 'H' and r['judgments']['judgment'] == 'PLAUSIBLE'
                                     and R.human_equivalent(r['reviewer']['kind'], s.fixture)),
            'budget_violations': acc['violations']}


# Benefit dimensions (direction of improvement); review burden is reported as a cost, never as a benefit.
DIMENSIONS = (('verified_connections_per_hour', 'higher'), ('false_or_premature_joins_made', 'lower'), ('median_minutes_per_connection', 'lower'),
              ('median_minutes_to_decisive_falsification', 'lower'), ('duplicate_research_avoided', 'higher'),
              ('original_frozen_m_passes_per_hour', 'higher'))
COSTS = (('review_burden_items', 'lower'), ('adjudicator_minutes', 'lower'))


def direction(g, s, better):
    if g is None or s is None:return 'NOT_COMPARABLE'
    if g == s:return 'EQUAL'
    return 'G' if (g > s) == (better == 'higher') else 'S'


def classify(packets, critical_stops=()):
    """Proposed descriptive decision rule (to be confirmed at activation). It describes this sample; it is not inference."""
    if critical_stops:return 'INVALID_CRITICAL_STOP', ['A critical stop occurred: fix and re-review before any further use.']
    pooled = {}
    for arm in ARMS:
        minutes = [p[arm]['analyst_minutes_all'] for p in packets]
        pooled[arm] = None if None in minutes else per_hour(sum(p[arm]['verified_connections'] for p in packets), sum(minutes))
    tally = {name: {'G': 0, 'S': 0, 'EQUAL': 0, 'NOT_COMPARABLE': 0} for name, _ in DIMENSIONS}
    for p in packets:
        for name, better in DIMENSIONS:tally[name][direction(p['G'][name], p['S'][name], better)] += 1
    favours = lambda arm: [n for n, t in tally.items() if t[arm] >= 2 and t[arm] > t['G' if arm == 'S' else 'S']]
    noisy = [p['G']['graph_suggestions_false_or_trivial'] for p in packets]
    false_n, total_n = sum(x[0] for x in noisy), sum(x[1] for x in noisy)
    noise = total_n >= 20 and false_n / total_n > 0.8
    notes = [f"pooled verified connections per analyst-hour (all minutes, graph time included): G {pooled['G']}, S {pooled['S']}",
             f"benefit dimensions favouring G: {favours('G') or 'none'}; favouring S: {favours('S') or 'none'}",
             f'graph suggestions adjudicated false or trivial: {false_n}/{total_n}',
             'Zero graph-only connections, alone, triggers no decision; every dimension is reported.',
             f'{len(packets)} packet pair(s): a description of this sample, not a statistical estimate.']
    comparable = sum(1 for p in packets if p['G']['analyst_minutes_all'] and p['S']['analyst_minutes_all'])
    if comparable < 3 or None in pooled.values():return 'INCONCLUSIVE', notes + ['Fewer than three comparable packet pairs.']
    if pooled['G'] >= pooled['S'] and len(favours('G')) >= 2 and not favours('S') and not noise:
        return 'GRAPH_INCREMENT_OBSERVED', notes + ['Proposed next step: a larger, separately approved pilot. Not evidence of investment value.']
    if pooled['G'] < pooled['S'] and not favours('G'):
        return 'NO_GRAPH_INCREMENT_OBSERVED', notes + ['Proposed next step: do not add graph discovery operators to the default workflow; '
                                                       'any retirement is a separate owner decision after reading every dimension.']
    return 'INCONCLUSIVE', notes + ['Mixed dimensions: the owner decides whether a larger pilot is worth its cost.']


def report(packet_dirs, critical_stops=()):
    """Paired per-packet outcomes for every dimension, the cost of the increment, and the proposed classification."""
    packets = []
    for d in map(Path, packet_dirs):
        snap = load_snapshot(d / 'snapshot.json')['snapshot']; rows = unblind(d)
        packets.append({'packet': snap['packet'], 'method': snap['prior']['packet_ledger']['method'],
                        **{arm: arm_metrics(Ledger(d / snap['arms'][arm]['ledger']).load(), arm, rows) for arm in ARMS}})
    for p in packets:
        p['directions'] = {name: direction(p['G'][name], p['S'][name], better) for name, better in DIMENSIONS + COSTS}
    verdict, notes = classify(packets, critical_stops)
    return {'banner': M.BANNER, 'scope': 'PILOT_PAIRED_REPORT', 'packets': packets, 'classification': verdict, 'notes': notes}


def markdown(rep):
    names = [n for n, _ in DIMENSIONS + COSTS]
    lines = ['| Packet | Dimension | S | G | Better |', '|---|---|---:|---:|---|']
    for p in rep['packets']:
        for n in names:lines.append(f"| {p['packet']} ({p['method']}) | {n} | {p['S'][n]} | {p['G'][n]} | {p['directions'][n]} |")
        lines.append(f"| {p['packet']} | analyst minutes (all; graph) | {p['S']['analyst_minutes_all']} | {p['G']['analyst_minutes_all']} "
                     f"({p['G']['graph_minutes']} graph) | |")
    return '\n'.join(lines + ['', f"Classification (proposed rule): **{rep['classification']}**", '', *[f'- {n}' for n in rep['notes']]])
