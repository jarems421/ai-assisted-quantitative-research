import unittest
import pyarrow as pa
from datetime import date
from src.research.exp004_frozen_price_bridge import enrich

class FrozenPriceBridgeTests(unittest.TestCase):
    def frames(self):
        f=pa.table({'ticker':['VPG'],'day':[date(2014,1,2)],'security_id':['frozen'],'unadjustedClose':[10.]})
        s=pa.table({'ticker':['VPG'],'day':[date(2014,1,2)],'openingPrice':[9.],'unadjustedClose':[10.]})
        return f,s
    def test_enrichment_retains_frozen_identity_and_excludes_source_extra(self):
        f,s=self.frames();extra=s.set_column(0,'ticker',pa.array(['EXTRA']))
        q,r=enrich(f,pa.concat_tables([s,extra]));self.assertEqual(q['status'],'PASS_FROZEN_PRICE_ENRICHMENT')
        self.assertEqual(q['unused_source_extras'],1);self.assertEqual(r['security_id'].to_pylist(),['frozen'])
    def test_duplicate_and_missing_rows_fail(self):
        f,s=self.frames()
        self.assertEqual(enrich(f,pa.concat_tables([s,s]))[0]['status'],'PRICE_KEY_AMBIGUITY_BLOCKED')
        self.assertEqual(enrich(f,s.slice(0,0))[0]['missing'],1)
    def test_exact_close_and_positive_open_required(self):
        f,s=self.frames()
        self.assertEqual(enrich(f,s.set_column(3,'unadjustedClose',pa.array([10.01])))[0]['CLOSE_mismatches'],1)
        self.assertEqual(enrich(f,s.set_column(2,'openingPrice',pa.array([0.])))[0]['status'],'LOCAL_EXECUTION_INPUTS_BLOCKED')
    def test_price_only_plan_excludes_identity_join_and_sealed_dates(self):
        import json
        from src.research.spec import ROOT
        plan=json.loads((ROOT/'docs/acceleration/exp004_frozen_price_acquisition_plan_v001.json').read_bytes())
        self.assertEqual(len(plan['requests']),27)
        for row in plan['requests']:
            query=row['request']['query'].lower()
            self.assertNotIn('security_segments',query);self.assertNotIn('security_id',query)
            self.assertTrue('2013-12-31'<=row['request']['params'][0]<=row['request']['params'][1]<='2020-12-31')
    def test_all_frozen_rows_enriched_does_not_imply_execution_day_exists(self):
        from src.research.exp004_frozen_price_bridge import execution_open_coverage
        f,s=self.frames();q,enriched=enrich(f,s)
        self.assertEqual(q['status'],'PASS_FROZEN_PRICE_ENRICHMENT')
        required=f.select(['ticker','day','security_id']).set_column(1,'day',pa.array([date(2014,1,3)]))
        coverage=execution_open_coverage(required,enriched)
        self.assertEqual(coverage['missing'],1);self.assertEqual(coverage['status'],'LOCAL_EXECUTION_INPUTS_BLOCKED')
