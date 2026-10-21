# Graph v1 historical backfill audit

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-21.** This audit records what the [historical-memory catalogue](graph/research_memory_catalogue.json) contains, what it leaves out on purpose, what it adds only as a retrieval aid, and what stays unresolved. No new scientific source was acquired, and every quote and document hash was checked against tracked repository files when the catalogue was written (`recorded_at_utc` 2026-10-21T11:05:23Z).

## Decision: catalogue entries, not reconstructed ledgers

None of the seven investigations was run in Discovery Lab. Rebuilding them as retrospective Discovery Lab campaigns would have meant writing dozens of required fields the original reports never recorded, freezing claims that were never frozen and assigning modern dispositions to historical verdicts. That would be a complete-looking but partly fictional ledger. So every investigation is held instead as **cited, non-authoritative memory**:

- **Verdicts:** each verdict is quoted verbatim, with its scope, from the report that recorded it.
- **Findings:** each finding carries an exact quote, its cited file and that file's SHA-256 at cataloguing time.
- **Documents:** documents appear only where a tracked receipt records their SHA-256 and locator. The validator checks both strings against the receipt.
- **Entities:** identifiers appear only when the repository already records them, either in a report or as a SEC archive path in a recorded locator. Everything else is `NAME:` and confined to its own investigation.

The graph turns this memory into `history`, `history_claim` and `history_finding` nodes. They are labelled `HISTORICAL_MEMORY`, and they never become observations, relationships, Discovery Lab claims, reviews, dispositions or freezes.

## Per-family record

| Family | Verdict quoted | Claims | Findings (kinds) | Requirement mappings | Entities (identity basis) | Documents by hash |
|---|---|---|---|---|---|---|
| **F01** salmon treatment capacity | BOUNDED_VERIFICATION_CLOSED / NOT_READY | 1 | 8: gaps 2, scope 2, identity 1, field present 1, access note 1, evidence-to-change 1 | Available capacity, realised activity, entity/cohort join | 4 BarentsWatch localities and 2 wellboat MMSIs (recorded identifiers) | 4 (all HTTP 200) |
| **SH09** offshore predecessor obligations | STOP / M NOT PASSED / H NOT ESTABLISHED | 1 | 9: gaps 3, omission 1, retrospective-only 1, access blocked 2, scope 1, evidence-to-change 1 | Historical schedule/version, documented allocation, retained/net | Chevron (CIK from SEC path); W&T and the Cox lease cohort name-only | 4 (two 200, two 403 error bodies) |
| **EF06** Citizens takeouts | HOLD v1; reject v2 as investment priority | 2 (v2 reformulates v1) | 5: gaps 2, field present 1, restricted M pass 1, information limit 1 | Retained/net, entity/cohort join | HCI (CIK from SEC path); carriers name-only | 3 (one is the recorded incomplete 6 MiB+1 prefix) |
| **F19** guaranty assessments and tax credits | HOLD / unapproved | 1 | 5: gaps 2, omission 1, field present 1, evidence-to-change 1 | Entity/cohort join, realised activity, historical version | Aetna, Voya Financial (CIKs from SEC paths); Voya insurer subsidiary name-only | 3 (one incomplete prefix) |
| **F09** creditor-protected receivables | Second investigation priority, not a pilot | 1 | 4: gap 1, field present 1, scope 2 | Unredacted contract amount | Mattel, Hasbro (CIKs from SEC paths); Toys R Us name-only | 2 |
| **F03** chemical permission and substitute sales | PROMISING BUT MISSING A CRITICAL INPUT | 1 | 5: gaps 2, omission 1, scope 1, evidence-to-change 1 | Realised activity, historical version | BASF name-only | 1 |
| **EF03** IV-fluid substitute output (distinct from F03) | HOLD / M NOT PASSED | 1 | 2: gap 1, information limit 1 | Available capacity | ICU Medical name-only | 0 (the campaign acquired none) |

F03 and EF03 are separate entries, with separate reports and separate verdicts. They are linked only as `related` investigations.

## Omitted deliberately

- **No observations or relationships.** The salmon visit counts, Citizens policy counts, Aetna's liability and the W&T purchase price stay quoted findings. They were not converted into numeric observation nodes, because the catalogue would then be producing new structured measurements from narrative summaries.
- **No freezes, reviews or dispositions.** Historical verdicts are cited, not re-adjudicated, and are never relabelled into the Discovery Lab decision vocabulary.
- **No predecessor obligation, lease list, security allocation, carrier allocation or redacted amount.** These are exactly what the original investigations failed to obtain.
- **No private material.** The salmon authentication token receipt (`PRIVATE_AUTH`) and all private archive bytes are excluded; the catalogue validator refuses any citation outside tracked `docs/` paths.
- **Not yet catalogued:** the other short-horizon and eight-family candidates, earlier frontier work and EXP001–EXP007. They can be added later under the same rules.

## Added only as retrieval aids

- **Requirement mappings.** Each finding is mapped to one of seven requirement classes, and the mapping is marked `mapping_review: PENDING_HUMAN_REVIEW`. A mapping helps find related investigations; it never claims that the requirement was met or that the gap cannot be filled.
- **SEC CIKs.** These are read from the archive path of a locator that a tracked receipt records, for example `/edgar/data/93410/`. The validator checks that the CIK matches that path. They identify an SEC filer, not a security, share class or ticker.
- **`status_class`** (STOPPED, HOLD, NOT_ADVANCED). A coarse grouping label; the verbatim verdict text remains the record.
- **Historical closure dates.** The report date, shown as context only. Graph knowledge time is the catalogue's own `recorded_at_utc`, so `--known-at 2026-10-20` excludes all historical memory.

## Unresolved

- Every human requirement judgment remains as the original reports recorded it. The catalogue adds no M or H judgment.
- Name-only entities are not joined across investigations. An identity question is raised only when names are similar within the loaded graph.
- **Quote currency:** if a cited report changes, the build flags `CITATION_HASH_CHANGED` (quote still present) or `STALE_CITATION` (quote gone). A removed report is flagged `MISSING_SOURCE_DOCUMENT`. No memory is silently refreshed.
- **Pending review:** the requirement mappings await human review. Until then, treat `same-gap` groupings as curated leads.
