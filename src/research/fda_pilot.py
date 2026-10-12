"""Gate 1 FDA frame audit using existing transport/archive; no event or price loader."""
import argparse,json,re
from html.parser import HTMLParser
from pathlib import Path
from src.research.procurement_pilot import PilotHTTP,contract as procurement_contract,MONTHS
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import ROOT,now
from src.research.spec import canonical,digest

DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/fda_pilot_v001'
PAGES=[
 ('F01','https://open.fda.gov/apis/drug/drugsfda/','Drugs@FDA source scope and transformed update behavior'),
 ('F02','https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files','Application/action/status/document schema and file revision behavior'),
 ('F03','https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process','Official application universe and historical coverage overview'),
 ('F04','https://www.fda.gov/drugs/drug-approvals-and-databases/complete-response-letters','Candidate official negative-decision documentation route; existence and scope not assumed'),
 ('F05','https://www.fda.gov/drugs/development-approval-process-drugs','Official review process and prospective application/decision/anticipation semantics')]


def contract():
    return {'version':'fda_frame_audit_v001','gate':1,'owner_authority':'FDA_FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY',
     'historical_frame_period':['2019-01-01','2020-11-30'],'documentation_observation_date':'2026-10-13',
     'request_ceiling':10,'total_pilot_ceiling':60,'FDA_documentation':[{'id':i,'url':u,'question':q} for i,u,q in PAGES],
     'pacing':{'workers':1,'global_minimum_seconds':0.6},
     'retry':{'maximum_attempts_per_request':3,'transient_statuses':[500,502,503,504],'backoff_seconds':[1,2],'no_retry_statuses':[403,429]},
     'gate2_requires':'Explicitly reviewed Gate1 PASS/outcome-independent denominator, negative/unresolved coverage and reconstruction evidence; then new exact event manifest before selection',
     'conditional_gate2_slots':MONTHS,'gate1_event_selection':False,'filters':{},'month_substitution':False,
     'questions':['source_universe','eventual_approval_conditioning','nonapproval_actions','observable_before_outcome','action_application_types',
                  'action_vs_update_date','original_documents','revision_reconstruction','denominator_completeness','unconditioned_comparisons'],
     'status_taxonomy':['FRAME_PASS','FRAME_UNCERTIFIED','OUTCOME_SELECTED_SOURCE_FRAME','SOURCE_ACCESS_BLOCKED',
                        'SOURCE_FRAME_AUDIT_INCOMPLETE_ACCESS_STOP','UNKNOWN','UNAVAILABLE','NOT_APPLICABLE','DATE_ONLY',
                        'PRIVATE_APPLICANT','RIGHTS_HOLDER_AMBIGUOUS','GATE2_NOT_AUTHORIZED'],
     'archive':'Existing Archive/immutable original bytes and canonical receipts; data/raw/fda_pilot_v001; reserve before transport; no overwrites',
     'stop':['Official source access denial','Uncertain transport/redirect','Approval-selected frame without authoritative alternative','10 Gate1 starts','60 total starts','Paid/evasive source','Performance information'],
     'forbidden':['Procurement retry','mirrors/proxies','commercial biotech databases','investor calendars','price data','returns','signals','ranking',
                  'causal claim','experiment registration','EXP006','graph','Phase4B/4C','paper/live'],
     'performance_authorized':False,'event_timing_policy_approved':False}


def validate(m):
    if canonical(m)!=canonical(contract()):raise ValueError('Frame scope/filters/ceilings/months changed')
    return digest(m)


def frozen():
    m=json.loads((DOCS/'phase4a_fda_frame_manifest.json').read_bytes());f=json.loads((DOCS/'phase4a_fda_frame_freeze.json').read_bytes())
    if validate(m)!=f['manifest_sha256']:raise ValueError('Frame freeze mismatch')
    return m


class FrameHTTP(PilotHTTP):
    """Scoped reuse of the unchanged procurement transport, not another collector."""
    def __init__(self,m,*,root=RAW,**kwargs):
        validate(m);super().__init__(procurement_contract(),root=root,**kwargs)
        self.m=m;self.allowed={p['url'] for p in m['FDA_documentation']}


def gate2_authority(frame,*,total_starts,event_manifest_frozen):
    if (frame.get('gate1')!='PASS' or frame.get('outcome_independent_frame') is not True
        or frame.get('negative_unresolved_coverage') is not True or not frame.get('review_receipt_sha256')
        or not event_manifest_frozen or total_starts>=60):raise ValueError('Gate2 prerequisites or total ceiling unresolved')
    return 'CONDITIONAL_SOURCE_ONLY_NO_PERFORMANCE'


class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.hidden:self.hidden-=1
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)


def scope_findings(body,source_sha256):
    p=Text();p.feed(body.decode('utf-8'));text=' '.join(' '.join(p.parts).split())
    patterns={'approved_product_scope':r'Drugs@FDA includes most of the drug products approved since 1939',
              'approved_product_categories':r'FDA-approved products for human use',
              'current_updates':r'Daily\s*\(Monday-Friday\)|updated each morning, Monday through Friday',
              'derivative_transform':r'converts the data into JSON',
              'submission_status_field':r'SubmissionStatusDate','sponsor_field':r'SponsorName',
              'negative_document_reference':r'complete response letters?'}
    locators={}
    for key,pattern in patterns.items():
        matches=list(re.finditer(pattern,text,re.I))
        locators[key]=[{'normalized_start':m.start(),'normalized_end':m.end(),'span_sha256':digest(text[m.start():m.end()]),'source_sha256':source_sha256} for m in matches]
    return {'transform':'HTML_visible_text_whitespace_fda_v001','normalized_text_sha256':digest(text),'locators':locators,
            'locator_scope':'Decoded visible-text offsets; source original-byte hash retained. Located text does not certify denominator completeness.'}


def outcome_gate(*,approved_scope,alternative_complete,access_blocked):
    if access_blocked:return 'SOURCE_FRAME_AUDIT_INCOMPLETE_ACCESS_STOP'
    if approved_scope and alternative_complete is False:return 'OUTCOME_SELECTED_SOURCE_FRAME'
    return 'FRAME_UNCERTIFIED'


def missing_record(reason):
    if reason not in ('UNKNOWN','UNAVAILABLE','NOT_APPLICABLE'):raise ValueError('Missingness reason absent')
    return {'value':None,'status':reason}


def retain_identity(records):
    if len({r['id'] for r in records})!=len(records):raise ValueError('Repeated case key')
    return records  # Private and multiple rights holders are retained, never filtered.


def acquire():
    m=frozen();h=FrameHTTP(m);saved=RAW/'gate1_result.json'
    if saved.exists():return json.loads(saved.read_bytes())
    sources=[];blocked=False
    for page in m['FDA_documentation']:
        try:r,body=h.fetch(page['url'],purpose='FDA_GATE1_FRAME_DOCUMENTATION')
        except ValueError:
            blocked=True;break
        row={'id':page['id'],'question':page['question'],'receipt':r,'findings':scope_findings(body,r['body']['sha256']) if r['status']==200 else None}
        sources.append(row)
        if r['status'] in (403,429) or (RAW/'publication_stop.json').exists():blocked=True;break
    approved=any(s['findings'] and (s['findings']['locators']['approved_product_scope'] or s['findings']['locators']['approved_product_categories']) for s in sources)
    result={'version':'fda_gate1_source_audit_v001','manifest_sha256':digest(m),'sources':sources,'requests':len(h.starts()),
     'source_frame_verdict':outcome_gate(approved_scope=approved,alternative_complete=None,access_blocked=blocked),
     'approved_product_scope_located':approved,'alternative_outcome_complete_frame_certified':False,'gate1':'FAIL_CLOSED',
     'gate2_ran':False,'event_manifest_created':False,'event_slots_instantiated':False,
     'family_verdict':'FDA_FAMILY_REJECT','verdict_scope':'This bounded Gate1 source audit did not establish the required historical outcome-independent frame; not evidence that every FDA frame is impossible',
     'performance_inputs':0,'observed_public_time':None,'timing_policy_approved':False,'stopped_at_utc':now()}
    put(saved,result);return result


def report(check=False):
    m=frozen();r=json.loads((RAW/'gate1_result.json').read_bytes());h=FrameHTTP(m)
    receipts=[json.loads(p.read_bytes()) for p in sorted((RAW/'receipts').glob('*.json'))]
    for x in receipts:h.archive.read(x['body'])
    starts=len(h.starts())
    if starts>10 or starts>60:raise ValueError('Quota exceeded')
    registry={'gate1_ceiling':10,'total_pilot_ceiling':60,'starts':starts,'response_receipts':receipts,
              'unresponded_reserved_attempts':starts-len(receipts),'counts':{'FDA':starts,'SEC':0,'OpenFIGI':0,'price':0,'procurement':0,'Nexus':0,'Aurora':0,'browser':0},
              'cost':'No purchase/upgrade; account-wide debit unknown','archive':'Original bytes/error receipts ignored; contact/auth headers excluded'}
    sources=r['sources'];scope=any(s['findings'] and s['findings']['locators']['approved_product_scope'] for s in sources)
    questions={
      'Q1':'Official documentation accessible for '+str(sum(x['status']==200 for x in receipts))+' responses; historical corpus completeness not certified',
      'Q2':'Approved-product scope documented; full negative/unresolved application frame not certified' if scope else 'UNKNOWN: no outcome-complete frame certified',
      'Q3':'Original documentation bytes/hash replay supported; application/action corpus revision replay not tested',
      'Q4':'UNAVAILABLE: no event selected, observed public instant or modeled bound approved',
      'Q5':'NOT_TESTED: applicant-to-economic-rights relationship',
      'Q6':'NOT_TESTED: rights-holder-to-historical-security coverage',
      'Q7':'NOT_MEASURED: repeated applications/products/sponsors and same-day clusters',
      'Q8':'NOT_CERTIFIED: schedules/advisory committees/prior communication can anticipate final action; no anticipation corpus acquired',
      'Q9':'NOT_CERTIFIED: approval-oriented database is not an outcome-independent treatment/comparison denominator; peers do not automatically repair it',
      'Q10':'No expansion: Gate1 failed closed; do not run Gate2 or a larger event/design campaign'}
    frame_questions={
      'source_universe':'Approved-product scope located in original docs' if scope else 'UNKNOWN',
      'eventual_approval_conditioning':'Approval-oriented documented universe; individual application selection/history not audited' if scope else 'UNKNOWN',
      'nonapproval_actions':'UNKNOWN; nonapproval/unresolved completeness not established. Previous negative actions of eventually approved applications would not suffice.',
      'observable_before_outcome':'UNKNOWN; no authoritative complete pre-outcome application frame established',
      'action_application_types':'PARTIAL_DOC_ONLY' if any(s['findings'] and s['findings']['locators']['submission_status_field'] for s in sources) else 'UNKNOWN',
      'action_vs_update_date':'Current update/derivative behavior located where supported; no date made into first-public timestamp',
      'original_documents':'Our new response bytes retained; historical source version preservation UNKNOWN',
      'revision_reconstruction':'Current documentation/API transformation is not historical application/action version replay',
      'denominator_completeness':'NOT_CERTIFIED',
      'unconditioned_comparisons':'NOT_CERTIFIED; approval-only sampling and generic sector peers cannot establish an outcome-independent eligible denominator'}
    summary={'family_status':'FDA_FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY','family_verdict':r['family_verdict'],
             'source_frame_verdict':r['source_frame_verdict'],'gate1':'FAIL_CLOSED','gate2_ran':False,'event_manifest_created':False,
             'gate1_manifest_sha256':digest(m),'total_requests':starts,'selected_events':0,'usable_applications':None,
             'effective_sample_size':None,'public_timing':'UNAVAILABLE','identity':'NOT_TESTED','questions':questions,
             'verdict_scope':r['verdict_scope'],'date':'2026-10-13','Phase4A':'ACTIVE_EXPERIMENT_SELECTION',
             'next_experiment':'NOT_YET_FROZEN','performance_authorized':False,'EXP004':'PAUSED','EXP005':'ABANDONED_ABSENT',
             'timing_policy_approved':False,'merger_family_automatic_launch':False}
    outputs={'phase4a_fda_source_registry.json':registry,'phase4a_fda_frame_review.json':{'gate1_verdict':r['source_frame_verdict'],'questions':frame_questions,'source_findings':sources,
              'outcome_complete_certified':False,'access_stop_scope':'Unvisited sources are not observed approval-only or absent-negative sources','gate2_authorized':False},
             'phase4a_fda_pilot_summary.json':summary}
    validation=DOCS/'phase4a_fda_validation.json';v=json.loads(validation.read_bytes()) if validation.exists() else {}
    questions_md='| Question | Answer |\n| --- | --- |\n'+'\n'.join('| '+k+' | '+a+' |' for k,a in questions.items())
    status_md='| Official documentation route | HTTP response | Scope evidence |\n| --- | --- | --- |\n'+'\n'.join('| '+s['id']+' | '+str(s['receipt']['status'])+' | '+('Original bytes/locators retained' if s['findings'] else 'Unavailable, no scope inferred')+' |' for s in sources)
    md=f'''# FDA pilot: Gate 1 source-frame disposition

**{r['family_verdict']}. Gate1 = FAIL_CLOSED; {r['source_frame_verdict']}.** As of 2026-10-13. Frozen manifest SHA-256 `{digest(m)}`. The [owner instruction](owner_fda_pilot_2026-10-13.md) and [plan](phase4a_fda_pilot_plan.md) require the denominator gate before individual events. No event was selected, no Gate2 manifest was created and the 12 conditional monthly slots were not instantiated as observed cases.

{status_md}

Gate1 used {starts} starts of its maximum10, including retries; the total60 ceiling was not approached. Original responses and error bodies are archived with request/retrieval times, content metadata, hashes and lengths. The [registry](phase4a_fda_source_registry.json) identifies exact routes and statuses. The collector reuses procurement's unchanged PilotHTTP and Archive under a separate FDA root. Procurement's stopped route was not retried, and no proxy, mirror or redirect was used.

Where located, the official Drugs@FDA description enumerates approved products and describes current updates/transformation. That supports an approval-oriented scope finding, not a complete historical decision denominator. It does not prove the absence of all negative actions: earlier failures for subsequently approved applications may exist and still leave never-approved/unresolved applications unrepresented. Conversely a negative-letter archive would need its own coverage/selection audit before it could repair the frame.

If the source audit stopped on access, its negative-decision documentation routes remain **unreviewed**, not proven empty. We do not promote this incomplete audit to proof of irreparable approval selection or the impossibility of every official FDA frame. The verdict rejects expansion under this bounded source audit because the mandatory outcome-independent frame was not established. [Detailed ten-question frame audit](phase4a_fda_frame_review.json) retains source-hash/text-transformation locators and UNKNOWN fields.

## Required pilot questions

{questions_md}

No approval sample, application/action count, applicant mapping, rights-holder/security mapping, action type distribution, regulatory timestamp, cluster count or effective independent sample size is claimed. Those are Gate2 tasks, which did not run. Source absence is not zero eligible actions. No private applicant or ambiguous economic-rights case was screened out; no case was selected at all. No FDA timing bound, midnight/open/close conversion or SEC filing-policy reuse occurred.

Comparison frames remain conceptual: contemporaneous eligible applications require a complete risk set; scheduled-decision cohorts require original acceptance/scheduling evidence; therapeutic peers need observed histories and controls for therapy/calendar confounding; within-issuer contrasts still share anticipation and repeated-product/issuer shocks. None is selected or causal. Prospective schedules, advisory committee/prior communications and rights-holder relationships would require separate scoped evidence; this pilot built no anticipation dataset and estimated no market outcome.

## Validation and stop

Validation: {v.get('local_tests_passed','pending')} local tests; {v.get('public_tests_passed','pending')} public tests; {v.get('tests_skipped','pending')} skipped. [Validation](phase4a_fda_validation.json). Offline report/hash reconciliation: `python -m src.research.fda_pilot report --check`. `acquire --execute` is an explicitly authorized remote mutation, not routine reproduction; the cached completed result performs no resubmission.

Phase4A remains ACTIVE_EXPERIMENT_SELECTION; next experiment NOT_YET_FROZEN, performance false. Procurement, Phase3, EXP004 pause, EXP005 abandonment/absence, original scorecard/FDA/merger evidence and v002/v003 approvals remain unchanged. No prices, returns, event studies, signals, ranking, experiment, SEC/OpenFIGI work, graph, causal lab, Nexus/Aurora or paper/live operation occurred.

**Stopped at Gate1.** No larger FDA campaign or approval-only event sample is authorized. No owner decision is needed to retain this negative result. The remaining predeclared merger-enforcement family may receive one bounded pass only under a new explicit instruction. Do not launch it automatically; after the original three candidates, stop and reassess hypothesis generation instead of adding families indefinitely. No Phase4B/4C begins here.
'''
    for a,b in [('Gate1','Gate 1'),('Gate2','Gate 2'),('maximum10','maximum 10'),('total60','total 60'),('Phase4A','Phase 4A'),('Phase3','Phase 3'),('Phase4B/4C','Phase 4B/4C')]:md=md.replace(a,b)
    texts={k:json.dumps(obj,sort_keys=True,indent=2)+'\n' for k,obj in outputs.items()};texts['phase4a_fda_pilot_report.md']=md
    for name,text in texts.items():
        p=DOCS/name
        if check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:raise ValueError('FDA report mismatch: '+name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['manifest','acquire','report']);p.add_argument('--execute',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.command=='manifest':print('Frame manifest:',digest(frozen()))
    elif a.command=='acquire':
        if not a.execute:p.error('Acquisition requires --execute')
        print('FDA Gate1:',acquire()['source_frame_verdict'])
    else:print('FDA report:',report(a.check)['family_verdict'])
