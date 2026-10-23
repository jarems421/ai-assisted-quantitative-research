# Owner instruction: Opportunity Scout AI Critic V1 (2026-10-23)

Archived verbatim below the rule. The owner also supplied a 34-page ChatGPT report, "Robust AI Critics for Opportunity Scout". It is read critically in [ai_critic_v001.md section 9](ai_critic_v001.md#9-reading-of-the-supplied-report); its original is not stored in the repository. This instruction authorises an offline implementation and a draft PR only: no model call, source acquisition, activation, credential access or merge.

---

# Research OS — Implement Opportunity Scout AI Critic V1

## Mission

We are developing **Research OS**, an AI-assisted quantitative research platform intended to discover unconventional, economically meaningful, falsifiable hypotheses with potential investment applications.

Repository: `jarems421/ai-assisted-quantitative-research`

I want you to **implement a rigorous, scalable AI critic system for Opportunity Scout before we proceed with real generation experiments**.

This is an implementation assignment, not merely a research document or architecture proposal.

Our existing Scout workflow uses human feasibility and readiness reviews. That is scientifically useful but will become a throughput bottleneck if we eventually generate hundreds or thousands of hypotheses.

The goal is to establish an AI-first review architecture in which specialist AI critics perform routine hypothesis assessment, Jev contributes structured independent judgments, and humans intervene selectively for calibration, difficult disagreements, significant research expenditures and consequential authorisations.

**The central requirement:**

Build critics that are difficult to fool, neither excessively lenient nor indiscriminately harsh, and capable of distinguishing scientifically fatal flaws from uncertainty that makes an idea worth investigating.

We want to preserve unconventional, potentially valuable hypotheses without compromising research standards.

---

## 1. Inspect the existing repository first

Fetch the latest `main` and inspect the actual implementations of:

- Opportunity Scout generation, schema validation, triage, duplicate detection, feasibility, review, selection and handoff.
- Existing frozen V001–V004 evaluation protocols and implementation/package hashes.
- N1 Windows observer, native collector and disabled launch boundary.
- The merged PR #21 post-generation evaluation workflow.
- Jev `providers.py`, its five existing questions, importer, response validation, provenance records and evaluation metrics.
- Discovery Lab, Measurement Gate M and the existing owner-authorisation boundaries.
- Graph R4's separately proposed AI adjudication design, for reusable assurance patterns only.

Do not assume a component is missing until you verify its implementation.

Before editing, produce a concise built-versus-missing inventory and identify the smallest set of new modules needed.

**Do not modify frozen experimental protocols or top-level Scout files if doing so invalidates existing implementation hashes.** Prefer a versioned subpackage and separately invoked CLI.

Do not interfere with N1 readiness, the V003 observer or the paused Graph R4 study.

---

## 2. Implement a layered critic architecture

Create a new versioned `AI_CRITIC_V001` workflow with these components.

### Layer A — Deterministic validation

Reuse existing checks wherever possible.

Check:

- Valid hypothesis schema and required fields.
- Exact duplicate detection and possible mechanism similarity.
- Predictor/outcome distinction.
- Falsifier presence and testability structure.
- Citation validity and source provenance.
- Information-timing consistency where evidence is available.
- Unsupported claims of documented evidence or certainty.
- Contradictions that can be established mechanically.

These checks must not hallucinate economic conclusions.

A genuinely speculative FORGE hypothesis must not be rejected merely because it has no source passages.

Separate:

- `INVALID_INPUT`
- `STRUCTURAL_DEFECT`
- `DOCUMENTED_CONTRADICTION`
- `MISSING_EVIDENCE`
- `UNKNOWN`

Only independently verifiable defects should receive definitive mechanical findings.

### Layer B — Scientific Critic

Create a specialist critic focused on:

1. Economic and causal mechanism coherence.
2. Completeness of the trigger → operational change → transmission → affected party → consequence chain.
3. Falsifiability and specific observations that could weaken the hypothesis.
4. Confounders and alternative explanations.
5. Circular reasoning and unsupported inference.
6. Predictor/outcome independence.
7. Evidence integrity and the difference between documented and speculative premises.
8. Information leakage and temporal ordering.

Require the critic to identify the exact proposition or assumption underlying every adverse judgment.

It must distinguish:

- A fundamentally incoherent mechanism.
- A coherent mechanism with an unresolved assumption.
- A coherent, testable but presently unverified idea.

**Lack of verification is not itself proof that a hypothesis is false.**

### Layer C — Economic Opportunity Critic

Create a separate critic focused on:

1. Distinctiveness of the proposed economic mechanism.
2. Internal novelty relative to Research OS history.
3. Plausible economic magnitude.
4. Identifiable parties, incentives and consequences.
5. Potential information asymmetry or underexplored causal relationship.
6. Feasibility of measuring the distinctive predictor.
7. Feasibility of measuring an independently defined outcome.
8. Availability and timing of potential source data.
9. Cost and expected value of the next investigation.
10. Possible relevance to investment research, without inventing profitability.

The critic should look for **research-worthy economic mechanisms**, not merely familiar trading signals.

An unusual idea with difficult data should generally be classified as `INCUBATE`, provided its mechanism and falsifier are credible.

Do not reward obscurity alone. Do not reward vague claims of originality.

### Layer D — Adversarial Critic

Implement a deeper adversarial review that can be invoked selectively.

It should attempt to:

- Find the strongest counterexample.
- Identify omitted assumptions.
- Construct plausible alternative explanations.
- Detect survivorship, selection and information-timing biases.
- Identify simpler existing explanations or substitute indicators.
- Determine whether the proposed falsifier genuinely distinguishes the mechanism.
- Challenge unsupported claims of economic significance or novelty.

**Require the adversarial critic to argue from evidence and logic, not from a predetermined desire to reject.**

Every proposed fatal objection must identify:

- The specific violated requirement.
- The relevant passage, assumption or evidence.
- Why it is fatal rather than merely unresolved.
- What observation, if any, could overturn the objection.

The adversarial critic must also be permitted to conclude `NO_FATAL_DEFECT_ESTABLISHED`.

Do not require it to invent a criticism when none is substantiated.

Initially reserve this critic for disagreements, unusually promising hypotheses, high-consequence candidates or uncertain fatal-defect findings.

---

## 3. Implement a disciplined judgment rubric

Do not use a single generic score such as `overall_quality: 8/10`.

Each critic should produce a strict machine-readable output with independent assessments for:

- Mechanism coherence.
- Falsifiability.
- Evidence integrity.
- Temporal validity.
- Internal novelty.
- Economic significance.
- Measurement feasibility.
- Research feasibility.
- Investment applicability.
- Uncertainty and unresolved assumptions.

For every assessment, include:

- Judgment: `PASS`, `FAIL`, `UNKNOWN`, or `NOT_APPLICABLE`.
- Severity and whether the issue is potentially fatal.
- Evidence or precise justification.
- Assumptions.
- A concrete repair or discriminating next check where appropriate.
- Critic/model/protocol identity and input hash.

Separate objective findings from subjective model estimates.

A model's confidence must never automatically count as validated probability.

The system should explicitly distinguish:

**Hard requirements:** schema validity, authentic citations, no demonstrated future leakage, coherent variable definitions and a testable claim.

**Soft assessments:** novelty, possible economic magnitude, practicality and expected research value.

**Uncertainty:** matters that cannot be determined from the supplied information.

A soft score cannot override a verified hard failure.

An unknown cannot silently become a pass or fail.

Avoid invented numerical precision and unsupported composite scores.

---

## 4. Build a deterministic decision policy

Implement a separate policy engine that consumes the critic outputs.

The critics must not grant themselves authority.

Support these proposed classifications:

**READY_CANDIDATE**

A scientifically coherent, falsifiable idea with a sufficiently clear measurement question and credible investigation route.

This means research-worthy, not proven or authorised.

**INCUBATE**

A coherent or potentially valuable idea with missing evidence, uncertain feasibility, unusual mechanisms or unresolved but nonfatal assumptions.

Preserve the idea and define precisely what evidence would justify reconsideration.

**REVISION_REQUIRED**

A candidate with a potentially repairable defect, such as an ambiguous variable definition or weak falsifier.

**REJECT_RECOMMENDED**

A candidate with a specifically substantiated fatal flaw, such as an incoherent causal mechanism, impossible temporal ordering or demonstrably circular prediction.

**ESCALATE**

A case with significant critic disagreement, uncertain fatal defects, novel high-upside possibilities or insufficient evidence to make a responsible disposition.

Never silently discard candidates.

Retain original versions, all assessments, disagreements and adverse findings.

For V1, these are **recommendations only**. The existing human READY/handoff and owner gates remain authoritative.

Design a separately versioned future routing mode in which calibrated critics may replace routine human review, but do not activate that mode without empirical validation and explicit owner approval.

---

## 5. Integrate Jev intelligently

Jev is already implemented as an optional TypeSafe System One shadow evaluator with five atomic questions.

Do not rebuild it or silently alter its existing frozen request schema.

Inspect the existing implementation and use it alongside the specialised critics.

For V1:

- Preserve Jev as an independent shadow reviewer.
- Reuse its existing response-import and provenance workflow.
- Compare its atomic judgments with the scientific and economic critics.
- Record agreements, disagreements, abstentions and confidence distributions.
- Do not treat Jev confidence as calibrated accuracy.
- Do not allow Jev to override deterministic findings.
- Do not allow Jev alone to reject, approve or promote a hypothesis.

Investigate whether Jev is more valuable as:

1. An early inexpensive atomic screener.
2. An independent disagreement detector.
3. An evidence-overstatement detector.
4. A falsifiability and mechanism-completeness checker.
5. A selective escalation trigger.

Recommend which use is most promising based on a testable evaluation design, not marketing claims.

Its exact model identifier, live response format, cost and operator-attested provenance remain subject to the previously documented limitations.

If additional Jev questions would materially improve evaluation, propose them under a **new versioned instrument** rather than altering the frozen five-question instrument.

No live Jev calls.

---

## 6. Prevent leniency, excessive harshness and AI self-confirmation

The critic prompts must follow explicit evaluation standards rather than generic instructions like "be ruthless."

Implement safeguards against:

- Sycophancy and excessive agreement.
- Excessively generous evaluations.
- Reflexive rejection of speculative ideas.
- Treating unfamiliarity as implausibility.
- Rewarding long or confident prose.
- Anchoring on the generator's stated quality.
- Shared-model confirmation bias.
- Invented fatal flaws.
- Fabricated novelty assessments.
- Prompt injection inside hypotheses and source passages.
- Circular evaluation where Scout judges its own generation.

Blind critics to generator identity, lane, prior scores and other critic outputs during independent initial reviews unless a particular field is genuinely required.

Support different model providers or model families through a bounded interface, without assuming that two prompts to the same model are statistically independent.

Do not make model calls during implementation.

The system should initially permit independent first-pass reviews, followed by disagreement analysis rather than unrestricted agent conversation.

Avoid open-ended debate loops, unlimited retries and uncontrolled token expenditure.

---

## 7. Create an adversarial benchmark

Implement a fixture-only benchmark containing clear, difficult and borderline cases.

Include at least these scenario families:

- A generic but plausible hypothesis.
- A genuinely distinctive, coherent speculative mechanism.
- A hypothesis with nonexistent supporting evidence.
- A hypothesis with no supplied evidence but a valid mechanism.
- A predictor observable only after the outcome.
- A circular predictor/outcome relationship.
- An impressive-sounding but economically incoherent claim.
- A strong mechanism with currently unavailable data.
- A feasible but economically trivial relationship.
- A good hypothesis containing uncertainty honestly.
- A subtly unfalsifiable claim.
- A duplicate rewritten using different terminology.
- A hypothesis with a serious confounder.
- An apparently bizarre idea with a valid, falsifiable economic pathway.
- Source-passage prompt injection.
- Conflicting critic assessments and abstentions.

Include metamorphic tests: altering writing style, length, ordering or irrelevant context should not arbitrarily reverse substantive judgments.

Test opposite failure modes:

**False acceptance:** weak ideas incorrectly promoted.

**False rejection:** promising or valid speculative ideas incorrectly discarded.

The benchmark must not simply reward critics for rejecting most inputs.

Use synthetic cases clearly identified as synthetic. Do not fabricate human expert labels or claim that synthetic accuracy establishes real-world calibration.

---

## 8. Define measurable acceptance criteria

Create a prospective evaluation plan with separate metrics for:

- Recall of independently labelled research-worthy candidates.
- Detection of independently established fatal flaws.
- False-rejection rate.
- False-acceptance rate.
- Precision of alleged fatal defects.
- Abstention and escalation rates.
- Inter-critic agreement and disagreement.
- Agreement against independent human anchors.
- Critic stability across prompt variants.
- Mechanism and sector diversity retention.
- Cost and latency per evaluated idea.
- Distinct useful research candidates per unit of research effort.

As starting engineering targets, investigate 95% recall of research-worthy ideas and 95% detection of demonstrable fatal defects.

**These are proposed targets, not calibrated thresholds or proof of performance.**

Define adequate sample sizes and uncertainty intervals before drawing conclusions.

Do not tune and evaluate on the same benchmark cases.

Include random human audits of AI-rejected and incubated candidates so that potentially valuable false negatives are not invisible.

Keep evaluation results separated by FORGE, evidence-led and other generation contexts.

No autonomy threshold should be activated simply because a small synthetic benchmark passes.

---

## 9. Keep human review selective, not universal

Our eventual target is:

- AI critics evaluate every valid generated card.
- Humans do not manually grade every ordinary card.
- Difficult or disputed cases receive selective human review.
- Random samples of accepted, incubated and rejected cases receive independent audit.
- Humans approve consequential research campaigns, resource expenditure and progression through existing scientific gates.

Implement a review-queue proposal that prioritises:

- Serious critic disagreements.
- Potentially valuable false negatives.
- Novel but poorly understood mechanisms.
- Uncertain fatal defects.
- Candidates requiring significant research resources.
- Representative random audit samples.

The queue must be reproducible from frozen inputs and recorded sampling seeds.

For the initial calibration, independent human labels remain required. Do not relabel AI opinions as HUMAN or bypass the existing contracts.

**The objective is to reduce long-term human workload while preserving a method for detecting when the automated reviewers are wrong.**

---

## 10. Integration and engineering constraints

Use existing Research OS primitives wherever possible.

Prefer a new versioned subpackage such as:

`src/research/opportunity_scout/critic_v1/`

Adapt that path if the repository suggests a better location.

Implement:

- Versioned critic prompts and rubrics.
- Strict output schemas.
- Independent review-input packages.
- Deterministic recommendation logic.
- Review and disagreement records.
- Jev shadow-comparison integration.
- Audit and calibration reports.
- Synthetic fixtures and adversarial tests.
- A CLI for offline preparation, import, validation, recommendation and reporting.
- Clear operator documentation.

A mocked or imported-response execution path is sufficient for initial implementation.

Future live model adapters should be explicitly disabled or fail closed until authorised.

Use content hashes and append-only or write-once artifacts where appropriate. Preserve missing, invalid, failed and conflicting attempts without replacement.

Do not create an unnecessarily large agent orchestration framework, a new database, a new journal infrastructure or an autonomous research system.

Do not silently modify existing Scout READY or Discovery Lab authorisation contracts.

Do not edit the registered Graph R4 human evaluation design.

No source acquisition, experimental activation, hosted API calls, account inspection, credential access, paid inference, real trading or brokerage integration.

---

## 11. Deliverables and validation

Open a **focused draft PR** implementing the complete offline AI Critic V1 foundation.

Include:

1. The implemented architecture and runnable offline CLI.
2. Scientific, economic and adversarial critic rubrics.
3. A reproducible synthetic benchmark and automated regression suite.
4. Jev integration and clearly documented limitations.
5. The deterministic classification and escalation policy.
6. A prospective calibration and eventual autonomy-admission protocol.
7. Specific documentation explaining how routine human review can eventually be replaced without removing consequential owner approvals.
8. Tests proving the frozen V004, N1, V003 and PR #21 boundaries remain intact.
9. Windows, Linux and public CI results on the exact proposed merge commit.
10. A short list of any remaining prerequisites before the first genuine critic evaluation.

Do not merge automatically.

At the end, report:

- Exactly what is implemented.
- What remains design-only.
- What can be tested offline immediately.
- What requires a real model or human reviewer.
- Which thresholds are proposed versus empirically validated.
- Whether the implementation is GO/NO-GO for offline readiness.
- Whether actual AI-controlled routing remains blocked.
- The shortest next step toward our first real Scout generation and critic evaluation.

## Final priority

**We are building this because we want Research OS to discover valuable economic hypotheses efficiently—not because we want to accumulate more software infrastructure.**

Make the design rigorous, but focused and usable.

Do not spend time engineering hypothetical future features that do not improve our ability to evaluate real generated ideas.

The key scientific question we eventually need to answer is:

**Can our AI critic system reliably distinguish genuinely research-worthy, unconventional economic hypotheses from incoherent, redundant or misleading ones, while substantially reducing human evaluation effort?**

Build the smallest serious system capable of testing that question.

Our eventual architecture should support extensive automated critique with selective human oversight, not require a human to approve every ordinary idea.

Preserve scientific integrity, exploration diversity, accurate uncertainty and the possibility that our critics are wrong.
