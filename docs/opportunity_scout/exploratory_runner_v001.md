# Opportunity Scout exploratory FORGE runner V001

> **Offline-tested only.** No live run has been made with this code.
> - It records one owner-authorised, seedless, memory-free FORGE generation through the Claude Code CLI.
> - It is separate from N1, the frozen V004 comparison and every scientific slot.
> - Its output is an exploratory archive, never a registered comparison.

The first exploratory FORGE pilot (two cards, VALID) was run by hand in claude.ai. Copying the prompt and the reply
caused most of its problems: a smart-quoted relay, and code-box copies without fences. This runner replaces those
manual steps and reuses the existing components unchanged:

| Step | Component reused |
|---|---|
| Archive, reserved attempt, FORGE prompt | `workflow.initialise` / `prepare` (no memory, `max_attempts=1`) |
| Research-only child environment | `v004_runtime.child_environment` (allowlist) |
| Executable discovery and hash, managed-policy check, credential-text guard | `claude_subscription` |
| Terminal classification | `v004_transport.classify_terminal` |
| Validation and import (ERROR/INVALID kept, output budget enforced) | `workflow.finish` |
| Triage and report | `workflow.triage`, `evaluation.report` |

Code: `src/research/opportunity_scout/exploratory_v001/`. No top-level Scout file, `v004_r3`, N1, observer,
`critic_v1` or `post_generation` file changes. Tests: `tests/opportunity_scout/test_exploratory_runner_v001.py`.

## Usage

```powershell
# 1. Plan: new archive, one reserved attempt, plan and authorisation template. Starts no process.
python -m src.research.opportunity_scout.exploratory_v001 plan .research/opportunity_scout/<new-archive> --title "<title>" --model claude-opus-5-5 --count 2 --effort low --max-output-tokens 16000 --timeout 300 --executable "<absolute path to claude.exe>"
# 2. The owner copies exports/exploratory-authorisation-TEMPLATE-ATT-0001.json OUTSIDE the archive and completes:
#    allowed_subscription_types (pro/max), hosted_transmission_approved: true, owner (a named human), approved_at (ISO with timezone).
#    Optionally pin account_fingerprint_sha256 from an earlier receipt.
# 3. Run: 4 administrative commands + 1 model invocation, then import, triage and report. Never retried.
python -m src.research.opportunity_scout.exploratory_v001 run .research/opportunity_scout/<archive> --authorisation <completed.json>
python -m src.research.opportunity_scout.exploratory_v001 status .research/opportunity_scout/<archive>
```

Close development Claude sessions (including IDE integrations) during a run. A change to development-account metadata
stops the run.

## What `run` does, in order

1. **Refuses** unless the authorisation binds the exact plan:
   - plan hash, archive, attempt, payload hash, model, effort, per-request cap, timeout, executable and hash,
     research configuration and child controls;
   - names a human owner with a timezone date;
   - approves exactly one model invocation and the four administrative commands;
   - lists only `pro`/`max` subscriptions.

   A refusal here consumes nothing.
2. **Consumes the attempt** with an exclusive claim file *before any CLI command*. A crash after this can never be
   re-run. `status` reports a claim without a receipt as interrupted, and `run` refuses an existing claim.
3. **Preflight**, all without a model call:
   - research configuration and credential store exist (existence only; contents never read);
   - no server-managed settings cache;
   - managed-policy check passes;
   - executable hash and child controls unchanged;
   - `--version`, and `--help` lists every flag used;
   - `auth status --json` shows `authMethod=claude.ai`, `apiProvider=firstParty`, an authorised subscription
     type, and `configDirectory` equal to the research directory.

   Only those categories, plus a hash fingerprint of identifying fields, are retained. Raw auth output is not stored.
   Any failure closes the attempt as ERROR with `NOT_INVOKED`.
4. **One invocation**: `--print` stream-json, raw JSON text (no `--json-schema`, which can reprompt), `--tools ""`,
   empty MCP, `--safe-mode`, `--restricted`, no setting sources or persistence, `dontAsk` permissions with prompts
   denied, `--max-turns 1`, a fresh session ID, and a temporary working directory outside the repository. The
   payload is the archived prompt plus the frozen format-only addendum (SHA256 `360f9354…`, the bytes used in the
   pilot).

   **Start accounting.** Launching a process is not counted as a model request. A `dispatch` marker is written
   just before the launch, and a `started` marker (with the PID) as soon as `Popen` returns. If that marker cannot
   be written, the new process tree is stopped.

   | `process_start` | Evidence | `provider_request` | `invocation_status` | `model_invocations` |
   |---|---|---|---|---|
   | `NOT_STARTED` | no launch (preflight or setup stop) | `NOT_SENT` | `NOT_INVOKED` | 0 |
   | `START_ATTEMPTED` | `Popen` raised `OSError`: the OS created no process | `NOT_SENT` | `NOT_INVOKED` | 0 |
   | `UNKNOWN` | the launch failed any other way, or was interrupted | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
   | `STARTED` | `Popen` returned | `VISIBLE_REQUEST_ID` only if the reviewed stream shows a request ID, else `UNKNOWN` | `INVOKED` / `UNKNOWN` | 1 |

   `model_invocations` counts CLI processes started, never provider requests. `process_start_attempts` counts
   launch calls. The generation-effort record uses the frozen enum (`invocation_status`) and names the start state
   in its description. A timeout, size stop or capture failure after the start is `STARTED`, with provider reach
   `UNKNOWN`. Every case consumes the attempt.

   Without a receipt, `status` reads only the markers: a claim alone is `NOT_STARTED`, a dispatch alone is
   `UNKNOWN` and a start marker is `STARTED`. With a receipt, it reports `accounting_agrees` and lists any
   contradiction between the receipt, the markers and the effort record.
5. **Raw capture straight to disk.** The CLI's stdout and stderr go directly into exclusive files in the archive, so
   nothing is buffered in memory and the bytes exist before any parsing. Limits are enforced **during** capture: the
   runner reads both pipes in 64 KiB chunks and, once stdout plus stderr pass 8 MiB, keeps nothing more and stops the
   CLI's process tree (`taskkill /F /T` from System32 on Windows; the CLI's own session on POSIX), as it also does at
   the timeout. At most one chunk per channel beyond the limit is kept; those bytes are hashed in the receipt and
   never loaded or parsed (`RUN_STOP:RECORDING_SIZE_LIMIT:PROCESS_TREE_STOPPED`, or `…_STOP_UNCONFIRMED` unless the
   kill succeeded, the process exited and both pipes reached end of file within 5 s). This is an IO bound, not a
   token certificate. Administrative output is bounded the same way at 1 MiB in memory and never stored
   (`ADMIN_OUTPUT_TOO_LARGE:<command>:<tree status>`). The stop helper is not a CLI command and is not counted.
   After the process ends, each raw file is flushed, fsynced and closed; every step is attempted once on every
   file. Any failure makes the attempt ERROR (`RAW_CAPTURE_FINALISE_FAILED:<channel>:<step>:<exception>`), and the
   possibly partial bytes are hashed but never parsed. The model is never invoked again. If the receipt itself cannot
   be written, `run` raises `INTERRUPTED`, the claim stays and `status` reports the attempt as interrupted.
6. **Fail-closed review.** The accepted event vocabulary is the one observed in a real 2.1.302 stream: `ui_invalidate`,
   `init`, `thinking_tokens`, `rate_limit_event`, assistant and result. The run stops on any of:
   - any other event, or a `user` event (an output-limit continuation appears as one);
   - a system, rate-limit, assistant or result event whose `session_id` is **missing** or different;
   - **no** `rate_limit_event` at all (absence is not evidence that overage was off);
   - reported `num_turns` that is not exactly the integer 1 (missing, 0, several and boolean all fail);
   - more than one assistant message or request ID;
   - tool use;
   - `apiKeySource` other than `none`;
   - model mismatch;
   - overage in use or a non-`allowed` rate limit;
   - a non-`firstParty` provider;
   - a non-success terminal or a stop reason other than `end_turn`;
   - result text differing from the assembled text;
   - unknown output usage;
   - a credential-like pattern anywhere in the raw stream.
7. **Postflight**:
   - `auth status` categories unchanged;
   - executable hash unchanged (auto-update detection);
   - development-account metadata unchanged (stat only);
   - no server-managed settings cache appeared.
8. **Import once.** Any fault is recorded as ERROR with no cards. Otherwise the unchanged importer decides VALID or
   INVALID, and enforces the batch's 6,000-output-token budget. Then the effort record, triage, report and receipt.

## Limits that stay (disclosed, not fixed)

- **Provider label.** The frozen provider enum has no automated-Claude label (`CLAUDE_CODE_SUBSCRIPTION` needs a V003
  comparison binding). Runs are recorded as `OPERATOR_ASSISTED`, with `parameters.transport =
  SCOUT_EXPLORATORY_RUNNER_V001`. **`OPERATOR_ASSISTED` here does not mean a human copied the reply.** The CLI was
  driven by this runner under owner authorisation. Read `parameters.transport` and `parameters.surface` before
  interpreting the label, and never pool these runs with manual operator-assisted results without that
  distinction. A proper label needs a new schema version.
- **Account isolation is configuration-level, not proven separation.** The runner shows that:
  - the child received only the research `CLAUDE_CONFIG_DIR` and no credential, endpoint or provider variables;
  - the CLI reported a first-party claude.ai login of an authorised plan type in that directory, before and after
    the call, with `apiKeySource: none`;
  - development-account file metadata did not change.

  It does not show which account the provider charged. It does not show that the CLI read nothing else under the
  same Windows user (these are CLI restrictions, not OS isolation), or that the account behind the research
  directory is the one the owner intends. That last point rests on the owner's attestation plus the optional pinned
  fingerprint.
- **Billing visibility is indirect.** The only billing-related evidence comes from CLI-reported stream metadata:
  - `isUsingOverage: false` and `status: allowed` on every `rate_limit_event`, with at least one required;
  - `overageStatus`;
  - `provider: firstParty`.

  These are the CLI's own statements, not an invoice or account statement. `total_cost_usd` (`costBasis: list`) is
  a client list-price estimate, recorded as `..._not_a_charge`. The actual subscription charge, the
  provider-request count and any server-side retries are UNKNOWN.
- **Raw streams are sensitive.** The retained stdout contains the model's thinking text and answer, local paths
  (the `init` event's working directory and PowerShell path, which can include the Windows user name), session and
  request identifiers, plugin names and rate-limit window metadata. User messages are not echoed, because
  `--replay-user-messages` is not used. It lives only in the git-ignored archive
  (`.research/opportunity_scout/…`). Never commit, publish or upload it. The credential-pattern check is a
  narrow regex (`sk-ant-`, `Bearer`, token/key JSON fields): a match stops the run but the bytes are **kept
  unredacted** (raw is never repaired), and anything the regex does not recognise is not detected.
- **Output budget versus thinking.** The batch output budget is at most 6,000 tokens (schema), Opus 5.5 thinking
  cannot be disabled, and thinking counts as output. Use `--effort low`. The per-request cap (default 16,000) is set
  above the budget deliberately, so the CLI does not auto-continue. An overrun is recorded honestly as ERROR, with no
  cards.
- **Fail-closed on new stream forms.** An unfamiliar event kind from a future CLI version stops the run (and
  consumes the attempt) rather than being trusted.
- **Process-tree stop is best effort, and it is checked.** At the timeout, the output limit or a capture-worker
  failure, the runner runs `taskkill /F /T /PID` (from System32) on Windows, or kills the CLI's own session group on
  POSIX, and then kills the CLI process directly. `taskkill /T` finds descendants through parent process IDs, so a
  descendant whose parent has already exited, or one that leaves the tree, can be missed. A POSIX descendant that
  starts its own session escapes the group. There is no Windows job-object containment here (the N1 collector has
  that; this runner does not reuse it). The stop is recorded as `PROCESS_TREE_STOPPED` only if the kill command
  succeeded, the CLI exited and both pipes reached end of file within 5 s. Otherwise it is
  `PROCESS_TREE_STOP_UNCONFIRMED`. End of file shows only that no process still holds the pipes, not that every
  descendant has exited. After the stop, nothing more is written to the raw files. The attempt is ERROR either way.
- **Capture-worker failures fail closed.** If a pump thread cannot read a pipe or write its raw file, it reports
  this to the supervising thread. Nothing more is kept on either channel, the tree is stopped, and the run is ERROR
  (`RUN_STOP:RAW_CAPTURE_WORKER_FAILED:<channel>:<READ|WRITE>:<exception>:<tree status>`) with no parsing and no
  cards. Bytes already written stay on disk and are hashed in the receipt.
- **Strictness can cost an attempt.** Requiring a rate-limit event and exactly one reported turn means a CLI build
  that omits either stops the run (and consumes the attempt) rather than passing it. This is intended.
- **Critics are not called.** The runner produces the archive that `critic_v1 prepare` reads. Critic replies still
  use the existing operator-attested `import-response` path, because `critic_v1` deliberately has no process code.

## Status

GO for independent code review. NO-GO for any live run until the owner authorises one, with a completed authorisation
file for a specific plan. No model was invoked and no generation attempt was consumed in building or testing this
runner.
