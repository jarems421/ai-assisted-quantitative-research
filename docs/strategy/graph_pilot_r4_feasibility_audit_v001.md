# Graph Pilot R4: pre-activation feasibility audit (version 001)

> **R4 is NOT_RUN, not activated and not authorised.** This is an offline audit plus a review of public documentation and terms pages. No dataset, API, filing, record listing or bulk route was fetched, queried or probed. No packet was formed, no reviewer was contacted and no decision is adopted here.

Base: `main` `4ace618` (PR #9 merged as `4e1465b`). Inputs: the [source plan](graph_pilot_r4_source_plan_v001.md), [readiness matrix](graph_pilot_r4_operational_readiness_v001.md), [activation template](graph_pilot_r4_activation_template_v001.md), [runbook](graph_pilot_r4_runbook_v001.md), [pre-registration E1–E8](graph_pilot_preregistration.md#packet-eligibility-and-selection) and the [R4 protocol draft](graph_pilot_r4_protocol_proposed.md).

**Classification: `FEASIBLE_FOR_OWNER_REGISTRATION_REVIEW`, conditionally.**

- **Conditions.**
  - Several registered reserves must be replaced before registration (section 4).
  - Two independent reviewers must actually be secured (section 5).
- **Feasible in documentation, not demonstrated.** Feasibility here means that a plausible documented route exists for every method. No route is verified, and no packet is assured.
- **Value.** Scientific value is limited (section 6). If reviewers cannot be secured, stopping R4 is the better choice.

## 1. Answers in brief

1. **Do we have enough plausible fresh original sources?**
   - **Barely, and only after changes.** Of the eight named environments, documentation already rules out five or makes them very unlikely: EIA, ERCOT, Companies House, NTSB and FSIS.
   - **Still plausible:** CAISO, GLEIF and CPSC.
   - **Proposed replacement:** FDIC BankFind, a documented keyless route not in our history, for the observation and event methods.
2. **Which routes are legally and technically plausible?**
   - **GLEIF** is the strongest: CC0 licence, free, no registration.
   - **CPSC** is documented and keyless.
   - **FDIC BankFind** is documented and keyless.
   - **CAISO** is technically plausible, but its site terms restrict copying, so E2 is doubtful.
   - Every route remains unverified until an authorised preflight.
3. **Can we realistically form three comparable pairs?**
   - **Plausibly, but not reliably.** P4 (hypothesis-first) needs no source.
   - Three pairs need two of P1–P3. With the reserves as currently listed, P1 is likely NOT_FORMED, so success depends on both P2 and P3.
   - With the proposed reserves, each of P1–P3 has one or two plausible routes.
4. **What do reviewers require?**
   - Two qualified, independent people, each spending an estimated 6–30 hours (assumptions in section 5).
   - Each must run a sealing command from a pinned checkout.
   - This is the main practical cost.
5. **What must you decide?** D1, F1, F2, U1, R1, the replacement reserves, the ceilings, the people and the mechanism statement (section 7).

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

### Observation-first

| | CAISO OASIS | EIA | ERCOT |
|---|---|---|---|
| 1. Unauthenticated route | DOC: SingleZip queries carry no credential ([OASIS FAQ](https://www.caiso.com/Documents/OASIS-Frequently-Asked-Questions.pdf)) | **No.** DOC: API v2 needs a registered key ([register](https://www.eia.gov/opendata/register.php), [docs](https://www.eia.gov/opendata/documentation.php)). Bulk files need no key | **No.** DOC: the Public API needs API Explorer registration, a subscription key and an ID token ([ERCOT developer](https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication)). Website report downloads: UNK |
| 2. Terms | **Doubtful.** DOC: site terms say "No material or information … may be copied, reproduced" except as authorised, while asking users to keep notices and "credit the California ISO" ([terms](https://www.caiso.com/privacy-terms-of-use)). Needs your own reading | API terms of service exist; key excluded anyway | UNK |
| 3. Size-safe | DOC: date-range limits per report; zipped XML/CSV; last 39 months available | **No.** The electricity bulk files (`ELEC.zip`, `EBA.zip`) are listed at 286,363 and 681,768 on the [bulk page](https://www.eia.gov/opendata/bulkfiles.php). Units are not stated (taken to be KB) | UNK |
| 4. Dates and identifiers | DOC: trade dates; pricing-node and area identifiers | — | — |
| 5. Method fields | **Weak.** Nodes and areas, not registry or facility identifiers of firms; E6 is doubtful | — | — |
| 6. Overlap or stop | None found | None found | None found |
| 7. UNK | Whether a zipped response meets E3; whether node identifiers count as "facility identifiers"; terms | — | — |
| **Verdict** | Plausible but weak | **Excluded** (key; bulk not size-safe) | **Excluded** (key) |

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
| **Verdict** | **Strong** | **Excluded** (key; bulk not size-safe) | Possible only under F1(b) with a document-level route definition; low yield |

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
| **Verdict** | Plausible, with identity risk | **Excluded or very unlikely** | **Excluded** |

### Proposed replacement (documented, consistent with the rules; not adopted)

**FDIC BankFind Suite** ([API documentation](https://api.fdic.gov/banks/docs/)):

- **Access.** DOC: "Users are currently not required to register and obtain a unique 'key'." JSON or CSV output; date filters in Elastic query syntax; definition files for Institution, History ("structure change events"), Financial and Failure data.
- **Not in history.** Absent from every receipt and tracked document.
- **Fits two methods:**
  - **observation-first:** quarterly financial quantities per FDIC certificate number;
  - **event-first:** structure-change events with certificate identifiers.
- **UNK:** the limit and pagination parameters (not on the documentation page; given in the linked definition files); the terms (none on that page).
- **Caveat.** Using one publisher for two packets weakens the separation between them. You may prefer it for only one method.

**Not proposed:**

- **MSHA:** bulk flat files; size-safety is doubtful; its API is through the DOL key service.
- **Companies House bulk:** size.
- **NTSB, EIA and ERCOT:** as above.

## 4. Packet feasibility matrix

Revision 2 allows **two environments per method**: "the third packet-freeze start may not be spent on a third environment". F2 = 3 needs an explicit amendment of that rule.

| Method | As listed (first two) | Proposed order (if adopted) | F1(a) strict | F1(b) | Two vs three reserves |
|---|---|---|---|---|---|
| P1 Observation | CAISO, then EIA. **EIA is dead**, so P1 rests on CAISO alone (terms, E3 and E6 doubtful). **Likely NOT_FORMED** | FDIC financials, then CAISO | Unaffected | Unaffected | A third (ERCOT) is dead. **No gain** |
| P2 Relationship | GLEIF, then Companies House. **Companies House is dead**, so P2 rests on GLEIF alone | GLEIF, then a new SEC route (F1(b) only) or none | Only GLEIF | SEC adds a low-yield reserve, and only under a document-level route definition | **No gain** under F1(a) |
| P3 Event | CPSC, then NTSB. **NTSB is near-dead**, so P3 rests on CPSC alone (identity risk) | CPSC, then FDIC history | Unaffected | Unaffected | A third (FSIS) is excluded. **No gain** |
| P4 Hypothesis | Your new mechanism statement; no starts | Same | — | — | — |

**Reading.**

- **Three pairs.** They need P4 plus two of P1–P3.
- **As listed,** each source method rests on a single live environment, so three pairs is possible but fragile.
- **With the proposed order,** each method has two plausible routes, and three pairs becomes a reasonable expectation. It is still not assured: E2–E6 are untested, and R3 lost two of four packets at formation.
- **F1.** F1(b) matters only for the SEC. Under the proposed order, **F1(a) is sufficient**, and avoids both the route-definition ambiguity and the many SEC stops. This revises the source plan's earlier recommendation of (b).
- **F2.** Three reserves add nothing, because no viable third environment per method was found.
- **Status of the proposals.** These are proposals made before any probe, for you to adopt or reject at registration. They are not substitutions after seeing content.

## 5. Independent reviewer logistics

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
- **Volume.** Four packets: *about 60–120 items per reviewer*.
- **Time per item.** R3 recorded no adjudicator minutes (UNKNOWN). *Assume 5–15 minutes per item*, including checking the evidence pack.
- **Total per reviewer.** *About 6–30 hours*, plus about 2 hours of briefing and practice and about 30 minutes per packet for sealing. Two reviewers: *about 15–65 person-hours*.
- **Calendar.** Reviews cannot start until a packet is blinded, and all reveals wait for every packet. *Allow 1–3 weeks.*

**Recruitment message (draft, for you to send; neutral about the hypothesis):**

> I am running a small, structured research-methods study and am looking for two independent reviewers. You would assess about 60–120 short items, each linking public records (for example regulatory notices, registries or filings), and record whether the stated connection is supported by the original documents, using a provided guide and evidence pack. The estimated time is 6–30 hours over 1–3 weeks, at your own pace. You would need to work independently: no contact with the other reviewer or with me about the items until you have finished and sealed your log, which takes one command-line step. No investment advice or market data is involved. ⟨Compensation: …⟩. If interested, I will send the role description and an independence checklist.

**Separate evidence access and personal sealing.**

1. **Separate bundles.** The blinding preparer makes one bundle per reviewer: `snapshot.json`, `packet.jsonl`, `blind_v2.json`, the sheet, the content-addressed evidence pack and the guide. Each bundle goes to its reviewer by a separate private channel.
2. **Sealing environment.** Each reviewer needs the pinned checkout and Python environment to run `pilot adjudication-seal`. Options:
   - (a) the reviewer installs it, which is a real burden for non-technical reviewers;
   - (b) the reviewer uses a prepared machine or account that only they control.

   A technical assistant must never run the seal on a reviewer's behalf.
3. **Seal handover.** The reviewer sends the seal file first and keeps the logs. The logs are sent only after both seals are committed (runbook Stage 6).

**Is the burden proportionate?** The burden is **substantial relative to the result.**

- **The result.** At most four pairs, giving a descriptive classification only, with session variance confounded with arm.
- **R3.** All 10 graph-operator connections were judged trivial, which suggests a null or small graph increment is the likely outcome.
- **The cost.** Two qualified volunteers at 6–30 hours each. If they would need payment or would be hard to find, the cost probably exceeds R4's scientific value.

## 6. Owner decision package (recommendations only; nothing adopted)

| Decision | Options | Recommendation |
|---|---|---|
| **D1** Arm analysts | (a) Hosted AI sessions with a human operator, as in R3. Needs separate registration of model and runtime, account context, resource exposure and stopping. (b) Human analysts | (a), if you accept that the result then measures AI-assisted research, not human research. (b) about doubles the people needed |
| **F1** Freshness | (a) Strict host level. (b) Record, filing set and exact route | **(a)**. It is sufficient with the proposed order, and simpler and safer against stops. Choose (b) only if you want the SEC, and then also define "route" |
| **F2** Reserve depth | 2, or 3 (needs an amendment) | **2**. No viable third environment was found |
| **Reserves** | Keep as listed, or adopt the proposed order: P1 FDIC financials then CAISO; P2 GLEIF; P3 CPSC then FDIC history | Adopt the proposed order, possibly using FDIC for only one method |
| **U1** Warning reuse | (a) Only items that document the avoided action. (b) A new design | (a) |
| **R1** Reviewer retrieval | (a) Evidence pack only. (b) Receipted fetches within a ceiling | (a). It also lightens the reviewer workload |
| **Consensus and blinding** | Register the proposed rules (unanimous; unresolved disagreement; unblinded included plus an exclusion sensitivity) or amend them | Register as proposed |
| **Ceilings** | Per campaign 120 min / 6 starts / 10 searches / 8 MiB. Packet freeze 2 starts × 3 methods at 4 MiB each | Cumulative R4 ceiling: 16 h / 54 starts / 80 searches / 88 MiB (8 campaigns plus the freeze) |
| **Realistic total workload** | — | *Assumptions:*<br>• arms: up to 16 h analyst time plus about 16–20 h operator time;<br>• preflight and freeze: about 3 h;<br>• blinding: about 1–2 h per packet;<br>• reviewers: about 15–65 person-hours;<br>• you: about 6–10 h (registration, terms reading, mechanism statement, M/H after unsealing).<br>**Total: about 45–110 person-hours over 3–6 weeks** |
| **Roles to fill** | Operator(s); blinding preparer (never a reviewer, never an operator of an unfinished campaign); R1 and R2 | Find R1 and R2 first. They are the binding constraint |

## 7. Unresolved prerequisites to an activation document

1. **Two named, independent reviewers**, recruited, checklist signed and briefed, with an agreed sealing environment. *This cannot be resolved offline. It is the main risk.*
2. **The D1, F1, F2, U1 and R1 decisions**, and the reserve order, registered.
3. **E2 terms confirmed by you** for every registered environment. CAISO's copying restriction needs your explicit reading, or CAISO should be dropped.
4. **Offline documentation reading still possible:**
   - the FDIC definition files (limit parameter; fields);
   - GLEIF's official API reference: whether relationship records can be filtered by date. The Postman page did not render offline.
5. **Overlap audit residue:** none blocking. The operator may confirm non-JSON private files when freezing the shortlist.
6. **The hypothesis-first mechanism statement:** new, not R3 P4's or any catalogued mechanism.
7. **The environment preparation record and the activation receipt** (runbook Stages 0a and 1).

## 8. Classification and supporting evidence

**`FEASIBLE_FOR_OWNER_REGISTRATION_REVIEW`.** Supporting evidence:

- **Sources.** Every source method has at least one documented, keyless, non-overlapping original-publisher route with no persisted stop: GLEIF (CC0), CPSC, FDIC BankFind and, more weakly, CAISO. With the proposed order, F1(a) alone gives each method two plausible routes.
- **Reviewers.** The reviewer arrangements are well defined, workable with existing code and commands, and need no new engineering.
- **What remains unknown** cannot be resolved offline: E2–E6 on actual responses, and the recruitment of reviewers.

**Two qualifications.**

1. **Feasibility is conditional.** It holds only if you adopt replacement reserves. As currently listed, three of the six registered environments are dead from documentation.
2. **Value may not justify the cost.** If two qualified independent reviewers cannot be secured at acceptable cost, I recommend **stopping R4** rather than preparing further. R3's trivial graph-operator connections and the descriptive-only design limit what R4 can show.
