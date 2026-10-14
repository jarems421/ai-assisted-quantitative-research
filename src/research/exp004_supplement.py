"""Explicitly authorized same-source execution-field acquisition only.

Legacy EXP004/Nexus pause guards remain intact. This transport allowlists Lake
SQL/metadata/download endpoints and never exposes a backtest or publication API.
"""
import argparse,hashlib,json,re
from pathlib import Path
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put,secret
from src.research.prepare_exp004 import verify_freeze
from src.research.item202_identity import require_published

DOCS=ROOT/'docs/acceleration'
PLAN=DOCS/'exp004_supplement_acquisition_plan.json'
OUT=ROOT/'data/raw/EXP004/execution_inputs_v001'


def allowed_call(method,path,body,requests,known_ids):
    if method=='POST' and path=='lake/queries':
        if digest(body) not in {digest(r) for r in requests}:raise ValueError('SQL outside frozen supplemental allowlist')
        return True
    if method=='GET' and path in ('lake/catalog/lake/sec_daily_ohlc','lake/catalog/lake/dividends'):return True
    m=re.fullmatch(r'lake/queries/([^/]+)(?:/manifest|/parts/\d+)?',path)
    if method=='GET' and m and m[1] in known_ids:return True
    raise ValueError('Only scoped Lake acquisition authorized; all other operations blocked')


def client(directory,requests):
    verify_freeze();require_published(PLAN)
    key=secret('NEXUSTRADE_API_KEY');url=secret('NEXUSTRADE_API_BASE_URL')
    if not key or not url:raise ValueError('Missing local Lake credentials; no values disclosed')
    from nexustrade.client import NexusTradeClient
    c=NexusTradeClient(api_key=key,base_url=url);transport=c._transport
    req=transport.request;binary=transport.request_bytes
    def known():return {json.loads(p.read_bytes())['id'] for p in OUT.glob('*/submission.json')}
    def capture(method,path,*,bytes_call=False,**kwargs):
        allowed_call(method,path,kwargs.get('body'),requests,known())
        if (OUT/'source_stop.json').exists() or (OUT/'reconciliation_stop.json').exists():raise ValueError('Persisted source/reconciliation stop; do not automatically continue')
        n=len(list(directory.glob('wire_request_*.json')))+1
        put(directory/f'wire_request_{n:04}.json',{'method':method,'path':path,'body':kwargs.get('body'),
            'idempotency_key':kwargs.get('idempotency_key'),'binary':bytes_call})
        try:result=(binary if bytes_call else req)(method,path,**kwargs)
        except Exception as error:
            put(directory/f'wire_error_{n:04}.json',{'type':type(error).__name__,'code':getattr(error,'code',None),'status_code':getattr(error,'status_code',None),'message':str(error)})
            put(OUT/'source_stop.json',{'directory':directory.relative_to(ROOT).as_posix(),'sequence':n,'type':type(error).__name__,'action':'NO_AUTO_RETRY'})
            raise ValueError('Source request failed; private error receipt retained') from None
        if isinstance(result,bytes):
            sha=hashlib.sha256(result).hexdigest();path_bytes=directory/f'wire_bytes_{n:04}_{sha}.parquet'
            if not path_bytes.exists():
                with path_bytes.open('xb') as f:f.write(result)
            put(directory/f'wire_response_{n:04}.json',{'sha256':sha,'bytes':len(result),'path':path_bytes.relative_to(ROOT).as_posix()})
        else:put(directory/f'wire_response_{n:04}.json',result)
        return result
    transport.request=lambda method,path,**kw:capture(method,path,**kw)
    transport.request_bytes=lambda method,path,**kw:capture(method,path,bytes_call=True,**kw)
    return c


def schema(table):
    if table not in ('sec_daily_ohlc','dividends'):raise ValueError('Undeclared table')
    directory=OUT/('schema_'+table);target=directory/'schema.json'
    if target.exists():return json.loads(target.read_bytes())
    if (directory/'wire_request_0001.json').exists():raise ValueError('Existing uncertain schema attempt cannot be repeated')
    directory.mkdir(parents=True,exist_ok=True)
    value=client(directory,[]).describe_lake_table(table);put(target,value);return value


def acquire(name):
    plan=json.loads(PLAN.read_bytes());record=next(r for r in plan['requests'] if r['name']==name);request=record['request']
    directory=OUT/name;directory.mkdir(parents=True,exist_ok=True)
    if (directory/'part_hashes.json').exists():
        for p in json.loads((directory/'part_hashes.json').read_bytes()):
            if hashlib.sha256((ROOT/p['path']).read_bytes()).hexdigest()!=p['sha256']:raise ValueError('Supplemental cache changed')
        return 'VERIFIED_CACHE'
    put(directory/'request.json',request);c=client(directory,[request])
    if not (directory/'submission.json').exists():
        if (directory/'intent.json').exists():raise ValueError('Uncertain query submission; reconcile ID, never resubmit')
        key='exp004-execution-v001-'+digest(request);put(directory/'intent.json',{'request_sha256':digest(request),'idempotency_key':key})
        put(directory/'submission.json',c.create_lake_query(request,idempotency_key=key))
    from nexustrade.lake import get,LakeQueryResult
    op=json.loads((directory/'submission.json').read_bytes());handle=get(op['id'],client=c)
    if not isinstance(handle,LakeQueryResult):handle=handle.wait(timeout_seconds=40)
    put(directory/'result_receipt.json',{'id':handle.id,'row_count':handle.row_count,'result':handle.result})
    parts=handle.download(directory/'parts')
    manifest=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(parts.glob('part-*.parquet'))]
    if not manifest:raise ValueError('No supplemental parts')
    put(directory/'part_hashes.json',manifest)
    return {'id':handle.id,'rows':handle.row_count,'parts':len(manifest)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('schema','acquire'));p.add_argument('name');p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:p.error('Remote acquisition requires explicit --execute')
    result=schema(a.name) if a.operation=='schema' else acquire(a.name)
    print('Schema retained' if a.operation=='schema' else result)
