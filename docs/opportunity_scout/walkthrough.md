# Opportunity Scout walkthrough

Two different artifacts exercise the same importer and archive rules. Neither demonstrates an investment opportunity or research-method superiority.

## Synthetic rehearsal

`python -m src.research.opportunity_scout demo --write` regenerates [synthetic_demo.json](synthetic_demo.json). With `--out .research/opportunity_scout/new-demo`, it also retains a complete replayable local archive.

The rehearsal freezes all lane prompts first, records three **SYNTHETIC_FIXTURE** attempts, imports six fictional cards, runs structural/provenance checks and a diversity selection, and records one simulated READY approval. The resulting Discovery Lab packet is explicitly PROPOSAL_ONLY and contains missing fields rather than invented source passports, observations or M/H reviews.

| Lane | Fictional mechanism families |
| --- | --- |
| Forge | Working-capital transfer in returnable packaging; complementary demand in water-treatment services. |
| Radar | Competition for inspection capacity; shared cold-storage liability transfer. Its source is an explicitly fictional index. |
| Gap | Customer-level recovery credits; municipal pump overhaul obligations. Historical F01 gaps supply cited memory, while all new economic premises are synthetic. |

The nine negative controls test automatic refusal or review warnings. Paraphrased contractor queues are surfaced as a possible mechanism duplicate, without asserting common economic identity. A coherent no-evidence card survives in INCUBATE. Semantic coherence and novelty remain missing independent labels even when schema checks pass.

The JSON reports zero model calls, zero real human reviews, no scientific requests, six cards, nine controls, UNKNOWN costs and no completed real baseline comparison. Simulated reviewer decisions never count toward real human-hour metrics.

## Operator-assisted example

[Saved prompts, responses, cards and report](operator_example/) contain three actual hypotheses authored by the existing Codex assistant and processed through the production operator importer. The complete original model output and provenance remain in the response files; these files are examples for replay, not a production generator or silent fallback.

All three prompts were exported before importing any card. Forge was authored/imported before Radar and Gap. The Forge payload contains no source seeds, memory or generated Radar ideas. **The author was an existing Codex session that had already read repository/design context**, so this is not evidence of independent fresh-session generation. An actual comparison should use fresh contexts as the guide specifies.

| Lane | Proposed question | Critical missing evidence | Recorded route |
| --- | --- | --- | --- |
| Forge | Could a battery-module warranty amendment transfer retained maintenance cash risk to equipment lessors? | Contract eligibility, retained allocation, collectibility and separate recovery receipts for the same leased cohort. | INCUBATE |
| Radar | Could property-policy takeout cohorts compete for mandatory inspection appointments at independent service contractors? | Actual inspection obligations/deadlines, assigned bookings, shared constrained rosters, independent customers and completed-job invoices. Policy counts are not those measurements. | INCUBATE |
| Gap | Could an unredacted municipal lease termination/repurchase schedule make equipment-financier residual exposure observable? | Original applicable schedule, named parties/security and independent settlement receipts. The alternative source has not been checked. | INCUBATE |

Radar's single source is an exact **retrospective report excerpt** from the existing EF06 catalogue. It inherits SOURCE_DESCRIBED, not original-field status. EF06 v1 remains HOLD; v2 remains rejected as an investment priority. The inspection mechanism is conjecture, and no contractor relationship or market exposure is asserted as fact.

Gap preserves F09's unredacted-amount obstacle and proposes a different domain. It does not reopen supplier-claim source work, infer a receivable amount, assert that a municipal document is accessible, or reclassify F09 as successful.

Provider identity is recorded as the current Codex/GPT-6 session with the exact API model version UNKNOWN. Per-invocation server timestamps, sampling seed, tokens and costs were unavailable and remain UNKNOWN. Workflow append/completion timestamps are recorded separately. There were **zero new model API calls, external novelty searches, scientific-source requests or real human reviews**. The hypotheses are unreviewed; no public/private novelty or investment value has been established.

Replaying the saved responses with the [operator guide](README.md#run-a-real-operator-assisted-batch) exercises the full batch/triage/shortlist/incubator path without claiming that new generation occurred. Human approval is intentionally absent, so an actual handoff attempt is refused. The synthetic rehearsal separately demonstrates the approved-handoff code path without inventing an owner decision.

## Evaluation boundary

The frozen protocol precedes implementation in commit `a13d2e3`. Unit tests exercise four equal-budget **synthetic** conditions, sealed packet integrity, metadata concealment, missing reviews, and shadow metrics against explicitly supplied fixture labels. The real four-condition generation-and-human-review study is NOT_RUN. Jev and Ollama wire boundaries were tested with fake transports; no successful live integration call is claimed.
