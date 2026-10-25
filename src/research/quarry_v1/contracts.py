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


def supply(value):
    validate(SUPPLY, value)
    need((value['fixture'] == 'SYNTHETIC') == (value['data_classification'] == 'SYNTHETIC'), 'fixture/classification mismatch')
    return value
