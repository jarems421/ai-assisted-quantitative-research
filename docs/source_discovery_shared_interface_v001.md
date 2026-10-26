# Source Discovery Shared Interface V001 (exported original) and reconciliation

**Status:** historical design record, superseded where the implemented contracts differ. The executable contracts in `src/research/source_v1/`, `src/research/campaign_v1/` and `src/research/source_search_v1/` govern.

## Provenance of the export

| Item | Value |
|---|---|
| Original | Claude Docs artifact "Source discovery architecture", tab **Shared interface V001** (https://claude.ai/artifact/EmtZo6b2HoU287Fk798RwB) |
| Tab revision | 2 (written 2026-10-25, unchanged since) |
| Exported | 2026-10-26, markdown export of the tab, 10,733 bytes |
| SHA-256 of the unmodified export | `fecf6933f7afe33bebe7144a7559560bacee8a3f5b212638a8590811988babd2` |
| Changes in the copy below | One only: the byline's owner mention chip (exported as `@james`) is rendered as "James Thomson", so GitHub does not notify an unrelated account. The date chip was exported as text. Nothing else was edited |

The original tab follows verbatim between the rules.

---

# Shared interface V001: campaign and source discovery

Oct 25, 2026 · James Thomson

Proposed. This is the contract between the campaign controller and the source-discovery component. It is written to be compatible with the source-request descriptor reserved on `codex/campaign-continuity-v001`, and it changes nothing in that branch. All records are canonical JSON with SHA-256 digests, and every record carries `authorises: []`.

## Call pattern

1. The campaign checks eligibility, holds any approval wait and writes one request file per attempt.
2. The campaign invokes `python -m src.research.source_v1 run <request.json> --scope <owner scope file>` as a bounded activity. Source discovery either refuses (NOT\_STARTED) or claims and runs exactly one attempt, writes its result and exits.
3. The campaign attaches the result by path and hash and reads its status, consumption, stop findings, pending hosts and custody handoffs. It decides what comes next: a custody step, an amendment wait or a new attempt.

Source discovery never calls back. Records live under `<base>/source-v1/<attempt_id>/` in the ignored `.research/` tree. Bodies sit in a `raw/` subfolder, which the campaign's metadata reader already refuses to scan. Read-only commands: `validate`, `status`, `result`. Record-only, run by the owner: `finalise-interrupted`.

## Mapping to the reserved descriptor

The request uses the schema name the campaign already reserves, `RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001`. Enabling the descriptor and writing requests is campaign work. Outputs use SOURCE\_\* names.

| Campaign field group | Source V001 fields |
| --- | --- |
| Identity | `campaign_id`, `branch_id`, `subject` (archive hash, card id, version, card hash), `request_id`, `attempt_id` |
| Decisive question | `question.text`, `question.requirements[]` |
| Authority | `authority`: scope reference and hash, owner, date, validity, operations, transmission, tiers, implementation hash |
| Stops | `stops.snapshot_sha256`, checked again against the live register at dispatch |
| Resources | `resources.campaign_allocation_ref`, `resources.reservation` |
| Provenance | Receipts and result: implementation hash, input and output hashes, original versus extraction, completeness |
| Result | SOURCE\_ACTIVITY\_RESULT\_V001: distinct statuses, receipts, `exactly_once: false` |

## Request

| Field | Content and rule |
| --- | --- |
| `schema` | `RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001` |
| `campaign_id`, `branch_id` | Campaign identifiers, opaque to source discovery |
| `subject` | `archive_sha256`, `card_id`, `card_version`, `card_sha256` |
| `request_id` | The logical request; several attempts may share it |
| `attempt_id` | Unique; a reused id is refused |
| `question` | `text`, the card's decisive question, and `requirements[]`, each with `id`, `role` (PREDICTOR, OUTCOME or CONTEXT), `quantity`, `unit`, `denominator`, `population`, `period` and `join`. Text or UNKNOWN; no dataset claims |
| `authority` | `scope_ref`, `scope_sha256`, `owner`, `decided_on` (date with timezone), `valid_until`, `implementation_sha256`, `operations` (V001: `RETRIEVE_EXACT_URL` only; SEARCH, MODEL\_CALL and EXTRACT reserved), `transmission` (V001: NONE), `tier_a` (`exact_urls[]`, `hosts[]`), `tier_b_classes` (V001: empty), `host_amendments[]` (hashes) |
| `stops` | `snapshot_sha256` |
| `resources` | `campaign_allocation_ref` (opaque, may be null) and `reservation`: `requests`, `total_bytes`, `per_response_bytes`, `wall_seconds`, `min_interval_seconds`, `searches`, `model_calls`, `metered_micro_usd` (the last three are 0 in V001) |
| `caller_ref` | Opaque; returned unchanged |

- The request hash is the SHA-256 of its canonical JSON.
- The owner scope file is a human record outside the request, and no assistant authors it. `run` checks its hash and that the request's tiers, operations, reservation and implementation hash fall within it. The request mirrors authority; it never grants it.

## Attempt journal

`<attempt>/journal.jsonl` uses the campaign V001 envelope: `seq`, `type`, `at`, `previous`, `record`, `hash`, with an exclusive writer lock and an fsync per event.

| Event | Record |
| --- | --- |
| ATTEMPT\_CLAIMED | Request hash, scope hash, reservation |
| REQUEST\_CLAIMED | Request index and URL, written before the connection opens |
| REQUEST\_FINISHED | Receipt hash |
| STOP\_FOUND | Stop finding hash |
| BUDGET\_EXHAUSTED | The limit reached |
| ATTEMPT\_FINISHED | Result hash |

Reserved for V002: MODEL\_CALL\_CLAIMED, MODEL\_CALL\_FINISHED, SEARCH\_OBSERVED, CANDIDATE\_RECORDED, HOST\_PENDING, EXTRACTION\_RECORDED, FIELD\_SUPPORT\_PROPOSED. A leftover lock or truncated tail means the attempt was interrupted. It is refused for mutation and never repaired.

## Retrieval receipt: SOURCE\_RETRIEVAL\_RECEIPT\_V001

One receipt per request, immutable.

| Field | Content |
| --- | --- |
| `attempt_id`, `request_index` | Position in the attempt |
| `requested_url`, `host`, `tier` | The exact target |
| `resolved_addresses[]`, `connected_address` | DNS answer and the pinned public address used |
| `started_at`, `finished_at` | UTC |
| `http_status` | Integer, or null if none was received |
| `headers_sha256`, `headers_selected` | Digest of all headers; `content-type`, `content-length`, `last-modified`, `etag`, `date` |
| `bytes_received`, `body_sha256`, `body_path` | Body kept under `raw/` even when incomplete |
| `complete` | True only for a full 2xx body within limits |
| `termination` | COMPLETE, SIZE\_STOP, TIME\_STOP, REDIRECT\_REFUSED, ACCESS\_DENIED, RATE\_LIMITED, NOT\_FOUND, UNEXPECTED\_RESPONSE or TRANSPORT\_FAILED |
| `implementation_sha256` | The running code |

Bodies are never parsed in V001.

## Activity result: SOURCE\_ACTIVITY\_RESULT\_V001

Written once per attempt. Fields: `request_sha256`, `attempt_id`, `caller_ref`, `journal_head`, `status`, `reason`, `receipts[]`, `retained[]` (URL, body hash, bytes, `complete`), `stop_findings[]`, `host_pending[]` (empty in V001), `field_support_proposals[]` (empty in V001), `consumption`, `custody_handoff[]` (receipt hash, body path, body hash), `exactly_once: false`, `authorises: []`.

| Status | Meaning |
| --- | --- |
| NOT\_STARTED | Refused before the claim (validation, authority, stop or reservation). Nothing sent |
| COMPLETE | Every planned request returned a complete 2xx body |
| PARTIAL | No stop condition, but at least one request ended at a size or time ceiling |
| UNAVAILABLE | The attempt ended on 404 or 410, recorded as a route-level stop finding |
| STOPPED | Ended by denial, rate limit, unexpected response, off-scope redirect, a stop in the register, or BUDGET. Remaining requests not sent |
| UNKNOWN | Interrupted or transport-uncertain; the remote effect is unknown. Also written by `finalise-interrupted` |

When several apply, the first in this order wins: UNKNOWN, STOPPED, UNAVAILABLE, PARTIAL, COMPLETE. The campaign may show an attempt with no claim as NOT\_STARTED and one with a claim but no result as INTERRUPTED.

## Stop snapshot and stop findings

**Stop entry:** `stop_id`; `scope` (HOST or ROUTE); `host`; `route` (exact URL or prefix, for ROUTE); `reason`; `observed_at`; `origin` (MACHINE\_RECORD, HUMAN\_ATTESTED or NEW\_FINDING); `evidence` (label and SHA-256, or UNKNOWN); `attested_by` (HUMAN\_ATTESTED only).

- **STOP\_SNAPSHOT\_V001:** entries sorted by id, input files by label and hash, `previous_snapshot_sha256` and its own hash. It must contain every entry of its predecessor.
- **STOP\_FINDING\_V001:** a NEW\_FINDING entry plus `attempt_id` and `receipt_sha256`, appended to the hash-chained register `<base>/source-v1/stops/register.jsonl`.
- **Matching:** case-insensitive host equality; a ROUTE stop matches its URL or prefix; unclear scope is recorded as HOST. A request is refused if any tier A host or URL matches.
- **Lifting:** only a future owner record (STOP\_LIFT, not part of V001). Software never removes an entry.
- **Privacy:** snapshots and the register live in ignored `.research/`. They carry hashes and labels from private stop files, never their contents.

## Budget reservation and consumption

- **Reservation**, from the request and within the owner scope, is fixed at ATTEMPT\_CLAIMED: `requests × per_response_bytes ≤ total_bytes`, plus wall time and the zero ceilings. It is never released.
- **Consumption**, in the result: `requests`, `bytes`, `wall_seconds`, `searches` and `model_calls`, each as `{at_least, exact}`; `metered_micro_usd` as `{reserved, estimated, actual}` with actual UNKNOWN unless evidenced; `subscription_usage` as NOT\_USED or UNKNOWN.
- `exact` is given only when every claimed request has a receipt. Interrupted requests count toward `at_least`.
- The campaign reads these values. It never sums them with its allocation, nets estimates against reservations or re-spends a reservation.

## Field support proposal

Reserved for Delivery 2; the V001 result carries an empty list.

| Field | Content |
| --- | --- |
| `proposal_id`, `retained_body_sha256` | What the proposal cites |
| `inspection_ref` | Quarry inspection excerpt id, or UNKNOWN |
| `excerpt` | `location`, `start_byte`, `end_byte`, `quote` |
| `l1_status` | VALUE\_QUOTED, QUOTE\_NOT\_FOUND or NOT\_CHECKED |
| `field_type` | From the closed vocabulary, or UNKNOWN |
| `unit`, `entity`, `period`, `basis` | Basis is GROSS, NET or UNKNOWN |
| `requirement_id` | The request requirement it addresses |
| `l2_status` | Always PROPOSED |
| `proposer` | MODEL or SOFTWARE, with served identity or REQUESTED\_ONLY |

Confirmation or rejection is a human record in Anvil/Discovery that cites `proposal_id`. Measurement validity (L3) never appears here.

## Invariants every implementation must test

1. A NOT\_STARTED result has no REQUEST\_CLAIMED event, and the fake transport records zero calls.
2. A durable REQUEST\_CLAIMED precedes every connection.
3. No URL is requested twice in an attempt, and a reused `attempt_id` is refused.
4. Redirects are never followed, and hosts outside tier A are never contacted.
5. A stop in the snapshot or the register refuses the request. A new denial writes a stop finding, and the remaining requests are not sent.
6. The result is written once and its hash is recorded in the journal; a second write is refused.
7. An interrupted attempt refuses mutation. `finalise-interrupted` yields UNKNOWN and sends nothing.
8. `exact` counts appear only when every claim has a receipt.
9. A truncated journal or leftover lock is never repaired or removed.
10. A running implementation hash that differs from `authority.implementation_sha256` refuses `run`.
11. Every record carries `authorises: []`, and no human-record field is written.

---

## Reconciliation with the implemented contracts (as of `main` e607e3f)

The tab above was written before implementation and before two review rounds. The table records each material difference. **Implemented** columns describe executable code; the tab is not normative where they differ.

### Source Retrieval V001 (`src/research/source_v1/`)

| Topic | Shared Interface V001 (draft) | Implemented |
|---|---|---|
| Invocation | `run <request.json> --scope <owner scope file>` | `run <request.json>`; the owner scope is referenced inside the request as `authority.scope {path, sha256}`. Commands: `implementation`, `stops-snapshot`, `check`, `run`, `status`, `result`, `finalise-interrupted` (no `validate`) |
| Record layout | `<base>/source-v1/<attempt_id>/` | `<base>/source-v1/attempts/<attempt_id>/`, plus global `ledger.jsonl`, `dispatch.lock`, `stops/snapshots/`, `stops/register.jsonl` |
| Authority fields | `owner`, `decided_on`, `valid_until`, `implementation_sha256` in the request | In the separate owner scope `SOURCE_RETRIEVAL_SCOPE_V001` (`decided_at`/`valid_until` with UTC offset), which also binds campaign, branch, card, the Quarry registry and acquisition scope, robots policy, reviewed access terms and cumulative ceilings. The request mirrors operations, transmission and tier A only |
| Stops | `stops.snapshot_sha256` | `stops.snapshot {path, sha256}`. The snapshot must be COMPLETE with a named human's `SOURCE_STOP_ATTESTATION_V001`, and fresh at run time (`STOP_SNAPSHOT_STALE`) |
| Reservation | includes `min_interval_seconds`; `requests × per_response_bytes ≤ total_bytes` | Pacing interval and timeout come from the Quarry scope. The product rule is not enforced; per-response ceilings shrink with remaining bytes. Requests must cover every URL plus one robots.txt per host |
| Journal | ATTEMPT_CLAIMED, REQUEST_CLAIMED, REQUEST_FINISHED, STOP_FOUND, BUDGET_EXHAUSTED, ATTEMPT_FINISHED; per-journal writer lock | Adds ATTEMPT_REFUSED (with reason) and ROBOTS_DISALLOWED. Locks are `attempt.lock` and the global `dispatch.lock`. Each result is anchored (journal event or create-only `finalisation.json`) **before** `result.json` is written |
| Receipt | status, headers, body, `complete` for "a full 2xx body", 9 terminations | Records facts (`stage`, `framing`, `content_encoding`, `declared_length`, `stopped_by`, `failure`) and recomputes `termination`, `complete`, `coverage` and `limitations` from them. Only an identity-encoded, fully framed `200` is COMPLETE. 15 terminations, including UNVERIFIED_LENGTH, UNEXPECTED_ENCODING, FRAMING_CONFLICT, DNS_FAILED, ADDRESS_REFUSED, DEADLINE_EXCEEDED |
| Result | listed fields; `retained[]` with `complete` | Adds `campaign_id`, `branch_id`, `request_id`, `scope_sha256`, `not_attempted`, `unfinished_requests`, `interrupted`, `journal_sha256`, `implementation_sha256`; `retained[]` and `custody_handoff[]` carry `coverage` and `custody_handoff[]` the exact Quarry route id. Every result is re-derivable byte for byte by `derive` |
| States | six statuses; campaign derives NOT_STARTED/INTERRUPTED | Same six statuses, plus attempt states `PRECLAIM_INCOMPLETE`, `INTERRUPTED`, `RESULT_PENDING` and `INCONSISTENT` from `status` |
| Route stops | match the URL **or a prefix** | Match the exact normalised request only |
| Field support proposal | reserved | Not implemented; `field_support_proposals` is always empty |
| Invariants 1-11 | listed | All implemented and covered by `tests/test_source_retrieval_v1.py` and `tests/test_source_retrieval_transport_v1.py` |

### Campaign Continuity V001 (`src/research/campaign_v1/`)

`status.branches[].provisional_source` advertises `RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001` with `implemented: false`, `dispatch_eligible: false` and required groups `EXACT_CARD_AND_DECISIVE_QUESTION`, `OWNER_SCOPE`, `HISTORICAL_STOPS`, `COMPONENT_RESERVATION`. The request schema name matches Source Retrieval V001. The campaign does not yet write requests, invoke `run` or attach results; that connection is campaign work. Its descriptor asks for a "component reservation ID"; Source Retrieval V001 provides none beyond the ledger's `ATTEMPT_RESERVED` event.

### Source Search Offline V001 (`src/research/source_search_v1/`)

Search validates already supplied capture bytes and defines **no shared wire contract**: candidate locations are caller-supplied `CandidatePointers`, and every candidate stays `MODEL_PROPOSED_SOURCE` or `BASELINE_PROPOSED_SOURCE`. The draft's reserved V002 events (SEARCH_OBSERVED, CANDIDATE_RECORDED, HOST_PENDING) and host tiers B and C exist nowhere. No binding from a search candidate to a Quarry route or retrieval request is implemented, and custody does not depend on one.

### Custody (this phase)

The draft says the campaign schedules "a custody step". Phase A implements that step as `python -m src.research.source_custody_v1 import` (see `docs/source_custody_v001.md`), producing a `QUARRY_SUPPLY_V002` package from a verified target receipt and a named human's claims record.

### Unresolved normative decisions

1. **Reservation identity.** Should Source Retrieval expose a reservation id for Campaign V001, or is the `ATTEMPT_RESERVED` ledger event hash sufficient?
2. **Custody scheduling and claims ownership.** Who schedules `source_custody_v1 import`, and who writes `QUARRY_RETRIEVAL_CLAIMS_V001` (the campaign owner, a separate reviewer)?
3. **Search to retrieval.** How a `MODEL_PROPOSED_SOURCE` candidate becomes an owner-approved Quarry route and exact-URL request; no contract exists.
4. **Eligible attempt statuses for custody.** Implemented: target receipts from finished COMPLETE, PARTIAL, STOPPED and UNAVAILABLE attempts are eligible; UNKNOWN and interrupted attempts are not. Confirm.
5. **Transport provenance.** Receipts do not record whether a real or injected transport produced them; SYNTHETIC classification currently rests on the human claims record.
6. **Caller authentication.** Neither Source Retrieval nor custody authenticates the campaign or the human named in a record.
