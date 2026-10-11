import copy
import unittest
from src.research.sec_pilot.parsing import digest
from src.research.sec_pilot.provenance import asof, binding, instant


def snapshot(facts):
    s = {'facts': facts}; s['snapshot_sha256'] = digest(s); return s


def fact(**kwargs):
    return dict({'fact_locator': 'synthetic', 'status': 'OBSERVED_SOURCE', 'source_sha256': 'synthetic-source',
                 'public_available_at_utc': '2020-01-02T14:00:00Z', 'availability_status': 'VERIFIED',
                 'approved_eligibility_at_utc': '2020-01-02T15:00:00Z', 'eligibility_policy_sha256': 'synthetic-policy',
                 'identity_status': 'VERIFIED', 'security_id': 'EXP999'}, **kwargs)


class ProvenanceTests(unittest.TestCase):
    def test_unknown_missing_ambiguous_and_future_fail_closed(self):
        for fields in ({'public_available_at_utc': None}, {'approved_eligibility_at_utc': None},
                       {'identity_status': 'UNRESOLVED'}, {'status': 'AMBIGUOUS'}, {'status': 'UNAVAILABLE'},
                       {'public_available_at_utc': '2021-01-01T00:00:00Z'}):
            s = snapshot([fact(**fields)])
            self.assertEqual(asof(s, '2020-02-01T00:00:00Z', snapshot_sha256=s['snapshot_sha256'])['usable'], [])

    def test_later_amendment_and_metadata_cannot_mutate_pinned_snapshot(self):
        old = snapshot([fact()]); at = '2020-02-01T00:00:00Z'
        before = asof(old, at, snapshot_sha256=old['snapshot_sha256'])
        new = snapshot([fact(), fact(fact_locator='amendment', public_available_at_utc='2020-03-01T00:00:00Z')])
        self.assertEqual(asof(old, at, snapshot_sha256=old['snapshot_sha256']), before)
        self.assertEqual(len(asof(new, at, snapshot_sha256=new['snapshot_sha256'])['usable']), 1)
        tampered = copy.deepcopy(old); tampered['facts'][0]['public_available_at_utc'] = '2019-01-01T00:00:00Z'
        with self.assertRaises(ValueError): asof(tampered, at, snapshot_sha256=old['snapshot_sha256'])

    def test_class_ambiguity_rename_reuse_end_and_missing(self):
        def row(sid, ticker, start, end=None):
            return dict(issuer_cik='999', security_id=sid, ticker=ticker, effective_from=start,
                        effective_to=end, status='VERIFIED', evidence_sha256='synthetic')
        rows = [row('one', 'OLD', '2019-01-01T00:00:00Z', '2020-01-01T00:00:00Z'),
                row('one', 'NEW', '2020-01-01T00:00:00Z', '2020-06-01T00:00:00Z')]
        self.assertEqual(binding(rows, '999', '2019-06-01T00:00:00Z')['ticker'], 'OLD')
        self.assertEqual(binding(rows, '999', '2020-02-01T00:00:00Z')['ticker'], 'NEW')
        self.assertEqual(binding(rows, '999', '2020-07-01T00:00:00Z')['status'], 'UNAVAILABLE')
        rows.append(row('two', 'NEW', '2020-01-01T00:00:00Z'))
        self.assertEqual(binding(rows, '999', '2020-02-01T00:00:00Z')['status'], 'UNAVAILABLE')
        self.assertEqual(binding([], '999', '2020-02-01T00:00:00Z')['status'], 'UNAVAILABLE')

    def test_dst_after_hours_and_naive_timestamp(self):
        self.assertEqual(instant('2020-03-09T18:30:00-04:00').hour, 22)
        self.assertEqual(instant('2020-01-09T18:30:00-05:00').hour, 23)
        with self.assertRaises(ValueError): instant('2020-01-09T18:30:00')
