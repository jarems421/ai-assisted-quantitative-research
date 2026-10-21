# Discovery Lab + Graph v1 pilot: proposed pre-registration (revision 2)

> **PROPOSED, NOT ACTIVE.** Nothing here authorises acquisition, a live campaign or any research step. It becomes binding only if the owner activates the [proposed authorisation](proposed_owner_graph_pilot_authorisation.md), and the activated text is committed before any source request.

Revision 1 was committed at `942650a`. Revision 2 applies the [owner's protocol corrections](owner_graph_pilot_protocol_2026-10-21.md). Every command it names has run against the implemented CLI in the [synthetic dry run](graph_pilot_dry_run.md) ([validation](graph_pilot_protocol_validation.json)).

**Activated 2026-10-21** by [the owner authorisation](owner_graph_pilot_2026-10-21.md), with owner-amended source routes only: P1 `NOT_FORMED` at preflight; P2 uses the documented SEC daily-index route; P3 uses keyless openFDA device enforcement; P4 uses the owner's primary mechanism. All other rules below apply unchanged.

## Corrections in revision 2

| # | Defect in revision 1 | Correction | Shown by |
|---|---|---|---|
| 1 | `--known-at START_UTC` replays every ledger only up to the campaign start, so `revisit`, `complements` and `suggestions` could not see the arm's own new observations. A later cutoff would admit anything else appended by then. | A **packet snapshot** pins the frozen prior knowledge before either arm starts. Each query names `--snapshot --arm --query-at` and sees exactly that prior knowledge plus its own ledger as appended by the query time. Future query times are refused, and a replayed query time gives the same graph. | Dry run §4; tests |
| 2 | Each arm received "its own prior pilot ledgers", so in later packets the graph arm would carry knowledge found with the graph, and the structured arm its own. | **No pilot ledger of either arm, and no other packet, is visible in any campaign.** Arm ledgers stay off `main` until all eight campaigns finish. | Dry run §8 |
| 3 | Pilot ledgers under `docs/strategy/discovery/` would enter every default graph build. Commands passed arm globs by hand. | The pilot lives under `docs/strategy/graph_pilot/`, outside default discovery. Snapshot mode refuses `--ledgers`, `--known-at`, `--catalogue`, `--mode` and `--as-of`. | Dry run §4; tests |
| 4 | Nothing stopped the structured arm calling graph operators. | With `--arm S`, every graph operator is refused; only `baseline-search` runs. | Dry run §3; tests |
| 5 | Blinding was a manual shuffled list. The log mixed arm-side fields with outcomes. The owner recorded dispositions between the two arms of a packet. | Arm connection logs are kept separate from adjudication. A separate session prepares a shuffled export with arm-hidden fields, one renderer for both arms and a hash-sealed key. Adjudication must be complete and human. Dispositions come after both arms finish. Residual leakage is stated below. | Dry run §5; tests |
| 6 | Zero graph-only connections across four pairs would retire the discovery operators. | Seven dimensions, with all analyst time in the denominator, give three descriptive classifications. Nothing is retired automatically. | Tests; dry run §7 |
| 7 | HTTP 200 qualified a source environment. | Eight eligibility criteria are evaluated on the response itself. Fallback is fixed and record selection is mechanical. | Section "Packet eligibility" |
| 8 | Effort categories (`GRAPH_QUERY` and others) are not valid Discovery Lab effort kinds; such records would be refused. | Categories are `[PILOT:CATEGORY]` tags on valid kinds, and `pilot account` checks them. | Dry run §6; tests |
| 9 | The 10-search ceiling had no check, because Discovery Lab budgets count no searches. | `pilot account` counts `SEARCH` efforts against the ceiling. | Tests |
| 10 | The graph recorded each cut ledger's current total length, so replaying a query time changed after later appends. | A cut input omits the ledger's current length. The visibility receipt reports it separately. | Dry run §4 |
| 11 | "False joins avoided", "time to decisive falsification" and "duplicate research avoided" had no mechanical definition. | Arm decisions are logged per connection; dispositions name their decisive record as `[DECISIVE:ID]`; avoided repeats are logged and adjudicated. | Section "Outcomes" |

## Questions

- **Q1, discovery method (descriptive).** What do Discovery Lab's four methods produce under equal budgets? This covers candidates formed, original frozen M passes, H judgments, reformulations, distinctive predictors actually observed, and source cost per candidate. Methods start from different packets, so Q1 differences are confounded with packet difficulty.
- **Q2, graph increment (paired).** Within the same packet, does adding Graph v1 to Discovery Lab plus competent structured-ledger search improve research on the dimensions below, counting all the analyst time the graph costs?

Neither question can show investment value. No security returns, prices or backtests are used. M passes and H judgments are research-quality outcomes only.

## Design

- **Units.** 4 starting packets (one per method) × 2 arms = **8 campaigns**, plus 4 packet-freeze steps.
- **Arms.**
  - **S (structured):** Discovery Lab commands; `graph baseline-search` with the snapshot; plain text search of the catalogue and its cited reports. No graph operator.
  - **G (graph):** every S tool, plus Graph v1 operators with the snapshot. The measured difference is the graph's increment, not graph versus no search.
- **Order.** Packets run in method order: observation, relationship, event, hypothesis. Arm order alternates as fixed now: P1 S then G, P2 G then S, P3 S then G, P4 G then S.

### Equivalent starting knowledge

Before either arm starts, the packet preparer writes `docs/strategy/graph_pilot/<packet>/snapshot.json` with `graph pilot snapshot`, and commits it. The snapshot pins:

| Frozen prior input | How it is pinned |
|---|---|
| Packet ledger | Exact prefix: event count and head hash. Any later change to the packet ledger is refused |
| Historical memory | Catalogue V002 by SHA-256; its recording time must precede the freeze |
| Packet bundle (private originals) | File names and SHA-256s; each arm verifies its own copy with `pilot verify` |
| Arm ledgers | Paths and campaign ids only. They must not exist yet, and each must begin after the freeze |

At a query time, an arm sees exactly:
- the frozen packet prefix;
- catalogue V002;
- its own ledger, as appended by the query time.

**Never visible** to either arm: the other arm's ledger, notes and connection log; every other packet; every earlier pilot ledger of either arm; records appended after the query time; ledger discovery. The query time may not be in the future or before the freeze. Every output carries a visibility receipt naming the snapshot hash, the query time and the inputs used.

**Earlier pilot ledgers: decision.** Revision 1 let each arm carry its own earlier pilot ledgers into later packets. That would compound any early graph-arm difference into later comparisons. Revision 2 excludes all pilot ledgers, of both arms, from every campaign. Each arm ledger is committed to its own branch, `graph-pilot/<packet>-<arm>`, and merged into `main` only after all eight campaigns and adjudications finish. Only then do pilot records become research memory.

### Execution separated from adjudication

| Role | Who | Sees | Does |
|---|---|---|---|
| Packet preparer | Fresh assistant session | Shortlist, eligibility rules | Probes environments, records the packet ledger, writes and commits the snapshot |
| Arm analyst | One fresh assistant session per campaign, in its own git worktree made at the snapshot commit | Protocol, its arm's tool list, snapshot, its bundle copy | Runs the campaign, logs effort and connections, freezes candidates; commits to its branch |
| Operator | Owner | Ceilings, critical-stop signals | Starts and stops sessions. Does not read arm ledgers, logs or session output until both arms of the packet finish. Gives both arms the same procedural answers only |
| Blind preparer | Fresh assistant session, neither arm | Both arm branches | Runs `pilot blind`; gives the owner the export only; keeps the key private |
| Adjudicator | Owner | Blinded export and cited originals | Adjudicates every item; afterwards decides M/H reviews and dispositions |

M/H reviews and dispositions are decided only after both arms of the packet finish and their connections are adjudicated. The blind preparer presents the frozen candidates of both arms in a shuffled order with campaign ids removed. It then appends the owner's decisions verbatim to the arm ledgers. This step is a procedure, not software.

### Budgets and time

- **Each campaign:** 120 analyst-minutes, 6 ordinary source starts, 10 search queries, 8 MiB of external response bodies.
- **Graph time is inside the budget.** All graph querying, suggestion review and follow-up count against the same 120 minutes, and there is no extension.
- **Effort categories.** Every effort record carries exactly one tag in its description: `[PILOT:SOURCE_SEARCH]`, `[PILOT:READING]`, `[PILOT:RECORDING]`, `[PILOT:BASELINE_SEARCH]`, `[PILOT:GRAPH_QUERY]`, `[PILOT:SUGGESTION_REVIEW]`, `[PILOT:FREEZE_PREP]` or `[PILOT:AVOIDED_REPEAT]`. The structured arm records no graph category. `pilot account` reports minutes by category, searches, starts and bytes against the ceilings, and flags untagged efforts.
- **Unknowns.** An unknown cost stays UNKNOWN and makes that arm's per-hour outcomes UNKNOWN; it is never treated as zero.

## Packet eligibility and selection

**Packet window:** the most recent complete calendar quarter that ended at least 12 months before activation.

**Probe:** each environment gets one request, to the exact listing or data route fixed in the activated shortlist. Eligibility is judged on that response alone:

| Criterion | Requirement |
|---|---|
| E1 Original publisher | The host is the publishing body's own domain, as named in the activated shortlist. No aggregator, mirror or press summary |
| E2 Open access | The owner confirmed at activation that access is free and unauthenticated and that the terms permit retrieval |
| E3 Complete, usable response | The response is HTTP 200, complete (no truncation) and at most 4 MiB. It is machine-readable records or a structured table, not a login wall, CAPTCHA or error page |
| E4 Dated | At least 3 records carry a per-record date inside the packet window |
| E5 Stable identifiers | Those records each carry the publisher's record identifier, unique within the response |
| E6 Relevant fields | Those records carry the method's required fields (below), non-empty |
| E7 Not stopped | Neither the host nor the route matches any persisted stop |
| E8 Original records | The records are the publisher's own data, as published |

**Required fields by method:**
- **Observation-first:** an identified entity (a registry or facility identifier) and a quantity or status field with stated units or categories.
- **Relationship-first:** an identified filer or party and the locator of the original document that states the relationship.
- **Event-first:** an event type or classification and an identified entity.
- **Hypothesis-first:** no source environment. The packet is the owner's mechanism statement, committed at activation, and the packet freeze spends no source starts.

**Fallback (fixed):**
- If any criterion fails, the environment is ineligible: record the failing criterion and probe the second listed environment, with no retry.
- If both fail, that method's packet is **NOT_FORMED** and the pilot continues with fewer pairs, reported as such. No substitute environment is chosen after seeing results.
- The third packet-freeze start may not be spent on a third environment.

**Selection (mechanical, outcome-blind):**
1. Keep the records that satisfy E4–E6.
2. Sort them by record date, then identifier, both ascending.
3. Take the first five, or all of them if only three or four qualify.

Before selection, the preparer reads no record content beyond the eligibility fields. Packets are never chosen by overlap with historical memory, by expected outcome or by prices. The packet ledger lists the excluded records and the reason for each.

## Connection logging

Each arm logs, in `connections-<arm>.jsonl`, **every** cross-record connection and avoided repeat it considered. `pilot connections` validates each log.

| Field | Meaning |
|---|---|
| `connection_id` | Graph suggestions keep their `SUG-` id; connections the analyst forms get `CON-` ids from `pilot.connection_id` |
| `kind` | `CONNECTION`, or `AVOIDED_REPEAT`: work not done because prior memory showed it blocked, stopped or uninformative. An avoided repeat states the avoided action as `AVOIDED: ...` |
| `operator`, `found_via` | How the connection was found: `GRAPH_ONLY`, `BASELINE_SEARCH_DISCOVERABLE`, `ANALYST_READING` or `BOTH`. The structured arm can log neither graph suggestions nor graph attributions |
| `source_record`, `target_record` | Exact references inside the arm's visible inputs (own ledger, frozen packet, catalogue) |
| `arm_decision` | `ACCEPTED` (with the Discovery Lab record that now holds it), `DECLINED` or `UNRESOLVED` |
| `analyst_minutes` | Minutes spent evaluating this connection. These minutes are also inside the effort records; they are used only for the per-connection time outcome |

## Blinded adjudication

- **Export.** After both arms of a packet finish, the blind preparer runs `pilot blind`. The export is shuffled with a salt the preparer chooses. Each item shows:
  - both endpoints, rendered by the same function whichever arm logged it (record text, entities, evidence locators and hashes, depth, dates and periods);
  - one mechanically computed `shared_structure`: same identified entity, shared document hashes, shared requirement tags and period coverage.
- **Hidden from the adjudicator:** arm, connection id, operator, `found_via`, the analyst's stated basis, arm decision, minutes, notes, arm campaign ids, graph explanations and match strengths.
- **Sealed key.** The key (blind id to arm and connection id, plus the salt) is written separately. Its SHA-256 is in the export, so it cannot change once adjudication begins.
- **Adjudication.** The owner adjudicates every item once against the cited originals, without consulting arm ledgers, logs or sessions:
  - `CONFIRMED_AGAINST_ORIGINALS`, which must list the evidence identifiers checked;
  - `PLAUSIBLE_UNVERIFIED`;
  - `REJECTED_FALSE`;
  - `REJECTED_TRIVIAL`.

  The owner also judges economic meaning (`MEANINGFUL`, `NOT_MEANINGFUL` or `UNCLEAR`): does the connection link an observed quantity or documented relationship to a listed company's documented exposure, or to a claim's required measurement? `pilot adjudications` validates the log for completeness and human authorship. The key is unsealed only after the adjudication log is committed.
- **Residual leakage (not removed):**
  - The same owner operates both arms and adjudicates. The owner knows the published arm order and may recognise content or style.
  - Record text can reveal how it was found; the arm instructions forbid naming tools in records, but this is not enforced.
  - M/H reviews and dispositions are made on arm-neutral copies by procedure only, and the owner may infer the arm.
  - Sessions and packets differ, so a difference between arms in one packet partly reflects session variance.

  **Blinding is partial,** and results must be read with this in mind.

## Outcomes

All per-hour outcomes divide by **all** logged analyst minutes of the arm, including graph querying and suggestion review. Each is reported per arm and per packet, with the direction of the G − S difference.

| Dimension | Definition | Better |
|---|---|---|
| Verified connections per analyst-hour | Connections the arm ACCEPTED that are adjudicated CONFIRMED and MEANINGFUL, per hour. Graph-only connections are reported as a subset | Higher |
| False or premature joins made | Accepted connections adjudicated REJECTED_FALSE or PLAUSIBLE_UNVERIFIED. Declined connections adjudicated false (joins avoided) and true connections declined are reported alongside | Lower |
| Minutes per evaluated connection | Median `analyst_minutes` over logged connections | Lower |
| Time to decisive falsification | Median, over REJECT and HOLD dispositions, of the analyst minutes logged before the record the disposition names as decisive (`[DECISIVE:ID]` in its reason) | Lower |
| Duplicate research avoided | Avoided repeats adjudicated CONFIRMED | Higher |
| Original frozen M passes per analyst-hour | M_PASSED dispositions on frozen, original, pre-outcome claims, per hour. H judgments are reported separately | Higher |
| Additional human review burden (a cost) | Items the adjudicator reviewed, adjudicator minutes, and suggestion-review minutes | Lower |

**Secondary:**
- reformulations;
- candidates per hour;
- distinctive predictors observed at original-field depth;
- source starts, bytes and blocked routes;
- the share of graph suggestions adjudicated false or trivial;
- provenance completeness;
- rebuild determinism.

**Not outcomes:** security returns, price moves, profitability or any trading signal.

## Stopping conditions

- **Campaign stop:** the campaign stops when any of these occurs:
  - 120 minutes are used;
  - any ceiling is reached;
  - every candidate formed is frozen or abandoned with a recorded reason.

  A 403, 404, other denial or timeout stops that host and route, with no retry or bypass.
- **Critical pilot stop (halt and report to the owner):**
  - the graph presents unverified material as verified;
  - any tool mutates an authoritative ledger, report or catalogue;
  - synthetic or retrospective records leak into pilot views;
  - an arm accesses the other arm's ledger, log or session, or an earlier pilot ledger;
  - any paid, authenticated or stopped-route request;
  - any budget breach;
  - any market-data or return access.
- **No efficacy or futility stopping.** All eight campaigns run unless a critical stop occurs.

## Analysis and decision rules

- **Analysis is descriptive only:** per-packet paired differences and pooled totals, with every denominator shown. No p-values or confidence intervals are computed; four pairs cannot support them.
- **How a dimension favours an arm:** it favours an arm when that arm is better in at least two packets and in more packets than the other arm.

**Proposed rules** (implemented in `pilot report` for the owner to confirm at activation; not empirically established):

| Result | Condition | Proposed next step |
|---|---|---|
| `INVALID_CRITICAL_STOP` | Any critical stop | Fix and re-review before any further use |
| `GRAPH_INCREMENT_OBSERVED` | All of: at least 3 comparable pairs; pooled verified connections per analyst-hour for G at least S's; at least two benefit dimensions favour G; none favours S; no more than 80% of graph suggestions false or trivial (once at least 20 are adjudicated) | A larger, separately approved pilot. Still not evidence of investment value |
| `NO_GRAPH_INCREMENT_OBSERVED` | At least 3 comparable pairs; G's pooled verified connections per analyst-hour below S's; no benefit dimension favours G | Do not add graph discovery operators to the default workflow. Any retirement is a separate owner decision after reading every dimension |
| `INCONCLUSIVE` | Anything else, including fewer than 3 comparable pairs or mixed dimensions | The owner decides whether a larger pilot is worth its cost |

Zero graph-only connections, alone, triggers no decision: an increment can also appear as fewer false joins, faster falsification or avoided repeats. Each classification describes this sample only; it is not a statistical estimate of the graph's value.

**Q1 results** inform which discovery methods deserve budget in a later campaign. They never rank methods statistically.
