"""Contract fixtures are not registered native observations or owner approval."""
import copy
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from src.research.spec import canonical
from src.research.opportunity_scout.n1_collector import binding as B, readiness as R
from src.research.opportunity_scout.v004_monitoring import ACCOUNT_PATHS
from src.research.opportunity_scout.v004_r3 import policy
from tests.scout_n1_fixtures import plan, changed


class NativeReadinessTests(unittest.TestCase):
    def record(self):
        b = {'binary_sha256': 'a' * 64, 'runtime': {'cli_version': 'FICTIONAL_DECLARATION_NOT_A_CLI', 'model': 'FICTIONAL_MODEL'},
             'argv': ['FICTIONAL_BOUND_ARGV'], 'environment': {}, 'system_sha256': 'b' * 64,
             'stdin_sha256': 'c' * 64, 'session_id': 'FICTIONAL_SESSION', 'capture_path': 'FICTIONAL_CAPTURE'}
        record = {'schema': R.VERSION, 'fixture': False, 'basis': 'OWNER_REVIEW_OF_INSTALLED_BUILD',
                  'bindings': {'binary_sha256': b['binary_sha256'], **b['runtime'], 'argv': b['argv'],
                               'environment_sha256': B.sha(canonical(b['environment'])),
                               'resource_policy_sha256': policy.policy_hash(), 'limits': dict(B.LIMITS),
                               'system_sha256': b['system_sha256'], 'stdin_sha256': b['stdin_sha256']},
                  'controls_supported': {k: True for k in R.CONTROLS},
                  'evidence': [{'description': 'FICTIONAL UNIT CONTRACT ONLY; no actual observation', 'sha256': 'd' * 64}]}
        return b, record

    def test_runtime_contract_consistency_is_not_authority(self):
        b, r = self.record()
        self.assertEqual(R.runtime_review(b, r), B.sha(canonical(r)))
        with patch('subprocess.Popen') as launch:
            with self.assertRaisesRegex(B.Refused, 'disabled'):
                R.launch_native(b, r, enabled=True)
        launch.assert_not_called()

    def test_missing_fixture_or_mismatched_verification_is_rejected(self):
        b, r = self.record()
        variants = [None, {}, {**r, 'fixture': True}, {**r, 'basis': 'DOCUMENTATION_ONLY'}, {**r, 'evidence': []}]
        for key in r['bindings']:
            wrong = copy.deepcopy(r); wrong['bindings'][key] = 'CHANGED'; variants.append(wrong)
        for key in R.CONTROLS:
            wrong = copy.deepcopy(r); wrong['controls_supported'][key] = False; variants.append(wrong)
        for wrong in variants:
            with self.subTest(record=wrong), self.assertRaises(B.Refused):
                R.runtime_review(b, wrong)

    def test_account_plan_cannot_impersonate_a_passed_window(self):
        b, _ = self.record()
        p = {'schema': R.VERSION, 'kind': 'PROSPECTIVE_OBSERVATION_PLAN',
             'session_id': b['session_id'], 'capture_path': b['capture_path'],
             'account_paths': list(ACCOUNT_PATHS), 'baseline_seconds': 60, 'cooldown_seconds': 60,
             'maximum_sample_gap_seconds': 5, 'managed_policy_presence_check': True,
             'process_start_ancestry_coverage': True, 'stop_on_any_metadata_drift': True,
             'stop_on_development_process': True, 'credential_content_reads': False,
             'historical_writer': 'UNKNOWN', 'baseline_observed': False, 'active_window_observed': False}
        self.assertEqual(R.observation_plan(b, p), B.sha(canonical(p)))
        for key, value in [('baseline_observed', True), ('active_window_observed', True), ('account_paths', []),
                           ('historical_writer', 'DEVELOPMENT'), ('credential_content_reads', True),
                           ('session_id', 'OTHER'), ('capture_path', 'OTHER'), ('maximum_sample_gap_seconds', 6)]:
            with self.subTest(key=key), self.assertRaises(B.Refused):
                R.observation_plan(b, {**p, key: value})

    def test_missing_owner_consent_and_fixture_success_cannot_enable_native(self):
        with tempfile.TemporaryDirectory() as d:
            b, a, data = plan(d)
            for approval in (None, a):
                with patch('subprocess.Popen') as launch:
                    with self.assertRaises(B.Refused):
                        R.review_plan(b, approval, data, {}, {})
                    with self.assertRaises(B.Refused):
                        R.launch_native(b, approval, data, fixture_success=True)
                launch.assert_not_called()
            self.assertFalse(Path(b['audit_root']).exists())

    def test_registry_cannot_dirty_sterile_working_directory(self):
        with tempfile.TemporaryDirectory() as d:
            b, a, data = plan(d)
            b, a = changed(b, audit_root=b['cwd'])
            with self.assertRaisesRegex(B.Refused, 'registry/cwd overlap'):
                B.validate(b, a, data)
