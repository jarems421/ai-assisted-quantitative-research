# EXP004 frozen-price bridge: VPG namespace drift

**VPG_SAME_SECURITY_NAMESPACE_DRIFT. PASS_SOURCE_BRIDGE_ONLY; performance remains blocked pending complete execution inputs.** Starting checkpoint `4b75f8d`, 2026-10-14. [Owner instruction](owner_exp004_vpg_bridge_2026-10-14.md), [exact certificate](exp004_frozen_price_bridge_v001.json), [remaining price-only queries](exp004_frozen_price_acquisition_plan_v001.json).

| In-scope VPG identity | Frozen snapshot | Bounded current query |
| --- | --- | --- |
| Security ID | `ticker:VSHw@2010-06-24` | `ticker:VSHw@2010-06-24#2` |
| Issuer CIK | 1487952 | 1487952 |
| Type / share-class FIGI | CS / BBG001T5X9F2 | CS / BBG001T5X9F2 |
| Effective span through the research cutoff | 2010-07-07–2020-12-31 | 2010-07-07–2020-12-31 |

The current base ID belongs to VSHw, described as Vishay Intertechnology ex-distribution when-issued common stock, CIK 103730, ending 2010-07-06. Its FIGI is unavailable. The separately retained VPGw record shares VPG's current ID/FIGI but has the parent CIK and an earlier when-issued span ending that same day. Those early records do not compete with VPG during the affected dates or the certified VPG span; their full spin-off economics are not certified here. VSH has a separate FIGI/ID and remains distinct. The changed ID and independently unchanged issuer/class/span, together with the nonoverlapping base-ID collision, support namespace drift at the observed record level. No undocumented internal publisher ID-generation algorithm or broad alias rule is claimed.

One current read-only source query returned four records. All nine available identity columns were acquired; composite FIGI, venue, provider ID and explicit class-title columns do not exist in the archived schema and were not invented. The historical comparison clips end dates at 2020-12-31 exactly as the frozen snapshot does; no post-cutoff market observations were queried. A first comparison prototype unnecessarily required the colliding record to be a same-issuer predecessor. Source review corrected that condition to exclude competing overlapping classes; original code and private prototype/review evidence remain retained. The five owner requirements are unchanged.

The archived first-quarter non-aggregating joined query contains exactly one result row for every frozen ticker/day. Any duplicate underlying OHLC row at one of those keys would have propagated through its ordinary inner join; no DISTINCT, grouping or price filter could suppress it. This proves uniqueness for the required keys at that archived query snapshot, while global OHLC extras outside the CS join remain unmeasured.

| First-quarter bridge | Result |
| --- | ---: |
| Frozen rows / unique ticker-day keys / enriched rows | 256,677 / 256,677 / 256,677 |
| Missing / duplicate / ambiguous required keys | 0 / 0 / 0 |
| Exact CLOSE mismatches, including all 62 VPG rows | 0 |
| Positive finite OPEN / missing / invalid | 256,677 / 0 / 0 |
| Additional source rows admitted | 0 |

All 62 VPG rows retain `ticker:VSHw@2010-06-24` inside EXP004. **CURRENT SECURITY_SEGMENTS IS NOT USED TO REWRITE FROZEN EXP004 IDENTITY.** Further price requests project only ticker, day, openingPrice and unadjustedClose from the same source, with exact frozen quarter bounds; extras stay outside the experiment. Every quarter requires unique prices, exact CLOSE equality and positive finite OPENs. Missing/ambiguous rows stop continuation.

This certificate establishes execution-field provenance, not a new economic freeze or v004 execution PASS. OPEN adjustment/share units, full price coverage, SPY, cash-dividend accounting and actual-held terminal paths still require their sequential certificates. No portfolio performance, metric, selection or trial occurred. Validation/Test accesses remain 0. Earlier exact-key failure reports, source receipts, global pause and frozen economic artifacts remain unchanged.
