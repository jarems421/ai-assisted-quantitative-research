# Graph v1 operator guide

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

Graph v1 lets a researcher ask, whenever something new is recorded: *have we met this object, document, relationship or research problem before, and what genuinely connects them?* It reads Discovery Lab ledgers and the historical-memory catalogue. It writes nothing back and authorises nothing. [Design](graph_v1_design.md) · [Walkthrough](graph_v1_walkthrough.md) · [Backfill audit](graph_v1_backfill_audit.md) · [Pre-pilot review](graph_v1_review.md) · [Pilot pre-registration](graph_pilot_preregistration.md) · [Pilot dry run](graph_pilot_dry_run.md) · [v1.1 connection classes](graph_v1_1_design.md).

## Quick start

```sh
python -m src.research.graph build --check                      # counts, inputs, exclusions, digest, rebuild check
python -m src.research.graph search "spare capacity"
python -m src.research.graph trace HIST-EF06                    # historical claim lineage and verdicts
python -m src.research.graph same-gap REQ_AVAILABLE_CAPACITY    # past work blocked by the same measurement
python -m src.research.graph explain HIST-SH09 CIK:0000093410   # why no exposure is demonstrated
python -m src.research.graph failures                           # bounded negative results, with scope
python -m src.research.graph demo --check                       # reproducible demos A-F
python -m src.research.graph evaluate                           # offline ordinary-search vs graph check
python -m src.research.graph quality --check                    # v1.1 synthetic discovery-quality regression
python -m unittest tests.test_graph -v
```

Node arguments accept full IDs (`observation:DLC-X/OBS-1@2`) or unambiguous short forms (`OBS-1`, `OBS-1@2`, `DLC-X`, `HIST-F01`, `CIK:0000093410`, `REQ_AVAILABLE_CAPACITY`). An ambiguous or unknown token is refused with suggestions. Add `--json` to any query for the structured result.

## Workflow with Discovery Lab

1. **Record.** Record an observation or documented relationship through Discovery Lab (`python -m src.research.discovery add ...`). Discovery Lab validates and appends it. Live ledgers live under `docs/strategy/discovery/`.
2. **Find connections.** Run `revisit <campaign or observation>` and `complements <observation>`. The graph rebuilds from the ledgers on every command, so it is never stale.
3. **Review.** Each suggestion lists its match basis, evidence, what is unverified and the minimum evidence to resolve it. The earlier claim's status stands.
4. **Check originals, only where authorised.** Any substantive new claim is recorded and frozen through Discovery Lab, under its existing M/H review. Cite a related earlier claim in `selection.prior_related_claims` using the campaign-qualified form `DLC-X/CAND-Y`, so the graph links them.
5. **Feed back.** The outcome, including a failure, becomes graph memory the next time the graph builds.

No graph command appends to a ledger or changes a disposition.

## Commands

| Command | Use |
|---|---|
| `build [--check]` | Projection counts, admitted inputs, excluded inputs, issue count and canonical digest; `--check` also rebuilds and compares digests |
| `search TEXT` | Nodes containing every term (up to 30), each with status, fixture and origin |
| `show NODE` | All attributes, restrictions, evidence references and incident edges |
| `neighbourhood NODE [--semantic N]` | A bounded neighbourhood; hubs and campaign-like nodes are listed as collapsed, not expanded |
| `explain A B [--semantic N]` | Up to 10 paths with step-by-step evidence and the first unsupported leap |
| `trace CLAIM` | Discovery Lab claim lineage (versions, freezes, reviews, dispositions) or historical investigation memory |
| `shared NODE` | Operator A: same document hash or identified entity in other campaigns |
| `complements OBSERVATION` | Operator B: documented, period-compatible context from other campaigns |
| `same-gap REQ_or_BLOCKER` | Operator C: claims blocked by the same requirement |
| `gaps CLAIM` | Operator G: unverified links |
| `revisit TARGET` | Operator F: earlier claims a new observation might inform |
| `changes` | Operator E: changed, conflicting, superseded and stale knowledge |
| `next` | Operator H: reusable decisive checks (`PROPOSAL_ONLY`) |
| `failures`, `orphans` | Bounded negative results; standalone observations retained for later |
| `export neighbourhood\|explain\|trace NODE... --format mermaid\|dot [--out FILE]` | Focused visual export with a legend and the banner |
| `suggestions TARGET` | Pilot hook: suggestions flagged with whether competent structured search over the same knowledge would find them |
| `baseline-search CAMPAIGN OBSERVATION` | The pilot's structured arm: exact-identifier, content-hash, reference, period and known-at search, with no graph projection |
| `pilot snapshot\|verify\|connections\|blind\|adjudications\|account\|report` | Proposed-pilot tooling: freeze a packet's prior inputs, verify an arm's starting copy, validate logs, build the blinded export, check accounting, report pairs |
| `pilot dry-run [--write\|--check]` | Synthetic end-to-end rehearsal of the pilot through this CLI |
| `pilot connections LOG --arm G [--suggestions FILE... --packet-snapshot SNAP]` | Validate a V1 log, or a V2 log whose graph-originated rows match the frozen, replayed suggestion export exactly (id, operator, bases, class, endpoints, time). Graph-originated V2 rows are refused without the export |
| `pilot snapshot ... --connection-log GRAPH_PILOT_CONNECTION_V2` | Freeze a prospective packet for V2 logs: V1 rows refused; operator version, classification ruleset (`--classification`) and exact implementation (commit, content of the computed import boundary, Python and dependency versions; clean git checkout required) pinned. The graph arm saves each suggesting query's `--json` output under `<packet>/suggestions-G/`; `pilot blind` seals their hashes in the key |
| `quality [--write\|--check]` | Graph v1.1 synthetic regression: v1, v1.1 and structured search on the same fixtures |
| `adversarial [--write\|--check]` | Graph v1.1 adversarial synthetic evaluation: reused citations, trivial shared identifiers, periods, tags, name and ticker identities |
| `pilot effort PACKET --arm S\|G` | R4 readiness: timestamp-derived elapsed time beside self-reported minutes, with discrepancy flags |
| `pilot suggestion-accounting PACKET [--export NAME]` | R4 readiness: exported, logged, declined and unlogged graph suggestions by class, with denominators |
| `pilot r4-dry-run [--write\|--check]` | R4 readiness Phase A synthetic rehearsal with mutation checks (not an R4 run) |
| `pilot session-attest PACKET --arm S\|G --event START\|STOP --by NAME` | The human arm operator's own immutable session attestation, written as the event happens (assistants refused) |
| `pilot adjudication-seal PACKET --reviewer R1\|R2 --by NAME` | Phase B: a human reviewer personally seals their economic and usefulness logs by hash (immutable; assistants refused) |
| `pilot adjudication-agreement PACKET [--export NAME]` | Phase B: validate both sealed reviewers; consensus, agreement (kappa), exposure, reveal order and conformance |
| `pilot r4-phase-b-dry-run [--write\|--check]` | Phase B synthetic rehearsal of dual human adjudication (not an R4 run) |
| `holdout [--write\|--check]` | GRAPH_CLASSIFICATION_V1_2 holdout, written after the rule was registered: v1.1 vs v1.2 vs structured search |

**Common options:**

| Option | Effect |
|---|---|
| `--mode memory\|prospective\|synthetic` | Choose which inputs are admitted (see below) |
| `--ledgers FILE...` | Use these ledgers instead of every `*.jsonl` under `docs/strategy/discovery/` |
| `--catalogue FILE` | Use a different historical-memory catalogue |
| `--no-memory` | Synthetic mode without historical memory |
| `--known-at TIME` | Only knowledge appended by this time |
| `--as-of DATE` | Only relationships valid, and observations occurred, by this economic date |
| `--verified-only` | Hide unverified assertions and historical memory |
| `--history` | Include superseded versions |
| `--exclude-retrospective` | Hide retrospective ledgers and historical memory |
| `--json` | Print the structured result instead of text |
| `--snapshot FILE --arm S\|G [--query-at TIME]` | Pilot view: the snapshot's frozen prior inputs plus that arm's own ledger as appended by the query time (default now, never in the future). Refuses `--ledgers`, `--known-at`, `--catalogue`, `--mode` and `--as-of`, and every graph operator for arm S |

## Reading results

**Every output starts with the banner. Treat it literally.**

- **Connection class (v1.1):** every `revisit`, `complements`, `shared`, `same-gap` and `next` result has a `connection_class`, and the output ends with a `connection_summary`:
  - **`ECONOMIC_CONNECTION_CANDIDATE`** rests on an exact document hash, an identified object or a documented relationship covering the date. It carries `grounding`: records, basis, joining objects, economic objects and roles, temporal check, what is established, what is not, the first unsupported inference and why it is worth investigating. It is a reason to investigate, never evidence of exposure.
  - **`METHODOLOGICAL_WARNING`** rests only on a shared requirement, tag, mapping or blocker. It carries `warning`: the shared requirement and the earlier record's lesson. Read it as "this was hard to measure before", never as "these events are connected". All `same-gap` and `next` results are warnings.
  - **`UNSUPPORTED_MATCH`**, for example a citation copied from the other record (`REUSED_CITATION`), is kept for transparency only.
  - Candidates always list first, so a tag match never outranks a grounded one.
- **Status on the record:** each record shows its assertion status, for example `ORIGINAL_FIELD_OBSERVED`, `ORIGINAL_DOCUMENT_REFERENCED` (document seen, field not verified), `DOCUMENTED_RELATIONSHIP` (with a separate allocation status) or `RECORDED_UNVERIFIED` (with a reason).
- **Joining points:** entities and documents only join records. Reaching a company tells you nothing about its exposure.
- **Suggestions:**
  - **`strength`** is the strongest match basis: exact document hash, then exact entity, then documented relationship in a compatible period, then requirement match, then author tag. Results sort by connection class first, then strength.
  - **`candidate_only: true`** means the match rests on a free-text author tag.
  - **`previous_status_stands: true`** is always set.
  - **`authority`** always says that no work is authorised.
- **Paths:** `explain` marks every step `STRUCTURAL` or `SEMANTIC_RELATIONSHIP`, and names the first unsupported economic leap. Even a fully supported path ends at `FINANCIAL_TRANSMISSION_UNVERIFIED`.
- **Rejections:** `rejected` lists look-alikes, keyword-only overlaps, period-incompatible relationships and unknown tags. These are useful because they show what the graph refused to connect.
- **Historical memory:** `HISTORICAL_CONCLUSION` nodes quote their source report. If `citation_status` is not `CURRENT`, re-read the report before relying on the memory.

## Modes and time

| Mode | Admits | When to use |
|---|---|---|
| `memory` (default) | Live and retrospective ledgers, plus the catalogue, all labelled | Exploring what Research OS knows |
| `prospective` | Live ledgers only | Evaluation protocols; combine with `--known-at` |
| `synthetic` | Synthetic fixtures only, with or without memory | Demonstrations and tests |

The two time filters answer different questions:

- **`--as-of 2000-06-30` (economic validity):** hides relationships whose dated period does not cover that date, and observations not yet occurred.
- **`--known-at 2026-11-01T00:00:00Z` (what Research OS had recorded by then):** uses ledger append times. It counts the catalogue from its own `recorded_at_utc`, never from the original investigation dates. It applies one cutoff to every ledger, so it is for looking back. For an active campaign, use `--snapshot`: frozen prior inputs, plus the campaign's own records as appended by the query time.

Unknown first-public times stay `UNKNOWN`. The graph never derives them.

## Requirement vocabulary and tags

The eight requirement classes are defined in catalogue V002, each with what it *does not* mean:

| Requirement class | Measurement it names |
|---|---|
| `REQ_AVAILABLE_CAPACITY` | Capacity actually available, net of commitments |
| `REQ_REALISED_ACTIVITY` | Activity that actually occurred |
| `REQ_QUALIFIED_COMMERCIAL_EXPOSURE` | A documented, qualified commercial opportunity or exposure (added in V002 for F03) |
| `REQ_RETAINED_NET_ECONOMICS` | Retained or net amounts |
| `REQ_DOCUMENTED_ALLOCATION` | A documented split of an aggregate |
| `REQ_ENTITY_COHORT_JOIN` | Matching entity, cohort and period |
| `REQ_UNREDACTED_CONTRACT_AMOUNT` | The contractual amount itself |
| `REQ_HISTORICAL_SCHEDULE_OR_VERSION` | The original dated schedule or version |

Claims link to requirements in three ways:

| Route | How it is created | Strength |
|---|---|---|
| Mechanical blocker mapping | A Discovery Lab checklist code (for example `ALLOCATION_UNVERIFIED`) maps to a class | Curated |
| Catalogue `claim_mappings` | Versioned, reviewable entries for live claims | Curated |
| Author tag | `[REQ:CLASS]` in a candidate's `missing_variables`, or `[MEASURES:CLASS]` in an observation's text | Candidate only |

Unknown tags are reported (`UNKNOWN_TAG`) and create no edge. A tag never shows that an observation measures a requirement or resolves a blocker.

To add memory or mappings, edit the catalogue under the rules in the [backfill audit](graph_v1_backfill_audit.md):

- Every quote must be an exact substring of a tracked report.
- Recompute that report's hash.
- Use identifiers only when the repository records them.

The build refuses structural errors and flags stale citations.

## Visual export

```sh
python -m src.research.graph export explain OBS-GB-1 SYN_LISTED:ECHO --mode synthetic --ledgers a.jsonl b.jsonl --out path.mmd
python -m src.research.graph export trace HIST-EF06 --format dot --out ef06.dot
```

**Mermaid export:**
- **Node colours:** verified assertions (green), recorded-unverified (amber, dashed), contradicted (red), superseded (grey), historical memory (purple), claims (blue), requirements and blockers (red dashed), neutral objects (white).
- **Arrows:** solid for semantic relationship ends, dotted for structural links.
- **Limit:** at most 30 nodes.

The DOT export uses the same categories.

## Test coverage map

`tests/test_graph.py` covers the owner's 44 adversarial cases:

| Cases | Test |
|---|---|
| 1, 2 | `test_tampered_ledger_refuses_build`, `test_duplicate_campaign_ids_refused` |
| 3 | `test_namespaced_identities_are_stable_and_distinct` |
| 4, 5, 6 | `test_similar_names_and_name_only_entities_never_merge`, `test_ticker_is_not_a_legal_entity_identity`, `test_cross_ledger_entity_type_conflict_is_exposed` |
| 7, 8 | `test_relationship_and_allocation_are_separate_assertions`, `test_verified_path_does_not_certify_exposure` |
| 9, 10 | `test_document_reference_and_schema_do_not_verify_a_quantity` |
| 11 | `test_retrospective_description_stays_unverified` |
| 12, 15 | `test_unknown_clocks_stay_unknown_and_first_public_is_never_derived` |
| 13 | `test_modern_relationship_is_not_applied_to_an_earlier_date` |
| 14 | `test_transcription_time_is_not_backdated` |
| 16, 17 | `test_shared_document_is_one_document_and_never_independent_corroboration` |
| 18 | `test_frozen_claim_keeps_its_version_references` |
| 19 | `test_reformulations_stay_distinct_from_originals` |
| 20, 21 | `test_contradicted_and_superseded_records_remain_inspectable` |
| 22, 23 | `test_synthetic_never_enters_memory_or_prospective_views`, `test_retrospective_and_historical_records_are_labelled` |
| 24, 25, 26, 27 | `test_entity_nodes_do_not_block_verified_traversal`, `test_structural_steps_do_not_reject_short_semantic_paths`, `test_long_paths_are_capped_and_never_self_certify`, `test_high_degree_hubs_do_not_bridge_results` |
| 28, 29 | `test_keywords_and_unknown_tags_create_no_links` |
| 30, 39 | `test_suggestions_never_become_verified_relationships` |
| 31 | `test_new_campaign_yields_an_explainable_cross_campaign_suggestion` |
| 32 | `test_historical_states_are_preserved_verbatim` |
| 33, 34 | `test_f01_and_sh09_gain_no_fictional_economic_facts` |
| 35 | `test_ef06_versions_are_separate_economic_objects` |
| 36, 41 | `test_missing_and_changed_reports_are_flagged_not_filled`, `test_corrupted_catalogue_refuses_build` |
| 37 | `test_reads_only_declared_inputs_and_never_private_archives` |
| 38 | `test_graph_operations_are_offline` |
| 40 | `test_build_is_deterministic_across_locations` |
| 42 | `test_empty_and_unrelated_inputs_abstain` |
| 43, 44 | The full local suite, public checks, the Discovery Lab demo check and the EXP004 audits (see the [validation receipt](graph_v1_validation.json)) |

Additional tests cover the walkthrough, the utility check and adjudication-log validation. `GraphReviewRegressionTests` covers the pre-pilot review defects: catalogue V002 corrections and V001 preservation, archive-path CIK identity, evaluation input isolation, competent-baseline fairness and pilot-export memory parity.

`GraphV11ConnectionClassTests` covers Graph v1.1: warnings versus economic candidates, grounded explanations, class ordering, reused citations, historical-memory warnings, the V2 suggestion-traceable connection log and R3 preservation ([design](graph_v1_1_design.md)).
