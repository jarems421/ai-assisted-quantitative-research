# Campaign Continuity V001

One persistent campaign groups exact hypothesis versions and references existing
offline operator runs. It does not run those activities, call a provider, acquire
evidence, write human decisions or change research gates. Domain records remain
the source of truth. This is a continuity spine, not an end-to-end research runner.

## Minimal operator example

Use the existing native Scout `card` output's `card_sha256` for each exact version.
The archive and completed runs below must already exist. Values in angle brackets
are placeholders; these commands neither generate cards nor run the operator.
Execute from the repository root:

```powershell
python -m src.research.campaign_v1 create CMP-001 --api-allocation-micro-usd 1000000
python -m src.research.campaign_v1 add-branch CMP-001 B1 --archive <archive> --idea <IDEA-id-1> --version 1 --card-sha256 <exact-card-hash-1>
python -m src.research.campaign_v1 add-branch CMP-001 B2 --archive <archive> --idea <IDEA-id-2> --version 1 --card-sha256 <exact-card-hash-2>
python -m src.research.campaign_v1 attach CMP-001 B1 A1 --run <completed-operator-run-directory-1>
python -m src.research.campaign_v1 attach CMP-001 B2 A2 --run <completed-operator-run-directory-2>
python -m src.research.campaign_v1 status CMP-001
python -m src.research.campaign_v1 reconcile CMP-001 --branch B1
python -m src.research.campaign_v1 final CMP-001 --json
```

`--base <directory>` precedes the command; the default is the checkout's ignored
`.research/`. The base's parent must exist. Records live under
`<base>/campaign-v1/<id>/`: immutable `campaign.json`, append-only `events.jsonl`,
and an exclusive `campaign.lock` while writing. A non-Git temporary base is useful
for synthetic fixtures. No campaign/private artifact is committed.

`continue` is an alias for **reference reconciliation only**, not native operator
`continue`. It observes a completed invocation already present on disk. `status`
and `final` are read-only, deterministic views with no clock dependence; `final`
does not close or approve the campaign. Native reports and original files are
never regenerated or repaired. No source or provider operation is exposed.

## Records and integrity

Contract: `RESEARCH_OS_CAMPAIGN_V001`. Branches pin archive, native Scout card ID,
positive version and canonical card SHA-256, plus the admitted Scout journal
prefix. Current Scout state is replayed using Scout itself. Revised card versions
require separate branches and never inherit approvals. A later review/stop makes
an old native Scout view stale, even if the card bytes have not changed.
Original custody hashes and working-copy journal heads are checked separately:
native human reviews may advance the working copy without mutating its original.
They must be re-evaluated by the native operator before campaign reconciliation.
`scout_route` and `scout_handoff_eligible` explicitly describe the registered
original; working-copy review progress is represented by validated native stages.

Events are `CREATED`, `BRANCH_ADDED`, `ACTIVITY_ATTACHED`, `ACTIVITY_OBSERVED`.
They carry sequence, timestamp, previous hash and canonical event hash; writes are
exclusive/append-only, flushed and fsynced. A creation interrupted between the
manifest and journal stays incomplete. Never recreate it in place. A truncated
event or stale lock is retained and refused for mutation; a human must reconcile
the interruption. No automatic lock deletion or tail repair exists. This assumes
a trusted local filesystem and reviewed Python; it is not an OS sandbox or
authenticated evidence of execution.

The native offline operator has no separate run receipt. Its hash-chained
`INVOCATION_FINISHED` event, reproducible retained report and explicitly hashed
run artifacts form the completion reference. Attach checks native profile,
archive/card/version/hash, completed integrity stage, report equality with native
journal rendering, linked-path refusal and artifact hashes. References retain
run location, event count/head, exact completion event, code binding and artifact
hashes. They contain no source observations, critic judgments or experiment state.
Only metadata and explicit operator artifact references are read; model captures
and private raw directories are not scanned. Native component custody contracts
remain authoritative; this does not independently authenticate source originals.

Repeated identical attachments and reconciliations append nothing. Reusing an
activity ID for another branch/run, attaching the same run twice or changing an
artifact is refused. If native events advance, status asks for reconciliation;
reconciliation verifies the old prefix/artifacts and records only the new native
completion reference. A crash between observations leaves the earlier observation
valid and the remaining one pending. Unfinished native work is never replayed.

The manifest pins campaign source hashes and the native operator's implementation
closure/profile binding. Code changes leave status readable with explicit drift,
but mutations are refused. Use the pinned environment, or separately create a new
campaign referencing eligible retained activity. There is no drift-acceptance flag
and no campaign operation that overrides a native binding, source stop or approval.

The projection reports branch stage, execution state, current Scout route and
handoff eligibility, blockers, pending human action groups, exact references and
next eligible action. Independent branches retain independent failures. This
offline profile does not establish an empirical outcome: `research_outcome` stays
null. A successful invocation or human M decision is not an empirical finding.
Human action groups are not an exhaustive count of individual records.

Multiple independently attached native runs have no authoritative supersession
relationship. Their individual validated stages, execution states, blockers and
pending decisions are retained in `activities[].state` and the Markdown report.
The branch has `stage: null`, `research_outcome: null` and
`execution_state: AMBIGUOUS_NATIVE_REFERENCE`; its next action is to inspect the
individual references. Attachment order, timestamps and apparent stage depth never
choose a winner, even if summaries happen to agree. Activity IDs are sorted only
for deterministic presentation. If any reference needs reconciliation, that
integrity refusal takes precedence; the other activity states remain visible.
Reconciliation observes native completions and does not resolve this ambiguity
or replay work. Single-activity summaries retain their existing behavior.

## Budgets

The optional integer micro-USD campaign allocation is informational in this
milestone: there are no reservations, spending operations or spend authority.
Native component budgets/claims remain unchanged. Status lists each Forge batch
once, by native batch ID and batch-record hash, with associated branch/archive
references. A repeated batch ID with conflicting content is refused. Copied
archives with the same batch identity remain one batch. No shared batch cost is
multiplied by card count. Allocation is never added to native charges, and unknown
component charges remain UNKNOWN. Actual budget admission belongs to a future
separately reviewed effectful integration.

## Reserved source-component boundary V001

`status.branches[].provisional_source.request_contract` advertises
`RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001`. It is a **disabled integration
descriptor**, not an executable request or approval. No request export/import,
dispatcher, source plan, receipt finaliser or source implementation is provided.
Claude's source-discovery work remains independent and unchanged.

A future independently reviewed consumer must bind:

| Field group | Required meaning |
|---|---|
| Identity | Schema version, campaign/branch, archive/card ID/version/hash; logical request/attempt identity |
| Decisive question | Exact card next-step question and required predictor/outcome, units, denominator, population, period and join; no unsupported dataset claim |
| Authority | Real external owner scope reference/hash, permitted operations/transmission, validity and human gates; no assistant-authored approval |
| Stops | Independently reconciled historical host/route/equivalent-route restrictions with provenance; unresolved/unclear scope blocks dispatch |
| Resources | Component reservation ID, aggregate campaign allocation reference, starts/bytes/time/provider ceilings; no double-counting batch costs |
| Provenance | Implementation/protocol, immutable input/output roots/hashes, original versus extraction, coverage/missingness and correction/version references |
| Result | Native durable attempt/receipt reference; NOT_STARTED, UNKNOWN, PARTIAL, UNAVAILABLE and STOPPED remain distinct; no claim of exactly-once remote execution |

**INCUBATE is compatible with a separately authorised provisional investigation.**
It does not require or fabricate Scout READY. Provisional source work does not
create an approved Scout-to-Anvil handoff, Discovery candidate, M/H pass or study
permission. Official Scout continuation retains its native current-version
feasibility/READY and human crosswalk requirements. Both tracks preserve every
source stop. Until reconciled with Claude's design and separately authorised,
`implemented` and `dispatch_eligible` remain false for every branch.

## Validation

`python -m unittest tests.test_campaign_continuity_v1 -v` uses two fictional cards,
real synthetic offline operator invocations and no external transport. It checks
distinct blockers, exact references, batch deduplication, duplicate activities,
stale artifacts/reviews, journal/report/manifest tampering, changed code,
interrupted observation recovery and denied network/process/foreign writes.
The module is admitted to the restricted offline inventory for Windows/Linux CI.
No passing fixture creates real human authority or research progress.
