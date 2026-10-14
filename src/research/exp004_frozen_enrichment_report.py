"""Offline all-quarter price bridge and missing execution-session report."""
import argparse,hashlib,json
from collections import Counter
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.exp004_frozen_price_bridge import OUT,DOCS,CERT
from src.research.exp004_supplement_qa import verify_refs

SUMMARY=DOCS/'exp004_frozen_enrichment_review_v001.json'
REPORT=DOCS/'exp004_frozen_enrichment_report.md'


def audit_coverage():
    import duckdb,pyarrow as pa,pyarrow.parquet as pq
    from src.research.exp004_frozen_price_bridge import build,enrich,execution_open_coverage
    from src.research.exp004_compile import calendar
    bridge=build();plan=json.loads((DOCS/'exp004_frozen_price_acquisition_plan_v001.json').read_bytes());prices=OUT/'prices'
    first_name='bars_2013-12-31_2014-03-31'
    rows=[dict(bridge['first_quarter'],name=first_name,old_parts=bridge['frozen_parts'],source_parts=bridge['completed_source_parts'])]
    _,first=enrich(pq.read_table(verify_refs(bridge['frozen_parts'])),pq.read_table(verify_refs(bridge['completed_source_parts'])))
    first_path=OUT/'first_quarter_enriched_frozen.parquet'
    if not first_path.exists():
        with first_path.open('xb') as f:pq.write_table(first,f)
    refs=[{'path':first_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(first_path.read_bytes()).hexdigest(),'bytes':first_path.stat().st_size}]
    put(OUT/'first_quarter_enriched_ref.json',refs[0])
    for r in plan['requests']:
        source_refs=json.loads((prices/r['name']/'part_hashes.json').read_bytes())
        source=pq.read_table(verify_refs(source_refs));old=pq.read_table(verify_refs(r['old_part_hashes']))
        if any(not r['request']['params'][0]<=d.isoformat()<=r['request']['params'][1] for d in source['day'].to_pylist()):raise ValueError('Out-of-scope price')
        qa,enriched=enrich(old,source);qa.update(name=r['name'],old_parts=r['old_part_hashes'],source_parts=source_refs)
        put(prices/r['name']/'enrichment_qa.json',qa)
        if qa['status']!='PASS_FROZEN_PRICE_ENRICHMENT':raise ValueError(qa['status'])
        ref=json.loads((prices/r['name']/'enriched_ref.json').read_bytes());stored=pq.read_table(verify_refs([ref]))
        if not stored.equals(enriched):raise ValueError('Enriched price derivative changed')
        rows.append(qa);refs.append(ref)
    if not pq.read_table(verify_refs(refs[:1])).equals(first):raise ValueError('Reused enriched part changed')
    db=duckdb.connect();db.from_parquet(verify_refs(refs)).create_view('enriched');required=[]
    raw=ROOT/'data/raw/EXP004/production_inputs_v001'
    for y in range(2015,2021):
        for panel in json.loads((raw/f'compiled_{y}_v002/decision_inputs.json').read_bytes()):
            required.extend({'security_id':sid,'ticker':ticker,'day':panel['decision']['session']} for sid,ticker in panel['ticker_byid'].items())
    put(OUT/'required_monthly_OPEN_keys.json',required);db.register('required',pa.Table.from_pylist(required))
    count=lambda sql:db.execute(sql).fetchone()[0]
    open_coverage=execution_open_coverage(pa.Table.from_pylist(required),pq.read_table(verify_refs(refs)))
    missing=open_coverage['missing'];valid=open_coverage['valid']
    spy_refs=[ref for q in rows for ref in q['source_parts'] if q['name'].startswith(tuple('bars_'+str(y) for y in range(2015,2021)))]
    db.from_parquet(verify_refs(spy_refs)).create_view('source')
    spy=db.execute("SELECT ticker,day,openingPrice,unadjustedClose FROM source WHERE ticker='SPY' AND day BETWEEN DATE '2015-01-02' AND DATE '2020-12-31' ORDER BY day").fetch_arrow_table()
    spy_path=OUT/'SPY_source_prices.parquet'
    if not spy_path.exists():
        with spy_path.open('xb') as f:pq.write_table(spy,f)
    if not pq.read_table(spy_path).equals(spy):raise ValueError('SPY derivative changed')
    spans=json.loads((ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json').read_bytes());spy_span=[r for r in spans if r['ticker']=='SPY']
    expected=[d for d in calendar() if d.isoformat()>='2015-01-02'];days=spy['day'].to_pylist()
    from src.research.exp004_supplement_qa import opens
    spyqa={'source_table':'lake.sec_daily_ohlc','source_key':['SPY','day'],'role':'EXPLICIT_ETF_BENCHMARK_SEPARATE_FROM_CS','source_rows':spy.num_rows,'unique_days':len(set(days)),'expected_sessions':len(expected),'missing_sessions':len(set(expected)-set(days)),'extra_sessions':len(set(days)-set(expected)),'OPEN':opens(spy['openingPrice'].to_pylist()),'frozen_identity_candidates':spy_span,'price_sha256':hashlib.sha256(spy_path.read_bytes()).hexdigest(),'inception_row':spy.slice(0,1).to_pylist(),'source_unit_certificate':'NOT_CERTIFIED'}
    for r in spyqa['inception_row']:r['day']=r['day'].isoformat()
    value={'price_enrichment_status':'PASS_ALL28_FROZEN_PRICE_ROWS','quarter_results':rows,'frozen_rows':sum(q['frozen_rows'] for q in rows),'enriched_rows':sum(q['enriched_rows'] for q in rows),'unused_source_extras':sum(q['unused_source_extras'] for q in rows),'unique_frozen_stable_ids':count('SELECT COUNT(DISTINCT security_id) FROM enriched'),'required_monthly_OPEN_pairs':len(required),'valid_monthly_OPEN_pairs':valid,'missing_monthly_OPEN_pairs':missing,'invalid_monthly_OPEN_pairs':len(required)-missing-valid,'enriched_parts':refs,'SPY':spyqa,'new_identity_queries':1,'new_price_queries':27,'source_calls':len(list(OUT.glob('identity/wire_request_*.json')))+len(list(OUT.glob('prices/*/wire_request_*.json'))),'new_schema_queries':0,'retries':0,'performance_executed':False}
    put(OUT/'price_coverage.json',value)
    missing_rows=db.execute('SELECT r.*,s.openingPrice,s.unadjustedClose FROM required r LEFT JOIN enriched e ON r.security_id=e.security_id AND r.ticker=e.ticker AND CAST(r.day AS DATE)=e.day LEFT JOIN source s ON r.ticker=s.ticker AND CAST(r.day AS DATE)=s.day WHERE e.security_id IS NULL ORDER BY r.day,r.ticker').fetch_arrow_table().to_pylist()
    put(OUT/'missing_required_OPEN_review.json',missing_rows);db.close()
    return value,missing_rows


def build(audit=False):
    from src.research.prepare_exp004 import verify_freeze
    freeze=verify_freeze();coverage=json.loads((OUT/'price_coverage.json').read_bytes());missing=json.loads((OUT/'missing_required_OPEN_review.json').read_bytes())
    if audit:coverage,missing=audit_coverage()
    panels=[]
    for year in range(2015,2021):panels+=json.loads((ROOT/f'data/raw/EXP004/production_inputs_v001/compiled_{year}_v002/decision_inputs.json').read_bytes())
    by_day={p['decision']['session']:p for p in panels};affected=[]
    for r in missing:
        if r['openingPrice'] is not None or r['unadjustedClose'] is not None:raise ValueError('Missing-key finding requires price-key absence, not ID substitution')
        affected.append(dict(r,intended_cells=['EW']+[name for name,targets in by_day[r['day']]['targets'].items() if r['security_id'] in targets],reason='NO_OHLC_ROW_FOR_REQUIRED_TICKER_DAY'))
    result={'status':'LOCAL_EXECUTION_INPUTS_BLOCKED','specific_blocker':'REQUIRED_EXECUTION_OPEN_ROWS_MISSING','starting_head':'4b75f8d5eb9bf6cae451ec34afe45ec113c0ac97','bridge_certificate_sha256':hashlib.sha256(CERT.read_bytes()).hexdigest(),'VPG_verdict':'VPG_SAME_SECURITY_NAMESPACE_DRIFT','coverage':coverage,'missing_required_OPEN_rows':affected,'missing_by_year':dict(sorted(Counter(r['day'][:4] for r in missing).items())),'missing_intended_cell_counts':dict(sorted(Counter(c for r in affected for c in r['intended_cells']).items())),'all_missing_keys_absent_from_price_only_source':True,'specification_sha256':freeze['frozen_specification_sha256'],'methodology_sha256':freeze['frozen_methodology_sha256'],'engine_sha256':hashlib.sha256((ROOT/'src/research/exp004_local_execution.py').read_bytes()).hexdigest(),'v004':'BLOCKED_NOT_ISSUED','dividend_queries':0,'dividend_events':None,'dividend_semantics':'NOT_CERTIFIED_UPSTREAM_REQUIRED_OPEN_STOP','actual_held_terminal_cases':None,'terminal_resolved':None,'terminal_unresolved':None,'performance_evaluations':0,'fold_evaluations':0,'full_replays':0,'Validation_accesses':0,'Test_accesses':0,'Nexus_backtests':0,'publication':0,'Aurora':0,'purchases':0,'account_debit':None,'future_unit_and_lifecycle_gates':'DEFERRED; positive OPEN field coverage alone does not certify nominal-share/cash-dividend execution'}
    put(SUMMARY,result);put(OUT/'execution_input_stop.json',{'status':result['status'],'specific_blocker':result['specific_blocker'],'summary_sha256':digest(result),'automatic_continuation':False})
    return result


def report(check=False):
    c=json.loads(SUMMARY.read_bytes());cov=c['coverage'];vpath=DOCS/'exp004_frozen_enrichment_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    quarters='\n'.join(f"| {q['name'].removeprefix('bars_')} | {q['frozen_rows']:,} | {q['enriched_rows']:,} | {q['missing']} | {q['duplicate_source_excess_rows']} | {q['CLOSE_mismatches']} | {q['OPEN']['missing']} / {q['OPEN']['invalid']} |" for q in cov['quarter_results'])
    missing='\n'.join(f"| {r['day']} | {r['ticker']} | `{r['security_id']}` | {', '.join(r['intended_cells'])} |" for r in c['missing_required_OPEN_rows'])
    text=f'''# EXP004 frozen-price enrichment: complete acquisition, execution-row stop

**LOCAL_EXECUTION_INPUTS_BLOCKED — REQUIRED_EXECUTION_OPEN_ROWS_MISSING. VPG namespace drift resolved; economic hypothesis untested.** Starting HEAD `{c['starting_head']}`, as of 2026-10-14. [Owner instruction](owner_exp004_vpg_bridge_2026-10-14.md), [source bridge](exp004_frozen_price_bridge_report.md), [canonical review](exp004_frozen_enrichment_review_v001.json).

## Resolved identity and completed enrichment

The bounded current identity query returned four records. VPG retains frozen CIK 1487952, CS type, share-class FIGI BBG001T5X9F2 and the 2010-07-07–2020-12-31 in-scope span. The current ID `ticker:VSHw@2010-06-24#2` differs from frozen `ticker:VSHw@2010-06-24`; the unsuffixed current VSHw record has a different CIK and ends before that span. The [certificate](exp004_frozen_price_bridge_v001.json) records **VPG_SAME_SECURITY_NAMESPACE_DRIFT** with independent fields and nonoverlap evidence. Internal publisher ID-generation code is not claimed audited; early when-issued spin-off economics remain outside this scoped equivalence.

Bridge checkpoint `c6d7224` was pushed before the remaining requests. The first quarter reused verified source bytes; no repeat request was made. The other 27 queries selected only ticker/day/openingPrice/unadjustedClose from `lake.sec_daily_ohlc`, with exact frozen bounds and no security_segments join. Every enriched row keeps its frozen security_id and CLOSE. No suffix stripping, replacement identity, new universe or survivor screen occurred. Extra source rows were excluded from candidate/EW enrichment; SPY was separately selected as its existing frozen ETF benchmark.

| Quarter | Frozen rows | Enriched rows | Missing source keys | Duplicate source keys | CLOSE mismatches | Missing / invalid OPEN fields |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{quarters}

Totals: **{cov['frozen_rows']:,} frozen / {cov['enriched_rows']:,} enriched rows**, {cov['unique_frozen_stable_ids']:,} stable IDs; all 28 quarters pass required-key uniqueness, exact CLOSE equality and positive finite OPEN-field checks. Observed source extras excluded from candidate/EW enrichment: {cov['unused_source_extras']:,}; first-quarter extras are measured only inside its archived CS-joined response. No first-quarter global source census is claimed.

## Concrete execution-session failure

Frozen numeric QA required complete prior sessions and historical execution identity; it did not prove that an execution-day OHLC row exists. Joining the 72 immutable monthly panels to the enriched prices gives **{cov['required_monthly_OPEN_pairs']:,} required common-population security/session pairs: {cov['valid_monthly_OPEN_pairs']:,} positive finite OPENs, {cov['missing_monthly_OPEN_pairs']} missing rows and {cov['invalid_monthly_OPEN_pairs']} invalid present OPENs**.

Every missing ticker/day is also absent from the full price-only responses, before any identity join. This is not renewed ID drift or 26 observed NULL-valued source bars: the rows themselves are unavailable. Each would be required by the frozen EW target; intended momentum cells are listed only where that security belongs to the frozen target. These are source/target checks, not executed holdings or performance.

| Required session | Ticker | Frozen stable ID | Intended cells affected |
| --- | --- | --- | --- |
{missing}

Earliest established failure: **2015-09-01 / SGOC / EW**. No adjacent-day/close substitution, cash allocation in place of a missing target, stale-price holding or population pruning was applied. This blocks the complete programme even if some cell/fold subsets have all their intended OPENs. No economic verdict can be inferred.

## SPY, actions and certificate boundary

SPY was recovered from the already acquired price-only responses, without another request or CS filtering: **{cov['SPY']['source_rows']:,} unique Development sessions**, {cov['SPY']['missing_sessions']} missing calendar sessions and {cov['SPY']['OPEN']['missing']} missing/{cov['SPY']['OPEN']['invalid']} invalid OPEN fields. The original historical snapshot binds it separately as ETF `figi:BBG001S72SM3`, CIK 884394. Inception 2015-01-02 is present. This is field/calendar/identity coverage, not cash-dividend or complete raw-share execution certification.

Dividend queries/events/accounting certification and actual-held terminal discovery were **NOT_RUN after the upstream required-OPEN failure**. Counts remain unmeasured, never zero-dividend or zero-terminal claims. The existing source schema includes declaration/ex/record/pay dates; their availability and semantics for held events are not certified by this pass. OPEN adjustment/share-unit consistency and lifecycle/calendar gates remain deferred; positive numeric OPENs alone cannot become nominal-share ledger inputs.

**v004: BLOCKED / not issued.** Spec `{c['specification_sha256']}`, methodology `{c['methodology_sha256']}` and engine `{c['engine_sha256']}` remain unchanged. No new economic/execution freeze, real ledger, NAV, return, effect, interval, p-value, selection or robustness exists. All 24 fold evaluations and six full replays remain NOT_RUN. The prior 59-evaluation ceiling, one diagnostic and 19 failure reserves remain unchanged.

New source operations: **1 identity query + 27 price queries; {cov['source_calls']} SDK transport calls**, including polls/manifests/downloads; 0 new schema queries, 0 retries, 0 SPY-only queries, 0 dividend/lifecycle queries. Previous first-quarter/source-schema operations are historical cache evidence, not new starts. Nexus backtests/publication/Aurora/purchases 0; actual debit UNKNOWN. Original and derived source bytes, request/operation receipts and hashes remain private and immutable. Contacts/credentials are not committed.

**Validation accesses 0; Test accesses 0; performance evaluations 0.** No 2021+ market/outcome data was queried or decoded. Prior reports, failed receipts, frozen experiments, processed baselines, metric code, dependency pins and remote pause remain unchanged. EXP005/006/007 stay closed and absent; no new experiment, vendor, source-family discovery, Phase 4B, optimizer or paper/live action occurred.

Validation: **{v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped**. [Receipt](exp004_frozen_enrichment_validation.json). Reproduce public report checks from tracked receipts; private audit reads immutable source parts and panels without network:

```sh
python -m src.research.exp004_frozen_enrichment_report --check
python -m src.research.exp004_frozen_enrichment_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

**Stopped at owner sections 12/24/25: required execution OPENs are missing.** The bridge source certificate passed; the local execution certificate did not. No further source request or downstream continuation follows automatically. Commit/push and hosted CI are delivery receipts reported separately.
'''
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('Enrichment report differs')
    else:REPORT.write_bytes(text.encode())
    return c['status']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.build or a.audit:print(build(a.audit)['status'])
    print(report(a.check))
