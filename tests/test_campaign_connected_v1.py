"""Connected fictional chain only. Native components, fake transport and denied external effects."""
from contextlib import contextmanager, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.campaign_connected_v1 import lineage as L, fixtures as F, rehearsal as D
from src.research.campaign_connected_v1.__main__ import main
from src.research.campaign_v1 import campaign as C, records as R
from src.research.discovery.ledger import Ledger
from src.research.operator import adapters, runs
from src.research.operator.journal import Journal
from src.research.operator.guard import offline
from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout.automation_v001 import execution as X
from src.research.quarry_v1 import evidence as Q
from src.research.source_v1 import retrieve as SR


def denied(*args, **kwargs):
    raise AssertionError('synthetic chain attempted real network/process/model transport')


@contextmanager
def altered(path, content):
    original = path.read_bytes()
    try:
        if content is None:
            path.unlink()
        else:
            path.write_bytes(content)
        yield
    finally:
        path.write_bytes(original)


# Before PR #46 merges, main has no custody implementation. This is a visible
# dependency skip, never end-to-end evidence. Combined-main CI must run every test.
@unittest.skipUnless(importlib.util.find_spec('src.research.source_custody_v1'), 'native custody PR #46 not integrated')
class ConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for target in ('socket.getaddrinfo', 'socket.create_connection', 'subprocess.Popen',
                       'src.research.source_v1.transport.HttpsTransport.open'):
            p = patch(target, side_effect=denied); p.start(); cls.addClassCleanup(p.stop)
        p = patch.object(X, 'revision', return_value={'commit': 'UNKNOWN', 'ref': 'UNKNOWN', 'basis': 'TEST_FIXTURE',
                                                     'reason': 'git metadata is not read in tests'})
        p.start(); cls.addClassCleanup(p.stop)
        tmp = tempfile.TemporaryDirectory(); cls.addClassCleanup(tmp.cleanup)
        cls.root = Path(tmp.name)
        cls.out = cls.root / 'connected'
        buf = io.StringIO()
        with redirect_stdout(buf):
            if main(['rehearse', '--out', str(cls.out)]) != 0:
                raise AssertionError(buf.getvalue())
        cls.summary = json.loads(buf.getvalue())
        cls.report = L.verify(cls.out / 'connected-checkpoint')
        cls.selection = cls.report['selection']

    def test_one_command_native_chain_keeps_same_original_and_human_blockers(self):
        report = self.report
        self.assertEqual(self.summary['external_requests'], 0)
        self.assertEqual((self.summary['model_calls'], self.summary['fake_transport_requests']), (0, 2))
        self.assertEqual(self.summary['anvil_status'], 'BLOCKED')
        self.assertEqual((self.out / 'custody' / 'original.bin').read_bytes(), F.TEXT)
        self.assertEqual(report['receipt']['body_sha256'], L.N.sha(F.TEXT))
        ref = report['source_reference']
        native_registry = Path(ref['source_base']) / 'source-v1' / 'attempts' / ref['attempt_id'] / 'inputs' / 'quarry-registry.json'
        self.assertEqual(report['native_registry_sha256'], L.N.sha(native_registry.read_bytes()))
        self.assertNotEqual(native_registry.read_bytes(), (self.out / 'custody' / 'registry.json').read_bytes())
        self.assertEqual(json.loads(native_registry.read_bytes()), json.loads((self.out / 'custody' / 'registry.json').read_bytes()))
        self.assertEqual(report['receipt']['coverage'], 'COMPLETE')
        self.assertEqual(report['source_consumption']['requests'], {'at_least': 2, 'exact': 2})
        self.assertEqual(report['publication_authenticity'], 'UNKNOWN')
        self.assertEqual(report['dataset_completeness'], 'UNKNOWN')
        self.assertEqual(report['scientific_meaning'], 'NOT_ESTABLISHED')
        self.assertIsNone(report['research_outcome'])
        native = report['native_anvil_checkpoint']
        self.assertEqual(native['stages']['JEV_EVIDENCE']['summary']['queue'][0]['id'], 'SYN_ALLOCATION')
        self.assertEqual(native['discovery']['fixture'], 'SYNTHETIC')
        self.assertFalse(native['discovery']['software_certifies_M'])
        self.assertTrue(all(r['human_judgment'] == 'NOT_REVIEWED' for r in native['discovery']['requirements'].values()))
        state = Ledger(native['stages']['ANVIL_CHECKS']['summary']['ledger']).load()
        passport = state.latest('source', adapters.source_id('SYN-REGISTER'))
        pointers = [e for q in passport['quantities'] for e in q['evidence']]
        self.assertTrue(pointers)
        for evidence in pointers:
            self.assertEqual((evidence['sha256'], evidence['archive'], evidence['depth']),
                             (report['receipt']['body_sha256'], 'quarry-export-manifest:' + report['quarry_export_manifest']['sha256'],
                              'UNVERIFIED'))
        self.assertIn('independent invoice totals', report['missing_fields'])
        self.assertEqual(report['authorises'], [])

    def test_read_only_reconstruction_seal_and_no_native_replay(self):
        before = {p: p.read_bytes() for p in self.out.rglob('*') if p.is_file()}
        with patch.object(SR, 'run', side_effect=denied), patch.object(runs, 'invoke', side_effect=denied), \
                patch.object(L.custody_api(), 'import_receipt', side_effect=denied):
            self.assertEqual(L.verify(self.out / 'connected-checkpoint'), self.report)
            stream = io.StringIO()
            with redirect_stdout(stream):
                self.assertEqual(main(['verify', str(self.out / 'connected-checkpoint')]), 0)
            self.assertEqual(json.loads(stream.getvalue()), self.report)
        self.assertEqual(before, {p: p.read_bytes() for p in self.out.rglob('*') if p.is_file()})
        with self.assertRaisesRegex(ValueError, 'never overwrite'):
            L.seal(self.selection, self.out / 'connected-checkpoint')

    def test_mismatched_source_campaign_branch_and_card_identity_refused(self):
        for changes in ({'url': 'https://documents.example.org/never-retrieved'}, {'branch': 'OTHER'},
                        {'source_activity': 'OTHER'}, {'operator_activity': 'OTHER'}):
            with self.subTest(changes), self.assertRaises((ValueError, KeyError, StopIteration)):
                L.inspect({**self.selection, **changes})
        bad = self.out / 'export' / 'input.json'
        data = json.loads(bad.read_bytes()); data['subject']['version'] += 1
        with altered(bad, R.canonical(data)), self.assertRaises(ValueError):
            L.inspect(self.selection)
        ref = self.report['source_reference']
        request = Path(ref['source_base']) / 'source-v1' / 'attempts' / ref['attempt_id'] / 'request.json'
        data = json.loads(request.read_bytes()); data['subject']['card_sha256'] = 'f' * 64
        with altered(request, R.canonical(data)), self.assertRaises(ValueError):
            L.inspect(self.selection)

    def test_missing_completion_is_not_reconstructed_from_sealed_package(self):
        completion = Path(self.report['custody']['completion']['path'])
        with altered(completion, None), self.assertRaisesRegex(ValueError, 'NATIVE_CUSTODY_COMPLETION_REQUIRED'):
            L.inspect(self.selection)
        self.assertEqual(L.verify(self.out / 'connected-checkpoint'), self.report)

    def test_changed_package_export_completion_and_checkpoint_are_refused(self):
        targets = [self.out / 'custody' / 'original.bin', self.out / 'export' / 'source' / 'original.bin',
                   Path(self.report['custody']['completion']['path']), self.out / 'connected-checkpoint' / 'checkpoint.json']
        for path in targets:
            with self.subTest(path=path.name), altered(path, path.read_bytes() + b'changed'), self.assertRaises(ValueError):
                L.verify(self.out / 'connected-checkpoint')

    def test_another_valid_export_cannot_replace_native_operator_input(self):
        target = self.root / 'another-valid-export'
        with offline([self.root]):
            Q.export(self.out / 'custody', self.out / 'inputs' / 'synthetic-inspection.json',
                     self.out / 'inputs' / 'subject.json', target)
        with self.assertRaisesRegex(ValueError, 'operator did not consume'):
            L.inspect({**self.selection, 'export': str(target)})

    def test_incomplete_retrieval_does_not_produce_connected_checkpoint(self):
        original = F.FakeTransport.open
        def unframed(fake, url, host, address, timeout):
            response = original(fake, url, host, address, timeout)
            if url == F.URL:
                response.headers = [('Content-Type', 'text/plain')]
            return response
        out = self.root / 'unframed'
        with patch.object(F.FakeTransport, 'open', unframed), self.assertRaisesRegex(ValueError, 'did not complete exactly'):
            D.rehearse(out)
        self.assertFalse((out / 'connected-checkpoint').exists())
        self.assertFalse((out / 'custody').exists())

    def test_changed_code_and_native_reference_require_reconciliation(self):
        with patch.object(L, 'implementation', return_value={'changed': True}), self.assertRaisesRegex(ValueError, 'chain/code changed'):
            L.verify(self.out / 'connected-checkpoint')
        campaign = C.Campaign(self.selection['campaign'])
        # An exact duplicate attachment cannot dispatch/replay or change the checkpoint.
        with patch.object(runs, 'invoke', side_effect=denied):
            self.assertFalse(campaign.attach('B0', 'OPERATOR-0', self.report['operator_reference']['run']))
        self.assertEqual(L.verify(self.out / 'connected-checkpoint'), self.report)

    def test_stale_native_completion_is_observed_without_replaying_one_shots(self):
        out = self.root / 'stale-native'
        D.rehearse(out)
        saved = L.verify(out / 'connected-checkpoint')
        old = saved['operator_reference']
        layout = runs.Layout(Path(old['run']).parent.parent, old['run_id'])
        claims_before = [e for e in Journal(layout.run).load() if e['type'] == 'STAGE_STARTED' and e['record']['kind'] == 'ONE_SHOT']
        # Only this explicit fixture continuation executes CHECK stages. Verification
        # below must refuse the stale reference, rather than execute or silently advance it.
        runs.invoke(layout, 'continue')
        self.assertEqual(claims_before, [e for e in Journal(layout.run).load()
                                        if e['type'] == 'STAGE_STARTED' and e['record']['kind'] == 'ONE_SHOT'])
        with patch.object(runs, 'invoke', side_effect=denied), self.assertRaises(ValueError):
            L.verify(out / 'connected-checkpoint')
        C.Campaign(saved['selection']['campaign']).reconcile('B0')
        with patch.object(runs, 'invoke', side_effect=denied), patch.object(SR, 'run', side_effect=denied):
            fresh = L.seal(saved['selection'], out / 'new-observation')
        self.assertNotEqual(fresh['operator_reference']['journal_head'], old['journal_head'])
        self.assertIsNone(fresh['research_outcome'])

    def test_unready_card_cannot_gain_anvil_candidate_from_completed_retrieval(self):
        campaign = C.Campaign(self.selection['campaign'])
        archive = Archive(self.report['hypothesis']['archive'])
        card = next(v[-1] for v in archive.load().cards.values() if v[-1]['lane'] == 'RADAR')
        campaign.add_branch('B1', archive.path, card['id'], card['version'], R.digest(card))
        with offline([self.root]):
            subject = F.put(self.root, 'unready-subject.json', adapters.subject(card)[0])['path']
            export = self.root / 'unready-export'
            Q.export(self.out / 'custody', self.out / 'inputs' / 'synthetic-inspection.json', subject, export)
            spec = runs.evidence_spec({'schema': 'RESEARCH_OS_OPERATOR_EVIDENCE_V001', 'routes': [],
                                      'exports': [{'label': 'SYN', 'path': str(export)}]}, self.root)
        layout = runs.create(runs.request_value(archive.path, card['id'], None, spec, [], None),
                             base=self.root / 'unready-workspace', run_id='OPR-SYNTHETIC-UNREADY')
        runs.invoke(layout, 'run')
        campaign.attach('B1', 'UNREADY-OPERATOR', layout.run)
        branch = campaign.status()['branches'][1]
        view = L.operator_view(branch['activities'][0], campaign.load()[2]['B1'])
        self.assertEqual(view['stages']['FORGE_READINESS']['status'], 'WAITING_FOR_HUMAN')
        self.assertEqual(view['stages']['ANVIL_DRAFTS']['summary']['candidate']['status'], 'NOT_DRAFTED')
        self.assertIsNone(view['discovery'])
        self.assertEqual(view['stages']['JEV_EVIDENCE']['status'], 'COMPLETE')
        # Source reference belongs to B0; a completed export does not retarget it.
        with self.assertRaisesRegex(ValueError, 'another branch'):
            L.inspect({**self.selection, 'branch': 'B1', 'operator_activity': 'UNREADY-OPERATOR'})
