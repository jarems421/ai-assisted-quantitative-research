"""Research OS operator V001: links left inside run directories, on SYNTHETIC fixtures only.

Run by the public runner, which permits creating a junction (Windows) or symlink (POSIX) inside a temporary
directory; the restricted offline runner denies link creation itself. No network, process, model or human judgment."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.research.opportunity_scout.automation_v001 import execution as X
from src.research.operator import cli, demo, runs
from src.research.operator.guard import Boundary, BoundaryViolation, resolved
from src.research.operator.journal import Journal

REVISION = {'commit': 'UNKNOWN', 'ref': 'UNKNOWN', 'basis': 'TEST_FIXTURE', 'reason': 'git metadata is not read in tests'}


def link(path, target):
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(target), str(path))  # no symlink privilege needed
    else:
        os.symlink(target, path, target_is_directory=True)


class LinkTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.f = demo.fixtures(self.root)
        self.outside = self.root / 'outside'; self.outside.mkdir()
        p = patch.object(X, 'revision', return_value=REVISION); p.start(); self.addCleanup(p.stop)

    def create(self, run_id):
        return runs.create(runs.request_value(self.f['archive'], self.f['ready_idea'], None, None, [], None), base=self.f['base'], run_id=run_id)

    def test_preexisting_link_in_a_run_directory_stops_before_custody(self):
        layout = self.create('OPR-LINK-BEFORE')
        link(layout.artifacts, self.outside)
        rep, _ = runs.invoke(layout, 'run')
        s = runs.current_stages(Journal(layout.run).load())
        self.assertEqual(s['PREFLIGHT']['status'], 'FAILED')
        self.assertIn('links in the run directories are refused', s['PREFLIGHT']['software_findings'][0])
        self.assertEqual(s['FORGE_CUSTODY']['status'], 'SKIPPED')
        self.assertFalse(layout.scout.exists())
        self.assertEqual(list(self.outside.iterdir()), [])
        self.assertEqual((rep['outcome'], rep['first_boundary']['stage']), ('FAILED', 'PREFLIGHT'))

    def test_link_added_after_a_run_blocks_continue_and_writes_nothing_through_it(self):
        layout = self.create('OPR-LINK-AFTER')
        runs.invoke(layout, 'run')
        link(layout.artifacts / 'escape', self.outside)
        rep, _ = runs.invoke(layout, 'continue')
        s = runs.current_stages(Journal(layout.run).load())
        self.assertEqual(s['PREFLIGHT']['status'], 'FAILED')
        self.assertEqual({s[n]['status'] for n in ('FORGE_CUSTODY', 'FORGE_RECORDS', 'ANVIL_DRAFTS')}, {'SKIPPED'})
        self.assertEqual(s['INTEGRITY']['status'], 'COMPLETE')
        self.assertEqual(list(self.outside.iterdir()), [])
        self.assertEqual(cli.status(layout)['outcome'], 'FAILED')

    def test_boundary_resolves_links_before_allowing_a_write(self):
        run = self.root / 'run'; run.mkdir()
        link(run / 'link', self.outside)
        b = Boundary(); b.roots = (resolved(run),); b.active = True
        b.audit('open', (str(run / 'real.json'), 'xb', os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        for event, args in (('open', (str(run / 'link' / 'x.json'), 'xb', os.O_CREAT | os.O_EXCL | os.O_WRONLY)),
                            ('os.mkdir', (str(run / 'link' / 'sub'), 0o777, None))):
            with self.assertRaises(BoundaryViolation, msg=event):
                b.audit(event, args)
        b.active = False
        self.assertEqual(list(self.outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
