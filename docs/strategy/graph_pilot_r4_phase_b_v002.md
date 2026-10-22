# Graph Pilot R4 Phase B: review corrections (version 002)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-phase-b` (draft PR #6, unmerged). R4 is NOT_RUN and not activated.**

This version corrects the three blockers from the independent review of `e4b9516` and records the requested activation design. [Version 001](graph_pilot_r4_phase_b_v001.md) is unchanged and still holds unless amended here.

**Untouched:** R3's files, the Graph v1.1 records, the v1.2 holdout, the generic register and Opportunity Scout.

[Phase B rehearsal](graph_pilot_r4_phase_b_dry_run.md) (23/23) · [Validation](graph_pilot_r4_phase_b_validation_v002.json)

## Blockers corrected

| Finding | Correction | Regression |
|---|---|---|
| **1. Reveal-order equality bypass** | `git merge-base --is-ancestor` succeeds for identical commits. `reveal_order()` now requires strict ancestry: a log whose first commit is the other reviewer's seal commit is `VIOLATED`. | A real throwaway-git case commits both seals and both reviewers' logs together; it is refused. The legitimate sequence still verifies, and the early-reveal case is still refused. |
| **2. Legacy packets defaulted to conforming** | An explicit cohort boundary. A report with no prospective packet is a pure legacy report and behaves exactly as before. Once any prospective packet is present, only R4-conforming packets form the primary cohort. Legacy packets are listed with `LEGACY_PACKET_OUTSIDE_R4_PRIMARY_COHORT` and keep their descriptive metrics. | A mixed report of R3 P3 and P4 plus synthetic R4 P1 counts one primary pair, not three; R3 is excluded with its reason; the result is INCONCLUSIVE. A pure R3 report is unchanged. |
| **3. Unknown adjudicator time omitted** | A cost total with any unknown entry is `UNKNOWN`, with the known subtotal and the unknown-entry count kept beside it. This applies to `adjudicator_minutes`, `suggestion_review_minutes` and `graph_minutes`. Medians now report how many unknown or unnamed entries they excluded. `direction()` treats UNKNOWN as not comparable. | A dual-reviewed item with one unknown reviewer duration gives an UNKNOWN total, the correct known subtotal and 1 unknown entry. |

**Effect on R3's computed report (its files are unchanged).**

- Every R3 adjudication records `adjudicator_minutes` as UNKNOWN: 17 in P3, 19 in P4. The code-generated report previously showed adjudicator cost as **0** with direction EQUAL; that was the silent-zero defect.
- It now shows UNKNOWN (P3: S 8 / G 9 unknown entries; P4: 7 / 12), with direction NOT_COMPARABLE.
- R3's classification (INCONCLUSIVE), its pooled rates (`G 3.151, S 4.162`) and its notes are unchanged; these cost fields never entered the classification.
- The frozen `graph_pilot_r3_results.md` never stated an adjudicator time, so no R3 document is contradicted.

## Unblinding: software controls versus procedural secrecy

**Enforced by this tool:**

- **Who unblinds.** Only two public commands unblind: `pilot report` and `pilot suggestion-accounting --export`. For a prospective packet, both go through `unblind()`, which computes the sealed dual consensus itself and refuses until both reviewers' seals are valid.
- **What `report` shows before that.** It lists the packet as `NOT_UNBLINDED` and excluded (`ADJUDICATION_NOT_DUAL`).
- **Supplied consensus.** A caller-supplied consensus is accepted only for synthetic packets, in tests.
- **Single-log unblinding.** `rehearsal_single_log` lets the Phase A synthetic rehearsal use one legacy log; it is refused for any live packet.
- **The agreement view.** `pilot adjudication-agreement` reads only the two logs; it never reads the key.

**Not enforced, and procedural:**

- `key.json` and `alias_key` are ordinary files. Anyone with repository or file access, including the owner, can read them, and nothing here cryptographically prevents that.
- Keeping them unread until both seals are committed, keeping logs private until both seals exist, and the absence of contact between reviewers are procedural commitments.
- The seals, reveal order and exposure declarations are evidence of those commitments, not proof.

## Proposed policy for POTENTIALLY_UNBLINDED items

This is registered now, before any R4 outcome exists, and is not chosen afterwards.

| Option | Effect | Bias limitations |
|---|---|---|
| **Inclusion (proposed primary)** | Exposed items stay in the primary analysis, labelled; denominators are complete | Exposed judgments may favour the arm the reviewer recognised. The direction is unknown, and labelling does not remove it. |
| **Exclusion (proposed sensitivity)** | Every packet with any POTENTIALLY_UNBLINDED item is removed | Exposure may correlate with arm, packet difficulty or reviewer, so dropping exposed packets can itself bias the comparison. It also cuts the pairs, often below the minimum of three. |
| Item-level exclusion (not proposed) | Removes only exposed items | It changes per-packet denominators in arm-dependent ways and leaves exposed reviewers' other judgments in place. |

**The rule, implemented as `blinding_sensitivity`.** The primary analysis includes exposed packets. The sensitivity excludes them. If the two classifications differ, no definitive classification is reported (INCONCLUSIVE, `BLINDING_SENSITIVITY_UNRESOLVED`). The rule is proposed: the owner registers it, or a different one, at activation.

**Consensus rule preserved (proposed).** An outcome counts only where both reviewers agree. A disagreement stays `UNRESOLVED_DISAGREEMENT`. There is no AI or operator arbitration and no tie-break, pending the owner's prospective registration.

## Evidence

- **Rehearsal.** `pilot r4-phase-b-dry-run --check`: 23/23. That includes the new same-commit violation and pre-seal unblinding refusal.
- **Focused tests.** 10 Phase B tests pass: 5 existing and 5 review regressions.
- **Mutation checks.** 21/21 caught: 8 for the new safeguards, plus the 13 Phase B mutations repeated against the extended tests. One was re-expressed because its target line changed.
- **Records.** The R2 dry-run record, the Phase A rehearsal record, and every v1.1 and v1.2 record regenerate byte-identically.
- **Full suite and CI.** See the [validation receipt](graph_pilot_r4_phase_b_validation_v002.json).
- **Clean-checkout limitation.** In a fresh worktree without the ignored private data, `test_exp001.FinalTestIntegrationTests` (needs `data/raw/EXP001_SPY_AI_SELECTION/`) and `test_phase3c_parser…test_original_namespace_scale_unit_and_aggregate_rejection_offline` (needs a private Phase 3C input) error. Both pass in the full checkout. Public CI runs `public_checks` and Scout's checks, which do not need private data.

## Engineering readiness

All three blockers are corrected, tested and mutation-checked. Remaining items are activation requirements, not engineering defects:

- recruit real reviewers;
- register the consensus and blinding rules;
- write the reviewer guide;
- write the arm, operator and reviewer instructions;
- write the R4 activation document.

These are listed in v001 and are unchanged.
