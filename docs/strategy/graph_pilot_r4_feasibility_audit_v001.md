# Graph Pilot R4: pre-activation feasibility audit (version 001)

> **R4 is NOT_RUN, not activated and not authorised.** This is an offline audit plus a review of public documentation and terms pages. No dataset, API, filing, record listing or bulk route was fetched, queried or probed. No packet was formed, no reviewer was contacted and no decision is adopted here.

Base: `main` `4ace618` (PR #9 merged as `4e1465b`). Inputs: the [source plan](graph_pilot_r4_source_plan_v001.md), [readiness matrix](graph_pilot_r4_operational_readiness_v001.md), [activation template](graph_pilot_r4_activation_template_v001.md), [runbook](graph_pilot_r4_runbook_v001.md), [pre-registration E1–E8](graph_pilot_preregistration.md#packet-eligibility-and-selection) and the [R4 protocol draft](graph_pilot_r4_protocol_proposed.md).

**Classification: `INCONCLUSIVE_MORE_OFFLINE_EVIDENCE_NEEDED`. Recommendation: PAUSE R4 pending a future owner decision** (see the [pause recommendation](graph_pilot_r4_pause_recommendation_v001.md)).

- **Source availability is thin.**
  - Observation-first has no documented route with confirmed terms.
  - Relationship-first has one plausible route under the recommended F1(a), and that route is GLEIF.
  - Only event-first has two documented candidates.
- **No route is established as eligible.** Documentation can support only parts of E1, E7 and E8. E2 needs your confirmation, and E3–E6 can be judged only on a probe response.
- **Reviewers.** The arrangement is well defined, but nobody is recruited, and the cost is high relative to a descriptive result from at most four pairs.

## 1. Answers in brief

1. **Do we have enough plausible fresh original sources?**
   - **No, not yet.**
   - **Ruled out or very unlikely from documentation:** EIA, ERCOT, Companies House, NTSB and FSIS.
   - **Documented and plausible:** GLEIF and CPSC.
   - **Doubtful:** CAISO; its terms are ambiguous, and its identifiers are weak.
   - **FDIC BankFind:** the history (structure-change) route is plausible for event-first. The financial-data route is **excluded** as an outcome-bearing environment (section 3).
2. **Which routes are legally and technically plausible?**
   - **GLEIF:** CC0 licence, free.
   - **CPSC:** keyless, date-bounded.
   - **FDIC history:** keyless.
   - **CAISO:** permission is ambiguous, not confirmed.

   All of these are *documented availability* only. None is established as E1–E8 eligible (section 4).
3. **Can we realistically form three comparable pairs?**
   - **Not with confidence.** Three pairs need P4 plus two of P1–P3.
   - P1 rests on CAISO alone, and is doubtful. P2 rests on GLEIF alone under F1(a). Only P3 has two documented candidates.
   - The realistic path needs both P2 (one environment) and P3 to form.
4. **What do reviewers require?**
   - Two qualified, independent people, each spending an estimated 6–30 hours (assumptions in section 6).
   - Each must run a sealing command from a pinned checkout.
5. **What must you decide?**
   - First: whether to pause R4.
   - If R4 resumes: D1, F1, F2, U1, R1, the reserves, the ceilings, the people and the mechanism statement (section 7).

## 2. Historical overlap and stop audit

**Method.** Read-only scan of `data/raw/` (8.5 GB, 35 campaign directories):

- URL fields (`url`, `final_url`, `primary_url`, `request_url` and similar) in every receipt-like JSON/JSONL file of 300 KB or less;
- all 32 persisted stop files;
- `git grep` of tracked `docs/` and `experiments/`.

Response bodies were not opened or parsed. Nothing was copied into Git. Below are aggregates only.

**Private receipts: 84 hosts.** Request-URL fields:

| Host family | Request-URL fields | Campaign families |
|---|---|---|
| `www.sec.gov` | about 20,200 | Item 2.02, Phase 3C/3E-R, SEC pilot, integration, Graph pilots, discovery |
| `data.sec.gov` | 422 | Phase 3C, 3E-R, Item 2.02 |
| `api.tiingo.com` and Tiingo | about 600 | EXP004, Phase 3C, Item 2.02 identity |
| `disclosures-clerk.house.gov`, `efdsearch.senate.gov`, Hugging Face | about 980 | EXP007, integration |
| `api.openfigi.com` | 108 | Identity work |
| Others | small | BigQuery and HTTP Archive; BarentsWatch; FDA, openFDA and accessdata; CMS; ClinicalTrials; Federal Register; FTC; NHTSA; NAIC; NRC; Ofwat; EPA; CourtListener and SH09 hosts; Illinois IGB; issuer and research sites |

The used SEC route families are:

- `/Archives/edgar/data/…`: filings, index headers and full submissions;
- `/Archives/edgar/daily-index/…`;
- `/Archives/edgar/full-index/…`;
- `data.sec.gov/submissions/…`.

**Candidate hosts in the private receipts: none.** No receipt names CAISO, EIA, ERCOT, GLEIF, Companies House, CPSC/saferproducts, NTSB, FSIS, FDIC, FFIEC or MSHA.

**Candidate hosts in tracked documents:**

- **EIA** is cited as documentation only, never acquired ([next frontier](next_frontier_evidence_review.md)).
- **MSHA** is cited only as a proposed concept.
- **FSIS:** [expanded discovery evidence](expanded_discovery_evidence.md) records `https://www.fsis.usda.gov/inspection/regulatory-enforcement` as a **browser 403**, with "no retry/alternate host … followed". The scope of that stop is unclear, so under the registered rule it is **treated as host-level**, and FSIS is excluded. I did not fetch any FSIS page.

**Persisted stops (32 files).** Classification for R4:

| Stop | Scope for R4 |
|---|---|
| NRC archive index 403; Ofwat 403; EPA 404; FTC 404 (merger); procurement 403; Senate eFD 403 | Route-level as recorded. **Host-level for R4 by the restrictive rule**, where the record does not limit the scope. None is a candidate host |
| FSIS browser 403 (tracked only) | Unclear scope → **host-level** |
| SEC: Phase 3C full-submission size stop (scope reviewed); Item 2.02 archive-day and feed-day transfer stops; one index-header stop with its exact URL; R2/R3 P2 8-K/EX-10 packet stops; route-preflight full-text search stop | **Route-level**, with recorded scopes. Any new SEC route must avoid all of them and their equivalents |
| openFDA `limit=1000` size stop; route-preflight blocks (ECHO, PHMSA, FERC eLibrary, OSHA, openFDA key) | Host or route as recorded; none is a candidate |
| Task closure stops (`final_stop.json` for discovery, frontier, salmon, SH09, Measurement Gate, web adoption, EXP004/006/007, Graph pilots) | Task-scoped "no further dispatch". **Not** permission to reuse the hosts they cover; those hosts are excluded under F1(a) as previously used |

**Audit status: COMPLETE for request receipts. Browser-era views are covered only through tracked documents.**

- Some earlier work (browser projections and searches in the frontier, short-horizon and expanded discovery tasks) is recorded in tracked documents, not in full receipts. That coverage is only as good as those documents.
- The 138 JSON/JSONL files over 300 KB were not parsed. They were only searched, in place, for the candidate host names: **0 matches**. Non-JSON bodies were not searched.

## 3. Publisher documentation (documentation and terms pages only)

Legend: **DOC** = stated in official documentation; **3P** = third-party description only; **UNK** = unknown until an authorised preflight or further reading.

Every verdict below concerns **documented availability**, not eligibility (section 4).

### Observation-first

| | CAISO OASIS | EIA | ERCOT |
|---|---|---|---|
| 1. Unauthenticated route | DOC: SingleZip queries carry no credential ([OASIS FAQ](https://www.caiso.com/Documents/OASIS-Frequently-Asked-Questions.pdf)) | **No.** DOC: API v2 needs a registered key ([register](https://www.eia.gov/opendata/register.php), [docs](https://www.eia.gov/opendata/documentation.php)). Bulk files need no key | **No.** DOC: the Public API needs API Explorer registration, a subscription key and an ID token ([ERCOT developer](https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication)). Website report downloads: UNK |
| 2. Terms | **Ambiguous, not confirmed** (see "CAISO terms" below) | API terms of service exist; key excluded anyway | UNK |
| 3. Size-safe | DOC: date-range limits per report; zipped XML/CSV; last 39 months available | **No.** The electricity bulk files (`ELEC.zip`, `EBA.zip`) are listed at 286,363 and 681,768 on the [bulk page](https://www.eia.gov/opendata/bulkfiles.php). Units are not stated (taken to be KB) | UNK |
| 4. Dates and identifiers | DOC: trade dates; pricing-node and area identifiers | — | — |
| 5. Method fields | **Weak.** Nodes and areas, not registry or facility identifiers of firms; E6 is doubtful | — | — |
| 6. Overlap or stop | None found | None found | None found |
| 7. UNK | Whether a zipped response meets E3; whether node identifiers count as "facility identifiers"; terms. Price reports are excluded (no prices; source plan section 4.5) | — | — |
| **Documented availability** | Doubtful | **Excluded** (key; bulk not size-safe) | **Excluded** (key) |

**CAISO terms.** These quotations come from [privacy-terms-of-use](https://www.caiso.com/privacy-terms-of-use), as excerpts from a tool-assisted reading of the page.

- **General rule.** "No material or information from this Website … may be copied, reproduced, …" except "(i) as authorized in these Terms of Use, (ii) as expressly authorized in the materials and/or information contained on this Website, or (iii) as expressly authorized in writing by the California ISO".
- **Public-use materials.** A further paragraph allows materials "that are freely available for public use consistent with the general policies of the Public Records Act" to be used "provided that you keep intact all copyright, trademark and other proprietary notices and that you credit the California ISO".
- **API terms.** These grant a "revocable, non-exclusive … limited license", and state that "CAISO owns all right, title and interest in and to the CAISO API and CAISO Data".
- **OASIS.** The page has no OASIS-specific terms, and it does not say whether OASIS data is "freely available for public use", or whether SingleZip counts as the "CAISO API".

**Reading.** Research retrieval *may* be permitted under the public-use paragraph, with credit, but that is **not confirmed**. Under E2 the owner must confirm the terms. On this record, E2 cannot be confirmed without one of:

- your own reading accepting the public-use paragraph as covering OASIS;
- CAISO's written authorisation, which would mean contacting CAISO: your decision, not taken here.

Until then, treat CAISO as **E2 unconfirmed**.

### Relationship-first

| | GLEIF | Companies House | New SEC route |
|---|---|---|---|
| 1. Unauthenticated route | DOC: the API is "based on the data found in the GLEIF Golden Copy" ([GLEIF API](https://www.gleif.org/en/lei-data/gleif-api)); "provided for free" ([terms](https://www.gleif.org/en/meta/lei-data-terms-of-use)) | **No** for the API (developer key; 3P and forum). The bulk Free Company Data Product needs no key | DOC: public; 10 requests per second; declared User-Agent ([Accessing EDGAR data](https://www.sec.gov/os/accessing-edgar-data)) |
| 2. Terms | DOC: "provided under the CC0 licence". No circumvention; no endorsement claims | Bulk: UNK | Public domain (DOC fair-access policy) |
| 3. Size-safe | 3P: `page[size]` capped at 200; about 60 requests per minute ([pygleif](https://pygleif.readthedocs.io/en/latest/api/generated/pygleif.v2.client.GleifClient.html)) | **No.** 3P: monthly split files of about 100 MB | Per-filing documents are small, but see row 6 |
| 4. Dates and identifiers | LEIs; registration and relationship dates (3P; official reference not readable offline) | — | Accession numbers; filing dates |
| 5. Method fields | Parent relationships between two LEIs; the GLEIF relationship record is itself the original (E8) | — | EX-10/EX-21 relationships. In R3, only 2 of 14 8-Ks qualified |
| 6. Overlap or stop | None found | None found | **Excluded under F1(a).** Under F1(b), every used family (`Archives/edgar/data`, the daily and full indexes, `submissions`) and full-text search is excluded *if "route" means the URL family*. If it means the individual document, new filings are fresh. **This definition is an owner decision** |
| 7. UNK | Whether a relationship listing can be bounded to the packet window by date (E4); listed-company coverage | — | — |
| **Documented availability** | **Plausible (strongest)** | **Excluded** (key; bulk not size-safe) | Possible only under F1(b) with a document-level route definition; low yield |

### Event-first

| | CPSC | NTSB | FSIS |
|---|---|---|---|
| 1. Unauthenticated route | DOC: [Recall Retrieval Web Services Programmers Guide v1.4](https://www.cpsc.gov/s3fs-public/RecallRetrievalWebServicesProgrammersGuide20180917.pdf); no key described | **Unlikely.** DOC: the developer portal requires sign-in ([portal](https://developer.ntsb.gov/)); the key requirement is UNK. The bulk `avall.zip` archive is large (3P description) | Not reviewed: host excluded |
| 2. Terms | Federal publication (assumed); UNK | UNK | — |
| 3. Size-safe | DOC: `RecallDateStart`/`RecallDateEnd` bound the query. **Risk:** the guide warns that an invalid parameter "will retrieve ALL" records | **No** for bulk | — |
| 4. Dates and identifiers | DOC: `RecallID`, `RecallNumber`, `RecallDate`, `LastPublishDate` | — | — |
| 5. Method fields | DOC: firm collections (Manufacturers, Retailers, Importers, Distributors) each carry `Name` and `CompanyID`. Whether `CompanyID` is populated, and whether it is more than a CPSC-internal key, is UNK. If it is names only, E6 fails (F3) | — | — |
| 6. Overlap or stop | None found | None found | **Excluded:** recorded 403, unclear scope |
| 7. UNK | Population of `CompanyID`; response size for one quarter | — | — |
| **Documented availability** | Plausible, with identity risk | **Excluded or very unlikely** | **Excluded** |

### FDIC BankFind: one route excluded, one plausible (proposal only; not adopted)

**Access** ([API documentation](https://api.fdic.gov/banks/docs/)):

- DOC: "Users are currently not required to register and obtain a unique 'key'."
- JSON or CSV output; date filters in Elastic query syntax; definition files for Institution, History ("structure change events"), Financial and Failure data.
- Absent from every receipt and tracked document.

**Financial data (observation-first): excluded.** The source plan (section 4.5, and the "Potential outcome leakage" check in section 5) says:

> a packet may contain no outcome fields, such as later financial results, price moves or follow-on disclosures, so outcome-bearing environments are excluded at registration

Bank financial results are exactly that kind of field. A financial-data packet would put financial results inside the packet itself, so this environment is excluded under the existing rule. **The protocol is not changed to accommodate it.**

**History (event-first): plausible, with outcome-field risk.** Structure-change events (mergers, failures and similar) carry certificate identifiers and dates. Whether a history record carries outcome fields, such as later or follow-on events or financial amounts, is **UNK** until the History definition file is read offline. If it does, this environment is excluded too.

**Other UNK:** the limit and pagination parameters (given in the definition files, not the documentation page); the terms (none on that page).

**Not proposed:**

- **MSHA:** bulk flat files; size-safety is doubtful; its API is through the DOL key service.
- **Companies House bulk:** size.
- **NTSB, EIA and ERCOT:** as above.

## 4. Documented availability versus E1–E8 eligibility

Documentation can show at most that a route *exists*. Eligibility is judged on the one probe response (E3–E6), with your confirmation (E2). Nothing below is a finding of eligibility.

| Criterion | Assessable offline? | GLEIF | CPSC | FDIC history | CAISO |
|---|---|---|---|---|---|
| E1 Original publisher | Partly (domain) | Supported | Supported | Supported | Supported |
| E2 Open access and terms | **Owner confirmation only** | Supported by CC0 text; owner confirmation still required | Owner confirmation required (terms UNK) | Owner confirmation required (terms UNK) | **Ambiguous; unconfirmed** |
| E3 Complete, 4 MiB or less, machine-readable | **No: probe only** | UNK (page cap 3P) | UNK (date bound DOC) | UNK | UNK (zipped) |
| E4 At least 3 records dated in the window | **No** | UNK (date filter UNK) | UNK | UNK | UNK |
| E5 Stable unique identifiers | **No** (fields documented) | UNK | UNK | UNK | UNK |
| E6 Method fields non-empty | **No** | UNK | UNK (`CompanyID` population) | UNK | UNK (weak identifiers) |
| E7 Not stopped | Yes (section 2) | Pass | Pass | Pass | Pass |
| E8 Publisher's own records | Partly | Supported | Supported | Supported | Supported |
| Outcome-leakage exclusion (source plan section 4.5) | Partly (documentation) | No outcome fields expected | No outcome fields expected (UNK) | **UNK; check the definition file** | **Price reports (for example LMPs) excluded**: the pilot uses no prices, and the source plan excludes price moves. Only a non-price report (for example a demand forecast) could be registered; owner to judge |

## 5. Packet feasibility matrix

Revision 2 allows **two environments per method**: "the third packet-freeze start may not be spent on a third environment". F2 = 3 needs an explicit amendment of that rule.

| Method | As listed (first two) | Documented, plausible candidates after this audit | F1(a) strict (recommended) | F1(b) | Two vs three reserves |
|---|---|---|---|---|---|
| P1 Observation | CAISO, then EIA (excluded) | **CAISO only** (E2 unconfirmed; E6 weak). FDIC financial data is excluded as outcome-bearing | One doubtful environment. **Likely NOT_FORMED** | Unchanged | No viable second or third environment was found. **No gain** |
| P2 Relationship | GLEIF, then Companies House (excluded) | **GLEIF only** | **One environment** | A new SEC route as a low-yield second reserve, only under a document-level route definition and avoiding every SEC stop | **No gain** |
| P3 Event | CPSC, then NTSB (near-excluded) | CPSC, then FDIC history (outcome fields UNK) | Two candidates, both with UNK | Unchanged | A third (FSIS) is excluded. **No gain** |
| P4 Hypothesis | Your new mechanism statement; no starts | Same | — | — | — |

**Reading.**

- **The path to three pairs.** It needs P4 plus two of P1–P3. With P1 doubtful, it realistically needs **both** P2 (a single environment under F1(a)) and P3 to form.
- **Two viable reserves.** Only P3 has two documented candidates. It is **not** true that every source method has two viable reserves.
- **R3.** It lost two of four packets at formation.
- **F1(a) versus F1(b).**
  - F1(a) keeps P2 at one environment.
  - F1(b) adds only a low-yield SEC reserve, plus the route-definition ambiguity and the many SEC stops.
  - Neither fixes the gap at P1. I still lean to F1(a), for its simplicity and safety, but it does **not** make P2 robust.
- **F2.** Three reserves add nothing, because no viable third environment per method was found.
- **Status of the candidates.** These are proposals made before any probe, for you to adopt or reject. They are not substitutions after seeing content.

## 6. Independent reviewer logistics

**Role.** Each reviewer independently judges every blinded item of every formed packet, from a provided bundle only:

- **CONNECTION items:** is the economic connection confirmed against the original documents, merely plausible, false, or trivial? And is it meaningful?
- **Warnings and avoided repeats:** were they useful?

Each reviewer declares their exposure per item and personally seals both logs before seeing anyone else's. The reviewer never learns which arm produced an item.

**Skills.**

- Reading primary documents: regulatory notices, registries, filings and recall or market records.
- Entity identity: identifiers versus names, parent and subsidiary, look-alikes.
- Relationship and period reasoning: does the document state the relationship, and for the right dates?
- Telling a source fact from an inferred mechanism.
- Comfort recording UNKNOWN.
- Basic command-line use, to run one sealing command.

No market or graph expertise is needed. Investment views are irrelevant.

**Independence checklist** (each reviewer answers in writing before any bundle is sent):

- [ ] I will not operate, supervise, attest or blind any R4 arm or packet.
- [ ] I have not seen R4 arm ledgers, logs, suggestion exports, keys, alias keys or the R3 V001 exports.
- [ ] I will not discuss items with the other reviewer, the operator or the owner before both seals are committed.
- [ ] I will not use AI assessments or other people's judgments.
- [ ] I will not fetch sources unless the activation allows it (R1).
- [ ] I have no financial interest that the items could affect, or I have declared it.
- [ ] I am a different person from the other reviewer, and I will seal under my own name.

**Workload (assumptions marked).**

- **Items per packet.** R3 produced 17 and 19 items per packet, all CONNECTION (observed). R4 also shows warnings and avoided repeats: *assume 15–30 items per formed packet*.
- **Volume.** Four packets: *about 60–120 items per reviewer*. Fewer if packets fail to form.
- **Time per item.** R3 recorded no adjudicator minutes (UNKNOWN). *Assume 5–15 minutes per item*, including checking the evidence pack.
- **Total per reviewer.** *About 6–30 hours*, plus about 2 hours of briefing and practice and about 30 minutes per packet for sealing. Two reviewers: *about 15–65 person-hours*.
- **Calendar.** Reviews cannot start until a packet is blinded, and all reveals wait for every packet. *Allow 1–3 weeks.*

**Recruitment message (draft, for you to send if R4 resumes; neutral about the hypothesis):**

> I am running a small, structured research-methods study and am looking for two independent reviewers. You would assess about 60–120 short items, each linking public records (for example regulatory notices, registries or filings), and record whether the stated connection is supported by the original documents, using a provided guide and evidence pack. The estimated time is 6–30 hours over 1–3 weeks, at your own pace. You would need to work independently: no contact with the other reviewer or with me about the items until you have finished and sealed your log, which takes one command-line step. No investment advice or market data is involved. ⟨Compensation: …⟩. If interested, I will send the role description and an independence checklist.

**Separate evidence access and personal sealing.**

1. **Separate bundles.** The blinding preparer makes one bundle per reviewer: `snapshot.json`, `packet.jsonl`, `blind_v2.json`, the sheet, the content-addressed evidence pack and the guide. Each bundle goes to its reviewer by a separate private channel.
2. **Sealing environment.** Each reviewer needs the pinned checkout and Python environment to run `pilot adjudication-seal`. Options:
   - (a) the reviewer installs it, which is a real burden for non-technical reviewers;
   - (b) the reviewer uses a prepared machine or account that only they control.

   A technical assistant must never run the seal on a reviewer's behalf.
3. **Seal handover.** The reviewer sends the seal file first and keeps the logs. The logs are sent only after both seals are committed (runbook Stage 6).

**Is the burden proportionate?** The burden is **substantial relative to the result.**

- **The result.** At most four pairs, and realistically three, giving a descriptive classification only, with session variance confounded with arm.
- **R3.** All 10 graph-operator connections were judged trivial, which suggests a null or small graph increment is the likely outcome.
- **The cost.** Two qualified volunteers at 6–30 hours each. If they would need payment or would be hard to find, the cost probably exceeds R4's scientific value.

## 7. Owner decision package (recommendations only; nothing adopted)

| Decision | Options | Recommendation |
|---|---|---|
| **Pause** | Pause R4 pending a future decision; proceed to registration; or stop R4 | **Pause** ([pause recommendation](graph_pilot_r4_pause_recommendation_v001.md)) |
| *If R4 resumes:* | | |
| **D1** Arm analysts | (a) Hosted AI sessions with a human operator, as in R3. Needs separate registration of model and runtime, account context, resource exposure and stopping. (b) Human analysts | (a), if you accept that the result then measures AI-assisted research, not human research. (b) about doubles the people needed |
| **F1** Freshness | (a) Strict host level. (b) Record, filing set and exact route | Lean (a), for simplicity and safety against stops. It leaves P2 with one environment. Choose (b) only if you want an SEC reserve, and then also define "route" |
| **F2** Reserve depth | 2, or 3 (needs an amendment) | **2**. No viable third environment was found |
| **Reserves** | Keep as listed, or P1 CAISO (if E2 is confirmed); P2 GLEIF; P3 CPSC then FDIC history (if the definition file shows no outcome fields) | Do not register P1 until a documented observation-first route with confirmed terms is found |
| **U1** Warning reuse | (a) Only items that document the avoided action. (b) A new design | (a) |
| **R1** Reviewer retrieval | (a) Evidence pack only. (b) Receipted fetches within a ceiling | (a). It also lightens the reviewer workload |
| **Consensus and blinding** | Register the proposed rules (unanimous; unresolved disagreement; unblinded included plus an exclusion sensitivity) or amend them | Register as proposed |
| **Ceilings** | Per campaign 120 min / 6 starts / 10 searches / 8 MiB. Packet freeze 2 starts × 3 methods at 4 MiB each | Cumulative R4 ceiling: 16 h / 54 starts / 80 searches / 88 MiB (8 campaigns plus the freeze) |
| **Realistic total workload** | — | *Assumptions:*<br>• arms: up to 16 h analyst time plus about 16–20 h operator time;<br>• preflight and freeze: about 3 h;<br>• blinding: about 1–2 h per packet;<br>• reviewers: about 15–65 person-hours;<br>• you: about 6–10 h.<br>**Total: about 45–110 person-hours over 3–6 weeks** |
| **Roles to fill** | Operator(s); blinding preparer (never a reviewer, never an operator of an unfinished campaign); R1 and R2 | Find R1 and R2 first. They are the binding constraint |

## 8. Unresolved prerequisites to an activation document

**Offline evidence still needed (the basis for INCONCLUSIVE):**

1. **An observation-first route** that is documented, keyless, not outcome-bearing and has confirmed terms. If none can be found, P1 is planned as NOT_FORMED.
2. **CAISO E2:** your reading of the public-use paragraph, or a decision to seek written authorisation, or to drop CAISO.
3. **The FDIC History definition file:** check for outcome fields, and the limit and pagination parameters.
4. **GLEIF's official API reference:** whether relationship records can be bounded by date to the packet window (E4). The Postman page did not render offline.
5. **CPSC:** any official statement on what `CompanyID` is and whether it is populated (E6).

**Human and owner prerequisites (not resolvable offline):**

6. Two named, independent reviewers, recruited, checklist signed and briefed, with an agreed sealing environment.
7. The D1, F1, F2, U1 and R1 decisions, and the reserve order, registered.
8. E2 confirmed by you for every registered environment.
9. The hypothesis-first mechanism statement: new, not R3 P4's or any catalogued mechanism.
10. The environment preparation record and the activation receipt (runbook Stages 0a and 1).

**Overlap audit residue:** none blocking. The operator may confirm non-JSON private files when freezing the shortlist.

## 9. Classification and supporting evidence

**`INCONCLUSIVE_MORE_OFFLINE_EVIDENCE_NEEDED`.**

**Why not `FEASIBLE_FOR_OWNER_REGISTRATION_REVIEW`.**

- P1 has no documented route with confirmed terms: CAISO's E2 is ambiguous, and FDIC financial data is outcome-bearing.
- P2 has one environment under the recommended F1(a).
- Only P3 has two documented candidates, both with open UNKs.
- No candidate is established as E1–E8 eligible, because documentation cannot assess E3–E6.
- Registering now would mean committing to a design whose realistic path to three pairs depends on single environments.

**Why not `NOT_FEASIBLE_UNDER_CURRENT_RULES`.**

- No rule rules R4 out.
- GLEIF (CC0) and CPSC are documented, keyless, non-overlapping and unstopped.
- The open items in points 1–5 can be resolved by offline documentation reading or by your terms decision, without any probe.

**Value.** Even if the offline evidence resolves favourably, the reviewer cost is high relative to a descriptive result from three or four pairs, given R3's trivial graph-operator connections. This supports pausing rather than continuing preparation by default.
