"""Bounded EXP003 source-coverage receipts, never candidate performance.

Remote submission is explicit (--execute); source queries are year-bounded and
immutable/idempotent. A completed query does not certify absent insider data.
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import argparse
import hashlib
import json

from src.nexus.process_exp001 import session_dates, observed, nth_weekday, easter
from src.research.pit_signals import decision_for_session

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/EXP003/final_readiness_20261011'


def save(path, value):
    data = (json.dumps(value, indent=2, default=str, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Immutable receipt differs')
    else:
        with path.open('xb') as handle:
            handle.write(data)


def decisions(year):
    # Extend only the source warmup calendar; leave EXP001's calendar untouched.
    holidays=set()
    for y in (2013,2014):
        holidays.update({observed(date(y,1,1)),nth_weekday(y,1,0,3),nth_weekday(y,2,0,3),
                         easter(y)-timedelta(days=2),
                         date(y,6,1)-timedelta(days=(date(y,6,1).weekday()-0)%7 or 7),
                         observed(date(y,7,4)),nth_weekday(y,9,0,1),
                         nth_weekday(y,11,3,4),observed(date(y,12,25))})
    warmup={date(2013,12,31)+timedelta(days=i) for i in range(366)
            if (date(2013,12,31)+timedelta(days=i)).weekday()<5
            and date(2013,12,31)+timedelta(days=i) not in holidays}
    sessions=sorted(warmup | session_dates(date(2015,1,1),date(2020,12,31)))
    found = set()
    result = []
    for i, day in enumerate(sessions):
        if day.year != year or day.month in found:
            continue
        found.add(day.month)
        before = sessions[i-1]
        boundary = before - timedelta(days=365)
        expected = sum(boundary <= d <= before for d in sessions)
        result.append({'session': day.isoformat(), 'prior_session': before.isoformat(),
                       'decision_utc': decision_for_session(day).astimezone(timezone.utc).replace(tzinfo=None).isoformat(),
                       'expected_365_sessions': expected})
    return result


def request(year):
    if year not in range(2015, 2021):
        raise ValueError('Outside Development coverage audit')
    ds = decisions(year)
    values = ','.join("(DATE '%s', DATE '%s', TIMESTAMP '%s', %d)" %
                      (d['session'], d['prior_session'], d['decision_utc'], d['expected_365_sessions']) for d in ds)
    # No current symbols, cap, volume, exchange, corpus or return fields.
    sql = """WITH bounds AS (SELECT CAST(? AS DATE) lo, CAST(? AS DATE) hi),
    decisions(session, prior_session, decision_utc, expected_sessions) AS (VALUES %s),
    mapped AS (
      SELECT o.ticker, CAST(o.date AS DATE) AS day, s.security_id, s.cik,
        COUNT(*) OVER(PARTITION BY o.ticker, CAST(o.date AS DATE)) mappings,
        s.asset_type, o.unadjustedClose
      FROM lake.sec_daily_ohlc o JOIN lake.security_segments s
        ON o.ticker=s.ticker AND CAST(o.date AS DATE) BETWEEN s.from_date AND COALESCE(s.to_date,DATE '2020-12-31'), bounds
      WHERE CAST(o.date AS DATE) BETWEEN lo AND hi AND s.from_date<=hi),
    valid AS (SELECT * FROM mapped WHERE mappings=1 AND asset_type='CS' AND security_id IS NOT NULL
      AND unadjustedClose>0 AND isfinite(unadjustedClose)),
    endpoints AS (
      SELECT d.*, p.security_id,p.ticker,p.cik,
        COUNT(*) OVER(PARTITION BY d.session,p.security_id) aliases
      FROM decisions d JOIN valid p ON p.day=d.prior_session
      JOIN lake.security_segments s ON s.ticker=p.ticker AND s.security_id=p.security_id
       AND d.session BETWEEN s.from_date AND COALESCE(s.to_date,DATE '2020-12-31')
       AND s.asset_type='CS'),
    pricecoverage AS (
      SELECT e.session,e.prior_session,e.decision_utc,e.expected_sessions,e.security_id,e.ticker,e.cik,e.aliases,
        COUNT(DISTINCT p.day) days_365, COUNT(p.day) rows_365,
        MIN(p.day) first_bar,MAX(p.day) last_bar
      FROM endpoints e LEFT JOIN valid p ON p.security_id=e.security_id
       AND p.day BETWEEN e.prior_session-INTERVAL 365 DAY AND e.prior_session
      GROUP BY ALL),
    ownerstate AS (
      SELECT d.session,v.issuerCik,
       COUNT(*) owner_version_rows,
       COUNT(DISTINCT CASE WHEN v.transactionCode='P' AND v.acquiredDisposed='A'
         AND v.rowKind='nonderiv' AND v.shares>0 AND isfinite(v.shares)
         AND (v.supersededAt IS NULL OR d.decision_utc<v.supersededAt)
         AND (v.coverageUnverifiedAt IS NULL OR d.decision_utc<v.coverageUnverifiedAt)
         AND v.ownerCik IS NOT NULL THEN v.ownerCik END) observed_buyers_90,
       SUM(CASE WHEN v.coverageUnverifiedAt<=d.decision_utc OR v.ownerCik IS NULL
         OR v.eventId IS NULL OR v.versionAccession IS NULL THEN 1 ELSE 0 END) unverified_versions
      FROM decisions d JOIN lake.insider_owner_events v ON v.availableAt<=d.decision_utc
        AND v.firstAvailableAt>d.decision_utc-INTERVAL 90 DAY AND v.firstAvailableAt<=d.decision_utc, bounds
      WHERE CAST(v.availableAt AS DATE) BETWEEN lo AND hi
      GROUP BY d.session,v.issuerCik),
    ambiguous AS (SELECT d.session,COUNT(DISTINCT p.ticker) ambiguous_identity_tickers
      FROM decisions d JOIN mapped p ON p.day=d.prior_session
      WHERE p.mappings<>1 OR p.security_id IS NULL GROUP BY d.session)
    SELECT p.*, COALESCE(o.owner_version_rows,0) observed_owner_version_rows,
      COALESCE(o.observed_buyers_90,0) observed_buyers_90,
      COALESCE(o.unverified_versions,0) unverified_versions,
      COALESCE(a.ambiguous_identity_tickers,0) ambiguous_identity_tickers
    FROM pricecoverage p LEFT JOIN ownerstate o ON ltrim(CAST(p.cik AS VARCHAR),'0')=ltrim(o.issuerCik,'0') AND p.session=o.session
    LEFT JOIN ambiguous a ON a.session=p.session ORDER BY p.session,p.security_id""" % values
    # Anchor to the actual prior session, including New Year weekend gaps.
    lower=min(date.fromisoformat(d['prior_session']) for d in ds)-timedelta(days=365)
    return {'query': sql, 'params': [lower.isoformat(), date(year,12,31).isoformat()]}


def run(year, execute=False):
    import pyarrow.parquet as pq
    from nexustrade import NexusTradeClient
    from nexustrade.lake import get, LakeQueryResult
    if not execute:
        return {'request': request(year), 'execute': False}
    config = {}
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1)
            config[key.strip()]=value.strip().strip('"').strip("'")
    client=NexusTradeClient(api_key=config['NEXUSTRADE_API_KEY'],base_url=config['NEXUSTRADE_API_BASE_URL'])
    version='v003' if year in (2017,2018) else 'v002'
    directory=RAW/(str(year)+'_'+version); directory.mkdir(parents=True,exist_ok=True)
    req=request(year); save(directory/'request.json',req)
    original=client._transport.request
    sequence=len(list(directory.glob('wire_request_*.json')))
    def capture(method,path,**kw):
        nonlocal sequence
        sequence+=1
        save(directory/f'wire_request_{sequence:04d}.json',{'method':method,'path':path,'body':kw.get('body'),'idempotency_key':kw.get('idempotency_key')})
        try: result=original(method,path,**kw)
        except Exception as error:
            save(directory/f'wire_error_{sequence:04d}.json',{'type':type(error).__name__,'message':str(error)})
            raise
        if not isinstance(result,bytes):save(directory/f'wire_response_{sequence:04d}.json',result)
        return result
    client._transport.request=capture
    if not (directory/'submission.json').exists():
        key='exp003-readiness-'+hashlib.sha256(json.dumps(req,sort_keys=True).encode()).hexdigest()
        intent=directory/'intent.json'
        if intent.exists():raise ValueError('Uncertain submission: reconcile intent before retry')
        save(intent,{'idempotency_key':key,'request':req,'purpose':'coverage counts, never strategy performance'})
        save(directory/'submission.json',client.create_lake_query(req,idempotency_key=key))
    op=json.loads((directory/'submission.json').read_text())
    print(year,op['id'],flush=True)
    if (directory/'rows.json').exists():return
    handle=get(op['id'],client=client)
    if not isinstance(handle,LakeQueryResult):handle=handle.wait(timeout_seconds=40)
    save(directory/'result_receipt.json',{'id':handle.id,'row_count':handle.row_count,'result':handle.result})
    parts=handle.download(directory/'parts')
    rows=[]
    for part in sorted(parts.glob('part-*.parquet')):rows.extend(pq.read_table(part).to_pylist())
    if len(rows)!=handle.row_count:raise ValueError('Incomplete query download')
    save(directory/'rows.json',rows)
    print('Downloaded coverage rows',len(rows),flush=True)


def summarize_saved():
    """Certifiable source rule and conservative zero gate, never a return test."""
    from collections import defaultdict
    import statistics
    from src.research.design_exp003 import eligible_identity
    spans=json.loads((ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json').read_text(encoding='utf-8'))
    span_index=defaultdict(list)
    for span in spans:span_index[span['ticker']].append(span)
    grouped=defaultdict(list)
    sources=[]
    for year in range(2015,2021):
        version='v003' if year in (2017,2018) else 'v002'
        path=RAW/(str(year)+'_'+version)/'rows.json'
        if not path.exists():raise ValueError('All six source receipts required')
        payload=path.read_bytes()
        sources.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),
                        'sha256':hashlib.sha256(payload).hexdigest()})
        for row in json.loads(payload):
            if row['session']>'2020-12-31' or row['last_bar']>row['prior_session']:
                raise ValueError('Coverage observation exceeds cutoff/decision')
            grouped[row['session']].append(row)
    monthly=[]
    annual=[]
    for day,rows in sorted(grouped.items()):
        ids=[r['security_id'] for r in rows]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate production decision identity')
        universe=[r for r in rows if r['aliases']==1
                  and eligible_identity(span_index[r['ticker']],r['ticker'],r['prior_session'])==r['security_id']
                  and eligible_identity(span_index[r['ticker']],r['ticker'],r['session'])==r['security_id']]
        momentum=[r for r in universe if r['days_365']==r['expected_sessions']
                  and r['rows_365']==r['days_365'] and r['last_bar']==r['prior_session']]
        # No window-completeness certificate exists in the observed surface.
        # Source-presence counts stay diagnostics, never valid scalar signals.
        monthly.append({'session':day,'decision_utc':rows[0]['decision_utc'],
                        'universe_count':len(universe),'valid_momentum_history_count':len(momentum),
                        'valid_insider_state_count':0,'both_count':0,'certified_insider_zero_count':0,
                        'unavailable_insider_count':len(universe),'joint_coverage_percent':0.0,
                        'ambiguous_identity_ticker_count':max(r['ambiguous_identity_tickers'] for r in rows),
                        'execution_identity_or_alias_exclusion_rows':len(rows)-len(universe),
                        'observed_positive_issuer_purchase_presence_count':sum(r['observed_buyers_90']>0 for r in universe),
                        'observed_issuer_event_presence_count':sum(r['observed_owner_version_rows']>0 for r in universe),
                        'observed_unverified_owner_version_security_count':sum(r['unverified_versions']>0 for r in universe),
                        'shortfall_K20':True,'shortfall_K40':True})
    if len(monthly)!=72:raise ValueError('Expected all 72 monthly decisions')
    for year in range(2015,2021):
        ms=[m for m in monthly if m['session'].startswith(str(year))]
        annual.append({'year':year,'monthly_decisions':len(ms),
                       'universe_min':min(m['universe_count'] for m in ms),
                       'universe_mean':statistics.fmean(m['universe_count'] for m in ms),
                       'universe_max':max(m['universe_count'] for m in ms),
                       'momentum_min':min(m['valid_momentum_history_count'] for m in ms),
                       'momentum_mean':statistics.fmean(m['valid_momentum_history_count'] for m in ms),
                       'momentum_max':max(m['valid_momentum_history_count'] for m in ms),
                       'universe_security_decisions':sum(m['universe_count'] for m in ms),
                       'valid_momentum_security_decisions':sum(m['valid_momentum_history_count'] for m in ms),
                       'both_security_decisions':0,'certified_zero_security_decisions':0,
                       'unavailable_insider_security_decisions':sum(m['universe_count'] for m in ms),
                       'joint_coverage_percent':0.0})
    return {'universe_gate':'PASS_SCOPED_SOURCE_RULE','production_joint_coverage_gate':'FAIL_NO_COVERAGE_CERTIFICATE',
            'monthly':monthly,'annual':annual,'source_artifacts':sources,
            'development_inception':None,'price_only_first_monthly_session':monthly[0]['session'],
            'scheduled_shortfalls':{'K20':72,'K40':72},
            'certified_zero_semantics':'Zero only from an audited complete security/window event-version and identity contract; absence, null correction flags and successful SQL alone do not certify it.',
            'limits':'Momentum counts certify positive unique completed-price history prerequisites, not a generated numeric split-adjusted rank stream. Insider source-presence counts use issuer CIK, not certified class-specific event identity. Production counts are zero because no certified states can be emitted; this does not establish economic absence or unusable vendor coverage.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('year',type=int);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();result=run(args.year,args.execute)
    if result is not None:print(json.dumps(result,indent=2))
