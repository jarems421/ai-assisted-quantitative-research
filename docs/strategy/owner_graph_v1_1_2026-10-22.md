# Research OS — Economic Knowledge Graph v1.1: Improve Discovery Quality

You are working in the existing Research OS repository:

`jarems421/ai-assisted-quantitative-research`

Your task is to implement a targeted improvement to **Economic Knowledge Graph v1**, based on the findings of the now-closed Graph Pilot R3.

**The objective is to make the graph discover more meaningful economic relationships while reducing irrelevant suggestions, without sacrificing provenance, historical memory, falsifiability or research integrity.**

This is a focused Graph improvement, NOT a rewrite of Research OS.

## 1. Understand the existing system first

Thoroughly inspect:

- `src/research/graph/`
- `src/research/graph/operators.py`
- `src/research/graph/rules.py`
- `src/research/graph/model.py`
- `src/research/graph/project.py`
- `src/research/graph/pilot.py`
- `tests/test_graph.py`
- `docs/strategy/graph_v1_design.md`
- `docs/strategy/graph_pilot_r3_results.md`
- `docs/strategy/graph_pilot_r3/adjudication_provenance_amendment.json`

Understand the existing graph ontology, projection architecture, historical catalogue, identity validation, time handling, operator semantics and suggestion system.

Preserve the existing design principle:

**The graph is a read-only, explainable research-memory and discovery layer, not an alternative source of truth.**

Do not modify authoritative Discovery Lab records or allow graph suggestions to approve research, verify exposure, or determine M/H.

## 2. The problem identified by Graph Pilot R3

The closed pilot produced the following descriptive results:

- 10 graph-operator connections were adjudicated trivial.
- Zero graph-only operator connections were confirmed.
- All 10 confirmed connections originated from analyst reading of original records.
- Structured search achieved 4.16 verified connections per analyst-hour versus 3.15 for graph-assisted research.
- The pilot was **INCONCLUSIVE**, with only two paired packets, potentially unblinded and AI-assisted adjudication.

Do not present these findings as proof that Graph v1 is ineffective generally.

However, they reveal an actionable weakness.

The graph connected unrelated historical investigations because they shared broad requirements such as:

- Missing capacity measurements.
- Unverified financial allocation.
- Unidentified suppliers.
- Missing economic exposure.
- Incomplete observations.

For example, an investigation about a medical-device recall might receive a graph connection to a salmon-farming investigation because both had missing capacity or allocation information.

That is not a meaningful economic connection.

It is, at most, a reusable methodological warning.

We need to distinguish these two things properly.

## 3. Introduce a clear distinction between economic connections and methodological warnings

Implement an explicit, explainable separation between:

**A. Economic connection candidates**

A potential relationship supported by specific evidence linking economic objects, events, documents, firms, products or causal mechanisms.

Examples include:

- An exact product identifier linking a recall to another regulatory record.
- A documented supplier/customer relationship covering the relevant period.
- A regulatory filing explicitly linking two recall events.
- A verified corporate-identity join connecting relevant records.
- A directly documented commercial relationship that might address a research hypothesis.

An exact identifier or shared document can justify investigating a connection, but does not independently prove financial exposure, causation, materiality or economic benefit.

**B. Methodological warnings**

Reusable lessons about how previous investigations failed or which variables remain difficult to measure.

Examples include:

- Another investigation also lacked cost allocation.
- Another company had unverified supplier identity.
- An unrelated historical claim failed because its measurement variable was incomplete.

These should remain valuable research memory, but they must not be reported as discovered economic connections.

**C. Unverified or rejected matches**

Identity lookalikes, overlapping terminology, out-of-period relationships, reused citations, and other matches that cannot justify even a provisional economic connection.

Retain useful explanations and abstention reasons.

Do not simply delete weak matches to make the results look better.

## 4. Improve the existing graph operators

Focus particularly on:

- `same_gap`
- `revisit`
- `next_questions`
- Relevant shared-entity/document and relationship operators.

The current `same_gap` operator is useful for finding claims blocked by the same requirement. Keep that ability, but explicitly classify its output as methodological reuse, not economic discovery.

The current `revisit` operator can produce suggestions based only on `AUTHOR_TAG_CANDIDATE`. Requirement-tag-only matches must not enter the economic-connection candidate category.

For `next_questions`, keep identifying recurring research requirements, but do not imply that several investigations sharing a requirement are economically related.

Where stronger independent evidence accompanies a weak requirement match, preserve the stronger evidence and classify based on that evidence rather than blindly suppressing the entire result.

Avoid hard-coded sector exclusions. A connection between different industries can be economically meaningful if a real, documented transmission mechanism exists.

### Require a grounded connection explanation

For each economic connection candidate, expose:

1. The exact source and target records.
2. The specific documented basis of the proposed connection.
3. The identifier, document or relationship involved.
4. The relevant economic objects and their roles.
5. Temporal compatibility, including unknown first-public times.
6. What the evidence establishes.
7. What remains unverified.
8. The first unsupported economic inference.
9. The reason the connection is worth investigating.

If an item cannot explain a specific economic relationship beyond shared research requirements, classify it as a warning or abstain.

Do not use an arbitrary numerical relevance score or an opaque LLM judgement to bypass the evidence rules.

## 5. Preserve genuinely useful graph capabilities

We do not want to weaken the system by making it excessively conservative.

Preserve:

- Historical memory and previous research failures.
- Exact-identifier discovery.
- Document and content-hash matching.
- Documented entity and relationship joins.
- Temporal validation.
- Cross-investigation learning.
- Contradictory evidence.
- Negative findings.
- Reusable research warnings.
- Useful questions for human investigators.
- Full evidence provenance and traceability.

In particular, the graph should still help researchers avoid repeating earlier investigative mistakes.

But **avoiding a repeated mistake is a different benefit from discovering a new economic relationship**. Report them separately.

## 6. Resolve the suggestion-traceability weakness for future evaluations

R3 also identified a protocol deviation: graph-originated connections were recorded under independently generated `CON-` IDs without preserving the original `SUG-` suggestion IDs.

This made the registered graph-suggestion rejection metric unusable.

Inspect the existing suggestion-ID and connection-log interfaces.

Design a backward-compatible way for future evaluation records to retain the originating suggestion ID, operator and evidence basis.

Do not change R3's historical logs, adjudications, sealed exports or results.

If changing an existing format would invalidate historical records, introduce a versioned prospective format instead.

Every newly logged graph-originated connection should be traceable to the exact suggestion that generated it.

## 7. Build strong regression tests

Create targeted synthetic test cases demonstrating that:

- A medical-device recall and an unrelated salmon investigation sharing a requirement produce a warning, not an economic connection.
- Shared generic allocation blockers do not imply shared economic exposure.
- Exact product identifiers can produce grounded candidate connections.
- A documented recall supersession produces a useful relationship.
- A supplier name match without legal identity evidence does not become a verified join.
- A documented relationship outside the relevant period is rejected.
- A shared document does not count as independent corroboration.
- Historical-memory warnings remain retrievable.
- Weak requirement-tag matches cannot outrank grounded connections.
- Connections retain suggestion IDs and complete provenance where the prospective format requires them.
- Outputs remain deterministic, read-only and reproducible.

Test both positive and negative cases. We must not improve precision by simply suppressing every possible discovery.

Use R3 solely as a diagnostic case. Do not tune a new benchmark retrospectively and then describe success on it as independent validation.

## 8. Evaluate quality without inventing performance claims

Create a new synthetic regression evaluation that measures separately:

- Grounded economic connection candidates.
- Methodological warnings.
- Trivial or unsupported matches.
- Missed valid connections.
- Identity or timing errors.
- Review burden.
- Provenance completeness.
- Useful historical-memory retrieval.

Compare Graph v1.1 against the previous implementation and competent structured search using the same synthetic fixtures.

These checks establish functional behaviour only.

Do not claim a real-world accuracy improvement, higher investment returns, superior economic discovery or statistically meaningful results without a separate prospective experiment.

Prepare a proposed Graph Pilot R4 protocol using fresh evidence packets, accurate effort logging, cleaner blinding, independently collected human judgments and at least the preregistered minimum number of pairs.

**Do not run a real R4 pilot or acquire external scientific evidence without separate authorisation.**

## 9. Engineering constraints

- Preserve all R3 historical artefacts, hashes and decisions.
- Do not rewrite Discovery Lab.
- Do not merge into `main` without review.
- Do not modify Opportunity Scout or its frozen evaluations.
- Keep the graph offline, read-only and deterministic.
- Do not create a second authoritative database.
- Do not introduce unnecessary dependencies or heavy frameworks.
- Prefer small, well-tested changes to the existing operators and presentation layers.
- Preserve existing public interfaces where possible. Version breaking changes.
- Do not use an LLM to invent or verify economic facts.
- Do not silently remove failing tests or relax integrity safeguards.

Work on a dedicated feature branch.

## 10. Deliverables

Implement the improvements, rather than merely producing a plan.

Then provide:

1. A clear explanation of the changes to each affected operator.
2. A before/after comparison using reproducible synthetic fixtures.
3. Tests covering grounded connections, methodological warnings and rejected matches.
4. Any necessary versioned changes to the suggestion logging format.
5. Updated documentation and examples showing the distinction between an economic connection and a reusable research warning.
6. A draft prospective R4 evaluation protocol, explicitly marked NOT_RUN.
7. Full validation results, including regression tests.
8. A final critical review identifying what is still unverified.

Commit and push the implementation to the feature branch when tests pass, reporting the commit SHA and exact files changed. Leave `main` untouched.

### The standard we're aiming for

Graph v1.1 should be able to say:

> "These two investigations shared an unresolved measurement requirement, so here's a relevant historical warning."

Without pretending that means:

> "These two economic events are connected."

And when there really is a documented relationship, it should explain precisely what connects the records, what is established, what remains unknown and why further investigation may be worthwhile.

**The objective is fewer meaningless economic connections, stronger grounded discovery and better use of accumulated research knowledge—not prettier metrics.**
