"""Last bounded check of independently indexed cofiler paths; no first-root absence inference."""
from collections import Counter
import argparse
import json

from src.research.spec import digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_population_acquire import RAW,DOCS,IndexHTTP,manifest
from src.research.item202_availability import parse_header
from src.research.item202_population import event_state,KEY_FIELDS
from src.research.item202_historical_continue import GROUPS,cache


def freeze():
    manifest();parent=json.loads((DOCS/'exp006_historical_population_certificate_v002.json').read_bytes())
    review=json.loads((DOCS/'exp006_historical_header_review_v002.json').read_bytes());lookup={r['accession']:r for r in review['records']}
    records=[]
    for result in parent['source_header_representation_audit']:
        if result['original_found']:continue
        row=lookup[result['accession']];old_urls={r['url'] for r in result['representations']}
        for cik in sorted({k['CIK'] for k in row['keys']},key=int):
            acc=row['accession'];base=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/"
            source=next(k for k in row['keys'] if k['CIK']==cik)
            urls=[base+acc+'-index-headers.html',base+acc+'.hdr.sgml','https://www.sec.gov/Archives/'+source['source_path']]
            new=[u for u in urls if u not in old_urls]
            if new:records.append({'accession':acc,'path_filer_CIK':cik,'keys':row['keys'],'urls':new})
    current=sum(len(list((RAW/g/'reservations').glob('*.json'))) for g in GROUPS)
    d={'version':'EXP006_other_indexed_cofiler_paths_v003','records':records,
       'parent_certificate_sha256':digest(parent),'previous_starts':current,'combined_ceiling':1000,
       'new_url_ceiling':sum(len(r['urls']) for r in records),
       'selection':'Only independently indexed other legal-filer paths for accessions missing on the first filer path. No new accession, ticker, host, current-survivor lookup or denied-route retry.',
       'cofiler_semantics':'One missing filer path does not prove the whole accession absent. All raw keys retained; successful header must explicitly contain each source filer CIK; no accession-only deduplication.'}
    put(DOCS/'exp006_historical_cofiler_dispatch_v003.json',d)
    return {'other_filer_paths':len(records),'new_URL_ceiling':d['new_url_ceiling'],'combined_starts_before':current}


def acquire():
    dispatch=json.loads((DOCS/'exp006_historical_cofiler_dispatch_v003.json').read_bytes())
    h=IndexHTTP('cofiler_headers',[u for r in dispatch['records'] for u in r['urls']],dispatch['new_url_ceiling'],allow_document_404=True)
    for row in dispatch['records']:
        for url in row['urls']:
            if sum(len(list((RAW/g/'reservations').glob('*.json'))) for g in (*GROUPS,'cofiler_headers'))>=1000:raise ValueError('Combined original ceiling')
            try:r,b=h.fetch(url)
            except ValueError:return finalize()
            if r['status']==200:break
    return finalize()


def finalize():
    parent=json.loads((DOCS/'exp006_historical_population_certificate_v002.json').read_bytes())
    dispatch=json.loads((DOCS/'exp006_historical_cofiler_dispatch_v003.json').read_bytes())
    source=json.loads((RAW/'resolved_population_v002.json').read_bytes())
    if source['sha256']!=parent['resolved_population_sha256'] or digest(source['rows'])!=source['sha256']:raise ValueError('Parent changed')
    additional={};receipts=[]
    for p in (RAW/'cofiler_headers/receipts').glob('*.json'):
        r=json.loads(p.read_bytes());receipts.append(r)
        if r['status']!=200:continue
        row=next(x for x in dispatch['records'] if r['url'] in x['urls']);body=Archive(RAW/'cofiler_headers').read(r['body'])
        if r['url'].endswith('.txt'):body=body.split(b'<DOCUMENT>',1)[0]
        for original in row['keys']:
            parsed=parse_header(body,cik=original['CIK'],accession=original['accession'],form='8-K')
            if parsed['source_chronology_contradictory'] or not parsed['source_items']:continue
            present='2.02' in parsed['source_items'];filed=parsed['FILED_AS_OF_DATE']
            day=filed[:4]+'-'+filed[4:6]+'-'+filed[6:] if filed else None
            additional[tuple(original[k] for k in KEY_FIELDS)]={'state':event_state('8-K',present),'Item202':present,
                'header_FILED_AS_OF_DATE':day,'index_filed_date_matches_header':day==original['filing_date'],
                'source_url':r['url'],'original_response_sha256':r['body']['sha256'],'source_identity_and_form_verified':True,
                'raw_index_key_retained':True}
    final=[]
    for row in source['rows']:
        k=tuple(row[x] for x in KEY_FIELDS)
        if k in additional:
            a=additional[k];row=dict(row,event_state=a['state'],source_Item202_present=a['Item202'],original_header_review=a)
        final.append(row)
    put(RAW/'resolved_population_final.json',{'rows':final,'sha256':digest(final)})
    unknown=[r for r in final if r['form']=='8-K' and r['event_state']=='UNKNOWN']
    all_keys={(r['CIK'],r['accession']) for r in final};accs={r['accession'] for r in final}
    candidates=[r for r in final if r['event_state']=='ORIGINAL_SIGNAL_EVENT']
    result=dict(parent,version='EXP006_historical_population_certificate_v003_final',
        status='HISTORICAL_ITEM_STATUS_BLOCKED' if unknown else 'SOURCE_POPULATION_RECONSTRUCTED_WITH_EXPLICIT_VERSION_LIMITATIONS',
        parent_certificate_sha256=digest(parent),cofiler_dispatch_sha256=digest(dispatch),resolved_population_sha256=digest(final),
        historical_Item_header_starts=sum(len(list((RAW/g/'reservations').glob('*.json'))) for g in (*GROUPS,'cofiler_headers')),
        additional_known_filer_paths_starts=len(receipts),additional_known_filer_paths_originals_found=sum(r['status']==200 for r in receipts),
        additional_source_rows_resolved=len(additional),
        candidate_original_Item202_rows=len(candidates),candidate_original_unique_filer_accession_count=len({(r['CIK'],r['accession']) for r in candidates}),
        candidate_original_unique_accessions=len({r['accession'] for r in candidates}),candidate_original_unique_CIKs=len({r['CIK'] for r in candidates}),
        unresolved_original_Item_source_rows=len(unknown),unresolved_original_Item_accessions=len({r['accession'] for r in unknown}),
        unresolved_original_Item_years=dict(Counter(r['filing_date'][:4] for r in unknown)),
        unknown_metadata_is_not_negative_Item=True,
        shared_accession_cofiler_extra_legal_filer_keys=len(all_keys)-len(accs),
        same_filer_accession_date_form_path_variant_extra_keys=len(final)-len(all_keys),
        extra_source_keys_per_accession=len(final)-len(accs),
        identity_status='DEFERRED_POPULATION_ITEM_MEMBERSHIP_STOP' if unknown else 'NEXT_REQUIRED_180_CANDIDATE_FEASIBILITY',
        Item_scope_limit='Source labels remain UNKNOWN on unrecovered originals, never nonItem2.02. No corrected original or amendment is substituted retrospectively.',
        original_missing_does_not_prove_legal_removal=True,
        further_raw_archive_fallback='Not launched: daily indexes succeeded; whole-day archives previously exceeded transfer bounds and prior stops remain. No huge Feed/Oldloads campaign or source recreation.',
        performance_evaluations=0,confirmation_accesses=0)
    put(DOCS/'exp006_historical_population_certificate_v003.json',result)
    put(RAW/'unresolved_source_keys_final.json',{'keys':[{k:r[k] for k in (*KEY_FIELDS,'population_state')} for r in unknown],
                                             'sha256':digest([{k:r[k] for k in (*KEY_FIELDS,'population_state')} for r in unknown])})
    return {k:result[k] for k in ('status','candidate_original_Item202_rows','candidate_original_unique_filer_accession_count','unresolved_original_Item_source_rows','unresolved_original_Item_accessions','historical_Item_header_starts','additional_known_filer_paths_originals_found')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('freeze','acquire','finalize'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.mode=='acquire' and not a.execute:p.error('Remote requests require --execute')
    print({'freeze':freeze,'acquire':acquire,'finalize':finalize}[a.mode]())


if __name__=='__main__':main()
