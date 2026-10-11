"""Meaningful identity adversaries and two-signal trial-accounting checks."""
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from src.research.design_exp003 import eligible_identity, evaluation_plan, universe_summary
from src.research.spec import ROOT, validate


def span(ticker='OLD', sid='stable', kind='CS', start='2015-01-01', end='2020-12-31'):
    return dict(ticker=ticker, security_id=sid, asset_type=kind, from_date=start, to_date=end)


class EXP003DesignTests(unittest.TestCase):
    def test_renames_and_ended_histories(self):
        spans = [span(end='2016-01-04'), span('NEW', start='2016-01-05')]
        self.assertEqual(eligible_identity(spans, 'OLD', '2016-01-04'), 'stable')
        self.assertIsNone(eligible_identity(spans, 'OLD', '2016-01-05'))
        self.assertEqual(eligible_identity(spans, 'NEW', '2016-01-05'), 'stable')

    def test_reused_tickers_and_type_ambiguity_fail_closed(self):
        for other in (span(sid='other'), span(kind='ETF'), span(kind=None), span(sid=None)):
            self.assertIsNone(eligible_identity([span(), other], 'OLD', '2015-01-02'))
        self.assertIsNone(eligible_identity([span(kind='ADRC')], 'OLD', '2015-01-02'))
        with self.assertRaisesRegex(ValueError, 'Post-cutoff'):
            eligible_identity([span()], 'OLD', '2021-01-01')

    def test_snapshot_aliases_staleness_and_ignored_filters(self):
        rows = [dict(ticker=t, security_id=s, day=d, proposed_adv=None, price_threshold=False)
                for t, s, d in [('OLD','stable','2015-01-30'), ('ALIAS','stable','2015-01-30'),
                                 ('OTHER','other','2015-01-29'), ('ENDED','ended','2015-01-30')]]
        spans = [span(), span('ALIAS'), span('OTHER','other'), span('ENDED','ended',end='2015-01-30')]
        result = universe_summary(spans, rows)
        self.assertEqual(result['totals']['stale_month_endpoint'], 1)
        self.assertEqual(result['totals']['duplicate_security_exclusion_rows'], 2)
        self.assertEqual(result['annual_union_ids'], {'2015': 1})
        self.assertEqual(result['retained_ids_with_a_pre_cutoff_ended_CS_span'], 1)
        self.assertIsNone(result['joint_development_inception'])

    def test_reduced_controls_and_all_attempt_accounting(self):
        plan = evaluation_plan()
        self.assertEqual(plan['family_cell_counts'], {'momentum_only':4, 'insider_only':4, 'momentum_insider':8})
        self.assertEqual(plan['conditional_remote_ceiling'], 116)
        self.assertEqual(plan['components']['development_grid_folds'], 72)
        for cell in plan['family_cells']['momentum_only']:
            self.assertNotIn('insider_lookback_calendar_days', cell)
        self.assertFalse(plan['spend_authorized'])
        self.assertIsNone(plan['token_quote'])

    def test_draft_cannot_freeze_from_placeholders(self):
        spec = json.loads((ROOT/'experiments/EXP003/spec.json').read_text(encoding='utf-8'))
        schema = json.loads((ROOT/'experiments/_template/spec.schema.json').read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(spec)
        with self.assertRaisesRegex(ValueError, 'Point-in-time availability unestablished'):
            validate(spec)
        self.assertEqual(spec['windows']['test'], {'start':'2024-01-01','end':'2024-12-31'})
        self.assertEqual(spec['maximum_complexity'], 2)
        self.assertTrue(all(value == 0 for value in spec['budget'].values()))

    def test_closed_EXP002_files_unchanged(self):
        provenance = json.loads((ROOT/'experiments/EXP003/provenance.json').read_text(encoding='utf-8'))
        for name, expected in provenance['preserved_EXP002_tracked_sha256'].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
