import unittest
from src.research.exp004_vpg_identity import verdict,OLD_ID,NEW_ID

class VPGIdentityTests(unittest.TestCase):
    def rows(self):
        a={'ticker':'VPG','cik':'1','asset_type':'CS','share_class_figi':'class','from_date':'2010-07-07','to_date':'2020-12-31','security_id':OLD_ID}
        b=dict(a,security_id=NEW_ID)
        predecessor=dict(a,ticker='VSHw',cik='other',share_class_figi=None,from_date='2010-06-24',to_date='2010-07-06')
        return [a],[b,predecessor]
    def test_suffix_alone_cannot_establish_namespace_drift(self):
        a,b=self.rows();self.assertNotEqual(verdict(a,b[:1])['verdict'],'VPG_SAME_SECURITY_NAMESPACE_DRIFT')
        self.assertEqual(verdict(a,b)['verdict'],'VPG_SAME_SECURITY_NAMESPACE_DRIFT')
    def test_class_issuer_overlap_or_competing_record_blocks(self):
        a,b=self.rows()
        for field,value in [('cik','1'),('to_date','2010-07-08')]:
            altered=[dict(r) for r in b];altered[1][field]=value
            self.assertNotEqual(verdict(a,altered)['verdict'],'VPG_SAME_SECURITY_NAMESPACE_DRIFT')
        self.assertEqual(verdict(a,b+[dict(b[0])])['verdict'],'VPG_DISTINCT_OR_AMBIGUOUS_SECURITY')
        altered=[dict(r) for r in b];altered[0]['share_class_figi']='other'
        self.assertNotEqual(verdict(a,altered)['verdict'],'VPG_SAME_SECURITY_NAMESPACE_DRIFT')
