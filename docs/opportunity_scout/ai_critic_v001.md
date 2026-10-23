# Opportunity Scout AI Critic V001

> **Offline foundation only.**
> - No model, Jev or hosted call was made. No credential was read, and nothing was activated.
> - Every card, critic answer, Jev answer and label in the code and tests is a `SYNTHETIC_FIXTURE`.
> - Critic outputs are **recommendations**. The human `SCOUT_READY_V002` review, the handoff approval and every owner gate stay authoritative. No AI-controlled routing exists in this version.

**Question this system exists to answer.** Can AI critics reliably tell research-worthy, unconventional economic hypotheses apart from incoherent, redundant or misleading ones, while greatly reducing human evaluation effort?

V001 is the smallest serious instrument for answering it. It provides:

- a layered critique of every valid card;
- a deterministic policy that the critics cannot override;
- a human-anchor instrument that measures when the critics are wrong;
- a synthetic adversarial benchmark that catches lenient, harsh, fabricating and style-sensitive critics.

Related documents:

- [Calibration and autonomy-admission protocol](ai_critic_v001_calibration_protocol.md)
- [Benchmark record](ai_critic_v001_benchmark.json)
- [Proposed Jev instrument V002](jev_instrument_v002_proposed.json)
- [Owner instruction](owner_ai_critic_v001_2026-10-23.md)

## 1. Built versus missing (inspected on main `14dfbe6`)

| Need | Existing implementation | V001 action |
|---|---|---|
| Schema, citations, documented-link depth, stage order, stopped routes | `schema.validate_idea`, `validate_seed`, `check_ref` | Reused inside Layer A, finding by finding |
| Structural warnings (falsifier, next question, predictor repeated as outcome, unsupported novelty) | `schema.structural_checks` | Reused, classified `STRUCTURAL_DEFECT` |
| Exact and possible duplicates | `engine.proximity` | Reused against a frozen reference set |
| Independent criticism | `reviews.CRITIC` + `critic-request`: one free-form record with five atomic answers; refuses generator self-review | Left unchanged. It has no rubric, no anchors and no policy, so V001 adds a versioned path beside it |
| Jev | `providers.QUESTIONS` (frozen five), `shadow_request`, `validate_shadow`; PR #21 provenance, label packet, `compare` | Reused as-is. Compared with the critics, shadow only |
| Answer extraction, raw bytes, injection flags | Graph R4 `ai_review` (paused study) | Pattern mirrored, not imported, so Scout never depends on the R4 module |
| Per-dimension rubric, anchored adverse findings, fatal versus repairable | Missing | `rubric.py` and frozen critic texts |
| Scientific, economic and adversarial critics | Missing | Three frozen prompt texts |
| Deterministic recommendation policy | Missing (frozen engine routes only `INCUBATE`/`HUMAN_REVIEW`) | `policy.py` |
| Human anchors for critic calibration, metrics with intervals, review queue | Missing (PR #21 labels answer the five Jev questions only) | `evaluation.py` |
| Adversarial benchmark | Missing (nine negative controls test software checks only) | `benchmark.py` |

**Frozen boundaries.**

- The new code is `src/research/opportunity_scout/critic_v1/`.
- It is outside every pinned closure:
  - the V004 closure: top-level `opportunity_scout/*.py`, `v004_r3/`, pinned by `hosted_acceptance_v001/prepare.check()`;
  - the N1 collector, pinned by `n1_followup_validation_v002.json`;
  - the V003 observer (`n1_preflight/monitor.py`);
  - PR #21 `post_generation/`.
- No existing Scout, Discovery Lab, Graph or protocol file changed.
- The only edited shared file is `tests/offline_inventory.json`, which registers the new test module.

## 2. Architecture

```text
archived card (immutable) ──► Layer A: deterministic checks ──────────────┐ operator side:
        │                                                                  │ lane, generator,
        └─► blinded critic input (card, passages, frozen reference set) ──┤ Layer A, mapping
                 │                     │                                  │
                 ▼                     ▼                                  ▼
          SCIENTIFIC critic     ECONOMIC critic   (independent, blind) ─► deterministic policy ──► recommendation
                                                                           │        ▲                 (write-once)
                                                    selected cases only ──► ADVERSARIAL critic        │
                                                                                                      ▼
                         Jev (frozen five questions) ── shadow comparison only        review queue + human anchors
```

### Layer A: deterministic validation (`deterministic.py`)

Every finding has one of five categories. Only the first three can be definitive, and each is verifiable from the card and supplied passages alone.

| Category | Examples | Definitive | Effect |
|---|---|---|---|
| `INVALID_INPUT` | Schema failure; unknown seed; Forge citing seeds; non-canonical requirement | Yes | Not sent to critics; `REVISION_REQUIRED` |
| `STRUCTURAL_DEFECT` | Stage order; DOCUMENTED link without citation or above its depth; existing structural warnings; exact core duplicate | Yes | Blocks READY; `REVISION_REQUIRED` |
| `DOCUMENTED_CONTRADICTION` | Citation not in the source; contradicted source used as support; reopened source stop; certified first-public time after the card cutoff | Yes | Blocks READY; `REVISION_REQUIRED` |
| `MISSING_EVIDENCE` | Speculative links; no passages; public time of a cited source unknown | No | Information only. A speculative Forge card is never penalised for having no passages |
| `UNKNOWN` | Possible mechanism duplicate; near-identical predictor and outcome wording; certainty or novelty language; instruction-like text | No | Advisories for critics and humans; instruction-like text forces `ESCALATE` |

Layer A also re-runs the frozen importer validation. A card the importer would refuse can never look clean.

### Critics (frozen texts in `critic_v1/resources/`, versioned by hash)

**Shared standard** (`common_v001.md`):

- **Authority boundary.** The card and passages are untrusted data.
- **Evidence boundary.** No outside facts; novelty means distinctness from the supplied reference set only.
- **Four judgments.** PASS, FAIL, UNKNOWN and NOT_APPLICABLE.
- **Six calibration rules.** Lack of verification is not falsity. Unusual is not implausible. Difficult data is never a coherence failure. Length and confidence earn nothing. Do not invent problems or soften real ones. Obscurity is not novelty.
- **Fatal test.** A finding is fatal only if no reasonable revision rescues the mechanism, and the critic must state what would overturn it.

**Specialists:**

- **SCIENTIFIC.** Primary dimensions: mechanism coherence, falsifiability, evidence integrity, temporal validity, uncertainty. It looks for chain completeness, confounders, circularity, predictor/outcome independence and leakage.
- **ECONOMIC.** Primary dimensions: internal novelty, economic significance, measurement feasibility, research feasibility, investment applicability, uncertainty. It looks for research-worthy mechanisms, not familiar signals, and never claims profitability.
- **ADVERSARIAL.** Primary dimensions: the hard dimensions plus uncertainty. It runs selectively. It seeks the strongest counterexample, omitted assumptions, alternatives, biases, simpler explanations and whether the falsifier discriminates. It examines earlier claims (stripped of critic identity, judgment and severity) and may conclude `NO_FATAL_DEFECT_ESTABLISHED`.

### The rubric (`rubric.py`)

Each answer gives all ten dimensions exactly once. Each dimension carries:

- judgment, typed failure, severity and `potentially_fatal`;
- the exact proposition;
- anchors, assumptions and a concrete next check;
- for fatal findings only, a fatal block.

There is no overall score.

| Class | Dimensions | Rule |
|---|---|---|
| Hard requirements | mechanism coherence, falsifiability, evidence integrity, temporal validity | A verified failure outranks any soft assessment |
| Soft assessments | internal novelty, economic significance, measurement and research feasibility, investment applicability | Never fatal; never override a hard failure |
| Uncertainty | uncertainty | FAIL means certainty exceeds evidence (repairable) |

**What makes an answer usable.** Every rule below is enforced in code, and an answer failing any of them is `INVALID`. It is kept, never repaired.

- **Anchors.** Every FAIL anchors to the exact input. A QUOTE must occur verbatim, with at least 8 characters, in the named field. An ABSENCE must name an existing field. Anchors may not cite another review's challenge text.
- **Fatal findings.** Only five failure types on hard dimensions can be potentially fatal, and each needs the violated requirement, why it is fatal rather than unresolved, and the overturning observation.
- **Missing evidence.** There is deliberately no "missing evidence" failure type. That argument can only be `UNKNOWN`.
- **Confidence.** `subjective_confidence` is coarse (LOW/MEDIUM/HIGH/UNSTATED) and is recorded as a model estimate, never as a probability.

### Deterministic policy (`policy.py`, `SCOUT_AI_CRITIC_POLICY_V001`)

The first matching rule wins. Every reason, disagreement, unknown and repair is recorded.

| Rule | Condition | Recommendation |
|---|---|---|
| R0 | Layer A `INVALID_INPUT` | `REVISION_REQUIRED` (not reviewed) |
| R1 | Instruction-like text in card or passages, or a critic suspects injection | `ESCALATE` |
| R2 | A first-pass answer missing, invalid or refused | `ESCALATE` |
| R3 | Any potentially fatal finding | Without adversarial review: `ESCALATE`. The adversarial critic confirms the same requirement a first-pass critic raised, and no first-pass critic PASSes it: `REJECT_RECOMMENDED`. Otherwise: `ESCALATE` |
| R4 | Definitive Layer A defect, non-fatal hard or uncertainty FAIL, or duplicate | `REVISION_REQUIRED` |
| R5 | Owning critic PASSes coherence, falsifiability, evidence integrity, timing, measurement and research route; no blocking soft FAIL | `READY_CANDIDATE` |
| R6 | Economic critic finds it distinct and material, but a hard dimension is UNKNOWN | `ESCALATE` |
| R7 | Otherwise | `INCUBATE`, with the checks that would justify reconsideration |

Consequences:

- **Rejection needs two critic roles.** No single critic and no adversarial objection alone can produce `REJECT_RECOMMENDED`.
- **Correlated support is flagged.** When the adversarial critic shares a model family with the first-pass critic that raised the defect, `correlated_support` is set and the selective queue audits the rejection.
- **Jev never enters the policy.**
- **Nothing is deleted.** Recommendation files are write-once and the archive is untouched.

**Adversarial selection** is policy-derived: `UNCERTAIN_FATAL_DEFECT`, `CRITIC_DISAGREEMENT`, `UNUSUALLY_PROMISING` or `NOVEL_HIGH_UPSIDE`. The one exception is an operator `HIGH_CONSEQUENCE` selection, which needs a written reason. Each subject gets at most one adversarial request.

## 3. Safeguards against leniency, harshness and self-confirmation

| Risk | Safeguard (tested) |
|---|---|
| Sycophancy, generous grading | No composite score; READY needs explicit PASS by the owning critic on six dimensions; LENIENT profile fails the benchmark by false acceptance |
| Reflexive rejection, unfamiliar = implausible | Fatal needs typed eligible failure + fatal block + adversarial confirmation of the same requirement; HARSH profile fails by false rejection; soft dimensions can never be fatal |
| Missing evidence treated as falsity | No failure type for it; speculative cards pass Layer A; benchmark `NO_EVIDENCE_VALID_MECHANISM` and `BIZARRE_BUT_VALID` must not be rejected |
| Long or confident prose, anchoring on self-assessed quality | Rubric rules 4 and 6; `CONFIDENT_FRAMING` variant must not improve any classification |
| Shared-model confirmation | Model family recorded per answer; `first_pass_independence` and `correlated_support` reported; generator model refused as its own critic |
| Invented flaws or novelty | Every FAIL anchored to verbatim input; FABRICATING profile is refused as `INVALID` and decides nothing |
| Prompt injection | Pattern flags on card and passages (never removed) force `ESCALATE`. Patterns cover overrides, judgment requests, addressing the evaluator, asserted answers, role tags and forged input markers. Input is ASCII-escaped JSON between markers carrying the input hash, so data cannot close the input block. Patterns are deliberately narrow ("operators ignore the rules" is economics, not an attack): they can miss novel attacks, which is why critics also report `injection_suspected` |
| Scout judging itself | Critics never see lane, generator, provenance, Layer A, routing or other critics; generator model refused |
| Unbounded loops, cost | Independent first pass, then at most one adversarial request; two attempts per request, the second only after an unusable first; a valid answer is never re-run |
| Presentation sensitivity | Input normalisation (NFKC, zero-width removed, whitespace collapsed, canonical keys, passages sorted by hash) makes whitespace, order and key changes byte-identical; `NEUTRAL_PADDING` variants measure the rest |

## 4. Benchmark (synthetic, `benchmark.py`)

The benchmark has 19 cards in 19 scenario families, split DEVELOPMENT/HOLDOUT. It includes all 16 requested scenarios, plus a documented timing contradiction, card-level injection and all-abstaining critics.

- **Labels.** Each card has designer labels (`SYNTHETIC_DESIGNER_NOT_HUMAN`) with acceptable and forbidden recommendation sets, so borderline cards accept more than one honest outcome.
- **Profiles.** Five scripted critic profiles run through the real validation and policy code.

| Profile | Passes | Acceptable | Forbidden | False acceptance | False rejection | Fatal detected | Invalid answers | Neutral stability |
|---|---|---|---|---|---|---|---|---|
| REFERENCE | Yes | 19/19 | 0 | 0/6 | 0/16 | 3/3 | 0 | 19/19 |
| LENIENT (everything PASS) | No | 8/19 | 10 | **6/6** | 0/16 | 0/3 | 0 | 19/19 |
| HARSH (fatal everywhere) | No | 5/19 | 9 | 0/6 | **14/16** | 3/3 | 0 | 19/19 |
| FABRICATING (invented quotes) | No | 14/19 | 0 | 0/6 | 0/16 | 0/3 | **38** | 19/19 |
| STYLE_SENSITIVE | No | 19/19 | 0 | 0/6 | 0/16 | 3/3 | 0 | **12/19** |

How to read it:

- **REFERENCE.** Passing proves only that intended judgments map to intended recommendations. It says nothing about a real model.
- **No reward for rejecting.** The benchmark never rewards rejecting most inputs (HARSH fails), nor accepting them (LENIENT fails).
- **Injection.** In every profile, instruction-like text produces `ESCALATE`.
- **Independence.** The benchmark and the critic texts share an author and are public, so the split is a regression check, not a sealed test.

Regenerate with `benchmark --write`; CI verifies with `benchmark --check`.

## 5. Jev, alongside the critics (`jev.py`)

- **Shadow only.** Jev stays an independent shadow reviewer with the unchanged frozen five questions (digest pinned in the tests) and the PR #21 import and provenance path.
- **Comparison.** `jev-compare` maps each Jev question onto one critic dimension and reports, per question:
  - agreement and decisive agreement, with the confusion matrix;
  - abstentions on both sides;
  - Jev confidence distributions when agreeing and when disagreeing (never treated as calibrated);
  - returned model, tokens and attestation status.
- **Mappings.** `falsifiable` is DIRECT and `certainty_exceeds_evidence` is INVERTED; the others are APPROXIMATE.
- **Candidate uses.** It reports counterfactual counts for the five candidate uses: early screener, disagreement detector, overstatement detector, falsifiability and mechanism checker, and escalation trigger. All are marked `applied: false`. Choosing among them needs the prospective design in the [protocol](ai_critic_v001_calibration_protocol.md#5-choosing-a-jev-role).
- **Jev never overrides Layer A, never enters the policy or the queue, and never rejects, approves or promotes alone.**

A [proposed V002 instrument](jev_instrument_v002_proposed.json) adds five atomic questions that map one-to-one onto hard dimensions (timing, circularity, discriminating falsifier, chain completeness, duplicate against the reference set). It is `PROPOSED_NOT_ACTIVE`; the frozen V001 instrument is untouched.

**Known limitations, unchanged:**

- **Model pin.** The `jev-1.13.0` pin needs an owner decision or an authorised `/v1/models` call.
- **Provenance.** Response provenance is operator attestation; the provider verifies nothing.
- **Cost.** Cost stays `UNKNOWN` without an invoice line.

The supplied report states that TypeSafe now publicly lists `jev-1.13.0` and `jev-1.14.0`. That claim was not checked here, and the repository status is not changed by it.

## 6. Operator workflow

```powershell
# 1. Freeze Layer A, blinded inputs and two first-pass requests per card (no model call).
python -m src.research.opportunity_scout.critic_v1 prepare --store N1=.research/opportunity_scout/<archive> --split TUNING --out .research/opportunity_scout/critic-v1-first
# 2. Independent human anchors, frozen before any critic output is read.
python -m src.research.opportunity_scout.critic_v1 anchor-packet .research/opportunity_scout/critic-v1-first --salt-file private-salt.json --out <new folder>
# 3. Under a separate owner authorisation: give requests/<id>.md to a fresh model session; save the raw reply unchanged.
python -m src.research.opportunity_scout.critic_v1 import-response <ws> <CRQ-id> reply.txt --model <exact id> --model-family <family> --provider OPERATOR_ASSISTED --by "<your name>" --fresh-context YES
# 4. Recommend, select adversarial reviews, recommend again.
python -m src.research.opportunity_scout.critic_v1 recommend <ws>
python -m src.research.opportunity_scout.critic_v1 adversarial <ws> <SUBJ-key> --reason UNCERTAIN_FATAL_DEFECT
# 5. Measure.
python -m src.research.opportunity_scout.critic_v1 evaluate <ws> --packet P --key K --anchors anchors.json
python -m src.research.opportunity_scout.critic_v1 queue <ws> --seed 20261023 [--mode SELECTIVE_PROPOSED]
python -m src.research.opportunity_scout.critic_v1 jev-compare <ws> --store N1=<archive>
python -m src.research.opportunity_scout.critic_v1 admission <ws>
# Offline checks
python -m src.research.opportunity_scout.critic_v1 benchmark --check
python -m src.research.opportunity_scout.critic_v1 sample-size --failures 1
python -m src.research.opportunity_scout.critic_v1 schema output
```

**Workspace.** Inside the repository a workspace must be `.research/opportunity_scout/critic-v1-*` (git-ignored). Everything in it is write-once:

- the manifest;
- requests, as JSON plus the exact prompt `.md`;
- raw replies, content-addressed;
- attempt, recommendation, queue, evaluation and Jev files.

Every attempt record is re-derived from its raw bytes on load; any edit to an attempt, raw reply or request is refused.

**`status` lists what is missing.** Never commit raw model replies or session links.

**Live adapters.** None exists: the package imports no network, process or credential module (tested by AST scan and a blocked socket). A future live adapter needs a new version and an owner authorisation.

## 7. What is implemented, design-only, or needs someone else

| | Status |
|---|---|
| Layer A, three critic texts, strict output contract, extraction, anchor validation | **Implemented, fixture-tested** |
| Blinded inputs, frozen reference set, write-once workspace, raw-byte import, attempt ceiling, self-review refusal | **Implemented, fixture-tested** |
| Deterministic policy, adversarial selection with stripped challenges, recommendations | **Implemented, fixture-tested** |
| Jev comparison, human-anchor packet and validation, evaluation metrics with Wilson and exact bounds, sample-size planner | **Implemented, fixture-tested** |
| `CALIBRATION_ALL` review queue | **Implemented and the only active queue mode** |
| `SELECTIVE_PROPOSED` queue (priority tiers, random audits of incubated/revised/rejected cards) | Computed for study; **design-only, never active** |
| Future routing mode `AI_ROUTINE_TRIAGE_V002` and its admission criteria | **Design-only.** `admission` reports eligibility for an owner decision and always returns `activated: false` |
| Calibrators (Platt/isotonic), conformal thresholds, cheap-to-strong cascade, model choice | **Design-only.** Need real anchors; see the protocol |
| Proposed Jev V002 instrument | **Design-only** |
| Real critic answers | **Need a real model** and a separate owner authorisation |
| Independent anchors and audits | **Need human reviewers** |

**Thresholds.**

- **Proposed:** every target and rate in V001. These are: 95% one-sided lower bounds for research-worthy retention and fatal-defect detection; a 10% false-acceptance upper bound; 30 human-human pairs; 20 neutral-variant groups at 95% stability; a 5% invalid-answer rate; audit rates of 20% for incubated and revised cards and 100% for rejections; 240 minutes for "significant resources".
- **Validated:** none, empirically. The sample sizes (59, 93 and 124 labelled cases for zero, one and two misses) are exact binomial arithmetic, not evidence.

## 8. GO/NO-GO

- **GO for offline readiness.** The path from archived cards to blinded critic requests, imported answers, deterministic recommendations, human anchors, calibration metrics, Jev comparison and a reproducible review queue is complete and tested on synthetic fixtures.
- **AI-controlled routing stays blocked.** No code path routes, rejects, deletes or approves. Admission needs holdout human evidence, an unchanged passing benchmark, a new version and an explicit owner decision.

**Prerequisites before the first genuine critic evaluation:**

1. Genuine generated cards in a Scout archive (N1/V004 generation, outside this task).
2. An owner authorisation for critic model use. It must name:
   - the model(s) and family, and the account;
   - consent to send these unpublished cards (or a local model);
   - a cost ceiling;
   - at most one valid answer per request, with no retry on content.
3. At least one independent human labeller (two for a human–human baseline), labelling the anchor packet before any critic output is read.
4. For Jev in the same study: the PR #21 prerequisites (model-pin decision, per-payload authorisation).

**Shortest path to the first real evaluation.**

1. When the first genuine archive exists, run `prepare --split TUNING` and build the anchor packet.
2. A human labels the packet.
3. Under the owner authorisation, the operator answers the two first-pass requests per card (plus selected adversarial requests).
4. `import-response`, `recommend`, `evaluate`.

That first run measures consistency only. Conclusions need the per-context sample sizes in the protocol.

## 9. Reading of the supplied report

The owner supplied a ChatGPT report, "Robust AI Critics for Opportunity Scout" (34 pages, 2026-10-23). It was read critically; its recommendations are leads, not authority. Its original is not stored in the repository. V001 handles it as follows:

- **Adopted:**
  - atomic per-dimension judgments with no composite score;
  - first-class abstention ("uncertain is not bad");
  - novelty relative to a frozen, hashed reference set;
  - canonical, blinded inputs that exclude generator identity;
  - untrusted-data boundary plus an injection suite;
  - critic definitions as versioned, hashed artifacts;
  - no network code in the core package;
  - retain, never delete;
  - calibration against blind human labels, using confidence bounds rather than point estimates and separate errors for rejection and acceptance;
  - random audits of the low-ranked tail;
  - "automate attention allocation before scientific authority".
- **Adapted:**
  - The report's four objective critics are replaced by your scientific, economic and adversarial structure. Each critic answers all ten atomic dimensions, so per-objective calibration remains possible.
  - Its 0–3 ordinal score is replaced by PASS/FAIL/UNKNOWN/NOT_APPLICABLE plus a typed failure and severity, which avoids invented precision.
  - Pydantic is replaced by the repository's existing `jsonschema`, so no new dependency is added.
- **Deferred:**
  - the `calibrated_human_agreement_probability` field and fitted calibrators (no anchors exist yet);
  - conformal or selective routing;
  - the cheap-to-strong cascade;
  - local evaluator models.
- **Not verified:** the report's model listings and prices, including Jev 1.14 and Claude pricing. They play no part in V001.
- **Noted:** a truly sealed challenge set is impossible in a public repository. The protocol uses a prospectively frozen holdout of real cards instead.
