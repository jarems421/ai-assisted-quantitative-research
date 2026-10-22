"""Approval-review artifacts and mocked interface boundaries; no native CLI IO."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from docs.opportunity_scout.hosted_acceptance_v001 import prepare as B
from src.research.spec import canonical
from src.research.opportunity_scout import prompts, schema as S, v004_isolation as I
from src.research.opportunity_scout.v004_r3 import package as P, policy, runtime as R, replay as J, transport as T
from tests.opportunity_scout import v004_fixtures as F


class HostedReadinessProposalTests(unittest.TestCase):
    def test_package_reconstructs_exact_bytes_and_remains_unbound(self):
        self.assertFalse(B.check()['hosted_authorised'])
        manifest = S.json_loads((B.HERE / 'manifest.json').read_text())
        self.assertEqual(manifest['stdin_sha256'], B.sha(canonical(B.request())))
        self.assertEqual(manifest['stdin_bytes'], len(canonical(B.request())))
        self.assertEqual((B.HERE / 'request.json').read_bytes(), canonical(B.request()))
        self.assertEqual(manifest['resource_policy_sha256'], policy.policy_hash())
        self.assertFalse(manifest['collector_implemented'])
        self.assertFalse(manifest['execution_bindings_complete'])
        self.assertEqual(manifest['authorises'], [])
        template = S.json_loads((B.HERE / 'runtime-template.json').read_text())
        self.assertEqual(template['candidate']['resource_policy'], policy.description())
        self.assertEqual(template['candidate']['environment_controls']['CLAUDE_CODE_MAX_OUTPUT_TOKENS'], '32768')
        with self.assertRaises(S.ScoutError): R.validate(template['candidate'])

    def test_one_call_protocol_retains_r3_and_does_not_approve_missing_branches(self):
        proposal = S.json_loads((B.HERE / 'protocol.json').read_text())
        self.assertEqual(proposal['parent_invocations_total_maximum'], 1)
        self.assertEqual(proposal['administrative_preflight_invocations_maximum'], 1)
        self.assertEqual(len(proposal['calls']), 1)
        self.assertEqual(proposal['reserved_scientific_attempts_consumed'], 0)
        self.assertEqual((proposal['combined_planning_reference_tokens'], proposal['elevated_annotation_at_tokens'],
                          proposal['best_effort_emergency_at_tokens']), (60000, 120000, 200000))
        self.assertFalse(proposal['planning_reference_is_ceiling'])
        self.assertFalse(proposal['guaranteed_token_or_financial_limit'])
        self.assertFalse(proposal['hosted_calls_authorised'])
        self.assertFalse(proposal['forced_output_limit_or_interruption'])
        argv = proposal['candidate_argv_review_only']
        self.assertEqual(argv[argv.index('--max-turns') + 1], '2')
        for forbidden in ('--bare', '--json-schema', '--resume', '--continue', '--fallback-model'):
            self.assertNotIn(forbidden, argv)
        self.assertTrue(any('continuation remains unvalidated' in s for s in proposal['inconclusive']))
        self.assertTrue(any('cancellation NOT_OBSERVED' in s for s in proposal['inconclusive']))

    def test_fixture_preserves_complete_schema_projection_and_unverified_source_depth(self):
        request = B.request(); expected = copy.deepcopy(S.GENERATION)
        expected['properties']['ideas'].update(minItems=2, maxItems=2)
        self.assertEqual(request['response_schema'], expected)
        self.assertEqual(set(request), set(B.legacy.PROMPT_FIELDS))
        self.assertIn(prompts.LANE_INSTRUCTIONS['PLAIN'], request['instructions'])
        self.assertNotIn('max_output_tokens', request)
        self.assertEqual(request['count'], 2)
        self.assertEqual(len(request['context']['seeds']), 2)
        for seed in request['context']['seeds'].values():
            self.assertFalse(seed['text_is_prefix'])
            S.validate_seed({k:v for k,v in seed.items() if k != 'text_is_prefix'})
            self.assertEqual(seed['fixture'], 'SYNTHETIC')
            self.assertEqual(seed['depth'], 'INDEXED_DESCRIPTION_ONLY')
            self.assertTrue(seed['text'].startswith('WHOLLY FICTIONAL'))
            self.assertFalse(seed['approved_for_hosted_use'])
            self.assertEqual(seed['clocks']['first_public']['value'], S.UNKNOWN)
        value = F.output(request)
        S.validate(request['response_schema'], value)
        for idea in value['ideas']:
            S.validate_idea(idea, 'PLAIN', request['context']['seeds'], request['context']['memory'])
        idea = copy.deepcopy(value['ideas'][0]); sid = next(iter(request['context']['seeds']))
        idea['seed_ids'] = [sid]; link = idea['mechanism']['links'][0]
        quote = request['context']['seeds'][sid]['text']
        link.update(basis='DOCUMENTED', statement=quote, evidence=[{'seed': sid, 'quote': quote}])
        with self.assertRaisesRegex(S.ScoutError, 'original-depth'):
            S.validate_idea(idea, 'PLAIN', request['context']['seeds'], request['context']['memory'])

    def test_documented_shape_inspired_but_fictional_wrapper_is_not_native_acceptance(self):
        request = {**B.request(), 'schema': P.REQUEST_VERSION, 'resource_policy_sha256': policy.policy_hash(), 'model': F.MODEL}
        events = F.events(request, 'FICTIONAL-N1')
        # Shape inspired by the official example, NOT a captured native event.
        events.insert(1, {'type': 'stream_event', 'session_id': 'FICTIONAL-N1',
                          'event': {'type': 'content_block_delta', 'index': 0,
                                    'delta': {'type': 'text_delta', 'text': '{"ideas":'}}})
        recording = T.Recording(F.encode(events))
        result = T.review(recording, request, 'FICTIONAL-N1')
        self.assertEqual(result['outcome'], 'RUN_STOP')
        self.assertIn('UNRECOGNISED_EVENT', result['integrity_faults'])
        self.assertEqual(result['exact_output'], events[-1]['result'])
        self.assertEqual(result['underlying_provider_requests'], S.UNKNOWN)

    def test_hosted_origin_is_not_made_fictional_by_using_fictional_input(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); package = base / 'package'
            P.build(package, F.blueprints(), R.description(F.MODEL, 'a'*64, 'FICTIONAL-2.1.302'), mode='SYNTHETIC')
            run = J.OfflineRun.create(base / 'run', package); consumed = run.start()
            request = P.load(package)[1][consumed['slot']]
            recording = T.Recording(F.encode(F.events(request, consumed['session_id'])), fictional=False)
            with self.assertRaises(S.ScoutError): T.review(recording, request, consumed['session_id'])
            with self.assertRaises(S.ScoutError): run.finish(recording, F.window(consumed['session_id']))
            status = run.status()
            self.assertEqual(status['consumed_attempts'], 1)
            self.assertEqual(status['actual_usage_outcome']['reported_combined_total'], S.UNKNOWN)
            with self.assertRaises(S.ScoutError): run.finish(recording, F.window(consumed['session_id']))
            with self.assertRaises(S.ScoutError): J.OfflineRun(run.root).start()

    def test_native_monitoring_cannot_be_relabelled_as_a_passed_fictional_window(self):
        window = F.window(); window['config_observation'] = 'OBSERVED_NATIVE'
        result = I.review(window, session_id='FICTIONAL-session')
        self.assertFalse(result['sampled_window_clean'])
        self.assertIn('RESEARCH_CONFIGURATION_NOT_ESTABLISHED', result['faults'])
        self.assertEqual(result['historical_writer'], S.UNKNOWN)

    def test_check_cli_is_read_only_and_preserves_exact_artifacts(self):
        before = {p.name: p.read_bytes() for p in B.HERE.glob('*') if p.is_file()}
        original = Path.open
        def read_only(path, mode='r', *args, **kwargs):
            self.assertFalse(any(flag in mode for flag in 'wax+'), 'validation attempted a file write')
            return original(path, mode, *args, **kwargs)
        output = io.StringIO()
        with patch('sys.argv', ['prepare', '--check']), patch.object(Path, 'open', read_only), contextlib.redirect_stdout(output):
            B.main()
        self.assertFalse(S.json_loads(output.getvalue())['hosted_authorised'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in B.HERE.glob('*') if p.is_file()})

    def test_removed_write_action_is_rejected_before_validation_without_mutation(self):
        before = {p.name: p.read_bytes() for p in B.HERE.glob('*') if p.is_file()}
        for arguments in (['--write'], ['--check', '--write']):
            with self.subTest(arguments=arguments), patch('sys.argv', ['prepare', *arguments]), \
                 patch.object(B, 'check', side_effect=AssertionError('removed action reached validation')), \
                 contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                B.main()
            self.assertEqual(error.exception.code, 2)
        self.assertEqual(before, {p.name: p.read_bytes() for p in B.HERE.glob('*') if p.is_file()})

    def test_fictional_seed_consent_is_explicit_unadopted_and_cannot_flip_schema_flags(self):
        proposal = S.json_loads((B.HERE / 'protocol.json').read_text())
        consent = proposal['fictional_seed_consent']
        self.assertIsNone(consent['registered_owner_consent'])
        self.assertFalse(consent['exception_adopted'])
        self.assertEqual(consent['execution_decision_now'], 'BLOCK')
        self.assertTrue(consent['generic_seed_gate_unchanged'])
        self.assertFalse(proposal['hosted_calls_authorised'])
        self.assertEqual(S.SEED['properties']['approved_for_hosted_use'], {'const': False})
        for seed in B.request()['context']['seeds'].values():
            self.assertFalse(seed['approved_for_hosted_use'])
            changed = {k:v for k,v in seed.items() if k != 'text_is_prefix'}
            changed['approved_for_hosted_use'] = True
            with self.assertRaises(S.ScoutError): S.validate_seed(changed)


if __name__ == '__main__': unittest.main()
