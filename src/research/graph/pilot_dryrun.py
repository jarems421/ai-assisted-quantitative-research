"""Synthetic end-to-end rehearsal of the proposed Discovery Lab + Graph v1 pilot, through the real CLIs.

Every step calls the ``discovery`` or ``graph`` command-line entry point with the exact arguments a
pilot session would type, in a temporary directory laid out like the pilot. Only the ledger clock is
replaced by a deterministic one, so the record regenerates byte-for-byte; it runs under the network
guard. Entities, documents, the adjudicator and all minutes are synthetic. Nothing is acquired and no
pilot is run.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shlex
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from src.research.discovery import cli as DCLI
from src.research.discovery.demo import clocks, entity, joins, passport, propositions, rec, selection, substitute
from src.research.discovery.ledger import Ledger
from src.research.graph import cli as GCLI
from src.research.graph import model as M
from src.research.graph import pilot as P
from src.research.sec_pilot.parsing import offline

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / 'docs/strategy/graph_pilot_dry_run.md'
AUTHORITY = 'docs/strategy/owner_graph_pilot_protocol_2026-10-21.md (offline synthetic rehearsal; no authority to acquire)'
START = datetime(2026, 10, 21, 12, 30, tzinfo=timezone.utc)  # after catalogue V002 was recorded and before this rehearsal was written
QUAY = entity('FACILITY', 'SYN_FACILITY:Q-1', 'Synthetic Quay One')
HARBOUR = entity('LISTED_COMPANY', 'SYN_LISTED:HARBOUR', 'Harbour Synthetic Holdings (fictional)')
BUNDLE = {'quay-one-throughput-2026-03.csv': b'facility,month,throughput_kt\nSYN_FACILITY:Q-1,2026-02,410\nSYN_FACILITY:Q-1,2026-03,265\n',
          'quay-operator-register.txt': b'SYN_FACILITY:Q-1 operated by SYN_LISTED:HARBOUR from 2020-01-01 (synthetic register)\n'}
NOTICE = b'Synthetic notice: Quay One berths 2-4 closed for maintenance, 2026-03-02 to 2026-03-27.\n'
SALT = 'dry-run-blinding-salt-0001'


class DryRunError(RuntimeError):
    """The rehearsal did not behave as the protocol requires."""


class Clock:
    def __init__(self):self.t = START

    def __call__(self):self.t += timedelta(minutes=1); return self.t.isoformat()

    def advance(self, minutes):self.t += timedelta(minutes=minutes)

    def at(self, seconds=30):return (self.t + timedelta(seconds=seconds)).isoformat()


def clocked(clock):
    """The Discovery Lab CLI's Ledger with this deterministic clock; everything else is unchanged."""
    class ClockedLedger(Ledger):
        def __init__(self, path, clock_=None):super().__init__(path, clock_ or clock)

        @classmethod
        def create(cls, path, campaign_, clock_=None):return super().create(path, campaign_, clock_ or clock)
    return ClockedLedger


def doc(locator, content, depth='VERIFIED_ORIGINAL_FIELD'):
    return {'locator': 'synthetic://' + locator, 'kind': 'ORIGINAL_DOCUMENT', 'depth': depth, 'passage': 'Synthetic rehearsal passage.',
            'sha256': hashlib.sha256(content).hexdigest(), 'archive': None, 'synthetic': True, 'reused_from': None}


def campaign(cid, title):
    return rec('campaign', id=cid, title=title, method='OBSERVATION_FIRST', fixture='SYNTHETIC', authority=AUTHORITY,
               question='What does a recorded change at Synthetic Quay One mean for its documented listed operator?',
               budget={'analyst_hours': 2, 'source_starts': 0, 'external_bytes': 0}, notes=['Synthetic pilot rehearsal; fictional entities.'])


def observation(oid, statement, value, units, evidence, kind='QUANTITY', why='', source='SRC-1'):
    return rec('observation', id=oid, source_id=source, kind=kind, statement=statement, value=value, units=units,
               denominator='single identified facility', entity=QUAY, depth='VERIFIED_ORIGINAL_FIELD', evidence=[evidence],
               clocks=clocks('2026-03-27', '2026-03-31', '2026-10-21T12:00:00+00:00'), as_of_status='VERIFIED_ONLY_RETROSPECTIVELY',
               why_informative=why or statement, outcome_independent=True)


def relationship(rid, reused=None):
    return rec('relationship', id=rid, source_entity=QUAY, target_entity=HARBOUR, type='OPERATION',
               direction='Harbour Synthetic Holdings operates Synthetic Quay One.',
               scope={'asset': 'SYN_FACILITY:Q-1', 'contract': 'NOT_APPLICABLE', 'product': 'bulk throughput', 'geography': 'synthetic port'},
               period={'start': '2020-01-01', 'end': 'OPEN'}, basis='DOCUMENTED', status='VERIFIED',
               evidence=[dict(doc('bundle/quay-operator-register.txt', BUNDLE['quay-operator-register.txt'], 'VERIFIED_ORIGINAL_RECORD'), reused_from=reused)],
               quantity_transfer={'status': 'NOT_APPLICABLE', 'method': 'NONE', 'evidence': [], 'note': 'Operator relationship only.'},
               limitations=['Operation does not establish the share of revenue earned at Quay One.'])


def candidate():
    return rec('candidate', id='CAND-1', method='OBSERVATION_FIRST', entry_record='OBS-1', population='Synthetic Quay One and its documented operator.',
               predictor={'observation_ids': ['OBS-1'], 'quantity': 'Berth closure at Quay One', 'units': 'berths closed x days', 'transformation': 'NONE'},
               exposure={'company': HARBOUR, 'relationship_ids': ['REL-1'], 'claim_basis': 'GROSS', 'allocation_required': False,
                         'gross': {'value': 12, 'units': 'USD million annual Quay One revenue (synthetic)'}, 'net': 'UNKNOWN',
                         'materiality': 'Synthetic: materiality not recorded.'},
               mechanism="Closed berths reduce handled volume and the operator's throughput revenue in the closure month.",
               outcome={'quantity': 'Operator-reported Quay One volume', 'units': 'kt/month', 'route': 'Issuer monthly operating statistics',
                        'source_id': 'UNKNOWN', 'status': 'ROUTE_ONLY', 'value': 'UNKNOWN', 'derived_from_observations': [], 'evidence': [],
                        'independence': 'Issuer-reported, not derived from the notice.'},
               joins=joins(legal_entity='VERIFIED', period='VERIFIED'),
               information_event={'description': 'Port maintenance notice', 'decision_time': 'UNKNOWN', 'basis': 'UNKNOWN'},
               public_time_route='Dated port notices; first-public time not certified.', horizon='Monthly statistics within weeks.',
               closest_substitute=substitute(False, 'Operator statements on maintenance.'), increment='UNKNOWN',
               falsification='Show that closure-month throughput at Quay One is not published at facility level.',
               missing_variables=['[REQ:REQ_REALISED_ACTIVITY] Quay One throughput during the closure month'], selection=selection(),
               propositions=propositions('Closure lowers handled volume.', 'UNKNOWN', 'UNKNOWN'),
               recommendation={'action': 'HOLD', 'reason': 'Closure-month throughput unobserved.'})


def effort(eid, category, minutes, kind='ANALYST_TIME', candidate_id=None):
    return rec('effort', id=eid, candidate_id=candidate_id, kind=kind, description=f'[PILOT:{category}] synthetic rehearsal step',
               analyst_minutes=minutes, source_starts=0, bytes='UNKNOWN' if kind == 'SEARCH' else 0, outcome='SUCCESS')


def log_row(arm, cid, operator, found_via, src, dst, basis, decision, minutes, record, kind='CONNECTION'):
    return {'connection_id': cid, 'arm': arm, 'kind': kind, 'operator': operator, 'found_via': found_via, 'source_record': src, 'target_record': dst,
            'basis': basis, 'arm_decision': decision, 'analyst_minutes': minutes, 'discovery_lab_record': record,
            'recorded_at_utc': START.isoformat(), 'notes': 'synthetic rehearsal'}


def stand_in_adjudication(item):
    """A labelled fixture stand-in for the owner, deciding from the blinded item only."""
    s = item['shared_structure']
    evidence = sorted({e['sha256'] for end in (item['from'], item['to']) for e in end['evidence'] if e['sha256']})
    if item['kind'] == 'AVOIDED_REPEAT':outcome, meaning, checked = 'CONFIRMED_AGAINST_ORIGINALS', 'UNCLEAR', [item['to']['evidence'][0]['locator']]
    elif s.get('relationship_period_covers_observation') == 'YES' and s['same_identified_entity']:outcome, meaning, checked = 'CONFIRMED_AGAINST_ORIGINALS', 'MEANINGFUL', evidence
    elif s['same_identified_entity']:outcome, meaning, checked = 'PLAUSIBLE_UNVERIFIED', 'UNCLEAR', []
    elif s['shared_requirement_tags']:outcome, meaning, checked = 'REJECTED_TRIVIAL', 'NOT_MEANINGFUL', []
    else:outcome, meaning, checked = 'REJECTED_FALSE', 'NOT_MEANINGFUL', []
    return {'blind_id': item['blind_id'], 'outcome': outcome, 'economic_meaning': meaning, 'checked_evidence': checked,
            'adjudicator': 'Synthetic owner stand-in (fixture)', 'adjudicator_kind': 'SYNTHETIC_FIXTURE', 'adjudicator_minutes': 2,
            'recorded_at_utc': START.isoformat(), 'notes': 'stand-in rule applied to the blinded item only'}


class Rehearsal:
    def __init__(self, clock):
        self.clock, self.lines, self.checks = clock, [], []

    def write(self, path, value):
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=1) + '\n', encoding='utf-8', newline='\n')
        return path.as_posix()

    def cli(self, module, argv, expect=0, show=True):
        main = {'discovery': DCLI.main, 'graph': GCLI.main}[module]
        out, err, code = io.StringIO(), io.StringIO(), 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:main(argv)
            except SystemExit as error:code = error.code if isinstance(error.code, int) else 1
        command = f'python -m src.research.{module} ' + shlex.join(argv)
        if code != expect:raise DryRunError(f'{command} exited {code}, expected {expect}: {err.getvalue().strip()}')
        if show:self.lines += ['```sh', command + ('' if expect == 0 else f'   # exit {code}: {err.getvalue().strip()}'), '```']
        return out.getvalue() if expect == 0 else err.getvalue()

    def refuse(self, name, module, argv, reason):
        """A command that must exit 2 for the stated reason, not merely fail."""
        self.check(name, reason in self.cli(module, argv, expect=2))

    def add(self, ledger, kind, record, name):
        self.cli('discovery', ['add', ledger, kind, self.write(f'records/{name}.json', record)], show=False)

    def check(self, name, ok):
        self.checks.append(name)
        if not ok:raise DryRunError(f'rehearsal assertion failed: {name}')

    def say(self, *text):self.lines += list(text)


def arm_campaign(r, packet, arm):
    """The start of one arm's session: a new observation recorded after the campaign start."""
    led = f'pilot/{packet}/{arm}.jsonl'
    r.cli('discovery', ['init', led, r.write(f'records/{packet}-{arm}-campaign.json', campaign(f'DLC-G{packet}-{arm}', f'Rehearsal packet {packet}, arm {arm}'))])
    r.add(led, 'effort', effort('EFF-1', 'READING', 15), f'{packet}-{arm}-eff1')
    r.add(led, 'source', passport('SRC-1', 'Synthetic port notices', field='berth_status', units='berths', publication='VERIFIED_ORIGINAL_RECORD'),
          f'{packet}-{arm}-src')
    r.add(led, 'effort', effort('EFF-2', 'RECORDING', 5), f'{packet}-{arm}-eff2')
    r.add(led, 'observation', observation('OBS-1', 'Quay One berths 2-4 closed for maintenance in March 2026.', 3, 'berths',
                                          doc('arm/quay-one-closure-notice', NOTICE), 'EVENT',
                                          '[MEASURES:REQ_REALISED_ACTIVITY] A closure constrains realised throughput at Quay One.'), f'{packet}-{arm}-obs1')
    r.say('', f'Arm {arm} started at {Ledger(led).load().events[0]["recorded_at_utc"]} and appended OBS-1 at {r.clock.t.isoformat()}.')
    return led, r.clock.at()


def finish_arm(r, arm, led, extra):
    for i, (category, minutes, kind) in enumerate(extra, 3):r.add(led, 'effort', effort(f'EFF-{i}', category, minutes, kind), f'{arm}-eff{i}')
    r.add(led, 'relationship', relationship('REL-1', 'FROZEN_PACKET/REL-P-1'), f'{arm}-rel1')
    r.add(led, 'candidate', candidate(), f'{arm}-cand1')
    r.cli('discovery', ['freeze', led, 'CAND-1'])
    r.add(led, 'effort', effort('EFF-F', 'FREEZE_PREP', 15, candidate_id='CAND-1'), f'{arm}-efff')


def packet_ledger(r, packet, records):
    led = f'pilot/{packet}/packet.jsonl'
    r.cli('discovery', ['init', led, r.write(f'records/{packet}-campaign.json', campaign(f'DLC-GPKT-{packet[1:]}', f'Rehearsal packet {packet}'))])
    r.add(led, 'source', passport('SRC-P-1', 'Synthetic port register', field='throughput', units='kt/month', publication='VERIFIED_ORIGINAL_RECORD'), f'{packet}-src')
    for kind, record in records:r.add(led, kind, record, f"{packet}-{record['id']}")
    return led


def snapshot(r, packet, led, bundle, frozen):
    d = f'pilot/{packet}'
    return json.loads(r.cli('graph', ['pilot', 'snapshot', f'{d}/snapshot.json', '--packet', packet, '--packet-ledger', led,
                                      '--arm-ledger', 'S', f'{d}/S.jsonl', f'DLC-G{packet}-S', '--arm-ledger', 'G', f'{d}/G.jsonl', f'DLC-G{packet}-G',
                                      '--bundle', bundle, '--frozen-at', frozen]))


def visibility_table(receipts):
    rows = [('snapshot', lambda v: v['snapshot_sha256'][:16] + '...'), ('query time', lambda v: v['query_at_utc']),
            ('frozen packet', lambda v: f"{v['frozen_prior']['packet_ledger']['campaign']}, {v['frozen_prior']['packet_ledger']['events']} events, "
                                        f"head {v['frozen_prior']['packet_ledger']['head_hash'][:12]}..."),
            ('catalogue', lambda v: v['frozen_prior']['catalogue_sha256'][:16] + '...'),
            ('own ledger', lambda v: f"{v['own_ledger']['campaign']}: {v['own_ledger']['events_visible']} of {v['own_ledger']['events_total']} events"),
            ('never visible', lambda v: '; '.join(v['not_visible']))]
    return ['| Input | ' + ' | '.join(f'Arm {a}' for a in receipts) + ' |', '|---|' + '---|' * len(receipts),
            *[f'| {name} | ' + ' | '.join(f(v) for v in receipts.values()) + ' |' for name, f in rows]]


def run(directory, clock):
    r = Rehearsal(clock); os.chdir(directory); d = 'pilot/P1'
    r.say('# Graph pilot dry run (synthetic rehearsal)', '', f'> {M.BANNER}', '',
          'Generated by `python -m src.research.graph pilot dry-run --write`; `--check` regenerates and compares it. Every command below ran '
          'against the implemented CLI, in a temporary directory laid out like the pilot (`pilot/<packet>/`; private bundle and key under '
          '`private/`). Entities, documents, the adjudicator and all minutes are synthetic; nothing was acquired and no pilot ran. Only the '
          'ledger clock is fixed, so times are deterministic.', '', '## 1. Frozen packet creation', '')
    packet = packet_ledger(r, 'P1', [('observation', observation('OBS-P-1', 'Quay One monthly throughput fell from 410 to 265 kt in March 2026.',
                                                                 {'from': 410, 'to': 265}, 'kt/month',
                                                                 doc('bundle/quay-one-throughput-2026-03.csv', BUNDLE['quay-one-throughput-2026-03.csv']),
                                                                 'STATE_CHANGE', source='SRC-P-1')),
                                     ('relationship', relationship('REL-P-1'))])
    for name, content in BUNDLE.items():
        Path('private/P1/bundle').mkdir(parents=True, exist_ok=True); Path('private/P1/bundle', name).write_bytes(content)
    frozen = clock.at(); clock.advance(4)
    out = snapshot(r, 'P1', packet, 'private/P1/bundle', frozen)
    r.say('', f"Snapshot `{out['snapshot_sha256'][:16]}...` frozen at {out['frozen_at_utc']}: packet ledger {out['prior']['campaign']} pinned at "
          f"{out['prior']['events']} events (head `{out['prior']['head_hash'][:12]}...`), catalogue V002 by SHA-256, {len(BUNDLE)} bundle files by SHA-256.")

    r.say('', '## 2. Both arm inputs', '', 'Each arm works in its own copy (in the pilot, its own git worktree) and verifies the snapshot and its bundle copy first.')
    summaries = {}
    for arm in P.ARMS:
        shutil.copytree('private/P1/bundle', f'worktree-{arm}/bundle')
        summaries[arm] = json.loads(r.cli('graph', ['pilot', 'verify', f'{d}/snapshot.json', '--bundle', f'worktree-{arm}/bundle']))
    r.check('both arms verify identical starting inputs: snapshot, packet prefix, catalogue and bundle', summaries['S'] == summaries['G'])
    fmt = {'snapshot_sha256': lambda v: v[:16] + '...', 'packet_ledger': lambda v: f"{v['campaign']}, {v['events']} events, head {v['head_hash'][:12]}...",
           'catalogue_sha256': lambda v: v[:16] + '...', 'bundle_digest': lambda v: v[:16] + '...', 'bundle_verified': str}
    r.say('', '| Starting input | Arm S | Arm G |', '|---|---|---|', *[f"| {k} | {f(summaries['S'][k])} | {f(summaries['G'][k])} |" for k, f in fmt.items()], '')
    shutil.copytree('private/P1/bundle', 'private/tamper/bundle'); Path('private/tamper/bundle/quay-operator-register.txt').write_bytes(b'altered\n')
    r.refuse('an altered bundle copy is refused', 'graph', ['pilot', 'verify', f'{d}/snapshot.json', '--bundle', 'private/tamper/bundle'], 'bundle differs')

    r.say('', '## 3. Arm S (structured search only)')
    s_led, s_query = arm_campaign(r, 'P1', 'S')
    r.refuse('a snapshot cannot be frozen once an arm ledger exists', 'graph',
             ['pilot', 'snapshot', f'{d}/snapshot-again.json', '--packet', 'P1', '--packet-ledger', packet, '--arm-ledger', 'S', s_led, 'DLC-GP1-S',
              '--arm-ledger', 'G', f'{d}/G.jsonl', 'DLC-GP1-G', '--frozen-at', clock.at()], 'already exists')
    s_out = json.loads(r.cli('graph', ['baseline-search', 'DLC-GP1-S', 'OBS-1', '--snapshot', f'{d}/snapshot.json', '--arm', 'S', '--query-at', s_query]))
    r.say('', 'Contexts found: ' + ', '.join(f"{c['record']} {c['bases']}" for c in s_out['contexts']) + '; catalogue: '
          + ', '.join(f"{k} {v['bases']}" for k, v in sorted(s_out['catalogue'].items())) + '.')
    r.check('arm S finds its own new observation at its query time', s_out['observation'] == 'DLC-GP1-S/OBS-1')
    r.refuse('arm S cannot run a graph operator', 'graph', ['revisit', 'OBS-1', '--snapshot', f'{d}/snapshot.json', '--arm', 'S', '--query-at', s_query],
             'uses no graph operator')
    finish_arm(r, 'S', s_led, [('BASELINE_SEARCH', 10, 'ANALYST_TIME'), ('READING', 10, 'ANALYST_TIME'), ('SOURCE_SEARCH', 5, 'SEARCH')])
    s_conn = [log_row('S', P.connection_id('DLC-GP1-S/OBS-1', c['record'], c['bases']), 'baseline-search', 'ANALYST_READING', 'DLC-GP1-S/OBS-1',
                      c['record'], c['bases'], 'ACCEPTED' if 'REL-' in c['record'] else 'DECLINED', 6, 'CAND-1' if 'REL-' in c['record'] else None)
              for c in s_out['contexts']]
    s_conn += [log_row('S', P.connection_id('DLC-GP1-S/OBS-1', h, v['bases']), 'baseline-search', 'ANALYST_READING', 'DLC-GP1-S/OBS-1', h, v['bases'],
                       'DECLINED', 3, None) for h, v in sorted(s_out['catalogue'].items())]
    clock.advance(3); r.add(s_led, 'observation', observation('OBS-2', 'Later arm S record.', 1, 'count', doc('arm/later-s', b'later S\n')), 'S-obs2')

    r.say('', '## 4. Arm G (structured search plus Graph v1)')
    clock.advance(5)
    g_led, g_query = arm_campaign(r, 'P1', 'G')
    snap = ['--snapshot', f'{d}/snapshot.json', '--arm', 'G', '--query-at', g_query]
    start = Ledger(g_led).load().events[0]['recorded_at_utc']
    r.say('', "The superseded command form, one `--known-at` set to the campaign start, cannot see the arm's own new observation:")
    r.refuse('defect reproduced: --known-at START hides the current observation', 'graph',
             ['revisit', 'OBS-1', '--mode', 'synthetic', '--ledgers', packet, g_led, '--known-at', start], "no node matches 'OBS-1'")
    r.say('', 'With the snapshot, the same observation is queryable at its query time:')
    revisit = json.loads(r.cli('graph', ['revisit', 'OBS-1', '--json', *snap]))
    complements = json.loads(r.cli('graph', ['complements', 'OBS-1', '--json', *snap]))
    sugg = json.loads(r.cli('graph', ['suggestions', 'DLC-GP1-G', *snap]))['suggestions']
    g_base = json.loads(r.cli('graph', ['baseline-search', 'DLC-GP1-G', 'OBS-1', *snap]))
    built = json.loads(r.cli('graph', ['build', '--check', *snap]))
    r.cli('graph', ['same-gap', 'REQ_REALISED_ACTIVITY', *snap]); r.cli('graph', ['explain', 'OBS-1', 'SYN_LISTED:HARBOUR', *snap])
    r.say('', f"revisit: {', '.join(x['match'] for x in revisit['results'])}. complements: {', '.join(x['match'] for x in complements['results'])}. "
          f"suggestions exported: {len(sugg)}, of which {sum(s['baseline_structured_discoverable'] for s in sugg)} structured search also finds. "
          f"Graph digest `{built['digest'][:16]}...`.", '', 'Visibility receipts at each arm\'s query time:', '',
          *visibility_table({'S': s_out['visibility'], 'G': built['visibility']}))
    r.check('revisit, complements and suggestions all see the current observation', revisit['results'] and complements['results'] and sugg)
    r.check('graph inputs are exactly the pinned packet and the own ledger as of the query time',
            [i['cut']['role'] for i in built['inputs']] == ['FROZEN_PRIOR_PACKET', 'OWN_ARM_G_AS_OF_QUERY'] and built['excluded'] == [])
    r.check('both arms see identical frozen prior knowledge', built['visibility']['frozen_prior'] == s_out['visibility']['frozen_prior'])
    r.check('the structured searches of both arms return the same packet and catalogue context',
            [c['record'] for c in g_base['contexts']] == [c['record'] for c in s_out['contexts']] and g_base['catalogue'] == s_out['catalogue'])
    r.say('', 'Isolation and time refusals:')
    r.refuse("the other arm's records are not in the graph arm's view", 'graph', ['show', 'DLC-GP1-S/OBS-1@1', *snap], 'no node matches')
    r.refuse("the other arm's campaign is not in the graph arm's structured search", 'graph', ['baseline-search', 'DLC-GP1-S', 'OBS-1', *snap], 'not recorded')
    r.refuse('extra ledgers cannot be mixed into a snapshot query', 'graph', ['revisit', 'OBS-1', *snap, '--ledgers', s_led], 'snapshot inputs are fixed')
    r.refuse('a future query time is refused', 'graph',
             ['revisit', 'OBS-1', '--snapshot', f'{d}/snapshot.json', '--arm', 'G', '--query-at', '2099-01-01T00:00:00+00:00'], 'in the future')
    r.refuse('a query time before the snapshot is refused', 'graph',
             ['revisit', 'OBS-1', '--snapshot', f'{d}/snapshot.json', '--arm', 'G', '--query-at', START.isoformat()], 'precedes the packet snapshot')
    finish_arm(r, 'G', g_led, [('GRAPH_QUERY', 10, 'ANALYST_TIME'), ('SUGGESTION_REVIEW', 15, 'ANALYST_TIME'), ('BASELINE_SEARCH', 5, 'ANALYST_TIME'),
                               ('SOURCE_SEARCH', 5, 'SEARCH')])
    r.add(g_led, 'effort', effort('EFF-AVOID', 'AVOIDED_REPEAT', 5), 'G-effavoid')
    clock.advance(3); r.add(g_led, 'observation', observation('OBS-2', 'Later arm G record.', 1, 'count', doc('arm/later-g', b'later G\n')), 'G-obs2')
    later = clock.at()
    r.say('', f'Arm G then appended OBS-2 at {clock.t.isoformat()}. Replaying the earlier query time, then querying later:')
    replay = json.loads(r.cli('graph', ['build', '--check', *snap]))
    r.check('replaying a query time gives the identical graph after later appends', replay['digest'] == built['digest'])
    r.refuse('a record appended after the query time is invisible at that time', 'graph', ['show', 'OBS-2', *snap], "no node matches 'OBS-2'")
    shown = r.cli('graph', ['show', 'OBS-2', '--snapshot', f'{d}/snapshot.json', '--arm', 'G', '--query-at', later])
    r.check('the same record is visible at a later query time', 'Later arm G record.' in shown)
    g_conn = [log_row('G', s['suggestion_id'], s['operator'], 'BASELINE_SEARCH_DISCOVERABLE' if s['baseline_structured_discoverable'] else 'GRAPH_ONLY',
                      s['target'], s['match'], s['match_bases'], 'DECLINED' if s['match'].startswith('history:') else 'ACCEPTED', 4,
                      None if s['match'].startswith('history:') else 'CAND-1') for s in sugg]
    g_conn.append(log_row('G', P.connection_id('DLC-GP1-G/OBS-1', 'HIST-F01/F6', ['AVOIDED']), 'revisit', 'GRAPH_ONLY', 'DLC-GP1-G/OBS-1', 'HIST-F01/F6',
                          ['AVOIDED: requesting vessel tracks to infer berth activity', 'HIST-F01/F6: route contexts do not establish work'],
                          'ACCEPTED', 3, 'EFF-AVOID', kind='AVOIDED_REPEAT'))

    r.say('', '## 5. Connection logs, dispositions and blinded adjudication', '')
    for arm, rows in (('S', s_conn), ('G', g_conn)):
        Path(f'{d}/connections-{arm}.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows), encoding='utf-8', newline='\n')
        r.cli('graph', ['pilot', 'connections', f'{d}/connections-{arm}.jsonl', '--arm', arm])
    Path('private/bad.jsonl').write_text(json.dumps(dict(s_conn[0], connection_id='SUG-' + '0' * 12)) + '\n', encoding='utf-8')
    r.refuse('the structured arm cannot log a graph suggestion', 'graph', ['pilot', 'connections', 'private/bad.jsonl', '--arm', 'S'], 'no graph suggestions')
    clock.advance(10)
    for arm in P.ARMS:
        r.add(f'{d}/{arm}.jsonl', 'disposition', rec('disposition', id='DSP-1', candidate_id='CAND-1', version=1, decision='HOLD', reason_type='OBSERVATION',
                                                   reason='[DECISIVE:CAND-1] Closure-month Quay One throughput is not observed.', scope='CAND-1 v1',
                                                   decided_by={'name': 'Synthetic owner stand-in (fixture)', 'kind': 'SYNTHETIC_FIXTURE'}), f'{arm}-dsp')
    r.cli('discovery', ['validate', s_led, g_led])
    r.say('Dispositions were recorded for both arms only after both campaigns had ended. A separate preparer session then built the export:')
    out = json.loads(r.cli('graph', ['pilot', 'blind', f'{d}/snapshot.json', '--log', 'S', f'{d}/connections-S.jsonl', '--log', 'G',
                                     f'{d}/connections-G.jsonl', '--salt', SALT, '--out', f'{d}/blind.json', '--key', 'private/P1/key.json']))
    export = json.loads(Path(f'{d}/blind.json').read_text(encoding='utf-8')); text = json.dumps(export['items'])
    leaks = [x for x in ('DLC-GP1-S', 'DLC-GP1-G', 'SUG-', 'CON-', 'GRAPH_ONLY', 'BASELINE_SEARCH_DISCOVERABLE', 'ANALYST_READING', '"arm"', 'ACCEPTED',
                         'DECLINED', 'revisit', 'complements', 'baseline-search', 'match_bases', 'synthetic rehearsal') if x in text]
    r.check(f'the blinded items carry no arm, campaign id, suggestion id, operator, attribution, arm decision or note (found: {leaks or "none"})', not leaks)
    fields = sorted({k for i in export['items'] for end in (i['from'], i['to']) for k in end})
    r.say('', f"{out['items']} items, shuffled; the key is sealed by hash `{out['key_sha256'][:16]}...` and held privately. Each endpoint is rendered "
          f"by one function whichever arm logged it (fields: {', '.join(fields)}), with one mechanical `shared_structure` per item.")
    adj = [stand_in_adjudication(i) for i in export['items']]
    Path(f'{d}/adjudications.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in adj), encoding='utf-8', newline='\n')
    r.cli('graph', ['pilot', 'adjudications', f'{d}/blind.json', f'{d}/adjudications.jsonl'])
    shutil.copy('private/P1/key.json', f'{d}/key.json')
    r.say('After adjudication was complete, the key was unsealed into the packet directory for reporting.')

    r.say('', '## 6. Budget accounting', '')
    accounts = {arm: json.loads(r.cli('graph', ['pilot', 'account', f'{d}/snapshot.json', '--arm', arm])) for arm in P.ARMS}
    r.say('', '| Arm | Minutes (all) | Graph minutes | Searches | Source starts | Bytes | Violations |', '|---|---:|---:|---:|---:|---:|---|',
          *[f"| {a} | {x['used']['analyst_minutes']} | {x['graph_minutes']} | {x['used']['searches']} | {x['used']['source_starts']} | "
            f"{x['used']['bytes']} | {len(x['violations'])} |" for a, x in accounts.items()],
          '', 'Ceilings per campaign: ' + ', '.join(f'{k} {v}' for k, v in P.CEILINGS.items()) + '. Synthetic campaigns cannot record source starts or bytes.')
    r.check('graph time is counted inside the graph arm budget', accounts['G']['graph_minutes'] == 25 and accounts['S']['graph_minutes'] == 0)

    r.say('', '## 7. Paired report', '')
    rep = r.cli('graph', ['pilot', 'report', d])
    r.say('', *rep.splitlines()[1:])
    r.check('a single packet pair is reported as inconclusive, never as a graph verdict', 'INCONCLUSIVE' in rep)

    r.say('', '## 8. A later packet sees no earlier pilot ledger', '',
          'Packet P2 (same method, for brevity) concerns the same facility, so a join to P1 records would be possible if they were inputs.')
    clock.advance(5)
    notice2 = b'Synthetic notice: Quay One dredging, April 2026.\n'
    packet2 = packet_ledger(r, 'P2', [('observation', observation('OBS-P-1', 'Quay One dredging scheduled for April 2026.', 1, 'events',
                                                                  doc('bundle/quay-one-dredging', notice2), 'EVENT', source='SRC-P-1'))])
    Path('private/P2/bundle').mkdir(parents=True); Path('private/P2/bundle/quay-one-dredging.txt').write_bytes(notice2)
    frozen2 = clock.at(); clock.advance(2)
    snapshot(r, 'P2', packet2, 'private/P2/bundle', frozen2)
    p2_led, p2_query = arm_campaign(r, 'P2', 'G')
    found = json.loads(r.cli('graph', ['complements', 'OBS-1', '--json', '--snapshot', 'pilot/P2/snapshot.json', '--arm', 'G', '--query-at', p2_query]))
    matches = [x['match'] for x in found['results']]
    r.say('', f"complements for P2 arm G: {', '.join(matches)}.")
    r.check('the later packet joins only its own frozen packet, never P1 packet or arm ledgers', matches and all('DLC-GPKT-2/' in m for m in matches))
    r.refuse('a P1 record is not visible from the P2 snapshot', 'graph',
             ['show', 'DLC-GP1-G/OBS-1@1', '--snapshot', 'pilot/P2/snapshot.json', '--arm', 'G', '--query-at', p2_query], 'no node matches')

    r.say('', '## Rehearsal assertions', '', f'All {len(r.checks)} passed (a failure stops the rehearsal):', '', *[f'- {name}' for name in r.checks])
    return '\n'.join(r.lines) + '\n'


def generate():
    here, clock = Path.cwd(), Clock()
    with tempfile.TemporaryDirectory() as tmp, offline(), patch.object(DCLI, 'Ledger', clocked(clock)):
        try:return run(tmp, clock)
        finally:os.chdir(here)


def check():
    if not RECORD.exists() or RECORD.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_pilot_dry_run.md differs from the regenerated rehearsal; run pilot dry-run --write')
    return {'dry_run': 'PASS', 'network': 'blocked', 'acquisition': 0, 'record': RECORD.relative_to(ROOT).as_posix()}
