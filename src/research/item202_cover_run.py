"""Explicit v002 cover acquisition and offline feasibility review; no outcomes."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,re,subprocess,time,uuid
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put,secret,SourceHTTP
from src.research.sec_pilot.acquisition import Archive,identity,now
from src.research.item202_identity import require_published,source_state
from src.research.item202_cover import parse_cover,choose_class,event_scope
RAW=ROOT/'data/raw/item202_cover_v002'
DOCS=ROOT/'docs/acceleration'
SAMPLE=DOCS/'exp006_cover_identity_sample_v002.json'

class Transport:
    """Durable single-attempt exact routes; no redirects, prices, or retries."""
    def __init__(self, provider, urls):
        self.provider=provider; self.root=RAW/provider; self.archive=Archive(self.root); self.urls=set(urls)
    def fetch(self,url,payload=None):
        if url not in self.urls: raise ValueError('Outside frozen identity route')
        if self.provider=='Tiingo' and ('/prices' in url or '?' in url): raise ValueError('No prices in identity pilot')
        request_key=digest({'url':url,'payload':payload}); cache=self.root/'completed'/(request_key+'.json')
        if cache.exists():
            r=json.loads(cache.read_bytes()); return r,self.archive.read(r['body'])
        if (self.root/'stop.json').exists(): raise ValueError('Persistent identity source stop')
        attempts=list((self.root/'reservations').glob('*.json'))
        limit={'SEC':280,'OpenFIGI':60,'Tiingo':150}[self.provider]
        if len(attempts)>=limit: raise ValueError('Identity request ceiling')
        if self.provider=='Tiingo':
            # Include preceding local source ledgers when enforcing 50/hour.
            recent=0; current=datetime.now(timezone.utc).timestamp()
            for pattern in ('**/attempts/Tiingo/*.json','*/Tiingo/reservations/*.json'):
                for p in (ROOT/'data/raw').glob(pattern):
                    r=json.loads(p.read_bytes()); t=r.get('request_started_at_utc')
                    if t and datetime.fromisoformat(t).timestamp()>current-3600: recent+=1
            if recent>=50: raise ValueError('Tiingo hourly quota pending')
        gap={'SEC':.6,'OpenFIGI':3.1,'Tiingo':.25}[self.provider]
        if attempts:
            last=max(json.loads(p.read_bytes())['request_started_at_utc'] for p in attempts)
            time.sleep(max(0,gap-(datetime.now(timezone.utc)-datetime.fromisoformat(last)).total_seconds()))
        headers={'User-Agent':identity() if self.provider=='SEC' else 'ResearchIdentityCertification/1.0','Accept-Encoding':'identity'}
        if self.provider=='OpenFIGI': headers['Content-Type']='application/json'
        if self.provider=='Tiingo':
            token=secret('TIINGO_API_KEY')
            if not token: raise ValueError('Configured provider unavailable')
            headers['Authorization']='Token '+token
        token_id=uuid.uuid4().hex
        r={'provider':self.provider,'url':url,'payload_sha256':digest(payload),'request_started_at_utc':now(),
           'request_headers':'AUTHENTICATION_AND_CONTACT_REDACTED','attempt':1,'sample_sha256':digest(json.loads(SAMPLE.read_bytes()))}
        put(self.root/'reservations'/(token_id+'.json'),r)
        try:
            from src.research.sec_pilot.parsing import canonical
            status,h,b,final=SourceHTTP._transport(url,headers,canonical(payload) if payload is not None else None)
            r.update(status=status,final_url=final,retrieved_at_utc=now(),body=self.archive.body('0000000000-00-000000',b),
                     response_headers={k.lower():v for k,v in h.items() if k.lower() in ('content-type','content-length','content-encoding','retry-after')})
            put(self.root/'receipts'/(token_id+'.json'),r)
            if final!=url or status not in (200,404): raise ValueError('Identity source transport stop')
            if r['response_headers'].get('content-encoding','identity').lower()!='identity': raise ValueError('Encoding mismatch')
            if 'content-length' in r['response_headers'] and int(r['response_headers']['content-length'])!=len(b): raise ValueError('Incomplete response')
            put(cache,r); return r,b
        except Exception as e:
            failure=dict(r,error_type=type(e).__name__)
            if hasattr(e,'partial_body'): failure['partial_body']=self.archive.body('0000000000-00-000000',e.partial_body)
            put(self.root/'errors'/(token_id+'.json'),failure)
            put(self.root/'stop.json',{'failure_sha256':digest(failure)})
            raise ValueError('Identity source stopped; private receipt retained') from None


def acquire():
    require_published(SAMPLE)
    planned=json.loads(SAMPLE.read_bytes())['records']
    urls={r['primary_url'] for r in planned if r['primary_url']}
    http=Transport('SEC',urls)
    # Exact previous originals are cache evidence, not new dispatches.
    caches={}
    for root in (ROOT/'data/raw/item202_identity_v001/SEC',ROOT/'data/raw/item202_date_repair_v001/primary'):
        for p in (root/'receipts').glob('*.json'):
            r=json.loads(p.read_bytes())
            if r.get('url') in urls and r.get('status')==200:caches[r['url']]=(root,r)
    for i,r in enumerate(planned):
        target=RAW/'acquisition'/(digest(r['source_key'])+'.json')
        if target.exists():continue
        url=r['primary_url']
        if not url:
            put(target,dict(r,source_status='PRIMARY_LOCATOR_UNAVAILABLE',receipt=None));continue
        if url in caches:
            root,receipt=caches[url];body=Archive(root).read(receipt['body']);cache_hit=True
        else:
            receipt,body=http.fetch(url);root=RAW/'SEC';cache_hit=False
        put(target,dict(r,source_status='ARCHIVED' if receipt['status']==200 else 'UNAVAILABLE',
            receipt=receipt,source_root=root.relative_to(ROOT).as_posix(),cache_hit=cache_hit))
        print('Frozen cover',i+1,'/',len(planned),'archived',flush=True)


def review():
    sample=json.loads(SAMPLE.read_bytes());records=[]
    for planned in sample['records']:
        r=json.loads((RAW/'acquisition'/(digest(planned['source_key'])+'.json')).read_bytes())
        parsed={'rows':[],'domestic_jurisdiction_points':[]}
        if r['receipt'] and r['receipt']['status']==200:
            body=Archive(ROOT/r['source_root']).read(r['receipt']['body']);parsed=parse_cover(body)
        chosen=choose_class(parsed['rows']);row=chosen['row'];reasons=[]
        valid=[x for x in parsed['rows'] if all(x.get(k) and x[k].lower() not in ('none','n/a','not applicable','—','-') for k in ('class_title','trading_symbol','exchange'))]
        if not valid:reasons.append('NO_COMPLETE_COVER_IDENTITY_TUPLE')
        if chosen['status']!='SINGLE_COMMON_CANDIDATE':reasons.append(chosen['status'])
        if row and (not re.fullmatch(r'[A-Za-z0-9.\-]{1,15}',row['trading_symbol'])):reasons.append('SYMBOL_REPRESENTATION_UNRESOLVED')
        if row and not re.search(r'\b(?:NYSE|NASDAQ|New York Stock Exchange|Cboe)\b',row['exchange'],re.I):reasons.append('US_MARKET_CONTEXT_UNRESOLVED')
        if not parsed['domestic_jurisdiction_points']:reasons.append('DOMESTIC_INCORPORATION_UNRESOLVED')
        if r['shared_accession']:reasons.append('COFILER_TO_EXACT_SECURITY_ISSUER_UNRESOLVED')
        records.append({'source_key':r['source_key'],'CIK':r['CIK'],'accession':r['accession'],'filing_date':r['filing_date'],
            'quarter':r['quarter'],'shared_accession':r['shared_accession'],'source_unique_issuer_events':r['source_unique_issuer_events'],
            'parsed':parsed,'complete_cover_tuple':bool(valid),'common_count':chosen['common_count'],
            'single_common_cover':chosen['status']=='SINGLE_COMMON_CANDIDATE','SEC_identity_candidate':not reasons,
            'selected_common_row':row,'source_failures':reasons,'source_root':r.get('source_root'),
            'cache_hit':r.get('cache_hit',False),'receipt':r['receipt']})
    value={'version':'EXP006_human_cover_review_v001','sample_sha256':digest(sample),'records':records,
           'records_sha256':digest(records),'cover_tuple_count':sum(r['complete_cover_tuple'] for r in records),
           'single_common_count':sum(r['single_common_cover'] for r in records),
           'multiple_common_count':sum(r['common_count']>1 for r in records),
           'SEC_identity_candidate_count':sum(r['SEC_identity_candidate'] for r in records),
           'source_failure_counts':dict(Counter(x for r in records for x in r['source_failures']))}
    put(RAW/'cover_review_v001.json',value)
    print({k:v for k,v in value.items() if k not in ('records',)})
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('acquire','review'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.command=='review':review()
    elif not a.execute:p.error('Remote acquisition requires --execute')
    else:acquire()

