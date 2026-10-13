You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
65b04ab877cd6359748d4528de45a29bfc516fb6

======================================================================
OWNER DECISION
EXP006 — ACCEPT EXPLICIT SOURCE MISSINGNESS AND CONTINUE TO IDENTITY
======================================================================

Historical filing-population reconstruction is complete.

Current state:

HISTORICAL_ITEM_STATUS_BLOCKED

because:

113 original source keys
across
107 accessions

remain without authoritative Item membership.

The owner now makes the following explicit scientific decision:

THESE 113 KEYS DO NOT BLOCK FURTHER EXP006 CLOSURE.

They remain permanently:

UNKNOWN_ITEM_STATUS

unless future already-authorized evidence resolves them.

They must never be:

treated as Item 2.02;
treated as non-Item 2.02;
used as controls;
imputed to zero activity;
dropped from source-missingness reporting.

No new broad source-recovery campaign is authorized for them.

The experiment's defensible source population claim is:

The union of archived SEC Development daily master-index observations,
reconciled against the present rebuilt quarterly census, with quarterly-only,
daily-only, amendment, cofiler, duplicate/version and unresolved states
explicitly retained.

This is NOT a claim of:

every legally required filing;
perfect contemporaneous ingestion;
zero PAC/deletion uncertainty;
or an untouched historical database snapshot.

Proceed to historical security identity.

If identity and all later gates pass, continue automatically to:

market-data certification
matching
inference calibration
synthetic power
Proof v2
EXP006 freeze
and Development.

Do not request another planning approval unless a genuine stop condition occurs.

======================================================================
1. PRESERVE CURRENT SOURCE HISTORY
======================================================================

Read and preserve:

docs/acceleration/exp006_historical_population_report.md
docs/acceleration/exp006_historical_population_certificate.json
docs/acceleration/exp006_historical_population_certificate_v003.json
docs/acceleration/exp006_historical_population_reconciliation.json
docs/acceleration/exp006_historical_header_review_v002.json

docs/acceleration/exp006_date_repair_report.md
docs/acceleration/exp006_availability_contract_v003.json
docs/acceleration/exp006_primary_title_review_v003.json

and all previous failed/pass receipts.

Do not rewrite:

the 404 evidence;
the 107 unresolved accessions;
the failed earlier source representations;
the daily/quarterly differences;
the prior timing results.

Historical truth remains historical truth.

======================================================================
2. SOURCE-MISSINGNESS CONTRACT
======================================================================

Create a compact versioned EXP006 source-missingness contract.

States must include at minimum:

ITEM202_CONFIRMED
NON_ITEM202_CONFIRMED
UNKNOWN_ITEM_STATUS
AMENDMENT_VERSION_ONLY

Current known counts include:

known original Item 2.02 source keys = 108,532
known original legal-filer/accession pairs = 108,364
known candidate accessions = 105,928
known candidate legal-filer CIKs = 6,189
non-Item source keys = 318,749
amendments = 11,944
unknown original source keys = 113
unknown original accessions = 107

Do not silently recompute these with a different historical definition.

Unknown Item filings:

cannot be event observations;
cannot be control observations.

They remain in source accounting.

======================================================================
3. MISSINGNESS SENSITIVITY — PREDECLARE NOW
======================================================================

Before any post-event returns exist, freeze a source-missingness sensitivity
requirement.

At minimum report future EXP006 results alongside:

unknown source-key count;
unknown count by year;
unknown count relative to confirmed Item events;
unknown identity coverage if identity is later obtained;
concentration by issuer/year where measurable.

The current unresolved key distribution is:

2015: 9
2016: 21
2017: 10
2018: 8
2019: 3
2020: 62

Do not use performance to decide whether missingness is acceptable.

No arbitrary requirement of zero unknowns is imposed.

If later evidence shows unknowns are strongly concentrated in a source,
identity, or lifecycle category that could materially bias the experiment,
report that and stop if necessary.

======================================================================
4. IDENTITY IS NOW THE PRIMARY GATE
======================================================================

The main scientific question is:

For each confirmed original Item 2.02 filing, what exact tradable security /
share class existed at the modeled decision date?

Do NOT resolve identity event-by-event if a dated issuer/security span can serve
many events.

Scale at:

issuer
security class
listing span

level.

Current candidate legal-filer CIK scale is approximately:

6,189

not 108k independent identity problems.

======================================================================
5. FULLY RESOLVED IDENTITY DEFINITION
======================================================================

A candidate event is FULLY_RESOLVED only if the repository can establish,
at the event decision date:

issuer CIK

exact tradable security/share class

domestic common-equity eligibility

historical ticker or provider lookup symbol

stable security/provider identifier

dated effective span containing the event date

listing/venue context where available

and sufficient lifecycle information to value the planned 20-session path.

Keep separate:

issuer CIK
legal filer CIK
submitting filer
security
share class
ticker
exchange
share-class FIGI
composite FIGI
provider ID

Never project today's ticker backwards.

Never select the first OpenFIGI match arbitrarily.

Never require a security to survive to the present.

======================================================================
6. GOVERNING COVERAGE STANDARD
======================================================================

Retain the repository's existing 95% fully-resolved identity standard unless an
already-governing later contract supersedes it.

Do NOT lower the standard merely to make EXP006 executable.

Measure coverage on the actual confirmed Item 2.02 event population.

Report additionally:

coverage by year
coverage by issuer
coverage for ended securities
coverage for renamed securities
coverage for multiple-class issuers

A global 95% number is not sufficient if early years or dead securities fail
systematically.

======================================================================
7. FREEZE A SOURCE-ONLY IDENTITY FEASIBILITY SAMPLE
======================================================================

Before scalable remote identity calls, freeze a deterministic sample of at most:

240 confirmed Item 2.02 events.

Cover:

2015–2020
all quarters
repeat-filing issuers
single-event issuers
shared-accession/cofiler cases

and where discoverable using PRE-OUTCOME source metadata only:

ticker changes
multiple common classes
mergers
ended listings
ambiguous identifiers

Do not select based on:

future return
price performance
company fame
survival
known market-data convenience

Push/freeze the sample before remote calls.

======================================================================
8. TEST MAXIMUM THREE IDENTITY ROUTES
======================================================================

Test no more than three serious routes.

ROUTE A — SEC PRIMARY EVIDENCE

Use dated SEC material available on or before the event date:

8-K cover metadata
nearest prior 10-Q
nearest prior 10-K
structured cover-page data
historical ticker
security title
exchange/listing fields

This is preferred evidence for what the issuer itself represented at the time.

ROUTE B — SEC + OPENFIGI

Use SEC-dated identifiers/symbol/class evidence as OpenFIGI query inputs.

OpenFIGI may resolve:

share-class FIGI
composite FIGI
candidate security identifiers

but current OpenFIGI metadata alone does NOT establish historical validity.

Multiple plausible classes => AMBIGUOUS.

ROUTE C — EXISTING CONFIGURED MARKET-DATA METADATA

Inspect existing configured providers such as:

Tiingo
FMP

only if credentials already exist.

Do not expose or commit secrets.

Use only metadata capabilities relevant to:

historical symbols
permanent IDs
listing periods
ended securities
corporate actions

No purchase or plan upgrade.

Do not use post-event returns.

======================================================================
9. EXP002 / NEXUS HISTORICAL DATA
======================================================================

EXP002 previously observed local historical security segments containing fields
such as:

ticker
security_id
share_class_figi
CIK
from_date
to_date
asset_type

Those artifacts may be used only according to their certified historical status.

They may provide:

DISCOVERY_ONLY
CORROBORATION_ONLY

unless current EXP006 evidence independently certifies them.

Do not promote the old underfilled Nexus/Lake universe into canonical EXP006
identity.

No Nexus historical execution.

No Aurora.

No new remote Nexus operations.

======================================================================
10. SELECT THE IDENTITY ROUTE BEFORE SCALING
======================================================================

Compare feasibility routes on:

dated evidence quality
exact-class resolution
historical ticker coverage
permanent-ID coverage
multiple-class ambiguity
rename coverage
ended-security coverage
request cost
reproducibility

Do NOT select based on future return availability.

Choose and freeze the identity method before scaling.

Retain failed routes.

======================================================================
11. SCALE USING DATED SPANS
======================================================================

Once one route passes:

construct reusable dated security/class spans for relevant issuers.

Example conceptual record:

issuer_cik
security_id
share_class_figi
ticker
exchange
asset_type
valid_from
valid_to
evidence_sources
provider_id
resolution_status

One span should serve all compatible events in that interval.

Do not request the same issuer/security mapping repeatedly for each filing.

Cache deterministic results.

======================================================================
12. MULTIPLE SHARE CLASSES
======================================================================

If an issuer has exactly one supported domestic listed common-equity class on
the event date:

use it.

If multiple eligible common classes exist:

do NOT choose arbitrarily.

Freeze a deterministic PRE-OUTCOME rule.

Permissible inputs may include:

issuer-declared principal class
dated listing evidence
pre-event liquidity

but no post-event outcome.

If no defensible deterministic rule exists:

mark the event AMBIGUOUS_CLASS.

======================================================================
13. COFILERS / SHARED ACCESSIONS
======================================================================

Do not deduplicate merely by accession.

Resolve:

legal filer
security issuer
security class

first.

Only after identity resolution aggregate to the actual tradable decision key:

security_id
class_id
decision_date

Preserve all source accession lineage.

One corporate disclosure must not accidentally generate duplicate independent
trades merely because multiple legal filers share the accession.

======================================================================
14. ENDED / RENAMED SECURITY COVERAGE
======================================================================

Explicitly identify cases involving:

ticker rename
exchange transfer
merger
delisting
bankruptcy
class conversion
security cancellation
stock consideration
cash consideration

A security that disappeared later is NOT ineligible merely because it is gone
today.

For every eligible event whose planned 20-session holding path crosses a
terminal event, the eventual execution layer must be able to determine economic
value.

Do not:

drop it
forward-fill forever
replace it with survivor
assign zero

without evidence.

======================================================================
15. IDENTITY PASS / STOP
======================================================================

Produce:

confirmed Item 2.02 event candidates
unique issuers
fully resolved events
ambiguous events
unresolved events

coverage %

coverage by year

multiple-class count

rename count

ended-security count

terminal-path-required count

missingness reasons.

If the governing 95% identity standard fails:

STOP at HISTORICAL_IDENTITY_BLOCKED.

Do not shrink Development years.

Do not silently exclude difficult issuers.

If the global threshold passes but dead/renamed/early-year coverage is
materially worse, assess whether that creates survivor bias before proceeding.

======================================================================
16. PRE-EVENT MARKET DATA IS ALLOWED ONLY FOR CERTIFICATION
======================================================================

Before freeze, provider observations are allowed only when strictly needed for:

identity
listing validity
corporate actions
pre-event liquidity
pre-event matching variables

No post-event event returns.

No 20-session outcomes.

No strategy P&L.

No alpha.

No confirmation outcomes.

Add explicit programmatic boundaries if useful.

======================================================================
17. MARKET-DATA PROVIDER CERTIFICATION
======================================================================

If identity passes, continue automatically.

Freeze a tiny provider certification sample covering where possible:

ordinary listed equity
split
cash dividend
ticker rename
ended/delisted class
merger or terminal event

Required provider capabilities:

historical OPEN prices

corporate actions

stable historical identifiers

renames

ended-security observations

reproducible requests

No paid upgrade.

No survivor-only provider.

If no configured source can preserve the required population:

STOP at MARKET_DATA_BLOCKED.

======================================================================
18. MATCHING CONTRACT
======================================================================

If provider certification passes:

freeze the existing owner-approved formal comparison rule BEFORE loading
post-event outcomes.

Use only pre-event:

industry
size
momentum
calendar proximity

No outcome-based matching.

No future fields.

No post-result weight adjustment.

Use deterministic tie-breaking.

Missing valid match => UNAVAILABLE_MATCH.

Unknown Item-status filings may NOT be controls.

SPY remains descriptive only.

Hash the matching procedure before Development outcomes.

======================================================================
19. INFERENCE CALIBRATION
======================================================================

Continue automatically.

Use actual event/matching geometry and SYNTHETIC outcomes only.

Evaluate at most THREE candidate inference procedures.

Stress:

repeated issuers

earnings-season clustering

calendar/common-factor shocks

industry shocks

persistent common components

20-session overlap

heterogeneous effects

unequal yearly event counts

missing controls

Choose primarily by:

null rejection near 5%

coverage near 95%

persistent-common-factor robustness

compatibility with actual geometry.

Do not choose based on power alone.

Retain failed methods.

Freeze the selected procedure before real post-event outcomes.

======================================================================
20. POWER
======================================================================

Using synthetic outcomes only, report power under:

0.00 pp
+0.50 pp
+1.00 pp

using actual event/control geometry.

Do not treat filing count as independent N.

If +0.50 pp is effectively untestable under the frozen materiality requirement:

STOP before freeze.

======================================================================
21. SOURCE MISSINGNESS FINAL REVIEW BEFORE FREEZE
======================================================================

Before EXP006 freeze, revisit ONLY the already-defined source unknown set.

Do not conduct another recovery campaign.

Report:

113 source keys / 107 accessions or updated count only if existing evidence
legitimately resolves them

year distribution

share relative to known Item events

whether they cluster by identity/lifecycle category

whether exclusion from both event and control pools materially threatens the
declared estimand.

The primary estimand should be stated explicitly as applying to:

SOURCE-RESOLVED ORIGINAL ITEM 2.02 EVENTS

within the declared reconstructed SEC observation population.

Do not overclaim all legally possible Item 2.02 filings.

======================================================================
22. FREEZE
======================================================================

If every mandatory gate passes:

create:

EXP006_SEC_ITEM202_PREDICTIVE

using repository conventions.

Freeze:

SOURCE:
reconstructed daily/quarterly SEC union
plus explicit UNKNOWN_ITEM_STATUS stratum

FEATURE:
confirmed original 8-K Item 2.02 only

AMENDMENTS:
version lineage only

AVAILABILITY:
v003 conservative date-envelope rule

DEVELOPMENT:
2015-01-01 through 2020-12-31

CONFIRMATION:
2021-01-01 through 2026-09-30

HORIZON:
20 regular trading sessions

COST:
10 bps per side

ROBUSTNESS:
20 bps per side
+1-session delay

MATERIALITY:
paired net mean >= +0.50 percentage point
AND
positive two-sided 95% lower confidence endpoint

TRIAL CEILING:
12

IDENTITY:
exact frozen dated-span contract

MARKET PROVIDER:
exact frozen certificate

MATCHING:
exact frozen deterministic rule

INFERENCE:
exact selected calibrated method

Run Proof v2.

Required state:

SCIENTIFICALLY_READY_FOR_FREEZE
performance_executed = false
confirmation_accesses = 0

Commit and PUSH the PRE-PERFORMANCE FREEZE.

Do not amend that commit later.

======================================================================
23. DEVELOPMENT
======================================================================

Only after the freeze commit exists:

Development post-event outcomes are authorized.

Run exactly one frozen Development evaluation.

No tuning.

No alternative:

feature
horizon
availability
identity rule
class-selection rule
matching rule
cost rule
inference method

after observing performance.

Historical confirmation remains completely unopened.

confirmation_access_count MUST remain 0.

======================================================================
24. DEVELOPMENT VERDICT
======================================================================

Use:

DEVELOPMENT_FAIL
DEVELOPMENT_MIXED
DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS requires BOTH:

paired net 20-session mean >= +0.50 percentage point

AND

positive two-sided 95% lower confidence endpoint versus zero.

Do not promote merely positive performance.

Do not redesign Item 2.02 in this task after a fail.

A negative result is a successful research result.

======================================================================
25. REQUEST DISCIPLINE
======================================================================

Do NOT:

retry the 107 unresolved source accessions through another broad campaign

download huge Feed/Oldloads archives

rerun the 1,500 daily population files

start another architecture phase

add another external data framework

buy data

use Nexus remotely

use Aurora

Identity requests must be cached and issuer/span-oriented.

Respect existing OpenFIGI/Tiingo/FMP limits.

======================================================================
26. REQUIRED OUTPUTS
======================================================================

Prefer:

one compact source-missingness contract

one identity feasibility receipt

one final identity certificate/report

then only if later gates pass:

market provider certificate

matching contract

inference certificate

EXP006 spec

Development report.

Do not generate ceremonial duplicates.

======================================================================
27. TESTS
======================================================================

Add focused tests for:

UNKNOWN_ITEM_STATUS excluded from event pool

UNKNOWN_ITEM_STATUS excluded from controls

amendment never independent signal

dated class span contains event date

current ticker cannot define past identity

ambiguous OpenFIGI candidates fail closed

multiple common classes use frozen rule or remain ambiguous

rename preserves stable identity

ended security is not survivor-filtered out

terminal event cannot be silently dropped

pre-event provider boundary

post-event outcomes inaccessible before freeze

confirmation inaccessible

identity coverage calculation

year-level identity missingness

freeze commit precedes performance artifact

historical population receipts unchanged

Public CI remains network-free.

======================================================================
28. FINAL DELIVERY
======================================================================

Report:

starting HEAD
final HEAD
commits
hosted CI

SOURCE:
known Item events
unknown Item status
year distribution
exact source population claim

IDENTITY:
sample size
routes evaluated
selected route
unique candidate issuers
fully resolved events
ambiguous
unresolved
coverage %
coverage by year
multiple-class cases
renames
ended classes
terminal paths

If continuation passes:

market provider certificate
matching coverage
inference calibration
synthetic power

If frozen:

EXP006 spec hash
freeze commit SHA

If Development runs:

eligible events
matched pairs
net paired mean
95% CI
p-value
materiality verdict
Development verdict

confirmation accesses MUST equal zero.

Then STOP.

======================================================================
29. OWNER INTENT
======================================================================

The historical population has been reconstructed.

Do not let 107 honestly missing historical source records force an impossible
zero-missingness standard.

Scientific rigor means:

preserve them,
label them,
exclude them symmetrically from event and control classification,
measure the missingness,
and disclose its limits.

It does NOT mean research can proceed only when every historical byte exists.

The main remaining challenge is now historical security identity.

Solve that at issuer/security-span scale.

If identity passes, keep moving toward the frozen experiment and the first
real Development result.

Do not create another planning loop.