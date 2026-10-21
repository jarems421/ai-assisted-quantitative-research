# Research OS — Build Discovery Lab v1

## Your role

You are the lead architect, quantitative research scientist and senior Python engineer working on Research OS.

Repository:

https://github.com/jarems421/ai-assisted-quantitative-research

Your mission is to **design and implement a genuinely useful, evidence-first investment idea discovery system** inside our existing Research OS.

This is an implementation task, not another theoretical research exercise.

I want a working, testable Discovery Lab that improves the quality of the investment hypotheses entering our existing research pipeline.

Use deep reasoning, but do not mistake complexity, large amounts of generated code or elaborate architecture for quality.

**Build the smallest effective system that solves the actual discovery problem.**

---

# 1. Understand the problem before designing the solution

Research OS already has extensive scientific infrastructure for investment research, evidence provenance, experimentation, statistical testing and preservation.

However, our upstream discovery process has repeatedly produced fascinating economic hypotheses that ultimately lacked essential measurable information.

Examples include:

- F01: shared salmon-industry treatment capacity, but the required private capacity allocations were not observable.
- F03: chemical substitution, without matched qualified sales or output.
- F09: bankruptcy-protected receivables, with critical contract amounts redacted.
- F19: insurer assessments and tax credits, without the required state/cohort capacity and outcome join.
- SH09: offshore predecessor cleanup obligations, where the original asset and security schedules were missing and the historical net-exposure predictor could not be reconstructed.
- EF06: insurer takeouts, where a reformulated gross-premium relationship was measurable but largely repeated what the issuer had already explained.

These failures do not necessarily invalidate the economics.

They demonstrate that our discovery process has often prioritised an appealing mechanism before establishing whether the distinctive information actually exists.

**Discovery Lab must fundamentally improve that ordering.**

We are NOT trying to build:

- Another generic trading indicator generator.
- A platform for collecting obscure datasets without a purpose.
- A gigantic web scraper.
- An autonomous stock picker.
- A multi-agent framework for its own sake.
- A system that generates hundreds of speculative investment theories.
- A second, incompatible research operating system.

We ARE trying to build a research instrument that finds meaningful, genuinely observable economic information and converts the strongest observations into precise, falsifiable investment research hypotheses.

The ultimate question is:

**Can we systematically discover a greater number of genuinely measurable, financially material, potentially differentiated research opportunities per analyst-hour than our previous approach?**

No claim of superior investment performance is justified until independently demonstrated.

---

# 2. Inspect the current repository first

Start by checking actual HEAD, Git status and existing project conventions.

Review at least:

- `AGENTS.md`
- `README.md`
- `docs/acceleration/master_plan.md`
- `docs/strategy/measurement_gate_m.md`
- `docs/strategy/frontier_selection_standard.md`
- `docs/strategy/measurement_gate_campaign_report.md`
- `docs/strategy/measurement_gate_campaign_cards.md`
- `docs/strategy/short_horizon_discovery_report.md`
- `docs/strategy/sh09_verification_report.md`
- `docs/strategy/discovery_bottleneck_report.md`
- Relevant research modules, CLI conventions, tests, source manifests and ledgers.
- The README generation template and presentation checks.

Latest known completed commit: `101d532`. Verify the actual repository state rather than assuming this is still HEAD.

If I have attached the new Discovery Lab Deep Research report, read it in full, critically. Treat it as a set of researched recommendations, not as an authoritative software specification. Distinguish verified evidence, plausible proposals and unverified claims.

Preserve all prior experiment contracts, reports, receipts, source stops and research dispositions.

F19 remains on HOLD. SH09 remains stopped. EXP004's execution restrictions remain unchanged.

Do not reactivate any source investigation or investment experiment.

Before implementation, briefly explain what existing repository functionality can be reused and what genuinely needs adding.

---

# 3. The discovery philosophy

The central principle is:

**Start with credible economic information, construct explicit economic relationships, and only then consider investment hypotheses.**

A dataset is not a signal.

An unusual correlation is not an economic mechanism.

An economic mechanism is not necessarily a public information advantage.

A public information advantage is not necessarily unpriced.

An unpriced effect is not necessarily an executable investment opportunity.

Discovery Lab must preserve these distinctions throughout its workflow.

### Discovery method A — Observation-first

Begin with something that actually exists in an original record.

Examples of observation types:

- A measurable reduction in capacity.
- A changed entitlement or regulatory payment.
- A contractual milestone.
- A quantity crossing an economically meaningful threshold.
- An observed operational backlog.
- A change in a company's obligations or rights.
- A verified production, shipping or procurement constraint.
- An unexpected mismatch between reported operational quantities.

Then investigate:

1. What exactly was measured?
2. In what units, by whom and when?
3. Which economically relevant entity is connected to it?
4. What financial consequence might follow?
5. Can the consequence be independently measured?
6. Does the information add anything beyond existing interpretations?

Observation-first does not mean searching historical outcomes until a profitable-looking pattern appears.

Protect against that selection bias.

### Discovery method B — Relationship-first

Begin with a documented economic relationship.

Examples:

- Supplier → customer.
- Borrower → lender.
- Insurer → insured exposure.
- Regulator → licence holder.
- Asset → responsible operator.
- Former owner → continuing obligation.
- Infrastructure → dependent production facility.
- Contract → beneficiary or obligated counterparty.
- Product shortage → genuinely compatible substitute capacity.

Investigate measurable changes propagating through these relationships.

The relationship must be independently supported.

Do not infer economic exposure merely because two company names appear in similar documents.

### Discovery method C — Event/expectation-first

Begin with a concrete event capable of changing investor expectations.

Examples include a regulatory determination, licence change, contract cancellation, production interruption, court decision or revised operating entitlement.

Identify the economic exposure and determine whether any original public observation could inform its consequences before the obvious issuer or market interpretation.

Distinguish a forecastable event from an event that was merely surprising in hindsight.

### Discovery method D — Hypothesis-first baseline

Preserve a smaller version of our existing mechanism-first discovery approach.

We need a meaningful baseline against which to compare improvements.

Do not automatically assume the newer methods are superior.

All methods must operate under the same scientific standards.

---

# 4. Build a useful Source Qualification workflow

Before promoting an observation, qualify its source.

Create a lightweight **Source Passport** containing:

- Source and original publisher.
- Exact source locator.
- Source family and economic domain.
- Available original data format.
- What economic quantities are actually reported.
- Exact example field names, units and denominator.
- Observation granularity.
- Stable entity, asset or contract identifiers.
- Historical coverage evidence.
- Revision and publication-version policy.
- Known public publication clocks and limitations.
- Frequency and typical release lag, where evidenced.
- Access restrictions and permissible use.
- Plausible links to listed-company financial exposure.
- Important omissions and misleading proxies.
- Evidence depth and precise citations.
- Cheapest next observation needed to establish usefulness.

Distinguish:

- VERIFIED ORIGINAL FIELD.
- VERIFIED ORIGINAL RECORD.
- INDEXED DESCRIPTION ONLY.
- SCHEMA ONLY.
- RETROSPECTIVE DESCRIPTION.
- UNVERIFIED.
- ACCESS BLOCKED.

A source must not be rated highly simply because it is unusual, extensive or machine-readable.

Avoid numerical quality scores that reward missing information.

Create a transparent qualitative prioritisation method focused on the next unit of useful research evidence.

**Critical:** source qualification is an inexpensive discovery aid, not a new evidence level or replacement for Measurement Gate M.

---

# 5. Build the observation system

Implement a compact, structured **Observation Card**.

Each card must contain, where applicable:

- Stable observation ID.
- Discovery method.
- Original source ID.
- Source record locator and recorded evidence depth.
- Source hash or source-archive pointer.
- Actual observation and measured value.
- Units, denominator and economic entity.
- Economic occurrence date.
- First-public availability or explicit UNKNOWN.
- Source record/version timestamp.
- Research retrieval or reconstruction timestamp.
- Why the observation is unusual or economically informative.
- Possible alternative explanations.
- Known information already disclosed elsewhere.
- Whether the observation is independent of an intended outcome.
- Current verification status.
- Links to related observations.
- Exact missing evidence.

Do not conflate economic occurrence, first publication, source version and retrieval.

Unknown timestamps must stay unknown.

Do not calculate historical availability from today's web cache or a historical-looking filename.

Support recording observations without forcing every one to become an investment idea.

An interesting measurement can remain a useful research object without becoming a candidate signal.

---

# 6. Build economic inference and relationship mapping

This is a particularly important component.

Create a simple, typed representation of an economic relationship.

Each relationship should identify:

- Source economic entity.
- Target economic entity.
- Relationship type.
- Economic direction and possible consequences.
- Applicable asset, contract, product or geography.
- Time period over which the relationship applies.
- Original evidence supporting the relationship.
- Whether quantities can actually be transferred or allocated between the entities.
- Known limitations and alternative explanations.

Then implement a lightweight **economic inference workflow**.

The workflow should help construct claims such as:

> A measured change in economic quantity X, affecting entity A through independently documented relationship R, may change listed company B's financial outcome Y within period T.

This is a claim template, not a prediction.

Require the user or Claude to specify what additional quantities are needed to turn this into an actual measurable proposition.

Pay special attention to invalid inference:

- Industry capacity is not company spare capacity.
- An approved contract amount is not realised revenue.
- A balance-sheet reserve is not necessarily cash available.
- An entire subsidiary's activity is not automatically retained parent profit.
- Current ownership does not establish past ownership.
- A gross obligation does not establish net recoverable liability.
- Two related records do not establish causality.

Do not build a graph database unless evidence from the initial implementation demonstrates that simple structured relationship records cannot support the required work.

Use existing Python, files and repository conventions wherever reasonable.

---

# 7. Build candidate formation and hypothesis freezing

A candidate should emerge only after the observation and its potential economic meaning have been articulated.

Each **Economic Inference Card** should include:

1. Distinctive predictor and measurement units.
2. Linked company and verified exposure.
3. Explicit economic mechanism.
4. Proposed independent outcome.
5. Valid join requirements.
6. Expected information event.
7. Plausible 5–20-trading-session relevance.
8. Closest competing explanation or information product.
9. Exact incremental information being proposed.
10. Cheapest decisive falsification.
11. Missing essential variables.
12. Known research-selection history.
13. Claim version.
14. Promotion or stop recommendation.

Preserve separate propositions for:

- Economic effect.
- Informational advantage.
- Residual investment usefulness.

Implement deterministic record validation for required fields, valid references, units and inconsistent states.

A candidate's initial hypothesis must be explicitly frozen before the researcher examines its intended historical outcome.

Changes to the distinguishing variable, population, mechanism or financial object must create a new version rather than silently overwriting the original claim.

Preserve the earlier version and why it changed.

A frozen discovery hypothesis is not a registered investment experiment.

Do not integrate discovery IDs into existing experiment numbering or alter trial counts.

---

# 8. Integrate the existing Measurement Gate M

Do not replace, redefine or bypass `measurement_gate_m.md`.

The existing six requirements remain:

1. Distinctive original predictor.
2. Correct units and interpretation.
3. Separately observable economic outcome.
4. Valid entity/cohort join.
5. Plausible route to historical public-time evidence.
6. Meaningful listed-company financial exposure.

Exact historical first-public certification belongs to later research stages where required. Do not make it a universal prerequisite for provisional measurement work.

Add a lightweight workflow that produces a **Measurement Gate M evidence checklist** from candidate records.

Automated checks may identify:

- Missing references.
- Unknown units.
- Missing independent outcome.
- Unsupported joins.
- Inconsistent entity IDs.
- Incomplete source provenance.
- Contradictory claim versions.

However, **software must not automatically certify M PASSED merely because fields are populated**.

The economic and evidential judgments remain subject to explicit human review.

Separate the H assessment:

Does a concrete information event plausibly change market expectations over 5–20 trading sessions?

Neither M nor H certifies alpha, causality or trading readiness.

Do not create a new Store transition or silently modify Level A/B/C.

---

# 9. Make Discovery Lab sceptical by design

The system should actively challenge proposed inferences.

Implement a documented reviewer workflow covering:

**Measurement sceptic:** Is the supposed predictor actually observable in the required units and population?

**Economic sceptic:** Does the proposed relationship produce the financial consequence being claimed?

**Information sceptic:** Is this already explained by the company, regulator, established research or commercial specialists?

**Timing sceptic:** Could the researcher have known the information before the proposed investment decision?

**Selection sceptic:** Was the candidate chosen because we inspected the answer or because an old event was famous?

**Investment sceptic:** Even if the economics are correct, why might investors have failed to price the information already?

These should initially be structured Claude review instructions and evidence checklists, not an expensive automatic multi-agent service.

Require explicit acknowledgement when a competitor, historical source or outcome has not actually been checked.

No unsupported claims such as "nobody else has discovered this" or "institutions overlook this".

---

# 10. Build a fair discovery-method comparison

We need to find out whether Discovery Lab improves our research process.

Implement a compact **Discovery Campaign** record supporting comparisons between:

- Observation-first.
- Relationship-first.
- Event/expectation-first.
- Hypothesis-first baseline.

Each campaign should record:

- Method used.
- Hypotheses or observations considered.
- Evidence encountered.
- Search and source attempts.
- Research time.
- External acquisition bytes.
- Source failures and restrictions.
- Candidates formed.
- Candidates stopped.
- Measurement Gate M decisions.
- H assessment.
- Specific reasons for failure.
- Cost of investigating promising candidates.

Useful evaluation measures include:

- Distinctive original predictors actually observed.
- Valid cross-source economic joins.
- Independent outcomes identified.
- Candidates satisfying all six M requirements.
- Candidates with plausible short-horizon information events.
- Substantive duplication with existing information products.
- Analyst time per defensible candidate.
- Research effort spent on unavailable variables.
- Downstream verification cost.

Distinguish observed results from incomplete assessments.

Do not construct a simplistic composite "alpha discovery score".

Do not reward one approach merely for creating more ideas.

Preserve denominators and abandoned attempts.

Make comparison budgets equal at the beginning rather than hard-coding an arbitrary 50/30/20 allocation. Adaptive budget allocation should require explicit evidence and approval.

Small early campaigns are exploratory; do not attach unjustified statistical confidence to an eight- or ten-idea comparison.

A useful discovery system must learn which methods produce better research objects, not simply generate more files.

---

# 11. Make the system usable in actual research

I do not want a collection of Markdown templates with no working workflow.

Build a minimal, coherent Python interface using the repository's existing conventions.

The precise command names are your choice after inspecting the codebase, but the operator should be able to:

1. Create a discovery campaign.
2. Register or inspect a source passport.
3. Record a real or explicitly synthetic observation.
4. Link an observation to a documented economic relationship.
5. Form an economic inference candidate.
6. Freeze the candidate's initial claim.
7. Validate the record and display missing evidence.
8. Record human M/H review and a reasoned stop/hold/verify disposition.
9. Produce a readable campaign summary.
10. Compare results across discovery methods without misrepresenting small samples.

Prefer simple JSON, existing ledgers, small Python modules and deterministic validation.

Reuse the existing infrastructure where suitable.

Do not duplicate the immutable-source system, introduce a new database, build a web application, create a scheduler or require a paid AI API.

Claude itself can be the interactive reasoning and discovery assistant; the local software should preserve evidence, validate mechanical requirements and make decisions auditable.

Provide useful examples and an operator guide.

A researcher should be able to perform a complete, offline demonstration without connecting an external service.

---

# 12. AI reasoning workflow

Use Claude where semantic reasoning genuinely helps:

- Identifying economically meaningful observations.
- Recognising possible cross-source relationships.
- Proposing falsifiable economic implications.
- Constructing precise alternative explanations.
- Finding conceptual similarities to known research.
- Critiquing hypotheses.
- Designing cheap decisive verification steps.

Do not delegate deterministic or high-risk factual certifications to unsupported language-model judgments.

Examples requiring checked source evidence or deterministic implementation:

- Publication timestamps.
- Numeric units and arithmetic.
- Legal obligations.
- Historical identity mappings.
- Source access rights.
- Financial allocations.
- Data completeness.
- Performance measurements.
- Correct economic outcome joins.

Provide reusable, structured Claude research prompts for each stage.

The AI reasoning workflow should ask for the **minimum additional evidence that could change a decision**.

It should not endlessly expand research because an idea sounds interesting.

---

# 13. Scientific and resource protections

This implementation task authorises local engineering and offline demonstration only.

**New scientific-source acquisition budget: ZERO.**

Do not conduct a live discovery campaign.

Do not download additional economic datasets.

Do not make paid requests.

Do not reopen closed source routes.

Do not trigger authenticated external services or cloud jobs.

Do not acquire security-price data, examine stock returns or conduct backtests.

Do not create or register a new investment experiment.

Existing repository evidence can be referenced at its recorded reading depth, but do not relabel old evidence as newly verified.

Use synthetic, appropriately labelled fixtures for functional demonstrations.

If using historical examples from existing reports to exercise the workflow, mark them as retrospective, previously inspected and unsuitable for untouched validation.

Do not generate imaginary profitable examples.

The future live campaign should require a separate explicit instruction and acquisition budget.

---

# 14. Implementation strategy — avoid overengineering

Use the following approach:

### Phase 1 — Architecture audit

Identify reusable functionality and the minimum new components.

Write a short design explaining the data flow and important boundaries.

Do not spend most of the task writing abstract architectural documentation.

### Phase 2 — Working vertical slice

Implement one complete offline pathway:

Source Passport → Observation → Economic Relationship → Candidate → Frozen Claim → M/H Evidence Review → Campaign Summary.

Make it functional and testable before expanding features.

### Phase 3 — Additional discovery methods

Support all four discovery methods through the same underlying evidence structure.

Avoid four separate implementations with duplicated logic.

### Phase 4 — Scientific safeguards

Implement immutable or clearly versioned claim history, source-evidence checks, timestamp separation, missing-data handling and appropriate status validation.

### Phase 5 — Comparison and reporting

Create a compact method-comparison report that correctly handles sparse results, unknowns and stopped investigations.

### Phase 6 — Documentation and validation

Deliver concise operator instructions, examples, tests and repository integration.

No unnecessary framework or speculative platform components.

---

# 15. Tests and acceptance criteria

The finished implementation must be demonstrably functional.

At minimum, test that:

- An original observation can be recorded with correct units and source provenance.
- An observation may exist without being promoted into a hypothesis.
- Economic relationships cannot be silently inferred from coincident names.
- Unsupported aggregate-to-cohort allocations remain unverified.
- A missing public-time certificate cannot be represented as verified as-of information.
- A candidate cannot silently change its original distinguishing claim after freezing.
- A materially changed claim creates a new version.
- An intended outcome cannot simply be copied from the predictor and called independent.
- An incomplete evidence card cannot be automatically certified as passing M.
- A reviewer may record uncertainty without forcing a positive or negative conclusion.
- Human decisions and reasons are retained.
- All discovery methods use the same measurement rules.
- Small campaign results do not generate unjustified performance claims.
- Unknown costs remain unknown rather than being treated as zero.
- No existing experiment/source stop is modified.
- The offline demonstration makes no external research requests.

Add appropriate property, regression or edge-case tests where valuable, without creating a huge testing framework.

Run the repository's existing local and public checks, plus new Discovery Lab tests.

Preserve historical results.

If generated presentation documents change, use their canonical source template and supported generation process.

---

# 16. Final deliverables

I expect:

**A. Working implementation**

A functional, lightweight Discovery Lab module integrated with Research OS.

**B. Research workflow**

A documented evidence-first process that Claude can use to investigate observations and relationships.

**C. Source and observation records**

Reusable source passports, observation cards, economic relationship records and candidate records.

**D. Measurement and information safeguards**

Existing M/H standards respected, with explicit verification and human adjudication boundaries.

**E. Campaign comparison**

A way to compare how different discovery approaches perform on research quality and efficiency.

**F. Offline walkthrough**

Demonstrate the full working flow on synthetic records.

**G. Documentation**

An operator guide explaining how to use Discovery Lab, how to interpret statuses, and when to request authority for a future live source campaign.

**H. Validation and delivery**

Run relevant tests, inspect the diff, preserve all existing work and report exactly what passed.

Commit and push the finished implementation if the working tree is safe and no unrelated modifications need to be included. Otherwise leave changes clearly isolated and explain the delivery blocker.

Report actual commit and hosted CI status without assuming success.

---

# 17. How I want you to reason

This is particularly important.

Use a scientific, adversarial, evidence-first reasoning process.

At each significant design decision, ask:

**First — Necessity**

What specific Research OS failure does this component prevent?

If you cannot identify the failure, reconsider the component.

**Second — Evidence**

Does the component help establish a real measurement, relationship or information advantage, or does it merely organise speculation?

Prioritise the former.

**Third — Falsifiability**

Can the proposed inference be rejected by a specific original observation?

If not, improve its formulation before promoting it.

**Fourth — Investment relevance**

Does the information have a credible connection to listed-company expectations and a plausible short-horizon event?

Do not substitute economic importance for a trading edge.

**Fifth — Simplicity**

Could a smaller deterministic implementation provide the same scientific value?

Prefer it unless there is a concrete reason not to.

**Sixth — Comparison**

How will we know this discovery process produces better research inputs than our previous method?

Preserve a baseline and measurable evaluation criteria.

**Seventh — Adversarial review**

What are the strongest reasons the idea, inference or software design could be wrong?

Try to falsify your own design before considering it complete.

Give me concise explanations of major architectural choices, rejected alternatives and remaining limitations. I do not need a transcript of your private internal deliberations.

Use your strongest available reasoning for architecture, financial-information semantics and scientific safeguards.

Do not spend resources endlessly reconsidering low-stakes implementation details.

---

# 18. Final instruction

Do not stop after producing a plan.

Plan the implementation briefly, then **build the usable first version** within the scope above.

The final result should be something we can immediately use for structured, evidence-first idea discovery once I separately authorise a live research campaign.

Prioritise:

**Better candidate quality → fewer unmeasurable ideas → clearer economic links → faster cheap falsification → more worthwhile research questions.**

Do not optimise for feature count, impressive architecture, number of hypotheses generated, or speculative claims about future trading profitability.

The goal is to turn Research OS's weakest stage—upstream discovery—into a disciplined, efficient and empirically improvable research capability.

Build Discovery Lab v1 accordingly.
