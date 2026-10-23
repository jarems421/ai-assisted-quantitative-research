# PR #15 V002 observer integration review

Review date: 2026-10-23. Repaired main `0f09da9` (owner-merged PR #18) was
integrated by merge commit `82d8238`, preserving the original PR #15 head
`790efd3945bb9ccd3e79e702afee8ad662ae6eae`. No rebase or force push.

This is a fresh Codex engineering assessment of the producer, normal-user reader
and queue implementation, separate from the earlier implementation narrative.
It is not an independent human security certification. No elevated watcher,
WMI subscription, actual account sampler, Claude/auth command, owner consent or
native N1 launch was exercised. **V002 has not been live-validated.** Graph R4
remains paused and NOT_RUN; this work authorises no research or hosted generation.

## Finding and correction

Before this integration, `watch.ps1` checked `stop.request` before draining its
queue, wrote END, then acknowledged remaining owned objects in `finally` without
recording them. An already-visible Claude START could disappear from an otherwise
accepted stream. The reader rejects recorded Claude activity but cannot recover
an event discarded by its producer. The existing WMI limitations did not justify
this deliberate omission.

`Complete-ScoutObservation` now unregisters both owned subscriptions with errors
fatal, drains the visible owned queue through the existing persist/exact-object
ACK path, checks for remaining visible arrivals, and only then writes END.
Failure cleanup never acknowledges unpersisted objects. An unsubscribe, write,
missing-object, queue-limit or visible-late-arrival failure cannot complete this
path. A failure after removal but before persisting its ACK leaves an incomplete
stream which the reader rejects; no recovery or replay is invented.

Four additional Windows regressions exercise production shutdown functions with
inert local timer subscriptions and synthetic queued events: pending colliding
START/EXIT objects precede END; a fictional queued Claude START is persisted and
rejected by the Python audit; failed persistence retains both pending objects
and no END; missing subscription similarly fails before removal or END. Unrelated
collision peers remain untouched. These tests never execute the watcher body.

## Reviewed properties and limits

- **Permissions and field scope.** The producer explicitly requires Administrator
  and selects process name, PID, parent PID and creation/event timestamps. It
  reads no command line, process environment or credential contents and launches
  no child. The reader refuses elevation before creating a claim or launching its
  byte-checked, harmless Python sentinel. Its seven-path account helper uses
  metadata only; all such APIs are mocked in this review's tests.
- **Exact-object acknowledgement.** Queue snapshot/removal locks `SyncRoot`;
  `ReferenceEquals` and `RemoveAt` identify one queued object. Numeric identifiers
  may collide and are never deduplication keys. Process bytes are flushed/fsynced
  before removal, then a matching sequence-linked ACK is persisted. Missing
  objects and persistence errors fail closed. The shutdown correction uses this
  same path, rather than a second acknowledgement implementation.
- **Failure and stale claims.** CreateNew/`xb` claims and outputs refuse reuse,
  including failed runs. There is no reset or automatic retry. Reader checks
  include path/link refusal, file identity and hardlink count, monotonic observed
  size, sequence/hash framing, event/ACK pairing and full final readback. Receipt
  creation can itself fail; absence of a receipt is never approval. The elevated
  writer and writable workspace require the same owner's trusted local machine;
  hash chaining does not authenticate a producer against that owner or an
  administrator. Path prechecks are not an OS security boundary against hostile
  concurrent filesystem replacement.
- **Event loss and timing.** Unregister-then-drain closes the visible shutdown
  omission. It does not certify WMI delivery completeness or prevent every
  in-flight delivery race after the final queue check. Heartbeats prove visible
  subscription presence only. One sentinel cannot establish every process's
  identity/ancestry, detect renamed processes or certify account identity.
  Producer checks a 360-second loop, a two-MiB crossing-record trigger and a
  10,000-event queue bound. Reader uses a 160-second loop, five-second sampling,
  heartbeat and stop limits, two-second child wait, and 60-second baseline and
  cooldown. These are cooperative checks around OS calls and fsync, not hard
  real-time interruption of blocked OS operations. N1 admission stays blocked.

## Historical evidence and validation scope

The V001 implementation remains in commit
`cfe7c2930310eb527e684a5780f033a2ce64871a`. The existing V001/V002 reports remain
unchanged: V001 stopped after 3,390 ms with INVALID_EVENT_IDENTIFIER; its 18
contiguous hash-valid records lack END. Its recorded 37,992-byte SHA256 is
`de25d5076369ce6addde45f7dd7efb28ccea89b2b06eea726121629b89c32e52`.
This review did not inspect or change that ignored private directory. Exact
retrospective collision peers and historical writer attribution remain UNKNOWN.
V002 uses a separate directory/schema and rejects V001 headers. No success is
appended to the failed observer or inferred from fixture success.

The inventory additions were reviewed module by module: 15 portable fictional
reader tests use the guarded Scout runner on Windows/Linux; eight native queue
tests use the process runner on Windows only, selected explicitly in both
workflows. Linux excludes that native module rather than counting skips or
claiming Windows coverage. Existing Graph inventory, scientific logic, collector,
N1 package and V003/R2/R3 inputs are unchanged relative to repaired main.

Final acceptance requires the complete guarded public, Scout and additional
suites, selected OS guard tests, six cross-process lock tests, all 25 native
collector tests and eight native queue tests. Expected workflow totals are 950
Windows, 917 Linux and 730 original public workflow, with zero unittest skips.
Actual exact-head run links, counts and the final merge recommendation are
recorded in PR #15 after CI completes; expected counts here are not a CI pass.

## Remaining owner decisions and work

1. Review the final PR #15 diff and exact-head checks and decide whether to merge
   it with a merge commit. The assistant does not merge it. PR #18's inventory
   repair is already owner-merged. An offline-preparation merge GO does not
   authorise an observation.
2. Separately authorise and start a fresh V002 metadata-only preparation window,
   after reviewing the exact privileged watcher/queue bytes and same-owner
   environment. Retain the failed V001 claim/evidence; refuse any stale V002
   claim. Obtain actual sentinel/event/metadata evidence. No auth/model command
   belongs to that window, and success establishes local preparation only.
3. Resolve actual account/policy presence and installed-runtime/control evidence
   under a separately bounded administrative authorisation. Review already
   recorded setup facts rather than repeat installation discovery unless changed;
   verify current hashes. No credential-content inspection or implicit
   help/version/auth allowance follows from this review.
4. Commission and independently review the still-disabled live admission and
   cancellation connection and N1-only adapter, reusing the existing collector.
   Exercise harmless fixtures, immediate baseline/start/ancestry coverage,
   STOP/cooldown and mutable-binding checks. This is an existing engineering
   blocker, not something an owner setting can bypass; a metadata-preparation
   receipt is not the launch connection. No replacement collector is needed.
5. Owner alone supplies exact runtime/model/package hashes, sole reservation and
   paths, privacy/retention/resource decisions, and named/date-stamped consent
   covering both seed IDs/text hashes and the N1-only hosted-use exception while
   retaining `approved_for_hosted_use:false`. This integration fills none of
   those fields. See the existing owner checklist for the detailed package.
6. Only a later explicit execution authority may permit the sole bounded native
   N1 capture: unchanged request once, no repair/retry/fallback or scientific
   dispatch, then STOP for offline interpretation. Provider behavior, attributable
   charges and remote cancellation remain unproved until evidenced. Until those
   blockers are resolved, actual N1 execution is **NO-GO** and `launch_native`
   continues to refuse.
