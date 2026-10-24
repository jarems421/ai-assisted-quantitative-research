# Discovery Lab operator guide

Discovery Lab records how an investment research idea earns, or fails to earn, its way to [Measurement Gate M](measurement_gate_m.md). It starts from evidence: an original observation, a documented relationship or a dated event. A mechanism-first baseline is kept for comparison. Every claim is frozen before its outcome is examined, checked mechanically, challenged by structured sceptic reviews and decided by a human.

It is **not** a signal generator, crawler, stock picker, evidence level or experiment registry. Discovery IDs never become `EXP` IDs; nothing here touches the experiment Store, trial counts, Nexus or market data. [Design and limits](discovery_lab_design.md) · [Claude prompts](discovery_lab_prompts.md) · [Offline walkthrough](discovery_lab_walkthrough.md).

## Quick start (offline, no network)

```sh
python -m src.research.discovery demo                 # print the synthetic walkthrough
python -m src.research.discovery demo --out <dir>     # also keep the five demo ledgers
python -m src.research.discovery demo --check         # verify the committed walkthrough
python -m unittest tests.test_discovery_lab -v
```

## Workflow

Each campaign is one append-only JSONL ledger. Draft each record from a template, fill every field (unknown facts stay `UNKNOWN`), then append it; invalid or forbidden records are refused with a reason.

| Step | Command |
| --- | --- |
| 1. Create a campaign (one method, equal budgets across compared campaigns) | `template campaign` → edit → `init LEDGER campaign.json` |
| 2. Register a Source Passport and see its next evidence rung | `add LEDGER source src.json` · `source LEDGER SRC-ID` |
| 3. Record an observation (it need never become a claim) | `add LEDGER observation obs.json` |
| 4. Record a documented relationship | `add LEDGER relationship rel.json` |
| 5. Form a candidate claim | `add LEDGER candidate cand.json` |
| 6. Freeze it **before** examining the intended outcome | `freeze LEDGER CAND-ID` |
| 7. Show mechanical blockers, gaps and the next decisive check | `checklist LEDGER CAND-ID` |
| 8. Record sceptic, M and H reviews; then a human disposition | `add LEDGER review rev.json` · `add LEDGER disposition dsp.json` |
| 9. Log effort, including failures and unknown costs | `add LEDGER effort eff.json` |
| 10. Summarise and compare | `summary LEDGER` · `compare L1 L2 ...` · `validate L1 ...` |

All commands are `python -m src.research.discovery <command>`. `prompt <stage> --ledger L --record ID` prints the matching Claude prompt with the record and checklist attached.

The four methods share every validator and the same checklist. They differ only in the claim's required entry point:

| Method | Entry record |
| --- | --- |
| `OBSERVATION_FIRST` | An earlier observation that is part of the predictor |
| `RELATIONSHIP_FIRST` | An earlier relationship that links the exposure |
| `EVENT_FIRST` | An earlier `EVENT` observation |
| `HYPOTHESIS_FIRST` (baseline) | None; the mechanism comes first |

## Reading the statuses

**Evidence depth**, per evidence item and observation:

| Depth | Meaning |
| --- | --- |
| `VERIFIED_ORIGINAL_FIELD` | The economic field itself was seen in an original, with a sha256 or archive pointer |
| `VERIFIED_ORIGINAL_RECORD` | The original document was seen with provenance, but not necessarily this field |
| `INDEXED_DESCRIPTION_ONLY` | A search index or catalogue describes it |
| `SCHEMA_ONLY` | A data dictionary defines the field; no record was seen |
| `RETROSPECTIVE_DESCRIPTION` | A later account describes earlier facts |
| `UNVERIFIED` | Not established |
| `ACCESS_BLOCKED` | The route refused access; record the limit, never bypass it |

Only `VERIFIED_ORIGINAL_FIELD` satisfies the distinctive-predictor requirement.

**Four clocks**, kept separate on every observation:

- **Economic occurrence:** when the real-world event happened.
- **First public:** when outsiders could first obtain it. A date is allowed only from an original publication-record certificate. Document dates, HTTP headers, web caches, filenames, search indexes and dataset versions are refused as first-public evidence.
- **Source version:** the date the publisher gives the record.
- **Retrieval:** when we obtained it.

`VERIFIED_AS_OF` needs a certified first-public time. Otherwise use `VERIFIED_ONLY_RETROSPECTIVELY` or `UNVERIFIED`. Exact first-public time is a Level B question; at M it appears as a gap, not a blocker.

**Relationships:**

- `basis` is `DOCUMENTED`, `NAME_MATCH_ONLY` or `INFERRED`. Only a documented basis, backed by original evidence and identified entities, can be `VERIFIED`.
- `quantity_transfer` stays `UNVERIFIED` unless an original document states the share. Proportional, equal-split and aggregate-as-cohort allocations are never verified.
- A relationship whose dated period does not cover the predictor's economic occurrence blocks the join.

**Checklist** (`software_certifies_M` is always `false`):

- **Requirement states:** each requirement is either `BLOCKED` (with codes such as `OUTCOME_ROUTE_ONLY_PROVISIONAL` or `ALLOCATION_UNVERIFIED`) or `NO_MECHANICAL_BLOCKER_HUMAN_JUDGMENT_REQUIRED`.
- **Gaps** are non-blocking warnings, such as `EXACT_PUBLIC_TIME_UNRESOLVED` or `NOT_ELIGIBLE_FOR_UNTOUCHED_EVALUATION`.
- **H gaps** concern the 5–20-session assessment and never affect M.
- **`next`** names the first blocked requirement, in this order: predictor, units, outcome, join, exposure, public-time route.

**Claim versions:**

- **Before freezing:** a changed version is a `PRE_FREEZE_REVISION`.
- **After freezing:** a version that keeps the distinguishing core (predictor, population, mechanism, outcome object, company, claim basis) is a `CLARIFICATION`. Any change to that core is a `MATERIAL_REVISION`, and that lineage is reported as a `REFORMULATION`.
- **Outcome seen first:** `after_outcome_seen` marks a post-outcome claim.
- **Renamed claims:** a new claim that reuses predictor observations must name its predecessor.

**Reviews and dispositions:**

- **Who may review:** reviews come from a human or an assistant. The M judgments are `EVIDENCED`, `NOT_EVIDENCED` or `UNCERTAIN`; uncertainty is a valid answer.
- **Rubber stamps are refused:** `EVIDENCED` is refused while that requirement has mechanical blockers.
- **What reviews must acknowledge:** every review must list the categories it did not check: competitor, historical source, outcome and public time, whichever apply.
- **Who decides:** dispositions are human decisions, using the M vocabulary `REJECT`, `HOLD`, `VERIFY`, `M_PASSED` and `LEVEL_A_DESIGN_CANDIDATE`.
- **What they authorise:** nothing; `authorizes` is always `[]`.
- **REJECT versus HOLD:** an access limit or unresolved question is `HOLD`, not `REJECT`.
- **VERIFY:** carries one decisive question and a cost, as `PROPOSAL_ONLY`.
- **M_PASSED:** needs a frozen version, zero blockers and a human M review evidencing all six requirements.
- **LEVEL_A_DESIGN_CANDIDATE:** additionally needs `M_PASSED`, a separate human H review, all three propositions stated and owner approval.

**Fixtures:** `SYNTHETIC` campaigns contain only fabricated evidence and use `SYNTHETIC_FIXTURE` reviewers. `RETROSPECTIVE_INSPECTED` campaigns restate existing repository evidence at its recorded depth. `LIVE` campaigns must cite an existing authority document. Comparisons never mix fixture classes.

## Using Claude

Claude drafts observations, relationships, mechanisms, alternative explanations and sceptic reviews using the [stage prompts](discovery_lab_prompts.md). It may not certify publication times, units, legal obligations, identity, access rights, allocations, completeness or outcome joins. The software records what was evidenced, and a human decides.

Always ask for the minimum evidence that could change the decision. Stop when none is affordable within existing authority.

## Interpreting summaries and comparisons

- **Denominators:** summaries show them: observations recorded versus used, claims, versions, and stopped versus undisposed claims.
- **Unknown costs:** these appear as `UNKNOWN` and never as zero.
- **No ranking:** the method comparison reports counts only, with no score or ranking. Its headline count is *original claims passing M without reformulation*, reported alongside effort.
- **Exploratory only:** a handful of campaigns is anecdote. Treat differences as questions for a later, pre-registered comparison.

## Requesting authority for a live campaign

This build authorised **zero acquisition**; no live campaign exists. A live campaign needs a separate owner instruction, committed before any dispatch, stating:

1. **Scope:** the method or methods and the number of campaigns per method, with **equal starting budgets** (analyst hours, ordinary source starts and MiB).
2. **Recording:** campaign ledgers committed before dispatch, with `fixture: LIVE`, `acquisition_authorized: true` and the authority path.
3. **Each request:** one `SOURCE_START` effort per request pointing to its acquisition receipt, retaining errors and denials. No retries, bypasses, paid or authenticated access unless separately approved. A persisted stop closes a route.
4. **Selection:** the starting sources or events must be fixed before outcomes are seen, and candidates frozen before their outcomes are examined.
5. **Close-out:** a summary and comparison at the end, with no automatic follow-on. A `VERIFY` proposal or `LEVEL_A_DESIGN_CANDIDATE` needs its own approval.

Store tracked live ledgers under `docs/strategy/discovery/`. Keep original bytes private under `data/raw/` and refer to them by sha256 or archive pointer.

## Audit corrections and operator limits (24 October 2026)

The [Anvil/Crucible readiness audit](anvil_crucible_readiness_audit.md) distinguishes mechanical checks from source verification and a complete Level A study design. A clean checklist is never an M certificate or permission to run an investigation.

The additive [Level A integrity preflight V001](level_a_integrity_hardening_v001.md) binds future readiness to exact source bytes, measurement construction, historical joins, selection history, Forge origin and a frozen study design. `python -m src.research.study_readiness_v1 inspect|verify` is read-only: inspection always requires an independent review, and verification requires the separately enrolled owner's exact-scope signed record. It never creates a human decision or runs a study. Legacy Discovery dispositions do not establish this new-profile readiness; historical replay and M/Level A/B/C definitions remain unchanged. Operational adoption and real-study authority require the owner, as described in the preflight.

- An observation's `VERIFIED_ORIGINAL_FIELD` label can cite document-level original evidence. This declaration requires an actual field reading; the software cannot prove the reading from a document hash. The shared record vocabulary and frozen fixtures remain unchanged.
- A gross-basis claim needs its gross amount; a known net amount cannot fill the missing gross measurement. The existing net-basis requirement remains unchanged.
- Source Passport versions used by a frozen claim are re-derived from the ledger's freeze-time history. Revising a predictor or outcome passport adds `SOURCE_REVISED_AFTER_FREEZE`; an old review cannot support a new M disposition while that blocker remains. Record a new candidate version and review the relevant evidence; never rewrite the frozen version or suppress the warning.
- Creates, appends and freezes claim a sibling `<ledger>.writer.lock` exclusively. A second writer is refused. Normal completion or a caught exception releases the marker. Process termination can leave it behind: stop all writers, retain the ledger and marker, verify the expected committed head and replay, and obtain explicit operator reconciliation before removing the stale marker. Never automatically steal a lock, edit a partial event or retry a disputed append.
- Loading refuses a file without its final newline, including an otherwise parseable final JSON object. Retain incomplete bytes and reconcile against a known checkpoint; no automatic repair is provided. Read summaries only when writing has finished.

The chain detects broken links and rule violations; it cannot authenticate its author, detect removal of a complete suffix without a separately known head, or prevent a filesystem owner recomputing a valid chain. `HUMAN` is a recorded assertion, not verified identity. Real reviews must be independently entered/approved by the responsible human; never import a model's self-description as that approval.

For the first real handoff, retain the exact Scout proposal and card hash separately, document the manual field mapping and any changed hypothesis, verify originals/units/outcome independence/dated joins as a human, and freeze a separately authorised study-specific Level A design before its intended results are inspected. Discovery Lab ends at the design-candidate proposal; it supplies no general Level A analysis command. A short reviewed analysis script can be sufficient. It does not require a new research framework.
