"""Synthetic enforcement tests. Mocked signers are never evidence of real human approval."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.research.discovery import demo as D
from src.research.discovery.ledger import Ledger
from src.research.spec import canonical, digest
from src.research.study_readiness_v1 import gate as G, approval as A
from src.research.study_readiness_v1.__main__ import main
from test_discovery_lab import campaign, observation, relationship, candidate, m_review, disposition


def evidence(raw):
    e = D.syn('fictional-original')
    e['sha256'] = G.sha(raw)
    return e


def finish(ledger, c):
    version = c['version']
    ledger.append('candidate', c)
    ledger.freeze(c['id'])
    ledger.append('review', m_review('REV-M-' + str(version), version=version))
    ledger.append('disposition', disposition('DSP-M-' + str(version), decision='M_PASSED', reason_type='EVIDENCE_COMPLETE', version=version))
    ledger.append('review', D.rec('review', id='REV-H-' + str(version), candidate_id=c['id'], version=version, kind='H', reviewer=D.reviewer(),
        judgments={'judgment': 'NOT_ESTABLISHED', 'information_event': 'UNKNOWN', 'expectation_mechanism': 'UNKNOWN',
                   'reason': 'SYNTHETIC: no investment advantage.'}, not_checked=D.not_checked('PUBLIC_TIME'), conclusion='Synthetic only.'))
    ledger.append('disposition', disposition('DSP-A-' + str(version), decision='LEVEL_A_DESIGN_CANDIDATE', reason_type='EVIDENCE_COMPLETE', version=version))


def make_packet(folder, edit_records=None):
    """Fictional same-publisher readings, actual Scout handoff and actual Discovery replay."""
    from src.research.opportunity_scout import engine as E, workflow as W, fixtures as F
    from src.research.opportunity_scout.storage import Archive
    folder.mkdir(parents=True)
    raw = canonical({'ceiling': 6, 'old_ceiling': 10, 'shipments': 61, 'prior_shipments': 80, 'gross': 40,
                     'relationship': 'F-001 operated by ALPHA in synthetic port from 1990.'})
    (folder / 'original.json').write_bytes(raw)
    ev = evidence(raw)
    pred = observation(value=6, evidence=[ev])
    out = observation('OBS-T-OUT', kind='QUANTITY', value=61, units='tonnes/quarter', outcome_independent=False, evidence=[ev])
    rel = relationship(evidence=[ev], scope={'asset': 'SYN_FACILITY:F-001', 'contract': 'NOT_APPLICABLE', 'product': 'bulk', 'geography': 'synthetic port'})
    c = candidate('HYPOTHESIS_FIRST', None)
    c['predictor']['quantity'] = 'Permitted daily ceiling'
    records = {'predictor': pred, 'outcome': out, 'relationships': [rel], 'candidate': c}
    if edit_records:
        edit_records(records)
    ledger = Ledger.create(folder / 'ledger.jsonl', campaign('HYPOTHESIS_FIRST'), D.Clock())
    ledger.append('source', D.passport('SRC-T', 'Fictional same-publisher original', field='ceiling', units='tonnes/day'))
    ledger.append('observation', pred)
    ledger.append('observation', out)
    for row in records['relationships']:
        ledger.append('relationship', row)
    finish(ledger, c)

    archive = Archive(folder / 'scout')
    W.initialise(archive, 'SYNTHETIC hardening only', fixture='SYNTHETIC', with_memory=False, moment=F.MOMENT)
    idea = F.idea()
    idea['predictor'].update(quantity=c['predictor']['quantity'], units=c['predictor']['units'])
    idea['outcome'].update(quantity=c['outcome']['quantity'], units=c['outcome']['units'])
    idea['falsifier']['observation'] = c['falsification']
    aid, _ = W.prepare(archive, 'FORGE', 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=F.MOMENT)
    W.finish(archive, aid, canonical({'ideas': [idea]}).decode(), F.provenance(), moment=F.MOMENT)
    card = next(v[-1] for v in archive.load().cards.values())
    archive.append('assessment', E.assess(archive.load(), card), recorded_at=F.MOMENT)
    archive.append('feasibility', F.feasibility(card), recorded_at=F.MOMENT)
    archive.append('review', {'readiness_version': 'SCOUT_READY_V002', 'idea_id': card['id'], 'version': card['version'],
        'decision': 'READY', 'reason_type': 'RESEARCHABLE', 'reason': 'SYNTHETIC test double only; no real human decision.', 'uncertainties': ['Fictional.'],
        'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'}, 'minutes': 'UNKNOWN',
        'approved_handoff': True, 'reconsider_when': 'Separately authorised evidence.', 'authorises_acquisition': False}, recorded_at=F.MOMENT)
    handoff_raw = canonical(E.handoff(archive.load(), card['id']))
    (folder / 'handoff.json').write_bytes(handoff_raw)
    scope = {'asset': 'SYN_FACILITY:F-001', 'cohort': 'single facility', 'geography': 'synthetic port', 'accounting_basis': 'GROSS'}
    measurements = []
    for mid, ob, location in [('X', pred, '/ceiling'), ('Y', out, '/shipments')]:
        measurements.append({'id': mid, 'observation_id': ob['id'], 'observation_version': 1, 'source_id': 'SRC-T', 'source_version': 1,
            'evidence_id': 'E1', 'location': location, 'extraction': 'JSON_POINTER', 'value': ob['value'], 'units': ob['units'],
            'denominator': ob['denominator'], 'entity': ob['entity']['id'], 'scope': dict(scope), 'nature': 'REPORTED',
            'period': {'start': '2000-03-01', 'end': '2000-03-31'}, 'public_time': {'status': 'RETROSPECTIVE_ONLY'}})
    mapping = {}
    for path in ('/predictor/quantity', '/predictor/units', '/outcome/quantity', '/outcome/units', '/falsifier/observation'):
        original = G.pointer(card['idea'], path)
        mapping[path] = {'original': original, 'mapped': original, 'change_reason': ''}
    design = {'question': 'Does this fictional documented ceiling reduction coincide with lower separately reported terminal shipments?',
              'falsifier': 'Shipments are unchanged or higher after the reduction; a missing same-facility measurement stops the check.',
              'eligible_population': 'One purposively chosen fictional terminal F-001; not a population-wide estimate.',
              'observation_unit': 'Facility-quarter, with the ceiling in tonnes/day kept distinct from quarterly output.',
              'baseline': 'Zero shipment change from the original prior_shipments field (80); compare reported shipments (61).',
              'competing_explanations': 'Demand decline, maintenance, seasonality and substitution could explain the same change.',
              'temporal_order': 'Original records describe the ceiling change before the quarterly shipment report; public-time producibility unestablished.',
              'reconstruction_limits': 'Retrospective v1 originals only; no claim that these versions were available to a historical investor.',
              'missingness': 'If the facility or either quarter is absent, stop; never replace it with group output.',
              'duplicates': 'One immutable publisher version per facility-quarter; revisions retained separately.',
              'dependence': 'One facility and shared economic shocks; no independent sampling or repeated-case inference.',
              'uncertainty': 'Report measurement/reconstruction sensitivity and confounding limits; no sampling confidence interval for this purposive case.',
              'inference': 'Descriptive comparison against zero change only; no causal or population effect estimate.',
              'analysis_family': 'One declared descriptive comparison; alternative definitions separately exploratory.',
              'stopping_rule': 'Stop on missing original measurements, joins or failed source inspection; no further source dispatch.'}
    design.update(mode='EXPLORATORY', evaluation='RETROSPECTIVE_SELECTED', predictor_root='P', outcome_root='O',
                  historically_actionable=False, causal_claim=False,
                  uncertainty_plan={'method': 'DESCRIPTIVE_ONLY', 'estimand': 'Recorded within-facility shipment change, not a causal effect.',
                    'independent_unit': 'Facility; only one purposively chosen unit.', 'dependence_handling': 'No independent repeated observations are assumed.',
                    'adequacy_check': 'One selected case cannot support a sampling interval; do not bootstrap quarters as independent units.',
                    'multiplicity': 'One descriptive comparison; all alternate definitions exploratory.',
                    'limitations': 'No control group, population inference or causal identification.', 'failure_action': 'DESCRIPTIVE_ONLY_OR_STOP'})
    p = {'schema': G.SCHEMA, 'fixture': 'SYNTHETIC', 'level': 'A', 'claim': 'RETROSPECTIVE_ECONOMIC_ONLY',
         'ledger': {'file': 'ledger.jsonl', 'sha256': G.sha(ledger.path.read_bytes())}, 'ledger_head': ledger.load().events[-1]['hash'],
         'candidate': {'id': c['id'], 'version': c['version'], 'sha256': digest(c)}, 'm_review_id': 'REV-M-1',
         'origin': {'handoff': {'file': 'handoff.json', 'sha256': G.sha(handoff_raw)}, 'card_id': card['id'], 'card_version': card['version'],
                    'card_sha256': digest(card), 'mapping': mapping, 'mechanism_mapping': 'SYNTHETIC: manual mechanism shortened; source-backed verification still required.'},
         'evidence': [{'id': 'E1', 'file': 'original.json', 'sha256': G.sha(raw), 'original_locator': 'synthetic://same-publisher/v1',
                       'archive': 'synthetic://immutable/v1', 'version': 'v1', 'kind': 'ORIGINAL', 'complete': True,
                       'location': 'JSON fields and relationship text', 'passage': 'F-001 operated by ALPHA', 'format': 'UTF8_TEXT'}],
         'measurements': measurements, 'construction': [{'id': 'P', 'op': 'IDENTITY', 'inputs': ['X'], 'value': pred['value'], 'units': pred['units']},
              {'id': 'O', 'op': 'IDENTITY', 'inputs': ['Y'], 'value': out['value'], 'units': out['units']}],
         'predictor_root': 'P', 'outcome_root': 'O', 'join': {'scope': scope, 'path': [
             {'relationship_id': r['id'], 'evidence_id': 'E1', 'scope': dict(scope), 'allocation': {'method': 'NONE_REQUIRED'}} for r in records['relationships']]},
         'financial_crosswalk': {'basis': 'GROSS', 'value': 40, 'units': 'USD million/year', 'denominator': 'per year',
             'scope': dict(scope), 'meaning': 'Gross scale; no net retained-cost claim.', 'evidence_id': 'E1', 'location': '/gross', 'extraction': 'JSON_POINTER'},
         'selection_history': G.selection_history(ledger.load(), c['id']), 'design': design,
         'owner_scope': {'action': 'LOCAL_LEVEL_A_ANALYSIS', 'network_requests': 0, 'model_calls': 0, 'spend': 0,
                         'evidence_ids': ['E1'], 'limits': 'SYNTHETIC only. One fixed retrospective contrast; no acquisition, returns or activation.'}}
    path = folder / 'packet.json'
    path.write_bytes(canonical(p))
    return path, p, ledger


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path, self.p, self.ledger = make_packet(self.root / 'packet')

    def save(self):
        self.path.write_bytes(canonical(self.p))

    def refused(self, code):
        self.save()
        result = G.inspect(self.path)
        self.assertFalse(result['ready'])
        self.assertEqual(result['status'], 'BLOCKED', result)
        self.assertIn(code, result['blocker'])

    def approval(self):
        self.save()
        payload = G.Packet(self.path).check()
        payload['owner_principal'] = 'SYNTHETIC_OWNER'
        for review in payload['reviews'].values():
            review.update(status='VERIFIED', evidence_ids=['E1'], note='SYNTHETIC test double; no human judgment.')
        path = self.root / 'review.json'
        path.write_bytes(canonical(payload))
        trust = self.root / 'trust.json'
        trust.write_bytes(canonical({'schema': 'LEVEL_A_OWNER_TRUST_V001', 'fixture': 'SYNTHETIC', 'principal': 'SYNTHETIC_OWNER',
                                     'allowed_signers': str(self.root / 'allowed_signers'), 'allowed_signers_sha256': '0' * 64}))
        return payload, path, trust

    def test_valid_retrospective_same_publisher_waits_for_independent_review(self):
        result = G.inspect(self.path)
        self.assertEqual(result['status'], 'INDEPENDENT_REVIEW_REQUIRED', result)
        self.assertFalse(result['ready'])
        self.assertEqual(result['authorises'], [])

    def test_synthetic_review_double_can_pass_without_claiming_identity_or_execution(self):
        _, review, trust = self.approval()
        with patch.object(A, 'verify_signature') as signer:
            result = A.verify(self.path, review, self.root / 'stand-in.sig', trust_path=trust)
        signer.assert_called_once()
        self.assertEqual(result['status'], 'SYNTHETIC_READY', result)
        self.assertFalse(result['human_identity_authenticated'])
        self.assertFalse(result['source_meaning_certified_by_software'])
        self.assertEqual(result['authorises'], [])

    def test_declared_field_without_independent_mapping_cannot_advance(self):
        self.p['measurements'][0]['extraction'] = 'HUMAN_PASSAGE'
        self.save()
        result = G.inspect(self.path)
        self.assertEqual(result['status'], 'INDEPENDENT_REVIEW_REQUIRED')
        payload, review, trust = self.approval()
        payload['reviews']['source_meaning']['status'] = 'PENDING'
        review.write_bytes(canonical(payload))
        with patch.object(A, 'verify_signature') as signer:
            self.assertIn('source_meaning', A.verify(self.path, review, 'none', trust_path=trust)['blocker'])
        signer.assert_not_called()

    def test_wrong_extracted_field_value_is_blocked(self):
        self.p['measurements'][0]['location'] = '/shipments'
        self.refused('SOURCE_TO_VALUE_MISMATCH')

    def test_source_bytes_changed_even_if_declared_original(self):
        (self.path.parent / 'original.json').write_text('{"ceiling": 999}')
        self.refused('INPUT_CHANGED')

    def test_missing_field_location_is_blocked(self):
        self.p['measurements'][0]['location'] = ''
        self.refused('SOURCE_LOCATION')

    def test_missing_units_denominator_and_scope_block(self):
        for key in ('units', 'denominator'):
            with self.subTest(key=key):
                old = self.p['measurements'][0][key]
                self.p['measurements'][0][key] = 'UNKNOWN'
                self.refused('SOURCE_TO_VALUE_MISMATCH')
                self.p['measurements'][0][key] = old
        self.p['measurements'][0]['scope']['accounting_basis'] = 'UNKNOWN'
        self.refused('MEASUREMENT_SCOPE_REQUIRED')

    def test_outcome_reconstructed_from_predictor_is_blocked(self):
        self.p['construction'][1].update(op='SUM', inputs=['P', 'P'], units='tonnes/day', value=12)
        self.refused('PREDICTOR_OUTCOME_OVERLAP')

    def test_transitive_circular_derivation_is_blocked(self):
        self.p['construction'][0]['inputs'] = ['O']
        self.p['construction'][1]['inputs'] = ['P']
        self.refused('CIRCULAR_CONSTRUCTION')

    def test_renamed_measurement_cannot_hide_overlap(self):
        self.p['measurements'][1].update(evidence_id='E1', location='/ceiling', extraction='HUMAN_PASSAGE')
        self.refused('PREDICTOR_OUTCOME_OVERLAP')

    def test_wrong_unit_conversion_is_blocked(self):
        self.p['construction'][0].update(op='CONVERT', factor=100, units='kg/day', value=600)
        self.refused('INCORRECT_UNIT_CONVERSION')

    def test_cross_dimension_conversion_is_blocked(self):
        self.p['construction'][0].update(op='CONVERT', factor=1, units='USD', value=6)
        self.refused('UNIT_CONVERSION_UNSUPPORTED')

    def test_unreproducible_transform_is_blocked(self):
        self.p['construction'][0]['op'] = 'RUN_PYTHON'
        self.refused('CONSTRUCTION_OR_UNIT_UNSUPPORTED')

    def test_wrong_transform_result_is_blocked(self):
        self.p['construction'][0]['value'] = 999
        self.refused('TRANSFORMATION_VALUE_MISMATCH')

    def test_unrelated_asset_or_cohort_or_accounting_is_blocked(self):
        for key in G.SCOPE_KEYS:
            with self.subTest(key=key):
                old = self.p['join']['path'][0]['scope'][key]
                self.p['join']['path'][0]['scope'][key] = 'unrelated'
                self.refused('JOIN_SCOPE_MISMATCH')
                self.p['join']['path'][0]['scope'][key] = old

    def test_current_owner_cannot_be_backfilled(self):
        self.p['measurements'][0]['period']['start'] = '1980-01-01'
        self.refused('HISTORICAL_OWNERSHIP_UNCOVERED')

    def test_old_certificate_cannot_bind_revised_content(self):
        self.p['measurements'][0]['public_time'] = {'status': 'EXACT_VERSION_CERTIFIED', 'content_sha256': '0' * 64,
            'certificate_evidence_id': 'E1', 'published_at': '1999-01-01'}
        self.refused('PUBLIC_CERTIFICATE_VERSION_MISMATCH')

    def test_retrospective_cannot_claim_historically_actionable(self):
        self.p['design']['historically_actionable'] = True
        self.refused('LEVEL_B_OR_CAUSAL_PROFILE_REQUIRED')

    def test_material_outcome_revision_cannot_keep_untouched_label(self):
        c = copy.deepcopy(self.ledger.load().latest('candidate', 'CAND-T-1'))
        c.update(version=2, supersedes=1, revision_reason='SYNTHETIC new outcome disclosure route.')
        c['outcome']['route'] = 'Different revised economic outcome route'
        finish(self.ledger, c)
        s = self.ledger.load()
        self.assertEqual(s.derived[('candidate', c['id'], 2)]['revision_kind'], 'CLARIFICATION')
        self.p.update(ledger={'file': 'ledger.jsonl', 'sha256': G.sha(self.ledger.path.read_bytes())}, ledger_head=s.events[-1]['hash'],
                      candidate={'id': c['id'], 'version': 2, 'sha256': digest(c)}, m_review_id='REV-M-2', selection_history=G.selection_history(s, c['id']))
        self.assertTrue(self.p['selection_history']['content_revised'])
        self.p['design']['evaluation'] = 'PROSPECTIVE_UNTOUCHED'
        self.refused('UNTOUCHED_HISTORY_LAUNDERING')

    def test_changed_outcome_value_and_original_retain_revision_history(self):
        raw = canonical({'shipments': 62, 'note': 'SYNTHETIC revised outcome original.'})
        (self.path.parent / 'revised-outcome.json').write_bytes(raw)
        e = evidence(raw)
        ob = copy.deepcopy(self.ledger.load().latest('observation', 'OBS-T-OUT'))
        ob.update(version=2, supersedes=1, revision_reason='SYNTHETIC outcome restatement.', value=62, evidence=[e])
        self.ledger.append('observation', ob)
        c = copy.deepcopy(self.ledger.load().latest('candidate', 'CAND-T-1'))
        c.update(version=2, supersedes=1, revision_reason='SYNTHETIC changed outcome measurement, not a fresh untouched claim.')
        c['outcome'].update(value=62, evidence=[e])
        finish(self.ledger, c)
        state = self.ledger.load()
        self.assertEqual(state.derived[('candidate', c['id'], 2)]['revision_kind'], 'CLARIFICATION')
        self.p.update(ledger={'file': 'ledger.jsonl', 'sha256': G.sha(self.ledger.path.read_bytes())}, ledger_head=state.events[-1]['hash'],
                      candidate={'id': c['id'], 'version': 2, 'sha256': digest(c)}, m_review_id='REV-M-2', selection_history=G.selection_history(state, c['id']))
        ev = copy.deepcopy(self.p['evidence'][0])
        ev.update(id='E2', file='revised-outcome.json', sha256=G.sha(raw), version='v2', passage='SYNTHETIC revised outcome original.')
        self.p['evidence'].append(ev)
        self.p['measurements'][1].update(observation_version=2, value=62, evidence_id='E2')
        self.p['construction'][1]['value'] = 62
        self.p['owner_scope']['evidence_ids'] = ['E1', 'E2']
        self.save()
        self.assertEqual(G.inspect(self.path)['status'], 'INDEPENDENT_REVIEW_REQUIRED', G.inspect(self.path))
        self.assertTrue(self.p['selection_history']['evidence_revised'])
        self.assertTrue(self.p['selection_history']['content_revised'])
        self.p['design']['evaluation'] = 'PROSPECTIVE_UNTOUCHED'
        self.refused('UNTOUCHED_HISTORY_LAUNDERING')

    def test_selection_history_cannot_be_omitted(self):
        self.p['selection_history']['not_untouched'] = False
        self.refused('SELECTION_HISTORY_MISMATCH')

    def test_selected_sample_cannot_be_confirmatory(self):
        self.p['design']['mode'] = 'CONFIRMATORY'
        self.refused('CONFIRMATORY_SELECTED_HISTORY')

    def test_model_human_label_is_not_an_owner_review(self):
        _, review, trust = self.approval()
        review.write_bytes(canonical({'reviewer': {'kind': 'HUMAN', 'name': 'Claude'}, 'approved': True}))
        with patch.object(A, 'verify_signature') as signer:
            result = A.verify(self.path, review, 'none', trust_path=trust)
        self.assertIn('REVIEW_FIELDS_INVALID', result['blocker'])
        signer.assert_not_called()

    def test_unrelated_existing_file_is_not_authority(self):
        _, _, trust = self.approval()
        path = self.root / 'unrelated.json'
        path.write_text('{"owner":"someone","approved":true}')
        self.assertFalse(A.verify(self.path, path, 'none', trust_path=trust)['ready'])

    def test_changed_forge_hypothesis_is_blocked(self):
        self.p['origin']['mapping']['/predictor/quantity']['mapped'] = 'Silently substituted forecast'
        self.refused('FORGE_HANDOFF_CHANGED')

    def test_changed_origin_card_hash_is_blocked(self):
        self.p['origin']['card_sha256'] = '0' * 64
        self.refused('FORGE_ORIGIN_CHANGED')

    def test_population_baseline_and_uncertainty_are_required(self):
        for key in ('eligible_population', 'baseline', 'uncertainty'):
            with self.subTest(key=key):
                old = self.p['design'].pop(key)
                self.refused('STUDY_DESIGN_INCOMPLETE')
                self.p['design'][key] = old
        self.p['design']['uncertainty_plan']['adequacy_check'] = 'UNKNOWN'
        self.refused('UNCERTAINTY_PLAN_INCOMPLETE')

    def test_a_source_route_forecast_is_not_a_realized_outcome(self):
        self.p['measurements'][1]['nature'] = 'FORECAST'
        self.refused('OUTCOME_NOT_REALIZED')

    def test_new_network_or_spend_cannot_hide_in_approved_scope(self):
        self.p['owner_scope']['network_requests'] = 1
        self.refused('OWNER_SCOPE_INVALID')

    def test_prior_approval_invalid_after_any_design_change(self):
        _, review, trust = self.approval()
        self.p['design']['baseline'] = 'Another frozen baseline'
        self.save()
        with patch.object(A, 'verify_signature') as signer:
            result = A.verify(self.path, review, 'none', trust_path=trust)
        self.assertIn('REVIEW_SCOPE_OR_INPUT_CHANGED', result['blocker'])
        signer.assert_not_called()

    def test_packet_cannot_enrol_its_own_trust(self):
        _, review, trust = self.approval()
        embedded = self.path.parent / 'trust.json'
        embedded.write_bytes(trust.read_bytes())
        self.assertIn('independently enrolled', A.verify(self.path, review, 'none', trust_path=embedded)['blocker'])

    def test_synthetic_trust_cannot_approve_live_packet(self):
        _, review, trust = self.approval()
        payload = G.Packet(self.path).check()
        payload['fixture'] = 'LIVE'
        with patch.object(G.Packet, 'check', return_value=payload), patch.object(A, 'verify_signature') as signer:
            self.assertIn('TRUST_FIXTURE_MISMATCH', A.verify(self.path, review, 'none', trust_path=trust)['blocker'])
        signer.assert_not_called()

    def test_inspect_cli_cannot_advance_or_execute(self):
        with redirect_stdout(io.StringIO()) as out:
            code = main(['inspect', str(self.path)])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out.getvalue())['ready'])

    def test_malformed_and_escaping_inputs_fail_closed(self):
        self.p['evidence'][0]['file'] = '../outside.json'
        self.refused('path leaves packet')
        self.path.write_text('{"schema":1,"schema":2}')
        self.assertEqual(G.inspect(self.path)['status'], 'BLOCKED')

    def test_legitimate_multihop_relationship_passes_mechanical_preflight(self):
        def edit(rows):
            parent = D.entity('LEGAL_ENTITY', 'SYN_SUB:ONE', 'Synthetic subsidiary')
            first = rows['relationships'][0]
            first['target_entity'] = parent
            second = copy.deepcopy(first)
            second.update(id='REL-T-2', source_entity=parent, target_entity=rows['candidate']['exposure']['company'])
            rows['relationships'].append(second)
            rows['candidate']['exposure']['relationship_ids'].append(second['id'])
        path, _, _ = make_packet(self.root / 'multihop', edit)
        self.assertEqual(G.inspect(path)['status'], 'INDEPENDENT_REVIEW_REQUIRED', G.inspect(path))

    def test_correct_conversion_is_reproduced(self):
        def edit(rows):
            rows['candidate']['predictor'].update(units='kg/day', transformation='1000 * tonnes/day')
        path, p, _ = make_packet(self.root / 'converted', edit)
        p['construction'][0].update(op='CONVERT', factor=1000, units='kg/day', value=6000)
        path.write_bytes(canonical(p))
        self.assertEqual(G.inspect(path)['status'], 'INDEPENDENT_REVIEW_REQUIRED', G.inspect(path))

    def test_verified_but_unrelated_original_relationship_is_blocked(self):
        def edit(rows):
            rows['relationships'][0]['scope']['asset'] = 'SYN_FACILITY:UNRELATED'
        path, _, _ = make_packet(self.root / 'unrelated-asset', edit)
        result = G.inspect(path)
        self.assertIn('JOIN_ASSET_OR_GEOGRAPHY_MISMATCH', result['blocker'])

    def test_assumed_allocation_is_blocked(self):
        self.p['join']['path'][0]['allocation']['method'] = 'EQUAL_SPLIT'
        self.refused('ALLOCATION_ASSUMPTION')

    def test_declared_history_stays_selected_after_flag_is_cleared(self):
        state = self.ledger.load()
        old = state.latest('candidate', 'CAND-T-1')
        old['selection']['outcome_inspected_before_freeze'] = True
        newer = copy.deepcopy(old)
        newer.update(version=2, supersedes=1, revision_reason='Synthetic clearing attempt.')
        newer['selection']['outcome_inspected_before_freeze'] = False
        state.versions['candidate'][old['id']].append(newer)
        history = G.selection_history(state, old['id'])
        self.assertTrue(history['outcome_or_selection_seen'])
        self.assertTrue(history['not_untouched'])

    def test_later_hold_cannot_reuse_prior_design_candidate(self):
        self.ledger.append('disposition', disposition('DSP-LATER-HOLD'))
        self.p.update(ledger={'file': 'ledger.jsonl', 'sha256': G.sha(self.ledger.path.read_bytes())}, ledger_head=self.ledger.load().events[-1]['hash'])
        self.refused('DISPOSITION_SUPERSEDED')

    def test_later_m_review_cannot_reuse_prior_pass(self):
        self.ledger.append('review', m_review('REV-LATER-M', judgment='NOT_EVIDENCED'))
        self.p.update(ledger={'file': 'ledger.jsonl', 'sha256': G.sha(self.ledger.path.read_bytes())}, ledger_head=self.ledger.load().events[-1]['hash'])
        self.refused('M_REVIEW_SUPERSEDED')

    def test_binary_original_can_be_recorded_but_needs_signed_human_mapping(self):
        self.p['evidence'][0]['format'] = 'BINARY_HUMAN_LOCATION'
        self.p['financial_crosswalk']['extraction'] = 'HUMAN_PASSAGE'
        for measurement in self.p['measurements']:
            measurement['extraction'] = 'HUMAN_PASSAGE'
        self.save()
        result = G.inspect(self.path)
        self.assertEqual(result['status'], 'INDEPENDENT_REVIEW_REQUIRED', result)
        self.assertFalse(result['ready'])

    def test_gross_scale_is_bound_to_an_original_value(self):
        self.p['financial_crosswalk']['location'] = '/shipments'
        self.refused('FINANCIAL_VALUE_MISMATCH')

    def test_reversed_documented_ownership_edge_is_supported(self):
        def edit(rows):
            r = rows['relationships'][0]
            r['source_entity'], r['target_entity'] = r['target_entity'], r['source_entity']
        path, p, _ = make_packet(self.root / 'reverse-ownership', edit)
        p['join']['path'][0]['traversal'] = 'REVERSE'
        path.write_bytes(canonical(p))
        self.assertEqual(G.inspect(path)['status'], 'INDEPENDENT_REVIEW_REQUIRED', G.inspect(path))


class HistoricalCompatibilityTests(unittest.TestCase):
    def test_six_historical_ledgers_replay_185_events_with_identical_bytes(self):
        root = Path(__file__).resolve().parents[1] / 'docs/strategy/graph_pilot_r3'
        expected = {'P3/G': 'a3c9c9d29b9d51833c8cb7c9bbed228cd5ef9fd5e22aa1577b33a7d9e0c09976',
                    'P3/packet': '80bd004c63a45b6b926516f023e61334c2dc03cce5086695322303e93c488d1e',
                    'P3/S': '38dbddf07cd4e14a79a4f55f1f9c3483bc2fa3378d3100db7f507c289798fda7',
                    'P4/G': 'f9cdb32e1c68322567ce5e040b068a53fcc62baf25c55d942a31eaf051e9efae',
                    'P4/packet': '144190ad880797cd8e8712963014462d44f43de1f2777bb8d40cef39f686e170',
                    'P4/S': 'acf48638eb907ace2b82a9a761549987ad60485ede98154dc114b03ac4c1cf5f'}
        total = 0
        for name, expected_hash in expected.items():
            path = root / (name + '.jsonl')
            raw = path.read_bytes()
            self.assertEqual(G.sha(raw), expected_hash)
            total += len(Ledger(path).load().events)
            self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(total, 185)
