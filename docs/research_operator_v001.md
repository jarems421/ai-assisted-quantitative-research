# Research OS operator V001

> **Workflow automation, not authority.** The operator runs existing offline stages in order, records what each
> one did, and stops at the exact human or evidence gate. It never records a human judgment, acquires a source,
> calls a model or provider, opens credentials, edits an archive or promotes research.

`python -m src.research.operator` is one deterministic local coordinator for the first cross-stage profile,
**`FORGE_TO_ANVIL_OFFLINE_V001`**: Forge archive → Quarry → Jev → Anvil drafts → Armoury. It replaces a manual
sequence of about a dozen component commands with `plan`, `run`, `continue` and `report`. It works with or without
Claude Code; the project skill `.claude/skills/research-os/` only calls it.

## Commands

| Command | Effect |
|---|---|
| `doctor` | Dependencies, required files, `.research/` ignore rule, git revision (read from metadata files) and a network/write boundary self-test |
| `subjects` | Named subjects from the private, git-ignored `.research/operator-v1/subjects.json` |
| `plan --subject NAME` or `--archive DIR [--idea IDEA-…]` | Lists the archive's cards, the stages, limits and predicted blockers. Reads a temporary copy of the Scout ledger; writes nothing to a run |
| `run …` | Creates run `OPR-…` and executes every eligible stage, then prints the consolidated report |
| `continue OPR-… [--evidence F] [--ledger L --candidate CAND-…] [--search T]` | Resumes orchestration with newly supplied inputs; never replays a one-shot stage |
| `status OPR-…` / `report OPR-… [--json]` | Read the run's journal; write nothing |
| `demo [--out DIR]` | The complete chain on synthetic fixtures in a new directory outside any checkout |

Typical session (Hypothesis B from Forge Pilot 001, with a local subject alias):

```powershell
python -m src.research.operator plan --subject hypothesis-b
python -m src.research.operator run --subject hypothesis-b --search refrigerant
python -m src.research.operator continue OPR-20261025T120000Z-a1b2c3 --evidence C:\owner\evidence.json
python -m src.research.operator report OPR-20261025T120000Z-a1b2c3
```

## Stages and what they delegate to

| Stage | Kind | Delegates to | Stops when |
|---|---|---|---|
| `PREFLIGHT` | CHECK | imports and required files | a dependency or file is missing |
| `FORGE_CUSTODY` | ONE_SHOT | hash the original archive and its critic workspace; byte-identical working copy | the archive is not Scout's, or holds a writer lock |
| `FORGE_RECORDS` | CHECK | `opportunity_scout validate`/`card`, `critic_v1 status`, `automation_v001 status`/`report` | the archive or idea is refused |
| `FORGE_READINESS` | CHECK | `opportunity_scout handoff` on the copy | no human READY review (WAITING_FOR_HUMAN) |
| `QUARRY_IMPORT:<label>` | ONE_SHOT | `quarry_v1 import-file`/`status` on owner-supplied files | files missing, classes mixed, or Quarry refuses |
| `QUARRY_EXPORT:<label>` | ONE_SHOT | `quarry_v1 export`/`validate-export` with a human-authored inspection | no inspection record, identity flags, or an invalid excerpt |
| `QUARRY_EVIDENCE` | CHECK | summary | no owner-supplied evidence (WAITING_FOR_EVIDENCE) |
| `JEV_EVIDENCE` | ONE_SHOT | `jev_navigation_integration_v1 compose-quarry`, `jev_navigation_v1 prepare`/`report` | no validated export |
| `JEV_MEMORY` | ONE_SHOT | Jev `MEMORY_NAVIGATOR` over the Graph memory catalogue | the catalogue's citations are stale |
| `ARMOURY_GRAPH` | CHECK | `graph same-gap` per card requirement; `graph search` per explicit term | — |
| `ANVIL_DRAFTS` | CHECK | draft adapters (below) | always waits for human inspection |
| `ANVIL_CHECKS` | CHECK / ONE_SHOT | `discovery validate`/`checklist`/`source`, Jev `WORKFLOW_NAVIGATOR`, `graph trace` | a real run has no ledger; checklist blockers remain; M is human |
| `DOWNSTREAM` | CHECK | records the boundaries | always NOT_AUTHORISED |
| `INTEGRITY` | CHECK | re-hash every original after each invocation | an original changed (FAILED) |

Jev runs deterministically only: no response is imported, so the inspection queue is the keyword baseline order. The
disabled TypeSafe adapter is never touched.

## Runs, journal and state

Each run has a unique ID and a private workspace under the ignored `.research/`:

| Path | Holds |
|---|---|
| `.research/operator-v1/<RUN>/journal.jsonl` | hash-chained events: request, scope, code revision and implementation digest per invocation, stage claims and results |
| `…/<RUN>/artifacts/` | card copy, Jev inputs, drafts and audits, synthetic preview ledgers, and every delegated command's output |
| `…/<RUN>/reports/report-<head>.json` / `.md` | the consolidated report for that journal head |
| `.research/opportunity_scout/<run>-forge`, `critic-v1-<run>-forge` | working copies of the archive and critic workspace |
| `.research/quarry-v1-<run>/`, `jev-provider-v1-<run>/`, `jev-navigation-v1-<run>/` | component outputs, in the locations their own guards require |

Stage statuses are `COMPLETE`, `FAILED`, `BLOCKED`, `WAITING_FOR_HUMAN`, `WAITING_FOR_EVIDENCE`, `NOT_AUTHORISED`,
`NOT_IMPLEMENTED`, `SKIPPED` (upstream failed) and `INTERRUPTED` (claimed, never finished). The run outcome is
`FAILED`, `INTERRUPTED` or `STOPPED_AT_BOUNDARY`; it is never "complete", because this profile ends at human Anvil
gates.

- A **ONE_SHOT** stage is claimed in the journal before it acts and is never re-run for the same inputs. An
  unfinished claim stays INTERRUPTED until a human reconciles it.
- A **CHECK** stage is read-only (or create-only into the run directory) and is re-evaluated only when its inputs
  change. New inputs produce new create-only output directories; nothing earlier is overwritten.
- One invocation holds `journal.lock`. A lock left by a crash is never removed automatically.
- Reports are rendered from the journal alone, so the same records always give the same report.

## Supplying evidence

Quarry has no acquisition dispatcher. The owner obtains originals under separate authority and names them in an
evidence file (paths relative to it):

```json
{"schema": "RESEARCH_OS_OPERATOR_EVIDENCE_V001",
 "routes": [{"label": "R1", "registry": "registry.json", "supply": "supply-R1.json",
             "original": "original.pdf", "inspection": "inspection-R1.json", "extracted_file": "R1.txt"},
            {"label": "R2", "registry": "registry.json", "supply": "supply-R2.json", "original": null}],
 "exports": [{"label": "R9", "path": "<an existing validated Quarry export>"}]}
```

`original: null` is an UNAVAILABLE route (a negative record, kept in the Jev queue and the Source Passport omissions).
`inspection` is the human-authored `QUARRY_INSPECTION_V001`; until it exists, the route waits for a human. Every
supplied file is hashed when supplied and re-checked after each invocation.

## Draft mappings

Two narrow adapters produce reviewable drafts with a field-level audit (`COPIED`, `TRANSFORMED`, `MISSING`,
`UNRESOLVED`):

- Scout handoff envelope → Discovery `candidate` v1 and the card's proposed source requirements. No handoff, no
  candidate draft: drafting without READY would bypass the gate.
- Quarry export → Discovery `source` (Source Passport) v1.

Claim-defining text (population, predictor and outcome quantities, mechanism, falsification) is carried verbatim or
by a stated rule. Anything the Discovery checklist reads as established (units, routes, timing, exposure, clocks)
stays `UNKNOWN`, and the card's proposal is quoted as `UNRESOLVED`. Where a contract needs a boolean or enum the card
does not state, the draft uses the value that adds blockers (for example `allocation_required: true`). Observations
are never drafted: values, units, denominators and the four clocks are read from originals by a human. Drafts are
validated as single records and never appended.

In a **synthetic** run only, the drafts are loaded into a `SYNTHETIC` preview ledger in the run directory to show the
mechanical checklist. A real run's checks need a ledger the owner's campaign created, supplied with `--ledger`; the
operator checks a pinned copy read-only.

## Boundary enforcement

These are enforced in code, not by instructions:

- An audit hook, active for the whole invocation, refuses sockets, process creation and symlinks. It also refuses
  writes outside the run's directories and opening credential or account paths.
- Only listed read-only or create-only component commands are callable. Recording reviews, revisions,
  dispositions or responses, dispatching providers and running pipelines are refused before import.
- Fixture classes never mix: synthetic evidence in a real run, or the reverse, is BLOCKED. A non-human approval in a
  real archive is never treated as READY.

## Testing

```powershell
python -m unittest tests.test_research_operator_v1 -v        # synthetic; also runs in offline CI ("additional")
$env:RESEARCH_OS_PILOT001_ARCHIVE = '<path>\forge-live-pilot-001'
python -m unittest tests.test_research_operator_v1_pilot001 -v   # local only: the real Pilot 001 Hypothesis B
```

The local Pilot 001 test checks the cross-stage protocol's G0, F1.a–d, F2/F3 and R1/R2 assertions:

- every original byte is unchanged;
- the copy validates at head `177addf1…`;
- the economic critique has no imported judgment;
- the legacy receipt is never verified;
- the v1 READY refusal is preserved;
- the run makes zero requests;
- the report is deterministic and `continue` replays nothing.

## Known limits (V001)

- One profile. Real runs stop at the Scout READY gate until the owner revises the card and a human records READY;
  Hypothesis B v1 has a prose source locator, so READY is impossible without a revision.
- No acquisition dispatcher, PDF/OCR extraction, Level A runner or automatic Armoury ingestion. These are reported
  as NOT_IMPLEMENTED.
- The archived pipeline report resolves its plan's relative critic-workspace path against the process directory, so
  it shows no critic subjects for a copied archive. The operator reads criticism from the copied workspace instead
  and reports the discrepancy.
- `worktree_clean` stays UNKNOWN: no git process is launched.
