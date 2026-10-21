"""Strict public contracts and inexpensive consistency checks, never an M/H evaluator."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re

from jsonschema import Draft202012Validator
from src.research.discovery import records as R
from src.research.spec import canonical, digest

UNKNOWN = 'UNKNOWN'
LANES = ('RADAR', 'FORGE', 'GAP', 'PLAIN')
MECHANISMS = ('SUBSTITUTION', 'CAPACITY_COMPETITION', 'SHARED_SUPPLIER', 'CONTRACTUAL_PASS_THROUGH',
              'WORKING_CAPITAL', 'LIABILITY_TRANSFER', 'REGULATORY_ASYMMETRY', 'COMPLEMENT_DEMAND',
              'MAINTENANCE_OBLIGATION', 'FINANCING_CONSTRAINT', 'OPERATIONAL_BOTTLENECK',
              'INDIRECT_BENEFICIARY', 'THIRD_ORDER')
TRANSFORMS = ('INVERT_CONSTRAINT', 'CROSS_INDUSTRY_ANALOGY', 'SECOND_ORDER', 'THIRD_ORDER',
              'CHANGE_ECONOMIC_ROLE', 'TRACE_OBLIGATION', 'COUNTERFACTUAL')
ROLES = ('SUPPLIER', 'CUSTOMER', 'OPERATOR', 'INSURER', 'LENDER', 'OWNER', 'COMPLEMENT', 'INFRASTRUCTURE', 'OTHER')
STAGES = ('TRIGGER', 'OPERATIONS', 'TRANSMISSION', 'PARTY', 'CONSEQUENCE')
ROUTE_STATES = ('DOCUMENTED_ROUTE', 'UNTESTED', 'INACCESSIBLE', 'UNKNOWN', 'STOPPED')
ROUTES = ('HUMAN_REVIEW', 'READY', 'INCUBATE', 'REJECT')
REQS = ('REQ_AVAILABLE_CAPACITY', 'REQ_REALISED_ACTIVITY', 'REQ_DOCUMENTED_ALLOCATION',
        'REQ_ENTITY_COHORT_JOIN', 'REQ_HISTORICAL_SCHEDULE_OR_VERSION', 'REQ_RETAINED_NET_ECONOMICS',
        'REQ_QUALIFIED_COMMERCIAL_EXPOSURE', 'REQ_UNREDACTED_CONTRACT_AMOUNT', 'REQ_OTHER')
HASH = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 4000}
LABEL = {'type': 'string', 'minLength': 1, 'maxLength': 200}
NUMBER = {'anyOf': [{'type': 'number', 'minimum': 0}, {'const': UNKNOWN}]}


class ScoutError(ValueError):
    pass


def obj(properties, required=None):
    return {'type': 'object', 'properties': properties, 'required': list(properties) if required is None else required,
            'additionalProperties': False}


def array(items, maximum=30, minimum=0):
    return {'type': 'array', 'items': items, 'minItems': minimum, 'maxItems': maximum}


def enum(values):
    return {'enum': list(values)}


REF = obj({'seed': LABEL, 'quote': TEXT})
LINK = obj({'from': enum(STAGES), 'to': enum(STAGES), 'statement': TEXT,
            'basis': enum(('DOCUMENTED', 'INFERRED', 'UNVERIFIED')), 'evidence': array(REF, 5), 'assumption': TEXT})
ROUTE = obj({'publisher': LABEL, 'locator': TEXT, 'fields': array(TEXT, 10, 1), 'state': enum(ROUTE_STATES),
             'evidence': array(REF, 5), 'limitation': TEXT, 'authorises_dispatch': {'const': False}})
IDEA = obj({
    'title': LABEL, 'seed_ids': array(LABEL, 10), 'historical_refs': array(obj({
        'investigation': LABEL, 'requirement': LABEL, 'changed_domain': TEXT, 'measurement_difference': TEXT}), 5),
    'mechanism': obj({'family': enum(MECHANISMS), 'transformation': enum(TRANSFORMS),
                      'trigger': TEXT, 'operational_effect': TEXT, 'transmission': TEXT,
                      'affected_party': TEXT, 'consequence': TEXT, 'links': array(LINK, 4, 4)}),
    'sector': LABEL, 'economic_role': enum(ROLES), 'entity_class': LABEL, 'entity_ids': array(LABEL, 10),
    'predictor': obj({'quantity': TEXT, 'units': LABEL, 'denominator': TEXT, 'timing': TEXT, 'distinctiveness': TEXT}),
    'outcome': obj({'quantity': TEXT, 'units': LABEL, 'independent_measurement': TEXT, 'timing': TEXT}),
    'required_relationship_evidence': array(TEXT, 10, 1), 'main_uncertainty': TEXT,
    'requirement': obj({'id': LABEL, 'description': TEXT}),
    'falsifier': obj({'observation': TEXT, 'weakens': TEXT}),
    'next_step': obj({'question': TEXT, 'source_hint': TEXT, 'analyst_minutes_estimate': NUMBER}),
    'source_routes': array(ROUTE, 8), 'information_pathway': LABEL,
    'overlooked_hypothesis': obj({'statement': TEXT, 'status': {'const': 'HYPOTHESIS_ONLY'}}),
    'reconsider_when': obj({'requirements': array(LABEL, 10), 'identifiers': array(LABEL, 10), 'observation': TEXT}),
})
GENERATION = obj({'ideas': array(IDEA, 12, 1)})
PUBLICATION = obj({'text': TEXT, 'sha256': HASH, 'quote': TEXT, 'kind': {'const': 'PUBLICATION_RECORD'}})
CLOCKS = obj({'economic_occurrence': TEXT, 'source_version': TEXT, 'retrieval': TEXT,
              'first_public': obj({'value': TEXT, 'basis': enum(('PUBLICATION_RECORD', UNKNOWN)),
                                   'certificate': {'anyOf': [PUBLICATION, {'type': 'null'}]}})})
SEED = obj({'id': {'type': 'string', 'pattern': '^SEED-[A-Za-z0-9_.-]+$'},
            'fixture': enum(('SYNTHETIC', 'APPROVED_LOCAL')), 'publisher': LABEL, 'locator': TEXT,
            'version': LABEL, 'text': {'type': 'string', 'minLength': 1, 'maxLength': 100000}, 'sha256': HASH,
            'depth': enum(R.DEPTHS), 'evidence_kind': enum(R.EVIDENCE_KINDS), 'clocks': CLOCKS,
            'limitations': array(TEXT, 20, 1), 'access': enum(ROUTE_STATES),
            'discovery_observation': {'type': ['object', 'null']},
            'approved_for_local_use': {'const': True}, 'approved_for_hosted_use': {'const': False}})
USAGE = obj({'input_tokens': NUMBER, 'output_tokens': NUMBER, 'cost': NUMBER, 'currency': enum(('USD', UNKNOWN))})
PROVIDER = obj({'model': LABEL, 'provider': enum(('OPERATOR_ASSISTED', 'OLLAMA_LOCAL', 'SYNTHETIC_FIXTURE')),
                'invoked_at': TEXT, 'completed_at': TEXT, 'parameters': {'type': 'object', 'maxProperties': 15},
                'seed': {'anyOf': [{'type': 'integer'}, {'const': UNKNOWN}]}, 'usage': USAGE,
                'context_declaration': TEXT, 'operator': LABEL})
REVIEW = obj({'idea_id': LABEL, 'version': {'type': 'integer', 'minimum': 1},
              'decision': enum(ROUTES), 'reason_type': enum(('STRUCTURAL', 'DUPLICATE', 'UNFALSIFIABLE',
                  'CONTRADICTED', 'UNWORKABLE', 'UNRESOLVED', 'SOURCE_ACCESS', 'RESEARCHABLE')),
              'reason': TEXT, 'uncertainties': array(TEXT, 15, 1),
              'reviewer': obj({'kind': enum(('HUMAN', 'SYNTHETIC_FIXTURE')), 'id': LABEL}),
              'minutes': NUMBER, 'approved_handoff': {'type': 'boolean'}, 'reconsider_when': TEXT,
              'authorises_acquisition': {'const': False}})


def validate(schema, value, where='record'):
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        e = errors[0]
        raise ScoutError(f'{where} /{"/".join(map(str, e.path))}: {e.message}')
    canonical(value)  # Reject non-finite numbers even if accepted by Python's JSON decoder.
    return value


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def timestamp(value):
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if t.tzinfo is None: raise ValueError()
        return t.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError) as error:
        raise ScoutError('timestamps require an explicit timezone') from error


def hash_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def json_loads(text):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out: raise ScoutError(f'duplicate JSON key: {k}')
            out[k] = v
        return out
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda s: (_ for _ in ()).throw(ScoutError('non-finite JSON number')))
    except (ValueError, RecursionError) as error:
        raise ScoutError(f'invalid JSON: {error}') from error


def validate_seed(seed):
    validate(SEED, seed, 'seed')
    if hash_text(seed['text']) != seed['sha256']: raise ScoutError('seed content hash mismatch')
    first = seed['clocks']['first_public']
    if first['value'] != UNKNOWN:
        timestamp(first['value'])
        cert = first['certificate']
        if first['basis'] != 'PUBLICATION_RECORD' or cert is None:
            raise ScoutError('first-public time requires an original publication record; no inferred dates')
        if hash_text(cert['text']) != cert['sha256'] or cert['quote'] not in cert['text'] or first['value'] not in cert['quote']:
            raise ScoutError('invalid publication-record certificate')
    elif first['basis'] != UNKNOWN or first['certificate'] is not None:
        raise ScoutError('unknown first-public clock must remain explicitly unknown')
    for key in ('economic_occurrence', 'source_version', 'retrieval'):
        if seed['clocks'][key] != UNKNOWN: timestamp(seed['clocks'][key])
    observation = seed['discovery_observation']
    if observation is not None:
        R.validate('observation', observation, 'SYNTHETIC' if seed['fixture'] == 'SYNTHETIC' else 'RETROSPECTIVE_INSPECTED')
        if observation['depth'] != seed['depth'] or observation['statement'] not in seed['text']:
            raise ScoutError('seed must preserve the supplied Discovery Lab observation depth and statement')
        if seed['depth'] in R.ORIGINAL and not any(e['sha256'] == seed['sha256'] and e['locator'] == seed['locator'] and
                e['passage'] in seed['text'] for e in observation['evidence']):
            raise ScoutError('inherited original evidence must bind this exact supplied text artifact, locator and passage')
    elif seed['depth'] in R.ORIGINAL:
        raise ScoutError('original-depth inheritance requires an existing validated Discovery Lab observation; metadata is not field verification')
    return seed


def check_ref(ref, seeds):
    if ref['seed'] not in seeds or ref['quote'] not in seeds[ref['seed']]['text']:
        raise ScoutError('fabricated or inexact citation: seed and exact source passage are required')


def validate_idea(idea, lane, seeds, memory):
    validate(IDEA, idea, 'idea')
    if idea['requirement']['id'] not in REQS or any(r not in REQS for r in idea['reconsider_when']['requirements']):
        raise ScoutError('use a canonical requirement ID or the explicit REQ_OTHER category')
    if lane == 'FORGE' and (idea['seed_ids'] or idea['historical_refs']):
        raise ScoutError('Forge is independent and must not claim unseen seed or memory inputs')
    if lane == 'RADAR' and not idea['seed_ids']: raise ScoutError('Evidence Radar requires an actual approved seed')
    if lane == 'GAP' and not idea['historical_refs']: raise ScoutError('Gap Explorer requires a cited historical obstacle')
    if len(set(idea['seed_ids'])) != len(idea['seed_ids']) or any(s not in seeds for s in idea['seed_ids']):
        raise ScoutError('unknown or duplicate seed reference')
    for i, link in enumerate(idea['mechanism']['links']):
        if (link['from'], link['to']) != (STAGES[i], STAGES[i + 1]): raise ScoutError('causal-chain stage order is invalid')
        if link['basis'] == 'DOCUMENTED' and not link['evidence']: raise ScoutError('documented causal link requires cited support')
        for ref in link['evidence']:
            check_ref(ref, seeds)
            if ref['seed'] not in idea['seed_ids']: raise ScoutError('causal evidence must be among the declared seed inputs')
            if link['basis'] == 'DOCUMENTED' and (seeds[ref['seed']]['depth'] not in R.ORIGINAL or seed_state(seeds[ref['seed']]) == 'CONTRADICTED' or link['statement'] != ref['quote']):
                raise ScoutError('a documented economic link must inherit an original-depth exact assertion, not metadata or a new inference')
    for ref in idea['historical_refs']:
        match = memory.get(ref['investigation'])
        if not match or ref['requirement'] not in match['requirements']: raise ScoutError('unknown historical investigation/requirement mapping')
        if ref['changed_domain'].strip().lower() in match['title'].lower(): raise ScoutError('constraint inversion must state a different domain')
    for route in idea['source_routes']:
        if route['state'] == 'DOCUMENTED_ROUTE' and not route['evidence']: raise ScoutError('documented route requires a source passage')
        for ref in route['evidence']: check_ref(ref, seeds)
        for seed in seeds.values():
            if seed['locator'] == route['locator'] and seed['access'] in ('STOPPED', 'INACCESSIBLE') and route['state'] != seed['access']:
                raise ScoutError('a recorded source stop or access denial cannot be silently reopened')
    return idea


DEPTH_MAPPING = {
    'VERIFIED_ORIGINAL_FIELD': 'ORIGINAL_FIELD_VERIFIED', 'VERIFIED_ORIGINAL_RECORD': 'ORIGINAL_RECORD_VERIFIED',
    'INDEXED_DESCRIPTION_ONLY': 'SOURCE_DESCRIBED', 'SCHEMA_ONLY': 'SOURCE_DESCRIBED',
    'RETROSPECTIVE_DESCRIPTION': 'SOURCE_DESCRIBED', 'UNVERIFIED': 'UNVERIFIED', 'ACCESS_BLOCKED': 'UNVERIFIED',
}


def seed_state(seed):
    if seed.get('discovery_observation') and seed['discovery_observation']['as_of_status'] == 'CONTRADICTED':
        return 'CONTRADICTED'
    return DEPTH_MAPPING[seed['depth']]


def structural_checks(idea):
    """Warnings, not scientific judgments. Coherence needs independent human review."""
    checks = []
    for key, text in [('FALSIFIER', idea['falsifier']['observation']), ('NEXT_QUESTION', idea['next_step']['question']),
                      ('DISTINCTIVE_PREDICTOR', idea['predictor']['distinctiveness'])]:
        if text == UNKNOWN or len(text.split()) < 5: checks.append(f'{key}_NEEDS_REVIEW')
    if re.search(r'\b(everything|always wins|cannot be falsified|no possible falsifier)\b', idea['falsifier']['observation'], re.I):
        checks.append('UNFALSIFIABLE_LANGUAGE')
    if idea['predictor']['quantity'].casefold() == idea['outcome']['quantity'].casefold(): checks.append('PREDICTOR_REPEATED_AS_OUTCOME')
    if R.UNSUPPORTED_NOVELTY.search(idea['overlooked_hypothesis']['statement']): checks.append('UNSUPPORTED_INFORMATION_ADVANTAGE_LANGUAGE')
    return {'checks': checks, 'substantive_coherence': 'NOT_REVIEWED', 'economic_truth': 'NOT_EVALUATED',
            'software_certifies_M': False, 'software_certifies_H': False}
