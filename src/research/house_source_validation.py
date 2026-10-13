"""House-only source gate and source-grounded OCR row extraction. No outcomes."""
from collections import Counter
from datetime import datetime
import re
from src.research.congress_originals import normalized

FIELDS=('transaction_type','transaction_date','asset_description','printed_ticker','member_identity','document_identity')


def house_population(rows):
    return [r for r in rows if r.get('chamber')=='house']


def orient_tokens(page):
    """Normalize dominant page text direction from source boxes, never expectations."""
    tokens=page['tokens'];vertical=0;horizontal=0
    for t in tokens:
        b=t['box'];dx=max(p[0] for p in b)-min(p[0] for p in b);dy=max(p[1] for p in b)-min(p[1] for p in b)
        if len(t['text'])<4:continue
        if dy>dx:vertical+=1
        else:horizontal+=1
    rotate=vertical>horizontal
    result=[]
    for i,t in enumerate(tokens):
        points=[(y,page['width']-x) if rotate else (x,y) for x,y in t['box']]
        xs,ys=zip(*points)
        result.append(dict(t,x=min(xs),right=max(xs),y=min(ys),bottom=max(ys),
                           cx=sum(xs)/4,cy=sum(ys)/4,token_index=i))
    return result


def parse_ocr_rows(projection,render_loader=None):
    """Parse printed code/date rows or checkbox columns using only OCR geometry.

    Unsupported/ambiguous layouts stay unparsed. No expected snapshot values.
    """
    rows=[]
    for page in projection['pages']:
        tokens=orient_tokens(page)
        # Checkbox tables explicitly name Purchase/Sale/Exchange subcolumns.
        headings={}
        for action,label in [('purchase','purchase'),('sale','sale'),('exchange','exchange')]:
            matches=[t for t in tokens if normalized(t['text'])==label or label=='exchange' and normalized(t['text'])=='exchante']
            if len(matches)==1:headings[action]=matches[0]
        date_tokens=[]
        for t in tokens:
            m=re.fullmatch(r'\s*(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{2}|\d{4})\s*',t['text'])
            if m:
                try:
                    day=datetime.strptime('/'.join(m.groups()),'%m/%d/%Y' if len(m[3])==4 else '%m/%d/%y').date().isoformat()
                    date_tokens.append(dict(t,day=day))
                except ValueError:pass
        # Earliest date column to the right of the transaction-type columns,
        # distinct from later notification dates. Require a source header.
        checkbox=len(headings)>=2
        if checkbox:
            action_right=max(t['right'] for t in headings.values())
            eligible_dates=[t for t in date_tokens if t['cx']>action_right and t['cy']>max(h['cy'] for h in headings.values())]
            date_x=min((t['cx'] for t in eligible_dates),default=None)
            dates=[t for t in eligible_dates if date_x is not None and abs(t['cx']-date_x)<45]
        else:
            dates=date_tokens
        for d in sorted(dates,key=lambda t:t['cy']):
            same=[t for t in tokens if abs(t['cy']-d['cy'])<=max(12,(d['bottom']-d['y'])*0.8)]
            action=None;asset_tokens=[];used=[];pixel_cells=None
            if checkbox:
                votes=[]
                for kind,h in headings.items():
                    xs=[t for t in same if (normalized(t['text']) in ('x','v') or t['text'].strip()=='×') and abs(t['cx']-h['cx'])<max(20,(h['right']-h['x'])*0.5)]
                    if xs:votes.append(kind);used+=xs
                if len(votes)==1:action=votes[0]
                if not votes and render_loader:
                    # Source-only bitmap check of the explicitly labelled cells.
                    # It receives source boxes, never an expected transaction.
                    marks=[];pixel_cells={}
                    image=render_loader(page, tokens)
                    for kind,h in headings.items():
                        radius=max(8,min(18,(d['bottom']-d['y'])*.55))
                        crop=image.crop((int(h['cx']-radius),int(d['cy']-radius),int(h['cx']+radius),int(d['cy']+radius))).convert('L')
                        values=list(crop.getdata());ink=sum(v<100 for v in values)/len(values) if values else 0
                        pixel_cells[kind]={'center':[h['cx'],d['cy']],'radius':radius,'ink_fraction':ink}
                        if .06<=ink<=.50:marks.append(kind)
                    if len(marks)==1:action=marks[0]
                left=min(t['x'] for t in headings.values())
                asset_tokens=[t for t in same if t['right']<left and len(t['text'])>2]
            else:
                codes=[t for t in same if normalized(t['text']) in ('p','s','e','purchase','sale','exchange','spartial') and t['cx']<d['cx']]
                if len(codes)==1:
                    code=codes[0];action={'p':'purchase','s':'sale','e':'exchange','purchase':'purchase','sale':'sale','exchange':'exchange','spartial':'sale'}[normalized(code['text'])]
                    asset_tokens=[t for t in same if t['right']<code['x'] and len(t['text'])>2];used=[code]
            if not asset_tokens:continue
            asset=' '.join(t['text'] for t in sorted(asset_tokens,key=lambda t:t['x']))
            rows.append({'action':action,'transaction_date':d['day'],'asset_text':asset,'raw':asset,
                'source_locator':{'page':page['page'],'token_indices':sorted({t['token_index'] for t in asset_tokens+used+[d]}),
                    'render_sha256':page['render_sha256'],'source_sha256':projection['source_sha256']},
                'minimum_confidence':min(t['confidence'] for t in asset_tokens+used+[d]),'source_bitmap_checkbox_cells':pixel_cells})
    return rows


def compare(expected,actual):
    fields={k:'UNKNOWN' for k in FIELDS}
    if not actual:return fields
    for field,key in [('transaction_type','action'),('transaction_date','transaction_date')]:
        if actual.get(key):fields[field]='AGREE' if actual[key]==expected[key] else 'DISAGREE'
    asset=normalized(expected.get('asset_description') or '')
    if asset:fields['asset_description']='AGREE' if asset in normalized(actual['asset_text']) else 'UNKNOWN'
    printed=expected.get('printed_ticker')
    if printed and re.search(r'\('+re.escape(printed)+r'\)',actual['asset_text'],re.I):fields['printed_ticker']='AGREE'
    return fields


def associate_ocr_row(expected,rows):
    """Only unique asset/symbol anchors. Unverified OCR ordinals cannot disambiguate."""
    asset=normalized(expected.get('asset_description') or '');ticker=expected.get('printed_ticker')
    hits=[r for r in rows if asset and asset in normalized(r['asset_text']) or ticker and re.search(r'\('+re.escape(ticker)+r'\)',r['asset_text'],re.I)]
    if len(hits)==1:return hits[0]
    # Identical mandatory values across every matching row can be corroborated
    # without choosing an expected date/action or claiming an exact row identity.
    if hits and all(r.get('action') and r.get('transaction_date') for r in hits) and len({(r['action'],r['transaction_date']) for r in hits})==1:
        result=dict(hits[0]);result['source_locator']={'equivalent_candidate_locators':[r['source_locator'] for r in hits]}
        result['minimum_confidence']=min(r['minimum_confidence'] for r in hits)
        return result
    return None


def evaluate_gate(records,contract):
    criteria=contract['source_gate'];core=('transaction_type','transaction_date','asset_description')
    decisive=[r for r in records if all(r['fields'][f] in ('AGREE','DISAGREE') for f in core)]
    rates={f:sum(r['fields'][f]=='AGREE' for r in decisive)/len(decisive) if decisive else 0 for f in core}
    # Reject purchase/nonpurchase disagreements in either direction, including
    # expected non-purchases extracted as purchases.
    purchase_disagreements=sum(r.get('actual_action') is not None and
        (r['action_expected']=='purchase')!=(r['actual_action']=='purchase') for r in records)
    unresolved=[r for r in records if r not in decisive]
    clusters={}
    for name,getter in [('action',lambda r:r['action_expected']),('year',lambda r:r['year']),
                        ('printed_present',lambda r:str(r['printed_present'])),('amendment',lambda r:str(r['amendment']))]:
        total=Counter(getter(r) for r in records);missing=Counter(getter(r) for r in unresolved)
        clusters[name]={k:{'total':n,'unresolved':missing[k]} for k,n in sorted(total.items())}
    checks={'denominator_exact':len(records)==criteria['denominator'],'decisive_minimum':len(decisive)>=criteria['minimum_decisive'],
        'no_purchase_disagreement':purchase_disagreements==0,
        'date_rate':rates['transaction_date']>=criteria['decisive_date_agreement_min'],
        'type_rate':rates['transaction_type']>=criteria['decisive_type_agreement_min'],
        'asset_rate':rates['asset_description']>=criteria['decisive_asset_agreement_min']}
    # Cluster review cannot create a pass automatically. This implementation
    # requires explicit source-grounded review if mechanical checks pass.
    mechanical=all(checks.values())
    return {'verdict':'REQUIRES_CLUSTER_REVIEW' if mechanical else 'ABANDON_EXP007_SOURCE_FEASIBILITY',
        'checks':checks,'decisive':len(decisive),'unknown':len(unresolved),'agreement_rates':rates,
        'purchase_nonpurchase_disagreements':purchase_disagreements,'unresolved_clusters':clusters}
