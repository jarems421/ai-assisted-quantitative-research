"""Evidence-local revenue review packets; discovery never certifies accounting."""
from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
import json,re
from pathlib import Path
from xml.etree import ElementTree as ET
from src.research.phase3c.sources import RAW,put
from src.research.sec_pilot.acquisition import Archive
from src.research.phase3c.parsing import InlineFacts,reconcile_inline
from src.research.phase3d.certification import canonical_revenue
from src.research.phase3c.quality import compatible
from src.research.spec import digest
from src.research.phase3d.proof import ROOT,file_hash
from .text import LocatedText

PRIVATE=ROOT/'data/raw/phase3d_closure_v001'
DOCS=ROOT/'docs/acceleration'
X='http://www.xbrl.org/2003/instance'; D='http://xbrl.org/2006/xbrldi'


def evidence_spans(text,pattern,limit=8):
    """Exact decoded-character locators; hits are prompts for review, not verdicts."""
    return [{'start':max(0,m.start()-200),'end':min(len(text),m.end()+700),
             'span_sha256':digest(text[max(0,m.start()-200):min(len(text),m.end()+700)])}
            for m in list(re.finditer(pattern,text,re.I))[:limit]]


def packet(filing,archive,cached):
    sources=filing.get('sources',{}); accession=filing['accessionNumber']
    result={'accession':accession,'issuer_cik':filing['issuer_cik'],'filing_period':filing['reportDate'],
            'sources':{k:r['body']['sha256'] for k,r in sources.items() if 'body' in r},
            'observations':[],'evidence':{},'review_status':'NEEDS_ADDITIONAL_EVIDENCE'}
    if any(not sources.get(k,{}).get('body') or sources[k].get('status')!=200 for k in ('instance','primary')):
        return dict(result,reason='MISSING_STATEMENT_EVIDENCE')
    raw=archive.read(sources['instance']['body']); primary=archive.read(sources['primary']['body']).decode('utf-8')
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper(): raise ValueError('Unsafe original XML')
    namespaces={pair[0]:pair[1] for _,pair in ET.iterparse(BytesIO(raw),events=('start-ns',))}
    root=ET.fromstring(raw); contexts={c.get('id'):c for c in root.findall(f'{{{X}}}context')}; units={u.get('id'):u for u in root.findall(f'{{{X}}}unit')}
    inline=InlineFacts(); inline.feed(primary)
    contract=json.loads((DOCS/'phase3d_revenue_contract.json').read_bytes())
    reconciled=bool(cached and cached.get('parser_original_reconciliation')=='PASS'
                     and cached.get('source_sha256')==sources['instance']['body']['sha256']
                     and cached.get('code_sha256')==file_hash(ROOT/'src/research/phase3c/parsing.py'))
    for i,node in enumerate(root):
        if not isinstance(node.tag,str) or not node.tag.startswith('{'): continue
        ns,concept=node.tag[1:].split('}',1)
        if concept not in contract['candidate_concepts'] or not re.fullmatch(r'http://fasb.org/us-gaap/20\d{2}(?:-\d{2}-\d{2})?',ns): continue
        c=contexts.get(node.get('contextRef')); u=units.get(node.get('unitRef'))
        if c is None or u is None: continue
        start=c.findtext(f'{{{X}}}period/{{{X}}}startDate'); end=c.findtext(f'{{{X}}}period/{{{X}}}endDate')
        entity=c.find(f'{{{X}}}entity/{{{X}}}identifier')
        dimensions=c.findall(f'.//{{{D}}}explicitMember')+c.findall(f'.//{{{D}}}typedMember')
        measure=u.findtext(f'{{{X}}}measure',''); prefix,_,unit=measure.partition(':')
        if (not start or not end or end>filing['reportDate'] or dimensions or entity is None
            or entity.get('scheme')!='http://www.sec.gov/CIK' or entity.text.zfill(10)!=filing['issuer_cik']
            or unit!='USD' or namespaces.get(prefix)!='http://www.xbrl.org/2003/iso4217'
            or not 350<=(date.fromisoformat(end)-date.fromisoformat(start)).days+1<=380): continue
        value=''.join(node.itertext()).strip()
        try:
            if not Decimal(value).is_finite() or Decimal(value)<=0: continue
        except ArithmeticError: continue
        check=reconcile_inline({'contributors':[{'concept':concept,'namespace':ns,'context_ref':node.get('contextRef'),
                                                'unit_ref':node.get('unitRef'),'exact_value':value}]},inline)
        scales={r['scale'] for r in check.get('primary_locators',[])}
        observation={'issuer_cik':filing['issuer_cik'],'accession':accession,'form':'10-K','original_version':'ORIGINAL',
            'concept':concept,'namespace':ns,'context_ref':node.get('contextRef'),'entity_cik':entity.text.zfill(10),'dimensions':[],
            'period_start':start,'period_end':end,'period_role':'CURRENT' if end==filing['reportDate'] else 'COMPARATIVE',
            'filing_period_end':filing['reportDate'],'unit':'USD','scale':next(iter(scales)) if len(scales)==1 else None,
            'value':value,'decimals':node.get('decimals'),'locator':f'root-child[{i}]#{node.get("id","")}',
            'statement_locator':None,'source_sha256':sources['instance']['body']['sha256'],'primary_sha256':sources['primary']['body']['sha256'],
            'original_element_reconciled':reconciled,'primary_reconciled':check.get('primary_reconciliation')=='PASS',
            'conflicting_duplicates':False,'nil':node.get('{http://www.w3.org/2001/XMLSchema-instance}nil') in ('true','1')}
        result['observations'].append({'observation':observation,'primary_locators':check.get('primary_locators',[])})
    for r in result['observations']:
        o=r['observation']; matches=[q['observation'] for q in result['observations'] if all(q['observation'][k]==o[k] for k in ('concept','namespace','period_start','period_end','unit'))]
        o['conflicting_duplicates']=len({Decimal(q['value']) for q in matches})>1
        r['observation_sha256']=digest(o)
        r['contract_disposition']=canonical_revenue(o,contract,[],trusted_receipts=set())['reason']
    patterns={'statement':r'CONSOLIDATED\s+(?:STATEMENTS?|STATEMENT)\s+OF\s+(?:INCOME|OPERATIONS|EARNINGS)',
              'tax':r'assessed taxes|sales taxes|taxes collected|net of taxes',
              'recognition':r'revenue recognition|Topic\s*606|ASC\s*606|Accounting Standards Update.{0,30}2014',
              'perimeter':r'basis of consolidation|principles of consolidation|business combinations|acquisitions',
              'discontinued':r'\b(?:discontinued operations|recast|retrospective|restat(?:ed|ement))\b'}
    located=LocatedText(primary)
    result['evidence']={k:located.hits(p) for k,p in patterns.items()}
    result['locator_semantics']='Strict UTF8 decoded-character spans / original XML root-child indexes; original byte SHA retained'
    result['original_parser_reconciled']=reconciled
    result['reason']='OTHER_REVIEW_REQUIRED' if result['observations'] else 'UNSUPPORTED_CONCEPT'
    return result


def build():
    prior=json.loads((DOCS/'phase3c_evidence.json').read_bytes()); cohort=json.loads((DOCS/'phase3c_pilot_cohort.json').read_bytes())
    allowed={a for chain in prior['chains'] for a in chain['filing_accessions']}
    parser_hash=file_hash(ROOT/'src/research/phase3c/parsing.py'); cache=RAW/'parsed'/parser_hash
    packets=[]; archive=Archive(RAW)
    for path in sorted((RAW/'filings_v003').glob('*.json')):
        filing=json.loads(path.read_bytes())
        if filing['accessionNumber'] not in allowed: continue
        existing=cache/(filing['accessionNumber']+'.json')
        p=packet(filing,archive,json.loads(existing.read_bytes()) if existing.exists() else None)
        p['packet_sha256']=digest(p); put(PRIVATE/'accounting_packets'/(p['packet_sha256']+'.json'),p); packets.append(p)
    if {p['accession'] for p in packets}!=allowed or len(packets)!=89: raise ValueError('Original denominator changed')
    scoped_reviews=[]
    tax_reviews={'0000320193-20-000096':r'elected to record revenue net of taxes collected from customers that are remitted to governmental authorities',
                 '0001564590-20-034944':r'Revenue is recognized net of allowances for returns and any taxes collected from customers'}
    for accession,pattern in tax_reviews.items():
        source=json.loads((RAW/'filings_v003'/(accession+'.json')).read_bytes())['sources']['primary']
        text=LocatedText(archive.read(source['body']).decode('utf-8'))
        matches=list(re.finditer(pattern,text.text,re.I))
        if len(matches)!=1:raise ValueError('Reviewed assessed-tax evidence changed')
        m=matches[0]
        receipt={'version':'accounting_disclosure_review_v001','accession':accession,'source_sha256':source['body']['sha256'],
                 'check':'net_assessed_tax_disclosure','decision':'CERTIFIED_SCOPED_DISCLOSURE_ONLY',
                 'reviewer':'Codex source-excerpt review','reviewed_on':'2026-10-12','review_timestamp_precision':'DAY',
                 'evidence_locator':text.locate(max(0,m.start()-100),min(len(text.text),m.end()+200)),
                 'scope':'One filing disclosure; no complete economic line, three-year tax/basis/perimeter or trading certification'}
        put(PRIVATE/'accounting_scoped_reviews'/(digest(receipt)+'.json'),receipt)
        scoped_reviews.append(dict(receipt,receipt_sha256=digest(receipt)))
    chains=[]
    for chain in prior['chains']:
        group=[p for p in packets if p['accession'] in chain['filing_accessions']]
        reasons=set(); comparisons=[]
        for p in group:
            current=[r for r in p['observations'] if r['observation']['period_role']=='CURRENT']
            if not current: reasons.add(p['reason'])
            if any(r['observation']['conflicting_duplicates'] for r in current): reasons.add('DUPLICATE_CONFLICT')
            if not p['evidence'].get('tax'): reasons.add('TAX_TREATMENT_UNRESOLVED')
            if not p['evidence'].get('statement'): reasons.add('MISSING_STATEMENT_EVIDENCE')
            # A found snippet cannot certify unchanged basis/perimeter or absence of discontinued operations.
            reasons.add('OTHER_REVIEW_REQUIRED')
        for prev,curr in zip(sorted(group,key=lambda p:p['filing_period']),sorted(group,key=lambda p:p['filing_period'])[1:]):
            left=[r['observation'] for r in prev['observations'] if r['observation']['period_role']=='CURRENT']
            right=[r['observation'] for r in curr['observations'] if r['observation']['period_end']==prev['filing_period']]
            matches=[(a,b) for a in left for b in right if a['concept']==b['concept'] and a['period_start']==b['period_start']]
            try: passed=bool(matches) and all(compatible(a,b) for a,b in matches)
            except (ValueError,ArithmeticError): passed=False
            comparisons.append({'predecessor':prev['accession'],'later_accession':curr['accession'],'numeric_rounding_candidate':passed})
            if not passed: reasons.add('COMPARATIVE_NOT_RECONCILED')
        chains.append({'case_key':chain['case_key'],'originals':len(group),'packet_hashes':[p['packet_sha256'] for p in group],
                       'status':'NEEDS_ADDITIONAL_EVIDENCE','failure_categories':sorted(reasons),'comparatives':comparisons,'certified_triple':False})
    return {'version':'accounting_review_v001','contract_sha256':file_hash(DOCS/'phase3d_revenue_contract.json'),
       'issuer_denominator':30,'three_original_denominator':29,'originals':89,'observations':sum(len(p['observations']) for p in packets),
       'current_observations':sum(r['observation']['period_role']=='CURRENT' for p in packets for r in p['observations']),
       'primary_rendering_reconciled':sum(r['observation']['primary_reconciled'] for p in packets for r in p['observations']),
       'full_certified_triples':0,'trusted_full_accounting_receipts':0,'chains':chains,
       'scoped_disclosure_reviews':scoped_reviews,
       'packet_index':[{'accession':p['accession'],'packet_sha256':p['packet_sha256'],'status':p['review_status'],
                        'reason':p['reason'],'original_parser_reconciled':p.get('original_parser_reconciled',False),
                        'evidence_span_counts':{k:len(v) for k,v in p['evidence'].items()}} for p in packets],
       'real_acceleration_computed':False,'new_source_requests':0,
       'limitations':'Rendering and keyword locators are evidence packets, not economic-line, assessed-tax, recognition or unchanged-perimeter certification. All failures retained.'}
