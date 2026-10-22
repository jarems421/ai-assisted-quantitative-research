"""Graph v1.1 adversarial synthetic evaluation (R4 readiness, Phase A): reused citations, trivial shared identifiers,
mismatched economic periods, misleading tags, name- and ticker-only identities, and genuine documented relationships.

Functional behaviour only. The fixtures and their ground truth were written together by the implementer, before any
system ran on them; they are not an independent or real-world benchmark, and no accuracy, discovery or investment
claim follows. Results are reported as found: no operator was changed after running this set (changing one now would be
tuning on it). Systems compared on identical inputs:

* ``graph_v1``: the R3 counting practice, every operator result counted as a connection;
* ``graph_v1_1``: only ECONOMIC_CONNECTION_CANDIDATE counts as a connection; warnings and unsupported matches are shown;
* ``structured_search``: the competent structured-ledger baseline (``baseline.structured_search``), every hit a result.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.research.discovery import records as R
from src.research.discovery.demo import Clock, entity, passport, rec, syn
from src.research.discovery.ledger import Ledger
from src.research.graph import baseline as B
from src.research.graph import connections as K
from src.research.graph import model as M
from src.research.graph import operators as O
from src.research.graph import quality as Q
from src.research.graph.fixtures import campaign, obs
from src.research.graph.project import build
from src.research.graph.rules import View

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / 'docs/strategy/graph_v1_1_adversarial.md'
U = R.UNKNOWN
P777, P888 = entity('PRODUCT', 'SYN_PRODUCT:UDI-777', 'Synthetic catheter kit UDI-777'), entity('PRODUCT', 'SYN_PRODUCT:UDI-888', 'Synthetic pump UDI-888')
SUPPLYCO = entity('LISTED_COMPANY', 'SYN_LISTED:SUPPLYCO', 'Supplyco Synthetic Manufacturing (fictional)')
OLDCO = entity('LISTED_COMPANY', 'SYN_LISTED:OLDCO', 'Oldco Synthetic Devices (fictional)')
INSPECTCO = entity('LISTED_COMPANY', 'SYN_LISTED:INSPECTCO', 'Inspectco Synthetic Compliance Software (fictional)')
AGENCY = entity('OTHER', 'SYN_REGULATOR:AGENCY-1', 'Synthetic Agency One (a regulator)')
NOTICE = syn('shared/notice-n5', 'VERIFIED_ORIGINAL_RECORD')


def build_fixtures(directory, clock=None):
    """A registry campaign recorded earlier, and a new recall campaign whose observations are the queries."""
    d, clock = Path(directory), clock or Clock()
    r = Ledger.create(d / 'AR.jsonl', campaign('DLC-ASYN-REG', 'Synthetic device registry and agency statistics', 'OBSERVATION_FIRST',
                                              'What do registries and agency statistics document?'), clock)
    r.append('source', passport('SRC-AR', 'Synthetic device registry', field='record', units='status', scheme='SYN_PRODUCT', object_type='PRODUCT'))
    r.append('observation', obs('OBS-AR-1', 'SRC-AR', 'Registry: UDI-777 is a sterile catheter kit.', 1, 'kits/box', P777, '2025-03-01', '2025-03-01',
                                '2026-10-01T00:00:00+00:00', 'Product registry entry.'))
    r.append('observation', rec('observation', id='OBS-AR-2', source_id='SRC-AR', kind='EVENT', statement='Notice N-5 published.', value='published', units='status',
                                denominator='single notice', entity=entity('OTHER', 'SYN_NOTICE:N-5', 'Synthetic notice N-5'), depth='VERIFIED_ORIGINAL_RECORD',
                                evidence=[NOTICE], clocks={k: {'value': U, 'basis': U, 'evidence': []} for k in R.CLOCKS}, as_of_status='UNVERIFIED',
                                why_informative='Notice text.', outcome_independent=True))
    r.append('observation', obs('OBS-AR-3', 'SRC-AR', 'Agency One published 212 inspections.', 212, 'inspections/year', AGENCY, '2025-01-31', '2025-01-31',
                                '2026-10-01T00:00:00+00:00', 'Agency workload.'))
    r.append('relationship', Q.relationship('REL-AR-1', SUPPLYCO, P777, 'SUPPLIER_CUSTOMER', 'Supplyco manufactures UDI-777 under contract.', '2024-01-01', 'OPEN'))
    r.append('relationship', Q.relationship('REL-AR-2', OLDCO, P888, 'SUPPLIER_CUSTOMER', 'Oldco supplied UDI-888.', '2008-01-01', '2011-12-31'))
    r.append('candidate', Q.claim('CAND-AR-1', 'OBS-AR-1', ['OBS-AR-1'], SUPPLYCO, 'Recall replacement volume raises Supplyco contract revenue.',
                                  ['[REQ:REQ_AVAILABLE_CAPACITY] spare sterilisation capacity'], relationships=['REL-AR-1']))
    r.append('candidate', Q.claim('CAND-AR-2', 'OBS-AR-3', ['OBS-AR-3'], INSPECTCO, 'Higher inspection counts raise demand for compliance software.',
                                  ['[REQ:REQ_DOCUMENTED_ALLOCATION] software revenue allocated to agency contracts']))
    n = Ledger.create(d / 'AN.jsonl', campaign('DLC-ASYN-NEW', 'Synthetic new recall campaign', 'OBSERVATION_FIRST', 'What does each new record connect to?'), clock)
    n.append('source', passport('SRC-AN', 'Synthetic recall notices', field='recall', units='status', scheme='SYN_PRODUCT', object_type='PRODUCT'))

    def event(oid, text, ent, why, evidence=None):
        return rec('observation', id=oid, source_id='SRC-AN', kind='EVENT', statement=text, value='recorded', units='status', denominator='single record',
                   entity=ent, depth='VERIFIED_ORIGINAL_FIELD', evidence=[evidence or syn(f'recalls/{oid}')],
                   clocks={'economic_occurrence': {'value': '2025-07-02', 'basis': 'DOCUMENT_DATE', 'evidence': [syn(f'dates/{oid}')]},
                           'first_public': {'value': U, 'basis': U, 'evidence': []}, 'source_version': {'value': U, 'basis': U, 'evidence': []},
                           'retrieval': {'value': U, 'basis': U, 'evidence': []}},
                   as_of_status='VERIFIED_ONLY_RETROSPECTIVELY', why_informative=why, outcome_independent=True)
    n.append('observation', event('OBS-AN-1', 'Catheter kit UDI-777 recalled.', P777, 'The recall itself.'))
    n.append('observation', event('OBS-AN-2', 'Pump UDI-888 recalled.', P888, 'A recall of a once-supplied pump.'))
    n.append('observation', event('OBS-AN-3', 'Notice N-5 restated.', entity('OTHER', 'SYN_NOTICE:N-5-COPY', 'Restated notice'), 'Restates the registry notice.',
                                  dict(NOTICE, reused_from='DLC-ASYN-REG/OBS-AR-2')))
    n.append('observation', event('OBS-AN-4', 'Agency One classified a recall.', AGENCY, 'The regulator acted.'))
    n.append('observation', event('OBS-AN-5', 'Warehouse two shipments paused.', entity('FACILITY', 'SYN_FACILITY:WH-2', 'Synthetic warehouse two'),
                                  '[MEASURES:REQ_DOCUMENTED_ALLOCATION] could show how costs are allocated'))
    n.append('observation', event('OBS-AN-6', 'Supplyco named in a recall letter.', entity('LEGAL_ENTITY', 'NAME:Supplyco', 'Supplyco'), 'Named only.'))
    n.append('observation', event('OBS-AN-7', 'SPLY named in a recall letter.', entity('LISTED_COMPANY', 'TICKER:SPLY', 'SPLY'), 'Ticker only.'))
    n.append('observation', event('OBS-AN-8', 'Notice N-5 also lists UDI-777.', entity('OTHER', 'SYN_NOTICE:N-5-LIST', 'Notice listing'), 'Independent use of the notice.',
                                  NOTICE))
    n.append('observation', event('OBS-AN-9', 'UDI-777 recall extended.', P777, '[MEASURES:REQ_AVAILABLE_CAPACITY] replacement demand'))
    return [d / 'AR.jsonl', d / 'AN.jsonl']


# Ground truth, written with the fixtures from the economics alone, before any system ran.
TASKS = (
    {'id': 'A1', 'challenge': 'reused citation', 'operator': 'shared', 'query': 'DLC-ASYN-NEW/OBS-AN-3', 'pair': 'campaign:DLC-ASYN-REG', 'truth': 'NOT_CONNECTED',
     'why': 'The record restates evidence copied from the registry record: one record, not a second one.'},
    {'id': 'A2', 'challenge': 'shared document, independent use', 'operator': 'shared', 'query': 'DLC-ASYN-NEW/OBS-AN-8', 'pair': 'campaign:DLC-ASYN-REG',
     'truth': 'CONNECTED_NOT_INDEPENDENT', 'why': 'Both cite notice N-5 itself: worth investigating, never independent corroboration.'},
    {'id': 'A3', 'challenge': 'trivial shared identifier', 'operator': 'revisit', 'query': 'DLC-ASYN-NEW/OBS-AN-4', 'pair': 'DLC-ASYN-REG/CAND-AR-2', 'truth': 'TRIVIAL',
     'why': 'The same regulator classified a recall and published inspection counts; nothing links the recall to compliance-software demand.'},
    {'id': 'A4', 'challenge': 'trivial shared identifier', 'operator': 'complements', 'query': 'DLC-ASYN-NEW/OBS-AN-4', 'pair': 'DLC-ASYN-REG/OBS-AR-3', 'truth': 'TRIVIAL',
     'why': "A regulator's annual inspection count is not context for one recall classification."},
    {'id': 'A5', 'challenge': 'mismatched economic period', 'operator': 'complements', 'query': 'DLC-ASYN-NEW/OBS-AN-2', 'pair': 'DLC-ASYN-REG/REL-AR-2',
     'truth': 'NOT_CONNECTED', 'why': 'The supply relationship ended in 2011; the recall is from 2025.'},
    {'id': 'A6', 'challenge': 'misleading tag', 'operator': 'revisit', 'query': 'DLC-ASYN-NEW/OBS-AN-5', 'pair': 'DLC-ASYN-REG/CAND-AR-2', 'truth': 'WARNING_ONLY',
     'why': 'A warehouse pause shares only an allocation tag with a compliance-software claim.'},
    {'id': 'A7', 'challenge': 'misleading tag on a genuine record', 'operator': 'revisit', 'query': 'DLC-ASYN-NEW/OBS-AN-9', 'pair': 'DLC-ASYN-REG/CAND-AR-1',
     'truth': 'CONNECTED', 'why': 'The exact product identifier links them; the capacity tag must not demote it.'},
    {'id': 'A8', 'challenge': 'genuine documented relationship', 'operator': 'complements', 'query': 'DLC-ASYN-NEW/OBS-AN-1', 'pair': 'DLC-ASYN-REG/REL-AR-1',
     'truth': 'CONNECTED', 'why': 'A documented manufacturing relationship covering 2025 concerns the recalled product.'},
    {'id': 'A9', 'challenge': 'genuine exact identifier', 'operator': 'revisit', 'query': 'DLC-ASYN-NEW/OBS-AN-1', 'pair': 'DLC-ASYN-REG/CAND-AR-1', 'truth': 'CONNECTED',
     'why': 'The recalled product is the predictor object of the registry claim.'},
    {'id': 'A10', 'challenge': 'name-only identity', 'operator': 'complements', 'query': 'DLC-ASYN-NEW/OBS-AN-6', 'pair': 'DLC-ASYN-REG/REL-AR-1',
     'truth': 'IDENTITY_UNPROVEN', 'why': 'A name in a letter is not legal identity evidence for the listed manufacturer.'},
    {'id': 'A11', 'challenge': 'ticker-only identity', 'operator': 'complements', 'query': 'DLC-ASYN-NEW/OBS-AN-7', 'pair': 'DLC-ASYN-REG/REL-AR-1',
     'truth': 'IDENTITY_UNPROVEN', 'why': 'A ticker-like string is not a legal entity identifier.'},
)
CONNECTED = ('CONNECTED', 'CONNECTED_NOT_INDEPENDENT')
SYSTEMS = ('graph_v1', 'graph_v1_1', 'structured_search')


def run(directory):
    paths = build_fixtures(directory)
    g = build(paths, catalogue_path=None, mode='synthetic', with_memory=False, requirements=Q.VOCABULARY)
    rows, shown = [], {'graph': set(), 'structured': set()}
    totals = {s: {'true_positives': 0, 'false_negatives': 0, 'false_positives': 0, 'false_positives_by_challenge': {}, 'identity_or_timing_errors': 0,
                  'warnings_correct': 0, 'warnings_on_true_connections': 0} for s in SYSTEMS}
    for task in TASKS:
        res, items = Q.graph_items(g, task)
        shown['graph'] |= {(task['operator'], task['query'], k) for k, _ in items}
        hit = dict(items).get(task['pair'])
        cls = hit['connection_class'] if hit else None
        sp = Q.structured(paths, task)
        shown['structured'] |= {(task['query'], k) for k in sp if not k.startswith('campaign:')}  # one search per query, whatever the task's operator
        presented = {'graph_v1': hit is not None, 'graph_v1_1': cls == K.ECONOMIC, 'structured_search': task['pair'] in sp}
        for system, connected in presented.items():
            t = totals[system]
            if task['truth'] in CONNECTED:t['true_positives' if connected else 'false_negatives'] += 1
            elif connected:
                t['false_positives'] += 1
                t['false_positives_by_challenge'][task['challenge']] = t['false_positives_by_challenge'].get(task['challenge'], 0) + 1
                if task['truth'] == 'IDENTITY_UNPROVEN' or task['challenge'] == 'mismatched economic period':t['identity_or_timing_errors'] += 1
        if cls == K.WARNING:totals['graph_v1_1']['warnings_correct' if task['truth'] == 'WARNING_ONLY' else 'warnings_on_true_connections'] += 1
        rows.append({'task': task['id'], 'challenge': task['challenge'], 'operator': task['operator'], 'truth': task['truth'],
                     'v1': 'connection' if presented['graph_v1'] else 'none', 'v1_1': cls or 'none',
                     'structured': 'connection' if presented['structured_search'] else 'none',
                     'abstained_or_rejected': sorted({a['code'] for a in res.get('abstentions', [])} | {x['code'] for x in res.get('rejected', [])})})
    for system in SYSTEMS:totals[system]['review_load'] = len(shown['structured'] if system == 'structured_search' else shown['graph'])
    return {'scope': 'SYNTHETIC_ADVERSARIAL_FUNCTIONAL_CHECK', 'operator_version': K.OPERATOR_VERSION, 'tasks': rows, 'totals': totals, 'digest': g.digest()}


def markdown(rep):
    t = rep['totals']
    L = ['# Graph v1.1 adversarial synthetic evaluation', '', f'> {M.BANNER}', '',
         'Generated by `python -m src.research.graph adversarial --write`; `--check` regenerates and compares it. **Not an independent or '
         'real-world benchmark:** the implementer wrote the fixtures and their truths together, before any system ran, and no operator was changed '
         'afterwards. "v1" is the R3 counting practice (every result a connection); v1.1 counts only economic connection candidates; structured search '
         'counts every hit.', '',
         '| Task | Challenge | Operator | Truth | v1 | v1.1 class | Structured search | Abstentions / rejections |', '|---|---|---|---|---|---|---|---|']
    for r in rep['tasks']:
        L.append(f"| {r['task']} | {r['challenge']} | {r['operator']} | {r['truth']} | {r['v1']} | {r['v1_1']} | {r['structured']} | "
                 f"{', '.join(r['abstained_or_rejected']) or '-'} |")
    labels = (('true_positives', 'True positives (of 4 valid connections)'), ('false_negatives', 'False negatives'),
              ('false_positives', 'False positives (non-connections presented as connections)'), ('identity_or_timing_errors', 'of which identity or timing errors'),
              ('warnings_correct', 'Warnings correctly kept as warnings (of 1)'), ('warnings_on_true_connections', 'Warnings on true connections'),
              ('review_load', 'Review load (all items shown, any class)'))
    L += ['', '| Measure | Graph v1 | Graph v1.1 | Structured search |', '|---|---:|---:|---:|']
    for k, label in labels:
        cell = lambda s: t[s][k] if not (s != 'graph_v1_1' and k.startswith('warnings')) else 'n/a'
        L.append(f'| {label} | {cell("graph_v1")} | {cell("graph_v1_1")} | {cell("structured_search")} |')
    fp = lambda s: ', '.join(f'{c} {n}' for c, n in sorted(t[s]['false_positives_by_challenge'].items())) or 'none'
    L += ['', '**False positives by challenge:**', '', *[f'- {s}: {fp(s)}' for s in SYSTEMS], '',
          '**Reading this honestly:**', '',
          '- v1.1 still presents both **trivial shared-identifier** pairs (A3, A4) as economic connection candidates: one identified regulator is enough '
          'to ground a candidate. Structured search makes the same two errors. This is the known limitation recorded in the v1.1 review; no rule was '
          'added after seeing it, because a fix now would be tuned on this set. Whether to add a role or relevance condition is an owner decision.',
          '- v1.1 removes the reused-citation and misleading-tag false positives by labelling them, and keeps the tag-plus-identifier pair (A7) as a candidate.',
          '- Period and identity traps (A5, A10, A11) are refused by all three systems; review load is not reduced by labelling.',
          f"- Projection digest `{rep['digest'][:16]}`; outputs are deterministic and read-only."]
    return '\n'.join(L) + '\n'


def generate():
    with tempfile.TemporaryDirectory() as tmp:return markdown(run(tmp))


def check():
    if not RECORD.exists() or RECORD.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_v1_1_adversarial.md differs from the regenerated evaluation; run adversarial --write')
    return {'adversarial': 'PASS', 'network': 'none', 'acquisition': 0, 'record': RECORD.relative_to(ROOT).as_posix()}
