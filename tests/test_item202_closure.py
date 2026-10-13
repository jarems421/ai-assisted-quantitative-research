import copy
from datetime import datetime
import json
from pathlib import Path
import unittest

from src.research.item202_closure import RULE, availability_gate, illustrative_open, require_availability
from src.research.spec import digest


class Item202ClosureTests(unittest.TestCase):
    def test_next_open_strictly_excludes_filing_date(self):
        self.assertEqual(illustrative_open('2015-01-05', ['2015-01-05', '2015-01-06'], synthetic=True),
                         '2015-01-06T14:30:00+00:00')

    def test_weekend_and_full_day_holiday_calendar(self):
        # Public synthetic dates exclude Friday's observed Independence Day closure.
        sessions = ['2020-07-02', '2020-07-06', '2020-07-07']
        for filed in ('2020-07-02', '2020-07-03', '2020-07-04', '2020-07-05'):
            self.assertEqual(illustrative_open(filed, sessions, synthetic=True), '2020-07-06T13:30:00+00:00')

    def test_dst_changes_open_utc_without_changing_local_rule(self):
        sessions = ['2020-03-06', '2020-03-09']
        self.assertEqual(illustrative_open('2020-03-05', sessions, synthetic=True), '2020-03-06T14:30:00+00:00')
        self.assertEqual(illustrative_open('2020-03-06', sessions, synthetic=True), '2020-03-09T13:30:00+00:00')

    def test_adjusted_date_can_make_rule_precede_acceptance(self):
        opened = illustrative_open('2015-01-05', ['2015-01-05', '2015-01-06', '2015-01-07'], synthetic=True)
        delayed_acceptance = '2015-01-07T16:00:00+00:00'
        self.assertLess(datetime.fromisoformat(opened), datetime.fromisoformat(delayed_acceptance))
        c = {'rule': RULE, 'owner_approved': True, 'source_semantics': {
            'filed_date_no_earlier_than_acceptance_certified': False,
            'earlier_date_adjustment_documented': True}}
        with self.assertRaisesRegex(ValueError, 'AVAILABILITY_BLOCKED'):
            require_availability(c)

    def test_approval_and_missing_evidence_do_not_activate_policy(self):
        c = {'rule': RULE, 'owner_approved': True}
        before = copy.deepcopy(c)
        result = availability_gate(c)
        self.assertEqual(result['status'], 'AVAILABILITY_BLOCKED')
        self.assertFalse(result['policy_activated'])
        self.assertIsNone(result['observed_public_available_at_utc'])
        self.assertEqual(c, before)
        with self.assertRaises(ValueError):
            illustrative_open('2015-01-05', ['2015-01-06'])

    def test_calendar_failure_and_rule_substitution_rejected(self):
        for sessions in ([], ['2015-01-05'], ['2015-01-06', '2015-01-06'], ['2015-01-07', '2015-01-06']):
            with self.assertRaises(ValueError):
                illustrative_open('2015-01-05', sessions, synthetic=True)
        with self.assertRaises(ValueError):
            availability_gate({'rule': 'Use max acceptance and filing date instead'})

    def test_public_stop_receipts_retain_unknowns_and_conditional_authority(self):
        docs = Path(__file__).resolve().parents[1] / 'docs/acceleration'
        c = json.loads((docs / 'exp006_availability_contract.json').read_bytes())
        r = json.loads((docs / 'exp006_closure_receipt.json').read_bytes())
        self.assertEqual(digest(c), r['availability_contract_sha256'])
        self.assertEqual(availability_gate(c)['status'], r['status'])
        self.assertFalse(r['scientifically_ready_for_freeze'])
        self.assertFalse(r['EXP006_created'])
        self.assertFalse(r['Development_run'])
        self.assertEqual((r['performance_evaluations'], r['held_out_confirmation_accesses']), (0, 0))
        self.assertIsNone(r['source_coverage']['full_period_Item202_count'])
        self.assertIsNone(r['identity']['unresolved'])
        self.assertEqual(r['parameters']['horizon_regular_sessions'], 20)
        self.assertEqual(r['parameters']['trial_ceiling'], 12)
