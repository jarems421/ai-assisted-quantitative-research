# Repository instructions

This repository studies AI-assisted quantitative research using NexusTrade simulations and independent local Python analysis. Preserve experiment history and distinguish historical simulation, Validation, held-out Test, and future paper/live results.

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
- Count all families, planned evaluations, failures, and poor results. Keep raw responses immutable and private; track specs, trial summaries, cards, reports, tests, and code.
- Infrastructure demonstrations must use synthetic EXP999 in temporary directories with fake transports. Do not start EXP002 during setup or tests.
