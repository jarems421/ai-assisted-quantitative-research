import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from docs.opportunity_scout.hosted_acceptance_v001 import prepare
from src.research.opportunity_scout.n1_collector import binding as B
from src.research.opportunity_scout.n1_collector.collector import _collect_fixture, collect_fixture
from tests.scout_n1_fixtures import plan, consent, changed


class N1BindingTests(unittest.TestCase):
    def test_unchanged_review_proposal_and_unknown_native_semantics(self):
        with tempfile.TemporaryDirectory() as d:
            b, a, data = plan(d)
            report = B.validate(b, a, data)
            self.assertFalse(report['native_launch_enabled'])
            self.assertEqual(report['native_semantics'], 'UNKNOWN')
            self.assertEqual(prepare.check()['status'], 'PROPOSAL_BYTES_CHECKED_NOT_EXECUTABLE')
            self.assertTrue(all(s['approved_for_hosted_use'] is False for s in prepare.request()['context']['seeds'].values()))
            import json
            protocol = json.loads((prepare.HERE / 'protocol.json').read_bytes())
            self.assertEqual({k: protocol[k] for k in B.LIMITS}, B.LIMITS)

    def test_bad_bindings_or_consent_never_launch_or_consume(self):
        with tempfile.TemporaryDirectory() as d:
            original, approval, data = plan(d)
            cases = [(original, None, data), ({}, approval, data), (original, approval, data + b'\n')]
            for key, value in [('proposal', {}), ('implementation', {}), ('dependencies', {}),
                               ('stdin_sha256', '0' * 64), ('system_sha256', '0' * 64),
                               ('binary_sha256', '0' * 64), ('runtime', 'UNKNOWN'),
                               ('argv', [original['binary'], '-c', 'raise SystemExit(99)']),
                               ('environment', {'ANTHROPIC_API_KEY': 'fictional-forbidden'}),
                               ('limits', {**B.LIMITS, 'watchdog_seconds': 601})]:
                b, a = changed(original, **{key: value}); cases.append((b, a, data))
            for key, value in [('approved', False), ('seeds', {}), ('N1_only_exception', False),
                               ('retained_seed_hosting_flags', True), ('binding_sha256', '0' * 64),
                               ('owner', ''), ('registered_at', ''), ('registered_at', 'not-a-date'),
                               ('registered_at', '2000-01-01T00:00:00'), ('trusted_local_filesystem_accepted', False),
                               ('privacy_resource_retention_accepted', False), ('single_invocation_only', False)]:
                a = {**approval, key: value}; cases.append((original, a, data))
            launch = Mock(side_effect=AssertionError('must not launch'))
            for b, a, payload in cases:
                with self.subTest(binding=b.get('stdin_sha256'), consent=a):
                    with self.assertRaises((ValueError, KeyError)):
                        _collect_fixture(b, a, payload, popen=launch)
            launch.assert_not_called()
            self.assertFalse(Path(original['audit_root']).exists())
            self.assertFalse(Path(original['capture_path']).exists())

    def test_native_templates_cannot_enter_fixture_launcher(self):
        with tempfile.TemporaryDirectory() as d:
            b, a, data = plan(d)
            b, a = changed(b, mode='NATIVE_REVIEW_ONLY')
            with self.assertRaisesRegex(B.Refused, 'native launch disabled'):
                collect_fixture(b, a, data)
            with self.assertRaises((B.Refused, AttributeError, TypeError)):
                B.review_native(b, a, data)
            self.assertFalse(Path(b['capture_path']).exists())

    def test_changed_system_bytes_and_dirty_cwd_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            b, a, data = plan(d)
            Path(b['system_file']).write_bytes(b'changed')
            with self.assertRaisesRegex(B.Refused, 'system bytes'):
                B.validate(b, a, data)
            b, a, data = plan(d)
            (Path(b['cwd']) / 'unexpected').touch()
            with self.assertRaisesRegex(B.Refused, 'sterile'):
                B.validate(b, a, data)
