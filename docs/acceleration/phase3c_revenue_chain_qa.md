# Phase 3C: original annual revenue-chain QA

**Source feasibility RED; semantics PARTIAL.** No real signal formula was evaluated. Fixed denominator: All frozen candidates with three discovered original annual 10-Ks; includes parser/context failures, never successful-download-only. Candidate issuers30; three originals 29; three offline parses 27; exact concept in all three7; numeric comparability passes 6; accounting/perimeter-certified triples 0.

| Case | Originals / parsed | Exact concept in three | Outcome |
| --- | --- | --- | --- |
| 0000004962/AXP | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000021344/KO | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000027419/TGT | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000050863/INTC | 3 / 2 | False | UNAVAILABLE_OTHER_EXPLICIT_REASON |
| 0000051143/IBM | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000077476/PEP | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000078003/PFE | 3 / 3 | True | UNAVAILABLE_CONTEXT |
| 0000080424/PG | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000104169/WMT | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000200406/JNJ | 2 / 2 | False | UNAVAILABLE_MISSING_ORIGINAL |
| 0000310158/MRK | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000320187/NKE | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000320193/AAPL | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000354950/HD | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000731766/UNH | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000789019/MSFT | 3 / 3 | True | UNAVAILABLE_ACCOUNTING_BASIS |
| 0000796343/ADBE | 3 / 0 | False | UNAVAILABLE_OTHER_EXPLICIT_REASON |
| 0000804328/QCOM | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000829224/SBUX | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000858877/CSCO | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0000909832/COST | 3 / 3 | True | UNAVAILABLE_ACCOUNTING_BASIS |
| 0001018724/AMZN | 3 / 3 | True | UNAVAILABLE_ACCOUNTING_BASIS |
| 0001045810/NVDA | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0001067983/BRK.B | 3 / 3 | True | UNAVAILABLE_ACCOUNTING_BASIS |
| 0001108524/CRM | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0001141391/MA | 3 / 3 | True | UNAVAILABLE_ACCOUNTING_BASIS |
| 0001326801/FB | 3 / 3 | True | UNAVAILABLE_ACCOUNTING_BASIS |
| 0001341439/ORCL | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0001403161/V | 3 / 3 | False | UNAVAILABLE_CONCEPT |
| 0001652044/GOOGL | 3 / 3 | False | UNAVAILABLE_CONCEPT |

Original revenue facts use the exact US-GAAP concept `RevenueFromContractWithCustomerExcludingAssessedTax`, annual350–380day duration, same issuer, no explicit/typed dimensions, USD and positive finite values. Pinned EdgarTools5.62.0 enumerates original instance elements offline; concept/namespace/context/unit/value counts reconcile exactly. Primary Inline XBRL values independently reconcile format/sign/scale, with original locators/hashes retained privately. Non-inline primary-statement reconciliation, conflicting originals and unsupported rendering stay unavailable. No issuer extension, alternate revenue concept, segment sum or pro-forma repair is selected.

Three consecutive originals retain separate accession-specific values. Later comparatives only check prior pinned values through disclosed rounding intervals; they never overwrite earlier facts. Equal numbers alone do not certify reporting-perimeter/accounting-policy compatibility. Those material review certificates remain absent, so fully certified rate is a conservative lower bound. A parsing/primary-reconciliation limitation is reported as such rather than evidence that an original filing never existed. Source-stack scalability is **not established** under this exact contract; complete certification review is required before expanding acquisition.

Filing-year counts: `{"2018": 15, "2019": 29, "2020": 28, "2021": 13, "UNKN": 4}`. Taxonomies: http://fasb.org/us-gaap/2017-01-31, http://fasb.org/us-gaap/2018-01-31, http://fasb.org/us-gaap/2019-01-31, http://fasb.org/us-gaap/2020-01-31. Current retrieved bytes are historical reconstruction, not contemporaneous vintages. Original and derived hashes/configs are in canonical evidence and content-addressed private snapshots. Reproducing QA never fetches SEC.
