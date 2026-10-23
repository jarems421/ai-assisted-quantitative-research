# Metadata observer V003: fresh fixed path, unchanged gates

Offline preparation only. V003 is NOT_RUN. No command below is authorised by
this document or by merging its PR. Native N1 launch remains disabled and
HOSTED_READINESS_BLOCKED. Graph R4 remains paused and NOT_RUN.

V003 supersedes the V002 operator procedure for a future, separately approved
metadata-only observation. It changes only the producer/reader schema to
`SCOUT_N1_PROCESS_OBSERVER_V003` and fixed output directory to
`.research/opportunity_scout/n1-admin-observer-v003/`. The native queue fixture
uses the corresponding fictional header. No detection, timing, sentinel,
metadata, ACK, shutdown or failure rule changes. The reader refuses V001/V002
headers and historical directory arguments; it never migrates their evidence.
The original reports remain historical, including their then-current commands.

## Preserved failure

The owner-approved V002 attempt on main
`58821ab6f9ee3bf4992ddac8262788754c727c24` stopped correctly when the initial
snapshot contained `claude.exe`, PID 18384, parent PID 23360. The same snapshot
named that parent `Code.exe`. This does not identify an extension, account,
operator or network activity. No exemption follows from the recorded parent.

V002's 113,524-byte stream has SHA256
`260e53368cfe071085dea90214591b2dc96633423230f18174a53044e595ae5c`.
The producer ended with STOP_REQUEST; 108 process records had matching ACKs.
The strict reader refused the stream, took one metadata sample, and launched no
sentinel. Baseline/cooldown stability and sentinel readiness were not established.
V001's original 37,992-byte stream SHA256 remains
`de25d5076369ce6addde45f7dd7efb28ccea89b2b06eea726121629b89c32e52`.
Keep both directories, claims, receipts, reports and all failed bytes unchanged.
The V002 implementation is retained by the above main commit. No live V003
success is inferred from fixtures or from either failed historical attempt.

## One future owner-approved V003 observation

1. Review and merge the focused revision, verify its exact committed source
   hashes and passing checks, and separately approve one metadata-only window.
   Verify V003's directory is absent and the reader is non-administrator. An
   existing directory/claim, changed code or insufficient permissions means STOP;
   do not delete, reset, switch paths ad hoc or retry.
2. Save work. Arrange inactivity of known Claude terminals and Claude-enabled
   VS Code integrations through their normal application controls before the
   window. If necessary, close the relevant editor normally and coordinate from
   another client. Do not use process-kill scripts, launch Claude to check its
   state, or alter credentials/settings. A closed terminal is not proof of a
   quiet environment: the unchanged observer rejects every visible `claude` or
   `claude.exe`, including children of `Code.exe`.
3. Understand the scope: the elevated watcher records system-wide process names,
   PIDs, parent PIDs and creation/start/exit times. The normal-user reader samples
   only stat metadata for the fixed seven account paths, never their contents.
   Process names and file metadata can reveal activity. Logs inherit local folder
   permissions, are not encrypted, and are Git-ignored; this procedure uploads no
   logs. The repository must remain trusted and unchanged while elevated code runs.
4. Only after explicit approval, use Windows PowerShell as administrator under
   the same Windows account and run the reviewed watcher once:

   ```powershell
   & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\Users\runni\quant-opportunity-scout-v1\src\research\opportunity_scout\n1_preflight\watch.ps1"
   ```

   The bypass applies to that child process only, not a persistent policy change.
   Leave its window open and promptly confirm OBSERVER_STARTED_METADATA_ONLY.
   Any error or different-account elevation means STOP; preserve the attempt.
5. After that confirmation, invoke the existing reader once from a normal-user
   shell at the repository root, using the reviewed actual Python executable:

   ```powershell
   Set-Location -LiteralPath 'C:\Users\runni\quant-opportunity-scout-v1'
   & 'C:\Users\runni\AppData\Local\Programs\Python\Python313\python.exe' -m src.research.opportunity_scout.n1_preflight.monitor --observe-only
   ```

   The exact runtime path must still match the reviewed local runtime. Begin
   promptly: the reader refuses an observer startup older than 180 seconds.
   It requires a 60-second baseline, launches one byte-checked harmless Python
   sentinel, checks its start/exit/parent, and observes a 60-second cooldown.
   The watcher has a 360-second loop limit, reader 160 seconds, heartbeat/sample
   and stop checks five seconds, sentinel wait two seconds, and producer recording
   and queue checks of two MiB and 10,000 events. These are cooperative OS-call
   bounds, not hard real-time guarantees. Keep the machine awake and quiet.
6. Retain `observer.claim`, `events.jsonl`, `reader.claim`,
   `metadata-samples.jsonl`, `stop.request` and `receipt.json` under V003. Review
   the strict audit, chain/ACKs, heartbeats, original-baseline metadata comparisons,
   sentinel proof, END and receipt/readback hashes. A STOP, incomplete evidence,
   drift, lost coverage or stale claim ends the attempt without recovery or retry.
   Never whitelist the contaminating process retrospectively. Preserve the
   producer's stop even if the reader cannot create a receipt.

Even a complete result establishes local observer preparation only. It does not
prove account identity, subscription isolation, lossless WMI coverage, every
process identity/ancestry, effective native runtime controls or N1 admission.
No Claude CLI command, auth check, consent, hosted generation or scientific slot
belongs to this procedure. Do not run a model after an observer success.

## Independent offline work, outside this revision

The existing collector can support a narrow admission/STOP/cancellation adapter
design and harmless fixture tests, with consumed-state preservation, binding
revalidation, baseline/cooldown and process-coverage gates. Keep native launch
disabled until separately authorised engineering and review. No replacement
collector, new journal, parser or campaign subsystem is needed.

Package/seed hashes and already-recorded runtime facts can be checked offline;
privacy, retention, resource and consent requirements can be prepared without
registering owner decisions. Actual account/policy/runtime-support evidence needs
its own bounded authority. Sentinel and quiet-window evidence require the later
approved observation. Native event/usage/continuation semantics and remote
cancellation remain unknown pending a separately authorised N1 capture.

V003 validation consists of fictional reader tests (including complete historical
stream rejection and fixed historical-path refusal), unchanged native queue and
collector fixtures, and the guarded regression suites. Actual exact-head counts,
CI links and merge GO/NO-GO are recorded in the draft PR after checks finish;
fixture success is never reported as live V003 validation.
