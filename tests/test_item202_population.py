from copy import deepcopy
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from src.research.item202_population import (parse_daily,reconcile,event_state,resolve_class,
    certification_query,terminal_guard)

HEADER='CIK|Company Name|Form Type|Date Filed|Filename\n'
class PopulationTests(unittest.TestCase):
    def row(self,cik='1',form='8-K',day='2015-01-05'):
        return {'CIK':cik,'accession':'0000000001-15-000001','form':form,'filing_date':day,
                'source_path':f'edgar/data/{cik}/0000000001-15-000001.txt','source_index_sha256':'a'*64,
                'source_line':2,'observed_index_day':day}

    def test_daily_compact_and_iso_dates_deterministic(self):
        for day in ('20150105','2015-01-05'):
            b=(HEADER+f'1|X|8-K|{day}|edgar/data/1/0000000001-15-000001.txt').encode()
            p=parse_daily(b,'2015-01-05','a'*64)
            self.assertEqual(p,parse_daily(b,'2015-01-05','a'*64))
            self.assertEqual(p['rows'][0]['filing_date'],'2015-01-05')
        self.assertEqual(len(parse_daily((HEADER.replace('Filename','File Name')+'1|X|8-K|20150105|edgar/data/1/0000000001-15-000001.txt').encode(),'2015-01-05','a'*64)['rows']),1)

    def test_daily_rejects_wrong_schema_future_and_path(self):
        for b in (b'not a master index',(HEADER+'1|X|8-K|20150106|edgar/data/1/0000000001-15-000001.txt').encode(),
                  (HEADER+'1|X|8-K|20150105|edgar/data/2/0000000001-15-000001.txt').encode()):
            with self.assertRaises(ValueError):parse_daily(b,'2015-01-05','a'*64)
        with self.assertRaises(ValueError):parse_daily(HEADER.encode(),'2021-01-01','a'*64)

    def test_empty_index_is_not_missing_filing_imputation(self):
        self.assertEqual(parse_daily(HEADER.encode(),'2015-01-05','a'*64)['rows'],[])

    def test_prior_year_row_retained_as_scope_count_not_event(self):
        p=parse_daily((HEADER+'1|X|8-K|20141231|edgar/data/1/0000000001-14-000001.txt').encode(),'2015-01-02','a'*64)
        self.assertEqual(p['outside_Development_rows'],1);self.assertEqual(p['rows'],[])

    def test_union_and_each_neutral_population_state(self):
        a,b,c=self.row(),self.row('2'),self.row('3')
        result=reconcile([a,b],[a,c])
        self.assertEqual([x['population_state'] for x in result['rows']],['PRESENT_BOTH','HISTORICAL_DAILY_ONLY','CURRENT_QUARTERLY_ONLY'])
        self.assertEqual(result,reconcile([b,a],[c,a]))
        self.assertEqual(result['daily_equivalent_extra_rows'],0)
        self.assertEqual(result['quarterly_equivalent_extra_rows'],0)

    def test_disjoint_sources_duplicate_counts_nonnegative(self):
        a,b=self.row(),self.row('2')
        for daily,quarterly,counts in (([a,a],[b],(1,0)),([a],[b,b],(0,1)),([],[b],(0,0))):
            result=reconcile(daily,quarterly)
            self.assertEqual((result['daily_equivalent_extra_rows'],result['quarterly_equivalent_extra_rows']),counts)

    def test_equivalent_rows_and_cofilers_do_not_disappear(self):
        a,b=self.row(),self.row('2')
        result=reconcile([a,a,b],[a,b])
        self.assertEqual(len(result['rows']),2);self.assertEqual(result['daily_equivalent_extra_rows'],1)
        self.assertEqual(len(result['rows'][0]['daily_observations']),2)

    def test_conflicting_same_filer_accession_kept(self):
        a,b=self.row(),self.row(day='2015-01-06')
        r=reconcile([a],[b])['rows']
        self.assertEqual(len(r),2);self.assertTrue(all(x['metadata_conflict'] for x in r))

    def test_original_item_and_amendment_version_only(self):
        self.assertEqual(event_state('8-K',True),'ORIGINAL_SIGNAL_EVENT')
        self.assertEqual(event_state('8-K/A',True),'AMENDMENT_VERSION_ONLY')
        self.assertEqual(event_state('8-K',False),'NON_ITEM202')
        self.assertEqual(event_state('8-K',None),'UNKNOWN')
        self.assertEqual(event_state('8-K',True,source_available=False),'SOURCE_REMOVED_OR_UNAVAILABLE')

    def span(self):
        return dict(issuer_cik='1',security_id='permanent1',class_id='common1',provider_id='provider1',
                    historical_ticker='OLD',source_sha256='a'*64,effective_from='2015-01-01',effective_to='2020-01-01',
                    domestic_common_equity_certified=True,listing_span_certified=True,twenty_session_lifecycle_certified=True)

    def test_point_current_ticker_not_projected_back(self):
        span=self.span();span['effective_from']=None
        self.assertEqual(resolve_class([span],'2016-01-01')['status'],'UNRESOLVED')
        span=self.span();span['listing_span_certified']=False
        self.assertEqual(resolve_class([span],'2016-01-01')['status'],'UNRESOLVED')

    def test_span_contains_event_exclusive_end(self):
        self.assertEqual(resolve_class([self.span()],'2015-01-01')['status'],'FULLY_RESOLVED')
        self.assertEqual(resolve_class([self.span()],'2020-01-01')['status'],'UNRESOLVED')

    def test_multiple_classes_need_predeclared_selection(self):
        a=self.span();b=dict(a,class_id='common2')
        self.assertEqual(resolve_class([a,b],'2016-01-01')['status'],'AMBIGUOUS')
        self.assertEqual(resolve_class([a,b],'2016-01-01',selected_class='common2')['status'],'AMBIGUOUS')
        self.assertEqual(resolve_class([a,b],'2016-01-01',selected_class='common2',predeclared_rule_hash='b'*64)['binding']['class_id'],'common2')

    def test_rename_same_stable_security_retains_both_spans(self):
        a=self.span();a['effective_to']='2016-01-01'
        b=dict(self.span(),effective_from='2016-01-01',historical_ticker='NEW')
        self.assertEqual(resolve_class([a,b],'2015-12-31')['binding']['historical_ticker'],'OLD')
        self.assertEqual(resolve_class([a,b],'2016-01-01')['binding']['security_id'],a['security_id'])

    def test_ended_missing_provider_and_unresolved_terminal_block(self):
        for present,crosses,terms in ((False,False,True),(True,True,False)):
            with self.assertRaises(ValueError):terminal_guard(self.span(),provider_present=present,crosses_terminal=crosses,terms_certified=terms)
        self.assertTrue(terminal_guard(self.span(),provider_present=True,crosses_terminal=True,terms_certified=True))

    def test_lifecycle_missing_cannot_become_full_identity(self):
        span=self.span();span['twenty_session_lifecycle_certified']=False
        self.assertEqual(resolve_class([span],'2016-01-01')['status'],'UNRESOLVED_TERMINAL_PATH')

    def test_pre_event_query_bounds_and_confirmation(self):
        self.assertTrue(certification_query('2014-01-01T00:00:00+00:00','2015-01-01T00:00:00+00:00','2015-01-05T14:30:00+00:00'))
        for end,decision,stage in (('2015-01-05T14:30:00+00:00','2015-01-05T14:30:00+00:00','development'),
             ('2015-01-06T00:00:00+00:00','2015-01-05T14:30:00+00:00','development'),
             ('2021-01-01T00:00:00+00:00','2021-01-05T14:30:00+00:00','confirmation')):
            with self.assertRaises(ValueError):certification_query('2014-01-01T00:00:00+00:00',end,decision,stage=stage)

    def test_fake_daily_transport_archive_cache_and_no_contact_receipt(self):
        from src.research import item202_population_acquire as module
        url='https://www.sec.gov/Archives/edgar/daily-index/2015/QTR1/index.json'
        calls=[]
        def transport(u,h,p):calls.append(u);return 200,{},b'{}',u
        with tempfile.TemporaryDirectory() as temp,patch.object(module,'RAW',Path(temp)),patch.object(module,'manifest',return_value={}),patch.object(module,'identity',return_value='PRIVATE_FIXTURE_VALUE'):
            h=module.IndexHTTP('directory',[url],1,transport=transport,sleep=lambda _:None)
            a,b=h.fetch(url);self.assertEqual(b,b'{}');self.assertEqual(h.fetch(url)[0],a)
            self.assertEqual(len(calls),1)
            self.assertNotIn('PRIVATE_FIXTURE_VALUE',json.dumps(a))
            with self.assertRaises(ValueError):h.fetch(url+'/other')

    def test_denial_is_archived_and_persistently_stopped_without_retry(self):
        from src.research import item202_population_acquire as module
        url='https://www.sec.gov/Archives/edgar/daily-index/2015/QTR1/index.json';calls=[]
        def transport(u,h,p):calls.append(u);return 403,{},b'Denied',u
        with tempfile.TemporaryDirectory() as temp,patch.object(module,'RAW',Path(temp)),patch.object(module,'manifest',return_value={}),patch.object(module,'identity',return_value='PRIVATE_FIXTURE_VALUE'):
            h=module.IndexHTTP('directory',[url],2,transport=transport,sleep=lambda _:None)
            for _ in range(2):
                with self.assertRaises(ValueError):h.fetch(url)
            self.assertEqual(len(calls),1);self.assertEqual(len(list((Path(temp)/'directory/receipts').glob('*.json'))),1)

    def test_reviewed_404_is_document_missingness_and_denial_still_stops(self):
        from src.research import item202_population_acquire as module
        urls=['https://www.sec.gov/Archives/edgar/data/1/missing','https://www.sec.gov/Archives/edgar/data/1/denied']
        calls=[]
        def transport(u,h,p):calls.append(u);return (404 if u==urls[0] else 403),{},b'Unavailable',u
        with tempfile.TemporaryDirectory() as temp,patch.object(module,'RAW',Path(temp)),patch.object(module,'manifest',return_value={}),patch.object(module,'identity',return_value='PRIVATE_FIXTURE_VALUE'):
            h=module.IndexHTTP('headers',urls,2,transport=transport,sleep=lambda _:None,allow_document_404=True)
            self.assertEqual(h.fetch(urls[0])[0]['status'],404)
            self.assertFalse((Path(temp)/'headers/stop.json').exists())
            with self.assertRaises(ValueError):h.fetch(urls[1])
            with self.assertRaises(ValueError):h.fetch(urls[1])
            self.assertEqual(len(calls),2)

    def test_cofiler_header_requires_each_legal_filer_not_accession_alone(self):
        from src.research.item202_availability import parse_header
        b=b'ACCESSION NUMBER: 0000000001-15-000001\nCONFORMED SUBMISSION TYPE: 8-K\nFILED AS OF DATE: 20150105\nCENTRAL INDEX KEY: 1\nCENTRAL INDEX KEY: 2\n<ITEMS>2.02'
        for cik in ('1','2'):
            self.assertFalse(parse_header(b,cik=cik,accession='0000000001-15-000001',form='8-K')['source_chronology_contradictory'])
        self.assertTrue(parse_header(b,cik='3',accession='0000000001-15-000001',form='8-K')['source_chronology_contradictory'])

    def test_passed_timing_and_classification_artifacts_unchanged(self):
        import hashlib
        docs=Path('docs/acceleration')
        frozen=json.loads((docs/'exp006_historical_population_manifest.json').read_bytes())['preserved_artifacts']
        for name in ('exp006_availability_contract_v003.json','exp006_availability_certificate_v003.json',
                     'exp006_date_validation_v003.json','exp006_primary_title_review_v003.json'):
            p=docs/name
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),frozen[p.as_posix()])

if __name__=='__main__':unittest.main()
