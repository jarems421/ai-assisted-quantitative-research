"""One bounded exact-URL retrieval attempt: refuse, or claim and retrieve serially, then one immutable result.

Called by the campaign controller as a bounded activity. It never schedules, retries, resumes or calls another
component. External effects happen only through the transport, and only after a durable claim. An attempt
that ends abnormally keeps its locks and is INTERRUPTED until the owner reconciles it record-only.
"""
from __future__ import annotations

import hashlib
import ipaddress
import math
import os
import time
from urllib import robotparser
from src.research.spec import canonical, digest
from src.research.quarry_v1 import io as Q
from src.research.quarry_v1.acquisition import plan as quarry_plan
from . import contracts as C, store as S, stops as T
from .transport import ROBOTS_AGENT, HttpsTransport

CHUNK = 64 * 1024
ROBOTS_MAX = 512 * 1024
HEADERS = ('content-type', 'content-length', 'content-encoding', 'last-modified', 'etag', 'date', 'location', 'retry-after')
LIMITATIONS = ['Bytes are the representation served at retrieval time; historical publication and earlier versions are UNKNOWN.',
               'TLS authenticated the host at retrieval time only; source authenticity and correctness are UNKNOWN.',
               'No content was parsed, extracted or interpreted.']
PRECEDENCE = ('UNKNOWN', 'STOPPED', 'UNAVAILABLE', 'PARTIAL')
# termination -> (attempt flag, stop scope, ends the attempt)
OUTCOMES = {'COMPLETE': (None, None, False), 'SIZE_STOP': ('PARTIAL', None, False), 'TIME_STOP': ('PARTIAL', None, False),
            'REDIRECT_REFUSED': ('STOPPED', 'ROUTE', True), 'ACCESS_DENIED': ('STOPPED', 'HOST', True),
            'RATE_LIMITED': ('STOPPED', 'HOST', True), 'NOT_FOUND': ('UNAVAILABLE', 'ROUTE', True),
            'UNEXPECTED_RESPONSE': ('STOPPED', 'HOST', True), 'DNS_FAILED': ('STOPPED', None, True),
            'ADDRESS_REFUSED': ('STOPPED', 'HOST', True), 'TRANSPORT_FAILED': ('UNKNOWN', 'HOST', True)}


def public(address):
    try:
        ip = ipaddress.ip_address(str(address).split('%')[0])
    except ValueError:
        return False
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not (ip.is_multicast or ip.is_private or ip.is_reserved or ip.is_loopback
                                 or ip.is_link_local or ip.is_unspecified)


def by_status(status):
    if 300 <= status < 400:
        return 'REDIRECT_REFUSED'
    if status in (401, 403):
        return 'ACCESS_DENIED'
    if status == 429:
        return 'RATE_LIMITED'
    if status in (404, 410):
        return 'NOT_FOUND'
    return 'UNEXPECTED_RESPONSE'


def directories(base, attempt_id):
    root = S.records(base)
    return root, root / 'attempts' / attempt_id


def authorise(request, base, ledger, now):
    """Every pre-claim check. Raises ValueError with a reason code; reads only."""
    a, r = request['authority'], request['resources']['reservation']
    scope_raw, scope = S.load(a['scope']['path'], 'owner scope')
    C.need(S.sha(scope_raw) == a['scope']['sha256'], 'SCOPE_CHANGED: owner scope bytes differ from the request hash')
    try:
        C.scope(scope)
    except ValueError as error:
        raise C.SourceError('SCOPE_INVALID: ' + str(error)) from error
    C.need((scope['campaign_id'], scope['branch_id'], scope['card_sha256'])
           == (request['campaign_id'], request['branch_id'], request['subject']['card_sha256']),
           'SCOPE_BINDING: the owner scope belongs to another campaign, branch or card')
    C.need(scope['implementation_sha256'] == S.implementation(), 'IMPLEMENTATION_DRIFT: the owner scope binds different source code')
    C.need(C.moment(scope['decided_at'], 'decided_at') <= now <= C.moment(scope['valid_until'], 'valid_until'),
           'SCOPE_NOT_VALID_NOW: outside the owner scope validity window')
    raws = {}
    for key in ('quarry_registry', 'quarry_scope'):
        raws[key] = S.read(scope[key]['path'], 1024 * 1024)
        C.need(S.sha(raws[key]) == scope[key]['sha256'], f'QUARRY_INPUT_CHANGED: {key} bytes differ from the owner scope')
    try:
        plan = quarry_plan(scope['quarry_registry']['path'], scope['quarry_scope']['path'])
    except ValueError as error:
        raise C.SourceError('QUARRY_RESTRICTION: ' + str(error)) from error
    registry = C.parse(raws['quarry_registry'], 'Quarry registry')
    C.need(plan['registry_sha256'] == digest(registry) and plan['scope_sha256'] == digest(C.parse(raws['quarry_scope'], 'Quarry scope')),
           'QUARRY_INPUT_CHANGED: Quarry files changed while being checked')
    q, tier = plan['scope'], a['tier_a']
    C.need(set(tier['exact_urls']) == set(q['exact_urls']) and set(tier['hosts']) == set(q['allowed_hosts']),
           'SCOPE_VIOLATION: request URLs or hosts differ from the owner-approved Quarry scope')
    C.need(r['requests'] <= q['request_ceiling'] and r['total_bytes'] <= q['total_byte_ceiling']
           and r['per_response_bytes'] <= q['per_response_byte_ceiling'], 'RESERVATION_EXCEEDS_SCOPE: above the Quarry scope ceilings')
    prior = [e['record'] for e in ledger if e['type'] == 'ATTEMPT_RESERVED' and e['record']['scope_sha256'] == a['scope']['sha256']]
    C.need(len(prior) < scope['attempt_ceiling'], 'SCOPE_ATTEMPTS_EXHAUSTED: the owner scope allows no further attempt')
    C.need(sum(p['reservation']['requests'] for p in prior) + r['requests'] <= scope['total_requests']
           and sum(p['reservation']['total_bytes'] for p in prior) + r['total_bytes'] <= scope['total_bytes'],
           'RESERVATION_EXCEEDS_SCOPE: cumulative reservations would exceed the owner scope (reservations are never released)')
    snapshot_raw, snapshot = T.snapshot(request['stops']['snapshot'])
    entries = snapshot['entries'] + T.findings(base)
    for url in tier['exact_urls']:
        hit = T.blocking(url, C.host_of(url), entries)
        C.need(hit is None, f"STOPPED_SOURCE: {hit['stop_id'] if hit else ''} stops {hit['scope'] if hit else ''} {hit['host'] if hit else ''}")
    return {'scope': scope, 'scope_raw': scope_raw, 'quarry': q, 'raws': raws, 'snapshot_raw': snapshot_raw,
            'routes': {route['locator']: route['id'] for route in registry['routes']}}


def check(request_path, base=None, clock=S.now):
    """Read-only preflight for the campaign: the refusal reason run would record, or None."""
    raw, request = S.load(request_path, 'source request')
    C.request(request)
    _, attempt = directories(base, request['attempt_id'])
    ledger = S.Journal(S.records(base) / 'ledger.jsonl').load()
    used = attempt.exists() or any(e['record'].get('attempt_id') == request['attempt_id'] for e in ledger)
    try:
        authorise(request, base, ledger, C.moment(clock(), 'clock'))
        reason = None
    except ValueError as error:
        reason = str(error)
    return {'request_sha256': S.sha(raw), 'attempt_id': request['attempt_id'], 'duplicate_attempt': used,
            'refusal': reason, 'implementation_sha256': S.implementation(), 'external_requests_started': 0, 'authorises': []}


def consumption(requests=0, requests_exact=True, received=0, bytes_exact=True, wall=0.0):
    count = lambda n, exact: {'at_least': n, 'exact': n if exact else None}
    return {'requests': count(requests, requests_exact), 'bytes': count(received, bytes_exact),
            'wall_seconds': count(round(wall, 3), requests_exact), 'searches': count(0, True), 'model_calls': count(0, True),
            'metered_micro_usd': {'reserved': 0, 'estimated': 0, 'actual': 0}, 'subscription_usage': 'NOT_USED'}


def outcome_record(request, request_sha, status, reason, **fields):
    value = {'schema': C.RESULT, 'request_sha256': request_sha, 'attempt_id': request['attempt_id'],
             'campaign_id': request['campaign_id'], 'branch_id': request['branch_id'], 'request_id': request['request_id'],
             'caller_ref': request['caller_ref'], 'scope_sha256': None, 'journal_head': None, 'status': status, 'reason': reason,
             'receipts': [], 'retained': [], 'stop_findings': [], 'host_pending': [], 'field_support_proposals': [],
             'custody_handoff': [], 'not_attempted': [], 'unfinished_requests': [], 'consumption': consumption(),
             'interrupted': False, 'journal_sha256': None, 'implementation_sha256': S.implementation(),
             'exactly_once': False, 'authorises': []}
    value.update(fields)
    C.need(value['status'] in C.STATUSES, 'unknown status')
    return value


def run(request_path, base=None, *, transport=None, clock=S.now, ticks=time.monotonic, sleep=time.sleep):
    raw, request = S.load(request_path, 'source request')
    C.request(request)
    root, attempt = directories(base, request['attempt_id'])
    dispatch = root / 'dispatch.lock'
    C.need(S.acquire(dispatch, {'attempt_id': request['attempt_id'], 'at': clock()}),
           'DISPATCH_LOCKED: another attempt is running or was interrupted; reconcile it before any new attempt')
    claimed = False
    try:
        ledger = S.Journal(root / 'ledger.jsonl', clock)
        events = ledger.load()
        C.need(not attempt.exists() and not any(e['record'].get('attempt_id') == request['attempt_id'] for e in events),
               'DUPLICATE_ATTEMPT: this attempt id was already used; a new attempt needs a new id from the campaign')
        attempt.mkdir(parents=True)
        request_sha = S.write_new(attempt / 'request.json', raw)
        journal = S.Journal(attempt / 'journal.jsonl', clock)
        try:
            ctx = authorise(request, base, events, C.moment(clock(), 'clock'))
        except ValueError as error:
            result = outcome_record(request, request_sha, 'NOT_STARTED', str(error))
            journal.append('ATTEMPT_REFUSED', {'result_sha256': S.write_new(attempt / 'result.json', result)})
            S.release(dispatch)
            return result
        C.need(S.acquire(attempt / 'attempt.lock', {'attempt_id': request['attempt_id'], 'at': clock()}), 'attempt locked')
        claimed = True
        reservation, scope_sha = request['resources']['reservation'], request['authority']['scope']['sha256']
        ledger.append('ATTEMPT_RESERVED', {'attempt_id': request['attempt_id'], 'request_sha256': request_sha,
                                           'scope_sha256': scope_sha, 'reservation': reservation})
        journal.append('ATTEMPT_CLAIMED', {'request_sha256': request_sha, 'scope_sha256': scope_sha, 'reservation': reservation,
                                           'snapshot_sha256': request['stops']['snapshot']['sha256'],
                                           'implementation_sha256': S.implementation()})
        for name, data in (('scope.json', ctx['scope_raw']), ('quarry-registry.json', ctx['raws']['quarry_registry']),
                           ('quarry-scope.json', ctx['raws']['quarry_scope']), ('stop-snapshot.json', ctx['snapshot_raw'])):
            S.write_new(attempt / 'inputs' / name, data)
        result = retrieve(request, request_sha, ctx, attempt, journal, ledger, T.register(base, clock),
                          transport or HttpsTransport(), clock, ticks, sleep)
        journal.append('ATTEMPT_FINISHED', {'result_sha256': S.write_new(attempt / 'result.json', result)})
    except BaseException:
        if not claimed:
            S.release(dispatch)
        raise  # After the claim, locks stay: the attempt is INTERRUPTED until reconciled.
    S.release(attempt / 'attempt.lock')
    S.release(dispatch)
    return result


def pause(ledger, interval, clock):
    """Seconds to wait so that consecutive dispatches, across all attempts, are at least interval apart."""
    last = next((e['at'] for e in reversed(ledger.load()) if e['type'] == 'REQUEST_DISPATCHING'), None)
    if not last:
        return 0.0
    return max(0.0, interval - (C.moment(clock(), 'clock') - C.moment(last, 'ledger time')).total_seconds())


def retrieve(request, request_sha, ctx, attempt, journal, ledger, register, transport, clock, ticks, sleep):
    r, q, attempt_id = request['resources']['reservation'], ctx['quarry'], request['attempt_id']
    steps, seen = [], set()
    for url in request['authority']['tier_a']['exact_urls']:
        host = C.host_of(url)
        if host not in seen:
            seen.add(host)
            steps.append(('ROBOTS', f'https://{host}/robots.txt', host))
        steps.append(('TARGET', url, host))
    start, used, index = ticks(), 0, 0
    flags, reason, ended = set(), None, False
    receipts, retained, findings, handoff, not_attempted, rules, robots_receipt = [], [], [], [], [], {}, {}

    def stop(scope, host, route, why, receipt_sha):
        finding = T.record(register, scope, host, route, why, attempt_id, receipt_sha, clock())
        journal.append('STOP_FOUND', {'stop_id': finding['stop_id'], 'scope': scope, 'host': host, 'route': route, 'reason': why})
        findings.append(finding)

    for role, url, host in steps:
        if ended:
            not_attempted.append(url)
            continue
        if role == 'TARGET' and not rules[host].can_fetch(ROBOTS_AGENT, url):
            stop('ROUTE', host, url, 'ROBOTS_DISALLOWED', robots_receipt[host])
            flags.add('STOPPED'); reason, ended = 'ROBOTS_DISALLOWED', True
            not_attempted.append(url)
            continue
        delay = rules[host].crawl_delay(ROBOTS_AGENT) if role == 'TARGET' else None
        wait = pause(ledger, max(float(q['minimum_interval_seconds']), float(delay or 0)), clock)
        elapsed, remaining = ticks() - start, r['total_bytes'] - used
        if index >= r['requests'] or remaining <= 0 or elapsed + wait >= r['wall_seconds']:
            journal.append('BUDGET_EXHAUSTED', {'requests': index, 'bytes': used, 'wall_seconds': round(elapsed, 3),
                                                'required_wait_seconds': round(wait, 3)})
            flags.add('STOPPED'); reason, ended = 'BUDGET', True
            not_attempted.append(url)
            continue
        if wait:
            sleep(wait)
        elapsed = ticks() - start
        index += 1
        cap = min(r['per_response_bytes'], remaining, ROBOTS_MAX if role == 'ROBOTS' else r['per_response_bytes'])
        journal.append('REQUEST_CLAIMED', {'index': index, 'role': role, 'url': url, 'host': host})
        ledger.append('REQUEST_DISPATCHING', {'attempt_id': attempt_id, 'index': index, 'host': host})
        receipt = fetch(transport, attempt, attempt_id, index, role, url, host, cap,
                        min(q['timeout_seconds'], r['wall_seconds'] - elapsed), clock, ticks)
        receipt_sha = S.write_new(attempt / 'receipts' / f'{index:03d}.json', receipt)
        journal.append('REQUEST_FINISHED', {'index': index, 'receipt_sha256': receipt_sha})
        receipts.append(receipt_sha)
        used += receipt['bytes_received']
        if receipt['body_path']:
            retained.append({'role': role, 'url': url, 'receipt_sha256': receipt_sha, 'body_path': receipt['body_path'],
                             'body_sha256': receipt['body_sha256'], 'bytes': receipt['bytes_received'],
                             'http_status': receipt['http_status'], 'coverage': receipt['coverage']})
        term, status = receipt['termination'], receipt['http_status']
        if role == 'ROBOTS':
            robots_receipt[host] = receipt_sha
            # RFC 9309 permits ignoring rules past 500 KiB, but an unread file is unresolved, never permissive.
            if term == 'COMPLETE' or (term == 'SIZE_STOP' and receipt['bytes_received']):
                rules[host] = robots(attempt, receipt)
                continue
            if status is not None and 400 <= status < 500 and status not in (401, 403, 429):
                rules[host] = robots(None, None)  # Unavailable robots.txt: no rules apply (RFC 9309 2.3.1.3).
                continue
            if term in ('TIME_STOP', 'SIZE_STOP'):
                flags.add('STOPPED'); reason, ended = 'ROBOTS_UNRESOLVED', True
                continue
        flag, scope, ends = OUTCOMES[term]
        if flag:
            flags.add(flag)
        if scope:
            stop(scope, host, url if scope == 'ROUTE' else None, term, receipt_sha)
        if ends:
            reason, ended = term if role == 'TARGET' else 'ROBOTS_' + term, True
        elif role == 'TARGET' and status is not None and 200 <= status < 300 and receipt['bytes_received']:
            handoff.append({'receipt_sha256': receipt_sha, 'requested_url': url, 'quarry_route_id': ctx['routes'].get(url),
                            'body_path': receipt['body_path'], 'body_sha256': receipt['body_sha256'],
                            'bytes': receipt['bytes_received'], 'coverage': receipt['coverage']})
    status = next((s for s in PRECEDENCE if s in flags), 'COMPLETE')
    return outcome_record(request, request_sha, status, reason or 'ALL_REQUESTS_FINISHED',
                          scope_sha256=request['authority']['scope']['sha256'], journal_head=journal.load()[-1]['hash'],
                          receipts=receipts, retained=retained, stop_findings=findings, custody_handoff=handoff,
                          not_attempted=not_attempted, consumption=consumption(index, True, used, True, ticks() - start))


def robots(attempt, receipt):
    rules = robotparser.RobotFileParser()
    raw = S.read(attempt / receipt['body_path'], ROBOTS_MAX) if receipt and receipt['body_path'] else b''
    rules.parse(raw.decode('utf-8', 'replace').splitlines())
    return rules


def fetch(transport, attempt, attempt_id, index, role, url, host, cap, deadline, clock, ticks):
    receipt = {'schema': C.RECEIPT, 'attempt_id': attempt_id, 'request_index': index, 'role': role, 'requested_url': url,
               'host': host, 'tier': 'A', 'resolved_addresses': [], 'connected_address': None, 'started_at': clock(),
               'finished_at': None, 'http_status': None, 'headers_sha256': None, 'headers_selected': {}, 'declared_length': None,
               'bytes_received': 0, 'body_sha256': None, 'body_path': None, 'complete': False, 'coverage': 'NONE',
               'termination': None, 'failure': None, 'max_bytes': cap, 'limitations': list(LIMITATIONS),
               'implementation_sha256': S.implementation()}

    def done(termination, failure=None):
        receipt.update(termination=termination, failure=failure, finished_at=clock())
        return receipt

    try:
        addresses = transport.resolve(host)
    except Exception as error:  # Exception text is never recorded, only its type.
        return done('DNS_FAILED', type(error).__name__)
    addresses = [str(a) for a in addresses] if isinstance(addresses, (list, tuple)) else []
    receipt['resolved_addresses'] = addresses[:16]
    if not addresses:
        return done('DNS_FAILED', 'NO_ADDRESS')
    if not all(public(a) for a in addresses):  # Any non-public answer refuses the host (rebinding defence).
        return done('ADDRESS_REFUSED', 'NON_PUBLIC_ADDRESS')
    receipt['connected_address'] = addresses[0]
    began = ticks()
    try:
        response = transport.open(url, host, addresses[0], max(1, math.ceil(deadline)))
    except Exception as error:
        return done('TRANSPORT_FAILED', type(error).__name__)
    try:
        status = response.status if isinstance(response.status, int) else None
        headers = [[str(k), str(v)] for k, v in response.headers]
        selected = {}
        for k, v in headers:
            if k.lower() in HEADERS and k.lower() not in selected:
                selected[k.lower()] = v[:2048]
        length = selected.get('content-length', '')
        declared = int(length) if length.isdigit() else None
        receipt.update(http_status=status, headers_sha256=S.sha(canonical(headers)), headers_selected=selected, declared_length=declared)
        ok = status is not None and 200 <= status < 300
        if ok and declared is not None and declared > cap:
            receipt['limitations'].append('Declared length exceeds the ceiling; no body bytes were read.')
            return done('SIZE_STOP', 'DECLARED_LENGTH_EXCEEDS_CEILING')
        relative = f'raw/{index:03d}.body'
        (attempt / 'raw').mkdir(exist_ok=True)
        digest_, total, size_stop, time_stop, failure = hashlib.sha256(), 0, False, False, None
        with Q.safe_path(attempt / relative).open('xb') as out:
            try:
                while True:
                    if ticks() - began > deadline:
                        time_stop = True
                        break
                    chunk = response.read(min(CHUNK, cap - total + 1))
                    if not chunk:
                        break
                    if total + len(chunk) > cap:
                        chunk, size_stop = chunk[:cap - total], True
                    out.write(chunk)
                    digest_.update(chunk)
                    total += len(chunk)
                    if size_stop:
                        break
            except Exception as error:
                failure = type(error).__name__
            out.flush()
            os.fsync(out.fileno())
        receipt.update(body_path=relative, bytes_received=total, body_sha256=digest_.hexdigest())
        short = declared is not None and total < declared and not (size_stop or time_stop)
        if status is None:
            termination, failure = 'TRANSPORT_FAILED', failure or 'NO_STATUS'
        elif not ok:
            termination = by_status(status)
        elif size_stop:
            termination = 'SIZE_STOP'
        elif time_stop:
            termination = 'TIME_STOP'
        elif failure or short:
            termination, failure = 'TRANSPORT_FAILED', failure or 'INCOMPLETE_BODY'
        else:
            termination = 'COMPLETE'
        complete = termination == 'COMPLETE'
        receipt.update(complete=complete, coverage='COMPLETE' if complete else 'PREFIX' if total else 'NONE')
        if ok and not complete:
            receipt['limitations'].append('The body is incomplete: only the retained prefix was received.')
        return done(termination, failure)
    finally:
        try:
            response.close()
        except Exception:
            pass


def verify(base, attempt_id):
    """(state, result or None, problems). Read-only: recomputes every hash; never repairs."""
    root, attempt = directories(base, attempt_id)
    C.need(attempt.is_dir(), 'unknown attempt')
    request_raw = S.read(attempt / 'request.json')
    events, tail = S.Journal(attempt / 'journal.jsonl').prefix()
    finished = {e['record']['index']: e['record']['receipt_sha256'] for e in events if e['type'] == 'REQUEST_FINISHED'}
    for index, expected in finished.items():
        raw = S.read(attempt / 'receipts' / f'{index:03d}.json')
        C.need(S.sha(raw) == expected, f'RECEIPT_ALTERED: receipt {index} differs from the journal')
        receipt = C.parse(raw, 'receipt')
        if receipt['body_path']:
            body = S.read(attempt / receipt['body_path'])
            C.need(S.sha(body) == receipt['body_sha256'] and len(body) == receipt['bytes_received'],
                   f'BODY_ALTERED: retained body {index} differs from its receipt')
    result_path = attempt / 'result.json'
    if not result_path.exists():
        return 'INTERRUPTED', None, ['claimed without a result'] + (['incomplete journal tail'] if tail else [])
    result_raw = S.read(result_path)
    result = C.parse(result_raw, 'result')
    C.need(result['request_sha256'] == S.sha(request_raw), 'REQUEST_ALTERED: request differs from the result')
    if result['interrupted']:
        C.need(result['journal_sha256'] == S.sha(S.Journal(attempt / 'journal.jsonl').bytes()), 'JOURNAL_ALTERED: after finalisation')
    else:
        C.need(not tail and events and events[-1]['type'] in ('ATTEMPT_FINISHED', 'ATTEMPT_REFUSED')
               and events[-1]['record']['result_sha256'] == S.sha(result_raw), 'RESULT_ALTERED: result differs from the journal')
    C.need(result['receipts'] == [finished[i] for i in sorted(finished)], 'RESULT_ALTERED: receipts differ from the journal')
    return result['status'], result, []


def status(base, attempt_id):
    root, attempt = directories(base, attempt_id)
    C.need(attempt.is_dir(), 'unknown attempt')
    try:
        state, result, notes = verify(base, attempt_id)
        problems = []
    except ValueError as error:
        state, result, notes, problems = 'INCONSISTENT', None, [], [str(error)]
    events, tail = [], b''
    try:
        events, tail = S.Journal(attempt / 'journal.jsonl').prefix()
    except ValueError as error:
        problems.append(str(error))
    return {'schema': C.STATUS, 'attempt_id': attempt_id, 'state': state, 'notes': notes, 'problems': problems,
            'result_sha256': S.sha(S.read(attempt / 'result.json')) if (attempt / 'result.json').exists() else None,
            'journal_events': len(events), 'journal_head': events[-1]['hash'] if events else None, 'incomplete_tail': bool(tail),
            'attempt_lock': S.holder(attempt / 'attempt.lock'), 'dispatch_lock': S.holder(root / 'dispatch.lock'),
            'result_status': result['status'] if result else None, 'authorises': []}


def finalise_interrupted(base, attempt_id, *, no_attempt_running, clock=S.now):
    """Record-only reconciliation run by the owner: writes an UNKNOWN result, sends nothing, removes no lock."""
    C.need(no_attempt_running is True, 'confirm that no process is still running this attempt')
    root, attempt = directories(base, attempt_id)
    C.need(attempt.is_dir() and not (attempt / 'result.json').exists(), 'no unreconciled attempt: it is unknown or already has a result')
    journal = S.Journal(attempt / 'journal.jsonl', clock)
    events, tail = journal.prefix()
    C.need((attempt / 'attempt.lock').exists() or any(e['type'] == 'ATTEMPT_CLAIMED' for e in events), 'the attempt was never claimed')
    request_raw = S.read(attempt / 'request.json')
    request = C.parse(request_raw, 'request')
    claimed = {e['record']['index']: e['record'] for e in events if e['type'] == 'REQUEST_CLAIMED'}
    finished = {e['record']['index']: e['record']['receipt_sha256'] for e in events if e['type'] == 'REQUEST_FINISHED'}
    received, retained = 0, []
    for index in sorted(finished):
        raw = S.read(attempt / 'receipts' / f'{index:03d}.json')
        C.need(S.sha(raw) == finished[index], f'RECEIPT_ALTERED: receipt {index} differs from the journal')
        received += C.parse(raw, 'receipt')['bytes_received']
    unfinished = []
    for index in sorted(set(claimed) - set(finished)):
        body = attempt / 'raw' / f'{index:03d}.body'
        kept = S.read(body) if body.exists() else None
        if kept is not None:
            received += len(kept)
            retained.append({'role': claimed[index]['role'], 'url': claimed[index]['url'], 'receipt_sha256': None,
                             'body_path': f'raw/{index:03d}.body', 'body_sha256': S.sha(kept), 'bytes': len(kept),
                             'http_status': None, 'coverage': 'UNKNOWN'})
        unfinished.append({**claimed[index], 'body_bytes_at_least': len(kept) if kept is not None else 0})
    # The remote effect of an unfinished request is unknown: its host is stopped, as for transport uncertainty.
    register, findings = T.register(base, clock), []
    for item in unfinished:
        findings.append(T.record(register, 'HOST', item['host'], None, 'INTERRUPTED_REQUEST', attempt_id, None, clock()))
    result = outcome_record(request, S.sha(request_raw), 'UNKNOWN', 'INTERRUPTED: finalised record-only by the owner; nothing was re-sent',
                            scope_sha256=request['authority']['scope']['sha256'], journal_head=events[-1]['hash'] if events else None,
                            receipts=[finished[i] for i in sorted(finished)], retained=retained, stop_findings=findings,
                            unfinished_requests=unfinished, interrupted=True, journal_sha256=S.sha(journal.bytes()),
                            consumption=consumption(len(claimed), not unfinished, received, not unfinished))
    S.write_new(attempt / 'result.json', result)
    return result
