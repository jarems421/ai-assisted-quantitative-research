You are taking over an active quantitative-research engineering project called RESEARCH OS.

This is not a toy backtester and not an “AI generates trading strategies” project.

The purpose of Research OS is to build a scientifically rigorous, evidence-native quantitative research system capable of determining whether candidate trading hypotheses contain robust, reproducible, net-of-cost alpha without fooling itself through survivorship bias, look-ahead bias, bad historical identity, data leakage, researcher degrees of freedom, multiple testing, or unreliable execution infrastructure.

The long-term objective is eventually to reach forward paper trading and determine whether any discovered strategy survives real future observation.

Profitability is NOT assumed or guaranteed.

The system is designed to discover whether robust alpha exists, reject false alpha aggressively, and accumulate reusable market knowledge over time.

======================================================================
0. OWNER / PROJECT / REPOSITORY
======================================================================

Owner is a solo university student building this with AI-assisted engineering, primarily Codex.

Local repository:

C:\Users\runni\quant\

GitHub repository:

jarems421/ai-assisted-quantitative-research

Default branch:

main

The repository already contains substantial implementation, tests, governance documentation, source evidence, experiment infrastructure, and acceleration-phase artifacts.

Do not create a replacement project.

Do not redesign the repository from scratch.

Inspect the actual codebase and integrate with what exists.

AGENTS.md should be treated as repository-level operating instructions.

Existing requirements include:

- run tests before claiming completion;
- commit and push verified work;
- protect secrets;
- do not commit .env;
- do not commit private raw vendor data that is intentionally ignored;
- preserve existing experiment freezes and evidence;
- do not modify previous phase artifacts merely to make later work look cleaner;
- distinguish evidence from assumption;
- retain failures instead of silently excluding them.

Relevant environment variables may include:

EDGAR_IDENTITY
TIINGO_API_KEY
OPENFIGI_API_KEY
FMP_API_KEY

Never print or commit API tokens.

======================================================================
1. CORE SCIENTIFIC PHILOSOPHY
======================================================================

Research OS should be built around the following principle:

    FIND REAL ALPHA BY MAKING FALSE ALPHA HARD TO ACCEPT.

A high Sharpe backtest is not sufficient evidence.

Every strategy should eventually be able to answer:

1. What exact hypothesis was tested?
2. What population was eligible?
3. What information was genuinely knowable at the time?
4. What security identity existed at that time?
5. What source supplied each observation?
6. What transformations were performed?
7. Which code/environment/version produced the result?
8. Which tests had already been attempted?
9. Which inference family was predeclared?
10. Which execution assumptions were used?
11. How were delistings, corporate actions and terminal values handled?
12. Can the experiment be replayed?
13. Can an independent implementation reproduce the important events?
14. Did the result survive untouched data?
15. Did it survive real forward observation?

The platform should systematically prefer:

- point-in-time evidence;
- primary sources;
- deterministic validation;
- explicit uncertainty;
- reproducibility;
- immutable experiment definitions;
- falsification;
- conservative eligibility;
- negative findings;
- independent reconciliation.

It should avoid:

- performance-first research;
- endless parameter optimization;
- trying strategies until something looks profitable;
- hindsight-repaired universes;
- dropping inconvenient securities;
- retroactively changing definitions because results were weak;
- allowing LLM judgment into deterministic scientific gates;
- assuming current ticker/entity mappings were historically valid;
- assuming a data provider is correct merely because an HTTP request succeeds.

======================================================================
2. LONG-TERM DIFFERENTIATING ARCHITECTURE
======================================================================

Research OS is evolving toward a much more distinctive architecture than:

    LLM -> indicator -> backtest -> optimize -> trade

The new architectural identity is:

    EVIDENCE-NATIVE QUANTITATIVE INTELLIGENCE SYSTEM

The long-term system should eventually contain:

PRIMARY PUBLIC SOURCES
    |
    v
TEMPORAL CORPORATE REALITY GRAPH
    |
    +--> deterministic hypothesis machinery
    +--> selective AI research / falsification
    +--> causal / counterfactual experiments
    |
    v
PROOF-CARRYING RESEARCH COMPILER
    |
    v
UNCERTAINTY / ABSTENTION
    |
    v
PORTFOLIO / RISK
    |
    v
EXECUTION ADAPTERS
    |
    +--> local reference engine
    +--> Nexus
    +--> potential future execution engines
    |
    v
FORWARD OBSERVATION
    |
    v
INSTITUTIONAL RESEARCH MEMORY
    |
    +--> feeds future research

The defining idea is not “we use AI agents”.

Large quant firms can massively outspend this project on compute, data, personnel and agent scale.

The small-team advantage should instead be:

    specialization
    x provenance
    x coherent architecture
    x extremely cheap AI-assisted engineering
    x accumulated historical research memory

The platform should accumulate assets that become harder to reproduce over time:

- historically dated corporate relationships;
- exact evidence provenance;
- experiment manifests;
- failed hypotheses;
- successful hypotheses;
- causal/event experiments;
- uncertainty calibration;
- execution receipts;
- source-quality history;
- forward paper evidence.

AI should NOT sit in every hot path.

Preferred division:

LLM / agent:
- interpret difficult disclosures;
- propose mechanisms;
- suggest hypotheses;
- critique hypotheses;
- help write code;
- investigate anomalies.

Deterministic code:
- timestamp evidence;
- validate evidence;
- resolve identities;
- enforce source policies;
- calculate signals;
- perform statistics;
- track trials;
- enforce stage boundaries;
- execute frozen strategies;
- decide whether formal gates pass.

======================================================================
3. NEXUS: CURRENT ROLE AND FUTURE ROLE
======================================================================

NexusTrade exists and may eventually be useful.

Nexus SDK version previously used:

1.42.0

Nexus also exposes Aurora / agent features.

However, Nexus is currently NOT trusted as the historical source of truth.

A previous historical experiment exposed a serious problem:

historical ticker/security execution appeared capable of silently pruning or mishandling delisted/renamed historical securities.

That means Nexus cannot currently be trusted to define the historical population for certified research.

This does NOT mean Nexus is useless.

The intended architecture is:

    Research OS = canonical scientific brain / source of truth
    Nexus       = downstream research, orchestration or execution tool

Nexus should eventually be used for some combination of:

- secondary backtest execution;
- portfolio orchestration;
- paper trading;
- order mechanics;
- potentially eventual broker connectivity;
- selective Aurora research assistance.

Nexus must NOT be allowed to redefine:

- historical universe;
- source evidence;
- identity mappings;
- information availability;
- trial family;
- statistical significance;
- experiment stage.

The future design should use a generic execution contract:

                    FROZEN EXPERIMENT
                          |
                          v
                   EXECUTION CONTRACT
                          |
              +-----------+------------+
              |                        |
              v                        v
       LOCAL REFERENCE              NEXUS
           ENGINE                   ADAPTER

Before Nexus is trusted again for a use case, both implementations should be reconciled on:

- eligible securities;
- signal observations;
- entry dates;
- exit dates;
- prices;
- corporate actions;
- dividends;
- splits;
- fees;
- cash;
- position sizes;
- delistings;
- terminal consideration;
- resulting returns.

An unexplained discrepancy should be treated as a failed certification.

Nexus is currently BLOCKED for historical execution.

No Nexus operations should be performed in Phase 3D unless explicitly required for a local interface abstraction that performs no remote Nexus operation.

Do not send support messages, start Nexus backtests, or use Aurora remotely without owner authorization.

======================================================================
4. PRIOR EXPERIMENT HISTORY
======================================================================

Several experiments preceded the present work.

EXP001
SPY SMA-style benchmark/trend research.
No convincing out-of-sample alpha.

EXP002
Institutional / insider feasibility.
Failed source feasibility.

EXP003
Insider feasibility.
Failed.

EXP004
Cross-sectional momentum study.

Original broad design included:

- SPY buy-and-hold leg;
- SMA trend leg;
- AI strategy exploration;
- historical windows;
- transaction fees;
- lagged indicators;
- dividends;
- splits;
- common performance statistics.

Later scientific review found the historical execution/universe problem.

EXP004 is therefore:

    OPERATIONALLY PAUSED

Do not resume EXP004 unless explicitly authorized.

EXP005
The intended first filing-derived cross-sectional strategy.

EXP005 HAS NOT BEEN CREATED OR FROZEN.

There must still be:

- no EXP005 directory;
- no registered EXP005 trial;
- no EXP005 performance;
- no optimization;
- no sealed-stage access.

Current status:

    EXP005 = NOT_READY

======================================================================
5. PHASE HISTORY
======================================================================

Research OS has progressed through several acceleration phases.

----------------------------------------------------------------------
PHASE 1
----------------------------------------------------------------------

Purpose:

- audit Research OS;
- guard EXP004 pause;
- establish SEC pilot design;
- prevent unreliable Nexus history from contaminating research.

Approximately 176 tests passed.

Relevant commits included:

afed5cb
742647a

----------------------------------------------------------------------
PHASE 2
----------------------------------------------------------------------

A bounded immutable SEC pilot was implemented using three historical
pre-2021 annual filings:

Apple FY2019
CIK 0000320193
accession 0000320193-19-000119

Apple FY2020
CIK 0000320193
accession 0000320193-20-000096

Facebook FY2019
CIK 0001326801
accession 0001326801-20-000013

Exactly 15 original SEC HTTP documents were preserved.

Approximately 54 MB.

3,761 XBRL facts.

The project implemented:

- immutable source capture;
- SHA-256 evidence;
- offline replay;
- XBRL parsing;
- SQLite persistence;
- Parquet persistence;
- DuckDB independent reconciliation.

191 tests passed.

Source fidelity:

PARTIAL

Trading eligibility:

BLOCKED

Nexus historical execution:

BLOCKED

Relevant commits included:

610e5c7
e3cdc28
5c57f79
5570caa

Artifacts include:

docs/acceleration/phase2_report.md
docs/acceleration/phase2_summary.json
docs/acceleration/phase2_validation.json

----------------------------------------------------------------------
PHASE 3A
----------------------------------------------------------------------

Purpose:

- SEC timestamp semantics;
- financial semantics;
- historical identity feasibility;
- proposed information-availability policy.

Approximately 203 tests passed.

Relevant commits:

62a8abb
16756ec

Fifteen scoped financial observations were source-certified.

The exact SEC acceptance clock had a subtle issue:

winter UTC cases were straightforward, but an October seasonal case
exposed one-hour ambiguity between literal EST treatment and correct
seasonal US Eastern time.

Therefore:

SEC acceptance timestamp:
PARTIAL

Actual public availability:
UNKNOWN

A conservative policy was proposed:

- wait through one full later exchange session;
- earliest eligibility at a subsequent session open.

However:

THE POLICY WAS ONLY PROPOSED.

It was not automatically approved.

The policy must not be falsely presented as the actual public publication timestamp.

Historical class identity remained:

PARTIAL

Financial semantics for the narrow scoped facts:

CERTIFIED_FOR_SCOPED_FACTS

Relevant artifacts:

phase3a_report.md
phase3a_evidence.json
phase3a_financial_qa.md
phase3a_identity.md
availability_policy_v001.md

----------------------------------------------------------------------
PHASE 3B
----------------------------------------------------------------------

Purpose:

design exactly one potential filing-derived hypothesis before broad
source expansion.

Chosen hypothesis family:

    ANNUAL REVENUE GROWTH ACCELERATION

Definition conceptually:

revenue growth this year
minus
revenue growth previous year

Requires three comparable original annual filings.

No secondary filing signal was allowed.

Proposed portfolio/research design included:

- monthly / first-session style rebalance;
- top 20;
- 95% capital deployment;
- matched 252-to-21-session price momentum;
- equal-weight controls;
- seeded no-information controls;
- 30 bps/side transaction cost;
- 60 bps stress;
- +1 and +5 execution-session timing stress.

A fixed maximum of:

36 primary strategy-path evaluations
+
9 contribution diagnostics
=
45 performance evaluations maximum

was proposed across future stages.

Zero actual strategy-performance evaluations were run.

The inference/trial design remained PARTIAL.

A one-sided Holm-controlled four-effect family was proposed.

A 2 percentage-point net annualized paired-mean materiality floor was proposed.

Approximately 206 tests passed.

Commit:

ec0c1e9

EXP005 remained NOT_READY.

----------------------------------------------------------------------
PHASE 3C
----------------------------------------------------------------------

PHASE 3C IS NOW COMPLETE AND PUSHED.

This is the CURRENT scientifically relevant state of the project.

Purpose:

perform a bounded free-data certification pilot before authorizing
EXP005 or broad historical acquisition.

No strategy performance was allowed.

The fixed cohort was frozen before price acquisition.

Cohort:

60 unique cases

Hash:

3aaaac0cad90dc5fbbe116132a97e4a2d6789f5dabb24dca2d6e2f14a0cb1199

Composition:

- 30 issuer/revenue candidates;
- 30 lifecycle stress targets;
- overlap allowed;
- failures retained.

These cases are a deliberately selected feasibility frame.

They are NOT a representative sample of all US equities.

They must NOT be described as 30 certified complex lifecycle histories.

----------------------------------------------------------------------
PHASE 3C REVENUE RESULTS
----------------------------------------------------------------------

29 discovered candidates contain three original annual filing candidates.

The original Phase 3B signal contract required the exact XBRL concept:

RevenueFromContractWithCustomerExcludingAssessedTax

throughout the full revenue chain.

Results:

7 / 29
have the exact concept throughout.

6 / 29
pass numeric comparability.

0 / 29
have full accounting/perimeter certification.

Therefore:

fully certified revenue triples = 0

The exact-concept-only source feasibility is RED under the predeclared
80% target.

This does NOT prove:

- revenue acceleration has no alpha;
- all alternative revenue tags are economically invalid;
- financial-statement revenue cannot be normalized.

It proves the original single-element contract is too narrow / insufficiently certified for this historical population.

No real revenue acceleration series was calculated.

No momentum series was calculated.

No portfolio series was calculated.

----------------------------------------------------------------------
PHASE 3C IDENTITY / LIFECYCLE RESULTS
----------------------------------------------------------------------

50 cases produced single identifier candidates.

However:

0 have fully certified historical listing spans.

OpenFIGI is useful as a stable identifier bridge.

It is NOT sufficient evidence by itself for:

- effective historical listing periods;
- ticker validity on arbitrary past dates;
- listing start/end;
- delisting reason;
- terminal consideration.

Historical identity remains:

PARTIAL

Corporate-action lifecycle remains:

PARTIAL

Terminal-value evidence remains:

BLOCKED

----------------------------------------------------------------------
PHASE 3C MARKET DATA RESULTS
----------------------------------------------------------------------

Tiingo EOD was used for bounded market data testing.

114 Tiingo requests were made.

54 responses returned HTTP 200.

45 were non-empty.

However:

0 complete historical NAV paths are fully certified.

Tiingo can provide:

- daily OHLCV;
- dividends;
- splits;

but the free stack has NOT yet demonstrated complete historical delisting / terminal-value reconstruction.

Market data coverage:

PARTIAL

----------------------------------------------------------------------
PHASE 3C AVAILABILITY RESULTS
----------------------------------------------------------------------

89 acquired annual filings were tested for calendar invariance.

All 89 pass the one-hour calendar-invariance probe.

However:

actual public availability remains UNKNOWN.

The conservative policy packet is now:

READY_FOR_OWNER_REVIEW

It is NOT approved automatically.

This distinction is mandatory.

A policy may define when Research OS CHOOSES to allow an observation.

That is not equivalent to proving exactly when the information became publicly disseminated.

----------------------------------------------------------------------
PHASE 3C INFERENCE RESULTS
----------------------------------------------------------------------

The predeclared synthetic calibration FAILED.

The original confirmatory inference implementation therefore cannot
be used for EXP005.

No replacement inference method was selected.

This is intentional.

The project must NOT inspect real performance and then choose whichever
inference method makes it significant.

Inference status:

BLOCKED

A replacement must be selected using synthetic/null calibration BEFORE
real EXP005 performance exists.

----------------------------------------------------------------------
PHASE 3C SOURCE REQUESTS
----------------------------------------------------------------------

Recorded source requests:

SEC:
505

OpenFIGI:
12

Tiingo:
114

FMP API:
0

Documentation requests:
9

Orbis:
0 logins / queries

Nexus:
0 calls

Free-tier pacing was checked.

One early Intel oversized full-submission request created a prefix-retention gap.

This is explicitly documented.

The collector was fixed for future oversized responses.

The failed original request is forbidden from retry merely to erase the evidence gap.

Later compact original-document acquisition does not rewrite history.

----------------------------------------------------------------------
PHASE 3C VALIDATION
----------------------------------------------------------------------

226 tests passed.

0 skipped.

Replay passed.

Audits passed.

Report consistency passed.

Presentation checks passed.

Source reconciliation passed.

All 380 preserved baseline files retain their hashes.

Relevant commits:

1fb74fc
    Add frozen free-source pilot and synthetic certification machinery

da35f25
    Report Phase 3C source limits and blocked inference calibration

Primary report:

docs/acceleration/phase3c_report.md

Supporting artifacts include:

phase3c_revenue_chain_qa.md
phase3c_identity_lifecycle.md
phase3c_market_data_qa.md
phase3c_availability_review.md
phase3c_inference_calibration.md
phase3c_execution_route.md
phase3c_scale_plan.md
phase3c_gate_review.md
phase3c_source_registry.json
phase3c_evidence.json

----------------------------------------------------------------------
PHASE 3C FINAL GATE STATE
----------------------------------------------------------------------

FREE_SOURCE_STACK
PARTIAL

REVENUE_TRIPLE_SEMANTICS
PARTIAL

SEC_SOURCE_COVERAGE
PARTIAL

HISTORICAL_SECURITY_IDENTITY
PARTIAL

MARKET_DATA_COVERAGE
PARTIAL

CORPORATE_ACTION_LIFECYCLE
PARTIAL

TERMINAL_VALUE_EVIDENCE
BLOCKED

PUBLIC_ELIGIBILITY_POLICY
READY_FOR_OWNER_REVIEW

INFERENCE_IMPLEMENTATION
BLOCKED

HISTORICAL_UNIVERSE_FEASIBILITY
BLOCKED

NEXUS_EXECUTION
BLOCKED

LOCAL_EXECUTION_ROUTE
NOT_IMPLEMENTED

EXP005_FREEZE_READINESS
NOT_READY

This state must be preserved honestly.

======================================================================
6. WHAT PHASE 3C MEANS
======================================================================

Phase 3C was successful even though many gates did not pass.

Its purpose was source certification, not alpha discovery.

It identified multiple ways an ordinary quant workflow could easily
produce misleading results:

1. inconsistent historical XBRL revenue concepts;
2. incomplete accounting/perimeter comparability;
3. weak historical security identity evidence;
4. incomplete terminal-value evidence;
5. unknown actual publication availability;
6. an inference procedure that failed a known synthetic null;
7. incomplete independent historical execution infrastructure.

Research OS correctly refused to start the strategy.

Do not weaken these standards merely because progress feels slow.

======================================================================
7. NEW ROADMAP
======================================================================

The project still uses an overall seven-stage concept, but Phase 3
has been subdivided because source and scientific blockers were real.

The revised path is:

PHASE 1
governance / audit / protect paused experiments

PHASE 2
immutable SEC source pilot

PHASE 3A
timestamp, semantics and identity feasibility

PHASE 3B
freeze candidate hypothesis design

PHASE 3C
bounded free-source certification pilot

PHASE 3D
CERTIFICATION CLOSURE
+
MINIMAL PROOF-CARRYING RESEARCH COMPILER
+
LOCAL REFERENCE EXECUTION SPINE

PHASE 4A
EXP005 freeze and first Development performance evidence

PHASE 4B
Temporal Corporate Reality Graph pilot

PHASE 4C
first causal / counterfactual event experiment

PHASE 5
portfolio/risk
+
uncertainty/abstention
+
research-value prioritization
+
strategy mechanism portfolio

PHASE 6
Nexus certification
+
forward paper-trading infrastructure

PHASE 7
actual forward observation
+
institutional research memory
+
later selective autonomous research

Do not skip directly from Phase 3C to broad Phase 4 performance.

======================================================================
8. PHASE 3D — PRIMARY OBJECTIVE
======================================================================

PHASE 3D IS THE NEXT PHASE.

Its objective is:

    CLOSE THE SCIENTIFIC BLOCKERS THAT PREVENT EXP005 FROM BEING
    FROZEN, WHILE BUILDING THE MINIMAL ARCHITECTURAL SPINE THAT MAKES
    FUTURE EXPERIMENTS PROOF-CARRYING AND EXECUTION-ENGINE-INDEPENDENT.

Phase 3D contains two coordinated workstreams.

WORKSTREAM A
Scientific certification closure.

WORKSTREAM B
Minimal Proof-Carrying Research Compiler + Local Reference Execution
contract.

Both must remain bounded.

Do NOT turn Phase 3D into the Corporate Reality Graph project.

Do NOT run strategy performance.

Do NOT create EXP005 prematurely.

======================================================================
9. PHASE 3D WORKSTREAM A — SCIENTIFIC CLOSURE
======================================================================

----------------------------------------------------------------------
A1. REVENUE SEMANTICS REVISION
----------------------------------------------------------------------

The exact single-XBRL-element approach failed source feasibility.

A replacement revenue contract may therefore be designed because:

- the failure occurred before performance;
- no EXP005 result exists;
- no optimization has occurred;
- the change is motivated by source semantics, not returns.

Create a new versioned candidate such as:

    RevenueContract_v002

Do NOT simply accept every tag containing the word “Revenue”.

The purpose is to create an accounting-defensible canonical annual
revenue observation.

The contract should preserve for every observation:

- issuer;
- accession;
- original XBRL concept;
- taxonomy;
- context;
- period start;
- period end;
- filing period;
- units;
- scale;
- reported value;
- statement location if available;
- accounting perimeter;
- consolidation context;
- canonical mapping;
- mapping rule;
- mapping confidence;
- review status;
- evidence source hash.

Candidate equivalence must be determined through documented accounting
logic.

Possible mappings may include different historical US-GAAP revenue
concepts only where they genuinely represent the same economic line.

Do not automatically move dates or periods.

Do not perform fuzzy LLM normalization in the canonical pipeline.

AI may assist the developer in understanding a filing, but final
canonical mappings must be deterministic or explicitly reviewed and
recorded.

Build QA designed to detect:

- mixed fiscal periods;
- duplicate contexts;
- instant vs duration mistakes;
- different consolidation perimeters;
- continuing vs discontinued operations problems;
- segment-only revenue mistaken for issuer revenue;
- unit/scale errors;
- amended/recast filing issues;
- taxonomy migration.

The new contract must be frozen before any real revenue-acceleration
series is computed.

Phase 3D does NOT need to prove the signal has alpha.

It needs to determine whether a defensible signal input can exist.

----------------------------------------------------------------------
A2. ACCOUNTING / PERIMETER CERTIFICATION
----------------------------------------------------------------------

Create an explicit certification process rather than leaving this as
an informal human judgment.

Use:

- automated checks where possible;
- bounded manual-review receipts where unavoidable.

Any human-reviewed exception should record:

- who/what reviewed it;
- why it was necessary;
- evidence;
- decision;
- timestamp;
- version.

Do not silently “fix” failures by deleting difficult issuers.

Retain denominator accounting.

----------------------------------------------------------------------
A3. HISTORICAL SECURITY IDENTITY
----------------------------------------------------------------------

Research OS needs effective-dated identity:

    issuer
      ->
    security/share class
      ->
    exchange
      ->
    ticker
      ->
    stable identifier
      ->
    effective historical interval

OpenFIGI alone cannot certify this.

Investigate authoritative or suitably independent evidence for:

- listing start;
- listing end;
- ticker changes;
- exchange changes;
- share-class changes;
- mergers;
- acquisitions;
- bankruptcies;
- spinoffs;
- delistings;
- security termination.

SEC source documents such as:

- 8-A;
- 25;
- 8-K;
- merger filings;
- registration statements;

may be relevant.

FMP may be used only as a bounded cross-check if appropriate.

University-accessible Orbis may be manually consulted if owner
authorization is given.

Do not automate Orbis scraping.

The end product should be an effective-dated identity model.

A current mapping is not historical evidence.

----------------------------------------------------------------------
A4. TERMINAL VALUE / LIFECYCLE
----------------------------------------------------------------------

A historical backtest must not make companies disappear.

Research OS needs an explicit terminal-event model.

Examples:

cash acquisition:
    terminal cash consideration

stock acquisition:
    conversion ratio and successor security if relevant

bankruptcy:
    actual recoverable value / terminal treatment supported by evidence

delisting:
    determine whether trading continued OTC or value became zero / other

spinoff:
    preserve distribution where appropriate

liquidation:
    preserve relevant distribution if evidenced

The objective is NOT necessarily to automate every exotic corporate
action in Phase 3D.

Instead:

- define the canonical event model;
- certify enough representative cases;
- prove no silent disappearance;
- preserve unresolved cases as unresolved.

If a security cannot be valued honestly after its terminal event,
Research OS should fail the path rather than assume zero or drop it.

----------------------------------------------------------------------
A5. AVAILABILITY POLICY OWNER REVIEW
----------------------------------------------------------------------

The Phase 3A/3C conservative policy packet is:

READY_FOR_OWNER_REVIEW

Phase 3D should prepare the decision clearly.

The owner must explicitly approve, reject or amend the policy.

Do not auto-approve it.

Maintain two separate concepts:

1. source acceptance timestamp / observed source metadata;
2. Research OS eligibility timestamp under an intentionally conservative rule.

Never claim the second proves the first.

The existing one-hour calendar invariance result across 89 filings
should remain part of the evidence packet.

If the owner approves a policy, create a versioned artifact such as:

    availability_policy_v002_approved

with explicit owner-decision evidence.

----------------------------------------------------------------------
A6. INFERENCE REVISION — PRE-PERFORMANCE ONLY
----------------------------------------------------------------------

The previous confirmatory implementation failed synthetic calibration.

This is a major scientific blocker.

Do NOT merely modify constants until it passes.

Do NOT inspect real EXP005 performance first.

Phase 3D should:

1. define a small bounded candidate inference family BEFORE evaluation;
2. freeze the candidate set;
3. generate known synthetic/null worlds;
4. test calibration;
5. evaluate type-I error behaviour, dependence sensitivity and relevant
   confidence/coverage properties;
6. select a replacement only from synthetic/null evidence;
7. document rejected methods too.

Potential candidates can include, where scientifically appropriate:

- alternative moving-block bootstrap constructions;
- stationary/bootstrap alternatives;
- different block lengths;
- studentized statistics;
- permutation/randomization procedures where assumptions permit;
- dependence-aware sign or rank procedures;
- HAC-style approaches where justified.

Do not mechanically use every method above.

Inspect the existing code and determine the minimal scientifically
appropriate candidate family.

The selected method should remain compatible with:

- paired strategy/control comparisons;
- cross-sectional dependence;
- time dependence;
- multiple comparisons;
- the existing frozen trial-budget philosophy.

Preserve the predeclared one-sided Holm family if still appropriate,
or revise it only BEFORE performance with a documented reason.

No EXP005 real returns may be used in method selection.

----------------------------------------------------------------------
A7. HISTORICAL UNIVERSE FEASIBILITY
----------------------------------------------------------------------

After improved identity and lifecycle evidence exists, determine whether
the free / permitted source stack can actually reconstruct a bounded
historical population without survivorship bias.

Do not scale to the full market prematurely.

Use a bounded certification sample.

Report denominator accounting.

Possible verdicts remain:

CERTIFIED
PARTIAL
BLOCKED

Do not force a pass.

======================================================================
10. PHASE 3D WORKSTREAM B — PROOF-CARRYING RESEARCH COMPILER
======================================================================

The Proof-Carrying Research Compiler should be intentionally minimal.

Do NOT build a giant custom language.

The goal is to turn a research experiment into a canonical,
machine-readable object whose result carries its provenance.

Conceptually:

HYPOTHESIS
POPULATION
OBSERVATIONS
SIGNAL
ELIGIBILITY
EXECUTION
COSTS
INFERENCE
TRIAL FAMILY
STAGE
DATA CONTRACTS

        |
        v

COMPILE

        |
        v

experiment manifest
source hashes
universe hash
identity-map hash
availability-policy hash
signal-spec hash
execution-spec hash
code hash
environment hash
trial-family hash
execution receipt
statistical receipt

A result should be interpretable as:

    This result is valid only under this exact source state,
    historical population, eligibility policy, code state, execution
    contract and statistical family.

This is “proof-carrying” in the provenance/reproducibility sense.

It does NOT mean mathematical proof that future alpha exists.

----------------------------------------------------------------------
B1. MINIMAL EXPERIMENT SCHEMA
----------------------------------------------------------------------

Define a versioned experiment schema that can eventually express EXP005.

Possible fields:

experiment_id
schema_version
hypothesis
population_contract
source_contracts
signal_contract
identity_contract
availability_policy
execution_contract
cost_model
inference_contract
trial_family
research_stage
sealed_stage_rules
dependencies
source_snapshot_ids
code_commit
environment_fingerprint

Keep it declarative.

Avoid strategy-specific Python hidden inside arbitrary callbacks unless
there is no reasonable alternative.

----------------------------------------------------------------------
B2. COMPILATION
----------------------------------------------------------------------

Implement a deterministic compile step.

Conceptually:

    research compile <experiment>

Compilation should:

- validate the experiment schema;
- verify referenced contracts exist;
- reject unapproved policies;
- reject missing source snapshots;
- reject unresolved mandatory gates;
- create content hashes;
- record code commit;
- record environment;
- produce immutable manifest output.

Compilation should NOT execute strategy performance in Phase 3D.

----------------------------------------------------------------------
B3. REPLAY
----------------------------------------------------------------------

Implement minimal replay semantics.

Conceptually:

    research replay <manifest>

Replay should be able to verify:

- referenced files exist;
- source hashes match;
- policy hashes match;
- code/environment compatibility where possible;
- inputs have not silently changed.

The first implementation can be modest.

Do not overpromise bit-for-bit reproducibility where libraries,
floating point or external systems make that impossible.

Clearly distinguish:

exact replay
vs
semantic reconciliation.

----------------------------------------------------------------------
B4. MUTATION / FAILURE TESTS
----------------------------------------------------------------------

Add tests proving the compiler refuses invalid research.

Examples:

- source hash changed;
- identity map changed;
- availability policy not approved;
- inference implementation uncertified;
- trial-family hash changed;
- population snapshot changed;
- stage illegally advanced;
- source contract missing;
- terminal event unresolved where mandatory.

Research OS should fail closed.

----------------------------------------------------------------------
B5. EXP005 AS FUTURE FIRST FULL COMPILED EXPERIMENT
----------------------------------------------------------------------

Do NOT create/freeze EXP005 simply because the schema exists.

However, the schema should be designed so EXP005 can become the first
full experiment compiled through it once all gates pass.

That will make EXP005 an end-to-end integration test of the new
architecture.

======================================================================
11. PHASE 3D LOCAL REFERENCE EXECUTION SPINE
======================================================================

Research OS currently has:

LOCAL_EXECUTION_ROUTE = NOT_IMPLEMENTED

Phase 3D should implement the minimal independent execution spine.

It should be deliberately boring.

No advanced optimizer.

No fancy UI.

No agent.

No portfolio AI.

The purpose is to have a transparent reference implementation against
which Nexus and future engines can later be reconciled.

It should eventually support enough primitives for EXP005:

- exchange sessions / trading calendar;
- observation timing;
- eligibility timing;
- signal ranking;
- rebalance events;
- position sizing;
- cash;
- buys;
- sells;
- transaction fees;
- dividends;
- splits;
- delisting / terminal events;
- NAV;
- execution receipts.

Phase 3D does NOT require running EXP005.

Synthetic fixtures and hand-verifiable tiny examples should be used.

Create deterministic examples including:

1. ordinary buy/hold/sell;
2. dividend;
3. split;
4. ticker change;
5. cash acquisition;
6. disappearing-security attempt;
7. unresolved terminal event.

The engine should never silently delete a security.

If the terminal state is unresolved and required for NAV:

FAIL.

This local engine becomes the scientific reference.

======================================================================
12. NEXUS ADAPTER CONTRACT IN PHASE 3D
======================================================================

Define the interface Nexus will later need to implement.

Do NOT use Nexus remotely yet.

Possible conceptual interface:

ExecutionInput
- frozen population;
- dated signal observations;
- execution sessions;
- sizing;
- costs;
- corporate-action instructions;
- starting capital.

ExecutionOutput
- orders;
- fills;
- positions;
- cash ledger;
- corporate-action ledger;
- NAV path;
- terminal events;
- warnings/errors;
- execution-engine metadata.

Later:

LocalReferenceAdapter
NexusAdapter

both implement the same semantic contract.

Phase 3D should preferably build:

- interface;
- local implementation;
- Nexus placeholder / disabled adapter.

Nexus must remain blocked until later certification.

======================================================================
13. WHAT PHASE 3D MUST NOT DO
======================================================================

Do NOT:

- run EXP005 performance;
- compute real revenue acceleration rankings;
- optimize parameters;
- open Validation;
- open Test;
- access sealed future data;
- restart EXP004;
- run Nexus remote backtests;
- perform Nexus paper trading;
- start live trading;
- build the entire Corporate Reality Graph;
- ingest ten new data ecosystems;
- build a giant AI agent swarm;
- build a generic causal inference engine;
- buy datasets;
- scrape Orbis;
- silently broaden revenue definitions;
- silently drop failed issuers;
- silently set unknown terminal values to zero;
- approve availability policy automatically;
- choose inference after seeing strategy performance;
- modify previous frozen artifacts simply to obtain green gates.

======================================================================
14. PHASE 3D REQUIRED DELIVERABLES
======================================================================

Inspect existing conventions before choosing exact filenames.

At minimum Phase 3D should produce equivalents of:

docs/acceleration/phase3d_report.md

docs/acceleration/phase3d_gate_review.md

docs/acceleration/phase3d_revenue_contract.md

a machine-readable revenue contract artifact

docs/acceleration/phase3d_identity_certification.md

docs/acceleration/phase3d_terminal_value.md

docs/acceleration/phase3d_availability_decision.md
or a packet explicitly waiting on owner decision

docs/acceleration/phase3d_inference_revision.md

machine-readable inference calibration artifacts

docs/acceleration/phase3d_execution_reference.md

machine-readable execution contract/schema

proof-carrying experiment schema

manifest compiler

manifest replay verifier

compiler mutation/failure tests

local reference execution engine

synthetic/hand-verifiable execution fixtures

generic execution adapter interface

disabled Nexus adapter placeholder

phase3d_evidence.json

phase3d_summary.json

Exact names can follow repository conventions.

Do not create redundant architecture if equivalent modules already exist.

======================================================================
15. PHASE 3D GATE MODEL
======================================================================

Use explicit gate statuses.

Potential final gates include:

REVENUE_CANONICALIZATION
ACCOUNTING_PERIMETER_CERTIFICATION
HISTORICAL_SECURITY_IDENTITY
CORPORATE_ACTION_LIFECYCLE
TERMINAL_VALUE_EVIDENCE
PUBLIC_ELIGIBILITY_POLICY
INFERENCE_IMPLEMENTATION
HISTORICAL_UNIVERSE_FEASIBILITY
PROOF_COMPILER
MANIFEST_REPLAY
LOCAL_EXECUTION_ROUTE
NEXUS_ADAPTER_INTERFACE
NEXUS_EXECUTION
EXP005_FREEZE_READINESS

NEXUS_EXECUTION should probably remain:

BLOCKED

unless owner explicitly changes scope.

EXP005_FREEZE_READINESS should become READY only if ALL mandatory
scientific prerequisites genuinely pass.

It is acceptable for Phase 3D to finish with EXP005 still NOT_READY.

Do not define success as “make every gate green”.

Define success as:

    replace uncertainty with evidence and preserve honest blockers.

======================================================================
16. OWNER DECISION POINT: AVAILABILITY
======================================================================

One current issue requires explicit owner review.

The previous proposal conservatively delayed SEC-derived information
through one complete later exchange session, with possible eligibility
at a later session open.

Before implementation treats a policy as approved:

- present the existing evidence;
- summarize alternatives;
- explain tradeoffs;
- request explicit owner authorization if not already recorded.

Do not bundle policy approval invisibly into code changes.

======================================================================
17. AFTER PHASE 3D
======================================================================

If Phase 3D genuinely reaches EXP005 freeze readiness, then separately
request authorization for Phase 4A.

Do not automatically begin it unless this new prompt explicitly grants
that permission.

PHASE 4A:

- perform authorized source acquisition;
- freeze EXP005;
- compile it through the proof-carrying system;
- compute Development only;
- reconcile local execution;
- run controls;
- perform predeclared inference;
- report result honestly.

Validation and Test remain sealed until Development gates justify
advancement.

No performance result should cause definitions to be retrospectively
changed.

======================================================================
18. PHASE 4B — TEMPORAL CORPORATE REALITY GRAPH
======================================================================

This comes AFTER the core Research OS can conduct a trustworthy
experiment.

The first graph should be deliberately narrow.

Recommended initial sources:

SEC
+
USAspending
+
historical security identity

Do NOT start with every alternative-data source.

The graph should eventually represent things such as:

Company
  -> filed -> filing
  -> won -> government award
  -> supplies -> company
  -> acquired -> company
  -> regulated by -> agency/rule
  -> changed -> ticker/exchange/security class
  -> experienced -> corporate event

Every edge should support fields like:

event_time
publicly_known_time
source
source_hash
entity_confidence
effective_from
effective_to

The key query is not:

    What relationships exist today?

It is:

    What relationships were legitimately knowable at historical time T?

The first graph can live in:

PostgreSQL
Parquet
DuckDB

Do not add Neo4j or specialized graph infrastructure unless traversal
actually becomes a bottleneck.

The graph should primarily exist to generate testable hypotheses, not
to create fancy visualizations or chatbot answers.

======================================================================
19. PHASE 4C — CAUSAL MARKET LABORATORY
======================================================================

After one event graph exists, select ONE event family.

A strong initial candidate:

    unusually large government contract awards

Potential workflow:

authoritative award
    ->
historically resolved listed recipient
    ->
exact public timestamp
    ->
treatment definition
    ->
credible control cohort
    ->
pre-treatment checks
    ->
event analysis
    ->
placebos
    ->
counterfactual / synthetic controls where justified
    ->
later fundamental consequences
    ->
proof-carrying research receipt

The causal system should ask:

- what changed?
- who was treated?
- when was it known?
- who is a credible comparison?
- were pre-event trajectories compatible?
- what other events contaminated the observation?
- does the result replicate across independent cohorts?
- does the proposed economic mechanism appear later?

Do NOT label something “causal” merely because a regression was run.

Identification assumptions must be explicit.

======================================================================
20. PHASE 5 — PORTFOLIO, UNCERTAINTY AND RESEARCH EFFICIENCY
======================================================================

If strategies survive earlier research, build:

A. portfolio construction;
B. risk controls;
C. cost/capacity modelling;
D. uncertainty-first decisions;
E. abstention;
F. research-value scheduling.

The system should be allowed to say:

    EVIDENCE INSUFFICIENT — DO NOT DEPLOY

Potential strategy state:

expected effect
uncertainty
evidence quality
regime similarity
distribution shift
cost sensitivity
liquidity/capacity
forward-calibration state

Do not force every forecast into BUY/SELL.

Also introduce a lightweight Research Value-of-Information mechanism.

Proposed research questions should be scored on:

- cost;
- novelty;
- overlap with existing experiments;
- expected statistical power;
- information gained if hypothesis succeeds;
- information gained if hypothesis fails.

The objective is:

    knowledge gained per unit of scarce research budget

not:

    maximum number of agent calls.

======================================================================
21. PHASE 6 — NEXUS CERTIFICATION AND PAPER TRADING
======================================================================

This is where Nexus should become important.

By this stage:

Research OS has already decided:

- strategy definition;
- population;
- source evidence;
- timing;
- signal;
- portfolio rules;
- risk;
- uncertainty;
- frozen order intent.

Nexus receives execution instructions.

Conceptually:

Research OS
    ->
frozen order intent
    ->
Nexus adapter
    ->
Nexus paper execution
    ->
orders/fills/positions
    ->
Research OS observation store

Critical principle:

    ORDERS TRAVEL OUT.
    EVIDENCE TRAVELS BACK.

Research OS remains canonical.

If Nexus disappears or changes behaviour, the research history remains
usable and another execution adapter can replace it.

Before forward use, perform Nexus certification against the local
reference implementation.

======================================================================
22. PHASE 7 — FORWARD EVIDENCE
======================================================================

Phase 7 cannot be accelerated merely by coding faster.

Real forward evidence requires future calendar time.

Research OS should compare:

historical expectation

versus

actual forward observation.

Store:

- fills;
- slippage;
- realized costs;
- missed trades;
- signal decay;
- regime state;
- expected return;
- realized return;
- execution failures;
- corporate-event surprises;
- model abstentions.

Forward evidence should update institutional research memory.

For slower monthly strategies, meaningful forward evidence may require
many months.

Six to twelve months can teach far more than a few weeks.

Do not confuse “paper-trading infrastructure completed” with
“paper strategy validated”.

======================================================================
23. SELECTIVE AUTONOMOUS RESEARCH — LATER, NOT CRITICAL PATH
======================================================================

The project may eventually include an autonomous or semi-autonomous
scientific researcher.

However this should NOT be the central differentiator or current
priority.

A future agent could:

- inspect the corporate graph;
- find unexplained relationships;
- propose hypotheses;
- retrieve relevant historical evidence;
- propose falsification tests;
- compare with failed research;
- recommend the highest-value next experiment.

But deterministic systems still control:

- canonical evidence;
- identities;
- timestamps;
- trial budgets;
- inference;
- stage advancement;
- execution.

The objective is not to create hundreds of agents.

The owner has a limited Codex subscription and wants low operating
cost.

Autonomy should therefore be selective and triggered when expected
research value justifies the cost.

======================================================================
24. REALISTIC TIMELINE
======================================================================

Do NOT claim this can all be finished in a weekend.

Codex can make software implementation dramatically faster.

It cannot eliminate:

- ambiguous filings;
- historical identity research;
- missing terminal-value evidence;
- bad source coverage;
- API restrictions;
- difficult accounting semantics;
- statistical methodology work;
- real future observation time.

Reasonable rough engineering estimates from the present state:

Phase 3D:
approximately 3–6 weeks

Phase 4A:
approximately 2–4 weeks after genuine 3D readiness

Phase 4B:
approximately 3–6 weeks

Phase 4C:
approximately 3–5 weeks

Phase 5:
approximately 3–5 weeks

Phase 6:
approximately 2–4 weeks

Some work can overlap.

A reasonable high-level target is approximately:

3–5 months

to reach a scientifically much stronger paper-trading-ready platform,
assuming consistent AI-assisted development and no catastrophic source
blocker.

This is NOT a deadline or guarantee.

Phase 7 forward evidence then takes actual market time.

======================================================================
25. YOUR TASK NOW
======================================================================

START PHASE 3D.

Before coding:

1. inspect AGENTS.md;
2. inspect repository structure;
3. inspect Phase 1/2/3A/3B/3C reports and machine-readable evidence;
4. inspect the existing source, experiment, inference, identity and
   execution-related code;
5. inspect current tests;
6. confirm the working tree / git state;
7. confirm the current main HEAD includes:

   1fb74fc
   da35f25

or later commits containing them.

Do not rely only on this handoff if the actual code contradicts a detail.

The repository is authoritative for implementation state.

However:

do not reinterpret explicit scientific stop conditions merely because
code makes something possible.

Then produce a concrete Phase 3D implementation plan based on the
ACTUAL codebase.

The plan should map existing modules to required changes and avoid
duplicating infrastructure.

Then implement Phase 3D incrementally.

Use small auditable commits.

Run targeted tests while developing and the full relevant suite before
completion.

Do not claim a gate passed unless evidence demonstrates it.

Do not start EXP005 performance.

Do not start Phase 4 automatically.

At the end:

- produce the Phase 3D report;
- produce all required QA/evidence artifacts;
- show exact gate verdicts;
- report unresolved blockers;
- report test counts;
- report source request counts;
- confirm previous frozen artifacts remain intact;
- commit verified work;
- push to main if AGENTS.md and repo policy permit;
- STOP.

If owner input is needed for the availability-policy approval, stop at
that decision point rather than silently deciding for them.

======================================================================
26. PHASE 3D SUCCESS CRITERION
======================================================================

The goal is NOT:

    “get EXP005 running at all costs”

The goal is:

    build enough scientifically defensible infrastructure that we can
    know whether EXP005 is actually ready.

If Phase 3D discovers the free-data approach cannot support EXP005,
report that.

If inference still cannot be calibrated, report that.

If historical terminal values remain incomplete, report that.

If all mandatory gates genuinely become certified, then mark:

    EXP005_FREEZE_READINESS = READY

but still do NOT run it without separate authorization.

The most important property of Research OS is that it refuses to
manufacture certainty.

Begin by inspecting the repository and producing the Phase 3D
implementation plan against the actual current codebase, then proceed
with implementation under these constraints.