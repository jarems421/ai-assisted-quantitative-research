# The Quarry V001

2026-10-25. Offline infrastructure only. No source acquisition, research provider call,
spend, campaign, Discovery append, scientific certification or activation is authorised.

The Quarry preserves explicitly supplied local copies and produces portable inspection
packages. The package's byte hash establishes consistency with a retained copy. It does
not authenticate the publisher, its date, source completeness or a human identity.

## Audit of main and reuse

Audited main: `78d3f7c0e1cc5feaec177e74b109ea0c384ed81c` (PRs #33/#34 merged).
Code and focused tests, rather than README claims, establish the following boundary:

| Existing component | Reused capability / boundary |
| --- | --- |
| `jev_navigation_v1/{contracts,navigation,workspace,evaluation}.py`, `test_jev_navigation_v1.py` | Three tasks, strict supplied artifacts, exact citations, pinned policy, Choice validation, deterministic ranking and budget diagnostics. Quarry emits its existing Evidence Prospector input without editing it. |
| `discovery/{records,ledger,review}.py`, Discovery tests | Source Passport vocabulary, replay, M checklist and V002 admission. Quarry's passport is an inspection worksheet, not a valid appended source/observation/review or M approval. |
| `graph/{catalogue,project,operators}.py`, Graph tests | Existing Armoury retrieval and grounded classifications remain authoritative within their derived-view limits. No new graph or catalogue is built. |
| `sec_pilot/{acquisition,parsing,provenance}.py`, source/reconciliation tests | Existing accession-specific originals and parsers separate byte custody, observed facts and historical availability. Its transport reads source identity/has source-specific allowlists: unsuitable for general reuse or activation here. No original archive is touched. |
| `source_first.py` | Fixed historical surfaces, shared quotas and persisted stops. It is a historical campaign, not an acquisition allowance for Quarry. |
| `opportunity_scout/n1_collector/{evidence,binding,collector}.py` | Prior art for exclusive claims and retained interrupted captures. N1 remains frozen; importing its provider/process machinery would couple unrelated closures. Quarry uses small local-file primitives only. |
| `study_readiness_v1/{gate,approval}.py` and readiness/signature tests | Actual exact-study inspection and independent trust/signature gate. Quarry cannot supply the ledger, study, signed judgments or trust needed for readiness. Human inspection stays PENDING. |

Missing capabilities were reusable supplied-file custody, portable raw/excerpt handoffs
and proposed route metadata. The provider integration belongs in the stacked Jev PR.
Historical Scout top-level files, N1, Graph, Discovery, source-first, Level A and Forge
provider validator/reporting are unchanged. Existing closed procurement/FDA/merger,
source-first surface stops, measurement-campaign stops, F19 HOLD, SH09 STOP and R4
pause remain recorded decisions; a new route record cannot reopen any of them.

## Operator flow

Use an explicitly selected local file. Never use account directories, credentials,
network shares or private archives merely because they are accessible on this machine.
The executable fixture creates complete examples of all JSON contracts:

```powershell
python -m src.research.quarry_v1 demo --out .research/quarry-v1-demo
python -m src.research.quarry_v1 import-file registry.json supply.json --file original.pdf --out .research/quarry-v1-import
python -m src.research.quarry_v1 status .research/quarry-v1-import
python -m src.research.quarry_v1 export .research/quarry-v1-import inspection.json subject.json --extracted-file supplied-text.txt --out .research/quarry-v1-handoff
python -m src.research.quarry_v1 validate-export .research/quarry-v1-handoff
python -m src.research.jev_navigation_v1 prepare .research/quarry-v1-handoff/input.json --out .research/jev-navigation-v1-quarry
```

For UTF-8 originals, use inspection mode `ORIGINAL_UTF8` and omit `--extracted-file`.
Each excerpt supplies its exact UTF-8 start/end byte offsets, quote and source location.
For binary formats, retain the original and supply a separately selected text extraction
with `SUPPLIED_EXTRACTION`, extraction method and page/table/location claims. Byte
ranges are verified against that text; its relationship to a PDF page remains a supplied
claim for human inspection. There is no silent PDF parser, OCR, model or measurement
extraction. Individual originals are limited to 16 MiB; Jev text to 4 MiB; existing
32-record/256-KiB Jev limits also apply. Nothing is truncated.

System-retrieved originals use `QUARRY_SUPPLY_V002` through Source Custody V001
(`docs/source_custody_v001.md`); V001 supplies are validated unchanged.

`registry.json` uses `QUARRY_ROUTE_REGISTRY_V001`; `supply.json` uses
`QUARRY_SUPPLY_V001`. All fields in `quarry_v1/contracts.py` are required; put UNKNOWN
in an unknown textual claim. Each proposed route records stable ID/version, exact
locator, publisher, expected fields, question, expected source/asset, originality claim,
restrictions, availability uncertainty and retained cited stops. A registry entry is
never evidence of successful retrieval. Import records source-version/retrieval claims,
classification, coverage, missing fields and limitations alongside the original bytes.

Wrong declared source/asset or expected-original-hash mismatches are retained as flags
and block export. Unknown identity also blocks export. Matching declarations cannot
detect a falsely attributed original: identity is not independently certified. Different
assets within a document remain visible for relevance assessment and human inspection.

## Storage and inspection

Every import/export directory and file is create-only. A claim precedes reading/writing
the original; no final manifest means PARTIAL_OR_INTERRUPTED and unusable evidence.
Do not overwrite, resume, repair or retry inside that directory. Keep failure/partial
bytes. A separate explicitly selected import may record a new supplied copy. File
flush/fsync is used; Windows directory durability is not a power-loss guarantee.

Load validates hashes and re-derives receipts. Export copies the entire source package,
separates original bytes from text/excerpts and reproduces the existing Jev input. It
retains source versions, exact quote/range, original/text hashes, access restrictions,
coverage, missing fields and stops. Validation also reconstructs the exact document
records, preventing removal of restrictions through an edited navigation input alone.
Hashes are not signatures or a defence against coordinated replacement of every file
and manifest. The local filesystem must be controlled by the owner. Symlink/junction,
credential/internal paths, relative-reference escapes and network shares are refused;
these checks are not a hostile concurrent filesystem sandbox.

`human-inspection.json` is mechanically validated as pending and includes a Source
Passport worksheet plus a prospective Anvil handoff. It never fabricates Discovery
source verification, observations, M/H, owner dispositions or signed judgments. A
human must separately assemble the exact study and use the existing readiness gate
with V002-admitted reviews and independently controlled trust. No readiness is claimed.

UNAVAILABLE imports deliberately omit original bytes and retain their negative metadata.
They can yield an explicit negative inspection record, never a measurement. A stopped
route can have an already supplied copy inspected, while retaining STOPPED in Jev.
Unavailable evidence never means a false economic hypothesis.

Status keeps the legacy `usable` boolean as an identity-flags check, explicitly labelled
`LEGACY_IDENTITY_CHECK_ONLY_NOT_ACCESS_PERMISSION`. Use `inspection_usable` for a retained
copy eligible for a cited handoff, and `negative_record_inspectable` for unavailable-source
metadata. A stopped retained copy can have `inspection_usable: true`; `acquisition_permitted`
is always false. Restrictions/stops are shown separately; historical stops are not reconciled.

New human handoffs are `QUARRY_HUMAN_INSPECTION_V002`. The prominent `evidence_inspection`
section includes original/text hashes, extraction mode/method and exact page/table/location
claims, coverage/missing fields, restrictions, and UNKNOWN authenticity/availability.
`SUPPLIED_EXTRACTION` is explicitly UNVERIFIED_AGAINST_ORIGINAL. Exact offsets only verify
the supplied text: they do not verify a PDF extraction or measurement. Historical V001
handoffs remain byte-preserved and loadable, without retroactively adding assurances.

## Future acquisition boundary

`plan-acquisition registry.json scope.json` performs local scope checks only. There is
**no acquisition dispatcher or activation command** in V001. Scope requires exact route
IDs, URLs, public HTTPS hosts, request/total/per-response byte ceilings, minimum serial
interval and timeout. Stops, restricted access, expanded URLs, IP literals, private/local
hostnames, credentials, ports and redirects are not admitted. No DNS request occurs.

The emitted design lists the controls a future reviewed transport must implement:
independent reconciliation of all persisted route/host stops (unclear means host-level),
owner approval binding exact hashes and terms, global pre-dispatch reservations,
destination-pinned public DNS/address checks, no proxies, bounded streamed capture,
preserved outcomes, no retry/fallback/resume and a whole-scope stop on uncertainty.
This design is intentionally non-executable; exact owner scope alone cannot enable it.
Historical reconciliation is **not performed** by this planner. A future activation needs
explicit inspection of Discovery ledgers, prior source/campaign decisions and private stop
receipts outside the new registry. Host-wide and unclear-scope stops apply to equivalent
routes: assigning a new route ID or URL cannot bypass an earlier denial. Preserve the
reconciliation evidence and obtain separate owner scope before any future dispatch.
No crawler, discovery expansion, login, CAPTCHA/paywall bypass or alternate denied
route exists. Existing source acquisition implementations are not invoked.

## Verification and limits

`tests/test_quarry_v1.py` is registered in the restricted offline inventory. Synthetic
tests cover custody and byte preservation, tampering, wrong source/asset/hash, partial
and unavailable imports, extraction separation, path/bounds refusal, stop retention,
exact Jev handoff and the full scripted offline ordering. The demo prioritises the F1
passage over an F2 decoy and leaves ambiguous evidence visible. It makes zero external
requests and leaves human inspection pending. Scripted choices demonstrate plumbing,
not Jev performance; independent labels and separately authorised provider evaluation
are still required under the existing navigation evaluation protocol.
