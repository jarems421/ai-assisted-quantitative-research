You are continuing Research OS.

Repository:
C:\Users\runni\quant\

GitHub:
jarems421/ai-assisted-quantitative-research

Branch:
main

Expected starting HEAD:
3c867089fffc16710d23f322f18c330fb5da495b

======================================================================
OWNER DECISION
EXP006 ITEM 2.02 — ACCEPTANCE-AWARE AVAILABILITY REMEDY
======================================================================

The previous Item 2.02 freeze-closure pass correctly stopped at:

AVAILABILITY_BLOCKED

because SEC filing dates may be adjusted backward to an earlier attempted
transmission while acceptance time remains later.

That finding is accepted and must remain preserved.

Do NOT weaken it.
Do NOT reinterpret FILED AS OF DATE as public availability.
Do NOT delete or overwrite the failed v001 availability contract.

The owner now authorizes ONE bounded remedy for the SAME Item 2.02 candidate.

If this availability remedy passes, automatically resume the remaining
pre-performance EXP006 closure gates from the previous owner instruction.

If all remaining scientific gates then pass:

freeze EXP006
and run Development only

under the already approved design.

Do not ask for intermediate approval unless a genuine stop condition occurs.

======================================================================
1. CURRENT STATE
======================================================================

Read and preserve:

docs/acceleration/exp006_freeze_review.md
docs/acceleration/exp006_closure_receipt.json
docs/acceleration/exp006_availability_contract.json
docs/acceleration/owner_item202_closure_2026-10-13.md

docs/acceleration/next_experiment_design_candidate.json
docs/acceleration/next_experiment_design_candidate.md

docs/acceleration/availability_policy_v002_approved.json
docs/acceleration/availability_policy_v003_proposed.json
docs/acceleration/availability_policy_v003_approved.json
docs/acceleration/availability_policy_v003_review_packet.md

and relevant availability/calendar/source code and tests.

Starting state:

EXP006 = ABSENT
performance evaluations = 0
confirmation accesses = 0
availability v001 = FAILED_AND_INACTIVE

The previously approved Item 2.02 feature, dates, horizon, costs,
materiality and trial ceiling remain approved.

No return-derived design change has occurred.

======================================================================
2. SCIENTIFIC INTERPRETATION OF THE FAILED RULE
======================================================================

The previous rule:

first regular NYSE open strictly after SEC filing-date calendar date

is permanently rejected for EXP006.

Reason:

official SEC filing date may precede successful EDGAR acceptance.

Preserve this as a negative finding.

The remedy must instead anchor to:

ACCEPTANCE-DATETIME

with filing date retained as a separate chronology field.

======================================================================
3. NEW EXP006-SPECIFIC MODELED POLICY
======================================================================

Create a new availability contract.

Suggested version:

EXP006_item202_availability_v002

Do NOT activate old global v002/v003.

The new owner-approved rule is:

ELIGIBLE OPEN =
09:30 America/New_York on the SECOND regular NYSE trading session strictly
after the LATER of:

A. SEC FILED AS OF DATE civil date

and

B. every plausible civil date implied by the accession's raw
   ACCEPTANCE-DATETIME interpretation.

The chosen eligible open must be identical under all retained plausible
acceptance interpretations.

If the eligible open differs between interpretations:

UNAVAILABLE_TIMING_AMBIGUOUS

If acceptance is missing:

UNAVAILABLE_ACCEPTANCE_MISSING

If source chronology is contradictory:

UNAVAILABLE_SOURCE_CHRONOLOGY

If calendar coverage is insufficient:

UNAVAILABLE_CALENDAR

Do not impute eligibility.

======================================================================
4. ACCEPTANCE-TIME INTERPRETATION
======================================================================

Research OS previously encountered ambiguity around raw SEC 14-digit acceptance
timestamps.

For this EXP006 policy, preserve at minimum:

raw acceptance string

seasonal US Eastern-time interpretation where applicable

literal EST interpretation if still plausible under source documentation

UTC representations of each candidate interpretation

civil date under each interpretation

Do not silently choose the interpretation that creates an earlier trade.

Require timing invariance:

all retained interpretations must map to the same second-later-session open.

If they do not:

the filing is unavailable.

This intentionally follows the conservative concept previously explored in
availability v003, but this is a NEW EXP006-specific contract with its own
scope, evidence and hash.

======================================================================
5. WHY SECOND SESSION
======================================================================

The second-session buffer is explicitly adopted BEFORE performance.

It is not an estimate of exact public availability.

It exists to create a conservative modeled execution boundary after EDGAR
acceptance/dissemination.

Record authoritative SEC evidence establishing at least:

- a filing is not officially accepted until EDGAR accepts it;
- accepted public submissions are subsequently disseminated publicly;
- SEC/PDS documentation describes dissemination following acceptance;
- historical/current SEC documentation describes rapid dissemination but does
  not provide an exact first-public timestamp for sec.gov;
- exact observed public availability therefore remains UNKNOWN.

Use official SEC sources only for this chronology review.

Relevant routes already identified include:

SEC filing-status guidance
SEC EDGAR data-access / dissemination documentation
SEC Public Dissemination Service documentation/specification
SEC webmaster FAQ
historical EDGAR/PDS technical documentation where useful

Archive exact source bytes and receipts under existing rules.

Do NOT claim:

acceptance timestamp == exact public timestamp.

The policy classification must remain something like:

MODELED_ACCEPTANCE_BUFFERED_ELIGIBILITY

not:

OBSERVED_PUBLIC_AVAILABILITY.

======================================================================
6. HISTORICAL SUPPORT
======================================================================

The policy must be credible for Development:

2015-01-01 through 2020-12-31

Do not rely solely on a 2024/2026 help page.

Use historical SEC/PDS documentation where available to establish that the
acceptance -> dissemination process and relevant header semantics existed over
the Development period.

Do not require an exact historical dissemination timestamp if the modeled
policy does not claim one.

If the basic acceptance/dissemination mechanism cannot be evidenced for the
Development period:

STOP at AVAILABILITY_BLOCKED_HISTORICAL_SUPPORT.

======================================================================
7. BOUNDED REAL-FILING CHRONOLOGY AUDIT
======================================================================

Before activating the policy, test it against a deterministic neutral sample.

Maximum:

48 SEC filing records

No market prices.

Cover, where source geometry permits:

2015
2016
2017
2018
2019
2020

different quarters

pre-market acceptance

regular-session acceptance

after-market acceptance

Friday acceptance

weekend/holiday transitions

DST periods

adjusted filing-date examples if actual 8-K examples can be identified
without outcome selection

8-K/A where relevant

Selection must be based only on chronology/source properties.

Do not select based on issuer fame, returns or later survival.

For each sampled filing preserve:

CIK
accession
form
FILED AS OF DATE
raw ACCEPTANCE-DATETIME
all accepted timestamp interpretations
candidate civil dates
resulting second-later-session open
invariance status
source chronology status

======================================================================
8. POLICY PASS CRITERIA
======================================================================

Availability passes only if:

1. acceptance timestamp is source-observable for the population method;

2. the SEC historical evidence supports acceptance preceding public
   dissemination in the ordinary EDGAR process;

3. the policy never generates an open before all retained acceptance
   interpretations;

4. candidate timestamp interpretations produce one invariant eligible open
   or the filing is explicitly unavailable;

5. filing-date adjustments cannot move eligibility earlier than acceptance
   because the later-of rule dominates them;

6. holidays/weekends/DST are handled by an explicit verified NYSE calendar;

7. exact public availability remains explicitly UNKNOWN;

8. no silently filled timing values exist.

If these conditions pass:

status =
AVAILABILITY_MODELED_POLICY_CERTIFIED_FOR_EXP006

This means:

a conservative predeclared modeled eligibility policy is approved.

It does NOT mean:

first public timestamp observed.

======================================================================
9. DO NOT OVER-TEST EXACT PUBLIC AVAILABILITY
======================================================================

Do not get trapped trying to prove an unavailable historical website timestamp.

The scientific question for this policy is not:

"What exact second did sec.gov first display this filing?"

It is:

"Is our predeclared execution point conservatively after the source process
that made the accepted public filing available, with uncertainty represented
and ambiguous cases excluded?"

If official evidence establishes that the second-session rule is a defensible
modeled bound, the absence of an exact website timestamp is not by itself a
blocker.

If evidence contradicts that conclusion:

stop.

======================================================================
10. IF AVAILABILITY PASSES — RESUME THE PREVIOUS CLOSURE
======================================================================

Do NOT stop simply to report that availability passed.

Automatically resume the existing owner instruction beginning with the next
uncompleted scientific gate.

Specifically continue:

full 2015–2020 SEC census

8-K / 8-K/A population

scalable Item 2.02 classification

PAC/version/missingness

dated issuer -> security/class identity

renames/delistings/terminal value

market-data provider certification

independent local execution

benchmark matching

inference calibration

synthetic power/effective geometry

Proof v2 pre-freeze compilation

Do not repeat completed integration work.

Do not revisit the approved feature/horizon/cost/materiality/trial choices.

======================================================================
11. MARKET PERFORMANCE REMAINS FORBIDDEN UNTIL FREEZE
======================================================================

During all remaining gate closure:

NO post-event returns

NO strategy performance

NO Development result

NO confirmation result

NO alpha estimate

NO benchmark outcome comparison

NO holding-period search

NO parameter tuning

Only source/identity/provider/execution/inference certification is allowed.

======================================================================
12. EXP006 FREEZE
======================================================================

If and only if every mandatory scientific gate closes:

create and register:

EXP006_SEC_ITEM202_PREDICTIVE

using repository conventions.

Freeze:

feature
population
availability v002
identity
benchmark matching
execution
20-session horizon
10 bps per side costs
Development 2015–2020
historical confirmation 2021–2026-09-30
inference method
materiality >=0.50pp
positive two-sided 95% lower endpoint
trial ceiling 12

Run Proof v2.

Expected pre-performance state:

SCIENTIFICALLY_READY_FOR_FREEZE

performance_executed = false
confirmation_accesses = 0

Commit and PUSH the frozen EXP006 specification before any Development
performance exists.

Do not amend/rewrite this freeze commit later.

======================================================================
13. DEVELOPMENT AUTHORIZATION AFTER FREEZE
======================================================================

Once the freeze commit exists:

Development performance IS authorized for:

2015-01-01 through 2020-12-31

under exactly the frozen contract.

Run the one frozen Development evaluation.

No tuning afterward.

No alternative horizon.

No replacement availability rule.

No alternative matching after viewing outcomes.

No alternative inference after viewing outcomes.

Historical confirmation:

2021-01-01 through 2026-09-30

must remain unopened.

confirmation_access_count must remain:

0

======================================================================
14. DEVELOPMENT VERDICT
======================================================================

Use the already approved conditions.

Possible verdicts:

DEVELOPMENT_FAIL
DEVELOPMENT_MIXED
DEVELOPMENT_PASS_FOR_CONFIRMATION_REVIEW

PASS requires BOTH:

estimated paired net 20-session mean difference >= +0.50 percentage point

AND

positive two-sided 95% lower confidence endpoint versus zero

under the frozen inference procedure.

A positive point estimate alone is not a pass.

Do not redesign the experiment in this task after a failure.

Negative evidence is a valid result.

======================================================================
15. REQUEST DISCIPLINE
======================================================================

Chronology-remedy documentation starts:

maximum 12 new SEC documentation/source starts

Real chronology sample:

prefer existing/public accession pages and archives;
maximum 48 sampled filings as above.

After availability passes, downstream acquisition follows the ceilings and
rules of the existing Item 2.02 closure instruction.

Use bulk data wherever possible.

No paid sources.
No purchase.
No Nexus remote execution.
No Aurora.
No browser-denial bypass.

======================================================================
16. REQUIRED AVAILABILITY ARTIFACTS
======================================================================

Create compact versioned artifacts, likely:

docs/acceleration/exp006_availability_contract_v002.json
docs/acceleration/exp006_availability_review_v002.md

and an exact chronology validation receipt.

Do not overwrite v001.

If the full closure continues, update the existing freeze-review state to
reference the new contract while preserving the failed v001 history.

======================================================================
17. TESTS
======================================================================

Add tests for:

filing date earlier than acceptance

filing date equal acceptance civil date

pre-market acceptance

during-market acceptance

after-market acceptance

Friday acceptance

holiday

DST

literal-EST vs seasonal-ET interpretation

invariant second-session result

non-invariant result -> unavailable

missing acceptance -> unavailable

contradictory chronology -> unavailable

policy cannot produce an open before acceptance

exact public timestamp remains null/unknown

old availability v001 remains failed

old v002/v003 remain unchanged

confirmation remains inaccessible

======================================================================
18. STOP CONDITIONS
======================================================================

Stop if:

acceptance timestamp cannot be obtained reproducibly for the relevant census;

historical SEC evidence contradicts the modeled chronology;

second-session eligibility can occur before a retained acceptance candidate;

timestamp interpretations materially prevent invariant eligibility at scale;

the exchange calendar cannot be certified;

or any later mandatory EXP006 scientific gate fails.

Do not invent a workaround.

But do NOT stop merely because exact first-public sec.gov timestamp is unknown;
that uncertainty is intentionally represented by the modeled policy.

======================================================================
19. GIT / DELIVERY
======================================================================

Use logical commits.

At minimum preserve these distinct history points if reached:

1. acceptance-aware availability remedy
2. remaining gate closure
3. EXP006 PRE-PERFORMANCE FREEZE
4. Development result

The freeze commit MUST precede any Development-result commit.

Push main and verify hosted CI.

Final report must state:

availability v002 verdict
evidence used
chronology sample size
acceptance-interpretation invariance counts
unavailable timing counts
exact public availability status

and, if continuation proceeds:

source census counts
Item 2.02 counts
identity coverage
terminal-path coverage
market-data certification
benchmark match coverage
inference calibration
power
EXP006 freeze SHA
Development result
confirmation access count

Then STOP.

======================================================================
20. OWNER INTENT
======================================================================

This is a narrow scientific repair, not another architecture phase.

The prior filing-date-only rule failed correctly.

We are not weakening the standard by pretending filing date equals
availability.

We are replacing the broken chronology anchor with a conservative,
acceptance-aware modeled execution policy.

Exact historical web-publication time may remain unknown.

What must be true is that the chosen execution boundary is defensibly after the
accepted public filing process under the declared uncertainty model.

If that passes, continue toward a real frozen experiment.

Do not create another planning loop.