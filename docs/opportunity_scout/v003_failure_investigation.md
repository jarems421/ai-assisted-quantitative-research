# V003 failed real run: root cause and prospective V004 design

**V003 remains stopped: PLAIN/ATT-0001 consumed / ERROR / zero saved cards / eleven undispatched reservations. V004 is design and fictional validation only; real execution is not authorised or ready.**

Investigation branch: `codex/opportunity-scout-v004-investigation`, based on frozen implementation commit `31325c4b76670136b9709adfb61f3783b02144c9`. The private V003 authorisation, all 28 files in its local experiment directory, ledgers, receipts, request hashes and old error labels remain unchanged. No real model request was made during this investigation. The nine implementation files bound by V003 are unchanged and the old replay/status validator still succeeds. The new diagnostic module reads retained artifacts; it does not append a correction to the experiment or call its dispatcher.

## What terminated the run

The terminal result says **`error_max_turns`**, `terminal_reason=max_turns`, `is_error=true`, exit code 1, and reported `num_turns=2`. Its API error status is null. Both rate-limit notifications report `allowed`; neither is a rate-limit refusal. Stderr is empty. The model reported throughout is `claude-opus-5-5`.

The local trace establishes this sequence without publishing generated text:

1. The first model response has one assistant message/request ID, with only an incomplete thinking event exposed in the retained stream.
2. Claude Code inserts a synthetic user message identifying an output-token-limit condition.
3. A second, different assistant message/request ID appears. Its thinking and formatting events share that second ID and therefore count as stream chunks of one additional model generation.
4. That second generation calls `StructuredOutput` once. Its `ideas` value is a **string**, whereas the frozen schema requires an **array** of two cards. The string itself does not parse as JSON. Local validation reports a `type` error at `/ideas`. No card was recovered, repaired or imported.
5. The formatting tool returns an error, and the CLI terminates at the agentic turn limit with no successful terminal structured output.

The immediate stop is therefore the **turn limit after output-limit recovery and a failed formatting/schema step**. The retained trace supports two distinct visible model responses/request IDs, not a claim to complete provider-wire observability. There is no evidence of an authentication denial in the designated fields.

The aggregate output exceeded the cap independently of that stop. The immutable receipt still carries the adapter's original authentication label. The ledger's immutable attempt result is `ERROR`; `workflow.finish` replaced the error description with its output-budget failure message. Both historical records are retained, including this distinction.

## Why the adapter called it authentication

The frozen adapter classifies any nonzero process exit using `re.search('auth|login|401', stderr + stdout, re.I)` **before** parsing the terminal result. That searches every identifier, plugin name and generated field. In this run, `401` occurs inside the session identifier repeated throughout the stream; `auth` also occurs inside a built-in plugin-authoring name. These are data, not HTTP status or login errors. The parser preserves an existing error with `record['error'] or ...`, so the later terminal failure cannot replace the false authentication label.

This is an implementation defect. The new, separate diagnostic classifier prioritises structured terminal subtypes and recognises authentication/rate failures only from designated structured fields or a narrowly anchored stderr fallback before any terminal envelope. It never searches general stdout for those labels. V003's adapter and stored label are deliberately not patched.

## Turns, generations, formatting and retries

These are separate counters:

| Quantity | Retained V003 evidence |
|---|---:|
| Claude CLI invocations / reserved Scout attempts consumed | 1 / 1 |
| Assistant stream events | 3 |
| Distinct visible assistant message IDs | 2 |
| Distinct visible request IDs | 2 |
| `StructuredOutput` calls / failed tool results | 1 / 1 |
| Synthetic output-limit messages | 1 |
| CLI reported agentic turns | 2 |
| Complete underlying provider request count | UNKNOWN |

The receipt's `visible_generation_attempts=1` records the wrapper invocation/Scout attempt, and does not accurately count the two distinct model responses revealed by the trace. It is preserved; prospective diagnostics expose the counters separately. A thinking fragment followed by formatting under the same ID is not a second generation. A new model response to continue output or repair/format a card **is** an additional generation, even within one process.

`CLAUDE_CODE_MAX_RETRIES=0` did not prevent the observed output-limit recovery. It concerns failed API-request retries, a different mechanism from model continuation or schema reprompting. [Anthropic's environment reference](https://code.claude.com/docs/en/env-vars) distinguishes the output-token setting and agentic-turn setting; neither certifies a single model call for an entire CLI invocation.

There is **no blanket incompatibility** between max-turns 1 and a successful `StructuredOutput` flow. In the realistic fictional one-turn probe below, one model generation plus the local formatting-tool result succeeded, while the CLI reported two turns. Raising the turn limit is therefore not a justified automatic fix. A schema repair loop can require another model generation, which the one-generation rule forbids regardless of whether a higher CLI turn limit permits it. Anthropic documents that [structured output can reprompt after validation failures](https://code.claude.com/docs/en/agent-sdk/structured-outputs); those calls are not free local formatting.

The old `isolation_verified=false` also combines two different questions: its environment/tool checks and its exactly-one-message check. The retained environment shows only the formatting tool, no MCP/skills, no permission denials and no subagents. The observed failure of generation independence explains the composite false value; it is not evidence of repository/file access. Prospective diagnostics report environment restrictions and generation independence separately, without claiming an OS sandbox.

## Why the token ceilings failed

| Input component | Tokens |
|---|---:|
| Ordinary input | 4 |
| Cache creation | 33,158 |
| Cache read | 3,924 |
| **Aggregate input** | **37,086** |
| Allowed input / excess | 30,000 / **7,086** |
| **Aggregate output** | **10,742** |
| Allowed output / excess | 6,000 / **4,742** |
| Reported thinking subcount | 1,759 |

Cached input is still model input under the frozen protocol. It cannot be discounted, omitted or reinterpreted as a zero-cost scientific resource. Terminal totals reconcile with the input components exposed for the two distinct requests: **18,512 + 18,574 = 37,086**. Each was below 30,000; their aggregate was not. Repeated thinking/output chunks must not be summed as if each were a new input charge. The output total is used directly; the thinking subcount is not added again.

The transmitted frozen prompt is 30,714 UTF-8 bytes, including a 6,749-byte response schema and a 22,470-byte context. The same schema is additionally supplied to the CLI's structured-output interface. This creates both prompt content and formatter/tool overhead; service/system scaffolding and repeated context also contribute. **Bytes are not tokens.** No exact tokenizer breakdown of those components or provider request payload was retained, so exact schema-only/CLI-only token attribution is UNKNOWN. The observed request totals are the reliable input evidence.

The child environment did request `CLAUDE_CODE_MAX_OUTPUT_TOKENS=6000` and max turns 1. However, the output setting is a **per-request setting**, not a demonstrated aggregate cap for all continuation/formatting activity in an invocation. The output-limit notification plus a second response is consistent with the CLI reaching an individual response limit and recovering. The receipt does not expose final per-request output totals or the wire `max_tokens`, so it cannot prove each individual request respected exactly 6,000 tokens, or assign the 10,742 total between them. `modelUsage.maxOutputTokens=128000` is model-capacity metadata, not proof that 128,000 was requested or that the environment setting was ignored.

The actual engineering defects are that V003 treated those requested controls as sufficient, checked input only after execution, and validated connectivity with a tiny one-field schema. Its successful tiny preflight did not exercise realistic payload/schema/output pressure or guarantee aggregate caps. Post-hoc failure accounting correctly prevented saved cards and later dispatch; it could not prevent the first attempt's excess or internal second response.

## Fixed fictional validation

Before dispatch, the harness wrote a private immutable three-slot plan. All probes used the same **25,477-byte fabricated input**, the actual full nested two-card Scout schema, fictional Aster/Lumen evidence and fictional memory only. It did not read or transmit any frozen research prompt, EF06 excerpt, catalogue content or earlier research response. Its short-field instruction was deliberately a load/formatting control, not an economic-quality comparison. Every probe had one fresh invocation, no harness retry, 150-second timeout, the research subscription and explicit Opus model. The two-turn probe was explicitly diagnostic, never an amendment to a scientific generation allowance.

| Fixed probe | CLI max turns | CLI reported turns | Distinct model messages | Input | Output | Full schema |
|---|---:|---:|---:|---:|---:|---|
| Structured, one-turn setting | 1 | 2 | 1 | 15,489 | 2,354 | Valid |
| Structured, two-turn diagnostic | 2 | 2 | 1 | 15,488 | 2,352 | Valid |
| Raw JSON, one-turn setting | 1 | 1 | 1 | 11,582 | 2,576 | Valid |

All three had no visible continuation, schema repair or model substitution. Raw JSON removed roughly 3,907 observed input tokens relative to the first structured probe on this fictional payload. That is a descriptive difference, not an exact universal schema-cost measurement: cache state and service scaffolding can vary. These are three different preplanned diagnostic slots, not retries or a selection of the best hypothesis response. No result authorises real execution or proves behavior at the output ceiling.

**Overall validation is incomplete:** the development-account file size/mtime guard changed during the three-probe window. The initial harness recorded only the end-of-window boolean, not per-file before/after states, so attribution is unresolved. A separate Claude process was running from before the window, and a later stat check showed `.claude.json` modified within it while settings/credential-store mtimes predated it. That supports concurrency as a possibility, not proof of the cause. No development credential contents were opened, login/logout invoked or account configuration intentionally changed. The selected child research configuration is retained in the receipts, but non-interference cannot be certified from this run.

No further model calls followed that guard finding. Original probe receipts, including the false guard result, remain unchanged. The prospective harness now retains per-probe metadata snapshots and stops remaining dispatch when that guard changes; offline regression tests exercise this behavior. Offline replay of the existing fictional captures also checks raw text against the original assistant text and preserves the failed guard. It makes zero new model requests and continues to report `validation_complete=false`. A quiet, attributable account-isolation validation remains a blocker; this report does not call the preflight complete.

## Proposed V004 repair and scientific tradeoffs

The [V004 proposal](proposed_protocol_v004.json) is unapproved and intentionally has **no real dispatcher**. The candidate route is raw JSON text with all tools disabled, exactly one visible generation and strict local validation of the original output. No formatter call, model-assisted repair, Markdown stripping, salvage, replacement or hidden continuation is accepted. A malformed/long response consumes its attempt. Structured output remains a diagnostic alternative, not a rationale for raising turn or generation allowances.

Necessary prospective changes are:

- Version the classifier and expose every simultaneous fault: terminal reason, model/effort, environment, generation count, schema and both budgets. Preserve UNKNOWN usage and total provider-request uncertainty.
- Freeze a minimal transport projection, transmitting the complete response schema once and retaining exact eligible evidence/memory/cutoff and lane instructions unless an explicit scientific amendment is needed. Do not rewrite V003 prompts, pools or software. Any input reduction needs its own rationale and approval.
- Preserve aggregate 30,000/6,000 ceilings as proposed constraints. Establish a defensible pre-dispatch full-input bound including scaffolding, and resolve prevention of internal extra generation/output overrun. Synthetic averages or a parent process killing the CLI after an event do not certify that no second provider request has already started. If the subscription interface cannot enforce those requirements, the official comparison stays blocked; a relaxation needs an explicit new owner decision, never a silent turn-limit increase.
- A uniform short-field instruction can reduce truncation risk, but changes the task and may constrain economic explanation/falsifiability detail. That tradeoff must be frozen across all conditions and assessed before authorisation. Reducing the card schema or allowing a formatting model call is also a scientific/procedural amendment, not an implementation-only repair.
- Keep the four conditions, three attempts/two cards each, FORGE/RADAR/GAP allocation, source stops, immutable failed-attempt accounting and independent-human/partial-blinding review boundaries. Reuse no generated V003 output as a seed or card and disclose the failed V003 run in subsequent research history. Do not pool it as a complete V004 comparison or economic result.

**Fresh owner consent is required** for a separately frozen V004 protocol, implementation/runtime and exact twelve new request/file/content hashes, provider/model/effort, privacy scope, owner identity/date and model-pinning limitations. V003 approval cannot be copied forward. No V004 owner approval is requested here: the aggregate-enforcement and account-attribution gates are unresolved, and a concrete real-generation package has not been activated.

## Offline commands and verification

Read only, prints allowlisted diagnostic fields:

```powershell
python -m src.research.opportunity_scout.v004_diagnostics analyse-retained --receipt .research/opportunity_scout/real-comparison-v003/exports/PLAIN-ATT-0001-invocation-v003.json --request .research/opportunity_scout/real-comparison-v003/exports/PLAIN-ATT-0001-request-v003.json
python -m src.research.opportunity_scout.v004_diagnostics replay-fictional --store .research/opportunity_scout/v004-investigation/fictional-probes
python -m unittest discover -s tests/opportunity_scout -v
python -m unittest tests.test_discovery_lab tests.test_graph -v
```

The implementation adds a separate diagnostic module and 20 new regression tests rather than modifying V003. **118 Scout tests and 84 Discovery Lab/Graph regressions pass.** Tests use fictional streams for max-turn/auth false positives, actual structured auth/rate failures, chunk deduplication, second generation/request IDs, schema/continuation loops, cached-token reconciliation, unknown usage, raw-output identity, model/environment deviations, fixed fictional payload/slot accounting, timeout and account-metadata stops. The machine-readable [validation record](v004_investigation_validation.json) records final test counts, retained-input hashes and preservation checks. Private prompts, authorisation contents, generated text, account credentials and raw CLI output are not published.
