"""Exact key/close reconciliation; no returns, NAV or selection metrics."""
from pathlib import Path
import hashlib,json,math
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.exp004_supplement import PLAN,OUT


def reconcile_frames(old,new):
    import duckdb
    db=duckdb.connect();db.register('old',old);db.register('new',new)
    key='security_id,ticker,day'
    o=db.execute('SELECT COUNT(*) FROM old').fetchone()[0];n=db.execute('SELECT COUNT(*) FROM new').fetchone()[0]
    missing=db.execute(f'SELECT COUNT(*) FROM (SELECT {key} FROM old EXCEPT ALL SELECT {key} FROM new)').fetchone()[0]
    extra=db.execute(f'SELECT COUNT(*) FROM (SELECT {key} FROM new EXCEPT ALL SELECT {key} FROM old)').fetchone()[0]
    duplicates={name:db.execute(f'SELECT COALESCE(SUM(n-1),0) FROM (SELECT COUNT(*) n FROM {name} GROUP BY {key} HAVING COUNT(*)>1)').fetchone()[0] for name in ('old','new')}
    # Compare CLOSE only for structurally pairable keys. Key substitutions must
    # not be incorrectly reported as changed prices.
    db.execute(f'CREATE TEMP VIEW paired_keys AS SELECT {key} FROM (SELECT {key},COUNT(*) n FROM old GROUP BY {key}) o JOIN (SELECT {key},COUNT(*) n FROM new GROUP BY {key}) n USING({key}) WHERE o.n=n.n')
    db.execute(f'CREATE TEMP VIEW old_paired AS SELECT old.* FROM old JOIN paired_keys USING({key})')
    db.execute(f'CREATE TEMP VIEW new_paired AS SELECT new.* FROM new JOIN paired_keys USING({key})')
    projection=key+',unadjustedClose'
    close_missing=db.execute(f'SELECT COUNT(*) FROM (SELECT {projection} FROM old_paired EXCEPT ALL SELECT {projection} FROM new_paired)').fetchone()[0]
    close_extra=db.execute(f'SELECT COUNT(*) FROM (SELECT {projection} FROM new_paired EXCEPT ALL SELECT {projection} FROM old_paired)').fetchone()[0]
    close_compared=db.execute('SELECT COUNT(*) FROM old_paired').fetchone()[0]
    db.close()
    return {'old_rows':o,'new_rows':n,'matched_keys':o-missing,'missing_keys':missing,'extra_keys':extra,
        'duplicate_keys':duplicates,'close_row_mismatches':max(close_missing,close_extra),
        'close_compared_rows':close_compared,'old_rows_unpairable_for_close':o-close_compared,
        'close_comparison':'Exact stored numeric equality; no tolerance; NULL matches NULL; multiset comparison preserves repeated rows',
        'status':'PASS_EXACT_KEYS_AND_CLOSE' if not (missing or extra or close_missing or close_extra) and duplicates['old']==duplicates['new'] else 'SOURCE_RECONCILIATION_BLOCKED'}


def verify_refs(refs):
    for ref in refs:
        path=ROOT/ref['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('Immutable source part changed')
    return [str(ROOT/r['path']) for r in refs]


def quarter(name):
    import pyarrow.parquet as pq
    plan=json.loads(PLAN.read_bytes());r=next(r for r in plan['requests'] if r['name']==name)
    newrefs=json.loads((OUT/name/'part_hashes.json').read_bytes())
    old=pq.read_table(verify_refs(r['old_part_hashes']));new=pq.read_table(verify_refs(newrefs))
    result=reconcile_frames(old,new)
    dates=new.column('day').to_pylist()
    if any(not '2013-12-31'<=d.isoformat()<='2020-12-31' for d in dates):raise ValueError('Post-cutoff price input')
    result.update(name=name,request_sha256=digest(r['request']),new_parts=newrefs,old_parts=r['old_part_hashes'])
    put(OUT/name/'reconciliation_v002.json',result)
    return result


def opens(values):
    missing=sum(v is None for v in values);invalid=sum(v is not None and (not math.isfinite(v) or v<=0) for v in values)
    return {'required':len(values),'valid':len(values)-missing-invalid,'missing':missing,'invalid':invalid}
