"""Offline redacted case receipts; bar candidates never imply no trading."""
import argparse,hashlib,json,math,re
from collections import Counter
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.exp004_gap_sources import PLAN,OUT
from src.research.exp004_execution_gaps import classify,amendment_ready,scale_screen,price_scope,RECOVERY

DOCS=ROOT/'docs/acceleration'
SUMMARY=DOCS/'exp004_execution_gap_review_v001.json'
REPORT=DOCS/'exp004_execution_gap_report.md'


def build(audit=False):
    from src.research.prepare_exp004 import verify_freeze
    freeze=verify_freeze();plan=json.loads(PLAN.read_bytes());policy=DOCS/'exp004_execution_gap_amendment_policy_v001.md'
    if hashlib.sha256(policy.read_bytes()).hexdigest()!=plan['policy_sha256']:raise ValueError('Policy changed after source access')
    original=ROOT/plan['inventory_source']
    if hashlib.sha256(original.read_bytes()).hexdigest()!=plan['inventory_source_sha256']:raise ValueError('Prior canonical inventory changed')
    cases=json.loads(original.read_bytes())['missing_required_OPEN_rows']
    if digest(cases)!=plan['inventory_sha256']:raise ValueError('26-case denominator changed')
    observations=json.loads((OUT/'observation_review.json').read_bytes())
    receipts=[json.loads(p.read_bytes()) for p in sorted((OUT/'http').glob('*.json'))]
    for r in receipts:
        body=(ROOT/r['body_path']).read_bytes()
        if hashlib.sha256(body).hexdigest()!=r['body_sha256'] or len(body)!=r['bytes']:raise ValueError('Original HTTP bytes changed')
    lake_refs=json.loads((OUT/'lake_batch/part_hashes.json').read_bytes())
    from src.research.exp004_supplement_qa import verify_refs
    import pyarrow.parquet as pq,duckdb
    lake=pq.read_table(verify_refs(lake_refs)).to_pylist()
    for row in lake:
        for key,value in row.items():
            if hasattr(value,'isoformat'):row[key]=value.isoformat()
    prior=json.loads(original.read_bytes());db=duckdb.connect()
    db.from_parquet(verify_refs(prior['coverage']['enriched_parts'])).create_view('frozen_prices')
    spans_path=ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json';spans=json.loads(spans_path.read_bytes())
    doc_receipt=next(r for r in receipts if 'src_app_api_documentation_documentation_module_ts-es2015' in r['url'])
    doc_text=(ROOT/doc_receipt['body_path']).read_text(errors='replace')
    raw_documented='Both raw prices and adjusted prices are available' in doc_text and 'jsonFieldName:"open"' in doc_text and 'jsonFieldName:"adjOpen"' in doc_text
    public_rows=[];candidate_bars=0;two_sided=0
    for case in cases:
        obs=next(r for r in observations if r['ticker']==case['ticker'] and r['day']==case['day'])
        primary=[r for r in lake if r['ticker']==case['ticker'] and r['case_day']==case['day']]
        if any(r['day']==case['day'] for r in primary):raise ValueError('This report is for unchanged primary gaps')
        rr=next(r for r in receipts if r['category']=='alternative_exact_case' and '/'+case['ticker']+'/prices?' in r['url'])
        parsed=json.loads((ROOT/rr['body_path']).read_bytes()) if rr['status']==200 else []
        request=next(r for r in plan['alternative_requests'] if r['ticker']==case['ticker'] and r['required_session']==case['day'])
        price_scope(parsed,*request['context_scope'])
        if parsed!=obs['alternative_rows']:raise ValueError('Alternative projection changed')
        exact=[r for r in parsed if r['date'][:10]==case['day']]
        known=[r for r in spans if r['ticker']==case['ticker'] and r['security_id']==case['security_id'] and r['asset_type']=='CS' and r['from_date']<=case['day']<=r['to_date']]
        controls=[]
        for point in primary:
            raw=db.execute('SELECT unadjustedClose FROM frozen_prices WHERE security_id=? AND ticker=? AND day=CAST(? AS DATE)',[case['security_id'],case['ticker'],point['day']]).fetchall()
            if len(raw)!=1 or raw[0][0]!=point['unadjustedClose']:raise ValueError('Diagnostic control differs from frozen observation')
            alt=next((r for r in parsed if r['date'][:10]==point['day']),None)
            if alt:controls.append({'day':point['day'],'source_sha256':rr['body_sha256'],'scale_screen_passed':scale_screen(alt['close'],raw[0][0])})
        candidate=exact[0] if len(exact)==1 else None;candidate_bars+=candidate is not None
        screen=len(controls)==2 and all(r['scale_screen_passed'] for r in controls);two_sided+=candidate is not None and screen
        positive=bool(candidate) and all(isinstance(candidate.get(k),(int,float)) and math.isfinite(candidate[k]) and candidate[k]>0 for k in ('open','close'))
        evidence={k:False for k in RECOVERY}
        evidence.update(exact_date_verified=bool(candidate),actual_session_bar_verified=bool(candidate) and candidate.get('volume',0)>0,positive_prices=positive,raw_unadjusted_contract_verified=bool(candidate) and raw_documented,share_unit_verified=bool(candidate) and screen,provenance_archived=True)
        # A dated frozen identity remains certified within its original scope.
        # Provider ticker+matching closes do not attest its class/venue/opening
        # sale-condition convention; do not silently promote that inference.
        evidence['security_identity_verified']=False
        evidence['timing_contract_verified']=False
        verdict=classify(evidence)
        note=('Raw daily bar candidate archived; surrounding scale screen '+('passes on both sides' if screen else 'is incomplete')+'. Exact provider-to-class/venue and compatible regular-session OPEN convention are not independently attested.' if candidate else 'No exact-date bar recovered from this route; empty response/404 is not proof of nontrading.')
        if case['ticker']=='TWMC':note+=' Official8-K describes an August4 deficiency notice with no immediate listing effect; it does not certify an August3 halt. Exchange endpoint returned two application errors without data; one deliberate date-format correction counted as another submission.'
        row={'required_session':case['day'],'ticker':case['ticker'],'frozen_security_id':case['security_id'],'affected_cells':case['intended_cells'],'primary_source_bar_present':False,'verdict':verdict,
             'evidence_source_1':{'source':'Existing Lake exact26case batch','parts':lake_refs},'evidence_source_2':{'source':'Tiingo exact historical symbol/context','url':rr['url'],'http_status':rr['status'],'source_sha256':rr['body_sha256'],'retrieved_at_utc':rr['retrieved_at_utc']},
             'security_identity_verified':evidence['security_identity_verified'],'frozen_identity_verified':len(known)==1,'session_trading_status':'VENDOR_REPORTED_ACTIVITY_NOT_CERTIFIED_EXECUTION' if candidate and candidate.get('volume',0)>0 else 'UNKNOWN','recovered_open':None,'recovered_close':None,
             'raw_unadjusted_contract_verified':evidence['raw_unadjusted_contract_verified'],'share_unit_verified':evidence['share_unit_verified'],'timing_contract_verified':False,'surrounding_session_check':controls,'corporate_or_listing_event':None,'first_later_certified_open_session':None,'candidate_daily_bar_present':bool(candidate),'complete_execution_interpretation':False,'source_hashes':[r['sha256'] for r in lake_refs]+[rr['body_sha256'],doc_receipt['body_sha256']],'notes':note}
        put(OUT/'case_receipts'/(case['ticker']+'_'+case['day']+'.json'),row);public_rows.append(row)
    db.close()
    requests=[json.loads(p.read_bytes()) for p in sorted((OUT/'scientific_requests').glob('*.json'))];categories=dict(Counter(r['category'] for r in requests))
    if len(requests)>40 or any(categories.get(k,0)>n for k,n in plan['allocation'].items()):raise ValueError('Scientific ceiling exceeded')
    wire=[json.loads(p.read_bytes()) for p in (OUT/'lake_batch').glob('wire_request_*.json')]
    operation=json.loads((OUT/'lake_batch/submission.json').read_bytes())['id']
    result={'version':'EXP004_execution_gap_review_v001','status':'EXECUTION_GAPS_UNRESOLVED','starting_head':plan['starting_head'],'inventory_sha256':plan['inventory_sha256'],'policy_sha256':plan['policy_sha256'],'case_rows':public_rows,'classification_counts':{v:sum(r['verdict']==v for r in public_rows) for v in __import__('src.research.exp004_execution_gaps',fromlist=['VERDICTS']).VERDICTS},'raw_daily_bar_candidates':candidate_bars,'two_sided_scale_screen_candidates':two_sided,'no_alternative_exact_bar':26-candidate_bars,'TWMC_verdict':next(r['verdict'] for r in public_rows if r['ticker']=='TWMC'),
            'request_budget':{'ceiling':40,'used':len(requests),'remaining':40-len(requests),'by_category':categories,'Lake_query_id':operation,'Lake_SDK_transport_calls':len(wire),'Lake_status_GETs':sum(r['method']=='GET' and r['path']=='lake/queries/'+operation for r in wire),'Lake_manifest_GETs':sum(r['path'].endswith('/manifest') for r in wire),'Lake_part_downloads':sum('/parts/' in r['path'] for r in wire),'direct_HTTP_retrievals':len(receipts),'browser_official_search_submissions':1,'browser_underlying_fetch_count':None,'deliberate_new_submissions_after_application_error':1,'automatic_retries':0},
            'documentation_receipts':[{k:r[k] for k in ('url','status','body_sha256','retrieved_at_utc','bytes')} for r in receipts if r['category']=='schema_documentation'],'official_HTTP_receipts':[{k:r[k] for k in ('url','status','body_sha256','retrieved_at_utc','bytes')} for r in receipts if r['category']=='official_corroboration'],
            'post_cutoff_search_snippets':'One fixed official-source search returned unrelated post-cutoff result snippets; archived/quarantined, never opened or used. No post2020 market/outcome series requested. Search is not a source timing/trading certificate.',
            'amendment_ready':amendment_ready(public_rows),'amendment_receipt_issued':False,'V001_engine_sha256':hashlib.sha256((ROOT/'src/research/exp004_local_execution.py').read_bytes()).hexdigest(),'V002_engine':None,'V002_pending_fixture_tests':'NOT_RUN_UPSTREAM_UNUSABLE_AMENDMENT','original_specification_sha256':freeze['frozen_specification_sha256'],'original_methodology_sha256':freeze['frozen_methodology_sha256'],'performance_executed':False,'fold_evaluations':'NOT_RUN','full_replays':'NOT_RUN','Development_performance_evaluations':0,'Validation_accesses':0,'Test_accesses':0,'dividend_requests':0,'broader_terminal_audit':False,'v004_issued':False,'Nexus_backtests':0,'Aurora':0,'purchases':0,'account_debit':None}
    put(SUMMARY,result);put(OUT/'final_stop.json',{'status':result['status'],'canonical_review_sha256':digest(result),'source_continuation_authorized':False})
    return result


def report(check=False):
    c=json.loads(SUMMARY.read_bytes());vpath=DOCS/'exp004_execution_gap_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    rows='\n'.join(f"| {r['required_session']} | {r['ticker']} | {', '.join(r['affected_cells'])} | {'YES' if r['candidate_daily_bar_present'] else 'NO'} | {len(r['surrounding_session_check'])}/2 | {r['verdict']} |" for r in c['case_rows'])
    counts='\n'.join(f'| {k} | {n} |' for k,n in c['classification_counts'].items());b=c['request_budget']
    text=f'''# EXP004 26 execution gaps: bounded forensic stop

**EXECUTION_GAPS_UNRESOLVED. All 26 retained; no-fill policy inactive; hypothesis untested.** Starting HEAD `{c['starting_head']}`, as of 2026-10-14. [Owner instruction](owner_exp004_execution_gaps_2026-10-14.md), [pre-performance plan](exp004_execution_gap_investigation_plan_v001.json), [exact policy](exp004_execution_gap_amendment_policy_v001.md), [canonical case receipts](exp004_execution_gap_review_v001.json).

The policy and exact persisted denominator were pushed in `3eb2d1a` before source investigation. It predeclares 40 scientific submissions and universal pending target-weight mechanics. The previous VPG bridge, 28-quarter enrichment, frozen identities/CLOSEs, SPY coverage and failed historical reports remain unchanged. This pass investigated execution evidence, not strategy outcomes.

## What the sources established

One exact26case Lake batch again found no required-date bars. It supplied adjoining observations for source checks; every used nominal CLOSE exactly reconciles to frozen prices. Twenty-six fixed Tiingo requests ran in TWMC-first order, each restricted to the required date and immediately adjoining certified calendar sessions. **{c['raw_daily_bar_candidates']} exact-date raw daily bar candidates** were archived; {c['two_sided_scale_screen_candidates']} have two-sided raw-close scale agreement under the predeclared2% sanity screen. TRNS has a bar but only one adjoining Lake control. Nine cases have no recovered exact-date bar from that route: TWMC/NFEC returned404; seven returned empty200 arrays. None proves no trading.

The official Tiingo documentation page is a shell. Its explicitly linked client/runtime/documentation module was archived and inspected offline. The publisher distinguishes raw from adjusted fields and describes date-specific daily opening/closing prices. Those definitions and close agreement do not independently attest exact provider-to-historical-class/venue binding or the regular-session opening-sale convention matching EXP004. The original Lake OPEN share-unit convention is also not resolved by this gap pass. **No candidate bar was promoted to RECOVERED_EXECUTION_BAR**, and raw candidate prices remain private rather than becoming executable inputs. Numeric/vendor-report success is separate from the frozen eight-condition execution standard.

Vendor-reported bars include CEMI/KIQ on2017-07-03 and BBU on2018-07-02. The holiday-adjacent pattern therefore does not establish that all such gaps are genuine nontrading. No absence, low volume, shortened calendar or empty vendor response was converted to a halt or no-fill certificate.

## TWMC first, and the exact remaining uncertainty

The frozen snapshot keeps TWMC's same class/CIK active on2020-08-03 and records KSPN from2020-09-08; no current ticker was projected backward. Tiingo's exact TWMC route returned404. The [issuer8-K filed2020-08-10](https://www.sec.gov/Archives/edgar/data/795212/000114036120017995/brhc10014270_8k.htm) describes a Nasdaq stockholders-equity deficiency notice receivedAugust4, with no immediate listing effect. It neither certifies a halt onAugust3 nor provides a compatible OPEN/CLOSE. The exchange historical endpoint returned application errors without data; the separately recorded ISO-date correction consumes another scientific submission. Neither error establishes no trading or universal exchange-archive absence.

TWMC remains **UNRESOLVED_VENDOR_GAP**. The other nine no-bar/incomplete-control cases and the16 two-sided candidates likewise lack the required complete evidence. No exact-day nontrading, executable interruption or positive identity/share-unit conflict was certified. These are evidence limitations, not proof of bad market observations or an economic failure.

| Verdict | Count |
| --- | ---: |
{counts}

| Required date | Ticker | Affected cells | Raw daily candidate | Adjoining controls | Final verdict |
| --- | --- | --- | --- | ---: | --- |
{rows}

Each immutable canonical row retains the original stable ID, source hashes/URLs/retrieval UTC, status, identity/raw/unit/timing flags, control checks and precise reason. Recovered OPEN/CLOSE and first-later-certified-OPEN fields remain unavailable. There are no strategy return fields and no dropped/replacement cases.

## Budget and amendment boundary

**{b['used']}/{b['ceiling']} scientific submissions; {b['remaining']} remaining**: Lake batch1, exact-case alternative26, official corroboration4, documentation5. The four official submissions comprise one issuer document, one official-source discovery query and two exchange endpoint submissions. The deliberate date-format correction is counted; automatic retries0. SDK transports {b['Lake_SDK_transport_calls']} include status GETs{b['Lake_status_GETs']}, manifest GETs{b['Lake_manifest_GETs']} and part downloads{b['Lake_part_downloads']}, separately from the single Lake query. Direct HTTP retrievals{b['direct_HTTP_retrievals']}. Browser underlying fetch count is unknown. One constrained discovery search returned unrelated post-cutoff snippets; they remain quarantined, unopened and unused, with no post2020 market/outcome series request. Current software documentation is not a historical trading observation.

**No execution amendment receipt issued; V002 not created; V001 preserved.** Policy SHA-256 `{c['policy_sha256']}` is frozen, but all-case activation failed. The policy defines cash remaining cash, retained pending sells/no assumed proceeds, full-funding-only pending buys, first later compatible OPEN with one pre-fill equity snapshot, no weight redistribution, monthly supersession, fill-only0.10% fees, certified split/terminal handling and labelled STALE_MARK_NONEXECUTABLE valuation only during positively certified nontrading. No such treatment was applied to these unresolved cases. Pending-order engine fixtures were not implemented because owner section13 conditions V002 on a usable amendment; V001 fixtures remain regression-tested.

Preserved hashes: spec `{c['original_specification_sha256']}`, methodology `{c['original_methodology_sha256']}`, V001 `{c['V001_engine_sha256']}`. The original freeze is unchanged. Raw source bodies/private projections/receipts remain ignored and immutable; contacts/credentials and signed URLs are not committed. No purchases/upgrades; account-wide debit unknown.

**24 folds NOT_RUN; six full replays NOT_RUN; Development evaluations0; Validation accesses0; Test accesses0.** No dividends, downstream held-terminal programme, v004, robustness, new experiment, other vendor campaign, Nexus/Aurora, optimizer, Phase4B or paper/live occurred. The prior59 evaluation ceiling/19 remaining reserves remain unchanged. This task deliberately ends at the gap gate, even if a later owner review finds a remedy.

Validation: **{v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped**. [Receipt](exp004_execution_gap_validation.json). Public regeneration reads tracked summaries; private audit verifies original HTTP/Parquet, controls, immutable case receipts and preserved unknowns without source requests:

```sh
python -m src.research.exp004_execution_gap_report --check
python -m src.research.exp004_execution_gap_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

**Stopped under owner sections12/17/19.** Vendor gaps cannot activate no-fill. No further source submission, amendment, engine or performance continuation follows automatically. Git/push and hosted CI are delivery receipts reported separately.
'''
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('Execution-gap report differs')
    else:REPORT.write_bytes(text.encode())
    return c['status']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.build or a.audit:print(build(a.audit)['status'])
    print(report(a.check))
