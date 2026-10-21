"""UNMISTAKABLY SYNTHETIC test controls. Never a model-provider fallback or real opportunity."""
from __future__ import annotations

import copy
from . import schema as S
from .providers import UNKNOWN_USAGE

MOMENT = '2026-10-21T18:00:00+00:00'
STORIES = {
    'CAPACITY_COMPETITION': ('Industrial repair services', 'INFRASTRUCTURE',
        ['A hypothetical refinery brings forward a maintenance shutdown.',
         'Its usual repair contractor must reserve more inspection shifts.',
         'Fixed shared inspection capacity could delay unrelated customer jobs.',
         'Independent customers of that contractor would bear the scheduling cost.',
         'Their equipment-return lead times would increase before the next maintenance cycle.'], 'inspection shifts'),
    'WORKING_CAPITAL': ('Returnable food packaging', 'CUSTOMER',
        ['A hypothetical deposit pool doubles the refundable charge on reusable crates.',
         'Seasonal users must finance more cash tied up in unchanged crate inventories.',
         'Deposit balances could transfer short-term financing demand to the users.',
         'Small independent packers would bear the cash-cycle change.',
         'Their separately reported short-term borrowing would rise around the inventory peak.'], 'currency per crate'),
    'COMPLEMENT_DEMAND': ('Water treatment equipment', 'COMPLEMENT',
        ['A hypothetical utility retires a treatment process that supplies recovered heat.',
         'Nearby membrane cleaning would need another heat source during maintenance.',
         'Replacement heat requirements could increase third-party cleaning-service demand.',
         'Independent mobile cleaning-service operators could receive additional orders.',
         'Their separately recorded cleaning-job volumes would rise in the affected service area.'], 'cleaning jobs'),
    'LIABILITY_TRANSFER': ('Shared cold storage', 'INSURER',
        ['A hypothetical storage cooperative changes the loss-sharing clause in a common contract.',
         'The first-loss layer moves from individual tenants to the shared pool.',
         'A changed retained-loss object could alter the pool need for excess insurance.',
         'Insurers supplying the pooled layer could face a different policy demand.',
         'Quoted coverage limits and realised pool premiums would change on the renewal date.'], 'currency per loss layer'),
    'REGULATORY_ASYMMETRY': ('Regional materials recovery', 'SUPPLIER',
        ['A hypothetical regional rule introduces customer-specific recovery credits.',
         'Facilities must record recovered inputs against named customer accounts.',
         'Mandatory account-level records might replace an otherwise unallocatable industry total.',
         'Independent recovery service suppliers could experience customer-specific order changes.',
         'Separate customer invoices would reveal whether the proposed order transfer occurred.'], 'tonnes per customer'),
    'MAINTENANCE_OBLIGATION': ('Municipal pump leasing', 'OWNER',
        ['A hypothetical municipal lessor changes the hour threshold for mandatory pump overhaul.',
         'Owners must reserve overhaul slots earlier for heavily used pumps.',
         'Contractually assigned overhaul costs could move between operators and lessors.',
         'Independent equipment lessors could bear a different maintenance cash requirement.',
         'Separately recorded lessor overhaul invoices would cluster around the new threshold.'], 'operating hours per pump'),
}


def seed():
    text = 'SYNTHETIC TEST ONLY. The fictional workshop index describes 12 inspection shifts per week. No booking allocation or customer identity is supplied.'
    return {'id': 'SEED-FIXTURE', 'fixture': 'SYNTHETIC', 'publisher': 'Fictional workshop index',
        'locator': 'synthetic://workshop/index-v1', 'version': 'synthetic-v1', 'text': text, 'sha256': S.hash_text(text),
        'depth': 'INDEXED_DESCRIPTION_ONLY', 'evidence_kind': 'INDEX_ENTRY',
        'clocks': {'economic_occurrence': S.UNKNOWN, 'source_version': S.UNKNOWN, 'retrieval': S.UNKNOWN,
                   'first_public': {'value': S.UNKNOWN, 'basis': S.UNKNOWN, 'certificate': None}},
        'limitations': ['Synthetic indexed description; no original field, booking, counterparty or publication time is verified.'],
        'access': 'UNTESTED', 'discovery_observation': None, 'approved_for_local_use': True, 'approved_for_hosted_use': False}


def idea(family='CAPACITY_COMPETITION', lane='FORGE', variant=0):
    sector, role, chain, units = STORIES[family]
    links = [{'from': S.STAGES[i], 'to': S.STAGES[i + 1], 'statement': chain[i] + ' If this premise holds, ' + chain[i + 1].lower(),
              'basis': 'UNVERIFIED', 'evidence': [], 'assumption': 'This entire economic link is hypothetical and has not been observed.'} for i in range(4)]
    return {'title': f'SYNTHETIC {sector} mechanism control {variant}', 'seed_ids': ['SEED-FIXTURE'] if lane == 'RADAR' else [],
        'historical_refs': [{'investigation': 'HIST-F01', 'requirement': 'REQ_AVAILABLE_CAPACITY',
            'changed_domain': sector, 'measurement_difference': 'Ask whether dated named customer assignments are published in this different domain; availability is untested.'}] if lane == 'GAP' else [],
        'mechanism': {'family': family, 'transformation': 'INVERT_CONSTRAINT' if lane == 'GAP' else 'CROSS_INDUSTRY_ANALOGY',
            'trigger': chain[0], 'operational_effect': chain[1], 'transmission': chain[2], 'affected_party': chain[3],
            'consequence': chain[4], 'links': links}, 'sector': sector, 'economic_role': role,
        'entity_class': 'Hypothetical independent legal entity; no listed exposure established', 'entity_ids': [],
        'predictor': {'quantity': f'Predetermined change in {units} at the named economic unit', 'units': units,
            'denominator': 'One dated customer/contract/equipment cohort, not an industry aggregate',
            'timing': 'Record the proposed trigger before inspecting its independent consequence.',
            'distinctiveness': 'Customer-specific changes would distinguish this mechanism from broad industry demand.'},
        'outcome': {'quantity': f'Separately invoiced realised consequence for {sector.lower()}', 'units': 'currency or delivered units, to be established',
            'independent_measurement': 'An independently recorded invoice or operating result, not a transformation of the predictor.',
            'timing': 'The next contract or operating cycle; public availability remains unknown.'},
        'required_relationship_evidence': ['Dated contract assigning the activity, obligation or customer share to the economic bearer.'],
        'main_uncertainty': 'Whether named customer/contract allocations and an independent consequence can be observed.',
        'requirement': {'id': 'REQ_DOCUMENTED_ALLOCATION', 'description': 'A source must identify the actual economic allocation rather than an assumed split.'},
        'falsifier': {'observation': 'Named customer records show no change in the assigned activity after the hypothetical trigger.',
            'weakens': 'The proposed transmission would lack its required operating change even if the broad event occurred.'},
        'next_step': {'question': 'Does an approved local original record state the dated customer allocation needed to distinguish this mechanism?',
            'source_hint': 'Proposed original customer/contract schedule; no dispatch is authorised.', 'analyst_minutes_estimate': S.UNKNOWN},
        'source_routes': [{'publisher': 'Fictional Workshop Records Office', 'locator': 'https://records.synthetic.invalid/contracts/allocation-register',
            'fields': ['Dated economic unit', 'Assigned quantity', 'Independent invoice'], 'state': 'UNTESTED', 'evidence': [],
            'limitation': 'No source was contacted and availability is not established.', 'authorises_dispatch': False}],
        'information_pathway': 'A dated operational disclosure, if it exists',
        'overlooked_hypothesis': {'statement': 'A conditional cross-customer allocation may require joining records that are normally reviewed separately; this is only a hypothesis.', 'status': 'HYPOTHESIS_ONLY'},
        'reconsider_when': {'requirements': ['REQ_DOCUMENTED_ALLOCATION'], 'identifiers': [],
            'observation': 'A dated original supplies the required named economic allocation and independent outcome route.'}}


def feasibility(card):
    """Simulated feasibility only; never a real human judgment."""
    route = card['idea']['source_routes'][0]
    return {'idea_id': card['id'], 'version': card['version'], 'readiness_version': 'SCOUT_READY_V002',
        'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'},
        'publisher': route['publisher'], 'locator': route['locator'], 'state': 'UNTESTED',
        'measurement_question': card['idea']['next_step']['question'],
        'assessment': 'SYNTHETIC ONLY: this fictional register would allow checking dated customer assignments against independently issued invoices, if published.',
        'conclusion': 'RESEARCHABLE_PROPOSAL', 'remaining_unknowns': ['All sources and economic premises are fictional.'],
        'fields_needed': route['fields'], 'identity_limit': 'Named counterparties would still need matching.',
        'historical_versions': 'UNKNOWN', 'independent_outcome': 'Invoice access is UNKNOWN.',
        'cheapest_check': 'Inspect the proposed allocation register only after separate authority.',
        'evidence': [], 'minutes': 'UNKNOWN', 'authorises_dispatch': False}


def provenance(model='SYNTHETIC_GENERATOR', provider='SYNTHETIC_FIXTURE'):
    return {'model': model, 'provider': provider, 'invoked_at': MOMENT, 'completed_at': MOMENT,
        'parameters': {'fixture': True}, 'seed': 0, 'usage': dict(UNKNOWN_USAGE),
        'context_declaration': 'SYNTHETIC FIXTURE ONLY; no model was invoked and no human judgment is claimed.',
        'operator': 'SYNTHETIC_FIXTURE'}


def negative_controls():
    base = idea()
    cases = []
    def add(cid, mutate, valid, lane='FORGE'):
        card = copy.deepcopy(base); mutate(card); cases.append({'id': cid, 'idea': card, 'lane': lane, 'schema_expected_valid': valid})
    add('GENERIC_THEME', lambda c: c['predictor'].update(distinctiveness='AI demand'), True)
    def paraphrase(c):
        c['title'] = 'SYNTHETIC contractor queues displace another customer'
        c['mechanism']['trigger'] = 'A fictional plant unexpectedly reserves additional workshop time.'
        c['mechanism']['operational_effect'] = 'The repair firm commits a larger fraction of a finite inspection roster.'
        c['mechanism']['transmission'] = 'With no extra shifts, work for different plant customers would be pushed back.'
        c['mechanism']['affected_party'] = 'Unrelated customers of the same fictional contractor would wait longer.'
        c['mechanism']['consequence'] = 'Recorded equipment-release delays would increase for those other customers.'
    add('PARAPHRASED_DUPLICATE', paraphrase, True)
    add('UNSUPPORTED_SUPPLIER', lambda c: c['mechanism']['links'][0].update(basis='DOCUMENTED'), False)
    add('FABRICATED_CITATION', lambda c: c['mechanism']['links'][0].update(evidence=[{'seed': 'SEED-NOT-SUPPLIED', 'quote': 'invented'}]), False)
    add('BROKEN_CHAIN', lambda c: c['mechanism']['links'][0].update(to='CONSEQUENCE'), False)
    add('UNFALSIFIABLE', lambda c: c['falsifier'].update(observation='No possible falsifier can weaken the claim.'), True)
    add('VALID_LOW_NOVELTY', lambda c: c['overlooked_hypothesis'].update(statement='A familiar capacity competition mechanism is a comparison control, not a novelty claim.'), True)
    add('COHERENT_SPECULATION', lambda c: None, True)
    clock = seed(); clock['clocks']['first_public'] = {'value': '2020-01-01T00:00:00Z', 'basis': 'DOCUMENT_DATE', 'certificate': None}
    cases.append({'id': 'IMPOSSIBLE_CLOCK', 'seed': clock, 'schema_expected_valid': False})
    return cases
