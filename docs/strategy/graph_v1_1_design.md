# Economic Knowledge Graph v1.1: economic connections versus research warnings

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Implemented offline on feature branch `graph-v1.1-discovery-quality`; not merged into `main`; no pilot has run.** Graph v1.1 is a targeted change to the v1 operators. They already recorded *why* two records matched. v1.1 uses those recorded bases to separate three kinds of result, and stops presenting all three as connections:

| Class | Meaning | Rule (categorical, from recorded bases) |
|---|---|---|
| `ECONOMIC_CONNECTION_CANDIDATE` | A possible relationship worth investigating, grounded in specific evidence | At least one grounding basis: `EXACT_DOCUMENT_HASH` (same document bytes), `EXACT_ENTITY_ID` (same identified object; never a name or ticker) or `DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD` (documented relationship covering the observed date) |
| `METHODOLOGICAL_WARNING` | Reusable research memory: an earlier investigation found the same thing hard to measure | Only requirement or tag bases: `AUTHOR_TAG_CANDIDATE`, `REQUIREMENT_MATCH`, curated mappings or a shared mechanical blocker |
| `UNSUPPORTED_MATCH` | Cannot justify even a provisional connection; kept for transparency | Neither, for example `REUSED_CITATION` (evidence copied from the other record) or `SAME_LOCATOR_ONLY` |

Look-alike names, keyword-only overlaps and out-of-period relationships stay in `rejected` and `abstentions`, exactly as in v1.

There is no relevance score and no model judgement. A candidate justifies investigation only. It never shows exposure, causation, materiality or economic benefit, and no class changes a ledger, a disposition, M/H or a source stop.

[Owner instruction](owner_graph_v1_1_2026-10-22.md) · [Quality regression](graph_v1_1_quality.md) · [R4 protocol draft (NOT_RUN)](graph_pilot_r4_protocol_proposed.md) · [Validation](graph_v1_1_validation.json) · [v1 design](graph_v1_design.md) · [Guide](graph_v1_guide.md) · Code: [`connections.py`](../../src/research/graph/connections.py), [`operators.py`](../../src/research/graph/operators.py), [`quality.py`](../../src/research/graph/quality.py)

## Why: the R3 diagnostic

Graph Pilot R3 was closed as INCONCLUSIVE: two pairs, potentially unblinded, AI-assisted adjudication ([results](graph_pilot_r3_results.md)). It is not evidence that Graph v1 is ineffective in general. It did surface one actionable weakness:

- All 10 graph-operator connections were judged trivial.
- Seven came from `same-gap` or `next`. They linked a recall packet to salmon, Chevron, BASF or insurance memory because each lacked capacity, allocation, net-economics or parent-join evidence.
- The other three were `revisit` keyword-only overlaps. v1 had already placed those in `rejected`, but the arm logged them as connections.
- All 10 confirmed connections came from reading originals: product-identifier joins, recall supersessions and an issuer disclosure.

R3 is used only as a diagnostic. The new fixtures reproduce its failure pattern on purpose. Success on them is a regression check, not independent validation.

## Changes by operator

| Operator | v1 | v1.1 |
|---|---|---|
| `revisit` | Earlier claims sorted by strongest basis; a tag-only lead was flagged `candidate_only` but still listed among connections | Every result is classed. A tag-only match is always a warning. A result with a tag *and* a grounding basis keeps both bases and is classed by the stronger one. Candidates always rank above warnings, which rank above unsupported matches. A documented relationship joining the records is now named in the explanation. A copied citation is `REUSED_CITATION`, not a document match |
| `same-gap` | Claims blocked by the same requirement, with a note that this is not an economic relationship | The same claims and leads, each classed `METHODOLOGICAL_WARNING` with the earlier record's lesson (its tagged missing variables and falsification route, or the cited historical finding) |
| `next` | Recurring requirements, ordered categorically | Unchanged ordering; each row is a `METHODOLOGICAL_WARNING` stating that the listed claims are not thereby economically related |
| `shared` | Other campaigns sharing a document hash or identified entity | Classed per campaign. One document is labelled `NOT_INDEPENDENT_CORROBORATION`. A citation reused from the other record becomes `UNSUPPORTED_MATCH` |
| `complements` | Documented, period-compatible context; refuses name-only identity and out-of-period relationships | Same matching; every result is a grounded candidate with an explanation. Refusals are unchanged and counted in the summary |

Every changed operator now returns `operator_version: GRAPH_OPERATORS_V1_1` and a `connection_summary` (candidates, warnings, unsupported, rejected). Result *membership* is unchanged apart from the reused-citation basis. Nothing that v1 found is suppressed; it is classed and ordered. Text output prints the summary line. `explain`, `trace`, `changes`, `gaps`, `failures` and `orphans` are unchanged.

## The grounded explanation

Each `ECONOMIC_CONNECTION_CANDIDATE` carries a `grounding` object with the nine required parts:

1. **`source_record`, `target_record`:** the exact versioned records.
2. **`documented_basis`:** each grounding basis, with what it means.
3. **`joining_objects`:** the identifier, document or relationship involved: identity status, content identity, period, direction, allocation.
4. **`economic_objects`:** each identified object and its role (`DESCRIBES`, `SUBJECT`, `OBJECT`, `EXPOSES`, `CONCERNS`).
5. **`temporal`:** occurrence, period and first-public time for both records, with `UNKNOWN` kept explicit. Also whether the relationship period covers the source date.
6. **`establishes`:** what the basis does show.
7. **`not_established`:** always exposure, transmission, materiality, allocation and quantity definition. Unknown first-public times and archive-path caveats are added when relevant.
8. **`first_unsupported_inference`:** from `rules.first_unsupported_leap` over source → identified objects → relationships → documents → target. Even a fully supported chain ends at `FINANCIAL_TRANSMISSION_UNVERIFIED`.
9. **`worth_investigating_because`:** derived from the target: its unresolved variables, the documented route, or the earlier verdict to read.

`connections.provenance_complete` checks that all parts are present. The quality regression requires all of them (4/4).

## Example: a grounded connection and a research warning

Both come from the synthetic regression fixtures (`python -m src.research.graph quality`).

**Economic connection candidate.** `complements DLC-QSYN-D/OBS-QD-2` matches the new recall record to a registry relationship:

| Part | Value |
|---|---|
| Records | `observation:DLC-QSYN-D/OBS-QD-2@1` → `relationship:DLC-QSYN-R/REL-QR-1@1` |
| Basis | `EXACT_ENTITY_ID` + `DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD` |
| Joins | `entity:SYN_RECALL:R-25` (IDENTIFIED); relationship "Recall R-26 expressly supersedes recall R-25.", 2025-01-01 to OPEN, `DOCUMENTED_RELATIONSHIP` |
| Temporal | Recall occurred 2025-07-02; the period covers it: **YES**. Both first-public times are **UNKNOWN** |
| Not established | Exposure of any listed company, transmission, materiality, allocation, same quantity definition, first-public times |
| First unsupported inference | `FINANCIAL_TRANSMISSION_UNVERIFIED`: every step is supported, but none shows quantity transmission, materiality or exposure |
| Why investigate | It documents a supersession for the object the recall concerns, a possible route to investigate |

**Methodological warning.** `revisit DLC-QSYN-D/OBS-QD-1` (a device recall tagged as possibly measuring capacity) reaches an aquaculture pen-capacity claim:

| Part | Value |
|---|---|
| Records | `observation:DLC-QSYN-D/OBS-QD-1@1` → `claim:DLC-QSYN-H/CAND-QH-1@1` |
| Linking basis | `AUTHOR_TAG_CANDIDATE` on `REQ_AVAILABLE_CAPACITY`, and nothing else |
| Meaning | "These records share an unresolved research requirement, so the earlier investigation is a relevant warning about what proved hard to measure. It is not evidence that the economic objects or events are connected." |
| Lesson | "free capacity net of bookings" was the earlier missing variable; its falsification route is attached |
| Use | Reuse the earlier recorded gap, falsification route or failure before acquiring similar evidence |

In the same `revisit` output, the exact-product match (UDI-001) to the registry claim is an economic candidate and ranks first. It also carried the capacity tag; the tag does not demote it.

## Before and after (synthetic, reproducible)

Full table: [graph_v1_1_quality.md](graph_v1_1_quality.md). Run `python -m src.research.graph quality --check` to regenerate and compare it. There are eight tasks with truths fixed before any system ran, plus a historical-memory probe against the committed V002 catalogue. "v1" is R3's counting practice, in which every operator result was a connection.

| Measure | Graph v1 | Graph v1.1 | Structured search |
|---|---:|---:|---:|
| Grounded connections presented (of 3 valid) | 3 | 3 | 3 |
| Missed valid connections | 0 | 0 | 0 |
| Trivial or unsupported matches presented as connections | 3 | 0 | 2 |
| Identity or timing errors | 0 | 0 | 0 |
| Review burden (items presented as connections) | 6 | 3 | 5 |
| Warnings retained as warnings (of 2) | 0 | 2 | 0 |
| Historical memory retrieved (of 2) / presented as connections / kept as cited warnings | 2 / 2 / 0 | 2 / 0 / 2 | 2 / 2 / 0 |

**Reading this honestly:**

- v1.1 finds exactly what v1 found. The gain is in presentation and review burden, not in new discoveries.
- Structured search also finds every valid connection here. As in the v1 review, the graph shows no discovery advantage over competent structured search on synthetic fixtures.
- Structured search reports tag-only and copied-evidence matches as plain results, and it has no same-gap view.
- These are functional checks on fixtures written by the implementer: no real-world accuracy, discovery or investment claim follows.

## Suggestion-traceable connection log (V2)

R3's graph arms logged graph-operator connections under fresh `CON-` ids. The originating `SUG-` id was lost, so the registered suggestion-rejection metric read 0/0.

**V2 format.** A row is V2 when it carries `log_version: GRAPH_PILOT_CONNECTION_V2`. It has the V1 fields plus:

| Field | Rule |
|---|---|
| `origin_suggestion_id` | Required (`SUG-` + 12 hex) for any row whose operator is a graph operator, or whose `found_via` is `GRAPH_ONLY` or `BOTH`; `null` otherwise |
| `origin_operator`, `origin_bases` | Must equal the suggestion's operator and exact match bases |
| `connection_class` | The suggestion's class. A `CONNECTION` row must be `ECONOMIC_CONNECTION_CANDIDATE` |
| `kind` | Adds `METHODOLOGICAL_WARNING`, so a warning the arm found useful is logged and scored separately |

**Validation.**

- `pilot connections LOG --arm G --suggestions EXPORTED.json` checks each origin against the exported suggestion list.
- The structured arm cannot log graph origins.
- Unblinding carries `log_version`, `origin_suggestion_id` and `connection_class`.
- `pilot report` counts graph items by origin and reports `methodological_warnings_logged` and `methodological_warnings_confirmed_useful` separately from connections.

**Backward compatibility.** V1 rows (R3) validate unchanged. R3's logs, adjudications, sealed exports, keys, results and dispositions are untouched. A test re-validates them, re-runs `pilot report --export blind_v2.json` and checks INCONCLUSIVE and pooled `G 3.151, S 4.162`.

## Validation

`python -m unittest discover -s tests` passes, with 10 new v1.1 tests. The graph, quality, dry-run, demo, build and public checks all pass. Receipt: [graph_v1_1_validation.json](graph_v1_1_validation.json).

| Test | Shows |
|---|---|
| Recall vs. unrelated salmon-style capacity claim | Warning, not a connection; lesson attached |
| Shared allocation blocker (`same-gap`), `next` | Warnings only; zero economic candidates |
| Exact product identifier | Grounded candidate, complete explanation; outranks the tag match |
| Documented supersession | Grounded; period YES; first unsupported inference named |
| Out-of-period supplier relationship; name-only supplier | Rejected (`PERIOD_INCOMPATIBLE`); abstains (`NO_VERIFIED_IDENTITY`) |
| Shared document; reused citation | Candidate marked not independent; reused citation unsupported |
| Historical memory | The real-catalogue warnings stay retrievable, cited, and their verdicts stand |
| Determinism | Classes categorical; repeat builds identical; inputs unchanged |
| V2 log | Origin required and matched; warnings cannot be logged as connections; S arm refused |
| R3 | Historical records and results unchanged |

## Critical review: what is still unverified

1. **No evidence of real-world improvement.** v1.1 changes how results are presented and counted. It finds nothing v1 did not. Whether it helps researchers, or whether the graph beats structured search at all, needs a prospective, properly blinded pilot (R4 draft, NOT_RUN).
2. **Self-written fixtures.** The fixtures and truths were written by the implementer to mirror R3. The 0-trivial result is a regression guarantee for those patterns, not a precision estimate.
3. **An exact identifier is not always informative.** `EXACT_ENTITY_ID` alone makes a candidate. Two records about the same regulator, exchange or very common product are "grounded" but may be trivial. Hub handling limits path expansion, not classification. A future version could need a role or degree condition. It was not added because there is no evidence yet to set one.
4. **Reuse detection depends on authors.** `REUSED_CITATION` relies on `reused_from` being recorded. Copied evidence without it still looks like an independent citation of the same document hash, which is itself never treated as corroboration.
5. **Lessons are only as good as the records.** A warning's lesson quotes tagged missing variables and the falsification route, or the cited historical finding. Requirement mappings in the catalogue remain retrieval aids pending human review.
6. **First-public times stay mostly UNKNOWN.** Temporal compatibility checks economic periods. It cannot certify that information was public at a decision time.
7. **Logging compliance is procedural.** V2 makes the origin checkable but cannot force an arm to log a graph-assisted idea as graph-originated. The R4 draft adds timestamp-derived effort and session-transcript checks.
8. **R3 is not reinterpreted.** Its free-text bases cannot be reclassified mechanically. Its INCONCLUSIVE result, dispositions and provenance amendment stand.

Main is untouched. Merging needs owner review.
