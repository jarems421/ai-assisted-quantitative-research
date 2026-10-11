"""Synthetic identity and pause failures; no remote transport."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.research.capabilities import ROOT, require_population, require_remote_enabled
from src.research.demo import FakeSDK
from src.research.nexus import Jobs
from src.research.store import Store
from src.research import exp004_inputs, exp004_execute, exp004_streams, exp004_publication_reconcile


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'security_id': 'synthetic-' + s, 'ticker': s} for s in ('OLD', 'ENDED', 'CLASS.A', 'KEPT')]

    def check(self, observed, **kwargs):
        return require_population(self.rows, observed, complete=kwargs.get('complete', True),
                                  binding_verified=kwargs.get('binding_verified', True))

    def test_order_independent_exact_population(self):
        self.assertEqual(self.check(self.rows[::-1])['status'], 'PASS')

    def test_pruning_and_equal_count_substitution_fail(self):
        for observed in (self.rows[-1:], self.rows[:-1] + [{'security_id': 'substitute', 'ticker': 'NEW'}]):
            with self.assertRaisesRegex(ValueError, 'POPULATION_MISMATCH'): self.check(observed)

    def test_current_alias_and_punctuation_rewrite_fail(self):
        for i, ticker in ((0, 'NEW'), (2, 'CLASS-A')):
            observed = [dict(r) for r in self.rows]; observed[i]['ticker'] = ticker
            with self.assertRaisesRegex(ValueError, 'POPULATION_MISMATCH'): self.check(observed)

    def test_unknown_capability_and_partial_evidence_fail(self):
        for kwargs in ({'complete': False}, {'binding_verified': False}, {'complete': 'true'}):
            with self.assertRaisesRegex(ValueError, 'Uncertified'): self.check(self.rows, **kwargs)

    def test_duplicate_missing_and_ambiguous_identity_fail(self):
        for observed in (self.rows + self.rows[:1], [{'ticker': 'OLD'}],
                         self.rows + [{'security_id': 'synthetic-OLD', 'ticker': 'NEW'}],
                         self.rows + [{'security_id': 'another-id', 'ticker': 'OLD'}], [None]):
            with self.assertRaises(ValueError): self.check(observed)

    def test_certified_empty_population_is_distinct_from_missing_evidence(self):
        self.assertEqual(require_population([], [], complete=True, binding_verified=True)['status'], 'PASS')
        with self.assertRaises(ValueError): require_population([], [], complete=False, binding_verified=True)


class PauseTests(unittest.TestCase):
    def test_exp004_entrypoints_stop_before_io_credentials_or_network(self):
        calls = [(exp004_inputs.client_for, (Path('unused'),)), (exp004_inputs.extract, ('unused', {})),
                 (exp004_execute.submit, ('EW', 0)), (exp004_execute.poll, ('unused',)),
                 (exp004_streams.publish, ()), (exp004_publication_reconcile.one, ('unused',)),
                 (exp004_publication_reconcile.remaining, ())]
        for action, args in calls:
            with self.subTest(action=action.__name__), self.assertRaisesRegex(ValueError, 'operationally paused'):
                action(*args)

    def test_synthetic_jobs_pause_leaves_scientific_state_and_transport_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'config').mkdir()
            (root/'config/operational_pauses.json').write_text(json.dumps({'EXP999': {'reason': 'synthetic pause'}}))
            spec = json.loads((ROOT/'tests/fixtures/research_os/EXP999.json').read_bytes())
            store = Store(root)
            try:
                store.register(spec); before = store.state('EXP999'); sdk = FakeSDK()
                jobs = Jobs(store, sdk, mcp=Mock())
                for call in (lambda: jobs.submit(spec, 'backtest', {}, {}, family='synthetic', candidate='x', parameters={}, execute=True),
                             lambda: jobs.poll(spec, 'unused'), lambda: jobs.reconcile(spec, 'unused', 'unused'),
                             lambda: jobs.deploy_paper(spec, 'unused', execute=True)):
                    with self.assertRaisesRegex(ValueError, 'operationally paused'): call()
                self.assertEqual(store.state('EXP999'), before)
                self.assertEqual(sdk.submissions + sdk.reads, 0)
                self.assertEqual(store.db.execute('SELECT count(*) FROM jobs').fetchone()[0], 0)
                jobs.mcp.assert_not_called()
            finally: store.close()

    def test_other_experiments_and_local_compilation_remain_available(self):
        require_remote_enabled(ROOT, 'EXP999')
        self.assertEqual(exp004_inputs.bar_request('2015-01-01', '2015-01-02')['params'],
                         ['2015-01-01', '2015-01-02'])

    def test_malformed_pause_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'config').mkdir()
            (root/'config/operational_pauses.json').write_text('{')
            with self.assertRaises(ValueError): require_remote_enabled(root, 'EXP999')
