You are continuing the existing Research OS project.

Repository:

C:\Users\runni\quant\

GitHub:

jarems421/ai-assisted-quantitative-research

Branch:

main

Expected current HEAD:

9031af3132d3441b0d21a080beda20017fae0946

Recent final Phase 3 commits include:

f064414 — Freeze final Phase 3 certification scope and upstream inference stop
66ed319 — Certify the fixed Student reference obstruction with public synthetic algebra
9031af3 — Close final Phase 3 at the mandatory inference stop and retain all denominators

======================================================================
FORMAL TRANSITION
PHASE 3 -> PHASE 4
======================================================================

Phase 3 is now complete.

The canonical final disposition is:

PHASE3_COMPLETION = COMPLETE_EXP005_ABANDONED

EXP005:

ABANDONED FOR THE APPROVED CONFIRMATORY DESIGN

ABSENT
UNREGISTERED
UNFROZEN
NO REAL PERFORMANCE OBSERVED

EXP004:

OPERATIONALLY_PAUSED

Do NOT reopen EXP005.

Do NOT interpret abandonment as evidence that revenue acceleration has
no alpha.

EXP005 was abandoned because its approved confirmatory statistical
design could not be scientifically defended before performance.

That is a successful Research OS outcome:

the system rejected an experiment before allowing a potentially
misleading backtest to become evidence.

This instruction formally moves the programme into:

PHASE 4

with a revised Phase 4A.

======================================================================
1. FIRST ACTION — INSPECT THE ACTUAL REPOSITORY
======================================================================

Before editing anything:

1. Read AGENTS.md.

2. Confirm:

git status
current branch
HEAD
remote state

3. Read the current:

README.md

docs/acceleration/master_plan.md

docs/research_os.md

docs/acceleration/phase3_final_report.md

docs/acceleration/phase3_final_gate_review.md

docs/acceleration/phase3_final_summary.json

docs/acceleration/phase3_final_inference_certificate.json

docs/acceleration/phase3e_redesign_report.md

docs/acceleration/availability_policy_v003_owner_decision.md

and all immediately relevant Phase 1 / 2 / 3A / 3B / 3C / 3D / 3E
summary/report artifacts necessary to reconstruct the programme
accurately.

Inspect actual implementation and tests before describing features.

Repository state is authoritative.

Do not write README claims based solely on this instruction.

======================================================================
2. MAJOR DOCUMENTATION OBJECTIVE
======================================================================

The README now needs a substantial rewrite.

The project has evolved far beyond:

"AI-assisted quantitative research with NexusTrade and backtesting."

That description is no longer sufficient.

The README should accurately communicate what has actually been built,
what has actually been tested, what has failed, and what the system is
becoming.

It should present Research OS as:

an evidence-native quantitative research system designed to determine
whether economically motivated hypotheses contain reproducible,
net-of-cost alpha while making false discoveries difficult to accept.

A concise core identity is:

    Research OS builds reproducible, point-in-time investment
    experiments from primary evidence and refuses to accept results
    that cannot carry their own provenance, timing, identity,
    execution and statistical justification.

Do not imply profitability has been established.

Do not imply a successful alpha strategy exists.

Do not hide negative experiments.

======================================================================
3. README MUST TELL THE FULL STORY
======================================================================

Rewrite README.md comprehensively.

It should be useful to:

- a quantitative researcher;
- an engineer;
- a recruiter/interviewer;
- a potential collaborator;
- the future project owner returning months later.

Avoid turning it into a giant raw changelog.

It should tell a coherent story.

A good structure may be approximately:

# Research OS

Short description / thesis

## Why this exists

## What makes Research OS different

## Architecture

## Scientific principles

## What has been built

## Research history so far

## Phase 3 outcome

## Current status

## Repository / system architecture

## Data and provenance

## Experiment compiler

## Independent execution

## Statistical validation

## Nexus role

## Current roadmap

## Testing / reproducibility

## Running the project

## Research integrity / limitations

Exact headings may differ if a better organization exists.

======================================================================
4. README — PROJECT THESIS
======================================================================

Make clear that this is NOT:

- an AI bot that generates trading strategies;
- a black-box backtester;
- an "AI hedge fund";
- a system that assumes more backtests create more edge;
- a Nexus wrapper.

The central principle is approximately:

    FIND REAL ALPHA BY MAKING FALSE ALPHA HARD TO ACCEPT.

Use more polished wording if appropriate.

The system should be explained as separating:

primary evidence

historical identity

availability / information timing

canonical observations

population construction

strategy specification

trial accounting

execution

statistical inference

stage advancement

forward observation

institutional research memory

AI assists interpretation, research planning, critique and engineering.

Deterministic code controls scientific truth.

======================================================================
5. README — ARCHITECTURE
======================================================================

Reflect the current intended architecture:

PRIMARY PUBLIC SOURCES

        ↓

TEMPORAL CORPORATE REALITY
(later Phase 4B milestone)

        ↓

HYPOTHESIS / MECHANISM LAYER
(selective AI + deterministic research)

        ↓

CAUSAL / STATISTICAL LAB

        ↓

PROOF-CARRYING RESEARCH COMPILER

        ↓

UNCERTAINTY / ABSTENTION

        ↓

PORTFOLIO / RISK

        ↓

EXECUTION ADAPTERS

        ↓

FORWARD OBSERVATION

        ↓

INSTITUTIONAL MEMORY

Research OS remains canonical.

Nexus is a downstream replaceable adapter.

Do not claim all future layers are already implemented.

Clearly distinguish:

IMPLEMENTED

PARTIAL / PROTOTYPE

PLANNED

======================================================================
6. README — WHAT IS ACTUALLY BUILT
======================================================================

Accurately summarize implemented infrastructure.

This includes, where supported by the repository:

- immutable raw-source preservation;
- SHA-256 provenance;
- multiple timing/provenance clocks;
- original SEC filing/XBRL pilot;
- offline replay;
- SQLite / Parquet / DuckDB reconciliation where applicable;
- source registries;
- point-in-time timing policy machinery;
- effective-date identity contracts;
- revenue accounting contracts;
- experiment/stage/trial controls;
- proof-carrying experiment schema;
- immutable manifest compiler;
- exact input replay;
- code/environment fingerprints;
- inference feasibility guards;
- synthetic calibration infrastructure;
- independent Decimal local execution ledger;
- dividends;
- splits;
- ticker changes;
- cash/stock lifecycle handling;
- fail-closed disappearing-security logic;
- population reconciliation;
- generic execution adapter;
- disabled Nexus adapter;
- public synthetic CI;
- preservation/audit checks.

Do NOT describe synthetic-only functionality as real-market-certified.

Use explicit labels where necessary.

======================================================================
7. README — RESEARCH HISTORY
======================================================================

Create a concise but meaningful history of the experiments/phases.

Do NOT dump every commit.

Summarize the important findings.

EXP001:

SPY trend/SMA research.

Final outcome:

no convincing out-of-sample alpha.

If the repository has more precise wording, use it.

EXP002:

institutional/insider feasibility.

Failed feasibility.

EXP003:

insider feasibility.

Failed.

EXP004:

cross-sectional momentum experiment.

Operationally paused because historical execution / security identity
behaviour through Nexus was not scientifically reliable enough.

Do not claim its strategy hypothesis failed if it was not tested fairly.

EXP005:

annual revenue-growth acceleration proposal.

NO real strategy performance was ever observed.

The experiment was ultimately abandoned before creation/freeze because
its approved confirmatory inference could not be defended under
persistent cross-year common-factor dependence.

This distinction is extremely important.

EXP005's abandonment means:

the experiment design failed scientific certification.

It does NOT mean:

revenue acceleration was shown not to work.

======================================================================
8. README — PHASE HISTORY
======================================================================

Summarize the major programme phases.

Do this compactly but comprehensively.

For example:

Phase 1
Repository / research-system audit and guardrails.

Phase 2
Immutable SEC/XBRL pilot and reproducibility foundation.

Phase 3A
SEC timing semantics, accounting semantics and historical identity
feasibility.

Phase 3B
Design of first filing-derived strategy family and pre-performance
trial architecture.

Phase 3C
Bounded free-source feasibility census.

Important findings included:

- incomplete revenue comparability;
- incomplete historical identity;
- incomplete terminal-value evidence;
- original inference calibration failure.

Phase 3D
Certification closure attempt + proof-carrying research compiler +
independent local execution spine.

Important infrastructure gains:

- manifest compiler;
- replay;
- local execution engine;
- fail-closed corporate actions;
- CI;
- inference-resolution guards.

Phase 3E
Final pre-performance EXP005 feasibility work.

Phase 3E-R
Historical-stage / availability redesign.

Final Phase 3
Fixed-design certification.

Final disposition:

COMPLETE_EXP005_ABANDONED

because inference could not be certified under unrestricted persistent
cross-year common dependence.

Preserve exact historical terminology from repository evidence where
appropriate.

======================================================================
9. README — PHASE 3 LESSONS
======================================================================

Add a section explaining what Phase 3 taught us.

Keep it concise and intellectually useful.

Examples:

1. Historical ticker data is not historical security identity.

2. Delisting is not equivalent to zero terminal value.

3. Current-company datasets can silently introduce survivorship bias.

4. A filing timestamp is not automatically exact public availability.

5. XBRL concept equality is not necessarily accounting/economic
   comparability.

6. A statistically convenient design can be mathematically incapable
   of meeting its own significance rule.

7. Passing synthetic calibration under a narrow independence model does
   not prove those assumptions apply to a real strategy.

8. More data acquisition cannot repair a fundamentally unjustified
   inferential assumption.

9. A valid research platform must be able to kill its own experiment
   before seeing performance.

This section should show why the long Phase 3 was valuable.

======================================================================
10. README — CURRENT STATUS
======================================================================

Make the current state unmistakable.

As of the final Phase 3 closure:

Phase 3:

COMPLETE

EXP005:

ABANDONED FOR APPROVED DESIGN

EXP004:

PAUSED

Real strategy performance from EXP005:

NONE

Nexus historical execution:

BLOCKED

Nexus adapter:

DEFINED / DISABLED

Paper trading:

NOT AUTHORIZED

Live trading:

NOT AUTHORIZED

Profitability:

UNESTABLISHED

Phase 4:

NOW BEGINNING

======================================================================
11. ROADMAP UPDATE
======================================================================

Update:

docs/acceleration/master_plan.md

and any other CURRENT roadmap/documentation that still describes
Phase 4A as:

"freeze EXP005 and run Development"

That is obsolete.

Do not rewrite historical artifacts that recorded the old plan at the
time.

Only update current governing documentation.

======================================================================
12. NEW PHASE 4 STRUCTURE
======================================================================

The new forward roadmap should be:

PHASE 4A
NEXT EXPERIMENT DISCOVERY, FEASIBILITY AND FREEZE

PHASE 4B
TEMPORAL CORPORATE REALITY GRAPH PILOT

PHASE 4C
FIRST CAUSAL / COUNTERFACTUAL EVENT EXPERIMENT

PHASE 5
PORTFOLIO / RISK + UNCERTAINTY / ABSTENTION +
RESEARCH VALUE-OF-INFORMATION

PHASE 6
NEXUS CERTIFICATION + FORWARD PAPER INFRASTRUCTURE

PHASE 7
FORWARD EVIDENCE + INSTITUTIONAL MEMORY +
LATER SELECTIVE AUTONOMOUS RESEARCH

Update master_plan.md to reflect this.

======================================================================
13. PHASE 4A — PURPOSE
======================================================================

Phase 4A must NOT repeat Phase 3.

Its purpose is to identify the next economically motivated hypothesis,
cheaply test whether it is experimentally viable, and freeze the first
new experiment that survives those checks.

The principle should be:

    FAIL CHEAPLY BEFORE CERTIFYING EXPENSIVELY.

Before a new candidate hypothesis receives a large source-certification
campaign, Research OS should determine:

- Is there enough independent/event variation?
- Is source timing reconstructible?
- Can security identities plausibly be resolved?
- Is there a sufficiently large historical population/event count?
- Is there a credible comparator/control?
- Can the proposed inference answer the question?
- Is the experiment likely to require impossible terminal/lifecycle
  reconstruction?
- Can the experiment be evaluated without survivorship bias?
- Does it add new mechanism knowledge rather than duplicate prior work?

No performance should be used for this initial feasibility screen.

======================================================================
14. PHASE 4A — NEW RESEARCH DIRECTION
======================================================================

The current preferred direction is EVENT-DRIVEN RESEARCH with richer
observation counts.

Do not immediately create a strategy.

The strongest first candidate family to investigate is:

LARGE GOVERNMENT CONTRACT AWARDS /
MATERIAL GOVERNMENT PROCUREMENT EVENTS

Conceptual evidence chain:

authoritative government award

        ↓

historically resolved public-company recipient

        ↓

exact public event timestamp

        ↓

security identity at event time

        ↓

treatment definition

        ↓

credible comparison cohort

        ↓

event / causal analysis

        ↓

later fundamental outcomes

        ↓

proof-carrying research receipt

This aligns naturally with later:

Temporal Corporate Reality Graph

and

Causal Market Laboratory.

======================================================================
15. WHY EVENT-DRIVEN IS PREFERRED
======================================================================

Phase 3 showed the difficulty of sparse annual filing signals.

Five effective annual groups can leave inference extremely fragile.

The next experiment family should preferably generate substantially
more independent or quasi-independent observations.

Government awards potentially offer:

- many dated events;
- authoritative public sources;
- clear event timing;
- direct real-world economic mechanism;
- reusable entity relationships;
- sector/recipient controls;
- event-level replication;
- natural integration into the future Corporate Reality Graph.

This does NOT mean such an effect is assumed profitable.

It means it may be a better research object.

======================================================================
16. PHASE 4A SHOULD BEGIN WITH HYPOTHESIS SELECTION
======================================================================

Do NOT immediately declare government awards the winner.

Start Phase 4A by constructing a small candidate-hypothesis shortlist.

Maximum approximately:

3–5 experiment families.

Candidate ideas should be:

economically motivated

sourceable from high-quality public evidence

high enough frequency for meaningful inference

point-in-time reconstructible

testable without enormous paid datasets

scientifically distinguishable from previous experiments

Examples may include:

A. large government contract awards

B. material FDA regulatory decisions

C. major public regulatory/rule events affecting identifiable firms

D. patent / approval / procurement events if historically timestamped
   and economically credible

E. another primary-source event family strongly supported by existing
   Research OS architecture

Do not create a giant strategy idea generator.

======================================================================
17. PHASE 4A FEASIBILITY SCORECARD
======================================================================

Before source-heavy work, score candidate families on:

Economic mechanism

Event frequency

Point-in-time timestamp quality

Historical security resolution difficulty

Control/counterfactual quality

Expected sample size

Dependence structure

Inference feasibility

Corporate-action burden

Survivorship risk

Data acquisition cost

Public-source availability

Potential future graph reuse

Potential causal identification

Novelty relative to existing experiments

Expected research value if hypothesis FAILS

Prefer hypotheses where both positive and negative findings would teach
Research OS something reusable.

======================================================================
18. NO PERFORMANCE IN INITIAL PHASE 4A SELECTION
======================================================================

Do NOT:

download price history for exploratory strategy returns

run event studies

calculate alpha

calculate candidate returns

optimize event thresholds

search holding periods

rank strategies based on backtest performance

during the initial candidate-selection step.

Phase 4A should first choose the experiment family using mechanism and
feasibility evidence.

Only after owner approval of the selected family should the full
experiment contract be frozen and any performance-authorized research
begin.

======================================================================
19. PHASE 4A DESIGN PRINCIPLE LEARNED FROM PHASE 3
======================================================================

Every new candidate experiment must pass a cheap pre-performance
feasibility gate BEFORE serious source acquisition.

Create a reusable framework/checklist if one does not exist.

Call it something like:

Experiment Feasibility Gate

or repository-equivalent naming.

It should answer:

SOURCE FEASIBILITY

TIMING FEASIBILITY

IDENTITY FEASIBILITY

POPULATION FEASIBILITY

EXECUTION FEASIBILITY

INFERENCE FEASIBILITY

POWER / RESOLUTION FEASIBILITY

CONTROL / COUNTERFACTUAL FEASIBILITY

TRIAL-BUDGET FEASIBILITY

If a hypothesis fails early:

reject it cheaply.

This should prevent future Phase 3-style multi-week certification work
on an experiment whose statistical design was impossible from the
start.

======================================================================
20. DO NOT DISCARD PHASE 3 INFRASTRUCTURE
======================================================================

Phase 3's infrastructure now becomes reusable platform infrastructure.

The following should survive into Phase 4:

proof compiler

source hashing

immutable snapshots

timing policies

population reconciliation

identity contracts

execution abstraction

local reference engine

trial ceilings

stage controls

synthetic inference calibration

inference-resolution guards

public CI

preservation audits

negative-result history

Do not create parallel replacements unless necessary.

======================================================================
21. TEMPORAL CORPORATE REALITY GRAPH — NEXT BUT NOT YET
======================================================================

Phase 4B remains the dedicated graph milestone.

Do not fully build it during the first Phase 4A selection step.

However, Phase 4A data contracts should anticipate future graph reuse.

For an event such as a government award, preserve concepts such as:

event_id

event_type

event_time

publicly_known_time

issuer

security

counterparty

government agency

contract identifier

award amount

effective dates

source

source_hash

entity_confidence

relationship confidence

This should make Phase 4A evidence reusable rather than disposable.

======================================================================
22. CAUSAL LAB — NEXT BUT NOT YET
======================================================================

Phase 4C will build deeper causal/counterfactual capability.

Phase 4A may evaluate whether a candidate family supports credible:

matched controls

pre-trend checks

placebos

synthetic controls

difference-in-differences

natural-experiment logic

where appropriate.

Do not mechanically label an experiment causal.

======================================================================
23. README — NEGATIVE RESULTS ARE FIRST-CLASS
======================================================================

README should explicitly state that failed experiments are retained.

Research OS has already accumulated:

negative strategy evidence

source failures

identity failures

statistical calibration failures

abandoned experimental designs

These are assets.

The system should treat them as institutional knowledge that prevents
future repeated mistakes.

This is one of the project's differentiators.

======================================================================
24. README — NEXUS
======================================================================

Explain Nexus accurately.

Nexus is NOT removed from the architecture.

Nexus is planned as a future replaceable downstream adapter for:

execution

orchestration

paper trading

possibly selected Aurora research-assistant tasks

after certification.

Research OS remains the source of truth for:

population

identity

information timing

strategy definition

trial accounting

inference

research stage

Historical Nexus execution remains blocked because previous testing
showed that historical identities/populations could be silently altered
or pruned.

Do not frame this as:

"Nexus is bad."

Frame it as:

"Not yet certified for the historical requirements of Research OS."

======================================================================
25. README — TESTING / ENGINEERING STATE
======================================================================

Use the latest verified test counts from repository artifacts.

Current final Phase 3 delivery reported:

278 local tests

52 public tests

0 skipped

hosted public CI passed

Do not hard-code these numbers if the new documentation changes cause
the suite count to change.

Run the suite and update README with the actual final counts if
including them.

Explain that public CI does not certify private source archives,
real-market execution or alpha.

======================================================================
26. README — DISCLAIMERS
======================================================================

Be explicit:

Research OS has NOT demonstrated a profitable trading strategy.

No live trading is authorized.

No paper strategy is currently validated.

Historical reconstruction remains a hard problem.

Synthetic statistical validation is not equivalent to real-world
assumption proof.

The project's purpose is to improve the probability that future
positive evidence deserves belief.

Avoid marketing language suggesting guaranteed alpha.

======================================================================
27. README — QUALITY
======================================================================

The README should feel like a serious open-source/research engineering
project.

It should be:

clear

modern

technically credible

readable

well structured

not bloated

not defensive

not AI-generated sounding

not full of giant walls of caveats before explaining the project

Lead with the exciting identity of the project.

Then explain rigor.

Use diagrams where helpful.

A Mermaid architecture diagram is appropriate.

Use concise tables where useful.

Do not reproduce every Phase report.

Link to deeper documents.

======================================================================
28. DOCUMENTATION CONSISTENCY
======================================================================

After README rewrite, audit current documentation for stale claims.

Especially search for statements saying:

EXP005 is the next experiment

Phase 4A freezes EXP005

the current roadmap waits for 2027–2032 Validation/Test

the project is primarily NexusTrade-based

the first strategy is still active

Update CURRENT / governing documentation.

Do NOT rewrite historical frozen reports merely because their old
forward plan is obsolete.

Historical reports should preserve what was believed at the time.

======================================================================
29. PHASE 4A INITIAL ARTIFACTS
======================================================================

Create a new Phase 4A planning package following repository
conventions.

Possible equivalents:

docs/acceleration/phase4a_plan.md

docs/acceleration/phase4a_candidate_families.md

docs/acceleration/phase4a_feasibility_framework.md

docs/acceleration/phase4a_candidate_scorecard.json

docs/acceleration/phase4a_status.json

Do not over-create files.

The key output is a strong experiment-selection process.

======================================================================
30. PHASE 4A STATUS AT END OF THIS INSTRUCTION
======================================================================

This instruction should begin Phase 4A but should NOT yet run the next
strategy.

Desired final state:

PHASE3_COMPLETION =
COMPLETE_EXP005_ABANDONED

PHASE4A =
ACTIVE_EXPERIMENT_SELECTION

NEXT_EXPERIMENT =
NOT_YET_FROZEN

PERFORMANCE_AUTHORIZED =
FALSE

NEXUS_EXECUTION =
BLOCKED

PAPER_TRADING =
NOT_AUTHORIZED

LIVE_TRADING =
NOT_AUTHORIZED

======================================================================
31. OPTIONAL FIRST CANDIDATE RESEARCH
======================================================================

After the documentation/roadmap transition is complete, perform a
bounded non-performance feasibility investigation of the candidate
event families.

Do not perform a strategy backtest.

For each candidate determine approximately:

available authoritative source

event count potential

timestamp quality

entity/security mapping difficulty

historical depth

control-group plausibility

likely dependence problems

inference sample geometry

cost

expected reuse value

Use existing primary/public documentation where possible.

The goal is to recommend which ONE family deserves the next full
experiment-design pass.

Government contract awards are the current leading hypothesis, but do
not force them to win.

======================================================================
32. OWNER REVIEW
======================================================================

At the end of this instruction, present:

1. updated project identity;
2. README changes;
3. roadmap changes;
4. Phase 4A candidate families;
5. feasibility scorecard;
6. recommended next experiment family;
7. why it beats the alternatives;
8. what evidence would be required next;
9. exact authorization required from the owner.

Then STOP.

Do NOT automatically launch source-heavy research or performance.

======================================================================
33. TESTING
======================================================================

Run:

documentation consistency checks

presentation checks

public synthetic tests

full local test suite

preservation audit

relevant report checks

hosted CI after push

Do not weaken tests to accommodate documentation changes.

======================================================================
34. COMMITS
======================================================================

Use small auditable commits.

A sensible structure might be:

1. close Phase 3 and refresh project identity/documentation;
2. update governing roadmap for Phase 4;
3. add Phase 4A experiment-selection framework;
4. report Phase 4A candidate recommendation.

Exact commit structure may differ if repository conventions suggest a
better split.

Push verified work to main if AGENTS.md permits.

======================================================================
35. FINAL DELIVERY
======================================================================

At completion report:

exact HEAD

all commits

README rewrite summary

roadmap changes

Phase 3 final state

Phase 4A current state

candidate experiment families considered

feasibility scores

recommended next family

whether government awards remain the preferred direction

new source requests, if any

local test count

public test count

CI result

preservation result

exact owner decision required next

Then STOP.

======================================================================
36. MOST IMPORTANT PRINCIPLE
======================================================================

Phase 3 should now become institutional memory, not unfinished work.

Do not reopen EXP005.

Do not keep repairing the abandoned experiment.

Take the infrastructure and lessons from Phase 3 and use them to make
future experiments cheaper to reject, easier to reproduce and harder
to fool ourselves with.

Phase 4 begins now.