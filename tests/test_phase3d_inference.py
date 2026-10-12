import unittest
import numpy as np
from src.research.phase3d.inference import exact_p,confidence_set,test,METHODS
from src.research.phase3c.inference import synthetic_windows
from src.research.analysis import holm


class InferenceTests(unittest.TestCase):
    def test_exact_enumeration_discreteness_and_holm_power_ceiling(self):
        for n in (2,6):
            p=exact_p(np.ones(n)); self.assertEqual(p,1/2**n)
            self.assertFalse(any(r['reject'] for r in holm({k:p for k in ('base','double_cost','delay1','delay5')},alpha=.05).values()))
            self.assertEqual(exact_p(-np.ones(n)),1)

    def test_inversion_coverage_under_all_sign_assignments(self):
        from itertools import product
        values=np.arange(1,7)/10
        rejected=0
        for row in product((-1,1),repeat=6): rejected+=exact_p(values*np.array(row),two_sided=True)<=.05
        self.assertLessEqual(rejected/64,.05)
        confidence=confidence_set(np.ones(2))
        self.assertEqual(confidence['accepted_intervals'][0]['lower'],None)
        self.assertEqual(confidence['accepted_intervals'][-1]['upper'],None)

    def test_paired_alignment_dependence_scope_and_determinism(self):
        x=np.random.default_rng(999).normal(0,.01,1512); w=synthetic_windows(x)
        for method in METHODS: self.assertEqual(test(w,method),test(w,method))
        with self.assertRaises(ValueError): test(w,'chosen_after_results')
        w[0]['strategy'][0]=None
        with self.assertRaises(ValueError): test(w,METHODS[0])
