"""Fictional evidence only, under Scout's process/private-read/network guards."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.spec import canonical
from src.research.opportunity_scout.n1_collector import admission as A, binding as B, readiness as R
from tests.scout_n1_admission_fixtures import package, frame, baseline, process_identity
from tests.scout_n1_fixtures import consent


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.b, self.a, self.payload, self.artifacts = package(self.temp.name)

    def window(self, active=False):
        w = A.Window(self.b)
        baseline(w, self.b)
        if active:
            w.step('ADMIT', 60, None)
            w.step('ATTACH', 60, process_identity())
        return w

    def sample(self, w, now, **changes):
        f = frame(self.b, w.seq + 1, now, w.phase, w.expected, first=not w.start_verified,
                  exited=w.phase == 'COOLDOWN')
        f.update(changes)
        w.step('SAMPLE', now, {'frame': f, 'local_exit_observed': w.phase == 'COOLDOWN'})

    def test_exact_evidence_contract_is_read_only_and_never_admits(self):
        before = copy.deepcopy(self.artifacts)
        result = A.review_contract(self.b, self.a, self.payload, self.artifacts)
        self.assertEqual(result['status'], 'OFFLINE_CONSISTENCY_ONLY_NOT_ADMISSION')
        self.assertFalse(result['native_launch_enabled'])
        self.assertEqual(result['owner_registration_sha256'], B.sha(canonical(self.a)))
        self.assertEqual(self.artifacts, before)
        self.assertFalse(Path(self.b['audit_root']).exists())

    def test_changed_originals_reviews_sources_and_missing_evidence_are_refused(self):
        for name in A.ARTIFACTS:
            artifacts = copy.deepcopy(self.artifacts); artifacts[name] += b'\n'
            with self.subTest(name=name), self.assertRaises((ValueError, KeyError)):
                A.review_contract(self.b, self.a, self.payload, artifacts)
        for key, change in [('sources', {}), ('audit', {}), ('hashes', {}), ('fixture', False), ('checks', {}),
                            ('sentinel', {'pid': 55, 'parent_pid': 11, 'name': 'python.exe', 'earliest_filetime': 100})]:
            artifacts = copy.deepcopy(self.artifacts)
            review = json.loads(artifacts['preparation_review']); review[key] = change
            artifacts['preparation_review'] = canonical(review)
            with self.subTest(review=key), self.assertRaises(ValueError):
                A.review_contract(self.b, self.a, self.payload, artifacts)
        with self.assertRaises(ValueError):
            A.review_contract(self.b, self.a, self.payload, {})

    def test_resealed_failed_or_historical_preparation_still_refused(self):
        for key, value in [('status', 'STOP'), ('N1_admission', True), ('continuous_coverage_certified', True),
                           ('schema', 'SCOUT_N1_PROCESS_OBSERVER_V002'), ('metadata_samples', 0),
                           ('observer_head', '0' * 64), ('sentinel_start_exit_parent_observed', False)]:
            artifacts = copy.deepcopy(self.artifacts)
            r = json.loads(artifacts['receipt']); r[key] = value; artifacts['receipt'] = canonical(r)
            review = json.loads(artifacts['preparation_review']); review['hashes']['receipt'] = B.sha(artifacts['receipt'])
            artifacts['preparation_review'] = canonical(review)
            b = copy.deepcopy(self.b); b['admission_contract']['artifacts'] = {k: B.sha(v) for k, v in artifacts.items()}
            with self.subTest(key=key), self.assertRaises(ValueError):
                A.review_contract(b, consent(b), self.payload, artifacts)

    def test_runtime_policy_plan_consent_and_reservation_gates(self):
        for name, field, value in [('runtime_review', 'controls_supported', {}), ('account_review', 'managed_policy', 'UNKNOWN'),
                                   ('account_review', 'identity', 'UNKNOWN'), ('observation_plan', 'baseline_seconds', 59),
                                   ('observation_plan', 'cooldown_seconds', 59)]:
            artifacts = copy.deepcopy(self.artifacts)
            record = json.loads(artifacts[name]); record[field] = value; artifacts[name] = canonical(record)
            b = copy.deepcopy(self.b); b['admission_contract']['artifacts'] = {k: B.sha(v) for k, v in artifacts.items()}
            with self.subTest(name=name, field=field), self.assertRaises(ValueError):
                A.review_contract(b, consent(b), self.payload, artifacts)
        with self.assertRaises(ValueError):
            A.review_contract(self.b, {**self.a, 'approved': False}, self.payload, self.artifacts)
        registry = Path(self.b['audit_root']); registry.mkdir()
        for name in ('.lock', self.b['reservation_id'] + '.json'):
            path = registry / name; path.write_bytes(b'FICTIONAL stale evidence')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'stale/held/consumed'):
                A.review_contract(self.b, self.a, self.payload, self.artifacts)
            self.assertEqual(path.read_bytes(), b'FICTIONAL stale evidence'); path.unlink()

    def test_resealed_metadata_gaps_drift_and_content_boundary_still_refused(self):
        for fault in ('gap', 'drift', 'contents', 'missing'):
            artifacts = copy.deepcopy(self.artifacts)
            rows = [json.loads(line) for line in artifacts['metadata'].splitlines()]
            if fault == 'gap': rows[1]['elapsed_seconds'] = 6
            if fault == 'drift': rows[1]['metadata']['files']['.claude-research.json'] = {'state': 'REGULAR_FILE',
                'size': 1, 'mtime_ns': 1, 'ctime_ns': 1, 'file_id': 1, 'device': 1}
            if fault == 'contents': rows[1]['metadata']['credential_contents_accessed'] = True
            if fault == 'missing': del rows[1]['metadata']['files']['.claude.json']
            artifacts['metadata'] = b''.join(canonical(row) + b'\n' for row in rows)
            receipt = json.loads(artifacts['receipt']); receipt['metadata_log_sha256'] = B.sha(artifacts['metadata'])
            artifacts['receipt'] = canonical(receipt)
            review = json.loads(artifacts['preparation_review'])
            review['hashes'] = {k: B.sha(artifacts[k]) for k in ('receipt', 'events', 'metadata')}
            artifacts['preparation_review'] = canonical(review)
            b = copy.deepcopy(self.b); b['admission_contract']['artifacts'] = {k: B.sha(v) for k, v in artifacts.items()}
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                A.review_contract(b, consent(b), self.payload, artifacts)

    def test_preparation_success_without_fresh_baseline_cannot_launch(self):
        gate = A.FixtureGate(self.b, self.a, self.payload, self.artifacts, lambda *args: None)
        with self.assertRaisesRegex(ValueError, 'fresh baseline'):
            gate.prelaunch(self.b, self.a, 0)
        self.assertEqual(gate.window.phase, 'STOP')
        with self.assertRaises(ValueError):
            gate.poll(60)

    def test_complete_baseline_owned_start_and_post_drain_cooldown(self):
        w = self.window(active=True)
        self.sample(w, 60.1)
        self.assertTrue(w.start_verified)
        w.step('DRAINED', 60.2, True)
        for i in range(12):
            self.sample(w, 60.2 + i * 5)
        self.assertEqual(w.phase, 'COOLDOWN')
        self.sample(w, 120.2)
        self.assertEqual(w.phase, 'COMPLETE')

    def test_short_baseline_stale_missing_sequence_future_and_nonfinite_stop(self):
        for changes in ({'seq': 99}, {'monotonic_seconds': 54}, {'monotonic_seconds': 62},
                        {'monotonic_seconds': float('nan')}, {'monotonic_seconds': float('inf')},
                        {'window_id': 'OTHER'}, {'binding_sha256': '0' * 64}, {'fixture': False}):
            w = self.window()
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.sample(w, 61, **changes)
            self.assertEqual(w.phase, 'STOP')
            with self.assertRaises(ValueError): self.sample(w, 62)
        w = A.Window(self.b); self.sample(w, 0)
        with self.assertRaisesRegex(ValueError, '60-second'):
            w.step('ADMIT', 1, None)
        w = self.window()
        with self.assertRaisesRegex(ValueError, 'gap'):
            self.sample(w, 65.01)

    def test_metadata_coverage_and_policy_unknowns_or_drift_stop(self):
        for changes in ({'coverage': {}}, {'coverage': {**A.COVERAGE, 'starts': False}},
                        {'coverage': {**A.COVERAGE, 'inventory': 1}},
                        {'coverage': {**A.COVERAGE, 'loss_detected': True}}, {'managed_policy': {'state': 'UNKNOWN'}},
                        {'account_review_sha256': '0' * 64}, {'runtime_review_sha256': '0' * 64},
                        {'metadata': {}}, {'processes': None}):
            with self.subTest(changes=changes), self.assertRaises((ValueError, KeyError)):
                self.sample(self.window(), 61, **changes)
        w = self.window(); self.sample(w, 61)
        m = copy.deepcopy(w.baseline); m['files']['.claude-research.json'] = {'state': 'REGULAR_FILE',
            'size': 1, 'mtime_ns': 1, 'ctime_ns': 1, 'file_id': 1, 'device': 1}
        with self.assertRaisesRegex(ValueError, 'drift'):
            self.sample(w, 62, metadata=m)

    def test_exact_process_only_and_transient_or_reused_pid_stops(self):
        for key, value in [('pid', 56), ('parent_pid', 11), ('creation_filetime', 101), ('name', 'claude.exe')]:
            w = self.window(active=True)
            wrong = {**w.expected, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.sample(w, 61, processes=[wrong], starts=[wrong])
        for field in ('processes', 'starts'):
            w = self.window(active=True)
            other = {**w.expected, 'pid': 56, 'name': 'claude.exe'}
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.sample(w, 61, **{field: [w.expected, other]})
        w = self.window(active=True)
        with self.assertRaises(ValueError): self.sample(w, 61, starts=[])
        # Pure fictional Claude identity: one exact owner can match, but a
        # second Claude under that same parent cannot inherit the exception.
        b = copy.deepcopy(self.b); b['binary'] = str(Path(b['binary']).with_name('claude.exe'))
        w = A.Window(b); baseline(w, b); w.step('ADMIT', 60, None); w.step('ATTACH', 60, process_identity())
        f = frame(b, w.seq + 1, 61, 'ACTIVE', w.expected, first=True)
        w.step('SAMPLE', 61, {'frame': f, 'local_exit_observed': False})
        f = frame(b, w.seq + 1, 62, 'ACTIVE', w.expected)
        f['processes'].append({**w.expected, 'pid': 56})
        with self.assertRaises(ValueError): w.step('SAMPLE', 62, {'frame': f, 'local_exit_observed': False})

    def test_unknown_start_identity_cleanup_and_no_restart(self):
        for key, value in [('created_windows_filetime', 'UNKNOWN'), ('collector_pid', 0), ('child_parent_basis', 'UNKNOWN')]:
            w = self.window(); w.step('ADMIT', 60, None)
            with self.subTest(key=key), self.assertRaises(ValueError):
                w.step('ATTACH', 60, {**process_identity(), key: value})
        w = self.window(active=True); self.sample(w, 61)
        with self.assertRaises(ValueError): w.step('DRAINED', 61, False)
        w = self.window(active=True); self.sample(w, 61); w.step('DRAINED', 61, True)
        with self.assertRaises(ValueError): self.sample(w, 62, descendants_absent=False)
        with self.assertRaises(ValueError): w.step('ADMIT', 62, None)

    def test_gate_cannot_rebind_or_enable_native_even_with_complete_fixtures(self):
        gate = A.FixtureGate(self.b, self.a, self.payload, self.artifacts, lambda *args: None)
        b = copy.deepcopy(self.b); b['reservation_id'] = b['session_id']
        with self.assertRaisesRegex(ValueError, 'another reservation'):
            gate.prelaunch(b, consent(b), 0)
        with self.assertRaisesRegex(ValueError, 'native'):
            A.FixtureGate({**self.b, 'mode': 'NATIVE_REVIEW_ONLY'}, self.a, self.payload, self.artifacts, lambda *a: None)
        with patch('subprocess.Popen') as launch, self.assertRaisesRegex(ValueError, 'disabled'):
            R.launch_native(self.b, self.a, self.payload, monitor=gate, enabled=True)
        launch.assert_not_called()
