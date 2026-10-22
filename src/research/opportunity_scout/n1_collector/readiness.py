"""Prospective one-N1 launch plan; no executable native launch path.

Checks supplied artifacts for consistency. It neither authenticates a human
registration nor observes an installed CLI/account. External assertions remain
assertions until independently reviewed. A fixture never supplies native evidence.
"""
import copy
import json
from pathlib import Path

from src.research.spec import canonical
from ..v004_monitoring import ACCOUNT_PATHS
from ..v004_r3 import policy
from . import binding as B

VERSION = 'SCOUT_N1_LAUNCH_READINESS_V002'
CONTROLS = ('exact_argv', 'subscription_configuration', 'research_config_configuration', 'requested_no_tools_mcp_skills',
            'requested_no_resume_zero_request_retries_no_fallback', 'fresh_session', 'raw_stream_output', 'medium_32768',
            'requested_two_turns_visible_generation_compliance_posthoc')


def runtime_review(binding, record):
    """No commands or executable reads here; validate a supplied review contract."""
    B.require(isinstance(record, dict) and record.get('schema') == VERSION, 'missing runtime verification')
    B.require(record.get('fixture') is False and record.get('basis') == 'OWNER_REVIEW_OF_INSTALLED_BUILD',
              'fictional/documentation-only success is not installed-runtime verification')
    expected = {'binary_sha256': binding['binary_sha256'], 'cli_version': binding['runtime']['cli_version'],
                'model': binding['runtime']['model'], 'argv': binding['argv'],
                'environment_sha256': B.sha(canonical(binding['environment'])),
                'resource_policy_sha256': policy.policy_hash(), 'limits': B.LIMITS,
                'system_sha256': binding['system_sha256'], 'stdin_sha256': binding['stdin_sha256']}
    B.require(record.get('bindings') == expected, 'runtime verification bindings differ')
    B.require(record.get('controls_supported') == {k: True for k in CONTROLS}, 'unsupported/unverified runtime control')
    B.require(isinstance(record.get('evidence'), list) and record['evidence'], 'installed-build support evidence required')
    for row in record['evidence']:
        B.require(set(row) == {'description', 'sha256'} and isinstance(row['description'], str) and row['description'].strip(), 'runtime evidence reference malformed')
        B.require(isinstance(row['sha256'], str) and len(row['sha256']) == 64 and
                  all(c in '0123456789abcdef' for c in row['sha256']), 'runtime evidence hash malformed')
    return B.sha(canonical(record))


def observation_plan(binding, plan):
    """Review a future monitoring plan, never fabricate a passed quiet window."""
    B.require(isinstance(plan, dict) and plan.get('schema') == VERSION and plan.get('kind') == 'PROSPECTIVE_OBSERVATION_PLAN', 'missing observation plan')
    B.require(plan.get('session_id') == binding['session_id'] and plan.get('capture_path') == binding['capture_path'], 'observation reservation differs')
    B.require(plan.get('account_paths') == list(ACCOUNT_PATHS), 'account watch set changed')
    B.require(plan.get('baseline_seconds') == 60 and plan.get('cooldown_seconds') == 60 and
              plan.get('maximum_sample_gap_seconds') == 5, 'quiet-window controls changed')
    B.require(plan.get('managed_policy_presence_check') is True and plan.get('process_start_ancestry_coverage') is True,
              'process/policy observation prerequisites missing')
    B.require(plan.get('stop_on_any_metadata_drift') is True and plan.get('stop_on_development_process') is True and
              plan.get('credential_content_reads') is False and plan.get('historical_writer') == 'UNKNOWN', 'account-isolation boundary changed')
    B.require(plan.get('baseline_observed') is False and plan.get('active_window_observed') is False,
              'a plan cannot impersonate actual account observations')
    return B.sha(canonical(plan))


def review_plan(binding, approval, payload, verification, observations):
    """Read-only, unlaunchable review artifact. No reservation is consumed."""
    binding, approval = copy.deepcopy(binding), copy.deepcopy(approval)
    B.review_native(binding, approval, payload)
    verification_hash = runtime_review(binding, verification)
    observation_hash = observation_plan(binding, observations)
    B.require(binding.get('runtime_verification_sha256') == verification_hash and
              binding.get('observation_plan_sha256') == observation_hash, 'review artifacts not bound in consent')
    registry = Path(binding['audit_root'])
    B.require(not (registry / '.lock').exists() and not (registry / (binding['reservation_id'] + '.json')).exists(),
              'stale/held lock or consumed reservation; no recovery/retry')
    manifest = json.loads((B.prepare.HERE / 'manifest.json').read_bytes())
    return {'schema': VERSION, 'status': 'OFFLINE_COHERENCE_ONLY_NOT_LAUNCH_PERMISSION',
            'binding_sha256': B.sha(canonical(binding)), 'approval_sha256': B.sha(canonical(approval)),
            'proposal': B.proposal(), 'collector_implementation': B.implementation(),
            'full_schema_sha256': manifest['full_two_card_schema_sha256'],
            'stdin_sha256': binding['stdin_sha256'], 'stdin_bytes': len(payload),
            'runtime_verification_sha256': verification_hash, 'observation_plan_sha256': observation_hash,
            'parent_invocations_maximum': 1, 'stdin_delivery': 'EXACT_BYTES_ONCE_THEN_EOF',
            'capture_path': binding['capture_path'], 'audit_root': binding['audit_root'],
            'reservation_id': binding['reservation_id'], 'session_id': binding['session_id'],
            'argv': binding['argv'], 'environment_sha256': B.sha(canonical(binding['environment'])),
            'limits': dict(B.LIMITS), 'resource_policy_sha256': policy.policy_hash(),
            'native_launch_enabled': False, 'consumed': False, 'provider_requests': 'UNKNOWN',
            'native_semantics': 'UNKNOWN', 'account_isolation': 'NOT_OBSERVED',
            'blockers': ['INDEPENDENT_ENGINEERING_REVIEW_AND_OWNER_REGISTRATION',
                         'ACTUAL_RUNTIME_SUPPORT_EVIDENCE_AND_RESEARCH_ACCOUNT_APPROVAL',
                         'LIVE_PRELAUNCH_AND_DURING_CAPTURE_OBSERVER_GATE_NOT_IMPLEMENTED',
                         'NATIVE_LAUNCH_WIRING_DISABLED'], 'authorises': []}


def launch_native(*args, **kwargs):
    # No enable flag, environment switch, fixture token or approval dictionary
    # can turn this review-only boundary into a process launch.
    raise B.Refused('native N1 launch disabled: reviewed live-observer admission and explicit owner registration required')
