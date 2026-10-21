# Graph pilot: packet freeze results and stop

**2026-10-21. Result: STOPPED before any campaign: no packet pair formed that the owner approved running.** The pilot was activated at `6c377d8` under the [active authorisation](owner_graph_pilot_2026-10-21.md). Packet freezes then ran in registered order, using four ordinary source starts and 5,537,804 response bytes, with zero searches. P1, P2 and P3 did not form. Only P4 (hypothesis-first, no source request) could form, and the owner [did not approve a P4-only comparison](owner_graph_pilot_route_amendment_2026-10-21.md). So no arm campaign, snapshot, connection log, adjudication or disposition exists. Q2 is unanswered; this is not evidence about the graph either way.

## Packet outcomes

| Packet | Requests | Outcome | Decisive fact |
|---|---:|---|---|
| P1 Observation-first | 0 | `NOT_FORMED` at preflight | ECHO's readable EPA documentation cannot apply the 2025-Q3 window outcome-blind; the PHMSA documentation returned 403 |
| P2 Relationship-first | 3 | `NOT_FORMED` | The first mechanically selected 8-K contains no `EX-10`, and the fixed budget allows no second filing |
| P3 Event-first | 1 | `NOT_FORMED` | The single permitted response exceeded the 4 MiB size stop, so it is incomplete and fails E3 |
| P4 Hypothesis-first | 0 | Not run | It could form, but a P4-only comparison is not approved |

## Receipts

Bodies are kept privately under ignored `data/raw/graph_pilot_20261021/`. Every request was made with `graph_pilot/fetch_one.py`: one request each, no retries, no redirects, no authentication. SEC requests declared the configured identity, which is redacted in the receipts.

| # | UTC start | URL | HTTP | Bytes | SHA-256 | Complete |
|---|---|---|---:|---:|---|---|
| P2-1 | 18:56:32 | `https://www.sec.gov/Archives/edgar/daily-index/2025/QTR3/index.json` | 200 | 42,826 | `607e179d…58a2` | yes |
| P2-2 | 18:56:47 | `https://www.sec.gov/Archives/edgar/daily-index/2025/QTR3/form.20250701.idx` | 200 | 1,087,985 | `bdf95bb0…771d` | yes |
| P2-3 | 18:57:12 | `https://www.sec.gov/Archives/edgar/data/4962/0000004962-25-000073.txt` | 200 | 212,689 | `9220af9f…141b` | yes |
| P3-1 | 18:57:24 | `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=1000` | 200 | 4,194,304 | `bee4be55…aa23` | **no: 4 MiB size-stop prefix** |

**Budgets used:**
- **P2 freeze:** 3/3 starts, 1,343,500 of 6 MiB.
- **P3 freeze:** 1/3 starts, 4,194,304 of 6 MiB.
- **Pilot:** 4/60 starts, 0/92 searches, 5.28 of 88 MiB.
- **Coordinator time:** packet preparation took about 2 minutes of wall-clock request time. Preflight documentation time was not separately logged.

No ceiling was reached and no stopped route was contacted.

## P2 detail

1. **Daily index.** `index.json` lists 64 daily form indexes for 2025 Q3. The rule selected the earliest, `form.20250701.idx` (1,063 KB).
2. **Eligibility.** The index passes E1–E8:
   - it is SEC's own host, and the response was complete;
   - it is a fixed-width table of form type, company, CIK, date filed and file name;
   - it holds 307 `8-K` rows dated 2025-07-01, each with a CIK and a submission locator;
   - the accession number is the identifier, unique except for 4 co-filed filings listed under more than one CIK;
   - no stop applies.
3. **Packet records.** The first five `8-K` records, by date then accession number, were:
   - American Express (CIK 4962, `0000004962-25-000073`);
   - Constellation Brands (16918, `0000016918-25-000074`);
   - JPMorgan Chase (19617, `0000019617-25-000509` and `-000510`);
   - Delmarva Power & Light (27879, `0000027879-25-000008`).
4. **Formation check.** Record 1's complete original submission lists the document types `8-K`, `EX-99.1`, `EX-101.*`, `GRAPHIC`, `XML`, `JSON` and `ZIP`, under the items "Regulation FD Disclosure" and "Financial Statements and Exhibits". **No `EX-10`.** Under the fixed rule, no relationship can be claimed from an index record, and no further filing may be opened.

## P3 detail

- **The response:** the keyless request was accepted (HTTP 200, no authentication denial). Its metadata reports `total: 599` records in the window, against `limit: 1000`. Records average about 18 KB each, mostly long product and code text, so the complete body would have been about 10 MB.
- **Why it fails:** only a labelled 4 MiB prefix was kept, holding about 228 records. It fails E3 (complete response), and its records were **not used**.
- **Coordinator error.** Choosing `limit=1000` in the fixed route was a route-design error by the coordinator, made on an underestimate of record size. A smaller fixed limit could have produced a complete response. The rule permits neither a retry nor a changed query, so the error stands rather than being repaired.

## What this shows

- **Getting a packet was the hard part.** With the frozen freeze budget (3 starts) and strict single-response rules, every documented, credential-free route either could not be fixed or failed on its first response.
- **Why each packet failed:**
  - **P2:** the one-filing check is structurally unlikely to find an `EX-10`, because the index carries no exhibit or item information. A start had to go on the directory listing to avoid guessing the file name.
  - **P3:** failed on a fixable parameter.
  - **P1:** failed on ECHO's documentation and access, not on data quality.
- **What was not measured.** No discovery method was exercised, and no graph or structured-search result exists. M passes: 0 by absence of campaigns, not by failure. H: none.

## Owner decision required

The pilot is closed (`final_stop.json`). Only the owner can choose to:

1. **Close the pilot as is.** No further requests.
2. **Approve P4 alone.** At most 2 campaigns, 4 h, 12 starts. Q2 stays `INCONCLUSIVE` by rule; previously declined.
3. **Amend routes again, then run:**
   - **P3:** the same keyless query with a size-safe fixed limit (for example `limit=100`, about 1.8 MB), selecting the first five by `report_date` then `recall_number`. This would be a second request to the same endpoint.
   - **P2:** a larger freeze start budget, allowing a fixed number of 8-K submissions to be checked in index order.

   Either change needs the owner, because it alters a dispatched route or a ceiling. Even with both, at most P2, P3 and P4 could form: three pairs, the minimum for a classification.
