"""Bounded official originals and field-level source checks; no outcomes."""
from collections import Counter
from datetime import datetime
import argparse,hashlib,json,re,subprocess
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.sec_pilot.acquisition import Archive
from src.research.item202_identity import require_published
from src.research.congress_sprint_source import DOCS,RAW,SprintHTTP

SAMPLE=DOCS/'exp007_original_validation_sample.json'
PYTHON=ROOT/'.research/exp007/pdf-env/Scripts/python.exe'


def normalized(text):return re.sub(r'[^a-z0-9]','',text.lower())


def original_url_allowed(chamber,url):
    if chamber=='house':return bool(re.fullmatch(r'https://disclosures-clerk\.house\.gov/public_disc/ptr-pdfs/\d{4}/[A-Za-z0-9_-]+\.pdf',url))
    if chamber=='senate':return bool(re.fullmatch(r'https://efdsearch\.senate\.gov/search/view/(?:ptr|paper)/[A-Za-z0-9-]+/',url))
    return False


def house_rows(pages):
    rows=[]
    for page in pages:
        lines=page['text'].splitlines();starts=[]
        pattern=r'\b(P|S|E|Purchase|Sale|Exchange)(?:\s*\(partial\))?\s+(\d{1,2}/\d{1,2}/\d{2,4})\b'
        for i,line in enumerate(lines):
            m=re.search(pattern,line,re.I)
            if m:starts.append((i,m))
        for j,(i,m) in enumerate(starts):
            end=starts[j+1][0] if j+1<len(starts) else len(lines)
            raw='\n'.join(lines[i:end]);action={'p':'purchase','s':'sale','e':'exchange','purchase':'purchase','sale':'sale','exchange':'exchange'}[m[1].lower()]
            day=datetime.strptime(m[2],'%m/%d/%Y' if len(m[2].split('/')[-1])==4 else '%m/%d/%y').date().isoformat()
            headers=[x for x in lines[:i] if re.search(r'\bAsset\b',x,re.I) and re.search(r'\bTransaction\b',x,re.I)]
            asset_text=raw
            if headers:
                header=headers[-1];start_col=re.search(r'\bAsset\b',header,re.I).start();end_col=re.search(r'\bTransaction\b',header,re.I).start()
                parts=[]
                for line in lines[i:end]:
                    if re.search(r'FILING STATUS|SUBHOLDING|COMMENT|CERTIFICATION',line,re.I):break
                    if not line.strip() and parts:break
                    parts.append(line[start_col:end_col])
                asset_text=' '.join(parts)
            rows.append({'action':action,'transaction_date':day,'raw':raw,'asset_text':asset_text,
                         'source_locator':{'page':page['page'],'start_line':i,'end_line':end}})
    return rows


def acquire():
    require_published(SAMPLE);sample=json.loads(SAMPLE.read_bytes());results=[]
    clients={ch:SprintHTTP('originals','HOUSE' if ch=='house' else 'SENATE') for ch in ('house','senate')}
    urls=sorted({(r['trade_key'][0],r['source_url']) for r in sample['records']})
    for chamber,url in urls:
        target=RAW/'original_acquisition'/(digest(url)+'.json')
        if target.exists():results.append(json.loads(target.read_bytes()));continue
        if not original_url_allowed(chamber,url):raise ValueError('Original URL outside exact official disclosure path')
        client=clients[chamber]
        if (client.root/'publication_stop.json').exists() and not client.reviewed_stop_allows(url):
            # Stop stays immutable; never retry or silently substitute a source.
            result={'source_url':url,'chamber':chamber,'status':'DEFERRED_PERSISTED_SOURCE_STOP'}
            put(target,result);results.append(result);continue
        receipt,body=client.fetch_reviewed(url,'FROZEN_ORIGINAL_DISCLOSURE_VALIDATION')
        result={'source_url':url,'chamber':chamber,'receipt':receipt,'source_root':client.root.relative_to(ROOT).as_posix(),
                'status':'ARCHIVED' if receipt['status']==200 else 'SOURCE_UNAVAILABLE'}
        put(target,result);results.append(result)
        print('Official original',chamber,receipt['status'],'retained',flush=True)
    value={'sample_sha256':digest(sample),'records':results,'records_sha256':digest(results)}
    put(RAW/'original_acquisition_result.json',value);return value


def review():
    sample=json.loads(SAMPLE.read_bytes());acquisition=json.loads((RAW/'original_acquisition_result.json').read_bytes())
    lookup={r['source_url']:r for r in acquisition['records']};records=[];parsed={}
    from src.research.congress_sprint_review import corpus
    geometry=json.loads((DOCS/'exp007_source_geometry.json').read_bytes())
    trades=corpus(range(int(geometry['development'][0][:4]),int(geometry['development'][1][:4])+1))['political_trades']
    original_trades={(r['chamber'],r['doc_id'],r['row_index']):r for r in trades}
    for r in sample['records']:
        source=lookup[r['source_url']];fields={k:'UNKNOWN' for k in ('transaction_type','transaction_date','asset_description','printed_ticker','member_identity','document_identity')}
        status='ORIGINAL_UNAVAILABLE';selected=None;reason=source['status']
        if source['status']=='ARCHIVED':
            root=ROOT/source['source_root'];body=Archive(root).read(source['receipt']['body'])
            if r['trade_key'][0]=='house' and body.startswith(b'%PDF'):
                if r['source_url'] not in parsed:
                    result=subprocess.run([str(PYTHON),'-m','src.research.congress_pdf',str(root/source['receipt']['body']['path'])],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    if result.returncode:raise ValueError('Offline PDF parser failed; no hidden fallback')
                    projection=json.loads(result.stdout);put(RAW/'pdf_projection'/(projection['source_sha256']+'.json'),projection)
                    parsed[r['source_url']]=projection
                projection=parsed[r['source_url']];rows=house_rows(projection['pages'])
                # Transaction/date association is anchored by exact original asset
                # or printed symbol. Never search by expected transaction type.
                asset=normalized(r['asset_description']);ticker=r.get('printed_ticker')
                matches=[x for x in rows if (asset and asset in normalized(x['asset_text']) or ticker and re.search(r'\('+re.escape(ticker)+r'\)',x['asset_text'],re.I)) and x['transaction_date']==r['transaction_date']]
                if len(matches)==1:
                    selected=matches[0];status='ORIGINAL_ROW_CHECKED';reason='UNIQUE_SOURCE_ASSET_OR_PRINTED_TICKER_AND_DATE_ASSOCIATION'
                    fields['transaction_type']='AGREE' if selected['action']==r['action'] else 'DISAGREE'
                    fields['transaction_date']='AGREE'
                    fields['asset_description']='AGREE' if asset and asset in normalized(selected['asset_text']) else 'UNKNOWN_PRESENTATION_DIFFERENCE'
                    fields['printed_ticker']='AGREE' if ticker and re.search(r'\('+re.escape(ticker)+r'\)',selected['raw'],re.I) else 'UNKNOWN'
                full=' '.join(p['text'] for p in projection['pages'])
                fields['document_identity']='AGREE' if r['trade_key'][1] in full else 'UNKNOWN'
                trade=original_trades[tuple(r['trade_key'])];first=normalized(trade.get('filer_first') or '');last=normalized(trade.get('filer_last') or '')
                if first and last and first in normalized(full) and last in normalized(full):fields['member_identity']='AGREE'
            elif r['trade_key'][0]=='senate':
                from src.research.item202_cover import CoverHTML
                parser=CoverHTML(body.decode('utf8',errors='replace'));parser.feed(body.decode('utf8',errors='replace'))
                senate_rows=[]
                for table in parser.tables:
                    mapping=None
                    for cells in table['rows']:
                        labels=[normalized(c['text']) for c in cells]
                        if 'transactiondate' in labels and 'type' in labels and 'assetname' in labels:
                            mapping={field:labels.index(label) for field,label in [('transaction_date','transactiondate'),('action','type'),('asset','assetname')]}
                            if 'ticker' in labels:mapping['ticker']=labels.index('ticker')
                            continue
                        if not mapping or len(cells)<=max(mapping.values()):continue
                        values={field:cells[i]['text'] for field,i in mapping.items()}
                        day=None
                        for fmt in ('%m/%d/%Y','%m/%d/%y','%Y-%m-%d'):
                            try:day=datetime.strptime(values['transaction_date'],fmt).date().isoformat();break
                            except ValueError:pass
                        if day:senate_rows.append(dict(values,transaction_date=day,source_locator={'representation':'HTML_TABLE','character_start':cells[0]['start'],'character_end':cells[-1]['end']}))
                asset=normalized(r['asset_description']);ticker=r.get('printed_ticker')
                matches=[x for x in senate_rows if x['transaction_date']==r['transaction_date'] and
                    (asset and asset in normalized(x['asset']) or ticker and ticker.casefold()==x.get('ticker','').casefold())]
                if len(matches)==1:
                    selected=matches[0];status='ORIGINAL_ROW_CHECKED';reason='UNIQUE_OFFICIAL_SENATE_ASSET_DATE_ROW'
                    fields['transaction_type']='AGREE' if selected['action'].lower()==r['action'] else 'DISAGREE'
                    fields['transaction_date']='AGREE';fields['asset_description']='AGREE' if asset in normalized(selected['asset']) else 'UNKNOWN'
                    fields['printed_ticker']='AGREE' if ticker and ticker.casefold()==selected.get('ticker','').casefold() else 'UNKNOWN'
                    fields['document_identity']='AGREE' if r['trade_key'][1] in r['source_url'] else 'UNKNOWN'
                full=' '.join(x for _,x in parser.visible);trade=original_trades[tuple(r['trade_key'])]
                if normalized(trade.get('filer_first') or '') in normalized(full) and normalized(trade.get('filer_last') or '') in normalized(full):fields['member_identity']='AGREE'
            else:
                reason='NON_PDF_HOUSE_ORIGINAL_UNAVAILABLE_FOR_PARSER'
        records.append({'trade_key':r['trade_key'],'source_url':r['source_url'],'action_expected':r['action'],
            'status':status,'fields':fields,'reason':reason,'source_locator':selected['source_locator'] if selected else None,
            'source_sha256':source.get('receipt',{}).get('body',{}).get('sha256'),
            'resolved_ticker_not_required_in_original':True})
    fields={field:dict(Counter(r['fields'][field] for r in records)) for field in records[0]['fields']}
    value={'version':'EXP007_original_field_validation_v001','sample_sha256':digest(sample),'records':records,'records_sha256':digest(records),
           'field_results':fields,'purchase_type_disagreements':sum(r['action_expected']=='purchase' and r['fields']['transaction_type']=='DISAGREE' for r in records),
           'classification_unresolved_observations':sum(r['fields']['transaction_type']=='UNKNOWN' for r in records),
           'no_unverified_purchase_classification_promoted':True,'performance_evaluations':0}
    put(RAW/'original_field_validation_v001.json',value)
    print('Original field-level results:',fields);return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('acquire','review'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.command=='review':review()
    elif not a.execute:p.error('Original acquisition requires --execute')
    else:acquire()
