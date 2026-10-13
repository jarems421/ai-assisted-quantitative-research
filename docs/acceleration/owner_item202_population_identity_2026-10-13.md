You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
020299da59f29fda4f1ff6f5d87bcbcbefc90f81

======================================================================
OWNER DECISION
EXP006 — HISTORICAL POPULATION + DATED SECURITY IDENTITY CLOSURE
======================================================================

Current state:

SCALABLE_ACCEPTANCE_DATE_BOUND_READY

Sampled Item 2.02 source classification also passes.

Current blocking status:

HISTORICAL_POPULATION_VERSION_IDENTITY_BLOCKED

EXP006 remains absent.
Performance evaluations = 0.
Historical confirmation accesses = 0.

This pass is NOT another timing review.

Do not reopen availability v003 unless new contradictory primary evidence appears.

The objective is now:

1. reconstruct the best defensible historical SEC filing population for
   Development 2015–2020;

2. preserve amendments / PAC / missing states without hindsight;

3. build a dated issuer -> security/class/provider bridge for the actual
   candidate events;

4. if those gates pass, automatically resume the remaining already-authorized
   EXP006 closure toward freeze and Development.

Do not request another owner planning decision unless a genuine stop condition
is reached.

======================================================================
1. READ CURRENT STATE
======================================================================

Inspect:

git status
git rev-parse HEAD
git branch --show-current

Then read at minimum:

AGENTS.md

docs/acceleration/exp006_date_repair_report.md
docs/acceleration/exp006_population_identity_review_v003.json
docs/acceleration/exp006_source_coverage.json
docs/acceleration/exp006_availability_contract_v003.json
docs/acceleration/exp006_primary_title_review_v003.json
docs/acceleration/owner_item202_date_repair_2026-10-13.md
docs/acceleration/owner_item202_remedy_2026-10-13.md
docs/acceleration/owner_item202_closure_2026-10-13.md

Previous Phase 3 identity/lifecycle work:

docs/acceleration/phase3c_identity_lifecycle.md
src/research/phase3c/sources.py
src/research/phase3c/registry.py

and:

experiments/EXP002/research/universe_audit.md

The latter may contain useful historical diagnostics but is NOT automatically
canonical evidence for EXP006.

Preserve all previous failed and passed receipts byte-for-byte.

======================================================================
2. DO NOT SOLVE THE WRONG SCALE
======================================================================

Current provisional Item 2.02 source rows:

109,347

Current provisional Item 2.02 unique CIKs:

6,196

Do NOT make one identity request per source row.

Identity must be constructed as dated spans at:

issuer / security-class / listing

level wherever possible.

One certified security span may serve many filings from the same issuer.

Prefer:

issuer-date intervals

over:

event-by-event repeated lookups.

The objective is a reusable dated identity table, not 109k unrelated mappings.

======================================================================
3. SIGNAL EVENT DEFINITION — RETAIN AMENDMENTS, DO NOT TRADE THEM
======================================================================

The selected EXP006 feature is:

ORIGINAL 8-K
with source-declared Item 2.02.

8-K/A rows remain part of:

version lineage
amendment history
missingness
correction/PAC analysis

but are NOT separate signal events.

Do not create a second trade merely because an 8-K/A exists.

Do not retroactively replace the original event using amendment information
that was unavailable at the original decision time.

Create explicit states such as:

ORIGINAL_SIGNAL_EVENT
AMENDMENT_VERSION_ONLY
NON_ITEM202
UNKNOWN
SOURCE_REMOVED_OR_UNAVAILABLE

Use repository-consistent names.

======================================================================
4. HISTORICAL POPULATION — USE DAILY MASTER INDEXES
======================================================================

The current 24 quarterly indexes are rebuilt views.

The SEC documentation already reviewed indicates that later PAC/removal
behavior can affect rebuilt full/quarterly indexes differently from previous
daily/feed/oldload views.

Before treating daily indexes as historical evidence, re-check the exact
official SEC documentation already archived.

If supported, reconstruct Development using official daily master indexes for:

2015-01-01 through 2020-12-31

Prefer routes equivalent to:

Archives/edgar/daily-index/YYYY/QTRx/master.YYYYMMDD.idx

or the exact official equivalent established by SEC directory metadata.

Do NOT use Feed/Oldloads for the full reconstruction unless daily indexes fail.

The previous Feed/Oldloads feasibility test showed that one daily archive can
exceed 256 MiB. That route is therefore a fallback, not the default.

======================================================================
5. DAILY-INDEX ACQUISITION BOUND
======================================================================

A full Development calendar is acceptable.

Maximum new daily-master starts:

1,650

Use:

cache first
official directory enumeration
single-worker respectful pacing
immutable source receipts

No retries unless existing transport policy permits them.

Do not request days that official directory metadata shows do not exist.

Do not use market data or returns.

======================================================================
6. DAILY VS QUARTERLY POPULATION RECONCILIATION
======================================================================

Build canonical keys from at least:

CIK
accession
form
filed date
source path

Compare the union of historical daily indexes against the existing current
quarterly census.

Report:

daily union rows
quarterly rows

present in both
daily-only
quarterly-only

8-K
8-K/A

unique accessions
unique CIKs

shared-accession/cofiler rows

duplicate/equivalent rows

For every difference preserve the actual key.

Do not call:

quarterly-only = invalid

or:

daily-only = deleted

without evidence.

Use neutral states such as:

PRESENT_BOTH
HISTORICAL_DAILY_ONLY
CURRENT_QUARTERLY_ONLY
CONFLICTING_METADATA

until additional evidence resolves them.

======================================================================
7. HISTORICAL EVENT POPULATION
======================================================================

Construct the Item 2.02 event candidate set from the reconciled source
population.

For rows present in current bulk metadata:

reuse the already audited Item labels.

For daily-only or otherwise unresolved keys:

do not assume Item 2.02 = false.

Resolve only the unresolved rows needed to determine whether they belong in the
Item 2.02 candidate set.

Use original SEC header/body evidence as needed.

Prefer batching/cache.

Do not re-download every known current filing.

If the number of unresolved historical-only keys requiring individual source
retrieval is unexpectedly huge:

STOP and report the count before launching an uncontrolled request campaign.

======================================================================
8. VERSION / PAC CERTIFICATE
======================================================================

Produce a compact certificate answering:

What filing population can EXP006 actually claim?

Possible acceptable wording may resemble:

"Union of archived SEC daily master-index observations over Development,
reconciled against the present rebuilt quarterly census."

Do NOT call it:

the complete set of every legal filing ever required

unless evidence actually establishes that.

Quantify:

daily-only keys
quarterly-only keys
missing original documents
amendments
unresolved version relationships
known PAC/removal evidence

No unknown count becomes zero by assumption.

If the daily archive itself is shown to be retrospectively rebuilt in a way
that destroys the required historical population property:

STOP at HISTORICAL_POPULATION_BLOCKED.

======================================================================
9. COFILER / ACCESSION SEMANTICS
======================================================================

Current candidate data contain shared accessions / cofilers.

Do not deduplicate merely by accession.

Do not assume one accession = one issuer.

Maintain:

legal filer CIK
submitting entity where distinct
accession
security issuer
security class

Only after dated identity resolution may multiple source rows be determined to
represent the same tradable issuer/class/day event.

The final trading event key should be something like:

security_id
class_id
decision_date

with source accession lineage retained.

Do not manufacture duplicate trades from cofilers.

======================================================================
10. IDENTITY — PREDECLARE THE REQUIRED CONTRACT
======================================================================

A source event is FULLY_RESOLVED only if, at the event decision date, the
system can establish:

issuer CIK

exact tradable security/class

domestic common-equity eligibility

historical ticker or equivalent provider lookup symbol

venue / listing context where available

stable provider/security identifier

effective date span containing the event date

and enough lifecycle information to value the planned 20-session position.

Keep distinct:

issuer
security
share class
ticker
exchange
FIGI
provider ID

No current ticker substitution backward.

No first-match OpenFIGI choice.

No current surviving-security requirement.

======================================================================
11. REUSE EXISTING EVIDENCE, BUT DO NOT PROMOTE FAILED SOURCES
======================================================================

EXP002 previously observed local Nexus/Lake security segments with fields such
as:

ticker
security_id
share_class_figi
CIK
from_date
to_date
asset_type

Those historical diagnostics may be reused as:

DISCOVERY_ONLY
or
CORROBORATION_ONLY

if already locally available.

They may NOT become the sole canonical EXP006 identity source because EXP002
already documented underfilled populations, missing/ambiguous types and
historical coverage failures.

Nexus historical execution remains disabled.

Do not make remote Nexus/Aurora calls.

======================================================================
12. IDENTITY SOURCE ROUTES — MAX THREE
======================================================================

Test no more than THREE serious identity routes.

Prefer existing configured/free sources.

Candidate route families:

A. SEC PRIMARY / PERIODIC-FILING EVIDENCE

Use dated source documents such as:

event filing cover page
nearest prior 10-Q / 10-K
structured cover-page facts where present
historical trading symbol
class title
exchange/listing evidence

Only evidence available on or before the event date may define the class.

B. SEC + OPENFIGI

Use exact dated symbol/class/exchange evidence from SEC as the lookup input.

OpenFIGI may supply:

share-class FIGI
composite FIGI
identifier candidates

but current OpenFIGI metadata alone is NOT a dated listing certificate.

Reject ambiguous multiple candidates.

C. EXISTING CONFIGURED MARKET-DATA METADATA

Inspect already configured providers such as Tiingo / FMP only where credentials
already exist.

Do not print or commit secrets.

A provider route is useful only if it can establish relevant historical:

ticker validity
listing start/end
permanent identity
ended-security coverage

Do not buy or upgrade a plan.

Do not add a random new commercial vendor during this pass.

======================================================================
13. SMALL IDENTITY FEASIBILITY SAMPLE FIRST
======================================================================

Before scaling to thousands of issuers, freeze a deterministic source-only
identity audit sample.

Maximum:

180 event candidates

Cover:

2015–2020
all years
all quarters
multiple events from same issuer
single-event issuers
shared-accession/cofiler cases

and, if discoverable WITHOUT returns:

ticker rename cases
merger/end-of-listing cases
multiple-class issuers
ambiguous OpenFIGI cases

No future return selection.

No issuer fame selection.

No survivor-only selection.

Freeze sample before remote identity calls.

======================================================================
14. SELECT THE IDENTITY ROUTE BEFORE FULL SCALE
======================================================================

Compare routes on:

dated evidence quality
exact-class resolution
historical ticker resolution
permanent-ID resolution
ended-security support
ambiguity
reproducibility
request cost

Do NOT choose based on how many future returns happen to exist.

Use the repository's existing historical identity standard where one is already
governing.

In particular, do not invent a weaker coverage threshold merely to force
EXP006 through.

If the repo's prior 95% fully-resolved standard remains governing, retain it.

Report explicitly if a different current governing contract supersedes it.

======================================================================
15. SCALE BY ISSUER/SPAN, NOT EVENT
======================================================================

If a route passes feasibility:

construct dated security spans for the unique relevant CIKs.

Cache and reuse spans across repeated filings.

Do not repeatedly resolve the same issuer/security for every Item 2.02 event.

Where one issuer has multiple common classes:

do not choose one arbitrarily.

If exactly one class is clearly the dated domestic listed common equity:

use it.

If multiple eligible common classes exist, freeze a deterministic selection
rule before any post-event outcomes.

An acceptable rule may use strictly PRE-EVENT information such as historical
listing evidence and pre-event liquidity, but any such rule must be specified
and hashed before outcome returns.

Do not use future performance to select a class.

======================================================================
16. PRE-EVENT MARKET INFORMATION IS ALLOWED FOR CERTIFICATION
======================================================================

This pass may use market/provider data strictly for:

historical identity
listing validity
corporate actions
pre-event liquidity needed for a predeclared class/matching rule

provided every observation is timestamped strictly before the event decision.

This is NOT performance authorization.

Still forbidden before freeze:

post-event returns
20-session event outcomes
paired performance
strategy P&L
Sharpe
alpha
confirmation-period outcomes

Implement explicit guards so pre-event certification queries cannot leak
post-event results.

======================================================================
17. ENDED / RENAMED CLASSES
======================================================================

For mapped event securities identify:

ticker renames
exchange changes
mergers
delistings
class conversions
terminal events

If the 20-session planned holding period crosses a terminal event:

record the exact required economic resolution.

Do not:

drop the observation
forward-fill last price forever
assume zero
replace the security with a survivor

unless primary/provider evidence supports the actual treatment.

A security may be historically eligible even if it no longer exists today.

======================================================================
18. IDENTITY CERTIFICATE OUTPUT
======================================================================

Report at minimum:

candidate original Item 2.02 events

unique CIKs

fully resolved events
ambiguous events
unresolved events

coverage %

coverage by year

coverage by issuer

single-class
multiple-class
rename
ended-security
terminal-path cases

No hidden exclusions.

If missingness clusters materially in early years or ended securities, report
it explicitly.

If the governing identity threshold fails:

STOP at HISTORICAL_IDENTITY_BLOCKED.

Do not shrink Development to later years automatically.

Do not silently drop difficult cases.

======================================================================
19. MARKET PROVIDER CERTIFICATION
======================================================================

If identity passes, continue automatically.

Certify the provider needed for:

historical opens
pre-event matching data
corporate actions
ended-security valuation

Use a tiny frozen audit covering where possible:

ordinary security
split
cash dividend
ticker rename
ended/delisted security
merger/terminal case

Do not inspect strategy outcomes.

If no configured/free provider can preserve these cases:

STOP at MARKET_DATA_BLOCKED.

======================================================================
20. MATCHING
======================================================================

If provider certification passes, resume the existing EXP006 contract.

Freeze the deterministic contemporaneous non-Item-2.02 control rule using only
pre-event:

industry
size
momentum
calendar proximity

as already approved.

No future information.

No outcome tuning.

SPY descriptive only.

Hash the matching rule before any post-event return is loaded.

======================================================================
21. INFERENCE / POWER
======================================================================

Then resume the already-authorized inference closure.

Use actual event/match geometry but synthetic outcomes only.

At most three inference candidates.

Stress:

repeated issuer
calendar clustering
earnings-season concentration
industry/common factors
persistent common shocks
20-session overlap
heterogeneity
missing controls

Select by calibration/coverage robustness, not power alone.

Then evaluate synthetic:

0.00 pp
+0.50 pp
+1.00 pp

under the selected method.

No real post-event outcomes yet.

======================================================================
22. FREEZE IF ALL GATES PASS
======================================================================

If and only if:

historical population passes
Item 2.02 source population passes
identity passes
terminal treatment passes
market provider passes
matching is frozen
inference calibrates
power is acceptable
Proof v2 passes

then create:

EXP006_SEC_ITEM202_PREDICTIVE

using repository conventions.

Freeze all existing owner-approved parameters unchanged:

Feature:
original 8-K Item 2.02

Availability:
certified v003 conservative date-envelope rule

Development:
2015-01-01 through 2020-12-31

Historical confirmation:
2021-01-01 through 2026-09-30

Horizon:
20 regular trading sessions

Base cost:
10 bps per side

Robustness:
20 bps per side
+1-session delay

Materiality:
paired net mean >= +0.50 percentage point
AND positive two-sided 95% lower confidence endpoint

Trial ceiling:
12

Push the PRE-PERFORMANCE FREEZE commit.

That commit must exist before any Development outcome artifact.

Do not amend it later.

======================================================================
23. DEVELOPMENT AFTER FREEZE ONLY
======================================================================

Only after the pushed freeze commit exists:

Development post-event outcomes are authorized.

Run exactly one frozen Development evaluation.

Do not tune afterward.

No:

new horizon
new feature
new availability rule
new class rule
new benchmark
new inference method

after seeing the result.

Historical confirmation remains completely unopened.

Required:

confirmation_access_count = 0

======================================================================
24. DEVELOPMENT VERDICT
======================================================================

Use only:

DEVELOPMENT_FAIL

DEVELOPMENT_MIXED

DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS still requires both:

paired net 20-session mean >= +0.50 pp

and

positive two-sided 95% lower confidence endpoint vs zero.

A positive estimate alone is not a pass.

Negative Development is a valid research result.

Do not redesign Item 2.02 in this task after failure.

======================================================================
25. STOP CONDITIONS
======================================================================

Stop before freeze if:

daily-index history cannot support the required historical population claim;

daily/quarterly differences cannot be represented without hindsight;

historical-only Item status cannot be resolved at reasonable scale;

dated security identity fails the governing coverage standard;

identity coverage is materially survivor-biased;

multiple classes require an unfrozen discretionary choice;

ended-security paths cannot be valued;

provider coverage drops dead securities;

matching requires future information;

inference does not calibrate;

materiality is effectively untestable;

Proof v2 fails.

Report the precise blocker.

Do not start another architecture phase.

======================================================================
26. REQUEST DISCIPLINE
======================================================================

Historical daily master indexes:

maximum 1,650 direct starts

Identity feasibility:

maximum 180 event candidates

OpenFIGI / Tiingo / FMP:

respect existing provider limits and configured credentials

No purchase.

No Orbis scraping.

No Nexus remote.

No Aurora.

No huge Feed/Oldloads campaign.

Reuse archives and caches.

======================================================================
27. REQUIRED ARTIFACTS
======================================================================

Prefer compact machine-readable receipts plus one human report.

Likely:

docs/acceleration/exp006_historical_population_certificate.json
docs/acceleration/exp006_historical_population_report.md

docs/acceleration/exp006_identity_sample.json
docs/acceleration/exp006_identity_certificate.json
docs/acceleration/exp006_identity_report.md

Only if later gates pass:

docs/acceleration/exp006_market_data_certificate.json
docs/acceleration/exp006_inference_certificate.json
experiments/EXP006/spec.json

and only after frozen Development executes:

reports/EXP006_development_report.md

Do not create documentation for ceremony.

======================================================================
28. TESTS
======================================================================

Add focused tests for:

daily-index deterministic parsing

daily/quarterly union

daily-only state

quarterly-only state

amendment retained but not independently traded

shared-accession/cofiler handling

no current ticker projection backward

dated class span contains event date

ambiguous class stays unavailable

multiple-class deterministic rule

rename within span

ended-security retention

terminal-path treatment

provider missing dead security -> fail

pre-event certification boundary

post-event data inaccessible before freeze

confirmation inaccessible

freeze commit precedes Development output

historical passed timing artifacts unchanged

Public CI remains network-free.

======================================================================
29. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

HISTORICAL POPULATION:

daily-index files
daily union rows
daily-only rows
quarterly-only rows
original 8-K count
8-K/A count
candidate original Item 2.02 events
unresolved Item states
PAC/version limitations

IDENTITY:

unique candidate CIKs
fully mapped events
ambiguous
unresolved
coverage %
coverage by year
multiple-class count
rename count
ended-class count
terminal resolved/unresolved

If continuation passes:

provider certificate
matching coverage
inference calibration
synthetic power

If frozen:

EXP006 spec hash
freeze commit

If Development runs:

eligible events
matched pairs
net paired mean
95% CI
p-value
materiality result
Development verdict

confirmation accesses MUST equal zero.

Then STOP.

======================================================================
30. OWNER INTENT
======================================================================

Timing is no longer the main problem.

Do not spend another cycle perfecting acceptance chronology.

The task is now to establish:

what the historical filing population actually was

and

which exact tradable security each filing belonged to at that time.

Solve those two problems at their natural scale:

daily filing indexes
+
issuer/security date spans

not hundreds of thousands of repeated per-event lookups.

If those gates close, continue toward freeze and a real Development result.

Do not create another planning loop.