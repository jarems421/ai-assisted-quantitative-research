from datetime import date
import unittest
from src.research.exp002_contracts import sec_filing_availability,decision_points,execution_signal,session_key,split_safe_ratio
from src.research.exp002_inference import paired_uncertainty,implementation_costs
from src.research.pit_signals import filing_state,decision_for_session


class FinalContracts(unittest.TestCase):
    def test_session_freshness_cannot_cross_formation_cutoff(self):
        with self.assertRaises(ValueError):decision_points(date(2021,1,1),5,valid=True)

    def test_same_day_restatement_needs_explicit_amendment_sequence(self):
        base=dict(availableAt='2015-05-15T03:59:59.999Z',kind='ORIGINAL',accession='original',
                  complete=True,identity_certified=True,holdings={'s':1})
        correction=dict(base,kind='RESTATEMENT',accession='amended',holdings={'s':2},amendment_sequence=1)
        t=decision_for_session(date(2015,6,1))
        self.assertEqual(filing_state([correction,base],t)['holdings'],{'s':2})
        del correction['amendment_sequence']
        with self.assertRaises(ValueError):filing_state([base,correction],t)

    def test_overlapping_addition_and_missing_original_rejected(self):
        original=dict(availableAt='2015-05-15T03:59:59.999Z',kind='ORIGINAL',accession='original',
                      complete=True,identity_certified=True,holdings={'s':1})
        addition=dict(original,kind='NEW HOLDINGS',accession='addition',availableAt='2015-05-16T03:59:59.999Z',holdings={'s':2})
        t=decision_for_session(date(2015,6,1))
        with self.assertRaises(ValueError):filing_state([original,addition],t)
        with self.assertRaises(ValueError):filing_state([addition],t)

    def test_naive_sec_timezone_standard_and_daylight(self):
        self.assertEqual(sec_filing_availability('2014-11-07 04:59:59.999','2014-11-06').hour,4)
        self.assertEqual(sec_filing_availability('2014-07-02 03:59:59.999','2014-07-01').hour,3)
        with self.assertRaises(ValueError):sec_filing_availability('2014-07-01 23:59:59.999','2014-07-01')

    def test_execution_equals_frozen_decision_and_stale_values_never_trade(self):
        day=date(2015,11,2);points=decision_points(day,5,valid=True)
        self.assertEqual(execution_signal(day,points['signal']['value'],1,points['session_key']['value']),5)
        self.assertIsNone(execution_signal(date(2015,11,3),5,1,session_key(day)))
        self.assertIsNone(execution_signal(day,5,0,session_key(day)))
        self.assertIsNone(execution_signal(day,5,None,None))
        self.assertNotIn('signal',decision_points(day,None,valid=False))

    def test_split_continuity_and_future_prefix(self):
        rows=[dict(executionDate='2020-08-31',splitFrom=1,splitTo=4)]
        self.assertEqual(split_safe_ratio(400,100,date(2020,8,28),date(2020,8,31),rows),1)
        future=dict(executionDate='2020-09-10',splitFrom=1,splitTo=10)
        self.assertEqual(split_safe_ratio(400,410,date(2020,8,27),date(2020,8,28),rows+[future]),1.025)

    def test_paired_bootstrap_identical_series_zero_differences(self):
        values=[.001*((i%7)-3) for i in range(100)]
        r=paired_uncertainty(values,values,draws=50)
        self.assertEqual(r['mean_ci_95'],[0,0]);self.assertEqual(r['sharpe_ci_95'],[0,0])
        self.assertFalse(r['holm_applied']);self.assertFalse(r['selection_bias_adjusted'])

    def test_bootstrap_deterministic_and_invalid_inputs(self):
        a=[.001*((i%7)-3) for i in range(100)];b=[v-.0001 for v in a]
        self.assertEqual(paired_uncertainty(a,b,draws=30),paired_uncertainty(a,b,draws=30))
        with self.assertRaises(ValueError):paired_uncertainty([0]*100,[0]*100,draws=30)
        with self.assertRaises(ValueError):paired_uncertainty(a,b[:-1],draws=30)

    def test_cost_stress_counts_both_sides_and_never_fabricates_execution(self):
        fills=[dict(quantity=10,price=100),dict(quantity=-10,price=110)]
        self.assertEqual(implementation_costs(fills,10),[1,1.1])
        self.assertEqual(implementation_costs(fills,20),[2,2.2])
        with self.assertRaises(ValueError):implementation_costs(fills,15)
