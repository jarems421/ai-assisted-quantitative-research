# V004 R2 feasibility and constraint-resolution review

**Strict Path A: BLOCKED. Path B: a different, unapproved exploratory design. No new hosted probes or Claude invocations occurred.** V003 remains consumed PLAIN/ATT-0001 / ERROR / zero saved cards / eleven undispatched slots. Its implementation, authorisation and all existing records are unchanged.

**Owner feedback incorporated:** propose one **60,000-token combined allowance per attempt**, counting ordinary input + cache creation + cache reads + output, with thinking already included in output not added again. Remove separate scientific input/output ceilings. Approximately **20,000 output tokens is planning guidance**, not a target, minimum, reserved split or separate output limit. Preserve detailed economic reasoning and the full response schema. No field-level brevity restriction is adopted.

The pinned 2.1.302 subscription CLI still does not establish prevention of every internal generation or the combined allowance being exceeded. Raising the allowance can reduce truncation pressure; it does not create an enforcement guarantee. It can potentially support an explicitly exploratory comparison of the **whole CLI-assisted workflow**, with reported-usage and visible-generation compliance checks, uncertainty and failure burden disclosed. That is not a controlled equal-call/equal-consumption comparison, and is not ready to run.

## Decision matrix

`ENFORCEABLE` means supported prevention **within the named scope**; `OBSERVABLE_ONLY` means reported violations/counts can be detected without reliable prevention; `UNKNOWN` means insufficient evidence. The [complete matrix](v004_constraint_matrix.json) separates documentation (D), inspected controls/code (I), prior empirical observations (E) and assumptions (A).

| Constraint and scope | Classification | Finding |
|---|---|---|
| Second parent dispatch / application repair | ENFORCEABLE | Durable slot marker, exclusive lock and no repair call path; does not bound CLI-internal work. |
| At most one visible model generation | OBSERVABLE_ONLY | V003 had two distinct message/request IDs despite max turns 1. |
| Proposed maximum two visible generations | OBSERVABLE_ONLY | Initial plus one evidenced append-only output-limit continuation; not provider-side prevention. |
| Every underlying provider request | UNKNOWN | Visible IDs are not complete wire visibility. |
| No automatic output-limit regeneration | OBSERVABLE_ONLY | Prior recovery was visible; no supported universal prevention mechanism established. |
| No CLI schema repair with raw JSON | OBSERVABLE_ONLY | Removing the formatter interface avoided that loop in one prior raw probe; not proof against all internal loops. |
| Combined input/cache/output <=60,000 | OBSERVABLE_ONLY | No certified complete-input/scaffolding/request/output bound; reported excess is detectable afterwards. |
| Cached input / thinking-output reports | OBSERVABLE_ONLY | Can reconcile available fields; error/crash completeness can be UNKNOWN. |
| Independent accuracy of all provider usage | UNKNOWN | No complete provider telemetry. |
| Reject invalid/observed-deviating output as compliant | ENFORCEABLE | Local validation/acceptance gate, not prevention of consumption. |
| Account metadata movement / historical writer | OBSERVABLE_ONLY / UNKNOWN | Detect a sampled change; cannot attribute the old change or infer leakage. |

Documentation promises must retain their scope: [CLI controls](https://code.claude.com/docs/en/cli-reference) limit agentic turns, and a dollar stop may overshoot; [environment controls](https://code.claude.com/docs/en/env-vars) distinguish per-request output settings and failed-request retries. Neither establishes the aggregate prevention required here. A read-only scan found relevant control names in the same executable hash as the retained run; names alone prove no behavior. No binary was executed or modified this pass.

[Structured output](https://code.claude.com/docs/en/agent-sdk/structured-outputs) can reprompt on validation errors. Hooks can gate tools/submitted prompts, but [documented hook coverage](https://code.claude.com/docs/en/hooks#userpromptsubmit) does not establish interception of every within-turn model request. No unsupported flag, hook, proxy, provider or API is adopted.

## Raw JSON and the full schema

Keep the original complete two-card schema and exact lane/citation/semantic checks. Raw JSON removes the CLI formatter transport; strict parsing must still reject Markdown fences, stringified arrays, missing/extra fields, wrong enums, malformed links, unsupported citations and incomplete cards. No extraction, repair or replacement. A schema-valid object alone does not establish economic coherence or falsifiability.

Existing observations only: the fictional raw probe used 11,582 input / 2,576 output tokens and passed the full schema, versus 15,489 / 2,354 for the one-turn structured probe. This is not a universal 3,907-token saving or evidence of economic quality. The probes used fabricated repeated context, predetermined families, permitted empty references and a short-field instruction; actual RADAR/GAP work requires exact evidence/historical references. Their success cannot certify real-payload fit, semantic validity or truncation behavior.

Do **not** adopt the fictional “normally under 18 words per field” directive or compress substantive reasoning to fit an obsolete cap. That can suppress causal qualifications, time/cohort/measurement details, exact quotations and decisive falsifiers. This is an analytical tradeoff, not an empirical finding that all short cards are weaker. Preserve substantive instructions and the full schema. Ask for two detailed, coherent, falsifiable hypotheses, without padding responses to the planning guideline. Quality is independently reviewed; token volume is not a quality score.

## Input and accounting resolution

The [complete-input method](v004_budget_and_quiet_window_review.md) inventories exact known content separately from unknown CLI/provider scaffolding, requires certified bounds on every request and internal-request count, and otherwise returns **BLOCKED** for Path A. No tokenizer-derived guarantee is inferred from bytes or fictional averages. Path B must explicitly call any forecast an estimate/UNKNOWN and accept the residual consumption risk.

For observed usage, sum ordinary + cache-creation + cache-read input once; never discount caching or add its nested subdetails again. Use final/model totals for output and preserve thinking detail without double addition. [Anthropic's accounting reference](https://code.claude.com/docs/en/agent-sdk/cost-tracking) says assistant-event output is a placeholder; some crash results zero totals and some budget-stop usage omits the crossing response. Reconcile available terminal/model counts; missing/conflicting evidence remains UNKNOWN. Never reconstruct output from placeholder counts or treat list-price estimates as subscription charges. This extends prospective accounting caution without changing the accepted V003 diagnosis or its stored values.

The R2 combined total is the reported input sum plus reported output. The same inclusive 60,000 threshold applies to every attempt in every condition, with no token transfers or hidden tolerance. Report input components, output/thinking detail, combined totals, visible generations/continuations, effort, unknowns and deviations per attempt and condition. Equal allowances do not imply equal consumption. The offline combined-budget helper tests boundaries, cached inputs, output above the planning guide, missing/conflicting usage and billing separation. Actual per-attempt subscription charges/currency remain UNKNOWN unless independently observable and attributable; do not infer zero charges or prorate fees. A future common runtime output setting must be explicitly frozen, without inheriting the old setting or treating a CLI cap as an aggregate guarantee.

Legacy V003 code and the prior V004 diagnostic runner retain their historical settings for replay/audit. They are not R2 dispatchers or R2 preflight evidence. Newly versioned continuation/runtime validation and complete-package tests remain necessary; the new helper performs offline arithmetic only. No current command is authorised to run R2 research or hosted fictional probes.

The existing lane-specific input access is intentional. With a combined allowance, smaller-input lanes have more possible output/continuation headroom. Disclose that workflow tradeoff, preserve the common eligible pool and allocation, and report actual component usage. Do not top up a condition, change evidence pools or force equal output after seeing responses.

## Account resolution and the two paths

Historical writer attribution cannot be recovered from an end-of-window boolean. The separate development process is a competing explanation, not proof; no credential contents are needed. The [quiet-window method](v004_budget_and_quiet_window_review.md) designs per-file, per-command/probe baseline/active/cooldown observations and process-lifetime checks without touching either account. It is not executed here. Even stable metadata proves only sampled stability, not content equality or every possible side effect.

**A — strict:** require hard prevention of the revised combined allowance and one generation. Do not dispatch unless independent prevention and complete-input proofs exist. More successful probes cannot convert estimates into guarantees. Keep BLOCKED; the present subscription interface is not a demonstrated fit. An alternative interface would require a separate owner task and scientific/consent review; none is switched on.

**B — exploratory, recommended design:** the separate [proposed amendment](v004_exploratory_amendment_proposed.json) uses the combined 60,000 allowance as a post-hoc compliance threshold. Permit at most **two visible generations** within one parent CLI invocation: initial response plus one clearly evidenced, append-only output-limit continuation of its unfinished response. A continuation can see only its own attempt; preserve every original chunk in order, without discarding a completed candidate or choosing a replacement. Schema/semantic repairs, complete-answer regeneration, unexplained request IDs, unverifiable continuation and a third generation stop further dispatch. Total underlying provider requests remain UNKNOWN; the extra context/output all counts against the same allowance.

An output-limit continuation is a reasonable prospective way to finish detailed reasoning, rather than requiring an artificially short response. It is not free formatting or proof of equal actual effort, and prior probes do not validate the new allowance/continuation configuration. Preserve all intended slots/failures in denominators; no successful-card-only winner comparison. Stop further dispatch on combined excess, missing/conflicting usage, identity/account/observability breaches or prohibited regeneration. A format-only failure may consume its slot and proceed once to the next frozen slot only under the explicitly proposed rule; no repairs. A stopped run remains incomplete. Explicit risk acceptance is required because observed excess can already have occurred before a stop.

Recommendation: Path B is scientifically defensible for **detailed hypothesis quality and workflow feasibility**, with the common allowance and bounded, transparent continuation. It better matches the owner's stated objective than forcing one short response. It cannot answer a strict equal-resource question, prove a discovery advantage or warrant economic/M/H claims. Neither path is currently authorised or execution-ready. V003's consumed failure is not reclassified under the later allowance.

Remaining owner decisions: choose B's explicit post-hoc/observability semantics and maximum-two-generation continuation/stopping rules, or retain A blocked; settle common runtime output/continuation settings in the complete package. Account isolation is a separate gate: decide whether unresolved historical attribution plus prospective controlled observations is sufficient and separately specify any future quiet-window/fictional-probe authority. The 60,000 combined design preference is incorporated; it is not hosted-input consent. Fresh hash-specific approval of all twelve requests, runtime, privacy/model limitations and residual resource risk remains required. No execution approval is created or requested here.

Offline validation: **139 Scout tests passed**, including 21 targeted combined-budget and metadata-monitoring tests. The [validation record](v004_feasibility_validation.json) records preservation checks for 41 prior private artifacts, the frozen V003 implementation and the accepted failure report. No new hosted probe, Claude executable invocation or account modification occurred.
