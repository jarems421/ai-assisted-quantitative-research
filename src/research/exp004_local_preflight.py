"""Offline EXP004 source conformance audit; never evaluates real portfolio NAV."""
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.prepare_exp004 import verify_freeze
from src.research.exp004_local_execution import ENGINE,schema_gate,exact_population,bounded

DOCS=ROOT/'docs/acceleration'
RAW=ROOT/'data/raw/EXP004/production_inputs_v001'
OUT=ROOT/'data/raw/EXP004/local_execution_v001'
CERT=DOCS/'exp004_local_execution_certificate_v002.json'


def hashed(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def build():
    import pyarrow.parquet as pq
    from src.research.design_exp003 import eligible_identity
    from src.research.exp004_compile import calendar
    f=verify_freeze();qa_path=ROOT/'experiments/EXP004/research/amended_input_qa.json';qa=json.loads(qa_path.read_bytes())
    parts=qa['source_parts'];inventory=[];missing_by_date=[];schemas=Counter()
    for ref in parts:
        path=ROOT/ref['path']
        if not path.resolve().is_relative_to(RAW.resolve()):raise ValueError('Source escapes frozen EXP004 inputs')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('Frozen source part changed')
        pf=pq.ParquetFile(path);columns=pf.schema_arrow.names;schema=tuple(columns);schemas[schema]+=1
        rows=pf.metadata.num_rows;is_price='unadjustedClose' in columns
        # Only dates are decoded. No price values or returns are inspected.
        dates=pq.read_table(path,columns=['day' if is_price else 'executionDate']).column(0).to_pylist()
        day_strings=[v.isoformat()[:10] for v in dates]
        if any(not '2013-12-31'<=d<='2020-12-31' for d in day_strings):raise ValueError('Out-of-scope observation')
        inventory.append(dict(ref,rows=rows,columns=columns,minimum_date=min(day_strings),maximum_date=max(day_strings),
            schema_gate=schema_gate(columns) if is_price else 'SPLIT_SOURCE_ONLY'))
    span_ref=next(r for r in json.loads((ROOT/'experiments/EXP003/provenance.json').read_bytes())['source_artifacts'] if 'historical_security_spans/rows.json' in r['path'])
    span_path=ROOT/span_ref['path']
    if hashlib.sha256(span_path.read_bytes()).hexdigest()!=span_ref['sha256']:raise ValueError('Historical identity source changed')
    spans=defaultdict(list)
    for r in json.loads(span_path.read_bytes()):spans[r['ticker']].append(r)
    inputs=[];monthly=[];planned=[];total=0;first_examples=[]
    for year in range(2015,2021):
        qp=RAW/f'compiled_{year}_v002/qa_summary.json';ip=qp.parent/'decision_inputs.json';q=json.loads(qp.read_bytes())
        if hashed(qp)['sha256']!=qa['yearly_qa_hashes'][str(year)] or hashed(ip)['sha256']!=q['private_input_sha256']:raise ValueError('Frozen panel changed')
        if q['source_parts']!=parts or q['status']!='PASS_LOCAL_NUMERIC':raise ValueError('Source lineage/QA mismatch')
        inputs.extend((hashed(qp),hashed(ip)))
        panels=json.loads(ip.read_bytes())
        for p in panels:
            day=p['decision']['session'];bounded(day);ids=list(p['ticker_byid']);total+=len(ids)
            exact_population(ids,list(p['momentum']['180']));exact_population(ids,list(p['momentum']['365']))
            for h in ('180','365'):
                exact_population(ids,p['ranking'][h])
                if p['ranking'][h]!=sorted(ids,key=lambda sid:(-p['momentum'][h][sid],sid)):raise ValueError('Frozen deterministic ranking changed')
                for k in (20,40):
                    name=f'M{h}_K{k}'
                    if list(p['targets'][name])!=p['ranking'][h][:k]:raise ValueError('Frozen target identity mismatch')
            for sid,ticker in p['ticker_byid'].items():
                for d in (day,p['decision']['prior_session']):
                    if eligible_identity(spans[ticker],ticker,d)!=sid:raise ValueError('Historical decision/execution identity mismatch')
            monthly.append({'day':day,'eligible':len(ids),'eligible_ids_sha256':digest(sorted(ids)),
                'source_identity_bindings':'PASS_EXACT_FROZEN_BINDING','executable_population':'NOT_CERTIFIED_NO_OPEN_INPUT',
                'missing_open_security_decisions':len(ids)})
            planned.append({'day':day,'population':p['ticker_byid'],'momentum_targets':{n:list(t) for n,t in p['targets'].items()},
                'EW_intended_ids':sorted(ids),'actual_holdings':None,'reason':'No execution OPENs; targets are prior frozen input QA, not fills'})
            if day=='2015-01-02':
                first_examples=[{'cell':n,'first_intended_target_ticker':p['ticker_byid'][next(iter(t))],
                                'stable_security_id':next(iter(t)),'session':day,'status':'NOT_EXECUTED_MISSING_OPEN'} for n,t in p['targets'].items()]
    if len(monthly)!=72 or total!=273115:raise ValueError('Complete frozen panel denominator mismatch')
    sources=[r for r in inventory if 'unadjustedClose' in r['columns']]
    if len(sources)!=28 or sum(r['rows'] for r in sources)!=7871192:raise ValueError('Price job/row denominator changed')
    if any(r['schema_gate']['status']!='LOCAL_EXECUTION_OPEN_PRICES_BLOCKED' for r in sources):raise ValueError('This stop receipt cannot substitute for complete execution certification')
    target_value={'planned_decisions':planned,'actual_holdings':'NONE_EXECUTION_NOT_STARTED','performance_executed':False}
    put(OUT/'blocked_target_inventory.json',target_value)
    prior=json.loads((ROOT/'experiments/EXP004/research/publication_runtime_audit.json').read_bytes())
    from src.research.exp004_inputs import bar_request
    value={'version':2,'engine':ENGINE,'engine_sha256':hashed(ROOT/'src/research/exp004_local_execution.py')['sha256'],
        'status':'LOCAL_EXECUTION_BLOCKED','specific_blocker':'LOCAL_EXECUTION_OPEN_PRICES_BLOCKED',
        'specification_sha256':f['frozen_specification_sha256'],'methodology_sha256':f['frozen_methodology_sha256'],
        'frozen_receipt':hashed(ROOT/'experiments/EXP004/freeze_versions/v002/receipt.json'),
        'source_inventory':inventory,'compiled_inputs':inputs,'historical_identity_source':span_ref,
        'calendar_sha256':digest([d.isoformat() for d in calendar()]),'calendar_status':'INHERITED_SIGNAL_CALENDAR; REAL_CLOSE_EXECUTION_NOT_CERTIFIED',
        'price_projection':bar_request('2015-01-01','2015-03-31')['query'],'price_jobs':28,'price_rows':7871192,
        'split_rows':sum(r['rows'] for r in inventory if 'executionDate' in r['columns']),
        'monthly':monthly,'security_decisions':total,'source_identity_and_ranking_reconciliation':'PASS72_DECISIONS',
        'local_executable_population_reconciliation':'BLOCKED; NO_COMPLETE_EXECUTION_INPUT',
        'missing_open_security_decisions':total,'first_intended_target_examples':first_examples,
        'blocked_target_inventory_sha256':digest(target_value),'actual_holdings':0,'real_fills':0,
        'action_coverage':{'split':'8149_SOURCE_ROWS; SIGNAL_QA_PRESERVED; HELD_EXECUTION_NOT_CERTIFIED',
            'cash_dividend':'NO_CASH_ENTITLEMENT_PAYMENT_SOURCE_IN_AUTHORIZED_EXTRACT',
            'terminal':'NO_TERMINAL_CONSIDERATION_PAYMENT_SOURCE_IN_AUTHORIZED_EXTRACT',
            'actually_held_action_events':'NOT_MEASURED_NO_POSITIONS','unresolved_action_count':None,
            'reason':'Close-only bars plus split factors cannot certify cash dividends or complete terminal economics; no missing event is asserted absent'},
        'SPY_local_execution_readiness':'BLOCKED_NO_CERTIFIED_OPEN_CASH_DIVIDEND_EXECUTION_INPUT',
        'funding':'25000USD','fee_percent':'0.10','nominal_deployment_percent':'95','fractional':True,'dividend_policy':'cash',
        'synthetic_reference':hashed(ROOT/'src/research/phase3d/execution.py'),
        'nexus_runtime_failure_preserved':hashed(ROOT/'experiments/EXP004/research/publication_runtime_audit.json'),
        'prior_reserve_accounting':prior['reserve_accounting'],'new_evaluations':0,'trial_ledger_mutations':0,
        'fold_evaluations_completed':0,'full_replays_completed':0,'performance_executed':False,
        'validation_accesses':0,'test_accesses':0,'new_source_requests':0,'Nexus_calls':0,'Aurora_calls':0,
        'owner_authority':hashed(DOCS/'owner_exp004_local_execution_2026-10-14.md'),
        'initial_preflight_receipt':hashed(DOCS/'exp004_local_execution_certificate_v001.json'),
        'version_reason':'Add an explicit core-ledger certified-entry guard; initial failed input receipt and prototype retained, no data or economic change'}
    put(CERT,value);return value


def report(check=False):
    c=json.loads(CERT.read_bytes());vpath=DOCS/'exp004_local_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    examples='\n'.join(f"| {r['cell']} | {r['first_intended_target_ticker']} | `{r['stable_security_id']}` | {r['session']} |" for r in c['first_intended_target_examples'])
    text=f'''# EXP004 local execution: frozen input boundary stop

**LOCAL_EXECUTION_BLOCKED — LOCAL_EXECUTION_OPEN_PRICES_BLOCKED. Hypothesis untested.** Starting HEAD `34c5b7595ddd30bc67627c4d61638a91a62e4efd`, as of 2026-10-14. [Owner instruction](owner_exp004_local_execution_2026-10-14.md) authorizes local-only Development after a passing, pushed pre-performance certificate. [This certificate](exp004_local_execution_certificate_v002.json) records a failed input gate, not permission to calculate performance. The initial failed preflight receipt and engine prototype are retained separately; version 2 adds an explicit core-ledger entry guard without changing inputs or economics.

## Concrete blocker

All **28 frozen price extracts / 7,871,192 rows** contain exactly `ticker`, `day`, `security_id`, `unadjustedClose`. **None contains execution OPEN prices.** Their original SQL explicitly projected completed closes; the source table's OHLC name is not evidence that omitted columns were downloaded. The split extract contains 8,149 rows with ticker, effective date and split operands only.

The local route cannot execute the frozen first-session 09:30 OPEN orders using these bytes. A prior close, same-day close, guessed OPEN or another vendor would change the execution contract. No such substitution occurred. The failure already applies at 2015-01-02 inception, before any actual position, dividend entitlement or terminal event exists.

All **72 monthly panels / 273,115 eligible security-decisions** were hash-verified. Exact stable IDs, both horizons, rankings and frozen Top-K targets reconcile, including historical prior/execution ticker bindings. This is source-input reconciliation. Locally executable population equality remains BLOCKED because every eligible execution OPEN is unavailable; it is not a passing runtime certificate. Every intended EW identity is retained, not pruned. The exact full target/identity inventory remains private and hash-pinned.

Examples from the already-frozen first-decision targets (not fills or performance):

| Cell | First intended target ticker | Stable ID | Intended session |
| --- | --- | --- | --- |
{examples}

SPY also lacks a certified local OPEN/cash-dividend execution input. Source cash-dividend entitlement/payment and terminal cash/stock/recovery instructions are not supplied by these price/split extracts. Declaration/catalog files are not event economics. Their completeness is unresolved, not a zero-event assumption. **Actually held securities/events: none**, because execution never began; affected held-action counts are NOT_MEASURED. The earliest established stop is missing OPEN inputs, rather than a claim of a particular missing held dividend or merger. No new data campaign or source lookup followed.

## Separate implementation and synthetic certification

`{c['engine']}` is a separately versioned Decimal34 ledger prototype in [exp004_local_execution.py](../../src/research/exp004_local_execution.py), hash `{c['engine_sha256']}`. It preserves the original EXP999 reference and its guards byte-for-byte. The new real entry point requires a passing certificate, matching engine/economic/input hashes and a pushed checkpoint; the blocked certificate rejects execution before reading portfolio inputs. There is no metric loader, network client or Store mutation in the engine.

Focused synthetic fixtures cover Top20/Top40 stable-ID ties, shortfall, EW, SPY inception-only buy, 95% nominal deployment, fractional sizing, 0.10% per-fill fees, monthly decisions, sales before buys, splits, dividend entitlement/payment, stable-ID rename, cash/stock mergers, evidenced cancellation, ended holdings, empty-universe liquidation, insufficient cash, duplicate/ambiguous/substituted IDs, missing prices, sealed dates and receipt replay. Independent hand calculations use USD25,000: 95% initial notional is USD23,750; fees USD23.75; flat-price initial NAV USD24,976.25. These are fake EXP999 accounting fixtures, never EXP004 performance. Synthetic correctness does not certify real source or lifecycle coverage.

## Preserved design, trial budget and stop

Economic specification `{c['specification_sha256']}` and methodology `{c['methodology_sha256']}` remain unchanged. Original freeze v001, amendment v002, numeric QA, [Nexus failure](../../experiments/EXP004/research/publication_runtime_audit.json) and [historical Development report](../../reports/EXP004_development_report.md) retain their bytes. No execution freeze version or PASS certificate was issued. No global pause guard was removed; Nexus remains disabled. The owner authorized this local attempt, but its scientific certification did not pass.

All **24 scored-fold evaluations and six full-Development replays are NOT_RUN**. Four-cell metrics, EW/SPY returns, paired effects, selection, turnover, participation, cost/delay robustness and regime results are unavailable. No economic failure/no-advance verdict can be inferred. The original 59-evaluation ceiling and prior one diagnostic/19 remaining failure reserves are preserved; this source preflight and synthetic fixtures create no completed economic evaluation or new trial. No real-run crash occurred.

**Validation accesses 0; Test accesses 0; new scientific source requests 0; Nexus/Aurora 0.** Only frozen Development/warmup dates were decoded; real price values were not analyzed. EXP005/EXP006/EXP007 remain closed and absent where previously absent; no EXP008, source discovery, Phase 4B, optimizer or paper/live operation occurred. Dependency pins and unrelated user files are preserved.

Validation: **{v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped**. [Validation receipt](exp004_local_validation.json). Public report checks need tracked receipts only; private source audit needs the unchanged EXP004 parts/panels and inherited identity snapshot.

```sh
python -m src.research.exp004_local_preflight --check
python -m src.research.exp004_local_preflight --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

**Stopped at the exact input blocker.** The owner's conditional instruction authorizes Development if certification passes; it cannot manufacture omitted execution/action evidence. No source acquisition is run or automatically proposed. The frozen economic question remains intact and untested. Delivery records final commits/push and hosted CI separately.
'''
    path=DOCS/'exp004_local_execution_report.md'
    if check:
        if path.read_bytes()!=text.encode():raise ValueError('Local execution report differs')
    else:path.write_bytes(text.encode())
    return c['status']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.build or a.audit:
        value=build();print(value['status'],value['specific_blocker'],value['security_decisions'])
    print(report(a.check))
