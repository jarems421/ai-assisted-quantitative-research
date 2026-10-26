"""V001 request, owner scope and stop attestation contracts. UNKNOWN is data, never a verified fact."""
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlsplit
from src.research.jev_navigation_v1.contracts import TEXT, HASH, LABEL, obj, array, validate, loads
from src.research.quarry_v1.acquisition import public_locator

REQUEST = 'RESEARCH_OS_PROVISIONAL_SOURCE_REQUEST_V001'
SCOPE = 'SOURCE_RETRIEVAL_SCOPE_V001'
ATTESTATION = 'SOURCE_STOP_ATTESTATION_V001'
SNAPSHOT = 'SOURCE_STOP_SNAPSHOT_V001'
FINDING = 'SOURCE_STOP_FINDING_V001'
RECEIPT = 'SOURCE_RETRIEVAL_RECEIPT_V001'
RESULT = 'SOURCE_ACTIVITY_RESULT_V001'
FINALISATION = 'SOURCE_ATTEMPT_FINALISATION_V001'
STATUS = 'SOURCE_ATTEMPT_STATUS_V001'
STATUSES = ('NOT_STARTED', 'COMPLETE', 'PARTIAL', 'UNAVAILABLE', 'STOPPED', 'UNKNOWN')
TERMINATIONS = ('COMPLETE', 'UNVERIFIED_LENGTH', 'SIZE_STOP', 'TIME_STOP', 'REDIRECT_REFUSED', 'ACCESS_DENIED', 'RATE_LIMITED',
                'NOT_FOUND', 'UNEXPECTED_RESPONSE', 'UNEXPECTED_ENCODING', 'FRAMING_CONFLICT', 'DNS_FAILED', 'ADDRESS_REFUSED',
                'TRANSPORT_FAILED')
# Coverage of the requested representation: only a verified, fully framed 200 body is COMPLETE.
COVERAGES = ('COMPLETE', 'UNVERIFIED', 'PREFIX', 'NONE')
UNRESERVED = re.compile(r'%(2[DdEe]|3[0-9]|[46][1-9A-Fa-f]|[57][0-9Aa]|5[Ff]|7[Ee])')
OPERATION = 'RETRIEVE_EXACT_URL'
ROBOTS_POLICY = 'ROBOTS_TXT_REQUIRED'
# Same names refused for human attestations elsewhere (graph pilot, exploratory runner).
ASSISTANT = re.compile(r'\b(claude|assistant|codex|chatgpt|gpt|copilot|gemini|llm|jev|typesafe|ai agent|bot)\b', re.I)
MAX_BYTES = 16 * 1024 * 1024

IDENT = {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$'}
FILE = obj({'path': TEXT, 'sha256': HASH})
NONE_OR_TEXT = {'anyOf': [TEXT, {'type': 'null'}]}
EMPTY = {'type': 'array', 'maxItems': 0}
REQUIREMENT = obj({'id': LABEL, 'role': {'enum': ['PREDICTOR', 'OUTCOME', 'CONTEXT']}, 'quantity': TEXT, 'unit': TEXT,
                   'denominator': TEXT, 'population': TEXT, 'period': TEXT, 'join': TEXT})
# Searches, model calls and metered spend do not exist in V001; their reservations are fixed at zero.
RESERVATION = obj({'requests': {'type': 'integer', 'minimum': 1, 'maximum': 32},
                   'total_bytes': {'type': 'integer', 'minimum': 1, 'maximum': MAX_BYTES},
                   'per_response_bytes': {'type': 'integer', 'minimum': 1, 'maximum': MAX_BYTES},
                   'wall_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 3600},
                   'searches': {'const': 0}, 'model_calls': {'const': 0}, 'metered_micro_usd': {'const': 0}})
REQUEST_SCHEMA = obj({
    'schema': {'const': REQUEST}, 'campaign_id': IDENT, 'branch_id': IDENT,
    'subject': obj({'archive_sha256': HASH, 'card_id': LABEL, 'card_version': {'type': 'integer', 'minimum': 1}, 'card_sha256': HASH}),
    'request_id': IDENT, 'attempt_id': IDENT,
    'question': obj({'text': TEXT, 'requirements': array(REQUIREMENT, 32)}),
    'authority': obj({'scope': FILE, 'operations': {'type': 'array', 'items': {'const': OPERATION}, 'minItems': 1, 'maxItems': 1},
                      'transmission': {'const': 'NONE'},
                      'tier_a': obj({'exact_urls': {**array(TEXT, 32), 'minItems': 1}, 'hosts': {**array(TEXT, 32), 'minItems': 1}}),
                      'tier_b_classes': EMPTY, 'host_amendments': EMPTY}),
    'stops': obj({'snapshot': FILE}),
    'resources': obj({'campaign_allocation_ref': NONE_OR_TEXT, 'reservation': RESERVATION}),
    'caller_ref': NONE_OR_TEXT})
SCOPE_SCHEMA = obj({
    'schema': {'const': SCOPE}, 'owner': TEXT, 'decided_at': TEXT, 'valid_until': TEXT,
    'campaign_id': IDENT, 'branch_id': IDENT, 'card_sha256': HASH, 'implementation_sha256': HASH,
    'quarry_registry': FILE, 'quarry_scope': FILE,
    'operations': {'type': 'array', 'items': {'const': OPERATION}, 'minItems': 1, 'maxItems': 1},
    'transmission': {'const': 'NONE'}, 'robots_policy': {'const': ROBOTS_POLICY}, 'access_terms_reviewed': TEXT,
    # Cumulative over every attempt under this scope; reservations are never released.
    'attempt_ceiling': {'type': 'integer', 'minimum': 1, 'maximum': 8},
    'total_requests': {'type': 'integer', 'minimum': 1, 'maximum': 256},
    'total_bytes': {'type': 'integer', 'minimum': 1, 'maximum': 8 * MAX_BYTES}})
RESOLUTION = obj({'input_sha256': HASH, 'hosts': array(TEXT, 64), 'routes': array(TEXT, 64), 'task_scoped_reason': NONE_OR_TEXT})
DOCUMENTED = obj({'host': TEXT, 'route': NONE_OR_TEXT, 'reason': TEXT, 'citation': TEXT})
ATTESTATION_SCHEMA = obj({
    'schema': {'const': ATTESTATION}, 'attested_by': TEXT, 'attested_at': TEXT,
    'inputs': array(HASH, 512), 'resolutions': array(RESOLUTION, 512), 'documented_stops': array(DOCUMENTED, 512),
    'statement': {'const': 'I reviewed the listed stop records and the reports available to me. Unclear scopes are recorded host-level.'}})


NONE_OR_HASH = {'anyOf': [HASH, {'type': 'null'}]}
NONE_OR_INT = {'anyOf': [{'type': 'integer', 'minimum': 0}, {'type': 'null'}]}
RECEIPT_SCHEMA = obj({
    'schema': {'const': RECEIPT}, 'attempt_id': IDENT, 'request_index': {'type': 'integer', 'minimum': 1, 'maximum': 32},
    'role': {'enum': ['ROBOTS', 'TARGET']}, 'requested_url': TEXT, 'host': TEXT, 'tier': {'const': 'A'},
    'stage': {'enum': ['DNS', 'ADDRESS', 'CONNECT', 'RESPONSE']},
    'resolved_addresses': {'type': 'array', 'items': {'type': 'string', 'maxLength': 64}, 'maxItems': 16},
    'connected_address': {'anyOf': [{'type': 'string', 'maxLength': 64}, {'type': 'null'}]},
    'started_at': TEXT, 'finished_at': TEXT, 'http_status': {'anyOf': [{'type': 'integer', 'minimum': 100, 'maximum': 999}, {'type': 'null'}]},
    'headers_sha256': NONE_OR_HASH, 'headers_selected': {'type': 'object', 'additionalProperties': {'type': 'string', 'maxLength': 2048}, 'maxProperties': 8},
    'framing': {'enum': ['CONTENT_LENGTH', 'CHUNKED', 'CLOSE_DELIMITED', 'CONFLICT', None]},
    'content_encoding': {'anyOf': [{'type': 'string', 'maxLength': 256}, {'type': 'null'}]},
    'declared_length': NONE_OR_INT, 'bytes_received': {'type': 'integer', 'minimum': 0, 'maximum': MAX_BYTES},
    'body_sha256': NONE_OR_HASH, 'body_path': NONE_OR_TEXT, 'stopped_by': {'enum': ['SIZE', 'DECLARED_SIZE', 'TIME', None]},
    'failure': {'anyOf': [LABEL, {'type': 'null'}]}, 'termination': {'enum': list(TERMINATIONS)}, 'complete': {'type': 'boolean'},
    'coverage': {'enum': list(COVERAGES)}, 'max_bytes': {'type': 'integer', 'minimum': 0, 'maximum': MAX_BYTES},
    'limitations': {'type': 'array', 'items': TEXT, 'maxItems': 8}, 'implementation_sha256': HASH})
FINALISATION_SCHEMA = obj({
    'schema': {'const': FINALISATION}, 'attempt_id': IDENT, 'kind': {'enum': ['INTERRUPTED', 'PRECLAIM_INCOMPLETE']},
    'result_sha256': HASH, 'request_sha256': HASH, 'journal_sha256': HASH, 'journal_bytes': {'type': 'integer', 'minimum': 0},
    'journal_events': {'type': 'integer', 'minimum': 0}, 'journal_head': NONE_OR_HASH, 'incomplete_tail_bytes': {'type': 'integer', 'minimum': 0},
    'finalised_at': TEXT, 'authorises': EMPTY})


class SourceError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise SourceError(message)


def human(name, what):
    need(isinstance(name, str) and name.strip() and name.strip().upper() not in ('UNKNOWN', 'OWNER', 'HUMAN')
         and not ASSISTANT.search(name), f'{what} must be a named human; assistant or placeholder names are refused')
    return name


def moment(text, what):
    try:
        value = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        value = None
    need(value is not None and value.tzinfo is not None, f'{what} must be an ISO 8601 time with a UTC offset')
    return value


def host_of(url):
    return public_locator(url)


def request(value):
    validate(REQUEST_SCHEMA, value)
    tier = value['authority']['tier_a']
    hosts = {host_of(u) for u in tier['exact_urls']}
    need(hosts == set(tier['hosts']), 'tier A hosts must be exactly the hosts of the exact URLs')
    keys = [dispatch_key(u) for u in tier['exact_urls']]
    need(len(set(keys)) == len(keys), 'two exact URLs make the same request; each URL is dispatched at most once')
    need(not any(k == dispatch_key(f'https://{host_of(u)}/robots.txt') for k, u in zip(keys, tier['exact_urls'])),
         'robots.txt is checked automatically, never a target')
    r = value['resources']['reservation']
    need(r['per_response_bytes'] <= r['total_bytes'], 'per-response ceiling exceeds the total byte reservation')
    # One robots.txt request per host precedes that host's first target.
    need(r['requests'] >= len(tier['exact_urls']) + len(hosts), 'reservation must cover every exact URL plus one robots.txt per host')
    return value


def target(url):
    """The request-target actually sent: path (or /) plus any non-empty query."""
    p = urlsplit(url)
    return (p.path or '/') + ('?' + p.query if p.query else '')


def dispatch_key(url):
    """Identity of the request a URL produces, for duplicate and route-stop matching.

    Dot segments are refused (servers may resolve them); escapes of unreserved characters are decoded and the
    remaining escapes upper-cased, so spellings of one request compare equal.
    """
    host = host_of(url)
    path = urlsplit(url).path
    need(not any(s in ('.', '..') for s in path.split('/')), 'dot segments are refused in exact URLs')
    normal = UNRESERVED.sub(lambda m: chr(int(m.group(1), 16)), target(url))
    return host + re.sub(r'%[0-9a-fA-F]{2}', lambda m: m.group(0).upper(), normal)


def hostname(value):
    need(isinstance(value, str) and host_of('https://' + value + '/') == value, 'public DNS hostname required')
    return value


def scope(value):
    validate(SCOPE_SCHEMA, value)
    human(value['owner'], 'scope owner')
    need(moment(value['decided_at'], 'decided_at') < moment(value['valid_until'], 'valid_until'), 'scope validity window is empty')
    return value


def attestation(value):
    validate(ATTESTATION_SCHEMA, value)
    human(value['attested_by'], 'stop attester')
    moment(value['attested_at'], 'attested_at')
    for r in value['resolutions']:
        need(bool(r['hosts'] or r['routes']) != bool(r['task_scoped_reason']),
             'each resolution names hosts/routes or a task-scoped reason, not both or neither')
        for host in r['hosts']:
            hostname(host)
        for route in r['routes']:
            dispatch_key(route)
    for d in value['documented_stops']:
        hostname(d['host'])
        if d['route']:
            need(host_of(d['route']) == d['host'], 'documented route must belong to its host')
            dispatch_key(d['route'])
    return value


def parse(raw, what):
    try:
        return loads(raw)
    except (ValueError, UnicodeDecodeError) as error:
        raise SourceError(f'{what} is not valid JSON') from error
