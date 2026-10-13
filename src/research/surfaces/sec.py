"""Original SEC filing-index population; no ticker/Item/outcome filtering."""
import re,hashlib
from src.research.surfaces.base import EvidenceTier,ProviderResult
from src.research.spec import digest

class SECSurfaceAdapter:
    surface_id='SEC';evidence_tier=EvidenceTier.PRIMARY_INDEX_OR_METADATA
    def access_contract(self):return {'identity':'local EDGAR_IDENTITY','source':'official filing indexes','tier':self.evidence_tier.value}
    def probe_manifest(self):return {'start':'2020-01-01','end':'2020-03-31','forms':['8-K','8-K/A'],'sample':'First four source-order original8-K entries per month'}
    def capabilities(self):return {'denominator':'DECLARED_INDEX_NOT_LEGAL_OBLIGATION','timing':'PUBLIC_TIMESTAMP_UNKNOWN','revisions':'PAC_DELETION_UNKNOWN_UNLESS_EVIDENCED','identity':'CIK_NOT_SECURITY'}
    def enumerate(self,body,source_sha256):
        rows=[];seen=set()
        for line_no,line in enumerate(body.decode('latin-1').splitlines(),1):
            parts=line.split('|')
            if len(parts)!=5 or parts[2] not in ('8-K','8-K/A'):continue
            cik,name,form,day,path=parts
            if not '2020-01-01'<=day<='2020-03-31':raise ValueError('Index row outside fixed source period')
            match=re.fullmatch(r'edgar/data/(\d+)/(\d{10}-\d{2}-\d{6})\.txt',path)
            if not match or int(match[1])!=int(cik):raise ValueError('Accession/file identity mismatch')
            accession=match[2]
            if accession in seen:raise ValueError('Duplicate accession')
            seen.add(accession)
            rows.append({'accession':accession,'issuer_cik':cik,'filed_name':name,'form':form,'filing_date':day,'source_filename':path,
             'source_line':line_no,'source_index_sha256':source_sha256,'amendment_relationship':'UNKNOWN' if form=='8-K/A' else 'NOT_APPLICABLE',
             'PAC_deletion_status':'UNKNOWN','original_body_status':'UNTESTED','public_availability_status':'PUBLIC_TIMESTAMP_UNKNOWN','acceptance_candidates':None})
        if not rows:raise ValueError('No denominator established, never fabricate zero')
        return rows
    def sample(self,rows):
        return [r for month in ('2020-01','2020-02','2020-03') for r in [x for x in rows if x['form']=='8-K' and x['filing_date'].startswith(month)][:4]]
    def normalize_probe(self,rows):raise ValueError('Explicit archived receipt required for SEC result construction')

def item_semantics(body,item='2.02'):
    text=body.decode('utf-8',errors='replace')
    # SGML item headers directly declare categories; avoid generic substring absence.
    headers=re.findall(r'^ITEM INFORMATION:\s*(.+)$',text,re.M)
    label={'2.02':'Results of Operations and Financial Condition','5.02':'Departure of Directors or Certain Officers','2.03':'Creation of a Direct Financial Obligation'}.get(item)
    if label and any(label.lower() in h.lower() for h in headers):return {'status':'PRESENT_SOURCE_HEADER','item':item,'headers':headers,'source_sha256':hashlib.sha256(body).hexdigest()}
    if headers:return {'status':'NOT_DECLARED_IN_COMPLETE_HEADER','item':item,'headers':headers,'absence_scope':'This submission header only; not zero corporate activity'}
    return {'status':'UNKNOWN','item':item,'reason':'No complete declared item header; textual proximity alone is insufficient'}
