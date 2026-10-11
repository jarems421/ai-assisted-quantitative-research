Create a new experiment:
EXP003
EXP002 is closed and must remain unchanged as a negative source-feasibility result.
Do not reuse EXP002 as a mutable continuation.
The new research question is:
Does combining medium-term price momentum with recent point-in-time qualifying insider-purchase activity improve robust out-of-sample performance relative to momentum alone?
This is a simpler two-signal experiment.
Do not include institutional/13F signals.
Reuse only methodology and infrastructure from EXP002 that passed audit:
- locally reconstructed PIT insider signal
- immutable custom-indicator transport
- availability-based decision logic
- missingness safeguards
- exact-session custom signal validity
- audited price/corporate-action conventions where applicable
- monthly cadence
- descriptive paired bootstrap framework
- Git/provenance rules
Do not inherit failed EXP002 assumptions:
- no native S&P 500 membership assumption
- no institutional signal
- no CUSIP omission-as-zero logic
- no uncertified ADV
- no market-cap filter
- no prospective rebalance gates
First task: universe feasibility only
Before candidate performance is tested, identify the simplest historically auditable equity universe available from Nexus/source data.
Prefer a universe defined from source fields that can actually be certified point-in-time.
Candidate possibilities may include:
- all securities with certified historical common-stock identity and valid historical price data
- a narrower exchange-listed subset if historical exchange status can be established cleanly
- another static-rule historical universe supported by stable identifiers
Do not use present-day membership backwards.
Do not require exactly 500 securities or another arbitrary target.
The universe must:
- use historical membership/identity
- retain later-delisted names where source history supports them
- exclude clearly non-common-equity instruments where auditable
- have deterministic inclusion rules
- avoid performance-based filtering
If exchange/OTC status cannot be certified reliably, document that and choose the narrowest defensible source-based rule rather than inventing a filter.
Proposed signal design
Momentum:
- 180 calendar days
- 365 calendar days
Insider:
- Distinct Qualifying Insider Purchasers
- 30 calendar days
- 90 calendar days
Holdings:
- 20
- 40
Monthly rebalance.
Equal signal-rank weights.
Equal security weights.
Use the existing audited disclosure cutoff/execution machinery.
Do not add additional alpha signals.
This gives at most:
2 × 2 × 2 = 8
full-composite cells.
Controls:
- momentum only
- insider only
- momentum + insider
- simple market benchmark if an appropriate explicit benchmark can be frozen
- equal-weight eligible-universe benchmark
Hypothesis
Primary comparison:
momentum + insider vs matched momentum-only
The composite must improve:
- mean daily net return
- zero-RF Sharpe
Lower drawdown alone does not confirm the hypothesis.
Chronology
Determine Development inception from actual warmup/source coverage only.
Development must end no later than:
2020-12-31
Outer Validation and historical Test must remain untouched during design.
Reuse the existing sealed-window philosophy, but do not automatically copy EXP002 dates unless coverage and chronology still support them.
Stop rule
Do not spend another large research cycle trying to make the universe perfect.
If a defensible historical universe can be established from existing source infrastructure, proceed toward freeze.
If not, return:
BLOCKED — UNIVERSE
and propose one materially simpler universe definition.
Do not open another general audit loop.
Outputs
Create the normal Research OS experiment structure for EXP003.
Produce:
- experiment spec
- provenance
- design README
- universe feasibility memo
- evaluation plan
- candidate/control definitions
Run the full test suite.
Commit and push.
Finish with:
- proposed historical universe
- Development start
- signal definitions
- parameter grid
- controls
- projected evaluation count
- remaining blockers
- whether EXP003 is:
READY FOR FREEZE REVIEW
NEEDS DESIGN REVISION
or
BLOCKED
Do not freeze automatically.

Why I prefer EXP003 over trying something completely new
We already spent a ton of effort validating the insider PIT pipeline.
Throwing that away now would be wasteful.
EXP003 lets us reuse the good parts of EXP002 while dropping the part that caused most of the trouble.
The experiment becomes much cleaner:
Momentum
   +
Insider purchase activity
   ↓
Does the extra information improve momentum?

That is scientifically easier to interpret too.
If it works, great.
If it doesn’t, we learn something meaningful.
And if it passes historical testing, it can go to paper.
Then after EXP003
I’d probably branch the research programme into separate families:
EXP003 — Momentum + Insider
EXP004 — Pure cross-sectional momentum
EXP005 — Earnings / fundamental revisions
EXP006 — Regime-aware allocation
EXP007 — Shorter-term event-driven
EXP008 — Ensemble of surviving strategies

And later, if Nexus improves its institutional identity provenance, we can revive the institutional component as a brand-new experiment, not retroactively reopen EXP002.
So the correct move now is:
archive EXP002, learn from it, simplify, and get EXP003 to an actual backtest much faster.

The system did what we built it to do. It killed a questionable experiment before the pretty equity curve could bias us.