"""Source-only corpus reconciliation, geometry and neutral original dispatch."""
from collections import Counter,defaultdict
import json,re
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.surfaces.congressional import CongressionalDisclosuresAdapter,TABLES
from src.research.congress_sprint_source import DOCS,RAW,OLD,PLAN
from src.research.congress_sprint import classify,resolution,contributor_asof


def corpus(years=range(2012,2026)):
    plan=json.loads(PLAN.read_bytes());m=json.loads((OLD/'snapshot_manifest.json').read_bytes())
    a=CongressionalDisclosuresAdapter(m,RAW/'snapshot_files',revision=plan['snapshot_revision'],retrieved_at=m['generatedAt'])
    return {t:[r for year in years for r in a.table(t,year)] for t in TABLES}


def geometry():
    data=corpus();f,t,e=(data[k] for k in TABLES);years={}
    for year in range(2012,2026):
        prefix=str(year)
        filings=[r for r in f if r['available_at'].startswith(prefix)]
        trades=[r for r in t if r['available_at'].startswith(prefix)]
        events=[r for r in e if r['first_available_at'].startswith(prefix)]
        years[prefix]={'filings':len(filings),'trades':len(trades),'event_versions':len(events),
            'filing_chambers':dict(Counter(r['chamber'] for r in filings)),
            'filing_months':sorted({r['available_at'][:7] for r in filings}),
            'purchase_trades':sum(r['action']=='purchase' for r in trades),
            'purchase_asset_candidates':sum(classify(r)['status']=='COMMON_EQUITY_CANDIDATE' for r in trades)}
    print('Source geometry by year:',years)
    # Calendar partition support means declared snapshot observation coverage,
    # not an exhaustive legally-required disclosure universe. Require both
    # chambers and observations in all twelve months, without inferring zeros.
    credible=[int(y) for y,x in years.items() if len(x['filing_months'])==12 and set(x['filing_chambers'])=={'house','senate'}]
    spans=[];current=[]
    for year in credible:
        if current and year!=current[-1]+1:spans.append(current);current=[]
        current.append(year)
    if current:spans.append(current)
    longest=max(spans,key=lambda x:(len(x),-x[0])) if spans else []
    cut=int(len(longest)*.7+.5)
    if cut<4 or len(longest)-cut<2:raise ValueError('SOURCE_GEOMETRY_BLOCKED')
    development=[f'{longest[0]}-01-01',f'{longest[cut-1]}-12-31'];held=[f'{longest[cut]}-01-01',f'{longest[-1]}-12-31']
    version_counts=Counter();lookup={(r['chamber'],r['doc_id'],r['row_index']):r for r in t};groups=defaultdict(list)
    for event in e:
        groups[event['event_id']].append(event)
        first,available,end=event['first_available_at'],event['available_at'],event.get('superseded_at')
        if first>available or end and end<available:version_counts['contradictory_availability']+=1
        source=lookup.get((event['chamber'],event['source_doc_id'],event['source_row_index']))
        if source and source['available_at']>available:version_counts['source_row_after_version']+=1
    for items in groups.values():
        ordered=sorted(items,key=lambda x:x['version'])
        if len(ordered)>1:
            for old,new in zip(ordered,ordered[1:]):
                if old.get('superseded_at')!=new['available_at']:version_counts['noncontiguous_or_overlapping_versions']+=1
    result={'version':'EXP007_source_geometry_v001','year_counts':years,'credible_calendar_years':credible,
        'calendar_support_rule':'Observed both chambers and all12 months; largest contiguous finished-year span; no legal-exhaustiveness claim',
        'development':development,'workflow_held_out_confirmation':held,'split_rule':'Nearest integer70% early years; >=4Development/>=2confirmation',
        'snapshot_evidence_tier':'AUDITED_EXTERNAL_DERIVED','row_counts':{k:len(v) for k,v in data.items()},
        'version_anomalies':dict(version_counts),'source_data_only_confirmation_geometry_reviewed':True,'confirmation_outcome_accesses':0}
    put(DOCS/'exp007_source_geometry.json',result)
    if version_counts:raise ValueError('VERSION_ASOF_SEMANTICS_BLOCKED; diagnostic receipt preserved')
    return result


def validation_sample():
    g=json.loads((DOCS/'exp007_source_geometry.json').read_bytes())
    data=corpus(range(int(g['development'][0][:4]),int(g['development'][1][:4])+1));trades=data['political_trades'];events=data['political_trade_events']
    versions={(e['chamber'],e['source_doc_id'],e['source_row_index']) for e in events if e['version']>1 and e['available_at'][:10]<=g['development'][1]}
    eligible=[r for r in trades if g['development'][0]<=r['available_at'][:10]<=g['development'][1]]
    strata=defaultdict(list)
    for r in eligible:strata[(r['available_at'][:4],r['chamber'])].append(r)
    selected=[];seen=set()
    def identity(r):return (r['chamber'],r['doc_id'],r['row_index'])
    for label,rows in sorted(strata.items()):
        ordered=sorted(rows,key=lambda r:digest(identity(r)))
        for predicate in (lambda r:r['action']=='purchase',lambda r:r['action']!='purchase',lambda r:identity(r) in versions,
            lambda r:r['printed_ticker'] and r['resolved_ticker'] and r['printed_ticker']!=r['resolved_ticker'],
            lambda r:not r['printed_ticker'],lambda r:r['printed_ticker'] and r['printed_ticker']==r['resolved_ticker']):
            hit=next((r for r in ordered if identity(r) not in seen and predicate(r)),None)
            if hit and len(selected)<96:selected.append(hit);seen.add(identity(hit))
    for r in sorted(eligible,key=lambda r:digest(identity(r))):
        if len(selected)==96:break
        if identity(r) not in seen:selected.append(r);seen.add(identity(r))
    records=[{'trade_key':list(identity(r)),'source_url':r['source_url'],'available_at':r['available_at'],
        'action':r['action'],'transaction_date':r['transaction_date'],'asset_description':r['asset_description'],
        'printed_ticker':r['printed_ticker'],'resolved_ticker':r['resolved_ticker'],'resolution_status':r['resolution_status'],
        'source_row_sha256':digest(r),'amended_version_source':identity(r) in versions} for r in selected]
    value={'version':'EXP007_neutral_original_validation_sample_v001','records':records,'records_sha256':digest(records),
        'source_geometry_sha256':digest(g),'maximum_observations':96,'selection':'Six neutral source strata per year/chamber, stable hash order, Development only; no amounts/performance selection',
        'purchase_classification_gate':'No unexplained purchase/nonpurchase disagreement in verified original rows; unresolved original evidence cannot certify its stratum',
        'actual_strata':{'chambers':dict(Counter(r['trade_key'][0] for r in records)),
          'years':dict(Counter(r['available_at'][:4] for r in records)),'actions':dict(Counter(r['action'] for r in records)),
          'printed_missing':sum(not r['printed_ticker'] for r in records),'printed_resolved_differ':sum(bool(r['printed_ticker'] and r['resolved_ticker'] and r['printed_ticker']!=r['resolved_ticker']) for r in records),
          'amendment_source_rows':sum(r['amended_version_source'] for r in records)},'performance_executed':False,'confirmation_accesses':0}
    put(DOCS/'exp007_original_validation_sample.json',value);print('Validation sample frozen:',len(records),'observations',value['actual_strata'])
    return value


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=('geometry','sample'));a=p.parse_args()
    print((geometry if a.command=='geometry' else validation_sample)())
