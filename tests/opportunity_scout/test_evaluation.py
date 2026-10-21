from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from src.research.spec import canonical, digest
from src.research.opportunity_scout import evaluation as V, schema as S, workflow as W
from src.research.opportunity_scout.cli import main, learning
from src.research.opportunity_scout.fixtures import MOMENT, STORIES, idea, seed, provenance
from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout.providers import shadow_request, QUESTIONS


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.states = {}
        families = list(STORIES)
        for condition in V.CONDITIONS:
            archive = Archive(Path(cls.temp.name) / condition)
            W.initialise(archive, 'SYNTHETIC frozen condition', fixture='SYNTHETIC', with_memory=True,
                         max_cards=6, max_attempts=3, moment=MOMENT)
            archive.append('seed', seed(), recorded_at=MOMENT)
            lanes = {'PLAIN': ['PLAIN'] * 3, 'EVIDENCE_ONLY': ['RADAR'] * 3,
                     'MECHANISM_ONLY': ['FORGE'] * 3, 'HYBRID': ['FORGE', 'RADAR', 'GAP']}[condition]
            for index, lane in enumerate(lanes):
                aid, _ = W.prepare(archive, lane, 2, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
                W.finish(archive, aid, canonical({'ideas': [idea(families[index * 2 + j], lane) for j in range(2)]}).decode(),
                         provenance(), moment=MOMENT)
            cls.states[condition] = archive.load()
        cls.packet, cls.key = V.blind(cls.states, 'SYNTHETIC_PRIVATE_TEST_SALT_12345')

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_four_conditions_have_equal_limits_and_common_inputs(self):
        self.assertEqual(len(self.packet['cards']), 24)
        self.assertEqual({len(s.cards) for s in self.states.values()}, {6})
        self.assertEqual({len(s.attempts) for s in self.states.values()}, {3})
        self.assertEqual({s.batch['max_output_tokens'] for s in self.states.values()}, {6000})

    def test_generator_metadata_is_hidden_with_partial_blinding_declared(self):
        for row in self.packet['cards']:
            self.assertEqual(set(row), {'blind_id', 'idea', 'source_passages'})
            self.assertNotIn('provenance', row)
            self.assertNotIn('lane', row)
            self.assertNotIn('id', row['idea'])
        self.assertEqual(self.packet['blinding'], 'PARTIAL_PROCEDURAL')

    def test_missing_reviewers_are_reported_without_fake_labels(self):
        result = V.evaluate_blind(self.packet, self.key, [])
        self.assertEqual(result['reviewed'], 0)
        self.assertEqual(len(result['missing']), 24)
        self.assertFalse(result['complete'])
        self.assertFalse(result['human_labels_invented'])

    def test_wrong_seal_or_changed_card_content_is_refused(self):
        key = copy.deepcopy(self.key); next(iter(key['assignments'].values()))['condition'] = 'OTHER'
        with self.assertRaises(S.ScoutError): V.evaluate_blind(self.packet, key, [])
        packet = copy.deepcopy(self.packet); packet['cards'][0]['idea']['title'] = 'Rewritten after seeing results'
        with self.assertRaises(S.ScoutError): V.evaluate_blind(packet, self.key, [])

    def test_incomplete_or_unequal_budget_comparison_cannot_be_scored(self):
        states = copy.deepcopy(self.states); states['PLAIN'].batch['max_attempts'] = 4
        with self.assertRaises(S.ScoutError): V.blind(states, 'SYNTHETIC_PRIVATE_TEST_SALT_12345')
        states = copy.deepcopy(self.states); states['PLAIN'].cards.pop(next(iter(states['PLAIN'].cards)))
        with self.assertRaises(S.ScoutError): V.blind(states, 'SYNTHETIC_PRIVATE_TEST_SALT_12345')

    def test_shadow_metrics_stay_unknown_without_independent_labels(self):
        metrics = V.shadow_metrics(self.states, self.key, [])
        for q in metrics['questions'].values():
            self.assertIsNone(q['agreement']); self.assertIsNone(q['binary_yes_brier'])
        self.assertFalse(metrics['calibration_established'])

    def test_shadow_agreement_uses_actual_distributions_not_confidence_as_truth(self):
        states = copy.deepcopy(self.states)
        bid, mapped = next(iter(self.key['assignments'].items()))
        s = states[mapped['condition']]
        s.shadows.append({'idea_id': mapped['idea_id'], 'version': 1, 'response': {'answers': {
            q: {'choice': 'yes', 'probabilities': {'yes': .8, 'no': .1, 'unsure': .1}, 'confidence': .95} for q in QUESTIONS}}})
        judgments = [{'blind_id': bid, 'atomic_answers': {q: 'yes' for q in QUESTIONS}}]
        result = V.shadow_metrics(states, self.key, judgments)
        self.assertAlmostEqual(result['questions']['falsifiable']['binary_yes_brier'], .04)
        self.assertEqual(result['questions']['falsifiable']['agreement'], 1)
        self.assertFalse(result['calibration_established'])

    def test_synthetic_reviews_cannot_be_passed_off_as_actual_human_labels(self):
        review = {'blind_id': self.packet['cards'][0]['blind_id'], 'reviewer': {'kind': 'HUMAN', 'id': 'NOT_REAL'},
            'coherent': 'YES', 'falsifiable': 'YES', 'research_worthy': 'YES', 'evidence_integrity': 'UNKNOWN',
            'minutes': 'UNKNOWN', 'notes': 'This is a software control, not actual human review.',
            'atomic_answers': {q: 'unsure' for q in QUESTIONS}}
        with self.assertRaises(S.ScoutError): V.evaluate_blind(self.packet, self.key, [review])

    def test_future_learning_retains_uninvestigated_and_missing_selection(self):
        data = learning(self.states['HYBRID'])
        self.assertEqual(len(data['records']), 6)
        self.assertTrue(all(r['investigation_status'] == 'NOT_INVESTIGATED' for r in data['records']))
        self.assertTrue(all(not r['uninvestigated_is_failure'] for r in data['records']))
        self.assertFalse(data['training_performed'])


class CLITests(unittest.TestCase):
    def test_import_status_reports_the_completed_attempt_with_later_attempts_pending(self):
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / 'status')
            def run(args):
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err): result = main(args)
                self.assertEqual(result, 0, err.getvalue())
                return json.loads(out.getvalue())
            run(['init', store, '--title', 'SYNTHETIC pending attempts', '--synthetic', '--no-memory'])
            first = run(['prepare', store, '--lane', 'FORGE', '--count', '1', '--model', 'SYNTHETIC_GENERATOR'])
            second = run(['prepare', store, '--lane', 'FORGE', '--count', '1', '--model', 'SYNTHETIC_GENERATOR'])
            response = Path(td) / 'response.json'
            response.write_bytes(canonical({'attempt_id': first['attempt_id'], 'provenance': provenance(provider='OPERATOR_ASSISTED'),
                                           'output': {'ideas': [idea()]}}))
            result = run(['import-response', store, str(response)])
            self.assertEqual(result['attempt_statuses'][first['attempt_id']], 'VALID')
            self.assertEqual(result['attempt_statuses'][second['attempt_id']], 'PENDING')

    def test_complete_operator_assisted_workflow_uses_real_importer(self):
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / 'operator')
            def run(args):
                out = io.StringIO(); err = io.StringIO()
                with redirect_stdout(out), redirect_stderr(err): result = main(args)
                self.assertEqual(result, 0, err.getvalue())
                return json.loads(out.getvalue())
            run(['init', store, '--title', 'SYNTHETIC operator workflow', '--synthetic', '--no-memory'])
            request = run(['prepare', store, '--lane', 'FORGE', '--count', '1', '--model', 'SYNTHETIC_GENERATOR'])
            p = provenance(provider='OPERATOR_ASSISTED')
            response = Path(td) / 'response.json'
            response.write_bytes(canonical({'attempt_id': request['attempt_id'], 'provenance': p, 'output': {'ideas': [idea()]}}))
            run(['run', store, '--responses', str(response)])
            cards = run(['list', store])['results']
            self.assertEqual(cards[0]['route'], 'INCUBATE')
            run(['card', store, cards[0]['id']]); run(['shortlist', store]); run(['incubator', store]); run(['report', store]); run(['validate', store])
            self.assertEqual(run(['learning-export', store])['records'][0]['investigation_status'], 'NOT_INVESTIGATED')
            self.assertEqual(run(['shadow-request', store, cards[0]['id']])['authorises'], [])
            self.assertEqual(run(['critic-request', store, cards[0]['id']])['authorises'], [])

    def test_invalid_input_returns_nonzero_without_authority_writes(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(['init', str(Path(__file__).resolve().parents[2] / 'docs'), '--title', 'forbidden']), 2)


if __name__ == '__main__': unittest.main()
