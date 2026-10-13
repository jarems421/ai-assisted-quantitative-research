from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import unittest
import gzip
import io
import tarfile

from src.research.item202_date_bound import (envelope, second_open, compare, confusion,
    primary_item202, exact_header_reconciliation, freeze_before_performance)


class DateBoundTests(unittest.TestCase):
    def setUp(self):
        self.days = [date(2015, 1, 1) + timedelta(days=i) for i in range(2192)
                     if (date(2015, 1, 1) + timedelta(days=i)).weekday() < 5]

    def check(self, iso, raw, filed='2020-06-01'):
        return compare(iso, filed, raw, filed.replace('-', ''), self.days, evidence_sha256='a'*64)

    def test_lexical_and_literal_dates_are_separate(self):
        e = envelope('2020-06-02T00:30:00Z', '2020-06-01')
        self.assertEqual(e['lexical_date'], '2020-06-02')
        self.assertEqual(e['literal_New_York_date'], '2020-06-01')
        self.assertEqual(e['envelope_date'], '2020-06-02')

    def test_explicit_offset_and_max_filed_adjustment(self):
        self.assertEqual(envelope('2020-06-01T23:30:00-08:00', '2020-06-01')['envelope_date'], '2020-06-02')
        self.assertEqual(envelope('2020-06-01T08:30:00Z', '2020-06-03')['envelope_date'], '2020-06-03')

    def test_invalid_or_missing_iso_fails_closed(self):
        for value in (None, '', '2020-06-01T12:00:00', '2020-13-01T12:00:00Z', '2020-06-01'):
            with self.assertRaises(ValueError): envelope(value, '2020-06-01')

    def test_confirmation_cannot_enter_envelope(self):
        with self.assertRaises(ValueError): envelope('2021-01-01T12:00:00Z', '2021-01-01')

    def test_same_day_equal_open_and_unknown_public_time(self):
        r = self.check('2020-06-01T18:00:00Z', '20200601140000')
        self.assertEqual(r['status'], 'PASS_DATE_DOMINANCE')
        self.assertEqual(r['delay_sessions'], 0)
        self.assertIsNone(r['exact_public_available_at_utc'])
        self.assertFalse(r['exact_clock_reconstructed'])
        self.assertFalse(r['policy_activated'])

    def test_later_envelope_is_conservative_latency(self):
        r = self.check('2020-06-02T00:30:00Z', '20200601203000')
        self.assertEqual(r['status'], 'PASS_DATE_DOMINANCE')
        self.assertEqual(r['delay_sessions'], 1)

    def test_raw_later_than_envelope_is_failure_not_correction(self):
        r = self.check('2020-06-01T12:00:00Z', '20200602120000')
        self.assertEqual(r['status'], 'FAIL_DATE_DOMINANCE')
        self.assertTrue(r['raw_date_later_than_envelope'])
        self.assertTrue(r['earlier_eligible_open'])

    def test_raw_midnight_candidates_not_collapsed(self):
        r = self.check('2020-06-02T00:30:00Z', '20200601233000')
        self.assertEqual(r['raw_candidate_civil_dates'], ['2020-06-01', '2020-06-02'])
        self.assertFalse(r['raw_v002_invariant'])
        self.assertEqual(r['status'], 'PASS_DATE_DOMINANCE')

    def test_filed_conflict_and_missing_header_unavailable(self):
        for raw, filed in ((None, '20200601'), ('20200601120000', '20200602')):
            r = compare('2020-06-01T12:00:00Z', '2020-06-01', raw, filed, self.days, evidence_sha256='a'*64)
            self.assertEqual(r['status'], 'UNAVAILABLE')

    def test_earlier_official_filed_date_cannot_advance_raw_anchor(self):
        r = self.check('2020-06-02T14:00:00Z', '20200602100000')
        self.assertEqual(r['status'], 'PASS_DATE_DOMINANCE')
        self.assertEqual(r['raw_anchor_date'], '2020-06-02')

    def test_dst_and_holiday(self):
        self.assertEqual(second_open('2020-03-06', self.days), '2020-03-10T13:30:00+00:00')
        days = [d for d in self.days if d != date(2020, 7, 3)]
        self.assertEqual(second_open('2020-07-02', days), '2020-07-07T13:30:00+00:00')

    def test_monotonicity_over_all_synthetic_calendar_anchors(self):
        for day in self.days[2:-5]:
            a = second_open(day, self.days)
            b = second_open(day + timedelta(days=1), self.days)
            self.assertLessEqual(a, b)

    def test_missing_or_corrupt_calendar_unavailable(self):
        for days in ([], self.days[::-1], self.days[-3:]):
            with self.assertRaises(ValueError): second_open('2020-06-01', days)

    def test_all_confusion_cells_and_unknown(self):
        rows = [{'bulk_present': a, 'primary_present': b} for a, b in
                ((True, True), (False, False), (True, False), (False, True), (False, None))]
        c = confusion(rows)
        self.assertEqual([c[x] for x in ('TP','TN','FP','FN','UNKNOWN')], [1]*5)
        self.assertEqual(c['coverage'], .8)

    def test_primary_heading_and_cross_reference_distinction(self):
        self.assertTrue(primary_item202(b'<p>Item 2.02.</p><p>Results of Operations and Financial Condition</p>')['present'])
        self.assertIsNone(primary_item202(b'<p>See Item 2.02 of another report.</p>')['present'])
        self.assertFalse(primary_item202(b'<p>Item 5.02 Leadership changes</p>')['present'])
        self.assertIsNone(primary_item202(b'<p>No identifiable filing structure</p>')['present'])

    def test_general_source_title_variants_and_reference_fail_closed(self):
        from src.research.item202_primary_review import inspect
        for heading in ('Item 2.02. Disclosure of Results of Operations and Financial Condition',
                        'Item 2.02 Results of Operation and Financial Condition',
                        'Item 2.02 — Results of Operations and Financial Condition'):
            self.assertTrue(inspect(heading.encode())['present'])
        self.assertIsNone(inspect(b'See Item 2.02 of the previous filing')['present'])

    def test_original_archive_header_reconciliation(self):
        h = b'<ACCEPTANCE-DATETIME>20150105120000\nACCESSION NUMBER: 0000000001-15-000001\nCONFORMED SUBMISSION TYPE: 8-K\nFILED AS OF DATE: 20150105\nCENTRAL INDEX KEY: 1\n<ITEMS>2.02'
        self.assertTrue(exact_header_reconciliation(h, h, cik='1', accession='0000000001-15-000001', form='8-K'))
        self.assertFalse(exact_header_reconciliation(h, h.replace(b'20150105120000', b'20150106120000'), cik='1', accession='0000000001-15-000001', form='8-K'))

    def test_streaming_oldload_selects_only_declared_header(self):
        from src.research.item202_date_repair import recover_archive
        acc='0000000001-15-000001'
        header=b'<SEC-HEADER>\nACCESSION NUMBER: '+acc.encode()+b'\n</SEC-HEADER>'
        other=b'<SEC-HEADER>ACCESSION NUMBER: 0000000001-21-000001</SEC-HEADER>'
        found,total=recover_archive(gzip.compress(header+b'<DOCUMENT>ignored</DOCUMENT>'+other), {acc:{}}, tar_format=False, max_uncompressed=10000)
        self.assertEqual(found,{acc:header});self.assertGreater(total,len(header))
        with self.assertRaises(ValueError):recover_archive(gzip.compress(header),{acc:{}},tar_format=False,max_uncompressed=1)

    def test_feed_archive_never_extracts_paths_to_disk(self):
        from src.research.item202_date_repair import recover_archive
        acc='0000000001-15-000001';body=b'<SEC-HEADER>original header</SEC-HEADER><DOCUMENT>not interpreted'
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w:gz') as archive:
            member=tarfile.TarInfo('../../'+acc+'.nc');member.size=len(body)
            archive.addfile(member,io.BytesIO(body))
        found,total=recover_archive(stream.getvalue(),{acc:{}},tar_format=True,max_uncompressed=10000)
        self.assertEqual(found[acc],body.split(b'<DOCUMENT>')[0])

    def test_freeze_before_performance_and_confirmation_rejection(self):
        for cert, pushed, stage in (({}, False, 'development'), ({'all_mandatory_gates_passed': True}, False, 'development'),
                                    ({'all_mandatory_gates_passed': True}, True, 'confirmation')):
            with self.assertRaises(ValueError): freeze_before_performance(cert, freeze_commit_pushed=pushed, stage=stage)
        freeze_before_performance({'all_mandatory_gates_passed': True}, freeze_commit_pushed=True, stage='development')

    def test_historical_clock_artifacts_preserved(self):
        docs = Path('docs/acceleration')
        manifest = docs / 'exp006_date_repair_manifest.json'
        if manifest.exists():
            for name, expected in json.loads(manifest.read_bytes())['preserved_artifacts'].items():
                self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(), expected, name)


if __name__ == '__main__': unittest.main()
