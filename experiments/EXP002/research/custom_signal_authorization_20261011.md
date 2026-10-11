EXP002 — Replace Ambiguous Native Signals With Audited Custom PIT Signals
EXP002 remains DRAFT. No candidate performance has been observed.
The previous audit has shown that our exact economic hypothesis is more precise than the semantics of several native Nexus indicators.
We will therefore prefer locally reconstructed, point-in-time disclosure signals published to Nexus as custom indicators, if that can be done safely and reproducibly.
Do not backtest EXP002 candidates yet.
Do not optimize.
Do not access outer Validation/Test.
Do not freeze the hypothesis.
The candidate-formation cutoff remains 2020-12-31.
1. Insider signal: own the definition
Stop relying on native DistinctBuyers as the primary EXP002 insider signal unless exact native semantics become fully equivalent to our desired definition.
Build a local point-in-time series representing:
distinct qualifying insider buyers per security over a trailing availability window
Requirements:
- use SEC/Form 4 source rows
- filter to nonderivative purchase transactions
- use transaction code P
- deduplicate transaction legs by stable filing/row identity
- deduplicate people by stable owner CIK
- preserve joint-owner filings without multiplying transaction counts
- use availableAt, never transaction date, to determine when a record enters state
- amendments must only alter state from their own later availableAt
- ambiguous filing chains are excluded rather than guessed
- unresolved security identities are excluded
Because code P can include private purchases, do not label the signal “open-market buying” unless the source provides a verified discriminator.
Rename the research concept if necessary to something accurate such as:
Distinct Qualifying Insider Purchasers
or another precise term supported by source semantics.
This is allowed because no performance has been observed.
Preserve the proposed windows:
- 30 calendar days
- 90 calendar days
Produce deterministic daily/as-of values.
2. Institutional signal: own the cohort definition
Do not use native NetHolderChange as the primary EXP002 institutional signal.
Build the previously audited matched-manager cohort signal locally.
Proposed mechanics:
- quarter Q becomes usable only after:
  - a fixed 60-calendar-day buffer after quarter end, AND
  - the relevant filing is actually public by the decision cutoff
- use only managers with unambiguously reconstructed eligible filings in both adjacent quarters
- compare holders within the same matched-manager set
- count current holders minus prior holders
- missing filing != zero holding
- a certified complete filing that omits a security may establish no holding
- amendments affect state only from their later availableAt
Preserve:
- excluded managers
- cohort coverage %
- matched manager count
- stale age
- amendment state
Emit the final scalar institutional score only when minimum data-quality rules are satisfied.
Otherwise emit missing/unavailable, never zero.
3. Custom indicator transport
Inspect the installed Nexus SDK/MCP custom-indicator interfaces.
Determine the safest supported representation for these reconstructed signals.
Prefer a point-in-time/disclosed representation using fields equivalent to:
- ticker/security identity
- observation timestamp
- availableAt
- value
- point semantic such as disclosed
Use actual SDK declarations, not guessed syntax.
Build an upload/export adapter but do not upload post-2020 values.
For Development, create a versioned dataset covering only the authorized Development/warmup period.
Every custom-data version must have:
- dataset version
- code version / Git SHA
- source hashes
- generation timestamp
- row count
- minimum and maximum source availableAt
- minimum and maximum emitted timestamp
- methodology hash
Once frozen, custom data must be immutable.
4. Eliminate information leakage by construction
Build a property test showing:
For every emitted signal value at decision time T:
all contributing source rows have availableAt <= T
Add adversarial tests where:
- an amendment arrives later
- a filing arrives after market close
- a filing arrives on a weekend
- an institutional filing arrives late
- a manager disappears between quarters
- a security identity changes
Verify that earlier values do not change when future records are added.
This should become a core Research OS PIT invariant.
5. Decision/execution convention
Retain the proposed decision convention:
21:00 America/New_York on the calendar day preceding the intended tradable session
with execution:
next intended trading session at 09:30 New York
But before freeze, prove it end-to-end using a minimal custom indicator diagnostic.
Construct an artificial disclosed signal that becomes available at known times:
- before cutoff
- after cutoff
- weekend
- holiday-adjacent
Run minimal daily Nexus diagnostics.
Confirm via event logs which signal becomes visible and when fills occur.
Include:
- normal weekday
- Monday after weekend
- early-close week if feasible
- DST boundary if feasible
Do not evaluate profitability.
6. Simplify the universe further if needed
The primary universe should not depend on any field we cannot certify.
Keep:
- historical common-stock identities
- price >= $5
- historical listing validity
- delisted histories
For liquidity, investigate whether the source provides a compatible price/volume pair.
Prefer, in order:
1. verified compatible historical price × volume units
2. a directly stored historical dollar-volume field
3. a simpler auditable liquidity proxy
If none is defensible, remove the dollar-volume eligibility filter from the primary hypothesis rather than using a technically dubious one.
Do not invent another replacement filter based on performance.
7. Resolve corporate-action price basis
This is now a critical gate.
Determine exactly what price series should feed:
- momentum
- price floor
- liquidity calculation
We need to avoid both:
- split discontinuities
- adjusted-price + dividend-cash double counting
Inspect Nexus/source declarations and bounded pre-2021 cases.
If necessary, use separate fields:
- one total-return-safe/adjusted field for indicators
- one nominal/unadjusted field for price floor
But only if documented and empirically verified.
Write the final price/corporate-action contract explicitly.
8. Historical exchange/security-type construction
Finish the explicit historical universe reconstruction without depending on ALL_US_STOCKS.
Required classifications:
- common stock
- ETF
- ADR
- preferred
- fund
- OTC
- exchange-listed
- unknown
Prefer security-master/listing history over current ticker metadata.
Preserve exclusions by month and reason.
If historical exchange status genuinely cannot be reconstructed safely, document that limitation and choose a reproducible narrower universe supported by the available history.
9. Warmup and Development inception
Extend only the minimum required pre-2015 historical data needed for:
- 365-calendar-day momentum
- 90-day insider window
- institutional prior eligible cohort
- liquidity lookback if retained
Then determine the earliest Development start solely from:
- complete signal warmup
- universe availability
- source PIT validity
If January 2015 cannot be certified, move the Development start later.
Do not force 2015 merely to preserve the old draft.
10. Finalize parameter grid
Assuming the audited custom signals survive:
Primary full-composite grid should be only:
- momentum: 180 / 365 calendar days
- insider: 30 / 90 calendar days
- holdings: 20 / 40
= 8 full-composite cells
Institutional cohort rule:
- fixed
Rebalance:
- monthly fixed
Liquidity:
- fixed if retained
Signal weights:
- equal fixed
Deployment:
- fixed after execution-buffer reconciliation
No additional optimization axis may be introduced without a new pre-performance design revision.
11. Deployment-buffer audit
Reconcile why the prior CQB/SPY diagnostic targeted $50 but filled approximately $42.50.
Establish:
- Nexus buying-power reserve
- configured deployment fraction
- fee buffer
- rounding
- DynamicRebalance allocation behavior
Set a primary deployment percentage that is actually achievable and stable.
Do not select it based on return.
12. Slippage policy
Determine what daily stock slippage Nexus can model.
If native slippage is unavailable or insufficient:
- keep the base engine run explicit about this
- predeclare an independent conservative execution/cost stress
Do not pretend 0.10% fee represents every implementation cost.
13. Keep prospective rebalance metrics out
Do not spend further design complexity on:
- expected benefit
- net benefit
- estimated cost gating
for the primary EXP002 strategy.
The server incompatibility and unresolved lineage are sufficient reason to exclude them.
They can be revisited in a different experiment.
14. Build final pre-freeze evidence
Update:
- design_revision.md
- spec.json
- provenance.json
- pit_audit.md
- universe_audit.md
- execution_audit.md
- nexus_runtime_audit.md
- coverage_summary.json
Create:
- custom_signal_spec.md
- custom_signal_manifest.json
- tests for deterministic point-in-time reconstruction
Raw source/custom-data files remain ignored.
15. Audit
Run:
python -m src.research audit EXP002
Do not weaken it.
READY FOR FREEZE REVIEW now requires:
- locally controlled PIT insider signal
- locally controlled PIT institutional signal
- immutable/custom-data provenance
- safe historical universe
- explicit price/corporate-action contract
- verified disclosure cutoff
- verified next-session execution
- warmup-supported Development start
- fixed missingness policy
- fixed 8-cell primary grid
- deployment semantics understood
- no remaining critical leakage issue
Run the complete test suite.
Commit and push all verified work.
End with exactly:
READY FOR FREEZE REVIEW
NEEDS DESIGN REVISION
or
BLOCKED
Do not freeze automatically.

Why I think this is the right move
We have already learned enough to know that simply piling more diagnostic queries onto native signals is starting to hit diminishing returns.
The institutional signal we actually want is not Nexus's native NetHolderChange; it is a specifically reconstructed matched-manager change between sufficiently mature public filing cohorts.    Pasted markdown
Likewise, our strict “open-market buyer” language isn't supported because the source audit found P also captures private purchases.    Pasted markdown
So rather than weaken the methodology to fit a convenient API, we should make the data pipeline fit the methodology.
That also has a big long-term benefit: if we eventually discover something interesting, we'll be able to explain exactly what the signal means, exactly when each datum became available, and reproduce it outside Nexus.
One thing I would change in the hypothesis wording
I would no longer say:
“corporate-insider accumulation”

if we mean only strict open-market purchases, because we can't currently prove that classification.
I'd probably freeze something closer to:
Does combining medium-term price momentum with recent point-in-time qualifying insider-purchase activity and matched-cohort institutional holder accumulation improve robust out-of-sample performance relative to momentum alone?

Slightly uglier English, but vastly more defensible.
And importantly, this isn't goalpost-moving after seeing results. There are still no candidate performance results. The whole point of DRAFT is to discover these data problems now