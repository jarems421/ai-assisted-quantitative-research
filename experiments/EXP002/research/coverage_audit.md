# EXP002 pre-freeze coverage audit - revised 2026-10-11

**NEEDS DESIGN REVISION.** The [final design/runtime audit](design_revision.md) and [owner authorization](design_revision_authorization_20261011.md) supersede earlier primary cap/recency/liquidity axes. 2014 ownership warmup is now included. Current coverage counts are source diagnostics only: price-volume adjustment, exchange history and usable native joint signals remain unverified. A final usable Development start is still null.

## Previous coverage/runtime phase

**NEEDS DESIGN REVISION.** The [owner authorization](audit_authorization_20261011.md) supersedes the earlier cost stop: up to 1,000 included research tokens for this audit. Nineteen parameterized Lake jobs and two diagnostic daily backtests were submitted; 16 Lake jobs completed and three failed (two timeout/interruption attempts and a result-row limit). All exact SQL, parameters, IDs, failures, bounds and raw hashes are in [coverage_query_log.json](coverage_query_log.json). No candidate performance, ranking effectiveness, optimization, Aurora job, portfolio creation call, deployment or brokerage action was used. Outer Validation/Test were not queried or defined. Hypothesis remains DRAFT.


## Actual source coverage

The canonical panels contain 330,404 security-month price snapshots (2014 supplies price warmup) and 513,438 equity-source ticker-month aggregates for 2015–2020. Historical spans map ownership records to stable IDs at their New York availability date. Ambiguous/unresolved mappings are excluded: 24,930 source aggregate records failed this check. Another 5,775 security-month prices ended before the month's last observed session and are excluded from month-end eligibility. These are aggregate-record counts, not unique security/filing counts.

The table uses **annual unions of monthly IDs**, not average universe sizes. Proposed liquid means CS-coded security, unadjusted nominal price >= $5, 252 prior valid price rows, 20 prior valid volume rows and proposed trailing dollar volume >= $10m. Exchange/OTC, unique-session lineage and volume adjustment compatibility remain unresolved. Cap-present counts use the broader CS panel.

| Year | CS price IDs | Proposed liquid IDs | Cap-present IDs | 20-volume-row IDs | Insider source IDs within liquid | Institutional source IDs within liquid | Both within liquid | Insider % | Institutional % | Both % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 4,722 | 1,995 | 3,542 | 4,700 | 1,831 | 1,456 | 1,365 | 91.78 | 72.98 | 68.42 |
| 2016 | 4,818 | 2,034 | 3,655 | 4,787 | 1,873 | 1,555 | 1,462 | 92.08 | 76.45 | 71.88 |
| 2017 | 4,856 | 2,114 | 3,765 | 4,832 | 1,936 | 1,704 | 1,593 | 91.58 | 80.61 | 75.35 |
| 2018 | 4,880 | 2,208 | 4,003 | 4,847 | 2,037 | 1,882 | 1,771 | 92.26 | 85.24 | 80.21 |
| 2019 | 4,868 | 2,140 | 4,150 | 4,846 | 1,959 | 1,958 | 1,823 | 91.54 | 91.50 | 85.19 |
| 2020 | 5,069 | 2,285 | 4,334 | 4,993 | 2,053 | 2,111 | 1,932 | 89.85 | 92.39 | 84.55 |

Percentages use proposed-liquid annual unions. “Both” excludes cap and means an equity-source record in each proposed 90/365-day recency window, **not complete usable native joint signal coverage**. Insider source presence includes nonpurchase legs; institutional presence is SH non-option holdings. Native completeness, true zeros and revision safety remain unverified; usable joint counts stay null.

[coverage_summary.json](coverage_summary.json) has all 72 monthly snapshots, both denominators, cap-lineage counts and annual unions. Prices must exist on the latest observed common-stock session of each month. Availability is evaluated at calendar month-end New York, not Friday's close before weekend filings. Ownership history starts in 2015, leaving early rolling windows left-censored. UTC-bounded extraction conservatively excludes December 31 NY end-of-day filings represented on January 1 UTC. These limitations prevent a complete endpoint claim.

## Dates and draft revisions

Source records support investigating 2015–2020, with 2014 price warmup. **A final usable joint Development start is unresolved.** Supplement early ownership warmup, prove revision/identity/native parity and session/volume basis before selecting start/folds from coverage alone. No evaluation dates were selected from performance.

Native ROC Day matched elapsed-calendar first-after-boundary references in 20/20 cases and completed-session references in 0/20. Proposed horizons are now **180/365 calendar days**; new lengths and completed-bar lag remain to be confirmed. The nominal $5 filter now uses unadjustedClose. Native same-timestamp fills invalidate assuming automatic next-session execution. Institutional partial-quarter cohorts require redesign: AAPL had 43 Q4 reporting managers versus 2,144 Q3 managers public on January 8, 2016.

## Remaining gates

- Insider completeness, owner deduplication, true zero/missing semantics, amendments and private versus open-market P classification.
- Institutional public-quarter/cohort completeness, null amendment flags, restatement/addition handling and justified maximum staleness.
- Historical cap-share vintages, class scope, missing lineage and native Fundamental parity.
- Completed-bar/session uniqueness, price-volume adjustment basis, lagged DynamicRebalance scheduling, slippage and corporate-action/delisting execution.
- Historical exchange/OTC and subtype vintages, delisting reasons and native ALL_US_STOCKS parity.
- Prospective rebalance formulas/as-of lineage: not certified safe; no primary or executable robustness gate added.
- Observable token debit/account allowance, plus existing inference and freeze requirements.

See [PIT](pit_audit.md), [universe](universe_audit.md), [execution](execution_audit.md), [runtime](nexus_runtime_audit.md) and [cost receipt](cost_receipt.json). Raw receipts remain ignored under data/raw/EXP002/audit/raw/runtime_20261011/. Recompute local counts with `python -m src.research.coverage_exp002`. The initial cost-blocked attempt remains in provenance/query-log history.

## Conditional chronological folds

If joint PIT coverage supports 2015, a conditional five-fold expanding proposal is: train 2015/evaluate 2016; train 2015 through 2016/evaluate 2017; train 2015 through 2017/evaluate 2018; train 2015 through 2018/evaluate 2019; train 2015 through 2019/evaluate 2020. These folds are not executed or confirmed sufficient. Reconcile inner-selection boundaries, warmup, embargo and evaluation count before freeze. None accesses outer Validation. If coverage invalidates 2015, revise chronology from coverage only, before performance.


## Current revision coverage interpretation

2014 ownership warmup now supplies early rolling source-recency windows; all 72 monthly diagnostics are regenerated in coverage_summary.json. Previous tables describe the earlier audit snapshot and are preserved as history. Current annual diagnostics below still use the old unverified ADV basis; they are not primary universe sizes, native completeness or zero-activity evidence. Market cap is no longer required by the primary proposal. No coverage-based final inception is claimed until critical PIT/source, price warmup and execution gates pass.


| Year | CS IDs | Provisional liquid IDs | Insider within liquid | Institutional within liquid | Both within liquid |
|---|---:|---:|---:|---:|---:|
| 2015 | 4722 | 1995 | 1838 | 1460 | 1372 |
| 2016 | 4818 | 2034 | 1873 | 1555 | 1462 |
| 2017 | 4856 | 2114 | 1936 | 1704 | 1593 |
| 2018 | 4880 | 2208 | 2037 | 1882 | 1771 |
| 2019 | 4868 | 2140 | 1959 | 1958 | 1823 |
| 2020 | 5069 | 2285 | 2053 | 2111 | 1932 |
