"""Pinned disclosure snapshot acquisition; original bytes and reviewed redirects."""
import argparse,hashlib,json
from pathlib import Path
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.integrations.http import BoundedHTTP
from src.research.item202_identity import require_published
from src.research.surfaces.congressional import CongressionalDisclosuresAdapter,TABLES

DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/exp007_congress_v001'
OLD=ROOT/'data/raw/integration_v002/comparison'
PLAN=DOCS/'exp007_source_sprint_contract.json'


def pinned_manifest_retrieved_at():
    pin=json.loads((OLD/'snapshot_pin.json').read_bytes())
    receipts=[json.loads(f.read_bytes()) for f in (OLD/'CONGRESS/receipts').glob('*.json')]
    times=[r['retrieved_at_utc'] for r in receipts if r.get('body',{}).get('sha256')==pin['source_sha256']]
    if not times:raise ValueError('Pinned manifest retrieval provenance unavailable')
    return min(times)


class SprintHTTP(BoundedHTTP):
    """Reuse audited transport with this task's own persisted source ceilings."""
    def __init__(self,stage,provider,*,transport=None,sleep=None):
        super().__init__(RAW/stage,provider,32,transport=transport,sleep=sleep)
        plan=json.loads(PLAN.read_bytes())
        ceiling=plan['source_snapshot_requests_ceiling' if stage=='snapshot' else 'original_validation_requests_ceiling']
        self.m.update(version='EXP007_source_dispatch_v001',request_ceiling=ceiling,
                      source_sprint_contract_sha256=digest(plan),retry={'transient_statuses':[]})


def acquire_snapshot():
    require_published(PLAN);plan=json.loads(PLAN.read_bytes());manifest=json.loads((OLD/'snapshot_manifest.json').read_bytes())
    if digest(manifest)!=plan['snapshot_manifest_sha256']:raise ValueError('Pinned manifest changed')
    completed=RAW/'snapshot_acquisition.json'
    if completed.exists():
        result=json.loads(completed.read_bytes())
        if result['plan_sha256']!=digest(plan):raise ValueError('Completed snapshot contract changed')
        a=CongressionalDisclosuresAdapter(manifest,RAW/'snapshot_files',revision=plan['snapshot_revision'],retrieved_at=pinned_manifest_retrieved_at())
        for f in plan['table_files']:a.verify(f)
        return result
    adapter=CongressionalDisclosuresAdapter(manifest,OLD/'snapshot_files',revision=plan['snapshot_revision'],retrieved_at=pinned_manifest_retrieved_at())
    http=SprintHTTP('snapshot','CONGRESS');results=[]
    for i,f in enumerate(plan['table_files']):
        target=RAW/'snapshot_files'/f['publicPath'];cache_hit=False
        if target.exists():
            body=target.read_bytes();cache_hit=True
        elif (OLD/'snapshot_files'/f['publicPath']).exists():
            body=adapter.verify(f).read_bytes();cache_hit=True
        else:
            receipt,body=http.fetch_reviewed(f['url'],'PINNED_DISCLOSURE_PARQUET')
            if receipt['status']!=200:raise ValueError('Disclosure snapshot source unavailable')
        if len(body)!=f['size'] or hashlib.sha256(body).hexdigest()!=f['sha256']:raise ValueError('Pinned Parquet integrity failure')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:stream.write(body)
        results.append({'table':f['table'],'year':f['year'],'publicPath':f['publicPath'],'sha256':f['sha256'],'bytes':len(body),'cache_hit':cache_hit})
        print('Verified pinned table',i+1,'/',len(plan['table_files']),flush=True)
    value={'plan_sha256':digest(plan),'files':results,'files_sha256':digest(results),'starts':len(http.starts()),
           'cache_hits':sum(x['cache_hit'] for x in results),'snapshot_revision':plan['snapshot_revision']}
    put(RAW/'snapshot_acquisition.json',value);return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:p.error('Remote source acquisition requires --execute')
    print(acquire_snapshot())
