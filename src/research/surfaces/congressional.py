"""Checksum-verified Python adapter for upstream camelCase Parquet snapshots."""
import hashlib,re
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from src.research.surfaces.base import EvidenceTier,ProviderResult
from src.research.sec_pilot.provenance import instant
from src.research.spec import digest

TABLES=('political_filings','political_trades','political_trade_events')
def scalar(value):
    if isinstance(value,datetime):
        # Upstream Date/TIMESTAMP writes UTC epoch values without Arrow timezone metadata.
        return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.astimezone(timezone.utc).isoformat()
    return value.isoformat() if hasattr(value,'isoformat') else value
def normalize(row):
    return {re.sub(r'(?<!^)(?=[A-Z])','_',k).lower():scalar(v) for k,v in row.items()}

class CongressionalDisclosuresAdapter:
    surface_id='CONGRESS';evidence_tier=EvidenceTier.AUDITED_EXTERNAL_DERIVED
    def __init__(self,manifest,root,*,revision,retrieved_at):
        if manifest.get('dataset')!='austin-starks/congressional-stock-trades' or manifest.get('schemaVersion') not in (1,2):raise ValueError('Unsupported dataset/schema')
        instant(manifest['generatedAt']);instant(retrieved_at)
        self.manifest=manifest;self.root=Path(root).resolve();self.revision=revision;self.retrieved_at=retrieved_at
        if not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('Snapshot revision must be immutable commit')
        for table in TABLES:
            if table not in manifest['tables']:raise ValueError('Required table missing')
    def access_contract(self):return {'tier':self.evidence_tier.value,'snapshot_sha256':digest(self.manifest),'revision':self.revision,'generatedAt':self.manifest['generatedAt']}
    def probe_manifest(self):return self.access_contract()
    def capabilities(self):return {'timing':'UPSTREAM_MODELED_EOD_NOT_OBSERVED_PUBLIC','identity':'PRINTED_RESOLVED_NOT_SECURITY_SPANS','denominator':'DECLARED_SNAPSHOT_NOT_ALL_DISCLOSURES','original_gate':False}
    def files(self,table,year):
        if table not in TABLES:raise ValueError('Only disclosure tables allowed')
        files=[f for m in self.manifest['tables'][table]['manifests'] if m['year']==year for f in m['files']]
        if not files:raise ValueError('Year unavailable, not zero')
        seen=set()
        for f in files:
            name=f['publicPath'];p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or not name.startswith('data/'+table+'/') or name in seen:raise ValueError('Unsafe/repeated snapshot path')
            if not re.fullmatch('[a-f0-9]{64}',f['sha256']) or type(f['size']) is not int or f['size']<0:raise ValueError('Missing integrity metadata')
            seen.add(name)
        return files
    def verify(self,file):
        path=(self.root/file['publicPath']).resolve()
        if not path.is_relative_to(self.root):raise ValueError('Snapshot path escape')
        data=path.read_bytes()
        if len(data)!=file['size'] or hashlib.sha256(data).hexdigest()!=file['sha256']:raise ValueError('Snapshot integrity failed')
        return path
    def table(self,table,year):
        import pyarrow.parquet as pq
        rows=[]
        for f in self.files(table,year):rows.extend(normalize(r) for r in pq.read_table(self.verify(f)).to_pylist())
        return rows
    def events_known_at(self,events,timestamp,trades=()):
        at=instant(timestamp);out=[];keys=set()
        originals={(r['chamber'],r['doc_id'],r['row_index']):r for r in trades}
        for r in events:
            key=(r['event_id'],r['version'])
            if key in keys:raise ValueError('Duplicate event version')
            keys.add(key)
            first=instant(r['first_available_at']);version_at=instant(r['available_at']);end=instant(r['superseded_at']) if r.get('superseded_at') else None
            if first>version_at or end is not None and end<version_at:raise ValueError('Contradictory version chronology')
            # firstAvailableAt is event origin, not disclosure of this amended version.
            if max(first,version_at)<=at and (end is None or at<end):
                original=originals.get((r['chamber'],r['source_doc_id'],r['source_row_index']))
                row=dict(r,printed_ticker=original.get('printed_ticker') if original else None,
                 resolved_ticker=original.get('resolved_ticker') if original else None,resolution_status=original.get('resolution_status') if original else 'UNAVAILABLE_ORIGINAL_TRADE',
                 upstream_ticker=r.get('ticker'),availability_status='UPSTREAM_MODELED_EOD_NOT_OBSERVED_PUBLIC',evidence_tier=self.evidence_tier.value)
                out.append(row)
        if len({r['event_id'] for r in out})!=len(out):raise ValueError('Overlapping event versions')
        return sorted(out,key=lambda r:(r['first_available_at'],r['event_id'],r['version']))
    def normalize_probe(self,rows):
        return ProviderResult(self.surface_id,self.evidence_tier,'https://huggingface.co/datasets/'+self.manifest['dataset'],digest(self.manifest),'snapshot_schema_v'+str(self.manifest['schemaVersion']),self.revision,self.retrieved_at,None,'UPSTREAM_MODELED_EOD','VERSIONED_EVENT_ROWS','EXTERNAL_SNAPSHOT_ONLY',{},self.access_contract(),tuple(rows))
