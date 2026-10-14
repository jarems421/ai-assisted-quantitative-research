import unittest
from src.research.exp004_supplement import allowed_call

class SupplementTests(unittest.TestCase):
    def test_exact_Lake_allowlist_does_not_lift_backtest_pause(self):
        q={'query':'fake','params':['2015-01-01','2020-12-31']}
        self.assertTrue(allowed_call('POST','lake/queries',q,[q],set()))
        self.assertTrue(allowed_call('GET','lake/queries/id/parts/0',None,[],{'id'}))
        for method,path,body in [('POST','backtests',q),('POST','custom-indicators',q),('GET','lake/queries/other',None),('POST','lake/queries',dict(q,query='changed'))]:
            with self.assertRaises(ValueError):allowed_call(method,path,body,[q],{'id'})
