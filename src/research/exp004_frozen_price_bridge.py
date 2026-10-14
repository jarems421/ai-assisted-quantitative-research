"""Attach price fields to immutable EXP004 identities; never re-identify rows."""
import argparse,hashlib,json
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.exp004_supplement_qa import verify_refs,opens
from src.research.exp004_vpg_identity import verdict,OLD_ID

DOCS=ROOT/'docs/acceleration'
OUT=ROOT/'data/raw/EXP004/frozen_price_bridge_v001'
CERT=DOCS/'exp004_frozen_price_bridge_v001.json'


def execution_open_coverage(required,enriched):
    """Source-row enrichment does not imply that every required session exists."""
    import duckdb
    db=duckdb.connect();db.register('required',required);db.register('enriched',enriched)
    q='FROM required r LEFT JOIN enriched e ON r.security_id=e.security_id AND r.ticker=e.ticker AND CAST(r.day AS DATE)=e.day'
    n=db.execute('SELECT COUNT(*) FROM required').fetchone()[0]
    missing=db.execute('SELECT COUNT(*) '+q+' WHERE e.security_id IS NULL OR e.openingPrice IS NULL').fetchone()[0]
    valid=db.execute('SELECT COUNT(*) '+q+' WHERE isfinite(e.openingPrice) AND e.openingPrice>0').fetchone()[0]
    db.close()
    return {'required':n,'valid':valid,'missing':missing,'invalid':n-missing-valid,
            'status':'PASS_OPEN_FIELD_COVERAGE_ONLY' if valid==n else 'LOCAL_EXECUTION_INPUTS_BLOCKED'}


def enrich(frozen,source):
    import duckdb
    db=duckdb.connect();db.register('frozen',frozen);db.register('source',source)
    count=lambda sql:db.execute(sql).fetchone()[0]
    n=count('SELECT COUNT(*) FROM frozen');keys=count('SELECT COUNT(*) FROM (SELECT DISTINCT ticker,day FROM frozen)')
    duplicate=count('SELECT COALESCE(SUM(n-1),0) FROM (SELECT COUNT(*) n FROM source GROUP BY ticker,day HAVING COUNT(*)>1)')
    missing=count('SELECT COUNT(*) FROM frozen f WHERE NOT EXISTS(SELECT 1 FROM source s WHERE f.ticker=s.ticker AND f.day=s.day)')
    ambiguous=count('SELECT COUNT(*) FROM frozen f JOIN (SELECT ticker,day FROM source GROUP BY ticker,day HAVING COUNT(*)>1) s USING(ticker,day)')
    extra=count('SELECT COUNT(*) FROM source s WHERE NOT EXISTS(SELECT 1 FROM frozen f WHERE f.ticker=s.ticker AND f.day=s.day)')
    q={'frozen_rows':n,'unique_frozen_ticker_day_keys':keys,'source_rows':source.num_rows,'missing':missing,'duplicate_source_excess_rows':duplicate,'ambiguous_frozen_rows':ambiguous,'unused_source_extras':extra}
    if missing or duplicate or ambiguous or keys!=n:
        db.close();return dict(q,status='PRICE_KEY_AMBIGUITY_BLOCKED'),None
    mismatches=count('SELECT COUNT(*) FROM frozen f JOIN source s USING(ticker,day) WHERE f.unadjustedClose IS DISTINCT FROM s.unadjustedClose')
    enriched=db.execute('SELECT f.ticker,f.day,f.security_id,s.openingPrice,f.unadjustedClose FROM frozen f JOIN source s USING(ticker,day) ORDER BY f.security_id,f.day').fetch_arrow_table()
    stats=opens(enriched.column('openingPrice').to_pylist());db.close()
    q.update(enriched_rows=enriched.num_rows,matched_source_rows=enriched.num_rows,CLOSE_mismatches=mismatches,OPEN=stats,frozen_identity_rewritten=False)
    status='PASS_FROZEN_PRICE_ENRICHMENT' if not mismatches and not stats['missing'] and not stats['invalid'] else 'SOURCE_RECONCILIATION_BLOCKED' if mismatches else 'LOCAL_EXECUTION_INPUTS_BLOCKED'
    return dict(q,status=status),enriched


def build():
    import pyarrow.parquet as pq
    from src.research.prepare_exp004 import verify_freeze
    from src.research.exp004_vpg_source import OUT as identity
    verify_freeze()
    path=ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json'
    frozen=json.loads(path.read_bytes());refs=json.loads((identity/'part_hashes.json').read_bytes())
    current=pq.read_table(verify_refs(refs)).to_pylist()
    for r in current:
        for k,v in r.items():
            if hasattr(v,'isoformat'):r[k]=v.isoformat()
    identity_result=verdict(frozen,current)
    if identity_result['verdict']!='VPG_SAME_SECURITY_NAMESPACE_DRIFT':raise ValueError('VPG_IDENTITY_BLOCKED')
    summary=json.loads((DOCS/'exp004_supplement_source_review.json').read_bytes());q0=summary['reconciliation']
    old=pq.read_table(verify_refs(q0['old_parts']));new=pq.read_table(verify_refs(q0['new_parts']))
    qa,enriched=enrich(old,new)
    if qa['status']!='PASS_FROZEN_PRICE_ENRICHMENT':raise ValueError(qa['status'])
    vpg=enriched.filter(__import__('pyarrow').compute.equal(enriched['ticker'],'VPG'))
    if vpg.num_rows!=62 or set(vpg['security_id'].to_pylist())!={OLD_ID}:raise ValueError('VPG frozen identity not preserved')
    value={'version':'EXP004_frozen_price_bridge_v001','status':'PASS_SOURCE_BRIDGE_ONLY','VPG':identity_result,
           'frozen_identity_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'current_identity_parts':refs,
           'current_identity_rows':current,'identity_comparison_scope':'2010-07-07 through2020-12-31; exact archived CIK/CS/share-class-FIGI/span; earlier when-issued records kept separate',
           'namespace_evidence':'Current base ID belongs to different-CIK VSHw ex-distribution when-issued span ending2010-07-06; VPG same CIK/FIGI/full in-scope span now has #2. No affected-period overlap. This establishes collision at the observed record level; undocumented internal publisher generation algorithm is not claimed.',
           'price_enrichment_key':['ticker','day'],'first_quarter':qa,'frozen_parts':q0['old_parts'],'completed_source_parts':q0['new_parts'],
           'first_quarter_uniqueness_basis':'Archived supplemental SQL has ordinary non-aggregating inner join with no DISTINCT. At least one CS span exists for every frozen ticker/day. Any duplicate OHLC row at a required key would propagate into that result; observed one result row per required key therefore certifies required-key uniqueness at that archived query snapshot. Global OHLC extras outside the CS join were not measured.',
           'VPG_rows':62,'VPG_retained_ID':OLD_ID,'VPG_OPEN':opens(vpg['openingPrice'].to_pylist()),
           'statement':'CURRENT SECURITY_SEGMENTS IS NOT USED TO REWRITE FROZEN EXP004 IDENTITY','economic_freeze_changed':False,
           'openingPrice_unit_basis':'NOT_YET_CERTIFIED_FOR_RAW_SHARE_LEDGER','performance_executed':False,'Validation_accesses':0,'Test_accesses':0}
    put(CERT,value);put(OUT/'first_quarter_enrichment_qa.json',qa)
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
    if a.build:print(build()['status'])
