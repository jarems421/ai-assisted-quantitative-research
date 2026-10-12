"""PIT metadata counts and immutable planning definitions, never financial signals."""
from collections import Counter
from datetime import date,datetime,timedelta
import json
from src.research.phase3d.proof import file_hash
from src.research.spec import digest
from .sources import DOCS,CUTOFF
from .calendar import sessions,clock_probe,open_utc,MAX_CALENDAR

CANDIDATES=[
 {'id':'A','description':'Longer Development, two funded historical confirmation windows',
  'development':['2020-03-02','2023-12-31'],'confirmation':[['2024-01-01','2024-12-31'],['2025-01-01',CUTOFF]],'confirmation_roles':['Validation','Owner-only Test']},
 {'id':'B','description':'Balanced Development with longer joint confirmation',
  'development':['2020-03-02','2022-12-31'],'confirmation':[['2023-01-01','2024-12-31'],['2025-01-01',CUTOFF]],'confirmation_roles':['Validation','Owner-only Test']},
 {'id':'C','description':'Short Development and one larger owner-held historical confirmation',
  'development':['2020-03-02','2021-12-31'],'confirmation':[['2022-01-01',CUTOFF]],'confirmation_roles':['Proposed owner-held confirmation; future stage adapter required']}]


def policy(source):
    old=json.loads((DOCS/'phase3c_evidence.json').read_bytes())['policy']
    first=min([r['filing_date'] for r in source['records']]+[datetime.strptime(r['acceptance_raw'],'%Y%m%d%H%M%S').date().isoformat()
               for r in source['records'] if r['acceptance_raw']])
    return {'version':'phase3er_ambiguity_buffer_v003','status':'PROPOSED_NOT_APPROVED','approval':None,'activation':'NOT_ACTIVATED',
            'scope':[first,CUTOFF],'rule':old['rule'],'clock_interpretations':['Seasonal Eastern Time','Literal UTC-05:00 EST'],
            'exact_public_availability':'UNKNOWN','source_manifest_sha256':file_hash(DOCS/'phase3e_redesign_source_metadata.json'),
            'calendar_code_sha256':file_hash(DOCS.parent.parent/'src/research/phase3er/calendar.py'),
            'calendar_evidence':[r['body_sha256'] for r in source['calendar_documents']],
            'v002_sha256':digest(old),'reason':'Warm-up source receipts plus historical stages beyond the approved2021 pilot; no broader date than necessary',
            'frame':'Fixed30 issuer metadata/header feasibility census; full production universe not certified',
            'calendar_scope':[first,'2026-10-09'],'calendar_role':'09:30 openings/full-day closures only; elapsed buffer dates beyond stage end never eligible within policy',
            'prerequisites':['Owner approval','Full accounting and effective class certification','Complete intended production-population contributor probe','Stage-safe adapter','No contradictory timing evidence'],
            'does_not_authorize':['Real eligibility activation','EXP005 creation/freeze/performance','EXP004 resume','Nexus/Aurora','heldout opening','Phase4A','paper/live']}


def invariance(source,p):
    authority=json.loads((DOCS/'phase3a_evidence.json').read_bytes())['acceptance_interpretations'][0]['evidence_sha256']
    records=[]
    for r in source['records']:
        result=clock_probe(r['acceptance_raw'],r['filing_date'],scope=p['scope'],evidence_sha256=authority)
        if not r['header_issuer_verified']:result.update(status='UNVERIFIED_HEADER_ISSUER',mechanical_bound_utc=None)
        records.append(dict(result,case_key=r['case_key'],accession=r['accession'],report_date=r['report_date'],
                            header_sha256=r['header_sha256'],policy_sha256=digest(p)))
    return {'version':'phase3er_clock_probe_v001','policy_sha256':digest(p),'denominator':len(records),
            'issuer_denominator':30,'status_counts':dict(Counter(r['status'] for r in records)),
            'records':records,'failed_rows':[r['accession'] for r in records if r['status']!='INVARIANT'],
            'certified_real_trading_eligible':0,'population_scope':'All selected annual originals in fixed30 frame; no full-market or amendment-exhaustiveness certificate'}


def triples(records):
    result=[]
    for case in sorted({r['case_key'] for r in records}):
        group=sorted((r for r in records if r['case_key']==case),key=lambda r:r['report_date'])
        for i in range(2,len(group)):
            chain=group[i-2:i+1]
            gaps=[(date.fromisoformat(b['report_date'])-date.fromisoformat(a['report_date'])).days for a,b in zip(chain,chain[1:])]
            valid=all(350<=gap<=380 for gap in gaps) and all(r['status']=='INVARIANT' for r in chain)
            result.append({'case_key':case,'accessions':[r['accession'] for r in chain],
                           'end_dates':[r['report_date'] for r in chain],'fiscal_end_gaps':gaps,
                           'latest_filing_date':chain[-1]['filing_date'],
                           'mechanical_bound_utc':max(r['mechanical_bound_utc'] for r in chain) if valid else None,
                           'mechanically_available':valid,'accounting_certified':False,'trading_eligible':False})
    return result


def window_geometry(bounds,states,all_records):
    start,end=map(date.fromisoformat,bounds)
    if start>end or end>date.fromisoformat(CUTOFF):raise ValueError('Future/reversed stage')
    days=sessions(start,end);by_month={}
    for d in days:by_month.setdefault(d.strftime('%Y-%m'),d)
    panel=[]
    for month,d in by_month.items():
        available=[r for r in states if r['mechanical_bound_utc'] and datetime.fromisoformat(r['mechanical_bound_utc'])<=open_utc(d)
                   and (d-date.fromisoformat(r['latest_filing_date'])).days<=400]
        panel.append({'month':month,'decision_date':d.isoformat(),'mechanically_available_issuers':len({r['case_key'] for r in available}),
                      'accounting_certified_issuers':0,'trading_eligible_issuers':0,'fixed_issuer_denominator':30})
    groups=[]
    for year in sorted({d.year for d in days}):
        portion=[d for d in days if d.year==year]
        groups.append({'year':year,'sessions':len(portion),'first':portion[0].isoformat(),'last':portion[-1].isoformat(),
                       'complete_calendar_year':start<=date(year,1,1) and end>=date(year,12,31)})
    source_events=sum(1 for r in states if r['mechanical_bound_utc'] and start<=datetime.fromisoformat(r['mechanical_bound_utc']).date()<=end)
    return {'bounds':bounds,'sessions':len(days),'monthly_decisions':len(panel),'annual_groups':groups,
            'complete_calendar_years':sum(r['complete_calendar_year'] for r in groups),'reporting_cycles_touched':len(groups),
            'mechanical_source_events_with_predecessors':source_events,'all_original_filing_events':sum(start<=date.fromisoformat(r['filing_date'])<=end for r in all_records),
            'possible_contributor_states':len(states),'monthly_panel':panel,'counts_are_independence_certificates':False,
            'identity_spans_certified':0,'terminal_paths_certified':0}


def build():
    source=json.loads((DOCS/'phase3e_redesign_source_metadata.json').read_bytes());p=policy(source);clock=invariance(source,p);states=triples(clock['records'])
    all_dates=sessions(date.fromisoformat(p['scope'][0]),MAX_CALENDAR)
    warmup=all_dates[all_dates.index(date(2020,3,2))-253].isoformat()
    rows=[]
    for c in CANDIDATES:
        dev=window_geometry(c['development'],states,clock['records']);confirmation=[window_geometry(w,states,clock['records']) for w in c['confirmation']]
        if date.fromisoformat(c['development'][1])>=date.fromisoformat(c['confirmation'][0][0]):raise ValueError('Stage overlap')
        rows.append(dict(c,development_geometry=dev,confirmation_geometry=confirmation,
                         confirmation_sessions=sum(w['sessions'] for w in confirmation),confirmation_year_groups=sum(len(w['annual_groups']) for w in confirmation),
                         independent_funding_windows=len(confirmation),price_warmup_start=warmup,
                         holdout_integrity='WORKFLOW_HELD_OUT_CANDIDATE_SPECIFIC_ONLY; prior market knowledge/cross-experiment exposure remains',
                         source_coverage='MECHANICAL_FRAME_ONLY; no certified universe/financial/price history',
                         stage_adapter='Existing three-stage gates for A/B; C requires separately reviewed owner-held confirmation mapping'))
    outputs={'availability_policy_v003_proposed.json':p,'phase3e_policy_v003_invariance.json':clock,
             'phase3e_stage_candidates.json':{'version':'phase3er_stage_candidates_v001','candidates':CANDIDATES,'performance_inputs':0},
             'phase3e_stage_geometry.json':{'version':'phase3er_geometry_v001','policy_sha256':digest(p),'candidates':rows,'contributor_states':states,'accounting_certified':0,'trading_eligible':0,
                 'filing_warmup_start':p['scope'][0],'price_warmup_start':warmup,'scope_end':CUTOFF}}
    return outputs


def generate(check=False):
    for name,value in build().items():
        content=json.dumps(value,sort_keys=True,indent=2)+'\n';path=DOCS/name
        if check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content:raise ValueError('Geometry/policy changed: '+name)
        else:path.write_text(content,encoding='utf-8',newline='\n')
    return 4
