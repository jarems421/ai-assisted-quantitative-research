"""Single-worker, explicit-boundary source receipts; no credential values logged."""
import hashlib
import json
import os
from pathlib import Path
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler

from src.research.sec_pilot.acquisition import Archive, NoRedirect, ROOT, identity, now
from src.research.sec_pilot.parsing import canonical, digest

RAW = ROOT / 'data/raw/phase3c_v001'
DOCS = ROOT / 'docs/acceleration'
PYTHON = ROOT / '.research/sec-pilot-venv/Scripts/python.exe'


def secret(name):
    value = os.environ.get(name)
    if value: return value
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            key, sep, val = line.partition('=')
            if sep and key.strip() == name:
                return val.strip().strip('"').strip("'") or None
    return None


def put(path, value):
    """Exclusive canonical immutable version; caller supplies content-addressed path."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    body = canonical(value)
    if path.exists():
        if path.read_bytes() != body: raise ValueError('Immutable record conflict')
    else:
        with path.open('xb') as f: f.write(body)


class SourceHTTP:
    LIMITS = {'SEC': (600, .55), 'OpenFIGI': (15, 3), 'Tiingo': (120, .2), 'FMP': (3, 1), 'Documentation': (15, .55)}

    def __init__(self, allowed, *, transport=None, root=RAW, sleep=time.sleep, clock=time.monotonic):
        self.allowed = set(allowed); self.root = Path(root); self.archive = Archive(self.root)
        self.transport = transport or self._transport; self.sleep = sleep; self.clock = clock
        self.last = {}; self.cache = self.root / 'requests'

    @staticmethod
    def _transport(url, headers, payload):
        request = Request(url, data=payload, headers=headers)
        try: response = build_opener(NoRedirect(), ProxyHandler({})).open(request, timeout=40)
        except HTTPError as error: response = error
        with response:
            chunks=[]; size=0
            while True:
                try: part=response.read(min(1024*1024,64*1024*1024+1-size))
                except Exception as error:
                    error.partial_body=b''.join(chunks)+getattr(error,'partial',b'')
                    raise
                if not part: break
                chunks.append(part); size+=len(part)
                if size>64*1024*1024:
                    error=ValueError('Source byte ceiling'); error.partial_body=b''.join(chunks)
                    error.reason_code='LOCAL_RESPONSE_BYTE_CEILING'; raise error
            data=b''.join(chunks)
            return response.status, dict(response.headers), data, response.geturl()

    def allow(self, url):
        p = urlsplit(url)
        if p.scheme != 'https' or p.fragment or p.username or p.password:
            raise ValueError('Unsafe source URL')
        self.allowed.add(url)

    def _stop(self, provider, value):
        put(self.root / 'stops' / provider / (digest(value) + '.json'), value)
        legacy = self.root / (provider + '_stop.json')
        if not legacy.exists(): put(legacy, value)

    def fetch(self, provider, url, *, payload=None, headers=None):
        if url not in self.allowed or provider not in self.LIMITS:
            raise ValueError('Source request outside allowlist')
        key = digest({'provider': provider, 'url': url, 'payload': payload})
        cached = self.cache / (key + '.json')
        if cached.exists():
            receipt = json.loads(cached.read_bytes()); body = self.archive.read(receipt['body'])
            return receipt, body
        stop = self.root / (provider + '_stop.json')
        versions = list((self.root / 'stops' / provider).glob('*.json'))
        review_path = self.root / (provider + '_stop_review_v001.json')
        reviewed_hash = json.loads(review_path.read_bytes()).get('reviewed_stop_sha256') if review_path.exists() else None
        if any(digest(json.loads(p.read_bytes())) != reviewed_hash for p in versions):
            raise ValueError('New persisted provider stop; no automatic retry')
        if stop.exists():
            resolution = self.root / (provider + '_stop_review_v001.json')
            previous = json.loads(stop.read_bytes())
            review = json.loads(resolution.read_bytes()) if resolution.exists() else {}
            allowed_alternative = url in review.get('allowed_alternative_urls', [])
            if provider == 'SEC' and review.get('mode') == 'INDEX_HEADER_PRIMARY_INSTANCE_ONLY':
                p = urlsplit(url)
                allowed_alternative = (not p.path.endswith('.txt') and
                    (p.netloc == 'www.sec.gov' and p.path.startswith('/Archives/edgar/data/') or
                     p.netloc == 'data.sec.gov' and p.path.startswith('/submissions/CIK')))
            if (review.get('reviewed_stop_sha256') != digest(previous) or key == previous.get('request_key')
                    or not allowed_alternative):
                raise ValueError('Persisted provider stop; no automatic retry')
        limit, gap = self.LIMITS[provider]
        attempts = self.root / 'attempts' / provider; attempts.mkdir(parents=True, exist_ok=True)
        request_headers = {'User-Agent': identity() if provider == 'SEC' else 'ResearchSourceCertification/1.0',
                           'Accept-Encoding': 'identity', **(headers or {})}
        for attempt in range(3):
            if len(list(attempts.glob('*.json'))) >= limit: raise ValueError('Provider request ceiling')
            if provider == 'Tiingo':
                prior = [json.loads(p.read_bytes()) for p in attempts.glob('*.json')]
                from datetime import datetime, timezone
                at = datetime.now(timezone.utc).timestamp()
                starts = {datetime.fromisoformat(r['request_started_at_utc']).timestamp() for r in prior}
                if sum(s > at-3600 for s in starts) >= 50 or sum(s > at-86400 for s in starts) >= 1000:
                    raise ValueError('Persisted Tiingo free request quota reached')
            if provider in self.last:
                delay = max(0, gap - (self.clock() - self.last[provider]))
                # Tiingo pacing needs external orchestration; never block >60s.
                if delay > 60: raise ValueError('Provider pacing pending; resume after recorded deadline')
                self.sleep(delay)
            self.last[provider] = self.clock()
            receipt = {'provider': provider, 'url': url, 'request_key': key, 'payload_sha256': digest(payload),
                       'request_started_at_utc': now(), 'attempt': attempt + 1,
                       'request_headers': 'REDACTED_AUTHENTICATION_AND_CONTACT', 'network': True}
            try:
                status, received_headers, data, final = self.transport(url, request_headers, canonical(payload) if payload is not None else None)
                # Archive every response immediately, before interpreting body/status/redirect.
                # Zero accession is an archive implementation bucket, NOT a filing identity.
                receipt.update(status=status, final_url=final, retrieved_at_utc=now(),
                               archive_bucket_role='NON_FILING_SOURCE_BLOB',
                               body=self.archive.body('0000000000-00-000000', data),
                               headers={k.lower(): v for k, v in received_headers.items() if k.lower() in
                                        ('content-type', 'content-length', 'content-encoding', 'retry-after',
                                         'ratelimit-limit', 'ratelimit-remaining', 'ratelimit-reset')})
                put(attempts / (uuid.uuid4().hex + '.json'), receipt)
                if final != url: raise ValueError('Undocumented redirect')
                if receipt['headers'].get('content-encoding', 'identity').lower() != 'identity':
                    raise ValueError('Unexpected content encoding')
                length = receipt['headers'].get('content-length')
                if length and int(length) != len(data): raise ValueError('Incomplete source response')
                if status == 200:
                    put(cached, receipt); return receipt, data
                if status not in (403, 429, 500, 502, 503, 504):
                    put(cached, receipt); return receipt, data
                retry = receipt['headers'].get('retry-after', '0')
                if not retry.isdecimal() or int(retry) > 30: raise ValueError('Retry backoff outside bounded policy')
                self.sleep(max(2 ** attempt, int(retry)))
            except Exception as error:
                receipt['error_type'] = type(error).__name__
                if hasattr(error, 'partial_body'):
                    receipt['partial_body'] = self.archive.body('0000000000-00-000000', error.partial_body)
                    receipt['complete'] = False
                if hasattr(error, 'reason_code'): receipt['reason_code'] = error.reason_code
                put(attempts / (uuid.uuid4().hex + '.json'), receipt)
                self._stop(provider, {'provider': provider, 'time': now(), 'error_type': type(error).__name__, 'request_key': key})
                raise ValueError('Source acquisition stopped; private error receipt retained') from None
        self._stop(provider, {'provider': provider, 'time': now(), 'reason': 'PERSISTENT_ACCESS_FAILURE', 'request_key': key})
        raise ValueError('Persistent source failure; provider stopped')


def freeze_cohort(rows, *, metadata_hashes):
    keys = [r['case_key'] for r in rows]
    if len(keys) != len(set(keys)) or len(keys) > 60: raise ValueError('Invalid unique cohort ceiling')
    ordered = sorted(rows, key=lambda r: r['case_key'])
    if sum(r['revenue_candidate'] for r in ordered) < 30: raise ValueError('Revenue cohort breadth')
    body = {'version': 'phase3c_cohort_v001', 'cases': ordered, 'metadata_hashes': sorted(set(metadata_hashes)),
            'selection': 'Fixed metadata-only named stress frame; stable case-key order; no market data or return selection',
            'category_evidence': 'Discovery metadata labels are hypotheses unless a dated primary source is linked',
            'source_cutoff': '2026-10-12', 'revenue_filing_selection': 'First original 10-K for each fiscal end year 2018,2019,2020, filed by2021-12-31',
            'price_bounds': ['2019-01-01', '2020-12-31'], 'frozen_before_price': True}
    value = dict(body, cohort_sha256=digest(body), frozen_at_utc=now())
    path = DOCS / 'phase3c_pilot_cohort.json'
    if path.exists():
        old = json.loads(path.read_bytes())
        if old['cohort_sha256'] != digest(body): raise ValueError('Frozen cohort changed')
        return old
    put(path, value); put(RAW / 'cohort_freeze.json', value)
    return value


def require_cohort(cohort):
    body = {k: v for k, v in cohort.items() if k not in ('cohort_sha256', 'frozen_at_utc')}
    if digest(body) != cohort.get('cohort_sha256') or not cohort.get('frozen_before_price'):
        raise ValueError('Frozen-before-price evidence absent or changed')
    private = RAW / 'cohort_freeze.json'
    if not private.exists() or json.loads(private.read_bytes()) != cohort:
        raise ValueError('Independent cohort freeze receipt absent')
