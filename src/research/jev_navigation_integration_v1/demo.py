"""Injected fictional transport only. Never reads a credential or makes a provider call."""
from datetime import datetime, timedelta, timezone
from src.research.spec import canonical, digest
from src.research.quarry_v1 import io, demo as D, evidence as Q
from src.research.jev_navigation_v1 import workspace as N, demo as J
from . import workspace as W, evaluation as V


def synthetic_approval(plan, root):
    """Fixture-only owner/account doubles, never suitable for LIVE dispatch."""
    now = datetime.now(timezone.utc)
    evidence = b'SYNTHETIC account/version/price/hard-cap evidence; not a real account or permission.'
    io.write(root / 'synthetic-account.txt', evidence, raw=True)
    (root / 'audit').mkdir()
    return {'schema': 'JEV_PROVIDER_OWNER_APPROVAL_V001', 'fixture': 'SYNTHETIC', 'owner': 'SYNTHETIC_FIXTURE_OPERATOR',
            'approved_at': now.isoformat(), 'expires_at': (now + timedelta(hours=1)).isoformat(),
            'plan_sha256': digest(plan), 'payload_sha256': plan['payload_sha256'],
            'allowed_data_classification': plan['data_classification'], 'disclosure_approved': True,
            'request_ceiling': 1, 'spend_ceiling_micro_usd': 3000, 'account_context': 'SYNTHETIC_NOT_AN_ACCOUNT',
            'account_evidence_sha256': io.sha(evidence), 'availability_model': plan['model'],
            'availability_basis': 'ACCOUNT_SPECIFIC_VERSION_CONFIRMATION', 'account_evidence_verified_at': now.isoformat(),
            'independent_billing_hard_limit_confirmed': True, 'remaining_account_hard_limit_micro_usd': 3000,
            'price_usd_per_billion_input_tokens': 42, 'output_tokens_free_confirmed': True, 'audit_root': str(root / 'audit')}


def run(out):
    root = io.new_directory(out, prefix='jev-provider-v1-')
    quarry_root = io.new_directory(io.ROOT / '.research' / ('quarry-v1-' + root.name)) if root.is_relative_to(io.ROOT) else root
    D.fixtures(quarry_root)
    Q.import_file(quarry_root / 'registry.json', quarry_root / 'supply.json', quarry_root / 'original.txt', quarry_root / 'custody')
    Q.export(quarry_root / 'custody', quarry_root / 'inspection.json', quarry_root / 'subject.json', quarry_root / 'handoff')
    nav = io.ROOT / '.research' / ('jev-navigation-v1-' + root.name) if root.is_relative_to(io.ROOT) else root / 'navigation'
    N.prepare(quarry_root / 'handoff/input.json', nav)
    provider_ws = root / 'provider'
    W.prepare(nav, provider_ws, model='jev-1.14.0', quarry_export=quarry_root / 'handoff')
    _, plan, _, bundle = W.load(provider_ws)
    io.write(root / 'synthetic-approval.json', synthetic_approval(plan, root))
    response = J.synthetic_response(bundle, {'B_F1_ORDER': {'predictor': 'yes', 'units': 'yes'}, 'C_AMBIGUOUS': {'predictor': 'unsure'}})['response']
    response['model'] = plan['model']  # Construct a clearly marked synthetic transport fixture, never a received answer.
    io.write(root / 'synthetic-labels.json', {r['id']: {'relevance': 'RELEVANT' if r['id'] == 'B_F1_ORDER' else 'UNRESOLVED' if r['id'] == 'C_AMBIGUOUS' else 'IRRELEVANT',
                                                   'important': r['id'] == 'B_F1_ORDER', 'reason': 'Synthetic designer control, not human judgment'} for r in bundle['request']['records']})
    io.write(root / 'synthetic-independence.txt', b'SYNTHETIC designer controls; no independent human benchmark', raw=True)
    io.write(root / 'registration.json', {'schema': 'JEV_NAVIGATION_EVALUATION_REGISTRATION_V001', 'fixture': 'SYNTHETIC',
                                         'labels_sha256': io.sha(io.read(root / 'synthetic-labels.json')),
                                         'independence_record_sha256': io.sha(io.read(root / 'synthetic-independence.txt')),
                                         'inspection_budgets': [1, 3], 'baseline': 'EXISTING_FIXED_KEYWORD_GRAPH_BASELINE',
                                         'additional_baseline_order': ['B_F1_ORDER', 'C_AMBIGUOUS', 'A_WRONG_ASSET'],
                                         'additional_baseline_description': 'Separate competent structured/analyst baseline needed for a real evaluation.'})
    V.freeze(provider_ws, root / 'registration.json')

    def fixture(payload, key, emit):
        emit(canonical(response))
        return 200

    W.dispatch(provider_ws, root / 'synthetic-approval.json', root / 'synthetic-account.txt', enabled=True, fixture_transport=fixture)
    report = W.report(provider_ws)
    evaluation = V.compare(provider_ws, root / 'synthetic-labels.json', root / 'synthetic-independence.txt')
    io.write(root / 'report.json', report)
    io.write(root / 'evaluation-report.json', evaluation)
    return {'fixture': 'SYNTHETIC_TRANSPORT_NOT_JEV_PERFORMANCE', 'order': [r['id'] for r in report['inspection_queue']],
            'raw_response_retained': True, 'external_requests': report['external_requests'], 'actual_cost': 'UNKNOWN',
            'human_inspection': str(quarry_root / 'handoff/human-inspection.json'), 'accuracy_established': False,
            'ready': False, 'authorises': []}
