# ACTIVE owner authorisation: first Discovery Lab + Graph v1 pilot

**Status: ACTIVE from the commit that adds this file.** This activates the [revision 2 proposal](proposed_owner_graph_pilot_authorisation.md) under the owner's [conditional go](owner_graph_pilot_conditional_go_2026-10-21.md) and [route-amendment decision](owner_graph_pilot_route_amendment_2026-10-21.md). In the owner's words: *"I select Option 2: amend the source routes before pilot activation"* and *"Once the exact source routes are established, activate the authorisation using this explicit owner decision and begin the first eligible packet."*

The protocol is the [pre-registration, revision 2](graph_pilot_preregistration.md). Its design, isolation, logging, blinding, outcomes, stopping conditions and decision rules apply unchanged. The **only** amendments are the source routes in section 3 below, made by the owner. The route evidence is in the [route preflight](graph_pilot_route_preflight.md) and section 3.

## 1. Scope

- **Size:** 4 packets × 2 arms, up to **8 campaigns** plus 4 packet freezes. Three valid pairs are acceptable to the owner if a packet cannot form.
- **Packet window:** **2025-07-01 to 2025-09-30.** A 2025 event read from a document retrieved in 2026 is not certified as public in 2025. Economic occurrence, source version, first-public time and retrieval stay distinct.
- **Order and arms, as registered:**

| Packet | Method | First arm | Second arm |
|---|---|---|---|
| P1 | Observation-first | S | G |
| P2 | Relationship-first | G | S |
| P3 | Event-first | S | G |
| P4 | Hypothesis-first | G | S |

- **Records:** `LIVE` ledgers under `docs/strategy/graph_pilot/<packet>/`, with this file as their authority.
- **Branches and worktrees:** each arm runs in a fresh session in its own git worktree made from the snapshot commit, on branch `graph-pilot/<packet>-<arm>`. Arm branches are merged into `main` only after every campaign and adjudication is complete.
- **Prohibited throughout:**
  - market data, prices, returns, backtests, trading, brokerage and portfolio work;
  - paid, authenticated or keyed sources, account creation and credentials;
  - cloud jobs;
  - reopening stopped investigations, or any EXP or Store change;
  - Discovery Lab v2 or Graph v2;
  - any automatic follow-on pilot.

## 2. Budgets (maximums, not targets)

| Unit | Analyst minutes | Ordinary source starts | Search queries | Response bytes |
|---|---:|---:|---:|---:|
| Each campaign | 120 | 6 | 10 | 8 MiB |
| Each packet freeze | 30 | 3 | 3 | 6 MiB |
| **Pilot ceiling** | **18 hours** | **60** | **92** | **88 MiB** |

**Budget rules:**
- Graph time counts inside each campaign's 120 minutes.
- No transfer between units.
- Unknown costs stay UNKNOWN.
- Dispatch stops before any request that would breach a ceiling.

## 3. Source routes (owner-amended; fixed before any request)

### P1 observation-first: `NOT_FORMED` at preflight

**EPA ECHO.** The owner allowed ECHO's two-request query-and-results flow, provided its publisher documentation verified the route. It did not:
- **Case service:** EPA's case-service documentation renders client-side and could not be read. The machine-readable specification was not found at EPA's published pattern (`swaggerx.swagger_json?p_prefix=CASE` returned 404, not pursued further).
- **Facility search:** EPA's readable *ECHO All Data Search Results Services* specification (v3.0, 8/11/2015) documents `get_facilities` then `get_qid`, with pages of at most 1,000 rows and `RegistryID` as a default column. But:
  - its base URLs are on the older host `ofmpub.epa.gov`, not the current service host;
  - its only enforcement-date filter is relative ("last formal enforcement action within 1–5 years");
  - its date field, `FacDateLastFormalAction`, is a facility's *most recent* action.

  Selecting facilities with Q3-2025 actions that way would depend on whether they had a later action, which is later information. The 2025-07-01 to 2025-09-30 window cannot be applied outcome-blind.
- **Ruling:** under the owner's rule ("If they cannot be established, mark the route ineligible"), ECHO is ineligible, with no request made.

**PHMSA (fallback)** remains blocked: its documentation returned 403 and the exact file route is unconfirmed. **P1 is `NOT_FORMED`.**

### P2 relationship-first: SEC EDGAR documented archive route

This route uses no full-text search and no undocumented endpoint. The SEC's [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) page documents:
- the `/Archives/edgar/daily-index` directory;
- that "each directory and all child subdirectories contain three files", including `index.json`;
- index records with company name, form type, CIK, date filed and file name;
- complete-submission text files at `/Archives/edgar/data/<CIK>/<accession>.txt`;
- fair access at 10 requests per second at most, with a declared User-Agent. The configured identity is used, and it is never logged.

The packet freeze makes **at most 3 requests**, in this fixed order:
1. `https://www.sec.gov/Archives/edgar/daily-index/2025/QTR3/index.json`. Of the entries named `form.<date>.idx`, the one with the earliest date on or after 2025-07-01 is the daily form index to use.
2. That daily form index. E1–E8 are judged on it:
   - records: form type, company, CIK, date filed, file name;
   - identifier: the accession number, taken from the file name;
   - required fields: an identified filer (CIK) and the original document locator.

   The packet records are the first five `8-K` records, sorted by date filed, then accession number.
3. The complete-submission text of the **first** packet record, capped at 4 MiB.

**Formation rule:**
- **P2 forms** only if that original submission contains a document of type `EX-10` (any `EX-10.x`) whose text identifies an agreement and a counterparty. The relationship is recorded from that exhibit only.
- **Otherwise P2 is `NOT_FORMED`.** An index record is never evidence of a relationship. The budget is not widened, no further filing is opened, and no issuer is preferred.

### P3 event-first: openFDA device enforcement, credential-free

The [device enforcement endpoint guide](https://open.fda.gov/apis/device/enforcement/how-to-use-the-endpoint/) states: "While you don't need an API Key to try or use the API". No key is registered or supplied.

**The packet freeze makes 1 request:**
`https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=1000`

This uses the documented `+TO+` range syntax, `:asc` sort and a maximum `limit` of 1000. An authentication denial stops the route, with no retry and no credential.

**Fields** ([definitions](https://open.fda.gov/fields/deviceenforcement.yaml)):
- `report_date`: "Date that the FDA issued the enforcement report". It is a report date, not first-public certification.
- `recall_initiation_date`: when the firm began notifying.
- `recall_number`: the stable identifier. `event_id` groups products.
- `classification` (I, II or III): the event type.
- `recalling_firm`: per the owner's field list, the entity field. It is a firm name with no registry identifier, so it is recorded as a **name-only identity** and never joined by identifier.

FDA "will make corrections or changes to recall information previously disclosed", so retrieved values are the current version.

**Packet records:** the first five qualifying records, sorted by `report_date`, then `recall_number`.

### P4 hypothesis-first: owner mechanism; no source request

**Primary mechanism, verbatim:** "A documented product-safety recall may change demand for replacement components supplied by an economically linked listed company. A measurable claim would require original compatibility or supplier documentation, independently observable activity, a credible historical public-time route and demonstrable issuer exposure."

It is distinct from prior investigations (see the preflight duplicate check), so the reserve is not used. The packet ledger records the mechanism as its question, and the freeze spends no source starts.

### Within campaigns

- **Which sources:** arms may fetch further free, public, unauthenticated original-publisher records only to investigate their packet. They may not contact `efts.sec.gov`, EPA ECHO, PHMSA, FERC eLibrary or DOL/OSHA APIs.
- **Request hygiene:**
  - one request per command and no retries;
  - at least 1 second between requests;
  - a 4 MiB size stop;
  - every request receipted, with a Discovery Lab `SOURCE_START` effort.

## 4. Retrieval: the existing manual receipt workflow

- **The script:** each request is made by [`graph_pilot/fetch_one.py`](graph_pilot/fetch_one.py). It reproduces the SH09 and Measurement Gate M receipt practice:
  - a reservation written before dispatch;
  - one standard-library GET, with no retry, no redirect following and no authentication;
  - a byte cap;
  - the body stored privately by SHA-256;
  - a receipt with URL, UTC start and finish, status, headers, bytes, digest, completeness and size stop.

  It refuses before dispatch at a start or byte ceiling, if a reservation has no receipt, or if a `final_stop.json` exists. It is a single-request command, not a crawler.
- **Private storage:** bodies and receipts stay under ignored `data/raw/graph_pilot_20261021/<packet>/<role>/`.
- **Searches:** made with the web-search tool and recorded as `SEARCH` efforts.
- **Hashes:** both are recorded in the validation receipt.
  - `fetch_one.py`: SHA-256 `3e51a00081b5db3ea4c702b0bbfd6117e1339ff70df0d1801aa54c35a958eb1a`.
  - Fixed [arm instructions](graph_pilot/arm_instructions.md): SHA-256 `ad070e4144d6e9d90489c28c2c2b72978befd100ee1eb39543ee2f75d32bcdb3`.

## 5. Source stops

Every persisted stop and denial recorded in AGENTS.md and prior receipts stays in force. The proposal's stop table is unchanged. F19 stays on HOLD and SH09 stays stopped. The PHMSA documentation 403 stops that route. Any new 403, 404, other denial, CAPTCHA, login wall or timeout stops that host and route for the rest of the pilot.

## 6. Roles, blinding and decisions

- **Operator and human adjudicator:** the owner. The owner adjudicates every blinded item and makes every M/H review and disposition. Claude never records them as human.
- **Coordinator (Claude):**
  - prepares packets under the fixed rules;
  - starts each arm as a fresh session with the fixed arm instructions;
  - prepares the blinded exports after both arms of a packet finish;
  - reports.

  The coordinator relays nothing between arms.
- **Blinding is partial, not complete**, as revision 2 states.
- **Decision rules:** revision 2's descriptive rules, as implemented in `pilot report`, are adopted. With fewer than three completed pairs, the evaluation is reported as `INCONCLUSIVE`.
- **Stop point:** no further pilot, acquisition or economic test follows automatically.
