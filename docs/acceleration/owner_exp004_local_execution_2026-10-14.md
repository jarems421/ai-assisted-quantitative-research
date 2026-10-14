You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
34c5b7595ddd30bc67627c4d61638a91a62e4efd

======================================================================
OWNER DECISION
EXP004 — RESUME WITH LOCAL DETERMINISTIC DEVELOPMENT EXECUTION
======================================================================

EXP006 and EXP007 are permanently closed as source-feasibility failures.

Do NOT:

reopen EXP006;
reopen EXP007;
select another event-study source;
start EXP008;
start Phase 4B;
run another external-repository audit;
perform another source-discovery campaign.

Resume:

EXP004 — Cross-Sectional Momentum

EXP004 already has a frozen/versioned economic design and complete Development
numeric QA.

Its economic hypothesis has NOT been tested.

The reason performance did not run is the independently documented Nexus
historical-symbol transport failure:

the publication/runtime route pruned the frozen historical population.

The owner now authorizes a LOCAL-ONLY deterministic Development execution path
for EXP004.

Nexus remains blocked.

No Nexus remote execution.
No Aurora.
No paper/live trading.

======================================================================
1. PRESERVE ALL EXISTING EXP004 HISTORY
======================================================================

Read and preserve at minimum:

experiments/EXP004/spec.json
experiments/EXP004/freeze_receipt.json
experiments/EXP004/freeze_versions/v002/
experiments/EXP004/research/final_freeze_review.md
experiments/EXP004/research/publication_runtime_audit.json
experiments/EXP004/research/development_authorization_20261011.md
reports/EXP004_development_report.md

docs/acceleration/historical_execution.md
docs/acceleration/phase3d_execution_reference.md

src/research/phase3d/execution.py
src/research/exp004_compile.py
src/research/exp004_execute.py
src/research/exp004_policy.py
src/research/exp004_streams.py
src/research/exp004_actions.py

and relevant tests.

Do NOT rewrite the Nexus failure.

It remains true:

historical-symbol transport through the tested Nexus path is uncertified.

The local route is a NEW separately versioned execution implementation.

======================================================================
2. ECONOMIC DESIGN IS FROZEN — DO NOT CHANGE IT
======================================================================

EXP004 remains:

Cross-sectional momentum only.

Momentum horizons:

180 elapsed calendar days
365 elapsed calendar days

Portfolio sizes:

Top 20
Top 40

Four cells:

M180_K20
M180_K40
M365_K20
M365_K40

Benchmarks:

monthly equal-weight eligible universe
explicit SPY buy-and-hold

Development:

2015-01-02 through 2020-12-31

Scored folds:

2017
2018
2019
2020

Outer Validation:

2021-01-01 through 2023-12-31

Historical Test:

2024-01-01 through 2024-12-31

Validation and Test remain CLOSED.

Costs:

$25,000 initial value
0.10% per fill
cash dividends
95% nominal deployment
fractional shares

Monthly cadence unchanged.

No new alpha parameters.
No new universe filters.
No market cap.
No ADV.
No exchange filter.
No liquidity threshold.
No present-day survivorship filter.

======================================================================
3. DO NOT MUTATE THE SYNTHETIC REFERENCE ENGINE IN PLACE
======================================================================

The current:

src/research/phase3d/execution.py

LocalReferenceAdapter is explicitly:

SYNTHETIC_ONLY
EXP999 only.

Preserve that contract.

Do NOT simply delete its guards.

Create a separately versioned production-research implementation for EXP004,
for example:

src/research/exp004_local_execution.py

or repository-consistent equivalent.

Suggested engine identity:

EXP004_LOCAL_REFERENCE_V001

It should reuse tested Decimal/ledger semantics where appropriate while keeping
the synthetic v001 implementation historically intact.

======================================================================
4. EXACT INPUT BOUNDARY
======================================================================

Use only the already-authorized immutable EXP004 Development inputs.

Current evidence includes:

28 price jobs
7,871,192 price rows
the existing split source
72 monthly Development panels
273,115 common eligible security-decisions

and the exact historical stable-ID/dated ticker bindings already used by the
successful Development input QA.

Verify hashes before execution.

No new current-symbol lookup.

No 2021+ observation.

No Validation/Test read.

No market-data source substitution merely for convenience.

======================================================================
5. LOCAL EXECUTION CONTRACT
======================================================================

Implement exactly the frozen semantics.

At each monthly rebalance:

decision information must precede execution;

execute at the frozen first eligible session OPEN;

use the exact frozen stable security identity;

rank descending by the frozen momentum score;

stable security ID is the deterministic tie-break;

select Top20 / Top40 as frozen;

equal weight selected positions;

95% nominal deployment;

long only;

fractional shares;

no leverage;

0.10% fee on every traded notional fill.

EW benchmark:

same common eligible population
same timing
same funding
same costs
same execution semantics.

SPY:

explicit frozen buy-and-hold contract.

======================================================================
6. CORPORATE ACTIONS MUST NOT BE HAND-WAVED
======================================================================

Preserve the existing split-safe signal contract.

The local execution path must establish exact treatment for any action relevant
to an actually held security during Development:

split
cash dividend
ticker rename
security/class transition
cash merger
stock merger
cancellation / terminal event

Do NOT:

forward-fill through disappearance;
drop dead securities;
replace historical symbol with today's symbol;
assume zero terminal value;
invent merger proceeds.

First inspect whether the required action evidence is already present in the
existing frozen/local source artifacts.

Do not launch a broad new data campaign.

If exact cash-dividend or terminal economics required for an actually held
position cannot be supported from the authorized source material:

STOP at:

LOCAL_EXECUTION_ACTIONS_BLOCKED

and report the exact affected holdings/events.

Do not weaken the frozen dividend policy.

======================================================================
7. EMPTY UNIVERSE / ENDED HISTORY
======================================================================

The frozen design says N=0 must liquidate to cash only when that execution
semantics is certified.

Implement and test it explicitly.

Ended historical securities must remain eligible while historically active.

The engine must fail if:

a held security disappears without a certified terminal instruction;

a ticker rename loses stable identity;

prices silently alter the frozen population;

or execution requires a current-survivor substitution.

======================================================================
8. PRE-PERFORMANCE ENGINE CERTIFICATION
======================================================================

Before calculating ANY EXP004 strategy performance:

create deterministic local fixtures covering:

monthly rebalance
Top20 / Top40
EW
SPY
fractional sizing
fees
sell-before-buy cash handling
split
cash dividend entitlement/payment
ticker rename with stable ID
cash merger
stock merger
cancellation with explicit recovery
ended security
empty-universe liquidation
insufficient cash
ambiguous identity rejection
missing price rejection

Where applicable reconcile exact Decimal results manually or against an
independent simple calculation.

Do not use real EXP004 performance to validate the engine.

======================================================================
9. POPULATION RECONCILIATION
======================================================================

For every real Development rebalance require exact equality between:

frozen eligible stable security IDs

and

locally executable stable security IDs.

Not just counts.

Exact IDs.

Any:

missing
extra
duplicate
substituted
ambiguous

security fails that decision.

No candidate can proceed on a pruned universe.

This is the defect that blocked Nexus and must not reappear locally.

======================================================================
10. PRE-PERFORMANCE LOCAL EXECUTION RECEIPT
======================================================================

Before any economic result exists, produce a compact certificate containing:

engine name/version/hash

frozen EXP004 spec hash

frozen methodology hash

Development source/input hashes

identity-binding hashes

corporate-action source hashes

calendar hash

fee/funding contract

population reconciliation status

fixture/test results

Validation/Test access count

performance_executed=false

Commit and PUSH this pre-performance execution certificate.

The economic specification remains unchanged.

If repository conventions require a freeze-version execution amendment, create
a new version which references the unchanged economic spec/methodology hashes
and changes only the execution-engine certificate.

Do not rewrite v001/v002 history.

======================================================================
11. DEVELOPMENT AUTHORIZATION
======================================================================

IF AND ONLY IF the local execution certificate passes:

Development execution is authorized.

No extra owner approval is needed.

Run exactly the already-frozen programme.

Scored folds:

2017
2018
2019
2020

for:

M180_K20
M180_K40
M365_K20
M365_K40
EW
SPY

Then run the six full-Development replays.

Do not access 2021+.

======================================================================
12. TRIAL LEDGER
======================================================================

Respect the existing EXP004 evaluation/trial budget.

Do NOT reset it merely because execution moved local.

Retain the prior historical Nexus transport diagnostic/failure accounting.

Record each actual frozen Development evaluation exactly once.

A software crash before a metric-producing completed evaluation should be
logged according to existing failure semantics, not silently deleted.

======================================================================
13. METRICS — USE THE FROZEN CONTRACT
======================================================================

For every momentum cell record the already-declared metrics:

total return

zero-RF Sharpe

Sortino

annualized volatility

maximum drawdown

turnover

participation

fold-by-fold results

performance relative to EW

performance relative to SPY

Primary selection statistic remains the frozen:

paired mean daily excess versus equal-weight universe

with the existing fold-consistency rules.

Do NOT invent a new significance threshold.

Do NOT change the selection rule after observing results.

======================================================================
14. EXISTING ADVANCEMENT CONDITIONS REMAIN
======================================================================

Retain the frozen conditions, including:

positive incremental performance versus EW;

required fold consistency;

adequate participation;

no critical execution/data failure;

complete four-cell surface.

An isolated winning cell must still be flagged as fragile.

Do not select only the maximum Sharpe.

Use the frozen deterministic tie-break.

======================================================================
15. ROBUSTNESS AFTER PRIMARY DEVELOPMENT
======================================================================

Only after the primary Development programme is complete, run the already
predeclared robustness analyses:

+10 bps per side

+20 bps per side

one additional execution-session delay

bull/bear descriptive decomposition

high/low-volatility descriptive decomposition

Do not create additional robustness tests.

======================================================================
16. VALIDATION AND TEST REMAIN SEALED
======================================================================

Do NOT access:

2021–2023 Validation

2024 Test

or later data.

No descriptive preview.

No source lookup requiring those outcome periods.

The end of this task is a Development verdict only.

======================================================================
17. DEVELOPMENT VERDICT
======================================================================

Use repository-consistent wording based on the frozen selection contract.

At minimum distinguish:

NO_EXP004_CANDIDATE_ADVANCES

EXP004_DEVELOPMENT_MIXED

EXP004_CANDIDATE_READY_FOR_VALIDATION_REVIEW

Do not authorize Validation automatically.

If a candidate advances:

STOP for owner review.

If none advances:

retain all results and STOP.

No redesign in this task.

======================================================================
18. NO NEW RESEARCH LOOP
======================================================================

Do NOT:

create EXP008

search for another dataset

change momentum horizons

change K

change costs

change universe

add factors

add ML

switch benchmarks

optimize execution delay

use today's symbols

retry Nexus

contact Nexus support

start paper/live

This task exists to answer the economic question that EXP004 was originally
built to answer.

======================================================================
19. TESTS
======================================================================

Add focused tests for:

real EXP004 input schema binding

stable-ID exact population equality

monthly rebalance

Top-K deterministic ties

95% deployment

fractional shares

fees

EW

SPY

split handling

cash dividend

rename

cash merger

stock merger

cancellation

ended security

empty-universe liquidation

no survivor substitution

no 2021+ reads

Validation/Test inaccessible

receipt hash stability

pre-performance certificate required before metric computation

synthetic reference implementation unchanged

Public CI must remain network-free.

======================================================================
20. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
all commits
hosted CI

LOCAL ENGINE:

engine version/hash
fixture results
population reconciliation
corporate-action coverage
blocked/unresolved action count
Development input hashes

DEVELOPMENT:

all 24 fold evaluations
all 6 full-Development replays

four-cell metrics
EW metrics
SPY metrics

primary paired excess results

fold consistency

participation

turnover

cost robustness

delay robustness

regime descriptions

selected candidate if any

trial/evaluation ledger

Validation accesses = 0
Test accesses = 0

Final status:

LOCAL_EXECUTION_BLOCKED

or

NO_EXP004_CANDIDATE_ADVANCES

or

EXP004_DEVELOPMENT_MIXED

or

EXP004_CANDIDATE_READY_FOR_VALIDATION_REVIEW

Then STOP.

======================================================================
21. OWNER INTENT
======================================================================

We have spent enough time selecting and certifying new event sources.

EXP004 already has:

a frozen economic question;
a historically defined universe;
complete Development price inputs;
a tiny four-cell parameter surface;
frozen benchmarks;
frozen costs;
sealed later periods.

Its previous failure was execution transport, not economic falsification.

Do not ask Nexus to preserve the historical universe.

Run the already-frozen research locally if the deterministic local engine can
be independently certified.

If local execution cannot preserve the frozen population or corporate-action
economics:

stop at that exact blocker.

If it can:

RUN DEVELOPMENT AND GIVE US THE RESULT.