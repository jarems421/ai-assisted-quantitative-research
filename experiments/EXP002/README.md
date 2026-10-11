# EXP002 — research design draft

**DRAFT, not frozen; no Nexus observation queries or jobs performed.** The [specification](spec.json) contains proposed methodological choices and a bounded declaration audit. All source and universe point-in-time flags remain false. [Provenance](provenance.json) separates VERIFIED declarations/documentation, PROPOSED choices and UNRESOLVED runtime evidence. No spend is approved: every stage token ceiling is zero. The supplied [Aurora memo](aurora_research_memo.md) is preserved verbatim as external evidence; its heading and self-reported activity are not independent verification.

## Question and proposed hypothesis

Among a dynamic liquid U.S. equity universe, does combining medium-term price momentum with point-in-time corporate-insider accumulation and improving institutional ownership produce more robust future performance than momentum alone?

The proposed full composite must add **net mean daily excess return and zero-RF Sharpe** over a matched momentum-only portfolio, with a stable effect across chronological folds and subsequent frozen evaluation windows. Lower drawdown or volatility without incremental return does not confirm this hypothesis. Complementary information is an economic rationale to investigate, not evidence of a predictive signal.

Economic falsifiers are nonpositive incremental net return or no Sharpe improvement in a later frozen period. Lack of Holm-adjusted statistical support means nonconfirmation, rather than proof of no effect. An isolated optimum, single-stock/regime dependence or disappearance under cost/disclosure-delay stress fails the robustness claim. Unusable point-in-time data invalidates the design before any economic test.

## Proposed universe and construction

Rebuild U.S. common-equity membership at each rebalance, using historical listings, stable security identifiers and only information available then. Include dead/delisted names in the source history; exclude funds, ETFs, preferreds, ADRs and OTC securities. Base liquidity filters are price at least $5, trailing 20-session average dollar volume at least $10 million and market capitalization at least $1 billion. All inputs are lagged to the decision time. These are proposals; historical Nexus membership and filter support are unverified.

Use the same point-in-time eligible signal-coverage universe for matched comparisons. Report its size, exclusions and coverage by date, then test momentum on the broader price-eligible universe to diagnose coverage-selection effects. A confirmed zero activity count is distinct from an unavailable filing or absent vendor history. Do not silently convert missing data to zero, use current holdings retrospectively or omit dead stocks. Missingness/staleness thresholds must be chosen from data-coverage evidence before freeze, without consulting performance.

Baseline construction is long-only, unlevered, monthly rebalancing, equal-weight top 20 holdings, 95% deployment and a cash remainder. Cross-sectional signal ranks are averaged with equal weights; ties require a deterministic stable-identifier rule. A positive expected signal direction means a higher rank is preferred. The primary proposed fields are ROC, DistinctBuyers and NetHolderChange. Purchase classification, normalization, rank arithmetic, historical units and stale-data handling remain unresolved. BuyCount/BuyValue and NewHolders/NetShareChange are research diagnostics, not permission to try unlimited substitutions.

No more than three alpha signal classes; one representation per class, fixed equal weights, no fitted interactions, stops, market timing overlay, leverage or sector-specific rules. Liquidity/membership filters are not additional alpha signals. Prospective turnover/cost gates are optional robustness designs only, pending audited units and proof of no future information; they cannot become a fourth tuned signal after results.

## Candidate, control and benchmark families

| Family | Role |
|---|---|
| Momentum only | Primary matched comparator; also a candidate |
| Insider only | Single-signal control |
| Institutional only | Single-signal control |
| Momentum + insider | Leave-in pair / institutional ablation |
| Momentum + institutional | Leave-in pair / insider ablation |
| Insider + institutional | Momentum ablation required by the existing three-signal control policy |
| Full composite | Main proposed hypothesis |
| Explicit SPY buy-and-hold | Simple market benchmark, with identical funding/cost conventions |
| Equal-weight dynamic eligible universe | Universe/exposure benchmark |

The ninth-family ceiling counts seven signal families and two benchmark families conservatively. Momentum-only remains a frozen explicit comparator, even if another eligible family wins selection. All family failures and weak results are retained. Failing to select the full composite is evidence against the proposed composite, not a reason to change the question.

## Preliminary parameter ranges

These are bounded design ranges, **not empirically supported optima or compiled Nexus handles**. Keep one coarse two-point grid; do not add unseen trials. The lower endpoints are proposed baseline values. Units require vendor verification before compilation.

| Concept | Proposed grid / fixed choice |
|---|---|
| Momentum | 126 or 252 trading sessions; lag the input close |
| Insider accumulation | 30 or 90 calendar days of publicly available qualifying disclosures |
| Institutional filing recency | 180 or 365 calendar days; limits eligible filing age, not a rolling sum of quarterly ownership changes |
| Holdings | 20 or 40 |
| Rebalance | Monthly baseline; weekly robustness alternative, exact calendar rules unresolved |
| Liquidity | $10m or $25m trailing 20-session average dollar volume |
| Market capitalization | $1bn or $5bn, point in time |
| Deployment / price floor | 95% / $5 fixed |
| Weights | Equal security weights and equal signal-rank weights |

The six numeric axes imply **64 cells**, not six independent optimization authorizations. A preliminary plan is 9 baseline family runs + 64 full-composite cells + 5 Development folds × (64 training candidates + 1 selected held-out candidate + 3 held-out comparators) + 4 outer-Validation runs + 8 stress scenarios × 4 portfolios + 4 historical-Test runs = **453 evaluation units**. This is planning arithmetic, not a Nexus preview or guaranteed upper bound: it counts repeated baselines and benchmarks, and actual fold/optimizer/stress amplification is unresolved. No grid is approved for execution. Before freeze, replace this proposal with an audited plan capped at 500 total remote evaluation units across the experiment, including failed jobs, controls, all fold internals and ancillary simulations. Reject any compiler/preview that exceeds the cap; do not silently prune after viewing outcomes. The generic v1 planner's 1,000-unit guard does not enforce this proposed aggregate ceiling; experiment-level ledger enforcement must be reviewed before freeze.

Signal alternatives, extra cadence grids, sector portfolios and new weighting schemes add counted trials and require a revised pre-freeze plan. Predeclared stresses diagnose the frozen candidate; they do not select replacements.

## Windows, lockbox and selection

| Segment | Provisional design only |
|---|---|
| Development | 2015-01-01–2020-12-31 |
| Inner Validation | 2019-01-01–2020-12-31, within Development |
| Outer Validation | 2021-01-01–2024-12-31, never candidate formation |
| Historical lockbox | **Unresolved**: `test: null`, no sealed range or authorization yet |
| Candidate-formation cutoff | Proposed 2020-12-31 |
| Forward paper | Begins after freeze, final review and separate owner approval; date unresolved |

Dates are proposed chronological partitions, not claims that insider/institutional history exists back to 2015. Final windows require common auditable coverage, enough Development data after warmup, nonoverlapping folds and a separate later lockbox. If coverage is insufficient, revise dates with a recorded coverage-only reason while still DRAFT; never choose dates from strategy performance. Proposed 400-calendar-day warmup is not evidence of vendor support or sufficient coverage, and must respect available pre-Development observations and the research cutoff.

The 2025–2026 SPY period was already opened for EXP001. It must not be described as unseen for EXP002. Any historical lockbox will be `workflow_held_out`, with prior knowledge disclosed. Before freeze its exact boundaries and sealed range must be specified and excluded from Aurora research. Until then, the manual prompt forbids all market/performance observations beyond the proposed Development cutoff. This is a research instruction, not a claim of server-side isolation.

Follow the existing sequence: data audit → hypothesis freeze → Development → candidate freeze → outer Validation → Development-only walk-forward → robustness → owner-approved historical Test → separate paper authorization. Within Development use chronological training and inner evaluation; a fold must never select on its held-out portion. Five expanding Development folds are proposed, with explicit boundaries, minimum training span and any embargo to be settled from coverage. Outer Validation and Test never retune selection.

Proposed selection uses highest eligible independent Development zero-RF Sharpe, with complete control evidence and stability diagnostics reported alongside it. Retain the starter eligibility proposals: maximum drawdown 25%, at least 20 completed trades, participation 35%; propose breadth at least 20. Exact participation/breadth measurement and tie handling require a written assessment contract before freeze. These are provisional design constraints, not fitted thresholds. Benchmark portfolios are reported even when strategy eligibility constraints are inapplicable.

## Costs, metrics and statistical policy

Initial funding is $25,000 per period. Proposed fee is 0.10% of notional per stock fill; dividends stay in cash. No verified spread/slippage model is available. Establish what the engine actually models and separately quantify implementable conservative spread/slippage and cost stress before freeze. Do not claim net executable performance from a guessed zero-slippage setting. Fees/dividends already reflected in equity are not added/subtracted again. Count turnover and trade costs for every family and comparator.

Use the existing independent metrics: true New York session closes, simple adjacent-close returns, RF=0, 252 sessions/year, sample daily SD, volatility = SD × sqrt(252), Sharpe = sqrt(252) × mean/SD, Sortino with zero daily MAR and downside RMS over all returns, period-specific running-peak drawdown and total return relative to initial funding. No definitions change after held-out outcomes. Stored engine ratios are supplementary and require their RF/execution convention caveats.

Record every attempted family, cell, failure, replacement and unresolved result. Proposed paired moving-block bootstrap uses aligned daily return differences, 20-session blocks, 10,000 draws and seed 2002. Bootstrap intervals alone are not Holm-adjusted p-values: the existing helper reports percentile intervals, so a valid null-centered one-sided test and its audited implementation remain unresolved before inferential claims. Proposed Holm familywise alpha is 0.05 across full-versus-momentum, full-versus-momentum+insider and full-versus-momentum+institutional comparisons and all declared confirmatory windows. Freeze the exact test inventory before results; parameter search and winner-selection bias remain even after adjusting these comparisons. Report effect sizes, uncertainty and nonconfirmation without treating absence of significance as equivalence.

Token ceilings are zero because no spending was authorized. Actual cost needs a current quote, asset counts, audited job amplification, event multiplier and server preview. The dated pricing file is metadata, not an account quote. Aurora cost is unknown. Do not infer free execution from the daily-stock price entry. Intraday research is out of scope.

## Robustness and prospective paper

Require complete parameter surfaces, neighbouring-cell and fold-rank stability, aligned controls, coverage audits, exposure/contribution diagnostics and regimes defined without optimizing strategy results. Predeclare cost doubling, one-bar execution delay, an alternative universe threshold, weekly cadence, bull/bear, high/low volatility, rising/falling rates and an extra filing-availability delay. Exact regime labels and delay size are unresolved; finalize from methodology/coverage before freeze. Missing scenario evidence remains `not_run`. Factor/sector confounding must be examined before any alpha claim; better Sharpe alone is insufficient.

Paper trading requires a separate owner decision, the frozen portfolio, recorded initial funding and a prospective monitoring plan. Propose at least six calendar months and six monthly rebalance opportunities, extending to twelve months for inadequate signal activity. Record signals, availability timestamps, target/actual holdings, fills, costs, discrepancies and benchmark returns. Predeclare operational stop criteria and review schedule before authorization; paper outcomes cannot retune this experiment. Only this forward evidence can be called genuinely forward unseen. No live-trading path is authorized.

## Evidence required from manual Aurora research

1. Do ROC and all six proposed disclosure fields actually exist, with which signatures, units, aggregation, rank/filter arithmetic and historical semantics?
2. Does each source preserve public filing acceptance, vendor ingestion and amendment timestamps, rather than trade date or quarter-end? Supply evidence of actual point-in-time behavior.
3. What are the joint coverage start/end, missingness, stale ages, purchase classifications and asynchronous institutional filing comparison rules? Can zeros be distinguished from missing data?
4. Can historical listings, dead securities, security types, market capitalization, splits and delisting proceeds be reconstructed at every rebalance without current membership or revised future inputs?
5. Can the proposed composite and matched controls use the same audited dynamic universe, next-session fills, exact cadence, warmup and cash/dividend/fee conventions? What evidence do events expose?
6. Are prospective turnover/cost/benefit metrics available before trade decisions, in what units, and without realized future returns? What slippage/capacity assumptions are defensible?
7. Which parameter units/ranges and chronological windows are supported by coverage alone? Can a later historical lockbox be protected, with acknowledged prior EXP001/model knowledge?
8. What actual evaluation count, fold amplification, current token quote and manual-Aurora access controls apply? Which economic mechanisms could fail, and which claims remain unsupported?

The [manual prompt](aurora_research_prompt.md) is retained as the original research instruction. The supplied memo has now been ingested claim-by-claim into provenance. Its original tool trajectory was not supplied, so its no-mutation/no-spend/access assertions remain external self-report. **The draft is not ready for human freeze approval.** Schema validation passes while `python -m src.research audit EXP002` intentionally fails on unestablished point-in-time evidence; the audit has not been weakened.

## Bounded declaration audit — 2026-10-11

VERIFIED below means the stated declaration, documentation or metadata was inspected. It never means an indicator was evaluated by the server. Installed SDK 1.42.0 signatures, source line numbers, source hashes and offline indicator JSON are recorded in provenance. No strategies, portfolios, candidate snapshots, API clients or jobs were created. Current MCP declarations were inspected without calling their tools.

| Blocker | Status and exact declaration | Remaining uncertainty |
|---|---|---|
| Insider fields | VERIFIED SDK: `InsiderTrades(asset, metric, role, window_days, owner_cik=None, issuer_cik=None, instrument=None)`; `DistinctBuyers`, `BuyCount`, `BuyValue` | Native identity/dedup, dollar scaling, zero/missing and amendment completeness |
| Institutional fields | VERIFIED SDK: `InstitutionalHoldings(asset, manager, metric='HolderCount', window_days=180, instrument='Equity')`; `NewHolders`, `NetHolderChange`, `NetShareChange` | Empty manager string is aggregate; quarter/cohort alignment and changes under asynchronous filings remain UNRESOLVED |
| Momentum | VERIFIED SDK: `PriceRateOfChange(asset, length=30, interval='Day')`; `IndicatorRateOfChange(operand, length=30, interval='Day')` | Both 126/252 serialize locally; native session/calendar counting, warmup and price basis UNRESOLVED |
| Market cap / liquidity | VERIFIED fields: `Fundamental(CANDIDATE,'marketCap')`, `Price`, `Volume`, `IndicatorSimpleMovingAverage`, `IndicatorWindowAgo`; `lake.sec_daily_ohlc.{date,closingPrice,volume,marketCap}` | PIT cap vintages, lagged completed bars, adjustment consistency, stale/missing behavior and ADV composition UNRESOLVED |
| Universe / exclusions | VERIFIED builders: `universe('ALL_US_STOCKS')`, `dynamic_rebalance`, `filter`, `select_top`, `select_percentile` | `IsAssetType` accepts Stock/Cryptocurrency/Option/Other; Stock includes ETFs. Historical listings/dead names/subtype exclusions/identifier changes UNRESOLVED |
| Availability / revisions | VERIFIED static columns: `availableAt`, `filingDate`, `availabilitySource`, `accession`, `isAmendment`, `amendmentType` | Native as-of mapping, ingestion, owner coverage, amendment replacement/addition and stale/zero taxonomy UNRESOLVED |
| Execution | VERIFIED `backtest(..., fee_config, dividend_policy)` and cash/reinvest choices; dividend/split catalog declarations | No next-session-delay or stock-slippage argument found on this handle; actual fill/debit/action timing UNRESOLVED |
| Prospective gates | VERIFIED `rebalance_planned_turnover()`, `rebalance_estimated_cost()`, `rebalance_expected_benefit()`, `rebalance_net_benefit()` → `RebalanceDecisionMetric` | Exact formulas, turnover convention and as-of input lineage UNRESOLVED |
| Coverage | VERIFIED public receipt lists 2015–2020 partitions for all four ownership tables | Joint native field/ticker/price/cap/security-master completeness UNRESOLVED |
| Future planning | VERIFIED declared `get_sweep_surface(portfolio_id?)`, `systematic_sweep(...,preview_only=True)`, `run_walk_forward_study(...,preview_only=True)` | No operation invoked; actual counts/quotes and sweep compilation billing UNRESOLVED |

Required native JSON selectors are `InsiderTrades.metric` and `InstitutionalHoldings.metric`, with `windowDays`; `manager` is a required SDK argument even though the aggregate value is an empty string. `CANDIDATE` omits `targetAsset` rather than naming a fake ticker. Documented insider/holder metrics use counts, BuyValue uses dollars and NetShareChange uses shares. ROC is documented in percentage units. These unit contracts have not been checked against native values. [Fundamental reference](https://nexustrade.io/docs/indicators/fundamental-indicators), [technical reference](https://nexustrade.io/docs/indicators/technical-indicators).

Material corrections to the external memo/design are recorded before freeze:

- SEC code P includes private purchases; it cannot establish an open-market-only filter by itself.
- The institutional recency axis was renamed to `institutional_filing_recency_calendar_days`, preserving 180/365. Latest-public versus prior-quarter comparison is documented, but synchronized cross-manager books are not established.
- Updated insider documentation distinguishes unknown owner/amendment coverage from a known zero. An institutional zero may mean no recently public filing. Neither is automatic evidence of no economic activity.
- An advanced-documentation ETF subtype example conflicts with the installed SDK enum. No unsupported subtype string was silently substituted, and no narrower historical universe was invented.

The vendor's [coverage publication](https://nexustrade.io/blog/free-historical-insider-and-institutional-stock-data-20261003) documents insider history from 2006 Q1 and institutional history from 2013 Q2. The [pinned snapshot receipt](https://huggingface.co/datasets/austin-starks/sec-ownership-disclosures/blob/0662635d4adddd295ba93530fa0de51aa453b97d/snapshot.json), generated October 10, lists all six Development years for each table. Its SHA-256 is `074f5471871cb871c44ef3a45da9e549f06c39405399a2a6e30b6a3d1df6f5ca`; only receipt metadata was downloaded, never Parquet or observations. Partition existence supports a coverage audit, not field completeness or equivalence to native engine inputs.

That publication describes a New York filing-day-end convention for the public ownership package. It is not exact intraday acceptance, nor proof of native-engine behavior. The custom-data SDK's date-only `disclosed` normalization uses next UTC midnight: that separate convention must not be generalized to SEC data. No fixed lag is assumed to repair revisions or identifier mappings.

The [prospective metric reference](https://nexustrade.io/docs/indicators/portfolio-indicators) documents turnover as a portfolio fraction and cost/benefit as dollars, evaluated before rebalance actions with zero outside those contexts. It does not establish the calculation formulas or point-in-time input lineage. No prospective gate was enabled.

For later planning, `get_sweep_surface` describes applicable axes. `systematic_sweep` preview declares `plannedUnits`, genes and warnings without launch, but does not establish zero billing for LLM gene compilation. `run_walk_forward_study` and the SDK `walk_forward` docstring declare a preview without creating a study or billing. None was called. `build_portfolio` is declared zero-token/no-persistence, but was not used because strategy generation is outside this task. Deterministic reviewed genes are required before any preview; do not invoke `gene_intents` under zero spend. No dedicated standalone backtest cost-estimate endpoint was found.

Read-only SDK metadata methods are `NexusTradeClient.get_lake_catalog()` and `describe_lake_table(table)`, issuing GETs to the versioned lake catalog. They were not invoked or assumed free. The SDK can create an anonymous workspace when authentication is absent; a later metadata audit must use existing registered authentication and avoid that side effect. [API overview](https://nexustrade.io/docs/api-reference/overview).

**READY FOR COVERAGE AUDIT** means the declaration/partition evidence supports reviewing the next bounded, non-performance audit of pre-cutoff completeness, identities and availability. It does not mean freeze-ready or authorize further data reads, spend, previews or jobs. The cutoff remains **2020-12-31**. Historical lockbox, native PIT coverage, execution/slippage, inferential implementation and actual budgets remain freeze blockers.
