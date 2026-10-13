"""Bounded unresolved-original Item retrieval, never one request per known row."""
from collections import Counter,defaultdict
import argparse
import json

from src.research.spec import digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_population_acquire import IndexHTTP,RAW,DOCS,manifest
from src.research.item202_availability import parse_header
from src.research.item202_population import event_state


def prepare():
    m=manifest();summary=json.loads((DOCS/'exp006_historical_population_reconciliation.json').read_bytes())
    data=json.loads((RAW/'classified_population.json').read_bytes())
    if digest(data['rows'])!=data['sha256']:raise ValueError('Classified population changed')
    unknown=defaultdict(list)
    for row in data['rows']:
        if row['form']=='8-K' and row['event_state']=='UNKNOWN':unknown[row['accession']].append(row)
    dispatch={'version':'EXP006_historical_original_Item_resolution_dispatch_v001','accession_count':len(unknown),
              'source_key_count':sum(map(len,unknown.values())),'ceiling':m['historical_only_classification_accession_ceiling'],
              'status':'HISTORICAL_ITEM_SCALING_BLOCKED' if len(unknown)>m['historical_only_classification_accession_ceiling'] else 'BOUNDED_ORIGINAL_HEADER_DISPATCH_READY',
              'selection':'All unresolved original keys, grouped by accession for a single request; full legal-filer keys retained. Cache first. No missing Item assumed false.',
              'records':[{'accession':acc,'keys':[{k:r[k] for k in ('CIK','accession','form','filing_date','source_path','population_state')} for r in rows],
                          'header_url':f"https://www.sec.gov/Archives/edgar/data/{int(min(rows,key=lambda r:int(r['CIK']))['CIK'])}/{acc.replace('-','')}/{acc}-index-headers.html"} for acc,rows in sorted(unknown.items())],
              'parent_population_sha256':data['sha256'],'performance_evaluations':0,'confirmation_accesses':0}
    put(DOCS/'exp006_historical_Item_resolution_dispatch.json',dispatch)
    return {k:dispatch[k] for k in ('status','accession_count','source_key_count','ceiling')}


def acquire():
    dispatch=json.loads((DOCS/'exp006_historical_Item_resolution_dispatch.json').read_bytes())
    if dispatch['status']!='BOUNDED_ORIGINAL_HEADER_DISPATCH_READY':raise ValueError('Unexpectedly large original retrieval campaign; stop')
    h=IndexHTTP('unresolved_headers',[r['header_url'] for r in dispatch['records']],dispatch['ceiling'])
    # Reuse all prior original headers only after their original hash verifies.
    cache={}
    for group in ('data/raw/item202_remedy_v001/chronology_headers','data/raw/item202_date_repair_v001/headers'):
        from src.research.spec import ROOT
        for p in (ROOT/group/'receipts').glob('*.json'):
            r=json.loads(p.read_bytes())
            if r.get('status')==200:cache[r['url']]=(ROOT/group,r)
    for i,row in enumerate(dispatch['records']):
        if row['header_url'] in cache:
            root,r=cache[row['header_url']];body=Archive(root).read(r['body'])
            put(RAW/'unresolved_header_cache'/(row['accession']+'.json'),{'receipt':r,'root':root.as_posix()})
        else:
            try:r,body=h.fetch(row['header_url'])
            except ValueError:break
        if (i+1)%25==0:print('Unresolved originals',i+1,'/',len(dispatch['records']),flush=True)
    return review()


def review():
    dispatch=json.loads((DOCS/'exp006_historical_Item_resolution_dispatch.json').read_bytes())
    data=json.loads((RAW/'classified_population.json').read_bytes())
    if data['sha256']!=dispatch['parent_population_sha256'] or digest(data['rows'])!=data['sha256']:raise ValueError('Parent population changed')
    observed={};known_unavailable=0;source_headers=[]
    for row in dispatch['records']:
        cached=RAW/'unresolved_header_cache'/(row['accession']+'.json')
        completed=RAW/'unresolved_headers/completed'/(digest({'url':row['header_url']})+'.json')
        if cached.exists():
            c=json.loads(cached.read_bytes());r=c['receipt'];body=Archive(c['root']).read(r['body'])
        elif completed.exists():r=json.loads(completed.read_bytes());body=Archive(RAW/'unresolved_headers').read(r['body'])
        else:
            matches=[]
            for p in (RAW/'unresolved_headers/receipts').glob('*.json'):
                r=json.loads(p.read_bytes())
                if r['url']==row['header_url']:matches.append(r)
            if not matches:continue
            r=matches[-1];body=Archive(RAW/'unresolved_headers').read(r['body'])
        source_headers.append({'accession':row['accession'],'status':r['status'],'source_sha256':r['body']['sha256'],'bytes':r['body']['bytes']})
        for source in row['keys']:
            key=(source['CIK'],source['accession'],source['form'],source['filing_date'],source['source_path'])
            if r['status']!=200:
                observed[key]={'Item202':None,'state':'SOURCE_REMOVED_OR_UNAVAILABLE','reason':'Observed source unavailability, not proven legal removal'};known_unavailable+=1;continue
            header=parse_header(body,cik=source['CIK'],accession=source['accession'],form=source['form'])
            filed=header.get('FILED_AS_OF_DATE');source_day=filed[:4]+'-'+filed[4:6]+'-'+filed[6:] if filed else None
            consistent=not header['source_chronology_contradictory'] and source_day==source['filing_date']
            present='2.02' in header['source_items'] if consistent else None
            observed[key]={'Item202':present,'state':event_state('8-K',present),'header_sha256':header['source_sha256'],
                           'reason':'Exact original source header matches filer/form/date/accession' if consistent else 'Original/current header conflicts with retained index key; no retrospective overwrite'}
    final=[]
    for row in data['rows']:
        key=tuple(row[k] for k in ('CIK','accession','form','filing_date','source_path'))
        if key in observed:
            value=observed[key];row=dict(row,event_state=value['state'],source_Item202_present=value['Item202'],original_header_review=value)
        final.append(row)
    put(RAW/'resolved_population.json',{'rows':final,'sha256':digest(final)})
    unresolved=sum(r['form']=='8-K' and r['event_state'] in ('UNKNOWN','SOURCE_REMOVED_OR_UNAVAILABLE') for r in final)
    summary=json.loads((DOCS/'exp006_historical_population_reconciliation.json').read_bytes())
    cert=dict(summary,version='EXP006_historical_population_certificate_v001',
              status='HISTORICAL_ITEM_SCALING_BLOCKED' if dispatch['status']=='HISTORICAL_ITEM_SCALING_BLOCKED' else 'HISTORICAL_ITEM_STATUS_BLOCKED' if unresolved else 'SOURCE_POPULATION_RECONSTRUCTED_WITH_EXPLICIT_VERSION_LIMITATIONS',
              resolved_population_sha256=digest(final),historical_Item_header_starts=len(list((RAW/'unresolved_headers/reservations').glob('*.json'))),
              historical_Item_header_audits=len(source_headers),header_sources=source_headers,
              candidate_original_Item202_rows=sum(r['event_state']=='ORIGINAL_SIGNAL_EVENT' for r in final),
              candidate_original_unique_CIKs=len({r['CIK'] for r in final if r['event_state']=='ORIGINAL_SIGNAL_EVENT'}),
              event_states=dict(Counter(r['event_state'] for r in final)),unresolved_original_Item_source_rows=unresolved,
              source_original_unavailability_count=known_unavailable if unresolved==0 else None,
              observed_source_unavailability_keys=known_unavailable,
              Item_membership_role='Source candidates from audited metadata/original headers, not certified equity identities or realized trades. Original primary validation remains sampled.',
              identity_status='DEFERRED_POPULATION_GATE' if unresolved else 'NEXT_REQUIRED_180_CANDIDATE_FEASIBILITY',
              original_and_amendment_information_never_retroactively_overwritten=True,
              performance_evaluations=0,confirmation_accesses=0)
    put(DOCS/'exp006_historical_population_certificate.json',cert)
    return {k:cert[k] for k in ('status','candidate_original_Item202_rows','candidate_original_unique_CIKs','unresolved_original_Item_source_rows','historical_Item_header_starts')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','acquire','review'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.mode=='acquire' and not a.execute:p.error('Remote header requests require --execute')
    print({'prepare':prepare,'acquire':acquire,'review':review}[a.mode]())


if __name__=='__main__':main()
