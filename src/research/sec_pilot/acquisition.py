"""Exact-document HTTP boundary and original-byte archive."""
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT/'docs/acceleration/sec_pilot_fixtures.json'
RAW = ROOT/'data/raw/sec_pilot'
MAX_BYTES = 64 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixtures():
    rows = json.loads(MANIFEST.read_bytes())['fixtures']
    if {r['accession'] for r in rows} != {'0000320193-19-000119', '0000320193-20-000096', '0001326801-20-000013'}:
        raise ValueError('Frozen fixture set changed')
    return rows


def identity():
    value = os.environ.get('EDGAR_IDENTITY')
    if not value and (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('EDGAR_IDENTITY='):
                value = line.split('=', 1)[1].strip().strip('"').strip("'")
    if not value or '@' not in value or '\n' in value or '\r' in value:
        raise ValueError('Local SEC identity unavailable; value is never logged')
    return value


class Boundary:
    def __init__(self, fixture):
        self.fixture = fixture
        self.base = fixture['index_url'].rsplit('/', 1)[0]+'/'
        a = fixture['accession']
        self.allowed = {self.base+a+suffix for suffix in ('-index.htm', '-index.html', '-index-headers.html', '.txt')}

    def add_document(self, name):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:htm|html|xml|xsd|txt)', name) or '..' in name:
            raise ValueError('Unsafe document name')
        url = self.base+name
        self.allowed.add(url)
        return url

    def check(self, url):
        p = urlsplit(url)
        if (p.scheme != 'https' or p.netloc != 'www.sec.gov' or p.query or p.fragment
                or '%' in p.path or url not in self.allowed):
            raise ValueError('URL outside exact SEC document allowlist')
        return url


class Archive:
    def __init__(self, root):
        from src.research.store import RawStore
        self.root = Path(root)
        self.receipts = RawStore(self.root)

    def body(self, accession, data):
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession):
            raise ValueError('Unsafe accession')
        digest = sha(data)
        target = self.root/accession/digest/'body.bin'
        if not target.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('Archive path escape')
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.partial-', dir=target.parent)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            try:
                os.link(temporary, target)  # Atomic, create-only; never replace another writer.
            except FileExistsError:
                if target.read_bytes() != data:
                    raise ValueError('Immutable content collision')
            if sha(target.read_bytes()) != digest or target.stat().st_size != len(data):
                raise ValueError('Original-byte integrity failure')
        finally:
            Path(temporary).unlink(missing_ok=True)
        return {'path': target.relative_to(self.root).as_posix(), 'sha256': digest, 'bytes': len(data)}

    def read(self, record):
        path = (self.root/record['path']).resolve()
        if not path.is_relative_to(self.root.resolve()): raise ValueError('Archive path escape')
        data = path.read_bytes()
        if sha(data) != record['sha256'] or len(data) != record['bytes']:
            raise ValueError('Archived body changed')
        return data


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


def http(url, request_identity):
    # No automatic redirect/proxy. Identity exists only in this request header.
    opener = build_opener(NoRedirect(), ProxyHandler({}))
    request = Request(url, headers={'User-Agent': request_identity, 'Accept-Encoding': 'identity'})
    try:
        response = opener.open(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        chunks = []; size = 0
        while True:
            try:
                part = response.read(1024*1024)
            except (Exception, KeyboardInterrupt) as error:
                error.partial_body = b''.join(chunks)+getattr(error, 'partial', b'')
                raise
            if not part: break
            size += len(part)
            if size > MAX_BYTES: raise ValueError('Response exceeds bounded byte ceiling')
            chunks.append(part)
        return response.status, dict(response.headers), b''.join(chunks)


class Acquire:
    def __init__(self, boundary, archive, *, transport=http, request_identity=None, sleep=time.sleep, clock=time.monotonic):
        self.boundary, self.archive, self.transport = boundary, archive, transport
        self.request_identity = request_identity
        self.sleep, self.clock, self.last = sleep, clock, None

    def get(self, url):
        self.boundary.check(url)
        accession = self.boundary.fixture['accession']
        original = url
        for attempt in range(3):
            # Each response, failure and redirect gets its own immutable attempt receipt.
            if self.last is not None: self.sleep(max(0, .5-(self.clock()-self.last)))
            self.last = self.clock()
            receipt = {'request_url': url, 'original_url': original, 'request_started_at_utc': now(), 'retrieved_at_utc': None,
                       'network': True, 'identity_header': 'REDACTED', 'attempt': attempt+1}
            key = f'{accession}/attempts/{uuid.uuid4().hex}.json'
            try:
                status, headers, data = self.transport(url, self.request_identity)
                receipt.update(status=status, final_url=url, retrieved_at_utc=now(), body=self.archive.body(accession, data),
                               headers={k.lower(): v for k, v in headers.items() if k.lower() in
                                        ('content-type', 'content-length', 'content-encoding', 'last-modified', 'retry-after')})
                self.archive.receipts.write(key, receipt)
                length = receipt['headers'].get('content-length')
                if length is not None and int(length) != len(data): raise ValueError('Incomplete response length')
                if receipt['headers'].get('content-encoding', 'identity').lower() != 'identity':
                    raise ValueError('Unexpected encoding; original bytes retained, decoding unsupported')
                if status == 200: return receipt
                if status in (301, 302, 303, 307, 308):
                    location = next((v for k, v in headers.items() if k.lower() == 'location'), '')
                    url = self.boundary.check(urljoin(url, location))
                elif status in (403, 429, 500, 502, 503, 504):
                    retry_after = receipt['headers'].get('retry-after')
                    if retry_after and (not retry_after.isdecimal() or int(retry_after) > 30):
                        raise ValueError('Retry-After exceeds bounded policy; stop acquisition')
                    self.sleep(max(2**attempt, int(retry_after or 0)))
                else: raise ValueError('SEC acquisition rejected; status '+str(status))
            except (Exception, KeyboardInterrupt) as error:
                if hasattr(error, 'partial_body'):
                    receipt['partial_body'] = self.archive.body(accession, error.partial_body)
                    receipt['complete'] = False
                # Record type only; exception strings can disclose identifying headers.
                self.archive.receipts.write(f'{accession}/errors/{uuid.uuid4().hex}.json',
                                             dict(receipt, error_type=type(error).__name__))
                raise
        raise ValueError('Persistent SEC restriction or retry ceiling; stop acquisition')
