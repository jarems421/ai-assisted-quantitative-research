# Phase 4A-R: source-first researchability map

**SOURCE_FIRST_DIRECTION_READY; SEC is the preferred surface for a subsequent bounded design review.** As of 2026-10-13. This is planning-level source-route plausibility, not a complete historical population, observed public-timing, identity, execution or inference certificate. Three fixed surfaces were reviewed after exact access probes; no fourth family pilot or hypothesis was selected. NEXT_EXPERIMENT NONE_SELECTED; PERFORMANCE_AUTHORIZED FALSE.

## Actual access and samples

| Surface / probe | Exact tested URL | HTTP | Bytes |
| --- | --- | ---: | ---: |
| SEC/SEC_ACCESS | https://www.sec.gov/Archives/edgar/data/320193/000032019319000119/0000320193-19-000119-index.htm | 200 | 13533 |
| SEC/SEC_DOC | https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data | 200 | 80349 |
| FR/FR_ACCESS | https://www.federalregister.gov/api/v1/documents.json?per_page=2&order=oldest&conditions%5Bpublication_date%5D%5Bis%5D=2019-01-02 | 200 | 4046 |
| FR/FR_DOC | https://www.federalregister.gov/developers/documentation/api/v1 | 302 | 0 |
| CT/CT_ACCESS | https://clinicaltrials.gov/api/v2/studies?pageSize=2&sort=LastUpdatePostDate%3Aasc&format=json&countTotal=true | 200 | 8241 |
| CT/CT_DOC | https://clinicaltrials.gov/data-api/api | 200 | 94247 |

Six starts, zero retries, of the36-start maximum; no search/discovery request, source purchase or account upgrade. Existing15 original Phase2 documents were hash/length verified without network and its archive/parser evidence reused. The current SEC fixture index matches its previous original bytes. All three primary routes returned usable200 responses. Federal Register documentation302 was archived without following; its source stop remains. ClinicalTrials documentation200 is a JavaScript shell, not substantive parsed API/history guidance. No blocked family route was retried. Git/CI metadata are separate delivery operations; account-wide debit remains unknown.

Federal Register's fixed2019-01-02 first page returned2 notices; the source advertises12 documents for that day. Ten unsampled records are not absent. Both sampled rows carry document number, publication date, agency IDs and official PDF links; those PDFs were not fetched and legal-original/correction lineage is not certified. ClinicalTrials' neutral first page returned2 studies and source count606601. Both happened to be COMPLETED; outcome was not a query filter. This current count is not a count of eligible corporate events or independent observations. Their first-post fields date to2000, last-update fields to2005, and the posting structs say ESTIMATED. They do not establish historical first-public time, prior content or complete historical registry coverage.

## Researchability matrix

| Dimension | SEC | FR | CT |
| --- | --- | --- | --- |
| SOURCE ACCESS | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE |
| DENOMINATOR | PARTIAL | PARTIAL | PARTIAL |
| HISTORICAL DEPTH | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE | PARTIAL |
| POINT IN TIME | PARTIAL | UNKNOWN | BLOCKED |
| TIMING | PARTIAL | PARTIAL | PARTIAL |
| REVISION LINEAGE | PARTIAL | UNKNOWN | BLOCKED |
| ENTITY IDENTIFIERS | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE |
| RELATIONSHIPS | PARTIAL | UNKNOWN | PARTIAL |
| RECORD FREQUENCY | PARTIAL | PARTIAL | PARTIAL |
| DEPENDENCE GEOMETRY | PARTIAL | PARTIAL | PARTIAL |
| TERMINAL LIFECYCLE BURDEN | PARTIAL | UNKNOWN | UNKNOWN |
| ACCESS COST | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE |
| REPRODUCIBILITY | PROVEN_FROM_EXISTING_EVIDENCE | PASS_BOUNDED_PROBE | PASS_BOUNDED_PROBE |
| GRAPH REUSE | PARTIAL | PARTIAL | PARTIAL |

Status meanings and hard gates: [SourceResearchabilityContract](phase4a_researchability_contract.md). [Canonical map](phase4a_researchability_map.json) gives every status a reason and source-hash/document provenance; [registry](phase4a_source_registry.json) records exact samples, request clocks and original-body hashes. No score totals or imagined alpha probabilities were used.

**SEC passes the planning-level hard-gate plausibility screen**: current access, documented form/CIK/date/path public-filing indexes, original accession/header archive/replay, historical index coverage, and plausible repeated observations. Denominator, PIT and record variation remain PARTIAL with explicitly recorded plausibility reasons. No source passes executable trading-certification gates. The preferred population is filings defined by type/date, not all historically tradable US stocks or all filings a company should have made. A complete obligation-based missing-filing panel cannot be manufactured from filed records.

Federal Register remains a conditional frontier, not a preferred surface: historical publication-date access works, but original-publication/PIT/correction evidence and company linkage are unresolved. ClinicalTrials is not ready for historical discovery through this probed route: current-version date/status/sponsor fields cannot reconstruct prior versions. Another official historical route was not tested and is not declared impossible. The small candidate set was not expanded to force success; only one of three surfaces currently meets evidenced planning plausibility.

## SEC-native surface limits

The official SEC guide documents public filing indexes from1994Q3, including company name, form type, CIK, date filed and source filename. It also documents post-acceptance corrections/deletions, nightly index changes and rebuilt quarterly/full indexes. Daily/feed/oldload indexes can retain references after later removals; that creates a plausible missingness-preserving census route, not recovery of unavailable original bytes. A current quarterly index is not an untouched historical vintage. Preserve daily enumeration, original accession versions, amendments, PAC/deletion relationships and unresolved missing documents in a versioned source denominator receipt before selecting a feature.

Acceptance, dissemination, filing date, public website accessibility and present-day download remain separate. Existing winter timestamp evidence and October uncertainty remain unchanged. No v002/v003 activation or extension to other forms occurs. New form/window/channel timing needs explicit review; possible conservative bounds are not observed public times. CIK identifies a filer, not a security/class; accession prefix can be an agent. Today's ticker/entity associations do not certify historical listed membership. Deleted/ended issuers cannot disappear from the denominator.

8-K, periodic, ownership and transaction form classes are conceptually enumerable from this filing universe, subject to source-contract review. No insider/institutional experiment is reopened: EXP002/EXP003 historical membership, identity, omission-to-zero and complete event-version failures remain. The review retrieves no Form4/13D/13G event corpus and supplies no absence certificate. Phase3 accounting/EPS/triple and terminal/execution/inference failures are likewise preserved, not solved by SEC access.

## Mechanisms and architecture decision

Only after the completed map, three SEC-native [mechanism directions](phase4a_mechanism_directions.md) are offered as PREDICTIVE ideas. No mechanism is chosen, scored on returns or registered. Federal Register/ClinicalTrials receive no new mechanism proposals while hard gates remain unresolved. Predictive work still needs PIT population, honest identity, matched benchmark, dependence-aware inference, costs, trial control and survivor-safe execution; causal identification is an additional requirement only for causal claims.

**KEEP_PHASE4B_LATER.** Actual blockers remain upstream source versions/denominators/public timing. SEC already supplies useful filer IDs; Federal Register lacks issuer IDs and ClinicalTrials sponsor relationships would require later dated bridges, but those limited probes do not establish entity resolution as the dominant recurring bottleneck. Standardize accession-filer-version, agency-document, study-sponsor/collaborator and eventual class spans only when a chosen source contract needs them. No graph, entity-spine campaign or causal lab is built.

The justified minimal gap is a **versioned filing-denominator receipt**, reusing archives/Store rather than another warehouse: declare date/form population; reconcile neutral daily-index entries to original accession bytes and missing/PAC/amendment states; keep as-of availability and class identity separate. This is a recommended bounded prototype, not an authorized implementation or full census. [Architecture decision](phase4a_architecture_decision.md) records the owner-approved change in sequencing and the remaining decision.

## Verification and stop

Validation: 315 local tests, 89 public tests, zero skipped. [Receipt](phase4a_source_first_validation.json). Public regeneration: `python -m src.research.source_first_report --check`. Private original-body/ledger audit: `python -m src.research.source_first_report --audit --check`; neither command acquires sources. `python -m src.research.source_first acquire --execute` is a separate bounded mutation and not reproduction; cached acquisition prevents blind resubmission. Old SEC offline replay/audit and historical pilot reports remain independently checked.

The mechanism-first family screen remains COMPLETE_THREE_FAMILIES_EXHAUSTED. Historical procurement/FDA/merger reports, raw errors/stops, all prior phase evidence, experiment artifacts, EXP004 pause, EXP005 abandonment/absence and inactive policy approvals are unchanged. No price/return/performance, strategy, new experiment, optimization, held-out opening, Orbis/Nexus/Aurora, Phase4B/4C, graph, causal lab or paper/live action occurred.

**Stop for owner review.** The exact proposed next decision is whether to commission one bounded SEC filing-denominator/PAC/availability contract prototype and then choose one of these predictive directions for a separate design review. The owner must specify the form/date/sample ceiling before any new source work. No future experiment or timing policy is approved by SOURCE_FIRST_DIRECTION_READY.
