import math
import unittest
from src.research.phase3_final import weighted_moments,witness


class CommonFactorObstructionTests(unittest.TestCase):
    def test_common_component_cancels_from_residual_variance_but_not_mean(self):
        example=witness();base=example['base_mean'];var=example['base_se2']
        for row in example['translations']:
            self.assertAlmostEqual(row['mean'],base+row['synthetic_common_offset'],places=14)
            self.assertAlmostEqual(row['estimated_mean_variance'],var,places=14)
        self.assertFalse(example['translations'][0]['positive_95_lower_endpoint'])
        self.assertTrue(example['translations'][-1]['positive_95_lower_endpoint'])

    def test_unseen_common_variance_enters_weighted_mean_quadratic_form(self):
        n=[251,250,252,250,187];total=sum(n);weights=[x/total for x in n]
        sigma2=.03**2;common2=.04**2
        covariance=[[common2+(sigma2/n[i] if i==j else 0) for j in range(5)] for i in range(5)]
        truevar=sum(weights[i]*weights[j]*covariance[i][j] for i in range(5) for j in range(5))
        self.assertAlmostEqual(truevar,common2+sigma2/total,places=15)
        self.assertGreater(truevar,1000*sigma2/total)

    def test_incomplete_or_nonfinite_group_algebra_fails_closed(self):
        for values,counts in [([0],[1]),([1,2],[1]),([1,math.nan],[1,1]),([1,2],[1,0])]:
            with self.assertRaises(ValueError):weighted_moments(values,counts)
