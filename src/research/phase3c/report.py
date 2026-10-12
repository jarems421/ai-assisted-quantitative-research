"""Reports from a redacted canonical source review; never strategy performance."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from src.research.phase3c.sources import RAW, DOCS
from src.research.phase3c.registry import registry
from src.research.sec_pilot.parsing import canonical, digest


def public_summary(private):
    chains = private['chains']; cases = private['cases']
    stats = {'candidate_issuers': len(chains), 'three_originals': sum(r['selected_originals'] == 3 for r in chains),
             'three_offline_parsed': sum(r['offline_parsed'] == 3 for r in chains),
             'exact_concept_three': sum(r['exact_concept_three'] for r in chains),
             'numeric_comparability_pass': sum(r['result'].get('numeric_comparability') == 'PASS' for r in chains),
             'fully_certified': sum(r['result']['status'] == 'CERTIFIED_CHAIN' for r in chains)}
    denom = stats['three_originals']
    stats['denominator_rule'] = 'All frozen candidates with three discovered original annual10Ks; includes parser/context failures, never successful-download-only'
    stats['certified_fraction'] = stats['fully_certified'] / denom if denom else None
    stats['feasibility_band'] = ('GREEN' if stats['certified_fraction'] >= .8 else 'AMBER' if stats['certified_fraction'] >= .5 else 'RED') if denom else 'UNRESOLVED'
    identities = [{'case_key': r['case_key'], 'status': r['status'], 'figi_status': r['figi_status'],
                   'figi_response_sha256': r['figi_response_sha256'], 'cover_observation_count': len(r['historical_cover_observations']),
                   'class_point_identified': r['class_point_identified'], 'ticker_exchange_point_identified': r['ticker_exchange_point_identified'],
                   'single_share_class_identifier_candidate': r['single_share_class_identifier_candidate'],
                   'partial_event_accession': r['partial_event_accession'],
                   'span_status': r['span_status'], 'terminal_status': r['terminal_status']} for r in private['identity']]
    market = [{'case_key': r['case_key'], 'source_status': r['source_status'],
               'metadata_received': bool(r['metadata']), 'qa': ({k:v for k,v in r['qa'].items() if k not in ('missing_sessions', 'extra_sessions')} |
                    {'unexplained_diagnostic_missing_count': len(r['qa']['missing_sessions']), 'extra_session_count': len(r['qa']['extra_sessions'])}) if r['qa'] else None,
               'source_hashes': r['source_hashes'],
               'listing_expected_session_status': r['listing_expected_session_status'], 'certified': False} for r in private['market']]
    calibrations = [r for r in private['calibration'] if r['protocol'] == 'phase3c_synthetic_calibration_v002']
    gates = {'FREE_SOURCE_STACK': 'PARTIAL', 'REVENUE_TRIPLE_SEMANTICS': 'PARTIAL', 'SEC_SOURCE_COVERAGE': 'PARTIAL',
             'HISTORICAL_SECURITY_IDENTITY': 'PARTIAL', 'MARKET_DATA_COVERAGE': 'PARTIAL',
             'CORPORATE_ACTION_LIFECYCLE': 'PARTIAL', 'TERMINAL_VALUE_EVIDENCE': 'BLOCKED',
             'PUBLIC_ELIGIBILITY_POLICY': 'READY_FOR_OWNER_REVIEW',
             'INFERENCE_IMPLEMENTATION': 'BLOCKED', 'HISTORICAL_UNIVERSE_FEASIBILITY': 'BLOCKED',
             'NEXUS_EXECUTION': 'BLOCKED', 'LOCAL_EXECUTION_ROUTE': 'NOT_IMPLEMENTED', 'EXP005_FREEZE_READINESS': 'NOT_READY'}
    market_metrics = {'price_http200_responses': sum(r['qa'] is not None for r in market),
                     'nonempty_responses': sum(r['qa'] is not None and r['qa']['received_sessions']>0 for r in market),
                     'diagnostic_full_calendar_passes': sum(r['qa'] is not None and r['qa']['session_status']=='PASS' for r in market),
                     'received_rows': sum(r['qa']['received_sessions'] for r in market if r['qa']),
                     'invalid_rows': sum(r['qa']['invalid_rows'] for r in market if r['qa']),
                     'duplicate_sessions': sum(r['qa']['duplicate_sessions'] for r in market if r['qa']),
                     'split_events': sum(r['qa']['split_event_rows'] for r in market if r['qa']),
                     'split_probe_passed': sum(r['qa']['split_reconciliation_candidates_passed'] for r in market if r['qa']),
                     'dividend_events': sum(r['qa']['dividend_event_rows'] for r in market if r['qa']),
                     'original_pre_event_dividend_probe_passed': sum(r['qa']['dividend_reconciliation_candidates_passed'] for r in market if r['qa']),
                     'separate_cash_exdate_internal_consistency_passed': sum(r['qa']['cash_exdate_price_internal_consistency_passed'] for r in market if r['qa'])}
    return {'version': 'phase3c_public_evidence_v001', 'baseline_git_sha': 'ec0c1e9', 'as_of': '2026-10-12',
            'cohort_sha256': private['cohort_sha256'], 'cases': cases, 'revenue_metrics': stats, 'chains': chains,
            'identity': identities, 'identity_status_counts': dict(Counter(r['status'] for r in identities)),
            'identity_metrics': {'class_point_identified_count': sum(r['class_point_identified'] for r in identities),
                'single_identifier_candidate_count': sum(r['single_share_class_identifier_candidate'] for r in identities),
                'ticker_exchange_point_count': sum(r['ticker_exchange_point_identified'] for r in identities),
                'sufficient_span_count': 0, 'contradiction_or_multi_identifier_count': sum(r['status']=='AMBIGUOUS' for r in identities),
                'confirmed_ended_denominator': None, 'terminal_certified_count': 0},
            'merger_primary_evidence': [{'issuer_cik': r['issuer_cik'], 'accession': r.get('accession'), 'status': r['status'],
                 'source_sha256': r.get('sources',{}).get('primary',{}).get('body',{}).get('sha256'),
                 'url': r.get('sources',{}).get('primary',{}).get('url')} for r in private.get('merger_primary_receipts',[])],
            'market': market, 'market_metrics': market_metrics, 'timing': private['timing'], 'policy': private['policy'], 'policy_sha256': private['policy_sha256'],
            'calibration': calibrations, 'filing_year_counts': private['filing_year_counts'], 'taxonomy_versions': private['taxonomy_versions'],
            'request_counts': private['request_counts'], 'body_receipts': private['body_receipts'],
            'completeness_summary': {k:v for k,v in private['completeness'].items() if k != 'rows'}, 'gates': gates,
            'nexus_calls': 0, 'strategy_performance_computed': False, 'real_signal_series_computed': False,
            'market_requests_after_freeze_verified': private['market_requests_after_freeze_verified'],
            'prior_stop_retained': True, 'oversized_initial_prefix_retention_gap': True}


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(v).replace('|', '/') for v in row) + ' |' for row in rows])


def render(s):
    metrics = s['revenue_metrics']; timing_counts = Counter(r['status'] for r in s['timing'])
    requests = ', '.join(f'{k}: {v}' for k,v in sorted(s['request_counts'].items()))
    chain_table = table(['Case', 'Originals / parsed', 'Exact concept in three', 'Outcome'],
                        [(r['case_key'], f"{r['selected_originals']} / {r['offline_parsed']}", r['exact_concept_three'], r['result']['status']) for r in s['chains']])
    identities = table(['Case', 'Identifier result', 'Dated covers', 'Identity / terminal'],
                       [(r['case_key'], r['figi_status'], r['cover_observation_count'], r['status'] + ' / ' + r['terminal_status']) for r in s['identity']])
    market = table(['Case', 'Metadata', 'Received / diagnostic expected sessions', 'Raw/session status', 'Listing span'],
                   [(r['case_key'], r['metadata_received'], f"{r['qa']['received_sessions']} / {r['qa']['expected_sessions']}" if r['qa'] else 'Unavailable',
                     r['qa']['session_status'] if r['qa'] else 'UNRESOLVED', r['listing_expected_session_status']) for r in s['market']])
    cal = s['calibration'][0] if s['calibration'] else None
    cal_table = table(['Synthetic family', 'Raw null/effect rejection', 'Wilson 95%', '126 / 504 block rejection', 'Sample gate pass'],
                      [(r['family'], f"{100*r['rejection_fraction_raw_alpha05']:.1f}%", f"{r['wilson95'][0]:.3f}–{r['wilson95'][1]:.3f}",
                        f"{r['block_rejection_fractions']['126']:.3f} / {r['block_rejection_fractions']['504']:.3f}", f"{r['sample_gate_pass_fraction']:.3f}") for r in cal['families']]) if cal else 'No calibration receipt.'
    gate_order = ('FREE_SOURCE_STACK','REVENUE_TRIPLE_SEMANTICS','SEC_SOURCE_COVERAGE','HISTORICAL_SECURITY_IDENTITY',
                  'MARKET_DATA_COVERAGE','CORPORATE_ACTION_LIFECYCLE','TERMINAL_VALUE_EVIDENCE','PUBLIC_ELIGIBILITY_POLICY',
                  'INFERENCE_IMPLEMENTATION','HISTORICAL_UNIVERSE_FEASIBILITY','NEXUS_EXECUTION','LOCAL_EXECUTION_ROUTE','EXP005_FREEZE_READINESS')
    gate_table = table(['Gate', 'Verdict'], [(k,s['gates'][k]) for k in gate_order])
    id_metrics = s['identity_metrics']
    merger_table = table(['Issuer CIK', 'Primary accession', 'Evidence disposition'],
                         [(r['issuer_cik'], r['accession'], 'PARTIAL_CLASS_POSITION_TERMS_UNCERTIFIED') for r in s['merger_primary_evidence']])
    readme = f'''# Phase 3C: free source certification pilot

**PARTIAL free source stack; EXP005 freeze NOT_READY.** As of2026-10-12. The metadata-only cohort froze{s['cases']} unique case keys before price acquisition, hash `{s['cohort_sha256']}`. Thirty issuer revenue candidates and thirty lifecycle stress targets are retained, including failures. Named lifecycle categories remain stress targets until independently verified; the cohort is a deliberately selected feasibility frame, not a representative US equity sample or proof of30 certified complex histories.

The exact annual revenue contract has{metrics['fully_certified']} fully certified triples of{metrics['three_originals']} discovered three-original candidates ({metrics['feasibility_band']} under the fixed source-feasibility rule). Parser and accounting/perimeter uncertainty contribute to this low certified fraction; it does **not** prove revenue acceleration has no alpha or that every rejected concept is economically unsuitable. No real acceleration, momentum or portfolio series was calculated.

Only{metrics['exact_concept_three']}/{metrics['three_originals']} three-original candidates contain the exact concept throughout;{metrics['numeric_comparability_pass']} pass numeric comparability. That concept ceiling alone is below the80% source-feasibility target for this selected vintage/frame, even before accounting/perimeter review. Do not broaden the tag or move dates automatically.

{gate_table}

## Evidence and limitations

- [Revenue-chain QA](phase3c_revenue_chain_qa.md): original accession/element reconciliation, missingness and unchanged single concept.
- [Identity and lifecycle](phase3c_identity_lifecycle.md): current OpenFIGI candidates cannot certify historical listing intervals or terminal consideration.
- [Market-data QA](phase3c_market_data_qa.md): bounded raw/action/session checks; vendor price/metadata bodies remain private.
- [Availability review](phase3c_availability_review.md): population clock probe and separate unapproved policy packet.
- [Synthetic calibration](phase3c_inference_calibration.md): original confirmatory method fails the predeclared calibration gate.
- [Execution routes](phase3c_execution_route.md), [scale plan](phase3c_scale_plan.md), [gate review](phase3c_gate_review.md), [source registry](phase3c_source_registry.json) and [canonical redacted evidence](phase3c_evidence.json).

Recorded source request starts: {requests}. FMP API calls0; Orbis logins/queries0; Nexus calls0. Browser official-documentation review is separate from these application source ledgers. Included source access incurred no purchase/upgrade; account-wide debit/usage and entitlement are not independently observed.

## Preservation and stop

Previous Phase1/2/3A/3B evidence and experiment freezes remain unchanged. EXP004 remains operationally paused; no EXP005 directory, registration, trial or state exists. No sealed stage, strategy performance, optimization, paper/live operation or next phase was opened. Original bodies and source-error receipts remain ignored. The initial Intel oversized full-submission attempt has an explicit prefix-retention gap; the collector was corrected to retain future oversized prefixes. Its original stop remains, the request is forbidden from retry, and a reviewed compact original-document route preserves all earlier receipts. This limitation is not erased by later successful documents.

Stop after Phase3C. Next owner review must address revenue comparability certification, dated identity/terminal evidence, proposed availability and **pre-performance inference revision**, then separately authorize any bounded next source work. No full acquisition or EXP005 is authorized by this report.
'''
    rev = f'''# Phase 3C: original annual revenue-chain QA

**Source feasibility {metrics['feasibility_band']}; semantics PARTIAL.** No real signal formula was evaluated. Fixed denominator: {metrics['denominator_rule']}. Candidate issuers{metrics['candidate_issuers']}; three originals{metrics['three_originals']}; three offline parses{metrics['three_offline_parsed']}; exact concept in all three{metrics['exact_concept_three']}; numeric comparability passes{metrics['numeric_comparability_pass']}; accounting/perimeter-certified triples{metrics['fully_certified']}.

{chain_table}

Original revenue facts use the exact US-GAAP concept `RevenueFromContractWithCustomerExcludingAssessedTax`, annual350–380day duration, same issuer, no explicit/typed dimensions, USD and positive finite values. Pinned EdgarTools5.62.0 enumerates original instance elements offline; concept/namespace/context/unit/value counts reconcile exactly. Primary Inline XBRL values independently reconcile format/sign/scale, with original locators/hashes retained privately. Non-inline primary-statement reconciliation, conflicting originals and unsupported rendering stay unavailable. No issuer extension, alternate revenue concept, segment sum or pro-forma repair is selected.

Three consecutive originals retain separate accession-specific values. Later comparatives only check prior pinned values through disclosed rounding intervals; they never overwrite earlier facts. Equal numbers alone do not certify reporting-perimeter/accounting-policy compatibility. Those material review certificates remain absent, so fully certified rate is a conservative lower bound. A parsing/primary-reconciliation limitation is reported as such rather than evidence that an original filing never existed. Source-stack scalability is **not established** under this exact contract; complete certification review is required before expanding acquisition.

Filing-year counts: `{json.dumps(s['filing_year_counts'], sort_keys=True)}`. Taxonomies: {', '.join(s['taxonomy_versions'])}. Current retrieved bytes are historical reconstruction, not contemporaneous vintages. Original and derived hashes/configs are in canonical evidence and content-addressed private snapshots. Reproducing QA never fetches SEC.
'''
    identity_doc = f'''# Phase 3C: historical class and lifecycle feasibility

**PARTIAL identity; terminal values BLOCKED.** Current identifier metadata or a filing cover cannot certify a continuous historical class/listing interval. Full certified identity rate0/{s['cases']}; terminal-event certified rate0/{s['cases']}. These are deliberately strict evidence outcomes, not claims that all issuers lack tradable histories. Ended-listing denominators cannot be certified from the planned category labels alone.

Distinct pilot denominators are{s['cases']} cases for each point metric: exact class point identified{id_metrics['class_point_identified_count']}; single share-class identifier candidate{id_metrics['single_identifier_candidate_count']}; historical ticker/exchange point identified{id_metrics['ticker_exchange_point_count']}; sufficient interval evidence{id_metrics['sufficient_span_count']}; ambiguous/multiple identifier result{id_metrics['contradiction_or_multi_identifier_count']}. Identifier candidates are not dated class bridges. Ending-resolution percentage is unavailable while the primary ending denominator remains uncertified, rather than assuming planned labels are observed endings.

{identities}

Issuer CIK, submitting CIK, accession, ticker, exact class, share-class FIGI, composite FIGI, exchange and effective span remain distinct. Multiple OpenFIGI share-class candidates remain AMBIGUOUS; no first-match choice or current ticker projected backward. Unlisted equity inclusion is explicit. Source hashes remain in canonical evidence; full vendor candidate metadata and original cover locators are private. AAPL/FB Phase3A provisional rows remain unchanged.

CIK submissions/dated cover observations establish discovery/point evidence only. A Form25/8-A header is not by itself common-stock ending/consideration proof, and an unrelated preferred-stock registration cannot certify the cohort class. Current pilot lifecycle evidence lacks independently reconciled exact position/terminal terms. Cash/stock mergers, spinoffs, bankruptcy/cancellation, class changes and exchange transfers require separate dated primary-source terms. Missing recovery is never0, perpetual last price or silent deletion. FMP cross-check unavailable without a local key/confirmed free endpoint; no Orbis automation.

Historical identity stack does not meet the95% fully resolved requirement. No difficult case was dropped, replaced or relabeled eligible to improve the rate. See [manual checks](phase3c_orbis_manual_checks.md) for specific unresolved questions.

## Primary event feasibility

{merger_table}

Ten bounded merger completion8-Ks were selected by fixed metadata event-date hypotheses and nearest Item2.01 within14days, then archived/reviewed offline. The hypotheses themselves were not treated as observed event dates. For example, original TWTR/ATVI/TIF/WFM documents disclose common-stock cash consideration, while XLNX describes stock conversion and fractional-share treatment. Those documents demonstrate that free primary consideration evidence exists; they do not yet reconcile exact stable-class bindings, exceptions, settlement timing or every position transition. Event-document presence remains PARTIAL, not full terminal certification. Source URLs/hashes are in canonical evidence. CBS as a surviving issuer must not be mislabeled a terminated class merely because it filed a merger completion report.
'''
    market_doc = f'''# Phase 3C: market-source QA

**PARTIAL observations; zero cases fully certified for historical NAV.** All requests are tied to the frozen cohort and fixed2019–2020 range. No raw/adjusted price performance, signal return, strategy correlation, Sharpe, drawdown or alpha was calculated. Provider bodies/metadata remain ignored under internal-use restrictions.

Aggregate source QA: `{json.dumps(s['market_metrics'],sort_keys=True)}`. HTTP200, nonempty response, diagnostic full-calendar match and certified listed-history completeness are distinct. Nine empty price responses do not become observed no-trading states. Split-only factor checks match the source's stated split multipliers. The original unverified pre-event cash-adjustment probe is retained with its failures; a separately labelled ex-date cash/price probe tests the CRSP convention referenced by Tiingo. Both use only adjustment factors, not security/portfolio returns. An internal same-vendor match cannot certify dividends independently. The [Tiingo ex-date definition](https://www.tiingo.com/documentation/corporate-actions/dividends) and publisher-indexed CRSP descriptions motivate the second probe, but the linked CRSP guide's live retrieval failed; no full current methodology certificate is claimed. Same-day split/distribution basis, payment timing and terminal transitions remain unresolved. No extra corporate-action API entitlement was assumed or queried.

{market}

The505-session full-range calendar is a **diagnostic upper frame**, not expected listing sessions for an uncertified ended/name-changed class. Required expected sessions must be recomputed from independently evidenced listing spans; API silence/start/end coverage cannot certify a holiday or delisting. Counts are raw response/session QA only. Rows require finite positive rawOHLC, coherent low/high, nonnegative volume/dividend and positive split factor; duplicates/missing/extra sessions remain explicit. Current adjusted-to-raw/action checks are candidates under a declared CRSP-like formula, not independent corporate-action or terminal certificates.

Even successful split/dividend field retrieval does not certify stock-dividend basis, merger consideration, bankruptcy recovery or position transitions. No portfolio can ever omit a held case or silently lose NAV; the95% source-feasibility target does not weaken that100% held-path requirement. The cohort-wide fully source-resolved market/identity/lifecycle rate is0/{s['cases']}. Free-tier account entitlement and other account usage are unknown; local starts obey the published50/hour bound and request/byte ceilings, with no upgrade or purchase.
'''
    avail = f'''# Phase 3C: availability policy owner-review packet

**READY_FOR_OWNER_REVIEW packet; NOT APPROVED.** Existing v001 and all original timestamp evidence remain unchanged. Exact first-public availability stays UNKNOWN. Proposed separately versioned pilot-only policy hash: `{s['policy_sha256']}`. Canonical definition is the `policy` object in [evidence](phase3c_evidence.json).

Rule:09:30America/New_York on the second session strictly after the later of official filing date and the acceptance civil date under each plausible UTC interpretation; all candidate opens must equal the raw-rule open and occur after every candidate instant. One complete later session buffer is a modeled assumption, never an observed public timestamp or guaranteed website posting bound. The proposed pilot scope covers2015–2021; it does not certify Phase3B's2021–2032 calendar. Acceptance remains PARTIAL when EST/seasonal ET differ.

Clock probe outcomes over acquired revenue originals: `{json.dumps(dict(timing_counts), sort_keys=True)}`. Every selected original gets a timing disposition, including missing header/calendar failures; undiscovered required originals remain unavailable. Near-midnight cases{sum(r.get('near_midnight', False) for r in s['timing'])}; weekend acceptance{sum(r.get('weekend', False) for r in s['timing'])}; weekday calendar-holiday acceptance{sum(r.get('weekday_holiday', False) for r in s['timing'])}; non-session acceptance{sum(r.get('non_session_date', False) for r in s['timing'])}; offset change across buffer{sum(r.get('dst_transition_week', False) for r in s['timing'])}. These are classifications under the pinned offline calendar, not independent exchange certification. Synthetic near-midnight/weekend/holiday/DST failures supplement observed coverage without claiming those real cases occurred.

The archived SEC PDS/FAQ interpretation evidence remains the Phase3A authoritative basis; no additional SEC timing claim resolved October DST behavior. New transport receipts preserve actual current retrieval; those clocks are not backdated. Fail closed on missing/contradictory dates, non-invariance, unsupported calendar, uncertified contributor/class or contrary public evidence.

Exact later owner action: review this policy object/hash, candidate instant evidence and contributor snapshot hashes; explicitly approve or reject that scope and modeled uncertainty in a separate owner artifact. Approval must bind policy hash, interpretation/contributor scope and authority artifact hash. No approval writer is invoked. A reviewed source/calendar implementation would still be needed before activation. Approval does not lift EXP004 pause, certify execution or authorize EXP005.
'''
    inference = f'''# Phase 3C: synthetic inference calibration

**BLOCKED.** The predeclared Phase3B noncircular null-centered bootstrap fails the synthetic size criterion. No real market or strategy returns entered calibration. No method was replaced or tuned to rescue the outcome.

Protocolv002:200replications/family,10,000draws/replication, fixed seed3003001, two funded windows756sessions each, primary252-session blocks, fixed126/504 sensitivities; pooled-mean centering preserves window contrasts, blocks stay within windows. Null-family acceptance requires Wilson95% upper bound for raw one-sidedalpha0.05 rejection<=0.10. This protocol was privately hashed before execution. Positive/negative cases assess known effects; their rejection rate is not Type-I error. Earlier primary-only prototype receipts remain private and unchanged.

{cal_table}

Annual reporting shocks, persistent AR(1),21-day overlapping-like dependence, heteroskedasticity and offsetting window shifts exercise the proposed assumptions. Bartlett HAC lags252/504, effective-size floor20 and six annual-block equivalents are diagnostics, not a power certificate. Four declared effects use conservative missing/failed p=1 and Holm; fully correlated four-effect family rates are retained in canonical evidence, with unknown general joint calibration explicitly unresolved. Unit tests additionally reject zero variance, missing/nonfinite NAV-derived inputs, misaligned/overlapping windows, few blocks and missing family effects.

Code success is not statistical certification. Primary null rejection exceeds the predeclared allowance across several families, including IID; the sample gate/adjustment does not license replacing the primary method with a better-looking block length. Recommend a separately reviewed **pre-performance** inferential revision (for example finite-sample/studentized or longer-window design), with a new fixed synthetic calibration protocol. Do not implement/adopt that alternative automatically. Preserve this negative result and all search accounting; EXP005 cannot freeze under this inference contract.
'''
    execution = '''# Phase 3C: execution-route comparison

**Nexus BLOCKED; local route NOT_IMPLEMENTED.** No Nexus call or real/synthetic strategy execution occurred. The conditional local harness was not built because the free source pilot does not satisfy historical identity, terminal-value and inference gates. Source-quality fixtures validate fields/contracts, not a portfolio engine.

| Scientific requirement | Nexus existing evidence | Provider-independent option |
| --- | --- | --- |
| Exact requested historical identities/population | Demonstrated pruning; BLOCKED | Source denominator and dated class bridge absent |
| Rename, class distinction, ended histories | Not certified | Candidate identifiers do not certify spans |
| Splits/dividend cash and dated factors | Production lifecycle incomplete | Source fields retrievable in some cases; interpretation incomplete |
| Merger/spinoff/terminal value and positions | Not certified | Primary class-specific consideration not reconciled |
| Declared execution timing/cost/reserve | Needs scoped complete fixtures | No engine implemented; source conventions unapproved |
| Deterministic source/spec replay | Existing local receipts, incomplete route certificate | Content-addressed source QA exists, not execution |

Neither route is selected on speed or presentation. Nexus would need exhaustive point/availability/value publication and pre-filter runtime population equality under pinned engine/source/spec hashes, including renamed/ended identities and terminal transitions. Counts, selected holdings or storage acceptance are insufficient. A local engine would need the same certificates and bounded synthetic/lifecycle fixtures; availability, costs, cash/stock conversion and terminal recovery cannot be guessed. Another vendor, broad refactor or full backtester remains unauthorized. See [unchanged contract](historical_execution.md).
'''
    scale = '''# Phase 3C: conditional scale plan

**Plan only; no full backfill authorized.** Pilot does not certify a survivor-free national listing denominator. SEC filers include nonlisted/noncommon securities, OpenFIGI output is current identifier metadata, and vendor supported-ticker directories are coverage lists. None alone supplies all historical ordinary listings, classes, obligations or terminal intervals.

| Scenario, not observed population | Approximate volume |
| --- | --- |
| 3,000–6,000issuer planning range over15annual cohorts | 45,000–90,000original annuals before amendments/issuer churn |
| Four original-document requests per annual | 180,000–360,000SECstarts plus index/discovery/lifecycle/error allowance |
| Five identifier jobs/request | 600–1,200initial mapping requests, more for historical aliases/classes |
| Two market calls per security,3,000–6,000cases | 6,000–12,000Tiingo calls before lifecycle/coverage retries |
| Assumed5–25MBarchived source set/annual | 225GB–2.25TB originals; explicit assumption, not a measured population estimate |

SEC2starts/second implies25–50hours of request-start time alone, excluding bytes/retries/stop reviews. OpenFIGI conservative5jobs/request and20starts/minute implies30–60minutes for one identifier pass, not historical interval completion. Tiingo50starts/hour implies120–240quota hours;500unique symbols/month requires6–12months at this assumed breadth, and1GB/month may bind much earlier. These published free caps are not account-specific receipts; do not assume omitted account activity is zero. A pilot with zero certified intervals cannot estimate unresolved population probability; do not project its selected-frame fractions to all issuers. Actual counts/cost/duration remain unknown.

Deterministic future manifest schema: population source/vintage/hash, issuerCIK, class/stableID and dated span evidence; required fiscal periods and original/amendment accessions; exact allowlisted document URLs/hashes; per-source request plan/quotas/byte ceiling; parser/code/config hash; approved policy hash; expected calendar sessions; lifecycle/terminal requirements; explicit completeness state; idempotency/cache/stop-review keys. Enumerate the independently sourced denominator before downloads, order by stable source key/hash, retain all failed/ended cases, and checkpoint immutable receipts. Resolve scientific identity/terminal/inference blockers before proposing a concrete full manifest.

Current scope has original2018–2020 annual candidates, mostly filed2019–2021. Earliest possible triple-based decisions are after each2020annual becomes policy-eligible, often2021; this is chronology, not performance. Source breadth, exact-concept and accounting/perimeter certification are incomplete. Phase3B windows remain unchanged planning artifacts. Development2026 is incomplete,2027+windows future; the pilot calendar does not certify future closures. No date alternative is activated. Any source-only date/contract revision needs owner review before performance. Later forward paper evidence remains a separate freeze/authorization/recording milestone.

A coverage-only alternative for owner review is a bounded check of fiscal2019–2021 originals under the **same exact concept**, without approving broader acquisition now. If that separately reviewed sample established the required breadth/comparability, a planning-only warm-up2019–2021 / Development2022–2027 / Validation2028–2030 / Test2031–2033 could be reviewed. No assertion that those periods pass coverage is made; this does not solve bank/conglomerate revenue semantics, identity or inference. The present80% chain coverage target is not supported by the exact-concept count reported in [revenue QA](phase3c_revenue_chain_qa.md). No new source requests, window activation or parameter change follows this recommendation.
'''
    gates_doc = f'''# Phase 3C: final gate review

**EXP005 NOT_READY.** The source pilot and synthetic machinery are complete within the recorded evidence limitations; no economic evaluation occurred.

{gate_table}

Availability READY_FOR_OWNER_REVIEW means a hashed uncertainty packet exists, not policy approval or trading eligibility. Identity/lifecycle, concept/primary/basis reconciliation and the negative inference calibration prevent certification. Full universe feasibility remains blocked and neither engine is certified. No gate is promoted because an API accepted a request.

Required owner decisions: review the proposed modeled availability packet; decide whether to commission bounded original-statement/accounting-perimeter and effective-dated class/terminal certification; review a **new pre-performance inference design** rather than approve the failed method; only then consider a bounded acquisition/engine-certification plan. No full acquisition, source purchase, EXP005 registration/freeze, sealed stage, portfolio study or Phase4 starts automatically.

Checks and preserved baseline counts are in [validation](phase3c_validation.json). Canonical evidence/report generation uses `python -m src.research.phase3c.report --check`; offline source review uses `python -m src.research.phase3c.review` and requires ignored originals, never network. Acquisition commands are separately opted-in source mutations and are not reproduction. No personal contact/API token, university credential or private vendor/raw dataset is committed. Git delivery reports exact checkpoints/push status.

**Stopped after Phase3C.** EXP004 operational pause and all previous evidence/frozen artifacts remain intact; EXP005 absent.
'''
    orbis = '''# Optional manual identity checks

No Orbis login, scraping or export was attempted. The [university database listing](https://www.lboro.ac.uk/services/library/databases/) describes access; actual owner licence and permissible export remain unverified. Continue without it.

If the owner chooses permitted manual validation, ask specifically:

- AAPL common stock: dated NASDAQ class/listing span covering2019–2020; exact FIGI level/class and original provider evidence.
- FB ClassA: dated NASDAQ span at2019–2020 decisions, FB-to-META transition/class continuity, source/vintage/hash; distinguish ClassB.
- GOOG versus GOOGL and BRK.A versus BRK.B: class-specific stable IDs and effective listing intervals, not issuer-level current profile.
- TWTR, XLNX, CELG: exact former listing end, class, cash/stock consideration and successor identity; link dated primary merger records.
- BBBY, SHLD and HTZ: distinguish predecessor cancelled classes from later issued/reused symbols; exact recovery/cancellation terms and evidence.

Record source product/version, retrieval time, case key, source document/date/locator, permitted evidence extract/hash, effective-from/to, identifier level and contradictions. Never assume university access grants bulk/export/redistribution rights. Manual evidence supplements rather than overrides original SEC sources and must undergo separate certification.
'''
    outputs = {'phase3c_report.md': readme, 'phase3c_revenue_chain_qa.md': rev, 'phase3c_identity_lifecycle.md': identity_doc,
            'phase3c_market_data_qa.md': market_doc, 'phase3c_availability_review.md': avail,
            'phase3c_inference_calibration.md': inference, 'phase3c_execution_route.md': execution,
            'phase3c_scale_plan.md': scale, 'phase3c_gate_review.md': gates_doc, 'phase3c_orbis_manual_checks.md': orbis}
    def readable(text):
        text=re.sub(r'\b(Phase|Item|Note|ASC|ASU|seed|alpha|over|before|after|covers|of|has|froze|proof|published|window|triple|originals|parses|candidates|passes|triples|cases|acceptance|count|identified|evidence|result|rate|calls|logins|queries|Protocol|Protocolv|primary|fixed|families)(?=\d)',r'\1 ',text)
        text=re.sub(r'(?<=\d)(requests|starts|replications|draws|sessions|days|years|annuals|issuer|cases|GB|MB|TB|hours|minutes|quota|jobs|symbols|APIcalls|logins|queries|exports)\b',r' \1',text)
        return text.replace('As of2026','As of 2026').replace('annual10Ks','annual 10-Ks').replace('annual10-Ks','annual 10-Ks').replace('Protocolv002','Protocol v002')
    return {name:readable(text) for name,text in outputs.items()}


def main():
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--check', action='store_true'); p.add_argument('--from-private', action='store_true'); a = p.parse_args()
    evidence_path = DOCS/'phase3c_evidence.json'
    if a.from_private:
        files = sorted((RAW/'reviews').glob('*.json'), key=lambda p:p.stat().st_mtime)
        evidence = public_summary(json.loads(files[-1].read_bytes()))
        evidence_path.write_bytes(canonical(evidence))
        (DOCS/'phase3c_source_registry.json').write_bytes(canonical(registry()))
    evidence = json.loads(evidence_path.read_bytes())
    for name, text in render(evidence).items():
        path = DOCS/name; content = text.strip() + '\n'
        if a.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content: raise ValueError('Stale public source report: ' + name)
        else: path.write_text(content, encoding='utf-8', newline='\n')
    print('PASS canonical source-only report consistency')


if __name__ == '__main__': main()
