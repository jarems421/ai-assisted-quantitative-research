"""One bounded exact-URL retrieval attempt: refuse, or claim and retrieve serially, then one immutable result.

Called by the campaign controller as a bounded activity. It never schedules, retries, resumes or calls another
component. External effects happen only through the transport, and only after a durable claim.

Every result is derived by one function, `derive`, from the attempt journal, the verified receipts and the
attempt's own input copies. The same function writes a result and verifies it, byte for byte. Each result is
anchored before it is written: by the journal (ATTEMPT_REFUSED / ATTEMPT_FINISHED) or, for an interrupted or
incompletely initialised attempt, by a create-only finalisation record. A receipt records facts; its
classification is recomputed from those facts on every verification.
"""
from __future__ import annotations

import hashlib
import ipaddress
import math
import os
import secrets
import time
from urllib import robotparser
from src.research.spec import canonical, digest
from src.research.quarry_v1 import io as Q
from src.research.quarry_v1.acquisition import plan as quarry_plan
from . import contracts as C, store as S, stops as T
from .transport import ROBOTS_AGENT, HttpsTransport

CHUNK = 64 * 1024
MAX_ANSWERS = 16
ROBOTS_MAX = 512 * 1024
HEADERS = ('content-type', 'content-length', 'content-encoding', 'transfer-encoding', 'last-modified', 'etag', 'date', 'location')
LIMITATIONS = ['Bytes are the representation served at retrieval time; historical publication and earlier versions are UNKNOWN.',
               'TLS authenticated the host at retrieval time only; source authenticity and correctness are UNKNOWN.',
               'No content was parsed, extracted or interpreted.']
EXTRA = {'DECLARED_SIZE': 'Declared length exceeds the ceiling; no body bytes were read.',
         'UNVERIFIED_LENGTH': 'The response had no length framing; completeness cannot be verified.',
         'PREFIX': 'The body is incomplete: only the retained prefix was received.',
         'UNEXPECTED_ENCODING': 'The body is content-encoded, not the identity representation requested; it was kept undecoded.',
         'FRAMING_CONFLICT': 'The response framing was contradictory; the body is not a verified representation.'}
PRECEDENCE = ('UNKNOWN', 'STOPPED', 'UNAVAILABLE', 'PARTIAL')
# termination -> (attempt flag, stop scope, ends the attempt)
OUTCOMES = {'COMPLETE': (None, None, False), 'UNVERIFIED_LENGTH': ('PARTIAL', None, False),
            'SIZE_STOP': ('PARTIAL', None, False), 'TIME_STOP': ('PARTIAL', None, False),
            'REDIRECT_REFUSED': ('STOPPED', 'ROUTE', True), 'ACCESS_DENIED': ('STOPPED', 'HOST', True),
            'RATE_LIMITED': ('STOPPED', 'HOST', True), 'NOT_FOUND': ('UNAVAILABLE', 'ROUTE', True),
            'UNEXPECTED_RESPONSE': ('STOPPED', 'HOST', True), 'UNEXPECTED_ENCODING': ('STOPPED', 'ROUTE', True),
            'FRAMING_CONFLICT': ('STOPPED', 'HOST', True), 'DNS_FAILED': ('STOPPED', None, True),
            'DEADLINE_EXCEEDED': ('STOPPED', None, True),
            'ADDRESS_REFUSED': ('STOPPED', 'HOST', True), 'TRANSPORT_FAILED': ('UNKNOWN', 'HOST', True)}
CUSTODY = ('COMPLETE', 'UNVERIFIED_LENGTH', 'SIZE_STOP', 'TIME_STOP')
INTERRUPTED = 'INTERRUPTED: finalised record-only by the owner; nothing was re-sent'
PRECLAIM = 'PRECLAIM_INCOMPLETE: initialisation was interrupted before the claim; nothing was dispatched'


# ---- pure classification ---------------------------------------------------------------------------------
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
    return 'UNEXPECTED_RESPONSE'  # Includes 204, 206 and every other non-200 success code.


def framing(headers):
    """(framing, declared length). Transfer-Encoding with Content-Length, other codings, or unequal or
    non-numeric lengths are a CONFLICT (RFC 9112 section 6.3)."""
    lengths = [v.strip() for k, v in headers if k.lower() == 'content-length']
    codings = ','.join(v for k, v in headers if k.lower() == 'transfer-encoding').lower().replace(' ', '')
    if codings:
        return ('CHUNKED', None) if codings == 'chunked' and not lengths else ('CONFLICT', None)
    if not lengths:
        return 'CLOSE_DELIMITED', None
    if len(set(lengths)) != 1 or not lengths[0].isdigit():
        return 'CONFLICT', None
    return 'CONTENT_LENGTH', int(lengths[0])


def terminate(r):
    """Termination recomputed from a receipt's recorded facts. Only a fully framed 200 is COMPLETE."""
    stage, status = r['stage'], r['http_status']
    if stage == 'DNS' and r['failure'] == 'DEADLINE_EXCEEDED':
        return 'DEADLINE_EXCEEDED'
    if stage != 'RESPONSE':
        return {'DNS': 'DNS_FAILED', 'ADDRESS': 'ADDRESS_REFUSED', 'CONNECT': 'TRANSPORT_FAILED'}[stage]
    if status is None:
        return 'TRANSPORT_FAILED'
    if status != 200:
        return by_status(status)
    if r['framing'] == 'CONFLICT':
        return 'FRAMING_CONFLICT'
    if r['content_encoding'] not in ('', 'identity'):
        return 'UNEXPECTED_ENCODING'
    if r['stopped_by'] in ('SIZE', 'DECLARED_SIZE'):
        return 'SIZE_STOP'
    if r['stopped_by'] == 'TIME':
        return 'TIME_STOP'
    if r['failure']:
        return 'TRANSPORT_FAILED'
    if r['framing'] == 'CONTENT_LENGTH':
        if r['bytes_received'] > r['declared_length']:
            return 'FRAMING_CONFLICT'
        return 'COMPLETE' if r['bytes_received'] == r['declared_length'] else 'TRANSPORT_FAILED'
    return 'COMPLETE' if r['framing'] == 'CHUNKED' else 'UNVERIFIED_LENGTH'


def classify(r):
    term = terminate(r)
    ok = r['http_status'] == 200
    coverage = ('COMPLETE' if term == 'COMPLETE' else 'UNVERIFIED' if term == 'UNVERIFIED_LENGTH'
                else 'PREFIX' if ok and r['bytes_received'] and term in ('SIZE_STOP', 'TIME_STOP', 'TRANSPORT_FAILED') else 'NONE')
    notes = list(LIMITATIONS)
    for key in ('DECLARED_SIZE' if r['stopped_by'] == 'DECLARED_SIZE' else None, term,
                'PREFIX' if ok and coverage == 'PREFIX' else None):
        if key in EXTRA:
            notes.append(EXTRA[key])
    return {**r, 'termination': term, 'complete': term == 'COMPLETE', 'coverage': coverage, 'limitations': notes}


def effect(role, r):
    """(robots kind, attempt flag, stop scope, reason, ends) for one receipt."""
    term, status = r['termination'], r['http_status']
    if role == 'ROBOTS':
        # RFC 9309 permits ignoring rules past 500 KiB, but an unread file is unresolved, never permissive.
        if term in ('COMPLETE', 'UNVERIFIED_LENGTH') or (term == 'SIZE_STOP' and r['bytes_received']):
            return 'RULES', None, None, None, False
        if status is not None and 400 <= status < 500 and status not in (401, 403, 429):
            return 'NO_RULES', None, None, None, False  # Unavailable robots.txt: no rules apply (RFC 9309 2.3.1.3).
        if term in ('TIME_STOP', 'SIZE_STOP'):
            return None, 'STOPPED', None, 'ROBOTS_UNRESOLVED', True
        flag, scope, ends = OUTCOMES[term]
        return None, flag, scope, 'ROBOTS_' + term, ends
    flag, scope, ends = OUTCOMES[term]
    return None, flag, scope, term, ends


def custody(r):
    return r['role'] == 'TARGET' and r['http_status'] == 200 and r['bytes_received'] > 0 and r['termination'] in CUSTODY


def robots(attempt, receipt):
    rules = robotparser.RobotFileParser()
    raw = S.read(attempt / receipt['body_path'], ROBOTS_MAX) if receipt and receipt['body_path'] else b''
    rules.parse(raw.decode('utf-8', 'replace').splitlines())
    return rules


def steps(request):
    out, seen = [], set()
    for url in request['authority']['tier_a']['exact_urls']:
        host = C.host_of(url)
        if host not in seen:
            seen.add(host)
            out.append(('ROBOTS', f'https://{host}/robots.txt', host))
        out.append(('TARGET', url, host))
    return out


def route_map(registry, quarry_scope):
    chosen, out = set(quarry_scope['route_ids']), {}
    for route in registry['routes']:
        if route['id'] in chosen:
            out.setdefault(route['locator'], []).append(route['id'])
    return out


def consumption(requests=0, exact=True, received=0, wall=0.0):
    count = lambda n: {'at_least': n, 'exact': n if exact else None}
    return {'requests': count(requests), 'bytes': count(received), 'wall_seconds': count(round(wall, 3)),
            'searches': {'at_least': 0, 'exact': 0}, 'model_calls': {'at_least': 0, 'exact': 0},
            'metered_micro_usd': {'reserved': 0, 'estimated': 0, 'actual': 0}, 'subscription_usage': 'NOT_USED'}


# ---- the single result derivation --------------------------------------------------------------------------
def derive(attempt, request, request_sha, events, receipts, kind, lookup, *, routes=None, journal_sha=None, refused=None):
    """The result an attempt's records imply. kind: FINISHED, REFUSED, INTERRUPTED or PRECLAIM_INCOMPLETE.

    events are the journal events the result accounts for (never its own anchor); receipts are verified
    (index, sha256, receipt) in finish order; lookup(core) returns the register record of a stop finding.
    """
    attempt_id = request['attempt_id']
    claim = next((e['record'] for e in events if e['type'] == 'ATTEMPT_CLAIMED'), None)
    claimed = {e['record']['index']: e['record'] for e in events if e['type'] == 'REQUEST_CLAIMED'}
    by_index = {i: (sha, r) for i, sha, r in receipts}
    flags, why, cores, rules, robots_sha, retained, handoff, unfinished = set(), None, {}, {}, {}, [], [], []
    for e in events:
        if e['type'] == 'REQUEST_FINISHED':
            sha, r = by_index[e['record']['index']]
            role, url, host = r['role'], r['requested_url'], r['host']
            if r['body_path']:
                retained.append({'role': role, 'url': url, 'receipt_sha256': sha, 'body_path': r['body_path'],
                                 'body_sha256': r['body_sha256'], 'bytes': r['bytes_received'],
                                 'http_status': r['http_status'], 'coverage': r['coverage']})
            rkind, flag, scope, reason, ends = effect(role, r)
            if rkind:
                rules[host], robots_sha[host] = robots(attempt, r if rkind == 'RULES' else None), sha
                continue
            if flag:
                flags.add(flag)
            if scope:
                core = T.finding(scope, host, url if scope == 'ROUTE' else None, reason, 'receipt', sha)
                cores.setdefault(core['stop_id'], core)
            if ends:
                why = why or reason
            elif custody(r):
                handoff.append({'receipt_sha256': sha, 'requested_url': url, 'quarry_route_id': (routes or {}).get(url, [None])[0],
                                'body_path': r['body_path'], 'body_sha256': r['body_sha256'], 'bytes': r['bytes_received'],
                                'coverage': r['coverage']})
        elif e['type'] == 'ROBOTS_DISALLOWED':
            x = e['record']
            core = T.finding('ROUTE', x['host'], x['url'], 'ROBOTS_DISALLOWED', 'receipt', x['robots_receipt_sha256'])
            cores.setdefault(core['stop_id'], core)
            flags.add('STOPPED')
            why = why or 'ROBOTS_DISALLOWED'
        elif e['type'] == 'BUDGET_EXHAUSTED':
            flags.add('STOPPED')
            why = why or 'BUDGET'
    claimed_steps = {(c['role'], c['url']) for c in claimed.values()}
    if kind == 'INTERRUPTED':
        for index in sorted(set(claimed) - set(by_index)):
            c = claimed[index]
            body, loose = attempt / 'raw' / f'{index:03d}.body', attempt / 'receipts' / f'{index:03d}.json'
            kept = S.read(body) if body.exists() else None
            if kept is not None:
                retained.append({'role': c['role'], 'url': c['url'], 'receipt_sha256': None, 'body_path': f'raw/{index:03d}.body',
                                 'body_sha256': S.sha(kept), 'bytes': len(kept), 'http_status': None, 'coverage': 'NONE'})
            unfinished.append({**c, 'body_bytes_at_least': len(kept) if kept is not None else 0,
                               'unbound_receipt_sha256': S.sha(S.read(loose)) if loose.exists() else None})
            # The remote effect of an unfinished request is unknown: its host is stopped, as for transport uncertainty.
            core = T.finding('HOST', c['host'], None, 'INTERRUPTED_REQUEST', f'attempt {attempt_id} request {index}', None)
            cores.setdefault(core['stop_id'], core)
        for role, url, host in steps(request):  # A robots decision a crash may have kept from being recorded.
            if role == 'TARGET' and host in rules and (role, url) not in claimed_steps and not rules[host].can_fetch(ROBOTS_AGENT, url):
                core = T.finding('ROUTE', host, url, 'ROBOTS_DISALLOWED', 'receipt', robots_sha[host])
                cores.setdefault(core['stop_id'], core)
        status, why = 'UNKNOWN', INTERRUPTED
    elif kind == 'PRECLAIM_INCOMPLETE':
        status, why = 'NOT_STARTED', PRECLAIM
    elif kind == 'REFUSED':
        status, why = 'NOT_STARTED', refused['reason']
    else:
        status, why = next((s for s in PRECEDENCE if s in flags), 'COMPLETE'), why or 'ALL_REQUESTS_FINISHED'
    started = claim is not None
    exact = not unfinished
    received = sum(r['bytes_received'] for _, _, r in receipts) + sum(u['body_bytes_at_least'] for u in unfinished)
    wall = 0.0
    if started:
        claimed_at = next(e['at'] for e in events if e['type'] == 'ATTEMPT_CLAIMED')
        wall = (C.moment(events[-1]['at'], 'journal time') - C.moment(claimed_at, 'journal time')).total_seconds()
    implementation = claim['implementation_sha256'] if claim else (refused['implementation_sha256'] if refused else None)
    return {'schema': C.RESULT, 'request_sha256': request_sha, 'attempt_id': attempt_id, 'campaign_id': request['campaign_id'],
            'branch_id': request['branch_id'], 'request_id': request['request_id'], 'caller_ref': request['caller_ref'],
            'scope_sha256': request['authority']['scope']['sha256'], 'journal_head': events[-1]['hash'] if events else None,
            'status': status, 'reason': why, 'receipts': [sha for _, sha, _ in receipts], 'retained': retained,
            'stop_findings': [lookup(core) for core in cores.values()], 'host_pending': [], 'field_support_proposals': [],
            'custody_handoff': handoff,
            'not_attempted': [url for role, url, _ in steps(request) if (role, url) not in claimed_steps] if started or claimed else [],
            'unfinished_requests': unfinished, 'consumption': consumption(len(claimed), exact, received, wall),
            'interrupted': kind in ('INTERRUPTED', 'PRECLAIM_INCOMPLETE'), 'journal_sha256': journal_sha,
            'implementation_sha256': implementation, 'exactly_once': False, 'authorises': []}


# ---- pre-claim -------------------------------------------------------------------------------------------
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
    registry, quarry_scope = C.parse(raws['quarry_registry'], 'Quarry registry'), C.parse(raws['quarry_scope'], 'Quarry scope')
    C.need(plan['registry_sha256'] == digest(registry) and plan['scope_sha256'] == digest(quarry_scope),
           'QUARRY_INPUT_CHANGED: Quarry files changed while being checked')
    q, tier = plan['scope'], a['tier_a']
    C.need(set(tier['exact_urls']) == set(q['exact_urls']) and set(tier['hosts']) == set(q['allowed_hosts']),
           'SCOPE_VIOLATION: request URLs or hosts differ from the owner-approved Quarry scope')
    routes = route_map(registry, quarry_scope)
    C.need(all(len(routes.get(u, [])) == 1 for u in tier['exact_urls']),
           'ROUTE_AMBIGUOUS: each exact URL must map to exactly one approved Quarry route')
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
    return {'scope_raw': scope_raw, 'quarry': q, 'raws': raws, 'snapshot_raw': snapshot_raw, 'routes': routes}


def check(request_path, base=None, clock=S.now):
    """Read-only preflight: the refusal reason run would record now, or None. Informational, never authority."""
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
            'refusal': reason, 'implementation_sha256': S.implementation(), 'external_requests_started': 0,
            'informational_only': True, 'authorises': []}


def create(attempt, raw):
    """The attempt directory appears atomically with its exact request; a leftover staging folder is inert."""
    staging = attempt.parent / f'.staging-{attempt.name}-{secrets.token_hex(4)}'
    staging.mkdir(parents=True)
    S.write_new(staging / 'request.json', raw)
    os.rename(staging, attempt)
    return S.sha(raw)


# ---- the attempt -----------------------------------------------------------------------------------------
def run(request_path, base=None, *, transport=None, clock=S.now, ticks=time.monotonic, sleep=time.sleep):
    raw, request = S.load(request_path, 'source request')
    C.request(request)  # Invalid requests fail here: no lock, no attempt.
    root, attempt = directories(base, request['attempt_id'])
    dispatch = root / 'dispatch.lock'
    C.need(S.acquire(dispatch, {'attempt_id': request['attempt_id'], 'at': clock()}),
           'DISPATCH_LOCKED: another attempt is running or was interrupted; reconcile it before any new attempt')
    created = False
    try:
        ledger = S.Journal(root / 'ledger.jsonl', clock)
        events = ledger.load()
        C.need(not attempt.exists() and not any(e['record'].get('attempt_id') == request['attempt_id'] for e in events),
               'DUPLICATE_ATTEMPT: this attempt id was already used; a new attempt needs a new id from the campaign')
        request_sha = create(attempt, raw)
        created = True  # From here only a clean refusal or a clean finish releases the dispatch lock.
        journal = S.Journal(attempt / 'journal.jsonl', clock)
        try:
            ctx = authorise(request, base, events, C.moment(clock(), 'clock'))
        except ValueError as error:
            refused = {'reason': str(error), 'implementation_sha256': S.implementation()}
            data = S.encode(derive(attempt, request, request_sha, [], [], 'REFUSED', None, refused=refused))
            journal.append('ATTEMPT_REFUSED', {**refused, 'result_sha256': S.sha(data)})
            S.write_new(attempt / 'result.json', data)
            S.release(dispatch)
            return C.parse(data, 'result')
        for name, data in (('scope.json', ctx['scope_raw']), ('quarry-registry.json', ctx['raws']['quarry_registry']),
                           ('quarry-scope.json', ctx['raws']['quarry_scope']), ('stop-snapshot.json', ctx['snapshot_raw'])):
            S.write_new(attempt / 'inputs' / name, data)
        C.need(S.acquire(attempt / 'attempt.lock', {'attempt_id': request['attempt_id'], 'at': clock()}), 'attempt locked')
        reservation, scope_sha = request['resources']['reservation'], request['authority']['scope']['sha256']
        ledger.append('ATTEMPT_RESERVED', {'attempt_id': request['attempt_id'], 'request_sha256': request_sha,
                                           'scope_sha256': scope_sha, 'reservation': reservation})
        journal.append('ATTEMPT_CLAIMED', {'request_sha256': request_sha, 'scope_sha256': scope_sha, 'reservation': reservation,
                                           'snapshot_sha256': request['stops']['snapshot']['sha256'],
                                           'implementation_sha256': S.implementation()})
        register = T.register(base, clock)
        retrieve(request, ctx, attempt, journal, ledger, register, transport or HttpsTransport(), clock, ticks, sleep)
        events = journal.load()
        result = derive(attempt, request, request_sha, events, receipts_of(attempt, events), 'FINISHED',
                        lambda core: T.ensure(register, core, request['attempt_id'], clock), routes=ctx['routes'])
        data = S.encode(result)
        journal.append('ATTEMPT_FINISHED', {'result_sha256': S.sha(data)})
        S.write_new(attempt / 'result.json', data)
    except BaseException:
        if not created:
            S.release(dispatch)
        raise  # Once the attempt exists, locks stay: PRECLAIM_INCOMPLETE or INTERRUPTED until reconciled.
    S.release(attempt / 'attempt.lock')
    S.release(dispatch)
    return result


def pause(ledger, interval, clock):
    """Seconds to wait so that consecutive dispatches, across all attempts, are at least interval apart."""
    last = next((e['at'] for e in reversed(ledger.load()) if e['type'] == 'REQUEST_DISPATCHING'), None)
    if not last:
        return 0.0
    return max(0.0, interval - (C.moment(clock(), 'clock') - C.moment(last, 'ledger time')).total_seconds())


def retrieve(request, ctx, attempt, journal, ledger, register, transport, clock, ticks, sleep):
    """Dispatch serially and record events; the result is derived afterwards from what was recorded."""
    r, q, attempt_id = request['resources']['reservation'], ctx['quarry'], request['attempt_id']
    start, used, index, rules, robots_sha = ticks(), 0, 0, {}, {}

    def stop(core):
        T.ensure(register, core, attempt_id, clock)
        journal.append('STOP_FOUND', {'stop_id': core['stop_id'], 'reason': core['reason']})

    def exhausted(requests, received, elapsed, wait):
        journal.append('BUDGET_EXHAUSTED', {'requests': requests, 'bytes': received, 'wall_seconds': round(elapsed, 3),
                                            'required_wait_seconds': round(wait, 3)})

    for role, url, host in steps(request):
        if role == 'TARGET' and not rules[host].can_fetch(ROBOTS_AGENT, url):
            journal.append('ROBOTS_DISALLOWED', {'url': url, 'host': host, 'robots_receipt_sha256': robots_sha[host]})
            stop(T.finding('ROUTE', host, url, 'ROBOTS_DISALLOWED', 'receipt', robots_sha[host]))
            return
        delay = rules[host].crawl_delay(ROBOTS_AGENT) if role == 'TARGET' else None
        wait = pause(ledger, max(float(q['minimum_interval_seconds']), float(delay or 0)), clock)
        elapsed, remaining = ticks() - start, r['total_bytes'] - used
        if index >= r['requests'] or remaining <= 0 or elapsed + wait >= r['wall_seconds']:
            return exhausted(index, used, elapsed, wait)
        if wait:
            sleep(wait)
            elapsed = ticks() - start
            if elapsed >= r['wall_seconds']:  # The sleep overran: never start a request once the budget has expired.
                return exhausted(index, used, elapsed, wait)
        index += 1
        cap = min(r['per_response_bytes'], remaining, ROBOTS_MAX if role == 'ROBOTS' else r['per_response_bytes'])
        journal.append('REQUEST_CLAIMED', {'index': index, 'role': role, 'url': url, 'host': host})
        ledger.append('REQUEST_DISPATCHING', {'attempt_id': attempt_id, 'index': index, 'host': host})
        receipt = fetch(transport, attempt, attempt_id, index, role, url, host, cap,
                        min(q['timeout_seconds'], r['wall_seconds'] - elapsed), clock, ticks)
        sha = S.write_new(attempt / 'receipts' / f'{index:03d}.json', receipt)
        journal.append('REQUEST_FINISHED', {'index': index, 'receipt_sha256': sha})
        used += receipt['bytes_received']
        rkind, _, scope, reason, ends = effect(role, receipt)
        if rkind:
            rules[host], robots_sha[host] = robots(attempt, receipt if rkind == 'RULES' else None), sha
            continue
        if scope:
            stop(T.finding(scope, host, url if scope == 'ROUTE' else None, reason, 'receipt', sha))
        if ends:
            return


def fetch(transport, attempt, attempt_id, index, role, url, host, cap, deadline, clock, ticks):
    r = {'schema': C.RECEIPT, 'attempt_id': attempt_id, 'request_index': index, 'role': role, 'requested_url': url, 'host': host,
         'tier': 'A', 'stage': 'DNS', 'resolved_addresses': [], 'connected_address': None, 'started_at': clock(),
         'finished_at': None, 'http_status': None, 'headers_sha256': None, 'headers_selected': {}, 'framing': None,
         'content_encoding': None, 'declared_length': None, 'bytes_received': 0, 'body_sha256': None, 'body_path': None,
         'stopped_by': None, 'failure': None, 'max_bytes': cap, 'implementation_sha256': S.implementation()}

    def done(failure=None):
        r.update(failure=failure, finished_at=clock())
        return classify(r)

    began = ticks()  # The request deadline includes DNS resolution.
    try:
        answers = transport.resolve(host)
    except Exception as error:  # Exception text is never recorded, only its type.
        return done(type(error).__name__)
    if not isinstance(answers, (list, tuple)) or not all(isinstance(a, str) and 0 < len(a) <= 64 for a in answers):
        return done('MALFORMED_DNS_ANSWER')
    if not answers:
        return done('NO_ADDRESS')
    # Every answer is validated before anything is truncated: a forbidden one anywhere refuses the host.
    forbidden = [a for a in answers if not public(a)]
    if forbidden:
        r['stage'], r['resolved_addresses'] = 'ADDRESS', (forbidden[:1] + [a for a in answers if a != forbidden[0]])[:MAX_ANSWERS]
        return done('NON_PUBLIC_ADDRESS')
    if len(answers) > MAX_ANSWERS:
        return done('OVERSIZED_DNS_ANSWER')
    if ticks() - began >= deadline:  # Slow resolution: never connect once the request's time has expired.
        return done('DEADLINE_EXCEEDED')
    r['stage'], r['resolved_addresses'], r['connected_address'] = 'CONNECT', list(answers), answers[0]
    try:
        response = transport.open(url, host, answers[0], max(1, math.ceil(deadline - (ticks() - began))))
    except Exception as error:
        return done(type(error).__name__)
    try:
        r['stage'] = 'RESPONSE'
        status = response.status if isinstance(response.status, int) and 100 <= response.status <= 999 else None
        headers = [[str(k), str(v)] for k, v in response.headers]
        selected = {}
        for k, v in headers:
            if k.lower() in HEADERS and k.lower() not in selected:
                selected[k.lower()] = v[:2048]
        kind, declared = framing(headers)
        encoding = ','.join(v for k, v in headers if k.lower() == 'content-encoding').strip().lower()[:256]
        r.update(http_status=status, headers_sha256=S.sha(canonical(headers)), headers_selected=selected, framing=kind,
                 content_encoding=encoding, declared_length=declared)
        if status == 200 and declared is not None and declared > cap:
            r['stopped_by'] = 'DECLARED_SIZE'
            return done()
        relative = f'raw/{index:03d}.body'
        (attempt / 'raw').mkdir(exist_ok=True)
        hasher, total, failure = hashlib.sha256(), 0, None
        with Q.safe_path(attempt / relative).open('xb') as out:
            try:
                while True:
                    if ticks() - began > deadline:
                        r['stopped_by'] = 'TIME'
                        break
                    chunk = response.read(min(CHUNK, cap - total + 1))
                    if not chunk:
                        break
                    if total + len(chunk) > cap:
                        chunk, r['stopped_by'] = chunk[:cap - total], 'SIZE'
                    out.write(chunk)
                    hasher.update(chunk)
                    total += len(chunk)
                    if r['stopped_by']:
                        break
            except Exception as error:
                failure = type(error).__name__
            out.flush()
            os.fsync(out.fileno())
        r.update(body_path=relative, bytes_received=total, body_sha256=hasher.hexdigest())
        if not failure and not r['stopped_by'] and kind == 'CONTENT_LENGTH' and total < declared:
            failure = 'INCOMPLETE_BODY'
        if status is None:
            failure = failure or 'NO_STATUS'
        return done(failure)
    finally:
        try:
            response.close()
        except Exception:
            pass


# ---- read-only verification and record-only reconciliation ----------------------------------------------
def check_receipt(attempt, attempt_id, index, claim, raw, expected_sha):
    C.need(S.sha(raw) == expected_sha, f'RECEIPT_ALTERED: receipt {index} differs from the journal')
    r = C.parse(raw, 'receipt')
    try:
        C.validate(C.RECEIPT_SCHEMA, r)
    except ValueError as error:
        raise C.SourceError(f'RECEIPT_MALFORMED: receipt {index}: {error}') from error
    C.need((r['attempt_id'], r['request_index'], r['role'], r['requested_url'], r['host'])
           == (attempt_id, index, claim['role'], claim['url'], claim['host']), f'RECEIPT_INCONSISTENT: receipt {index} identity')
    C.need({k: r[k] for k in ('termination', 'complete', 'coverage', 'limitations')}
           == {k: v for k, v in classify(r).items() if k in ('termination', 'complete', 'coverage', 'limitations')},
           f'RECEIPT_INCONSISTENT: receipt {index} classification differs from its recorded facts')
    resolved, stage = r['resolved_addresses'], r['stage']
    C.need((stage == 'DNS' and not resolved and r['connected_address'] is None)
           or (stage == 'ADDRESS' and resolved and not all(public(a) for a in resolved) and r['connected_address'] is None)
           or (stage in ('CONNECT', 'RESPONSE') and resolved and all(public(a) for a in resolved) and r['connected_address'] == resolved[0]),
           f'RECEIPT_INCONSISTENT: receipt {index} addresses')
    C.need(stage == 'RESPONSE' or (r['http_status'] is None and r['body_path'] is None and r['framing'] is None),
           f'RECEIPT_INCONSISTENT: receipt {index} has response facts without a response')
    C.need(r['bytes_received'] <= r['max_bytes'] and (r['stopped_by'] != 'SIZE' or r['bytes_received'] == r['max_bytes'])
           and (r['stopped_by'] != 'DECLARED_SIZE' or (r['body_path'] is None and r['declared_length'] > r['max_bytes'])),
           f'RECEIPT_INCONSISTENT: receipt {index} byte ceiling')
    if r['body_path'] is None:
        C.need(r['bytes_received'] == 0 and r['body_sha256'] is None, f'RECEIPT_INCONSISTENT: receipt {index} body')
    else:
        C.need(r['body_path'] == f'raw/{index:03d}.body', f'RECEIPT_INCONSISTENT: receipt {index} body path')
        body = S.read(attempt / r['body_path'])
        C.need(S.sha(body) == r['body_sha256'] and len(body) == r['bytes_received'], f'BODY_ALTERED: retained body {index} differs from its receipt')
    return r


def receipts_of(attempt, events):
    attempt_id = attempt.name
    claimed = {e['record']['index']: e['record'] for e in events if e['type'] == 'REQUEST_CLAIMED'}
    out = []
    for e in events:
        if e['type'] == 'REQUEST_FINISHED':
            index = e['record']['index']
            C.need(index in claimed and index not in [i for i, _, _ in out], f'JOURNAL_INCONSISTENT: request {index}')
            raw = S.read(attempt / 'receipts' / f'{index:03d}.json')
            out.append((index, S.sha(raw), check_receipt(attempt, attempt_id, index, claimed[index], raw, e['record']['receipt_sha256'])))
    return out


def recorded_routes(attempt):
    registry, quarry_scope = attempt / 'inputs' / 'quarry-registry.json', attempt / 'inputs' / 'quarry-scope.json'
    if not (registry.exists() and quarry_scope.exists()):
        return {}
    return route_map(C.parse(S.read(registry), 'registry copy'), C.parse(S.read(quarry_scope), 'Quarry scope copy'))


def readonly(base):
    existing = {f['stop_id']: f for f in T.findings(base)}

    def lookup(core):
        record = existing.get(core['stop_id'])
        C.need(record is not None and all(record.get(k) == v for k, v in core.items()),
               f"STOP_FINDING_MISSING: {core['stop_id']} ({core['reason']}) is not in the stop register")
        return record
    return lookup


def examine(base, attempt_id):
    """Everything verification and reconciliation need; raises ValueError on any inconsistency."""
    root, attempt = directories(base, attempt_id)
    C.need(attempt.is_dir(), 'unknown attempt')
    request_raw = S.read(attempt / 'request.json')
    request = C.parse(request_raw, 'request')
    C.request(request)
    C.need(request['attempt_id'] == attempt_id, 'REQUEST_INCONSISTENT: attempt id')
    journal = S.Journal(attempt / 'journal.jsonl')
    events, tail = journal.prefix()
    ledger = S.Journal(root / 'ledger.jsonl').load()
    claimed = ((attempt / 'attempt.lock').exists() or any(e['type'] == 'ATTEMPT_CLAIMED' for e in events)
               or any(e['type'] == 'ATTEMPT_RESERVED' and e['record']['attempt_id'] == attempt_id for e in ledger))
    anchor = events[-1] if events and not tail and events[-1]['type'] in ('ATTEMPT_FINISHED', 'ATTEMPT_REFUSED') else None
    return {'attempt': attempt, 'request': request, 'request_sha': S.sha(request_raw), 'journal_raw': journal.bytes(),
            'events': events, 'tail': tail, 'claimed': claimed, 'anchor': anchor}


def verify(base, attempt_id):
    """(state, result, notes). Read-only: re-derives the result and compares it byte for byte; never repairs."""
    x = examine(base, attempt_id)
    attempt, events = x['attempt'], x['events']
    result_path, final_path = attempt / 'result.json', attempt / 'finalisation.json'
    journal_sha = refused = None
    if final_path.exists():
        C.need(x['anchor'] is None, 'FINALISATION_CONFLICT: a journal-anchored attempt also has a finalisation record')
        final = C.parse(S.read(final_path), 'finalisation')
        try:
            C.validate(C.FINALISATION_SCHEMA, final)
        except ValueError as error:
            raise C.SourceError('FINALISATION_MALFORMED: ' + str(error)) from error
        C.need(final['attempt_id'] == attempt_id and final['request_sha256'] == x['request_sha']
               and final['journal_sha256'] == S.sha(x['journal_raw']) and final['journal_bytes'] == len(x['journal_raw'])
               and final['journal_events'] == len(events) and final['incomplete_tail_bytes'] == len(x['tail'])
               and final['journal_head'] == (events[-1]['hash'] if events else None),
               'JOURNAL_ALTERED: the journal differs from the one bound at finalisation')
        C.need((final['kind'] == 'INTERRUPTED') == x['claimed'], 'FINALISATION_INCONSISTENT: claim state')
        kind, accounted, expected_sha, journal_sha = final['kind'], events, final['result_sha256'], final['journal_sha256']
    elif x['anchor']:
        kind = 'FINISHED' if x['anchor']['type'] == 'ATTEMPT_FINISHED' else 'REFUSED'
        C.need((kind == 'FINISHED') == x['claimed'], 'JOURNAL_INCONSISTENT: claim state')
        accounted, expected_sha = events[:-1], x['anchor']['record']['result_sha256']
        refused = x['anchor']['record'] if kind == 'REFUSED' else None
    else:
        C.need(not result_path.exists(), 'RESULT_UNANCHORED: a result exists without a journal anchor or finalisation record')
        state = 'INTERRUPTED' if x['claimed'] else 'PRECLAIM_INCOMPLETE'
        return state, None, ['no result: reconcile with finalise-interrupted'] + (['incomplete journal tail'] if x['tail'] else [])
    receipts = receipts_of(attempt, accounted) if kind in ('FINISHED', 'INTERRUPTED') else []
    C.need(kind in ('FINISHED', 'INTERRUPTED') or not any(e['type'] != 'ATTEMPT_REFUSED' for e in events),
           'JOURNAL_INCONSISTENT: a not-started attempt has dispatch events')
    expected = derive(attempt, x['request'], x['request_sha'], accounted, receipts, kind, readonly(base),
                      routes=recorded_routes(attempt) if receipts else {}, journal_sha=journal_sha, refused=refused)
    data = S.encode(expected)
    C.need(S.sha(data) == expected_sha, 'RESULT_ALTERED: the result its records imply differs from its anchor')
    if not result_path.exists():
        return 'RESULT_PENDING', expected, ['anchored result not yet written; finalise-interrupted writes it']
    C.need(S.read(result_path) == data, 'RESULT_ALTERED: result bytes differ from the result its records imply')
    return expected['status'], expected, []


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
            'finalised': (attempt / 'finalisation.json').exists(),
            'attempt_lock': S.holder(attempt / 'attempt.lock'), 'dispatch_lock': S.holder(root / 'dispatch.lock'),
            'result_status': result['status'] if result else None, 'authorises': []}


def finalise_interrupted(base, attempt_id, *, no_attempt_running, clock=S.now):
    """Record-only reconciliation run by the owner. Sends nothing and removes no lock; repeating it adds nothing.

    An interrupted attempt gets an UNKNOWN result, and an attempt interrupted before its claim a NOT_STARTED one.
    Stop findings its verified receipts imply are recorded if a crash lost them. The finalisation record binds
    the exact result bytes and the journal as found (any incomplete tail included, never truncated).
    """
    C.need(no_attempt_running is True, 'confirm that no process is still running this attempt')
    try:
        state, result, _ = verify(base, attempt_id)
    except ValueError as error:
        raise C.SourceError('INCONSISTENT: ' + str(error) + '; nothing was written, reconcile by hand') from error
    _, attempt = directories(base, attempt_id)
    if state == 'RESULT_PENDING':
        S.write_new(attempt / 'result.json', S.encode(result))
        return result
    if result is not None:
        return result
    x = examine(base, attempt_id)
    kind = 'INTERRUPTED' if state == 'INTERRUPTED' else 'PRECLAIM_INCOMPLETE'
    receipts = receipts_of(attempt, x['events']) if kind == 'INTERRUPTED' else []
    register = T.register(base, clock)
    result = derive(attempt, x['request'], x['request_sha'], x['events'], receipts, kind,
                    lambda core: T.ensure(register, core, attempt_id, clock), routes=recorded_routes(attempt) if receipts else {},
                    journal_sha=S.sha(x['journal_raw']))
    data = S.encode(result)
    events = x['events']
    S.write_new(attempt / 'finalisation.json', {
        'schema': C.FINALISATION, 'attempt_id': attempt_id, 'kind': kind, 'result_sha256': S.sha(data),
        'request_sha256': x['request_sha'], 'journal_sha256': S.sha(x['journal_raw']), 'journal_bytes': len(x['journal_raw']),
        'journal_events': len(events), 'journal_head': events[-1]['hash'] if events else None,
        'incomplete_tail_bytes': len(x['tail']), 'finalised_at': clock(), 'authorises': []})
    S.write_new(attempt / 'result.json', data)
    return result
