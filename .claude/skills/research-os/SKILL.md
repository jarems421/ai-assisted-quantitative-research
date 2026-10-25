---
name: research-os
description: Run Research OS on a hypothesis through the deterministic offline operator (Forge archive -> Quarry -> Jev -> Anvil drafts -> Armoury), continue an existing run, or report on one. Use when the user asks to "run Research OS on <hypothesis>", "continue the Research OS run", or "what is blocking <hypothesis>".
argument-hint: "[subject name | archive path + IDEA-id | continue OPR-...]"
allowed-tools: Bash(python -m src.research.operator:*)
---

# Research OS operator

You orchestrate one deterministic local coordinator, `python -m src.research.operator`, from the repository root. It
is **workflow automation, not authority**: it never records a human judgment, acquires a source, calls a model or
provider, opens credentials or promotes research. Do not improvise sequences of component commands; the operator runs
them for the owner. Documentation: `docs/research_operator_v001.md`.

## Steps

1. **Identify the subject** (one profile exists: `FORGE_TO_ANVIL_OFFLINE_V001`).
   - `python -m src.research.operator subjects` lists named subjects from the private
     `.research/operator-v1/subjects.json` (for example `hypothesis-b`).
   - Given an archive path: `python -m src.research.operator plan --archive <dir>` lists its cards. "Latest approved"
     means `ready_review: true`; if no card has one, say so instead of choosing for the owner.
   - If the subject is still ambiguous, ask one question. Never guess an archive path.
2. **Plan**: `python -m src.research.operator plan --subject <name>` (or `--archive <dir> --idea IDEA-...`). Mention
   the predicted blockers in one or two lines.
3. **Run**: the same arguments with `run`. Add `--search <term>` only for terms the user named. The command prints the
   consolidated Markdown report and the run ID (`OPR-...`).
4. **Present the report naturally**: the hypothesis, where it stopped and why, research blockers, software blockers,
   remaining human decisions, and cost/accounting. `STOPPED_AT_BOUNDARY` is a correct stop at a human or evidence
   gate, never success; `FAILED` or `INTERRUPTED` is a problem to explain. Keep research findings and software findings
   separate. Do not add scientific confidence, cost estimates or interpretations the report does not contain.
5. **Ask only for genuine owner inputs**: a decision (revise the card? authorise a campaign?), an owner-supplied
   original, or a human record the owner makes personally. Quote the exact command the report gives the owner.
6. **Continue** when the user says the inputs exist: `python -m src.research.operator continue OPR-... [--evidence
   <evidence.json>] [--ledger <ledger.jsonl> --candidate CAND-... --crosswalk <crosswalk.json>] [--search <term>]`.
   It resumes orchestration only; recorded one-shot stages are never replayed. A supplied candidate stays `UNLINKED`
   until a human crosswalk binds it to the card. If `continue` is refused for **implementation drift**, explain it
   and offer a fresh `run`; only the owner may choose `--accept-implementation-drift <digest>`. Never pass that flag
   on your own initiative.
7. **Re-read** at any time: `status OPR-...` or `report OPR-...` (`--json` for structure).

## Never

- Author, draft or "help fill" any human or evidence record for the owner: Scout revision, feasibility or READY review;
  Quarry registry, supply or inspection excerpts; Discovery campaign, observation, candidate, M/H review or
  disposition; or a Forge-to-Anvil crosswalk (including completing `crosswalk-template.json`). If the owner wants
  one, they write it and run the command the report names.
- Call component commands yourself to push a stage forward (for example `opportunity_scout review|revise|feasibility`,
  `discovery add|disposition`, `quarry_v1 import-file|export`, `jev_navigation_* import-response|prepare`,
  `automation_v001 run`, `exploratory_v001 run`, `critic_v1 import-response`) or start a Claude Code, Codex, Gemini or
  Jev session. The operator refuses those internally; do not route around it.
- Open `*.bin` files, `raw/` folders, stdout/stderr captures, `.env` or any credential file, or paste raw model
  responses into the conversation. Report hashes and statuses instead.
- Remove a `journal.lock`, edit a journal, delete run or archive directories, or retry an `INTERRUPTED` stage. Explain
  the interruption and ask the owner to reconcile it.
- Edit or commit anything under `.research/`. Runs are private and git-ignored.

## Debugging

The report ends with the exact delegated commands. For diagnosis you may re-run only the read-only ones
(`validate`, `card`, `status`, `report`, `validate-export`) on the run's working copies, never on an original archive.
`python -m src.research.operator doctor` checks dependencies, required files and the network/process boundary.
`python -m src.research.operator demo` runs the complete chain on synthetic fixtures in a temporary directory.
