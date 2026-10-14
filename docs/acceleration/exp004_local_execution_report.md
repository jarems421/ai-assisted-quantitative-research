# EXP004 local execution: frozen input boundary stop

**LOCAL_EXECUTION_BLOCKED — LOCAL_EXECUTION_OPEN_PRICES_BLOCKED. Hypothesis untested.** Starting HEAD `34c5b7595ddd30bc67627c4d61638a91a62e4efd`, as of 2026-10-14. [Owner instruction](owner_exp004_local_execution_2026-10-14.md) authorizes local-only Development after a passing, pushed pre-performance certificate. [This certificate](exp004_local_execution_certificate_v003.json) records a failed input gate, not permission to calculate performance. Earlier failed receipts/prototypes are retained: version 2 adds the core-ledger entry guard; version 3 keeps SPY's explicit ETF binding separate from the candidates/EW CS population. Neither changes inputs or economics.

## Concrete blocker

All **28 frozen price extracts / 7,871,192 rows** contain exactly `ticker`, `day`, `security_id`, `unadjustedClose`. **None contains execution OPEN prices.** Their original SQL explicitly projected completed closes; the source table's OHLC name is not evidence that omitted columns were downloaded. The split extract contains 8,149 rows with ticker, effective date and split operands only.

The local route cannot execute the frozen first-session 09:30 OPEN orders using these bytes. A prior close, same-day close, guessed OPEN or another vendor would change the execution contract. No such substitution occurred. The failure already applies at 2015-01-02 inception, before any actual position, dividend entitlement or terminal event exists.

All **72 monthly panels / 273,115 eligible security-decisions** were hash-verified. Exact stable IDs, both horizons, rankings and frozen Top-K targets reconcile, including historical prior/execution ticker bindings. This is source-input reconciliation. Locally executable population equality remains BLOCKED because every eligible execution OPEN is unavailable; it is not a passing runtime certificate. Every intended EW identity is retained, not pruned. The exact full target/identity inventory remains private and hash-pinned.

Examples from the already-frozen first-decision targets (not fills or performance):

| Cell | First intended target ticker | Stable ID | Intended session |
| --- | --- | --- | --- |
| M180_K20 | EGLE | `cik:1322439:?:EGLE@2005-06-30` | 2015-01-02 |
| M180_K40 | EGLE | `cik:1322439:?:EGLE@2005-06-30` | 2015-01-02 |
| M365_K20 | VRS | `cik:1126216:CS:VRS@2008-05-31` | 2015-01-02 |
| M365_K40 | VRS | `cik:1126216:CS:VRS@2008-05-31` | 2015-01-02 |

SPY also lacks a certified local OPEN/cash-dividend execution input. Source cash-dividend entitlement/payment and terminal cash/stock/recovery instructions are not supplied by these price/split extracts. Declaration/catalog files are not event economics. Their completeness is unresolved, not a zero-event assumption. **Actually held securities/events: none**, because execution never began; affected held-action counts are NOT_MEASURED. The earliest established stop is missing OPEN inputs, rather than a claim of a particular missing held dividend or merger. No new data campaign or source lookup followed.

## Separate implementation and synthetic certification

`EXP004_LOCAL_REFERENCE_V001` is a separately versioned Decimal34 ledger prototype in [exp004_local_execution.py](../../src/research/exp004_local_execution.py), hash `11915121d3a3b4ff30866e31b7f832b5791e33dc060a296438ab83dfc4f0431b`. It preserves the original EXP999 reference and its guards byte-for-byte. The new real entry point requires a passing certificate, matching engine/economic/input hashes and a pushed checkpoint; the blocked certificate rejects execution before reading portfolio inputs. There is no metric loader, network client or Store mutation in the engine.

Focused synthetic fixtures cover Top20/Top40 stable-ID ties, shortfall, EW, SPY inception-only buy, 95% nominal deployment, fractional sizing, 0.10% per-fill fees, monthly decisions, sales before buys, splits, dividend entitlement/payment, stable-ID rename, cash/stock mergers, evidenced cancellation, ended holdings, empty-universe liquidation, insufficient cash, duplicate/ambiguous/substituted IDs, missing prices, sealed dates and receipt replay. Independent hand calculations use USD25,000: 95% initial notional is USD23,750; fees USD23.75; flat-price initial NAV USD24,976.25. These are fake EXP999 accounting fixtures, never EXP004 performance. Synthetic correctness does not certify real source or lifecycle coverage.

## Preserved design, trial budget and stop

Economic specification `32b216dd7d510399421d9ea89e61aff30c6b59aa8a4e0b31f5786615c1e6b3b9` and methodology `6bcb2a0c8513c06bfe4040275cfe6fa7f204b8e5844a80e36ed3e574560bee2a` remain unchanged. Original freeze v001, amendment v002, numeric QA, [Nexus failure](../../experiments/EXP004/research/publication_runtime_audit.json) and [historical Development report](../../reports/EXP004_development_report.md) retain their bytes. No execution freeze version or PASS certificate was issued. No global pause guard was removed; Nexus remains disabled. The owner authorized this local attempt, but its scientific certification did not pass.

All **24 scored-fold evaluations and six full-Development replays are NOT_RUN**. Four-cell metrics, EW/SPY returns, paired effects, selection, turnover, participation, cost/delay robustness and regime results are unavailable. No economic failure/no-advance verdict can be inferred. The original 59-evaluation ceiling and prior one diagnostic/19 remaining failure reserves are preserved; this source preflight and synthetic fixtures create no completed economic evaluation or new trial. No real-run crash occurred.

**Validation accesses 0; Test accesses 0; new scientific source requests 0; Nexus/Aurora 0.** Only frozen Development/warmup dates were decoded; real price values were not analyzed. EXP005/EXP006/EXP007 remain closed and absent where previously absent; no EXP008, source discovery, Phase 4B, optimizer or paper/live operation occurred. Dependency pins and unrelated user files are preserved.

Validation: **469 local tests, 241 public tests, 0 skipped**. [Validation receipt](exp004_local_validation_v002.json). Public report checks need tracked receipts only; private source audit needs the unchanged EXP004 parts/panels and inherited identity snapshot.

```sh
python -m src.research.exp004_local_preflight --check
python -m src.research.exp004_local_preflight --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

**Stopped at the exact input blocker.** The owner's conditional instruction authorizes Development if certification passes; it cannot manufacture omitted execution/action evidence. No source acquisition is run or automatically proposed. The frozen economic question remains intact and untested. Delivery records final commits/push and hosted CI separately.
