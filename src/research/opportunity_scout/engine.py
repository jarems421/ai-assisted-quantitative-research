"""Replay rules and proposal-level routing. Outcome records never alter the frozen policy."""
from __future__ import annotations

import copy
from difflib import SequenceMatcher
import re

from src.research.spec import digest
from . import BANNER, VERSION
from . import schema as S
from .prompts import make_prompt

POLICY = 'SCOUT_FROZEN_POLICY_V001'
BATCH = S.obj({'id': S.LABEL, 'title': S.TEXT, 'fixture': S.enum(('SYNTHETIC', 'SCOUT_EXPLORATORY')),
    'base_commit': {'type': 'string', 'pattern': '^[a-f0-9]{40}$'}, 'knowledge_cutoff': S.TEXT, 'max_cards': {'type': 'integer', 'minimum': 1, 'maximum': 60},
    'max_attempts': {'type': 'integer', 'minimum': 1, 'maximum': 12},
    'max_output_tokens': {'type': 'integer', 'minimum': 100, 'maximum': 6000},
    'shortlist_slots': {'type': 'integer', 'minimum': 2, 'maximum': 6}, 'policy': {'const': POLICY},
    'memory': S.obj({'schema': {'const': 'SCOUT_MEMORY_V001'}, 'catalogue_sha256': S.HASH,
        'recorded_at': S.TEXT, 'graph_digest': S.HASH, 'investigations': {'type': 'object'}, 'same_gap': {'type': 'object'},
        'mapping_review': S.TEXT, 'ledgers_read': {'const': []}, 'creates_original_observations': {'const': False}}),
    'acquisition_authorised': {'const': False}})


class State:
    def __init__(self):
        self.batch = None
        self.seeds, self.prompts, self.attempts, self.cards, self.assessments = {}, {}, {}, {}, {}
        self.reviews, self.selections, self.novelty, self.feasibility = [], [], [], []
        self.shadows, self.critics, self.outcomes, self.efforts, self.reconsiderations, self.events = [], [], [], [], [], []

    def latest(self, idea_id):
        try: return self.cards[idea_id][-1]
        except KeyError as error: raise S.ScoutError('unknown idea id') from error

    def current_review(self, card):
        return next((r for r in reversed(self.reviews) if r['idea_id'] == card['id'] and r['version'] == card['version']), None)

    def route(self, card):
        review = self.current_review(card)
        assessment = self.assessments.get((card['id'], card['version']))
        return review['decision'] if review else assessment['recommended_route'] if assessment else card['initial_routing']


def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys): raise S.ScoutError(f'expected exactly {sorted(keys)}')


def core(idea):
    return {k: idea[k] for k in ('mechanism', 'sector', 'economic_role', 'entity_class', 'predictor', 'outcome',
                                'required_relationship_evidence', 'falsifier', 'requirement')}


def normal_text(card):
    idea = card['idea']
    text = ' '.join([idea['mechanism'][x] for x in ('trigger', 'operational_effect', 'transmission', 'consequence')]
                    + [idea['predictor']['quantity'], idea['outcome']['quantity']]).casefold()
    for entity in idea['entity_ids']: text = text.replace(entity.casefold(), '<entity>')
    return ' '.join(re.findall(r'[a-z]+', text))


def proximity(state, card):
    matches = []
    for other_id, versions in state.cards.items():
        if other_id == card['id']: continue
        other = versions[-1]
        if digest(core(card['idea'])) == digest(core(other['idea'])):
            matches.append({'idea_id': other_id, 'version': other['version'], 'kind': 'EXACT_CORE_DUPLICATE',
                            'why': 'Identical structured economic core; no entity-identity assertion.'})
            continue
        a, b = card['idea'], other['idea']
        if a['mechanism']['family'] == b['mechanism']['family']:
            similarity = SequenceMatcher(None, normal_text(card), normal_text(other)).ratio()
            matches.append({'idea_id': other_id, 'version': other['version'],
                'kind': 'POSSIBLE_MECHANISM_DUPLICATE' if similarity >= .65 or
                    (a['economic_role'] == b['economic_role'] and a['mechanism']['transformation'] == b['mechanism']['transformation']) else 'SAME_MECHANISM_FAMILY',
                'why': 'Same declared mechanism family; wording/role/transformation overlap requires review.',
                'text_similarity': round(similarity, 3), 'economic_identity_established': False})
    return sorted(matches, key=lambda x: (x['kind'], x['idea_id']))


def assess(state, card):
    check = S.structural_checks(card['idea'])
    matches = proximity(state, card)
    reasons = check['checks'][:]
    if any(m['kind'] == 'EXACT_CORE_DUPLICATE' for m in matches): reasons.append('EXACT_DUPLICATE_REVIEW')
    speculative = not card['idea']['seed_ids'] or all(link['basis'] != 'DOCUMENTED' for link in card['idea']['mechanism']['links'])
    return {'idea_id': card['id'], 'version': card['version'], 'policy': POLICY, 'checks': check,
            'proximity': matches, 'historical_proximity': historical_proximity(state, card),
            'recommended_route': 'HUMAN_REVIEW' if reasons or not speculative else 'INCUBATE',
            'reasons': reasons or ['Coherent structure with unresolved evidence; retain for review.'],
            'external_novelty': 'NOT_CHECKED', 'structural_novelty': 'NOT_REVIEWED',
            'reconsider_when': card['idea']['reconsider_when'], 'authority': 'NONE', 'speculative': speculative}


def historical_proximity(state, card):
    requirement = card['idea']['requirement']['id']
    return [{'investigation': inv['id'], 'basis': 'REQUIREMENT_MATCH', 'requirement': requirement,
             'previous_verdict': inv['verdict'], 'evidence': [f['citation'] for f in inv['findings'] if f['requirement'] == requirement],
             'economic_identity_established': False, 'novelty_established': False,
             'mapping_review': 'PENDING_HUMAN_REVIEW'}
            for inv in state.batch['memory']['investigations'].values() if requirement in inv['requirements']]


def source_restrictions(state, card):
    proposed = {r['locator'] for r in card['idea']['source_routes']}
    return [{'locator': route['locator'], 'investigation': inv['id'], 'code': 'PREVIOUS_SOURCE_STOP',
             'receipt': route['receipt'], 'scope': route['scope'], 'authorises_dispatch': False}
            for inv in state.batch['memory']['investigations'].values()
            for route in inv.get('closed_source_routes', []) if route['locator'] in proposed]


def provider_check(provider, state):
    S.validate(S.PROVIDER, provider, 'provider provenance')
    start = S.timestamp(provider['invoked_at']) if provider['invoked_at'] != S.UNKNOWN else None
    end = S.timestamp(provider['completed_at']) if provider['completed_at'] != S.UNKNOWN else None
    if start and end and start > end: raise S.ScoutError('provider timestamps reversed')
    if any(k.lower() in ('api_key', 'key', 'authorization', 'password', 'secret', 'access_token', 'refresh_token') for k in provider['parameters']):
        raise S.ScoutError('credentials must never enter model provenance')
    if state.batch['fixture'] != 'SYNTHETIC' and provider['provider'] == 'SYNTHETIC_FIXTURE':
        raise S.ScoutError('synthetic provider cannot enter an exploratory batch')


def parse_result(state, attempt, raw):
    response = S.json_loads(raw)
    prompt = state.prompts[attempt['prompt_id']]
    S.validate(prompt['response_schema'], response, 'generation')
    allowed = {sid: state.seeds[sid] for sid in prompt['context']['seeds']}
    for idea in response['ideas']:
        S.validate_idea(idea, prompt['lane'], allowed, prompt['context']['memory'])
        for link in idea['mechanism']['links']:
            for ref in link['evidence']:
                if ref['quote'] not in prompt['context']['seeds'][ref['seed']]['text']:
                    raise S.ScoutError('citation was not visible in the supplied prompt context')
    return response['ideas']


def card_from(state, attempt_id, index, recorded_at):
    attempt = state.attempts[attempt_id]
    prompt = state.prompts[attempt['prompt_id']]
    idea = parse_result(state, attempt, attempt['result']['raw_response'])[index]
    idea_id = 'IDEA-' + digest({'batch': state.batch['id'], 'attempt': attempt_id, 'index': index})[:12]
    card = {'schema': 'OPPORTUNITY_CARD_V001', 'id': idea_id, 'version': 1, 'supersedes': None,
        'revision_reason': 'Initial generation', 'revision_kind': 'ORIGINAL', 'created_at': recorded_at,
        'knowledge_cutoff': prompt['knowledge_cutoff'], 'lane': prompt['lane'], 'method': prompt['prompt_version'],
        'fixture': state.batch['fixture'], 'original_seed': idea['seed_ids'] or 'NONE_YET', 'idea': idea,
        'evidence_state': 'GENERATED_CLAIM',
        'evidence_support': [{'seed': sid, 'inherited_depth': state.seeds[sid]['depth'],
            'mapped_state': S.seed_state(state.seeds[sid]), 'seed_hash': digest(state.seeds[sid]),
            'scout_certifies': False} for sid in idea['seed_ids']],
        'provenance': {'attempt_id': attempt_id, 'response_index': index, 'prompt_sha256': prompt['sha256'],
            **attempt['result']['provider']},
        'initial_features': {'core_hash': digest(core(idea)), 'requirement': idea['requirement']['id'],
            'mechanism': idea['mechanism']['family'], 'sector': idea['sector'], 'economic_role': idea['economic_role'],
            'information_pathway': idea['information_pathway']},
        'internal_similarity_at_creation': [], 'external_novelty_at_creation': 'NOT_CHECKED',
        'research_cost': {'estimate_minutes': idea['next_step']['analyst_minutes_estimate'], 'actual_cost': S.UNKNOWN},
        'review_provenance_at_creation': [], 'initial_routing': 'HUMAN_REVIEW' if idea['seed_ids'] else 'INCUBATE',
        'revision_history': [], 'authorises': []}
    card['internal_similarity_at_creation'] = proximity(state, card) + historical_proximity(state, card)
    return card


def require_card(state, record):
    card = state.latest(record['idea_id'])
    if record['version'] != card['version']: raise S.ScoutError('record must target the current immutable card version')
    return card


def apply(s, kind, r, moment):
    """Every append and load uses these rules. No trust in a stored derived routing flag."""
    S.timestamp(moment)
    if kind == 'batch':
        if s.batch: raise S.ScoutError('batch already exists')
        S.validate(BATCH, r, 'batch'); S.timestamp(r['knowledge_cutoff'])
        if S.timestamp(r['knowledge_cutoff']) > S.timestamp(moment): raise S.ScoutError('knowledge cutoff cannot be in the future')
        s.batch = copy.deepcopy(r); return
    if s.batch is None: raise S.ScoutError('initialise a batch first')
    if kind == 'seed':
        S.validate_seed(r)
        if r['id'] in s.seeds or len(s.seeds) >= 20: raise S.ScoutError('duplicate seed or seed ceiling')
        if (s.batch['fixture'] == 'SYNTHETIC') != (r['fixture'] == 'SYNTHETIC'): raise S.ScoutError('synthetic and local evidence cannot mix')
        s.seeds[r['id']] = copy.deepcopy(r)
    elif kind == 'prompt':
        expected = make_prompt(s, r['lane'], r['count'], r['id'])
        if r != expected or r['id'] in s.prompts: raise S.ScoutError('prompt altered or id reused')
        s.prompts[r['id']] = copy.deepcopy(r)
    elif kind == 'attempt_start':
        S.validate(S.obj({'id': S.LABEL, 'prompt_id': S.LABEL, 'requested_model': S.LABEL,
            'provider': S.enum(('OPERATOR_ASSISTED', 'OLLAMA_LOCAL', 'SYNTHETIC_FIXTURE')), 'started_at': S.TEXT}), r)
        if r['prompt_id'] not in s.prompts or r['id'] in s.attempts or len(s.attempts) >= s.batch['max_attempts']:
            raise S.ScoutError('unknown prompt, duplicate attempt or generation-attempt ceiling')
        if r['provider'] == 'SYNTHETIC_FIXTURE' and s.batch['fixture'] != 'SYNTHETIC': raise S.ScoutError('fixture provider refused')
        S.timestamp(r['started_at']); s.attempts[r['id']] = copy.deepcopy(r)
    elif kind == 'attempt_result':
        S.validate(S.obj({'attempt_id': S.LABEL, 'provider': S.PROVIDER, 'raw_response': {'type': 'string', 'maxLength': 1000000},
                         'raw_import': {'type': 'string', 'maxLength': 1000000},
                         'status': S.enum(('VALID', 'INVALID', 'ERROR')), 'error': {'type': ['string', 'null'], 'maxLength': 4000}}), r)
        attempt = s.attempts.get(r['attempt_id'])
        if not attempt or 'result' in attempt: raise S.ScoutError('unknown or already completed attempt')
        provider_check(r['provider'], s)
        if r['provider']['provider'] != attempt['provider']: raise S.ScoutError('provider mismatch')
        if r['status'] == 'VALID':
            ideas = parse_result(s, attempt, r['raw_response'])
            if len(s.cards) + len(ideas) > s.batch['max_cards']: raise S.ScoutError('card budget exceeded')
            if r['error'] is not None: raise S.ScoutError('valid result cannot hide an error')
        elif not r['error']: raise S.ScoutError('failed/invalid attempts require an explicit error')
        attempt['result'] = copy.deepcopy(r)
    elif kind == 'card':
        if len(s.cards) >= s.batch['max_cards']: raise S.ScoutError('card budget exceeded')
        expected = card_from(s, r['provenance']['attempt_id'], r['provenance']['response_index'], moment)
        if r != expected or r['id'] in s.cards: raise S.ScoutError('card differs from frozen raw generation or id was reused')
        if s.attempts[r['provenance']['attempt_id']]['result']['status'] != 'VALID': raise S.ScoutError('invalid generation cannot become a card')
        s.cards[r['id']] = [copy.deepcopy(r)]
    elif kind == 'revision':
        exact(r, ('idea_id', 'from_version', 'idea', 'reason', 'actor', 'after_outcome_known'))
        old = s.latest(r['idea_id'])
        if r['from_version'] != old['version'] or not isinstance(r['reason'], str) or len(r['reason']) < 10:
            raise S.ScoutError('revision requires latest version and a concrete reason')
        S.validate(S.obj({'kind': S.enum(('HUMAN', 'ASSISTANT', 'SYNTHETIC_FIXTURE')), 'id': S.LABEL}), r['actor'])
        if (s.batch['fixture'] == 'SYNTHETIC') != (r['actor']['kind'] == 'SYNTHETIC_FIXTURE'):
            raise S.ScoutError('synthetic and actual revision provenance cannot mix')
        if not isinstance(r['after_outcome_known'], bool): raise S.ScoutError('declare outcome inspection explicitly')
        S.validate_idea(r['idea'], old['lane'], s.seeds, s.batch['memory']['investigations'])
        for before in old['idea']['source_routes']:
            if before['state'] in ('STOPPED', 'INACCESSIBLE') and any(after['locator'] == before['locator'] and after['state'] != before['state'] for after in r['idea']['source_routes']):
                raise S.ScoutError('a revision cannot reopen an earlier stopped/denied route')
        card = copy.deepcopy(old)
        card.update({'version': old['version'] + 1, 'supersedes': digest(old), 'revision_reason': r['reason'],
            'revision_kind': 'MATERIAL_REFORMULATION' if digest(core(old['idea'])) != digest(core(r['idea'])) else 'CLARIFICATION',
            'created_at': moment, 'knowledge_cutoff': moment, 'idea': copy.deepcopy(r['idea']),
            'revision_history': old['revision_history'] + [{'version': old['version'], 'sha256': digest(old),
                'reason': r['reason'], 'actor': r['actor'], 'after_outcome_known': r['after_outcome_known']}],
            'initial_routing': 'HUMAN_REVIEW', 'review_provenance_at_creation': []})
        card['evidence_support'] = [{'seed': sid, 'inherited_depth': s.seeds[sid]['depth'],
            'mapped_state': S.seed_state(s.seeds[sid]), 'seed_hash': digest(s.seeds[sid]),
            'scout_certifies': False} for sid in r['idea']['seed_ids']]
        s.cards[r['idea_id']].append(card)
    elif kind == 'assessment':
        card = require_card(s, r)
        if assess(s, card) != r: raise S.ScoutError('assessment must match frozen deterministic checks')
        s.assessments[(card['id'], card['version'])] = copy.deepcopy(r)
    elif kind == 'review':
        S.validate(S.REVIEW, r, 'human review'); card = require_card(s, r)
        if (s.batch['fixture'] == 'SYNTHETIC') != (r['reviewer']['kind'] == 'SYNTHETIC_FIXTURE'):
            raise S.ScoutError('synthetic reviewers and real human decisions remain separate')
        if r['reason'] == S.UNKNOWN or len(r['reason'].split()) < 5:
            raise S.ScoutError('routing needs a concrete recorded reason, not a placeholder')
        if (card['id'], card['version']) not in s.assessments: raise S.ScoutError('run deterministic triage before human routing')
        if r['decision'] == 'REJECT' and r['reason_type'] in ('UNRESOLVED', 'SOURCE_ACCESS'):
            raise S.ScoutError('missing evidence or source access alone cannot reject an economic mechanism')
        if r['decision'] == 'READY':
            a = assess(s, card)
            if a['checks']['checks']: raise S.ScoutError('unresolved structural warnings need correction before READY')
            stopped = {x['locator'] for x in source_restrictions(s, card)}
            if not any(x['state'] in ('DOCUMENTED_ROUTE', 'UNTESTED') and x['publisher'] != S.UNKNOWN and x['locator'] not in stopped for x in card['idea']['source_routes']):
                raise S.ScoutError('READY needs a plausible identified publisher route, not immediate original evidence')
        if r['approved_handoff'] and r['decision'] != 'READY': raise S.ScoutError('only human READY may approve a handoff proposal')
        s.reviews.append(copy.deepcopy(r))
    elif kind == 'selection':
        if r != select(s): raise S.ScoutError('selection must follow the frozen diversity policy and include all candidates')
        s.selections.append(copy.deepcopy(r))
    elif kind in ('novelty', 'feasibility', 'shadow', 'critic', 'outcome', 'effort', 'reconsideration'):
        from .reviews import apply_review_event
        apply_review_event(s, kind, r, moment)
    else: raise S.ScoutError(f'unsupported event type {kind}')


def select(state):
    cards = [v[-1] for v in state.cards.values()]
    candidates = [c for c in cards if state.route(c) in ('READY', 'INCUBATE') and not assess(state, c)['checks']['checks']]
    candidates.sort(key=lambda c: (state.route(c) != 'READY', c['created_at'], c['id']))
    chosen, used = [], set()
    # Preserve one explicitly speculative exploration niche when available.
    speculation = next((c for c in candidates if state.route(c) == 'INCUBATE' and assess(state, c)['speculative']), None)
    if speculation:
        chosen.append(speculation); used.add(speculation['idea']['mechanism']['family'])
    for c in candidates:
        family = c['idea']['mechanism']['family']
        if len(chosen) >= state.batch['shortlist_slots']: break
        if c not in chosen and family not in used and not any(
            digest(core(c['idea'])) == digest(core(x['idea'])) for x in chosen):
            chosen.append(c); used.add(family)
    chosen_ids = {c['id'] for c in chosen}
    return {'policy': POLICY, 'slots': state.batch['shortlist_slots'], 'speculative_slot_reserved': speculation is not None,
        'selected': [{'idea_id': c['id'], 'version': c['version'], 'route': state.route(c),
            'niche': [c['idea']['mechanism']['family'], 'SPECULATIVE' if assess(state, c)['speculative'] else 'SOURCE_SEEDED'],
            'reason': 'Fixed diversity niche; exploration reserved; no overall quality score.'} for c in chosen],
        'all_candidates': [{'idea_id': c['id'], 'version': c['version'], 'selected': c['id'] in chosen_ids,
            'route': state.route(c), 'reason': 'SELECTED_NICHE' if c['id'] in chosen_ids else 'NOT_SELECTED_NOT_A_FAILURE'} for c in cards],
        'authorises': []}


def handoff(state, idea_id):
    card = state.latest(idea_id); review = state.current_review(card)
    if not review or review['decision'] != 'READY' or not review['approved_handoff']:
        raise S.ScoutError('handoff needs an explicit human READY review approving this exact version')
    return {'schema': 'DISCOVERY_LAB_STARTING_PROPOSAL_V001', 'banner': BANNER, 'status': 'PROPOSAL_ONLY',
            'opportunity_card': card, 'opportunity_card_sha256': digest(card), 'human_scout_review': review,
            'seeds': [state.seeds[sid] for sid in card['idea']['seed_ids']],
            'historical_duplicates': proximity(state, card), 'source_limitations': [state.seeds[sid]['limitations'] for sid in card['idea']['seed_ids']],
            'discovery_method_proposed': {'RADAR': 'OBSERVATION_FIRST', 'FORGE': 'HYPOTHESIS_FIRST',
                'GAP': 'HYPOTHESIS_FIRST', 'PLAIN': 'HYPOTHESIS_FIRST'}[card['lane']],
            'unfilled_discovery_fields': ['campaign authority', 'source passports', 'original predictor observations',
                'documented relationships', 'dated listed-parent exposure', 'separate outcome join', 'M/H human reviews'],
            'is_discovery_candidate_record': False, 'creates_campaign': False, 'writes_ledger': False,
            'certifies_M': False, 'certifies_H': False, 'acquisition_authorised': False, 'authorises': []}
