# Minimal SEC filing pilot specification

Implementation status (2026-10-12): see the [Phase 2 outcome report](phase2_report.md) and [canonical summary](phase2_summary.json). The original pre-implementation acceptance specification below remains the historical scope contract; its original “not acquired” statements describe the preparation checkpoint.

**Specification only, 2026-10-11.** Implement next only with owner authorization. This pilot tests provenance and as-of reconstruction, not forecasts, insider feed completeness or strategy performance. No full backfill, EXP005 creation/freeze, Nexus publication or backtest is included.

## Fixed scope and environment

Use exactly three pre-2021 annual filings listed in [fixtures.json](sec_pilot_fixtures.json): Apple 2019 and 2020, and Facebook 2019 (accepted January 2020). Selected deterministically for two consecutive annual versions, inline XBRL/text parsing, after-hours timing and a historically named issuer; no returns, prices or strategy rankings informed selection. SEC index metadata was checked in Phase 1; source bytes and source SHA-256 are **not yet acquired**. This is a named fixture plan, not a claim of a completed dataset. The set does not establish delisting or amendment coverage; synthetic cases test those policies.

The owner's follow-up authorized required dependency downloads. `edgartools==5.62.0` and `pyarrow==23.0.1` are installed in ignored `.research/sec-pilot-venv`, with no AI/cloud extras. [Version metadata](https://pypi.org/pypi/edgartools/5.62.0/json) requires `pyarrow>=23.0.1`; the research pin remains 20.0.0. All 44 resolved packages have pinned wheel hashes in [the pilot lock](sec_pilot_requirements.lock), with [licence declarations and notice-file hashes](sec_pilot_dependency_inventory.json). `pip check`, external-network-blocked EdgarTools import and synthetic Parquet interoperability pass. Before filing acquisition, still verify offline parser APIs and acquisition throttling in the pinned release; dependency preparation is not pilot implementation.

Reproduce the isolated environment on CPython 3.13 / Windows x86-64:

```powershell
python -m venv .research/sec-pilot-venv
& .research/sec-pilot-venv/Scripts/python.exe -m pip install --require-hashes -r docs/acceleration/sec_pilot_requirements.lock
& .research/sec-pilot-venv/Scripts/python.exe -m pip check
```

Wheel hashes in this lock are platform-specific; another platform needs its own separately reviewed resolution. Use installed research DuckDB/SQLite for downstream checks, exchanging schema-defined Parquet. No SEC source bytes were acquired during preparation. Keep the dependency notices intact; the inventory includes GPLv2-or-later Unidecode and MPL components, so do not treat the environment as wholly MIT or relicense dependencies under repository terms.

Use the publisher's [accession lookup](https://github.com/dgunning/edgartools/wiki/FindingThings) rather than `Company(ticker).latest()` or current company facts. Confirm the returned issuer CIK, accession, form and document identity against the fixed manifest. CIK in the accession prefix can identify a submitting agent; it is not automatically the issuer. No current ticker lookup establishes historical class membership.

SEC requires identified automated requests and imposes fair-access limits. Configure the owner's identity locally (never commit personal contact details), one worker at a conservative 2 requests/second, bounded retry/backoff, no proxy evasion. Library cache hits must be distinguishable from network receipts; stop on persistent 403/429 rather than broaden retrieval. [SEC developer guidance](https://www.sec.gov/about/developer-resources) and [EdgarTools identity configuration](https://github.com/dgunning/edgartools/blob/main/docs/installation.md) are the authoritative starting points. Verify exact HTTP behavior in the pinned release; a library configuration declaration is not evidence that throttling works.

## Acquisition and source manifest

Acquisition allowlist: each fixed accession's index/header, complete submission text, primary annual document and referenced XBRL documents needed for the chosen extraction. No current submissions/company-facts enumeration, hidden latest-filing fetch or 2021+ corpus access. Enforce URL/CIK/accession allowlist at transport, including redirects. Use identity only in request headers, not public manifests.

Capture every HTTP response immediately as original bytes under ignored `data/raw/sec_pilot/<accession>/<sha256>/`; do not reserialize the raw submission, HTML or XML. Preserve content encoding/decoding lineage, request URL, final URL, status, content type, retrieval UTC, byte length, hash, headers needed for provenance, and acquisition error receipts. Redact credentials/contact details in tracked manifests and identify that redaction. Repeated retrieval yielding different bytes creates a new version; existing bytes never change. A cache path or last-modified header is not proof of historical availability.

Reuse `RawStore` for JSON receipts; it canonicalizes JSON and therefore is **not** an original-byte store. Add a small exclusive-create byte helper with path containment, hash verification and immutable conflict checks. Parsing must read the archived bytes offline with transport disabled. If the pinned library cannot parse all required archived material without network calls, record that blocker; do not silently fall back to a latest-company object. Record parser version, extraction configuration/hash, code Git SHA and source hashes with each derivative.

## PIT schema

| Table / key | Required fields and semantics |
|---|---|
| `source_documents` `(accession, document_name, source_sha256)` | issuer CIK, submitting CIK when known, form, SEC URL, archive path/hash/bytes, acceptance raw text and timezone evidence, `accepted_at_utc`, nullable `public_available_at_utc`, `availability_status`, evidence link, `retrieved_at_utc`, acquisition error/status |
| `filing_versions` `(issuer_cik, accession)` | report period, filing date, accepted instant, reconstruction status, original/amendment link (nullable with reason), parser/config/code hashes; no overwriting prior version |
| `facts` `(accession, source_document_sha256, fact_locator)` | concept/namespace, exact value and normalized numeric value, unit, decimals, context/entity/dimensions, period start/end or instant, document byte/element locator, availability evidence/status; duplicate/conflicting contexts retained |
| `text_sections` `(accession, document_sha256, section_locator)` | section label, original locator/span, normalized text hash, transformation version; missing section stays unavailable |
| `security_bindings` `(issuer_cik, security_id, effective_from, effective_to, source_sha256)` | historical ticker, class/subtype, venue if known, mapping evidence and confidence/status; one issuer can have multiple classes; no current ticker substitution |
| `asof_views` `(decision_utc, accession, fact_locator)` | version selection policy/hash, public-availability basis, historical reconstruction flag, contributor hashes, identity status; unresolved fields remain nullable/unavailable |

Reuse Parquet/PyArrow for derivatives, DuckDB for reconciliation queries and standard-library SQLite for manifest keys/retrieval status. Do not put large filing bytes in SQLite or introduce another warehouse/service. Public metadata and synthetic fixture tests live under a pilot namespace, not an immutable historical experiment directory.

## Four distinct clocks

- **Acceptance:** SEC system acceptance instant; preserve original timestamp representation and validate its timezone using archived header/index evidence. Do not silently trust a trailing `Z` or assume EST versus daylight saving without evidence.
- **Public availability:** first accessibility to the relevant public information channel. SEC says filings commonly appear shortly after acceptance and provides no first-public timestamp; acceptance alone is insufficient to certify exact public availability. [SEC timing FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)
- **Historical reconstruction:** bytes acquired today reconstruct a past accession, not a contemporaneous ingestion record. Label `historically_reconstructed`; source-version drift remains possible even with frozen current bytes.
- **Local ingestion:** actual download/parse receipt time in UTC in the present, never backdated to acceptance or filing date.

Default exact-availability state is UNKNOWN unless evidenced. A conservative next-session or filing-date-EOD assumption, if later predeclared and approved, belongs in a separately labelled modeling-policy field; it does not populate `public_available_at_utc` as an observed fact. This source-only pilot may pass storage/parser tests while its trading-availability gate remains unresolved. No feature is eligible for a trading decision unless its approved availability bound is no later than that decision. Historical evidence is workflow-held-out, not genuinely forward unseen.

## Acceptance tests for implementation milestone

| Test | Required outcome |
|---|---|
| Fixed accessions / network bounds | Exactly the three named accessions; fixture transport rejects current-company/latest data, another accession, out-of-cutoff requests and redirect escapes; zero Nexus calls |
| Original-byte integrity | Hash/length verify; rerun is idempotent; altered bytes create a new version or fail, never overwrite; path escape and race tested |
| Offline deterministic parser | Archived synthetic HTML/SGML/XML parse with network disabled; reruns produce identical normalized rows/config hashes; real three-file parse compared to documented fields |
| Clock separation | Download time stays present-day; after-hours/weekend, DST and conflicting timestamp representations tested; unknown first-public time cannot become accepted time implicitly |
| Future-prefix invariance | A synthetic later amendment/restatement cannot change an earlier as-of view; post-cutoff source is rejected; original and amendment retained distinctly |
| Context and missingness | Duration/instant, unit, dimensions and accession-specific contexts preserved; duplicate/conflicting contexts flagged; absent fact/filing never manufactured as zero |
| Historical class identity | Synthetic rename, ticker reuse, class split, delisting and overlapping mappings; CIK-to-multiple-security ambiguity stays unavailable; all bindings have evidence and spans |
| Reconciliation | Source manifest counts/keys/hashes match archived bytes and Parquet; SQLite ↔ DuckDB results agree; count-preserving substitutions and missing historical identities fail shared reconciliation |
| Dependency isolation | Research pins unchanged; isolated lock/wheel/licence inventory saved; generated Parquet read correctly using existing research Arrow/DuckDB |
| Scope and reproducibility | No market returns, alpha selection, freeze, experiment state writes, publication or performance jobs; public synthetic tests need no private/raw data or SEC requests |

Completion report must distinguish storage/parser success from public-availability, historical class and coverage certification. Three annual filings do not certify an insider feed, amendments exhaustiveness, an entire universe or genuinely absent events. Carry limitations forward, then choose one economic mechanism for a separately reviewed EXP005 design. Do not scale acquisition or select signals on pilot success automatically.
