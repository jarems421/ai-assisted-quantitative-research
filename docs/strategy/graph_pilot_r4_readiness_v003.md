# Graph Pilot R4 readiness, Phase A final correction (version 003)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Branch `graph-pilot-r4-readiness` (draft PR #3, unmerged). R4 is NOT_RUN, not activated and not authorised; Phase B has not started.**

This version adds the execution-provenance validator, records three owner decisions, and makes CI verify the v1.2 registration order. [Version 002](graph_pilot_r4_readiness_v002.md) and [version 001](graph_pilot_r4_readiness_v001.md) stay unchanged as history; everything in v002 still holds unless amended here.

**Untouched:** R3, the Graph v1.1 evaluations and Opportunity Scout.

[R4 graph configuration](graph_pilot_r4_graph_configuration_v001.json) · [Synthetic dry run](graph_pilot_r4_dry_run.md) (51/51) · [v1.2 registration](graph_v1_2_rule_registration.md) · [v1.2 holdout](graph_v1_2_holdout.md) · [Validation](graph_pilot_r4_readiness_validation_v003.json)

## 1. Saved execution provenance: IMPLEMENTED, TESTED

**The finding.** `receipt_core()` drops the receipt's `implementation_check`, so that a replay may legitimately run later at a content-identical unrelated commit. As a result, `load_suggestion_exports()` did not validate the saved running-commit metadata at all.

**The fix.** Every visibility receipt of a pinned packet now saves an execution-provenance record: `{status, running_commit, dirty_pinned_paths}`, where the last field lists pinned files uncommitted at query time. `validate_execution_provenance()` checks this record separately from replay, for every saved output, before blinding. It runs again at unblinding and report time. Its result is sealed in the blinding key's export manifest.

**What is refused:**

| Problem | Example |
|---|---|
| Missing | No `implementation_check` in the receipt |
| Malformed | A missing or extra field; an unknown status; a running commit that is not 40-hex; dirty paths that are not a sorted list of pinned files |
| Inconsistent | `EXACT_COMMIT` when the running commit is not the pinned commit, or the reverse; `GIT_UNAVAILABLE_CONTENT_VERIFIED` that still names a commit or dirty paths |
| Modified | A running commit not in this repository; one whose pinned files differ from the pin at paths other than the declared dirty ones; for live packets, one dated after the query |

**Legitimate replay is preserved.** The record is validated against the repository's history, not against the current HEAD. Replay after HEAD has moved to an unrelated commit, with identical pinned code and runtime, is accepted; both a regression test and the rehearsal check this. A focused test shows that changing only `running_commit`, status or dirty paths, with every other field intact, is refused before sealing.

**What the validator establishes:**

- the saved record is well formed and consistent with the snapshot pin;
- the named commit exists in this repository and is dated no later than the query, by its self-declared committer date;
- that commit's pinned files differ from the pinned content exactly at the declared uncommitted paths.

Together, these mean the commit could have run the pinned code.

**What stays procedural:**

- that the query actually ran at that commit;
- a git commit, its date and local history are self-reported; they are not cryptographic or external attestation;
- a fabricated record naming another commit that is consistent in this way cannot be told apart from a real one. A test demonstrates this limit explicitly.
- the date check applies to live packets only; synthetic rehearsals use a fixed synthetic clock and report `NOT_APPLICABLE_SYNTHETIC_CLOCK`.

## 2. Owner decisions, recorded

1. **Proposed R4 graph configuration, frozen prospectively.** [graph_pilot_r4_graph_configuration_v001.json](graph_pilot_r4_graph_configuration_v001.json) sets:
   - `GRAPH_OPERATORS_V1_1` with `GRAPH_CLASSIFICATION_V1_2`;
   - the generic register V001 by hash;
   - V2 connection logs;
   - pin V002.

   `pilot.load_r4_configuration()` refuses if the register no longer matches. V2 snapshots now default to this configuration and record `r4_configuration.conforms`; an explicit `--classification GRAPH_CLASSIFICATION_V1_1` is recorded as a deviation. Outside R4 snapshots, v1.1 stays the default. The v1.1 quality, adversarial, walkthrough and R2 dry-run records, and R3, are unchanged.
2. **No register tuning.** `generic_identifiers_v001.json` is unchanged since the rule commit `426c211`, and a test checks this. Holdout H7 stays an observed limitation. Any expansion needs independently grounded identifiers or taxonomy, a new register version and a new prospective evaluation.
3. **The strict boundary is accepted.** The over-approximating static closure of pin V002 is accepted for R4, with the requirements in §3.

## 3. Environmental stability requirements for R4 (strict boundary)

1. **One frozen checkout.** Every arm query, export save, blinding, unblinding and report runs from a checkout whose pinned-closure content equals the pin:
   - graph, discovery, `spec.py`, the R4 fetch tool and `sec_pilot/parsing.py`;
   - the lazily imported `exp004_policy`, `exp002_contracts` and `pit_signals`.

   Editing any of them during the pilot refuses every pinned operation. Unrelated paths, such as Opportunity Scout and docs, may change; that passes only as `UNRELATED_COMMIT_CHANGE`, with identical pinned content.
2. **One Python environment.** The same Python version (major, minor and micro) and implementation, and the same versions of the recorded distributions: `jsonschema`, `nexustrade` and `tzdata`, with `edgar` and `lxml` absent as pinned. No package installs, upgrades or removals during the pilot. A dedicated virtual environment, with its full package list recorded at activation, is recommended.
3. **Git metadata and history kept.** Freezing needs a clean pinned set in a git checkout. Validating saved provenance needs every commit named in a receipt to remain in the repository. So there must be no shallow clones, rebases, history rewriting or squash merges that remove those commits.
4. **Not covered by the pin:**
   - the operating system and hardware;
   - the standard-library implementation beyond the Python version;
   - network conditions for acquisition, which go through the receipted `fetch_one.py` path.

## 4. CI verifies the v1.2 registration order

**Before.** The ordering test skipped on GitHub's default shallow checkout (`fetch-depth: 1`).

**Now.** `.github/workflows/public-synthetic.yml` checks out full history (`fetch-depth: 0`). Under `GITHUB_ACTIONS`, the test fails instead of skipping if history is unavailable. It verifies that:

- rule commit `426c211` is an ancestor of HEAD;
- the registration document and register existed at that commit;
- the holdout module and record did not;
- the register is unchanged since.

**Merge note.** This ordering evidence lives in the branch's commits. A squash or rebase merge would remove `426c211` from `main`, and the test would then fail. **Merge PR #3 with a merge commit**, as for PRs #1 and #2.

## 5. Status summary

| Item | Status |
|---|---|
| Implementation pin V002 (boundary, runtime, uniform enforcement) | IMPLEMENTED, TESTED |
| Saved execution-provenance validation | IMPLEMENTED, TESTED |
| Effort evidence, attestations, primary measure and gate | IMPLEMENTED, TESTED |
| Suggestion accounting (row and suggestion levels) | IMPLEMENTED, TESTED |
| R4 graph configuration (V1_1 operators + V1_2 classification) | REGISTERED (proposed), TESTED |
| v1.2 holdout | TESTED; supported on this holdout; not an independent benchmark |
| Adjudicator exposure, two-reviewer agreement, warning usefulness | NOT_IMPLEMENTED (Phase B) |
| R4 | NOT_RUN |

## 6. Remaining issues (unchanged from v002 unless noted)

- **Accepted:** the pin boundary's over-approximation (§3).
- **Unchanged from v002:**
  - per-process memoisation of content, runtime and git state;
  - self-declared attestation timing;
  - the minimal generic register (H7);
  - the weaker adjudicator name check (Phase B);
  - the pre-existing flaky SEC-pilot concurrency test.
- **New, procedural:** execution provenance is consistency with the repository's history, not proof (§1).

## 7. Merge blockers

None technical, provided that:

1. the owner reviews the draft PR;
2. CI passes with full history, so the ordering test runs rather than skipping;
3. the PR is merged with a merge commit, not a squash or rebase.

Phase B scope is unchanged from v002 §7.
