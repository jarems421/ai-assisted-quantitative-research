# N1 admission, STOP and cancellation: narrow offline audit

2026-10-23; inspected merged main `14dfbe63205fb51bb3efef6153e338fa9420583e`
(PRs #20 and #21). **N1 remains blocked; native launch remains disabled.**
This is an engineering assessment, not owner approval or live assurance.

## Existing implementation and its evidence

| Requirement | What exists | Evidence limit / remaining gate |
|---|---|---|
| Exact content and consent | `n1_collector/binding.py` checks unchanged N1 proposal/request/system, collector sources, dependencies, binary, argv/environment, sterile/disjoint paths, UUIDs and explicit seed-hash consent with retained false hosting flags. | Native mode is review-only. Owner identity and external review hashes are assertions, not authenticated account facts. Invalid consent refuses before consumption/spawn. |
| Runtime support | `readiness.runtime_review` requires every named control supported, exact runtime/resource bindings and installed-build evidence references; documentation-only and fixture evidence are refused. | Fictional contract tests establish validation, not truth of an installed-build review. Unsupported/unknown controls must block; no flag removal/fallback. |
| Observation plan | `readiness.observation_plan` fixes seven metadata paths, 60-second baseline/cooldown, maximum five-second gaps, process/managed-policy prerequisites and zero-drift stops. | A prospective plan explicitly cannot claim observations. `review_plan` is read-only and refuses stale/held locks and consumed reservations. |
| V003 preparation | `n1_preflight` checks chain/sequence/ACKs, subscription heartbeats, initial processes and later starts/exits, unchanged original-baseline metadata, sentinel start/exit/parent/time, END and readback. Any visible `claude`/`claude.exe` is refused, including an editor child. | Reader timing/metadata tests are virtual. Eight Windows tests execute queue/persistence/shutdown functions with fictional events/timers, never the live WMI watcher. Successful V003 means local preparation only: receipt retains `N1_admission:false`, coverage uncertified and account UNKNOWN. |
| Single-use capture | Existing `Capture` exclusively locks a separate registry and durably claims the reservation before spawn; raw bytes precede witnessed index records. Race, failed-spawn, crash, storage-failure and reuse checks already exist. | Real local Python fixtures only. Consumed claims persist; STOP/interruption retains the registry lock. Invalid input refused before consumption is not a launched attempt. No resume, reset, retry or lock recovery. |
| STOP/cancellation | Existing collector has 600-second watchdog, 12-MiB recording trigger, reads <=64 KiB, five-second escalation and <=30-second drain. Pipe/storage/interruption and incomplete cleanup retain evidence. | No connection from live account/process observations to this loop exists. Local terminate/job-call results do not establish remote-model cancellation. Windows job assignment is post-spawn, best effort; descendants before assignment remain UNKNOWN. |

`LOCAL_CAPTURE_COMPLETE` describes byte capture, not model success: a nonzero
exit can have complete bytes and still consumes its reservation. The successful
local-capture lock release never deletes the consumed claim. Native acceptance
must separately classify runtime/auth/content/usage failures; it does not exist yet.

Historical V001 failed at numeric event acknowledgement and lacks END. V002
correctly refused an initial Claude process before sentinel launch. Neither
established a baseline/cooldown or account identity. This audit read their tracked
reports, not private historical streams, and changes none of their evidence.

## One demonstrated correction

The V003 reader measured cooldown from the loop timestamp **before** sentinel
spawn/wait. Independent fictional 1.75-second spawn and wait delays each reproduced
a success after only **58.25 seconds following child completion**. Start that clock
with fresh monotonic time after `child.wait()` returns. Existing virtual end-to-end
tests now assert >=60 seconds before launch and >=60 seconds between child
completion and stop request, including both delay cases. Both cases failed before
the correction and pass afterwards. No gate, schema, path or production limit is
relaxed. V003's changed reader bytes need review before any future approved window.

## The missing connection, bounded precisely

There is **no implemented V003-receipt-to-single-use-N1 admission interface**.
`quiet_window_review_sha256` alone is an opaque reference; `launch_native()` always
refuses and `collect_fixture()` accepts only the fixed Python fixture. Supplying a
successful receipt cannot bypass either boundary.

The minimum future connection must reuse `Capture`, its registry and the current
byte spool. Its review/consent binding must name the exact V003 receipt bytes,
event audit head/count/bytes, metadata-log hash/count and reviewed observer source
identity, together with the exact runtime/account/policy reviews and sole N1
reservation/session/capture. Check those originals rather than trusting a PASS
field. These hashes detect consistency, not factual authenticity or local rollback.
Recheck mutable bindings immediately before the sole spawn. The existing durable
claim must precede it; failure/cancellation after consumption never reopens it.

An ended preparation window is **not** fresh launch-time coverage. The connection
still needs a new per-command >=60-second baseline, active monitoring, post-drain
child-absence check and >=60-second cooldown, comparing the original baseline
throughout with gaps <=5 seconds. V003's 160-second reader/360-second producer
cannot cover a possible 600-second N1 plus surrounding windows/cleanup unchanged.
The preparation reader also rejects the intended Claude process. Keep that strict
preparation rule; any future active-window exception must identify only the exact
collector-owned process by actual PID/creation/parent evidence, with every other
Claude rejected. Never infer coverage from an empty list or heartbeat alone.

Loss/unknown coverage, metadata drift including research files, unexpected Claude,
managed policy present/unknown, changed bindings, unsupported controls, invalid
consent or stale reservations must refuse launch or signal the existing
cancellation path during capture. No post-hoc whitelist or automatic recovery.
Test this finite connection with harmless fixtures once the approved observation
mechanism and runtime facts are available. This audit adds no speculative adapter,
replacement launcher, journal, monitor framework or native enable switch.

## External/live gates and work that is unnecessary

Actual Windows event delivery/access, sentinel observation, account provenance,
managed-policy presence and installed runtime/control support remain external
evidence. Obtain them only under their separately bounded owner authority; do not
read credentials to resolve ambiguity. A sentinel cannot certify lossless WMI.
The owner must accept disclosed coverage/containment, filesystem, privacy,
retention, quota and unmetered-work limits, or N1 remains blocked.

Native event/ID/usage/continuation semantics require the authorised N1 bytes and
subsequent offline interpretation. No new parser, live token meter, hypothesis
generator, diagnostic model call or major Scout project is needed before capturing
those bytes. R3 stays 60,000 planning / 120,000 annotation / proposed 200,000
best-effort emergency, candidate 32,768 per response; bytes are not tokens or money.
Provider-request completeness, charges and remote cancellation remain UNKNOWN
absent evidence; an uninterrupted N1 leaves cancellation unobserved.

Further offline engineering **is necessary only for the existing narrow admission/
STOP connection before native execution**. It cannot be replaced by owner settings
or another readiness document. Its final wiring depends on the external evidence;
no broader infrastructure work is justified now.

## Verification and shortest path

Local verification and exact-head GitHub workflow results are recorded in the
draft PR and final delivery. Existing workflow selections already exercise the
changed virtual test on Windows/Linux and the Windows process fixtures; neither
workflow nor test inventory needs changing (two subcases extend one declared test).
`hosted_acceptance_v001.prepare --check` passes unchanged. Frozen V004/N1 proposal
bytes, top-level Scout modules, Jev, AI Critic, Graph R4 and scientific protocols
are untouched. No live observer, Claude/auth command, account-content read,
existing-process termination, owner registration or research slot was performed.

1. Owner reviews this small correction and its CI; any merge is the owner's act.
2. Separately authorise one fresh V003 preparation window; arrange development
   inactivity through normal controls; preserve any failure without retry.
3. Obtain the separately authorised account/policy and installed-runtime evidence.
   Reuse recorded setup facts, verify current identities and STOP on unknowns.
4. Finish and independently review only the collector's admission/STOP connection
   above, with harmless failure/cancellation fixtures and full-window bounds.
5. Owner registers exact final hashes, sole reservation/paths, explicit retained-
   false seed exception and privacy/resource/retention decisions, and separately
   authorises execution. Fresh immediate monitoring must still pass.
6. Capture N1 once: exact request then EOF, immutable private byte spools, no repair,
   retry, fallback or additional parent. Preserve STOP/consumption on failure.
   Then STOP for offline interpretation; no scientific dispatch follows.
