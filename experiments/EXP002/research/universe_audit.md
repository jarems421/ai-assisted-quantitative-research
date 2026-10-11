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
