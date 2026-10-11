# EXP003 bounded historical universe feasibility

**VERIFIED scoped identity feasibility; PROPOSED production universe.** Local-only, 2026-10-11. No Nexus call or performance calculation. EXP002 source artifacts were read and hashed, never modified. This pass does not reopen its failed index/institutional hypothesis.

Use a **source-covered historical common-equity universe**, explicitly defined by `lake.security_segments` effective spans and completed `lake.sec_daily_ohlc` prices. This drops the requirement to recover every S&P constituent or all US listings. The saved catalog describes listing spans as historical Polygon point-in-time listings; that is verified catalog guidance, not universal database-vintage certification.

Deterministic membership at each proposed decision:

1. Join the historically traded ticker to its inclusive `from_date` / `to_date` span at the completed price date and intended decision/execution dates. Require a nonmissing stable `security_id` and unique identity. A rename is joined through stable identity and must have an unambiguous active execution ticker. Never filter on current `canonical_symbol`.
2. Require unanimous `asset_type='CS'` among matching spans. Exclude ambiguous types, missing IDs, unknown types, ADR, ETF, preferred, warrant, fund and other non-CS types. Same-ID duplicate aliases at a snapshot are unavailable rather than silently combined.
3. Require a finite positive completed prior-session price and sufficient split-safe lookback history for the maximum 365-calendar-day momentum prerequisite. Source price/identity availability must satisfy the existing 21:00 New York cutoff. Retain ended histories while historically active; never require a company to survive to today's extraction.
4. For primary comparisons apply the same certified insider/price coverage intersection to all families and the eligible-universe benchmark. A genuine zero is eligible only with a complete certified source state; missingness is not zero. Keep exclusion ledgers. No return, ranking outcome or post-cutoff observation determines membership.

Rules 1–2 have a reproducible month-end feasibility prototype. Rules 3–4 describe production prerequisites, **not established full daily panels**. The monthly prototype joins at the saved price snapshot date; it does not pretend to reconstruct the first-session rebalance population.

No exchange, OTC, country or venue field exists in the observed security-span declaration. Do not invent a historical exchange filter or describe this population as entirely US exchange listed. CS is the source's common-stock classification, not independent proof of every security's economic subtype. A narrower certified exchange population can be proposed later only with evidence and before performance, not as an extra optimized axis. No arbitrary population target, market cap, ADV or $5 floor is added here.

## Bounded evidence

The immutable saved span extraction contains **15,952 spans**, including **7,286 CS spans**, overlapping 2015–2020. Dates at the source query ceiling were clipped to 2020-12-31. The saved price panel contains **330,404 security-month aggregates**; it has neither full daily bars nor prices in the exported columns. It was produced by a historical ticker/date/CS join, not present-day membership. Its `prior_price_bars` counts cannot establish distinct sessions or a calendar-day horizon and are deliberately unused. ADV, cap and price-threshold flags are also unused.

The local feasibility pass excludes 5,775 rows preceding their month's common latest snapshot and 129 identity/type inconsistencies. It retains **324,500 security-month observations**, with no duplicated same-security endpoint rows. Annual unions (not mean population sizes):

| Year | Identity-supported source snapshot IDs |
|---|---:|
| 2015 | 4,721 |
| 2016 | 4,816 |
| 2017 | 4,854 |
| 2018 | 4,878 |
| 2019 | 4,866 |
| 2020 | 5,067 |

There are **2,242 retained IDs with at least one CS span ending before the cutoff**. Ends include renames and do not prove delisting reasons or merger proceeds; this count demonstrates that the rule does not require current survival. Raw clipped spans do not identify future delistings. Catalog canonical labels may reflect later renames; labels never enter selection.

Exact monthly counts, type counts and exclusions are in [universe_summary.json](universe_summary.json). Original extraction SQL/bounds and source/catalog hashes are referenced by [provenance](../provenance.json); raw data remains private under `data/raw/EXP002/`. Reproduce with `python -m src.research.design_exp003`.

## Warmup and decision

The aggregate panel starts 2015-01-02 and ends 2020-12-31. Prior work extracted 2014 price/ownership warmup and the 2013-12-31 price endpoint, but endpoint coverage and row counts alone do not certify every security's 365-day completed-bar history or genuine-zero insider coverage. **Joint Development start stays unresolved**; 2015-01-02 is only the required schema placeholder. No fold or held-out date is approved. No outer-period observations were inspected.

This source-defined rule resolves the need for complete index membership and supplies a feasible identity basis. It does not resurrect institutional/CUSIP assumptions. Unknown vendor omissions, revisions, venues and delisting economics are disclosed limitations; they are not erased by passing tests. Production joint coverage and compiler certification are the next focused prerequisites, not another general source-search loop. Overall EXP003 is **NEEDS DESIGN REVISION**, not ready for freeze or performance execution.
