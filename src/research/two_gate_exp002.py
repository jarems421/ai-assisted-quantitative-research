"""Reproduce two-gate source diagnostics locally; never evaluate performance."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from math import isfinite
import json
from src.research.extraction import decode_page, simulated_timestamp
from src.research.pit_signals import NY, instant

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dated_identity(holding, mappings):
    """Validate supplied resolver evidence, not invent a replacement crosswalk.

    Listing spans alone do not certify a CUSIP-to-share-class mapping. Foreign
    suffixes and ticker case are retained. Conflicting candidates fail closed.
    """
    for key in ('cusip','accession','manager_cik','reporting_quarter','availableAt'):
        if not holding.get(key):return None
    public=instant(holding['availableAt']);day=public.astimezone(NY).date()
    matches=[]
    for mapping in mappings:
        if mapping.get('cusip')!=holding['cusip']:continue
        required=('ticker','security_id','source','valid_from','valid_to','status','date_basis')
        if any(not mapping.get(k) for k in required):continue
        if mapping['status']!='CERTIFIED_UNIQUE' or mapping['date_basis']!='America/New_York':continue
        if date.fromisoformat(mapping['valid_from'])<=day<=date.fromisoformat(mapping['valid_to']):
            matches.append(mapping)
    # Do not emulate the published resolver's first-covering-span fallback.
    return matches[0] if len(matches)==1 else None


def omission_state(identity, state, decision):
    """An unresolved unrelated bond need not invalidate certified stock absence.

    Require the candidate's unique dated CUSIP and the complete raw filing
    state; never infer absence from a ticker-only filtered extraction.
    """
    if identity is None:return 'UNAVAILABLE'
    if not all(identity.get(k) for k in ('cusip','ticker','security_id','source','valid_from','valid_to')):
        return 'UNAVAILABLE'
    if identity.get('status')!='CERTIFIED_UNIQUE' or identity.get('date_basis')!='America/New_York':
        return 'UNAVAILABLE'
    day=instant(decision).astimezone(NY).date()
    if not date.fromisoformat(identity['valid_from'])<=day<=date.fromisoformat(identity['valid_to']):
        return 'UNAVAILABLE'
    flags=('complete_eligible_filing','all_raw_rows_available','asof_reconstructed','amendments_reconciled')
    if not all(state.get(k) is True for k in flags):return 'UNAVAILABLE'
    if not all(state.get(k) for k in ('accession','manager_cik','reporting_quarter')):
        return 'UNAVAILABLE'
    if 'raw_cusip_holdings' not in state or not state.get('availableAt'):return 'UNAVAILABLE'
    if instant(state['availableAt'])>instant(decision):return 'UNAVAILABLE'
    quantity=state['raw_cusip_holdings'].get(identity['cusip'],0)
    if not isinstance(quantity,(int,float)) or not isfinite(quantity) or quantity<0:
        return 'UNAVAILABLE'
    return 'HELD' if quantity>0 else 'NOT_HELD'


def page(path):
    rows,more,total=decode_page(load(path)['response'],'events',1)
    if more or len(rows)!=total:raise ValueError('Incomplete audit page')
    for row in rows:
        if simulated_timestamp(row,'events').astimezone(NY).date()>date(2020,12,31):
            raise ValueError('Post-cutoff observation')
    return rows


def summarize():
    spans=load(RAW/'historical_security_spans/rows.json')
    by_ticker=defaultdict(list)
    for s in spans:by_ticker[s['ticker']].append(s)
    lake=load(RAW/'memberships/rows.json');monthly=[];prior={};native_sets=[]
    for path in sorted((RAW/'monthly_population').glob('month_*.json')):
        day=path.stem.removeprefix('month_');rows=page(path)
        opened=[r for r in rows if simulated_timestamp(r,'events').astimezone(NY).hour==9]
        if len(opened)!=1:raise ValueError('Missing/duplicate native open')
        audit=opened[0]['event']['signals'][0]['actionMetadata']['rebalance']['dynamicAudit']
        symbols=[a[0] for a in audit['allocations']];native_sets.append(set(symbols))
        ids={};unresolved=0
        for symbol in symbols:
            valid={s['security_id'] for s in by_ticker[symbol] if s['from_date']<=day<=s['to_date'] and s['security_id']}
            if len(valid)==1:ids[symbol]=valid.pop()
            else:unresolved+=1
        lake_symbols={r['componentCode'] for r in lake if r['startDate'][:10]<=day<=r['endDate'][:10]}
        prior_ids={v:k for k,v in prior.items()}
        renamed=sum(v in prior_ids and prior_ids[v]!=k for k,v in ids.items())
        monthly.append({'session_date':day,'decision_timestamp':(datetime.fromisoformat(day).replace(tzinfo=NY)-timedelta(days=1)).replace(hour=21).isoformat(),
                        'native_candidate_pool':audit['universeSize'],'native_members':len(symbols),
                        'unique_stable_ids':len(set(ids.values())),'unresolved_identities':unresolved,
                        'ticker_changes_from_prior_month':renamed,'lake_members':len(lake_symbols),
                        'native_only_count':len(set(symbols)-lake_symbols),'lake_only_count':len(lake_symbols-set(symbols)),
                        'native_only_examples':sorted(set(symbols)-lake_symbols)[:10],'lake_only_examples':sorted(lake_symbols-set(symbols))[:10]})
        prior=ids
    for record,symbols in zip(monthly,native_sets):
        record['later_removed_by_last_sample']=len(symbols-native_sets[-1])
    transitions=[];event_rows=144;order_count=0
    for name in ('tesla_transition','rename_transition','acquisition_removal','addition_transition'):
        rows=page(RAW/name/'events_0001.json');event_rows+=len(rows)
        order_count+=sum(r['eventType'] in ('Order','OrderRejected') for r in rows)
        for r in rows:
            local=simulated_timestamp(r,'events').astimezone(NY)
            if local.hour!=9:continue
            for signal in r['event'].get('signals',[]):
                if not signal['conditionName'].startswith('Is '):continue
                result=signal['audit']['results']['0']
                transitions.append({'case':name,'session_date':local.date().isoformat(),'declaration':signal['conditionName'],
                                    'native_value':result.get('lhsValue'),'native_error':result.get('lhsError')})
    cohorts=[]
    for year in (2015,2017,2020):
        rows=load(RAW/f'cohort_{year}/rows.json');sets=defaultdict(set)
        for r in rows:
            q=date.fromisoformat(r['periodOfReport'])
            public=datetime.fromisoformat(r['availableAt']).replace(tzinfo=instant('2015-01-01T00:00:00Z').tzinfo).astimezone(NY).date()
            if r['submissionType']=='13F-HR' and public<=q+timedelta(days=60):sets[r['periodOfReport']].add(r['cik'])
        p,q=sorted(sets);a,b=sets[p],sets[q]
        cohorts.append({'year':year,'filing_snapshots':len(rows),'source_rows':sum(r['rows'] for r in rows),
                        'resolved_ticker_percent':100*sum(r['resolved_rows'] for r in rows)/sum(r['rows'] for r in rows),
                        'unresolved_cusips_summed_per_filing':sum(r['unresolved_cusips'] for r in rows),
                        'unique_grain_snapshots':sum(r['rows']==r['unique_rows'] for r in rows),
                        'public_original_managers_prior':len(a),'public_original_managers_current':len(b),
                        'matched_public_managers':len(a&b),'known_union_coverage':len(a&b)/len(a|b),
                        'certified_complete_identity_filings':0,'certifiable_omission_securities':0,
                        'usable_production_cohort':False})
    anchors=('AAPL','MSFT','IBM','XOM','JNJ','JPM','GE','F','WMT','KO','AAL','TSLA')
    for cohort in cohorts:
        year=cohort['year']
        cohort['dated_security_sample']={}
        for month in ('09','12'):
            i=next(i for i,r in enumerate(monthly) if r['session_date'].startswith(f'{year}-{month}'))
            cohort['dated_security_sample'][monthly[i]['session_date']]=sorted(set(anchors)&native_sets[i])
    identity_rows=load(RAW/'sample_identities/rows.json')
    identity_counts=Counter(r['resolvedTicker'] for r in identity_rows)
    return {'gate_a':'FAIL','gate_b':'FAIL','outcome':'ABANDON EXP002','monthly':monthly,'transitions':transitions,
            'native_min_members':min(r['native_members'] for r in monthly),'native_max_members':max(r['native_members'] for r in monthly),
            'cohorts':cohorts,'identity_sample':{'cusip_listing_combinations':len(identity_rows),'combinations_per_ticker':dict(identity_counts),
                                               'certified_mapping_provenance_rows':0,'raw_receipts_private':True},
            'diagnostic_backtests':5,'lake_jobs':7,'lake_completed':6,'lake_failed':1,
            'retrieved_event_rows':event_rows,'retrieved_event_pages':76,'observed_orders_in_transition_pages':order_count,
            'membership_audit_scope':'72 execution opens and closes; membership counts before nominal-price/signal filters; not a certified preceding-21:00 universe',
            'cohort_scope':'Source presence/grain and public-manager coverage, not SEC-completeness or a production signal',
            'performance_evaluated':False,'held_out_access':False,'hypothesis_frozen':False}


if __name__=='__main__':
    (ROOT/'experiments/EXP002/research/two_gate_summary.json').write_text(json.dumps(summarize(),indent=2)+'\n',encoding='utf-8')
    print('Two-gate evidence reproduced locally; no Nexus calls or performance')
