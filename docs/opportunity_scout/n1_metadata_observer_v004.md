# N1 metadata observer V004: prospective pair-boundary heartbeat correction

Offline engineering only, based on reviewed main `43ed881e`. NOT_RUN. This is
`SCOUT_N1_PROCESS_OBSERVER_V004`, distinct from the frozen scientific Scout V004
protocol. No live observation or native N1 execution is authorised by this document,
its tests, a PR or a merge. The V003 approval was consumed by its STOP.

## Evidence and bounded diagnosis

The original V003 stream (133,443 bytes, SHA256
`33d3718dd6bfbc095b0cb6659d7be77f16d0b0e45b2c0080bf1f29f59f895ad3`)
contains a 10.150-second heartbeat gap: records 176 (34.868s) and 245 (45.018s).
Between them are 34 process events and 34 adjacent exact ACKs. The first 11 pairs
account for 9.941 seconds from the preceding heartbeat; the remaining 23 pairs
finish in 206ms, followed by the heartbeat 3ms later. No adjacent record gap exceeds
795ms. The stream has 324 chained records; all 146 process events have ACKs.
The reader stopped before its baseline completed; no sentinel/cooldown was reached.

The whole-batch-before-heartbeat scheduling vulnerability is demonstrated. The
relative contribution of synchronous flush, PowerShell work, queue operations,
scheduling or WMI backlog is unknown. Record timestamps precede serialization and
flush, so their differences are not isolated disk timings. WMI TIME_CREATED values
are neither queried process creation identities nor receipt/coverage certificates.

V001/V002/V003 original evidence remains private and immutable. Their original
sources in `n1_preflight/` remain byte-identical to reviewed main. Nothing migrates,
repairs or reinterprets a historical stream.

## Small prospective implementation

`src/research/opportunity_scout/n1_preflight_v004/` contains:

- `watch.ps1`: the existing watcher architecture with heartbeat/deadline checks
  between complete event/ACK pairs and on empty iterations. It reuses the unchanged
  exact-object queue helper at `../n1_preflight/queue.ps1`.
- `monitor.py`: an exact copy of the V003 reader with only schema and fixed-path
  substitutions. Duplication deliberately keeps the historical implementation and
  its global version/path constants unchanged; tests pin that relationship.
- `__init__.py`: package marker only.

The sole new path is `.research/opportunity_scout/n1-admin-observer-v004/`.
The reader refuses V001/V002/V003 headers and directories before any claim/launch.
There is no fallback, alternative path, retry or recovery interface.

The watcher checks monotonic deadlines before/after queue retrieval, process
persistence, exact-object acknowledgement, ACK persistence, subscription queries
and final shutdown work. The next heartbeat remains nominally due after one
second; the maximum remains five seconds. A heartbeat never splits an event/ACK
pair. A failed or overdue process write is not acknowledged. A write failure may
leave an incomplete pair; that evidence is retained and cannot pass the reader.

Heartbeat deadlines remain anchored to the actual recorded heartbeat timestamp.
After writing a new heartbeat, the OLD deadline is checked before changing that
anchor, and the new write's own duration is checked. Neither a late heartbeat nor
a post-flush reset can repair an expired window. Blocking calls remain cooperative:
an overrun is detected once control returns, not preempted by a hard real-time timer.

A poisoned-write flag prevents appending a purported chained ERROR/recovery record
after a failed write/flush, which may have left partial or unconfirmed bytes.
Deadline failures after successful persistence can append an explicit ERROR.
Either case is STOP; no valid successful END is manufactured. Shutdown unsubscribes
before draining as before; it cannot emit a subscriptions-present heartbeat after
unsubscribe. Its remaining drain must finish inside the same deadline or STOP.

The seven-path metadata scope, normal-user reader, strict Claude rejection,
60-second baseline and post-exit cooldown, five-second sampling/heartbeat limits,
160/360-second reader/producer loops, two-second sentinel wait, two-MiB recording
and 10,000-event queue checks, synchronous persistence and ACK rules are unchanged.

## Offline verification, not live assurance

The Windows fixture extracts the original loop iteration or prospective functions
only, supplies fictional PowerShell queue objects, and uses a virtual clock. It
never executes watcher startup, WMI subscriptions, account sampling or a sentinel.
Actual JSON framing, hashing, temporary-file flushes and exact-object queue removal
are exercised. All event identifiers deliberately collide numerically.

With 34 events and 150ms charged per durable record, the unchanged V003 iteration
produces a 10.200-second heartbeat gap. The corrected iteration's maximum is 1.200
seconds with all 34 events and ACKs retained in order. These are fictional timing
results, not performance measurements or a claim to reproduce the unknown OS cause.

Seventeen Windows scenarios cover before/after burst timing, empty queue, slow
process/ACK/heartbeat writes, a first slow heartbeat, late queue/subscription calls,
missing subscription, overflow, malformed event, fictional Claude, failed
persistence, and successful/overdue shutdown (including END persistence). Python checks the resulting original
fixture bytes, chains, exact adjacent ACKs and strict reader outcomes. Five portable
tests pin historical sources, enforce version isolation, replay the V003 timing
failure, reuse 16 applicable unchanged reader regressions (including virtual full
baseline/cooldown), and confirm native launch remains disabled.

Timely heartbeats show control-loop progress only. They do not prove currentness of
queued events, lossless WMI delivery, complete inventory/ancestry, effective N1
containment, account identity or subscription isolation. Backlog is not erased,
coalesced or retrospectively approved by heartbeats. Coverage stays uncertified.
The existing N1 admission code still references its V003 preparation contract;
this change does not adapt or admit a V004 receipt.

As with the existing procedure, a reader receipt alone is not final evaluation:
wait for producer completion and independently audit the final original stream.
For example, an END write that returns after its deadline is followed by ERROR;
the final stream is refused, including any trailing record after END. The reader
may have seen END while the producer was still blocked in persistence. Do not
classify an in-flight stream/receipt as PASS or infer durable completion from it.

## Future operational boundary

Review the exact source hashes and full CI results in the focused draft PR first.
Any later observation needs a fresh exact owner approval naming this prospective
version, its fixed unused path, reviewed checkout and source hashes. Only then use
the existing two-terminal procedure with the V004 watcher/module substitutions,
under the same account and unchanged privacy/resource/quiet-window requirements.
No operational commands are authorised here. Any STOP consumes that future attempt
and preserves its original directory/claims without retry. Native N1 remains
disabled and needs its separate evidence and authorisation gates.
