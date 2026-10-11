# EXP002 historical universe audit

VERIFIED source observation: lake.security_segments returned 16,748 cutoff-bounded spans intersecting 2014–2020. Fields include ticker, security_id, share_class_figi, cik, from_date, to_date and asset_type. Returned endpoints are clipped; current canonical symbols and future segment endpoints are not used to choose historical securities.

The 2015–2020 taxonomy has 6,558 CS IDs across 7,286 spans and 2,861 ETF IDs across 3,069 spans. ADRC/ADRP/ADRR, PFD, funds, units, rights, warrants and unknown types occur. 2,473 CS spans ended during the window; this includes renames/mergers and **is not a confirmed delisted-company count**.

Ended securities are historically discoverable: SNDK has a bounded end of May 11, 2016; the price panel includes earlier-ended CQB/ROC rows. SNDK's type is null, illustrating coverage lost under strict subtype requirements. No subsequent return was inspected. Source discoverability does not verify native delisting liquidation.

## Proposed explicit filter

- Join by ticker and effective span, with stable security_id across renames; reject ambiguous mappings.
- Require CS; exclude ETF/ETN/ADR/preferred/fund/unit/right/warrant and unknown types, recording exclusions.
- Require a current completed-session price, unadjusted nominal price >= $5 and validated lagged volume/dollar-volume.
- Use cap only with audited public share lineage/scope; revise explicitly if unavailable.
- Establish historical exchange/OTC exclusion. The inspected schema has **no exchange/OTC field**; CS alone is insufficient.

Segment publication vintages, native ALL_US_STOCKS parity, share-class/company selection, subtype completeness, exchange exclusions, identifier corrections and merger/delisting execution remain unresolved. Identity checks excluded 24,930 ownership aggregates; no current ticker substitution was used. Native IsAssetType Stock alone cannot exclude ETFs. The two diagnostics use an explicit ticker; no native DynamicRebalance membership probe was run. This filter is proposed, not certified executable. No outer Validation/Test definition changed.


## Revised primary construction (2026-10-11)

Prefer explicit effective historical security spans to native ALL_US_STOCKS. Primary proposal: known CS common stocks, nominal unadjusted price >= $5, fixed USD 10m ADV on 20 distinct completed lagged sessions; retain ended spans. Exclude ADR/ETF/preferred/fund/other/unknown types and ambiguous identities; record exclusions, including unsupported delisted histories. Historical exchange/OTC vintages remain unavailable in the inspected schema. No safe exchange-only universe or full native parity is claimed.

Market cap is removed from the primary universe and grid; USD 25m liquidity is robustness only. Existing liquid-ID counts use unverified price-volume units and must not be treated as finalized eligibility. AAPL unadjustedClose/closingPrice = 4 before its split and 1 afterward; reported volume basis remains unresolved.

The CQB/SPY diagnostic pruned CQB after its final January 6, 2015 source session and sold it January 7 at 90% of the prior close. This is event-level evidence for one native delisting mechanism, not proof of merger consideration, all security types, complete historic membership or exchange vintages. See [design revision](design_revision.md).


## Narrower proposed universe; ADV removed

Current proposal is historical GSPC effective membership intersected with certified CS listing/security-ID spans, nominal unadjustedClose >= $5; no primary market-cap/ADV filter. 559 bounded index_constituents rows retain ended spans, with endpoints clipped to authorized dates; present-day isActive is unused. This is a reproducible narrower proposal, not evidence of public membership vintages, complete dead-stock coverage, identifier lineage or exchange/OTC classification. Existing monthly exclusion counts remain available; certified exclusions for the narrower primary universe cannot yet be computed and remain null. No replacement liquidity gate was selected. Final universe is unresolved.


## Final bounded pass — current evidence (2026-10-11)

This update supersedes unresolved claims in the historical text above only where explicitly evidenced. EXP002 remains **DRAFT / NEEDS DESIGN REVISION**. See [final freeze review](final_freeze_review.md), [source summary](final_source_summary.json) and [runtime summary](final_runtime_summary.json).

VERIFIED, bounded: naive SEC availability is UTC corresponding to NY filing-date EOD (130,308 institutional plus 60 insider records); all 79 sampled insider events link to filing-owner records. Numeric + validity + exact session-key transport passes four valid and two invalid/absent monthly fixtures. Never use the rejected custom lag. Nominal-price floor and local effective-split momentum avoid future split factors; cash dividends are accounted once. Native AAPL quotes/dividend units reconcile. Fixed nominal deployment is 95%, observed effective 93.5% before fees at $25,000; undocumented reserve and merger economics are noncritical execution limitations.

CRITICAL failures: historical membership is underfilled (380 symbols in January 2015; 482 in December 2020) with reused/renamed symbol/type mismatches and 19 missing IDs; institutional source extracts cannot yet certify eligible-security omission as zero. CUSIP-only original/restatement/addition mechanics are not certified production holdings. No usable complete 20-manager cohort or joint inception follows. Do not use today's symbols backwards or missing holdings as zero.

PROPOSED fixed institutional quality: 20 matched managers, 95% known-public union coverage, 180-day quarter/publication stale ceiling; 95% passes 16/23 global adjacent source cohorts, reducing to 90% adds only one. These source distributions are not complete issuer cohorts. Eight composite cells remain unchanged. Conditional four folds yield 218 future remote evaluations + 23 past diagnostics = 241, plus 18 local fixed-fill cost analyses. Active inception/folds remain unapproved. Validation is 2021–2023; workflow-held-out Test 2024 is explicitly sealed, with prior EXP001/model knowledge disclosed. No held-out observations accessed. Statistical intervals are descriptive, never p-values; see [contract](statistical_contract.md).

Original reports/failed calls remain historical evidence. This pass added ten diagnostic runs, seven Lake submissions (six complete/one timeout), 240 events/twelve pages and three artificial indicator creates. No candidate study, optimization, portfolio creation API, deployment, credit purchase or freeze occurred. Actual token debit remains unknown.
