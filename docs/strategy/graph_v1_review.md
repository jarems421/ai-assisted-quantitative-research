# Graph v1 final review and pilot preflight

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**2026-10-21. Targeted corrections only; no pilot, acquisition or architecture change.** The review re-read every catalogue mapping against its cited report and checked each SEC identity. It also tested whether the offline evaluation reads only its declared inputs, and whether the baseline it compares against is competent.

It found and corrected four real defects:
- **Mapping errors:** three mappings were inaccurate, and one finding's text did not match its quote.
- **Identities:** archive-path CIKs were presented as fully identified issuers.
- **Evaluation inputs:** the evaluation depended on the real catalogue.
- **Baseline:** the baseline was a substring search with no period check, and the pilot export gave the baseline less memory than the graph.

**Follow-up:** the pilot protocol was corrected in [revision 2](graph_pilot_preregistration.md) under a [later instruction](owner_graph_pilot_protocol_2026-10-21.md). It fixes the `--known-at` cutoff, carry-over between arms, blinding, decision rules and packet eligibility; see its corrections table.

[Owner instruction](owner_graph_pilot_preflight_2026-10-21.md) · [Pilot pre-registration (proposed)](graph_pilot_preregistration.md) · [Proposed owner authorisation (not active)](proposed_owner_graph_pilot_authorisation.md) · [Catalogue V002](graph/research_memory_catalogue_v002.json) · [Validation](graph_v1_review_validation.json)

## 1. Historical requirement mappings

**Versioning.** The catalogue is now versioned rather than edited in place:
- **V001:** `research_memory_catalogue.json` (SHA-256 `3ca36321…16bb`, commit `ab00a97`) is byte-identical and still loads.
- **V002:** `research_memory_catalogue_v002.json` supersedes it. V002 records 12 corrections, each with its target, old value, new value, reason and citation, in `mapping_corrections`. All seven verdicts are unchanged. A test asserts that the verdict sets of V001 and V002 are equal.

**All 38 V001 findings were reviewed:** 32 unchanged, 6 corrected and 1 finding added.

| Finding | V001 mapping | V002 mapping | Why |
|---|---|---|---|
| F03 F1, F2 | `REQ_REALISED_ACTIVITY` | **`REQ_QUALIFIED_COMMERCIAL_EXPOSURE`** (new class) | F03 needs "a documented, material, qualified supplier opportunity that investors had reason to expect". That is an expected commercial position, not activity that occurred. V001's realised-activity definition itself contained "qualified sales or orders", which caused the conflation; that wording was removed |
| F03 F3 | `SOURCE_OMISSION` → historical version | **`ACQUISITION_LIMIT`**, no requirement | The passage says a summary was retrieved instead of the full decision. It does not show that the full decision is unavailable |
| F19 F3 | `SOURCE_OMISSION` → historical version | **`ACQUISITION_LIMIT`**, no requirement | The parent filing was a byte-limited prefix. The report calls it "a resource limitation rather than an access denial" |
| SH09 F4 | Text said "recoverable-net not reconstructed", but the quote concerned the combined charge | Text and quote now both state "no pre-announcement change in asset-specific recoverable-net exposure" | Text and quote did not match |
| SH09 F10 (new) | — | Combined charge not a cleanup-only, Cox-only or lease-matched outcome → `REQ_ENTITY_COHORT_JOIN` | The quote moved off F4 describes an outcome-scope gap |
| EF06 F2 | `REQ_ENTITY_COHORT_JOIN` | **`REQ_DOCUMENTED_ALLOCATION`** | The passage forbids inventing carrier, cancellation, reinsurance or monthly allocations of group totals |

**Kept after review:**
- F01's capacity, activity and control mappings.
- SH09's omitted schedules and unacquired motion, which name the needed historical object; the clarified definition says the class does not assert unavailability.
- SH09's security allocation.
- EF06 v1 retained premium.
- EF03 available output.
- F19's cohort join and credits used.
- F09's redaction.

**Definitions clarified:**
- **`REQ_HISTORICAL_SCHEDULE_OR_VERSION`** now excludes "an incomplete or partial retrieval of an existing original (an acquisition limit, not unavailability)".
- **`REQ_ENTITY_COHORT_JOIN`** now names verified ownership and control explicitly, which F01 F4 relies on.

**Resulting groupings.** `same-gap REQ_HISTORICAL_SCHEDULE_OR_VERSION` now returns only SH09, and `REQ_REALISED_ACTIVITY` no longer returns F03. Mappings remain retrieval aids pending human review.

## 2. SEC CIK identities

**Defect.** V001 projected six SEC entities as `IDENTIFIED`, with their reported type feeding conflict detection. Their CIK only names the EDGAR archive directory of a recorded document. Nothing had corroborated the issuer name, listing, securities or group structure.

**V002 and the projection now:**
- **Name citation:** each CIK requires a `name_citation`. This is a quote from the cited report that contains both the archive path and the entity name. It is the report's own link text, for example `[Chevron January 2, 2024 8-K](…/edgar/data/93410/…)`. For Voya Financial, the name comes from the cited link's file name.
- **Corroboration statement:** each CIK records that listing, securities, subsidiaries and ownership are not established.
- **Status:** catalogue-only CIKs are `ARCHIVE_PATH_IDENTIFIER`, not `IDENTIFIED`, and carry that restriction.
- **Types:** catalogue types go into `memory_types`, which are excluded from type-conflict checks. A live ledger recording the same CIK as a legal entity therefore causes no spurious conflict.
- **Joins:** an exact CIK join with a live ledger is still made. Every such suggestion lists, under not-yet-verified, "that the archive-path CIK in historical memory is the same economic entity".
- **Leaps:** `explain` reports `IDENTITY_UNCORROBORATED` for an archive-path-only entity.
- **No invented structure:** no subsidiary edge links Voya Financial (CIK 1535929) and the name-only Voya insurer; a test checks this. No ownership, security or ticker is created anywhere.

The salmon locality numbers and vessel MMSIs remain recorded identifiers, quoted from the report's table and text.

## 3. Evaluation isolation

**Defect.** The synthetic evaluation loaded the real catalogue for its requirement vocabulary, so the benchmark depended on an undeclared input, and could change when the catalogue changed.

**Fix:**
- **Declared inputs only:** `evaluate.run` builds with `catalogue_path=None` and an explicit fixture vocabulary (`fixtures.REQUIREMENTS`). It records the declared inputs: ledger file hashes, the vocabulary digest, no catalogue and no ledger discovery.
- **Refusal:** it refuses to run (`isolation violated`) if any historical node, catalogue, excluded input or extra ledger appears.
- **Test:** a test runs the evaluation with catalogue loading and ledger discovery patched to fail, and passes.

**Already isolated, confirmed by tests:**
- Memory and prospective modes exclude synthetic ledgers.
- Prospective mode excludes the catalogue and retrospective ledgers.
- `--known-at` excludes later-appended records and a catalogue recorded later.
- The walkthrough's single synthetic-with-memory demonstration is labelled.

## 4. Baseline fairness

**V001 baselines, and why they were unfair:**
- **"Identifier search" matched substrings.** For example, `SYN_FACILITY:T-7` matches inside `SYN_FACILITY:T-7B`.
- **It ignored relationship periods and versions.**
- **It joined name strings.**
- **In the pilot hook it searched ledgers only**, while the graph also had historical memory. Every catalogue-based graph suggestion would therefore have been mis-labelled "graph only".

**New competent baseline.** [`baseline.py`](../../src/research/graph/baseline.py) uses no graph projection. It:
- loads ledgers through Discovery Lab's validated loader, using latest versions and honouring `--known-at`;
- matches exact identifier fields, never substrings;
- matches content-evidence hashes;
- matches exact requirement tags;
- follows each claim's recorded observation and relationship references;
- excludes relationships whose period is incompatible or unresolved;
- refuses `NAME:` and `TICKER:` joins;
- searches the catalogue's structured entity, document and requirement fields when the graph has memory.

It is exposed as `python -m src.research.graph baseline-search`, the structured arm's tool in the pilot. The pilot export now gives this baseline the same ledgers, catalogue and `--known-at` as the graph.

**Revised offline comparison** (synthetic and constructed, so a functional check only):

| Task | Truth | Naive text | Structured search | Graph |
|---|---|---|---|---|
| T1 | connected | recovered | recovered | recovered |
| T2 | not connected (look-alike facility) | false connection | correctly absent | correctly absent |
| T3 | identity unproven (name only) | premature join | withheld | withheld and flagged |
| T4 | not connected (period) | false connection | correctly absent | correctly absent |
| T5 | identity unproven (ticker) | premature join | withheld | withheld and flagged |

**A competent structured search matches the graph on every claim connection in this set.** The graph's increment here is identity questions and step-by-step explanation, not recall. The pilot must test whether that increment, plus cross-campaign memory and requirement grouping, is worth the analyst time it costs.

## 5. Regression tests

Six tests cover the defects found:
- the V002 corrections, V001 preservation and resulting groupings;
- archive-path CIK identity, name citations and refusal of a corrupted citation;
- the archive-path join caveat with no type conflict;
- evaluation reading only declared inputs;
- exact, temporal and identity-aware baseline behaviour, including the substring case and known-at;
- the pilot export giving the baseline the same memory.

The adjudication-log test now covers the arm field and `CON-` connection IDs.

## 6. Remaining limitations

- **Untested in practice.** Every utility result is synthetic. The real catalogue holds seven investigations, and no live ledger exists.
- **Pending review.** Requirement mappings, including the V002 corrections, are curated by Claude and still need human review. The new class has a single member, F03.
- **Uncorroborated CIKs.** Archive-path CIKs remain uncorroborated, because corroborating them would need new acquisition.
- **Manual blinding.** Adjudication blinding in the pilot depends on a procedure (a separately prepared, shuffled export), not on software.
- **No dedicated fetcher.** Pilot source retrieval would use the existing receipt practice. There is no dedicated bounded-fetch tool; see the authorisation's activation conditions.
