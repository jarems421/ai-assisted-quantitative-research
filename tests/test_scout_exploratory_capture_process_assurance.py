"""Bounded capture of the exploratory runner V001 with real local Python children. No CLI, model, network,
credential or account inspection. Separate from v004_checks, whose process guard intentionally refuses Popen.
Every child runs fixed code, floods or hangs, and gives up by itself after 30 seconds."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from src.research.opportunity_scout import schema as S
from src.research.opportunity_scout.exploratory_v001 import runner as X
from tests.opportunity_scout.test_exploratory_runner_v001 import Base, FakeCLI

# Real local Python children (no CLI, model, network or account): each floods or hangs; a grandchild heartbeats
# into a file so a surviving descendant is visible. Every child gives up by itself after 30 seconds.
HEARTBEAT = 'import sys,time\nend=time.time()+30\nwhile time.time()<end:\n open(sys.argv[1],"ab").write(b".");time.sleep(0.02)'
def child(body, heartbeat=None):
    spawn = ('import os,subprocess,sys,time\n'
             f'subprocess.Popen([sys.executable,"-I","-c",{HEARTBEAT!r},{str(heartbeat)!r}])\n'
             f'end=time.time()+30\nwhile not os.path.exists({str(heartbeat)!r}) and time.time()<end:time.sleep(0.01)\n') if heartbeat else ''
    return [sys.executable, '-I', '-c', spawn + body]
FLOOD = 'import sys,time\nend=time.time()+30\nwhile time.time()<end:sys.{}.buffer.write(b"x"*65536)'
HANG = 'import time\ntime.sleep(30)'


class BoundedCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.dir = Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def sinks(self):return io.BytesIO(), io.BytesIO()

    def assert_descendant_stopped(self, heartbeat):
        before = heartbeat.stat().st_size; time.sleep(0.3)
        self.assertEqual(heartbeat.stat().st_size, before, 'a descendant survived the stop')

    def test_normal_output_and_input_are_captured_exactly(self):
        out, err = self.sinks()
        script = 'import sys\nd=sys.stdin.buffer.read()\nsys.stdout.buffer.write(d[::-1]);sys.stderr.buffer.write(b"e");sys.exit(3)'
        p = X.capture(child(script), stdout=out, stderr=err, limit=1024, timeout=30, input=b'abc')
        self.assertEqual((p.returncode, out.getvalue(), err.getvalue()), (3, b'cba', b'e'))

    def test_flood_stops_the_process_tree_and_keeps_a_bounded_prefix(self):
        for channel in ('stdout', 'stderr'):  # the bound is combined: stderr alone also trips it
            with self.subTest(channel=channel):
                out, err = self.sinks(); heartbeat = self.dir / f'{channel}.beat'; started = time.monotonic()
                with self.assertRaises(X.OutputLimitExceeded) as caught:
                    X.capture(child(FLOOD.format(channel), heartbeat), stdout=out, stderr=err, limit=X.MAX_ADMIN_BYTES, timeout=30)
                self.assertLess(time.monotonic() - started, 20)
                kept = len(out.getvalue()) + len(err.getvalue())
                self.assertEqual(caught.exception.captured, kept)
                self.assertGreater(kept, X.MAX_ADMIN_BYTES); self.assertLessEqual(kept, X.MAX_ADMIN_BYTES + 2 * X.CHUNK)
                self.assertEqual(caught.exception.tree, 'PROCESS_TREE_STOPPED')
                self.assert_descendant_stopped(heartbeat)

    def test_timeout_also_stops_the_process_tree(self):
        out, err = self.sinks(); heartbeat = self.dir / 'hang.beat'
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            X.capture(child(HANG, heartbeat), stdout=out, stderr=err, limit=1024, timeout=1)
        self.assertEqual(caught.exception.tree, 'PROCESS_TREE_STOPPED')
        self.assert_descendant_stopped(heartbeat)


class OutputLimitRunTests(Base):
    """The runner with the real bounded capture: a local flooding child stands in for one CLI command."""
    def run_with(self, flood_when, parse_allowed=False):
        fake = FakeCLI(self); seen = []
        def runner(args, **kwargs):
            seen.append(list(args))
            if flood_when(args, seen):  # the child environment is replaced only so a bare local Python can start
                fake.calls.append((list(args), kwargs))
                return X.capture(child(FLOOD.format('stdout')), **{**kwargs, 'env': None})
            return fake(args, **kwargs)
        result = self.planned(); self.host.runner = runner
        with patch.object(X, 'review', side_effect=None if parse_allowed else AssertionError('an oversized stream must never be parsed'),
                          wraps=X.review if parse_allowed else None) as parse:
            receipt = X.run(self.store, self.authorise(result), host=self.host)
        return receipt, fake, parse

    def test_model_stream_limit_stops_during_capture_and_preserves_raw_bytes(self):
        receipt, cli, parse = self.run_with(lambda args, seen: '--print' in args)
        self.assertEqual((receipt['status'], receipt['error']), ('ERROR', 'RUN_STOP:RECORDING_SIZE_LIMIT:PROCESS_TREE_STOPPED'))
        self.assertEqual((receipt['model_invocations'], receipt['administrative_commands_run'], receipt['retried'], receipt['cards']), (1, 3, False, []))
        parse.assert_not_called()
        raw = self.store / 'exports/exploratory-ATT-0001-stdout.bin'
        size = raw.stat().st_size
        self.assertGreater(size, X.MAX_STREAM_BYTES); self.assertLessEqual(size, X.MAX_STREAM_BYTES + 2 * X.CHUNK)
        self.assertEqual((receipt['stdout_bytes'], receipt['stdout_sha256']), (size, hashlib.sha256(raw.read_bytes()).hexdigest()))
        state = self.state()
        self.assertEqual((state.attempts['ATT-0001']['result']['status'], len(state.cards), state.efforts[-1]['invocation_status']), ('ERROR', 0, 'UNKNOWN'))
        self.assertEqual((receipt['process_start'], receipt['provider_request']), ('STARTED', 'UNKNOWN'))  # unparsed: provider reach unknown
        st = X.status(self.store); self.assertEqual((st['claimed'], st['receipt'], st['interrupted']), (True, True, False))
        auth = sorted(self.base.glob('authorisation-*.json'))[-1]
        with self.assertRaises(S.ScoutError):X.run(self.store, auth, host=self.host)  # consumed: never retried
        self.assertEqual(cli.kinds().count('MODEL'), 1)

    def test_administrative_limit_stops_preflight_before_the_model(self):
        receipt, cli, _ = self.run_with(lambda args, seen: args[1:] == ['--help'])
        self.assertEqual((receipt['status'], receipt['error']), ('ERROR', 'PREFLIGHT_STOP:ADMIN_OUTPUT_TOO_LARGE:--help:PROCESS_TREE_STOPPED'))
        self.assertEqual((receipt['model_invocations'], receipt['administrative_commands_run']), (0, 2))
        self.assertNotIn('MODEL', cli.kinds())
        self.assertFalse((self.store / 'exports/exploratory-ATT-0001-stdout.bin').exists())
        self.assertEqual(self.state().efforts[-1]['invocation_status'], 'NOT_INVOKED')

    def test_postflight_auth_status_limit_is_named_and_closes_without_cards(self):
        def second_auth(args, seen):return args[1:] == ['auth', 'status', '--json'] and sum(a[1:] == args[1:] for a in seen) == 2
        receipt, cli, _ = self.run_with(second_auth, parse_allowed=True)  # the model stream itself is normal
        self.assertEqual(receipt['status'], 'ERROR'); self.assertEqual(self.state().cards, {})
        self.assertIn('POSTFLIGHT_ADMIN_OUTPUT_TOO_LARGE:auth:PROCESS_TREE_STOPPED', receipt['error'])
        self.assertEqual((receipt['model_invocations'], receipt['administrative_commands_run']), (1, 4))
        self.assertNotIn('xxxx', json.dumps(receipt))  # raw administrative output is never stored
