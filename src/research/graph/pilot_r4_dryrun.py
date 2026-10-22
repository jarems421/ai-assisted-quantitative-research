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
import tempfile
from datetime import timedelta
from pathlib import Path

from src.research.discovery.demo import passport
from src.research.discovery.ledger import Ledger
from src.research.graph import catalogue as C
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
    for rel in I.pinned_paths(root):
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
    (impl / 'docs').mkdir(); (impl / 'docs/unrelated.md').write_text('Unrelated change.\n', encoding='utf-8')
    git(impl, 'add', '-A'); git(impl, 'commit', '-q', '-m', 'Unrelated documentation change')
    c.ok('pin', 'an unrelated commit with identical implementation passes as UNRELATED_COMMIT_CHANGE',
         I.verify(pin, impl)['status'] == 'UNRELATED_COMMIT_CHANGE', I.verify(pin, impl)['status'])
    bare = d / 'no-git'
    for rel in I.pinned_paths(impl):(bare / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(impl / rel, bare / rel)
    c.refused('pin', 'missing git metadata cannot be pinned', lambda: I.pin(bare), 'git metadata is unavailable')
    c.ok('pin', 'missing git metadata at verification still enforces content', I.verify(pin, bare)['status'] == 'GIT_UNAVAILABLE_CONTENT_VERIFIED',
         I.verify(pin, bare)['status'])
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


def session(path, arm, bounds, recorded_by=None):
    """Operator-recorded session bounds: the session opens with the campaign record and closes at its last record."""
    start, end = bounds
    Path(path).write_text(json.dumps({'version': P.SESSION_VERSION, 'arm': arm, 'started_at_utc': start.isoformat(), 'ended_at_utc': end.isoformat(),
                                      'recorded_by': recorded_by or {'name': 'Synthetic operator stand-in (fixture)', 'kind': 'SYNTHETIC_FIXTURE'},
                                      'notes': 'synthetic rehearsal'}), encoding='utf-8')


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
    g_rows = [row(rel, 'ACCEPTED', 'EFF-G-3'), row(same, 'DECLINED'), row(warn, 'UNRESOLVED')]
    s_rows = [{'connection_id': P.connection_id('DLC-GR4-S/OBS-1', 'DLC-GR4PKT/REL-P-1', ['EXACT_ENTITY_ID']), 'arm': 'S', 'kind': 'CONNECTION',
               'operator': 'baseline-search', 'found_via': 'ANALYST_READING', 'source_record': 'DLC-GR4-S/OBS-1', 'target_record': 'DLC-GR4PKT/REL-P-1',
               'basis': ['EXACT_ENTITY_ID'], 'arm_decision': 'DECLINED', 'analyst_minutes': 3, 'discovery_lab_record': None,
               'recorded_at_utc': s_at, 'notes': 'synthetic rehearsal', 'log_version': P.CONNECTION_LOG_V2, 'origin_suggestion_id': None,
               'origin_operator': None, 'origin_bases': [], 'connection_class': None}]
    for arm, rows in (('S', s_rows), ('G', g_rows)):
        (pk / f'connections-{arm}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    return index


def effort_checks(c, pk, bounds):
    session(pk / 'session-S.json', 'S', bounds['S']); session(pk / 'session-G.json', 'G', bounds['G'])
    g, s = P.derived_effort(pk, 'G'), P.derived_effort(pk, 'S')
    codes = lambda e: sorted({f['code'] for f in e['flags']})
    c.ok('effort', 'contemporaneous G logging: derived and self-reported minutes agree within the threshold', 'EFFORT_DISCREPANCY' not in codes(g),
         f"span {g['observed_span_minutes']} vs self {g['self_reported']['analyst_minutes']}; session {g['session']['minutes']}; flags {codes(g) or 'none'}")
    c.ok('effort', 'graph query and suggestion-review time are reported where measurable',
         g['graph_time']['queries_recorded'] == 2 and g['graph_time']['self_reported_minutes'] == 9 and 'GRAPH_MINUTES_EXCEED_OBSERVED_WINDOWS' not in codes(g),
         f"{g['graph_time']['queries_recorded']} recorded queries; {g['graph_time']['self_reported_minutes']} self-reported graph minutes; "
         f"review windows <= {g['graph_time']['review_window_minutes_upper_bound']} min")
    c.ok('effort', 'an inflated S effort is flagged against span, session and its append interval',
         {'EFFORT_DISCREPANCY', 'EFFORT_EXCEEDS_APPEND_INTERVAL', 'SELF_REPORTED_EXCEEDS_SESSION'} <= set(codes(s)),
         f"span {s['observed_span_minutes']} vs self {s['self_reported']['analyst_minutes']}; flags {codes(s)}")
    (pk / 'session-S.json').rename(pk / 'session-S.hold')
    s2 = P.derived_effort(pk, 'S')
    c.ok('effort', 'missing session bounds are reported, never inferred', s2['session'] == {'status': 'NOT_RECORDED', 'minutes': 'UNKNOWN'}
         and 'SESSION_BOUNDS_NOT_RECORDED' in codes(s2), f"session {s2['session']['status']}, minutes {s2['session']['minutes']}")
    (pk / 'session-S.hold').rename(pk / 'session-S.json')
    bad = pk / 'session-bad.json'; session(bad, 'S', bounds['S'], {'name': 'Claude', 'kind': 'ASSISTANT'})
    c.refused('effort', 'session bounds recorded by an assistant are refused',
              lambda: P.load_session(bad, 'S', P.parse_time('2026-10-21T00:00:00+00:00'), 'SYNTHETIC'), 'recorded by the human operator')
    bad.unlink()
    exports = pk / P.SUGGESTION_EXPORT_DIR; exports.rename(pk / 'exports.hold')
    g2 = P.derived_effort(pk, 'G')
    c.ok('effort', 'graph minutes without any recorded graph query are flagged', 'GRAPH_TIME_WITHOUT_RECORDED_QUERIES' in codes(g2), codes(g2))
    (pk / 'exports.hold').rename(exports)


def accounting_checks(c, pk, index):
    a = P.suggestion_accounting(pk)
    e, w, u = (a['by_class'][k] for k in ('ECONOMIC_CONNECTION_CANDIDATE', 'METHODOLOGICAL_WARNING', 'UNSUPPORTED_MATCH'))
    c.ok('accounting', 'exported = logged + exported-but-unlogged, per class',
         all(x['exported'] == x['logged_suggestions'] + x['exported_unlogged'] for x in (e, w, u)),
         f"economic {e['exported']}={e['logged_suggestions']}+{e['exported_unlogged']}; warning {w['exported']}={w['logged_suggestions']}+{w['exported_unlogged']}; "
         f"unsupported {u['exported']}")
    c.ok('accounting', 'declined suggestions are counted', e['logged_by_decision'] == {'ACCEPTED': 1, 'DECLINED': 1, 'UNRESOLVED': 0},
         e['logged_by_decision'])
    c.ok('accounting', 'a zero denominator is explicit, not zero', u['rates']['logged_share_of_exported']['value'] == 'UNDEFINED_ZERO_DENOMINATOR',
         u['rates']['logged_share_of_exported'])
    c.ok('accounting', 'outcomes are NOT_ADJUDICATED before adjudication', e['adjudicated'] == 'NOT_ADJUDICATED' and
         a['confirmed_economic_discoveries']['count'] == 'NOT_ADJUDICATED', e['adjudicated'])
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
    disc, warn = a['confirmed_economic_discoveries']['count'], a['methodological_warnings_confirmed']['count']
    c.ok('accounting', 'after adjudication, outcomes are counted per class with denominators',
         isinstance(a['by_class']['ECONOMIC_CONNECTION_CANDIDATE']['adjudicated'], dict),
         {k: a['by_class'][k]['adjudicated'] for k in ('ECONOMIC_CONNECTION_CANDIDATE', 'METHODOLOGICAL_WARNING')})
    forced = [dict(r, outcome='CONFIRMED_AGAINST_ORIGINALS', economic_meaning='MEANINGFUL', arm_decision='ACCEPTED')
              if r.get('connection_class') == 'METHODOLOGICAL_WARNING' else r for r in unblinded]
    f = P.suggestion_accounting(pk, forced)
    c.ok('accounting', 'a warning confirmed as useful is never counted as an economic discovery',
         f['confirmed_economic_discoveries']['count'] == disc and f['methodological_warnings_confirmed']['count'] == warn + 1,
         f"discoveries {disc} -> {f['confirmed_economic_discoveries']['count']}; warnings confirmed {warn} -> {f['methodological_warnings_confirmed']['count']}")
    rep = P.report([pk], export_name='blind_v2.json')
    c.ok('report', 'the paired report carries effort checks and suggestion accounting; one pair stays INCONCLUSIVE',
         rep['classification'] == 'INCONCLUSIVE' and 'effort_check' in rep['packets'][0] and 'suggestion_accounting' in rep['packets'][0], rep['classification'])
    return a, rep


def run(directory):
    d = Path(directory); c = Checks(); clock = DR.Clock()
    pin = pinning(c, d)
    pk, _ = packet(c, d, clock, pin)
    bounds = arms(pk, clock)
    tamper_checks(c, pk)
    index = logs(pk, bounds)
    effort_checks(c, pk, bounds)
    before = accounting_checks(c, pk, index)
    after, rep = blind_and_report(c, pk, index)
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
    L += ['', '## Effort (synthetic packet P1)', '', '| Arm | Observed span (min) | Session (min) | Self-reported (min) | Flags |', '|---|---:|---:|---:|---|']
    for arm in P.ARMS:
        e = res['effort'][arm]
        L.append(f"| {arm} | {e['observed_span_minutes']} | {e['session']['minutes']} | {e['self_reported']['analyst_minutes']} | "
                 f"{', '.join(sorted({f['code'] for f in e['flags']})) or 'none'} |")
    L += ['', '## Suggestion accounting (arm G, after the stand-in adjudication)', '',
          '| Class | Exported | Logged | Accepted / declined / unresolved | Exported, unlogged | Adjudicated outcomes |', '|---|---:|---:|---|---:|---|']
    for k, x in res['accounting_after']['by_class'].items():
        dec = x['logged_by_decision']
        adj = ', '.join(f'{o}: {n}' for o, n in x['adjudicated'].items() if n) or 'none'
        L.append(f"| {k} | {x['exported']} | {x['logged_suggestions']} | {dec['ACCEPTED']} / {dec['DECLINED']} / {dec['UNRESOLVED']} | {x['exported_unlogged']} | {adj} |")
    a = res['accounting_after']
    L += ['', f"- Confirmed economic discoveries: {a['confirmed_economic_discoveries']['count']} (rule: {a['confirmed_economic_discoveries']['rule']}).",
          f"- Methodological warnings confirmed: {a['methodological_warnings_confirmed']['count']}; never counted as discoveries.",
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
