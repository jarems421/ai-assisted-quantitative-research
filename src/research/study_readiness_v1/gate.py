"""Fail-closed checks for an exact future study, outside frozen Discovery/Graph closures.

This profile checks a small, reproducible measurement construction. Economic meaning,
source completeness and inference suitability remain explicit signed human judgments.
It neither authenticates a human nor certifies M, causality or historical actionability.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.research.discovery.ledger import Ledger
from src.research.discovery.review import checklist
from src.research.spec import canonical, digest

SCHEMA = 'LEVEL_A_READINESS_V001'
REVIEW_SCHEMA = 'LEVEL_A_INDEPENDENT_REVIEW_V001'
CHECKS = ('source_meaning', 'independence', 'historical_join', 'selection_history',
          'forge_mapping', 'study_design', 'm_reaffirmation', 'owner_scope')
DESIGN_TEXT = ('question', 'falsifier', 'eligible_population', 'observation_unit',
               'baseline', 'competing_explanations', 'temporal_order', 'reconstruction_limits',
               'missingness', 'duplicates', 'dependence', 'uncertainty', 'inference',
               'analysis_family', 'stopping_rule')
SCOPE_KEYS = ('asset', 'cohort', 'geography', 'accounting_basis')
# Narrow dimensional conversions. A new conversion needs a new reviewed profile.
UNITS = {'kg/day': ('mass/day', Decimal('1')), 'tonnes/day': ('mass/day', Decimal('1000')),
         'kg/quarter': ('mass/quarter', Decimal('1')), 'tonnes/quarter': ('mass/quarter', Decimal('1000')),
         'USD': ('money/USD', Decimal('1')), 'USD million': ('money/USD', Decimal('1000000'))}


class NotReady(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise NotReady(message)


def text(value):
    return isinstance(value, str) and value.strip().upper() not in ('', 'UNKNOWN', 'TBD', 'N/A', 'NONE')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(rows, label):
    require(isinstance(rows, list) and rows, f'{label}: nonempty list required')
    result = {r['id']: r for r in rows}
    require(len(result) == len(rows), f'{label}: duplicate identifiers')
    return result


def number(value):
    require(type(value) in (int, float), 'MEASUREMENT: finite numeric scalar required by V001 profile')
    result = Decimal(str(value))
    require(result.is_finite(), 'MEASUREMENT: finite value required')
    return result


def pointer(obj, path):
    require(isinstance(path, str) and path.startswith('/'), 'SOURCE_LOCATION: JSON pointer required')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def read_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'JSON: duplicate key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(NotReady('JSON: nonfinite value')))


class Packet:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.root = self.path.parent
        self.manifest_raw = self.path.read_bytes()
        self.p = read_json(self.manifest_raw)
        self.inputs = {}
        self.cache = {}

    def artifact(self, ref):
        name = ref['file']
        path = (self.root / name).resolve()
        require(not Path(name).is_absolute() and path.is_relative_to(self.root), 'INPUT: path leaves packet')
        if name not in self.cache:
            self.cache[name] = path.read_bytes()
        raw = self.cache[name]
        require(sha(raw) == ref['sha256'], f'INPUT_CHANGED:{name}')
        self.inputs[name] = sha(raw)
        return raw

    def check(self):
        p = self.p
        require(p['schema'] == SCHEMA, 'PROFILE: unsupported schema')
        require(p['level'] == 'A' and p['claim'] == 'RETROSPECTIVE_ECONOMIC_ONLY',
                'LEVEL_B_SEPARATE: V001 cannot certify historical actionability, causality or alpha')
        ledger_raw = self.artifact(p['ledger'])
        ledger = Ledger(self.root / p['ledger']['file'])
        s = ledger.load()
        require(ledger.path.read_bytes() == ledger_raw, 'INPUT_CHANGED:ledger during replay')
        require(p['fixture'] == s.fixture and s.fixture in ('LIVE', 'SYNTHETIC', 'RETROSPECTIVE_INSPECTED'), 'FIXTURE_MISMATCH')
        cid, version = p['candidate']['id'], p['candidate']['version']
        c = s.version('candidate', cid, version)
        require(c is not None and digest(c) == p['candidate']['sha256'], 'CANDIDATE_CHANGED')
        require(c == s.latest('candidate', cid) and s.frozen(cid, version), 'CANDIDATE: latest frozen version required')
        require(p['ledger_head'] == s.events[-1]['hash'], 'LEDGER_HEAD_CHANGED')
        report = checklist(s, cid, version)
        require(not any(r['blockers'] for r in report['requirements'].values()), 'M_MECHANICAL_BLOCKERS')
        m = next((r for r in s.reviews if r['id'] == p['m_review_id']), None)
        require(m is not None and m['kind'] == 'M' and m['candidate_id'] == cid and m['version'] == version
                and all(j['judgment'] == 'EVIDENCED' for j in m['judgments'].values()), 'M_REVIEW_REQUIRED')
        require(m['reviewer']['kind'] == ('SYNTHETIC_FIXTURE' if s.fixture == 'SYNTHETIC' else 'HUMAN'), 'M_REVIEW_KIND')
        require(m == [r for r in s.reviews if r['kind'] == 'M' and r['candidate_id'] == cid and r['version'] == version][-1],
                'M_REVIEW_SUPERSEDED')
        for decision in ('M_PASSED', 'LEVEL_A_DESIGN_CANDIDATE'):
            require(any(r['candidate_id'] == cid and r['version'] == version and r['decision'] == decision
                        for r in s.dispositions), f'DISPOSITION_REQUIRED:{decision}')
        require([r for r in s.dispositions if r['candidate_id'] == cid and r['version'] == version][-1]['decision']
                == 'LEVEL_A_DESIGN_CANDIDATE', 'DISPOSITION_SUPERSEDED')

        self.origin(c)
        evidence = unique(p['evidence'], 'evidence')
        for ev in evidence.values():
            raw = self.artifact(ev)
            require(all(text(ev[k]) for k in ('original_locator', 'version', 'location')), 'SOURCE_PROVENANCE_REQUIRED')
            require(ev['complete'] is True and ev['kind'] == 'ORIGINAL', 'SOURCE_INCOMPLETE_OR_NONORIGINAL')
            require(ev['format'] in ('UTF8_TEXT', 'BINARY_HUMAN_LOCATION') and text(ev['passage']), 'SOURCE_FORMAT_OR_PASSAGE_REQUIRED')
            if ev['format'] == 'UTF8_TEXT':
                # Exact text anchoring is mechanical; a quoted sentence is not semantic proof.
                require(ev['passage'] in raw.decode('utf-8'), 'SOURCE_PASSAGE_NOT_FOUND')

        measures = unique(p['measurements'], 'measurements')
        observations = {}
        for mid, item in measures.items():
            ob = s.version('observation', item['observation_id'], item['observation_version'])
            require(ob is not None and ob == s.latest('observation', ob['id']), 'OBSERVATION_CHANGED')
            require(ob['id'] not in observations, 'MEASUREMENT: duplicate observation mapping')
            observations[ob['id']] = mid
            ev = evidence[item['evidence_id']]
            require(any(e.get('sha256') == ev['sha256'] for e in ob['evidence']), 'OBSERVATION_SOURCE_HASH_MISMATCH')
            require(item['source_id'] == ob['source_id'] and item['source_version'] == s.latest('source', ob['source_id'])['version'], 'SOURCE_VERSION_MISMATCH')
            require(item['value'] == ob['value'] and item['units'] == ob['units'] and item['denominator'] == ob['denominator']
                    and item['entity'] == ob['entity']['id'], 'SOURCE_TO_VALUE_MISMATCH')
            require(item['nature'] in ('MEASURED', 'REPORTED', 'ESTIMATED', 'FORECAST', 'CONDITIONAL'), 'MEASUREMENT_NATURE_REQUIRED')
            require(all(text(item[k]) for k in ('units', 'denominator', 'entity')), 'MEASUREMENT_SCOPE_REQUIRED')
            require(all(text(item['scope'][k]) for k in SCOPE_KEYS), 'MEASUREMENT_SCOPE_REQUIRED')
            start, end = date.fromisoformat(item['period']['start']), date.fromisoformat(item['period']['end'])
            occurred = date.fromisoformat(ob['clocks']['economic_occurrence']['value'][:10])
            require(start <= occurred <= end, 'MEASUREMENT_PERIOD_MISMATCH')
            if item['extraction'] == 'JSON_POINTER':
                require(ev['format'] == 'UTF8_TEXT', 'BINARY_EXTRACTION_REQUIRES_HUMAN_REVIEW')
                extracted = pointer(read_json(self.cache[ev['file']]), item['location'])
                require(type(extracted) == type(item['value']) and extracted == item['value'], 'SOURCE_TO_VALUE_MISMATCH')
            else:
                require(item['extraction'] == 'HUMAN_PASSAGE' and text(item['location']), 'EXTRACTION_PROFILE_UNKNOWN')
            number(item['value'])
            public = item['public_time']
            require(public['status'] in ('RETROSPECTIVE_ONLY', 'EXACT_VERSION_CERTIFIED'), 'PUBLIC_VERSION_STATUS_REQUIRED')
            if public['status'] == 'EXACT_VERSION_CERTIFIED':
                require(public['content_sha256'] == ev['sha256'] and public['certificate_evidence_id'] in evidence
                        and text(public['published_at']), 'PUBLIC_CERTIFICATE_VERSION_MISMATCH')
            # RETROSPECTIVE_ONLY deliberately needs no first-public certificate at Level A.

        nodes = unique(p['construction'], 'construction')
        require(not (nodes.keys() & measures.keys()), 'CONSTRUCTION: colliding identifiers')
        seen, active = {}, set()

        def evaluate(nid):
            if nid in seen:
                return seen[nid]
            require(nid not in active, 'CIRCULAR_CONSTRUCTION')
            active.add(nid)
            if nid in measures:
                item = measures[nid]
                ev = evidence[item['evidence_id']]
                # Hash + source location catches a copied reading under a new ID.
                result = (number(item['value']), item['units'], {nid}, {(ev['sha256'], item['location'])})
            else:
                node = nodes[nid]
                args = [evaluate(i) for i in node['inputs']]
                require(args, 'CONSTRUCTION: missing inputs')
                leaves = set.union(*(a[2] for a in args))
                require(len({measures[i]['denominator'] for i in leaves}) == 1
                        and all(measures[i]['scope'] == measures[next(iter(leaves))]['scope'] for i in leaves),
                        'TRANSFORMATION_DENOMINATOR_OR_SCOPE_MISMATCH')
                op = node['op']
                if op == 'IDENTITY':
                    require(len(args) == 1 and node['units'] == args[0][1], 'UNIT_MISMATCH')
                    value = args[0][0]
                elif op == 'CONVERT':
                    require(len(args) == 1, 'CONVERSION: one input required')
                    old, new = UNITS.get(args[0][1]), UNITS.get(node['units'])
                    require(old is not None and new is not None and old[0] == new[0], 'UNIT_CONVERSION_UNSUPPORTED')
                    factor = number(node['factor'])
                    require(factor == old[1] / new[1], 'INCORRECT_UNIT_CONVERSION')
                    value = args[0][0] * factor
                else:
                    require(op in ('DIFFERENCE', 'SUM') and all(a[1] == node['units'] for a in args), 'CONSTRUCTION_OR_UNIT_UNSUPPORTED')
                    if op == 'DIFFERENCE':
                        require(len(args) == 2, 'DIFFERENCE: two inputs required')
                        value = args[0][0] - args[1][0]
                    else:
                        value = sum(a[0] for a in args)
                require(value == number(node['value']), 'TRANSFORMATION_VALUE_MISMATCH')
                result = (value, node['units'], set.union(*(a[2] for a in args)), set.union(*(a[3] for a in args)))
            active.remove(nid)
            seen[nid] = result
            return result

        for nid in nodes:
            evaluate(nid)
        pred, out = evaluate(p['predictor_root']), evaluate(p['outcome_root'])
        require(not (pred[2] & out[2] or pred[3] & out[3]), 'PREDICTOR_OUTCOME_OVERLAP')
        require({measures[i]['observation_id'] for i in pred[2]} == set(c['predictor']['observation_ids']), 'PREDICTOR_MAPPING_INCOMPLETE')
        require({measures[i]['observation_id'] for i in out[2]} == set(c['outcome']['derived_from_observations']), 'OUTCOME_MAPPING_INCOMPLETE')
        require(pred[1] == c['predictor']['units'] and out[1] == c['outcome']['units']
                and out[0] == number(c['outcome']['value']), 'CANDIDATE_CONSTRUCTION_MISMATCH')
        require(all(measures[i]['nature'] in ('MEASURED', 'REPORTED') for i in out[2]), 'OUTCOME_NOT_REALIZED')
        require(pred[2] | out[2] == measures.keys(), 'UNUSED_MEASUREMENT')
        require(c['outcome']['source_id'] in {measures[i]['source_id'] for i in out[2]}, 'OUTCOME_SOURCE_MAPPING_MISMATCH')
        financial = p['financial_crosswalk']
        number(financial['value'])
        require(financial['basis'] == c['exposure']['claim_basis'] and financial['basis'] in ('GROSS', 'NET'), 'FINANCIAL_BASIS_UNSUPPORTED')
        amount = c['exposure']['gross' if financial['basis'] == 'GROSS' else 'net']
        require(financial['value'] == amount['value'] and financial['units'] == amount['units']
                and text(financial['denominator']) and text(financial['meaning']) and financial['scope'] == p['join']['scope'], 'FINANCIAL_CROSSWALK_MISMATCH')
        ev = evidence[financial['evidence_id']]
        if financial['extraction'] == 'JSON_POINTER':
            require(ev['format'] == 'UTF8_TEXT' and pointer(read_json(self.cache[ev['file']]), financial['location']) == financial['value'], 'FINANCIAL_VALUE_MISMATCH')
        else:
            require(financial['extraction'] == 'HUMAN_PASSAGE' and text(financial['location']), 'FINANCIAL_LOCATION_REQUIRED')
        for mid in pred[2]:
            self.join(s, c, measures[mid], [measures[i] for i in out[2]], evidence)
        design = p['design']
        require(all(text(design.get(k)) for k in DESIGN_TEXT), 'STUDY_DESIGN_INCOMPLETE')
        require(design['mode'] in ('EXPLORATORY', 'CONFIRMATORY'), 'STUDY_MODE_REQUIRED')
        require(design['predictor_root'] == p['predictor_root'] and design['outcome_root'] == p['outcome_root'], 'DESIGN_MAPPING_MISMATCH')
        require(design['historically_actionable'] is False and design['causal_claim'] is False, 'LEVEL_B_OR_CAUSAL_PROFILE_REQUIRED')
        inference = design['uncertainty_plan']
        require(inference['method'] in ('DESCRIPTIVE_ONLY', 'CLUSTER_BOOTSTRAP', 'BLOCK_BOOTSTRAP', 'EXACT_RANDOMIZATION', 'ANALYTIC')
                and all(text(inference[k]) for k in ('estimand', 'independent_unit', 'dependence_handling', 'adequacy_check', 'multiplicity', 'limitations'))
                and inference['failure_action'] == 'DESCRIPTIVE_ONLY_OR_STOP', 'UNCERTAINTY_PLAN_INCOMPLETE')
        history = selection_history(s, cid)
        require(p['selection_history'] == history, 'SELECTION_HISTORY_MISMATCH')
        require(not history['not_untouched'] or design['evaluation'] == 'RETROSPECTIVE_SELECTED', 'UNTOUCHED_HISTORY_LAUNDERING')
        require(design['evaluation'] in ('RETROSPECTIVE_SELECTED', 'PROSPECTIVE_UNTOUCHED'), 'EVALUATION_LABEL_REQUIRED')
        require(design['mode'] != 'CONFIRMATORY' or not history['not_untouched'], 'CONFIRMATORY_SELECTED_HISTORY')
        scope = p['owner_scope']
        require(scope['action'] == 'LOCAL_LEVEL_A_ANALYSIS' and scope['network_requests'] == 0 and scope['model_calls'] == 0
                and scope['spend'] == 0 and text(scope['limits']) and scope['evidence_ids'] == sorted(evidence), 'OWNER_SCOPE_INVALID')
        require(ledger.path.read_bytes() == ledger_raw, 'INPUT_CHANGED:ledger during assessment')
        implementation = Path(__file__).parent
        files = list(implementation.glob('*.py')) + list(implementation.parent.joinpath('discovery').glob('*.py'))
        files += [implementation.parent / 'spec.py']
        return {'schema': REVIEW_SCHEMA, 'fixture': s.fixture, 'manifest_sha256': sha(self.manifest_raw),
                'inputs': dict(sorted(self.inputs.items())), 'candidate': p['candidate'], 'ledger_head': p['ledger_head'],
                'design_sha256': digest(design), 'owner_scope_sha256': digest(scope), 'm_review_sha256': digest(m),
                'implementation_sha256': digest({str(f.relative_to(implementation.parent)): sha(f.read_bytes()) for f in files}),
                'reviews': {key: {'status': 'PENDING', 'evidence_ids': [], 'note': ''} for key in CHECKS}}

    def origin(self, c):
        origin = self.p['origin']
        handoff = read_json(self.artifact(origin['handoff']))
        card = handoff['opportunity_card']
        require(handoff['schema'] == 'DISCOVERY_LAB_STARTING_PROPOSAL_V001' and card['lane'] == 'FORGE', 'FORGE_HANDOFF_REQUIRED')
        require(handoff['opportunity_card_sha256'] == digest(card) == origin['card_sha256']
                and card['id'] == origin['card_id'] and card['version'] == origin['card_version'], 'FORGE_ORIGIN_CHANGED')
        require(card['fixture'] == self.p['fixture'], 'FORGE_FIXTURE_MISMATCH')
        idea = card['idea']
        # Exact mappings are preserved; scientific changes must be explicitly crosswalked.
        targets = {'/predictor/quantity': c['predictor']['quantity'], '/predictor/units': c['predictor']['units'],
                   '/outcome/quantity': c['outcome']['quantity'], '/outcome/units': c['outcome']['units'],
                   '/falsifier/observation': c['falsification']}
        require(set(origin['mapping']) == set(targets), 'FORGE_MAPPING_INCOMPLETE')
        for path, target in targets.items():
            row = origin['mapping'][path]
            require(row['original'] == pointer(idea, path) and row['mapped'] == target, 'FORGE_HANDOFF_CHANGED')
            require(row['original'] == row['mapped'] or text(row['change_reason']), 'FORGE_CHANGE_UNDISCLOSED')
        require(text(origin['mechanism_mapping']), 'FORGE_MECHANISM_MAPPING_REQUIRED')

    def join(self, s, c, pred, outcomes, evidence):
        join = self.p['join']
        scope = pred['scope']
        require(join['scope'] == scope and all(o['scope'] == scope for o in outcomes), 'JOIN_SCOPE_MISMATCH')
        current = pred['entity']
        require(not current.startswith(('NAME:', 'TICKER:')), 'STABLE_IDENTIFIER_REQUIRED')
        used, entities = [], {current}
        start = min(date.fromisoformat(t) for t in [pred['period']['start']] + [o['period']['start'] for o in outcomes])
        end = max(date.fromisoformat(t) for t in [pred['period']['end']] + [o['period']['end'] for o in outcomes])
        for edge in join['path']:
            rel = s.latest('relationship', edge['relationship_id'])
            require(rel is not None and rel['status'] == 'VERIFIED' and rel['basis'] == 'DOCUMENTED', 'JOIN_RELATIONSHIP_UNVERIFIED')
            traversal = edge.get('traversal', 'FORWARD')
            require(traversal in ('FORWARD', 'REVERSE'), 'JOIN_TRAVERSAL_UNKNOWN')
            source, target = ('source_entity', 'target_entity') if traversal == 'FORWARD' else ('target_entity', 'source_entity')
            require(rel[source]['id'] == current, 'JOIN_DISCONNECTED')
            current = rel[target]['id']
            require(current not in entities and not current.startswith(('NAME:', 'TICKER:')), 'JOIN_CYCLE_OR_UNSTABLE_IDENTIFIER')
            entities.add(current)
            used.append(rel['id'])
            require(rel['period']['start'] != 'UNKNOWN' and date.fromisoformat(rel['period']['start'][:10]) <= start
                    and (rel['period']['end'] == 'OPEN' or rel['period']['end'] != 'UNKNOWN'
                         and date.fromisoformat(rel['period']['end'][:10]) >= end), 'HISTORICAL_OWNERSHIP_UNCOVERED')
            ev = evidence[edge['evidence_id']]
            require(any(e.get('sha256') == ev['sha256'] for e in rel['evidence']), 'JOIN_EVIDENCE_HASH_MISMATCH')
            require(edge['scope'] == scope, 'JOIN_SCOPE_MISMATCH')
            if edge.get('scope_basis') == 'ENTITY_WIDE_OWNERSHIP':
                # A parent owns the subsidiary as a whole; the original need not
                # enumerate every subsidiary asset. This is not an allocation.
                require(rel['type'] == 'OWNERSHIP' and all(rel[k]['type'] in ('LEGAL_ENTITY', 'LISTED_COMPANY')
                        for k in ('source_entity', 'target_entity')), 'ENTITY_WIDE_OWNERSHIP_REQUIRED')
                for key in ('asset', 'geography'):
                    require(rel['scope'][key] in (scope[key], 'NOT_APPLICABLE'), 'JOIN_ASSET_OR_GEOGRAPHY_MISMATCH')
            else:
                require(edge.get('scope_basis', 'EXACT_ASSET') == 'EXACT_ASSET', 'JOIN_SCOPE_BASIS_UNKNOWN')
                for key in ('asset', 'geography'):
                    require(rel['scope'][key] == scope[key], 'JOIN_ASSET_OR_GEOGRAPHY_MISMATCH')
            require(edge['allocation']['method'] in ('NONE_REQUIRED', 'DOCUMENTED'), 'ALLOCATION_ASSUMPTION')
            if c['exposure']['allocation_required'] or edge['allocation']['method'] == 'DOCUMENTED':
                require(edge['allocation']['method'] == 'DOCUMENTED' and rel['quantity_transfer']['status'] == 'VERIFIED'
                        and any(e.get('sha256') == evidence[edge['allocation']['evidence_id']]['sha256']
                                for e in rel['quantity_transfer']['evidence']), 'ALLOCATION_EVIDENCE_REQUIRED')
        require(used and set(used) == set(c['exposure']['relationship_ids']) and current == c['exposure']['company']['id'], 'EXPOSURE_PATH_INCOMPLETE')
        require(all(o['entity'] in entities for o in outcomes), 'OUTCOME_ENTITY_DISCONNECTED')


def selection_history(s, cid):
    """New readiness interpretation only; never changes V001 stored derived fields."""
    versions = s.versions['candidate'][cid]
    selected, unknown, revised = False, False, False
    # Include declared related families; the owner must inspect undisclosed near-duplicates.
    family = {cid}
    pending = [cid]
    while pending:
        for c in s.versions['candidate'][pending.pop()]:
            for other in c['selection']['prior_related_claims']:
                if other not in family:
                    require(other in s.versions['candidate'], 'RELATED_HISTORY_MISSING')
                    family.add(other)
                    pending.append(other)
    used_observations, used_relationships, used_sources = set(), set(), set()
    for related in family:
        for row in s.versions['candidate'][related]:
            used_observations.update(row['predictor']['observation_ids'] + row['outcome']['derived_from_observations'])
            used_relationships.update(row['exposure']['relationship_ids'])
            if row['outcome']['source_id'] != 'UNKNOWN':
                used_sources.add(row['outcome']['source_id'])
    for oid in used_observations:
        used_sources.update(o['source_id'] for o in s.versions['observation'][oid])
    evidence_revised = any(len(s.versions[kind][rid]) > 1 for kind, ids in
                           [('source', used_sources), ('observation', used_observations), ('relationship', used_relationships)] for rid in ids)
    for related in family:
        rows = s.versions['candidate'][related]
        for c in rows:
            sel = c['selection']
            selected |= c['after_outcome_seen'] or sel['outcome_inspected_before_freeze'] is True or sel['famous_case'] or sel['purposive_control']
            unknown |= sel['outcome_inspected_before_freeze'] == 'UNKNOWN'
        # All changes outside administrative version bookkeeping are conservative review triggers.
        def content(c):
            return {k: v for k, v in c.items() if k not in ('version', 'supersedes', 'revision_reason')}
        revised |= any(content(a) != content(b) for a, b in zip(rows, rows[1:]))
    return {'family': sorted(family), 'candidate_versions': len(versions), 'outcome_or_selection_seen': bool(selected),
            'unknown_selection': bool(unknown), 'content_revised': bool(revised), 'evidence_revised': evidence_revised,
            'not_untouched': bool(selected or unknown or revised or evidence_revised or s.fixture != 'LIVE')}


def inspect(path):
    """Return a review request, never readiness or permission."""
    try:
        payload = Packet(path).check()
        return {'status': 'INDEPENDENT_REVIEW_REQUIRED', 'ready': False, 'authorises': [], 'review_payload': payload}
    except (ValueError, KeyError, TypeError, OSError, IndexError, RecursionError) as error:
        return {'status': 'BLOCKED', 'ready': False, 'authorises': [], 'blocker': str(error)}
