# Graph Pilot R4 readiness, Phase A hardening (version 002)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-readiness`. R4 is NOT_RUN, not activated and not authorised.**

This version supersedes the status in [version 001](graph_pilot_r4_readiness_v001.md), which is kept unchanged as history. It records:

- the owner's six prospective policies;
- the three code-review findings and their fixes;
- the GRAPH_CLASSIFICATION_V1_2 rule and its holdout.

**Untouched:** R3, the Graph v1.1 frozen evaluations (quality, adversarial, walkthrough, R2 dry run) and Opportunity Scout. All of them regenerate byte-identically.

**Status labels:**

- **IMPLEMENTED:** code exists on this branch.
- **TESTED:** a focused test or rehearsal check fails when the behaviour is broken. Every hardening safeguard was also broken deliberately, and all 11 breaks were caught.
- **NOT_IMPLEMENTED:** no code yet.
- **NOT_RUN:** not executed, by design.

[Synthetic dry run](graph_pilot_r4_dry_run.md) (49/49) · [v1.2 rule registration](graph_v1_2_rule_registration.md) · [v1.2 holdout](graph_v1_2_holdout.md) · [R4 protocol draft (NOT_RUN)](graph_pilot_r4_protocol_proposed.md) · [Validation](graph_pilot_r4_readiness_validation_v002.json)

## 1. Owner policies, registered prospectively

| # | Policy | Implementation | Status |
|---|---|---|---|
| 1 | A discrepancy is material above the greater of 5 minutes or 10% of the derived comparator; smaller ones are still reported | `compare_minutes` reports `difference_minutes`, `difference_percent`, `material_threshold_minutes` and `material`. Below-threshold differences are reported as `EFFORT_DIFFERENCE_BELOW_THRESHOLD` | IMPLEMENTED, TESTED |
| 2 | Generic shared identifiers alone are insufficient; any stronger rule is designed prospectively and evaluated on a fresh holdout | `GRAPH_CLASSIFICATION_V1_2`, registered and committed (`426c211`) before the holdout existed; see §4. v1.1 stays the default, and the adversarial set was not used | IMPLEMENTED, TESTED |
| 3 | `UNRELATED_COMMIT_CHANGE` only with identical pinned content; record the actual commit, and pin Python and dependency versions | Pin V002 also records `runtime`: the Python version and implementation, and the versions of the imported third-party distributions, plus `tzdata` for `zoneinfo`. Verification refuses any content or runtime difference. Every visibility receipt records the actual `running_commit` | IMPLEMENTED, TESTED |
| 4 | Pin `sec_pilot/parsing.py` if it is on the acquisition, validation or enforcement path; document the boundary | The pin's boundary is now computed: the static closure of `src.*` imports from the graph and discovery packages, `spec.py` and the R4 fetch tool (`docs/strategy/graph_pilot/fetch_one.py`). It includes package `__init__` files and imports inside functions. This pins `parsing.py`, whose `offline` guard enforces the rehearsal network block | IMPLEMENTED, TESTED |
| 5 | The 30-minute gap threshold is descriptive only | `gap_policy: DESCRIPTIVE_ONLY`; gaps are listed and never subtracted | IMPLEMENTED, TESTED |
| 6 | Human operators personally record start and stop, in separate immutable attestations written as the events occur; no assistant self-attestation | See below | IMPLEMENTED, TESTED |

**Session attestations (policy 6).** `pilot session-attest PACKET --arm S|G --event START|STOP --by NAME` writes `session-<arm>-start.json` or `-stop.json` (`GRAPH_PILOT_SESSION_ATTESTATION_V001`).

- **Written once.** A second START is refused.
- **Written at the event.** The recorded time may lag the event by at most 5 minutes.
- **Human only.** Assistant names (Claude, Codex, GPT and similar) and non-human kinds are refused.
- **Ordered.** A STOP needs its START. START must be attested before the arm begins recording, and STOP after its last record.
- **Sealed.** `pilot blind` seals both files' hashes in the key; unblinding refuses any later edit.

## 2. Code-review findings

**A. Accounting levels: FIXED, TESTED.**

- `suggestion_accounting` now keeps two separate levels, each with a matching denominator:
  - **Suggestion level:** unique origins, giving exported, logged, exported but unlogged, the decision pattern (`ANY_ACCEPTED`, `ALL_DECLINED`, `UNRESOLVED_OR_MIXED`) and adjudicated suggestions.
  - **Row level:** connection-log rows, by kind and decision.
- Every rate pairs a numerator and denominator of the same level; for example, declined rows over logged rows. `rows_sharing_an_origin` is reported.
- Adjudication outcomes are joined per row (connection id), never overwritten by origin. Several rows sharing one origin keep their own outcomes, and conflicting outcomes are counted.
- Discoveries are reported as rows and as distinct origin suggestions. A focused test and the rehearsal cover duplicate-origin rows.

**B. Primary measure and sensitivity: FIXED, TESTED.**

- **Registered primary measure (proposed for activation):** self-reported analyst minutes, all categories, graph time included.
- **Sensitivities:**
  - The attested-session sensitivity is valid only when every arm has RECORDED session attestations.
  - The observed-span sensitivity is descriptive only.
- **Why elapsed time is not effort.** Elapsed session or record time includes idle time, interruptions and waiting that cannot be separated from research. It also misses work before the first or after the last record.
- **Per-arm `effort_evidence`:** `CONSISTENT`, `INCOMPLETE`, `MATERIAL_DISCREPANCY` or `CONTRADICTORY`.
- **The gate.** For prospective (V2) packets, a definitive classification needs one of:
  - every arm CONSISTENT; or
  - no arm CONTRADICTORY, and the classification unchanged under the attested-session sensitivity.

  Otherwise it is INCONCLUSIVE (`EFFORT_EVIDENCE_UNRESOLVED`), with the primary result shown beside it.
- **Reporting.** The report prints the effort evidence first.
- **Legacy packets** (R2 dry run, R3) keep their exact classification and notes; R3 is still INCONCLUSIVE, pooled `G 3.151, S 4.162`.

**C. Pin enforcement: FIXED, TESTED.**

- **Before:** only `arm_graph` checked the pin, so the structured-search arm (`arm_view`), unblinding, effort and accounting did not.
- **Now:** `load_snapshot` enforces content and runtime, so every snapshot-bound entry point verifies the same pin.
- **Tested:** with a simulated implementation change, the focused test and the rehearsal confirm that all of these refuse:
  - the S arm view, by API;
  - `baseline-search`, by CLI;
  - `arm_graph`, by API;
  - `revisit`, by CLI;
  - export replay;
  - unblinding;
  - effort and accounting;
  - `verify`.
- **Boundary.** Direct `build()` or `baseline.structured_search()` calls on raw ledgers are not snapshot-bound, so no pin applies; the pilot never uses them.

## 3. Synthetic end-to-end rehearsal: 49/49

`pilot r4-dry-run --check`.

**The pipeline:**

- a V2 packet pinned from a throwaway git copy;
- attested sessions, graph queries and the frozen export;
- V2 logs, including two rows sharing one origin;
- effort evidence and accounting;
- blind, alias, leak-scan, a labelled synthetic adjudication stand-in, unblind, and the report;
- uniform pin enforcement, with a simulated implementation change.

**Effort results.** G is CONSISTENT: 16 self-reported minutes against a 16-minute attested session. S is CONTRADICTORY: it claims 46 minutes against a 14-minute session.

**Mutations, each refused or flagged:**

- runtime and implementation changes;
- assistant, non-human and duplicate attestations;
- a STOP without a START;
- an attestation edited after blinding;
- a missing export;
- a warning forced to "confirmed".

## 4. GRAPH_CLASSIFICATION_V1_2 and its holdout

**The rule** ([registration](graph_v1_2_rule_registration.md)):

- An `EXACT_ENTITY_ID` basis does not ground when every shared identified object is generic: typed `REGULATOR` or `GEOGRAPHY`, or matched by the versioned register, which covers ISO 10383 `MIC:` exchanges and `ISO3166:` geographies.
- A documented relationship or the same document still grounds, and so does any shared non-generic object.
- Names never decide genericness.

**Ordering.** The rule and plan were committed and pushed (`426c211`) before the holdout fixtures existed. The rule was not changed after the holdout ran.

**The holdout.** [graph_v1_2_holdout.md](graph_v1_2_holdout.md) has 10 fresh cases with their own campaigns, entities and identifiers.

| Measure | v1.1 | v1.2 | Structured search |
|---|---:|---:|---:|
| True positives (of 5) | 5 | 5 | 5 |
| False negatives | 0 | 0 | 0 |
| False positives | 5 | 1 | 5 |
| Review load (all items shown) | 19 | 19 | 14 |

**Reading:**

- **Result.** Under the registered reading, the result is **SUPPORTED on this holdout**.
- **Remaining false positive.** It is H7, the declared expected miss: a central bank recorded as a legal entity with an LEI, not in the register.
- **H10.** A regulator plus a shared tag becomes a warning, as its truth says.
- **Review load is not reduced.**
- **Caveat.** The same implementer wrote both the rule and the holdout; this is not an independent or real-world benchmark.
- **Adoption.** v1.2 is not yet the default: an R4 snapshot records its ruleset, and adopting v1.2 for R4 is an owner decision.

## 5. NOT_RUN (by design)

- **R4 itself:** activation, source preflight, packet formation, arm campaigns, real sessions and attestations, human adjudication, unblinding and the report.
- **No real-world data:** no real-world source request or acquisition of any kind.

## 6. Unresolved technical issues

1. **The pin boundary over-approximates.** `spec.py` lazily imports `exp004_policy`, which pulls in `exp002_contracts`, `pit_signals` and optional `nexustrade`. A static closure cannot tell executed imports from unexecuted ones. So a change to those frozen modules, or installing `edgar` or `lxml`, would refuse a pinned packet. This errs strict.
2. **Memoisation.** Content, runtime and git state are cached per process, keyed on file modification times and sizes and on the git `HEAD`, index and reflog. An edit that preserves both size and modification time inside one long-running process would go unseen until the next process. Each CLI query is a new process.
3. **Attestation timing is self-declared.** The tool writes attestations at the event, and they are write-once and sealed at blinding. Nothing proves when a human wrote them; there is no external timestamping. An assistant using a human's name cannot be detected; this remains procedural.
4. **The generic register is minimal.** Central banks, courts, tax authorities and standard setters are recognised only if typed `REGULATOR` or listed by exact identifier (holdout H7). Entries need owner review.
5. **The rule-ordering test skips** where git history is shallow (CI's `fetch-depth: 1`). It runs locally.
6. **Weaker adjudicator name check.** `validate_adjudications` still uses the older prefix-only assistant check, not the stricter `ASSISTANT_NAME` pattern. This belongs to Phase B.
7. **A pre-existing flaky test outside Graph.** `test_sec_pilot_acquisition…test_concurrent_idempotence_and_changed_versions` raised "Archive path escape" under thread concurrency once in two full local runs. It passed 5 of 5 times in isolation and in the second full run. This branch does not change `sec_pilot` or that test. It is recorded in the receipt and not fixed here.

## 7. Phase B scope (precise)

1. **Adjudicator exposure.**
   - Each adjudication row carries `exposure`: `SAW_ARM_INFO=YES|NO`, plus what was seen (arm ledger, connection log, session, key, AI assessment, other adjudications).
   - The validator refuses a missing note, and any adjudicator who operated or attested an arm.
   - Any YES marks the packet potentially unblinded in the report.
   - The stricter assistant check applies to adjudicator names.
2. **Independent two-reviewer agreement.**
   - A second adjudication log against the same aliased export, by a different human, each sealed (hash committed) before the other is visible and before unsealing.
   - Per-item agreement, raw agreement and Cohen's kappa, each with its denominator, plus the list of disagreements.
   - Disagreements are never resolved by an AI or by an operator.
   - A registered rule for which outcome feeds the dimensions: for example, a confirmation only when both confirm, with disagreements reported as `UNRESOLVED`.
3. **Separate warning-usefulness adjudication.**
   - Its own vocabulary, for example `USEFUL_LESSON_REUSED`, `USEFUL_NOT_USED` and `NOT_USEFUL`, with the avoided action and its evidence.
   - Its own denominator over logged warnings.
   - A report dimension kept apart from economic discoveries, so warnings are no longer adjudicated with the connection outcomes.
4. **For each:** a sealed log format, validators, tests, mutation checks and an extension of `pilot r4-dry-run`.

## 8. Owner decisions still open

1. Adopt `GRAPH_CLASSIFICATION_V1_2` for R4 snapshots, or keep v1.1.
2. Owner-reviewed additions to the generic register: for example, specific central banks or courts by LEI.
3. Whether the over-approximating pin boundary (issue 1) is acceptable, or the closure should exclude imports that are unreachable from the pilot entry points.
