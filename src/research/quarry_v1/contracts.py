"""V001 strict evidence contracts. UNKNOWN is data, never a verified fact."""
from src.research.jev_navigation_v1.contracts import TEXT, HASH, LABEL, obj, array, validate, need

UNKNOWN_HASH = {'anyOf': [HASH, {'const': 'UNKNOWN'}]}
STOP = obj({'id': LABEL, 'scope': TEXT, 'reason': TEXT, 'citation': TEXT, 'citation_sha256': UNKNOWN_HASH})
ROUTE = obj({'id': LABEL, 'version': TEXT, 'locator': TEXT, 'publisher': TEXT,
             'expected_fields': array(TEXT), 'question': TEXT, 'access_restrictions': array(TEXT),
             'originality_claim': {'enum': ['ORIGINAL', 'SECONDARY', 'UNKNOWN']},
             'expected_source_identity': TEXT, 'expected_asset': TEXT,
             'availability_uncertainties': array(TEXT), 'stops': array(STOP)})
REGISTRY = obj({'schema': {'const': 'QUARRY_ROUTE_REGISTRY_V001'}, 'routes': {**array(ROUTE, 32), 'minItems': 1}})
SUPPLY = obj({'schema': {'const': 'QUARRY_SUPPLY_V001'}, 'route_id': LABEL, 'route_version': TEXT,
              'fixture': {'enum': ['SYNTHETIC', 'OWNER_SUPPLIED']},
              'data_classification': {'enum': ['SYNTHETIC', 'PUBLIC_REPOSITORY', 'LOCAL_PRIVATE']},
              'title': TEXT, 'source_identity_claim': TEXT, 'asset_claim': TEXT,
              'source_version_claim': TEXT, 'retrieved_at_claim': TEXT, 'retrieval_method_claim': TEXT,
              'historical_availability_claim': TEXT, 'expected_original_sha256': UNKNOWN_HASH,
              'coverage': {'enum': ['COMPLETE_CLAIMED', 'PARTIAL', 'UNKNOWN', 'UNAVAILABLE']},
              'limitations': array(TEXT), 'missing_fields': array(TEXT)})
EXCERPT = obj({'id': LABEL, 'location': TEXT, 'start_byte': {'type': 'integer', 'minimum': 0},
               'end_byte': {'type': 'integer', 'minimum': 1}, 'quote': TEXT})
INSPECTION = obj({'schema': {'const': 'QUARRY_INSPECTION_V001'},
                 'mode': {'enum': ['ORIGINAL_UTF8', 'SUPPLIED_EXTRACTION']},
                 'extraction_method_claim': TEXT, 'excerpts': {**array(EXCERPT, 32), 'minItems': 1}})


def registry(value):
    validate(REGISTRY, value)
    need(len({r['id'] for r in value['routes']}) == len(value['routes']), 'duplicate route ID')
    return value


# V002 adds exactly one supply kind, SYSTEM_RETRIEVED: bytes a verified Source Retrieval V001 receipt retained.
# Every V001 field keeps its V001 meaning; V001 records are validated by the unchanged V001 schema.
SUPPLY_V002 = 'QUARRY_SUPPLY_V002'
RETRIEVAL_METHOD = 'SOURCE_RETRIEVAL_V001 exact-URL HTTPS GET; receipt '
# HTTP transfer coverage -> Quarry coverage. Nothing maps to a stronger Quarry coverage than the transfer supports.
TRANSFER_COVERAGE = {'COMPLETE': ('COMPLETE_CLAIMED', ('COMPLETE',)), 'UNVERIFIED': ('UNKNOWN', ('UNVERIFIED_LENGTH',)),
                     'PREFIX': ('PARTIAL', ('SIZE_STOP', 'TIME_STOP'))}
SYSTEM_RETRIEVAL = obj({
    'source_component': {'const': 'SOURCE_RETRIEVAL_V001'}, 'attempt_id': LABEL, 'request_sha256': HASH,
    'result_sha256': HASH, 'receipt_sha256': HASH, 'requested_url': TEXT, 'http_status': {'const': 200},
    'termination': {'enum': ['COMPLETE', 'UNVERIFIED_LENGTH', 'SIZE_STOP', 'TIME_STOP']},
    'transfer_coverage': {'enum': list(TRANSFER_COVERAGE)}, 'body_sha256': HASH,
    'body_bytes': {'type': 'integer', 'minimum': 1}, 'started_at': TEXT, 'finished_at': TEXT,
    'implementation_sha256': HASH, 'claims_sha256': HASH,
    # What a retrieval receipt can never establish, stated explicitly in custody.
    'publication_authenticity': {'const': 'UNKNOWN'}, 'dataset_completeness': {'const': 'UNKNOWN'},
    'scientific_meaning': {'const': 'NOT_ESTABLISHED'}})
SUPPLY_V2 = {**SUPPLY, 'properties': {**SUPPLY['properties'], 'schema': {'const': SUPPLY_V002},
                                      'fixture': {'const': 'SYSTEM_RETRIEVED'},
                                      'coverage': {'enum': ['COMPLETE_CLAIMED', 'PARTIAL', 'UNKNOWN']},
                                      'system_retrieval': SYSTEM_RETRIEVAL},
             'required': [*SUPPLY['required'], 'system_retrieval']}


def transfer_limitations(retrieval):
    """Limitations every SYSTEM_RETRIEVED supply carries, so Jev and humans see what the transfer establishes."""
    r = retrieval
    lines = [f"System-retrieved by Source Retrieval V001 attempt {r['attempt_id']} from {r['requested_url']} "
             f"(HTTP {r['http_status']}, {r['termination']}, {r['body_bytes']} bytes, finished {r['finished_at']}; receipt {r['receipt_sha256']}).",
             'Transfer coverage ' + r['transfer_coverage'] + ' describes the HTTP transfer of this exact URL only; publication '
             'authenticity, dataset completeness and scientific meaning are not established.']
    if r['transfer_coverage'] == 'PREFIX':
        lines.append('Only a prefix of the served representation was retained; the remainder was not received.')
    if r['transfer_coverage'] == 'UNVERIFIED':
        lines.append('The response had no length framing; whether the retained bytes are the whole representation is unverified.')
    return lines


def supply(value):
    if isinstance(value, dict) and value.get('schema') == SUPPLY_V002:
        return supply_v2(value)
    validate(SUPPLY, value)
    need((value['fixture'] == 'SYNTHETIC') == (value['data_classification'] == 'SYNTHETIC'), 'fixture/classification mismatch')
    return value


def supply_v2(value):
    validate(SUPPLY_V2, value)
    r = value['system_retrieval']
    coverage, terminations = TRANSFER_COVERAGE[r['transfer_coverage']]
    need(r['termination'] in terminations and value['coverage'] == coverage,
         'coverage must follow the HTTP transfer exactly; partial or unverified bytes are never COMPLETE')
    need(value['expected_original_sha256'] == r['body_sha256'], 'expected original hash must be the retained body hash')
    need(value['retrieved_at_claim'] == r['finished_at'] and value['retrieval_method_claim'] == RETRIEVAL_METHOD + r['receipt_sha256'],
         'retrieval time and method must be the observed receipt values')
    need(all(line in value['limitations'] for line in transfer_limitations(r)), 'transfer limitations must be carried into custody')
    return value


# The exact native records a SYSTEM_RETRIEVED package retains, so a later reviewer can check its provenance
# without the original Source Retrieval directory. Quarry checks their consistency; only the custody bridge,
# which runs Source Retrieval's own verification, creates them.
RETAINED = ('retrieval-receipt.json', 'retrieval-result.json', 'retrieval-claims.json')
# The human claims record retained in a V002 package. A named record is a claim, never authentication.
CLAIMS = 'QUARRY_RETRIEVAL_CLAIMS_V001'
CLAIMS_STATEMENT = 'I inspected the retained bytes of this receipt. These are my claims about them, not verified facts.'
CLAIMS_SCHEMA = obj({
    'schema': {'const': CLAIMS}, 'attested_by': TEXT, 'attested_at': TEXT,
    'attempt_id': LABEL, 'receipt_sha256': HASH, 'body_sha256': HASH,
    'title': TEXT, 'source_identity_claim': TEXT, 'asset_claim': TEXT, 'source_version_claim': TEXT,
    'historical_availability_claim': TEXT, 'data_classification': {'enum': ['SYNTHETIC', 'PUBLIC_REPOSITORY', 'LOCAL_PRIVATE']},
    'limitations': array(TEXT), 'missing_fields': array(TEXT), 'statement': {'const': CLAIMS_STATEMENT}})


def claims_record(value):
    """Schema, named-human field (assistant and placeholder names refused) and timezone; not identity proof."""
    from src.research.source_v1.contracts import human, moment
    try:
        validate(CLAIMS_SCHEMA, value)
        human(value['attested_by'], 'claims attester')
        moment(value['attested_at'], 'attested_at')
    except (KeyError, TypeError, ValueError) as error:
        need(False, 'retained claims record invalid: ' + str(error))
    return value
CLAIM_FIELDS = ('title', 'source_identity_claim', 'asset_claim', 'source_version_claim', 'historical_availability_claim',
                'data_classification', 'missing_fields')


def retained(value, files, original_sha256, size):
    """Check retained receipt, result and claims bytes against a V002 supply and the retained original."""
    import hashlib
    from src.research.jev_navigation_v1.contracts import loads
    r = value['system_retrieval']
    need(set(files) == set(RETAINED), 'SYSTEM_RETRIEVED custody needs its retained receipt, result and claims records')
    sha = {name: hashlib.sha256(files[name]).hexdigest() for name in RETAINED}
    need((sha['retrieval-receipt.json'], sha['retrieval-result.json'], sha['retrieval-claims.json'])
         == (r['receipt_sha256'], r['result_sha256'], r['claims_sha256']), 'retained native records differ from the supply binding')
    try:
        claims_record(loads(files['retrieval-claims.json']))
    except ValueError as error:
        need(False, str(error))
    try:
        receipt, result, claims = (loads(files[name]) for name in RETAINED)
        handoff = {'receipt_sha256': r['receipt_sha256'], 'requested_url': r['requested_url'], 'quarry_route_id': value['route_id'],
                   'body_path': receipt['body_path'], 'body_sha256': r['body_sha256'], 'bytes': r['body_bytes'], 'coverage': r['transfer_coverage']}
        ok = (receipt['schema'] == 'SOURCE_RETRIEVAL_RECEIPT_V001' and receipt['role'] == 'TARGET'
              and (receipt['attempt_id'], receipt['requested_url'], receipt['http_status'], receipt['termination'], receipt['coverage'],
                   receipt['body_sha256'], receipt['bytes_received'], receipt['started_at'], receipt['finished_at'], receipt['implementation_sha256'])
              == (r['attempt_id'], r['requested_url'], 200, r['termination'], r['transfer_coverage'], original_sha256, size,
                  r['started_at'], r['finished_at'], r['implementation_sha256'])
              and r['body_sha256'] == original_sha256 and r['body_bytes'] == size
              and result['schema'] == 'SOURCE_ACTIVITY_RESULT_V001' and result['attempt_id'] == r['attempt_id']
              and result['request_sha256'] == r['request_sha256'] and result['interrupted'] is False
              and result['status'] in ('COMPLETE', 'PARTIAL', 'STOPPED', 'UNAVAILABLE')
              and r['receipt_sha256'] in result['receipts'] and handoff in result['custody_handoff']
              and claims['schema'] == CLAIMS
              and (claims['attempt_id'], claims['receipt_sha256'], claims['body_sha256']) == (r['attempt_id'], r['receipt_sha256'], original_sha256)
              and all(claims[k] == value[k] for k in CLAIM_FIELDS)
              and all(line in value['limitations'] for line in claims['limitations']))
    except (KeyError, TypeError, ValueError):
        ok = False
    need(ok, 'retained receipt, result or claims do not support this SYSTEM_RETRIEVED supply')


def binding(route, value):
    """A SYSTEM_RETRIEVED supply belongs only to the route whose exact locator was retrieved."""
    if value['schema'] == SUPPLY_V002:
        need(route['locator'] == value['system_retrieval']['requested_url'], 'retrieved URL differs from the route locator')
