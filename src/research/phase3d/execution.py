"""Small Decimal long-only ledger. Synthetic input only; no data or network access."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
from typing import Protocol
import hashlib
from pathlib import Path

from src.research.spec import digest
from src.research.capabilities import require_population
from src.research.sec_pilot.provenance import instant


def number(value, *, positive=False):
    if isinstance(value, (float, bool)): raise ValueError('Use exact decimal strings or integers')
    try: n = Decimal(value)
    except (InvalidOperation, TypeError): raise ValueError('Invalid decimal') from None
    if not n.is_finite() or n < 0 or (positive and n <= 0): raise ValueError('Nonfinite or invalid amount')
    return n


class ExecutionAdapter(Protocol):
    def execute(self, inputs: dict) -> dict: ...


class NexusAdapter:
    def execute(self, inputs):
        raise ValueError('NEXUS_EXECUTION_BLOCKED: no transport implemented')


class LocalReferenceAdapter:
    def execute(self, inputs):
        with localcontext() as context:
            context.prec = 34
            return _execute(deepcopy(inputs))


def _execute(data):
    if data.get('experiment_id') != 'EXP999' or data.get('mode') != 'SYNTHETIC_INFRASTRUCTURE':
        raise ValueError('Real strategy execution is outside Phase 3D scope')
    if data.get('contract_version') != 'execution_v001': raise ValueError('Unknown execution contract')
    sessions = data['sessions']; ids = [r['session'] for r in sessions]
    if not sessions or ids != sorted(set(ids)): raise ValueError('Duplicate or unordered sessions')
    for prev, curr in zip(sessions, sessions[1:]):
        if instant(prev['close_at']) >= instant(curr['open_at']): raise ValueError('Session overlap')
    if any(instant(s['open_at']) >= instant(s['close_at']) for s in sessions): raise ValueError('Invalid session clock')
    initial = number(data['starting_cash'], positive=True); fee = number(data['fee_bps']) / 10000
    if fee >= 1: raise ValueError('Invalid fee')
    positions = {}; cash = initial; receivables = []
    output = {k:[] for k in ('orders','fills','positions','cash_ledger','action_ledger','nav','populations','observations')}
    output['cash_ledger'].append({'session': ids[0], 'kind': 'FUNDING', 'amount': str(initial), 'cash': str(cash)})
    bindings = data['bindings']
    if not bindings: raise ValueError('Identity bindings required')
    for b in bindings:
        if not all(b.get(k) for k in ('security_id','issuer_cik','class','ticker','exchange','effective_from','effective_to','source_sha256')):
            raise ValueError('Incomplete identity interval')
        if instant(b['effective_from']) >= instant(b['effective_to']): raise ValueError('Reversed identity interval')
    def active(at):
        rows = [b for b in bindings if instant(b['effective_from']) <= at < instant(b['effective_to'])]
        pairs = [{'security_id':b['security_id'],'ticker':b['ticker']} for b in rows]
        require_population(pairs, pairs, complete=True, binding_verified=True)
        return {b['security_id']:b for b in rows}
    events = data.get('events', [])
    keys = [r['event_id'] for r in events]
    if len(keys) != len(set(keys)) or any(r['session'] not in ids for r in events): raise ValueError('Duplicate/out-of-calendar event')
    schedules = data.get('rebalances', [])
    if len(schedules) != len({r['session'] for r in schedules}) or any(r['session'] not in ids for r in schedules):
        raise ValueError('Duplicate/out-of-calendar rebalance')
    previous_active = None
    for session in sessions:
        day = session['session']; opened = instant(session['open_at']); live = active(opened)
        prices = session['prices']
        if set(prices) != set(live): raise ValueError('Prices change the certified population')
        for p in prices.values(): number(p['open'], positive=True); number(p['close'], positive=True)
        output['populations'].append({'session':day, 'identities':sorted((k,b['ticker']) for k,b in live.items())})
        today = sorted([r for r in events if r['session']==day], key=lambda r:(r['sequence'],r['event_id']))
        if len(today) != len({r['sequence'] for r in today}): raise ValueError('Ambiguous action order')
        terminal = set()
        for e in today:
            sid = e['security_id']; kind = e['kind']; qty = positions.get(sid, Decimal(0))
            if (not e.get('source_sha256') or e.get('status') != 'CERTIFIED_SYNTHETIC_FIXTURE'
                    or instant(e['available_at']) > opened): raise ValueError('Unknown or future lifecycle evidence')
            if previous_active is None or sid not in previous_active: raise ValueError('Action lacks prior identity/position basis')
            before = qty
            amount = Decimal(0)
            if kind == 'split':
                if sid not in live: raise ValueError('Split identity disappeared')
                positions[sid] = qty * number(e['ratio'], positive=True)
            elif kind == 'dividend':
                if e.get('currency') != 'USD' or e.get('share_basis') != 'CURRENT_AFTER_PRIOR_SEQUENCED_ACTIONS':
                    raise ValueError('Unsupported dividend convention')
                pay = e['pay_session']
                if pay not in ids or pay < day: raise ValueError('Unresolved payment calendar')
                amount = qty * number(e['cash_per_share'])
                receivables.append({'security_id':sid,'event_id':e['event_id'],'pay_session':pay,'amount':amount})
            elif kind in ('cash_merger','cancellation','stock_merger'):
                if sid in live or sid in terminal: raise ValueError('Terminal identity remains active or repeats')
                terminal.add(sid)
                if kind == 'cash_merger':
                    if e.get('currency') != 'USD' or e.get('pay_session') != day: raise ValueError('Deferred/unresolved merger cash unsupported')
                    amount = qty * number(e['cash_per_share'], positive=True); cash += amount
                    output['cash_ledger'].append({'session':day,'kind':kind,'event_id':e['event_id'],'amount':str(amount),'cash':str(cash)})
                elif kind == 'stock_merger':
                    successor=e['successor_security_id']
                    if successor not in live: raise ValueError('Successor identity unresolved')
                    positions[successor] = positions.get(successor,Decimal(0)) + qty * number(e['ratio'],positive=True)
                elif not e.get('explicit_zero_recovery_evidence'): raise ValueError('Zero recovery cannot be assumed')
                positions[sid]=Decimal(0)
            else: raise ValueError('Unresolved or unsupported lifecycle event')
            output['action_ledger'].append({'session':day,'event_id':e['event_id'],'security_id':sid,'kind':kind,
                'quantity_before':str(before),'quantity_after':str(positions.get(sid,qty)), 'entitlement_or_cash':str(amount),'source_sha256':e['source_sha256']})
        if previous_active is not None and set(previous_active)-set(live) != terminal:
            raise ValueError('Disappearing security lacks exact terminal instruction')
        for payable in receivables:
            if payable['pay_session']==day:
                cash += payable['amount']
                output['cash_ledger'].append({'session':day,'kind':'DIVIDEND_PAYMENT','event_id':payable['event_id'],
                                             'amount':str(payable['amount']),'cash':str(cash)})
        receivables = [r for r in receivables if r['pay_session']>day]
        if any(q and sid not in live for sid,q in positions.items()): raise ValueError('Unresolved held security')
        schedule = next((r for r in schedules if r['session']==day),None)
        if schedule:
            decision = instant(schedule['decision_at'])
            if decision >= opened: raise ValueError('Decision must precede execution')
            decision_live = active(decision)
            obs = schedule['observations']; observed=[{'security_id':r['security_id'],'ticker':r['ticker']} for r in obs]
            require_population([{'security_id':k,'ticker':b['ticker']} for k,b in decision_live.items()], observed, complete=True,binding_verified=True)
            for r in obs:
                if instant(r['available_at']) > decision or not r.get('source_sha256'): raise ValueError('Future/missing observation evidence')
                # Signal may be negative; exact, finite numeric rank only.
                v=Decimal(r['value'])
                if not v.is_finite(): raise ValueError('Invalid rank value')
            k=schedule['top_k']; exposure=number(schedule['exposure'])
            if type(k) is not int or not 0 <= k <= len(obs) or exposure>1 or (k==0 and exposure!=0): raise ValueError('Invalid sizing')
            chosen=sorted(obs,key=lambda r:(-Decimal(r['value']),r['security_id']))[:k]
            if any(r['security_id'] not in live for r in chosen): raise ValueError('Selected identity ended before execution')
            output['observations'].append(deepcopy(schedule))
            equity = cash + sum(q*number(prices[sid]['open'],positive=True) for sid,q in positions.items() if q) + sum(r['amount'] for r in receivables)
            targets={r['security_id']:equity*exposure/k/number(prices[r['security_id']]['open'],positive=True) for r in chosen}
            deltas={sid:targets.get(sid,Decimal(0))-positions.get(sid,Decimal(0)) for sid in set(targets)|{sid for sid,q in positions.items() if q}}
            for sid, delta in sorted(deltas.items(),key=lambda x:(x[1]>0,x[0])):
                if delta==0: continue
                price=number(prices[sid]['open'],positive=True); notional=abs(delta)*price; cost=notional*fee
                after=cash-delta*price-cost
                if after < 0: raise ValueError('Insufficient cash; no hidden sizing adjustment')
                cash=after; positions[sid]=positions.get(sid,Decimal(0))+delta
                order={'session':day,'security_id':sid,'ticker':live[sid]['ticker'],'quantity':str(delta),'price':str(price),'fee':str(cost)}
                output['orders'].append(dict(order)); output['fills'].append(dict(order))
                output['cash_ledger'].append({'session':day,'kind':'FILL','security_id':sid,'amount':str(-delta*price-cost),'cash':str(cash)})
        nav=cash+sum(q*number(prices[sid]['close'],positive=True) for sid,q in positions.items() if q)+sum(r['amount'] for r in receivables)
        output['positions'].append({'session':day,'holdings':{sid:str(q) for sid,q in sorted(positions.items()) if q}})
        output['nav'].append({'session':day,'cash':str(cash),'receivables':str(sum(r['amount'] for r in receivables)), 'nav':str(nav)})
        previous_active=live
    if receivables: raise ValueError('Unpaid terminal receivable requires separately supported valuation')
    output.update(input_sha256=digest(data),engine={'name':'local_reference_v001','arithmetic':'Decimal34',
                  'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'scope':'SYNTHETIC_ONLY','settlement':'immediate fixtures','fractional_shares':True},warnings=[],errors=[])
    output['receipt_sha256']=digest(output)
    return output


def reconcile_outputs(expected, observed):
    """Exact semantic ledger check; engine metadata may differ, events may not."""
    for row in (expected, observed):
        if digest({k:v for k,v in row.items() if k!='receipt_sha256'}) != row.get('receipt_sha256'):
            raise ValueError('Corrupt execution receipt')
    a={k:v for k,v in expected.items() if k not in ('engine','receipt_sha256')}
    b={k:v for k,v in observed.items() if k not in ('engine','receipt_sha256')}
    if a != b: raise ValueError('Semantic execution mismatch: no tolerance or dropped fields')
    return {'status':'PASS_EXACT_SEMANTIC_LEDGER','output_sha256':digest(a)}
