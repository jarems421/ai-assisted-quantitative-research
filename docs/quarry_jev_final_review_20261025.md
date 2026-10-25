# Quarry/Jev final review and integration — 2026-10-25

Offline engineering only. No provider, authenticated model-list, source, paid service,
experiment, real human label, M/H decision or study activation was performed. Nothing
in this review authorises one. PRs #35/#36 remain drafts; neither is merged here.

## Baseline and inherited Forge finding

GitHub confirmed the owner merged PR #37 on 2026-10-25 at
`543129c52397af013088daec00d99193e87de3d1`. Its reviewed head was
`0ec4a1f97dab59a53f52a439c1d09ff9202a4932`, with Windows/Linux offline and public CI
all green. Actual origin/main was fetched, rather than treating the PR head as main.
Quarry was merged onto that main; Jev was merged onto the revised Quarry branch.
No history was rewritten or force-pushed. The inventory merge preserves every main
entry, adding only the Quarry/Jev declarations. Final-head CI is recorded in the PRs;
old-base green checks are not evidence for the integrated heads.

The additional Forge concern is **confirmed in merged code**. `finalisation()` branches
on whether `report_sha256` is a dictionary, without checking the receipt schema. A
throwaway synthetic check (mocked stage/Markdown readers; actual temporary hashes)
produced VERIFIED for a V001-labelled receipt with otherwise matching V002 bindings,
and LEGACY_RECEIPT_UNBOUND for a V002 receipt missing that binding. No Pilot 001 file
was read, rewritten, regenerated or repaired for this check.

Because #37 was already merged, this assignment does not change Forge. The separate
Forge worktree also had pre-existing uncommitted edits; these were left untouched and
not imported. Smallest proposed prospective follow-up: branch explicitly on the exact
receipt schema; accept V001 only as legacy (refuse unexpected V002 binding fields),
require V002 binding fields before verification, and classify unknown/missing schemas
as unverified. Add synthetic regressions for the two cases above and unknown schemas;
keep the actual historical V001 receipt byte-identical. This inherited issue needs a
separate authorised Forge correction, not an overlapping change in these PRs.

## Confirmed defects corrected

| Finding | Correction |
| --- | --- |
| Quarry `usable` conflated identity flags with inspection/access | Preserve its legacy meaning explicitly; add retained-copy inspection eligibility, negative-metadata eligibility, restrictions/stops and acquisition permission (always false). Stopped retained copies remain inspectable; unavailable originals are not called usable originals. |
| Extraction assurance was insufficiently visible | New human handoff V002 names original/text hashes, extraction mode and claimed method/location, coverage/missing fields, restrictions, UNKNOWN authenticity and UNVERIFIED supplied-extraction accuracy. Legacy V001 handoffs remain loadable unchanged. |
| Failed Jev attempts were scored using fallback order | Evaluation V002 emits null model-ranking metrics and unknown abstention rates for unusable attempts, preserves both baseline diagnostics and explicitly counts/retains failures. |
| Provider metadata could copy arbitrary JSON/strings | Whitelist reviewed model IDs and bounded integer usage; otherwise UNKNOWN/fixed faults. Re-derive the safe metadata on report load, including invalid attempts. Requested identity, provider-reported identity and unverified runtime identity are separate. |
| HTTP IncompleteRead could hold un-emitted partial bytes | Preserve those partial bytes in private raw capture before recording only the exception type. No repair or successful classification follows. |

Focused regressions exercise stopped routes, unavailable originals, identity mismatch,
valid copies, binary-original extraction/page claims, V001 compatibility, malformed
responses, recognised model drift, HTTP failure, transport failure, refusal,
interruption, valid responses, arbitrary/nested/credential-shaped metadata, out-of-bound
usage, and safe report loading. All original raw responses remain unchanged.

## Accepted limitations and future enhancements

- Hashes/create-only storage detect inconsistency, not coordinated replacement of all
  local files. Filesystem ownership and independent human identity remain external.
- Supplied extraction is not an independently verified representation of a PDF. No
  general PDF/OCR subsystem is added; human original inspection remains necessary.
- Historical stops outside the new registry are not reconciled by the disabled planner.
  Future activation must inspect ledger/campaign/private stop records, including
  host-wide and unclear-scope restrictions. A new ID or equivalent URL cannot reopen
  an earlier denial. There is no source dispatcher.
- The provider's socket inactivity timeout is not a strict total wall-clock deadline.
  A trickling peer can extend total time. Plans now expose that fact; a strict deadline
  is future transport work, not an assurance supplied by these offline tests.
- A byte-size payload bound is not verified tokenization. Provider context errors stay
  failed attempts. Account/version availability, effective pricing, hard billing cap
  and actual charges remain unverified without independent owner evidence.
- Synthetic labels/answers exercise diagnostics only. They do not establish Jev
  usefulness, accuracy, source authenticity, economic meaning or scientific readiness.

## Official integration boundary reconfirmed

Public documentation only was rechecked on 2026-10-25. The
[System One reference](https://docs.typesafe.ai/api/system-one) still specifies the
fixed POST endpoint and supplied state/questions/model. The
[Choice specification](https://docs.typesafe.ai/primitives/choice) and
[confidence formula](https://docs.typesafe.ai/confidence) support the current strict
yes/no/unsure schema, distributions, argmax and tie/abstention handling. The
[models reference](https://docs.typesafe.ai/models) lists the two pinned versions,
64k/32k default request/question context limits, input-token pricing and free output.
These documented facts do not verify an account or authenticate a runtime. There was
no authenticated request, model-list call or model substitution.

## Authored review changes: every file and reason

| PR | File | Why |
| --- | --- | --- |
| #35 | `src/research/quarry_v1/evidence.py` | Explicit status scopes and versioned human extraction handoff; legacy validation retained. |
| #35 | `src/research/quarry_v1/acquisition.py` | Machine-readable NOT_PERFORMED stop reconciliation and no new-ID bypass. |
| #35 | `tests/test_quarry_v1.py` | Status/extraction/page-claim and legacy-handoff regressions. |
| #35 | `docs/quarry_v001.md` | Explain output semantics, unverified extraction and required historical stop review. |
| both | `tests/offline_inventory.json` | Preserve all merged Forge entries; register exact reviewed Quarry/Jev test methods. |
| #36 | `src/research/jev_navigation_integration_v1/provider.py` | Bounded whitelist metadata; explicit inactivity timeout; retained partial HTTP bytes. |
| #36 | `src/research/jev_navigation_integration_v1/workspace.py` | Safe metadata at dispatch/report and truthful machine-readable transport limits. |
| #36 | `src/research/jev_navigation_integration_v1/evaluation.py` | Separate failed attempts/baselines from actual model-assisted metrics. |
| #36 | `src/research/jev_navigation_integration_v1/demo.py` | Required adverse demo: two originals, independent outcome, poorly ranked falsifier, decoy, ambiguity, unavailable/stopped route and pending human inspection. |
| #36 | `tests/test_jev_navigation_integration_v1.py` | Adversarial metadata and evaluation-failure regressions; retained adverse record universe. |
| #36 | `docs/jev_navigation_provider_v001.md` | Explain corrected metrics/metadata and accurate timeout boundary. |
| #36 | `docs/quarry_jev_final_review_20261025.md` | This review, findings, baseline evidence, file list and remaining prerequisites. |

The nine paths imported from #37 (AGENTS.md; its automation guide; automation
credentials/execution/pipeline/providers; inventory; and the two Forge test modules)
are baseline changes, not authored Quarry/Jev corrections. Compare frozen Scout,
Forge, Discovery, Graph, Level A and historical research paths directly with merged
origin/main: these PRs add no changes to them.

## Architectural alignment and stopping point

Forge generates/critiques; Quarry retains potential evidence; Jev allocates inspection
attention over that supplied universe and existing Armoury/Graph memory. Deterministic
Discovery blockers and source stops win. Humans/The Anvil inspect originals, actual
measurements, independent outcomes, timing and eligibility. Existing Armoury records
remain the source of conclusions/failures/provenance. Crucible/Whetstone/Temper need
separately qualified evidence and evaluation controls. Neither new package grants
M/H, appends a campaign, promotes Scout cards, certifies first-public time, upgrades
graph connectivity to economic transmission or manufactures a human approval.

The adverse demo keeps every record, including a deliberately missed important
falsifier and a STOPPED unavailable source. Both existing keyword/Graph baseline and
an explicitly supplied independent-search/analyst ordering use the same frozen
universe/budgets; the demo's analyst ordering/labels are designer controls, not humans.
Real human time accounting, independent assembly and source judgments stay external.

No new crawler, ML, embeddings, dashboard, PDF platform or autonomous agent is needed
or added. After current-head tests/CI and the synthetic demo pass, stop here. Exact
heads, bases and final results are recorded in PR #35/#36 descriptions. The inherited
Forge schema issue above remains a separate owner follow-up; no Quarry/Jev actuation
uses that verifier. Before a real Quarry/Anvil exercise: explicit local material/scope,
historical stop review if acquisition is proposed, human originals/extraction inspection,
exact study and existing M/owner/trust gates. Before live Jev: independent frozen labels,
exact payload/disclosure approval, account/version/pricing/hard-cap evidence, stopping
arrangements (including any required strict deadline), and separate owner activation.
