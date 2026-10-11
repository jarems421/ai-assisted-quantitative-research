EXP002 — Final Blocker Resolution and Freeze-Candidate Preparation
EXP002 remains DRAFT.
This is the final pre-freeze blocker-resolution pass.
The objective is not to discover additional sophistication. The objective is to produce the simplest EXP002 design that is defensible enough to freeze.
No candidate performance.
No optimization.
No outer Validation/Test access.
No hypothesis freeze automatically.
Use Nexus Lake, SDK, MCP and minimal deterministic diagnostic backtests as needed.
Research-credit conservation is not a priority, but statistical degrees of freedom remain strictly constrained.
Candidate-formation cutoff remains 2020-12-31.
1. Preserve what is already settled
Do not reopen these design choices unless new evidence proves them invalid:
- locally reconstructed PIT ownership signals
- no native ownership fallback
- momentum = 180 / 365 calendar days
- insider window = 30 / 90 calendar days
- holdings = 20 / 40
- exactly 8 full-composite parameter cells
- monthly rebalance
- equal signal-rank weights
- equal security weights
- market cap removed
- ADV removed
- prospective rebalance gates excluded
- institutional cohort rule fixed rather than optimized
Do not introduce another optimization axis.
2. Resolve the historical price contract
This is now the most important technical gate.
Determine the exact Nexus/source fields and semantics for:
- nominal/unadjusted price
- split-adjusted price
- dividend-adjusted or total-return-adjusted price if present
- execution price used by Nexus daily backtests
- historical revision/vintage behavior
Use bounded pre-2021 corporate-action examples involving:
- ordinary stock with no action
- stock split
- cash dividend
- preferably ticker/security change
Establish a final contract for:
Price floor
Use a genuinely nominal historical price.
Momentum
Use a split-continuous historical price series that does not create artificial momentum jumps.
If dividend-adjusted pricing plus Nexus cash dividends would constitute double counting, do not use dividend-adjusted prices for portfolio equity.
Indicator-input adjustment and portfolio cash-flow treatment may differ if verified safe.
Document this distinction precisely.
If Nexus price-vintage provenance cannot be independently established but its historical series is deterministic and corporate-action behavior is empirically verified, classify the remaining vendor-revision risk explicitly as a limitation rather than automatically blocking EXP002, provided no evidence of look-ahead exists.
Do not demand impossible proof of vendor database immutability.
3. Certify custom disclosure transport end-to-end
We already know direct custom-indicator availableAt behavior worked in bounded diagnostics.
Build the production execution pattern, not the production alpha dataset yet.
Use artificial custom points representing:
- available before previous-day 21:00 cutoff
- available after cutoff
- Friday after cutoff
- weekend publication
- holiday-adjacent publication
- amendment superseding an earlier value
- unavailable/invalid companion value
The strategy must consume a precomputed decision-value stream rather than raw disclosure state at the trading open.
At each intended monthly trading session:
- decision value is generated from source state known by the preceding calendar-day 21:00 NY cutoff
- validity must be current for that exact decision
- stale numeric custom-indicator carry-forward must not resurrect an unavailable observation
- execution occurs at the intended next-session 09:30
Verify using event traces.
Add an invariant test:
signal_used_at_execution == signal_frozen_at_authorized_decision_cutoff
If the custom-indicator transport cannot guarantee missingness safely, use an explicit companion validity indicator and require validity == 1.
4. Resolve timestamp timezone semantics
The underlying Parquet timestamps lacked timezone annotations.
Establish their intended timezone from:
- dataset generation code
- schema documentation
- SEC filing timestamps
- known filing examples
Compare bounded source examples against known SEC acceptance/publication times where feasible.
The goal is to determine whether naive timestamps represent:
- UTC
- America/New_York
- another documented convention
Do not silently assume UTC.
If the original source pipeline clearly defines normalization semantics, record and test them.
Build conversion tests around:
- standard time
- daylight-saving time
This must be resolved before production ownership signal generation.
5. Insider source certification
The hypothesis is now based on:
Distinct Qualifying Insider Purchasers
not “strict open-market purchasers.”
Keep that terminology.
Complete only the minimum source-quality work needed to certify production reconstruction:
- owner CIK stability
- event/version identity
- correction chains
- P/A purchase qualification
- positive shares
- active version as-of T
- conflicting version handling
- unresolved ticker/security identity
Missing or ambiguous records remain unavailable.
We do not need perfect knowledge of every Form 4 semantic edge case to run EXP002; we need a reproducible and explicitly scoped signal definition.
Document excluded transaction types rather than broadening the signal.
6. Institutional production reconstruction
Finalize the institutional rule.
Primary signal:
matched-manager institutional holder-count change
Use:
- adjacent quarters
- 60-calendar-day minimum quarter maturity
- actual public availability by cutoff
- matched manager set across the two quarters
- positive security holding versus absence from a certified complete filing
- amendments only from their later public availability
Resolve:
- RESTATEMENT replacement
- NEW HOLDINGS additions
- overlapping amendments
- missing originals
- manager identifier stability
Keep ambiguous chains unavailable.
Quality threshold
The current software defaults of:
- 20 matched managers
- 95% of publicly known denominator
are not yet justified.
Use 2014–2020 coverage only, not returns, to determine whether these thresholds are sensible.
Prefer round, conservative thresholds.
If 95% causes excessive missingness, choose a lower coverage threshold only from observed source-coverage distributions and document the rationale.
This decision becomes fixed before performance.
Define maximum staleness from filing mechanics/quarter chronology, not returns.
7. Freeze a narrower historical universe that we can actually defend
Do not spend unlimited time reconstructing every U.S. security subtype.
Current proposal:
historical S&P 500 / GSPC membership
intersected with:
- certified common-stock listing span
- valid historical identity
- nominal price >= $5
with later-delisted/removed members retained historically.
Validate:
- historical constituent effective dates
- stable security/ticker mapping
- constituent removals
- later-delisted securities
- common-stock classification
We need historical membership, not today's S&P 500 list applied backwards.
If this construction is materially safer than ALL_US_STOCKS, make it final.
Do not block freeze merely because it is narrower than our original U.S.-equity ambition.
Update the hypothesis wording to refer to a:
historical large-cap U.S. equity universe
or more precise wording matching the verified universe.
8. Determine Development inception
Once price, ownership and universe contracts are final:
calculate the earliest date where every candidate has sufficient prior information for:
- 365-calendar-day momentum
- 90-day insider window
- two mature adjacent institutional quarters
- 60-day cohort buffer
- historical membership
Do not force 2015-01-01.
Choose the earliest defensible Development date from coverage alone.
Development end remains:
2020-12-31
Then redesign the expanding chronological folds around the actual start.
Prefer clean calendar-year held-out folds if possible.
If five folds are not methodologically sensible after the revised start, use four rather than weakening warmup requirements.
Do not access 2021+ data.
9. Deployment reserve
Investigate the repeated $15 allocation shortfall only enough to define a deterministic allocation convention.
We do not need the undocumented internal reserve formula if we can specify an allocation Nexus can reliably execute.
Test several non-performance diagnostic allocations, e.g.:
- 90%
- 92.5%
- 95%
solely to determine execution feasibility / reserve behavior.
Do not compare returns.
Choose the highest simple deployment percentage that consistently executes intended allocations without rejected orders under the diagnostic fixture.
This is an implementation constraint, not an optimized alpha parameter.
Freeze one value.
10. Slippage
Do not block EXP002 because Nexus lacks a native daily stock-slippage parameter.
Base simulation:
- existing 0.10% per-fill cost
Predeclare local additional transaction-cost stresses:
- +10 bps traded notional
- +20 bps traded notional
applied on each side in the independent robustness layer.
Label these as implementation-cost stresses, not literal slippage simulation.
This is sufficient for EXP002 v1 unless evidence shows the strategy has extreme turnover.
11. Corporate actions / delistings
Separate:
critical for signal correctness
from:
real-world execution approximation
Critical before freeze:
- splits must not create false momentum
- nominal price floor must remain meaningful
- dividend treatment must not double count
Noncritical but reportable limitation:
- exact economic recovery on every merger/delisting
- precise stock-vs-cash merger consideration
If Nexus has a deterministic delisting approximation but cannot reproduce every real corporate action perfectly, record the limitation.
Do not keep EXP002 DRAFT indefinitely attempting to reconstruct perfect merger accounting.
12. Historical lockbox
EXP001 has already exposed substantial 2025–2026 SPY information.
We therefore must not pretend that period is fully unseen.
Pick a historical workflow lockbox before any EXP002 performance testing, subject to available data.
Clearly label it:
workflow_held_out
not genuinely prospective.
The strongest evidence will remain future paper trading after freeze.
Candidate generation and Development end in 2020.
Outer Validation remains conceptually later than Development.
Choose exact Validation/Test boundaries now using chronology/data availability only, not outcomes.
Record prior human/model historical knowledge as a limitation.
Do not query their observations.
13. Statistical confirmation contract
Finish the inference rules before Development.
Primary scientific comparison:
full composite versus matched momentum-only
Primary effects:
- mean daily excess return difference
- zero-RF Sharpe difference
Require directional improvement in both.
Predeclare:
- paired block bootstrap
- block length
- draw count
- fixed seed
- valid one-sided null-centered test if inferential p-values are used
- Holm family and alpha
Do not claim significance unless the implementation is genuinely valid.
If a defensible p-value implementation would add excessive complexity, use predeclared bootstrap confidence intervals and label them descriptive uncertainty rather than forcing a significance claim.
Selection bias from the Development grid remains explicitly acknowledged.
14. Final evaluation plan
Recalculate total trials after the final Development inception/folds are known.
Preserve:
- all seven signal families
- explicit SPY benchmark
- equal-weight eligible-universe benchmark
- eight full-composite cells
- appropriately reduced cells for ablations
- complete trial ledger
Do not add hidden retries/trials.
Failed runs remain counted.
15. Final freeze-review package
Create/update:
- final_freeze_review.md
- spec.json
- provenance.json
- README.md
- custom_signal_spec.md
- custom_signal_manifest.json
- pit_audit.md
- universe_audit.md
- execution_audit.md
- nexus_runtime_audit.md
- evaluation_plan.json
- statistical/inference specification
Explicitly divide remaining uncertainties into:
CRITICAL
Would permit look-ahead, survivorship contamination or an undefined primary signal.
NONCRITICAL LIMITATION
Real implementation uncertainty that can be transparently stress-tested/reported.
A noncritical limitation must no longer automatically prevent freeze.
16. Audit
Run:
python -m src.research audit EXP002
You may update the audit implementation only if the previous gate is genuinely overbroad and the methodological distinction is documented.
Do not weaken any look-ahead, PIT, sealed-date or provenance protection simply to obtain PASS.
Run the complete repository test suite.
Commit and push.
Finish with a final table:
| Gate | PASS/FAIL | Evidence |
covering:
- ownership PIT
- custom transport
- timezone
- historical universe
- price/corporate actions
- execution timing
- institutional cohort
- missingness
- Development inception
- lockbox dates
- statistical contract
- immutable provenance
Then list all remaining noncritical limitations separately.
End with exactly one:
READY FOR FREEZE REVIEW
NEEDS DESIGN REVISION
BLOCKED
Do not freeze automatically.

The important change here
I’m deliberately giving Codex permission to stop treating every unknown as equally fatal.
Right now its audit is behaving almost like:
“Can we prove every feature of historical market data to courtroom standards?”

That sounds rigorous, but eventually becomes counterproductive.
For example, the fact that Nexus's exact internal deployment reserve formula isn't documented should not carry the same weight as:
“Can a 2020 decision accidentally use a 2021 amendment?”

The second one can invalidate the experiment.
The first one is mostly an execution-model limitation we can test, disclose and stress.
Likewise, exact merger consideration for every delisted company would be nice, but it doesn't need to keep EXP002 in DRAFT forever if our primary signal and price series are clean.
Where we currently stand
We've actually solved a lot:
- locally controlled point-in-time reconstruction exists;
- future amendments don't mutate earlier locally computed values by construction;    Pasted markdown
- Nexus custom indicators support explicit timestamp + availableAt;
- artificial runtime availability worked;
- the broken disclosure-lag method has been rejected;
- the primary grid is down to only 8 cells;
- market cap is gone;
- ADV is gone;
- native ownership signals are no longer required;
- the troublesome prospective turnover gates are gone.    Pasted markdown    Pasted markdown
So we're no longer redesigning the actual strategy every turn. We're mostly closing implementation contracts.
This should be the final serious pre-freeze pass.
If it returns READY FOR FREEZE REVIEW, send me the final review and we scrutinize the whole EXP002 spec once. Then you freeze it.
If it returns NEEDS DESIGN REVISION again, I would not automatically send another huge audit prompt. At that point we'll look specifically at the remaining failed gates and make a decision: fix them, simplify around them, or abandon EXP002 and move to a cleaner hypothesis.
That prevents this from turning into an infinite pre-backtest research project