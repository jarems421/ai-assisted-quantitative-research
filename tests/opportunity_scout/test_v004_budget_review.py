"""Offline tests for combined accounting, including the old failure counterfactual."""
import unittest

from src.research.opportunity_scout import schema as S, v004_budget_review as B
from src.research.opportunity_scout.storage import ROOT, input_json


class CombinedBudgetReviewTests(unittest.TestCase):
    def usage(self, ordinary=10000, write=10000, read=10000, output=20000):
        return dict(zip(B.COMPONENTS, (ordinary, write, read, output)))

    def test_all_three_input_categories_and_output_count_once(self):
        usage = self.usage()
        usage['cache_creation'] = {'ephemeral_1h_input_tokens': 10000}
        usage['output_tokens_details'] = {'thinking_tokens': 5000}
        result = B.assess_reported_budget(usage)
        self.assertEqual(result['reported_input_total'], 30000)
        self.assertEqual(result['reported_combined_total'], 50000)
        self.assertEqual(result['reported_thinking_subcount'], 5000)
        self.assertEqual(result['budget_status'], 'WITHIN_ALLOWANCE')

    def test_exact_combined_boundary_is_inclusive_and_no_hidden_grace_band(self):
        self.assertEqual(B.assess_reported_budget(self.usage(output=30000))['budget_status'], 'WITHIN_ALLOWANCE')
        result = B.assess_reported_budget(self.usage(output=30001))
        self.assertEqual(result['budget_status'], 'OVER_ALLOWANCE'); self.assertEqual(result['excess_tokens'], 1)

    def test_output_guide_does_not_become_a_new_output_ceiling_or_target(self):
        result = B.assess_reported_budget(self.usage(ordinary=1000, write=0, read=0, output=35000))
        self.assertTrue(result['output_above_planning_guideline'])
        self.assertEqual(result['budget_status'], 'WITHIN_ALLOWANCE')
        self.assertFalse(result['output_guideline_is_compliance_cap'])
        self.assertEqual(B.assess_reported_budget(self.usage(0, 0, 0, 1))['budget_status'], 'WITHIN_ALLOWANCE')

    def test_input_has_no_old_separate_ceiling(self):
        result = B.assess_reported_budget(self.usage(ordinary=45000, write=0, read=0, output=10000))
        self.assertEqual(result['budget_status'], 'WITHIN_ALLOWANCE')

    def test_heavily_cached_consumption_is_not_discounted(self):
        result = B.assess_reported_budget(self.usage(ordinary=0, write=0, read=55000, output=6000))
        self.assertEqual(result['reported_combined_total'], 61000)
        self.assertEqual(result['budget_status'], 'OVER_ALLOWANCE')

    def test_missing_bad_or_noninteger_usage_never_becomes_zero(self):
        for bad in (None, -1, 1.5, True, S.UNKNOWN):
            usage = self.usage(); usage['cache_read_input_tokens'] = bad
            self.assertEqual(B.assess_reported_budget(usage)['budget_status'], 'UNKNOWN')
        usage = self.usage(); usage.pop('output_tokens')
        self.assertEqual(B.assess_reported_budget(usage)['budget_status'], 'UNKNOWN')
        self.assertEqual(B.assess_reported_budget(None)['budget_status'], 'UNKNOWN')

    def test_unknown_thinking_does_not_invalidate_observed_total_output(self):
        result = B.assess_reported_budget(self.usage())
        self.assertEqual(result['reported_thinking_subcount'], S.UNKNOWN)
        self.assertEqual(result['budget_status'], 'WITHIN_ALLOWANCE')

    def test_conflicting_thinking_detail_is_not_silently_normalised(self):
        usage = self.usage(); usage['output_tokens_details'] = {'thinking_tokens': 20001}
        result = B.assess_reported_budget(usage)
        self.assertEqual(result['budget_status'], 'UNKNOWN')
        self.assertIn('THINKING_SUBCOUNT_EXCEEDS_OUTPUT', result['issues'])

    def test_subscription_billing_and_provider_completeness_are_never_inferred(self):
        usage = self.usage(); usage['total_cost_usd'] = 0.8
        result = B.assess_reported_budget(usage)
        self.assertEqual(result['actual_subscription_charge'], S.UNKNOWN)
        self.assertEqual(result['provider_usage_completeness'], S.UNKNOWN)
        self.assertFalse(result['consumption_prevention_verified'])
        self.assertFalse(result['real_generation_authorised'])

    def test_new_allowance_does_not_rehabilitate_historical_V003(self):
        result = B.assess_reported_budget(self.usage(4, 33158, 3924, 10742))
        self.assertEqual(result['reported_combined_total'], 47828)
        self.assertEqual(result['budget_status'], 'WITHIN_ALLOWANCE')
        self.assertFalse(result['real_generation_authorised'])
        # This only evaluates fictional numeric inputs under R2; no ledger IO.

    def test_active_prospective_protocol_and_accounting_do_not_drift(self):
        proposal = input_json(ROOT / 'docs/opportunity_scout/proposed_protocol_v004.json')
        budget = proposal['budget_proposal']
        self.assertEqual(budget['aggregate_combined_tokens_per_attempt'], B.COMBINED_ALLOWANCE)
        self.assertEqual(budget['output_planning_guideline_tokens'], B.OUTPUT_PLANNING_GUIDE)
        self.assertNotIn('aggregate_input_tokens_per_attempt', budget)
        self.assertNotIn('aggregate_output_tokens_per_attempt', budget)
        self.assertFalse(proposal['authority']['real_generation_authorised'])
        self.assertFalse(proposal['authority']['fictional_hosted_probes_authorised'])


if __name__ == '__main__': unittest.main()
