EXP002 — Design Revision + Final Pre-Freeze Runtime Audit
The coverage/runtime audit returned NEEDS DESIGN REVISION.
This is expected and acceptable. No candidate performance has been observed, so EXP002 may still be revised using coverage/runtime evidence.
The owner authorizes further Nexus Lake queries and minimal diagnostic daily backtests where they materially improve methodological certainty.
Use Nexus aggressively for verification, but do not use additional degrees of freedom for performance search.
Do not:
- evaluate candidate returns
- rank candidate performance
- optimize
- query outer Validation
- query historical Test
- deploy
- freeze EXP002
Candidate-formation cutoff remains:
2020-12-31
A. Revise the provisional design from the evidence already obtained
Incorporate these findings:
Momentum
Native PriceRateOfChange(..., interval='Day') matched calendar-time references in 20/20 probes and completed-session references in 0/20.
Replace the old proposed 126/252-session interpretation with:
- 180 calendar days
- 365 calendar days
Keep this as a two-point Development grid unless further runtime evidence invalidates it.
Market-price input must ultimately use an explicitly completed-bar-safe convention.
Market-cap filter
Historical marketCap point-in-time safety remains unresolved.
Do not make market capitalization a required primary-universe filter unless this audit proves its historical vintages are point-in-time safe.
If it cannot be established safely, remove market cap from the primary EXP002 design rather than guessing.
It may remain a documented diagnostic/robustness concept only.
Universe
Prefer an explicitly reconstructed historical universe over blindly trusting present-day membership.
Current provisional primary eligibility should be based on auditable historical information:
- common-stock security type
- nominal unadjusted price ≥ $5
- lagged trailing 20-session dollar volume
- historical listing/security identity
- explicit exchange/OTC rules once verified
Preserve later-delisted securities.
Resolve ADR, ETF, preferred, OTC and other subtype treatment before freeze.
Rebalance frequency
Make monthly the only primary cadence.
Weekly remains a predeclared robustness scenario only.
Do not optimize rebalance frequency in Development.
Market-cap parameter axis
Remove the $1bn / $5bn optimization axis unless PIT market cap becomes fully verified.
This reduces unnecessary model-selection degrees of freedom.
B. Resolve 2014 ownership warmup
The current source panel begins ownership analysis in 2015, which left-censors early 2015 rolling windows.
Query the minimum required 2014 ownership data to establish warmup for:
- insider disclosures
- institutional filings
No post-2020 observations.
Determine whether sufficient pre-2015 history exists to support a genuine 2015 Development start under the revised lookbacks.
Do not choose the start based on performance.
If 2015 remains unsuitable, identify the earliest defensible start based exclusively on coverage/PIT requirements.
C. Redesign the insider signal carefully
Our primary insider hypothesis is actual open-market accumulation, not every transaction that happens to increase ownership.
Audit native/source behavior sufficient to define:
DistinctBuyers
using qualifying open-market purchase transactions.
Resolve:
- transaction code P
- open-market classification
- owner identity/deduplication
- duplicate filing legs
- same insider appearing multiple times
- amended filings
- accession handling
- role filters
- null owner/security identities
- missing versus genuine zero activity
Compare the definition of:
- DistinctBuyers
- BuyCount
- BuyValue
for semantics only.
Do not performance-test them against each other.
Unless evidence strongly invalidates it, keep DistinctBuyers as the proposed single primary insider representation to minimize degrees of freedom.
Keep proposed availability windows:
- 30 calendar days
- 90 calendar days
All qualifying records must satisfy an as-of rule based on public availability, not transaction date.
D. Redesign the institutional signal around complete-enough public cohorts
The existing audit demonstrated that naïvely comparing the newest partially filed quarter can be invalid.
Example already observed:
- AAPL Q4 public managers on 2016-01-08: 43
- previous Q3 managers: 2,144
We therefore need a cohort-completeness policy before Development.
Use 2014–2020 pre-cutoff filings to quantify:
- reporting-quarter end
- filing/public availability delay
- manager counts over time after quarter end
- amendment timing
- percentage of eventual cohort publicly available by day N
- cross-sectional variation in availability
Evaluate completeness at sensible calendar offsets such as:
- 30 days
- 45 days
- 50 days
- 60 days
- additional values only if needed to characterize the filing distribution
This is coverage analysis, not strategy optimization.
Choose a fixed cohort-availability rule based on filing mechanics/completeness, never subsequent returns.
Prefer a simple fixed rule if defensible.
For example, a rule conceptually like:
institutional quarter becomes eligible only after a fixed predeclared post-quarter availability buffer
may be preferable to dynamically assuming every newest filing is a complete cohort.
Do not hard-code 45/50/60 days before the coverage analysis supports the final choice.
Then establish exactly how:
NetHolderChange
is computed between eligible public cohorts.
Unless invalidated, retain NetHolderChange as the sole primary institutional representation.
NewHolders and NetShareChange remain diagnostics/controls, not additional representations to try after seeing performance.
Resolve whether the current proposed 180/365-day institutional window_days axis remains meaningful after cohort gating.
If that parameter becomes redundant or conceptually unsound, remove it from the primary grid before freeze.
E. Amendment/revision policy
Establish an explicit as-of reconstruction rule for SEC-derived data.
The desired principle is:
only information with availableAt <= decision_timestamp may exist to the strategy
Determine how later amendments behave.
A later amendment must not rewrite an earlier historical decision.
For each filing/security state, reconstruct what was publicly known as of that timestamp.
Verify this with bounded source/Lake samples.
Write the rule into the EXP002 specification before freeze.
F. Missingness policy
Freeze a strict distinction among:
- genuine zero qualifying insider purchases
- no qualifying transaction
- no filing
- no institutional filing sufficiently complete yet
- missing vendor observation
- unresolved identity
- stale observation
- unavailable historical coverage
Missing data must not become numerical zero automatically.
Decide whether a security with unavailable signal data is:
- excluded from the matched signal universe
- retained with a separate missingness representation
Prefer the simplest auditable rule that preserves fair matched comparisons.
All candidate/control portfolios must use comparable eligible universes where required by the hypothesis.
G. Verify completed-bar and next-session execution
Native diagnostic fills occurred at the signal timestamp.
EXP002 must therefore explicitly create the intended execution separation.
Use minimal deterministic diagnostic daily backtests to identify an implementation that guarantees:
1. market-price indicators only use fully completed information
2. disclosure records are only used after their public availableAt
3. the portfolio decision occurs without future information
4. the resulting rebalance fills no earlier than the next tradable session intended by the specification
Investigate Nexus timing/scheduling mechanisms including:
- explicit indicator lag
- IndicatorWindowAgo
- strategy timing
- DynamicRebalance scheduling
- open versus close execution
- any actual supported delay semantics
Do not infer syntax.
Use the installed SDK/MCP declarations.
Prefer a convention conceptually equivalent to:
decision at day t → fully completed/available data only → execution at next session
But implement it according to verified Nexus behavior.
Produce an event-level diagnostic proving the final convention.
H. Verify liquidity construction
Establish a PIT-safe trailing average dollar volume filter.
Resolve:
- exactly which historical price field is used
- volume adjustment semantics
- split effects
- duplicate/non-session rows
- one-day lag
- 20 valid completed sessions
The filter must never include the execution session's unknown data.
Decide whether $10m / $25m remains a Development grid or whether liquidity should be a single eligibility threshold.
Prefer fewer optimized eligibility parameters where possible.
If there is no strong methodological reason to optimize liquidity, consider freezing $10m as a universe requirement and moving $25m to robustness only.
This decision must be made before seeing candidate performance.
I. Corporate-action and delisting probes
Use minimal pre-2021 deterministic cases where needed to verify Nexus handling of:
- stock splits
- cash dividends
- ticker changes
- mergers if supported
- delistings
Inspect events/equity mechanics, not profitability.
Determine compatibility between:
- the price field used for momentum/liquidity
- separate dividend cash handling
Avoid adjusted-price plus dividend-cash double counting.
Determine what happens to a DynamicRebalance holding that delists.
J. Historical universe
Complete the remaining historical-universe audit.
Resolve, using Nexus Lake/source data and minimal runtime probes as necessary:
- exchange history
- OTC treatment
- ADRs
- ETFs
- preferred shares
- ordinary/common shares
- ticker changes
- stable security IDs
- securities that later delist
Compare this explicit universe against ALL_US_STOCKS.
We do not need exact parity if an explicit safer historical universe can be built reproducibly.
Prefer the safer explicit construction.
K. Prospective rebalance metrics
Continue auditing:
- planned turnover
- estimated cost
- expected benefit
- net benefit
Determine:
- formula
- unit
- inputs
- timestamp
- whether any component contains future/realized information
Unless fully certified safe and interpretable, keep these out of the primary EXP002 strategy.
They are optional later robustness mechanisms only.
L. Reduce the search space before performance exists
Once the above evidence is resolved, redesign the parameter grid to minimize unnecessary degrees of freedom.
Target something around 16–32 full-composite cells, not an unnecessarily large grid.
Likely retained axes may include:
- momentum horizon: 180 / 365 calendar days
- insider window: 30 / 90 days
- holdings: 20 / 40
Add an institutional or liquidity axis only if the revised methodology shows it represents a genuinely meaningful uncertainty.
Monthly rebalance should be fixed.
Equal signal-rank weighting should be fixed.
95% deployment should be fixed.
Do not add new parameters merely to reach a target grid size.
Recalculate the full EXP002 remote-evaluation count including:
- all seven signal families
- both benchmarks
- complete parameter surface
- Development folds
- controls
- failed/unresolved trials
- outer Validation
- robustness
- eventual Test
Keep the complete trial ledger.
M. Final Development chronology
Using coverage only, finalize:
- Development start
- Development end 2020-12-31
- warmup
- five expanding chronological folds if feasible
- any embargo
No date may be selected based on performance.
Do not access 2021+ observations to make this decision.
N. Update artifacts
Update:
- spec.json
- provenance.json
- EXP002 README.md
- coverage_audit.md
- coverage_summary.json
- pit_audit.md
- universe_audit.md
- execution_audit.md
- nexus_runtime_audit.md
- cost_receipt.json
Create if useful:
- design_revision.md
Raw evidence stays under ignored storage.
Every changed design assumption must have:
- old value
- new value
- evidence
- reason
- confirmation that no strategy performance informed the change
O. Pre-freeze audit
Run:
python -m src.research audit EXP002
Do not weaken the audit.
A READY FOR FREEZE REVIEW result should require at minimum:
- defensible PIT insider construction
- defensible institutional cohort construction
- explicit missingness policy
- safe historical universe
- completed-bar semantics
- proven intended execution timing
- coverage-supported Development start
- bounded finalized search grid
- no unresolved critical leakage issue
If a noncritical item remains unresolved, document why it does not threaten the primary hypothesis.
Run the complete repository test suite.
Commit and push verified work.
Finish with:
- revised primary universe
- revised insider definition
- revised institutional definition
- revised momentum definition
- exact information cutoff/execution convention
- Development dates/folds
- final parameter grid
- projected evaluation count
- Nexus calls/tokens
- remaining blockers
- tests
- commits
End with exactly one:
READY FOR FREEZE REVIEW
NEEDS DESIGN REVISION
BLOCKED
Do not freeze automatically.