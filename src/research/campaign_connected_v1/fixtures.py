"""Fictional records and in-memory transport ONLY. No transport/runtime selection.

These fixture scopes, stop attestations and custody claims are never real human acts.
Every artifact is created under a new standalone SYNTHETIC rehearsal directory.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.research.campaign_v1 import native as N, records as R
from src.research.source_v1 import contracts as K, stops, store as S

HOST = 'documents.example.org'
URL = 'https://' + HOST + '/synthetic/allocation.txt'
ROBOTS = 'https://' + HOST + '/robots.txt'
OWNER = 'Jordan Fictional-Owner'
TEXT = (b'SYNTHETIC REGISTER. Fictional allocation: 12 inspection shifts per week to customer C-1.\n'
        b'Independent invoice totals: UNKNOWN. No real measurement or source.\n')
QUOTE = 'Fictional allocation: 12 inspection shifts per week to customer C-1.'


class Clock:
    def __init__(self):
        self.time, self.seconds = datetime(2026, 10, 26, 12, tzinfo=timezone.utc), 0.0

    def now(self):
        self.time += timedelta(microseconds=1)
        return self.time.isoformat(timespec='microseconds')

    def ticks(self):
        return self.seconds

    def sleep(self, seconds):
        self.seconds += seconds
        self.time += timedelta(seconds=seconds)


class Response:
    status = 200

    def __init__(self, body):
        self.body, self.position = body, 0
        self.headers = [('Content-Type', 'text/plain; charset=utf-8'), ('Content-Length', str(len(body)))]

    def read(self, size):
        data = self.body[self.position:self.position + size]
        self.position += len(data)
        return data

    def close(self):
        pass


class FakeTransport:
    """No sockets, DNS or library HTTP calls; exactly two known in-memory replies."""
    def __init__(self):
        self.opened, self.resolved = [], []

    def resolve(self, host):
        R.need(host == HOST, 'unexpected fictional host')
        self.resolved.append(host)
        return ['93.184.216.34']

    def open(self, url, host, address, timeout):
        R.need(host == HOST and address == '93.184.216.34' and url in (URL, ROBOTS), 'unexpected fictional request')
        self.opened.append(url)
        return Response(b'User-agent: *\nAllow: /\n' if url == ROBOTS else TEXT)


def put(root, name, value):
    path = Path(root) / name
    S.write_new(path, value)
    return {'path': str(path), 'sha256': N.sha(R.read(path))}


def request(root, base, branch, campaign_id, clock):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    registry = put(root, 'registry.json', {'schema': 'QUARRY_ROUTE_REGISTRY_V001', 'routes': [{
        'id': 'SYN-REGISTER', 'version': '1', 'locator': URL, 'publisher': 'FICTIONAL publisher',
        'expected_fields': ['allocation', 'independent invoice totals'], 'question': 'SYNTHETIC allocation question',
        'access_restrictions': [], 'originality_claim': 'ORIGINAL', 'expected_source_identity': 'register-1',
        'expected_asset': 'allocation register', 'availability_uncertainties': ['Fictional fixture only.'], 'stops': []}]})
    quarry = put(root, 'quarry-scope.json', {'schema': 'QUARRY_ACQUISITION_SCOPE_V001', 'route_ids': ['SYN-REGISTER'],
        'exact_urls': [URL], 'allowed_hosts': [HOST], 'request_ceiling': 2, 'total_byte_ceiling': 8192,
        'per_response_byte_ceiling': 4096, 'minimum_interval_seconds': 2, 'timeout_seconds': 10})
    negative = put(root, 'historical-stop.json', {'status': 'STOPPED', 'url': 'https://stopped.example.net/x',
                                               'note': 'SYNTHETIC unrelated stop; never lifted'})
    attestation = put(root, 'synthetic-attestation.json', {'schema': K.ATTESTATION, 'attested_by': OWNER,
        'attested_at': '2026-10-26T08:00:00+00:00', 'inputs': [negative['sha256']], 'resolutions': [], 'documented_stops': [],
        'statement': 'I reviewed the listed stop records and the reports available to me. Unclear scopes are recorded host-level.'})
    snapshot = stops.build([negative['path']], base, attestation=attestation['path'], clock=clock.now)
    scope = put(root, 'synthetic-scope.json', {'schema': K.SCOPE, 'owner': OWNER,
        'decided_at': '2026-10-26T09:00:00+00:00', 'valid_until': '2026-10-27T09:00:00+00:00',
        'campaign_id': campaign_id, 'branch_id': branch['branch_id'], 'card_sha256': branch['card_sha256'],
        'implementation_sha256': S.implementation(), 'quarry_registry': registry, 'quarry_scope': quarry,
        'operations': ['RETRIEVE_EXACT_URL'], 'transmission': 'NONE', 'robots_policy': 'ROBOTS_TXT_REQUIRED',
        'access_terms_reviewed': 'SYNTHETIC fixture scope only; no real terms review or authority.',
        'attempt_ceiling': 1, 'total_requests': 2, 'total_bytes': 8192})
    value = {'schema': K.REQUEST, 'campaign_id': campaign_id, 'branch_id': branch['branch_id'],
        'subject': {'archive_sha256': N.sha(R.read(Path(branch['archive']) / 'scout.jsonl')),
                    'card_id': branch['idea_id'], 'card_version': branch['version'], 'card_sha256': branch['card_sha256']},
        'request_id': 'REQ-SYNTHETIC-CONNECTED', 'attempt_id': 'SRC-SYNTHETIC-CONNECTED',
        'question': {'text': 'SYNTHETIC allocation and missing independent outcome', 'requirements': [{
            'id': 'ER-1', 'role': 'PREDICTOR', 'quantity': 'allocation', 'unit': 'shifts/week', 'denominator': 'UNKNOWN',
            'population': 'UNKNOWN', 'period': 'UNKNOWN', 'join': 'UNKNOWN'}]},
        'authority': {'scope': scope, 'operations': ['RETRIEVE_EXACT_URL'], 'transmission': 'NONE',
            'tier_a': {'exact_urls': [URL], 'hosts': [HOST]}, 'tier_b_classes': [], 'host_amendments': []},
        'stops': {'snapshot': {'path': snapshot['path'], 'sha256': snapshot['sha256']}},
        'resources': {'campaign_allocation_ref': None, 'reservation': {'requests': 2, 'total_bytes': 8192,
            'per_response_bytes': 4096, 'wall_seconds': 60, 'searches': 0, 'model_calls': 0, 'metered_micro_usd': 0}},
        'caller_ref': 'SYNTHETIC_NOT_RESEARCH_NO_REAL_AUTHORITY'}
    return put(root, 'request.json', value)['path']


def claims(root, ctx, x):
    return put(root, 'synthetic-claims.json', {'schema': x.CLAIMS, 'attested_by': OWNER,
        'attested_at': '2026-10-26T13:00:00+00:00', 'attempt_id': ctx['attempt_id'], 'receipt_sha256': ctx['receipt_sha256'],
        'body_sha256': ctx['receipt']['body_sha256'], 'title': 'SYNTHETIC fictional allocation register',
        'source_identity_claim': 'register-1', 'asset_claim': 'allocation register', 'source_version_claim': 'fictional-1',
        'historical_availability_claim': 'UNKNOWN', 'data_classification': 'SYNTHETIC',
        'limitations': ['Fictional fixture; no real evidence, human judgment or economic result.'],
        'missing_fields': ['independent invoice totals', 'measurement population and period'], 'statement': x.STATEMENT})['path']


def inspection(root):
    start = TEXT.index(QUOTE.encode())
    return put(root, 'synthetic-inspection.json', {'schema': 'QUARRY_INSPECTION_V001', 'mode': 'ORIGINAL_UTF8',
        'extraction_method_claim': 'SYNTHETIC exact UTF8 fixture; no human inspection', 'excerpts': [{
            'id': 'SYN_ALLOCATION', 'location': 'fictional register line 1', 'start_byte': start,
            'end_byte': start + len(QUOTE.encode()), 'quote': QUOTE}]})['path']
