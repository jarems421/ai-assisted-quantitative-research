"""EXP004 local ledger v001; production requires a pushed, passing certificate.

No source client, return metric, Store mutation or remote execution exists here.
The historical EXP999 reference implementation remains unchanged.
"""
from copy import deepcopy
from decimal import Decimal,localcontext
import hashlib
from pathlib import Path
from src.research.spec import digest
from src.research.phase3d.execution import number
from src.research.sec_pilot.provenance import instant

ENGINE='EXP004_LOCAL_REFERENCE_V001'
CELLS=('M180_K20','M180_K40','M365_K20','M365_K40','EW','SPY')
_CERTIFIED_ENTRY=object()


def bounded(day):
    from datetime import date
    date.fromisoformat(day)
    if not '2015-01-02'<=day<='2020-12-31':raise ValueError('Validation/Test/later or outside Development')


def exact_population(expected,observed):
    for values in (expected,observed):
        if len(values)!=len(set(values)) or any(not x for x in values):raise ValueError('Duplicate/ambiguous identity')
    if set(expected)!=set(observed):raise ValueError('Exact stable-ID population mismatch; no pruning/substitution')


def targets(cell,values):
    if cell not in CELLS:raise ValueError('Outside frozen cells')
    if any(not Decimal(str(v)).is_finite() for v in values.values()):raise ValueError('Invalid signal')
    if cell=='SPY':
        if len(values)!=1:raise ValueError('Exactly one certified SPY identity required')
        return {next(iter(values)):Decimal('.95')}
    k=len(values) if cell=='EW' else int(cell.rsplit('K',1)[1])
    if not k:return {}
    ids=sorted(values,key=lambda sid:(-Decimal(str(values[sid])),sid))[:k]
    return {sid:Decimal('.95')/k for sid in ids}


def schema_gate(columns):
    required={'ticker','day','security_id','unadjustedOpen','unadjustedClose'}
    return {'status':'PASS_SCHEMA_ONLY' if required<=set(columns) else 'LOCAL_EXECUTION_OPEN_PRICES_BLOCKED',
            'missing_fields':sorted(required-set(columns)), 'close_as_open_permitted':False}


class LocalEXP004Adapter:
    def execute(self,data,certificate_path):
        import json
        cert=json.loads(Path(certificate_path).read_bytes())
        if cert.get('status')!='PASS_PRE_PERFORMANCE_LOCAL_EXECUTION' or cert.get('engine')!=ENGINE:
            raise ValueError('Pre-performance local certificate has not passed')
        if cert.get('engine_sha256')!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise ValueError('Engine certificate changed')
        from src.research.prepare_exp004 import verify_freeze
        f=verify_freeze()
        if cert.get('specification_sha256')!=f['frozen_specification_sha256'] or cert.get('methodology_sha256')!=f['frozen_methodology_sha256']:raise ValueError('Frozen economic contract mismatch')
        from src.research.item202_identity import require_published
        require_published(Path(certificate_path))
        if digest(data) not in cert.get('certified_execution_input_hashes',[]):raise ValueError('Uncertified input')
        if data.get('experiment_id')!='EXP004':raise ValueError('EXP004 only')
        return ledger(data,_authorization=_CERTIFIED_ENTRY)

    def execute_fixture(self,data):
        if data.get('experiment_id')!='EXP999' or data.get('mode')!='SYNTHETIC_INFRASTRUCTURE':raise ValueError('Fake fixtures only')
        return ledger(data)


def ledger(inputs,*,_authorization=None):
    if inputs.get('experiment_id')=='EXP004':
        if _authorization is not _CERTIFIED_ENTRY:raise ValueError('Real ledger requires verified pushed certificate entry')
    elif inputs.get('experiment_id')!='EXP999' or inputs.get('mode')!='SYNTHETIC_INFRASTRUCTURE':
        raise ValueError('Synthetic fixture or certified EXP004 input required')
    with localcontext() as ctx:
        ctx.prec=34
        data=deepcopy(inputs);sessions=data['sessions'];days=[s['day'] for s in sessions]
        if not days or days!=sorted(set(days)):raise ValueError('Session calendar incomplete/duplicate/unordered')
        for day in days:bounded(day)
        cell=data['cell'];cash=Decimal(25000);fee=Decimal('.001');positions={};receivables=[];prior_bindings={}
        rebalances=data['rebalances'];events=data.get('actions',[])
        if len(rebalances)!=len({r['day'] for r in rebalances}) or any(r['day'] not in days for r in rebalances):raise ValueError('Invalid rebalance schedule')
        if len(rebalances)!=len({r['day'][:7] for r in rebalances}):raise ValueError('More than one monthly decision')
        if cell=='SPY' and (len(rebalances)!=1 or rebalances[0]['day']!=days[0]):raise ValueError('SPY buys once at inception')
        keys=[a['event_id'] for a in events]
        if len(keys)!=len(set(keys)) or any(a['day'] not in days for a in events):raise ValueError('Invalid action identity/calendar')
        result={'fills':[],'actions':[],'cash':[],'nav':[],'populations':[],'rebalances':[]}
        last_close=None
        for s in sessions:
            day=s['day'];op=instant(s['open_at']);cl=instant(s['close_at'])
            from zoneinfo import ZoneInfo
            from datetime import time
            if op.astimezone(ZoneInfo('America/New_York')).time()!=time(9,30):raise ValueError('Execution must use09:30NewYork OPEN')
            if op>=cl or last_close is not None and last_close>=op:raise ValueError('Invalid session clocks')
            if op.date().isoformat()!=day or cl.date().isoformat()!=day:raise ValueError('Mismatched clock/session')
            last_close=cl;bindings=s['bindings'];ids=[b['security_id'] for b in bindings]
            exact_population(ids,ids);live={b['security_id']:b for b in bindings}
            tickers=[b['ticker'] for b in bindings]
            if len(tickers)!=len(set(tickers)):raise ValueError('Ambiguous ticker binding')
            for b in bindings:
                allowed_type=(b.get('asset_type')=='CS' if cell!='SPY' else b.get('asset_type')=='ETF' and b.get('ticker')=='SPY')
                if not allowed_type or not b.get('source_sha256') or not b.get('ticker'):raise ValueError('Uncertified historical CS or explicit SPY ETF binding')
            prices=s['prices']
            for sid,p in prices.items():
                if sid not in live:raise ValueError('Price lacks stable identity')
                number(p['open'],positive=True);number(p['close'],positive=True)
            today=sorted([a for a in events if a['day']==day],key=lambda a:(a['sequence'],a['event_id']))
            if len(today)!=len({a['sequence'] for a in today}):raise ValueError('Ambiguous action order')
            terminal=set()
            for a in today:
                if not a.get('certified') or not a.get('source_sha256') or instant(a['available_at'])>op:raise ValueError('Unresolved/future action')
                sid=a['security_id'];q=positions.get(sid,Decimal(0));kind=a['kind']
                if sid not in prior_bindings:raise ValueError('Action lacks prior dated identity')
                if kind=='split':
                    if sid not in live:raise ValueError('Split loses identity')
                    positions[sid]=q*number(a['ratio'],positive=True)
                elif kind=='dividend':
                    if a.get('currency')!='USD' or a.get('share_basis')!='CURRENT_AFTER_PRIOR_SEQUENCED_ACTIONS':raise ValueError('Unknown dividend economics')
                    if a['pay_day'] not in days or a['pay_day']<day:raise ValueError('Unknown dividend payment')
                    receivables.append({'pay_day':a['pay_day'],'amount':q*number(a['cash_per_share'])})
                elif kind in ('cash_merger','stock_merger','cancellation'):
                    if sid in live or sid in terminal:raise ValueError('Ambiguous terminal identity')
                    terminal.add(sid)
                    if kind=='stock_merger':
                        successor=a['successor_security_id']
                        if successor not in live:raise ValueError('Unknown successor class')
                        positions[successor]=positions.get(successor,Decimal(0))+q*number(a['ratio'],positive=True)
                    else:
                        if a.get('currency')!='USD' or a.get('pay_day')!=day:raise ValueError('Unknown terminal payment')
                        if kind=='cancellation' and not a.get('recovery_evidence'):raise ValueError('Cancellation recovery cannot be assumed')
                        cash+=q*number(a['cash_per_share'],positive=kind=='cash_merger')
                    positions[sid]=Decimal(0)
                else:raise ValueError('Unsupported action')
                result['actions'].append(dict(a,quantity_before=str(q),quantity_after=str(positions.get(sid,q))))
            for sid,q in positions.items():
                if q and sid not in live:raise ValueError('Held security disappears without terminal instruction')
            for r in receivables:
                if r['pay_day']==day:cash+=r['amount']
            receivables=[r for r in receivables if r['pay_day']>day]
            rb=next((r for r in rebalances if r['day']==day),None)
            if rb:
                if instant(rb['decision_at'])>=op:raise ValueError('Decision does not precede execution')
                expected=rb['eligible_ids'];observed=rb['executable_ids']
                exact_population(expected,observed);exact_population(expected,list(rb['values']))
                if any(sid not in live or sid not in prices for sid in observed):raise ValueError('Missing eligible execution binding/price')
                if any(sid not in prices for sid,q in positions.items() if q):raise ValueError('Missing held execution price')
                weights=targets(cell,rb['values'])
                equity=cash+sum(q*number(prices[sid]['open'],positive=True) for sid,q in positions.items() if q)+sum(r['amount'] for r in receivables)
                qty={sid:equity*w/number(prices[sid]['open'],positive=True) for sid,w in weights.items()}
                deltas={sid:qty.get(sid,Decimal(0))-positions.get(sid,Decimal(0)) for sid in set(qty)|{k for k,v in positions.items() if v}}
                for sid,delta in sorted(deltas.items(),key=lambda item:(item[1]>0,item[0])):
                    if not delta:continue
                    price=number(prices[sid]['open'],positive=True);notional=abs(delta)*price;cost=notional*fee
                    after=cash-delta*price-cost
                    if after<0:raise ValueError('Insufficient cash; no rescale/leverage')
                    cash=after;positions[sid]=positions.get(sid,Decimal(0))+delta
                    result['fills'].append({'day':day,'security_id':sid,'ticker':live[sid]['ticker'],'quantity':str(delta),'price':str(price),'fee':str(cost)})
                result['populations'].append({'day':day,'stable_ids':sorted(observed)})
                result['rebalances'].append({'day':day,'weights':{k:str(v) for k,v in weights.items()}})
            if any(sid not in prices for sid,q in positions.items() if q):raise ValueError('Missing held close; no forward fill')
            nav=cash+sum(q*number(prices[sid]['close'],positive=True) for sid,q in positions.items() if q)+sum(r['amount'] for r in receivables)
            result['cash'].append(str(cash));result['nav'].append(str(nav));prior_bindings=live
        if receivables:raise ValueError('Unpaid receivable needs certified terminal valuation')
        result.update(engine=ENGINE,input_sha256=digest(inputs),arithmetic='Decimal34')
        result['receipt_sha256']=digest(result)
        return result
