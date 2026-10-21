# Packet P3: blinded adjudication sheet (GRAPH_PILOT_BLIND_V2_ALIASED)

17 items, shuffled. Arm, operator, attribution, decision, minutes and notes are hidden; record ids of the current campaign are per-item aliases.

For each item record **outcome** (`CONFIRMED_AGAINST_ORIGINALS` with the evidence hashes or locators you checked, `PLAUSIBLE_UNVERIFIED`, `REJECTED_FALSE`, `REJECTED_TRIVIAL`) and **economic meaning** (`MEANINGFUL`, `NOT_MEANINGFUL`, `UNCLEAR`).

## 1. `ADJ-793909d493` (CONNECTION)

- **From:** historical_claim `HISTORICAL_MEMORY/HIST-SH09/claim-v1`
  - Text: Change in Chevron recoverable-net predecessor cleanup exposure before 2024-01-02
  - Entities: `CIK:0000093410` (Chevron Corporation); `NAME:W&T Offshore` (W&T Offshore); `NAME:Cox estate leases` (Cox-estate leases with outstanding obligations)
  - Evidence: `https://www.wtoffshore.com/investors/sec-filings/all-sec-filings/content/0001104659-23-126389/0001104659-23-126389.pdf` depth RECEIPT_HTTP_200, sha256 `1d468393d22cfafe99b67b1432a38bcfc0630b85e4e76620a8e9ff5285451651`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/93410/000009341024000002/cvx-20240102.htm` depth RECEIPT_HTTP_200, sha256 `4c5d6244c33ac20637cfd6b4e6ce4f939bb0ce6f13281f963d8005ba80195766`
  - Evidence: `https://chevroncorp.gcs-web.com/static-files/51fe92ca-3680-42a4-b804-2c9433cfe667` depth RECEIPT_HTTP_403, sha256 `f70acef4d8bb6b5b9c67c042676f0cd5217face3fc2630b0ff877665e86dd36f`
  - Evidence: `https://www.courtlistener.com/?q=%22MLCJR%22&type=r&order_by=dateFiled%20asc` depth RECEIPT_HTTP_403, sha256 `dc6f503969324d8da3b8204988ce06ab0be870d8fad8c777fc731daa71fd37c0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A31ac7246`
  - Text: Outcome check for CAND-A6e8d73de: the quarterly reports for the periods ended 2025-06-30 and 2025-09-30 contain no text on the Extended Tip or MicroMyst applicators, endotoxin, sterility or the 2025 recall events (text searched for "recall", "applicator", "MicroMyst", "endotoxin", "steril"). Their only recall-named special charge is "Boston recall / Braintree transition" (an earlier recall of Boston-facility products): $13,630 thousand and $13,957 thousand for the two quarters. CSS revenue was $304.0 million (Q2, change attributed to combined "quality and operational issues") and $292.6 million (Q3). No amount is attributed to the 2025 applicator recalls. Decides the frozen outcome: the registrant reports no recall-specific amount for these applicators, only combined quality and operational effects. Product revenue of the recalled applicators Any recall cost recorded within combined quality charges
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation)
  - value: NO_AMOUNT_ATTRIBUTED_TO_THE_APPLICATOR_RECALLS
  - units: USD thousands (no attributed amount)
  - occurred: 2025-09-30
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 2. `ADJ-e977207739` (CONNECTION)

- **From:** historical_claim `HISTORICAL_MEMORY/HIST-F01/claim-v1`
  - Text: Cross-owner treatment-resource dependence and available treatment capacity
  - Entities: `BW_LOCALITY:10029` (Tuholmane Ø); `BW_LOCALITY:10212` (Bogen); `BW_LOCALITY:10041` (Kviksholmen); `BW_LOCALITY:10213` (Naustneset); `MMSI:257210000` (ROSTEIN (wellboat)); `MMSI:257262000` (RONJA SUND (wellboat))
  - Evidence: `https://www.barentswatch.no/bwapi/v1/geodata/fishhealth/locality/10029/vessel/2021/10` depth RECEIPT_HTTP_200, sha256 `fce8a379fa8dd198407483bb512df417dc95b5d236c4ba62012559f596a40d4b`
  - Evidence: `https://www.barentswatch.no/bwapi/v1/geodata/fishhealth/locality/10213/vessel/2024/10` depth RECEIPT_HTTP_200, sha256 `253a49d06ceeb3b5e7a8984d16d18e70699c24f2bbfe98efe0c4716598ee25f1`
  - Evidence: `https://www.barentswatch.no/bwapi/v1/geodata/fishhealth/vesseltrack/257210000/2021/10` depth RECEIPT_HTTP_200, sha256 `d01c12155bfe1fd903110e81067307cc85259d82e400775ee921d17d41ab3660`
  - Evidence: `https://www.barentswatch.no/bwapi/openapi/fishhealth/openapi.json` depth RECEIPT_HTTP_200, sha256 `4b95578a944443798f2afcb8214d10069b6b931cc733c85646716afdac1cf675`
- **To:** relationship `CURRENT_ARM_CAMPAIGN/REL-A76e5d8c6`
  - Text: possible identity: the recalling firm named in the FDA records may be the listed subsidiary
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences), Princeton NJ); `NAME:Integra LifeSciences Corporation` (Integra LifeSciences Corporation (Delaware))
  - type: OTHER
  - period: {'end': '2025-07-02', 'start': '2025-05-22'}
  - basis: NAME_MATCH_ONLY
  - status: UNVERIFIED
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000017/iart-20241231xexx211.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `2ab0313fd6d420f3e3aec900880500304d1635c119bcde666b526f85badc3d97`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 3. `ADJ-e14ea60127` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-Acdd1c21d`
  - Text: Quarterly report for the period ended 2025-03-31 (filed before the recalls' initiation dates): Neurosurgery revenue $190,912 thousand (prior-year quarter $202,268 thousand); Codman Specialty Surgical segment $280,664 thousand; total revenue $382,653 thousand. Neurosurgery excluding the acquisition declined low single digits, driven by Dural Access and Repair, Advanced Energy and Neuro Monitoring. Special charges include "Boston recall / Braintree transition" $14,810 thousand. Pre-event scale of the revenue line the recalled applicators may belong to; shows the registrant itemises recall-related special charges. Which revenue line includes the Extended Tip and MicroMyst applicators Product-level revenue of the recalled items EDGAR acceptance time
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation)
  - value: 190912
  - units: USD thousands (net revenue, Neurosurgery revenue line)
  - occurred: 2025-03-31
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A482566d4`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 4. `ADJ-d4a210e351` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A46ebbed8`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** relationship `CURRENT_ARM_CAMPAIGN/REL-A25b86b20`
  - Text: source owns target (subsidiary listed in the parent's Exhibit 21.1)
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation); `NAME:Integra LifeSciences Corporation` (Integra LifeSciences Corporation (Delaware))
  - type: OWNERSHIP
  - period: {'end': '2024-12-31', 'start': 'UNKNOWN'}
  - basis: DOCUMENTED
  - status: UNVERIFIED
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000017/iart-20241231xexx211.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `2ab0313fd6d420f3e3aec900880500304d1635c119bcde666b526f85badc3d97`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none; relationship period covers observation: UNRESOLVED

## 5. `ADJ-84e34126a1` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A9307dc0f`
  - Text: Pre-event disclosure (period ended 2025-03-31): on December 19, 2024 a subsidiary of the registrant received an FDA warning letter on quality system issues at facilities in Mansfield MA, Plainsboro NJ and Princeton NJ; the company had initiated shipping holds for several products and a voluntary recall of disposable patties and strips. Revenue declines were attributed to quality and operational issues. Quality-system problems at a Princeton facility were disclosed before the 2025 applicator recalls; a later recall may restate known risk rather than add information. Manufacturing site of the recalled applicators Name of the subsidiary that received the warning letter
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation)
  - value: FDA warning letter received 2024-12-19 (quality system issues, three facilities including Princeton NJ)
  - units: regulatory action (category)
  - occurred: 2024-12-19
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-Aaca04313`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 6. `ADJ-6fcb2b50a4` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A93430d37`
  - Text: FDA device enforcement record Z-1961-2025 (event 96965): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: MicroMyst Applicator, Box of 5. Consisting of a multilumen applicator and filtered line for use with the Integra Flow Source for the controlled application of two liquids. Reason: Lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-23
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A1663e332`
  - Text: The Form 10-Q for the quarter ended 2025-06-30 (accession 0000917520-25-000074) contains no mention of the recalled applicators, the MicroMyst applicator, endotoxins or sterility assurance, and no recall-specific amount for them. Its recall references concern the 2024 patties-and-strips recall and the 2023 Boston-facility recall; the special-charge line "Boston recall / Braintree transition" was $13.630 million for the quarter. Total revenue was $415.605 million and Codman Specialty Surgical revenue $303.958 million; revenue changes are attributed to unquantified "quality and operational issues". Dural sealant products are stated to be sourced mostly from third-party vendors. The frozen outcome route for CAND-Afee388f7: the issuer report for the quarter containing recall initiation. EDGAR acceptance record (first-public time) not retrieved Product-line revenue for the recalled applicators
  - Entities: `SEC_CIK:917520` (Integra LifeSciences Holdings Corporation)
  - value: no recall-specific amount or mention for these applicators
  - units: USD thousands (revenue and charges); presence or absence of disclosure
  - occurred: 2025-06-30
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 7. `ADJ-db8b15dde2` (CONNECTION)

- **From:** relationship `CURRENT_ARM_CAMPAIGN/REL-Ad636d8a4`
  - Text: source owns target (subsidiary listed in the parent's Exhibit 21.1)
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation); `NAME:Integra LifeSciences Corporation` (Integra LifeSciences Corporation (Delaware))
  - type: OWNERSHIP
  - period: {'end': '2024-12-31', 'start': 'UNKNOWN'}
  - basis: DOCUMENTED
  - status: UNVERIFIED
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000017/iart-20241231xexx211.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `2ab0313fd6d420f3e3aec900880500304d1635c119bcde666b526f85badc3d97`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A15b26376`
  - Text: Quarterly report for the period ended 2025-03-31 (filed before the recalls' initiation dates): Neurosurgery revenue $190,912 thousand (prior-year quarter $202,268 thousand); Codman Specialty Surgical segment $280,664 thousand; total revenue $382,653 thousand. Neurosurgery excluding the acquisition declined low single digits, driven by Dural Access and Repair, Advanced Energy and Neuro Monitoring. Special charges include "Boston recall / Braintree transition" $14,810 thousand. Pre-event scale of the revenue line the recalled applicators may belong to; shows the registrant itemises recall-related special charges. Which revenue line includes the Extended Tip and MicroMyst applicators Product-level revenue of the recalled items EDGAR acceptance time
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation)
  - value: 190912
  - units: USD thousands (net revenue, Neurosurgery revenue line)
  - occurred: 2025-03-31
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
- **Mechanical shared structure:** same identified entity ['CIK:0000917520']; shared document hashes 0; shared requirement tags none; relationship period covers observation: UNRESOLVED

## 8. `ADJ-6b5b79c2d6` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A0309968f`
  - Text: The GUDID record for primary device identifier 10381780000143 (Extended Tip Applicator, catalog 205108, the identifier printed in recall Z-1958-2025) names labeler "Integra Lifesciences Corporation", DUNS 083171244; package identifier 30381780000147 is a BOX containing 5 of that device. Joins the recalled product to a labeler legal entity through an exact device identifier and supplies a DUNS identifier; shows the recalled SKU is a box of 5 devices, so the recall unit count is ambiguous between boxes and devices. GUDID records for the other recalled identifiers (10381780000150, 10381780000167, 10381780000112) were not retrieved Whether recall product_quantity counts boxes or devices Any identifier joining DUNS 083171244 to an SEC filer
  - Entities: `DUNS:083171244` (Integra Lifesciences Corporation)
  - value: labeler DUNS 083171244; 5 devices per box
  - units: identifier; devices per package
  - occurred: UNKNOWN
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://accessgudid.nlm.nih.gov/api/v3/devices/lookup.json?di=10381780000143` depth VERIFIED_ORIGINAL_FIELD, sha256 `d6ad2dde4a3e98ee9d760174dc390fad39376312e101f2c61106cc3d6681004a`
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A0a0af697`
  - Text: Exhibit 21.1 to the FY2024 Form 10-K of Integra LifeSciences Holdings Corporation (accession 0000917520-25-000017) lists "Integra LifeSciences Corporation" (Delaware) among its subsidiaries. The exhibit gives no ownership share, address or identifier. Documents that a subsidiary bearing the labeler name belongs to the listed parent. Ownership share and date coverage of the subsidiary relationship in May 2025 Identifier shared between the subsidiary and the GUDID DUNS or FDA recalling firm
  - Entities: `SEC_CIK:917520` (Integra LifeSciences Holdings Corporation)
  - value: listed as subsidiary
  - units: category
  - occurred: UNKNOWN
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000017/iart-20241231xexx211.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `2ab0313fd6d420f3e3aec900880500304d1635c119bcde666b526f85badc3d97`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 9. `ADJ-dc62481aff` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A10ffdce7`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-Adce6cd3e`
  - Text: The Form 10-Q for the quarter ended 2025-06-30 (accession 0000917520-25-000074) contains no mention of the recalled applicators, the MicroMyst applicator, endotoxins or sterility assurance, and no recall-specific amount for them. Its recall references concern the 2024 patties-and-strips recall and the 2023 Boston-facility recall; the special-charge line "Boston recall / Braintree transition" was $13.630 million for the quarter. Total revenue was $415.605 million and Codman Specialty Surgical revenue $303.958 million; revenue changes are attributed to unquantified "quality and operational issues". Dural sealant products are stated to be sourced mostly from third-party vendors. The frozen outcome route for CAND-Ab3d29651: the issuer report for the quarter containing recall initiation. EDGAR acceptance record (first-public time) not retrieved Product-line revenue for the recalled applicators
  - Entities: `SEC_CIK:917520` (Integra LifeSciences Holdings Corporation)
  - value: no recall-specific amount or mention for these applicators
  - units: USD thousands (revenue and charges); presence or absence of disclosure
  - occurred: 2025-06-30
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 10. `ADJ-87143e90ad` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A08cc6827`
  - Text: The GUDID record for primary device identifier 10381780000143 (Extended Tip Applicator, catalog 205108, the identifier printed in recall Z-1958-2025) names labeler "Integra Lifesciences Corporation", DUNS 083171244; package identifier 30381780000147 is a BOX containing 5 of that device. Joins the recalled product to a labeler legal entity through an exact device identifier and supplies a DUNS identifier; shows the recalled SKU is a box of 5 devices, so the recall unit count is ambiguous between boxes and devices. GUDID records for the other recalled identifiers (10381780000150, 10381780000167, 10381780000112) were not retrieved Whether recall product_quantity counts boxes or devices Any identifier joining DUNS 083171244 to an SEC filer
  - Entities: `DUNS:083171244` (Integra Lifesciences Corporation)
  - value: labeler DUNS 083171244; 5 devices per box
  - units: identifier; devices per package
  - occurred: UNKNOWN
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://accessgudid.nlm.nih.gov/api/v3/devices/lookup.json?di=10381780000143` depth VERIFIED_ORIGINAL_FIELD, sha256 `d6ad2dde4a3e98ee9d760174dc390fad39376312e101f2c61106cc3d6681004a`
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `FROZEN_PACKET/OBS-P-1`
  - Text: FDA device enforcement record Z-1904-2025 (event 96891): Class I recall by SunMed Holdings, LLC, status Ongoing. Product: Broselow Pediatric Emergency Rainbow Tape (distribution by AirLife); REF 7700REA AirLife brand, 2025 Edition, and 36-23446 Rev 2 Print Version The Broselow Tape is a length- and weight-based reference tool specifically designed for pediatric emergency care. Reason: The impacted tape was manufactured with incorrect information on the tape. Incorrect values are printed in the Red zone, Orange zone, and Grey zone. Using the incorrect values in the Red zone could lead to shocking a patient with an excessive dose of joules, causing significant harm including burns, heart damage, and cardiac arrest. Incorrect values in the Orange zone could lead to overdosing the  A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:SunMed Holdings, LLC` (SunMed Holdings, LLC)
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-15
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **Mechanical shared structure:** same identified entity none; shared document hashes 1; shared requirement tags none

## 11. `ADJ-ea7badfe21` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A0a88b94c`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A878d892a`
  - Text: The GUDID record for primary device identifier 10381780000143 (Extended Tip Applicator, catalog 205108, the identifier printed in recall Z-1958-2025) names labeler "Integra Lifesciences Corporation", DUNS 083171244; package identifier 30381780000147 is a BOX containing 5 of that device. Joins the recalled product to a labeler legal entity through an exact device identifier and supplies a DUNS identifier; shows the recalled SKU is a box of 5 devices, so the recall unit count is ambiguous between boxes and devices. GUDID records for the other recalled identifiers (10381780000150, 10381780000167, 10381780000112) were not retrieved Whether recall product_quantity counts boxes or devices Any identifier joining DUNS 083171244 to an SEC filer
  - Entities: `DUNS:083171244` (Integra Lifesciences Corporation)
  - value: labeler DUNS 083171244; 5 devices per box
  - units: identifier; devices per package
  - occurred: UNKNOWN
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://accessgudid.nlm.nih.gov/api/v3/devices/lookup.json?di=10381780000143` depth VERIFIED_ORIGINAL_FIELD, sha256 `d6ad2dde4a3e98ee9d760174dc390fad39376312e101f2c61106cc3d6681004a`
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **Mechanical shared structure:** same identified entity none; shared document hashes 1; shared requirement tags none

## 12. `ADJ-ef9beef356` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A6210d639`
  - Text: FDA device enforcement record Z-1961-2025 (event 96965): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: MicroMyst Applicator, Box of 5. Consisting of a multilumen applicator and filtered line for use with the Integra Flow Source for the controlled application of two liquids. Reason: Lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-23
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A23cc7793`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **Mechanical shared structure:** same identified entity none; shared document hashes 1; shared requirement tags none

## 13. `ADJ-7b96650ced` (CONNECTION)

- **From:** historical_claim `HISTORICAL_MEMORY/HIST-EF06/claim-v1`
  - Text: Per-carrier/cohort accepted and retained premium after cancellations and reinsurance
  - Entities: `CIK:0001400810` (HCI Group); `NAME:Homeowners Choice` (Homeowners Choice (carrier)); `NAME:TypTap` (TypTap (carrier))
  - Evidence: `https://www.sec.gov/Archives/edgar/data/1400810/000095017024028021/hci-ex99_1.htm` depth RECEIPT_HTTP_200, sha256 `f68089cd7e28c90911213dc2a9d8de071fa0555d268273bf7c91508dc9c36748`
  - Evidence: `https://www.citizensfla.com/documents/20702/29465645/2023+Stats.pdf/29ae7065-eb6e-28b8-5841-21e1dbba3049?t=1704899022388` depth RECEIPT_HTTP_200, sha256 `fc39950acee670d29b0e246d19c4a1b5f7ca1347c6a9c4703b946a1103375c51`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/1400810/000095017024028620/hci-20231231.htm` depth RECEIPT_HTTP_200, sha256 `0310d3f0cab53c34b16ae83aa065c78ba91bcb551bc003865ebd0d08653a5840`
- **To:** candidate `CURRENT_ARM_CAMPAIGN/CAND-A63b95f2d`
  - Text: A Class I recall for endotoxin and sterility-assurance failures removes the applicators from sale and incurs replacement, write-off and remediation costs. If material, the registrant attributes a revenue reduction or an itemised charge to this recall in its quarterly report covering the initiation dates (period ended 2025-06-30) or the following quarter (period ended 2025-09-30). Class I recall classification of Extended Tip and MicroMyst applicators, with reported product_quantity 6,216 units, 2,524 units, 212 units and 4,882 units (as reported; not summed, unit meaning per box or per device unverified) [REQ:REQ_ENTITY_COHORT_JOIN] identifier-level identity of the recalling firm and the revenue line containing the applicators [REQ:REQ_DOCUMENTED_ALLOCATION] a recall-specific amount rather than a combined quality or remediation charge First-public time of the 2025-07-02 enforcement report Product revenue of the recalled applicators
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation)
  - outcome: Revenue reduction or charge that the registrant explicitly attributes to the recall of these applicators (Extended Tip, MicroMyst, or the recall event they belong to) in its quarterly reports for periods ended 2025-06-30 and 2025-09-30
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000041/iart-20250331.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `50ac4fe375df7ad26f8806f71ff78dd6f3d19c833583e35dba0dd50e5fe31ae7`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags ['REQ_DOCUMENTED_ALLOCATION']

## 14. `ADJ-dffcf49273` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-A5cc18af6`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-Ae6e1befc`
  - Text: The Form 10-Q for the quarter ended 2025-09-30 (accession 0000917520-25-000096) contains no mention of the recalled applicators, MicroMyst, endotoxins or sterility assurance, and no recall-specific amount for them. Its recall references concern the earlier patties-and-strips and Boston recalls; the "Boston recall / Braintree transition" special charge was $13.957 million for the quarter. Total revenue was $402.1 million and Codman Specialty Surgical revenue $292.6 million. The second frozen outcome route for CAND-A693c5cda: the issuer report for the quarter containing the FDA report date. EDGAR acceptance record (first-public time) not retrieved
  - Entities: `SEC_CIK:917520` (Integra LifeSciences Holdings Corporation)
  - value: no recall-specific amount or mention for these applicators
  - units: USD (revenue and charges); presence or absence of disclosure
  - occurred: 2025-09-30
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 15. `ADJ-ab3ea60347` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-Aafc6e24b`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A4c38dd2d`
  - Text: FDA device enforcement record Z-1959-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 15 CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **Mechanical shared structure:** same identified entity none; shared document hashes 1; shared requirement tags none

## 16. `ADJ-c487a29a99` (CONNECTION)

- **From:** observation `CURRENT_ARM_CAMPAIGN/OBS-Abddaf20b`
  - Text: FDA device enforcement record Z-1958-2025 (event 96934): Class I recall by Integra LifeSciences Corp. (NeuroSciences), status Ongoing. Product: Extended Tip Applicator, 8CM, Box of 5. Reason: Devices contain potentially out-of-specification levels of endotoxins and lack of sterility assurance. A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:Integra LifeSciences Corp. (NeuroSciences)` (Integra LifeSciences Corp. (NeuroSciences))
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-22
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-Ab5359929`
  - Text: Outcome check for CAND-A6b25b72b: the quarterly reports for the periods ended 2025-06-30 and 2025-09-30 contain no text on the Extended Tip or MicroMyst applicators, endotoxin, sterility or the 2025 recall events (text searched for "recall", "applicator", "MicroMyst", "endotoxin", "steril"). Their only recall-named special charge is "Boston recall / Braintree transition" (an earlier recall of Boston-facility products): $13,630 thousand and $13,957 thousand for the two quarters. CSS revenue was $304.0 million (Q2, change attributed to combined "quality and operational issues") and $292.6 million (Q3). No amount is attributed to the 2025 applicator recalls. Decides the frozen outcome: the registrant reports no recall-specific amount for these applicators, only combined quality and operational effects. Product revenue of the recalled applicators Any recall cost recorded within combined quality charges
  - Entities: `CIK:0000917520` (Integra LifeSciences Holdings Corporation)
  - value: NO_AMOUNT_ATTRIBUTED_TO_THE_APPLICATOR_RECALLS
  - units: USD thousands (no attributed amount)
  - occurred: 2025-09-30
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000074/iart-20250630.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `f272c710f040d62eff9e2bec3fce050ac9ba295863f34687d96ad6a3a0b5992f`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
  - Evidence: `https://www.sec.gov/Archives/edgar/data/917520/000091752025000096/iart-20250930.htm` depth VERIFIED_ORIGINAL_FIELD, sha256 `859cb91bb8b06a22e5a08649a2f4cdb4fe889e136700fa2eafa89201a16e7751`
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

## 17. `ADJ-b30a491381` (CONNECTION)

- **From:** observation `FROZEN_PACKET/OBS-P-1`
  - Text: FDA device enforcement record Z-1904-2025 (event 96891): Class I recall by SunMed Holdings, LLC, status Ongoing. Product: Broselow Pediatric Emergency Rainbow Tape (distribution by AirLife); REF 7700REA AirLife brand, 2025 Edition, and 36-23446 Rev 2 Print Version The Broselow Tape is a length- and weight-based reference tool specifically designed for pediatric emergency care. Reason: The impacted tape was manufactured with incorrect information on the tape. Incorrect values are printed in the Red zone, Orange zone, and Grey zone. Using the incorrect values in the Red zone could lead to shocking a patient with an excessive dose of joules, causing significant harm including burns, heart damage, and cardiac arrest. Incorrect values in the Orange zone could lead to overdosing the  A dated FDA recall classification (report date 2025-07-02) for an identified product; the recalling firm is named only. First-public time of the enforcement report (only the current API version was retrieved) Registry identity of the recalling firm, its parent and any listed-company link Quantities affected and any financial consequence
  - Entities: `NAME:SunMed Holdings, LLC` (SunMed Holdings, LLC)
  - value: Class I
  - units: FDA recall class
  - occurred: 2025-05-15
  - depth: VERIFIED_ORIGINAL_FIELD
  - Evidence: `https://api.fda.gov/device/enforcement.json?search=report_date:[2025-07-01+TO+2025-09-30]&sort=report_date:asc&limit=50` depth VERIFIED_ORIGINAL_FIELD, sha256 `99e8d37983e6d2de368aa6fc75d970d499da2f4ae726e3f3f2678f4b9d9853d0`
- **To:** observation `CURRENT_ARM_CAMPAIGN/OBS-A1e8c3de3`
  - Text: A search index lists a quarterly report (period ended 2025-06-30) of SLR Investment Corp. (archive-path CIK 1418076) as describing a first-lien loan to a borrower named "SunMed Group Holdings, LLC". The original was not retrieved. The index summary also displayed post-event fair values for the loan, so any loan-value outcome for this borrower was seen before any claim could be frozen. Possible route from the packet's SunMed recall record (OBS-P-1) to listed lenders; retained to avoid repeating a contaminated outcome check. Original schedule of investments row Identity between the borrower and the recalling firm A pre-event, outcome-blind formation of any claim
  - Entities: `NAME:SunMed Group Holdings, LLC` (SunMed Group Holdings, LLC)
  - value: UNKNOWN
  - units: UNKNOWN
  - occurred: UNKNOWN
  - depth: INDEXED_DESCRIPTION_ONLY
  - Evidence: `https://www.sec.gov/Archives/edgar/data/1418076/000095017025103004/ck0001418076-20250630.htm` depth INDEXED_DESCRIPTION_ONLY
- **Mechanical shared structure:** same identified entity none; shared document hashes 0; shared requirement tags none

