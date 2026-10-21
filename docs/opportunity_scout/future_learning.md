# Future-learning data contract: capture now, do not train

Phase 1 uses fixed `SCOUT_FROZEN_POLICY_V001` and `SCOUT_PROMPTS_V001`. No event handler updates prompts, budgets, quotas, similarity thresholds, weights or training data selection in response to outcomes. `learning-export` is a dataset export, not a learning operation.

## Units and time

| Unit | Identity and immutable information |
| --- | --- |
| Batch | Stable batch ID, starting main commit, fixture class, knowledge cutoff, budgets and fixed memory snapshot with catalogue/report/graph hashes. |
| Attempt | Reserved ID before dispatch; requested provider/model; prompt hash and complete context; actual returned model, parameters, supported/unknown seed, invocation/completion metadata, raw output, errors and known/unknown token/cost fields. Pending attempts stay pending rather than being resubmitted invisibly. |
| Idea version | Stable idea ID plus increasing version; original creation/cutoff, seed snapshot hashes, generated content, inherited depths and initial features. The original hypothesis stays GENERATED_CLAIM. |
| Revision | Previous-version hash, reason, actor, outcome-inspection declaration and MATERIAL_REFORMULATION/CLARIFICATION label. Version 1 and its features are never replaced. |
| Review | Target idea/version, actor kind/identity, concrete reason and uncertainty, routing decision, effort, proposal-only handoff approval. Later reviews reverse routing without deleting older reviews. |
| Selection | Fixed policy, selected niches, exploration reservation and all candidates' selected/unselected states and reasons. Unselected does not mean unsuccessful. |
| Outcome reference | Separately recorded downstream label, exact external record hash/quote/locator, human actor and time. Scout does not independently certify, recompute or create that decision. |

Archive event `recorded_at` is append time. Source clocks, model invocation time, historical catalogue recording time and outcome-reference time are separate. An old event date does not make a later transcription point-in-time evidence. A modern model may know historical outcomes; this system claims no genuinely unseen historical evaluation.

## Labels must remain separate

| Label | Permitted interpretation | Forbidden substitution |
| --- | --- | --- |
| NOT_INVESTIGATED | No legitimate downstream outcome is recorded; selection may be non-random. | Bad idea, zero return, failed M, negative training label. |
| SOURCE_BLOCKED | A recorded route failed or was inaccessible; the mechanism may remain untested. | MECHANISM_FALSIFIED or no economic value. |
| MECHANISM_FALSIFIED | A referenced observation/decision weakens the specified economic mechanism within scope. | Universal disproof, unprofitability, or a source-access result. |
| MEASURABLE | A measurement object was recorded as available. | M passed, H passed, forecast increment, implementability or alpha. |
| M_PASSED | Reference to an actual human M decision recorded elsewhere. | A Scout certification or new acquisition authority. |
| H_PLAUSIBLE / H_NOT_ESTABLISHED | Separate human horizon judgment references. | An observed short-term market response. |
| STATISTICAL_RESULT | A later separately governed result, with the original reference and selection context. | Retrospective permission to tune original ideas or overwrite initial features. |
| REFORMULATED | A materially changed question; preserve predecessor and outcome knowledge. | Success of the original hypothesis. |

SCOUT_REVIEW is routing. DISCOVERY_LAB_OUTCOME and MEASUREMENT_GATE_OUTCOME remain downstream references, not target labels created by Scout. The full event history permits keeping those categories distinct when preparing any later dataset.

## Selective investigation and denominator rules

Keep every valid generated card, duplicate and rejected card; malformed generations remain as retained raw attempts with errors. Retain all material revisions rather than training on the polished survivor alone. The current importer never silently substitutes fixtures for missing generation.

Preserve all shortlist entries, unselected candidates, deferred/incubated candidates, missing independent judgments, source failures and unknown time/cost. Review minutes and additional-effort entries must not duplicate the same work. Human-hour yield stays null if required human review/time is missing; known-zero cost is different from unknown cost.

The saved operator example has three incubated hypotheses and no human/scientific outcome labels. The synthetic rehearsal has simulated review decisions explicitly labelled SYNTHETIC_FIXTURE. These populations must not be pooled into a prospective research success rate. Synthetic reviewer values cannot pass as real human labels in the comparison harness.

## Before any future training

A new owner decision and independently reviewed design would need to establish valid label definitions, data rights, temporal splits, model/knowledge contamination limits, dependence and selection mechanisms, handling of missing-not-at-random outcomes and reformulations, and appropriate untouched evaluation. No such policy, model, contextual bandit, self-fine-tuning, feedback-driven prompt adjustment or reinforcement learning is implemented here.
