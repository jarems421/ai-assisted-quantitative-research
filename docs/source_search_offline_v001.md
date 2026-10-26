# Source-search offline validation V001

`src/research/source_search_v1/` inspects already supplied bytes. It has no
dispatcher, HTTP client, subprocess, filesystem writer, credential reader or
provider SDK. The unused authorised Codex probe remains unused. No live runtime
has been qualified, and passing synthetic tests grants no execution authority.

## Narrow provider boundary

`CaptureParser.parse(event_bytes) -> Observation` is the provider abstraction for
this delivery. `inspect_capture` consumes that observation, the exact opaque input
and final-output bytes, and caller-selected JSON locations for candidate claims.
These are internal frozen Python types, not campaign/source request or result
schemas. A future effectful runtime must retain its own claimed attempt, bounded
capture and immutable receipts before passing bytes here. No retry, scheduling,
account, reservation or authority policy is implemented in these parsers.

Three capture profiles share this boundary:

- `CodexJSONL`: one thread/turn, one final message, completed items, typed usage,
  and only reasoning, agent-message and explicit web-search items. Command, file,
  MCP, collaboration, function and unknown items are refused. A web-search item
  needs an explicit search/open-page/find-in-page action; unknown formats fail
  closed. This synthetic profile is **not** a claim that the installed CLI emits
  these exact fields. It must be reconciled with a qualified runtime capture.
- `ResponsesSnapshot`: one final Response JSON object with completed status,
  one assistant output-text message, optional reasoning, completed web-search
  calls, citations and typed usage. Incomplete, refused, failed and unknown-tool
  outputs are rejected. This does not parse SSE or claim an interrupted stream
  reached completion. A future transport must preserve raw streaming events
  separately, or deliberately use a bounded non-streaming response snapshot.
- `BaselineCapture`: consumes caller-supplied deterministic output with empty
  provider events and no model identity. It implements no live search or index
  loader. Bind the exact index, algorithm/version and query in the opaque input;
  its hash alone cannot prove that the algorithm executed. A later baseline may
  search a supplied frozen publisher catalogue without model calls.

Provider `models`, `usage`, queries, source URLs and citation locations are
**observed fields in supplied bytes**. They are not independently authenticated
execution evidence. Model identity asserted inside the final message cannot
populate provider identity. Missing observed identity remains explicitly UNKNOWN;
a mismatch is a fault. Missing search events remains unobserved, never a claimed
zero provider-request count. Citations do not count as search calls. Underlying
request counts, subscription usage and financial charges are not inferred.

## Candidate validation and retention

`CandidatePointers` names the locations of URL, requirement IDs, publisher claim,
source-kind claim and optionally claimed publisher host in a JSON document. The
caller supplies these locations and the allowed requirement IDs; property names
and top-level layout are deliberately unspecified. Unknown requirements, missing
fields, malformed or duplicate-key JSON, nonfinite numbers, unsafe URL syntax and
unexpected tools are faults. JSON is never repaired or executed.

URLs must be credential-free HTTPS DNS locators with no IP literal, local suffix,
control characters or nonstandard port. Validation performs no DNS resolution,
GET, terms check, publisher authentication or source-stop reconciliation. Public
syntax is not proof of a public IP, existing document or usable dataset. Optional
domain filtering checks returned metadata and candidate hosts at label boundaries;
it is a post-capture filter, not authority to contact any host.

Every model candidate stays `MODEL_PROPOSED_SOURCE`; baseline candidates stay
`BASELINE_PROPOSED_SOURCE`. An ORIGINAL claim remains an assertion. SECONDARY and
UNKNOWN claims are retained with explicit uncertainty. Publisher-host disagreement
is flagged; a matching host does not establish publisher identity. A candidate URL
absent from observed source/citation metadata is retained as unobserved, which
exposes unsupported/fabricated leads without pretending URL existence can be
established offline. Host/provider matching is never dataset verification.

Deduplication groups only conservative URL equivalence (host case, default HTTPS
port and empty path). Each occurrence retains its exact URL, field pointers,
requirements, publisher claim and observed event locations, including conflicting
claims. Paths, query strings and fragments are not silently collapsed.

`Review.valid` means format validation passed, **not** that identity is known,
search ran, candidates are useful or scientific requirements are satisfied. Read
`uncertainties` too. No scientific outcome, READY, human record or research gate
is emitted. A valid empty list is not proof of exhaustive search.

`Review.artifacts` retains exact input/output/event bytes, including failures,
negative answers and partial captures, with SHA-256 for each. Negative-result
meaning stays in those original bytes until the shared contract defines it.
Persistence belongs to the future native attempt owner; no files are written by
this library. Raw artifacts may contain injection text, unpublished research or
sensitive metadata: keep them private rather than serialising the entire review
into a public report. Hashes establish identity, not origin or authenticity.

Input is capped at 1 MiB; output plus event captures at 1 MiB, with at most 4,096
events/items and 64 candidate locations. Oversize supplied bytes are hashed and
retained but not parsed. This is a parsing bound, not in-flight enforcement: the
caller has already allocated the bytes. A future runtime must enforce capture
and time limits while receiving them. Empty/truncated capture does not establish
that dispatch never started and cannot authorise replay.

## Shared interface dependency

The provisional references are [Campaign Continuity V001](campaign_continuity_v001.md)
(`RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001`, disabled source descriptor) and
Source Retrieval V001's request/result contracts in draft
[PR #44](https://github.com/jarems421/ai-assisted-quantitative-research/pull/44),
reviewed at `ba2fedbfaa8ec4576944407dd233e0d8f1bd3b03`. That implementation permits
`RETRIEVE_EXACT_URL`, transmission NONE and zero searches/model calls/spend.
It cannot authorise or describe a model search by substituting new field values.
This package imports none of it and changes none of its files.

Claude's Source Discovery V1.1 addendum assigns the source component single
attempts/receipts/stops, campaign eligibility and aggregate resources to the
campaign, custody to Quarry, and scientific judgments to Anvil/humans. Its separate
Shared Interface V001 is not yet exported. Therefore this delivery intentionally
has no shared request/result encoder, candidate wire schema, authority validator,
field-support proposal contract or campaign attachment path.

The future binding must define exact candidate/negative-result fields and
exhaustive enumeration, retained artifact references, requested/observed model
identity, scope/transmission/budget/stops and native receipt mappings. Callers must
not omit inconvenient candidates by selecting only favourable field locations.
This utility cannot establish enumeration completeness without the shared schema.
An INCUBATE card can be a future provisionally authorised subject; this library
neither requires nor creates Scout READY and never bypasses downstream gates.

## Deployment choices (26 October 2026)

| Choice | Capabilities and confinement | Costs and provenance | Still requires evidence |
|---|---|---|---|
| A: restricted Codex CLI | Potential live web search and JSONL. Installed `0.164.0-alpha.11.1` still exposes `apply_patch` in the hardened local preview; read-only writes policy does not remove the tool. **Blocked.** | Existing ChatGPT login; marginal USD and subscription consumption UNKNOWN. Capture exact binary/config identity, requested/observed model, event URLs/actions, usage and raw bytes. | Supported removal of all forbidden tools; actual event vocabulary, live-search behavior, domain enforcement and structured output. No CLI patch or validation bypass. |
| B: Responses API, only `web_search` configured | Explicit hosted tool list can omit shell, file, functions, MCP and computer tools. Web search itself can search, open pages and find text. This limits configured tools, not publisher scope or scientific validity. | Separately billed API; owner-approved account/budget needed. Capture response/model/status, usage, actions, sources and citations. | Exact model/account compatibility, bounded capture, final/incomplete behavior, pricing/reservation and domain controls. No API client or call included. |
| C: deterministic supplied publisher/search baseline | Fixed catalogue and query algorithm can be run locally with no model/tools/network. Narrower recall; no invented route or live availability check. | No provider charge for a wholly local run; compute and human maintenance remain. Bind index/algorithm/query bytes, returned routes and provenance. | Representative catalogue coverage, exact algorithm and matched evaluation budget. Here only supplied-output inspection exists. An external search API would need separate authority, costs and transport controls. |

Official [Codex web-search documentation](https://learn.chatgpt.com/docs/web-search)
distinguishes hosted search from local command networking. Its
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents search-domain settings, which do not restrict connectors/MCP or command
traffic. Neither resolves the installed CLI's tool-removal blocker.

The [Responses web-search guide](https://developers.openai.com/api/docs/guides/tools-web-search)
documents `web_search`, domain filters (including subdomains), action metadata,
URL citations and the optional full `web_search_call.action.sources` list. Sources
are provider-reported URLs, not retained original bytes. Live access defaults on;
setting `external_web_access:false` uses cached/indexed results and is still a
hosted operation, unsuitable for this offline suite. We would request sources
explicitly in a separately authorised future runtime.

The [Responses create reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
defines `max_output_tokens` for generated output including reasoning, and
`max_tool_calls` across all built-in tools. These are provider-side request
controls to qualify and reconcile; neither supplies a local total-dollar ceiling
or proves every internal HTTP request is counted. Stopping a client does not
prove the hosted request stopped or incurred no charge. The CLI capability
review established no comparable configured search-count ceiling; observed events
and a process timeout would be weaker than admission of a known worst-case spend.

The [API pricing page](https://developers.openai.com/api/docs/pricing) currently
lists standard `gpt-6.1-sol` input/output at $2/$10 per million tokens (cached input
$0.10), and web search at $10 per 1,000 calls plus search-content tokens at model
rates. These dated list prices are not account entitlement, a quote or a hard
spend guarantee. A future reservation needs input/search-content bounds, output
and call ceilings and uncertain-outcome treatment; it cannot be inferred from
this parser's usage fields. No charge, credential access or paid fallback occurred.

The private local capability report remains the installed-runtime evidence:
`C:/Users/runni/quant-live-source-search-v001/.research/source-search-capability-20261026T002414Z/capability-report.md`,
SHA-256 `1261c9ef27f61d71a58e16b3b263000c9713196ae391eb3504afb51c91874f32`.
It records zero model invocations, raw administrative hashes and the qualification
of two administrative return codes. Raw previews are not published in this PR.

## Minimum connection work and verification

1. Export/reconcile Shared Interface V001 and implement its field-location,
   exhaustive-validation and native artifact mapping in a small separate binding.
2. Qualify one approved runtime: demonstrate forbidden-tool removal for CLI, or
   obtain separate API billing authority and validate an explicit web-only tool
   list. Keep the unused CLI probe unused until its original isolation condition
   is met; there is no implicit authorisation for an API probe.
3. Implement that runtime's claim-before-effect, no-retry bounded capture and
   native receipts, identity/usage accounting, scope/stop/budget checks; reconcile
   its actual event vocabulary with the parser. Parser success alone cannot
   qualify isolation, prove zero hidden requests or permit retrieval.

Run `python -m unittest tests.test_source_search_v1 -v`. The same module is listed
as `additional` in the reviewed offline inventory and runs in Windows/Linux CI.
All fixtures are fictional and in memory. Per-test guards deny filesystem opens,
sockets/DNS, shell and subprocess operations; the restricted runner adds its
existing audit guard. No test invokes search, a model, a tool or a source route.

Existing restricted-offline, public/Graph/Discovery/Level A, guarded Scout,
campaign/operator/Quarry/Jev and native guard/process regressions remain unchanged.
No historical records, frozen contracts, scheduling or scientific gates are edited.
