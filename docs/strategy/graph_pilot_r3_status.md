# Graph pilot revision 3: execution status (awaiting owner adjudication)

**2026-10-21. Status: all formed campaigns complete; blinded adjudication is pending with the owner.** Revision 3 is an **exploratory amended attempt**. Its routes were changed after the revision 2 source-formation failures had been reviewed ([authority](owner_graph_pilot_r3_2026-10-21.md)). No graph-versus-structured-search outcome is reported yet: arm labels stay sealed until adjudication is complete.

**Only two packet pairs (P3, P4) formed. Under the owner's rule they will be described but receive no graph-increment classification.**

## 1. Original stopped revision 2 (unchanged)

Recorded in the [freeze report](graph_pilot_packet_freeze_report.md) and its [receipt](graph_pilot_receipt.json): 4 starts and 5,537,804 bytes. P1, P2 and P3 did not form, no campaign ran, and the private `final_stop.json` is untouched.

## 2. Revision 3 source preparation

| Packet | New requests | Result |
|---|---:|---|
| P1 | 0 | Not restarted (owner) |
| P2 | 14 (17 cumulative) | **`NOT_FORMED`**: 2 of the 14 frozen accessions qualify, and 3 are required |
| P3 | 1 (2 cumulative) | **Formed** |
| P4 | 0 | **Formed** |

**P2 accessions checked, in frozen order 2–15:**
- **Qualified (2):**
  - **order 7, Greif (`0000043920-25-000038`):** Item 1.01 and an EX-10.1 *Purchase and Sale Agreement* dated 2025-06-30. The parties are Greif Packaging LLC (seller), Packaging Corporation of America (purchaser) and Greif, Inc. (guarantor). The object is the equity of Greif Containerboard Solutions and Box-Board Holding; the price is $1.8 billion, subject to adjustment.
  - **order 12, Royal Gold (`0000085535-25-000092`):** Item 1.01 and an EX-10.1 *Sixth Amendment to Revolving Facility Credit Agreement* dated 2025-06-26. The borrowers are Royal Gold, Inc. and RGLD Gold AG, with named subsidiary guarantors and The Bank of Nova Scotia as administrative agent. The individual lenders appear only on the signature pages.
- **Not used:** order 2, Constellation Brands, hit the 4 MiB size stop, so its prefix was not used.
- **Not qualifying:** the other 11 had no EX-10 and no Item 1.01. Their items were Regulation FD disclosure, other events, Item 2.03 obligations, Item 2.01 completion (with a press release), Item 5.02 and dividends.
- **Usage:** P2 used 17 of its 17 cumulative starts and 14,767,792 of 24 MiB.

**P3's single authorised request** (`limit=50`) returned HTTP 200 and was complete at 1,120,085 bytes, out of 599 records in the window. The packet is the first five rows by `report_date`, then `recall_number`. They are five Class I device recalls reported 2025-07-02: SunMed Holdings `Z-1904-2025`, and Integra LifeSciences `Z-1958`, `Z-1959`, `Z-1960` and `Z-1961-2025`. The recalling firms are name-only identities, and these rows are not a population.

**P4** is the owner's frozen recall-to-replacement-component mechanism, with no request.

## 3. Formed packets

| Packet | Snapshot SHA-256 | Packet prefix | Committed before arms |
|---|---|---|---|
| P3 event-first | `156acba2…3bad` | `DLC-GPKT-3`, 7 events, head `b573457a…` | `5f3b7ef` |
| P4 hypothesis-first | `80a583a7…a363` | `DLC-GPKT-4`, 1 event, head `670fe0eb…` | `5f3b7ef` |

## 4. Campaigns (arm order as registered)

**How each campaign ran:**
- Each arm was a fresh agent session in its own git worktree, created from `5f3b7ef`, on its own branch, which is not merged.
- The prompts were rendered mechanically from the fixed [revision 3 instructions](graph_pilot/arm_instructions_r3.md). They are identical except for the packet, arm and tool fields; this was checked by diff.
- The coordinator relayed nothing between arms and did not read arm findings while arms were running.

| Campaign | Commit | Wall clock (UTC) | Logged min | Graph min | Starts | Searches | Bytes | Events | Connections |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| P3-S (first) | `d99f114` | 19:25–19:38 | 21.25 | 0 | 4 | 4 | 4,027,465 | 40 | 8 |
| P3-G | `0630496` | 19:39–19:54 | 14.4 | 2.5 | 4 | 3 | 5,664,632 | 38 | 9 |
| P4-G (first) | `40158c6` | 19:55–20:13 | 23.68 | 4.99 | 6 | 6 | 2,511,515 | 56 | 12 |
| P4-S | `8248440` | 20:14–21:04 (outage about 20:30–21:02) | 22 | 0 | 5 | 6 | 4,835,031 | 38 | 7 |

**Results across the four campaigns:**
- Every ledger replays (chain and rules PASS), every connection log validates, and `pilot account` reports no violations.
- All requests returned HTTP 200 complete, with no denial, retry or stopped route.
- Each campaign used well under its 120 minutes.

**Cumulative pilot use, across both revisions:**

| Resource | Used | Ceiling |
|---|---:|---:|
| Source starts | 38 | 60 |
| Response bytes | 35.4 MiB | 88 MiB |
| Searches | 19 | 92 |
| Arm minutes logged | about 81 | – |

## 5. Graph versus structured search

**Not yet available.** The [P3 sheet](graph_pilot_r3/P3/adjudication_sheet.md) (17 items) and [P4 sheet](graph_pilot_r3/P4/adjudication_sheet.md) (19 items) are shuffled and arm-hidden. The keys are hash-sealed (P3 `e9ab04ff…`, P4 `270f6da3…`) and held privately. The paired report runs only after the owner's adjudications are committed and the keys are unsealed. With two pairs it is descriptive only.

## 6. Protocol limitations and deviations (disclosed by arms or found by the coordinator)

- **Self-reported minutes are imprecise:**
  - P3-S logged about 8.7 minutes more than its clock;
  - P4-G's first efforts logged 10 minutes for about 2.7 elapsed;
  - P4-S logged about 3.5 minutes more than its clock;
  - P3-G logged some efforts ahead of the clock.

  All minutes-based dimensions inherit this error, and minutes are mostly far below the 120 available.
- **Outcome exposure before freeze (P4-G).** Search snippets showed outcome-related values (a recall expansion and a quarterly net-sales figure) **before** CAND-2 was frozen. CAND-1's selection flag was corrected in a new version. The owner must weigh this at the M/H stage.
- **Outcome exposure, route declined (P3-G).** A search summary showed post-event values for a similarly named borrower. That route was declined, with no claim formed.
- **Late connection logs.** P3-G and P4-G wrote their connection logs in one batch at the end, not as the work happened.
- **Interruption (P4-S).** P4-S was interrupted by an API session limit, from about 20:30Z to 21:02Z. It resumed in the same session within its unchanged window, after a procedural note only. No request was in flight.
- **Coordinator tooling fixes** during blinding, with no data changed:
  - `pilot blind` now accepts an accepted connection's ledger record when it is qualified with the arm's own campaign id;
  - it also accepts records of review and disposition kinds.
- **Packet-builder resume.** The coordinator's P3 packet-builder script failed after the campaign and source records. The same ledger was resumed by appending; nothing was deleted.
- **Blinding is partial.** The same owner operates and adjudicates. Record content can hint at the arm; this was checked by mechanical scans, which found no leaks in the exports.

## 7. Owner action required

1. **Adjudicate every item** in both sheets. Fill in `adjudications_TEMPLATE.jsonl` in each packet directory:
   - `outcome`, plus `checked_evidence` hashes or locators for any confirmation;
   - `economic_meaning`;
   - `adjudicator` (your name) and `recorded_at_utc`;
   - `adjudicator_minutes` if known.

   Save each as `adjudications.jsonl`. Adjudicate without consulting arm branches.
2. **After adjudication**, the coordinator will:
   - validate both logs;
   - unseal the keys;
   - present the frozen candidates of both arms, arm-neutral and shuffled, with evidence packets for **your** M/H decisions and dispositions (each REJECT or HOLD naming its decisive record);
   - then run the descriptive paired report.

No M/H decision, adjudication or disposition is made without the owner.
