"""Draft mappings into Jev and Discovery shapes: reviewable proposals with a field-level audit, never ledger records.

Claim-defining text (population, predictor and outcome quantities, mechanism, falsification) is carried verbatim or
by a stated rule. Anything the Discovery checklist reads as established (units, routes, timing, exposure, clocks)
stays UNKNOWN and the source's proposal for it is listed UNRESOLVED, so a draft can never remove a mechanical
blocker. Where a contract needs a boolean or enum that the source does not state, the draft takes the value that adds
rather than removes blockers, and lists it UNRESOLVED. Observations are never drafted: their values, units,
denominators and four clocks must be read from a retained original by a human. Nothing here appends to a ledger,
certifies a field meaning or records a human judgment."""
from __future__ import annotations

import re

from src.research.discovery import records as R
from src.research.jev_navigation_v1.contracts import M_ORDER
from src.research.opportunity_scout.readiness import identifiable
from src.research.spec import digest

U = R.UNKNOWN
DRAFT = 'RESEARCH_OS_OPERATOR_DRAFT_V001'
AUDIT = 'RESEARCH_OS_OPERATOR_MAPPING_AUDIT_V001'
CLASSES = ('COPIED', 'TRANSFORMED', 'MISSING', 'UNRESOLVED')
STATUS = 'DRAFT_NOT_A_LEDGER_RECORD_HUMAN_INSPECTION_REQUIRED'


class Audit:
    def __init__(self, target, source):
        self.target, self.source, self.rows = target, source, []

    def add(self, field, cls, source, note, proposal=None):
        assert cls in CLASSES
        row = {'field': field, 'class': cls, 'source': source, 'note': note}
        if proposal is not None:
            row['source_value'] = proposal
        self.rows.append(row)

    def copied(self, field, source, target_value, source_value):
        if target_value != source_value:  # a COPIED field is identical by construction; anything else is drift
            raise ValueError(f'mapping drift in COPIED field {field}')
        self.add(field, 'COPIED', source, 'verbatim')

    def value(self):
        counts = {c: sum(r['class'] == c for r in self.rows) for c in CLASSES}
        return {'schema': AUDIT, 'target': self.target, 'source': self.source, 'rows': self.rows, 'counts': counts,
                'human_inspection_required': True, 'authorises': []}


def card_ref(card):
    return {'idea_id': card['id'], 'version': card['version'], 'card_sha256': digest(card)}


def requirements(idea):
    return sorted({idea['requirement']['id'], *idea['reconsider_when']['requirements'], *(h['requirement'] for h in idea['historical_refs'])})


def subject(card):
    """Jev SUBJECT from one card version, as the cross-stage protocol specifies."""
    i, a = card['idea'], Audit('JEV_NAVIGATION_SUBJECT', card_ref(card))
    value = {'id': card['id'], 'version': card['version'], 'question': i['next_step']['question'],
             'predictor': i['predictor']['quantity'], 'outcome': i['outcome']['quantity'], 'unresolved_m': list(M_ORDER),
             'concept_terms': [], 'entity_ids': [], 'document_sha256': [], 'requirement_ids': requirements(i)}
    a.copied('id', 'card.id', value['id'], card['id'])
    a.copied('version', 'card.version', value['version'], card['version'])
    a.copied('question', 'card.idea.next_step.question', value['question'], i['next_step']['question'])
    a.copied('predictor', 'card.idea.predictor.quantity', value['predictor'], i['predictor']['quantity'])
    a.copied('outcome', 'card.idea.outcome.quantity', value['outcome'], i['outcome']['quantity'])
    a.add('unresolved_m', 'TRANSFORMED', 'rule', 'All six M requirements are unresolved at Forge; none is evidenced by a card.')
    a.add('concept_terms', 'MISSING', None, 'No card field supplies concept terms; none is invented.')
    a.add('entity_ids', 'UNRESOLVED' if i['entity_ids'] else 'MISSING', 'card.idea.entity_ids',
          'Generator-proposed identifiers are not verified identities; a human decides whether to include them.' if i['entity_ids']
          else 'The card names no entity identifiers.', i['entity_ids'] or None)
    a.add('document_sha256', 'MISSING', None, 'No verified document is attached to a card.')
    a.add('requirement_ids', 'TRANSFORMED', 'card.idea.requirement.id + reconsider_when.requirements + historical_refs[].requirement',
          'Sorted union of the requirement identifiers the card names.')
    return value, a.value()


def memory_subject(value, known):
    """Restrict requirement identifiers to those the memory catalogue defines; the rest are listed, never dropped silently."""
    kept = [r for r in value['requirement_ids'] if r in known]
    dropped = [r for r in value['requirement_ids'] if r not in known]
    return {**value, 'requirement_ids': kept}, dropped


def mechanism_text(m):
    return (f"{m['family']} ({m['transformation']}). Trigger: {m['trigger']} Operational effect: {m['operational_effect']} "
            f"Transmission: {m['transmission']} Affected party: {m['affected_party']} Consequence: {m['consequence']}")


def candidate(handoff, fixture):
    """Discovery candidate v1 draft from a Scout handoff envelope (DISCOVERY_LAB_STARTING_PROPOSAL_V001)."""
    card = handoff['opportunity_card']; i = card['idea']
    a = Audit('DISCOVERY_CANDIDATE', {**card_ref(card), 'handoff_sha256': digest(handoff)})
    seen = any(r.get('after_outcome_known') is True for r in card.get('revision_history') or [])
    record = R.template('candidate')
    record.update({'id': 'CAND-' + card['id'], 'after_outcome_seen': seen, 'method': handoff['discovery_method_proposed'],
                   'population': i['entity_class'], 'mechanism': mechanism_text(i['mechanism']),
                   'falsification': f"{i['falsifier']['observation']} Weakens: {i['falsifier']['weakens']}",
                   'missing_variables': [*i['required_relationship_evidence'], 'Main uncertainty: ' + i['main_uncertainty']]})
    record['predictor'].update(quantity=i['predictor']['quantity'], transformation=U)
    record['exposure'].update(allocation_required=True)
    record['outcome'].update(quantity=i['outcome']['quantity'])
    record['closest_substitute']['not_checked_reason'] = 'Operator draft from a Scout card; no closest substitute has been checked.'
    record['selection'].update(prior_related_claims=sorted({h['investigation'] for h in i['historical_refs']}),
                               notes=f"Operator draft from Scout card {card['id']} v{card['version']} sha256 {digest(card)}, "
                                     f"handoff sha256 {digest(handoff)}; sector: {i['sector']}.")
    record['recommendation'] = {'action': 'HOLD', 'reason': 'Operator draft only: human inspection and separate owner campaign authority are required before any append.'}
    a.add('id', 'TRANSFORMED', 'card.id', "'CAND-' prefix on the card identifier.")
    a.add('version/supersedes/revision_reason', 'TRANSFORMED', 'rule', 'A new Discovery record family starts at version 1.')
    a.add('after_outcome_seen', 'TRANSFORMED' if seen else 'UNRESOLVED', 'card.revision_history[].after_outcome_known',
          'True because a recorded revision declares the outcome known.' if seen else
          'Scout records no outcome-known revision; a human must confirm before any append.')
    a.copied('method', 'handoff.discovery_method_proposed', record['method'], handoff['discovery_method_proposed'])
    a.add('entry_record', 'MISSING', None, 'A hypothesis-first claim has no Discovery entry record yet.')
    a.copied('population', 'card.idea.entity_class', record['population'], i['entity_class'])
    a.copied('predictor.quantity', 'card.idea.predictor.quantity', record['predictor']['quantity'], i['predictor']['quantity'])
    a.add('predictor.observation_ids', 'MISSING', None, 'No human-read original observation exists.')
    a.add('predictor.units', 'UNRESOLVED', 'card.idea.predictor.units', 'Proposed units only; units are read from an original before entry.', i['predictor']['units'])
    a.add('predictor.transformation', 'UNRESOLVED', 'card.idea.predictor.denominator + timing',
          'The card states a denominator and timing, not a transformation; a human decides.', {'denominator': i['predictor']['denominator'], 'timing': i['predictor']['timing']})
    a.add('exposure.company/relationship_ids/gross/net/materiality', 'MISSING', None, 'No listed-company exposure is identified by a card.')
    a.add('exposure.claim_basis', 'UNRESOLVED', 'template', 'Template value GROSS with UNKNOWN amounts (blocked as unquantified); a human sets the basis.')
    a.add('exposure.allocation_required', 'UNRESOLVED', 'rule', 'Fail-closed true: adds allocation blockers until a human decides it is not required.')
    a.add('mechanism', 'TRANSFORMED', 'card.idea.mechanism', 'Labelled concatenation of family, transformation and the five verbatim chain fields.')
    a.copied('outcome.quantity', 'card.idea.outcome.quantity', record['outcome']['quantity'], i['outcome']['quantity'])
    a.add('outcome.units', 'UNRESOLVED', 'card.idea.outcome.units', 'Proposed units only; stays UNKNOWN until read from an original.', i['outcome']['units'])
    a.add('outcome.route/independence', 'UNRESOLVED', 'card.idea.outcome.independent_measurement',
          'A proposed measurement is not an established route or independence.', i['outcome']['independent_measurement'])
    a.add('outcome.source_id/status/value/evidence', 'MISSING', None, 'No outcome source or value is observed; status UNVERIFIED.')
    a.add('joins', 'MISSING', None, 'Every join dimension stays UNVERIFIED.')
    a.add('information_event', 'UNRESOLVED', 'card.idea.information_pathway', 'A proposed pathway is not a dated information event.', i['information_pathway'])
    a.add('public_time_route', 'UNRESOLVED', 'card.idea.information_pathway', 'No public-time route is evidenced.', i['information_pathway'])
    a.add('horizon', 'UNRESOLVED', 'card.idea.outcome.timing', 'Outcome timing is not a 5-20 session horizon rationale.', i['outcome']['timing'])
    a.add('closest_substitute', 'MISSING', None, 'Not checked.')
    a.add('increment', 'MISSING', None, 'No incremental-information claim is evidenced.')
    a.add('falsification', 'TRANSFORMED', 'card.idea.falsifier', "Verbatim observation, then ' Weakens: ' and the verbatim weakens text.")
    a.add('missing_variables', 'TRANSFORMED', 'card.idea.required_relationship_evidence + main_uncertainty', 'Verbatim items; main uncertainty prefixed.')
    a.add('selection.prior_related_claims', 'TRANSFORMED', 'card.idea.historical_refs[].investigation', 'Sorted unique investigation identifiers.')
    a.add('selection.famous_case/purposive_control/outcome_inspected_before_freeze', 'UNRESOLVED', 'template', 'Template values; a human confirms the selection record.')
    a.add('selection.notes', 'TRANSFORMED', 'card + handoff hashes', 'Provenance note: card and handoff SHA-256, sector.')
    a.add('propositions', 'MISSING', None, 'All three propositions UNTESTED.')
    a.add('recommendation', 'TRANSFORMED', 'rule', 'Fixed HOLD: a draft recommends nothing.')
    return wrap('candidate', record, fixture, a)


def source_requirements(card, synthetic):
    """The card's proposed source routes as Discovery source requirements (proposals; never dispatched)."""
    return [{'publisher': r['publisher'], 'locator': r['locator'], 'fields': r['fields'], 'state': r['state'],
             'limitation': r['limitation'], 'identifiable_locator': identifiable(r, synthetic), 'authorises_dispatch': False}
            for r in card['idea']['source_routes']]


def source_id(route_id):
    return 'SRC-' + re.sub(r'[^A-Za-z0-9_.-]', '-', route_id)


def passport(provenance, inspection, export_sha256, fixture):
    """Discovery Source Passport v1 draft from one validated Quarry export (QUARRY_HANDOFF_V001 provenance)."""
    route, supply, receipt = provenance['route'], provenance['supply'], provenance['receipt']
    a = Audit('DISCOVERY_SOURCE_PASSPORT', {'route_id': route['id'], 'route_version': route['version'], 'export_manifest_sha256': export_sha256})
    synthetic = fixture == 'SYNTHETIC'
    held = receipt['original_sha256'] is not None
    evidence = [{'locator': route['locator'], 'kind': 'ORIGINAL_DOCUMENT' if route['originality_claim'] == 'ORIGINAL' else 'SECONDARY_ANALYSIS',
                 'depth': 'UNVERIFIED', 'passage': U, 'sha256': receipt['original_sha256'],
                 'archive': f'quarry-export-manifest:{export_sha256}', 'synthetic': synthetic, 'reused_from': None}] if held else []
    stops = [f"STOP {s['id']}: {s['scope']} - {s['reason']} - {s['citation']}" for s in route['stops']]
    record = R.template('source')
    record.update({'id': source_id(route['id']), 'name': supply['title'], 'publisher': route['publisher'], 'locator': route['locator'],
                   'quantities': [{'depth': 'UNVERIFIED', 'evidence': evidence, 'field': f, 'meaning': U, 'units': U, 'denominator': U}
                                  for f in route['expected_fields']] or record['quantities'],
                   'omissions': [*supply['missing_fields'], *supply['limitations'], *route['availability_uncertainties'], *stops,
                                 *(['Quarry negative record: the owner could not supply this route (UNAVAILABLE).'] if not held else [])],
                   'next_observation': route['question']})
    record['history'].update(coverage=f"Supplied coverage claim (unverified): {supply['coverage']}")
    record['publication_clock'].update(description=f"Supplied historical-availability claim (unverified): {supply['historical_availability_claim']}")
    record['access'].update(status='BLOCKED' if route['stops'] else 'RESTRICTED' if route['access_restrictions'] else U)
    a.add('id', 'TRANSFORMED', 'route.id', "'SRC-' prefix; characters outside the Discovery id alphabet become '-'.")
    a.copied('name', 'supply.title', record['name'], supply['title'])
    a.copied('publisher', 'route.publisher', record['publisher'], route['publisher'])
    a.copied('locator', 'route.locator', record['locator'], route['locator'])
    a.add('family/domain/granularity/formats/identifiers', 'MISSING', None, 'Not stated by the route or supply record.')
    a.add('quantities[].field', 'COPIED' if route['expected_fields'] else 'MISSING', 'route.expected_fields', 'Field names only; one quantity per expected field.')
    a.add('quantities[].meaning/units/denominator', 'UNRESOLVED', 'retained original', 'Field meaning, units and denominator stay UNKNOWN until a human reads the original.')
    a.add('quantities[].evidence', 'TRANSFORMED' if held else 'MISSING', 'receipt.original_sha256 + route.locator',
          'One UNVERIFIED pointer to the retained Quarry original; kind follows originality_claim '
          f"({route['originality_claim']}; UNKNOWN maps to SECONDARY_ANALYSIS)." if held else 'No original was supplied.')
    a.add('history.coverage', 'TRANSFORMED', 'supply.coverage', 'Labelled as an unverified supplied claim; depth UNVERIFIED.')
    a.add('revision_policy', 'MISSING', None, 'No revision policy is recorded.')
    a.add('publication_clock.description', 'TRANSFORMED', 'supply.historical_availability_claim', 'Labelled as an unverified supplied claim.')
    a.add('publication_clock.frequency/release_lag', 'MISSING', None, 'Not recorded.')
    a.add('access.status', 'TRANSFORMED' if route['stops'] or route['access_restrictions'] else 'UNRESOLVED', 'route.stops + route.access_restrictions',
          'BLOCKED when a stop is recorded, RESTRICTED when restrictions exist; an owner-supplied copy does not establish open access.')
    a.add('access.permitted_use', 'MISSING', None, 'Permitted use is an owner decision.')
    a.add('omissions', 'TRANSFORMED', 'supply.missing_fields + limitations + route.availability_uncertainties + stops',
          'Verbatim items in that order; every stop is preserved with its citation.')
    a.copied('next_observation', 'route.question', record['next_observation'], route['question'])
    a.add('exposure_links/misleading_proxies', 'MISSING', None, 'Not stated.')
    a.add('clocks.economic_occurrence', 'MISSING', None, 'Read from the original by a human, in an observation record.')
    a.add('clocks.first_public', 'MISSING', None, 'Needs an original publication-record certificate; never inferred.')
    a.add('clocks.source_version', 'UNRESOLVED', 'supply.source_version_claim', 'A supplied claim, not a dataset-version certificate.', supply['source_version_claim'])
    a.add('clocks.retrieval', 'UNRESOLVED', 'supply.retrieved_at_claim', 'A retrieval clock needs a retrieval receipt; Quarry receipts record custody only.', supply['retrieved_at_claim'])
    a.add('observations', 'UNRESOLVED', 'inspection.excerpts', 'Excerpts are available for a human to map to observation records; no observation is drafted.',
          [{'id': e['id'], 'location': e['location']} for e in inspection['excerpts']])
    return wrap('source', record, fixture, a)


def wrap(kind, record, fixture, audit):
    try:
        R.validate(kind, record, fixture)
        validation = {'single_record_contract': 'VALID', 'fixture': fixture, 'error': None}
    except ValueError as error:  # recorded, never repaired
        validation = {'single_record_contract': 'INVALID', 'fixture': fixture, 'error': str(error)}
    return {'schema': DRAFT, 'status': STATUS, 'kind': kind, 'fixture': fixture, 'record': record, 'record_sha256': digest(record),
            'validation': validation, 'appended': False, 'authorises': []}, audit.value()


def preview_campaign(run_id, method, question):
    """A SYNTHETIC preview campaign for synthetic fixture runs only: no authority, budget or acquisition."""
    return {'id': 'DLC-' + run_id + '-PREVIEW', 'title': 'SYNTHETIC operator preview of draft mappings', 'method': method,
            'fixture': 'SYNTHETIC', 'question': question, 'authority': 'SYNTHETIC_FIXTURE_NO_AUTHORITY',
            'acquisition_authorized': False, 'budget': {'analyst_hours': 0, 'source_starts': 0, 'external_bytes': 0},
            'notes': ['Synthetic preview only: demonstrates mechanical checks on drafts; never research evidence.']}
