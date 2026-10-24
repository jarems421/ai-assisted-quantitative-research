"""Offline enforcement examples: synthetic classifiers are not independent human labels."""
import ast
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from src.research.spec import canonical, digest
from src.research.jev_navigation_v1 import contracts as K, demo as D, navigation as N, workspace as W
from src.research.jev_navigation_v1.__main__ import main
from src.research.jev_navigation_v1.evaluation import at_budget
from test_discovery_lab import world, candidate


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = D.evidence_input(self.root / 'sources')
        self.workspace = self.root / 'workspace'
        W.prepare(self.input, self.workspace)
        self.bundle = W.load(self.workspace)[1]

    def saved(self, script=None):
        if script is None:
            script = K.loads((D.FIXTURES / 'scripted_choices.json').read_bytes())['evidence']
        value = D.synthetic_response(self.bundle, script)
        path = self.root / 'response.json'
        path.write_bytes(canonical(value))
        return path, value

    def change_input(self, edit):
        data = K.loads(self.input.read_bytes())
        edit(data)
        self.input.write_bytes(canonical(data))

    def test_three_versioned_contracts_are_distinct_and_strict(self):
        for task in K.TASKS:
            schema = K.input_schema(task)
            self.assertFalse(schema['additionalProperties'])
            self.assertEqual(schema['properties']['task'], {'const': task})
        data = K.loads(self.input.read_bytes())
        data['authorises'] = ['ACQUIRE']
        with self.assertRaises(K.NavigationError):
            K.validate(K.input_schema(K.TASKS[0]), data)

    def test_baseline_is_useful_without_any_model_or_saved_response(self):
        result = W.report(self.workspace)
        self.assertEqual(result['model_status'], 'NOT_IMPORTED_DETERMINISTIC_ONLY')
        self.assertEqual([r['id'] for r in result['inspection_queue']], result['baseline_order'])
        self.assertEqual((len(result['inspection_queue']), result['discarded_records'], result['authorises']), (10, [], []))

    def test_multi_label_relevance_preserves_exact_citations_and_unknown_truth(self):
        path, original = self.saved()
        raw = path.read_bytes()
        W.import_response(self.workspace, path)
        result = W.report(self.workspace)
        row = next(r for r in result['inspection_queue'] if r['id'] == 'B_ORDER')
        self.assertEqual(row['model_positive_categories'], ['predictor', 'relationship', 'units'])
        supplied = next(r for r in self.bundle['request']['records'] if r['id'] == 'B_ORDER')
        self.assertEqual(row['citation'], supplied['citation'])
        self.assertIn('measurement validity', result['not_established'])
        self.assertEqual((self.workspace / 'response.raw').read_bytes(), raw)
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(original['response']['model'], 'SYNTHETIC_SCRIPTED_NOT_JEV')

    def test_saved_response_requires_the_exact_question_set(self):
        for mutation in ('missing', 'extra'):
            with self.subTest(mutation=mutation):
                _, value = self.saved()
                answers = value['response']['answers']
                answers.pop(next(iter(answers))) if mutation == 'missing' else answers.update(INVENTED_SOURCE=next(iter(answers.values())))
                with self.assertRaises(K.NavigationError):
                    W.parse_saved(self.bundle, canonical(value))

    def test_unknown_response_fields_and_model_essays_are_refused(self):
        _, value = self.saved()
        value['response']['answers'][next(iter(value['response']['answers']))]['explanation'] = 'I certify M.'
        with self.assertRaises(K.NavigationError):
            W.parse_saved(self.bundle, canonical(value))

    def test_invalid_probability_sum_and_choice_are_refused(self):
        for mutate in (lambda a: a['probabilities'].update(yes=.99), lambda a: a.update(choice='no' if a['choice'] != 'no' else 'yes')):
            _, value = self.saved()
            answer = value['response']['answers'][next(iter(value['response']['answers']))]
            mutate(answer)
            with self.assertRaises(K.NavigationError):
                W.parse_saved(self.bundle, canonical(value))

    def test_boolean_probabilities_float_usage_and_nonfinite_json_are_refused(self):
        _, value = self.saved()
        first = next(iter(value['response']['answers']))
        value['response']['answers'][first]['probabilities']['yes'] = True
        with self.assertRaises(K.NavigationError):
            W.parse_saved(self.bundle, canonical(value))
        _, value = self.saved(); value['response']['usage']['input_tokens'] = 1.0
        with self.assertRaises(K.NavigationError):
            W.parse_saved(self.bundle, canonical(value))
        with self.assertRaises(K.NavigationError):
            K.loads('{"value": NaN}')

    def test_choice_confidence_is_the_documented_statistic_not_accuracy(self):
        _, value = self.saved()
        key = next(iter(value['response']['answers']))
        value['response']['answers'][key]['confidence'] = .99
        with self.assertRaisesRegex(K.NavigationError, 'confidence inconsistent'):
            W.parse_saved(self.bundle, canonical(value))
        self.assertEqual(W.report(self.workspace)['authorises'], [])

    def test_ties_and_explicit_unsure_abstain_without_discarding(self):
        _, value = self.saved()
        key = next(iter(value['response']['answers']))
        value['response']['answers'][key].update(choice='yes', probabilities={'yes': .5, 'no': .5, 'unsure': 0}, confidence=.25)
        a = W.parse_saved(self.bundle, canonical(value))[key]
        self.assertEqual((a['effective_choice'], a['abstention']), ('unsure', 'TIED_MAXIMUM'))
        self.assertEqual(a['raw']['choice'], 'yes')
        result = N.report(self.bundle, W.parse_saved(self.bundle, canonical(value)))
        self.assertEqual(len(result['inspection_queue']), 10)
        self.assertTrue(next(r for r in result['inspection_queue'] if r['id'] == 'H_AMBIGUOUS')['abstentions'])

    def test_all_abstaining_answers_leave_the_baseline_order_intact(self):
        script = {r['id']: {c: 'unsure' for c in K.EVIDENCE} for r in self.bundle['request']['records']}
        path, _ = self.saved(script)
        W.import_response(self.workspace, path)
        result = W.report(self.workspace)
        self.assertEqual([r['id'] for r in result['inspection_queue']], result['baseline_order'])

    def test_real_model_claims_cannot_be_imported_as_synthetic_results(self):
        _, value = self.saved()
        value['response']['model'] = 'jev-1.14.0'
        with self.assertRaises(K.NavigationError):
            W.parse_saved(self.bundle, canonical(value))
        value['fixture'] = 'REAL_JEV_RESPONSE'
        with self.assertRaisesRegex(K.NavigationError, 'only explicitly synthetic'):
            W.parse_saved(self.bundle, canonical(value))

    def test_invalid_bytes_are_kept_and_cannot_be_repaired_or_overwritten(self):
        path = self.root / 'invalid.json'; path.write_bytes(b'{broken response')
        with self.assertRaises(ValueError):
            W.import_response(self.workspace, path)
        self.assertEqual((self.workspace / 'response.raw').read_bytes(), b'{broken response')
        self.assertEqual(K.loads((self.workspace / 'import.json').read_bytes())['status'], 'INVALID')
        path, _ = self.saved()
        with self.assertRaises(FileExistsError):
            W.import_response(self.workspace, path)
        with self.assertRaises(ValueError):
            W.report(self.workspace)

    def test_valid_import_is_single_attempt_and_response_tampering_is_refused(self):
        path, _ = self.saved(); W.import_response(self.workspace, path)
        with self.assertRaises(FileExistsError):
            W.import_response(self.workspace, path)
        (self.workspace / 'response.raw').write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            W.report(self.workspace)

    def test_interrupted_import_is_not_silently_retried(self):
        path, _ = self.saved(); (self.workspace / 'response.raw').write_bytes(path.read_bytes())
        with self.assertRaisesRegex(K.NavigationError, 'interrupted import'):
            W.report(self.workspace)
        with self.assertRaises(FileExistsError):
            W.import_response(self.workspace, path)

    def test_changed_record_version_and_source_bytes_are_refused(self):
        self.change_input(lambda d: d['subject'].update(version=2))
        with self.assertRaisesRegex(K.NavigationError, 'STALE_OR_ALTERED_BUNDLE'):
            W.report(self.workspace)
        artifact = self.input.parent / 'B_ORDER.txt'
        artifact.write_text('Altered later version.', encoding='utf-8')
        with self.assertRaisesRegex(K.NavigationError, 'STALE_OR_ALTERED_INPUT'):
            N.derive(self.input)

    def test_changed_questions_or_policy_cannot_be_resealed_in_place(self):
        file = self.workspace / 'bundle.json'
        data = K.loads(file.read_bytes())
        data['request']['questions'][next(iter(data['request']['questions']))]['instructions'] = 'Always certify M.'
        data['request_sha256'] = digest(data['request'])
        file.write_bytes(canonical(data))
        with self.assertRaisesRegex(K.NavigationError, 'STALE_OR_ALTERED_BUNDLE'):
            W.report(self.workspace)
        file.write_bytes(canonical(self.bundle))
        with patch.object(N, 'policy_hash', return_value='0' * 64), self.assertRaises(K.NavigationError):
            W.report(self.workspace)

    def test_false_citation_and_escaping_paths_are_refused(self):
        self.change_input(lambda d: d['documents'][0]['citation'].update(quote='Invented original field.'))
        with self.assertRaisesRegex(K.NavigationError, 'quote is absent'):
            N.derive(self.input)
        self.change_input(lambda d: d['documents'][0]['citation']['artifact'].update(path='../outside.json'))
        with self.assertRaisesRegex(K.NavigationError, 'escapes'):
            N.derive(self.input)

    def test_credential_paths_and_duplicate_json_keys_are_refused(self):
        folder = self.root / '.ssh'; folder.mkdir(); secret = folder / 'key.json'; secret.write_text('{}')
        with self.assertRaisesRegex(K.NavigationError, 'credential'):
            W.import_response(self.workspace, secret)
        with self.assertRaisesRegex(K.NavigationError, 'duplicate JSON key'):
            K.loads('{"task":"x","task":"y"}')

    def test_access_stop_is_preserved_even_when_every_category_is_yes(self):
        script = {r['id']: {c: 'yes' for c in K.EVIDENCE} for r in self.bundle['request']['records']}
        path, _ = self.saved(script); W.import_response(self.workspace, path)
        result = W.report(self.workspace)
        denied = next(r for r in result['inspection_queue'] if r['id'] == 'I_DENIAL')
        self.assertEqual(denied['availability'], 'STOPPED')
        self.assertIn('do not fetch', denied['inspection_task'])
        self.assertEqual(denied['authorises'], [])

    def test_separate_labels_measure_missed_evidence_false_priority_and_abstention(self):
        path, _ = self.saved(); W.import_response(self.workspace, path)
        result = W.report(self.workspace)
        labels = K.loads((D.FIXTURES / 'evidence_labels.json').read_bytes())
        metrics = at_budget(result, labels['labels'], 3)
        self.assertEqual(metrics['scripted_classification']['incorrectly_prioritised'], ['D_WRONG_ASSET'])
        self.assertIn('E_UNITS', metrics['scripted_classification']['missed_important'])
        self.assertEqual(metrics['scripted_classification']['precision_at_budget'], 2 / 3)
        self.assertEqual(metrics['scripted_classification']['recall_at_budget'], 2 / 5)
        self.assertIn('H_AMBIGUOUS', metrics['abstentions'])
        self.assertIn('not independent human', metrics['interpretation'])
        self.assertNotIn('labels', canonical(self.bundle['request']).decode('utf-8'))
        with self.assertRaises(K.NavigationError):
            at_budget(result, {}, 3)

    def test_cli_prepare_report_schema_and_refusal_have_no_authority(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['report', str(self.workspace)]), 0)
        self.assertEqual(json.loads(output.getvalue())['authorises'], [])
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['schema', K.TASKS[1]]), 0)
        self.assertEqual(json.loads(output.getvalue())['authorises'], [])
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(['prepare', str(self.input), '--out', str(self.workspace)]), 2)
        self.assertEqual(json.loads(error.getvalue())['authorises'], [])


class MemoryNavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = D.memory_input(self.root / 'memory')

    def test_real_sh09_is_surfaced_with_exact_recorded_blockers_and_stop_scope(self):
        bundle = N.derive(self.path)
        script = K.loads((D.FIXTURES / 'scripted_choices.json').read_bytes())['memory']
        result = N.report(bundle, W.parse_saved(bundle, canonical(D.synthetic_response(bundle, script))))
        sh09 = result['inspection_queue'][0]
        self.assertEqual(sh09['id'], 'HIST-SH09')
        cat, issues = N.C.load()
        original = next(i for i in cat['investigations'] if i['id'] == 'HIST-SH09')
        self.assertFalse(issues)
        self.assertEqual(sh09['findings'], original['findings'])
        self.assertEqual(sh09['recorded_verdict'], original['verdict'])
        self.assertEqual(sh09['historical_closure'], original['historical_closure'])
        self.assertEqual(sh09['recorded_documents'], original['documents'])
        self.assertFalse(sh09['economic_relationship_established'])

    def test_shared_requirements_cannot_become_economic_connections(self):
        bundle = N.derive(self.path)
        report = N.report(bundle)
        sh09 = next(r for r in report['inspection_queue'] if r['id'] == 'HIST-SH09')
        self.assertEqual(sh09['connection'], 'SHARED_METHODOLOGICAL_PROBLEM')
        self.assertFalse(sh09['economic_relationship_established'])
        self.assertEqual(report['deterministic']['graph_classifications_changed'], False)

    def test_model_only_similarity_is_explicitly_conceptual_not_a_documented_link(self):
        bundle = N.derive(self.path)
        script = {'HIST-EF03': {'mechanism': 'yes'}}
        report = N.report(bundle, W.parse_saved(bundle, canonical(D.synthetic_response(bundle, script))))
        row = next(r for r in report['inspection_queue'] if r['id'] == 'HIST-EF03')
        self.assertEqual(row['connection'], 'POSSIBLE_CONCEPTUAL_SIMILARITY')
        self.assertFalse(row['economic_relationship_established'])

    def test_exact_existing_document_reference_is_distinct_from_a_causal_connection(self):
        cat, _ = N.C.load()
        inv = next(i for i in cat['investigations'] if i['documents'])
        data = K.loads(self.path.read_bytes()); data['subject']['document_sha256'] = [inv['documents'][0]['sha256']]
        self.path.write_bytes(canonical(data))
        report = N.report(N.derive(self.path))
        row = next(r for r in report['inspection_queue'] if r['id'] == inv['id'])
        self.assertEqual(row['connection'], 'EXACT_DOCUMENTED_REFERENCE')
        self.assertFalse(row['economic_relationship_established'])

    def test_unrelated_memory_is_not_labelled_as_a_strong_link(self):
        report = N.report(N.derive(self.path))
        row = next(r for r in report['inspection_queue'] if r['id'] == 'HIST-EF03')
        self.assertEqual(row['connection'], 'UNSUPPORTED_ASSOCIATION')
        self.assertFalse(row['exact_document_references'] or row['exact_entity_references'])

    def test_changed_catalogue_citation_is_refused_without_touching_history(self):
        cat = K.loads(N.C.CATALOGUE_PATH.read_bytes())
        cat['investigations'][0]['verdict']['citation']['quote'] = 'A fabricated historical conclusion.'
        copied = self.path.parent / 'catalogue.json'; copied.write_bytes(canonical(cat))
        data = K.loads(self.path.read_bytes()); data['catalogue'] = {'base': 'INPUT', 'path': copied.name, 'sha256': N.sha(copied.read_bytes())}
        self.path.write_bytes(canonical(data))
        with self.assertRaisesRegex(K.NavigationError, 'STALE_MEMORY'):
            N.derive(self.path)


class WorkflowNavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def unresolved(self):
        folder = self.root / 'unresolved'; folder.mkdir()
        ledger = world(folder)
        c = candidate()
        c['outcome'].update(status='UNVERIFIED', value='UNKNOWN', evidence=[], derived_from_observations=[])
        ledger.append('candidate', c)
        data = {'schema': K.INPUT, 'task': K.TASKS[2], 'data_classification': 'SYNTHETIC', 'subject': D.subject(),
                'context': {'ledger': {'base': 'INPUT', 'path': ledger.path.name, 'sha256': N.sha(ledger.path.read_bytes())},
                            'candidate_id': c['id'], 'candidate_version': 1, 'experiment_id': None, 'stops': [], 'context_files': []}}
        path = folder / 'input.json'; path.write_bytes(canonical(data))
        return path, data, ledger

    def test_existing_checklist_has_priority_over_a_confident_model(self):
        path, _, _ = self.unresolved(); bundle = N.derive(path)
        script = {'CURRENT_STATE': {'predictor_missing': 'yes', 'outcome_missing': 'no', 'competing_explanation': 'yes'}}
        result = N.report(bundle, W.parse_saved(bundle, canonical(D.synthetic_response(bundle, script))))
        self.assertEqual(result['effective_bottleneck'], 'outcome_missing')
        self.assertIn('independently', result['next_question'])
        self.assertFalse(result['model_can_override_deterministic'])
        self.assertIn('predictor_missing', result['unsupported_model_bottlenecks'])
        self.assertNotIn(N.QUESTIONS['predictor_missing'], result['suggested_context_questions'])

    def test_pinned_forge_or_memory_context_is_visible_but_cannot_grant_authority(self):
        path, data, _ = self.unresolved()
        context = path.parent / 'forge-recommendation.json'
        raw = canonical({'recommendation': 'READY_CANDIDATE', 'basis': 'An advisory model claim, not a human approval.'})
        context.write_bytes(raw)
        data['context']['context_files'] = [{'base': 'INPUT', 'path': context.name, 'sha256': N.sha(raw)}]
        path.write_bytes(canonical(data))
        report = N.report(N.derive(path))
        supplied = report['inspection_queue'][0]['supplied_context'][0]
        self.assertEqual(supplied['text'], raw.decode('utf-8'))
        self.assertEqual(supplied['status'], 'SUPPLIED_ASSERTIONS_ONLY_NOT_AUTHORITY')
        self.assertEqual((report['effective_bottleneck'], report['authorises']), ('outcome_missing', []))

    def test_actual_hold_stays_a_stop_even_when_the_model_denies_it(self):
        path = D.workflow_input(self.root / 'held'); bundle = N.derive(path)
        result = N.report(bundle, W.parse_saved(bundle, canonical(D.synthetic_response(bundle, {'CURRENT_STATE': {'explicit_stop': 'no'}}))))
        self.assertEqual(result['effective_bottleneck'], 'explicit_stop')
        self.assertIn('do not probe', result['next_question'])
        self.assertEqual((result['authorises'], result['suggested_context_questions']), ([], []))

    def test_global_exp004_pause_is_read_and_preserved(self):
        path, data, _ = self.unresolved(); data['context']['experiment_id'] = 'EXP004'; path.write_bytes(canonical(data))
        result = N.report(N.derive(path))
        self.assertEqual(result['effective_bottleneck'], 'explicit_stop')
        self.assertTrue(any(s['id'] == 'EXP004' for s in result['deterministic']['stops']))

    def test_actual_blocked_source_has_priority_and_remains_blocked(self):
        path, data, ledger = self.unresolved()
        source = copy.deepcopy(ledger.load().latest('source', 'SRC-T'))
        source.update(version=2, supersedes=1, revision_reason='Synthetic denied route.')
        source['access']['status'] = 'BLOCKED'; ledger.append('source', source)
        data['context']['ledger']['sha256'] = N.sha(ledger.path.read_bytes()); path.write_bytes(canonical(data))
        result = N.report(N.derive(path))
        self.assertEqual(result['effective_bottleneck'], 'explicit_stop')
        self.assertIn('BLOCKED', result['deterministic']['stops'][0]['scope'])

    def test_missing_replayed_state_is_insufficient_not_invented_from_model(self):
        path, data, _ = self.unresolved()
        data['context'].update(ledger=None, candidate_id=None, candidate_version=None); path.write_bytes(canonical(data))
        bundle = N.derive(path)
        report = N.report(bundle, W.parse_saved(bundle, canonical(D.synthetic_response(bundle, {'CURRENT_STATE': {'human_judgment_missing': 'yes'}}))))
        self.assertEqual(report['effective_bottleneck'], 'insufficient_information')
        self.assertIn('human_judgment_missing', report['unsupported_model_bottlenecks'])

    def test_superseded_candidate_version_is_refused(self):
        path, data, ledger = self.unresolved()
        c = copy.deepcopy(ledger.load().latest('candidate', 'CAND-T-1'))
        c.update(version=2, supersedes=1, revision_reason='Synthetic clarification.')
        ledger.append('candidate', c)
        data['context']['ledger']['sha256'] = N.sha(ledger.path.read_bytes()); path.write_bytes(canonical(data))
        with self.assertRaisesRegex(K.NavigationError, 'STALE_CANDIDATE_VERSION'):
            N.derive(path)

    def test_changed_ledger_head_after_prepare_is_refused(self):
        path, _, ledger = self.unresolved(); target = self.root / 'bundle'; W.prepare(path, target)
        ledger.freeze('CAND-T-1')
        with self.assertRaisesRegex(K.NavigationError, 'STALE_OR_ALTERED_INPUT'):
            W.report(target)

    def test_v001_history_keeps_v002_blockers_despite_contrary_classifications(self):
        cases = (
            ('gross_net_only_evidenced_review.jsonl', 'financial_bridge', 'GROSS_EXPOSURE_UNVERIFIED', 'exposure_unverified'),
            ('source_revised_not_evidenced_review.jsonl', 'distinctive_predictor', 'SOURCE_REVISED_AFTER_FREEZE', 'predictor_missing'),
        )
        for name, requirement, blocker, effective in cases:
            with self.subTest(name=name):
                folder = self.root / name.removesuffix('.jsonl'); folder.mkdir()
                source = N.ROOT / 'tests/fixtures/discovery_v001' / name
                raw = source.read_bytes()
                ledger_path = folder / name; ledger_path.write_bytes(raw)
                state = N.Ledger(ledger_path).load()
                self.assertEqual(state.rules, 'DISCOVERY_LAB_RULES_V001')
                c = state.latest('candidate', 'CAND-T-1')
                data = {'schema': K.INPUT, 'task': K.TASKS[2], 'data_classification': 'SYNTHETIC', 'subject': D.subject(),
                        'context': {'ledger': {'base': 'INPUT', 'path': name, 'sha256': N.sha(raw)},
                                    'candidate_id': c['id'], 'candidate_version': c['version'], 'experiment_id': None,
                                    'stops': [], 'context_files': []}}
                path = folder / 'input.json'; path.write_bytes(canonical(data))
                bundle = N.derive(path)
                script = {'CURRENT_STATE': {effective: 'no', 'human_judgment_missing': 'yes'}}
                result = N.report(bundle, W.parse_saved(bundle, canonical(D.synthetic_response(bundle, script))))
                blockers = result['deterministic']['checklist']['requirements'][requirement]['blockers']
                self.assertTrue(any(blocker in value for value in blockers))
                self.assertEqual(result['effective_bottleneck'], effective)
                self.assertEqual(result['authorises'], [])
                self.assertEqual(ledger_path.read_bytes(), raw)
                self.assertEqual(source.read_bytes(), raw)


class RetirementAndBoundaryTests(unittest.TestCase):
    def test_nonfrozen_legacy_api_rejects_real_batches_before_reading_a_response(self):
        from src.research.opportunity_scout.post_generation import review
        from src.research.opportunity_scout.schema import ScoutError
        archive = Mock(); archive.load.return_value.batch = {'fixture': 'EXPLORATORY'}
        with self.assertRaisesRegex(ScoutError, 'LEGACY_RETIRED'):
            review.import_response(archive, 'IDEA-X', 1, '0' * 64, 'does-not-exist.json', 'not a review', transport='SYNTHETIC_FIXTURE')
        archive.append.assert_not_called()

    def test_prospective_shadow_entry_points_are_disabled_before_loading_any_archive(self):
        from src.research.opportunity_scout.post_generation.cli import main as old_main
        from src.research.opportunity_scout.critic_v1.cli import main as critic_main
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(old_main(['import-response', 'missing', 'IDEA-X', 'missing.json', '--version', '1', '--request-sha256', '0' * 64, '--by', 'not an approval']), 2)
        self.assertIn('LEGACY_RETIRED', error.getvalue())
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(critic_main(['jev-compare', 'missing', '--store', 'X=missing']), 2)
        self.assertIn('LEGACY_RETIRED', error.getvalue())

    def test_no_navigation_transport_credentials_legacy_critic_or_mutation_of_research(self):
        forbidden = ('socket', 'urllib', 'requests', 'http', 'subprocess', 'typesafe_sdk', 'nexustrade')
        for path in (N.ROOT / 'src/research/jev_navigation_v1').glob('*.py'):
            source = path.read_text(encoding='utf-8'); tree = ast.parse(source)
            names = [n.name for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names]
            names += [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            self.assertFalse([n for n in names if n.split('.')[0] in forbidden or 'opportunity_scout' in n], path.name)
            self.assertNotIn('os.environ', source)
            self.assertNotIn('getenv(', source)
            self.assertNotIn(".append('review'", source)

    def test_minimal_demo_runs_all_three_types_without_approvals_or_activation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = D.run(Path(tmp) / 'demo')
        self.assertEqual(result['memory_order'][0], 'HIST-SH09')
        self.assertEqual(result['workflow']['effective_bottleneck'], 'explicit_stop')
        self.assertEqual((result['provider_activated'], result['authorises']), (False, []))


if __name__ == '__main__':
    unittest.main()
