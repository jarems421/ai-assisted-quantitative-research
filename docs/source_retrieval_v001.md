# Source Retrieval V001

Source Retrieval V001 runs **one bounded, owner-authorised retrieval attempt for exact HTTPS URLs**. Each attempt leaves durable provenance and one immutable result. It is the first component of Research OS's original-evidence acquisition capability, not a research assistant. It never searches, crawls, calls a model, extracts or interprets content, retries, resumes or schedules work.

Code: `src/research/source_v1/`. Design baseline: the Source Discovery V1.1 addendum and its shared interface. Tests:

- `tests/test_source_retrieval_v1.py`: restricted offline runner, with fake transports.
- `tests/test_source_retrieval_transport_v1.py`: the real transport against a loopback-only TLS server, run as its own CI step.

**Status:** implemented and tested offline and on loopback only. No owner scope, stop attestation or live retrieval exists. A first live use needs an owner scope that a named human writes for one exact URL.

## Ownership

| Owner | Responsibility |
|---|---|
| Campaign controller (Campaign Continuity V001) | Writes the request, decides whether to run it, attaches the result and chooses what happens next |
| Source Retrieval | One attempt: checks, claims, retrieval, receipts, stop findings, the result |
| Quarry | Custody of retained originals later, through a custody step the campaign schedules (SUPPLY V002 is not part of this milestone) |
| Named humans | The owner scope, the stop attestation, reconciling interruptions and removing locks |

Source Retrieval never calls the campaign, the operator, Quarry, Jev or Anvil.

## Inputs

All inputs are local files, bound to each other by SHA-256.

| Input | Written by | Contents |
|---|---|---|
| Quarry route registry and acquisition scope (`QUARRY_ROUTE_REGISTRY_V001`, `QUARRY_ACQUISITION_SCOPE_V001`) | Owner | Exact URLs, hosts, request and byte ceilings, minimum interval and timeout. Validated by Quarry's own unchanged `plan()`: stopped or restricted routes, expansion and private locators are refused. Each exact URL must map to exactly one approved route (`ROUTE_AMBIGUOUS` otherwise) |
| Owner scope (`SOURCE_RETRIEVAL_SCOPE_V001`) | A named human, never an assistant | Binds campaign, branch, card hash, implementation hash, the two Quarry files, validity window, robots policy, reviewed access terms, and cumulative attempt, request and byte ceilings |
| Stop attestation (`SOURCE_STOP_ATTESTATION_V001`) | A named human | Binds every stop-record input by hash, resolves records that name no host, and lists stops known only from reports |
| Stop snapshot (`SOURCE_STOP_SNAPSHOT_V001`) | `stops-snapshot` | Machine-readable stops (any URL in a stop record gives a host-level stop) plus the attested ones. `COMPLETE` only with an attestation that leaves nothing unresolved. Additive over a previous snapshot |
| Request (`RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001`) | Campaign | Identity, decisive question, references to the owner scope and stop snapshot, tier A URLs, component reservation, opaque `caller_ref` |

Get the implementation hash an owner scope must bind with `python -m src.research.source_v1 implementation`. Any change to the package, or to the Quarry, contract or spec code it uses, changes the hash and refuses old scopes.

**Exact URLs.** HTTPS, a public DNS host, no port, credentials or fragment, and no dot segments. Two URLs that produce the same request are refused before anything is created: `/x` and `/x?`, a bare host and `/`, or `%31` and `1`. Each request is dispatched at most once per attempt.

## What these records do and do not establish

- **Retrieved bytes are not an authenticated original.** A COMPLETE receipt means the host named in the URL, authenticated by TLS at retrieval time, served exactly these bytes in a fully framed `200` response. It does not establish that the document is genuine, correct, the publisher's original or the version that was public at any earlier time.
- **`check` is informational, not authority.** It reports the refusal `run` would record at that moment. Conditions can change before `run`, and only `run`'s own checks decide.
- **Names are not authentication.** The owner and attester fields are human-name strings, refused when they look like an assistant or a placeholder. They are not cryptographic signatures and do not prove who wrote the file.
- **The campaign is not authenticated.** Source V001 checks that the request's campaign, branch and card match the owner scope. It does not authenticate the caller or prove the request came from Campaign Continuity V001.

## One attempt

1. **Refuse, or prepare.**
   - Invalid requests fail before anything is written.
   - The command takes the global dispatch lock and refuses a reused attempt id.
   - The attempt directory appears atomically with its exact request, renamed from a staging folder.
   - It then checks the owner scope, Quarry `plan()` and route mapping, validity, implementation hash, reservation against the Quarry and cumulative scope ceilings, and stops (the snapshot, its freshness and the live register).
   - A failure writes an anchored `NOT_STARTED` result and touches no network.
2. **Claim.** It copies the inputs, then appends `ATTEMPT_RESERVED` to the global ledger and `ATTEMPT_CLAIMED` to the attempt journal before any network effect. The reservation is never released.
3. **Per request,** serially: robots.txt once per host, then each target.
   - Pace globally from the last dispatch in the ledger, honouring a robots.txt `Crawl-delay`. A delay that cannot fit the wall budget stops the attempt (BUDGET) without sleeping.
   - Check the budget.
   - Journal `REQUEST_CLAIMED` and ledger `REQUEST_DISPATCHING`.
   - Resolve DNS. Every address in the answer is validated before anything is truncated. A non-public address anywhere refuses the host. A malformed answer, or one with more than 16 addresses, refuses the request. If the request's time expired during resolution, no connection is made.
   - Connect only to the pinned first address, with the URL host for SNI and certificate checks.
   - GET with no redirects, identity encoding and no proxy or credentials.
   - Stream to an exclusive raw file within the byte and time ceilings.
   - Write an immutable receipt recording facts: stage reached, status, framing, content encoding, declared length, bytes, stop cause, failure type. Its classification is recomputed from those facts.
4. **Result.** The result is derived from the journal and verified receipts. Its SHA-256 is appended to the journal (`ATTEMPT_FINISHED`) before `result.json` is written, then the locks are released.

| Response | Receipt termination | Coverage | Attempt effect | Stop finding |
|---|---|---|---|---|
| `200`, identity encoding, framed by Content-Length (bytes equal) or completed chunked encoding | COMPLETE | COMPLETE | continue | — |
| `200` with no length framing (connection close) | UNVERIFIED_LENGTH | UNVERIFIED | PARTIAL, continue | — |
| `200` over the byte ceiling (declared: no body read; streamed: prefix kept) | SIZE_STOP | PREFIX or NONE | PARTIAL, continue | — |
| `200` past the time ceiling | TIME_STOP | PREFIX or NONE | PARTIAL, continue | — |
| `200` with a non-identity Content-Encoding | UNEXPECTED_ENCODING | NONE | STOPPED, end | route |
| `200` with contradictory framing: Transfer-Encoding plus Content-Length, other transfer codings, unequal or non-numeric lengths, or more bytes than declared | FRAMING_CONFLICT | NONE | STOPPED, end | host |
| 3xx | REDIRECT_REFUSED | NONE | STOPPED, end | route |
| 401, 403 | ACCESS_DENIED | NONE | STOPPED, end | host |
| 429 | RATE_LIMITED | NONE | STOPPED, end | host |
| 404, 410 | NOT_FOUND | NONE | UNAVAILABLE, end | route |
| 204, 206 and every other status | UNEXPECTED_RESPONSE | NONE | STOPPED, end | host |
| DNS failure, no address, a malformed answer or more than 16 addresses | DNS_FAILED | NONE | STOPPED, end | — |
| Request time expired during DNS resolution, before connecting | DEADLINE_EXCEEDED | NONE | STOPPED, end | — |
| A non-public address anywhere in the answer | ADDRESS_REFUSED | NONE | STOPPED, end | host |
| Connection, TLS or read failure, or fewer bytes than declared | TRANSPORT_FAILED | PREFIX or NONE | UNKNOWN, end | host |

- **Custody handoff.** Only `200` target bodies with bytes, ending COMPLETE, UNVERIFIED_LENGTH, SIZE_STOP or TIME_STOP, go into the custody handoff, with their coverage. A known partial body is never labelled COMPLETE. Error bodies are kept in `raw/` as evidence with coverage NONE.
- **robots.txt.** A 200 response is parsed, with at most the first 512 KiB used; a disallowed target is not requested and receives a route stop. Other 4xx responses, apart from 401, 403 and 429, mean "no robots.txt" and impose no rules. An unread or timed-out robots.txt stops the attempt (`ROBOTS_UNRESOLVED`). Robots requests count against the reservation.
- **Status precedence:** UNKNOWN, STOPPED, UNAVAILABLE, PARTIAL, then COMPLETE. Receipts record exception type names only, never exception text.

## Result integrity and attempt states

`derive` is the only constructor of results. It works from the journal events a result accounts for, the verified receipts (each re-classified from its facts, with its body re-hashed) and the attempt's own input copies. `status` and `result` re-derive the result and compare it byte for byte with both its anchor and `result.json`. Any edit to status, consumption, retained bodies, custody handoff, stop findings or unexpected fields is reported as INCONSISTENT; nothing is repaired.

| State | Meaning | Anchor |
|---|---|---|
| `PRECLAIM_INCOMPLETE` | Initialisation stopped after the attempt directory appeared and before the claim; nothing was dispatched. The dispatch lock is kept as evidence | none yet |
| `NOT_STARTED` | Clean refusal before the claim | `ATTEMPT_REFUSED` in the journal (with its reason) |
| `INTERRUPTED` | Claimed, with no result | none yet |
| `RESULT_PENDING` | Anchored, but the crash came before `result.json` was written; reconciliation writes the bytes the anchor binds | journal or finalisation record |
| `COMPLETE`, `PARTIAL`, `UNAVAILABLE`, `STOPPED` | Finished | `ATTEMPT_FINISHED` in the journal |
| `UNKNOWN` or `NOT_STARTED` with `interrupted: true` | Reconciled by the owner | create-only `finalisation.json` |
| `INCONSISTENT` | A record differs from what the others imply | — |

`journal_head` in a result is the hash of the last journal event the result accounts for: the event immediately before `ATTEMPT_FINISHED` or `ATTEMPT_REFUSED`, or, for a finalised attempt, the last complete line. The anchor event itself binds the result's SHA-256.

## Interruption

If initialisation or the attempt ends abnormally, the locks stay and every further attempt is refused (`DISPATCH_LOCKED`). The owner:

1. Confirms no process is running and runs `finalise-interrupted <attempt> --no-attempt-running`. This:
   - writes a `finalisation.json` binding the exact result SHA-256 and the journal as found, including any incomplete tail, which is never truncated or rewritten;
   - then writes `result.json`: `UNKNOWN` for a claimed attempt, `NOT_STARTED` with `interrupted: true` for a pre-claim one;
   - records every stop finding the verified receipts imply, if a crash lost it. This covers 401, 403, 429, 5xx, redirects, 404, non-public addresses, transport failures and robots disallows, each with a deterministic stop id;
   - adds a host stop for each unfinished request.

   Nothing is re-sent. Repeating the command adds nothing and returns the same result; a crash during it can be completed by running it again.
2. Removes `attempts/<attempt>/attempt.lock` and `dispatch.lock` by hand. Software never removes them.

The campaign decides whether a new attempt, with a new id and reservation, is appropriate. Exactly-once remote execution is never claimed.

## Stops: software-enforced versus human-attested

- **Software-enforced:**
  - Machine-readable stop records are imported, and any URL in them gives a host-level stop.
  - At every run, each recorded input must still exist unchanged, and no new `*stop*.json` may have appeared in a declared `--from-dir`. Otherwise `STOP_SNAPSHOT_STALE` refuses the run until the snapshot is rebuilt and re-attested.
  - New findings in the register apply immediately.
  - Route stops match the exact request (normalised as above), never a URL prefix.
- **Human-attested:**
  - That the declared inputs and directories are the relevant stop records.
  - The scope of records that name no host.
  - Stops known only from reports.

  Software cannot check completeness beyond what it was given.

## Limits: strict versus soft

| Limit | Enforcement |
|---|---|
| Request count, total and per-response bytes, scope attempt and cumulative ceilings | Strict: checked before each request; byte reads are capped |
| Wall-clock budget before a request, `Crawl-delay` against the budget | Strict: an attempt never starts a request or sleep it cannot fit, and rechecks after a pacing sleep, so an overrunning sleep never leads to a request |
| Per-request time ceiling | Soft: it includes DNS resolution and is checked before connecting and between reads. A resolver call or one blocking read can overrun by up to its own duration or the socket timeout |
| Global pacing interval | Strict within one records base: measured from the ledger's last dispatch. Not coordinated across separate bases or machines |
| Searches, model calls, metered spend | Zero by construction: no such operation exists |

## Commands

```powershell
python -m src.research.source_v1 implementation
python -m src.research.source_v1 stops-snapshot --from-dir data/raw --input <file> [--attestation <file>] [--previous <snapshot>]
python -m src.research.source_v1 check <request.json>      # informational: the refusal run would record now
python -m src.research.source_v1 run <request.json>        # one attempt; real HTTPS
python -m src.research.source_v1 status <attempt-id>       # read-only re-derivation and verification
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
| `attempts/<id>/result.json`, `finalisation.json` | `SOURCE_ACTIVITY_RESULT_V001`; the owner's reconciliation record, when there is one |

## Interface consumed by Campaign Continuity V001

1. The campaign writes a request in the reserved `RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001` schema.
2. It may run `check`, but only for information.
3. It invokes `run`, then attaches `attempts/<id>/result.json` by path and hash.
4. It reads `status` for verification, state and lock holders.

The result fields are:

- **Identity:** `schema`, `request_sha256`, `attempt_id`, `campaign_id`, `branch_id`, `request_id`, `caller_ref`, `scope_sha256`.
- **Outcome:** `status` (`NOT_STARTED`, `COMPLETE`, `PARTIAL`, `UNAVAILABLE`, `STOPPED` or `UNKNOWN`), `reason`, `interrupted`.
- **Evidence:** `receipts[]` (SHA-256 of each receipt file), `retained[]`, `custody_handoff[]` (eligible 200 target bodies with exact Quarry route id, hash, bytes and coverage).
- **Findings and remaining work:** `stop_findings[]`, `not_attempted[]`, `unfinished_requests[]`.
- **Consumption:** requests, bytes and wall seconds as `{at_least, exact}`; searches and model calls zero; metered spend zero; subscription usage `NOT_USED`.
- **Binding:** `journal_head`, `journal_sha256` (finalised attempts), `implementation_sha256`.
- **Reserved, empty in V001:** `host_pending[]`, `field_support_proposals[]`.
- **Constants:** `exactly_once: false`, `authorises: []`.

The campaign never sums component reservations with its own allocation. Source V001 provides no reservation identifier beyond the ledger's `ATTEMPT_RESERVED` event for the attempt.

## Safety properties and assumptions

**Restricted offline tests** use fictional hosts, injected fake transports and a fake clock. Socket, DNS and process creation are denied by the runner and also patched in each test. Covered:

- Private, loopback, link-local, ULA, CGNAT, mapped, multicast, unspecified, mixed and malformed addresses.
- Refused redirects, DNS failures, and stopped hosts and routes, with exact route matching.
- 401, 403, 429, 404, 5xx, 204 and 206 responses.
- Non-identity encoding, close-delimited, chunked and contradictory framing, overlong and short bodies.
- Declared and streamed oversize, time and byte budgets, pacing and `Crawl-delay`.
- Duplicate and equivalent URLs, ambiguous routes, and duplicate and concurrent attempts.
- Pre-claim failure, interruption and record-only finalisation, including:
  - a 403 whose stop was lost in a crash;
  - a robots disallow lost the same way;
  - a crash during reconciliation itself;
  - idempotent repetition.
- Altered and consistently re-chained forgeries of results, receipts, bodies, journals and finalised results, including unexpected fields.
- Scope violations, Quarry route stops, cumulative scope ceilings, stale snapshots, robots.txt cases and stop attestation rules.

**Loopback transport tests** run the real `HttpsTransport` and `fetch` against a local TLS server on `127.0.0.1`, with fictional test certificates. DNS is denied and every connection is asserted to target loopback. Covered:

- Request framing: request line, Host, User-Agent, identity encoding and no other headers.
- Content-Length, chunked and close-delimited bodies.
- Short Content-Length, truncated chunks and a connection reset.
- 206, 204, gzip, TE plus CL conflict and an unfollowed 302.
- Certificate hostname mismatch and an untrusted CA, both refused before any request is sent.
- Streamed and declared byte ceilings.

**Assumptions, not established by these tests:**

- No real network or real resolver has been used. Public-CA trust stores, real servers' TLS behaviour, IPv6 and proxies or middleboxes are untested.
- The DNS answer is validated and pinned once per request. Rebinding between the check and the connection is prevented by connecting to the pinned address, not by resolving again.
- Machine stop reconciliation finds URLs anywhere in a stop record and stops their hosts, so it can over-block. Completeness of human-attested stops rests on the attester.
- A trusted local filesystem and reviewed code; this is not an OS sandbox. A party able to rewrite every record consistently (journal, receipts, bodies, register and result) is out of scope. Locks and fsync give crash evidence, not exactly-once execution.
- The `ResearchOS-SourceRetrieval` user-agent is honest but carries no contact identity. Site terms beyond robots.txt rest on the owner's `access_terms_reviewed` statement.

**Not in this milestone:** search, Codex or any model call, OCR or extraction, field proposals, host tiers B and C, host amendments, Quarry SUPPLY V002, campaign scheduling or attachment, and any live retrieval.
