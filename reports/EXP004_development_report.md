# EXP004 Development — frozen, input QA blocked

**No Development performance results exist.** The owner approved the exact reviewed specification and methodology. The audit passed and `freeze-hypothesis` completed before preparation. Freeze checkpoint: `efc3626` on `main`, pushed to GitHub. No candidate or benchmark backtest, custom publication or performance query was performed. Nine authorized source Lake jobs completed; Nexus source bounds stayed pre-2021. Incidental later web-search references are disclosed in provenance, never used.

Frozen hypothesis: medium-term cross-sectional price momentum improves net mean daily return and zero-RF Sharpe versus monthly equal-weight ownership of the same historical source-defined common-equity universe, with directionally consistent chronological held-out Development folds.

| Frozen artifact | SHA-256 |
|---|---|
| Specification | `88fec6e53e14939d3a40fa8f55170ad40712f5b1b8ff7e2c5c9002a4d2ef185d` |
| Methodology | `caf07509c04a9b703725983482e7502c03616b1ab27bdc5287148fdcca9b6328`; file mapping in [freeze receipt](../experiments/EXP004/freeze_receipt.json). |

The reviewed specification bytes, source-universe definition, costs, four cells, benchmarks, statistical definitions and selection contract remain unchanged. Development is 2015-01-02–2020-12-31; outer Validation 2021–2023 remains unopened. Sealed ranges are 2024-01-01–2024-12-31 and 2025-01-01–9999-12-31. No later observations may repair Development inputs.

## Input QA

The owner's subsequent authorization allowed included research tokens for bounded production preparation, then lifted the numerical 2,000-token cap. No frozen specification/budget field changed and no credit purchase occurred. See [authorization](../experiments/EXP004/research/input_preparation_authorization.json).

Nine Lake jobs completed: eight quarter-sized CS nominal-price extracts covering 2013-12-31 through 2015-12-31 (2,189,960 rows), plus a 2013-12-31?2020-12-31 split extract (8,149 rows). Two packed-array SQL submissions were rejected without job IDs and are retained. All source parameters, IDs, immutable receipts/Parquet hashes and 38 logged transport calls are in the [query ledger](../experiments/EXP004/research/production_query_log.json). No precise Lake cost quote or debit appeared in receipts: charges remain unknown, not zero. This stop is about source integrity, not budget.

Local numeric QA generated all 12 monthly 2015 panels under the frozen completed-session, historical-identity and split-safe calculation. Eligible counts range 3,553?3,736. Compared with prior count-only prerequisites, strict calendar/positive-price and historical lookback-identity checks produce additional explicit exclusions; no new financial screen was added. Exact numbers, stable-ID rankings and top K targets remain private with hashes. These are input data, not performance. Later full numerical panels remain unbuilt after the critical failure.

**Critical gate: ambiguous same-date split lineage.** The table exposes only ticker, executionDate, splitFrom and splitTo; it has no event/version/public-availability identity. A focused current-catalog check found no alternate split event/version table. Three active CS histories have distinct same-date factors:

| Security | Source effective date | Factors | Affected predeclared decisions |
|---|---|---|---|
| LADR | 2015-12-08 | 1.126853 and 1.097582 | 2016 monthly decisions; full-Development replay |
| BTX | 2016-06-17 | 2.0 and 0.01 | 2016-07 through 2017-06; scored 2017 |
| ALEX | 2017-11-28 | 1.5741279154 and 1.42 | 2017-12 through 2018-11; scored 2017/2018 |

Multiple rows may represent real sequential legs or unresolved vendor revisions/identity errors. Neither choosing one nor compounding all is certified by this schema. The frozen helper multiplies intervening factors; without authoritative event lineage, production use cannot establish the intended split-continuous price contract. Three other CS same-date groups do not enter the saved monthly eligible windows and are not presented as active blockers.

ALEX's 2017 issuer announcement says the stock distribution amount depended on prices following a January 2018 election deadline. This does not identify which Nexus row is correct, but reinforces that a November-dated adjustment must have a verified as-of basis rather than assumed availability. [Issuer announcement](https://investors.alexanderbaldwin.com/2017-11-16-Alexander-Baldwin-Declares-783-Million-Special-Distribution), [SEC accompanying materials](https://www.sec.gov/Archives/edgar/data/1545654/000154565417000073/a3-accompanying_materials.htm).

The [split QA receipt](../experiments/EXP004/research/production_split_qa.json) preserves exact rows, affected windows and inference boundaries. No heuristic ratio selection, new ticker exclusion, rewritten source response or alpha redesign occurred. The [input manifest](../experiments/EXP004/development_input_manifest.json) remains blocked and prevents submission. Production custom streams were not created. A corrected/certified event and availability lineage under the existing methodology is required; otherwise a separately reviewed design revision would be needed, which this task does not authorize.

A targeted pre-cutoff issuer search returned incidental later dividend-page references; these were excluded, and no linked post-cutoff page was opened. Exact primary pages opened describe 2017/2018 events only. No 2021+ Nexus observation, Validation job or Test job occurred. The exposure note is retained rather than claiming all web responses contained only pre-cutoff text.

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

Both explicit SPY and monthly entire eligible-universe benchmarks remain unsubmitted. There are **0 runs and no run IDs**; the frozen plan has 24 scored-fold jobs, six full-Development replays and the later conditional stages/reserve. Withholding SPY avoids producing an unmatched partial programme while the shared source split lineage is uncertified.

## Selection, stability and robustness

Selection is **not evaluated**. This is not `NO EXP004 CANDIDATE ADVANCES`: that verdict requires the completed four-fold evidence and frozen eligibility rule. No winner is selected. Neither isolated optima nor horizon/holding sensitivity, fold signs or turnover can be measured without returns/events.

Local additional 10/20-bps cost stresses and the one-session-delay test have not run. They remain separate from base results and may not be used to change definitions or loosen eligibility. Regime decomposition likewise has no observations. Every failure/unknown remains explicit; nothing is reported as economic falsification or confirmed alpha.

Source-population coverage, vendor revisions, historical knowledge, simulated fills/corporate actions, effective deployment, capacity and selection bias retain their frozen limitations. No universe or alpha parameter changed to solve the input failure.

Reproduce preparation locally with `python -m src.research.prepare_exp004`; this performs no Nexus operations. The freeze and raw preparation receipt are immutable. Stop before affected runs and before outer Validation.

Validation: 151 software tests passed; semantic audit passes at HYPOTHESIS_FROZEN; six presentation artifacts are deterministic. Production split QA remains failed and is not overridden by software checks.
