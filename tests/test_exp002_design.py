import unittest
from src.research.design_exp002 import evaluation_plan


class DesignPlanTests(unittest.TestCase):
    def test_ablation_families_do_not_repeat_irrelevant_axes(self):
        plan = evaluation_plan({"momentum_lookback_calendar_days": [180, 365], "insider_lookback_calendar_days": [30, 90], "number_of_holdings": [20, 40]})
        self.assertEqual(plan["family_cells"]["institutional"], 2)
        self.assertEqual(plan["family_cells"]["full_composite"], 8)
        self.assertEqual(sum(plan["family_cells"].values()), 34)
        self.assertEqual(plan["components"]["development_grid_folds"], 180)
        self.assertEqual(plan["projected_ceiling_with_reserve"], 281)

    def test_undeclared_axis_and_duplicate_values_are_rejected(self):
        ranges = {"momentum_lookback_calendar_days": [180, 365], "insider_lookback_calendar_days": [30, 90], "number_of_holdings": [20, 40]}
        with self.assertRaises(ValueError):
            evaluation_plan(dict(ranges, liquidity=[10000000, 25000000]))
        with self.assertRaises(ValueError):
            evaluation_plan(dict(ranges, number_of_holdings=[20, 20]))
