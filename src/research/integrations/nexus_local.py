"""Optional installed SDK HTML projection; literal bytes only, no client surface."""
import hashlib,importlib.metadata
from src.research.sec_pilot.parsing import offline
from src.research.spec import digest

def prepare_html(body):
    if not isinstance(body,bytes):raise TypeError('Original archived bytes required; URLs/clients are not accepted')
    with offline():
        from nexustrade.scanned_table import prepare_web_pages
        if importlib.metadata.version('nexustrade')!='1.42.0':raise ValueError('Pinned installed helper required')
        prepared=prepare_web_pages({'original':body})['original']
    return {'source_sha256':hashlib.sha256(body).hexdigest(),'input_sha256':hashlib.sha256(body).hexdigest(),'output_sha256':digest(prepared),'upstream_version':'1.42.0','evidence_tier':'PRIMARY_DERIVED','projection':prepared,'absence_certified':False,'remote_execution':False}
