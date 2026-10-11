# EXP002 point-in-time audit

All PIT flags remain false. VERIFIED means sample/declaration behavior within the stated scope, not complete native runtime safety.

| Input | Observed evidence | Unresolved |
|---|---|---|
| Insider | Filing-date-end availableAt, originals/amendments in 90 combined samples; native AAPL zeros in a source-populated window with no P rows | Universal zero/missing contract, owner deduplication, amendments, ingestion delay and exact acceptance timestamp (absent from inspected schema) |
| Insider amounts | 232,152 of 232,685 P acquired rows have null totalValue; 533 are nonnull | Native shares × price reconstruction and missing operands; compilation does not establish amount equivalence |
| Insider timing | 24 P acquired rows have economic dates later than availability; other report/transaction anomalies exist | Native temporal rejection and full row-level quality rules |
| Institutional | Public availableAt, quarter/accession/version metadata; median original-filing delay 43–44 days, p95 45–48 in isAmendment=false groups | Frequent null amendment flags; complete public-quarter cohorts and native amendment equivalence |
| Market cap | Live schema: unadjustedClose × sharesOutstanding, sharesAsOf/availableAt/accession/scope; source presence measured | Older null lineage, stale/class versus issuer shares, native Fundamental parity and filing-vintage reconstruction |
| Liquidity | 20-prior-row mean(unadjustedClose × volume), current row excluded; catalog says finalized EOD refresh at 21:00 NY | Unique exchange sessions, volume adjustment, publication/revision vintage and native lag composition |

## Missingness policy requirements before Development

Preserve null, absent row, explicit zero, stale observation and errors separately. Absence is never automatically zero. AAPL shows a sample purchase zero with other source activity but no qualifying P record; a universal true-zero rule still needs complete feed/identity evidence. No filing differs from no vendor record; notice-only 13F differs from a complete holdings report. Missing amount operands invalidate amounts, not counts automatically.

Unknown subtype, ambiguous identity, missing availability, unverifiable cap lineage and economic dates after public availability require explicit exclusions/quality flags, never replacement from later data. A/M/F are not purchases; P includes private purchases. Stale last-public values retain their age and date. Proposed recency windows are not empirically certified freshness thresholds.

## Availability and versions

Use timezone-aware availableAt, never transaction/report date. Filing-day-end data cannot inform that day's earlier open/close; execution must follow availability. Exact acceptance/ingestion timing was not exposed.

Raw originals and amendments coexist. Resolve amendment status from submission type and explicit flags, flag conflicts/nulls and preserve both versions. RESTATEMENT replacements and NEW HOLDINGS additions must become effective only when public. Insider samples retain an original and amendment with a corrected reporting period; this does not prove native revision-chain behavior.

At January 8, 2016, AAPL had 2,144 public Q3 reporting managers versus 43 Q4 managers. Raw share sums include versions and are not native reconstructions. Choose a reproducible public-quarter/completeness rule and matched cohorts before freezing the institutional representation. A fixed 45-day lag is insufficient evidence: some p95 delays exceed it and amendments can be much later. No maximum staleness threshold is frozen.

The corporate probe records cash dividends on pay date but no split event across the split window. Full adjustment/merger/delisting equivalence and dividend basis remain unverified. If cap PIT cannot be proven, a cap-free price/liquidity alternative may be reviewed; it is not silently substituted.
