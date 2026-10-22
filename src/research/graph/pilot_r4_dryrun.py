"""Graph Pilot R4 readiness, Phase A: a synthetic end-to-end rehearsal with mutation checks. NOT an R4 run.

It exercises the three Phase A requirements on fictional fixtures, offline, in a temporary directory:
exact implementation pinning (against a throwaway git copy of the pinned set), timestamp-derived effort,
and full suggestion accounting, through V2 snapshot, graph queries, the frozen suggestion export, V2 logs,
blinding, aliasing, a labelled synthetic adjudication stand-in, unblinding and the paired report.
Each mutation must be refused or flagged. No source is fetched, no real campaign or adjudication runs, and
nothing here activates R4.

Regenerate the record only with ``python -m src.research.graph pilot r4-dry-run --write``; ``--check`` compares.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import contextlib
import io
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from src.research.discovery.demo import passport
from src.research.discovery.ledger import Ledger
from src.research.graph import catalogue as C
from src.research.graph import cli as GCLI
from src.research.graph import evaluate as E
from src.research.graph import implementation as I
from src.research.graph import model as M
from src.research.graph import operators as O
from src.research.graph import pilot as P
from src.research.graph import pilot_dryrun as DR
from src.research.graph.rules import View

ROOT = I.ROOT
RECORD = ROOT / 'docs/strategy/graph_pilot_r4_dry_run.md'
SALT = 'r4-readiness-rehearsal-salt-0001'
GIT_ENV = {'GIT_AUTHOR_DATE': '2026-10-21T12:00:00+00:00', 'GIT_COMMITTER_DATE': '2026-10-21T12:00:00+00:00'}


def git(directory, *args):
    env = {**os.environ, **GIT_ENV}
    return subprocess.run(['git', '-c', 'user.name=Synthetic pin', '-c', 'user.email=synthetic-pin@example.invalid', '-c', 'core.autocrlf=false',
                           '-C', str(directory), *args], capture_output=True, text=True, check=True, env=env, timeout=120)


def remove_tree(path):
    """Delete a temporary tree, including git's read-only object files on Windows."""
    def retry(func, target, _):
        os.chmod(target, stat.S_IWRITE); func(target)
    if Path(path).exists():shutil.rmtree(path, onexc=retry)


def pinned_copy(directory, root=ROOT):
    """Copy the pinned implementation set into a fresh git repository with one fixed-date commit."""
    d = Path(directory); d.mkdir(parents=True, exist_ok=True)
    for rel in I.closure(root)[0]:
        (d / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(Path(root) / rel, d / rel)
    git(d, 'init', '-q'); git(d, 'add', '-A'); git(d, 'commit', '-q', '-m', 'Synthetic pinned copy of the Graph implementation')
    return d


_PINS = {}


def synthetic_pin(root=ROOT):
    """A real pin of the current implementation content, taken from a clean throwaway git copy (cached by content)."""
    key = I.content(root)['tree_digest']
    if key not in _PINS:
        tmp = Path(tempfile.mkdtemp(prefix='graph-pin-'))
        try:_PINS[key] = I.pin(pinned_copy(tmp / 'impl', root))
        finally:remove_tree(tmp)
    return _PINS[key]


class Checks:
    def __init__(self):self.rows = []

    def ok(self, area, name, passed, observed):
        self.rows.append({'area': area, 'check': name, 'observed': observed, 'result': 'PASS' if passed else 'FAIL'})

    def refused(self, area, name, fn, contains, error=(P.PilotError, I.PinError)):
        try:fn()
        except error as exc:
            self.ok(area, name, contains in str(exc), f'refused: {contains}' if contains in str(exc) else f'refused for another reason: {exc}')
            return
        self.ok(area, name, False, 'NOT refused')


def pinning(c, d):
    """Requirement 1 against a throwaway git copy: what passes, what refuses."""
    impl = pinned_copy(d / 'impl'); pin = I.pin(impl)
    c.ok('pin', 'a clean checkout pins commit and content', I.verify(pin, impl)['status'] == 'EXACT_COMMIT', I.verify(pin, impl)['status'])
    target = impl / 'src/research/graph/connections.py'; original = target.read_bytes()
    target.write_bytes(original.replace(b'\n', b'\r\n'))
    v = I.verify(pin, impl)
    c.ok('pin', 'CRLF-only checkout differences verify (normalised), and are reported as dirty',
         v['status'] == 'EXACT_COMMIT' and v['dirty_pinned_paths'] == ['src/research/graph/connections.py'], f"{v['status']}; dirty {v['dirty_pinned_paths']}")
    c.refused('pin', 'a dirty pinned set cannot be pinned', lambda: I.pin(impl), 'uncommitted changes')
    target.write_bytes(original + b'# edited\n')
    c.refused('pin', 'a changed implementation file refuses verification', lambda: I.verify(pin, impl), "'changed': ['src/research/graph/connections.py']")
    target.write_bytes(original)
    extra = impl / 'src/research/graph/extra_module.py'; extra.write_text('X = 1\n', encoding='utf-8')
    c.refused('pin', 'an added implementation file refuses verification', lambda: I.verify(pin, impl), "'added': ['src/research/graph/extra_module.py']")
    extra.unlink()
    (impl / 'unrelated').mkdir(); (impl / 'unrelated/notes.md').write_text('Unrelated change.\n', encoding='utf-8')
    git(impl, 'add', '-A'); git(impl, 'commit', '-q', '-m', 'Unrelated documentation change')
    c.ok('pin', 'an unrelated commit with identical implementation passes as UNRELATED_COMMIT_CHANGE',
         I.verify(pin, impl)['status'] == 'UNRELATED_COMMIT_CHANGE', I.verify(pin, impl)['status'])
    bare = d / 'no-git'
    for rel in I.closure(impl)[0]:(bare / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(impl / rel, bare / rel)
    c.refused('pin', 'missing git metadata cannot be pinned', lambda: I.pin(bare), 'git metadata is unavailable')
    c.ok('pin', 'missing git metadata at verification still enforces content', I.verify(pin, bare)['status'] == 'GIT_UNAVAILABLE_CONTENT_VERIFIED',
         I.verify(pin, bare)['status'])
    boundary = {'src/research/sec_pilot/parsing.py', 'docs/strategy/graph_pilot/fetch_one.py', 'src/research/spec.py'}
    c.ok('pin', 'the boundary includes the R4 fetch tool and the offline guard (static import closure)', boundary <= set(pin['files']),
         f"{sorted(boundary & set(pin['files']))}")
    c.ok('pin', 'the pin records Python and dependency versions', set(pin['runtime']) == {'python', 'implementation', 'dependencies'},
         f"Python recorded; {len(pin['runtime']['dependencies'])} distributions recorded")
    other = dict(pin, runtime=dict(pin['runtime'], python='0.0.0'))
    c.refused('pin', 'a different Python or dependency version refuses verification', lambda: I.verify(other, impl), 'the runtime differs')
    return pin


def packet(c, d, clock, pin):
    """A V2 packet frozen with the pin; legacy and tampered snapshots."""
    pk = d / 'P1'
    led = Ledger.create(pk / 'packet.jsonl', DR.campaign('DLC-GR4PKT', 'R4 rehearsal packet'), clock)
    led.append('source', passport('SRC-P-1', 'register', field='t', units='kt/month', publication='VERIFIED_ORIGINAL_RECORD'))
    led.append('observation', DR.observation('OBS-P-1', 'Quay One throughput fell.', {'from': 410, 'to': 265}, 'kt/month',
                                              DR.doc('bundle/x', b'x'), 'STATE_CHANGE', source='SRC-P-1'))
    led.append('relationship', DR.relationship('REL-P-1'))
    bundle = d / 'bundle'; bundle.mkdir(); (bundle / 'x.csv').write_bytes(b'x')
    clock.advance(1); frozen = clock.at(); clock.advance(2)
    arms = {'S': (pk / 'S.jsonl', 'DLC-GR4-S'), 'G': (pk / 'G.jsonl', 'DLC-GR4-G')}
    P.make_snapshot(pk / 'snapshot.json', 'P1', pk / 'packet.jsonl', arms, bundle, frozen_at=frozen, connection_log=P.CONNECTION_LOG_V2, implementation=pin)
    snap = json.loads((pk / 'snapshot.json').read_text(encoding='utf-8'))
    c.ok('pin', 'the V2 snapshot binds commit, content digest and operator version',
         set(snap['graph_implementation']) >= {'commit', 'tree_digest', 'files'} and snap['graph_operator_version'] == 'GRAPH_OPERATORS_V1_1',
         f"commit, tree digest and per-file digests ({'src/research/graph/pilot.py' in snap['graph_implementation']['files']}); {snap['graph_operator_version']}")
    c.ok('pin', 'the running implementation matches the pin (content check on every query)',
         P.implementation_check(snap, with_git=False)['status'] == 'CONTENT_VERIFIED', P.implementation_check(snap, with_git=False)['status'])
    P.make_snapshot(d / 'legacy' / 'snapshot.json', 'P1', pk / 'packet.jsonl', {'S': (d / 'legacy/S.jsonl', 'DLC-GR4-S'), 'G': (d / 'legacy/G.jsonl', 'DLC-GR4-G')},
                    bundle, frozen_at=frozen)
    legacy = json.loads((d / 'legacy/snapshot.json').read_text(encoding='utf-8'))
    c.ok('legacy', 'a legacy (non-V2) snapshot carries no pin and is not checked', P.implementation_check(legacy)['status'] == 'NOT_PINNED_LEGACY',
         P.implementation_check(legacy)['status'])
    return pk, bundle


def tamper_checks(c, pk):
    snap = json.loads((pk / 'snapshot.json').read_text(encoding='utf-8'))
    when = Ledger(pk / 'G.jsonl').load().events[-1]['recorded_at_utc']  # a valid query time: only the pin can refuse it
    tampered = {**snap, 'graph_implementation': {**snap['graph_implementation'], 'tree_digest': '0' * 64,
                                                 'files': {**snap['graph_implementation']['files'], 'src/research/graph/operators.py': '0' * 64}}}
    (pk / 'tampered.json').write_text(json.dumps(tampered), encoding='utf-8')
    unpinned = {k: v for k, v in snap.items() if k != 'graph_implementation'}
    (pk / 'unpinned.json').write_text(json.dumps(unpinned), encoding='utf-8')
    c.refused('pin', 'a snapshot pinned to another implementation refuses every arm query', lambda: P.arm_graph(pk / 'tampered.json', 'G', when),
              "'changed': ['src/research/graph/operators.py']")
    c.refused('pin', 'a V2 snapshot without a pin is refused', lambda: P.load_snapshot(pk / 'unpinned.json'), 'must pin the Graph implementation')


def effort(eid, category, minutes, kind='ANALYST_TIME'):
    return DR.effort(eid, category, minutes, kind)


def arms(pk, clock):
    """S logs honestly except one inflated effort; G logs as it works and saves each graph query."""
    s = Ledger.create(pk / 'S.jsonl', DR.campaign('DLC-GR4-S', 'S arm'), clock); s_start = clock.t
    s.append('source', passport('SRC-1', 'notices', field='b', units='berths', publication='VERIFIED_ORIGINAL_RECORD'))
    s.append('observation', DR.observation('OBS-1', 'Quay One berths closed.', 3, 'berths', DR.doc('arm/n', DR.NOTICE), 'EVENT',
                                           '[MEASURES:REQ_REALISED_ACTIVITY] closure'))
    clock.advance(5); s.append('effort', effort('EFF-S-1', 'READING', 6))
    clock.advance(5); s.append('effort', effort('EFF-S-2', 'BASELINE_SEARCH', 40))  # inflated: about 6 minutes elapsed
    s_end = clock.t
    clock.advance(2)
    g = Ledger.create(pk / 'G.jsonl', DR.campaign('DLC-GR4-G', 'G arm'), clock); g_start = clock.t
    g.append('source', passport('SRC-1', 'notices', field='b', units='berths', publication='VERIFIED_ORIGINAL_RECORD'))
    g.append('observation', DR.observation('OBS-1', 'Quay One berths closed.', 3, 'berths', DR.doc('arm/n', DR.NOTICE), 'EVENT',
                                           '[MEASURES:REQ_REALISED_ACTIVITY] closure'))
    g.append('effort', effort('EFF-G-0', 'RECORDING', 3))  # recording the source and observation
    query = clock.at(); gg, view = P.arm_graph(pk / 'snapshot.json', 'G', query)
    receipt = json.loads(json.dumps(view['receipt']))
    outputs = {'001-suggestions.json': {'banner': M.BANNER, 'input': 'DLC-GR4-G', 'visibility': receipt,
                                        'suggestions': E.export_suggestions(gg, 'DLC-GR4-G', view['ledgers'], C.load(view['catalogue'])[0], None, view['cuts'])},
               '002-same-gap.json': json.loads(json.dumps({**O.same_gap(gg, 'REQ_REALISED_ACTIVITY', View()), 'visibility': receipt}, default=str))}
    for name, doc_ in outputs.items():
        (pk / P.SUGGESTION_EXPORT_DIR).mkdir(exist_ok=True); (pk / P.SUGGESTION_EXPORT_DIR / name).write_text(json.dumps(doc_, indent=1), encoding='utf-8')
    clock.advance(3); g.append('effort', effort('EFF-G-1', 'GRAPH_QUERY', 4))
    clock.advance(4); g.append('effort', effort('EFF-G-2', 'SUGGESTION_REVIEW', 5))
    clock.advance(3); g.append('effort', effort('EFF-G-3', 'READING', 4))
    g_end = clock.t
    return {'S': (s_start, s_end), 'G': (g_start, g_end)}


OPERATOR = 'Synthetic operator stand-in (fixture)'


def attest(pk, arm, bounds):
    """The operator stand-in attests START as the campaign opens and STOP after its last record (separate immutable files)."""
    start, stop = bounds
    P.attest_session(pk, arm, 'START', OPERATOR, 'SYNTHETIC_FIXTURE', now=start)
    P.attest_session(pk, arm, 'STOP', OPERATOR, 'SYNTHETIC_FIXTURE', now=stop)


def logs(pk, bounds):
    index, _ = P.load_suggestion_exports(P.default_exports(pk / 'snapshot.json'), pk / 'snapshot.json')
    at = (bounds['G'][1] - timedelta(seconds=30)).isoformat()  # logged inside the G campaign, after its query
    s_at = (bounds['S'][1] - timedelta(seconds=30)).isoformat()
    econ = sorted((e for e in index.values() if e['connection_class'] == 'ECONOMIC_CONNECTION_CANDIDATE'), key=lambda e: e['match'])
    warn = sorted((e for e in index.values() if e['operator'] == 'same-gap'), key=lambda e: e['match'])[0]

    def row(e, decision, record=None, **change):
        r = {'connection_id': e['suggestion_id'], 'arm': 'G', 'kind': 'CONNECTION' if e['connection_class'] == 'ECONOMIC_CONNECTION_CANDIDATE' else 'METHODOLOGICAL_WARNING',
             'operator': e['commands'][0], 'found_via': 'GRAPH_ONLY', 'source_record': e['target'] if e['source_endpoints'] else 'DLC-GR4-G/OBS-1',
             'target_record': e['target_endpoints'][0], 'basis': list(e['match_bases']), 'arm_decision': decision, 'analyst_minutes': 2,
             'discovery_lab_record': record, 'recorded_at_utc': at, 'notes': 'synthetic rehearsal', 'log_version': P.CONNECTION_LOG_V2,
             'origin_suggestion_id': e['suggestion_id'], 'origin_operator': e['operator'], 'origin_bases': list(e['match_bases']),
             'connection_class': e['connection_class']}
        return {**r, **change}
    rel = next(e for e in econ if 'REL-P-1' in e['match']); same = next(e for e in econ if 'OBS-P-1' in e['match'])
    second = row(same, 'UNRESOLVED', connection_id=P.connection_id(same['target'], same['target_endpoints'][0], ['second look at the same suggestion']),
                 basis=['second look at the same suggestion'])  # a second row sharing one origin
    g_rows = [row(rel, 'ACCEPTED', 'EFF-G-3'), row(same, 'DECLINED'), second, row(warn, 'UNRESOLVED')]
    s_rows = [{'connection_id': P.connection_id('DLC-GR4-S/OBS-1', 'DLC-GR4PKT/REL-P-1', ['EXACT_ENTITY_ID']), 'arm': 'S', 'kind': 'CONNECTION',
               'operator': 'baseline-search', 'found_via': 'ANALYST_READING', 'source_record': 'DLC-GR4-S/OBS-1', 'target_record': 'DLC-GR4PKT/REL-P-1',
               'basis': ['EXACT_ENTITY_ID'], 'arm_decision': 'DECLINED', 'analyst_minutes': 3, 'discovery_lab_record': None,
               'recorded_at_utc': s_at, 'notes': 'synthetic rehearsal', 'log_version': P.CONNECTION_LOG_V2, 'origin_suggestion_id': None,
               'origin_operator': None, 'origin_bases': [], 'connection_class': None}]
    for arm, rows in (('S', s_rows), ('G', g_rows)):
        (pk / f'connections-{arm}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    return index


def effort_checks(c, pk, bounds, legacy):
    attest(pk, 'S', bounds['S']); attest(pk, 'G', bounds['G'])
    g, s = P.derived_effort(pk, 'G'), P.derived_effort(pk, 'S')
    codes = lambda e: sorted({f['code'] for f in e['flags']})
    c.ok('effort', 'contemporaneous G logging: no material discrepancy; the difference is still reported; evidence CONSISTENT',
         'EFFORT_DISCREPANCY' not in codes(g) and 'EFFORT_DIFFERENCE_BELOW_THRESHOLD' in codes(g) and g['effort_evidence'] == 'CONSISTENT',
         f"session {g['session']['minutes']} vs self {g['self_reported']['analyst_minutes']} ({g['comparisons']['session']['difference_minutes']} min, "
         f"{g['comparisons']['session']['difference_percent']}%); {g['effort_evidence']}")
    small = P.compare_minutes(54, 50)
    c.ok('effort', 'material threshold is the greater of 5 minutes or 10% of the comparator; smaller differences are reported',
         small['material'] is False and small['difference_minutes'] == 4 and P.compare_minutes(130, 120)['material'] is False
         and P.compare_minutes(133, 120)['material'] is True,
         f"54 vs 50: {small['difference_minutes']} min / {small['difference_percent']}%, threshold {small['material_threshold_minutes']}; 133 vs 120 material")
    c.ok('effort', 'graph query and suggestion-review time are reported where measurable',
         g['graph_time']['queries_recorded'] == 2 and g['graph_time']['self_reported_minutes'] == 9 and 'GRAPH_MINUTES_EXCEED_OBSERVED_WINDOWS' not in codes(g),
         f"{g['graph_time']['queries_recorded']} recorded queries; {g['graph_time']['self_reported_minutes']} self-reported graph minutes; "
         f"review windows <= {g['graph_time']['review_window_minutes_upper_bound']} min")
    c.ok('effort', 'an inflated S effort is flagged against the session and its append interval; evidence CONTRADICTORY',
         {'EFFORT_DISCREPANCY', 'EFFORT_EXCEEDS_APPEND_INTERVAL', 'SELF_REPORTED_EXCEEDS_SESSION'} <= set(codes(s)) and s['effort_evidence'] == 'CONTRADICTORY',
         f"session {s['session']['minutes']} vs self {s['self_reported']['analyst_minutes']}; {s['effort_evidence']}")
    c.ok('effort', 'long gaps are descriptive only and never subtracted', s['gap_policy'].startswith('DESCRIPTIVE_ONLY'), s['gap_policy'])
    held = {e: pk / f'session-S-{e.lower()}.hold' for e in P.SESSION_EVENTS}
    for e in P.SESSION_EVENTS:P.session_path(pk, 'S', e).rename(held[e])
    s2 = P.derived_effort(pk, 'S')
    c.ok('effort', 'missing session attestations are reported, never inferred', s2['session'] == {'status': 'NOT_RECORDED', 'minutes': 'UNKNOWN'}
         and 'SESSION_BOUNDS_NOT_RECORDED' in codes(s2) and s2['effort_evidence'] in ('INCOMPLETE', 'MATERIAL_DISCREPANCY'),
         f"session {s2['session']['status']}, minutes {s2['session']['minutes']}")
    held['START'].rename(P.session_path(pk, 'S', 'START'))
    s3 = P.derived_effort(pk, 'S')
    c.ok('effort', 'a START without its STOP is INCOMPLETE_NO_STOP', s3['session']['status'] == 'INCOMPLETE_NO_STOP', s3['session']['status'])
    held['STOP'].rename(P.session_path(pk, 'S', 'STOP'))
    c.refused('effort', 'an attestation is immutable (a second START is refused)', lambda: P.attest_session(pk, 'S', 'START', OPERATOR, 'SYNTHETIC_FIXTURE'),
              'already exists and is immutable')
    c.refused('effort', 'assistant self-attestation is refused by name', lambda: P.attest_session(legacy, 'S', 'START', 'Claude (assistant)', 'SYNTHETIC_FIXTURE'),
              'assistant self-attestation is refused')
    c.refused('effort', 'an attestation by a non-human kind is refused', lambda: P.attest_session(legacy, 'S', 'START', 'Operator', 'ASSISTANT'),
              'attested by the human arm operator personally')
    c.refused('effort', 'a STOP needs its START', lambda: P.attest_session(legacy, 'G', 'STOP', 'Operator', 'SYNTHETIC_FIXTURE'), 'needs its START')
    exports = pk / P.SUGGESTION_EXPORT_DIR; exports.rename(pk / 'exports.hold')
    g2 = P.derived_effort(pk, 'G')
    c.ok('effort', 'graph minutes without any recorded graph query are flagged', 'GRAPH_TIME_WITHOUT_RECORDED_QUERIES' in codes(g2), codes(g2))
    (pk / 'exports.hold').rename(exports)


def accounting_checks(c, pk, index):
    a = P.suggestion_accounting(pk)
    e, w, u = (a['by_class'][k] for k in ('ECONOMIC_CONNECTION_CANDIDATE', 'METHODOLOGICAL_WARNING', 'UNSUPPORTED_MATCH'))
    c.ok('accounting', 'exported = logged + exported-but-unlogged suggestions, per class',
         all(x['exported'] == x['logged_suggestions'] + x['exported_unlogged'] for x in (e, w, u)),
         f"economic {e['exported']}={e['logged_suggestions']}+{e['exported_unlogged']}; warning {w['exported']}={w['logged_suggestions']}+{w['exported_unlogged']}; "
         f"unsupported {u['exported']}")
    c.ok('accounting', 'two rows sharing one origin: rows and suggestions are counted separately',
         (e['logged_rows'], e['logged_suggestions'], e['rows_sharing_an_origin']) == (3, 2, 2)
         and e['rows_by_decision'] == {'ACCEPTED': 1, 'DECLINED': 1, 'UNRESOLVED': 1}
         and e['suggestions_by_decision'] == {'ANY_ACCEPTED': 1, 'ALL_DECLINED': 0, 'UNRESOLVED_OR_MIXED': 1},
         f"{e['logged_rows']} rows, {e['logged_suggestions']} suggestions; rows {e['rows_by_decision']}; suggestions {e['suggestions_by_decision']}")
    r = e['rates']
    c.ok('accounting', 'every rate pairs a numerator and denominator of the same level',
         (r['declined_share_of_logged_rows']['numerator'], r['declined_share_of_logged_rows']['denominator']) == (1, 3)
         and (r['all_declined_share_of_logged_suggestions']['numerator'], r['all_declined_share_of_logged_suggestions']['denominator']) == (0, 2),
         f"declined rows 1/3; all-declined suggestions 0/2")
    c.ok('accounting', 'a zero denominator is explicit, not zero', u['rates']['logged_share_of_exported_suggestions']['value'] == 'UNDEFINED_ZERO_DENOMINATOR',
         u['rates']['logged_share_of_exported_suggestions'])
    c.ok('accounting', 'outcomes are NOT_ADJUDICATED before adjudication', e['adjudicated'] == 'NOT_ADJUDICATED' and
         a['confirmed_economic_discoveries']['rows'] == 'NOT_ADJUDICATED', e['adjudicated'])
    exports = pk / P.SUGGESTION_EXPORT_DIR; exports.rename(pk / 'exports.hold')
    m = P.suggestion_accounting(pk)
    c.ok('accounting', 'a missing V2 export makes exported counts UNKNOWN, never zero',
         m['traceability'] == 'V2_EXPORT_MISSING' and m['totals']['exported'] == 'UNKNOWN', f"{m['traceability']}; exported {m['totals']['exported']}")
    (pk / 'exports.hold').rename(exports)
    return a


def blind_and_report(c, pk, index):
    logs_ = {arm: pk / f'connections-{arm}.jsonl' for arm in P.ARMS}
    export = P.blind(pk / 'snapshot.json', logs_, SALT, pk / 'blind.json', pk / 'key.json')
    v2 = P.alias_export(pk / 'blind.json', pk / 'blind_v2.json', pk.parent / 'alias.json')
    leaks = P.scan_leaks(v2['items'], P.own_records(export))
    c.ok('blinding', 'the aliased export passes the leak scan', not leaks, f'{len(v2["items"])} items, {len(leaks)} findings')
    rows = [DR.stand_in_adjudication(i) for i in v2['items']]
    (pk / 'adjudications.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    unblinded = P.unblind(pk, 'blind_v2.json')
    a = P.suggestion_accounting(pk, unblinded)
    disc, warn = a['confirmed_economic_discoveries']['rows'], a['methodological_warnings_confirmed']['rows']
    ea = a['by_class']['ECONOMIC_CONNECTION_CANDIDATE']['adjudicated']
    c.ok('accounting', 'after adjudication, every row keeps its own outcome (never overwritten by origin)',
         ea['rows_adjudicated'] == 3 and ea['suggestions_adjudicated'] == 2, f"{ea['rows_adjudicated']} rows, {ea['suggestions_adjudicated']} suggestions; {ea['rows']}")
    same = next(r for r in unblinded if r['arm'] == 'G' and r['connection_id'].startswith('CON-'))
    split = [dict(r, outcome='REJECTED_FALSE') if r['connection_id'] == same['connection_id'] else r for r in unblinded]
    sa = P.suggestion_accounting(pk, split)['by_class']['ECONOMIC_CONNECTION_CANDIDATE']['adjudicated']
    c.ok('accounting', 'two rows of one suggestion with different outcomes are both counted and the conflict is reported',
         sa['suggestions_with_conflicting_outcomes'] >= 1 and sa['rows']['REJECTED_FALSE'] >= 1, f"conflicting suggestions {sa['suggestions_with_conflicting_outcomes']}; {sa['rows']}")
    forced = [dict(r, outcome='CONFIRMED_AGAINST_ORIGINALS', economic_meaning='MEANINGFUL', arm_decision='ACCEPTED')
              if r.get('connection_class') == 'METHODOLOGICAL_WARNING' else r for r in unblinded]
    f = P.suggestion_accounting(pk, forced)
    c.ok('accounting', 'a warning confirmed as useful is never counted as an economic discovery',
         f['confirmed_economic_discoveries']['rows'] == disc and f['methodological_warnings_confirmed']['rows'] == warn + 1,
         f"discoveries {disc} -> {f['confirmed_economic_discoveries']['rows']}; warnings confirmed {warn} -> {f['methodological_warnings_confirmed']['rows']}")
    stop = P.session_path(pk, 'G', 'STOP'); original = stop.read_bytes()
    stop.write_bytes(original.replace(b'stopped', b'ended'))
    c.refused('effort', 'an attestation edited after blinding refuses unblinding', lambda: P.unblind(pk, 'blind_v2.json'), 'changed after blinding')
    stop.write_bytes(original)
    rep = P.report([pk], export_name='blind_v2.json')
    c.ok('report', 'the report states the primary measure, both sensitivities and the effort evidence; one pair stays INCONCLUSIVE',
         rep['classification'] == 'INCONCLUSIVE' and rep['effort_evidence_summary'] == ['CONSISTENT', 'CONTRADICTORY']
         and set(rep['classification_sensitivity']) == {'session', 'observed_span'},
         f"{rep['classification']}; evidence {rep['effort_evidence_summary']}; sensitivities {rep['classification_sensitivity']}")
    return a, rep


def provenance_checks(c, pk):
    """The saved execution-provenance record is validated separately from replay: tampering refuses, an unrelated HEAD does not."""
    snap = pk / 'snapshot.json'; f = P.default_exports(snap)[0]; original = f.read_bytes()
    doc = json.loads(original); doc['visibility']['implementation_check']['running_commit'] = 'f' * 40
    f.write_text(json.dumps(doc), encoding='utf-8')
    c.refused('provenance', 'a modified saved running commit (all else intact) is refused before sealing',
              lambda: P.load_suggestion_exports(P.default_exports(snap), snap), 'not in this repository')
    f.write_bytes(original)
    moved = lambda root=I.ROOT, paths=None: {'status': 'CLEAN', 'commit': '1' * 40, 'dirty': []}
    with patch.object(I, 'git_state', moved):
        manifest = P.load_suggestion_exports(P.default_exports(snap), snap)[1]
    c.ok('provenance', 'replay after HEAD moves to an unrelated commit with identical pinned code is accepted',
         all(m['execution_provenance']['level'] == 'COMMIT_CONSISTENT_WITH_PIN' for m in manifest), 'COMMIT_CONSISTENT_WITH_PIN')


def uniform_pin_checks(c, pk):
    """Simulate a changed implementation: every snapshot-bound entry point, for both arms, must refuse."""
    real = I.content
    def changed(root=I.ROOT):
        now = real(root); files = dict(now['files'], **{'src/research/graph/baseline.py': '0' * 64})
        return {**now, 'files': files, 'tree_digest': '0' * 64}
    snap = pk / 'snapshot.json'; when = Ledger(pk / 'S.jsonl').load().events[-1]['recorded_at_utc']; g_when = Ledger(pk / 'G.jsonl').load().events[-1]['recorded_at_utc']

    def cli(*argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            try:GCLI.main(list(argv))
            except SystemExit:
                if 'differs from the snapshot pin' in err.getvalue():raise P.PilotError('differs from the snapshot pin')
                raise
    paths = {'structured-search arm view (S, API)': lambda: P.arm_view(snap, 'S', when),
             'structured search (S, CLI baseline-search)': lambda: cli('baseline-search', 'DLC-GR4-S', 'OBS-1', '--snapshot', str(snap), '--arm', 'S', '--query-at', when),
             'graph query (G, API arm_graph)': lambda: P.arm_graph(snap, 'G', g_when),
             'graph query (G, CLI revisit)': lambda: cli('revisit', 'OBS-1', '--snapshot', str(snap), '--arm', 'G', '--query-at', g_when),
             'export replay': lambda: P.load_suggestion_exports(P.default_exports(snap), snap),
             'unblinding': lambda: P.unblind(pk, 'blind_v2.json'), 'effort': lambda: P.derived_effort(pk, 'S'),
             'suggestion accounting': lambda: P.suggestion_accounting(pk), 'verify': lambda: P.verify_summary(snap)}
    with patch.object(I, 'content', changed):
        for name, fn in paths.items():c.refused('uniform pin', f'{name} refuses a changed implementation', fn, 'differs from the snapshot pin')


def run(directory):
    d = Path(directory); c = Checks(); clock = DR.Clock()
    pin = pinning(c, d)
    pk, _ = packet(c, d, clock, pin)
    bounds = arms(pk, clock)
    tamper_checks(c, pk)
    index = logs(pk, bounds)
    provenance_checks(c, pk)
    effort_checks(c, pk, bounds, d / 'legacy')
    before = accounting_checks(c, pk, index)
    after, rep = blind_and_report(c, pk, index)
    uniform_pin_checks(c, pk)
    return {'checks': c.rows, 'accounting_before': before, 'accounting_after': after, 'effort': rep['packets'][0]['effort_check']}


def markdown(res):
    L = ['# Graph Pilot R4 readiness: Phase A synthetic dry run', '', f'> {M.BANNER}', '',
         '**NOT an R4 run.** Synthetic fixtures only, offline, in a temporary directory; no source fetched, no real campaign, session or '
         'adjudication. The adjudicator and operator are labelled fixture stand-ins. Regenerate with '
         '`python -m src.research.graph pilot r4-dry-run --write`; `--check` compares. Commit hashes and content digests are not printed, '
         'because they change with every implementation commit.', '',
         '| Area | Check | Observed | Result |', '|---|---|---|---|']
    for r in res['checks']:
        L.append(f"| {r['area']} | {r['check']} | {str(r['observed']).replace('|', '/')} | {r['result']} |")
    L += ['', '## Effort (synthetic packet P1; primary measure = self-reported minutes)', '',
          '| Arm | Observed span (min) | Attested session (min) | Self-reported (min) | Difference vs session | Evidence | Flags |', '|---|---:|---:|---:|---|---|---|']
    for arm in P.ARMS:
        e = res['effort'][arm]; cmp_ = e['comparisons'].get('session') or e['comparisons']['observed_span']
        L.append(f"| {arm} | {e['observed_span_minutes']} | {e['session']['minutes']} | {e['self_reported']['analyst_minutes']} | "
                 f"{cmp_['difference_minutes']} min ({cmp_['difference_percent']}%) | {e['effort_evidence']} | {', '.join(sorted({f['code'] for f in e['flags']})) or 'none'} |")
    L += ['', '## Suggestion accounting (arm G, after the stand-in adjudication)', '',
          '| Class | Exported | Logged suggestions | Exported, unlogged | Logged rows | Rows accepted / declined / unresolved | Adjudicated rows |',
          '|---|---:|---:|---:|---:|---|---|']
    for k, x in res['accounting_after']['by_class'].items():
        dec = x['rows_by_decision']
        adj = ', '.join(f'{o}: {n}' for o, n in x['adjudicated']['rows'].items() if n) or 'none'
        L.append(f"| {k} | {x['exported']} | {x['logged_suggestions']} | {x['exported_unlogged']} | {x['logged_rows']} | "
                 f"{dec['ACCEPTED']} / {dec['DECLINED']} / {dec['UNRESOLVED']} | {adj} |")
    a = res['accounting_after']
    L += ['', f"- Confirmed economic discoveries: {a['confirmed_economic_discoveries']['rows']} row(s), "
              f"{a['confirmed_economic_discoveries']['distinct_origin_suggestions']} suggestion(s) (rule: {a['confirmed_economic_discoveries']['rule']}).",
          f"- Methodological warnings confirmed: {a['methodological_warnings_confirmed']['rows']}; never counted as discoveries.",
          f"- {sum(r['result'] == 'PASS' for r in res['checks'])}/{len(res['checks'])} checks passed."]
    return '\n'.join(L) + '\n'


def generate():
    tmp = Path(tempfile.mkdtemp(prefix='graph-r4-dry-run-'))
    try:
        res = run(tmp)
    finally:
        remove_tree(tmp)
    if any(r['result'] != 'PASS' for r in res['checks']):
        raise DR.DryRunError('R4 readiness rehearsal failed: ' + '; '.join(r['check'] for r in res['checks'] if r['result'] != 'PASS'))
    return markdown(res)


def check():
    if not RECORD.exists() or RECORD.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_pilot_r4_dry_run.md differs from the regenerated rehearsal; run pilot r4-dry-run --write')
    return {'r4_dry_run': 'PASS', 'network': 'none', 'acquisition': 0, 'record': RECORD.relative_to(ROOT).as_posix()}
