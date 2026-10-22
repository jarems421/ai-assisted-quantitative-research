# Graph Pilot R4 readiness, Phase A: infrastructure and validation (version 001)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-readiness`, from `main` at `adc1584` (Graph v1.1 merged). R4 is NOT_RUN, not activated and not authorised.**

Phase A is infrastructure and synthetic validation only:

- no source was fetched, and no packet, campaign, session or adjudication ran;
- no R3 record changed;
- no Opportunity Scout file was touched.

[R4 protocol draft (NOT_RUN)](graph_pilot_r4_protocol_proposed.md) · [Synthetic dry run](graph_pilot_r4_dry_run.md) · [Adversarial evaluation](graph_v1_1_adversarial.md) · [Graph v1.1 design](graph_v1_1_design.md) · [Validation](graph_pilot_r4_readiness_validation.json)

**Status labels:**

- **IMPLEMENTED:** code exists on this branch.
- **TESTED:** a focused regression test or a dry-run mutation check fails when the behaviour is broken. Each of the five core safeguards was also broken deliberately once, and each break was caught.
- **NOT_IMPLEMENTED:** no code yet.
- **NOT_RUN:** not executed, by design.

## 1. Exact Git commit pinning: IMPLEMENTED, TESTED

`src/research/graph/implementation.py`; snapshot field `graph_implementation`.

| Rule | Behaviour | Status |
|---|---|---|
| What is bound | A V2 snapshot (`pilot snapshot --connection-log GRAPH_PILOT_CONNECTION_V2`) records the git HEAD, the per-file sha256 of the pinned set and their combined `tree_digest`, beside `graph_operator_version` | IMPLEMENTED, TESTED |
| Pinned set | Every `*.py` file under `src/research/graph/` and `src/research/discovery/`, plus `src/research/spec.py`: the code that determines graph outputs, suggestion ids and pilot validation. The catalogue is pinned separately by hash. `sec_pilot/parsing.py`, the demo network guard, is excluded | IMPLEMENTED, TESTED |
| Enforcement | Content is enforced, not commit. Every arm query, export replay, blinding and unblinding passes through `arm_graph`, which refuses if the running pinned-set content differs from `tree_digest`, naming the changed, added or removed files. `pilot verify` also reports how the current commit relates to the pin | IMPLEMENTED, TESTED |
| Dirty working tree | Freezing refuses any modified, staged, deleted or untracked pinned file. Dirty files outside the pinned set are allowed. At verification, a dirty pinned file is reported and passes only if its content still equals the pin | IMPLEMENTED, TESTED |
| Missing git metadata | Freezing refuses, because an unversioned implementation cannot be pinned. Verification still enforces content and reports `GIT_UNAVAILABLE_CONTENT_VERIFIED`. A commit is never inferred | IMPLEMENTED, TESTED |
| Legitimate unrelated changes | A different HEAD with identical pinned content passes as `UNRELATED_COMMIT_CHANGE`, for example `main` advancing with Opportunity Scout work. Line endings are normalised (CRLF to LF), so `autocrlf` differences verify | IMPLEMENTED, TESTED |
| Legacy compatibility | Snapshots without `connection_log` (the R2 dry run, R3) carry no pin and report `NOT_PINNED_LEGACY`. R3 snapshots verify unchanged | TESTED |
| A V2 snapshot without a pin | Refused on load | TESTED |

Tests and rehearsal use a throwaway git copy of the pinned set with a fixed-date commit. That exercises real git without depending on whether the developer's tree is clean.

## 2. Timestamp-derived effort accounting: IMPLEMENTED, TESTED

`pilot effort PACKET --arm S|G`; also `effort_check` in `pilot report`.

**Timestamps used:**

- every arm ledger append;
- every connection-log row;
- every graph query saved in the frozen suggestion export (arm G);
- operator-recorded session bounds (`session-<arm>.json`, `GRAPH_PILOT_SESSION_V001`), when present.

The session file must be recorded by a human operator; an assistant-recorded file is refused.

**Excluded.** Human decisions in the arm ledger are not arm effort: dispositions, and M/H reviews by a human. They are recorded after the campaign by protocol, and are counted as excluded rather than silently dropped.

**Reported side by side:**

- the observed span from the first to the last arm record;
- the session minutes, or `UNKNOWN` when no session file exists (never inferred);
- self-reported minutes, by category;
- self-reported graph minutes (`GRAPH_QUERY`, `SUGGESTION_REVIEW`), the number of recorded graph queries, and an upper bound on the review windows after each query;
- gaps longer than 30 minutes, listed but never subtracted.

**Flags:**

| Flag | Meaning |
|---|---|
| `EFFORT_DISCREPANCY` | Self-reported and derived minutes differ, against the span and against the session |
| `SELF_REPORTED_EXCEEDS_SESSION` | More minutes claimed than the session lasted |
| `EFFORT_EXCEEDS_APPEND_INTERVAL` | An effort claims more than the time since the previous effort (or the campaign start), plus one minute |
| `ACTIVITY_OUTSIDE_SESSION` | Records fall outside the recorded session bounds |
| `SESSION_BOUNDS_NOT_RECORDED` | No session file exists |
| `SELF_REPORTED_MINUTES_UNKNOWN` | Some efforts record no minutes |
| `GRAPH_QUERIES_WITHOUT_GRAPH_TIME` | Graph queries were recorded, but no graph minutes were claimed |
| `GRAPH_TIME_WITHOUT_RECORDED_QUERIES` | Graph minutes were claimed, but no query was recorded |
| `GRAPH_MINUTES_EXCEED_OBSERVED_WINDOWS` | More graph minutes claimed than the observed review windows allow |

**Interpretation.** Derived values bound elapsed time between recorded actions; they do not measure effort. Idle time inside the span cannot be separated, and work before the first or after the last record is unobserved. Nothing is inferred there.

**R3, read only (a diagnostic; no R3 file, verdict or result changes):**

| Packet, arm | Observed span | Self-reported | Difference | Note |
|---|---:|---:|---:|---|
| P3-S | 11.05 | 21.25 | +10.20 | Over-logging, consistent with the R3 disclosure |
| P3-G | 13.48 | 14.40 | +0.92 | Not flagged |
| P4-S | 49.10 | 22.00 | −27.10 | Includes a 31.98-minute gap: the recorded interruption |
| P4-G | 15.87 | 23.68 | +7.81 | Flagged |

No R3 session bounds were recorded.

## 3. Full suggestion accounting: IMPLEMENTED, TESTED

`pilot suggestion-accounting PACKET [--export blind_v2.json]`; also `suggestion_accounting` in `pilot report`.

**Per class** (`ECONOMIC_CONNECTION_CANDIDATE`, `METHODOLOGICAL_WARNING`, `UNSUPPORTED_MATCH`, always all three):

- exported;
- logged suggestions and logged rows;
- logged rows by kind, and by decision: accepted, declined, unresolved;
- exported but unlogged;
- adjudicated outcomes, after unblinding.

**Each rate carries its numerator and denominator.** A zero denominator reads `UNDEFINED_ZERO_DENOMINATOR`, and missing data reads `UNKNOWN`, never 0.

**Discoveries.** Confirmed economic discoveries count only rows that are an `ECONOMIC_CONNECTION_CANDIDATE`, logged as a `CONNECTION`, `ACCEPTED`, `CONFIRMED_AGAINST_ORIGINALS` and `MEANINGFUL`. Warnings confirmed as useful are reported separately and never counted as discoveries; a mutation test forces this case.

**Traceability status:**

- `V2_FROZEN_EXPORT`;
- `V2_EXPORT_MISSING`, where exported counts are `UNKNOWN`;
- `NOT_TRACEABLE_V1`. R3 reads this way: its 10 graph-operator rows are reported as untraced, and exported counts are `UNKNOWN`.

## 4. Adversarial synthetic validation: TESTED (not a benchmark)

[graph_v1_1_adversarial.md](graph_v1_1_adversarial.md) (`python -m src.research.graph adversarial --check`).

The set has 11 tasks:

- reused citation;
- shared document used independently;
- two trivial shared identifiers (one regulator);
- a mismatched economic period;
- a misleading tag;
- a misleading tag on a genuine record;
- a genuine documented relationship;
- a genuine exact identifier;
- a name-only identity;
- a ticker-only identity.

I wrote the truths before running any system, and changed no operator afterwards.

| Measure | Graph v1 | Graph v1.1 | Structured search |
|---|---:|---:|---:|
| True positives (of 4) | 4 | 4 | 4 |
| False negatives | 0 | 0 | 0 |
| False positives | 4 | 2 | 4 |
| Identity or timing errors | 0 | 0 | 0 |
| Warnings kept as warnings (of 1) | n/a | 1 | n/a |
| Review load (all items shown) | 9 | 9 | 11 |

**Finding.** v1.1 still presents both trivial shared-identifier pairs as economic candidates, and structured search makes the same two errors. This confirms the limitation recorded in the v1.1 review. It is reported as found. A fix tuned on this set would not be validation.

## 5. Synthetic end-to-end dry run: TESTED

[graph_pilot_r4_dry_run.md](graph_pilot_r4_dry_run.md) (`pilot r4-dry-run --check`): 28/28 checks.

The pipeline runs end to end:

- a V2 packet frozen with a real pin from a throwaway git copy;
- graph queries saved to the frozen export, and V2 logs;
- session bounds and effort checks;
- suggestion accounting;
- blind, alias, leak-scan, a labelled synthetic adjudication stand-in, unblind, and the paired report (one pair, INCONCLUSIVE).

**Mutations, each refused or flagged:**

- a dirty, changed or added implementation file;
- missing git metadata;
- a snapshot pinned to other code;
- a V2 snapshot without a pin;
- an inflated effort;
- missing or assistant-recorded session bounds;
- graph time without queries;
- a missing export;
- a warning forced to "confirmed".

## 6. NOT_RUN (by design)

- **R4 itself:** activation, source preflight, packet formation, arm campaigns, real sessions, independent human adjudication, unblinding and the report.
- **No real-world data:** no real-world source request or acquisition of any kind.

## 7. Remaining Phase B gaps (NOT_IMPLEMENTED)

1. **Adjudicator exposure.**
   - Each adjudication row needs `EXPOSURE: SAW_ARM_INFO=YES|NO` with what was seen (arm ledger, log, session, key, AI assessment), generalising R3's owner-only `SAW_V001`.
   - The validator must refuse a missing note.
   - The report must mark the comparison potentially unblinded on any YES, and refuse any adjudicator who operated an arm.
2. **Two-reviewer agreement.**
   - A second, independent adjudication log against the same aliased export, recorded before either is unsealed.
   - Per-item agreement, kappa or raw agreement with its denominator, and the list of disagreements.
   - A rule that disagreements are reported and never resolved by an AI or by the operator.
   - An explicit owner choice of which log, or what rule, feeds the registered dimensions.
3. **Warning usefulness scoring.**
   - Warnings are still adjudicated with the connection outcomes, so "REJECTED_TRIVIAL" conflates "not an economic connection", which is true by construction, with "not useful".
   - Needed: a separate vocabulary (for example `USEFUL_LESSON_REUSED`, `USEFUL_NOT_USED`, `NOT_USEFUL`), with evidence of the avoided action, its own denominator, and a report dimension separate from discoveries.
4. **Also not implemented.**
   - Session-transcript checks: detecting a graph-assisted idea logged as analyst reading remains procedural.
   - Arm instructions for saving every suggesting query's output to `suggestions-G/` and for operator session files.
   - Pinning the arm sessions' runtime environment (Python and dependency versions) beyond the code.

## 8. Issues requiring owner decisions

1. **Effort threshold reading.** The draft says "above 10% or 5 minutes". Phase A applies it literally: either condition flags. Both conditions are reported separately. A "whichever is larger" reading, with 5 minutes as a floor, would flag far fewer short campaigns.
2. **Trivial shared identifiers.** Should a single identified object of a generic role (a regulator, an exchange) ground an economic candidate? Any rule needs a new, separately frozen evaluation, not this adversarial set.
3. **Gap reporting convention.** 30 minutes is unregistered, used for listing only. Should it be registered?
4. **Unrelated-commit policy.** Is content-identical `UNRELATED_COMMIT_CHANGE` acceptable for R4 arm sessions, or must sessions run at the exact pinned commit?
5. **Pinned set scope.** Is excluding `sec_pilot/parsing.py` acceptable, and should runtime dependencies be pinned too?
6. **Session bounds procedure.** Who records the bounds, and when? Phase A requires a human operator and refuses assistant-recorded bounds.
