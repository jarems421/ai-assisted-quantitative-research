# Item 2.02: conservative date repair and population closure

**SCALABLE_ACCEPTANCE_DATE_BOUND_READY. Sampled Item 2.02 concordance passes. EXP006 freeze remains blocked at HISTORICAL_POPULATION_VERSION_IDENTITY_BLOCKED.** Starting HEAD `cafb8e9c6ea7fec23d2a4ac366ab1af03440cf47`, as of 2026-10-13. The owner's expected checkpoint was followed by the README-only `cafb8e9` commit; research inputs were unchanged. [Exact owner instruction](owner_item202_date_repair_2026-10-13.md).

The narrower civil-date requirement was tested and passed; exact raw-clock reconstruction was not attempted or asserted. The [earlier freeze review](exp006_freeze_review.md), mixed-clock failure, calendar sensitivity and v002 policy keep their original bytes. This pass continued automatically into primary classification and population/identity review, then stopped at those remaining scientific gates. No prices or performance were accessed.

## Date provenance

The [frozen v003 transform](exp006_availability_contract_v003.json) takes the maximum of the ISO string's lexical date, its literal offset-aware instant converted to New York civil date, and the census filed date. Eligibility is the second regular NYSE session strictly after that envelope, at 09:30 New York. No CIK/year offsets or learned clock corrections are used. Conservative later execution is accepted by the owner. Exact public availability remains UNKNOWN; timing is modeled and the policy is not activated for a trading population.

The [new sample](exp006_date_validation_sample_v003.json) was pushed in `35f3fba` before its first header request. It excludes the original 48 records. Each of 48 year/quarter/form cells has five accessions: all six Development years, four quarters, originals and amendments. Hash-ordered clock-stress strata use only archived Development source metadata. Representation proxies are sampling labels, not inferred serialization modes.

| Expanded original-header audit | Count |
| --- | ---: |
| New original headers / HTTP 200 | 240 / 240 |
| Envelope earlier than any raw candidate civil date | 0 |
| Bulk lexical / literal-New-York date exactly matches latest raw civil date | 149 / 223 |
| Both retained raw interpretations have the same civil date | 240 |
| Same-day / later-day envelope versus latest raw civil date | 138 / 102 |
| Same / later / earlier eligible open | 192 / 48 / 0 |
| Delay: 0 / 1 / 2+ sessions | 192 / 48 / 0 |
| Raw-v002 candidate-open non-invariance in sample | 0 |

[Canonical validation](exp006_date_validation_v003.json) retains each source hash, candidate date and open, and the full cell/stress distributions: 40 records per year, 60 per quarter and 120 per form. It covers near lexical UTC midnight (57), near New York midnight (48), Friday (99), DST-window (38) and pre/regular/after-market **bulk-clock** strata (64/66/110). These overlapping strata are not raw-market-hour observations. Observed literal-bulk minus seasonal-source offsets include -5, -4, 0, +4 and +5 hours (39/49/55/76/21). The sample directly exercises the prior representation discrepancies without reconstructing unsampled raw seconds.

This is an expanded mechanical source audit, not proof that every unsampled metadata value is error-free. Full-population missing/conflicting/out-of-scope inputs remain unavailable. The passed bound permits subsequent source closure; it does not certify class-specific calendars, identity, execution or returns.

## Official archive feasibility

Both separately predeclared official channels were reached through their root, year and quarter JSON indexes (six HTTP 200 responses). The first frozen day, 2015-01-06, requested the evidenced Oldloads `.gz` and Feed `.nc.tar.gz` links. Each transfer crossed the declared 256 MiB ceiling and stopped; neither was retried. Twelve fixed days remain in [the archive frame](exp006_archive_feasibility_v003.json), with eleven unvisited days retained explicitly.

Oldloads retains a 269,484,032-byte prefix: its initial reader checked after a 1 MiB chunk and overshot the ceiling by that chunk. The corrected Feed reader retains 268,435,457 bytes (ceiling plus one detection byte). Original prefixes, errors and persisted stops are immutable. The inherited transport-error schema did not retain response status/headers, so those statuses remain UNKNOWN. Whole-file sizes/hashes, uncompressed totals, accession extraction and exact raw-header reconciliation were not certified. Successful directory access is not full archive scalability; bounded transfer failure does not prove the archives inaccessible. Synthetic gzip/tar tests verify extraction logic separately.

No enormous raw-header fallback was launched: the date envelope passed. Six-year PAC/deletion exhaustiveness is still unresolved; these partial day files cannot establish it.

## Primary classification and historical population

The 96-record source-only primary sample froze in `4c48a83` before body requests, with two records per year/quarter/form cell. Positive/negative balance was attempted where the fixed timing sample supplied both; actual labels are 27 positive and 69 negative. No missing stratum was replaced by an outcome-selected issuer.

The first title parser returned TP22, TN69, FP0, FN0, UNKNOWN5. [Its original receipt](exp006_primary_validation_v003.json) is preserved. Source locators show a Disclosure-of prefix, singular Operation or Unicode dash in those five headings. A separately versioned general rule was applied to all 96 cached originals, with no accession-specific override or further download. [Reviewed concordance](exp006_primary_title_review_v003.json): **TP27, TN69, FP0, FN0, UNKNOWN0; coverage 100%.** Header, bulk declaration and primary title agree. This source-informed parser review is not an independent classifier holdout.

| Source population / certification boundary | Result |
| --- | --- |
| Current quarterly census | 438,666 rows: 426,750 originals / 11,916 amendments |
| CIKs / unique accessions | 11,340 / 426,974 |
| Provisional Item 2.02 labels | 108,364 original rows / 983 amendment rows |
| Candidate source keys / unique accessions / CIKs | 109,347 / 106,895 / 6,196 |
| Full-population certified Item 2.02 count | UNKNOWN; 96-source concordance is a sample certificate |
| Full-population classification/version states unresolved | 438,666 |
| Dated class/provider-bound source keys | 0 certified / 109,347 unresolved |
| Renamed / ended classes; complete terminal paths | Counts UNKNOWN; no complete terminal certificate |

[Population review](exp006_population_identity_review_v003.json) keeps current-index keys, amendments, shared accessions and cofilers. Candidate shared-accession excess is 2,452 rows; they cannot become independent trades by deduplication on CIK or accession alone. SEC's [PAC documentation](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) explains why rebuilt quarterly/full indexes do not prove the original daily/feed/oldload vintage. Historical deleted keys, unavailable-original counts and amendment-parent links remain unproved, never zero by assumption.

The minimum source-key binding table retains all 109,347 provisional records with nullable class, security ID, venue, effective spans and provider ID. Prior identity receipts have 60 cases and zero complete spans; 57 candidate CIKs overlap that point-evidence frame. No point or current ticker was promoted into a historical span, and no row was dropped. Filer CIK is not a security class. This prevents a certified non-hindsight equity/event/control population and population-preserving valuation, including ended histories. That is the specific closure blocker after the timing and sampled classification passes.

## Stop, verification and reproduction

Market provider/API certification, exact matching, real execution, inference candidates/calibration and synthetic power were not run after the upstream population/identity stop. No spec hash, freeze commit, Development event/pair count, effect, interval or p-value exists. EXP006 remains absent; performance evaluations and confirmation accesses are **0**, with the 12-evaluation ceiling unchanged. EXP004 stays paused; EXP005 stays abandoned/absent. No Nexus, Aurora, purchases, optimizer, paper/live or new phase occurred.

New direct starts: **344 SEC** (240 headers, 96 primary documents, six archive directory probes, two incomplete archive GETs); zero retries, zero market/provider requests. One official-guide browser review is separate; its underlying fetch count is unknown. Git/GitHub delivery checks are also separate. No purchase/upgrade; account-wide debit is unknown. Identity loads locally without exposing its value. The inherited collector's generic User-Agent receipt label is inaccurate for these SEC calls: the wrapper actually supplies the locally configured identified SEC User-Agent. A separate redaction/provenance annotation records this without changing old receipts or publishing contacts.

**Validation:** 378 local tests; 150 public tests; zero skipped. [Validation receipt](exp006_date_repair_validation.json). Earlier reports, contracts, frozen experiment artifacts, source bodies, processed baselines and dependency pins are hash-checked. No historical report is regenerated or rewritten by this pass.

```sh
python -m src.research.item202_date_repair_report --check
python -m src.research.item202_date_repair_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Report regeneration uses tracked summaries only; private audit needs ignored originals and source-key bindings and makes no network request. Remote acquisition commands require explicit `--execute`; completed receipts and persisted stops prevent blind retry. The earlier raw-clock failure remains historically true; the new date-bound certificate is distinct. **Stopped at historical population/version and class-identity certification, before freeze or performance.** Commit SHAs and hosted CI are recorded in the delivery message, without embedding a self-referential final SHA here.
