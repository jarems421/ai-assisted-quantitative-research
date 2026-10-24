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
   re-run. `status` reports a claim without a receipt as interrupted.
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
5. **Raw stdout/stderr bytes are written before parsing.**
6. **Fail-closed review.** The accepted event vocabulary is the one observed in a real 2.1.302 stream: `ui_invalidate`,
   `init`, `thinking_tokens`, `rate_limit_event`, assistant and result. The run stops on any of:
   - any other event, or a `user` event (an output-limit continuation appears as one);
   - more than one assistant message or request ID;
   - tool use;
   - `apiKeySource` other than `none`;
   - model mismatch;
   - overage in use or a non-`allowed` rate limit;
   - a non-`firstParty` provider;
   - a non-success terminal or a stop reason other than `end_turn`;
   - result text differing from the assembled text;
   - unknown output usage.
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
  SCOUT_EXPLORATORY_RUNNER_V001`. A proper label needs a new schema version.
- **Output budget versus thinking.** The batch output budget is at most 6,000 tokens (schema), Opus 5.5 thinking
  cannot be disabled, and thinking counts as output. Use `--effort low`. The per-request cap (default 16,000) is set
  above the budget deliberately, so the CLI does not auto-continue. An overrun is recorded honestly as ERROR, with no
  cards.
- **Fail-closed on new stream forms.** An unfamiliar event kind from a future CLI version stops the run (and
  consumes the attempt) rather than being trusted.
- **Account identity is categorical.** Config directory, auth method, subscription type and an optional fingerprint
  of whatever identifying fields `auth status` exposes. Provider-side identity, the request count and billing remain
  UNKNOWN. `total_cost_usd` is a client list-price estimate, never recorded as a charge.
- **Not a sandbox.** These are CLI restrictions, not OS isolation.
- **Critics are not called.** The runner produces the archive that `critic_v1 prepare` reads. Critic replies still
  use the existing operator-attested `import-response` path, because `critic_v1` deliberately has no process code.

## Status

GO for independent code review. NO-GO for any live run until the owner authorises one, with a completed authorisation
file for a specific plan. No model was invoked and no generation attempt was consumed in building or testing this
runner.
