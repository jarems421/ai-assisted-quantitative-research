# Research OS architecture and operating contracts

**Pre-Level-A measurement gate (2026-10-21):** [Measurement Gate M](strategy/measurement_gate_m.md) formalises a manual positive-control requirement for separately authorised new frontier research. An actual distinctive predictor, usable units, separately observable outcome, valid economic join, plausible public-time route and meaningful listed exposure must exist before a deeper study is proposed. M is not a fourth evidence level or a new runtime transition; it certifies neither prediction nor historical actionability. The [eight-family campaign](strategy/measurement_gate_campaign_report.md) preserves original failures and a separately rejected gross-only reformulation in a lightweight ledger. No economic design or acquisition follows automatically. Frozen v1 contracts and historical decisions below remain unchanged.

**Frontier candidate assessment:** the [value-and-competition standard](strategy/frontier_selection_standard.md) distinguishes economic relevance, external interest, exact-signal saturation, differentiation and investment usefulness. Novelty of data, mechanism, signal or join does not establish a profitable opportunity. Frictions that might preserve an advantage need evidence. This governs new selection reasoning without altering v1 contracts or authorizing research execution.

**New research evidence tiers (2026-10-20):** [Level A](strategy/next_frontier_review.md) permits explicitly disclosed retrospective reconstructions to test economic associations; valid units, joins, missingness and temporal definitions remain mandatory. It does not establish causality or historical trading value. Level B requires historically available information; Level C additionally requires executable investment accounting and independent evidence. These tiers apply to separately authorized new work and do not migrate, reopen or weaken frozen v1 experiments. The proposed river pilot awaits approval; its sources have not been acquired.

**EXP004 execution-gap investigation stopped with unresolved evidence; no-fill remains inactive.** The [26-case forensic report](acceleration/exp004_execution_gap_report.md) preserves complete 28-quarter price enrichment and all frozen identities. Independent requests returned 17 raw daily bar candidates, including 16 with two-sided scale agreement; none meets the complete historical provider-class/session-opening certificate. Nine cases have no recovered exact-date bar from that route; TWMC remains unresolved. All 26 remain represented. No no-trading certificate, amendment receipt or V002 engine exists; all folds/replays/performance remain NOT_RUN, Validation/Test0. This source result is not an economic verdict.

Research OS controls canonical evidence, contracts, scientific gates, trials and reproducible execution. Its [Phase 3D checkpoint](acceleration/phase3d_report.md) supplies revenue/identity contracts, a declarative proof schema/compiler, exact input replay and a synthetic local Decimal ledger with a disabled Nexus adapter. These software passes do not certify a real historical universe or alpha. EXP004 remains paused. V002/v003 modeled policies retain their approvals and inactive status; exact public availability remains UNKNOWN. They do not authorize a timing rule for another event family.

The v1 architecture and commands below remain compatibility infrastructure; no old experiment is migrated or reopened. The minimal spine reuses hashes, immutable stores, population reconciliation and stage principles. Real compiler-to-Store/selection integration remains blocked pending scientific certificates and separate experiment authorization. Phase 4A-I adds versioned evidence-tier adapters and a design-only Proof v2; v1 controllers, gates and frozen outputs remain unchanged. Current work stops at candidate review with executable certification blocked. Synthetic commands are `python -m src.research.phase3d check` and `python -m src.research.phase3d report --check`; private source reconciliation adds `python -m src.research.phase3d review --check`.

## V1 compatibility architecture and responsibility

```mermaid
flowchart TD
    Spec["Validated specification / point-in-time audit"] --> Gates["SQLite gates / frozen hashes / human approvals"]
    Gates --> Plan["Funnel / cost and evaluation ceilings"]
    Plan --> SDK["Observed typed Nexus SDK jobs"]
    SDK --> Journal["Durable keys, IDs, warnings and trial records"]
    Journal --> MCP["Authorized MCP session bridge: events first, then history"]
    MCP --> Raw["Immutable private raw responses / hashes / integrity"]
    Raw --> Local["Independent metrics / stability / robustness"]
    Local --> Report["Cards, figures, reports and README registry"]
    Roles["Aurora role prompts / trajectory provenance / grading plan"] -. "remote execution blocked pending isolation" .-> SDK
```

Codex develops and operates the reviewed infrastructure within task authorization. Aurora can reason about hypotheses, but it cannot supply human approval or be trusted to enforce sealed-data access with a prompt. Nexus supplies server simulations, sweep/fold outputs, custom indicators and paper execution. Python validates access, preserves provenance and computes independent statistics. The [capability document](nexus_capabilities.md) distinguishes verified surfaces from missing controls; exact schemas/signatures are tracked alongside it.

## Specifications and stages

The [template](../experiments/_template/README.md) describes every required field. Inner Validation is inside Development, while outer Validation and historical Test are later disjoint windows. All sources and universe membership require point-in-time assertions; unestablished availability blocks freeze. Assertions still need evidence from filing/publication timestamps and vendor revision policies, not just a checked boolean.

Stages are strictly sequential:

```text
DRAFT -> HYPOTHESIS_FROZEN -> DEVELOPMENT -> CANDIDATE_FROZEN
      -> VALIDATION -> WALK_FORWARD -> ROBUSTNESS
      -> TEST_AUTHORIZED -> TEST_COMPLETE -> PAPER_AUTHORIZED -> PAPER
```

- Hypothesis freeze hashes the complete specification, including costs, ranges, budgets and methodology. Editing it later fails verification; use a new experiment for a changed hypothesis.
- Candidate freeze requires an independently assessed eligible Development trial, highest eligible declared primary metric, complexity limits, counted control evidence and frozen explicit benchmark portfolios. Full inline portfolio snapshots are hashed; subsequent evaluations cannot substitute altered snapshots.
- Validation/Test progression requires completed candidate and explicit benchmark jobs. Failed or unresolved jobs block progression. Walk-forward training and held-out folds stay inside Development and must respect chronology/embargo and nonoverlapping held-out periods.
- Robustness must have recorded scenario evidence before Test authorization. Missing tests remain `not_run`; they are never filled with guessed results. The owner reviews these results during the authorization decision.
- Test needs a reviewed `robustness.json` matching the frozen hashes and the interactive owner string **`OPEN EXP002 TEST`**. Paper needs a separate reviewed `final_review.json` and **`DEPLOY EXP002 PAPER`**. Noninteractive authorization is rejected. Automation must not type these confirmations for the owner.
- Paper deployment uses the observed SDK paper method only and requires a saved draft exactly matching the frozen portfolio. Server-added fields that cause mismatch require explicit review; no fields are silently discarded. A prior submission marker blocks retry because deploy has no idempotency key. No live stage, brokerage connector or order submission adapter exists.

This is application-level enforcement, not a sandbox against someone modifying Python, SQLite or review files. Approval provenance is local; no server human-identity attestation was exposed. Git preserves the tracked audit records, but the working filesystem remains under owner control.

## Commands

Install with `python -m pip install -r requirements-research.txt`. Run from the repository root with Python 3.11+ (verified on 3.13):

| Command | Purpose / required evidence |
|---|---|
| `python -m src.research propose EXP002` | Create an editable local DRAFT; TODO fields intentionally block freeze; no Nexus call |
| `... audit EXP002` | Validate schema, windows, PIT declarations and freeze integrity |
| `... research EXP002` | Generate five role prompts with cutoff and provenance; no remote Aurora job |
| `... freeze-hypothesis EXP002` | Freeze the complete specification |
| `... develop EXP002 --candidate candidate.json` | Enter Development and plan a bounded inline simulation |
| `... optimize EXP002 --candidate candidate.json --job-config sweep.json` | Declared exhaustive sweep with reviewed compiled SDK handle |
| `... resume EXP002 --job-key KEY` | Resume reads/extraction of the existing operation, never another submission |
| `... assess EXP002 --job-key KEY --input assessment.json` | Independent close metrics plus trade, participation and breadth eligibility evidence |
| `... ingest-surface EXP002 --job-key KEY --input normalized_cells.json` | Preserve every successful, failed or unresolved cell from an audited complete raw sweep; independently assess successful cells |
| `... freeze-candidate EXP002 --candidate candidate.json` | Freeze eligible winner and explicit benchmark/control snapshots |
| `... validate EXP002` | Plan frozen outer Validation; `--benchmark NAME` evaluates its frozen benchmark |
| `... walk-forward EXP002 --job-config walk_forward.json --folds N --evaluations N` | Observed SDK fold job handle; requires completed Validation |
| `... stress EXP002 --input stress_results.json` | Record predeclared scenario observations; do not fabricate cost/delay/universe reruns |
| `... authorize-test EXP002` | Owner-only interactive confirmation after evidence review |
| `... test EXP002` | Plan authorized Test; also run each `--benchmark NAME` before completion |
| `... report EXP002 --input report_bundle.json` | Generate independent metrics, card, candidate/benchmark tables, stress matrix and figures |
| `... evaluate-agent EXP002 --agent-id ID` | Optional MCP process-grading request plan; quote needed before any execution |
| `... authorize-paper EXP002` | Separate owner-only authorization after final report review |
| `... paper EXP002 --paper-portfolio ID` | Plan a checked paper deployment; no live equivalent |
| `... demo EXP999 --dry-run` | Fully temporary synthetic job, pagination, immutability and idempotency smoke test |

Every command supports `--dry-run`: state/report writes occur in a temporary workspace, and remote execution is disabled. A dry run previews one command against current persisted gates; it does not fabricate completion of earlier stages. `--dry-run` and `--execute` are mutually exclusive. Without `--execute`, job commands only plan (local stage transitions can still be persisted when not dry-running).

Remote simulation execution additionally needs `--execute`, an explicitly exported `NEXUSTRADE_API_KEY`, and `--mcp-bridge your_module:call`. The bridge is an authorized callable `call(tool_name, arguments) -> raw MCP response`, using the exact [observed declarations](nexus_mcp_inventory.json). No OAuth token is loaded or invented, no SDK anonymous workspace is created, and no guessed REST history endpoint is used. This setup task did not install a credentialed bridge or invoke one.

Sweep/walk-forward handles must use actual fields from the Nexus surface/preview, not names guessed from a parameter label. The CLI will return a required-evidence plan if no compiled handle is supplied. V1 execution accepts a bounded exhaustive typed gene grid matching the frozen ranges, with explicit `num_windows: 1`; generational or amplified multi-window plans require a reviewed planner extension. Remote optimizer/study execution also requires a normalized `server_preview` sidecar containing `payload_hash` (the local canonical digest of `{portfolio, args}`), `planned_evaluations`, `estimated_tokens`, and `expires_on`. This is local provenance from an authorized actual Nexus preview, not an invented server endpoint. Keep the full original preview in private raw storage and audit the normalization. Inner selection belongs inside Development, never outer Validation. `validate_folds` ingests explicit fold definitions, selected parameters and metrics, rejecting chronology/overlap failures. Raw engine surfaces are retained in full; normalization into the local surface/fold contracts is explicit rather than silently assuming an undocumented result shape.

## Inputs, extraction and provenance

- Candidate JSON contains `name`, `family`, `signals`, `signal_count`, `parameters`, inline `portfolio`, `trial_key`, `control_evidence` trial keys, and `benchmarks` mapping declared names to inline portfolios. Relevant controls comprise the simple benchmark, all single signals, full composite and leave-one-out ablations. Record `parameters.signals` on each control trial so distinct ablations can be checked; repeating one trial key does not satisfy the requirement. Failed controls remain in the ledger.
- Assessment JSON contains `closes`, `completed_trades`, `participation`, and `breadth`. Each close contains `date`, UTC `timestamp`, `portfolio_value`, and `close_evidence_timestamp`. It must match verified exchange/market evidence, be a regular 16:00 or evidenced 13:00 New York close, and stay in the authorized window. Source-normalization and close/calendar evidence need review; the metric function does not manufacture missing market evidence.
- Report bundles contain named `runs` with `stage` and `closes`, `limitations`, `interpretation`, optional benchmark interpretation, full parameter `surface`, `folds` and `stress` results. Missing studies are displayed honestly. `review_complete` is an explicit owner-reviewed assertion for the final paper review; default false. Figures and metrics are generated from these supplied observations.
- SQLite state is private under ignored `.research/`; each update exports tracked `experiments/<ID>/state.json` and `trials.json`. A clone does not inherit local approval authority automatically. Never delete failed trials or unresolved keys.
- Job keys hash logical request, stage and frozen spec. Reserve before transport. If the response is lost, mark `UNKNOWN`, retain the key and billing reservation, and never blindly resubmit. Read polling can retry only timeouts, connection failures, 429/502/503/504. MCP reads are throttled to two per second with backoff. Definitive failed jobs remain counted.
- History/events are paginated until explicit exhaustion, with final declared row count checks. Save every response field and page request immutably, extract events first when requested, preserve noise/audits, and keep administrative/corporate-action dates separate from simulated timestamps. Unknown pagination/schema fails closed. Interrupted extraction resumes saved pages; existing different bytes cannot be overwritten. A partially written/corrupt page requires manual reconciliation, not replacement.
- A run integrity report records counts, pages, bounds and SHA-256 hashes. Dates are interpreted as New York sessions, with the UTC end boundary extending into the next UTC date when appropriate. No deduplication or daily-close transformation occurs during raw extraction.
- The trial ledger records family, candidate, parameters, run ID, stage, status/metrics and eligibility. Status history is retained, assessed metrics cannot be rewritten, and changing trial provenance is rejected. Sweep jobs retain planned evaluation counts even if full per-cell normalization is pending; full raw surfaces are kept. `ingest-surface` requires an audited normalization tied to the saved response SHA-256, exact coverage of the declared grid including failed/unresolved cells, and successful cells' portfolio/run/close evidence. Each cell gets a durable trial key; counts remain in the parent to avoid double counting. Family and cumulative evaluation ceilings include failed/unresolved trials, and model-selection inference must include every attempted variant, not merely ledger rows.

## Budget and research funnel

The [pricing metadata](../config/research_pricing.json) records official sources, observation date and expiry. Expired pricing blocks jobs. Estimates use calendar days, interval/options class, event multiplier, asset factor, grid size, fold multiplier and optimizer minimum; they are not invoices. Quote Aurora separately, including its USD ceiling. Server previews can supply exact planned evaluation/token estimates to the budget module; no account pricing endpoint was exposed in the SDK/schema inventory.

The default funnel is audit without performance search; daily non-options Development screen; bounded parameter stability; frozen Validation; chronological walk-forward; robustness; human-authorized historical lockbox; separately authorized forward paper. Intraday/event-heavy work requires a hypothesis/execution rationale and its own ceiling. Do not divide a minute run to evade the observed warmup-inclusive 730-day cap.

## Robustness, statistics and contamination

Parameter surfaces retain every cell, best cell, adjacent declared-grid perturbations, neighbour average, range-normalized sensitivity, plateau fraction and isolated-optimum warning. Rank stability uses adjacent-fold Spearman correlation with average ranks for ties. These diagnostics do not silently choose a new winner.

The gauntlet ingests genuine transaction-cost, additional-bar delay, changed-universe, cadence and parameter reruns. Regime summaries require supplied bull/bear, high/low volatility and rate labels with availability evidence. Nonadjacent regime closes are never stitched into invented equity/drawdown series. No rate classification or execution counterfactual is guessed from returns.

Paired moving-block resampling uses the same indices for strategy and benchmark, fixed seeds and percentile confidence intervals for mean daily excess return. Block length and stationarity assumptions must be predeclared and sensitivity checked; the routine is not an alpha significance certificate. Holm adjustment uses the complete supplied p-value family, with failed/unresolved variants retained rather than removed. See the [step-down implementation reference](https://www.statsmodels.org/v0.13.5/_modules/statsmodels/stats/multitest.html) and [block-bootstrap coverage research](https://arxiv.org/abs/0804.4361). DSR and PBO/CSCV are deliberately not implemented or claimed; v1 uses Holm as its multiple-testing adjustment and does not invent valid p-values from Sharpe.

Historical workflow holdouts can still be known to modern models. Corpus mining is hypothesis evidence only: recorded candidate-formation backtests must end by the research cutoff. Arbitrary SQL is not automatically declared safe just because it contains a date literal; bounded queries and row availability require audit. Never copy the historical highest-Sharpe strategy as evidence of alpha. Forward paper after freeze is the strongest genuinely unseen evidence, subject to executable cost/market assumptions.

## Aurora boundary and remaining integration gates

Save every Aurora response immediately when received, before claim auditing or specification updates. Preserve its text verbatim as a numbered artifact:

```text
experiments/EXP002/research/
├── aurora_research_memo_001.md
├── aurora_research_memo_002.md
└── ...
```

Use the next unused number after the highest existing number; never overwrite originals. Follow-ups, corrections, incomplete responses, and negative findings each receive their own file. Keep verification and interpretation separate, and link each artifact and its SHA-256 in experiment provenance with known source, receipt date, session reference, and access bounds. Unknown metadata stays explicitly unknown. Existing legacy memos retain their paths and references.

These research artifacts enter Git through the repository's normal review, commit, and push workflow. Credentials and private raw datasets remain in ignored storage; clearly label any tracked redacted copy. Manual Aurora responses must be supplied to Codex for capture; this policy does not automatically intercept external chats or enable remote Aurora execution.

Five independent roles generate complete stored prompts: researcher, data auditor, architect, skeptic and execution reviewer. Trajectory ingestion preserves original outputs under private raw storage after request-scope audit. The optional evaluator plan asks for ten process dimensions (hypothesis, data, PIT, simplicity, falsifiability, benchmark, confounders, execution, novelty and ablation), with feedback; return is not the objective.

Remote Aurora launching remains explicitly blocked: the observed SDK cannot restrict tools or sealed dates. Implementing unattended launch would defeat the requested protection. A future server-enforced isolated role environment, current cost quote, and budget reservation are prerequisites. Trajectory/evaluator plans are not presented as already completed research runs.

Before any real experiment execution, the owner must supply a genuine hypothesis/PIT audit, reviewed portfolio/control and benchmark snapshots, authorized extraction bridge, compiled Nexus sweep/fold configurations, fresh pricing, and normalization of actual engine surfaces into reviewed local evidence. Test and paper remain distinct interactive human gates. No new experiment or live capability was activated by infrastructure installation.

## Reproduction

```sh
python -m unittest discover -s tests -v
python -m src.research demo EXP999 --dry-run
python -m src.presentation.exp001 --check
```

The EXP999 demonstration writes only to a temporary directory and submits to in-process fake transports. Existing EXP001 tests still require the private raw files; public clones can run `python -m unittest discover -s tests -p test_research_os.py -v` and the synthetic demo. Completed future reports update `experiments/registry.json`, and README generation consumes those cards without altering EXP001 metrics or its final report.

Legacy command examples use historical identifiers to document the interface. EXP002/EXP003 remain closed, EXP004 paused, and no EXP005 draft is authorized. Follow the active roadmap for the next separately approved milestone.
