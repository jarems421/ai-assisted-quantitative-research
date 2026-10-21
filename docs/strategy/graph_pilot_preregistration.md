# Discovery Lab + Graph v1 pilot: proposed pre-registration

> **PROPOSED, NOT ACTIVE.** Nothing here authorises acquisition, a live campaign or any research step. It becomes binding only if the owner activates the [proposed authorisation](proposed_owner_graph_pilot_authorisation.md), and the activated text is committed before any source request.

## Questions

The pilot separates two questions that must not be confused:

- **Q1, discovery method (descriptive).** What do Discovery Lab's four methods (observation-first, relationship-first, event-first, hypothesis-first) produce under equal budgets? This covers candidates formed, original frozen M passes, H judgments, reformulations, distinctive predictors actually observed, and source cost per candidate. Q1 outcomes are reported per method, pooled over arms and per arm. Methods start from different packets, so Q1 differences are descriptive and confounded with packet difficulty.
- **Q2, graph increment (paired).** Within the same method and starting packet, does adding Graph v1 to Discovery Lab plus competent structured-ledger search increase verified, economically meaningful connections per analyst-hour? Does it reduce false suggestions, avoid duplicate research or shorten time to decisive falsification? Q2 outcomes are reported as paired differences per packet.

Neither question can show investment value. No security returns, prices or backtests are used. M passes and H judgments are recorded as research-quality outcomes only.

## Design

- **Units.** 4 starting packets (one per method) × 2 arms = **8 campaigns**, plus 4 neutral packet-freeze steps.
- **Arms.**
  - **S (structured):** Discovery Lab v1 commands; `python -m src.research.graph baseline-search` (competent structured-ledger search over the same ledgers and catalogue); plain text search of the catalogue and its cited reports. No graph operator.
  - **G (graph):** every S tool, plus Graph v1 operators. The measured difference is therefore the graph's increment, not graph versus no search.
- **Equivalent starting information.**
  - **Packet:** both arms of a packet receive the identical frozen packet bundle: documents, hashes and a packet note.
  - **Memory:** both arms receive the same historical memory (catalogue V002 and its cited reports), and each arm's own prior pilot ledgers only.
  - **Separation:** each arm's ledgers live in a separate directory (`docs/strategy/discovery/pilot/S/` and `.../G/`). Every command passes `--ledgers` for its own arm and `--known-at` set to the campaign start. Accessing the other arm's ledgers or notes before the pilot ends is a protocol violation.
- **Equal budgets per campaign:** 120 analyst-minutes, 6 ordinary source starts, 10 search queries, 8 MiB of external response bodies.
- **Graph time is inside the budget.** All graph querying, suggestion review and follow-up of a suggestion count against the same 120 minutes. There is no extra time, and the campaign stops at 120 minutes. Time is logged as effort records in these categories: `SOURCE_SEARCH`, `READING`, `RECORDING`, `BASELINE_SEARCH`, `GRAPH_QUERY`, `SUGGESTION_REVIEW`, `DISPOSITION_PREP`. Graph arm results are also reported with graph-specific minutes removed, so the cost of the increment is visible.
- **Sessions.** Each campaign is run by a fresh assistant session. It receives only the protocol, its arm's tool list, the packet bundle, the historical memory and its arm's prior ledgers. The owner does not relay findings between arms.
- **Allocation and order.**
  - **Method order:** packets in method order observation, relationship, event, hypothesis.
  - **Arm order:** alternates by packet, fixed now: packet 1 S then G, packet 2 G then S, packet 3 S then G, packet 4 G then S.
  - **Packets:** selected by the rule in the authorisation, without reference to historical memory overlap or any outcome. The packet freeze is committed (hash) before either arm starts.
- **Dispositions.** These are human-only, as in Discovery Lab. The owner records each campaign's dispositions before the paired campaign begins, using the unchanged Measurement Gate M and H rules.

## Connection logging and adjudication

- **What counts.** Each arm logs every cross-record connection it considers. A connection is a link between a new record and a prior record, claim or historical investigation, or between new records in different campaigns. Each entry carries its basis, the minutes spent and how it was found.
  - **Graph suggestions** keep their `SUG-` IDs.
  - **Connections the analyst forms** get `CON-` IDs from `evaluate.connection_id`.
  - **Recording:** connections an arm accepts are recorded through Discovery Lab, as a relationship record or a claim citing `selection.prior_related_claims`.
- **Blinded adjudication.** After both arms of a packet finish, a separate session prepares one shuffled list of all logged connections, with arm labels removed. The owner adjudicates each entry as one of: `CONFIRMED_AGAINST_ORIGINALS` (must cite the Discovery Lab record now holding it), `PLAUSIBLE_UNVERIFIED`, `REJECTED_FALSE`, `REJECTED_TRIVIAL`.
- **Economic meaning.** The owner also judges economic meaning against a fixed rubric: the connection links an observed quantity or documented relationship to a listed company's documented exposure, or to a claim's required measurement. Labels are re-attached only after adjudication. The log is validated by `python -m src.research.graph adjudications`.
- **Attribution (`found_via`).**
  - `GRAPH_ONLY`: surfaced by a graph operator, and the mechanical flag shows competent structured search over the same knowledge would not find it.
  - `BASELINE_SEARCH_DISCOVERABLE`: surfaced by the graph, but the structured search would also find it.
  - `ANALYST_EXTRA_TIME`: found through ordinary reading.
  - `BOTH`.
  - The structured arm cannot record `GRAPH_ONLY` or `BOTH`; the validator refuses them.

## Outcomes

**Primary, Q2 (paired per packet, reported as counts and per analyst-hour):**

| Outcome | Definition |
|---|---|
| P1 Verified economically meaningful connections per analyst-hour | Connections adjudicated `CONFIRMED_AGAINST_ORIGINALS` and economically meaningful, divided by minutes used / 60 |
| P2 False suggestions | Logged connections adjudicated `REJECTED_FALSE`, plus `REJECTED_TRIVIAL` reported separately. For G, also the share of adjudicated graph suggestions that were false or trivial |
| P3 Duplicate research avoided | Confirmed instances where the arm checked prior memory and did not acquire a source, or pursue a requirement, already recorded as blocked, stopped or unavailable for the same entity (an `AVOIDED_REPEAT` effort citing the prior record). The opposite, repeated dead-end work, is detected after the fact by comparing pilot source locators and requirement tags with prior stops and gaps |
| P4 Time to decisive falsification | Minutes from campaign start to the first record that names the decisive missing variable, or to a disposition (REJECT, HOLD, VERIFY or M_PASSED), for each candidate. Median per arm |

**Secondary:**
- **Q1 and Q2:** original frozen M passes (human); H judgments (human, separate); reformulations; candidates per hour; distinctive predictors observed at original-field depth.
- **Effort and sources:** source starts, bytes and blocked routes encountered.
- **Burden and integrity:** suggestions adjudicated per hour (review burden); provenance completeness of accepted connections; graph rebuild determinism (digest identical when rebuilt from the same inputs).

**Not outcomes:** security returns, price moves, profitability or any trading signal.

## Stopping conditions

- **Campaign stop:** 120 minutes used, any source ceiling reached, or a human disposition recorded for every candidate formed. A 403, 404, other denial or timeout stops that route, with no retry or bypass.
- **Critical pilot stop (halt and report to owner):**
  - the graph presents unverified material as verified;
  - any authoritative ledger, report or catalogue is mutated by a tool;
  - synthetic or retrospective records leak into prospective views;
  - cross-arm ledger access;
  - any paid, authenticated or stopped-route request;
  - any budget breach;
  - any market-data or return access.
- **No efficacy or futility stopping.** The sample is far too small; all 8 campaigns run unless a critical stop occurs.

## Analysis and decision rules

**Method of analysis.** Descriptive only: per-packet paired differences and totals, with every denominator shown. No p-values or confidence intervals are computed, since 4 pairs cannot support them. Unknown costs stay UNKNOWN.

**Proposed decision rules.** These are proposals for the owner to confirm at activation; they are not empirically established:

| Result | Proposed next step |
|---|---|
| Any critical stop | Fix and re-review before any further use |
| No graph-only connection, across all 4 pairs, both confirmed against originals and judged economically meaningful | Retire the discovery operators (`revisit`, `complements`, `shared`, `same-gap`, `next`) from the research workflow. Keep `trace`, `explain`, `changes` and the catalogue |
| More than 80% of adjudicated graph suggestions `REJECTED_FALSE` or `REJECTED_TRIVIAL` (with at least 20 adjudicated) | Tighten match rules or remove the noisiest operator |
| At least one graph-only confirmed meaningful connection, no critical failure, and the false/trivial share at or below 80% | Proceed to a larger, separately approved pilot. The result is still not evidence of investment value |

**Q1 results** inform which discovery methods deserve budget in a later campaign. They never rank methods statistically.
