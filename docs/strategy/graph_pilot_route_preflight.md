# Graph pilot: source-route preflight (documentation only)

**2026-10-21. Result: ACTIVATION NOT COMPLETED — owner decision required.** Under the [conditional go](owner_graph_pilot_conditional_go_2026-10-21.md), each shortlisted route in the [revision 2 authorisation](proposed_owner_graph_pilot_authorisation.md) was checked against its publisher's public documentation only. **No scientific-data endpoint was contacted, no packet was probed, and no activated authorisation was written.**

None of the six shortlisted data routes can be fixed as a single-request, credential-free, original record route under the frozen rules. All six were stopped at preflight. Under the fallback rule, P1, P2 and P3 would each be `NOT_FORMED`. P4 (hypothesis-first) can form.

## Summary

| Packet | First choice | Second choice | Packet if activated unchanged |
|---|---|---|---|
| P1 Observation-first | EPA ECHO: blocked by a **two-call design** | PHMSA incidents: blocked, **documentation 403**, route unconfirmed | `NOT_FORMED` |
| P2 Relationship-first | SEC EDGAR full-text search: **no documented API**, a query term is required, no documented exhibit filter | FERC eLibrary: **no documented record route** | `NOT_FORMED` |
| P3 Event-first | openFDA device enforcement: **an API key is required** (a credential) | OSHA inspections: **API key required**; legacy site being retired | `NOT_FORMED` |
| P4 Hypothesis-first | Primary mechanism: distinct from prior work | Reserve not needed | Forms (no source starts) |

Packet window, as fixed by revision 2 for activation on 2026-10-21: **2025-07-01 to 2025-09-30.**

## Route findings

Each heading gives the twelve preflight items where the documentation established them. **UNKNOWN** means the documentation did not establish the item.

### P1a. EPA ECHO enforcement cases (first choice): BLOCKED, design
- **Publisher and route.** US EPA, ECHO. The data host is `echodata.epa.gov`, using `case_rest_services` (documentation at [echo.epa.gov/tools/web-services](https://echo.epa.gov/tools/web-services)). The services are GET only, returning JSON or XML, with no key stated.
- **Call flow.** The service descriptions (`get_cases`, `get_qid`) say: "Use get_cases to validate passed query parameters, obtain summary statistics and to obtain a queryid (QID)", and "Use get_qid, with the returned QID, to paginate through arrays of case results". QIDs last about 30 minutes. This text comes from mock copies of EPA's service specification, because EPA's own documentation page renders client-side and did not load as text.
- **Blocker.** The first response carries counts and a query ID but **no case records**. Revision 2 judges each environment on one request, so E4–E6 cannot be met in one response. Bulk ECHO downloads are large ZIP files that would hit the 4 MiB metadata-only stop.
- **Stop intersection.** None. The stopped route is the single PDF `https://www.epa.gov/system/files/documents/2024-11/420r24022.pdf` (404, eight-family campaign). ECHO uses a different host and service, so the route is not stopped. It is blocked by its design, not by a stop.
- **Not established:** date-field definitions, identifiers, size controls and terms (UNKNOWN). The fallback is P1b.

### P1b. PHMSA pipeline incident data (fallback): BLOCKED, access
- **Publisher and route.** US DOT, PHMSA. The download page is "[Distribution, Transmission & Gathering, LNG, and Liquid Accident and Incident Data](https://www.phmsa.dot.gov/data-and-statistics/pipeline/distribution-transmission-gathering-lng-and-liquid-accident-and-incident-data)".
- **Blocker.** A documentation fetch of that page returned **HTTP 403** and was not retried. A domain-limited search found only the label "Hazardous Liquid Accident Data - January 2010 to present (ZIP)", not the file URL. The search results describe each ZIP as holding a data file and a field-description file, covering all years since 2010.
- **Consequences.**
  - The exact route, size, terms and date-field meanings are **UNKNOWN**.
  - Any request now would mean guessing a URL on a host that refused the documentation fetch.
  - A multi-year ZIP would likely hit the 4 MiB stop.
- **Pilot stop.** The 403 stops that documentation route for the pilot.

### P2a. SEC EDGAR material-contract exhibits (first choice): BLOCKED, route undefined
- **Publisher and coverage.** US SEC. The [EDGAR full-text search FAQ](https://www.sec.gov/edgar/search/efts-faq.html) states that search covers "the full text of all EDGAR filings submitted electronically since 2001", including "all attachments".
- **Blockers.**
  - The FAQ documents no API endpoint (the `efts.sec.gov` backend is undocumented).
  - It documents form-type selection only through the browser interface, and no exhibit-type (EX-10) filter.
  - Every search needs query words.
- **Consequence.** Fixing this route would mean choosing an undocumented endpoint and a search term. The search term would itself be a selection choice, so these are not routine details.
- **Stop intersection.** No recorded SEC stop. Earlier archive requests to `www.sec.gov` returned 200.
- **Not established:** identifiers in the response, date-field definitions and size controls (UNKNOWN for this route).

### P2b. FERC eLibrary contract filings (fallback): BLOCKED, route undefined
- **What is documented.** FERC documents only the [eLibrary web search](https://www.ferc.gov/elibrary-quick-help): Filed Date and Posted Date; accession numbers of the form `YYYYMMDD-XXXX`; coverage from 2004-06-06.
- **Blocker.** No public search API or record endpoint was found. The search page is a browser application, so a single GET returns its shell, not records. FERC's listed API is for submissions, not search.

### P3a. openFDA device enforcement (first choice): BLOCKED, credentials
- **Publisher and coverage.** US FDA, openFDA. Data comes from the FDA Recall Enterprise System, 2004 to present, updated weekly ([overview](https://open.fda.gov/apis/device/enforcement/)).
- **Fields.** `recall_number`, `event_id`, `report_date`, `recall_initiation_date`, `center_classification_date`, `classification`, `recalling_firm` and `openfda` ([fields](https://open.fda.gov/apis/device/enforcement/searchable-fields/)). The documentation gives types only, not definitions. `limit` is at most 1000 ([query parameters](https://open.fda.gov/apis/query-parameters/)).
- **Version caution.** FDA "will make corrections or changes to recall information previously disclosed". Records may therefore be revised, and none is a first-public-time certificate.
- **Blocker.** The [authentication page](https://open.fda.gov/apis/authentication/) states: "An API key is required to make calls to the openFDA API." It also lists a no-key limit ("240 requests per minute, per IP address"), but nowhere describes a key as optional. A key is a registered credential, which this authority prohibits. An unkeyed request against that explicit statement is not taken.
- **Stop intersection.** None. The stopped FDA routes are the complete-response-letters page (404) and an `accessdata.fda.gov` redirect (302); the recorded FDA pages are on the drugs side only.

### P3b. OSHA inspection and citation records (fallback): BLOCKED, credentials
- **What is documented.** DOL documents OSHA enforcement data through its [developer portal](https://developer.dol.gov/health-and-safety/dol-osha-enforcement/) and [API user guide](https://www.dataportal.dol.gov/pdf/dol-api-user-guide.pdf).
- **Blocker.** The search results describe the v4 API as authenticated with a registered key, and the older `data.dol.gov` API with a registered token. DOL is retiring the [enforcement website](https://enforcedata.dol.gov/views/home.php), and its bulk catalogues are large files.

## P4 mechanisms: duplicate check

Prior work was checked through repository reports and the catalogue only.
- **Primary** (a recall changes replacement-component demand for an economically linked listed supplier): **no prior investigation of this mechanism.**
  - The nearest prior work is the NHTSA complaint-to-recall idea in the [reorientation review](reorientation_review.md) and [opportunity map](opportunity_map.md). It concerns the *recalling* issuer (F/GM) and complaints before recall, and it stopped at source feasibility.
  - EF03 (IV-fluid substitute output) concerns substitute capacity after a shortage, not recall-driven component demand.
  - The primary is usable; the reserve is not needed.
- **Reserve** (an infrastructure approval delay changes a linked operator's utilisation): no prior investigation found. The nearest are H-2A certification timing and F03 use-specific permissions, both different objects.

## Retrieval method

The existing practice recorded in `data/raw/sh09_verification_20261021/` and `measurement_gate_campaign_20261021/` is manual and one request at a time:
- a reservation file written before dispatch;
- a single standard-library GET with no retries, a byte cap and no authentication;
- a receipt (URL, UTC start and finish, status, headers, byte count, SHA-256, completeness, size stop);
- the body stored by hash.

The scripts that produced those receipts were not committed. If the pilot is activated, the same receipt schema would be reproduced in a single-request script whose source and SHA-256 are recorded in the activated authorisation before use. That is a disclosed reproduction of the existing practice, not a crawler. Searches are counted separately, as before.

## Documentation accesses during preflight

None of these are scientific-data requests, and none counts against pilot budgets (the pilot is not active):
- **Ten page fetches:** ECHO web services; ECHO enforcement-case page (navigation shell only); a third-party API mock (redirect, not followed); a second mock; the PHMSA page (**403**); the SEC full-text-search FAQ; openFDA enforcement overview, fields and query-parameter pages; the openFDA authentication page (read twice).
- **Four domain-limited searches:** ECHO service names; the PHMSA file; DOL OSHA API; FERC eLibrary API.

## Decision needed from the owner

Activating revision 2 unchanged would leave only P4, a single pair. The Q2 classification would then be `INCONCLUSIVE` by rule (fewer than three comparable pairs), and Q1 would cover one method. The owner chooses:

1. **Run P4 alone.** Activate with P1–P3 recorded as `NOT_FORMED` at preflight. This costs at most two campaigns (4 h, 12 starts, 20 searches, 16 MiB) and yields one pilot pair, with no possible Q2 verdict.
2. **Amend routes before activation.** Each amendment below is the owner's to make, not mine:
   - **ECHO:** allow the documented two-call flow (`get_cases` then `get_qid` for the window) as one probe costing 2 starts, with fixed parameters.
   - **SEC:** allow the publisher-hosted but undocumented full-text-search JSON route, with an owner-fixed query term, form filter and date range.
   - **openFDA:** allow a free registered API key, kept private. This overrides "no credentials".

   With at least two of these amendments, three or four pairs could form. PHMSA, FERC and OSHA have no route available without credentials, guessing or a bypass.
3. **Do not run the pilot now.**
