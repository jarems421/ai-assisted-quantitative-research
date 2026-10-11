# Manual Aurora research prompt — EXP002

Prepared locally; **not submitted**. Remote Aurora remains blocked in Research OS because prompt instructions are not server-side tool/date isolation. Manual use does not fix that limitation. If you cannot establish an auditable read-only research scope, use documentation/capability metadata only, report historical evidence as unresolved, and do not grant data/job access. No spending is authorized by this draft.

Copy the following into your manual research session when its access scope is appropriate:

---

We are designing EXP002 for a rigorous quantitative research programme. This turn is **research and evidence gathering only**.

Do not create or modify portfolios, backtest or rerun jobs, optimize, deploy, place trades, freeze a hypothesis, select a winner or evaluate strategy performance. Do not query any proposed held-out Test period or outer Validation. The provisional candidate-formation cutoff is **2020-12-31**: no market, signal-observation, corpus-performance or backtest observations beyond that date. Current documentation/schema metadata can describe coverage boundaries without retrieving later observations. Test dates remain unresolved; this does not authorize unrestricted historical access.

Research question:

**Among a dynamic liquid U.S. equity universe, does combining medium-term price momentum with point-in-time corporate-insider accumulation and improving institutional ownership produce more robust future performance than momentum alone?**

Investigate actual Nexus implementability and historical coverage for:

- Medium-term momentum / Rate of Change.
- Corporate insider activity, especially DistinctBuyers, BuyCount and BuyValue.
- Institutional ownership changes, especially NewHolders, NetHolderChange and NetShareChange.
- Lagged liquidity and point-in-time market-cap filters.
- Dynamic historical U.S. common-equity universe construction, including dead/delisted securities and security-type exclusions.

For every source identify the signal's meaning, units, exact supported SDK/tool declaration, public usable timestamp versus economic/reporting date, vendor ingestion delay, historical coverage, likely missingness, stale observations, survivorship, revision and leakage risks. Provide direct evidence references and quoted field names. Distinguish verified documentation, actually audited observations, reasoned proposals and unresolved claims. Current holdings, transaction dates and quarter-end dates are not point-in-time availability evidence. Do not claim that a fixed lag cures unknown revisions. Inspect only expressly permitted read-only metadata/evidence; if access cannot be bounded, stop that investigation and mark it unresolved.

Propose interpretable families and matched controls:

- Momentum only.
- Insider only.
- Institutional only.
- Momentum + insider.
- Momentum + institutional.
- Insider + institutional, to complete the three-signal leave-one-out controls.
- Full composite.
- Explicit SPY buy-and-hold.
- Equal-weight dynamic eligible universe.

Use at most three alpha signal classes, one representation each and equal rank weights. DistinctBuyers and NetHolderChange are proposed primary representations, not verified choices. Alternatives must be counted and settled before freeze. Explain how the same historical universe, coverage, execution, funding and costs apply across comparisons. Explain how zeros differ from absent data and how asynchronous institutional filings are compared without hindsight.

Evaluate these preliminary design ranges based on implementability/coverage, not historical strategy returns:

| Parameter | Proposed range |
|---|---|
| Momentum | 126–252 trading sessions |
| Insider | 30–90 calendar days from disclosure availability |
| Institutional | 180–365 calendar days of filing updates |
| Holdings | 20–40 |
| Rebalance | Monthly baseline; weekly robustness alternative |
| Average dollar volume | $10m–$25m, trailing 20 lagged sessions |
| Market capitalization | $1bn–$5bn, point in time |

Verify units and actual historical support; do not invent an SDK parameter name from these conceptual labels. Proposed funding is $25,000, fee 0.10% per stock fill, dividends cash, 95% deployment, daily simulations and next-session execution. Slippage, cadence, warmup (proposed 400 calendar days), missing/stale handling and corporate actions need evidence. No claim of executable net performance from zero assumed slippage.

Investigate whether prospective rebalance planned turnover, estimated cost, expected benefit or net benefit can gate trades **before execution**, and identify their exact units, formulas and inputs. These are optional robustness mechanisms, not permission for new tuned rules or realized future-return inputs.

Identify plausible failure mechanisms: late/noisy disclosures, insider transaction classification, institutional filer churn, sparse coverage, survivorship, revised inputs, redundant exposures, momentum crashes, crowding, capacity and transaction costs. Explain what evidence would disconfirm the incremental-information hypothesis.

Dates are provisional: Development 2015–2020, inner Validation 2019–2020, outer Validation 2021–2024. Do not inspect outer Validation observations. Determine only whether metadata supports sufficiently long joint historical coverage. Historical lockbox dates are unresolved and must later be sealed before freeze; EXP001 already exposed 2025–2026 SPY outcomes. Historical evidence is workflow-held-out, never genuinely unseen; prospective paper begins only after freeze and separate owner approval.

Return a structured research memo with:

1. Claim/evidence table: exact field or operation, source link/reference, evidence date, access scope, verified/proposed/unresolved status, public usable timestamp, coverage, missingness and risk.
2. Dynamic-universe implementation and missingness/revision audit plan; list any unsupported step.
3. Simple candidate/control definitions and bounded parameter units/ranges.
4. Coverage-based date-window recommendations without any held-out observations or performance.
5. Execution, costs, prospective turnover gates and remaining limitations.
6. Actual job amplification/count and dated quote requirements; no new paid query, preview job or agent job is authorized. Report unknown cost as unknown.
7. Falsifiers, confounders, robustness requirements and unresolved freeze blockers.
8. All read operations performed and their bounds, plus explicit confirmation of no portfolio/job/trade mutation. If none performed, say so.

Do not replace absent evidence with confident claims. This memo will be audited locally before any hypothesis freeze. The current draft has zero spend ceilings and is not execution-ready.
