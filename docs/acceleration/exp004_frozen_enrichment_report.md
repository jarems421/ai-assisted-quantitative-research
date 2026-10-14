# EXP004 frozen-price enrichment: complete acquisition, execution-row stop

**LOCAL_EXECUTION_INPUTS_BLOCKED — REQUIRED_EXECUTION_OPEN_ROWS_MISSING. VPG namespace drift resolved; economic hypothesis untested.** Starting HEAD `4b75f8d5eb9bf6cae451ec34afe45ec113c0ac97`, as of 2026-10-14. [Owner instruction](owner_exp004_vpg_bridge_2026-10-14.md), [source bridge](exp004_frozen_price_bridge_report.md), [canonical review](exp004_frozen_enrichment_review_v001.json).

## Resolved identity and completed enrichment

The bounded current identity query returned four records. VPG retains frozen CIK 1487952, CS type, share-class FIGI BBG001T5X9F2 and the 2010-07-07–2020-12-31 in-scope span. The current ID `ticker:VSHw@2010-06-24#2` differs from frozen `ticker:VSHw@2010-06-24`; the unsuffixed current VSHw record has a different CIK and ends before that span. The [certificate](exp004_frozen_price_bridge_v001.json) records **VPG_SAME_SECURITY_NAMESPACE_DRIFT** with independent fields and nonoverlap evidence. Internal publisher ID-generation code is not claimed audited; early when-issued spin-off economics remain outside this scoped equivalence.

Bridge checkpoint `c6d7224` was pushed before the remaining requests. The first quarter reused verified source bytes; no repeat request was made. The other 27 queries selected only ticker/day/openingPrice/unadjustedClose from `lake.sec_daily_ohlc`, with exact frozen bounds and no security_segments join. Every enriched row keeps its frozen security_id and CLOSE. No suffix stripping, replacement identity, new universe or survivor screen occurred. Extra source rows were excluded from candidate/EW enrichment; SPY was separately selected as its existing frozen ETF benchmark.

| Quarter | Frozen rows | Enriched rows | Missing source keys | Duplicate source keys | CLOSE mismatches | Missing / invalid OPEN fields |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2013-12-31_2014-03-31 | 256,677 | 256,677 | 0 | 0 | 0 | 0 / 0 |
| 2014-04-01_2014-06-30 | 264,970 | 264,970 | 0 | 0 | 0 | 0 / 0 |
| 2014-07-01_2014-09-30 | 274,315 | 274,315 | 0 | 0 | 0 | 0 / 0 |
| 2014-10-01_2014-12-31 | 278,025 | 278,025 | 0 | 0 | 0 | 0 / 0 |
| 2015-01-01_2015-03-31 | 267,053 | 267,053 | 0 | 0 | 0 | 0 / 0 |
| 2015-04-01_2015-06-30 | 277,383 | 277,383 | 0 | 0 | 0 | 0 / 0 |
| 2015-07-01_2015-09-30 | 285,367 | 285,367 | 0 | 0 | 0 | 0 / 0 |
| 2015-10-01_2015-12-31 | 286,170 | 286,170 | 0 | 0 | 0 | 0 / 0 |
| 2016-01-01_2016-03-31 | 272,165 | 272,165 | 0 | 0 | 0 | 0 / 0 |
| 2016-04-01_2016-06-30 | 284,607 | 284,607 | 0 | 0 | 0 | 0 / 0 |
| 2016-07-01_2016-09-30 | 285,810 | 285,810 | 0 | 0 | 0 | 0 / 0 |
| 2016-10-01_2016-12-31 | 284,618 | 284,618 | 0 | 0 | 0 | 0 / 0 |
| 2017-01-01_2017-03-31 | 279,453 | 279,453 | 0 | 0 | 0 | 0 / 0 |
| 2017-04-01_2017-06-30 | 283,475 | 283,475 | 0 | 0 | 0 | 0 / 0 |
| 2017-07-01_2017-09-30 | 283,709 | 283,709 | 0 | 0 | 0 | 0 / 0 |
| 2017-10-01_2017-12-31 | 282,837 | 282,837 | 0 | 0 | 0 | 0 / 0 |
| 2018-01-01_2018-03-31 | 273,720 | 273,720 | 0 | 0 | 0 | 0 / 0 |
| 2018-04-01_2018-06-30 | 287,934 | 287,934 | 0 | 0 | 0 | 0 / 0 |
| 2018-07-01_2018-09-30 | 285,404 | 285,404 | 0 | 0 | 0 | 0 / 0 |
| 2018-10-01_2018-12-31 | 286,122 | 286,122 | 0 | 0 | 0 | 0 / 0 |
| 2019-01-01_2019-03-31 | 274,854 | 274,854 | 0 | 0 | 0 | 0 / 0 |
| 2019-04-01_2019-06-30 | 284,022 | 284,022 | 0 | 0 | 0 | 0 / 0 |
| 2019-07-01_2019-09-30 | 289,448 | 289,448 | 0 | 0 | 0 | 0 / 0 |
| 2019-10-01_2019-12-31 | 288,298 | 288,298 | 0 | 0 | 0 | 0 / 0 |
| 2020-01-01_2020-03-31 | 279,111 | 279,111 | 0 | 0 | 0 | 0 / 0 |
| 2020-04-01_2020-06-30 | 283,424 | 283,424 | 0 | 0 | 0 | 0 / 0 |
| 2020-07-01_2020-09-30 | 291,682 | 291,682 | 0 | 0 | 0 | 0 / 0 |
| 2020-10-01_2020-12-31 | 300,539 | 300,539 | 0 | 0 | 0 | 0 / 0 |

Totals: **7,871,192 frozen / 7,871,192 enriched rows**, 6,635 stable IDs; all 28 quarters pass required-key uniqueness, exact CLOSE equality and positive finite OPEN-field checks. Observed source extras excluded from candidate/EW enrichment: 6,631,753; first-quarter extras are measured only inside its archived CS-joined response. No first-quarter global source census is claimed.

## Concrete execution-session failure

Frozen numeric QA required complete prior sessions and historical execution identity; it did not prove that an execution-day OHLC row exists. Joining the 72 immutable monthly panels to the enriched prices gives **273,115 required common-population security/session pairs: 273,089 positive finite OPENs, 26 missing rows and 0 invalid present OPENs**.

Every missing ticker/day is also absent from the full price-only responses, before any identity join. This is not renewed ID drift or 26 observed NULL-valued source bars: the rows themselves are unavailable. Each would be required by the frozen EW target; intended momentum cells are listed only where that security belongs to the frozen target. These are source/target checks, not executed holdings or performance.

| Required session | Ticker | Frozen stable ID | Intended cells affected |
| --- | --- | --- | --- |
| 2015-09-01 | SGOC | `cik:1412095:?:SGOC@2010-12-31` | EW |
| 2015-10-01 | ERB | `ticker:ERB@2012-06-30` | EW |
| 2015-10-01 | SLI | `cik:89270:?:SLI@2003-09-30` | EW |
| 2016-07-01 | IDSY | `figi:BBG001SCYJ38` | EW |
| 2016-08-01 | BXC | `cik:1301787:CS:BXC@2004-12-31` | EW |
| 2017-03-01 | HGSH | `figi:BBG001SPKCM8` | EW |
| 2017-05-01 | UG | `figi:BBG001S6DYH6` | EW |
| 2017-07-03 | BTN | `figi:BBG001SGN0V1` | EW |
| 2017-07-03 | CEMI | `figi:BBG001SD7FL4` | EW |
| 2017-07-03 | KIQ | `figi:BBG001S62439` | EW |
| 2017-07-03 | NFEC | `ticker:NFEC@2010-10-31` | EW |
| 2017-08-01 | PYDS | `figi:BBG001S8CPZ2` | EW |
| 2017-08-01 | SMTX | `cik:1108320:?:SMTX@2003-09-30` | EW |
| 2017-09-01 | CXDC | `figi:BBG001SVWG25` | EW |
| 2018-02-01 | INFU | `figi:BBG001SQTYK1` | EW |
| 2018-03-01 | TRNS | `figi:BBG001S5WVW6` | EW |
| 2018-05-01 | WSTG | `cik:945983:?:PROG@2003-09-30` | EW |
| 2018-07-02 | BBU | `cik:1654795:?:BBUw@2016-05-31` | EW |
| 2018-07-02 | NBY | `cik:1389545:?:NBY@2007-10-31` | EW |
| 2018-08-01 | ISSC | `figi:BBG001S8H2T5` | EW |
| 2018-11-01 | ALKS | `cik:874663:?:ALKS@2003-09-30` | EW |
| 2019-02-01 | IDSA | `cik:4187:?:IDSA@2003-09-30` | EW |
| 2019-03-01 | SGRP | `figi:BBG001SCV2B9` | EW |
| 2019-10-01 | TACT | `figi:BBG001S5WK05` | EW |
| 2019-12-02 | ASRV | `figi:BBG001SD3BP3` | EW |
| 2020-08-03 | TWMC | `figi:BBG001S5WYG8` | EW, M365_K20, M365_K40 |

Earliest established failure: **2015-09-01 / SGOC / EW**. No adjacent-day/close substitution, cash allocation in place of a missing target, stale-price holding or population pruning was applied. This blocks the complete programme even if some cell/fold subsets have all their intended OPENs. No economic verdict can be inferred.

## SPY, actions and certificate boundary

SPY was recovered from the already acquired price-only responses, without another request or CS filtering: **1,511 unique Development sessions**, 0 missing calendar sessions and 0 missing/0 invalid OPEN fields. The original historical snapshot binds it separately as ETF `figi:BBG001S72SM3`, CIK 884394. Inception 2015-01-02 is present. This is field/calendar/identity coverage, not cash-dividend or complete raw-share execution certification.

Dividend queries/events/accounting certification and actual-held terminal discovery were **NOT_RUN after the upstream required-OPEN failure**. Counts remain unmeasured, never zero-dividend or zero-terminal claims. The existing source schema includes declaration/ex/record/pay dates; their availability and semantics for held events are not certified by this pass. OPEN adjustment/share-unit consistency and lifecycle/calendar gates remain deferred; positive numeric OPENs alone cannot become nominal-share ledger inputs.

**v004: BLOCKED / not issued.** Spec `32b216dd7d510399421d9ea89e61aff30c6b59aa8a4e0b31f5786615c1e6b3b9`, methodology `6bcb2a0c8513c06bfe4040275cfe6fa7f204b8e5844a80e36ed3e574560bee2a` and engine `11915121d3a3b4ff30866e31b7f832b5791e33dc060a296438ab83dfc4f0431b` remain unchanged. No new economic/execution freeze, real ledger, NAV, return, effect, interval, p-value, selection or robustness exists. All 24 fold evaluations and six full replays remain NOT_RUN. The prior 59-evaluation ceiling, one diagnostic and 19 failure reserves remain unchanged.

New source operations: **1 identity query + 27 price queries; 152 SDK transport calls**, including polls/manifests/downloads; 0 new schema queries, 0 retries, 0 SPY-only queries, 0 dividend/lifecycle queries. Previous first-quarter/source-schema operations are historical cache evidence, not new starts. Nexus backtests/publication/Aurora/purchases 0; actual debit UNKNOWN. Original and derived source bytes, request/operation receipts and hashes remain private and immutable. Contacts/credentials are not committed.

**Validation accesses 0; Test accesses 0; performance evaluations 0.** No 2021+ market/outcome data was queried or decoded. Prior reports, failed receipts, frozen experiments, processed baselines, metric code, dependency pins and remote pause remain unchanged. EXP005/006/007 stay closed and absent; no new experiment, vendor, source-family discovery, Phase 4B, optimizer or paper/live action occurred.

Validation: **479 local tests, 251 public tests, 0 skipped**. [Receipt](exp004_frozen_enrichment_validation.json). Reproduce public report checks from tracked receipts; private audit reads immutable source parts and panels without network:

```sh
python -m src.research.exp004_frozen_enrichment_report --check
python -m src.research.exp004_frozen_enrichment_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

**Stopped at owner sections 12/24/25: required execution OPENs are missing.** The bridge source certificate passed; the local execution certificate did not. No further source request or downstream continuation follows automatically. Commit/push and hosted CI are delivery receipts reported separately.
