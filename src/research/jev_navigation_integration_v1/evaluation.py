"""Freeze a separately labelled holdout before dispatch; reuse existing budget metrics."""
from src.research.spec import digest
from src.research.jev_navigation_v1 import contracts as K
from src.research.jev_navigation_v1.evaluation import at_budget
from src.research.quarry_v1 import io
from . import workspace as W

REGISTRATION = K.obj({'schema': {'const': 'JEV_NAVIGATION_EVALUATION_REGISTRATION_V001'},
                      'fixture': {'enum': ['SYNTHETIC', 'INDEPENDENT_HUMAN_HOLDOUT']},
                      'labels_sha256': K.HASH, 'independence_record_sha256': K.HASH,
                      'inspection_budgets': {**K.array({'type': 'integer', 'minimum': 1, 'maximum': 32}, 4), 'minItems': 1},
                      'baseline': {'const': 'EXISTING_FIXED_KEYWORD_GRAPH_BASELINE'},
                      'additional_baseline_order': {**K.array(K.LABEL, 32), 'minItems': 1},
                      'additional_baseline_description': K.TEXT})


def freeze(workspace, registration_path):
    root, plan, _, bundle = W.load(workspace)
    K.need(not (root / 'attempt.json').exists(), 'holdout registration must precede dispatch')
    registration = io.json_file(registration_path)
    K.validate(REGISTRATION, registration)
    K.need(all(type(b) is int and b <= len(bundle['request']['records']) for b in registration['inspection_budgets']), 'fixed budgets must fit frozen universe')
    K.need(set(registration['additional_baseline_order']) == {r['id'] for r in bundle['request']['records']}, 'additional baseline must rank the same complete record universe')
    # Labels and human independence records are opaque hashes here. Neither is read or sent.
    value = {'schema': 'JEV_NAVIGATION_FROZEN_EVALUATION_V001', 'plan_sha256': digest(plan),
             'registration': registration, 'request_sha256': bundle['request_sha256'],
             'record_ids': sorted(r['id'] for r in bundle['request']['records']),
             'endpoints': ['precision_at_budget', 'recall_at_budget', 'missed_important', 'incorrectly_prioritised',
                           'unresolved_inspections', 'abstentions', 'invalid_response_count', 'citation_and_stop_preservation'],
             'authorises': []}
    io.write(root / 'evaluation.json', value)
    return value


def compare(workspace, labels_path, independence_record_path):
    root, plan, _, bundle = W.load(workspace)
    frozen = io.json_file(root / 'evaluation.json')
    registration = frozen['registration']
    K.validate(REGISTRATION, registration)
    K.need(frozen['plan_sha256'] == digest(plan) and frozen['request_sha256'] == bundle['request_sha256'], 'evaluation freeze stale')
    labels_raw = io.read(labels_path, 1024 * 1024)
    independence_raw = io.read(independence_record_path, 1024 * 1024)
    K.need(io.sha(labels_raw) == registration['labels_sha256'] and io.sha(independence_raw) == registration['independence_record_sha256'], 'labels or independent exposure/assembly record changed since freeze')
    result = W.report(workspace)
    K.need(result['provider']['status'] != 'NOT_DISPATCHED', 'evaluation requires a retained attempt, including failure')
    claim = io.json_file(root / 'attempt.json')
    K.need(claim['evaluation_sha256'] == io.sha(io.read(root / 'evaluation.json')), 'evaluation must be frozen in the pre-dispatch claim')
    K.need((registration['fixture'] == 'SYNTHETIC') == (claim['fixture'] == 'SYNTHETIC'), 'synthetic results cannot establish human-holdout effectiveness')
    labels = K.loads(labels_raw)
    provider_status = result['provider']['status']
    model_metrics_available = provider_status in ('SYNTHETIC_VALID', 'PROVIDER_VALID')
    comparisons = []
    for budget in registration['inspection_budgets']:
        comparison = at_budget(result, labels, budget)
        ranking_metrics = comparison.pop('scripted_classification')
        comparison['navigation_classification'] = ranking_metrics if model_metrics_available else None
        comparison['model_metrics_status'] = 'VALID_CLASSIFICATIONS' if model_metrics_available else 'UNAVAILABLE_PROVIDER_ATTEMPT_UNUSABLE'
        comparison['abstention_status'] = 'RECORDED_FROM_VALID_CLASSIFICATIONS' if model_metrics_available else 'UNKNOWN_NO_VALID_CLASSIFICATIONS'
        if not model_metrics_available:
            comparison['abstentions'] = None
        structured = at_budget({**result, 'baseline_order': registration['additional_baseline_order']}, labels, budget)
        comparison['additional_baseline'] = structured['baseline']
        comparison['interpretation'] = 'Synthetic software diagnostics, not Jev effectiveness.' if claim['fixture'] == 'SYNTHETIC' else 'Owner-supplied holdout labels and independence attestations; not authenticated human identity or established accuracy.'
        if not model_metrics_available:
            comparison['interpretation'] = 'Provider attempt unusable: model-assisted metrics and abstention rates are unavailable. Baseline metrics are diagnostics only; the failed attempt remains in this evaluation.'
        comparisons.append(comparison)
    citations_preserved = all(r['citation'] == next(original['citation'] for original in bundle['request']['records'] if original['id'] == r['id']) for r in result['inspection_queue'])
    stops_preserved = all(r['availability'] == next(original['availability'] for original in bundle['request']['records'] if original['id'] == r['id']) for r in result['inspection_queue'])
    return {'schema': 'JEV_PROVIDER_EVALUATION_V002', 'comparisons': comparisons, 'fixture': registration['fixture'],
            'model_metrics_available': model_metrics_available, 'retained_attempts': 1,
            'usable_classification_attempts': int(model_metrics_available),
            'unusable_provider_attempts': int(not model_metrics_available),
            'invalid_response_count': result['invalid_response_count'], 'provider_status': result['provider']['status'],
            'citation_and_stop_preservation': citations_preserved and stops_preserved,
            'additional_baseline': {'description': registration['additional_baseline_description'], 'order': registration['additional_baseline_order']},
            'human_independence_authenticated': False, 'accuracy_established': False, 'authorises': []}
