# EXP002 native runtime audit

## ROC Day units

PriceRateOfChange(AAPL,126/252,Day) compiled/evaluated without lhs errors in ten open/close samples per length. Independent bounded prices give **20/20 matches** to the first observed price tick after evaluation_time minus N elapsed calendar days (within 0.001 percentage points) and **0/20 matches** to N completed-session closes.

At January 8, 2016 close, the 126 reference selects September 8 opening price and 252 selects May 4 opening price. This is one-asset/week evidence, including timezone/holiday effects, not a global vendor guarantee. It invalidates calling those lengths completed sessions. Proposed horizons become 180/365 calendar days; actual new lengths and completed-bar lag still require confirmation. No predictive performance influenced the revision.

| Declaration | Sample verification | Remaining evidence |
|---|---|---|
| InsiderTrades(AAPL, DistinctBuyers/BuyCount/BuyValue, Any, 90, instrument=Equity) | All evaluated; zeros with source activity but no P rows | General missing-history/zero, owner dedup, positive amount reconstruction, amendments |
| InstitutionalHoldings(AAPL, empty manager, NewHolders/NetHolderChange/NetShareChange,365,Equity) | All evaluated; distinct strategy IDs retain generic-named traces | Public-quarter/cohort completeness, source parity, versions and stale/zero contracts |
| Daily fee/dividend configuration | Fill fee and pay-date dividend observed | DynamicRebalance, slippage, lag and complete action contract |
| ALL_US_STOCKS | Historical Lake segments and identity panel observed | Native membership parity and exchange/OTC/type exclusions |
| Prospective rebalance metrics | Prior declarations/documentation | Runtime formulas/units/as-of safety |

AAPL's January 8 newest quarter has 43 public managers versus 2,144 prior-quarter managers. This supports a cohort-comparability concern; raw versioned share sums are not deduplicated native reconstructions, and precise attribution of each native change remains unresolved.

P source rows predominantly lack totalValue and some economic dates exceed availability. Raw versions coexist without establishing native replacement semantics. See query log and nexus_runtime_summary.json for sample-scoped evidence. No performance search or freeze occurred.


## Design-revision runtime audit (2026-10-11)

[Design revision](design_revision.md) supersedes primary market-cap, liquidity, recency and cadence axes. Five further Lake jobs completed; two SQL requests were rejected before job IDs. One 50-second wait expired; the existing job was polled, not resubmitted. Six diagnostic backtests: four complete, two retained schema failures. Events: 228 rows / seven pages (one empty exhaustion page). New Nexus calls: 66, including two rejected requests; cumulative 261. Actual token debit remains unknown, shared ceiling 1,000 included tokens, no purchases.

2014 source warmup is saved and used locally. Mature cohort completeness supports considering a fixed 60-day gate, never a hindsight completeness input. Native horizons 180/365 evaluate; sample 12.5-Hour operand lag recovers prior completed closes, while one Day does not. Prospective-metric conditions are incompatible with the observed backend; basic dynamic actions without them complete. CQB pruning/liquidation is observed in one case, with unexplained haircut/allocation mechanics. No ALL_US_STOCKS/global candidate simulation substitutes for absent exchange history.

All critical PIT flags remain false. Source classification, amendments/completeness, native matched-cohort parity, volume/price basis, safe monthly disclosure/execution composition and start/folds remain unresolved. No hypothesis freeze, candidate study, optimizer, outer Validation/Test or deployment occurred. One metadata web search returned unsolicited unrelated later vendor performance snippets, excluded and logged in provenance; no linked performance page was opened. The unchanged semantic gate remains a deliberate failure, not weakened to pass.
