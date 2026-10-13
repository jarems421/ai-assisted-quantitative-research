import copy,hashlib,json,sys,tempfile,types,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from src.research.surfaces.base import EvidenceTier,ProviderResult
from src.research.surfaces.congressional import CongressionalDisclosuresAdapter
from src.research.surfaces.sec import SECSurfaceAdapter,item_semantics,daily_index_keys
from src.research.signals.time_window import ElapsedWindow,TimedObservation
from src.research.integrations.nexus_local import prepare_html
from src.research.integrations.registry import validate_registry
from src.research.source_first_v2 import selection_contract,select,GATES
from src.research.proof_v2 import compile_design,ROLES
from src.research.integrations.http import BoundedHTTP
from src.research.phase3c.sources import put

def snapshot():return {'schemaVersion':1,'dataset':'austin-starks/congressional-stock-trades','generatedAt':'2026-10-13T00:00:00Z','tables':{k:{'manifests':[{'year':2020,'files':[]}]} for k in ('political_filings','political_trades','political_trade_events')}}
def event(version,available,superseded=None):return {'event_id':'house:D:1','version':version,'chamber':'house','source_doc_id':'D','source_row_index':version,'source_url':'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2020/D.pdf','transaction_date':'2020-01-01','first_available_at':'2020-01-10T00:00:00Z','available_at':available,'superseded_at':superseded,'ticker':'UPSTREAM'}

class IntegrationTests(unittest.TestCase):
    def test_daily_quarter_date_representation_and_shared_accession_not_dropped(self):
        a=b'1|Issuer|8-K|20200102|edgar/data/1/0000000001-20-000001.txt'
        b=a.replace(b'20200102',b'2020-01-02');self.assertEqual(daily_index_keys(a),daily_index_keys(b))
        joint=b+b'\n2|Cofiler|8-K|2020-01-02|edgar/data/2/0000000001-20-000001.txt'
        rows=SECSurfaceAdapter().enumerate(joint,'a'*64);self.assertEqual(len(rows),2);self.assertTrue(rows[1]['duplicate_accession_source_row'])
    def test_publisher_redirect_archived_reviewed_and_deny_not_overridden(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(url,*a):
                return (302,{'Location':'https://huggingface.co/target'},b'redirect',url) if url.endswith('/start') else (200,{},b'file',url)
            h=BoundedHTTP(tmp,'CONGRESS',24,transport=fake,sleep=lambda _:None)
            r,b=h.fetch_reviewed('https://huggingface.co/start','fixture');self.assertEqual(b,b'file');self.assertEqual(len(h.starts()),2)
            self.assertTrue((Path(tmp)/'CONGRESS/publication_stop.json').exists())
            reopened=BoundedHTTP(tmp,'CONGRESS',24,transport=lambda u,*a:(403,{},b'denied',u),sleep=lambda _:None)
            r,_=reopened.fetch_reviewed('https://huggingface.co/new','new');self.assertEqual(r['status'],403)
            with self.assertRaises(ValueError):reopened.fetch_reviewed('https://huggingface.co/another','blocked')
    def test_comparison_budget_does_not_reset_per_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(24):put(Path(tmp)/'CONGRESS/reservations'/f'{i}.json',{'request_started_at_utc':'2000-01-01T00:00:00Z'})
            h=BoundedHTTP(tmp,'SEC',24,transport=lambda *a:self.fail('25th request'),sleep=lambda _:None)
            with self.assertRaises(ValueError):h.fetch_reviewed('https://www.sec.gov/fixture','fixture')
    def test_derived_provider_never_promoted_by_official_url(self):
        r=ProviderResult('OpenBB',EvidenceTier.AUDITED_EXTERNAL_DERIVED,'https://www.sec.gov/x','a'*64,'v1','snapshot','2026-10-13T00:00:00Z',None,'UNKNOWN','UNKNOWN','DISCOVERY',{}, {},())
        with self.assertRaises(ValueError):r.require_original()

    def test_snapshot_hash_length_and_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=snapshot();body=b'fixture';f={'publicPath':'data/political_trades/2020.parquet','size':7,'sha256':hashlib.sha256(body).hexdigest()}
            m['tables']['political_trades']['manifests'][0]['files']=[f];a=CongressionalDisclosuresAdapter(m,tmp,revision='a'*40,retrieved_at='2026-10-13T00:00:00Z')
            p=Path(tmp)/f['publicPath'];p.parent.mkdir(parents=True);p.write_bytes(body);self.assertEqual(a.verify(f),p.resolve())
            p.write_bytes(b'changed')
            with self.assertRaises(ValueError):a.verify(f)
            f['publicPath']='../escape'
            with self.assertRaises(ValueError):a.files('political_trades',2020)

    def test_amended_version_cannot_leak_through_event_first_date(self):
        a=CongressionalDisclosuresAdapter(snapshot(),'.',revision='a'*40,retrieved_at='2026-10-13T00:00:00Z')
        rows=[event(1,'2020-01-10T00:00:00Z','2020-02-10T00:00:00Z'),event(2,'2020-02-10T00:00:00Z')]
        self.assertEqual(a.events_known_at(rows,'2020-01-05T00:00:00Z'),[])
        self.assertEqual([r['version'] for r in a.events_known_at(rows,'2020-01-10T00:00:00Z')],[1])
        self.assertEqual([r['version'] for r in a.events_known_at(rows,'2020-02-10T00:00:00Z')],[2])
        self.assertEqual(rows[0]['transaction_date'],'2020-01-01')

    def test_ticker_source_member_missingness_preserved(self):
        a=CongressionalDisclosuresAdapter(snapshot(),'.',revision='a'*40,retrieved_at='2026-10-13T00:00:00Z');e=event(1,'2020-01-10T00:00:00Z');e['member_id']=None
        trade={'chamber':'house','doc_id':'D','row_index':1,'printed_ticker':'OLD','resolved_ticker':'NEW','resolution_status':'unresolved'}
        row=a.events_known_at([e],'2020-02-01T00:00:00Z',[trade])[0]
        self.assertEqual((row['printed_ticker'],row['resolved_ticker']),('OLD','NEW'));self.assertEqual(row['resolution_status'],'unresolved');self.assertIsNone(row['member_id']);self.assertEqual(row['source_url'],e['source_url'])
        self.assertNotIn('ticker',row);self.assertEqual(row['upstream_ticker'],'UPSTREAM')

    def test_window_irregular_bucket_expiry_and_out_of_order(self):
        at=datetime(2020,1,1,tzinfo=timezone.utc);w=ElapsedWindow(timedelta(hours=1),timedelta(minutes=5))
        w.push(TimedObservation(at,10));self.assertEqual(w.push(TimedObservation(at+timedelta(minutes=1),20)),20)
        self.assertEqual(w.push(TimedObservation(at+timedelta(minutes=10),40)),30)
        self.assertEqual(w.push(TimedObservation(at+timedelta(hours=2),80)),80)
        with self.assertRaises(ValueError):w.push(TimedObservation(at,3))
        with self.assertRaises(ValueError):TimedObservation(datetime(2020,1,1),4)

    def test_stream_batch_state_capacity_and_reset(self):
        at=datetime(2020,1,1,tzinfo=timezone.utc);rows=[TimedObservation(at+timedelta(minutes=i),i+1) for i in (0,5,10)]
        one=ElapsedWindow(timedelta(hours=1),timedelta(minutes=1));values=[one.push(r) for r in rows]
        batch=ElapsedWindow(timedelta(hours=1),timedelta(minutes=1));self.assertEqual(batch.batch(rows),values)
        restored=ElapsedWindow.restore(one.state());new=TimedObservation(at+timedelta(minutes=15),5)
        self.assertEqual(one.push(new),restored.push(new));self.assertEqual(values,[1,3.5,6.0])
        self.assertEqual(one.value_ago(timedelta(minutes=5)),11);one.reset();self.assertIsNone(one.sma())
        bounded=ElapsedWindow(timedelta(hours=1),timedelta(minutes=1),1);bounded.push(rows[0])
        with self.assertRaises(ValueError):bounded.push(rows[1])

    def test_nexus_literal_input_no_remote_surface(self):
        fake=types.ModuleType('nexustrade.scanned_table');fake.prepare_web_pages=lambda pages:{'original':{'document':{'visible_text':'local'},'error':None}}
        with patch.dict(sys.modules,{'nexustrade.scanned_table':fake}),patch('importlib.metadata.version',return_value='1.42.0'):
            row=prepare_html(b'<p>local</p>');self.assertFalse(row['remote_execution']);self.assertFalse(row['absence_certified'])
        with self.assertRaises(TypeError):prepare_html('https://example.com')

    def test_sec_denominator_no_item_or_issuer_filter(self):
        body=b'1|Private|8-K|2020-01-02|edgar/data/1/0000000001-20-000001.txt\n2|Ended|8-K/A|2020-01-02|edgar/data/2/0000000002-20-000001.txt'
        a=SECSurfaceAdapter();rows=a.enumerate(body,'a'*64);self.assertEqual(len(rows),2);self.assertEqual(len(a.sample(rows)),1)
        with self.assertRaises(ValueError):a.normalize_probe(rows)
        result=a.normalize_probe(rows,{'url':'https://www.sec.gov/index','body':{'sha256':'a'*64},'retrieved_at_utc':'2026-10-13T00:00:00Z'})
        self.assertEqual(result.evidence_tier,EvidenceTier.PRIMARY_INDEX_OR_METADATA)
        with self.assertRaises(ValueError):result.require_original()
        self.assertEqual(item_semantics(b'ITEM INFORMATION: Results of Operations and Financial Condition\n')['status'],'PRESENT_SOURCE_HEADER')
        self.assertEqual(item_semantics(b'<p>nothing</p>')['status'],'UNKNOWN')

    def test_frozen_lexicographic_selection_not_profitability(self):
        a={'id':'SEC','gates':{g:'PASS_BOUNDED_PROBE' for g in GATES},'derived_dependencies':0,'identity_burden':1,'plausible_independent_frequency':1}
        b=dict(a,id='CONGRESS',derived_dependencies=1)
        self.assertEqual(select([b,a])['winner'],'SEC');b['gates']=dict(b['gates'],POINT_IN_TIME='BLOCKED');self.assertEqual(select([a,b])['winner'],'SEC')

    def test_proof_refuses_execution_and_changed_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);records={r:{'fixture_contract':True} for r in ROLES};records.update(population={'status':'SOURCE_CONTRACT_READY_FOR_DESIGN'},source_surface={'version':'v2'},source_snapshot={'source_end':'2020-03-31','evidence_tier':'PRIMARY_INDEX_OR_METADATA','upstream_version':'SEC','source_sha256s':['a'*64]},availability={'status':'PUBLIC_TIMESTAMP_UNKNOWN'},identity={'required':'Dated class/listing evidence'},trial_family={'ceiling':10},inference_contract={'obviously_impossible':False})
            refs={}
            for role,obj in records.items():
                p=root/(role+'.json');p.write_text(json.dumps(obj));refs[role]={'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            spec={'mode':'DESIGN_ONLY','estimand_type':'PREDICTIVE','performance_authorized':False,'performance_executed':False,'experiment_registered':False,'contracts':refs,'research_cutoff':'2020-03-31'}
            with patch('src.research.proof_v2.environment',return_value={'fixture':True}):self.assertFalse(compile_design(spec,root,root/'out')['scientifically_certified'])
            bad=dict(spec,performance_authorized=True)
            with self.assertRaises(ValueError):compile_design(bad,root,root/'out')
            (root/'population.json').write_text('{}')
            with self.assertRaises(ValueError):compile_design(spec,root,root/'out')

    def test_registry_refuses_unused_dependency_or_evidence_promotion(self):
        rows=[{'name':n,'pinned_audit_commit':'a'*40,'repo':'url','license':'MIT','role':'role','integration_status':'REFERENCE_ONLY','runtime_dependency':False,'canonical_evidence_role':'NONE_LIBRARY_IS_NOT_PRIMARY_EVIDENCE','allowed_usage':['read'],'forbidden_usage':['remote'],'reason':'reason','files_inspected':['file']} for n in ('FinRL','OpenBB','scikit-learn','pandas','numpy','matplotlib','chrono-ta','nexustrade-py','congressional-disclosures')]
        validate_registry(rows);rows[0]['runtime_dependency']=True
        with self.assertRaises(ValueError):validate_registry(rows)
