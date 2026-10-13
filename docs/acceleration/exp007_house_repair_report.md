# EXP007 final House-only original-source repair

**ABANDON_EXP007_SOURCE_FEASIBILITY. House source gate fails; economic hypothesis untested.** Starting HEAD `7451373705b09f152107a88af69aec4ee2199cf5`, as of 2026-10-13. [Owner instruction](owner_exp007_house_repair_2026-10-13.md) authorized one final pre-performance House-only revision, with mandatory abandonment if the frozen source criteria failed. No experiment was registered or frozen.

## Fixed source revision and bounded repair

[Design v002](exp007_design_candidate_v002.json) restricts the estimand to source-resolved House common-equity purchase disclosures versus SPY over 20 sessions. This source-access revision precedes all market outcomes; it does not select members, parties, amounts, sectors or returns. The earlier [House/Senate report](exp007_source_validation_report.md), 96-row sample, schema/snapshot receipts, original PDFs/projections and Senate 403 remain unchanged. Senate observations are outside v002, not House failures. No Senate request or access workaround occurred.

All **61 existing House observations** remain, with no replacements. **27** had decisive text-source validation before repair. OCR attempted the other **34 observations across 33 cached official PDFs**, processing 331 pages. Full transaction documents were projected because the archived image-only PDFs supply no reliable text page index; source geometry alone drives row extraction. No expected asset, ticker, action or date is supplied to the OCR worker. A general parser extracts rows first; association uses source asset/printed-symbol evidence, then independently compares action/date. Ambiguous associations and low-confidence OCR remain UNKNOWN. Labeled checkbox cells retain source-image coordinates and ink measurements; multiple marked cells remain ambiguous. Repeated assets corroborate core fields only if every matching source row has identical action/date values. Source-informed general layout interpretation is not an independent classifier holdout.

The isolated pipeline uses RapidOCR 3.4.0, ONNX Runtime 1.23.2, pypdfium2 4.30.0 and packaged local models. Four local processes partition the fixed documents; each uses one CPU inference thread and identical settings. Render hashes, page numbers, token boxes/confidences, source hashes, model/configuration and projection hashes are retained privately. OCR is **DERIVED_PROJECTION_OF_PRIMARY_ORIGINAL**, not a new primary source. [Wheel lock](exp007_house_ocr_requirements.lock), [licence/notice inventory](exp007_house_ocr_inventory.json) and [canonical certificate](exp007_house_source_certificate_v002.json) preserve reproduction evidence. Canonical research requirements are unchanged. Rendering follows the [pypdfium2 API](https://pypdfium2.readthedocs.io/en/v4/python_api.html); engine provenance is [RapidOCR](https://github.com/RapidAI/RapidOCR).

The first offline setup caught the library's automatic visualization-font fetch at the socket guard; no projection completed. It was corrected to use a local Windows Arial font, which does not influence recognition. The failed setup log and initial render remain retained. No cloud OCR, LLM transcription or external OCR request occurred. Local dependency downloads and official software-documentation review are separate from scientific source calls.

## Frozen source gate

The criteria were committed and pushed in `deae95a` before OCR: at least **55/61** decisive type/date/asset rows; zero confirmed purchase/non-purchase disagreements; decisive date/type agreement at least 98% and normalized asset agreement at least 95%; no undermining systematic unresolved cluster. No threshold was relaxed.

**Final decisive rows: 28/61; unresolved core validation: 33/61.** Confirmed purchase/non-purchase disagreements: 0. The decisive minimum fails. Field-specific unknowns remain explicit:

| Field | Agree | Disagree | Unknown |
| --- | ---: | ---: | ---: |
| transaction type | 28 | 0 | 33 |
| transaction date | 36 | 0 | 25 |
| asset description | 36 | 0 | 25 |
| printed ticker | 26 | 0 | 35 |
| member identity | 58 | 0 | 3 |
| document identity | 27 | 0 | 34 |

Printed ticker is compared only when original evidence supports it; a resolver-corrected symbol is never required to appear in a filing. Member/document identity are reported separately from the three mandatory transaction fields. An UNKNOWN is not a source disagreement, a non-purchase or zero activity. This result does not prove upstream purchases are materially misclassified or that every original is unreadable.

| Unresolved cluster dimension | Group | Frozen observations | Core unresolved |
| --- | --- | ---: | ---: |
| action | exchange | 3 | 1 |
| action | purchase | 29 | 17 |
| action | sale | 29 | 15 |
| amendment | False | 55 | 30 |
| amendment | True | 6 | 3 |
| printed_present | False | 31 | 27 |
| printed_present | True | 30 | 6 |
| year | 2014 | 8 | 6 |
| year | 2015 | 5 | 2 |
| year | 2016 | 5 | 4 |
| year | 2017 | 12 | 9 |
| year | 2018 | 6 | 3 |
| year | 2019 | 4 | 2 |
| year | 2020 | 10 | 5 |
| year | 2021 | 11 | 2 |

These retained clusters describe extraction missingness, not market outcomes. The mechanical source gate fails independently of a favorable interpretation of cluster patterns; no downstream source-resolved trading population is certified.

## Final stop and verification

**Abandon EXP007 as a source-feasibility candidate.** No third source repair, fresh sample, reduced thresholds, modern-year restriction, Senate retry, alternate original route or new OCR provider follows. The predictive economic hypothesis remains untested. Provider/class/path certification, actual event aggregation, market sessions/prices, inference calibration, synthetic power, Proof, spec, freeze and Development are **NOT_RUN**. There is no effect, interval, p-value or materiality verdict. The 8-evaluation ceiling remains untouched; performance evaluations and confirmation outcome accesses are **0**.

Scientific source starts: **0**; Senate **0**; provider/identity/Nexus/Aurora **0**. Only cached originals were used; no purchase or upgrade. Account-wide debit is UNKNOWN. Source geometry keeps Development 2014–2021 and owner-held confirmation 2022–2025 as prior planning boundaries; no stage was opened or shortened to improve coverage. The owner-predeclared modeled EOD and second-later-session entry contract remains unactivated; exact public availability remains UNKNOWN.

Validation: **451 local tests, 223 public tests, 0 skipped**. [Receipt](exp007_house_validation.json). Public report regeneration reads tracked receipts; private audit verifies immutable PDFs, render/text hashes, blind extraction replay and the frozen 61-row frame. Public CI needs no OCR binary, private filing or network.

```sh
python -m src.research.house_repair_report --check
python -m src.research.house_repair_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Recreate the isolated helper on CPython 3.13/Windows x86-64 with `python -m venv .research/exp007_house/ocr-env`, then its interpreter's `pip install --require-hashes -r docs/acceleration/exp007_house_ocr_requirements.lock`. Private OCR replay additionally needs the archived exact dispatch, original PDFs and local Arial font; no source acquisition command is included. Source hashes, parser code and model hashes identify this reconstruction, not contemporaneous ingestion or legal disclosure exhaustiveness.

EXP002–EXP006 remain closed to new research; EXP004 stays paused and EXP005/EXP006 abandoned/absent. Previous reports, raw bodies, frozen experiments, processed metrics and dependency pins are preserved. No paid provider, Phase 4B, optimizer or paper/live operation occurred. **Stopped under owner sections 8/25; no automatic next phase.** Commit/push and hosted CI are delivery receipts reported separately.
