# Phase 2: SEC source-certification implementation plan

**Planning only — 2026-10-12.** This review prepares a bounded implementation milestone. The supplied document begins “Planning only” and contains a proposed implementation prompt; that embedded prompt is not executed in this turn. No pilot code, SEC acquisition, experiment or modeling policy is introduced. The [existing SEC pilot specification](sec_pilot.md) remains authoritative for acceptance, with the implementation decisions below proposed for its next authorized milestone.

The target is faithful reconstruction of three filings, with explicit limits on trading eligibility and execution compatibility. Source fidelity can pass while both of those downstream gates remain unresolved. No economic or performance evidence follows from successful parsing.

## Fixed contract and current readiness

| Item | Fixed boundary / observed status |
|---|---|
| Real sources | Apple `0000320193-19-000119`, Apple `0000320193-20-000096`, Facebook `0001326801-20-000013`; [existing fixture manifest](sec_pilot_fixtures.json) unchanged |
| Acquisition | Not implemented or executed; no current-company facts, submissions enumeration, additional accessions or external taxonomy retrieval |
| Environment | Existing isolated EdgarTools 5.62.0 / PyArrow 23.0.1; `pip check` passes; research PyArrow remains 20.0.0 |
| Research OS | Reuse JSON receipts and SQLite conventions; do not register a pilot as an experiment, reuse its state database or modify legacy PIT cutoffs |
| EXP004 | Operational pause retained; semantic audit passes at unchanged `HYPOTHESIS_FROZEN`; no Nexus operations |
| Availability / security binding | No new evidence or approved eligibility policy; UNKNOWN cannot enter a trading decision |

## Installed parser findings

Inspected the installed pinned source directly, rather than assuming examples match the release. These are code observations, not executed offline parsing tests.

| Pinned API | Proposed use | Boundary to prove |
|---|---|---|
| `edgar.sgml.sgml_common.FilingSGML.from_text(full_text_submission)` | Parse explicitly decoded archived submission text; preserve original bytes and decoding lineage separately | Synthetic header/document fixture must parse without network; do not use URL-capable `from_source` or network-backed `from_filing` |
| `edgar.xbrl.xbrl.XBRL.from_files(instance_file, schema_file, presentation_file, calculation_file, definition_file, label_file)` | Pass only declared local files; optional linkbases only when needed and archived | Offline behavior, context/fact fidelity and dependency closure require tests; no external schema fetch or current-filing fallback |
| `XBRL.parser.parse_instance_content(content)` | Potential explicit-decoding alternative to the file reader | Installed file reader uses `Path.read_text()` without an encoding argument; encoding policy must be deterministic across platforms |
| Installed instance XML parser | Parse raw fact/context/unit data instead of standardized financial statement views | Uses `recover=True`; add strict well-formedness validation with external entities/DTD access disabled before certifying output. A recovered malformed document cannot silently pass |

Use filing-specific raw facts; avoid statement stitching, latest-company lookups and automatic aggregation. Verify duplicate/conflicting facts, exact values, units and source locators against original elements, even if library convenience views select a single entity/value. Source locators must refer to the archived original or an explicitly linked derived document, not an unexplained normalized-text position.

Prefer explicit local files over directory discovery. A complete submission may contain useful embedded documents, but do not assume it contains every required XBRL instance/linkbase. Determining the closed document set is part of the acquisition plan. If the library cannot replay required archived inputs offline, stop the affected route and report the limitation; do not change the pinned version or silently build a replacement parser.

## Five verified checkpoints

Use a small separate `src/research/sec_pilot/` package. Begin with cohesive archive/acquisition, parsing, provenance/as-of and reconciliation/CLI components; split files only when the implementation warrants it. No new warehouse or orchestration framework is needed.

| Checkpoint | Concrete work | Completion evidence / stop condition |
|---|---|---|
| A — Fixture and transport boundary | Offline `plan`; exact three accession roots; index/header/full-submission seed URLs; explicit required-document list; single-worker identified transport with rate/retry ceilings | Fake transport rejects unapproved accession, host, path, query, traversal, redirect and current-company endpoints. Validate parser feasibility locally before spending acquisition requests. Missing configured identity stops real acquisition |
| B — Immutable archive | Byte-preserving create-only content store; bounded streaming; complete-download finalization; immutable attempt receipts; cached/network distinction | Interrupted, short, oversized, failed and concurrent writes tested. Hash/length and source identity verified before a successful manifest entry. Identical content is reused; changed content creates a new version |
| C — Offline parser | Pinned SGML/XBRL APIs; strict validation; archival locators and exact values; local-only dependencies | Repeated runs produce identical canonical payloads and table keys. Network-blocked SGML/XML/HTML fixtures run in the isolated interpreter. Unsupported paths stop; no fallback fetch |
| D — PIT reconstruction | Four clocks plus separately nullable eligibility policy; source-snapshot identity; version and historical class contracts | Future amendments, later metadata and renamed/reused/multiple-class fixtures cannot mutate an earlier pinned replay. Unknown eligibility, missing bindings and conflicting facts are explicitly unavailable |
| E — Reconciliation and report | Exact-key/hash SQLite ↔ Parquet ↔ DuckDB comparisons; offline replay; full regression; source-only outcome report | Count-preserving substitutions, context/value changes, missing sources and version mismatches fail. Report each gate as PASS/PARTIAL/BLOCKED with actual evidence, never performance metrics |

Each completed checkpoint receives a reviewed commit and push under [AGENTS.md](../../AGENTS.md). The future implementation authorization should permit the three-source acquisition after A passes; a checkpoint does not by itself demand renewed approval within that already authorized scope. This planning turn does not authorize it. Persistent SEC restrictions, inability to enforce the allowlist, unavailable identity or a required scope expansion stops acquisition.

## Acquisition decisions to make concrete

Use a dedicated HTTP boundary rather than EdgarTools network acquisition. Enforce one worker and at most two requests/second across every attempt and redirect; bounded retries for transient failures, explicit terminal treatment of persistent 403/429, maximum redirects, response bytes and total attempts. Identity comes from local configuration, never from committed contact details or an invented name/email.

Do not equate an accession-directory allowlist with a document allowlist. Start from the exact index/header/submission URLs. An index or submission may propose primary/XBRL filenames; validate each as a plain in-accession document name and approve only the documents required by the extraction contract. Freeze that exact acquisition plan/hash before fetching those additional files. Redirects must remain inside the exact allowed document set; aliases need an explicit declared equivalent, not a wildcard. No external imports are automatically approved.

Capture each response body before parsing, including error bodies, with safe HTTP metadata. Request headers containing identity or credentials are omitted/redacted in public metadata. Preserve the raw transfer representation available to the chosen client and document decompression/decoding explicitly; do not call decoded text “original HTTP bytes.” Local interrupted partials remain private attempt evidence and cannot masquerade as finalized sources. Record exceptions without leaking request identity through error strings.

Finalize a complete temporary body inside the archive filesystem using an exclusive destination operation that cannot overwrite another writer; avoid an unconditional replace on the immutable content path. Flush, verify hash/length and handle races by checking existing bytes. Record attempt receipts separately from content so identical content acquired at different times retains separate retrieval histories. Reuse `RawStore` for those canonical JSON receipts, not the source body.

## As-of and identity decisions

An immutable replay key should include `(source_snapshot_sha256, decision_utc, parser/config hashes, eligibility_policy_sha256)`. A source snapshot names exact byte versions and immutable provenance records. Later evidence creates a new snapshot; it never edits the old snapshot's availability or identity declarations. This makes future-prefix invariance testable without pretending today's historical acquisition happened in the past.

Store SEC acceptance, evidenced first-public availability, historical reconstruction status, retrieval time and parsing/ingestion time separately. Acceptance timezone evidence must come from the archived header/index. A future modeling bound has separate policy/evidence fields and cannot populate an observed publication timestamp. Phase 2 does not approve that policy. Real-source trading views may consequently contain **zero eligible facts**, while issuer-level source storage remains useful and successful.

Keep each fact tied to its accession, original namespace/local concept, context, unit, exact value, source element and period semantics. Later comparative/restated figures are observations of the later filing. Do not retroactively replace an earlier filing or infer amendment relationships from equal periods alone. Preserve missing/nil/zero distinctions. Reject unsupported fiscal/YTD derivations unless every component and its temporal/identity evidence is present in the pinned decision snapshot; quarterly feature engineering is outside this pilot.

CIK denotes an issuer, not a tradable security. Retain historical names/class descriptions from the filing as issuer evidence; do not fabricate stable security IDs or class bindings. Dated mappings need independently documented lineage and unique valid spans. Generic exact-population reconciliation applies only when exhaustive stable-ID/ticker bindings and completeness evidence actually exist; do not manufacture those inputs from issuer rows.

## Verification and deliverables for implementation

Credential-free tests use synthetic EXP999 material in temporary directories and fake HTTP transports. The standard research interpreter tests archive/transport/as-of contracts; pinned-parser integration tests run explicitly in the isolated interpreter. A skipped parser test is not a pass. Compare original-element facts, normalized canonical rows and independent SQL storage queries; comparing three copies of the same bad export is insufficient reconciliation.

Test renamed/reused/ended identities, multiple classes, overlapping/missing spans, conflicting/duplicate XBRL contexts, instant/duration/fiscal differences, actual zero/nil/missing, malformed XML, late amendments, DST/after-hours timestamps, future source metadata, interrupted/racing writes, redirect escapes and count-preserving substitutions. Record the exact key/value mismatch, not just a boolean failure.

The separate proposed CLI has `plan`, explicit `acquire --execute`, `parse`, `replay`, `audit` and `report`. Only acquisition can reach SEC, with the planned allowlist and explicit execution flag. Parsing/replay/report must run without network or Nexus credentials. These names are proposed interfaces, not commands that currently exist.

The implementation delivers a generated compact `phase2_report.md` backed by canonical pilot summaries: accession/document acquisition outcomes, original hashes, parser/reconciliation results, source-located fact examples, clock evidence, unresolved identities, replay commands, actual tests/skips, environment versions and Git checkpoints. Keep original source files, private attempt receipts and contact identity ignored. Preserve the existing experiment records and public fixture manifest.

Report separate verdicts for **source fidelity**, **trading eligibility** and **execution compatibility**. A successful three-filing archive cannot establish precise public availability, full-market/insider coverage, historical security binding, alpha or Nexus compatibility. Phase 3 recommendation should address remaining data/availability/identity prerequisites for a separately specified economic forecast; no automatic expansion, freeze, backfill or study.

## Checks executed in this planning review

| Check | Actual result |
|---|---|
| Research baseline | `python -m unittest discover -s tests -v`: **176 passed** |
| EXP004 local semantic audit | PASS; unchanged `HYPOTHESIS_FROZEN`, specification `32b216dd7d510399421d9ea89e61aff30c6b59aa8a4e0b31f5786615c1e6b3b9` |
| Phase 1 support verification | PASS against existing private receipts; offline, zero Nexus calls |
| Presentation verification | PASS, six deterministic artifacts |
| Isolated dependency consistency | `pip check`: no broken requirements |
| New parser/acquisition/replay tests | NOT RUN; implementation does not exist |
| Real filing acquisition | NOT RUN |

The tests include the existing EXP001 deterministic local integration suite, using already-opened private records; no new held-out observations or performance queries were requested. Existing experiment/report/processed/metric bytes were checked for changes. The next executable milestone remains separate from this planning review.
