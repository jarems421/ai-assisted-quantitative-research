# EXP006: source missingness accepted; historical identity stop

**HISTORICAL_IDENTITY_BLOCKED. EXP006 remains absent and unfrozen.** Starting HEAD `65b04ab877cd6359748d4528de45a29bfc516fb6`. The [owner instruction](owner_item202_identity_2026-10-13.md) accepted explicit source missingness and authorized automatic identity closure. The unknown keys no longer block continuation, and no further source recovery is required by this decision. All three bounded identity routes were tested; none supplies the required dated class/provider/listing and 20-session lifecycle certificate. No route was selected or scaled.

## Source contract and correction

The [missingness contract](exp006_source_missingness_contract_v001.json) retains 108,532 known original Item 2.02 source keys, 108,364 legal-filer/accession pairs, 105,928 accessions and 6,189 legal-filer CIKs. These are source candidates, not independently aggregated trading events. Non-Item keys remain 318,749; amendments remain 11,944 version-only keys. The estimand is restricted to **source-resolved original Item 2.02 events** in the reconstructed daily/quarterly observation union, not every legally required filing or an untouched contemporaneous database.

All 113 unknown original keys / 107 accessions remain UNKNOWN_ITEM_STATUS and are excluded symmetrically from event and control pools. Years: 2015=9, 2016=21, 2017=10, 2018=8, 2019=3, 2020=62. Their key count is 0.1041% of known Item source keys; this is not a certified missing-trade rate. There are 88 legal filers in the unknown set, with at most 5 unknown keys per filer. Identity/lifecycle concentration remains unmeasured; no source recovery campaign was launched. The pre-performance sensitivity requirements remain mandatory if research advances.

The [aggregate correction](exp006_population_duplicate_correction_v001.json) fixes a prior software defect: absent-key defaultdict lookups enlarged both lookup maps during union traversal. Correct equivalent repeated observations are **111 daily and 0 quarterly**, replacing the historical reported -390 / -672. The 439,338 union keys, difference hashes, classifications and 113 unknowns are unchanged. Earlier reports and receipts retain their original bytes; their two duplicate aggregates are superseded by this separate correction. Regression tests now cover disjoint and partially overlapping populations.

## Identity feasibility

The [pushed source-only sample](exp006_identity_sample_v001.json) contains 240 confirmed-membership candidates, ten per year/quarter, across 230 legal filers. It includes 24 single-event issuers and 27 shared-accession source keys. Selection uses only source keys and filing-frequency/cofiler strata, with deterministic hash order; no prices, fame, current ticker or survival filter. Metadata membership remains subject to the earlier sampled primary semantic certificate. The sample was pushed before dispatch; [dated-symbol provider inputs](exp006_identity_provider_inputs_v001.json) were separately pushed before vendor queries.

| Route | Acquired evidence | Certification limit |
| --- | --- | --- |
| SEC primary | 240 original event covers plus 12 nearest-prior annual covers; 30 event Inline symbol points and 2 annual symbol points | Cover observations establish dated points, not complete effective listing spans, stable class/provider bridges or lifecycle paths. Missing Inline fields do not prove no historically listed equity. |
| SEC + OpenFIGI | 12 distinct dated-symbol queries; all candidate classes retained privately | Current identifiers do not date their validity. No first-match choice, issuer-to-class promotion or current-ticker substitution. |
| Configured provider metadata | 12 Tiingo metadata queries; zero prices; FMP unconfigured | Returned data-history start/end fields are not listing-effective boundaries or terminal consideration. No certified stable class span follows. |

Fully resolved sample events: **0/240 (0.0%)**, below the unchanged 95% standard. 240 are unresolved; 0 have certified ambiguous-resolution status. Multiple cover symbols (3) are a source-review warning, not a certified count of multiple eligible common classes. No sample row is dropped.

| Filed year | Sample candidates | Fully resolved | Coverage |
| --- | ---: | ---: | ---: |
| 2015 | 40 | 0 | 0.0% |
| 2016 | 40 | 0 | 0.0% |
| 2017 | 40 | 0 | 0.0% |
| 2018 | 40 | 0 | 0.0% |
| 2019 | 40 | 0 | 0.0% |
| 2020 | 40 | 0 | 0.0% |

The full source population has **0 certified event bindings / 108,532 retained source keys** because no route qualified for scaling. This is the certificate inventory, not an extrapolated failure probability from the sample or proof that every issuer is unresolvable. Per-issuer/per-year uncertified key accounting is archived privately for all 6,189 legal filers, with every original source key retained and bound to the unchanged population hash. The public certificate records year totals. Full-population multiple-class, renamed, ended and terminal-required counts remain UNKNOWN; their denominators were not certified. Complete terminal paths remain zero. A disappeared security is never disqualified by present survival or silently assigned zero value.

The local EXP002 discovery artifact overlaps 186 sample legal filers (279 rows). Its clipped spans, incomplete venue/type evidence and prior underfilled source universe were not independently recertified. It remains DISCOVERY_ONLY; its current canonical-symbol field was not used. No Nexus request occurred.

## Verification and stop

Source starts: SEC 252, OpenFIGI 12, Tiingo 12; retries 0. Original bodies, full vendor payloads and redacted-contact receipts remain immutable and ignored. HTTP outcomes: {"200": 275, "404": 1}. One worker enforces SEC spacing and exact routes, conservative OpenFIGI pacing, and persisted Tiingo request quotas. Current metadata retrieval is historical reconstruction, not pre-event information. No purchase/upgrade; account-wide usage is UNKNOWN.

Validation: 408 local tests; 180 public tests; 0 skipped. [Receipt](exp006_identity_validation.json). Public report regeneration uses tracked receipts only; audit reads ignored archived evidence and makes no network requests.

```sh
python -m src.research.item202_identity_report --check
python -m src.research.item202_identity_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

The passed v003 date policy, earlier classification/source receipts, all frozen experiments and prior processed results remain unchanged. EXP004 stays paused; EXP005 abandoned/absent; EXP006 absent. Market price certification, matching, inference/calibration/power, Proof, freeze and Development did not run after the identity gate failed. Performance evaluations and confirmation accesses are **0**; the 12-evaluation ceiling is unchanged. No Aurora, Nexus, optimizer, paper/live action or new phase occurred.

**Stopped under owner section 15 at HISTORICAL_IDENTITY_BLOCKED.** The concrete missing capability is independently dated common-class/listing/provider spans with lifecycle support. No additional planning approval was requested and no downstream gate was weakened to manufacture a freeze.
