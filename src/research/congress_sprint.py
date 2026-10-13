"""EXP007 source contracts and pre-performance guards. No outcome loader."""
from collections import defaultdict
from datetime import datetime,time,timezone
from zoneinfo import ZoneInfo
import json
from src.research.sec_pilot.provenance import instant
from src.research.spec import digest

NY=ZoneInfo('America/New_York')


def classify(trade):
    action=trade.get('action')
    if action=='purchase':kind='PURCHASE'
    elif action in ('sale','exchange'):return {'status':'EXCLUDED_NON_PURCHASE','reason':action}
    else:return {'status':'UNKNOWN_TRANSACTION','reason':action}
    code=trade.get('asset_type_code');label=(trade.get('asset_type_label') or '').lower()
    if code=='ST' or label=='stock':return {'status':'COMMON_EQUITY_CANDIDATE','action':kind,'provider_common_class_required':True}
    if code or label:return {'status':'EXCLUDED_OR_UNRESOLVED_ASSET','reason':{'code':code,'label':label}}
    return {'status':'UNKNOWN_ASSET_CLASS'}


def resolution(trade):
    printed=trade.get('printed_ticker');resolved=trade.get('resolved_ticker');status=trade.get('resolution_status')
    usable=status in ('printed','resolved') and bool(resolved)
    return {'printed_ticker':printed,'resolved_ticker':resolved,'resolution_status':status,
            'resolution_reason':trade.get('resolution_reason'),'printed_equals_resolved':bool(printed and resolved and printed==resolved),
            'status':'SOURCE_RESOLVED_CANDIDATE' if usable else 'UNRESOLVED_SECURITY'}


def eligible_open(event,sessions):
    first=instant(event['first_available_at']);version=instant(event['available_at']);bound=max(first,version)
    if first>version:raise ValueError('Contradictory availability chronology')
    civil=bound.astimezone(NY).date();later=[d for d in sessions if d>civil]
    if len(later)<2:raise ValueError('Calendar coverage unavailable')
    entry=datetime.combine(later[1],time(9,30),NY).astimezone(timezone.utc)
    if entry<=bound:raise ValueError('Entry does not follow modeled bound')
    end=instant(event['superseded_at']) if event.get('superseded_at') else None
    if end and entry>=end:return {'status':'SUPERSEDED_BEFORE_ENTRY','entry_utc':None}
    return {'status':'MODELED_CONSERVATIVE_DISCLOSURE_ELIGIBILITY','entry_utc':entry.isoformat(),
            'effective_bound_utc':bound.isoformat(),'anchor_New_York_date':civil.isoformat(),'exact_public_availability':'UNKNOWN'}


def consolidate(rows):
    groups=defaultdict(list)
    for r in rows:
        if not r.get('stable_security_id') or not r.get('entry_date'):raise ValueError('Identity/entry required before consolidation')
        groups[(r['stable_security_id'],r['entry_date'])].append(r)
    return [{'stable_security_id':key[0],'entry_date':key[1],'disclosures':len(part),
             'members':len({r['member_id'] for r in part if r.get('member_id')}),
             'lineage':[{'event_id':r['event_id'],'version':r['version']} for r in sorted(part,key=lambda r:(r['event_id'],r['version']))]}
            for key,part in sorted(groups.items())]


def stage_guard(decision,development,confirmation,*,outcome=False,pushed_freeze=False,all_gates=False):
    day=decision[:10]
    if confirmation[0]<=day<=confirmation[1]:raise ValueError('Owner-held confirmation inaccessible')
    if not development[0]<=day<=development[1]:raise ValueError('Outside frozen Development')
    if outcome and not (pushed_freeze and all_gates):raise ValueError('Outcomes require pushed scientific freeze')
    return True


def contributor_asof(event,trades):
    """Upstream contributor arrays can grow retrospectively; date each link."""
    bound=max(instant(event['first_available_at']),instant(event['available_at']));accepted=[];future=[];missing=[]
    lookup={(r['chamber'],r['doc_id'],r['row_index']):r for r in trades}
    for identifier in json.loads(event.get('contributor_row_ids') or '[]'):
        doc,_,row=identifier.rpartition(':');trade=lookup.get((event['chamber'],doc,int(row)))
        if not trade:missing.append(identifier)
        elif instant(trade['available_at'])>bound:future.append(identifier)
        else:accepted.append(identifier)
    return {'asof_contributors':accepted,'future_contributors_not_used':future,'unavailable_contributors':missing,
            'upstream_contributor_list_sha256':digest(event.get('contributor_row_ids'))}
