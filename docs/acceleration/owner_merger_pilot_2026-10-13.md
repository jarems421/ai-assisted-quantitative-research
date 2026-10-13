You are continuing Research OS Phase 4A.

Repository:

C:\Users\runni\quant\

GitHub:

jarems421/ai-assisted-quantitative-research

Branch:

main

Expected current HEAD:

f2013b50a5c555aa02d4f7df9bfe55283ac5e39f

Recent FDA commits:

f4ef17e — Freeze FDA denominator audit and enforce Gate 1 before event selection
9d3b2a9 — Preserve FDA frame responses and distinguish incomplete audit from family rejection
3151fb6 — Freeze reviewed FDA landing-route continuation without resetting request budget
f2013b5 — Close FDA pilot at uncertified denominator and preserve bounded source evidence

======================================================================
OWNER DECISION
======================================================================

The FDA source-only pilot is closed.

Canonical disposition:

FDA_FAMILY_REJECT
GATE1_FAIL_CLOSED
FRAME_UNCERTIFIED_NEGATIVE_ROUTE_UNAVAILABLE

This rejects the audited FDA frame/routes.

It does NOT establish that:

- every official FDA source is unsuitable;
- regulatory decisions have no economic effect;
- all negative FDA decisions are unavailable.

Do NOT reopen the FDA pilot.

Do NOT construct an approval-only event sample.

Do NOT search for additional FDA routes under this instruction.

Government procurement remains rejected under its frozen source-channel
pilot.

The owner now authorizes the THIRD AND FINAL PRESELECTED Phase 4A family:

PUBLIC MERGER-ENFORCEMENT DECISIONS

Status:

MERGER_ENFORCEMENT_FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY

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
1. CRITICAL PROGRAMME RULE
======================================================================

This is the LAST of the three predeclared Phase 4A candidate families.

The three are:

1. government procurement;
2. FDA regulatory decisions;
3. merger enforcement.

Government procurement failed cheaply.

FDA failed cheaply.

Merger enforcement now receives one bounded feasibility pilot.

After this pilot:

DO NOT automatically invent a fourth family.

DO NOT continue family shopping.

If merger enforcement fails, Phase 4A must stop and reassess the
hypothesis-generation / experiment-selection architecture.

This rule is mandatory.

======================================================================
2. PURPOSE
======================================================================

The question is:

Can public merger-enforcement events support a scientifically defensible,
point-in-time public-company experiment without conditioning the research
population on the fact that enforcement eventually occurred?

The obvious treatment events include things such as:

- FTC merger challenges;
- DOJ Antitrust merger challenges;
- complaints;
- injunction actions;
- consent settlements;
- abandonment announcements linked to enforcement;
- clearance / termination outcomes where independently observable.

But a list of challenged mergers is NOT an experiment denominator.

The first scientific problem is:

Can we construct a historical set of pending eligible mergers as they
existed BEFORE knowing which deals would later be challenged, cleared,
settled, abandoned or completed?

That is Gate 1.

======================================================================
3. READ FIRST
======================================================================

Before changing code or making remote requests, read:

AGENTS.md

README.md

docs/acceleration/master_plan.md

docs/acceleration/phase4a_plan.md

docs/acceleration/phase4a_candidate_families.md

docs/acceleration/phase4a_feasibility_framework.md

docs/acceleration/phase4a_procurement_pilot_report.md

docs/acceleration/phase4a_fda_pilot_report.md

and inspect the existing:

- manifest freezing;
- source collector;
- reviewed-stop hooks;
- immutable source archives;
- request ceilings;
- denominator retention;
- hash receipts;
- pilot reporting;
- public checks.

Reuse those systems.

Do not build a third parallel acquisition framework.

======================================================================
4. CENTRAL SCIENTIFIC RISK
======================================================================

Merger enforcement is especially vulnerable to selection bias.

An FTC or DOJ case directory naturally emphasizes deals where the agency
took visible action.

That does NOT define the pre-decision merger risk set.

The experiment cannot simply compare:

challenged deals

against

generic stocks

and call that enforcement alpha.

The relevant scientific question is closer to:

Among pending mergers that could plausibly have experienced regulatory
review, does a newly public enforcement action change market expectations
relative to an appropriate pre-existing comparison population?

Therefore the pilot must investigate whether a historical risk set of
pending mergers can be reconstructed WITHOUT selecting deals using
future enforcement outcome.

======================================================================
5. TWO-GATE STRUCTURE
======================================================================

Use two sequential gates.

GATE 1:

SOURCE-FRAME / PRE-DECISION RISK-SET FEASIBILITY

GATE 2:

BOUNDED EVENT / PARTY / SECURITY / LIFECYCLE FEASIBILITY

Gate 2 may run only if Gate 1 passes.

Do not prepare individual challenged cases first and rationalize a
population afterward.

======================================================================
6. GATE 1 — FREEZE EXACT FRAME MANIFEST
======================================================================

Before any acquisition, freeze a machine-readable Gate 1 manifest.

Suggested artifact:

docs/acceleration/phase4a_merger_frame_manifest.json

It must define the exact official routes/questions before requests.

At minimum investigate:

Q1.
What official FTC / DOJ sources enumerate merger-enforcement actions?

Q2.
What event/action types do they include?

Q3.
Do they expose only positive enforcement actions, or also clearance /
non-action / terminated investigation outcomes?

Q4.
Can an eligible merger population be observed BEFORE knowing enforcement
outcome?

Q5.
Can a pending-merger risk set be reconstructed from public primary
sources such as SEC merger filings / transaction announcements without
using future enforcement status?

Q6.
Is there any official HSR-derived historical public frame sufficiently
granular for individual transactions?

Q7.
Can deal announcement dates, enforcement-action dates and completion /
abandonment dates be distinguished?

Q8.
Are agency case-page update dates distinct from original first-public
action dates?

Q9.
Can the research denominator include untreated / unchallenged deals
without selecting them using later completion?

Q10.
Is there a realistic bounded source route for doing this without a paid
merger database?

======================================================================
7. GATE 1 — MAXIMUM 12 REQUEST STARTS
======================================================================

Gate 1 maximum:

12 request starts INCLUDING retries.

Use official sources only.

Potential official sources may include, subject to repository/source
review:

- FTC cases/proceedings;
- FTC competition / merger enforcement pages;
- DOJ Antitrust merger / case releases;
- SEC EDGAR documentation/search routes;
- official HSR statistics/documentation;
- other official U.S. government documentation necessary to establish
  frame semantics.

Do NOT use:

- Bloomberg;
- Refinitiv;
- Capital IQ;
- FactSet;
- Mergermarket;
- commercial M&A databases;
- news aggregators as canonical population evidence;
- Wikipedia;
- current deal lists;
- price data.

Search engines may be used only for bounded discovery of official
sources where necessary.

Search results are not canonical evidence.

======================================================================
8. PRIMARY GATE 1 STOP — TREATMENT-SELECTED FRAME
======================================================================

If the available official evidence lets us construct only:

"mergers we now know received public enforcement action"

but NOT a credible pre-decision merger risk set:

STOP.

Use an explicit status such as:

TREATMENT_SELECTED_SOURCE_FRAME

or repository-equivalent naming.

Do not proceed by using:

- S&P 500 peers;
- generic industry controls;
- completed mergers selected ex post;
- later-abandoned deals selected ex post

as automatic replacements for the missing risk set.

Those may later be analytical comparators, but they do not repair a
treatment-selected denominator.

======================================================================
9. HSR LIMIT
======================================================================

Do not assume HSR filing data solve the denominator problem.

Determine exactly what HSR information is publicly available
historically at transaction level.

Aggregate annual HSR statistics do NOT establish an individual merger
risk set.

If transaction-level HSR filings are confidential / unavailable:

record that explicitly.

Do not infer individual submissions from aggregate counts.

======================================================================
10. SEC AS POSSIBLE RISK-SET SOURCE
======================================================================

A possible alternative risk-set route may be public merger filings in
SEC EDGAR.

This is only a hypothesis.

Gate 1 should determine whether a bounded mechanical frame could be
constructed from filings such as, where applicable:

- merger agreements;
- 8-K transaction announcements;
- DEFM14A / PREM14A;
- S-4;
- SC TO;
- other transaction filings.

Do NOT acquire a full historical SEC merger population yet.

Instead establish whether a deterministic pre-outcome census rule is
plausible.

Example conceptual rule:

all eligible U.S.-listed merger agreements publicly announced in a
fixed historical interval that satisfy a source-defined transaction
contract, regardless of later enforcement/completion outcome.

Do not adopt that rule unless supported.

======================================================================
11. GATE 1 PASS CRITERIA
======================================================================

Gate 1 passes only if there is a plausible public-primary-source route
to all of the following:

1. define eligible mergers before enforcement outcome;
2. retain challenged and unchallenged deals;
3. identify announcement/economic date;
4. reconstruct agency-action chronology separately;
5. avoid selecting solely on completion or enforcement;
6. keep failed/unresolved transactions in denominator;
7. do this without an unauthorized commercial database.

If these cannot be established:

STOP CHEAPLY.

======================================================================
12. GATE 2 — ONLY IF GATE 1 PASSES
======================================================================

If Gate 1 passes:

freeze a second exact event manifest BEFORE event acquisition.

Use a fixed 12-slot pilot.

Preferred fixed periods:

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

For each slot choose the FIRST ELIGIBLE PENDING MERGER under the frozen
risk-set construction rule.

Do NOT choose:

the first enforcement action.

The slot should originate from the pre-outcome merger frame.

Then determine whether an enforcement outcome/action exists later.

This distinction is critical.

======================================================================
13. ELIGIBLE MERGER CONTRACT
======================================================================

Before selecting Gate 2 deals define an exact transaction contract.

Specify:

- acquisition/merger form;
- public target requirement or not;
- public acquirer requirement or not;
- U.S. listing requirement;
- minimum source evidence;
- announcement/economic date;
- cash/stock/mixed transactions;
- tender offers;
- mergers of equals;
- spin-mergers;
- asset acquisitions;
- bankruptcy sales;
- private-target acquisitions;
- foreign issuers;
- multiple competing bids;
- amended deals.

Do not decide these case by case after acquisition.

Simpler is preferable.

The objective is feasibility, not universal M&A coverage.

======================================================================
14. GATE 2 TOTAL REQUEST CEILING
======================================================================

Total pilot ceiling:

72 request starts INCLUDING:

Gate 1
Gate 2
all retries

Why 72 rather than 60:

merger identity/lifecycle evidence naturally requires two corporate
parties and potentially one agency chronology per case.

This remains tightly bounded.

Do not exceed 72.

Indicative allocation AFTER Gate 1:

- FTC/DOJ enforcement chronology;
- SEC transaction documents;
- bounded identity documents;
- OpenFIGI corroboration if useful;
- official documentation clarification.

No price provider is authorized.

Do not automatically consume the ceiling.

Stop early when feasibility is decided.

======================================================================
15. IMMUTABLE SOURCE PRESERVATION
======================================================================

For all successful and error responses preserve according to Research OS
source rules:

source
URL / identifier
request timestamp
retrieval timestamp
HTTP status
original bytes
SHA-256
content type
manifest question/slot
selection rule
revision relationship
transformation lineage

No overwriting.

No silent redirect substitution.

If a route changes materially:

stop/review/freeze a new route before continuation, as learned from the
FDA pilot.

======================================================================
16. ENFORCEMENT EVENT SEMANTICS
======================================================================

For each selected transaction, where supported, distinguish:

deal announcement

merger agreement

HSR filing if publicly evidenced

Second Request if publicly evidenced

FTC complaint

DOJ complaint

administrative challenge

federal-court challenge

consent agreement

settlement

remedy/divestiture

agency clearance if genuinely public

investigation closure if genuinely public

deal amendment

termination

abandonment

completion

Do not collapse these into one generic:

ENFORCEMENT_DATE.

Each event has different informational meaning.

======================================================================
17. PUBLIC TIMING
======================================================================

Agency action date is not automatically exact first-public time.

For each relevant event distinguish:

legal/economic effective date

filing date

complaint date

press-release date

observed public timestamp if actually evidenced

page update timestamp

retrieval timestamp

present-day reconstruction time

Statuses may include:

OBSERVED_PUBLIC_TIMESTAMP

DATE_ONLY

MODELED_BOUND_POSSIBLE

CONTRADICTORY

UNAVAILABLE

Do not fabricate intraday times.

Do not reuse SEC filing availability v002/v003 for FTC/DOJ press
releases.

A future merger-event timing policy would need separate review.

======================================================================
18. BOTH SIDES OF THE DEAL
======================================================================

Merger events involve at least:

target

acquirer

and sometimes competing bidders / divestiture buyers.

For every pilot deal, preserve identities separately.

Do not treat a corporate transaction as one issuer.

Attempt to map:

target legal issuer

target security/class

acquirer legal issuer

acquirer security/class

transaction consideration

cash component

stock component

exchange ratio

election mechanics where relevant

effective/termination dates

source evidence

Historical class identity must remain explicit.

======================================================================
19. LIFECYCLE BURDEN — CRITICAL
======================================================================

This family was originally ranked lower partly because the event itself
can terminate the target security.

Therefore Gate 2 must assess the true lifecycle burden.

For each pilot transaction ask:

If this were eventually used in a strategy experiment, could Research OS
value a target/acquirer position honestly through:

- completion;
- termination;
- cash acquisition;
- stock conversion;
- mixed consideration;
- fractional shares;
- election mechanics;
- CVRs;
- amended consideration;
- terminated deals?

Do not actually build full terminal certificates in this pilot unless a
small bounded case is needed to determine feasibility.

Report complexity.

If nearly every useful event requires bespoke terminal reconstruction,
that is a major negative family characteristic.

======================================================================
20. NO SURVIVORSHIP SHORTCUT
======================================================================

Do not define the historical sample by companies that still trade now.

Do not drop acquired targets.

Do not map old targets to current tickers without evidence.

Do not replace ended securities with current parents.

Ended target histories are central to this family.

======================================================================
21. TREATMENT DEFINITION
======================================================================

Do NOT yet freeze a trading treatment.

The pilot should determine which enforcement events are plausible
information shocks.

Potentially interesting events include:

public challenge

injunction filing

unexpected settlement/remedy

public investigation closure

But no event is automatically the treatment.

Ask:

Which event is economically interpretable?

Which event is first public?

Which event may be anticipated?

Which event is duplicated by earlier information?

Do not use returns to choose.

======================================================================
22. ANTICIPATION
======================================================================

Anticipation is likely severe.

Potential prior information includes:

deal announcement

regulatory risk disclosures

HSR filing

Second Request

public political opposition

agency statements

litigation rumors

extended closing dates

deal amendments

Do not collect a huge anticipation dataset.

Determine whether enough of the regulatory process is observable to
prevent labeling a highly anticipated challenge as a clean surprise.

This is a feasibility question.

======================================================================
23. CONTROL / COUNTERFACTUAL FEASIBILITY
======================================================================

Do NOT select actual controls yet.

Evaluate structures such as:

other pending mergers in the same pre-decision risk set

contemporaneous deals not challenged at that time

matched merger-arbitrage peers

within-deal acquirer/target contrast

later-challenged deals before their challenge

other defensible risk-set comparisons

For each discuss:

future-outcome conditioning

industry confounding

deal-size confounding

cash/stock structure

regulatory exposure

time-varying merger-spread conditions

shared agency/policy regimes

repeat acquirers

event-time clustering

Do not call anything causal yet.

======================================================================
24. SAMPLE / CLUSTER GEOMETRY
======================================================================

No returns.

Report source-only geometry such as:

risk-set deals

selected pilot deals

FTC/DOJ intervention events

agency counts

unique targets

unique acquirers

repeat acquirers

cash deals

stock deals

mixed deals

same-day regulatory events

industry clusters

annual clusters

completed deals

abandoned deals

ended target securities

Do not call raw deal count independent N.

Assess whether a larger census might plausibly create useful independent
variation.

======================================================================
25. NO PERFORMANCE
======================================================================

Absolute prohibition:

NO Tiingo

NO FMP

NO price history

NO merger spreads

NO event returns

NO abnormal returns

NO alpha

NO deal-arbitrage return

NO target premium analysis

NO acquirer return analysis

NO portfolio

NO holding period

NO optimization

NO signal

NO experiment registration

NO EXP006

The family must first survive source/design feasibility.

======================================================================
26. GATE 1 FINAL STATUSES
======================================================================

Use precise classifications such as:

PRE_DECISION_RISK_SET_PLAUSIBLE

TREATMENT_SELECTED_SOURCE_FRAME

RISK_SET_REQUIRES_COMMERCIAL_DATA

HSR_TRANSACTION_FRAME_UNAVAILABLE

SEC_RISK_SET_ROUTE_PLAUSIBLE

SOURCE_ACCESS_BLOCKED

DENOMINATOR_UNCERTIFIED

Do not claim more than evidence supports.

======================================================================
27. FINAL FAMILY VERDICT
======================================================================

Assign exactly one:

MERGER_FAMILY_ADVANCE

MERGER_FAMILY_REDESIGN

MERGER_FAMILY_REJECT

MERGER_FAMILY_ADVANCE:

Evidence justifies a larger bounded experiment/population-contract phase.

No performance authorization follows.

MERGER_FAMILY_REDESIGN:

A specific, narrow alternate source/frame appears viable and should be
reviewed before expansion.

MERGER_FAMILY_REJECT:

The family fails on accessible denominator, timing, identity,
lifecycle, sample or control feasibility.

======================================================================
28. IMPORTANT — AFTER THIS PILOT
======================================================================

Regardless of verdict:

DO NOT automatically select another experiment family.

This was candidate 3/3.

At completion set Phase 4A family-screen state appropriately.

If MERGER_FAMILY_ADVANCE:

stop for owner approval of the larger experiment-design phase.

If MERGER_FAMILY_REDESIGN:

stop for exact bounded redesign review.

If MERGER_FAMILY_REJECT:

set something equivalent to:

PHASE4A_FAMILY_SCREEN =
THREE_PREDECLARED_FAMILIES_EXHAUSTED

and:

NEXT_EXPERIMENT =
NONE_SELECTED

Then stop for a higher-level reassessment.

Do NOT propose candidate #4 automatically.

======================================================================
29. IF ALL THREE FAMILIES FAIL
======================================================================

If procurement, FDA and merger enforcement all end rejected, create a
short Phase 4A family-screen synthesis.

Do NOT immediately solve it.

Summarize:

PROCUREMENT:
why it failed and what was never tested.

FDA:
why it failed and what was never tested.

MERGER:
why it failed and what was never tested.

Then identify patterns across failures.

Examples might include:

- inaccessible primary publication channels;
- incomplete pre-outcome denominators;
- historical identity burden;
- terminal-security complexity;
- public-timing ambiguity;
- dependence / control problems.

Separate:

SOURCE-PROBLEM

from:

HYPOTHESIS-PROBLEM

from:

SYSTEM-DESIGN-PROBLEM.

Do not conclude:

"event-driven research does not work."

Three bounded failed frames do not establish that.

======================================================================
30. PHASE 4A REASSESSMENT QUESTIONS
======================================================================

If all three fail, the synthesis should prepare the owner to answer:

1. Should Research OS improve generic population/source infrastructure
   before selecting another hypothesis?

2. Should Phase 4B Temporal Corporate Reality work move earlier because
   identity/event lineage is repeatedly blocking family selection?

3. Should the next hypothesis be selected specifically from sources with
   already-accessible outcome-complete panels?

4. Should future family triage require direct source-access proof before
   mechanism scoring?

5. Are we over-constraining experiment families by requiring an
   unnecessary form of control/causal framing?

6. Which failure modes are reusable platform requirements versus
   family-specific problems?

Do not answer these automatically unless the pilot result itself clearly
supports an engineering recommendation.

======================================================================
31. ARTIFACTS
======================================================================

Follow repository conventions.

Likely equivalents:

docs/acceleration/phase4a_merger_pilot_plan.md

docs/acceleration/phase4a_merger_frame_manifest.json

docs/acceleration/phase4a_merger_event_manifest.json

docs/acceleration/phase4a_merger_source_registry.json

docs/acceleration/phase4a_merger_frame_review.json

docs/acceleration/phase4a_merger_events.json

docs/acceleration/phase4a_merger_timing_review.json

docs/acceleration/phase4a_merger_identity_review.json

docs/acceleration/phase4a_merger_lifecycle_review.json

docs/acceleration/phase4a_merger_cluster_geometry.json

docs/acceleration/phase4a_merger_pilot_report.md

docs/acceleration/phase4a_merger_pilot_summary.json

docs/acceleration/phase4a_merger_validation.json

If all three families fail also create an equivalent of:

docs/acceleration/phase4a_family_screen_summary.md

docs/acceleration/phase4a_family_screen_summary.json

Do not create redundant artifacts.

======================================================================
32. ROADMAP / README
======================================================================

Do NOT perform another wholesale README rewrite.

Make only minimal current-status changes.

Record:

- procurement rejected under frozen source route;
- FDA rejected under audited outcome-frame routes;
- merger enforcement is now candidate 3/3;
- no experiment is frozen;
- no performance is authorized.

If merger also fails, clearly record:

THREE PREDECLARED FAMILY PILOTS COMPLETE

and stop.

Preserve all historical reports unchanged.

======================================================================
33. TESTING
======================================================================

Add deterministic tests for:

Gate 1 before Gate 2

12-request Gate 1 ceiling

72-request total ceiling

manifest freeze

pre-decision risk-set requirement

treatment-selection stop

no completed-deal-only filtering

no challenged-deal-only filtering

12 fixed slots if Gate 2 runs

no current-survivor filtering

target/acquirer identity separation

terminal/lifecycle status retention

unknown vs unavailable semantics

no market-price loader

no experiment registration

three-family exhaustion stop

Run:

targeted tests

public checks

full local suite

preservation audit

report checks

presentation checks

hosted CI after push

======================================================================
34. COMMITS
======================================================================

Use small auditable commits.

Likely:

1. freeze merger denominator/risk-set audit;
2. acquire and preserve Gate 1 evidence;
3. if Gate 1 passes, freeze bounded event pilot;
4. run event/identity/lifecycle feasibility;
5. close merger family;
6. if all three failed, record three-family synthesis.

Do not perform downstream work after an upstream stop merely to make the
phase appear complete.

======================================================================
35. STOP CONDITIONS
======================================================================

Stop immediately if:

official source access is blocked;

only enforcement-positive cases can be enumerated;

no plausible public pre-decision merger risk set can be constructed;

risk-set construction clearly requires paid/commercial merger data;

selection requires discretionary hindsight;

transaction-level HSR evidence is unavailable and no bounded alternative
risk set is plausible;

identity/lifecycle burden clearly makes the proposed frame infeasible;

request ceiling is reached;

performance information enters the workflow;

another owner decision is required.

Do not route around a stop.

======================================================================
36. FINAL DELIVERY
======================================================================

At completion report:

exact HEAD

all commits

Gate 1 manifest hash

Gate 1 request totals

pre-decision risk-set verdict

HSR findings

SEC risk-set feasibility

whether Gate 2 ran

if Gate 2 ran:

- 12-slot denominator;
- transaction types;
- enforcement chronology;
- target/acquirer identity results;
- lifecycle burden;
- public timing classifications;
- clustering geometry;
- control feasibility;
- anticipation feasibility.

total source requests

final merger-family verdict

status of all three Phase 4A families

whether the three-family screen is exhausted

local test count

public test count

hosted CI result

preservation audit

exact next owner decision required

Then STOP.

Do NOT launch candidate #4.

Do NOT create an experiment.

Do NOT acquire prices.

Do NOT begin Phase 4B/4C automatically.

======================================================================
37. OWNER INTENT
======================================================================

Research OS should reject unsuitable research families before they become
expensive backtests.

Procurement did that after two requests.

FDA did it after five requests.

Merger enforcement now receives the same discipline.

But this is the final family in the predeclared shortlist.

If it fails, the lesson is not:

"keep brainstorming until something passes."

The lesson is:

stop and inspect why our experiment-selection pipeline has rejected all
three candidates.

The next decision would then be architectural/research-directional, not
another automatic family pilot.

Proceed from evidence.