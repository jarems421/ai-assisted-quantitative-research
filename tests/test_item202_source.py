import unittest
from src.research.item202_source import enumerate_index,metadata_labels,metadata_clock_conformance

class SourceClosureTests(unittest.TestCase):
    def test_full_period_census_determinism_and_forms(self):
        for year in range(2015,2021):
            for q in range(1,5):
                body=(f'1|Ended|8-K|{year}-{1+3*(q-1):02}-02|edgar/data/1/0000000001-{str(year)[2:]}-000001.txt\n'
                      f'2|Cofiler|8-K/A|{year}-{1+3*(q-1):02}-02|edgar/data/2/0000000001-{str(year)[2:]}-000001.txt').encode()
                a=enumerate_index(body,year,q,'a'*64)
                self.assertEqual(a,enumerate_index(body,year,q,'a'*64));self.assertEqual(len(a),2)
                self.assertEqual(a[1]['amendment_state'],'UNRESOLVED')
                self.assertEqual(a[0]['Item202_classification'],'UNKNOWN_NOT_CLASSIFIED')
    def test_cutoff_and_wrong_quarter_fail(self):
        with self.assertRaises(ValueError):enumerate_index(b'',2021,1,'a'*64)
        with self.assertRaises(ValueError):enumerate_index(b'1|X|8-K|2020-04-02|edgar/data/1/0000000001-20-000001.txt',2020,1,'a'*64)
    def test_metadata_missing_not_zero_and_labels_are_not_primary_certificates(self):
        c={'accessionNumber':['a','b'],'filingDate':['2020-01-02','2020-01-03'],'form':['8-K','8-K/A'],'items':['2.02,9.01','']}
        rows=metadata_labels(c,{'a','b'})
        self.assertEqual(rows[0]['Item202'],'PRESENT_METADATA');self.assertEqual(rows[1]['Item202'],'UNKNOWN')
        self.assertIsNone(rows[0]['acceptance_representation'])
    def test_future_metadata_fields_not_read(self):
        class Bomb:
            def __len__(self):raise AssertionError('Future feature array read')
        c={'accessionNumber':['future'],'filingDate':['2021-01-01'],'items':Bomb(),'acceptanceDateTime':Bomb()}
        self.assertEqual(metadata_labels(c,{'future'}),[])
    def test_raw_alias_and_double_conversion_not_silently_repaired(self):
        source=['2015-02-04T16:50:34+00:00']
        self.assertEqual(metadata_clock_conformance('2015-02-04T16:50:34Z',source),'MATCH_SOURCE_CANDIDATE')
        for clock in ('2015-02-04T11:50:34Z','2015-02-04T21:50:34Z'):
            self.assertEqual(metadata_clock_conformance(clock,source),'CONFLICTING_SOURCE_CLOCK_REPRESENTATION')
        self.assertEqual(metadata_clock_conformance(None,source),'UNKNOWN_UNSUPPORTED_CLOCK_REPRESENTATION')
