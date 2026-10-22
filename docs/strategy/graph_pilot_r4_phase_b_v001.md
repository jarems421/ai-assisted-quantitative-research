# Graph Pilot R4 Phase B: independent dual human adjudication (version 001)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-phase-b`, from `main` at `ca9f4ce` (PR #3 merged with a merge commit; post-merge CI passed). Draft PR, not merged.**

**Scope:**

- R4 is NOT_RUN, not activated and not authorised.
- No real source, campaign, session, reviewer or adjudication; synthetic fixtures only.
- No AI judgment substitutes for human adjudication, and no investment outcome is inferred.

**Untouched:** R3, the Graph v1.1 evaluations, the v1.2 holdout, the generic register and Opportunity Scout.

[Phase B rehearsal](graph_pilot_r4_phase_b_dry_run.md) (21/21) · [Phase A readiness v004](graph_pilot_r4_readiness_v004.md) · [Validation](graph_pilot_r4_phase_b_validation.json) · Code: [`adjudication.py`](../../src/research/graph/adjudication.py)

## What was built (IMPLEMENTED, TESTED)

| Requirement | Implementation | Shown by |
|---|---|---|
| 1. Per-item exposure declarations, with conflicts | Every row of both logs carries `exposure` (see below). Each item is classed CLEAN, POTENTIALLY_UNBLINDED, NOT_INDEPENDENT or CONFLICTED (see below) | Rehearsal; mutation checks |
| 2. Two independently sealed human logs, then agreement | See below | Rehearsal; unit tests; mutation checks |
| 3. Separate warning-usefulness assessment | See below | Rehearsal; unit tests; mutation checks |
| 4. Non-conforming snapshots kept out of the primary comparison | See below | Rehearsal; unit tests; mutation checks |
| 5. Rehearsal, adversarial, mutation, preservation and CI checks | `pilot r4-phase-b-dry-run --check`: 21/21 checks; 13/13 Phase B mutations caught; legacy preservation tests | This report; [validation](graph_pilot_r4_phase_b_validation.json) |

**1. Exposure declarations.**

- **The record.** Every row carries `exposure`, with four fields:
  - `saw_arm_info`: YES or NO;
  - `seen`: drawn from arm ledger, connection log, arm session, blinding key, alias key, suggestion export, V001 export, the other reviewer's judgments, an AI assessment, or other;
  - `operated_or_attested_arm`: YES or NO;
  - `note`.

  YES must match the listed arm-identifying material.
- **The classes:**
  - **CLEAN:** nothing arm-identifying seen.
  - **POTENTIALLY_UNBLINDED:** arm-identifying material seen.
  - **NOT_INDEPENDENT:** the other reviewer's judgments, or an AI assessment, seen.
  - **CONFLICTED:** the reviewer declares arm operation, or their name matches a session attester.
- **Who may adjudicate.** Only humans, with the stricter assistant-name check.

**2. Two sealed logs.**

- **The logs.** Reviewers R1 and R2 each write `adjudications-R.jsonl` (economic confirmation) and `warning-usefulness-R.jsonl`, against the same aliased export.
- **Sealing.** Each reviewer personally seals both logs by hash, with an independence statement: `pilot adjudication-seal --reviewer R --by NAME` writes an immutable `adjudication-seal-R.json`.
- **What is refused:**
  - logs changed after sealing;
  - a seal made before its last judgment;
  - one person acting as both reviewers;
  - a second seal by the same reviewer.
- **Reveal order.** In git, each reviewer's logs must first appear no earlier than the other reviewer's seal, which gives `VERIFIED`; otherwise the result is `VIOLATED`.
- **Agreement.** `pilot adjudication-agreement` reports, for outcome, economic meaning and usefulness:
  - raw agreement and Cohen's kappa, each with its denominator;
  - the confusion matrix;
  - every disagreement.
- **Consensus rule (proposed).** An outcome counts only where both reviewers agree. Otherwise it is `UNRESOLVED_DISAGREEMENT`, never resolved by an AI or an operator.

**3. Warning usefulness.**

- **Separate items.** The economic log may judge only CONNECTION items. The usefulness log covers only METHODOLOGICAL_WARNING and AVOIDED_REPEAT items.
- **Categories:** `USEFUL_LESSON_REUSED`, which needs the avoided action and the checked lesson evidence; `USEFUL_NOT_USED`; `NOT_USEFUL`; `CANNOT_ASSESS`.
- **Reporting.** The report gives `warning_usefulness` per arm, with its own denominator and agreement. Avoided repeats count only as both-reviewer `USEFUL_LESSON_REUSED`. Usefulness is never an economic discovery; a test forcing every warning to "reused" leaves discoveries unchanged.

**4. Conformance.** In `pilot report`, a prospective packet enters the primary comparison only if:

- its snapshot conforms (`r4_configuration.conforms: true`);
- both seals are valid;
- no item is CONFLICTED or NOT_INDEPENDENT;
- for live packets, the reveal order is VERIFIED.

Every other packet is listed in `excluded_from_primary`, with its problems and any owner `deviation-*.json` records. Those are preserved, and their treatment can only be `EXCLUDED_FROM_PRIMARY` or `SECONDARY_DESCRIPTIVE_ONLY`; a request to include a packet in the primary comparison is refused.

**Rehearsal results.** In the rehearsal, P1 conforms and P2 (v1.1, deviation recorded, reveal order violated) is excluded. P1's agreement figures:

| Judgment | Items | Raw agreement | Kappa |
|---|---:|---:|---:|
| Outcome | 4 | 3/4 | 0.6 |
| Economic meaning | 4 | 3/4 | 0.6 |
| Usefulness | 1 | 0/1 | 0.0 |

There is one unresolved economic disagreement and one unresolved usefulness disagreement. One conforming pair stays INCONCLUSIVE.

**Legacy preserved:**

- R3 (V1, single adjudication log) reports exactly as before: INCONCLUSIVE, pooled `G 3.151, S 4.162`, with no conformance or usefulness fields.
- The R2 dry-run record, the v1.1 quality, adversarial and walkthrough records, the v1.2 holdout, and the register are byte-unchanged.

**One documented record change.** The Phase A rehearsal record (`graph_pilot_r4_dry_run.md`) was regenerated. Its single changed line shows that Phase A's synthetic V2 packet, adjudicated with one legacy log, is now correctly excluded from the primary comparison. Its session sensitivity therefore reads NOT_VALID, and the classification is still INCONCLUSIVE.

## Unresolved activation requirements (owner and procedure)

1. **Real reviewers.** Two different human reviewers who did not operate or attest any arm. Recruiting and instructing them is procedural.
2. **Independence is evidenced, not proven.** Seals, the reveal order and exposure declarations are self-reported records. Reviewers must keep their logs private, with no shared notes or discussion, until both seals are committed; the logs are committed only afterwards.
3. **Register the consensus rule at activation.** Both reviewers must agree, and disagreements stay `UNRESOLVED_DISAGREEMENT`. No third-reviewer or arbitration protocol exists. If one is wanted, it needs its own prospective design.
4. **A reviewer guide** defining the economic outcome and usefulness categories with examples, frozen before review.
5. **Arm and operator instructions** for V2 exports, session attestations and the reviewer handoff. These are not yet written.
6. **Small samples.** Kappa with few items is unstable, so agreement figures are descriptive only.
7. **The R4 activation document itself.** The owner's authorisation, source preflight, packets, ceilings, the named reviewers and operators, and the registered rules (configuration V002, effort gate, consensus rule).
8. **Carried over from Phase A:**
   - per-process memoisation;
   - self-declared attestation and git timing;
   - the minimal generic register (H7);
   - the pre-existing flaky SEC-pilot test.

   The legacy single-log adjudication validator keeps its original name check, to preserve R3 behaviour.
