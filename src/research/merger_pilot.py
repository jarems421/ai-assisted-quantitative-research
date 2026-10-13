"""Source-only merger risk-set gates; shared immutable transport, no price path."""
import argparse
import hashlib
import json
from pathlib import Path
from src.research.procurement_pilot import PilotHTTP,contract as shared_contract,MONTHS
from src.research.fda_pilot import Text,missing_record
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import ROOT,now
from src.research.spec import canonical,digest

DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/merger_pilot_v001'
PAGES=[
 ('M01','https://www.ftc.gov/legal-library/browse/cases-proceedings','FTC case/action enumeration, source selection and original/update-date distinction'),
 ('M02','https://www.ftc.gov/enforcement/premerger-notification-program','Public HSR scope: transaction granularity, confidentiality and aggregate statistics'),
 ('M03','https://www.justice.gov/atr/antitrust-case-filings','DOJ action/case types and enforcement-positive versus closure/non-action scope'),
 ('M04','https://www.sec.gov/about/developer-resources','EDGAR public index/archive route for deterministic pre-outcome filing enumeration'),
 ('M05','https://www.sec.gov/files/form8-k.pdf','Transaction agreement/announcement disclosure requirements and limits')]
PASS_REQUIREMENTS=('pre_outcome_eligibility','challenged_and_unchallenged_retained','announcement_date_evidence',
 'separate_action_chronology','no_completion_or_enforcement_selection','failed_unresolved_retained','public_noncommercial_route')


def contract():
    return {'version':'merger_frame_audit_v001','gate':1,'owner_authority':'MERGER_ENFORCEMENT_FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY',
     'candidate_number':3,'candidate_ceiling':3,'historical_frame_period':['2019-01-01','2020-11-30'],
     'documentation_observation_date':'2026-10-13','official_documentation':[{'id':i,'url':u,'question':q} for i,u,q in PAGES],
     'request_ceiling':12,'total_pilot_ceiling':72,'pacing':{'workers':1,'global_minimum_seconds':0.6},
     'retry':shared_contract()['retry'],'conditional_gate2_slots':MONTHS,'gate1_event_selection':False,
     'gate2_selection':'FIRST_ELIGIBLE_PENDING_MERGER_FROM_PRE_OUTCOME_FRAME_NOT_FIRST_ENFORCEMENT_ACTION',
     'gate2_requires':list(PASS_REQUIREMENTS)+['review_receipt_sha256','separate_exact_event_manifest_frozen_before_dispatch'],
     'filters':{},'month_substitution':False,'transaction_contract':'NOT_ADOPTED_GATE1_ONLY',
     'questions':['agency_source_scope','action_types','nonaction_coverage','pre_outcome_observability','SEC_pending_risk_set',
      'HSR_transaction_granularity','announcement_action_terminal_dates','case_update_vs_first_public','untreated_denominator','bounded_noncommercial_route'],
     'status_taxonomy':['PRE_DECISION_RISK_SET_PLAUSIBLE','TREATMENT_SELECTED_SOURCE_FRAME','HSR_TRANSACTION_FRAME_UNAVAILABLE',
      'SEC_RISK_SET_ROUTE_PLAUSIBLE','SOURCE_ACCESS_BLOCKED','SOURCE_ROUTE_UNAVAILABLE','REDIRECT_BOUNDARY_STOP',
      'DENOMINATOR_UNCERTIFIED','UNKNOWN','UNAVAILABLE','NOT_APPLICABLE','DATE_ONLY','GATE2_NOT_RUN'],
     'archive':'Shared PilotHTTP and Archive; immutable original success/error bodies; reserve before transport; no overwrite',
     'stop':['Access denial','Redirect/transport uncertainty','Uncertified pre-decision frame','Paid/evasive route','12 Gate1 starts','72 total starts','Performance inputs'],
     'forbidden':['FDA reopening','procurement reopening','commercial M&A sources','current-survivor filtering','completed-only sampling',
      'challenged-only sampling','prices','merger spreads','returns','signals','control selection','experiment registration','EXP006',
      'graph','causal claim','Nexus','Aurora','Phase4B/4C','paper/live','candidate4'],
     'performance_authorized':False,'timing_policy_approved':False,'redirect_following':False,'automatic_next_family':False}


def validate(m):
    if canonical(m)!=canonical(contract()):raise ValueError('Merger frame scope/filter/route/ceiling changed')
    return digest(m)


def frozen():
    m=json.loads((DOCS/'phase4a_merger_frame_manifest.json').read_bytes())
    receipt=json.loads((DOCS/'phase4a_merger_frame_freeze.json').read_bytes())
    if validate(m)!=receipt['manifest_sha256']:raise ValueError('Merger freeze mismatch')
    return m


class FrameHTTP(PilotHTTP):
    def __init__(self,m,*,root=RAW,**kwargs):
        validate(m);super().__init__(shared_contract(),root=root,**kwargs)
        self.m=m;self.allowed={p['url'] for p in m['official_documentation']}
    # Shared default reviewed_stop_allows remains False: no automatic resumption.


def frame_gate(evidence):
    if evidence.get('access_blocked'):return 'SOURCE_ACCESS_BLOCKED'
    if all(evidence.get(k) is True for k in PASS_REQUIREMENTS):return 'PRE_DECISION_RISK_SET_PLAUSIBLE'
    if evidence.get('enforcement_selected') is True and evidence.get('alternative_risk_set') is False:return 'TREATMENT_SELECTED_SOURCE_FRAME'
    return 'DENOMINATOR_UNCERTIFIED'


def gate2_authority(evidence,*,total_starts,event_manifest_frozen):
    if (frame_gate(evidence)!='PRE_DECISION_RISK_SET_PLAUSIBLE' or not evidence.get('review_receipt_sha256')
        or not event_manifest_frozen or total_starts<0 or total_starts>=72):raise ValueError('Gate2 prerequisites unresolved or ceiling reached')
    return 'SOURCE_ONLY_NO_PERFORMANCE'


def party_record(deal_id):
    return {'deal_id':deal_id,'target':{'issuer':None,'security':None,'status':'UNKNOWN'},
     'acquirer':{'issuer':None,'security':None,'status':'UNKNOWN'},
     'consideration':None,'lifecycle_status':'UNAVAILABLE','observed_public_at':None,'timing_policy_approved':False}


def screen_state(verdict):
    if verdict not in ('MERGER_FAMILY_ADVANCE','MERGER_FAMILY_REDESIGN','MERGER_FAMILY_REJECT'):raise ValueError('Unreviewed verdict')
    return {'candidate_count':3,'candidate_ceiling':3,'automatic_next_family':False,
     'family_screen':'THREE_PREDECLARED_FAMILIES_EXHAUSTED' if verdict=='MERGER_FAMILY_REJECT' else 'THREE_PREDECLARED_FAMILY_PILOTS_COMPLETE_OWNER_REVIEW',
     'next_experiment':'NONE_SELECTED' if verdict=='MERGER_FAMILY_REJECT' else 'NOT_YET_FROZEN',
     'performance_authorized':False,'Phase4B_4C_authorized':False}


def acquire():
    m=frozen();http=FrameHTTP(m);saved=RAW/'gate1_acquisition.json'
    if saved.exists():return json.loads(saved.read_bytes())
    rows=[];stop='DOCUMENTATION_ACQUIRED_REVIEW_REQUIRED'
    for page in m['official_documentation']:
        try:receipt,body=http.fetch(page['url'],purpose='MERGER_GATE1_DOCUMENTATION_'+page['id'])
        except ValueError:stop='REDIRECT_OR_TRANSPORT_BOUNDARY_STOP';break
        rows.append({'id':page['id'],'receipt':receipt})
        if receipt['status']!=200:
            stop='SOURCE_ACCESS_BLOCKED' if receipt['status'] in (403,429) else 'SOURCE_ROUTE_UNAVAILABLE';break
    result={'manifest_sha256':digest(m),'sources':rows,'requests':len(http.starts()),'acquisition_stop':stop,
     'scientific_review':'REQUIRED_NOT_AUTOMATICALLY_PASSED','gate2_ran':False,'event_manifest_created':False,
     'performance_inputs':0,'retrieval_finished_at_utc':now()}
    put(saved,result);return result


def report(check=False):
    m=frozen();http=FrameHTTP(m);result=RAW/'gate1_acquisition.json'
    review=json.loads((DOCS/'phase4a_merger_frame_review.json').read_bytes())
    if review['acquisition_sha256']!=hashlib.sha256(result.read_bytes()).hexdigest() or review['manifest_sha256']!=digest(m):raise ValueError('Review/acquisition lineage changed')
    receipts=sorted([json.loads(p.read_bytes()) for p in (RAW/'receipts').glob('*.json')],key=lambda r:r['request_started_at_utc'])
    for r in receipts:http.archive.read(r['body'])
    if len(http.starts())>12 or len(http.starts())>72:raise ValueError('Request ceiling exceeded')
    state=screen_state(review['family_verdict'])
    summary={'date':'2026-10-13','manifest_sha256':digest(m),'gate1':review['gate1'],'pre_decision_risk_set_verdict':review['source_frame_verdict'],
     'family_verdict':review['family_verdict'],'source_requests':len(http.starts()),'response_count':len(receipts),
     'retries':sum(json.loads(p.read_bytes())['attempt']>1 for p in http.starts()),'gate2_ran':False,'event_manifest_created':False,
     'conditional_slots':12,'slots_instantiated':False,'selected_deals':0,'risk_set_deals':None,'effective_independent_N':None,
     'HSR':review['HSR'],'SEC_risk_set':review['SEC_risk_set'],'EXP004':'PAUSED','EXP005':'ABANDONED_ABSENT',**state}
    registry={'gate1_ceiling':12,'total_pilot_ceiling':72,'starts':len(http.starts()),'response_receipts':receipts,
     'unresponded_reservations':len(http.starts())-len(receipts),'counts':{'FTC':sum('ftc.gov/' in r['url'] for r in receipts),
      'DOJ':sum('justice.gov/' in r['url'] for r in receipts),'SEC':sum('sec.gov/' in r['url'] for r in receipts),'OpenFIGI':0,
      'prices':0,'FDA':0,'procurement':0,'Nexus':0,'Aurora':0,'source_browser_search':0},
     'cost':'No purchase/upgrade; account-wide usage/debit unknown','archive':'All original success/error bytes ignored; headers exclude personal contact/auth values'}
    vpath=DOCS/'phase4a_merger_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    rows='| Official route | Status |\n| --- | --- |\n'
    for page in m['official_documentation']:
        found=[r for r in receipts if r['url']==page['url']]
        rows+='| '+page['id']+' — '+page['url']+' | '+(', '.join(str(r['status']) for r in found) if found else 'UNVISITED_AFTER_STOP')+' |\n'
    questions='| Gate 1 question | Finding |\n| --- | --- |\n'+'\n'.join('| '+k+' | '+value+' |' for k,value in review['questions'].items())
    md=f'''# Merger enforcement: pre-decision source-frame pilot

**{review['family_verdict']}. Gate 1 {review['gate1']}; {review['source_frame_verdict']}.** As of 2026-10-13. Candidate 3/3 closed within its source-only scope. Frozen manifest SHA-256 `{digest(m)}`. The [owner instruction](owner_merger_pilot_2026-10-13.md) requires a pre-decision pending-merger frame before individual cases. No event, deal, price, strategy or experiment was selected.

## Source evidence and denominator

{rows}
{review['narrative']}

The [source registry](phase4a_merger_source_registry.json) preserves request/retrieval times, statuses, content metadata, source hashes and lengths. Original bodies, errors and persisted stop stay ignored and immutable. The collector reuses PilotHTTP and Archive, including the existing default closed reviewed-stop hook; no parallel transport was built. No silent redirects, proxy, host rotation, mirror or denial retry occurred. Present-day reconstruction is not contemporaneous ingestion or proof of historical public availability.

{questions}

HSR transaction-level availability: **{review['HSR']}**. SEC pre-outcome risk-set feasibility: **{review['SEC_risk_set']}**. Unvisited documents are not evidence that HSR is confidential, that SEC is unsuitable, that all agency routes are inaccessible, or that only challenged deals exist. Aggregate HSR counts would not establish individual transactions even if later acquired. A filing-defined SEC census would require a deterministic transaction contract and historical index/announcement/duplicate/version review; none is adopted here. The scientific verdict is limited to this audited source route/frame.

## Downstream work not run

Gate 2 did not run. Its twelve months remain conditional, not twelve observed no-deal months. No event manifest, eligible transaction contract, enforcement chronology, target/acquirer bridge, consideration/terminal certificate, timing classification or cluster geometry was created. Risk-set deal count and effective independent count remain unavailable, not zero. Selected deals are zero because selection never ran. No acquired target was dropped or replaced with a current parent; no deal was selected at all.

Controls remain conceptual. Other pending mergers need an ex-ante observable risk set; contemporaneously unchallenged deals must not be selected by eventual non-challenge/completion; merger-arbitrage peers face industry, size, consideration, regulatory exposure and common merger-spread conditions; acquirer/target contrasts share the deal shock; later-challenged deals can contaminate comparisons and share agency/policy regimes. No control or causal estimand is adopted. Generic stocks and completed-only comparisons do not repair a missing pre-decision denominator.

Anticipation is not empirically assessed: announcements, regulatory-risk disclosures, HSR/Second Requests when genuinely public, agency statements, extended closing dates and amended agreements would need separately scoped chronology. A public challenge cannot automatically be called a clean surprise. Repeat acquirers, shared policy/industry/calendar shocks and multiple actions per deal remain dependence concerns, not measured clusters. Cash, stock, mixed/election/fractional/CVR and ended-target paths remain lifecycle requirements; no honest NAV certificate is claimed. Action, complaint, press-release, page-update and first-public dates remain distinct. No intraday timestamp was manufactured and filing policies v002/v003 were not reused.

## Verification and programme stop

{len(http.starts())} starts including retries; Gate 1 ceiling12, conditional total72. No source purchase; account-wide debit unknown. Git/CI metadata checks are delivery operations recorded separately. Validation: {v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, zero skipped. [Validation receipt](phase4a_merger_validation.json). `python -m src.research.merger_pilot report --check` reconciles archived bytes and tracked output without network; `acquire --execute` is a separate authorized mutation and never routine reproduction.

Procurement remains PROCUREMENT_FAMILY_REJECT; FDA remains FDA_FAMILY_REJECT. Their reports/bytes, Phase 3, frozen experiments, inactive policies, EXP004 pause and EXP005 absence/abandonment are unchanged. No EXP006, market data, returns, merger spreads, signal, ranking, portfolio, held-out opening, Nexus/Aurora, graph, causal lab, Phase 4B/4C or paper/live action occurred.

**{state['family_screen']}; NEXT_EXPERIMENT = {state['next_experiment']}.** See the [three-family synthesis](phase4a_family_screen_summary.md). Stop for higher-level architecture/research-direction reassessment. No candidate4, larger acquisition or automatic Phase 4B/4C begins.
'''
    outputs={'phase4a_merger_source_registry.json':registry,'phase4a_merger_pilot_summary.json':summary,'phase4a_merger_pilot_report.md':md}
    if review['family_verdict']=='MERGER_FAMILY_REJECT':outputs.update(synthesis(summary))
    for name,value in outputs.items():
        text=json.dumps(value,sort_keys=True,indent=2)+'\n' if not isinstance(value,str) else value;p=DOCS/name
        if check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:raise ValueError('Merger output mismatch: '+name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    return summary


def synthesis(merger):
    proc=json.loads((DOCS/'phase4a_procurement_pilot_summary.json').read_bytes())
    fda=json.loads((DOCS/'phase4a_fda_pilot_summary.json').read_bytes())
    obj={'date':'2026-10-13',**screen_state('MERGER_FAMILY_REJECT'),'families':[
     {'family':'procurement','verdict':proc['verdict'],'starts':proc['requests'],'failure':'Frozen publication channel403; independent transaction documentation not announcement substitute','not_tested':'Award/action/recipient/timing/controls/geometry'},
     {'family':'FDA','verdict':fda['family_verdict'],'starts':fda['total_requests'],'failure':'Approval-oriented sources; no certified complete denominator; exact negative-document route404','not_tested':'Event census, rights/security, timing, clusters, controls'},
     {'family':'merger','verdict':merger['family_verdict'],'starts':merger['source_requests'],'failure':merger['pre_decision_risk_set_verdict'],'not_tested':'Pre-decision population, HSR/SEC alternatives, deals/parties/lifecycle/timing/geometry/controls'}],
     'finding_scope':'Three bounded frames failed; no economic hypothesis was tested and no event-driven research impossibility established',
     'source_problem':'Accessible primary routes and outcome-independent denominators were not established in bounded audits',
     'hypothesis_problem':'UNTESTED: no prices/returns; failure is not evidence that mechanisms lack alpha',
     'system_design_problem':'Early source gates worked; route verification before scoring is a supported engineering lesson. Identity/terminal/control burdens remain mostly prospective, not three empirically established failures.',
     'next_owner_decision':'Choose higher-level hypothesis-generation/source-population architecture reassessment scope; no fourth family or Phase4B/4C automatic authorization'}
    table='| Family | Bounded failure | Work never tested | Starts |\n| --- | --- | --- | ---: |\n'+'\n'.join('| '+r['family']+' | '+r['failure']+' | '+r['not_tested']+' | '+str(r['starts'])+' |' for r in obj['families'])
    md=f'''# Phase 4A: three-family screen synthesis

**THREE_PREDECLARED_FAMILIES_EXHAUSTED; NEXT_EXPERIMENT = NONE_SELECTED.** As of 2026-10-13. No performance authorized. These are three rejected bounded source frames, not economic falsification or proof that event-driven research cannot work.

{table}

See the [procurement](phase4a_procurement_pilot_report.md), [FDA](phase4a_fda_pilot_report.md) and [merger](phase4a_merger_pilot_report.md) reports. Their failed/deferred denominators remain explicit. Unvisited alternatives are unknown, not observed missing populations. No family obtained a trading-ready timing, identity, execution or inference certificate.

Source problem: ordinary publication access and complete pre-outcome denominator evidence were unresolved. Hypothesis problem: untested; no market returns or economic effect were measured. System-design problem: the bounded early gates prevented unsupported experiments. Freeze and prove an accessible exact route before mechanism scores drive acquisition is a justified engineering recommendation, not authorization to implement another campaign. The pilots do not show that identity/terminal defects caused all three stops; those remain downstream risks mostly never tested.

Owner reassessment should decide:

1. Should generic population/source infrastructure precede another hypothesis?
2. Should Phase 4B temporal corporate identity/event lineage move earlier, and what evidence warrants that cost when most mappings were never tested?
3. Should the next hypothesis begin from an already-accessible outcome-complete panel?
4. Should triage require exact source-access proof before mechanism scoring?
5. Are control/causal requirements stronger than needed for the intended predictive estimand? A predictive study still needs a non-hindsight population, though it need not claim causality.
6. Which requirements are reusable (archive, route proof, denominator/timing/identity/stop gates) and which are family-specific (FDA rights/negative actions; procurement award lineage; merger two-party terminal paths)?

These are review questions, not adopted answers or a fourth candidate. Preserve prior policies, reports, experiments, EXP004 pause and EXP005 abandonment/absence. No graph, causal lab, prices, experiment, paper/live or Phase 4B/4C is launched. **Stop for an explicit architecture/research-direction decision.**
'''
    return {'phase4a_family_screen_summary.json':obj,'phase4a_family_screen_summary.md':md}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('manifest','acquire','report'))
    parser.add_argument('--execute',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.command=='manifest':print('Merger manifest:',digest(frozen()))
    elif args.command=='acquire':
        if not args.execute:parser.error('Acquisition requires --execute')
        print('Merger acquisition:',acquire()['acquisition_stop'])
    else:print('Merger report:',report(args.check)['family_verdict'])
