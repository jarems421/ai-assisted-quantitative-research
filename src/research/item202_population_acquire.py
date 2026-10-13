"""Exact official daily-index reconstruction. Remote requests require --execute."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import uuid
from urllib.parse import urljoin

from src.research.spec import ROOT,digest
from src.research.phase3c.sources import SourceHTTP,put
from src.research.sec_pilot.acquisition import Archive,identity,now
from src.research.item202_population import parse_daily

DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/item202_historical_population_v001'
MANIFEST=DOCS/'exp006_historical_population_manifest.json'


def manifest():
    m=json.loads(MANIFEST.read_bytes())
    for name,h in m['preserved_artifacts'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('Historical artifact changed: '+name)
    if m['starting_head']!='020299da59f29fda4f1ff6f5d87bcbcbefc90f81':raise ValueError('Unexpected starting checkpoint')
    return m


class IndexHTTP:
    """Existing Archive/transport reused, with exact UA and failure provenance."""
    def __init__(self,group,urls,ceiling,*,transport=None,sleep=time.sleep):
        self.group=group;self.root=RAW/group;self.allowed=set(urls);self.ceiling=ceiling
        self.archive=Archive(self.root);self.transport=transport or SourceHTTP._transport;self.sleep=sleep
        self.manifest_sha256=digest(manifest())

    def starts(self):return list((self.root/'reservations').glob('*.json'))

    def fetch(self,url):
        if url not in self.allowed:raise ValueError('Outside exact frozen daily-index allowlist')
        completed=self.root/'completed'/(digest({'url':url})+'.json')
        if completed.exists():
            r=json.loads(completed.read_bytes());return r,self.archive.read(r['body'])
        if (self.root/'stop.json').exists():raise ValueError('Persisted daily source stop; never blind retry')
        if len(self.starts())>=self.ceiling:raise ValueError('Daily source request ceiling')
        prior=[json.loads(p.read_bytes())['request_started_at_utc'] for p in RAW.glob('*/reservations/*.json')]
        if prior:self.sleep(max(0,.6-(datetime.now(timezone.utc)-datetime.fromisoformat(max(prior))).total_seconds()))
        token=uuid.uuid4().hex
        receipt={'url':url,'request_started_at_utc':now(),'attempt':1,'manifest_sha256':self.manifest_sha256,
                 'request_headers':'LOCALLY_IDENTIFIED_SEC_USER_AGENT_REDACTED','group':self.group}
        put(self.root/'reservations'/(token+'.json'),receipt)
        try:
            status,headers,body,final=self.transport(url,{'User-Agent':identity(),'Accept-Encoding':'identity'},None)
            receipt.update(status=status,final_url=final,retrieved_at_utc=now(),body=self.archive.body('0000000000-00-000000',body),
                headers={k.lower():v for k,v in headers.items() if k.lower() in ('content-type','content-length','content-encoding','last-modified','retry-after')})
            put(self.root/'receipts'/(token+'.json'),receipt)
            if final!=url or status!=200:raise ValueError('Non200 or redirect: stop exact source channel')
            if receipt['headers'].get('content-encoding','identity').lower()!='identity':raise ValueError('Encoding not declared')
            if 'content-length' in receipt['headers'] and int(receipt['headers']['content-length'])!=len(body):raise ValueError('Response length mismatch')
            put(completed,receipt);return receipt,body
        except Exception as error:
            failure=dict(receipt,error_type=type(error).__name__)
            if hasattr(error,'partial_body'):failure['partial_body']=self.archive.body('0000000000-00-000000',error.partial_body)
            put(self.root/'errors'/(token+'.json'),failure)
            put(self.root/'stop.json',{'reason':'SOURCE_TRANSPORT_OR_BOUNDARY_STOP','failure_sha256':digest(failure),'url':url})
            raise ValueError('Daily source stopped; immutable response/error retained') from None


def directories():
    m=manifest();h=IndexHTTP('directories',m['daily_directory_routes'],m['directory_start_ceiling'])
    rows=[];sources=[]
    for url in m['daily_directory_routes']:
        r,b=h.fetch(url);sources.append(r)
        d=json.loads(b);base=url.rsplit('/',1)[0]+'/'
        year=int(url.split('/')[-3]);quarter=int(url.split('/')[-2][-1])
        for item in d.get('directory',{}).get('item',[]):
            name=item.get('name','');match=re.fullmatch(r'master\.(\d{8})\.idx',name)
            if not match:continue
            day=datetime.strptime(match[1],'%Y%m%d').date().isoformat()
            if int(day[:4])!=year or (int(day[5:7])-1)//3+1!=quarter:raise ValueError('Directory source day escapes quarter')
            rows.append({'day':day,'year':year,'quarter':quarter,'url':urljoin(base,name),
                         'directory_source_sha256':r['body']['sha256'],'publisher_size':item.get('size')})
        print('Directory',year,quarter,'master files',sum(x['year']==year and x['quarter']==quarter for x in rows),flush=True)
    if len(rows)>1650 or len({r['url'] for r in rows})!=len(rows):raise ValueError('Enumerated daily set exceeds ceiling or duplicates')
    value={'version':'EXP006_exact_daily_master_dispatch_v001','frozen_at_utc':now(),'records':sorted(rows,key=lambda r:r['day']),
           'records_sha256':digest(sorted(rows,key=lambda r:r['day'])),'directories':[{'url':r['url'],'body':r['body']} for r in sources],
           'source_documentation_sha256':m['daily_evidence_review_sha256'],'enumerated_not_invented_days':True}
    put(DOCS/'exp006_daily_master_dispatch.json',value)
    return {'status':'DAILY_ROUTES_FROZEN_BEFORE_MASTER_REQUESTS','files':len(rows),'directory_starts':len(h.starts())}


def masters():
    m=manifest();dispatch=json.loads((DOCS/'exp006_daily_master_dispatch.json').read_bytes())
    if digest(dispatch['records'])!=dispatch['records_sha256']:raise ValueError('Daily dispatch changed')
    h=IndexHTTP('daily_masters',[r['url'] for r in dispatch['records']],1650)
    cache_path=ROOT/'.research/item202_historical_population/daily_cache.json'
    cache={r['url']:r for r in json.loads(cache_path.read_bytes())} if cache_path.exists() else {}
    stats=[]
    for i,row in enumerate(dispatch['records']):
        if row['url'] in cache:
            c=cache[row['url']];r=json.loads((ROOT/c['receipt_path']).read_bytes());b=Archive(ROOT/c['root']).read(r['body']);hit=True
        else:r,b=h.fetch(row['url']);hit=False
        parsed=parse_daily(b,row['day'],r['body']['sha256'])
        part=dict(parsed,receipt=r,cache_hit=hit,source_root=cache[row['url']]['root'] if hit else h.root.relative_to(ROOT).as_posix())
        put(RAW/'daily_parts'/(row['day']+'.json'),part)
        stats.append({'day':row['day'],'rows':len(parsed['rows']),'source_sha256':r['body']['sha256'],'cache_hit':hit,'bytes':len(b)})
        if (i+1)%25==0 or i+1==len(dispatch['records']):print('Daily files',i+1,'/',len(dispatch['records']),'rows so far',sum(r['rows'] for r in stats),'starts',len(h.starts()),flush=True)
    put(RAW/'daily_acquisition_result.json',{'files':stats,'request_starts':len(h.starts()),'cache_hits':sum(r['cache_hit'] for r in stats),'status':'DAILY_ARCHIVE_COMPLETE'})
    return {'status':'DAILY_ARCHIVE_COMPLETE','files':len(stats),'starts':len(h.starts()),'rows':sum(r['rows'] for r in stats)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('directories','masters'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:p.error('Remote acquisition requires --execute')
    print(directories() if a.mode=='directories' else masters())


if __name__=='__main__':main()
