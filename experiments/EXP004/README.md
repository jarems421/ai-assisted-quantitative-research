# EXP004 — cross-sectional price momentum

**DRAFT · READY FOR FREEZE REVIEW.** This is an independent price-only experiment. No performance has been queried, hypothesis frozen, Nexus operation called or spending authorized. EXP003 is closed externally as source-feasibility-blocked; its economic hypothesis was never tested and its original files remain unchanged.

Does medium-term cross-sectional price momentum produce robust out-of-sample excess performance in our historically auditable source-defined common-equity universe?

| Component | Frozen design |
|---|---|
| Universe | Historically effective unique source-covered CS stable identities, positive completed nominal prices, unambiguous prior-session/execution identity, maximum-365-day completed history. Retain later-ended histories while eligible. No claim of complete US exchange coverage. |
| Signal | Split-safe price momentum over 180 or 365 **elapsed calendar days**, completed information only. No cash dividends in the price ratio. |
| Four cells | M180/K20, M180/K40, M365/K20, M365/K40. Higher momentum first; stable-ID ties; equal weights. |
| Fixed execution | Monthly first trading session; preceding calendar day 21:00 New York cutoff; intended next-session 09:30 fill. Numeric/validity/exact-date and monthly-schedule guards. |
| Costs | $25,000; 0.10% per stock fill; cash dividends; nominal 95% deployment. Inherited bounded samples deployed 93.5% before fees; this is an observation, not a universal reserve formula. |
| Primary benchmark | Monthly equal-weight **entire same eligible universe**, with identical funding/costs/decision dates. |
| Market benchmark | Explicit SPY buy-and-hold, identical funding/costs, purchased once at the run's permitted inception. |
| Development | **2015-01-02–2020-12-31**; price-only inception supported by existing warmup receipts. |
| Expanding folds | Train 2015–2016/evaluate 2017; expand through 2017/evaluate 2018, through 2018/evaluate 2019, through 2019/evaluate 2020. |
| Outer Validation | 2021-01-01–2023-12-31; inaccessible during design/Development. |
| Sealed historical Test | 2024-01-01–2024-12-31; requires separate owner opening. Workflow-held-out, not genuinely unseen. |
| Planned evaluations | **59** including 20 failed/unresolved reserve; 12 separate local cost sensitivities. Development execution authorized; input QA must pass before submission. |

No insider, institutional, fundamental, cap, ADV, exchange/index-membership or prospective rebalance signal/filter is included. No extra price floor is added: inherited positivity is supported, a separate nominal threshold was not certified for this population. Both horizons and the equal-weight benchmark use the same maximum-horizon eligible population, so changing the signal does not silently change the comparator.

Eligibility requires audited aligned comparison, no critical data/execution failure, at least 90% audited scheduled participation in **every** scored fold, positive pooled mean daily net excess and separate zero-RF Sharpe difference versus equal-weight universe, positive median fold mean excess, and positive mean excess in at least three of four folds. Select highest **median held-out-fold mean daily excess**; tie-break by lower population SD of the two one-axis neighbors' pooled mean effects, lower mean absolute traded-notional/equity turnover, then ascending horizon/holdings. Missing neighbor effects have unknown (infinite tie-break) sensitivity. No eligible cell means no advancement. SPY comparison is reported independently and does not replace this primary comparator.

Report all four cells and both benchmarks, including poor results/failures: total return, RF=0 Sharpe, Sortino, annualized volatility, maximum drawdown, turnover, participation, fold metrics, and paired differences versus equal-weight universe and SPY. Flag isolated optima as fragile; never retrospectively substitute a neighbor. Robustness includes local additional 10/20 bps traded-notional cost per side, one extra execution session, and fixed descriptive market-regime decomposition. No new optimized axes.

See [freeze review](research/final_freeze_review.md), [selection contract](research/selection_contract.md), [price-only coverage](research/price_coverage.json), [candidate definitions](candidate_definitions.json), [evaluation ledger](evaluation_plan.json), [SDK fixtures](compiled_templates.json), [provenance](provenance.json), and [verbatim owner request](research/owner_request_20261011.md). VERIFIED labels apply only to named declarations, scoped inherited observations and local software behavior; they do not certify immutable vendor history or executable live profitability.

Reproduce this bounded local binding check with `python -m src.research.design_exp004`, validate with `python -m src.research audit EXP004`, and run `python -m unittest discover -s tests -v`. Ignored historical receipts are required to reproduce coverage counts. Hypothesis review does not authorize jobs: immutable numeric input generation/QA, production stream binding, current pricing/account checks and explicit execution approval must precede any submission. Paper evidence requires separate approval and at least six months/six monthly opportunities. There is no live-trading path.
