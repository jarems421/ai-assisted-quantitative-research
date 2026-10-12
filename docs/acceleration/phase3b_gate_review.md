# Phase 3B: gate review and stop

**Design completed; EXP005 freeze is NOT_READY.** As of 2026-10-12. [Revenue design](phase3b_design.md), [source requirements](phase3b_source_requirements.json), and [trial budget](phase3b_trial_budget.md) are non-executable planning artifacts. No experiment was registered or frozen.

| Gate | Verdict | Evidence / remaining requirement |
| --- | --- | --- |
| HYPOTHESIS_DESIGN | READY | One falsifiable revenue-acceleration hypothesis, matched momentum, competing explanations and stop rules. |
| PRIMARY_SIGNAL_SEMANTICS | PARTIAL | Individual annual revenue observations certified; three-original accounting/rounding/perimeter comparability not certified. |
| SOURCE_COVERAGE | PARTIAL | Three existing filings; no issuer has the required pilot triple or population-scale coverage. |
| PUBLIC_ELIGIBILITY_POLICY | PROPOSED | No owner approval. Exact public time UNKNOWN. Existing v001 remains unchanged. |
| HISTORICAL_SECURITY_IDENTITY | PARTIAL | AAPL/FB Class A provisional point evidence; class/listing/lifecycle bridge unresolved. |
| HISTORICAL_UNIVERSE | BLOCKED | No certified source-defined population/coverage denominator, liquidity panel or terminal-value contract. |
| EXECUTION_ROUTE | BLOCKED | Existing Nexus population pruning unresolved; no new call or alternative engine implemented. |
| TRIAL_AND_INFERENCE_DESIGN | PARTIAL | Exact45-evaluation ceiling; descriptive bootstrap reusable. New null-test calibration and ledger/selection adapter must pass before freeze. |
| EXP005_FREEZE_READINESS | NOT_READY | Missing source, policy, identity, calendar, execution and inference certificates plus separate owner authorization. |

## Timestamp property, without promotion

The offline metadata-only probe/test in [planning.py](../../src/research/sec_pilot/planning.py) and [tests](../../tests/test_sec_phase3b_planning.py) preserves unknown public time and unapproved policy. Both October candidate instants map to the same illustrative eligible open for the fixed filings; a near-midnight synthetic case gives different opens unless the later filing date covers the rollover. Holiday/weekend/DST/calendar failures are tested. This is a property of calendar mechanics only. Source timestamp evidence is unchanged, October certification remains PARTIAL, and the current policy's certified-acceptance gate is not bypassed. A separately approved ambiguity-tolerant version and complete-population probe would be necessary to use this alternative in trading eligibility.

## Decisions still required

Owner review should first decide whether to commission a bounded **source-only** certification of three-original revenue comparability and dated class/listing identity, and whether to approve a separately versioned modeled availability policy after reviewing timing uncertainty. This document supplies no approval. Review the fixed monthly top20, capital/liquidity/cost assumptions, conditional dates and small budget before any performance access. The six-year joint confirmation requirement means a three-year Validation result alone cannot establish significance; some proposed dates are future and calendar/source coverage remains conditional.

Execution requires a population-preserving route certificate and separate authorization, not merely a policy approval. Independent null-test calibration and stage-safe source/selection adapters are needed before a real freeze. If coverage forces a source-only revision, preserve this draft and issue a reviewed version before returns. Do not solve infeasibility by survivor filtering or post-result parameter changes.

## Verification scope

**Executed: 206 tests passed, zero skipped.** The three new public calendar tests pass; existing203 regression tests pass. Legacy tests read already-opened EXP001 local records only for regression, not new research or strategy-return inspection. Additional passing checks:

```sh
python -m src.research.sec_pilot.phase3a --check
python -m src.research.sec_pilot report --check
python -m src.research.support_case --check
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

The pre-task SHA-256 inventory covers376 pre-existing tracked/source/snapshot/processed/state files against checkpoint `16756ec`. All374 preserved files match; only the two deliberately updated README/template files differ. Phase1/2/3A evidence, private archived SEC bodies/receipts/snapshots, frozen experiment artifacts, canonical processed baselines and operational pause are unchanged. Read-only SQLite verification finds no EXP005 registration; EXP004 remains HYPOTHESIS_FROZEN and its separate operational pause is intact. Full Phase3A regeneration still reports zero approved real policies and the same15 scoped observations. Presentation verifies all six deterministic artifacts. Logs and the inventory remain ignored under `.research/`; no contact details or private raw content enter tracked outputs. These are scoped local checks, not an independent account-wide audit.

The four new design documents need no private data to read; planning tests use public metadata and offline calendar rules only. Commit/push receipts are reported in the delivery message rather than embedded as self-referential hashes.

No SEC filing acquisition, real signal computation, return/performance inspection, Nexus call, purchase, Validation/Test opening, EXP005 creation/freeze, optimization, paper/live action or automatic next-phase transition occurred. **Stopped after Phase3B.**
