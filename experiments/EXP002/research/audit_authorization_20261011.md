EXP002 Nexus research-credit authorization update
The owner has explicitly authorized use of the NexusTrade research-token allowance for rigorous EXP002 research.
Research-token conservation is no longer a blocking objective.
We are on a high-capacity Nexus plan and want to exploit Nexus's capabilities aggressively where doing so improves evidence quality, auditability, or research speed.
This does not authorize:
- live trading
- brokerage actions
- paper deployment
- opening outer Validation early
- opening historical Test
- changing frozen methodology after results
- unlimited strategy/data mining
For the pre-freeze EXP002 coverage/runtime audit, you are authorized to use up to 1,000 Nexus research tokens.
Do not purchase additional credits or exceed the included account allowance.
Use server previews/quotes where available and record actual token usage.
Resume the EXP002 coverage audit
The previous audit stopped because create_lake_query(...) might consume Nexus research credits. That restriction is now removed.
Use Nexus's actual read-only Lake/SDK/MCP capabilities as needed to establish whether EXP002 is valid before hypothesis freeze.
The hard candidate-formation cutoff remains:
2020-12-31
Absolutely no strategy-performance or signal/market observations after this date may be used during candidate formation.
Do not query outer Validation or Test.
1. Use Nexus Lake aggressively for data auditing
Run bounded read-only Lake queries needed to measure:
- yearly and monthly universe coverage
- insider coverage
- institutional coverage
- market-cap coverage
- price/volume coverage
- joint coverage
- missingness
- stale observations
- availableAt
- amendment/revision behavior
- historical listings
- delisted securities
- security type/subtype
- stable identifiers
- corporate-action metadata
Preserve every SQL query, job ID, returned row count, bounds and raw result hash.
Use parameterized SQL and explicit date predicates.
If a query unexpectedly returns post-2020 observations:
- quarantine it
- do not use those observations
- correct the query
- record the incident
2. Verify native Nexus behaviour, not just documentation
Resolve the current blockers using actual Nexus evidence wherever possible:
Insider
Audit:
- DistinctBuyers
- BuyCount
- BuyValue
- transaction code P
- availableAt
- filing/acceptance dates
- amendments
- zero versus absent data
Nexus documentation currently states that Insider Trades represent open-market Form 4 purchases/sales and that a trade counts from when the filing became public. Verify this against actual pre-cutoff data. 
Institutional
Audit:
- NewHolders
- NetHolderChange
- NetShareChange
- filing quarter
- public filing timestamp
- amendment behavior
- asynchronous filer timing
Nexus documentation states that level metrics use the latest quarter whose filing was public by the evaluation date and change metrics compare against the preceding quarter; amendments replace originals only once the amendment becomes public. Verify this where possible against source observations.
Momentum
Verify runtime support for:
PriceRateOfChange(asset, length, interval='Day')
Confirm that 126 and 252 completed-session lookbacks compile correctly without running performance searches.
Market cap / liquidity
Determine whether historical marketCap is defensibly point-in-time.
Determine the exact safe construction of trailing 20-session average dollar volume using completed bars.
If market cap is unsafe, identify and document a safer historical universe construction rather than forcing its inclusion.
Dynamic universe
Audit the actual historical behaviour of:
ALL_US_STOCKS
Determine:
- whether later-delisted stocks appear historically
- stable identifier handling
- historical membership
- ETF inclusion/exclusion
- ADRs
- preferred shares
- OTC securities
- other non-common-stock types
If Nexus cannot natively isolate historical common equities safely, design an explicit auditable filter.
3. Perform bounded runtime-semantic probes where Lake alone is insufficient
If an ambiguity can only be resolved by a Nexus simulation, you are authorized to run minimal diagnostic daily non-options backtests using pre-2021 data.
These must be diagnostic probes, not searches for profitable parameters.
Examples:
- confirming next-session execution timing
- verifying availableAt behaviour
- inspecting zero/missing indicator output
- checking dividend handling
- checking split handling
- checking delisted-security behaviour
- checking DynamicRebalance membership
- confirming completed-bar lag semantics
Use tiny deterministic fixtures and the shortest sufficient dates/universe.
Save full events for diagnostic probes where event traces are needed, remembering their retention window.
Never use the return/Sharpe of a diagnostic probe as research evidence.
4. Use structured Nexus tools wherever possible
Prefer:
- typed SDK calls
- structured MCP parameters
- direct Lake SQL
over natural-language Aurora calls for deterministic auditing.
Nexus's MCP documentation indicates structured inputs bypass the LLM for faster deterministic execution where supported.
Use Aurora only where reasoning is genuinely useful.
5. Obtain actual cost information
Use available previews/planning operations to establish:
- planned evaluations
- token estimates
- asset amplification
- fold amplification
- event costs
Record estimate versus actual consumption where Nexus returns it.
Cost is now an optimization variable, not a blocker.
Stop only if the 1,000-token pre-freeze audit ceiling would be exceeded.
6. Complete the coverage audit
Produce actual 2015–2020 statistics for:
- price-eligible universe size
- insider-covered securities
- institutional-covered securities
- market-cap-covered securities
- liquidity-covered securities
- joint-signal universe
- joint coverage percentage
Break this down at least annually and preferably quarterly/monthly when useful.
Determine the earliest defensible Development start from coverage only.
Do not choose dates based on strategy outcomes.
7. Establish missingness policy
Explicitly determine when Nexus means:
- true zero
- no qualifying filing
- missing observation
- stale observation
- unresolved ticker/security
- unavailable history
Write the exact EXP002 policy before strategy performance is examined.
8. Establish filing-delay policy
Quantify insider and institutional filing delays.
Decide, based only on availability mechanics and coverage:
- minimum usable timestamp
- next-session trading convention
- maximum allowed institutional staleness, if required
- amendment handling
Freeze these semantics before Development.
9. Establish execution semantics
Use minimal diagnostic backtests if necessary to verify:
- signal evaluation time
- order submission time
- fill timing
- fee treatment
- dividend treatment
- split treatment
- delisting behaviour
- daily bar availability
Do not infer these purely from EXP001 if EXP002's DynamicRebalance execution differs.
10. Prospective rebalance intelligence
Investigate Nexus's actual:
- planned turnover
- estimated cost
- expected benefit
- net benefit
metrics.
Determine their units, inputs, timing and whether they are safe to use before execution.
Do not add them to the primary strategy.
Decide only whether they are sufficiently clean to predeclare as a robustness/ablation mechanism.
11. Produce a final pre-freeze evidence pack
Update/create:
- coverage_audit.md
- coverage_summary.json
- pit_audit.md
- universe_audit.md
- execution_audit.md
- nexus_runtime_audit.md
- coverage_query_log.json
- cost_receipt.json
- spec.json
- provenance.json
- EXP002 README.md
Keep all large/raw responses under ignored raw storage.
12. Production-readiness check
Run:
python -m src.research audit EXP002
Do not weaken the audit.
If evidence invalidates an existing design assumption, revise it now while EXP002 is still DRAFT, with the evidence and reason recorded.
This is allowed because no candidate performance has been observed.
13. Tests and Git
Run the entire repository test suite, including EXP001 software-regression tests.
EXP001 outputs may be used only to verify that old software was not broken, never as EXP002 research evidence.
If tests pass, commit and push.
Final response
Report:
- Nexus queries/jobs executed
- research tokens estimated
- research tokens actually consumed if observable
- final usable Development start
- universe construction
- PIT status by signal
- missingness rules
- execution rules
- amendment/staleness rules
- joint coverage statistics
- remaining unresolved issues
- whether prospective rebalance metrics are safe
- tests passed
- commit SHA
End with exactly one:
READY FOR FREEZE REVIEW
NEEDS DESIGN REVISION
BLOCKED
Do not freeze EXP002 automatically.

And going forward, I’d loosen the budgets even further
I don't want the Research OS constantly interrupting you over 10–30 tokens.
For context, Nexus currently says a daily non-options backtest is free. Daily optimization is about 0.02 token/evaluation, with a minimum of 2 tokens per optimization job. So even 500 daily evaluations are only ~10 tokens at the headline rate before the documented asset factor/minimums. NexusTrade
That means the scarce resource isn't really Nexus compute.
Our scarce resource is clean statistical evidence.
So I'd use Nexus hard:
- thousands of coverage/data-quality checks → absolutely
- large predeclared parameter sweeps → yes
- extensive walk-forward folds → yes
- multiple cost/execution stresses → yes
- many bootstrap/robustness analyses → yes
- Aurora premium models for difficult research → yes
- full events for finalists/diagnostics → yes
- corpus mining for hypotheses → yes
But not:
- “run 20,000 random strategies and give me whichever made the most”
- changing parameter grids after seeing results
- repeatedly reopening Test
- adding signals because Validation looked bad
Nexus itself warns that optimization can produce spectacular backtests that fail live, and explicitly recommends train/validation separation and simplicity. NexusTrade
We can also use Aurora harder
Aurora is explicitly designed to execute multi-step sequences of research → strategy creation → backtest → optimization autonomously. NexusTrade
Once a hypothesis is frozen, I'm much happier with us giving Aurora significant budget to:
- independently critique it
- investigate failure modes
- inspect companies/signals
- interpret unusual results
- diagnose why controls differ
- evaluate strategy mechanics
And for deterministic operations, Nexus MCP's structured mode bypasses the LLM, which is exactly what we want for automated orchestration. NexusTrade
So yes: use the Max/Unstoppable capacity properly.
The new principle should be:
Be lavish with computation and verification. Be extremely stingy with degrees of freedom.

That's how we use Nexus far more aggressively and drastically improve the quality instead of just generating more backtests.