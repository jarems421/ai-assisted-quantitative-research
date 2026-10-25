---
name: opportunity-scout
description: Run one live Opportunity Scout scan (generation plus scientific and economic critics) through the scan_v001 operator command, or execute an existing prepared Scout plan such as Pilot 002. Use only when the user explicitly asks to run a Scout scan, for example "Run Opportunity Scout. Two hypotheses, $1 budget."
argument-hint: "[count and budget | existing plan archive]"
allowed-tools: Bash(python -m src.research.opportunity_scout.scan_v001:*), PowerShell(*scout.ps1*)
---

# Opportunity Scout scan operator

A scan sends prompts to paid or subscription providers and consumes a one-shot attempt. You operate it; the owner
authorises it. Documentation: `docs/opportunity_scout/scan_v001.md`.

## Steps

1. **Plan and check, never run.** From the repository root, in PowerShell:
   `.\src\research\opportunity_scout\scan_v001\scout.ps1 -Count <n> -Budget <usd> -PlanOnly`
   (or `-Archive <existing plan> -PlanOnly`). The shortcut loads the Gemini key from the owner's encrypted store into
   its own process only. Never pass `-Count`/`-Budget` with `-Archive`.
2. **Report the summary exactly**: plan hash, archive, providers and models (including any requested-only identity),
   request counts, the reservation cap (a software limit, not a charge), disclosure scope, one-shot risk and every
   `WARNING`/`BLOCKED` line. If anything is blocked, stop and explain; do not work around a blocker.
3. **Wait for the owner's explicit confirmation of that exact plan hash in the conversation** (for example "run plan
   4ed332eb…"). A general request to scan, an earlier approval, a different hash or your own judgment is not
   confirmation. Never type `RUN …` or pass `-Confirm` on your own initiative.
4. **Run once** with the confirmed hash, in the background (it can take many minutes):
   `.\src\research\opportunity_scout\scan_v001\scout.ps1 -Archive <archive> -Confirm <full plan hash>`
   Do not start or close Claude Code sessions or change settings while it runs.
5. **Report status only**: the printed outcome and `python -m src.research.opportunity_scout.automation_v001 status
   <archive>`. Do not open critic records or the pipeline report if a blind QB001 assessment is pending.

## Never

- Re-run, retry or resume a claimed plan, or plan a replacement after a failure without the owner asking.
- Edit a plan, the configuration's owner, the authorisation, frozen prompts or archives; or fill an authorisation by hand.
- Read, print or copy API keys, `%LOCALAPPDATA%\ResearchOS\*`, credential files or raw `*.bin` model output.
- Treat a critic PASS, a recommendation or a finished run as READY, M/H, evidence or investment advice.
