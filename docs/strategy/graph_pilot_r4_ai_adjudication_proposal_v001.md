# Graph Pilot R4: two-model AI adjudication variant (PROPOSED, version 001)

> **PROPOSED — NOT REGISTERED — NO EXPERIMENTAL AUTHORITY.**
> - R4 is NOT_RUN. It is recommended to be paused (PR #12).
> - Nothing here authorises a model call, hosted-model use, source retrieval, packet, review or activation.
> - The human dual-adjudication design (Phase B, [reviewer guide](graph_pilot_r4_reviewer_guide_v001.md)) is unchanged and remains the registered-ready design.
> - This variant is a separate path, and AI outputs are never human judgments.

## 1. What this changes, and what it does not

| Unchanged | New, proposed |
|---|---|
| Phase B human review: `adjudications-R.jsonl`, `warning-usefulness-R.jsonl`, `adjudication-seal-R.json`, assistant names refused, conformance needing two human seals | A separate AI-review path, `src/research/graph/ai_review.py`, with its own files (`ai-review-*.json`, `ai-cross-review-*.json`, their seals, `ai-reconciliation`) |
| `pilot report`, the cohort and conformance rules | An AI-reviewed packet never conforms under the human rules. `pilot report` will list it as non-conforming (no human seals). AI results come only from `pilot ai-reconcile`, labelled AI-ADJUDICATED |
| R1–R3 records, results and classifications; persisted stops; Measurement Gate M | — |
| Blinding (`pilot blind`, `realias`, `leak-scan`) and the evidence pack (runbook Stage 4) | The package is built *from* the leak-scanned `blind_v2.json`; nothing upstream changes |

**Implementation pin.** Adding `ai_review.py` and its CLI commands grows the pinned implementation closure from 38 to 39 files and changes its digest. No snapshot exists, so nothing breaks. An activation would record the new values, as runbook Stage 0a already requires.

## 2. The workflow

**Roles.**

- The **operator** is a named human. They run each model session, save its raw output privately, store the model's JSON answer verbatim, record provenance and seal.
- The operator never edits model content. A failed answer is preserved as a failed attempt.
- No reviewer model ever sees the arms, the keys, the other model's answer before both are sealed, or unnecessary historical results.

| Stage | Who | What | Command |
|---|---|---|---|
| 0. Package | Blinding preparer | From the leak-scanned `blind_v2.json`, plus the content-addressed evidence pack, build one package for both models | `pilot ai-package <P>/blind_v2.json --evidence-dir <pack> --out <P>/ai/ --own-from <P>/blind.json` |
| A1. Primary review | Operator, separately for each model | Send the [reviewer instructions](graph_pilot_r4_ai_review/stage_a_reviewer_prompt_v001.md), the [checklist](graph_pilot_r4_ai_review/review_checklist_v001.md) and the package files (`package.json`, `items.md`, `response_template.json`, `evidence/`) **unchanged**. Slot A is the GPT reviewer; slot B is the Claude reviewer | — |
| A2. Store | Operator | Save the raw output privately (ignored `data/raw/…`). Extract the single JSON block verbatim into `review`. Add operator-recorded `provenance`. Check it | `pilot ai-review-check <P>/ai <P>/ai/ai-review-A.json` |
| A3. Seal | Operator | Seal each valid answer, once | `pilot ai-review-seal <P>/ai --stage primary --slot A --by "<name>"` |
| A4. Reveal | Operator | Commit **both seals first**, then both answers in a later commit (`stage_order` checks this) | git |
| B1. Cross inputs | Operator | After both primary seals: the two frozen answers as auditors receive them. Model answers only; provenance withheld | `pilot ai-cross-inputs <P>/ai --out <P>/ai/cross-in/` |
| B2. Cross-review | Operator, separately for each model | Send the [cross-review instructions](graph_pilot_r4_ai_review/stage_b_cross_review_prompt_v001.md), the checklist, the package, `review_A.json`, `review_B.json` and `cross_review_template.json`. Each model audits both answers, including its own | — |
| B3. Store, seal, reveal | Operator | As A2–A4, with `--stage cross` | `pilot ai-review-seal <P>/ai --stage cross --slot A --by "<name>"` |
| C. Reconcile | Anyone | Deterministic item-level reconciliation | `pilot ai-reconcile <P>/ai --markdown <P>/ai/ai-reconciliation.md` |

**Unblinding** for any arm-level comparison follows only after Stage C, using the existing key procedure. **Arm-level metrics from AI labels are deliberately not implemented** (section 8).

**Provenance** (operator-recorded; validated; carried into seals and reconciliation):

| Field | Content |
|---|---|
| `reviewer_kind` | Always `AI_MODEL` |
| `product` | For example "ChatGPT Deep Research" |
| `model_identifier` | Exactly as displayed or returned, else `UNKNOWN` |
| `mode` | `EVIDENCE_PACK_ONLY` or `BROWSING_ALLOWED` |
| `prompt_sha256` | Must equal the frozen texts in the package |
| `run_started_utc`, `run_finished_utc` | Run times |
| `usage` | Tokens, credits or quota, else `UNKNOWN` |
| `resources` | Plan, limits and tools enabled, else `UNKNOWN` |
| `conversation_reference` | Private session reference, else `UNKNOWN` |
| `raw_output_sha256` | Hash of the saved raw output |
| `run_by` | The human operator. Assistant names are refused |

## 3. Frozen reviewer texts (send unchanged)

| File | Purpose | Deliverable |
|---|---|---|
| [`review_checklist_v001.md`](graph_pilot_r4_ai_review/review_checklist_v001.md) | The checklist, identical for both models | 1 |
| [`stage_a_reviewer_prompt_v001.md`](graph_pilot_r4_ai_review/stage_a_reviewer_prompt_v001.md) | Neutral reviewer instructions | 2 |
| [`primary_answer_template_v001.json`](graph_pilot_r4_ai_review/primary_answer_template_v001.json) | Structured answer template. Illustrative; the package contains the exact one for its items | 3 |
| [`stage_b_cross_review_prompt_v001.md`](graph_pilot_r4_ai_review/stage_b_cross_review_prompt_v001.md) and [`cross_review_template_v001.json`](graph_pilot_r4_ai_review/cross_review_template_v001.json) | Cross-review instructions and template | 4 |

**Properties** (tested):

- the texts pass the export leak scan, so they contain no arm, tool or method words;
- the checklist names every label and field the validator accepts;
- the templates equal the validator's generator;
- the package records each text's sha256, and every answer must cite those hashes.

**Criteria.** The checklist defines `CONFIRMED`, `FALSE`, `TRIVIAL`, `PLAUSIBLE_UNVERIFIED` and `UNKNOWN`. It defines economic meaning separately, and usefulness separately for warnings. It requires exact quotes or exact locations, treats confidence as non-evidence, and forbids invented sources, identifiers, relationships and economic effects.

**Mapping to the human vocabulary** (for comparison only; never merged into human logs):

| AI label | Human label |
|---|---|
| `CONFIRMED` | `CONFIRMED_AGAINST_ORIGINALS` |
| `FALSE` | `REJECTED_FALSE` |
| `TRIVIAL` | `REJECTED_TRIVIAL` |
| `PLAUSIBLE_UNVERIFIED` | Same |
| `UNKNOWN` | **No human counterpart.** The human guide folds insufficient evidence into `PLAUSIBLE_UNVERIFIED`. `UNKNOWN` is used only when an item cannot be assessed at all, and is never silently mapped |

## 4. Reconciliation (Stage C, deterministic)

**Mechanical evidence check.** Each support entry is checked against the package file:

| Check | Result |
|---|---|
| Quote, text formats (JSON, HTML with tags stripped, plain text) | Whitespace- and case-normalised containment: `FOUND` or `NOT_FOUND` |
| JSON pointer location | Must resolve |
| PDFs, archives, images, missing files | `UNVERIFIABLE` |

Per answer and item, the verification is:

- `VERIFIED`: every entry `FOUND`;
- `NOT_FOUND`: any entry `NOT_FOUND`;
- `UNVERIFIABLE`: anything else;
- `NO_SUPPORT`: no entries.

A support entry citing a file the item does not cite is **refused at validation**.

**Labels** (the cross-review never changes one):

| Condition | Economic label (CONNECTION) | Usefulness label (warnings, avoided repeats) |
|---|---|---|
| The two answers differ | `AI_UNRESOLVED_DISAGREEMENT` | `AI_UNRESOLVED_DISAGREEMENT` |
| Same, and either has a `NOT_FOUND` quote | `AI_AGREED_<O>_QUOTE_NOT_FOUND` | `AI_AGREED_<U>_QUOTE_NOT_FOUND` |
| Same `CONFIRMED`/`FALSE`, but not both `VERIFIED` | `AI_AGREED_<O>_NOT_MACHINE_VERIFIED` | Same rule for `USEFUL_LESSON_REUSED` |
| Same, otherwise | `AI_AGREED_<O>` | `AI_AGREED_<U>` |

- **Meaning** is reconciled separately: `AI_AGREED_<M>` or `AI_UNRESOLVED_DISAGREEMENT`.
- **AI-verified economic connection** = `AI_AGREED_CONFIRMED` **and** `AI_AGREED_MEANINGFUL`.
- **Robust** additionally requires all of:
  - both cross-reviews present;
  - neither auditor reports `UNSUPPORTED`, `FACTUAL_ERROR`, `MISQUOTE`, `UNSUPPORTED_CONCLUSION` or `INVENTED_CONTENT` against either answer;
  - two distinct model identifiers;
  - neither primary answer had access outside the package.
- **Disputed items stay disputed.** There is no third reading, no confidence weighting and no auditor arbitration. The variant registers no separate resolution mechanism.
- **Reported, never used:** confidence, self-audit (each auditor's own answer is marked), integrity flags, missed evidence and model identifiers.

## 5. Evidence-pack-only versus unrestricted Deep Research browsing

| | Evidence-pack-only (recommended) | Browsing (Deep Research default) |
|---|---|---|
| Inputs | Exactly the package; identical for both models | The package plus the open web, different for each run |
| Blinding | Preserved, given leak-scanned items | **At risk.** This repository is **public**: protocol documents, R3 results and adjudications, PR text and anything pushed during R4 (exports, packages, answers, arm branches) are findable |
| Independence | Neither model can see the other's answer | Neither can see the other *only if* nothing is pushed or posted before both seals |
| Fabrication | Every citation is checkable against the package | Outside sources are not in the package, so their quotes cannot be machine-verified |
| Reproducibility | Same package, same texts and hashes | Web content changes; searches are unrecorded |
| Enforcement | Instructions plus declared outside sources. **Not technically enforceable** in a hosted product that browses by design | — |

**Recommendations:**

- **Both primary reviewers evidence-pack-only.** For the GPT reviewer, prefer a mode with browsing disabled. If Deep Research must browse, record `BROWSING_ALLOWED`. The reconciliation then marks that reviewer's answers potentially unblinded, and nothing they touch counts as robust.
- **Keep R4 artefacts off the public remote until Stage C.** That covers exports, packages, answers, seals and arm branches; commit locally. Reveal order needs commits, not pushes. Making the repository private is an account setting: your decision, not taken here.

## 6. Prompt-injection risks

**Sources:**

- evidence documents, which are third-party text;
- item text, which arm sessions wrote. If D1 chooses AI arms, that text is model-generated;
- at the cross stage, the other model's answer.

**Mitigations:**

- the frozen "data, not instructions" rule in all texts;
- deterministic integrity flags. The builder flags instruction-like text in items and evidence and never removes it (evidence is immutable);
- refusal of any leak in items, rendered items or texts;
- quote verification;
- structured answers validated against a closed schema, so no free-form label is accepted;
- the human operator stores outputs. No model has write access to the repository.

**Residual risk.** A subtly persuasive document cannot be detected mechanically. Two models from different vendors reduce correlated manipulation but do not remove it. The flags and the cross-review's `integrity_notes` are the evidence.

## 7. Preserved open issues (from PR #12, not resolved here)

- **Classification.** The feasibility audit classifies R4 `INCONCLUSIVE_MORE_OFFLINE_EVIDENCE_NEEDED` and recommends a **pause**. This variant does not lift the pause.
- **P1 (observation).** No documented route with confirmed terms:
  - CAISO E2 is ambiguous (copying prohibited except as authorised; a public-use paragraph applies only to materials "freely available for public use"), and price reports are excluded;
  - EIA and ERCOT need keys;
  - FDIC financial data is excluded as outcome-bearing.
- **P2 (relationship).** GLEIF only, under F1(a).
- **P3 (event).** CPSC, then FDIC history. History outcome fields are UNK; the population of CPSC `CompanyID` is UNK.
- **Uploading evidence.** Sending evidence to hosted models publishes it to an external service. Publisher terms, including CAISO's, must permit that use, as well as retrieval.

## 8. What AI-only R4 could and could not conclude

**It could report**, per packet:

- how often two different models, working blind and from identical evidence, agree;
- which agreed confirmations survive mechanical quote checks and two audits;
- the review burden.

After unblinding, a descriptive arm comparison *of AI labels* would be possible. **It is not built.** Building it would extend `pilot report` with an AI-adjudicated cohort, and that needs your decision first.

**It could not report:**

- a human-adjudicated R4 classification;
- independence in the human sense: the models share training data and public knowledge, and may make correlated errors;
- statistical significance or an investment claim.

If D1 also uses AI arms, the loop becomes AI-generated research evaluated by AI. That measures inter-model agreement on AI work, not research value to a human researcher.

## 9. Assessment: is AI-only R4 scientifically worthwhile?

**Not on its own, and not now.** It removes the reviewer-recruitment bottleneck, and adds something genuinely useful: mechanical quote verification and structured, auditable disagreement. But four things stand against it:

1. **Sources remain the binding constraint.** R4 cannot form three comparable pairs with confidence (PR #12), and AI review does not help form packets.
2. **The measuring instrument is weaker.** Two AI reviewers plus AI audits are not independent expert adjudication. With AI arms, the result is circular.
3. **Browsing reviewers on a public repository** put blinding at risk unless the run is evidence-pack-only and nothing is pushed.
4. **R3's lesson.** AI-assisted, potentially unblinded adjudication was already R3's main limitation. AI-only review makes that limitation the design.

**What would be worthwhile, if you want it:** a small **instrument check** before any decision to unpause. Run this workflow, evidence-pack-only, on a fixed set of already-closed items, to measure inter-model agreement and the quote-verification failure rate. That would also be a new hosted-model activity, needing your separate authorisation. Its contamination limits would have to be stated: R3 items were adjudicated with AI assistance, and the R3 material is public.

**Recommendation:** keep R4 paused. Approve this variant only as a registered, explicitly labelled secondary design, and only if:

- the source questions resolve;
- both primary reviewers are evidence-pack-only;
- its labels are never presented as human adjudication or as the R4 primary classification.

## 10. Owner approval checklist (for any later activation)

- [ ] Decide whether R4 is unpaused at all (PR #12). Resolve its five offline source items.
- [ ] Register this variant (v001) and the sha256 of the three frozen texts. Note that it is secondary to, and does not replace, the human design.
- [ ] Register the exact products and model identifiers for slot A (GPT) and slot B (Claude), the account context, usage and resource limits, the human operator, and the stopping arrangements.
- [ ] Register the attempts policy. Suggested: one primary attempt per slot; one re-run only after a technical failure (no output, or truncated output), with every attempt preserved and counted. Never a re-run because of the content of an answer.
- [ ] Choose evidence-pack-only or browsing for each slot (recommended: evidence-pack-only for both).
- [ ] Decide on keeping R4 artefacts off the public remote until Stage C, or on making the repository private.
- [ ] Confirm that publisher terms permit uploading each evidence file to the two hosted services.
- [ ] Decide what AI labels are used for: item-level reporting only, or a future, separately approved AI-adjudicated cohort in `pilot report`.
- [ ] Decide D1. If arms are AI, accept the circularity stated in section 8, or reject the variant.
- [ ] Confirm that the AI labels and every summary of them carry the AI-ADJUDICATED banner, and never appear as human judgments.

## 11. Code and tests (offline)

`src/research/graph/ai_review.py` and five `pilot ai-*` commands:

- the package builder (leak scan, evidence hash checks, missing-evidence records, integrity flags, templates);
- validators for primary answers and cross-reviews (closed schema, item-evidence-only support, no relabelling in audits);
- once-only seals;
- the git stage-order check;
- deterministic reconciliation, with a Markdown table.

The ten tests in `tests/test_graph.py` (`GraphAIReviewTests`) use synthetic packets in temporary directories. There are no network or model calls, and no human logs are written.
