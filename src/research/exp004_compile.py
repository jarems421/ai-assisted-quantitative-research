"""Numeric Development-only EXP004 QA using immutable Lake receipts."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from functools import lru_cache
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import duckdb
import pyarrow.parquet as pq

from src.nexus.process_exp001 import session_dates, observed, nth_weekday, easter
from src.research.design_exp003 import eligible_identity
from src.research.exp004_inputs import ROOT, RAW, save
from src.research.exp004_policy import momentum, ranked_targets
from src.research.prepare_exp004 import verify_freeze
from src.research.readiness_exp003 import decisions
from src.research.exp004_actions import classify_groups, crossing

NY=ZoneInfo('America/New_York')


def calendar():
    holidays=set()
    for y in (2013,2014):
        holidays.update({observed(date(y,1,1)),nth_weekday(y,1,0,3),nth_weekday(y,2,0,3),
                         easter(y)-timedelta(days=2),
                         date(y,6,1)-timedelta(days=(date(y,6,1).weekday()-0)%7 or 7),
                         observed(date(y,7,4)),nth_weekday(y,9,0,1),nth_weekday(y,11,3,4),observed(date(y,12,25))})
    warmup={date(2013,12,31)+timedelta(days=i) for i in range(366)
            if (date(2013,12,31)+timedelta(days=i)).weekday()<5
            and date(2013,12,31)+timedelta(days=i) not in holidays}
    return sorted(warmup|session_dates(date(2015,1,1),date(2020,12,31)))


@lru_cache(maxsize=None)
def eod(day):
    return datetime.combine(day,time(21),NY).astimezone(timezone.utc).isoformat()


def assert_split_lineage(ticker,effective,legs):
    factors={float(r['splitTo'])/float(r['splitFrom']) for r in legs}
    if len(factors)>1:
        raise ValueError('Input QA failed: ambiguous same-date split legs for '+ticker+
                         ' at '+effective.isoformat()+'; no authoritative event/version lineage')


def compile_year(year):
    freeze=verify_freeze()
    if year not in range(2015,2021):raise ValueError('Development only')
    spans=defaultdict(list)
    spanpath=ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json'
    for s in json.loads(spanpath.read_bytes()):spans[s['ticker']].append(s)
    @lru_cache(maxsize=None)
    def identity(ticker,day):
        return eligible_identity(spans[ticker],ticker,day)
    parts=sorted(RAW.glob('bars_*/parts/**/part-*.parquet'))
    if not parts:raise ValueError('Numeric bars absent')
    db=duckdb.connect()
    db.from_parquet(list(map(str,parts))).create_view('bars')
    split_parts=sorted((RAW/'splits/parts').rglob('part-*.parquet'))
    if not split_parts:raise ValueError('Effective split input absent')
    splits=defaultdict(list)
    raw_splits=[]
    for part in split_parts:
        raw_splits.extend(pq.read_table(part).to_pylist())
    groups=classify_groups(raw_splits,identity)
    by_action_id=defaultdict(list)
    for g in groups:
        sid=g['security_id']
        if sid:
            by_action_id[sid].append(g)
            if not g['ambiguity_reason']:
                splits[sid].append({'executionDate':g['effective_date'],'splitFrom':1,
                                    'splitTo':g['factor'],'availableAt':eod(date.fromisoformat(g['effective_date']))})
    sources=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in parts+split_parts]
    cal=calendar();monthly=[];private=[]
    source_hash=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    for d in decisions(year):
        prior=date.fromisoformat(d['prior_session']);boundary=prior-timedelta(days=365)
        expected={v.isoformat() for v in cal if boundary<=v<=prior}
        at=datetime.fromisoformat(d['decision_utc']).replace(tzinfo=timezone.utc)
        byid=defaultdict(list)
        for ticker,day,sid,price in db.execute('SELECT ticker,day,security_id,unadjustedClose FROM bars WHERE day BETWEEN ? AND ? ORDER BY security_id,day',[boundary,prior]).fetchall():
            byid[sid].append((ticker,day,price))
        values={180:{},365:{}};ticker_byid={};excluded=defaultdict(int);action_exclusions=[]
        source_universe=0
        for sid,records in byid.items():
            end=[r for r in records if r[1]==prior]
            if len(end)!=1:excluded['missing_or_duplicate_endpoint']+=1;continue
            ticker=end[0][0]
            if (identity(ticker,d['prior_session'])!=sid
                    or identity(ticker,d['session'])!=sid):
                excluded['ambiguous_or_inactive_identity']+=1;continue
            source_universe+=1
            days=[r[1].isoformat() for r in records]
            if len(set(days))!=len(days) or set(days)!=expected:
                excluded['missing_duplicate_or_noncalendar_sessions']+=1;continue
            if any(identity(t,day.isoformat())!=sid for t,day,p in records):
                excluded['lookback_identity_ambiguity']+=1;continue
            if any(p is None or not math.isfinite(p) or p<=0 for t,day,p in records):
                excluded['invalid_price']+=1;continue
            affected=crossing(by_action_id[sid],prior)
            if affected:
                excluded['corporate_action_ambiguity']+=1
                action_exclusions.append({'security_id':sid,'events':[g['effective_date'] for g in affected]})
                for g in affected:
                    if g['first_affected_decision'] is None:g['first_affected_decision']=d['session']
                    g['last_affected_decision']=d['session'];g['excluded_security_decisions']+=1
                continue
            bars=[{'date':day.isoformat(),'availableAt':eod(day),'unadjustedClose':p} for t,day,p in records]
            for h in values:values[h][sid]=momentum(bars,splits[sid],prior,at,h)
            ticker_byid[sid]=ticker
        if len(set(ticker_byid.values()))!=len(ticker_byid):raise ValueError('Duplicate execution ticker identities')
        ranking={h:sorted(v,key=lambda sid:(-v[sid],sid)) for h,v in values.items()}
        targets={f'M{h}_K{k}':ranked_targets(v,k) for h,v in values.items() for k in (20,40)}
        valid=bool(values[180]) and set(values[180])==set(values[365])
        monthly.append(dict(d,source_universe=source_universe,eligible_count=len(ticker_byid),excluded=dict(excluded),
                            action_exclusions=action_exclusions,K20_available=len(ticker_byid)>=20,K40_available=len(ticker_byid)>=40,
                            shared_population_sha256=hashlib.sha256(json.dumps(sorted(ticker_byid)).encode()).hexdigest(),
                            qa_status='PASS_LOCAL_NUMERIC' if valid else 'FAIL_EMPTY_UNIVERSE',
                            rankings_sha256=hashlib.sha256(json.dumps(ranking,sort_keys=True).encode()).hexdigest(),
                            selected_top_K={name:list(t) for name,t in targets.items()}))
        private.append({'decision':d,'ticker_byid':ticker_byid,'momentum':values,'ranking':ranking,'targets':targets})
        print(d['session'],'eligible',len(ticker_byid),'exclusions',dict(excluded),flush=True)
    db.close()
    output=RAW/f'compiled_{year}_v002'
    save(output/'decision_inputs.json',private)
    summary={'year':year,'status':'PASS_LOCAL_NUMERIC' if all(m['qa_status']=='PASS_LOCAL_NUMERIC' for m in monthly) else 'FAIL',
             'frozen_specification_sha256':freeze.get('old_specification_sha256',freeze['frozen_specification_sha256']),'source_sha256':source_hash,
             'source_parts':sources,'monthly':monthly,
             'ambiguity_ledger':[g for g in groups if g['ambiguity_reason']],
             'amendment_rule':'Inclusive prior-session-minus365-calendar-days through prior session; ambiguity excludes the common four-cell/EW population until it ages out. Ordinary unique factors remain applicable. Same-factor duplicates normalize once; raw rows remain immutable.',
             'normalization':'Price availability uses inherited finalized21:00NY EOD convention, not a vendor availability column. Effective splits use the same completed-day normalization solely under the inherited scoped split contract, never future factors; precise announcement/vintage immutability is not claimed.',
             'private_input_sha256':hashlib.sha256((output/'decision_inputs.json').read_bytes()).hexdigest(),
             'nexus_strategy_jobs':0}
    save(output/'qa_summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('year',type=int)
    compile_year(parser.parse_args().year)
