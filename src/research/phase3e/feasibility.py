"""Date/source feasibility decisions; no signals, prices, returns or transport."""
from datetime import date, timedelta
import json
from pathlib import Path
from src.research.phase3d.approval import approved_pilot
from src.research.phase3d.proof import file_hash

ROOT=Path(__file__).resolve().parents[3]
DOCS=ROOT/'docs/acceleration'


def interval(value):
    if len(value)!=2:raise ValueError('Exactly two date endpoints required')
    start,end=map(date.fromisoformat,value)
    if start>end:raise ValueError('Reversed date interval')
    return start,end


def horizon_gate(policy_scope, windows):
    """Coverage is necessary, never sufficient for activation or research access."""
    lower,upper=interval(policy_scope)
    if set(windows)!={'development','validation','test'}:raise ValueError('Three distinct stages required')
    rows=[];previous=None
    for stage in ('development','validation','test'):
        start,end=interval(windows[stage])
        if previous is not None and start<=previous:raise ValueError('Overlapping research stages')
        previous=end;intersection_start=max(start,lower);intersection_end=min(end,upper)
        covered=max(0,(intersection_end-intersection_start).days+1)
        total=(end-start).days+1
        rows.append({'stage':stage,'requested':windows[stage],'calendar_days':total,
                     'policy_covered_calendar_days':covered,'uncovered_calendar_days':total-covered,
                     'policy_covers_complete_stage':lower<=start<=end<=upper})
    fits=all(r['policy_covers_complete_stage'] for r in rows)
    return {'status':'COVERED_NOT_AUTHORIZED' if fits else 'INCOMPATIBLE_POLICY_SCOPE',
            'policy_scope':policy_scope,'stages':rows,'complete_stages_covered':sum(r['policy_covers_complete_stage'] for r in rows),
            'research_authorized':False,'policy_extension_approved':False}


def contributor_bounds(chains,timing):
    """Only previously published clock metadata; no financial values or signal."""
    index={r['accession']:r for r in timing}
    if len(index)!=len(timing):raise ValueError('Ambiguous accession timing')
    rows=[]
    for chain in chains:
        accessions=chain['filing_accessions'];bounds=[];reason=None
        if len(accessions)!=3:reason='MISSING_THIRD_ORIGINAL'
        else:
            for accession in accessions:
                r=index.get(accession)
                candidate=r.get('candidate_bounds_utc',[]) if r else []
                if not r or r['status']!='INVARIANT' or len(set(candidate))!=1:
                    reason='CLOCK_OR_CALENDAR_UNRESOLVED';break
                bounds.append(candidate[0])
        rows.append({'case_key':chain['case_key'],'originals':len(accessions),'accessions':accessions,
                     'mechanical_all_contributor_bound_utc':max(bounds) if not reason else None,
                     'status':reason or 'MECHANICAL_BOUND_ONLY','source_triple_certified':False,'trading_eligible':False})
    if len(rows)!=30 or len({r['case_key'] for r in rows})!=30:raise ValueError('Fixed revenue denominator changed')
    return rows


def evidence():
    approval=approved_pilot(DOCS)
    prior=json.loads((DOCS/'phase3c_evidence.json').read_bytes())
    requirements=json.loads((DOCS/'phase3b_source_requirements.json').read_bytes())
    windows={k:requirements['conditional_windows'][k] for k in ('development','validation','test')}
    gate=horizon_gate(approval['scope'],windows)
    bounds=contributor_bounds(prior['chains'],prior['timing'])
    accounting=json.loads((DOCS/'phase3d_accounting_review.json').read_bytes())
    identity=json.loads((DOCS/'phase3d_identity_closure.json').read_bytes())
    terminal=json.loads((DOCS/'phase3d_terminal_closure.json').read_bytes())
    calibration=json.loads((DOCS/'phase3d_inference_calibration_v002.json').read_bytes())
    names=['phase3b_design.md','phase3b_source_requirements.json','phase3b_trial_budget.md',
           'phase3c_evidence.json','phase3d_accounting_review.json','phase3d_identity_closure.json',
           'phase3d_terminal_closure.json','phase3d_inference_calibration_v002.json','availability_policy_v002_approved.json',
           'owner_phase3e_2026-10-12.md','phase3e_plan.md']
    return {'version':'phase3e_feasibility_v001','baseline':'081dfe638f1acb8e580a70de2c991bc83dfed5c1',
            'inputs':{name:file_hash(DOCS/name) for name in names},'horizon':gate,'contributors':bounds,
            'stop_condition':'Owner request section37: availability-policy scope incompatible with required historical design',
            'feasibility_verdict':'REDESIGN_REQUIRED' if gate['status']=='INCOMPATIBLE_POLICY_SCOPE' else 'UNRESOLVED_NOT_A_CERTIFICATE',
            'execution_disposition':'STOPPED_AT_PRE_ACQUISITION_SCOPE_GATE',
            'prior_revenue':{'originals':accounting['originals'],'issuers':30,'triples':29,'certified_triples':accounting['full_certified_triples'],
                             'partially_reviewed_not_certified':29,'new_reviews':0},
            'prior_identity':{'cases':60,'certified_full_spans':identity['certified_full_spans'],'status_counts':identity['status_counts'],'new_reviews':0},
            'prior_terminal':{'cases':60,'completion_document_sets':terminal['completion_document_denominator'],
                              'certified_position_cases':terminal['certified_position_terminal_cases'],'complete_nav_paths':terminal['complete_nav_paths'],'new_reviews':0},
            'inference':{'v003_protocol':'NOT_FROZEN','v003_calibration':'NOT_RUN_UPSTREAM_STOP','new_replications':0,
                         'prior_v002_candidate_verdicts':calibration['candidate_verdicts'],'prior_v002_selected_method':calibration['selected_method'],
                         'real_power':'UNKNOWN','v003_detectable_effect':'NOT_ESTIMATED','hypothesis_change_adopted':False},
            'policy':{'status':'OWNER_APPROVED_PILOT_NOT_ACTIVATED','hash':approval['policy_sha256'],'scope':approval['scope'],
                      'public_available_at_utc':None,'real_views_activated':0,'reapproval_requested':False},
            'real_signals_or_returns_computed':False,'EXP004':'PAUSED','EXP005':'ABSENT','Phase4A':'NOT_STARTED'}
