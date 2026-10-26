"""Retrieval-to-custody bridge: one verified Source Retrieval target receipt becomes one native Quarry package.

Source Retrieval's own verification decides whether the attempt is consistent; this module only selects a
custody-eligible target receipt, binds it to the owner-approved Quarry route, and calls Quarry's unchanged
import. The identity and asset claims in a Quarry supply are human assertions, so they come from a named
human's QUARRY_RETRIEVAL_CLAIMS_V001 record, never from software. Nothing here reads the network.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from src.research.spec import digest
from src.research.jev_navigation_v1.contracts import TEXT, HASH, LABEL, obj, array, validate
from src.research.quarry_v1 import contracts as K, evidence as E, io as QIO
from src.research.source_v1 import contracts as C, retrieve as R, store as S

CLAIMS = 'QUARRY_RETRIEVAL_CLAIMS_V001'
MARKER = 'SOURCE_CUSTODY_CLAIM_V001'
STATEMENT = 'I inspected the retained bytes of this receipt. These are my claims about them, not verified facts.'
CLAIMS_SCHEMA = obj({
    'schema': {'const': CLAIMS}, 'attested_by': TEXT, 'attested_at': TEXT,
    'attempt_id': LABEL, 'receipt_sha256': HASH, 'body_sha256': HASH,
    'title': TEXT, 'source_identity_claim': TEXT, 'asset_claim': TEXT, 'source_version_claim': TEXT,
    'historical_availability_claim': TEXT, 'data_classification': {'enum': ['SYNTHETIC', 'PUBLIC_REPOSITORY', 'LOCAL_PRIVATE']},
    'limitations': array(TEXT), 'missing_fields': array(TEXT), 'statement': {'const': STATEMENT}})


class CustodyError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise CustodyError(message)


def custody_root(base):
    return S.records(base).parent / 'source-custody-v1'


def preflight(base, attempt_id, url):
    """Read-only: the verified, custody-eligible target receipt for url, bound to its approved Quarry route."""
    try:
        state, result, _ = R.verify(base, attempt_id)
    except ValueError as error:
        raise CustodyError('SOURCE_INCONSISTENT: ' + str(error)) from error
    need(result is not None and state == result['status'], f'SOURCE_NOT_FINISHED: the attempt is {state}; only a finished, anchored result is eligible')
    need(not result['interrupted'] and result['status'] in ('COMPLETE', 'PARTIAL', 'STOPPED', 'UNAVAILABLE'),
         f"SOURCE_NOT_ELIGIBLE: a {result['status']} attempt{' (interrupted)' if result['interrupted'] else ''} supplies no custody")
    x = R.examine(base, attempt_id)
    attempt = x['attempt']
    receipts = {sha: r for _, sha, r in R.receipts_of(attempt, x['events'][:-1])}  # verify established the journal anchor
    entries = [h for h in result['custody_handoff'] if h['requested_url'] == url]
    if not entries:
        seen = [r for r in receipts.values() if r['requested_url'] == url]
        need(False, 'NOT_CUSTODY_ELIGIBLE: ' + (f"{url} ended {seen[0]['termination']} (HTTP {seen[0]['http_status']}); "
                                                 'robots.txt, error pages and unsupported outcomes are never original evidence'
                                                 if seen else f'{url} was not retrieved by this attempt'))
    handoff = entries[0]
    receipt = receipts.get(handoff['receipt_sha256'])
    need(receipt is not None and R.custody(receipt) and receipt['role'] == 'TARGET' and receipt['requested_url'] == url,
         'RECEIPT_MISMATCH: the custody handoff does not name a verified target receipt for this URL')
    need((receipt['body_path'], receipt['body_sha256'], receipt['bytes_received'], receipt['coverage'])
         == (handoff['body_path'], handoff['body_sha256'], handoff['bytes'], handoff['coverage'])
         and receipt['coverage'] in K.TRANSFER_COVERAGE, 'RECEIPT_MISMATCH: body path, size, hash or coverage differ')
    # The route and its version come from the owner-approved Quarry files the attempt bound by hash.
    scope_raw = S.read(attempt / 'inputs' / 'scope.json')
    scope = C.parse(scope_raw, 'owner scope copy')
    need(S.sha(scope_raw) == result['scope_sha256'], 'SCOPE_MISMATCH: the attempt scope copy differs from its request')
    raws = {k: S.read(attempt / 'inputs' / f'{k.replace("_", "-")}.json') for k in ('quarry_registry', 'quarry_scope')}
    need(all(S.sha(raws[k]) == scope[k]['sha256'] for k in raws), 'SCOPE_MISMATCH: Quarry file copies differ from the owner scope')
    registry, quarry_scope = K.registry(C.parse(raws['quarry_registry'], 'registry copy')), C.parse(raws['quarry_scope'], 'Quarry scope copy')
    routes = [r for r in registry['routes'] if r['id'] in quarry_scope['route_ids'] and r['locator'] == url]
    need(len(routes) == 1 and routes[0]['id'] == handoff['quarry_route_id'], 'ROUTE_MISMATCH: no single approved Quarry route for this URL')
    body = S.read(attempt / receipt['body_path'])
    need(S.sha(body) == receipt['body_sha256'] and len(body) == receipt['bytes_received'], 'BODY_MISMATCH: retained body differs from its receipt')
    return {'attempt_id': attempt_id, 'url': url, 'result_sha256': S.sha(S.read(attempt / 'result.json')),
            'request_sha256': result['request_sha256'], 'receipt_sha256': handoff['receipt_sha256'], 'receipt': receipt,
            'route': routes[0], 'registry_raw': raws['quarry_registry'], 'body': body}


def fingerprint(ctx):
    return {k: ctx[k] for k in ('result_sha256', 'request_sha256', 'receipt_sha256')} | {
        'route': ctx['route'], 'registry': S.sha(ctx['registry_raw']), 'body': S.sha(ctx['body'])}


def claims(path, ctx):
    raw, value = S.load(path, 'retrieval claims')
    try:
        validate(CLAIMS_SCHEMA, value)
    except ValueError as error:
        raise CustodyError('CLAIMS_INVALID: ' + str(error)) from error
    C.human(value['attested_by'], 'claims attester')
    C.moment(value['attested_at'], 'attested_at')
    need((value['attempt_id'], value['receipt_sha256'], value['body_sha256']) == (ctx['attempt_id'], ctx['receipt_sha256'], ctx['receipt']['body_sha256']),
         'CLAIMS_MISMATCH: the claims name a different attempt, receipt or body')
    return S.sha(raw), value


def supply(ctx, claims_sha, claimed):
    r = ctx['receipt']
    retrieval = {'source_component': 'SOURCE_RETRIEVAL_V001', 'attempt_id': ctx['attempt_id'], 'request_sha256': ctx['request_sha256'],
                 'result_sha256': ctx['result_sha256'], 'receipt_sha256': ctx['receipt_sha256'], 'requested_url': ctx['url'],
                 'http_status': r['http_status'], 'termination': r['termination'], 'transfer_coverage': r['coverage'],
                 'body_sha256': r['body_sha256'], 'body_bytes': r['bytes_received'], 'started_at': r['started_at'],
                 'finished_at': r['finished_at'], 'implementation_sha256': r['implementation_sha256'], 'claims_sha256': claims_sha,
                 'publication_authenticity': 'UNKNOWN', 'dataset_completeness': 'UNKNOWN', 'scientific_meaning': 'NOT_ESTABLISHED'}
    limitations = list(dict.fromkeys([*K.transfer_limitations(retrieval), *r['limitations'], *claimed['limitations']]))
    value = {'schema': K.SUPPLY_V002, 'route_id': ctx['route']['id'], 'route_version': ctx['route']['version'],
             'fixture': 'SYSTEM_RETRIEVED', 'data_classification': claimed['data_classification'], 'title': claimed['title'],
             'source_identity_claim': claimed['source_identity_claim'], 'asset_claim': claimed['asset_claim'],
             'source_version_claim': claimed['source_version_claim'], 'retrieved_at_claim': r['finished_at'],
             'retrieval_method_claim': K.RETRIEVAL_METHOD + ctx['receipt_sha256'],
             'historical_availability_claim': claimed['historical_availability_claim'], 'expected_original_sha256': r['body_sha256'],
             'coverage': K.TRANSFER_COVERAGE[r['coverage']][0], 'limitations': limitations,
             'missing_fields': claimed['missing_fields'], 'system_retrieval': retrieval}
    return K.supply(value)


def import_receipt(base, attempt_id, url, claims_path, out, clock=S.now):
    """Create one Quarry package for one receipt; a receipt enters custody at most once."""
    ctx = preflight(base, attempt_id, url)
    claims_sha, claimed = claims(claims_path, ctx)
    value = supply(ctx, claims_sha, claimed)
    target = QIO.safe_path(out)
    need(not target.exists(), 'OUTPUT_EXISTS: custody output is create-only')
    marker = custody_root(base) / 'receipts' / f"{ctx['receipt_sha256']}.json"
    if marker.exists():
        prior = C.parse(S.read(marker), 'custody claim')
        same = prior.get('supply_sha256') == digest(value)
        need(False, ('REUSED_CUSTODY: this receipt is already in custody at ' if same else
                     'INCONSISTENT_DUPLICATE: this receipt is already in custody with a different supply at ') + str(prior.get('package')))
    with tempfile.TemporaryDirectory(prefix='source-custody-') as tmp:
        stage = Path(tmp)
        QIO.write(stage / 'registry.json', ctx['registry_raw'], raw=True)
        QIO.write(stage / 'supply.json', value)
        QIO.write(stage / 'original.bin', ctx['body'], raw=True)  # The verified bytes, not a re-read of the source file.
        need(fingerprint(preflight(base, attempt_id, url)) == fingerprint(ctx),
             'SOURCE_CHANGED_AFTER_PREFLIGHT: source records changed while preparing custody; nothing was imported')
        S.write_new(marker, {'schema': MARKER, 'receipt_sha256': ctx['receipt_sha256'], 'attempt_id': attempt_id, 'url': url,
                             'supply_sha256': digest(value), 'claims_sha256': claims_sha, 'package': str(target),
                             'claimed_at': clock(), 'authorises': []})
        receipt = E.import_file(stage / 'registry.json', stage / 'supply.json', stage / 'original.bin', target)
    return {'package': str(target), 'quarry_receipt': receipt, 'supply_sha256': digest(value), 'custody_claim': str(marker),
            'coverage': value['coverage'], 'external_requests_started': 0, 'authorises': []}


def status(base, receipt_sha256):
    """Read-only: the custody claim for a receipt, and whether its package completed and still verifies."""
    marker = custody_root(base) / 'receipts' / f'{receipt_sha256}.json'
    need(marker.is_file(), 'no custody claim for this receipt')
    claim = C.parse(S.read(marker), 'custody claim')
    package = Path(claim['package'])
    try:
        state = E.status(package)
        consistent = state.get('status') != 'PARTIAL_OR_INTERRUPTED' and digest(E.load(package)['supply']) == claim['supply_sha256']
    except (OSError, ValueError) as error:
        state, consistent = {'status': 'MISSING_OR_INCONSISTENT', 'fault_type': type(error).__name__}, False
    return {'custody_claim': claim, 'package_status': state, 'consistent': consistent, 'authorises': []}
