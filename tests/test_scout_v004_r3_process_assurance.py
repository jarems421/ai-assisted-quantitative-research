"""R3 journal locks exercised by local Python children, never Claude.

Reuse the adversarial process scenarios so both versioned journals retain the
same lock/kill/race contract. All paths and child inputs are fictional temp data.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

from src.research.opportunity_scout.v004_r3 import package as P, runtime as R, replay as J
from tests import test_scout_v004_process_assurance as original
from tests.opportunity_scout import v004_fixtures as F

WORKER = original.WORKER.replace(
    'from src.research.opportunity_scout import v004_replay as J,schema as S',
    'from src.research.opportunity_scout import schema as S\n'
    'from src.research.opportunity_scout.v004_r3 import replay as J')
# A silent no-op substitution would re-test only the R2 journal.
assert 'v004_r3 import replay as J' in WORKER and 'v004_replay as J' not in WORKER


class R3CrossProcessAssuranceTests(original.CrossProcessAssuranceTests):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.package = self.base / 'package'
        P.build(self.package, F.blueprints(), R.description(F.MODEL, 'a' * 64, 'FICTIONAL-2.1.302'), mode='SYNTHETIC')
        self.run = J.OfflineRun.create(self.base / 'run', self.package)

    def worker(self, action):
        child = subprocess.Popen([sys.executable, '-u', '-c', WORKER, action, str(self.run.root)],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.stop, child)
        return child
