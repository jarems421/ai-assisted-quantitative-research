# PROPOSED owner authorisation: first Discovery Lab + Graph v1 pilot

> **STATUS: PROPOSED, NOT ACTIVE.** This document authorises nothing in its current form.
>
> **How it would be activated:** the owner copies it to `docs/strategy/owner_graph_pilot_<date>.md`, edits the bracketed choices, removes this banner, and states activation in their own words. That activated text is committed and pushed before any source request.
>
> **What still requires that activation:** every source request, campaign ledger, search query or packet freeze.

This pilot executes the [pre-registration](graph_pilot_preregistration.md). The reasons for the pilot are set out in the [review](graph_v1_review.md).

## 1. Scope

- **Pilot size:** 4 starting packets, one per Discovery Lab method, × 2 arms (S: structured-ledger search; G: structured search plus Graph v1) = **8 campaigns**, plus **4 packet-freeze steps**.
- **Campaign records:** campaigns are `LIVE` Discovery Lab ledgers under `docs/strategy/discovery/pilot/S/` and `docs/strategy/discovery/pilot/G/`, with `acquisition_authorized: true` and this activated document as the authority.
- **Prohibited throughout:**
  - market data, security prices or returns, backtests, trading or brokerage;
  - paid sources, account creation, credentials or authenticated requests;
  - cloud jobs;
  - Discovery Lab or Graph code changes during the pilot, other than bug fixes reported to the owner;
  - any experiment registration, Store transition or change to EXP001–EXP007;
  - any automatic follow-on pilot.

## 2. Budgets

| Unit | Analyst minutes | Ordinary source starts | Search queries | External response bytes |
|---|---:|---:|---:|---:|
| Each campaign (×8) | 120 | 6 | 10 | 8 MiB |
| Each packet freeze (×4) | 30 | 3 | 3 | 6 MiB |
| **Pilot ceiling** | **18 hours** | **60** | **92** | **88 MiB** |

**Budget accounting:**
- **Graph time:** graph querying and suggestion review count inside the 120 campaign minutes. No extension is permitted.
- **Unused budget:** a campaign's unused budget does not transfer to another campaign, arm or packet.
- **Unknown costs:** an unknown cost is recorded as UNKNOWN. It does not count as headroom.

## 3. Source selection rules

**Eligible packet source environments:**
- free, public and unauthenticated;
- published by the original body (regulator, court, agency or issuer filing system);
- carrying dated records with stable identifiers;
- with terms that permit retrieval;
- not on the stop list in section 4.

**Packet rule (decided before any inspection):**
- **Order of trial:** for each method, take the first eligible environment in the shortlist below, in listed order.
- **Probe:** the packet-freeze step makes one landing or data request. HTTP 200 qualifies the environment. Any other status stops that environment, counts against the freeze budget, and moves to the next listed environment, with no retry.
- **Window:** the packet window is the most recent complete calendar quarter that ended at least 12 months before activation.
- **Records:** the first records in the window matching the method's entry rule (an observation, a documented relationship, an event, or the stated mechanism) form the packet, up to the freeze budget.
- **Neutrality:** packets are never chosen by overlap with historical memory, by expected outcome or by prices.

**Proposed shortlist.** Unverified environments; the owner may amend this before activation.

| Method | First choice | Second choice |
|---|---|---|
| Observation-first | [US EPA ECHO enforcement case data] | [US PHMSA pipeline incident data] |
| Relationship-first | [SEC EDGAR material-contract exhibits (EX-10) filed in the window] | [FERC eLibrary contract filings] |
| Event-first | [openFDA device recall records] | [OSHA inspection and citation records] |
| Hypothesis-first | [Owner-written mechanism statement, committed at activation, not previously investigated in Research OS] | [Second owner-written mechanism] |

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

## 5. Activation conditions

Before the first request, the owner confirms these in the activated text:
1. **Shortlist:** the source shortlist (as amended) and the two hypothesis-first mechanism statements.
2. **Retrieval method:** source retrieval uses the existing manual receipt practice. Alternatively, the owner separately authorises a small bounded fetch utility, built and reviewed before activation. **Recommended:** the utility, to make receipts exact.
3. **Adjudicator and blinding:** the adjudicator (the owner) and the blinding procedure in the pre-registration.
4. **Decision rules:** the proposed decision rules, or the owner's replacements.

## 6. Commands, valid only after activation

```sh
# Preflight (records the starting state in the pilot receipt)
git status && git log -1 --format=%H
python -m unittest discover -s tests -v
python -m src.research.public_checks
python -m src.research.graph build --check                        # record the memory digest

# Per campaign: ARM is S or G; LEDGER is docs/strategy/discovery/pilot/ARM/DLC-...jsonl
python -m src.research.discovery template campaign > campaign.json  # fixture LIVE, method, acquisition_authorized true,
                                                                    # authority = activated document, budget = section 2
python -m src.research.discovery init LEDGER campaign.json
python -m src.research.discovery add LEDGER source|observation|relationship|candidate|review|disposition|effort RECORD.json
python -m src.research.discovery freeze LEDGER CAND-ID
python -m src.research.discovery checklist LEDGER CAND-ID

# Structured arm (S): no graph operators
python -m src.research.graph baseline-search DLC-ID OBS-ID --ledgers docs/strategy/discovery/pilot/S/*.jsonl --known-at START_UTC

# Graph arm (G): the same baseline-search over pilot/G/*.jsonl, plus:
python -m src.research.graph revisit DLC-ID --ledgers docs/strategy/discovery/pilot/G/*.jsonl --known-at START_UTC
python -m src.research.graph complements OBS-ID --ledgers docs/strategy/discovery/pilot/G/*.jsonl --known-at START_UTC
python -m src.research.graph same-gap REQ_... --ledgers docs/strategy/discovery/pilot/G/*.jsonl
python -m src.research.graph explain NODE_A NODE_B --ledgers docs/strategy/discovery/pilot/G/*.jsonl
python -m src.research.graph suggestions DLC-ID --ledgers docs/strategy/discovery/pilot/G/*.jsonl --known-at START_UTC > suggestions.json

# After both arms of a packet: blinded adjudication, then validation and summaries
python -m src.research.graph adjudications docs/strategy/discovery/pilot/adjudication_log.jsonl
python -m src.research.discovery compare docs/strategy/discovery/pilot/S/*.jsonl docs/strategy/discovery/pilot/G/*.jsonl
python -m src.research.discovery validate docs/strategy/discovery/pilot/S/*.jsonl docs/strategy/discovery/pilot/G/*.jsonl
```

**Always pass `--ledgers` for the running arm.** The default ledger discovery would include both arms.

## 7. Deliverables after the pilot

- **Records:** campaign ledgers, the adjudication log, the pilot receipt (requests, bytes, minutes by category, deviations) and a report.
- **Report content:** Q1 descriptive results per method; Q2 paired results per packet, with every denominator; and the decision under the confirmed rules.
- **Stop point:** no further pilot, acquisition or economic test follows automatically.
