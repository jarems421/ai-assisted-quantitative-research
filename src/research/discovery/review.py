"""Mechanical Measurement Gate M / H checklist and next-evidence selection.

The checklist finds mechanical blockers: missing references, unknown units, absent independent
outcomes, unsupported joins or allocations, unidentified exposure and incomplete provenance. It never
certifies M: a requirement with no mechanical blocker still needs an explicit human judgment, which
lives in a review record. The six requirements are those of docs/strategy/measurement_gate_m.md.
"""
from __future__ import annotations

from src.research.discovery import records as R

RULES_V001 = 'DISCOVERY_LAB_RULES_V001'
# V002 adds SOURCE_REVISED_AFTER_FREEZE and GROSS_EXPOSURE_UNVERIFIED. V001 events replay without them.
RULES_V002 = 'DISCOVERY_LAB_RULES_V002'

U = R.UNKNOWN
ORDER = ('distinctive_predictor', 'meaning_and_units', 'separate_outcome', 'valid_join', 'financial_bridge', 'public_time_route')


def observations(s, c):
    return [s.latest('observation', oid) for oid in c['predictor']['observation_ids']]


def relationships(s, c):
    return [s.latest('relationship', rid) for rid in c['exposure']['relationship_ids']]


def required_acknowledgements(s, c):
    """Categories a reviewer must explicitly mark as not checked, given the claim's current evidence."""
    obs = observations(s, c); out = set()
    if not c['closest_substitute']['checked']:out.add('COMPETITOR')
    if c['outcome']['status'] != 'OBSERVED_VALUE':out.add('OUTCOME')
    if not obs or any(o['depth'] not in R.ORIGINAL for o in obs):out.add('HISTORICAL_SOURCE')
    if not obs or any(o['clocks']['first_public']['value'] == U for o in obs):out.add('PUBLIC_TIME')
    return out


def covered(period, moment):
    start = R.when(period['start'], 'period.start'); end = None if period['end'] in ('OPEN', U) else R.when(period['end'], 'period.end')
    if start is None or (end is None and period['end'] == U):return None
    return R.before(start, moment) and (end is None or R.before(moment, end))


def revised_sources(s, c):
    """Derive source versions at freeze from history without changing stored V001 freeze records."""
    sources = {}
    freeze = s.frozen(c['id'], c['version'])
    if not freeze:
        return []
    for event in s.events:
        record = event['record']
        if event['type'] == 'source':
            sources[record['id']] = record['version']
        if event['type'] == 'freeze' and record == {'candidate_id': c['id'], 'version': c['version']}:
            break
    used = {}
    for oid in c['predictor']['observation_ids'] + c['outcome']['derived_from_observations']:
        ob = s.version('observation', oid, freeze['references'][oid])
        requirement = 'distinctive_predictor' if oid in c['predictor']['observation_ids'] else 'separate_outcome'
        used.setdefault(ob['source_id'], set()).add(requirement)
    if c['outcome']['source_id'] != U:
        used.setdefault(c['outcome']['source_id'], set()).add('separate_outcome')
    return [(sid, sources[sid], s.latest('source', sid)['version'], sorted(requirements))
            for sid, requirements in sorted(used.items())
            if sources[sid] != s.latest('source', sid)['version']]


def checklist(s, cid, version=None, rules=RULES_V002):
    c = s.version('candidate', cid, version)
    if c is None:raise ValueError(f'unknown candidate {cid} v{version}')
    b = {k: [] for k in R.M_REQUIREMENTS}; gaps, h = [], []
    obs, rels = observations(s, c), relationships(s, c); freeze = s.frozen(cid, c['version'])
    p, o, x = c['predictor'], c['outcome'], c['exposure']

    if not obs:b['distinctive_predictor'].append('NO_PREDICTOR_OBSERVATION')
    for ob in obs:
        if ob['depth'] != 'VERIFIED_ORIGINAL_FIELD':b['distinctive_predictor'].append(f"PREDICTOR_NOT_ORIGINAL_FIELD:{ob['id']}={ob['depth']}")
        if ob['value'] == U:b['distinctive_predictor'].append(f"PREDICTOR_VALUE_UNKNOWN:{ob['id']}")
        access = s.latest('source', ob['source_id'])['access']['status']
        if access in ('BLOCKED', 'PAID', 'AUTHENTICATED'):b['distinctive_predictor'].append(f"SOURCE_ACCESS_{access}:{ob['source_id']}")
        if ob['units'] == U:b['meaning_and_units'].append(f"UNKNOWN_UNITS:{ob['id']}")
        elif p['transformation'] == 'NONE' and p['units'] != U and R.norm(ob['units']) != R.norm(p['units']):
            b['meaning_and_units'].append(f"UNITS_INCONSISTENT:{ob['id']}")
        if ob['denominator'] == U:gaps.append(f"DENOMINATOR_UNKNOWN:{ob['id']}")
        if ob['outcome_independent'] is False:b['separate_outcome'].append(f"PREDICTOR_NOT_INDEPENDENT_OF_OUTCOME:{ob['id']}")
        elif ob['outcome_independent'] == U:gaps.append(f"OUTCOME_INDEPENDENCE_UNKNOWN:{ob['id']}")
        occurred = R.when(ob['clocks']['economic_occurrence']['value'], 'clock')
        if occurred is None:b['valid_join'].append(f"PREDICTOR_ECONOMIC_TIME_UNKNOWN:{ob['id']}")
        for rel in rels:
            if occurred is None:continue
            inside = covered(rel['period'], occurred)
            if inside is None:b['valid_join'].append(f"RELATIONSHIP_PERIOD_UNKNOWN:{rel['id']}")
            elif not inside:b['valid_join'].append(f"RELATIONSHIP_PERIOD_UNCOVERED:{rel['id']}@{ob['id']}")
        if ob['depth'] in R.ORIGINAL and ob['clocks']['retrieval']['value'] == U:b['public_time_route'].append(f"RETRIEVAL_TIME_UNKNOWN:{ob['id']}")
        if ob['clocks']['first_public']['value'] == U:gaps.append(f"EXACT_PUBLIC_TIME_UNRESOLVED:{ob['id']} (Level B question, not an M blocker)")
    if p['units'] == U:b['meaning_and_units'].append('UNKNOWN_UNITS:predictor')

    if o['status'] == 'UNVERIFIED':b['separate_outcome'].append('NO_INDEPENDENT_OUTCOME')
    if o['status'] == 'ROUTE_ONLY':b['separate_outcome'].append('OUTCOME_ROUTE_ONLY_PROVISIONAL')
    if o['units'] == U:b['separate_outcome'].append('OUTCOME_UNITS_UNKNOWN')
    if o['route'] == U:b['separate_outcome'].append('OUTCOME_ROUTE_UNKNOWN')

    for dim, j in c['joins'].items():
        if j['status'] == 'UNVERIFIED':b['valid_join'].append(f'UNSUPPORTED_JOIN:{dim}')
    for rel in rels:
        if rel['status'] != 'VERIFIED':b['valid_join'].append(f"RELATIONSHIP_{rel['status']}:{rel['id']}")
        if x['allocation_required'] and rel['quantity_transfer']['status'] != 'VERIFIED':
            b['valid_join'].append(f"ALLOCATION_UNVERIFIED:{rel['id']}={rel['quantity_transfer']['method']}")
    if x['allocation_required'] and not rels:b['valid_join'].append('ALLOCATION_UNVERIFIED:no-relationship')
    if freeze:
        for rid, v in freeze['references'].items():
            current = (s.latest('observation', rid) or s.latest('relationship', rid))['version']
            if current != v:
                req = 'distinctive_predictor' if rid.startswith('OBS-') else 'valid_join'
                b[req].append(f'REFERENCE_REVISED_AFTER_FREEZE:{rid} v{v}->v{current}')
        for sid, previous, current, requirements in (revised_sources(s, c) if rules != RULES_V001 else []):
            for req in requirements:
                b[req].append(f'SOURCE_REVISED_AFTER_FREEZE:{sid} v{previous}->v{current}')

    company = x['company']
    if R.named_only(company):b['financial_bridge'].append('COMPANY_NOT_IDENTIFIED')
    if company['type'] != 'LISTED_COMPANY':b['financial_bridge'].append('EXPOSURE_NOT_A_LISTED_COMPANY')
    if not any(r['status'] == 'VERIFIED' and company['id'] in (r['source_entity']['id'], r['target_entity']['id']) for r in rels):
        b['financial_bridge'].append('EXPOSURE_NOT_LINKED_BY_VERIFIED_RELATIONSHIP')
    if x['claim_basis'] != 'NOT_MONETARY' and x['gross'] == U and x['net'] == U:b['financial_bridge'].append('EXPOSURE_UNQUANTIFIED')
    elif x['claim_basis'] == 'GROSS' and x['gross'] == U and rules != RULES_V001:b['financial_bridge'].append('GROSS_EXPOSURE_UNVERIFIED')
    if x['claim_basis'] == 'NET' and x['net'] == U:b['financial_bridge'].append('NET_EXPOSURE_UNVERIFIED')
    if x['materiality'] == U:b['financial_bridge'].append('MATERIALITY_UNSTATED')
    if c['public_time_route'] == U:b['public_time_route'].append('NO_PUBLIC_TIME_ROUTE')
    for e in [company, *[ob['entity'] for ob in obs]]:
        if e['id'] in s.name_variants:gaps.append(f"ENTITY_NAME_VARIANTS:{e['id']}={sorted(s.name_variants[e['id']])}")

    event = c['information_event']
    if event['description'] == U:h.append('NO_INFORMATION_EVENT')
    if event['decision_time'] == U:h.append('DECISION_TIME_UNKNOWN')
    if c['horizon'] == U:h.append('NO_5_20_SESSION_RATIONALE')
    if c['increment'] == U:h.append('NO_INCREMENT_STATED')
    if not c['closest_substitute']['checked']:h.append('COMPETITOR_NOT_CHECKED')
    decision = R.when(event['decision_time'], 'decision_time')
    for ob in obs:
        public = R.when(ob['clocks']['first_public']['value'], 'first_public')
        if public is None:h.append(f"PREDICTOR_PUBLIC_TIME_UNKNOWN:{ob['id']}")
        elif decision is not None and not R.before(public, decision):h.append(f"PREDICTOR_PUBLIC_AFTER_DECISION:{ob['id']}")

    d = s.derived[('candidate', cid, c['version'])]
    if not freeze:gaps.append('NOT_FROZEN')
    if d['claim_class'] == 'REFORMULATION':gaps.append('MATERIAL_REFORMULATION: report separately from original claims')
    if d['post_outcome']:gaps.append('POST_OUTCOME_CLAIM: outcome seen before this version; not untouched evidence')
    sel = c['selection']
    if sel['famous_case'] or sel['purposive_control'] or sel['outcome_inspected_before_freeze'] is not False or s.fixture != 'LIVE':
        gaps.append('NOT_ELIGIBLE_FOR_UNTOUCHED_EVALUATION')

    human = [r for r in s.reviews if r['candidate_id'] == cid and r['version'] == c['version'] and R.human_equivalent(r['reviewer']['kind'], s.fixture)]
    m = [r for r in human if r['kind'] == 'M']; hr = [r for r in human if r['kind'] == 'H']
    requirements = {k: {'mechanical': 'BLOCKED' if b[k] else 'NO_MECHANICAL_BLOCKER_HUMAN_JUDGMENT_REQUIRED', 'blockers': b[k],
                        'human_judgment': m[-1]['judgments'][k]['judgment'] if m else 'NOT_REVIEWED'} for k in R.M_REQUIREMENTS}
    return {'candidate': cid, 'version': c['version'], 'frozen': bool(freeze), 'software_certifies_M': False,
            'requirements': requirements, 'gaps': gaps, 'h_gaps': h,
            'h_human_judgment': hr[-1]['judgments']['judgment'] if hr else 'NOT_REVIEWED',
            'acknowledge_not_checked': sorted(required_acknowledgements(s, c)), 'next': next_step(c, requirements, h, m)}


def next_step(c, requirements, h, m_reviews):
    """The first unresolved requirement in Measurement Gate M order; never several parallel hunts."""
    for k in ORDER:
        if requirements[k]['blockers']:
            return {'requirement': k, 'blocker': requirements[k]['blockers'][0], 'cheapest_falsification': c['falsification'],
                    'instruction': 'Resolve this before spending effort on later requirements. Stop if the cheapest original '
                                   'observation cannot change the disposition within existing authority.'}
    if not m_reviews:return {'requirement': None, 'blocker': 'HUMAN_M_REVIEW_REQUIRED', 'cheapest_falsification': c['falsification'],
                             'instruction': 'No mechanical blocker remains; a human must judge all six M requirements.'}
    if h:return {'requirement': 'H', 'blocker': h[0], 'cheapest_falsification': c['falsification'],
                 'instruction': 'Measurement and short-horizon relevance are separate; M does not imply H.'}
    return {'requirement': None, 'blocker': None, 'cheapest_falsification': c['falsification'],
            'instruction': 'No mechanical next step; any further work needs a human disposition and separate authority.'}


def source_next(passport):
    """Qualitative next-evidence rung for a Source Passport. Unusual or large sources earn nothing here."""
    original = lambda claim: claim['depth'] in R.ORIGINAL
    if passport['access']['status'] in ('BLOCKED', 'PAID', 'AUTHENTICATED'):
        return 'STOP_ROUTE', f"Access is {passport['access']['status']}; record the limit, do not bypass or purchase."
    if not any(original(q) for q in passport['quantities']):
        return 'OBTAIN_ONE_ORIGINAL_RECORD', 'Obtain one original record showing the economic field itself, not a schema or index description.'
    if any(original(q) and q['units'] == U for q in passport['quantities']):
        return 'ESTABLISH_UNITS', 'Establish units and denominator of the verified field before interpreting it.'
    if not any(original(i) for i in passport['identifiers']):
        return 'ESTABLISH_STABLE_IDENTIFIER', 'Show a stable entity/asset/contract identifier in an original record.'
    if not original(passport['history']):
        return 'EVIDENCE_HISTORICAL_COVERAGE', 'Show one dated historical record; current data cannot stand in for past versions.'
    if not original(passport['revision_policy']):
        return 'ESTABLISH_REVISION_POLICY', 'Establish whether old versions survive revision before relying on history.'
    if not original(passport['publication_clock']):
        return 'IDENTIFY_PUBLICATION_ROUTE', 'Identify how first-public timing could be evidenced (needed by Level B, not by M).'
    if not passport['exposure_links']:
        return 'IDENTIFY_LISTED_EXPOSURE', 'Name a plausible listed-company link to examine; this is not yet a verified relationship.'
    return 'READY_FOR_OBSERVATIONS', 'Source qualified for recording observations. This is a discovery aid, not an evidence level.'
