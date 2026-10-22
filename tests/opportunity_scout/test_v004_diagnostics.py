"""Fictional regression evidence for prospective V004; no live calls."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.research.spec import canonical
from src.research.opportunity_scout import schema as S, v004_diagnostics as D
from src.research.opportunity_scout.fixtures import idea
from src.research.opportunity_scout.claude_subscription import ClaudeSubscription


def stream(*, structured=True, messages=1, subtype='success', tool_error=False,
           input_parts=(2, 1000, 100), output_tokens=3000, continuation=False):
    output = {'ideas': [idea(variant=i) for i in range(2)]}
    events = [{'type': 'system', 'subtype': 'init', 'model': 'claude-opus-5-5',
        'session_id': 'SYNTHETIC-401-UUID', 'plugins': [{'name': 'plugin-authoring'}],
        'tools': ['StructuredOutput'] if structured else [], 'skills': [], 'mcp_servers': [],
        'apiKeySource': 'none', 'permissionMode': 'dontAsk'}]
    for i in range(messages):
        message = {'id': 'msg_FICTIONAL_' + str(i), 'model': 'claude-opus-5-5', 'content': []}
        events.append({'type': 'assistant', 'request_id': 'req_FICTIONAL_' + str(i), 'message': message})
    if continuation:
        events.insert(2, {'type': 'user', 'isSynthetic': True, 'message': {'content': [
            {'type': 'text', 'text': 'FICTIONAL output token limit notification'}]}})
    events[-1]['message']['content'] = ([{'type': 'tool_use', 'name': 'StructuredOutput', 'input': output}]
        if structured else [{'type': 'text', 'text': canonical(output).decode()}])
    if tool_error:
        events[-1]['message']['content'][0]['input'] = {'ideas': 'FICTIONAL malformed array string'}
        events.append({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'is_error': True,
                         'content': 'FICTIONAL output schema failed'}]}})
    terminal = {'type': 'result', 'subtype': subtype, 'is_error': subtype != 'success',
        'num_turns': 2 if structured else 1, 'api_error_status': None,
        'usage': {'input_tokens': input_parts[0], 'cache_creation_input_tokens': input_parts[1],
            'cache_read_input_tokens': input_parts[2], 'output_tokens': output_tokens,
            'output_tokens_details': {'thinking_tokens': 100}},
        'modelUsage': {'claude-opus-5-5': {'maxOutputTokens': 128000}}, 'permission_denials': [],
        'subagent_stats': {'spawned': 0}}
    if subtype == 'success':
        terminal['result'] = canonical(output).decode()
        if structured: terminal['structured_output'] = output
    events.append(terminal)
    return events


class DiagnosticsTests(unittest.TestCase):
    def setUp(self): self.schema = D.fictional_input()[1]

    def analyse(self, events, **kwargs):
        return D.analyse('\n'.join(json.dumps(e) for e in events), kwargs.pop('returncode', 0), self.schema, **kwargs)

    def test_structured_terminal_max_turns_wins_over_auth_substrings(self):
        events = stream(subtype='error_max_turns')
        result = self.analyse(events, returncode=1)
        self.assertEqual(result['termination'], 'CLI_MAX_TURNS')
        self.assertNotIn('AUTHENTICATION', json.dumps(result))

    def test_uuids_plugin_names_and_generated_auth_text_never_imply_auth_failure(self):
        events = stream(); events[-1]['errors'] = ['An author compared login queues; value 401 is data.']
        self.assertEqual(self.analyse(events)['termination'], 'SUCCESS')

    def test_designated_auth_status_and_error_type_are_recognised(self):
        for error in ({'type': 'authentication_error'}, {'status': 401}):
            events = stream(subtype='error_during_execution'); events.insert(1, {'type': 'error', 'error': error})
            self.assertEqual(self.analyse(events, returncode=1)['termination'], 'AUTHENTICATION_FAILED')
        events = stream(subtype='error_during_execution'); events[-1]['api_error_status'] = 401
        self.assertEqual(self.analyse(events, returncode=1)['termination'], 'AUTHENTICATION_FAILED')

    def test_designated_rate_limit_and_stderr_fallback_are_narrow(self):
        events = stream(subtype='error_during_execution'); events[-1]['api_error_status'] = 429
        self.assertEqual(self.analyse(events, returncode=1)['termination'], 'RATE_LIMIT')
        self.assertEqual(D.termination([], 1, 'Authentication failed'), 'AUTHENTICATION_FAILED')
        self.assertEqual(D.termination([], 1, 'authoring plugin UUID 401'), 'CLI_FAILED')

    def test_thinking_and_formatting_chunks_share_one_message_but_not_a_second_generation(self):
        events = stream(); thinking = copy.deepcopy(events[1]); thinking['message']['content'] = [{'type': 'thinking'}]
        events.insert(1, thinking)
        result = self.analyse(events)
        self.assertEqual(result['assistant_stream_events'], 2)
        self.assertEqual(result['distinct_visible_assistant_messages'], 1)
        self.assertEqual(result['reported_agentic_turns'], 2)
        self.assertTrue(result['candidate_one_generation_pass'])
        thinking['message']['id'] = 'msg_FICTIONAL_SECOND_GENERATION'
        self.assertFalse(self.analyse(events)['candidate_one_generation_pass'])

    def test_output_limit_retry_is_distinct_from_formatting_and_network_retries(self):
        result = self.analyse(stream(messages=2, continuation=True))
        self.assertEqual(result['distinct_visible_request_ids'], 2)
        self.assertEqual(result['synthetic_output_limit_notifications'], 1)
        self.assertEqual(result['underlying_provider_requests'], S.UNKNOWN)
        self.assertIn('ONE_VISIBLE_GENERATION_NOT_ESTABLISHED', result['deviations'])

    def test_cached_usage_is_counted_once_from_terminal_not_repeated_chunks(self):
        events = stream(input_parts=(4, 33158, 3924), output_tokens=10742)
        result = self.analyse(events)
        self.assertEqual(result['usage']['input_total'], 37086)
        self.assertEqual(result['usage']['input_excess'], 7086)
        self.assertEqual(result['usage']['output_excess'], 4742)
        self.assertEqual(result['usage']['output_total'], 10742)  # Thinking is not added twice.
        self.assertIn('INPUT_TOKEN_CEILING_EXCEEDED', result['deviations'])
        self.assertIn('OUTPUT_TOKEN_CEILING_EXCEEDED', result['deviations'])

    def test_missing_usage_precludes_a_pass_and_model_cap_is_not_actual_request_cap(self):
        events = stream(); events[-1]['usage'].pop('cache_read_input_tokens')
        result = self.analyse(events)
        self.assertEqual(result['usage']['input_total'], S.UNKNOWN)
        self.assertFalse(result['candidate_one_generation_pass'])
        self.assertEqual(self.analyse(stream())['usage']['output_cap'], 6000)

    def test_type_mismatch_is_exposed_without_private_error_messages_or_repair(self):
        result = self.analyse(stream(tool_error=True, subtype='error_max_turns'), returncode=1)
        self.assertEqual(result['formatting_schema_errors'], [{'validator': 'type', 'path': ['ideas']}])
        self.assertEqual(result['failed_tool_results'], 1)
        self.assertNotIn('malformed array string', json.dumps(result))
        self.assertFalse(result['terminal_schema_valid'])

    def test_environment_is_separate_from_generation_independence(self):
        result = self.analyse(stream(messages=2))
        self.assertTrue(result['environment_isolation_verified'])
        self.assertFalse(result['single_visible_generation_verified'])
        events = stream(); events[0]['tools'].append('Read')
        self.assertFalse(self.analyse(events)['environment_isolation_verified'])

    def test_raw_one_generation_needs_zero_tools_and_locally_valid_unrepaired_json(self):
        result = self.analyse(stream(structured=False), structured=False)
        self.assertTrue(result['candidate_one_generation_pass'])
        events = stream(structured=False); events[-1]['result'] = '```json\n{}\n```'
        self.assertFalse(self.analyse(events, structured=False)['candidate_one_generation_pass'])
        self.assertFalse(self.analyse(stream(), structured=False)['candidate_one_generation_pass'])

    def test_terminal_text_cannot_silently_replace_original_output(self):
        events = stream(structured=False); events[1]['message']['content'][0]['text'] = 'FICTIONAL ORIGINAL BROKEN OUTPUT'
        result = self.analyse(events, structured=False)
        self.assertIn('TERMINAL_OUTPUT_DIFFERS_FROM_ORIGINAL_TEXT', result['deviations'])
        self.assertFalse(result['candidate_one_generation_pass'])

    def test_reprompt_or_second_request_id_cannot_hide_behind_one_message_id(self):
        events = stream(); events.insert(1, {'type': 'user', 'isSynthetic': True,
            'message': {'content': [{'type': 'text', 'text': 'FICTIONAL schema reprompt'}]}})
        self.assertFalse(self.analyse(events)['candidate_one_generation_pass'])
        events = stream(); chunk = copy.deepcopy(events[1]); chunk['request_id'] = 'req_FICTIONAL_SECOND'
        chunk['message']['content'] = []; events.insert(1, chunk)
        self.assertFalse(self.analyse(events)['candidate_one_generation_pass'])

    def test_multiple_formatting_calls_are_not_relabelled_as_one_generation(self):
        events = stream(); events[1]['message']['content'] *= 2
        result = self.analyse(events)
        self.assertIn('ADDITIONAL_FORMATTING_OR_TOOL_CALL', result['deviations'])
        self.assertFalse(result['candidate_one_generation_pass'])

    def test_model_mismatch_fails_even_with_valid_output(self):
        result = self.analyse(stream(), expected_model='claude-opus-999')
        self.assertIn('MODEL_MISMATCH', result['deviations'])

    def test_full_schema_two_cards_and_realistic_fictional_load_are_fixed(self):
        text, schema = D.fictional_input()
        self.assertGreater(len(text.encode()), 25000)
        self.assertEqual(schema['properties']['ideas']['minItems'], 2)
        self.assertEqual(schema['properties']['ideas']['maxItems'], 2)
        self.assertEqual(schema['properties']['ideas']['items'], S.IDEA)
        self.assertNotIn('EF06', text); self.assertNotIn('HIST-F01', text)
        self.assertEqual(text, D.fictional_input()[0])

    def test_diagnostic_two_turn_probe_does_not_change_one_generation_eligibility(self):
        self.assertEqual(D.PROBES[1], ('STRUCTURED_TWO_TURNS_DIAGNOSTIC', True, 2))
        self.assertFalse(self.analyse(stream(messages=2))['candidate_one_generation_pass'])

    def test_fixed_probe_runner_no_arbitrary_prompt_fallback_or_retry(self):
        with tempfile.TemporaryDirectory() as td:
            client = Mock(); client.inspect.return_value = {'cli_version': 'FICTIONAL'}; client.env = {}
            client.arguments.side_effect = lambda model, schema, cid: ['fake.exe', '--session-id', cid, '--json-schema', json.dumps(schema)]
            runner = Mock(side_effect=[subprocess.CompletedProcess([], 1, '\n'.join(json.dumps(e) for e in stream(subtype='error_max_turns')), ''),
                subprocess.CompletedProcess([], 0, '\n'.join(json.dumps(e) for e in stream()), ''),
                subprocess.CompletedProcess([], 0, '\n'.join(json.dumps(e) for e in stream(structured=False)), '')])
            with patch.object(D, 'development_account_metadata', return_value={'fixture': 'UNCHANGED'}):
                result = D.synthetic_probe(Path(td) / 'probe', client=client, runner=runner)
            self.assertEqual(runner.call_count, 3)
            self.assertEqual({c.kwargs['input'] for c in runner.call_args_list}, {D.fictional_input()[0]})
            self.assertEqual([c.kwargs['env']['CLAUDE_CODE_MAX_TURNS'] for c in runner.call_args_list], ['1', '2', '1'])
            self.assertNotIn('--json-schema', runner.call_args_list[-1].args[0])
            with self.assertRaises(S.ScoutError): D.synthetic_probe(Path(td) / 'probe', client=client, runner=runner)
            self.assertEqual(runner.call_count, 3)
            self.assertFalse(result['real_generation_authorised'])
            # Preserve a failing end-of-window guard during offline replay;
            # replay does not dispatch, replace receipts or upgrade readiness.
            root = Path(td) / 'probe/exports'
            summary_path = root / 'fictional-probe-summary-v004.json'
            original = S.json_loads(summary_path.read_text(encoding='utf-8'))
            original['development_account_metadata_unchanged'] = False
            summary_path.write_bytes(canonical(original) + b'\n')
            bytes_before = {p.name: p.read_bytes() for p in root.iterdir()}
            replay = D.replay_fictional(Path(td) / 'probe')
            self.assertFalse(replay['validation_complete']); self.assertEqual(replay['new_cli_invocations'], 0)
            self.assertEqual(bytes_before, {p.name: p.read_bytes() for p in root.iterdir()})
            self.assertEqual(runner.call_count, 3)

    def test_timeout_and_auth_failure_stop_remaining_probe_slots_without_retry(self):
        for response in (subprocess.TimeoutExpired(['fake'], 150),
                         subprocess.CompletedProcess([], 1, '', 'Not logged in')):
            with self.subTest(response=type(response).__name__), tempfile.TemporaryDirectory() as td:
                client = Mock(); client.inspect.return_value = {}; client.env = {}
                client.arguments.return_value = ['fake.exe', '--json-schema', '{}']
                runner = Mock(side_effect=response) if isinstance(response, Exception) else Mock(return_value=response)
                result = D.synthetic_probe(Path(td) / 'probe', client=client, runner=runner)
                runner.assert_called_once(); self.assertEqual(len(result['probes']), 1)

    def test_development_metadata_change_stops_probes_and_records_unresolved_guard(self):
        with tempfile.TemporaryDirectory() as td:
            client = Mock(); client.inspect.return_value = {}; client.env = {}
            client.arguments.return_value = ['fake.exe', '--json-schema', '{}']
            runner = Mock(return_value=subprocess.CompletedProcess([], 0,
                '\n'.join(json.dumps(e) for e in stream()), ''))
            with patch.object(D, 'development_account_metadata', side_effect=[{'file': 'BEFORE'}, {'file': 'AFTER'}]):
                result = D.synthetic_probe(Path(td) / 'probe', client=client, runner=runner)
            runner.assert_called_once()
            self.assertFalse(result['development_account_metadata_unchanged'])


if __name__ == '__main__': unittest.main()
