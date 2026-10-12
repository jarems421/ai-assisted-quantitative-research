"""Final upstream inference stop; offline evidence only, no acquisition/execution path."""
import argparse,json,math
from pathlib import Path
from src.research.spec import digest
from src.research.phase3d.proof import file_hash
from src.research.phase3er.inference import critical

DOCS=Path(__file__).resolve().parents[2]/'docs/acceleration'


def weighted_moments(values,counts):
    """Deterministic synthetic algebra helper; not a real-return data interface."""
    if len(values)!=len(counts) or len(values)<2 or not all(math.isfinite(x) for x in [*values,*counts]) or min(counts)<=0:
        raise ValueError('Complete finite groups and positive session weights required')
    total=sum(counts);mean=sum(x*n for x,n in zip(values,counts))/total
    se2=sum(n*(x-mean)**2 for x,n in zip(values,counts))/((len(values)-1)*total)
    return mean,se2


def witness():
    counts=[251,250,252,250,187];values=[-.015,.01,.005,-.005,.02]
    mean,se2=weighted_moments(values,counts)
    rows=[]
    for common in [-.1,0.,.1]:
        mu,var=weighted_moments([x+common for x in values],counts)
        rows.append({'synthetic_common_offset':common,'mean':mu,'estimated_mean_variance':var,
                     'positive_95_lower_endpoint':mu-critical(4)*math.sqrt(var)>0})
    return {'counts':counts,'synthetic_group_values':values,'base_mean':mean,'base_se2':se2,'translations':rows,
            'source':'Fixed fabricated values; no real returns or new simulation','performance_inputs':0}


def load(name):return json.loads((DOCS/name).read_bytes())


def build():
    approval=load('availability_policy_v003_approved.json');policy=load('availability_policy_v003_proposed.json')
    if approval['policy_sha256']!=digest(policy) or approval['activation_status']!='NOT_ACTIVATED':raise ValueError('Approval or activation changed')
    if digest(policy)!='438d7bcf7d091f596009ba841e6dacbd960c18493c34ffec798d8c1aaf1dacbd':raise ValueError('Fixed policy changed')
    cal=load('phase3e_inference_calibration_v003_correction_001.json')
    rows=[r for r in cal['rows'] if r['geometry']=='C' and r['method']=='session_weighted_group_student' and r['world']=='common_crossyear' and r['annual_effect']==0]
    if len(rows)!=3 or any(r['role']!='STRESS_DIAGNOSTIC' for r in rows):raise ValueError('Frozen stress evidence changed')
    accounting=load('phase3d_accounting_review.json');identity=load('phase3d_identity_closure.json');terminal=load('phase3d_terminal_closure.json')
    oldnav=load('phase3e_nav_feasibility.json');market=load('phase3c_evidence.json')
    chains=[dict(c,final_campaign_status='DEFERRED_UPSTREAM_INFERENCE_STOP',new_certified_triple=False,
                 outcome='OTHER_EXPLICIT_REASON',outcome_reason='Accounting review not completed in this pass; mandatory inference stop reached first',
                 prior_evidence_reference='phase3d_accounting_review.json') for c in accounting['chains'] if c['originals']==3]
    if len(chains)!=29 or len(identity['cases'])!=60 or len(oldnav['cases'])!=60:raise ValueError('Fixed denominator changed')
    cert={'version':'phase3_final_inference_certificate_v001','verdict':'BLOCKED','approved_method':'session_weighted_group_student',
          'estimand':'252 times mean aligned daily net candidate-minus-momentum arithmetic differences',
          'formal_hypothesis':'One primary H0: annual paired mean <=0; one-sided alpha0.05',
          'materiality':'Estimated annual mean >=0.02 AND positive two-sided95 lower endpoint against zero',
          'robustness':'Double-cost/+1/+5-session estimated effects strictly positive; mandatory gates, not discoveries',
          'group_structure':'Five Stage C calendar-year groups; 251,250,252,250,187 sessions; partial2026 retained',
          'reference':'Student df4; session-weighted group mean and residual mean-variance estimate',
          'required_assumptions':['Common group mean','Independent approximately Gaussian group means','Group variance inversely proportional to session counts'],
          'synthetic_calibration':'Prior frozen certification worlds pass conditionally; known common-crossyear stress fails; no new simulation',
          'known_failure_rows':rows,'deterministic_counterexample':witness(),
          'model':'X_g = theta + Z + epsilon_g; independent zero-mean Gaussian Z and epsilon; Var(epsilon_g)=sigma2/n_g',
          'true_mean_variance':'Var(weighted_mean)=Var(Z)+sigma2/sum(n_g)',
          'expected_estimated_mean_variance':'E(residual_se2)=sigma2/sum(n_g); common Z cancels from every residual',
          'conditioning_limit':'Conditioning on realized Z changes the group mean to theta+Z; it does not supply the approved unconditional mean-null guarantee. No estimand change is adopted.',
          'limiting_false_primary_rejection':0.5,'limiting_two_sided_coverage':0.0,
          'limit_scope':'As common-factor variance grows with idiosyncratic variance fixed; analytical counterexample, not measured real error rates',
          'real_world_assumption_status':'NOT_ESTABLISHED; persistent common exposure admissible, not proven to be the actual return process',
          'scientific_conclusion':'No uniform certification over an unrestricted persistent-common-factor class. The design supplies no independently justified bound or cancellation restriction.',
          'economic_source_structure':['Recurring issuer membership','Annual signals can persist across year boundaries','Overlapping holdings and shared market/regime exposures','Matched momentum does not algebraically guarantee cancellation of differential factor loading'],
          'evidence_limit':'These structural risks do not prove actual correlation or actual rejection probability. Source integrity and larger issuer counts do not establish time-group independence.',
          'power_reference':'phase3e_power_mde_v003.json','power_scope':'Prior conditional synthetic evidence only; no real tracking error or power estimate',
          'method_search':False,'real_performance_inputs':0}
    sources={'version':'phase3_final_source_registry_v001','counts':dict.fromkeys(['SEC','OpenFIGI','Tiingo','FMP','documentation_HTTP','browser','Orbis','Nexus','Aurora'],0),
             'successes':0,'failures':0,'new_source_debit':0,'account_wide_debit':'UNKNOWN','pacing_issues':[],
             'requests':[],'reason':'Section29 upstream inference stop; no source request dispatched','git_and_ci':'Separate delivery metadata, not research source requests'}
    outcomes={'REVENUE_CANONICALIZATION':'PARTIAL_PRIOR_EVIDENCE','ACCOUNTING_PERIMETER_CERTIFICATION':'BLOCKED_PRIOR_EVIDENCE',
     'REVENUE_TRIPLE_FEASIBILITY':'29_RETAINED_REVIEW_DEFERRED_INFERENCE_STOP','HISTORICAL_SECURITY_IDENTITY':'PARTIAL_PRIOR_60_CASES',
     'CORPORATE_ACTION_LIFECYCLE':'PARTIAL_PRIOR_EVIDENCE','TERMINAL_VALUE_EVIDENCE':'BLOCKED_PRIOR_0_CERTIFICATES',
     'PRICE_SOURCE_CERTIFICATION':'PARTIAL_PRIOR_BOUNDED_QA','HISTORICAL_NAV_FEASIBILITY':'BLOCKED_PRIOR_0_PATHS',
     'HISTORICAL_UNIVERSE_FEASIBILITY':'BLOCKED','PUBLIC_ELIGIBILITY_POLICY':'OWNER_APPROVED_NOT_ACTIVATED',
     'PUBLIC_ELIGIBILITY_ACTIVATION_READINESS':'BLOCKED','STAGE_C_ADAPTER':'NOT_IMPLEMENTED_DEFERRED_INFERENCE_STOP',
     'STAGE_ISOLATION':'EXISTING_CONTROLS_PRESERVED_NO_NEW_STAGE_OPENED','INFERENCE_HYPOTHESIS_STRUCTURE':'OWNER_APPROVED_UNCHANGED',
     'INFERENCE_CALIBRATION':'CONDITIONAL_PRIOR_PASS_KNOWN_CROSSYEAR_FAILURE','INFERENCE_REAL_ASSUMPTIONS':'UNJUSTIFIED_COMMON_FACTOR_RESTRICTION',
     'INFERENCE_IMPLEMENTATION':'BLOCKED','TRIAL_FAMILY':'45_CEILING_PRESERVED_NO_NEW_INVENTORY_ADOPTED',
     'PROOF_COMPILER_REAL_DESIGN_CHECK':'NOT_IMPLEMENTED_DEFERRED_INFERENCE_STOP','LOCAL_EXECUTION_ROUTE':'PARTIAL_SYNTHETIC_PRIOR_EVIDENCE',
     'NEXUS_EXECUTION':'BLOCKED_DISABLED','EXP005_FREEZE_READINESS':'NOT_READY','PHASE3_COMPLETION':'COMPLETE_EXP005_ABANDONED'}
    inputs=['availability_policy_v003_approved.json','availability_policy_v003_proposed.json','phase3e_inference_protocol_v003.json',
            'phase3e_inference_calibration_v003_correction_001.json','phase3d_accounting_review.json','phase3d_identity_closure.json',
            'phase3d_terminal_closure.json','phase3c_evidence.json','phase3e_nav_feasibility.json','phase3e_power_mde_v003.json']
    summary={'version':'phase3_final_summary_v001','verdict':'ABANDON_EXP005','PHASE3_COMPLETION':'COMPLETE_EXP005_ABANDONED',
     'verdict_scope':'Approved Stage C confirmatory experiment under the current required certification standard and fixed method; not falsification of the revenue hypothesis or all alternative designs',
     'decision_basis':'Mandatory inference assumptions lack defensible design-based bounds; exact common-factor counterexample and frozen stress failure. No certified bounded remedy preserving fixed design/method is established.',
     'stop_authority':'Owner final instruction section29; implementation order in section30 is approximate',
     'stop_consequence':'29-chain and60-case campaigns, new price acquisition, real NAV certification, adapter and dry compiler implementation are explicitly deferred, not completed or claimed passed',
     'future_owner_choice':'No decision required to complete this stop. Any attempt to reopen this experiment would require a separate owner instruction addressing the inferential restriction; no automatic planning phase or source campaign.',
     'EXP004':'OPERATIONALLY_PAUSED','EXP005':'ABSENT_NOT_REGISTERED_NOT_FROZEN_NO_REAL_PERFORMANCE_NOT_READY',
     'accounting_prior_certified':0,'accounting_denominator':29,'identity_full_spans':0,'identity_denominator':60,
     'terminal_certificates':0,'nav_certified_paths':0,'policy_activated':False,'public_availability':'UNKNOWN',
     'salesforce_conflict':'UNAVAILABLE_UNCHANGED','gates':outcomes,'input_file_hashes':{n:file_hash(DOCS/n) for n in inputs},
     'new_simulations':0,'real_performance_inputs':0,'new_source_requests':0}
    outputs={'phase3_final_summary.json':summary,'phase3_final_inference_certificate.json':cert,'phase3_final_source_registry.json':sources,
     'phase3_final_revenue_certification.json':{'denominator':29,'prior_certified_triples':0,'new_certified_triples':0,'completed_new_accounting_reviews':0,'status':'DEFERRED_INFERENCE_STOP','chains':chains},
     'phase3_final_identity_certification.json':{'denominator':60,'prior_status_counts':identity['status_counts'],'prior_full_spans':0,'new_reviews':0,'status':'DEFERRED_INFERENCE_STOP','cases':identity['cases']},
     'phase3_final_terminal_certification.json':{'frame_denominator':60,'prior_completion_documents':terminal['completion_document_denominator'],'prior_reviewed_disclosures':terminal['reviewed_disclosed_claims'],'certified_position_terminal_cases':0,'status':'DEFERRED_INFERENCE_STOP','prior_claims':terminal['claims'],'cases':[{'case_key':r['case_key'],'prior_terminal_status':r['terminal_status'],'new_review_status':'DEFERRED_INFERENCE_STOP','terminal_certificate':False} for r in identity['cases']]},
     'phase3_final_price_certification.json':{'denominator':60,'status':'PARTIAL_PRIOR_QA_NEW_CAMPAIGN_DEFERRED','prior_metrics':market['market_metrics'],'approved_warmup':'2019-02-28','StageC_coverage_certified':False,'new_requests':0},
     'phase3_final_nav_feasibility.json':{'denominator':60,'certified_paths':0,'new_real_paths_computed':0,'status':'DEFERRED_INFERENCE_STOP','cases':oldnav['cases']},
     'phase3_final_policy_activation_review.json':{'policy_sha256':digest(policy),'owner_approval':'RECORDED_UNCHANGED','activation':'NOT_ACTIVATED','readiness':'BLOCKED','exact_public_availability':'UNKNOWN','salesforce_conflict':'UNAVAILABLE','source_and_stage_prerequisites':'UNSATISFIED_UNCHANGED'},
     'phase3_final_exp005_readiness.json':{'verdict':'ABANDON_EXP005','freeze_readiness':'NOT_READY','experiment_registered':False,'experiment_frozen':False,'performance_authorized':False,'gates':outcomes}}
    return outputs


def generate(check=False):
    outputs=build();s=outputs['phase3_final_summary.json'];c=outputs['phase3_final_inference_certificate.json']
    def percent_range(values):return f'{100*min(values):.1f}–{100*max(values):.1f}%'
    rejected=percent_range([r['primary_rejection']['fraction'] for r in c['known_failure_rows']])
    covered=percent_range([r['coverage']['fraction'] for r in c['known_failure_rows']])
    power=load('phase3e_power_mde_v003.json')
    default=next(r for r in power['rows'] if r['geometry']=='C' and r['iid_annual_tracking_error']==.025)
    point=next(r for r in default['points'] if r['effect']==.02)
    primary_power=percent_range(point['primary_rejection_range']);support_power=percent_range(point['full_support_range'])
    mdes='/'.join(f"+{100*next(r for r in power['rows'] if r['geometry']=='C' and r['iid_annual_tracking_error']==noise)['mde_grid_upper_bound']:g}" for noise in [.025,.05,.1])
    gate='| Gate | Verdict |\n| --- | --- |\n'+'\n'.join('| '+k+' | '+v+' |' for k,v in s['gates'].items())
    outputs={n:json.dumps(v,sort_keys=True,indent=2)+'\n' for n,v in outputs.items()}
    outputs['phase3_final_gate_review.md']='# Final Phase 3 gates\n\n'+gate+'\n\nAbandonment is a closure verdict for the approved confirmatory design, not an experiment registration or a statement that the economic hypothesis has no alpha. Deferred campaigns did not pass.\n'
    outputs['phase3_final_stage_adapter_review.md']='# Stage C adapter and dry compiler disposition\n\n**Not implemented: deferred at the mandatory upstream inference stop.** Existing Test/paper controls and synthetic-only compiler remain unchanged. Development and owner-held confirmation were not opened. No real-design dry compilation was attempted; no structural readiness certificate is claimed. Adapter work cannot remedy the missing scientific dependence restriction. The 45-evaluation ceiling remains unchanged; no revised inventory, performance slots or method is adopted.\n'
    validation=DOCS/'phase3_final_validation.json'
    checked=json.loads(validation.read_bytes()) if validation.exists() else {}
    results=f"{checked.get('local_tests_passed','pending')} local tests; {checked.get('public_tests_passed','pending')} public tests; {checked.get('tests_skipped','pending')} skipped"
    outputs['phase3_final_report.md']=f'''# Final Phase 3: approved experiment certification stop

**ABANDON_EXP005. PHASE3_COMPLETION = COMPLETE_EXP005_ABANDONED.** As of 2026-10-12, starting from `05aca92`. The [fixed final plan](phase3_final_plan.md) and [complete owner instruction](owner_phase3_final_2026-10-12.md) prohibit further design/method search and require a stop when inference cannot be defended. This is a closure decision for the approved confirmatory experiment under the required scientific standard. It does not falsify revenue acceleration, invalidate Research OS, or prove that every possible alternative experiment is impossible.

## Decisive inference obstruction

The approved Student reference requires independent approximately Gaussian annual group means with common mean and variance proportional to inverse session counts. Stage C has five groups, with 251, 250, 252, 250 and 187 sessions. Repeated issuer exposures, annual signal persistence, overlapping holdings and shared regimes make a persistent differential common factor admissible. Matching momentum on the same population does not enforce equal factor loadings. These structural risks do not prove actual return dependence; no actual candidate/control returns are inspected.

For the zero-mean common-factor model `X_g = theta + Z + epsilon_g`, with independent Gaussian components and `Var(epsilon_g)=sigma²/n_g`, the weighted mean contains `Z` but every demeaned residual cancels it. Consequently:

- True mean variance is `Var(Z) + sigma²/sum(n_g)`.
- Expected Student estimated mean variance is only `sigma²/sum(n_g)`.
- As common-factor variance grows, one-sided primary false rejection tends to 50% and two-sided interval coverage tends to zero. These are analytical limits, not measured real error rates.

The method therefore cannot be certified uniformly over this unrestricted dependence class. Neither source integrity, a larger issuer count nor calendar-year grouping bounds the omitted term. The current source/design evidence supplies no independently justified restriction or differential-loading cancellation. No bounded remedy preserving the fixed method/design has been established; additional filing/identity downloads would not provide that statistical guarantee. A counterexample is not proof that the actual process follows it: the obstruction is inability to establish the required restriction before freezing the confirmatory inference.

The [inference certificate](phase3_final_inference_certificate.json) retains all three **previously frozen** C common-crossyear zero-effect rows: primary rejection {rejected}, coverage {covered}. They remain stress diagnostics, not retroactively relabeled certification worlds. The earlier conditional certification-world passes and +5-point power result are preserved; they do not certify real independence. Prior default-noise +2-point primary power was {primary_power}, and combined materiality/stress support {support_power}. The IID fixed-grid MDE upper bounds for C were {mdes} points at 2.5/5/10-point noise. No new simulation, tracking-error estimate or method search occurred.

One primary discovery, one-sided alpha 0.05, positive two-sided 95% lower endpoint against zero, estimated annual mean at least two points and positive double-cost/+1/+5 estimates remain unchanged. Approved v003 and Stage C remain planning approval only; they are not rescinded or activated by this scientific closure verdict.

## Retained denominators and deferred work

| Workstream | Prior evidence retained | New certification campaign |
| --- | --- | --- |
| Revenue | 29 triples / 89 originals / 30 issuers; 0 fully certified | 0 completed new accounting reviews; all 29 explicitly deferred |
| Identity | 60 cases: 52 point-only, 6 unresolved, 1 ambiguous, 1 end-only; 0 full spans | All 60 retained; no new effective-span review |
| Terminal | 60 cases, 10 completion-document sets, 6 scoped disclosures; 0 position certificates | Deferred; disclosed consideration never becomes realized cash |
| Price | Prior 22,075 rows; 41 diagnostic full-calendar passes, not listed-history certificates | No Stage C acquisition or coverage certification |
| NAV/universe | 0 complete NAV paths / 60 cases; population uncertified | No real path, holding or population constructed |
| Stage adapter / dry compiler | Prior controls and synthetic-only compiler preserved | Not implemented; upstream stop, no readiness claim |
| Trial family | Existing 45 ceiling, no performance | Inventory remapping deferred; no new slots adopted |

These are **deferred campaigns**, not 29 failed complete accounting reviews or 60 completed identity reviews. Every chain/case remains in the linked machine-readable artifacts with its prior evidence and explicit stop status. The stop under owner section 29 precedes downstream acquisition and implementation; section 30 permits an approximate order. This package does not claim that source issues are inherently insoluble. No paid source was sought, and no inaccessible resource caused this stop.

## Policy and experiment boundaries

V003 hash `438d7bcf7d091f596009ba841e6dacbd960c18493c34ffec798d8c1aaf1dacbd` remains approved for planning, inactive, scope 2018-02-28–2026-09-30. Exact public availability stays UNKNOWN and Salesforce contributor `0001108524-22-000008` unavailable. V002 is unchanged. Source warm-up 2018-02-28, required price warm-up 2019-02-28, Development 2020-03-02–2021-12-31 and owner-held confirmation 2022-01-01–2026-09-30 are preserved. No real policy view is activated.

EXP004 remains operationally paused. EXP005 remains absent, unregistered, unfrozen, with no real performance and freeze readiness NOT_READY. ABANDON_EXP005 is this report's feasibility disposition; no experiment-state mutation or deletion occurred. All source, class, terminal, calendar, population and execution gates remain fail-closed. Nexus adapter stays disabled.

## Verification and stop

Validation: {results}. [Validation receipt](phase3_final_validation.json), [complete gates](phase3_final_gate_review.md), [canonical summary](phase3_final_summary.json), [source registry](phase3_final_source_registry.json). New SEC/OpenFIGI/Tiingo/FMP/documentation/browser/Orbis/Nexus/Aurora requests all zero; no acquisition failures, rate-limit issues or new source charge. Account-wide usage remains unknown. Git/hosted-CI metadata are separate delivery operations.

```sh
python -m src.research.phase3_final --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

Public regeneration uses tracked prior evidence only. New tests check the deterministic synthetic variance obstruction; no real return loader or acquisition command exists. Legacy regression checks use already-opened EXP001 data and do not authorize new held-out research access. No new signals, ranks, portfolios, performance, confirmation results, optimization, purchases, paper/live or Phase 4A occurred.

**Stopped under owner section 29.** No bounded owner decision is required to complete this closure. Reopening the same experiment would require a separate instruction addressing the missing inferential restriction; it cannot be inferred from source access or the existing planning approval. No next planning phase is proposed or started.
'''
    for name,text in outputs.items():
        p=DOCS/name
        if check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:raise ValueError('Final report mismatch: '+name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    return len(outputs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    print('Final closure artifacts:',generate(parser.parse_args().check))
