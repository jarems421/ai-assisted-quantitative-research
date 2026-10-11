# EXP002 native index-membership certification

**Gate A FAIL.** Historical timing works in the bounded transition fixtures, but population/identity completeness does not. No candidate performance or 2021+ observations were accessed.

SDK 1.42.0: `IsIndexMember(asset, index="SP500")` emits `{"type":"IsIndexMember","targetAsset":<Stock>,"index":"SP500"}`. The asset can be `CANDIDATE` in a dynamic filter. `universe("SP500")` is available; its audit `universeSize` is a candidate pool, not a dated membership certificate. The preferred tested declaration is this native pool filtered with `IsIndexMember(CANDIDATE,"SP500") == True`; zero deployment and an always-false action condition prevent trading.

MCP exposes no standalone `IsIndexMember` operation in the observed tool inventory. Its `create_portfolio` / `build_portfolio` declarations accept `strategies: Array<unknown>`; this is a generic structured-authoring surface, not a separately verified typed membership declaration. Neither authoring operation was called. The actual membership diagnostics used the exact SDK declaration above. Observed declarations are archived privately.

Lake declaration: `lake.index_constituents` has indexCode, indexName, componentCode, componentName, sector, industry, weight, startDate, endDate, isActive. GSPC denotes the S&P 500. There is no stable security ID or publication timestamp in this table. Metadata `isActive` is not used for historical eligibility. The newly bounded query returns 557 overlapping rows; it preserves the prior local reconstruction as a comparison, not an authoritative substitute.

| Mechanism | Native result | Boundary |
|---|---|---|
| AAL addition | False March 20; true March 23–24, 2015 | Lake effective start is March 23 |
| Tesla addition | False December 18; true December 21–22, 2020 | Matches independent index-provider announcement |
| AIV removal | True December 18; false December 21–22, 2020 | Matches the same announcement |
| NU→ES rename | NU true/ES false February 18; reverse February 19–20, 2015 | Previously certified stable-ID span corroborates rename |
| Later-acquired CELG | True November 20, 2019; its audit disappears thereafter | Disappearance is unavailable evidence, not an observed explicit false value |

The [index provider's December 11, 2020 announcement](https://press.spglobal.com/2020-12-11-Tesla-Set-to-Join-S-P-500-100-Apartment-Income-REIT-to-Join-S-P-MidCap-400) specifies Tesla replacing AIV before the December 21 open. Current-known membership is not assumed or queried as market data. Correct cases demonstrate historical timing in those cases; they do not certify missing constituents.

## All 72 monthly population samples

One existing diagnostic daily simulation covers 2015-01-02 through 2020-12-31, with no orders. Seventy-two one-session event queries retrieved both open and close, exactly two NoSignal observations per page. Full native allocations supply member symbols; they are not truncated `passedAssets` examples. These populations precede any nominal-price or ownership-coverage exclusion. The native input pool is about 768–770; actual filtered populations range **385–475**. January 2015 has **385**; December 2020 has **474**. Small share-class/effective-date differences cannot explain this material underfill.

The [machine-readable monthly ledger](two_gate_summary.json) reports native/Lake counts and both symbol-difference counts with bounded examples, unique stable IDs (384–475), unresolved identity counts (0–3), observed month-to-month ticker changes and removals by the last monthly sample. Security spans were independently extracted, with historical date-valid joins. Mapping the observed members does not recover absent members. The removal count is within these observed samples, not a census of every later delisting. Counts are audited execution opens, not certification of the preceding-day 21:00 universe.

**No production universe is adopted.** Native date semantics pass selected transitions, but unexplained missing historical names remain a critical survivorship/completeness risk. We do not infer the vendor's cause, repair missing names with today's symbols, or try another increasingly complicated substitute. Gate A FAIL terminates that investigation under the owner stop rule.
