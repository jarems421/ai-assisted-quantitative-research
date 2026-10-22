"""Targeted offline tests of metadata monitoring; no credential file is opened."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.opportunity_scout import schema as S, v004_monitoring as M


class MonitoringReviewTests(unittest.TestCase):
    def samples(self, root):
        return [M.account_metadata(root) for _ in range(3)]

    def test_account_snapshot_never_opens_or_hashes_credential_contents(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / '.claude').mkdir()
            (root / '.claude/.credentials.json').write_text('SYNTHETIC DO NOT OPEN')
            with patch.object(Path, 'open', side_effect=AssertionError('account contents opened')), \
                 patch.object(Path, 'read_bytes', side_effect=AssertionError('account bytes read')), \
                 patch.object(Path, 'read_text', side_effect=AssertionError('account text read')):
                snapshot = M.account_metadata(root)
            self.assertEqual(snapshot['files']['.claude/.credentials.json']['state'], 'REGULAR_FILE')
            self.assertFalse(snapshot['credential_contents_accessed'])
            self.assertNotIn('SYNTHETIC DO NOT OPEN', str(snapshot))

    def test_changed_file_and_replacement_are_guard_failures_without_attribution(self):
        with tempfile.TemporaryDirectory() as td:
            a = M.account_metadata(td); b = copy.deepcopy(a)
            b['files']['.claude.json'] = {'state': 'REGULAR_FILE', 'size': 10, 'mtime_ns': 20,
                                         'ctime_ns': 20, 'file_id': 1, 'device': 1}
            result = M.compare_metadata(a, b)
            self.assertEqual(result['changed_paths'], ['.claude.json'])
            self.assertEqual(result['writer_attribution'], S.UNKNOWN)
            self.assertEqual(result['credential_leakage'], 'NOT_ESTABLISHED')
            c = copy.deepcopy(b); c['files']['.claude.json']['file_id'] = 2
            self.assertFalse(M.compare_metadata(b, c)['unchanged_observed_metadata'])

    def test_same_size_and_times_do_not_prove_equal_contents(self):
        with tempfile.TemporaryDirectory() as td:
            a, b, _ = self.samples(td); result = M.compare_metadata(a, b)
            self.assertTrue(result['unchanged_observed_metadata'])
            self.assertEqual(result['content_equality'], S.UNKNOWN)
            self.assertFalse(result['probe_authorised'])

    def test_unobservable_or_incomplete_path_coverage_cannot_pass(self):
        with tempfile.TemporaryDirectory() as td:
            a, b, _ = self.samples(td)
            b['files']['.claude/.credentials.json'] = {'state': 'UNOBSERVABLE'}
            self.assertFalse(M.compare_metadata(a, b)['unchanged_observed_metadata'])
            b['files'].pop('.claude.json')
            with self.assertRaises(S.ScoutError): M.compare_metadata(a, b)

    def test_per_probe_baseline_cannot_hide_earlier_drift(self):
        with tempfile.TemporaryDirectory() as td:
            samples = self.samples(td)
            for s in samples[1:]: s['files']['.claude.json'] = {'state': 'UNOBSERVABLE'}
            result = M.quiet_window_review(samples, [{'observable': True, 'processes': []}] * 3)
            self.assertIn('ACCOUNT_METADATA_GUARD_FAILED', result['flags'])

    def test_separate_development_process_contaminates_quiet_window(self):
        with tempfile.TemporaryDirectory() as td:
            samples = self.samples(td)
            processes = [{'observable': True, 'processes': []},
                         {'observable': True, 'processes': [{'pid': 42, 'started_at': '2026-10-22T08:00:00Z'}]},
                         {'observable': True, 'processes': []}]
            result = M.quiet_window_review(samples, processes)
            self.assertIn('CONCURRENT_OR_UNEXPECTED_CLAUDE_PROCESS', result['flags'])
            self.assertFalse(result['window_observationally_clean'])

    def test_pid_reuse_or_missing_process_visibility_is_not_clean(self):
        with tempfile.TemporaryDirectory() as td:
            samples = self.samples(td)
            permitted = {'pid': 42, 'started_at': '2026-10-22T08:00:00Z'}
            processes = [{'observable': True, 'processes': [permitted]}] * 2 + [
                {'observable': True, 'processes': [{'pid': 42, 'started_at': '2026-10-22T09:00:00Z'}]}]
            self.assertFalse(M.quiet_window_review(samples, processes, allowed_probe=permitted)['window_observationally_clean'])
            processes[-1] = {'observable': False, 'processes': []}
            self.assertIn('PROCESS_OBSERVABILITY_UNKNOWN', M.quiet_window_review(samples, processes, allowed_probe=permitted)['flags'])

    def test_clean_sampled_window_still_never_authorises_probe_or_proves_noninterference(self):
        with tempfile.TemporaryDirectory() as td:
            result = M.quiet_window_review(self.samples(td), [{'observable': True, 'processes': []}] * 3)
            self.assertTrue(result['window_observationally_clean'])
            self.assertFalse(result['content_noninterference_proven']); self.assertFalse(result['probe_authorised'])

    def test_only_parent_recorded_probe_may_appear_in_active_middle_sample(self):
        with tempfile.TemporaryDirectory() as td:
            permitted = {'pid': 42, 'started_at': '2026-10-22T08:00:00Z'}
            quiet = {'observable': True, 'processes': []}
            active = {'observable': True, 'processes': [permitted]}
            samples = self.samples(td)
            self.assertTrue(M.quiet_window_review(samples, [quiet, active, quiet], allowed_probe=permitted)['window_observationally_clean'])
            self.assertIn('PROBE_OUTSIDE_ACTIVE_SAMPLE', M.quiet_window_review(samples, [active, active, quiet], allowed_probe=permitted)['flags'])

    def test_command_lines_and_reversed_sample_times_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            samples = self.samples(td)
            samples[0]['sampled_at'] = '2099-01-01T00:00:00Z'
            with self.assertRaises(S.ScoutError): M.compare_metadata(samples[0], samples[1])
            samples = self.samples(td)
            processes = [{'observable': True, 'processes': [{'pid': 1, 'started_at': '2026-10-22T08:00:00Z',
                                                           'command_line': 'MUST NOT COLLECT'}]}] * 3
            with self.assertRaises(S.ScoutError): M.quiet_window_review(samples, processes)


if __name__ == '__main__': unittest.main()
