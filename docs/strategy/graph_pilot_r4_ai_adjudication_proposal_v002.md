# Graph Pilot R4: two-model AI adjudication variant (PROPOSED, version 002)

> **PROPOSED — NOT REGISTERED — NO EXPERIMENTAL AUTHORITY.**
> - R4 is NOT_RUN and remains paused (PR #12).
> - Nothing here authorises a model call, hosted-model use, source retrieval, packet, review or activation.
> - The human dual-adjudication design (Phase B) is unchanged and is never fed by this path.
> - AI outputs are model outputs: never human judgments, never established economic truth, never trading alpha.

Version 002 is an **assurance hardening** of [version 001](graph_pilot_r4_ai_adjudication_proposal_v001.md), which is kept unchanged as history. It follows an independent repository review of `src/research/graph/ai_review.py`. Every finding was re-checked against the merged code before it was changed (section 9).

The workflow, roles, frozen reviewer texts, the evidence-pack-only recommendation and the scientific assessment of v001 (its sections 3, 5, 7, 8 and 9) still apply. This document describes only what is new or changed.

## 1. What changed

| Area | v001 | v002 |
|---|---|---|
| Package identity | sha256 of `package.json` | sha256 of `package_manifest.json`, which binds the bytes of every reviewer-facing artifact |
| What a model received | Not recorded | `ai-bundle-<stage>-<slot>.json`: the hash of every supplied file, compared by content |
| Raw model output | `raw_output_sha256` format check only | Raw bytes kept in a private content-addressed store; deterministic extraction must reproduce the stored answer |
| Cross-review identity | Not compared with the primary slot | Cross-review X must name the same product and model identifier as primary X |
| `robust` | Blocked only by `UNSUPPORTED` or a serious issue | Replaced by `ai_audit_supported`: both auditors must find both answers `SUPPORTED` |
| Interpretation | `ai_verified_economic_connection` | Renamed `ai_agreed_documented_connection`, plus six separately reported assessment dimensions |
| Instruction-like text | Flagged; no effect on conformance | Flagged by severity; a named human disposes of every flag before Stage A; unresolved or confirmed flags withhold conformance |
| Synthetic provenance | Implicit | `provenance_class` on every answer; synthetic answers in a live package withhold conformance; reports carry a synthetic banner |

**Unchanged:** the model-facing texts and templates (`*_v001`, same hashes), the answer schema the models fill in, quote verification, label reconciliation, the git reveal order, zero-item support and the separation from human adjudication.

**Versions.** `GRAPH_AI_REVIEW_PACKAGE_V2`, `GRAPH_AI_REVIEW_MANIFEST_V1`, `GRAPH_AI_PRIMARY_REVIEW_V2`, `GRAPH_AI_CROSS_REVIEW_V2`, `GRAPH_AI_REVIEW_SEAL_V2`, `GRAPH_AI_RECONCILIATION_V2`, `GRAPH_AI_REVIEW_INPUT_BUNDLE_V1`, `GRAPH_AI_RAW_RESPONSE_RECORD_V1` and `GRAPH_AI_INJECTION_DISPOSITION_V1`.

No V1 package, answer, seal or reconciliation was ever produced: none exists in the repository, and R4 never ran. V1 documents are therefore **refused with an explicit message**, never silently reinterpreted under V2.

## 2. Workflow (changed steps in bold)

| Stage | Who | What | Command |
|---|---|---|---|
| 0. Package | Blinding preparer | Build the package and its manifest from `blind_v2.json` and the evidence pack | `pilot ai-package <P>/blind_v2.json --evidence-dir <pack> --out <P>/ai/ --own-from <P>/blind.json` |
| **0b. Flags** | **A named human** | **Read every integrity flag and dispose of each one, once, before Stage A. Commit the record before any primary answer** | `pilot ai-injection-flags <P>/ai`, then `pilot ai-injection-dispose <P>/ai --decision ID=DISPOSITION=REASON … --by "<name>"` |
| **A0. Bundle** | **Operator, per model** | **Before the run, create the upload folder from the package and record it** (or record a folder you assembled yourself) | `pilot ai-bundle <P>/ai --stage primary --slot A --dir <upload> --write --by "<name>"` |
| A1. Primary review | Operator, per model | Supply exactly the bundle folder | — |
| **A2. Store** | **Operator** | **Record every attempt's raw response (failed ones too), then store the extracted JSON verbatim as `review`, citing that attempt and the bundle record** | `pilot ai-raw-record <P>/ai --stage primary --slot A --raw <file> --raw-store <private> --by "<name>"`, then `pilot ai-review-check <P>/ai <answer> --raw-store <private>` |
| **A3. Seal** | **Operator** | **Seal once. Refused unless the raw response verifies** | `pilot ai-review-seal <P>/ai --stage primary --slot A --by "<name>" --raw-store <private>` |
| A4. Reveal | Operator | Commit both seals first, then both answers | git |
| B1. Cross inputs | Operator | After both primary seals | `pilot ai-cross-inputs <P>/ai --out <dir>` |
| **B2–B3** | **Operator, per model** | **As A0–A4 with `--stage cross`; the Stage B bundle must also contain `review_A.json` and `review_B.json` with exactly the sealed bytes. Slot X must be run by the same model as primary X** | `pilot ai-bundle … --stage cross …` etc. |
| C. Reconcile | Operator (holds the private store) | Deterministic reconciliation | `pilot ai-reconcile <P>/ai --raw-store <private> --markdown <P>/ai/ai-reconciliation.md` |

Bundle records, raw-response records and dispositions are operator-side files in the package folder. They are never supplied to a model.

## 3. Package manifest and input bundles

**Manifest** (`package_manifest.json`, written last):

- It lists the sha256 and size of every reviewer-facing artifact:
  - `package.json`, `items.md`, `response_template.json`, `cross_review_template.json`;
  - the three frozen texts;
  - every evidence file in the package.
- It also lists the exact Stage A and Stage B input lists. Stage A gets the response template and the Stage A prompt; Stage B gets the cross template, the Stage B prompt, and the two derived `review_<slot>.json` files.
- It does not list itself. The package identity is the manifest's own hash, so nothing hashes itself.

**Loading.** `load_package` refuses a package when:

- any listed file is missing or changed;
- the manifest lists more or fewer artifacts than the package has;
- the stage lists are not the deterministic ones;
- `items.md` or a template is not the deterministic rendering of `package.json`. This catches a consistent edit in which both the file and its manifest entry were re-hashed.

Answers and seals cite `manifest_sha256`.

**Bundles.** `ai-bundle` hashes every file actually present in the folder supplied to the model. Validation recomputes the expected bytes from the package (and, for Stage B, from the sealed primary answers), then compares **by content**, not by name. Each problem is listed:

- `MISSING`: an expected file was not supplied (a renamed file shows as `MISSING` plus `EXTRA_FILE_SUPPLIED`);
- `EXTRA_FILE_SUPPLIED`: for example, the other model's answer in a Stage A bundle;
- `BYTES_DIFFER`: altered, substituted or swapped content.

A bundle recorded after the run started is `RECORDED_AFTER_RUN_START`. An answer citing a different bundle record is `NOT_CITED`. The two primary bundles must be the identical Stage A package (`PRIMARY_BUNDLES_DIFFER`).

A mismatched bundle is preserved and the answer can still be sealed for diagnostics. The result is non-conforming.

## 4. Raw model responses

**Private store.**

- `ai-raw-record` copies the response bytes unchanged into a content-addressed store (file name = sha256).
- It refuses a store that git would track: one inside a working tree and not ignored, or one with tracked files. Use an ignored path such as `data/raw/…`, or a folder outside the repository.

**Public record** (`ai-raw-<stage>-<slot>-<NNN>.json`):

- It contains attempt number, raw hash and size, extraction rule and status, the canonical hash of the extracted object, receipt and record times, and the operator.
- It contains **no response content**.
- Attempts are numbered contiguously and never overwritten. Empty, truncated and unparseable responses are recorded like any other.

**Extraction rule `SINGLE_FENCED_JSON_BLOCK_AT_END_V1`.** This is what the frozen prompts already ask for:

- the bytes are UTF-8;
- there is exactly one fenced block (an opening ```` ``` ```` line with no info string or `json`, and a closing ```` ``` ```` line);
- only whitespace follows it;
- the content is strict JSON (no duplicate keys, no NaN or Infinity) and an object.

Nothing is trimmed, repaired or rewritten. The statuses are `EXTRACTED`, `EMPTY`, `NOT_UTF8`, `NO_CODE_BLOCK`, `MULTIPLE_CODE_BLOCKS`, `UNCLOSED_CODE_BLOCK`, `NOT_A_JSON_BLOCK`, `BLOCK_NOT_AT_END`, `INVALID_JSON` and `NOT_AN_OBJECT`.

**Verification** (`raw` status of an answer):

| Status | Meaning |
|---|---|
| `VERIFIED` | The cited record is the latest attempt; the raw bytes are in the store with that hash; re-extraction gives exactly the stored `review` |
| `RECORD_MISSING`, `RECORD_MISMATCH` | No record for the cited attempt, or record and answer cite different bytes or packages (a fabricated hash lands here) |
| `NOT_LATEST_ATTEMPT`, `RECORDS_NOT_CONTIGUOUS` | An older attempt is cited, or an attempt record is missing or renamed |
| `RAW_NOT_AVAILABLE`, `RAW_HASH_MISMATCH` | Store not supplied or file absent; stored bytes altered |
| `EXTRACTION_CHANGED`, `EXTRACTION_FAILED` | The record no longer matches re-extraction; the cited attempt has no extractable answer |
| `REVIEW_DIFFERS_FROM_RAW` | The stored `review` is not the extracted answer (it was edited) |

**Rules:**

- A seal is refused unless the status is `VERIFIED`. Reconciliation without the private store is never conforming.
- Attempts are reported as `SINGLE`, `TECHNICAL_RETRIES_ONLY` or `CONFLICTING`. `CONFLICTING` means an earlier attempt also yielded an extractable answer, so a re-run was not a technical failure. It withholds conformance, which implements v001's suggested attempts policy conservatively.

**Other provenance changes:**

- `conversation_reference` must be `UNKNOWN` or `sha256:<hash>` of the private reference, so session links never enter public files.
- Record `usage` and `resources` without account identifiers.
- `provenance_class` is `REAL_MODEL_RUN` or `SYNTHETIC_FIXTURE`.

## 5. Identity binding

For each slot, reconciliation compares the cross-review's `product` and `model_identifier` (exactly, after trimming whitespace) with the primary answer's sealed identity. A case change counts as a mismatch. Each slot's result is `MATCHED`, `MISMATCHED` or `UNAVAILABLE`.

| Condition | Reason |
|---|---|
| Cross-review X names another product or identifier than primary X (including swapped or identical cross models) | `CROSS_IDENTITY_MISMATCH_X` |
| Any primary or cross identifier or product is empty or `UNKNOWN` | `MODEL_IDENTITY_UNKNOWN_<PRIMARY|CROSS>_X` (an empty value is refused at validation) |
| The two primary identifiers are equal (ignoring case) | `MODEL_IDENTITY_NOT_DISTINCT` |

Mismatches are noted and the result keeps every diagnostic. **Identities remain operator attestations.** They are labelled `OPERATOR_ATTESTATION (not provider-corroborated)` unless provider evidence (for example a model identifier returned in API metadata) is separately archived and checked; this software does not do that. The owner's registration (v001 section 10) is the reference a human should compare them with.

## 6. Reconciliation V2

**Labels** are unchanged: `AI_AGREED_<O>` with quote suffixes, or `AI_UNRESOLVED_DISAGREEMENT`. Cross-reviews, confidence and a third reading never change a label.

**Six dimensions, reported separately per item** (`assessment`):

| Dimension | What it reports | What it does not mean |
|---|---|---|
| 1. File and quote integrity | Original files present; each answer's quote verification; whether both are character-exact | That the quoted text is true |
| 2. Identity and period join | What the export itself declares (shared document hash, identified entity, name-only entities, both ends dated); status `DECLARED_BY_EXPORT_NOT_CHECKED_BY_AI_REVIEW` | That the join is valid |
| 3. Documentary support | Model agreement that the documents support (`AI_AGREED_SUPPORTED_WITH_EXACT_QUOTES`) or contradict the claim; audits `ALL_FOUR_SUPPORTED`, `NOT_ALL_SUPPORTED` or `INCOMPLETE` | That the relationship exists in the world |
| 4. Model agreement on economic meaning | `AI_AGREED_MEANINGFUL`, etc. | Human or expert judgment |
| 5. Economic mechanism or causal inference | Always `NOT_ASSESSED_BY_THIS_INSTRUMENT` | — |
| 6. Independent real-world validation | Always `NONE` | — |

**Item flags:**

- **`ai_agreed_documented_connection`**: the same conditions as v001's `ai_verified_economic_connection`, renamed because "verified economic connection" overstated what two models agreeing on documents establishes. The conditions are: a CONNECTION item, `AI_AGREED_CONFIRMED` (both answers' quotes character-exact) and `AI_AGREED_MEANINGFUL`.
- **`ai_audit_supported`** (replaces `robust`). This is a documented connection where:
  - both auditors report `SUPPORTED` for both answers, with no serious issue;
  - every evidence file of the item is present;
  - the package result is conforming.

  `PARTLY_SUPPORTED`, `CANNOT_CHECK`, `UNSUPPORTED`, a missing auditor or a serious issue each block it. `audit_supported_conditions` reports the item-level conditions without the package gate.

The old names do not appear in V2 output (`label_versions` records the mapping). Counts are `ai_agreed_documented_connections` and `ai_audit_supported_connections`.

**Conformance gate** (all must hold; otherwise `conforming_counts` is `null` and no item is `ai_audit_supported`):

| Condition | Reason when it fails |
|---|---|
| Stage order `VERIFIED` (now also: any disposition committed strictly before both primary answers) | `STAGE_ORDER_NOT_COMMITTED`, `STAGE_ORDER_VIOLATED` |
| Both cross-reviews sealed and valid | `CROSS_REVIEW_X_UNAVAILABLE` |
| Known, distinct, bound identities | Section 5 |
| No browsing or declared outside source | `EXTERNAL_ACCESS_<STAGE>_X` |
| Raw responses verified, attempts not conflicting | `RAW_OUTPUT_<STATUS>_<STAGE>_X`, `RAW_ATTEMPTS_CONFLICTING_<STAGE>_X` |
| Input bundles verified and the primary bundles identical | `INPUT_BUNDLE_<STATUS>_<STAGE>_X`, `PRIMARY_BUNDLES_DIFFER` |
| No evidence missing | `EVIDENCE_MISSING_FROM_PACKAGE` |
| Every integrity flag disposed as harmless or not an instruction | `PROMPT_INJECTION_UNRESOLVED`, `PROMPT_INJECTION_CONFIRMED` |
| No synthetic-fixture answer in a live package | `SYNTHETIC_PROVENANCE_IN_LIVE_PACKAGE_<STAGE>_X` |

**Synthetic labelling.** Any `SYNTHETIC_FIXTURE` answer gives `evidence_class: SYNTHETIC_FIXTURE_ANSWERS` and a second banner. Real models reviewing synthetic items keep `package_fixture: SYNTHETIC`: that is calibration, never R4 evidence.

## 7. Prompt-injection boundary

**Detection.** Item text and the raw text of machine-checkable evidence are scanned after NFKC normalisation, removal of zero-width characters and collapsing of whitespace. Comments and attributes in HTML are included. Flags never change or remove any text.

| Severity | Patterns |
|---|---|
| `INSTRUCTION_ATTEMPT_SUSPECTED` | Override instructions ("ignore all prior instructions"); direct label requests ("mark this item as"); addressing the model ("note to the assessor", "you are now an evaluator"); asserting the correct label ("the correct classification here is", "reviewers should mark") |
| `AMBIGUOUS_INSTRUCTION_LIKE_TEXT` | Mentions of system prompts, prompt injection or jailbreaks; role prefixes such as `reviewer:` |

Formats that cannot be scanned (PDF, archives, images) are listed in `unscanned_evidence`. They are a reported limitation, not a flag.

**Disposition.** Before Stage A, a named human (assistant names are refused) reads each flag (`ai-injection-flags` shows the matched passages) and records, once:

- `HARMLESS_QUOTED_EXAMPLE`;
- `NOT_AN_INSTRUCTION`;
- `INSTRUCTION_ATTEMPT_CONFIRMED`; or
- `UNRESOLVED`.

Each disposition needs a stated reason.

| Result | Effect |
|---|---|
| No flags | `CLEAR` |
| Every flag disposed as harmless or not an instruction | `DISPOSED`; may conform |
| Any flag undisposed or `UNRESOLVED` | `PROMPT_INJECTION_UNRESOLVED`; withheld |
| Any `INSTRUCTION_ATTEMPT_CONFIRMED` | `PROMPT_INJECTION_CONFIRMED`; withheld for the whole package (conservative) |
| Disposition committed after a primary answer | `STAGE_ORDER_VIOLATED` |

**Limits.**

- Pattern matching does not detect every injection. The tests include a persuasive sentence that is deliberately not flagged.
- Models' own `integrity_notes` are reported in `integrity.model_integrity_notes`. They do not gate, because they arrive after the answers and cannot be disposed of prospectively.

## 8. Tests

`GraphAIReviewTests` in `tests/test_graph.py` now has **22 tests** (previously 13). They use synthetic packets in temporary directories and throwaway git repositories, with no network and no model calls. Every answer is labelled `SYNTHETIC_FIXTURE`, and the raw responses are local fixture bytes written by the test.

New adversarial coverage:

- **Identity.** Swapped, identical, unknown model and unknown product, other product, case-altered and empty identities.
- **Package.** An edit to each artifact category; missing files; substituted evidence; a missing or incomplete manifest; altered stage lists; consistent re-hashed edits to `items.md` and both templates; a V1 package.
- **Bundles.**
  - extra, altered, missing, substituted and renamed files;
  - the wrong stage template;
  - swapped Stage B review files and a mismatched primary bundle;
  - a bundle recorded late, and a citation of another bundle record.
- **Raw responses.**
  - 4 valid and 12 invalid extraction cases;
  - missing and altered stored bytes, a fabricated hash and an edited review (with the seal refused);
  - a tampered record;
  - a technical retry, conflicting attempts, a stale citation and a deleted attempt record;
  - a tracked versus an ignored store.
- **Audit support.** `PARTLY_SUPPORTED` and `CANNOT_CHECK` on own and other answers; `UNSUPPORTED`; `MISQUOTE`; combinations; a missing auditor.
- **Assessment.** The six dimensions, contradiction, disputed meaning, and no reuse of V1 names.
- **Injection.**
  - obvious, zero-width, full-width and HTML-comment examples, with an ambiguous harmless example and an undetected subtle one;
  - no, partial, unresolved, confirmed and harmless dispositions, and a late disposition;
  - an assistant disposer and an unknown flag.
- **Zero items.** A zero-item package conforms with zero counts.

## 9. Before and after: the verified defects

| # | Defect, as verified in merged code (`main` at `1be7d8f`) | After |
|---|---|---|
| 1 | `validate_cross` never compared the cross-review's product or identifier with the primary slot; `UNKNOWN` was checked only for primaries | Bound per slot; `UNKNOWN` checked for all four runs; mismatches recorded and withheld (section 5) |
| 2 | `load_package` checked texts and evidence only. `items.md` and both templates were unbound, and nothing recorded what each model received | Manifest with deterministic re-derivation; per-run input bundles compared by content (section 3) |
| 3 | `raw_output_sha256` was a regex format check, linked to no bytes | Private content-addressed store, attempt records, deterministic extraction, `REVIEW_DIFFERS_FROM_RAW`; seals need `VERIFIED` (section 4) |
| 4 | `robust` was blocked only by `UNSUPPORTED` or a serious issue; `PARTLY_SUPPORTED` and `CANNOT_CHECK` counted | `ai_audit_supported` needs four `SUPPORTED` findings (section 6) |
| 5 | One label, `ai_verified_economic_connection`, implied economic verification from quotation validity | Renamed; six dimensions reported separately; mechanism and real-world validation are explicitly absent (section 6) |
| 6 | Integrity flags were reported but never affected conformance | Severity classes, prospective human disposition, gate and ordering (section 7) |

## 10. Residual risks that software cannot remove

- **Operator attestation.** Model identity, run times, the supplied folder and the receipt of raw bytes are recorded by the operator. The software checks consistency, not truth. A dishonest operator could fabricate a raw response that extracts to an invented answer.
- **Provider corroboration.** Hosted chat products rarely expose verifiable model identifiers or signed transcripts. Identities stay attestations.
- **Attempt completeness.** An attempt never recorded, or the last record deleted, cannot be detected without git history or an external log.
- **Upload fidelity.** A bundle records a folder; it cannot prove the hosted product ingested every file (for example, silent truncation of long evidence).
- **Injection detection.** It is pattern-based and incomplete. A persuasive document is not detectable mechanically. Unscannable formats (PDF) are only listed.
- **PDF verification.** Quotes from PDFs remain `UNVERIFIABLE`, unchanged from v001. This is a known limit, not a document-processing subsystem.
- **Join and economic truth.** Dimensions 2, 5 and 6 are not assessed. Two models agreeing on exact quotes is AI agreement on documents, with correlated-error risk (shared training data, public repository).
- **Public repository.** Browsing reviewers are potentially unblinded. R4 artefacts and raw stores stay off the remote until Stage C.

## 11. Recommendation

**READY_FOR_OFFLINE_CALIBRATION**, in a narrow sense. The software and the unchanged frozen texts now have defensible evidence integrity and calibrated labels, sufficient for a separately authorised instrument check on fixed synthetic or already-closed items, evidence-pack-only, as v001 section 9 proposed.

This recommendation:

- authorises no model call (that needs the owner's separate authorisation and registration);
- does not unpause R4;
- does not make AI labels human adjudication or R4 evidence.

The instrument is **not** ready for R4 use while R4 is paused and its source questions are unresolved.

## 12. Owner checklist additions (to v001 section 10)

- [ ] Register the private raw-store location (git-ignored or outside the repository) and who holds it.
- [ ] Register the attempts policy: v002 treats any earlier extractable attempt as `CONFLICTING`.
- [ ] Name the human who disposes of integrity flags, and accept the conservative rule that a confirmed attempt withholds the whole package.
- [ ] Decide what provider evidence, if any, should corroborate model identities.
- [ ] Note that `ai_review.py` changed: the pinned implementation closure digest changes (no snapshot exists, so nothing breaks).
