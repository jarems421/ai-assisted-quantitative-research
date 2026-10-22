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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.research.discovery import records as R
from src.research.discovery.ledger import Ledger, totals
from src.research.discovery.review import covered
from src.research.graph import catalogue as C
from src.research.graph import connections as K
from src.research.graph import implementation as I
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
# Owner decision (2026-10-22): the proposed R4 graph configuration, frozen prospectively. V2 snapshots default to it.
# V002 supersedes V001 (identical configuration; V001's hand-entered recorded_at_utc was later than its own commit and is
# preserved unchanged; see docs/strategy/graph_timestamp_corrections_2026-10-22.json).
R4_CONFIGURATION = C.ROOT / 'docs/strategy/graph_pilot_r4_graph_configuration_v002.json'
R4_CONFIGURATION_VERSION = 'GRAPH_PILOT_R4_GRAPH_CONFIGURATION_V002'
# Saved execution provenance (the implementation_check of every visibility receipt).
PROVENANCE_KEYS = ('status', 'running_commit', 'dirty_pinned_paths')
PROVENANCE_STATUSES = ('EXACT_COMMIT', 'UNRELATED_COMMIT_CHANGE', 'GIT_UNAVAILABLE_CONTENT_VERIFIED')
PROVENANCE_ESTABLISHES = ('the saved record is well formed and consistent with the snapshot pin; the named commit exists in this repository, is dated '
                          'no later than the query (by its self-declared committer date; no skew allowance), and its pinned files differ from the pinned content '
                          'exactly at the declared uncommitted paths, so it could have run the pinned code')
PROVENANCE_PROCEDURAL = ('that the query actually ran at that commit: a git commit, its date and local history are self-reported and not a '
                         'cryptographic or external attestation; a fabricated record naming another consistent commit cannot be distinguished')
# Owner policy (2026-10-22): a self-reported vs derived difference is material above the greater of 5 minutes or 10%.
EFFORT_DISCREPANCY = {'minutes': 5, 'share': 0.10}
# Owner policy: the human arm operator personally writes separate, immutable START and STOP attestations as they occur.
SESSION_VERSION = 'GRAPH_PILOT_SESSION_ATTESTATION_V001'
SESSION_KEYS = ('version', 'packet', 'arm', 'event', 'at_utc', 'recorded_at_utc', 'recorded_by', 'statement')
SESSION_EVENTS = ('START', 'STOP')
ATTESTATION_LAG_MINUTES = 5
ASSISTANT_NAME = re.compile(r'\b(claude|assistant|codex|chatgpt|gpt|copilot|gemini|llm|ai agent|bot)\b', re.I)
# Owner policy: descriptive only. Gaps between recorded actions longer than this are listed, never subtracted from effort.
LONG_GAP_MINUTES = 30

CONNECTION_KEYS = ('connection_id', 'arm', 'kind', 'operator', 'found_via', 'source_record', 'target_record', 'basis', 'arm_decision',
                   'analyst_minutes', 'discovery_lab_record', 'recorded_at_utc', 'notes')
CONNECTION_KINDS = ('CONNECTION', 'AVOIDED_REPEAT')
FOUND_VIA = ('GRAPH_ONLY', 'BASELINE_SEARCH_DISCOVERABLE', 'ANALYST_READING', 'BOTH')
ARM_DECISIONS = ('ACCEPTED', 'DECLINED', 'UNRESOLVED')
OUTCOMES = ('CONFIRMED_AGAINST_ORIGINALS', 'PLAUSIBLE_UNVERIFIED', 'REJECTED_FALSE', 'REJECTED_TRIVIAL')
MEANING = ('MEANINGFUL', 'NOT_MEANINGFUL', 'UNCLEAR')
# Prospective V2 connection log (Graph v1.1). V1 rows (R3) stay valid unchanged; a V2 row names its version and keeps the
# exact originating graph suggestion, so graph-originated connections are always traceable (R3 lost this: CON- ids only).
CONNECTION_LOG_V2 = 'GRAPH_PILOT_CONNECTION_V2'
CONNECTION_KEYS_V2 = CONNECTION_KEYS + ('log_version', 'origin_suggestion_id', 'origin_operator', 'origin_bases', 'connection_class')
CONNECTION_KINDS_V2 = CONNECTION_KINDS + ('METHODOLOGICAL_WARNING',)
GRAPH_OPERATORS = tuple(o for o in G_OPERATORS if o not in S_OPERATORS)
# Graph-originated V2 rows must come from an operator that issues SUG- ids, saved as its snapshot-mode JSON in the
# packet's frozen suggestion export directory at query time. Inspection operators (explain, trace, ...) issue none.
SUGGESTING_OPERATORS = ('revisit', 'complements', 'shared', 'same-gap', 'next', 'suggestions')
SUGGESTION_EXPORT_DIR = 'suggestions-G'
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

def load_r4_configuration(path=R4_CONFIGURATION):
    """The registered R4 graph configuration; refuses if its register no longer matches the frozen hash."""
    cfg = json.loads(Path(path).read_text(encoding='utf-8'))
    if cfg.get('version') != R4_CONFIGURATION_VERSION:raise PilotError(f'not a {R4_CONFIGURATION_VERSION} configuration')
    if cfg['graph_operator_version'] != K.OPERATOR_VERSION or cfg['classification'] not in K.CLASSIFICATIONS:
        raise PilotError('the registered R4 configuration names operators or rules this implementation does not provide')
    if sha256(C.ROOT / cfg['generic_register']['path']) != cfg['generic_register']['sha256']:
        raise PilotError('the generic-identifier register differs from the registered R4 configuration')
    return cfg


def make_snapshot(out, packet, packet_ledger, arms, bundle=None, catalogue=C.CATALOGUE_PATH, frozen_at=None, now=None, connection_log=None,
                  implementation=None, classification=None):
    """Freeze one packet's prior knowledge. ``arms`` maps S and G to (ledger path, campaign id); neither ledger may exist yet.

    ``connection_log=CONNECTION_LOG_V2`` (prospective pilots) freezes the packet for V2 logs: every arm row must then be V2,
    with graph rows checked against the frozen suggestion export, and the graph operators are pinned to this version and to the
    exact implementation (``implementation.pin()``: commit and content digest; ``implementation`` overrides it, for a pin
    taken from another checkout). A V2 packet also records its classification ruleset (``classification``; V1_2 pins the
    generic-identifier register by hash)."""
    if connection_log not in (None, CONNECTION_LOG_V2):raise PilotError(f'connection_log is {CONNECTION_LOG_V2} or omitted')
    cfg = load_r4_configuration() if connection_log else None
    classification = classification or (cfg['classification'] if cfg else K.CLASSIFICATION_V1_1)
    if classification not in K.CLASSIFICATIONS:raise PilotError(f'classification is one of {K.CLASSIFICATIONS}')
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
    if connection_log:
        try:pinned = implementation if implementation is not None else I.pin()
        except I.PinError as error:raise PilotError(str(error)) from error
        register = None
        if classification == K.CLASSIFICATION_V1_2:
            K.load_register()
            register = {'path': K.GENERIC_REGISTER.relative_to(C.ROOT).as_posix(), 'sha256': sha256(K.GENERIC_REGISTER)}
        snap.update({'connection_log': connection_log, 'graph_operator_version': K.OPERATOR_VERSION, 'graph_implementation': pinned,
                     'classification': {'rules': classification, 'generic_register': register},
                     'r4_configuration': {'path': R4_CONFIGURATION.relative_to(C.ROOT).as_posix(), 'sha256': sha256(R4_CONFIGURATION),
                                          'conforms': classification == cfg['classification'] and (register or {}).get('sha256') == cfg['generic_register']['sha256']}})
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
    if snap.get('connection_log') == CONNECTION_LOG_V2 and not snap.get('graph_implementation'):
        raise PilotError('a V2 packet snapshot must pin the Graph implementation (commit and content digest)')
    # Uniform enforcement: every snapshot-bound entry point (arm views for both arms, graph queries, structured search,
    # replay, blinding, unblinding, effort, accounting, report) loads the snapshot here, so all verify the same pin.
    implementation_check(snap, with_git=False)
    register = (snap.get('classification') or {}).get('generic_register')
    if register and sha256(C.ROOT / register['path']) != register['sha256']:raise PilotError('the generic-identifier register differs from the snapshot')
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
            'bundle_verified': v['bundle_verified'], 'implementation': implementation_check(v['snapshot'])}


def implementation_check(snap, with_git=True):
    """Legacy snapshots carry no pin (NOT_PINNED_LEGACY); a pinned snapshot refuses any other implementation."""
    if not snap.get('graph_implementation'):return {'status': 'NOT_PINNED_LEGACY'}
    try:return I.verify(snap['graph_implementation'], with_git=with_git)
    except I.PinError as error:raise PilotError(str(error)) from error


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
    if snap.get('graph_implementation'):
        receipt['graph_implementation'] = {k: snap['graph_implementation'][k] for k in ('commit', 'tree_digest')}
        check = implementation_check(snap)  # the actual running commit, recorded with every query
        receipt['implementation_check'] = {'status': check['status'], 'running_commit': check['running_commit'],
                                           'dirty_pinned_paths': check.get('dirty_pinned_paths', [])}
        receipt['classification_rules'] = (snap.get('classification') or {}).get('rules', K.CLASSIFICATION_V1_1)
    return {'ledgers': ledgers, 'cuts': cuts, 'catalogue': v['catalogue'], 'mode': 'memory' if snap['fixture'] == 'LIVE' else 'synthetic',
            'receipt': receipt, 'snapshot': snap}


def arm_graph(snapshot, arm, query_at=None, now=None):
    """Graph v1 over exactly the arm's visible inputs. Only the graph arm uses it."""
    view = arm_view(snapshot, arm, query_at, now)
    pinned = view['snapshot'].get('graph_operator_version')
    if pinned not in (None, K.OPERATOR_VERSION):raise PilotError(f'the snapshot pins {pinned}; these operators are {K.OPERATOR_VERSION}')
    g = build(view['ledgers'], catalogue_path=view['catalogue'], mode=view['mode'], with_memory=True, cuts=view['cuts'])
    rules = (view['snapshot'].get('classification') or {}).get('rules', K.CLASSIFICATION_V1_1)
    K.use_rules(g, rules, K.load_register(C.ROOT / view['snapshot']['classification']['generic_register']['path'])
                if rules == K.CLASSIFICATION_V1_2 else None)
    if g.excluded or len(g.inputs) != 2 or not g.catalogue:raise PilotError(f'arm inputs incomplete: {g.excluded}')
    view['receipt']['graph_digest'] = g.digest()
    return g, view


# -- frozen suggestion export (V2) -------------------------------------------------------------------

def export_entries(doc):
    """Suggestions in one saved snapshot-mode output: a `suggestions` export or a suggesting operator's --json."""
    if 'suggestions' in doc:rows, command = [(s['operator'], s) for s in doc['suggestions']], 'suggestions'
    elif doc.get('operator') in SUGGESTING_OPERATORS:rows, command = [(doc['operator'], r) for r in doc['results']], doc['operator']
    else:raise PilotError(f'not a suggestion output; save the snapshot-mode JSON of one of {SUGGESTING_OPERATORS}')
    out = []
    for op, r in rows:
        if op == 'next':targets = r['open_claims'] + r['historical_investigations']
        else:targets = [r['match']]
        out.append({'suggestion_id': r['suggestion_id'], 'command': command, 'operator': op, 'target': r['target'], 'match': r['match'],
                    'match_bases': list(r['match_bases']), 'connection_class': r['connection_class'],
                    # same-gap and next link the arm's own record to a recorded claim; other operators fix both ends
                    'source_endpoints': None if op in ('same-gap', 'next') else [r['target']], 'target_endpoints': targets})
    return out


def replay(g, view, doc):
    """Re-run the saved query on the arm graph at its recorded query time (the graph is deterministic)."""
    from src.research.graph import evaluate as E
    from src.research.graph import operators as O
    from src.research.graph.rules import View
    if 'suggestions' in doc:return {'suggestions': E.export_suggestions(g, doc['input'], view['ledgers'], C.load(view['catalogue'])[0], None, view['cuts'])}
    v = View(**doc['view'])
    run = {'revisit': O.revisit, 'complements': O.complements, 'shared': O.shared, 'same-gap': O.same_gap}
    res = O.next_questions(g, v) if doc['operator'] == 'next' else run[doc['operator']](g, doc['input'], v)
    return json.loads(json.dumps(res, default=str))


def validate_execution_provenance(saved, snap, query_at, where, root=None):
    """Check the execution-provenance record saved with a query (its receipt's ``implementation_check``).

    Replay deliberately ignores this record, because a replay may run later at a content-identical unrelated commit; it is
    validated here instead. Malformed, removed, internally inconsistent or modified records are refused. What a passing
    record establishes, and what stays procedural, is returned with it (``PROVENANCE_ESTABLISHES`` / ``PROVENANCE_PROCEDURAL``)."""
    root = root or I.ROOT; pinned = snap.get('graph_implementation')
    if not pinned:return {'level': 'NOT_PINNED_LEGACY'}
    if saved is None:raise PilotError(f'{where}: the saved execution-provenance record (implementation_check) is missing')
    if not isinstance(saved, dict) or tuple(sorted(saved)) != tuple(sorted(PROVENANCE_KEYS)):
        raise PilotError(f'{where}: execution provenance must have exactly the fields {PROVENANCE_KEYS}')
    status, commit, dirty = saved['status'], saved['running_commit'], saved['dirty_pinned_paths']
    if status not in PROVENANCE_STATUSES:raise PilotError(f'{where}: execution provenance status {status!r} is not one of {PROVENANCE_STATUSES}')
    if not isinstance(dirty, list) or dirty != sorted(set(dirty)) or not set(dirty) <= set(pinned['files']):
        raise PilotError(f'{where}: dirty_pinned_paths must be a sorted list of pinned files')
    if status == 'GIT_UNAVAILABLE_CONTENT_VERIFIED':
        if commit != 'UNKNOWN' or dirty:raise PilotError(f'{where}: a query without git metadata names no running commit and no dirty paths')
        return {'level': 'NO_COMMIT_CLAIMED', 'status': status, 'running_commit': commit}
    if not re.fullmatch(r'[0-9a-f]{40}', str(commit)):raise PilotError(f'{where}: the saved running commit is not a 40-hex commit id')
    if (status == 'EXACT_COMMIT') != (commit == pinned['commit']):
        raise PilotError(f'{where}: status {status} is inconsistent with the running commit and the pinned commit')
    at = I.files_at_commit(root, commit, list(pinned['files']))
    if at is None:raise PilotError(f'{where}: the saved running commit {commit[:12]} is not in this repository (or git is unavailable here)')
    differing = sorted(p for p, d in pinned['files'].items() if at.get(p) != d)
    if differing != dirty:
        raise PilotError(f'{where}: the saved record declares uncommitted pinned paths {dirty}, but commit {commit[:12]} differs from the pin at {differing}')
    dated = I.commit_time(root, commit)
    if snap.get('fixture') == 'SYNTHETIC':date_check = 'NOT_APPLICABLE_SYNTHETIC_CLOCK'  # fixture query times are a fixed synthetic clock
    # No clock-skew allowance is registered: a commit dated even one second after the query is refused. (The human
    # attestation lag is a different rule and is deliberately not reused here.) Pilot machines need a synchronised clock.
    elif dated is None or parse_time(dated) > parse_time(query_at):
        raise PilotError(f'{where}: the saved running commit {commit[:12]} is dated after the query')
    else:date_check = 'COMMIT_DATED_BEFORE_QUERY'
    return {'level': 'COMMIT_CONSISTENT_WITH_PIN', 'status': status, 'running_commit': commit, 'dirty_pinned_paths': dirty, 'date_check': date_check,
            'establishes': PROVENANCE_ESTABLISHES, 'does_not_establish': PROVENANCE_PROCEDURAL}


def receipt_core(receipt):
    """A visibility receipt without its volatile fields: the arm ledger's total length and the running commit when saved
    (a replay may run later, at a content-identical unrelated commit). The saved running-commit record is validated
    separately by ``validate_execution_provenance``."""
    core = json.loads(json.dumps(receipt, default=str))
    core.get('own_ledger', {}).pop('events_total', None)
    core.pop('implementation_check', None)
    return core


def replayed_output(g, view, doc):
    """What the saved output must equal, field for field, apart from its visibility envelope (checked separately)."""
    if 'suggestions' in doc:return {'banner': M.BANNER, 'input': doc.get('input'), 'suggestions': json.loads(json.dumps(replay(g, view, doc)['suggestions']))}
    return replay(g, view, doc)


def load_suggestion_exports(files, snapshot):
    """The graph arm's frozen suggestion export: each saved output must belong to this packet snapshot and arm G, and must
    replay exactly from the snapshot at its recorded query time. Equality covers the whole saved output (results, grounded
    explanations, warnings, rejections, abstentions, notes and summary), not only the indexed suggestion fields, and the
    visibility receipt must equal the replayed receipt except the volatile arm-ledger length. Returns the suggestion index and a manifest of file hashes (sealed in the blinding key)."""
    from src.research.graph import operators as O
    v, index, manifest = load_snapshot(snapshot), {}, []
    for f in sorted(Path(x) for x in files):
        doc = json.loads(f.read_text(encoding='utf-8')); vis = doc.get('visibility') or {}
        if vis.get('arm') != 'G' or vis.get('snapshot_sha256') != v['sha256']:raise PilotError(f'{f.name}: not a graph-arm output for this packet snapshot')
        entries = export_entries(doc)
        provenance = validate_execution_provenance(vis.get('implementation_check'), v['snapshot'], vis['query_at_utc'], f.name)
        g, view = arm_graph(snapshot, 'G', vis['query_at_utc'])
        if receipt_core(vis) != receipt_core(view['receipt']):raise PilotError(f'{f.name}: visibility receipt differs from its snapshot replay')
        body, expected = {k: x for k, x in doc.items() if k != 'visibility'}, replayed_output(g, view, doc)
        if body != expected:
            fields = sorted(k for k in set(body) | set(expected) if body.get(k) != expected.get(k))
            raise PilotError(f'{f.name}: saved output differs from its snapshot replay in {fields}; the export was edited or produced elsewhere')
        for e in entries:
            if O.suggestion_id(e['operator'], e['target'], e['match'], e['match_bases']) != e['suggestion_id']:raise PilotError(f'{f.name}: {e["suggestion_id"]} does not recompute')
            allowed = {K.WARNING} if e['operator'] in ('same-gap', 'next') else {K.classify(e['match_bases'])}
            if getattr(g, 'classification', K.CLASSIFICATION_V1_1) == K.CLASSIFICATION_V1_2:
                allowed.add(K.classify([b for b in e['match_bases'] if b != 'EXACT_ENTITY_ID']))  # a generic identifier may not ground
            if e['connection_class'] not in allowed:raise PilotError(f'{f.name}: {e["suggestion_id"]} class differs from its bases')
            prev = index.get(e['suggestion_id'])
            e = dict(e, export=f.name, query_at_utc=vis['query_at_utc'], commands=sorted({e['command']} | set(prev['commands'] if prev else ())))
            if prev and parse_time(prev['query_at_utc']) <= parse_time(e['query_at_utc']):e = dict(prev, commands=e['commands'])  # earliest issue stands
            index[e['suggestion_id']] = e
        manifest.append({'path': Path(os.path.relpath(f.resolve(), Path(snapshot).resolve().parent)).as_posix(), 'sha256': sha256(f),
                         'query_at_utc': vis['query_at_utc'], 'suggestions': len(entries),
                         'execution_provenance': {k: provenance.get(k) for k in ('level', 'status', 'running_commit')}})
    return index, manifest


def default_exports(snapshot):
    d = Path(snapshot).parent / SUGGESTION_EXPORT_DIR
    return sorted(d.glob('*.json')) if d.is_dir() else []


def covers(suggested, logged):
    """A logged endpoint must be the suggested record, or a record inside a suggested campaign or investigation."""
    s, x = ref_key(suggested), ref_key(logged)
    return x == s or x.startswith(s + '/')


# -- arm connection logs ----------------------------------------------------------------------------

def graph_originated(r):
    return r['operator'] in GRAPH_OPERATORS or r['found_via'] in ('GRAPH_ONLY', 'BOTH') or r['connection_id'].startswith('SUG-')


def validate_v2_origin(r, w, arm, suggestions):
    """V2 traceability: a graph-originated row names the exact suggestion it came from, and that suggestion must be in the
    frozen export with the same operator, bases, class and endpoints, issued before the row was recorded."""
    if r['log_version'] != CONNECTION_LOG_V2:raise PilotError(f'{w}: unknown log_version {r["log_version"]}')
    if r['kind'] not in CONNECTION_KINDS_V2:raise PilotError(f'{w}: invalid kind')
    if not graph_originated(r):
        if r['origin_suggestion_id'] is not None or r['origin_operator'] is not None or r['origin_bases']:
            raise PilotError(f'{w}: only graph-originated rows carry suggestion origins')
    else:
        if arm == 'S':raise PilotError(f'{w}: the structured arm has no graph suggestions')
        if r['operator'] not in SUGGESTING_OPERATORS:
            raise PilotError(f'{w}: a graph-originated row comes from a suggestion-producing operator {SUGGESTING_OPERATORS}, not {r["operator"]}')
        if not re.fullmatch(r'SUG-[0-9a-f]{12}', str(r['origin_suggestion_id'])):raise PilotError(f'{w}: a graph-originated row keeps its SUG- origin id')
        if r['connection_id'].startswith('SUG-') and r['connection_id'] != r['origin_suggestion_id']:raise PilotError(f'{w}: a SUG- connection id is its origin id')
        if not r['origin_bases'] or r['connection_class'] not in K.CLASSES:
            raise PilotError(f'{w}: origin_operator, origin_bases and connection_class must record the originating suggestion')
        if r['kind'] == 'CONNECTION' and r['connection_class'] != K.ECONOMIC:
            raise PilotError(f'{w}: a {r["connection_class"]} cannot be logged as an economic connection; log it as METHODOLOGICAL_WARNING')
        if suggestions is None:
            raise PilotError(f'{w}: a graph-originated V2 row is checked against the frozen suggestion export; none was supplied')
        s = suggestions.get(r['origin_suggestion_id'])
        if s is None:raise PilotError(f'{w}: {r["origin_suggestion_id"]} is not in the frozen suggestion export')
        if r['origin_operator'] != s['operator'] or r['operator'] not in s['commands']:raise PilotError(f'{w}: origin operator differs from the originating suggestion')
        if list(r['origin_bases']) != s['match_bases'] or r['connection_class'] != s['connection_class']:
            raise PilotError(f'{w}: origin bases or class differ from the exported suggestion')
        if (s['source_endpoints'] is not None and not any(covers(e, r['source_record']) for e in s['source_endpoints'])) or \
                not any(covers(e, r['target_record']) for e in s['target_endpoints']):
            raise PilotError(f'{w}: endpoints are not those of the originating suggestion')
        if parse_time(r['recorded_at_utc']) < parse_time(s['query_at_utc']):raise PilotError(f'{w}: recorded before its originating suggestion was issued')
    if r['kind'] == 'METHODOLOGICAL_WARNING' and r['connection_class'] not in (K.WARNING, None):
        raise PilotError(f'{w}: a logged methodological warning has class {K.WARNING}')


def validate_connections(path, arm, suggestions=None, require_v2=False):
    """Every connection, warning or avoided repeat an arm considered, as the arm logged it during the campaign.

    Accepts V1 rows (as in R3) unchanged and prospective V2 rows. ``suggestions`` is the index from
    ``load_suggestion_exports``; every graph-originated V2 row is refused without it. ``require_v2`` (a packet snapshot
    frozen for V2 logs) refuses V1 rows, so origin checking cannot be avoided by logging in the old format."""
    rows, seen, index = read_jsonl(path), set(), suggestions
    for n, r in enumerate(rows, 1):
        w = f'{Path(path).name} line {n}'
        v2 = 'log_version' in r
        if require_v2 and not v2:raise PilotError(f'{w}: this packet was frozen for {CONNECTION_LOG_V2} logs; V1 rows are refused')
        keys = CONNECTION_KEYS_V2 if v2 else CONNECTION_KEYS
        if tuple(sorted(r)) != tuple(sorted(keys)):raise PilotError(f'{w}: fields must be exactly {keys}')
        if v2:validate_v2_origin(r, w, arm, index)
        if r['arm'] != arm:raise PilotError(f'{w}: logged by arm {r["arm"]}, expected {arm}')
        if not re.fullmatch(r'(SUG|CON)-[0-9a-f]{12}', r['connection_id']) or r['connection_id'] in seen:raise PilotError(f'{w}: invalid or repeated id')
        seen.add(r['connection_id'])
        if r['kind'] not in (CONNECTION_KINDS_V2 if v2 else CONNECTION_KINDS) or r['found_via'] not in FOUND_VIA or r['arm_decision'] not in ARM_DECISIONS:
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


def blind(snapshot, logs, salt, blind_out, key_out, suggestion_exports=None):
    """Prepare the adjudicator's export: shuffled, arm-hidden items with identical provenance rendering for both arms.

    Run by a session that is neither arm, after both arms of the packet finish. The key (blind id -> arm and
    connection id, plus the salt) is written separately and its hash recorded in the export, so it cannot be
    changed once adjudication begins. V2 graph rows are checked against the frozen suggestion export
    (default: ``suggestions-G/*.json`` beside the snapshot), whose file hashes are sealed in the key."""
    if not salt or len(salt) < 16:raise PilotError('the blinding salt needs at least 16 characters, chosen by the preparer and kept in the key')
    v = load_snapshot(snapshot); snap = v['snapshot']; cat = C.load(v['catalogue'])[0]
    files = default_exports(snapshot) if suggestion_exports is None else list(suggestion_exports)
    index, manifest = load_suggestion_exports(files, snapshot) if files else (None, [])
    attested = [{'path': f.name, 'sha256': sha256(f)} for arm in ARMS for e in SESSION_EVENTS if (f := session_path(Path(snapshot).parent, arm, e)).is_file()]
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

        for r in validate_connections(logs[arm], arm, index if arm == 'G' else None, snap.get('connection_log') == CONNECTION_LOG_V2):
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
    sealed = {'version': BLIND_VERSION, 'snapshot_sha256': v['sha256'], 'salt': salt, 'items': dict(sorted(key.items()))}
    if manifest:sealed['suggestion_exports'] = manifest  # private with the key: file names would reveal the graph arm
    if attested:sealed['session_attestations'] = attested  # sealed so a later edit of a START or STOP attestation is detected
    key_sha = write_new(key_out, sealed)
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


def unblind(packet_dir, export_name='blind.json', adjudications=None, rehearsal_single_log=False):
    """Join adjudications to arm logs through the sealed key, after adjudication is complete and committed.

    ``export_name`` selects the presentation the adjudicator used (``blind_v2.json`` for an aliased export); its
    blind ids and key seal are those of the original export.

    Legacy (V1) packets use the single ``adjudications.jsonl``. A prospective (V2) packet is unblinded only from the
    consensus of BOTH valid sealed reviewers (``adjudication.dual``), computed here; this tool offers no path to its
    outcomes before both seals exist. ``adjudications`` (a caller-supplied consensus) is accepted only for synthetic
    packets, in tests; ``rehearsal_single_log`` lets the Phase A synthetic rehearsal use one legacy log and is refused for
    live packets. These are software controls on this tool only: anyone with the files can read ``key.json``; keeping it
    unread until both seals are committed is procedural."""
    d = Path(packet_dir)
    export = json.loads((d / export_name).read_text(encoding='utf-8'))
    if sha256(d / 'key.json') != export['key_sha256']:raise PilotError('the key does not match the hash sealed in the blinded export')
    key = json.loads((d / 'key.json').read_text(encoding='utf-8'))
    # The sealed snapshot decides the log rules (V2-frozen or legacy V1); a missing or different snapshot is refused, never assumed V1.
    if not (d / 'snapshot.json').is_file() or sha256(d / 'snapshot.json') != key['snapshot_sha256']:
        raise PilotError('the packet snapshot is missing or differs from the one sealed in the key')
    snap = load_snapshot(d / 'snapshot.json')['snapshot']  # the same packet-ledger, catalogue and implementation checks as every other entry point
    if snap.get('connection_log') != CONNECTION_LOG_V2:
        if adjudications is None:adjudications = validate_adjudications(d / export_name, d / 'adjudications.jsonl')
    elif adjudications is not None:
        if snap['fixture'] != 'SYNTHETIC':raise PilotError('a live prospective packet is unblinded only from its sealed dual logs, never from supplied adjudications')
    else:
        from src.research.graph import adjudication as AD
        dual = AD.dual(d, export_name)
        if dual['status'] == 'DUAL_SEALED':adjudications = dual['adjudications']
        elif rehearsal_single_log and snap['fixture'] == 'SYNTHETIC':adjudications = validate_adjudications(d / export_name, d / 'adjudications.jsonl')
        else:raise PilotError('a prospective packet is unblinded only after both reviewers have sealed valid logs (pilot adjudication-agreement)')
    if set(adjudications) != set(key['items']):raise PilotError('the adjudications must cover exactly the blinded items')
    for m in key.get('session_attestations', []):
        if not (d / m['path']).is_file() or sha256(d / m['path']) != m['sha256']:raise PilotError(f"session attestation {m['path']} changed after blinding")
    index = None
    frozen_v2 = json.loads((d / 'snapshot.json').read_text(encoding='utf-8')).get('connection_log') == CONNECTION_LOG_V2
    if key.get('suggestion_exports'):
        for m in key['suggestion_exports']:
            if not (d / m['path']).is_file() or sha256(d / m['path']) != m['sha256']:raise PilotError(f"frozen suggestion export {m['path']} changed after blinding")
        index = load_suggestion_exports([d / m['path'] for m in key['suggestion_exports']], d / 'snapshot.json')[0]
    logs = {arm: {r['connection_id']: r for r in validate_connections(d / f'connections-{arm}.jsonl', arm, index if arm == 'G' else None, frozen_v2)} for arm in ARMS}
    rows = []
    for bid, ref in key['items'].items():
        r, a = logs[ref['arm']][ref['connection_id']], adjudications[bid]
        rows.append({'blind_id': bid, **{k: r[k] for k in ('arm', 'connection_id', 'kind', 'operator', 'found_via', 'arm_decision', 'analyst_minutes')},
                     **{k: r.get(k) for k in ('log_version', 'origin_suggestion_id', 'connection_class')},
                     **{k: a[k] for k in ('outcome', 'economic_meaning', 'adjudicator_minutes')},
                     **({'usefulness': a['usefulness']} if 'usefulness' in a else {})})
    if len(rows) != sum(len(x) for x in logs.values()):raise PilotError('every logged connection must appear in the blinded export')
    return rows


# -- aliased presentation (BLIND_V2) and recursive leak scanning --------------------------------------
# V001 exports copied arm-chosen record ids and free text verbatim, so ids such as OBS-G-7 (or an arm's
# distinctive id style) could identify the arm. V2 is derived from an unchanged V001 export: every record id
# of the arm's own campaign, wherever it appears, becomes an opaque per-item alias; campaign ids, archive
# paths and branch names become neutral placeholders. Blind ids, order, evidence hashes and the key seal are
# unchanged, so the sealed mapping and any adjudication template stay valid.

ALIAS_VERSION = 'GRAPH_PILOT_BLIND_V2_ALIASED'
RECORD_TOKEN = re.compile(r'\b(?:SRC|OBS|REL|CAND|REV|DSP|EFF)-[A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*')  # never a trailing '.' or '-'
PACKET_RECORD = re.compile(r'^(?:SRC|OBS|REL)-P-\d+$')
NEUTRAL = ((re.compile(r'\bDLC-G?P\d+-[SG]\b'), 'CURRENT_ARM_CAMPAIGN'), (re.compile(r'/(P\d+)/[SG]/'), r'/\1/ARM/'),
           (re.compile(r'graph-pilot(?:-r3)?/P\d+-[SG]\b'), 'ARM_BRANCH'))
LEAK_PATTERNS = (
    ('ARM_LETTER_RECORD_ID', re.compile(r'\b(?:SRC|OBS|REL|CAND|REV|DSP|EFF)-[SG](?:[.-][A-Za-z0-9_]+)*\b')),
    ('ARM_CAMPAIGN_ID', re.compile(r'\bDLC-G?P\d+-[SG]\b')),
    ('ARM_PATH', re.compile(r'/P\d+/[SG]/')),
    ('ARM_BRANCH', re.compile(r'graph-pilot(?:-r3)?/P\d+-[SG]\b')),
    ('ARM_LABEL', re.compile(r'\b(?:[SG] arm|arm [SG]|structured arm|graph arm)\b', re.I)),
    ('PILOT_CONNECTION_ID', re.compile(r'\b(?:SUG|CON)-[0-9a-f]{12}\b')),
    ('ATTRIBUTION_OR_DECISION', re.compile(r'\b(?:GRAPH_ONLY|BASELINE_SEARCH_DISCOVERABLE|ANALYST_READING|ACCEPTED|DECLINED)\b')),
    ('TOOL_WORD', re.compile(r'\b(?:graph|suggestions?|baseline|baseline-search|revisit|complements)\b', re.I)))


def strings(value, path='$'):
    """Every string (keys and values) in a nested JSON value, with its path."""
    if isinstance(value, str):yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield f'{path}.<key>', str(k); yield from strings(v, f'{path}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):yield from strings(v, f'{path}[{i}]')


def scan_leaks(value, own_records=()):
    """Arm-identifying strings anywhere in a nested value (or a text): patterns plus any listed own-arm record id."""
    found, own = [], set(own_records)
    for path, s in (strings(value) if not isinstance(value, str) else [('$text', value)]):
        for code, pat in LEAK_PATTERNS:
            found += [{'path': path, 'code': code, 'match': m.group(0)} for m in pat.finditer(s)]
        found += [{'path': path, 'code': 'OWN_ARM_RECORD_ID', 'match': m.group(0)} for m in RECORD_TOKEN.finditer(s) if m.group(0) in own]
    return found


def own_records(export):
    return sorted({i[e]['record'] for i in export['items'] for e in ('from', 'to') if i[e]['campaign'] == 'CURRENT_ARM_CAMPAIGN'})


def alias_item(item, secret):
    own = {item[e]['record'] for e in ('from', 'to') if item[e]['campaign'] == 'CURRENT_ARM_CAMPAIGN'}
    aliases, bid = {}, item['blind_id']

    def alias(token):
        if PACKET_RECORD.match(token) and token not in own:return token
        if token not in aliases:
            digest_ = hashlib.sha256(f'{secret}|{bid}|{token}'.encode()).hexdigest()[:8]
            aliases[token] = f"{token.split('-', 1)[0]}-A{digest_}"
        return aliases[token]

    def rewrite(value, key=None):
        if isinstance(value, dict):return {k: rewrite(v, k) for k, v in value.items()}
        if isinstance(value, list):return [rewrite(v) for v in value]
        if not isinstance(value, str) or key in ('blind_id', 'sha256', 'kind', 'campaign', 'depth'):return value
        out = RECORD_TOKEN.sub(lambda m: alias(m.group(0)), value)
        for pat, repl in NEUTRAL:out = pat.sub(repl, out)
        return out

    return rewrite(item), aliases


def alias_export(blind_path, out, alias_key_out, secret=None):
    """Write the versioned aliased presentation of an unchanged V001 export, refusing if any leak remains."""
    import secrets as _secrets
    src = Path(blind_path); export = json.loads(src.read_text(encoding='utf-8'))
    if export.get('version') != BLIND_VERSION:raise PilotError(f'aliasing derives from a {BLIND_VERSION} export')
    secret = secret or _secrets.token_hex(16)
    items, maps = [], {}
    for i in export['items']:
        new, aliases = alias_item(i, secret); items.append(new); maps[i['blind_id']] = aliases
    leaks = scan_leaks(items)
    if leaks:raise PilotError(f'aliased items still leak: {leaks[:5]}')
    key_sha = write_new(alias_key_out, {'version': ALIAS_VERSION, 'derived_from_sha256': sha256(src), 'secret': secret, 'aliases': maps})
    v2 = {'version': ALIAS_VERSION, 'packet': export['packet'], 'fixture': export['fixture'], 'snapshot_sha256': export['snapshot_sha256'],
          'key_sha256': export['key_sha256'], 'derived_from': {'path': src.name, 'sha256': sha256(src), 'version': BLIND_VERSION,
                                                               'presentation_status': 'COMPROMISED: arm-identifying record ids and id styles were visible'},
          'alias_key_sha256': key_sha,
          'aliasing': ['every record id of the current arm campaign, in any field or text, is an opaque per-item alias (kind prefix kept)',
                       'frozen-packet (SRC/OBS/REL-P-n) and historical (HIST-) references are unchanged',
                       'campaign ids, archive paths and branch names are neutral placeholders',
                       'blind ids, item order, evidence hashes, dates, values, periods and texts are otherwise unchanged'],
          'hidden_from_adjudicator': export['hidden_from_adjudicator'],
          'instructions': export['instructions'] + ['Aliases are per item: the same alias in two items is not implied to be the same record.'],
          'items': items, 'leak_scan': {'patterns': [c for c, _ in LEAK_PATTERNS] + ['OWN_ARM_RECORD_ID'], 'findings': 0}}
    write_new(out, v2)
    return v2


def sheet(export):
    """Readable adjudication sheet: only fields present in the export, every item in export order."""
    L = [f"# Packet {export['packet']}: blinded adjudication sheet ({export['version']})", '',
         f"{len(export['items'])} items, shuffled. Arm, operator, attribution, decision, minutes and notes are hidden"
         + ('; record ids of the current campaign are per-item aliases.' if export['version'] == ALIAS_VERSION else '.'), '',
         'For each item record **outcome** (`CONFIRMED_AGAINST_ORIGINALS` with the evidence hashes or locators you checked, `PLAUSIBLE_UNVERIFIED`, '
         '`REJECTED_FALSE`, `REJECTED_TRIVIAL`) and **economic meaning** (`MEANINGFUL`, `NOT_MEANINGFUL`, `UNCLEAR`).', '']
    for n, i in enumerate(export['items'], 1):
        L += [f"## {n}. `{i['blind_id']}` ({i['kind']})", '']
        if i.get('avoided_action'):L.append('- **Avoided action:** ' + '; '.join(i['avoided_action']))
        for label in ('from', 'to'):
            x = i[label]
            L += [f"- **{label.title()}:** {x['kind']} `{x['campaign']}/{x['record']}`", f"  - Text: {x['text']}"]
            if x['entities']:L.append('  - Entities: ' + '; '.join(f"`{a['id']}` ({a['name']})" for a in x['entities']))
            for k in ('value', 'units', 'occurred', 'depth', 'type', 'period', 'basis', 'status', 'outcome'):
                if k in x:L.append(f'  - {k}: {x[k]}')
            for ev in x['evidence']:
                L.append(f"  - Evidence: `{ev['locator']}` depth {ev['depth']}" + (f", sha256 `{ev['sha256']}`" if ev['sha256'] else '')
                         + (f" — \"{ev['passage']}\"" if ev.get('passage') else ''))
        s = i['shared_structure']
        L += [f"- **Mechanical shared structure:** same identified entity {s['same_identified_entity'] or 'none'}; shared document hashes "
              f"{len(s['shared_document_hashes'])}; shared requirement tags {s['shared_requirement_tags'] or 'none'}"
              + (f"; relationship period covers observation: {s['relationship_period_covers_observation']}" if 'relationship_period_covers_observation' in s else ''), '']
    return '\n'.join(L) + '\n'


# -- budget accounting and outcomes -----------------------------------------------------------------

def account(ledger, arm):
    """Effort by pilot category against the per-campaign ceilings. Unknown minutes stay UNKNOWN, never zero."""
    s = ledger if not isinstance(ledger, (str, Path)) else Ledger(ledger).load()
    by, unknown_by, violations = {c: 0 for c in CATEGORIES}, {c: 0 for c in CATEGORIES}, []
    for e in s.efforts:
        found = CATEGORY_TAG.findall(e['description'])
        cat = found[0] if len(found) == 1 and found[0] in CATEGORIES else None
        if cat is None:violations.append({'effort': e['id'], 'code': 'UNCATEGORISED_EFFORT'})
        elif e['analyst_minutes'] != R.UNKNOWN:by[cat] += e['analyst_minutes']
        else:unknown_by[cat] += 1
        if arm == 'S' and cat in GRAPH_CATEGORIES:violations.append({'effort': e['id'], 'code': 'GRAPH_TIME_IN_STRUCTURED_ARM'})
        if e['kind'] == 'SEARCH' and cat != 'SOURCE_SEARCH':violations.append({'effort': e['id'], 'code': 'SEARCH_NOT_CATEGORISED_SOURCE_SEARCH'})
    t = totals(s.efforts)
    used = {'analyst_minutes': t['analyst_minutes']['known'], 'source_starts': t['source_starts']['known'],
            'searches': sum(e['kind'] == 'SEARCH' for e in s.efforts), 'bytes': t['bytes']['known']}
    for k, limit in CEILINGS.items():
        if used[k] > limit:violations.append({'code': 'OVER_CAMPAIGN_CEILING', 'field': k, 'used': used[k], 'ceiling': limit})
    unknown = {k: t[k]['unknown_entries'] for k in ('analyst_minutes', 'source_starts', 'bytes')}
    return {'campaign': s.campaign['id'], 'arm': arm, 'minutes_by_category': by, 'unknown_entries_by_category': unknown_by,
            'graph_minutes': sum(by[c] for c in GRAPH_CATEGORIES), 'graph_minutes_unknown_entries': sum(unknown_by[c] for c in GRAPH_CATEGORIES),
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
    graph_items = [r for r in conn if r['connection_id'].startswith('SUG-') or r.get('origin_suggestion_id')]
    warnings = [r for r in mine if r['kind'] == 'METHODOLOGICAL_WARNING']
    traced = [r for r in mine if r.get('origin_suggestion_id')]  # V2 graph rows of every kind; warnings are never hidden from the count
    by_class = {c: [sum(r['outcome'] in ('REJECTED_FALSE', 'REJECTED_TRIVIAL') for r in traced if r['connection_class'] == c),
                    sum(r['connection_class'] == c for r in traced)] for c in K.CLASSES if any(r['connection_class'] == c for r in traced)}
    m = original_m_passes(s); falsify = decisive_minutes(s)
    adj = [r['adjudicator_minutes'] for r in mine]; adj_unknown = sum(x == R.UNKNOWN for x in adj)
    review_unknown = acc['unknown_entries_by_category']['SUGGESTION_REVIEW']
    total = lambda known, unknown: R.UNKNOWN if unknown else known  # an incomplete total is UNKNOWN, never a partial sum
    return {'campaign': s.campaign['id'], 'analyst_minutes_all': minutes,
            'graph_minutes': total(acc['graph_minutes'], acc['graph_minutes_unknown_entries']), 'graph_minutes_known': acc['graph_minutes'],
            'graph_minutes_unknown_entries': acc['graph_minutes_unknown_entries'],
            'verified_connections': len(verified), 'verified_connections_per_hour': per_hour(len(verified), minutes),
            'graph_only_verified': sum(r['found_via'] == 'GRAPH_ONLY' for r in verified),
            'false_or_premature_joins_made': sum(r['arm_decision'] == 'ACCEPTED' and r['outcome'] in ('REJECTED_FALSE', 'PLAUSIBLE_UNVERIFIED') for r in conn),
            'false_joins_declined': sum(r['arm_decision'] == 'DECLINED' and r['outcome'] == 'REJECTED_FALSE' for r in conn),
            'true_connections_declined': sum(r['arm_decision'] != 'ACCEPTED' and confirmed(r) for r in conn),
            'median_minutes_per_connection': median([r['analyst_minutes'] for r in conn]),
            'median_minutes_per_connection_excluded_unknown': sum(r['analyst_minutes'] == R.UNKNOWN for r in conn),
            'median_minutes_to_decisive_falsification': median(falsify.values()), 'decisive_falsification': falsify,
            'median_minutes_to_decisive_falsification_excluded': sum(v in (R.UNKNOWN, 'NOT_NAMED') for v in falsify.values()),
            'duplicate_research_avoided': sum(r['kind'] == 'AVOIDED_REPEAT' and r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS' for r in mine),
            'methodological_warnings_logged': len(warnings),
            'methodological_warnings_confirmed_useful': sum(r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS' for r in warnings),
            'review_burden_items': len(mine),
            'adjudicator_minutes': total(sum(x for x in adj if x != R.UNKNOWN), adj_unknown),
            'adjudicator_minutes_known': sum(x for x in adj if x != R.UNKNOWN), 'adjudicator_minutes_unknown_entries': adj_unknown,
            'suggestion_review_minutes': total(acc['minutes_by_category']['SUGGESTION_REVIEW'], review_unknown),
            'suggestion_review_minutes_known': acc['minutes_by_category']['SUGGESTION_REVIEW'], 'suggestion_review_minutes_unknown_entries': review_unknown,
            'graph_suggestions_false_or_trivial': [sum(r['outcome'] in ('REJECTED_FALSE', 'REJECTED_TRIVIAL') for r in graph_items), len(graph_items)],
            'graph_rows_false_or_trivial_by_class': by_class,
            'original_frozen_m_passes': m, 'original_frozen_m_passes_per_hour': per_hour(m, minutes),
            'h_plausible_human': sum(1 for r in s.reviews if r['kind'] == 'H' and r['judgments']['judgment'] == 'PLAUSIBLE'
                                     and R.human_equivalent(r['reviewer']['kind'], s.fixture)),
            'budget_violations': acc['violations'], **dual_metrics(mine, conn, warnings)}


USEFULNESS_CATEGORIES = ('USEFUL_LESSON_REUSED', 'USEFUL_NOT_USED', 'NOT_USEFUL', 'CANNOT_ASSESS', 'UNRESOLVED_DISAGREEMENT')


def dual_metrics(mine, conn, warnings):
    """Phase B (dual-reviewer consensus rows only): avoided-repetition usefulness, kept apart from economic confirmation."""
    if not any('usefulness' in r for r in mine):return {}
    assessed = [r for r in mine if r.get('usefulness') is not None]
    reused = lambda rows: sum(r['usefulness'] == 'USEFUL_LESSON_REUSED' for r in rows)
    avoided = [r for r in assessed if r['kind'] == 'AVOIDED_REPEAT']
    return {'duplicate_research_avoided': reused(avoided),  # both reviewers: the lesson changed or avoided a stated action
            'methodological_warnings_confirmed_useful': reused([r for r in warnings if r.get('usefulness') is not None]),
            'warning_usefulness': {'assessed': len(assessed), **{c: sum(r['usefulness'] == c for r in assessed) for c in USEFULNESS_CATEGORIES},
                                   'reused_share': ratio(reused(assessed), len(assessed)),
                                   'note': 'avoided-repetition usefulness; never an economic discovery'},
            'unresolved_disagreements': sum(r['outcome'] == 'UNRESOLVED_DISAGREEMENT' or r['economic_meaning'] == 'UNRESOLVED_DISAGREEMENT' for r in conn)}


# Benefit dimensions (direction of improvement); review burden is reported as a cost, never as a benefit.
DIMENSIONS = (('verified_connections_per_hour', 'higher'), ('false_or_premature_joins_made', 'lower'), ('median_minutes_per_connection', 'lower'),
              ('median_minutes_to_decisive_falsification', 'lower'), ('duplicate_research_avoided', 'higher'),
              ('original_frozen_m_passes_per_hour', 'higher'))
COSTS = (('review_burden_items', 'lower'), ('adjudicator_minutes', 'lower'))


def direction(g, s, better):
    if g in (None, R.UNKNOWN) or s in (None, R.UNKNOWN):return 'NOT_COMPARABLE'
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


# -- R4 readiness: timestamp-derived effort ------------------------------------------------------------
#
# Registered primary measure (proposed for R4 activation): analyst effort is the self-reported minutes of the arm's effort
# records (all categories, graph time included), as in revisions 2 and 3. Elapsed time is evidence about those minutes, not a
# replacement: a session or record span contains idle time, interruptions and waiting that cannot be separated from research
# work, and it misses work done before the first or after the last record. Derived elapsed time is therefore used only to
# check the self-reported minutes and, where operator-attested session bounds exist for every arm, as a sensitivity
# denominator. Gap durations are listed descriptively and never subtracted.

def minutes_between(a, b):
    return round((b - a).total_seconds() / 60, 2)


def compare_minutes(reported, derived):
    """Owner policy: a discrepancy is material when it exceeds the greater of 5 minutes or 10% of the derived comparator.
    The absolute and percentage differences are always reported, including smaller ones."""
    diff = round(reported - derived, 2)
    threshold = round(max(EFFORT_DISCREPANCY['minutes'], EFFORT_DISCREPANCY['share'] * derived), 2)
    return {'derived_minutes': derived, 'self_reported_minutes': reported, 'difference_minutes': diff,
            'difference_percent': round(100 * diff / derived, 1) if derived else 'UNDEFINED_ZERO_DENOMINATOR',
            'material_threshold_minutes': threshold, 'material': abs(diff) > threshold, 'rule': 'GREATER_OF_5_MINUTES_OR_10_PERCENT'}


def session_path(packet_dir, arm, event):
    return Path(packet_dir) / f'session-{arm}-{event.lower()}.json'


def check_attester(name, kind, fixture):
    allowed = ('HUMAN', 'SYNTHETIC_FIXTURE') if fixture == 'SYNTHETIC' else ('HUMAN',)
    if kind not in allowed or not name or not str(name).strip():raise PilotError('session times are attested by the human arm operator personally')
    if ASSISTANT_NAME.search(str(name)):raise PilotError(f'assistant self-attestation is refused ({name!r})')


def attest_session(packet_dir, arm, event, name, kind='HUMAN', now=None):
    """The human operator's own immutable attestation, written at the moment the arm session starts or stops."""
    d = Path(packet_dir); snap = load_snapshot(d / 'snapshot.json')['snapshot']
    if arm not in ARMS or event not in SESSION_EVENTS:raise PilotError(f'arm is one of {ARMS}; event is one of {SESSION_EVENTS}')
    check_attester(name, kind, snap['fixture'])
    if event == 'STOP' and not session_path(d, arm, 'START').is_file():raise PilotError('a STOP attestation needs its START attestation')
    t = utc(now).isoformat()
    doc = {'version': SESSION_VERSION, 'packet': snap['packet'], 'arm': arm, 'event': event, 'at_utc': t, 'recorded_at_utc': t,
           'recorded_by': {'name': name, 'kind': kind},
           'statement': f"I personally {'started' if event == 'START' else 'stopped'} the arm {arm} session at this time."}
    try:write_new(session_path(d, arm, event), doc)
    except FileExistsError as error:raise PilotError(f'the {event} attestation for arm {arm} already exists and is immutable') from error
    return doc


def load_attestation(path, packet, arm, event, fixture):
    s = json.loads(Path(path).read_text(encoding='utf-8')); w = Path(path).name
    if tuple(sorted(s)) != tuple(sorted(SESSION_KEYS)) or s['version'] != SESSION_VERSION:raise PilotError(f'{w}: fields must be exactly {SESSION_KEYS}')
    if (s['packet'], s['arm'], s['event']) != (packet, arm, event):raise PilotError(f'{w}: attests {s["packet"]}/{s["arm"]}/{s["event"]}, expected {packet}/{arm}/{event}')
    check_attester(s['recorded_by'].get('name'), s['recorded_by'].get('kind'), fixture)
    at, written = parse_time(s['at_utc']), parse_time(s['recorded_at_utc'])
    if not 0 <= minutes_between(at, written) <= ATTESTATION_LAG_MINUTES:
        raise PilotError(f'{w}: an attestation is written when its event occurs (within {ATTESTATION_LAG_MINUTES} minutes)')
    return s, at, written


def sessions(packet_dir, arm, snap, first, last):
    """Operator-attested session bounds, or a status saying why they cannot be used. Never inferred from records."""
    d, problems = Path(packet_dir), []
    start_p, stop_p = session_path(d, arm, 'START'), session_path(d, arm, 'STOP')
    if not start_p.is_file() and not stop_p.is_file():return {'status': 'NOT_RECORDED', 'minutes': R.UNKNOWN}
    if not start_p.is_file():return {'status': 'CONTRADICTORY', 'minutes': R.UNKNOWN, 'problems': ['STOP attested without a START']}
    _, start, start_written = load_attestation(start_p, snap['packet'], arm, 'START', snap['fixture'])
    if not stop_p.is_file():return {'status': 'INCOMPLETE_NO_STOP', 'started_at_utc': start.isoformat(), 'minutes': R.UNKNOWN}
    _, stop, stop_written = load_attestation(stop_p, snap['packet'], arm, 'STOP', snap['fixture'])
    if start < parse_time(snap['frozen_at_utc']):problems.append('session started before the packet freeze')
    if stop <= start:problems.append('STOP is not after START')
    if start_written > first + timedelta(minutes=ATTESTATION_LAG_MINUTES):problems.append('START attested after the arm had begun recording')
    if stop_written < last:problems.append('STOP attested before the last arm record')
    out = {'status': 'CONTRADICTORY' if problems else 'RECORDED', 'started_at_utc': start.isoformat(), 'stopped_at_utc': stop.isoformat(),
           'minutes': minutes_between(start, stop) if stop > start else R.UNKNOWN, 'attestations': [start_p.name, stop_p.name]}
    if problems:out['problems'] = problems
    return out


def effort_evidence(e):
    """CONSISTENT, INCOMPLETE, MATERIAL_DISCREPANCY or CONTRADICTORY: how far the self-reported minutes are supported."""
    codes = {f['code'] for f in e['flags']}
    if codes & {'SESSION_CONTRADICTORY', 'SELF_REPORTED_EXCEEDS_SESSION', 'ACTIVITY_OUTSIDE_SESSION'}:return 'CONTRADICTORY'
    if codes & {'EFFORT_DISCREPANCY', 'EFFORT_EXCEEDS_APPEND_INTERVAL', 'GRAPH_MINUTES_EXCEED_OBSERVED_WINDOWS', 'GRAPH_TIME_WITHOUT_RECORDED_QUERIES',
                'GRAPH_QUERIES_WITHOUT_GRAPH_TIME'}:return 'MATERIAL_DISCREPANCY'
    if codes & {'SELF_REPORTED_MINUTES_UNKNOWN', 'SESSION_BOUNDS_NOT_RECORDED', 'SESSION_INCOMPLETE'}:return 'INCOMPLETE'
    return 'CONSISTENT'


def derived_effort(packet_dir, arm):
    """Elapsed-time evidence for one arm campaign from recorded timestamps, beside its self-reported minutes (the primary measure).

    Timestamps used: every arm ledger append, every connection-log row, every graph query in the frozen suggestion
    export (arm G), and the operator's START/STOP attestations (``session-<arm>-start.json``, ``-stop.json``). These bound
    elapsed time; they do not measure effort. Idle time between records cannot be separated, and work before the first or
    after the last record is not observed, so nothing is inferred there: missing evidence is reported as UNKNOWN."""
    d = Path(packet_dir); v = load_snapshot(d / 'snapshot.json'); snap = v['snapshot']
    s = Ledger(d / snap['arms'][arm]['ledger']).load(); acc = account(s, arm)
    # Human decisions recorded in the arm ledger (dispositions; M/H reviews by a human) come after the campaign by protocol: not arm activity.
    human = lambda e: e['type'] == 'disposition' or (e['type'] == 'review' and R.human_equivalent(e['record']['reviewer']['kind'], s.fixture))
    excluded = [e for e in s.events if human(e)]
    times = [(parse_time(e['recorded_at_utc']), f"ledger:{e['type']}") for e in s.events if not human(e)]
    log = d / f'connections-{arm}.jsonl'
    if log.is_file():times += [(parse_time(r['recorded_at_utc']), 'connection_log') for r in read_jsonl(log)]
    queries = []
    if arm == 'G':
        for f in default_exports(d / 'snapshot.json'):
            vis = json.loads(f.read_text(encoding='utf-8')).get('visibility') or {}
            if vis.get('query_at_utc'):queries.append(parse_time(vis['query_at_utc']))
        times += [(q, 'graph_query') for q in queries]
    times.sort(key=lambda x: x[0]); flags = []
    first, last = times[0][0], times[-1][0]
    span = minutes_between(first, last)
    gaps = [{'after': a[1], 'at_utc': a[0].isoformat(), 'minutes': minutes_between(a[0], b[0])} for a, b in zip(times, times[1:])
            if minutes_between(a[0], b[0]) > LONG_GAP_MINUTES]
    reported, unknown = acc['used']['analyst_minutes'], acc['unknown_entries']['analyst_minutes']
    if unknown:flags.append({'code': 'SELF_REPORTED_MINUTES_UNKNOWN', 'entries': unknown})
    session = sessions(d, arm, snap, first, last)
    if session['status'] == 'NOT_RECORDED':flags.append({'code': 'SESSION_BOUNDS_NOT_RECORDED'})
    elif session['status'] == 'INCOMPLETE_NO_STOP':flags.append({'code': 'SESSION_INCOMPLETE'})
    elif session['status'] == 'CONTRADICTORY':flags.append({'code': 'SESSION_CONTRADICTORY', 'problems': session['problems']})
    if session.get('stopped_at_utc') and session['minutes'] != R.UNKNOWN:
        start, stop = parse_time(session['started_at_utc']), parse_time(session['stopped_at_utc'])
        outside = [label for t_, label in times if t_ < start or t_ > stop]
        if outside:flags.append({'code': 'ACTIVITY_OUTSIDE_SESSION', 'records': len(outside)})
    comparisons = {'observed_span': {**compare_minutes(reported, span), 'complete': not unknown}}
    if session['status'] == 'RECORDED':
        comparisons['session'] = {**compare_minutes(reported, session['minutes']), 'complete': not unknown}
        if reported > session['minutes'] + comparisons['session']['material_threshold_minutes']:
            flags.append({'code': 'SELF_REPORTED_EXCEEDS_SESSION', 'self_reported': reported, 'session': session['minutes']})
    # The session is the comparator when attested; otherwise the observed span, whose shortfall may be legitimate unrecorded work.
    comparator = 'session' if 'session' in comparisons else 'observed_span'
    c = comparisons[comparator]
    flags.append({'code': 'EFFORT_DISCREPANCY' if c['material'] else 'EFFORT_DIFFERENCE_BELOW_THRESHOLD', 'against': comparator,
                  'difference_minutes': c['difference_minutes'], 'difference_percent': c['difference_percent']})
    # Per effort: an effort covers the work since the previous effort (or the campaign start), so its claimed minutes cannot exceed
    # that interval by more than a minute when efforts are logged as the work completes (the R4 rule).
    over, previous = [], parse_time(s.events[0]['recorded_at_utc'])
    for e in s.events[1:]:
        if e['type'] != 'effort':continue
        at = parse_time(e['recorded_at_utc'])
        if e['record']['analyst_minutes'] != R.UNKNOWN:
            interval = minutes_between(previous, at)
            if e['record']['analyst_minutes'] > interval + 1:over.append({'effort': e['record']['id'], 'claimed': e['record']['analyst_minutes'], 'interval': interval})
        previous = at
    if over:flags.append({'code': 'EFFORT_EXCEEDS_APPEND_INTERVAL', 'efforts': len(over)})
    graph = {'self_reported_minutes': acc['graph_minutes'], 'by_category': {c_: acc['minutes_by_category'][c_] for c_ in GRAPH_CATEGORIES}}
    if arm == 'G':
        later = [t_ for t_, _ in times]
        windows = [minutes_between(q, next((t_ for t_ in later if t_ > q), q)) for q in sorted(queries)]
        graph.update({'queries_recorded': len(queries), 'review_window_minutes_upper_bound': round(sum(windows), 2)})
        if queries and not acc['graph_minutes']:flags.append({'code': 'GRAPH_QUERIES_WITHOUT_GRAPH_TIME', 'queries': len(queries)})
        if snap.get('connection_log') == CONNECTION_LOG_V2 and acc['graph_minutes'] and not queries:flags.append({'code': 'GRAPH_TIME_WITHOUT_RECORDED_QUERIES'})
        if queries and compare_minutes(acc['graph_minutes'], sum(windows))['material'] and acc['graph_minutes'] > sum(windows):
            flags.append({'code': 'GRAPH_MINUTES_EXCEED_OBSERVED_WINDOWS', 'self_reported': acc['graph_minutes'], 'windows': round(sum(windows), 2)})
    else:
        graph.update({'queries_recorded': 'NOT_APPLICABLE'})
    out = {'campaign': s.campaign['id'], 'arm': arm, 'first_record_utc': first.isoformat(), 'last_record_utc': last.isoformat(),
           'timestamps': len(times), 'excluded_human_decision_records': {k: sum(e['type'] == k for e in excluded) for k in ('review', 'disposition')},
           'observed_span_minutes': span, 'long_gaps': gaps, 'gap_policy': 'DESCRIPTIVE_ONLY: listed, never subtracted from effort',
           'session': session, 'self_reported': {'analyst_minutes': reported, 'unknown_entries': unknown, 'by_category': acc['minutes_by_category']},
           'primary_measure': 'SELF_REPORTED_ANALYST_MINUTES', 'comparator': comparator, 'comparisons': comparisons, 'graph_time': graph,
           'efforts_exceeding_append_interval': over, 'flags': flags,
           'threshold': f"material when |self-reported - derived| > the greater of {EFFORT_DISCREPANCY['minutes']} minutes or "
                        f"{int(EFFORT_DISCREPANCY['share'] * 100)}% of the derived comparator; smaller differences are still reported",
           'interpretation': 'Derived values bound elapsed time between recorded actions; they are not measured effort. Idle time inside the span '
                             'is not separable, and work before the first or after the last record is unobserved.'}
    out['effort_evidence'] = effort_evidence(out)
    return out


# -- R4 readiness: full suggestion accounting -------------------------------------------------------------

def ratio(numerator, denominator):
    if numerator == R.UNKNOWN or denominator == R.UNKNOWN:return {'numerator': numerator, 'denominator': denominator, 'value': R.UNKNOWN}
    return {'numerator': numerator, 'denominator': denominator,
            'value': round(numerator / denominator, 4) if denominator else 'UNDEFINED_ZERO_DENOMINATOR'}


ADJUDICATED = ('CONFIRMED_AGAINST_ORIGINALS', 'PLAUSIBLE_UNVERIFIED', 'REJECTED_FALSE', 'REJECTED_TRIVIAL')
FALSE_OR_TRIVIAL = ('REJECTED_FALSE', 'REJECTED_TRIVIAL')


def suggestion_decision(decisions):
    """One suggestion logged in several rows: ANY_ACCEPTED, ALL_DECLINED, or UNRESOLVED_OR_MIXED (no acceptance)."""
    if 'ACCEPTED' in decisions:return 'ANY_ACCEPTED'
    return 'ALL_DECLINED' if decisions == {'DECLINED'} else 'UNRESOLVED_OR_MIXED'


def suggestion_accounting(packet_dir, adjudicated_rows=None):
    """Every graph suggestion of arm G, by class, at two separate levels with compatible numerators and denominators:

    * suggestion level (unique origin ids): exported, logged, exported but unlogged, decision pattern, adjudicated;
    * row level (connection-log rows, several of which may share one origin): rows by kind and decision, adjudicated.

    Adjudication outcomes are joined per row (connection id), never overwritten by origin. ``adjudicated_rows`` (from
    ``unblind``) adds outcomes; without it they are NOT_ADJUDICATED. Legacy V1 packets cannot trace suggestions
    (NOT_TRACEABLE_V1); a V2 packet without its export is V2_EXPORT_MISSING and its exported counts are UNKNOWN, never
    zero. Warnings are never counted as discoveries."""
    d = Path(packet_dir); snap = load_snapshot(d / 'snapshot.json')['snapshot']
    v2 = snap.get('connection_log') == CONNECTION_LOG_V2
    log = d / 'connections-G.jsonl'
    rows = read_jsonl(log) if log.is_file() else []
    key = json.loads((d / 'key.json').read_text(encoding='utf-8')) if (d / 'key.json').is_file() else {}
    files = [d / m['path'] for m in key['suggestion_exports']] if key.get('suggestion_exports') else default_exports(d / 'snapshot.json')
    if not v2:
        traceability, index = 'NOT_TRACEABLE_V1', None
    elif not files:
        traceability, index = 'V2_EXPORT_MISSING', None
    else:
        traceability, index = 'V2_FROZEN_EXPORT', load_suggestion_exports(files, d / 'snapshot.json')[0]
    if index is not None and log.is_file():validate_connections(log, 'G', index, True)
    traced = [r for r in rows if r.get('origin_suggestion_id')]
    judged = {r['connection_id']: r for r in (adjudicated_rows or []) if r.get('arm') == 'G' and r.get('origin_suggestion_id')}
    out, totals_ = {}, {}
    for c in K.CLASSES:
        exported = R.UNKNOWN if index is None else sum(e['connection_class'] == c for e in index.values())
        mine = [r for r in traced if r['connection_class'] == c]
        by_origin = {}
        for r in mine:by_origin.setdefault(r['origin_suggestion_id'], []).append(r)
        unlogged = R.UNKNOWN if index is None else sum(1 for e in index.values() if e['connection_class'] == c and e['suggestion_id'] not in by_origin)
        patterns = {k: 0 for k in ('ANY_ACCEPTED', 'ALL_DECLINED', 'UNRESOLVED_OR_MIXED')}
        for group in by_origin.values():patterns[suggestion_decision({r['arm_decision'] for r in group})] += 1
        rows_by_decision = {k: sum(r['arm_decision'] == k for r in mine) for k in ARM_DECISIONS}
        entry = {'exported': exported, 'logged_suggestions': len(by_origin), 'exported_unlogged': unlogged, 'suggestions_by_decision': patterns,
                 'logged_rows': len(mine), 'rows_by_kind': {k: sum(r['kind'] == k for r in mine) for k in CONNECTION_KINDS_V2},
                 'rows_by_decision': rows_by_decision, 'rows_sharing_an_origin': sum(len(g_) for g_ in by_origin.values() if len(g_) > 1),
                 'rates': {'logged_share_of_exported_suggestions': ratio(len(by_origin), exported),
                           'unlogged_share_of_exported_suggestions': ratio(unlogged, exported),
                           'all_declined_share_of_logged_suggestions': ratio(patterns['ALL_DECLINED'], len(by_origin)),
                           'declined_share_of_logged_rows': ratio(rows_by_decision['DECLINED'], len(mine))}}
        if adjudicated_rows is None:entry['adjudicated'] = 'NOT_ADJUDICATED'
        else:
            row_out = [judged[r['connection_id']] for r in mine if r['connection_id'] in judged]
            groups = [[judged[r['connection_id']]['outcome'] for r in g_ if r['connection_id'] in judged] for g_ in by_origin.values()]
            groups = [g_ for g_ in groups if g_]
            entry['adjudicated'] = {'rows': {o: sum(r['outcome'] == o for r in row_out) for o in ADJUDICATED}, 'rows_adjudicated': len(row_out),
                                    'suggestions_adjudicated': len(groups),
                                    'suggestions_with_any_false_or_trivial': sum(any(o in FALSE_OR_TRIVIAL for o in g_) for g_ in groups),
                                    'suggestions_with_conflicting_outcomes': sum(len(set(g_)) > 1 for g_ in groups)}
            a = entry['adjudicated']
            entry['rates']['false_or_trivial_share_of_adjudicated_rows'] = ratio(sum(a['rows'][o] for o in FALSE_OR_TRIVIAL), a['rows_adjudicated'])
            entry['rates']['any_false_or_trivial_share_of_adjudicated_suggestions'] = ratio(a['suggestions_with_any_false_or_trivial'], a['suggestions_adjudicated'])
        out[c] = entry
    for k in ('exported', 'logged_suggestions', 'exported_unlogged', 'logged_rows'):
        vals = [out[c][k] for c in K.CLASSES]
        totals_[k] = R.UNKNOWN if R.UNKNOWN in vals else sum(vals)
    confirmed = lambda r: r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS'
    discoveries = [r for r in judged.values() if r['connection_class'] == K.ECONOMIC and r['kind'] == 'CONNECTION'
                   and r['arm_decision'] == 'ACCEPTED' and confirmed(r) and r['economic_meaning'] == 'MEANINGFUL']
    warnings_ = [r for r in judged.values() if r['connection_class'] == K.WARNING and (r.get('usefulness') == 'USEFUL_LESSON_REUSED' if 'usefulness' in r else confirmed(r))]
    legacy_graph_rows = [r for r in rows if not r.get('origin_suggestion_id') and r['operator'] in GRAPH_OPERATORS]
    pending = 'NOT_ADJUDICATED'
    return {'packet': snap['packet'], 'arm': 'G', 'traceability': traceability, 'by_class': out, 'totals': totals_,
            'confirmed_economic_discoveries': {'rows': len(discoveries) if adjudicated_rows is not None else pending,
                                               'distinct_origin_suggestions': len({r['origin_suggestion_id'] for r in discoveries}) if adjudicated_rows is not None else pending,
                                               'rule': 'ECONOMIC_CONNECTION_CANDIDATE + CONNECTION + ACCEPTED + CONFIRMED_AGAINST_ORIGINALS + MEANINGFUL'},
            'methodological_warnings_confirmed': {'rows': len(warnings_) if adjudicated_rows is not None else pending,
                                                  'note': 'reusable research memory; never counted as an economic discovery'},
            'untraced_graph_operator_rows': len(legacy_graph_rows),
            'structured_arm': 'NOT_APPLICABLE: arm S has no graph suggestions'}


# -- paired report: primary measure, sensitivity and effort evidence --------------------------------------------

DEFINITIVE = ('GRAPH_INCREMENT_OBSERVED', 'NO_GRAPH_INCREMENT_OBSERVED')


def with_minutes(packets, basis):
    """Packets with the per-hour dimensions recomputed on a derived denominator, or None where any arm lacks one."""
    out = []
    for p in packets:
        q = dict(p)
        for arm in ARMS:
            e = p['effort_check'][arm]
            minutes = (e['session']['minutes'] if e['session']['status'] == 'RECORDED' else None) if basis == 'session' else e['observed_span_minutes']
            if minutes in (None, R.UNKNOWN) or not minutes:return None
            m = dict(p[arm]); m['analyst_minutes_all'] = minutes
            m['verified_connections_per_hour'] = per_hour(m['verified_connections'], minutes)
            m['original_frozen_m_passes_per_hour'] = per_hour(m['original_frozen_m_passes'], minutes)
            q[arm] = m
        out.append(q)
    return out


def report(packet_dirs, critical_stops=(), export_name='blind.json'):
    """Paired per-packet outcomes for every dimension, the cost of the increment, and the proposed classification.

    The registered primary measure is self-reported analyst minutes. A definitive classification also requires the effort
    evidence to support it: either every arm's effort evidence is CONSISTENT, or no arm is CONTRADICTORY and the
    classification is unchanged under the attested-session sensitivity denominator. Otherwise it is reported as
    INCONCLUSIVE (EFFORT_EVIDENCE_UNRESOLVED), with the primary result shown beside it. The observed-span sensitivity is
    descriptive only and never supports a classification."""
    from src.research.graph import adjudication as AD
    packets, prospective = [], False
    for d in map(Path, packet_dirs):
        snap = load_snapshot(d / 'snapshot.json')['snapshot']
        v2 = snap.get('connection_log') == CONNECTION_LOG_V2
        prospective = prospective or v2
        dual = AD.dual(d, export_name) if v2 else None
        sealed = (not v2) or dual['status'] == 'DUAL_SEALED'
        rows = unblind(d, export_name) if sealed else None  # a prospective packet is never unblinded before both seals
        effort = {arm: derived_effort(d, arm) for arm in ARMS}
        packet = {'packet': snap['packet'], 'method': snap['prior']['packet_ledger']['method'],
                  **({arm: arm_metrics(Ledger(d / snap['arms'][arm]['ledger']).load(), arm, rows) for arm in ARMS} if sealed else
                     {'outcomes': 'NOT_UNBLINDED: both reviewers must seal valid logs first'}),
                  'effort_check': effort, 'effort_evidence': {arm: effort[arm]['effort_evidence'] for arm in ARMS},
                  'suggestion_accounting': suggestion_accounting(d, rows)}
        if v2:
            packet['conformance'] = AD.conformance(d, snap, dual)
            packet['adjudication'] = {k: dual[k] for k in dual if k != 'adjudications'}
        packets.append(packet)
    for p in packets:
        if 'G' in p:p['directions'] = {name: direction(p['G'][name], p['S'][name], better) for name, better in DIMENSIONS + COSTS}
    # Explicit cohort boundary. A report with no prospective packet is a pure legacy report and behaves exactly as before.
    # Once any prospective (R4) packet is present, the primary cohort is R4-conforming packets only: a legacy packet has no
    # R4 conformance and never enters it (or counts towards its minimum of three pairs); it stays listed, with its metrics.
    if prospective:
        primary_packets = [p for p in packets if 'conformance' in p and p['conformance']['status'] == 'CONFORMING']
        excluded = [{'packet': p['packet'], 'problems': p['conformance']['problems'], 'deviations': p['conformance']['deviations']} if 'conformance' in p
                    else {'packet': p['packet'], 'problems': ['LEGACY_PACKET_OUTSIDE_R4_PRIMARY_COHORT'], 'deviations': []}
                    for p in packets if p not in primary_packets]
    else:
        primary_packets, excluded = packets, []
    final, primary, sensitivity, notes = final_classification(primary_packets, critical_stops, prospective)
    blinding = blinding_sensitivity(primary_packets, critical_stops) if prospective else None
    if blinding and blinding['gate'] == 'UNRESOLVED' and final in DEFINITIVE:
        notes = notes + [f"BLINDING_SENSITIVITY_UNRESOLVED: excluding potentially unblinded packets gives {blinding['classification']}"]; final = 'INCONCLUSIVE'
    if prospective:
        notes = notes + [f'{len(primary_packets)} conforming packet pair(s) in the primary comparison; {len(excluded)} excluded and listed.']
        if any(p['conformance']['potentially_unblinded'] for p in primary_packets):notes.append('POTENTIALLY_UNBLINDED: a reviewer declared arm-identifying exposure.')
    return {'banner': M.BANNER, 'scope': 'PILOT_PAIRED_REPORT', 'prospective': prospective, 'packets': packets, 'classification': final,
            'excluded_from_primary': excluded, 'classification_primary': primary, 'blinding_sensitivity': blinding,
            'classification_sensitivity': sensitivity, 'effort_evidence_summary': sorted({v for p in packets for v in p['effort_evidence'].values()}),
            'notes': notes}


def blinding_sensitivity(primary_packets, critical_stops=()):
    """Proposed policy (to register before any R4 outcome): POTENTIALLY_UNBLINDED packets stay in the primary analysis,
    labelled; a sensitivity excludes every packet with any such item. If the two classifications differ, no definitive
    classification is reported (INCONCLUSIVE). The treatment is fixed here, before outcomes, never chosen afterwards."""
    flagged = [p['packet'] for p in primary_packets if p['conformance']['potentially_unblinded']]
    if not flagged:return {'potentially_unblinded_packets': [], 'classification': 'NOT_APPLICABLE', 'gate': 'NOT_APPLICABLE'}
    kept = [p for p in primary_packets if not p['conformance']['potentially_unblinded']]
    alt = classify(kept, critical_stops)[0]
    primary = classify(primary_packets, critical_stops)[0]
    return {'potentially_unblinded_packets': flagged, 'packets_after_exclusion': len(kept), 'classification': alt,
            'gate': 'CONSISTENT' if alt == primary else 'UNRESOLVED'}


def final_classification(packets, critical_stops=(), prospective=True):
    """Primary classification on self-reported minutes, sensitivities on derived denominators, and the effort-evidence gate.

    The gate and its notes apply to prospective (V2) packets. Legacy packets (the R2 dry run, R3) keep their original
    classification and notes exactly; their effort evidence and sensitivities are returned as data only."""
    primary, notes = classify(packets, critical_stops)
    sensitivity = {}
    for basis in ('session', 'observed_span'):
        alt = with_minutes(packets, basis)
        sensitivity[basis] = classify(alt, critical_stops)[0] if alt else 'NOT_VALID: a derived denominator is missing for some arm'
    evidence = [v for p in packets for v in p['effort_evidence'].values()]
    if not prospective:return primary, primary, sensitivity, notes
    final, effort_note = primary, None
    if primary in DEFINITIVE:
        if all(v == 'CONSISTENT' for v in evidence):effort_note = 'effort evidence CONSISTENT for every arm'
        elif 'CONTRADICTORY' not in evidence and sensitivity['session'] == primary:
            effort_note = 'effort evidence incomplete or discrepant, but the classification is unchanged under the attested-session sensitivity'
        else:
            final = 'INCONCLUSIVE'
            effort_note = (f'EFFORT_EVIDENCE_UNRESOLVED: the primary measure gives {primary}, but effort evidence is '
                           f'{sorted(set(evidence))} and the session sensitivity gives {sensitivity["session"]}')
    notes = notes + ([effort_note] if effort_note else []) + [
        'Primary measure: self-reported analyst minutes. Elapsed session or record time is not active research effort (it includes idle time, '
        'interruptions and waiting, and misses unrecorded work); it is used to check the primary measure and as a sensitivity only.']
    return final, primary, sensitivity, notes


def markdown(rep):
    names = [n for n, _ in DIMENSIONS + COSTS]
    head = [f"**Effort evidence: {', '.join(rep['effort_evidence_summary'])}.** Primary classification {rep['classification_primary']}; "
            f"session sensitivity {rep['classification_sensitivity']['session']}; observed-span sensitivity (descriptive) "
            f"{rep['classification_sensitivity']['observed_span']}.", ''] if rep.get('prospective') else []
    lines = ['| Packet | Dimension | S | G | Better |', '|---|---|---:|---:|---|']
    for p in rep['packets']:
        if 'G' not in p:
            lines.append(f"| {p['packet']} ({p['method']}) | outcomes | {p['outcomes']} | | |"); continue
        for n in names:lines.append(f"| {p['packet']} ({p['method']}) | {n} | {p['S'][n]} | {p['G'][n]} | {p['directions'][n]} |")
        lines.append(f"| {p['packet']} | analyst minutes (all; graph) | {p['S']['analyst_minutes_all']} | {p['G']['analyst_minutes_all']} "
                     f"({p['G']['graph_minutes']} graph) | |")
        if rep.get('prospective'):lines.append(f"| {p['packet']} | effort evidence | {p['effort_evidence']['S']} | {p['effort_evidence']['G']} | |")
    return '\n'.join(head + lines + ['', f"Classification (proposed rule): **{rep['classification']}**", '', *[f'- {n}' for n in rep['notes']]])
