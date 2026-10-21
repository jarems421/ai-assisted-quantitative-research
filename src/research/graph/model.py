"""Graph v1 vocabulary: node kinds, assertion statuses, bounds and match-strength order.

Verification belongs to assertions (observations and relationship assertions), never to the
structural nodes they connect. Entities, documents and campaigns are neutral joining points.
"""
from __future__ import annotations

import re

BANNER = 'DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY'
RULES = 'GRAPH_PROJECTION_RULES_V001'
MODES = ('memory', 'prospective', 'synthetic')

# Assertion statuses (adapted from the Discovery Lab depth and relationship vocabulary).
ORIGINAL_FIELD_OBSERVED = 'ORIGINAL_FIELD_OBSERVED'          # observation depth VERIFIED_ORIGINAL_FIELD
ORIGINAL_DOCUMENT_REFERENCED = 'ORIGINAL_DOCUMENT_REFERENCED'  # VERIFIED_ORIGINAL_RECORD: document seen, field not verified
DOCUMENTED_RELATIONSHIP = 'DOCUMENTED_RELATIONSHIP'            # relationship VERIFIED with DOCUMENTED basis
RECORDED_UNVERIFIED = 'RECORDED_UNVERIFIED'
CONTRADICTED = 'CONTRADICTED'
SUPERSEDED = 'SUPERSEDED'                                      # display overlay for non-latest versions
HISTORICAL_CONCLUSION = 'HISTORICAL_CONCLUSION'
SUGGESTION_ONLY = 'SUGGESTION_ONLY'
VERIFIED_ASSERTIONS = frozenset({ORIGINAL_FIELD_OBSERVED, DOCUMENTED_RELATIONSHIP})

DEPTH_REASON = {'RETROSPECTIVE_DESCRIPTION': 'RETROSPECTIVE_ONLY', 'SCHEMA_ONLY': 'SCHEMA_ONLY',
                'INDEXED_DESCRIPTION_ONLY': 'INDEXED_ONLY', 'ACCESS_BLOCKED': 'ACCESS_BLOCKED', 'UNVERIFIED': 'UNVERIFIED'}

KINDS = ('campaign', 'source', 'document', 'observation', 'entity', 'relationship', 'claim', 'requirement', 'blocker',
         'history', 'history_claim', 'history_finding')
ASSERTION_KINDS = frozenset({'observation', 'relationship'})
# Nodes that would create trivial "same campaign / same blocker" paths are never traversal bridges.
BRIDGE_BLOCKED = frozenset({'campaign', 'source', 'requirement', 'blocker', 'history'})

HUB_DEGREE = 25
MAX_NODES = 30
DEFAULT_SEMANTIC_HOPS = 2
MAX_SEMANTIC_HOPS = 3
MAX_PATHS = 10
MAX_SUGGESTIONS = 10
MAX_EXPANSIONS = 50000

# Categorical match strength, strongest first. Lower categories never become verified links.
MATCH_STRENGTH = ('EXACT_DOCUMENT_HASH', 'EXACT_ENTITY_ID', 'DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD', 'REQUIREMENT_MATCH',
                  'AUTHOR_TAG_CANDIDATE', 'TEXT_SIMILARITY_ONLY')

ABSTENTIONS = ('NO_VERIFIED_IDENTITY', 'PERIOD_UNRESOLVED', 'PERIOD_INCOMPATIBLE', 'ALLOCATION_UNVERIFIED',
               'SOURCE_DEPTH_INSUFFICIENT', 'ONLY_SHARED_KEYWORD', 'ONLY_NAME_SIMILARITY', 'SOURCE_INDEPENDENCE_UNKNOWN',
               'RETROSPECTIVE_ONLY', 'PREVIOUS_SOURCE_STOP', 'UNKNOWN_TAG', 'HUB_SUPPRESSED', 'NO_USEFUL_SUGGESTION',
               'NO_OPEN_CLAIMS', 'NO_PATH_WITHIN_BOUNDS')

TAG = re.compile(r'\[(REQ|MEASURES):([A-Z][A-Z0-9_]*)\]')
STOPWORDS = frozenset('inc corp corporation co company ltd limited plc llc holdings holding group the fictional synthetic sa ag asa '
                      'and of for with from that this into than were which their there about after before under between'.split())


def tokens(text, minimum=1):
    return [t for t in re.findall(r'[a-z0-9]+', str(text).lower()) if len(t) >= minimum and t not in STOPWORDS]


def keywords(text):
    """Significant words used only to recognise (and reject) keyword-only similarity."""
    return set(tokens(text, 5))
