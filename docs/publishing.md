# Publishing and Git setup

The initial local audit found no Git repository. This project is now configured for `jarems421/ai-assisted-quantitative-research`, with `main` as the working branch. The workflow in [AGENTS.md](../AGENTS.md) governs future commits and pushes. The repository was created private and subsequently made public with owner authorization after auditing all tracked history for credentials and private data. Licensing remains a separate decision.

Choose an existing GitHub repository or create a destination with the intended visibility first. Do not publish the workspace wholesale. The local `.env`, ignored raw Nexus data, parquet exports under `lake-results/`, extraction checkpoints, and caches must remain private. Review other existing scripts and local configuration before including them in an initial commit.

For a different new, empty destination, the local setup would be:

```sh
git init -b main
git remote add origin <your-github-repository-url>
git status --short
```

Review and stage an explicit list of intended public files. Check `git diff --cached`, run the relevant checks, and commit. Then:

```sh
git push -u origin main
```

If the destination already has history, clone it into a separate directory and integrate the reviewed files there rather than creating competing initial history. Do not force-push. Never put an access token in a remote URL; use your GitHub authentication mechanism.

`.gitattributes` preserves exact file bytes, including line endings, because the frozen regression baseline verifies source and output SHA-256 hashes. Do not normalize those files on checkout or commit.

## Suggested GitHub presentation

- Description: “AI-assisted quantitative research with frozen out-of-sample evaluation and independent Python statistics.”
- Topics: `quantitative-finance`, `systematic-trading`, `research`, `backtesting`, `python`, `reproducibility`.
- A license requires an explicit owner choice and a review of redistribution rights for source data and derived artifacts. No license has been invented; public visibility alone does not grant an open-source license.
- Issue templates and a separate contribution guide can wait until there is an actual collaboration process. Research changes must preserve frozen results and document their experimental scope.

## Reproduction and public-data boundaries

Published processed CSVs and `metrics.json` suffice to regenerate the README tables and four figures. The full research processor and integration tests additionally require the ignored raw histories, events, metadata, and integrity reports in `data/raw/EXP001_SPY_AI_SELECTION/`. A public clone cannot independently re-extract or verify those private inputs without obtaining them separately. Publishing does not authorize new Nexus calls or backtests.

CSV `date` is the New York session date; `timestamp` is the selected close in UTC. `portfolio_value`, `cash`, `position_value`, `comparison_value`, and `reserved_collateral` are dollar values. The explicit SPY benchmark comes from its own portfolio CSV, not `comparison_value`. Metrics use return fractions except fields explicitly labelled percent; public tables convert fractions to percentages. Maximum drawdown is shown as a positive loss magnitude; drawdown charts plot negative distance from each period's running peak.

The manifest's `SEALED` status is a preserved historical record. The final report and processed Test results document the subsequent authorized opening; this presentation task does not change the manifest or experiment history.
