import unittest
from src.research.phase3e.feasibility import horizon_gate,contributor_bounds


class Phase3EFeasibilityTests(unittest.TestCase):
    def test_legacy_programme_cannot_fit_pilot_approval(self):
        windows={'development':['2021-01-01','2026-12-31'],'validation':['2027-01-01','2029-12-31'],'test':['2030-01-01','2032-12-31']}
        result=horizon_gate(['2015-01-01','2021-12-31'],windows)
        self.assertEqual(result['status'],'INCOMPATIBLE_POLICY_SCOPE')
        self.assertEqual(result['complete_stages_covered'],0)
        self.assertEqual(result['stages'][0]['policy_covered_calendar_days'],365)
        self.assertEqual(result['stages'][1]['policy_covered_calendar_days'],0)
        self.assertFalse(result['research_authorized'])

    def test_date_coverage_does_not_grant_authority_and_stages_cannot_overlap(self):
        windows={'development':['2015-01-01','2017-12-31'],'validation':['2018-01-01','2019-12-31'],'test':['2020-01-01','2021-12-31']}
        result=horizon_gate(['2015-01-01','2021-12-31'],windows)
        self.assertEqual(result['status'],'COVERED_NOT_AUTHORIZED');self.assertFalse(result['research_authorized'])
        with self.assertRaises(ValueError):horizon_gate(['2015-01-01','2021-12-31'],dict(windows,test=['2019-01-01','2021-12-31']))
        with self.assertRaises(ValueError):horizon_gate(['2021-12-31','2015-01-01'],windows)

    def test_contributor_bound_is_not_a_signal_or_certified_chain(self):
        chains=[{'case_key':str(i),'filing_accessions':['a','b','c']} for i in range(30)]
        times=[{'accession':a,'status':'INVARIANT','candidate_bounds_utc':[d,d]} for a,d in [('a','2019-01-04T14:30:00+00:00'),('b','2020-01-06T14:30:00+00:00'),('c','2021-01-07T14:30:00+00:00')]]
        rows=contributor_bounds(chains,times)
        self.assertEqual(rows[0]['mechanical_all_contributor_bound_utc'],times[-1]['candidate_bounds_utc'][0])
        self.assertFalse(rows[0]['trading_eligible']);self.assertFalse(rows[0]['source_triple_certified'])
        times[-1]['candidate_bounds_utc'].append('2021-01-08T14:30:00+00:00')
        self.assertEqual(contributor_bounds(chains,times)[0]['status'],'CLOCK_OR_CALENDAR_UNRESOLVED')
