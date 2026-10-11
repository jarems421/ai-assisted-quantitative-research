# Phase 2: immutable SEC filing and PIT pilot

**Source fidelity: PARTIAL. Trading eligibility: BLOCKED. Execution compatibility: BLOCKED.**

As of 2026-10-12. The three fixed filings were acquired, archived and parsed offline. Original XBRL fact elements, namespaces, contexts/entities/periods, units and exact values reconcile to the pinned parser. Full primary-document text is extracted with source provenance. Source fidelity remains PARTIAL because acceptance timezone conversion, item-level text segmentation and broader financial-semantic certification are not established. Exact public availability and historical tradable class bindings remain unresolved; no eligibility modeling policy was approved.

## Fixed sources and reconciliation

| Accession | Original documents | Original bytes | XBRL facts | Offline parse | Exact cross-store audit | Trading-eligible facts |
|---|---:|---:|---:|---|---|---:|
| 0000320193-19-000119 | 5 | 18,386,071 | 1,312 | PASS_OFFLINE | PASS | 0 |
| 0000320193-20-000096 | 5 | 17,412,204 | 1,388 | PASS_OFFLINE | PASS | 0 |
| 0001326801-20-000013 | 5 | 17,925,840 | 1,061 | PASS_OFFLINE | PASS | 0 |

Each source set contains the SEC index, header, complete submission, primary annual HTML and extracted XBRL instance. All 15 HTTP attempts returned 200. Requests used one worker, at most two starts/second, a locally configured identified User-Agent, identity encoding, no proxy and exact document allowlists. No other filing was fetched. All response bodies and private receipts remain ignored. [Canonical public summary](phase2_summary.json) lists each original SHA-256 and byte length.

SQLite and Parquet store six per-snapshot tables as exact key/canonical-JSON payload records; nested financial contexts remain intact. DuckDB and PyArrow independently read Parquet and compare complete keys and values against SQLite and canonical records. Original-element/parser reconciliation is separate from those storage checks. Empty security bindings are deliberate; an actual fail-closed as-of view is archived and reconciled.

## Source-grounded examples

| Accession | Concept | Exact reported value | Unit reference | Context |
|---|---|---:|---|---|
| 0000320193-19-000119 | RevenueFromContractWithCustomerExcludingAssessedTax | 260174000000 | usd | FD2019Q4YTD |
| 0000320193-20-000096 | RevenueFromContractWithCustomerExcludingAssessedTax | 274515000000 | usd | i223bd574caab4f739f73936be6065c72_D20190929-20200926 |
| 0001326801-20-000013 | Assets | 133376000000 | usd | FI2019Q4 |

These are filing observations, not forecasts or performance. Dimensions can identify a product/class subset; the example is not automatically consolidated revenue. Units, namespace, original element locator and source hash are retained in the normalized records; the public summary links each example to its instance hash and locator. Missing/nil values remain unavailable; an actual zero remains a source zero. Conflicting duplicates remain ambiguous. Comparative prior-year facts belong to the later accession and never replace earlier snapshots.

## Four clocks and identity

| Accession | SEC acceptance representation | UTC acceptance | First public availability | Historical reconstruction |
|---|---|---|---|---|
| 0000320193-19-000119 | `20191030181236` | UNRESOLVED | UNKNOWN | Present-day archived bytes |
| 0000320193-20-000096 | `20201029180625` | UNRESOLVED | UNKNOWN | Present-day archived bytes |
| 0001326801-20-000013 | `20200129211214` | UNRESOLVED | UNKNOWN | Present-day archived bytes |

The original header timestamp is preserved verbatim. No EST/daylight-saving conversion was silently inferred. Actual retrieval and ingestion UTC times are separately retained in the public summary and private receipts. Those times do not imply historical public availability. Submitting CIK remains explicitly unknown rather than inferred from an accession prefix. Issuer CIK is verified against SGML but is not a unique security ID; all real security bindings remain unresolved.

The 2020-12-31 as-of audit admits zero facts to a trading decision: public availability, approved eligibility policy and class identity are missing. Synthetic verified-policy fixtures test the gating machinery; they approve no real policy. Replay pins exact sources, parser bytes/configuration and provenance. A newer parser receives a new directory keyed by its code hash; earlier derived snapshots, timestamps and prototypes are preserved. Later amendments/metadata cannot modify an earlier pinned snapshot. Historical reconstructed evidence is not genuinely forward unseen.

## Reproduction and checks

```sh
python -m src.research.sec_pilot plan
python -m src.research.sec_pilot replay
python -m src.research.sec_pilot audit
python -m src.research.sec_pilot report --check
python -m unittest discover -s tests -v
```

Replay/audit require ignored original bodies and receipts; they do not call SEC or Nexus. The public report can be regenerated from the two small summaries alone with `python -m src.research.sec_pilot report`. Acquisition is a separate remote command requiring `acquire --execute`; it is not routine reproduction. Completed accessions are verified cache hits. A persisted acquisition stop prohibits automatic resubmission.

**Validation:** 191 tests passed; 0 skipped. The pinned parser fixtures execute in the isolated interpreter, not as skipped standard-environment tests. EXP004 semantic audit, six presentation artifacts, Phase 1 support hashes, pilot offline replay, report consistency, isolated dependency consistency and cross-version Parquet reading passed. [Validation receipt](phase2_validation.json) records the checks.

Environment: CPython 3.13; research PyArrow 20.0.0 / DuckDB 1.3.2; isolated EdgarTools 5.62.0 / PyArrow 23.0.1. Research dependency pins and all 111 snapshotted historical files are unchanged. No credentials, personal contact identity, private receipts or original filings are committed. Existing unrelated local files were left untouched.

## Disposition and next action

The pipeline is implemented and the bounded acquisition/replay completed; the scientific verdict is PARTIAL source fidelity, BLOCKED trading eligibility and BLOCKED Nexus execution compatibility. Three annual filings do not establish full-market, amendment, delisting or insider coverage. Dimensions/units/periods are preserved, not converted into an earnings-surprise feature. Item segmentation, acceptance timezone evidence and class identity need further scoped certification.

Before Phase 3, review the archived source examples and decide how independently evidenced availability and historical class bindings can be supplied. Only then specify an economic filing-derived forecast and its matched control/search budget. Do not start broader acquisition, EXP005, performance evaluation or an optimizer from this outcome.

EXP004 remains operationally paused. Zero Nexus operations, performance queries, backtests, optimization, credit purchases, held-out reads, paper/live operations or EXP005 actions occurred.

Git checkpoints pushed to `main`: `610e5c7` — bounded acquisition/archive; `e3cdc28` — offline parser/PIT/reconciliation; `5c57f79` — versioned parser snapshots/full primary text. The final report/documentation commit is reported in the delivery message; the repository history supplies its SHA without embedding a self-referential commit hash in generated content.
