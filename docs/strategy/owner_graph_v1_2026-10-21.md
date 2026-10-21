# RESEARCH OS — BUILD ECONOMIC KNOWLEDGE GRAPH V1
## Final Architecture Approval, Engineering Implementation and Verification

You are the lead systems architect and principal engineer for Research OS.

**Your task is to implement a complete, practical, evidence-backed Economic Knowledge Graph v1, tightly integrated with the existing Discovery Lab v1.**

This is an approved offline engineering task. Do not stop after producing another architecture proposal.

Use your previously completed document, **“Economic Knowledge Graph v1: architecture decision”**, as the starting architecture, but incorporate every correction and requirement below.

The goal is to create a genuinely useful research-memory and discovery system, not an impressive but superficial graph visualisation.

## 0. EXECUTIVE INSTRUCTION

Research OS is evolving into an AI-assisted system that discovers, investigates and tests potential investment opportunities.

We are not simply building individual trading strategies.

We are building a research system that:

1. Accumulates knowledge from investigations.
2. Remembers previously examined economic observations and relationships.
3. Connects evidence across separate campaigns.
4. Identifies potentially meaningful new relationships.
5. Reuses previous research, including unsuccessful investigations.
6. Understands which evidence is missing.
7. Proposes useful next research questions.
8. Maintains rigorous uncertainty, provenance, identity and historical-time controls.
9. Feeds useful discoveries into the existing Discovery Lab workflow.
10. Improves through accumulated research without independently declaring financial conclusions.

**The graph is Research OS's cumulative economic research memory and discovery coordinator.**

It is not a separate authority for scientific truth, investment decisions, source acquisitions or strategy validation.

### The central outcome

When a new observation enters Research OS, the system should be able to ask:

> Have we encountered this economic entity, asset, relationship, measurement, constraint or research problem before?

If yes:

> What do we already know, what genuinely connects these records, what remains unknown, and is there an inexpensive, authorised way to investigate the connection?

If no:

> Should this observation be retained independently so future investigations can discover it?

**Both outcomes are valuable.**

The graph should become more useful as research accumulates, without becoming noisier or less trustworthy.

---

# 1. SOURCE OF TRUTH AND REPOSITORY AUDIT

Repository:

`jarems421/ai-assisted-quantitative-research`

Branch:

`main`

Last known commit:

`e34b471`

Verify the current HEAD before working.

Read the repository and all relevant instructions, especially:

- `AGENTS.md`
- `README.md`
- `src/research/discovery/`
- `src/research/discovery/records.py`
- `src/research/discovery/ledger.py`
- `src/research/discovery/review.py`
- `src/research/discovery/report.py`
- `src/research/discovery/cli.py`
- `docs/strategy/discovery_lab_design.md`
- `docs/strategy/discovery_lab_guide.md`
- `docs/strategy/discovery_lab_prompts.md`
- `docs/strategy/discovery_lab_walkthrough.md`
- `docs/strategy/measurement_gate_m.md`
- All relevant research reports on F01, F03, F09, F19, SH09, EF06 and related historical failures
- Existing hashing, offline guards, public-test registration, CI and experiment preservation requirements

Read the existing code in sufficient depth to understand its actual contracts.

Do not guess how the ledger functions.

Do not rewrite Discovery Lab merely to fit your proposed graph.

## Existing Discovery Lab functionality

Discovery Lab v1 already provides:

- Append-only, hash-chained JSONL ledgers
- Full rule replay when loading
- Typed source, observation, relationship and candidate records
- Explicit unknown values
- Original evidence and provenance references
- Four distinct clocks
- Historical validity periods
- Claim freezing and version lineage
- Sceptical reviews
- Six unchanged Measurement Gate M requirements
- Separate H assessment
- Human-only dispositions
- Synthetic, retrospective and live fixture classes
- Source budgets and research authority boundaries
- A documented offline demonstration
- Public CI integration

**All of these are existing infrastructure, not features to rebuild.**

Graph v1 must consume them safely.

---

# 2. APPROVED ARCHITECTURE

Implement the following architecture.

## A. Canonical records remain authoritative

Discovery Lab's existing replay-validated ledgers are the authoritative records for new structured discovery research.

Older research reports remain authoritative for their original historical findings and decisions.

The graph is derived from those sources.

It cannot:

- Rewrite a ledger
- Alter a frozen candidate
- Reclassify a historical failure
- Change a source stop
- Certify evidence
- Approve a measurement
- Decide M or H
- Initiate a new investigation
- Request scientific-source access
- Produce trading signals
- Execute or backtest strategies

If the graph's interpretation conflicts with an authoritative source, the source wins.

## B. One graph, several logical views

Implement one canonical in-memory graph projection exposing at least three logical views:

**Evidence and provenance**

Documents, source passports, cited evidence, observations, quantities, measurement meaning, independent outcome routes and four clocks.

**Economic reality and exposure**

Legal entities, listed companies, facilities, contracts, products, assets, obligations, documented relationships, validity periods and explicitly unknown allocations.

**Research memory and discovery**

Campaigns, ideas, claims, frozen versions, reviews, dispositions, missing evidence, historical failures, repeated research problems and suggested connections.

These are filtered views of one graph, not three databases.

## C. Rebuildable in-memory projection

Use a deterministic read-only projection over validated local records.

Prefer Python standard-library data structures and an adjacency index.

Do not add Neo4j, a graph server, vector database, multi-agent framework, external API or other expensive infrastructure.

Do not introduce a SQLite cache unless there is a demonstrated performance problem.

Build should be deterministic: identical authoritative inputs and identical projection rules produce an identical canonical digest.

A cache, if ever required, must remain disposable.

## D. Restricted historical-memory catalogue

Implement the constrained historical-memory catalogue proposed in your architecture review.

Its responsibilities are:

- Identify historical investigations.
- Cite exact historical research reports.
- Preserve original verdicts and their scope.
- Record recurring missing-measurement classes.
- Support retrieval of related older investigations.
- Detect stale or changed referenced reports.

It must not independently assert new economic facts.

Historical conclusions should be tied to exact report paths, contents or hashes and reviewable source passages.

A historical decision must not become a new Discovery Lab disposition simply because the graph includes it.

---

# 3. IMPORTANT CORRECTIONS TO YOUR EARLIER PLAN

These corrections override contradictory parts of your previous architecture decision.

## Correction 1 — Verification belongs to assertions, not ordinary graph nodes

Your original proposal risked making verified paths impossible to traverse because entity and document nodes were not consistently given verification tiers.

Fix this properly.

Separate:

1. The existence of a node in the graph.
2. The identity evidence supporting the node.
3. The evidence status of an assertion about that node.
4. Whether a particular relation is valid within a requested historical period.
5. Whether the relation carries a verified numerical allocation.
6. Whether the entire economic inference has passed human review.

For example:

A legal entity may have a documented identifier.

A separate original record may document that entity operating a facility.

A third record may observe a measured change in that facility.

These are separate assertions.

The path through the entity node must remain traversable without treating the entity itself as the proof of every linked financial proposition.

Implement explicit assertion-level validation and provenance.

Distinguish:

- `DOCUMENTED_RELATIONSHIP`
- `ORIGINAL_FIELD_OBSERVED`
- `ORIGINAL_DOCUMENT_REFERENCED`
- `RECORDED_UNVERIFIED`
- `CONTRADICTED`
- `SUPERSEDED`
- `HISTORICAL_CONCLUSION`
- `SUGGESTION_ONLY`

Adapt names to the existing vocabulary.

Do not misrepresent `VERIFIED_ORIGINAL_RECORD` as verification that the specific economic field was measured.

**Most importantly: a verified connection is not automatically a verified economic exposure.**

## Correction 2 — Count semantic hops separately from structural hops

Your proposal capped paths at three graph edges.

But representing relationships as first-class assertion nodes introduces additional structural hops.

For example:

Observation → entity → relationship assertion → facility → another observation

That may be a short and meaningful economic explanation despite requiring several graph edges.

Implement:

- A default limit of approximately two meaningful economic relationships.
- A strict maximum of three meaningful relationships.
- An appropriate bounded structural traversal depth.
- A maximum of 30 displayed nodes by default.
- A maximum of 10 explanation paths.

The explanation must distinguish structural connections from semantic relationships.

No transitive financial inference is allowed merely because a path exists.

## Correction 3 — Historical memory must be usable immediately

Your original plan hid all retrospective research by default.

That would make Graph v1 appear almost empty because there are currently no live Discovery Lab campaigns.

Instead, use two separate viewing modes:

**Research memory mode — default for exploration**

Show eligible historical and live research, clearly labelled by origin and evidence depth.

**Prospective evaluation mode**

Only show knowledge permitted by the evaluation protocol, with temporal and fixture restrictions explicitly enforced.

Synthetic records must remain isolated in a clearly identified synthetic mode.

Do not imply that a retrospectively transcribed document was known to Research OS at the earlier historical date.

## Correction 4 — Historical time and research-ingestion time must not be confused

Preserve four clocks:

- Economic occurrence
- First public availability
- Original source version/publication
- Research retrieval/ingestion

Additionally distinguish the timestamp when a record was actually appended to a Research OS ledger.

When historical research is transcribed in 2026, do not make the graph pretend it possessed that particular structured record in 2023.

An original investigation's historical closure date is contextual history, not a substitute for a trustworthy graph-ingestion timestamp.

Implement clearly named historical filters, for example:

- `--as-of` for economic validity
- `--known-at` for recorded research knowledge, where that can actually be reconstructed
- Explicit availability/unknown status when a historical snapshot cannot be certified

Unknown historical availability must remain unknown.

For retrospective backfills, historical context may be shown, but it must not silently qualify for prospective point-in-time tests.

## Correction 5 — Avoid fragile free-text tag promotion

Your original proposal used conventions like:

`[REQ:REQ_AVAILABLE_CAPACITY]`

and

`[MEASURES:REQ_AVAILABLE_CAPACITY]`

inside existing text fields.

These can be convenient author annotations, but they are not reliable evidence.

Implement a centrally validated requirement vocabulary.

A tag can help retrieve a potentially relevant observation.

It cannot establish that the observation measures the requirement, has correct units or solves a historical blocker.

For v1, prefer derived, versioned, reviewable mappings in the graph's non-authoritative catalogue rather than silently modifying old or frozen Discovery Lab records.

Where free-text tags are supported, validate them, label their origin and treat them as **candidate matches**.

Do not create a large new ontology or force a Discovery Lab rules migration unless the existing representation demonstrably cannot support the functionality.

## Correction 6 — Improve the evaluation comparison

Your earlier proposal evaluated a baseline first and then let the graph provide additional research suggestions.

That can demonstrate incremental ideas, but also gives the graph-assisted process additional research attention.

The pilot must distinguish:

- New connections found because of the graph
- Connections found because of additional analyst time
- Connections already discoverable through ordinary structured-ledger search
- Suggestions that are plausible but unverified
- Suggestions that were actually confirmed against originals

Implement the hooks and evaluation records needed for a fair later comparison.

Do not launch the pilot now.

---

# 4. MINIMUM GRAPH ONTOLOGY

Build a small, carefully controlled ontology.

Use the existing Discovery Lab vocabulary wherever possible.

Suggested node categories:

- Campaign
- Source passport
- Document/evidence object
- Observation
- Economic entity
- Economic relationship assertion
- Candidate claim/version
- Measurement requirement
- Explicit blocker
- Historical research conclusion

Reviews and dispositions may initially be attached to their exact candidate versions rather than separate graph nodes if that makes the system simpler without losing explainability.

Each relevant node should carry:

- Stable graph identifier
- Original source/campaign identifier
- Record type
- Version
- Fixture class
- Evidence depth or status where applicable
- Available four-clock fields
- Provenance and report references
- Economic entity scope
- Supersession/contradiction state
- Restrictions on interpretation

## Identity

Use namespaced IDs.

Discovery Lab IDs are not necessarily globally unique across campaign ledgers.

Refuse duplicate campaign IDs where uniqueness is expected.

Use stable identifiers for cross-campaign entity joins.

Do not automatically join companies based on names.

Do not confuse:

- Listed issuer
- Legal entity
- Subsidiary
- Parent
- Facility
- Contract
- Security
- Ticker
- Historical alias

A ticker is not a permanent legal-entity identifier.

A company with the same name in two documents is not necessarily the same entity.

Where identity is uncertain, create an explicit identity question, not a verified merge.

Detect contradictory types assigned to the same stable identifier.

## Documents

Join documentary references by actual trusted SHA-256 where available.

A URL or locator alone is weaker evidence and must not automatically prove identical content.

Multiple documents from the same publisher are not necessarily independent.

Two different hashes are not automatically independent either.

Always state when source independence has not been established.

## Relationships

Reuse existing documented relationship types.

Relationships must preserve:

- Source entity
- Target entity
- Direction
- Basis
- Documentary evidence
- Scope
- Validity period
- Allocation status
- Explicit limitations
- Alternatives or contradictory interpretations

Represent relationship assertions as first-class graph objects where useful, rather than unsupported plain triples.

Do not add generic `RELATED_TO` economic edges.

Do not automatically compose ownership, supply, operation or obligation edges into a financially quantified exposure.

---

# 5. THE GRAPH MUST ACCUMULATE REAL RESEARCH MEMORY

The knowledge graph should be able to retain useful findings even when no candidate reaches Measurement Gate M.

Examples of valuable persistent knowledge:

- A specific dataset contains a relevant field.
- A dataset only describes a field, without providing the actual rows.
- An observed quantity is capacity, not utilisation.
- A relationship is documented but its allocation is unknown.
- A legal entity is distinct from the listed parent.
- A source was blocked by access restrictions.
- A historical observation was only visible retrospectively.
- A candidate was rejected for insufficient differentiation.
- A source version changed after a candidate was frozen.
- A hypothesis was reformulated after its outcome was examined.
- Two past investigations require the same unavailable measurement.
- A future dataset might plausibly address a missing measurement.

These should remain usable across research campaigns.

**A negative research result is not an economically false proposition.**

For example, failing to measure spare salmon-treatment capacity does not establish that spare capacity does not exist.

Preserve the exact scope of conclusions.

Do not turn a bounded failure into a global statement that an opportunity is impossible.

---

# 6. HISTORICAL BACKFILL

Create practical historical memory for the existing investigations.

Prioritise:

1. F01 — salmon treatment and service capacity
2. SH09 — offshore predecessor obligations and historical lease mapping
3. EF06 — original and reformulated gross/net insurance objects
4. F19 — insurance assessment and credit utilisation
5. F09 — bankruptcy receivables
6. F03 — chemical substitution and qualified sales

Carefully distinguish similarly named or numbered investigation families.

Do not conflate F03 and EF03.

Read the actual source reports before mapping their findings.

## Historical backfill rules

Use only facts already recorded in Research OS.

Do not acquire new scientific documents.

Do not manufacture an original numeric observation from a narrative summary.

Do not invent stable identifiers, measured values, publication records, legal obligations, financial allocations or source access permissions.

Do not invent original pre-outcome freezes for claims that were not actually frozen.

Do not manufacture new human M/H reviews or dispositions.

If an old investigation cannot be faithfully represented as a complete retrospective Discovery Lab campaign, retain it in the separate, explicitly non-authoritative historical-memory catalogue instead.

**Faithful, limited historical memory is preferable to an apparently complete but fictional reconstructed ledger.**

Any actual retrospective Discovery Lab ledgers must use existing replay validation and clearly label retrospective/post-outcome selection.

Each reconstructed family must preserve its original STOP, HOLD, rejection or limited conclusion.

If there is insufficient information for a proposed field, keep it unknown.

Provide a backfill audit report showing what was recorded, omitted, inferred as a retrieval aid and left unresolved.

---

# 7. HIGH-SIGNAL DISCOVERY OPERATORS

Implement the following genuinely functional research operations.

Do not create operators that simply generate convincing-sounding AI prose.

Each operator must operate on graph records and return structured, explainable results.

## Operator A — Shared evidence and entities

Given a node or campaign:

Find other campaigns that reference the same trusted document hash, stable entity or known economic object.

Return:

- Matching records
- Exact match basis
- Source evidence
- Scope and period
- Original dispositions
- Whether the records are genuinely complementary or merely reuse the same source

A shared company alone must not count as a novel economic discovery.

## Operator B — Complementary observations

Given an observation:

Find independently recorded relationship assertions or observations that may provide missing context.

Example:

An observed facility restriction may relate to an earlier documented operator or contractual counterparty.

The output should describe the potential connection and what remains necessary to prove a financial transmission.

Require suitable identity and temporal checks.

Abstain where the connection is only name- or keyword-based.

## Operator C — Shared missing measurements

Find claims blocked by the same actual research requirement.

Examples:

- Available versus nameplate capacity
- Gross versus net retained financial exposure
- Allocated versus aggregate obligations
- Realised activity versus permission
- Unredacted contractual amounts
- Historical source versions or missing schedules

Preserve exactly why each claim was blocked.

A shared blocker is an opportunity to reuse investigative knowledge, not proof of an economic relationship.

## Operator D — Explain a connection

Given two nodes:

Show the shortest relevant bounded paths.

For every step report:

- The relationship or structural connection
- What the source actually establishes
- Exact evidence references
- Economic period
- Clocks where applicable
- Evidence depth
- Missing quantities
- Identity uncertainties
- Whether the path is connectivity only

The operator must explicitly identify the first unsupported economic leap.

## Operator E — Changed or conflicting knowledge

Detect mechanically supportable cases including:

- Source content hash changed at a known locator
- Conflicting entity types
- Contradicted relationships
- Superseded versions
- Changed observations
- Reference revisions after claim freezing
- Stale historical report hashes

Do not invent a contradiction merely because two records have different values for different periods or populations.

## Operator F — Potential reactivation lead

Given a new observation:

Find earlier claims whose missing measurement might be addressed by the new information.

Example:

A past investigation was blocked by unavailable spare capacity.

A new observation appears to describe actual contractual bookings or capacity allocation.

The graph may say:

"This observation might address a previously recorded measurement requirement."

It must also say:

- Why it matched
- Whether the field is actually visible
- Relevant units and population
- Identity and time compatibility
- Whether the new information existed historically
- What is not yet verified
- What minimum evidence would resolve the gap
- Whether the previous investigation is stopped
- That no new work is authorised

The suggestion must not reopen the stopped research.

## Operator G — Missing economic links

For a candidate, explain which specific links remain unverified.

For example:

Documented contract → unknown counterparty allocation → unverified issuer net exposure.

Display missing links clearly.

Never fill them by proportional arithmetic or model inference.

## Operator H — Next research question

Given open candidate claims and their existing constraints:

Identify potentially reusable decisive checks.

Prefer:

- Specific original fields
- Already documented source routes
- Reusable checks across multiple claims
- Cheap falsification
- Source access within existing authority

But do not claim numerical expected value or rank by fabricated probabilities.

If no affordable check exists, return an abstention or stop recommendation.

**A recommended check is not authorisation to perform it.**

---

# 8. ANTI-NOISE SYSTEM

This is a core product requirement.

A graph with many false or trivial connections is worse than a small graph with useful ones.

Implement the following controls.

### Hard admission rules

Only accept graph material from:

- Replay-validated Discovery Lab ledgers
- Validated, appropriately labelled historical-memory references
- Explicit synthetic fixtures when operating in synthetic mode

No raw source rows should be blindly converted into graph nodes.

No LLM-generated connection should enter the verified assertion layer.

### Identity and deduplication

Deduplicate using justified identifiers and canonical source hashes.

Preserve distinct original records when their meanings, periods or versions differ.

Do not collapse two separate quantities simply because their labels resemble one another.

### Hub suppression

Generic blocker categories, frequent regulators, common sources and heavily connected entities must not dominate suggested connections.

Suppress these as traversal bridges when they create trivial paths.

But keep them searchable and available for explicit inspection.

### Bounded results

Use sensible defaults:

- 30 displayed nodes
- Two meaningful economic relationship hops
- Three maximum meaningful economic relationship hops
- Ten explanation paths
- Ten suggestions per operator invocation

Allow explicit filtered exploration without generating giant unreadable diagrams.

### Quality hierarchy

Prioritise match explanations based on categorical evidence strength:

1. Exact original document/content reference
2. Exact, justified stable economic identity
3. Documented relationship and compatible period
4. Specific measurement-requirement match
5. Analyst-supplied tag or possible textual similarity

The lower categories must never be silently promoted into verified links.

No arbitrary universal confidence score.

### Abstention

If the necessary evidence does not exist, the graph should say so.

Useful examples:

- `NO_VERIFIED_IDENTITY`
- `PERIOD_UNRESOLVED`
- `ALLOCATION_UNVERIFIED`
- `SOURCE_DEPTH_INSUFFICIENT`
- `ONLY_SHARED_KEYWORD`
- `SOURCE_INDEPENDENCE_UNKNOWN`
- `RETROSPECTIVE_ONLY`
- `PREVIOUS_SOURCE_STOP`
- `NO_USEFUL_SUGGESTION`

Adapt exact labels to the implementation.

Each abstention should explain why.

---

# 9. WORKING USER INTERFACE

The graph needs to be practical to use.

Implement a clean command-line interface:

`python -m src.research.graph ...`

Suggested commands, adapting exact names as appropriate:

```bash
python -m src.research.graph build --check

python -m src.research.graph search "salmon capacity"

python -m src.research.graph show NODE_ID

python -m src.research.graph neighbourhood NODE_ID

python -m src.research.graph explain NODE_A NODE_B

python -m src.research.graph trace CLAIM_ID

python -m src.research.graph shared NODE_ID

python -m src.research.graph complements OBSERVATION_ID

python -m src.research.graph same-gap REQ_AVAILABLE_CAPACITY

python -m src.research.graph gaps CLAIM_ID

python -m src.research.graph revisit CAMPAIGN_ID

python -m src.research.graph changes

python -m src.research.graph failures

python -m src.research.graph orphans

python -m src.research.graph next

python -m src.research.graph demo --check
```

Implement meaningful help text, useful output formatting and informative error messages.

## Focused graph visualisation

Export a selected neighbourhood, claim trace or explanatory path in Mermaid and optionally DOT format.

Mermaid is preferred because the repository already uses it.

Visualisation should clearly distinguish:

- Original observations
- Economic objects
- Documented relationships
- Unverified connections
- Historical memory
- Claims
- Missing evidence
- Contradictions

Use clear labels and a legend.

Never display the whole growing graph as an unreadable hairball.

An optional dependency-free local HTML explorer is welcome if it can be implemented cleanly without compromising offline operation or substantially increasing scope.

However, the CLI, focused visual exports and real discovery operators take priority.

The graph must remain usable without the HTML interface.

Every exported or printed derived graph result must make its status clear:

**DERIVED RESEARCH VIEW — NOT INDEPENDENT EVIDENCE — NO RESEARCH AUTHORITY**

---

# 10. INTEGRATION INTO DISCOVERY LAB

Graph v1 must fit into the existing research workflow.

The intended sequence is:

1. A researcher records an observation or documented relationship through Discovery Lab.
2. Discovery Lab validates and appends the record.
3. The graph rebuilds or refreshes its derived projection.
4. The graph identifies potentially related historical observations, relationships and research gaps.
5. A researcher reviews the proposed connections.
6. Verified original evidence is examined where authorised.
7. Any substantive new claim is separately recorded and frozen through Discovery Lab.
8. Existing M/H review remains unchanged.
9. The eventual outcome and the lessons from failure become reusable graph memory.

No graph operator may append authoritative Discovery Lab records automatically.

## Cross-campaign lineage

Ensure that future work can identify a relationship to a previous claim even when it appears in another campaign ledger.

Do not rely solely on unvalidated local IDs.

Use explicit campaign-qualified references in derived graph metadata.

Respect the current Discovery Lab schema rather than silently introducing new required fields.

If stronger cross-campaign lineage eventually requires a schema migration, document it as a future Discovery Lab v2 decision.

---

# 11. ADVERSARIAL TESTING

Write comprehensive tests that cover at least the following cases:

1. Tampered ledger input is rejected.
2. Duplicate campaign IDs are rejected.
3. Namespaced record identities remain stable.
4. Two entities sharing a name are not automatically merged.
5. A ticker is not treated as a permanent legal-entity identity.
6. Conflicting cross-ledger entity types are exposed.
7. A documented relationship remains separate from its allocation evidence.
8. A verified entity path does not certify financial exposure.
9. An original document citation does not automatically verify a specific quantity.
10. Schema-only evidence cannot satisfy an original measured predictor.
11. Retrospective descriptions do not become original-field observations.
12. Unknown historical clocks remain unknown.
13. A modern relationship cannot be applied to an earlier date without evidence.
14. Retrospective transcription time is not rewritten as original historical research time.
15. The graph does not derive first-public time from modern records.
16. Two copies of a source are not automatically independent corroboration.
17. Different hashes from related publishers do not automatically certify independence.
18. A frozen claim retains correct record-version references.
19. Reformulated claims remain distinct from originals.
20. Contradicted records remain available for inspection.
21. Superseded versions remain available with explicit history filters.
22. Synthetic campaigns cannot contaminate prospective real-research views.
23. Retrospective records are visibly identified in research-memory mode.
24. Verified traversal is not incorrectly blocked by neutral structural entity nodes.
25. Structural hop counts do not incorrectly reject short semantic paths.
26. Long-path economic inferences cannot self-certify.
27. Generic high-degree hubs do not generate spurious discovery results.
28. Shared keywords alone do not create verified edges.
29. Unknown measurement tags do not create strong matches.
30. A proposed match cannot become a verified relationship without Discovery Lab review.
31. A new campaign may produce an explainable cross-campaign suggestion.
32. Historical HOLD and STOP states remain unchanged.
33. F01 does not acquire fictional treatment-capacity information.
34. SH09 does not acquire a fictional lease or security allocation.
35. EF06 v1 and v2 remain separate economic objects.
36. Missing source documents are reported rather than filled in.
37. Private archive bytes and credentials are never exported.
38. Graph commands operate entirely offline.
39. Build and queries do not modify authoritative ledgers.
40. Two builds from unchanged inputs yield identical canonical digests.
41. Corrupted historical catalogue references are flagged.
42. Empty inputs or unrelated records produce appropriate abstentions.
43. Existing Discovery Lab tests remain successful.
44. Existing experiment and source-stop preservation checks remain successful.

Do not write tests that merely assert the specific prose generated by a canned demo.

Test actual projection, identity, graph traversal, uncertainty handling, filtering and discovery logic.

---

# 12. REQUIRED DEMONSTRATIONS

Provide reproducible offline demonstrations.

## Demo A — F01 salmon

Show the previously examined treatment-capacity investigation.

The graph should identify the relevant past observations and the exact outstanding measurement problem.

It must not claim that vessel visits are treatment episodes or that proximity demonstrates available spare capacity.

Show how a hypothetical future observation might match the missing-requirement category while remaining an unverified lead.

## Demo B — SH09 offshore

Show the recorded predecessor-obligation research.

Explain which source relationships exist, which historical lease/security allocations are missing and why the available graph does not demonstrate a valid issuer exposure.

Respect all recorded access denials.

## Demo C — EF06 claim versioning

Show:

- Original economic object
- Reformulated economic object
- Gross versus retained/net distinction
- The version lineage
- Existing M result, where documented
- Original H/investment limitation
- Why v2 cannot be counted as an original v1 success

## Demo D — Cross-campaign synthetic discovery

Construct two fully synthetic but structurally valid campaigns.

Campaign A records a verified relationship involving a specific facility or contract and retains a claim blocked by a missing operational quantity.

Campaign B later records a new observation about the same properly identified economic object.

The graph must detect the possible complementary relationship without being given the answer manually in the query.

It should explain the connection and list the specific missing evidence.

## Demo E — False-positive rejection

Construct superficially similar records with names or keywords in common but different economic identities, periods or populations.

The graph must refuse to present the similarity as a verified economic connection.

## Demo F — Growth over time

Show the same graph rebuilt before and after a new valid campaign ledger becomes available.

Demonstrate:

- Existing knowledge preserved
- New observation discoverable
- A genuinely useful new suggestion
- No duplicated authoritative evidence
- Deterministic output
- No mutation of existing research records

---

# 13. TEST GRAPH UTILITY AGAINST A SIMPLE LEDGER

Before any real discovery pilot, implement an offline baseline evaluation.

Compare:

**Baseline A:** ordinary structured-ledger and text/identifier search.

**System B:** the same available knowledge with graph-specific operators.

Use identical source records and a fixed evaluation task set.

Measure:

- Correct cross-campaign connections recovered
- False-positive relationships
- Relevant missing requirements identified
- Explanation/provenance completeness
- Whether the graph finds links baseline search misses
- Build and query runtime
- Manual review burden where it can be measured honestly

The synthetic comparison demonstrates operational functionality, not scientific research superiority.

Do not fabricate empirical gains.

Also prepare a prospective pilot protocol that separates graph benefit from extra research effort.

Include proposed failure criteria:

- Any incorrect promotion of unverified material stops deployment until fixed.
- Any mutation of an authoritative record is a critical failure.
- Any synthetic/retrospective leakage into prospective evaluation is a critical failure.
- Persistent high false-positive rates should cause rules to be tightened or operators removed.
- No incremental usefulness after a sufficiently informative pilot should justify simplifying the graph.

The exact numeric thresholds must be labelled proposed rather than empirically established.

Do not execute a live campaign.

---

# 14. ENGINEERING QUALITY

Build to production-quality standards appropriate for a small research repository.

Priorities, in order:

1. Correctness
2. Preservation of research integrity
3. Provenance
4. Useful graph queries
5. Conservative discovery
6. Understandable implementation
7. Reproducibility
8. Good ergonomics
9. Performance
10. Visual polish

Avoid unnecessary abstraction layers.

Avoid giant monolithic files where clean small modules are justified.

Avoid speculative distributed systems, event brokers, model orchestration or databases.

No new external dependency unless it demonstrably improves v1 and cannot reasonably be avoided.

The code should be straightforward enough for another researcher to audit.

Treat the graph as a scientific instrument whose mistakes must be diagnosable.

Every operator must be explainable.

---

# 15. IMPLEMENTATION SEQUENCE

Work through the following stages without stopping to ask for approval between ordinary engineering steps.

### Stage 1 — Audit and baseline

- Confirm HEAD and repository state.
- Inspect relevant implementation.
- Run existing tests.
- Record preservation baseline.
- Define precise minimal ontology and integration points.

### Stage 2 — Core projection

- Implement deterministic, validated ledger ingestion.
- Implement stable graph identities.
- Implement nodes and typed assertions.
- Implement canonical digest.
- Preserve versions, fixture categories, dates and provenance.

### Stage 3 — Integrity and graph rules

- Implement assertion-based verification.
- Add identity conflict detection.
- Implement semantic and structural path separation.
- Add historical filters.
- Enforce no automatic financial inference.

### Stage 4 — Historical memory

- Implement catalogue validation.
- Add faithful initial legacy backfill.
- Preserve exact historical outcomes.
- Detect stale report references.
- Clearly distinguish legacy memory from original observations.

### Stage 5 — Discovery functionality

Implement the shared, complements, same-gap, explain, changes, revisit, gaps and next operators.

Make them genuinely functional.

Add clear abstentions and noise suppression.

### Stage 6 — Interface and visualisation

Implement the CLI, search, inspection, trace, filtered neighbourhood and focused visual export.

### Stage 7 — Offline demonstrations

Build reproducible synthetic fixtures and historical worked examples.

### Stage 8 — Adversarial verification

Run new graph tests, full Discovery Lab tests, public checks and relevant preservation suites.

Fix all regressions.

### Stage 9 — Documentation

Document:

- Architecture and source-of-truth boundaries
- Node and relationship ontology
- How evidence is represented
- How verified versus proposed links differ
- How historical research is retained
- Cross-campaign identity
- Temporal validity
- Discovery operators
- Anti-noise and abstention rules
- CLI examples
- Visualisation usage
- Known limitations
- Graph v2 possibilities
- Later prospective pilot protocol

### Stage 10 — Delivery

Commit the intended changes to the appropriate branch and push following existing repository conventions.

Verify hosted CI where accessible.

Do not claim CI success unless actually observed.

Do not modify unrelated worktree files.

Preserve all existing frozen research decisions.

---

# 16. STRICT RESEARCH AUTHORITY BOUNDARIES

This task authorises:

- Local repository inspection
- Offline engineering
- Existing-source and historical-report reuse
- Synthetic test creation
- Graph implementation
- Documentation
- Local tests
- Normal repository commits and pushes

It does not authorise:

- New scientific-source acquisition
- Reopening stopped source routes
- Paid or authenticated research access
- Cloud research jobs
- Market-data collection
- Historical price inspection
- Economic backtests
- Strategy execution
- Brokerage connections
- Modification of EXP001–EXP007 or any Store contract
- Automatic Measurement Gate M approval
- Automatic H approval
- Automatically starting a discovery pilot

Specific historical constraints remain intact:

- F19 stays on HOLD.
- SH09 remains stopped.
- EXP004 retains its unresolved execution boundaries.
- All prior source stops and acquisition restrictions remain in force.
- Historical trial counts and experiment identities remain unchanged.

A graph recommendation never grants scientific authority.

---

# 17. DEFINITION OF DONE

I do not want a theoretical design that happens to contain some Python modules.

I want a graph that is already useful.

Success requires all of the following:

**Accumulation**

The graph retains meaningful past discoveries and can incorporate future validated campaign records.

**Connection**

It finds justified cross-campaign relationships that would otherwise require manual research-memory searches.

**Explanation**

Every meaningful proposed connection can be traced to its inputs and evidence limitations.

**Noise rejection**

It distinguishes valuable candidate connections from trivial overlaps or unsupported inference.

**Historical integrity**

The graph remembers what previous investigations concluded without rewriting them.

**Discovery support**

It identifies missing measurements, reusable evidence and potential next research questions.

**Practical usability**

A researcher can search, inspect, trace, explore and visually review the graph through working commands.

**Scientific discipline**

No hallucinated edge, unknown financial allocation, retrospective source, graph path or AI interpretation automatically becomes accepted economic evidence.

**Reproducibility**

Identical inputs yield identical derived graph outputs.

**Non-interference**

Discovery Lab, Measurement Gate M, experiments, source stops and research authority remain intact.

**Verification**

The new test suite and the existing repository checks pass.

---

# 18. FINAL DELIVERY REPORT

After implementation, provide a clear report covering:

1. Exact architecture implemented.
2. What changed from the original architecture plan.
3. All files created and modified.
4. Working graph capabilities.
5. Discovery operators implemented.
6. Historical investigations integrated.
7. Noise controls and refusal behaviour.
8. Demonstration outputs.
9. Actual test results and command counts.
10. Existing tests and preservation checks.
11. Deterministic rebuild verification.
12. Remaining weaknesses.
13. Features postponed to Graph v2.
14. Commit SHA and push confirmation.
15. Hosted CI result if observed.
16. How to use the graph today.
17. The exact next step for the controlled Discovery Lab + Graph pilot.

Be explicit about what is implemented, what is only proposed and what remains unverified.

## Final instruction

**Build the graph now.**

Do not turn this into another multi-page planning exercise.

You already completed the architecture study. The corrections above settle the major architectural questions.

Make reasonable engineering decisions autonomously, keep the existing repository contracts intact and implement the smallest complete system that fulfils the requirements.

The result should be a genuine, increasingly useful research-memory and discovery tool, not merely a network diagram.

**We are building the foundation for a system that may eventually discover trading strategies—not a system that assumes its discoveries are already profitable.**
