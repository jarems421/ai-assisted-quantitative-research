# Graph Pilot R4: operational readiness assessment (version 001)

> **R4 is NOT_RUN, not activated and not authorised.** This assessment covers offline preparation only. No source was fetched, no arm was operated, no reviewer was recruited, and no hosted-model research ran.

Package: [reviewer guide](graph_pilot_r4_reviewer_guide_v001.md) · [runbook](graph_pilot_r4_runbook_v001.md) · [source plan](graph_pilot_r4_source_plan_v001.md) · [activation template](graph_pilot_r4_activation_template_v001.md). Base: `main` `9ac56d33e6b3a7e97dfc3c56faf0e91ef0edeb92`; post-merge public CI passed.

## Readiness matrix

| Area | State | Evidence or what is missing |
|---|---|---|
| **Engineering, implemented and independently verified** | READY | Phase A: implementation pin, effort evidence, suggestion accounting, provenance, configuration V002. Phase B: dual sealed review, exposure, usefulness, conformance, zero-item packets, content-verified reveal order. Owner-reviewed PRs #3 and #6 were merged with merge commits and CI passed |
| **Synthetic evidence** | EXISTS | Phase A rehearsal (51 checks), Phase B rehearsal (30), v1.2 holdout and mutation suites. These are **synthetic, self-written functional checks only**: no evidence that Graph improves real research |
| **Operational documents** | DRAFTED (this package) | Checked against the code: every `pilot` command and flag in the documents exists in the CLI (15 subcommands), and the reviewer-guide row templates match the validators' exact fields and labels. A reviewer-bundle seal, made without any arm files, validated in the full packet (offline synthetic check) |
| **Human arrangements** | MISSING | Two independent reviewers (recruited, briefed, confirmed); arm operator(s); a blinding preparer; a decision on the arm analyst type (D1); a schedule with a review window |
| **Owner decisions** | PENDING | D1, F1, F2, U1, R1 and the ceilings, consensus rule, blinding treatment and mechanism statement (below) |
| **Source questions not answerable offline** | OPEN | Whether any candidate route exists, is keyless, has terms permitting retrieval, is size-safe, carries identifiers and the required fields, and is free of overlap. All candidates are `CANDIDATE_UNVERIFIED` |
| **Conditions preventing activation** | PRESENT | No completed activation document; no named reviewers; no frozen R4 environment or recorded runtime; private-receipt overlap audit not done; no publisher-terms confirmations; no hypothesis-first mechanism statement |

## Decisions the owner must make (before activation)

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| **D1** | Who are the arm analysts? | (a) Fresh AI-assistant sessions supervised by a human operator, as in R3. Activation must explicitly authorise hosted-model use for arms. "Analyst minutes" then measures session time. (b) Human analysts | Choose one type for both arms of every packet. (a) is reproducible with the existing arm instructions. (b) answers a question closer to "does it help a human researcher?" Owner's choice |
| **F1** | Freshness level | (a) Strict: no reused host. This risks the relationship packet. (b) No reused record, filing set or exact route, verified by an overlap audit | (b), registered before any probe |
| **F2** | Reserve depth | Two environments per method (revision 2), or three with a matching packet-freeze start ceiling | Decide at registration, never after a failure |
| **U1** | Can a plain `METHODOLOGICAL_WARNING` be scored `USEFUL_LESSON_REUSED`? | The blinded item shows no arm action. Either (a) keep the guide's rule: only items that document the avoided action, which in practice means AVOIDED_REPEAT; or (b) add a registered way for arms to record the action a warning changed | (a) for R4. (b) would be a new design |
| **R1** | May reviewers fetch missing originals? | (a) No: missing evidence means `PLAUSIBLE_UNVERIFIED` or `CANNOT_ASSESS`. (b) Yes, receipted, within a reviewer ceiling | (a); the evidence pack should be complete |
| — | Consensus rule, blinding treatment, ceilings, schedule, people, routes, mechanism statement | Register or amend as proposed in the template | — |

## Contradictions and ambiguities found

1. **The adjudicator count.** The protocol draft says "at least one adjudicator … two preferred". The merged code requires two valid seals for conformance. The activation template states the code's rule and that it supersedes the draft wording; the owner should confirm it at registration.
2. **The leak scan needs `--own-from`.** Without the V001 export as `--own-from`, `pilot leak-scan` cannot detect arm-own record ids, which was the R3 failure. The runbook makes it mandatory; the R4 protocol draft does not mention it.
3. **Reviewer access to originals.** The protocol says reviewers adjudicate "against originals", but arm-fetched originals sit in arm-identifying paths. The runbook resolves this procedurally with a content-addressed evidence pack, built by a preparer who never reviews.
4. **Key location.** `pilot blind --key` writes the key wherever directed, but `unblind` and `report` read `<packet>/key.json`. The key stays outside the repository until both seals are committed, then is placed and committed. This is procedural only: the owner can always read it.
5. **Name-conflict check timing.** Sealing in a reviewer bundle cannot see the session attestations, so the attester-name conflict check runs when `adjudication-agreement` or `report` reads the full packet. It is still enforced before any comparison.
6. **The freshness rule versus feasibility** (source plan F1 to F3): stated, not weakened.
7. **Usefulness of warnings** (U1): ambiguous under the current schema.

None of these needs new engineering. Each is either procedural or an owner decision.

## What a four-packet R4 can and cannot conclude

**It can:**

- describe, for this sample, whether Graph assistance changed verified economic connections per analyst-hour, false or premature joins, time to decisive falsification, duplicated research avoided, original frozen M passes, review burden and warning usefulness;
- give a descriptive classification, if at least three comparable conforming pairs exist and the effort and blinding gates support it.

**It cannot** give statistical significance, a generalisable effect size, an investment edge or return claims, or proof of reviewer independence. Session variance is confounded with arm (one session per campaign).

## Exact next human actions

1. **Owner:** decide D1, F1, F2, U1 and R1, and the ceilings.
2. **Owner:** recruit two independent reviewers who will not operate or attest any arm, and name a blinding preparer. Brief the reviewers with the reviewer guide.
3. **Operator:** complete the private-receipt overlap audit. Read the publisher terms for each shortlisted environment, offline, from published terms pages only, without probing data routes.
4. **Owner:** write the hypothesis-first mechanism statement.
5. **Owner:** complete the activation template and commit it as `owner_graph_pilot_r4_<date>.md`. Only then may Stage 1 (frozen environment) and Stage 2 (preflight) begin.
