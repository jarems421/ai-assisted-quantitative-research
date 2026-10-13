from copy import deepcopy
from datetime import date,datetime,timedelta
import json
from pathlib import Path
import unittest
from src.research.item202_availability import probe,parse_header,calendar_sessions

class AcceptanceRemedyTests(unittest.TestCase):
    def setUp(self):
        self.days=[date(2015,1,1)+timedelta(days=i) for i in range(2192) if (date(2015,1,1)+timedelta(days=i)).weekday()<5]
    def test_adjusted_earlier_filed_date_cannot_advance_acceptance_anchor(self):
        p=probe('20150107110000','20150105',self.days,evidence_sha256='a'*64)
        self.assertTrue(p['invariant']);self.assertEqual(p['modeled_eligible_open_utc'],'2015-01-09T14:30:00+00:00')
    def test_equal_pre_during_after_acceptance(self):
        for clock in ('080000','115000','181000'):
            p=probe('20150107'+clock,'20150107',self.days,evidence_sha256='a'*64)
            self.assertEqual(p['modeled_eligible_open_utc'],'2015-01-09T14:30:00+00:00')
    def test_friday_weekend(self):
        p=probe('20150109181000','20150109',self.days,evidence_sha256='a'*64)
        self.assertEqual(p['modeled_eligible_open_utc'],'2015-01-13T14:30:00+00:00')
    def test_holiday_and_dst(self):
        days=[d for d in self.days if d!=date(2020,7,3)]
        p=probe('20200702183000','20200702',days,evidence_sha256='a'*64)
        self.assertEqual(p['modeled_eligible_open_utc'],'2020-07-07T13:30:00+00:00')
        p=probe('20200306183000','20200306',self.days,evidence_sha256='a'*64)
        self.assertEqual(p['modeled_eligible_open_utc'],'2020-03-10T13:30:00+00:00')
    def test_literal_est_and_seasonal_candidates_retained(self):
        p=probe('20200702183000','20200702',self.days,evidence_sha256='a'*64)
        self.assertEqual(len(p['candidate_interpretations']),2)
        self.assertNotEqual(*[x['utc'] for x in p['candidate_interpretations']])
        self.assertTrue(p['invariant'])
    def test_midnight_disagreement_unavailable_not_hidden_by_global_max(self):
        p=probe('20201029233000','20201029',self.days,evidence_sha256='a'*64)
        self.assertEqual(p['status'],'UNAVAILABLE_TIMING_AMBIGUOUS');self.assertIsNone(p['modeled_eligible_open_utc'])
        p=probe('20201029233000','20201030',self.days,evidence_sha256='a'*64)
        self.assertTrue(p['invariant'])
    def test_missing_acceptance(self):
        self.assertEqual(probe(None,'20150105',self.days,evidence_sha256='a'*64)['status'],'UNAVAILABLE_ACCEPTANCE_MISSING')
    def test_source_conflict_and_invalid_timestamp(self):
        for raw,contradictory in (('20150105120000',True),('invalid',False),('20200308023000',False)):
            self.assertEqual(probe(raw,'20150105',self.days,evidence_sha256='a'*64,contradictory=contradictory)['status'],'UNAVAILABLE_SOURCE_CHRONOLOGY')
    def test_calendar_missing_and_corrupt(self):
        for days in ([],[date(2015,1,8)],[date(2015,1,9),date(2015,1,8)]):
            self.assertEqual(probe('20150107120000','20150107',days,evidence_sha256='a'*64)['status'],'UNAVAILABLE_CALENDAR')
    def test_bound_later_than_every_candidate_public_unknown(self):
        p=probe('20200702183000','20200702',self.days,evidence_sha256='a'*64)
        self.assertTrue(all(datetime.fromisoformat(p['modeled_eligible_open_utc'])>datetime.fromisoformat(x['utc']) for x in p['candidate_interpretations']))
        self.assertIsNone(p['exact_public_available_at_utc']);self.assertFalse(p['policy_activated'])
    def test_confirmation_source_rejected(self):
        p=probe('20210107120000','20210107',self.days,evidence_sha256='a'*64)
        self.assertEqual(p['status'],'UNAVAILABLE_SOURCE_CHRONOLOGY')
    def test_header_identity_and_conflicts(self):
        b=b'<ACCEPTANCE-DATETIME>20150105120000\nACCESSION NUMBER: 0000000001-15-000001\nCONFORMED SUBMISSION TYPE: 8-K\nFILED AS OF DATE: 20150105\nCENTRAL INDEX KEY: 1\n<ITEMS>2.02'
        self.assertFalse(parse_header(b,cik='1',accession='0000000001-15-000001',form='8-K')['source_chronology_contradictory'])
        self.assertTrue(parse_header(b+b'\n<ACCEPTANCE-DATETIME>20150106120000',cik='1',accession='0000000001-15-000001',form='8-K')['source_chronology_contradictory'])
    def test_source_calendar_hash_and_mourning_close(self):
        c=json.loads(Path('docs/acceleration/exp006_calendar_certificate_v002.json').read_bytes())
        days=calendar_sessions(c);self.assertEqual(len(days),1511);self.assertNotIn(date(2018,12,5),days)
        bad=deepcopy(c);bad['full_day_closures'].remove('2018-12-05')
        with self.assertRaises(ValueError):calendar_sessions(bad)
    def test_v001_and_old_global_policy_history(self):
        c=json.loads(Path('docs/acceleration/exp006_availability_contract.json').read_bytes());self.assertEqual(c['status'],'AVAILABILITY_BLOCKED')
        for n in ('availability_policy_v002_approved.json','availability_policy_v003_approved.json'):
            self.assertEqual(json.loads(Path('docs/acceleration',n).read_bytes())['activation_status'],'NOT_ACTIVATED')
