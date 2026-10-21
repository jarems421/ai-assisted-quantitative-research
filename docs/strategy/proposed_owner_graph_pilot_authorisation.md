# PROPOSED owner authorisation: first Discovery Lab + Graph v1 pilot (revision 2)

> **STATUS: PROPOSED, NOT ACTIVE.** This document authorises nothing in its current form.
>
> **How it would be activated:** the owner copies it to `docs/strategy/owner_graph_pilot_<date>.md`, edits the bracketed choices, removes this banner, and states activation in their own words. That activated text is committed and pushed before any source request.
>
> **What still requires that activation:** every source request, campaign ledger, search query or packet freeze.

This pilot executes the [pre-registration, revision 2](graph_pilot_preregistration.md). The reasons for the pilot are in the [review](graph_v1_review.md), and its corrections in the [protocol instruction](owner_graph_pilot_protocol_2026-10-21.md). Every command in section 6 ran against the implemented CLI in the [synthetic dry run](graph_pilot_dry_run.md).

## 1. Scope

- **Pilot size:** 4 starting packets (one per Discovery Lab method) × 2 arms (S: structured-ledger search; G: structured search plus Graph v1) = **8 campaigns**, plus **4 packet-freeze steps**. No separate operational shakedown is proposed: the synthetic dry run already exercises every command, and a live shakedown would spend source budget without testing anything the dry run does not.
- **Records:** packet and campaign ledgers are `LIVE` Discovery Lab ledgers under `docs/strategy/graph_pilot/<packet>/`, with `acquisition_authorized: true` and this activated document as their authority. That directory is outside default ledger discovery.
- **Branches:** arm ledgers and connection logs live on branches `graph-pilot/<packet>-<arm>` until all eight campaigns and their adjudications finish.
- **Prohibited throughout:**
  - market data, security prices or returns, backtests, trading or brokerage;
  - paid sources, account creation, credentials or authenticated requests;
  - cloud jobs;
  - Discovery Lab or Graph code changes during the pilot, other than bug fixes reported to the owner;
  - any experiment registration, Store transition or change to EXP001–EXP007;
  - any automatic follow-on pilot.

## 2. Budgets (proposed maximums, not a standing allowance)

| Unit | Analyst minutes | Ordinary source starts | Search queries | External response bytes |
|---|---:|---:|---:|---:|
| Each campaign (×8) | 120 | 6 | 10 | 8 MiB |
| Each packet freeze (×4) | 30 | 3 | 3 | 6 MiB |
| **Pilot ceiling** | **18 hours** | **60** | **92** | **88 MiB** |

**Budget accounting:**
- **Graph time** (querying, suggestion review and follow-up) counts inside the 120 campaign minutes. No extension is permitted.
- **Unused budget** does not transfer between campaigns, arms or packets.
- **Unknown costs** are recorded as UNKNOWN; they never count as headroom.
- **Owner time** as operator or adjudicator is recorded separately and is not part of the arm budgets.

## 3. Source selection rules

**Packet rule (decided before any inspection):**
1. **Window:** the most recent complete calendar quarter that ended at least 12 months before activation.
2. **Probe:** one request per environment, to the exact route fixed in the shortlist. The environment is eligible only if the response meets all eight criteria E1–E8 of the pre-registration: original publisher, open access, complete usable response, at least 3 dated records in the window, stable identifiers, the method's required fields, no persisted stop, and the publisher's own records. **HTTP 200 alone does not qualify.**
3. **Fallback:** if any criterion fails, record which one and probe the second environment, with no retry. If both fail, that method's packet is NOT_FORMED and is reported. No third environment is tried.
4. **Selection:** take the qualifying records sorted by record date, then identifier, and keep the first five (or all, if three or four qualify). The packet preparer reads nothing beyond the eligibility fields before selection.
5. **Neutrality:** packets are never chosen by overlap with historical memory, by expected outcome or by prices.

**Proposed shortlist.** These environments are unverified. Before activation the owner fixes, for each one, the exact route, the required field names and confirmation of the terms.

| Method | First choice | Second choice |
|---|---|---|
| Observation-first | [US EPA ECHO facility enforcement data service (echo.epa.gov), exact route to be fixed] | [US PHMSA pipeline incident data, exact route to be fixed] |
| Relationship-first | [SEC EDGAR full-text search for material-contract exhibits (EX-10) filed in the window] | [FERC eLibrary contract filings, exact route to be fixed] |
| Event-first | [openFDA device recall endpoint] | [OSHA inspection data, exact route to be fixed] |
| Hypothesis-first | [Owner-written mechanism statement, committed at activation, not previously investigated in Research OS] | [Second owner-written mechanism] |

The ECHO data service is a different host and route from the stopped EPA report PDF (`www.epa.gov/system/files/...`). The owner should confirm this before activation.

**Within a campaign:**
- **Which sources:** an arm may request further sources only to investigate its packet's records and the claims it forms. It must not run unrelated discovery.
- **Request hygiene:**
  - Ordinary requests are spaced at least 1 second apart.
  - A response over 4 MiB, or of unknown length over 4 MiB, gets a metadata-only stop.
  - Every request gets a receipt (locator, UTC time, status, bytes, SHA-256, completeness) and a Discovery Lab `SOURCE_START` effort pointing to it.
  - Original bodies stay private under `data/raw/graph_pilot_<date>/`.

## 4. Source stops

**Carried forward unchanged.** Every persisted stop and recorded denial in AGENTS.md and in prior receipts remains in force. This includes:

| Recorded stop | Source of the stop |
|---|---|
| NRC route (HTTP 403) | Next-frontier source check |
| Federal procurement discovery route (403) | Procurement pilot |
| FDA routes and the FTC merger directory (404) | FDA and merger pilots |
| CourtListener RECAP search and the Chevron static-files letter host (403) | SH09 verification |
| Ofwat model index (403) and EPA report (404) | Eight-family M campaign |
| NAIC opt-ins FAQ (403) | Discovery bottleneck check |
| Glaukos q4cdn and GlobeNewswire routes (403) | Frontier selection II |
| ClinicalTrials current-version history route | Source-first pass |
| Every `final_stop.json` | All prior tasks |

**Unchanged holds:** F19 remains on HOLD and SH09 remains stopped. Neither may be reopened through the pilot.

**New stops during the pilot:**
- **Denials:** any 403, 404, other denial, CAPTCHA, login wall or timeout stops that host and route for the rest of the pilot. There are no retries, mirrors or bypasses.
- **Ceilings:** reaching a campaign or pilot ceiling stops dispatch immediately.

## 5. Activation decision

The owner decides, in the activated text:

1. **Go or no-go** for the full four-packet, eight-campaign pilot under these ceilings, or a smaller number of packets.
2. **Shortlist:** the exact routes, field names and terms confirmation for each environment, and the two hypothesis-first mechanism statements.
3. **Retrieval method:** existing manual receipt practice, or a separately authorised small bounded-fetch utility, built and reviewed before activation. **Recommended:** the utility, to make receipts exact.
4. **Roles:** that the owner acts as operator and adjudicator, under the pre-registration's separation and blinding procedure, accepting its stated residual leakage.
5. **Decision rules:** the proposed multi-dimensional classification, or the owner's replacements, fixed before any packet is frozen.

## 6. Commands, valid only after activation

Every pilot command below (packet freeze, arm, blinding and report) ran in the [dry run](graph_pilot_dry_run.md) with temporary paths in place of these. The preflight lines are the repository's standard checks. Angle brackets mark private locations.

```sh
# Preflight (record in the pilot receipt)
git status && git log -1 --format=%H
python -m unittest discover -s tests -v
python -m src.research.public_checks
python -m src.research.graph pilot dry-run --check
python -m src.research.graph build --check                    # record the memory digest

# Packet freeze (packet preparer); P is P1..P4. Commit the snapshot before any arm starts.
python -m src.research.discovery init docs/strategy/graph_pilot/P/packet.jsonl CAMPAIGN.json
python -m src.research.discovery add docs/strategy/graph_pilot/P/packet.jsonl source|observation RECORD.json
python -m src.research.graph pilot snapshot docs/strategy/graph_pilot/P/snapshot.json --packet P \
    --packet-ledger docs/strategy/graph_pilot/P/packet.jsonl \
    --arm-ledger S docs/strategy/graph_pilot/P/S.jsonl DLC-GP-S --arm-ledger G docs/strategy/graph_pilot/P/G.jsonl DLC-GP-G \
    --bundle data/raw/graph_pilot_<date>/P/bundle

# Each arm, in its own worktree at the snapshot commit (ARM is S or G); first verify the starting inputs
python -m src.research.graph pilot verify docs/strategy/graph_pilot/P/snapshot.json --bundle <bundle copy>
python -m src.research.discovery init docs/strategy/graph_pilot/P/ARM.jsonl CAMPAIGN.json
python -m src.research.discovery add docs/strategy/graph_pilot/P/ARM.jsonl source|observation|relationship|candidate|effort RECORD.json
python -m src.research.discovery freeze docs/strategy/graph_pilot/P/ARM.jsonl CAND-ID
SNAP="--snapshot docs/strategy/graph_pilot/P/snapshot.json --arm ARM"    # --query-at defaults to now

# Structured arm (S): baseline-search only
python -m src.research.graph baseline-search DLC-GP-S OBS-ID $SNAP
# Graph arm (G): the same baseline-search, plus graph operators
python -m src.research.graph revisit OBS-ID $SNAP
python -m src.research.graph complements OBS-ID $SNAP
python -m src.research.graph suggestions DLC-GP-G $SNAP
python -m src.research.graph same-gap REQ_... $SNAP
python -m src.research.graph explain NODE_A NODE_B $SNAP
python -m src.research.graph pilot connections docs/strategy/graph_pilot/P/connections-ARM.jsonl --arm ARM
python -m src.research.graph pilot account docs/strategy/graph_pilot/P/snapshot.json --arm ARM

# After both arms of the packet finish (blind preparer, then owner)
python -m src.research.graph pilot blind docs/strategy/graph_pilot/P/snapshot.json \
    --log S docs/strategy/graph_pilot/P/connections-S.jsonl --log G docs/strategy/graph_pilot/P/connections-G.jsonl \
    --salt SALT --out docs/strategy/graph_pilot/P/blind.json --key data/raw/graph_pilot_<date>/P/key.json
python -m src.research.graph pilot adjudications docs/strategy/graph_pilot/P/blind.json docs/strategy/graph_pilot/P/adjudications.jsonl
# commit the adjudications; copy the key to docs/strategy/graph_pilot/P/key.json; record dispositions with [DECISIVE:ID]

# After all packets
python -m src.research.discovery validate docs/strategy/graph_pilot/*/S.jsonl docs/strategy/graph_pilot/*/G.jsonl
python -m src.research.graph pilot report docs/strategy/graph_pilot/P1 docs/strategy/graph_pilot/P2 docs/strategy/graph_pilot/P3 docs/strategy/graph_pilot/P4
```

**Every graph query passes `--snapshot` and `--arm`.** The tool refuses `--ledgers`, `--known-at`, `--catalogue` and `--mode` alongside a snapshot, and refuses every graph operator for arm S.

## 7. Deliverables after the pilot

- **Records:** packet and campaign ledgers, snapshots, connection logs, blinded exports, adjudication logs, unsealed keys, the pilot receipt (requests, bytes, minutes by category, deviations) and a report.
- **Report content:** Q1 descriptive results per method; Q2 paired results per packet on every dimension, with every denominator; the classification under the confirmed rules; and the residual blinding limits.
- **Stop point:** no further pilot, acquisition or economic test follows automatically.
