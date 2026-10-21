"""Independent findings, shadow judgments, reversible human routing and later outcome references."""
from __future__ import annotations

import copy

from src.research.spec import digest
from . import schema as S

ACTOR = S.obj({'kind': S.enum(('HUMAN', 'ASSISTANT', 'SYNTHETIC_FIXTURE')), 'id': S.LABEL})
TARGET = {'idea_id': S.LABEL, 'version': {'type': 'integer', 'minimum': 1}}
NOVELTY = S.obj({**TARGET, 'reviewer': ACTOR, 'independent_of_generator': {'const': True},
    'external_status': S.enum(('NOT_CHECKED', 'PRIOR_ART_FOUND', 'NO_SUBSTANTIVE_MATCH_IN_DECLARED_SEARCH', 'UNCERTAIN')),
    'structural_status': S.enum(('NOT_CHECKED', 'KNOWN_MECHANISM', 'UNUSUAL_COMBINATION', 'UNCERTAIN')),
    'search_queries': S.array(S.TEXT, 20), 'evidence': S.array(S.REF, 20), 'limits': S.array(S.TEXT, 20, 1),
    'reviewed_at': S.TEXT, 'private_investor_use': {'const': 'UNKNOWN'}, 'minutes': S.NUMBER})
FEASIBILITY = S.obj({**TARGET, 'reviewer': ACTOR, 'locator': S.TEXT, 'state': S.enum(S.ROUTE_STATES),
    'fields_needed': S.array(S.TEXT, 12, 1), 'identity_limit': S.TEXT, 'historical_versions': S.TEXT,
    'independent_outcome': S.TEXT, 'cheapest_check': S.TEXT, 'evidence': S.array(S.REF, 10),
    'minutes': S.NUMBER, 'authorises_dispatch': {'const': False}})
from .readiness import VERSION as READY_VERSION
FEASIBILITY_V002 = S.obj({**FEASIBILITY['properties'], 'readiness_version': {'const': READY_VERSION},
    'publisher': S.LABEL, 'measurement_question': S.TEXT, 'assessment': S.TEXT,
    'conclusion': S.enum(('RESEARCHABLE_PROPOSAL', 'UNRESOLVED', 'NOT_FEASIBLE')),
    'remaining_unknowns': S.array(S.TEXT, 12, 1)})
GENERATION_EFFORT = S.obj({'attempt_id': S.LABEL, 'actor': ACTOR, 'human_minutes': S.NUMBER,
    'wall_seconds': S.NUMBER, 'context_id': S.LABEL, 'fresh_context': S.enum(('YES', 'NO', 'UNKNOWN')),
    'invocation_status': S.enum(('INVOKED', 'NOT_INVOKED', 'UNKNOWN')),
    'no_prior_generated_cards': S.enum(('YES', 'NO', 'UNKNOWN')), 'description': S.TEXT})
GENERATION_EFFORT['properties'].update({'correction_of': S.HASH, 'correction_reason': S.TEXT})
CRITIC = S.obj({**TARGET, 'model': S.LABEL, 'independent_of_generator': {'const': True},
    'unsupported_steps': S.array(S.TEXT, 10), 'competing_explanations': S.array(S.TEXT, 10, 1),
    'generic_interpretations': S.array(S.TEXT, 10), 'economic_significance_gaps': S.array(S.TEXT, 10),
    'observation_requirements': S.array(S.TEXT, 10), 'identity_or_timing_errors': S.array(S.TEXT, 10),
    'decisive_falsifier': S.TEXT, 'uncertainty': S.TEXT, 'reviewed_at': S.TEXT, 'usage': S.USAGE,
    'certifies_evidence': {'const': False}, 'routing_authority': {'const': False},
    'atomic_answers': S.obj({q: S.enum(('yes', 'no', 'unsure')) for q in
        ('explicit_mechanism', 'evidence_supported', 'falsifiable', 'next_check_addresses_gap', 'certainty_exceeds_evidence')})})
OUTCOME = S.obj({**TARGET, 'label': S.enum(('NOT_INVESTIGATED', 'SOURCE_BLOCKED', 'MECHANISM_FALSIFIED', 'MEASURABLE',
    'M_PASSED', 'H_PLAUSIBLE', 'H_NOT_ESTABLISHED', 'STATISTICAL_RESULT', 'REFORMULATED')),
    'reference': S.obj({'locator': S.TEXT, 'sha256': S.HASH, 'quote': S.TEXT}), 'reviewer': ACTOR,
    'recorded_elsewhere_at': S.TEXT, 'reason': S.TEXT, 'outcome_was_known_before_revision': {'type': 'boolean'},
    'human_decision_reference_only': {'const': True}, 'scout_certifies': {'const': False}})
EFFORT = S.obj({'kind': S.enum(('GENERATION', 'REVIEW', 'NOVELTY', 'FEASIBILITY', 'SELECTION', 'HANDOFF', 'OTHER')),
    'actor': ACTOR, 'minutes': S.NUMBER, 'cost': S.NUMBER, 'currency': S.enum(('USD', S.UNKNOWN)), 'description': S.TEXT})
RECONSIDER = S.obj({'seed_id': S.LABEL, 'requirements': S.array(S.LABEL, 10), 'identifiers': S.array(S.LABEL, 10),
    'leads': S.array(S.obj({**TARGET, 'basis': S.enum(('EXACT_IDENTIFIER', 'EXPLICIT_REQUIREMENT_MATCH')),
        'matches': S.array(S.LABEL, 10, 1), 'suggestion_only': {'const': True}, 'previous_status_stands': {'const': True}}), 60),
    'authorises': {'const': []}})


def actor_check(state, actor):
    if (state.batch['fixture'] == 'SYNTHETIC') != (actor['kind'] == 'SYNTHETIC_FIXTURE'):
        raise S.ScoutError('synthetic and actual review provenance cannot mix')


def reconsider(state, seed_id, requirements, identifiers):
    if seed_id not in state.seeds: raise S.ScoutError('reconsideration needs an imported seed')
    if any(not r.startswith('REQ_') for r in requirements): raise S.ScoutError('requirements must be exact requirement IDs, not keywords')
    if any(':' not in x or x.startswith(('NAME:', 'TICKER:')) for x in identifiers):
        raise S.ScoutError('name/ticker similarity cannot trigger reconsideration')
    leads = []
    for versions in state.cards.values():
        card = versions[-1]
        if state.route(card) != 'INCUBATE': continue
        trigger = card['idea']['reconsider_when']
        ids = sorted(set(trigger['identifiers']) & set(identifiers))
        reqs = sorted(set(trigger['requirements']) & set(requirements))
        for matches, basis in ((ids, 'EXACT_IDENTIFIER'), (reqs, 'EXPLICIT_REQUIREMENT_MATCH')):
            if matches: leads.append({'idea_id': card['id'], 'version': card['version'], 'basis': basis, 'matches': matches,
                                      'suggestion_only': True, 'previous_status_stands': True})
    return {'seed_id': seed_id, 'requirements': requirements, 'identifiers': identifiers, 'leads': leads, 'authorises': []}


def apply_review_event(state, kind, r, moment):
    from .engine import require_card
    schemas = {'novelty': NOVELTY, 'feasibility': FEASIBILITY_V002 if 'readiness_version' in r else FEASIBILITY,
               'critic': CRITIC, 'outcome': OUTCOME, 'generation_effort': GENERATION_EFFORT,
               'effort': EFFORT, 'reconsideration': RECONSIDER}
    if kind == 'shadow':
        from .providers import validate_shadow
        validate_shadow(state, r)
        state.shadows.append(copy.deepcopy(r)); return
    S.validate(schemas[kind], r, kind)
    if kind == 'reconsideration':
        if r != reconsider(state, r['seed_id'], r['requirements'], r['identifiers']):
            raise S.ScoutError('reconsideration leads must match exact identifiers/explicit requirements')
        state.reconsiderations.append(copy.deepcopy(r)); return
    if kind == 'effort':
        actor_check(state, r['actor']); state.efforts.append(copy.deepcopy(r)); return
    if kind == 'generation_effort':
        actor_check(state, r['actor'])
        previous = next((x for x in reversed(state.efforts) if x.get('attempt_id') == r['attempt_id']), None)
        if r['attempt_id'] not in state.attempts:
            raise S.ScoutError('generation effort needs an existing attempt')
        if previous:
            if r.get('correction_of') != digest(previous) or len(r.get('correction_reason', '').split()) < 5:
                raise S.ScoutError('effort correction needs the previous record hash and a concrete reason')
        elif 'correction_of' in r or 'correction_reason' in r:
            raise S.ScoutError('effort correction has no preceding record')
        state.efforts.append({'kind': 'GENERATION_ATTEMPT', **copy.deepcopy(r)}); return
    card = require_card(state, r)
    if kind == 'critic':
        if r['model'] == card['provenance']['model']: raise S.ScoutError('generator self-review cannot become independent criticism')
        S.timestamp(r['reviewed_at']); state.critics.append(copy.deepcopy(r)); return
    actor_check(state, r['reviewer'])
    if kind == 'novelty':
        if r['reviewer']['id'] == card['provenance']['model']: raise S.ScoutError('generator cannot certify its own novelty')
        S.timestamp(r['reviewed_at'])
        if r['external_status'] not in ('NOT_CHECKED', 'UNCERTAIN') and (not r['evidence'] or not r['search_queries']):
            raise S.ScoutError('external novelty needs actual independently recorded search findings and citations')
        for ref in r['evidence']: S.check_ref(ref, state.seeds)
        state.novelty.append(copy.deepcopy(r))
    elif kind == 'feasibility':
        if 'readiness_version' in r:
            if not any(x['locator'] == r['locator'] and x['publisher'] == r['publisher'] for x in card['idea']['source_routes']):
                raise S.ScoutError('feasibility must identify a proposed route on this card version')
            if r['measurement_question'] != card['idea']['next_step']['question']:
                raise S.ScoutError('feasibility must address the exact decisive next-step question')
            if r['conclusion'] == 'RESEARCHABLE_PROPOSAL' and (len(r['assessment'].split()) < 10 or r['assessment'] == S.UNKNOWN):
                raise S.ScoutError('researchability needs a substantive human explanation; unknowns may remain')
        from .engine import source_restrictions
        if any(x['locator'] == r['locator'] for x in source_restrictions(state, card)) and r['state'] != 'STOPPED':
            raise S.ScoutError('historical source closure stands; Scout cannot reopen it')
        previous = [x for x in card['idea']['source_routes'] if x['locator'] == r['locator']]
        previous += [x for x in state.feasibility if x['idea_id'] == card['id'] and x['locator'] == r['locator']]
        if any(x['state'] in ('STOPPED', 'INACCESSIBLE') and x['state'] != r['state'] for x in previous):
            raise S.ScoutError('stopped or denied source cannot be reopened by a scout finding')
        if r['state'] == 'DOCUMENTED_ROUTE' and not r['evidence']: raise S.ScoutError('a documented route needs a cited passage')
        for ref in r['evidence']: S.check_ref(ref, state.seeds)
        state.feasibility.append(copy.deepcopy(r))
    elif kind == 'outcome':
        S.timestamp(r['recorded_elsewhere_at'])
        if r['reviewer']['kind'] not in ('HUMAN', 'SYNTHETIC_FIXTURE'): raise S.ScoutError('later scientific outcomes require human-recorded references')
        if r['label'] == 'MECHANISM_FALSIFIED' and 'source' in r['reason'].lower() and 'blocked' in r['reason'].lower():
            raise S.ScoutError('source-blocked is a separate label, not mechanism falsification')
        state.outcomes.append(copy.deepcopy(r))
