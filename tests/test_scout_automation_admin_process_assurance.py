"""Research OS pipeline V001: Codex administrative commands through the real bounded capture, with fixed local Python
children standing in for the Codex CLI. No CLI, model, network, credential or account inspection. Separate from
v004_checks, whose process guard intentionally refuses Popen. Each child floods, hangs or prints one fixed fixture
answer, and gives up by itself after 30 seconds."""
import time
import unittest
from unittest.mock import patch

from src.research.opportunity_scout.automation_v001 import providers as V
from src.research.opportunity_scout.exploratory_v001 import runner as X
from tests.opportunity_scout.test_research_pipeline_v001 import Base
from tests.test_scout_exploratory_capture_process_assurance import HANG, child

# Alternates stdout and stderr, so neither channel alone reaches the administrative bound but together they pass it.
BOTH = ('import sys,time\nend=time.time()+30\nwhile time.time()<end:\n'
        ' for s in (sys.stdout,sys.stderr):s.buffer.write(b"x"*65536);s.buffer.flush()')


class CodexAdminProcessTests(Base):
    """The whole pipeline run; only the first Codex administrative command is replaced by a local child."""
    def run_admin_child(self, body):
        self.heartbeat, self.sinks = self.base / 'admin.beat', []
        def runner(args, **kwargs):
            if '--json' in args:return self.fake_codex(args, **kwargs)  # never reached: the preflight stops first
            self.sinks.append(kwargs)  # the child environment is replaced only so a bare local Python can start
            return X.capture(child(body, self.heartbeat), **{**kwargs, 'env': None})
        self.pipe.codex_runner = runner
        started = time.monotonic()
        self.execute()
        self.elapsed = time.monotonic() - started
        [record] = self.preflights()  # one Codex executable, so exactly one preflight record
        return record

    def assert_stopped_before_any_critic_process(self, stop):
        rep = self.report()
        for idea in self.ideas():self.assertEqual(self.critic(rep, idea, 'SCIENTIFIC')['faults'], ['PREFLIGHT_STOP:' + stop])
        self.assertEqual((len(self.sinks), self.codex_calls), (1, []))
        before = self.heartbeat.stat().st_size; time.sleep(0.3)
        self.assertEqual(self.heartbeat.stat().st_size, before, 'a descendant survived the stop')

    def test_combined_stdout_and_stderr_flood_stops_the_tree_during_capture(self):
        rec = self.run_admin_child(BOTH)
        self.assertEqual((rec['stop'], rec['administrative_launches'], rec['processes_started']),
                         ('ADMIN_OUTPUT_TOO_LARGE:--version:PROCESS_TREE_STOPPED', 1, 1))
        self.assertLess(self.elapsed, 25)
        out, err = (len(self.sinks[0][c].getvalue()) for c in ('stdout', 'stderr'))
        self.assertEqual(self.sinks[0]['limit'], X.MAX_ADMIN_BYTES)
        self.assertGreater(out + err, X.MAX_ADMIN_BYTES); self.assertLessEqual(out + err, X.MAX_ADMIN_BYTES + 2 * X.CHUNK)
        self.assertTrue(0 < out < X.MAX_ADMIN_BYTES and 0 < err < X.MAX_ADMIN_BYTES)  # the bound is combined, not per channel
        self.assert_stopped_before_any_critic_process(rec['stop'])

    def test_real_pipes_carry_a_stderr_login_result_through_the_preflight(self):
        """Real children answer as codex 0.164 does: version and help on stdout, the login result on stderr only."""
        answers = {'--version': 'import sys;sys.stdout.write("codex-cli 0.164.0-fixture\\n")',
                   'login': 'import sys;sys.stderr.write("Logged in using ChatGPT\\n")',
                   'exec': 'import sys;sys.stdout.write(sys.argv[1])'}
        def runner(args, **kwargs):
            if '--json' in args:return self.fake_codex(args, **kwargs)
            command = child(answers[args[1]]) + ([' '.join(V.CODEX_FLAGS)] if args[1] == 'exec' else [])
            return X.capture(command, **{**kwargs, 'env': None})
        self.pipe.codex_runner = runner
        self.execute()
        [record] = self.preflights()
        self.assertEqual((record['auth'], record['cli_version'], record['administrative_launches'], record['processes_started']),
                         ('CHATGPT_LOGIN', 'codex-cli 0.164.0-fixture', 3, 3))
        self.assertEqual(len(self.codex_calls), 2)  # both scientific critics dispatched after the real-pipe preflight

    def test_hung_command_is_stopped_at_the_administrative_timeout(self):
        with patch.object(X, 'ADMIN_TIMEOUT', 1):rec = self.run_admin_child(HANG)
        self.assertEqual((rec['stop'], rec['administrative_launches'], rec['processes_started']),
                         ('ADMIN_TIMEOUT:--version:PROCESS_TREE_STOPPED', 1, 1))
        self.assertEqual(self.sinks[0]['timeout'], 1)
        self.assert_stopped_before_any_critic_process(rec['stop'])


if __name__ == '__main__':
    unittest.main()
