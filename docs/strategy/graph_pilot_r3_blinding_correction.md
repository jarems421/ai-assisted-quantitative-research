# Graph pilot revision 3: blinding defect and corrected adjudication materials

**2026-10-21. The original (V001) adjudication presentations were compromised and have been disclosed to the owner. Corrected V2 presentations replace them for adjudication; the originals and their sealed keys are preserved unchanged.** Correcting the format cannot undo the owner's earlier exposure. The owner [reported the defect](owner_graph_pilot_r3_blinding_fix_2026-10-21.md) on reviewing the sheets.

## Defect

| Packet | What leaked | Mechanical scan of the committed V001 export |
|---|---|---|
| P3 | Arm G's self-chosen record ids carry its arm letter: `OBS-G-1`, `OBS-G-5` to `OBS-G-8`, `REL-G-1`, `REL-G-2` and `CAND-G-1`. They appear as endpoint ids and inside endpoint text (for example, references to `CAND-G-1`). | 47 findings in the JSON and 47 in the sheet (arm-letter and own-arm ids) |
| P4 | No arm letters, but the two arms used visibly different id styles: plain `OBS-1` to `OBS-7` against descriptive ids such as `OBS-MGA-SUBSIDIARIES` and `CAND-RECALL-REMEDY-CAMERA`. Items can be grouped by arm. | 29 own-arm ids in the JSON and 29 in the sheet |

## Cause

- **Export:** `pilot.blind` (V001) copied each endpoint's record id and free text verbatim from the arm ledgers, and arms choose their own ids.
- **My scan:** before publication I checked only campaign ids, pilot connection ids, attribution words and tool words. **I did not check record ids or embedded references.**
- **My claim:** the [status record](graph_pilot_r3_status.md) therefore wrongly stated that the scans found no leaks.
- **Arm instructions:** they forbade naming tools or arms in text, but did not constrain record ids.

## What is preserved, unchanged

| Artefact | SHA-256 |
|---|---|
| `graph_pilot_r3/P3/blind.json` (V001) | `6d28c55c…b6ba` |
| `graph_pilot_r3/P4/blind.json` (V001) | `13b80b6c…ec9b` |
| `adjudication_sheet.md` (both packets) | Unchanged; compromised |
| Sealed keys (private) | P3 `e9ab04ff…`, P4 `270f6da3…` |

The blind ids, the sealed blind-id → arm mappings and the `adjudications_TEMPLATE.jsonl` files stay valid. No arm ledger, connection log, freeze time, candidate or source record was changed. No key was unsealed and no arm branch was merged.

## Correction (versioned tooling)

- **New export version.** `GRAPH_PILOT_BLIND_V2_ALIASED`, written by `python -m src.research.graph pilot realias`, is derived from an unchanged V001 export:
  - **Own-arm record ids** become opaque per-item aliases, wherever they appear (endpoint ids, text, passages, locators). The kind prefix is kept, for example `OBS-A1b2c3d4e`. The same alias in two items does not imply the same record.
  - **Kept as they are:** frozen-packet references (`OBS-P-n`) and historical references (`HIST-…`).
  - **Neutral placeholders:** campaign ids, archive paths and branch names.
  - **Unchanged:** blind ids, item order, the key seal, evidence hashes and depths, values, dates, periods, entities and all other text. This was verified field by field.
  - **Private alias maps:** P3 `f143656d…`, P4 `9d811ee8…`.
- **Recursive leak scan.** `pilot leak-scan` walks every key and value of the full JSON, and the full text of sheets. It flags:
  - arm-letter record ids and own-arm record ids;
  - arm campaign ids, paths and branches;
  - arm labels, pilot connection ids, attribution and decision words, and tool words.

  `realias` refuses to write output that still leaks. Both V2 exports and sheets scan at **0 findings**; both V001 exports reproduce their findings.
- **Downstream support.** `pilot sheet` renders the readable sheet from an export. `pilot report --export blind_v2.json` and `unblind(..., 'blind_v2.json')` unblind through the original sealed key.
- **Tests.** Four new regression tests cover:
  - nested ids, embedded text references, candidate references, campaign ids, paths and branches;
  - the scan across keys, lists and markdown;
  - adjudication and unblinding through V2;
  - the committed artefacts.

  56 graph tests pass.
- **Scanner fix.** The scanner's record-id pattern initially absorbed a sentence's trailing full stop; this was fixed before any V2 artefact was committed or shown.

## Residual limitations (not removed)

- **Prior exposure.** The owner has read the V001 sheets. For P3 in particular, the arm of every item using a `-G-` id is now known to them. An adjudication by the owner is therefore **potentially unblinded**.
- **Remaining content cues.** Writing style, record granularity, evidence choices and the number of endpoints from the arm's own campaign may still suggest the arm.
- **Same person throughout.** The owner operates, adjudicates and later decides M/H.
- **Lost cross-item links.** Because aliases are per item, the adjudicator can no longer see that two items share an arm record. This was accepted to avoid creating new arm clusters.

## Separately flagged for later M/H review (sealed until adjudication)

The flags are mechanical and decide nothing. They are kept privately because they identify arms; private file `keys/mh_review_flags.json`, SHA-256 `a07e8c29…ce0b`. They list:
- records containing dates after the packet window (excluding retrieval clocks), such as dataset versions and later filings;
- candidate versions and their selection flags (`outcome_inspected_before_freeze`, `after_outcome_seen`, derived post-outcome status);
- effort descriptions that mention outcome-like information before a freeze.

**Per-packet counts (arms combined):**

| Flag | P3 | P4 |
|---|---:|---:|
| Records with post-window dates | 10 | 9 |
| Candidate versions | 5 | 9 |
| Candidate versions flagged outcome-before-freeze or post-outcome | 1 | 5 |
| Effort mentions to review | 8 | 8 |

Freeze times and candidate records are not altered, and this contamination is not dismissed. The M/H stage must weigh every flag.

## How to adjudicate now

1. **Use only** [P3 V2 sheet](graph_pilot_r3/P3/adjudication_sheet_v2.md) and [P4 V2 sheet](graph_pilot_r3/P4/adjudication_sheet_v2.md), or the matching `blind_v2.json`. Do not open the V001 sheets, arm branches, connection logs or private keys.
2. **Preferably** use an independent adjudicator who has never seen the V001 sheets or arm material. Give them only the V2 sheets, the cited public originals and these instructions.
3. **For every item**, fill in `adjudications_TEMPLATE.jsonl` (same blind ids) and save it as `adjudications.jsonl` in that packet folder. Per item, record:
   - **`outcome`:** `CONFIRMED_AGAINST_ORIGINALS` only after checking the cited original; list the checked sha256 values or locators in `checked_evidence`. Otherwise `PLAUSIBLE_UNVERIFIED` (the evidence falls short), `REJECTED_FALSE` or `REJECTED_TRIVIAL`. A shared identifier or hash alone never confirms a connection.
   - **`economic_meaning`:** `MEANINGFUL`, `NOT_MEANINGFUL` or `UNCLEAR`.
   - **Who and when:** `adjudicator` (a real name), `adjudicator_kind` `HUMAN`, `recorded_at_utc` and `adjudicator_minutes`, or `UNKNOWN`.
   - **`notes`:** must begin `EXPOSURE: SAW_V001=YES` or `EXPOSURE: SAW_V001=NO`.
4. **Commit the two logs.** Only then will the coordinator:
   - validate them against `blind_v2.json`;
   - unseal the keys;
   - present M/H materials with the sealed flags;
   - run the descriptive report.

**Interpretation rules:** if any adjudication carries `SAW_V001=YES`, the P3/P4 graph comparison is reported as **potentially unblinded**. With only two pairs, it is descriptive in any case.
