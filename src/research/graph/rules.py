"""Visibility filters, bounded path search and step-by-step explanation.

Two hop counts are kept apart: structural edges (record to entity, record to document, claim to
record) and semantic hops (passing through a relationship assertion). Paths are explanations of
connectivity only; they never certify transmission, allocation, materiality or exposure.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass

from src.research.discovery import records as R
from src.research.discovery.review import covered
from src.research.graph import model as M

HISTORICAL_FIXTURES = frozenset({'HISTORICAL_MEMORY', 'RETROSPECTIVE_INSPECTED'})


@dataclass(frozen=True)
class View:
    as_of: str | None = None
    verified_only: bool = False
    history: bool = False
    exclude_retrospective: bool = False

    def describe(self):
        return asdict(self)


def when(value):
    return R.when(value, 'as_of') if value else None


def occurrence(n):
    return when(n['attrs']['clocks']['economic_occurrence']['value']) if n['kind'] == 'observation' else None


def period_check(n, moment):
    """True/False/None for whether a relationship's dated period covers ``moment``."""
    if moment is None:return None
    return covered(n['attrs']['period'], moment)


def visible(g, nid, view):
    """(visible, reason). Hidden records stay in the graph and remain inspectable with other filters."""
    n = g.nodes[nid]
    if n['superseded'] and not view.history:return False, 'SUPERSEDED'
    if view.exclude_retrospective and n['fixture'] in HISTORICAL_FIXTURES:return False, 'RETROSPECTIVE_ONLY'
    if view.verified_only:
        if n['kind'] in M.ASSERTION_KINDS and n['status'] not in M.VERIFIED_ASSERTIONS:return False, 'NOT_A_VERIFIED_ASSERTION'
        if n['fixture'] in HISTORICAL_FIXTURES:return False, 'RETROSPECTIVE_ONLY'
    if view.as_of:
        moment = when(view.as_of)
        if n['kind'] == 'relationship':
            inside = period_check(n, moment)
            if inside is None:return False, 'PERIOD_UNRESOLVED'
            if not inside:return False, 'PERIOD_INCOMPATIBLE'
        if n['kind'] == 'observation':
            occurred = occurrence(n)
            if occurred is None:return False, 'PERIOD_UNRESOLVED'
            if not R.before(occurred, moment):return False, 'NOT_YET_OCCURRED'
    return True, None


def verified_assertion(n):
    return n['kind'] in M.ASSERTION_KINDS and n['status'] in M.VERIFIED_ASSERTIONS and not n['superseded']


def bridge_allowed(g, nid, endpoints):
    if nid in endpoints:return True
    return g.nodes[nid]['kind'] not in M.BRIDGE_BLOCKED and g.degree(nid) <= M.HUB_DEGREE


def find_paths(g, a, b, view, semantic=M.DEFAULT_SEMANTIC_HOPS, limit=M.MAX_PATHS):
    """Shortest bounded simple paths, fewest semantic hops first. Hubs and campaign-like nodes are never bridges."""
    semantic = max(1, min(int(semantic), M.MAX_SEMANTIC_HOPS)); structural = 2 * semantic + 4
    start = int(g.nodes[a]['kind'] == 'relationship')
    queue, found, expansions = deque([(a, (a,), (), start)]), [], 0
    while queue and expansions < M.MAX_EXPANSIONS:
        node, nodes, edges, hops = queue.popleft()
        if node == b and len(nodes) > 1:
            found.append({'nodes': list(nodes), 'edges': list(edges), 'semantic_hops': hops, 'structural_edges': len(edges)}); continue
        if len(edges) >= structural:continue
        for i in g.adj.get(node, []):
            e = g.edges[i]; other = e['dst'] if e['src'] == node else e['src']
            if other in nodes or not visible(g, other, view)[0] or not bridge_allowed(g, other, (a, b)):continue
            more = hops + int(g.nodes[other]['kind'] == 'relationship')
            if more > semantic:continue
            expansions += 1
            queue.append((other, nodes + (other,), edges + (i,), more))
    bridges = lambda p: sum(g.nodes[x]['kind'] in ('claim', 'document', 'history_claim', 'history_finding') for x in p['nodes'][1:-1])
    found.sort(key=lambda p: (bridges(p), p['structural_edges'], p['semantic_hops'], p['nodes']))
    return found[:limit], {'semantic_limit': semantic, 'structural_limit': structural, 'expansions': expansions,
                           'truncated': expansions >= M.MAX_EXPANSIONS}


def evidence_refs(g, nid, clocks=False):
    """Primary evidence for a node; clock evidence is counted unless requested."""
    refs, clock_refs = [], 0
    for e, other, direction in g.neighbours(nid):
        if e['kind'] == 'CITES' and direction == 'out':
            if e['attrs']['role'].startswith('clocks.') and not clocks:clock_refs += 1; continue
            refs.append({'document': other, 'role': e['attrs']['role'], 'depth': e['attrs']['depth'], 'passage': e['attrs']['passage']})
    if clock_refs:refs.append({'clock_evidence_items': clock_refs})
    n = g.nodes[nid]
    if n['kind'] == 'history_finding':refs.append({'citation': n['attrs']['citation']})
    if n['kind'] == 'history':refs.append({'citation': n['attrs']['verdict']['citation']})
    return sorted(refs, key=lambda r: str(r))


def establishes(g, nid):
    n, a = g.nodes[nid], g.nodes[nid]['attrs']
    if n['kind'] == 'observation':
        return f"Source records: {n['label']} (value {a['value']} {a['units']}); {g.display_status(nid)}"
    if n['kind'] == 'relationship':
        return f"{n['label']}; basis {a['basis']}; {g.display_status(nid)}; allocation {a['allocation_status']}"
    if n['kind'] == 'entity':
        return f"Joining point {a['identifier']} ({a['identity_status']}); proves no financial proposition by itself"
    if n['kind'] == 'document':
        return f"Shared cited document ({a['content_identity']}); source independence not assessed"
    if n['kind'] == 'claim':return 'Hypothesis record, not an economic assertion'
    if n['kind'].startswith('history'):return 'Historical research memory cited verbatim, not new evidence'
    return f"{n['kind']} node"


def describe_step(g, i, frm, to):
    e, n = g.edges[i], g.nodes[to]
    semantic = e['kind'] in ('SUBJECT', 'OBJECT')
    step = {'from': frm, 'to': to, 'edge': e['kind'], 'direction': 'forward' if e['src'] == frm else 'reverse',
            'connection': 'SEMANTIC_RELATIONSHIP' if semantic else 'STRUCTURAL', 'node_kind': n['kind'],
            'status': g.display_status(to), 'establishes': establishes(g, to), 'evidence': evidence_refs(g, to), 'missing': []}
    if n['kind'] == 'relationship':
        step['period'] = n['attrs']['period']
        if n['attrs']['allocation_status'] == 'ALLOCATION_UNVERIFIED':step['missing'].append('ALLOCATION_UNVERIFIED')
    if n['kind'] == 'observation':
        step['clocks'] = n['attrs']['clocks']; step['depth'] = n['attrs']['depth']
        if n['attrs']['value'] == R.UNKNOWN:step['missing'].append('VALUE_UNKNOWN')
        if n['attrs']['units'] == R.UNKNOWN:step['missing'].append('UNITS_UNKNOWN')
    if n['kind'] == 'entity':
        step['identity'] = {'status': n['attrs']['identity_status'], 'types': n['attrs']['types'], 'memory_types': n['attrs'].get('memory_types', []),
                            'names': n['attrs']['names']}
    return step


def first_unsupported_leap(g, nodes):
    """The first point where the path stops being supported economic evidence."""
    anchor = next((occurrence(g.nodes[x]) for x in nodes if g.nodes[x]['kind'] == 'observation' and occurrence(g.nodes[x])), None)
    if not any(g.nodes[x]['kind'] in M.ASSERTION_KINDS for x in nodes):
        return {'node': nodes[-1], 'code': 'NO_ECONOMIC_ASSERTION_ON_PATH',
                'detail': 'the connection runs only through research records, documents or identities; no observation or relationship asserts it'}
    for x in nodes:
        n = g.nodes[x]; k = n['kind']
        if k in M.ASSERTION_KINDS and not verified_assertion(n):
            return {'node': x, 'code': 'SOURCE_DEPTH_INSUFFICIENT' if k == 'observation' else 'RELATIONSHIP_NOT_DOCUMENTED',
                    'detail': f"{g.display_status(x)} {n['reasons']}"}
        if k == 'relationship':
            inside = period_check(n, anchor)
            if anchor and inside is None:return {'node': x, 'code': 'PERIOD_UNRESOLVED', 'detail': 'relationship period unknown for the observed date'}
            if anchor and inside is False:return {'node': x, 'code': 'PERIOD_INCOMPATIBLE', 'detail': f"period {n['attrs']['period']} excludes {anchor}"}
        if k == 'entity':
            if n['attrs']['identity_status'] == 'ARCHIVE_PATH_IDENTIFIER':
                return {'node': x, 'code': 'IDENTITY_UNCORROBORATED', 'detail': 'archive-path CIK only; issuer identity not corroborated'}
            if n['attrs']['identity_status'] != 'IDENTIFIED':return {'node': x, 'code': 'NO_VERIFIED_IDENTITY', 'detail': n['attrs']['identity_status']}
            if len(n['attrs']['types']) > 1:return {'node': x, 'code': 'ENTITY_TYPE_CONFLICT', 'detail': str(n['attrs']['types'])}
        if k == 'claim' and x not in (nodes[0], nodes[-1]):
            return {'node': x, 'code': 'RESEARCH_HYPOTHESIS_BRIDGE', 'detail': 'connected only because one claim cites both records'}
        if k.startswith('history') and x not in (nodes[0], nodes[-1]):
            return {'node': x, 'code': 'RESEARCH_MEMORY_BRIDGE', 'detail': 'connected only through historical research memory'}
        if k == 'document' and x not in (nodes[0], nodes[-1]):
            return {'node': x, 'code': 'SHARED_SOURCE_ONLY', 'detail': 'connected only because both records cite this document'}
    allocation = [x for x in nodes if g.nodes[x]['kind'] == 'relationship' and g.nodes[x]['attrs']['allocation_status'] == 'ALLOCATION_UNVERIFIED']
    if allocation:return {'node': allocation[0], 'code': 'ALLOCATION_UNVERIFIED', 'detail': 'no documented quantity transfer along this relationship'}
    return {'node': nodes[-1], 'code': 'FINANCIAL_TRANSMISSION_UNVERIFIED',
            'detail': 'every step is supported, but no step shows quantity transmission, materiality or exposure'}


def explain_path(g, path):
    steps = [describe_step(g, i, path['nodes'][k], path['nodes'][k + 1]) for k, i in enumerate(path['edges'])]
    return {'nodes': path['nodes'], 'semantic_hops': path['semantic_hops'], 'structural_edges': path['structural_edges'],
            'start': {'node': path['nodes'][0], 'status': g.display_status(path['nodes'][0]), 'establishes': establishes(g, path['nodes'][0]),
                      'evidence': evidence_refs(g, path['nodes'][0])},
            'steps': steps, 'first_unsupported_leap': first_unsupported_leap(g, path['nodes']),
            'connectivity_only': True, 'exposure_certified': False, 'causal_claim': False}
