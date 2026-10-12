# Repository instructions

This repository builds Research OS, an evidence-native quantitative intelligence system with independent local analysis and downstream execution adapters. Preserve experiment history and distinguish historical simulation, Validation, held-out Test, and future paper/live results.

## Research integrity

- Read the relevant manifest, report, processor, tests, and canonical processed results before changing an experiment.
- Treat raw research data as immutable. Keep it under ignored `data/raw/`; never edit raw responses or expose large payloads in public documentation.
- Preserve frozen strategy definitions, metric definitions, selection rules, evaluation windows, and regression baselines. Do not tune methodology after seeing held-out results.
- Nexus operations require task authorization. Local documentation and analysis tasks do not authorize new backtests, trades, portfolio changes, optimization, or additional experiments.
- EXP001 is complete. Its manifest retains a historical sealed-Test marker; the final report records the subsequent authorized one-time opening. Do not rewrite the historical manifest to resolve that distinction.
- Report negative and mixed findings honestly. Reducing volatility or drawdown is distinct from outperforming a benchmark; do not claim alpha without supporting evidence.

## Repository presentation

- Keep the repository understandable to a first-time reader. Public documentation should be concise, visually clean, technically credible, and free of internal clutter.
- Prefer explanatory tables, useful charts, diagrams, and links to deeper documentation over raw dumps or unexplained JSON.
- Give every completed experiment a human-facing summary with benchmark, costs, evaluation windows, selection rule, and limitations. Explain important numbers in context.
- Keep `README.md` current when the project meaningfully changes: explain the objective, architecture, completed work, current findings, and reproduction commands.
- Update the experiment registry and headline findings when experiments finish. Generate numeric tables from canonical processed results instead of manually duplicating values.
- Human-facing outputs need meaningful labels, units, dates, and explanations of ambiguous metrics. Preserve canonical filenames and experiment IDs unless a justified change is explicitly authorized.
- Use restrained, consistent chart styling, descriptive titles, labelled axes, readable dates, legends where needed, and clear captions. Avoid decorative charts and misleading scales.
- Generate figures and tables reproducibly from processed data. Document their commands and dependencies; identify what can be reproduced without private raw data.

## Git and GitHub workflow

- Treat Git history as part of the deliverable.
- At the beginning of meaningful work, inspect `git status`, the current branch, and configured remotes.
- Do not overwrite, discard, reset, or stage unrelated user changes.
- After completing a meaningful unit of work and verifying it, create a Git commit.
- For larger tasks, make multiple logical checkpoint commits rather than one giant final commit when appropriate.
- Use concise, descriptive commit messages explaining what changed; avoid vague messages such as `updates`.
- Stage only files relevant to the completed work.
- Run the relevant tests/checks before committing whenever the project has them.
- Before committing, inspect the staged diff for accidental secrets, generated junk, or unrelated changes.
- Never commit `.env`, API keys, credentials, secrets, ignored raw data, temporary extraction files, caches, or other files excluded by `.gitignore`.
- After a successful commit, push it to the current tracked GitHub branch when a GitHub remote is configured and authentication is available.
- If the current branch has no upstream, set an appropriate upstream on the first safe push.
- Never force-push, use destructive resets, rewrite published history, or amend already-pushed commits unless the user explicitly requests it.
- If a push is rejected because the remote has diverged, do not force it. Stop, inspect the situation, and tell the user what needs resolving.
- If tests fail, do not hide the failure. Fix failures caused by the current work; otherwise report the existing failure before deciding whether to commit.
- An explicit instruction not to commit or not to push overrides this default.
- At the end of each completed task, report the commit message, commit SHA, branch, whether it was pushed successfully, and tests/checks run. If Git or a remote is missing, report the blocker accurately; do not imply a commit or push happened.
- If Git, a remote, or an upstream is missing, explain exactly what is missing before taking account-level or remote-creation action. Do not invent a GitHub destination or publish private material.

## Local checks

- Run the research suite with `python -m unittest discover -s tests -v`. Integration tests require the ignored raw EXP001 files and regenerate existing outputs deterministically.
- Reproduce the existing local analysis with `python -m src.nexus.process_exp001` only when the task authorizes processing; it does not call Nexus.
- Generate public presentation artifacts with `python -m src.presentation.exp001`; verify them with `python -m src.presentation.exp001 --check`.
- Documentation work must leave raw files, experiment manifests, canonical processed results, and frozen metric code unchanged.

## Research OS v1

- New research uses `experiments/<ID>/spec.json` validated against `experiments/_template/spec.schema.json`; never migrate or rewrite immutable EXP001 results through Research OS.
- Follow the sequential gates and frozen specification/candidate hashes. Development access and candidate-formation corpus evidence cannot extend past the declared research cutoff. Validation cannot retune the candidate.
- Historical held-out data is `workflow_held_out`; modern AI may know historical events. Only forward evidence after freeze may be described as `genuinely_forward_unseen`.
- Never execute or supply the owner-only interactive Test or paper confirmations on the user's behalf. These are separate human decisions, even when broader research automation is authorized.
- Live trading has no Research OS path. Do not add brokerage/order operations to bypass this boundary.
- Aurora prompts are not access control. Remote Aurora stays disabled until an audited server-side tool/date isolation capability is available.
- Require current cost metadata, explicit execution opt-in, predeclared evaluation ceilings, and an extraction bridge before remote jobs. Preserve uncertain submissions and reconcile their existing IDs; never blindly resubmit.
- Use an already authorized included research allowance actively for bounded verification and auditability; do not request renewed approval for small calls within its scope and ceiling. Record estimates, actual debits when observable, and unknowns. Be generous with computation and strict with degrees of freedom: no unbounded strategy mining, retrospective grid changes, or early held-out access. An audit allowance does not authorize candidate studies, deployment, credit purchases, or later phases.
- Count all families, planned evaluations, failures, and poor results. Keep raw responses immutable and private; track specs, trial summaries, cards, reports, tests, and code.
- Infrastructure demonstrations must use synthetic EXP999 in temporary directories with fake transports. Do not start EXP002 during setup or tests.

## Aurora research artifacts

- Save every Aurora response immediately upon receipt, before auditing, summarizing, or updating the experiment specification. This includes manual responses supplied by the user, follow-ups, incomplete responses, and negative findings.
- Save the original response verbatim under `experiments/<ID>/research/aurora_research_memo_<NNN>.md`, starting at `001` and incrementing the highest existing number. Never overwrite or reuse an artifact number; corrections and later responses get new files.
- Keep interpretation, claim verification, and VERIFIED / PROPOSED / UNRESOLVED labels in separate provenance or analysis files. Link the original artifact and its SHA-256 in experiment provenance; record source, receipt date, session reference, and access bounds when known, and mark unknown metadata explicitly.
- Track research memos in Git using the Git and GitHub workflow above. Credentials or private raw datasets must remain in ignored private storage; any tracked redacted copy must be identified as such and reference the private original without exposing it.
- Preserve existing legacy memo paths and provenance references. Archival does not authorize Aurora execution, spending, performance queries, or access beyond the experiment cutoff.

## Governing direction: 2026-10-12

- Follow `docs/acceleration/master_plan.md` and the complete owner plan linked there until the owner changes direction. Older phase documents are historical evidence, not current execution authorization.
- Research OS is canonical for source state, historical population/identity, availability, contracts, trial accounting and inference. Nexus is downstream and historical execution remains blocked.
- Phase 3D permits bounded source certification, a minimal proof compiler, synthetic inference revision and a local reference execution spine. Use synthetic EXP999 in temporary directories for compiler/execution demonstrations. Do not create EXP005 or inspect real signal rankings/strategy performance.
- Keep failed Phase 3C calibration and single-concept feasibility evidence immutable. New pre-performance contracts get new versions and review receipts; never broaden tags or dates silently.
- Availability requires an explicit recorded owner decision. A modeled eligibility bound does not certify exact public availability or resolve acceptance clock uncertainty.
- EXP004 remains operationally paused. No remote Nexus/Aurora, support message, purchase, Orbis scraping, sealed-stage access, optimizer or paper/live operation is included in Phase 3D.
- Stop after Phase 3D reporting and verified commits/pushes. Phase 4A, the temporal graph, causal lab, portfolio layer and forward operations each require their own milestones and authorization.

## Phase 3E scope disposition

- The owner-authorized Phase 3E is separate from Phase 3D. Its complete request is archived in `docs/acceleration/owner_phase3e_2026-10-12.md`; the bounded plan and early-stop report use a new namespace and preserve all earlier evidence.
- Phase 3E stopped under owner section 37 at incompatibility between the existing twelve-year programme and the approved 2015–2021 pilot policy. EXP005 feasibility is REDESIGN_REQUIRED, freeze readiness NOT_READY. Source acquisition and inference v003 were deferred, not performed or certified.
- Reuse the exact approved pilot policy without requesting its approval again. A wider policy or a reviewed staged horizon is a separate owner decision; do not infer it from this roadmap. No real signal/performance, EXP004 resume, EXP005 creation or Phase 4A is authorized by the early-stop artifacts.

## Phase 3E-R redesign

- The owner authorized replacing the old mandatory 6/3/3 programme, bounded filing/header/calendar acquisition and synthetic stage/inference comparison. Preserve earlier Phase 3E reports as historical evidence; use `docs/acceleration/phase3e_redesign_report.md` and the exact owner request for this new scope.
- The owner approved exact v003 hash `438d7bcf7d091f596009ba841e6dacbd960c18493c34ffec798d8c1aaf1dacbd`, scope 2018-02-28 through 2026-09-30, conditional Stage C and the hierarchy/materiality semantics for planning/design only. See `docs/acceleration/availability_policy_v003_owner_decision.md` and its separate receipt. Preserve the historical proposal, v002 and its approval unchanged. V003 is NOT_ACTIVATED; exact public availability stays UNKNOWN and the Salesforce conflict stays unavailable. No real eligibility/performance or next-phase permission is implied.
- Preserve both v003 calibration runs and the analytical AR-generator correction receipt. Do not remove failed methods/worlds or claim synthetic power certifies real annual independence, accounting, class identity, population coverage or execution.
- The separate owner decision is now recorded; stop after verified approval documentation/commits/pushes pending a new bounded instruction. All remaining scientific gates stay fail-closed. EXP004 remains paused and EXP005 absent/NOT_READY; no real source-certification campaign, strategy calculation, heldout opening, Nexus/Aurora, purchase, optimizer, paper/live or Phase 4A is authorized by the planning/design approval.
