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
