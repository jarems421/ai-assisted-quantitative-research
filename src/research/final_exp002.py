"""Reproduce the final pre-performance EXP002 evidence without remote calls."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import statistics

from src.research.extraction import decode_page, simulated_timestamp
from src.research.exp002_contracts import sec_filing_availability, execution_signal, session_key, split_safe_ratio
from src.research.pit_signals import NY, filing_state

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/EXP002/audit/raw/final_blockers_20261011'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def events(directory):
    rows=[];terminal=False
    pages=sorted(directory.glob('events_*.json'))
    for n,path in enumerate(pages,1):
        response=read(path)['response']
        text='\n'.join(c['text'] for c in response.get('content',[]) if c['type']=='text')
        if text.startswith('No events match this query in an available event store.'):
            if not rows or n!=len(pages):raise ValueError('Unproven exhaustion')
            terminal=True;continue
        page,more,total=decode_page(response,'events',n)
        rows.extend(page)
        if not more:
            if len(rows)!=total:raise ValueError('Missing events')
            terminal=True
    if not terminal:raise ValueError('Incomplete pagination')
    for row in rows:
        if simulated_timestamp(row,'events').astimezone(NY).date()>date(2020,12,31):
            raise ValueError('Post-cutoff simulated observation')
    return rows,len(pages)


def runtime_summary():
    reference=read(RAW/'decision_transport_v001/source_state_reference.json')
    summary={'performance_calculated':False,'transport':{},'deployment':{},'corporate':{}}
    for name,expected in reference.items():
        rows,pages=events(RAW/name);audits=[];fills=[]
        for row in rows:
            e=row['event'];local=simulated_timestamp(row,'events').astimezone(NY)
            if e.get('status')=='Filled':
                if (local.hour,local.minute)!=(9,30):raise ValueError('Wrong execution time')
                fills.append(local.isoformat())
            if (local.hour,local.minute)!=(9,30):continue
            for signal in e.get('signals',[]):
                results=signal.get('audit',{}).get('results',{})
                def value(key):
                    a=results.get(key,{})
                    return a.get('lhsValue') if not a.get('lhsError') else None
                used=execution_signal(local.date(),value('0.1'),value('0.0.0.1'),value('0.0.1'))
                intended=date.fromisoformat(expected['decision'][:10])+timedelta(days=1)
                target=expected['expected_value'] if local.date()==intended else None
                if used!=target or signal['isTrue']!=(target is not None):raise ValueError('Decision transport mismatch')
                audits.append({'session':local.date().isoformat(),'used':used,'expected':target,
                               'validity':value('0.0.0.1'),'freshness':value('0.0.1')})
        if len(fills)!=(1 if expected['state']=='USABLE' else 0):raise ValueError('Unexpected fills')
        if not audits:raise ValueError('Missing transport condition audits')
        summary['transport'][name]={'id':read(RAW/name/'submission.json')['id'],'events':len(rows),'pages':pages,'audits':audits,'fills':fills,'pass':True}
    for name in ('deployment_90','deployment_92_5','deployment_95'):
        rows,pages=events(RAW/name);filled=[r['event'] for r in rows if r['event'].get('status')=='Filled']
        bad=[r for r in rows if r['eventType']=='OrderRejected' or r['event'].get('status')=='Rejected']
        nominal=float(name.removeprefix('deployment_').replace('_','.'))
        notional=sum(f['quantity']*f['filledAtPrice'] for f in filled)
        summary['deployment'][name]={'id':read(RAW/name/'submission.json')['id'],'nominal_percent':nominal,'stock_notional':notional,'observed_percent':notional/25000*100,'fees':sum(f['fees'] for f in filled),'rejected_orders':len(bad),'fills':len(filled),'events':len(rows),'pages':pages,'pass':len(filled)==2 and not bad}
    rows,pages=events(RAW/'corporate_price');actions=[r['event'] for r in rows if r['eventType']=='ApplyDividend']
    filled=[r['event'] for r in rows if r['event'].get('status')=='Filled']
    source=read(RAW/'price_cases/rows.json');appl=[r for r in source if r['ticker']=='AAPL']
    by_day={r['date'][:10]:r for r in appl}
    market=[r['event'] for r in rows if r['eventType']=='Market']
    differences=[]
    for event in market:
        at=datetime.fromisoformat(event['timestamp'].replace('Z','+00:00')).astimezone(NY)
        src=by_day[at.date().isoformat()];field='openingPrice' if at.hour==9 else 'closingPrice'
        differences.append(abs(event['prices']['AAPL Stock']['price']-src[field]))
    split=dict(executionDate='2020-08-31',splitFrom=1,splitTo=4)
    before,after=by_day['2020-08-28'],by_day['2020-08-31']
    ratio=split_safe_ratio(before['unadjustedClose'],after['unadjustedClose'],date(2020,8,28),date(2020,8,31),[split])
    native_ratio=after['closingPrice']/before['closingPrice']
    summary['corporate']={'id':read(RAW/'corporate_price/submission.json')['id'],'events':len(rows),'pages':pages,'sampled_market_observations':len(market),'source_sessions':len(appl),'max_native_source_price_difference':max(differences),'buy_quantity':filled[0]['quantity'],'fill_price':filled[0]['filledAtPrice'],'native_dividend_per_adjusted_share':actions[0]['dividend']['cashAmount'],'source_dividend_per_nominal_share':.82,'dividend_share_units_match':abs(actions[0]['dividend']['cashAmount']-.82/4)<1e-7,'split_safe_ratio_matches_native':abs(ratio-native_ratio)<1e-10,'no_separate_split_quantity_adjustment':not any(r['eventType']=='ApplyStockSplit' for r in rows),'complete_market_sessions':len(market)==2*len(appl)}
    if (max(differences)>0.000008 or not summary['corporate']['dividend_share_units_match']
            or not summary['corporate']['split_safe_ratio_matches_native']
            or not summary['corporate']['complete_market_sessions']):
        raise ValueError('Corporate-action/price fixture does not reconcile')
    return summary


def source_summary():
    old=ROOT/'data/raw/EXP002/audit/raw/revision_20261011'
    filings=read(old/'cohort_filings/rows.json')
    for row in filings:sec_filing_availability(row['availableAt'],row['filingDate'])
    insider=read(RAW/'insider_versions/rows.json')
    for row in insider:sec_filing_availability(row['availableAt'],row['filingDate'])
    owner=read(ROOT/'data/raw/EXP002/audit/raw/custom_pit_20261011/owner_sample_short/rows.json')
    linked={(r['accession'],r['ownerCik']):r for r in insider}
    matches=[r for r in owner if (r['versionAccession'],r['ownerCik']) in linked]
    identity_matches=sum(str(int(r['issuerCik']))==str(int(r['cik'])) for r in insider if r['cik'])
    universe=read(RAW/'universe_identity/rows.json')
    dates=['2014-01-02','2015-01-02','2016-01-04','2017-01-03','2018-01-02','2019-01-02','2020-01-02','2020-12-31']
    sizes={d:len({r['ticker'] for r in universe if r['member_from']<=d<=r['member_to']}) for d in dates}
    quarters=defaultdict(set)
    for r in filings:
        if r['submissionType']=='13F-HR' and r['periodOfReport']<='2019-12-31':
            public=sec_filing_availability(r['availableAt'],r['filingDate']).astimezone(NY).date()
            if public<=date.fromisoformat(r['periodOfReport'])+timedelta(days=60):quarters[r['periodOfReport']].add(r['cik'])
    pair_metrics=[]
    qs=sorted(quarters)
    for p,q in zip(qs,qs[1:]):
        coverage=len(quarters[p]&quarters[q])/len(quarters[p]|quarters[q])
        pair_metrics.append({'prior':p,'current':q,'matched':len(quarters[p]&quarters[q]),'coverage':coverage})
    holdings=read(RAW/'institutional_full_filings_bounded/rows.json');groups=defaultdict(list)
    for r in holdings:groups[r['accession']].append(r)
    metadata={r['accession']:r for r in read(RAW/'selected_filings.json')}
    chains=defaultdict(list)
    for accession,positions in groups.items():
        meta=metadata[accession];r=positions[0]
        public=sec_filing_availability(r['availableAt'],r['filingDate'])
        values=defaultdict(float)
        for position in positions:
            if position['sharesType']=='SH' and not position['putCall']:
                values[position['cusip']]+=position['sharesAmount']
        chains[(r['cik'],r['periodOfReport'])].append({'accession':accession,'availableAt':public.isoformat(),
            'kind':'ORIGINAL' if r['submissionType']=='13F-HR' else r['amendmentType'],
            'amendment_sequence':int(meta['amendmentNo']) if meta['amendmentNo'] else None,
            'holdings':dict(values),'complete':True,'identity_certified':True})
    diagnostics={}
    for key,versions in chains.items():
        try:
            state=filing_state(versions,datetime(2015,3,2,tzinfo=timezone.utc))
            diagnostics['/'.join(key)]={'state':'RECONSTRUCTED_CUSIP_ONLY','positions':len(state['holdings']),
                                       'public_versions':len(state['contributors']),'listed_identity_certified':False}
        except ValueError as error:
            diagnostics['/'.join(key)]={'state':'UNAVAILABLE','reason':str(error)}
    rename=read(RAW/'rename_identity/rows.json')
    return {'timezone':{'institutional_matches':len(filings),'insider_matches':len(insider),'naive_representation':'UTC','semantic':'SEC filing-date end-of-day America/New_York; conservative availability, not exact acceptance time'},'insider':{'events':len(owner),'linked_events':len(matches),'filing_issuer_security_cik_matches':identity_matches,'filing_rows':len(insider),'scope':'bounded AAPL/MSFT sample only; no production alpha dataset'},'universe':{'joined_rows':len(universe),'membership_sizes':sizes,'missing_security_ids':sum(r['security_id'] is None for r in universe),'types':dict(Counter(r['asset_type'] for r in universe)),'ended_membership_rows':sum(r['member_to']<'2020-12-31' for r in universe),'rename_NU_ES':rename,'critical':'Underfilled historical membership and anachronistic/reused symbols; absent members cannot be explained as contemporaneous exclusions'},'institutional':{'full_source_rows':len(holdings),'filings':{a:{'rows':len(rs),'unresolved_ticker_rows':sum(r['resolvedTicker'] is None for r in rs),'type':rs[0]['submissionType'],'amendment':rs[0]['amendmentType']} for a,rs in groups.items()},'cusip_only_chain_diagnostics':diagnostics,'adjacent_global_cohort_metrics':pair_metrics,'min_global_matched_coverage':min(r['coverage'] for r in pair_metrics),'median_global_matched_coverage':statistics.median(r['coverage'] for r in pair_metrics),'quarters_pass_95':sum(r['coverage']>=.95 for r in pair_metrics),'quality_policy':'20 matched managers, 95% public-known matched coverage, max 180-day current-quarter/publication age; fixed before returns','critical':'Complete-filing omission cannot yet certify zero for eligible securities when security/CUSIP reconciliation is unresolved'}}


if __name__=='__main__':
    target=ROOT/'experiments/EXP002/research'
    for name,value in [('final_runtime_summary.json',runtime_summary()),('final_source_summary.json',source_summary())]:
        (target/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Final bounded evidence reproduced locally; no Nexus calls or performance')
