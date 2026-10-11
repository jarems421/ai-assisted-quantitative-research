"""Synthetic tests only; no Nexus or strategy-performance observations."""
import unittest
from src.research.coverage_exp002 import summarize


class CoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.prices = [{"security_id": "one", "ticker": "NEW", "day": "2016-01-29",
                        "cap_present": True, "cap_lineage": True, "cap_threshold": True,
                        "prior_price_bars": 252, "prior_volume_bars": 20,
                        "price_threshold": True, "proposed_adv": 11_000_000}]
        self.spans = [{"ticker": "OLD", "security_id": "one",
                       "bounded_from_date": "2015-01-01", "bounded_to_date": "2015-12-31"}]

    def test_absent_source_is_not_verified_zero_or_usable_coverage(self):
        result = summarize(self.prices, [], self.spans)
        month = result["monthly_coverage"][0]
        self.assertEqual(month["source_presence_percentages"]["joint_source_presence_ids"], 0)
        self.assertIsNone(month["verified_usable_joint_count"])

    def test_rename_joins_source_by_identity_and_staleness_expires(self):
        owned = [{"dataset": "insider", "ticker": "OLD",
                  "last_availableAt": "2015-12-20T04:59:59Z"}]
        result = summarize(self.prices, owned, self.spans)
        self.assertEqual(result["monthly_coverage"][0]["source_counts"]["insider_source_presence_ids"], 1)
        owned[0]["last_availableAt"] = "2015-01-20T04:59:59Z"
        result = summarize(self.prices, owned, self.spans)
        self.assertEqual(result["monthly_coverage"][0]["source_presence_percentages"]["insider_source_presence_ids"], 0)

    def test_ended_price_is_excluded_and_duplicate_month_is_rejected(self):
        old = dict(self.prices[0], security_id="ended", day="2016-01-08")
        result = summarize(self.prices + [old], [], self.spans)
        self.assertEqual(result["monthly_coverage"][0]["source_counts"]["common_stock_price_ids"], 1)
        self.assertEqual(result["identity_and_snapshot_issues"]["excluded_earlier_last_price_security_months"], 1)
        with self.assertRaises(ValueError):
            summarize(self.prices * 2, [], self.spans)

    def test_cutoff_and_ambiguous_identity_fail_closed(self):
        owned = [{"dataset": "insider", "ticker": "OLD",
                  "last_availableAt": "2021-01-02T00:00:00Z"}]
        with self.assertRaises(ValueError):
            summarize(self.prices, owned, self.spans)
        owned[0]["last_availableAt"] = "2015-12-20T04:59:59Z"
        result = summarize(self.prices, owned, self.spans + [dict(self.spans[0], security_id="other")])
        self.assertEqual(result["identity_and_snapshot_issues"]["unresolved_or_ambiguous_ownership_identity_rows"], 1)
