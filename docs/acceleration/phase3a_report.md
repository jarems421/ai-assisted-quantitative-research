# Phase 3A: SEC source certification and identity feasibility

**Fifteen scoped annual observations are certified; trading and execution remain blocked.** As of 2026-10-12. No new filings, strategy research, performance queries, Nexus operations or EXP005 were started.

| Gate | Verdict |
| --- | --- |
| Acceptance timestamp interpretation | PARTIAL |
| Exact public availability | UNKNOWN |
| Conservative eligibility policy | PROPOSED_NOT_APPROVED |
| Historical class identity | PARTIAL |
| Financial semantic interpretation | CERTIFIED_FOR_SCOPED_FACTS |
| Text segmentation | DEFERRED |
| Nexus historical execution | BLOCKED |
| Phase 3B design readiness | READY_FOR_CONDITIONAL_DESIGN |

## Acceptance and public availability

| Accession | Original acceptance | Certified UTC | Seasonal ET candidate | Literal EST candidate | Interpretation |
| --- | --- | --- | --- | --- | --- |
| 0000320193-19-000119 | 20191030181236 | UNRESOLVED | 2019-10-30T22:12:36+00:00 | 2019-10-30T23:12:36+00:00 | PARTIAL |
| 0000320193-20-000096 | 20201029180625 | UNRESOLVED | 2020-10-29T22:06:25+00:00 | 2020-10-29T23:06:25+00:00 | PARTIAL |
| 0001326801-20-000013 | 20200129211214 | 2020-01-30T02:12:14+00:00 | 2020-01-30T02:12:14+00:00 | 2020-01-30T02:12:14+00:00 | CERTIFIED |

The [SEC PDS specification](https://www.sec.gov/files/info/edgar/pdsdissemspec072213.pdf), section 2.1, labels acceptance time “EST”. The [SEC FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) ties the SGML timestamp to that definition. The archived [Regulation S-T business-hour rules](https://www.govinfo.gov/content/pkg/CFR-2011-title17-vol2/pdf/CFR-2011-title17-vol2-sec232-11.pdf) use standard or daylight time when applicable, but do not explicitly redefine the SGML field. Winter conversion converges under both interpretations; the two October conversions differ by an hour. Those candidates are separated from certified acceptance; no undocumented DST assumption is activated. A dated authoritative clarification of the SGML field’s daylight-saving behavior is the remaining timestamp blocker.

The SEC FAQ states there is no first-public website timestamp and no guaranteed posting lag. The [SEC access guide](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) notes next-business-day dissemination for some late filings; the PDS describes a subscriber feed, which is a different channel from website availability. Neither generic timing statement certifies an accession’s exact first-public instant. All observed public timestamps remain UNKNOWN. Four narrowly bounded documentation responses were archived privately, with URL/retrieval-time/byte hashes retained in evidence. No new filing acquisition occurred.

## Scoped source findings

See the [financial-semantic QA](phase3a_financial_qa.md), [historical identity matrix](phase3a_identity.md) and [proposed availability policy](availability_policy_v001.md). Each of five concepts per filing is selected by a separately versioned rule and reconciled to original primary Inline XBRL scale/context/unit. Original facts and alternatives remain immutable. AAPL/FB cover-page evidence and existing source identifiers improve feasibility but do not certify listing-effective spans or a class bridge.

| Accession | Candidate Item 1 / 1A / 7 / 8 lengths (characters) | Text verdict |
| --- | --- | --- |
| 0000320193-19-000119 | 13097 / 54994 / 34079 / 96467 | DEFERRED |
| 0000320193-20-000096 | 13163 / 60994 / 32221 / 96953 | DEFERRED |
| 0001326801-20-000013 | 13233 / 139450 / 63133 / 98262 | DEFERRED |

Pinned EdgarTools 5.62.0 supports `ParserConfig(form="10-K")`; the generic Phase 2 call did not provide a form. The configured offline probe extracts all twelve requested candidate items reproducibly. Item text hashes/character counts are retained; source start/end anchors, TOC exclusion and cross-reference boundaries are not independently certified. Segmentation is DEFERRED rather than inferred from plausible lengths. No new segmenter, embeddings, search service or sentiment model is built.

## Nexus dependency

Retain EXECUTION_BLOCKED. The [existing execution contract](historical_execution.md) still requires:

- Source-side dated stable-ID/class/ticker/listing lineage, separate from SEC issuer identity.
- Complete publication with preserved identity, availability, values and every requested point; storage acceptance alone is insufficient.
- Exhaustive pre-filter runtime identity lists matching the certified population exactly, including renamed and ended histories; no equal-count substitution or current-survivor pruning.
- Audited corporate-action, cash/stock conversion, merger/delisting terminal-value and position-transition handling under declared costs/timing.

Source-side progress does not resolve the demonstrated Nexus pruning failure. No vendor call, support message, upload, diagnostic or EXP004 operation occurred.

## Reproduction and preserved history

```sh
python -m src.research.sec_pilot.phase3a --check
python -m src.research.sec_pilot.phase3a --report-only --check
python -m unittest discover -s tests -v
python -m src.research.sec_pilot replay
python -m src.research.sec_pilot audit
python -m src.research.sec_pilot report --check
python -m src.research audit EXP004
python -m src.presentation.exp001 --check
```

The full new check uses existing ignored Phase 2 snapshots, the four archived documentation responses and existing source parts; it has no acquisition path. Report-only regeneration needs the public canonical evidence. Versioned interpretation receipts use new content-hash filenames under ignored storage; earlier prototypes are retained. Phase 2 raw bodies, derived snapshots, hashes, original report/summary/validation and all frozen experiments remain unchanged. Legacy regression tests use already-opened EXP001 local records and do not authorize new held-out research access. Dependency pins and the isolated environment remain unchanged.

The baseline was 191 passing tests. Final executed checks and counts are recorded in [validation](phase3a_validation.json). The code checkpoint `62a8abb` added interpretation/eligibility/semantic gates; subsequent verified commits and push status are reported in the delivery message.

## Recommendation and stop

READY_FOR_CONDITIONAL_DESIGN means enough scoped annual accounting evidence exists to discuss a future mechanism and data requirements. It is not permission to construct a trading-ready signal, run performance tests or freeze EXP005. Before executable research, obtain the October timestamp clarification, owner review of the proposed availability assumption, an independently dated class/ID bridge and certified population-preserving execution. Do not compute fundamental acceleration across incompatible comparative EPS/share bases or infer analyst earnings surprise without a separate expectations source.

**Stopped after Phase 3A.** No Phase 3B, broader SEC backfill, real policy approval, portfolio optimization, purchases, Test opening, paper/live operation or new experiment is included.
