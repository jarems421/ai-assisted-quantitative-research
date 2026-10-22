# Opportunity Scout V002 prompt research — prospective only

**No hosted trials, scientific generation, source acquisition or prompt activation.** Baseline/main: `4ace618c6a68d525407417dc45b93f0ae400090f`. Branch `codex/scout-v002-creativity` is independent of still-unmerged collector PR #11. No N1 package or frozen V004 input includes V002. Collector work continues separately; this work is not a prerequisite to N1 and must not delay it.

The supplied 25-page PDF was read in full, including its reference list (exact file hash in the [attribution register](prompt_research_sources_v002.json)). Its recommendations are hypotheses. Its suggested run sequence, claims of likely improvements and Skill workflows are not execution instructions. Only the owner's engineering/prompt-research request authorises this implementation. No external Skill, tool, model agent or third-party implementation was installed or activated.

## Two explicit single-invocation candidates

`src/research/opportunity_scout/prompt_research/prompts.py` exposes:

```python
from src.research.opportunity_scout.prompt_research import prompts
candidate = prompts.make_prompt(validated_state, "FORGE", 2, "PROMPT-RESEARCH",
                                version=prompts.B)
request_bytes = prompts.payload_bytes(candidate)  # Local bytes only, no dispatch.
```

There is no default V002 version, dispatcher or provider call. `version="SCOUT_PROMPTS_V001"` delegates directly to the original constructor and returns its exact historical object. V002 with PLAIN is refused: the registered competent PLAIN baseline gets no specialised creativity instructions. HYBRID is not a new lane; its existing FORGE/RADAR/GAP allocation remains untouched. Any later workflow comparison must freeze the allocation separately, without generated-idea leakage between lanes/attempts.

**A — `SCOUT_PROMPTS_V002A_ABSTRACT_DIVERGENCE`.** A concise search objective broadens abstract economic relationships before final selection/serialization. It encourages distant relational analogy, informative absence, dynamic processes and alternative measurement axes without prescribing an internal reasoning transcript. Structurally distinct mechanisms matter more than sector labels. Speculative but coherent questions can survive with UNKNOWN evidence; they still need an ordinary alternative, discriminating observation and inexpensive falsifier.

**B — `SCOUT_PROMPTS_V002B_STRUCTURED_RECOMBINATION`.** The priority candidate explores constraint/shock, role, transfer/obligation, counterparty, transmission object, observable trace, timing and counterfactual. Ten named optional lenses cover inversion, role transfer, obligations, stocks versus transitions, measurement axes, qualified absence, distant relational analogy, second/third-order incidence and counterfactual comparisons. It asks for coherent combinations, not a Cartesian-product checklist or long chain of thought. The final representation remains Trigger -> Operations -> Transmission -> Party -> Consequence.

Both ask for only the final requested JSON. No intermediate brainstorming, private reasoning disclosure, separate critic call, repair or reflection loop is requested. No examples are included: anchoring versus steering is an unresolved empirical tradeoff. A future few-shot variant would be separately versioned and tested, not silently added to either candidate.

## Lane and evidence integrity

| Lane | Candidate behavior | Boundary retained |
|---|---|---|
| FORGE | Abstract recombination/analogy before names | No source/memory input, seed/historical refs empty, every link inferred/unverified |
| RADAR | Supplied observations precede alternative interpretations and downstream consequences | Exact visible quotes, inherited depth, observed/inferred separation; missing reports are not factual absences |
| GAP | Invert a supplied historical measurement obstacle in a different setting | Exact investigation/requirement, original verdict and source stops retained; new source availability stays UNKNOWN |
| PLAIN | Explicit V001 only | Frozen text/hash/default behavior unchanged |

V002 reuses the V001 constructor's seed projection, 8,000-character source prefixes, cutoff checks, lane access and full response schema; it changes the creative instructions in a separate envelope. `validate_response()` checks provenance and delegates to the original engine's schema/lane/semantic/citation validator, without rewriting the raw response. No claim of company exposure, contract allocation, historical public time, external originality, M/H passage or available data follows from valid JSON. Graph connectivity remains non-evidence.

The original seven transformation enums and thirteen mechanism families are unchanged. New lenses are not new output labels: the model must choose a truthful supported tag for an aspect and explain other structure in existing fields. This may still restrict mechanisms that cannot fit the taxonomy; it is a disclosed shared constraint, not proof of exhaustiveness. A future schema amendment would require a distinct experiment.

The inherited legacy constructor's 6,000 output-cap audit field is omitted from **new V002 envelopes**, not edited in V001 or V004. V002 has no runtime authority. Candidate 32,768 and any R3 resource policy must be separately adopted/frozen for a new comparison. Detailed explanations are preserved within the unchanged schema's existing field sizes; no artificial word cap is added. Extra instruction/schema/context bytes create overhead. The 240,000-byte local IO guard is not tokenization, full CLI input coverage or a consumption guarantee. Resource differences and possible formatting failures are outcomes to report, not grounds for tuning prompts after seeing results.

## Provenance and reproducibility

`prompt_research/resources/manifest.json` pins normalized-LF resource hashes, the frozen baseline source hash and full schema hash; mismatches fail rather than auto-refresh. Each prospective prompt binds its exact canonical hash, resource manifest, source closure, original V001 projection, eligible pool hashes, cutoff and explicit version. CRLF-to-LF normalization is declared and applies only to repository text fingerprints; exact generated request bytes would need a separate future freeze. The new conservative source inventory is separate from all historical package inventories. Validation does not append scientific ledgers or claim an actual generation.

Construction Python/dependency versions are also pinned and rechecked. `payload_bytes()` exposes the exact canonical lane/count/cutoff/instructions/schema/context projection, separately hashed and byte-counted. Source inventories and audit metadata stay outside the transmitted task; the full response schema appears once. Those bytes still have no system/runtime/hosted authority and their size is not a complete provider-token bound.

Research references, revisions, licenses, techniques and transfer limits are registered separately. Important corrections: CreativeDC's verified v2 title is *Enhancing Diversity of LLM-Generated Educational Tasks*; format-template research does not establish a Scout JSON-schema effect; the inspected AI Scientist code uses a custom source-code license, not an assumed unrestricted open-source license. No external implementation/prompt blocks were copied. Non-exclusive arXiv distribution rights are not treated as software-reuse rights. The proposed economic prompts use original wording and methodological ideas.

## Proposed evaluation and immediate use

The [new evaluation proposal](prompt_evaluation_v001.json) compares V001/A/B on FORGE only, six attempts per arm, two cards per attempt: **18 proposed attempts / 36 intended slots**. This is not the existing V004 twelve-attempt/24-slot comparison and spends none of its reservations. Six permutation blocks balance each arm twice at each position, frozen without model results. RADAR/GAP can later be tested in their own matched strata; they are not pooled opportunistically into this primary pilot. This design choice needs owner approval.

The primary proposed rate is distinct, independently reviewed M-investigation-worthy mechanisms per total human generation-supervision/review hour. Report reported-token efficiency, generation-wall efficiency and actual attributable charges separately; do not invent a composite denominator. All failed work counts. Two independent humans should seal assessments before reveal and disclose generation exposure. Hide prompt/runtime identifiers and randomise review order, while acknowledging content may reveal the variant. Disagreement remains unresolved, not assistant-adjudicated. Human mechanism clusters count once within each arm; the same independently found mechanism can earn each arm credit once, with cross-arm overlap disclosed. Do not credit only the first generation in time.

Keep structural novelty, mechanism diversity, economic coherence, falsifiability, distinctive predictor, independent outcome potential, evidence integrity, source-route researchability, information timing/expectation revision, duplication and human effort separate. A worthy next M investigation is not any of the six original-evidence M requirements passed, a positive H decision, causality or alpha. Source-route potential can remain UNKNOWN; cheap discriminating checks are proposals only.

`prompt_research/evaluation.py` supplies the balanced order, full reserved-slot inventory, inclusive four-component R3 arithmetic, separate content/resource outcomes and existing internal proximity flags. Missing/conflicting usage or effort stays UNKNOWN; costs are not inferred from tokens or list-price estimates. Invalid/surplus/absent outputs and undispatched slots are retained. No human quality labels are created. The inventory always reports comparison incomplete without independent reviews; even all VALID JSON does not imply scientific success. Software similarity is a review aid, not mechanism identity or external novelty.

The 24 intended V004 cards are too few to establish small differences; this proposed 36-slot pilot also has no demonstrated power. Cards within one attempt are dependent. A pilot can identify large practical problems or promising effort-adjusted yields, but a promotion claim needs a separately registered replication and worthwhile effect size. Future Claude generations and independent reviewers are required to test the hypothesis that either prompt actually improves ideas. Offline tests cannot choose a winner.

## File inventory

New source namespace: `prompt_research/__init__.py`, `prompts.py`, `evaluation.py`. New versioned resources: `resources/abstract_divergence.txt`, `structured_recombination.txt`, `common.txt`, `lanes.json`, `manifest.json`. New test: `tests/opportunity_scout/test_prompt_research.py`. New documentation: this report, `prompt_evaluation_v001.json`, `prompt_research_sources_v002.json`, `scout_agentic_v001_design.md` and `prompt_research_validation_v002.json`. No existing tracked file is changed. The current CI discovery already runs the new guarded tests; no workflow redesign is required.

Recommendation: retain B as the priority **candidate**, A as the simpler alternative, and V001 as the unchanged control. Review the prompt/evaluation package separately while resolving N1's narrow native admission/runtime/consent gates. Do not substitute V002 into the frozen V004 workflow or launch a trial on the basis of this document.
