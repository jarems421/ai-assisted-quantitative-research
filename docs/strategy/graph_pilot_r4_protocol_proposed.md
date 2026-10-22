# Graph Pilot R4: proposed prospective protocol (draft)

> **STATUS: NOT_RUN. PROPOSED DRAFT, NOT ACTIVE.** Nothing here authorises a source request, packet, campaign, adjudication or any research step. It becomes binding only if the owner writes a separate activation (`owner_graph_pilot_r4_<date>.md`) naming the exact text, and that text is committed before any request.

Drafted 2026-10-22 with [Graph v1.1](graph_v1_1_design.md), on feature branch `graph-v1.1-discovery-quality`. It reuses the [revision 2 pre-registration](graph_pilot_preregistration.md) except where stated, and fixes the [R3 deviations](graph_pilot_r3_results.md#6-limitations-and-deviations). R3 stays closed and INCONCLUSIVE; none of its records, packets, ledgers or adjudications enter R4.

## Question

**Q2 (paired, descriptive).** Within the same fresh packet, does adding Graph v1.1 to Discovery Lab plus competent structured-ledger search improve research, counting all the analyst time the graph costs? Two separate benefits are measured:

- **(a) Economic discovery:** economic connection candidates the arm accepts and an independent human confirms against originals.
- **(b) Avoided repetition:** methodological warnings and avoided repeats confirmed useful.

The two are never pooled.

No prices, returns, backtests or investment claims. M passes and H judgments are research-quality outcomes only.

## Changes from R3

| R3 problem | R4 rule |
|---|---|
| Only two pairs formed; no classification possible | Four packets are planned. A **graph-increment classification requires at least three completed pairs**, as preregistered. An ordered reserve list of eligible environments is fixed before any request. If a packet fails to form, the next reserve is probed mechanically, never chosen after seeing content. With fewer than three pairs the result is descriptive only, and no budget expansion or replacement campaign follows |
| Reused packets and routes; R2/R3 sources | **Fresh packets only.** No source, host route, filing set or record used in R1–R3 or earlier Research OS campaigns. Packet ledgers start empty of pilot history |
| The openFDA `limit=1000` response exceeded the size stop | **Size-safe routes only.** Each route must document a page-size or record limit. The request uses a limit whose worst-case documented record size fits under the per-start byte stop, with half the stop as margin. An over-size response is a NOT_FORMED stop, never retried |
| `SUG-` ids were lost; the suggestion-rejection metric read 0/0 | **V2 connection logs are mandatory.** Each packet is frozen with `pilot snapshot --connection-log GRAPH_PILOT_CONNECTION_V2`, so V1 rows are refused and the operator version is pinned. The graph arm saves every suggesting query's snapshot-mode JSON under `<packet>/suggestions-G/` at query time. Every graph-originated row keeps `origin_suggestion_id`, `origin_operator`, `origin_bases` and `connection_class`. These must match a suggestion that replays from the snapshot, with the same endpoints, issued before the row. `pilot blind` seals the export hashes in the key; `unblind` and `report` recheck them |
| Requirement-tag analogies were counted as connections | Graph operators run at `GRAPH_OPERATORS_V1_1`. A warning can only be logged as `METHODOLOGICAL_WARNING`; the validator refuses it as `CONNECTION`. Warnings are a separate dimension |
| Self-logged minutes over-stated some arms by about 9 minutes | **Timestamp-derived effort.** The primary measure remains self-reported analyst minutes, which are checked against ledger, connection-log and graph-query times and against the operator's attested session. The human arm operator personally writes separate, immutable START and STOP attestations (`pilot session-attest`) as each event occurs; assistants never attest. A difference is material above the greater of 5 minutes or 10% of the derived comparator, and smaller differences are still reported. Gaps are descriptive and never subtracted. A definitive classification needs supporting effort evidence (see Outcomes) |
| Two arms wrote connection logs at the end | Logs are written as connections are considered. Each row's `recorded_at_utc` must fall inside the campaign window and precede the arm's final freeze |
| V001 exports leaked arm ids; the owner saw them | Only aliased V2 exports (`pilot realias`) are produced. `pilot leak-scan` must show 0 findings before an export is shown to anyone. No V001-style export exists for R4 |
| The same owner operated, adjudicated with AI assistance, and was exposed | **Independent human adjudication.** At least one adjudicator who did not operate either arm and saw no arm ledger, log, session or key. Two adjudicators are preferred; disagreements are reported, not resolved by an AI. No AI assessment is produced or read before every human adjudication is committed. Every item carries `EXPOSURE: SAW_ARM_INFO=YES\|NO`; any YES marks the comparison potentially unblinded |
| Outcome-like snippets were seen before a freeze (P4-G) | The arm instructions forbid reading outcome fields or outcome-bearing search snippets before the claim is frozen. Any such exposure is logged at once as a deviation on that claim |
| One session per arm confounds session with arm | Still one session per campaign, with the order alternating by packet as fixed now. This confound is declared, not removed |

## Design (unchanged from revision 2 unless stated)

- **Units.** 4 packets (observation-, relationship-, event- and hypothesis-first) × 2 arms. Order: P1 S then G, P2 G then S, P3 S then G, P4 G then S.
- **Arms.**
  - **S:** Discovery Lab, `baseline-search` with the snapshot, and text search of the catalogue and reports.
  - **G:** everything S has, plus the Graph v1.1 operators via `--snapshot --arm G --query-at`.
- **Pinned code.** The snapshot records the graph commit SHA and `operator_version`. A campaign run on different code is invalid.
- **Equivalent starting knowledge.** The same packet snapshot rules as revision 2: frozen packet prefix, catalogue V002 and the arm's own ledger by query time only. No pilot ledger of either arm and no other packet is visible. Arm branches are `graph-pilot-r4/<packet>-<arm>`, merged only after all adjudication.
- **Per-campaign budget (proposed maximum).** 120 minutes, 6 source starts, 10 searches, 8 MiB.
- **Pilot ceilings.** Set by the owner at activation, counted separately from R1–R3 and including packet freeze. No standing allowance follows from this draft.

## Outcomes

**Primary measure and gate (Phase A hardening, [readiness v002](graph_pilot_r4_readiness_v002.md)).** All per-hour dimensions use self-reported analyst minutes. Attested session minutes give a sensitivity, valid only where every arm's START and STOP are attested; the observed record span is descriptive only. Elapsed time is not active research effort: it includes idle time, interruptions and waiting, and misses unrecorded work.

A definitive classification requires either every arm's effort evidence to be CONSISTENT, or no arm CONTRADICTORY and the same classification under the session sensitivity. Otherwise the result is INCONCLUSIVE (`EFFORT_EVIDENCE_UNRESOLVED`), shown beside the primary result.

**Graph configuration (owner decision, frozen prospectively).** R4 uses `GRAPH_OPERATORS_V1_1` with `GRAPH_CLASSIFICATION_V1_2`, under which generic shared identifiers do not ground, and generic register V001, as frozen in [graph_pilot_r4_graph_configuration_v002.json](graph_pilot_r4_graph_configuration_v002.json), which supersedes V001 with identical content and corrected time fields. V2 snapshots default to it and record any deviation. A snapshot with `r4_configuration.conforms: false` must never be treated as a conforming R4 packet: at activation it is refused, or listed as a deviation with the owner's written reason. The rule was registered before its holdout and is supported on it.

**Execution provenance and environment ([readiness v003](graph_pilot_r4_readiness_v003.md)).** Each saved query records its running commit and uncommitted pinned paths. These are validated against the repository's history before blinding, and the commit may be dated no later than the query, with no skew allowance; that is consistency, not proof. R4 runs from one frozen checkout and one Python environment, with full git history kept and no package changes.

All per-hour outcomes use all analyst minutes, including graph query and suggestion-review time, and report self-logged and derived minutes side by side.

| Dimension | Definition |
|---|---|
| Verified economic connections per hour | ACCEPTED rows of class `ECONOMIC_CONNECTION_CANDIDATE` (G) or analyst connections (S), adjudicated CONFIRMED and MEANINGFUL. Graph-originated ones (by `origin_suggestion_id`) are reported as a subset |
| Graph suggestions false or trivial | Over logged economic candidates (`graph_suggestions_false_or_trivial`) and over every graph-originated row by class (`graph_rows_false_or_trivial_by_class`). Exported suggestions with no logged row are counted as not evaluated |
| Useful methodological warnings | `METHODOLOGICAL_WARNING` rows and avoided repeats adjudicated CONFIRMED useful. Reported separately; never added to connections |
| False or premature joins | As revision 2 |
| Minutes per evaluated connection | As revision 2 |
| Time to decisive falsification | As revision 2 (`[DECISIVE:ID]`) |
| Original frozen M passes per hour | As revision 2; H reported separately |
| Review burden | Every item of every class the adjudicator reviewed, adjudicator minutes, suggestion-review minutes. Fewer items labelled as connections is not lower burden |

Analysis is descriptive only: per-packet paired differences and pooled totals, every denominator shown, with no p-values. The rules in `pilot report` apply only with three or more completed pairs. They are proposals for the owner to confirm at activation and are not empirically established.

**What would count against Graph v1.1.** If graph-originated economic candidates are mostly adjudicated trivial or false, or G's verified rate per hour is not higher than S's in at least two of three or more pairs, the discovery-operator claim is not supported. That is recorded as such. Nothing is retired automatically.

## Stops

- **Campaign stops:** as revision 2. A denial or timeout stops that route, with no retry or bypass.
- **Critical stops:** as revision 2, plus:
  - a V2 row that fails origin validation and is not corrected before the export;
  - any export shown before `leak-scan` passes;
  - any AI assessment read before human adjudication is committed.

## Tooling status before activation

Phase A ([readiness report](graph_pilot_r4_readiness_v001.md), branch `graph-pilot-r4-readiness`) implemented and tested items 1, 4 and 6 on synthetic fixtures only:

1. **IMPLEMENTED.** Timestamp-derived effort from append, connection-log, graph-query and operator-attested session timestamps (`pilot effort`; `pilot session-attest`).
2. **IMPLEMENTED (Phase B, [report](graph_pilot_r4_phase_b_v001.md)).** Per-item exposure declarations (`exposure`: saw_arm_info, seen, operated_or_attested_arm), with CONFLICTED and NOT_INDEPENDENT detection.
3. **IMPLEMENTED (Phase B).** Two independently sealed human logs (`pilot adjudication-seal`), a git reveal-order check, and agreement reporting (raw agreement, kappa, disagreements; `pilot adjudication-agreement`). The consensus rule is proposed: an outcome counts only where both reviewers agree.
4. **IMPLEMENTED.** V2 snapshots pin the git commit, the content of the computed implementation boundary (graph, discovery, `spec.py`, the R4 fetch tool and their static import closure) and the Python and dependency versions (`graph_implementation`), beside `connection_log`, `graph_operator_version` and the classification ruleset. Receipts record the actual running commit.
5. **IMPLEMENTED (Phase B).** A separate warning-usefulness log and categories (`USEFUL_LESSON_REUSED`, `USEFUL_NOT_USED`, `NOT_USEFUL`, `CANNOT_ASSESS`), with its own denominators. Conformance-gated primary comparison: non-conforming packets are listed, never compared. Reveal order needs strict ancestry over the commits holding the sealed bytes; zero-row packets are sealed and reported explicitly ([Phase B v003](graph_pilot_r4_phase_b_v003.md)); legacy packets never join an R4 primary cohort; prospective outcomes are unblinded only after both valid seals; POTENTIALLY_UNBLINDED items are included (labelled) with a packet-exclusion sensitivity that must agree (proposed, [Phase B v002](graph_pilot_r4_phase_b_v002.md)).
6. **IMPLEMENTED.** Full suggestion accounting: exported, logged, declined and exported-but-unlogged suggestions by class (`pilot suggestion-accounting`; `pilot report`).

Each remaining item needs tests and a synthetic dry run before any activation. The Phase A rehearsal is `pilot r4-dry-run`.

## Not authorised

This draft authorises no source preflight, request, credential, packet, campaign, adjudication, merge or change to R3, F19, SH09 or any earlier stop.
