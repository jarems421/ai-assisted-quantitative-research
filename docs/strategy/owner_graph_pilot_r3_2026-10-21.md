# ACTIVE owner authorisation: graph pilot revision 3 (exploratory amended attempt)

**Status: ACTIVE from the commit that adds this file.** The authority is the owner's [final bounded amendment](owner_graph_pilot_r3_amendment_2026-10-21.md): *"I choose Option 3: amend P2 and P3, then attempt the P2/P3/P4 pilot."*

**Exploratory, not a pristine revision 2.** This protocol was amended **after** the source-formation failures in the [revision 2 freeze report](graph_pilot_packet_freeze_report.md) had been reviewed. Revision 2's activated attempt ([authority](owner_graph_pilot_2026-10-21.md), [receipt](graph_pilot_receipt.json), private `data/raw/graph_pilot_20261021/final_stop.json`) stays exactly as recorded: four requests, no campaigns, stopped. Revision 3 has its own records under `docs/strategy/graph_pilot_r3/` and its own private archive, `data/raw/graph_pilot_r3_20261021/`.

**What carries over unchanged** from the [pre-registration](graph_pilot_preregistration.md) and the revision 2 authority, except for the routes below:
- design and arm order: P2 G then S; P3 S then G; P4 G then S;
- snapshot isolation and branch separation (now `graph-pilot-r3/<packet>-<arm>`);
- time controls and logging;
- partial blinding and human-only adjudication, M/H reviews and dispositions;
- outcomes and descriptive decision rules;
- all source stops and prohibitions.

P1 is not restarted, and P4 alone is not authorised.

## 1. Ceilings (cumulative, including revision 2's spend)

| Unit | Minutes | Starts | Searches | Bytes |
|---|---:|---:|---:|---:|
| P2 packet freeze (cumulative) | 60 | 17 (3 used; **14 new**) | 0 | 24 MiB (1,343,500 used) |
| P3 packet freeze (cumulative) | 30 | 3 (1 used; **1 new authorised**) | 0 | 8 MiB (4,194,304 used) |
| P4 packet freeze | 30 | 0 | 0 | 0 |
| Each arm campaign (×6 at most) | 120 | 6 | 10 | 8 MiB |
| **Whole pilot (cumulative)** | **18 h** | **60** (4 used) | **92** | **88 MiB** (5,537,804 used) |

At most this totals 55 starts, about 80 MiB, 60 searches and 14 hours, so every campaign keeps equal and complete S and G budgets. The 4 MiB per-response stop is unchanged. No time transfers between arms.

## 2. P3: one authorised second request (frozen)

`https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50`

**Conditions:**
- **Access:** keyless. The request is made once, through `fetch_one.py`, into `data/raw/graph_pilot_r3_20261021/P3/prep`, with `--max-starts 1 --max-bytes 4194304` (the remaining P3 bytes).
- **Eligibility:** only a complete original response is accepted; E1–E8 are judged on it.
- **Selection:** the first five qualifying records by `report_date`, then `recall_number`. They are the first rows of a bounded response, **not** a complete population of the window.
- **Entity:** `recalling_firm` is a name-only identity.
- **Clocks:** `report_date` (report issued), `recall_initiation_date` (event), first-public time (UNKNOWN unless proven) and retrieval time stay distinct.
- **Failure:** if it fails, **P3 is `NOT_FORMED`**, with no further repair.

## 3. P2: fixed extension (frozen before dispatch)

The SEC index files already acquired are reused without refetching: `index.json` (`607e179d…58a2`) and `form.20250701.idx` (`bdf95bb0…771d`), both hash-verified. Their deterministic order is: 8-K rows dated 2025-07-01, sorted by date filed then accession number, with co-filed duplicate accessions keeping the index's first row. The previously inspected `0000004962-25-000073` is excluded. The next **14 distinct accessions**, which are the only filings that may be inspected, are:

| Order | Accession | CIK | Company (as indexed) | Complete submission |
|---:|---|---|---|---|
| 2 | `0000016918-25-000074` | 16918 | CONSTELLATION BRANDS, INC. | `https://www.sec.gov/Archives/edgar/data/16918/0000016918-25-000074.txt` |
| 3 | `0000019617-25-000509` | 19617 | JPMORGAN CHASE & CO | `https://www.sec.gov/Archives/edgar/data/19617/0000019617-25-000509.txt` |
| 4 | `0000019617-25-000510` | 19617 | JPMORGAN CHASE & CO | `https://www.sec.gov/Archives/edgar/data/19617/0000019617-25-000510.txt` |
| 5 | `0000027879-25-000008` | 27879 | DELMARVA POWER & LIGHT CO /DE/ | `https://www.sec.gov/Archives/edgar/data/27879/0000027879-25-000008.txt` |
| 6 | `0000037996-25-000139` | 37996 | FORD MOTOR CO | `https://www.sec.gov/Archives/edgar/data/37996/0000037996-25-000139.txt` |
| 7 | `0000043920-25-000038` | 43920 | GREIF, INC | `https://www.sec.gov/Archives/edgar/data/43920/0000043920-25-000038.txt` |
| 8 | `0000046195-25-000016` | 46195 | BANK OF HAWAII CORP | `https://www.sec.gov/Archives/edgar/data/46195/0000046195-25-000016.txt` |
| 9 | `0000065984-25-000074` | 65984 | ENTERGY CORP /DE/ | `https://www.sec.gov/Archives/edgar/data/65984/0000065984-25-000074.txt` |
| 10 | `0000070858-25-000249` | 70858 | BANK OF AMERICA CORP /DE/ | `https://www.sec.gov/Archives/edgar/data/70858/0000070858-25-000249.txt` |
| 11 | `0000081061-25-000027` | 81061 | PUBLIX SUPER MARKETS INC | `https://www.sec.gov/Archives/edgar/data/81061/0000081061-25-000027.txt` |
| 12 | `0000085535-25-000092` | 85535 | ROYAL GOLD INC | `https://www.sec.gov/Archives/edgar/data/85535/0000085535-25-000092.txt` |
| 13 | `0000088053-25-000530` | 791718 | EUROPEAN EQUITY FUND, INC / MD | `https://www.sec.gov/Archives/edgar/data/791718/0000088053-25-000530.txt` |
| 14 | `0000092122-25-000066` | 41091 | GEORGIA POWER CO | `https://www.sec.gov/Archives/edgar/data/41091/0000092122-25-000066.txt` |
| 15 | `0000320335-25-000038` | 320335 | GLOBE LIFE INC. | `https://www.sec.gov/Archives/edgar/data/320335/0000320335-25-000038.txt` |

**Procedure:**
- **Fetching:** each filing is one `fetch_one.py` request into `data/raw/graph_pilot_r3_20261021/P2/prep`, with `--max-starts 14`, `--max-bytes 23822324` (24 MiB less 1,343,500) and the configured SEC identity.
- **Order and stopping:** filings are fetched in the order above. Fetching stops once five filings qualify, or when the list, the starts, the bytes or the 60 minutes run out.
- **Qualifying:** a filing qualifies only if its original submission contains either:
  - an `EX-10` agreement that identifies parties and a relationship; or
  - an 8-K **Item 1.01** disclosure that itself explicitly documents identifiable parties and the contractual relationship.
- **What does not qualify:** an index row, press release, issuer name, narrative guess or generic reference to an agreement.
- **What is recorded:** exactly what each filing supports, with missing counterparties, terms, quantities, allocations and exposure stated as missing.
- **Packet:** the first five qualifying filings in this order (at least three are required). **If fewer than three qualify, P2 is `NOT_FORMED`.**

## 4. P4: unchanged

The packet is the previously frozen primary mechanism, verbatim in the [revision 2 authority](owner_graph_pilot_2026-10-21.md). It uses no source request and no reformulation.

## 5. Execution

1. **Packets:** each packet that forms gets a packet ledger, a private bundle and a snapshot (`graph pilot snapshot`), committed before either arm starts.
2. **Arms:** arms run as fresh isolated agent sessions in their own worktrees, using the fixed [revision 3 arm instructions](graph_pilot/arm_instructions_r3.md) (SHA-256 `9d3ca76833c501c0b52a8d1b4065c5974b6ec2e13532ea0a1267e89b964eb8bc`). Requests go through [`fetch_one.py`](graph_pilot/fetch_one.py) (SHA-256 `3e51a00081b5db3ea4c702b0bbfd6117e1339ff70df0d1801aa54c35a958eb1a`).
3. **Owner decisions:** after both arms of a packet finish, the blinded export goes to the owner for adjudication. M/H reviews and dispositions are the owner's.
4. **Classification:** fewer than three completed valid pairs gets **no definitive graph-increment classification**.
5. **No further changes:** no more route changes, budget expansion or replacement packets.
