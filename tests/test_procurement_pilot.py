import copy,json
from pathlib import Path
import tempfile
import unittest
from src.research.procurement_pilot import contract,validate_manifest,select_announcement,event_record,timing,lineage,PilotHTTP,ALTERNATIVE
from src.research.phase3c.sources import put


class ProcurementPilotTests(unittest.TestCase):
    def test_manifest_freeze_slots_and_nested_filters(self):
        m=contract();validate_manifest(m);self.assertEqual(len(m['slots']),12)
        for field in ('issuer','current_public','award_size','industry','price','effect'):
            bad=copy.deepcopy(m);bad['selection']['filters'][field]='anything'
            with self.assertRaises(ValueError):validate_manifest(bad)
        for key,value in [('request_ceiling',61),('fallback','easier month'),('performance_authorized',True)]:
            bad=copy.deepcopy(m);bad[key]=value
            with self.assertRaises(ValueError):validate_manifest(bad)

    def test_earliest_is_complete_source_order_not_amount_or_recipient(self):
        base='https://www.defense.gov/News/Contracts/Contract/Article/'
        a={'page_date':'2019-01-02','url':base+'10/first/','recipient':'Private LLC','amount':'1'}
        b={'page_date':'2019-01-03','url':base+'11/later/','recipient':'Public PLC','amount':'99999'}
        self.assertEqual(select_announcement([b,a],'2019-01',complete=True),a)
        with self.assertRaises(ValueError):select_announcement([a],'2019-01',complete=False)
        self.assertIsNone(select_announcement([a],'2019-03',complete=True))

    def test_unavailable_slots_and_private_ambiguous_cases_are_not_dropped(self):
        rows=[event_record(s['slot']) for s in contract()['slots']]
        rows[0].update(recipient='Private LLC',recipient_status='PRIVATE_RECIPIENT')
        rows[1].update(recipient='Ambiguous Ltd',recipient_status='RECIPIENT_PARENT_AMBIGUOUS')
        self.assertEqual(len(rows),12);self.assertIsNone(rows[11]['award'])
        self.assertEqual(rows[0]['recipient_status'],'PRIVATE_RECIPIENT')
        self.assertEqual(rows[1]['recipient_status'],'RECIPIENT_PARENT_AMBIGUOUS')

    def test_date_only_is_not_observed_timestamp_or_filing_policy(self):
        r=timing('2019-01-02');self.assertEqual(r['status'],'DATE_ONLY')
        self.assertIsNone(r['public_available_at_utc']);self.assertFalse(r['modeled_policy_approved'])
        with self.assertRaises(ValueError):timing('2019-01-02','2019-01-02T17:00:00Z')
        self.assertEqual(timing(None)['status'],'UNAVAILABLE')

    def test_lineage_duplicate_and_missing_are_explicit(self):
        self.assertEqual(lineage('A',['B']),'UNMATCHED')
        self.assertEqual(lineage('A',['A']),'USASPENDING_MATCHED_IDENTIFIER_ONLY')
        self.assertEqual(lineage('A',['A','A']),'USASPENDING_AMBIGUOUS')

    def test_error_body_immutable_stop_cache_and_no_host_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def fake(url,headers,payload):calls.append(url);return 403,{'Content-Type':'text/html'},b'original denial',url
            h=PilotHTTP(contract(),root=tmp,transport=fake,sleep=lambda _:None)
            url=contract()['slots'][0]['discovery_url'];r,body=h.fetch(url)
            self.assertEqual(h.archive.read(r['body']),b'original denial')
            h.fetch(url);self.assertEqual(len(calls),1)
            with self.assertRaises(ValueError):h.fetch(contract()['slots'][1]['discovery_url'])
            with self.assertRaises(ValueError):h.fetch('https://www.war.gov/News/Contracts/')
            h.fetch(ALTERNATIVE);self.assertEqual(len(h.starts()),2)
            path=Path(tmp)/r['body']['path'];path.write_bytes(b'tampered')
            with self.assertRaises(ValueError):h.archive.read(r['body'])

    def test_retry_reservations_and_total_ceiling_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def fake(url,headers,payload):calls.append(url);return (503 if len(calls)<3 else 200),{},b'bytes',url
            h=PilotHTTP(contract(),root=tmp,transport=fake,sleep=lambda _:None)
            h.fetch(contract()['slots'][0]['discovery_url']);self.assertEqual(len(h.starts()),3)
            for i in range(57):put(Path(tmp)/'reservations'/f'ceiling_{i}.json',{'request_started_at_utc':'2000-01-01T00:00:00+00:00'})
            h2=PilotHTTP(contract(),root=tmp,transport=fake,sleep=lambda _:None)
            with self.assertRaises(ValueError):h2.fetch(ALTERNATIVE)
            self.assertEqual(len(calls),3)

    def test_redirect_and_interruption_count_and_fail_closed(self):
        for redirect in (False,True):
            with tempfile.TemporaryDirectory() as tmp:
                def fake(url,headers,payload):
                    if redirect:return 302,{},b'redirect body','https://example.invalid/'
                    raise TimeoutError()
                h=PilotHTTP(contract(),root=tmp,transport=fake,sleep=lambda _:None)
                with self.assertRaises(ValueError):h.fetch(contract()['slots'][0]['discovery_url'])
                self.assertEqual(len(h.starts()),1)
                self.assertTrue((Path(tmp)/'publication_stop.json').exists())

    def test_price_performance_and_unrelated_routes_are_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            h=PilotHTTP(contract(),root=tmp,transport=lambda *a: self.fail('Transport must not run'))
            for url in ('https://api.tiingo.com/tiingo/daily/A/prices','https://api.nexustrade.io/backtest','https://data.sec.gov/api/xbrl/companyfacts/CIK0001.json'):
                with self.assertRaises(ValueError):h.fetch(url)
            self.assertEqual(len(h.starts()),0)
