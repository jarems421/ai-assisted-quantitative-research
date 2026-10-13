"""EXP006 v002 human-readable cover identity and bounded path certificates.

Pure functions: no network, prices, outcome statistics or experiment state.
"""
from html.parser import HTMLParser
from datetime import date
import hashlib
import re
import unicodedata

INCEPTION='2019-05-02'
END='2020-12-31'
PARSER_VERSION='human_cover_table_v001'
# Explicit names avoid treating a US exchange or mailing address as domicile.
US_STATES=set(['alabama','alaska','arizona','arkansas','california','colorado','connecticut','delaware','florida','georgia','hawaii','idaho','illinois','indiana','iowa','kansas','kentucky','louisiana','maine','maryland','massachusetts','michigan','minnesota','mississippi','missouri','montana','nebraska','nevada','new hampshire','new jersey','new mexico','new york','north carolina','north dakota','ohio','oklahoma','oregon','pennsylvania','rhode island','south carolina','south dakota','tennessee','texas','utah','vermont','virginia','washington','west virginia','wisconsin','wyoming','district of columbia'])
TAXONOMY={'include':['common stock','common shares','ordinary shares'],
 'exclude':['preferred','preference','depositary','depository','warrant','rights','units','debt','notes','bonds','convertible','exchange traded fund','etf','fund shares'],
 'domestic_status':'Require independently source-grounded US incorporation; US venue alone insufficient',
 'multiple_common_classes':'MULTIPLE_ELIGIBLE_CLASSES_NO_DISCRETIONARY_SELECTION'}


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC',text).replace('\u200b','').split())


class CoverHTML(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.tables=[];self.stack=[];self.text=text
        self.lines=[0]
        for m in re.finditer('\n',text):self.lines.append(m.end())
        self.hidden=0;self.visible=[]
    def source_offset(self):
        line,col=self.getpos();return self.lines[line-1]+col
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','ix:header'):self.hidden+=1
        if tag=='table':self.stack.append({'start':self.source_offset(),'rows':[],'row':None,'cell':None})
        if self.stack:
            t=self.stack[-1]
            if tag=='tr':t['row']=[]
            if tag in ('td','th') and t['row'] is not None:t['cell']={'start':self.source_offset(),'parts':[]}
    def handle_data(self,data):
        if self.hidden:return
        self.visible.append((self.source_offset(),data))
        for t in self.stack:
            if t['cell'] is not None:t['cell']['parts'].append(data)
    def handle_endtag(self,tag):
        if tag in ('script','style','ix:header'):self.hidden=max(0,self.hidden-1)
        if not self.stack:return
        t=self.stack[-1]
        if tag in ('td','th') and t['cell'] is not None:
            cell=t['cell'];cell.update(text=normalized(' '.join(cell.pop('parts'))),end=self.source_offset()+len(tag)+3)
            if t['row'] is not None:t['row'].append(cell)
            t['cell']=None
        if tag=='tr' and t['row'] is not None:t['rows'].append(t['row']);t['row']=None
        if tag=='table':
            t=self.stack.pop();t['end']=self.source_offset()+8;self.tables.append(t)


def header_kind(text):
    t=normalized(text).lower()
    if 'title of each class' in t or 'class of securities' in t:return 'class_title'
    if 'trading symbol' in t:return 'trading_symbol'
    if 'exchange' in t and ('registered' in t or 'name of' in t):return 'exchange'
    return None


def parse_cover(body):
    text=body.decode('utf-8',errors='replace');p=CoverHTML(text);p.feed(text);p.close()
    rows=[];sha=hashlib.sha256(body).hexdigest()
    # The cover ends at the first substantive Item heading. Exhibits or later
    # narrative tables cannot supply a missing cover identity.
    item=re.search(r'\bitem\s+(?:1\.01|2\.02|[1-9]\.\d\d)\b',normalized(' '.join(t for _,t in p.visible)),re.I)
    cutoff=len(text)
    if item:
        for pos,data in p.visible:
            if re.search(r'\bitem\s+[1-9]\.\d\d\b',data,re.I):cutoff=min(cutoff,pos)
    for table in sorted(p.tables,key=lambda t:t['start']):
        if table['start']>=cutoff:continue
        header=None;header_indices=None
        for cells in table['rows']:
            kinds=[header_kind(c['text']) for c in cells]
            if all(k in kinds for k in ('class_title','trading_symbol','exchange')):
                header={k:kinds.index(k) for k in ('class_title','trading_symbol','exchange')}
                header_indices={k:sum(bool(c['text']) for c in cells[:i]) for k,i in header.items()}
                continue
            if not header:continue
            nonempty=[c for c in cells if c['text']]
            selected={}
            for field,index in header.items():
                cell=cells[index] if len(cells)>max(header.values()) else None
                if cell is None or not cell['text']:
                    j=header_indices[field];cell=nonempty[j] if j<len(nonempty) else None
                selected[field]=cell
            if any(c is None for c in selected.values()):continue
            values={k:c['text'] for k,c in selected.items()}
            if any(header_kind(v) for v in values.values()):continue
            if len(set(values.values()))<3:continue
            symbol=values['trading_symbol']
            if not re.fullmatch(r'[A-Za-z0-9.\-/ ,;()]{1,40}',symbol):continue
            rows.append(dict(values,source_hash=sha,source_locator={'representation':'HTML_TABLE',
                'character_start':min(c['start'] for c in selected.values()),
                'character_end':max(c['end'] for c in selected.values()),
                'field_character_spans':{k:[c['start'],c['end']] for k,c in selected.items()}}))
    # Source-preserving formatted text fallback, never company-name inference.
    if not rows:
        block=re.search(r'title of each class[^\n]*\n[^\n]*trading symbol[^\n]*\n[^\n]*exchange[^\n]*\n',text,re.I)
        # Ordinary three-column header on one line is the common text variant.
        if not block:block=re.search(r'title of each class[^\n]*trading symbol[^\n]*exchange[^\n]*\n',text,re.I)
        if block:
            pos=block.end()
            for line in text[pos:].splitlines(keepends=True):
                if re.search(r'\bitem\s+[1-9]\.\d\d',line,re.I):break
                fields=re.split(r'\t+| {2,}',line.strip())
                if len(fields)==3 and re.fullmatch(r'[A-Za-z0-9.\-/]{1,15}',fields[1]):
                    rows.append(dict(zip(('class_title','trading_symbol','exchange'),map(normalized,fields)),source_hash=sha,
                        source_locator={'representation':'FORMATTED_TEXT','character_start':pos,'character_end':pos+len(line)}))
                pos+=len(line)
                if pos-block.end()>4000:break
    # Duplicate/equivalent rendering is one point, with all locators retained.
    unique={}
    for row in rows:
        k=tuple(row[f] for f in ('class_title','trading_symbol','exchange'))
        if k not in unique:unique[k]=dict(row,additional_locators=[])
        else:unique[k]['additional_locators'].append(row['source_locator'])
    jurisdiction=[]
    for table in p.tables:
        if table['start']>=cutoff:continue
        for i,cells in enumerate(table['rows']):
            if not any(re.search(r'(?:state|jurisdiction).*?(?:incorporat|organiz)',c['text'],re.I) for c in cells):continue
            for neighbor in table['rows'][max(0,i-1):i+2]:
                for cell in neighbor:
                    if normalized(cell['text']).lower() in US_STATES:
                        jurisdiction.append({'value':cell['text'],'character_start':cell['start'],'character_end':cell['end']})
    return {'version':PARSER_VERSION,'rows':list(unique.values()),'domestic_jurisdiction_points':jurisdiction,'source_sha256':sha,
            'source_encoding':'UTF8_WITH_REPLACEMENT_FOR_INVALID_BYTES','inline_required':False}


def class_kind(title):
    t=normalized(title).lower()
    if any(re.search(r'\b'+re.escape(word)+r'(?:s)?\b',t) for word in TAXONOMY['exclude']):return 'EXCLUDED_NON_COMMON'
    if any(word in t for word in TAXONOMY['include']):return 'COMMON_EQUITY_CANDIDATE'
    return 'UNRESOLVED_CLASS_TAXONOMY'


def choose_class(rows):
    common=[r for r in rows if class_kind(r['class_title'])=='COMMON_EQUITY_CANDIDATE']
    if len(common)>1:return {'status':'MULTIPLE_ELIGIBLE_CLASSES','row':None,'common_count':len(common)}
    if len(common)==1:return {'status':'SINGLE_COMMON_CANDIDATE','row':common[0],'common_count':1}
    return {'status':'NO_ELIGIBLE_COMMON_CLASS','row':None,'common_count':0}


def event_scope(day):return INCEPTION<=day<=END


def provider_bridge(cover,candidates,*,historical_link_evidence=None):
    """Unique present-day match is a candidate; evidence must tie exact class."""
    if len(candidates)>1:return {'status':'AMBIGUOUS_PROVIDER_MAPPING','binding':None}
    if len(candidates)!=1:return {'status':'PROVIDER_MAPPING_UNAVAILABLE','binding':None}
    e=historical_link_evidence or {}
    if not all(e.get(k) for k in ('source_sha256','exact_class_reconciled','symbol_exchange_reconciled','historical_ticker_reuse_checked')):
        return {'status':'UNIQUE_CURRENT_CANDIDATE_UNCERTIFIED_HISTORICAL_LINK','binding':None}
    return {'status':'MAPPED','binding':candidates[0]}


def path_certificate(expected_sessions,observations,actions,*,identity_continuity=False):
    """Receives presence flags, never numeric prices. Exit is entry +20 sessions."""
    if len(expected_sessions)!=21 or expected_sessions!=sorted(set(expected_sessions)):raise ValueError('Entry plus 20-session exit required')
    start,end=expected_sessions[0],expected_sessions[-1]
    if not identity_continuity:return {'status':'IDENTITY_CONTINUITY_UNRESOLVED'}
    seen={r['date']:r for r in observations}
    for action in actions:
        if not start<=action['date']<=end:continue
        if action['type'] in ('rename','exchange_change','split','dividend') and not action.get('evidence_sha256'):
            return {'status':'ACTION_LINEAGE_UNRESOLVED'}
        if action['type'] in ('merger','cancellation','delisting','conversion') and not action.get('economic_transition_certified'):
            return {'status':'TERMINAL_PATH_UNRESOLVED'}
    if any(d not in seen or seen[d].get('open_available') is not True for d in expected_sessions):return {'status':'MISSING_SESSION_OR_OPEN'}
    return {'status':'PATH_CERTIFIED','entry':start,'exit':end,'sessions':21}


def pool_eligible(row,pool,*,identity_status):
    from src.research.item202_identity import allowed_pool
    return event_scope(row['filing_date']) and allowed_pool(row,pool) and identity_status=='FULLY_RESOLVED'
