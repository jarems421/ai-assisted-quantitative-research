# Web-adoption Day 1: access established, historical-version gate not passed

**DAY1_SOURCE_FEASIBILITY_CLOSED; ECONOMIC_HYPOTHESIS_UNTESTED.** As of 2026-10-20. The owner-approved Shopify/Wix pilot retrieved real historical source observations, but cannot proceed to a historically timed adoption panel under its unchanged contract. The missing evidence is the exact detector/deployment lineage and an evidenced public bound for the same derived values, including the December 2019 cohort. This is a bounded source-feasibility finding, not proof that the data never existed or web adoption has no predictive value.

[Owner approval](owner_web_adoption_pilot_approval_2026-10-20.md) · [Unchanged design](web_adoption_pilot.md) · [Source card](web_adoption_day1_card.md) · [Canonical observations, query/cost and source receipts](web_adoption_day1_receipt.json).

## What was actually retrieved

Six executed, dry-run-checked BigQuery queries returned **180 page-month records**: twenty hash-ordered desktop root pages from each of nine fixed months. Two further payloads and two summaries repeat existing December records, giving 184 delivered rows, not 184 distinct observations. Original responses and query job receipts are private and hash-pinned. The [initial query plan](web_adoption_day1_query_plan.json) and [two-record layout follow-up](web_adoption_day1_query_plan_v002.json) were pushed before their dispatches. The sixth query inspected summaries of the same two records; its exact SQL/hash and pre-dispatch dry run are retained in the canonical receipt.

| Crawl label | Page records | Shopify-labelled records | Wix-labelled records |
| --- | ---: | ---: | ---: |
| 2019-12 | 20 | 4 | 0 |
| 2020-01 | 20 | 4 | 0 |
| 2020-02 | 20 | 2 | 0 |
| 2020-03 | 20 | 1 | 0 |
| 2020-04 | 20 | 1 | 0 |
| 2023-04 | 20 | 2 | 0 |
| 2023-05 | 20 | 2 | 0 |
| 2023-06 | 20 | 2 | 0 |
| 2023-07 | 20 | 2 | 0 |

These are tiny **monthly access probes**, independently ordered by the source root-page hash, not the proposed fixed 50,000-origin cohort. The twenty records in a later month need not be the same twenty origins. Zero Wix labels in these probes is not evidence of vendor absence or weak adoption. No valid-detector absence, persistent addition/removal, feature value or eligible signal time was certified.

The publisher's public technology-report endpoint separately returned **16 vendor-month aggregate rows**, covering both vendors in the two four-month blocks with desktop/mobile counts. These current aggregates demonstrate another accessible measurement surface; they are not the frozen-cohort signal, historical paying customers or revenue. No growth measure was substituted for the selected transform.

## Why the historical source gate did not pass

The live `httparchive.crawl.pages` table is accessible, with the documented technology schema and partition filters. Its table creation timestamp is in October 2024. Five tested dated legacy tables and the older `all.pages` route returned 404. Their absence today does not prove original records unavailable everywhere, and migration does not establish that every present value changed.

The initial December query projected modern JSON paths and found nulls. Inspection of the full payloads corrected that layout assumption: historical fields are `_result` and `_date`. Both examined payloads have successful result code zero and actual December 2019 test instants. Their payloads and summaries did not expose a linked historical detector/version/publication certificate. The first projection's nulls remain in its receipt; they are not described as failed crawls or missing test dates.

Four original-test requests selected from the neutral sample—two December 2019, one January 2020 and one April 2023—returned HTTP 200 with application-level “Test not found”. A separately fetched documentation example had a failed crawl result and was not promoted to a qualifying sample. These findings apply to those routes/records only.

A historical Wappalyzer source commit from April 2020 is accessible and contains both Shopify and Wix rules. Source code existence is distinct from the deployed configuration for each contributing crawl. The publisher's [2019 technology discussion](https://discuss.httparchive.org/t/technologies-table/1587) and [integration history](https://github.com/HTTPArchive/bigquery/issues/19) distinguish runtime collection and historical backfills. They do not identify the exact historical version of each present label.

Publication evidence also matters. A [January 22, 2020 maintainer reply](https://discuss.httparchive.org/t/frequency-of-updates/1846) says the January crawl was still incomplete. The [2023 release discussion](https://discuss.httparchive.org/t/next-monthly-upload/2581) places collection later in the nominal month. Neither a nominal month nor actual page test time is the publication bound required for today's derived detector values. A public bucket-inventory request returned 403 and was not retried; the legacy downloads host had a DNS failure, also retained without retry. No mirror, proxy, broad crawl or massive raw-page recovery followed.

**Disposition:** raw reconstructed labels can be retrieved; the historically usable adoption dataset required by this design was **not established**. The primary gate stopped after approximately 39 minutes, within its eight-hour maximum. This was an early failed prerequisite, not an eight-hour exhaustive search of every possible archive. No cohort expansion, business targets or market data followed.

## Ordered backup checks

| Backup | Actual observation | Disposition |
| --- | --- | --- |
| Software consumption, first | Retrieved all **231** rows from the public `deps_dev_v1.Snapshots` time table. Oldest: **2022-05-08T02:05:29.029028Z**; 87 snapshots fall in 2022–2023, none in 2020–2021. No dependency edges acquired. | Audited exported-snapshot route lacks the required 2020 start. Original package ages cannot backdate resolved graphs. Alternative original-declaration reconstruction and dated Twilio/Datadog ownership were not certified; no new business/return manifest adopted. |
| NHTSA, second | Retrieved official dataset inventory and complaint/communication layouts, plus one publisher-linked complaint API schema example. That example is outside the Ford/GM frame: **0 in-scope complaint records**, 0 communication records and no corpus download. | Historical versions/public bounds not certified on these routes. No complaint feature or return test. |

The [NHTSA complaint layout](https://static.nhtsa.gov/odi/ffdd/cmpl/CMPL.txt) explicitly documents 2021 changes to historical manufacturer/component values and blank/numeric representations. It distinguishes date added to file from date received. The current 2020–2024 complaint archive is listed as updated in October 2026; receipt-year packaging is not a 2020 public vintage. The [communication layout](https://static.nhtsa.gov/odi/ffdd/tsbs/TSBS.txt) also documents schema changes and multiplicity across products/components. These current sources are useful, but do not reconstruct all earlier versions needed by the proposed historical comparison. No blanket claim about every possible NHTSA archive is made.

Each backup stopped within its two-hour maximum. No fourth candidate or open-ended recovery campaign was launched.

## Setup, actual usage and cost

The owner permitted billing to remain linked and requested autonomous setup. Local Application Default Credentials work. Only the **Cloud Billing and Resource Manager administrative APIs** were enabled to inspect linkage and project inventories; their APIs are [free to use](https://cloud.google.com/billing/v1/pricing). Billing linkage, the owner's Gemini cap and other services were not changed. No Vertex/Gemini workload, compute instance, paid dataset, persistent output table or storage bucket was created.

All three currently linked projects returned complete zero-job October inventories before query execution. Post-run inventories show exactly these six jobs and zero jobs in the other two projects. Seven dry runs were recorded; one oversized combined sample was not executed and was split into below-cap queries before dispatch. Every executed job was below 25 GiB; jobs ran serially, with fixed IDs and no blind resubmission.

| Executed source query | Actual billed query usage, GiB |
| --- | ---: |
| 2020_block_neutral_v001 | 6.555 |
| 2023_apr_may_neutral_v001 | 15.053 |
| 2023_jun_jul_neutral_v001 | 14.831 |
| dec2019_payload_layout_v002 | 20.333 |
| dec2019_sample_v001 | 1.661 |
| dec2019_summary_provenance_v001 | 2.110 |
| **Total** | **60.543** |

Actual billed query usage is **65,007,517,696 bytes**; this is a usage quantity, not a monetary bill. **Expected query charge: £0 under the monthly free tier**, based on the complete current linked-project inventories and these bounded jobs. An invoice/account debit was not independently observed. Unrelated past project relinking/deletion and future account use are not certified by this check. No paid spending was authorized. The Gemini API cap was not treated as BigQuery cost protection, and no free-trial credit balance was used as a substitute for free-tier accounting.

The archive accounts for **42 ordinary HTTP starts** (39 HTTP 200, one 301, one 403, one DNS failure) and **68 Google API starts**: 22 account/table metadata, one snapshot-timestamp read, seven dry runs, six administrative setup/poll calls, six query submissions, twenty query-status reads and six result reads. Total archived response bodies: **4,190,727 bytes**, well below the 2 GiB export/storage ceiling. Query scans are not downloaded bytes. Browser, OAuth/CLI internal requests and local software downloads are separate; their underlying wire counts are unknown. Market requests and economic analyses: **0**.

Two initial API-enable requests used an invalid body, returned 400 and were retained; corrected requests succeeded. Earlier service-disabled reads remain historical. Automatic retries were zero. Ordinary-source starts were paced, but **one WPT source start and a BigQuery status poll were 0.684322 seconds apart**: the global cross-client one-second condition was not fully met. This operational deviation is disclosed; no full pacing-compliance claim is made. All source/account dispatch is now closed by persisted stop markers.

## Scientific state and reproduction

There is **no measured economic result**: 0 certified fixed-cohort origins, 0 adoption features, 0 acquired KPI targets, 0 business forecasts and 0 return analyses. This source result neither establishes nor rejects predictive value. The selected companies, signal, business targets and horizon were unchanged.

Public receipt review needs no credentials, network or raw data:

```sh
python -m json.tool docs/strategy/web_adoption_day1_receipt.json
python -m src.presentation.exp001 --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.research audit EXP004
python -m src.research.exp004_execution_gap_report --check
```

The first command inspects the tracked receipt; it does not replay scientific acquisition. Private source audit requires original ignored HTTP/BigQuery responses and reservations under `data/raw/web_adoption_day1_v001/`. Exact source/query hashes and counts are public; raw pages, package/API bodies, account identifiers and credentials are not redistributed. Temporary local acquisition helpers are not a new public platform. Re-executing the published SQL would be new acquisition and requires a new bounded instruction after this stop.

**Validation: 485 local tests and 257 public tests passed, 0 skipped.** The [validation and preservation receipt](web_adoption_day1_validation.json) also records 109 response-body hash checks and 665 byte-identical prior tracked files; only four living guidance/presentation files changed. EXP004 remains paused with every gap and no-fill boundary unchanged. EXP001–EXP007 history, canonical processed results, frozen methods and dependency pins are preserved. No new experiment, Nexus/Aurora, optimizer, paper/live or automatic next phase occurred. **Stopped after the primary source gate and its two authorized backups.** Delivery commit/push and hosted CI are reported separately.
