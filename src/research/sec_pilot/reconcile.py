"""Exact canonical records across isolated pilot SQLite, Parquet and DuckDB."""
import json
from pathlib import Path
import sqlite3
from src.research.sec_pilot.parsing import canonical, digest

TABLES = ('source_documents', 'filing_versions', 'facts', 'text_sections', 'security_bindings', 'asof_views')


def records(snapshot, job):
    return {'source_documents': [{'role': role, **record} for role, record in sorted(job['sources'].items())],
            'filing_versions': [{k: v for k, v in snapshot.items() if k not in ('facts', 'text_sections', 'security_bindings', 'asof_views')}],
            **{name: snapshot[name] for name in TABLES[2:]}}


def exact(expected, observed):
    if sorted(expected) != sorted(observed): raise ValueError('Cross-store exact key/value mismatch')


def reconcile(snapshot, job, destination):
    import pyarrow as pa
    import pyarrow.parquet as pq
    import duckdb
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=True)
    data = records(snapshot, job); db = sqlite3.connect(destination/'manifest.sqlite')
    result = {}
    try:
        for name in TABLES:
            expected = sorted((digest(row), canonical(row).decode()) for row in data[name])
            if len({k for k, _ in expected}) != len(expected): raise ValueError('Duplicate canonical record')
            db.execute(f'CREATE TABLE IF NOT EXISTS {name} (key TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            old = db.execute(f'SELECT key,payload FROM {name} ORDER BY key').fetchall()
            if old: exact(expected, old)
            else:
                db.executemany(f'INSERT INTO {name} VALUES (?,?)', expected); db.commit()
            parquet = destination/(name+'.parquet')
            if not parquet.exists():
                table = pa.table({'key': pa.array([r[0] for r in expected], type=pa.string()),
                                  'payload': pa.array([r[1] for r in expected], type=pa.string())})
                pq.write_table(table, parquet)
            arrow_rows = [(r['key'], r['payload']) for r in pq.read_table(parquet).to_pylist()]
            with duckdb.connect() as connection:
                sql_rows = connection.execute('SELECT key,payload FROM read_parquet(?) ORDER BY key', [str(parquet)]).fetchall()
            exact(expected, arrow_rows); exact(expected, sql_rows)
            exact(expected, db.execute(f'SELECT key,payload FROM {name} ORDER BY key').fetchall())
            result[name] = {'status': 'PASS', 'rows': len(expected), 'canonical_records_sha256': digest(expected)}
    finally: db.close()
    return result
