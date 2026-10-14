"""Tracked summary of the supplemental source-key stop; no execution metrics."""
import argparse,hashlib,json
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.exp004_supplement import OUT,PLAN,DOCS
from src.research.exp004_supplement_qa import quarter,verify_refs,opens

SUMMARY=DOCS/'exp004_supplement_source_review.json'
REPORT=DOCS/'exp004_supplement_execution_report.md'


def build():
    import duckdb,pyarrow.parquet as pq
    from src.research.prepare_exp004 import verify_freeze
    f=verify_freeze();plan=json.loads(PLAN.read_bytes());first=plan['requests'][0];name=first['name'];qa=quarter(name)
    if qa['status']!='SOURCE_RECONCILIATION_BLOCKED':raise ValueError('This source-stop report requires the established failing key gate')
    db=duckdb.connect();db.from_parquet(verify_refs(qa['old_parts'])).create_view('old');db.from_parquet(verify_refs(qa['new_parts'])).create_view('new')
    missing=db.execute('SELECT security_id,ticker,day FROM old EXCEPT ALL SELECT security_id,ticker,day FROM new ORDER BY ticker,day,security_id').fetchall()
    extra=db.execute('SELECT security_id,ticker,day FROM new EXCEPT ALL SELECT security_id,ticker,day FROM old ORDER BY ticker,day,security_id').fetchall()
    pairs=db.execute('SELECT o.security_id old_id,n.security_id new_id,o.ticker,o.day FROM old o JOIN new n USING(ticker,day) WHERE o.security_id<>n.security_id ORDER BY o.day').fetchall()
    def records(rows,names):return [{k:v.isoformat() if hasattr(v,'isoformat') else v for k,v in zip(names,row)} for row in rows]
    differences={'missing':records(missing,['security_id','ticker','day']),'extra':records(extra,['security_id','ticker','day']),
        'same_ticker_day_changed_ids':records(pairs,['old_id','new_id','ticker','day'])}
    put(OUT/'source_key_differences.json',differences)
    opening_stats=opens(pq.read_table(verify_refs(qa['new_parts']),columns=['openingPrice']).column(0).to_pylist());db.close()
    schema_path=OUT/'schema_sec_daily_ohlc/schema.json';schema=json.loads(schema_path.read_bytes())
    wire=[]
    for path in sorted(OUT.glob('*/wire_request_*.json')):
        data=json.loads(path.read_bytes());wire.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'method':data['method'],'endpoint':data['path']})
    completed=[r['name'] for r in plan['requests'] if (OUT/r['name']/'part_hashes.json').exists()]
    if completed!=[name]:raise ValueError('Acquisition continued beyond source stop')
    value={'status':'LOCAL_EXECUTION_INPUTS_BLOCKED','specific_blocker':'SOURCE_RECONCILIATION_BLOCKED','starting_head':plan['starting_head'],
        'specification_sha256':f['frozen_specification_sha256'],'methodology_sha256':f['frozen_methodology_sha256'],
        'engine_sha256':hashlib.sha256((ROOT/'src/research/exp004_local_execution.py').read_bytes()).hexdigest(),
        'schema_sha256':hashlib.sha256(schema_path.read_bytes()).hexdigest(),'source_table':'lake.sec_daily_ohlc','source_columns':[c['name'] for c in schema['columns']],
        'acquisition_plan_sha256':digest(plan),'completed_quarters':completed,'unvisited_quarters':[r['name'] for r in plan['requests'] if r['name']!=name],
        'operation_id':json.loads((OUT/name/'submission.json').read_bytes())['id'],'reconciliation':qa,
        'differences_sha256':digest(differences),'changed_id_rows':len(pairs),'affected_tickers':sorted({r[2] for r in pairs}),
        'changed_identity_examples':differences['same_ticker_day_changed_ids'][:3],
        'first_discrepancy_date':min(r[3].isoformat() for r in pairs),'last_discrepancy_date':max(r[3].isoformat() for r in pairs),
        'matched_CLOSE_mismatches':qa['close_row_mismatches'],'warmup_OPEN_field_checks':opening_stats,
        'required_Development_OPEN_coverage':{'same_common_population_decisions':273115,'valid_observed':0,'missing_observed':0,'invalid_observed':0,
            'not_acquired_upstream_stop':273115,'basis':'Frozen monthly panels; no Development price quarter acquired; not observed missing prices'},
        'SPY':'NOT_ACQUIRED_UPSTREAM_KEY_STOP','dividend_events_acquired':None,'dividend_queries':0,'dividend_semantics':'NOT_CERTIFIED_UPSTREAM_STOP',
        'actual_held_terminal_cases':'NOT_MEASURED_UPSTREAM_STOP','resolved_terminal_cases':None,'unresolved_terminal_cases':None,
        'v004':'BLOCKED_NOT_ISSUED','price_queries':1,'schema_queries':1,'SDK_source_calls':len(wire),'wire_receipts':wire,
        'automatic_retries':0,'performance_evaluations':0,'fold_evaluations':0,'full_replays':0,'Validation_accesses':0,'Test_accesses':0,
        'backtests':0,'publication':0,'Aurora':0,'credit_purchases':0,'actual_account_debit':None,
        'first_reconciliation_diagnostic_sha256':hashlib.sha256((OUT/name/'reconciliation.json').read_bytes()).hexdigest(),
        'diagnostic_correction':'Original projection-multiset mismatch combined missing keys with close differences; v002 separates them:62missing/62extra keys,0matched CLOSE mismatches. Source stop unchanged.',
        'prior_reserve_accounting':json.loads((ROOT/'experiments/EXP004/research/publication_runtime_audit.json').read_bytes())['reserve_accounting']}
    put(SUMMARY,value);return value


def report(check=False):
    c=json.loads(SUMMARY.read_bytes());q=c['reconciliation'];vpath=DOCS/'exp004_supplement_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    examples='\n'.join(f"| {r['ticker']} | {r['day']} | `{r['old_id']}` | `{r['new_id']}` |" for r in c['changed_identity_examples'])
    text=f'''# EXP004 supplemental execution acquisition: source-key stop

**LOCAL_EXECUTION_INPUTS_BLOCKED — SOURCE_RECONCILIATION_BLOCKED. Hypothesis untested.** Starting HEAD `{c['starting_head']}`, as of 2026-10-14. [Owner instruction](owner_exp004_supplement_2026-10-14.md) authorized same-source omitted execution-field acquisition and automatic local Development only after certification. The collector stopped at the mandatory exact-key gate; no performance or v004 PASS certificate exists.

## OPEN field acquired; exact source identity failed

One permitted schema description confirms `openingPrice` is a DOUBLE in `lake.sec_daily_ohlc`. Earlier archived EXP002 source queries already used it. The [28-request plan](exp004_supplement_acquisition_plan.json) was committed/pushed in `0c6f5b6` before dispatch. It preserves the exact original historical `security_segments` join, CS rule, dates and ordering, adding only `openingPrice` to the projected fields.

The first warmup quarter, **2013-12-31–2014-03-31**, completed as `{c['operation_id']}`. New requests, idempotency key, operation/status receipts, original Parquet bytes and part hashes are immutable under ignored `data/raw/EXP004/execution_inputs_v001/`. The prior 28 CLOSE-only extracts remain untouched.

| Reconciliation measure | Count |
| --- | ---: |
| Frozen / supplemental rows | {q['old_rows']:,} / {q['new_rows']:,} |
| Exact matched `(security_id,ticker,day)` keys | {q['matched_keys']:,} |
| Missing frozen / extra supplemental keys | {q['missing_keys']} / {q['extra_keys']} |
| Duplicate excess rows: frozen / supplemental | {q['duplicate_keys']['old']} / {q['duplicate_keys']['new']} |
| Matched rows compared for CLOSE | {q['close_compared_rows']:,} |
| Matched CLOSE mismatches | {q['close_row_mismatches']} |
| Frozen rows unpairable for exact-key CLOSE comparison | {q['old_rows_unpairable_for_close']} |

All **62 identity substitutions concern VPG**, spanning {c['first_discrepancy_date']}–{c['last_discrepancy_date']}. The ticker and date remain the same; the source assigns a different stable-ID string. Example observations:

| Ticker | Source day | Frozen stable ID | Supplemental stable ID |
| --- | --- | --- | --- |
{examples}

Equal counts do not certify equality. No `#2` stripping, issuer inference, alias rewrite, current-symbol lookup or exclusion of VPG was used to repair the mismatch. This establishes source-key drift under the tested same-source join; it does not establish whether the publisher changed namespace, class lineage or issuer identity. No fresh identity lookup followed. No empirical performance selected the stop.

The first diagnostic conflated projection-row differences with changed CLOSE values. Its original receipt remains immutable. The separately versioned replay correctly reports **62 missing/62 extra keys and zero matched CLOSE mismatches**; the failed population gate and stop remain unchanged. No CLOSE tolerance was introduced after inspection.

## Coverage and deferred gates

The fetched warmup part has **{c['warmup_OPEN_field_checks']['valid']:,} positive finite OPEN values, {c['warmup_OPEN_field_checks']['missing']} missing and {c['warmup_OPEN_field_checks']['invalid']} invalid**. These are raw field checks, not nominal-share execution or full Development certification. Existing adjusted-price/share-unit evidence remains a separate requirement; a positive `openingPrice` alone does not certify the raw-share/cash-dividend ledger.

The remaining **27 quarters were not requested** after reconciliation failed. No Development execution OPENs were acquired. All 273,115 frozen common-population security-decisions remain pending acquisition, not 273,115 observed NULLs or invalid prices. SPY remains separate from CS and was NOT_ACQUIRED. Dividend events/source/pay-date semantics and actual-held-path terminal discovery were NOT_RUN at this upstream stop. Their counts remain unmeasured, never zero-dividend or zero-terminal claims.

**v004: BLOCKED / not issued.** No new execution freeze, real ledger, portfolio NAV, return, Sharpe, paired excess, winner or robustness was calculated. All 24 folds/six full replays remain NOT_RUN. Economic spec `{c['specification_sha256']}`, methodology `{c['methodology_sha256']}` and engine hash `{c['engine_sha256']}` are unchanged. The older [local OPEN-input stop](exp004_local_execution_report.md), freeze v001/v002, amended panels, Nexus failure, original Development report and closed EXP005/006/007 retain their bytes.

Source operations: **1 schema description, 1 completed price query, {c['SDK_source_calls']} SDK transport calls including status/manifest/download; zero automatic retries**. Polls are distinct from query submissions. SPY/dividend/lifecycle queries 0; backtests/publication/Aurora 0; purchases/upgrades 0. Actual account debit is UNKNOWN. Exact private HTTP bodies and byte hashes are retained; credential values/contact information are not committed.

**Validation accesses 0; Test accesses 0; real performance evaluations 0.** The 59-evaluation ceiling, earlier one diagnostic and 19 failure reserves remain unchanged. No global Nexus pause was removed. The narrowly allowlisted source client permits only frozen Lake acquisition endpoints and refuses continuation after the persisted reconciliation stop; legacy remote backtest/publication paths remain paused.

Validation: **{v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped**. [Receipt](exp004_supplement_validation.json). [Canonical source review](exp004_supplement_source_review.json). Offline checks:

```sh
python -m src.research.exp004_supplement_report --check
python -m src.research.exp004_supplement_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

Public report regeneration requires tracked summaries only. Private audit requires the frozen/supplemental Parquet and original receipts and performs no network request. Acquisition requires `--execute` and is not reproduction; no stopped request is automatically resubmitted. Unrelated user files and dependency pins are unchanged. No new experiment, vendor, event-source discovery, Phase 4B, optimizer or paper/live activity occurred.

**Stopped under owner sections 5/20 at exact source-key reconciliation, before dividend/lifecycle certification or performance.** No repair mapping or further source campaign is adopted. Git checkpoints and hosted CI are delivery receipts reported separately.
'''
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('Supplement report differs')
    else:REPORT.write_bytes(text.encode())
    return c['status']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.build or a.audit:print(build()['status'])
    print(report(a.check))
