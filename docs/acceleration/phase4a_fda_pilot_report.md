# FDA pilot: source-frame stop

**FDA_FAMILY_REJECT. Gate 1 FAIL_CLOSED; FRAME_UNCERTIFIED_NEGATIVE_ROUTE_UNAVAILABLE.** As of 2026-10-13. Five source requests established approval-oriented documentation but no outcome-complete historical decision denominator. This rejects the audited frame/routes, not every possible FDA source or the economic relevance of regulatory decisions. No event, prices, strategy or experiment was created.

## Frozen routes and preserved continuation

Original manifest SHA-256 `6014f0841b91a25be9640acad801c5f03bace49f64fabfe80d0919278fc3f69d`; [continued exact manifest](phase4a_fda_frame_manifest_v002.json) SHA-256 `056ba94081b3b1b0ad2514d98f28e257bffe16f2c6cd478634828cee7ca8ef43`. The [owner instruction](owner_fda_pilot_2026-10-13.md) authorized at most ten Gate 1 starts; the [follow-up](decisions/fda_gate1_continue_reply_001.md) continued that scope. Version 2 was committed before dispatch and changed only the official landing route, using the acquired data-file page's HTTP href with a declared HTTPS scheme upgrade. It did not claim to know the original redirect target.

| Route | HTTP | Original bytes |
| --- | ---: | ---: |
| https://open.fda.gov/apis/drug/drugsfda/ | 200 | 120359 |
| https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files | 200 | 34324 |
| https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process | 302 | 15991 |
| https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm | 200 | 38244 |
| https://www.fda.gov/drugs/drug-approvals-and-databases/complete-response-letters | 404 | 14495 |

The original overview request returned HTTP 302; its body, error and stop remain unchanged. An explicit hash-checked review permitted only the separately frozen FDA routes. It reused the same archive, reservations and ceilings. The secure official landing page then returned 200. The exact negative-letter documentation route returned 404, so acquisition stopped immediately: F05 remains unvisited. Neither 302 nor 404 is a 403/429 access denial. The 404 establishes only that this URL was unavailable, not that all negative FDA letters are absent. No redirects, proxy, mirror, procurement retry or alternative host was used. No remaining budget was spent after this stop.

The original automated FDA_FAMILY_REJECT draft and subsequent [incomplete-audit REDESIGN review](phase4a_fda_disposition_review.json) are retained. The [new scientific disposition](phase4a_fda_disposition_review_v002.json) records this completed bounded continuation separately. [Version 2 source registry](phase4a_fda_source_registry_v002.json) and [frame review](phase4a_fda_frame_review_v002.json) retain all five response hashes, lengths, retrieval/request times and normalized source locators. Original response bodies remain private and immutable; present-day retrieval is historical reconstruction, not contemporaneous public availability.

## Denominator findings

| Gate 1 question | Evidence / limit |
| --- | --- |
| Q1 | Drugs@FDA/openFDA describe approved products; official monthly reports cover CDER approvals/tentative approvals, not CBER approvals. |
| Q2 | Approval-oriented universe explicitly documented; tentative approvals are not a complete never-approved/unresolved risk set. |
| Q3 | Not established. The exact negative-letter documentation URL returned 404; this does not prove negative decisions or other official archives absent. |
| Q4 | UNKNOWN: no complete pre-outcome application census established. |
| Q5 | PARTIAL_DOC_ONLY: NDA/BLA/ANDA, originals/supplements and tentative/final report distinctions documented. Withdrawal/discontinuation/other action coverage unresolved. |
| Q6 | Database update cadence and submission-status date fields are distinct; none is certified first-public time. |
| Q7 | These acquired response bytes are immutable. Historical original application/action document versions not tested; landing page describes most recent approved labeling. |
| Q8 | UNKNOWN: current database/API transformation does not establish historical revision replay. |
| Q9 | FAIL_CLOSED: no certified outcome-complete historical eligible denominator under these audited routes. |
| Q10 | NOT_CERTIFIED: approval/tentative-only reports and generic sector peers do not repair future-outcome conditioning. |

The twelve months are conditional Gate 2 slots, not twelve observed empty months. Gate 2 did not run; no event manifest, application/action census, public/private mapping, rights-holder/security mapping, timestamp or cluster geometry was created. Missing source coverage is unavailable, never a zero count of FDA decisions. Tentative approvals or previous negative actions of eventually approved applications cannot establish complete never-approved/unresolved coverage. The stronger claim OUTCOME_SELECTED_SOURCE_FRAME for every possible official FDA route is not made from this incomplete alternative-source evidence.

## Pilot questions and design limits

Q1 authoritative historical source access is partial; Q2 outcome completeness is not certified; Q3 regulatory-action replay is untested (our new documentation bytes alone replay); Q4 public timing is unavailable; Q5 applicant/rights-holder and Q6 historical security mapping were not tested; Q7 clustering is not measured; Q8 anticipation requires future scoped evidence; Q9 outcome-independent comparisons are not certified; Q10 expansion is rejected under this frame.

Application acceptance/decision schedules, advisory committees, priority review and prior communications would be needed to assess anticipation; no anticipation dataset was built. Contemporaneous applications require an outcome-independent risk set; scheduled cohorts require independently dated schedules; therapeutic peers face therapy/calendar confounding and outcome selection; within-issuer contrasts retain issuer, repeated-product and programme dependence. No control was selected and no causal claim is made. Raw actions, applications, products, sponsors, economic clusters and effective independent sample size remain unmeasured. No market-based power or return was calculated. Regulatory date, document date, current update time and first-public time remain distinct. No FDA timing policy or SEC policy reuse was approved.

## Verification and stop

Validation: 296 local tests; 70 public tests; zero skipped. [Validation receipt](phase4a_fda_validation.json). Reconcile archived hashes and regenerate with `python -m src.research.fda_pilot report --check`; it makes no network request. Acquisition and reviewed continuation are separate explicit remote mutations, not reproduction. Completed results are retained and never blindly resubmitted.

Five starts, zero retries, of Gate 1 maximum ten and total conditional maximum sixty. SEC, OpenFIGI, prices, procurement, Nexus, Aurora and source browser search all zero. No purchase/upgrade; account-wide debit is unknown. Git/hosted-CI metadata are delivery checks recorded separately. Existing procurement, Phase 3, frozen experiments, EXP004 pause, EXP005 abandonment/absence, candidate scorecard and inactive approved policies are preserved. The shared collector gained a reviewed-stop hook; its procurement default still rejects a stopped route, and original acquisition-code hashes remain pinned to their historical Git checkpoints.

**Stopped after the FDA source-only pilot.** No larger FDA campaign, approval-only event sample, EXP006, Phase 4B/4C, graph, causal lab or paper/live activity is authorized. No decision is needed to record this negative pilot. The next optional owner decision is whether to authorize a separately bounded merger-enforcement pilot, the last of the original three families. It does not launch automatically; after that family the repository must stop and reassess rather than continue family shopping.
