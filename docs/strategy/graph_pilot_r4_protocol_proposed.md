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
| Self-logged minutes over-stated some arms by about 9 minutes | **Timestamp-derived effort.** Each effort's minutes are checked against ledger append times and the session start and end. Both self-logged and derived minutes are reported. A difference above 10% or 5 minutes per campaign is a flagged deviation |
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

## Tooling needed before activation (not yet implemented)

These are not implemented on this branch.

1. A derived-effort report from append and session timestamps.
2. Per-item `SAW_ARM_INFO` exposure for adjudicators other than the owner, generalising the R3 `SAW_V001` note.
3. A two-adjudicator log with agreement reporting.
4. Pinning the graph git commit in the snapshot. `connection_log` and `graph_operator_version` are already implemented.
5. An adjudication vocabulary for warnings ("useful lesson" or "not useful"). Today a warning is adjudicated with the connection outcomes.
6. A count of exported-but-unlogged suggestions in `pilot report`, read from the sealed manifest.

Each needs tests and a synthetic dry run (`pilot dry-run`) before any activation.

## Not authorised

This draft authorises no source preflight, request, credential, packet, campaign, adjudication, merge or change to R3, F19, SH09 or any earlier stop.
