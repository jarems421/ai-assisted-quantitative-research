"""LOCAL ONLY: the real archived Forge Pilot 001 Hypothesis B through the operator, on a verified working copy.

Set RESEARCH_OS_PILOT001_ARCHIVE to the original forge-live-pilot-001 directory (its critic workspace is found beside
it). The original is never a command target; the run lives in a temporary directory outside any checkout, and the
test asserts every original byte is unchanged. Without the private archive the whole module skips, so it is
excluded from CI. Nothing here calls a model, opens a network connection or records a human judgment."""
import os
from pathlib import Path
import tempfile
import unittest

from src.research.spec import canonical
from src.research.operator import report as RP, runs
from src.research.operator.journal import Journal

ARCHIVE = os.environ.get('RESEARCH_OS_PILOT001_ARCHIVE')
IDEA, HEAD = 'IDEA-4ccd3d91f9c3', '177addf19d0714039a4fab73b5f1eb8b9d7f15629c7fb5d1536ea91d3dca9257'
REFUSAL = 'Opportunity Scout: handoff needs an explicit human READY review approving this exact version'


@unittest.skipUnless(ARCHIVE and Path(ARCHIVE).is_dir(), 'private Forge Pilot 001 archive not supplied (RESEARCH_OS_PILOT001_ARCHIVE)')
class Pilot001HypothesisBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.archive = Path(ARCHIVE)
        cls.critic = cls.archive.parent / f'critic-v1-{cls.archive.name}'
        cls.before = (runs.tree(cls.archive), runs.tree(cls.critic))
        request = runs.request_value(cls.archive, IDEA, None, None, ['refrigerant'], None)
        cls.layout = runs.create(request, base=Path(cls.tmp.name) / 'workspace', run_id='OPR-PILOT001-TEST')
        cls.first, _ = runs.invoke(cls.layout, 'run')
        cls.keys = [e['record']['key'] for e in Journal(cls.layout.run).load() if e['type'] == 'STAGE_STARTED']
        cls.second, _ = runs.invoke(cls.layout, 'continue')
        cls.after = (runs.tree(cls.archive), runs.tree(cls.critic))
        cls.stages = runs.current_stages(Journal(cls.layout.run).load())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_g0_original_archive_and_critic_workspace_unchanged(self):
        self.assertEqual(self.before[0]['count'], 44)
        self.assertEqual([t['digest'] for t in self.before], [t['digest'] for t in self.after])
        self.assertTrue(self.stages['FORGE_CUSTODY']['summary']['byte_identical'])
        self.assertEqual(set(self.stages['INTEGRITY']['summary']['checks'].values()), {'UNCHANGED'})

    def test_f1_copy_validates_as_hypothesis_b_v1(self):
        r = self.stages['FORGE_RECORDS']['summary']
        self.assertEqual((r['archive']['events'], r['archive']['head']), (9, HEAD))
        h = r['hypothesis']
        self.assertEqual((h['idea_id'], h['version'], h['route'], h['lane']), (IDEA, 1, 'INCUBATE', 'FORGE'))
        self.assertEqual(r['fixture_class'], 'REAL')

    def test_f1_criticism_is_reported_without_an_economic_judgment(self):
        c = self.stages['FORGE_RECORDS']['summary']['criticism']
        self.assertEqual(c['requests']['SCIENTIFIC']['request_id'], 'CRQ-fcfc4a4722049d6e')
        self.assertEqual(c['requests']['SCIENTIFIC']['attempts'], ['VALID'])
        self.assertEqual(c['requests']['ECONOMIC']['request_id'], 'CRQ-952b880443c8b5c3')
        self.assertEqual((c['requests']['ECONOMIC']['attempts'], c['requests']['ECONOMIC']['pipeline_outcome']), ([], 'PROVIDER_FAULT'))
        self.assertEqual((c['recommendation']['classification'], c['recommendation']['rule']), ('ESCALATE', 'R2_INCOMPLETE_REVIEW'))

    def test_f1d_legacy_pipeline_receipt_is_never_verified(self):
        f = self.stages['FORGE_RECORDS']['summary']['pipeline']['finalisation']
        self.assertEqual((f['state'], f['consistent']), ('LEGACY_RECEIPT_UNBOUND', False))

    def test_f2_f3_v1_ready_refusal_is_preserved(self):
        r = self.stages['FORGE_READINESS']
        self.assertEqual(r['status'], 'WAITING_FOR_HUMAN')
        self.assertEqual(r['summary']['refusal'], REFUSAL)
        self.assertEqual([x['identifiable'] for x in r['summary']['routes']], [False])
        self.assertEqual(sorted(p.name for p in (self.layout.scout / 'exports').iterdir()), sorted(n[len('exports/'):] for n in self.before[0]['files'] if n.startswith('exports/')))
        self.assertEqual(self.stages['ANVIL_DRAFTS']['summary']['candidate']['status'], 'NOT_DRAFTED')
        self.assertEqual(self.stages['ANVIL_CHECKS']['status'], 'WAITING_FOR_HUMAN')

    def test_no_request_model_call_or_promotion(self):
        a = self.second['accounting']
        self.assertEqual((a['operator_model_or_provider_calls'], a['operator_network_requests'], a['boundary_denials']), (0, 0, 0))
        self.assertEqual(self.stages['DOWNSTREAM']['status'], 'NOT_AUTHORISED')
        self.assertEqual(self.second['authorises'], [])

    def test_r1_r2_armoury_retrieval(self):
        g = self.stages['ARMOURY_GRAPH']['summary']
        self.assertEqual(g['search']['refrigerant']['results'], 0)
        cap = g['same_gap']['REQ_AVAILABLE_CAPACITY']
        self.assertEqual(cap['connection_summary']['economic_connection_candidates'], 0)
        self.assertIn('history:HIST-EF03', cap['origins'])
        self.assertEqual(self.stages['JEV_MEMORY']['status'], 'COMPLETE')

    def test_meaningful_blocked_state_deterministic_report_and_no_replay(self):
        self.assertEqual(self.second['outcome'], 'STOPPED_AT_BOUNDARY')
        self.assertEqual(self.second['first_boundary']['stage'], 'FORGE_READINESS')
        self.assertEqual(self.stages['QUARRY_EVIDENCE']['status'], 'WAITING_FOR_EVIDENCE')
        events = Journal(self.layout.run).load()
        self.assertEqual(canonical(RP.render(events)), canonical(self.second))
        later = [e['record']['key'] for e in events if e['type'] == 'STAGE_STARTED'][len(self.keys):]
        self.assertTrue(all(k.startswith(('PREFLIGHT', 'INTEGRITY')) for k in later), later)


if __name__ == '__main__':
    unittest.main()
