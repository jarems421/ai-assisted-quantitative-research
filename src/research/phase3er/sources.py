"""Exact annual-header/metadata acquisition for the fixed revenue frame only."""
from pathlib import Path
import json,re
from html import unescape
from src.research.phase3c.sources import RAW as OLD,SourceHTTP,put
from src.research.sec_pilot.acquisition import ROOT,Archive,identity
from src.research.phase3c.acquire import filing_rows
from src.research.spec import digest

RAW=ROOT/'data/raw/phase3er_v001';DOCS=ROOT/'docs/acceleration'
CUTOFF='2026-09-30'
DOCUMENTS=[
 'https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf',
 'https://www.nyse.com/publicdocs/ICE_NYSE_2025_Yearly_Trading_Calendar.pdf',
 'https://www.nyse.com/trade/hours-calendars',
 'https://www.nyse.com/publicdocs/nyse/markets/american-options/rule-interpretations/2025/National_Day_of_Mourning_20250102.pdf']


class BoundedHTTP(SourceHTTP):
    LIMITS={'SEC':(990,.55),'Documentation':(24,.55)}
    def fetch(self,provider,url,**kwargs):
        validate_url(provider,url)
        return super().fetch(provider,url,**kwargs)


def validate_url(provider,url):
    if provider=='Documentation' and url in DOCUMENTS:return
    if provider=='SEC' and (re.fullmatch(r'https://data.sec.gov/submissions/CIK\d{10}(?:-submissions-\d+)?\.json',url)
        or re.fullmatch(r'https://www.sec.gov/Archives/edgar/data/\d+/\d{18}/\d{10}-\d{2}-\d{6}-index-headers\.html',url)):return
    raise ValueError('Only bounded SEC metadata/header and official calendar URLs allowed')


def cached():
    return {r['url']:r for path in sorted((OLD/'requests').glob('*.json'))
            for r in [json.loads(path.read_bytes())] if r.get('status')==200}


def header_url(cik,accession):
    if not re.fullmatch(r'\d{10}',cik) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession):raise ValueError('Unsafe identity/accession')
    return f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/{accession}-index-headers.html'


def metadata(execute=False):
    old=cached();http=BoundedHTTP(set(),root=RAW);records=[]
    cases=[r for r in json.loads((DOCS/'phase3c_pilot_cohort.json').read_bytes())['cases'] if r['revenue_candidate']]
    def load(url,case,reason):
        validate_url('SEC',url)
        q={'provider':'SEC','url':url,'case_key':case['case_key'],'reason':reason}
        put(RAW/'questions'/(digest(q)+'.json'),q)
        if url in old:return old[url],Archive(OLD).read(old[url]['body']),'phase3c_v001'
        if not execute:raise ValueError('Missing bounded metadata; explicit acquire required')
        http.allow(url);receipt,body=http.fetch('SEC',url)
        if receipt['status']!=200:raise ValueError('Metadata unavailable')
        return receipt,body,'phase3er_v001'
    for case in cases:
        receipt,body,namespace=load(case['source'],case,'Fixed-issuer annual filing-date coverage, not current class membership')
        data=json.loads(body)
        if int(data['cik'])!=int(case['issuer_cik']):raise ValueError('Issuer metadata mismatch')
        rows=filing_rows(data['filings']['recent']);contributors=[receipt['body']['sha256']]
        for part in data['filings'].get('files',[]):
            if part['filingTo']<'2018-01-01' or part['filingFrom']>CUTOFF:continue
            url='https://data.sec.gov/submissions/'+part['name']
            rec,b,_=load(url,case,'Historical metadata part intersects original/predecessor and proposed-stage coverage')
            rows+=filing_rows(json.loads(b));contributors.append(rec['body']['sha256'])
        originals={}
        for r in sorted(rows,key=lambda r:(r['filingDate'],r['accessionNumber'])):
            if r['form']!='10-K' or not '2018-01-01'<=r.get('reportDate','')<=CUTOFF or r['filingDate']>CUTOFF:continue
            originals.setdefault(r['reportDate'],r)
        if len(originals)>9:raise ValueError('Original annual endpoint ceiling')
        for r in originals.values():records.append({'case_key':case['case_key'],'issuer_cik':case['issuer_cik'],
            'accession':r['accessionNumber'],'report_date':r['reportDate'],'filing_date':r['filingDate'],
            'metadata_acceptance_representation':r.get('acceptanceDateTime'),
            'metadata_hashes':contributors,'header_url':header_url(case['issuer_cik'],r['accessionNumber'])})
    return {'version':'phase3er_header_plan_v001','cutoff':CUTOFF,'issuer_denominator':30,'records':records,
            'purpose':'Clock and predecessor counts only; no financial facts or current-ticker binding'}


def acquire():
    identity();print('SEC identity loads successfully; value withheld',flush=True)
    plan=metadata(execute=True);put(RAW/'header_plan.json',plan)
    old=cached();http=BoundedHTTP({r['header_url'] for r in plan['records']}|set(DOCUMENTS),root=RAW)
    docs=[]
    for url in DOCUMENTS:
        validate_url('Documentation',url)
        q={'provider':'Documentation','url':url,'reason':'Opening/full-day closure evidence through elapsed historical cutoff'}
        put(RAW/'questions'/(digest(q)+'.json'),q)
        rec,_=http.fetch('Documentation',url);docs.append({'url':url,'status':rec['status'],'body':rec['body']})
    put(RAW/'calendar_documents.json',docs)
    records=[]
    for i,r in enumerate(plan['records']):
        url=r['header_url'];validate_url('SEC',url)
        q={'provider':'SEC','url':url,'case_key':r['case_key'],'accession':r['accession'],
           'reason':'Original annual acceptance civil clock and issuer evidence for stage/policy feasibility'}
        put(RAW/'questions'/(digest(q)+'.json'),q)
        if url in old:receipt=old[url];body=Archive(OLD).read(receipt['body']);namespace='phase3c_v001';hit=True
        else:receipt,body=http.fetch('SEC',url);namespace='phase3er_v001';hit=False
        text=unescape(body.decode('utf-8',errors='strict')) if receipt['status']==200 else ''
        matches=re.findall(r'ACCEPTANCE-DATETIME[>\s:]+(\d{14})',text)
        ciks=re.findall(r'CENTRAL INDEX KEY[>\s:]+(\d+)',text)
        verified=bool(ciks and int(ciks[0])==int(r['issuer_cik']))
        record=dict(r,acceptance_raw=matches[0] if len(set(matches))==1 else None,
                    header_issuer_verified=verified,header_sha256=receipt['body']['sha256'],
                    receipt_namespace=namespace,retrieved_at_utc=receipt['retrieved_at_utc'],
                    status=receipt['status'],existing_archive_hit=hit)
        put(RAW/'header_records'/(r['accession']+'.json'),record);records.append(record)
        if i%20==0:print('Header coverage examined',i+1,'/',len(plan['records']),flush=True)
    summary={'version':'phase3er_source_metadata_v001','issuer_denominator':30,'records':records,
             'calendar_documents':[dict(r,body_sha256=r['body']['sha256']) for r in docs],
             'source_facts':'Filing metadata and headers only; original annual accounting bodies not acquired',
             'cutoff':CUTOFF,'all_cases_retained':True}
    put(RAW/'source_summary.json',summary)
    (DOCS/'phase3e_redesign_source_metadata.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return summary
