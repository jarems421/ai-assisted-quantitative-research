"""Bounded, receipt-first sources for the fixed 26 execution stock-days."""
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put,secret,SourceHTTP
from src.research.prepare_exp004 import verify_freeze
from src.research.item202_identity import require_published
from src.research.exp004_supplement import allowed_call

PLAN=ROOT/'docs/acceleration/exp004_execution_gap_investigation_plan_v001.json'
OUT=ROOT/'data/raw/EXP004/execution_gap_investigation_v001'


def now():return datetime.now(timezone.utc).isoformat()


def reserve(category,key,source):
    require_published(PLAN);p=json.loads(PLAN.read_bytes());folder=OUT/'scientific_requests';folder.mkdir(parents=True,exist_ok=True)
    policy=ROOT/'docs/acceleration/exp004_execution_gap_amendment_policy_v001.md'
    if hashlib.sha256(policy.read_bytes()).hexdigest()!=p['policy_sha256']:raise ValueError('Frozen contingency policy changed')
    rows=[json.loads(x.read_bytes()) for x in folder.glob('*.json')]
    from src.research.exp004_execution_gaps import request_room
    if not request_room(rows,category,key,p['allocation'],p['request_ceiling']):raise ValueError('Frozen scientific ceiling or previously submitted request; no automatic retry')
    if (OUT/'final_stop.json').exists():raise ValueError('Investigation has stopped')
    put(folder/f'{len(rows)+1:03d}_{key}.json',{'category':category,'key':key,'source':source,'submitted_at_utc':now(),'automatic_retry':False})


def lake():
    verify_freeze();require_published(PLAN);p=json.loads(PLAN.read_bytes());request=p['Lake_request'];folder=OUT/'lake_batch';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'part_hashes.json').exists():return json.loads((folder/'part_hashes.json').read_bytes())
    if (folder/'source_stop.json').exists():raise ValueError('Lake batch source stopped')
    from nexustrade.client import NexusTradeClient
    key=secret('NEXUSTRADE_API_KEY');url=secret('NEXUSTRADE_API_BASE_URL')
    if not key or not url:raise ValueError('Local Lake credentials missing; values not printed')
    c=NexusTradeClient(api_key=key,base_url=url);t=c._transport;raw=t.request;binary=t.request_bytes
    def capture(method,path,*,bytes_call=False,**kw):
        known={json.loads((folder/'submission.json').read_bytes())['id']} if (folder/'submission.json').exists() else set()
        if path.startswith('lake/catalog/'):raise ValueError('No schema call in batch quota')
        allowed_call(method,path,kw.get('body'),[request],known)
        n=len(list(folder.glob('wire_request_*.json')))+1
        put(folder/f'wire_request_{n:04d}.json',{'method':method,'path':path,'body':kw.get('body'),'idempotency_key':kw.get('idempotency_key'),'at_utc':now()})
        try:value=(binary if bytes_call else raw)(method,path,**kw)
        except Exception as e:
            put(folder/f'wire_error_{n:04d}.json',{'type':type(e).__name__,'message':str(e),'at_utc':now()})
            put(folder/'source_stop.json',{'reason':'SOURCE_ERROR','no_retry':True})
            raise ValueError('Private Lake error preserved') from None
        if isinstance(value,bytes):
            sha=hashlib.sha256(value).hexdigest();fpath=folder/f'bytes_{sha}.parquet'
            if not fpath.exists():
                with fpath.open('xb') as f:f.write(value)
            put(folder/f'wire_response_{n:04d}.json',{'sha256':sha,'bytes':len(value),'path':fpath.relative_to(ROOT).as_posix(),'retrieved_at_utc':now()})
        else:put(folder/f'wire_response_{n:04d}.json',value)
        return value
    t.request=lambda method,path,**kw:capture(method,path,**kw)
    t.request_bytes=lambda method,path,**kw:capture(method,path,bytes_call=True,**kw)
    if not (folder/'submission.json').exists():
        reserve('Lake_batch',digest(request),'lake.sec_daily_ohlc exact26case context')
        idempotency='exp004-gap-v001-'+digest(request);put(folder/'intent.json',{'idempotency_key':idempotency,'request':request})
        put(folder/'submission.json',c.create_lake_query(request,idempotency_key=idempotency))
    from nexustrade.lake import get,LakeQueryResult
    op=json.loads((folder/'submission.json').read_bytes());h=get(op['id'],client=c)
    if not isinstance(h,LakeQueryResult):h=h.wait(timeout_seconds=40)
    put(folder/'result_receipt.json',{'id':h.id,'row_count':h.row_count,'result':h.result})
    parts=h.download(folder/'parts')
    refs=[{'path':r.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(r.read_bytes()).hexdigest(),'bytes':r.stat().st_size} for r in sorted(parts.glob('part-*.parquet'))]
    put(folder/'part_hashes.json',refs);return refs


def http(category,url,provider,*,transport=None):
    require_published(PLAN);p=json.loads(PLAN.read_bytes());key=digest({'category':category,'url':url});folder=OUT/'http';folder.mkdir(parents=True,exist_ok=True)
    receipt_path=folder/(key+'.json')
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_bytes());body=(ROOT/receipt['body_path']).read_bytes()
        if hashlib.sha256(body).hexdigest()!=receipt['body_sha256']:raise ValueError('HTTP original changed')
        return receipt,body
    if (OUT/'provider_stops'/provider).exists():raise ValueError('Provider stopped; no retry or evasion')
    if category=='alternative_exact_case' and url not in {r['url'] for r in p['alternative_requests']}:raise ValueError('Alternative request outside frozen exact cases')
    if category not in ('alternative_exact_case','official_corroboration','schema_documentation'):raise ValueError('Unknown HTTP budget category')
    u=urlsplit(url)
    if u.scheme!='https' or u.username or u.password or u.fragment:raise ValueError('Unsafe source URL')
    if category!='alternative_exact_case':
        frozen=OUT/'reviewed_urls'/(key+'.json')
        if not frozen.exists():raise ValueError('Freeze documentation/corroboration URL before fetch')
    headers={'User-Agent':'ResearchOS-26-case-source-audit','Accept-Encoding':'identity'}
    if provider=='Tiingo':
        token=secret('TIINGO_API_KEY')
        if not token:raise ValueError('Local Tiingo credential absent; value not printed')
        headers['Authorization']='Token '+token
        starts=[]
        for path in (ROOT/'data/raw').glob('**/attempts/Tiingo/*.json'):
            r=json.loads(path.read_bytes());starts.append(datetime.fromisoformat(r['request_started_at_utc']).timestamp())
        for path in folder.glob('*.json'):
            r=json.loads(path.read_bytes())
            if r.get('provider')=='Tiingo':starts.append(datetime.fromisoformat(r['request_started_at_utc']).timestamp())
        t=time.time()
        if sum(at>t-3600 for at in set(starts))>=50 or sum(at>t-86400 for at in set(starts))>=1000:raise ValueError('Persisted free source quota reached')
    if provider=='SEC':
        from src.research.sec_pilot.acquisition import identity
        headers['User-Agent']=identity()
    reserve(category,key,url);at=now();time.sleep(.55)
    try:status,response_headers,body,final=(transport or SourceHTTP._transport)(url,headers,None)
    except Exception as e:
        partial=getattr(e,'partial_body',b'');sha=hashlib.sha256(partial).hexdigest();path=folder/(sha+'.bin')
        if not path.exists():
            with path.open('xb') as f:f.write(partial)
        put(receipt_path,{'url':url,'provider':provider,'category':category,'request_started_at_utc':at,'retrieved_at_utc':now(),'status':None,'body_path':path.relative_to(ROOT).as_posix(),'body_sha256':sha,'bytes':len(partial),'error_type':type(e).__name__,'complete':False,'headers':'REDACTED_AUTHENTICATION_CONTACT'})
        stop=OUT/'provider_stops'/provider;stop.parent.mkdir(parents=True,exist_ok=True);put(stop,{'reason':'TRANSPORT_ERROR'})
        raise ValueError('Source transport error preserved privately') from None
    sha=hashlib.sha256(body).hexdigest();path=folder/(sha+'.bin')
    if not path.exists():
        with path.open('xb') as f:f.write(body)
    receipt={'url':url,'provider':provider,'category':category,'request_started_at_utc':at,'retrieved_at_utc':now(),'status':status,'final_url':final,'body_path':path.relative_to(ROOT).as_posix(),'body_sha256':sha,'bytes':len(body),'request_headers':'REDACTED_AUTHENTICATION_CONTACT','response_headers':{k.lower():v for k,v in response_headers.items() if k.lower() in ('content-type','content-length','content-encoding','retry-after')}}
    put(receipt_path,receipt)
    if status in (403,429) or final!=url:
        stop=OUT/'provider_stops'/provider;stop.parent.mkdir(parents=True,exist_ok=True);put(stop,{'reason':'ACCESS_DENIAL_OR_REDIRECT','status':status,'url':url})
    return receipt,body


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('lake','alternative'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:p.error('Source mutation requires --execute')
    if a.operation=='lake':print('Lake parts retained',len(lake()))
    else:
        plan=json.loads(PLAN.read_bytes())
        for r in plan['alternative_requests']:
            receipt,body=http('alternative_exact_case',r['url'],'Tiingo')
            count=len(json.loads(body)) if receipt['status']==200 and isinstance(json.loads(body),list) else None
            print(r['ticker'],r['required_session'],receipt['status'],'context_rows',count,flush=True)
            if (OUT/'provider_stops/Tiingo').exists():break
