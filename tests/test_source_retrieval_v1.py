"""Source Retrieval V001 offline regressions: fictional hosts, injected fake transports, denied network/process.

No test resolves a name, opens a socket or starts a process; passing fixtures establish no source truth,
authority or research progress.
"""
import copy
import io as pyio
import json
import socket
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from src.research.spec import canonical, digest
from src.research.source_v1 import __main__ as CLI, contracts as C, retrieve as R, stops as T, store as S, transport as N

HOST = 'documents.example.org'
URL1, URL2 = f'https://{HOST}/orders/1.pdf', f'https://{HOST}/orders/2.html'
ROBOTS = f'https://{HOST}/robots.txt'
PUBLIC = '93.184.216.34'
OWNER = 'Jordan Fictional-Owner'
ALLOW = b'User-agent: *\nAllow: /\n'


class Clock:
    def __init__(self):
        self.t, self.mono, self.sleeps = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc), 0.0, []

    def now(self):
        self.t += timedelta(microseconds=1)
        return self.t.isoformat(timespec='microseconds')

    def ticks(self):
        return self.mono

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.mono += seconds
        self.t += timedelta(seconds=seconds)


class FakeResponse:
    def __init__(self, spec, clock):
        self.status, self.spec, self.clock, self.pos, self.reads = spec.get('status', 200), spec, clock, 0, 0
        body = spec.get('body', b'')
        self.body = body
        self.headers = list(spec.get('headers', [('Content-Type', 'application/octet-stream')]))
        if spec.get('declared', True):
            self.headers.append(('Content-Length', str(spec.get('length', len(body)))))

    def read(self, size):
        self.reads += 1
        self.clock.mono += self.spec.get('slow', 0)
        if self.spec.get('interrupt_after') is not None and self.pos >= self.spec['interrupt_after']:
            raise KeyboardInterrupt
        if self.spec.get('fail_after') is not None and self.pos >= self.spec['fail_after']:
            raise ConnectionResetError('peer said something private')
        chunk = self.body[self.pos:self.pos + min(size, self.spec.get('chunk', 4096))]
        self.pos += len(chunk)
        return chunk

    def close(self):
        pass


class FakeTransport:
    def __init__(self, clock, responses, dns=None):
        self.clock, self.responses, self.dns = clock, responses, dns or {}
        self.resolved, self.opened, self.objects = [], [], []

    def resolve(self, host):
        self.resolved.append(host)
        self.clock.mono += getattr(self, 'dns_seconds', 0)  # A slow resolver.
        value = self.dns.get(host, [PUBLIC])
        if isinstance(value, BaseException):
            raise value
        return value

    def open(self, url, host, address, timeout):
        self.opened.append((url, host, address, timeout))
        spec = self.responses[url]
        if isinstance(spec, BaseException):
            raise spec
        response = FakeResponse(spec, self.clock)
        self.objects.append(response)
        return response


def denied(*args, **kwargs):
    raise AssertionError('offline test attempted a real network or process operation')


class SourceRetrievalTests(unittest.TestCase):
    def setUp(self):
        for target in ('socket.getaddrinfo', 'socket.create_connection', 'subprocess.Popen'):
            p = patch(target, side_effect=denied)
            p.start()
            self.addCleanup(p.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / 'records'
        self.clock = Clock()
        self.urls = [URL1, URL2]
        self.scope_changes = {}
        self.quarry_changes = {}
        self.build()

    # ---- fixtures -------------------------------------------------------------------------------------------
    def put(self, name, value):
        data = value if isinstance(value, bytes) else canonical(value)
        (self.root / name).write_bytes(data)
        return {'path': str(self.root / name), 'sha256': S.sha(data)}

    def build(self, attest=True, stop_records=(), resolutions=None):
        routes = [{'id': f'R{i}', 'version': '1', 'locator': u, 'publisher': 'FICTIONAL publisher', 'expected_fields': ['quantity'],
                   'question': 'fictional question', 'access_restrictions': [], 'originality_claim': 'ORIGINAL',
                   'expected_source_identity': f'doc-{i}', 'expected_asset': 'F1', 'availability_uncertainties': ['Fictional'],
                   'stops': []} for i, u in enumerate(self.urls)]
        self.registry = self.put('registry.json', {'schema': 'QUARRY_ROUTE_REGISTRY_V001', 'routes': routes})
        hosts = sorted({C.host_of(u) for u in self.urls})
        quarry = {'schema': 'QUARRY_ACQUISITION_SCOPE_V001', 'route_ids': [r['id'] for r in routes], 'exact_urls': list(self.urls),
                  'allowed_hosts': hosts, 'request_ceiling': 8, 'total_byte_ceiling': 1048576,
                  'per_response_byte_ceiling': 262144, 'minimum_interval_seconds': 2, 'timeout_seconds': 10, **self.quarry_changes}
        self.quarry = self.put('quarry-scope.json', quarry)
        records = [self.put(f'stop-{i}.json', r) for i, r in enumerate(stop_records or [{'status': 'STOPPED', 'url': 'https://stopped.example.net/x'}])]
        attestation = None
        if attest:
            attestation = self.put('attestation.json', {
                'schema': C.ATTESTATION, 'attested_by': OWNER, 'attested_at': '2026-10-26T08:00:00+00:00',
                'inputs': sorted(r['sha256'] for r in records), 'resolutions': resolutions or [], 'documented_stops': [],
                'statement': 'I reviewed the listed stop records and the reports available to me. Unclear scopes are recorded host-level.'})
        snap = T.build([r['path'] for r in records], self.base, attestation=attestation and attestation['path'], clock=self.clock.now)
        self.snapshot = {'path': snap['path'], 'sha256': snap['sha256']}
        scope = {'schema': C.SCOPE, 'owner': OWNER, 'decided_at': '2026-10-26T09:00:00+00:00',
                 'valid_until': '2026-10-27T09:00:00+00:00', 'campaign_id': 'CMP-T', 'branch_id': 'B1', 'card_sha256': 'c' * 64,
                 'implementation_sha256': S.implementation(), 'quarry_registry': self.registry, 'quarry_scope': self.quarry,
                 'operations': ['RETRIEVE_EXACT_URL'], 'transmission': 'NONE', 'robots_policy': 'ROBOTS_TXT_REQUIRED',
                 'access_terms_reviewed': 'Fictional terms reviewed by the fictional owner', 'attempt_ceiling': 4,
                 'total_requests': 64, 'total_bytes': 8388608, **self.scope_changes}
        self.scope = self.put('scope.json', scope)

    def request(self, attempt='A1', change=None):
        value = {'schema': C.REQUEST, 'campaign_id': 'CMP-T', 'branch_id': 'B1',
                 'subject': {'archive_sha256': 'a' * 64, 'card_id': 'IDEA-FICTIONAL', 'card_version': 1, 'card_sha256': 'c' * 64},
                 'request_id': 'REQ-1', 'attempt_id': attempt,
                 'question': {'text': 'Fictional decisive question', 'requirements': [
                     {'id': 'ER-1', 'role': 'PREDICTOR', 'quantity': 'fictional quantity', 'unit': 'USD', 'denominator': 'UNKNOWN',
                      'population': 'UNKNOWN', 'period': 'UNKNOWN', 'join': 'UNKNOWN'}]},
                 'authority': {'scope': self.scope, 'operations': ['RETRIEVE_EXACT_URL'], 'transmission': 'NONE',
                               'tier_a': {'exact_urls': list(self.urls), 'hosts': sorted({C.host_of(u) for u in self.urls})},
                               'tier_b_classes': [], 'host_amendments': []},
                 'stops': {'snapshot': self.snapshot},
                 'resources': {'campaign_allocation_ref': None, 'reservation': {
                     'requests': 6, 'total_bytes': 1048576, 'per_response_bytes': 262144, 'wall_seconds': 600,
                     'searches': 0, 'model_calls': 0, 'metered_micro_usd': 0}},
                 'caller_ref': 'campaign-opaque-ref'}
        if change:
            change(value)
        return self.put(f'request-{attempt}.json', value)['path']

    def transport(self, responses=None, dns=None):
        default = {ROBOTS: {'body': ALLOW, 'headers': [('Content-Type', 'text/plain')]},
                   URL1: {'body': b'%PDF-1.4 fictional original \x00\xff bytes'}, URL2: {'body': b'<html>fictional</html>'}}
        default.update(responses or {})
        return FakeTransport(self.clock, default, dns)

    def dispatch(self, request, transport):
        return R.run(request, self.base, transport=transport, clock=self.clock.now, ticks=self.clock.ticks, sleep=self.clock.sleep)

    def attempt(self, attempt='A1'):
        return S.records(self.base) / 'attempts' / attempt

    def ledger(self):
        return S.Journal(S.records(self.base) / 'ledger.jsonl').load()

    def assert_not_started(self, result, code, transport):
        self.assertEqual(result['status'], 'NOT_STARTED')
        self.assertTrue(result['reason'].startswith(code), result['reason'])
        self.assertEqual((transport.resolved, transport.opened), ([], []))
        self.assertFalse(any(e['type'] == 'ATTEMPT_RESERVED' and e['record']['attempt_id'] == result['attempt_id'] for e in self.ledger()))
        self.assertFalse((S.records(self.base) / 'dispatch.lock').exists())

    # ---- behaviour ------------------------------------------------------------------------------------------
    def test_complete_attempt_retains_original_bytes_with_receipts_and_custody_handoff(self):
        t = self.transport()
        result = self.dispatch(self.request(), t)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual([o[0] for o in t.opened], [ROBOTS, URL1, URL2])
        self.assertTrue(all(o[2] == PUBLIC and o[1] == HOST for o in t.opened))
        a = self.attempt()
        for item in result['custody_handoff']:
            body = (a / item['body_path']).read_bytes()
            self.assertEqual(S.sha(body), item['body_sha256'])
            self.assertEqual(body, t.responses[item['requested_url']]['body'])
        self.assertEqual([h['quarry_route_id'] for h in result['custody_handoff']], ['R0', 'R1'])
        receipt = json.loads((a / 'receipts' / '002.json').read_bytes())
        self.assertEqual((receipt['termination'], receipt['complete'], receipt['coverage'], receipt['connected_address']),
                         ('COMPLETE', True, 'COMPLETE', PUBLIC))
        self.assertEqual(result['consumption']['requests'], {'at_least': 3, 'exact': 3})
        self.assertEqual(result['consumption']['metered_micro_usd'], {'reserved': 0, 'estimated': 0, 'actual': 0})
        self.assertEqual((result['exactly_once'], result['authorises'], result['interrupted']), (False, [], False))
        self.assertEqual(len(self.clock.sleeps), 2)  # Serial pacing between the three requests.
        self.assertTrue(all(1.99 < s <= 2 for s in self.clock.sleeps))
        journal = [e['type'] for e in S.Journal(a / 'journal.jsonl').load()]
        self.assertEqual(journal[0], 'ATTEMPT_CLAIMED')
        self.assertEqual(journal[-1], 'ATTEMPT_FINISHED')
        self.assertLess(journal.index('REQUEST_CLAIMED'), journal.index('REQUEST_FINISHED'))
        self.assertEqual(R.status(self.base, 'A1')['state'], 'COMPLETE')
        self.assertFalse((a / 'attempt.lock').exists() or (S.records(self.base) / 'dispatch.lock').exists())
        self.assertEqual(sorted(p.name for p in (a / 'inputs').iterdir()),
                         ['quarry-registry.json', 'quarry-scope.json', 'scope.json', 'stop-snapshot.json'])

    def test_private_and_non_public_addresses_are_refused_before_any_connection(self):
        for i, answer in enumerate((['10.0.0.5'], ['127.0.0.1'], ['169.254.169.254'], ['::1'], ['fc00::1'], ['100.64.0.1'],
                                    ['::ffff:10.0.0.1'], ['224.0.0.1'], ['0.0.0.0'], [PUBLIC, '192.168.1.1'], ['not-an-address'])):
            with self.subTest(answer=answer):
                self.base = self.root / f'records-{i}'
                self.build()
                t = self.transport(dns={HOST: answer})
                result = self.dispatch(self.request(), t)
                self.assertEqual((result['status'], result['reason']), ('STOPPED', 'ROBOTS_ADDRESS_REFUSED'))
                self.assertEqual(t.opened, [])
                self.assertEqual([(f['scope'], f['host']) for f in result['stop_findings']], [('HOST', HOST)])
                again = self.transport()
                self.assert_not_started(self.dispatch(self.request('A2'), again), 'STOPPED_SOURCE', again)

    def test_redirects_are_refused_never_followed(self):
        t = self.transport({URL1: {'status': 302, 'headers': [('Location', 'https://elsewhere.example.net/x')], 'body': b'moved'}})
        result = self.dispatch(self.request(), t)
        self.assertEqual((result['status'], result['reason']), ('STOPPED', 'REDIRECT_REFUSED'))
        self.assertEqual([o[0] for o in t.opened], [ROBOTS, URL1])
        self.assertEqual(result['not_attempted'], [URL2])
        receipt = json.loads((self.attempt() / 'receipts' / '002.json').read_bytes())
        self.assertEqual(receipt['headers_selected']['location'], 'https://elsewhere.example.net/x')
        self.assertEqual([(f['scope'], f['route']) for f in result['stop_findings']], [('ROUTE', URL1)])
        self.assertEqual(result['custody_handoff'], [])

    def test_dns_failure_stops_without_connection_or_stop_finding(self):
        for i, answer in enumerate((socket.gaierror(8, 'private resolver detail'), [])):
            with self.subTest(answer=answer):
                self.base = self.root / f'records-{i}'
                self.build()
                t = self.transport(dns={HOST: answer})
                result = self.dispatch(self.request(), t)
                self.assertEqual((result['status'], result['reason'], t.opened, result['stop_findings']),
                                 ('STOPPED', 'ROBOTS_DNS_FAILED', [], []))
                receipt = (self.attempt() / 'receipts' / '001.json').read_text()
                self.assertNotIn('private resolver detail', receipt)

    def test_stopped_hosts_and_routes_refuse_before_claim(self):
        self.build(stop_records=[{'note': 'closed', 'receipt': {'url': f'https://{HOST}/anything'}}])
        t = self.transport()
        result = self.dispatch(self.request(), t)
        self.assert_not_started(result, 'STOPPED_SOURCE', t)
        snapshot = json.loads(Path(self.snapshot['path']).read_bytes())
        self.assertNotIn('closed', json.dumps(snapshot['entries']))  # Private stop text is never copied.
        record = {'status': 'STOPPED', 'reason': 'route closed; no host named'}
        self.build(stop_records=[record], resolutions=[{'input_sha256': S.sha(canonical(record)), 'hosts': [],
                                                        'routes': [URL2], 'task_scoped_reason': None}])
        t = self.transport()
        result = self.dispatch(self.request('A2'), t)
        self.assert_not_started(result, 'STOPPED_SOURCE', t)

    def test_403_and_429_create_host_stops_and_end_the_attempt(self):
        for i, (status, term) in enumerate(((403, 'ACCESS_DENIED'), (401, 'ACCESS_DENIED'), (429, 'RATE_LIMITED'), (500, 'UNEXPECTED_RESPONSE'))):
            with self.subTest(status=status):
                self.base = self.root / f'records-{i}'
                self.build()
                t = self.transport({URL1: {'status': status, 'body': b'denied page kept as error bytes'}})
                result = self.dispatch(self.request(), t)
                self.assertEqual((result['status'], result['reason'], result['not_attempted']), ('STOPPED', term, [URL2]))
                self.assertEqual([(f['scope'], f['host'], f['reason']) for f in result['stop_findings']], [('HOST', HOST, term)])
                self.assertEqual(result['custody_handoff'], [])
                self.assertEqual([r['http_status'] for r in result['retained']], [200, status])
                again = self.transport()
                self.assert_not_started(self.dispatch(self.request('A2'), again), 'STOPPED_SOURCE', again)

    def test_404_is_unavailable_with_a_route_stop(self):
        result = self.dispatch(self.request(), self.transport({URL1: {'status': 404, 'body': b'not here'}}))
        self.assertEqual((result['status'], result['reason']), ('UNAVAILABLE', 'NOT_FOUND'))
        self.assertEqual([(f['scope'], f['route']) for f in result['stop_findings']], [('ROUTE', URL1)])

    def test_oversized_responses_stop_at_the_ceiling(self):
        big = b'x' * 300000
        t = self.transport({URL1: {'body': big}})
        result = self.dispatch(self.request(), t)
        self.assertEqual(result['status'], 'PARTIAL')
        receipt = json.loads((self.attempt() / 'receipts' / '002.json').read_bytes())
        self.assertEqual((receipt['termination'], receipt['stopped_by'], receipt['bytes_received'], receipt['body_path']),
                         ('SIZE_STOP', 'DECLARED_SIZE', 0, None))
        self.assertEqual(t.objects[1].reads, 0)  # Metadata-only stop: no body byte read.
        self.base = self.root / 'records-streamed'
        self.build()
        t = self.transport({URL1: {'body': big, 'declared': False, 'chunk': 65536}})
        result = self.dispatch(self.request(), t)
        self.assertEqual(result['status'], 'PARTIAL')
        prefix = (self.attempt() / 'raw' / '002.body').read_bytes()
        self.assertEqual(prefix, big[:262144])
        handoff = result['custody_handoff'][0]
        self.assertEqual((handoff['coverage'], handoff['bytes']), ('PREFIX', 262144))
        self.assertEqual(result['custody_handoff'][1]['coverage'], 'COMPLETE')

    def test_partial_transfer_is_unknown_and_stops_the_host(self):
        for i, spec in enumerate(({'body': b'y' * 40, 'length': 100}, {'body': b'z' * 5000, 'fail_after': 1024, 'chunk': 512})):
            with self.subTest(spec=sorted(spec)):
                self.base = self.root / f'records-{i}'
                self.build()
                result = self.dispatch(self.request(), self.transport({URL1: spec}))
                self.assertEqual((result['status'], result['reason']), ('UNKNOWN', 'TRANSPORT_FAILED'))
                receipt = (self.attempt() / 'receipts' / '002.json').read_text()
                self.assertIn('INCOMPLETE_BODY' if i == 0 else 'ConnectionResetError', receipt)
                self.assertNotIn('peer said something private', receipt)
                self.assertEqual([(f['scope'], f['host']) for f in result['stop_findings']], [('HOST', HOST)])
                self.assertEqual(result['custody_handoff'], [])

    def test_time_ceiling_and_byte_budget_are_enforced(self):
        result = self.dispatch(self.request(), self.transport({URL1: {'body': b's' * 20000, 'chunk': 1000, 'slow': 1}}))
        self.assertEqual(result['status'], 'PARTIAL')
        receipt = json.loads((self.attempt() / 'receipts' / '002.json').read_bytes())
        self.assertEqual(receipt['termination'], 'TIME_STOP')
        self.assertLess(receipt['bytes_received'], 20000)
        self.base = self.root / 'records-budget'
        self.build()
        def small(value):
            value['resources']['reservation'].update(total_bytes=40, per_response_bytes=40)
        result = self.dispatch(self.request(change=small), self.transport({URL1: {'body': b'b' * 40, 'declared': False}}))
        self.assertEqual((result['status'], result['reason'], result['not_attempted']), ('STOPPED', 'BUDGET', [URL2]))
        self.assertLessEqual(result['consumption']['bytes']['exact'], 40)

    def test_duplicate_attempts_and_concurrent_dispatch_are_refused(self):
        request = self.request()
        self.dispatch(request, self.transport())
        before = (self.attempt() / 'result.json').read_bytes(), (S.records(self.base) / 'ledger.jsonl').read_bytes()
        t = self.transport()
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_ATTEMPT'):
            self.dispatch(request, t)
        self.assertEqual(before, ((self.attempt() / 'result.json').read_bytes(), (S.records(self.base) / 'ledger.jsonl').read_bytes()))
        self.assertEqual((t.resolved, t.opened), ([], []))
        S.acquire(S.records(self.base) / 'dispatch.lock', {'attempt_id': 'OTHER'})
        with self.assertRaisesRegex(ValueError, 'DISPATCH_LOCKED'):
            self.dispatch(self.request('A2'), t)
        self.assertFalse(self.attempt('A2').exists())

    def test_interrupted_attempt_keeps_locks_and_finalises_record_only(self):
        t = self.transport({URL1: {'body': b'i' * 5000, 'chunk': 1000, 'interrupt_after': 2000}})
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch(self.request(), t)
        status = R.status(self.base, 'A1')
        self.assertEqual(status['state'], 'INTERRUPTED')
        self.assertIsNotNone(status['attempt_lock'])
        self.assertEqual(status['dispatch_lock']['attempt_id'], 'A1')
        with self.assertRaisesRegex(ValueError, 'DISPATCH_LOCKED'):
            self.dispatch(self.request('A2'), self.transport())
        with self.assertRaisesRegex(ValueError, 'confirm'):
            R.finalise_interrupted(self.base, 'A1', no_attempt_running=False)
        opened = len(t.opened)
        result = R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        self.assertEqual(len(t.opened), opened)  # Nothing re-sent.
        self.assertEqual((result['status'], result['interrupted']), ('UNKNOWN', True))
        self.assertEqual([u['url'] for u in result['unfinished_requests']], [URL1])
        self.assertEqual(result['consumption']['requests'], {'at_least': 2, 'exact': None})
        self.assertGreaterEqual(result['consumption']['bytes']['at_least'], 2000)
        self.assertEqual([(f['scope'], f['reason']) for f in result['stop_findings']], [('HOST', 'INTERRUPTED_REQUEST')])
        self.assertEqual(R.status(self.base, 'A1')['state'], 'UNKNOWN')
        self.assertTrue((self.attempt() / 'attempt.lock').exists())  # Never removed by software.
        self.assertEqual(R.finalise_interrupted(self.base, 'A1', no_attempt_running=True), result)  # Idempotent.

    def test_altered_receipts_bodies_results_and_journals_are_detected(self):
        self.dispatch(self.request(), self.transport())
        a = self.attempt()
        for target, code in (('receipts/002.json', 'RECEIPT_ALTERED'), ('raw/002.body', 'BODY_ALTERED'),
                             ('result.json', 'RESULT_ALTERED'), ('journal.jsonl', 'journal chain changed')):
            with self.subTest(target=target):
                path = a / target
                original = path.read_bytes()
                path.write_bytes(original.replace(b'1', b'2', 1) if target != 'raw/002.body' else original + b'!')
                status = R.status(self.base, 'A1')
                self.assertEqual(status['state'], 'INCONSISTENT')
                self.assertTrue(any(code in p for p in status['problems']), status['problems'])
                out = pyio.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(CLI.main(['--base', str(self.base), 'result', 'A1']), 1)
                path.write_bytes(original)
        self.assertEqual(R.status(self.base, 'A1')['state'], 'COMPLETE')

    def test_scope_violations_are_refused_before_claim(self):
        def url(value):
            value['authority']['tier_a'] = {'exact_urls': [URL1], 'hosts': [HOST]}
        def ceiling(value):
            value['resources']['reservation']['requests'] = 9
        cases = [('url outside scope', url, 'SCOPE_VIOLATION'), ('above Quarry ceiling', ceiling, 'RESERVATION_EXCEEDS_SCOPE')]
        for i, (name, change, code) in enumerate(cases):
            with self.subTest(name):
                t = self.transport()
                self.assert_not_started(self.dispatch(self.request(f'V{i}', change), t), code, t)
        scope_cases = [('other card', {'card_sha256': 'd' * 64}, 'SCOPE_BINDING'),
                       ('code drift', {'implementation_sha256': 'e' * 64}, 'IMPLEMENTATION_DRIFT'),
                       ('expired', {'valid_until': '2026-10-26T10:00:00+00:00'}, 'SCOPE_NOT_VALID_NOW'),
                       ('assistant owner', {'owner': 'Claude (assistant)'}, 'SCOPE_INVALID'),
                       ('placeholder owner', {'owner': 'OWNER'}, 'SCOPE_INVALID')]
        for i, (name, changes, code) in enumerate(scope_cases):
            with self.subTest(name):
                self.scope_changes = changes
                self.build()
                t = self.transport()
                self.assert_not_started(self.dispatch(self.request(f'S{i}'), t), code, t)
        self.scope_changes = {}
        self.build()
        request = self.request('H1')
        Path(self.scope['path']).write_bytes(Path(self.scope['path']).read_bytes() + b' ')
        t = self.transport()
        self.assert_not_started(self.dispatch(request, t), 'SCOPE_CHANGED', t)
        self.build(attest=False)
        t = self.transport()
        self.assert_not_started(self.dispatch(self.request('N1'), t), 'STOP_ATTESTATION_MISSING', t)
        for bad in ('http://documents.example.org/x', 'https://127.0.0.1/x', 'https://documents.example.org:8443/x', ROBOTS):
            with self.subTest(bad=bad):
                self.urls = [bad]
                with self.assertRaises(ValueError):
                    R.run(self.request('X1', lambda v: v['authority'].update(tier_a={'exact_urls': [bad], 'hosts': [HOST]})), self.base,
                          transport=self.transport())
                self.assertFalse(self.attempt('X1').exists())

    def test_quarry_route_stops_and_cumulative_scope_reservations_hold(self):
        self.scope_changes = {'attempt_ceiling': 1}
        self.build()
        self.dispatch(self.request('C1'), self.transport())
        t = self.transport()
        self.assert_not_started(self.dispatch(self.request('C2'), t), 'SCOPE_ATTEMPTS_EXHAUSTED', t)
        self.scope_changes = {}
        self.base = self.root / 'records-quarry'
        self.build()
        registry = json.loads(Path(self.registry['path']).read_bytes())
        registry['routes'][0]['stops'] = [{'id': 'S1', 'scope': 'host', 'reason': 'fictional', 'citation': 'fictional', 'citation_sha256': 'UNKNOWN'}]
        self.registry = self.put('registry.json', registry)
        scope = json.loads(Path(self.scope['path']).read_bytes())
        scope['quarry_registry'] = self.registry
        self.scope = self.put('scope.json', scope)
        t = self.transport()
        self.assert_not_started(self.dispatch(self.request('Q1'), t), 'QUARRY_RESTRICTION', t)

    def test_stop_snapshot_requires_named_human_attestation_and_is_additive(self):
        url_record = self.put('url-stop.json', {'status': 'STOPPED', 'receipt': {'requested_url': 'https://blocked.example.net/a'}})
        bare = self.put('bare-stop.json', {'status': 'STOPPED', 'reason': 'secret internal note'})
        first = T.build([url_record['path'], bare['path']], self.base, clock=self.clock.now)
        self.assertEqual((first['status'], first['unresolved_inputs']), ('ATTESTATION_REQUIRED', [bare['sha256']]))
        def attest(**changes):
            value = {'schema': C.ATTESTATION, 'attested_by': OWNER, 'attested_at': '2026-10-26T08:00:00+00:00',
                     'inputs': [url_record['sha256'], bare['sha256']],
                     'resolutions': [{'input_sha256': bare['sha256'], 'hosts': ['other.example.net'], 'routes': [], 'task_scoped_reason': None}],
                     'documented_stops': [{'host': 'reports.example.net', 'route': None, 'reason': 'Documented 403', 'citation': 'fictional report'}],
                     'statement': 'I reviewed the listed stop records and the reports available to me. Unclear scopes are recorded host-level.'}
            value.update(changes)
            return self.put('attest.json', value)['path']
        for changes, message in (({'attested_by': 'Codex'}, 'named human'), ({'inputs': [url_record['sha256']]}, 'exactly'),
                                 ({'resolutions': []}, None)):
            with self.subTest(changes=sorted(changes)):
                if message:
                    with self.assertRaisesRegex(ValueError, message):
                        T.build([url_record['path'], bare['path']], self.base, attestation=attest(**changes), clock=self.clock.now)
                else:
                    out = T.build([url_record['path'], bare['path']], self.base, attestation=attest(**changes), clock=self.clock.now)
                    self.assertEqual(out['status'], 'ATTESTATION_REQUIRED')
        done = T.build([url_record['path'], bare['path']], self.base, attestation=attest(), previous=first['path'], clock=self.clock.now)
        self.assertEqual(done['status'], 'COMPLETE')
        snapshot = json.loads(Path(done['path']).read_bytes())
        hosts = {(e['host'], e['origin']) for e in snapshot['entries']}
        self.assertEqual(hosts, {('blocked.example.net', 'MACHINE_RECORD'), ('other.example.net', 'HUMAN_ATTESTED'),
                                 ('reports.example.net', 'HUMAN_ATTESTED')})
        self.assertNotIn('secret internal note', Path(done['path']).read_text())
        self.assertEqual(snapshot['previous_snapshot_sha256'], first['sha256'])
        with self.assertRaisesRegex(ValueError, 'STOP_ATTESTATION_MISSING'):
            T.snapshot({'path': first['path'], 'sha256': first['sha256']})

    def test_robots_policy_is_checked_before_targets(self):
        cases = [(b'User-agent: *\nDisallow: /orders/\n', 200, 'STOPPED', 'ROBOTS_DISALLOWED', [ROBOTS]),
                 (b'', 404, 'COMPLETE', 'ALL_REQUESTS_FINISHED', [ROBOTS, URL1, URL2]),
                 (b'no', 403, 'STOPPED', 'ROBOTS_ACCESS_DENIED', [ROBOTS]),
                 (b'err', 503, 'STOPPED', 'ROBOTS_UNEXPECTED_RESPONSE', [ROBOTS])]
        for i, (body, status, expected, reason, opened) in enumerate(cases):
            with self.subTest(status=status):
                self.base = self.root / f'records-{i}'
                self.build()
                t = self.transport({ROBOTS: {'status': status, 'body': body}})
                result = self.dispatch(self.request(), t)
                self.assertEqual((result['status'], result['reason'], [o[0] for o in t.opened]), (expected, reason, opened))
        big_robots = {'body': b'#' * 600000}
        self.base = self.root / 'records-robots-big'
        self.build()
        result = self.dispatch(self.request(), self.transport({ROBOTS: big_robots}))
        self.assertEqual((result['status'], result['reason']), ('STOPPED', 'ROBOTS_UNRESOLVED'))

    # ---- PR #44 review: reproductions -------------------------------------------------------------------
    def rechain(self, path, mutate):
        """Rewrite a journal consistently, as someone with filesystem access could."""
        events = [json.loads(line) for line in path.read_bytes().splitlines()]
        mutate(events)
        previous, out = S.GENESIS, b''
        for seq, e in enumerate(events):
            core = {'seq': seq, 'type': e['type'], 'at': e['at'], 'previous': previous, 'record': e['record']}
            previous = digest(core)
            out += canonical({**core, 'hash': previous}) + b'\n'
        path.write_bytes(out)

    def forge_result(self, change):
        a = self.attempt()
        result = json.loads((a / 'result.json').read_bytes())
        change(result)
        data = canonical(result) + b'\n'
        (a / 'result.json').write_bytes(data)
        def anchor(events):
            events[-1]['record']['result_sha256'] = S.sha(data)
        self.rechain(a / 'journal.jsonl', anchor)

    def interrupt(self, responses=None):
        t = self.transport(responses or {URL1: {'body': b'i' * 5000, 'chunk': 1000, 'interrupt_after': 2000}})
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch(self.request(), t)
        return t

    def test_review_1_finalised_interrupted_result_is_bound_by_a_finalisation_record(self):
        self.interrupt()
        R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        a = self.attempt()
        self.assertTrue((a / 'finalisation.json').exists())
        original = (a / 'result.json').read_bytes()
        for name, change in (('status', lambda r: r.update(status='COMPLETE')),
                             ('consumption', lambda r: r['consumption']['bytes'].update(exact=5000)),
                             ('retained', lambda r: r['retained'].pop()),
                             ('handoff', lambda r: r['custody_handoff'].append({'receipt_sha256': r['receipts'][0]}))):
            with self.subTest(name):
                value = json.loads(original)
                change(value)
                (a / 'result.json').write_bytes(canonical(value) + b'\n')
                self.assertEqual(R.status(self.base, 'A1')['state'], 'INCONSISTENT')
        (a / 'result.json').write_bytes(original)
        self.assertEqual(R.status(self.base, 'A1')['state'], 'UNKNOWN')
        body = a / 'raw' / '002.body'
        body.write_bytes(body.read_bytes() + b'!')
        self.assertEqual(R.status(self.base, 'A1')['state'], 'INCONSISTENT')

    def test_review_2_stop_finding_lost_in_a_crash_is_reconstructed_from_receipts(self):
        real = T.record
        calls = []
        def crash(*args, **kwargs):
            calls.append(args)
            raise KeyboardInterrupt
        with patch.object(T, 'record', side_effect=crash):
            self.interrupt({URL1: {'status': 403, 'body': b'denied'}})
        self.assertEqual(T.findings(self.base), [])  # The 403 receipt exists; its stop was never recorded.
        t = self.transport()
        with patch.object(T, 'record', side_effect=lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt)):
            with self.assertRaises(KeyboardInterrupt):  # A crash during reconciliation itself.
                R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        result = R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        self.assertEqual([(f['scope'], f['host'], f['reason']) for f in result['stop_findings']], [('HOST', HOST, 'ACCESS_DENIED')])
        again = R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)  # Idempotent.
        self.assertEqual(again, result)
        self.assertEqual(len(T.findings(self.base)), 1)
        self.assertEqual((t.resolved, t.opened), ([], []))
        for lock in (self.attempt() / 'attempt.lock', S.records(self.base) / 'dispatch.lock'):
            lock.unlink()  # The owner's manual step after reconciliation.
        later = self.transport()
        self.assert_not_started(self.dispatch(self.request('A2'), later), 'STOPPED_SOURCE', later)
        self.base = self.root / 'records-robots'
        self.build()
        with patch.object(T, 'record', side_effect=crash):
            self.interrupt({ROBOTS: {'body': b'User-agent: *\nDisallow: /orders/1.pdf\n'}})
        result = R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        self.assertEqual([(f['scope'], f['route'], f['reason']) for f in result['stop_findings']], [('ROUTE', URL1, 'ROBOTS_DISALLOWED')])

    def test_review_3_only_verified_complete_200_responses_become_complete_originals(self):
        cases = [
            ('206', {'status': 206, 'body': b'part'}, 'STOPPED', 'UNEXPECTED_RESPONSE', None),
            ('204', {'status': 204, 'body': b''}, 'STOPPED', 'UNEXPECTED_RESPONSE', None),
            ('gzip', {'body': b'\x1f\x8b gz', 'headers': [('Content-Encoding', 'gzip')]}, 'STOPPED', 'UNEXPECTED_ENCODING', None),
            ('unframed', {'body': b'close-delimited', 'declared': False}, 'PARTIAL', 'UNVERIFIED_LENGTH', 'UNVERIFIED'),
            ('chunked', {'body': b'chunked body', 'declared': False, 'headers': [('Transfer-Encoding', 'chunked')]}, 'COMPLETE', 'COMPLETE', 'COMPLETE'),
            ('te and length', {'body': b'x' * 10, 'headers': [('Transfer-Encoding', 'chunked')]}, 'STOPPED', 'FRAMING_CONFLICT', None),
            ('two lengths', {'body': b'x' * 10, 'headers': [('Content-Length', '9')]}, 'STOPPED', 'FRAMING_CONFLICT', None),
            ('bad length', {'body': b'x' * 10, 'declared': False, 'headers': [('Content-Length', '1e3')]}, 'STOPPED', 'FRAMING_CONFLICT', None),
            ('overlong body', {'body': b'x' * 40, 'length': 10}, 'STOPPED', 'FRAMING_CONFLICT', None)]
        for i, (name, spec, status, termination, coverage) in enumerate(cases):
            with self.subTest(name):
                self.base = self.root / f'records-{i}'
                self.build()
                result = self.dispatch(self.request(), self.transport({URL1: spec}))
                receipt = json.loads((self.attempt() / 'receipts' / '002.json').read_bytes())
                self.assertEqual((result['status'], receipt['termination']), (status, termination))
                first = [h for h in result['custody_handoff'] if h['requested_url'] == URL1]
                self.assertEqual(first[0]['coverage'] if first else None, coverage)
                self.assertEqual(receipt['complete'], termination == 'COMPLETE')
                self.assertEqual(R.status(self.base, 'A1')['state'], status)

    def test_review_4_equivalent_urls_cannot_be_dispatched_twice(self):
        for i, pair in enumerate(((URL1, URL1 + '?'), (f'https://{HOST}', f'https://{HOST}/'),
                                  (URL1, URL1.replace('1.pdf', '%31.pdf')))):
            with self.subTest(pair=pair):
                self.base = self.root / f'records-dup-{i}'
                self.urls = list(pair)
                self.build()
                t = self.transport({u: {'body': b'same'} for u in pair})
                with self.assertRaisesRegex(ValueError, 'same request'):
                    self.dispatch(self.request(), t)
                self.assertEqual((t.resolved, t.opened), ([], []))
                self.assertFalse(self.attempt().exists())
        self.urls = [URL1, URL2]
        self.build()
        registry = json.loads(Path(self.registry['path']).read_bytes())
        registry['routes'].append({**registry['routes'][0], 'id': 'R0-COPY'})
        self.registry = self.put('registry.json', registry)
        quarry = json.loads(Path(self.quarry['path']).read_bytes())
        quarry['route_ids'].append('R0-COPY')
        self.quarry = self.put('quarry-scope.json', quarry)
        scope = json.loads(Path(self.scope['path']).read_bytes())
        scope.update(quarry_registry=self.registry, quarry_scope=self.quarry)
        self.scope = self.put('scope.json', scope)
        t = self.transport()
        self.assert_not_started(self.dispatch(self.request('A9'), t), 'ROUTE_AMBIGUOUS', t)

    def test_review_5_pre_claim_failures_are_distinct_from_refusals_and_claims(self):
        with patch.object(R, 'authorise', side_effect=OSError('disk full')), self.assertRaises(OSError):
            self.dispatch(self.request(), self.transport())
        status = R.status(self.base, 'A1')
        self.assertEqual(status['state'], 'PRECLAIM_INCOMPLETE')
        self.assertEqual(status['dispatch_lock']['attempt_id'], 'A1')  # Kept as evidence, never removed silently.
        with self.assertRaisesRegex(ValueError, 'DISPATCH_LOCKED'):
            self.dispatch(self.request('A2'), self.transport())
        result = R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        self.assertEqual((result['status'], result['interrupted'], result['reason'].split(':')[0]),
                         ('NOT_STARTED', True, 'PRECLAIM_INCOMPLETE'))
        self.assertEqual(R.status(self.base, 'A1')['state'], 'NOT_STARTED')
        self.assertFalse(any(e['type'] == 'ATTEMPT_RESERVED' for e in self.ledger()))

    def test_review_6_forged_but_rechained_results_and_receipts_fail_closed(self):
        self.dispatch(self.request(), self.transport({URL1: {'body': b'x' * 300000, 'declared': False, 'chunk': 65536}}))
        self.assertEqual(R.status(self.base, 'A1')['state'], 'PARTIAL')
        a = self.attempt()
        pristine = {p: p.read_bytes() for p in a.rglob('*') if p.is_file()}
        def restore():
            for p, data in pristine.items():
                p.write_bytes(data)
        forgeries = {
            'handoff upgraded': lambda r: (r.update(status='COMPLETE'), r['custody_handoff'][0].update(coverage='COMPLETE')),
            'handoff bytes': lambda r: r['custody_handoff'][0].update(bytes=1),
            'handoff route': lambda r: r['custody_handoff'][0].update(quarry_route_id='R1'),
            'handoff without receipt': lambda r: r['custody_handoff'][0].update(receipt_sha256='f' * 64),
            'status': lambda r: r.update(status='COMPLETE'),
            'consumption': lambda r: r['consumption']['bytes'].update(exact=1, at_least=1),
            'unexpected field': lambda r: r.update(extra=True),
            'stop findings': lambda r: r['stop_findings'].append({'stop_id': 'STP-forged'})}
        for name, change in forgeries.items():
            with self.subTest(name):
                try:
                    self.forge_result(change)
                    self.assertEqual(R.status(self.base, 'A1')['state'], 'INCONSISTENT')
                finally:
                    restore()
        self.assertEqual(R.status(self.base, 'A1')['state'], 'PARTIAL')
        receipt_path = a / 'receipts' / '002.json'
        receipt = json.loads(receipt_path.read_bytes())
        receipt.update(termination='COMPLETE', complete=True, coverage='COMPLETE')
        data = canonical(receipt) + b'\n'
        receipt_path.write_bytes(data)
        old = S.sha(pristine[receipt_path])
        def swap(events):
            for e in events:
                if e['type'] == 'REQUEST_FINISHED' and e['record']['receipt_sha256'] == old:
                    e['record']['receipt_sha256'] = S.sha(data)
        self.rechain(a / 'journal.jsonl', swap)
        self.forge_result(lambda r: (r.update(receipts=[S.sha(data) if x == old else x for x in r['receipts']]),
                                     [h.update(receipt_sha256=S.sha(data), coverage='COMPLETE') for h in r['custody_handoff'] if h['receipt_sha256'] == old],
                                     [x.update(receipt_sha256=S.sha(data), coverage='COMPLETE') for x in r['retained'] if x['receipt_sha256'] == old]))
        status = R.status(self.base, 'A1')
        self.assertEqual(status['state'], 'INCONSISTENT')
        self.assertTrue(any('RECEIPT_INCONSISTENT' in p for p in status['problems']), status['problems'])
        restore()
        receipt = json.loads(receipt_path.read_bytes())
        receipt['interpretation'] = 'complete original'  # An unexpected field, consistently rechained.
        data = canonical(receipt) + b'\n'
        receipt_path.write_bytes(data)
        self.rechain(a / 'journal.jsonl', swap)
        status = R.status(self.base, 'A1')
        self.assertTrue(any('RECEIPT_MALFORMED' in p for p in status['problems']), status['problems'])

    def test_review_7_route_stops_are_exact_and_stale_snapshots_are_refused(self):
        record = {'status': 'STOPPED', 'reason': 'route closed; no host named'}
        self.build(stop_records=[record], resolutions=[{'input_sha256': S.sha(canonical(record)), 'hosts': [],
                                                        'routes': [f'https://{HOST}/orders/1'], 'task_scoped_reason': None}])
        result = self.dispatch(self.request(), self.transport())
        self.assertEqual(result['status'], 'COMPLETE')  # https://host/orders/1 does not stop .../orders/1.pdf
        stops_dir = self.root / 'stop-dir'
        stops_dir.mkdir()
        (stops_dir / 'final_stop.json').write_bytes(canonical({'status': 'STOPPED', 'url': 'https://stopped.example.net/x'}))
        self.base = self.root / 'records-fresh'
        snap = T.build([], self.base, from_dirs=[stops_dir], attestation=self.put('att.json', {
            'schema': C.ATTESTATION, 'attested_by': OWNER, 'attested_at': '2026-10-26T08:00:00+00:00',
            'inputs': [S.sha((stops_dir / 'final_stop.json').read_bytes())], 'resolutions': [], 'documented_stops': [],
            'statement': 'I reviewed the listed stop records and the reports available to me. Unclear scopes are recorded host-level.'})['path'],
            clock=self.clock.now)
        self.snapshot = {'path': snap['path'], 'sha256': snap['sha256']}
        (stops_dir / 'new' ).mkdir()
        (stops_dir / 'new' / 'publication_stop.json').write_bytes(canonical({'status': 403, 'url': f'https://{HOST}/x'}))
        t = self.transport()
        self.assert_not_started(self.dispatch(self.request('F1'), t), 'STOP_SNAPSHOT_STALE', t)

    # ---- PR #44 final edge cases ---------------------------------------------------------------------------
    def test_final_1_every_dns_answer_is_validated_before_any_truncation(self):
        publics = [f'93.184.216.{i}' for i in range(1, 17)]
        cases = [('16 public then private', publics + ['10.0.0.1'], 'ADDRESS_REFUSED'),
                 ('private hidden past 16', publics[:8] + ['127.0.0.1'] + publics[8:], 'ADDRESS_REFUSED'),
                 ('oversized all public', publics + ['93.184.216.200'], 'DNS_FAILED'),
                 ('non-string entry', [PUBLIC, 1234], 'DNS_FAILED'),
                 ('overlong entry', [PUBLIC, '9' * 100], 'DNS_FAILED'),
                 ('not a list', {'a': PUBLIC}, 'DNS_FAILED')]
        for i, (name, answer, termination) in enumerate(cases):
            with self.subTest(name):
                self.base = self.root / f'records-dns-{i}'
                self.build()
                t = self.transport(dns={HOST: answer})
                result = self.dispatch(self.request(), t)
                receipt = json.loads((self.attempt() / 'receipts' / '001.json').read_bytes())
                self.assertEqual(t.opened, [])  # Never connects after a forbidden or malformed answer.
                self.assertEqual((result['status'], receipt['termination'], receipt['connected_address']), ('STOPPED', termination, None))
                self.assertEqual(R.status(self.base, 'A1')['state'], 'STOPPED')
        self.base = self.root / 'records-dns-16'
        self.build()
        t = self.transport(dns={HOST: publics})
        self.assertEqual(self.dispatch(self.request(), t)['status'], 'COMPLETE')  # Sixteen public answers are accepted.
        self.assertTrue(all(o[2] == publics[0] for o in t.opened))

    def test_final_2_no_request_or_connection_starts_after_the_time_has_expired(self):
        overshoot = Clock()
        overshoot.sleep = lambda seconds: Clock.sleep(overshoot, seconds + 1000)  # Asked for ~2 s, slept far past the 600 s budget.
        self.clock = overshoot
        t = self.transport()
        result = self.dispatch(self.request(), t)
        self.assertEqual([o[0] for o in t.opened], [ROBOTS])
        self.assertEqual((result['status'], result['reason'], result['not_attempted']), ('STOPPED', 'BUDGET', [URL1, URL2]))
        self.assertEqual(result['consumption']['requests'], {'at_least': 1, 'exact': 1})
        events = [e['type'] for e in S.Journal(self.attempt() / 'journal.jsonl').load()]
        self.assertEqual(events.count('REQUEST_CLAIMED'), 1)
        self.assertIn('BUDGET_EXHAUSTED', events)
        self.assertEqual(R.status(self.base, 'A1')['state'], 'STOPPED')
        self.base, self.clock = self.root / 'records-slow-dns', Clock()
        self.build()
        t = self.transport()
        t.dns_seconds = 30  # Longer than the 10 s request timeout.
        result = self.dispatch(self.request(), t)
        receipt = json.loads((self.attempt() / 'receipts' / '001.json').read_bytes())
        self.assertEqual((t.opened, receipt['termination'], receipt['connected_address']), ([], 'DEADLINE_EXCEEDED', None))
        self.assertEqual((result['status'], result['reason'], result['stop_findings']), ('STOPPED', 'ROBOTS_DEADLINE_EXCEEDED', []))
        self.assertEqual(R.status(self.base, 'A1')['state'], 'STOPPED')

    def test_robots_crawl_delay_paces_within_the_wall_budget(self):
        result = self.dispatch(self.request(), self.transport({ROBOTS: {'body': b'User-agent: *\nCrawl-delay: 5\n'}}))
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(len(self.clock.sleeps), 2)
        self.assertTrue(all(4.99 < s <= 5 for s in self.clock.sleeps))
        self.base, self.clock = self.root / 'records-slow', Clock()
        self.build()
        t = self.transport({ROBOTS: {'body': b'User-agent: *\nCrawl-delay: 100000\n'}})
        result = self.dispatch(self.request(), t)
        self.assertEqual((result['status'], result['reason'], [o[0] for o in t.opened]), ('STOPPED', 'BUDGET', [ROBOTS]))
        self.assertEqual(self.clock.sleeps, [])  # Never sleeps past the wall budget.

    def test_pinned_https_connection_uses_validated_address_and_url_host(self):
        class Sock:
            def __init__(self, peer): self.peer, self.closed = peer, False
            def getpeername(self): return (self.peer, 443)
            def close(self): self.closed = True
        class Context:
            def wrap_socket(self, sock, server_hostname):
                self.wrapped = (sock, server_hostname)
                return sock
        calls = []
        def connect(address, timeout):
            calls.append((address, timeout))
            return Sock(address[0])
        with patch.object(N.socket, 'create_connection', side_effect=connect):
            c = N.PinnedHTTPSConnection(HOST, PUBLIC, 7, Context())
            c.connect()
        self.assertEqual(calls, [((PUBLIC, 443), 7)])
        self.assertEqual(c._context.wrapped[1], HOST)
        liar = Sock('10.0.0.1')
        with patch.object(N.socket, 'create_connection', return_value=liar), self.assertRaises(ConnectionError):
            N.PinnedHTTPSConnection(HOST, PUBLIC, 7, Context()).connect()
        self.assertTrue(liar.closed)

    def test_check_is_read_only_and_cli_reports_without_dispatch(self):
        request = self.request()
        before = sorted(p.relative_to(self.root) for p in self.root.rglob('*'))
        value = R.check(request, self.base, clock=self.clock.now)
        self.assertEqual((value['refusal'], value['duplicate_attempt'], value['external_requests_started']), (None, False, 0))
        self.assertEqual(before, sorted(p.relative_to(self.root) for p in self.root.rglob('*')))
        out = pyio.StringIO()
        with redirect_stdout(out):
            self.assertEqual(CLI.main(['implementation']), 0)
        self.assertEqual(json.loads(out.getvalue())['implementation_sha256'], S.implementation())
        self.build(attest=False)
        out = pyio.StringIO()
        with redirect_stdout(out):  # A refused run never constructs the real transport.
            self.assertEqual(CLI.main(['--base', str(self.base), 'run', self.request('R1')]), 0)
        self.assertEqual(json.loads(out.getvalue())['status'], 'NOT_STARTED')

    def test_campaign_interface_fields_and_component_boundaries(self):
        result = self.dispatch(self.request(), self.transport())
        self.assertEqual(sorted(result), sorted([
            'schema', 'request_sha256', 'attempt_id', 'campaign_id', 'branch_id', 'request_id', 'caller_ref', 'scope_sha256',
            'journal_head', 'status', 'reason', 'receipts', 'retained', 'stop_findings', 'host_pending', 'field_support_proposals',
            'custody_handoff', 'not_attempted', 'unfinished_requests', 'consumption', 'interrupted', 'journal_sha256',
            'implementation_sha256', 'exactly_once', 'authorises']))
        self.assertEqual((result['schema'], result['caller_ref'], result['host_pending'], result['field_support_proposals']),
                         (C.RESULT, 'campaign-opaque-ref', [], []))
        source = '\n'.join(p.read_text() for p in (S.ROOT / 'src/research/source_v1').glob('*.py'))
        for forbidden in ('subprocess', 'opportunity_scout', 'research.operator', 'campaign_v1', 'webbrowser', 'requests', 'urllib.request'):
            self.assertNotIn('import ' + forbidden, source)
            self.assertNotIn('from src.research.' + forbidden.split('.')[-1], source)
        self.assertIn('RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001', C.REQUEST)


if __name__ == '__main__':
    unittest.main()
