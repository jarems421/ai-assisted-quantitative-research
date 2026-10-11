# EXP003 ? momentum plus qualifying insider purchases

**DRAFT ? NEEDS DESIGN REVISION. Final focused pre-freeze pass complete.** The accepted source-defined universe gate passes. Insider window completeness does not: no certified production insider states or zeros can be emitted. Joint inception remains unresolved. EXP002 is closed and unchanged; no candidate performance, optimization, held-out observations or automatic freeze occurred.

Does adding publicly usable qualifying insider purchases to medium-term momentum improve **both mean daily net return and zero-RF Sharpe** versus matched momentum-only? Lower drawdown alone cannot confirm this hypothesis.

| Component | Predeclared design |
|---|---|
| Universe | Source-covered historical CS identity spans, unique stable IDs and positive completed prices; retain ended histories while effective. No current/index membership, cap, ADV or invented exchange/OTC filter. |
| Signals | Split-safe 180/365-calendar-day momentum; 30/90-day Distinct Qualifying Insider Purchasers, nonderivative P/A positive shares including private purchases, distinct owner CIK, publication-based versions/corrections. |
| Grid | 8 composite, 4 momentum-only and 4 insider-only cells; no irrelevant ablation dimensions. Monthly, equal percentile ranks, stable-ID ties and equal security weights. |
| Matched comparison | Same momentum horizon, K, dates, certified universe, funding and costs. Broader momentum coverage is diagnostic only. |
| Decision / execution | Previous calendar day 21:00 New York / intended 09:30 monthly first session. Numeric, validity and exact session-key guards. |
| Costs | $25,000, 0.10% per stock fill, cash dividends, nominal 95%; inherited bounded reserve convention is not an exact future-fill guarantee. |
| Shortfall | Hold min(N,K). Nominal per-name allocation 95/K%; total 95?min(N,K)/K%. Remainder cash; N=0 cash-only. Empty-universe liquidation still needs runtime evidence. |
| Selection | Positive pooled paired mean and Sharpe differences, positive median fold mean improvement, no critical failure and ?90% scheduled participation in every scored fold. Highest median fold mean improvement, then lower neighbor dispersion, turnover and fixed parameter order. |
| Dates | Joint inception unresolved; Development ends 2020-12-31. Conditional folds not activated. Outer Validation 2021?2023; sealed historical Test 2024. |
| Benchmarks | SDK-compiled explicit SPY and equal-weight entire eligible universe, plus matched momentum. Dynamic templates have unresolved production streams. |
| Robustness | Local +10/+20 bps costs per side; one extra execution session; existing grid neighborhoods; broader momentum diagnostic. No weekly cadence or added tuning axis. |
| Budget | This pass: up to 2,000 included tokens, no credit purchase. Future candidate execution unauthorized. 116 conditional future evaluations; actual audit debit unknown. |

Read the [final review](research/final_freeze_review.md), [monthly/annual coverage](research/production_coverage_summary.json), [candidate definitions](candidate_definitions.json), [evaluation plan](evaluation_plan.json), [provenance](provenance.json) and [query log](research/readiness_query_log.json). VERIFIED labels apply only to the named observation or scoped contract. All **323,910 source-rule security-decisions** are UNAVAILABLE for insider production certification; this is not evidence of zero insider activity. Numeric zero requires an audited complete security/window event-version and identity contract. Absence of purchases, null correction flags and query success cannot supply it.

The schema-required Development start 2015-01-02 remains a nonexecuting placeholder. Source-rule universe PIT is scoped to historical reconstruction; insider PIT remains false, so the semantic source audit rejects the draft. All post-2020 observations remain prohibited during design. Validation/Test are workflow-held-out historical data; owner-approved future paper remains the forward test.

The schema now supports explicit paired-effect selection instead of forcing standalone-Sharpe selection. Legacy DD/trade fields are neutral at 100%/0 and do not gate paired eligibility. The 90% participation requirement refers to scheduled rebalance decisions, not names traded: unchanged holdings count only with a completed audited evaluation; cash-only missing-coverage dates do not. Legacy experiments retain their selection behavior. No performance metric formula or PIT/temporal gate was weakened.

No production custom dataset was generated; the [manifest](production_custom_signal_manifest.json) records blocked readiness. Future versions need a stage-bound EXP003 export adapter preserving the same frozen reconstruction and owner Test gates; the inherited exporter?s hard 2020 ceiling cannot be silently bypassed. Compiled SDK templates explicitly use unpublished IDs and fixture tickers, not executable production claims.

Eight bounded Lake jobs completed; one SQL submission was rejected without a job ID. Two changed requests corrected New Year warmup bounds. Client waits were reconciled with existing IDs. Exact requests and raw hashes are logged; raw receipts remain ignored under `data/raw/EXP003/`. The [verbatim authorization](research/final_pass_authorization_20261011.md) records the task-specific allowance.

This pass stops at a specific source-contract failure rather than opening another general audit. Supply a complete security/window insider contract, or explicitly revise/abandon the signal before performance. Do not turn missing observations into zero. Inception, folds and production publication remain downstream of that gate.

Run `python -m src.research audit EXP003` (expected insider-PIT rejection), `python -m unittest discover -s tests -v`, and `python -m src.presentation.exp001 --check`. Reproduce the original identity prototype/conditional plan with `python -m src.research.design_exp003`; reproduce current coverage locally with `summarize_saved()` in `src.research.readiness_exp003`. Remote `--execute` is not standing authorization for another task.
