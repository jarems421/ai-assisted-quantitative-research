"""Real local Python-process lock tests. No CLI/provider or account inspection.

Separate from v004_checks, whose process guard intentionally refuses Popen.
Every child receives only a temporary fictional journal and runs fixed code.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from src.research.sec_pilot.parsing import offline
from src.research.opportunity_scout import schema as S, v004_package as P, v004_replay as J
from tests.opportunity_scout import v004_fixtures as F

WORKER = '''
import json,sys
from pathlib import Path
from src.research.sec_pilot.parsing import offline
from src.research.opportunity_scout import v004_replay as J,schema as S
with offline():
 root=Path(sys.argv[2])
 if sys.argv[1]=='hold':
  with J.locked(root):
   (root.parent/'worker-ready').write_text('locked')
   sys.stdin.buffer.read(1)
 else:
  try:
   J.OfflineRun(root).start()
   print(json.dumps({'started':True}))
  except S.ScoutError:
   print(json.dumps({'started':False}))
'''


class CrossProcessAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name); self.package=self.base/'package'
        P.build(self.package,F.blueprints(),F.runtime(),mode='SYNTHETIC')
        self.run=J.OfflineRun.create(self.base/'run',self.package)

    def worker(self,action):
        child=subprocess.Popen([sys.executable,'-u','-c',WORKER,action,str(self.run.root)],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(self.stop,child)
        return child

    def stop(self,child):
        if child.poll() is None: child.kill()
        child.communicate(timeout=15)

    def holder(self):
        child=self.worker('hold'); deadline=time.monotonic()+15
        while not (self.base/'worker-ready').exists():
            if child.poll() is not None or time.monotonic()>deadline: self.fail('local lock worker failed to become ready')
            time.sleep(.025)
        return child

    def attempt(self,child):
        out,err=child.communicate(timeout=15)
        self.assertEqual(child.returncode,0,err.decode('utf-8'))
        return json.loads(out)['started']

    def test_other_process_cannot_enter_held_lock_then_release_allows_one_slot(self):
        with offline():
            holder=self.holder(); self.assertFalse(self.attempt(self.worker('start')))
            self.assertEqual(self.run.status()['consumed_attempts'],0)
            holder.communicate(input=b'x',timeout=15); self.assertEqual(holder.returncode,0)
            self.assertTrue(self.attempt(self.worker('start')))
            self.assertEqual(self.run.status()['consumed_attempts'],1)

    def test_killed_holder_leaves_stale_lock_and_no_auto_recovery(self):
        with offline():
            holder=self.holder(); holder.kill(); holder.communicate(timeout=15)
            self.assertTrue((self.run.root/'.lock').exists())
            self.assertFalse(self.attempt(self.worker('start')))
            with self.assertRaises(S.ScoutError): self.run.start()

    def test_competing_processes_cannot_consume_two_slots(self):
        with offline():
            first,second=self.worker('start'),self.worker('start')
            self.assertEqual(sum((self.attempt(first),self.attempt(second))),1)
            status=self.run.status(); self.assertEqual(status['consumed_attempts'],1)
            self.assertTrue(status['pending_requires_owner_review'])


if __name__=='__main__': unittest.main()
