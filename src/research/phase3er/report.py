"""Reports and owner packet from canonical metadata and two preserved toy runs."""
import json,re
from datetime import datetime,date
from src.research.spec import digest
from src.research.phase3d.proof import file_hash
from .sources import DOCS
from .audit import source_ledger
from .calendar import sessions,open_utc,NY,MAX_CALENDAR


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |',
        *['| '+' | '.join(map(str,row))+' |' for row in rows]])


def load(name):return json.loads((DOCS/name).read_bytes())


def metadata_representation_review(policy,clock):
    """Ancillary literal-ISO sensitivity; never certify the producer's Z semantics."""
    source=load('phase3e_redesign_source_metadata.json');index={r['accession']:r for r in clock['records']}
    days=sessions(date.fromisoformat(policy['scope'][0]),MAX_CALENDAR);rows=[]
    for r in source['records']:
        original=r.get('metadata_acceptance_representation');base=index[r['accession']]
        try:
            instant=datetime.fromisoformat(original.replace('Z','+00:00'))
            if instant.tzinfo is None:raise ValueError('Unlabelled metadata instant')
            later=[d for d in days if d>max(instant.astimezone(NY).date(),date.fromisoformat(r['filing_date']))]
            bound=open_utc(later[1]).isoformat()
            status='BASE_CLOCK_UNAVAILABLE' if base['status']!='INVARIANT' else 'LITERAL_ISO_BOUND_MATCHES' if bound==base['mechanical_bound_utc'] else 'REPRESENTATION_BOUND_CONFLICT'
        except (ValueError,TypeError,AttributeError,IndexError):instant=None;bound=None;status='UNAVAILABLE_METADATA_REPRESENTATION'
        rows.append({'accession':r['accession'],'original_metadata_representation':original,
                     'literal_iso_utc_candidate':instant.isoformat() if instant else None,'literal_metadata_bound_utc':bound,
                     'base_clock_status':base['status'],'status':status,'counterfactual_not_observed_clock':True,'trading_eligible':False})
    return {'version':'phase3er_metadata_representation_review_v001','policy_sha256':digest(policy),'denominator':len(rows),
            'records':rows,'same_bounds':sum(r['status']=='LITERAL_ISO_BOUND_MATCHES' for r in rows),
            'base_unavailable':sum(r['status']=='BASE_CLOCK_UNAVAILABLE' for r in rows),
            'limitations':'Raw metadata ISO and SGML representations retained; literal Z interpretation is sensitivity evidence, never proof of producer timezone or historical publication'}


def power_resolution(cal):
    rows=[]
    for geo in ('A','B','C'):
        for method in ('session_weighted_group_student','symmetric_group_sign'):
            for noise in (.01,.025,.05,.10):
                passing=[];points=[]
                for effect in (.02,.05,.10,.15,.20):
                    found=[r for r in cal['power_sensitivity'] if r['geometry']==geo and r['method']==method and r['annual_tracking_error']==noise and r['annual_effect']==effect]
                    minimum=min(r['full_support']['wilson95'][0] for r in found)
                    if minimum>=.8:passing.append(effect)
                    points.append({'effect':effect,'minimum_full_support_lower95':minimum,
                        'primary_rejection_range':[min(r['primary_rejection']['fraction'] for r in found),max(r['primary_rejection']['fraction'] for r in found)],
                        'full_support_range':[min(r['full_support']['fraction'] for r in found),max(r['full_support']['fraction'] for r in found)],
                        'mean95_interval_width_range':[min(r['mean_interval_width'] for r in found),max(r['mean_interval_width'] for r in found)] if all(r['mean_interval_width'] is not None for r in found) else None})
                first=min(passing) if passing else None
                rows.append({'geometry':geo,'method':method,'iid_annual_tracking_error':noise,'mde_grid_upper_bound':first,
                             'mde_grid_lower_bound':max((e for e in (.02,.05,.10,.15,.20) if first and e<first),default=0) if first else .20,
                             'interpretation':'Fixed-grid complete-support80% Wilson-lower threshold; not interpolated or real power','points':points})
    return {'version':'phase3er_power_mde_v003','target_power':.8,'rows':rows,'real_tracking_error':'UNKNOWN',
            'materiality_boundary':'At true effect0.02, symmetric estimated-floor acceptance cannot exceed50%; primary-test and full-support power are separately reported'}


def source_coverage(geometry):
    originals={a for r in load('phase3c_evidence.json')['chains'] for a in r['filing_accessions']}
    rows=[]
    for candidate in geometry['candidates']:
        for role,w in [('Development',candidate['development_geometry']),*zip(candidate['confirmation_roles'],candidate['confirmation_geometry'])]:
            states=[s for s in geometry['contributor_states'] if s['mechanical_bound_utc'] and w['bounds'][0]<=s['mechanical_bound_utc'][:10]<=w['bounds'][1]]
            panel=w['monthly_panel'];counts=[r['mechanically_available_issuers'] for r in panel]
            rows.append({'geometry':candidate['id'],'role':role,'bounds':w['bounds'],
                         'metadata_events_with_predecessors':len(states),'events_with_all_three_old_financial_original_bodies':sum(set(s['accessions'])<=originals for s in states),
                         'minimum_mechanical_issuer_count':min(counts),'maximum_mechanical_issuer_count':max(counts),'fixed_frame_denominator':30,
                         'accounting_certified':0,'trading_eligible':0,'financial_body_coverage_for_new_headers':'NOT_ACQUIRED'})
    return {'version':'phase3er_source_coverage_annotation_v001','original_financial_body_count':len(originals),'metadata_original_count':250,
            'rows':rows,'mechanical_counts':'Upper-bound possible contributor states, not latest-signal eligibility; newer missing/amended facts can invalidate states',
            'population':'Selected30-issuer feasibility frame, not full US equity denominator; minimum100/500 production requirements unestablished'}


def generate(check=False):
    p=load('availability_policy_v003_proposed.json');g=load('phase3e_stage_geometry.json');clock=load('phase3e_policy_v003_invariance.json')
    cal=load('phase3e_inference_calibration_v003_correction_001.json');original=load('phase3e_inference_calibration_v003.json')
    power=power_resolution(cal);coverage=source_coverage(g);ledger=source_ledger()
    representations=metadata_representation_review(p,clock)
    qualified=[r for r in cal['candidate_verdicts'] if all(r[k] for k in ('null_gate','coverage_gate','bounded_interval','useful_power'))]
    if qualified!=[next(r for r in cal['candidate_verdicts'] if r['geometry']=='C' and r['method']=='session_weighted_group_student')]:
        raise ValueError('Frozen comparison no longer supports this conditional recommendation; new reviewed report required')
    recommendation={'version':'phase3er_stage_recommendation_v001','verdict':'STAGE_DESIGN_READY_FOR_OWNER_REVIEW','recommended_geometry':'C',
        'development':['2020-03-02','2021-12-31'],'historical_owner_held_confirmation':['2022-01-01','2026-09-30'],
        'formation_research_cutoff':'2021-12-31','design_metadata_cutoff':'2026-09-30','research_date':'2026-10-12',
        'source_warmup_start':g['filing_warmup_start'],'price_warmup_start':g['price_warmup_start'],
        'policy_scope':p['scope'],'policy_sha256':digest(p),'policy_status':p['status'],
        'inference_architecture':'One primary one-sided alpha0.05; positive two-sided95 lower bound; estimated mean>=0.02; positive double-cost/delay stresses',
        'method':'session_weighted_group_student','method_certification':'CONDITIONAL_SYNTHETIC_ONLY_REAL_ASSUMPTIONS_UNESTABLISHED',
        'year_sign_proposal':'At least ceil(two-thirds of year parts) positive: both2 Development parts;4/5 holdout parts including partial2026',
        'trial_ceiling':'Prior45 ceiling retained; no real trials or new signals; revised stage inventory needs explicit later review',
        'inference_prerequisite_revision':'Proposed group-reference/calibration contract replaces old six annual-equivalent, three/window and HAC252/504 effective-size prerequisites; old artifacts and real gates unchanged',
        'power_scope':'Conditional confirmation statistical/materiality/stress-mean support only; excludes Development advancement, year-sign/contributor-concentration and all source/execution gates',
        'stage_adapter':'NOT_IMPLEMENTED; owner-held confirmation must retain human Test/paper controls; old real stage gates unchanged',
        'tradeoffs':['Only22 Development decisions; weaker diagnosis/regime breadth','No separate independent historical Validation/Test replication',
                    'Largest candidate-specific workflow-held-out tape; prior market/cross-experiment knowledge remains',
                    'One CRM chronology conflict retained; all accounting/class/terminal/source coverage uncertified',
                    'Reference calendar only; actual per-security/exchange calendars require class certification',
                    'Synthetic80% screen at5points/2.5point noise; no80% two-point real-alpha claim'],
        'performance_authorized':False,'policy_activated':False,'EXP005_FREEZE_READINESS':'NOT_READY'}
    gates={'CURRENT_POLICY':'V002_APPROVED_PILOT_PRESERVED_NOT_ACTIVATED','PROPOSED_POLICY_V003':'PROPOSED_NOT_APPROVED',
        'POLICY_SCOPE_COMPATIBILITY':'COVERED_FOR_PROPOSED_BOUNDED_GEOMETRY_NOT_AUTHORIZATION','POLICY_CLOCK_INVARIANCE':'249_INVARIANT_1_SOURCE_CHRONOLOGY_CONFLICT',
        'STAGE_SOURCE_GEOMETRY':'METADATA_REFERENCE_CALENDAR_ONLY_CERTIFIED_TRADING_COUNT_ZERO','STAGE_HOLDOUT_INTEGRITY':'CANDIDATE_SPECIFIC_WORKFLOW_HELD_OUT_WITH_DISCLOSED_PRIOR_KNOWLEDGE',
        'INFERENCE_HYPOTHESIS_STRUCTURE':'FROZEN_SINGLE_PRIMARY_PLUS_MANDATORY_STRESSES_PROPOSAL','MATERIALITY_RULE':'ESTIMATED_TWO_POINT_FLOOR_PLUS_EVIDENCE_AGAINST_ZERO',
        'INFERENCE_RESOLUTION':'STUDENT_CONTINUOUS_SIGN95_INTERVAL_INFEASIBLE','INFERENCE_CALIBRATION':'CONDITIONAL_MODEL_GATES_PASS_CORRECTED_RUN',
        'INFERENCE_POWER':'C_PASSES_FIXED_FIVE_POINT_SYNTHETIC_SCREEN_REAL_POWER_UNKNOWN','MINIMUM_DETECTABLE_EFFECT':'NO_REAL_MDE_IID_SENSITIVITY_REPORTED',
        'STAGE_DESIGN_FEASIBILITY':'STAGE_DESIGN_READY_FOR_OWNER_REVIEW','PUBLIC_ELIGIBILITY_ACTIVATION_READINESS':'BLOCKED_OWNER_AND_SOURCE_IDENTITY_CALENDAR_GATES',
        'EXP005_FEASIBILITY':'CONDITIONAL_STAGE_PLAN_ONLY_SCIENTIFIC_CERTIFICATION_REMAINS_INCOMPLETE','EXP005_FREEZE_READINESS':'NOT_READY','NEXUS_EXECUTION':'BLOCKED'}
    summary={'version':'phase3er_redesign_summary_v001','baseline':'87f23f6198f096d611918b24eac0080b3350aa60','gates':gates,
             'recommendation':recommendation,'sources':ledger,'clock_denominator':250,'clock_status_counts':clock['status_counts'],
             'source_financial_originals_unchanged':89,'real_certified_triples':0,'real_certified_identity_spans':0,'real_terminal_nav_paths':0,
             'inference_runs':2,'unique_synthetic_noise_realizations_per_run':86400,'both_runs_preserved':True,
             'corrected_non_ar_and_null_invariants_exact':True,'correction_disclosure':'phase3e_v003_generator_correction.md',
             'inputs':{n:file_hash(DOCS/n) for n in ('availability_policy_v003_proposed.json','phase3e_stage_geometry.json','phase3e_policy_v003_invariance.json',
                    'phase3e_inference_protocol_v003.json','phase3e_inference_calibration_v003.json','phase3e_inference_calibration_v003_correction_001.json')},
             'EXP004':'PAUSED','EXP005':'ABSENT_NOT_READY','Nexus_Aurora_operations':0,'next_phase_started':False}
    stage_table=table(['Candidate','Development sessions / months','Confirmation sessions / months / annual groups','Useful-power gate'],
        [(c['id'],f"{c['development_geometry']['sessions']} / {c['development_geometry']['monthly_decisions']}",
          f"{c['confirmation_sessions']} / {sum(w['monthly_decisions'] for w in c['confirmation_geometry'])} / {c['confirmation_year_groups']}",
          next(v['useful_power'] for v in cal['candidate_verdicts'] if v['geometry']==c['id'] and v['method']=='session_weighted_group_student')) for c in g['candidates']])
    calibration_table=table(['Geometry','Maximum null rejection / maximum Wilson upper','Minimum95 coverage / minimum Wilson lower','Worst +5 support / Wilson lower'],
        [(geo,*[
           f"{max(r['primary_rejection']['fraction'] for r in rows if r['annual_effect']==0):.1%} / {max(r['primary_rejection']['wilson95'][1] for r in rows if r['annual_effect']==0):.1%}",
           f"{min(r['coverage']['fraction'] for r in rows):.1%} / {min(r['coverage']['wilson95'][0] for r in rows):.1%}",
           f"{min(r['full_support']['fraction'] for r in rows if r['annual_effect']==.05):.1%} / {min(r['full_support']['wilson95'][0] for r in rows if r['annual_effect']==.05):.1%}"])
         for geo in ('A','B','C') for rows in [[r for r in cal['rows'] if r['geometry']==geo and r['method']=='session_weighted_group_student' and r['role']=='CERTIFICATION']]])
    power_table=table(['Candidate / iid noise (annual points)','Primary power at +2','Full support at +2 / +5 / +10','MDE80 grid upper / expected95 width at MDE (points)'],
        [(f"{r['geometry']} / {r['iid_annual_tracking_error']*100:g}",
          f"{r['points'][0]['primary_rejection_range'][0]:.1%}–{r['points'][0]['primary_rejection_range'][1]:.1%}",
          ' / '.join(f"{x['full_support_range'][0]:.1%}–{x['full_support_range'][1]:.1%}" for x in r['points'][:3]),
          f"{r['mde_grid_upper_bound']*100:g} / "+'–'.join(f'{v*100:.2f}' for v in next(x['mean95_interval_width_range'] for x in r['points'] if x['effect']==r['mde_grid_upper_bound'])) if r['mde_grid_upper_bound'] else '>20 / unavailable')
         for r in power['rows'] if r['method']=='session_weighted_group_student'])
    stress_table=table(['Stress world / C Student, zero effect','Primary rejection range','95 coverage range'],
        [(world,f"{min(r['primary_rejection']['fraction'] for r in rows):.1%}–{max(r['primary_rejection']['fraction'] for r in rows):.1%}",
          f"{min(r['coverage']['fraction'] for r in rows):.1%}–{max(r['coverage']['fraction'] for r in rows):.1%}")
         for world in dict.fromkeys(r['world'] for r in cal['rows'] if r['geometry']=='C' and r['method']=='session_weighted_group_student' and r['role']=='STRESS_DIAGNOSTIC')
         for rows in [[r for r in cal['rows'] if r['geometry']=='C' and r['method']=='session_weighted_group_student' and r['world']==world and r['annual_effect']==0]]])
    gate_table=table(['Gate','Disposition'],gates.items())
    vpath=DOCS/'phase3e_redesign_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else None
    validation=f"{v['tests_passed']} full local tests, {v['tests_skipped']} skipped; {v['public_tests_passed']} public tests passed." if v else 'Final validation pending.'
    texts={
 'phase3e_redesign_report.md':f'''# Phase 3E-R: historical design and modeled timing proposal

**Stage C is conditionally READY_FOR_OWNER_REVIEW; EXP005 remains NOT_READY.** As of2026-10-12. The owner's new instruction retires the old mandatory 6/3/3 programme. No existing phase report, policy approval or frozen experiment is rewritten. This pass uses metadata/header acquisition, reference-calendar counts and synthetic inference only.

## Scope and source evidence

The proposed policy covers **{p['scope'][0]} through {p['scope'][1]}**, hash `{digest(p)}`. Its start covers the earliest predecessor source receipt actually used; its endpoint is a completed quarter, not future2026-12-31. Elapsed calendar buffer dates end2026-10-09. V002 remains approved for2015–2021 and unchanged; v003 remains PROPOSED_NOT_APPROVED and unactivated. Exact first-public availability stays UNKNOWN. [Exact owner packet](availability_policy_v003_review_packet.md).

All30 revenue candidates remain. 250 first-original annual metadata/header records cover fiscal endpoints2018 through the elapsed cutoff; 89 original financial source sets remain unchanged. New requests were SEC161 and official calendar Documentation4, all200; 89 headers reused original archives. Browser method/calendar review adds10 separately logged operations. OpenFIGI/Tiingo/FMP/Orbis/Nexus/Aurora remain0. No price history, later financial facts, full submissions or full-market backfill were acquired. [Source ledger](phase3e_redesign_source_registry.json).

Reference-calendar clock probes return **249 invariant /1 unresolved**. Salesforce accession `0001108524-22-000008` retains acceptance `20220224161345`, filed-as-of `20210317` and report period `20210131`; the archived header and metadata agree on the earlier filing date but contradict the later acceptance chronology. No correction or earlier availability is inferred. Every contributor state containing that source remains unavailable; the case stays in the denominator. This is source chronology failure, not proof that a two-session rule resolves the source timestamp. [All probes and failures](phase3e_policy_v003_invariance.json).

The [NYSE calendar/hours](https://www.nyse.com/trade/hours-calendars), archived yearly calendars and [mourning memo](https://www.nyse.com/publicdocs/nyse/markets/american-options/rule-interpretations/2025/National_Day_of_Mourning_20250102.pdf) support a separate opening/full-day-closure reference extension, including2025-01-09. Earlier calendar/metric code is unchanged. Exchange/class-specific and execution-close calendars remain prerequisites; this is not a complete tradable-security calendar certificate. DST, near-midnight, holiday/weekend, chronology/contradiction and cutoff failures have public tests.

## Bounded stage comparison

{stage_table}

A uses Development2020-03-02–2023-12-31, Validation2024 and Test2025–2026-09-30. B uses Development2020-03-02–2022-12-31, Validation2023–2024 and Test2025–2026-09-30. C uses Development2020-03-02–2021-12-31 and one owner-held historical confirmation2022-01-01–2026-09-30. Partial2020/2026 periods are not full years. C preserves more candidate-specific confirmation evidence and is the only geometry passing the corrected frozen useful-power screen; it sacrifices Development breadth and separate historical replication. A/B fit existing three-stage concepts more directly. C needs a separately reviewed owner-held confirmation mapping that preserves human Test/paper controls; no real stage adapter is enabled here.

Filing warm-up starts **{g['filing_warmup_start']}**; the253-prior-session price warm-up would start **{g['price_warmup_start']}**, but those prices were not acquired. Candidate-formation research cutoff would be2021-12-31 for C, distinct from this pass's authorized metadata cutoff2026-09-30 and actual research date2026-10-12. Later metadata inspection is disclosed and cannot authorize later financial facts for candidate formation.

Initial mechanical frame availability is only1/30 at the first proposed monthly decision; later counts reach30. These are upper-bound contributor states, not a latest-signal eligible universe. Accounting-certified and trading-eligible counts remain0, as do full identity/terminal certificates. Existing89 financial bodies do not cover the later header-only events. [Complete source/body coverage annotation](phase3e_redesign_source_coverage.json) and [all monthly geometry](phase3e_stage_geometry.json) preserve missingness. The frame is deliberately selected feasibility evidence; production100-monthly/500-window issuer and event/participation requirements are unestablished. The proposed inception can still fail source certification; no difficult issuer is dropped.

## Frozen inference, correction and power

[Hierarchy review](phase3e_inference_hierarchy_review.md) proposes one primary discovery with mandatory positive cost/delay stresses. Estimated annual mean>=2points and a positive two-sided95 lower endpoint retain the original materiality intent; the lower bound is against zero, not above2points. Year-sign proposal: both Development year parts and at least4/5 holdout year parts positive. No K, signal, momentum, cost or holding parameter is tuned.

V003 protocol, geometries and methods froze at`0a7f790` before simulation. The first full run had an AR innovation normalization error and is preserved. [Analytical correction001](phase3e_v003_generator_correction.md) froze at`c572ce3` before one rerun: total innovation factor becomes1−rho, matching the declared long-run noise. No threshold, method, date, seed, world or effect changed. Non-AR/IID outputs and all zero-effect rejection/coverage counts match exactly across runs. Both600-replication runs are archived;86400 unique synthetic noise realizations/run. [Original results](phase3e_inference_calibration_v003.json); [corrected results](phase3e_inference_calibration_v003_correction_001.json).

{calibration_table}

The Student kernel keeps exact session weights and a finite-group reference under independent approximately Gaussian, common-mean groups with inverse-session-count variance. Real annual independence/variance assumptions remain UNESTABLISHED. The exact symmetric-group alternative has no bounded two-sided95 interval at three/four/five groups and cannot advance. Calibration success is conditional to predeclared worlds; the following assumption-violating stress diagnostics remain failures/limitations:

{stress_table}

{power_table}

Noise is a synthetic sensitivity parameter, never estimated from real strategy returns. MDE entries are the first passing fixed-grid upper bound; no interpolation or true minimum is claimed. At the true2-point estimated-floor boundary, full acceptance cannot reach80% for a symmetric estimate even if the primary test has power. At the default2.5-point noise, none of these geometries has80% primary-test power at+2points; C supports the predeclared+5-point screen under the corrected certification worlds. Higher tracking error materially increases MDE. [All power/width/range evidence](phase3e_power_mde_v003.json). This does not certify real alpha or actual power.

## Gates and stop

{gate_table}

**Validation:** {validation} [Receipt](phase3e_redesign_validation.json). Commands:

```sh
python -m src.research.phase3er report --check
python -m src.research.phase3er geometry --check
python -m src.research.phase3er audit
python -m src.research.public_checks
python -m unittest discover -s tests -v
```

Report/geometry reproduction uses public canonical metadata; archive/freeze audit needs ignored originals and receipts. Acquisition is an explicit remote command, never routine reproduction. Software checks use already-opened EXP001 fixtures only for regression; no new heldout research/performance access occurs. Historical confirmation is workflow-held-out for this candidate, with prior market and cross-experiment knowledge disclosed, not genuinely forward unseen. Only later logged future paper evidence can earn that description.

**Stop for owner review of the exact v003 policy and conditional Stage C design.** Approval would permit recording that modeling/design decision only; it does not certify sources/assumptions, activate eligibility, authorize more acquisition, create/freeze EXP005 or open performance. Existing EXP004 pause, source/experiment history and v002 approval remain intact. No Nexus/Aurora, purchases, optimization, graph, causal platform, paper/live activity or Phase4A occurred.
''',
 'availability_policy_v003_review_packet.md':f'''# V003 owner decision packet

**PROPOSED_NOT_APPROVED; NOT_ACTIVATED.** Exact proposed scope: **{p['scope'][0]}–{p['scope'][1]}**. Canonical policy SHA-256: `{digest(p)}`. [Exact JSON definition](availability_policy_v003_proposed.json), [250 contributor probes](phase3e_policy_v003_invariance.json), [stage recommendation](phase3e_stage_recommendation.json), [full report](phase3e_redesign_report.md).

Rule, copied exactly from v002: `{p['rule']}`. Plausible seasonal-ET and literal-EST source instants are preserved. Require the same second-later-session09:30 open under all interpretations, strictly later than all source instants and within scope. Invalid source chronology, calendar coverage, timing non-invariance or contradictory public evidence stays unavailable. Modeling never populates an observed public timestamp. Exact public availability is **UNKNOWN**; historical bytes are present-day reconstruction with possible version drift.

The reference calendar spans {p['calendar_scope'][0]}–{p['calendar_scope'][1]}; only elapsed buffer dates are used, and buffered opens after policy end are unavailable. Weekends/full-day holidays, Carter closure, DST and near-midnight cases are tested. Complete per-security/class/exchange and execution-close calendars remain unresolved. The bounded30-issuer census has249 invariant records and1 Salesforce chronology failure; all failures/contributing states remain unavailable. This does not certify a full US population or amendment exhaustiveness. A larger eventual population requires its own complete contributor check.

Conditional Stage C proposal: source warm-up {g['filing_warmup_start']}; required price warm-up {g['price_warmup_start']} (not acquired); Development2020-03-02–2021-12-31; single owner-held historical confirmation2022-01-01–2026-09-30. Candidate-formation cutoff2021-12-31; design metadata cutoff2026-09-30. No future full2026 or2027+ session is assumed. Existing Stage/Store controls are not relaxed; an owner-held confirmation adapter is required before an executable freeze.

Inference proposal: one formal primary positive net paired arithmetic-mean effect, one-sided alpha0.05; positive two-sided95 lower bound; estimated mean>=2annual percentage points; all double-cost/+1/+5-delay estimates positive. No separate stress significance is claimed. Source/year-sign/diagnostic conditions remain mandatory. Student group inference is conditionally calibrated on predeclared models; exact sign inference fails confidence resolution. The original and analytically corrected runs remain disclosed. C passes the corrected80% complete-support screen at+5points/2.5-point synthetic tracking error; real tracking error/power and annual-independence assumptions remain unknown. Review all stress failures and MDE sensitivity in the report; this is not an80% two-point-alpha guarantee.

Tradeoffs: only22 Development decisions, sparse/unqualified early source coverage, one historical replication, partial final year, prior historical knowledge, required stage adapter, all accounting/class/terminal source gates still blocked, and a known source chronology conflict. Source certification may invalidate the proposed inception. None is concealed by the recommendation.

**Exact decision requested:** approve or reject this separately versioned modeled policy scope/definition and the conditional Stage C/hierarchy/materiality proposal for subsequent planning. Accept the stated modeled timing uncertainty while observed publication remains UNKNOWN. Preserve v002 unchanged. Approval supplies no automatic eligibility activation, source acquisition/certification campaign, experiment registration/freeze, real inference certificate, performance or Phase4A authorization. A separate instruction is required for subsequent bounded work. Defer is an available choice.
''',
 'phase3e_redesign_gate_review.md':'# Phase 3E-R gate review\n\n'+gate_table+'\n\nConditional stage review readiness is distinct from an executable source/inference/experiment certificate. No real eligibility or stage is opened.\n'}
    outputs={'phase3e_power_mde_v003.json':power,'phase3e_stage_recommendation.json':recommendation,
             'phase3e_metadata_representation_review.json':representations,
             'phase3e_redesign_source_coverage.json':coverage,'phase3e_redesign_source_registry.json':ledger,'phase3e_redesign_summary.json':summary}
    rendered={n:json.dumps(value,sort_keys=True,indent=2)+'\n' for n,value in outputs.items()};rendered.update(texts)
    for name,content in rendered.items():
        if name.endswith('.md'):
            clarification='The proposed group-reference/calibration contract explicitly replaces the old six annual-equivalent, three/window and HAC-effective-size prerequisites. This is a pre-performance inference proposal; old artifacts and real stage gates are unchanged. Power covers conditional confirmation statistical/materiality/stress-mean support only. It excludes Development advancement, year-sign/contributor-concentration checks and all source/execution gates; it is not the probability that EXP005 advances. An inconclusive result cannot establish absence of a true two-point effect.'
            if name=='phase3e_redesign_report.md':content=content.replace('## Gates and stop',clarification+'\n\n## Gates and stop')
            if name=='availability_policy_v003_review_packet.md':content=content.replace('Tradeoffs:',clarification+'\n\nTradeoffs:')
            if name in ('phase3e_redesign_report.md','availability_policy_v003_review_packet.md'):
                note='Raw metadata ISO strings are also preserved. [Independent literal-ISO sensitivity](phase3e_metadata_representation_review.json) gives the same buffered open for all 249 base-invariant records; the Salesforce conflict remains unavailable. This counterfactual does not certify that the publisher\'s trailing Z is an observed UTC timestamp or repair the source chronology.\n\n'
                anchor='**Stop for owner review' if name=='phase3e_redesign_report.md' else '**Exact decision requested:**'
                content=content.replace(anchor,note+anchor)
            content=re.sub(r'\b(All|As of|only|through|before|after|for|from|at|ends|including|scope|policy|seed|alpha|Development|Validation|Test|Phase|sided)(?=\d)',r'\1 ',content)
            content=re.sub(r'(?<=\d)(points|point|annual|sessions|months|years|replication|replications|realizations|requests|operations|headers)\b',r' \1',content)
            content=content.replace('future2026','future 2026').replace('cutoff2026','cutoff 2026').replace('cutoff2021','cutoff 2021').replace('date2026','date 2026').replace('Dataset30','Dataset 30').replace('bounded30','bounded 30').replace('Existing89','Existing 89')
            content=content.replace('at`','at `').replace('true2','true 2').replace('default2.5','default 2.5').replace('reach80%','reach 80%').replace('has80%','has 80%').replace('an80%','an 80%').replace('corrected80%','corrected 80%')
            content=content.replace('two-sided 95','two-sided 95%').replace('two-sided95','two-sided 95%').replace('Minimum95','Minimum 95%').replace('expected95','expected 95%').replace('MDE80','MDE at 80% power')
            for before,after in [('end2026','end 2026'),('endpoints2018','endpoints 2018'),('SEC161','SEC 161'),('Documentation4','Documentation 4'),('all200','all 200'),('adds10','adds 10'),('remain0','remain 0'),('remain unavailable','remain unavailable'),('confirmation2022','confirmation 2022'),('Partial2020','Partial 2020'),('the253','the 253'),('be2021','be 2021'),('reach30','reach 30'),('production100','production 100'),('above2','above 2'),('least4/5','least 4/5'),('becomes1','becomes 1'),('Both600','Both 600'),(';86400','; 86400'),('95 coverage','95% coverage'),('at+2','at +2'),('predeclared+5','predeclared +5'),('has249','has 249'),('and1 ','and 1 '),('screen at+5','screen at +5')]:
                content=content.replace(before,after)
        path=DOCS/name
        if check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content:raise ValueError('Redesign report changed: '+name)
        else:path.write_text(content,encoding='utf-8',newline='\n')
    return len(rendered)
