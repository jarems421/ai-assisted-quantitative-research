"""Frozen-price-only acquisition; immutable identity and old stops stay intact."""
import argparse,hashlib,json
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put,secret
from src.research.prepare_exp004 import verify_freeze
from src.research.item202_identity import require_published
from src.research.exp004_supplement import allowed_call

PLAN=ROOT/'docs/acceleration/exp004_frozen_price_acquisition_plan_v001.json'
OUT=ROOT/'data/raw/EXP004/frozen_price_bridge_v001/prices'


def acquire(name):
    verify_freeze();require_published(PLAN)
    plan=json.loads(PLAN.read_bytes());record=next(r for r in plan['requests'] if r['name']==name);request=record['request'];base=OUT;directory=base/name;directory.mkdir(parents=True,exist_ok=True)
    if (base/'reconciliation_stop.json').exists() or (base.parent/'execution_input_stop.json').exists():raise ValueError('Price enrichment/execution input stopped; no continuation')
    cert=ROOT/'docs/acceleration/exp004_frozen_price_bridge_v001.json';require_published(cert)
    if hashlib.sha256(cert.read_bytes()).hexdigest()!=plan['bridge_sha256']:raise ValueError('Source bridge changed')
    return acquire_in(directory,request)


def acquire_in(OUT,request):
    if (OUT/'part_hashes.json').exists():
        for r in json.loads((OUT/'part_hashes.json').read_bytes()):
            if hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Price cache hash changed')
        return 'VERIFIED_CACHE'
    if (OUT/'source_stop.json').exists():raise ValueError('Price source stopped; no automatic retry')
    key=secret('NEXUSTRADE_API_KEY');url=secret('NEXUSTRADE_API_BASE_URL')
    if not key or not url:raise ValueError('Missing local credentials; no values exposed')
    from nexustrade.client import NexusTradeClient
    c=NexusTradeClient(api_key=key,base_url=url);t=c._transport;raw=t.request;binary=t.request_bytes
    def capture(method,path,*,bytes_call=False,**kw):
        known={json.loads((OUT/'submission.json').read_bytes())['id']} if (OUT/'submission.json').exists() else set()
        # No schema endpoint or other SQL is authorized by this one-query plan.
        if path.startswith('lake/catalog/'):raise ValueError('No new identity schema query authorized')
        allowed_call(method,path,kw.get('body'),[request],known)
        n=len(list(OUT.glob('wire_request_*.json')))+1
        put(OUT/f'wire_request_{n:04}.json',{'method':method,'path':path,'body':kw.get('body'),'idempotency_key':kw.get('idempotency_key'),'binary':bytes_call})
        try:value=(binary if bytes_call else raw)(method,path,**kw)
        except Exception as error:
            put(OUT/f'wire_error_{n:04}.json',{'type':type(error).__name__,'message':str(error)})
            put(OUT/'source_stop.json',{'status':'LOCAL_EXECUTION_INPUTS_BLOCKED','automatic_retry':False})
            raise ValueError('Price source error preserved privately') from None
        if isinstance(value,bytes):
            sha=hashlib.sha256(value).hexdigest();p=OUT/f'wire_bytes_{n:04}_{sha}.parquet'
            with p.open('xb') as f:f.write(value)
            put(OUT/f'wire_response_{n:04}.json',{'sha256':sha,'bytes':len(value),'path':p.relative_to(ROOT).as_posix()})
        else:put(OUT/f'wire_response_{n:04}.json',value)
        return value
    t.request=lambda method,path,**kw:capture(method,path,**kw)
    t.request_bytes=lambda method,path,**kw:capture(method,path,bytes_call=True,**kw)
    put(OUT/'request.json',request)
    if not (OUT/'submission.json').exists():
        if (OUT/'intent.json').exists():raise ValueError('Uncertain identity query; never resubmit')
        identity_key='exp004-frozen-price-v001-'+digest(request);put(OUT/'intent.json',{'idempotency_key':identity_key})
        put(OUT/'submission.json',c.create_lake_query(request,idempotency_key=identity_key))
    from nexustrade.lake import get,LakeQueryResult
    op=json.loads((OUT/'submission.json').read_bytes());h=get(op['id'],client=c)
    if not isinstance(h,LakeQueryResult):h=h.wait(timeout_seconds=40)
    put(OUT/'result_receipt.json',{'id':h.id,'row_count':h.row_count,'result':h.result})
    parts=h.download(OUT/'parts')
    refs=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(parts.glob('part-*.parquet'))]
    if not refs:raise ValueError('No identity source parts')
    put(OUT/'part_hashes.json',refs)
    return {'id':h.id,'rows':h.row_count}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:p.error('Remote identity acquisition requires --execute')
    print(acquire(a.name))
