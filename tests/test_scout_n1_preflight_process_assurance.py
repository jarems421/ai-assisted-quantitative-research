"""Fixed local Python/PowerShell fixtures only; no WMI/account/model commands."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from src.research.opportunity_scout.v004_runtime import OS_ENV

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/scout_n1_queue_fixture.py'


@unittest.skipUnless(os.name == 'nt', 'Windows PowerShell queue implementation')
class QueueAssuranceTests(unittest.TestCase):
    def run_case(self, case):
        env = {k: v for k, v in os.environ.items() if k.upper() in OS_ENV}
        result = subprocess.run([sys.executable, '-I', str(FIXTURE), case],
                                capture_output=True, timeout=75, env=env, shell=False)
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

    def test_shutdown_persists_pending_collision_peers_before_end(self):
        report = self.run_case('shutdown')
        self.assertEqual(report['shutdown_events_persisted'], 2)
        self.assertTrue(report['unrelated_event_retained'])

    def test_queued_fictional_claude_start_at_shutdown_is_rejected(self):
        self.assertEqual(self.run_case('shutdown_claude')['shutdown_events_persisted'], 2)

    def test_shutdown_write_failure_retains_events_and_cannot_end(self):
        self.assertTrue(self.run_case('shutdown_disk_failure')['shutdown_failed_without_removal'])

    def test_shutdown_unsubscribe_failure_retains_events_and_cannot_end(self):
        self.assertTrue(self.run_case('shutdown_unsubscribe_failure')['shutdown_failed_without_removal'])


if __name__ == '__main__':
    unittest.main()
