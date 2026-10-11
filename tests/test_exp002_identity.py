import unittest
from src.research.two_gate_exp002 import dated_identity,omission_state

class IdentityContractTests(unittest.TestCase):
    def setUp(self):
        self.h=dict(cusip='037833100',accession='filing',manager_cik='0000002230',reporting_quarter='2015-06-30',availableAt='2015-08-15T03:59:59.999Z')
        self.m=dict(cusip='037833100',ticker='AAPL',security_id='stable',source='certified dated crosswalk',valid_from='2013-01-01',valid_to='2020-12-31',status='CERTIFIED_UNIQUE',date_basis='America/New_York')
    def test_requires_mapping_span_not_just_listing_span(self):
        self.assertEqual(dated_identity(self.h,[self.m]),self.m)
        for key in ('source','valid_from','valid_to','security_id','status','date_basis'):
            row=dict(self.m);del row[key];self.assertIsNone(dated_identity(self.h,[row]))
    def test_conflicting_or_outside_mapping_never_first_wins(self):
        self.assertIsNone(dated_identity(self.h,[self.m,dict(self.m,ticker='AAPL.MX')]))
        self.assertIsNone(dated_identity(self.h,[dict(self.m,valid_from='2016-01-01')]))
    def test_missing_identity_and_future_amendments_never_zero(self):
        s=dict(accession='filing',manager_cik='0000002230',reporting_quarter='2015-06-30',complete_eligible_filing=True,all_raw_rows_available=True,asof_reconstructed=True,amendments_reconciled=True,raw_cusip_holdings={'OTHER':1},availableAt='2015-08-15T03:59:59.999Z')
        self.assertEqual(omission_state(self.m,s,'2015-09-01T01:00:00Z'),'NOT_HELD')
        self.assertEqual(omission_state(None,s,'2015-09-01T01:00:00Z'),'UNAVAILABLE')
        self.assertEqual(omission_state(self.m,dict(s,all_raw_rows_available=False),'2015-09-01T01:00:00Z'),'UNAVAILABLE')
        self.assertEqual(omission_state(self.m,dict(s,availableAt='2016-01-01T00:00:00Z'),'2015-09-01T01:00:00Z'),'UNAVAILABLE')
        self.assertEqual(omission_state(self.m,dict(s,raw_cusip_holdings={'037833100':float('nan')}),'2015-09-01T01:00:00Z'),'UNAVAILABLE')
