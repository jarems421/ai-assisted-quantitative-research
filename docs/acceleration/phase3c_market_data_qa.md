# Phase 3C: market-source QA

**PARTIAL observations; zero cases fully certified for historical NAV.** All requests are tied to the frozen cohort and fixed 2019–2020 range. No raw/adjusted price performance, signal return, strategy correlation, Sharpe, drawdown or alpha was calculated. Provider bodies/metadata remain ignored under internal-use restrictions.

Aggregate source QA: `{"diagnostic_full_calendar_passes": 41, "dividend_events": 252, "duplicate_sessions": 0, "invalid_rows": 0, "nonempty_responses": 45, "original_pre_event_dividend_probe_passed": 6, "price_http200_responses": 54, "received_rows": 22075, "separate_cash_exdate_internal_consistency_passed": 252, "split_events": 4, "split_probe_passed": 4}`. HTTP200, nonempty response, diagnostic full-calendar match and certified listed-history completeness are distinct. Nine empty price responses do not become observed no-trading states. Split-only factor checks match the source's stated split multipliers. The original unverified pre-event cash-adjustment probe is retained with its failures; a separately labelled ex-date cash/price probe tests the CRSP convention referenced by Tiingo. Both use only adjustment factors, not security/portfolio returns. An internal same-vendor match cannot certify dividends independently. The [Tiingo ex-date definition](https://www.tiingo.com/documentation/corporate-actions/dividends) and publisher-indexed CRSP descriptions motivate the second probe, but the linked CRSP guide's live retrieval failed; no full current methodology certificate is claimed. Same-day split/distribution basis, payment timing and terminal transitions remain unresolved. No extra corporate-action API entitlement was assumed or queried.

| Case | Metadata | Received / diagnostic expected sessions | Raw/session status | Listing span |
| --- | --- | --- | --- | --- |
| 0000004962/AXP | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000014693/BF.A | False | Unavailable | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000021344/KO | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000027419/TGT | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000031235/KODK | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000040545/GE | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000050863/INTC | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000051143/IBM | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000077476/PEP | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000078003/PFE | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000080424/PG | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000098246/TIF | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000101829/UTX | False | Unavailable | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000104169/WMT | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000200406/JNJ | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000310158/MRK | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000320187/NKE | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000320193/AAPL | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000354950/HD | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000701985/LB | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000718877/ATVI | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000731766/UNH | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000743988/XLNX | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000789019/MSFT | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000796343/ADBE | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000804328/QCOM | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000813828/CBS | False | Unavailable | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000816284/CELG | True | 226 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000829224/SBUX | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000858877/CSCO | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000865436/WFM | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000886158/BBBY | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0000899866/ALXN | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000909832/COST | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0000931336/DF | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001004980/PCG | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001011006/YHOO | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001018724/AMZN | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001045810/NVDA | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001067983/BRK.A | False | Unavailable | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001067983/BRK.B | False | Unavailable | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001108524/CRM | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001141391/MA | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001166126/JCP | False | Unavailable | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001310067/SHLD | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001326801/FB | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001339947/VIAB | True | 234 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001341439/ORCL | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001357204/DUNK | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001403161/V | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001418091/TWTR | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001563922/SUNE | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001564708/NWSA | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001652044/GOOG | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001652044/GOOGL | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001657853/HTZ | True | 0 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001666700/DD | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001744489/DIS | True | 505 / 505 | PASS | UNRESOLVED_LISTING_INTERVAL |
| 0001751788/DOW | True | 452 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |
| 0001754301/FOXA | True | 458 / 505 | UNRESOLVED | UNRESOLVED_LISTING_INTERVAL |

The505-session full-range calendar is a **diagnostic upper frame**, not expected listing sessions for an uncertified ended/name-changed class. Required expected sessions must be recomputed from independently evidenced listing spans; API silence/start/end coverage cannot certify a holiday or delisting. Counts are raw response/session QA only. Rows require finite positive rawOHLC, coherent low/high, nonnegative volume/dividend and positive split factor; duplicates/missing/extra sessions remain explicit. Current adjusted-to-raw/action checks are candidates under a declared CRSP-like formula, not independent corporate-action or terminal certificates.

Even successful split/dividend field retrieval does not certify stock-dividend basis, merger consideration, bankruptcy recovery or position transitions. No portfolio can ever omit a held case or silently lose NAV; the95% source-feasibility target does not weaken that100% held-path requirement. The cohort-wide fully source-resolved market/identity/lifecycle rate is0/60. Free-tier account entitlement and other account usage are unknown; local starts obey the published 50/hour bound and request/byte ceilings, with no upgrade or purchase.
