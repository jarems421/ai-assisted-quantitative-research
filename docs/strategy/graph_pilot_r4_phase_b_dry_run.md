# Graph Pilot R4 Phase B: synthetic dry run (dual human adjudication)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**NOT an R4 run.** Synthetic fixtures only, offline, in a temporary directory and a throwaway git repository. The two reviewers, the operator and the owner are labelled fixture stand-ins: no real person adjudicated and no AI judgment is used. Regenerate with `python -m src.research.graph pilot r4-phase-b-dry-run --write`; `--check` compares.

| Area | Check | Observed | Result |
|---|---|---|---|
| conformance | P1 conforms to the registered R4 configuration; P2 (v1.1) is recorded as non-conforming | P1 conforms; P2 conforms=false | PASS |
| exposure | a row without an exposure declaration is refused | refused: fields must be exactly | PASS |
| exposure | saw_arm_info YES without listing arm-identifying material is refused | refused: saw_arm_info must be YES exactly when | PASS |
| exposure | each declaration maps to its item status | {'arm ledger seen': 'POTENTIALLY_UNBLINDED', "the other reviewer's judgments seen": 'NOT_INDEPENDENT', 'an AI assessment seen': 'NOT_INDEPENDENT', 'arm operation declared': 'CONFLICTED'} | PASS |
| exposure | a reviewer who attested an arm session is CONFLICTED, whatever they declare | CONFLICTED (matched to a session attestation) | PASS |
| exposure | an assistant cannot adjudicate | refused: an assistant cannot adjudicate | PASS |
| separation | an economic log cannot judge a warning item (usefulness is separate) | refused: not an unadjudicated CONNECTION item | PASS |
| usefulness | USEFUL_LESSON_REUSED must state the avoided action | refused: states the action the lesson changed or avoided | PASS |
| sealing | a seal is immutable | refused: already sealed | PASS |
| sealing | a log edited after sealing is refused | refused: changed after sealing | PASS |
| dual | two sealed reviewers give a consensus with agreement statistics | outcome agreement 3/4, kappa 0.6 | PASS |
| dual | a disagreement stays UNRESOLVED_DISAGREEMENT (never resolved by an AI or operator) | 1 disagreement: PLAUSIBLE_UNVERIFIED vs REJECTED_TRIVIAL | PASS |
| dual | git reveal order verified (seals committed before logs) | VERIFIED | PASS |
| usefulness | usefulness has its own agreement and consensus | usefulness kappa 0.0; R1 reused vs R2 not used: UNRESOLVED | PASS |
| dual | a log revealed before the other reviewer sealed is a reveal-order violation | R1 economic log was committed before R2 sealed | PASS |
| dual | R1 and R2 must be two different humans | refused: two different humans | PASS |
| dual | a single sealed reviewer is not dual adjudication | ADJUDICATION_NOT_DUAL | PASS |
| dual | a prospective packet cannot be unblinded before both reviewers seal | refused: only after both reviewers have sealed | PASS |
| dual | seals and logs first appearing in the same commit are a reveal-order violation (strict ancestry) | R1 economic log first appears in the same commit as the R2 seal | PASS |
| conformance | no deviation record can admit a packet to the primary comparison | refused: can never enter the primary | PASS |
| zero items | a zero-row packet has an empty frozen export | 0 items | PASS |
| zero items | a reviewer must still write both logs, explicitly empty | refused: explicitly empty | PASS |
| zero items | a zero-item seal still needs a reviewer-level exposure declaration | refused: exposure must have exactly | PASS |
| zero items | two different sealed reviewers, verified reveal order and explicit zero denominators; the packet conforms | DUAL_SEALED, 0 items, reveal VERIFIED, kappa UNDEFINED_ZERO_DENOMINATOR, CONFORMING | PASS |
| zero items | the zero-row packet is reported and enters the primary comparison with zero counts, not dropped | in primary; G verified 0, review items 0, adjudicator minutes 0 | PASS |
| dual | a log whose committed history holds other content (a placeholder first) is a violation, not VERIFIED | R1 economic file: committed history does not hold only the sealed content | PASS |
| dual | a seal rewritten after its first commit is a violation, even though it still validates | VERIFIED -> VIOLATED: R1 seal file: committed history does not hold only the sealed content | PASS |
| conformance | only the conforming packet enters the primary comparison; the non-conforming one is listed with its owner deviation | P2 excluded: ['NON_CONFORMING_CONFIGURATION', 'REVEAL_ORDER_VIOLATED']; deviation preserved | PASS |
| usefulness | usefulness is reported separately and never counted as an economic discovery | G usefulness assessed 1 (unresolved 1); economic discoveries 1 | PASS |
| report | one conforming pair stays INCONCLUSIVE | INCONCLUSIVE | PASS |

## Agreement (P1)

| Judgment | Items | Agreements | Raw agreement | Cohen's kappa | Disagreements |
|---|---:|---:|---:|---:|---:|
| outcome | 4 | 3 | 0.75 | 0.6 | 1 |
| economic_meaning | 4 | 3 | 0.75 | 0.6 | 1 |
| usefulness | 1 | 0 | 0.0 | 0.0 | 1 |

- Consensus rule: an outcome counts only where both reviewers agree; otherwise UNRESOLVED_DISAGREEMENT, never resolved by an AI or operator.
- Reveal order: VERIFIED.
- Primary comparison: 1 conforming packet pair(s) in the primary comparison; 1 excluded and listed.
- 30/30 checks passed.
