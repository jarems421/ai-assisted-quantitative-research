"""Bounded extraction and ambiguous-action safety, with no remote calls."""
import unittest
from datetime import date

from src.research.exp004_inputs import bar_request
from src.research.exp004_compile import calendar, eod, assert_split_lineage
from src.research.prepare_exp004 import verify_freeze


class EXP004SourceTests(unittest.TestCase):
    def test_bound_queries_cannot_read_later_market_data(self):
        self.assertEqual(bar_request('2013-12-31','2014-03-31')['params'],['2013-12-31','2014-03-31'])
        for start,end in [('2020-01-01','2021-01-01'),('2013-01-01','2014-01-01'),('2016-01-01','2015-01-01')]:
            with self.assertRaises(ValueError):bar_request(start,end)

    def test_same_date_actions_require_lineage_not_a_guessed_ratio(self):
        assert_split_lineage('A',date(2016,1,1),[{'splitFrom':1,'splitTo':2}])
        with self.assertRaisesRegex(ValueError,'authoritative event/version lineage'):
            assert_split_lineage('A',date(2016,1,1),[{'splitFrom':1,'splitTo':2},{'splitFrom':1,'splitTo':3}])

    def test_calendar_and_availability_reuse_completed_contract(self):
        dates=calendar()
        self.assertEqual(min(dates),date(2013,12,31))
        self.assertEqual(max(dates),date(2020,12,31))
        self.assertNotIn(date(2018,12,5),dates)
        self.assertEqual(eod(date(2015,1,1)),'2015-01-02T02:00:00+00:00')
        self.assertEqual(eod(date(2015,7,1)),'2015-07-02T01:00:00+00:00')

    def test_source_work_never_changes_frozen_methodology(self):
        self.assertEqual(verify_freeze()['status'],'HYPOTHESIS_FROZEN')
