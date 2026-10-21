"""Frozen descriptive metrics and partially blinded review, with explicit missing labels."""
from __future__ import annotations

from collections import Counter
import hashlib
import hmac

from src.research.spec import canonical, digest
from . import schema as S
from . import engine as E
from .storage import ROOT

CONDITIONS = ('PLAIN', 'EVIDENCE_ONLY', 'MECHANISM_ONLY', 'HYBRID')
PROTOCOL_PATH = ROOT / 'docs/opportunity_scout/evaluation_protocol.json'


def protocol(version='V001'):
    if version not in ('V001', 'V002'): raise S.ScoutError('unknown evaluation protocol')
    path = PROTOCOL_PATH if version == 'V001' else PROTOCOL_PATH.with_name('evaluation_protocol_v002.json')
    return S.json_loads(path.read_text(encoding='utf-8'))


def report(state):
    from .accounting import generation
    cards = [v[-1] for v in state.cards.values()]
    assessments = [E.assess(state, c) for c in cards]
    exact = {c['id'] for c in cards if any(x['kind'] == 'EXACT_CORE_DUPLICATE' for x in E.proximity(state, c))}
    duplicate_excess = len(cards) - len({digest(E.core(c['idea'])) for c in cards})
    humans = [r for r in state.reviews if r['reviewer']['kind'] == 'HUMAN']
    minutes = [r['minutes'] for r in humans] + [e['minutes'] for e in state.efforts
              if e['actor']['kind'] == 'HUMAN' and e['kind'] != 'GENERATION_ATTEMPT']
    minutes += [r['human_minutes'] for r in generation(state)['attempts']]
    minutes += [r['minutes'] for r in state.feasibility + state.novelty if r['reviewer']['kind'] == 'HUMAN']
    # Separate ledgers: review.minutes is review effort; effort records are additional effort, never duplicate it.
    known_minutes = sum(m for m in minutes if m != S.UNKNOWN)
    missing_time = sum(m == S.UNKNOWN for m in minutes)
    all_reviewed = bool(cards) and all(state.current_review(c) for c in cards)
    approvals = [c for c in cards if state.current_review(c) and state.current_review(c)['approved_handoff']]
    groups = {k: Counter() for k in ('mechanism', 'sector', 'economic_role', 'lane', 'evidence_maturity', 'requirement', 'information_pathway')}
    for c, a in zip(cards, assessments):
        idea = c['idea']
        for key, value in {'mechanism': idea['mechanism']['family'], 'sector': idea['sector'], 'economic_role': idea['economic_role'],
            'lane': c['lane'], 'evidence_maturity': 'SPECULATIVE' if a['speculative'] else 'SOURCE_SEEDED',
            'requirement': idea['requirement']['id'], 'information_pathway': idea['information_pathway']}.items(): groups[key][value] += 1
    attempts = list(state.attempts.values())
    costs = [a.get('result', {}).get('provider', {}).get('usage', {}).get('cost', S.UNKNOWN) for a in attempts]
    route_states = []
    novelty_states = []
    for card in cards:
        current_routes = {r['locator']: r['state'] for r in card['idea']['source_routes']}
        current_routes.update({r['locator']: r['state'] for r in state.feasibility
                              if r['idea_id'] == card['id'] and r['version'] == card['version']})
        route_states += list(current_routes.values())
        novelty = next((r for r in reversed(state.novelty) if r['idea_id'] == card['id'] and r['version'] == card['version']), None)
        novelty_states.append(novelty['external_status'] if novelty else 'NOT_CHECKED')
    return {'schema': 'SCOUT_DESCRIPTIVE_REPORT_V001', 'fixture': state.batch['fixture'], 'policy': E.POLICY,
        'protocol_sha256': digest(protocol()), 'archive_head': state.events[-1]['hash'] if state.events else None,
        'generation': {'reserved_attempts': len(attempts), 'valid': sum(a.get('result', {}).get('status') == 'VALID' for a in attempts),
            'invalid': sum(a.get('result', {}).get('status') == 'INVALID' for a in attempts),
            'errors': sum(a.get('result', {}).get('status') == 'ERROR' for a in attempts),
            'pending': sum('result' not in a for a in attempts), 'cards': len(cards),
            'all_immutable_versions': sum(map(len, state.cards.values())),
            'known_cost': sum(c for c in costs if c != S.UNKNOWN), 'unknown_cost_entries': sum(c == S.UNKNOWN for c in costs)},
        'actual_generation_accounting': generation(state),
        'coverage': {k: dict(v) for k, v in groups.items()},
        'duplicates': {'exact_duplicate_excess': duplicate_excess, 'denominator': len(cards),
            'rate': duplicate_excess / len(cards) if cards else None, 'cards_in_exact_overlap': sorted(exact),
            'uncertain_pairs': sorted({tuple(sorted([c['id'], x['idea_id']])) for c in cards for x in E.proximity(state, c)
                                       if x['kind'] == 'POSSIBLE_MECHANISM_DUPLICATE'})},
        'structural_checks': {'warning_free': sum(not a['checks']['checks'] for a in assessments),
            'substantive_coherence': 'MISSING_INDEPENDENT_REVIEW', 'falsifiability_review': 'MISSING_INDEPENDENT_REVIEW'},
        'source_feasibility': dict(Counter(route_states)),
        'source_restrictions': [restriction for c in cards for restriction in E.source_restrictions(state, c)],
        'external_novelty': {'reviewed_entries': len(state.novelty), 'current_recorded_states': dict(Counter(novelty_states)), 'not_checked_cards': [c['id'] for c in cards
            if not any(r['idea_id'] == c['id'] and r['version'] == c['version'] and r['external_status'] != 'NOT_CHECKED' for r in state.novelty)]},
        'routing': dict(Counter(state.route(c) for c in cards)), 'shortlist': E.select(state),
        'human_work': {'review_records': len(humans), 'known_minutes': known_minutes, 'unknown_time_entries': missing_time,
            'all_cards_reviewed': all_reviewed, 'distinct_approved_handoff_proposals': len({digest(E.core(c['idea'])) for c in approvals}),
            'handoffs_per_human_hour': len({digest(E.core(c['idea'])) for c in approvals}) / (known_minutes / 60)
                if all_reviewed and not missing_time and known_minutes > 0 and humans else None},
        'learning_labels': {'uninvestigated_ids': [c['id'] for c in cards if not any(o['idea_id'] == c['id'] and o['label'] != 'NOT_INVESTIGATED' for o in state.outcomes)],
            'recorded_outcomes': dict(Counter(o['label'] for o in state.outcomes)), 'source_failure_is_economic_failure': False},
        'jev': {'shadow_records': len(state.shadows), 'human_agreement': None, 'brier_score': None,
                'reason': 'Use the separately blinded evaluation review inputs; no human labels are invented.'},
        'conditions': {name: 'NOT_RUN' for name in CONDITIONS},
        'false_rejections_of_speculation': None, 'statistical_significance': 'NOT_CLAIMED',
        'adaptive_policy': False, 'scientific_source_requests': 0, 'authorises': []}


def blind(states, salt, *, version='V001', binding=None):
    if set(states) != set(CONDITIONS): raise S.ScoutError('all four frozen comparison conditions are required')
    if not isinstance(salt, str) or len(salt) < 20: raise S.ScoutError('use a private blinding salt of at least 20 characters')
    config = protocol(version)['budget_per_condition']
    from .accounting import fairness
    accounting = fairness(states, config)
    if version == 'V002' and binding is None:
        accounting['incomplete_records'].append('V002 needs a frozen package and pre-generation runtime binding')
        accounting['comparative_eligible'] = False
    if accounting['actual_attempt_counts_equal'] is False or any(len(s.attempts) != config['generation_attempts']
            or any('result' not in a for a in s.attempts.values()) for s in states.values()):
        raise S.ScoutError('actual generation attempts/completions differ; inspect the comparison fairness report')
    fixture = {s.batch['fixture'] for s in states.values()}
    if len(fixture) != 1: raise S.ScoutError('synthetic and exploratory comparisons cannot mix')
    if len({digest(s.seeds) for s in states.values()}) != 1 or len({digest(s.batch['memory']) for s in states.values()}) != 1:
        raise S.ScoutError('comparison conditions need the same eligible seed/memory pool')
    if len({s.batch['knowledge_cutoff'] for s in states.values()}) != 1:
        raise S.ScoutError('comparison conditions need the same knowledge cutoff')
    public, assignments = [], {}
    for condition, state in states.items():
        if len(state.cards) != config['raw_cards'] or state.batch['max_cards'] != config['raw_cards'] or state.batch['max_attempts'] != config['generation_attempts'] or state.batch['max_output_tokens'] != config['max_output_tokens_per_attempt']:
            raise S.ScoutError('comparison is incomplete or generation budgets differ from the frozen protocol')
        expected_lanes = {'PLAIN': {'PLAIN': 6}, 'EVIDENCE_ONLY': {'RADAR': 6}, 'MECHANISM_ONLY': {'FORGE': 6},
                          'HYBRID': {'RADAR': 2, 'FORGE': 2, 'GAP': 2}}[condition]
        if dict(Counter(v[0]['lane'] for v in state.cards.values())) != expected_lanes:
            raise S.ScoutError('condition does not match the preregistered lane allocation')
        for card in [v[0] for v in state.cards.values()]:
            bid = 'BLIND-' + hmac.new(salt.encode(), canonical([condition, card['id']]), hashlib.sha256).hexdigest()[:16]
            idea = {k: v for k, v in card['idea'].items() if k not in ('seed_ids', 'historical_refs')}
            # Economic content may reveal the lane; generator metadata is removed, not content cues.
            row = {'blind_id': bid, 'idea': idea,
                'source_passages': [{'text': state.seeds[s]['text'][:8000], 'depth': state.seeds[s]['depth'],
                    'limitations': state.seeds[s]['limitations']} for s in card['idea']['seed_ids']]}
            public.append(row)
            assignments[bid] = {'condition': condition, 'idea_id': card['id'], 'version': 1, 'card_sha256': digest(card)}
    public.sort(key=lambda r: r['blind_id'])
    sealed = {'assignments': assignments, 'salt_sha256': S.hash_text(salt), 'public_cards_sha256': digest(public),
              'accounting': accounting, 'binding': binding}
    packet = {'schema': 'SCOUT_BLINDED_REVIEW_V001', 'protocol_sha256': digest(protocol(version)),
        'protocol_version': version, 'comparative_eligible': accounting['comparative_eligible'],
        'cards': public, 'key_sha256': digest(sealed), 'fixture': fixture.pop(),
        'blinding': 'PARTIAL_PROCEDURAL', 'reviewer_labels': [], 'missing_reviewer_judgments': len(public)}
    return packet, sealed


def evaluate_blind(packet, sealed, judgments):
    version = packet.get('protocol_version', 'V001')
    if packet.get('key_sha256') != digest(sealed) or packet.get('protocol_sha256') != digest(protocol(version)):
        raise S.ScoutError('review packet/key/protocol mismatch')
    expected = {r['blind_id'] for r in packet['cards']}
    if digest(packet['cards']) != sealed.get('public_cards_sha256') or expected != set(sealed['assignments']) or len(expected) != len(packet['cards']):
        raise S.ScoutError('blinded card content or assignments changed after freeze')
    rows, seen = [], set()
    for review in judgments:
        properties = {'blind_id': S.LABEL, 'reviewer': S.obj({'kind': {'const': 'SYNTHETIC_FIXTURE' if packet['fixture'] == 'SYNTHETIC' else 'HUMAN'}, 'id': S.LABEL}),
            'coherent': S.enum(('YES', 'NO', 'UNKNOWN')), 'falsifiable': S.enum(('YES', 'NO', 'UNKNOWN')),
            'research_worthy': S.enum(('YES', 'NO', 'UNKNOWN')), 'evidence_integrity': S.enum(('YES', 'NO', 'UNKNOWN')),
            'minutes': S.NUMBER, 'notes': S.TEXT,
            'atomic_answers': S.obj({q: S.enum(('yes', 'no', 'unsure')) for q in __import__('src.research.opportunity_scout.providers', fromlist=['QUESTIONS']).QUESTIONS})}
        if version == 'V002': properties['independent_of_generation'] = {'const': True}
        S.validate(S.obj(properties), review)
        if review['blind_id'] not in expected or review['blind_id'] in seen: raise S.ScoutError('unknown or duplicate blinded review')
        seen.add(review['blind_id']); rows.append(copy_review(review, sealed))
    review_effort = {}
    for condition in CONDITIONS:
        values = [r['minutes'] for r in rows if r['condition'] == condition]
        cap = protocol(version)['budget_per_condition'].get('human_review_minutes', 180)
        review_effort[condition] = {'reviewed': len(values), 'known_minutes': sum(v for v in values if v != S.UNKNOWN),
            'unknown_entries': sum(v == S.UNKNOWN for v in values), 'over_budget': sum(v for v in values if v != S.UNKNOWN) > cap}
    review_complete = seen == expected and all(not r['unknown_entries'] and not r['over_budget'] for r in review_effort.values())
    return {'schema': 'SCOUT_BLINDED_EVALUATION_V001', 'protocol_sha256': digest(protocol(version)),
            'review_effort': review_effort,
            'generation_fairness': sealed.get('accounting', {'comparative_eligible': False, 'status': 'NOT_RECORDED_IN_LEGACY_PACKET'}),
            'comparative_eligible': sealed.get('accounting', {}).get('comparative_eligible', False) and review_complete,
            'fixture': packet['fixture'],
            'judgments': rows, 'reviewed': len(rows), 'missing': sorted(expected - seen),
            'complete': seen == expected, 'statistical_significance': 'NOT_CLAIMED',
            'human_labels_invented': False, 'adaptive_policy': False}


def quality_audit(state):
    """Separate operational facts from substantive judgments that software cannot supply."""
    from .readiness import identifiable, feasibility_for
    cards = [v[-1] for v in state.cards.values()]
    rows = []
    for card in cards:
        novelty = next((r for r in reversed(state.novelty) if r['idea_id'] == card['id'] and r['version'] == card['version']), None)
        review = state.current_review(card)
        rows.append({'idea_id': card['id'], 'version': card['version'],
            'mechanism_label': card['idea']['mechanism']['family'],
            'structural_warnings': E.assess(state, card)['checks']['checks'],
            'substantive_economic_coherence': 'NOT_CHECKED',
            'internal_proximity': E.proximity(state, card),
            'external_novelty': novelty['external_status'] if novelty else 'NOT_CHECKED',
            'identifiable_proposed_routes': sum(identifiable(r, state.batch['fixture'] == 'SYNTHETIC') for r in card['idea']['source_routes']),
            'human_feasibility': 'RESEARCHABLE_PROPOSAL' if feasibility_for(state, card) else 'NOT_ESTABLISHED',
            'source_verification': 'NOT_CHECKED', 'route': state.route(card),
            'ready_review_version': review.get('readiness_version', 'LEGACY_V001') if review else 'NOT_CHECKED',
            'validated_economic_finding': 'NOT_ESTABLISHED'})
    return {'schema': 'SCOUT_OPERATIONAL_QUALITY_AUDIT_V001', 'fixture': state.batch['fixture'],
        'cards': rows, 'distinct_mechanism_labels': len({r['mechanism_label'] for r in rows}),
        'substantive_mechanism_diversity': 'NOT_CHECKED',
        'interpretation': [
            'Family counts are labels. Different labels can share a mechanism; one label can contain distinct mechanisms. Human comparison of transmission, economic roles and decisive measurements is missing.',
            'Internal exact/wording similarity checks do not search external literature or commercial offerings. NOT_CHECKED establishes no novelty.',
            'An identifiable URL is a proposed route. Human feasibility addresses a measurement plan; neither establishes access or original fields.',
            'Schema and chain checks establish valid structure. Economic coherence requires independent substantive judgment.',
            'READY is a human-approved research proposal with unresolved questions. It is not an economic finding, M/H review or acquisition authority.'],
        'composite_score': None, 'adaptive_policy': False, 'authorises': []}


def copy_review(review, sealed):
    return {**review, 'condition': sealed['assignments'][review['blind_id']]['condition']}


def shadow_metrics(states, sealed, judgments):
    """Agreement only where independent labels exist; confidence is not a ground truth."""
    from .providers import QUESTIONS
    by_question = {q: {'compared': 0, 'agreed': 0, 'binary_yes_brier_terms': [], 'critic_compared': 0,
                       'critic_agreed': 0, 'deterministic_compared': 0, 'deterministic_agreed': 0} for q in QUESTIONS}
    for review in judgments:
        mapped = sealed['assignments'][review['blind_id']]
        state = states[mapped['condition']]
        card = state.cards[mapped['idea_id']][mapped['version'] - 1]
        shadows = [r for r in state.shadows if r['idea_id'] == card['id'] and r['version'] == card['version']]
        if not shadows: continue
        critic = next((r for r in reversed(state.critics) if r['idea_id'] == card['id'] and r['version'] == card['version']), None)
        for q, answer in shadows[-1]['response']['answers'].items():
            label = review['atomic_answers'][q]
            metrics = by_question[q]
            metrics['compared'] += 1; metrics['agreed'] += answer['choice'] == label
            if label in ('yes', 'no'): metrics['binary_yes_brier_terms'].append((answer['probabilities']['yes'] - int(label == 'yes')) ** 2)
            if critic and 'atomic_answers' in critic:
                metrics['critic_compared'] += 1; metrics['critic_agreed'] += answer['choice'] == critic['atomic_answers'][q]
            checks = S.structural_checks(card['idea'])['checks']
            if q in ('explicit_mechanism', 'falsifiable'):
                mechanical = 'no' if (q == 'falsifiable' and any('FALSIF' in x for x in checks)) else 'yes'
                metrics['deterministic_compared'] += 1; metrics['deterministic_agreed'] += answer['choice'] == mechanical
    output = {}
    for q, m in by_question.items():
        terms = m.pop('binary_yes_brier_terms')
        output[q] = {**m, 'agreement': m['agreed'] / m['compared'] if m['compared'] else None,
                     'errors': m['compared'] - m['agreed'], 'binary_yes_brier': sum(terms) / len(terms) if terms else None,
                     'binary_label_count': len(terms)}
    return {'questions': output, 'shadow_only': True, 'calibration_established': False,
            'note': 'Binary-yes Brier is conditional on independently supplied yes/no labels; unsure labels are excluded. Mechanical agreement is structure only.'}
