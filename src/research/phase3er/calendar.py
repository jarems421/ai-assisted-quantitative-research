"""Opening-only historical calendar; no Test data or price access."""
from datetime import date,timedelta,datetime,time,timezone
from zoneinfo import ZoneInfo
from src.nexus.process_exp001 import session_dates
from src.research.sec_pilot.certification import acceptance

NY=ZoneInfo('America/New_York');MAX_CALENDAR=date(2026,10,9);MAX_STAGE=date(2026,9,30)
EXTENSION_CLOSURES={date.fromisoformat(d) for d in (
 '2025-01-01','2025-01-09','2025-01-20','2025-02-17','2025-04-18','2025-05-26','2025-06-19','2025-07-04','2025-09-01','2025-11-27','2025-12-25',
 '2026-01-01','2026-01-19','2026-02-16','2026-04-03','2026-05-25','2026-06-19','2026-07-03','2026-09-07')}


def sessions(start,end):
    if not date(2018,1,1)<=start<=end<=MAX_CALENDAR:raise ValueError('Unsupported or future calendar')
    old=sorted(session_dates(start,min(end,date(2024,12,31)))) if start<=date(2024,12,31) else []
    first=max(start,date(2025,1,1))
    return old+[first+timedelta(days=i) for i in range(max(0,(end-first).days+1))
                if (first+timedelta(days=i)).weekday()<5 and first+timedelta(days=i) not in EXTENSION_CLOSURES]


def open_utc(day):return datetime.combine(day,time(9,30),NY).astimezone(timezone.utc)


def clock_probe(raw,filed,*,scope,evidence_sha256,contradictory_public_utc=None):
    """v002 ambiguity logic, fresh bounded calendar; never create an eligibility view."""
    candidates=[];bounds=[]
    try:
        start,end=map(date.fromisoformat,scope);f=date.fromisoformat(filed)
        if not date(2018,1,1)<=start<=end<=MAX_STAGE:raise ValueError('Unsupported policy scope')
        interpreted=acceptance(raw,evidence_sha256=evidence_sha256)
        candidates=[datetime.fromisoformat(interpreted[k]) for k in ('candidate_eastern_utc','candidate_literal_est_utc')]
        raw_date=datetime.strptime(raw,'%Y%m%d%H%M%S').date()
        civil=[raw_date]+[d.astimezone(NY).date() for d in candidates]
        if not all(start<=d<=f<=end for d in civil):raise ValueError('Source chronology or scope')
        calendar=sessions(start,MAX_CALENDAR);bounds=[]
        for d in civil:
            later=[s for s in calendar if s>max(d,f)]
            if len(later)<2:raise ValueError('Missing buffer sessions')
            bounds.append(open_utc(later[1]))
        invariant=len(set(bounds))==1 and all(bounds[0]>d for d in candidates)
        if contradictory_public_utc and datetime.fromisoformat(contradictory_public_utc)>bounds[0]:invariant=False
        in_scope=bounds[0].astimezone(NY).date()<=end
        return {'status':'INVARIANT' if invariant and in_scope else 'NON_INVARIANT' if not invariant else 'BOUND_OUTSIDE_SCOPE',
                'acceptance_raw':raw,'filing_date':filed,'candidate_instants_utc':[d.isoformat() for d in candidates],
                'candidate_bounds_utc':[d.isoformat() for d in bounds],
                'mechanical_bound_utc':bounds[0].isoformat() if invariant and in_scope else None,
                'acceptance_certification':interpreted['status'],'exact_public_availability':'UNKNOWN',
                'policy_approved':False,'trading_eligible':False}
    except (ValueError,TypeError) as error:
        return {'status':'UNAVAILABLE_CLOCK_CALENDAR_OR_SCOPE','acceptance_raw':raw,'filing_date':filed,
                'candidate_instants_utc':[d.isoformat() for d in candidates],'candidate_bounds_utc':[d.isoformat() for d in bounds],
                'failure_reason':str(error),'mechanical_bound_utc':None,'policy_approved':False,'trading_eligible':False,'exact_public_availability':'UNKNOWN'}
