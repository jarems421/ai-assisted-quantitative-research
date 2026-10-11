import unittest
from datetime import datetime, timezone

from src.research.cohorts_exp002 import asof_versions, cohort_coverage, institutional_state


class CohortAuditTests(unittest.TestCase):
    def test_later_restatement_cannot_rewrite_earlier_state(self):
        original = {"availableAt": "2015-05-15T03:59:59Z", "kind": "ORIGINAL", "holdings": {"stable-A": 10}}
        amendment = {"availableAt": "2015-06-02T03:59:59Z", "kind": "RESTATEMENT", "holdings": {"stable-B": 20}}
        before = datetime(2015, 5, 20, tzinfo=timezone.utc)
        after = datetime(2015, 6, 3, tzinfo=timezone.utc)
        self.assertEqual(institutional_state([original, amendment], before), institutional_state([original], before))
        self.assertEqual(institutional_state([original, amendment], after), {"stable-B": 20})

    def test_missing_and_ambiguous_amendments_fail_closed(self):
        decision = datetime(2015, 6, 3, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            institutional_state([], decision)
        with self.assertRaises(ValueError):
            asof_versions([{"availableAt": None}], decision)
        original = {"availableAt": "2015-05-15T03:59:59Z", "kind": "ORIGINAL", "holdings": {"A": 1}}
        for kind, holdings in [("UNKNOWN", {}), ("NEW HOLDINGS", {"A": 2})]:
            with self.assertRaises(ValueError):
                institutional_state([original, {"availableAt": "2015-06-02T03:59:59Z", "kind": kind, "holdings": holdings}], decision)

    def test_cohort_uses_public_ny_date_deduplicates_managers(self):
        row = {"cik": "1", "periodOfReport": "2014-12-31", "availableAt": "2015-02-15T04:59:59.999Z", "submissionType": "13F-HR"}
        later = dict(row, availableAt="2015-03-02T04:59:59Z")
        result = cohort_coverage([row, later])
        self.assertEqual(result["cohorts"][0]["counts"]["45"], 1)
        self.assertEqual(result["cohorts"][0]["original_managers_public_within_365_days"], 1)

    def test_future_cutoff_and_immature_denominator(self):
        row = {"cik": "1", "periodOfReport": "2020-09-30", "availableAt": "2020-11-14T04:59:59Z", "submissionType": "13F-HR"}
        self.assertEqual(cohort_coverage([row])["cohorts"], [])
        with self.assertRaises(ValueError):
            cohort_coverage([dict(row, availableAt="2021-01-02T04:59:59Z")])


if __name__ == "__main__":
    unittest.main()
