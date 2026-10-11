Aurora EXP002 research memo
EXP002 remains a planning memo, not an executable or performance result. No portfolios, candidates, backtests, optimization jobs, trades, brokerage connections, or account changes were made. No market or signal observations beyond the 2020-12-31 formation cutoff were retrieved, and no held-out period was accessed.
Verified documentation and coverage metadata
- Insider data: NexusTrade documents insider_transactions for reported derivative and non-derivative transaction legs and insider_filings for filings and reporting-owner combinations. Publicly documented backfill begins in 2006 Q1 and extends through 2026 Q2. This is coverage metadata, not evidence that every ticker, field, or date is complete.
- Institutional data: institutional_holdings contains reported 13F holding legs and institutional_filings contains 13F submissions with reporting-period and amendment metadata. Publicly documented backfill begins in 2013 Q2. 13F data does not reveal all between-quarter trades, excludes short positions, and only covers securities within the 13F reporting framework.
- Point-in-time availability: SEC-derived rows use availableAt, with quarterly availability assigned conservatively to the end of the filing date in America/New_York. Transaction dates and reporting periods are not substitutes for public usability timestamps. A fixed lag does not automatically eliminate revision risk.
- Insider syntax: public documentation includes examples like InsiderTrades(AAPL, BuyCount, OfficerOrDirector, 90) > 0. DistinctBuyers and BuyValue still require exact declaration/unit/support verification.
- Institutional syntax: documentation includes examples like InstitutionalHoldings(AAPL, empty manager, NetShareChange, 180) > 0. NewHolders is documented as a count of managers opening positions. NetHolderChange and exact units/behavior still require native declaration verification.
- Momentum: technical building blocks appear available, but the exact EXP002 Rate-of-Change declaration, arguments and 126–252-session support remain unverified.
- Dynamic universe: Nexus documents an ALL_US_STOCKS-style universe, filtering/ranking, dynamic rebalancing and historical delisting handling at a high level. Exact 2015–2020 PIT membership, security-type exclusions, identifier changes and missing-identifier behavior remain unresolved.
- Custom point-in-time data supports availableAt and point semantics, but this does not prove every native insider/institutional field has complete revision history.
- Lake/catalog access is read-only, but completeness for the required EXP002 universe and fields has not yet been established.
Candidate families
1. Momentum only
2. Insider only
3. Institutional only
4. Momentum + insider
5. Momentum + institutional
6. Insider + institutional
7. Full composite
8. SPY buy-and-hold
9. Equal-weight dynamic eligible universe
Proposed ranges remain untested:
- momentum: 126–252 trading sessions
- insider: 30–90 calendar days from disclosure availability
- institutional: 180–365 calendar days of filing updates
- holdings: 20–40
- rebalance: monthly baseline; weekly robustness
- ADV: $10m–$25m trailing 20 sessions
- market cap: $1bn–$5bn PIT
- funding: $25,000
- fee: 0.10% per stock fill
- cash dividends
- 95% deployment
- daily simulation
- proposed next-session execution
- roughly 400 calendar days warm-up
Freeze blockers
- exact support/units for DistinctBuyers, BuyCount, BuyValue, NewHolders, NetHolderChange, NetShareChange
- exact momentum/ROC declaration and support
- PIT market-cap and lagged dollar-volume fields
- complete historical dynamic common-equity universe including delistings/security-type filters
- amendment/revision handling
- joint field-level 2015–2020 coverage and missingness
- execution timing, slippage, corporate actions and prospective rebalance metrics
- historical lockbox
- actual cost/query/job estimates
The hypothesis should be considered weakened/falsified if the full composite does not improve matched momentum-only performance under the same PIT universe/execution assumptions, or if apparent gains disappear under availableAt, amendments, costs, capacity and missingness controls.
No paid query, preview job, agent job, backtest, optimization, trade or deployment occurred.
EXP002 is not execution-ready.
