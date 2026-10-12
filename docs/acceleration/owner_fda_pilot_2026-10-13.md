You are continuing Research OS Phase 4A.

Repository:

C:\Users\runni\quant\

GitHub:

jarems421/ai-assisted-quantitative-research

Branch:

main

Expected current HEAD:

1529838ec711520c3f1f5ba54f9e718bc60c5eda

Recent procurement-pilot commits:

ace4dc9 — Freeze approved procurement pilot manifest and bounded access controls
f74899e — Retain procurement access denial and all twelve source-pilot slots
1529838 — Close procurement pilot cheaply at its official publication-channel gate

======================================================================
OWNER DECISION
======================================================================

The procurement source-only pilot is closed.

Canonical disposition:

PROCUREMENT_FAMILY_REJECT
SOURCE_CHANNEL_BLOCKED

This is a rejection of the approved frozen publication-channel/frame.

It is NOT proof that:

- all government procurement research is impossible;
- procurement has no economic effect;
- USAspending is unusable;
- every official publication channel is inaccessible.

Do NOT reopen the procurement pilot.

Do NOT retry the blocked route.

Do NOT look for mirrors/proxies/workarounds.

Preserve it as institutional negative evidence.

The owner now authorizes the next Phase 4A cheap-feasibility candidate:

FDA DRUG REGULATORY DECISIONS

Status:

FDA_FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY

This is NOT:

EXPERIMENT_APPROVED
EXPERIMENT_REGISTERED
EXPERIMENT_FROZEN
PERFORMANCE_AUTHORIZED
CAUSAL_CLAIM_AUTHORIZED
PHASE4B_AUTHORIZED
PHASE4C_AUTHORIZED
PAPER_AUTHORIZED
LIVE_AUTHORIZED

EXP004 remains paused.

EXP005 remains abandoned and absent.

No Phase 3 work is reopened.

======================================================================
1. PURPOSE
======================================================================

The purpose is to answer cheaply:

Can FDA drug regulatory decisions support a scientifically defensible,
point-in-time public-company event experiment?

The most important question is NOT initially:

"Can we download FDA approvals?"

The most important question is:

"Can we define an outcome-complete historical decision frame that does
not select observations merely because they were approved?"

This distinction is critical.

A database of approved drugs may be useful for many purposes while
still being scientifically unsuitable as the denominator for testing
the market effect of approval.

Therefore this pilot has TWO sequential gates.

GATE 1:

SOURCE-FRAME / DENOMINATOR FEASIBILITY

GATE 2:

BOUNDED EVENT / IDENTITY FEASIBILITY

Do not proceed to Gate 2 unless Gate 1 passes.

======================================================================
2. READ FIRST
======================================================================

Before changing code or performing network requests:

read:

AGENTS.md

README.md

docs/acceleration/master_plan.md

docs/acceleration/phase4a_plan.md

docs/acceleration/phase4a_candidate_families.md

docs/acceleration/phase4a_feasibility_framework.md

docs/acceleration/phase4a_procurement_pilot_report.md

docs/acceleration/phase4a_procurement_pilot_manifest.json

and inspect the source/archive/request infrastructure actually used by
the procurement pilot.

Reuse the existing:

manifest freezing
request ceilings
immutable bytes
hash receipts
denominator retention
stop semantics
public checks
preservation checks

Do not create a parallel acquisition architecture.

======================================================================
3. CORE FDA SCIENTIFIC RISK
======================================================================

FDA approvals have an obvious economic mechanism:

a regulatory decision may materially alter expected commercialization,
cash flows and product value.

But the design has serious risks:

- approval-selected source frames;
- missing or non-public negative decisions;
- scheduled/anticipated PDUFA decisions;
- advisory committee information before final action;
- repeated products/indications;
- sponsor versus economic rights-holder differences;
- subsidiary/licensing relationships;
- multiple actions for one application;
- supplements versus original applications;
- applicant changes;
- clustering within issuers and therapeutic programmes.

The source pilot must test these before any strategy design.

======================================================================
4. AUTHORITATIVE SOURCE FAMILY
======================================================================

Start from official FDA sources only.

Potential official sources include, subject to actual repository/source
inspection:

- Drugs@FDA data files;
- Drugs@FDA application/action/document pages;
- openFDA Drugs@FDA interfaces;
- official FDA approval/action letters or regulatory documents;
- other official FDA datasets/documentation strictly necessary to
  understand the historical decision frame.

Do NOT use:

- commercial biotech databases;
- news aggregators as canonical evidence;
- current Wikipedia/company lists;
- scraped investor calendars;
- paid PDUFA datasets.

SEC may later be used for bounded sponsor/rights-holder identity
evidence.

OpenFIGI may later be used only for identifier corroboration.

No market-data provider is authorized.

======================================================================
5. GATE 1 — SOURCE-FRAME / DENOMINATOR AUDIT
======================================================================

Before selecting individual FDA events, freeze a small exact audit
manifest.

Suggested artifact:

docs/acceleration/phase4a_fda_frame_manifest.json

The manifest must define the questions being tested.

At minimum determine:

Q1.
What universe does each official FDA source enumerate?

Q2.
Does it enumerate only applications/products that eventually received
approval?

Q3.
Does it contain historical regulatory actions that did NOT result in
approval?

Q4.
Can an application be observed in the source BEFORE knowing its final
outcome?

Q5.
Can the source distinguish:

original application
supplement
tentative approval
final approval
withdrawal
discontinuation
other regulatory action

where applicable?

Q6.
Are action dates historical economic/regulatory dates or present-day
database/update dates?

Q7.
Are original documents preserved or overwritten?

Q8.
Can application/action revisions be reconstructed?

Q9.
Can we identify a sufficiently complete eligible application/action
frame from official evidence?

Q10.
Can a treatment and comparison frame be defined without conditioning on
future approval?

======================================================================
6. CRITICAL STOP — OUTCOME-SELECTED FRAME
======================================================================

If the available official source frame only lets us identify:

"applications/products we now know were approved"

and there is no bounded authoritative route for constructing the
corresponding eligible non-approved / unresolved decision frame:

STOP.

Use verdict:

OUTCOME_SELECTED_SOURCE_FRAME

Do NOT continue by building a sample of approvals only.

Do NOT rationalize sector peers as automatically solving the issue.

Do NOT use stock returns.

Do NOT substitute company press releases for a missing population
denominator.

That would recreate survivorship/selection bias in a different form.

This is a primary scientific stop condition.

======================================================================
7. GATE 1 REQUEST BUDGET
======================================================================

Gate 1 should be extremely cheap.

Maximum:

10 request starts including retries.

Use only official FDA documentation/data-source access needed to answer
the denominator questions.

If Gate 1 fails:

stop immediately.

Do not use the remaining pilot budget.

If Gate 1 passes:

freeze the exact Gate 2 acquisition manifest before continuing.

======================================================================
8. GATE 2 — FIXED 12-SLOT PILOT
======================================================================

Only if Gate 1 passes.

Use 12 fixed historical monthly slots:

2019:
January
March
May
July
September
November

2020:
January
March
May
July
September
November

For each month select the FIRST ELIGIBLE OFFICIAL REGULATORY
DECISION/ACTION under a mechanical rule frozen before acquisition.

The selection rule must NOT condition on:

- approval versus rejection;
- sponsor;
- public-company status;
- market capitalization;
- product importance;
- therapeutic area;
- newsworthiness;
- current survival;
- stock availability;
- price movement.

If a month contains no eligible event under the frozen definition:

retain the empty slot.

Do not substitute a different month because the result is inconvenient.

======================================================================
9. DEFINE "ELIGIBLE FDA ACTION" BEFORE ACQUISITION
======================================================================

Do not leave "FDA decision" vague.

Using Gate 1 source semantics, define exactly what enters the frame.

The definition should specify:

application type(s)

action type(s)

original versus supplemental application treatment

whether tentative approvals count

whether withdrawals count

whether non-approval decisions can be observed

whether biologics are included or excluded

whether devices are excluded

how multiple actions on the same application/date are handled

how duplicate/product-level rows collapse

The rule must be frozen before selecting the 12 events.

Do not change it after seeing the cases.

======================================================================
10. REQUEST CEILING
======================================================================

Total pilot maximum:

60 request starts INCLUDING Gate 1 and all retries.

Gate 1:

up to 10.

If Gate 1 passes, remaining requests may be allocated approximately to:

- FDA event/application/document retrieval;
- SEC sponsor/rights-holder identity;
- OpenFIGI identifier corroboration;
- official documentation clarification.

The 60 total is authoritative.

Do not exceed it.

Do not automatically spend all 60.

Stop as soon as the scientific question is answered.

======================================================================
11. IMMUTABLE SOURCE PRESERVATION
======================================================================

For every successful authoritative response preserve:

source
URL / identifier
request timestamp
retrieval timestamp
response status
content type
original bytes
SHA-256
manifest slot
selection rule
revision/version evidence
transformation lineage

Error responses should also retain receipts consistent with existing
Research OS practice.

Never overwrite an older source version.

======================================================================
12. EVENT RECORD
======================================================================

For each selected eligible event, preserve where supported:

application number

application type

product

active ingredient

sponsor/applicant

regulatory action

action date

document date

letter/document identifier

approval status/action status

indication where relevant

original versus supplemental application

tentative/final distinction

revision/update evidence

official source identifier

source hash

Unknown values remain UNKNOWN.

Do not infer them from generic knowledge.

======================================================================
13. PUBLIC-TIMING REVIEW
======================================================================

Regulatory action date is NOT automatically first-public timestamp.

For every event distinguish:

regulatory/economic action date

document/letter date

database action date

page-publication date if available

observed first-public timestamp if genuinely evidenced

retrieval timestamp

present-day reconstruction time

If only a date exists:

classify DATE_ONLY.

Do not fabricate midnight, market open or market close.

Do not reuse SEC filing policy v002/v003 automatically.

FDA timing requires a separate future policy if needed.

Potential statuses:

OBSERVED_PUBLIC_TIMESTAMP

DATE_ONLY

MODELED_BOUND_POSSIBLE

CONTRADICTORY

UNAVAILABLE

No timing policy is approved by this pilot.

======================================================================
14. APPLICANT / ECONOMIC RIGHTS HOLDER
======================================================================

A named FDA applicant is not automatically the public security that
economically owns the drug.

For at most one mechanically selected application/event per slot,
perform bounded identity probing.

Attempt to distinguish:

FDA applicant

legal sponsor

parent company

licensee

co-development partner

commercial rights holder

public issuer candidate

historical issuer at event time

security/class candidate

Ambiguity remains explicit.

Do NOT assume:

applicant = listed parent

current owner = historical owner

brand owner = application holder

licensing rights = full economics

======================================================================
15. SEC IDENTITY PROBING
======================================================================

SEC may be used after Gate 1 passes.

Use it only to test historical applicant/rights-holder/public-security
mapping feasibility.

Do not launch a large filing campaign.

Preserve evidence for relationships.

Statuses may include:

PUBLIC_ISSUER_DIRECT

PUBLIC_PARENT_EVIDENCED

LICENSE_RELATIONSHIP_PARTIAL

PRIVATE_APPLICANT

MULTIPLE_ECONOMIC_RIGHTS_HOLDERS

HISTORICAL_OWNER_UNRESOLVED

SEC_MAPPING_UNAVAILABLE

Do not drop private or unresolved cases.

======================================================================
16. OPENFIGI
======================================================================

OpenFIGI is optional corroboration.

It may help bridge issuer/security identifiers.

It is NOT evidence of:

drug ownership

historical licensing rights

FDA action timing

economic exposure

historical parent relationship

Use conservatively.

======================================================================
17. DENOMINATOR ACCOUNTING
======================================================================

The denominator is the fixed source frame and, if Gate 2 occurs, the 12
fixed monthly slots.

Do not report only successfully mapped public companies.

Retain outcomes such as:

NO_ELIGIBLE_ACTION

OFFICIAL_RECORD_FOUND

OFFICIAL_DOCUMENT_MISSING

NEGATIVE_ACTION_PRESENT

APPROVAL_ACTION_PRESENT

PRIVATE_APPLICANT

PUBLIC_PARENT_PLAUSIBLE

RIGHTS_HOLDER_AMBIGUOUS

HISTORICAL_SECURITY_PARTIAL

TIMING_DATE_ONLY

TIMING_UNAVAILABLE

The status taxonomy must be frozen before final reporting.

======================================================================
18. REPEATED-EVENT / CLUSTER GEOMETRY
======================================================================

Do not count FDA rows as independent observations.

Investigate clustering by:

application

product

active ingredient

indication

sponsor

parent issuer

therapeutic programme

calendar date

advisory committee

annual regulatory cycle

Determine whether 100 apparent actions could collapse into far fewer
economic clusters.

Report source-only geometry.

No market outcomes.

======================================================================
19. ANTICIPATION
======================================================================

FDA actions are often partially anticipated.

Investigate whether the official source structure exposes or points to:

PDUFA-style decision schedules

advisory committee dates

earlier application acceptance

priority review status

prior regulatory communication

This pilot should NOT build a full anticipation dataset.

Instead determine:

Is anticipation likely to be an unavoidable part of experiment design?

What sources would be needed later?

Would exact event-time inference be misleading without those sources?

======================================================================
20. CONTROL / COUNTERFACTUAL FEASIBILITY
======================================================================

Do NOT select controls yet.

Evaluate possible comparison frames conceptually.

Potential structures might include:

other eligible applications with contemporaneous decisions

applications approaching regulatory decisions

same therapeutic area

similar sponsors/products without approval at that point

within-company decisions

other defensible designs

But nothing is automatically valid.

For each possible control structure discuss:

selection bias

future-outcome conditioning

calendar confounding

therapeutic-area confounding

issuer dependence

anticipation

repeated-product dependence

Do not label any structure causal.

======================================================================
21. CHEAP INFERENCE GEOMETRY
======================================================================

Without returns, estimate only source/design geometry:

number of raw actions

number of applications

number of products

number of sponsors

number of plausible public issuers

repeat issuers

repeat applications

same-day clusters

annual groups

potential treatment/control counts

Do not calculate power from market returns.

Do not claim independent observations.

If the source frame yields too few plausible independent event clusters,
reject cheaply.

======================================================================
22. NO PERFORMANCE
======================================================================

Absolute prohibition:

NO price history

NO returns

NO abnormal returns

NO event-study returns

NO market-adjusted returns

NO alpha

NO strategy signals

NO ranking

NO threshold optimization

NO event windows chosen from outcomes

NO holding-period selection

NO experiment registration

NO EXP006 creation

The purpose is source and experiment feasibility only.

======================================================================
23. NO PHASE 4B / 4C YET
======================================================================

Do not build the Temporal Corporate Reality Graph.

Do not build the causal lab.

However, evidence contracts should remain reusable later.

Potential future entities include:

FDA application

regulatory action

product

drug/ingredient

sponsor

rights holder

issuer

security

source document

relationship

revision

No graph database is needed for this pilot.

======================================================================
24. TEN REQUIRED PILOT QUESTIONS
======================================================================

At completion answer:

Q1.
Is there an authoritative accessible historical FDA source frame?

Q2.
Is that frame outcome-complete enough to avoid approval-selection bias?

Q3.
Can regulatory actions be reconstructed reproducibly?

Q4.
Can public timing be observed or conservatively bounded?

Q5.
Can FDA applicants be mapped to historical economic rights holders?

Q6.
Can those rights holders be mapped to historical listed securities at
useful frequency?

Q7.
How severe are repeated application/product/issuer clusters?

Q8.
Is anticipation a tractable design problem?

Q9.
Can a credible treatment/comparison population be constructed without
conditioning on future outcomes?

Q10.
Does this family justify a larger experiment-design/population phase?

======================================================================
25. FINAL VERDICT
======================================================================

Assign exactly one:

FDA_FAMILY_ADVANCE

FDA_FAMILY_REDESIGN

FDA_FAMILY_REJECT

FDA_FAMILY_ADVANCE:

The source-only evidence justifies a larger bounded experiment-design
and population-feasibility phase.

No performance authorization follows.

FDA_FAMILY_REDESIGN:

The mechanism remains interesting but the source frame/event definition
must change in one specific bounded way.

FDA_FAMILY_REJECT:

The family fails cheaply on denominator/source/timing/identity/control
feasibility.

If Gate 1 fails because the only usable frame is approval-selected,
FDA_FAMILY_REJECT is appropriate unless a clearly identified official
bounded alternative frame exists.

======================================================================
26. IMPORTANT — DO NOT KEEP FAMILY-SHOPPING FOREVER
======================================================================

Phase 4A should not become another endless planning programme.

Government procurement has now failed cheaply.

FDA is the next bounded candidate.

If FDA also fails cheaply, the remaining preselected merger-enforcement
family may receive one similarly bounded feasibility pass.

After those three predeclared candidates, STOP and reassess the
hypothesis-generation process rather than creating an endless list of
event families.

This constraint should be recorded in governing Phase 4A documentation.

======================================================================
27. NEW ARTIFACTS
======================================================================

Follow repository naming conventions.

Likely equivalents:

docs/acceleration/phase4a_fda_pilot_plan.md

docs/acceleration/phase4a_fda_frame_manifest.json

docs/acceleration/phase4a_fda_event_manifest.json

docs/acceleration/phase4a_fda_source_registry.json

docs/acceleration/phase4a_fda_frame_review.json

docs/acceleration/phase4a_fda_events.json

docs/acceleration/phase4a_fda_timing_review.json

docs/acceleration/phase4a_fda_identity_review.json

docs/acceleration/phase4a_fda_cluster_geometry.json

docs/acceleration/phase4a_fda_pilot_report.md

docs/acceleration/phase4a_fda_pilot_summary.json

docs/acceleration/phase4a_fda_validation.json

Do not create unnecessary duplicates.

======================================================================
28. TESTS
======================================================================

Add deterministic tests for:

Gate 1 before Gate 2

10-request Gate 1 ceiling

60-request total ceiling

manifest freeze

outcome-selection stop

12 fixed month slots

no approval filtering

no issuer filtering

no public-company filtering

no discretionary month substitution

original-byte hashing

unknown versus unavailable semantics

private applicant retention

rights-holder ambiguity retention

no market-price loader in FDA pilot path

no experiment registration

Run:

targeted tests

public checks

full local suite

preservation audit

report checks

presentation checks

hosted CI after push

======================================================================
29. COMMITS
======================================================================

Use small auditable commits.

Suggested structure:

1. freeze FDA denominator/source-frame audit;
2. run and preserve Gate 1 evidence;
3. only if Gate 1 passes, freeze and run bounded 12-slot event pilot;
4. report family verdict.

If Gate 1 fails, there may only need to be:

plan/manifest
evidence
closure

Do not create fake downstream work after an upstream stop.

======================================================================
30. STOP CONDITIONS
======================================================================

Stop immediately if:

official FDA source access is blocked;

source frame is irreparably approval-selected;

negative/non-approved eligible population cannot be bounded;

the selection rule requires discretionary outcome-based choices;

source requires paid access;

historical applicant/rightsholder mapping clearly requires an
unauthorized commercial database;

60 requests are reached;

accidental performance information enters the workflow;

another owner decision is required.

Do not route around these conditions.

======================================================================
31. ROADMAP / README
======================================================================

Do not perform another wholesale README rewrite.

The current README is now the governing public overview.

Only update current documentation minimally to record:

- procurement rejected under frozen source channel;
- FDA now selected for bounded feasibility;
- Phase 4A remains ACTIVE_EXPERIMENT_SELECTION;
- no next experiment is frozen;
- no performance authorization exists.

Historical procurement reports remain unchanged.

======================================================================
32. FINAL DELIVERY
======================================================================

At completion report:

exact HEAD

all commits

Gate 1 manifest hash

Gate 1 request totals

source-frame verdict

whether Gate 2 ran

if Gate 2 ran:
12-slot denominator
event/action types
applicant mapping
rights-holder/public-security mapping
timing classifications
cluster geometry

control/counterfactual feasibility

anticipation feasibility

total source requests

final FDA-family verdict

local test count

public test count

hosted CI result

preservation audit

exact next owner decision, if any

Then STOP.

Do NOT launch merger enforcement automatically.

Do NOT create an experiment.

Do NOT acquire prices.

Do NOT start Phase 4B or Phase 4C.

======================================================================
33. OWNER INTENT
======================================================================

Research OS is now supposed to reject weak experiment families early.

The procurement pilot did this correctly after two requests.

Repeat that discipline here.

The FDA family should survive only if official evidence can support a
non-outcome-selected historical frame, reproducible regulatory actions,
tractable public timing, historical economic-rights identity and enough
prospective variation for a serious experiment.

A cheap FDA rejection is a successful Phase 4A result.

Proceed from evidence, not from the desire to reach a backtest.