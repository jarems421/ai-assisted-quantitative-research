"""Development SEC source population and identity guards; no outcome loader."""
from collections import defaultdict
from datetime import date, datetime
import re

KEY_FIELDS = ('CIK', 'accession', 'form', 'filing_date', 'source_path')


def key(row):
    return tuple(row[k] for k in KEY_FIELDS)


def parse_daily(body, observed_day, source_sha256):
    observed = date.fromisoformat(observed_day)
    if not date(2015, 1, 1) <= observed <= date(2020, 12, 31):
        raise ValueError('Daily source outside Development')
    text = body.decode('latin-1')
    if not any(h in text for h in ('CIK|Company Name|Form Type|Date Filed|Filename',
                                  'CIK|Company Name|Form Type|Date Filed|File Name')):
        raise ValueError('Daily master schema missing')
    rows=[];outside=0
    for line_number,line in enumerate(text.splitlines(),1):
        fields=line.split('|')
        if len(fields)!=5 or fields[2] not in ('8-K','8-K/A'): continue
        cik,name,form,day,path=fields
        filed = datetime.strptime(day,'%Y%m%d').date() if re.fullmatch(r'\d{8}',day) else date.fromisoformat(day)
        if filed > observed: raise ValueError('Daily index lists future filed date')
        if not date(2015,1,1)<=filed<=date(2020,12,31): outside+=1;continue
        m=re.fullmatch(r'edgar/data/(\d+)/(\d{10}-\d{2}-\d{6})\.txt',path)
        if not m or int(m[1])!=int(cik): raise ValueError('Daily identity/path conflict')
        rows.append({'CIK':str(int(cik)),'accession':m[2],'form':form,'filing_date':filed.isoformat(),
                     'source_path':path,'source_line':line_number,'source_index_sha256':source_sha256,
                     'observed_index_day':observed_day})
    return {'rows':rows,'outside_Development_rows':outside,'observation_day':observed_day}


def reconcile(daily, quarterly):
    daily_map=defaultdict(list);quarter_map=defaultdict(list)
    for r in daily: daily_map[key(r)].append(r)
    for r in quarterly: quarter_map[key(r)].append(r)
    result=[]
    for k in sorted(daily_map.keys()|quarter_map.keys()):
        d,q=daily_map[k],quarter_map[k]
        state='PRESENT_BOTH' if d and q else 'HISTORICAL_DAILY_ONLY' if d else 'CURRENT_QUARTERLY_ONLY'
        result.append(dict(zip(KEY_FIELDS,k),population_state=state,
                           daily_observations=[{'day':r['observed_index_day'],'sha256':r['source_index_sha256'],'line':r['source_line']} for r in d],
                           quarterly_observations=[{'sha256':r['source_index_sha256'],'line':r['source_line']} for r in q]))
    # Same CIK/accession but different form/date/path is preserved and flagged,
    # never fixed by preferring the current or first observation.
    groups=defaultdict(list)
    for row in result: groups[(row['CIK'],row['accession'])].append(row)
    for group in groups.values():
        for row in group: row['metadata_conflict']=len(group)>1
    return {'rows':result,'daily_equivalent_extra_rows':len(daily)-len(daily_map),
            'quarterly_equivalent_extra_rows':len(quarterly)-len(quarter_map)}


def event_state(form, item_present, *, source_available=True, conflicting=False):
    if not source_available:return 'SOURCE_REMOVED_OR_UNAVAILABLE'
    if conflicting:return 'UNKNOWN'
    if form=='8-K/A':return 'AMENDMENT_VERSION_ONLY'
    if form!='8-K':raise ValueError('Unsupported source form')
    if item_present is None:return 'UNKNOWN'
    return 'ORIGINAL_SIGNAL_EVENT' if item_present else 'NON_ITEM202'


def certification_query(start, end, decision, *, stage='development'):
    """Pre-event only. Confirmation is never opened by source certification."""
    s,e,d=map(datetime.fromisoformat,(start,end,decision))
    if any(x.tzinfo is None for x in (s,e,d)):raise ValueError('UTC-aware query bounds required')
    if stage!='development' or not date(2015,1,1)<=d.date()<=date(2020,12,31):
        raise ValueError('Confirmation certification inaccessible')
    if s>e or e>=d:raise ValueError('Post-event query forbidden before freeze')
    return True


def resolve_class(spans, decision, *, selected_class=None, predeclared_rule_hash=None):
    eligible=[s for s in spans if s.get('effective_from') and s.get('effective_to')
              and s['effective_from']<=decision<s['effective_to']]
    required=('issuer_cik','security_id','class_id','provider_id','historical_ticker','source_sha256')
    eligible=[s for s in eligible if all(s.get(k) for k in required)
              and s.get('domestic_common_equity_certified') is True and s.get('listing_span_certified') is True]
    if len(eligible)>1:
        if selected_class is None or not predeclared_rule_hash:return {'status':'AMBIGUOUS','binding':None}
        eligible=[s for s in eligible if s['class_id']==selected_class]
    if len(eligible)!=1:return {'status':'UNRESOLVED','binding':None}
    return {'status':'FULLY_RESOLVED' if eligible[0].get('twenty_session_lifecycle_certified') else 'UNRESOLVED_TERMINAL_PATH',
            'binding':eligible[0]}


def terminal_guard(binding, *, provider_present, crosses_terminal, terms_certified):
    if not provider_present:raise ValueError('Provider missing historically eligible security')
    if crosses_terminal and not terms_certified:raise ValueError('Terminal path unresolved; never drop or forward-fill')
    if not binding.get('listing_span_certified'):raise ValueError('Point/current metadata cannot establish historical listing')
    return True
