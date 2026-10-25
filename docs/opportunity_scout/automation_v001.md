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
  - Codex 0.164 prints the login result on **stderr**, with stdout empty. Each administrative command's text is
    therefore its stdout, then its stderr on its own line.
  - The login check needs exactly that one line across both channels. An API-key login, "not logged in", no
    output, the line on both channels, or any extra line is a stop.
- **Review of the JSONL stream:**
  - one `thread.started` with a thread ID, then exactly one turn, ending in `turn.completed` with integer usage;
  - only `agent_message` and `reasoning` items, with exactly one completed agent message. Every `item.completed`
    event is counted, so a second completion of the same item ID is `DUPLICATE_ITEM_COMPLETION` and never collapses
    into one message;
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

- **One request.** A single `POST …/v1beta/models/<model>:generateContent`: one user turn (the frozen prompt),
  `maxOutputTokens` bound, optional `thinkingConfig.thinkingLevel`, **no tools**, no system instruction. No retries.
  - `candidateCount` is not sent. It defaults to 1 when unset, and the Gemini 4 Argon guide says to remove it.
  - The review still requires exactly one candidate.
  - For `gemini-4-argon`, non-streaming REST output is capped at 32,768 tokens, thinking included.
- **Key handling.** The key is read from the owner-named environment variable only at dispatch, sent in the
  `x-goog-api-key` header, and never written or logged.
- **No redirects.** urllib's default redirect handling copies custom headers, the key included, onto a follow-up
  request to any origin. The transport sends only to `https://generativelanguage.googleapis.com` (default port, no
  user info) and refuses **every** redirect (`GEMINI_REDIRECT_REFUSED:HTTP_3xx`) before any follow-up request exists.
  An offline origin simulator tests this, with a control showing plain urllib would forward the key.
- **Spend cap.** Before dispatch, a conservative worst-case cost (prompt bytes ≥ input tokens, plus the full output
  cap at documented prices) must fit the remaining owner spend cap. After the response, an estimate from the
  reported usage is recorded **as an estimate, never a charge**.
- **Review.** HTTP 200; one candidate with `finishReason: STOP`; text parts only (any function call, code, inline
  data or thought part is a fault); `modelVersion` equal to, or a dated version of, the requested model;
  integer usage. A prompt block or HTTP 402/429 is a fault. A missing thinking count is UNKNOWN, never zero. The
  raw body passes credential screen V002 (see Forge Pilot 001 corrections).
- **Data use.** Paid-tier content is documented as not used to improve Google's products. Free-tier content is. The
  free-tier models are different Flash models, so they would be a substitution and are not offered.

**Limits.** No API key, billing account or credit exists for this project yet, so a live run is blocked on the owner.
The `thinkingLevel` values are documented for Gemini 3 models, and acceptance for `gemini-4-argon` is unverified (a
rejection is a fail-closed HTTP 400).

## Antigravity (consumer)

`ANTIGRAVITY_CONSUMER` validates as a role only so a plan can name it and be refused. The pipeline records
`PROVIDER_UNAVAILABLE_OR_NOT_AUTHORISED` and never launches `agy`. No OAuth extraction, endpoint proxying, client
spoofing or browser automation exists anywhere in this package.

# Research OS pipeline V001: one plan → one authorisation → one run → one report

> **Offline-tested only.** No live run has been made.
> - The software integration works end to end with fake providers.
> - That proves no provider compatibility, research accuracy or permission to use any hosted account.

Code: `src/research/opportunity_scout/automation_v001/pipeline.py` and `__main__.py`.
Tests: `tests/opportunity_scout/test_research_pipeline_v001.py`, plus real local Python children in
`tests/test_scout_automation_admin_process_assurance.py` (CI on both platforms).

The pipeline coordinates existing components. It adds no generation, rubric, archive or policy logic:

| Stage | Existing component (unchanged) |
|---|---|
| Generation | `exploratory_v001.runner.plan` / `run`, with its own owner authorisation nested in the pipeline one |
| Critic inputs | `critic_v1.packages.prepare` (Layer A, blinded frozen requests, TUNING split) |
| Critic replies | `automation_v001.providers`, then `critic_v1.packages.import_response` |
| Recommendation | `critic_v1.policy.recommend` (advisory, write-once) |
| Report | `evaluation.report`, plus one consolidated JSON and Markdown report |

## Usage

```powershell
# Plan: archive, reserved generation attempt, pipeline plan and authorisation template. Starts no process.
python -m src.research.opportunity_scout.automation_v001 plan .research/opportunity_scout/<new-run> --title "<title>" --model claude-opus-5-5 --count 2 --effort low --executable "<claude.exe>" --scientific scientific-role.json --economic economic-role.json --spend-cap-usd 2 --codex-home "<CODEX_HOME>"
# The owner completes exports/pipeline-authorisation-TEMPLATE.json (and its nested generation block) OUTSIDE the archive.
python -m src.research.opportunity_scout.automation_v001 run .research/opportunity_scout/<run> --authorisation <completed.json>
python -m src.research.opportunity_scout.automation_v001 status .research/opportunity_scout/<run>
python -m src.research.opportunity_scout.automation_v001 report .research/opportunity_scout/<run>
```

Add `--json` to `report` for the full record.

Example role files:
- Scientific: `{"provider": "CODEX_CLI", "family": "openai", "model": "<gpt-6-* slug>", "effort": "xhigh", "accept_requested_identity": false, "executable": "<codex.exe>"}`
- Economic: `{"provider": "GEMINI_API", "family": "google", "model": "gemini-4-argon", "api_key_env": "GEMINI_API_KEY", "max_output_tokens": 8192, "thinking_level": "high", "prices": {"input_usd_per_million": 2.0, "output_usd_per_million": 10.0, "source": "ai.google.dev pricing", "as_of": "2026-10-24"}}`

## What the authorisation binds

The pipeline authorisation must bind all of the following:
- the plan hash;
- both critic roles exactly (provider, family, model, effort, executable hash, identity acceptance, prices, key variable name, output cap);
- the spend cap and the maximum number of critic requests (two per card);
- one attempt per request, and the stage list;
- `adversarial_permitted: false`;
- the raw-retention policy;
- `hosted_transmission_approved: true`;
- a named human owner with a timezone date.

For Gemini it also needs a positive cap and the owner's attestation that prepaid auto-reload is disabled. The nested
generation authorisation must bind the planned generation and name the same owner; the merged runner validates the rest.

Per-request hashes cannot exist before the cards are generated. The authorisation therefore binds the frozen critic
texts by hash and the deterministic request construction. Each actual request and prompt hash is recorded when it
is built, and every prompt is re-checked against its frozen `rendered_prompt_sha256` before dispatch.

## Safety behaviour

- **One attempt.** Each request is claimed exclusively before dispatch and is never dispatched twice. This is
  stricter than the critic contract's allowance of two attempts. Critics run in separate processes or HTTP requests,
  and each sees only its own frozen blinded request.
- **No resume.** The whole run is claimed before any process. A second `run` is refused. A crash leaves a partial
  record: `status` shows `INTERRUPTED`, and `report` marks a claimed request whose outcome was never recorded as
  `CLAIMED_OUTCOME_UNKNOWN`. That request is never re-dispatched.
- **Faults are never imported.** A provider fault means the reply is not imported. Its raw bytes are kept beside the
  ledger record, and the request stays unanswered, so the policy gives ESCALATE. Invalid replies are imported unchanged
  and stay INVALID.
- **Spend reservations are never released.** Each Gemini request reserves its full worst-case cost (exact whole
  micro-USD, rounded up; the cap is rounded down) before its dispatch record exists. The cumulative reservation never
  goes down: not for a lower usage estimate, missing usage, a transport failure, a refused redirect or a crash.
  Estimates are recorded beside it, never subtracted. The cap therefore bounds the sum of worst cases.
- **Bounded Codex administrative commands.** `--version`, `login status` and `exec --help` run only through the
  merged runner's `admin` and `capture`:
  - stdout and stderr together are capped at 1 MiB **while capturing**, with a 30-second timeout;
  - past the cap, at the timeout or on a capture failure the process tree is stopped, and each is a named
    `PREFLIGHT_STOP` before any critic process;
  - each distinct executable identity (resolved path, pinned SHA-256 and `CODEX_HOME`) gets its own preflight before
    its first critic process. `pipeline-codex-preflight-claim-<id>.json` is written before the first launch, and
    `pipeline-codex-preflight-record-<id>.json` records the launches and the confirmed starts;
  - one executable passing never authorises another. Only roles with an identical identity reuse a result, and an
    unrecorded or failed preflight is a stop for that executable;
  - the pinned hash is rechecked before every critic launch, so a cached preflight never covers a changed binary
    (`EXECUTABLE_CHANGED_BEFORE_DISPATCH`).
- **HTTP protocol errors are faults.** `http.client` errors such as `IncompleteRead` or `BadStatusLine` are not
  `OSError`s, and they become `TRANSPORT_FAILED:<type>` like any other failed send:
  - no partial body is kept or imported, the reservation stays, and the request count is UNKNOWN;
  - only the exception type, or one of the transport's own fixed `GEMINI_*` codes, is recorded. Exception text can
    carry partial response bytes.
- **Adversarial review is never dispatched.** A policy recommendation for it is recorded `PENDING_APPROVAL`.
- **Unavailable roles stop honestly.** An unavailable role (`ANTIGRAVITY_CONSUMER`) is recorded
  `PROVIDER_UNAVAILABLE_OR_NOT_AUTHORISED` and the run ends `INCOMPLETE_CRITICS`. Nothing is substituted.
- **No authority.** Recommendations never change Scout routing and carry no READY, investment, causal or trading
  authority.

## Report

`pipeline-report.json` and `pipeline-report.md` contain:
- every card with its Scout ID, route, falsifier and next step;
- the generation status, model and error;
- per-dimension Scientific and Economic judgments;
- disagreements, fatal claims and repairs, and the reconsider-when checks;
- unknown dimensions and unresolved assumptions;
- the deterministic recommendation and adversarial status;
- each critic's provider, model, identity basis, faults, usage and cost estimate;
- the accounting below, and the Gemini reservations and estimate total;
- missing or interrupted stages.

There is no composite score. Actual charges are UNKNOWN.

## Status and accounting

`status` and the report count from recorded files only. Each count is `{at_least, exact}`. Every marker is written
before the launch or request it names, so a missing marker establishes zero. Nothing else does.

| Measure | Evidence |
|---|---|
| Model CLI processes started | Generation `process_start`; `pipeline-started-<request>`, written by `on_start` once `Popen` returns. A dispatch without that marker is UNKNOWN |
| Administrative CLI launches (send no prompt) | Generation receipt `administrative_commands_run`; each Codex preflight record. A claim without its record is UNKNOWN |
| Dispatches attempted | `exploratory-dispatch-*` and `pipeline-dispatch-<request>` |
| Provider requests | Generation: a visible request ID means at least 1. Codex: a model-authored message means at least 1. Gemini: a recorded response is exactly 1 (no redirects or retries) |

**Unknowns:**
- A started CLI process is never counted as one provider request, so Claude and Codex request counts stay `exact:
  UNKNOWN`.
- A dispatched Gemini request with no recorded response (transport failure, refused redirect or crash) is UNKNOWN.

## Offline demonstration (what the tests prove)

The tests run with a fake Claude CLI in the real 2.1.302 vocabulary, a fake Codex JSONL stream, a fake Gemini
transport and `SYNTHETIC FIXTURE` critic answers, with socket and process creation denied.

1. One run generates two cards. Each gets two independently dispatched critic requests, byte-identical to its frozen
   blinded request, so four imports are VALID, both cards are READY_CANDIDATE, a report is written and the routes stay
   INCUBATE.
2. A scripted scientific CONFOUNDED versus economic PASS disagreement gives REVISION_REQUIRED, with adversarial
   review `PENDING_APPROVAL` and no fifth call.
3. An invalid Gemini reply is kept as INVALID, and a two-message Codex stream is a provider fault and is not
   imported. Both lead to ESCALATE, with no second attempt.
4. Model fallback on either provider, unobserved Codex identity without acceptance, and unknown usage are all faults.
5. A Codex API-key login stops before dispatch. A Gemini authorisation without the auto-reload attestation is refused,
   and a spend cap below the worst case means no request is sent.
6. An unavailable Antigravity role, HTTP 401 and an absent key are each reported, with nothing substituted.
7. A timeout or transport failure is final, and a failed send counts as UNKNOWN, never zero.
8. A crash after a process starts leaves a truthful partial report, and the duplicate run is refused, with no second
   dispatch.
9. Altered authorisations (assistant owner, other generation owner, adversarial, two attempts, other model) are
   refused before any process. Plan, status and report start nothing. The new package is outside the frozen V004 and
   R3 closures.
10. The API key reaches only the transport header. It never appears in any written file.
11. Through the real transport and an offline origin simulator, a redirect from the documented host is refused, with
    no follow-up request, so `attacker.invalid` never receives the key.
12. Reservations are never released. With one reservation held, a second request that no longer fits is refused,
    whether the first had a low estimate, missing usage or a transport failure.
13. Codex administrative commands get the 1 MiB combined limit, the 30-second timeout and no stdin. Each of these
    stops the preflight by name before any critic process: overflow, timeout, capture failure, non-zero exit, a
    runner returning oversized output, and a refused launch. With real children, a combined stdout/stderr flood (each
    channel under 1 MiB) and a hang are stopped together with their process trees.
14. Accounting is exactly zero before a run. After the run there are three model CLI processes, five dispatches, and
    provider requests at least five with exact UNKNOWN. A crash keeps the started process counted and leaves its
    requests UNKNOWN.
15. `IncompleteRead` (through the real transport, with a truncated body), `HTTPException`, `BadStatusLine` and an
    untrusted `ScoutError` message each give a recorded `TRANSPORT_FAILED:<type>` fault:
    - the run finishes, with one dispatch per request and none resent;
    - the reservation stays, and the request count and estimate are UNKNOWN;
    - neither the key nor the partial body appears in any written file.
16. With both critics on Codex, the identity decides the preflight:
    - an identical executable runs one preflight;
    - two different executables each run their own three commands before their first critic process;
    - a second executable with an API-key login or a failed command is stopped while the first's critics stay VALID;
    - a binary changed after planning gets no command at all, and one changed during a run is never launched again.

## Blockers to one fully automated live run

1. **Economic critic.** No compliant automated route is set up. The consumer Antigravity route is not authorised, and
   the Gemini API needs the owner to create an AI Studio key with prepaid credit (minimum $5) and auto-reload off. At
   documented prices one economic request is a few cents: a 24 KB prompt and up to 8,192 output tokens is at most about
   $0.13 worst case at $2/$10. That is an estimate, not a quote.
2. **Scientific critic model choice.** The owner must pick an exact Codex slug (there is no plain "GPT-6") and decide
   whether to accept requested-only identity. The Codex `--json` profile has not been observed live, and the binary is
   an extension-bundled alpha. An official Codex CLI install is recommended.
3. **Generator.** The merged runner has never run live. Its own preflight (`--version`, `--help`, `auth status`) and the
   strict stream profile will first meet a real CLI on the first authorised run.
4. **Owner approvals.** Hosted transmission of unpublished cards to OpenAI and Google, the spend cap, and the
   authorisation file itself.

## Forge Pilot 001 corrections (prospective, 2026-10-25)

Forge Pilot 001 (`.research/opportunity_scout/forge-live-pilot-001`, private) is complete and immutable. Its records,
including the economic `PROVIDER_FAULT` for `CRQ-952b880443c8b5c3` and its V001 report, are never rewritten,
regenerated or re-imported. The changes below apply only to runs made after them. No live model call was made to
develop or test them.

**Credential screen V002** (`automation_v001/credentials.py`; providers `SCOUT_CRITIC_PROVIDERS_V002`).
- *Defect.* V001 adapters used `claude_subscription.safe_output`, whose `Bearer\s+\S+` fires on any word after
  "bearer". The frozen economic rubric itself says "an identifiable economic bearer exists", so ordinary critique
  prose was a credential fault. A local, value-free diagnostic located Pilot 001's single match in the reply's prose.
- *Rule.* After "bearer" (any case) or an `Authorization:` header, a value in the RFC 6750 token alphabet is a
  credential at 20+ characters, or at 6+ unless it is a plain word, hyphenated compound or all-capitals label. Digits
  are not required. `sk-ant-` and the credential JSON keys are kept. OpenAI- and Google-shaped keys are added, and so
  are `id_token`, `apikey`, `client_secret` and `x-goog-api-key`.
- *Scope.* Raw bytes and every decoded JSON string are screened, so a JSON-escaped value is caught too.
- *Records.* Every critic record carries `credential_screen: {version, categories}`. These are labels only, never a
  value.
- *Accepted gap.* A real 6–19 character token spelt like an ordinary word is not detected.
- *Unchanged.* `safe_output` itself and the exploratory Claude runner are not changed (they are frozen closures).

**Receipt and report V002** (`SCOUT_RESEARCH_PIPELINE_RECEIPT_V002` / `..._REPORT_V002`).
- *Defect.* V001 `finish` rendered the report before writing the REPORT stage and receipt. Every finished V001
  report therefore reads `INTERRUPTED_OR_NOT_FINISHED` with REPORT `NOT_RECORDED`.
- *Order now.* The report files are written first, with the decided outcome. Then the REPORT stage is written with
  their hashes. Last comes the receipt, which binds both files and the execution record. The receipt is the commit
  marker, and each report states it is final only when the receipt binds it.
- *Verification.* `status.finalisation` re-checks, read-only, everything a V002 receipt binds:
  - both report files' hashes;
  - `pipeline-execution.json` against `execution_sha256`;
  - the REPORT stage's hash record;
  - every persisted stage status against the receipt;
  - the saved report's own outcome and stages.

  Each check is `MATCH`, `MISMATCH`, `ABSENT` or `UNREADABLE`. The state is:
  - `VERIFIED` when all checks match;
  - `MISMATCH` when any check is a mismatch;
  - otherwise `UNVERIFIED` (including an unreadable receipt).

  Only `VERIFIED` is `consistent: true`. A receipt that merely exists means the run finished, not that it is
  verified. The other states are:
  - `NOT_FINALISED`, after a crash (any report files are `UNCOMMITTED`);
  - `LEGACY_RECEIPT_UNBOUND`, for a V001 run. Pilot 001 also shows `consistent: false`.

  Nothing is repaired. After a finished V002 run, a live `report` equals the committed one.

**Execution provenance V001** (`automation_v001/execution.py`).
- *What is recorded.* `pipeline-execution.json` is written right after the claim and before any process. It holds:
  - HEAD, read from the `.git` / `gitdir` / `commondir` / ref / `packed-refs` files, with no git process launched;
  - the CRLF-normalised hash of every file in the static `src.*` import closure of `automation_v001` (relative
    imports included), with their digest;
  - the Python runtime;
  - the Scout batch `base_commit`, labelled as a historical constant, not the executing revision.
- *Worktree cleanliness* is always `UNKNOWN`: establishing it needs the index and object store.
- *Failures.* Unreadable metadata is `UNKNOWN` with a reason, and a failure never blocks a run.
- *Unchanged.* Plans and authorisations, critic texts (still pinned by `critic_resources_sha256`) and every frozen
  Scout contract are unchanged.
