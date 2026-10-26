# Source Retrieval V001

Source Retrieval V001 runs **one bounded, owner-authorised retrieval attempt for exact HTTPS URLs**. Each attempt leaves durable provenance and one immutable result. It is the first component of Research OS's original-evidence acquisition capability, not a research assistant. It never searches, crawls, calls a model, extracts or interprets content, retries, resumes or schedules work.

Code: `src/research/source_v1/`. Design baseline: the Source Discovery V1.1 addendum and its shared interface. Tests: `tests/test_source_retrieval_v1.py` (restricted offline runner).

**Status:** implemented and tested offline only. No owner scope, stop attestation or live retrieval exists. A first live use needs an owner scope that a named human writes for one exact URL.

## Ownership

| Owner | Responsibility |
|---|---|
| Campaign controller | Writes the request, decides whether to run it, attaches the result and chooses what happens next |
| Source Retrieval | One attempt: checks, claims, retrieval, receipts, stop findings, the result |
| Quarry | Custody of retained originals later, through a custody step the campaign schedules (SUPPLY V002 is not part of this milestone) |
| Named humans | The owner scope, the stop attestation, reconciling interruptions and removing locks |

Source Retrieval never calls the campaign, the operator, Quarry, Jev or Anvil.

## Inputs

All inputs are local files, bound to each other by SHA-256.

| Input | Written by | Contents |
|---|---|---|
| Quarry route registry and acquisition scope (`QUARRY_ROUTE_REGISTRY_V001`, `QUARRY_ACQUISITION_SCOPE_V001`) | Owner | Exact URLs, hosts, request and byte ceilings, minimum interval and timeout. Validated by Quarry's own unchanged `plan()`: stopped or restricted routes, expansion and private locators are refused |
| Owner scope (`SOURCE_RETRIEVAL_SCOPE_V001`) | A named human, never an assistant | Binds campaign, branch, card hash, implementation hash, the two Quarry files, validity window, robots policy, reviewed access terms, and cumulative attempt, request and byte ceilings |
| Stop attestation (`SOURCE_STOP_ATTESTATION_V001`) | A named human | Binds every stop-record input by hash, resolves records that name no host, and lists stops known only from reports |
| Stop snapshot (`SOURCE_STOP_SNAPSHOT_V001`) | `stops-snapshot` | Machine-readable stops (any URL in a stop record gives a host-level stop) plus the attested ones. `COMPLETE` only with an attestation that leaves nothing unresolved. Additive over a previous snapshot |
| Request (`RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001`) | Campaign | Identity, decisive question, references to the owner scope and stop snapshot, tier A URLs, component reservation, opaque `caller_ref` |

Get the implementation hash an owner scope must bind with `python -m src.research.source_v1 implementation`. Any change to the package, or to the Quarry, contract or spec code it uses, changes the hash and refuses old scopes.

## One attempt

1. **Refuse or claim.** The command takes the global dispatch lock and refuses a reused attempt id. It then checks the owner scope, Quarry `plan()`, validity, implementation hash, reservation against the Quarry and cumulative scope ceilings, and stops (snapshot plus the live register). A failure writes a `NOT_STARTED` result and touches no network.
2. **Claim.** Before any network effect, it appends `ATTEMPT_RESERVED` to the global ledger and `ATTEMPT_CLAIMED` to the attempt journal. The reservation is never released.
3. **Per request,** serially: robots.txt once per host, then each target.
   - Pace globally from the last dispatch in the ledger, honouring a robots.txt `Crawl-delay`. A delay that cannot fit the wall budget stops the attempt (BUDGET) without sleeping.
   - Check the budget.
   - Journal `REQUEST_CLAIMED` and ledger `REQUEST_DISPATCHING`.
   - Resolve DNS. Refuse the host if any answer is not a public global unicast address.
   - Connect only to the pinned first address, with the URL host for SNI and certificate checks.
   - GET with no redirects, identity encoding and no proxy or credentials.
   - Stream to an exclusive raw file within the byte and time ceilings.
   - Write an immutable receipt.
4. **Result.** Written once; its hash is the journal's last event. Then the locks are released.

| Response | Receipt termination | Attempt effect | Stop finding |
|---|---|---|---|
| 2xx, complete | COMPLETE | continue | — |
| 2xx over the byte ceiling (declared: no body read; streamed: prefix kept) | SIZE_STOP | PARTIAL, continue | — |
| 2xx past the time ceiling | TIME_STOP | PARTIAL, continue | — |
| 3xx | REDIRECT_REFUSED | STOPPED, end | route |
| 401, 403 | ACCESS_DENIED | STOPPED, end | host |
| 429 | RATE_LIMITED | STOPPED, end | host |
| 404, 410 | NOT_FOUND | UNAVAILABLE, end | route |
| Other status | UNEXPECTED_RESPONSE | STOPPED, end | host |
| DNS failure or no address | DNS_FAILED | STOPPED, end | — |
| Non-public address | ADDRESS_REFUSED | STOPPED, end | host |
| Connection, TLS or read failure, or a short body | TRANSPORT_FAILED | UNKNOWN, end | host |

For robots.txt, a 2xx response is parsed, with at most the first 512 KiB used; a disallowed target is not requested and receives a route stop. Other 4xx responses, apart from 401, 403 and 429, mean "no robots.txt" and impose no rules. An unread or timed-out robots.txt stops the attempt (`ROBOTS_UNRESOLVED`). Robots requests count against the reservation.

Status precedence: UNKNOWN, STOPPED, UNAVAILABLE, PARTIAL, then COMPLETE. Receipts record exception type names only, never exception text.

## Interruption

If the process ends after the claim without a result, the locks stay and the attempt is `INTERRUPTED`. Every further attempt is refused (`DISPATCH_LOCKED`). The owner then:

1. Confirms no process is running and runs `finalise-interrupted <attempt> --no-attempt-running`. This writes an `UNKNOWN` result, records each unfinished request with the bytes kept so far, and adds a host stop for each unfinished request. Nothing is re-sent.
2. Removes `attempts/<attempt>/attempt.lock` and `dispatch.lock` by hand. Software never removes them.

The campaign decides whether a new attempt, with a new id and reservation, is appropriate. Exactly-once remote execution is never claimed.

## Commands

```powershell
python -m src.research.source_v1 implementation
python -m src.research.source_v1 stops-snapshot --from-dir data/raw --input <file> [--attestation <file>] [--previous <snapshot>]
python -m src.research.source_v1 check <request.json>      # read-only: the refusal run would record
python -m src.research.source_v1 run <request.json>        # one attempt; real HTTPS
python -m src.research.source_v1 status <attempt-id>       # read-only verification
python -m src.research.source_v1 result <attempt-id>       # verified result only
python -m src.research.source_v1 finalise-interrupted <attempt-id> --no-attempt-running
```

`--base <dir>` goes before the command. Records live under `<base>/source-v1/`, by default this checkout's ignored `.research/`; another Git checkout is refused.

| Path | Contents |
|---|---|
| `ledger.jsonl` | Global hash-chained ledger: reservations and dispatch times |
| `dispatch.lock` | Present while an attempt runs, or after an interruption |
| `stops/snapshots/*.json`, `stops/register.jsonl` | Snapshots and new stop findings |
| `attempts/<id>/request.json`, `inputs/`, `journal.jsonl` | Exact request, copies of its inputs, attempt journal |
| `attempts/<id>/receipts/NNN.json`, `raw/NNN.body` | Receipts and retained bytes, including error bodies and prefixes |
| `attempts/<id>/result.json` | `SOURCE_ACTIVITY_RESULT_V001` |

## Interface consumed by Campaign Continuity V001

The campaign writes a request in the reserved `RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001` schema. It can preflight with `check`, invoke `run`, then attach `attempts/<id>/result.json` by path and hash. It reads `status` for verification and lock state. The result fields are:

- **Identity:** `schema`, `request_sha256`, `attempt_id`, `campaign_id`, `branch_id`, `request_id`, `caller_ref`, `scope_sha256`.
- **Outcome:** `status` (`NOT_STARTED`, `COMPLETE`, `PARTIAL`, `UNAVAILABLE`, `STOPPED` or `UNKNOWN`), `reason`, `interrupted`.
- **Evidence:** `receipts[]` (SHA-256 of each receipt file), `retained[]`, `custody_handoff[]` (2xx target bodies with Quarry route id, hash, bytes and coverage).
- **Findings and remaining work:** `stop_findings[]`, `not_attempted[]`, `unfinished_requests[]`.
- **Consumption:** requests, bytes and wall seconds as `{at_least, exact}`; searches and model calls zero; metered spend zero; subscription usage `NOT_USED`.
- **Binding:** `journal_head`, `journal_sha256`, `implementation_sha256`.
- **Reserved, empty in V001:** `host_pending[]`, `field_support_proposals[]`.
- **Constants:** `exactly_once: false`, `authorises: []`.

The campaign shows an attempt with no claim as not started, and one with a claim but no result as interrupted. It never sums component reservations with its own allocation.

## Safety properties and assumptions

**Tested offline** with fictional hosts, injected fake transports and a fake clock, under the restricted runner. Socket, DNS and process creation are denied there and also patched in each test. Covered:

- Private, loopback, link-local, ULA, CGNAT, mapped, multicast, unspecified, mixed and malformed addresses.
- Refused redirects, DNS failures, and stopped hosts and routes, including hosts from machine records, attested routes and new findings.
- 401, 403, 429, 404 and 5xx responses.
- Declared and streamed oversize, short bodies and reset connections.
- Time and byte budgets, global pacing and `Crawl-delay`.
- Duplicate and concurrent attempts.
- Interruption, record-only finalisation and persistent locks.
- Altered receipts, bodies, results and journals.
- Scope violations: URLs, ceilings, card binding, implementation drift, expiry, assistant or placeholder owners and changed scope bytes.
- Quarry route stops, cumulative scope ceilings, robots.txt allow, disallow, absent, denied, error and oversize.
- Stop attestation identity, input binding, completeness and additivity.
- The pinned connection: TCP to the pinned address, SNI and certificate for the URL host, and refusal of a different peer.

**Assumptions, not established by these tests:**

- The real `HttpsTransport` has never been run against a network. TLS, `http.client` chunked and length handling and real resolvers are trusted, not tested.
- Time bounds are checked between reads. A single blocking read can overrun by up to the socket timeout.
- The DNS answer is validated and pinned once per request. Rebinding between the check and the connection is prevented by connecting to the pinned address, not by resolving again.
- Machine stop reconciliation finds URLs anywhere in a stop record and stops their hosts, so it can over-block. Records naming no host need the human attestation. Completeness of the stops known only from reports rests on the attester.
- A trusted local filesystem and reviewed code; this is not an OS sandbox. Lock files and fsync give crash evidence, not exactly-once execution.
- The `ResearchOS-SourceRetrieval` user-agent is honest but carries no contact identity. Site terms beyond robots.txt rest on the owner's `access_terms_reviewed` statement.

**Not in this milestone:** search, Codex or any model call, OCR or extraction, field proposals, host tiers B and C, host amendments, Quarry SUPPLY V002, campaign scheduling or attachment, and any live retrieval.
