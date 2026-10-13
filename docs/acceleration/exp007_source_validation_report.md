# EXP007 congressional purchase sprint: original-source validation stop

**ORIGINAL_SOURCE_VALIDATION_BLOCKED. Hypothesis untested; no registration, freeze or Development.** Starting HEAD `bdb884e4342be622ee37b0d5800afaa437587648`, as of 2026-10-13. [Owner instruction](owner_exp007_congressional_2026-10-13.md) authorized one predictive disclosure study, not reopening EXP002–EXP006. EXP007 was verified free in read-only state before source work; roadmap mentions were not treated as registration.

## Pinned source and actual schema

The audited external derived snapshot remains **AUDITED_EXTERNAL_DERIVED**, not PRIMARY_ORIGINAL. Dataset revision `58ffb57382208624bd61a6de68c68782eb26cbf6`, manifest SHA256 `39cf5506dfc968fcaa32126c91fc4c73c11856b5d93799245cc70dd8cf8311d7`, generatedAt `2026-10-12T07:38:23.530Z`. Its original manifest body hash/retrieval timestamps and all 42 file hashes/lengths are in [the canonical receipt](exp007_source_validation_receipt_v002.json). Acquired2012–2025 tables reconcile to 10,277 filings, 175,402 trade rows and 170,934 event versions. Three prior 2020 files were hash-verified cache hits. The incomplete 2026 partitions were not acquired. This is the declared reconstructed snapshot corpus, not every legal disclosure, perfect extraction/resolution or contemporaneous ingestion.

| Required role | Actual upstream field / location |
| --- | --- |
| Logical event/version | events.eventId / version |
| Member/chamber | all tables.memberId / chamber; filerKey, displayName, identitySource and filer names retained |
| Reported ownership | trades/events.owner; trades.ownerCodeRaw; no owner filter or claim that the member personally executed every disclosed household transaction |
| Transaction/date/type | trades.transactionDate / action / actionCodeRaw; events.transactionDate / action |
| Asset description/type | trades/events.assetDescription / assetTypeCode / assetTypeLabel |
| Printed/resolved identity | trades.printedTicker / resolvedTicker / resolutionStatus / resolutionReason; events.ticker is retained only as upstream provenance |
| Official source document | filings/trades.docId; events.sourceDocId / sourceRowIndex; sourceUrl and rawSha256 where available |
| Version information time | events.firstAvailableAt / availableAt / supersededAt; filings/trades.availableAt and availabilitySource |
| Amount | trades.amountBracket / amountLow / amountHigh; event amountLow / amountHigh; descriptive only |
| Contributors | events.contributorRowIds; links are date-filtered before any as-of descriptive count |

[Scope/schema contract](exp007_source_sprint_contract.json) records the actual Arrow types. The existing adapter normalizes camelCase and upstream naive Arrow timestamps as audited UTC epoch values; that representation does not turn modeled EOD into observed website publication time.

## Source-only stages and original validation

Both chambers and all twelve calendar months are observed in the contiguous 2014–2025 corpus partitions. That is snapshot observation support, not legal-universe completeness. The rounded chronological 70/30 rule yields **Development 2014-01-01–2021-12-31**, **workflow-held-out confirmation 2022-01-01–2025-12-31**. Year counts use upstream UTC availability partitions; actual New York entry/exit calendars and stage-edge buffering remain uncertified. This source-only split is not an executable stage certificate. 2012 is partial-year/Senate-only;2013 is Senate-only; neither was silently filled. No return selected the split. Confirmation source geometry was reviewed solely for this owner-authorized stage selection; its market outcomes remain unopened.

The [neutral sample](exp007_original_validation_sample.json) froze 96 Development observations before official original requests:61 House /35 Senate, all eight years,44 purchases /48 sales /4 exchanges,49 printed tickers missing,7 printed/resolved differences and 13 amendment-source observations. This is a validation sample, never the trading population. The corrected resolver ticker was not required to appear in an original.

Official House documents:59 HTTP 200 PDFs covering61 observations. The first frozen Senate paper URL returned403; its exact body/receipt and persisted stop remain immutable. The other34 Senate source documents were not visited, not 34 observed denials. No retry, alternate host, user-agent change, agreement submission, cookie bypass or search workaround followed. One inaccessible paper route does not prove all Senate documents inaccessible.

House PDF text projection is offline with isolated pypdf 6.1.3 and socket access disabled;34 observations have image-only/empty text projections and remain UNKNOWN, not no-trade documents. Image-only extraction is a parser limitation, not absence of purchase evidence. General row reconciliation associates source asset/printed symbol independently of expected action/date, then compares both fields; it cannot hide a date/type disagreement by searching only for matching expected values. The first projection/association receipt is preserved separately. Original character/line/page provenance and raw hashes remain private.

| Field | Agreement | Disagreement | Unknown |
| --- | ---: | ---: | ---: |
| asset description | 27 | 0 | 69 |
| document identity | 27 | 0 | 69 |
| member identity | 27 | 0 | 69 |
| printed ticker | 24 | 0 | 72 |
| transaction date | 27 | 0 | 69 |
| transaction type | 27 | 0 | 69 |

Of 44 purchase observations, 12 have independently matched original transaction-type agreement; 32 remain UNKNOWN. No purchase-type disagreement was established. **This does not certify reliability across the frame and does not prove upstream purchases are materially misclassified.** All Senate validation remains unavailable and early/image-based House evidence remains unresolved. Required cross-source original-field validation is therefore PARTIAL/BLOCKED; no silently House-only or text-only cohort replaces the declared source contract.

## Candidate accounting, timing and unopened gates

Development raw purchase trade records: **62,180**. Explicit stock-code/label candidates: **13,141**; printed ticker present **12,672**, resolved ticker present **432**, reliable source-status candidates **13,093**, unresolved **48**. Unknown purchase asset classes: **46,451**. Stock labels are candidates pending common-equity/provider confirmation; no unknown asset becomes equity and no current ticker is projected backward. These counts precede version/identity/calendar/aggregation certification and are not independent trading-event counts.

Upstream `resolutionStatus=printed` normally leaves `resolvedTicker` null. That retains the printed symbol as an unchanged source candidate; `resolved` uses the separate resolver field. Both fields/status/reason remain intact and null is never relabelled equal or different. The initial diagnostic summary incorrectly required a redundant resolved field for printed status; it is preserved privately by hash, with this corrected schema interpretation separately versioned before any outcomes.

| Upstream UTC availability year | Purchase trade rows | Explicit stock candidates | Source-resolved candidates |
| --- | ---: | ---: | ---: |
| 2014 | 6,228 | 0 | 0 |
| 2015 | 6,766 | 499 | 494 |
| 2016 | 6,818 | 766 | 755 |
| 2017 | 7,811 | 747 | 738 |
| 2018 | 9,209 | 1,972 | 1,964 |
| 2019 | 7,989 | 2,591 | 2,580 |
| 2020 | 9,444 | 3,718 | 3,715 |
| 2021 | 7,915 | 2,848 | 2,847 |

Information time remains **UPSTREAM_MODELED_EOD_NOT_OBSERVED_PUBLIC**. The predeclared entry is09:30 New York on the second regular NYSE session strictly after the New York date of `max(firstAvailableAt, versionAvailableAt)`, strictly later than every effective bound. Exact public availability is UNKNOWN. Half-open supersession is respected; a version superseded before its eligible entry cannot generate that entry. 3,643 Development contributor links are later than their version bound and excluded from as-of counts, while the original arrays remain preserved. This is no claim that every upstream revision/extraction history is independently certified. No real calendar/execution eligibility view was activated.

Future event aggregation remains one stable security/eligible-entry date, unweighted by disclosure/member counts, retaining lineage. No 95% rule over all disclosures was imposed. The estimand is explicitly conditional on source-resolved, provider-confirmed common-equity purchases; it cannot claim unresolved disclosures. Provider/path coverage and the final unique event count are **NOT_MEASURED**, not0% market-provider success. Original validation failed upstream; no provider, price/session inspection, actual-event aggregation, inference candidate, calibration, power, Proof or scientific freeze ran. The SPY paired 20-session hypothesis,10 bps/side cost,0.50 percentage-point threshold, positive 95% lower endpoint and 8-real-evaluation ceiling remain predeclared; no real performance evaluation consumed the ceiling.

## Verification, reproduction and stop

New scientific source starts: **138**: snapshot 78 (39 pinned files and 39 publisher-declared redirects), original 60 (59 House PDFs and one Senate 403). Three prior Parquet cache hits are separate. HTTP{"200": 98, "302": 39, "403": 1}; retries 0; source browser calls 0; market/identity/Nexus/Aurora/purchases/upgrades 0. Exact signed redirect URLs remain private; tracked hashes/timestamps document provenance without publishing tokens. Account-wide debit/usage is UNKNOWN. Local EDGAR/Tiingo credentials were never needed, exposed or committed.

Validation: 436 local tests, 208 public tests, 0 skipped. [Validation receipt](exp007_validation.json). Research pins are unchanged. [Isolated PDF lock](exp007_pdf_requirements.lock) and [BSD-3-Clause dependency/notice hashes](exp007_pdf_parser_inventory.json) reproduce the offline helper. Public report checks require tracked summaries; private audit requires ignored original bodies, pinned Parquet, projections and baseline inventory and makes no source request.

```sh
python -m src.research.congress_sprint_report --check
python -m src.research.congress_sprint_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Recreate the source-only PDF helper with `python -m venv .research/exp007/pdf-env` and that interpreter's `pip install --require-hashes -r docs/acceleration/exp007_pdf_requirements.lock`. Acquisition commands require explicit `--execute`; stopped channels are never routine reproduction. Public CI does not import pypdf or read private bodies. Legacy EXP001 tests use already-opened records only for regression.

**Stopped at the mandatory original-source validation gate under owner section 24.** No spec/freeze SHA, Development effect/interval/p-value or materiality verdict exists. EXP007 remains proposed, unregistered and unfrozen. Performance evaluations and confirmation outcome accesses are **0**. EXP002–EXP006 were not reopened; EXP004 stays paused, EXP005/EXP006 abandoned and absent. No paid provider, SEC identity rescue, other repository audit, Phase 4B, optimization or paper/live action occurred. This is a source-validation limitation, not an economic test of congressional purchases or a claim of alpha.
