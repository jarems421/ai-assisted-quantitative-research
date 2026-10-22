# Graph Pilot R4 activation (TEMPLATE, version 001)

> # DRAFT — NOT ACTIVE — NO EXPERIMENTAL AUTHORITY.
> This is a template for the owner to complete. It authorises nothing in this form. To activate R4, the owner completes **every** `⟨OWNER: …⟩` field, removes this banner, and commits the result as `docs/strategy/owner_graph_pilot_r4_<YYYY-MM-DD>.md` to `main` before any source request. Every rule below marked **PROPOSED** takes effect only through that registration. The per-campaign figures are proposals, not standing authorisations.

## 1. Authority and scope

- **Authority.** This document, when completed and committed: `⟨OWNER: commit SHA once committed⟩`.
- **Question.** The R4 Q2 paired descriptive comparison ([protocol](graph_pilot_r4_protocol_proposed.md)): within the same fresh packet, does adding Graph to Discovery Lab plus competent structured-ledger search improve research, counting all the analyst time the graph costs?
- **Two separate benefits.**
  - **(a) Economic discovery:** connections confirmed and meaningful under the consensus rule.
  - **(b) Avoided repetition:** warning and avoided-repeat usefulness.

  These are never pooled.
- **Excluded:** prices, returns, backtests and investment-performance claims. M and H are research-quality outcomes only. With four packets the result is descriptive only: no p-values.

## 2. Exact pins

| Item | Pin |
|---|---|
| Code (merged `main`) | `9ac56d33e6b3a7e97dfc3c56faf0e91ef0edeb92`, or ⟨OWNER: a later commit with identical pinned content⟩ |
| Implementation pin version | `GRAPH_IMPLEMENTATION_PIN_V002` (boundary: the static import closure of graph, discovery, `spec.py` and `fetch_one.py`; 38 files at `9ac56d3`) |
| Implementation content digest at `9ac56d3` | `e33093b5809b1a6ea3a1e8cd5eeda03146eec3b874b0f00be525dc85bf78e8da`, informative. Each snapshot records the actual pin |
| Runtime | ⟨OWNER: Python version, implementation and the package list of the frozen R4 environment, captured at Stage 1⟩. Do not copy a developer machine's runtime |
| Graph configuration | [`graph_pilot_r4_graph_configuration_v002.json`](graph_pilot_r4_graph_configuration_v002.json), sha256 `fc2d7d9c5a7670a731c814f44386f0dc474345b79ba9766b84c6f4b633013a50`: `GRAPH_OPERATORS_V1_1` + `GRAPH_CLASSIFICATION_V1_2` + generic register V001 |
| Generic register | [`generic_identifiers_v001.json`](graph/generic_identifiers_v001.json), sha256 `39dd7026b03d5db83c191e1ae56b55c2eab27eb7e3322c6082422b7923915b04`. Its `recorded_at_utc` is known to be unreliable ([corrections](graph_timestamp_corrections_2026-10-22.json)) |
| Historical catalogue | `research_memory_catalogue_v002.json`, sha256 `afd91e54697f7e47e8844f4076267bae95814cbd12e29e4ec9f97ba9f9a589a9` |
| Fetch tool | `docs/strategy/graph_pilot/fetch_one.py`, sha256 `3e51a00081b5db3ea4c702b0bbfd6117e1339ff70df0d1801aa54c35a958eb1a` |
| Connection log | `GRAPH_PILOT_CONNECTION_V2` (every packet frozen with `--connection-log GRAPH_PILOT_CONNECTION_V2`) |
| Operational documents | [reviewer guide v001](graph_pilot_r4_reviewer_guide_v001.md), [runbook v001](graph_pilot_r4_runbook_v001.md) and [source plan v001](graph_pilot_r4_source_plan_v001.md): ⟨OWNER: sha256 of each at registration⟩ |

## 3. People

| Role | Person | Independence confirmation |
|---|---|---|
| Research owner | ⟨OWNER⟩ | — |
| Arm operator(s) | ⟨OWNER: name(s)⟩ | Operators never review a packet they operated |
| Arm analyst type | ⟨OWNER: decision D1, below⟩ | The same type for both arms of every packet |
| Blinding preparer | ⟨OWNER: name; never a reviewer⟩ | — |
| Reviewer R1 | ⟨OWNER: name⟩ | ⟨OWNER: confirmed no arm operation or attestation, no prior contact about R4 items⟩ |
| Reviewer R2 | ⟨OWNER: name, a different person from R1⟩ | ⟨OWNER: as above⟩ |
| Technical assistant | ⟨OWNER: permitted? what scope?⟩ | Never writes or seals judgments, attestations or decisions |

## 4. Sources and packets

- **Packet window:** ⟨OWNER: the most recent complete calendar quarter ending at least 12 months before activation⟩.
- **Freshness rule:** ⟨OWNER: decision F1: strict host-level, or record, filing-set and exact-route level with an overlap audit⟩.
- **Reserve depth:** ⟨OWNER: decision F2: two or three environments per method; the packet-freeze start ceiling to match⟩.
- **Overlap audit:** ⟨OWNER: confirmation that the operator completed the private-receipt overlap audit (source plan F4)⟩.

| Packet | Method | Ordered environments and exact probe routes (with limit parameter) | E2 terms confirmation |
|---|---|---|---|
| P1 | Observation-first | ⟨OWNER: from source plan O-1, O-2, O-3, amended⟩ | ⟨OWNER⟩ |
| P2 | Relationship-first | ⟨OWNER: from R-1, R-2, R-3, as allowed by F1⟩ | ⟨OWNER⟩ |
| P3 | Event-first | ⟨OWNER: from E-1, E-2, E-3⟩ | ⟨OWNER⟩ |
| P4 | Hypothesis-first | ⟨OWNER: the new mechanism statement, text committed here; not R3 P4's or any catalogued mechanism⟩ | n/a |

**Arm order:** P1 S then G; P2 G then S; P3 S then G; P4 G then S. One session per campaign.

**Stopped routes:** every persisted Research OS stop, plus ⟨OWNER: any additions⟩.

## 5. Schedule

⟨OWNER: dates for environment freeze, preflight, each arm session, blinding, review window, reveal and report. Leave enough time for the review window: both reviewers must seal before either log is revealed.⟩

## 6. Ceilings (PROPOSED; not standing authorisations)

| Ceiling | Proposed | Owner value |
|---|---|---|
| Per campaign: analyst minutes / source starts / searches / response bytes | 120 / 6 / 10 / 8 MiB | ⟨OWNER⟩ |
| Packet freeze: starts per method; bytes per probe | 2 (or 3, under F2) / 4 MiB | ⟨OWNER⟩ |
| Cumulative pilot: minutes / starts / searches / bytes (counted separately from R1–R3; includes packet freeze) | ⟨OWNER⟩ | ⟨OWNER⟩ |

## 7. Stopping rules

- **Campaign stop:** at the minute ceiling or any ceiling, or when every candidate is frozen or abandoned with a recorded reason.
- **Route stop:** any denial, timeout or oversized response, with no retry or bypass.
- **Critical stop:** see the [runbook](graph_pilot_r4_runbook_v001.md#3-stops-incomplete-packets-and-preserved-failures). Halt and report; delete nothing.
- **Packets that fail to form:** NOT_FORMED packets and incomplete campaigns are preserved and reported. No replacement packet, budget expansion or post-hoc substitute.

## 8. Review and analysis policy (PROPOSED, for registration)

- **Two independent human reviewers**, R1 and R2. Both are required for a packet to conform: the merged code requires two valid seals. This supersedes the protocol draft's earlier wording that "at least one" adjudicator was required and two preferred.
- **Consensus rule:** only matching independent reviewer judgments establish an outcome. Any disagreement stays `UNRESOLVED_DISAGREEMENT`. There is no AI, operator or third-reviewer arbitration. ⟨OWNER: register or amend⟩
- **Blinding treatment:**
  - potentially unblinded packets stay labelled in the primary comparison;
  - a packet-exclusion sensitivity runs alongside;
  - if the two classifications differ, no definitive classification is reported.

  ⟨OWNER: register or amend⟩
- **Primary measure:** self-reported analyst minutes, with attested-session minutes as a sensitivity. A definitive classification needs supporting effort evidence. A material discrepancy is one above the greater of 5 minutes or 10% of the derived comparator.
- **Conformance:** a packet enters the primary comparison only if all of these hold:
  - `r4_configuration.conforms: true`;
  - two valid seals;
  - no CONFLICTED or NOT_INDEPENDENT item or reviewer;
  - reveal order VERIFIED.

  Non-conforming packets are listed with their reasons. Owner deviation records are preserved and never re-admit a packet.
- **Minimum:** at least three comparable conforming pairs for a definitive descriptive classification; otherwise INCONCLUSIVE.
- **After unsealing:** M/H reviews and dispositions under the original [Measurement Gate M](measurement_gate_m.md).
- **Separately reported:** review burden (all items reviewed, including discarded suggestions) and warning usefulness.
- **Open item:** ⟨OWNER: decision U1. Can a plain `METHODOLOGICAL_WARNING` item ever be scored `USEFUL_LESSON_REUSED`? The blinded item records no arm action, so the reviewer guide limits this to items that themselves document the avoided action.⟩

## 9. Activation checklist (all must be true before the first request)

- [ ] Every ⟨OWNER⟩ field above completed; the banner removed; committed to `main` as `owner_graph_pilot_r4_<date>.md`.
- [ ] Decisions D1, F1, F2 and U1 recorded.
- [ ] Two named reviewers confirmed independent and briefed with the reviewer guide.
- [ ] The frozen environment created; its runtime recorded; the offline self-tests passed (runbook Stage 1).
- [ ] The private-receipt overlap audit completed.
- [ ] Publisher terms confirmed for every registered environment (E2).
