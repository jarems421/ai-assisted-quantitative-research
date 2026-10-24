# Jev shadow-critic retirement and compatibility map

**Decision from the owner's 2026-10-24 task: LEGACY_RETIRED — NOT ACTIVE.** Jev is Research Navigation Intelligence, not a third Forge critic, shadow scientific reviewer, screening model or competitor to Sol/Argon. No former critic calibration or proposed role is a future activation path. This retires the role prospectively; it does not rewrite historical evidence or remove general human review.

## A. Operational paths safely retired

| Path | Prospective disposition | Compatibility retained |
| --- | --- | --- |
| `post_generation.cli import-response` | Real imports refused before opening an archive or reading a response. CLI help and errors identify retirement. | `--synthetic-fixture` still exercises the existing validation/provenance contract on synthetic batches only. |
| `post_generation.review.import_response` | API also refuses unless both fixture batch and transport are synthetic, preventing an ordinary CLI bypass through this non-frozen helper. | Existing saved records, parsing rules, schemas, packet seals, raw-byte comparisons and historical report functions are preserved. |
| `critic_v1.cli jev-compare` | Default invocation refused before workspace access. It is no longer a proposed screening workflow. | `--legacy-replay` explicitly allows an archived descriptive report, with a retired/historical-only CLI wrapper. The old versioned report body and its counterfactual counts remain historical, not recommendations. |
| `post_generation compare` | Removed from prospective workflow recommendations and labelled retired in help/results. | Read-only replay of old records is still available. No new Jev response is obtained or imported. |

The new navigator neither imports nor calls any of these paths. Retiring them authorises no replacement provider call.

## B. Frozen implementation, records, tests and schemas preserved

| Component | Why retained; current meaning |
| --- | --- |
| Top-level Scout `providers.py`: `JEV_MODEL`, `QUESTIONS`, `shadow_request`, `validate_shadow`, `JevShadowClient`; top-level `cli.py`, `engine.py`, `evaluation.py`, `v003.py` and archive validation | Every top-level Scout `.py` is inside frozen V004/N1 implementation boundaries. Physical removal or edits invalidate approved packages. `shadow-request`/`shadow-import` and the dormant client remain compatibility code, **not active or authorised future interfaces**. No new permission can be inferred from their availability. |
| `post_generation.review` packet/label/provenance version constants and reviewer text; `post_generation.__init__` | Existing packets hash all reviewer-facing text and require unchanged derivation. The generic independent human label packet, label validation and review functionality remain useful and unchanged. The only changed helper behavior is prospective import retirement, outside old replay rules. |
| `critic_v1/jev.py`, `critic_v1/evaluation.py`, `critic_v1/policy.py` | Frozen descriptive comparison semantics, archived exclusions and safeguards that Jev never enters critic policy remain. Counterfactual screener/escalation counts are historical calculations, not an activation recommendation. General critic human calibration stays separate and is not retired. |
| Frozen V001–V004/N1, observers, `v004_r3`, hosted acceptance package and Graph/Discovery implementation closures | No source edits. Graph roots include all Graph/Discovery modules plus their static import closure; the standalone navigator does not become a dependency of those roots. No Graph fixtures, historical classifications, holdout or source stops are changed. |
| `critic_v1/resources/manifest.json`, frozen scientific/economic/adversarial texts, evaluation protocol/schema and saved responses/archives | All retained byte-compatible. No archive or result is deleted, re-scored, relabelled or migrated. Nothing uses a Jev opinion as a human anchor. |
| Existing `test_scout.py`, `test_shadow_review.py`, `test_ai_critic_v1.py` and frozen package tests | Preserved as compatibility checks, not proof the retired role remains active. The old five-question hash and historical model pin stay unchanged. New retirement tests live separately. |

The top-level dormant client cannot be physically disabled here without changing a frozen contract. Its legacy approval surface is **not** new authority to use it. This is the exact unavoidable coexistence: frozen interfaces and replay remain, current plans and the safe non-frozen prospective imports are retired. A future physical removal requires a new reviewed compatibility version, not a stealth hash refresh.

## C. Current documentation updated prospectively

- [Research OS contracts](../research_os.md), [master plan](../acceleration/master_plan.md), [architectural roadmap](../strategy/forging_an_edge_roadmap.md) and [Scout operator entry point](../opportunity_scout/README.md) identify navigation as Jev's current role and remove active shadow-critic recommendations.
- The README source template and regenerated repository README link navigation as a read-only cross-cutting aid. No new architecture diagram depicts Jev as a hypothesis critic.
- A narrowly appended AGENTS note identifies this role decision; all other research boundaries remain in force. The test inventory receives one new module entry only, avoiding active Forge test entries and PR #31's separate additions.

## D. Historical documents retained unchanged, superseded here for Jev's role

| Historical document/record | Superseded prospective portion |
| --- | --- |
| `docs/opportunity_scout/jev_post_generation_readiness_v001.md` | First real shadow comparison checklist, new shadow response imports and future shadow activation. Its independent human review/handoff explanation remains historical useful context. |
| `docs/opportunity_scout/ai_critic_v001.md`, section 5 and Jev prerequisites elsewhere | Jev alongside critics, candidate screener/disagreement/escalation roles and a genuine Jev critic study. Scientific/economic criticism, independent human anchors and all safeguards remain. |
| `docs/opportunity_scout/ai_critic_v001_calibration_protocol.md`, “Choosing a Jev role” | Human-versus-Jev critic calibration and selection among five future screening roles. General critic calibration is not superseded. |
| `docs/opportunity_scout/jev_instrument_v002_proposed.json` | Proposed additional critic questions and activation/evaluation plan; now retired, not registered, never reinterpreted as navigation. |
| `docs/opportunity_scout/design.md`, `evaluation_protocol.json`, `acceptance_review.md`, `acceptance_validation.json`, `v003_validation.json` | Original optional shadow integration/validation checkpoint. In particular `design.md` is hashed by V003; its wording must stay unchanged. |
| `docs/opportunity_scout/owner_ai_critic_v001_2026-10-23.md` | Historical owner scope; it is not edited into a new authorisation. The newer strategic direction supersedes only future Jev-role planning. |
| `walkthrough.md`, `synthetic_demo.json`, `operator_example/report.json`, `first_comparison_v002/README.md`, `claude_v003_powershell.md` | Historical examples, optional Jev steps and archived model pin. Replay/example provenance stays intact; commands are not a new operational recommendation. |
| N1 admission/stop audit documents and any archived experiment/source material mentioning Jev | Historical analysis/records retained. Their scientific dispositions, stop scopes and model-exposure facts are not changed. |

Dependency search covered `src/`, `docs/`, `config/`, tests and the current README/template for Jev, TypeSafe, shadow critic, five-question review and calibration references. Active policy exclusions such as `jev_used: false` are safeguards to retain, not invitations to reactivate the critic. New navigation evaluation is defined independently in [its protocol](evaluation_protocol.md).
