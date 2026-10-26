# Source Custody V001: verified retrieval into Quarry custody

Source Custody V001 takes **one verified Source Retrieval V001 target receipt** and makes it **one native Quarry package**. That package exports through Quarry's unchanged interface into the existing Jev navigation input.

It is offline and deterministic. It performs no network access, retrieval, extraction, OCR or interpretation, and it records no human judgement of its own. A retrieved body enters custody only with a named human's claims record, because a Quarry supply's identity and asset claims are human assertions.

- Code: `src/research/quarry_v1/contracts.py` (`QUARRY_SUPPLY_V002`), `src/research/source_custody_v1/` (the bridge).
- Tests: `tests/test_source_custody_v1.py`.
- Interface history: `docs/source_discovery_shared_interface_v001.md`.

**Status:** synthetic fixtures only. No real attempt, claims record or custody exists, and no live activity occurred.

## Contracts it builds on (as implemented on `main`)

### Source Retrieval V001

Full contract: `docs/source_retrieval_v001.md`. Records live under `<base>/source-v1/attempts/<attempt_id>/`:

| Record | Format |
|---|---|
| `result.json` | `SOURCE_ACTIVITY_RESULT_V001`, derived by `retrieve.derive` and anchored in the journal (`ATTEMPT_FINISHED`/`ATTEMPT_REFUSED`) or by `finalisation.json`. `custody_handoff[]` lists each eligible target body: `receipt_sha256`, `requested_url`, `quarry_route_id`, `body_path`, `body_sha256`, `bytes`, `coverage` |
| `receipts/NNN.json` | `SOURCE_RETRIEVAL_RECEIPT_V001`: facts (`stage`, `http_status`, `framing`, `content_encoding`, `declared_length`, `bytes_received`, `stopped_by`, `failure`, timestamps, addresses) plus `termination`, `complete`, `coverage` and `limitations` recomputed from them |
| `raw/NNN.body` | The retained bytes, including error bodies and prefixes |
| `inputs/` | Exact copies of the owner scope, Quarry registry, Quarry acquisition scope and stop snapshot the attempt ran under |

Only `200` target bodies ending COMPLETE, UNVERIFIED_LENGTH, SIZE_STOP or TIME_STOP appear in `custody_handoff`, with coverage COMPLETE, UNVERIFIED or PREFIX.

### Quarry V001

- `import-file registry supply --file original --out`: creates a create-only package (`claim.json`, `registry.json`, `supply.json`, `original.bin`, `receipt.json`, sealed `manifest.json`). V002 supplies are refused here (see below). It validates the supply with `contracts.supply`, flags identity mismatches and hashes the original.
- `status`, `export package inspection subject [--extracted-file] --out`, `validate-export`: export requires no identity flags, reproduces exact UTF-8 excerpt ranges (from the original, or from an explicitly supplied extraction for binary originals) and emits the existing Jev `JEV_NAVIGATION_INPUT_V001`.

## `QUARRY_SUPPLY_V002`

V002 adds exactly one supply kind, `SYSTEM_RETRIEVED`. Every V001 field keeps its V001 name and meaning, and one object is added:

| Field | Rule |
|---|---|
| `schema` | `QUARRY_SUPPLY_V002` |
| `fixture` | `SYSTEM_RETRIEVED` (the only value) |
| `coverage` | Follows the HTTP transfer exactly: COMPLETE gives `COMPLETE_CLAIMED`, UNVERIFIED gives `UNKNOWN`, PREFIX gives `PARTIAL`. Never `UNAVAILABLE`, never stronger than the transfer |
| `expected_original_sha256` | Must equal the retained body hash |
| `retrieved_at_claim`, `retrieval_method_claim` | Must be the receipt's `finished_at` and `SOURCE_RETRIEVAL_V001 exact-URL HTTPS GET; receipt <sha256>` |
| `limitations` | Must contain the generated transfer limitations: source attempt, URL, HTTP status, termination, bytes, time and receipt; that transfer coverage is not authenticity, dataset completeness or meaning; prefix and unframed warnings. Also the receipt's own limitations and the human's |
| `system_retrieval` | `source_component`, `attempt_id`, `request_sha256`, `result_sha256`, `receipt_sha256`, `requested_url`, `http_status` (200), `termination`, `transfer_coverage`, `body_sha256`, `body_bytes`, `started_at`, `finished_at`, `implementation_sha256`, `claims_sha256`, and the constants `publication_authenticity: UNKNOWN`, `dataset_completeness: UNKNOWN`, `scientific_meaning: NOT_ESTABLISHED` |

**Compatibility rules**

- **V001 is unchanged.** Records without `"schema": "QUARRY_SUPPLY_V002"` are validated by the unchanged V001 schema, so V001 can never claim `SYSTEM_RETRIEVED` or carry `system_retrieval`. OWNER_SUPPLIED and SYNTHETIC records are never reinterpreted.
- **Route binding.** On import and on every load, a V002 supply's route locator must equal `system_retrieval.requested_url` (`contracts.binding`). Route id and version are checked as for V001.
- **Only the bridge creates V002 packages.** Quarry's ordinary `import_file` and `import-file` command refuse a V002 supply. The only V002 creation API is `evidence.import_retrieved(..., source_base=...)`. It re-runs Source Retrieval's native verification of the named attempt under `source_base`, through the bridge's read-only preflight. It then requires the retained receipt, result, original and imported Quarry registry to be byte-identical to the native records the attempt was authorised under, and the route and version to match (`NATIVE_MISMATCH` otherwise).
- **Retained native records.** A V002 package keeps the exact bytes of three native records: `retrieval-receipt.json` (the Source Retrieval receipt), `retrieval-result.json` (the attempt result) and `retrieval-claims.json` (the human claims record). They are sealed in the package manifest and copied into every export under `source/`. On import and on every load, Quarry checks `contracts.retained`:
  - the three records' hashes match the supply binding;
  - the receipt is a 200 TARGET receipt for that URL, termination, coverage, times and implementation, with the retained original's hash and size;
  - the result is a finished, non-interrupted attempt that lists the receipt and the exact custody-handoff entry, including the route id;
  - the claims record names the same attempt, receipt and body, and its claim fields match the supply.

  - the claims record passes the full `QUARRY_RETRIEVAL_CLAIMS_V001` schema, with a named-human field (assistant and placeholder names refused) and a timestamp with a UTC offset.

  A later reviewer can therefore inspect the exact claims record and the receipt evidence without the original Source Retrieval directory.

**Two kinds of verification**

| | At creation (`import_retrieved`) | Portable (every `load`, export and validation) |
|---|---|---|
| What runs | Source Retrieval's native verification of the attempt directory, plus byte equality with the retained records | Consistency of the retained receipt, result, claims, supply and original |
| What it establishes | The package's records are those of a verified native attempt on this machine | The records support each other and the supply; nothing about whether a native attempt existed |
| Needs | The Source Retrieval records base | Only the package |

**Procedural boundary and remaining misuse risk.** Within trusted Python this boundary prevents accidental bypass; it cannot prevent deliberate bypass:

- A fully self-consistent invented record set (correct hashes, matching result handoff and claims) passes the portable check. This is demonstrated by `test_final_invented_native_records_cannot_create_v002_custody`, which also shows that such a set cannot pass `import_retrieved`.
- Code that calls the private `evidence._import` directly, or that fabricates an entire native attempt directory (journal, receipts, inputs, snapshot) consistently, can still produce a package that loads.
- A V002 package received from elsewhere therefore shows consistency, not that native verification happened. Establishing that requires re-running verification against the original attempt directory, or trusting the machine and process that created it.
- No record authenticates a human's identity.
- **Package files are unchanged.** The package receipt (`QUARRY_RECEIPT_V001`), export, handoff (`QUARRY_HANDOFF_V001`), Jev input and validation are the same code paths. V002 provenance travels in `supply.json` and the export's `provenance.json`, and the transfer facts reach Jev through `limitations`. Jev's `availability` stays `SUPPLIED_COPY`, because the Jev contract has no retrieval value and was not changed.
- **Data classification.** `data_classification` comes from the human claims. V002 does not tie SYNTHETIC to the fixture kind, because receipts do not record whether a real or injected transport produced them (see open questions).

## `QUARRY_RETRIEVAL_CLAIMS_V001` (human record)

Written by a named human after inspecting the retained bytes; assistant and placeholder names are refused. Fields:

- **Binding:** `attested_by`, `attested_at` (with UTC offset), and the exact `attempt_id`, `receipt_sha256` and `body_sha256` it describes.
- **Claims:** `title`, `source_identity_claim`, `asset_claim`, `source_version_claim`, `historical_availability_claim`, `data_classification`, `limitations`, `missing_fields`.
- **Statement:** the fixed statement that these are claims, not verified facts.

UNKNOWN identity or asset claims are allowed. Quarry then flags them, and export stays blocked until the identity is reconciled, as for V001.

## The bridge

```powershell
python -m src.research.source_custody_v1 preflight <attempt-id> <exact-url>                                   # read-only
python -m src.research.source_custody_v1 import <attempt-id> <exact-url> --claims claims.json --out .research/quarry-v1-<name>
python -m src.research.source_custody_v1 status <receipt-sha256>                                               # read-only
python -m src.research.quarry_v1 export .research/quarry-v1-<name> inspection.json subject.json [--extracted-file text.txt] --out .research/quarry-v1-<handoff>
python -m src.research.quarry_v1 validate-export .research/quarry-v1-<handoff>
python -m src.research.jev_navigation_v1 prepare .research/quarry-v1-<handoff>/input.json --out .research/jev-navigation-v1-<name>
```

`--base` goes before the command and is the same records base as Source Retrieval's.

1. **Preflight** (read-only):
   - Source Retrieval's own `verify` must return a finished, anchored, non-interrupted result with status COMPLETE, PARTIAL, STOPPED or UNAVAILABLE.
   - The URL must have exactly one `custody_handoff` entry naming a verified target receipt; body path, size, hash and coverage must agree.
   - The attempt's input copies must match the owner scope and the request.
   - Exactly one approved Quarry route must have this locator, and it must be the handoff's route.
   - The body must still hash correctly.
2. **Claims:** validated and bound to that attempt, receipt and body.
3. **Supply:** `QUARRY_SUPPLY_V002` is built and validated by Quarry's contract.
4. **Stage and re-check:** the verified bytes (not a re-read of the source file), the registry copy and the supply are staged in a temporary directory, and the preflight is run again. Any change since the first preflight refuses with nothing imported.
5. **Claim and import:**
   - A create-only custody claim `<base>/source-custody-v1/receipts/<receipt>.json` is written.
   - Quarry's `import_retrieved` then creates the package with the retained native records; output directories are create-only.
   - Only after the package is sealed, a create-only completion record `<receipt>.completed.json` binds the exact claim bytes and the package manifest.
   - A receipt enters custody at most once: reusing it reports `REUSED_CUSTODY`, and reusing it with different claims `INCONSISTENT_DUPLICATE`. A claim without a confirmed package refuses any further import with `CUSTODY_INCOMPLETE`; it is never retried, replaced or removed by software.

`status <receipt>` is read-only:

| State | Meaning |
|---|---|
| `CUSTODY_COMPLETE` | The claim, its completion record and the sealed package all agree: attempt, receipt, URL, claims hash, supply hash and package |
| `CLAIM_WITHOUT_PACKAGE` | Interrupted after the claim, before Quarry created the package directory |
| `PACKAGE_INCOMPLETE` | Interrupted during package creation (Quarry PARTIAL_OR_INTERRUPTED) |
| `COMPLETION_MISSING` | A package exists but no completion record confirms it |
| `INCONSISTENT` | Any claim field, the completion record or the package differs |

| Refusal | When |
|---|---|
| `SOURCE_INCONSISTENT` | Native verification fails: altered result, receipt, body or journal |
| `SOURCE_NOT_FINISHED` | INTERRUPTED, PRECLAIM_INCOMPLETE or RESULT_PENDING |
| `SOURCE_NOT_ELIGIBLE` | NOT_STARTED, UNKNOWN, or a finalised interrupted attempt |
| `NOT_CUSTODY_ELIGIBLE` | robots.txt, error pages (401/403/404/5xx), 204/206, encoded or conflicting responses, or a URL the attempt did not retrieve |
| `RECEIPT_MISMATCH`, `BODY_MISMATCH` | Handoff and receipt disagree on receipt, path, size, hash or coverage |
| `SCOPE_MISMATCH`, `ROUTE_MISMATCH` | Input copies differ from the owner scope, or the URL does not map to one approved route |
| `CLAIMS_INVALID`, `CLAIMS_MISMATCH` | Malformed claims, an assistant or placeholder attester, or claims for another attempt, receipt or body |
| `SOURCE_CHANGED_AFTER_PREFLIGHT` | Source records changed between the two preflights |
| `OUTPUT_EXISTS`, `REUSED_CUSTODY`, `INCONSISTENT_DUPLICATE`, `CUSTODY_INCOMPLETE` | Create-only output, one custody per receipt, no retry of an unconfirmed claim |
| Direct `quarry_v1 import-file` of a V002 supply | Refused: V002 provenance is established only through the bridge |

## Jev handoff, proved on synthetic fixtures

`tests/test_source_custody_v1.py` runs a fictional attempt through the fake transport, then:

- creates custody from a fictional human's claims;
- exports with an exact-UTF-8 inspection record;
- validates the export;
- runs the existing Jev workspace `prepare`/`report`.

It checks that:

- **The bytes are unchanged:** the package's `original.bin` is byte-identical to the retrieved body.
- **Provenance reaches the export:** `provenance.json` carries the full `system_retrieval` binding.
- **Jev receives the limits:** the Jev document carries the original hash, the exact quote, `Coverage: COMPLETE_CLAIMED`, the receipt-bound transfer limitations and the missing fields.
- **Nothing is approved:** human inspection stays `PENDING_HUMAN_INSPECTION`.
- **Inputs are enforced:**
  - a binary (PDF-like) original refuses `ORIGINAL_UTF8` and needs an explicitly supplied extraction (`UNVERIFIED_AGAINST_ORIGINAL`);
  - wrong byte ranges are refused;
  - prefix and unframed transfers keep PARTIAL or UNKNOWN coverage with their warnings, and cannot be relabelled COMPLETE.
- **No new transport calls:** custody, export and Jev make none.

No new Jev engine, field interpretation, approval or Anvil decision is created.

## Operational consequences

- **Source Retrieval implementation hash changes.** The Quarry contract module is one of the files it binds, so any owner scope must bind the new hash; none exists yet.
- **Operator implementation drift.** The Research OS operator's implementation closure includes Quarry, so existing private operator runs will report implementation drift on `continue`. Only the owner may accept it.
- **Untouched:** campaign, Scout, operator rules, source search and Anvil code.

## Open contract questions

These are recorded in `docs/source_discovery_shared_interface_v001.md`:

- reservation identity;
- who schedules custody and writes claims;
- the search-candidate-to-route binding;
- which attempt statuses are eligible for custody;
- transport provenance for SYNTHETIC classification;
- caller authentication.
