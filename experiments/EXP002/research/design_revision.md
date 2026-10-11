# EXP002 design revision and final pre-freeze audit

**NEEDS DESIGN REVISION. DRAFT; not frozen or executable.** See the verbatim [owner request](design_revision_authorization_20261011.md), [change ledger](design_revision_log.json), [runtime summary](revision_runtime_summary.json), [cohort coverage](cohort_summary.json), and [complete query log](coverage_query_log.json). All design changes precede candidate performance. No candidate return was calculated or ranked, and no outer Validation/Test observation was queried through Nexus.

## Primary proposal

| Component | Revised proposal | Evidence boundary |
|---|---|---|
| Universe | Effective historical listing/security-ID spans; CS common stocks; nominal unadjusted price >= $5; fixed $10m ADV on 20 distinct prior completed sessions; US exchange listings only; exclude OTC/ADR/ETF/preferred/fund/unknown types | Historical exchange vintages and compatible volume basis unresolved; explicit construction preferred over ALL_US_STOCKS |
| Market cap | Removed from primary eligibility and parameter grid | Historical share vintages/class scope not certified; diagnostic concept only |
| Momentum | 180/365 elapsed calendar days, evaluated from completed price information | Native horizons evaluated; four lagged-open samples match prior closes; all eight new horizon/calendar references match within 0.001 percentage points. Full price vintage and scheduling contract unresolved |
| Insider | One representation: distinct owner CIK among certified **open-market** nonderivative purchase disclosures; 30/90 calendar-day availability windows | P includes private purchases. No source discriminator establishes strict open-market qualification; do not silently broaden hypothesis |
| Institutional | One representation: matched-manager holder-count change between two eligible adjacent public quarter cohorts; proposed fixed 60-day buffer | Source cohort coverage supports consideration; native NetHolderChange is not this reconstructed definition |
| Cadence/weights | Monthly only, first tradable session; equal signal ranks and security weights; 95% deployment | Weekly is robustness only; exact monthly scheduling needs implementation audit |
| Liquidity | $10m eligibility, $25m robustness only | No liquidity optimization. Existing unadjusted-price-times-volume diagnostic counts are not certified primary eligibility |

Retain later-delisted histories. Unsupported/ambiguous identity records must be counted as exclusions; retaining ended CS spans does not prove all delisted companies are covered. Source subtype metadata lacks exchange/OTC vintages. No native ALL_US_STOCKS parity is claimed, and a large universe backtest was not submitted to substitute for missing identity evidence.

## Ownership warmup and cohort mechanics

The new 2014 extract contains 73,739 ticker-month aggregates representing 318,671 nonderivative insider rows and 4,056,067 SH non-option institutional rows. It is incorporated into the reproducible local coverage processor. These are source rows, not filings, unique securities or complete native signals. Early-2015 source-recency windows are no longer left-censored by the old extraction start; vendor completeness, true zeros, publication-edge handling and amendment identity remain unproven.

The cohort audit reads 130,308 original/amended filing records from 2014-2020. To avoid immature endpoints, completeness diagnostics use 24 reporting quarters through 2019 Q4. The denominator is distinct original managers first publicly available within **365 calendar days**, not all eventual managers forever. The denominator uses later pre-cutoff information only for coverage analysis; it must never enter a historical strategy decision. Managers arriving later than 365 days and amendments are recorded separately.

| Buffer after quarter end | Global minimum public fraction | Global median | Ten-issuer sample minimum |
|---|---:|---:|---:|
| 30 days | 20.19% | 23.94% | 0.00% |
| 45 days | 70.49% | 94.91% | 50.00% |
| 50 days | 96.01% | 97.93% | 95.07% |
| 60 days | 97.46% | 98.87% | 97.15% |

The issuer sample includes 430,976 manager/issuer/quarter availability records and 222 nonempty issuer-quarter cohorts, from AAPL, MSFT, IBM, XOM, JNJ, JPM, GE, F, WMT and KO. This is a bounded mechanism sample, not a representative small-cap coverage survey. Minima differ materially from medians. A **60-day fixed gate is PROPOSED**, because it improves the observed missing tail beyond 50 days without creating a strategy-tuned axis. It is not a guarantee of completeness or a finalized economic staleness threshold. The cohort becomes eligible only after the buffer's New York end of day, and the actual filing must also be public by the decision cutoff.

For the proposed institutional change, use only unambiguously reconstructed managers with usable submissions for both eligible quarters. Count current holders minus prior holders within that same manager set. A certified complete filing omitting a security can establish no holding; a missing filing cannot. Track excluded managers and cohort coverage. Native latest-public-quarter NetHolderChange does not establish these mechanics. Remove the 180/365-day institutional recency axis: it is conceptually redundant with explicit adjacent eligible cohorts and must not become a post-result substitution.

## As-of revisions and missingness

Always filter `availableAt <= decision_timestamp` **before** assembling a state. Never resolve an old decision using a later amended filing or later issuer/owner identity. Institutional originals initialize a linked manager/quarter state; a public RESTATEMENT replaces it from that amendment's availability; NEW HOLDINGS adds only reconciled, nonoverlapping entries. Unknown types, ambiguous order, missing originals, null chains and overlapping additions are excluded pending source reconciliation. Source originals/amendments coexist; the tested local reconstruction policy prevents a later amendment changing an earlier view. Synthetic policy tests establish software behavior, not native/vendor parity.

For insider legs, deduplicate accession + rowKind + rowSk **before** joining reporting owners. Count distinct stable owner CIK, not names or multiplied transaction amounts. Joint filings can contain multiple owners: summing shares after this join would overcount. The 2014-2020 qualifying P/A nonderivative subset has no missing owner join/null owner CIK in the measured join, but joint owners, null ticker identities and missing amount operands occur. Exact correction links and owner attribution still need evidence. BuyCount and BuyValue remain semantics diagnostics; no performance comparison was made.

Keep separate states: genuine zero qualifying purchases; observed filing with no qualifying transaction; no filing; incomplete institutional cohort; missing vendor observation; unresolved identity; stale observation; unavailable history. Only a certified complete coverage/state may yield numeric zero. Primary matched comparisons exclude unavailable/ambiguous signals across all seven families, with an exclusion ledger. Broader momentum coverage is a separately declared diagnostic, not a silently different primary comparator. Reporting staleness and native zero fallbacks do not certify source completeness.

## Information and execution proposal

Decision cutoff: **21:00 America/New_York on the calendar day preceding the intended tradable session**. Only certified data public by that cutoff, from fully completed prior market sessions, may be used. Fill: **09:30 New York at the next intended tradable session**, with monthly dates supplied by an audited historical calendar. This allows weekend information only if public by the Sunday cutoff; it is deliberately not a promise to include every overnight filing. Price vendor readiness at the cutoff must be established, not assumed from an EOD-refresh documentation statement.

`CurrentTimeHours() == 9.5` produced opening fills in the sample. `IndicatorWindowAgo(operand, 1, 'Day')` retained prior-open values on ordinary weekdays; `PreviousClosingPrice` returned Data not available at all four tested opens. By contrast, `IndicatorWindowAgo(Price/PriceRateOfChange, 12.5, 'Hour')` matched prior completed closes at four January 2016 opens, including Monday after a weekend. This proves a useful sample mechanism. It does **not** prove disclosure cutoff composition, all holidays/DST/early closes, first-session-of-month scheduling, source vintage safety, or execution of the full reconstructed signal/universe.

Prospective metric conditions produced a reproducible server incompatibility (`unknown field compound, expected metric`), even with an empty DynamicRebalance pipeline. Removing those conditions allowed the same basic dynamic action to complete. Documentation describes turnover as a fraction and cost/benefit as dollars, but exact formulas/lineage were not certified. Keep all four prospective gates outside the primary strategy; the isolation does not prove every metric independently fails.

The CQB/SPY diagnostic retained CQB before its final January 6, 2015 source session, pruned it on January 7, and sold the remaining 2.9316241726 shares at $13.0409997940, exactly 90% of the prior $14.4899997711 close. This is observed engine mechanics, not verified merger proceeds or a universal delisting policy. An accepted/open order also blocked the January 8 rebalance. General delisting economics, ticker changes, cash/stock merger consideration, latency and slippage remain unresolved. Initial CQB/SPY targets were $50 each but fills were $42.50 each; effective deployment/default allocation buffers also need reconciliation before claiming the intended 95%.

AAPL source prices were unadjustedClose/4 before its 2020 split and equal afterward; no ApplyStockSplit appeared in the earlier native corporate-action probe. Its native prices and cash dividend suggest split-adjusted units in this sample. Catalog prose describes broader adjustment, so total-return adjustment and cash-dividend compatibility cannot be certified from generic wording alone. Volume basis is undocumented: multiplying unadjusted price by split-adjusted volume would inflate ADV by four. Do not use the current diagnostic ADV as a safe eligibility filter until compatible units, distinct sessions and lag are proven.

## Chronology, grid and ledger

**Final usable Development start remains unresolved.** Source records support studying 2015-2020; they do not yet certify a 2015 start for the reconstructed matched strategy. A 400-calendar-day price warmup for January 2015 extends before the existing January 2014 extraction. Resolve that coverage and critical PIT gates before choosing inception from coverage alone. End remains 2020-12-31. Inner 2019-2020 evaluation is part of Development selection, not independent confirmation.

Conditional five-fold proposal: train 2015 / evaluate 2016; train 2015 through 2016 / evaluate 2017; train 2015 through 2017 / evaluate 2018; train 2015 through 2018 / evaluate 2019; train 2015 through 2019 / evaluate 2020. Training includes only earlier dates, with past warmup outside scored returns. Embargo, minimum sufficient training, rank aggregation/eligibility/ties and overlap with inner selection remain unresolved. No fold was executed. No 2021+ data may resolve these choices.

Three two-point axes yield **8 full-composite cells**, not 16-32; do not invent another axis to hit a target. [The local enumeration](evaluation_plan.json) counts 34 distinct cells across seven families and two benchmarks per fold: 180 Development fold runs + 9 selected-family Development replays + 54 runs for six predeclared Development robustness scenarios + 9 outer Validation + 9 eventual Test + 20 failed/unresolved reserve = **281 future evaluations**. Eight already attempted diagnostic backtests make **289 projected total backtest evaluations**. Parameter cells are omitted for absent signals, preventing duplicate ablations. Lake jobs are a separate query ledger. Any extra replay/fold/internal amplification must consume the reserve or trigger a pre-performance redesign, never disappear from the ledger.

The six provisional robustness scenarios are doubled fee, additional session delay, $25m ADV, weekly cadence, additional filing delay, and an alternate audited universe. Magnitudes and alternate-universe definitions still need pre-freeze justification; regime subsets are local diagnostics, not six more simulation grids. This is a conditional plan, not a server preview, approved execution or finalized freeze contract. Historical lockbox remains unspecified; inference and ledger enforcement blockers persist.

## Audit outcome

This revision submitted five new Lake jobs, all completed, plus two rejected SQL attempts with no job IDs; one client wait timed out and the existing job was subsequently polled. Six daily diagnostic backtests were attempted: four completed, two schema failures retained. Events were extracted first: **228 rows across seven pages**, including an empty exhaustion page. Newly logged Nexus calls: **66** (64 successful receipts/downloads/pages and two rejected submissions); cumulative logged count: **261**. Actual token debit and remaining allowance remain unknown; published daily non-options estimates are zero, and no credit purchase occurred. The shared included-token authorization is 1,000, not a new 1,000 for each revision. Ceiling compliance cannot be independently reconciled from exposed receipts.

One metadata web search unexpectedly returned unrelated 2026 vendor performance snippets. Their values were excluded from evidence/design; no linked performance pages were opened. The exposure is recorded explicitly in provenance rather than claiming every public response was performance-free. All queried Nexus source/market/simulated observations remained pre-cutoff.

The full software suite passes **86 tests**. The unchanged semantic audit still rejects EXP002 because price/corporate-action PIT availability is unestablished; all critical source/universe PIT flags remain false. EXP001 results, definitions and raw data remain unchanged. No saved-portfolio creation call, optimization, candidate study, outer Validation/Test job, deployment, brokerage operation, Aurora run or freeze occurred.

Strict open-market classification, executable as-of amended matched cohorts, historical exchange/OTC, compatible price/volume/adjustments, complete execution/disclosure timing, sufficient warmup and final chronology remain critical blockers. They cannot be resolved by confident documentation or passing software tests.

**NEEDS DESIGN REVISION**


## Current custom-PIT revision

The owner-approved pre-performance change replaces native ownership indicators with local reconstruction and renames insider activity to **Distinct Qualifying Insider Purchasers**, explicitly including private P purchases. ADV is removed from primary eligibility; historical GSPC/CS is a proposed narrower universe. Eight composite cells remain. The detailed current contract and remaining blockers are in [custom_signal_spec.md](custom_signal_spec.md). Five completed artificial runtime diagnostics yielded 170 events/five pages; the custom indicator lag failed the 21:00 cutoff. One artificial indicator was created; zero production indicators were uploaded. Three immutable unavailable-panel gap ledgers each have 4384 audit decisions and zero numeric points. They are not complete Development data. The updated ledger has 13 attempted diagnostic backtests and 294 projected total including conditional future runs; no candidate study. Full suite: 104 passing; semantic PIT audit still rejects. **NEEDS DESIGN REVISION.**
