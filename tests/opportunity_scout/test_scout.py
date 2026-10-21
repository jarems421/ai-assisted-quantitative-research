from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import engine as E, schema as S, workflow as W
from src.research.opportunity_scout import evaluation as V
from src.research.opportunity_scout.storage import Archive, ROOT, input_json
from src.research.opportunity_scout.fixtures import MOMENT, seed, idea, provenance
from src.research.opportunity_scout.providers import JevShadowClient, OllamaProvider, shadow_request, QUESTIONS
from src.research.opportunity_scout.reviews import reconsider


class ScoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Archive(Path(self.temp.name) / 'batch')
        W.initialise(self.archive, 'SYNTHETIC software tests', fixture='SYNTHETIC', with_memory=False, moment=MOMENT)

    def generate(self, family='CAPACITY_COMPETITION', lane='FORGE', body=None):
        if lane == 'RADAR' and not self.archive.load().seeds: self.archive.append('seed', seed(), recorded_at=MOMENT)
        aid, _ = W.prepare(self.archive, lane, 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
        state = W.finish(self.archive, aid, canonical({'ideas': [body or idea(family, lane)]}).decode(), provenance(), moment=MOMENT)
        return state, next(reversed(state.cards)) if state.cards else None

    def review(self, iid, decision='READY', reason_type='RESEARCHABLE'):
        return {'idea_id': iid, 'version': self.archive.load().latest(iid)['version'], 'decision': decision,
            'reason_type': reason_type, 'reason': 'SYNTHETIC workflow decision only; no real human judgment.',
            'uncertainties': ['Synthetic assumptions remain unverified.'],
            'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'}, 'minutes': S.UNKNOWN,
            'approved_handoff': decision == 'READY', 'reconsider_when': 'A dated original must resolve the declared allocation.',
            'authorises_acquisition': False}

    def test_speculative_idea_survives_without_evidence(self):
        state, iid = self.generate()
        assessed = W.triage(self.archive)
        self.assertEqual(assessed.route(assessed.latest(iid)), 'INCUBATE')
        self.assertEqual(state.latest(iid)['original_seed'], 'NONE_YET')
        self.assertEqual(state.latest(iid)['evidence_state'], 'GENERATED_CLAIM')

    def test_three_lane_contexts_are_independent(self):
        self.archive.append('seed', seed(), recorded_at=MOMENT)
        _, forge = W.prepare(self.archive, 'FORGE', 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
        _, radar = W.prepare(self.archive, 'RADAR', 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
        self.assertEqual(forge['context'], {'seeds': {}, 'memory': {}})
        self.assertNotIn('cards', str(forge['context']))
        self.assertTrue(radar['context']['seeds'])
        self.assertNotEqual(forge['instructions'], radar['instructions'])
        self.assertFalse(forge['contains_generated_ideas'])

    def test_radar_and_gap_require_their_real_inputs(self):
        with self.assertRaises(S.ScoutError): W.prepare(self.archive, 'RADAR', 1, 'x', moment=MOMENT)
        with self.assertRaises(S.ScoutError): W.prepare(self.archive, 'GAP', 1, 'x', moment=MOMENT)

    def test_forge_cannot_claim_unseen_source_or_history(self):
        card = idea(); card['seed_ids'] = ['SEED-FIXTURE']
        state, _ = self.generate(body=card)
        self.assertFalse(state.cards)
        result = next(iter(state.attempts.values()))['result']
        self.assertEqual(result['status'], 'INVALID')
        self.assertIn('SEED-FIXTURE', result['raw_response'])

    def test_fabricated_citation_cannot_become_a_fact(self):
        card = idea(); card['mechanism']['links'][0]['evidence'] = [{'seed': 'SEED-MISSING', 'quote': 'invented'}]
        state, _ = self.generate(body=card)
        self.assertFalse(state.cards)
        self.assertIn('fabricated', next(iter(state.attempts.values()))['result']['error'])

    def test_metadata_cannot_be_promoted_to_documented_economic_link(self):
        card = idea(lane='RADAR'); card['mechanism']['links'][0].update(basis='DOCUMENTED',
            evidence=[{'seed': 'SEED-FIXTURE', 'quote': seed()['text']}])
        state, _ = self.generate(lane='RADAR', body=card)
        self.assertFalse(state.cards)

    def test_seed_hash_must_match_and_original_depth_is_inherited_only(self):
        s = seed(); s['sha256'] = '0' * 64
        with self.assertRaises(S.ScoutError): self.archive.append('seed', s)

    def original_seed(self):
        from src.research.discovery.demo import rec, syn, clocks, entity
        s = seed(); s['depth'] = 'VERIFIED_ORIGINAL_FIELD'; s['evidence_kind'] = 'ORIGINAL_DOCUMENT'
        evidence = syn('workshop/index-v1', passage=s['text']); evidence['sha256'] = s['sha256']; evidence['locator'] = s['locator']
        observation = rec('observation', id='OBS-SCOUT-CONTROL', source_id='SRC-SCOUT-CONTROL',
            kind='QUANTITY', statement=s['text'], value=12, units='inspection shifts per week', denominator='one fictional workshop',
            entity=entity('FACILITY', 'SYN_FACILITY:SCOUT', 'Fictional workshop'), depth='VERIFIED_ORIGINAL_FIELD',
            evidence=[evidence], clocks=clocks('UNKNOWN'), as_of_status='VERIFIED_ONLY_RETROSPECTIVELY',
            why_informative='SYNTHETIC field inheritance test only.', alternative_explanations=[], prior_disclosure='UNKNOWN',
            outcome_independent=False, related=[], missing_evidence=['No real source or economic outcome exists.'])
        s['discovery_observation'] = observation
        return s

    def test_existing_original_field_is_inherited_with_exact_artifact_binding(self):
        s = self.original_seed(); S.validate_seed(s)
        self.assertEqual(S.seed_state(s), 'ORIGINAL_FIELD_VERIFIED')
        self.archive.append('seed', s, recorded_at=MOMENT)
        state, iid = self.generate(lane='RADAR')
        self.assertEqual(state.latest(iid)['evidence_support'][0]['mapped_state'], 'ORIGINAL_FIELD_VERIFIED')
        self.assertFalse(state.latest(iid)['evidence_support'][0]['scout_certifies'])

    def test_mismatched_original_hash_cannot_become_verified_support(self):
        s = self.original_seed(); s['discovery_observation']['evidence'][0]['sha256'] = '0' * 64
        with self.assertRaises(S.ScoutError): S.validate_seed(s)

    def test_contradicted_assertion_is_preserved_and_never_promoted(self):
        s = self.original_seed(); s['discovery_observation']['as_of_status'] = 'CONTRADICTED'
        S.validate_seed(s); self.assertEqual(S.seed_state(s), 'CONTRADICTED')
        self.archive.append('seed', s, recorded_at=MOMENT)
        card = idea(lane='RADAR'); card['mechanism']['links'][0].update(basis='DOCUMENTED', statement=s['text'],
            evidence=[{'seed': s['id'], 'quote': s['text']}])
        state, _ = self.generate(lane='RADAR', body=card)
        self.assertFalse(state.cards)
        s = seed(); s['depth'] = 'VERIFIED_ORIGINAL_FIELD'
        with self.assertRaises(S.ScoutError): self.archive.append('seed', s)

    def test_first_public_not_derived_from_event_or_document_date(self):
        s = seed(); s['clocks']['first_public'] = {'value': MOMENT, 'basis': 'DOCUMENT_DATE', 'certificate': None}
        with self.assertRaises(S.ScoutError): S.validate_seed(s)
        self.assertEqual(seed()['clocks']['first_public']['value'], 'UNKNOWN')

    def test_invalid_chain_preserves_raw_generation_and_error(self):
        card = idea(); card['mechanism']['links'][0]['to'] = 'CONSEQUENCE'
        state, _ = self.generate(body=card)
        self.assertEqual(len(state.attempts), 1)
        self.assertFalse(state.cards)
        self.assertEqual(next(iter(state.attempts.values()))['result']['status'], 'INVALID')

    def test_json_duplicates_nan_and_extra_fields_are_refused(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(S.ScoutError): S.json_loads(value)
        c = idea(); c['alpha_certified'] = True
        state, _ = self.generate(body=c)
        self.assertFalse(state.cards)

    def test_generation_budget_has_no_silent_retry_or_fixture_fallback(self):
        archive = Archive(Path(self.temp.name) / 'bounded')
        W.initialise(archive, 'bounded', fixture='SYNTHETIC', with_memory=False, max_attempts=1, moment=MOMENT)
        W.prepare(archive, 'FORGE', 1, 'x', moment=MOMENT)
        with self.assertRaises(S.ScoutError): W.prepare(archive, 'FORGE', 1, 'x', moment=MOMENT)
        self.assertEqual(len(archive.load().attempts), 1)

    def test_response_size_candidate_count_and_token_budget_are_enforced(self):
        aid, _ = W.prepare(self.archive, 'FORGE', 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
        p = provenance(); p['usage']['output_tokens'] = 7000
        state = W.finish(self.archive, aid, canonical({'ideas': [idea()]}).decode(), p, moment=MOMENT)
        self.assertFalse(state.cards)
        self.assertEqual(state.attempts[aid]['result']['status'], 'ERROR')

    def test_unknown_cost_and_review_time_remain_unknown(self):
        state, _ = self.generate()
        rep = V.report(state)
        self.assertEqual(rep['generation']['unknown_cost_entries'], 1)
        self.assertIsNone(rep['human_work']['handoffs_per_human_hour'])
        self.assertIsNone(rep['jev']['brier_score'])

    def test_exact_and_reworded_duplicates_are_not_economic_identity(self):
        state, first = self.generate()
        c = idea(); c['title'] = 'Completely different wording for the same core'
        state, second = self.generate(body=c)
        matches = E.proximity(state, state.latest(second))
        self.assertTrue(any(m['kind'] == 'EXACT_CORE_DUPLICATE' for m in matches))
        c['mechanism']['transmission'] = 'Alternative prose describes the identical fixed capacity allocation mechanism.'
        state, third = self.generate(body=c)
        self.assertTrue(any(m['kind'] == 'POSSIBLE_MECHANISM_DUPLICATE' and not m['economic_identity_established'] for m in E.proximity(state, state.latest(third))))

    def test_shortlist_preserves_speculation_and_multiple_mechanisms(self):
        for family in ('CAPACITY_COMPETITION', 'WORKING_CAPITAL', 'COMPLEMENT_DEMAND'): self.generate(family)
        state = W.triage(self.archive); selected = E.select(state)
        self.assertTrue(selected['speculative_slot_reserved'])
        self.assertEqual(len(selected['selected']), 3)
        self.assertEqual(len(selected['all_candidates']), 3)
        self.assertNotIn('quality_score', str(selected))

    def test_source_stop_cannot_be_reopened_by_generation(self):
        s = seed(); s['access'] = 'STOPPED'; self.archive.append('seed', s, recorded_at=MOMENT)
        c = idea(lane='RADAR'); c['source_routes'][0]['locator'] = s['locator']; c['source_routes'][0]['state'] = 'UNTESTED'
        state, _ = self.generate(lane='RADAR', body=c)
        self.assertFalse(state.cards)

    def test_source_access_failure_cannot_reject_a_coherent_mechanism(self):
        _, iid = self.generate(); W.triage(self.archive)
        with self.assertRaises(S.ScoutError): self.archive.append('review', self.review(iid, 'REJECT', 'SOURCE_ACCESS'))
        self.assertEqual(self.archive.load().route(self.archive.load().latest(iid)), 'INCUBATE')

    def test_no_automatic_ready_or_handoff(self):
        state, iid = self.generate(); W.triage(self.archive)
        with self.assertRaises(S.ScoutError): E.handoff(self.archive.load(), iid)
        self.assertFalse(E.assess(state, state.latest(iid))['checks']['software_certifies_M'])

    def test_explicit_review_produces_proposal_not_a_discovery_record(self):
        _, iid = self.generate(); W.triage(self.archive)
        self.archive.append('review', self.review(iid))
        p = E.handoff(self.archive.load(), iid)
        self.assertEqual(p['status'], 'PROPOSAL_ONLY')
        self.assertFalse(p['is_discovery_candidate_record'])
        self.assertFalse(p['creates_campaign']); self.assertFalse(p['acquisition_authorised']); self.assertFalse(p['certifies_M'])

    def test_human_routing_is_reversible_and_old_decisions_remain(self):
        _, iid = self.generate(); W.triage(self.archive)
        self.archive.append('review', self.review(iid))
        self.archive.append('review', self.review(iid, 'INCUBATE', 'UNRESOLVED'))
        state = self.archive.load()
        self.assertEqual(len(state.reviews), 2)
        self.assertEqual(state.route(state.latest(iid)), 'INCUBATE')

    def test_synthetic_and_actual_human_labels_do_not_mix(self):
        _, iid = self.generate(); W.triage(self.archive)
        r = self.review(iid); r['reviewer']['kind'] = 'HUMAN'
        with self.assertRaises(S.ScoutError): self.archive.append('review', r)

    def test_revisions_preserve_initial_features_and_reset_approval(self):
        state, iid = self.generate(); original = copy.deepcopy(state.latest(iid)); W.triage(self.archive)
        self.archive.append('review', self.review(iid))
        changed = copy.deepcopy(original['idea']); changed['predictor']['quantity'] = 'A materially different independent customer quantity'
        self.archive.append('revision', {'idea_id': iid, 'from_version': 1, 'idea': changed, 'reason': 'Synthetic material correction after inspection.',
            'actor': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_EDITOR'}, 'after_outcome_known': True})
        state = self.archive.load()
        self.assertEqual(state.cards[iid][0], original)
        self.assertEqual(state.latest(iid)['revision_kind'], 'MATERIAL_REFORMULATION')
        self.assertEqual(state.latest(iid)['initial_features'], original['initial_features'])
        with self.assertRaises(S.ScoutError): E.handoff(state, iid)

    def test_reconsideration_requires_exact_requirement_and_never_promotes(self):
        _, iid = self.generate(); W.triage(self.archive)
        self.archive.append('seed', seed())
        state = self.archive.load()
        lead = reconsider(state, 'SEED-FIXTURE', ['REQ_DOCUMENTED_ALLOCATION'], [])
        self.assertEqual(len(lead['leads']), 1)
        self.assertTrue(lead['leads'][0]['suggestion_only'])
        self.archive.append('reconsideration', lead)
        self.assertEqual(self.archive.load().route(self.archive.load().latest(iid)), 'INCUBATE')
        self.assertFalse(reconsider(state, 'SEED-FIXTURE', [], ['LEI:LOOKALIKE'])['leads'])
        with self.assertRaises(S.ScoutError): reconsider(state, 'SEED-FIXTURE', [], ['NAME:Workshop'])

    def test_external_novelty_requires_independent_evidence_backed_findings(self):
        _, iid = self.generate()
        r = {'idea_id': iid, 'version': 1, 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'INDEPENDENT_SYNTHETIC'},
            'independent_of_generator': True, 'external_status': 'NO_SUBSTANTIVE_MATCH_IN_DECLARED_SEARCH',
            'structural_status': 'UNCERTAIN', 'search_queries': [], 'evidence': [], 'limits': ['No actual search occurred.'],
            'reviewed_at': MOMENT, 'private_investor_use': 'UNKNOWN', 'minutes': 'UNKNOWN'}
        with self.assertRaises(S.ScoutError): self.archive.append('novelty', r)

    def test_shadow_distribution_never_changes_routing(self):
        state, iid = self.generate(); W.triage(self.archive); state = self.archive.load()
        response = {'model': 'jev-1.13.0', 'usage': {'input_tokens': 100, 'output_tokens': 20},
            'answers': {q: {'type': 'choice', 'choice': 'no', 'probabilities': {'yes': .01, 'no': .98, 'unsure': .01}, 'confidence': .97} for q in QUESTIONS}}
        self.archive.append('shadow', {'idea_id': iid, 'version': 1, 'request_sha256': digest(shadow_request(state, iid)),
            'response': response, 'imported_at': MOMENT, 'cost': 'UNKNOWN', 'currency': 'UNKNOWN',
            'shadow_only': True, 'transport': 'SYNTHETIC_FIXTURE'})
        new = self.archive.load()
        self.assertEqual(new.route(new.latest(iid)), 'INCUBATE')
        self.assertEqual(len(new.shadows), 1)

    def test_jev_requires_separate_payload_approval_and_no_key_is_assumed(self):
        transport = unittest.mock.Mock()
        client = JevShadowClient(transport)
        with self.assertRaises(S.ScoutError): client.call({'private': 'never send'}, key='FAKE_TEST_KEY')
        transport.assert_not_called()
        approval = {'payload_sha256': digest({}), 'owner_approved': True, 'classification': 'SYNTHETIC_APPROVED', 'authority_reference': 'SYNTHETIC TEST ONLY'}
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(S.ScoutError): client.call({}, approval=approval)
        transport.assert_not_called()

    def test_ollama_wire_boundary_is_local_bounded_and_not_a_fixture_fallback(self):
        state = self.archive.load()
        _, prompt = W.prepare(self.archive, 'FORGE', 1, 'LOCAL_TEST_MODEL', 'SYNTHETIC_FIXTURE', moment=MOMENT)
        seen = []
        def transport(endpoint, payload):
            seen.append((endpoint, payload))
            return {'model': 'LOCAL_TEST_MODEL', 'done': True, 'response': canonical({'ideas': [idea()]}).decode()}, 'SYNTHETIC TRANSPORT BODY'
        raw, p, body = OllamaProvider('LOCAL_TEST_MODEL', transport).generate(prompt)
        self.assertEqual(seen[0][0], 'http://127.0.0.1:11434/api/generate')
        self.assertFalse(seen[0][1]['stream']); self.assertEqual(seen[0][1]['options']['num_predict'], 6000)
        self.assertEqual(p['usage']['cost'], 'UNKNOWN')
        self.assertEqual(p['provider'], 'OLLAMA_LOCAL')

    def test_modified_hash_chain_and_recomputed_rule_bypass_both_fail(self):
        state, iid = self.generate(); W.triage(self.archive)
        events = [json.loads(x) for x in self.archive.file.read_text().splitlines()]
        events[-1]['record']['recommended_route'] = 'READY'
        events[-1]['hash'] = digest({k: v for k, v in events[-1].items() if k != 'hash'})
        self.archive.file.write_bytes(b''.join(canonical(e) + b'\n' for e in events))
        with self.assertRaises(S.ScoutError): self.archive.load()

    def test_unsafe_paths_output_overwrites_and_unterminated_event_fail_closed(self):
        for location in (ROOT / 'docs/strategy/discovery', ROOT / 'src', ROOT / 'experiments'):
            with self.subTest(path=location), self.assertRaises(S.ScoutError): Archive(location)
        for name in ('../escape.json', 'x/y.json', 'C:stream.json'):
            with self.assertRaises(S.ScoutError): self.archive.export(name, {})
        self.archive.export('one.json', {})
        with self.assertRaises(FileExistsError): self.archive.export('one.json', {})
        self.archive.file.write_bytes(self.archive.file.read_bytes().rstrip(b'\n'))
        with self.assertRaises(S.ScoutError): self.archive.load()

    def test_credential_and_private_raw_inputs_are_not_opened(self):
        for location in (ROOT / '.env', ROOT / 'data/raw/private.json', ROOT / 'docs/strategy/graph_pilot_r3/P3-G.json'):
            with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
                with self.assertRaises(S.ScoutError): input_json(location)

    def test_another_git_worktree_is_outside_scout_archive_scope(self):
        other = Path(self.temp.name) / 'other-worktree'
        other.mkdir(); (other / '.git').write_text('gitdir: synthetic-test-marker')
        with self.assertRaises(S.ScoutError): Archive(other / 'docs/strategy/pilot')

    def test_later_outcomes_do_not_change_frozen_selection_or_generation_features(self):
        state, iid = self.generate(); W.triage(self.archive)
        state = self.archive.load(); before = E.select(state); initial = copy.deepcopy(state.latest(iid))
        self.archive.append('outcome', {'idea_id': iid, 'version': 1, 'label': 'SOURCE_BLOCKED',
            'reference': {'locator': 'synthetic://source-stop', 'sha256': 'a' * 64, 'quote': 'SYNTHETIC source access failure.'},
            'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'}, 'recorded_elsewhere_at': MOMENT,
            'reason': 'An original route was inaccessible; the mechanism remains untested.',
            'outcome_was_known_before_revision': False, 'human_decision_reference_only': True, 'scout_certifies': False})
        after = self.archive.load()
        self.assertEqual(E.select(after), before)
        self.assertEqual(after.latest(iid), initial)
        self.assertEqual(V.report(after)['learning_labels']['recorded_outcomes'], {'SOURCE_BLOCKED': 1})

    def test_memory_reads_no_active_ledgers_and_preserves_verdicts(self):
        from src.research.opportunity_scout.memory import snapshot
        from src.research.discovery.ledger import Ledger
        with patch('src.research.graph.project.discover_ledgers', side_effect=AssertionError('no discovery')), \
             patch.object(Ledger, 'load', side_effect=AssertionError('no pilot reads')), \
             patch.object(socket, 'create_connection', side_effect=AssertionError('offline')):
            memory = snapshot()
        self.assertEqual(len(memory['investigations']), 7)
        self.assertEqual(memory['ledgers_read'], [])
        self.assertIn('HOLD', memory['investigations']['HIST-F19']['verdict']['text'])
        self.assertIn('STOP', memory['investigations']['HIST-SH09']['verdict']['text'])

    def test_demo_is_reproducible_and_no_human_labels_or_model_calls_are_invented(self):
        from src.research.opportunity_scout.demo import run
        with patch.object(socket, 'create_connection', side_effect=AssertionError('offline')):
            a, b = run(), run()
        self.assertEqual(a, b)
        self.assertEqual(len(a['cards']), 6)
        self.assertEqual(a['model_calls'], 0)
        self.assertEqual(a['real_human_reviews'], 0)
        self.assertEqual(a['report']['conditions']['PLAIN'], 'NOT_RUN')
        for c in a['negative_controls']: self.assertEqual(c['valid'], c['expected_schema_valid'], c['id'])


if __name__ == '__main__': unittest.main()
