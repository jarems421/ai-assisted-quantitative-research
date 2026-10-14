# EXP004 supplemental execution acquisition: source-key stop

**LOCAL_EXECUTION_INPUTS_BLOCKED — SOURCE_RECONCILIATION_BLOCKED. Hypothesis untested.** Starting HEAD `dea0f93adb12c0c21172b242b1800718f6d0bc67`, as of 2026-10-14. [Owner instruction](owner_exp004_supplement_2026-10-14.md) authorized same-source omitted execution-field acquisition and automatic local Development only after certification. The collector stopped at the mandatory exact-key gate; no performance or v004 PASS certificate exists.

## OPEN field acquired; exact source identity failed

One permitted schema description confirms `openingPrice` is a DOUBLE in `lake.sec_daily_ohlc`. Earlier archived EXP002 source queries already used it. The [28-request plan](exp004_supplement_acquisition_plan.json) was committed/pushed in `0c6f5b6` before dispatch. It preserves the exact original historical `security_segments` join, CS rule, dates and ordering, adding only `openingPrice` to the projected fields.

The first warmup quarter, **2013-12-31–2014-03-31**, completed as `lq_ffd1521c122f3200f148b6e0`. New requests, idempotency key, operation/status receipts, original Parquet bytes and part hashes are immutable under ignored `data/raw/EXP004/execution_inputs_v001/`. The prior 28 CLOSE-only extracts remain untouched.

| Reconciliation measure | Count |
| --- | ---: |
| Frozen / supplemental rows | 256,677 / 256,677 |
| Exact matched `(security_id,ticker,day)` keys | 256,615 |
| Missing frozen / extra supplemental keys | 62 / 62 |
| Duplicate excess rows: frozen / supplemental | 0 / 0 |
| Matched rows compared for CLOSE | 256,615 |
| Matched CLOSE mismatches | 0 |
| Frozen rows unpairable for exact-key CLOSE comparison | 62 |

All **62 identity substitutions concern VPG**, spanning 2013-12-31–2014-03-31. The ticker and date remain the same; the source assigns a different stable-ID string. Example observations:

| Ticker | Source day | Frozen stable ID | Supplemental stable ID |
| --- | --- | --- | --- |
| VPG | 2013-12-31 | `ticker:VSHw@2010-06-24` | `ticker:VSHw@2010-06-24#2` |
| VPG | 2014-01-02 | `ticker:VSHw@2010-06-24` | `ticker:VSHw@2010-06-24#2` |
| VPG | 2014-01-03 | `ticker:VSHw@2010-06-24` | `ticker:VSHw@2010-06-24#2` |

Equal counts do not certify equality. No `#2` stripping, issuer inference, alias rewrite, current-symbol lookup or exclusion of VPG was used to repair the mismatch. This establishes source-key drift under the tested same-source join; it does not establish whether the publisher changed namespace, class lineage or issuer identity. No fresh identity lookup followed. No empirical performance selected the stop.

The first diagnostic conflated projection-row differences with changed CLOSE values. Its original receipt remains immutable. The separately versioned replay correctly reports **62 missing/62 extra keys and zero matched CLOSE mismatches**; the failed population gate and stop remain unchanged. No CLOSE tolerance was introduced after inspection.

## Coverage and deferred gates

The fetched warmup part has **256,677 positive finite OPEN values, 0 missing and 0 invalid**. These are raw field checks, not nominal-share execution or full Development certification. Existing adjusted-price/share-unit evidence remains a separate requirement; a positive `openingPrice` alone does not certify the raw-share/cash-dividend ledger.

The remaining **27 quarters were not requested** after reconciliation failed. No Development execution OPENs were acquired. All 273,115 frozen common-population security-decisions remain pending acquisition, not 273,115 observed NULLs or invalid prices. SPY remains separate from CS and was NOT_ACQUIRED. Dividend events/source/pay-date semantics and actual-held-path terminal discovery were NOT_RUN at this upstream stop. Their counts remain unmeasured, never zero-dividend or zero-terminal claims.

**v004: BLOCKED / not issued.** No new execution freeze, real ledger, portfolio NAV, return, Sharpe, paired excess, winner or robustness was calculated. All 24 folds/six full replays remain NOT_RUN. Economic spec `32b216dd7d510399421d9ea89e61aff30c6b59aa8a4e0b31f5786615c1e6b3b9`, methodology `6bcb2a0c8513c06bfe4040275cfe6fa7f204b8e5844a80e36ed3e574560bee2a` and engine hash `11915121d3a3b4ff30866e31b7f832b5791e33dc060a296438ab83dfc4f0431b` are unchanged. The older [local OPEN-input stop](exp004_local_execution_report.md), freeze v001/v002, amended panels, Nexus failure, original Development report and closed EXP005/006/007 retain their bytes.

Source operations: **1 schema description, 1 completed price query, 11 SDK transport calls including status/manifest/download; zero automatic retries**. Polls are distinct from query submissions. SPY/dividend/lifecycle queries 0; backtests/publication/Aurora 0; purchases/upgrades 0. Actual account debit is UNKNOWN. Exact private HTTP bodies and byte hashes are retained; credential values/contact information are not committed.

**Validation accesses 0; Test accesses 0; real performance evaluations 0.** The 59-evaluation ceiling, earlier one diagnostic and 19 failure reserves remain unchanged. No global Nexus pause was removed. The narrowly allowlisted source client permits only frozen Lake acquisition endpoints and refuses continuation after the persisted reconciliation stop; legacy remote backtest/publication paths remain paused.

Validation: **472 local tests, 244 public tests, 0 skipped**. [Receipt](exp004_supplement_validation.json). [Canonical source review](exp004_supplement_source_review.json). Offline checks:

```sh
python -m src.research.exp004_supplement_report --check
python -m src.research.exp004_supplement_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

Public report regeneration requires tracked summaries only. Private audit requires the frozen/supplemental Parquet and original receipts and performs no network request. Acquisition requires `--execute` and is not reproduction; no stopped request is automatically resubmitted. Unrelated user files and dependency pins are unchanged. No new experiment, vendor, event-source discovery, Phase 4B, optimizer or paper/live activity occurred.

**Stopped under owner sections 5/20 at exact source-key reconciliation, before dividend/lifecycle certification or performance.** No repair mapping or further source campaign is adopted. Git checkpoints and hosted CI are delivery receipts reported separately.
