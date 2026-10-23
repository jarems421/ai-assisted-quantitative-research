# N1 admission/STOP receiver V001: offline component, native execution disabled

Based on merged main `188cf5c` (PR #23). This implements the finite receiving and
cancellation connection from `n1_admission_stop_audit_v001.md`. It supplies **no
live observation source**, owner registration or native launcher. No live observer,
account/credential inspection, Claude command, model call or research slot occurs.
AI Critic, Jev, Graph R4, Discovery Lab and frozen scientific packages are unchanged.
The branch subsequently integrates owner-merged main `682ce25` (PR #22) without
editing any AI Critic file; the combined inventory is retained.

## What is implemented

`n1_collector/admission.py` defines `SCOUT_N1_ADMISSION_STOP_V001`:

- `review_contract(binding, approval, payload, artifacts)` is read-only consistency
  checking. It always returns `OFFLINE_CONSISTENCY_ONLY_NOT_ADMISSION` and
  `native_launch_enabled:false`. It reuses existing exact-content, runtime/plan,
  owner-consent and stale-reservation checks. It neither authenticates a person nor
  observes an account/runtime. Fixture reviews cannot satisfy native review.
- `Window` validates/replays fictional observations and phase transitions. It
  refuses every non-`LOCAL_FIXTURE` binding, regardless of supplied evidence.
- `FixtureGate` connects only that receiver to the existing fixed-Python fixture
  collector. It adds no executable/argv choice, CLI, process sampler or provider
  interface. An admission contract without its bound gate is refused.

`collect_fixture(..., monitor=gate)` reuses the existing `Capture`, registry,
raw byte spool, concurrent pipe drain and `trigger`/`Containment.cancel` path.
There is no second collector, monitor producer, journal or dispatcher.

## Exact evidence and reservation binding

The existing binding/approval format is retained. Its new `admission_contract`
has exactly `schema`, `window_id`, `artifacts`, `preparation_audit` and
`managed_policy_scope_sha256`. The artifact map holds exact byte SHA256s for:

| Artifact | Required check |
|---|---|
| `receipt` | Exact V003 success fields; N1 admission remains false, coverage uncertified and account/provider facts UNKNOWN. |
| `events` | Existing strict V003 `Stream` replay: original bytes, sequence/hash chain, process rejection, ACKs, heartbeats and complete END. Head/count/bytes must match both receipt and contract. |
| `metadata` | Exact receipt hash/count, complete seven-path metadata scope, original-baseline comparisons, ordered <=5-second gaps and at least 120 seconds of recorded span. |
| `preparation_review` | Separately supplied review bound to those three original hashes, audit and exact observer/helper/sentinel source hashes. A named independent reviewer attests the two 60-second windows and sentinel; the identified sentinel start/exit/parent/time must also pass existing `Stream.proof`. |
| `account_review` | Versioned external research-account review, exact child environment hash, absent managed policy and reviewed policy-scope hash. Presence/UNKNOWN/other state is refused. |
| `runtime_review` | Existing installed-build support contract in native review; separately marked fictional support in fixtures. Missing/unsupported controls refuse. |
| `observation_plan` | Existing prospective seven-path/60-second/five-second plan, with no claim that its observations have happened. |

The existing owner approval hashes the **whole binding**, including this contract
and its sole reservation/session/capture/registry. The existing durable consumed
claim hashes that binding and approval before spawn. Every new observation must
carry the matching binding hash, window identity and account/runtime review hashes;
changing a reservation or replaying another window therefore fails. The proposed
native review also reconciles its existing account/quiet-window references with
the supplied exact reviews. No real owner fields are populated here.

These checks establish consistency, not factual truth, independent identity,
signatures or protection from coordinated local rollback. The reviewer supplies
the sentinel identity and independence/timing attestations; this code does not
invent them or infer independence from a name. Keep all original evidence privately.

## Fresh observations and STOP

Preparation is historical prerequisite evidence. It never supplies a current
baseline. The fixture receiving protocol requires:

1. A new sequence of fresh observations covering >=60 seconds before admission.
   A sample is at most five seconds old, timestamps cannot run backwards or into
   the future, sample/receiver gaps are <=5 seconds, and sequence numbers cannot
   repeat/skip. Missing/stale/contradictory records poison the gate; no reset.
2. Explicit inventory, start and ancestry coverage with no reported loss, unchanged
   original seven-path metadata, matching account/runtime/policy evidence, and no
   Claude/owned-process inventory or start events during baseline/cooldown. Empty
   process lists without the explicit coverage declaration do not pass.
3. After the existing consumed claim and exact mutable-binding recheck, one fixture
   admission transition. The spawned collector PID, directly owned child PID and
   queried Windows creation FILETIME form the expected identity. UNKNOWN birth
   identity refuses; no POSIX receipt-time placeholder is substituted.
4. Before stdin, an independent-source-contract start and inventory record must
   match **all** of that exact child identity and binary name. All other reported
   starts/processes are refused, including transient Claude activity or another
   process with the same parent/name/PID but a different creation identity. There
   is no name-, parent-, editor- or account-wide Claude whitelist. After local exit,
   a contradictory still-present owned process is also refused.
5. Continuous checks in the existing collector loop. Any failed check or source
   exception calls `trigger('MONITOR_STOP', ...)`, which records the stop and
   invokes existing local cancellation/escalation/drain. A journal/storage failure
   still reaches existing exception cleanup and leaves interruption/claims intact.
   Receiver freshness is checked again after every callback returns; a late final
   callback cannot hide behind its earlier timestamp and claim completion. The
   journal records receiver time after return so replay can check the same delay.
6. Local exit, both EOFs and completed cleanup before a >=60-second cooldown with
   independently reported descendant absence. Missing/unknown/failed cleanup,
   drift or lost coverage cannot yield completion or release the registry.

Raw supplied observations and transitions are `MONITOR` events in the **existing**
witnessed capture journal. Baseline records are flushed there after consumption;
invalid records are retained. `audit()` replays the same receiver, reconciles
attach/exit/drain order with collector facts and requires a complete valid window
before a successful monitored receipt can release the lock. A false completion
cannot unlock it. A monitored nonzero exit is a retained STOP; unmonitored legacy
byte-capture semantics are unchanged.

The existing 600-second wall bound, 12-MiB raw recording trigger, <=64-KiB read,
five-second escalation and <=30-second drain are unchanged. Post-launch cooldown
counts in receipt wall time; it adds no grace to the 600-second bound. Supplied
monitor records reuse the observer's two-MiB bound and the collector's 64-KiB
per-record bound. Blocking OS/fsync/source calls remain cooperative limitations.

Refused inputs before a consumed claim launch nothing; the observation gate stays
poisoned. After consumption, failed spawn, STOP, interruption and cancellation keep
the claim; STOP/interruption retains the lock. There is no retry/recovery operation.
The real producer must separately retain its original failed observation attempt;
this receiver does not allocate or recover observer windows.

## What the tests establish, and where implementation stops

Portable guarded tests use fictional V003 streams, metadata, reviews and virtual
time. Windows process tests launch only the existing harmless Python producers.
They prove the receiving checks and actual connection to local termination,
consumed retention, byte preservation, cleanup refusal and completion replay.
Their observation callbacks deliberately construct fictional reports from supplied
fixture identities; they are **not independent OS identity/coverage evidence**.
Virtual cooldown time is labelled fixture-only and is not live timing assurance.
Linux exercises the portable receiver; Windows collector integration uses actual
local child creation FILETIME. Unknown creation identity is refused elsewhere.

**The exact remaining external/engineering dependency is a separately reviewed live
observation source and transport.** It must deliver the full-window records above
with independently queried creation identities, all relevant transient starts,
coverage/loss evidence, receiver-clock freshness, metadata and policy scope, while
retaining original failed bytes and enforcing bounded delivery. This code does
not manufacture those facts or certify a callback that might block. V003's ended
160-second reader/360-second producer and event `TIME_CREATED` cannot simply be
relabelled as that source for a possible 600-second capture plus surrounding windows.

Actual V003 success, account/policy provenance, installed-runtime controls and
owner acceptance of coverage/containment/privacy/resource limits remain external.
Windows post-spawn job-assignment gaps are unchanged. Local cancel-call success
is not remote-model cancellation; remote cancellation, provider requests and
charges stay UNKNOWN. Native event/usage/continuation semantics require the later
authorised N1 bytes, then offline interpretation; no new parser is required now.

**Ready for operational review of this offline component; NOT ready for native
admission.** `readiness.launch_native()` still always refuses, and both this gate
and the collector refuse native modes. A separately reviewed and owner-authorised
successor must supply the real source and enable one exact launch connection.
No further speculative infrastructure is proposed. Exact local/CI outcomes and
merge GO/NO-GO are recorded in the focused draft PR after verification.
