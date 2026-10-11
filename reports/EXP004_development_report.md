# EXP004 Development — frozen, input QA blocked

**No Development performance results exist.** The owner approved the exact reviewed specification and methodology. The audit passed and `freeze-hypothesis` completed before preparation. Freeze checkpoint: `efc3626` on `main`, pushed to GitHub. No candidate or benchmark backtest, custom publication, performance query or held-out read was performed.

Frozen hypothesis: medium-term cross-sectional price momentum improves net mean daily return and zero-RF Sharpe versus monthly equal-weight ownership of the same historical source-defined common-equity universe, with directionally consistent chronological held-out Development folds.

| Frozen artifact | SHA-256 |
|---|---|
| Specification | `88fec6e53e14939d3a40fa8f55170ad40712f5b1b8ff7e2c5c9002a4d2ef185d` |
| Methodology | `caf07509c04a9b703725983482e7502c03616b1ab27bdc5287148fdcca9b6328`; file mapping in [freeze receipt](../experiments/EXP004/freeze_receipt.json). |

The reviewed specification bytes, source-universe definition, costs, four cells, benchmarks, statistical definitions and selection contract remain unchanged. Development is 2015-01-02–2020-12-31; outer Validation 2021–2023 remains unopened. Sealed ranges are 2024-01-01–2024-12-31 and 2025-01-01–9999-12-31. No later observations may repair Development inputs.

## Input QA

The [Development manifest](../experiments/EXP004/development_input_manifest.json) binds all 72 monthly decision dates, inherited source receipt hashes, per-date universe/history prerequisite counts, four cells and fold boundaries to the freeze. Each decision currently fails **MISSING NUMERIC INPUT**. Completed-price counts are not prices: they cannot produce exact split-safe 180/365-day momentum, numeric ranking values or selected top K. The existing small diagnostic price/split samples do not cover the frozen source population. No absent value becomes a zero or an invented rank.

Required production inputs are immutable numeric nominal completed prices and effective split lineage, with as-of availability and historical identity/session reconciliation. After extraction, complete per-decision QA must prove eligible counts, stable identities, no ambiguous/duplicate identity, both horizon values, exact ranks/top K, completed-bar availability and no future bars. The local preparation gate rejects incomplete evidence before submission. Unpublished SDK fixture IDs cannot be used for a run.

The reviewed budget is zero. Dated daily non-options backtest estimates are zero, but they do not establish the cost of additional Lake extraction/custom publication. An explicit included-token preparation ceiling is pending; old experiment allowances are not transferred and no credit purchase is authorized. This is an operational input/cost stop, not a strategy redesign or a new generic source audit.

## Four-cell surface

| Cell | Independent metrics | Paired EW/SPY effects | Turnover / participation | Nexus ID |
|---|---|---|---|---|
| M180/K20 | Not run | Not run | Not measured | None |
| M180/K40 | Not run | Not run | Not measured | None |
| M365/K20 | Not run | Not run | Not measured | None |
| M365/K40 | Not run | Not run | Not measured | None |

## Fold and benchmark programme

| Earlier history | Scored year | Four cells + EW + SPY |
|---|---|---|
| 2015–2016 | 2017 | All six unsubmitted |
| 2015–2017 | 2018 | All six unsubmitted |
| 2015–2018 | 2019 | All six unsubmitted |
| 2015–2019 | 2020 | All six unsubmitted |

Both explicit SPY and monthly entire eligible-universe benchmarks remain unsubmitted. There are **0 runs and no run IDs**; the frozen plan has 24 scored-fold jobs, six full-Development replays and the later conditional stages/reserve. Withholding SPY avoids producing an unmatched partial programme while the shared input panel is unavailable.

## Selection, stability and robustness

Selection is **not evaluated**. This is not `NO EXP004 CANDIDATE ADVANCES`: that verdict requires the completed four-fold evidence and frozen eligibility rule. No winner is selected. Neither isolated optima nor horizon/holding sensitivity, fold signs or turnover can be measured without returns/events.

Local additional 10/20-bps cost stresses and the one-session-delay test have not run. They remain separate from base results and may not be used to change definitions or loosen eligibility. Regime decomposition likewise has no observations. Every failure/unknown remains explicit; nothing is reported as economic falsification or confirmed alpha.

Source-population coverage, vendor revisions, historical knowledge, simulated fills/corporate actions, effective deployment, capacity and selection bias retain their frozen limitations. No universe or alpha parameter changed to solve the input failure.

Reproduce preparation locally with `python -m src.research.prepare_exp004`; this performs no Nexus operations. The freeze and raw preparation receipt are immutable. Stop before affected runs and before outer Validation.

Validation: 147 software tests passed; semantic audit passes at HYPOTHESIS_FROZEN; six presentation artifacts are deterministic. Input QA remains failed and is not overridden by software checks.
