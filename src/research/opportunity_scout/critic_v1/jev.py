"""Jev beside the critics: a descriptive, shadow-only comparison of the frozen five atomic answers with critic judgments.

Reuses the unchanged instrument (``providers.QUESTIONS``), the archived shadow records and the PR #21 provenance status.
Jev never enters the policy or the review queue. Its confidence is reported as a distribution, never as calibrated
accuracy. The five candidate uses are measured as counterfactual counts, so a later study can decide between them."""
from __future__ import annotations

from collections import Counter

from src.research.spec import digest
from .. import schema as S
from ..post_generation import review as SR
from ..providers import JEV_MODEL, QUESTIONS
from . import packages as P, policy as Q, rubric as K

JEV_COMPARISON_V = 'SCOUT_CRITIC_JEV_COMPARISON_V001'
CHOICES = ('yes', 'no', 'unsure')
# Frozen Jev question -> (critic dimension, owning critic, relation). INVERTED: Jev "yes" means a problem.
MAPPING = {'explicit_mechanism': ('mechanism_coherence', 'SCIENTIFIC', 'APPROXIMATE'),
           'evidence_supported': ('evidence_integrity', 'SCIENTIFIC', 'APPROXIMATE'),
           'falsifiable': ('falsifiability', 'SCIENTIFIC', 'DIRECT'),
           'next_check_addresses_gap': ('research_feasibility', 'ECONOMIC', 'APPROXIMATE'),
           'certainty_exceeds_evidence': ('uncertainty', 'SCIENTIFIC', 'INVERTED')}
INTERPRETATION = [
    'Shadow only: Jev changed no recommendation, queue position, route or archive record.',
    'Agreement with an AI critic is AI agreement, not accuracy. Only independent human anchors measure accuracy.',
    'Jev confidence is a model output; it is reported as a distribution and is never treated as a calibrated probability.',
    'Question-to-dimension mappings marked APPROXIMATE ask related but not identical questions.',
    'Use-case counts are counterfactual descriptions on a small, non-random set; choosing a Jev role needs the prospective design in the calibration protocol.']


def critic_choice(question, assessment):
    j = assessment['judgment']
    if j in ('UNKNOWN', 'NOT_APPLICABLE'):return 'unsure'
    good = j == 'PASS'
    return ('no' if good else 'yes') if MAPPING[question][2] == 'INVERTED' else ('yes' if good else 'no')


def bins(values):
    return {f'{i / 10:.1f}-{(i + 1) / 10:.1f}': sum(min(int(v * 10), 9) == i for v in values) for i in range(10)}


def compare(ws, states, provenance=None, recommendations=None):
    """``states``: {archive name: State} named as in the workspace; ``provenance``: {archive: [PR #21 provenance records]}."""
    manifest, (chosen, _) = ws.manifest(), P.usable(ws)
    recommendations = recommendations or Q.evaluate_workspace(ws)
    rows, missing = [], {'subjects_without_jev': [], 'subjects_without_critics': [], 'archives_not_supplied': set(), 'card_changed': []}
    for key, entry in sorted(manifest['subjects'].items()):
        if entry['variant_of'] or entry['input_sha256'] is None:continue
        state = states.get(entry['archive'])
        if state is None:missing['archives_not_supplied'].add(entry['archive']); continue
        versions = state.cards.get(entry['idea_id'], [])
        if len(versions) < entry['version'] or digest(versions[entry['version'] - 1]) != entry['card_sha256']:
            missing['card_changed'].append(key); continue
        shadows = [r for r in state.shadows if r['idea_id'] == entry['idea_id'] and r['version'] == entry['version']]
        if not shadows:missing['subjects_without_jev'].append(key); continue
        critics = chosen.get(key, {})
        if not all(c in critics for c in K.FIRST_PASS):missing['subjects_without_critics'].append(key)
        shadow = shadows[0]  # earliest, as in PR #21: a later re-run cannot replace an inconvenient answer
        rows.append({'key': key, 'shadow': shadow, 'critics': critics, 'layer_a': entry['layer_a'], 'recommendation': recommendations[key],
                     'provenance': SR.provenance_status(state, shadow, (provenance or {}).get(entry['archive'], []))})
    questions = {}
    for q, (dimension, owner, relation) in MAPPING.items():
        confusion = {j: {c: 0 for c in CHOICES} for j in CHOICES}
        agree_conf, disagree_conf = [], []
        for row in rows:
            if owner not in row['critics']:continue
            answer = row['shadow']['response']['answers'][q]
            c = critic_choice(q, K.assessments(row['critics'][owner]['output'])[dimension])
            confusion[answer['choice']][c] += 1
            (agree_conf if answer['choice'] == c else disagree_conf).append(answer['confidence'])
        pairs = sum(sum(v.values()) for v in confusion.values())
        decisive = sum(confusion[a][b] for a in ('yes', 'no') for b in ('yes', 'no'))
        problem = SR.PROBLEM[q]
        questions[q] = {'critic_dimension': dimension, 'critic': owner, 'relation': relation, 'pairs': pairs,
            'agreement': sum(confusion[c][c] for c in CHOICES) / pairs if pairs else None,
            'decisive_agreement': (confusion['yes']['yes'] + confusion['no']['no']) / decisive if decisive else None,
            'confusion_jev_by_critic': confusion,
            'jev_abstained': sum(confusion['unsure'].values()), 'critic_abstained': sum(confusion[j]['unsure'] for j in CHOICES),
            'opposite_decisions': confusion['yes']['no'] + confusion['no']['yes'],
            'screening': {'jev_flags_problem': sum(confusion[problem].values()), 'critic_flags_problem': sum(confusion[j][problem] for j in CHOICES),
                          'both': confusion[problem][problem], 'jev_only': sum(confusion[problem][c] for c in CHOICES if c != problem),
                          'critic_only': sum(confusion[j][problem] for j in CHOICES if j != problem)},
            'jev_confidence_when_agreeing': bins(agree_conf), 'jev_confidence_when_disagreeing': bins(disagree_conf)}
    def jev_flags(row):return any(row['shadow']['response']['answers'][q]['choice'] in (SR.PROBLEM[q], 'unsure') for q in QUESTIONS)
    def jev_disagrees(row):
        return any(owner in row['critics'] and row['shadow']['response']['answers'][q]['choice'] != critic_choice(q, K.assessments(row['critics'][owner]['output'])[d])
                   for q, (d, owner, _) in MAPPING.items())
    flagged = Counter(row['recommendation']['classification'] for row in rows if jev_flags(row))
    overstated = [row for row in rows if row['shadow']['response']['answers']['certainty_exceeds_evidence']['choice'] == 'yes']
    uses = {
        'early_atomic_screener': {q: questions[q]['screening'] for q in QUESTIONS},
        'disagreement_detector': {
            'subjects_with_critic_disagreement': sum(bool(r['recommendation']['disagreements']) for r in rows),
            'of_which_jev_also_disagrees_with_a_critic': sum(bool(r['recommendation']['disagreements']) and jev_disagrees(r) for r in rows),
            'subjects_without_critic_disagreement_where_jev_disagrees': sum(not r['recommendation']['disagreements'] and jev_disagrees(r) for r in rows)},
        'evidence_overstatement_detector': {
            'jev_says_certainty_exceeds_evidence': len(overstated),
            'of_which_layer_a_language_flag': sum(any(f['code'] in ('CERTAINTY_LANGUAGE', 'UNSUPPORTED_NOVELTY_OR_CERTAINTY_LANGUAGE', 'UNSUPPORTED_INFORMATION_ADVANTAGE_LANGUAGE',
                                                                     'DOCUMENTED_BASIS_OVERCLAIMED') for f in r['layer_a']['findings']) for r in overstated),
            'of_which_critic_uncertainty_or_integrity_fail': sum(any(K.assessments(a['output'])[d]['judgment'] == 'FAIL' for a in r['critics'].values()
                                                                   for d in ('uncertainty', 'evidence_integrity')) for r in overstated)},
        'falsifiability_mechanism_checker': {q: {'agreement': questions[q]['agreement'], 'pairs': questions[q]['pairs']} for q in ('explicit_mechanism', 'falsifiable')},
        'selective_escalation_trigger_counterfactual': {'subjects_jev_would_flag': sum(flagged.values()),
            'by_policy_classification': {c: flagged[c] for c in Q.CLASSES}, 'applied': False}}
    used = [r['shadow'] for r in rows]
    prov = Counter(r['provenance'] for r in rows)
    return {'schema': JEV_COMPARISON_V, 'fixture': manifest['fixture'], 'workspace_manifest_sha256': digest(manifest),
            'subjects_compared': len(rows), 'questions': questions, 'candidate_uses': uses,
            'jev_usage': {'requested_model': JEV_MODEL, 'returned_models': dict(Counter(s['response']['model'] for s in used)),
                          'input_tokens': sum(s['response']['usage']['input_tokens'] for s in used),
                          'output_tokens': sum(s['response']['usage']['output_tokens'] for s in used),
                          'cost': S.UNKNOWN if any(s['cost'] == S.UNKNOWN for s in used) or not used else sum(s['cost'] for s in used),
                          'response_provenance': {'operator_attested': prov['OPERATOR_ATTESTED'], 'missing': prov['MISSING'],
                                                  'mismatched': prov['MISMATCHED'], 'provider_verified': 0}},
            'missing': {**missing, 'archives_not_supplied': sorted(missing['archives_not_supplied'])},
            'interpretation': INTERPRETATION, 'shadow_only': True, 'routing_changed': False, 'jev_overrides_deterministic': False,
            'calibration_established': False, 'authorises': []}
