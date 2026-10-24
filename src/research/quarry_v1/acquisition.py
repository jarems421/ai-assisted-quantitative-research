"""Design-only acquisition boundary. This version deliberately has no HTTP dispatcher."""
import ipaddress
import re
from urllib.parse import urlsplit
from src.research.spec import digest
from . import contracts as K, io

SCOPE = K.obj({'schema': {'const': 'QUARRY_ACQUISITION_SCOPE_V001'},
               'route_ids': {**K.array(K.LABEL, 32), 'minItems': 1},
               'exact_urls': {**K.array(K.TEXT, 32), 'minItems': 1},
               'allowed_hosts': {**K.array(K.TEXT, 32), 'minItems': 1},
               'request_ceiling': {'type': 'integer', 'minimum': 1, 'maximum': 32},
               'total_byte_ceiling': {'type': 'integer', 'minimum': 1, 'maximum': 16777216},
               'per_response_byte_ceiling': {'type': 'integer', 'minimum': 1, 'maximum': 16777216},
               'minimum_interval_seconds': {'type': 'number', 'minimum': 1},
               'timeout_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 60}})


def public_locator(url):
    p = urlsplit(url)
    K.need(p.scheme == 'https' and p.hostname and p.netloc == p.hostname and not p.fragment
           and not p.username and not p.password and '\\' not in url and not any(ord(x) <= 32 for x in url), 'exact HTTPS public host required; no credentials, ports or fragments')
    host = p.hostname
    K.need(bool(re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+', host)) and not host.endswith(('.local', '.localhost', '.internal', '.test', '.invalid', '.example')),
           'public DNS hostname required')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host
    raise ValueError('IP literal refused')


def plan(registry_path, scope_path):
    registry = K.registry(io.json_file(registry_path))
    scope = io.json_file(scope_path)
    K.validate(SCOPE, scope)
    routes = {r['id']: r for r in registry['routes']}
    K.need(set(scope['route_ids']) <= set(routes), 'unknown source route')
    chosen = [routes[i] for i in scope['route_ids']]
    K.need(not any(r['stops'] for r in chosen), 'STOP_PRESERVED: stopped route cannot be planned for dispatch')
    K.need(not any(r['access_restrictions'] for r in chosen), 'restricted or unresolved access requires separate reviewed boundary')
    K.need(set(scope['exact_urls']) == {r['locator'] for r in chosen}, 'exact routes only; no expansion')
    K.need({public_locator(u) for u in scope['exact_urls']} == set(scope['allowed_hosts']), 'host allowlist mismatch')
    K.need(len(scope['exact_urls']) <= scope['request_ceiling']
           and scope['per_response_byte_ceiling'] <= scope['total_byte_ceiling'], 'inconsistent ceilings')
    return {'schema': 'QUARRY_ACQUISITION_PLAN_V001', 'registry_sha256': digest(registry), 'scope': scope,
            'scope_sha256': digest(scope), 'status': 'DISABLED_DESIGN_ONLY', 'owner_approval': 'PENDING_NOT_AUTHORITY',
            'required_future_controls': ['Owner approval binds exact registry/scope hashes, human identity, timezone date and access terms.',
                'Independently reconcile every persisted host/route stop, including unclear scopes as host-level; no stop override field.',
                'Resolve DNS and pin public global destination IP for every connection; refuse private/reserved/link-local and DNS rebinding; no proxy.',
                'Serial GET only, all redirects refused, no retries or fallback; reserve request and worst-case bytes before dispatch.',
                'Persist claim before network, bound elapsed time and streamed bytes, preserve partial/error bytes and receipts without parsing.',
                'Rate pacing is global across approved scope; stop whole scope on denial, unexpected response or transport uncertainty; no resume.',
                'No search/crawl/login/CAPTCHA/paywall bypass, ambient credentials, or new route discovery.'],
            'external_requests_started': 0, 'authorises': []}
