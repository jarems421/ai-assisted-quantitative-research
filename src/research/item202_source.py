"""Development-only SEC census keys and structured-label presence; no outcomes."""
from datetime import date, datetime
import re


def enumerate_index(body, year, quarter, source_sha256):
    if year not in range(2015,2021) or quarter not in (1,2,3,4):
        raise ValueError('Development source boundary')
    rows=[]
    for n,line in enumerate(body.decode('latin-1').splitlines(),1):
        fields=line.split('|')
        if len(fields)!=5 or fields[2] not in ('8-K','8-K/A'):continue
        cik,name,form,day,path=fields;d=date.fromisoformat(day)
        if d.year!=year or (d.month-1)//3+1!=quarter:raise ValueError('Index date outside frozen quarter')
        m=re.fullmatch(r'edgar/data/(\d+)/(\d{10}-\d{2}-\d{6})\.txt',path)
        if not m or int(m[1])!=int(cik):raise ValueError('Source identity/path conflict')
        rows.append({'CIK':cik,'filed_name':name,'accession':m[2],'form':form,'filing_date':day,
                     'source_path':path,'source_line':n,'source_index_sha256':source_sha256,
                     'PAC_version_state':'UNKNOWN','original_body_state':'NOT_QUERIED',
                     'Item202_classification':'UNKNOWN_NOT_CLASSIFIED','amendment_state':'UNRESOLVED' if form=='8-K/A' else 'ORIGINAL'})
    if not rows:raise ValueError('No defensible nonempty source frame')
    return rows


def metadata_labels(columns, census_accessions):
    """Scope by date/accession before reading form/items/acceptance; missing is unknown."""
    rows=[]
    for i,acc in enumerate(columns.get('accessionNumber',[])):
        day=columns['filingDate'][i]
        if not '2015-01-01'<=day<='2020-12-31' or acc not in census_accessions:continue
        def value(key):
            a=columns.get(key);return a[i] if a is not None and i<len(a) else None
        item=value('items');clock=value('acceptanceDateTime')
        # Empty/missing labels are not a certified negative item declaration.
        rows.append({'accession':acc,'filing_date':day,'form':value('form'),'items_raw':item,
                     'primary_document':value('primaryDocument'),
                     'acceptance_representation':clock,'label_status':'DECLARED_METADATA_LABEL' if item else 'UNKNOWN_METADATA_LABEL_MISSING',
                     'Item202':'PRESENT_METADATA' if item and '2.02' in re.split(r'\s*,\s*',item) else 'NOT_DECLARED_METADATA' if item else 'UNKNOWN'})
    return rows


def metadata_clock_conformance(iso_value, source_utc_candidates):
    """Check the declared ISO clock against originals; never guess a repair mode."""
    try:
        at=datetime.fromisoformat(iso_value.replace('Z','+00:00'))
        candidates=[datetime.fromisoformat(x) for x in source_utc_candidates]
        if at.tzinfo is None or not candidates or any(x.tzinfo is None for x in candidates):
            raise ValueError('Unclassified clock')
        return 'MATCH_SOURCE_CANDIDATE' if at in candidates else 'CONFLICTING_SOURCE_CLOCK_REPRESENTATION'
    except (ValueError,TypeError,AttributeError):
        return 'UNKNOWN_UNSUPPORTED_CLOCK_REPRESENTATION'
