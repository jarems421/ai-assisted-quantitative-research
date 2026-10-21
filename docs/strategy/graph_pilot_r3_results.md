# Graph pilot revision 3: descriptive results

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-22. Result: INCONCLUSIVE.** By rule, two pairs receive no graph-increment classification. The comparison is also **potentially unblinded**: the owner adjudicated after seeing the compromised V001 sheets. Within those limits, one pattern is clear. **All 10 connections produced by graph operators were adjudicated trivial. All 10 confirmed connections came from analyst reading:** 8 in the structured arms and 2 by reading in the graph arms. This is a description of two small, exploratory packets, not evidence about Graph v1 in general. It is not a scientific null on the graph either, and it says nothing about investment value.

Final dispositions are pending with the owner (see the [M/H packet](graph_pilot_r3/mh_decision_packet.md)). Until they are recorded, time to decisive falsification is not computable.

## 1. Original stopped revision 2

Unchanged: 4 starts and 5,537,804 bytes. P1, P2 and P3 did not form, and no campaign ran ([freeze report](graph_pilot_packet_freeze_report.md)).

## 2. Revision 3 source preparation (exploratory, amended after reviewing the failures)

| Packet | Result |
|---|---|
| P1 | Not restarted |
| P2 | **NOT_FORMED.** 2 of the 14 frozen 8-K accessions qualify (Greif's purchase agreement; Royal Gold's credit amendment); 3 were required |
| P3 | Formed: a complete keyless openFDA response with `limit=50`, giving five Class I device recalls reported 2025-07-02 |
| P4 | Formed: the owner's frozen recall-to-replacement-component mechanism |

## 3. Formed packets

| Packet | Snapshot | Pair | Arm order |
|---|---|---|---|
| P3 event-first | `156acba2…` | S `DLC-GP3-S`, G `DLC-GP3-G` | S then G |
| P4 hypothesis-first | `80a583a7…` | G `DLC-GP4-G`, S `DLC-GP4-S` | G then S |

## 4. Campaign results

| Campaign | Observations (from packet) | Relationships | Sources fetched | Claims (versions) | Frozen | Mechanical M blockers | Arm recommendation |
|---|---|---|---|---|---|---:|---|
| P3-S | 8 (5) | 2: 1 documented and verified, 1 unverified | SEC 3, AccessGUDID 1 | 1 (2) | yes | 17 | STOP |
| P3-G | 8 (4) | 2 unverified, 1 of them name-match only | SEC 4 | 1 (3) | yes | 16 | STOP |
| P4-S | 6 (0) | 4 unverified, 2 of them name-match only | NHTSA 2, SEC 3 | 1 (4) | yes | 20 | STOP |
| P4-G | 7 (0) | 3 unverified | NHTSA 4, SEC 2 | 2 (3, 2) | yes | 16 and 20 | STOP |

**Records and reviews:**
- **Depth:** all observations are at original-field depth, except one indexed description in P3-G and one original record in P4-S.
- **Clocks:** every first-public time is UNKNOWN.
- **Reviews:** sceptic reviews are assistant drafts. No human M or H review exists.

**Original frozen M passes: 0 in every arm.** Every candidate keeps 16–20 mechanical blockers, so `M_PASSED` is refused whatever the review.

**Selection status:** 4 of the 5 candidates carry post-outcome status; the sealed flags are now in `mh_review_flags.json`.

**Decisive missing variables** recur across all arms:
- **Identity:** labeller, supplier or firm identity at registry level, joined to the listed parent for the period.
- **Allocation:** a recall-specific amount rather than combined quality or remediation charges.
- **Product economics:** product or remedy-part revenue, price and units, including whether a recall quantity counts boxes or devices.
- **Commercial terms:** cost-sharing, reimbursement and warranty terms.
- **Timing:** first-public times.

**Original versus retrospective evidence.** All fetched evidence is original-publisher bytes (SEC, NHTSA and AccessGUDID) retrieved in 2026, so values are current versions. Several records postdate the packet window, including 2026 NHTSA documents and later filings. They are flagged and must not be read as information available in 2025. The AI assessment also reports, unverified, that FDA's recall page posted Z-1958-2025 on 2025-06-20, not on the 2025-07-02 report date.

## 5. Graph versus structured search (descriptive, potentially unblinded)

**Adjudicated outcomes by origin:**

| Origin | Items | Confirmed | Plausible, unverified | Trivial | False |
|---|---:|---:|---:|---:|---:|
| Graph arm, via a graph operator (`same-gap` 6, `revisit` 3, `next` 1) | 10 | **0** | 0 | **10** | 0 |
| Graph arm, via reading | 11 | 2 | 7 | 2 | 0 |
| Structured arm (reading 14, `baseline-search` 1) | 15 | 8 | 3 | 4 | 0 |

**Registered dimensions** (`pilot report --export blind_v2.json`; all analyst minutes, graph time included):

| Packet | Dimension | S | G |
|---|---|---:|---:|
| P3 | Verified connections per analyst-hour (accepted, confirmed and meaningful) | 2.82 (1) | 0.0 (0) |
| P3 | Confirmed connections declined or left unresolved by the arm | 4 | 0 |
| P3 | False or premature joins made | 0 | 0 |
| P3 | Median minutes per connection | 1.0 | 1.0 |
| P3 | Review burden (items) | 8 | 9 |
| P4 | Verified connections per analyst-hour | 5.45 (2) | 5.07 (2) |
| P4 | False or premature joins made (accepted but unverified) | 0 | 2 |
| P4 | Median minutes per connection | 2 | 1.0 |
| P4 | Review burden (items) | 7 | 12 |
| Both | Duplicate research avoided | 0 | 0 |
| Both | Original frozen M passes per hour | 0 | 0 |
| Both | Time to decisive falsification | pending dispositions | pending dispositions |

**Reading the numbers:**
- **Pooled verified connections per analyst-hour:** S 4.16, G 3.15. No benefit dimension favours G; the verified rate favours S in both packets.
- **Classification:** `INCONCLUSIVE` (fewer than three pairs).
- **Graph-only rediscoveries:** none of the graph arms' connections attributed `GRAPH_ONLY` was confirmed, so there are no graph-only discoveries in this sample.
- **Benefits that did not appear:** avoided errors and faster falsification could also count as graph benefits under the protocol. Neither appeared: no avoided repeats were logged, and falsification timing awaits dispositions.

**What the graph operators produced.** They produced analogies to historical investigations through shared requirement tags, for example capacity, allocation and supplier exposure linked to the salmon, Chevron, BASF or insurance memory. The adjudicator judged every one trivial: a generic research warning, not an economic connection. This agrees with the AI assessment's design observation. The useful connections were record-level: the product-identifier joins, the recall supersession links, and the issuer disclosure showing that a supplier may bear recall costs, which challenges the mechanism. All of these came from reading the originals.

## 6. Limitations and deviations

- **Potentially unblinded.** The V001 sheets leaked arm ids, and the owner saw them before adjudicating ([blinding correction](graph_pilot_r3_blinding_correction.md)). The owner judged first and then reported an exact match with the AI assessment; that assessment was also made with V001 exposure. No independent adjudication exists.
- **Two pairs, two methods.** The pairs cover the event-first and hypothesis-first methods only. Each arm was a single session, so session variance is confounded with arm. No statistical claim is possible.
- **`SUG-` ids not used.** The graph arms logged graph-operator connections under `CON-` ids instead of their `SUG-` ids, a protocol deviation. The registered "share of graph suggestions false or trivial" therefore reads 0/0. The equivalent by operator is 10/10 trivial.
- **Unreliable minutes.** Self-logged minutes over-state some arms by up to about 9 minutes. All per-hour figures inherit that error, and campaigns used only 14–24 of their 120 minutes.
- **Outcome exposure before a freeze (P4-G CAND-2).** Snippets with outcome-like figures were seen first, and 4 of the 5 candidates have post-outcome status. These must be weighed at disposition.
- **Smaller deviations:**
  - P4-S was interrupted for about 30 minutes, with no extension and no request in flight;
  - two arms wrote their connection logs at the end;
  - two blinding-tool reference fixes;
  - the packet-builder resume.
- **Not evidence of failure.** P1 and P2 failed at source formation; that is a sourcing outcome, not evidence about the graph.

## Recommendation (not implemented)

**Tighten or simplify weak discovery operators**, specifically the requirement-tag analogy operators (`same-gap`, and `revisit` and `next` where they reach historical memory only through requirement tags).

**Possible changes:**
- type these connections separately as methodological warnings;
- exclude them from discovered-connection counts;
- require an identifier, document or relationship join before an item counts as a connection.

Any change needs a separate owner decision and a new evaluation; this pilot does not establish Graph v1's value beyond competent structured search.
