"""Source-only identity feasibility. No market outcome or experiment loader."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import hashlib
import html
import json
import re
import subprocess
import time
import uuid
from urllib.parse import quote

from src.research.spec import ROOT, digest
from src.research.phase3c.sources import put, secret, SourceHTTP
from src.research.sec_pilot.acquisition import Archive, identity, now
from src.research.item202_population import key, resolve_class

DOCS = ROOT/'docs/acceleration'
RAW = ROOT/'data/raw/item202_identity_v001'
OLD = ROOT/'data/raw/item202_historical_population_v001'
SAMPLE = DOCS/'exp006_identity_sample_v001.json'


def source_state(row):
    if row['form'] == '8-K/A': return 'AMENDMENT_VERSION_ONLY'
    return {'ORIGINAL_SIGNAL_EVENT':'ITEM202_CONFIRMED', 'NON_ITEM202':'NON_ITEM202_CONFIRMED'}.get(row['event_state'], 'UNKNOWN_ITEM_STATUS')


def allowed_pool(row, pool):
    if pool not in ('event', 'control'): raise ValueError('Unknown pool')
    return source_state(row) == ('ITEM202_CONFIRMED' if pool == 'event' else 'NON_ITEM202_CONFIRMED')


def sample_rows(rows):
    """Ten per year/quarter, rotating single/repeat/shared source strata only."""
    events = [r for r in rows if allowed_pool(r, 'event')]
    pairs = {(r['CIK'], r['accession']) for r in events}
    issuer_counts = Counter(c for c, a in pairs)
    cofilers = defaultdict(set)
    for c, a in pairs: cofilers[a].add(c)
    cells = defaultdict(dict)
    for r in events:
        cell = (r['filing_date'][:4], (int(r['filing_date'][5:7])-1)//3+1)
        p = (r['CIK'], r['accession'])
        if p not in cells[cell] or key(r) < key(cells[cell][p]): cells[cell][p] = r
    selected = []; seen = set()
    for cell in sorted(cells):
        ordered = sorted(cells[cell].values(), key=lambda r:digest(list(key(r))))
        chosen = []
        for predicate in (lambda r:issuer_counts[r['CIK']]==1,
                          lambda r:len(cofilers[r['accession']])>1,
                          lambda r:issuer_counts[r['CIK']]>1):
            hit = next((r for r in ordered if (r['CIK'],r['accession']) not in seen and r not in chosen and predicate(r)), None)
            if hit: chosen.append(hit)
        for r in ordered:
            if len(chosen)>=10: break
            if r not in chosen and (r['CIK'],r['accession']) not in seen: chosen.append(r)
        if len(chosen)!=10: raise ValueError('Source cell underfilled')
        for r in chosen:
            seen.add((r['CIK'],r['accession']))
            m=r.get('metadata') or {}; name=m.get('primary_document')
            url=None
            if name and re.fullmatch(r'[A-Za-z0-9_.-]+',name) and '..' not in name:
                url=f"https://www.sec.gov/Archives/edgar/data/{r['CIK']}/{r['accession'].replace('-','')}/{name}"
            selected.append({'source_key':list(key(r)), 'CIK':r['CIK'],'accession':r['accession'],
                'filing_date':r['filing_date'],'primary_url':url,'quarter':cell[1],
                'source_unique_issuer_events':issuer_counts[r['CIK']],
                'shared_accession':len(cofilers[r['accession']])>1,
                'metadata_sha256':digest(m)})
    if len(selected)!=240: raise ValueError('Sample must cover all 24 cells')
    return selected


def coverage(records):
    statuses=Counter(r['status'] for r in records)
    years={}
    for year in sorted({r['filing_date'][:4] for r in records}):
        part=[r for r in records if r['filing_date'].startswith(year)]
        n=sum(r['status']=='FULLY_RESOLVED' for r in part)
        years[year]={'denominator':len(part),'fully_resolved':n,'coverage_percent':100*n/len(part)}
    return {'denominator':len(records),'fully_resolved':statuses['FULLY_RESOLVED'],
            'ambiguous':statuses['AMBIGUOUS'], 'unresolved':len(records)-statuses['FULLY_RESOLVED']-statuses['AMBIGUOUS'],
            'coverage_percent':100*statuses['FULLY_RESOLVED']/len(records) if records else None,'by_year':years}


def cover_observations(body):
    """Original Inline cover fields are dated points, never effective spans."""
    text=body.decode('utf-8',errors='replace'); fields=defaultdict(list)
    for m in re.finditer(r'<ix:nonNumeric\b([^>]*)>(.*?)</ix:nonNumeric\s*>',text,re.I|re.S):
        name=re.search(r'\bname\s*=\s*[\"\']([^\"\']+)',m[1],re.I)
        if not name: continue
        concept=name[1].split(':')[-1]
        if concept in ('TradingSymbol','SecurityExchangeName','Security12bTitle','EntityCentralIndexKey'):
            value=html.unescape(re.sub('<[^>]+>',' ',m[2])).strip()
            fields[concept].append({'value':' '.join(value.split()),'character_start':m.start(),'character_end':m.end()})
    return dict(fields)


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
        limit={'SEC':252,'OpenFIGI':12,'Tiingo':12}[self.provider]
        if len(attempts)>=limit: raise ValueError('Identity request ceiling')
        if self.provider=='Tiingo':
            # Include preceding local source ledgers when enforcing 50/hour.
            recent=0; current=datetime.now(timezone.utc).timestamp()
            for pattern in ('**/attempts/Tiingo/*.json','item202_identity_v001/Tiingo/reservations/*.json'):
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


def acquire_sec():
    require_published(SAMPLE)
    sample=json.loads(SAMPLE.read_bytes()); records=sample['records']+sample.get('prior_annual_probes',[])
    urls=[r['primary_url'] for r in records if r['primary_url']]
    http=Transport('SEC',urls)
    for i,r in enumerate(records):
        target=RAW/'cover_reviews'/(digest(r['source_key'])+'.json')
        if target.exists(): continue
        if not r['primary_url']: put(target,dict(r,source_status='PRIMARY_LOCATOR_UNAVAILABLE',fields={})); continue
        receipt,body=http.fetch(r['primary_url'])
        fields=cover_observations(body) if receipt['status']==200 else {}
        put(target,dict(r,source_status='ARCHIVED' if receipt['status']==200 else 'SOURCE_UNAVAILABLE',
                       receipt=receipt,fields=fields,listing_span_certified=False))
        print('SEC identity cover',i+1,'/',len(records),flush=True)


def freeze_provider_inputs():
    candidates=[]
    for p in sorted((RAW/'cover_reviews').glob('*.json')):
        r=json.loads(p.read_bytes())
        symbols={f['value'] for f in r['fields'].get('TradingSymbol',[]) if re.fullmatch(r'[A-Za-z0-9.\-]{1,15}',f['value'])}
        if len(symbols)==1:
            candidates.append({'CIK':r['CIK'],'accession':r['accession'],'filing_date':r['filing_date'],
                               'symbol':next(iter(symbols)),'source_sha256':r['receipt']['body']['sha256']})
    seen=set(); selected=[]
    for r in sorted(candidates,key=digest):
        if r['symbol'] in seen: continue
        seen.add(r['symbol']); selected.append(r)
        if len(selected)==12: break
    value={'version':'EXP006_dated_cover_provider_inputs_v001','records':selected,'records_sha256':digest(selected),
           'selection':'First 12 distinct hash-ordered symbols from archived original Inline TradingSymbol; not current ticker lookup',
           'current_vendor_results_are_candidates_only':True,'source_sample_sha256':digest(json.loads(SAMPLE.read_bytes()))}
    put(DOCS/'exp006_identity_provider_inputs_v001.json',value)
    return value


def acquire_providers():
    require_published(SAMPLE)
    require_published(DOCS/'exp006_identity_provider_inputs_v001.json')
    inputs=json.loads((DOCS/'exp006_identity_provider_inputs_v001.json').read_bytes())['records']
    figi=Transport('OpenFIGI',{'https://api.openfigi.com/v3/mapping'})
    tiingo=Transport('Tiingo',{f"https://api.tiingo.com/tiingo/daily/{quote(r['symbol'],safe='')}" for r in inputs})
    for r in inputs:
        result={**r}
        jobs=[{'idType':'TICKER','idValue':r['symbol'],'exchCode':'US','marketSecDes':'Equity','includeUnlistedEquities':True}]
        for provider,client,url,payload in (
            ('OpenFIGI',figi,'https://api.openfigi.com/v3/mapping',jobs),
            ('Tiingo',tiingo,f"https://api.tiingo.com/tiingo/daily/{quote(r['symbol'],safe='')}",None)):
            target=RAW/'provider_reviews'/provider/(digest(r)+'.json')
            if target.exists(): continue
            receipt,body=client.fetch(url,payload)
            parsed=json.loads(body) if receipt['status']==200 else None
            put(target,dict(result,receipt=receipt,result=parsed,listing_span_certified=False))
            print(provider,'identity metadata archived',flush=True)


def require_published(path):
    relative=path.relative_to(ROOT).as_posix()
    frozen=subprocess.check_output(['git','show','origin/main:'+relative],cwd=ROOT)
    if frozen!=path.read_bytes(): raise ValueError('Identity dispatch must be pushed before remote acquisition')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('command',choices=('sec','provider-plan','providers'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.command=='provider-plan': print(freeze_provider_inputs()['records_sha256'])
    elif not a.execute: p.error('Remote acquisition requires --execute')
    elif a.command=='sec': acquire_sec()
    else: acquire_providers()
