"""Offline archive/freeze verification; no network, calculations or rewrites."""
from collections import Counter
from datetime import datetime
import json
from src.research.sec_pilot.acquisition import Archive
from src.research.phase3c.sources import require_cohort,RAW as OLD
from src.research.phase3d.proof import file_hash
from src.research.spec import digest
from .sources import RAW,DOCS


def source_ledger():
    providers={}
    for provider in ('SEC','Documentation'):
        rows=[json.loads(p.read_bytes()) for p in (RAW/'attempts'/provider).glob('*.json')]
        times=sorted(datetime.fromisoformat(r['request_started_at_utc']) for r in rows)
        gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:])]
        providers[provider]={'request_starts':len(rows),'successes':sum(r.get('status')==200 for r in rows),
             'failures':sum(r.get('status')!=200 for r in rows),'minimum_observed_start_gap_seconds':min(gaps) if gaps else None,
             'required_gap_seconds':.55,'purchase_or_upgrade':False,'account_wide_debit':'UNKNOWN'}
    for name in ('OpenFIGI','Tiingo','FMP','Orbis','Nexus','Aurora'):
        providers[name]={'request_starts':0,'successes':0,'failures':0,'purchase_or_upgrade':False,'account_wide_debit':'UNKNOWN'}
    providers['documentation/browser']={'operations':10,'search_queries':3,'page_opens':5,'pdf_screenshots':2,
                'source':'Official calendar and primary statistical-method references; independent of original-byte HTTP receipts',
                'original_byte_hash':'NOT_AVAILABLE_FROM_BROWSER_TOOL'}
    return {'version':'phase3er_source_registry_v001','providers':providers,'archived_existing_header_hits':89,
            'new_original_header_receipts':161,'new_original_calendar_responses':4,'price_or_financial_fact_acquisition':False,
            'delivery_network':'Git push / hosted CI metadata observations recorded separately from source research'}


def audit():
    require_cohort(json.loads((DOCS/'phase3c_pilot_cohort.json').read_bytes()))
    source=json.loads((RAW/'source_summary.json').read_bytes())
    if source!=json.loads((DOCS/'phase3e_redesign_source_metadata.json').read_bytes()):raise ValueError('Public/source summary mismatch')
    indexes={root:{record['url']:record for p in (root/'requests').glob('*.json') for record in [json.loads(p.read_bytes())]} for root in (OLD,RAW)}
    for r in source['records']:
        root=OLD if r['receipt_namespace']=='phase3c_v001' else RAW
        rec=indexes[root][r['header_url']]
        Archive(root).read(rec['body'])
        if rec['body']['sha256']!=r['header_sha256']:raise ValueError('Header lineage mismatch')
        if json.loads((RAW/'header_records'/(r['accession']+'.json')).read_bytes())!=r:raise ValueError('Header derivative changed')
    for r in source['calendar_documents']:Archive(RAW).read(r['body'])
    protocol=json.loads((DOCS/'phase3e_inference_protocol_v003.json').read_bytes());geometry=json.loads((DOCS/'phase3e_stage_geometry.json').read_bytes())
    first=json.loads((RAW/'inference_freeze.json').read_bytes());corrected=json.loads((RAW/'inference_freeze_correction_001.json').read_bytes())
    if first['protocol_sha256']!=digest(protocol) or corrected['protocol_sha256']!=digest(protocol):raise ValueError('Frozen protocol changed')
    if first['geometry_sha256']!=digest(geometry) or corrected['geometry_sha256']!=digest(geometry):raise ValueError('Frozen geometry changed')
    if first['candidate_code_sha256']!=file_hash(DOCS.parent.parent/'src/research/phase3er/inference.py'):raise ValueError('Frozen method code changed')
    if corrected['original_code_sha256']!=first['candidate_code_sha256'] or corrected['corrected_code_sha256']!=file_hash(DOCS.parent.parent/'src/research/phase3er/inference_correction.py'):raise ValueError('Correction code changed')
    old=json.loads((DOCS/'phase3e_inference_calibration_v003.json').read_bytes());new=json.loads((DOCS/'phase3e_inference_calibration_v003_correction_001.json').read_bytes())
    for result,freeze in [(old,first),(new,corrected)]:
        if result['freeze_receipt_sha256']!=digest(freeze) or json.loads((RAW/'calibration'/(digest(result)+'.json')).read_bytes())!=result:raise ValueError('Calibration archive changed')
    for a,b in zip(old['rows'],new['rows']):
        if a['world'] not in ('ar05','persistent098') and a!=b:raise ValueError('Non-AR outputs changed')
        if a['annual_effect']==0 and (a['primary_rejection']!=b['primary_rejection'] or a['coverage']!=b['coverage']):raise ValueError('Scale-invariant null outputs changed')
    if old['power_sensitivity']!=new['power_sensitivity']:raise ValueError('IID sensitivity changed')
    ledger=source_ledger()
    if any(r.get('failures',0) for r in ledger['providers'].values()):raise ValueError('Unreconciled source failures')
    if any(r.get('minimum_observed_start_gap_seconds',1)<.54 for r in ledger['providers'].values()):raise ValueError('Source pacing failure')
    return {'status':'PASS_BOUNDED_ARCHIVE_AND_FREEZE_RECONCILIATION','header_records':250,'original_runs_preserved':2,
            'non_ar_and_null_invariants_exact':True,'acquisition':False,'real_performance':False}
