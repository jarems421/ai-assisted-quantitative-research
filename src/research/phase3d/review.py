"""Offline bounded accounting-candidate census, not a new SEC parser or signal."""
from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from src.research.phase3c.sources import RAW
from src.research.sec_pilot.acquisition import Archive
from src.research.spec import digest
from .proof import ROOT,file_hash

XBRLI='http://www.xbrl.org/2003/instance'
XBRLDI='http://xbrl.org/2006/xbrldi'


def candidate_census():
    contract=json.loads((ROOT/'docs/acceleration/phase3d_revenue_contract.json').read_bytes())
    cohort=json.loads((ROOT/'docs/acceleration/phase3c_pilot_cohort.json').read_bytes())
    cases={r['issuer_cik']:r['case_key'] for r in cohort['cases'] if r['revenue_candidate']}
    prior=json.loads((ROOT/'docs/acceleration/phase3c_evidence.json').read_bytes())
    allowed={a for r in prior['chains'] for a in r['filing_accessions']}
    records=[]; archive=Archive(RAW)
    for path in sorted((RAW/'filings_v003').glob('*.json')):
        filing=json.loads(path.read_bytes()); accession=filing['accessionNumber']
        if accession not in allowed: continue
        if filing['form']!='10-K': raise ValueError('Original form changed')
        row={'case_key':cases[filing['issuer_cik']],'accession':accession,'filing_period':filing['reportDate'],
             'concept_candidates':{},'status':'UNAVAILABLE_INSTANCE','source_manifest_sha256':file_hash(path),
             'certified_source_line':False,'accounting_perimeter_status':'UNRESOLVED'}
        instance=filing.get('sources',{}).get('instance')
        if not instance or instance.get('status')!=200 or 'body' not in instance:
            records.append(row); continue
        raw=archive.read(instance['body']); row['source_sha256']=instance['body']['sha256']
        if b'<!DOCTYPE' in raw.upper(): raise ValueError('Unexpected DTD in archived XBRL')
        namespaces={}
        for _,pair in ET.iterparse(BytesIO(raw),events=('start-ns',)): namespaces[pair[0]]=pair[1]
        tree=ET.fromstring(raw)
        contexts={c.get('id'):c for c in tree.findall(f'{{{XBRLI}}}context')}
        units={u.get('id'):u for u in tree.findall(f'{{{XBRLI}}}unit')}
        counts=Counter(); conflicts=0; seen={}
        for fact in tree:
            if not fact.tag.startswith('{'): continue
            namespace,concept=fact.tag[1:].split('}',1)
            if concept not in contract['candidate_concepts'] or not re.fullmatch(r'http://fasb.org/us-gaap/20\d{2}(?:-\d{2}-\d{2})?',namespace): continue
            context=contexts.get(fact.get('contextRef')); unit=units.get(fact.get('unitRef'))
            if context is None or unit is None: continue
            end=context.findtext(f'{{{XBRLI}}}period/{{{XBRLI}}}endDate')
            start=context.findtext(f'{{{XBRLI}}}period/{{{XBRLI}}}startDate')
            entity=context.findtext(f'{{{XBRLI}}}entity/{{{XBRLI}}}identifier')
            if not start or end!=filing['reportDate'] or entity is None or entity.lstrip('0')!=filing['issuer_cik'].lstrip('0'): continue
            if not 350 <= (date.fromisoformat(end)-date.fromisoformat(start)).days+1 <=380: continue
            if context.find(f'.//{{{XBRLDI}}}explicitMember') is not None or context.find(f'.//{{{XBRLDI}}}typedMember') is not None: continue
            measure=unit.findtext(f'{{{XBRLI}}}measure','')
            prefix,_,name=measure.partition(':')
            if name!='USD' or namespaces.get(prefix)!='http://www.xbrl.org/2003/iso4217': continue
            try:
                value=Decimal(fact.text or '')
                if not value.is_finite() or value<=0: continue
            except ArithmeticError: continue
            counts[concept]+=1
            key=(namespace,concept,start,end,measure)
            if key in seen and seen[key]!=value: conflicts+=1
            seen[key]=value
        row.update(status='CANDIDATE_CENSUS_ONLY_NOT_CERTIFIED',concept_candidates=dict(sorted(counts.items())),
                   conflicting_equivalent_contexts=conflicts,primary_sha256=filing.get('sources',{}).get('primary',{}).get('body',{}).get('sha256'))
        records.append(row)
    if {r['accession'] for r in records}!=allowed or len(records)!=89: raise ValueError('Original denominator changed')
    issuers=[]
    for cik,key in sorted(cases.items(),key=lambda kv:kv[1]):
        group=[r for r in records if r['case_key']==key]
        issuers.append({'case_key':key,'selected_originals':len(group),'candidate_in_every_original':len(group)==3 and all(r['concept_candidates'] for r in group),
                        'competing_line_in_any_original':any(len(r['concept_candidates'])>1 for r in group),'certified_triple':False})
    return {'version':'phase3d_candidate_census_v001','contract_sha256':digest(contract),'prior_evidence_sha256':file_hash(ROOT/'docs/acceleration/phase3c_evidence.json'),
            'source_frame_sha256':cohort['cohort_sha256'],'original_denominator':len(records),'issuer_denominator':len(issuers),
            'concept_presence_upper_bound_triples':sum(r['candidate_in_every_original'] for r in issuers),
            'fully_certified_triples':0,'review_receipts_accepted':0,'records':records,'issuers':issuers,
            'limitations':'Candidate presence only; no source line chosen, statement/Inline reconciliation, historic taxonomy mapping, accounting or perimeter certification inferred. Census not an alpha feature; old parser snapshots preserved.',
            'new_source_requests':0,'real_acceleration_computed':False}
