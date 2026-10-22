# Graph Pilot R4: independent reviewer guide (version 001)

> **DRAFT FOR OWNER REGISTRATION — NOT ACTIVE.** This guide becomes binding only if the R4 activation document names it by hash. R4 is NOT_RUN.

**Purpose.** You are one of two independent human reviewers, R1 or R2. Your job is to **assess evidence**. It is not to reward unusual ideas, and it is not to prove that any research method is useful. You will judge blinded items, each a proposed link between two records, against the original documents they cite. You never learn which research arm produced an item until both reviewers have sealed their judgments.

**Who should not use this guide.** Anyone who operated an arm, attested an arm session, prepared the blinding, saw the blinding key, or saw the other reviewer's judgments. If that is you, stop: you are not independent for that packet.

All examples below are **fictional training cases**. They name no real company, product, regulator or document.

---

## 1. What you receive and what you may see

**You receive, for each packet, a reviewer bundle containing:**

- `blind_v2.json` (the aliased, leak-scanned export) and its readable sheet;
- an **evidence pack**: copies of the cited original documents, named by their `sha256`;
- the frozen packet ledger and snapshot, which you need only so the sealing command can run;
- this guide.

**Before you seal, you may NOT see:**

- the arm ledgers (`S.jsonl`, `G.jsonl`) or connection logs (`connections-*.jsonl`);
- suggestion exports (`suggestions-G/`), session attestation files, `blind.json` (V001), `key.json` or alias keys;
- the other reviewer's logs, notes or conversation;
- any AI-generated assessment of these items;
- any report or summary.

If you see any of these, even accidentally, **declare it** (section 6). Never hide it.

**Do not fetch sources yourself** unless the activation document explicitly authorises reviewer retrieval. If an original you need is missing from the evidence pack, record that the evidence is insufficient (section 4). Do not look it up.

**What an item looks like.** Each item has:

| Field | Meaning |
|---|---|
| `blind_id` | The item's identifier (`ADJ-…`). Copy it exactly |
| `kind` | `CONNECTION` (judge economically) or `METHODOLOGICAL_WARNING` / `AVOIDED_REPEAT` (judge usefulness) |
| `from`, `to` | The two endpoints. Each has `kind` (observation, relationship, candidate claim, source, or a historical investigation, claim or finding), `text`, `entities` (identifier and name), `evidence` (`locator`, `sha256`, `depth`), and, where relevant, `value`/`units`/`occurred` or `type`/`period`/`status` |
| `shared_structure` | A mechanical comparison: same identified entity, shared document hashes, shared requirement tags, name- or ticker-only entities, and whether a relationship's period covers the observation date (`YES`/`NO`/`UNRESOLVED`) |
| `avoided_action` | Only on `AVOIDED_REPEAT` items: the action the earlier lesson is said to have avoided |

Record identifiers inside items are aliases (`OBS-A3f…`). The label `CURRENT_ARM_CAMPAIGN` appears for both arms, so it tells you nothing about which arm produced the item.

---

## 2. Economic items (`kind: CONNECTION`): the four outcomes

Use exactly these labels; the validator refuses any other. There is no `UNKNOWN` outcome: insufficient evidence is `PLAUSIBLE_UNVERIFIED`.

| `outcome` | Use when | Must also do |
|---|---|---|
| `CONFIRMED_AGAINST_ORIGINALS` | You opened the cited originals, and they establish both endpoints' facts as recorded **and** the joining basis: the same identified entity, the same document, or a documented relationship covering the date | List in `checked_evidence` the `sha256` values or locators **from this item** that you checked; at least one is required |
| `PLAUSIBLE_UNVERIFIED` | The link may be real, but the originals you have do not establish it: a missing document, an unidentified entity, an unknown period, or a quantity whose definition you cannot confirm | Say in `notes` what is missing |
| `REJECTED_FALSE` | The originals contradict the link: a different entity, a period that does not cover the date, a misread value or unit, or a document that does not say what is claimed | Say in `notes` what contradicts it |
| `REJECTED_TRIVIAL` | The link is true but carries no economic information. Examples: two records sharing only a regulator, exchange or region; only a shared requirement tag; the same document restated as if it were new; boilerplate | Say in `notes` why it is uninformative |

**Then judge `economic_meaning`:** `MEANINGFUL`, `NOT_MEANINGFUL` or `UNCLEAR`. The question is the one printed in the export: *does the connection link an observed quantity or documented relationship to a listed company's documented exposure, or to a claim's required measurement?*

**Only `CONFIRMED_AGAINST_ORIGINALS` together with `MEANINGFUL` from BOTH reviewers counts as a verified economic connection.**

### How to assess the evidence

1. **Original documents.** Prefer the publisher's own record (`depth` such as `VERIFIED_ORIGINAL_FIELD` or `VERIFIED_ORIGINAL_RECORD`). A press summary, aggregator or later restatement does not establish a fact. A `SOURCE_PASSPORT` or `REPORT_QUOTE` depth describes where a fact came from; it is not the fact.
2. **Entities.** A shared registry identifier (a product code, facility identifier or legal-entity identifier) can join records. **A matching name never establishes identity.** `shared_structure.name_or_ticker_only_entities` flags names and tickers. Two firms both called "Northfield Components" are not thereby the same firm.
3. **Relationships.** A relationship must be **documented** by an original that states it, such as a contract, a registry parent link or a licence, and must **cover the date** of the observation. If `relationship_period_covers_observation` is `NO`, the link is `REJECTED_FALSE` unless the originals show otherwise. If it is `UNRESOLVED`, the link is at most `PLAUSIBLE_UNVERIFIED`.
4. **Dates.** Keep four clocks apart: when the economic event happened, the source version date, when it was first public, and when it was retrieved. A first-public time is unknown unless an original publication record proves it. Do not infer it from a document's date.
5. **Economic transmission.** No connection, however well documented, shows that a quantity reached a company's earnings, cash or valuation. A `MEANINGFUL` connection reaches a documented exposure or a required measurement. It never proves the financial effect. Treat any claimed effect as a mechanism to be tested, not a confirmed fact.
6. **Missing evidence.** Absence is not evidence of absence. A missing allocation, unknown counterparty share or unrecorded period keeps the link at `PLAUSIBLE_UNVERIFIED` at most.

### Verified source fact versus speculative mechanism

| Statement in an item | Status |
|---|---|
| "Registry record R-7 shows the facility's capacity is 40 units per week" (and the original shows it) | Verified source fact |
| "The facility is owned by Larchmont Holdings" (a registry parent record shows it, covering the date) | Verified relationship |
| "So a capacity cut will lower Larchmont's quarterly revenue" | Speculative mechanism. Never confirmed by a connection |

---

## 3. Usefulness items (`kind: METHODOLOGICAL_WARNING` or `AVOIDED_REPEAT`)

These are **not** economic discoveries. Never judge them in the economic log; the validator refuses that. Use exactly these labels:

| `usefulness` | Use when | Must also do |
|---|---|---|
| `USEFUL_LESSON_REUSED` | The item itself shows that a specific earlier lesson changed or avoided a stated action, and the cited lesson evidence supports applying it here. For an `AVOIDED_REPEAT` item the action is in `avoided_action`. A plain `METHODOLOGICAL_WARNING` item rarely shows this, because it records only the two linked records | Write the action in `avoided_action`, and list the lesson's evidence (`sha256` or locator from this item) in `checked_evidence` |
| `USEFUL_NOT_USED` | The lesson is relevant and correctly applies to this situation, but nothing in the item shows it changed anything | `avoided_action` may be null |
| `NOT_USEFUL` | The lesson is irrelevant, generic, wrong or misapplied. For example, a capacity lesson from an unrelated industry attached only by a shared tag | Explain in `notes` |
| `CANNOT_ASSESS` | You cannot open the lesson's evidence, or the item is too incomplete to judge | Explain in `notes` |

A useful warning helps a researcher avoid repeating a known mistake. That is a different benefit from discovering a new economic connection, and the two are reported separately.

---

## 4. Recording UNKNOWN, insufficient evidence, disagreement and zero items

- **Insufficient evidence:**
  - economic items: `PLAUSIBLE_UNVERIFIED` with `UNCLEAR` meaning;
  - usefulness items: `CANNOT_ASSESS`.
  - Never guess upward.
- **Your time:** record `adjudicator_minutes` as a number from your own clock. If you did not time an item, write `"UNKNOWN"`, never 0. Unknown time makes the review-cost total UNKNOWN, which is the correct outcome.
- **Disagreement:** you never see the other reviewer's judgments, so you never resolve a disagreement. An outcome counts only where both reviewers agree. Any mismatch stays `UNRESOLVED_DISAGREEMENT`, with no arbitration by an AI, an operator or a third reading.
- **Zero-item packets:** a packet can legitimately have no items. Then both of your log files must exist **and be empty** (0 bytes). Do not write a placeholder row. Seal them with your reviewer-level exposure declaration as usual.

---

## 5. Completing your two logs

Write one JSON object per line. Use exactly these fields; the sealing command validates them and refuses any error. Replace `R1` with your slot, and use your own name throughout, the same in every row.

**Economic log: `adjudications-R1.jsonl`** (one row per `CONNECTION` item, every one of them)

```json
{"blind_id": "ADJ-0123456789", "outcome": "CONFIRMED_AGAINST_ORIGINALS", "economic_meaning": "MEANINGFUL",
 "checked_evidence": ["<sha256 from this item>"], "adjudicator": "<your name>", "adjudicator_kind": "HUMAN",
 "adjudicator_minutes": 6, "recorded_at_utc": "2026-11-03T10:15:00+00:00", "notes": "Registry parent record covers the observation date.",
 "log_version": "GRAPH_PILOT_ADJUDICATION_V2", "reviewer": "R1",
 "exposure": {"saw_arm_info": "NO", "seen": [], "operated_or_attested_arm": "NO", "note": ""}}
```

**Usefulness log: `warning-usefulness-R1.jsonl`** (one row per `METHODOLOGICAL_WARNING` and `AVOIDED_REPEAT` item)

```json
{"blind_id": "ADJ-9876543210", "usefulness": "USEFUL_NOT_USED", "avoided_action": null, "checked_evidence": [],
 "adjudicator": "<your name>", "adjudicator_kind": "HUMAN", "adjudicator_minutes": 3, "recorded_at_utc": "2026-11-03T10:40:00+00:00",
 "notes": "Lesson applies; no sign it changed the work.", "log_version": "GRAPH_PILOT_WARNING_USEFULNESS_V1", "reviewer": "R1",
 "exposure": {"saw_arm_info": "NO", "seen": [], "operated_or_attested_arm": "NO", "note": ""}}
```

**Rules:**

- Cover every item of the right kind, once each.
- Use real UTC times.
- `checked_evidence` may only contain hashes or locators that appear in that item.
- `seen` is a sorted list without duplicates (section 6).

---

## 6. Exposure declarations and independence

Every row carries `exposure`, and your seal carries a reviewer-level one covering your whole review:

| Field | Values | Rule |
|---|---|---|
| `saw_arm_info` | `YES` / `NO` | `YES` exactly when `seen` lists any arm-identifying item |
| `seen` | Any of: `ARM_LEDGER`, `CONNECTION_LOG`, `ARM_SESSION`, `BLINDING_KEY`, `ALIAS_KEY`, `SUGGESTION_EXPORT`, `V001_EXPORT`, `OTHER_ADJUDICATION`, `AI_ASSESSMENT`, `OTHER` | List everything you saw before judging |
| `operated_or_attested_arm` | `YES` / `NO` | `YES` if you ran or attested any arm session of this packet |
| `note` | Text, which may be empty | What you saw and when |

**What each declaration does:**

- **Arm-identifying material:** if you saw any of the first seven (ledgers, connection logs, sessions, keys, alias keys, suggestion exports, V001 export), the item is labelled **POTENTIALLY_UNBLINDED**. It stays in the analysis, labelled, and a sensitivity analysis checks whether excluding such packets changes the result.
- **The other reviewer's judgments, or an AI assessment:** the item is **NOT_INDEPENDENT**, and the packet leaves the primary comparison.
- **Arm operation or attestation:** if you operated or attested an arm, or your name matches a session attester, you are **CONFLICTED**, and the packet leaves the primary comparison.

Honest declaration costs you nothing; concealment invalidates the study.

---

## 7. Sealing your logs independently

When both logs are complete, seal them yourself in your own checkout of the pinned code:

```text
python -m src.research.graph pilot adjudication-seal <reviewer-bundle-dir> --reviewer R1 --by "<your name>" \
    --saw-arm-info NO --operated-or-attested-arm NO [--seen ...] [--note "..."]
```

**What the command does:**

- validates both logs and refuses on any error, with nothing written;
- writes an immutable `adjudication-seal-R1.json` holding the hashes of both logs, the export hash, your declaration and an independence statement.

A second seal is refused. Editing a log after sealing invalidates it.

**Hand-over order.** Send the operator **only your seal file first**. Keep your logs private until the operator confirms that both reviewers' seals are committed. Then hand over your logs, byte for byte unchanged. Each log must first appear in a commit strictly after the other reviewer's seal, and its committed bytes must be exactly the sealed bytes; otherwise the packet's reveal order is VIOLATED.

---

## 8. Training examples (fictional)

| # | Item | Decision and why |
|---|---|---|
| 1 | **Positive.** An observation records "Kiln K-14 output 3,200 t, March". The original registry row shows facility identifier `FAC:K14`. A relationship record, backed by a registry parent filing, says Brennor Cement plc operates `FAC:K14` from 2023 to OPEN. Period covers: YES | `CONFIRMED_AGAINST_ORIGINALS`, `MEANINGFUL`. The identified facility is linked by a documented, period-covering relationship to a listed company's exposure. Revenue effect: not established |
| 2 | **Negative, trivial.** Two observations both concern `REG:Northern Safety Board`: one is a fine on a bakery, one an inspection count for shipyards | `REJECTED_TRIVIAL`, `NOT_MEANINGFUL`. A shared regulator carries no economic link |
| 3 | **Negative, false.** A supplier relationship "Coldwater Valves supplied the pump line, 2015–2017" is linked to a 2026 recall | `REJECTED_FALSE`. The period does not cover the event (`relationship_period_covers_observation: NO`) |
| 4 | **Negative, identity.** "Harbour Metals" in a recall letter is linked to listed "Harbour Metals Group". The entities are name-only | `PLAUSIBLE_UNVERIFIED` at most, with `UNCLEAR` meaning. Name similarity is not identity |
| 5 | **Ambiguous.** Same product code `SKU:7781` in a recall and in a supplier filing, but the filing's evidence is missing from your evidence pack | `PLAUSIBLE_UNVERIFIED`, `UNCLEAR`, with the note "supplier filing not in evidence pack". Do not fetch it |
| 6 | **Ambiguous.** Two records cite the same document hash; one restates the other | If it is the same record restated: `REJECTED_TRIVIAL`. If two independent uses of one document: possibly `CONFIRMED_AGAINST_ORIGINALS`, noting that it is one document, not independent corroboration |
| 7 | **Usefulness, positive.** `AVOIDED_REPEAT` with `avoided_action: "did not request vessel tracks again"`, citing an earlier finding that tracks did not establish treatment work | `USEFUL_LESSON_REUSED`, with the avoided action written and the finding's evidence listed |
| 8 | **Usefulness, negative.** `METHODOLOGICAL_WARNING` linking a device recall to an aquaculture capacity lesson by a shared capacity tag only | `NOT_USEFUL`. The lesson does not apply to this situation |
| 9 | **Zero items.** The export has no items | Two empty log files, then seal. No rows |
