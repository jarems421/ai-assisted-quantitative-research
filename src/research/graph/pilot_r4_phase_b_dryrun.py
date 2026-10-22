"""Graph Pilot R4 Phase B: synthetic end-to-end rehearsal of dual human adjudication. NOT an R4 run.

Two synthetic packets go through the Phase A pipeline (pinned V2 snapshot, attested sessions, frozen suggestion export,
V2 logs, blinding, aliasing): P1 conforms to the registered R4 configuration; P2 is frozen with GRAPH_CLASSIFICATION_V1_1
under a recorded owner deviation. Two labelled synthetic reviewer stand-ins then make separate economic and usefulness
judgments, declare exposure per item, seal by hash and reveal in a throwaway git repository. Every adversarial case is a
check that must be refused, flagged or excluded. No source is fetched, no real person adjudicates, nothing activates R4.

Regenerate only with ``python -m src.research.graph pilot r4-phase-b-dry-run --write``; ``--check`` compares.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from src.research.discovery.demo import passport
from src.research.discovery.ledger import Ledger
from src.research.graph import adjudication as AD
from src.research.graph import connections as K
from src.research.graph import model as M
from src.research.graph import pilot as P
from src.research.graph import pilot_dryrun as DR
from src.research.graph import pilot_r4_dryrun as R4

ROOT = R4.ROOT
RECORD = ROOT / 'docs/strategy/graph_pilot_r4_phase_b_dry_run.md'
EXPORT = 'blind_v2.json'
REVIEWER = {'R1': 'Synthetic reviewer one (fixture)', 'R2': 'Synthetic reviewer two (fixture)'}
CLEAN = {'saw_arm_info': 'NO', 'seen': [], 'operated_or_attested_arm': 'NO', 'note': ''}


def build_packet(c, base, name, classification=None, empty=False):
    """One synthetic packet through the Phase A pipeline, up to the aliased export (``empty``: no connection rows at all)."""
    d = Path(base) / name; d.mkdir(parents=True); clock = DR.Clock()
    led = Ledger.create(d / 'packet.jsonl', DR.campaign('DLC-GR4PKT', 'Phase B rehearsal packet'), clock)
    led.append('source', passport('SRC-P-1', 'register', field='t', units='kt/month', publication='VERIFIED_ORIGINAL_RECORD'))
    led.append('observation', DR.observation('OBS-P-1', 'Quay One throughput fell.', {'from': 410, 'to': 265}, 'kt/month', DR.doc('bundle/x', b'x'),
                                              'STATE_CHANGE', source='SRC-P-1'))
    led.append('relationship', DR.relationship('REL-P-1'))
    bundle = d / 'bundle'; bundle.mkdir(); (bundle / 'x.csv').write_bytes(b'x')
    clock.advance(1); frozen = clock.at(); clock.advance(2)
    P.make_snapshot(d / 'snapshot.json', name, d / 'packet.jsonl', {'S': (d / 'S.jsonl', 'DLC-GR4-S'), 'G': (d / 'G.jsonl', 'DLC-GR4-G')}, bundle,
                    frozen_at=frozen, connection_log=P.CONNECTION_LOG_V2, implementation=R4.synthetic_pin(), classification=classification)
    bounds = R4.arms(d, clock); R4.logs(d, bounds); R4.attest(d, 'S', bounds['S']); R4.attest(d, 'G', bounds['G'])
    if empty:
        for a in P.ARMS:(d / f'connections-{a}.jsonl').write_text('', encoding='utf-8')  # a fully formed packet with zero rows
    export = P.blind(d / 'snapshot.json', {a: d / f'connections-{a}.jsonl' for a in P.ARMS}, R4.SALT, d / 'blind.json', d / 'key.json')
    P.alias_export(d / 'blind.json', d / EXPORT, Path(base) / f'alias-{name}.json')
    return d, export


def economic_row(item, reviewer, outcome=None, exposure=None, name=None):
    base = DR.stand_in_adjudication(item)
    if outcome:base.update(outcome=outcome, economic_meaning='NOT_MEANINGFUL' if outcome.startswith('REJECTED') else base['economic_meaning'],
                           checked_evidence=base['checked_evidence'] if outcome == 'CONFIRMED_AGAINST_ORIGINALS' else [])
    return {**base, 'adjudicator': name or REVIEWER[reviewer], 'adjudicator_kind': 'SYNTHETIC_FIXTURE', 'log_version': AD.ADJUDICATION_V2,
            'reviewer': reviewer, 'exposure': exposure or dict(CLEAN), 'notes': 'synthetic stand-in'}


def usefulness_row(item, reviewer, usefulness, exposure=None, name=None):
    reused = usefulness == 'USEFUL_LESSON_REUSED'
    evidence = sorted(AD.evidence_of(item))[:1] if reused else []
    return {'blind_id': item['blind_id'], 'usefulness': usefulness, 'avoided_action': 'did not request vessel tracks a second time' if reused else None,
            'checked_evidence': evidence, 'adjudicator': name or REVIEWER[reviewer], 'adjudicator_kind': 'SYNTHETIC_FIXTURE', 'adjudicator_minutes': 1,
            'recorded_at_utc': DR.START.isoformat(), 'notes': 'synthetic stand-in', 'log_version': AD.USEFULNESS_V1, 'reviewer': reviewer,
            'exposure': exposure or dict(CLEAN)}


def write_logs(d, reviewer, econ, use):
    f = AD.files(d, reviewer)
    f['economic'].write_text(''.join(json.dumps(r) + '\n' for r in econ), encoding='utf-8')
    f['usefulness'].write_text(''.join(json.dumps(r) + '\n' for r in use), encoding='utf-8')


def judgments(d):
    """R1 and R2 judge independently: they disagree on one connection and on the warning's usefulness."""
    export = json.loads((d / EXPORT).read_text(encoding='utf-8'))
    items, econ_ids, use_ids = AD.partition(export)
    econ = sorted(econ_ids); flip = next(b for b in econ if DR.stand_in_adjudication(items[b])['outcome'] == 'PLAUSIBLE_UNVERIFIED')
    logs = {}
    for rv in AD.REVIEWERS:
        e = [economic_row(items[b], rv, 'REJECTED_TRIVIAL' if (rv == 'R2' and b == flip) else None) for b in econ]
        u = [usefulness_row(items[b], rv, 'USEFUL_LESSON_REUSED' if rv == 'R1' else 'USEFUL_NOT_USED') for b in sorted(use_ids)]
        logs[rv] = (e, u)
    return items, econ_ids, use_ids, logs, flip


def git_init(base):
    R4.git(base, 'init', '-q'); R4.git(base, 'add', '-A'); R4.git(base, 'commit', '-q', '-m', 'packets before adjudication')


def commit(base, paths, message):
    R4.git(base, 'add', *[str(p) for p in paths]); R4.git(base, 'commit', '-q', '-m', message)


def exposure_checks(c, d, items, econ_ids, logs, fixture):
    first = sorted(econ_ids)[0]; e, u = logs['R1']

    def with_row(row):
        write_logs(d, 'R1', [row if r['blind_id'] == first else r for r in e], u)
    validate = lambda: AD.validate_reviewer(d, EXPORT, 'R1', fixture)
    bad = economic_row(items[first], 'R1'); bad.pop('exposure'); with_row(bad)
    c.refused('exposure', 'a row without an exposure declaration is refused', validate, 'fields must be exactly')
    with_row(economic_row(items[first], 'R1', exposure={**CLEAN, 'saw_arm_info': 'YES'}))
    c.refused('exposure', 'saw_arm_info YES without listing arm-identifying material is refused', validate, 'saw_arm_info must be YES exactly when')
    statuses = {}
    for label, exposure, name in (('arm ledger seen', {**CLEAN, 'saw_arm_info': 'YES', 'seen': ['ARM_LEDGER']}, None),
                                  ('the other reviewer\'s judgments seen', {**CLEAN, 'seen': ['OTHER_ADJUDICATION']}, None),
                                  ('an AI assessment seen', {**CLEAN, 'seen': ['AI_ASSESSMENT']}, None),
                                  ('arm operation declared', {**CLEAN, 'operated_or_attested_arm': 'YES'}, None)):
        with_row(economic_row(items[first], 'R1', exposure=exposure)); statuses[label] = validate()['status'][first]
    c.ok('exposure', 'each declaration maps to its item status',
         statuses == {'arm ledger seen': 'POTENTIALLY_UNBLINDED', "the other reviewer's judgments seen": 'NOT_INDEPENDENT',
                      'an AI assessment seen': 'NOT_INDEPENDENT', 'arm operation declared': 'CONFLICTED'}, statuses)
    write_logs(d, 'R1', [economic_row(items[b], 'R1', name=R4.OPERATOR) for b in sorted(econ_ids)],
               [usefulness_row(r_item, 'R1', 'USEFUL_NOT_USED', name=R4.OPERATOR) for r_item in [items[r['blind_id']] for r in u]])
    c.ok('exposure', 'a reviewer who attested an arm session is CONFLICTED, whatever they declare', set(validate()['status'].values()) == {'CONFLICTED'},
         'CONFLICTED (matched to a session attestation)')
    write_logs(d, 'R1', [economic_row(items[b], 'R1', name='Claude (assistant)') for b in sorted(econ_ids)], u)
    c.refused('exposure', 'an assistant cannot adjudicate', validate, 'an assistant cannot adjudicate')
    write_logs(d, 'R1', [economic_row(items[b], 'R1') for b in sorted(econ_ids)] + [economic_row(items[u[0]['blind_id']], 'R1')], u)
    c.refused('separation', 'an economic log cannot judge a warning item (usefulness is separate)', validate, 'not an unadjudicated CONNECTION item')
    write_logs(d, 'R1', e, [dict(u[0], avoided_action=None)])
    c.refused('usefulness', 'USEFUL_LESSON_REUSED must state the avoided action', validate, 'states the action the lesson changed or avoided')
    write_logs(d, 'R1', e, u)


def zero_item_checks(c, base):
    """A fully formed packet with zero rows: explicit empty logs, two sealed reviewers, verified reveal order, eligible."""
    p5, export = build_packet(c, base, 'P5', empty=True)
    commit(base, [p5], 'P5 packet (zero rows) before adjudication')
    c.ok('zero items', 'a zero-row packet has an empty frozen export', export['items'] == [] and AD.partition(json.loads((p5 / EXPORT).read_text(encoding='utf-8')))[0] == {},
         '0 items')
    c.refused('zero items', 'a reviewer must still write both logs, explicitly empty', lambda: AD.seal(p5, EXPORT, 'R1', REVIEWER['R1'], dict(CLEAN), 'SYNTHETIC_FIXTURE'),
              'explicitly empty')
    for rv in AD.REVIEWERS:write_logs(p5, rv, [], [])
    c.refused('zero items', 'a zero-item seal still needs a reviewer-level exposure declaration',
              lambda: AD.seal(p5, EXPORT, 'R1', REVIEWER['R1'], {'saw_arm_info': 'NO'}, 'SYNTHETIC_FIXTURE'), 'exposure must have exactly')
    for rv in AD.REVIEWERS:AD.seal(p5, EXPORT, rv, REVIEWER[rv], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    commit(base, [AD.files(p5, rv)['seal'] for rv in AD.REVIEWERS], 'P5 seals')
    commit(base, [AD.files(p5, rv)[k] for rv in AD.REVIEWERS for k in ('economic', 'usefulness')], 'P5 empty logs revealed after both seals')
    dual = AD.dual(p5, EXPORT)
    conf = AD.conformance(p5, P.load_snapshot(p5 / 'snapshot.json')['snapshot'], dual)
    c.ok('zero items', 'two different sealed reviewers, verified reveal order and explicit zero denominators; the packet conforms',
         dual['status'] == 'DUAL_SEALED' and dual['items'] == 0 and dual['reveal_order']['status'] == 'VERIFIED'
         and dual['agreement']['outcome']['kappa'] == 'UNDEFINED_ZERO_DENOMINATOR' and conf['status'] == 'CONFORMING',
         f"{dual['status']}, 0 items, reveal {dual['reveal_order']['status']}, kappa {dual['agreement']['outcome']['kappa']}, {conf['status']}")
    rep = P.report([base / 'P1', p5], export_name=EXPORT)
    z = next(p for p in rep['packets'] if p['packet'] == 'P5')
    c.ok('zero items', 'the zero-row packet is reported and enters the primary comparison with zero counts, not dropped',
         rep['excluded_from_primary'] == [] and z['G']['review_burden_items'] == 0 and z['G']['verified_connections'] == 0
         and z['suggestion_accounting']['totals']['logged_rows'] == 0 and z['G']['adjudicator_minutes'] == 0,
         f"in primary; G verified {z['G']['verified_connections']}, review items {z['G']['review_burden_items']}, adjudicator minutes {z['G']['adjudicator_minutes']}")


def content_history_checks(c, base, p2):
    """Reveal order uses the commits that hold the sealed bytes, not merely files of the same name."""
    fresh = lambda name: shutil.copytree(p2, base / name, ignore=shutil.ignore_patterns('adjudication-seal-*', 'adjudications-*', 'warning-usefulness-*'))
    p6 = fresh('P6'); lg = judgments(p6)[3]
    for rv in AD.REVIEWERS:write_logs(p6, rv, *lg[rv]); AD.seal(p6, EXPORT, rv, REVIEWER[rv], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    commit(base, [AD.files(p6, rv)['seal'] for rv in AD.REVIEWERS], 'P6 seals')
    real = {rv: {k: AD.files(p6, rv)[k].read_bytes() for k in ('economic', 'usefulness')} for rv in AD.REVIEWERS}
    for rv in AD.REVIEWERS:AD.files(p6, rv)['economic'].write_text('', encoding='utf-8')  # a placeholder committed first
    commit(base, [AD.files(p6, rv)[k] for rv in AD.REVIEWERS for k in ('economic', 'usefulness')], 'P6 placeholder logs')
    for rv in AD.REVIEWERS:
        for k, b in real[rv].items():AD.files(p6, rv)[k].write_bytes(b)
    commit(base, [AD.files(p6, rv)['economic'] for rv in AD.REVIEWERS], 'P6 sealed logs replace the placeholders')
    r6 = AD.reveal_order(p6)
    c.ok('dual', 'a log whose committed history holds other content (a placeholder first) is a violation, not VERIFIED',
         r6['status'] == 'VIOLATED' and 'only the sealed content' in r6['detail'], r6['detail'])
    p7 = fresh('P7'); lg = judgments(p7)[3]
    for rv in AD.REVIEWERS:write_logs(p7, rv, *lg[rv]); AD.seal(p7, EXPORT, rv, REVIEWER[rv], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    commit(base, [AD.files(p7, rv)['seal'] for rv in AD.REVIEWERS], 'P7 seals')
    commit(base, [AD.files(p7, rv)[k] for rv in AD.REVIEWERS for k in ('economic', 'usefulness')], 'P7 logs')
    before = AD.reveal_order(p7)['status']
    s = AD.files(p7, 'R1')['seal']; s.write_text(json.dumps(json.loads(s.read_text(encoding='utf-8')), indent=2) + '\n', encoding='utf-8')
    commit(base, [s], 'P7 R1 seal rewritten after its first commit')
    r7 = AD.reveal_order(p7)
    c.ok('dual', 'a seal rewritten after its first commit is a violation, even though it still validates',
         before == 'VERIFIED' and r7['status'] == 'VIOLATED' and AD.dual(p7, EXPORT)['status'] == 'DUAL_SEALED', f"{before} -> {r7['status']}: {r7['detail']}")


def run(directory):
    base = Path(directory); c = R4.Checks()
    p1, export1 = build_packet(c, base, 'P1')
    p2, _ = build_packet(c, base, 'P2', classification=K.CLASSIFICATION_V1_1)
    snap1 = P.load_snapshot(p1 / 'snapshot.json')['snapshot']
    c.ok('conformance', 'P1 conforms to the registered R4 configuration; P2 (v1.1) is recorded as non-conforming',
         snap1['r4_configuration']['conforms'] is True and P.load_snapshot(p2 / 'snapshot.json')['snapshot']['r4_configuration']['conforms'] is False,
         'P1 conforms; P2 conforms=false')
    (p2 / 'deviation-001.json').write_text(json.dumps({'version': AD.DEVIATION_VERSION, 'packet': 'P2', 'kind': 'NON_CONFORMING_CONFIGURATION',
                                                       'reason': 'Synthetic owner stand-in: comparison run under v1.1 rules for illustration.',
                                                       'decided_by': {'name': 'Synthetic owner stand-in (fixture)', 'kind': 'SYNTHETIC_FIXTURE'},
                                                       'decided_at_utc': DR.START.isoformat(), 'treatment': 'SECONDARY_DESCRIPTIVE_ONLY'}), encoding='utf-8')
    git_init(base)
    items, econ_ids, use_ids, logs, flip = judgments(p1)
    exposure_checks(c, p1, items, econ_ids, logs, snap1['fixture'])
    for d in (p1, p2):
        lg = judgments(d)[3]
        for rv in AD.REVIEWERS:write_logs(d, rv, *lg[rv])
    for rv in AD.REVIEWERS:AD.seal(p1, EXPORT, rv, REVIEWER[rv], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    c.refused('sealing', 'a seal is immutable', lambda: AD.seal(p1, EXPORT, 'R1', REVIEWER['R1'], dict(CLEAN), 'SYNTHETIC_FIXTURE'), 'already sealed')
    f = AD.files(p1, 'R1')['economic']; original = f.read_bytes()
    f.write_bytes(original.replace(b'synthetic stand-in', b'edited after sealing', 1))
    c.refused('sealing', 'a log edited after sealing is refused', lambda: AD.dual(p1, EXPORT), 'changed after sealing')
    f.write_bytes(original)
    seals = [AD.files(p1, rv)['seal'] for rv in AD.REVIEWERS]
    commit(base, seals, 'P1 seals before logs are revealed')
    commit(base, [AD.files(p1, rv)[k] for rv in AD.REVIEWERS for k in ('economic', 'usefulness')], 'P1 logs revealed after both seals')
    dual = AD.dual(p1, EXPORT)
    c.ok('dual', 'two sealed reviewers give a consensus with agreement statistics', dual['status'] == 'DUAL_SEALED'
         and dual['agreement']['outcome']['items'] == len(econ_ids), f"outcome agreement {dual['agreement']['outcome']['raw_agreement']['numerator']}/"
         f"{dual['agreement']['outcome']['raw_agreement']['denominator']}, kappa {dual['agreement']['outcome']['kappa']}")
    c.ok('dual', 'a disagreement stays UNRESOLVED_DISAGREEMENT (never resolved by an AI or operator)',
         dual['adjudications'][flip]['outcome'] == AD.UNRESOLVED and [x['blind_id'] for x in dual['agreement']['outcome']['disagreements']] == [flip],
         f"1 disagreement: {dual['agreement']['outcome']['disagreements'][0]['R1']} vs {dual['agreement']['outcome']['disagreements'][0]['R2']}")
    c.ok('dual', 'git reveal order verified (seals committed before logs)', dual['reveal_order']['status'] == 'VERIFIED', dual['reveal_order']['status'])
    c.ok('usefulness', 'usefulness has its own agreement and consensus', dual['agreement']['usefulness']['items'] == len(use_ids)
         and all(dual['adjudications'][b]['usefulness'] == AD.UNRESOLVED for b in use_ids), f"usefulness kappa {dual['agreement']['usefulness']['kappa']}; R1 reused vs R2 not used: UNRESOLVED")
    # P2: R1 log revealed before R2 sealed -> reveal order violated (and P2 is non-conforming anyway).
    AD.seal(p2, EXPORT, 'R1', REVIEWER['R1'], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    commit(base, [AD.files(p2, 'R1')[k] for k in ('seal', 'economic', 'usefulness')], 'P2 R1 sealed and revealed early')
    AD.seal(p2, EXPORT, 'R2', REVIEWER['R2'], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    commit(base, [AD.files(p2, 'R2')[k] for k in ('seal', 'economic', 'usefulness')], 'P2 R2 sealed after R1 was visible')
    c.ok('dual', 'a log revealed before the other reviewer sealed is a reveal-order violation', AD.dual(p2, EXPORT)['reveal_order']['status'] == 'VIOLATED',
         AD.dual(p2, EXPORT)['reveal_order']['detail'])
    same = {'R1': REVIEWER['R1'], 'R2': REVIEWER['R1']}
    p3 = base / 'P3'; shutil.copytree(p2, p3, ignore=shutil.ignore_patterns('adjudication-seal-*', 'adjudications-*', 'warning-usefulness-*'))
    lg = judgments(p3)[3]
    for rv in AD.REVIEWERS:
        write_logs(p3, rv, [dict(r, adjudicator=same[rv]) for r in lg[rv][0]], [dict(r, adjudicator=same[rv]) for r in lg[rv][1]])
        AD.seal(p3, EXPORT, rv, same[rv], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    c.refused('dual', 'R1 and R2 must be two different humans', lambda: AD.dual(p3, EXPORT), 'two different humans')
    (p3 / 'adjudication-seal-R2.json').unlink()
    c.ok('dual', 'a single sealed reviewer is not dual adjudication', AD.dual(p3, EXPORT)['status'] == 'ADJUDICATION_NOT_DUAL', 'ADJUDICATION_NOT_DUAL')
    c.refused('dual', 'a prospective packet cannot be unblinded before both reviewers seal', lambda: P.unblind(p3, EXPORT), 'only after both reviewers have sealed')
    # Both seals and both reviewers' logs first appear in ONE commit: neither seal precedes the other's judgments.
    p4 = base / 'P4'; shutil.copytree(p2, p4, ignore=shutil.ignore_patterns('adjudication-seal-*', 'adjudications-*', 'warning-usefulness-*'))
    lg = judgments(p4)[3]
    for rv in AD.REVIEWERS:
        write_logs(p4, rv, *lg[rv]); AD.seal(p4, EXPORT, rv, REVIEWER[rv], dict(CLEAN), 'SYNTHETIC_FIXTURE')
    commit(base, [p4], 'P4 seals and logs together')
    same_commit = AD.dual(p4, EXPORT)['reveal_order']
    c.ok('dual', 'seals and logs first appearing in the same commit are a reveal-order violation (strict ancestry)',
         same_commit['status'] == 'VIOLATED' and 'same commit' in same_commit['detail'], same_commit['detail'])
    bad = p2 / 'deviation-002.json'
    bad.write_text(json.dumps({**json.loads((p2 / 'deviation-001.json').read_text(encoding='utf-8')), 'treatment': 'INCLUDE_IN_PRIMARY'}), encoding='utf-8')
    c.refused('conformance', 'no deviation record can admit a packet to the primary comparison', lambda: AD.deviations(p2, 'SYNTHETIC'), 'can never enter the primary')
    bad.unlink()
    zero_item_checks(c, base)
    content_history_checks(c, base, p2)
    rep = P.report([p1, p2], export_name=EXPORT)
    excluded = {x['packet']: x for x in rep['excluded_from_primary']}
    c.ok('conformance', 'only the conforming packet enters the primary comparison; the non-conforming one is listed with its owner deviation',
         list(excluded) == ['P2'] and {'NON_CONFORMING_CONFIGURATION', 'REVEAL_ORDER_VIOLATED'} <= set(excluded['P2']['problems'])
         and excluded['P2']['deviations'][0]['treatment'] == 'SECONDARY_DESCRIPTIVE_ONLY',
         f"P2 excluded: {sorted(excluded['P2']['problems'])}; deviation preserved")
    g = next(p for p in rep['packets'] if p['packet'] == 'P1')['G']
    acc = next(p for p in rep['packets'] if p['packet'] == 'P1')['suggestion_accounting']
    c.ok('usefulness', 'usefulness is reported separately and never counted as an economic discovery',
         'warning_usefulness' in g and acc['confirmed_economic_discoveries']['rows'] <= 1 and g['warning_usefulness']['UNRESOLVED_DISAGREEMENT'] == 1,
         f"G usefulness assessed {g['warning_usefulness']['assessed']} (unresolved {g['warning_usefulness']['UNRESOLVED_DISAGREEMENT']}); "
         f"economic discoveries {acc['confirmed_economic_discoveries']['rows']}")
    c.ok('report', 'one conforming pair stays INCONCLUSIVE', rep['classification'] == 'INCONCLUSIVE', rep['classification'])
    return {'checks': c.rows, 'dual': dual, 'report': rep}


def markdown(res):
    a = res['dual']['agreement']
    L = ['# Graph Pilot R4 Phase B: synthetic dry run (dual human adjudication)', '', f'> {M.BANNER}', '',
         '**NOT an R4 run.** Synthetic fixtures only, offline, in a temporary directory and a throwaway git repository. The two reviewers, the '
         'operator and the owner are labelled fixture stand-ins: no real person adjudicated and no AI judgment is used. Regenerate with '
         '`python -m src.research.graph pilot r4-phase-b-dry-run --write`; `--check` compares.', '',
         '| Area | Check | Observed | Result |', '|---|---|---|---|']
    for r in res['checks']:
        L.append(f"| {r['area']} | {r['check']} | {str(r['observed']).replace('|', '/')} | {r['result']} |")
    L += ['', '## Agreement (P1)', '', '| Judgment | Items | Agreements | Raw agreement | Cohen\'s kappa | Disagreements |', '|---|---:|---:|---:|---:|---:|']
    for k in ('outcome', 'economic_meaning', 'usefulness'):
        x = a[k]
        L.append(f"| {k} | {x['items']} | {x['agreements']} | {x['raw_agreement']['value']} | {x['kappa']} | {len(x['disagreements'])} |")
    L += ['', f"- Consensus rule: {res['dual']['consensus_rule']}.", f"- Reveal order: {res['dual']['reveal_order']['status']}.",
          f"- Primary comparison: {res['report']['notes'][-1] if res['report']['notes'] else ''}",
          f"- {sum(r['result'] == 'PASS' for r in res['checks'])}/{len(res['checks'])} checks passed."]
    return '\n'.join(L) + '\n'


def generate():
    tmp = Path(tempfile.mkdtemp(prefix='graph-r4-phase-b-'))
    try:res = run(tmp)
    finally:R4.remove_tree(tmp)
    if any(r['result'] != 'PASS' for r in res['checks']):
        raise DR.DryRunError('Phase B rehearsal failed: ' + '; '.join(f"{r['check']} ({r['observed']})" for r in res['checks'] if r['result'] != 'PASS'))
    return markdown(res)


def check():
    if not RECORD.exists() or RECORD.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_pilot_r4_phase_b_dry_run.md differs from the regenerated rehearsal; run pilot r4-phase-b-dry-run --write')
    return {'r4_phase_b_dry_run': 'PASS', 'network': 'none', 'acquisition': 0, 'record': RECORD.relative_to(ROOT).as_posix()}
