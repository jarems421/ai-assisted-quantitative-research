"""Class/lifecycle review of existing source bodies within2015–2021 only."""
from collections import Counter
import json,re
from src.research.phase3c.sources import RAW,put
from src.research.sec_pilot.acquisition import Archive
from src.research.sec_pilot.acquisition import now
from src.research.phase3d.proof import file_hash
from src.research.spec import digest
from .accounting import PRIVATE,DOCS
from .text import LocatedText

# Developer review of source excerpts. Each replay must find the exact disclosed
# terms; these facts do not certify payment timing, a full span or position NAV.
REVIEWS={
 '0001144204-17-045261':{'kind':'cash_acquisition','cash_per_share':'42.00','currency':'USD','pattern':r'converted into the right to receive \$42\.00 in cash, without interest'},
 '0001193125-21-004213':{'kind':'cash_acquisition','cash_per_share':'131.50','currency':'USD','pattern':r'converted into the right to receive \$131\.50 in cash, without interest and less any required tax withholding'},
 '0001104659-19-065939':{'kind':'mixed_cash_stock_contingent','cash_per_share':'50.00','currency':'USD','stock_ratio':'1',
                       'contingent_right':'One CVR; contingent USD9, never assumed payable','pattern':r'\$50\.00 in cash, without interest, \(2\) one share of Bristol-Myers Squibb common stock and \(3\) one tradeable contingent value right'},
 '0001104659-21-094624':{'kind':'mixed_cash_stock_election','cash_per_share':'60','currency':'USD','stock_ratio':'2.1243',
                       'stock_instrument':'AstraZeneca ADS, with ordinary-share election','pattern':r'2\.1243 American depositary shares.{0,380}\(2\) \$60 in cash'},
 '0001193125-19-306335':{'kind':'stock_acquisition_fractional_cash','stock_ratio':'0.59625',
                       'stock_instrument':'Viacom Class B to ViacomCBS Class B; cash-in-lieu required','pattern':r'0\.59625 shares of ViacomCBS Class B Common Stock'},
 '0001193125-19-306334':{'kind':'surviving_issuer_rename_exchange_change',
                       'pattern':r'with CBS continuing as the surviving company'}
}


def within_cutoff(accession):
    if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession or ''): raise ValueError('Bad accession chronology')
    return 15<=int(accession[11:13])<=21


def build():
    cohort=json.loads((DOCS/'phase3c_pilot_cohort.json').read_bytes())
    prior=json.loads((DOCS/'phase3c_evidence.json').read_bytes()); old={r['case_key']:r for r in prior['identity']}
    batch_path=PRIVATE/'source_review_batch.json'
    if not batch_path.exists():put(batch_path,{'recorded_at_utc':now(),'reviewer':'Codex source-excerpt review'})
    batch=json.loads(batch_path.read_bytes())
    docs=[]; receipts=[]; archive=Archive(RAW)
    for name in ('lifecycle_primary_summary.json','merger_primary_summary.json'):
        for row in json.loads((RAW/name).read_bytes()):
            accession=row.get('accession'); primary=row.get('sources',{}).get('primary')
            result={'issuer_cik':row['issuer_cik'],'accession':accession,'form':row.get('form','8-K'),
                    'status':'OUTSIDE_CLOSURE_CUTOFF_METADATA_ONLY','body_read':False,'review_receipt_sha256':None}
            if not within_cutoff(accession): docs.append(result); continue
            if not primary or primary.get('status')!=200 or not primary.get('body'):
                result['status']='SOURCE_UNAVAILABLE';docs.append(result);continue
            source=archive.read(primary['body']).decode('utf-8'); text=LocatedText(source)
            result.update(status='EVIDENCE_PACKET_NOT_SPAN_CERTIFIED',body_read=True,source_sha256=primary['body']['sha256'],url=primary['url'],
                          endpoint_candidates=text.hits(r'commence trading|ceased trading|suspend.{0,60}trading|effective|registered',limit=8),
                          term_candidates=text.hits(r'converted into|converted automatically|per Share|common stock|liquidat|bankrupt|cancel|over-the-counter',limit=8))
            recipe=REVIEWS.get(accession)
            if recipe:
                hits=list(re.finditer(recipe['pattern'],text.text,re.I))
                if len(hits)!=1: raise ValueError('Reviewed source assertion missing/ambiguous: '+accession)
                match=hits[0]; locator=text.locate(max(0,match.start()-500),min(len(text.text),match.end()+1000))
                receipt={'version':'source_claim_review_v001','reviewer':'Codex source-excerpt review','decision':'CERTIFIED_DISCLOSED_TERMS_ONLY',
                   'source_sha256':primary['body']['sha256'],'accession':accession,'issuer_cik':row['issuer_cik'],
                   'evidence_locator':locator,'facts':{k:v for k,v in recipe.items() if k!='pattern'},
                   'exceptions':'Retain excluded affiliate/dissenting shares, withholding, elections, contingent and fractional consideration where source specifies; do not presume ordinary held-position treatment',
                   'security_id':None,'share_class':'AS_DEFINED_IN_SOURCE_NOT_STABLE_ID_CERTIFIED',
                   'payment_timing':'UNRESOLVED','position_contract':'UNRESOLVED','reviewed_on':'2026-10-12',
                   'review_timestamp_precision':'DAY','recorded_at_utc':batch['recorded_at_utc'],
                   'complete_terminal_certificate':False}
                put(PRIVATE/'lifecycle_reviews'/(digest(receipt)+'.json'),receipt)
                result.update(review_receipt_sha256=digest(receipt),disclosed_facts=receipt['facts'],status='DISCLOSED_TERMS_REVIEWED_PATH_UNRESOLVED')
                receipts.append(receipt)
            put(PRIVATE/'lifecycle_packets'/(digest(result)+'.json'),result);docs.append(result)
    cases=[]
    for case in cohort['cases']:
        previous=old[case['case_key']]; relevant=[r for r in docs if r['issuer_cik']==case['issuer_cik']]
        if previous['status']=='AMBIGUOUS': status='AMBIGUOUS_CLASS'
        elif previous['cover_observation_count'] or previous['single_share_class_identifier_candidate']: status='POINT_OBSERVATION_ONLY'
        else: status='UNRESOLVED'
        endpoint=None
        if case['issuer_cik']=='0000098246':
            tif=next((r for r in docs if r['accession']=='0001193125-21-004213' and r['body_read']),None)
            source_row=next(r for r in json.loads((RAW/'merger_primary_summary.json').read_bytes()) if r['accession']=='0001193125-21-004213')
            text=LocatedText(archive.read(source_row['sources']['primary']['body']).decode('utf-8'))
            exact=r'Trading of the Common Stock on NYSE was suspended prior to the opening of trading on January 7, 2021'
            matches=list(re.finditer(exact,text.text))
            if tif and len(matches)==1:
                m=matches[0];status='PARTIAL_END_ONLY'
                endpoint={'event_date':'2021-01-07','timing_precision':'BEFORE_OPEN_NOT_EXACT_INSTANT',
                          'share_class':'Common stock, par value USD0.01; TIF/NYSE cover evidence',
                          'source_sha256':tif['source_sha256'],'evidence_locator':text.locate(m.start(),m.end()),
                          'listing_removal_distinct_from_trading_suspension':True}
        # No precise listing span is manufactured from disclosure/registration.
        cases.append({'case_key':case['case_key'],'issuer_cik':case['issuer_cik'],'historical_symbol_candidate':case['historical_symbol_candidate'],
             'identity_status':status,'effective_from':None,'effective_to':None,'start_evidence_sha256':None,'end_evidence_sha256':None,
             'stable_identifier_status':previous['figi_status'],'class_point_identified':previous['class_point_identified'],
             'reviewed_end_evidence':endpoint,
             'source_document_accessions':[r['accession'] for r in relevant],
             'terminal_status':'DISCLOSED_TERMS_ONLY' if any(r.get('review_receipt_sha256') for r in relevant) else 'UNRESOLVED',
             'complete_nav_capable':False,'reason':'Independent listing endpoints, dated stable class bridge and complete settlement/recovery terms missing'})
    return ({'version':'identity_closure_v001','denominator':60,'cases':cases,'status_counts':dict(Counter(r['identity_status'] for r in cases)),
             'certified_full_spans':0,'source_documents':docs,'outside_cutoff_documents':sum(not r['body_read'] and r['status']=='OUTSIDE_CLOSURE_CUTOFF_METADATA_ONLY' for r in docs),'new_source_requests':0},
            {'version':'terminal_closure_v001','frame_denominator':60,'completion_document_denominator':10,'reviewed_disclosed_claims':len(receipts),
             'claims':[{'accession':r['accession'],'source_sha256':r['source_sha256'],'receipt_sha256':digest(r),'facts':r['facts'],
                       'complete_terminal_certificate':False,'evidence_locator':r['evidence_locator']} for r in receipts],
             'certified_position_terminal_cases':0,'complete_nav_paths':0,'incomplete_frame_paths':60,
             'limitations':'Source consideration/surviving issuer facts are reviewed; payment, exact class intervals, successor and excluded-holder terms remain unresolved. No NAV calculated.'})
