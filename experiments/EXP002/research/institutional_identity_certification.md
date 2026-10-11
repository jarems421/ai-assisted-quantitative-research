# EXP002 institutional identity certification

**Gate B FAIL.** Keep the matched-manager signal definition; no native NetHolderChange fallback. Failure is lack of a certified candidate-security CUSIP mapping and complete as-of filing contract, not the mere presence of unresolved unrelated securities.

## Pinned published resolver

Inspected code revision **aaa6e7a8d8a00d22d221e288d9f2f3e0a6150625**, package **0.4.1**. Public dataset metadata revision **0662635d4adddd295ba93530fa0de51aa453b97d** and snapshot.json were saved; no dataset observation files were downloaded. This public snapshot revision is **not established as the deployed Nexus dataset/code revision**. The actual Lake response bytes are pinned by receipt hashes; deployed revision remains undisclosed.

The [actual resolver](https://github.com/austin-starks/sec-ownership-disclosures/blob/aaa6e7a8d8a00d22d221e288d9f2f3e0a6150625/src/extraction/resolveHoldingTickers.ts) takes `TickerSpan {cusip,ticker,fromDate?,toDate?}`, matches each holding on its availableAt UTC date, preserves ticker case and returns null outside all spans. However, undated spans apply to every date and overlapping covering spans use the first match. Its tests expressly preserve these behaviors. Thus the existence of this function does not establish unique, dated mappings in the deployed feed.

The [N-PORT builder](https://github.com/austin-starks/sec-ownership-disclosures/blob/aaa6e7a8d8a00d22d221e288d9f2f3e0a6150625/src/extraction/cusipTickerCrosswalk.ts) produces CUSIP/ticker/ISIN/source pairs, not certified validity spans. The [OpenFIGI client](https://github.com/austin-starks/sec-ownership-disclosures/blob/aaa6e7a8d8a00d22d221e288d9f2f3e0a6150625/src/sources/openFigiClient.ts) returns shareClassFigi, US ticker and venue tickers; it is not itself historical listing evidence. [README guidance](https://github.com/austin-starks/sec-ownership-disclosures/blob/aaa6e7a8d8a00d22d221e288d9f2f3e0a6150625/README.md) warns against undated mappings and foreign venue/currency suffix stripping. Its older METHODOLOGY text still calls mapping unfinished; that disagreement is retained, not resolved by treating prose as deployed behavior. No post-cutoff N-PORT or mapping observations were fetched.

## Exact required identity contract

For each candidate require original CUSIP, accession, manager CIK, reporting quarter, availableAt, resolved ticker, stable security ID, mapping source, mapping validity interval, mapping status/confidence and explicit date basis. Require a unique certified mapping valid at the relevant public-availability instant; keep case and venue/currency suffixes intact. Check the stable ID against the historical listing span. Undated, conflicting, outside-span or unsupported mappings remain unavailable. Resolver UTC-date semantics must be reconciled with listing-date semantics at midnight boundaries; a listing span alone is not a dated CUSIP mapping.

The observed holdings schema exposes accession/infoTableSk/availableAt/cusip/figi/resolvedTicker and transaction-class fields, but **not mapping source, validity span, confidence or stable identity**. The listing table exposes stable security_id/share_class_figi and listing spans but not original CUSIP. Joining solely through resolvedTicker cannot prove the omitted CUSIP mapping provenance. The fixed twelve-symbol sample yields 32 CUSIP/listing combinations; some stocks have multiple CUSIPs, so issuer-level ticker agreement is not sufficient share-class identity. No alternate simplified crosswalk was fabricated.

## Omission-as-zero

For security S, manager M, quarter Q: require a certified complete eligible filing, complete raw CUSIP rows, reconstruction at the decision time, correctly applied public amendments/additions, and S's unique dated CUSIP/security identity. Only absence of that CUSIP from this complete reconstructed state establishes NOT_HELD. Missing filing, filtered-out raw rows, missing S mapping, conflicting amendments or future state means UNAVAILABLE. An unresolved unrelated bond need not invalidate S once these requirements are independently satisfied. This refines the earlier blanket unresolved-row concern without weakening S's identity gate.

`src.research.two_gate_exp002` implements fail-closed validation of supplied resolver evidence and this omission contract; it does not invent mappings or certify production inputs. Synthetic tests verify software behavior only.

## Date-stratified coverage and real usability

Sample years were fixed at 2015, 2017, 2020; adjacent Q2/Q3 cohorts, 60-calendar-day maturity. Source queries cover July–November only. The twelve symbols are the previous mechanism-audit anchors plus AAL/TSLA transition controls, selected without performance. The monthly native panel identifies ten eligible sample symbols in 2015/2017 and eleven in 2020; TSLA is correctly absent before its December addition. These are eligible under the tested membership source, not a certified complete universe or nominal-price screen.

| Year | Filing snapshots | Holding rows | Nonnull ticker resolution | Matched public original managers | Known-union coverage | Certifiable omission securities |
|---|---:|---:|---:|---:|---:|---:|
| 2015 | 8,436 | 3,281,143 | 71.36% | 3,989 | 97.08% | 0 |
| 2017 | 8,951 | 3,427,465 | 82.12% | 4,272 | 97.47% | 0 |
| 2020 | 10,920 | 4,181,982 | 90.61% | 5,216 | 96.31% | 0 |

All 28,307 extracted filing summaries have rowCount=distinct infoTableSk count. This proves grain uniqueness, **not filing completeness**. Per-filing unresolved-CUSIP sums are 671,664 / 438,396 / 302,960; these are not global unique CUSIPs. Original managers are counted only once public within the maturity gate. Late versions remain in the raw extraction. Public-manager coverage is not security-specific completeness; no production holder-count changes were calculated. Full per-filing distributions and per-date sampled securities are in [two_gate_summary.json](two_gate_summary.json) and ignored source receipts.

The prior six fully extracted original/amended filings establish local CUSIP-only replacement/addition mechanics but lack certified listed-security mapping. In this pass the number of complete **identity-certified** manager filings and certifiable omitted sample securities remains **zero**, rather than a manufactured estimate. A meaningful production cohort therefore has not been demonstrated.

Keep **20 matched managers / 95% public-known union coverage / 180-calendar-day quarter/publication staleness**, based on the prior complete distribution and this source-only sample, not returns. Threshold changes cannot cure missing identity certification. These fixed rules are recorded for history; no candidate evaluation is authorized.

## Decision

Gate B FAIL. The owner stop rule applies: both gates failed, so **ABANDON EXP002** as a negative research-design feasibility result, not an economic falsification. No momentum+insider fork is created or executed. No broad revision or further source substitution is initiated.
