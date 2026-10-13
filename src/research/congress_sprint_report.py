"""Canonical EXP007 source-validation stop; no remote acquisition or outcomes."""
from collections import Counter
import argparse,hashlib,json,sqlite3
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.surfaces.congressional import TABLES,CongressionalDisclosuresAdapter
from src.research.congress_sprint import classify,resolution,contributor_asof
from src.research.congress_sprint_source import RAW,DOCS,OLD,PLAN
from src.research.congress_sprint_review import corpus

SUMMARY=DOCS/'exp007_source_validation_receipt_v002.json'
REPORT=DOCS/'exp007_source_validation_report.md'


def build():
    p=json.loads(PLAN.read_bytes());g=json.loads((DOCS/'exp007_source_geometry.json').read_bytes())
    sample=json.loads((DOCS/'exp007_original_validation_sample.json').read_bytes())
    validation=json.loads((RAW/'original_field_validation_v002.json').read_bytes())
    original=json.loads((RAW/'original_acquisition_result.json').read_bytes())
    data=corpus(range(int(g['development'][0][:4]),int(g['development'][1][:4])+1))
    trades=data['political_trades'];events=data['political_trade_events'];cutoff=g['development'][1]
    trades=[r for r in trades if g['development'][0]<=r['available_at'][:10]<=cutoff]
    purchases=[r for r in trades if r['action']=='purchase'];stock=[r for r in purchases if classify(r)['status']=='COMMON_EQUITY_CANDIDATE']
    resolved=[r for r in stock if resolution(r)['status']=='SOURCE_RESOLVED_CANDIDATE']
    lookup={(r['chamber'],r['doc_id'],r['row_index']):r for r in trades};links=Counter()
    for event in events:
        if not g['development'][0]<=event['available_at'][:10]<=cutoff:continue
        link=contributor_asof(event,trades,lookup=lookup)
        links['future_contributor_links_excluded']+=len(link['future_contributors_not_used'])
        links['unavailable_contributor_links']+=len(link['unavailable_contributors'])
    baseline=json.loads((ROOT/'.research/exp007/baseline.json').read_bytes())
    protected={name:h for name,h in baseline.items() if name.startswith(('experiments/','data/processed/')) or name.startswith('docs/acceleration/') and name!='docs/acceleration/master_plan.md'}
    for name,h in protected.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('Retired/frozen historical artifact changed: '+name)
    source_starts={};statuses=Counter();source_receipts=[]
    for stage in ('snapshot','originals'):
        source_starts[stage]=len(list((RAW/stage).glob('*/reservations/*.json')))
        for f in (RAW/stage).glob('*/receipts/*.json'):
            r=json.loads(f.read_bytes());Archive(f.parent.parent).read(r['body']);statuses[str(r['status'])]+=1
            source_receipts.append({'stage':stage,'provider':f.parent.parent.name,'status':r['status'],'body':r['body'],
                'request_started_at_utc':r['request_started_at_utc'],'retrieved_at_utc':r['retrieved_at_utc']})
    # Raw redirect targets may be signed: tracked provenance stores hashes/bodies,
    # not their query credentials. Exact publisher redirects remain private.
    m=json.loads((OLD/'snapshot_manifest.json').read_bytes());pin=json.loads((OLD/'snapshot_pin.json').read_bytes())
    manifest_sources=[]
    for f in (OLD/'CONGRESS/receipts').glob('*.json'):
        r=json.loads(f.read_bytes())
        if r.get('body',{}).get('sha256')==pin['source_sha256']:manifest_sources.append({'original_body_sha256':r['body']['sha256'],'retrieved_at_utc':r['retrieved_at_utc']})
    if not manifest_sources:raise ValueError('Original pinned-manifest retrieval provenance not found')
    c={'version':'EXP007_source_validation_stop_v002','status':'ORIGINAL_SOURCE_VALIDATION_BLOCKED',
       'starting_head':p['starting_head'],'proposed_experiment_id':'EXP007','proposed_label':'EXP007_CONGRESSIONAL_PURCHASE_DISCLOSURE',
       'experiment_registered':False,'hypothesis_status':'UNTESTED','snapshot_revision':p['snapshot_revision'],
       'snapshot_manifest_sha256':p['snapshot_manifest_sha256'],'generatedAt':p['generatedAt'],'original_manifest_retrieval':manifest_sources,
       'evidence_tier':'AUDITED_EXTERNAL_DERIVED','source_file_hashes':[{'path':f['publicPath'],'sha256':f['sha256'],'bytes':f['size']} for f in p['table_files']],
       'all_loaded_source_counts':g['row_counts'],'source_years':[2012,2025],'development':g['development'],'confirmation':g['workflow_held_out_confirmation'],
       'confirmation_source_geometry_only_reviewed':True,'confirmation_outcome_accesses':0,
       'original_validation_sample_sha256':digest(sample),'original_validation_observations':len(sample['records']),
       'original_validation_sha256':digest(validation),'field_results':validation['field_results'],
       'source_original_outcomes':dict(Counter(x['chamber']+':'+x['status'] for x in original['records'])),
       'original_observation_reasons':dict(Counter(r['reason'] for r in validation['records'])),
       'sample_chambers':sample['actual_strata']['chambers'],'sample_expected_purchases':sum(r['action_expected']=='purchase' for r in validation['records']),
       'sample_purchase_type_results':dict(Counter(r['fields']['transaction_type'] for r in validation['records'] if r['action_expected']=='purchase')),
       'observed_purchase_type_disagreements':validation['purchase_type_disagreements'],
       'purchase_classification_reliability':'PARTIAL_UNKNOWN_NOT_PROVEN_UNRELIABLE_OR_CERTIFIED',
       'stop_reason':'Official Senate paper403 persisted; all35 Senate validation observations remain unavailable, while34 House observations have image-only/empty text. Required original-field validation is not established across the declared source frame.',
       'source_population_development':{'purchase_trade_records':len(purchases),'source_stock_type_candidates':len(stock),'source_resolved_stock_candidates':len(resolved),
         'printed_ticker_present_in_stock_candidates':sum(bool(r['printed_ticker']) for r in stock),
         'resolved_ticker_present_in_stock_candidates':sum(bool(r['resolved_ticker']) for r in stock),
         'unresolved_stock_candidates':len(stock)-len(resolved),'unknown_purchase_asset_classes':sum(classify(r)['status']=='UNKNOWN_ASSET_CLASS' for r in purchases),
         'purchase_records_by_year':dict(sorted(Counter(r['available_at'][:4] for r in purchases).items())),
         'stock_candidates_by_year':dict(sorted(Counter(r['available_at'][:4] for r in stock).items())),
         'source_resolved_candidates_by_year':dict(sorted(Counter(r['available_at'][:4] for r in resolved).items())),
         'provider_confirmed':None,'path_certified':None,'final_unique_trading_events':None},
       'version_guard_findings':dict(links),'version_interval_anomalies':g['version_anomalies'],
       'availability_rule':p['availability'],'upstream_timing':p['upstream_timing'],'exact_public_availability':'UNKNOWN','policy_activated':False,
       'identity_provider_requests':0,'market_outcome_requests':0,'inference_methods_evaluated':0,'synthetic_power_run':False,
       'spec_sha256':None,'freeze_commit':None,'performance_evaluations':0,'real_trial_ceiling':8,
       'source_starts':source_starts,'total_scientific_source_starts':sum(source_starts.values()),'HTTP_statuses':dict(statuses),
       'source_receipts':source_receipts,'snapshot_verified_prior_cache_hits':3,'retries':0,'additional_source_browser_requests':0,
       'Nexus_Aurora_requests':0,'purchases_upgrades':False,'account_wide_debit':'UNKNOWN','held_out_outcomes_opened':False,
       'prior_failed_pdf_review_sha256':hashlib.sha256((RAW/'original_field_validation_v001.json').read_bytes()).hexdigest(),
       'initial_resolution_summary_sha256':hashlib.sha256((RAW/'source_validation_summary_v001.json').read_bytes()).hexdigest(),
       'resolution_role_correction':'Printed status uses printedTicker as unchanged candidate even when resolvedTicker is null; both original fields retained. Initial summary incorrectly required resolvedTicker for printed status. No market outcomes used.',
       'protected_artifact_hashes':protected,'no_retired_experiment_reopened':True}
    put(SUMMARY,c);return c


def audit():
    c=json.loads(SUMMARY.read_bytes());plan=json.loads(PLAN.read_bytes());m=json.loads((OLD/'snapshot_manifest.json').read_bytes())
    if digest(m)!=c['snapshot_manifest_sha256']:raise ValueError('Pinned manifest changed')
    a=CongressionalDisclosuresAdapter(m,RAW/'snapshot_files',revision=c['snapshot_revision'],retrieved_at=c['original_manifest_retrieval'][0]['retrieved_at_utc'])
    for f in plan['table_files']:a.verify(f)
    sample=json.loads((DOCS/'exp007_original_validation_sample.json').read_bytes())
    if digest(sample)!=c['original_validation_sample_sha256']:raise ValueError('Frozen validation sample changed')
    from src.research.congress_originals import review
    if digest(review())!=c['original_validation_sha256']:raise ValueError('Original field checks changed')
    if build()!=c:raise ValueError('Canonical source stop changed')
    for stage in ('snapshot','originals'):
        if c['source_starts'][stage]>128:raise ValueError('Source budget exceeded')
    db=sqlite3.connect((ROOT/'.research/state.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    if db.execute("select count(*) from experiments where id like 'EXP007%'").fetchone()[0]:raise ValueError('Blocked experiment registered')
    return {'status':'PASS','pinned_Parquet_files':42,'neutral_original_observations':96,'confirmation_outcome_accesses':0}


def report(check=False):
    c=json.loads(SUMMARY.read_bytes());g=json.loads((DOCS/'exp007_source_geometry.json').read_bytes());p=c['source_population_development']
    vpath=DOCS/'exp007_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    fields='\n'.join(f"| {name.replace('_',' ')} | {counts.get('AGREE',0)} | {counts.get('DISAGREE',0)} | {sum(n for k,n in counts.items() if k not in ('AGREE','DISAGREE'))} |" for name,counts in c['field_results'].items())
    years='\n'.join(f"| {year} | {count:,} | {p['stock_candidates_by_year'].get(year,0):,} | {p['source_resolved_candidates_by_year'].get(year,0):,} |" for year,count in p['purchase_records_by_year'].items())
    text=f'''# EXP007 congressional purchase sprint: original-source validation stop

**ORIGINAL_SOURCE_VALIDATION_BLOCKED. Hypothesis untested; no registration, freeze or Development.** Starting HEAD `{c['starting_head']}`, as of 2026-10-13. [Owner instruction](owner_exp007_congressional_2026-10-13.md) authorized one predictive disclosure study, not reopening EXP002–EXP006. EXP007 was verified free in read-only state before source work; roadmap mentions were not treated as registration.

## Pinned source and actual schema

The audited external derived snapshot remains **AUDITED_EXTERNAL_DERIVED**, not PRIMARY_ORIGINAL. Dataset revision `{c['snapshot_revision']}`, manifest SHA256 `{c['snapshot_manifest_sha256']}`, generatedAt `{c['generatedAt']}`. Its original manifest body hash/retrieval timestamps and all42 file hashes/lengths are in [the canonical receipt](exp007_source_validation_receipt_v002.json). Acquired2012–2025 tables reconcile to {c['all_loaded_source_counts']['political_filings']:,} filings, {c['all_loaded_source_counts']['political_trades']:,} trade rows and {c['all_loaded_source_counts']['political_trade_events']:,} event versions. Three prior2020 files were hash-verified cache hits. The incomplete2026 partitions were not acquired. This is the declared reconstructed snapshot corpus, not every legal disclosure, perfect extraction/resolution or contemporaneous ingestion.

| Required role | Actual upstream field / location |
| --- | --- |
| Logical event/version | events.eventId / version |
| Member/chamber | all tables.memberId / chamber; filerKey, displayName, identitySource and filer names retained |
| Reported ownership | trades/events.owner; trades.ownerCodeRaw; no owner filter or claim that the member personally executed every disclosed household transaction |
| Transaction/date/type | trades.transactionDate / action / actionCodeRaw; events.transactionDate / action |
| Asset description/type | trades/events.assetDescription / assetTypeCode / assetTypeLabel |
| Printed/resolved identity | trades.printedTicker / resolvedTicker / resolutionStatus / resolutionReason; events.ticker is retained only as upstream provenance |
| Official source document | filings/trades.docId; events.sourceDocId / sourceRowIndex; sourceUrl and rawSha256 where available |
| Version information time | events.firstAvailableAt / availableAt / supersededAt; filings/trades.availableAt and availabilitySource |
| Amount | trades.amountBracket / amountLow / amountHigh; event amountLow / amountHigh; descriptive only |
| Contributors | events.contributorRowIds; links are date-filtered before any as-of descriptive count |

[Scope/schema contract](exp007_source_sprint_contract.json) records the actual Arrow types. The existing adapter normalizes camelCase and upstream naive Arrow timestamps as audited UTC epoch values; that representation does not turn modeled EOD into observed website publication time.

## Source-only stages and original validation

Both chambers and all twelve calendar months are observed in the contiguous2014–2025 corpus partitions. That is snapshot observation support, not legal-universe completeness. The rounded chronological70/30 rule yields **Development2014-01-01–2021-12-31**, **workflow-held-out confirmation2022-01-01–2025-12-31**. Year counts use upstream UTC availability partitions; actual New York entry/exit calendars and stage-edge buffering remain uncertified. This source-only split is not an executable stage certificate. 2012 is partial-year/Senate-only;2013 is Senate-only; neither was silently filled. No return selected the split. Confirmation source geometry was reviewed solely for this owner-authorized stage selection; its market outcomes remain unopened.

The [neutral sample](exp007_original_validation_sample.json) froze96 Development observations before official original requests:61 House /35 Senate, all eight years,44 purchases /48 sales /4 exchanges,49 printed tickers missing,7 printed/resolved differences and13 amendment-source observations. This is a validation sample, never the trading population. The corrected resolver ticker was not required to appear in an original.

Official House documents:59 HTTP200 PDFs covering61 observations. The first frozen Senate paper URL returned403; its exact body/receipt and persisted stop remain immutable. The other34 Senate source documents were not visited, not34 observed denials. No retry, alternate host, user-agent change, agreement submission, cookie bypass or search workaround followed. One inaccessible paper route does not prove all Senate documents inaccessible.

House PDF text projection is offline with isolated pypdf6.1.3 and socket access disabled;34 observations have image-only/empty text projections and remain UNKNOWN, not no-trade documents. Image-only extraction is a parser limitation, not absence of purchase evidence. General row reconciliation associates source asset/printed symbol independently of expected action/date, then compares both fields; it cannot hide a date/type disagreement by searching only for matching expected values. The first projection/association receipt is preserved separately. Original character/line/page provenance and raw hashes remain private.

| Field | Agreement | Disagreement | Unknown |
| --- | ---: | ---: | ---: |
{fields}

Of44 purchase observations, {c['sample_purchase_type_results'].get('AGREE',0)} have independently matched original transaction-type agreement; {c['sample_purchase_type_results'].get('UNKNOWN',0)} remain UNKNOWN. No purchase-type disagreement was established. **This does not certify reliability across the frame and does not prove upstream purchases are materially misclassified.** All Senate validation remains unavailable and early/image-based House evidence remains unresolved. Required cross-source original-field validation is therefore PARTIAL/BLOCKED; no silently House-only or text-only cohort replaces the declared source contract.

## Candidate accounting, timing and unopened gates

Development raw purchase trade records: **{p['purchase_trade_records']:,}**. Explicit stock-code/label candidates: **{p['source_stock_type_candidates']:,}**; printed ticker present **{p['printed_ticker_present_in_stock_candidates']:,}**, resolved ticker present **{p['resolved_ticker_present_in_stock_candidates']:,}**, reliable source-status candidates **{p['source_resolved_stock_candidates']:,}**, unresolved **{p['unresolved_stock_candidates']:,}**. Unknown purchase asset classes: **{p['unknown_purchase_asset_classes']:,}**. Stock labels are candidates pending common-equity/provider confirmation; no unknown asset becomes equity and no current ticker is projected backward. These counts precede version/identity/calendar/aggregation certification and are not independent trading-event counts.

Upstream `resolutionStatus=printed` normally leaves `resolvedTicker` null. That retains the printed symbol as an unchanged source candidate; `resolved` uses the separate resolver field. Both fields/status/reason remain intact and null is never relabelled equal or different. The initial diagnostic summary incorrectly required a redundant resolved field for printed status; it is preserved privately by hash, with this corrected schema interpretation separately versioned before any outcomes.

| Upstream UTC availability year | Purchase trade rows | Explicit stock candidates | Source-resolved candidates |
| --- | ---: | ---: | ---: |
{years}

Information time remains **UPSTREAM_MODELED_EOD_NOT_OBSERVED_PUBLIC**. The predeclared entry is09:30 New York on the second regular NYSE session strictly after the New York date of `max(firstAvailableAt, versionAvailableAt)`, strictly later than every effective bound. Exact public availability is UNKNOWN. Half-open supersession is respected; a version superseded before its eligible entry cannot generate that entry. {c['version_guard_findings'].get('future_contributor_links_excluded',0):,} Development contributor links are later than their version bound and excluded from as-of counts, while the original arrays remain preserved. This is no claim that every upstream revision/extraction history is independently certified. No real calendar/execution eligibility view was activated.

Future event aggregation remains one stable security/eligible-entry date, unweighted by disclosure/member counts, retaining lineage. No95% rule over all disclosures was imposed. The estimand is explicitly conditional on source-resolved, provider-confirmed common-equity purchases; it cannot claim unresolved disclosures. Provider/path coverage and the final unique event count are **NOT_MEASURED**, not0% market-provider success. Original validation failed upstream; no provider, price/session inspection, actual-event aggregation, inference candidate, calibration, power, Proof or scientific freeze ran. The SPY paired20-session hypothesis,10bps/side cost,0.50percentage-point threshold, positive95% lower endpoint and8-real-evaluation ceiling remain predeclared; no real performance evaluation consumed the ceiling.

## Verification, reproduction and stop

New scientific source starts: **{c['total_scientific_source_starts']}**: snapshot78 (39 pinned files and39 publisher-declared redirects), original60 (59 House PDFs and one Senate403). Three prior Parquet cache hits are separate. HTTP{json.dumps(c['HTTP_statuses'],sort_keys=True)}; retries0; source browser calls0; market/identity/Nexus/Aurora/purchases/upgrades0. Exact signed redirect URLs remain private; tracked hashes/timestamps document provenance without publishing tokens. Account-wide debit/usage is UNKNOWN. Local EDGAR/Tiingo credentials were never needed, exposed or committed.

Validation: {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped. [Validation receipt](exp007_validation.json). Research pins are unchanged. [Isolated PDF lock](exp007_pdf_requirements.lock) and [BSD3 dependency/notice hashes](exp007_pdf_parser_inventory.json) reproduce the offline helper. Public report checks require tracked summaries; private audit requires ignored original bodies, pinned Parquet, projections and baseline inventory and makes no source request.

```sh
python -m src.research.congress_sprint_report --check
python -m src.research.congress_sprint_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Recreate the source-only PDF helper with `python -m venv .research/exp007/pdf-env` and that interpreter's `pip install --require-hashes -r docs/acceleration/exp007_pdf_requirements.lock`. Acquisition commands require explicit `--execute`; stopped channels are never routine reproduction. Public CI does not import pypdf or read private bodies. Legacy EXP001 tests use already-opened records only for regression.

**Stopped at the mandatory original-source validation gate under owner section24.** No spec/freeze SHA, Development effect/interval/p-value or materiality verdict exists. EXP007 remains proposed, unregistered and unfrozen. Performance evaluations and confirmation outcome accesses are **0**. EXP002–EXP006 were not reopened; EXP004 stays paused, EXP005/EXP006 abandoned and absent. No paid provider, SEC identity rescue, other repository audit, Phase4B, optimization or paper/live action occurred. This is a source-validation limitation, not an economic test of congressional purchases or a claim of alpha.
'''
    import re
    text=re.sub(r'\b(Development|confirmation|contiguous|chronological|froze|observations|House|Senate|purchases|sales|exchanges|missing|differences|and|Of|entry|paired|positive|section|Phase|files|incomplete|prior|snapshot|original|HTTP|retries|calls|upgrades|Stock|stock|No)(?=\d)',r'\1 ',text)
    text=text.replace('all42','all 42').replace('the contiguous2014','the contiguous 2014').replace('one Senate403','one Senate 403').replace('not34','not 34').replace('a text-only','a text-only')
    text=re.sub(r'(?<=\d)(?=bps|percentage)', ' ',text).replace('pypdf6.1.3','pypdf 6.1.3').replace('BSD3','BSD-3-Clause')
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('EXP007 report differs')
    else:REPORT.write_bytes(text.encode())
    return {'status':c['status'],'registered':False,'confirmation_outcome_accesses':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.build:print(build()['status'])
    if a.audit:print(audit())
    print(report(a.check))
