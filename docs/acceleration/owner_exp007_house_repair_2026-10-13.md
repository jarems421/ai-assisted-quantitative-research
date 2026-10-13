You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
7451373705b09f152107a88af69aec4ee2199cf5

======================================================================
OWNER DECISION
EXP007 — FINAL HOUSE-ONLY ORIGINAL-SOURCE REPAIR
======================================================================

Current state:

ORIGINAL_SOURCE_VALIDATION_BLOCKED

EXP007 remains:
PROPOSED
UNREGISTERED
UNFROZEN

Performance evaluations = 0.
Confirmation outcome accesses = 0.

The existing 96-observation validation sample contains:

61 House observations
35 Senate observations

Observed original validation:

27 decisive original matches
0 observed disagreements
34 House image-only / empty text projections
35 Senate observations unavailable after one preserved HTTP 403 route stop

The owner now authorizes ONE final source-feasibility revision:

REDEFINE THE CANDIDATE AS HOUSE-ONLY.

Do NOT attempt another Senate automated-access campaign.

Do NOT retry/bypass the preserved Senate 403.
Do NOT accept legal/access agreements on the owner's behalf.
Do NOT use alternate hosts, mirrors, cookies, session tricks or scraping.

The Senate evidence remains historically preserved as an inaccessible route for
this experiment.

The new proposed experiment is:

HOUSE COMMON-EQUITY PURCHASE DISCLOSURE
vs
SPY
over 20 sessions.

This revision occurs before any EXP007 market outcome has been accessed.

======================================================================
1. PRESERVE V001
======================================================================

Do not overwrite:

docs/acceleration/exp007_source_validation_report.md
docs/acceleration/exp007_original_validation_sample.json
existing snapshot/schema receipts
Senate 403 body/receipt
House PDF bodies/projections
all v001 contracts

Create a separately versioned candidate:

EXP007 design v002

recording that the scope changed from:

Congressional / House + Senate

to:

HOUSE ONLY

because direct official-original validation is available from the House route
while the authorized Senate route is not.

This is a source-access decision, not a return-selected decision.

======================================================================
2. HYPOTHESIS
======================================================================

Estimand type:

PREDICTIVE

No causal claim.

Hypothesis:

When a U.S. House member's disclosed purchase of a listed common equity becomes
publicly available under the declared modeled information-time contract, the
purchased security may exhibit positive subsequent SPY-relative return.

Primary outcome:

mean net 20-session return of eligible purchased security
minus
SPY return over the same entry/exit window.

Do not call this alpha.

No:

member ranking
party split
committee effect
amount threshold
amount-bracket search
sector filter
purchase/sale grid
horizon grid
ML

======================================================================
3. SOURCE POPULATION
======================================================================

Primary source surface:

HOUSE disclosure rows only.

Senate rows are OUTSIDE the v002 estimand.

Do not treat Senate unknowns as House source failures.

The source remains:

AUDITED_EXTERNAL_DERIVED

with official House original validation.

Do not promote the snapshot to PRIMARY_ORIGINAL.

Preserve:

snapshot revision
manifest hash
file hashes
event/version chronology
source URLs
raw document hashes
printed/resolved ticker distinction

======================================================================
4. REUSE THE FROZEN HOUSE SAMPLE
======================================================================

Do not select a new favorable validation sample.

Use the existing:

61 House observations

from the already frozen 96-record v001 sample.

They are the v002 House validation frame.

Current state:

27 decisive
34 image-only / empty-text UNKNOWN

No replacement rows.

No outcome-selected substitutions.

No extra easy PDFs added to improve validation rate.

======================================================================
5. OCR IS AUTHORIZED ONLY FOR THE 34 FROZEN HOUSE ORIGINALS
======================================================================

The 34 House PDFs are official original documents already acquired.

Their current UNKNOWN status results from image-only / empty-text projection.

A bounded OCR repair is authorized.

No cloud OCR.

No LLM transcription API.

No network OCR.

Use a deterministic local OCR pipeline.

Prefer existing system tools if present.

If a new OCR dependency is necessary:

keep it isolated exactly as the pypdf helper was isolated;
pin exact versions/hashes where feasible;
record license/inventory;
do not alter canonical research requirements unless genuinely required.

Render only the necessary pages.

Retain:

original PDF SHA256
page number
render hash
OCR-engine/version
OCR text hash
bounding/source provenance where supported

The OCR output is:

DERIVED_PROJECTION_OF_PRIMARY_ORIGINAL

not a new primary source.

======================================================================
6. OCR MUST NOT BE GUIDED BY EXPECTED SNAPSHOT VALUES
======================================================================

Do NOT search the image specifically for the expected:

action
date
ticker
asset

and call a matching hit validation.

Instead:

OCR the relevant transaction table/page generally

then independently parse rows

then associate source rows

then compare the extracted fields against the snapshot.

Expected dataset values must not influence OCR transcription.

No accession/member-specific string patch.

======================================================================
7. HOUSE ORIGINAL FIELD VALIDATION
======================================================================

For all 61 frozen House observations compare:

document identity
member identity
transaction type
transaction date
asset description
printed ticker where present

against the official House original.

Retain:

AGREE
DISAGREE
UNKNOWN

per field.

The upstream resolver's corrected ticker is NOT required to appear in the
original.

Only printed ticker is original-source comparable.

======================================================================
8. PREDECLARED SOURCE PASS CRITERIA
======================================================================

Freeze these criteria BEFORE OCR results are reviewed.

HOUSE SOURCE VALIDATION passes only if:

A. At least 55 of 61 frozen House observations
   (>=90.16%)
   obtain decisive original validation for:

   transaction type
   transaction date
   asset description

AND

B. PURCHASE CLASSIFICATION:

   zero confirmed purchase/non-purchase classification disagreements

AND

C. Among decisive rows:

   transaction-date agreement >= 98%

   transaction-type agreement >= 98%

   asset-description normalized agreement >= 95%

AND

D. No systematic unresolved cluster clearly tied to:

   purchases specifically
   early years
   printed-ticker presence
   amendments

that would undermine the declared source-resolved estimand.

Do not weaken these thresholds after OCR.

If this gate fails:

ABANDON_EXP007_SOURCE_FEASIBILITY

and STOP.

No third source repair.

======================================================================
9. SOURCE-RESOLVED ESTIMAND
======================================================================

If House validation passes, define the estimand explicitly as applying to:

SOURCE-RESOLVED HOUSE COMMON-EQUITY PURCHASE DISCLOSURES

not:

all congressional trades
all House trades
all legally required disclosures.

Unknown source records remain outside both event and control claims.

Report missingness.

======================================================================
10. DEVELOPMENT / CONFIRMATION
======================================================================

Retain the existing source-only chronological split unless House-only geometry
makes it mechanically invalid:

Development:
2014-01-01 through 2021-12-31

Workflow-held-out confirmation:
2022-01-01 through 2025-12-31

Confirmation market outcomes remain unopened.

If House-only source geometry has no usable eligible stock observations in an
early year, that year may simply contribute zero events.

Do NOT move Development inception to optimize event count or returns.

If House-only geometry cannot support at least four calendar years containing
eligible events:

SOURCE_GEOMETRY_BLOCKED.

======================================================================
11. EVENT CLASSIFICATION
======================================================================

Eligible event source state must be an unequivocal:

PURCHASE

of a common/listed equity.

Exclude:

sales
exchanges not clearly purchases
options
warrants
bonds
funds / ETFs where identified
private securities
crypto
unknown asset types
other non-common-equity assets

Unknown is not equity.

Do not use amount as an eligibility rule.

======================================================================
12. VERSION / AS-OF SEMANTICS
======================================================================

Retain existing:

firstAvailableAt
availableAt
supersededAt

semantics.

Future amended versions must not rewrite prior event state.

Use only the version that existed at the modeled decision time.

Retain contributor filtering by information time.

======================================================================
13. AVAILABILITY
======================================================================

Keep:

UPSTREAM_MODELED_EOD_NOT_OBSERVED_PUBLIC

Exact public timestamp remains UNKNOWN.

Use the already proposed conservative rule:

eligible entry =
09:30 America/New_York
on the SECOND regular NYSE session strictly after
the New York civil date implied by the latest effective event/version
availability bound.

No same-day trade.

No first-session trade.

Validate:

weekends
holidays
DST
stage edges

before outcomes.

======================================================================
14. SECURITY IDENTITY
======================================================================

Use the source-defined fields:

printedTicker
resolvedTicker
resolutionStatus
resolutionReason

as distinct fields.

Rules:

resolutionStatus=printed:
printed ticker remains the candidate symbol;
resolvedTicker may legitimately be null.

resolutionStatus=resolved:
retain both printed and resolved values.

unresolved:
UNRESOLVED_SECURITY.

Never silently overwrite printed ticker.

No current-ticker projection backward.

======================================================================
15. PROVIDER/PATH CERTIFICATION
======================================================================

If House source validation passes, continue automatically.

Use an existing configured market-data provider.

No purchase or upgrade.

For each distinct candidate security/decision date certify:

historically tradable common equity at entry

provider identifier / symbol mapping

entry session exists

20th-session exit can be economically valued

corporate-action continuity

If applicable handle:

split
cash dividend
ticker rename
merger
delisting
security cancellation
stock consideration
cash consideration

Do not require a complete multi-year listing span outside the 20-session path.

Do not drop ended securities.

======================================================================
16. PERFORMANCE VALUES REMAIN SEALED
======================================================================

Before freeze, provider certification may inspect:

metadata
session existence
corporate actions
identifier continuity
null/non-null availability

but must not calculate or summarize:

event return
SPY-relative return
20-session P&L
mean return
Sharpe
alpha

Add hard guards.

======================================================================
17. EVENT AGGREGATION
======================================================================

Freeze before outcomes:

PRIMARY EVENT KEY =
stable security identity
+
modeled eligible entry date

Multiple House disclosures mapping to the same security and same eligible entry
become one primary trading observation.

Retain:

number of filings
number of members
source lineage

for description only.

Do not weight the primary outcome by number of lawmakers/disclosures.

Same security on later eligible dates remains a separate event.

======================================================================
18. SPY BENCHMARK
======================================================================

The single formal benchmark is SPY.

Primary paired observation:

security 20-session total return
minus
SPY total return over identical entry/exit dates
minus
10 bps per side security transaction costs.

Do not add alternative benchmarks.

======================================================================
19. INFERENCE
======================================================================

Before real outcomes:

use actual House event geometry
with synthetic outcomes only.

Maximum THREE inference procedures.

Must account for:

repeated securities
repeated members
calendar clustering
market shocks
20-session overlap
unequal yearly frequency

Select primarily by:

null rejection near 5%
95% coverage
common-factor robustness
compatibility with event geometry

not power alone.

Retain failed methods.

Freeze selected inference before returns.

======================================================================
20. POWER
======================================================================

Synthetic outcomes only.

Evaluate:

0.00 pp
+0.50 pp
+1.00 pp

under actual House geometry.

If the +0.50 pp materiality effect is effectively untestable:

POWER_BLOCKED.

Do not add Senate merely to improve power.

======================================================================
21. MATERIALITY / COST / TRIAL CEILING
======================================================================

Retain:

20-session horizon

10 bps per side base cost

future robustness:
20 bps per side
+1-session delayed entry

materiality:

mean net SPY-relative return >= +0.50 percentage point

AND

positive two-sided 95% lower confidence endpoint versus zero

fresh real-performance ceiling:

8 evaluations

No return-derived changes.

======================================================================
22. PRE-PERFORMANCE FREEZE
======================================================================

If:

House original-source validation passes

provider/path certification passes

event geometry passes

inference calibration passes

power passes

Proof v2 passes

then create/register:

EXP007_HOUSE_PURCHASE_DISCLOSURE

or repository-consistent equivalent.

Freeze hashes for:

snapshot
House source-validation certificate
event classifier
version semantics
availability
security identity
provider
aggregation
stage split
entry/exit
corporate actions
SPY benchmark
cost
inference
materiality
trial ceiling
code/environment

At freeze:

performance_executed=false
confirmation_accesses=0

Commit and PUSH:

PRE-PERFORMANCE FREEZE

before any Development result exists.

Do not amend it afterward.

======================================================================
23. DEVELOPMENT
======================================================================

Only after the pushed freeze exists:

run exactly ONE primary Development evaluation.

No:

new source scope
Senate reintroduction
member ranking
party split
amount threshold
new horizon
new benchmark
new inference
new aggregation
new identity rule

after observing performance.

Confirmation outcomes remain unopened.

confirmation_access_count=0.

======================================================================
24. VERDICT
======================================================================

Use only:

DEVELOPMENT_FAIL
DEVELOPMENT_MIXED
DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS requires BOTH:

mean net 20-session SPY-relative return >= +0.50 pp

AND

positive two-sided 95% lower endpoint versus zero.

If fail:

retain it and STOP.

Do not redesign House purchases in this task.

If pass:

STOP before confirmation.

======================================================================
25. FINAL ABANDONMENT RULE
======================================================================

This is the final source-validation repair for EXP007.

If the frozen 61-House original sample cannot satisfy the source-validation
criteria after the bounded OCR pass:

ABANDON_EXP007_SOURCE_FEASIBILITY.

Do NOT:

create another sample
lower thresholds
restart Senate
add a new OCR/cloud provider
change chambers again
select modern years only
search another original source route
start another source rescue

Preserve the hypothesis as untested.

======================================================================
26. TESTS
======================================================================

Add focused tests for:

OCR provenance linkage to PDF/page/render

expected-value-independent row extraction

House purchase classification

transaction date comparison

asset normalization

printed ticker comparison

unknown OCR stays UNKNOWN

Senate excluded from v002 population

future amendment not rewriting past state

modeled second-session availability

unresolved security fails closed

same-security/date deduplication

corporate-action path

SPY paired dates

outcomes inaccessible before freeze

confirmation inaccessible

freeze before Development artifact

Public CI remains network-free and must not require OCR binaries.

======================================================================
27. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

HOUSE SOURCE VALIDATION:

61 frozen observations
prior text-readable decisive count
OCR attempted count
final decisive count
unknown count

field agreement:
transaction type
transaction date
asset description
printed ticker

source gate PASS/FAIL

If continuation proceeds:

House purchase candidate count
common-equity count
identity/provider/path count
unique primary events
events by year
inference calibration
synthetic power

If frozen:

experiment ID
spec hash
freeze commit

If Development runs:

event count
unique securities
mean net SPY-relative 20-session return
95% CI
p-value
materiality result
Development verdict

confirmation accesses MUST equal zero.

Then STOP.

======================================================================
28. OWNER INTENT
======================================================================

Do not spend another day proving that one Senate automated route returns 403.

The House has an accessible official disclosure surface.

The remaining House source-validation gap is primarily 34 image-only official
documents, which is a bounded extraction problem.

Resolve that once.

If House original validation passes:

continue all the way toward freeze and Development.

If it fails:

close EXP007.

No more source-search loops.