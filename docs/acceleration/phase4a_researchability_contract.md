# SourceResearchabilityContract v001

This small review contract extends existing source/receipt/timing/population infrastructure. It is not a trading certificate or a warehouse. Code: [source_first.py](../../src/research/source_first.py). A review row identifies source, exact frozen routes, access-attempt evidence, sample rule, source hashes, fourteen dimension statuses/reasons/provenance, timing capability and explicitly justified plausible hard gates.

| Dimension | Required distinction |
| --- | --- |
| SOURCE_ACCESS | Actual current primary probe versus prior archived access; HTTP200 alone is not schema success |
| DENOMINATOR | Source-defined record population versus outcome-selected/success-only/corporate-survivor list |
| HISTORICAL_DEPTH | Observed sample vintage versus documented extent versus audited complete coverage |
| POINT_IN_TIME | Original historical record/known time versus present-day reconstruction/latest state |
| TIMING | Observed public instant/date, plausible separately modeled bound, present-day database or contradiction |
| REVISION_LINEAGE | Separate versions/corrections/amendments versus overwritten current record |
| ENTITY_IDENTIFIERS | Accession/CIK, document/agency ID or NCT/sponsor name versus traded security/class |
| RELATIONSHIPS | Evidenced issuer/applicant/sponsor/subsidiary bridge versus inferred current owner |
| RECORD_FREQUENCY | Publisher/sample count, observations per period and missingness versus independent N |
| DEPENDENCE_GEOMETRY | Repeated entity/document/study/agency/calendar/programme clusters, not raw-row independence |
| TERMINAL_LIFECYCLE_BURDEN | Source's natural exposure to ended securities and transitions; no survivor shortcut |
| ACCESS_COST | Public/no purchase in this pass; account-wide usage unknown; no entitlement invented |
| REPRODUCIBILITY | Original archived bytes, immutable hash/receipt/rule/code lineage and offline replay |
| GRAPH_REUSE | Potential later entity/time/source relationships, without building a graph |

Statuses: PROVEN_FROM_EXISTING_EVIDENCE, PASS_BOUNDED_PROBE, PARTIAL, UNKNOWN, BLOCKED, NOT_APPLICABLE. Each requires a reason and evidence reference; missing values also distinguish UNKNOWN (not established) from UNAVAILABLE (known unavailable under the route/scope). No total score selects a surface. Failed primary probes are reviewed as access failures; unvisited follow-ups stay unknown.

Hard gates: access, denominator, PIT, historical depth, reproducibility and sufficient plausible record variation. PARTIAL may justify **planning-level plausibility** only with an explicit evidence-backed basis in `plausible_hard_gates`; it never passes an executable proof compiler, source census or policy gate. BLOCKED/UNKNOWN cannot become preferred. Trading readiness remains separate and fail-closed.

Timing classes: OBSERVED_PUBLIC_TIMESTAMP, OBSERVED_DATE_ONLY, MODELED_BOUND_PLAUSIBLE, PRESENT_DAY_DATABASE_ONLY, CONTRADICTORY, UNKNOWN. A recorded acceptance/effective/posted date cannot manufacture exact first accessibility. This pass approves no new timing policy and activates no old policy.

Access precedes scientific interpretation. A map must precede mechanism directions. Maximum three directions per qualified source; each declares ESTIMAND_TYPE PREDICTIVE or CAUSAL_CANDIDATE, exact proposed record, natural population, economic reasoning, dependence, earlier failure risk and cheapest next falsification. Predictive comparisons need a frozen benchmark/evaluation design; causal candidates additionally need identification/counterfactual assumptions and the dedicated later milestone. Neither status approves an experiment or real inference.
