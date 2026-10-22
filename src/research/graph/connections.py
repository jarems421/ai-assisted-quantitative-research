"""Graph v1.1 connection classes: economic connection candidates, methodological warnings and unsupported matches.

Graph Pilot R3 (closed; descriptive only) found every graph-operator connection adjudicated trivial: the
operators linked unrelated investigations because both lacked the same measurement (capacity,
allocation, supplier identity). A shared unresolved requirement is reusable research memory, not an
economic connection. This module separates the two, using the match bases operators already record:

* ECONOMIC_CONNECTION_CANDIDATE - at least one grounding basis: the same document bytes (content hash,
  not a reused citation), the same identified economic object, or a documented relationship covering the
  observed date. Every candidate carries a grounded explanation: what connects the records, what that
  establishes, what stays unverified, and the first unsupported economic inference. A candidate justifies
  investigation only; it never shows exposure, causation, materiality or benefit.
* METHODOLOGICAL_WARNING - linked only by shared requirements, curated mappings, author tags or mechanical
  blockers. Retained with the earlier investigation's recorded lesson; never counted as a discovery.
* UNSUPPORTED_MATCH - neither: for example a citation reused from the other record, or a locator-only match.

Classification is categorical, from recorded bases; no score or model judgement is used.

Rulesets (prospective, chosen per snapshot; the default stays V1_1 so every v1.1 output and frozen record is unchanged):

* ``GRAPH_CLASSIFICATION_V1_1`` - the rules above.
* ``GRAPH_CLASSIFICATION_V1_2`` - owner policy (2026-10-22): a generic shared identifier is insufficient by itself.
  When every identified object behind ``EXACT_ENTITY_ID`` is generic (recorded type REGULATOR or GEOGRAPHY, or an
  identifier matched by the versioned register ``docs/strategy/graph/generic_identifiers_v001.json``, e.g. ISO 10383
  exchange codes), that basis does not ground. A documented relationship or the same document still grounds, and a
  non-generic shared object alongside a generic one still grounds. The downgraded item records why. Registered before
  any holdout fixture for it was written; evaluated only on a separate holdout, never on the v1.1 adversarial set.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.research.discovery import records as R
from src.research.graph import model as M
from src.research.graph import rules as G

OPERATOR_VERSION = 'GRAPH_OPERATORS_V1_1'
CLASSIFICATION_V1_1, CLASSIFICATION_V1_2 = 'GRAPH_CLASSIFICATION_V1_1', 'GRAPH_CLASSIFICATION_V1_2'
CLASSIFICATIONS = (CLASSIFICATION_V1_1, CLASSIFICATION_V1_2)
GENERIC_REGISTER = Path(__file__).resolve().parents[3] / 'docs/strategy/graph/generic_identifiers_v001.json'
GENERIC_REGISTER_VERSION = 'GRAPH_GENERIC_IDENTIFIERS_V001'
ECONOMIC = 'ECONOMIC_CONNECTION_CANDIDATE'
WARNING = 'METHODOLOGICAL_WARNING'
UNSUPPORTED = 'UNSUPPORTED_MATCH'
CLASSES = (ECONOMIC, WARNING, UNSUPPORTED)
CLASS_ORDER = {c: i for i, c in enumerate(CLASSES)}
GROUNDING = {
    'EXACT_DOCUMENT_HASH': 'both records cite the same document bytes (content hash); one document is not independent corroboration',
    'EXACT_ENTITY_ID': 'both records concern the same identified economic object (exact identifier, never a name or ticker)',
    'DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD': 'a documented relationship involving that object covers the observed date'}
METHODOLOGICAL = {
    'AUTHOR_TAG_CANDIDATE': 'an author tag says the record may bear on a requirement the other claim lacks',
    'CURATED_MAPPING': 'a curated mapping assigns both to the same requirement class',
    'CURATED_HISTORICAL_MAPPING': 'a curated historical mapping assigns the earlier investigation to the same requirement class',
    'MECHANICAL_BLOCKER': 'both claims are blocked by the same mechanical checklist blocker',
    'REQUIREMENT_MATCH': 'both records share a requirement class'}
UNSUPPORTED_BASES = {'REUSED_CITATION': 'one record cites evidence copied from the other (reused_from); the same evidence, not a second record',
                     'SAME_LOCATOR_ONLY': 'only a document locator matches; no content hash',
                     'GENERIC_SHARED_IDENTIFIER': 'the only shared identified object is a generic institutional identifier (a regulator, exchange, '
                                                  'geography or other generic role); insufficient by itself under GRAPH_CLASSIFICATION_V1_2'}
NOT_ESTABLISHED = ['financial exposure of any listed company', 'causation or transmission of a quantity', 'materiality',
                   'allocation of any quantity to a counterparty', 'that the records describe the same quantity definition and units']
WARNING_MEANING = ('These records share an unresolved research requirement, so the earlier investigation is a relevant warning about '
                   'what proved hard to measure. It is not evidence that the economic objects or events are connected.')
ROLE_EDGES = ('DESCRIBES', 'SUBJECT', 'OBJECT', 'EXPOSES', 'CONCERNS')


def classify(bases):
    b = set(bases)
    if b & set(GROUNDING):return ECONOMIC
    if b & set(METHODOLOGICAL):return WARNING
    return UNSUPPORTED


def order_key(item, strength):
    return (CLASS_ORDER[item['connection_class']], strength.get(item.get('strength'), 99), str(item.get('match')), str(item.get('target')))


def economic_objects(g, nid):
    out = []
    for e, other, d in g.neighbours(nid):
        if d == 'out' and e['kind'] in ROLE_EDGES and g.nodes[other]['kind'] == 'entity':
            a = g.nodes[other]['attrs']
            out.append({'record': nid, 'role': e['kind'], 'entity': other, 'identifier': a['identifier'], 'identity_status': a['identity_status'],
                        'names': a['names']})
    return sorted(out, key=lambda x: (x['role'], x['entity']))


def join_object(g, v):
    n = g.nodes.get(v)
    if n is None:return {'object': v, 'kind': 'unknown'}
    if n['kind'] == 'document':
        return {'object': v, 'kind': 'document', 'content_identity': n['attrs']['content_identity'], 'locators': n['attrs']['locators'],
                'independence': 'NOT_INDEPENDENT_CORROBORATION: one document cited by both records'}
    if n['kind'] == 'entity':
        return {'object': v, 'kind': 'entity', 'identifier': n['attrs']['identifier'], 'identity_status': n['attrs']['identity_status'],
                'names': n['attrs']['names']}
    if n['kind'] == 'relationship':
        return {'object': v, 'kind': 'relationship', 'type': n['attrs']['type'], 'direction': n['attrs']['direction'], 'period': n['attrs']['period'],
                'status': g.display_status(v), 'allocation': n['attrs']['allocation_status']}
    if n['kind'] == 'requirement':
        return {'object': v, 'kind': 'requirement', 'note': 'methodological only; not part of the economic grounding'}
    return {'object': v, 'kind': n['kind']}


def clock_view(g, nid):
    n = g.nodes[nid]
    if n['kind'] == 'observation':
        return {'record': nid, 'occurred': G.occurrence(n) or R.UNKNOWN, 'first_public': n['attrs']['clocks']['first_public']['value']}
    if n['kind'] == 'relationship':return {'record': nid, 'period': n['attrs']['period'], 'first_public': R.UNKNOWN}
    return {'record': nid, 'kind': n['kind'], 'first_public': R.UNKNOWN}


def ground(g, source, target, bases, via):
    """The grounded explanation every economic connection candidate must carry (nine parts)."""
    joins = [join_object(g, v) for v in sorted(set(via))]
    grounding = sorted({b for b in bases if b in GROUNDING}, key=list(GROUNDING).index)
    # The join chain for the first unsupported inference: identified objects, then documented relationships, then documents.
    middle = [j['object'] for kind in ('entity', 'relationship', 'document') for j in joins if j['kind'] == kind and j['object'] not in (source, target)]
    chain = [source] + middle + [target]
    temporal = {'source': clock_view(g, source), 'target': clock_view(g, target)}
    moment = G.occurrence(g.nodes[source]) if g.nodes[source]['kind'] == 'observation' else None
    rel = target if g.nodes[target]['kind'] == 'relationship' else next((j['object'] for j in joins if j['kind'] == 'relationship'), None)
    if rel:
        inside = G.period_check(g.nodes[rel], moment)
        temporal['relationship_period_covers_source'] = {True: 'YES', False: 'NO', None: 'UNRESOLVED'}[inside]
    unknown_public = [t for t in (temporal['source'], temporal['target']) if t['first_public'] == R.UNKNOWN]
    not_established = list(NOT_ESTABLISHED)
    if unknown_public:not_established.append('first-public time of ' + ', '.join(t['record'] for t in unknown_public) + ' (UNKNOWN)')
    if any(j.get('identity_status') == 'ARCHIVE_PATH_IDENTIFIER' for j in joins):
        not_established.append('that the archive-path identifier is the same economic entity (listing, securities and group structure not established)')
    t = g.nodes[target]
    if t['kind'] in ('claim', 'history_claim'):
        missing = t['attrs'].get('missing_variables') or [g.nodes[f]['label'] for e, f, d in g.neighbours(target) if e['kind'] == 'HAS_FINDING' and d == 'out']
        why = f"the target claim records unresolved variables ({'; '.join(missing[:3]) or 'see claim'}) that the source record may bear on"
    elif t['kind'] == 'relationship':
        why = f"it documents {t['label']} for the object the source concerns, a possible transmission route to investigate"
    elif t['kind'] == 'observation':
        why = 'an independently recorded observation of the same identified object; compare definitions, units and dates before combining'
    elif t['kind'] == 'history':
        why = 'an earlier investigation concerned the same identifier; read its cited report (its verdict stands)'
    else:
        why = f'the {t["kind"]} shares grounded structure with the source'
    return {'source_record': source, 'target_record': target,
            'documented_basis': [{'basis': b, 'meaning': GROUNDING[b]} for b in grounding],
            'joining_objects': joins, 'economic_objects': economic_objects(g, source) + economic_objects(g, target), 'temporal': temporal,
            'establishes': [GROUNDING[b] for b in grounding] + [G.establishes(g, target)],
            'not_established': not_established, 'first_unsupported_inference': G.first_unsupported_leap(g, chain),
            'worth_investigating_because': why}


def lesson(g, target, requirements):
    n = g.nodes[target]
    if n['kind'] == 'history_claim':
        hist = target.split('/claim-')[0]
        found = [f for x in (target, hist) for e, f, d in g.neighbours(x) if e['kind'] == 'HAS_FINDING' and d == 'out']
        return sorted({(g.nodes[f]['label'], g.nodes[f]['attrs']['citation']['path']) for f in found
                       if g.nodes[f]['attrs']['requirement'] in requirements or g.nodes[f]['attrs']['finding_kind'] == 'EVIDENCE_TO_CHANGE'})
    if n['kind'] == 'claim':
        return [v for v in n['attrs'].get('missing_variables', []) if any(f'[REQ:{r}]' in v for r in requirements)] + [n['attrs'].get('falsification')]
    return []


def warn(g, source, target, bases, via):
    """A reusable research warning: the earlier record's lesson, explicitly not an economic connection."""
    requirements = sorted({v.split(':', 1)[1] for v in via if str(v).startswith('requirement:')})
    return {'not_an_economic_connection': True, 'meaning': WARNING_MEANING, 'source_record': source, 'target_record': target,
            'shared_requirements': requirements, 'linking_bases': [{'basis': b, 'meaning': METHODOLOGICAL.get(b, UNSUPPORTED_BASES.get(b, b))} for b in sorted(set(bases))],
            'lesson': lesson(g, target, requirements),
            'use': 'Reuse the earlier recorded gap, falsification route or failure before acquiring similar evidence.'}


def load_register(path=GENERIC_REGISTER):
    reg = json.loads(Path(path).read_text(encoding='utf-8'))
    if reg.get('version') != GENERIC_REGISTER_VERSION:raise ValueError(f'not a {GENERIC_REGISTER_VERSION} register')
    for key in ('entity_types', 'identifier_prefixes', 'identifiers'):
        if not isinstance(reg.get(key), list) or not all(isinstance(x, dict) and x.get('category') and x.get('rationale') for x in reg[key]):
            raise ValueError(f'register {key} entries each need a category and a rationale')
    return reg


def use_rules(g, rules=CLASSIFICATION_V1_1, register=None):
    """Select the classification ruleset for queries on this graph (V1_2 also needs the generic-identifier register)."""
    if rules not in CLASSIFICATIONS:raise ValueError(f'classification rules are one of {CLASSIFICATIONS}')
    g.classification, g.generic_register = rules, (register or load_register()) if rules == CLASSIFICATION_V1_2 else None
    return g


def generic_category(g, nid):
    """The generic institutional category of an entity node, or None. Never from a name."""
    reg, a = g.generic_register, g.nodes[nid]['attrs']
    types = set(a.get('types', ())) | set(a.get('memory_types', ()))
    for x in reg['entity_types']:
        if x['type'] in types:return x['category']
    for x in reg['identifier_prefixes']:
        if a['identifier'].startswith(x['prefix']):return x['category']
    for x in reg['identifiers']:
        if a['identifier'] == x['id']:return x['category']
    return None


def apply_rules(g, item, bases, via):
    """The bases that count under the graph's ruleset, and the generic-identifier explanation when V1_2 removes one."""
    if getattr(g, 'classification', CLASSIFICATION_V1_1) == CLASSIFICATION_V1_1 or 'EXACT_ENTITY_ID' not in bases:return list(bases), None
    vias = list(via) + [m.get('via') for m in item.get('matches', [])]
    entities = sorted({v for v in vias if isinstance(v, str) and v.startswith('entity:') and v in g.nodes})
    categories = {e: generic_category(g, e) for e in entities}
    if not entities or not all(categories.values()):return list(bases), None
    return [b for b in bases if b != 'EXACT_ENTITY_ID'], {
        'rule': CLASSIFICATION_V1_2, 'entities': [{'entity': e, 'category': c} for e, c in categories.items()],
        'note': 'every shared identified object here is a generic institutional identifier; EXACT_ENTITY_ID does not ground this item'}


def annotate(g, item, source, target, bases, via):
    """Add the connection class and its explanation to an operator result (in place); returns it."""
    effective, generic = apply_rules(g, item, bases, via)
    item['connection_class'] = classify(effective)
    if generic:item['generic_identifier'] = generic
    if getattr(g, 'classification', CLASSIFICATION_V1_1) != CLASSIFICATION_V1_1:item['classification_rules'] = g.classification
    if item['connection_class'] == ECONOMIC:item['grounding'] = ground(g, source, target, effective, via)
    elif item['connection_class'] == WARNING:item['warning'] = warn(g, source, target, effective, via)
    else:item['unsupported'] = {'reason': [UNSUPPORTED_BASES.get(b, b) for b in sorted(set(effective))] + ([UNSUPPORTED_BASES['GENERIC_SHARED_IDENTIFIER']] if generic else []),
                                'note': 'cannot justify even a provisional economic connection; retained for transparency'}
    return item


def summarise(out, rejected=()):
    rows = out['results']
    out['operator_version'] = OPERATOR_VERSION
    out['connection_summary'] = {'economic_connection_candidates': sum(r.get('connection_class') == ECONOMIC for r in rows),
                                 'methodological_warnings': sum(r.get('connection_class') == WARNING for r in rows),
                                 'unsupported_matches': sum(r.get('connection_class') == UNSUPPORTED for r in rows),
                                 'rejected': len(list(rejected)),
                                 'note': 'Only economic connection candidates are discoveries to investigate; warnings are reusable research memory.'}
    return out


GROUNDED_FIELDS = ('source_record', 'target_record', 'documented_basis', 'joining_objects', 'economic_objects', 'temporal', 'establishes',
                   'not_established', 'first_unsupported_inference', 'worth_investigating_because')


def provenance_complete(item):
    """Every economic candidate must expose all grounded-explanation parts, non-empty."""
    if item.get('connection_class') != ECONOMIC:return True
    gnd = item.get('grounding') or {}
    return all(gnd.get(k) for k in GROUNDED_FIELDS)
