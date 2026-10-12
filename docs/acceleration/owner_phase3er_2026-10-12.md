<WritingBlock id="48217" variant="document">
# Research OS — Phase 3E-R  
## Date-Scope Redesign, Availability-Policy Extension Review, and Pre-Performance Stage Feasibility

You are continuing the existing Research OS project.
Repository:
C:\Users\runni\quant\
GitHub:
jarems421/ai-assisted-quantitative-research
Branch:
main
Expected current HEAD:
87f23f6198f096d611918b24eac0080b3350aa60
Recent Phase 3E commits:
- 2acf8ab — Freeze bounded Phase 3E evidence and experiment feasibility plan
- 222448a — Audit Phase 3E horizon scope without granting research access
- 87f23f6 — Record Phase 3E redesign verdict at the required scope stop
Earlier Phase 3D/3E evidence must remain preserved.
1. OWNER DECISION
The owner has reviewed the Phase 3E scope-stop result.
The following redesign work is now explicitly authorized:
Do not retain the existing 2021–2032 six-year Development / three-year Validation / three-year Test calendar as the required EXP005 programme.
Prepare a scientifically justified replacement stage design using historical dates that are already observable as of the current research date.
Prepare a separately versioned modeled-availability policy proposal extending only as far as needed to support that redesigned historical programme.
The existing 2015–2021 policy must remain unchanged and preserved.
The new wider policy is NOT automatically approved by this authorization.
Before any EXP005 performance is observed, compare bounded candidate stage geometries using source coverage, calendar structure, stage isolation, and synthetic inference/power only.
No EXP005 creation, freeze, real signal calculation, performance, Nexus use, Phase 4A, paper trading, or live trading is authorized.

This owner instruction resolves the prior Phase 3E scope-stop question.
Do not ask whether the old 12-year programme should remain.
It should not remain the mandatory EXP005 stage design.
2. IMPORTANT DATE RULE
The current date is 2026-10-12.
Do NOT treat all of calendar year 2026 as historically observable.
A policy or historical stage may only use information that could have existed by the actual research cutoff.
For any redesigned historical programme:
research_cutoff <= 2026-10-12
and preferably use the exact current repository/research cutoff convention already implemented.
Do not use:
- future 2026 filings;
- future 2026 prices;
- future corporate actions;
- future calendar sessions;
- 2027+ observations.
The phrase “extend through 2026” means:
extend only through the already-observable portion of 2026 required by the design,

not:
assume 2026-12-31 has already occurred.

3. READ FIRST
Before coding or acquiring anything:
1. Read AGENTS.md.
2. Confirm branch, HEAD, working tree, and upstream status.
3. Read in full:
   - docs/acceleration/master_plan.md
   - docs/acceleration/phase3d_report.md
   - docs/acceleration/phase3d_closure_report.md
   - docs/acceleration/phase3e_plan.md
   - docs/acceleration/phase3e_report.md
   - docs/acceleration/phase3e_exp005_feasibility.json
   - docs/acceleration/phase3e_inference_review.md
   - docs/acceleration/availability_policy_v002_approved.json
   - docs/acceleration/phase3d_inference_design_v002.md
   - docs/acceleration/phase3d_inference_protocol_v002.json
   - docs/acceleration/phase3d_inference_calibration_v002.json
   - docs/acceleration/phase3d_inference_resolution.json
   - relevant Phase 3C availability artifacts
   - relevant source census and filing metadata artifacts.
4. Inspect relevant implementation under:
   - src/research/phase3e/
   - src/research/phase3d/
   - src/research/phase3c/
   - src/research/sec_pilot/
   - src/research/capabilities.py
   - src/research/spec.py
   - src/research/analysis.py
   - experiment/stage/trial infrastructure
   - public CI
   - tests.
Repository reality overrides implementation assumptions in this prompt.
Scientific stop rules in this prompt do not.
4. CURRENT VERIFIED STATE
Phase 3E concluded:
EXP005_FEASIBILITY = REDESIGN_REQUIRED
and:
EXP005_FREEZE_READINESS = NOT_READY
No EXP005 experiment exists.
No real EXP005 performance has been observed.
Current important source state includes:
- 89 original annual filings;
- 30 fixed revenue candidates;
- 29 discovered three-original chains;
- 0 fully certified revenue triples;
- 60 fixed identity/lifecycle cases;
- 0 complete historical identity spans;
- 0 complete terminal position certificates;
- 0 complete historical NAV-capable paths.
The prior approved modeled-availability policy covers:
2015-01-01 through 2021-12-31
Its status is:
OWNER_APPROVED_PILOT_NOT_ACTIVATED
Exact public availability remains:
UNKNOWN
Do not change that.
5. WHY THE OLD STAGE PROGRAMME IS INVALID
The previous conditional programme was:
Development:
2021-01-01 through 2026-12-31
Validation:
2027-01-01 through 2029-12-31
Test:
2030-01-01 through 2032-12-31
That requires twelve full non-overlapping calendar years.
The approved modeled policy covers only 2015–2021.
Therefore the old programme cannot execute under the current approval.
Furthermore, the existing filing triples do not support a 2015 signal inception.
Phase 3E found mechanical contributor bounds for the current three-original sets around:
2020-02-24
through
2021-03-03
depending on chain.
Those are contributor/source bounds, not certified signal-eligibility dates.
Therefore simply relabeling 2015–2021 as Development is not valid.
This redesign must start from actual source availability and predecessor requirements.
6. OBJECTIVE OF THIS PASS
This is not Phase 4A.
This is not another generic Phase 3E source-acquisition campaign.
This is a focused Phase 3E-R redesign pass.
Its purpose is to determine:
1. what historical date range can legitimately support EXP005;
2. what modeled availability-policy scope would be required;
3. what historical stage geometry is scientifically preferable;
4. whether that geometry can support meaningful inference before performance;
5. what exact owner decision is required next.
The output should be a bounded design recommendation, not a strategy result.
7. ABSOLUTE PERFORMANCE FIREWALL
Do NOT calculate or inspect:
- real revenue acceleration;
- real momentum;
- real candidate ranks;
- real holdings;
- real portfolio returns;
- SPY comparisons;
- Sharpe;
- Sortino;
- drawdown;
- alpha;
- excess return;
- candidate-vs-control return differences;
- any real performance measure.
Do NOT create EXP005.
Do NOT register EXP005.
Do NOT freeze EXP005.
Do NOT open Development.
Do NOT open Validation.
Do NOT open Test.
Do not use market performance to choose stage dates.
If any accidental process exposes real EXP005 performance:
STOP,
record contamination,
report it,
do not use it.
8. PRESERVE THE EXISTING POLICY
The existing policy:
phase3c_ambiguity_buffer_v002
and its owner approval must remain historically unchanged.
Do not mutate it.
Do not expand its scope in place.
Do not edit its hash.
Do not reinterpret its original approval.
Create a new versioned proposal for any expanded scope.
Conceptually:
availability_policy_v003_proposed
or repository-equivalent naming.
It must be independent evidence.
9. PROPOSED POLICY V003
The starting hypothesis is that the same conservative modeling logic may be suitable beyond 2021, but this must be re-reviewed rather than assumed.
The existing conceptual rule is approximately:
determine the later relevant filing/acceptance civil date under plausible timestamp interpretations, wait conservatively through the required later exchange sessions, and only permit modeled eligibility when ambiguity produces the same resulting eligible open and the open is later than every plausible source instant.

Use the exact repository definition, not this paraphrase, as the baseline.
For v003:
1. preserve exact public availability as UNKNOWN;
2. preserve all plausible source clock representations;
3. never promote modeled eligibility into an observed publication timestamp;
4. fail closed on timing non-invariance;
5. fail closed on unsupported calendar periods;
6. fail closed on contradictory timing evidence.
Do not simply change:
2021 -> 2026
in a JSON field.
The new scope requires new evidence and review.
10. POLICY V003 SCOPE
Do not automatically choose 2015-01-01 through 2026-12-31.
Instead derive the minimum useful proposed scope from candidate historical stage designs.
The maximum possible historical cutoff is:
2026-10-12
or the exact repository-defined current research cutoff.
The minimum start should be determined by:
- predecessor filing requirements;
- actual candidate filing metadata;
- policy mechanics;
- source coverage;
- calendar availability.
The proposed v003 scope should be only as broad as necessary.
Possible result could be something like:
2019-X-X through 2026-10-12
or
2020-X-X through 2026-10-12
if that is what the evidence supports.
Do not widen to 2015 merely because v002 began there.
11. POLICY V003 REVIEW PACKET
Produce a full owner-review packet for v003.
It must include:
- exact policy definition;
- exact proposed start/end scope;
- policy hash;
- relationship to v002;
- reason expansion is required;
- what remains UNKNOWN;
- complete calendar coverage;
- clock ambiguity tests;
- DST tests;
- near-midnight cases;
- weekends/holidays;
- filing-date vs acceptance-date edge cases;
- complete contributor invariance results for the proposed research population/scope;
- any failed rows;
- consequences of failures.
Important:
v003 must remain:
PROPOSED_NOT_APPROVED
until the owner explicitly approves it.
Do not activate it.
Do not create real eligibility views under it.
12. NO AUTOMATIC POLICY APPROVAL
This prompt authorizes:
- design;
- analysis;
- review packet;
- synthetic/calendar tests.
It does NOT constitute owner approval of v003.
At the end, if v003 is recommended, present the exact decision packet and stop for owner review.
13. HISTORICAL STAGE REDESIGN
Do not retain the old mandatory 6/3/3 split.
Do not immediately choose a new split either.
Compare a small bounded set of candidate stage geometries.
Candidate designs must:
- use only historically observable dates;
- respect contributor/source availability;
- respect the proposed policy scope;
- preserve meaningful untouched holdout evidence;
- avoid stage leakage;
- preserve enough sample for inference;
- remain operationally realistic.
Do not optimize stage boundaries against performance.
There is no performance access.
Use only:
- dates;
- session counts;
- filing counts;
- predecessor-chain counts;
- population coverage counts;
- source coverage;
- synthetic power/calibration.
14. CANDIDATE STAGE FAMILIES
Evaluate only a small scientifically motivated family.
For example, consider structures conceptually like:
Family A — conventional historical split
Longer Development,
short Validation,
final historical Test.
Family B — balanced staged split
Development receives the majority of usable history,
with meaningful Validation and Test periods.
Family C — Development + single historical holdout
One larger Development stage,
one untouched historical confirmation stage,
followed later by true forward paper evidence.
Family D — expanding / forward-chaining validation
Only if it fits the existing Research OS stage-control philosophy and
can remain fully predeclared.
Do NOT mechanically implement all four.
Inspect existing experiment/stage architecture and choose perhaps 2–4 realistic candidate geometries.
Do not add dozens of date combinations.
No search over every possible boundary.
15. IMPORTANT FORWARD-EVIDENCE PRINCIPLE
The redesigned historical experiment does NOT need to pretend that future calendar years 2027–2032 are historical holdouts.
Research OS already has a later forward-paper stage.
Therefore the redesign should distinguish:
historical holdout evidence
from
future forward evidence.
A valid architecture could eventually be:
historical Development
→ historical untouched confirmation
→ forward paper trading
rather than:
historical Development
→ wait years for Validation
→ wait more years for Test
→ then forward paper.
Do not adopt this automatically.
Evaluate it as a scientific option.
16. SOURCE COVERAGE BY STAGE
For each candidate geometry determine, without calculating signals:
- number of exchange sessions;
- number of monthly decision dates;
- number of annual reporting cycles;
- number of possible three-original contributor states;
- number of candidate issuers with mechanical predecessor availability;
- number of source-covered filing events;
- identity/lifecycle coverage status;
- warm-up requirements;
- incomplete edge periods.
Do not call a mechanically possible triple certified.
Maintain separate counts:
mechanically_available
versus:
accounting_certified
versus:
trading_eligible
Currently certified issuer count may remain zero.
That is acceptable.
17. LIMITED SOURCE ACQUISITION AUTHORITY
This redesign pass may make bounded source-only acquisitions only if required to determine:
- filing date/acceptance coverage;
- source availability through the proposed historical cutoff;
- calendar/policy invariance;
- non-performance stage feasibility.
Permitted sources remain:
- SEC EDGAR;
- official filing metadata;
- official exchange/calendar documentation;
- OpenFIGI only for non-performance identifier feasibility if needed;
- official documentation.
Do NOT acquire market price history for performance.
Do NOT calculate momentum.
Do NOT acquire broad Tiingo history merely because later stages may need it.
Do NOT perform a full backfill.
If later annual filings are needed only to establish source coverage,
acquire the smallest bounded set necessary.
Every request must be logged.
18. ACCOUNTING/IDENTITY WORK IN THIS PASS
Do NOT restart the entire 29-chain accounting certification effort yet.
Do NOT restart the entire 60-case identity campaign yet.
The purpose of this pass is stage/scope redesign.
However, use existing evidence to calculate coverage constraints.
If a small amount of source acquisition is strictly required to determine whether a proposed stage is even structurally possible, it may be performed.
Do not attempt to green all source gates before the scope design exists.
After v003/stage design owner review, the full source-certification work can resume under the final scope.
19. INFERENCE CONCEPTUAL REVIEW
Phase 3E already noted an important conceptual point:
The economic discovery is one mechanism.
The stress cases:
- doubled transaction cost;
- +1-session delay;
- +5-session delay
may be robustness/falsification conditions rather than four separate discoveries.
The prior formal design treated all four as separate Holm-controlled hypotheses.
Do not silently change that.
This redesign pass must evaluate the scientific structure explicitly.
Ask:
What claim are we actually trying to confirm?

The likely primary claim is:
revenue-growth acceleration has positive and economically meaningful net incremental performance relative to the matched momentum control.

Then determine whether:
- double cost;
- delay1;
- delay5
are separate statistical discoveries,
or mandatory robustness conditions for the same primary claim.
No real performance exists, so this is the correct time to decide.
20. MATERIALITY RULE REVIEW
The existing 2 percentage-point annualized materiality rule must also be clarified.
Determine from historical design documents whether the intended rule is closer to:
Interpretation A
estimated net incremental effect > 2 percentage points
AND statistical evidence primary effect > 0
or
Interpretation B
lower confidence bound > 2 percentage points.
These imply radically different power requirements.
Do not choose whichever is easier.
Trace the historical wording.
If genuinely ambiguous, document that and propose the more defensible interpretation.
No adoption without explicit frozen design evidence.
21. STAGE GEOMETRY BEFORE INFERENCE
For every candidate stage geometry calculate source/calendar-only sample structure.
Examples:
- daily session count;
- monthly rebalance count;
- years;
- reporting cycles;
- funded windows;
- possible independent blocks;
- boundary effects.
Do not equate counts with independence.
These geometry artifacts feed synthetic inference.
22. INFERENCE V003
Once candidate stage geometries are defined, create a bounded pre-performance inference review.
Do NOT yet search endlessly for a method.
Freeze a small v003 candidate family.
Maximum:
2–3 methods.
The methods should reflect the selected observation geometry.
Possible families, if justified, include:
- studentized block-bootstrap inference;
- self-normalized time-series inference;
- improved small-sample HAC;
- cluster/wild-cluster inference if there is a defensible cluster structure.
Do not include methods merely because a package implements them.
Each method must have:
- estimand;
- assumptions;
- observation unit;
- dependence treatment;
- test statistic;
- confidence procedure;
- multiplicity treatment;
- finite-sample concerns.
23. DO NOT FREEZE V003 TOO EARLY
Unlike the aborted Phase 3E run, v003 now has a valid upstream purpose.
But the order must be:
1. candidate policy scope;
2. candidate stage geometries;
3. source/calendar geometry;
4. hypothesis hierarchy decision;
5. materiality interpretation;
6. inference candidate family;
7. freeze protocol;
8. synthetic simulation.
Never reverse that order.
24. SYNTHETIC CALIBRATION ONLY
No real return information.
For each serious candidate stage geometry, use synthetic data reflecting its actual sample structure.
Synthetic worlds should include appropriately:
- iid null;
- AR dependence;
- high persistence;
- annual/reporting shocks;
- rebalance shocks;
- common market shocks;
- heteroskedasticity;
- skew/heavy tails;
- overlap;
- regime changes;
- positive effects;
- negative effects.
Distinguish:
CERTIFICATION_WORLDS
from:
STRESS_DIAGNOSTICS
Do not demand validity under assumptions the chosen method never claims.
25. POWER / MDE ANALYSIS
For each candidate geometry and inference architecture, report pre-performance:
- empirical type-I error;
- family-wise error where relevant;
- confidence coverage;
- power at +2 points;
- power at +5 points;
- power at +10 points;
- perhaps +15/+20 if useful;
- minimum detectable effect at fixed target power;
- expected interval width;
- sensitivity to dependence.
Target power should be defined before simulation.
Do not make a weak design look acceptable by choosing a lower threshold afterward.
If 80% power is unrealistic for the intended claim, report that.
If a +2-point effect cannot be meaningfully detected in any available geometry, say so.
26. COMPARE STAGE DESIGNS SCIENTIFICALLY
The recommendation must not be:
“choose the split with the most observations.”
Compare:
- source coverage;
- stage isolation;
- statistical power;
- holdout credibility;
- temporal regime diversity;
- amount of untouched evidence;
- feasibility of later forward paper confirmation.
Do not use real returns.
27. POSSIBLE OUTCOMES
At the end of this redesign pass, issue one stage-design verdict:
STAGE_DESIGN_READY_FOR_OWNER_REVIEW
A specific scope + stage geometry + inference architecture is scientifically recommended.
STAGE_DESIGN_INFEASIBLE_WITH_CURRENT_HISTORY
No defensible staged design exists through the current historical cutoff.
POLICY_SCOPE_EXTENSION_INSUFFICIENT
The available historical range remains too short even with expansion.
SOURCE_HISTORY_EXTENSION_REQUIRED
Earlier filings/source history are needed before a useful design can exist.
Do not force a positive outcome.
28. EXP005 STATUS DURING THIS PASS
Regardless of the redesign recommendation:
EXP005_FREEZE_READINESS = NOT_READY
must remain unless a later separately authorized source/inference certification pass completes all remaining gates.
This pass is not allowed to declare EXP005 fully freeze-ready merely because a stage geometry exists.
29. NEXUS
Nexus remains completely blocked.
Zero:
- Nexus backtests;
- SDK operations;
- Aurora calls;
- support messages;
- paper trades;
- remote Nexus jobs.
NexusAdapter remains disabled.
30. CORPORATE REALITY GRAPH
Do not build it.
Still Phase 4B.
31. CAUSAL MARKET LAB
Do not build it.
Still Phase 4C.
32. PUBLIC CI
Preserve the public/synthetic GitHub Actions workflow.
Add new public synthetic tests if appropriate.
CI must not require:
- secrets;
- raw private source bodies;
- research API calls;
- market data;
- EXP005 performance.
Hosted CI is engineering evidence only.
33. PROOF COMPILER
Preserve all existing fail-closed compiler semantics.
The compiler should remain synthetic-only for real strategy execution.
You may add stage-design feasibility artifacts or policy-hash compatibility checks if cleanly useful.
Do NOT enable real EXP005 compilation.
34. RECOMMENDED NEW ARTIFACTS
Follow repository naming conventions.
Create equivalents of:
- phase3e_redesign_plan.md
- phase3e_redesign_report.md
- phase3e_redesign_summary.json
- phase3e_stage_candidates.json
- phase3e_stage_geometry.json
- availability_policy_v003_proposed.json
- availability_policy_v003_review_packet.md
- phase3e_policy_v003_invariance.json
- phase3e_inference_hierarchy_review.md
- phase3e_inference_protocol_v003.json
- phase3e_inference_calibration_v003.json
- phase3e_power_mde_v003.json
- phase3e_stage_recommendation.json
- phase3e_redesign_gate_review.md
- phase3e_redesign_validation.json
Do not overwrite:
- v002 policy;
- original Phase 3E report;
- Phase 3D reports;
- previous inference protocols/results.
35. GATES TO REPORT
At minimum:
CURRENT_POLICY
PROPOSED_POLICY_V003
POLICY_SCOPE_COMPATIBILITY
POLICY_CLOCK_INVARIANCE
STAGE_SOURCE_GEOMETRY
STAGE_HOLDOUT_INTEGRITY
INFERENCE_HYPOTHESIS_STRUCTURE
MATERIALITY_RULE
INFERENCE_RESOLUTION
INFERENCE_CALIBRATION
INFERENCE_POWER
MINIMUM_DETECTABLE_EFFECT
STAGE_DESIGN_FEASIBILITY
PUBLIC_ELIGIBILITY_ACTIVATION_READINESS
EXP005_FEASIBILITY
EXP005_FREEZE_READINESS
NEXUS_EXECUTION
Use precise statuses.
36. IMPORTANT STATUS DISTINCTIONS
Do not conflate:
POLICY_PROPOSED
with
POLICY_APPROVED
or
POLICY_ACTIVATED.
Likewise:
STAGE_DESIGN_RECOMMENDED
does not equal
EXP005_READY.
And:
MATHEMATICALLY_POWERED_SYNTHETICALLY
does not equal
REAL_INFERENCE_CERTIFIED.
Maintain all distinctions explicitly.
37. SOURCE REQUEST ACCOUNTING
Report all new Phase 3E-R requests separately:
- SEC;
- OpenFIGI;
- Tiingo;
- FMP;
- documentation/browser;
- Orbis;
- Nexus.
Orbis must remain zero unless separately authorized.
Nexus must remain zero.
If there are zero source requests, report zero.
Do not manufacture acquisition merely to make the phase appear substantial.
38. STOP FOR OWNER REVIEW
If a specific v003 policy and stage design are recommended:
STOP.
Present the owner with:
1. exact proposed policy scope;
2. policy hash;
3. modeled timing rule;
4. unresolved exact-public-availability disclaimer;
5. stage dates;
6. warm-up dates;
7. Development dates;
8. historical holdout dates;
9. inference architecture;
10. materiality definition;
11. synthetic calibration results;
12. power/MDE;
13. reasons this design is preferred;
14. all important tradeoffs.
Do NOT approve v003 on the owner's behalf.
Do NOT activate it.
Do NOT proceed into source certification/performance.
39. ABSOLUTE PROHIBITIONS
Do not:
- calculate real EXP005 signal values;
- calculate real momentum;
- calculate real returns;
- rank securities;
- calculate performance;
- optimize parameters;
- create/freeze EXP005;
- open any strategy stage;
- extend policy without approval;
- assume future dates;
- drop difficult issuers;
- change the revenue hypothesis;
- add a new filing signal;
- resume EXP004;
- call Nexus;
- call Aurora;
- build the graph;
- build causal research;
- paper trade;
- live trade.
40. OWNER INTENT
The owner does NOT want to wait until 2032 simply because an old planning document assigned Validation/Test to future years.
The purpose is to make the best scientifically defensible use of historical information already available now, while preserving genuine future forward evidence later.
This does NOT mean:
“use all history for Development.”
Historical holdout integrity still matters.
Design a sensible separation.
41. SUCCESS CONDITION
This redesign pass succeeds if it answers:
Given the information genuinely observable by 2026-10-12, what is the strongest scientifically defensible historical stage design for EXP005, what modeled-availability scope would it require, and is that design statistically capable of answering the intended economic question before we ever inspect returns?

That answer may still be:
no sufficiently strong design exists.

That is acceptable.
42. IMPLEMENTATION ORDER
Proceed in this order:
1. audit repository;
2. write/freeze Phase 3E-R plan;
3. reconstruct exact source/calendar geometry;
4. derive minimal candidate v003 policy scope;
5. run full timing/calendar invariance analysis;
6. define bounded candidate historical stage geometries;
7. compare source-only stage coverage;
8. resolve proposed hypothesis hierarchy;
9. resolve materiality interpretation;
10. define/freeze v003 inference protocol;
11. run synthetic calibration;
12. run power/MDE analysis;
13. compare candidate stage geometries;
14. select recommendation or declare infeasibility;
15. generate v003 owner review packet if appropriate;
16. run targeted tests;
17. run full local tests;
18. run public synthetic checks;
19. preserve prior hashes;
20. commit in small auditable commits;
21. push to main if repository policy permits;
22. confirm hosted CI;
23. STOP FOR OWNER REVIEW.
43. FINAL RESPONSE
At completion report:
- exact HEAD;
- commits;
- source request counts;
- proposed v003 scope;
- policy invariance results;
- candidate stage geometries;
- recommended stage geometry;
- warm-up / Development / holdout boundaries;
- hypothesis hierarchy recommendation;
- materiality interpretation;
- v003 inference methods;
- null calibration;
- power results;
- minimum detectable effects;
- remaining scientific blockers;
- EXP005 status;
- local tests;
- public tests;
- CI status;
- preservation results;
- exact owner decision required.
Then stop.
Do not start Phase 4A.
</WritingBlock>
The critical part is that this tells Codex not to just pick 2020–2023 / 2024–2025 / 2026 because it looks neat. It has to compare stage structures on source coverage and synthetic statistical power first, while the real returns remain untouched.