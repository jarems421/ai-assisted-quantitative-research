"""Fictional OS-event records only; these tests inspect no account or process."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.research.opportunity_scout.n1_preflight import monitor as M


class Records:
    def __init__(self):
        self.seq = 0
        self.previous = '0' * 64

    def row(self, kind, data, elapsed=0):
        if kind in ('START', 'EXIT'):
            data = {**data, 'queue_event_identifier': data.get('queue_event_identifier', 7)}
            raw = self.one(kind, data, elapsed)
            persisted_seq = self.seq
            return raw + self.one('QUEUE_ACK', {'record_seq': persisted_seq, 'queue_event_identifier': data['queue_event_identifier']}, elapsed)
        return self.one(kind, data, elapsed)

    def one(self, kind, data, elapsed=0):
        self.seq += 1
        record = json.dumps({'seq': self.seq, 'previous': self.previous, 'elapsed_ms': elapsed,
                             'kind': kind, 'data': data}, separators=(',', ':'))
        self.previous = M.sha(record.encode())
        return json.dumps({'record': record, 'sha256': self.previous}).encode() + b'\n'

    def prefix(self, processes=()):
        return (self.row('HEADER', {'schema': M.VERSION, 'pid': 10, 'session': 'FICTIONAL_NOT_REGISTERED', 'claude_invocations': 0})
                + self.row('SNAPSHOT', {'processes': list(processes)})
                + self.row('HEARTBEAT', {'subscriptions_present': True}))


class ObserverTests(unittest.TestCase):
    def process(self, **changes):
        return {'pid': 11, 'parent_pid': 10, 'name': 'python.exe', 'creation_filetime': '100', **changes}

    def test_split_records_and_exact_audit_without_rewriting(self):
        r = Records()
        raw = r.prefix([self.process()]) + r.row('END', {'reason': 'STOP_REQUEST', 'coverage_certified': False}, 1000)
        state = M.Stream()
        for byte in raw:
            state.feed(bytes([byte]))
        self.assertTrue(state.ended)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'events.jsonl'
            path.write_bytes(raw)
            self.assertEqual(M.audit(path), {'head': state.previous, 'records': 4, 'bytes': len(raw)})
            self.assertEqual(path.read_bytes(), raw)

    def test_changed_bytes_chain_sequence_and_timestamp_rejected(self):
        original = Records().prefix()
        for old, new in [(b'HEARTBEAT', b'HEARTBEAX'), (b'"sha256": "', b'"sha256": "0')]:
            with self.subTest(old=old), self.assertRaises(M.Refused):
                M.Stream().feed(original.replace(old, new))
        for seq, previous, elapsed in [(9, '0' * 64, 0), (4, 'a' * 64, 0), (4, None, -1)]:
            r = Records(); prefix = r.prefix()
            if seq == 9:
                r.seq = 8
            if previous:
                r.previous = previous
            state = M.Stream(); state.feed(prefix)
            with self.subTest(seq=seq), self.assertRaises(M.Refused):
                state.feed(r.row('HEARTBEAT', {'subscriptions_present': True}, elapsed))

    def test_existing_and_transient_claude_both_stop(self):
        with self.assertRaisesRegex(M.Refused, 'contaminates'):
            M.Stream().feed(Records().prefix([self.process(name='Claude.exe')]))
        r = Records(); state = M.Stream(); state.feed(r.prefix())
        with self.assertRaisesRegex(M.Refused, 'contaminates'):
            state.feed(r.row('START', {'pid': 50, 'parent_pid': 1, 'name': 'claude.exe', 'event_filetime': '101'}))

    def test_proof_requires_start_exit_parent_name_and_time(self):
        r = Records(); state = M.Stream(); state.feed(r.prefix())
        with self.assertRaises(M.Refused):
            state.proof(50, 10, 'python.exe', 100)
        state.feed(r.row('START', {'pid': 50, 'parent_pid': 10, 'name': 'python.exe', 'event_filetime': '101'}))
        with self.assertRaises(M.Refused):
            state.proof(50, 10, 'python.exe', 100)
        state.feed(r.row('EXIT', {'pid': 50, 'name': 'python.exe', 'event_filetime': '102'}))
        state.proof(50, 10, 'python.exe', 100)
        for args in [(51, 10, 'python.exe', 100), (50, 11, 'python.exe', 100),
                     (50, 10, 'other.exe', 100), (50, 10, 'python.exe', 103)]:
            with self.subTest(args=args), self.assertRaises(M.Refused):
                state.proof(*args)

    def test_stale_missing_unknown_or_extra_events_stop(self):
        for kind, data, elapsed in [('HEARTBEAT', {'subscriptions_present': False}, 1),
                                    ('HEARTBEAT', {'subscriptions_present': True}, 5001),
                                    ('ERROR', {'code': 'AccessDenied'}, 1),
                                    ('PROVIDER_EVENT', {}, 1),
                                    ('END', {'reason': 'TIME_LIMIT', 'coverage_certified': False}, 1),
                                    ('START', {'pid': 1, 'parent_pid': 2, 'name': 'python.exe', 'event_filetime': '3', 'command_line': 'FORBIDDEN'}, 1)]:
            r = Records(); state = M.Stream(); state.feed(r.prefix())
            with self.subTest(kind=kind, data=data), self.assertRaises(M.Refused):
                state.feed(r.row(kind, data, elapsed))

    def test_missing_end_partial_tail_and_trailing_bytes_preserved(self):
        for suffix in (b'', b'partial', b'\xff'):
            r = Records(); raw = r.prefix() + suffix
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / 'events.jsonl'; path.write_bytes(raw)
                with self.assertRaises(M.Refused):
                    M.audit(path)
                self.assertEqual(path.read_bytes(), raw)
        r = Records(); raw = r.prefix() + r.row('END', {'reason': 'STOP_REQUEST', 'coverage_certified': False})
        for extra in (b'\n', b'garbage'):
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / 'events.jsonl'; path.write_bytes(raw + extra)
                with self.assertRaises(M.Refused):
                    M.audit(path)
                self.assertEqual(path.read_bytes(), raw + extra)

    def test_oversize_and_unsafe_process_fields_stop(self):
        state = M.Stream()
        with self.assertRaises(M.Refused):
            state.feed(b'x' * (M.MAX_BYTES + 1))
        for process in [self.process(pid=True), self.process(name=None), {**self.process(), 'environment': {}}]:
            with self.subTest(process=process), self.assertRaises(M.Refused):
                M.Stream().feed(Records().prefix([process]))

    def test_duplicate_claim_refuses_without_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'claim'
            M.exclusive(path, b'original')
            with self.assertRaises(FileExistsError):
                M.exclusive(path, b'changed')
            self.assertEqual(path.read_bytes(), b'original')

    def test_duplicate_json_keys_and_exit_before_snapshot_refused(self):
        state = M.Stream()
        with self.assertRaises(M.Refused):
            state.feed(b'{"record":"{}","record":"{}","sha256":"x"}\n')
        r = Records()
        state = M.Stream()
        state.feed(r.row('HEADER', {'schema': M.VERSION, 'claude_invocations': 0}))
        with self.assertRaises(M.Refused):
            state.feed(r.row('EXIT', {'pid': 12, 'name': 'python.exe', 'event_filetime': '100'}))

    def test_colliding_queue_ids_are_preserved_with_one_ack_per_event(self):
        r = Records(); state = M.Stream(); state.feed(r.prefix())
        state.feed(r.row('START', {'pid': 50, 'parent_pid': 10, 'name': 'python.exe', 'event_filetime': '101', 'queue_event_identifier': 7}))
        state.feed(r.row('EXIT', {'pid': 50, 'name': 'python.exe', 'event_filetime': '102', 'queue_event_identifier': 7}))
        self.assertEqual(state.seq, 7)
        self.assertIsNone(state.pending_ack)
        state.proof(50, 10, 'python.exe', 100)

    def test_missing_wrong_or_duplicate_ack_stops_without_ignoring_error(self):
        for fault in ('missing', 'wrong_record', 'wrong_id', 'duplicate'):
            r = Records(); state = M.Stream(); state.feed(r.prefix())
            state.feed(r.one('START', {'pid': 50, 'parent_pid': 10, 'name': 'python.exe', 'event_filetime': '101', 'queue_event_identifier': 7}))
            ack = {'record_seq': 4, 'queue_event_identifier': 7}
            if fault == 'duplicate':
                state.feed(r.one('QUEUE_ACK', ack))
            with self.subTest(fault=fault), self.assertRaises(M.Refused):
                if fault == 'missing':
                    state.feed(r.one('HEARTBEAT', {'subscriptions_present': True}))
                else:
                    if fault == 'wrong_record': ack['record_seq'] = 3
                    if fault == 'wrong_id': ack['queue_event_identifier'] = 8
                    state.feed(r.one('QUEUE_ACK', ack))

    def test_v001_header_cannot_be_migrated_to_v002(self):
        with self.assertRaises(M.Refused):
            M.Stream().feed(Records().row('HEADER', {'schema': 'SCOUT_N1_PROCESS_OBSERVER_V001', 'claude_invocations': 0}))

    def test_cli_cannot_accept_auth_executable_or_argv(self):
        for args in [[], ['--auth'], ['--observe-only', '--binary', 'claude.exe']]:
            with patch.object(M, 'observe') as observe, patch('sys.argv', ['monitor', *args]), \
                    patch('sys.stderr'), self.assertRaises(SystemExit):
                M.main()
            observe.assert_not_called()

    def test_virtual_end_to_end_normal_window_and_adversarial_failures(self):
        # Every OS observation and subprocess is fictional. Real IO is confined
        # to a temporary test directory. No Windows/account sampler is called.
        from src.research.opportunity_scout.v004_monitoring import ACCOUNT_PATHS
        for fault in (None, 'drift', 'stall', 'sample_gap', 'missing_start', 'missing_exit', 'child_timeout', 'rewrite'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as d:
                directory = Path(d)
                source = directory / 'events.jsonl'
                rows = Records(); source.write_bytes(rows.prefix())
                clock = SimpleNamespace(now=0.0, ended=False, rewritten=False)
                metadata = {'sampled_at': '2000-01-01T00:00:00+00:00', 'files': {p: {'state': 'ABSENT'} for p in ACCOUNT_PATHS}}

                def sample():
                    if fault == 'drift' and clock.now > 3:
                        return {**metadata, 'files': {p: {'state': 'REGULAR_FILE', 'size': 1} for p in ACCOUNT_PATHS}}
                    return metadata

                def append(kind, data):
                    with source.open('ab') as handle:
                        handle.write(rows.row(kind, data, int(clock.now * 1000)))

                def sleep(seconds):
                    clock.now += seconds
                    if fault == 'sample_gap' and clock.now > 2:
                        clock.now += 6
                    if fault == 'rewrite' and clock.now > 3 and not clock.rewritten:
                        raw = source.read_bytes(); source.write_bytes(raw.replace(b'HEARTBEAT', b'HEARTBEAX'))
                        clock.rewritten = True
                    if (directory / 'stop.request').exists():
                        if not clock.ended:
                            append('END', {'reason': 'STOP_REQUEST', 'coverage_certified': False}); clock.ended = True
                    elif fault != 'stall' or clock.now < 2:
                        append('HEARTBEAT', {'subscriptions_present': True})

                def launch(argv, **kwargs):
                    self.assertEqual(argv, [M.sys.executable, '-I', str(M.CHILD)])
                    self.assertFalse(kwargs['shell'])
                    self.assertEqual(kwargs['stdin'], M.subprocess.DEVNULL)
                    self.assertEqual(kwargs['stdout'], M.subprocess.DEVNULL)
                    self.assertEqual(kwargs['stderr'], M.subprocess.DEVNULL)
                    self.assertLessEqual(set(kwargs['env']), {'SystemRoot', 'WINDIR'})
                    stamp = str(int((10000 + 11644473600) * 10000000))
                    if fault != 'missing_start':
                        append('START', {'pid': 555, 'parent_pid': M.os.getpid(), 'name': Path(M.sys.executable).name, 'event_filetime': stamp})
                    if fault != 'missing_exit':
                        append('EXIT', {'pid': 555, 'name': Path(M.sys.executable).name, 'event_filetime': stamp})
                    def wait(timeout):
                        if fault == 'child_timeout':
                            raise M.subprocess.TimeoutExpired('LOCAL_FIXTURE', timeout)
                        return 0
                    return SimpleNamespace(pid=555, wait=wait, poll=lambda: 0)

                with patch.object(M, 'DIRECTORY', directory), patch.object(M, 'IS_WINDOWS', True), \
                        patch.object(M, 'require_normal_user'), patch.object(M, 'account_metadata', side_effect=sample), \
                        patch.object(M.time, 'monotonic', side_effect=lambda: clock.now), \
                        patch.object(M.time, 'time', return_value=10000), patch.object(M.time, 'sleep', side_effect=sleep), \
                        patch.object(M.subprocess, 'Popen', side_effect=launch) as popen:
                    result = M.observe(directory)
                self.assertEqual(result['claude_invocations'], 0)
                self.assertFalse(result['N1_admission'])
                self.assertEqual(result['account_identity'], 'UNKNOWN')
                self.assertTrue((directory / 'reader.claim').exists())
                self.assertTrue((directory / 'stop.request').exists())
                self.assertEqual(json.loads((directory / 'receipt.json').read_bytes()), result)
                self.assertEqual(result['metadata_log_sha256'], M.sha((directory / 'metadata-samples.jsonl').read_bytes()))
                self.assertEqual(result['metadata_samples'], len((directory / 'metadata-samples.jsonl').read_bytes().splitlines()))
                if fault is None:
                    self.assertEqual(result['status'], 'LOCAL_OBSERVER_PREPARATION_COMPLETE_NOT_AUTH_OR_N1')
                    self.assertGreaterEqual(result['observed_wall_seconds'], 120)
                    self.assertTrue(result['sentinel_start_exit_parent_observed'])
                    self.assertEqual(popen.call_count, 1)
                else:
                    self.assertEqual(result['status'], 'STOP')

    def test_elevated_reader_refuses_before_claim_or_launch(self):
        with patch.object(M, 'IS_WINDOWS', True), patch.object(M, 'require_normal_user', side_effect=M.Refused('administrator')), \
                patch.object(M, 'exclusive') as create, patch.object(M.subprocess, 'Popen') as popen:
            with self.assertRaises(M.Refused):
                M.observe()
        create.assert_not_called(); popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
