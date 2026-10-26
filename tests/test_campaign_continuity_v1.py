"""Temporary synthetic campaigns using real offline operator receipts; no hosted/source activity."""
import contextlib
import copy
import io
import json
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.research.campaign_v1 import campaign as C, native as N, records as R
from src.research.campaign_v1.__main__ import main
from src.research.operator import demo, runs, report
from src.research.operator.journal import Journal
from src.research.opportunity_scout.automation_v001 import execution as X
from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout import fixtures as F
from src.research.spec import canonical, digest
from tests.test_research_operator_v1 import REVISION, read_tree


class CampaignTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.f = demo.fixtures(self.root)
        p = patch.object(X, 'revision', return_value=REVISION); p.start(); self.addCleanup(p.stop)
        self.c = C.create(self.f['base'], 'CMP-SYNTHETIC', 1000000)
        self.ids = [self.f['ready_idea'], self.f['unreviewed_idea']]
        self.layouts = []
        for index, iid in enumerate(self.ids):
            self.c.add_branch(f'B{index}', self.f['archive'], iid, 1, digest(Archive(self.f['archive']).load().latest(iid)))
            layout = runs.create(runs.request_value(self.f['archive'], iid, None, None, [], None),
                                 base=self.f['base'], run_id=f'OPR-CAMPAIGN-{index}')
            runs.invoke(layout, 'run')
            self.layouts.append(layout)

    def attach(self):
        for i, layout in enumerate(self.layouts):
            self.c.attach(f'B{i}', f'A{i}', layout.run)

    def test_two_branches_exact_identity_and_distinct_blockers_no_science_inferred(self):
        self.attach(); rep = self.c.status()
        a, b = rep['branches']
        self.assertEqual([a['stage'], b['stage']], ['QUARRY_EVIDENCE', 'FORGE_READINESS'])
        self.assertTrue(all(x['research_outcome'] is None for x in (a, b)))
        self.assertNotEqual(a['blockers'], b['blockers'])
        for i, row in enumerate((a, b)):
            card = Archive(self.f['archive']).load().latest(self.ids[i])
            self.assertEqual((row['hypothesis']['idea_id'], row['hypothesis']['version'], row['hypothesis']['card_sha256']),
                             (self.ids[i], 1, digest(card)))
            self.assertEqual(row['activities'][0]['receipt']['event'], 'INVOCATION_FINISHED')
        self.assertEqual(len(rep['budgets']['component_batches']), 1)
        self.assertEqual(rep['budgets']['component_batches'][0]['branches'], ['B0', 'B1'])
        self.assertEqual(rep['budgets']['component_actual_charges'], 'UNKNOWN')
        self.assertEqual(rep['authorises'], [])

    def test_duplicate_activity_and_branch_conflicts_do_not_append_or_reexecute(self):
        self.attach(); before = read_tree(self.f['base'])
        self.assertFalse(self.c.attach('B0', 'A0', self.layouts[0].run))
        with self.assertRaisesRegex(ValueError, 'identity conflict'):
            self.c.attach('B1', 'A0', self.layouts[1].run)
        with self.assertRaisesRegex(ValueError, 'another branch'):
            self.c.attach('B1', 'OTHER', self.layouts[0].run)
        with self.assertRaisesRegex(ValueError, 'already attached'):
            self.c.attach('B0', 'OTHER', self.layouts[0].run)
        self.assertEqual(read_tree(self.f['base']), before)

    def test_card_hash_version_and_native_branch_must_match(self):
        for version, sha in ((2, 'a' * 64), (1, 'b' * 64)):
            with self.assertRaisesRegex(ValueError, 'version/hash mismatch'):
                self.c.add_branch('WRONG', self.f['archive'], self.ids[0], version, sha)
        with self.assertRaisesRegex(ValueError, 'same card'):
            self.c.add_branch('ALIAS', self.f['archive'], self.ids[0], 1, digest(Archive(self.f['archive']).load().latest(self.ids[0])))

    def test_status_final_are_deterministic_and_read_only_without_native_operations(self):
        self.attach(); before = read_tree(self.root)
        with patch.object(runs, 'invoke', side_effect=AssertionError('native replay')), \
                patch.object(socket, 'create_connection', side_effect=AssertionError('network')), \
                patch.object(subprocess, 'Popen', side_effect=AssertionError('process')):
            first = canonical(self.c.status())
            self.assertEqual(first, canonical(C.Campaign(self.c.root).status()))
            for command in ('status', 'final'):
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(main(['--base', str(self.f['base']), command, 'CMP-SYNTHETIC', '--json']), 0)
                self.assertEqual(canonical(json.loads(out.getvalue())), first)
            self.assertEqual(self.c.reconcile(), {'A0': 'UNCHANGED', 'A1': 'UNCHANGED'})
        self.assertEqual(read_tree(self.root), before)

    def test_stale_artifact_isolated_from_other_branch(self):
        self.attach()
        artifact = next(self.layouts[0].artifacts.glob('card-*.json'))
        artifact.write_bytes(artifact.read_bytes() + b' ')
        rows = self.c.status()['branches']
        self.assertEqual(rows[0]['execution_state'], 'RECONCILIATION_REQUIRED')
        self.assertEqual(rows[0]['activities'][0]['run_id'], self.layouts[0].run_id)
        self.assertEqual(rows[1]['execution_state'], 'STOPPED_AT_BOUNDARY')
        result = self.c.reconcile()
        self.assertTrue(result['A0'].startswith('RECONCILIATION_REQUIRED'))
        self.assertEqual(result['A1'], 'UNCHANGED')

    def test_changed_code_keeps_reports_readable_but_refuses_mutation(self):
        self.attach(); changed = copy.deepcopy(N.implementation()); changed['campaign'] = 'a' * 64
        before = read_tree(self.c.root)
        with patch.object(N, 'implementation', return_value=changed):
            self.assertTrue(self.c.status()['implementation_changed'])
            with self.assertRaisesRegex(ValueError, 'IMPLEMENTATION_CHANGED'):
                self.c.reconcile()
        self.assertEqual(read_tree(self.c.root), before)

    def test_native_report_and_journal_tamper_never_become_valid_activity(self):
        layout = self.layouts[0]
        saved = next(layout.reports.glob('*.json'))
        original = saved.read_bytes(); value = json.loads(original); value['outcome'] = 'COMPLETE'
        saved.write_bytes(canonical(value))
        with self.assertRaisesRegex(ValueError, 'report differs'):
            self.c.attach('B0', 'A0', layout.run)
        saved.write_bytes(original)
        self.c.attach('B0', 'A0', layout.run)
        Journal(layout.run).file.write_bytes(Journal(layout.run).file.read_bytes()[:-1])
        self.assertEqual(self.c.status()['branches'][0]['execution_state'], 'RECONCILIATION_REQUIRED')

    def test_interrupted_campaign_observation_reconstructs_without_native_replay(self):
        self.attach()
        # Existing operator performs a separately requested synthetic CHECK continuation.
        for layout in self.layouts:
            runs.invoke(layout, 'continue')
        self.assertTrue(all(b['execution_state'] == 'RECONCILIATION_REQUIRED' for b in self.c.status()['branches']))
        native_before = [read_tree(l.run) for l in self.layouts]
        real = self.c.journal.append
        count = 0
        def crash(kind, record, **kw):
            nonlocal count
            count += 1
            if count == 2:
                raise KeyboardInterrupt('synthetic interruption before second observation')
            return real(kind, record, **kw)
        with patch.object(self.c.journal, 'append', side_effect=crash), self.assertRaises(KeyboardInterrupt):
            self.c.reconcile()
        rebuilt = C.Campaign(self.c.root)
        with patch.object(runs, 'invoke', side_effect=AssertionError('no replay')):
            self.assertEqual(rebuilt.reconcile(), {'A0': 'UNCHANGED', 'A1': 'OBSERVED_EXISTING_COMPLETION'})
            self.assertEqual(rebuilt.reconcile(), {'A0': 'UNCHANGED', 'A1': 'UNCHANGED'})
        self.assertEqual([read_tree(l.run) for l in self.layouts], native_before)

    def test_unfinished_native_invocation_and_missing_receipt_are_not_replayed(self):
        self.attach(); layout = self.layouts[0]
        Journal(layout.run).append('INVOCATION_STARTED', {'command': 'continue', 'execution': runs.provenance()})
        before = read_tree(layout.run)
        self.assertIn('never replay', self.c.reconcile()['A0'])
        self.assertEqual(read_tree(layout.run), before)

    def test_campaign_chain_truncation_manifest_tamper_and_stale_lock_refused(self):
        before = self.c.journal.file.read_bytes()
        self.c.journal.file.write_bytes(before[:-1])
        with self.assertRaisesRegex(ValueError, 'incomplete journal'):
            self.c.status()
        self.c.journal.file.write_bytes(before)
        manifest = self.c.root / 'campaign.json'; original = manifest.read_bytes()
        value = json.loads(original); value['api_allocation_micro_usd'] = 1; manifest.write_bytes(canonical(value))
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            self.c.status()
        manifest.write_bytes(original)
        self.c.journal.lock.write_text('SYNTHETIC stale lock')
        with self.assertRaisesRegex(ValueError, 'locked'):
            self.c.reconcile()
        self.assertTrue(self.c.journal.lock.exists())

    def test_incubate_provisional_boundary_does_not_require_or_create_ready(self):
        state = Archive(self.f['archive']).load()
        self.assertFalse(state.current_review(state.latest(self.ids[1])))
        before = read_tree(self.f['archive'])
        row = self.c.status()['branches'][1]
        boundary = row['provisional_source']
        self.assertFalse(boundary['requires_scout_ready'])
        self.assertFalse(boundary['implemented']); self.assertFalse(boundary['dispatch_eligible'])
        self.assertEqual(read_tree(self.f['archive']), before)

    def test_path_escape_and_invalid_campaign_location_refused(self):
        for name in ('../escape', 'a/b', ''):
            with self.assertRaises(ValueError):
                C.create(self.f['base'], name)
        with self.assertRaisesRegex(ValueError, 'private/raw'):
            self.c.attach('B0', 'A0', self.root / '.env')

    def test_guard_blocks_network_process_and_foreign_writes(self):
        from src.research.operator.guard import BoundaryViolation, BOUNDARY
        original = N.branch_current
        # Direct audit probes, as in operator regressions: no real attempt may
        # contaminate the outer restricted-suite guard's forbidden-operation latch.
        for effect in (lambda: BOUNDARY.audit('socket.connect', (None, ('example.invalid', 9))),
                       lambda: BOUNDARY.audit('subprocess.Popen', ('never-start', [], None, None)),
                       lambda: (self.root / 'foreign.txt').write_text('no')):
            def unexpected(branch):
                effect()
                return original(branch)
            with patch.object(N, 'branch_current', side_effect=unexpected), self.assertRaises(BoundaryViolation):
                self.c.status()
        self.assertFalse((self.root / 'foreign.txt').exists())

    def test_native_code_change_is_not_accepted_as_a_new_observation(self):
        self.attach()
        real = N.observe
        def drifted(*args, **kw):
            observation, rep = real(*args, **kw)
            observation['binding'] = {**observation['binding'], 'implementation': 'e' * 64}
            return observation, rep
        before = read_tree(self.c.root)
        with patch.object(N, 'observe', side_effect=drifted):
            self.assertIn('NATIVE_IMPLEMENTATION_CHANGED', self.c.reconcile()['A0'])
            self.assertEqual(self.c.status()['branches'][0]['execution_state'], 'RECONCILIATION_REQUIRED')
        self.assertEqual(read_tree(self.c.root), before)

    def test_current_scout_stop_overrides_an_old_ready_native_report(self):
        self.attach()
        archive = Archive(self.f['archive']); card = archive.load().latest(self.ids[0])
        # Fixture-only withdrawal: native Scout owns this record, never campaign code.
        archive.append('review', {'readiness_version': 'SCOUT_READY_V002', 'idea_id': card['id'], 'version': 1,
                                 'decision': 'INCUBATE', 'reason_type': 'UNRESOLVED',
                                 'reason': 'SYNTHETIC later review withdraws the earlier READY decision.', 'uncertainties': ['Fixture only.'],
                                 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'},
                                 'minutes': 'UNKNOWN', 'approved_handoff': False, 'reconsider_when': 'Fixture evidence',
                                 'authorises_acquisition': False})
        row = self.c.status()['branches'][0]
        self.assertFalse(row['scout_handoff_eligible'])
        self.assertEqual(row['scout_route'], 'INCUBATE')
        self.assertEqual(row['execution_state'], 'RECONCILIATION_REQUIRED')
        self.assertTrue(any('STALE_NATIVE_SCOUT_RECORDS' in b for b in row['blockers']))
        self.assertIsNone(row['research_outcome'])

    def test_native_working_copy_review_can_advance_without_changing_original(self):
        self.attach(); layout = self.layouts[1]
        original = read_tree(self.f['archive'])
        work = Archive(layout.scout); card = work.load().latest(self.ids[1])
        # Native-owned SYNTHETIC records only. Campaign never authors reviews.
        work.append('feasibility', F.feasibility(card), recorded_at=F.MOMENT)
        review = copy.deepcopy(work.load().reviews[0]); review['idea_id'] = card['id']
        work.append('review', review, recorded_at=F.MOMENT)
        self.assertEqual(self.c.status()['branches'][1]['execution_state'], 'RECONCILIATION_REQUIRED')
        runs.invoke(layout, 'continue')
        native_before = read_tree(layout.run)
        self.assertEqual(self.c.reconcile('B1'), {'A1': 'OBSERVED_EXISTING_COMPLETION'})
        row = self.c.status()['branches'][1]
        self.assertEqual(row['stage'], 'QUARRY_EVIDENCE')
        self.assertEqual(row['execution_state'], 'STOPPED_AT_BOUNDARY')
        self.assertFalse(row['scout_handoff_eligible'])  # explicitly the original
        self.assertEqual(read_tree(self.f['archive']), original)
        self.assertEqual(read_tree(layout.run), native_before)

    def test_completed_quarry_jev_continuation_is_referenced_without_native_replay(self):
        self.attach(); layout = self.layouts[0]
        p = Path(self.f['evidence'])
        evidence = runs.evidence_spec(json.loads(p.read_bytes()), p.parent)
        runs.invoke(layout, 'continue', supplied={'evidence': evidence, 'search_terms': [], 'ledger': None})
        before = read_tree(self.f['base'])
        result = self.c.reconcile('B0')
        self.assertEqual(result, {'A0': 'OBSERVED_EXISTING_COMPLETION'})
        row = self.c.status()['branches'][0]
        self.assertEqual(row['stage'], 'ANVIL_DRAFTS')
        self.assertEqual(row['execution_state'], 'STOPPED_AT_BOUNDARY')
        self.assertIsNone(row['research_outcome'])
        # Only campaign observations change; native operator/Quarry/Jev trees do not.
        after = read_tree(self.f['base'])
        self.assertEqual({k: v for k, v in before.items() if not k.startswith('campaign-v1/')},
                         {k: v for k, v in after.items() if not k.startswith('campaign-v1/')})

    def test_multiple_completed_runs_are_ambiguous_independent_of_attachment_order(self):
        old = self.layouts[0]
        p = Path(self.f['evidence'])
        evidence = runs.evidence_spec(json.loads(p.read_bytes()), p.parent)
        other = runs.create(runs.request_value(self.f['archive'], self.ids[0], None, evidence, [], None),
                            base=self.f['base'], run_id='OPR-SAME-CARD-EVIDENCE')
        runs.invoke(other, 'run')
        before = read_tree(self.f['base'])
        views = []; campaigns = []
        with patch.object(runs, 'invoke', side_effect=AssertionError('native replay')):
            for index, order in enumerate(((('A-OLD', old), ('A-EVIDENCE', other)),
                                           (('A-EVIDENCE', other), ('A-OLD', old)))):
                campaign = C.create(self.f['base'], f'CMP-ORDER-{index}')
                campaigns.append(campaign)
                card = Archive(self.f['archive']).load().latest(self.ids[0])
                campaign.add_branch('B0', self.f['archive'], card['id'], card['version'], digest(card))
                for aid, layout in order:
                    campaign.attach('B0', aid, layout.run)
                views.append(campaign.status()['branches'][0])
                self.assertEqual(campaign.reconcile(), {'A-EVIDENCE': 'UNCHANGED', 'A-OLD': 'UNCHANGED'})
        self.assertEqual(views[0], views[1],
                         f"Attachment order selected branch stages: {[v['stage'] for v in views]}")
        row = views[0]
        self.assertEqual(row['execution_state'], 'AMBIGUOUS_NATIVE_REFERENCE')
        self.assertIsNone(row['stage']); self.assertIsNone(row['research_outcome'])
        self.assertEqual({a['activity_id']: a['state']['stage'] for a in row['activities']},
                         {'A-OLD': 'QUARRY_EVIDENCE', 'A-EVIDENCE': 'ANVIL_DRAFTS'})
        for activity in row['activities']:
            self.assertEqual(activity['state']['execution_state'], 'STOPPED_AT_BOUNDARY')
            self.assertIsNone(activity['state']['research_outcome'])
            self.assertTrue(activity['state']['blockers'])
        rendered = C.markdown({'campaign_id': 'CMP-VIEW', 'journal_head': 'a' * 64,
                               'journal_events': 1, 'branches': [row],
                               'budgets': {'component_batches': []}})
        for text in ('AMBIGUOUS_NATIVE_REFERENCE', 'A-OLD', 'A-EVIDENCE', 'QUARRY_EVIDENCE', 'ANVIL_DRAFTS'):
            self.assertIn(text, rendered)
        after = read_tree(self.f['base'])
        self.assertEqual({k: v for k, v in before.items() if not k.startswith('campaign-v1/')},
                         {k: v for k, v in after.items() if not k.startswith('campaign-v1/')})
        # Integrity failures still take precedence, without hiding the other run.
        artifact = next(old.artifacts.glob('card-*.json'))
        artifact.write_bytes(artifact.read_bytes() + b' ')
        invalid = [c.status()['branches'][0] for c in campaigns]
        self.assertEqual(invalid[0], invalid[1])
        self.assertEqual(invalid[0]['execution_state'], 'RECONCILIATION_REQUIRED')
        self.assertEqual({a['activity_id']: a['state']['execution_state'] for a in invalid[0]['activities']},
                         {'A-OLD': 'RECONCILIATION_REQUIRED', 'A-EVIDENCE': 'STOPPED_AT_BOUNDARY'})
