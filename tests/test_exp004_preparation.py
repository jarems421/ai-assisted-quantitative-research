"""Production input gates; no live SDK client or remote operations."""
import copy
import json
import unittest

from src.research.prepare_exp004 import check_numeric_input, verify_freeze
from src.research.spec import ROOT, digest


class EXP004PreparationTests(unittest.TestCase):
    def arguments(self):
        return {'session': '2016-07-01', 'prior_session': '2016-06-30',
                'decision': '2016-07-01T01:00:00Z',
                'expected_sessions': ['2015-07-01', '2016-01-04', '2016-06-30']}

    def rows(self):
        return [{'security_id': 'stable-A', 'identity_audited': True, 'ambiguous': False,
                 'asset_type': 'CS', 'source_sha256': 'synthetic-fixture-only', 'splits': [],
                 'bars': [{'date': day, 'availableAt': day+'T23:00:00Z', 'unadjustedClose': price}
                          for day, price in [('2015-07-01', 100), ('2016-01-04', 110), ('2016-06-30', 120)]]}]

    def test_frozen_methodology_remains_exact(self):
        f = verify_freeze()
        original=json.loads((ROOT/'experiments/EXP004/freeze_receipt.json').read_bytes())
        self.assertEqual(original['frozen_specification_sha256'], '88fec6e53e14939d3a40fa8f55170ad40712f5b1b8ff7e2c5c9002a4d2ef185d')
        self.assertEqual(f['frozen_specification_sha256'],digest(json.loads((ROOT/'experiments/EXP004/spec.json').read_bytes())))

    def test_counts_do_not_create_numeric_rank_or_zero(self):
        result = check_numeric_input([], ['stable-A'], **self.arguments())
        self.assertEqual(result['status'], 'FAIL')
        self.assertIsNone(result['ranking_values'])
        counts = [{'security_id': 'stable-A', 'days_365': 253}]
        self.assertEqual(check_numeric_input(counts, ['stable-A'], **self.arguments())['status'], 'FAIL')

    def test_valid_fixture_generates_both_horizons_and_shortfall_targets(self):
        result = check_numeric_input(self.rows(), ['stable-A'], **self.arguments())
        self.assertEqual(result['status'], 'PASS_LOCAL_NUMERIC_QA')
        self.assertAlmostEqual(result['ranking_values'][365]['stable-A'], .2)
        self.assertAlmostEqual(result['ranking_values'][180]['stable-A'], 120/110-1)
        self.assertEqual(result['selected_top_K']['M180_K20'], {'stable-A': 4.75})

    def test_duplicate_missing_future_and_ambiguous_inputs_fail(self):
        rows = self.rows()
        variants = [rows+copy.deepcopy(rows), self.rows()]
        variants[1][0]['ambiguous'] = True
        future = self.rows(); future[0]['bars'][-1]['availableAt'] = '2021-01-01T00:00:00Z'
        missing = self.rows(); missing[0]['bars'].pop(1)
        duplicates = self.rows(); duplicates[0]['bars'].append(copy.deepcopy(duplicates[0]['bars'][0]))
        for rows in variants+[future, missing, duplicates]:
            self.assertEqual(check_numeric_input(rows, ['stable-A'], **self.arguments())['status'], 'FAIL')

    def test_preparation_manifest_is_hashed_and_prevents_submissions(self):
        m = json.loads((ROOT/'experiments/EXP004/development_input_manifest.json').read_text(encoding='utf-8'))
        expected = m.pop('input_manifest_sha256')
        self.assertEqual(digest(m), expected)
        self.assertEqual(len(m['decisions']), 72)
        self.assertTrue(all(d['session']<='2020-12-31' for d in m['decisions']))
        self.assertTrue(all(not d['submit_allowed'] or d['qa_status']=='PASS_LOCAL_NUMERIC' for d in m['decisions']))
