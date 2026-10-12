import unittest
import numpy as np
from src.research.phase3er.inference import evaluate,student_survival,critical,summarize
from src.research.phase3er.geometry import triples,window_geometry
from src.research.phase3er import inference as frozen
from src.research.phase3er import inference_correction as corrected


class RedesignInferenceTests(unittest.TestCase):
    def test_generator_correction_is_analytic_and_non_ar_unchanged(self):
        geo={'confirmation_geometry':[{'annual_groups':[{'sessions':252},{'sessions':250},{'sessions':187}]}]}
        for world in ['iid','ar05','persistent098']:
            original,counts=frozen.synthetic(np.random.default_rng(4),geo,world,.025,'mixed_common',20)
            actual,same=corrected.synthetic(np.random.default_rng(4),geo,world,.025,'mixed_common',20)
            factor=1 if world=='iid' else np.sqrt(1-(.5 if world=='ar05' else .98)**2)
            np.testing.assert_allclose(actual,original*factor,rtol=1e-12,atol=1e-14)
            self.assertEqual(counts,same)
    def test_failed_correction_run_restores_frozen_generator(self):
        original=frozen.synthetic
        with self.assertRaises(ValueError):corrected.calibrate({'seed':0},[])
        self.assertIs(frozen.synthetic,original)
    def test_student_reference_and_unequal_session_weights(self):
        self.assertAlmostEqual(student_survival(1,1),.25,places=12)
        self.assertAlmostEqual(critical(4),2.7764451051977987,places=9)
        x=np.array([[.01,.03,.05]]*4);counts=[252,250,188]
        result=evaluate(x,counts)['session_weighted_group_student']
        self.assertAlmostEqual(result['mean'][0],np.average(x[0],weights=counts))
        self.assertNotAlmostEqual(result['mean'][0],x[0].mean())
        positive=evaluate(x+.1,counts)['session_weighted_group_student']
        self.assertLess(positive['p'][0],result['p'][0])
    def test_sign_discreteness_and_unbounded95_cannot_advance(self):
        x=np.array([[[.03,.04,.05,.06,.07]]*4])
        result=evaluate(x,[252]*5)['symmetric_group_sign']
        self.assertEqual(result['p'][0,0],1/32)
        summary=summarize(result,.05,[0,.005,.002,.01],1)
        self.assertEqual(summary['primary_rejection']['hits'],1)
        self.assertEqual(summary['full_support']['hits'],0)
        self.assertIsNone(summary['mean_interval_width'])
    def test_zero_variance_nan_and_missing_groups_fail_closed(self):
        result=evaluate(np.zeros((1,4,3)),[252]*3)['session_weighted_group_student']
        self.assertEqual(result['p'][0,0],1)
        self.assertFalse(result['valid'][0,0])
        with self.assertRaises(ValueError):evaluate(np.full((4,3),np.nan),[252]*3)
        with self.assertRaises(ValueError):evaluate(np.zeros((4,2)),[252]*3)
    def test_metadata_gap_and_clock_failure_do_not_create_a_state(self):
        rows=[{'case_key':'synthetic','accession':str(i),'report_date':d,'filing_date':f,'status':status,
               'mechanical_bound_utc':f+'T14:30:00+00:00' if status=='INVARIANT' else None}
              for i,d,f,status in [(0,'2018-12-31','2019-03-01','INVARIANT'),(1,'2019-12-31','2020-03-02','INVARIANT'),(2,'2020-12-31','2021-03-01','UNAVAILABLE')]]
        state=triples(rows)[0]
        self.assertFalse(state['mechanically_available']);self.assertIsNone(state['mechanical_bound_utc'])
        out=window_geometry(['2021-03-01','2021-03-31'],[state],rows)
        self.assertEqual(out['monthly_panel'][0]['mechanically_available_issuers'],0)
        self.assertEqual(out['monthly_panel'][0]['fixed_issuer_denominator'],30)
