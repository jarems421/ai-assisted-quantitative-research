"""Fixed local Python/PowerShell fixtures only; no WMI/account/model commands."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.research.opportunity_scout.v004_runtime import OS_ENV

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/scout_n1_queue_fixture.py'


@unittest.skipUnless(os.name == 'nt', 'Windows PowerShell queue implementation')
class QueueAssuranceTests(unittest.TestCase):
    def test_v004_virtual_heartbeat_deadlines_and_exact_ack_burst(self):
        from src.research.opportunity_scout.n1_preflight_v004 import monitor as N
        from src.research.opportunity_scout.n1_preflight import monitor as H
        with tempfile.TemporaryDirectory(prefix='scout-heartbeat-fictional-') as directory:
            env = {k: v for k, v in os.environ.items() if k.upper() in OS_ENV}
            shell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
            env['PSModulePath'] = str(shell.parent / 'Modules')
            result = subprocess.run([str(shell), '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                                    str(ROOT / 'tests/fixtures/scout_n1_v004_heartbeat_fixture.ps1'),
                                    '-FixtureRoot', str(ROOT), '-OutputDirectory', directory],
                                    capture_output=True, timeout=75, env=env, shell=False)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            reports = {r['case']: r for r in json.loads(result.stdout)}
            self.assertEqual(len(reports), 17)
            for name, report in reports.items():
                with self.subTest(case=name):
                    self.assertTrue(report['unrelated_retained'])
                    self.assertTrue(report['exact_pending'])
                    path = Path(directory) / (name + '.jsonl')
                    raw = path.read_bytes()
                    frames = [json.loads(line) for line in raw.splitlines()]
                    records = [json.loads(f['record']) for f in frames]
                    previous = '0' * 64
                    for i, (frame, record) in enumerate(zip(frames, records), 1):
                        digest = hashlib.sha256(frame['record'].encode()).hexdigest()
                        self.assertEqual((record['seq'], record['previous'], frame['sha256']), (i, previous, digest))
                        previous = digest
                    events = [r for r in records if r['kind'] in ('START', 'EXIT')]
                    acks = [r for r in records if r['kind'] == 'QUEUE_ACK']
                    for ack in acks:
                        event = records[ack['seq'] - 2]
                        self.assertIn(event['kind'], ('START', 'EXIT'))
                        self.assertEqual(ack['data'], {'record_seq': event['seq'], 'queue_event_identifier': 73})
                    heartbeats = [r['elapsed_ms'] for r in records if r['kind'] == 'HEARTBEAT']
                    gaps = [b-a for a, b in zip(heartbeats, heartbeats[1:])]
                    if name == 'legacy_burst':
                        self.assertIsNone(report['error'])
                        self.assertEqual(max(gaps), 10200)
                        with self.assertRaisesRegex(H.Refused, 'producer heartbeat gap'):
                            H.audit(path)
                    elif name in ('burst', 'empty', 'shutdown'):
                        self.assertIsNone(report['error'])
                        self.assertLessEqual(max(gaps, default=0), 5000)
                        self.assertEqual(report['pending'], 0)
                        N.audit(path)
                        self.assertEqual([r['data']['pid'] for r in events], list(range(100, 134)) if name != 'empty' else [])
                        self.assertEqual(len(acks), len(events))
                        if name == 'burst':
                            self.assertEqual(max(gaps), 1200)
                            self.assertGreater(len(heartbeats), 2)
                    elif name == 'claude':
                        self.assertIsNone(report['error'])  # Producer records; strict reader rejects.
                        self.assertEqual(len(events), 34)
                        self.assertEqual(len(acks), 34)
                        with self.assertRaisesRegex(N.Refused, 'Claude process contaminates'):
                            N.audit(path)
                    else:
                        self.assertIsNotNone(report['error'])
                        reason = {
                            'first_slow_heartbeat': 'HEARTBEAT_WRITE_DEADLINE_EXPIRED',
                            'missing_subscription': 'SUBSCRIPTION_LOST',
                            'overflow': 'EVENT_QUEUE_LIMIT',
                            'malformed': 'ProcessID',
                            'persistence_failure': 'FICTIONAL_PERSISTENCE_FAILURE',
                        }.get(name, 'HEARTBEAT_DEADLINE_EXPIRED')
                        self.assertIn(reason, report['error'])
                        self.assertEqual(records[-1]['kind'], 'START' if name == 'persistence_failure' else 'ERROR')
                        self.assertEqual(any(r['kind'] == 'END' for r in records), name == 'shutdown_end_slow')
                        with self.assertRaises(N.Refused):
                            N.audit(path)
                        if name in ('slow_event', 'persistence_failure', 'late_queue', 'malformed'):
                            self.assertEqual(report['pending'], 34)
                            self.assertEqual(len(acks), 0)
                        if name == 'late_heartbeat':
                            self.assertEqual(report['last_heartbeat'], 0)
                            self.assertIn('HEARTBEAT_DEADLINE_EXPIRED', report['error'])
                    self.assertEqual(path.read_bytes(), raw)

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
