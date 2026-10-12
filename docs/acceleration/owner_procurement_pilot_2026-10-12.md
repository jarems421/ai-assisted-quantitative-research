You are continuing Research OS Phase 4A.

Repository:

C:\Users\runni\quant\

GitHub:

jarems421/ai-assisted-quantitative-research

Branch:

main

Expected current HEAD:

91c2c2d4d5d7ee27648257bc87342ab0490b7c36

======================================================================
OWNER DECISION
======================================================================

The owner APPROVES:

1. government procurement / government contract award announcements as
   the next Research OS experiment family for bounded feasibility work;

and

2. the proposed 12-announcement SOURCE-ONLY feasibility pilot, subject
   to the acquisition-manifest controls below.

This is:

FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY

It is NOT:

EXPERIMENT_APPROVED
EXPERIMENT_FROZEN
PERFORMANCE_AUTHORIZED
GRAPH_AUTHORIZED
CAUSAL_CLAIM_AUTHORIZED
PAPER_AUTHORIZED
LIVE_AUTHORIZED

EXP004 remains paused.

EXP005 remains abandoned and absent.

No Phase 3 work is reopened.

======================================================================
1. PURPOSE OF THIS PILOT
======================================================================

The purpose is to answer cheaply:

Can government procurement announcements support a scientifically
usable, point-in-time, public-company event experiment?

The pilot must investigate:

- authoritative source accessibility;
- event lineage;
- award/action semantics;
- first-public timing evidence;
- recipient identity;
- recipient-parent relationships;
- historical security mapping plausibility;
- revisions/modifications;
- duplicate/event clustering;
- missingness;
- denominator construction;
- rough effective event/sample geometry.

The pilot does NOT investigate returns.

The pilot does NOT test alpha.

The pilot does NOT construct a strategy.

======================================================================
2. APPROVED PILOT FRAME
======================================================================

Use exactly 12 historical announcement slots:

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

For each month:

select the FIRST AVAILABLE DATED OFFICIAL ANNOUNCEMENT under a
mechanical rule frozen before acquisition.

Do NOT select based on:

award amount
recipient
public/private status
industry
security availability
interestingness
future knowledge
current-company status

Failed or unavailable months remain in the denominator.

Do not substitute easier months after observing failures unless the
manifest explicitly contains a deterministic fallback rule approved
before acquisition.

======================================================================
3. EXACT ACQUISITION MANIFEST — FREEZE BEFORE REQUESTS
======================================================================

Before any pilot source request:

create and freeze an exact machine-readable acquisition manifest.

Use repository conventions.

Suggested artifact:

docs/acceleration/phase4a_procurement_pilot_manifest.json

and a short human-readable companion if useful.

The manifest must specify:

- pilot version;
- research cutoff;
- 12 fixed month slots;
- announcement-source family;
- deterministic first-available selection rule;
- deterministic fallback rule, if any;
- exact discovery route allowed;
- USAspending corroboration route;
- SEC identity route;
- OpenFIGI corroboration route;
- request ceiling;
- retry policy;
- pacing;
- archive/storage contract;
- hash policy;
- stop conditions;
- forbidden sources/actions;
- output questions.

Before dispatch, run a manifest self-check proving it contains no:

- issuer filter;
- current-public-company filter;
- award-size filter;
- industry filter;
- event-effect filter;
- price filter;
- performance information;
- discretionary month replacement.

Commit/freeze this manifest BEFORE source acquisition.

If the exact manifest materially deviates from the owner-approved scope,
STOP for owner review.

If it implements the approved scope exactly, no additional owner
decision is required before dispatch.

======================================================================
4. REQUEST CEILING
======================================================================

Maximum:

60 request starts TOTAL, including retries.

Indicative allocation:

up to 12 official announcement/documentation retrievals

up to 12 USAspending award/transaction corroborations

up to 24 SEC identity/evidence documents

up to 12 OpenFIGI corroborations

The total ceiling is authoritative.

Unused allocation from one category does NOT automatically permit
expansion into unrelated sources.

Do not exceed 60.

If the scientific question can be answered with fewer requests, stop
early.

======================================================================
5. ALLOWED SOURCES
======================================================================

Allowed:

official government procurement announcement source(s)

USAspending official API/documentation

SEC EDGAR

OpenFIGI

official documentation necessary to interpret these sources

Do NOT use:

Tiingo
FMP
Orbis
Nexus
Aurora
price vendors
market-return APIs
news aggregators as canonical evidence
paid data

Search engines may be used only for bounded discovery of official
sources when direct official routes fail.

Search snippets are not canonical source evidence.

======================================================================
6. SOURCE ACCESS STOP
======================================================================

The prior documentation pass found that some defense announcement pages
were inaccessible.

Therefore source access itself is an early gate.

Test the official publication channel within the earliest authorized
requests.

If the official route is persistently inaccessible through ordinary
permitted access:

DO NOT evade it.

Do not rotate hosts, proxies, unofficial mirrors or scraping tricks.

Record:

SOURCE_CHANNEL_BLOCKED

and determine whether another genuinely official accessible channel
exists.

If no adequate official historical channel exists:

stop the pilot cheaply.

That is a valid negative result.

======================================================================
7. REQUEST PACING
======================================================================

Use one worker.

Maximum request-start rate:

2 starts / second

Prefer materially slower pacing where source guidance suggests it.

Retries count against the 60-request ceiling.

Use bounded retries.

Persistent:

403
429
access denial
source contradiction

must fail closed.

Do not repeatedly hammer a source.

======================================================================
8. IMMUTABLE SOURCE PRESERVATION
======================================================================

For every successful source response:

preserve original bytes immediately.

Record:

source
URL / source identifier
request timestamp
response status
retrieval timestamp
SHA-256
content type
storage path / receipt ID
selection slot
selection rule
transformation lineage

Never overwrite an earlier response with a newer version.

Revisions become separate evidence.

Reuse existing Research OS source/archive machinery where possible.

Do not create a parallel storage system.

======================================================================
9. ANNOUNCEMENT SEMANTICS
======================================================================

For each selected announcement determine:

announcement identifier if available

official page date

page/release timestamp if actually available

agency

award / contract identifier

recipient as printed

award/action amount

contract ceiling if present

obligation if present

transaction/action type

new award vs modification

option/exercise status

period of performance if present

description

revision/update evidence

source hash

Do not force fields where the source does not contain them.

Keep:

UNKNOWN

distinct from:

NOT_APPLICABLE

and:

UNAVAILABLE.

======================================================================
10. PUBLIC TIMING
======================================================================

This is a critical gate.

Do NOT reuse filing-policy v002/v003 automatically.

Government procurement events require their own timing semantics.

For each event distinguish:

economic event date

signature/action date

USAspending transaction/action date

announcement-page date

observed publication timestamp, if actually evidenced

retrieval timestamp

present-day reconstruction time

Do not claim first-public time from a date-only page.

If exact first-public timestamp is unavailable, investigate whether a
conservative modeled eligibility policy could later be constructed.

Do NOT approve such a policy in this pilot.

Output should classify timing as something like:

OBSERVED_TIMESTAMP_SUPPORTED

DATE_ONLY

MODELED_BOUND_POSSIBLE

CONTRADICTORY

UNAVAILABLE

Do not convert a date into a fake timestamp.

======================================================================
11. USASPENDING LINEAGE
======================================================================

For the mechanically selected event, attempt bounded corroboration in
USAspending.

Preserve:

award ID

transaction/action ID

parent award relationships

modification number

action date

award amount semantics

obligation/outlay/ceiling distinctions where exposed

recipient identifiers

agency identifiers

update/revision fields

source hashes

The goal is to determine whether USAspending provides a stable lineage
for reconstructing the event.

Do not assume:

announcement amount = transaction obligation

or:

base award = modification

or:

contract ceiling = economically new information.

Explicitly test these distinctions.

======================================================================
12. RECIPIENT / COMPANY IDENTITY
======================================================================

At most ONE mechanically selected first-listed award per announcement
page may receive detailed identity probing.

Do not choose the easiest public recipient.

For that recipient attempt to determine:

printed recipient

legal entity name

recipient identifier(s)

parent entity if applicable

public/private/unknown status at event time

issuer candidate if applicable

SEC CIK if applicable

security/class candidate if applicable

ticker/exchange evidence if available

mapping ambiguity

source provenance

A private recipient is a valid pilot result.

An unresolved recipient is a valid pilot result.

Do not drop these from the denominator.

======================================================================
13. SEC IDENTITY PROBING
======================================================================

SEC acquisition is for identity feasibility only.

Do not conduct a huge filing campaign.

Use up to the approved request allowance.

Determine whether recipient -> issuer -> security can plausibly be
resolved historically.

Do not infer:

subsidiary recipient = listed parent

without dated evidence.

Do not infer:

current parent = historical parent.

Do not infer:

CIK = security.

Record relationship confidence and unresolved links.

======================================================================
14. OPENFIGI
======================================================================

OpenFIGI may corroborate identifiers.

It is not authoritative evidence of:

historical ownership

historical listing interval

announcement timing

recipient-parent relationship

Use it only within the existing Research OS identity philosophy.

======================================================================
15. DENOMINATOR ACCOUNTING
======================================================================

The denominator is the 12 fixed announcement slots.

Never report success rates only among accessible/public-company cases.

For each slot retain explicit status.

Examples:

OFFICIAL_EVENT_FOUND

OFFICIAL_PAGE_UNAVAILABLE

NO_ANNOUNCEMENT_FOUND_UNDER_RULE

AWARD_SELECTED

PRIVATE_RECIPIENT

PUBLIC_RECIPIENT_PLAUSIBLE

RECIPIENT_PARENT_AMBIGUOUS

SEC_MAPPING_PARTIAL

TIMING_DATE_ONLY

TIMING_CONTRADICTORY

USASPENDING_MATCHED

USASPENDING_AMBIGUOUS

The exact taxonomy should be frozen before derived reporting.

======================================================================
16. EVENT CLUSTERING / EFFECTIVE SAMPLE GEOMETRY
======================================================================

Do not count raw awards as independent observations.

Investigate evidence for clustering by:

recipient

parent issuer

agency

contract

award ID

modification chain

announcement page

calendar date

programme

budget cycle

Determine whether apparently many rows collapse into a much smaller
number of economically distinct events.

Produce source-only geometry such as:

raw announcement slots

announcement pages found

award lines

unique awards

unique action chains

unique recipients

unique plausible public issuers

recipient repeats

agency repeats

same-day clusters

modification clusters

This is not an effective sample-size certificate yet.

It is evidence for the next inference design.

======================================================================
17. CONTROL / COUNTERFACTUAL FEASIBILITY
======================================================================

Do NOT choose controls yet.

Do NOT use returns.

Instead evaluate what comparison frames might eventually be available.

Potential categories may include:

sector peers

procurement competitors

nonwinning bidders, only if observable

similar contractors without contemporaneous awards

within-recipient event contrasts

other justified structures

For each candidate explain:

what evidence would define it

selection risk

anticipation risk

confounding risk

dependence risk

Do not label any as causal.

======================================================================
18. ANTICIPATION / INFORMATION LEAKAGE
======================================================================

Government awards may be anticipated.

Investigate source structure for evidence such as:

solicitations

pre-award notices

expected procurement schedules

bid announcements

prior modifications

budget authorizations

Do not acquire a broad anticipation dataset in this pilot.

Simply determine whether anticipation is likely to be a major design
issue and identify what future source evidence would be required.

======================================================================
19. NO PERFORMANCE
======================================================================

Absolute prohibition:

no price data

no returns

no event-study returns

no alpha

no abnormal returns

no market-adjusted returns

no thresholds chosen from outcomes

no holding periods

no portfolio construction

no signal

no ranking

no strategy optimization

No EXP006 or other experiment should be registered yet.

======================================================================
20. NO PHASE 4B GRAPH YET
======================================================================

Do not build the Temporal Corporate Reality Graph platform.

However, structure pilot evidence so it can later be reused.

Useful conceptual entities include:

government agency

announcement

award

transaction/action

recipient

parent company

issuer

security

source document

revision

relationship

Store ordinary relational/evidence records first.

Do not introduce graph infrastructure solely for 12 pilot cases.

======================================================================
21. NO PHASE 4C CAUSAL PLATFORM
======================================================================

Do not build the causal lab.

This pilot may identify potential causal/control structures only.

No causal effect estimate is authorized.

======================================================================
22. PILOT SUCCESS QUESTIONS
======================================================================

At the end answer explicitly:

Q1.
Can authoritative historical announcements be retrieved reliably?

Q2.
Can an award/action be linked reproducibly to USAspending lineage?

Q3.
Can original award semantics distinguish new economic information from
modification/ceiling noise?

Q4.
Can first-public timing be observed or conservatively bounded?

Q5.
Can recipients be resolved historically to listed issuers/securities
often enough to justify further work?

Q6.
How much repetition/clustering exists?

Q7.
Does a credible comparison/control frame appear feasible?

Q8.
Is there enough prospective event variation to justify a larger
population census?

Q9.
What are the likely dominant dependence structures?

Q10.
Should government procurement proceed to a full experiment-design and
population-feasibility phase?

======================================================================
23. REQUIRED FINAL VERDICT
======================================================================

Assign exactly one:

PROCUREMENT_FAMILY_ADVANCE

PROCUREMENT_FAMILY_REDESIGN

PROCUREMENT_FAMILY_REJECT

Definitions:

PROCUREMENT_FAMILY_ADVANCE

The source-only pilot supports spending the next bounded effort on a
real experiment/population contract.

This does NOT authorize performance.

PROCUREMENT_FAMILY_REDESIGN

The basic family remains interesting but a specific source/timing/
identity framing must change before expansion.

PROCUREMENT_FAMILY_REJECT

The family fails cheaply on source/timing/identity/sample/control
feasibility and should not receive a larger campaign.

======================================================================
24. ARTIFACTS
======================================================================

Follow repository conventions.

Create equivalents of:

docs/acceleration/phase4a_procurement_pilot_plan.md

docs/acceleration/phase4a_procurement_pilot_manifest.json

docs/acceleration/phase4a_procurement_source_registry.json

docs/acceleration/phase4a_procurement_events.json

docs/acceleration/phase4a_procurement_timing_review.json

docs/acceleration/phase4a_procurement_identity_review.json

docs/acceleration/phase4a_procurement_cluster_geometry.json

docs/acceleration/phase4a_procurement_pilot_report.md

docs/acceleration/phase4a_procurement_pilot_summary.json

docs/acceleration/phase4a_procurement_validation.json

Do not create unnecessary files if a cleaner repository structure is
available.

======================================================================
25. PRESERVATION
======================================================================

Do not rewrite Phase 3 evidence.

Do not rewrite EXP005 history.

Do not delete FDA/merger candidate-family evidence.

Those remain institutional memory.

Government procurement is now the selected family for this bounded
pilot, not a proven winner.

======================================================================
26. TESTING
======================================================================

Add deterministic tests for:

manifest freeze

12-slot denominator

selection rule

no issuer/amount filtering

request ceiling

retry accounting

timing status semantics

source hashing

event lineage

missing/unavailable retention

private-recipient retention

identity ambiguity retention

no price/performance loader in the pilot path

Run:

targeted tests

public checks

full local suite

preservation audit

report consistency checks

presentation checks

hosted CI after push

======================================================================
27. COMMITS
======================================================================

Use small auditable commits.

A reasonable pattern:

1. freeze procurement pilot contract/manifest;
2. acquire and archive bounded source evidence;
3. build lineage/timing/identity feasibility evidence;
4. report pilot verdict and gates.

Do not mix acquisition with unrelated refactors.

Push to main if AGENTS.md permits.

======================================================================
28. STOP CONDITIONS
======================================================================

Stop early if:

official historical publication channel is unusable;

the 60-request ceiling is reached;

a source requires paid access;

a source requires evasion;

the selection rule cannot be executed without discretionary cherry-pick;

recipient mapping fundamentally requires an unauthorized dataset;

accidental performance information enters the workflow;

another owner decision becomes necessary.

Report the stop honestly.

======================================================================
29. FINAL DELIVERY
======================================================================

At completion report:

exact HEAD

all commits

frozen manifest hash

request totals by source

12-slot denominator outcome

official-page accessibility

USAspending linkage results

recipient/public-company mapping results

timing results

cluster/repetition geometry

control feasibility

anticipated dominant dependence issues

final procurement-family verdict

local test count

public test count

hosted CI

preservation audit

next exact owner decision required

Then STOP.

Do NOT create/freeze an experiment.

Do NOT acquire prices.

Do NOT start Phase 4B/4C.

======================================================================
30. OWNER INTENT
======================================================================

The purpose of Phase 4A is now to fail cheaply.

Twelve messy source cases that reveal procurement is a poor research
family are more valuable than thousands of downloaded rows followed by
another late-stage statistical failure.

Likewise, if the pilot demonstrates good source lineage, usable timing,
resolvable historical identities and sufficient prospective variation,
then the next step can justify a larger bounded experiment-design
campaign.

Proceed from evidence, not enthusiasm.