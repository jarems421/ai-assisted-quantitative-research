"""Acceptance controls. Every output and human decision here is a test double."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import schema as S, engine as E, workflow as W, evaluation as V
from src.research.opportunity_scout import comparison as C
from src.research.opportunity_scout.accounting import generation, fairness
from src.research.opportunity_scout.fixtures import idea, provenance, feasibility, MOMENT
from src.research.opportunity_scout.storage import Archive, ROOT
from tests.opportunity_scout import test_evaluation as evaluation_fixtures


class ReadinessAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.archive = Archive(Path(self.temp.name) / 'control')
        W.initialise(self.archive, 'UNIT TEST, not real generation or human approval', with_memory=False, moment=MOMENT)

    def card(self, route=None):
        body = idea()
        body['source_routes'][0].update(route or {'publisher': 'UK Cabinet Office', 'locator': 'https://www.gov.uk/contracts-finder'})
        aid, _ = W.prepare(self.archive, 'FORGE', 1, 'UNIT_TEST_GENERATOR', moment=MOMENT)
        p = provenance(provider='OPERATOR_ASSISTED'); p['model'] = 'UNIT_TEST_GENERATOR'
        state = W.finish(self.archive, aid, canonical({'ideas': [body]}).decode(), p, moment=MOMENT)
        W.triage(self.archive)
        return next(v[-1] for v in state.cards.values())

    def finding(self, card):
        finding = feasibility(card)
        finding['reviewer'] = {'kind': 'HUMAN', 'id': 'UNIT_TEST_HUMAN_DOUBLE'}
        finding['assessment'] = ('A bounded search of named equipment lease awards and attached maintenance schedules '
            'could identify the retained maintenance unit and counterparty. Schedules and independent invoices may be absent; '
            'that is the decisive first check, not an asserted measurement.')
        finding['remaining_unknowns'] = ['No original schedule, invoice, allocation or access has been verified.']
        return finding

    def review(self, card):
        return {'readiness_version': 'SCOUT_READY_V002', 'idea_id': card['id'], 'version': card['version'],
            'decision': 'READY', 'reason_type': 'RESEARCHABLE',
            'reason': 'UNIT TEST human double approves a bounded proposed measurement question only.',
            'uncertainties': ['All allocations and source availability remain unverified.'],
            'reviewer': {'kind': 'HUMAN', 'id': 'UNIT_TEST_HUMAN_DOUBLE'}, 'minutes': 'UNKNOWN',
            'approved_handoff': True, 'reconsider_when': 'Inspect the relevant published schedule after separate authority.',
            'authorises_acquisition': False}

    def test_placeholders_cannot_be_ready_even_with_a_human_feasibility_record(self):
        card = self.card({'publisher': 'Some original contract publisher', 'locator': 'PROPOSAL_ONLY: some original contract'})
        self.archive.append('feasibility', self.finding(card))
        with self.assertRaisesRegex(S.ScoutError, 'identifiable publisher'): self.archive.append('review', self.review(card))
        state = self.archive.load()
        self.assertEqual(state.route(state.latest(card['id'])), 'INCUBATE')

    def test_identifiable_route_alone_is_insufficient_but_speculation_can_receive_human_approval(self):
        card = self.card()
        with self.assertRaises(S.ScoutError): self.archive.append('review', self.review(card))
        self.archive.append('feasibility', self.finding(card))
        self.archive.append('review', self.review(card))
        state = self.archive.load(); proposal = E.handoff(state, card['id'])
        self.assertTrue(E.assess(state, card)['speculative'])
        self.assertEqual(card['idea']['source_routes'][0]['state'], 'UNTESTED')
        self.assertEqual(card['idea']['source_routes'][0]['evidence'], [])
        self.assertEqual(proposal['status'], 'PROPOSAL_ONLY')
        self.assertFalse(proposal['certifies_M']); self.assertFalse(proposal['acquisition_authorised'])

    def test_wrong_question_assistant_and_later_access_failure_cannot_satisfy_handoff(self):
        card = self.card(); finding = self.finding(card)
        wrong = copy.deepcopy(finding); wrong['measurement_question'] = 'Is this a popular industry?'
        with self.assertRaises(S.ScoutError): self.archive.append('feasibility', wrong)
        assistant = copy.deepcopy(finding); assistant['reviewer']['kind'] = 'ASSISTANT'
        self.archive.append('feasibility', assistant)
        with self.assertRaises(S.ScoutError): self.archive.append('review', self.review(card))
        self.archive.append('feasibility', finding); self.archive.append('review', self.review(card))
        finding['state'] = 'INACCESSIBLE'; finding['conclusion'] = 'NOT_FEASIBLE'
        self.archive.append('feasibility', finding)
        with self.assertRaises(S.ScoutError): E.handoff(self.archive.load(), card['id'])

    def test_legacy_ready_replays_but_cannot_be_newly_appended_or_handed_off(self):
        card = self.card(); review = self.review(card); del review['readiness_version']
        with self.assertRaises(S.ScoutError): self.archive.append('review', review)
        state = self.archive.load()
        # Construct an authentic V001-style hash envelope to test historical replay only.
        core = {'seq': len(state.events) + 1, 'type': 'review', 'recorded_at': state.events[-1]['recorded_at'],
                'previous': state.events[-1]['hash'], 'record': review}
        with self.archive.file.open('ab') as f: f.write(canonical({**core, 'hash': digest(core)}) + b'\n')
        original = self.archive.file.read_bytes(); state = self.archive.load()
        self.assertEqual(state.current_review(card), review)
        self.assertEqual(self.archive.file.read_bytes(), original)
        with self.assertRaises(S.ScoutError): E.handoff(state, card['id'])

    def test_quality_audit_keeps_structure_feasibility_novelty_and_findings_separate(self):
        card = self.card(); self.archive.append('feasibility', self.finding(card)); self.archive.append('review', self.review(card))
        audit = V.quality_audit(self.archive.load()); row = audit['cards'][0]
        self.assertEqual(audit['distinct_mechanism_labels'], 1)
        self.assertEqual(audit['substantive_mechanism_diversity'], 'NOT_CHECKED')
        self.assertEqual(row['structural_warnings'], [])
        self.assertEqual(row['substantive_economic_coherence'], 'NOT_CHECKED')
        self.assertEqual(row['external_novelty'], 'NOT_CHECKED')
        self.assertEqual(row['source_verification'], 'NOT_CHECKED')
        self.assertEqual(row['human_feasibility'], 'RESEARCHABLE_PROPOSAL')
        self.assertEqual(row['validated_economic_finding'], 'NOT_ESTABLISHED')
        self.assertIsNone(audit['composite_score'])


class AccountingAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse generation fixtures, not their tests or purported real labels.
        evaluation_fixtures.EvaluationTests.setUpClass()
        cls.addClassCleanup(evaluation_fixtures.EvaluationTests.tearDownClass)

    def states(self):
        states = copy.deepcopy(evaluation_fixtures.EvaluationTests.states)
        for name, state in states.items():
            for aid, attempt in state.attempts.items():
                attempt['result']['provider']['usage'].update({'input_tokens': 1500, 'output_tokens': 2000})
                state.efforts.append({'kind': 'GENERATION_ATTEMPT', 'attempt_id': aid,
                    'actor': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'TEST_DOUBLE'},
                    'human_minutes': 1, 'wall_seconds': 5, 'context_id': name + aid,
                    'invocation_status': 'INVOKED',
                    'fresh_context': 'YES', 'no_prior_generated_cards': 'YES', 'description': 'Synthetic accounting control.'})
        return states

    def test_actual_attempt_counts_are_checked_even_with_six_cards_and_equal_ceilings(self):
        states = self.states(); states['PLAIN'].attempts.pop('ATT-0003')
        audit = fairness(states, V.protocol('V002')['budget_per_condition'])
        self.assertFalse(audit['actual_attempt_counts_equal']); self.assertFalse(audit['comparative_eligible'])
        with self.assertRaises(S.ScoutError): V.blind(states, 'UNIT_TEST_PRIVATE_SALT_12345')

    def test_missing_usage_and_effort_remain_unknown_with_known_subtotals(self):
        states = self.states(); state = states['PLAIN']; state.efforts.pop()
        state.attempts['ATT-0001']['result']['provider']['usage']['output_tokens'] = 'UNKNOWN'
        audit = fairness(states, V.protocol('V002')['budget_per_condition'])
        totals = audit['conditions']['PLAIN']['totals']
        self.assertEqual(totals['output_tokens'], {'known_total': 4000, 'unknown_entries': 1, 'total': 'UNKNOWN'})
        self.assertEqual(totals['human_minutes']['total'], 'UNKNOWN')
        self.assertFalse(audit['comparative_eligible']); self.assertTrue(audit['incomplete_records'])
        self.assertEqual(audit['conditions']['PLAIN']['invoked_reported'], 2)
        self.assertEqual(audit['conditions']['PLAIN']['invocation_unknown'], 1)
        self.assertEqual(audit['actual_attempt_counts_equal'], 'UNKNOWN')

    def test_actual_effort_differences_within_caps_are_reported_without_rebalancing(self):
        states = self.states(); states['PLAIN'].efforts[0]['wall_seconds'] = 20
        audit = fairness(states, V.protocol('V002')['budget_per_condition'])
        self.assertTrue(audit['comparative_eligible']); self.assertFalse(audit['actual_effort_equal']['wall_seconds'])
        self.assertEqual(audit['conditions']['PLAIN']['totals']['wall_seconds']['total'], 30)

    def test_reused_context_mixed_models_and_token_excess_are_deviations(self):
        for change in ('context', 'model', 'tokens', 'failed', 'not_invoked'):
            with self.subTest(change=change):
                states = self.states(); state = states['PLAIN']
                if change == 'context': state.efforts[0]['context_id'] = states['HYBRID'].efforts[0]['context_id']
                if change == 'model': state.attempts['ATT-0001']['result']['provider']['model'] = 'OTHER_MODEL'
                if change == 'tokens': state.attempts['ATT-0001']['result']['provider']['usage']['input_tokens'] = 30001
                if change == 'failed': state.attempts['ATT-0001']['result']['status'] = 'ERROR'
                if change == 'not_invoked': state.efforts[0]['invocation_status'] = 'NOT_INVOKED'
                audit = fairness(states, V.protocol('V002')['budget_per_condition'])
                self.assertFalse(audit['comparative_eligible']); self.assertTrue(audit['deviations'])

    def test_blinded_packet_discloses_incomplete_accounting_without_revealing_conditions(self):
        packet, key = V.blind(evaluation_fixtures.EvaluationTests.states, 'UNIT_TEST_PRIVATE_SALT_12345')
        self.assertFalse(packet['comparative_eligible'])
        self.assertNotIn('conditions', packet)
        self.assertTrue(key['accounting']['incomplete_records'])
        result = V.evaluate_blind(packet, key, [])
        self.assertFalse(result['comparative_eligible'])

    def test_v002_requires_independent_review_attestation_and_reports_review_budget(self):
        from src.research.opportunity_scout.providers import QUESTIONS
        packet, key = V.blind(self.states(), 'UNIT_TEST_PRIVATE_SALT_12345', version='V002', binding={'fixture': 'SYNTHETIC'})
        rows = [{'blind_id': c['blind_id'], 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'TEST_ONLY'},
            'independent_of_generation': True, 'coherent': 'UNKNOWN', 'falsifiable': 'UNKNOWN',
            'research_worthy': 'UNKNOWN', 'evidence_integrity': 'UNKNOWN', 'minutes': 10,
            'notes': 'Synthetic reviewer fixture only.', 'atomic_answers': {q: 'unsure' for q in QUESTIONS}}
            for c in packet['cards']]
        self.assertFalse(V.evaluate_blind(packet, key, [])['comparative_eligible'])
        self.assertTrue(V.evaluate_blind(packet, key, rows)['comparative_eligible'])
        changed = copy.deepcopy(rows); changed[0]['independent_of_generation'] = False
        with self.assertRaises(S.ScoutError): V.evaluate_blind(packet, key, changed)
        changed = copy.deepcopy(rows); changed[0]['minutes'] = 'UNKNOWN'
        self.assertFalse(V.evaluate_blind(packet, key, changed)['comparative_eligible'])
        changed = copy.deepcopy(rows); changed[0]['minutes'] = 181
        result = V.evaluate_blind(packet, key, changed)
        self.assertFalse(result['comparative_eligible'])
        self.assertTrue(any(x['over_budget'] for x in result['review_effort'].values()))


class PackageAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        C.freeze(self.root / 'frozen', ROOT / 'docs/opportunity_scout/operator_example/seeds.json')

    def test_package_is_reproducible_with_twelve_new_prompts_and_no_generated_cards(self):
        original = C.status(self.root / 'frozen')
        C.install(self.root / 'replay', self.root / 'frozen/exports')
        self.assertEqual(C.status(self.root / 'replay'), original)
        requests = C.requests(self.root / 'replay')['requests']
        self.assertEqual(len(requests), 12)
        self.assertEqual(len(C.requests(self.root / 'replay')['requests']), 12)
        _, _, states = C.load(self.root / 'replay')
        self.assertEqual({len(s.cards) for s in states.values()}, {0})
        self.assertEqual(len({digest(s.seeds) for s in states.values()}), 1)
        self.assertEqual(len({digest(s.batch['memory']) for s in states.values()}), 1)
        self.assertTrue(all(not p['contains_generated_ideas'] for s in states.values() for p in s.prompts.values()))
        self.assertFalse(original['fairness']['comparative_eligible'])

    def test_changed_blueprint_and_late_model_binding_are_refused(self):
        root, _, states = C.load(self.root / 'frozen')
        archive = Archive(root.path / 'PLAIN')
        p = provenance(provider='OPERATOR_ASSISTED')
        W.finish(archive, 'ATT-0001', '{}', p)  # invalid output still consumes the attempt
        with self.assertRaisesRegex(S.ScoutError, 'before any imported generation'):
            C.bind(root.path, 'TEST_MODEL', {})
        path = root.path / 'exports/PLAIN-blueprint.json'; data = S.json_loads(path.read_text())
        data['events'][0]['record']['title'] = 'Retrospectively altered'
        path.write_bytes(canonical(data))
        with self.assertRaises(S.ScoutError): C.load(root.path)

    def test_runtime_binding_is_immutable_and_covers_actual_model_and_settings(self):
        root, _, _ = C.load(self.root / 'frozen')
        runtime = C.bind(root.path, 'UNIT_TEST_MODEL', {'temperature': 0.8})
        with self.assertRaises(S.ScoutError): C.bind(root.path, 'OTHER', {})
        archive = Archive(root.path / 'PLAIN')
        p = provenance(provider='OPERATOR_ASSISTED'); p['model'] = 'OTHER_MODEL'
        W.finish(archive, 'ATT-0001', '{}', p)
        audit = C.status(root.path)['fairness']
        self.assertTrue(any('differs from bound runtime' in d for d in audit['deviations']))
        path = root.path / 'exports' / C.RUNTIME
        runtime['model'] = 'OTHER_MODEL'; path.write_bytes(canonical(runtime))
        with self.assertRaisesRegex(S.ScoutError, 'immutable'): C.status(root.path)

    def test_generation_effort_correction_preserves_history_and_uses_latest_record(self):
        root, _, _ = C.load(self.root / 'frozen'); archive = Archive(root.path / 'PLAIN')
        effort = {'attempt_id': 'ATT-0001', 'actor': {'kind': 'HUMAN', 'id': 'UNIT_TEST_DOUBLE'},
            'human_minutes': 'UNKNOWN', 'wall_seconds': 10, 'context_id': 'TEST_FRESH_CONTEXT',
            'invocation_status': 'UNKNOWN',
            'fresh_context': 'YES', 'no_prior_generated_cards': 'YES', 'description': 'UNIT TEST only.'}
        state = archive.append('generation_effort', effort)
        amended = {**effort, 'human_minutes': 2, 'correction_of': digest(state.efforts[-1]),
                   'correction_reason': 'Unit test corrects previously unknown operator effort.'}
        state = archive.append('generation_effort', amended)
        self.assertEqual(len(state.efforts), 2)
        self.assertEqual(generation(state)['attempts'][0]['human_minutes'], 2)
        with self.assertRaises(S.ScoutError): archive.append('generation_effort', effort)

    def test_local_runner_uses_twelve_frozen_stateless_requests_without_redispatch(self):
        from src.research.opportunity_scout.providers import OllamaProvider
        calls = []
        def generate(provider, prompt, seed_value):
            calls.append(prompt['sha256'])
            bodies = [idea(lane=prompt['lane'], variant=i) for i in range(2)]
            if prompt['lane'] == 'RADAR':
                for body in bodies: body['seed_ids'] = list(prompt['context']['seeds'])
            p = provenance(provider='OLLAMA_LOCAL'); p['model'] = provider.model
            p['parameters'] = {'seed': 0, 'temperature': 0.8, 'num_predict': 6000}
            p['invoked_at'] = p['completed_at'] = S.utc_now()
            p['usage'].update({'input_tokens': 1000, 'output_tokens': 2000})
            return canonical({'ideas': bodies}).decode(), p, 'UNIT TEST FAKE TRANSPORT'
        with patch.object(OllamaProvider, 'generate', generate):
            report = C.run_local(self.root / 'frozen', 'UNIT_TEST_LOCAL_MODEL')
            self.assertEqual(len(calls), 12)
            self.assertEqual({x['cards'] for x in report['fairness']['conditions'].values()}, {6})
            self.assertEqual(report['fairness']['deviations'], [])
            self.assertFalse(report['fairness']['comparative_eligible'])  # human effort is still UNKNOWN
            with self.assertRaisesRegex(S.ScoutError, 're-dispatch'):
                C.run_local(self.root / 'frozen', 'UNIT_TEST_LOCAL_MODEL')
            self.assertEqual(len(calls), 12)


if __name__ == '__main__': unittest.main()
