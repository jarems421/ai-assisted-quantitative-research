EXP004 has completed freeze review and is approved.
Freeze the EXP004 hypothesis and full experiment specification exactly as currently reviewed.
Do not change:
- universe definition
- Development dates
- fold boundaries
- Validation dates
- sealed Test dates
- four momentum cells
- benchmark definitions
- selection rule
- eligibility requirements
- transaction costs
- robustness contract
- statistical definitions
First run:
python -m src.research audit EXP004
Confirm it passes.
Then execute:
python -m src.research freeze-hypothesis EXP004
Record:
- frozen specification hash
- frozen methodology hash
- Git SHA
- exact sealed date ranges
- exact candidate definitions
- exact benchmark definitions
- exact selection contract
Commit and push the freeze.
After the freeze is successfully committed, prepare EXP004 Development for execution.
Development execution preparation
We are now authorized to begin Development only.
Absolutely no outer Validation or Test observations may be accessed.
Compile the production Nexus inputs for:
Momentum candidates
- M180 / K20
- M180 / K40
- M365 / K20
- M365 / K40
Benchmarks
- monthly equal-weight eligible universe
- explicit SPY buy-and-hold
Use:
- Development: 2015-01-02 through 2020-12-31
- monthly first-session rebalance
- preceding-calendar-day 21:00 New York information cutoff
- next intended session 09:30 execution
- $25,000 starting equity
- 0.10% fee per stock fill
- cash dividends
- nominal 95% deployment
Use the frozen historical source-defined CS universe and completed split-safe momentum contract.
Do not introduce new filters.
Do not add price, liquidity, market-cap, sector or index screens.
Production input QA
Before submitting runs, verify:
- every decision date
- eligible universe count
- stable IDs
- momentum availability
- exact ranking values
- selected top K
- no future bars
- no duplicate identities
- no ambiguous identities
Store the frozen Development input manifest and hashes.
If input QA fails, stop before submitting the affected run.
Do not redesign the strategy to repair poor coverage.
Run the four-fold Development programme
Execute the predeclared chronological folds:
1. train 2015–2016 / score 2017
2. train 2015–2017 / score 2018
3. train 2015–2018 / score 2019
4. train 2015–2019 / score 2020
Run all four momentum cells.
Run the equal-weight eligible-universe benchmark and SPY benchmark as required by the frozen evaluation plan.
Do not stop early because a strategy looks bad.
Do not add candidates because results look disappointing.
Preserve all failures.
Raw extraction
Immediately after each completed Nexus run:
- capture run metadata
- capture configuration
- capture warnings
- extract history
- extract events where required by the frozen audit policy
- preserve raw responses immutably
- hash everything
- update the trial ledger
Do not overwrite prior receipts.
Independent analysis
Calculate the frozen independent metrics locally.
For every cell/fold report:
- total return
- mean daily return
- annualized volatility
- RF=0 Sharpe
- Sortino
- maximum drawdown
- turnover
- scheduled participation
- paired mean daily excess versus equal-weight universe
- Sharpe difference versus equal-weight universe
- comparison versus SPY
Pool only the predeclared scored fold observations.
Apply the exact frozen selection rule:
- participation ≥90% in every scored fold
- positive pooled mean daily excess
- positive pooled zero-RF Sharpe difference
- positive median fold mean excess
- positive mean excess in at least 3 of 4 folds
Then select by:
1. highest median held-out-fold mean daily excess
2. lower parameter sensitivity
3. lower turnover
4. deterministic ascending parameter order
If no candidate qualifies, record:
NO EXP004 CANDIDATE ADVANCES
Do not loosen the rule.
Stability analysis
Display the full 4-cell surface.
Report:
- fold-by-fold incremental effects
- sign consistency
- sensitivity to 180 vs 365 days
- sensitivity to K20 vs K40
- isolated-optimum warning
Do not replace the selected winner after inspecting neighbours.
Development-only robustness
Do not run outer Validation yet.
Only after Development selection, perform the predeclared Development robustness work allowed by the frozen plan.
Keep +10/+20 bps local cost stresses clearly separate from base Nexus results.
Preserve the one-session execution-delay test according to the frozen plan.
Reporting
Create:
reports/EXP004_development_report.md
Include:
- frozen hypothesis
- four-cell results
- fold results
- benchmark results
- full stability surface
- turnover
- robustness
- selected candidate or no-advance result
- limitations
Update the README experiment registry.
Do not characterize Development performance as confirmed alpha.
Git
Make logical commits during execution.
Push all verified work.
Keep raw private data ignored.
Finish by reporting:
- freeze hash
- Nexus run IDs
- run count
- four-cell Development table
- fold table
- benchmark table
- selected candidate, if any
- reason it passed/failed
- robustness results
- tests passed
- final commit SHA
Stop before outer Validation.
Do not open Validation or Test automatically.