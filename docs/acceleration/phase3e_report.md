# Phase 3E: experiment feasibility and scope stop

**EXP005 feasibility: REDESIGN_REQUIRED. Freeze: NOT_READY.** This new phase began from `081dfe6` on 2026-10-12 and stopped at the owner-required date-scope gate before acquisition or new calibration. The [frozen plan](phase3e_plan.md) is a distinct Phase 3E artifact. Previous Phase 3D reports/results remain unchanged.

The [owner request](owner_phase3e_2026-10-12.md), section 37, explicitly requires: “Stop early and report” when “The availability-policy scope is incompatible with the required historical design.” Section 22 requires date reconciliation before performance and forbids silently extending the existing approval. This condition is established by the following comparison, without market or candidate-return information:

| Stage | Existing conditional dates | Policy-covered days / requested days | Complete stage covered |
| --- | --- | --- | --- |
| development | 2021-01-01 to 2026-12-31 | 365 / 2191 | False |
| validation | 2027-01-01 to 2029-12-31 | 0 / 1096 | False |
| test | 2030-01-01 to 2032-12-31 | 0 / 1096 | False |

The existing design needs twelve nonoverlapping full calendar years: six Development, three Validation and three Test. The approved modeled policy has seven years, 2015–2021; only the first Development year is inside it, and no complete stage is covered. This proves the current dated programme cannot execute under the current approval. It does **not** prove that every shorter or forward design is impossible, or that revenue acceleration lacks alpha.

Nor can the entire seven-year pilot become Development merely by moving dates: the fixed originals cover fiscal 2018–2020. Calendar-only contributor bounds for the 29 complete original sets range from `2020-02-24T14:30:00+00:00` to `2021-03-03T14:30:00+00:00`. These are the latest constituent metadata bounds per chain, not trading-eligible dates or certified triples. There are no predecessor triples in this set supporting 2015-inception panels. The JNJ case retains its two-original gap. More historical annual sources, accounting-vintage review and calendar/identity coverage would be required for a retrospective earlier-start redesign; none is acquired automatically.

| Evidence | Preserved denominator and prior result | Phase 3E work |
| --- | --- | --- |
| Revenue | 89 originals / 30 issuers / 29 triples; 0 fully certified | 29 triple reviews deferred; no new failed/certified/resolvable classification |
| Identity | 60 cases; 0 full spans; 1 ambiguous, 1 end-only, 52 point-only, 6 unresolved | No new span certificate |
| Terminal | 60 cases / 10 completion-document sets; 6 scoped term reviews, 0 position certificates | No new terminal certificate |
| Historical NAV | 0 complete / 60 retained cases in prior evidence | [Complete case matrix](phase3e_nav_feasibility.json); no new path computed |
| Inference | Both v002 methods failed frozen size/coverage/power gates | No v003 protocol frozen, no simulation, no new detectable-effect estimate |

The four Phase 3E questions have precise limits. Source-triple, identity and terminal sufficiency remain unresolved from prior evidence; this phase does not infer their solvability or fundamental unavailability. The current dated experiment is incompatible with policy scope. The resulting verdict is REDESIGN_REQUIRED, not ABANDON_HYPOTHESIS: a useful alternative may exist, but cannot be certified from these bounds or the earlier failed calibration.

[Conceptual inference review](phase3e_inference_review.md) separates one economic discovery from stress conditions and clarifies the original two-point estimated-mean rule. No revised hierarchy, method, materiality threshold or performance window is adopted. Protocol v003 and calibration were explicitly deferred at the upstream stop; no synthetic success is claimed. [Canonical feasibility evidence](phase3e_exp005_feasibility.json) preserves the earlier method verdicts by reference/hash. Existing v002 primary Holm power at +2 points: monthly_hac12: 4.5%–4.5%; monthly_studentized_circular12: 5.5%–6.0%; neither method calibrated. These values are generated from the prior canonical synthetic results, not Phase 3E simulations or real power estimates.

| Gate | Disposition |
| --- | --- |
| REVENUE_CANONICALIZATION | PARTIAL_PRIOR_EVIDENCE |
| ACCOUNTING_PERIMETER_CERTIFICATION | BLOCKED_PRIOR_EVIDENCE |
| REVENUE_TRIPLE_FEASIBILITY | DEFERRED_SCOPE_STOP |
| HISTORICAL_SECURITY_IDENTITY | PARTIAL_PRIOR_EVIDENCE |
| CORPORATE_ACTION_LIFECYCLE | PARTIAL_PRIOR_EVIDENCE |
| TERMINAL_VALUE_EVIDENCE | BLOCKED_PRIOR_EVIDENCE |
| HISTORICAL_NAV_FEASIBILITY | BLOCKED_PRIOR_EVIDENCE |
| PUBLIC_ELIGIBILITY_POLICY | OWNER_APPROVED_PILOT_NOT_ACTIVATED |
| PUBLIC_ELIGIBILITY_ACTIVATION_READINESS | INCOMPATIBLE_WITH_EXISTING_PROGRAMME |
| INFERENCE_HYPOTHESIS_STRUCTURE | CONCEPTUAL_REVIEW_NOT_ADOPTED |
| INFERENCE_RESOLUTION_FEASIBILITY | NO_V003_DESIGN_FROZEN |
| INFERENCE_CALIBRATION | NOT_RUN_UPSTREAM_SCOPE_STOP |
| INFERENCE_POWER | NOT_ESTIMATED_V003 |
| INFERENCE_IMPLEMENTATION | BLOCKED_PRIOR_CALIBRATION |
| HISTORICAL_UNIVERSE_FEASIBILITY | BLOCKED |
| PROOF_COMPILER | SYNTHETIC_ONLY_PREVIOUSLY_VERIFIED |
| MANIFEST_REPLAY | SYNTHETIC_ONLY_PREVIOUSLY_VERIFIED |
| LOCAL_EXECUTION_ROUTE | PARTIAL_SYNTHETIC_PREVIOUSLY_VERIFIED |
| NEXUS_ADAPTER_INTERFACE | DEFINED_DISABLED |
| NEXUS_EXECUTION | BLOCKED |
| EXP005_FEASIBILITY | REDESIGN_REQUIRED |
| EXP005_FREEZE_READINESS | NOT_READY |

**Verification:** 266 local tests passed, 0 skipped; 40 public tests passed. [Validation receipt](phase3e_validation.json). Public report regeneration uses tracked metadata only:

```sh
python -m src.research.phase3e report --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

New requests: SEC 0, OpenFIGI 0, Tiingo 0, FMP 0, Orbis 0, Nexus 0, Aurora 0, source documentation/browser 0. Git push and hosted-CI metadata checks are delivery operations recorded separately. No source access cost was incurred; account-wide usage remains unknown. Original bytes, private receipts, frozen experiments and all prior phase reports remain unchanged. EXP004 is paused and EXP005 absent. No signals, rankings, performance, sealed stages, graph, optimizer, paper/live operation or Phase 4A occurred.

Owner review now needs a **date-scope decision**: retain the twelve-year staged programme and commission a separately versioned wider modeled policy, or commission a shorter/different staged design inside the existing scope with adequate predecessor coverage and power. These choices are conditional proposals; neither is authorized or scientifically certified here. The already approved exact pilot policy is not being resubmitted for approval. Acquisition and v003 calibration belong after that scope decision under a new bounded instruction. **Stopped under section 37; no automatic next phase.**
