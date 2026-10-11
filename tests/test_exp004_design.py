"""Pre-run protection and selection contracts; synthetic effects only."""
import copy
import hashlib
import json
import unittest
from datetime import date, datetime, timezone

from src.research.exp004_policy import cells, compile_templates, momentum, ranked_targets, paired_eligibility, select
from src.research.design_exp004 import evaluation_plan, price_coverage
from src.research.ingestion import eligible
from src.research.spec import ROOT, enforce_range, validate


def evidence(parameters=None):
    return {'parameters': parameters or cells()[0], 'primary_benchmark': 'equal_weight_eligible_universe',
            'comparison_audited': True, 'critical_rules_pass': True, 'same_dates_universe_costs': True,
            'pooled_mean_daily_excess': .001, 'pooled_sharpe_difference': .1,
            'mean_traded_notional_fraction': .1,
            'paired_folds': [{'year': y, 'scheduled_decisions': 12, 'participating_decisions': 11,
                             'mean_daily_excess': .001, 'sharpe_difference': .1}
                            for y in range(2017, 2021)]}


class EXP004DesignTests(unittest.TestCase):
    def test_schema_draft_and_sealed_access(self):
        spec = json.loads((ROOT/'experiments/EXP004/spec.json').read_text(encoding='utf-8'))
        validate(spec)
        self.assertTrue(eligible(spec, {}, evidence()))
        self.assertEqual(spec['approval_state'], 'DRAFT')
        self.assertEqual(spec['windows']['development']['start'], '2015-01-02')
        for day in ('2021-01-01', '2024-01-01'):
            with self.assertRaises(ValueError): enforce_range(spec, 'DRAFT', day, day)
        with self.assertRaises(ValueError): enforce_range(spec, 'TEST_AUTHORIZED', '2024-01-01', '2024-12-31')
        enforce_range(spec, 'TEST_AUTHORIZED', '2024-01-01', '2024-12-31', test_authorized=True)
        spec['optimization_ranges']['unexpected_axis'] = [1, 2]
        with self.assertRaises(ValueError): validate(spec)

    def test_primary_comparator_and_direction_not_standalone_sharpe(self):
        self.assertFalse(paired_eligibility({'sharpe': 100}))
        for change in ({'primary_benchmark': 'SPY'}, {'pooled_mean_daily_excess': 0},
                       {'pooled_sharpe_difference': -1}, {'comparison_audited': False},
                       {'critical_rules_pass': False}, {'same_dates_universe_costs': False},
                       {'pooled_mean_daily_excess': float('nan')}):
            self.assertFalse(paired_eligibility(dict(evidence(), **change)))

    def test_each_fold_participation_and_three_positive_folds(self):
        e = evidence(); e['paired_folds'][0]['participating_decisions'] = 10
        self.assertFalse(paired_eligibility(e))
        e = evidence(); e['paired_folds'][0]['participating_decisions'] = 13
        self.assertFalse(paired_eligibility(e))
        e = evidence(); e['paired_folds'][0]['mean_daily_excess'] = -.0001
        self.assertTrue(paired_eligibility(e))
        e['paired_folds'][1]['mean_daily_excess'] = -.0001
        self.assertFalse(paired_eligibility(e))
        e = evidence(); e['paired_folds'].pop()
        self.assertFalse(paired_eligibility(e))

    def test_complete_surface_no_advancement_and_fixed_ties(self):
        candidates = [evidence(p) for p in cells()]
        self.assertEqual(select(candidates)['parameters'], cells()[0])
        candidates[1]['mean_traded_notional_fraction'] = .01
        self.assertIs(select(candidates), candidates[1])
        for c in candidates: c['pooled_sharpe_difference'] = 0
        self.assertIsNone(select(candidates))
        with self.assertRaises(ValueError): select(candidates[:-1])
        candidates[-1] = copy.deepcopy(candidates[0])
        with self.assertRaises(ValueError): select(candidates)

    def test_median_fold_over_single_or_pooled_optimum(self):
        candidates = [evidence(p) for p in cells()]
        candidates[0]['pooled_mean_daily_excess'] = 10
        candidates[1]['paired_folds'][0]['mean_daily_excess'] = .1
        for f in candidates[2]['paired_folds']: f['mean_daily_excess'] = .002
        self.assertIs(select(candidates), candidates[2])

    def test_price_momentum_split_and_future_prefix(self):
        bars = [{'date': '2015-12-31', 'availableAt': '2016-01-01T02:00:00Z', 'unadjustedClose': 100},
                {'date': '2016-06-28', 'availableAt': '2016-06-29T01:00:00Z', 'unadjustedClose': 60}]
        split = {'executionDate': '2016-05-01', 'availableAt': '2016-05-01T00:00:00Z', 'splitFrom': 1, 'splitTo': 2}
        at = datetime(2016, 6, 29, 1, tzinfo=timezone.utc)
        value = momentum(bars, [split], date(2016, 6, 28), at, 180)
        self.assertAlmostEqual(value, .2)
        future = dict(split, executionDate='2017-01-01', availableAt='2017-01-01T00:00:00Z')
        self.assertEqual(momentum(bars, [split, future], date(2016, 6, 28), at, 180), value)
        with self.assertRaises(ValueError): momentum(bars+bars[:1], [split], date(2016,6,28), at,180)
        with self.assertRaises(ValueError): momentum(bars[:-1], [split], date(2016,6,28), at,180)
        with self.assertRaises(ValueError): momentum(bars, [dict(split, availableAt='2017-01-01T00:00:00Z')], date(2016,6,28), at,180)

    def test_stable_id_ties_and_cash_shortfall(self):
        values = {'B': 0, 'A': 0}
        targets = ranked_targets(values, 20)
        self.assertEqual(list(targets), ['A', 'B'])
        self.assertEqual(sum(targets.values()), 9.5)
        self.assertEqual(ranked_targets({}, 40), {})
        with self.assertRaises(ValueError): ranked_targets({'A': float('nan')}, 20)

    def test_compiled_sdk_and_evaluation_ledger(self):
        compiled = compile_templates()
        self.assertEqual(len(compiled['candidates']), 4)
        self.assertEqual(compiled['remote_calls'], 0)
        self.assertEqual(compiled, json.loads((ROOT/'experiments/EXP004/compiled_templates.json').read_text(encoding='utf-8')))
        plan = evaluation_plan()
        self.assertEqual(sum(plan['independent_runs'].values()), 59)
        self.assertEqual(plan['local_cost_analyses'], 12)
        self.assertEqual(plan['attempted_exp004_remote_jobs'], 0)

    def test_existing_price_evidence_inception_and_determinism(self):
        raw = ROOT/'data/raw/EXP003/final_readiness_20261011/2015_v002/rows.json'
        if not raw.exists(): self.skipTest('Private immutable coverage receipts absent')
        result = price_coverage()
        self.assertEqual(result, json.loads((ROOT/'experiments/EXP004/research/price_coverage.json').read_text(encoding='utf-8')))
        self.assertEqual(result['development_inception'], '2015-01-02')
        self.assertEqual(result['monthly_decisions'], 72)
        self.assertEqual(result['price_prerequisite_security_decisions'], 273452)
        self.assertEqual(result['minimum_eligible_prerequisite_count'], 3595)
        self.assertFalse(any(m['shortfall_K40'] for m in result['monthly']))

    def test_closed_experiments_and_results_unchanged(self):
        provenance = json.loads((ROOT/'experiments/EXP004/provenance.json').read_text(encoding='utf-8'))
        for path, expected in provenance['protected_tracked_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), expected, path)
        self.assertFalse(provenance['operations']['hypothesis_frozen'])
        self.assertEqual(provenance['operations']['nexus_calls'], 0)
