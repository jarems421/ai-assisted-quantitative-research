"""Fixed local Python/PowerShell fixtures only; no WMI/account/model commands."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/scout_n1_queue_fixture.py'


@unittest.skipUnless(os.name == 'nt', 'Windows PowerShell queue implementation')
class QueueAssuranceTests(unittest.TestCase):
    def run_case(self, case):
        env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP') if k in os.environ}
        result = subprocess.run([sys.executable, '-I', str(FIXTURE), case],
                                capture_output=True, timeout=35, env=env, shell=False)
        self.assertEqual(result.returncode, 0, result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
        report = json.loads(result.stdout)
        self.assertTrue(report['fixture'])
        self.assertTrue(report['frame_chain_verified'])
        self.assertEqual(report['claude_invocations'], 0)
        self.assertEqual(report['wmi_subscriptions'], 0)
        return report

    def test_duplicate_identifiers_preserve_both_objects_and_unrelated_event(self):
        report = self.run_case('collision')
        self.assertEqual(report['colliding_events_preserved'], 2)
        self.assertTrue(report['unrelated_event_retained'])

    def test_concurrent_sources_acknowledge_each_visible_object_once(self):
        self.assertGreaterEqual(self.run_case('concurrent')['processed'], 10)

    def test_failed_persistence_cannot_acknowledge_event(self):
        self.assertTrue(self.run_case('disk_failure')['failed_write_event_still_queued'])

    def test_missing_exact_object_fails_without_consuming_collision_peer(self):
        self.assertTrue(self.run_case('missing_object')['missing_object_failed_closed'])


if __name__ == '__main__':
    unittest.main()
