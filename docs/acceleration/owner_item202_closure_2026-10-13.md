You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
8e8ad0c7f676d916832bfaae4e0fb1ff17adf492

======================================================================
OWNER INSTRUCTION
ITEM 2.02 FREEZE CLOSURE + DEVELOPMENT
======================================================================

Phase 4A-I is complete.

Do NOT start another architecture phase.
Do NOT search for another hypothesis.
Do NOT audit more external repositories.
Do NOT reopen procurement, FDA, merger, EXP004 or EXP005.
Do NOT build Phase 4B.
Do NOT use Nexus historical execution.

The current concrete candidate is:

SEC_ITEM202_SOURCE_DECLARED_DISCLOSURE

from:

docs/acceleration/next_experiment_design_candidate.json
docs/acceleration/next_experiment_design_candidate.md

Current state:

READY_FOR_EXPERIMENT_FREEZE_REVIEW

but:

EXECUTABLE_FREEZE = BLOCKED

The owner now authorizes bounded closure of the known scientific blockers.

IF AND ONLY IF all mandatory gates genuinely pass:

1. register the next experiment as EXP006;
2. freeze its exact specification;
3. acquire/use DEVELOPMENT market data only;
4. execute the frozen Development evaluation;
5. report the Development result honestly;
6. STOP without opening historical confirmation.

This instruction therefore authorizes Development performance only AFTER
the experiment has been fully frozen.

No performance may be inspected during gate closure or design decisions.

======================================================================
1. READ CURRENT STATE FIRST
======================================================================

Before mutation inspect:

git status
git branch --show-current
git rev-parse HEAD
git remote -v

Then read at minimum:

AGENTS.md
README.md

docs/acceleration/master_plan.md
docs/acceleration/phase4a_integration_report.md
docs/acceleration/phase4a_source_contract_prototype.md
docs/acceleration/phase4a_researchability_v2.json
docs/acceleration/phase4a_researchability_v2_report.md
docs/acceleration/next_experiment_design_candidate.json
docs/acceleration/next_experiment_design_candidate.md
docs/acceleration/phase4a_integration_validation.json

src/research/surfaces/sec.py
src/research/source_first_v2.py
src/research/proof_v2.py

src/research/store.py
src/research/spec.py

src/research/phase3d/execution.py
src/research/inference_feasibility.py
src/metrics/performance.py

experiments/_template/spec.schema.json

and relevant tests.

Repository state is authoritative.

Preserve all historical experiment and source artifacts.

======================================================================
2. OWNER ADOPTION OF CURRENT DESIGN PARAMETERS
======================================================================

The following proposals are now OWNER-APPROVED for EXP006 design work,
subject to the scientific gates below.

Feature:

SEC original 8-K with source-declared Item 2.02,
corroborated where required by the original primary filing.

Estimand type:

PREDICTIVE

No causal claim.

Development:

2015-01-01 through 2020-12-31

Historical workflow-held-out confirmation:

2021-01-01 through 2026-09-30

DO NOT OPEN THIS CONFIRMATION PERIOD DURING THIS TASK.

Evaluation horizon:

20 regular trading sessions

No horizon search.

Base transaction cost:

10 bps per side
20 bps round trip

Future predeclared robustness:

20 bps per side
40 bps round trip

and:

+1 eligible-session entry delay

Do not run confirmation robustness now.

Trial ceiling:

12 total evaluations under the existing proposal.

No feature search.
No horizon search.
No threshold search.
No model search.
No post-result redesign in this pass.

Materiality proposal is adopted pre-performance:

estimated paired net 20-session mean difference
>= 0.50 percentage point

AND

positive two-sided 95% lower confidence endpoint against zero.

This is a prospective gate.
Do not change it after observing returns.

======================================================================
3. AVAILABILITY POLICY FOR THIS EXPERIMENT ONLY
======================================================================

Do NOT activate old v002/v003 globally.

Create a new EXP006-specific availability contract.

The owner approves this conservative modeled eligibility rule:

An SEC filing may first become executable at the first regular NYSE session
OPEN strictly AFTER the SEC "date filed" calendar date.

Never execute on the filing date itself.

Examples:

filed Monday -> earliest Tuesday regular open
filed Friday -> earliest next regular NYSE open
filed weekend/holiday -> earliest regular open after that date

This is:

MODELED_CONSERVATIVE_ELIGIBILITY

NOT:

OBSERVED_FIRST_PUBLIC_TIMESTAMP

Before adopting it in the frozen experiment, verify from authoritative SEC
documentation that the declared filing date cannot precede the filing's
acceptance/public filing date in a way that would make the next-session rule
look into the future.

If that semantic cannot be supported:

STOP at AVAILABILITY_BLOCKED.

Do not invent a timestamp.

Keep separately:

economic event date
SEC filing date
acceptance timestamp where available
modeled eligibility
retrieval time

======================================================================
4. SOURCE COVERAGE — SCALE THE SEC CONTRACT
======================================================================

The Q1 2020 prototype is insufficient for Development.

Build the full declared Development source census for:

2015-01-01 through 2020-12-31

Forms:

8-K
8-K/A

Population must be based on SEC source enumeration BEFORE Item filtering.

Preserve:

CIK
accession
source path
form
filed date
cofilers
shared accessions
amendment/version state
missing/unavailable documents
PAC/deletion evidence where available

Do not define the population from:

today's tickers
current surviving issuers
price-data availability
Item 2.02 presence
future returns
future corporate survival

======================================================================
5. ACQUISITION STRATEGY — DO NOT FETCH TENS OF THOUSANDS OF BODIES
======================================================================

Prefer official SEC bulk/index/submission surfaces.

Reuse existing archives.

Use:

quarterly/daily indexes
official bulk submission metadata
official accession metadata
original filings only where necessary

before considering per-document acquisition.

The objective is:

complete source-defined enumeration
+
reliable Item 2.02 classification

not:

download every filing body.

If official structured SEC metadata provides historical Item declarations,
audit its semantics against originals before relying on it.

Freeze the classifier/source contract BEFORE market returns are loaded.

======================================================================
6. ITEM 2.02 CLASSIFICATION VALIDATION
======================================================================

Validate scalable Item 2.02 classification against a deterministic primary-file
sample across the Development years.

Maximum primary-body semantic audit:

48 filings

Use a frozen mechanically selected sample covering:

years
quarters
declared Item 2.02
declared non-Item 2.02
8-K/A where relevant

Selection may stratify on the SOURCE LABEL being validated.

It may not use:

issuer fame
future returns
stock survival
price history

Ambiguous cases remain UNKNOWN.

Never infer:

no Item 2.02

merely because a document is missing.

Produce classification precision/coverage counts.

If scalable source metadata materially disagrees with original filings:

STOP or use a primary-document method that remains computationally realistic.

======================================================================
7. PAC / VERSION / MISSINGNESS CHECK
======================================================================

The current Q1 prototype checked only three dates.

Extend reconciliation enough to determine whether the Development denominator
can retain historically referenced filings despite current index rebuilds,
corrections or removals.

Prefer historical daily/feed/oldload references where supported.

Do not claim an untouched historical SEC vintage unless one actually exists.

Required output:

what population the contract certifies;
what it does not certify;
count of references without available original bytes;
count of amendments;
count of conflicting/versioned records;
count of unresolved states.

Do not silently drop any category.

======================================================================
8. HISTORICAL ISSUER -> SECURITY/CLASS IDENTITY
======================================================================

Build ONLY the minimum identity layer needed for EXP006.

Do not build the full Phase 4B graph.

For each qualifying source event, determine the dated listed equity class that
could actually have been traded at execution time.

Preferred evidence hierarchy should use contemporaneous evidence such as:

SEC cover-page trading symbol / exchange information
contemporaneous 10-Q / 10-K / 8-K metadata
existing approved identifier sources
OpenFIGI only where its result can be dated/validated
configured market-data metadata where historically explicit

Never use:

today's ticker alone
current company lookup alone
surviving-security-only joins

Keep separately:

issuer CIK
legal filer
security/class
exchange
ticker
effective date span
provider identifier

Cofilers must not become duplicate independent trades.

Unresolved mappings stay UNAVAILABLE.

======================================================================
9. ENDED / RENAMED / DELISTED SECURITIES
======================================================================

No survivorship shortcut is allowed.

Before Development performance:

identify every qualifying Development event whose mapped class:

renamed
changed ticker
merged
delisted
converted
ceased trading
or otherwise ended

inside the required price/execution path.

Such observations cannot disappear.

For any position ending before the scheduled 20-session exit:

resolve the actual economic terminal path using documented cash/stock/corporate
action treatment.

If a required terminal path cannot be valued:

mark it unresolved.

If unresolved terminal paths would have to be dropped to calculate performance:

BLOCK EXECUTION.

Do not substitute last price forever.
Do not assign zero unless zero is economically evidenced.

======================================================================
10. MARKET DATA PROVIDER CERTIFICATION
======================================================================

Inspect existing configured providers and local credentials WITHOUT PRINTING OR
COMMITTING SECRETS.

Prefer an already configured source that can support:

historical OHLC/open prices
splits
dividends / total-return treatment
ticker changes
ended securities where required
stable reproducible requests

No purchase or subscription upgrade is authorized.

No Nexus execution.

Do not use a convenient current-survivor dataset merely to make the experiment
run.

Before bulk Development acquisition, run a tiny provider certification sample
covering:

normal security
split/dividend case
ticker rename if available
ended/delisted case if available

Archive request/provider provenance under existing raw-data rules.

If no existing provider can preserve the experiment population honestly:

STOP at MARKET_DATA_BLOCKED.

======================================================================
11. EXECUTION CONTRACT
======================================================================

Extend/reuse the independent local execution machinery.

Do not rely on Nexus.

EXP006 execution:

entry =
first approved eligible regular-session OPEN

exit =
regular-session OPEN exactly 20 trading sessions after entry

Base costs:
10 bps each side

Corporate actions must be economically consistent.

Use Decimal or existing exact money/quantity semantics where appropriate.

Explicitly handle:

splits
dividends if held through entitlement
ticker changes
cash consideration
stock consideration where supported
delisting/terminal value
missing sessions

Do not forward-fill through terminal events.

Create deterministic synthetic and tiny real-data reconciliation tests BEFORE
running Development.

======================================================================
12. BENCHMARK / MATCHING CONTRACT
======================================================================

The design candidate requires a contemporaneous non-Item-2.02 baseline.

Formalize the exact deterministic matching algorithm BEFORE loading outcome
returns.

Use only information available before the event.

Matching dimensions must remain the predeclared concepts:

industry
size
momentum
calendar proximity

Do not add predictive variables.

Do not optimize weights after returns.

No future-outcome matching.

No same issuer as its own control unless explicitly justified in the frozen
contract.

No Item 2.02 control.

Use a deterministic tie-break.

Missing valid match => UNAVAILABLE.

SPY remains a descriptive comparator, not a second formal discovery claim.

The exact matching rule must be hashed/frozen before real post-event returns
are calculated.

======================================================================
13. INFERENCE — SOLVE BEFORE PERFORMANCE
======================================================================

Do not repeat the EXP005 inference failure.

Use the REAL source/event geometry but SYNTHETIC outcomes only.

The method must account for:

repeated issuers
calendar clustering
earnings/reporting seasons
industry shocks
persistent common factors
20-session overlap
unequal numbers of events per month/year
heterogeneity
missing matches
partial-year support

You may compare at most THREE candidate inference methods.

This is a method-calibration exercise, not a strategy search.

Potential classes include:

calendar/block bootstrap
multiway clustered procedures
calendar-time portfolio inference
or another method justified by implementation and statistical literature.

Do not choose based on power alone.

Primary selection criteria:

1. null rejection near alpha = 0.05
2. confidence coverage near 95%
3. robustness to persistent common-factor worlds
4. compatibility with actual repeated-issuer/calendar geometry

Power is secondary.

Retain failed methods.

Freeze the winning method BEFORE Development returns are loaded.

If no method calibrates defensibly:

STOP at INFERENCE_BLOCKED.

======================================================================
14. POWER / EFFECTIVE SAMPLE GEOMETRY
======================================================================

Using no real post-event returns, report:

raw events
unique issuers
events per issuer
events per date/month/year
overlap geometry
control-match coverage
effective dependence geometry

Run synthetic power checks for at least:

0 effect
+0.50 percentage point effect
+1.00 percentage point effect

under the adopted inference method.

Do not convert raw filing count into independent N.

If the materiality threshold is effectively untestable under the available
geometry:

STOP before freeze.

======================================================================
15. PRE-FREEZE REVIEW
======================================================================

Only after Sections 3–14 pass:

compile the final EXP006 candidate through Proof v2.

It must include hashes for:

population
source census
classification contract
availability
identity
market-data provider
benchmark matching
execution
costs
inference
trial family
code
environment

At this exact moment:

performance_executed = false

No Development post-event returns may have been inspected.

Expected status:

SCIENTIFICALLY_READY_FOR_FREEZE

If not:

STOP.

======================================================================
16. REGISTER AND FREEZE EXP006
======================================================================

If all gates pass, create:

experiments/EXP006/spec.json

using the canonical schema.

Suggested experiment name:

EXP006_SEC_ITEM202_PREDICTIVE

or repository-consistent equivalent.

Record:

one feature
one horizon
one primary benchmark
one inference method
one Development period
one held-out confirmation period
costs
materiality
trial ceiling
availability rule
identity contract
execution contract
source hashes
code hashes

Freeze it.

Commit the frozen experiment specification BEFORE Development performance.

This commit must visibly predate any Development result artifact.

Push the freeze commit if repository workflow permits.

======================================================================
17. AFTER FREEZE — DEVELOPMENT ONLY IS AUTHORIZED
======================================================================

ONLY after EXP006 is frozen:

load/acquire required market outcomes for:

2015-01-01 through 2020-12-31

Do not access post-2020 outcome data for analysis.

Historical confirmation:

2021-01-01 through 2026-09-30

must remain workflow-held-out.

Do not summarize it.
Do not compute it.
Do not preview it.
Do not run descriptive statistics on its returns.

Modern AI knowledge of historical events is acknowledged, but the stored
outcomes must remain unopened.

======================================================================
18. RUN EXACTLY THE FROZEN DEVELOPMENT EVALUATION
======================================================================

Calculate the frozen primary estimand once.

No parameter tuning.

No alternative horizon.

No new feature.

No new matching rule.

No alternative inference method after seeing results.

No dropping inconvenient observations.

No "quick check" of confirmation.

Report at minimum:

eligible source events
mapped securities
matched pairs
unresolved exclusions by reason
unique issuers
calendar distribution

gross 20-session event return
gross control return
gross paired difference

net event return
net control return
net paired difference

confidence interval
p-value where defined

materiality threshold result

SPY descriptive comparator

turnover/exposure statistics where relevant

cost impact

Do not call excess return "alpha" unless the frozen estimand genuinely supports
that wording.

======================================================================
19. DEVELOPMENT VERDICT
======================================================================

Use one of:

DEVELOPMENT_FAIL

DEVELOPMENT_MIXED

DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS requires the predeclared statistical AND materiality conditions.

A weak positive number is not a pass.

A statistically significant but economically sub-material result is not a pass.

A material point estimate with confidence interval crossing zero is not a pass.

If it fails:

retain it.

Do not redesign Item 2.02 during this task.

If it passes:

do NOT open confirmation.

The next owner decision would be whether to authorize the one historical
workflow-held-out confirmation under the already frozen contract.

======================================================================
20. TRIAL ACCOUNTING
======================================================================

Record every real performance evaluation against the existing ceiling.

Synthetic inference calibration does not become unbounded method search.

Do not reset the trial budget.

Do not hide failed acquisition/execution attempts.

The first Development result must remain in history even if something later
needs fixing.

A genuine implementation bug may be corrected only with:

documented bug
preserved original output
new version
clear statement that the rerun is a corrected execution, not a fresh trial

======================================================================
21. REQUEST / COST DISCIPLINE
======================================================================

Prefer bulk SEC files and batched provider calls.

Do not perform thousands of individual document requests when an official bulk
surface exists.

No paid purchase.

No account upgrade.

No remote Aurora.

No Orbis scraping.

No browser automation around denials.

Respect source terms and pacing.

Record request totals separately for:

SEC source certification
identity source
market data
GitHub engineering operations

======================================================================
22. TESTS
======================================================================

Add tests for at least:

full-period census determinism
8-K / 8-K/A version retention
Item 2.02 classification
missing-document UNKNOWN behavior
cofiler deduplication at trade level
availability next-session policy
holiday/weekend calendar behavior
dated ticker/class mapping
ticker rename
split
dividend
delisting/terminal handling
no survivor filtering
benchmark deterministic matching
no future fields in matching
inference null calibration
persistent common-factor stress
overlapping-horizon stress
trial counting
Proof v2 freeze rejection before gates
held-out access prohibition
Development-only market-data boundary
historical artifacts unchanged

Public CI must remain network-free using fixtures/fake transports.

======================================================================
23. DO NOT OVERENGINEER
======================================================================

This is a closure-and-experiment task.

Do not:

build a generalized corporate graph
build a new research platform
add more source types
audit more GitHub repositories
introduce ML
add an LLM strategy selector
rewrite the whole README
design Phase 5
design live trading
create a generalized market-data warehouse

Implement only what EXP006 needs.

======================================================================
24. STOP CONDITIONS
======================================================================

Stop before performance if any mandatory condition fails:

source census cannot be made defensible

Item 2.02 classification is unreliable

availability rule is unsupported

historical class identity is materially survivor-biased

terminal positions cannot be valued

market provider cannot preserve required securities

benchmark matching requires hindsight

no inference method calibrates acceptably

materiality threshold is effectively untestable

Proof v2 cannot certify the final design

held-out isolation cannot be enforced

Stop and report the exact blocker.

Do not route around it.

======================================================================
25. REQUIRED ARTIFACTS
======================================================================

Use repository conventions, but likely create:

docs/acceleration/exp006_freeze_review.md
docs/acceleration/exp006_source_coverage.json
docs/acceleration/exp006_availability_contract.json
docs/acceleration/exp006_identity_certificate.json
docs/acceleration/exp006_market_data_certificate.json
docs/acceleration/exp006_execution_certificate.json
docs/acceleration/exp006_inference_certificate.json

experiments/EXP006/spec.json

and, only if frozen and Development runs:

reports/EXP006_development_report.md
data/processed/EXP006_.../

Do not create redundant documentation merely for ceremony.

Prefer compact machine-readable receipts plus one clear human report.

======================================================================
26. GIT SEQUENCING
======================================================================

The important audit boundary is:

PRE-PERFORMANCE FREEZE COMMIT

before:

DEVELOPMENT RESULT COMMIT

Use logical commits.

At minimum there must be a distinct pushed commit containing the frozen EXP006
spec before any commit containing Development performance.

Never amend/rewrite that freeze commit afterward.

======================================================================
27. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
all commits
hosted CI

source coverage:
years
8-K count
8-K/A count
unique CIKs
Item 2.02 count
unknown count

availability:
exact adopted policy
evidence supporting it

identity:
mapped count
unresolved count
ended-class count
terminal resolution count

market data:
provider
version/API contract
requests
coverage
corporate-action treatment

benchmark:
exact matching rule
match rate

inference:
methods evaluated
synthetic calibration
chosen method
power geometry

freeze:
EXP006 created yes/no
spec SHA/hash
freeze commit SHA

If Development ran:

event count
paired count
net effect
confidence interval
p-value
materiality verdict
Development verdict

held-out confirmation access count MUST equal zero.

Also report:

local tests
public tests
preservation result

Then STOP.

======================================================================
28. OWNER INTENT
======================================================================

We have spent enough time proving architecture.

The goal is now to answer a real falsifiable question without sacrificing the
controls that make the answer credible.

Do the minimum necessary work to close the known Item 2.02 gates.

If they close:

freeze the experiment and run Development.

If they do not:

stop at the specific blocker.

Do not invent another phase to avoid getting an answer.

A negative Development result is a successful research outcome.

A blocked experiment with a real scientific reason is also acceptable.

What is not acceptable is another broad planning cycle with no decision.

Proceed without asking for intermediate owner approval unless a genuine stop
condition is reached.