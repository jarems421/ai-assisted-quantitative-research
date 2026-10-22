"""GRAPH_CLASSIFICATION_V1_2 holdout: fresh synthetic cases written after the rule was registered and committed.

The rule, its register and the evaluation plan were committed first (``graph_v1_2_rule_registration.md``, commit
426c211). These fixtures and their truths were written afterwards, from the registered case categories, with fresh campaign
ids, entities, identifiers and wording; nothing is reused from the v1.1 adversarial or quality fixtures. Truth comes
from the economics alone and was fixed before any system ran. The rule was not changed after this holdout ran.

Each case has its own prior campaign and query campaign, so no case can match another. Functional behaviour only: the
same implementer wrote the rule and the holdout, so this is not an independent or real-world benchmark.
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
RECORD = ROOT / 'docs/strategy/graph_v1_2_holdout.md'
RULE_COMMIT = '426c21119a25e9786f2fc4fd405bf4de914d6ab6'
U = R.UNKNOWN
ent = entity
MAKER = ent('LISTED_COMPANY', 'SYN_LISTED:HOLD-PILLMAKER', 'Pillmaker Holdout Pharma (fictional)')


def observation(oid, source, text, value, units, e, why='Holdout record.', evidence=None):
    o = obs(oid, source, text, value, units, e, '2025-06-01', '2025-06-01', '2026-10-01T00:00:00+00:00', why)
    return {**o, 'evidence': [evidence]} if evidence else o


def claim(cid, entry, ids, company, missing):
    return Q.claim(cid, entry, ids, company, 'Holdout synthetic mechanism.', missing)


# Case -> (prior records, query records, operator, query, pair, truth, why). Written before any system ran.
def cases():
    a, x, region, lei = (ent('REGULATOR', 'SYN_AUTHORITY:HOLD-BOARD-A', 'Holdout Pharmacy Board A'), ent('OTHER', 'MIC:XHLD', 'Holdout exchange XHLD'),
                         ent('GEOGRAPHY', 'SYN_REGION:HOLD-NORTHLAND', 'Holdout Northland region'),
                         ent('LEGAL_ENTITY', 'LEI:SYNHOLD0CENTRALBANK1', 'Holdout Central Bank'))
    d, e5, tab = ent('REGULATOR', 'SYN_AUTHORITY:HOLD-BOARD-D', 'Holdout Pharmacy Board D'), ent('REGULATOR', 'SYN_AUTHORITY:HOLD-BOARD-E', 'Holdout Pharmacy Board E'), \
        ent('PRODUCT', 'SYN_PRODUCT:HOLD-NDC-4411', 'Holdout tablet NDC-4411')
    authco, widget = ent('LISTED_COMPANY', 'SYN_LISTED:HOLD-AUTHORITY-HOLDINGS', 'Authority Holdings plc (fictional)'), ent('PRODUCT', 'SYN_PRODUCT:HOLD-SKU-9090', 'Holdout widget SKU-9090')
    i, j = ent('REGULATOR', 'SYN_AUTHORITY:HOLD-BOARD-I', 'Holdout Pharmacy Board I'), ent('REGULATOR', 'SYN_AUTHORITY:HOLD-BOARD-J', 'Holdout Pharmacy Board J')
    bulletin = syn('hold/board-i-bulletin-12', 'VERIFIED_ORIGINAL_RECORD')
    rel = Q.relationship('REL-H4', d, MAKER, 'REGULATOR_LICENSEE', "Board D suspended Pillmaker's manufacturing licence.", '2025-01-01', 'OPEN')
    return [
        ('H1', 'regulator only', [observation('OBS-H1P', 'SRC-H', 'Board A licence count published.', 120, 'licences', a)],
         [observation('OBS-H1Q', 'SRC-H', 'Board A fined a pharmacy chain.', 1, 'fines', a)], 'complements', 'OBS-H1Q', 'OBS-H1P', 'TRIVIAL',
         'One regulator publishing a licence count and fining a chain says nothing about a link between the two.'),
        ('H2', 'exchange only (MIC)', [observation('OBS-H2P', 'SRC-H', 'XHLD listed 40 new firms.', 40, 'listings', x),
                                     claim('CAND-H2P', 'OBS-H2P', ['OBS-H2P'], ent('LISTED_COMPANY', 'SYN_LISTED:HOLD-BROKERCO', 'Brokerco (fictional)'),
                                           ['[REQ:REQ_DOCUMENTED_ALLOCATION] brokerage revenue by venue'])],
         [observation('OBS-H2Q', 'SRC-H', 'XHLD halted trading for an hour.', 1, 'halts', x)], 'revisit', 'OBS-H2Q', 'CAND-H2P', 'TRIVIAL',
         'A trading halt on a venue does not link to a brokerage claim that merely uses the same venue.'),
        ('H3', 'geography only', [observation('OBS-H3P', 'SRC-H', 'Northland rainfall above average.', 1.2, 'ratio', region)],
         [observation('OBS-H3Q', 'SRC-H', 'Northland retail footfall fell.', -0.1, 'ratio', region)], 'shared', 'OBS-H3Q', 'campaign:DLC-HOLD-P-H3', 'TRIVIAL',
         'Two statistics about the same region are not connected by sharing it.'),
        ('H4', 'regulator with a documented relationship', [rel], [observation('OBS-H4Q', 'SRC-H', 'Board D licence actions published.', 3, 'actions', d)],
         'complements', 'OBS-H4Q', 'REL-H4', 'CONNECTED', "A documented licence suspension of Pillmaker by Board D covers the period."),
        ('H5', 'regulator and a shared product', [observation('OBS-H5P1', 'SRC-H', 'Board E inspected a plant.', 1, 'inspections', e5),
                                                 observation('OBS-H5P2', 'SRC-H', 'NDC-4411 shortage reported.', 1, 'reports', tab)],
         [observation('OBS-H5Q1', 'SRC-H', 'Board E issued a notice.', 1, 'notices', e5), observation('OBS-H5Q2', 'SRC-H', 'NDC-4411 recalled.', 1, 'recalls', tab)],
         'shared', 'DLC-HOLD-Q-H5', 'campaign:DLC-HOLD-P-H5', 'CONNECTED', 'Both campaigns concern tablet NDC-4411, a specific product.'),
        ('H6', 'institutional-sounding company name', [observation('OBS-H6P', 'SRC-H', 'Authority Holdings reported revenue.', 10, 'USD million', authco)],
         [observation('OBS-H6Q', 'SRC-H', 'Authority Holdings won a contract.', 1, 'contracts', authco)], 'complements', 'OBS-H6Q', 'OBS-H6P', 'CONNECTED',
         'The same listed company; its name is irrelevant.'),
        ('H7', 'generic institution recorded with an LEI (not in the register)', [observation('OBS-H7P', 'SRC-H', 'Central bank set its policy rate.', 4.0, 'percent', lei)],
         [observation('OBS-H7Q', 'SRC-H', 'Central bank published a speech.', 1, 'speeches', lei)], 'complements', 'OBS-H7Q', 'OBS-H7P', 'TRIVIAL',
         'A central bank touches everything; two of its outputs are not thereby connected. Expected V1_2 miss: not typed or registered as generic.'),
        ('H8', 'genuine shared product', [observation('OBS-H8P', 'SRC-H', 'SKU-9090 sold 5,000 units.', 5000, 'units', widget),
                                          claim('CAND-H8P', 'OBS-H8P', ['OBS-H8P'], ent('LISTED_COMPANY', 'SYN_LISTED:HOLD-WIDGETCO', 'Widgetco (fictional)'),
                                                ['[REQ:REQ_REALISED_ACTIVITY] SKU-9090 sell-through'])],
         [observation('OBS-H8Q', 'SRC-H', 'SKU-9090 recalled.', 1, 'recalls', widget)], 'revisit', 'OBS-H8Q', 'CAND-H8P', 'CONNECTED',
         'The recalled widget is the predictor object of the Widgetco claim.'),
        ('H9', 'one document about one regulator', [observation('OBS-H9P', 'SRC-H', 'Board I bulletin 12 lists suspensions.', 4, 'suspensions', i, evidence=bulletin)],
         [observation('OBS-H9Q', 'SRC-H', 'Board I bulletin 12 lists fines.', 2, 'fines', i, evidence=bulletin)], 'shared', 'OBS-H9Q', 'campaign:DLC-HOLD-P-H9',
         'CONNECTED_NOT_INDEPENDENT', 'Both cite bulletin 12 itself: worth reading, never independent corroboration.'),
        ('H10', 'regulator with a shared requirement tag', [observation('OBS-H10P', 'SRC-H', 'Board J staffing level.', 30, 'staff', j),
                                                            claim('CAND-H10P', 'OBS-H10P', ['OBS-H10P'], ent('LISTED_COMPANY', 'SYN_LISTED:HOLD-AUDITCO', 'Auditco (fictional)'),
                                                                  ['[REQ:REQ_AVAILABLE_CAPACITY] spare audit capacity'])],
         [observation('OBS-H10Q', 'SRC-H', 'Board J inspection backlog.', 12, 'weeks', j, why='[MEASURES:REQ_AVAILABLE_CAPACITY] backlog')], 'revisit', 'OBS-H10Q', 'CAND-H10P',
         'WARNING_ONLY', 'The same regulator plus a shared capacity requirement: a methodological warning at most.'),
    ]


CONNECTED = ('CONNECTED', 'CONNECTED_NOT_INDEPENDENT')
SYSTEMS = ('graph_v1_1', 'graph_v1_2', 'structured_search')


def build_fixtures(directory, clock=None):
    d, clock, paths = Path(directory), clock or Clock(), []
    for cid, _, prior, query, *_ in cases():
        for side, records in (('P', prior), ('Q', query)):
            led = Ledger.create(d / f'{side}-{cid}.jsonl', campaign(f'DLC-HOLD-{side}-{cid}', f'Holdout {cid} {side}', 'OBSERVATION_FIRST', 'Holdout?'), clock)
            led.append('source', passport('SRC-H', 'Holdout source', field='f', units='u'))
            for r in records:led.append({'OBS': 'observation', 'CAN': 'candidate', 'REL': 'relationship'}[r['id'][:3]], r)
            paths.append(d / f'{side}-{cid}.jsonl')
    return paths


def key(node):
    return node.split(':', 1)[1].rsplit('@', 1)[0] if ':' in node and not node.startswith('campaign:') else node


def run_graph(g, op, token):
    v = View()
    res = {'revisit': O.revisit, 'complements': O.complements, 'shared': O.shared}[op](g, token, v)
    return res, {(r['match'] if op == 'shared' else key(r['match'])): r for r in res['results']}


def structured(paths, query_campaign, oids):
    """Competent structured search for every queried observation; returns records and campaigns it presents."""
    found = {}
    for oid in oids:
        s = B.structured_search(paths, query_campaign, oid)
        for c, x in s['claims'].items():found[c] = x['bases']
        for x in s['contexts']:found[x['record']] = x['bases']; found[f"campaign:{x['record'].split('/')[0]}"] = x['bases']
    return found


def run(directory):
    paths = build_fixtures(directory)
    graphs = {'graph_v1_1': build(paths, catalogue_path=None, mode='synthetic', with_memory=False, requirements=Q.VOCABULARY),
              'graph_v1_2': K.use_rules(build(paths, catalogue_path=None, mode='synthetic', with_memory=False, requirements=Q.VOCABULARY), K.CLASSIFICATION_V1_2)}
    totals = {s: {'true_positives': 0, 'false_negatives': 0, 'false_positives': 0, 'false_positives_by_case': [], 'warnings': 0, 'review_load': 0} for s in SYSTEMS}
    rows = []
    for cid, category, prior, query, op, q, pair, truth, why in cases():
        qc, pc = f'DLC-HOLD-Q-{cid}', f'DLC-HOLD-P-{cid}'
        token = q if q.startswith('DLC-') else f'{qc}/{q}'
        target = pair if pair.startswith('campaign:') else f'{pc}/{pair}'
        row = {'case': cid, 'category': category, 'operator': op, 'truth': truth}
        for system in ('graph_v1_1', 'graph_v1_2'):
            res, items = run_graph(graphs[system], op, token)
            hit = items.get(target); cls = hit['connection_class'] if hit else None
            row[system] = cls or 'none'
            totals[system]['review_load'] += len(items)
            if cls == K.WARNING:totals[system]['warnings'] += 1
            presented = cls == K.ECONOMIC
            score(totals[system], truth, presented, cid)
            if system == 'graph_v1_2' and hit and hit.get('generic_identifier'):row['v1_2_reason'] = ', '.join(sorted({e['category'] for e in hit['generic_identifier']['entities']}))
        oids = [r['id'] for r in query if r['id'].startswith('OBS')]
        sp = structured(paths, qc, oids)
        row['structured_search'] = 'connection' if target in sp else 'none'
        totals['structured_search']['review_load'] += len([k for k in sp if not k.startswith('campaign:')])
        score(totals['structured_search'], truth, target in sp, cid)
        rows.append(row)
    return {'scope': 'SYNTHETIC_HOLDOUT_FUNCTIONAL_CHECK', 'rule_commit': RULE_COMMIT, 'cases': rows, 'totals': totals,
            'digest': graphs['graph_v1_1'].digest()}


def score(t, truth, presented, cid):
    if truth in CONNECTED:t['true_positives' if presented else 'false_negatives'] += 1
    elif presented:t['false_positives'] += 1; t['false_positives_by_case'].append(cid)


def markdown(rep):
    t = rep['totals']; generic = ('H1', 'H2', 'H3', 'H7', 'H10')
    v11 = sum(c in generic for c in t['graph_v1_1']['false_positives_by_case']); v12 = sum(c in generic for c in t['graph_v1_2']['false_positives_by_case'])
    supported = v12 < v11 and t['graph_v1_2']['false_negatives'] <= t['graph_v1_1']['false_negatives']
    L = ['# GRAPH_CLASSIFICATION_V1_2 holdout (synthetic)', '', f'> {M.BANNER}', '',
         f"Generated by `python -m src.research.graph holdout --write`; `--check` regenerates and compares it. The rule and this plan were committed first "
         f"([registration](graph_v1_2_rule_registration.md), commit `{rep['rule_commit'][:7]}`); these fresh fixtures and truths were written afterwards and "
         'the rule was not changed after it ran. **Not an independent or real-world benchmark:** the same implementer wrote both.', '',
         '| Case | Category | Operator | Truth | v1.1 class | v1.2 class | v1.2 generic reason | Structured search |', '|---|---|---|---|---|---|---|---|']
    for r in rep['cases']:
        L.append(f"| {r['case']} | {r['category']} | {r['operator']} | {r['truth']} | {r['graph_v1_1']} | {r['graph_v1_2']} | {r.get('v1_2_reason', '-')} | {r['structured_search']} |")
    L += ['', '| Measure | Graph v1.1 | Graph v1.2 | Structured search |', '|---|---:|---:|---:|']
    for k, label in (('true_positives', 'True positives (of 5 valid)'), ('false_negatives', 'False negatives'), ('false_positives', 'False positives'),
                     ('warnings', 'Warnings on the queried pair'), ('review_load', 'Review load (all items shown)')):
        cell = lambda s: 'n/a' if (k == 'warnings' and s == 'structured_search') else t[s][k]
        L.append(f'| {label} | {cell("graph_v1_1")} | {cell("graph_v1_2")} | {cell("structured_search")} |')
    L += ['', '**False positives by case:** ' + '; '.join(f"{s}: {', '.join(t[s]['false_positives_by_case']) or 'none'}" for s in SYSTEMS), '',
          f"**Registered reading:** V1_2 supports the policy on this holdout only if it presents fewer generic-only false positives than V1_1 "
          f"(V1_1 {v11}, V1_2 {v12}) and adds no false negatives (V1_1 {t['graph_v1_1']['false_negatives']}, V1_2 {t['graph_v1_2']['false_negatives']}): "
          f"**{'SUPPORTED on this holdout' if supported else 'NOT SUPPORTED on this holdout'}**.",
          '- H7 (a central bank recorded as a legal entity with an LEI, not in the register) is the declared expected miss: V1_2 cannot recognise it without a '
          'register entry, and does not.' if 'H7' in t['graph_v1_2']['false_positives_by_case'] else '- H7 was not presented as a connection by V1_2.',
          '- Labelling does not reduce review load: every item is still shown, with its class.',
          f"- Projection digest `{rep['digest'][:16]}`; outputs are deterministic and read-only."]
    return '\n'.join(L) + '\n'


def generate():
    with tempfile.TemporaryDirectory() as tmp:return markdown(run(tmp))


def check():
    if not RECORD.exists() or RECORD.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_v1_2_holdout.md differs from the regenerated holdout; run holdout --write')
    return {'holdout': 'PASS', 'network': 'none', 'acquisition': 0, 'record': RECORD.relative_to(ROOT).as_posix()}
