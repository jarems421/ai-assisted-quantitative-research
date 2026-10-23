"""Real local Python pipes, outside the Scout suite's no-subprocess guard.

All producers are fixed checked-in harmless Python fixtures. No network/account
inspection or native CLI is involved. Temporary bindings are simulated consent.
"""
import hashlib
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.research.spec import canonical
from src.research.sec_pilot.parsing import offline
from src.research.opportunity_scout.storage import ROOT
from src.research.opportunity_scout.n1_collector import binding as B
from src.research.opportunity_scout.n1_collector.collector import collect_fixture, _collect_fixture
from src.research.opportunity_scout.n1_collector.evidence import Capture, audit
from tests.scout_n1_fixtures import plan, consent, changed

WORKER = ROOT / 'tests/fixtures/scout_n1_worker.py'


class N1ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.guard = offline()
        self.guard.__enter__()
        self.addCleanup(self.guard.__exit__, None, None, None)

    def run_case(self, case='bytes', **limits):
        b, a, payload = plan(self.root, case, **limits)
        result = collect_fixture(b, a, payload)
        self.assertEqual(result['status'], 'SEALED_BYTES_VERIFIED')
        return b, a, payload, result['receipt']

    def raw(self, b, channel='stdout'):
        return (Path(b['capture_path']) / (channel + '.bin')).read_bytes()

    def test_invalid_unknown_and_missing_terminal_preserved_exactly(self):
        b, a, data, r = self.run_case()
        expected = b'\xffinvalid JSON\r\n\n{"unknown_native_event":true}\n' + hashlib.sha256(data).hexdigest().encode() + b'\x00tail'
        self.assertEqual(self.raw(b), expected)
        self.assertEqual(self.raw(b, 'stderr'), b'\xfeSTDERR\r\npartial')
        self.assertEqual(r['outcome'], 'LOCAL_CAPTURE_COMPLETE', r['stop_reasons'])
        self.assertEqual(r['stdin']['bytes_written'], len(data))
        self.assertTrue(r['stdin']['completed'])
        self.assertEqual(r['native_terminal'], 'UNKNOWN_NOT_PARSED')
        for k in ('visible_generations', 'provider_requests', 'provider_usage', 'actual_subscription_charge', 'remote_cancellation'):
            self.assertEqual(r[k], 'UNKNOWN')
        self.assertEqual(r['scientific_slots_consumed'], 0)
        self.assertEqual(r['spawn_attempts'], 1)
        self.assertTrue(r['drain_complete'])
        if os.name == 'nt':
            self.assertIsInstance(r['process']['created_windows_filetime'], int)

    def test_concurrent_stderr_flood_does_not_deadlock_or_lose_bytes(self):
        b, _, _, r = self.run_case('flood')
        self.assertEqual(self.raw(b), b'O' * (128 * 4096))
        self.assertEqual(self.raw(b, 'stderr'), b'E' * (128 * 16384))
        self.assertEqual(r['returncode'], 0)
        self.assertEqual(r['outcome'], 'LOCAL_CAPTURE_COMPLETE', r['stop_reasons'])

    def test_split_utf8_and_malformed_partial_line_are_not_decoded(self):
        b, _, _, r = self.run_case('split', maximum_read_chunk_bytes=1)
        self.assertEqual(self.raw(b), b'\xe2\x82\xac\xf0\x9f\x8c\x8d\xff\r\n{"a":')
        rows = [json.loads(x) for x in (Path(b['capture_path']) / 'journal.jsonl').read_bytes().splitlines()]
        self.assertTrue(all(x['record']['length'] == 1 for x in rows if x['type'] == 'CHUNK'))
        self.assertEqual(r['outcome'], 'LOCAL_CAPTURE_COMPLETE', r['stop_reasons'])

    def test_delayed_descendant_eof_is_drained_after_parent_exit(self):
        b, _, _, r = self.run_case('delayed')
        self.assertEqual(self.raw(b), b'parent-exited\nheld-pipe-tail\xff')
        self.assertTrue(all(r['eof'].values()))
        self.assertTrue(r['drain_complete'])

    def test_trailing_data_after_terminal_looking_text_is_retained(self):
        b, _, _, r = self.run_case('trailing')
        self.assertEqual(self.raw(b), b'{"type":"result","result":"not authoritative"}\nTRAILING\xff\x00NO_NEWLINE')
        self.assertEqual(r['native_terminal'], 'UNKNOWN_NOT_PARSED')

    def test_nonzero_exit_is_independent_of_capture_integrity(self):
        b, _, _, r = self.run_case('nonzero')
        self.assertEqual(r['returncode'], 7)
        self.assertEqual(self.raw(b), b'partial-before-error')
        self.assertEqual(r['outcome'], 'LOCAL_CAPTURE_COMPLETE')
        self.assertEqual(r['native_compatibility'], 'NOT_TESTED')

    def test_failed_process_creation_remains_consumed(self):
        b, a, data = plan(self.root)
        def failed_spawn(*args, **kwargs):
            Path(kwargs['cwd']).rmdir()  # Empty test directory only; actual OS spawn fails.
            return subprocess.Popen(*args, **kwargs)
        result = _collect_fixture(b, a, data, popen=failed_spawn)
        self.assertEqual(result['receipt']['stop_reasons'], ['SPAWN_FAILED'])
        self.assertIsNone(result['receipt']['process'])
        self.assertTrue((Path(b['audit_root']) / (b['reservation_id'] + '.json')).is_file())
        with self.assertRaises(B.Refused):
            collect_fixture(b, a, data)

    def test_timeout_cancels_attributed_local_process_and_preserves_prefix(self):
        b, _, _, r = self.run_case('sleep', watchdog_seconds=.4)
        self.assertIn('WATCHDOG', r['stop_reasons'])
        self.assertEqual(self.raw(b), b'before-watchdog')
        self.assertTrue(r['cancellations'])
        self.assertEqual(r['remote_cancellation'], 'UNKNOWN')
        self.assertEqual(r['outcome'], 'STOP_EVIDENCE_RETAINED')
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())

    def test_io_trigger_keeps_crossing_chunk_and_marks_any_cutoff(self):
        b, _, _, r = self.run_case('threshold', combined_recording_io_trigger_bytes=8193,
                                   maximum_read_chunk_bytes=4096)
        self.assertIn('RECORDING_IO_TRIGGER', r['stop_reasons'])
        self.assertGreaterEqual(len(self.raw(b)), 8193)
        self.assertLess(len(self.raw(b)), 8193 + 4096)
        self.assertEqual(self.raw(b), b'X' * len(self.raw(b)))
        self.assertEqual(r['outcome'], 'STOP_EVIDENCE_RETAINED')

    def test_keyboard_interruption_never_seals_or_reopens_reservation(self):
        b, a, data = plan(self.root)
        with self.assertRaises(KeyboardInterrupt):
            _collect_fixture(b, a, data, after_raw=lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
        result = audit(b['capture_path'])
        self.assertEqual(result['status'], 'INTERRUPTED_EVIDENCE_RETAINED')
        self.assertGreater(sum(result['unindexed_tail_bytes'].values()), 0)
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())
        last = json.loads((Path(b['capture_path']) / 'journal.jsonl').read_bytes().splitlines()[-1])
        self.assertEqual(last['type'], 'INTERRUPTED')
        self.assertIn('os_call_returned', last['record']['local_cancel'])
        with self.assertRaises(B.Refused):
            collect_fixture(b, a, data)

    def worker(self, b, a, data, action='collect'):
        inputs = self.root / ('input-' + b['reservation_id'] + '.json')
        payload = self.root / ('stdin-' + b['reservation_id'] + '.bin')
        if not inputs.exists():
            inputs.write_bytes(canonical([b, a])); payload.write_bytes(data)
        return subprocess.Popen([sys.executable, '-m', 'tests.fixtures.scout_n1_worker', str(inputs), str(payload), action],
                                cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_real_process_crash_after_raw_fsync_preserves_unindexed_tail(self):
        b, a, data = plan(self.root)
        p = self.worker(b, a, data, 'crash-after-raw')
        out, err = p.communicate(b'x', timeout=15)
        self.assertEqual(p.returncode, 42, (out, err))
        result = audit(b['capture_path'])
        self.assertEqual(result['status'], 'INTERRUPTED_EVIDENCE_RETAINED')
        self.assertGreater(sum(result['unindexed_tail_bytes'].values()), 0)
        self.assertFalse((Path(b['capture_path']) / 'receipt.json').exists())
        with self.assertRaises(B.Refused):
            collect_fixture(b, a, data)

    def test_two_processes_racing_sole_reservation_launch_only_once(self):
        b, a, data = plan(self.root)
        workers = [self.worker(b, a, data) for _ in range(2)]
        for p in workers:
            p.stdin.write(b'x'); p.stdin.flush()
        outcomes = [p.communicate(timeout=20) for p in workers]
        self.assertEqual(sorted(p.returncode for p in workers), [0, 2], outcomes)
        result = audit(b['capture_path'])
        self.assertEqual(result['status'], 'SEALED_BYTES_VERIFIED')
        rows = [json.loads(x) for x in (Path(b['capture_path']) / 'journal.jsonl').read_bytes().splitlines()]
        self.assertEqual(sum(x['type'] == 'SPAWNED' for x in rows), 1)
        self.assertEqual(sum(x['type'] == 'CONSUMED' for x in rows), 1)

    def test_stale_lock_is_not_removed_even_for_different_reservation(self):
        b, a, _ = plan(self.root)
        c = Capture(b, a); c.abandon()
        lock = Path(b['audit_root']) / '.lock'
        before = lock.read_bytes()
        b2, a2, data2 = plan(self.root)
        with self.assertRaises(FileExistsError):
            collect_fixture(b2, a2, data2)
        self.assertEqual(lock.read_bytes(), before)
        self.assertFalse(Path(b2['capture_path']).exists())

    def test_consumed_claim_blocks_rebinding_to_another_capture_path(self):
        b, a, data, _ = self.run_case()
        b2, a2 = changed(b, capture_path=str(self.root / 'replacement'))
        with self.assertRaises(FileExistsError):
            collect_fixture(b2, a2, data)
        self.assertFalse(Path(b2['capture_path']).exists())

    def test_audit_is_read_only_and_detects_raw_and_journal_tampering(self):
        b, a, data, _ = self.run_case()
        root = Path(b['capture_path'])
        before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
        audit(root)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        raw = root / 'stdout.bin'
        raw.write_bytes(b'X' + raw.read_bytes()[1:])  # Deliberate corruption of temporary fixture only.
        with self.assertRaisesRegex(B.Refused, 'original bytes changed'):
            audit(root)

    def test_journal_suffix_rollback_cannot_silently_pass(self):
        b, _, _, _ = self.run_case()
        root = Path(b['capture_path']); journal = root / 'journal.jsonl'
        lines = journal.read_bytes().splitlines(keepends=True)
        journal.write_bytes(b''.join(lines[:-1]))
        self.assertEqual(audit(root)['status'], 'INTERRUPTED_EVIDENCE_RETAINED')

    def test_consumed_before_spawn_and_storage_failure_fail_closed(self):
        b, a, data = plan(self.root)
        def inspect_spawn(*args, **kwargs):
            root = Path(b['capture_path'])
            self.assertTrue((Path(b['audit_root']) / (b['reservation_id'] + '.json')).is_file())
            first = json.loads((root / 'journal.jsonl').read_bytes().splitlines()[0])
            self.assertEqual(first['type'], 'CONSUMED')
            self.assertEqual((root / 'witnesses/00000001.json').read_bytes().strip(), canonical(first))
            return subprocess.Popen(*args, **kwargs)
        self.assertEqual(_collect_fixture(b, a, data, popen=inspect_spawn)['status'], 'SEALED_BYTES_VERIFIED')

    def test_interruption_between_consumption_and_spawn_never_launches(self):
        b, a, data = plan(self.root)
        original = Capture.event
        def interrupt(capture, kind, record):
            if kind == 'LAUNCH_INTENT':
                raise KeyboardInterrupt()
            return original(capture, kind, record)
        with patch.object(Capture, 'event', interrupt), patch.object(subprocess, 'Popen') as launch:
            with self.assertRaises(KeyboardInterrupt):
                collect_fixture(b, a, data)
        launch.assert_not_called()
        self.assertEqual(audit(b['capture_path'])['status'], 'INTERRUPTED_EVIDENCE_RETAINED')
        self.assertTrue((Path(b['audit_root']) / (b['reservation_id'] + '.json')).exists())

    def test_index_persistence_failure_keeps_fsynced_original_tail(self):
        b, a, data = plan(self.root)
        original = Capture.event
        def fail_index(capture, kind, record):
            if kind == 'CHUNK':
                # Fail actual exclusive witness creation for this chunk only.
                with patch('src.research.opportunity_scout.n1_collector.evidence.exclusive', side_effect=OSError('fixture storage failure')):
                    return original(capture, kind, record)
            return original(capture, kind, record)
        with patch.object(Capture, 'event', fail_index):
            with self.assertRaises(OSError):
                collect_fixture(b, a, data)
        result = audit(b['capture_path'])
        self.assertEqual(result['status'], 'INTERRUPTED_EVIDENCE_RETAINED')
        self.assertGreater(sum(result['unindexed_tail_bytes'].values()), 0)
        self.assertTrue(result['registry_lock_present'])

    def test_fsync_failure_before_launch_cannot_start_child(self):
        b, a, data = plan(self.root)
        with patch('os.fsync', side_effect=OSError('fixture fsync failure')), patch.object(subprocess, 'Popen') as launch:
            with self.assertRaises(OSError):
                collect_fixture(b, a, data)
        launch.assert_not_called()
        self.assertFalse(Path(b['capture_path']).exists())
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())

    def test_incomplete_drain_is_explicit_and_stops(self):
        b, _, _, r = self.run_case('delayed', drain_grace_maximum_seconds=.05)
        self.assertIn('DRAIN_INCOMPLETE', r['stop_reasons'])
        self.assertEqual(r['outcome'], 'STOP_EVIDENCE_RETAINED')
        self.assertFalse(r['drain_complete'])
        self.assertTrue(r['truncated'])
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())

    def test_stop_receipt_cannot_unlock_a_different_reservation(self):
        b, _, _, _ = self.run_case('sleep', watchdog_seconds=.4)
        self.assertTrue((Path(b['capture_path']) / 'receipt.json').exists())
        b2, a2, data2 = plan(self.root)
        with self.assertRaises(FileExistsError):
            collect_fixture(b2, a2, data2)
        self.assertFalse(Path(b2['capture_path']).exists())

    def test_closed_stdin_cannot_be_reported_as_complete(self):
        b, a, data = plan(self.root)
        def close_stdin(*args, **kwargs):
            p = subprocess.Popen(*args, **kwargs)
            p.stdin.close()  # Real harmless producer receives EOF before its input.
            return p
        result = _collect_fixture(b, a, data, popen=close_stdin)
        self.assertEqual(result['receipt']['outcome'], 'STOP_EVIDENCE_RETAINED')
        self.assertIn('STDIN_INCOMPLETE', result['receipt']['stop_reasons'])
        self.assertFalse(result['receipt']['stdin']['completed'])
        self.assertTrue(result['registry_lock_present'])

    def test_falsely_complete_receipt_cannot_release_lock(self):
        import copy
        _, _, _, normal = self.run_case()
        b, a, _ = plan(self.root)
        c = Capture(b, a)
        c.event('LAUNCH_INTENT', {'parent_invocations_maximum': 1})
        c.event('SPAWN_FAILED', {'error_type': 'FICTIONAL_FAILURE'})
        wrong = copy.deepcopy(normal)
        wrong.update(process=None, returncode=None, eof={'stdout': False, 'stderr': False},
                     raw_sha256={x: B.sha(b'') for x in ('stdout', 'stderr')},
                     recorded_bytes={'stdout': 0, 'stderr': 0})
        with self.assertRaisesRegex(B.Refused, 'false complete'):
            c.seal(wrong)
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())

    def test_unknown_eof_channel_is_not_a_completion_fact(self):
        b, a, _ = plan(self.root)
        c = Capture(b, a)
        c.event('LAUNCH_INTENT', {})
        c.event('SPAWNED', {'pid': 999999})
        c.event('EOF', {'channel': 'invented'})
        c.abandon()
        with self.assertRaisesRegex(B.Refused, 'invalid/duplicate EOF'):
            audit(b['capture_path'])

    def monitored_case(self, case='sleep', fault=None):
        from tests.scout_n1_admission_fixtures import monitored
        from src.research.opportunity_scout.n1_collector import collector as C
        b, a, data, gate, clock = monitored(self.root, case, fault)
        if os.name != 'nt':
            # This receiver requires queried Windows creation identity. No
            # POSIX placeholder is substituted. CI selects this suite on Windows.
            with patch.object(C, 'time', clock), self.assertRaisesRegex(B.Refused, 'identity/start/parent'):
                collect_fixture(b, a, data, monitor=gate)
            self.assertTrue((Path(b['audit_root']) / (b['reservation_id'] + '.json')).exists())
            return b, a, data, None
        with patch.object(C, 'time', clock):
            result = collect_fixture(b, a, data, monitor=gate)
        return b, a, data, result

    def test_monitored_capture_requires_complete_cooldown_and_keeps_bytes(self):
        b, a, data, result = self.monitored_case('split')
        if result is None: return
        r = result['receipt']
        self.assertEqual(r['outcome'], 'LOCAL_CAPTURE_COMPLETE', r['stop_reasons'])
        self.assertTrue(r['monitor']['complete'])
        self.assertFalse(r['monitor']['native_launch_enabled'])
        self.assertEqual(self.raw(b), b'\xe2\x82\xac\xf0\x9f\x8c\x8d\xff\r\n{"a":')
        self.assertGreaterEqual(r['observed_wall_seconds_through_receipt'], 60)
        self.assertEqual(r['remote_cancellation'], 'UNKNOWN')
        self.assertTrue(result['reservation_consumed'])
        self.assertFalse(result['registry_lock_present'])

    def test_observation_failures_cancel_existing_collector_and_never_retry(self):
        for fault in ('coverage', 'identity', 'stale', 'drift', 'source_error'):
            with self.subTest(fault=fault):
                # Each fictional attempt has its own registry, never a reset.
                case_root = self.root / fault; case_root.mkdir()
                original = self.root; self.root = case_root
                try:
                    b, a, data, result = self.monitored_case(fault=fault)
                finally:
                    self.root = original
                if result is None: continue
                r = result['receipt']
                self.assertEqual(r['outcome'], 'STOP_EVIDENCE_RETAINED')
                self.assertIn('MONITOR_STOP', r['stop_reasons'])
                self.assertEqual(self.raw(b), b'before-watchdog')
                self.assertTrue(r['cancellations'])
                self.assertTrue(all(x['target_pid'] == r['process']['pid'] for x in r['cancellations']))
                self.assertEqual(r['remote_cancellation'], 'UNKNOWN')
                self.assertFalse(r['monitor']['complete'])
                self.assertTrue(result['registry_lock_present'])
                with patch('subprocess.Popen') as launch, self.assertRaises(B.Refused):
                    collect_fixture(b, a, data)
                launch.assert_not_called()

    def test_failed_monitor_cleanup_retains_stop_even_with_exit_and_eof(self):
        b, _, _, result = self.monitored_case('split', 'cleanup')
        if result is None: return
        r = result['receipt']
        self.assertEqual(r['returncode'], 0)
        self.assertTrue(all(r['eof'].values()))
        self.assertIn('MONITOR_STOP', r['stop_reasons'])
        self.assertFalse(r['monitor']['complete'])
        self.assertTrue(result['registry_lock_present'])

    def test_observation_failure_after_claim_before_spawn_stays_consumed(self):
        from tests.scout_n1_admission_fixtures import monitored, frame
        from src.research.opportunity_scout.n1_collector import collector as C
        b, a, data, gate, clock = monitored(self.root)
        original = Capture.event
        def lose_coverage(capture, kind, record):
            if kind == 'LAUNCH_INTENT':
                def source(phase, expected, now, exited):
                    row = frame(b, gate.window.seq + 1, now)
                    row['coverage']['starts'] = False
                    return row
                gate.source = source
            return original(capture, kind, record)
        with patch.object(C, 'time', clock), patch.object(Capture, 'event', lose_coverage), \
                patch('subprocess.Popen') as launch, self.assertRaisesRegex(B.Refused, 'coverage'):
            collect_fixture(b, a, data, monitor=gate)
        launch.assert_not_called()
        self.assertTrue((Path(b['audit_root']) / (b['reservation_id'] + '.json')).exists())
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())
        self.assertEqual(audit(b['capture_path'])['status'], 'INTERRUPTED_EVIDENCE_RETAINED')

    def test_false_monitor_completion_cannot_release_registry(self):
        from tests.scout_n1_admission_fixtures import package, process_identity
        from src.research.opportunity_scout.n1_collector.admission import VERSION
        _, _, _, normal = self.run_case()
        b, a, _ , _ = package(self.root)
        c = Capture(b, a); identity = process_identity()
        c.event('LAUNCH_INTENT', {}); c.event('SPAWNED', identity)
        c.event('OS_EXIT', {'returncode': 0})
        for channel in ('stdout', 'stderr'): c.event('EOF', {'channel': channel})
        wrong = copy.deepcopy(normal)
        wrong.update(process=identity, returncode=0, raw_sha256={x: B.sha(b'') for x in ('stdout', 'stderr')},
                     recorded_bytes={'stdout': 0, 'stderr': 0}, monitor={'schema': VERSION, 'fixture': True,
                     'window_id': b['admission_contract']['window_id'], 'complete': True, 'native_launch_enabled': False})
        with self.assertRaisesRegex(B.Refused, 'false complete observation'):
            c.seal(wrong)
        self.assertTrue((Path(b['audit_root']) / '.lock').exists())
