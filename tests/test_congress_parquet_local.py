import hashlib,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
from src.research.surfaces.congressional import CongressionalDisclosuresAdapter,TABLES

class CongressionalParquetTests(unittest.TestCase):
    def test_real_arrow_naive_utc_conversion_and_duckdb_version_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stamp=datetime(2020,1,10);later=datetime(2020,2,10)
            events=[{'eventId':'e','version':1,'chamber':'house','sourceDocId':'d','sourceRowIndex':1,'sourceUrl':'https://disclosures-clerk.house.gov/d','transactionDate':'2020-01-01','firstAvailableAt':stamp,'availableAt':stamp,'supersededAt':later,'ticker':'UP'},
             {'eventId':'e','version':2,'chamber':'house','sourceDocId':'d','sourceRowIndex':2,'sourceUrl':'https://disclosures-clerk.house.gov/d','transactionDate':'2020-01-01','firstAvailableAt':stamp,'availableAt':later,'supersededAt':None,'ticker':'UP'}]
            records={'political_filings':[{'docId':'d'}],'political_trades':[{'docId':'d','rowIndex':1,'chamber':'house','printedTicker':'OLD','resolvedTicker':None,'resolutionStatus':'unresolved'},{'docId':'d','rowIndex':2,'chamber':'house','printedTicker':'OLD','resolvedTicker':'CURRENT','resolutionStatus':'resolved'}],'political_trade_events':events}
            manifest={'dataset':'austin-starks/congressional-stock-trades','schemaVersion':2,'generatedAt':'2026-10-13T00:00:00Z','tables':{}}
            for table,rows in records.items():
                p=root/'data'/table/'2020.parquet';p.parent.mkdir(parents=True);pq.write_table(pa.Table.from_pylist(rows),p);body=p.read_bytes()
                manifest['tables'][table]={'manifests':[{'year':2020,'files':[{'publicPath':p.relative_to(root).as_posix(),'size':len(body),'sha256':hashlib.sha256(body).hexdigest()}]}]}
            a=CongressionalDisclosuresAdapter(manifest,root,revision='a'*40,retrieved_at='2026-10-13T00:00:00Z');rows=a.table('political_trade_events',2020)
            out=a.events_known_at(rows,'2020-01-20T00:00:00Z',a.table('political_trades',2020));self.assertEqual(out[0]['version'],1);self.assertIsNone(out[0]['resolved_ticker'])
            with duckdb.connect() as db:
                result=db.execute('SELECT version FROM read_parquet(?) WHERE "availableAt" <= ? AND ("supersededAt" IS NULL OR ? < "supersededAt")',[str(root/'data/political_trade_events/2020.parquet'),datetime(2020,1,20),datetime(2020,1,20)]).fetchall()
            self.assertEqual(result,[(out[0]['version'],)])
