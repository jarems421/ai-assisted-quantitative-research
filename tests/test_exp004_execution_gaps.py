import unittest
from src.research.exp004_execution_gaps import classify,scale_screen,RECOVERY,amendment_ready

class ExecutionGapEvidenceTests(unittest.TestCase):
    def test_vendor_absence_or_zero_volume_does_not_certify_no_trade(self):
        for e in ({},{'vendor_empty':True},{'two_vendors_empty':True},{'volume':0}):
            self.assertEqual(classify(e),'UNRESOLVED_VENDOR_GAP')
        self.assertEqual(classify({'authoritative_exact_no_trading':True}),'CERTIFIED_NO_TRADING')
    def test_recovery_requires_every_contract_field(self):
        e={k:True for k in RECOVERY};self.assertEqual(classify(e),'RECOVERED_EXECUTION_BAR')
        for k in RECOVERY:
            x=dict(e);x[k]=False;self.assertNotEqual(classify(x),'RECOVERED_EXECUTION_BAR')
        self.assertEqual(classify(dict(e,positive_identity_or_unit_conflict=True)),'IDENTITY_OR_SHARE_UNIT_CONFLICT')
    def test_scale_screen_does_not_accept_split_units_or_derive_price(self):
        self.assertTrue(scale_screen('10.01','10'));self.assertFalse(scale_screen('2.5','10'))
        self.assertFalse(scale_screen('nan','10'))
    def test_one_unresolved_case_prevents_amendment(self):
        rows=[{'required_session':'2017-01-03','ticker':str(i),'frozen_security_id':str(i),'verdict':'CERTIFIED_NO_TRADING'} for i in range(26)]
        self.assertTrue(amendment_ready(rows));rows[-1]['verdict']='UNRESOLVED_VENDOR_GAP';self.assertFalse(amendment_ready(rows))
        with self.assertRaises(ValueError):amendment_ready(rows[:-1])
    def test_scientific_budget_and_duplicate_submission(self):
        from src.research.exp004_execution_gaps import request_room
        allocation={'Lake_batch':1,'alternative_exact_case':26,'official_corroboration':8,'schema_documentation':5}
        records=[{'category':'Lake_batch','key':'first'}]
        self.assertFalse(request_room(records,'Lake_batch','new',allocation))
        self.assertFalse(request_room(records,'official_corroboration','first',allocation))
        self.assertTrue(request_room(records,'official_corroboration','new',allocation))
        full=[{'category':category,'key':str(i)} for category,n in allocation.items() for i in range(n)]
        self.assertFalse(request_room(full,'official_corroboration','extra',allocation))
    def test_provider_context_cannot_extend_into_sealed_market_dates(self):
        from src.research.exp004_execution_gaps import price_scope
        price_scope([{'date':'2020-08-03T00:00:00Z'}],'2020-07-31','2020-08-04')
        with self.assertRaises(ValueError):price_scope([{'date':'2021-01-04T00:00:00Z'}],'2020-07-31','2020-08-04')
