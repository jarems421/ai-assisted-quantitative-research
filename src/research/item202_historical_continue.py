"""Reviewed non-denial header representation fallback within the same budget."""
from collections import Counter
import argparse
import json
import re

from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_population_acquire import RAW,DOCS,IndexHTTP,manifest
from src.research.item202_availability import parse_header
from src.research.item202_population import event_state

GROUPS=('unresolved_headers','unresolved_headers_continued','unresolved_header_representations')


def freeze():
    manifest();old=json.loads((RAW/'unresolved_headers/stop.json').read_bytes())
    requests=[json.loads(p.read_bytes()) for p in (RAW/'unresolved_headers/receipts').glob('*.json')]
    failed=[r for r in requests if r['url']==old['url']]
    if len(failed)!=1 or failed[0]['status']!=404:raise ValueError('Only evidenced non-denial404 permits representation review')
    frame=json.loads((DOCS/'exp006_historical_Item_resolution_dispatch.json').read_bytes())
    visited={r['url'] for r in requests};records=[]
    for row in frame['records']:
        base=row['header_url'].rsplit('/',1)[0]+'/'
        source=min(row['keys'],key=lambda r:int(r['CIK']))
        records.append(dict(row,original_header_url=row['header_url'],
                            original_source_urls=[base+row['accession']+'.hdr.sgml',
                                                  'https://www.sec.gov/Archives/'+source['source_path']],
                            original_html_already_visited=row['header_url'] in visited))
    review={'version':'EXP006_original_header_representation_review_v002','reviewed_stop_sha256':digest(old),
            'reviewed_response_sha256':digest(failed[0]),'parent_dispatch_sha256':digest(frame),
            'parent_certificate_sha256':digest(json.loads((DOCS/'exp006_historical_population_certificate.json').read_bytes())),
            'remaining_start_ceiling':1000-len(requests),'combined_all_group_start_ceiling':1000,
            'basis':'Archived official Accessing EDGAR Data guide documents accession .hdr.sgml headers and raw submission text paths. Observed404 NoSuchKey is not denial; source availability unknown until equivalent original representation checked.',
            'old_stop_and_response_preserved':True,'denied_or_uncertain_requests_never_retried':True,
            'selection':'Same625 accessions; reuse ten successful originals and every completed response. HTML URL never repeats. Only on404 try frozen .hdr.sgml then source-index .txt; stop on403/429, redirect or transport uncertainty.',
            'dates':'Index dates remain source observations; header FILED AS OF DATE is a separate primary field. Item membership requires exact filer/form/accession, not equality of index and header date labels.',
            'records':records,'performance_evaluations':0,'confirmation_accesses':0}
    put(DOCS/'exp006_historical_header_review_v002.json',review)
    return {'status':'EXACT_REPRESENTATION_CONTINUATION_FROZEN','records':len(records),'remaining_starts':review['remaining_start_ceiling']}


def cache():
    output={}
    for group in GROUPS:
        for p in (RAW/group/'receipts').glob('*.json'):
            r=json.loads(p.read_bytes());output[r['url']]=(RAW/group,r)
    return output


def acquire():
    review=json.loads((DOCS/'exp006_historical_header_review_v002.json').read_bytes())
    if digest(json.loads((RAW/'unresolved_headers/stop.json').read_bytes()))!=review['reviewed_stop_sha256']:
        raise ValueError('Reviewed original stop changed')
    known=cache()
    urls=[r['header_url'] for r in review['records'] if not r['original_html_already_visited']]
    html=IndexHTTP('unresolved_headers_continued',urls,review['remaining_start_ceiling'],allow_document_404=True)
    extra=IndexHTTP('unresolved_header_representations',[u for r in review['records'] for u in r['original_source_urls']],review['remaining_start_ceiling'],allow_document_404=True)
    def get(client,url):
        if url in known:
            root,r=known[url];return r,Archive(root).read(r['body'])
        if sum(len(list((RAW/g/'reservations').glob('*.json'))) for g in GROUPS)>=1000:
            raise ValueError('Combined original retrieval start ceiling')
        r,b=client.fetch(url);known[url]=(client.root,r);return r,b
    for i,row in enumerate(review['records']):
        try:
            r,b=get(html,row['header_url'])
            if r['status']==404:
                for alternative in row['original_source_urls']:
                    r,b=get(extra,alternative)
                    if r['status']==200:break
        except ValueError:break
        if (i+1)%25==0:print('Original membership audit',i+1,'/',len(review['records']),'starts',sum(len(list((RAW/g/'reservations').glob('*.json'))) for g in GROUPS),flush=True)
    return audit()


def audit():
    review=json.loads((DOCS/'exp006_historical_header_review_v002.json').read_bytes());known=cache()
    data=json.loads((RAW/'classified_population.json').read_bytes())
    observed={};source_records=[]
    for row in review['records']:
        attempts=[(u,known[u]) for u in [row['header_url'],*row['original_source_urls']] if u in known]
        success=next(((u,root,r) for u,(root,r) in attempts if r['status']==200),None)
        source_records.append({'accession':row['accession'],'original_found':bool(success),
            'representations':[{'url':u,'status':r['status'],'body':r['body']} for u,(root,r) in attempts]})
        if not success:continue
        url,root,r=success;body=Archive(root).read(r['body'])
        # Submission bodies are archived intact but only their header is parsed.
        if url.endswith('.txt'):body=body.split(b'<DOCUMENT>',1)[0]
        for source in row['keys']:
            key=tuple(source[k] for k in ('CIK','accession','form','filing_date','source_path'))
            header=parse_header(body,cik=source['CIK'],accession=source['accession'],form='8-K')
            consistent=not header['source_chronology_contradictory']
            present='2.02' in header['source_items'] if consistent else None
            filed=header.get('FILED_AS_OF_DATE');day=filed[:4]+'-'+filed[4:6]+'-'+filed[6:] if filed else None
            observed[key]={'Item202':present,'state':event_state('8-K',present),
                'header_sha256':header['source_sha256'],'original_response_sha256':r['body']['sha256'],
                'source_url':url,'header_FILED_AS_OF_DATE':day,'index_filed_date_matches_header':day==source['filing_date'],
                'source_identity_and_form_verified':consistent,'raw_index_key_retained':True}
    final=[]
    for row in data['rows']:
        key=tuple(row[k] for k in ('CIK','accession','form','filing_date','source_path'))
        if key in observed:
            o=observed[key];row=dict(row,event_state=o['state'],source_Item202_present=o['Item202'],original_header_review=o)
        final.append(row)
    put(RAW/'resolved_population_v002.json',{'rows':final,'sha256':digest(final)})
    unresolved=sum(r['form']=='8-K' and r['event_state']=='UNKNOWN' for r in final)
    parent=json.loads((DOCS/'exp006_historical_population_certificate.json').read_bytes())
    result=dict(parent,version='EXP006_historical_population_certificate_v002',
        status='HISTORICAL_ITEM_STATUS_BLOCKED' if unresolved else 'SOURCE_POPULATION_RECONSTRUCTED_WITH_EXPLICIT_VERSION_LIMITATIONS',
        parent_certificate_sha256=digest(parent),review_sha256=digest(review),resolved_population_sha256=digest(final),
        historical_Item_header_starts=sum(len(list((RAW/g/'reservations').glob('*.json'))) for g in GROUPS),
        source_original_unavailability_count=None if unresolved else 0,
        observed_original_missing_all_tested_representations=sum(not r['original_found'] and len(r['representations'])==3 and all(x['status']==404 for x in r['representations']) for r in source_records),
        unvisited_original_accessions=sum(not r['representations'] for r in source_records),
        source_header_representation_audit=source_records,
        candidate_original_Item202_rows=sum(r['event_state']=='ORIGINAL_SIGNAL_EVENT' for r in final),
        candidate_original_unique_CIKs=len({r['CIK'] for r in final if r['event_state']=='ORIGINAL_SIGNAL_EVENT'}),
        candidate_original_unique_filer_accession_count=len({(r['CIK'],r['accession']) for r in final if r['event_state']=='ORIGINAL_SIGNAL_EVENT'}),
        event_states=dict(Counter(r['event_state'] for r in final)),unresolved_original_Item_source_rows=unresolved,
        observed_header_index_date_differences=sum(not r.get('original_header_review',{}).get('index_filed_date_matches_header',True) for r in final),
        identity_status='DEFERRED_POPULATION_GATE' if unresolved else 'NEXT_REQUIRED_180_CANDIDATE_FEASIBILITY',
        date_field_difference_not_Item_absence=True,performance_evaluations=0,confirmation_accesses=0)
    put(DOCS/'exp006_historical_population_certificate_v002.json',result)
    return {k:result[k] for k in ('status','candidate_original_Item202_rows','candidate_original_unique_CIKs','unresolved_original_Item_source_rows','historical_Item_header_starts','observed_original_missing_all_tested_representations')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('freeze','acquire','audit'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.mode=='acquire' and not a.execute:p.error('Source requests require --execute')
    print({'freeze':freeze,'acquire':acquire,'audit':audit}[a.mode]())


if __name__=='__main__':main()
