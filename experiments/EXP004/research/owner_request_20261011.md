Create EXP004 — Cross-Sectional Momentum
Close EXP003 without modification as a source-feasibility-blocked experiment. Its economic hypothesis was never tested.
Create a new independent experiment:
EXP004
Research question
Does medium-term cross-sectional price momentum produce robust out-of-sample excess performance in our historically auditable source-defined common-equity universe?
This is the first experiment intended to proceed directly to actual alpha testing.
Do not include:
- insider data
- institutional data
- fundamentals
- market cap
- ADV
- current-index membership
- prospective rebalance metrics
Reuse the audited infrastructure that passed EXP003:
- historical source-defined CS stable-identity universe
- historical effective identity spans
- valid completed historical price requirements
- split-safe momentum price contract
- nominal historical price floor if already certified
- monthly scheduling
- next-session 09:30 execution convention
- $25,000 funding
- 0.10% fee per fill
- cash dividends
- nominal 95% deployment / documented observed reserve behaviour
- Research OS provenance and sealing
- paired/descriptive bootstrap infrastructure where appropriate
Do not reopen already-passed generic infrastructure audits.
Universe
Use the EXP003 universe gate that already passed:
source-defined historical common-stock identities with unique historical stable IDs, valid effective identity spans and valid historical prices.
Retain later-ended/delisted histories while historically eligible.
Exclude ambiguous identities.
Do not claim this represents the complete U.S. exchange-listed market.
Do not launch another universe search.
Signal
Cross-sectional momentum only.
Predeclare:
- 180 elapsed calendar days
- 365 elapsed calendar days
Use only completed split-safe historical price information available before the decision.
At each monthly rebalance, rank eligible securities cross-sectionally by momentum.
Prefer higher momentum.
Portfolio sizes
Predeclare:
- top 20
- top 40
Therefore the primary parameter surface is exactly:
2 momentum horizons × 2 holding counts = 4 cells
Do not add another alpha parameter.
Monthly cadence fixed.
Equal-weight holdings fixed.
Benchmarks
Freeze:
1. explicit SPY buy-and-hold
2. monthly equal-weight eligible-universe portfolio
The equal-weight universe benchmark is particularly important because it tells us whether momentum ranking adds value beyond simply owning the source universe.
Chronology
Because insider coverage is no longer required, determine Development inception using only the already-audited price/universe warmup.
If the existing evidence certifies a clean 2015 start after 365-calendar-day warmup, use it.
Otherwise choose the earliest clean date from price/universe availability only.
Development ends:
2020-12-31
Prefer expanding chronological folds ending in:
- 2017
- 2018
- 2019
- 2020
if supported.
Freeze outer Validation before performance:
2021-01-01 – 2023-12-31
Freeze workflow-held-out historical Test:
2024-01-01 – 2024-12-31
Do not retrieve Validation or Test observations during design/Development.
Selection rule
We are not merely searching for the highest Development Sharpe.
For each of the four momentum cells record:
- total return
- zero-RF Sharpe
- Sortino
- annualized volatility
- max drawdown
- turnover
- participation
- fold-by-fold performance
- performance relative to equal-weight universe
- performance relative to SPY
Candidate eligibility should require:
- adequate scheduled participation
- no critical execution/data failure
- positive incremental performance versus the equal-weight universe on the predeclared primary measure
- reasonable fold consistency
Predeclare the exact primary selection statistic before running performance.
Prefer a robust criterion based on median held-out-fold excess performance with Sharpe as a secondary requirement rather than selecting a single maximum backtest.
Tie-break using lower sensitivity/turnover, then deterministic parameter ordering.
Do not modify this after results.
Stability
With only four cells, report the complete parameter surface.
We want to know whether:
- both momentum horizons work
- both holding counts work
- one isolated configuration carries the entire result
Flag isolated optima as fragile.
Robustness
Predeclare:
- +10 bps additional traded-notional cost per side
- +20 bps additional traded-notional cost per side
- one-session extra execution delay
- basic bull/bear and high/low-volatility descriptive decomposition
Do not introduce additional optimized parameters.
Final pre-run check
This experiment should not trigger another broad research audit.
Perform only the minimum checks necessary to bind the already-certified price/universe machinery to EXP004.
If those existing contracts compile correctly, prepare EXP004 for freeze.
Run:
python -m src.research audit EXP004
Run the full test suite.
Commit and push.
Finish with:
- final universe
- Development inception
- folds
- Validation dates
- sealed Test dates
- four parameter cells
- benchmarks
- selection rule
- projected run count
- remaining noncritical limitations
- tests
- commit SHA
End with:
READY FOR FREEZE REVIEW
or, only if something genuinely critical fails:
BLOCKED
Do not freeze automatically.