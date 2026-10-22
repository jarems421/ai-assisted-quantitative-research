# N1 metadata observer preparation V001

Status: local engineering and metadata-only preparation; **HOSTED_READINESS_BLOCKED**.
No Claude/authentication launcher is added. No account, execution approval, N1
runtime binding or scientific journal is created or changed. The owner authorised
the limited account/configuration check in conversation; that does not authorise
N1, change the frozen proposal or register fictional-seed consent.

## Why this small addition exists

Static discovery found the recorded WinGet CLI and the research configuration
directory. Point-in-time process checks initially found two VS Code Claude
extension processes. After the owner paused/restarted extensions, the next snapshot
found zero. These observations do not identify either account or attribute the
historical V003 writer. A normal-user process-start subscription was refused with
`AccessDenied`. The owner then demonstrated successful registration/unregistration
in an administrator PowerShell window. Registration alone does not establish event
delivery or a passed quiet window.

The precise missing step is to test actual delivery of start/exit/parent events
and account metadata stability before attempting the separately authorised
administrative account check. This addition does only that preparation. It does
not finish or activate the native N1 launcher.

## Two privilege levels, no Claude invocation

`src/research/opportunity_scout/n1_preflight/watch.ps1` runs as administrator for
WMI subscriptions. It reads only process name/PID/parent/creation/event-time
metadata, never command lines, environments, credential contents or account files.
It records one initial snapshot, process-start/stop events and subscription
heartbeats in a new, exclusive, fsynced SHA256-chained stream. It never starts a
child process, elevates another process, invokes Claude or changes policy. Bounds:
six-minute window, two-MiB recording trigger (crossing record retained), bounded
event-queue check and roughly one-second heartbeat. A retained claim prevents
reuse; no cleanup/reset/resume is provided. An incomplete/errored observer cannot
produce a passed reader receipt.

`n1_preflight/monitor.py --observe-only` is normal-user only. It reuses the exact
seven-path `account_metadata`/`compare_metadata` functions (stat only), requires
60 seconds before and after one fixed, harmless Python sentinel, validates its
start/exit/parent/event timestamps, and checks the observer stream/hash chain.
Unknown/error/malformed events, duplicate keys, unexpected Claude activity,
metadata drift/unknowns, stale/missing heartbeats, reader gaps, missing sentinel
events, file replacement/truncation, incomplete END and trailing bytes stop the
check. Per-file stat samples are written and fsynced before classification, with
the exact metadata-log hash/count retained in the receipt and readback checked.
The reader has a 160-second watchdog and retains its single-use claim and
receipt; neither claims authorisation for another run. The administrator observer
must be started within three minutes of the reader attaching, to leave room for
the bounded check. Stop signals are cooperative; no unrelated process is killed.

Metadata remains private under ignored
`.research/opportunity_scout/n1-admin-observer-v001/`. No raw auth output exists:
there is no auth invocation. Process names/times and local paths can still be
private. Do not publish that directory or its raw stream. Hashes detect inconsistent
edits; they do not prevent coordinated local rollback or authenticate a producer.
Windows power-loss/directory durability is not certified. The optional Python
sentinel is checked against fixed source bytes and receives no credential/provider
environment variables.

## Owner operation

The same Windows owner uses the existing administrator window solely for the
process observer. Save work and keep Claude paused. The command below uses
`-ExecutionPolicy Bypass` only for the new child PowerShell process so the local
helper can run despite this machine's observed `Restricted` policy. It changes no
persistent execution-policy setting. It executes repository code with administrator
rights: review the helper first. If managed policy blocks it, stop rather than
altering system policy. There is no account/Claude command in it.

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\Users\runni\quant-opportunity-scout-v1\src\research\opportunity_scout\n1_preflight\watch.ps1"
```

Wait for `OBSERVER_STARTED_METADATA_ONLY`, leave that window open and promptly
report the message here. The assistant can then run the already-authorised
metadata-only reader from its normal-user workspace. Alternatively, its complete
normal-user command, from the repository directory, is:

```powershell
python -m src.research.opportunity_scout.n1_preflight.monitor --observe-only
```

Do not run the reader elevated. Do not run Claude in the administrator window.
On any error, preserve the directory and report only the status; do not delete
claims, restart the check or paste raw process/account metadata. No automatic
second observation is authorised by this helper. A stale claim requires review.

## Meaning and remaining gates

`LOCAL_OBSERVER_PREPARATION_COMPLETE_NOT_AUTH_OR_N1` means the observed local
sentinel/metadata window passed this preparatory test. It is **not** a certificate
of complete Windows process visibility, lossless WMI delivery or absence of
renamed/hidden processes. WMI `TIME_CREATED` is an event-generation timestamp, not
a queried process creation identity. Polling/heartbeats and one sentinel cannot
prove all intervening starts were delivered. Cross-process causal order, hostile
tampering and provider requests remain outside this result.

Account identity/login validity, managed-policy presence/scope, installed-build
control behavior, a live command-specific admission/cancellation connection and
the original one-command `auth status` check remain unresolved. This preparation
does not consume that auth-status allowance, demonstrate its quiet window or
waive any N1 condition. The native collector's `launch_native()` still always
refuses. No generated card or experimental outcome is produced.

Validation uses fictional recorded OS events, fake time and mocked subprocesses;
no account/process sampler runs in the unit tests. A local codec check invokes
only the extracted PowerShell serializer on fictional data, checking its actual
bytes through the Python auditor. That is not a live WMI compatibility result.
The exact frozen N1 package must still pass `prepare --check`. Previous V003,
R2/R3, collector, schema, inputs, evidence, approvals and Graph remain unchanged.
