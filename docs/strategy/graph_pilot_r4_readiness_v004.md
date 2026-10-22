# Graph Pilot R4 readiness, Phase A timestamp corrections (version 004)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-readiness` (PR #3, unmerged). R4 is NOT_RUN, not activated and not authorised; Phase B has not started.**

This version records two timestamp corrections and one activation requirement. Everything in [version 003](graph_pilot_r4_readiness_v003.md) still holds unless amended here; versions 001–003 are unchanged.

**Untouched:** R3, the Graph v1.1 records, the v1.2 holdout, the generic register and Opportunity Scout.

[Timestamp corrections](graph_timestamp_corrections_2026-10-22.json) · [R4 graph configuration V002](graph_pilot_r4_graph_configuration_v002.json) · [Validation](graph_pilot_r4_readiness_validation_v004.json)

## 1. Commit-date rule: no tolerance

**The finding.** `validate_execution_provenance()` accepted a live packet's running commit dated up to 5 minutes after the query. It had reused `ATTESTATION_LAG_MINUTES`, the human-attestation tolerance, which contradicted the documented "no later than the query" rule.

**The correction:**

- The allowance is removed. The commit's declared date must be at or before the query time.
- No clock-skew rule is registered, and the attestation lag is deliberately not reused.
- Exact-boundary tests show that a commit dated exactly at the query passes, while one dated 1 second later, or 4 minutes 59 seconds later, is refused. A mutation that restores the 5-minute allowance is caught.

**Consequence.** Pilot machines need a synchronised clock. A commit made on a machine whose clock runs ahead could otherwise make a genuine query fail this check. That failure is safe: it refuses rather than passes. Adding any skew allowance would need a separately justified, prospectively registered rule.

## 2. Hand-entered recorded times later than their own commits

| File | `recorded_at_utc` as written | Introducing commit (committer date) | Action |
|---|---|---|---|
| `graph_pilot_r4_graph_configuration_v001.json` | 2026-10-22T12:00:00Z | `3bf0474` (11:03:15Z) | Preserved unchanged; superseded by V002 |
| `graph/generic_identifiers_v001.json` | 2026-10-22T10:30:00Z | `426c211` (10:23:16Z) | Preserved unchanged: it is frozen by hash, and the owner directed it stay unchanged |

**What happened.** I entered both values as rounded times. Neither was an observed time, and neither was an intended effective or future time. The clock-generated validation receipts were checked and all precede their commits.

**What changed:**

- **Configuration V002** has the identical configuration. Its `recorded_at_utc` is the real write time (11:11:04Z, before its commit), and it also records:
  - `configuration_first_committed`: commit `3bf0474` and its date, the upper bound on when the configuration content was first authored;
  - `supersedes`: V001 by hash, with the reason;
  - `owner_decision`: the exact decision time is not recorded.

  `pilot.load_r4_configuration()` now loads V002.
- **The register** keeps its incorrect `recorded_at_utc`. Read it as unreliable: the time evidence is its introducing commit. The registration order relies on commit ancestry, not on that field.
- **A regression test** checks that hand-recorded times in V002 and in the correction record are no later than the commits that introduced them; in CI it fails if either file is uncommitted. It also checks that both defective files are preserved byte-for-byte, that their defects are real, and that V001 and V002 configure the same thing.

## 3. Activation requirement: non-conforming snapshots

A V2 snapshot records `r4_configuration.conforms`. A snapshot with `conforms: false` was frozen with a configuration other than the registered one, for example `--classification GRAPH_CLASSIFICATION_V1_1`.

**For Phase B and activation:** such a snapshot must never be treated, silently or otherwise, as a conforming R4 experimental packet. Before an R4 report counts a packet, the activation must refuse it, or list it explicitly as a deviation with the owner's written reason. The current code records the flag but does not yet refuse it. Making it refuse is an activation-tooling item.

## 4. Remaining blockers

None technical, provided that:

1. the owner gives final approval;
2. CI passes on the final commit, with the ordering and timestamp tests running;
3. the PR is merged with a **merge commit**, not a squash or rebase, so that `426c211`, `3bf0474` and the later commits remain in `main`'s history.
