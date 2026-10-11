# EXP002 execution audit

| Diagnostic | Dates | Job ID | Events / pages |
|---|---|---|---|
| Eight native metrics/timing | 2016-01-04–2016-01-08 | 6acb87638c2f7fb888b3c0ed | 260 / 6 |
| Single-entry corporate actions | 2020-08-06–2020-09-01 | 6acb88758c2f7fb888b3c16a | 80 / 2 |

Full pages preserve noise/audits with repeats uncollapsed. Administrative createdAt/expirationTime in 2026 remain private and separate from pre-cutoff simulated timestamps. Supplied performance summaries are unused, never evidence of profitability.

VERIFIED sample: signals evaluate at daily open/close and orders fill at the same signal timestamp/price. Native $1 fills charge $0.001, consistent with 0.10%. Accepted/filled snapshots are repeated records, not separate trades.

One ApplyDividend occurs on August 13 at the saved pay date with share quantity/cash amount. No ApplyStockSplit appears across the split window. Adjusted prices/shares are suggested, but full raw/adjusted reconciliation, merger and delisting liquidation remain unverified.

Execution must follow all input availability, with prior completed bars and public filings. Native immediate fills contradict assuming automatic next-session timing. EXP002 needs verified lag composition plus scheduling. DynamicRebalance timing/membership, slippage, action basis and delistings remain open. Diagnostics are fixtures, not candidate trials.

Prospective turnover/cost/benefit/net-benefit declarations exist, but formulas and exclusively as-of inputs were not established with a dynamic probe. **Not certified safe**: keep outside primary strategy and do not execute a robustness gate until audited.


## Final diagnostic isolation (2026-10-11)

Six new daily diagnostics were attempted: timing/prospective combined (failed), timing-only (completed), empty-pipeline dynamic with prospective conditions (failed), empty-pipeline dynamic without prospective conditions (completed), CQB/SPY delisting (completed), and completed-bar lag (completed). Exact bodies, idempotency keys, statuses and events remain private under revision_20261011. IDs and event counts are in [revision runtime summary](revision_runtime_summary.json); all failures remain logged.

Proposed information cutoff: prior-calendar-day 21:00 New York; intended execution at next tradable-session 09:30 New York, monthly first-session schedule. CurrentTimeHours()==9.5 produces sample opening fills. IndicatorWindowAgo(operand,1,Day) reads prior-open values on normal weekdays; PreviousClosingPrice is unavailable at all four tested opens. IndicatorWindowAgo(Price/PriceRateOfChange,12.5,Hour) matched all four prior completed closes, including a weekend. No disclosure/monthly calendar/full vintage guarantee follows from this sample; DST/holidays/early closes, source readiness, rank composition and matched cohort implementation remain unverified.

Prospective conditions reproducibly fail with unknown field compound, expected metric; removing them allows basic DynamicRebalance. Four gates stay out of primary. Exact individual failure isolation/formulas/as-of inputs remain unresolved.

CQB is pruned after January 6 and liquidated January 7 at $13.040999794 (90% of the last $14.489999771 close), with fee. An accepted order blocks January 8 rebalance. Correct corporate consideration and general liquidation policy remain unresolved. Initial targets were 5% each but fills were $42.50 each from $1,000 funding: effective deployment differed from the target, so default buffers/allocation settings need reconciliation before claiming 95% achieved deployment.

AAPL source split-basis ratios are 4 before August 31, 2020 and 1 afterward. Price/dividend double counting, reported volume basis, generalized splits/ticker changes/mergers and stock slippage remain critical gates. No source-derived strategy performance was evaluated.
