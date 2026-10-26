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


def binding(route, value):
    """A SYSTEM_RETRIEVED supply belongs only to the route whose exact locator was retrieved."""
    if value['schema'] == SUPPLY_V002:
        need(route['locator'] == value['system_retrieval']['requested_url'], 'retrieved URL differs from the route locator')
