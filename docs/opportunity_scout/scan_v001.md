# Opportunity Scout scan V001: one operator command

> **Operator convenience only.** `scan_v001` plans (or loads), checks, confirms and runs the merged research pipeline
> (`automation_v001`) once. It adds no generation, rubric, archive, provider, spend or policy logic, and it never
> retries, resumes, substitutes a model or approves anything without the owner's confirmation of the exact plan hash.

Code: `src/research/opportunity_scout/scan_v001/` (`scan.py`, `__main__.py`, optional `scout.ps1`).
Tests: `tests/opportunity_scout/test_scan_v001.py` (offline, pipeline fixtures).

## Use

```powershell
# Once: settings copied from a reviewed plan (no secrets), and the Gemini key stored DPAPI-encrypted for this Windows user
python -m src.research.opportunity_scout.scan_v001 configure --owner "<your name>" --from-plan .research/opportunity_scout/forge-live-pilot-002 --prices-valid-until 2026-11-30
powershell -NoProfile -ExecutionPolicy Bypass -File .\src\research\opportunity_scout\scan_v001\scout.ps1 -SetGeminiKey

# Every scan: one command (plans a new archive, checks it, asks you to type RUN <hash prefix>, runs once)
powershell -NoProfile -ExecutionPolicy Bypass -File .\src\research\opportunity_scout\scan_v001\scout.ps1 -Count 2 -Budget 1

# An existing unclaimed plan (for example Pilot 002) instead of a new one
powershell -NoProfile -ExecutionPolicy Bypass -File .\src\research\opportunity_scout\scan_v001\scout.ps1 -Archive .research/opportunity_scout/forge-live-pilot-002
```

Run these from the repository root. Windows' default execution policy (Restricted) refuses `.\scout.ps1`;
`-ExecutionPolicy Bypass -File` applies only to that one process and changes no system setting.

`-PlanOnly` stops after the checks and summary. `-Confirm <full plan sha256>` confirms non-interactively; use it only
with a hash the owner has explicitly confirmed (this is how Claude Code operates a scan, see the
`opportunity-scout` skill). Python equivalent: `python -m src.research.opportunity_scout.scan_v001 scan [--count N]
[--budget USD] [--archive PATH] [--plan-only] [--confirm HASH]` with `GEMINI_API_KEY` already in the environment.

## What it does

1. **Plan** (new scans only): `automation_v001.pipeline.plan` into `.research/opportunity_scout/scout-scan-<UTC stamp>`
   with the configured models; an existing path is refused, never overwritten.
2. **Check** before anything is claimed, using the run's own functions: plan integrity and that the attempt is still
   pending and unclaimed; Claude binary hash and the runner's preflight (`--version`, `--help`, `auth status`
   categories, research configuration, allowed subscription, optional account pin); Codex binary hash and preflight
   (`--version`, `login status`, `exec --help`); Gemini key **presence** only; prices still valid; the spend cap covers
   the planned Gemini reservations; and a short quiet window on the development-account files (below). No model is
   called. Any failure prints `BLOCKED` and nothing is started.
3. **Confirm**: one summary with the plan hash, provider identities, request counts, the reservation cap, disclosure
   scope and one-shot risk. Interactively you type `RUN <first 12 characters of the plan hash>`.
4. **Run**: the owner authorisation is built from the plan's own template with the configured owner and the actual
   local time, validated by the pipeline's and runner's own checks, and written create-only with a confirmation record
   to `.research/opportunity_scout/scan-v001/<archive>/`. Then `pipeline.run` is called once and `result.json` records
   the status. A plan that already has an authorisation or claim is refused; nothing is re-run.

## Sessions and accounts (investigated 2026-10-25)

The generation runner stats `~/.claude.json`, `~/.claude/settings.json` and `~/.claude/.credentials.json` before
generation and after it; any change stops the run (`DEVELOPMENT_ACCOUNT_METADATA_CHANGED`) and consumes the attempt.
During a three-minute stat-only observation with an active Claude Code session working normally, none of these files
changed, so open sessions are not in themselves a conflict. Starting or closing a session, changing settings or a token
refresh during the run could change them, so the check observes them for `quiet_seconds` and blocks if they move, and
the command asks you not to start or close Claude Code sessions while it runs. Codex sessions do not interact with a
tripwire: the critic uses `--ephemeral` with the configured `CODEX_HOME`. Child processes receive allowlisted
environments, so unrelated API-key variables in the terminal are never passed to the Claude or Codex CLIs.

## Secrets

The configuration names only the key variable (`GEMINI_API_KEY`). `scout.ps1 -SetGeminiKey` stores the key with
`ConvertFrom-SecureString` (Windows DPAPI, current user) under `%LOCALAPPDATA%\ResearchOS\`; each run decrypts it only
into that process's environment and removes it afterwards. Python checks presence, never reads or prints the value;
the pipeline reads it only when sending a Gemini request.

## Limits

- The confirmation is an owner assertion bound to the configured name, not an authenticated identity.
- Anything the plan binds (models, counts, cap, executables) is fixed once planned; change the configuration and plan
  again rather than editing a plan. A changed binary blocks the check.
- The 6,000-token generation budget is unchanged; a count whose observed size approaches it is warned about.
- Outcomes after the claim (budget overrun, provider faults, interruption) are recorded by the pipeline and never retried.
