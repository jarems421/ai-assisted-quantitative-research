"""Offline daily/quarterly reconciliation and pre-outcome source classification."""
from collections import Counter,defaultdict
import json
import zipfile

from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.item202_population import reconcile,event_state,KEY_FIELDS
from src.research.item202_population_acquire import RAW,DOCS,manifest
from src.research.item202_source import metadata_labels

OLD=ROOT/'data/raw/item202_remedy_v001'


def build_population():
    m=manifest()
    acquisition=json.loads((RAW/'daily_acquisition_result.json').read_bytes())
    dispatch=json.loads((DOCS/'exp006_daily_master_dispatch.json').read_bytes())
    if len(acquisition['files'])!=len(dispatch['records']):raise ValueError('Incomplete daily archive')
    daily=[];quarterly=[]
    for part in sorted((RAW/'daily_parts').glob('*.json')):
        daily += json.loads(part.read_bytes())['rows']
    for part in sorted((OLD/'source_closure/census_parts').glob('*.json')):
        for row in json.loads(part.read_bytes())['rows']:
            quarterly.append({k:row[k] for k in (*KEY_FIELDS,'source_line','source_index_sha256')})
    r=reconcile(daily,quarterly);rows=r['rows']
    put(RAW/'reconciled_population.json',{'rows':rows,'sha256':digest(rows)})
    differences=[x for x in rows if x['population_state']!='PRESENT_BOTH' or x['metadata_conflict']]
    put(RAW/'population_differences.json',{'rows':differences,'sha256':digest(differences)})
    existing=json.loads((OLD/'source_closure/bulk_labels.json').read_bytes())
    if digest(existing['rows'])!=existing['stats']['rows_sha256']:raise ValueError('Prior bulk metadata changed')
    lookup={(x['CIK'],x['accession']):x['metadata'] for x in existing['rows'] if x['metadata']}
    missing=defaultdict(set)
    for row in rows:
        if (row['CIK'],row['accession']) not in lookup:missing[int(row['CIK'])].add(row['accession'])
    bulk=json.loads((OLD/'bulk_snapshot/result.json').read_bytes())
    extra={};members=[]
    if missing:
        with zipfile.ZipFile(OLD/'bulk_snapshot'/bulk['body']['path']) as z:
            names=set(z.namelist())
            for cik,accs in sorted(missing.items()):
                name=f'CIK{cik:010}.json'
                if name not in names:continue
                data=json.loads(z.read(name));members.append(name)
                labels=metadata_labels(data.get('filings',{}).get('recent',{}),accs)
                for f in data.get('filings',{}).get('files',[]):
                    if f['filingTo']<'2015-01-01' or f['filingFrom']>'2020-12-31':continue
                    if f['name'] not in names:continue
                    members.append(f['name']);labels+=metadata_labels(json.loads(z.read(f['name'])),accs)
                for label in labels:extra.setdefault((str(cik),label['accession']),[]).append(label)
    classified=[];unknown_accessions=set()
    for row in rows:
        known=lookup.get((row['CIK'],row['accession']))
        candidates=[known] if known else extra.get((row['CIK'],row['accession']),[])
        candidates=[c for c in candidates if c['form']==row['form'] and c['filing_date']==row['filing_date']]
        distinct={digest({k:c.get(k) for k in ('form','filing_date','items_raw','acceptance_representation','primary_document')}) for c in candidates}
        meta=candidates[0] if len(distinct)==1 else None
        present=True if meta and meta['Item202']=='PRESENT_METADATA' else False if meta and meta['Item202']=='NOT_DECLARED_METADATA' else None
        # Conflicting source keys remain explicitly unresolved. Amendment form
        # still prevents independent trading even when its Item label is unknown.
        state=event_state(row['form'],present,conflicting=row['metadata_conflict'])
        if row['form']=='8-K/A':state='AMENDMENT_VERSION_ONLY'
        if row['form']=='8-K' and (present is None or row['metadata_conflict']):unknown_accessions.add(row['accession'])
        classified.append(dict(row,source_Item202_present=present,event_state=state,metadata=meta,
                               Item_evidence='CURRENT_OFFICIAL_BULK_LABEL_SAMPLE_AUDITED' if meta else 'UNKNOWN'))
    put(RAW/'classified_population.json',{'rows':classified,'sha256':digest(classified),
                                        'extra_bulk_members_examined':members,'extra_metadata_current_company_fields_used':False,
                                        'future_Item_clock_values_interpreted':0})
    summary={'version':'EXP006_daily_quarterly_population_reconciliation_v001',
             'status':'POPULATION_ITEM_RESOLUTION_REQUIRED' if unknown_accessions else 'SOURCE_POPULATION_RECONSTRUCTED',
             'source_claim':'Union of archived SEC daily master-index observations over Development, reconciled against the present rebuilt quarterly census; retain quarterly-only keys separately, never label them invalid.',
             'daily_index_files':len(acquisition['files']),'daily_request_starts':acquisition['request_starts'],
             'daily_cache_hits':acquisition['cache_hits'],'directory_request_starts':len(list((RAW/'directories/reservations').glob('*.json'))),
             'daily_observation_rows':len(daily),'daily_union_rows':len({tuple(x[k] for k in KEY_FIELDS) for x in daily}),
             'quarterly_rows':len(quarterly),'reconciled_union_rows':len(rows),
             'population_states':dict(Counter(x['population_state'] for x in rows)),
             'daily_union_original8K':len({tuple(x[k] for k in KEY_FIELDS) for x in daily if x['form']=='8-K'}),
             'daily_union_amendment8KA':len({tuple(x[k] for k in KEY_FIELDS) for x in daily if x['form']=='8-K/A'}),
             'daily_union_unique_accessions':len({x['accession'] for x in daily}),'daily_union_unique_CIKs':len({x['CIK'] for x in daily}),
             'union_unique_accessions':len({x['accession'] for x in rows}),'union_unique_CIKs':len({x['CIK'] for x in rows}),
             'shared_accession_cofiler_extra_rows':len(rows)-len({x['accession'] for x in rows}),
             'duplicate_equivalent_daily_rows':r['daily_equivalent_extra_rows'],'duplicate_equivalent_quarterly_rows':r['quarterly_equivalent_extra_rows'],
             'conflicting_source_keys':sum(x['metadata_conflict'] for x in rows),
             'event_states':dict(Counter(x['event_state'] for x in classified)),
             'candidate_original_Item202_rows':sum(x['event_state']=='ORIGINAL_SIGNAL_EVENT' for x in classified),
             'candidate_original_unique_CIKs':len({x['CIK'] for x in classified if x['event_state']=='ORIGINAL_SIGNAL_EVENT'}),
             'unresolved_original_Item_accessions':len(unknown_accessions),'unresolved_original_Item_source_rows':sum(x['form']=='8-K' and x['event_state']=='UNKNOWN' for x in classified),
             'source_original_unavailability_count':None,'amendment_parent_links_certified':0,
             'unresolved_version_relationships':sum(x['form']=='8-K/A' for x in rows),
             'known_PAC_removal_count':None,'difference_is_not_deletion_evidence':True,'complete_legal_filing_population_claimed':False,
             'contemporaneous_ingestion_claimed':False,'daily_bytes_vintage':'Present-day historical reconstruction; publisher semantics support previous-daily versus rebuilt-quarter distinction, not a guaranteed untouched version for every document.',
             'union_sha256':digest(rows),'differences_sha256':digest(differences),'classified_rows_sha256':digest(classified),
             'difference_examples':differences[:12],'difference_actual_keys':'All exact keys and observation locators retained in ignored population_differences.json',
             'unresolved_header_accession_ceiling':m['historical_only_classification_accession_ceiling'],
             'timing_contract_unchanged':True,'performance_evaluations':0,'confirmation_accesses':0}
    put(DOCS/'exp006_historical_population_reconciliation.json',summary)
    return {k:summary[k] for k in ('status','daily_index_files','daily_union_rows','quarterly_rows','population_states','candidate_original_Item202_rows','unresolved_original_Item_accessions')}


if __name__=='__main__':print(build_population())
