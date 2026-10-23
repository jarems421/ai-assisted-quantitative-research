# Jev shadow review and post-generation readiness (v001)

> **Offline readiness only.**
> - No Jev or other hosted call was made. No credential was read, and no experiment was activated.
> - Every card, Jev answer and label in the tests is a `SYNTHETIC_FIXTURE`, not real model output or human judgment.
> - Jev is a **shadow reviewer**. It never routes, rejects, certifies evidence or economic truth, or grants research authority.
> - Frozen V001–V004 designs and the N1 work are unchanged. The new code lives in `src/research/opportunity_scout/post_generation/`, outside the V004 implementation closure (which hashes every top-level `opportunity_scout/*.py`); no top-level Scout module changed.

**Purpose.** When genuine Scout ideas exist, the owner can:

1. collect independent labels for them;
2. compare a separately authorised Jev shadow run against those labels; and
3. take a human-approved idea into Discovery Lab without new engineering.

## 1. Built versus missing

**Status key.** *Built, fixture-tested*: implemented and exercised only on synthetic fixtures. *External*: needs something outside this repository (an authorisation, a person, a live response).

### Jev integration

| Capability | Status | Notes |
|---|---|---|
| `shadow-request STORE IDEA`: System One request (`model`, `state`, five `choice` questions with yes/no/unsure criteria) | Built, fixture-tested | Matches the documented request shape (public docs re-read 2026-10-23). **Never sent live** |
| Model pin `jev-1.13.0` | **Unverified** | The docs' examples use `jev-latest` and `jev-preview`; available names come from `GET /v1/models`, which is an API call needing authorisation. The response `model` may differ from the request: now reported |
| Response validation (`shadow-import`) | Built, fixture-tested | Exactly the documented fields: `model`, `answers.<q>.{type, choice, probabilities, confidence}`, `usage.{input_tokens, output_tokens}` as integers. Probabilities must sum to 1 and `choice` must be their argmax |
| Strictness | Deliberate | The docs do not say whether extra fields can appear. An undocumented field is **refused, never stripped**: the response stays unimported and is kept as received |
| Cost | Correctly `UNKNOWN` | System One documents no price or currency field ("output tokens are currently free"). Cost stays `UNKNOWN` unless separately evidenced |
| `JevShadowClient` | Built, never used live | Refuses without a payload-specific owner approval and a `PUBLIC_APPROVED`/`SYNTHETIC_APPROVED` classification; reads the key only after that |
| Transport label for a client-made call | Inconsistent | The importer refuses `OWNER_AUTHORISED_HTTP`, so a response fetched by `JevShadowClient` cannot be recorded under that label. For the first run, use the operator path (section 3) and import as `IMPORTED_NOT_CALLED`. Not changed here |
| `python -m src.research.opportunity_scout.post_generation import-response STORE IDEA RESPONSE.json` | **New**, fixture-tested | Wraps a saved response file unchanged; computes the request hash; cost and currency default to `UNKNOWN`. Removes hand-editing of judgments into records |
| Four-condition Jev metrics (`evaluate-blind --states`) | Built, fixture-tested | Agreement and binary Brier only, and only via the frozen comparison |
| Non-comparative label packet, labels and comparison (`post_generation label-packet`, `post_generation compare`) | **New**, fixture-tested | Section 2 |
| Real Jev responses, API key, per-payload owner approval, independent labellers | **External** | — |

### Scout after generation

| Step | Status | Notes |
|---|---|---|
| Import generated output (`import-response`, `run --responses`) | Built, tested | Schema and citations checked; invalid attempts retained |
| Validation and duplicate proximity (`triage`, `card`) | Built, tested | Exact core duplicates and possible mechanism duplicates are flagged for human review, never auto-merged |
| Human review, feasibility (`SCOUT_READY_V002`), READY with `approved_handoff` | Built, tested | READY needs a human feasibility assessment of the exact next-step question and an identifiable publisher route |
| Shortlist (`shortlist`) | Built, tested | Diversity niches; not required for a handoff |
| Handoff (`handoff STORE IDEA`) → `DISCOVERY_LAB_STARTING_PROPOSAL_V001` | Built, tested | Proposal only; lists unfilled Discovery Lab fields; certifies nothing |
| The same trace in an exploratory (non-synthetic) batch | Probed, not committed | It works end to end. A committed test would need fabricated HUMAN records, so the committed trace uses synthetic stand-ins |
| Frozen four-condition human evaluation (`blind`, `blind-evaluation`, `evaluate-blind`) | Built, tested | **Refuses** unless every condition has its full cards and completed attempts |
| Discovery Lab intake of a handoff | **No code, by design** | A live campaign needs a separate owner document (`AGENTS.md`). Section 4 gives the manual mapping |

### Concrete gaps found and fixed (offline, narrow)

1. **No label path for incomplete generation.** V004 expects invalid or missing outputs (V003 stopped on its first attempt). The only human-label path refused anything short of four complete conditions, so the first genuine ideas could not be labelled, and Jev could not be compared at all.
   - **Fix:** a separate, explicitly non-comparative label packet over every current card in any archives. The frozen comparison is unchanged and remains the only basis for condition comparisons.
2. **Jev metrics too thin.** The existing metrics report agreement and binary Brier only.
   - **Fix:** the new report adds abstention, a three-way confusion matrix, disagreement types, a 0.25 reference Brier and human–human agreement. It adds problem flags beyond the one existing mechanical check, the returned model against the requested one, tokens, unknown cost and every missing record.
3. **Importing required hand-copying the response into a record.** **Fix:** `post_generation import-response` reads the saved file unchanged.

## 2. The offline shadow-evaluation workflow

| # | Step | Command | Guarantees |
|---|---|---|---|
| 1 | Receive frozen ideas | (generation import; N1/V004 is Codex's) | Cards are immutable versions; invalid attempts retained |
| 2 | Label packet | `python -m src.research.opportunity_scout.post_generation label-packet --store NAME=PATH … --salt-file salt.json --out <new dir>` | Every current card, labelled or not, with or without Jev. Generator metadata, lanes, ids and **all Jev output removed**. Private key hash-seals the mapping and the fixture class. `comparative_eligible: false` |
| 3 | Independent labels | Labellers fill `label_template` per card | One record per reviewer and card. `saw_jev_output: false` and `independent_of_generation: true` are required. HUMAN only in real batches (SYNTHETIC_FIXTURE only in synthetic ones); assistant or model names refused. `unsure` allowed; real minutes or `UNKNOWN` |
| 4 | Jev requests | `shadow-request STORE IDEA` per card | Exact payload and `payload_sha256` for the owner's approval |
| 5 | Jev responses | `python -m src.research.opportunity_scout.post_generation import-response STORE IDEA response.json` | Stored unchanged and bound to the request hash. Refused responses are left unimported, never repaired. Repeated imports are kept; the comparison uses the **earliest** |
| 6 | Compare | `python -m src.research.opportunity_scout.post_generation compare --store NAME=PATH … --packet P --key K --labels L` | Descriptive report (below) |
| 7 | Report | — | Include `missing`, `usage_and_cost` and `interpretation` verbatim. No calibration, significance or routing claim |

**Report contents per question:**

- Pairs compared, agreement, and decisive agreement (both answers yes or no).
- Disagreement split: opposite decisions; Jev abstained while the label decided; the label abstained while Jev decided.
- Jev and label abstention rates, and the full Jev-by-label confusion matrix.
- Binary Brier on P(yes) where the label is yes or no, with the constant-0.5 reference of 0.25.
- Human–human agreement where two labellers answered the same card.
- Problem flags, where the problem answer is `no`, except `yes` for `certainty_exceeds_evidence`:
  - flagged by the labels;
  - also flagged by Jev;
  - missed by Jev;
  - Jev false alarms, against an opposite or unsure label;
  - for `falsifiable` only (the one question with a mechanical check), Jev flags the structural check did not raise.

**Not computed:**

- Three-class Brier: `unsure` is abstention, not an outcome.
- Any composite score.
- Any condition or method comparison.

**Always reported:** cards without a Jev answer, cards without labels, repeated Jev records, cards revised since the packet, label minutes known or unknown, returned model names, tokens, and the number of records with unknown cost.

## 3. Operator checklist: first separately authorised Jev shadow comparison

**Before any request.**

1. The owner records an authorisation naming:
   - the archives and the exact card ids and versions;
   - each `payload_sha256` from `shadow-request`;
   - the classification and an explicit decision to send these unpublished cards to TypeSafe (an external service: sending publishes them to it);
   - the person and account, a token or cost ceiling, the model name, and "one request per payload, no retry on content".
2. Resolve the model pin: either the owner accepts `jev-1.13.0` as documented in the repository, or separately authorises one `GET /v1/models`. Record which.
3. Build the label packet (step 2). Give labellers **only** the packet: not the key, the archives or any Jev output.
4. Collect every label and commit it locally **before** any Jev response is imported or viewed. The import date does not prove label independence, so this ordering is procedural.

**Running Jev (outside Scout).**

5. Send each frozen payload unchanged, once. Save the response body exactly as received in a private location. Note the usage shown; leave cost `UNKNOWN` unless an invoice line exists.
6. On an HTTP error, timeout or truncated body, stop and record it. Do not resend without the owner's decision.

**Afterwards.**

7. Run `post_generation import-response` for each response. Keep any refused response file as it is, and report it.
8. Run `post_generation compare`, and publish the report with its `missing` and `interpretation` sections.
9. Jev answers are never used to route, reject, shortlist or approve. The human review records stay the only routing.

## 4. Shortest path: genuine idea to a human-approved Discovery Lab investigation

| # | Who | Step |
|---|---|---|
| 1 | Codex / operator | Generation imported into a Scout archive (outside this task) |
| 2 | Software | `triage STORE`: structural validation and duplicate proximity. Inspect with `card STORE IDEA` |
| 3 | Human | Resolve duplicates or structural warnings with `review` (for example `reason_type: DUPLICATE`), or `revise` |
| 4 | Human | `feasibility STORE f.json` (`SCOUT_READY_V002`) for the card's exact `next_step.question` and an identifiable publisher route |
| 5 | Human | `review STORE r.json`: `READY` with `approved_handoff: true` for that exact version |
| 6 | Software | `handoff STORE IDEA` writes the starting proposal (`shortlist` is optional) |
| 7 | **Owner** | A new owner document authorising a bounded live Discovery Lab campaign: question, method, analyst hours, source starts, bytes, acquisition yes or no |
| 8 | Human | Draft the campaign (`python -m src.research.discovery template campaign`) and `init`. Map the fields as below |
| 9 | Human | Discovery Lab proper: source passports and original-source verification, observations and relationships, a frozen claim, the mechanical checklist, and a **human Measurement Gate M review**. Nothing from Scout or Jev substitutes for any of these |

**Campaign fields at step 8:**

- `method` = the handoff's `discovery_method_proposed`;
- `question` = the card's `next_step.question`;
- `authority` = the step 7 document;
- `fixture` = `LIVE`;
- `notes` cite `opportunity_card_sha256` and the handoff file hash.

Jev can run in parallel at any point. It is never a gate.

## 5. GO/NO-GO

**GO for offline evaluation readiness.**

- The software path from generated cards to independent labels, a Jev shadow comparison and a human-approved handoff is complete and tested on synthetic fixtures.
- That includes the incomplete-generation case the frozen comparison refuses.

**Not GO for anything live.** The first real comparison still needs, outside the software:

- genuine generated ideas;
- the owner's per-payload Jev authorisation, including consent to send unpublished cards to TypeSafe;
- a decision on the model pin;
- at least one independent human labeller, two for a human–human baseline.

Results on a first small set describe consistency only. They establish no calibration, significance or research benefit.
