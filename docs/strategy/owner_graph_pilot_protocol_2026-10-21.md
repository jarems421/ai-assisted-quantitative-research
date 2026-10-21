# Research OS — Correct and Finalise the Discovery Lab + Graph Pilot Protocol

The Graph v1 preflight has been completed and committed at `942650a`.

The implementation is accepted as the engineering baseline, but the proposed pilot needs one final methodological correction before activation.

**Task: fix the pilot protocol and any small, demonstrably necessary evaluation-code defects. Do not initiate scientific-source acquisition or start a live campaign.**

Read `AGENTS.md`, the current Graph and Discovery Lab code, `graph_pilot_preregistration.md`, `proposed_owner_graph_pilot_authorisation.md`, the review documents and existing source stops.

## 1. Correct the time-cutoff problem

The proposed commands use `--known-at START_UTC`, but Graph v1's prefix replay excludes observations appended later in the campaign.

Implement and test a correct approach that separates:

- Frozen prior knowledge available at the start of a campaign.
- New records legitimately appended within the active campaign.
- The current time of a graph query.
- Any information acquired after the permitted query time.

A current observation must be available to `revisit`, `complements` and `suggestions` without allowing future knowledge or other-arm records to leak in.

Do not simply remove all temporal controls.

Use explicit, reproducible input snapshots or a similarly auditable solution.

## 2. Ensure genuinely equivalent starting knowledge

For each matched packet:

- Give both S and G the identical frozen packet.
- Give both the same frozen historical-research memory.
- Give both identical access to prior knowledge permitted by the protocol.
- Keep each arm's new findings, notes and ledgers separate.
- Do not let earlier experimental arms create an unintended information advantage in later comparisons.

If this requires revising the handling of previous pilot ledgers, document the decision clearly.

## 3. Strengthen blinding

Separate campaign execution from adjudication as far as practicable.

Ensure the adjudicator receives shuffled, arm-hidden connection records with equivalent provenance.

Acknowledge any residual leakage arising from the same human owner supervising multiple arms.

Do not claim complete blinding where it cannot be achieved.

## 4. Revise the decision rules

Do not automatically retire graph discovery operators solely because four packet pairs produce zero graph-only connections.

Evaluate graph value across several independent dimensions:

- New verified connections
- False or premature joins avoided
- Time saved in evaluating a connection
- Time to decisive falsification
- Duplicate research avoided
- Additional human review burden
- Original frozen M passes per analyst-hour

Keep all analyst time, including graph querying and suggestion review, in the primary denominator.

Graph-only connections are valuable but not the only form of useful incremental benefit.

Describe success, failure and inconclusive results without inventing statistical certainty.

## 5. Tighten packet eligibility

An HTTP 200 response alone is insufficient.

A source environment must provide a demonstrably usable, original, dated record route with relevant fields and stable identifiers.

Fix the exact selection and fallback rules in advance.

Preserve neutral, outcome-blind packet selection. Do not cherry-pick records that make the graph look useful.

All existing source stops remain binding.

## 6. Perform a complete offline dry run

Before activation, run a synthetic end-to-end rehearsal of:

- Frozen packet creation
- Both arm inputs
- Query-time visibility
- Cross-arm isolation
- Search baseline
- Graph-assisted query
- Candidate freezing
- Suggestion logging
- Human adjudication format
- Budget accounting
- Paired reporting

Prove specifically that observations appended after campaign start remain queryable by their own arm while later or other-arm data are unavailable.

Confirm that the correct commands actually execute against the implemented CLI.

## 7. Scope, authority and delivery

Keep the proposed pilot at four packets and eight campaigns unless there is a clear reason to recommend a smaller separate operational shakedown.

Retain the 18-hour, 60-source-start and 88-MiB aggregate ceilings as proposed maximums, not standing authorisation.

You may make narrowly necessary offline code, test and documentation corrections, then commit and push them following repository conventions.

Run the full relevant tests and report actual hosted CI status where available.

Preserve Discovery Lab v1, Graph v1's core architecture, Measurement Gate M, experiment records, source stops, F19 HOLD and SH09 STOP.

Do not build Graph v2 or Discovery Lab v2.

Do not activate the proposed owner authorisation.

Do not fetch external scientific sources, open market data, run backtests or begin the pilot.

## Final deliverables

Produce:

1. Updated preregistration and owner-authorisation proposal.
2. Exact list of methodological corrections.
3. Working synthetic dry-run results.
4. Proof of equivalent starting inputs and correct temporal visibility.
5. Tests and validation receipt.
6. Commit and CI verification.
7. Clear instructions for the owner's final activation decision.

**Stop after the corrected protocol is delivered. The owner will separately decide whether to activate it.**
