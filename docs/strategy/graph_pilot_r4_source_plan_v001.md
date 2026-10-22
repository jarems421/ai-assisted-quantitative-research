# Graph Pilot R4: offline source and packet-feasibility plan (version 001)

> **DRAFT — NOT ACTIVE — NO EXPERIMENTAL AUTHORITY.** No source in this document has been fetched, probed or preflighted. Every statement about a source's content, access, format or limits is **`CANDIDATE_UNVERIFIED`**: it is a planning assumption that only an approved operator's preflight can confirm or refute. Nothing here authorises a request.

## 1. What the protocol requires

- **Packets.** Four packets, one per method (observation-, relationship-, event- and hypothesis-first), each with paired S/G arms. A definitive descriptive classification needs at least three comparable conforming pairs.
- **Fresh packets** ([R4 protocol](graph_pilot_r4_protocol_proposed.md)): no source, host route, filing set or record used in R1–R3 or earlier Research OS campaigns.
- **Size-safe routes:** each route documents a page or record limit, and a probe stays under the per-start byte stop with half the stop as margin.
- **Eligibility** E1–E8 and **mechanical selection** as in the [revision 2 pre-registration](graph_pilot_preregistration.md#packet-eligibility-and-selection).
- **Access:** free, public, unauthenticated original publishers only. No keys, accounts, mirrors, paid sources, prices or returns.

## 2. Offline overlap evidence (what was checked here)

**Tracked history.** I counted hosts referenced in tracked documents (`git grep` over `docs/` and `experiments/`, `9ac56d3`). Heavily used or referenced hosts include:

| Hosts | Used for |
|---|---|
| `www.sec.gov`, `data.sec.gov`, `xbrl.sec.gov` | EDGAR, 8-K/EX-10 and Item 2.02 work, R3 P2 |
| `api.fda.gov`, `www.fda.gov`, `accessgudid.nlm.nih.gov` | FDA pilot, R3 P3/P4 recalls |
| `static.nhtsa.gov`, `www.nhtsa.gov` | NHTSA work |
| `www.barentswatch.no` | Salmon |
| `disclosures-clerk.house.gov`, `efdsearch.senate.gov` | EXP007 |
| `httparchive.org`, `bigquery.googleapis.com` | Web adoption |
| `www.cms.gov` | F02 |
| `content.naic.org` | F19 |
| `www.courtlistener.com`, `www.data.bsee.gov`, `www.wtoffshore.com` | SH09 |
| `www.federalregister.gov`, `clinicaltrials.gov` | Source-first work |
| `www.ftc.gov` | Merger pilot |
| `echo.epa.gov`, `www.epa.gov` | Campaigns, R2 preflight |
| `www.ofwat.gov.uk`, `echa.europa.eu` | Campaigns |
| `api.tiingo.com`, `nexustrade.io`, `api.openfigi.com` | Market and identity data; out of scope for R4 anyway |

Also referenced, so an overlap audit is required: `www.eia.gov`, `fsis.usda.gov`, `usaspending.gov`, `faa.gov`, `ferc.gov`, `nrc.gov`, `msha.gov`, `govinfo.gov`, `uspto.gov`, BTS/`transtats`.

**Not found in tracked history** (0 matches): `gleif.org`, `cpsc.gov`/`saferproducts.gov`, `ntsb.gov`, `census.gov`, `bls.gov`, `caiso.com`, `ercot`, `misoenergy`, `pjm.com`, `ecfr.gov`, `regulations.gov`, `sam.gov`, `companieshouse`, `fmcsa`.

**Not completed:** a full audit of the private receipts under ignored `data/raw/`; the receipt formats vary. **The operator must complete it before activation** (section 5). A host absent from tracked documents is not proven unused.

## 3. Candidate environments (all `CANDIDATE_UNVERIFIED`)

The order is the proposed probe order. Selection follows the fixed rules in section 4. Nothing below asserts that a route exists, is keyless, has the stated fields or meets E1–E8.

| Method | Order | Candidate environment | Why it might fit (unverified) | Known risks to check |
|---|---|---|---|---|
| Observation-first | O-1 | CAISO OASIS public market and operations data (`oasis.caiso.com`) | Dated quantities for identified resources or nodes | Whether resource identifiers map to listed parents; response size; zipped formats |
| | O-2 | US EIA electricity data (`www.eia.gov`; plant- and utility-level) | Plant identifiers with operator utility identifiers | **Referenced in tracked history: overlap audit**; whether the API requires a key; bulk-file sizes |
| | O-3 | ERCOT public reports (`ercot.com`) | Dated operational quantities | Whether access needs registration or keys; identifier stability |
| Relationship-first | R-1 | GLEIF LEI Level 2 relationship records (`api.gleif.org`) | Documented accounting-consolidation parent relationships between LEIs, dated | Whether the relationship originals are the GLEIF records themselves (E8); page-size controls; listed-parent coverage |
| | R-2 | UK Companies House bulk data downloads (`download.companieshouse.gov.uk`) | Company identifiers and control relationships | **Likely fails size-safety** (large bulk files); the API needs a key (not allowed) |
| | R-3 | A **new, non-overlapping** SEC filing route | The largest free source of documented listed-company relationships | **Excluded under F1(a), the default**; possible only if the owner adopts F1(b) (section 6). Never SEC full-text search (stopped), nor the R2–R3 `index.json`, daily form index or 8-K routes |
| Event-first | E-1 | CPSC recalls data (`www.saferproducts.gov` / `cpsc.gov`) | Dated product recalls with firm names and recall identifiers | Whether firms carry stable identifiers (names alone cannot join); page limits; overlap with recall-themed historical memory (allowed, but no record reuse) |
| | E-2 | NTSB investigation data (`ntsb.gov`) | Dated events with identified operators, aircraft or vessels | Download format and size; identifier stability |
| | E-3 | USDA FSIS recalls (`fsis.usda.gov`) | Dated recalls with establishment numbers | **Referenced in tracked history: overlap audit**; API form |
| Hypothesis-first | H | The owner's new mechanism statement | No source environment; spends no packet-freeze starts | Must be new: not R3 P4's recall and supplier-liability mechanism, and not any catalogued investigation's mechanism |

**Exclusions, in order of precedence:**

1. **Persisted stops are never reopened, under any freshness rule.** These include NRC 403, Ofwat 403, EPA 404, PHMSA, ECHO, SEC full-text search, FERC eLibrary, OSHA, openFDA `limit=1000` and every other persisted Research OS stop.
   - **A host-level stop** excludes the whole host.
   - **A route-level stop** excludes that route and any equivalent route returning the same records, for example the same endpoint with different parameters, a mirror or a variant URL.
   - **A stop whose recorded scope is unclear** is treated as host-level.
2. **Any route needing a key, account or payment.** `regulations.gov`, `sam.gov` and FMCSA web services are excluded on the key requirement as well as being unverified.
3. **Previously used hosts** (section 2), as set by owner decision F1 (section 6):
   - **F1(a), strict, and the default.** Until the owner adopts F1(b) in the activation document, every host in section 2 is excluded. This includes the "referenced" hosts once the overlap audit confirms their use. Candidates O-2, E-3 and R-3 then fall away.
   - **F1(b)**, only if the owner adopts it prospectively in the activation document, before any probe. A previously used host may supply a *new* route, but only if all of these hold:
     - the route has no stop of its own;
     - the host has no host-level stop;
     - no selected record, filing set or route overlaps R1–R3, earlier receipts or the catalogue (section 5).

     F1(b) is never a remedy for a route that has failed. A route that failed in this pilot or any earlier campaign stays stopped.

## 4. Mechanical, outcome-blind packet formation

1. **Fixed at activation, before any request:** each method's ordered environments (section 3, as amended by the owner); the exact probe URL with its documented limit parameter; the packet window (the most recent complete calendar quarter ending at least 12 months before activation); and the byte stops.
2. **One probe per environment, no retry.** Judge E1–E8 on that response alone. **E2** (open access and terms) is the owner's documented confirmation from the publisher's published terms, read before activation.
3. **Select records mechanically:**
   - keep records meeting E4–E6;
   - sort by record date, then publisher identifier;
   - take the first five, or all if three or four qualify.

   The preparer reads no record content beyond the eligibility fields before selection.
4. **Fallback** follows the fixed environment order only. A failed environment records its failing criterion. If every registered environment of a method fails, the packet is NOT_FORMED. **Never choose a substitute after seeing content.**
5. **Outcome leakage.**
   - **Environments:** a packet may contain no outcome fields, such as later financial results, price moves or follow-on disclosures, so outcome-bearing environments are excluded at registration.
   - **Records:** a record dated after the packet window is excluded.
   - **Arms:** an arm must not read outcome fields or outcome-bearing snippets before freezing a claim.

## 5. What the approved operator checks at preflight (later, not here)

| Check | Pass condition | Stop condition |
|---|---|---|
| Original-source accessibility | HTTP 200 from the publisher's own domain; machine-readable records, not a login wall or CAPTCHA | Any 403, 404, other denial, timeout, login or CAPTCHA: the route stops, no retry |
| Stable identifiers | A publisher record identifier on every selected record, unique in the response | Missing or duplicated identifiers fail E5 |
| Pagination and size | A documented page or limit parameter; response ≤ 4 MiB and complete | An oversized or truncated response is NOT_FORMED for that environment; it is never re-requested smaller |
| Publication and version timestamps | Per-record dates inside the window; any source-version or first-public field recorded as given | A first-public time stays UNKNOWN unless an original publication record proves it |
| Economic observations and relationships | The method's required fields (E6) are present and non-empty | Missing fields fail E6 |
| Method suitability | Observation: identified entity plus a quantity with units. Relationship: an identified party plus the original document locator. Event: an event classification plus an identified entity | Unsuitable: the next environment |
| Historical overlap or contamination | No selected record, filing set or route appears in R1–R3, earlier receipts or the catalogue's cited documents (by locator and hash) | Any overlap fails E7; record it, then the next environment |
| Legal and access restrictions | The publisher's terms permit retrieval and research use, without registration | Restricted: excluded at registration |
| Potential outcome leakage | No outcome fields in packet records | Present: excluded at registration |
| Resource limits | Packet-freeze starts and bytes within the activation ceilings | A breach is a critical stop |

## 6. Feasibility problems requiring owner decisions

**F1. The freshness rule may make relationship-first packets impractical.** Read strictly, "no host route used in earlier campaigns", excludes the SEC: the largest free, keyless source of documented relationships between listed companies and contracts or counterparties. The remaining relationship candidates are untested, and may fail E2, E3 or E6. Options:

- **(a) Keep strict freshness.** Accept a material risk that the relationship packet is NOT_FORMED.
- **(b) Define freshness at the level of record, filing set and exact route.** A previously used host is then allowed with a new route and no overlapping records, verified by the section 5 overlap check. Every persisted host-level and route-level stop still applies (section 3).

I recommend (b). It keeps the scientific aim, no reused records, and is auditable. But it is the owner's decision, and it takes effect only when adopted prospectively in the activation document, before any probe. Until then (a) applies. F1 cannot be invoked after a route fails, to reach that route or an equivalent one.

**F2. Reserve depth.** Revision 2 allows two environments per method ("the third packet-freeze start may not be spent on a third environment"). R3 lost two of four packets at formation. With three methods needing sources and a minimum of three comparable pairs, two environments per method may be too few. Options:

- keep two;
- allow three per method, with the packet-freeze start ceiling raised to match.

This must be decided at registration, not after a failure.

**F3. Identity in event sources.** Recall and accident sources often carry firm *names* rather than registry identifiers, and a name never joins. An event packet can still form under E6 ("an identified entity") only if the source provides identifiers. Otherwise it fails E6. That is honest, but it should be expected.

**F4. The private receipt audit is incomplete offline.** The operator must finish the overlap audit (section 2) before the shortlist is frozen.
