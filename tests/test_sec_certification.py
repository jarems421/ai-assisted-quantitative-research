import copy
from datetime import date
import unittest
from src.research.sec_pilot.certification import acceptance, local_time, proposed_bound, policy_view, resolve_class, semantic
from src.research.sec_pilot.parsing import digest


class TimestampTests(unittest.TestCase):
    def test_est_edt_after_hours_and_unresolved_are_separate(self):
        january = acceptance('20200129211214', evidence_sha256='a'*64)
        self.assertEqual(january['accepted_at_utc'], '2020-01-30T02:12:14+00:00')
        october = acceptance('20201029180625', evidence_sha256='a'*64)
        self.assertIsNone(october['accepted_at_utc'])
        self.assertNotEqual(october['candidate_eastern_utc'], october['candidate_literal_est_utc'])
        self.assertIsNone(october['public_available_at_utc'])
        self.assertEqual(local_time('20200309183000')[1].hour, 22)

    def test_invalid_nonexistent_and_ambiguous_wall_times_rejected(self):
        for raw in ('20201101013000', '20200308023000', '20200230090000', 'bad', '20201301000000'):
            with self.assertRaises(ValueError): local_time(raw)

    def test_weekend_holiday_buffer_and_calendar_failure(self):
        days = [date(2020, 7, 2), date(2020, 7, 6), date(2020, 7, 7)]
        self.assertEqual(proposed_bound('20200702183000', '2020-07-02', days), '2020-07-07T13:30:00+00:00')
        with self.assertRaises(ValueError): proposed_bound('20200702183000', '2020-07-02', days[:2])


class PolicyTests(unittest.TestCase):
    def setup_data(self):
        policy = {'status': 'PROPOSED_NOT_APPROVED', 'version': 'synthetic'}
        fact = {'fact_key': 'EXP999', 'semantic_status': 'CERTIFIED_FOR_SCOPED_FACTS', 'identity_status': 'CERTIFIED', 'security_id': 'EXP999',
                'public_available_at_utc': None, 'contributors': [{'acceptance_status': 'CERTIFIED', 'source_sha256': 'synthetic',
                'accepted_at_utc': '2020-01-01T00:00:00Z', 'policy_sha256': digest(policy),
                'proposed_eligibility_at_utc': '2020-01-06T14:30:00Z', 'public_available_at_utc': None}]}
        facts = [fact]; approval = {'status': 'OWNER_APPROVED', 'policy_sha256': digest(policy),
                                   'snapshot_sha256': digest(facts), 'authority_artifact_sha256': 'a'*64}
        return policy, facts, approval

    def test_no_unapproved_policy_admits_facts_and_unknown_stays_unknown(self):
        p, f, a = self.setup_data(); old = copy.deepcopy(f)
        self.assertEqual(policy_view(f, '2020-02-01T00:00:00Z', snapshot_sha256=digest(f), policy=p)['usable'], [])
        self.assertEqual(len(policy_view(f, '2020-02-01T00:00:00Z', snapshot_sha256=digest(f), policy=p, approval=a)['usable']), 1)
        self.assertEqual(f, old); self.assertIsNone(f[0]['public_available_at_utc'])

    def test_all_contributors_future_and_pinned_approvals(self):
        p, f, a = self.setup_data()
        before = policy_view(f, '2020-02-01T00:00:00Z', snapshot_sha256=digest(f), policy=p, approval=a)
        new = copy.deepcopy(f); new[0]['contributors'].append(dict(new[0]['contributors'][0], proposed_eligibility_at_utc='2020-03-01T00:00:00Z'))
        new_a = dict(a, snapshot_sha256=digest(new))
        self.assertEqual(policy_view(new, '2020-02-01T00:00:00Z', snapshot_sha256=digest(new), policy=p, approval=new_a)['usable'], [])
        self.assertEqual(policy_view(f, '2020-02-01T00:00:00Z', snapshot_sha256=digest(f), policy=p, approval=a), before)
        with self.assertRaises(ValueError): policy_view(new, '2020-02-01T00:00:00Z', snapshot_sha256=digest(f), policy=p)


class ClassTests(unittest.TestCase):
    def row(self, **fields):
        return dict({'issuer_cik': '999', 'class': 'A', 'start': '2019-01-01T00:00:00Z', 'end': '2020-01-01T00:00:00Z',
                     'ticker': 'OLD', 'security_id': 'EXP999-A', 'source_sha256': 'synthetic', 'status': 'CERTIFIED'}, **fields)

    def test_classes_rename_reuse_delisting_merger_overlap_and_missing(self):
        rows = [self.row(), self.row(**{'class': 'B', 'security_id': 'EXP999-B'}),
                self.row(start='2020-01-01T00:00:00Z', end='2020-06-01T00:00:00Z', ticker='NEW'),
                self.row(issuer_cik='888', security_id='OTHER')]
        self.assertEqual(resolve_class(rows, '999', 'A', '2019-05-01T00:00:00Z')['security_id'], 'EXP999-A')
        self.assertEqual(resolve_class(rows, '999', 'A', '2020-05-01T00:00:00Z')['ticker'], 'NEW')
        self.assertEqual(resolve_class(rows, '999', 'A', '2020-07-01T00:00:00Z')['status'], 'UNAVAILABLE')
        for bad in ([self.row(), self.row()], [self.row(source_sha256=None)], [self.row(corporate_action_unresolved=True)], []):
            self.assertEqual(resolve_class(bad, '999', 'A', '2019-05-01T00:00:00Z')['status'], 'UNAVAILABLE')


class SemanticTests(unittest.TestCase):
    def fixture(self):
        return {'fixture': {'issuer_cik': '0000000999'}, 'report_period_raw': '20191231', 'facts': [
            {'concept': 'NetIncomeLoss', 'namespace': 'http://fasb.org/us-gaap/2019', 'exact_value': '0', 'decimals': '0',
             'unit_xml': '<unit xmlns="http://www.xbrl.org/2003/instance" xmlns:iso="http://www.xbrl.org/2003/iso4217"><measure>iso:USD</measure></unit>',
             'context': {'entity': {'identifier': '0000000999'}, 'dimensions': {}, 'period': {'type': 'duration', 'startDate': '2019-01-01', 'endDate': '2019-12-31'}},
             'status': 'OBSERVED_SOURCE', 'nil': False, 'fact_locator': 'synthetic'}]}

    def test_annual_zero_and_identical_duplicates_retained(self):
        s = self.fixture(); s['facts'].append(dict(s['facts'][0], fact_locator='duplicate'))
        self.assertEqual(semantic(s, 'Net income')['candidate_count'], 2)
        self.assertEqual(semantic(s, 'Net income')['status'], 'SELECTED_PENDING_PRIMARY_RECONCILIATION')

    def test_segments_comparatives_units_missing_and_conflicts_fail(self):
        s = self.fixture(); s['facts'][0]['context']['dimensions'] = {'product': 'phone'}
        self.assertEqual(semantic(s, 'Net income')['status'], 'UNAVAILABLE')
        s = self.fixture(); s['facts'].append(dict(s['facts'][0], exact_value='5', fact_locator='conflict'))
        self.assertEqual(semantic(s, 'Net income')['status'], 'AMBIGUOUS')
        s = self.fixture(); s['facts'][0]['context']['period']['endDate'] = '2018-12-31'
        self.assertEqual(semantic(s, 'Net income')['status'], 'UNAVAILABLE')
        self.assertEqual(semantic(self.fixture(), 'Revenue')['status'], 'UNAVAILABLE')
