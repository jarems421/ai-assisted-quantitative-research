# V004 resource governance amendment R3 — proposed only

**HOSTED_READINESS_BLOCKED.** The owner clarified that 60,000 combined tokens was an approximate preference, not a strict financial or scientific ceiling. This proposal replaces the prospective rigid stop with common operational governance. It does not change code, activate Path B, authorise hosting, merge PR #4 or reinterpret V003. The [machine-readable amendment](v004_resource_governance_r3_proposed.json) names the R2/Path B clauses it would replace. Earlier reports and validation results retain their original scope.

Recommend keeping **32,768 per response**, Medium requested, the full two-card schema and detailed economic reasoning. Approximately **60,000 combined tokens** and **20,000 output tokens** are planning references only: neither a target, reserved input/output split, separate scientific ceiling nor quality score. Count ordinary input + cache creation + cache reads + output once, including failed/continued work. Thinking remains included in output rather than added again. Report actual usage as an experimental outcome; tokens and CLI list-price estimates do not establish subscription charges.

## Proposed common decision policy

| Reported combined usage T | Resource treatment | Effect if adopted |
|---|---|---|
| T < 120,000 | Ordinary variation; record difference from the 60,000 reference | No token-only stop or scientific invalidation. This includes crossing 60,000. |
| 120,000 <= T < 200,000 | Elevated-usage annotation | Nonblocking: retain component/history/continuation explanation from existing telemetry. Do not add a justification call, repair, retry or condition-specific permission step. |
| T >= 200,000 | Proposed emergency trigger | Best-effort abort if reliably detectable during the parent invocation; stop every later dispatch. Retain all actual work, content validity and scientific-review status separately. |
| Missing/conflicting required terminal usage | Measurement-integrity stop | Preserve observed counts and UNKNOWN; stop later dispatch. Absence of real-time counts before the CLI reports them is not zero consumption or an automatic startup failure. |
| Prohibited regeneration, repair, identity/account/journal deviation | Integrity stop at any usage | Small consumption never excuses an unauthorised third generation, replacement or other breach. |

**120,000 and 200,000 are recommendations, not adopted owner ceilings.** The flag is a simple twice-reference annotation, not a learned anomaly detector. The emergency trigger is a practical round operational backstop, not a financial authorisation, independent provider bound or assertion that every high-usage attempt is uncontrolled. A legitimate large-input continuation may trip it. Conversely, prohibited regeneration can occur far below it. Crossing 60,000 alone is ordinary variation under this proposed policy, not a missing scientific card or protocol violation.

The following examples are conditional arithmetic, assuming two contributing requests, honored 32,768 output settings, complete usage and an output-sized history replay. They are not forecasts, tokenizer certificates or bounds on unseen work:

| Example | Combined tokens | Proposed treatment |
|---|---:|---|
| Two full outputs; 12,000 input each, no generated history replay | 89,536 | Ordinary variation |
| Same, with 32,768 more input in the continuation | 122,304 | Elevated annotation; no numeric stop |
| 30,000 base input each, two full outputs and 32,768 history input | 158,304 | Elevated annotation; no numeric stop |
| 50,000 base input each, same outputs/history | 198,304 | Elevated annotation, close to emergency; no numerical exception or threshold change |
| 60,000 base input each, same outputs/history | 218,304 | Emergency; can be a lawful but unusually costly context, not proof of a loop |

Thus 200,000 gives useful headroom above the earlier 122,304 scenario and the 158,304 larger-input example, while detecting much larger consumption. It is a judgment for review, not a statistically calibrated cutoff. A lower trigger reduces exposure but risks stopping useful detailed work; a higher one may allow a costly loop or hidden work to continue longer. Lowering the per-response cap is not automatically safer: a 28,000-output/12,000-input task can fit in one 32,768 response at 40,000 total, but forcing continuation can raise it to 52,000 or 76,576 in the earlier illustrative traces. Preserve reasoning rather than reintroducing field brevity or reducing evidence to fit a reference.

There is no established reliable live aggregate token meter. A future collector may act on a deduplicated, attributable reported aggregate/lower bound when it reaches 200,000; it must not sum repeated chunks, assistant output placeholders or terminal plus the same per-model totals. If usage arrives only at termination, the action is necessarily to stop **later** dispatch, not prevention of the finished consumption. Cancellation/timeout cannot undo provider work or exclude hidden requests. No supported maximum spend follows from the threshold. UNKNOWN is never replaced by a byte/token conversion or three fictional averages.

## Additional safeguards and scientific fairness

Keep one parent invocation per consumed slot, at most two visible generations, and only an evidenced append-only output-limit continuation for the second. No separate parent call, schema/semantic repair, replacement, best-of/refinement or unexplained IDs. These remain strict regardless of how many tokens are available. Keep the existing candidate time/human/IO safeguards, durable originals, fresh contexts, no-tools transport and account monitoring. An emergency or integrity failure stops the whole run, not only an inconvenient condition; no replacement, automatic resume or reallocation follows. Ordinary format failures retain the separately proposed no-repair/next-slot distinction.

Freeze this same policy across all four conditions, along with the existing allocation, order, complete inputs/projection and full schema. No condition gets a top-up, shorter substantive task or adaptive allowance based on earlier results. Smaller input contexts may consume less or need fewer continuations; that is measured workflow behavior. Do not infer greater quality from more tokens or greater efficiency from fewer tokens without independent assessment. Keep independent human review, all twelve intended attempts and 24 intended card slots, including failed, malformed, missing and surplus output. Retain schema/content validity separately from resource events. A stop before all scheduled slots finish leaves an incomplete comparison. If terminal accounting reveals an emergency only after the final slot, report all recorded slots and the emergency separately; do not erase data, invent missing cards or claim an event-free run.

Record cumulative input components/output/combined totals and unknown-entry counts after every attempt, with fixed summaries after blocks of four. These are accounting checkpoints, not discretionary pauses to change scientific inputs or settings. The twelve-attempt planning reference is 720,000 tokens, not a run ceiling. No additional run-wide token ceiling is proposed. Twelve attempts approaching the emergency trigger would be a very resource-intensive outcome and must be reported as such; 2.4 million is neither authorised spending nor a guaranteed maximum. No hidden financial assumption, provider switch or overage enablement is introduced.

The scientific tradeoff is fewer failures caused solely by the old planning number, with greater permitted variation in actual effort. A condition may consume more tokens while producing more detailed cards; report quality and consumption separately rather than attributing differences solely to prompt content or claiming equal-resource efficiency. This remains a descriptive comparison of whole workflows under a common frozen policy, not the earlier strict Path A experiment or a test of guaranteed equal consumption.

## Approval and implementation consequences

The reviewed runtime/transport, journal R2 and old budget helper are **unchanged** and still enforce the earlier 60,000 post-hoc stop in fictional rehearsal. Their prior tests prove that earlier policy only. Do not run them as if this R3 amendment had been implemented. The new amendment must be explicitly selected, versioned, integrated into accounting/runtime/package/stop logic, hashed and independently reviewed with boundary/regression tests before any hosted validation. Old receipts/classifications are never migrated or normalised into R3 successes.

The earlier H1–H3 plan's 60,000/180,000 thresholds were also prospective. A future separately approved validation package must freeze one resource policy explicitly; it cannot silently adopt this one or acquire extra tests. Retain the bounded at-most-three-parent design and decisive event/profile checks, exact fictional inputs, account quiet window, stop conditions and no retries. Any aggregate emergency policy for that validation needs its own explicit specification; it is not supplied by multiplying a planning reference.

All approval gates remain: focused independent journal review; a reviewed, approval-bound live collector/single-journal mechanism and rollback threat model; actual CLI/account observations; separate authority for exact bounded fictional validation; and then a fully frozen real package with fresh owner protocol/privacy/model/input consent. Historical account writer remains UNKNOWN. No account or credential contents are accessed. V003, its failure labels, authority, ledger and unused reservations remain unchanged.

The resource-specific blocker update is:

| Category | Current status |
|---|---|
| Passed offline | Existing schema/lane checks, accounting arithmetic, R2 journal and recorded-stream controls retain their earlier tested scope. Scientific allocation/order and original full schema remain unchanged. |
| Requires implementation/review | R3 tier classification, separate resource/content status, cumulative summaries, live-counter deduplication and newly frozen package policy are not implemented. |
| Requires actual CLI observations | Native event/continuation behavior, requested settings, usage completeness/latency and safe research-account selection remain unestablished. |
| Requires owner decision/consent | Decide whether to adopt the proposed 120,000 flag and 200,000 emergency trigger; formally approve the complete Path B policy/rules and residual risks. Separately authorise validation and later exact real-package consent. |
| Intrinsic disclosure | Unknown provider requests/scaffolding, best-effort cancellation, local audit limits, uncertain attributable charges, partial blinding and resource differences remain. Removing an artificial ceiling does not resolve them. |

Future implementation acceptance cases must include 60,001 continuing without a token fault; 120,000 and 199,999 producing only annotations; 200,000 triggering the proposed emergency; UNKNOWN/conflicting usage stopping without zero substitution; a third generation stopping even at low usage; a 122,304-token lawful continuation remaining numerically eligible; fixed 12/24 denominators and every historical R2/V003 record unchanged. These are specifications, not claims of implemented R3 tests.

The [design-check record](v004_resource_governance_r3_design_check.json) verifies the draft's JSON, numerical examples, unchanged runtime/allocation/order, preservation and continuing authority restrictions. Eleven existing accounting tests passed for the unchanged R2 helper; they are not validation of an R3 implementation or hosted interface.
