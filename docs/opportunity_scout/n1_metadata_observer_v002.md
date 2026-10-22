# Metadata observer V002: exact-object queue acknowledgement

Preparation only. **HOSTED_READINESS_BLOCKED**; no Claude/authentication launcher,
N1 activation or scientific request is added. This is a prospective correction to
the local metadata helper, not a repair/retry of any consumed scientific attempt.
The existing limited account-check authorisation does not become N1 consent.

## Preserved V001 failure

The owner-started V001 watcher stopped after 3,390 ms with an `ArgumentException`,
`INVALID_EVENT_IDENTIFIER,Microsoft.PowerShell.Commands.RemoveEventCommand`.
The retained stream has 18 contiguous, hash-valid records and no END: HEADER,
SNAPSHOT, heartbeats, process events and ERROR. The original 37,992 bytes have
SHA256 `de25d5076369ce6addde45f7dd7efb28ccea89b2b06eea726121629b89c32e52`.
Keep `.research/opportunity_scout/n1-admin-observer-v001/`, its claim and its
failure unchanged. Do not remove its claim, append a success, or run the reader
against it. V001 implementation is retained in Git commit
`cfe7c2930310eb527e684a5780f033a2ce64871a`.

This was an event-queue acknowledgement failure. No authentication command was
attempted, no native N1 observation occurred and zero scientific slots were used.
It establishes nothing about which subscription account would be used.

## Diagnosis and bounded fix

The V001 implementation assumed PowerShell's numeric `EventIdentifier` uniquely
identified a queued object. A local, unprivileged experiment with two .NET timers
reproduced a duplicate numeric identifier and the same `INVALID_EVENT_IDENTIFIER`
failure after 13 successful removals. Sequential synthetic events did not fail.
Neither experiment used WMI, account files or a model. Microsoft's current
[event manager source](https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/EventManager.cs)
uses an incrementing counter; its
[Remove-Event implementation](https://github.com/PowerShell/PowerShell/blob/master/src/Microsoft.PowerShell.Commands.Utility/commands/utility/RemoveEventCommand.cs)
removes every matching numeric ID. Thus one removal can consume a collision peer,
and a subsequent removal fails. This explains the reproduced mechanism; V001 did
not record queue identifiers, so the exact colliding original objects cannot be
identified retrospectively. Do not claim that level of forensic attribution.

V002 adds `n1_preflight/queue.ps1`. Snapshotting and acknowledgement use the queue's
`SyncRoot`; acknowledgement finds the exact `PSEventArgs` object by reference and
removes only its position. No numeric-ID deduplication or catch-and-ignore fallback
exists. Missing objects remain a hard failure. The producer first writes/fsyncs
the process record, then removes that object, then writes/fsyncs a `QUEUE_ACK`
referencing that precise record sequence. Each local queue identifier is retained
as metadata even if another event has the same number. It is not a provider
request ID or generation ID.

The V002 reader requires one correct ACK per persisted process event and rejects
missing, unmatched or repeated ACKs. It refuses V001 headers; it never converts
the failed V001 stream to V002. The new directory is exclusively
`.research/opportunity_scout/n1-admin-observer-v002/`; no live V002 observation is
started by the fix or its tests. Existing single-use claims, metadata sampling,
timing/size bounds, normal-user reader and elevated metadata-only watcher roles
remain. Historical writer attribution stays UNKNOWN. WMI delivery completeness,
remote/account identity and full N1 admission remain unproved.

## Regression evidence

- Fifteen fictional-stream/virtual-time unit tests include duplicate queue IDs,
  complete per-event ACKs, wrong/missing/repeated ACKs, refusal of V001, prior
  metadata/heartbeat/integrity stops and exact byte readback.
- Four Windows process tests use a fixed local Python fixture, which starts
  Windows PowerShell with only extracted production functions and synthetic
  in-memory events. Deterministic duplicate IDs retain both owned objects and an
  unrelated collision peer; two concurrent timers are acknowledged one visible
  object at a time; failed persistence leaves the event queued; a missing exact
  object fails without consuming its peer. All four passed locally. No WMI
  subscription, account access, privilege escalation or Claude command occurs in
  those tests. Real producer hashes and reader audits are exercised.
- The existing GitHub N1 process step now includes these four tests. Their success
  is queue-regression evidence, not a native WMI or Claude compatibility claim.

No N1 package, V003/R2/R3, card schema, previous collector or Graph source changed.
Exact proposal checking and the full relevant suites remain required before
delivery; a CI result is only claimed when actually observed.

## Proposed next local observation

V002 requires a new, explicit owner-started metadata observation; do not restart
V001, remove either claim or start a model. This command creates the V002 files
only. In the same owner's administrator PowerShell:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\Users\runni\quant-opportunity-scout-v1\src\research\opportunity_scout\n1_preflight\watch.ps1"
```

The execution-policy bypass applies solely to that child PowerShell process. It
changes no persistent setting. Review local privileged code before running it.
Leave the window open when `OBSERVER_STARTED_METADATA_ONLY` appears and report
promptly; the assistant can run the already-authorised normal-user metadata-only
reader. Do not run Claude elevated. This proposed observation, even if successful,
does not perform `auth status`, establish its command-specific quiet window,
inspect credential contents, approve fictional seeds or unblock N1 generation.
