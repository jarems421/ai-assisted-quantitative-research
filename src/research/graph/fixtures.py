"""Fully synthetic Discovery Lab campaigns for graph demonstrations, evaluation and tests.

Every ledger is written through the real Discovery Lab append rules (and therefore replayed on
load). Entities, documents and numbers are fictional; no real identifier is used.
"""
from __future__ import annotations

from pathlib import Path

from src.research.discovery import records as R
from src.research.discovery.demo import BUDGET, Clock, clk, clocks, entity, joins, passport, propositions, rec, selection, substitute, syn
from src.research.discovery.ledger import Ledger

U = R.UNKNOWN
AUTHORITY = 'docs/strategy/owner_graph_v1_2026-10-21.md (offline synthetic fixture)'
ECHO = entity('LISTED_COMPANY', 'SYN_LISTED:ECHO', 'Echo Synthetic Logistics (fictional)')
T7 = entity('FACILITY', 'SYN_FACILITY:T-7', 'Synthetic Terminal Seven')
T9 = entity('FACILITY', 'SYN_FACILITY:T-9', 'Synthetic Terminal Nine')
# Declared, self-contained requirement vocabulary for isolated evaluations (no historical catalogue involved).
REQUIREMENTS = [{'id': 'REQ_REALISED_ACTIVITY', 'label': 'Realised activity (fixture vocabulary)',
                 'definition': 'Activity that actually occurred, as distinct from permission or capacity.', 'does_not_mean': ['a ceiling']},
                {'id': 'REQ_AVAILABLE_CAPACITY', 'label': 'Available capacity (fixture vocabulary)',
                 'definition': 'Capacity available net of commitments.', 'does_not_mean': ['nameplate capacity']}]


def campaign(cid, title, method, question):
    return rec('campaign', id=cid, title=title, method=method, fixture='SYNTHETIC', question=question, authority=AUTHORITY,
               budget=dict(BUDGET), notes=['Fabricated graph fixture; no real entities or documents.'])


def obs(oid, source, statement, value, units, ent, occurred, version, retrieved, why, public=None, kind='QUANTITY', depth='VERIFIED_ORIGINAL_FIELD'):
    return rec('observation', id=oid, source_id=source, kind=kind, statement=statement, value=value, units=units,
               denominator='single identified object', entity=ent, depth=depth, evidence=[syn(f'{source}/{oid}', depth)],
               clocks=clocks(occurred, version, retrieved, public), as_of_status='VERIFIED_AS_OF' if public else 'VERIFIED_ONLY_RETROSPECTIVELY',
               why_informative=why, outcome_independent=True)


def campaign_a(path, clock):
    """Relationship-first: a documented take-or-pay dependency and a claim blocked by current throughput."""
    led = Ledger.create(path, campaign('DLC-GSYN-A', 'Synthetic take-or-pay dependency', 'RELATIONSHIP_FIRST',
                                       'Would a fall in Terminal Seven throughput create shortfall payments for Echo?'), clock)
    led.append('source', passport('SRC-GA-CONTRACTS', 'Synthetic contract register', field='minimum_annual_volume', units='Mt/year',
                                  scheme='SYN_CONTRACT', object_type='CONTRACT', publication='VERIFIED_ORIGINAL_RECORD'))
    led.append('relationship', rec(
        'relationship', id='REL-GA-1', source_entity=ECHO, target_entity=T7, type='CONTRACT_COUNTERPARTY',
        direction='Echo holds a take-or-pay throughput contract at Terminal Seven with a 2.0 Mt/year minimum.',
        scope={'asset': 'SYN_FACILITY:T-7', 'contract': 'SYN_CONTRACT:TOP-7', 'product': 'bulk throughput', 'geography': 'synthetic port'},
        period={'start': '1998-01-01', 'end': '2005-12-31'}, basis='DOCUMENTED', status='VERIFIED',
        evidence=[syn('contracts/TOP-7', 'VERIFIED_ORIGINAL_RECORD')],
        quantity_transfer={'status': 'VERIFIED', 'method': 'CONTRACTUAL_AMOUNT', 'evidence': [syn('contracts/TOP-7/minimum')],
                           'note': 'Documented 2.0 Mt/year minimum; shortfall-payment rate not recorded.'},
        limitations=['A minimum volume is not a shortfall payment; force-majeure terms are unrecorded.']))
    led.append('relationship', rec(
        'relationship', id='REL-GA-2', source_entity=ECHO, target_entity=T9, type='OPERATION', direction='Echo currently operates Terminal Nine.',
        period={'start': '2010-01-01', 'end': 'OPEN'}, basis='DOCUMENTED', status='VERIFIED', evidence=[syn('registry/T-9/operator-2010', 'VERIFIED_ORIGINAL_RECORD')],
        quantity_transfer={'status': 'NOT_APPLICABLE', 'method': 'NONE', 'evidence': [], 'note': 'Operator relationship only.'},
        limitations=['Current operation does not establish operation before 2010.']))
    led.append('observation', obs('OBS-GA-1', 'SRC-GA-CONTRACTS', 'Terminal Seven annual throughput, 1999.', 1.9, 'Mt/year', T7,
                                  '1999-12-31', '2000-01-15', '2000-02-01T00:00:00+00:00', 'Baseline throughput just below the contracted minimum.'))
    led.append('candidate', rec(
        'candidate', id='CAND-GA-1', method='RELATIONSHIP_FIRST', entry_record='REL-GA-1', population='Terminal Seven and its take-or-pay counterparty Echo.',
        predictor={'observation_ids': ['OBS-GA-1'], 'quantity': 'Terminal Seven throughput relative to the contracted minimum', 'units': 'Mt/year', 'transformation': 'NONE'},
        exposure={'company': ECHO, 'relationship_ids': ['REL-GA-1'], 'claim_basis': 'GROSS', 'allocation_required': False,
                  'gross': {'value': 30, 'units': 'USD million/year take-or-pay commitment (synthetic)'}, 'net': U,
                  'materiality': 'Synthetic: the commitment is described as material to Echo.'},
        mechanism='Throughput below the minimum obliges Echo to make shortfall payments.',
        outcome={'quantity': 'Echo reported shortfall payments', 'units': 'USD million/year', 'route': 'Issuer annual commitments note',
                 'source_id': U, 'status': 'ROUTE_ONLY', 'value': U, 'derived_from_observations': [], 'evidence': [], 'independence': 'Issuer-reported cash item.'},
        joins=joins(legal_entity='VERIFIED', period='VERIFIED'),
        information_event={'description': 'Port authority throughput release', 'decision_time': U, 'basis': U},
        public_time_route='Dated port authority releases; certification pending.', horizon='Quarterly throughput could revise payment expectations within weeks.',
        closest_substitute=substitute(False, 'Echo commentary on Terminal Seven volumes.'), increment=U,
        falsification='Show that current-period Terminal Seven throughput is not published at facility level.',
        missing_variables=['[REQ:REQ_REALISED_ACTIVITY] Terminal Seven throughput in the current period (2000)'], selection=selection(),
        propositions=propositions('Low throughput triggers shortfall payments.', U, U), recommendation={'action': 'HOLD', 'reason': 'Current throughput unobserved.'}))
    led.freeze('CAND-GA-1')
    led.append('disposition', rec('disposition', id='DSP-GA-1', candidate_id='CAND-GA-1', version=1, decision='HOLD', reason_type='OBSERVATION',
                                  reason='Current-period Terminal Seven throughput has not been observed.', scope='CAND-GA-1 v1',
                                  decided_by={'name': 'Synthetic reviewer (fixture stand-in for a human)', 'kind': 'SYNTHETIC_FIXTURE'}))
    return led


def campaign_b(path, clock):
    """Observation-first, recorded later: a certified throughput observation about the same identified facility."""
    led = Ledger.create(path, campaign('DLC-GSYN-B', 'Synthetic port throughput observation', 'OBSERVATION_FIRST',
                                       'What changed in recorded port throughput this quarter?'), clock)
    led.append('source', passport('SRC-GB-PORT', 'Synthetic port authority throughput statistics', field='quarterly_throughput', units='Mt/quarter',
                                  publication='VERIFIED_ORIGINAL_RECORD'))
    certificate = clk('2000-07-10', 'PUBLICATION_RECORD', [syn('port/bulletin/2000-07-10', 'VERIFIED_ORIGINAL_RECORD', 'PUBLICATION_RECORD')])
    led.append('observation', obs('OBS-GB-1', 'SRC-GB-PORT', 'Terminal Seven quarterly throughput fell.', {'from': 0.48, 'to': 0.21}, 'Mt/quarter', T7,
                                  '2000-06-30', '2000-07-10', '2000-08-01T00:00:00+00:00',
                                  '[MEASURES:REQ_REALISED_ACTIVITY] Realised quarterly throughput at Terminal Seven more than halved.', certificate, 'STATE_CHANGE'))
    return led


def campaign_c(path, clock):
    """Look-alikes: similar names, a name-only company, a ticker identity, a modern relationship and an unknown tag."""
    led = Ledger.create(path, campaign('DLC-GSYN-C', 'Synthetic look-alike observations', 'OBSERVATION_FIRST',
                                       'Do superficially similar records connect to earlier research?'), clock)
    led.append('source', passport('SRC-GC-NEWS', 'Synthetic trade bulletin', field='reported_throughput', units='Mt/quarter', publication='VERIFIED_ORIGINAL_RECORD'))
    t7b = entity('FACILITY', 'SYN_FACILITY:T-7B', 'Synthetic Terminal Seven B')
    led.append('observation', obs('OBS-GC-1', 'SRC-GC-NEWS', 'Terminal Seven B quarterly throughput fell.', {'from': 0.30, 'to': 0.25}, 'Mt/quarter', t7b,
                                  '2000-06-30', '2000-07-12', '2000-08-02T00:00:00+00:00', '[MEASURES:REQ_NOT_IN_VOCABULARY] Different terminal with a similar name.', kind='STATE_CHANGE'))
    led.append('observation', obs('OBS-GC-2', 'SRC-GC-NEWS', 'Echo Logistics announced a contract review.', 'review announced', 'status',
                                  entity('LISTED_COMPANY', 'NAME:Echo Logistics', 'Echo Logistics'), '2000-07-05', '2000-07-05', '2000-08-02T00:00:00+00:00',
                                  'Company named only; identity with any listed Echo is unproven.', kind='EVENT'))
    led.append('observation', obs('OBS-GC-3', 'SRC-GC-NEWS', 'Terminal Nine quarterly throughput fell in early 2000.', {'from': 0.9, 'to': 0.7}, 'Mt/quarter', T9,
                                  '2000-03-31', '2000-04-10', '2000-08-02T00:00:00+00:00', 'Precedes any documented Echo operation of Terminal Nine.', kind='STATE_CHANGE'))
    led.append('observation', obs('OBS-GC-4', 'SRC-GC-NEWS', 'Ticker ECHO reported lower shipped volumes.', 'lower', 'status',
                                  entity('LISTED_COMPANY', 'TICKER:ECHO', 'Echo Synthetic Logistics'), '2000-07-20', '2000-07-20', '2000-08-02T00:00:00+00:00',
                                  'Identified only by a ticker, which is not a permanent legal-entity identity.', kind='EVENT'))
    return led


def campaign_salmon(path, clock):
    """Hypothetical future observation for Demo A: a synthetic booking register tagged with a historical requirement."""
    led = Ledger.create(path, campaign('DLC-GSYN-S', 'Synthetic wellboat booking register', 'OBSERVATION_FIRST',
                                       'Does a booking register expose booked versus free treatment capacity?'), clock)
    led.append('source', passport('SRC-GS-BOOKINGS', 'Synthetic wellboat booking register', field='treatment_slots_free', units='slots/week',
                                  scheme='SYN_VESSEL', object_type='ASSET'))
    led.append('observation', obs('OBS-GS-1', 'SRC-GS-BOOKINGS', 'Synthetic wellboat One shows 3 of 14 weekly treatment slots free.', {'from': 14, 'to': 3}, 'slots/week',
                                  entity('ASSET', 'SYN_VESSEL:WB-1', 'Synthetic wellboat One'), '2001-03-09', '2001-03-10', '2001-04-01T00:00:00+00:00',
                                  '[MEASURES:REQ_AVAILABLE_CAPACITY] Booked versus free treatment slots for one vessel.'))
    return led


def campaign_hub(path, clock, size=30):
    """Many observations about one regulator: a high-degree hub that must not bridge trivial paths."""
    led = Ledger.create(path, campaign('DLC-GSYN-H', 'Synthetic regulator hub', 'OBSERVATION_FIRST', 'Hub stress fixture.'), clock)
    led.append('source', passport('SRC-GH-REG', 'Synthetic regulator notices', field='notice', units='count', scheme='SYN_REGULATOR', object_type='REGULATOR'))
    regulator = entity('REGULATOR', 'SYN_REGULATOR:R-1', 'Synthetic Regulator One')
    for i in range(size):
        led.append('observation', obs(f'OBS-GH-{i:02d}', 'SRC-GH-REG', f'Routine notice {i:02d} issued.', 1, 'count', regulator,
                                      '2000-05-01', '2000-05-02', '2000-08-03T00:00:00+00:00', 'Routine administrative notice.', kind='EVENT'))
    return led


def build_all(directory, clock=None):
    """Write all fixtures with one deterministic clock; returns their paths by key."""
    directory = Path(directory); clock = clock or Clock()
    paths = {k: directory / f'{k}.jsonl' for k in ('A', 'B', 'C', 'S', 'H')}
    campaign_a(paths['A'], clock); campaign_b(paths['B'], clock); campaign_c(paths['C'], clock)
    campaign_salmon(paths['S'], clock); campaign_hub(paths['H'], clock)
    return paths
