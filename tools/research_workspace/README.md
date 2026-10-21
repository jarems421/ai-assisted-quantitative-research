# Your research workspace

A quiet, personal reading workspace for Research OS. Warm paper, sage accents, comfortable spacing, a focused graph, and an optional evening theme. Everything scientific comes from the existing public repository records.

## Open it locally

Requires Python 3.11+, Git, and Node 22.12+ (tested with Python 3.13 and Node 24). From this worktree:

```powershell
cd C:\Users\runni\quant-research-workspace\tools\research_workspace
python -m pip install -r requirements.txt
npm.cmd ci
npm.cmd run dev
```

Open the printed local URL, normally **http://127.0.0.1:5173**. On macOS/Linux, use `npm` in place of `npm.cmd` and the corresponding checkout path. Existing installations of the Python packages can be reused. Dependency installation requires internet; using the application and regenerating its export require no external service.

For a production build:

```powershell
npm.cmd run build
npm.cmd run preview
```

The preview normally serves **http://127.0.0.1:4173**. Both commands bind to loopback. Stop the server with Ctrl+C. The browser needs a local server; opening `index.html` directly is unsupported.

## What is here

| Place | What you can do |
| --- | --- |
| Your desk | See actual snapshot contents, open the F19 reading note, and find recurring measurement needs. |
| Investigations | Search F01, F03, F09, F19, SH09, EF03 and EF06; filter recorded dispositions; inspect ideas, supporting and limiting findings, missing measurements, evidence-to-change notes, entities and source receipts. |
| Claim history | Inspect every catalogued claim version and its recorded statuses. EF06's restricted gross v2 stays separate from retained-net v1 and never counts as original-claim success. |
| Connections | Search Graph v1 indexed fields, select nodes or edges, refocus, expand to 8/16/30 nodes, filter node/edge kinds, scopes, superseded versions and verified assertions; read the existing operator's first unsupported economic inference. |
| Research memory | Reuse the existing same-gap results; search source limitations; inspect shared-operator abstentions, recorded changes, and evidence needs without reopening investigations. |
| Pilot notebook | Start with an empty state; explicitly import a completed, unsealed report export into tab memory. Display recorded S/G values, analyst time, connections, duplicates, M/H counts, comparison directions and budget violations. |
| Experiment archive | Read fixed public report references for EXP001–EXP007, including the later EXP004 execution-gap and EXP007 House-repair closures. |
| Sources | Open exact included document text, jump to a cited quote, search a passage, and inspect file hashes and citation freshness. Original publisher response bodies are not included. |

Global search opens with **Ctrl+K** or **Command+K**. Dialogs support Escape and native focus containment. Icon navigation retains accessible labels on smaller screens. Theme is the only localStorage preference. The app stores no research notes or decisions.

## How it works

```text
Fixed, tracked public catalogue + cited reports + seven experiment reports
    ↓ allowlist, containment, size, tracking and link checks
export_workspace.py
    ↓ existing Graph v1 build(ledgers=[]), View, and operators
public/workspace.json (generated, ignored)
    ↓ one same-origin read
React + TypeScript + Vite → local browser
```

The deterministic adapter imports existing Graph v1 modules without modifying them. It explicitly passes an empty ledger list: it never discovers or reads campaign ledgers. Historical findings remain historical findings. It exports original operator outputs for neighbourhoods, explanations, trace, gaps, shared, same-gap, changes, next questions, failures and orphans. The UI presents these results and applies text/type filters; it creates no second economic inference engine. `complements` and `revisit` are unavailable because this snapshot contains no original observations.

At the checked-out baseline `7940cde`, catalogue V002 has **7 investigations, 39 findings, 8 requirement classes, 99 graph nodes and 121 structural edges**, with current citations. There are **0 original observation nodes and 0 documented economic relationship assertion nodes**. The export reads no live or synthetic campaign records; empty scopes say what is absent from this export, without asserting what exists on another branch.

`public/workspace.json`, `dist/`, caches, and dependency directories are ignored. Export output is atomically replaced inside this app; inputs remain byte-identical. The browser has no research write API, filesystem API, external API, login, database, crawler, chat agent or acquisition control. All graph output carries the existing derived-view banner.

### Input and serving boundaries

- The adapter accepts no arbitrary CLI input/output paths. Its exact allowlist lives in `export_workspace.py`. Catalogue citation paths are checked before the existing loader runs. Inputs must be tracked regular files under this checkout, not symlinks/junctions, and at most 3 MB each.
- Catalogue path-contract changes fail closed and require a code review. Changed report hashes remain visibly flagged; nothing silently refreshes a citation.
- Neither active arm records, packet snapshots, blind keys, credentials, `.env`, private raw bodies, nor ignored archives are read. Source locators are displayed as text, so opening a receipt never dispatches a scientific-source request.
- React escapes document and import text. There is no HTML/Markdown execution, `dangerouslySetInnerHTML`, iframe, remote font, remote image or CDN. The production CSP limits requests to the local origin (the dev policy additionally permits loopback Vite websockets).
- Vite development filesystem access is restricted to this app directory, with `.git`, `.env` and data paths denied. Production serves only the built app and generated public export, never the repository root.
- Package installation and feature-branch Git delivery are separate development operations; neither grants scientific-source authority.

## Completed pilot report import

The workspace does not run `pilot report`, unblind anything, or locate pilot files. An owner must first complete the authorised pilot/unsealing process outside this app. The file selector is enabled only after the viewer confirms the report is completed, unsealed and authorised for viewing.

Wrap the **unchanged existing `PILOT_PAIRED_REPORT` object** in this exact envelope:

```json
{
  "schema": "WORKSPACE_COMPLETED_PILOT_V1",
  "lifecycle": "COMPLETED_UNSEALED",
  "authorisation": {
    "path": "docs/strategy/owner_completed_report.md",
    "sha256": "<64 lowercase hexadecimal characters from the real owner document>"
  },
  "source_report_sha256": "<64 lowercase hexadecimal characters from the original report file>",
  "report": "REPLACE THIS STRING WITH THE UNCHANGED PAIRED REPORT OBJECT"
}
```

The example is explanatory and deliberately not importable. Do not fabricate owner authority or results. The parser accepts 1–4 unique packet pairs, the current `arm_metrics` fields and comparison directions, known classifications, finite nonnegative metric numbers or null, native decisive-check UNKNOWN/NOT_NAMED states, structured budget violations, and a maximum 1 MB file. Unexpected fields (including arm ledgers or blind keys), active lifecycle states, unsafe authority paths and malformed reports are refused. The file is read in browser memory only and can be removed with one click; reloading clears it.

Authority and source-report hashes are **declared provenance**, not independently verified signatures. The app does not open their paths or certify the owner's lifecycle declaration or scientific judgments. Notes are text, never executable markup. Recorded values/classifications are not recalculated. The native paired-report contract omits source counts, detailed missing evidence and protocol deviations beyond budget violations; the viewer says these are unavailable rather than inventing values. Blinding remains partial under the existing protocol.

## Verification

```powershell
npm.cmd run export
npm.cmd test
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:browser
```

If an appropriate local Chromium is already installed, set `WORKSPACE_CHROMIUM` to its executable path before the browser test instead of downloading another browser. Browser installation is a developer setup step, not a runtime requirement.

Verified in this worktree: **11 Python boundary/export tests, 7 TypeScript contract tests, and 5 Chromium browser scenarios**. The production build and TypeScript check pass. Browser scenarios cover real-record navigation, source passage highlighting, graph bounds and explanations, scope empty states, EF06 reformulation handling, memory filters, safe report imports, mobile overflow, theme switching and keyboard search. The real app made no external browser requests in the monitored desk/source scenario. These checks demonstrate software behavior, not scientific or investment results.

Screenshots from the running production build: [reading desk](screenshots/desk.png), [connections](screenshots/connections.png), [claim history](screenshots/claim-history.png), [mobile](screenshots/mobile.png), [evening](screenshots/evening.png).

## Current limits

This is a static historical snapshot, not a live research monitor. Regenerate with `npm.cmd run export` after separately reviewed changes to its permitted inputs; do not point it at another worktree's live pilot. Existing report text may retain Markdown syntax because the viewer preserves the original bytes as escaped text. Every citation opens inside the fixed local document set.

Connections use a simple bounded layout with an accessible record inspector, zoom and scrolling. Pair explanations are exported for visible investigation neighbourhoods and direct edges. Unexported pairs clearly abstain. Scope, version and assertion filters work on included records; live and synthetic scopes truthfully remain empty. Economic periods not recorded on a node stay unknown; investigation closure dates are labelled as closure dates.

No research conclusions, source stops, M/H decisions, experiments, frozen records or research-engine code are changed. The entire implementation stays under `tools/research_workspace/` on `codex/research-workspace`, in a separate worktree. No merge or push to `main` is part of delivery.
