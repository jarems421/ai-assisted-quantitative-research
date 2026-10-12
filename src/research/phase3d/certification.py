"""Explicit reviewed accounting and identity contracts. No fuzzy normalization."""
from datetime import date, timedelta
from decimal import Decimal
import re
from src.research.spec import digest
from src.research.phase3c.quality import compatible
from src.research.sec_pilot.provenance import instant


def canonical_revenue(row, contract, receipts, *, trusted_receipts):
    original=dict(row)
    def unavailable(reason): return {'status':'UNAVAILABLE','reason':reason,'original':original,'contract_sha256':digest(contract)}
    if row.get('concept') not in contract['candidate_concepts'] or not re.fullmatch(r'http://fasb.org/us-gaap/20\d{2}(?:-\d{2}-\d{2})?',row.get('namespace','')):
        return unavailable('UNAPPROVED_CONCEPT_OR_TAXONOMY')
    if any(k not in row for k in contract['mandatory_provenance']): return unavailable('INCOMPLETE_PROVENANCE')
    try:
        start=date.fromisoformat(row['period_start']); end=date.fromisoformat(row['period_end']); value=Decimal(row['value'])
        invalid=(row['form']!='10-K' or row['original_version']!='ORIGINAL' or row['dimensions'] or row['unit']!='USD'
                 or row['issuer_cik']!=row['entity_cik'] or row.get('period_role') not in ('CURRENT','COMPARATIVE')
                 or (row['period_role']=='CURRENT' and row['filing_period_end']!=row['period_end'])
                 or (row['period_role']=='COMPARATIVE' and row['filing_period_end']<=row['period_end'])
                 or not 350 <= (end-start).days+1 <=380 or not value.is_finite() or value<=0
                 or row['conflicting_duplicates'] or not row['original_element_reconciled'] or not row['primary_reconciled']
                 or not row['statement_locator'] or not row['locator'] or row.get('nil'))
    except (ValueError,TypeError,ArithmeticError): return unavailable('INVALID_PERIOD_OR_VALUE')
    if invalid: return unavailable('CONTEXT_VERSION_SCALE_OR_STATEMENT')
    matching=[r for r in receipts if digest(r) in trusted_receipts and r.get('source_sha256')==row['source_sha256']
              and r.get('primary_sha256')==row['primary_sha256'] and r.get('locator')==row['locator']
              and r.get('concept')==row['concept'] and r.get('namespace')==row['namespace']
              and r.get('observation_sha256')==digest(row)]
    if len(matching)!=1: return unavailable('MISSING_OR_CONFLICTING_REVIEW')
    receipt=matching[0]
    try: instant(receipt['reviewed_at'])
    except (KeyError,ValueError): return unavailable('INVALID_REVIEW_CLOCK')
    if (not all(receipt.get(k) for k in ('reviewer','version','reason','mapping_rule','accounting_basis','perimeter','evidence_locators'))
            or receipt.get('decision')!='CERTIFIED' or any(receipt.get('checks',{}).get(k) is not True for k in contract['mandatory_review_checks'])):
        return unavailable('ACCOUNTING_PERIMETER_NOT_CERTIFIED')
    result={'status':'CERTIFIED_SOURCE_LINE','original':original,'canonical_mapping':contract['canonical_line'],
            'mapping_rule':receipt['mapping_rule'],'mapping_confidence':'EXPLICIT_REVIEW_NOT_PROBABILITY',
            'accounting_basis':receipt['accounting_basis'],'perimeter':receipt['perimeter'],
            'review_receipt_sha256':digest(receipt),'contract_sha256':digest(contract),
            'trading_eligible':False}
    return dict(result,certification_sha256=digest(result))


def revenue_triple(observations, comparatives):
    if len(observations)!=3 or any(r['status']!='CERTIFIED_SOURCE_LINE' or r['original'].get('period_role')!='CURRENT' for r in observations):
        return {'status':'UNAVAILABLE','reason':'MISSING_CERTIFIED_ORIGINAL'}
    if any(digest({k:v for k,v in r.items() if k!='certification_sha256'})!=r.get('certification_sha256') for r in [*observations,*comparatives]):
        return {'status':'UNAVAILABLE','reason':'CERTIFIED_OBSERVATION_CHANGED'}
    rows=sorted(observations,key=lambda r:r['original']['period_end'])
    original=[r['original'] for r in rows]
    if len({r['accession'] for r in original})!=3 or len({r['issuer_cik'] for r in original})!=1:
        return {'status':'UNAVAILABLE','reason':'ISSUER_OR_ORIGINAL_VERSION_CONFLICT'}
    if len({r['accounting_basis'] for r in rows})!=1 or len({r['perimeter'] for r in rows})!=1:
        return {'status':'UNAVAILABLE','reason':'BASIS_OR_PERIMETER_CHANGE'}
    if len(comparatives)!=2: return {'status':'UNAVAILABLE','reason':'MISSING_COMPARATIVE'}
    for prior,current,comparison in zip(original,original[1:],comparatives):
        if (date.fromisoformat(current['period_start'])!=date.fromisoformat(prior['period_end'])+timedelta(days=1)
                or comparison.get('status')!='CERTIFIED_SOURCE_LINE'):
            return {'status':'UNAVAILABLE','reason':'PERIOD_OR_COMPARATIVE_CERTIFICATION'}
        c=comparison['original']
        if (c.get('period_role')!='COMPARATIVE' or c['accession']!=current['accession'] or c['issuer_cik']!=current['issuer_cik']
                or c['period_start']!=prior['period_start'] or c['period_end']!=prior['period_end']
                or c['unit']!=prior['unit'] or comparison['accounting_basis']!=rows[0]['accounting_basis']
                or comparison['perimeter']!=rows[0]['perimeter'] or not compatible(prior,c)):
            return {'status':'UNAVAILABLE','reason':'ROUNDING_OR_COMPARATIVE_PERIMETER'}
    return {'status':'CERTIFIED_SOURCE_TRIPLE','contributor_hashes':[digest(r) for r in rows],
            'trading_eligible':False,'acceleration_computed':False}


def dated_identity(rows, *, at, trusted_evidence):
    instant(at)
    for row in rows:
        fields=('issuer_cik','security_id','class','exchange','ticker','identifier_level','effective_from','effective_to','start_evidence_sha256','end_evidence_sha256')
        if not all(row.get(k) for k in fields): raise ValueError('Point evidence is not an effective identity span')
        if (row['start_evidence_sha256'] not in trusted_evidence or row['end_evidence_sha256'] not in trusted_evidence
                or instant(row['effective_from'])>=instant(row['effective_to'])):
            raise ValueError('Untrusted or invalid identity endpoints')
    selected=[r for r in rows if instant(r['effective_from'])<=instant(at)<instant(r['effective_to'])]
    if len(selected)!=len({r['security_id'] for r in selected}) or len(selected)!=len({r['ticker'] for r in selected}):
        raise ValueError('Overlapping identity/class or ticker reuse')
    return {'status':'CERTIFIED_FOR_EVIDENCED_INSTANT','at':at,'rows':selected,'identity_sha256':digest(rows)}
