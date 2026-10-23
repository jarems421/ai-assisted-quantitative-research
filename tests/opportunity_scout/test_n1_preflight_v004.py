"""Portable fictional contracts; no real observation or private evidence read."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.opportunity_scout.n1_preflight import monitor as H
from src.research.opportunity_scout.n1_preflight_v004 import monitor as N
from tests.opportunity_scout import test_n1_preflight_monitor as historical_tests


class ProspectiveObserverTests(unittest.TestCase):
    def test_reader_is_exact_versioned_copy_and_historical_sources_are_pinned(self):
        names = {
            'watch.ps1': 'f17a577de7c04855305adfdec1ebfc6bac8cadae6570d66832c035e5ec03c881',
            'monitor.py': 'da235994103f4565c391e147fe6118984cd5bec3f1c9f675dbc74944fb8e409b',
            'queue.ps1': 'f9521f20e06f0b1314376e88cf49a9f70b60477e4c5327be78d18392084f977a',
        }
        folder = H.ROOT / 'src/research/opportunity_scout/n1_preflight'
        for name, expected in names.items():
            self.assertEqual(hashlib.sha256((folder / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest(), expected)
        original = (folder / 'monitor.py').read_text()
        prospective = (folder.parent / 'n1_preflight_v004/monitor.py').read_text()
        self.assertEqual(prospective, original.replace('SCOUT_N1_PROCESS_OBSERVER_V003', N.VERSION)
                         .replace('n1-admin-observer-v003', N.DIRECTORY.name))
        self.assertEqual((N.VERSION, N.DIRECTORY.name), ('SCOUT_N1_PROCESS_OBSERVER_V004', 'n1-admin-observer-v004'))
        self.assertFalse(N.reader_receipt()['N1_admission'])
        self.assertFalse(N.reader_receipt()['continuous_coverage_certified'])

    def test_new_contract_rejects_all_historical_headers_and_paths(self):
        for version in ('001', '002', '003'):
            r = historical_tests.Records()
            raw = r.row('HEADER', {'schema': 'SCOUT_N1_PROCESS_OBSERVER_V' + version, 'claude_invocations': 0})
            with self.subTest(version=version), self.assertRaisesRegex(N.Refused, 'observer header required'):
                N.Stream().feed(raw)
            path = N.ROOT / '.research/opportunity_scout' / ('n1-admin-observer-v' + version)
            with patch.object(N, 'IS_WINDOWS', True), patch.object(N, 'require_normal_user'), \
                    patch.object(N, 'exclusive') as create, patch.object(N.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(N.Refused, 'sole fixed observer directory'):
                    N.observe(path)
                create.assert_not_called(); launch.assert_not_called()

    def test_registered_v003_gap_remains_invalid_in_fictional_timing_replay(self):
        r = historical_tests.Records()
        raw = r.row('HEADER', {'schema': H.VERSION, 'claude_invocations': 0})
        raw += r.row('SNAPSHOT', {'processes': []})
        raw += r.row('HEARTBEAT', {'subscriptions_present': True}, 34868)
        # Public timing facts only, not original system-wide process records.
        raw += r.row('HEARTBEAT', {'subscriptions_present': True}, 45018)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fictional-v003-gap.jsonl'; path.write_bytes(raw)
            with self.assertRaisesRegex(H.Refused, 'producer heartbeat gap'):
                H.audit(path)
            with self.assertRaisesRegex(N.Refused, 'observer header required'):
                N.audit(path)
            self.assertEqual(path.read_bytes(), raw)

    def test_new_reader_retains_existing_virtual_safety_and_cooldown_regressions(self):
        # Reuse the unchanged 16 applicable V003 tests against the exact copied
        # reader. All account observations/processes are mocked by those tests.
        suite = unittest.defaultTestLoader.getTestCaseNames(historical_tests.ObserverTests)
        with patch.object(historical_tests, 'M', N):
            for name in suite:
                if name == 'test_v003_producer_reader_receipt_and_fixed_path_agree':
                    continue
                with self.subTest(regression=name):
                    getattr(historical_tests.ObserverTests(name), name)()

    def test_native_launch_remains_disabled(self):
        from src.research.opportunity_scout.n1_collector import readiness
        with self.assertRaises(Exception):
            readiness.launch_native()

