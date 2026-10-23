# Opportunity Scout v1

A local, non-learning stage before Discovery Lab. It turns approved source snippets, deliberately speculative mechanisms and historical measurement gaps into immutable research proposals. It preserves weak ideas, duplicates, failed generations and unresolved questions rather than pretending they are research results.

[Design and report reading record](design.md) · [Frozen evaluation protocol](evaluation_protocol.json) · [Walkthrough and examples](walkthrough.md) · [Future-learning contract](future_learning.md) · [Validation](validation.json).

## Start here

[Acceptance corrections](acceptance_review.md), [prospective V002 comparison and exact commands](first_comparison_v002/README.md), and [operational quality audit](operational_quality_audit.md) describe the stricter acceptance rules. Protocol V001 and saved operator examples remain historical artifacts.

Work from the isolated **`codex/opportunity-scout-v1`** checkout, based on main `5f3b7ef91cfca8e7d13661a577a67751165c65cd`. Python 3.11+ and the repository's existing `jsonschema`/timezone support are sufficient. There are no new runtime packages, databases or services. If those minimal existing dependencies are missing, install `jsonschema>=4.23,<5` and `tzdata` in your local environment.

```powershell
cd C:\Users\runni\quant-opportunity-scout-v1
python -m src.research.opportunity_scout --help
python -m src.research.opportunity_scout demo --out .research/opportunity_scout/first-demo
python -m src.research.opportunity_scout list .research/opportunity_scout/first-demo
python -m src.research.opportunity_scout shortlist .research/opportunity_scout/first-demo
python -m src.research.opportunity_scout report .research/opportunity_scout/first-demo
```

The demo uses **six synthetic fixture cards**, not model-generated opportunities. Its reviewer is `SYNTHETIC_FIXTURE`, not a human. The demo makes zero model calls and zero source requests. Choose a new output directory on a second run: existing archives and exports are not overwritten. To regenerate the tracked synthetic result, use `demo --write`.

All research output says `SCOUT PROPOSAL ONLY`. Scout never creates a Discovery Lab campaign, writes pilot ledgers, evaluates M/H, runs an experiment, contacts a scientific-data endpoint or grants acquisition authority.

## Run a real operator-assisted batch

The repository includes three **actual structured hypotheses authored by the existing Codex assistant**, separately from the synthetic fixtures. They use the normal importer, have no independently established novelty, and remain INCUBATE. No additional model API was called. This was one existing session, not a controlled test of independent model contexts. [Read their limitations](walkthrough.md#operator-assisted-example).

To replay those saved responses without claiming new generation:

```powershell
$scout = '.research/opportunity_scout/operator-replay'
python -m src.research.opportunity_scout init $scout --title 'Replay of saved operator responses'
python -m src.research.opportunity_scout seed $scout docs/opportunity_scout/operator_example/seeds.json
python -m src.research.opportunity_scout prepare-batch $scout --per-lane 1 --model 'Saved operator response replay; no new model invocation'
python -m src.research.opportunity_scout run $scout --responses docs/opportunity_scout/operator_example/forge-response.json docs/opportunity_scout/operator_example/radar-response.json docs/opportunity_scout/operator_example/gap-response.json
python -m src.research.opportunity_scout list $scout
python -m src.research.opportunity_scout incubator $scout
```

Replay preserves the responses' original model identity and completion metadata, while recording the new import and card-creation times. It does not make the replay an unseen evaluation or a new model call. Requested and returned model identities remain separate. New contexts may contain additional source restrictions; do not present replay as generation against those new inputs.

For **new** generation, initialise a new batch, import your own approved seeds, and run `prepare-batch --model 'actual model identity'`. The archive receives three separate frozen prompts and reserved attempts. Each exported file includes its exact prompt hash, response schema, context and provenance schema.

1. Give Forge its exported prompt in a **fresh model session**, before inspecting Radar's ideas. Forge receives no seeds, memory or another lane's output.
2. Give Radar only its prompt and supplied evidence snippets. A snippet's declared reading depth never becomes new field verification.
3. Give Gap Explorer its prompt and hash-validated historical memory. It must state an exact old obstacle, a different domain and the measurement difference. Prior verdicts and source stops stand.
4. Save each structured output together with actual provider provenance in the response-import envelope.
5. Import the responses with `run --responses ...`, which validates, creates cards, triages and records a diversity shortlist. There is no fixture fallback when output is missing or invalid.

The envelope is `{ "attempt_id": "ATT-0001", "provenance": { ... }, "output": { "ideas": [ ... ] } }`. Export exact schemas with `schema idea` and `schema provenance`; the saved response files are complete examples. The system injects IDs, versions, lane, prompt hash, timing and initial features; a generator cannot grant itself routing authority or an evidence certificate. Underlying model invocation times, seed, tokens and cost can be UNKNOWN when unavailable; recorded workflow times do not impersonate server inference timestamps.

### Optional configured local model

```powershell
python -m src.research.opportunity_scout run $scout --local-model 'your-already-installed-ollama-model' --per-lane 2
```

Use a **new batch with no already-reserved operator attempts** for this alternative. The adapter calls only `http://127.0.0.1:11434/api/generate`, with structured output, an output-token ceiling and no streaming. It never installs, downloads or pulls a model. Failed requests stay recorded with UNKNOWN costs, and there are no automatic retries. This adapter was wire-contract tested with a fake transport; no live Ollama request is claimed in this delivery.

Do not send unpublished ideas, private archives or confidential seed material to a hosted model without separate owner approval. Prompt export stays local and is not approval to upload it.

## Evidence, clocks and boundaries

`seed STORE file.json` accepts an explicit `{ "seeds": [...] }` bundle. `schema seed` supplies the exact format. Each seed includes approved local-use status, publisher/locator, source version, supplied text and matching hash, inherited Discovery Lab depth, evidence kind, four separate clocks, access state and limitations. Seed text is data, never model instructions.

| Display state | Existing vocabulary / meaning |
| --- | --- |
| GENERATED_CLAIM | The opportunity remains a generated hypothesis, including when a seed exists. |
| SOURCE_DESCRIBED | INDEXED_DESCRIPTION_ONLY, SCHEMA_ONLY or RETROSPECTIVE_DESCRIPTION; no original field is established. |
| ORIGINAL_RECORD_VERIFIED | Inherited VERIFIED_ORIGINAL_RECORD on an existing validated observation and exact supplied text artifact. |
| ORIGINAL_FIELD_VERIFIED | Inherited VERIFIED_ORIGINAL_FIELD on that same bounded basis; Scout does not certify it. |
| UNVERIFIED | Unknown or access-blocked evidence. |
| CONTRADICTED | An existing observation explicitly records contradiction; it cannot support a documented link. |

Original-depth inheritance currently requires a **text artifact** whose hash, locator and passage match the supplied observation evidence. It does not turn a PDF excerpt into a new original-byte certificate. Binary/private originals are not opened. Source authenticity and semantic entailment still require human inspection; schema consistency is not proof of truth.

First-public time requires an original publication-record certificate, never an event date, document date or today's API output. Unknown clocks stay UNKNOWN. Seeds or catalogue knowledge recorded after a frozen batch cutoff are refused. Historical/modern-model context is not genuinely unseen historical evidence.

Source-route states are DOCUMENTED_ROUTE, UNTESTED, INACCESSIBLE, UNKNOWN or STOPPED. Even a documented route is not tested access, sufficient fields or permission to call it. Declared seed stops and denied routes cannot be silently reopened. New memory snapshots include exact source references from closed historical investigations; matches are flagged and cannot become the sole route supporting READY. The archive snapshots memory once rather than rediscovering live ledgers.

IO accepts bounded explicit JSON only, rejects duplicate keys/non-finite numbers, private raw/pilot paths and links/junctions, and never resolves nested source locators. Within this checkout, writes are confined to `.research/opportunity_scout/`. Archives inside other repositories or worktrees are refused. Append locks, exclusive exports, size/event ceilings, hash chaining and full rule replay protect against accidental mutation. These are tamper-evident local records, not cryptographic authentication of the owner or source publisher.

## Inspect, review and hand off

```powershell
python -m src.research.opportunity_scout card $scout IDEA-id-from-list
python -m src.research.opportunity_scout triage $scout
python -m src.research.opportunity_scout schema feasibility
python -m src.research.opportunity_scout feasibility $scout your-human-feasibility.json
python -m src.research.opportunity_scout schema review
python -m src.research.opportunity_scout review $scout your-human-review.json
python -m src.research.opportunity_scout handoff $scout IDEA-id-from-list
```

Mechanical checks report missing specificity, malformed chains, predictor/outcome repetition, unsupported novelty language and duplicates. They never certify economic coherence. Exact economic-core duplicates differ from uncertain prose/mechanism overlaps; neither establishes entity identity. Historical requirement matches cite original verdicts and are retrieval aids pending human review.

Automatic routing is only INCUBATE or HUMAN_REVIEW. A human supplies READY or REJECT through an explicit version-targeted review and can reverse it through another append. Source access or missing evidence alone cannot justify REJECT. New READY records use `readiness_version: SCOUT_READY_V002` and need a separate current-version **human feasibility** record: exact publisher/identifiable proposed URL, exact next-step measurement question, substantive assessment, `conclusion: RESEARCHABLE_PROPOSAL`, field/identity/version/outcome limits and remaining unknowns. Placeholder prose cannot identify a route. UNTESTED sources and speculation remain eligible; original evidence is not mandatory. `schema feasibility` and `schema review` expose the complete contracts. READY authorises no work and does not evaluate M. Handoff also needs `approved_handoff: true` and rechecks current feasibility. Historical V001 reviews replay without silent upgrading.

The resulting `DISCOVERY_LAB_STARTING_PROPOSAL_V001` contains the complete card, hash, human Scout review, seed limitations, causal assumptions, predictor, outcome/relationship requirements, falsifier, cost estimate, duplicate references and timing limits. It explicitly lists unavailable Discovery Lab fields. It is **not** a fabricated candidate record and does not create or mutate any campaign.

The shortlist reserves a speculative exploration slot when available, then preserves different mechanism families with separate evidence/sector/role/requirement/pathway reporting. It records every candidate's selected or unselected state. There is no global idea score, learned ranker or outcome-driven selection adjustment. A shortlist is a reading/consideration list, not approval for acquisition.

## Independent findings and criticism

`schema novelty`, `schema feasibility`, `schema critic`, `schema outcome` and `schema effort` expose their exact contracts. Append them with `novelty`, `feasibility`, `critic-import`, `outcome` or `effort`.

- **Novelty:** internal overlap, external/public search and structural mechanism assessment remain separate. External claims require independently recorded search queries, exact supplied source passages and limits. No matching search result does not establish undiscovered ideas or private investor usage. Private usage stays UNKNOWN.
- **Feasibility:** record the original fields, publisher route state, identity/version limits, independent outcome and cheapest check. No API is assumed usable from documentation alone. An access stop stays a stop.
- **Criticism:** `critic-request STORE IDEA` exports the exact card/evidence plus a structured challenge prompt. Import requires a different declared model identity and independent context. Same-model self-review is refused as independent criticism; different names alone cannot prove independence, so the operator must use separate contexts honestly. Critic judgments cannot route or verify an idea.
- **Revisions:** `revise STORE revision.json` appends a new version naming its predecessor, reason, actor and whether outcomes were already known. Changes to the economic core are labelled MATERIAL_REFORMULATION. Initial features and every previous version stay intact; prior READY/approval does not carry to the new version.
- **Incubation:** `reconsider STORE --seed SEED-id --requirement REQ_DOCUMENTED_ALLOCATION` creates suggestion-only leads for exact declared requirements. Exact identifiers can also be supplied; NAME/TICKER or broad keywords are refused. The idea stays incubated until a new human review.

Review records contain their own effort. Use separate `effort` records for **additional** work, not a duplicate of the same review minutes. Missing human time makes the handoff-per-hour metric unknown.

## Jev: optional shadow only

`shadow-request STORE IDEA` exports narrow Choice questions about mechanism, factual support, falsifiability, next-check relevance and certainty. Each includes yes/no/unsure. The official [System One contract](https://docs.typesafe.ai/api/system-one) was checked before implementation; the request pins `jev-1.13.0`, and returned model identity, distributions, confidence, usage and known/unknown cost are retained separately.

`shadow-import STORE response-record.json` imports a separately obtained response after hash/type/distribution validation. It does not change routing, delete cards, decide profitability or certify M/H. The optional Python `JevShadowClient` refuses a hosted call without payload-specific owner/cost approval and an explicit public/synthetic classification. It reads no key until those checks pass. No key is assumed or registered, and no hosted call was made or verified in this task.

After generation, use the [post-generation readiness workflow](jev_post_generation_readiness_v001.md). `python -m src.research.opportunity_scout.post_generation import-response STORE IDEA response.json` imports a saved System One response file unchanged. `label-packet` builds a non-comparative blinded packet of every current card (no Jev output) for independent labels, even when generation is incomplete. `compare` reports agreement, abstention, disagreement types, binary Brier, human–human agreement, problem flags, model identity, usage and unknown cost. It is descriptive and shadow-only, and never a condition comparison.

## Frozen evaluation and future learning

V001 was committed as **`a13d2e3` before implementation/results** and remains unchanged. It compares PLAIN, EVIDENCE_ONLY, MECHANISM_ONLY and HYBRID using a common eligible pool and equal ceilings. The first real comparison uses prospective **V002**, frozen in `a5bba7f`, with explicit actual-attempt, invocation, effort, token and context accounting. Use the [frozen package and commands](first_comparison_v002/README.md); archived operator cards are excluded. Equal configured ceilings alone never establish equal actual effort.

`blind STORE --plain ... --evidence ... --mechanism ... --hybrid ... --salt-file private-salt.json` refuses incomplete or unequal-budget comparisons and exports a common reviewer packet plus a hash-sealed private key. Give only the packet to the reviewer. `evaluate-blind packet.json key.json --judgments human-judgments.json --states condition-paths.json` validates labels and can compare Jev separately against independent human labels, mechanical checks and critic answers. Without judgments it reports every missing reviewer. Blinding is partial and procedural; content can reveal the lane and the same owner may operate and review.

Nine frozen negative controls cover generic themes, paraphrases, unsupported relationships, fabricated citations, bad historical timing, malformed chains, unfalsifiability, low novelty and coherent speculation. Their automatic results are software checks, not human semantic labels. Substantive coherence, external novelty, false rejection rates and research-worthy handoffs require independent review. Brier values use actual distributions only where binary human labels exist; confidence is not ground truth or evidence of calibration. No significance or model superiority follows from this small harness.

`learning-export STORE` preserves initial cards/features, model/prompt provenance, attempts/errors/costs, review and selection histories, immutable revisions and later human outcome **references**. NOT_INVESTIGATED, SOURCE_BLOCKED, MECHANISM_FALSIFIED, MEASURABLE, M_PASSED, H and statistical results remain distinct. Nothing trains or adapts. [Detailed contract](future_learning.md).

## Validation and limits

```powershell
python -m unittest discover -s tests/opportunity_scout -v
python -m src.research.opportunity_scout validate .research/opportunity_scout/operator-example
```

The acceptance suite passes **66 Scout tests and 84 existing Discovery Lab/Graph regressions**, zero skipped. These establish software behavior, not economic findings. See [acceptance validation](acceptance_validation.json); the older [50-test validation record](validation.json) is preserved historically.

The real four-condition human comparison has not run. No external novelty search, original-source acquisition, human M/H decision or live model API verification is claimed. Ollama/Jev adapters are contract-tested; operator imports run end to end. The current Codex-authored examples are speculative and unreviewed. A future separately authorised investigation, and actual independent labels, are needed to assess research usefulness. The dashboard branch and all pilot branches remain separate.
