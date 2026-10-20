# Proposed pilot: does public-web adoption measure a real business change?

**PROPOSED_FOR_OWNER_REVIEW, 2026-10-20. No acquisition, policy activation, experiment registration or economic analysis is authorized by this document.** This is a new descriptive research proposal. It does not change EXP004 or reuse any old experiment's approval, trial reserve or sealed-stage access. [Rationale](reorientation_review.md) · [Backups](opportunity_map.md) · [Source evidence](evidence_review.md).

## Question, null and scope

Customer-controlled websites can expose use of a web platform. Persistent changes in a comparable observed installed base might contain information about its vendor's paid business. The first question is whether that information improves a simple forecast of the next quarterly operating metric. Only if it does should this pilot inspect a possible delayed equity-return relationship.

**Mechanism null:** the single adoption measure adds no predictive information beyond the vendor's latest publicly reported operating trend. **Return-screen null:** positive adoption observations have no positive subsequent vendor-minus-software-sector return after the specified cost deduction. Both are predictive associations. Neither identifies a causal effect of installing software on a stock price.

Proposed cases are **Shopify / SHOP** and **Wix / WIX**, selected for observable web-platform products and separately disclosed subscription metrics. They are a deliberate, small case study selected today, with historical-knowledge and survival-selection limitations. Results will not represent all software firms, delisted vendors or the entire public web. No replacement vendor is selected for a weak result or inconvenient coverage.

The report's millions-of-sites ambition is deferred. The initial cohort is the 50,000 lowest SHA-256 canonical-origin hashes among successful desktop root-page observations in **December 2019**, regardless of technology. Freeze its full membership before later observations. This targets adoption changes among those baseline observed origins, not all new internet businesses. Preserve source HTTP/HTTPS/port distinctions; do not assume an origin equals an independent customer or company.

| Boundary | Proposed value |
| --- | --- |
| Source warm-up | January–December 2019; no returns needed |
| Measurement/screen interval | 2020–2023; historical reconstruction and exploratory outcomes |
| Economic date bounds | Return entry and exit must both fall within 2020-01-02–2023-12-29; retain boundary-excluded observations explicitly |
| Later potential confirmation | 2024–2025 return windows remain unread by this pilot; separate reviewed design and owner authorization required |
| Genuine forward evidence | Starts only after a later freeze and elapsed future observations; none exists here |
| Search scope | Two vendors, one source family, one adoption transform, one primary horizon, one business model; every diagnostic retained |

Some issuer disclosure examples for 2023/2024 were visible during this review. No fundamental dataset is claimed unseen. The later return window would be workflow-held-out only, with modern-model and previous project knowledge disclosed. Existing experiments' controls remain intact; a new descriptive output never advances their Store state.

## Minimum real inputs and joins

Only the following inputs are proposed. Exact query/schema and example receipts must be saved before expanding the sample. No source data was retrieved to populate these tables during the strategic review.

| Input | Exact source / required fields | Key and historical join |
| --- | --- | --- |
| Web observations | [`httparchive.crawl.pages`](https://httparchive.org/docs/reference/tables/pages): `date`, `client`, `page`, `root_page`, `is_root_page`, `wptid`, `technologies.technology`, success evidence and available detector/crawl metadata. Earlier partitions may require the publisher's documented legacy schema; inspect, never guess parity. | `(crawl_label, client, canonical_origin)` plus original page/WPT locator. Keep duplicate/retest observations and resolve by a fixed source-order rule only when equivalent; conflicts unavailable. |
| Technology definition | [HTTP Archive Wappalyzer fork](https://github.com/HTTPArchive/wappalyzer), actual historical crawler/detector configuration and label lineage | `(technology_label, definition_version, effective_month)` → product → dated vendor/issuer evidence. Freeze relevant definitions; no issuer-specific post-result patches. |
| Source availability | [Release process](https://httparchive.org/docs/guides/release-cycle), dated original release announcements/object evidence for the specific partitions | `(partition, source_version_hash)` → evidenced public upper bound, basis, retrieval time. Crawl label and test date remain separate. A table last-modified timestamp alone cannot prove the earlier version contained today's values. |
| Operating targets | [Shopify results](https://www.shopify.com/investors/financial-reports), [Shopify annual reports](https://www.shopify.com/investors/annual-reports), [Wix quarterly releases](https://investors.wix.com/financials) and original issuer filings | SHOP: monthly recurring revenue (MRR); WIX: Creative Subscriptions ARR. `(issuer, fiscal_quarter, original_release_hash, metric_definition)` with exact value/unit and first publication bound. No fallback to whichever KPI correlates best. |
| Securities | Original period-appropriate issuer cover/exchange evidence, then [Tiingo EOD metadata](https://www.tiingo.com/documentation/end-of-day) as a provider cross-check | Proposed SHOP Class A subordinate voting shares, WIX ordinary shares; US-listed lines, no Canadian/US series splicing. CIK/product identity and share-class/provider identity are distinct. IGV and SPY remain separate ETFs. Dated mapping is required for these four instruments only. |
| Return measurements, conditional | `https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate=2019-01-01&endDate=2023-12-29`, daily frequency, for SHOP/WIX/IGV/SPY only; `close`, `adjClose`, `volume`, `splitFactor`, `divCash`, date and metadata | `(verified_class, session)` aligned to one US session calendar. No latest/global ticker enumeration or source switch to fill an inconvenient return. Provider rights/entitlement must permit this use. |

The technology source/fields and both issuer financial-report indexes were verified in publisher documentation. Historical partition access, detector lineage, release bounds, complete KPI series and the four dated provider bindings remain **NOT_VERIFIED_FOR_THIS_PILOT**. An index with historical year selectors is not proof that every original release can be retrieved. Follow evidenced links, not guessed filenames. The first day's output must say what actually exists, with actual sample counts.

Minimal local outputs, if approved: `origins.parquet`, `vendor_month.parquet`, `kpi_quarter.parquet`, and conditional `event_returns.parquet`, plus one manifest of source hashes, query/configuration versions and attempts. Reuse existing immutable-byte/JSON helpers. No new registry, service, event bus or generic warehouse.

## Observation and information time

Keep five fields distinct: crawl's nominal month, actual test time, specific dataset/version publication bound, present retrieval time, and the signal's usable time. HTTP Archive's current guide explicitly warns that a first-of-month table label can precede the actual crawl. Some historical technology results were also produced retrospectively. A modern detection on old HTML cannot become a contemporaneous 2020 observation merely because the page was captured then.

For each scored month, require a defensible public upper bound for the **data version and detector result being used**. A date-only release receipt becomes end-of-day in its evidenced timezone; unclear timezone means unavailable until bounded. Signal time is the latest bound of every contributing observation/definition, including the December 2019 cohort dataset. No measurement can be used before that baseline cohort was publicly constructible. A subsequent persistence check cannot be backdated to the first sighting.

**Proposed conservative screen convention:** use the first audited US regular-session close at least **48 elapsed hours after signal time**. This is a new modeled waiting rule submitted for approval. It is not an observed fill, a claim about exact first-public accessibility, or activation of an older SEC availability policy. Apply the same rule to every observation. Weekend/holiday/early-close handling follows the declared calendar, not 20 calendar days.

If historical source versions/public bounds cannot be established within day one, label the retrospective source gate failed. A table label plus an arbitrary month-end/30-day delay does not cure revision leakage. No massive WARC recovery is allowed in this pilot. A future first-seen measurement could be proposed separately, with a longer horizon to results.

## One feature and one business test

For origin `d`, vendor `v`, and monthly crawl `t`, define `X[d,v,t]` as present, absent or unavailable. **Absent requires a successful relevant crawl and a valid detector execution capable of detecting that vendor.** Missing crawl, ambiguous redirect, detector failure or uncertain label lineage is unavailable.

Use only origins in the fixed cohort with valid observations in all four months `t-3` through `t`. Count persistent additions `0,0,1,1` and persistent removals `1,1,0,0`. Let `B` be vendor-positive origins at `t-2` within that same four-month comparison cohort. The sole primary feature is:

```text
S[v,t] = (persistent_additions[v,t] - persistent_removals[v,t]) / B[v,t-2]
```

If `B < 100`, the vendor-month is unavailable. Report cohort retention, successes, missing observations, positive counts, additions/removals and exclusion reasons at every month. Do not redistribute missing sites' weights or rank-weight the feature. No CrUX popularity weighting, CT corroboration, 5/10-session horizon, detector ensemble or additional feature is selected after results.

Detector lineage is a measurement prerequisite. The 2023 crawl-scheduling change must be labeled and checked for a discontinuity. Root-only/desktop-only prevents the later addition of interior pages or combined mobile/desktop observations from inflating customer counts. A technical discontinuity that explains the purported signal ends the present transform; it is not patched after observing returns.

For the business test, use quarter-end cutoffs `q`: choose the latest monthly feature **available at that cutoff**, then predict the following quarter's year-over-year log growth in the one specified metric. Only original disclosed targets are used. At each cutoff, the benchmark forecasts the latest year-over-year metric growth already public at that time. A later comparative/restated value cannot replace the earlier target or predictor.

The augmented forecast is `benchmark + b*S`. Fit **one shared scalar coefficient** by least squares on previously public target residuals; no intercept, nonlinear model or feature search. Require eight completed quarterly origins before scoring; expand training chronologically. Score only targets ending by 2023-12-31. Pool comparable dimensionless growth errors, and also report each vendor separately. All lags are enforced using disclosure time, not quarter end. The actual number of scoreable quarters remains to be measured; it will be small.

Proposed mechanism GO requires at least six scored calendar quarters covering both vendors, a pooled MAE improvement of at least 5% over the benchmark, and nonnegative improvement for each vendor. Report the raw errors and each quarter's contribution. A single common macro quarter or definition/pricing break driving the improvement yields INCONCLUSIVE, not proof of a demand signal. These are proposed investment-of-research-time gates, not significance thresholds or certified power. MRR/ARR can rise through pricing rather than adoption; disclose known pricing/perimeter changes and retain the periods, without selecting exclusions on outcome.

If the mechanism gate fails, publish the result and stop before stock returns. If the target series is inconsistent/unavailable, record source feasibility failure and do not silently substitute revenue, customer counts or another vendor. This does not reopen EXP005's annual-revenue hypothesis.

## Conditional first stock-return screen

Freeze this section and the actual source/feature hashes before any return calculation. The report's wording about freezing only after finding delayed incorporation (PDF p. 17) should not be followed literally: that would allow outcome-informed specification. Business screening and any later stock screen are counted in the new attempt log; failed runs and negative diagnostics remain visible.

For each eligible vendor-month, let `e` be the proposed entry-close session and `e+20` the twentieth subsequent session. Measure:

```text
R[v,t] = adjusted_close[v,e+20] / adjusted_close[v,e] - 1
E[v,t] = R[v,t] - R[IGV,t]
primary active observation = S[v,t] > 0
net_excess_screen = E[v,t] - 0.0020
```

The one primary outcome is the mean net excess across positive-signal observations, with vendor-specific means and an equal-vendor summary shown. Subtract 20 bps roundtrip from the active vendor leg without crediting benchmark trading costs; also show a 40 bps deduction and a fixed +1-session entry/exit shift. IGV is the proposed software-sector comparator; SPY is secondary. Show unconditional vendor-minus-IGV means and nonpositive-signal observations to expose a generic vendor/sector effect. Report prior 20-session relative momentum and a predeclared linear momentum-adjusted descriptive association; it is a control, not an alternative optimized trading rule.

This is an **uncompounded event-return comparison for a hypothetical long-only rule**, not a portfolio NAV or a self-financing hedged return. Overlapping 20-session windows cannot be summed as independent capital allocations. Prices are measurement endpoints; neither a guaranteed closing-auction fill nor nominal-share execution is certified. Do not calculate portfolio Sharpe, realized slippage, capacity, terminal cash or trade counts from this table. No stock borrow is assumed.

Negative checks are fixed before outcomes: (1) compare the identical feature with the preceding 20-session return, to expose reverse timing/price-trend effects; (2) show a one-month-lagged feature as a staleness diagnostic; (3) show detector/crawl coverage changes versus the feature; (4) separate vendor and calendar-year contributions. They are disclosed diagnostics, not a search for whichever version turns positive. A lead-feature computation using future installations is prohibited as a trading result. A placebo's nonzero association is not automatically a failure; explain shared trends and seasonality.

Minimum screen support proposed: 30 eligible months per vendor, at least 24 shared months, and at least 10 positive and 10 nonpositive months per vendor. Keep all attempted months and missing/boundary states. Fewer observations means INCONCLUSIVE, with no later date extension. Thousands of customer sites increase measurement precision, **not** the independent number of return observations. At most 48 calendar entry months exist in the proposed interval before source/edge losses; two stocks remain only two stocks. Persistent sector/regime exposure and overlapping horizons make a universal p-value unjustified. Report estimates and dependence sensitivity; no formal significance/80%-power or alpha certificate is promised.

An economic GO means further validation is worth commissioning: primary net effect positive, positive at doubled costs and +1-session shift, positive separately for both vendors, positive active-minus-unconditional excess contrast within each vendor, and no single calendar year supplies more than half the sum of positive year-level contributions. A positive momentum-adjusted feature association must also remain; generic persistent vendor outperformance is not adoption information. Otherwise record negative, fragile or inconclusive evidence. This is a **research-priority gate**, not proof of an investable discovery. New inference and an untouched validation contract belong to the next milestone; no failed legacy method is reused as certified.

## Prices, actions, missingness, costs and capacity

Use the vendor's documented split/dividend-adjusted close ratios as a reconstructed total-return **measurement**, preserving original raw closes/actions alongside them. Confirm methodology and example split/dividend transitions for these four instruments; do not add cash dividends again. Adjusted levels are never signal inputs, price thresholds or nominal-share fills. Today's corrected prices and action-adjustment vintage are a disclosed measurement limitation, not a contemporaneous feed.

Require positive finite unique endpoints, dated class/provider agreement and correct calendar alignment. Missing endpoints or an ended/reorganized instrument with no evidenced economic return stay unavailable and remain in the sample accounting. No forward fill, adjacent-price substitution, current-ticker rewrite or deletion. If unresolved endpoints materially undermine the fixed four-instrument screen, stop the screen; there is no provider-rescue campaign or surviving replacement. An ordinary split handled consistently in adjusted ratios does not require rebuilding EXP004's raw-share ledger.

Hypothetical liquidity check uses only trailing 20-session raw dollar volume known before entry. Proposed minimum average dollar volume is USD 10 million. Illustrative USD 10,000 total, two fixed USD 5,000 slots, would be 0.05% of that daily volume per active slot; that arithmetic is not a fill/impact or production-capacity certificate. Unknown volume/class stays unavailable. The cost deductions do not cover every spread, tax, financing or market-impact cost. Neither paid data nor actual capital deployment is proposed.

## Proposed one-week schedule and ceilings

Five working days within **2026-10-21–2026-10-27**, if approved in time. Dates may shift together with approval; the effort limits do not. Weekend days have no unattended collection. Maximum **40 working hours**, primary source gate at eight hours, backup source checks at two hours each, no fourth candidate. At most **one family reaches a return screen** this week. A measured negative result ends the economic sprint; backups do not become an undisclosed performance tournament.

The new plain attempt log has a proposed ceiling of **nine economic analyses**, including failed/unresolved attempts: one business-model/baseline comparison, one primary return comparison, doubled-cost and +1-session sensitivities, four fixed negative checks and one momentum-adjusted association. Tables broken down by vendor/year describe those same analyses. Deterministic replay is not another hypothesis. No grid, feature/horizon swap or replenished reserve; none of the earlier experiments' evaluation allowances is used.

| Day | Work and measurable deliverable | Stop/go |
| --- | --- | --- |
| 1 — Wed 21 | Freeze a short question/source card. Inspect two fixed four-month blocks: Jan–Apr 2020 and Apr–Jul 2023. Dry-run query costs; retrieve a small neutral origins sample only after access/rights checks. Record actual counts and release/detector evidence. | No usable historical versions/bounds, unaffordable query or no legitimate access → stop primary by eight hours. Do not build a crawler. |
| 2 — Thu 22 | If primary passes, create the bounded cohort/panel and exact KPI definitions. Report actual coverage, unavailable states, example transitions and dated joins; verify return-date join code with fake prices. | Historical lineage must support every scored row; no later detector backfill passed off as old data. If blocked, at most two hours each on backup 1 then backup 2 source feasibility. |
| 3 — Fri 23 | Run the single rolling business-metric comparison with target/publication clocks; publish errors, coverage and definition breaks. | Fail/insufficient support → finish with that result. Pass → retain exact source/feature hashes and proceed to the predeclared conditional screen. |
| 4 — Mon 26 | Only after the mechanism gate, retrieve the four bounded price series, audit actions/identity/calendar, create a tiny complete event-return table, then run the same calculation for all eligible months. | No source substitution or outcome-driven parameter change. Evidence table must include failed/unavailable observations and benchmark returns. |
| 5 — Tue 27 | Run fixed cost/delay/negative checks; generate a compact report and one useful plot; independently inspect joins/counts, run focused tests, commit/push. | Deliver measured negative/fragile/inconclusive evidence or a case for a separate validation. No automatic next phase. |

Proposed access limits: **USD 0 paid spend**, no billing enablement, no upgrades. BigQuery sandbox/project must have adequate unused free allowance: dry-run each query, set `maximum_bytes_billed`, cap each at 25 GiB and the week at 512 GiB; storage/export at 2 GiB. If below-cap execution is infeasible, stop rather than spend more. A `LIMIT` or hash filter alone is not a query-cost cap. Free availability is account-dependent; no current quota was inspected. [Publisher controls](https://docs.cloud.google.com/bigquery/docs/best-practices-costs), [free-program description](https://docs.cloud.google.com/free/docs/free-cloud-features).

Proposed requests across the whole week, including a backup: at most 12 executed BigQuery queries, at most 120 ordinary documentation/definition/issuer/public-source HTTP starts including retries, and 8 market starts (four metadata, four bounded price histories). One worker, at most one HTTP start/second or any stricter published rule; query jobs run serially. Save every result/error; do not blindly resubmit uncertain jobs. No retry on denial, identity bypass, proxy, cloud scrape or alternate paid provider. Dry-run/metadata operations and exported bytes are recorded separately. These limits are a planning proposal, not debit evidence or authorization today.

The first successful test is a reproducible source-to-business comparison with real observations, a frozen denominator and an interpretable negative or positive estimate. If it reaches prices, the deliverable adds the exact dated return/benchmark pairs and predeclared cost sensitivity. It is successful research even when the claimed relationship is absent. It is not yet a strategy ready for funding.
