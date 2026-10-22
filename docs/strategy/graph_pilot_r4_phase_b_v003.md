# Graph Pilot R4 Phase B: zero-item packets and content-verified reveal order (version 003)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-phase-b` (draft PR #6, unmerged). R4 is NOT_RUN and not activated.**

This version is a strictly scoped correction from the final review of `df5ad31`. [v001](graph_pilot_r4_phase_b_v001.md) and [v002](graph_pilot_r4_phase_b_v002.md) are unchanged and still hold unless amended here.

**Untouched:** R3, the Graph v1.1 records, the v1.2 holdout, the generic register and Opportunity Scout.

[Phase B rehearsal](graph_pilot_r4_phase_b_dry_run.md) (30/30: the existing 23 checks unchanged, plus 7) · [Validation](graph_pilot_r4_phase_b_validation_v003.json)

## 1. Zero-item packets: an explicit, auditable path

A fully formed packet can legitimately produce zero CONNECTION, METHODOLOGICAL_WARNING and AVOIDED_REPEAT rows. Before this fix:

- `validate_reviewer()` derived no identity from empty logs;
- `seal()` could not associate the logs with the named reviewer;
- `load_seal()` called `max()` over no judgments.

**Now:**

| Step | Rule |
|---|---|
| Logs | Each reviewer must write both log files, even when empty. A missing log file is refused, never read as empty, for every packet |
| Seal V002 | The seal carries the reviewer's identity and a mandatory reviewer-level `reviewer_exposure` (the same fields as an item's exposure), with item counts that must match the logs. With zero items, the seal is the reviewer's identity and declaration over explicitly empty logs |
| Exposure and conflicts | The reviewer-level declaration is classed like an item's. A CONFLICTED reviewer (one who declares arm operation, or whose name matches a session attester) or a NOT_INDEPENDENT reviewer makes the packet non-conforming, as an item would. POTENTIALLY_UNBLINDED at reviewer level labels the packet |
| Identities | Two different humans are still required. With no log rows, identity comes from each seal |
| Timing | "Sealed after the last judgment" is checked whenever judgments exist. With zero judgments there is nothing for it to follow |
| Agreement | Explicit zero denominators: 0 items, raw agreement `UNDEFINED_ZERO_DENOMINATOR`, kappa `UNDEFINED_ZERO_DENOMINATOR` |
| Unblinding and report | The consensus is empty and `unblind()` returns no rows. The packet stays in the report and, when everything else conforms, enters the primary comparison with zero counts. No judgment, discovery, usefulness score or reviewer effort is invented; zero adjudicator minutes is a true sum over zero items |
| Eligibility | No packet-eligibility rule excludes zero-row packets. One could only be added as a separately preregistered rule |

**Rehearsal (P5, zero rows):**

- an empty frozen export;
- missing logs refused;
- a seal without a reviewer-level exposure declaration refused;
- two different sealed reviewers;
- reveal order VERIFIED in real git;
- CONFORMING, and reported in the primary comparison with zero counts.

**Unit tests:**

- a zero-item reviewer who attested an arm is CONFLICTED;
- one person sealing both reviewer slots is refused;
- a zero-item reviewer who saw an AI assessment is NOT_INDEPENDENT;
- a V001 seal without the reviewer-level declaration is refused.

## 2. Reveal order now uses the commits that hold the sealed bytes

**The gap.** `reveal_order()` used each path's first-introduction commit, matched by file name only. A false VERIFIED was possible if:

- a placeholder log was committed after the other reviewer's seal and later replaced with the sealed content; or
- a seal file was rewritten after its first commit.

**The fix (fail closed).** For each seal and log, the current bytes are hashed exactly (`git hash-object --no-filters`). Every commit reachable from HEAD that touches the path must hold exactly those bytes. If any commit holds other content (a placeholder first, a later change, a deletion or a re-addition), or the working copy differs from what was committed, the result is **VIOLATED**. A file never committed is NOT_COMMITTED. Ordering then uses the first commit holding the sealed bytes, with strict ancestry as in v002.

**Regressions in real throwaway git:**

- placeholder-then-sealed logs are VIOLATED;
- a seal rewritten (reformatted) after its first commit is VIOLATED, even though the seal still validates;
- an uncommitted edit to a sealed file is VIOLATED;
- the legitimate sequence still VERIFIES;
- the earlier same-commit and early-reveal violations still hold.

**Residual limitations (procedural, documented):**

- **History can be rewritten.** Rebases or force-pushes can rewrite git history, and commit order is a property of the local graph, not of wall-clock time. The pilot must keep history intact, as already required: no squash, rebase or shallow clones.
- **Byte comparison only.** The check compares exact bytes. A repository that applied text conversion on commit would make legitimate files look changed. That fails closed: the result is a refusal, never a false VERIFIED. This repository preserves bytes (`* -text`).
- **Other channels.** Nothing here detects a reviewer who saw the other's judgments outside git. Seals, reveal order and exposure declarations are evidence, not proof.

## Evidence

- **Rehearsal.** `pilot r4-phase-b-dry-run --check`: 30/30. The 23 existing checks are unchanged.
- **Focused tests.** 13 Phase B tests: 5 existing, 5 from v002, and 3 for zero items and content history.
- **Mutation checks, the full suite and CI.** See the [validation receipt](graph_pilot_r4_phase_b_validation_v003.json).
- **Clean-checkout limitation, unchanged from v002.** Two tests need ignored private inputs: the EXP001 integration tests and one Phase 3C parser test. Public CI does not need them.

## Engineering readiness

The zero-item path and content-verified reveal order are implemented and tested. No review finding remains open. Remaining items are activation requirements (v001 and v002), not engineering defects.
