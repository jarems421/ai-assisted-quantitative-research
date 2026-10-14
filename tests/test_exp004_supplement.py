import unittest
from src.research.exp004_supplement import allowed_call

class SupplementTests(unittest.TestCase):
    def frames(self):
        import pyarrow as pa
        from datetime import date
        return pa.table({'ticker':['OLD'],'day':[date(2020,1,2)],'security_id':['A'],'unadjustedClose':[10.0]})
    def test_exact_keys_and_CLOSE_do_not_accept_equal_count_substitution(self):
        import pyarrow as pa
        from src.research.exp004_supplement_qa import reconcile_frames
        old=self.frames();self.assertEqual(reconcile_frames(old,old)['status'],'PASS_EXACT_KEYS_AND_CLOSE')
        new=old.set_column(0,'ticker',pa.array(['NEW']))
        result=reconcile_frames(old,new)
        self.assertEqual(result['missing_keys'],1);self.assertEqual(result['close_row_mismatches'],0)
        self.assertEqual(result['close_compared_rows'],0)
        new=old.set_column(3,'unadjustedClose',pa.array([10.00001]))
        self.assertEqual(reconcile_frames(old,new)['close_row_mismatches'],1)
    def test_open_missing_nonpositive_and_nonfinite_fail_closed(self):
        from src.research.exp004_supplement_qa import opens
        self.assertEqual(opens([10.,None,0.,-1.,float('nan')]),{'required':5,'valid':1,'missing':1,'invalid':3})
    def test_exact_Lake_allowlist_does_not_lift_backtest_pause(self):
        q={'query':'fake','params':['2015-01-01','2020-12-31']}
        self.assertTrue(allowed_call('POST','lake/queries',q,[q],set()))
        self.assertTrue(allowed_call('GET','lake/queries/id/parts/0',None,[],{'id'}))
        for method,path,body in [('POST','backtests',q),('POST','custom-indicators',q),('GET','lake/queries/other',None),('POST','lake/queries',dict(q,query='changed'))]:
            with self.assertRaises(ValueError):allowed_call(method,path,body,[q],{'id'})
