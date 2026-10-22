"""Graph v1.1 discovery-quality regression: v1 behaviour, v1.1 classes and structured search on identical synthetic fixtures.

Functional behaviour only. The fixtures and ground truth were written together, before any system ran,
and they deliberately reproduce the failure pattern Graph Pilot R3 surfaced (unrelated investigations
linked by a shared missing measurement). They are therefore a diagnostic, not independent validation;
no real-world accuracy, discovery or investment claim follows from them.

"v1 behaviour" is the R3 counting practice: every operator result was treated as a connection suggestion.
v1.1 returns the same result sets (membership is unchanged), now classed and ordered; the comparison is
therefore about what is presented as an economic connection, not about different matching.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.research.discovery import records as R
from src.research.discovery.demo import Clock, entity, joins, passport, propositions, rec, selection, substitute, syn
from src.research.discovery.ledger import Ledger
from src.research.graph import baseline as B
from src.research.graph import catalogue as Cat
from src.research.graph import connections as K
from src.research.graph import model as M
from src.research.graph import operators as O
from src.research.graph.fixtures import REQUIREMENTS, build_all, campaign, obs
from src.research.graph.project import build
from src.research.graph.rules import View

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / 'docs/strategy/graph_v1_1_quality.md'
U = R.UNKNOWN
VOCABULARY = REQUIREMENTS + [{'id': 'REQ_DOCUMENTED_ALLOCATION', 'label': 'Documented allocation (fixture vocabulary)',
                              'definition': 'A documented, recall- or contract-specific amount allocated to the entity.',
                              'does_not_mean': ['a combined charge']}]
PRODUCT_1, PRODUCT_2 = entity('PRODUCT', 'SYN_PRODUCT:UDI-001', 'Synthetic applicator UDI-001'), entity('PRODUCT', 'SYN_PRODUCT:UDI-002', 'Synthetic camera UDI-002')
RECALL_25, RECALL_26 = entity('OTHER', 'SYN_RECALL:R-25', 'Synthetic recall R-25'), entity('OTHER', 'SYN_RECALL:R-26', 'Synthetic recall R-26')
DEVCO, CAMCO = entity('LISTED_COMPANY', 'SYN_LISTED:DEVCO', 'Devco Synthetic Medical (fictional)'), entity('LISTED_COMPANY', 'SYN_LISTED:CAMCO', 'Camco Synthetic Optics (fictional)')
PEN = entity('FACILITY', 'SYN_FACILITY:PEN-9', 'Synthetic treatment pen nine')
FARMCO = entity('LISTED_COMPANY', 'SYN_LISTED:FARMCO', 'Farmco Synthetic Aquaculture (fictional)')
NOTICE = syn('shared/notice-77', 'VERIFIED_ORIGINAL_RECORD')


def claim(cid, entry, observation_ids, company, mechanism, missing, relationships=()):
    return rec('candidate', id=cid, method='OBSERVATION_FIRST', entry_record=entry, population='Synthetic fixture population.',
               predictor={'observation_ids': list(observation_ids), 'quantity': 'Synthetic predictor', 'units': 'count', 'transformation': 'NONE'},
               exposure={'company': company, 'relationship_ids': list(relationships), 'claim_basis': 'GROSS', 'allocation_required': False,
                         'gross': {'value': 10, 'units': 'USD million (synthetic)'}, 'net': U, 'materiality': 'Synthetic.'},
               mechanism=mechanism, outcome={'quantity': 'Synthetic outcome', 'units': 'USD million', 'route': 'Issuer report', 'source_id': U,
                                             'status': 'ROUTE_ONLY', 'value': U, 'derived_from_observations': [], 'evidence': [], 'independence': 'Issuer-reported.'},
               joins=joins(legal_entity='VERIFIED', period='VERIFIED'), information_event={'description': 'Synthetic', 'decision_time': U, 'basis': U},
               public_time_route='Synthetic.', horizon='Synthetic.', closest_substitute=substitute(False, 'Synthetic.'), increment=U,
               falsification='Synthetic falsification route.', missing_variables=list(missing), selection=selection(),
               propositions=propositions('Synthetic effect.', U, U), recommendation={'action': 'HOLD', 'reason': 'Synthetic.'})


def relationship(rid, subject, obj, kind, direction, start, end):
    return rec('relationship', id=rid, source_entity=subject, target_entity=obj, type=kind, direction=direction,
               period={'start': start, 'end': end}, basis='DOCUMENTED', status='VERIFIED', evidence=[syn(f'registry/{rid}', 'VERIFIED_ORIGINAL_RECORD')],
               quantity_transfer={'status': 'NOT_APPLICABLE', 'method': 'NONE', 'evidence': [], 'note': 'No quantity transfer documented.'},
               limitations=['Synthetic relationship; no allocation.'])


def build_fixtures(directory, clock=None):
    """Three synthetic campaigns: an unrelated earlier investigation, a registry, and a new recall campaign (the queries)."""
    d, clock = Path(directory), clock or Clock()
    h = Ledger.create(d / 'QH.jsonl', campaign('DLC-QSYN-H', 'Synthetic earlier treatment-capacity investigation', 'OBSERVATION_FIRST', 'Is pen capacity binding?'), clock)
    h.append('source', passport('SRC-QH', 'Synthetic pen register', field='capacity', units='slots'))
    h.append('observation', obs('OBS-QH-1', 'SRC-QH', 'Pen nine capacity recorded.', 14, 'slots/week', PEN, '2001-03-09', '2001-03-10', '2001-04-01T00:00:00+00:00', 'Capacity.'))
    h.append('candidate', claim('CAND-QH-1', 'OBS-QH-1', ['OBS-QH-1'], FARMCO, 'Binding pen capacity raises treatment cost.',
                                ['[REQ:REQ_AVAILABLE_CAPACITY] free capacity net of bookings', '[REQ:REQ_DOCUMENTED_ALLOCATION] treatment cost allocated to Farmco']))
    r = Ledger.create(d / 'QR.jsonl', campaign('DLC-QSYN-R', 'Synthetic device and recall registry', 'OBSERVATION_FIRST', 'What do registries document?'), clock)
    r.append('source', passport('SRC-QR', 'Synthetic device registry', field='packaging', units='devices/box', scheme='SYN_PRODUCT', object_type='PRODUCT'))
    r.append('observation', obs('OBS-QR-1', 'SRC-QR', 'Registry: UDI-001 is packaged five devices per box.', 5, 'devices/box', PRODUCT_1, '2025-01-15', '2025-01-15', '2026-10-01T00:00:00+00:00', 'Packaging units for the product.'))
    r.append('observation', rec('observation', id='OBS-QR-2', source_id='SRC-QR', kind='EVENT', statement='Notice 77 published.', value='published', units='status',
                                denominator='single notice', entity=entity('OTHER', 'SYN_NOTICE:77', 'Synthetic notice 77'), depth='VERIFIED_ORIGINAL_RECORD',
                                evidence=[NOTICE], clocks={k: {'value': U, 'basis': U, 'evidence': []} for k in R.CLOCKS}, as_of_status='UNVERIFIED',
                                why_informative='Notice text.', outcome_independent=True))
    r.append('relationship', relationship('REL-QR-1', RECALL_26, RECALL_25, 'OTHER', 'Recall R-26 expressly supersedes recall R-25.', '2025-01-01', 'OPEN'))
    r.append('relationship', relationship('REL-QR-2', CAMCO, PRODUCT_2, 'SUPPLIER_CUSTOMER', 'Camco supplied camera UDI-002.', '2010-01-01', '2012-12-31'))
    r.append('candidate', claim('CAND-QR-1', 'OBS-QR-1', ['OBS-QR-1'], DEVCO, 'Recalled boxes, not devices, drive replacement cost.',
                                ['[REQ:REQ_REALISED_ACTIVITY] units actually replaced', '[REQ:REQ_AVAILABLE_CAPACITY] spare production capacity']))
    q = Ledger.create(d / 'QD.jsonl', campaign('DLC-QSYN-D', 'Synthetic new device-recall campaign', 'OBSERVATION_FIRST', 'What does a new recall connect to?'), clock)
    q.append('source', passport('SRC-QD', 'Synthetic recall notices', field='recall', units='status', scheme='SYN_PRODUCT', object_type='PRODUCT'))
    event = lambda oid, text, ent, why, evidence=None: rec('observation', id=oid, source_id='SRC-QD', kind='EVENT', statement=text, value='recalled', units='status',
                                                           denominator='single recall', entity=ent, depth='VERIFIED_ORIGINAL_FIELD',
                                                           evidence=[evidence or syn(f'recalls/{oid}')], clocks={'economic_occurrence': {'value': '2025-07-02', 'basis': 'DOCUMENT_DATE', 'evidence': [syn(f'dates/{oid}')]},
                                                                                       'first_public': {'value': U, 'basis': U, 'evidence': []},
                                                                                       'source_version': {'value': U, 'basis': U, 'evidence': []},
                                                                                       'retrieval': {'value': U, 'basis': U, 'evidence': []}},
                                                           as_of_status='VERIFIED_ONLY_RETROSPECTIVELY', why_informative=why, outcome_independent=True)
    q.append('observation', event('OBS-QD-1', 'Applicator UDI-001 recalled.', PRODUCT_1, '[MEASURES:REQ_AVAILABLE_CAPACITY] A recall may strain replacement capacity.'))
    q.append('observation', event('OBS-QD-2', 'Recall R-25 action recorded.', RECALL_25, 'The recall event itself.'))
    q.append('observation', event('OBS-QD-3', 'Camera UDI-002 recalled.', PRODUCT_2, 'A recall of a supplied camera.'))
    q.append('observation', event('OBS-QD-4', 'Acme Optics named in a recall.', entity('LEGAL_ENTITY', 'NAME:Acme Optics', 'Acme Optics'), 'Supplier named only.'))
    q.append('observation', event('OBS-QD-5', 'Notice 77 restated.', entity('OTHER', 'SYN_NOTICE:77-COPY', 'Restated notice'), 'Restates the registry notice.',
                                  dict(NOTICE, reused_from='DLC-QSYN-R/OBS-QR-2')))
    q.append('observation', event('OBS-QD-6', 'Notice 77 also lists UDI-001.', entity('OTHER', 'SYN_NOTICE:77-LIST', 'Notice listing'), 'Independent use of the notice.', NOTICE))
    q.append('candidate', claim('CAND-QD-1', 'OBS-QD-1', ['OBS-QD-1'], DEVCO, 'The recall changes replacement-part demand.',
                                ['[REQ:REQ_DOCUMENTED_ALLOCATION] a recall-specific charge']))
    return [d / 'QH.jsonl', d / 'QR.jsonl', d / 'QD.jsonl']


# Ground truth, written with the fixtures (before any system ran).
TASKS = (
    {'id': 'Q1', 'operator': 'revisit', 'query': 'DLC-QSYN-D/OBS-QD-1', 'pair': 'DLC-QSYN-R/CAND-QR-1', 'truth': 'CONNECTED',
     'why': 'Exact product identifier UDI-001 links the recall to the registry claim (grounded; exposure still unverified).'},
    {'id': 'Q2', 'operator': 'revisit', 'query': 'DLC-QSYN-D/OBS-QD-1', 'pair': 'DLC-QSYN-H/CAND-QH-1', 'truth': 'WARNING_ONLY',
     'why': 'A device recall and an aquaculture capacity claim share only a missing capacity measurement.'},
    {'id': 'Q3', 'operator': 'complements', 'query': 'DLC-QSYN-D/OBS-QD-2', 'pair': 'DLC-QSYN-R/REL-QR-1', 'truth': 'CONNECTED',
     'why': 'A documented supersession relationship covers the recall date.'},
    {'id': 'Q4', 'operator': 'complements', 'query': 'DLC-QSYN-D/OBS-QD-3', 'pair': 'DLC-QSYN-R/REL-QR-2', 'truth': 'NOT_CONNECTED',
     'why': 'The documented supply relationship ended in 2012; the recall is from 2025.'},
    {'id': 'Q5', 'operator': 'complements', 'query': 'DLC-QSYN-D/OBS-QD-4', 'pair': None, 'truth': 'IDENTITY_UNPROVEN',
     'why': 'The supplier is named only; no legal identity evidence.'},
    {'id': 'Q6', 'operator': 'shared', 'query': 'DLC-QSYN-D/OBS-QD-5', 'pair': 'campaign:DLC-QSYN-R', 'truth': 'NOT_CONNECTED',
     'why': 'The record restates evidence copied from the registry record: one record, not a document match.'},
    {'id': 'Q7', 'operator': 'shared', 'query': 'DLC-QSYN-D/OBS-QD-6', 'pair': 'campaign:DLC-QSYN-R', 'truth': 'CONNECTED_NOT_INDEPENDENT',
     'why': 'An independent citation of the same notice: worth investigating, never independent corroboration.'},
    {'id': 'Q8', 'operator': 'same-gap', 'query': 'REQ_DOCUMENTED_ALLOCATION', 'pair': 'DLC-QSYN-H/CAND-QH-1', 'truth': 'WARNING_ONLY',
     'why': 'Shared generic allocation blocker; no shared economic exposure.'},
)
CONNECTED = ('CONNECTED', 'CONNECTED_NOT_INDEPENDENT')


def key(node):
    return node.split(':', 1)[1].rsplit('@', 1)[0] if ':' in node and not node.startswith('campaign:') else node


def graph_items(g, task):
    v = View()
    if task['operator'] == 'revisit':res = O.revisit(g, task['query'], v); items = [(key(r['match']), r) for r in res['results']]
    elif task['operator'] == 'complements':res = O.complements(g, task['query'], v); items = [(key(r['match']), r) for r in res['results']]
    elif task['operator'] == 'shared':res = O.shared(g, task['query'], v); items = [(r['match'], r) for r in res['results']]
    else:res = O.same_gap(g, task['query'], v); items = [(key(r['claim']), r) for r in res['results']]
    return res, items


def structured(paths, task):
    if task['operator'] == 'same-gap':return None
    campaign_, oid = task['query'].split('/')
    found = B.structured_search(paths, campaign_, oid)
    pairs = {c: v['bases'] for c, v in found['claims'].items()}
    pairs.update({c['record']: c['bases'] for c in found['contexts']})
    pairs.update({f'campaign:{c["record"].split("/")[0]}': c['bases'] for c in found['contexts']})
    return pairs


def memory(directory):
    """Historical memory: the synthetic wellboat observation against the committed catalogue (V002).

    Its capacity tag matches two closed investigations; all three systems retrieve them. The difference is presentation."""
    paths = build_all(Path(directory) / 'memory', Clock())
    g = build([paths['S']], mode='synthetic', with_memory=True)
    hist = [r for r in O.revisit(g, 'DLC-GSYN-S/OBS-GS-1', View())['results'] if r['match'].startswith('history:')]
    found = B.structured_search([paths['S']], 'DLC-GSYN-S', 'OBS-GS-1', catalogue=Cat.load()[0])['catalogue']
    cited = [r for r in hist if r['connection_class'] == K.WARNING and any(c.endswith('.md') for _, c in r['warning']['lesson'])]
    return {'investigations': sorted(r['match'].split(':', 1)[1].split('/')[0] for r in hist),
            'retrieved': {'graph_v1': len(hist), 'graph_v1_1': len(hist), 'structured_search': len(found)},
            'as_connections': {'graph_v1': len(hist), 'graph_v1_1': sum(r['connection_class'] == K.ECONOMIC for r in hist), 'structured_search': len(found)},
            'warnings_with_cited_lesson': {'graph_v1': 0, 'graph_v1_1': len(cited), 'structured_search': 0}}


def run(directory):
    paths = build_fixtures(directory)
    g = build(paths, catalogue_path=None, mode='synthetic', with_memory=False, requirements=VOCABULARY)
    rows, totals = [], {s: {'grounded_found': 0, 'missed_valid': 0, 'unsupported_as_connection': 0, 'identity_or_timing_errors': 0,
                           'presented_as_connections': 0, 'warnings_retained': 0} for s in ('graph_v1', 'graph_v1_1', 'structured_search')}
    complete = []
    for task in TASKS:
        res, items = graph_items(g, task)
        hit = dict(items).get(task['pair']) if task['pair'] else None
        v11_class = hit['connection_class'] if hit else None
        v1_connection = hit is not None  # R3 practice: every result was counted as a connection suggestion
        v11_connection = v11_class == K.ECONOMIC
        sp = structured(paths, task)
        s_connection = None if sp is None else (task['pair'] in sp)
        for system, connected in (('graph_v1', v1_connection), ('graph_v1_1', v11_connection), ('structured_search', s_connection)):
            if connected is None:continue
            t = totals[system]
            if task['truth'] in CONNECTED:
                t['grounded_found' if connected else 'missed_valid'] += 1
            elif connected:
                t['unsupported_as_connection'] += 1
                if task['truth'] in ('NOT_CONNECTED', 'IDENTITY_UNPROVEN') and task['id'] in ('Q4', 'Q5'):t['identity_or_timing_errors'] += 1
            t['presented_as_connections'] += int(bool(connected))
        if task['truth'] == 'WARNING_ONLY' and hit is not None:  # v1 kept these items too, but labelled them connections
            totals['graph_v1_1']['warnings_retained'] += int(v11_class == K.WARNING)
        complete += [K.provenance_complete(r) for _, r in items if r.get('connection_class') == K.ECONOMIC]
        rows.append({'task': task['id'], 'operator': task['operator'], 'truth': task['truth'], 'v1': 'connection' if v1_connection else 'none',
                     'v1_1': v11_class or 'none', 'structured': 'n/a' if s_connection is None else ('connection' if s_connection else 'none'),
                     'abstained': [a['code'] for a in res.get('abstentions', [])], 'rejected': sorted({x['code'] for x in res.get('rejected', [])})})
    order = O.revisit(g, 'DLC-QSYN-D/OBS-QD-1', View())['results']
    return {'scope': 'SYNTHETIC_FIXTURE_FUNCTIONAL_CHECK', 'operator_version': K.OPERATOR_VERSION, 'tasks': rows, 'totals': totals,
            'provenance_complete': f'{sum(complete)}/{len(complete)}', 'grounded_ranked_first': [r['connection_class'] for r in order],
            'memory': memory(directory), 'digest': g.digest()}


def markdown(rep):
    L = ['# Graph v1.1 discovery-quality regression (synthetic)', '', f'> {M.BANNER}', '',
         'Generated by `python -m src.research.graph quality --write`; `--check` regenerates and compares it. Functional behaviour on '
         'fixtures written together with their ground truth, deliberately reproducing the R3 failure pattern: a diagnostic, not independent '
         'validation, and no real-world accuracy or investment claim. "v1" is the R3 counting practice (every operator result counted as a '
         'connection); v1.1 returns the same result sets, classed and ordered.', '',
         '| Task | Operator | Truth | v1 | v1.1 class | Structured search | Abstentions / rejections |', '|---|---|---|---|---|---|---|']
    for r in rep['tasks']:
        L.append(f"| {r['task']} | {r['operator']} | {r['truth']} | {r['v1']} | {r['v1_1']} | {r['structured']} | {', '.join(r['abstained'] + r['rejected']) or '-'} |")
    labels = {'grounded_found': 'Grounded connections presented (of 3 valid)', 'missed_valid': 'Missed valid connections',
              'unsupported_as_connection': 'Trivial or unsupported matches presented as connections', 'identity_or_timing_errors': 'Identity or timing errors',
              'presented_as_connections': 'Review burden (items presented as connections)', 'warnings_retained': 'Warnings retained as warnings (of 2)'}
    L += ['', '| Measure | Graph v1 | Graph v1.1 | Structured search |', '|---|---:|---:|---:|']
    for k, label in labels.items():
        L.append(f"| {label} | {rep['totals']['graph_v1'][k]} | {rep['totals']['graph_v1_1'][k]} | {rep['totals']['structured_search'][k]} |")
    mem, n = rep['memory'], len(rep['memory']['investigations'])
    for k, label in (('retrieved', f'Historical-memory investigations retrieved (of {n} tag-linked)'),
                     ('as_connections', 'Historical memory presented as connections'),
                     ('warnings_with_cited_lesson', 'Historical memory kept as warnings with a cited lesson')):
        L.append(f"| {label} | {mem[k]['graph_v1']} | {mem[k]['graph_v1_1']} | {mem[k]['structured_search']} |")
    L += ['', f"- Provenance: {rep['provenance_complete']} v1.1 economic candidates carry every grounded-explanation part.",
          f"- Ordering for `revisit OBS-QD-1`: {', '.join(rep['grounded_ranked_first'])} (grounded first).",
          '- Structured search has no same-gap equivalent (Q8 n/a); it reports tag-only and copied-evidence matches as plain results.',
          '- v1 kept the two warnings as results but labelled them connections; v1.1 keeps them, as warnings with their lessons.',
          f"- Historical memory: `revisit DLC-GSYN-S/OBS-GS-1` (synthetic wellboat fixture) against the committed V002 catalogue reaches "
          f"{', '.join(mem['investigations'])} by capacity tag only. Retrieval is unchanged; v1.1 presents it as reusable warnings, not discoveries.",
          f"- Projection digest `{rep['digest'][:16]}`; outputs are deterministic and read-only."]
    return '\n'.join(L) + '\n'


def generate():
    with tempfile.TemporaryDirectory() as tmp:return markdown(run(tmp))


def check():
    if not RECORD.exists() or RECORD.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_v1_1_quality.md differs from the regenerated regression; run quality --write')
    return {'quality': 'PASS', 'network': 'none', 'acquisition': 0, 'record': RECORD.relative_to(ROOT).as_posix()}
