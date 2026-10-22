# N1 follow-up V002: review-only launch package

**HOSTED_READINESS_BLOCKED / native launch disabled.** This updates still-draft PR #11; it does not treat that PR as merged. Review baseline: `367ee833f7a8b361b6519e578b964e6d979d1ee5`, based on fetched main `4ace618c6a68d525407417dc45b93f0ae400090f`. At inspection PR #11 was OPEN/draft with successful CI run `39817355611`; PR #10 was merged at that main commit. No merge, native invocation, account/configuration inspection or hosted request is authorised or performed. This is the implementing agent's engineering assessment, not an independent certification.

## Corrections found by source review and adversarial fixtures

1. The registry could overlap the empty working directory and dirty it during consumption. Require disjoint registry/capture/working directories and keep the system file outside mutable evidence directories.
2. An unexpected closed-stdin exception could terminate the feeder without setting its error field. Catch ordinary pipe/value failures and require completed stdin with the exact payload length before claiming local completion. Retain STOP and the lock on failure.
3. Audit checked bytes/hashes but not all completion semantics. Replay unique launch/spawn/exit facts, restrict EOF channels, reconcile process/exit/stdin state and reject falsely complete cleanup/resource claims. `seal()` audits before releasing the lock, so a false receipt cannot unlock later work.
4. An interrupted journal write could provoke a second append against an orphan witness or an already ended journal. Poison interrupted writes, reject append after close/end, and preserve the original persistence exception and evidence rather than attempting repair.

Existing raw-write-before-index ordering, exclusive claims, consumed-before-spawn semantics, actual two-process races, stale-lock refusal, original-byte mutation detection and retained STOP behavior remain. Crash recovery means preserved interruption and permanent refusal to retry; there is no recovery/resume operation. Windows post-spawn job assignment remains best effort with an attribution gap. File fsync is requested; Windows directory/power-loss persistence, hostile coordinated rollback, complete descendant visibility and remote cancellation are not certified.

## Maximum safe next subset

`src/research/opportunity_scout/n1_collector/readiness.py` adds `SCOUT_N1_LAUNCH_READINESS_V002`:

- `runtime_review(binding, record)` checks an externally supplied installed-build review contract against binary/version/model, exact argv, environment, stdin/system, existing N1 limits and R3 policy. Missing controls, fixture success, documentation-only evidence and changed bindings fail. These checks test consistency of claims, not their factual truth or human authenticity.
- `observation_plan(binding, plan)` binds the sole session/capture, exact seven metadata paths, 60-second baseline/cooldown and five-second gaps, process-start/ancestry coverage, policy presence and zero-drift/development-process stops. A plan claiming already observed baseline/active coverage is refused. It reads no account file or process inventory.
- `review_plan(...)` reuses the original N1 exact-content and explicit retained-false consent gate, requires both supplied review artifacts to be hash-bound inside that consent, refuses held/stale/consumed reservations, and returns one intended argv/environment/path/resource plan. It creates no files, consumes no reservation and always returns `native_launch_enabled:false`, `consumed:false`, UNKNOWN native semantics and NOT_OBSERVED account isolation.
- `launch_native(...)` always refuses. There is no enable flag, fixture token or approval dictionary that can activate it.

This is a complete **offline review artifact interface**, not a complete live launcher. Implementing an unverified callback that trusts a monitoring hash or a fixture PASS would bypass the remaining gate. The precise unresolved interface is a separately reviewed live observer admission: verified quiet baseline and account provenance immediately before spawn, reliable process identity/start coverage, continuous during-capture STOP/cancellation signalling, original-baseline comparison, cooldown and child absence after drain. No such real evidence exists here; the old fictional isolation profile cannot be relabelled native. Once resolved, a narrow N1-only wrapper can reuse the current Capture/byte-spool components. It must revalidate exact mutable bindings immediately before the sole spawn; no new journal, campaign runner or provider parser is needed.

Supported argv must be checked for the installed binary through separately authorised/registered evidence; documentation is a design input only. Unsupported controls mean STOP. No `help`, `version`, `auth status`, model probe, login or configuration command inherits permission. Current external review hash references alone are not proof of an account or an installed-build guarantee. The prospective runtime contract names requested controls and post-hoc visible-generation accounting; it does not assert prevention of unseen retries/continuations or provider-request visibility.

## Exact remaining decisions and bindings

| Gate | Required resolution | Current result |
|---|---|---|
| Engineering | Independent review of PR #11 corrections/readiness and approved narrow live-observer wiring | Not independently certified; launch disabled |
| Runtime | Absolute executable/hash/version, supported exact argv, canonical model/capability, Python/dependencies, environment/system/stdin/schema/source hashes | UNBOUND; no CLI inspected |
| Registration | One approved capture, external registry/reservation UUID, fresh session and sterile directory; accepted trusted-filesystem/rollback scope | No execution registration |
| Owner consent | Named owner/date; exact complete package; both seed IDs/text hashes and explicit N1-only exception despite retained false hosting flags; single parent only; privacy/access/retention and resource uncertainty | No consent registered; snapshots/schema unchanged |
| Account and monitoring | Separately approved owner research-account identification, bounded administrative scope if needed, metadata-only quiet-window/process-start coverage and live admission | NOT_OBSERVED; historical writer UNKNOWN |
| Native interpretation | One future immutable observation, then offline review of event shapes, IDs, deltas/snapshots, terminal usage and continuation attribution | UNKNOWN; no guessed parser or compatibility claim |

The N1 limits remain **600 seconds, 12 MiB combined recording trigger, <=64 KiB reads, five-second escalation, <=30-second drain and candidate 32,768 per response**. R3 remains 60,000 planning / 120,000 elevated / proposed 200,000 best-effort emergency, counting ordinary input/cache creation/cache read/output once and thinking as an output subcount. No V004-R2 60,000 automatic ceiling is substituted. No validated native meter exists; byte limits are not token or financial bounds. Provider counts/completeness, model backend pinning, remote cancellation and attributable subscription billing remain UNKNOWN. No repairs, additional parent, resume or fallback become authorised.

Future quiet-window STOP checklist remains: any drift including research metadata; missing sampling/start-event/ancestry coverage; development Claude activity; overlap; managed-policy presence/unknown; account fallback; mismatched binding; unsupported flag; journal/storage fault; incomplete drain or unresolved descendants. No post-hoc whitelist or inference of credential leakage. No account observations occur in this work.

## Files and validation

Changed: `n1_collector/binding.py`, `collector.py`, `evidence.py`, `tests/test_scout_n1_collector_process_assurance.py`. Added: `n1_collector/readiness.py`, `tests/opportunity_scout/test_n1_readiness.py`, this report. Existing N1 package, V003, original R2/R3 scientific sources, full card schema, prompt V001, original validation records and Graph remain unchanged. New validation records describe this revision without refreshing prior sample hashes.

Focused checks cover missing/mismatched permission and runtime evidence, binary/stdin/system/argv changes, location/registry overlap, false fixture authority, native refusal, reuse/races/stale locks/retained STOP, failed spawn and interrupted fsync/index, unknown EOF, incomplete stdin and false completion. Full public, guarded Scout and process suites and exact-head GitHub CI are required for delivery. Successful fictional outputs remain engineering fixtures; they are not economic findings or authority for N1 or any of the twelve scientific attempts/24 intended cards.

Recommendation: GO for review of this finite offline milestone, **NO-GO for N1 execution**. Resolve the narrow live-observer/runtime/consent registration before authorising the one capture. Unknown native semantics alone do not require a preliminary hosted probe: N1 is intended to observe them once. After N1, stop for offline interpretation; no automatic scientific dispatch follows.
