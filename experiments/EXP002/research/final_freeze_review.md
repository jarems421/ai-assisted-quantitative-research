# EXP002 final pre-freeze review

**NEEDS DESIGN REVISION. DRAFT; no automatic freeze.** This pass follows the verbatim [owner request](final_blocker_authorization_20261011.md). No EXP002 candidate performance, optimization or post-2020 source observation was accessed.

The proposed question is: in a historical large-cap US common-equity universe, does combining 180/365-calendar-day momentum with 30/90-day Distinct Qualifying Insider Purchasers and matched-manager institutional holder-count change improve paired net daily return and zero-RF Sharpe versus momentum alone? P purchases include private purchases. Keep 20/40 holdings, eight composite cells, monthly cadence, equal ranks/security weights, and no native ownership fallback, market cap, ADV or prospective metric gates.

| Gate | PASS/FAIL | Evidence and boundary |
|---|---|---|
| Ownership PIT | PASS — scoped source contract | All 79 sampled owner events link to 60 filing-owner records; 60 issuer/security CIK checks match. Version/dedup/positive-share/future-amendment rules are locally controlled. This certifies the sampled contract, not universal feed completeness. |
| Custom transport | PASS — artificial execution pattern | Four valid monthly sessions each trade exactly once with the predeclared decision value; invalid and omitted updates never trade despite stale numeric carry-forward. Three disclosed streams: numeric value, validity==1, exact YYYYMMDD session key. |
| Timezone | PASS | 130,308 institutional and 60 insider filing values exactly match NY filing-date EOD stored as naive UTC across standard/daylight time. Explicit conversion rejects other conventions. This is conservative availability, not exact SEC acceptance time. |
| Historical universe | **FAIL — CRITICAL** | Supplied memberships contain 365 symbols at 2014 inception, 380 at 2015 inception and 482 at 2020 end. Literal constituent-symbol joins produce reused/renamed-symbol type errors and 19 missing security IDs. The absent historical constituents cannot be explained as contemporaneous exclusions. NU→ES is individually verified, but does not certify the whole membership panel. |
| Price/corporate actions | PASS — bounded contract | Nominal unadjustedClose for the floor; local momentum uses only splits effective within completed lookback bars. AAPL split continuity and native adjusted dividend units reconcile. All 48 native open/close prices match source prices within $0.000008. The observed Polygon source is consistent with official [split-adjustment documentation](https://massive.com/docs/rest/stocks/aggregates/custom-bars); this is not universal Nexus pipeline certification. MSFT no-action and NU/ES source samples are consistent. |
| Execution timing | PASS — bounded fixture | Observed intended fills at 09:30 NY; hour, validity and exact-date guards reject other days and closes, including a DST-adjacent Monday. The rejected 12.5-hour custom lag remains prohibited. |
| Institutional cohort | **FAIL — CRITICAL production identity/zero gate** | 629 source rows from six original/amended filings exercise CUSIP-only replacement/addition mechanics. Two adjacent sample originals each have nine unresolved ticker rows. Full CUSIP→eligible-security reconciliation is not established, so their omissions cannot certify zero. No usable 20-manager production cohort has been demonstrated. |
| Missingness | PASS — fail-closed contract | Numeric missing values are omitted; validity/session-key companions prevent stale resurrection. Ambiguous ownership/filing/identity states are unavailable. Institutional production usability remains the failed gate above. |
| Development inception | **FAIL — downstream of critical source gates** | Price warmup includes 2013-12-31 and ownership source warmup includes 2014. Those dates alone cannot establish usable joint coverage. 2015-01-02 is a planning placeholder, not a certified inception. |
| Lockbox dates | PASS — chronology designated, coverage confirmation pending | Outer Validation 2021-01-01–2023-12-31; historical Test 2024-01-01–2024-12-31 is sealed now. No observations queried. Both are workflow-held-out; prior EXP001/model knowledge is disclosed. |
| Statistical contract | PASS — predeclared descriptive uncertainty | Paired 20-return blocks, 10,000 draws, seed 2,002,001; percentile intervals for mean excess and Sharpe difference. No p-values/significance claim. Holm remains reserved for a separately validated inferential implementation. |
| Immutable provenance | PASS | Source/receipt hashes, original request, archived fixture/helper code, disclosed publication IDs, exact SQL/bounds and job outcomes are preserved. Production alpha datasets remain unpublished. |

Evidence is reproducible locally in [final_runtime_summary.json](final_runtime_summary.json), [final_source_summary.json](final_source_summary.json), [custom_signal_manifest.json](custom_signal_manifest.json) and [statistical_contract.md](statistical_contract.md), using `python -m src.research.final_exp002`. Passing tests do not certify missing source evidence.

## Execution convention and fixed costs

Choose **nominal deployment 95%**, the highest predeclared diagnostic level completing without rejected orders. On $25,000 funding the 90%, 92.5% and 95% probes produced $22,125, $22,750 and $23,375 stock notional: consistently 1.5 percentage points below nominal targets. The earlier $1,000 probe's $15 gap fits the same funding-scaled offset. Retain this empirical engine allocation convention, not a guarantee for every future portfolio. At nominal 95%, the observed two-asset implementation deploys 93.5% before $23.375 fees. No return selected this setting.

Base fee is 0.10% per fill, cash dividends. Predeclare additional local +10/+20-bps traded-notional stresses on both sides. These are implementation-cost stresses, not literal stock-slippage simulation. Do not reject freeze merely because an internal reserve formula or native daily-stock slippage field is undocumented.

## Chronology and trial accounting

Development ends 2020-12-31. Final inception and active folds remain unapproved until source gates pass. If 2015-01-02 is certified, use four expanding clean-year held-out folds (train 2015–2016/evaluate 2017, then evaluate 2018, 2019 and 2020), with past warmup outside scored returns. This provides at least two training years. Do not replace this conditional start with a performance-selected date.

The conditional four-fold plan has 34 family cells plus two benchmarks per fold: 144 fold runs, nine selected-family Development replays, 27 runs for three fixed remote Development stresses, nine outer Validation and nine eventual Test runs, plus a 20-failure reserve = **218 future evaluations**. Add **23 already attempted diagnostic backtests** = **241 conditional total**. Two local cost stresses across nine selected families add 18 local analyses, not remote jobs. Retain the earlier plans as history. No final evaluation count or candidate execution is authorized while inception is unresolved.

This pass submitted ten diagnostic backtests and seven Lake queries: six queries completed, one failed by server timeout; the changed, date-bounded full-filing query is a separate counted attempt. Ten runs yielded 240 events across twelve retrieved pages, including one empty corporate exhaustion page. One Lake client wait timed out; the same ID was polled. Three artificial custom indicators were created. No saved-portfolio API, candidate study, optimization, credit purchase, deployment or held-out read occurred.

## NONCRITICAL LIMITATIONS

- Vendor data can be revised; frozen source snapshots are deterministic, but independent historical database immutability is not claimed. No such uncertainty alone is treated as proof of leakage.
- Conservative filing-date EOD availability differs from precise SEC acceptance/publication and vendor ingestion time. Exact public SEC pages were inaccessible in this pass; the timezone conclusion follows source guidance and exact stored-row identities.
- Source-observed purchase activity is not all economic insider activity. Private P purchases, excluded transaction types and vendor omissions limit interpretation.
- Native split-adjusted execution and cash dividends reconcile in bounded cases; this is not universal corporate-action certification. Exact merger/delisting consideration, stock/cash conversions and liquidity recovery remain engine approximations.
- The empirically observed reserve/deployment behavior is not an account-wide guarantee. Whole-share/fractional handling, turnover, liquidity, market impact, financing and taxes can differ in practice.
- The two cost stresses are uncalibrated fixed-fill-tape sensitivities; they do not fully model trading consequences.
- Historical researcher/model knowledge, grid selection and bootstrap assumptions limit scientific conclusions. Statistical significance or persistent alpha is not promised.
- Actual research-token debit/remaining allowance is not exposed. The previous 1,000-token included authorization remains the recorded numerical ceiling; no credit purchase occurred and independent billing compliance cannot be asserted.

## Decision required before another research phase

The remaining work is specific: obtain a trustworthy historical constituent/identifier history, and establish an eligible-security CUSIP/complete-filing contract with a demonstrated usable matched cohort. Do not fix the first by applying today's symbols backwards or the second by treating unknown holdings as zero. If these sources cannot be supplied, simplify or abandon the ownership hypothesis rather than launch another general audit. Leave Development inception unresolved until they pass.

The unchanged semantic audit still rejects EXP002; no look-ahead, sealed-date, provenance or PIT gate was weakened. No hypothesis was frozen.

Validation: 114 software tests passed. The unchanged semantic audit exits 1 at institutional PIT availability; schema and sealed-date structure are valid. Local source/runtime summaries are byte deterministic. EXP001 tracked results and definitions are unchanged.
