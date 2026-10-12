import copy
from datetime import date
import json
from pathlib import Path
import unittest

from src.nexus.process_exp001 import session_dates
from src.research.sec_pilot.planning import ambiguity_probe


class Phase3BPlanningTests(unittest.TestCase):
    def test_archived_timestamp_candidates_preserve_unknowns_and_policy(self):
        evidence = json.loads(Path('docs/acceleration/phase3a_evidence.json').read_bytes())
        before = copy.deepcopy(evidence)
        sessions = sorted(session_dates(date(2019, 1, 1), date(2020, 12, 31)))
        expected_opens = ['2019-11-04T14:30:00+00:00', '2020-11-03T14:30:00+00:00',
                          '2020-02-03T14:30:00+00:00']
        for row, expected in zip(evidence['acceptance_interpretations'], expected_opens, strict=True):
            raw = row['raw']
            p = ambiguity_probe(raw, row['filing_date'], sessions,
                                evidence_sha256=row['evidence_sha256'])
            self.assertTrue(p['calendar_invariant'])
            self.assertEqual(p['raw_rule_bound_utc'], expected)
            self.assertIsNone(p['public_available_at_utc'])
            self.assertFalse(p['policy_approved'])
            if raw.startswith('201910') or raw.startswith('202010'):
                self.assertIsNone(p['certified_acceptance_utc'])
                self.assertEqual(p['acceptance_status'], 'PARTIAL')
        self.assertEqual(evidence, before)

    def test_midnight_counterexample_and_filing_date_mask(self):
        sessions = sorted(session_dates(date(2020, 10, 1), date(2020, 11, 15)))
        # Literal EST candidate becomes next-day seasonal New York civil time.
        p = ambiguity_probe('20201029233000', '2020-10-29', sessions, evidence_sha256='a' * 64)
        self.assertFalse(p['calendar_invariant'])
        self.assertFalse(p['candidate_chronology_valid'])
        self.assertNotEqual(*p['candidate_bounds_utc'])
        p = ambiguity_probe('20201029233000', '2020-10-30', sessions, evidence_sha256='a' * 64)
        self.assertTrue(p['calendar_invariant'])

    def test_holiday_dst_and_invalid_calendar_fail_closed(self):
        sessions = sorted(session_dates(date(2020, 7, 1), date(2020, 7, 10)))
        p = ambiguity_probe('20200702183000', '2020-07-02', sessions, evidence_sha256='a' * 64)
        self.assertTrue(p['calendar_invariant'])
        self.assertEqual(p['raw_rule_bound_utc'], '2020-07-07T13:30:00+00:00')
        for days in (sessions[:1], sessions + [sessions[0]]):
            with self.assertRaises(ValueError):
                ambiguity_probe('20200702183000', '2020-07-02', days, evidence_sha256='a' * 64)
        with self.assertRaises(ValueError):
            ambiguity_probe('20201101013000', '2020-11-01', sessions, evidence_sha256='a' * 64)
