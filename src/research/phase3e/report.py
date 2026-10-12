"""Deterministic public early-stop reports; no source acquisition or simulation."""
import json
from .feasibility import DOCS,evidence


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |',
                     *['| '+' | '.join(map(str,row))+' |' for row in rows]])


def generate(check=False):
    e=evidence()
    if e['feasibility_verdict']!='REDESIGN_REQUIRED':raise ValueError('Early-stop report requires established scope incompatibility')
    gates={'REVENUE_CANONICALIZATION':'PARTIAL_PRIOR_EVIDENCE','ACCOUNTING_PERIMETER_CERTIFICATION':'BLOCKED_PRIOR_EVIDENCE',
           'REVENUE_TRIPLE_FEASIBILITY':'DEFERRED_SCOPE_STOP','HISTORICAL_SECURITY_IDENTITY':'PARTIAL_PRIOR_EVIDENCE',
           'CORPORATE_ACTION_LIFECYCLE':'PARTIAL_PRIOR_EVIDENCE','TERMINAL_VALUE_EVIDENCE':'BLOCKED_PRIOR_EVIDENCE',
           'HISTORICAL_NAV_FEASIBILITY':'BLOCKED_PRIOR_EVIDENCE','PUBLIC_ELIGIBILITY_POLICY':'OWNER_APPROVED_PILOT_NOT_ACTIVATED',
           'PUBLIC_ELIGIBILITY_ACTIVATION_READINESS':'INCOMPATIBLE_WITH_EXISTING_PROGRAMME',
           'INFERENCE_HYPOTHESIS_STRUCTURE':'CONCEPTUAL_REVIEW_NOT_ADOPTED','INFERENCE_RESOLUTION_FEASIBILITY':'NO_V003_DESIGN_FROZEN',
           'INFERENCE_CALIBRATION':'NOT_RUN_UPSTREAM_SCOPE_STOP','INFERENCE_POWER':'NOT_ESTIMATED_V003',
           'INFERENCE_IMPLEMENTATION':'BLOCKED_PRIOR_CALIBRATION','HISTORICAL_UNIVERSE_FEASIBILITY':'BLOCKED',
           'PROOF_COMPILER':'SYNTHETIC_ONLY_PREVIOUSLY_VERIFIED','MANIFEST_REPLAY':'SYNTHETIC_ONLY_PREVIOUSLY_VERIFIED',
           'LOCAL_EXECUTION_ROUTE':'PARTIAL_SYNTHETIC_PREVIOUSLY_VERIFIED','NEXUS_ADAPTER_INTERFACE':'DEFINED_DISABLED',
           'NEXUS_EXECUTION':'BLOCKED','EXP005_FEASIBILITY':'REDESIGN_REQUIRED','EXP005_FREEZE_READINESS':'NOT_READY'}
    e['gates']=gates
    prior_identity=json.loads((DOCS/'phase3d_identity_closure.json').read_bytes())
    nav={'version':'phase3e_nav_feasibility_v001','assessment':'NOT_RUN_UPSTREAM_SCOPE_STOP',
         'denominator':60,'prior_certified_paths':0,'new_paths_computed':0,
         'cases':[{'case_key':r['case_key'],'prior_identity_status':r['identity_status'],
                   'identity_complete':False,'calendar_complete':None,'prices_complete':None,
                   'corporate_actions_complete':None,'terminal_terms_complete':False,
                   'nav_path_certified':False,'phase3e_status':'DEFERRED_SCOPE_STOP'} for r in prior_identity['cases']],
         'unknown_fields':'Null is unassessed, not missing data or proof of failure; false certificates refer to prior incomplete evidence.'}
    registry={'version':'phase3e_source_registry_v001','new_requests':{p:{'requests':0,'successes':0,'failures':0,'network_cost_incurred':0,
                   'account_wide_usage':'UNKNOWN','pacing':'NOT_APPLICABLE_NO_REQUESTS'} for p in ['SEC','OpenFIGI','Tiingo','FMP','Orbis','Nexus','Aurora','documentation/browser']},
              'acquisition':'NOT_STARTED_OWNER_SECTION37_STOP','prior_totals':'Unchanged; see phase3c_report.md and phase3d_closure_summary.json'}
    bounds=[r['mechanical_all_contributor_bound_utc'] for r in e['contributors'] if r['mechanical_all_contributor_bound_utc']]
    earliest=min(bounds) if bounds else None;latest=max(bounds) if bounds else None
    power=e['inference']['prior_v002_power02_ranges']
    power_text='; '.join(f"{method}: {low:.1%}–{high:.1%}" for method,(low,high) in power.items())
    horizon=table(['Stage','Existing conditional dates','Policy-covered days / requested days','Complete stage covered'],
                  [(r['stage'],' to '.join(r['requested']),f"{r['policy_covered_calendar_days']} / {r['calendar_days']}",r['policy_covers_complete_stage']) for r in e['horizon']['stages']])
    gate_table=table(['Gate','Disposition'],gates.items())
    validation=DOCS/'phase3e_validation.json';v=json.loads(validation.read_bytes()) if validation.exists() else None
    verification=f"{v['tests_passed']} local tests passed, {v['tests_skipped']} skipped; {v['public_tests_passed']} public tests passed." if v else 'Final validation pending.'
    texts={
      'phase3e_report.md':f'''# Phase 3E: experiment feasibility and scope stop

**EXP005 feasibility: REDESIGN_REQUIRED. Freeze: NOT_READY.** This new phase began from `081dfe6` on 2026-10-12 and stopped at the owner-required date-scope gate before acquisition or new calibration. The [frozen plan](phase3e_plan.md) is a distinct Phase 3E artifact. Previous Phase 3D reports/results remain unchanged.

The [owner request](owner_phase3e_2026-10-12.md), section 37, explicitly requires: “Stop early and report” when “The availability-policy scope is incompatible with the required historical design.” Section 22 requires date reconciliation before performance and forbids silently extending the existing approval. This condition is established by the following comparison, without market or candidate-return information:

{horizon}

The existing design needs twelve nonoverlapping full calendar years: six Development, three Validation and three Test. The approved modeled policy has seven years, 2015–2021; only the first Development year is inside it, and no complete stage is covered. This proves the current dated programme cannot execute under the current approval. It does **not** prove that every shorter or forward design is impossible, or that revenue acceleration lacks alpha.

Nor can the entire seven-year pilot become Development merely by moving dates: the fixed originals cover fiscal 2018–2020. Calendar-only contributor bounds for the 29 complete original sets range from `{earliest}` to `{latest}`. These are the latest constituent metadata bounds per chain, not trading-eligible dates or certified triples. There are no predecessor triples in this set supporting 2015-inception panels. The JNJ case retains its two-original gap. More historical annual sources, accounting-vintage review and calendar/identity coverage would be required for a retrospective earlier-start redesign; none is acquired automatically.

| Evidence | Preserved denominator and prior result | Phase 3E work |
| --- | --- | --- |
| Revenue | 89 originals / 30 issuers / 29 triples; 0 fully certified | 29 triple reviews deferred; no new failed/certified/resolvable classification |
| Identity | 60 cases; 0 full spans; 1 ambiguous, 1 end-only, 52 point-only, 6 unresolved | No new span certificate |
| Terminal | 60 cases / 10 completion-document sets; 6 scoped term reviews, 0 position certificates | No new terminal certificate |
| Historical NAV | 0 complete / 60 retained cases in prior evidence | [Complete case matrix](phase3e_nav_feasibility.json); no new path computed |
| Inference | Both v002 methods failed frozen size/coverage/power gates | No v003 protocol frozen, no simulation, no new detectable-effect estimate |

The four Phase 3E questions have precise limits. Source-triple, identity and terminal sufficiency remain unresolved from prior evidence; this phase does not infer their solvability or fundamental unavailability. The current dated experiment is incompatible with policy scope. The resulting verdict is REDESIGN_REQUIRED, not ABANDON_HYPOTHESIS: a useful alternative may exist, but cannot be certified from these bounds or the earlier failed calibration.

[Conceptual inference review](phase3e_inference_review.md) separates one economic discovery from stress conditions and clarifies the original two-point estimated-mean rule. No revised hierarchy, method, materiality threshold or performance window is adopted. Protocol v003 and calibration were explicitly deferred at the upstream stop; no synthetic success is claimed. [Canonical feasibility evidence](phase3e_exp005_feasibility.json) preserves the earlier method verdicts by reference/hash. Existing v002 primary Holm power at +2 points: {power_text}; neither method calibrated. These values are generated from the prior canonical synthetic results, not Phase 3E simulations or real power estimates.

{gate_table}

**Verification:** {verification} [Validation receipt](phase3e_validation.json). Public report regeneration uses tracked metadata only:

```sh
python -m src.research.phase3e report --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

New requests: SEC 0, OpenFIGI 0, Tiingo 0, FMP 0, Orbis 0, Nexus 0, Aurora 0, source documentation/browser 0. Git push and hosted-CI metadata checks are delivery operations recorded separately. No source access cost was incurred; account-wide usage remains unknown. Original bytes, private receipts, frozen experiments and all prior phase reports remain unchanged. EXP004 is paused and EXP005 absent. No signals, rankings, performance, sealed stages, graph, optimizer, paper/live operation or Phase 4A occurred.

Owner review now needs a **date-scope decision**: retain the twelve-year staged programme and commission a separately versioned wider modeled policy, or commission a shorter/different staged design inside the existing scope with adequate predecessor coverage and power. These choices are conditional proposals; neither is authorized or scientifically certified here. The already approved exact pilot policy is not being resubmitted for approval. Acquisition and v003 calibration belong after that scope decision under a new bounded instruction. **Stopped under section 37; no automatic next phase.**
''',
      'phase3e_gate_review.md':f'''# Phase 3E gate review

{gate_table}

REDESIGN_REQUIRED is established for the current programme by date-scope incompatibility. The approved seven-year pilot cannot contain the existing twelve-year nonoverlapping programme. A covered date interval alone supplies no source, identity, terminal, power or execution certificate and no stage authorization. Source questions and v003 calibration remain deferred, not failed new evaluations. This is the owner's explicit early-stop disposition; it is not a completed evidence-acquisition campaign.
''',
      'phase3e_inference_review.md':'''# Phase 3E conceptual inference review — deferred protocol

The economic question remains whether annual revenue-growth acceleration adds a positive, economically meaningful net paired effect to matched momentum on the same PIT population. The estimand remains 252 × the session-weighted mean daily simple-return difference; it is neither CAGR difference nor a cross-sectional issuer mean. No real paired tape is read.

The prior record is explicit rather than ambiguous on materiality: Phase 3B requires an estimated mean at least two annual percentage points, positive lower descriptive bound and evidence against zero. Requiring a lower bound above two points would be a new, stronger inferential claim. It must not be silently substituted. For a symmetric unbiased estimate, a hard estimated-mean floor at the true boundary has acceptance probability at most one half even before statistical/stress gates; power at the boundary must be distinguished from detectable effects above it. No new power value is calculated here.

There is one economic mechanism. Doubled-cost and execution-delay paths could coherently be mandatory falsifiers of that mechanism rather than separate discoveries. That interpretation would remove formal claims of statistical significance for each stress: support would require one primary confirmatory test plus predeclared positive stressed estimates and all falsification conditions. It is conceptually defensible but changes the prior four-effect inferential promise. It remains a proposal, not an adopted hierarchy chosen to repair failed calibration.

Daily sessions, monthly decisions and yearly filings are counts, not independent observations. Repeated issuers and renewable holdings, overlapping portfolios, common shocks and rebalance dates can sustain serial dependence. Independent funding prevents positions crossing windows; it does not make market shocks independent. Earlier calendar geometry is 1,763 sessions / 84 months in 2015–2021. The fixed annual triples start contributing only at their own later metadata bounds; they do not establish a seven-year usable tape, 500 issuers/window or the original event-count floors.

The original six-year joint Validation/Test confirmation and six-year Development programme cannot fit the approved scope together. Shortening stages, borrowing Development into confirmation or replacing future time by synthetic draws would change the scientific question/evidence regime. No such change is adopted. Fixing that horizon and source scope is logically prior to choosing the effective observation structure and freezing v003.

Protocol v003: NOT_FROZEN. Methods: NOT_SELECTED. Calibration: NOT_RUN_UPSTREAM_SCOPE_STOP. New synthetic replications: 0. Type-I/FWER, coverage, power and MDE: NOT_ESTIMATED_V003. Earlier protocols, seeds, gates and negative results remain immutable. A later bounded protocol must define certification assumptions versus stress diagnostics, useful power at effects above the materiality boundary, and a very small method family before simulation. No statistical thresholds are weakened here.
'''}
    outputs={'phase3e_exp005_feasibility.json':json.dumps(e,sort_keys=True,indent=2)+'\n',
             'phase3e_nav_feasibility.json':json.dumps(nav,sort_keys=True,indent=2)+'\n',
             'phase3e_source_registry.json':json.dumps(registry,sort_keys=True,indent=2)+'\n',**texts}
    for name,body in outputs.items():
        path=DOCS/name
        if check:
            if not path.exists() or path.read_text(encoding='utf-8')!=body:raise ValueError('Phase 3E artifact changed: '+name)
        else:path.write_text(body,encoding='utf-8',newline='\n')
    return len(outputs)
