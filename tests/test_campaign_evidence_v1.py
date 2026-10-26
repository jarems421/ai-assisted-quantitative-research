"""Fictional native source/operator records only. No acquisition, model or real human act."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.campaign_evidence_v1.continuity import Companion, observe_source
from src.research.campaign_evidence_v1.rehearsal import rehearse, refused_source
from src.research.campaign_evidence_v1.__main__ import main
from src.research.campaign_v1 import campaign as C, native as N, records as R
from src.research.operator import demo, runs
from src.research.operator.guard import offline, BOUNDARY, BoundaryViolation
from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout.automation_v001 import execution as X
from src.research.source_v1 import retrieve as SR, store as S
from tests import test_source_retrieval_v1 as SF
from tests.test_research_operator_v1 import REVISION, read_tree


class CampaignEvidenceTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.f = demo.fixtures(self.root / 'operator')
        p = patch.object(X, 'revision', return_value=REVISION); p.start(); self.addCleanup(p.stop)
        self.c = C.create(self.f['base'], 'CMP-EVIDENCE')
        self.ids = [self.f['ready_idea'], self.f['unreviewed_idea']]
        for i, idea in enumerate(self.ids):
            self.c.add_branch(f'B{i}', self.f['archive'], idea, 1, R.digest(Archive(self.f['archive']).load().latest(idea)))
        self.e = Companion(self.c.root).create()
        # Reuse the existing source suite's explicitly fictional scope/attestation
        # doubles and injected transport. No such human records exist in rehearsal.
        self.s = SF.SourceRetrievalTests('test_complete_attempt_retains_original_bytes_with_receipts_and_custody_handoff')
        self.s.setUp(); self.addCleanup(self.s.doCleanups)
        self.s.scope_changes = {'campaign_id': self.c.root.name, 'branch_id': 'B0',
                                'card_sha256': self.c.load()[2]['B0']['card_sha256']}
        self.s.build()

    def source(self, status='COMPLETE', attempt='A1', branch='B0', change=None):
        b = self.c.load()[2][branch]
        def bind(r):
            r['campaign_id'], r['branch_id'], r['request_id'] = self.c.root.name, branch, 'REQ-' + attempt
            r['subject'] = {'archive_sha256': N.sha(R.read(Path(b['archive']) / 'scout.jsonl')),
                            'card_id': b['idea_id'], 'card_version': b['version'], 'card_sha256': b['card_sha256']}
            if change: change(r)
        self.s.scope_changes.update(branch_id=branch, card_sha256=b['card_sha256'])
        if status == 'NOT_STARTED':
            self.s.scope_changes['valid_until'] = '2026-10-26T09:01:00+00:00'
        self.s.build()
        p = self.s.request(attempt, bind)
        values = {'COMPLETE': {}, 'PARTIAL': {SF.URL1: {'body': b'fictional partial', 'declared': False}},
                  'STOPPED': {SF.URL1: {'status': 403}}, 'UNAVAILABLE': {SF.URL1: {'status': 404}},
                  'UNKNOWN': {SF.URL1: {'body': b'prefix', 'fail_after': 0}},
                  'INTERRUPTED': {SF.URL1: {'body': b'prefix', 'interrupt_after': 0}}, 'NOT_STARTED': {}}
        transport = self.s.transport(values[status])
        with offline([self.s.root]):
            if status == 'INTERRUPTED':
                with self.assertRaises(KeyboardInterrupt):
                    self.s.dispatch(p, transport)
            else:
                result = self.s.dispatch(p, transport)
                self.assertEqual(result['status'], status)
        return self.s.attempt(attempt)

    def operator(self, idea=0, name='OPR-CHECKPOINT', evidence=False):
        layout = runs.create(runs.request_value(self.f['archive'], self.ids[idea], None, None, [], None),
                             base=self.f['base'], run_id=name)
        runs.invoke(layout, 'run')
        if evidence:
            spec = runs.evidence_spec(R.loads(R.read(self.f['evidence'])), Path(self.f['evidence']).parent)
            runs.invoke(layout, 'continue', supplied={'evidence': spec, 'search_terms': [], 'ledger': None})
        self.c.attach(f'B{idea}', name, layout.run)
        return layout

    def test_valid_native_reference_idempotent_and_campaign_bytes_unchanged(self):
        self.source()
        original = read_tree(self.c.root)
        with patch.object(SR, 'run', side_effect=AssertionError('no dispatch')), patch.object(runs, 'invoke', side_effect=AssertionError('no replay')):
            self.assertTrue(self.e.attach('B0', 'SOURCE-1', self.s.base, 'A1'))
            before = read_tree(self.e.root)
            self.assertFalse(self.e.attach('B0', 'SOURCE-1', self.s.base, 'A1'))
            rep = self.e.checkpoint()
        self.assertEqual(before, read_tree(self.e.root))
        self.assertEqual(original, read_tree(self.c.root))
        row = rep['branches'][0]['source_activities'][0]
        self.assertEqual(row['integrity'], 'VERIFIED_NATIVE_RESULT')
        self.assertEqual(row['status'], 'COMPLETE')
        self.assertEqual(row['custody'], 'AWAITING_NATIVE_QUARRY_CUSTODY')
        self.assertEqual(len(row['reference']['receipts']), 3)
        self.assertEqual(row['reference']['result_sha256'], S.sha(S.read(self.s.attempt() / 'result.json')))
        self.assertIsNone(rep['branches'][0]['research_outcome'])
        self.assertFalse(rep['budgets']['source_costs_aggregated'])

    def test_wrong_campaign_branch_card_version_and_archive_are_refused(self):
        for key, value in [('campaign_id', 'OTHER'), ('branch_id', 'B1'), ('card_version', 2),
                           ('card_sha256', 'f' * 64), ('archive_sha256', 'f' * 64)]:
            # Separate temporary native bases avoid reopening any stopped route.
            self.s.base = self.s.root / key
            def change(r):
                (r if key in ('campaign_id', 'branch_id') else r['subject'])[key] = value
            self.source('NOT_STARTED', change=change)
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.e.attach('B0', 'SOURCE-' + key, self.s.base, 'A1')
        self.assertEqual(len(self.e.load()[-1]), 0)

    def test_duplicate_attempt_and_activity_conflicts_refused(self):
        self.source(); self.e.attach('B0', 'S1', self.s.base, 'A1')
        with self.assertRaisesRegex(ValueError, 'already attached'):
            self.e.attach('B0', 'S2', self.s.base, 'A1')
        with self.assertRaises(ValueError):
            self.e.attach('B1', 'S1', self.s.base, 'A1')
        self.operator(name='OPR-SHARED-ID')
        with self.assertRaisesRegex(ValueError, 'identity conflict'):
            self.e.attach('B0', 'OPR-SHARED-ID', self.s.base, 'A1')

    def test_source_result_receipt_body_and_journal_tampering_isolated(self):
        self.source(); self.e.attach('B0', 'S1', self.s.base, 'A1')
        for rel in ['result.json', 'receipts/002.json', 'raw/002.body', 'journal.jsonl']:
            p = self.s.attempt() / rel; raw = p.read_bytes()
            try:
                p.write_bytes(raw + b'changed')
                rep = self.e.checkpoint()
                self.assertEqual(rep['branches'][0]['source_activities'][0]['integrity'], 'RECONCILIATION_REQUIRED')
                self.assertEqual(rep['branches'][1]['campaign_state']['execution_state'], 'WAITING_FOR_NATIVE_REFERENCE')
            finally:
                p.write_bytes(raw)

    def test_negative_and_uncertain_statuses_are_not_collapsed(self):
        for status in ('NOT_STARTED', 'STOPPED', 'UNAVAILABLE', 'PARTIAL', 'UNKNOWN'):
            self.s.base = self.s.root / status
            self.s.scope_changes.pop('valid_until', None)
            self.source(status, attempt=status)
            self.e.attach('B0', status, self.s.base, status)
        rows = self.e.checkpoint()['branches'][0]['source_activities']
        self.assertEqual({r['status'] for r in rows}, {'NOT_STARTED', 'STOPPED', 'UNAVAILABLE', 'PARTIAL', 'UNKNOWN'})
        self.assertTrue(all(r['integrity'] == 'VERIFIED_NATIVE_RESULT' for r in rows))

    def test_interrupted_attempt_needs_native_verified_finalisation(self):
        self.source('INTERRUPTED')
        probe = self.e.check_source('B0', self.s.base, 'A1')
        self.assertFalse(probe['attachment_eligible'])
        self.assertEqual(probe['native']['state'], 'INTERRUPTED')
        with self.assertRaises(ValueError):
            self.e.attach('B0', 'S1', self.s.base, 'A1')
        SR.finalise_interrupted(self.s.base, 'A1', no_attempt_running=True, clock=self.s.clock.now)
        self.e.attach('B0', 'S1', self.s.base, 'A1')
        r = self.e.checkpoint()['branches'][0]['source_activities'][0]
        self.assertEqual(r['status'], 'UNKNOWN')
        self.assertTrue(r['interrupted'])
        self.assertIsNotNone(r['reference']['finalisation_sha256'])
        self.assertTrue((self.s.attempt() / 'attempt.lock').exists())

    def test_operator_human_wait_and_missing_ready_never_create_candidate(self):
        archive = Archive(self.f['archive']); state = archive.load()
        review = copy.deepcopy(state.current_review(state.latest(self.ids[0])))
        review.update(idea_id=self.ids[1], decision='INCUBATE', approved_handoff=False)
        archive.append('review', review, recorded_at=demo.MOMENT)
        self.source(branch='B1'); self.e.attach('B1', 'S-INCUBATE', self.s.base, 'A1')
        self.operator(idea=1)
        rep = self.e.checkpoint()['branches'][1]
        op = rep['operator_checkpoints'][0]
        self.assertEqual(op['integrity'], 'VERIFIED_NATIVE_COMPLETION')
        self.assertEqual(rep['campaign_state']['scout_route'], 'INCUBATE')
        self.assertEqual(rep['source_activities'][0]['status'], 'COMPLETE')
        self.assertEqual(op['stages']['FORGE_READINESS']['status'], 'WAITING_FOR_HUMAN')
        self.assertEqual(op['stages']['ANVIL_DRAFTS']['summary']['candidate']['status'], 'NOT_DRAFTED')
        self.assertIn('CURRENT_SCOUT_READY_HANDOFF_REQUIRED_FOR_APPROVED_CONTINUATION', rep['pending_native_gates'])
        self.assertIsNone(op['discovery'])

    def test_native_quarry_jev_and_discovery_reused_without_fake_source_link(self):
        self.operator(evidence=True)
        rep = self.e.checkpoint()['branches'][0]
        op = rep['operator_checkpoints'][0]
        self.assertEqual(op['integrity'], 'VERIFIED_NATIVE_COMPLETION', op)
        self.assertEqual(op['stages']['JEV_EVIDENCE']['status'], 'COMPLETE')
        self.assertIsNotNone(op['discovery'])
        self.assertFalse(op['discovery']['software_certifies_M'])
        self.assertTrue(any(r['blockers'] for r in op['discovery']['requirements'].values()))
        self.assertEqual(rep['source_to_quarry']['status'], 'NOT_IMPLEMENTED_WAITING_FOR_NATIVE_CUSTODY_BRIDGE')
        self.assertIn('HUMAN_M_REVIEW_NOT_RECORDED_IN_LINKED_NATIVE_CHECKLIST', rep['pending_native_gates'])
        self.assertTrue(any('CROSSWALK' in r for r in rep['pending_native_gates']))
        exports = [v['summary']['export'] for k, v in op['stages'].items() if k.startswith('QUARRY_EXPORT:') and v['status'] == 'COMPLETE']
        manifest = Path(exports[0]) / 'manifest.json'; raw = manifest.read_bytes()
        try:
            manifest.write_bytes(raw + b' ')
            bad = self.e.checkpoint()['branches'][0]['operator_checkpoints'][0]
            self.assertEqual(bad['integrity'], 'RECONCILIATION_REQUIRED')
        finally:
            manifest.write_bytes(raw)
        # An actual supplied ledger without a crosswalk remains unlinked, even
        # when it is byte-for-byte the preview for the same card.
        ledger = self.root / 'unlinked.jsonl'
        ledger.write_bytes(Path(op['stages']['ANVIL_CHECKS']['summary']['ledger']).read_bytes())
        spec = runs.evidence_spec(R.loads(R.read(self.f['evidence'])), Path(self.f['evidence']).parent)
        supplied = runs.ledger_spec(ledger, op['discovery']['candidate'], None)
        layout = runs.create(runs.request_value(self.f['archive'], self.ids[0], None, spec, [], supplied),
                             base=self.f['base'], run_id='OPR-UNLINKED')
        runs.invoke(layout, 'run')
        self.c.attach('B0', 'OPR-UNLINKED', layout.run)
        rep = self.e.checkpoint()['branches'][0]
        unlinked = next(o for o in rep['operator_checkpoints'] if o['activity_id'] == 'OPR-UNLINKED')
        self.assertEqual(unlinked['stages']['ANVIL_CHECKS']['summary']['link'], 'UNLINKED')
        self.assertIsNone(unlinked['discovery'])
        self.assertEqual(rep['campaign_state']['execution_state'], 'AMBIGUOUS_NATIVE_REFERENCE')

    def test_changed_native_completion_and_ambiguous_runs_remain_unresolved(self):
        first = self.operator(name='OPR-FIRST')
        self.operator(name='OPR-SECOND')
        rep = self.e.checkpoint()['branches'][0]
        self.assertEqual(rep['campaign_state']['execution_state'], 'AMBIGUOUS_NATIVE_REFERENCE')
        self.assertEqual(len(rep['operator_checkpoints']), 2)
        from src.research.operator.journal import Journal
        journal = Journal(first.run)
        journal.append('INVOCATION_FINISHED', journal.load()[-1]['record'])
        rep = self.e.checkpoint()['branches'][0]
        self.assertEqual(rep['campaign_state']['execution_state'], 'RECONCILIATION_REQUIRED')
        self.assertTrue(any(r['integrity'] == 'RECONCILIATION_REQUIRED' for r in rep['operator_checkpoints']))

    def test_stale_card_and_code_refuse_mutation_without_rewriting_native_history(self):
        self.source(); original = read_tree(self.c.root)
        with patch('src.research.campaign_evidence_v1.continuity.implementation', return_value={'changed': True}), \
             patch('src.research.campaign_evidence_v1.checkpoint.implementation', return_value={'changed': True}):
            with self.assertRaisesRegex(ValueError, 'IMPLEMENTATION_CHANGED'):
                self.e.attach('B0', 'S1', self.s.base, 'A1')
            self.assertTrue(self.e.checkpoint()['implementation_changed'])
        with patch.object(N, 'branch_current', side_effect=R.CampaignError('STALE_CARD_VERSION')):
            with self.assertRaisesRegex(ValueError, 'STALE_CARD_VERSION'):
                self.e.attach('B0', 'S1', self.s.base, 'A1')
        self.assertEqual(original, read_tree(self.c.root))
        archive = Archive(self.f['archive'])
        from src.research.opportunity_scout import fixtures as F
        archive.append('feasibility', F.feasibility(archive.load().latest(self.ids[0])), recorded_at=demo.MOMENT)
        with self.assertRaisesRegex(ValueError, 'archive/card/version/hash'):
            self.e.attach('B0', 'S1', self.s.base, 'A1')

    def test_legacy_bindings_companion_tamper_truncation_and_stale_lock(self):
        self.assertEqual(N.implementation()['campaign'], 'df6467ba915919d8d33433c1ec063bb9c8d398d4d93eee480007cf406ca5c3b0')
        p = self.e.root / 'events.jsonl'; raw = p.read_bytes()
        p.write_bytes(raw + b'{')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.e.checkpoint()
        p.write_bytes(raw)
        m = self.e.root / 'companion.json'; original = m.read_bytes()
        m.write_text('{}')
        with self.assertRaises((ValueError, KeyError)):
            self.e.checkpoint()
        m.write_bytes(original)
        (self.e.root / 'companion.lock').write_text('owner must reconcile')
        self.source()
        with self.assertRaisesRegex(ValueError, 'locked'):
            self.e.attach('B0', 'S1', self.s.base, 'A1')
        self.assertTrue((self.e.root / 'companion.lock').exists())

    def test_status_cli_and_refusals_are_deterministic_read_only_and_guarded(self):
        self.source(); self.e.attach('B0', 'S1', self.s.base, 'A1')
        before = read_tree(self.f['base'])
        self.assertEqual(self.e.checkpoint(), self.e.checkpoint())
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['--base', str(self.f['base']), 'checkpoint', self.c.root.name]), 0)
        self.assertEqual(json.loads(output.getvalue())['authorises'], [])
        self.assertEqual(before, read_tree(self.f['base']))
        probes = [('socket.connect', (None, ('example.invalid', 1))), ('subprocess.Popen', ('forbidden',)),
                  ('open', (str(self.root / '.codex' / 'auth.json'), 'r', 0)),
                  ('open', (str(self.root / 'foreign.txt'), 'w', 1))]
        original = N.branch_current
        for event, args in probes:
            def probe(branch):
                BOUNDARY.audit(event, args)
                return original(branch)
            with patch.object(N, 'branch_current', side_effect=probe), self.assertRaises(BoundaryViolation):
                self.e.attach('B0', 'S1', self.s.base, 'A1')
        self.assertFalse((self.root / 'foreign.txt').exists())

    def test_rehearsal_refusal_and_native_anvil_preview_are_explicit(self):
        out = self.root / 'rehearsal'
        with patch.object(SR, 'run', side_effect=AssertionError('no source dispatch')):
            result = rehearse(out)
        self.assertEqual(result['outcome'], 'FOUNDATION_ONLY_CUSTODY_BRIDGE_NOT_CONNECTED')
        self.assertEqual(result['model_calls'], 0); self.assertEqual(result['external_requests'], 0)
        self.assertEqual(result, json.loads((out / 'checkpoint.json').read_bytes()))
        r = result['checkpoint']['branches'][0]
        self.assertEqual(r['source_activities'][0]['status'], 'NOT_STARTED')
        self.assertEqual(r['operator_checkpoints'][0]['integrity'], 'VERIFIED_NATIVE_COMPLETION')
        self.assertFalse(list(out.rglob('ABSENT-owner-scope.json')))
        with self.assertRaises(ValueError):
            rehearse(out)
