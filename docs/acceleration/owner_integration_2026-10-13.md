You are continuing the existing Research OS project.

Repository:

C:\Users\runni\quant\

GitHub:

jarems421/ai-assisted-quantitative-research

Branch:

main

Expected current HEAD:

aad8ab7946bd4853d5f987ae0165943de25f4400

Current validated baseline:

315 local tests
89 public tests
0 skipped

Current canonical programme state:

PHASE3_COMPLETION =
COMPLETE_EXP005_ABANDONED

PHASE4A_FAMILY_SCREEN =
COMPLETE_THREE_FAMILIES_EXHAUSTED

PHASE4A_R =
SOURCE_FIRST_DIRECTION_READY

PREFERRED_CURRENT_SURFACE =
SEC

NEXT_EXPERIMENT =
NONE_SELECTED

PERFORMANCE_AUTHORIZED =
FALSE

PHASE4B =
KEEP_LATER

NEXUS_EXECUTION =
BLOCKED

EXP004 =
OPERATIONALLY_PAUSED

EXP005 =
ABANDONED_AND_ABSENT

======================================================================
OWNER INSTRUCTION
PHASE 4A-I — EXTERNAL REPOSITORY INTEGRATION + SOURCE-FIRST CONTINUATION
======================================================================

The owner has identified several external open-source repositories that may
materially improve Research OS:

- austin-starks/congressional-disclosures
- austin-starks/chrono-ta
- austin-starks/nexustrade-py
- pandas-dev/pandas
- matplotlib/matplotlib
- numpy/numpy
- scikit-learn/scikit-learn
- AI4Finance-Foundation/FinRL
- OpenBB / canonical current OpenBB repository

This instruction authorizes a DEEP READ-ONLY AUDIT of those repositories
followed by ACTUAL IMPLEMENTATION of the components that are useful to the
current Research OS architecture.

Do not stop after writing an integration matrix.

Build the useful integrations.

However:

DO NOT blindly vendor external code.

DO NOT import dependencies merely because they are popular.

DO NOT replace Research OS scientific controls with third-party abstractions.

DO NOT weaken provenance, timing, denominator, identity, stage, trial or
performance boundaries.

DO NOT reactivate Nexus execution.

DO NOT run strategy performance.

DO NOT create another endless architecture subphase.

The end state of this instruction should be:

1. useful external capabilities integrated into Research OS;
2. Research OS source architecture generalized without invalidating historical
   v001 evidence;
3. Congressional Disclosures evaluated as a real additional source surface;
4. SEC re-evaluated under the improved architecture;
5. ONE preferred research surface selected by a frozen rule;
6. ONE bounded source-contract prototype completed on the preferred surface;
7. ONE predictive mechanism direction advanced to a concrete
   PRE-PERFORMANCE DESIGN CANDIDATE if the evidence supports it;
8. a clear next step that is close to experiment freeze rather than another
   broad planning cycle.

No prices or returns are authorized in this instruction.

======================================================================
1. FIRST — INSPECT THE ACTUAL CURRENT REPOSITORY
======================================================================

Before implementing anything:

read:

AGENTS.md
README.md
requirements.txt
requirements-docs.txt
requirements-research.txt

docs/acceleration/master_plan.md
docs/acceleration/phase4a_researchability_report.md
docs/acceleration/phase4a_researchability_map.json
docs/acceleration/phase4a_researchability_contract.md
docs/acceleration/phase4a_source_registry.json
docs/acceleration/phase4a_mechanism_directions.md
docs/acceleration/phase4a_architecture_decision.md

src/research/source_first.py
src/research/source_first_report.py
src/research/procurement_pilot.py
src/research/fda_pilot.py
src/research/merger_pilot.py

src/research/phase3c/sources.py
src/research/sec_pilot/acquisition.py
src/research/sec_pilot/parsing.py
src/research/sec_pilot/provenance.py

src/research/spec.py
src/research/store.py

src/research/phase3d/proof.py
src/research/phase3d/execution.py
src/research/inference_feasibility.py

src/metrics/performance.py

src/nexus/

tests/test_source_first.py
tests/test_procurement_pilot.py
tests/test_fda_pilot.py
tests/test_merger_pilot.py
tests/test_phase3d_proof.py
tests/test_phase3d_execution.py

and relevant public-check wiring.

Run:

git status
git branch --show-current
git rev-parse HEAD
git remote -v

before mutation.

Repository state is authoritative.

======================================================================
2. IMPORTANT HISTORICAL-CODE CONSTRAINT
======================================================================

DO NOT materially mutate the scientific semantics of:

src/research/source_first.py

That module is source_first_v001.

Its validate() function requires canonical equality with the frozen contract.
Historical manifests and reports depend on those exact semantics.

Likewise preserve historical semantics of:

procurement_pilot.py
fda_pilot.py
merger_pilot.py
phase3d/proof.py
phase3d/execution.py

unless a bug fix is independently necessary and does not alter historical
evidence interpretation.

Do NOT "upgrade v001 in place."

Instead create versioned successors.

Suggested architecture:

src/research/surfaces/
    __init__.py
    base.py
    sec.py
    congressional.py

src/research/integrations/
    __init__.py
    registry.py
    congressional.py
    nexus_local.py

src/research/signals/
    __init__.py
    time_window.py

src/research/source_first_v2.py
src/research/source_first_v2_report.py

src/research/proof_v2.py

Use cleaner repository-consistent names if warranted.

Historical v001 code must continue reproducing byte-for-byte outputs.

======================================================================
3. EXTERNAL REPOSITORY AUDIT
======================================================================

Inspect the external repositories themselves, not just their README headlines.

Use temporary / ignored storage such as:

.research/external-audit/

Do NOT commit cloned third-party repositories.

For every external repo record:

repository
resolved canonical owner/name
HEAD commit SHA
default branch
license
relevant package/release version
files/modules inspected
useful concepts
code worth adopting
code NOT appropriate for Research OS
runtime dependency recommendation
licensing/attribution implications

Inspect enough implementation and tests to understand actual contracts.

At minimum inspect:

------------------------------------------------------------
A. austin-starks/congressional-disclosures
------------------------------------------------------------

README
package.json
dataset/
sources/
storage/
lake/
identity/
backfill/
integrity.ts
relevant tests
snapshot download/verification code
SQLite schema/migrations
event consolidation/versioning
member identity
source URL handling

Pay special attention to:

political_filings
political_trades
political_trade_events

and fields/semantics equivalent to:

transaction_date
available_at
first_available_at
superseded_at
printed_ticker
resolved_ticker
resolution_status
sourceUrl
member_id
chamber
action
amount_low
amount_high

Determine exactly how:

- amendments are consolidated;
- first availability is derived;
- supersession is represented;
- original source linkage is retained;
- unresolved tickers are represented;
- public snapshots are checksum verified;
- snapshot version/generatedAt is represented.

------------------------------------------------------------
B. austin-starks/chrono-ta
------------------------------------------------------------

Inspect actual indicator/window implementation and tests.

Focus only on reusable temporal semantics:

- elapsed-time windows;
- UTC timestamped observations;
- nondecreasing-time requirement;
- same-current-bucket replacement;
- expiration by elapsed time;
- batch vs streaming parity;
- serialized-state continuation;
- golden-vector testing.

Do NOT port its entire indicator catalog.

------------------------------------------------------------
C. austin-starks/nexustrade-py
------------------------------------------------------------

The repository already depends on:

nexustrade==1.42.0

Audit the installed version and upstream repo.

Focus on LOCAL / PURE functionality such as:

prepare_web_pages
structured document preparation
evidence-pointer validation
local statistics helpers
schema-bound extraction interfaces

Do NOT enable:

NexusTradeClient remote backtests
host.fetch
agent runs
Aurora
Lake remote operations
paper trading
live trading

Nexus remains downstream and blocked for historical execution.

------------------------------------------------------------
D. OpenBB
------------------------------------------------------------

Inspect its provider/data-integration architecture.

Focus on:

provider abstraction
normalized query/results
provider-specific metadata
extension boundaries
data routing
schema normalization

Do not install the full OpenBB stack unless a concrete current
Research OS use justifies it.

Research OS must remain canonical for evidence.

------------------------------------------------------------
E. AI4Finance-Foundation/FinRL
------------------------------------------------------------

Inspect architecture and current successor guidance.

Focus on future lessons for:

environment contracts
risk layer
train/test separation
portfolio interfaces

Do NOT add FinRL as a runtime dependency merely for future work.

This is probably a Phase 5 integration/defer decision.

------------------------------------------------------------
F. NumPy / pandas / scikit-learn / Matplotlib
------------------------------------------------------------

Treat these as scientific-computing dependencies, not research evidence
providers.

Audit current Research OS usage first.

Note:

phase3d/proof.py currently records NumPy in its environment fingerprint.

requirements-research.txt currently does not explicitly pin NumPy.

Resolve that inconsistency deliberately.

Matplotlib is already a documentation/presentation dependency.

Only add pandas or scikit-learn if new implemented code actually needs them.

Do not create dependency bloat.

======================================================================
4. EXTERNAL INTEGRATION REGISTRY
======================================================================

Create a small machine-readable integration registry.

Suggested:

docs/architecture/external_integrations.json

and:

docs/architecture/external_integrations.md

or repository-equivalent paths.

Each dependency/repository should have:

name
repo
pinned_audit_commit
license
role
integration_status
runtime_dependency
canonical_evidence_role
allowed_usage
forbidden_usage
Research OS module
reason

Statuses:

ADOPTED_RUNTIME
ADOPTED_SEMANTICS
ADOPTED_INTERFACE_PATTERN
EXISTING_DEPENDENCY
OPTIONAL_ADAPTER
DEFERRED_PHASE5
REFERENCE_ONLY
REJECTED

This registry must be executable/validated by tests where practical.

======================================================================
5. REQUIRED HIGH-LEVEL INTEGRATION DECISIONS
======================================================================

Unless actual code audit disproves these assumptions, implement the following
direction.

------------------------------------------------------------
Congressional Disclosures
------------------------------------------------------------

ADOPT AS:

OPTIONAL SOURCE-SURFACE ADAPTER

and:

AUDITED_DERIVED_DATASET INPUT

NOT automatically PRIMARY_CANONICAL_EVIDENCE.

------------------------------------------------------------
Chrono-TA
------------------------------------------------------------

ADOPT:

TIMESTAMP/WINDOW SEMANTICS

Do not add Rust as a mandatory dependency.

------------------------------------------------------------
NexusTrade-PY
------------------------------------------------------------

ADOPT:

SAFE LOCAL HELPERS ONLY

Keep remote execution blocked.

------------------------------------------------------------
OpenBB
------------------------------------------------------------

ADOPT:

PROVIDER-INTERFACE DESIGN LESSONS

Do not make OpenBB canonical evidence.

Avoid full runtime dependency unless strictly necessary.

------------------------------------------------------------
FinRL
------------------------------------------------------------

DEFER:

PHASE 5 / portfolio-risk-environment work.

No runtime import now unless concrete current use emerges.

------------------------------------------------------------
NumPy
------------------------------------------------------------

Make explicit/pinned if actually part of Research OS environment.

------------------------------------------------------------
pandas
------------------------------------------------------------

Add only if used by implemented integration.

DuckDB/PyArrow are already present and may avoid the need.

------------------------------------------------------------
scikit-learn
------------------------------------------------------------

Do not add until an actual predictive model contract needs it.

------------------------------------------------------------
Matplotlib
------------------------------------------------------------

Keep presentation-only unless evidence supports another role.

======================================================================
6. EVIDENCE-TIER MODEL
======================================================================

Research OS now needs an explicit distinction between primary evidence and
useful derived datasets.

Implement a small evidence-tier contract.

Suggested levels:

PRIMARY_ORIGINAL

PRIMARY_INDEX_OR_METADATA

PRIMARY_DERIVED

AUDITED_EXTERNAL_DERIVED

DISCOVERY_ONLY

UNVERIFIED_EXTERNAL

A record entering Research OS should know:

source_provider
evidence_tier
source_url
source_sha256 if available
upstream_version
upstream_commit_or_snapshot
retrieved_at
available_at_claim
available_at_status
revision_status
canonical_for_what

Important rule:

AUDITED_EXTERNAL_DERIVED does not automatically become
PRIMARY_ORIGINAL merely because it links to an official source.

This is critical for congressional-disclosures and OpenBB.

======================================================================
7. GENERALIZE SOURCE SURFACES — VERSION 2
======================================================================

Create a new v2 surface architecture.

Do not retrofit v001.

Define a lightweight protocol/dataclass equivalent to:

ResearchSurfaceAdapter

with concepts such as:

surface_id
name
evidence_tier
access_contract()
probe_manifest()
probe()
normalize_probe()
denominator_capability()
timing_capability()
revision_capability()
entity_capability()
reproducibility_capability()

Do not overabstract.

Existing:

SourceHTTP
Archive
RawStore
put()
digest()
canonical()

should remain the underlying evidence machinery where suitable.

Do not create a second raw archive system.

======================================================================
8. REUSE EXISTING HTTP / ARCHIVE MACHINERY
======================================================================

The current project already has robust pieces:

src/research/phase3c/sources.py::SourceHTTP

src/research/sec_pilot/acquisition.py::Archive

src/research/procurement_pilot.py::PilotHTTP

These provide useful behavior:

exact allowlists
original-byte archival
SHA-256
bounded response size
explicit request receipts
request pacing
provider stop persistence
no automatic blind resubmission
redirect constraints
credential redaction
immutable writes

Source-first v2 must reuse these concepts.

Do not solve source acquisition again from scratch.

If a cleaner shared boundary is justified, refactor only while maintaining
v1 regression compatibility.

======================================================================
9. CONGRESSIONAL DISCLOSURES ADAPTER
======================================================================

Build:

CongressionalDisclosuresAdapter

or repository-equivalent.

Preferred implementation:

consume the project's audited PUBLIC SNAPSHOT / Parquet output directly from
Python using existing:

PyArrow
DuckDB

rather than making Node/npm mandatory for ordinary Research OS analysis.

Node/npm may remain an optional rebuild route.

The adapter must be able to:

1. retrieve/read snapshot manifest metadata;
2. verify published file byte counts/hashes;
3. identify snapshot generatedAt/version;
4. query political_filings;
5. query political_trades;
6. query political_trade_events;
7. preserve sourceUrl;
8. preserve raw transaction date;
9. preserve first public availability;
10. preserve supersession;
11. preserve printed ticker separately from resolved ticker;
12. preserve unresolved mappings;
13. expose neutral as-of queries.

No silently inferred ticker.

No using current ticker as historical identity proof.

======================================================================
10. CONGRESSIONAL POINT-IN-TIME VIEW
======================================================================

Implement a deterministic function equivalent to:

events_known_at(timestamp)

It must enforce:

first_available_at <= timestamp

and:

superseded_at is null
OR
timestamp < superseded_at

depending on upstream version semantics confirmed by audit.

Later amended records must not leak backward.

The function must NEVER use:

transaction_date

as public availability.

It may expose transaction_date as a separate economic date.

Add tests demonstrating:

transaction occurs before disclosure;
event unavailable before first_available_at;
event becomes available at/after first_available_at;
later superseding event does not rewrite historical prior state;
printed ticker remains separate from resolved ticker.

======================================================================
11. CONGRESSIONAL SNAPSHOT TRUST BOUNDARY
======================================================================

The external audited snapshot is useful but not sufficient to become canonical
primary evidence.

Implement explicit status such as:

AUDITED_EXTERNAL_DERIVED

For future experiment certification require either:

A. independently verified original-source receipts;

or

B. an owner-approved contract explicitly accepting the external audited
derived snapshot for a declared purpose.

Do not accidentally let a Hugging Face/Parquet snapshot satisfy
PRIMARY_ORIGINAL gates.

======================================================================
12. CONGRESSIONAL NEUTRAL VALIDATION SAMPLE
======================================================================

After the adapter exists, perform a bounded neutral validation.

No returns.

Freeze before source requests:

a snapshot version;
a deterministic event ordering;
a neutral sample rule.

Use at most:

12 political_trade_events

selected mechanically, for example from a fixed historical period and sorted
by:

first_available_at
then stable event identifier

Do NOT select by:

politician
ticker
profitability
purchase magnitude
public-company fame
future stock survival

For sampled rows, validate where possible:

sourceUrl accessibility
official chamber source
document/event relationship
transaction date
availability date evidence
amendment/supersession
printed ticker
member identity

Maximum:

18 direct original-source requests

for this validation.

No OCR/model spending unless explicitly necessary and already available.

If direct source validation is impossible, retain the dataset as derived.

======================================================================
13. CHRONO-TA TEMPORAL SEMANTICS
======================================================================

Create small Python-native temporal primitives inspired by the verified
chrono-ta behavior.

Do NOT copy the entire crate.

Suggested:

TimedObservation
ElapsedWindow
TimedSeriesBuffer

Requirements:

timezone-aware UTC timestamps
nondecreasing timestamps
explicit bucket width
same-bucket replacement
elapsed-time expiration
deterministic ordering
bounded memory
reset support
batch == streaming semantics

Implement only a minimal useful set of signal primitives, for example:

elapsed SMA
elapsed ROC / value-ago

Do not implement RSI/MACD/etc unless required.

These utilities will later support:

momentum controls
event-window diagnostics
irregular historical observations
live/forward state

without assuming N calls == N days.

======================================================================
14. CHRONO GOLDEN/PARITY TESTS
======================================================================

Create independent Research OS tests for temporal semantics.

Include cases for:

irregular observations

same timestamp/bucket update

daily gaps

window expiry

batch vs streaming

state reset

out-of-order rejection

Do not claim bit-for-bit parity with chrono-ta unless actually verified.

If you copy any upstream golden vectors:

record source repository
commit
license
exact file/line origin

Prefer independently constructed vectors.

======================================================================
15. NEXUSTRADE-PY SAFE LOCAL INTEGRATION
======================================================================

NexusTrade execution remains blocked.

Do NOT modify:

phase3d/execution.py::NexusAdapter

to call the remote service.

Instead create a local-safe integration module.

Potentially expose wrappers around verified pure/local functions such as:

prepare_web_pages

and other deterministic document helpers.

If stats helpers are adopted, use them only as:

independent cross-checks

not canonical inference.

Explicitly block or omit imports/routes that can:

submit backtests
start agent runs
invoke host fetch
use Aurora
open paper execution
use brokerage endpoints

Add tests that prove the Research OS local wrapper cannot create remote jobs.

======================================================================
16. NEXUS DOCUMENT PREPARATION
======================================================================

If prepare_web_pages is confirmed pure/local:

integrate it as an OPTIONAL secondary HTML visible-text projection.

Rules:

original bytes remain authority

prepared visible text is derived evidence

hidden/scripts removed by helper are not proof of absence

projection must retain:

source hash
upstream helper version
input hash
output hash

Do not replace existing original-byte archives.

Use only if it materially improves current source parsing.

======================================================================
17. OPENBB PROVIDER BOUNDARY
======================================================================

Do NOT install OpenBB merely to say it is integrated.

Instead inspect its provider abstraction and use useful architectural ideas to
make Research OS source adapters composable.

A Research OS provider result must retain:

provider name
canonical upstream source
query contract
retrieval time
raw/derived status
provider metadata
point-in-time status
evidence tier

OpenBB itself, if later used, should begin as:

DISCOVERY_ONLY

or:

UNVERIFIED_EXTERNAL / AUDITED_EXTERNAL_DERIVED

depending on endpoint.

It must never bypass source certification.

======================================================================
18. FINRL BOUNDARY
======================================================================

Do not build RL now.

Record FinRL / FinRL-X as:

DEFERRED_PHASE5

Use the audit to identify future contracts that may be useful:

market environment
action/observation schema
risk constraints
train/test isolation
portfolio interface

Do not add these abstractions now unless they solve an existing concrete
Research OS problem.

======================================================================
19. SCIENTIFIC PYTHON DEPENDENCIES
======================================================================

Audit current environment.

Address the fact that proof.py fingerprints NumPy while NumPy is not explicitly
pinned by requirements-research.txt.

If NumPy is directly required:

pin a compatible version after running the complete suite.

Do not rely on a transitive dependency for a scientific fingerprint.

For pandas:

only add if congressional/surface implementation concretely uses it.

Prefer existing DuckDB/PyArrow where they already solve the job.

For scikit-learn:

do not install until a frozen predictive-model experiment actually requires it.

For Matplotlib:

retain presentation separation.

Document versions and licenses.

======================================================================
20. PROOF COMPILER V2 — DESIGN ONLY
======================================================================

Do NOT alter historical phase3d/proof.py semantics.

Create a versioned successor capable of compiling a REAL DESIGN MANIFEST
without executing performance.

Suggested roles:

population
source_surface
source_snapshot
availability
identity
feature_contract
benchmark_contract
execution_contract
inference_contract
trial_family
cost_contract

The compiler should validate:

file hashes
source evidence tiers
upstream dataset version
dependency versions
research cutoff
population denominator receipt
timing status
identity status
trial ceiling
performance_authorized == false

It must NOT:

execute a strategy
load returns
open held-out data
register EXP006
advance Store stage
call Nexus

A successful design compile means:

STRUCTURALLY_READY_FOR_EXPERIMENT_FREEZE_REVIEW

not:

strategy certified.

======================================================================
21. SOURCE-FIRST V2 RESEARCHABILITY PASS
======================================================================

After integration, run a new bounded source-first comparison.

Do NOT overwrite:

phase4a_researchability_map.json

or any v001 artifact.

Create v2 artifacts.

The serious candidate surfaces are now:

1. SEC/EDGAR
2. Congressional Disclosures

Federal Register may remain recorded as conditional.

ClinicalTrials remains blocked/current-version-limited from v1.

Do not re-run failed procurement/FDA/merger family routes.

======================================================================
22. FIXED WINNER SELECTION RULE
======================================================================

Freeze the selection rule BEFORE running the v2 comparison.

Do not choose whichever source "feels better."

A source is eligible only if none of these is BLOCKED:

SOURCE_ACCESS
DENOMINATOR
POINT_IN_TIME
HISTORICAL_DEPTH
REPRODUCIBILITY

Then compare eligible surfaces lexicographically:

1. greater number of:
   PROVEN_FROM_EXISTING_EVIDENCE
   or PASS_BOUNDED_PROBE
   across hard gates;

2. fewer PARTIAL hard gates;

3. fewer dependencies on non-primary derived evidence;

4. simpler historical identity burden;

5. higher plausible independent-record frequency;

6. if still tied:
   SEC wins because its primary-source archive/replay is already independently
   established in Research OS.

Freeze this rule.

No alpha/performance consideration.

======================================================================
23. V2 REQUEST CEILING
======================================================================

External GitHub repository audit requests are engineering review and separate
from scientific source acquisition.

For NEW research-source activity under v2:

maximum:

24 starts

including retries

before selecting the preferred surface.

Congressional neutral validation maximum:

18 original-source starts

inside that ceiling where practical.

Reuse existing SEC evidence without new requests wherever possible.

Do not burn requests merely to fill the budget.

======================================================================
24. AUTOMATIC CONTINUATION AFTER SURFACE SELECTION
======================================================================

Do NOT stop simply because a preferred source surface has been selected.

The owner explicitly authorizes ONE bounded source-contract prototype on the
winning surface.

No additional owner response is required if the winner is chosen exactly under
the frozen rule and the prototype stays inside this instruction.

Still no prices/returns.

======================================================================
25. IF SEC WINS
======================================================================

Implement the currently recommended:

SEC FILING-DENOMINATOR / PAC / AVAILABILITY CONTRACT PROTOTYPE

Use a NEW version.

Do not reuse v002/v003 as universal policy.

Prototype population:

FORM TYPE:
8-K

FIXED SOURCE PERIOD:
2020-01-01 through 2020-03-31

Purpose:

prove that Research OS can construct a versioned filing denominator suitable
for later predictive feature selection.

Do NOT select filings by Item 2.02/5.02/etc yet.

Population comes first.

======================================================================
26. SEC PROTOTYPE — ENUMERATION
======================================================================

Use official SEC filing indexes.

Prefer the smallest bounded combination of:

quarterly index

daily index / feed / oldload evidence where appropriate

archive index pages

needed to test:

population enumeration
accession identity
8-K vs 8-K/A
PAC/deletion evidence
index rebuild/revision semantics
missing original bodies

Do NOT download every Q1 2020 filing body.

Build the denominator first.

======================================================================
27. SEC PROTOTYPE — NEUTRAL BODY SAMPLE
======================================================================

After the 8-K denominator is frozen:

select at most 12 accessions

mechanically.

Suggested neutral rule:

first four eligible original/index entries by source order from:

January
February
March 2020

No item filtering.

No issuer filtering.

No current ticker filtering.

No interesting-company filtering.

Failed/unavailable accessions remain represented.

Maximum new SEC requests for the entire prototype:

32

including retries and indexes.

If existing cached/archive evidence supplies a request, reuse it.

======================================================================
28. SEC DENOMINATOR RECEIPT
======================================================================

Create a machine-readable receipt containing:

contract_version

form

date_start
date_end

index sources

index hashes

enumerated rows

accession
CIK
company/filed name
form
filing date
source filename

amendment relationship if evidenced

PAC/deletion state if evidenced

original-body state:
AVAILABLE
MISSING
REMOVED
UNTESTED

acceptance candidates if evidenced

public availability status

retrieval status

present-day reconstruction timestamp

Important:

the denominator receipt certifies:

WHAT WAS ENUMERATED FROM THE DECLARED SOURCE CONTRACT

not:

all filings legally required to exist.

Do not manufacture missing required filings.

======================================================================
29. SEC AVAILABILITY
======================================================================

Keep:

filing date
acceptance time
public dissemination
website accessibility
retrieval time

separate.

Do not activate v002/v003.

For this 8-K prototype classify timing only.

Possible statuses:

ACCEPTANCE_OBSERVED
DATE_ONLY
MODELED_BOUND_PLAUSIBLE
PUBLIC_TIMESTAMP_UNKNOWN
CONTRADICTORY

No new trading eligibility policy is approved.

======================================================================
30. IF CONGRESSIONAL DISCLOSURES WINS
======================================================================

Instead implement:

CONGRESSIONAL DISCLOSURE DENOMINATOR / AVAILABILITY CONTRACT PROTOTYPE

Freeze:

exact snapshot version
generatedAt
snapshot manifest hash
selected table
historical interval
selection rule

Use:

political_trade_events

as the economic-event layer only after verifying its versioning semantics.

Fixed prototype period:

2020-01-01 through 2020-03-31
based on FIRST PUBLIC AVAILABILITY

not transaction date.

Do not filter by politician or stock.

======================================================================
31. CONGRESSIONAL PROTOTYPE POPULATION
======================================================================

Population:

all event versions in the fixed interval under the frozen table/snapshot
contract, with explicit treatment of superseded versions.

The denominator receipt should preserve:

event ID
member ID
chamber
action
transaction date
first_available_at
superseded_at
printed ticker
resolved ticker
resolution status
amount range
source URL
upstream snapshot version/hash

Do not treat resolved ticker as historical security identity.

======================================================================
32. CONGRESSIONAL ORIGINAL-SOURCE SAMPLE
======================================================================

Select at most 12 events mechanically from the frozen denominator.

No:

member filtering
ticker filtering
amount filtering
purchase-only filtering
famous-politician filtering

Validate official source linkage where available.

Classify:

PRIMARY_SOURCE_VERIFIED

SOURCE_URL_ACCESSIBLE_UNVERIFIED_SEMANTICS

DERIVED_ONLY

SOURCE_UNAVAILABLE

Keep all 12.

======================================================================
33. AFTER THE WINNING SOURCE PROTOTYPE
======================================================================

Evaluate whether the source contract is sufficiently strong to proceed.

Verdicts:

SOURCE_CONTRACT_READY_FOR_DESIGN

SOURCE_CONTRACT_PARTIAL_REMEDIABLE

SOURCE_CONTRACT_REJECT

If PARTIAL_REMEDIABLE:

the remedy must be specific and bounded.

Do not create another general research programme.

======================================================================
34. PREDICTIVE MECHANISM SELECTION
======================================================================

If and only if:

SOURCE_CONTRACT_READY_FOR_DESIGN

select ONE predictive mechanism direction using a frozen non-performance rule.

No returns.

For SEC:

use the existing Phase 4A-R ordering, which was already presented by
source-contract testability / learning value:

1. 8-K Item 2.02 operating-results disclosure
2. 8-K Item 5.02 governance transition disclosure
3. 8-K Items 1.01/2.03/3.02 financing/obligation disclosure

Test them in that order.

Choose the first whose source semantics can be expressed reproducibly from the
denominator.

Do not compare hypothetical profitability.

For Congressional Disclosures:

the first candidate should be:

PUBLICLY DISCLOSED EQUITY PURCHASE ACTIVITY

defined at public disclosure time.

Do not use transaction date as signal time.

Do not include options unless separately supported.

Do not select a politician.

Population remains the complete frozen disclosure frame.

======================================================================
35. CHEAP FEATURE-SEMANTIC TEST
======================================================================

For the chosen mechanism, perform a tiny neutral source-only semantic test.

No market data.

SEC example:

can an accession-specific original 8-K be classified into the target Item/event
category without hindsight or ambiguous absence assumptions?

Congressional example:

can a disclosure event be reproducibly identified as an equity purchase using
the frozen source/event contract?

Keep ambiguous cases UNKNOWN.

Do not force classification.

Maximum:

12 source records.

======================================================================
36. CREATE A PRE-PERFORMANCE DESIGN CANDIDATE
======================================================================

If semantic feasibility passes, create a versioned design candidate.

Do NOT register EXP006 yet.

Suggested artifact:

docs/acceleration/next_experiment_design_candidate.json

and:

docs/acceleration/next_experiment_design_candidate.md

It should specify:

candidate name

estimand_type = PREDICTIVE

source population

information-time field

feature definition

unknown/missing rules

issuer/security mapping requirement

benchmark concept

execution timing concept

cost concept

dependence structure

grouping/clustering concerns

Development geometry proposal

future held-out geometry concept

inference requirements

trial ceiling proposal

materiality concept

known blockers

No performance values.

No effect-size assumption derived from returns.

======================================================================
37. DO NOT REPEAT PHASE 3 INFERENCE MISTAKE
======================================================================

Before recommending experiment freeze, run cheap inference geometry checks.

No real returns.

Use only:

record counts
issuer/member counts
calendar clustering
repeat-event patterns
synthetic worlds

Determine whether the proposed design would have enough meaningful independent
structure for a plausible inference plan.

Do not freeze a method merely because it is convenient.

Do not require perfect real-world inference proof yet.

But reject designs whose sample geometry makes the desired inference obviously
impossible.

======================================================================
38. PREDICTIVE CLAIM — NOT CAUSAL CLAIM
======================================================================

The next experiment need not be causal.

A valid predictive estimand may be:

Given information publicly available at decision time t, does a predeclared
feature predict subsequent net returns relative to a predeclared benchmark?

Do not claim:

the disclosure CAUSED the return.

Phase 4C remains the causal milestone.

======================================================================
39. PROOF V2 DRY COMPILE
======================================================================

If a design candidate exists, run the new Proof Compiler v2 in DESIGN-ONLY mode.

It should produce:

source hashes
denominator receipt hash
source adapter version
external upstream version
feature contract hash
timing status
identity requirements
inference geometry receipt
trial ceiling
code/environment fingerprints

And:

performance_executed = false

performance_authorized = false

experiment_registered = false

Expected result:

STRUCTURALLY_READY_FOR_EXPERIMENT_FREEZE_REVIEW

or an explicit blocker.

======================================================================
40. OPENBB / FINRL MUST NOT DERAIL THIS PASS
======================================================================

The purpose of integrating external projects is to accelerate Research OS.

Do not spend the whole pass building generic adapters for tools we do not need.

OpenBB integration may end at:

ADOPTED_INTERFACE_PATTERN

FinRL may end at:

DEFERRED_PHASE5

scikit-learn may remain:

NOT_INSTALLED_UNTIL_MODEL_REQUIRED

That is a valid useful integration decision.

Congressional Disclosures, temporal window semantics and Nexus local helper
boundaries deserve the most implementation attention.

======================================================================
41. DEPENDENCY POLICY
======================================================================

Do not clone third-party source into this repo.

Prefer:

normal package dependency
clean-room compatible implementation of semantics
optional adapter
subprocess only when justified

If code is directly copied or materially adapted:

preserve license
add attribution
record upstream commit
keep copied surface minimal

Create/update a third-party notice if required.

======================================================================
42. PUBLIC CI
======================================================================

Public CI must remain:

network-free
credential-free
private-raw-data-free
performance-free

Use fake transports / fixtures.

Congressional public tests may use tiny synthetic/example manifests, not the
full external dataset.

Temporal tests are pure.

Nexus local wrapper tests must monkeypatch or structurally prove remote
operations cannot occur.

======================================================================
43. TESTS TO ADD
======================================================================

At minimum cover:

External integration registry validation

Evidence-tier ordering / no accidental promotion

Source-first v1 unchanged regression

Source-first v2 adapter contract

Congressional snapshot hash verification

Congressional historical as-of behavior

Superseded amendment behavior

Transaction date != availability date

Printed ticker != resolved ticker

Unresolved ticker retained

Congressional sourceUrl retained

Chrono-style same-bucket replacement

Elapsed-time expiry

Batch/stream parity

Out-of-order timestamp rejection

Nexus local helper no-remote guard

OpenBB external results cannot satisfy PRIMARY_ORIGINAL gate

FinRL remains non-runtime/deferred unless deliberately changed

Dependency fingerprint includes directly used scientific packages

SEC denominator receipt if SEC wins

Congressional denominator receipt if Congress wins

Neutral sample determinism

No price/return loader in this path

No experiment registration

Proof v2 refuses performance_authorized=true

Historical artifact hashes unchanged

======================================================================
44. REQUIREMENTS
======================================================================

Reconcile dependencies.

Likely:

requirements.txt
    remain minimal runtime/base

requirements-docs.txt
    retain Matplotlib

requirements-research.txt
    explicit directly-used scientific dependencies

Do not arbitrarily upgrade:

duckdb==1.3.2
pyarrow==20.0.0
nexustrade==1.42.0

without a compatibility reason.

If NumPy is direct:

pin it.

If pandas is used:

pin it.

Do not add scikit-learn unless code uses it.

Run fresh-environment import tests if feasible.

======================================================================
45. README
======================================================================

Do NOT perform another giant README rewrite.

Update only what materially changed.

The README should eventually reflect:

- source-first architecture;
- external integration boundary;
- Congressional Disclosures as audited/derived source if integrated;
- elapsed-time signal semantics;
- Nexus local helpers versus blocked execution;
- SEC/congressional winner;
- next design candidate status;
- no profitability established.

Keep it concise.

If README is generated by a renderer, modify the renderer rather than
hand-edit generated sections.

======================================================================
46. MASTER PLAN / AGENTS
======================================================================

Update CURRENT governing documentation.

Do not alter historical reports.

AGENTS.md should gain concise instructions covering:

evidence tiers

source adapters

derived-dataset trust boundaries

Congressional snapshot semantics

temporal window semantics

Nexus remote block

source-first v2

no automatic promotion of external provider records

The master plan should show:

Phase 4A-I:
EXTERNAL_INTEGRATION_AND_SOURCE_CONTRACT

and then the resulting preferred-source/design status.

======================================================================
47. ARTIFACTS
======================================================================

Use repository conventions.

Likely artifacts include:

docs/architecture/external_integrations.md
docs/architecture/external_integrations.json

docs/acceleration/phase4a_integration_plan.md
docs/acceleration/phase4a_integration_report.md

docs/acceleration/phase4a_researchability_v2.json
docs/acceleration/phase4a_researchability_v2_report.md

docs/acceleration/phase4a_source_contract_prototype.json
docs/acceleration/phase4a_source_contract_prototype.md

docs/acceleration/next_experiment_design_candidate.json
docs/acceleration/next_experiment_design_candidate.md

docs/acceleration/phase4a_integration_validation.json

Do not create files for the sake of having files.

======================================================================
48. IMPLEMENTATION ORDER
======================================================================

Proceed approximately:

1. audit current repo;
2. freeze this integration plan;
3. audit external repos and licenses;
4. record pinned upstream SHAs;
5. build integration registry;
6. implement evidence tiers;
7. implement source adapter v2 contract;
8. implement Congressional adapter;
9. implement Congressional as-of/version semantics;
10. implement small temporal-window primitives from chrono-ta semantics;
11. implement Nexus local-only wrapper if useful;
12. implement OpenBB-compatible provider boundary only as needed;
13. record FinRL deferral/future interface findings;
14. reconcile scientific dependencies;
15. build proof compiler v2 design-only mode;
16. run public tests before any source requests;
17. freeze Researchability v2 comparison rule;
18. run bounded SEC/Congressional comparison;
19. select winner mechanically;
20. run ONE bounded source-contract prototype;
21. if ready, run tiny feature-semantic test;
22. if ready, create ONE predictive design candidate;
23. run synthetic/sample-geometry feasibility checks;
24. dry-compile design with Proof v2;
25. update current docs/README minimally;
26. full tests;
27. preservation audit;
28. logical commits;
29. push main;
30. verify hosted CI;
31. STOP.

Do not stop after step 3 with an audit-only report.

======================================================================
49. COMMIT STRUCTURE
======================================================================

Use small auditable commits.

A sensible pattern:

1.
Record external integration scope and third-party audit

2.
Add evidence tiers and source-adapter v2 boundary

3.
Integrate Congressional disclosure snapshot/as-of semantics

4.
Add elapsed-time signal primitives and local Nexus-safe helpers

5.
Add design-only proof compiler v2 and dependency provenance

6.
Run source-first v2 and freeze preferred surface

7.
Certify bounded source-contract prototype

8.
Prepare next predictive design candidate

9.
Update governing documentation and validation receipts

Adjust if repository structure suggests a cleaner sequence.

Do not put all work into one giant commit.

======================================================================
50. STOP CONDITIONS
======================================================================

Stop rather than inventing a workaround if:

an external license is incompatible;

a required source requires paid access;

Congressional snapshot integrity cannot be verified;

official-source linkage materially contradicts derived records;

source-first v2 has no eligible surface;

both SEC and Congress have BLOCKED denominator/PIT/reproducibility gates;

the source-contract prototype fails fundamentally;

the proposed predictive design has obviously unusable independent geometry;

a dependency change breaks historical reproduction;

Nexus integration would require remote execution;

a task would expose performance;

a full-market price corpus becomes necessary;

owner-only Test/paper/live authorization would be required.

Do not route around a stop.

======================================================================
51. PERFORMANCE BOUNDARY
======================================================================

This instruction does NOT authorize:

stock price acquisition for the candidate

future returns

backtesting

abnormal returns

alpha

Sharpe

Sortino

drawdown

strategy comparison

holding-period search

threshold optimization

Development performance

held-out access

Nexus remote jobs

Aurora

paper trading

live trading

The purpose is to get the software and source contract READY so the next owner
decision can be:

FREEZE THIS DESIGN AND RUN DEVELOPMENT

rather than another architecture review.

======================================================================
52. FINAL VERDICT
======================================================================

At completion assign one overall status:

READY_FOR_EXPERIMENT_FREEZE_REVIEW

SOURCE_CONTRACT_PARTIAL_REMEDIABLE

INTEGRATION_BLOCKED

READY_FOR_EXPERIMENT_FREEZE_REVIEW requires:

external integration completed;

historical v1 evidence preserved;

one preferred source selected under frozen rule;

source denominator prototype passed;

availability semantics explicitly classified;

feature semantics reproducible;

sample/dependence geometry not obviously impossible;

design-only proof compile passes;

no performance observed.

======================================================================
53. FINAL DELIVERY
======================================================================

Report:

exact HEAD

all commits

external repos audited

upstream SHAs/versions/licenses

integration decision for each repo

new runtime dependencies

dependency versions

evidence-tier implementation

source-adapter v2 implementation

Congressional adapter status

Congressional point-in-time validation results

Chrono-derived temporal primitives added

Nexus local-only integration result

OpenBB integration decision

FinRL integration/defer decision

NumPy/pandas/sklearn/Matplotlib dependency decisions

Researchability v2 matrix

SEC vs Congressional selection result

exact source-selection rule outcome

research-source request totals

source-contract prototype result

denominator size

neutral sample size

timing statuses

identity/mapping status

selected predictive mechanism, if any

sample/dependence geometry

Proof v2 dry-compile result

overall readiness verdict

local test count

public test count

hosted CI result

preservation audit

exact next owner decision required

Then STOP.

======================================================================
54. OWNER INTENT
======================================================================

This work is intended to speed Research OS up.

Do not turn a list of useful repositories into another year-long infrastructure
rewrite.

Use external projects where they concretely solve a problem.

Reject or defer them where they do not.

Congressional Disclosures is especially promising because much of the difficult
source/version/public-availability machinery already exists in an auditable
open-source form.

Chrono-TA provides useful time semantics.

NexusTrade-PY contains useful local machinery but remote execution remains
uncertified.

OpenBB demonstrates a useful provider boundary.

FinRL is likely a later portfolio/risk concern.

NumPy/pandas/scikit-learn/Matplotlib are tools, not research truth.

Research OS remains the authority for:

what source evidence is trusted;

what was known when;

what population existed;

which security is represented;

what experiment was frozen;

how many trials were attempted;

what inference is valid;

and whether evidence may advance.

The target outcome is not "more integrations."

The target outcome is:

a cleaner Research OS,
a genuinely researchable source,
and one concrete predictive design that is finally close to being run.

Proceed through implementation and the bounded source-contract continuation
without stopping for intermediate owner approval unless a stop condition above
is reached.