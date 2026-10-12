# Phase 3B: proposed trial and inference ceiling

**DRAFT_NOT_REGISTERED_NOT_FROZEN. Zero trials executed or authorized.** The [design](phase3b_design.md) proposes exactly one revenue family and one transform: difference of adjacent annual growth rates from three original snapshots. No secondary family, alternative denominator, normalization/winsorization, lookback, holding-period, K or universe search is reserved.

| Fixed choice | Ceiling |
| --- | --- |
| Filing family / transform | 1 / 1 |
| Holding/rebalance schedule | One month renewable; monthly first session |
| Cardinality / exposure | Top20 / 95%, same as momentum and no-information control |
| Momentum | One 252-to-21-session total-return definition |
| Cost scenarios | Base30bps/side and stress60bps/side |
| Timing scenarios | Base; +1 and +5 execution sessions |
| Strategy paths | 30 planned + 6 failure/unresolved reserve = **36 maximum** |
| Contribution diagnostics | 3 per stage × 3 stages = **9 maximum** |
| Total performance evaluations | **45 maximum**, encompassing local and remote work |

These are an additive list, not a Cartesian grid. Reserve slots may reconcile or replace failed attempts under the same frozen design; they cannot add a new economic parameter. Every genuinely new submission/analysis attempt uses a slot, including failure before results, partial population, poor outcomes and unresolved jobs. Re-fetching an existing immutable result by the original key is not a new strategy trial. Never resubmit an uncertain operation before reconciling its original ID. A reconciled failed attempt remains consumed.

## Exact inventory

| Stage | Base paths | Stress paths | Subtotal |
| --- | --- | --- | ---: |
| Development | Revenue, matched momentum, eligible-universe EW, fixed-seed no-information | Revenue + momentum for doubled cost; revenue + momentum for +1 session; revenue + momentum for +5 sessions | 10 |
| Validation | Same four frozen paths | Same six frozen stress paths | 10 |
| Owner-authorized Test | Same four frozen paths | Same six frozen stress paths | 10 |
| Failure/unresolved reserve | No new family or scenario | Six attempted evaluations maximum across all stages | 6 |

Each row refers to a complete funded window. Reporting six fixed Development years or three Validation/Test years from one complete tape is a prespecified decomposition, not permission to submit extra fold jobs. An independently funded extra fold, cost recomputation or additional realized strategy comparison consumes a slot; no unused reserve can legitimize an undeclared hypothesis. Inference on joint Validation+Test is one predeclared analysis of already counted paths, not another simulation.

The nine fixed local contribution evaluations are: exclude top1 issuer contribution, top5 issuer contributions, and top5 positive daily contributions, once for the primary paired base difference in each stage. Each gets its own durable analysis key and retains its result even if negative. These are additive accounting diagnostics, not rebalanced replacement portfolios. A trade-rerun after exclusions would be a different strategy and is prohibited.

Three block lengths252/126/504 with10,000 draws and seed3003001, fixed metric reports, source/coverage audits, yearly partitions and descriptive beta/exposure summaries are deterministic prespecified summaries, not candidate searches. Record their configuration/result hashes under the originating trial; no seed or interval selection. Development and Validation intervals remain descriptive. At most four null-confirmatory tests on the unchanged joint Validation/Test path are proposed; no bootstrap draws count as independent observations or additional alpha families. The future null-test implementation/calibration must be independently verified before freeze.

## Ledger and family accounting

Use existing [durable job/trial journal](../../src/research/store.py), [budget planner](../../src/research/budget.py) and [stage gates](../../src/research/spec.py) only after a separately authorized real registration. Add future non-remote analyses to the same auditable ledger with parent strategy key, source/spec/policy/engine hashes, stage, family, parameters, scenario, status and actual/unknown cost. Never instantiate that store or register EXP005 as part of this planning task. Current token pricing is not refreshed and no remote cost authorization is inferred.

Same family means this exact acceleration mechanism on the fixed original-snapshot contract. The three declared stress pairs are robustness, the fixed-seed no-information path is ablation, and the universe-EW path is a control. A new denominator basis, revenue taxonomy fallback, availability assumption after results, family, momentum lookback, K, cutoff/liquidity threshold, holding schedule, universe or execution engine creates a new performance-informed trial and may require a new experiment. A genuinely new mechanism always requires a new reviewed experiment; this ceiling never resets and earlier failures must be disclosed across subsequent research.

Selection is pass/fail for one predeclared candidate, not ranking candidates by Sharpe. Gross results cannot select over net results. Historical Development finding then source/code amendment requires preserved old evidence and a counted, reviewed revision; Validation/Test may never retune. Pre-performance source-only changes require a new draft/version and owner review before any performance access.

## Statistical and economic contract

Primary net annualized paired mean floor2percentage points; year-sign requirements4/6Development,2/3Validation; doubled-cost/+1/+5 effects positive. Descriptive paired annual-block intervals are not p-values. Formal inference awaits all lawful joint Validation/Test evidence, adequate dependence/coverage and pre-freeze null calibration. One-sided null-centered paired mean tests form a fixed four-effect Holm family at alpha0.05; failed/unresolved p-values1 stay in family. Primary adjusted p<=0.05, positive primary descriptive lower bound and all declared falsification/robustness gates are required for support. Stresses are not alternate winners. Inadequate evidence is inconclusive, not a search-expansion permission.

Stop at any critical source/identity/availability/runtime failure. Budget ceilings do not authorize work or override sealed stages. No performance evaluation, including a reserve attempt, has occurred in Phase3B.
