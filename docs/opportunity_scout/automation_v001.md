# Research OS automation V001: critic providers

> **Offline-tested only.**
> - No model was invoked. No paid request was made. No credential was read.
> - Each adapter turns one frozen AI Critic V1 prompt into the model's final reply bytes.
> - The unchanged `critic_v1` importer judges each reply.

Code: `src/research/opportunity_scout/automation_v001/providers.py`.
Tests: `tests/opportunity_scout/test_critic_providers_v001.py`.

No `critic_v1`, top-level Scout, `v004_r3`, N1, observer, `post_generation` or `exploratory_v001` file is changed.

## Provider compatibility matrix (verified 2026-10-24, no prompt sent)

| Role | Route | Installed on this machine | Auth / billing | Model choice | Status |
|---|---|---|---|---|---|
| Generator | Claude Code CLI via the merged exploratory runner (PR #26) | `claude.exe` 2.1.302 (static file version; also seen in a real 2.1.302 stream) | Research subscription config, checked by `auth status` | `claude-opus-5-5` | Implemented and merged; never run live |
| Scientific critic | **OpenAI Codex CLI** `codex exec --json` | `codex-cli 0.164.0-alpha.11.1`, **bundled in the VS Code ChatGPT extension** (`…/openai.chatgpt-26.1021.22027-win32-x64/bin/windows-x86_64/codex.exe`). No standalone install found | `codex login status`: **"Logged in using ChatGPT"** (subscription, not an API key) | Bundled catalog lists `gpt-6-astra`, `gpt-6-sol`, `gpt-6.1-sol`, `gpt-6-luna` (and GPT-5.x). **There is no plain "GPT-6".** Efforts include `xhigh` (and `max`/`ultra`) | Adapter implemented; owner must choose a slug |
| Economic critic | **Gemini API** `generateContent` | No CLI needed | **Paid only** for `gemini-4-argon` (no free tier). Prepaid credit with auto-reload off gives a hard stop at a $0 balance (HTTP 402) | `gemini-4-argon` (the API ID matching the pilot's "Argon"). Documented price $2.00 in / $10.00 out per 1M tokens to 30 Nov 2026, then $4 / $20; thinking billed as output | Adapter implemented; needs owner API key, prepaid credit and spend cap |
| Economic critic | Antigravity CLI `agy -p` (consumer Google AI Pro/Ultra) | `agy.exe` installed | Consumer login | "Gemini 4 Argon" | **`PROVIDER_UNAVAILABLE_OR_NOT_AUTHORISED`**: Google's FAQ says wrapping `agy` in third-party applications is not supported under consumer plans, and third-party access violates its Terms. Never launched |
| Economic critic | Gemini CLI | Not installed | Consumer accounts stopped being served on 18 June 2026; API keys stated unaffected | — | Not used |

**Sources:**
- Codex non-interactive and CLI reference: `learn.chatgpt.com/docs/non-interactive-mode`, `learn.chatgpt.com/docs/cli/reference`.
- Codex config: `developers.openai.com/codex/config-basic`, which documents `web_search = disabled | cached | live`, default `cached`.
- Google: `github.com/google-gemini/gemini-cli/discussions/28017`, `antigravity.google/docs/cli/headless/`,
  `antigravity.google/docs/faq/`, `ai.google.dev/gemini-api/docs/pricing`, `ai.google.dev/gemini-api/docs/billing`.

**Commands run (none sent a prompt):** with the extension-bundled `codex.exe`, `--version`, `login status`,
`exec --help` and `debug models --bundled` (the bundled catalog, no remote refresh). Account entitlement may differ from
the bundled catalog.

## Codex CLI adapter (scientific)

```text
codex exec --json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox read-only
           --model <slug> --config model_reasoning_effort="<effort>" --config web_search="disabled" --cd <empty temp dir>
           (frozen prompt bytes on stdin; no positional prompt, no --output-schema)
```

- **Environment.** Allowlisted OS variables plus `CODEX_HOME`. `OPENAI_API_KEY`, `CODEX_API_KEY`, base-URL and
  org/project variables never reach the child, so API-key billing can't silently replace the ChatGPT login.
- **Preflight.** Executable hash unchanged; `codex-cli` version; `login status` exactly `Logged in using ChatGPT`;
  `exec --help` lists every flag used.
- **Review of the JSONL stream:**
  - one `thread.started` with a thread ID, then exactly one turn, ending in `turn.completed` with integer usage;
  - only `agent_message` and `reasoning` items, with exactly one completed agent message;
  - any command, file-change, MCP, web-search, plan or unknown item, any `turn.failed`/`error` or unknown event, a
    non-zero exit or a timeout is a fault.

  A faulted reply is never imported.
- **Model identity.** The documented `--json` events may not report the model. If the stream reports one, it must
  equal the requested slug (`MODEL_MISMATCH` otherwise). If it reports none, the identity is `REQUESTED_ONLY`, which
  is a fault **unless the owner sets `accept_requested_identity: true`** in the authorisation. That acceptance is
  recorded with every reply.

**Limits:**
- **Event profile not yet observed live.** It comes from the docs: real field names could differ, and a first live
  run may stop on an unrecognised form.
- **Agent wrapper.** Codex adds its own agent base instructions, a coding-agent persona, around the frozen prompt.
  That is a confound against the web ChatGPT pilot, and it can't be removed through the documented flags.
- **Unsupported install.** The binary is an **alpha build inside an auto-updating extension**. The executable hash is
  pinned and rechecked, so an update stops the run. The owner should install the official Codex CLI and pin that.
- **Charges and requests unknown.** One CLI process is not proof of one provider request. The subscription charge
  and the underlying request count stay UNKNOWN.
- **No account isolation.** `--ignore-user-config` still authenticates from `CODEX_HOME`, which by default is the
  same `~/.codex` the extension uses, so this uses the owner's normal Codex account.
- **Automation terms.** OpenAI's docs call API keys "the right default for automation". ChatGPT-managed auth is
  described for trusted runners, not public repositories' CI. This is local use on the owner's machine, not CI, but
  the owner should confirm it fits their plan.

## Gemini API adapter (economic)

- **One request.** A single `POST …/v1beta/models/<model>:generateContent`: one user turn (the frozen prompt), one
  candidate, `maxOutputTokens` bound, optional `thinkingConfig.thinkingLevel`, **no tools**, no system instruction.
  No retries.
- **Key handling.** The key is read from the owner-named environment variable only at dispatch, sent in the
  `x-goog-api-key` header, and never written or logged.
- **Spend cap.** Before dispatch, a conservative worst-case cost (prompt bytes ≥ input tokens, plus the full output
  cap at documented prices) must fit the remaining owner spend cap. After the response, an estimate from the
  reported usage is recorded **as an estimate, never a charge**.
- **Review.** HTTP 200; one candidate with `finishReason: STOP`; text parts only (any function call, code, inline
  data or thought part is a fault); `modelVersion` equal to, or a dated version of, the requested model;
  integer usage. A prompt block or HTTP 402/429 is a fault. A missing thinking count is UNKNOWN, never zero.
- **Data use.** Paid-tier content is documented as not used to improve Google's products. Free-tier content is. The
  free-tier models are different Flash models, so they would be a substitution and are not offered.

**Limits.** No API key, billing account or credit exists for this project yet, so a live run is blocked on the owner.
The `thinkingLevel` values are documented for Gemini 3 models, and acceptance for `gemini-4-argon` is unverified (a
rejection is a fail-closed HTTP 400).

## Antigravity (consumer)

`ANTIGRAVITY_CONSUMER` validates as a role only so a plan can name it and be refused. The pipeline records
`PROVIDER_UNAVAILABLE_OR_NOT_AUTHORISED` and never launches `agy`. No OAuth extraction, endpoint proxying, client
spoofing or browser automation exists anywhere in this package.
