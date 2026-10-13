"""Offline identity gate receipt and reproducible public report."""
from collections import Counter, defaultdict
import argparse
import hashlib
import json

from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_identity import DOCS,RAW,OLD,SAMPLE,source_state,coverage,cover_observations
from src.research.item202_population import key
from src.research.item202_date_bound import envelope,second_open
from src.research.item202_availability import calendar_sessions

RECEIPT=DOCS/'exp006_identity_certificate_v001.json'
REPORT=DOCS/'exp006_identity_report.md'


def review():
    sample=json.loads(SAMPLE.read_bytes())
    records=[]; points=[]; multiple_symbols=0
    population=json.loads((OLD/'resolved_population_final.json').read_bytes())
    if digest(population['rows'])!=sample['source_population_sha256']:raise ValueError('Population changed')
    lookup={key(r):r for r in population['rows']}
    sessions=calendar_sessions(json.loads((DOCS/'exp006_calendar_certificate_v002.json').read_bytes()))
    for planned in sample['records']+sample['prior_annual_probes']:
        r=json.loads((RAW/'cover_reviews'/(digest(planned['source_key'])+'.json')).read_bytes())
        if r.get('receipt'):
            body=Archive(RAW/'SEC').read(r['receipt']['body'])
            if r['receipt']['status']==200 and cover_observations(body)!=r['fields']:raise ValueError('Original cover replay differs')
        if planned.get('probe_role'):
            if planned['filing_date']>=planned['event_filed_date']:raise ValueError('Annual probe is not prior')
            points.append({'CIK':r['CIK'],'accession':r['accession'],'fields':r['fields'],'source_sha256':r.get('receipt',{}).get('body',{}).get('sha256'),'role':'PRIOR_ANNUAL_POINT'})
            continue
        source=lookup[tuple(r['source_key'])];decision=None;timing_reason=None
        try:
            m=source.get('metadata') or {}
            decision=second_open(envelope(m.get('acceptance_representation'),r['filing_date'])['envelope_date'],sessions)
        except ValueError as e:timing_reason=str(e)
        symbols={f['value'] for f in r['fields'].get('TradingSymbol',[])}
        titles={f['value'] for f in r['fields'].get('Security12bTitle',[])}
        cik_points={f['value'].lstrip('0') for f in r['fields'].get('EntityCentralIndexKey',[])}
        multiple_symbols+=len(symbols)>1
        # All observed fields are source points. No listing start/end, stable
        # issuer-class-provider bridge or 20-session lifecycle certificate exists.
        reasons=['NO_CERTIFIED_EFFECTIVE_LISTING_SPAN','NO_CERTIFIED_STABLE_CLASS_PROVIDER_BRIDGE','NO_CERTIFIED_20_SESSION_LIFECYCLE']
        if not symbols:reasons.append('NO_INLINE_HISTORICAL_SYMBOL_POINT')
        if len(symbols)>1:reasons.append('MULTIPLE_COVER_SYMBOLS_REQUIRE_CLASS_REVIEW')
        if cik_points and source['CIK'] not in cik_points:reasons.append('LEGAL_FILER_TO_COVER_ISSUER_UNRESOLVED')
        if not decision:reasons.append('MODELED_DECISION_UNAVAILABLE')
        records.append({'source_key':r['source_key'],'CIK':r['CIK'],'filing_date':r['filing_date'],
            'decision_utc':decision,'timing_unavailable_reason':timing_reason,'status':'UNRESOLVED',
            'reasons':reasons,'dated_symbol_point_count':len(symbols),'dated_title_point_count':len(titles),
            'source_sha256':r.get('receipt',{}).get('body',{}).get('sha256')})
    put(RAW/'identity_sample_review.json',{'records':records,'records_sha256':digest(records),'prior_annual_points':points})
    provider_stats={}
    for provider in ('OpenFIGI','Tiingo'):
        reviewed=[]
        for p in sorted((RAW/'provider_reviews'/provider).glob('*.json')):
            r=json.loads(p.read_bytes());body=Archive(RAW/provider).read(r['receipt']['body'])
            if r['receipt']['status']==200 and json.loads(body)!=r['result']:raise ValueError('Provider replay changed')
            if provider=='OpenFIGI':
                data=(r['result'][0].get('data',[]) if isinstance(r['result'],list) and r['result'] else [])
                classes={x.get('shareClassFIGI') for x in data if x.get('shareClassFIGI')}
                reviewed.append({'dated_input_sha256':r['source_sha256'],'response_sha256':r['receipt']['body']['sha256'],
                    'candidate_count':len(data),'share_class_candidate_count':len(classes),'historical_span_certified':False})
            else:
                data=r['result'] if isinstance(r['result'],dict) else {}
                reviewed.append({'dated_input_sha256':r['source_sha256'],'response_sha256':r['receipt']['body']['sha256'],
                    'available_field_names':sorted(data),'returned_ticker_matches_dated_input':data.get('ticker','').upper()==r['symbol'].upper(),
                    'data_coverage_bounds_not_listing_spans':bool(data.get('startDate') or data.get('endDate')),
                    'historical_span_certified':False})
        provider_stats[provider]={'reviewed_inputs':len(reviewed),'fully_certified_spans':0,'reviewed':reviewed}
    counts={};statuses=Counter()
    for provider in ('SEC','OpenFIGI','Tiingo'):
        root=RAW/provider;reserved={p.stem for p in (root/'reservations').glob('*.json')}
        receipts={p.stem:p for p in (root/'receipts').glob('*.json')};errors={p.stem:p for p in (root/'errors').glob('*.json')}
        if reserved!=receipts.keys()|errors.keys():raise ValueError('Unreconciled source reservation')
        counts[provider]=len(reserved)
        for p in receipts.values():
            r=json.loads(p.read_bytes());Archive(root).read(r['body']);statuses[str(r['status'])]+=1
            if r['attempt']!=1:raise ValueError('Unexpected retry')
    unknown=[r for r in population['rows'] if source_state(r)=='UNKNOWN_ITEM_STATUS']
    issuer_unknown=Counter(r['CIK'] for r in unknown)
    confirmed=[r for r in population['rows'] if source_state(r)=='ITEM202_CONFIRMED']
    legacy_path=ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json'
    legacy=json.loads(legacy_path.read_bytes())
    if isinstance(legacy,dict):legacy=legacy.get('rows',[])
    sample_ciks={r['CIK'] for r in records}
    legacy_matches=[r for r in legacy if str(r.get('cik') or '').lstrip('0') in sample_ciks]
    preserved=json.loads((ROOT/'.research/item202_identity/baseline.json').read_bytes())
    required={p:h for p,h in preserved.items() if p.startswith(('experiments/','data/processed/')) or
        p.startswith('docs/acceleration/') and p not in ('docs/acceleration/master_plan.md',)}
    for p,h in required.items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('Prior artifact changed: '+p)
    c={'version':'EXP006_identity_certificate_v001','status':'HISTORICAL_IDENTITY_BLOCKED',
       'starting_head':sample['starting_head'],'sample_sha256':digest(sample),'sample_review_sha256':digest(records),
       'sample':coverage(records),'sample_unique_CIKs':len(sample_ciks),'sample_single_event_issuers':len({r['CIK'] for r in sample['records'] if r['source_unique_issuer_events']==1}),
       'sample_shared_accession_keys':sum(r['shared_accession'] for r in sample['records']),
       'sample_dated_symbol_points':sum(r['dated_symbol_point_count']>0 for r in records),'sample_multiple_cover_symbols':multiple_symbols,
       'prior_annual_cover_probes':len(points),'prior_annual_symbol_points':sum(bool(p['fields'].get('TradingSymbol')) for p in points),
       'sample_reason_counts':dict(Counter(reason for r in records for reason in r['reasons'])),
       'routes_evaluated':['SEC_EVENT_AND_PRIOR_ANNUAL_COVERS','SEC_DATED_SYMBOLS_PLUS_OPENFIGI','CONFIGURED_TIINGO_METADATA'],
       'selected_route':None,'issuer_span_scaling_run':False,'governing_threshold_percent':95,
       'provider_reviews':provider_stats,'legacy_EXP002_matching_rows':len(legacy_matches),'legacy_EXP002_matching_sample_CIKs':len({str(r['cik']).lstrip('0') for r in legacy_matches}),
       'legacy_status':'DISCOVERY_ONLY_NOT_INDEPENDENTLY_CERTIFIED','legacy_sha256':hashlib.sha256(legacy_path.read_bytes()).hexdigest(),
       'full_population':{'source_Item202_keys':len(confirmed),'legal_filer_accession_pairs':len({(r['CIK'],r['accession']) for r in confirmed}),
          'accessions':len({r['accession'] for r in confirmed}),'legal_filer_CIKs':len({r['CIK'] for r in confirmed}),
          'certified_event_bindings':0,'uncertified_source_keys_retained':len(confirmed),'certified_coverage_percent':0,
          'unresolved_keys_by_year':dict(sorted(Counter(r['filing_date'][:4] for r in confirmed).items())),
          'full_population_route_test_run':False,'ambiguous_class_count':None,'rename_count':None,'ended_class_count':None,'terminal_required_count':None,
          'complete_terminal_paths':0,'unresolved_issuer_population_not_filtered':True},
       'missingness':{'unknown_source_keys':len(unknown),'unknown_accessions':len({r['accession'] for r in unknown}),
          'years':dict(sorted(Counter(r['filing_date'][:4] for r in unknown).items())),
          'unique_legal_filer_CIKs':len(issuer_unknown),'largest_issuer_unknown_keys':max(issuer_unknown.values()),
          'unknown_identity_lifecycle_coverage':'UNMEASURED','unknowns_in_event_or_control_pools':0},
       'request_starts':counts,'HTTP_statuses':dict(statuses),'retries':0,'market_price_requests':0,
       'FMP_status':'UNCONFIGURED_NOT_QUERIED','Nexus_requests':0,'performance_evaluations':0,'confirmation_accesses':0,
       'next_gates':'PROVIDER_PRICE_CERTIFICATION_MATCHING_INFERENCE_POWER_FREEZE_DEVELOPMENT_NOT_RUN_UPSTREAM_IDENTITY_STOP',
       'preserved_artifact_hashes':required,'account_wide_debit':'UNKNOWN','purchase_or_upgrade':False}
    put(RECEIPT,c)
    return c


def report(check=False):
    c=json.loads(RECEIPT.read_bytes());s=c['sample'];p=c['full_population'];u=c['missingness']
    vpath=DOCS/'exp006_identity_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    table='\n'.join(f"| {year} | {row['denominator']} | {row['fully_resolved']} | {row['coverage_percent']:.1f}% |" for year,row in s['by_year'].items())
    text=f'''# EXP006: source missingness accepted; historical identity stop

**HISTORICAL_IDENTITY_BLOCKED. EXP006 remains absent and unfrozen.** Starting HEAD `{c['starting_head']}`. The [owner instruction](owner_item202_identity_2026-10-13.md) accepted explicit source missingness and authorized automatic identity closure. The source unknowns no longer impose a zero-missingness gate. All three bounded identity routes were tested; none supplies the required dated class/provider/listing and 20-session lifecycle certificate. No route was selected or scaled.

## Source contract and correction

The [missingness contract](exp006_source_missingness_contract_v001.json) retains {p['source_Item202_keys']:,} known original Item 2.02 source keys, {p['legal_filer_accession_pairs']:,} legal-filer/accession pairs, {p['accessions']:,} accessions and {p['legal_filer_CIKs']:,} legal-filer CIKs. These are source candidates, not independently aggregated trading events. Non-Item keys remain 318,749; amendments remain 11,944 version-only keys. The estimand is restricted to **source-resolved original Item 2.02 events** in the reconstructed daily/quarterly observation union, not every legally required filing or an untouched contemporaneous database.

All {u['unknown_source_keys']} unknown original keys / {u['unknown_accessions']} accessions remain UNKNOWN_ITEM_STATUS and are excluded symmetrically from event and control pools. Years: 2015=9, 2016=21, 2017=10, 2018=8, 2019=3, 2020=62. Their key count is 0.1041% of known Item source keys; this is not a certified missing-trade rate. There are {u['unique_legal_filer_CIKs']} legal filers in the unknown set, with at most {u['largest_issuer_unknown_keys']} unknown keys per filer. Identity/lifecycle concentration remains unmeasured; no source recovery campaign was launched. The pre-performance sensitivity requirements remain mandatory if research advances.

The [aggregate correction](exp006_population_duplicate_correction_v001.json) fixes a prior software defect: absent-key defaultdict lookups enlarged both lookup maps during union traversal. Correct equivalent repeated observations are **111 daily and 0 quarterly**, replacing the historical reported -390 / -672. The 439,338 union keys, difference hashes, classifications and 113 unknowns are unchanged. Earlier reports and receipts retain their original bytes; their two duplicate aggregates are superseded by this separate correction. Regression tests now cover disjoint and partially overlapping populations.

## Identity feasibility

The [pushed source-only sample](exp006_identity_sample_v001.json) contains {s['denominator']} confirmed-membership candidates, ten per year/quarter, across {c['sample_unique_CIKs']} legal filers. It includes {c['sample_single_event_issuers']} single-event issuers and {c['sample_shared_accession_keys']} shared-accession source keys. Selection uses only source keys and filing-frequency/cofiler strata, with deterministic hash order; no prices, fame, current ticker or survival filter. Metadata membership remains subject to the earlier sampled primary semantic certificate. The sample was pushed before dispatch; [dated-symbol provider inputs](exp006_identity_provider_inputs_v001.json) were separately pushed before vendor queries.

| Route | Acquired evidence | Certification limit |
| --- | --- | --- |
| SEC primary | {s['denominator']} original event covers plus {c['prior_annual_cover_probes']} nearest-prior annual covers; {c['sample_dated_symbol_points']} event Inline symbol points and {c['prior_annual_symbol_points']} annual symbol points | Cover observations establish dated points, not complete effective listing spans, stable class/provider bridges or lifecycle paths. Missing Inline fields do not prove no historically listed equity. |
| SEC + OpenFIGI | {c['provider_reviews']['OpenFIGI']['reviewed_inputs']} distinct dated-symbol queries; all candidate classes retained privately | Current identifiers do not date their validity. No first-match choice, issuer-to-class promotion or current-ticker substitution. |
| Configured provider metadata | {c['provider_reviews']['Tiingo']['reviewed_inputs']} Tiingo metadata queries; zero prices; FMP unconfigured | Returned data-history start/end fields are not listing-effective boundaries or terminal consideration. No certified stable class span follows. |

Fully resolved sample events: **{s['fully_resolved']}/{s['denominator']} ({s['coverage_percent']:.1f}%)**, below the unchanged 95% standard. {s['unresolved']} are unresolved; {s['ambiguous']} have certified ambiguous-resolution status. Multiple cover symbols ({c['sample_multiple_cover_symbols']}) are a source-review warning, not a certified count of multiple eligible common classes. No sample row is dropped.

| Filed year | Sample candidates | Fully resolved | Coverage |
| --- | ---: | ---: | ---: |
{table}

The full source population has **0 certified event bindings / {p['source_Item202_keys']:,} retained source keys** because no route qualified for scaling. This is the certificate inventory, not an extrapolated failure probability from the sample or proof that every issuer is unresolvable. Per-issuer/per-year uncertified key accounting remains in the canonical certificate. Full-population multiple-class, renamed, ended and terminal-required counts remain UNKNOWN; their denominators were not certified. Complete terminal paths remain zero. A disappeared security is never disqualified by present survival or silently assigned zero value.

The local EXP002 discovery artifact overlaps {c['legacy_EXP002_matching_sample_CIKs']} sample legal filers ({c['legacy_EXP002_matching_rows']} rows). Its clipped spans, incomplete venue/type evidence and prior underfilled source universe were not independently recertified. It remains DISCOVERY_ONLY; its current canonical-symbol field was not used. No Nexus request occurred.

## Verification and stop

Source starts: SEC {c['request_starts']['SEC']}, OpenFIGI {c['request_starts']['OpenFIGI']}, Tiingo {c['request_starts']['Tiingo']}; retries 0. Original bodies, full vendor payloads and redacted-contact receipts remain immutable and ignored. HTTP outcomes: {json.dumps(c['HTTP_statuses'],sort_keys=True)}. One worker enforces SEC spacing and exact routes, conservative OpenFIGI pacing, and persisted Tiingo request quotas. Current metadata retrieval is historical reconstruction, not pre-event information. No purchase/upgrade; account-wide usage is UNKNOWN.

Validation: {v.get('local_tests_passed','pending')} local tests; {v.get('public_tests_passed','pending')} public tests; {v.get('tests_skipped','pending')} skipped. [Receipt](exp006_identity_validation.json). Public report regeneration uses tracked receipts only; audit reads ignored archived evidence and makes no network requests.

```sh
python -m src.research.item202_identity_report --check
python -m src.research.item202_identity_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

The passed v003 date policy, earlier classification/source receipts, all frozen experiments and prior processed results remain unchanged. EXP004 stays paused; EXP005 abandoned/absent; EXP006 absent. Market price certification, matching, inference/calibration/power, Proof, freeze and Development did not run after the identity gate failed. Performance evaluations and confirmation accesses are **0**; the 12-evaluation ceiling is unchanged. No Aurora, Nexus, optimizer, paper/live action or new phase occurred.

**Stopped under owner section 15 at HISTORICAL_IDENTITY_BLOCKED.** The concrete missing capability is independently dated common-class/listing/provider spans with lifecycle support. No additional planning approval was requested and no downstream gate was weakened to manufacture a freeze.
'''
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('Identity report differs')
    else:REPORT.write_bytes(text.encode())
    return {'status':c['status'],'fully_resolved':s['fully_resolved'],'denominator':s['denominator'],'confirmation_accesses':0}


def audit():
    c=json.loads(RECEIPT.read_bytes())
    for p,h in c['preserved_artifact_hashes'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('Prior artifact changed: '+p)
    sample=json.loads(SAMPLE.read_bytes())
    if digest(sample)!=c['sample_sha256']:raise ValueError('Sample changed')
    r=json.loads((RAW/'identity_sample_review.json').read_bytes())
    if digest(r['records'])!=c['sample_review_sha256']:raise ValueError('Identity review changed')
    # Re-running review verifies all originals, vendor payloads and source keys.
    if review()!=c:raise ValueError('Certificate replay differs')
    return {'status':'PASS','sample_events_replayed':len(r['records']),'confirmation_accesses':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--review',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.review:print(review()['status'])
    if a.audit:print(audit())
    print(report(a.check))
