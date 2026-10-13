You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
bdb884e4342be622ee37b0d5800afaa437587648

======================================================================
OWNER DECISION
PHASE 4A — EXP007 CONGRESSIONAL PURCHASE DISCLOSURE SPRINT
======================================================================

EXP006 is permanently closed:

ABANDON_EXP006_SOURCE_FEASIBILITY

Do NOT reopen:

EXP002
EXP003
EXP004
EXP005
EXP006

Do NOT rescue Item 2.02.
Do NOT launch another SEC identity campaign.
Do NOT start Phase 4B.
Do NOT audit another external repository.

The objective now is:

GET ONE DEFENSIBLE PREDICTIVE EXPERIMENT TO DEVELOPMENT PERFORMANCE.

The next candidate is based on the already-integrated:

austin-starks/congressional-disclosures

snapshot and:

src/research/surfaces/congressional.py

Candidate label:

EXP007_CONGRESSIONAL_PURCHASE_DISCLOSURE

Before registration, verify EXP007 is not already a registered experiment ID.
Historical roadmap mentions do not count as registration.
If EXP007 is genuinely occupied, use the next free experiment ID.

======================================================================
1. HYPOTHESIS
======================================================================

Estimand type:

PREDICTIVE

No causal claim.

Hypothesis:

A publicly disclosed purchase of a listed common equity by a member of the
United States Congress may contain positive predictive information for that
security's subsequent return.

Primary estimand:

NET 20-SESSION RETURN OF DISCLOSED PURCHASED SECURITY
MINUS
SPY RETURN OVER THE SAME ENTRY/EXIT WINDOW

averaged over the frozen eligible event population.

Do not call this alpha.

One feature:

CONGRESSIONAL COMMON-EQUITY PURCHASE DISCLOSURE

One horizon:

20 regular trading sessions

One formal benchmark:

SPY

No politician ranking.
No party effect.
No committee effect.
No transaction-size threshold.
No amount-bracket optimization.
No sector search.
No purchase-vs-sale grid.
No horizon search.
No ML.

======================================================================
2. START BY INSPECTING ACTUAL SNAPSHOT SCHEMA
======================================================================

Read:

src/research/surfaces/congressional.py

docs/acceleration/phase4a_integration_report.md

docs/architecture/external_integrations.md

tests covering CongressionalDisclosuresAdapter

and the pinned snapshot manifest / existing cached Parquet artifacts.

Inspect the actual schemas of:

political_filings
political_trades
political_trade_events

Do not assume field names from this instruction where upstream names differ.

Document the fields actually available for:

event ID
event version
member identity
chamber
transaction date
transaction type
asset description/type
printed ticker
resolved ticker
resolution status
source document ID
source URL
first_available_at
available_at
superseded_at
amount/range if present

Amount data are descriptive only for this experiment.

======================================================================
3. EVIDENCE BOUNDARY
======================================================================

The Congressional snapshot remains:

AUDITED_EXTERNAL_DERIVED

It does NOT become PRIMARY_ORIGINAL.

Preserve:

snapshot revision
manifest hash
file hashes
generatedAt
retrieval time
source URLs
event-version chronology

The primary experiment may use the audited derived dataset only under an
explicit evidence contract.

Do not claim:

complete legal disclosure universe
perfect extraction
perfect ticker resolution
observed exact public timestamp

unless independently evidenced.

======================================================================
4. ORIGINAL-SOURCE VALIDATION
======================================================================

Before freezing the experiment, validate the fields needed for the experiment
against official House/Senate disclosure documents.

Freeze a neutral validation sample BEFORE fetching originals.

Maximum:

96 disclosure/trade observations.

Cover where available:

House
Senate

multiple years

purchases
non-purchases

printed tickers present
printed tickers missing

resolved == printed
resolved != printed

event amendments / versions

different transaction-date / disclosure-lag geometries

No selection using returns or stock performance.

Compare upstream snapshot against original disclosure evidence for:

transaction type
transaction date
asset/security description
printed ticker
member/document identity

Do NOT require original PDFs to contain the upstream resolver's corrected
ticker; that is a derived field.

Report field-level agreement and UNKNOWN states.

If purchase classification is materially unreliable:

STOP.

======================================================================
5. EVENT POPULATION
======================================================================

Primary source population:

snapshot event versions whose active as-of state indicates an unequivocal
PURCHASE transaction in a common/listed equity.

Exclude before performance:

sales
exchanges that are not clearly purchases
options
warrants
bonds
funds / ETFs if distinguishable
private securities
crypto
non-security assets
unknown transaction types
unknown asset classes

Do not infer unknown asset type as equity.

Do not use transaction amount as an eligibility threshold.

Unknown records remain UNKNOWN, not non-events.

======================================================================
6. VERSION / AS-OF SEMANTICS
======================================================================

Use the existing version-aware semantics.

For any decision timestamp, only the event version actually available at that
time may exist.

Respect:

first_available_at
available_at
superseded_at

An amended future version must never rewrite the earlier event state.

Retain the original event/version lineage.

Do not use today's corrected event state at an earlier decision date.

======================================================================
7. AVAILABILITY
======================================================================

Current adapter explicitly labels upstream timing:

UPSTREAM_MODELED_EOD_NOT_OBSERVED_PUBLIC

Preserve that statement.

Do NOT pretend first_available_at is an observed exact website timestamp.

Predeclare the conservative execution policy:

ELIGIBLE ENTRY =
09:30 America/New_York on the SECOND regular NYSE session strictly after the
calendar date associated with the event/version's effective upstream
availability bound.

For an original version use the latest relevant bound required by:

first_available_at
and
that version's available_at

before the event can exist.

The execution open must be strictly later than all effective modeled
availability bounds.

Exact public availability remains UNKNOWN.

This is:

MODELED_CONSERVATIVE_DISCLOSURE_ELIGIBILITY

not observed publication time.

Validate weekend/holiday/DST behavior.

======================================================================
8. SECURITY IDENTITY — KEEP THIS NARROW
======================================================================

Do not recreate EXP006's multi-year identity problem.

The disclosure itself contains:

printed ticker

and the upstream derived dataset may contain:

resolved ticker
resolution status

The experiment's source-defined estimand may be restricted to:

SOURCE-RESOLVED DISCLOSED COMMON-EQUITY PURCHASES

provided the restriction is frozen before outcomes.

For each event retain separately:

printed_ticker
resolved_ticker
resolution_status

Never silently replace printed ticker.

If printed == resolved:

record that.

If they differ:

retain both and the upstream resolver status/reason where available.

If no reliable resolution exists:

UNRESOLVED_SECURITY

and the event is unavailable.

======================================================================
9. HISTORICAL PROVIDER CONFIRMATION
======================================================================

Before returns, validate that the chosen ticker/security corresponded to a
tradable listed common equity at the modeled decision date.

Use an existing configured provider.

No paid upgrade.

Prefer exact historical evidence such as:

provider historical metadata
stable provider security ID
dated symbol coverage
common-equity classification

OpenFIGI may corroborate an exact candidate, but must not date the security on
its own.

Do not require a multi-year listing span outside the event-to-exit window.

Required certificate:

security can be identified at entry
+
security can be economically valued through the 20-session exit.

If ticker changes inside the 20-session path:

preserve identity.

If merger/delisting/cancellation occurs:

require economic terminal treatment.

======================================================================
10. IDENTITY COVERAGE — DO NOT REPEAT EXP006'S WRONG DENOMINATOR
======================================================================

Do NOT require 95% of all congressional disclosures to be resolvable.

The estimand itself is explicitly conditional on:

SOURCE-RESOLVED COMMON-EQUITY PURCHASE DISCLOSURES.

Therefore report, but do not hide:

total purchase disclosures
asset-class eligible
printed-ticker present
resolved-ticker present
provider-confirmed
path-certified
unresolved

The experiment must not claim results for unresolved disclosures.

However:

if missing/resolution failures are so concentrated by year/chamber/event type
that the resolved cohort is clearly non-representative even of the declared
source-resolved estimand, STOP.

Do not select the coverage rule based on returns.

======================================================================
11. DUPLICATE / CLUSTER EVENT RULE
======================================================================

Avoid counting the same security/day repeatedly merely because:

multiple lawmakers purchased it;
multiple disclosures appeared;
multiple versions exist.

Before outcomes freeze the aggregation rule:

PRIMARY EVENT KEY =
stable security identity
+
modeled eligible entry date

Multiple qualifying disclosures mapping to the same security and same eligible
entry date become ONE trading event.

Retain metadata such as:

number of disclosures
number of members

for descriptive reporting only.

Do not weight the primary signal by those counts.

Repeated events on different dates remain separate but dependence-aware.

======================================================================
12. DEVELOPMENT / CONFIRMATION SPLIT
======================================================================

Use source geometry only.

Before market outcomes are loaded, inspect the years with credible source and
version coverage.

Choose the longest contiguous set of COMPLETE calendar years that provides:

at least 4 Development years

and

at least 2 later workflow-held-out years where possible.

Use a mechanical chronological split:

earliest approximately 70% of complete years = Development
latest approximately 30% = workflow-held-out confirmation

with the split rounded at a calendar-year boundary.

Do not inspect returns to choose the split.

Freeze exact dates before outcome access.

If source history cannot support at least:

4 full Development years

STOP at SOURCE_GEOMETRY_BLOCKED.

The confirmation period must remain unopened during this task.

======================================================================
13. COST / EXECUTION
======================================================================

Predeclare:

entry =
eligible regular-session OPEN

exit =
OPEN exactly 20 regular trading sessions after entry

base cost =
10 bps per side

round trip =
20 bps

future robustness =
20 bps per side
+
1-session delayed entry

No participation/capacity claim.

Use corporate-action-consistent valuation.

Include cash dividends economically earned during the holding period.

Do not forward-fill through terminal events.

======================================================================
14. SPY BENCHMARK
======================================================================

Primary paired observation:

security 20-session total return
minus
SPY total return over the exact same entry/exit dates
minus
the disclosed-security transaction-cost assumption

SPY is the one formal benchmark.

No benchmark shopping.

Do not add QQQ, sector ETFs, factors, Russell indices, etc. after seeing
performance.

Any additional comparator would require a future separately authorized study.

======================================================================
15. MATERIALITY
======================================================================

Predeclare before performance:

Development economic materiality threshold:

+0.50 percentage point

for mean net 20-session SPY-relative return.

Statistical requirement:

positive two-sided 95% lower confidence endpoint versus zero.

PASS ultimately requires both.

This threshold is not return-derived.

======================================================================
16. INFERENCE BEFORE RETURNS
======================================================================

Use actual event geometry but synthetic outcomes only.

At most THREE candidate procedures.

The method must account for:

repeated securities
repeated members
calendar clustering
market-wide shocks
20-session overlap
multiple disclosures in similar periods
heterogeneous event frequency
unequal yearly counts

Candidate classes may include:

calendar-block bootstrap

multiway clustered inference

calendar-time portfolio inference

Do not select based on power alone.

Primary selection criteria:

null rejection near 5%
coverage near 95%
persistent common-factor robustness
compatibility with actual event geometry

Retain failed methods.

Freeze the selected method before real post-event outcomes.

======================================================================
17. SYNTHETIC POWER
======================================================================

Using actual source/identity/event geometry and synthetic outcomes only,
estimate behavior under:

0.00 pp
+0.50 pp
+1.00 pp

Do not treat raw disclosures as independent N.

If +0.50 pp is effectively untestable:

STOP at POWER_BLOCKED.

======================================================================
18. TRIAL CEILING
======================================================================

Use a fresh EXP007 ceiling:

8 real performance evaluations maximum.

Initial allocation:

1 primary Development result

1 SPY descriptive/gross companion if separately counted by the repository

2 predeclared future robustness evaluations

1 eventual held-out confirmation primary

1 eventual confirmation robustness

2 reserves for documented execution corrections/failures

Do not reset the ceiling.

Synthetic inference calibration is recorded separately and must remain bounded.

======================================================================
19. PRE-PERFORMANCE FREEZE
======================================================================

If source validation, timing, identity/path, inference and power pass:

create/register:

EXP007_CONGRESSIONAL_PURCHASE_DISCLOSURE

or next free repository-consistent ID if EXP007 is already registered.

Freeze hashes for:

snapshot
upstream revision
source-validation contract
event classification
version/as-of semantics
availability
identity
duplicate aggregation
Development/confirmation split
market provider
entry/exit
corporate actions
SPY benchmark
costs
inference
materiality
trial ceiling
code/environment

Run Proof v2.

Required state:

SCIENTIFICALLY_READY_FOR_FREEZE

performance_executed = false

confirmation_accesses = 0

Commit and PUSH a distinct:

PRE-PERFORMANCE FREEZE

before any Development outcome artifact exists.

Do not amend/rewrite it later.

======================================================================
20. DEVELOPMENT
======================================================================

Only after the pushed freeze commit exists:

load Development outcomes.

Run exactly the frozen primary evaluation.

No:

politician ranking
amount threshold
party split
committee filter
new horizon
new benchmark
new event aggregation
new identity rule
new inference method

after seeing the result.

Do NOT open workflow-held-out confirmation.

confirmation_access_count = 0

required.

======================================================================
21. DEVELOPMENT VERDICT
======================================================================

Use only:

DEVELOPMENT_FAIL

DEVELOPMENT_MIXED

DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS requires BOTH:

mean net 20-session SPY-relative return >= +0.50 pp

AND

positive two-sided 95% lower confidence endpoint versus zero.

If it fails:

retain the result.

Do not redesign congressional purchases during this task.

If it passes:

do not open confirmation.

Stop for owner review.

======================================================================
22. ORIGINAL-SOURCE / DERIVED-DATA LANGUAGE
======================================================================

Be precise in reports.

Allowed:

"audited external derived snapshot linked to official disclosure documents"

Not allowed without evidence:

"complete congressional trading database"

"primary-source canonical trade history"

"exact observed public timestamp"

"all congressional stock trades"

Keep evidence-tier language explicit.

======================================================================
23. DO NOT OVERENGINEER
======================================================================

Do NOT:

build Phase 4B

build a general political-data platform

download every original PDF if a bounded validation suffices

introduce ML

build politician scoring

build portfolio optimization

integrate another GitHub project

use Nexus historical execution

use Aurora

start paper/live trading

This is one predictive experiment sprint.

======================================================================
24. STOP CONDITIONS
======================================================================

Stop before performance if:

snapshot integrity fails

purchase classification is unreliable

version/as-of semantics cannot support the event definition

modeled availability cannot conservatively precede execution

security identity is too ambiguous for the declared source-resolved cohort

market provider cannot preserve ended/renamed securities through 20 sessions

source geometry gives too few usable Development events

inference does not calibrate

power is inadequate

Proof v2 fails

held-out isolation cannot be enforced

Do not route around a genuine blocker.

======================================================================
25. TESTS
======================================================================

Add focused tests for:

snapshot checksum/version pinning

purchase vs sale classification

unknown transaction state

asset/common-equity classification

printed vs resolved ticker separation

unresolved ticker fail-closed

event version available_at handling

future amendment not rewriting past state

modeled EOD availability

weekend/holiday entry rule

same-security/same-entry-date deduplication

repeated security on later date retained

20-session exit

split/dividend treatment

rename inside path

terminal event handling

SPY paired-window alignment

no post-event outcome before freeze

confirmation inaccessible

trial accounting

freeze commit before Development result

Public CI remains network-free.

======================================================================
26. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

SOURCE:
snapshot revision/hash
years
filings
trades
event versions
original-validation sample
field-level agreement

EVENT POPULATION:
purchase records
common-equity eligible
printed ticker coverage
resolved coverage
provider/path coverage
final unique event count
events by year

TIMING:
exact modeled availability rule
unknown/public timing statement

INFERENCE:
method candidates
synthetic calibration
selected method
power

If frozen:
experiment ID
spec hash
freeze commit SHA

If Development runs:
events
unique securities
net mean SPY-relative 20-session return
95% CI
p-value
materiality result
Development verdict

confirmation accesses MUST equal zero.

Then STOP.

======================================================================
27. OWNER INTENT
======================================================================

EXP006 taught us that source choice must make tradable-security identity a
first-class property.

Do not repeat the SEC identity reconstruction exercise.

The congressional disclosure source already exposes transaction-level ticker
information and versioned availability semantics.

Test one simple predictive claim:

publicly disclosed common-equity purchases
->
subsequent 20-session SPY-relative return.

Do the minimum certification necessary to make that result credible.

If the gates pass:

FREEZE AND RUN DEVELOPMENT.

If a genuine gate fails:

STOP AT THAT GATE.

No more broad planning loops.