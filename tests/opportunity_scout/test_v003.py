"""Fictional-only mocked CLI regression tests. Never contacts Anthropic."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import claude_subscription as C, v003 as V3
from src.research.opportunity_scout import schema as S, evaluation as V, workflow as W
from src.research.opportunity_scout.fixtures import MOMENT, seed, idea
from src.research.opportunity_scout.providers import QUESTIONS
from src.research.opportunity_scout.storage import Archive, input_json

MODEL = 'claude-opus-99-1'


def envelope(output=None, model=MODEL, usage=True):
    output = {'extra_deposit_units': 12} if output is None else output
    init = {'type': 'system', 'subtype': 'init', 'model': model, 'tools': ['StructuredOutput'],
            'skills': [], 'mcp_servers': [], 'permissionMode': 'dontAsk', 'apiKeySource': 'none'}
    result = {'type': 'result', 'subtype': 'success', 'is_error': False,
              'result': json.dumps(output), 'structured_output': output,
              'modelUsage': {model: {'inputTokens': 10}}, 'permission_denials': [],
              'subagent_stats': {'spawned': 0}, 'total_cost_usd': 99.5}
    if usage:
        result['usage'] = {'input_tokens': 10, 'cache_read_input_tokens': 20,
                           'cache_creation_input_tokens': 30, 'output_tokens': 70,
                           'output_tokens_details': {'thinking_tokens': 5}}
    assistant = {'type': 'assistant', 'message': {'id': 'msg_FICTIONAL_001', 'model': model, 'content': [
        {'type': 'tool_use', 'name': 'StructuredOutput', 'input': output}]}}
    return '\n'.join(json.dumps(e) for e in (init, assistant, result)) + '\n'


def fictional_package(path):
    """V002-shaped package containing zero real seed, catalogue or report data."""
    path.mkdir()
    files = {}
    memory = W.empty_memory(MOMENT)
    memory['investigations'] = {'HIST-SYNTHETIC': {'id': 'HIST-SYNTHETIC',
        'title': 'Fictional Aster depot inspection', 'requirements': ['REQ_AVAILABLE_CAPACITY'],
        'findings': [], 'verdict': 'FICTIONAL_NOT_CHECKED', 'closed_source_routes': []}}
    with tempfile.TemporaryDirectory() as td:
        for condition in V.CONDITIONS:
            archive = Archive(Path(td) / condition)
            # Initialise without ever reading the repository's real memory catalogue.
            W.initialise(archive, 'SYNTHETIC ' + condition, fixture='SYNTHETIC', with_memory=False,
                         max_cards=6, max_attempts=3, moment=MOMENT)
            batch = copy.deepcopy(archive.load().batch); batch['memory'] = memory
            replacement = Archive(Path(td) / (condition + '-with-fictional-memory'))
            replacement.append('batch', batch, recorded_at=MOMENT)
            replacement.append('seed', seed(), recorded_at=MOMENT)
            for lane in V.protocol('V003')['allocation'][condition]:
                W.prepare(replacement, lane, 2, 'MODEL_BOUND_BEFORE_GENERATION', moment=MOMENT)
            data = {'events': [{k: e[k] for k in ('type', 'record', 'recorded_at')}
                               for e in replacement.load().events]}
            name = condition + '-blueprint.json'; (path / name).write_bytes(canonical(data) + b'\n')
            files[name] = digest(data)
    manifest = {'schema': 'SCOUT_COMPARISON_PACKAGE_V002', 'protocol_sha256': digest(V.protocol('V002')),
                'generation_status': 'NOT_RUN', 'hosted_transmission_authorised': False, 'files': files}
    (path / 'comparison-manifest.json').write_bytes(canonical(manifest) + b'\n')


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.config = self.base / '.claude-research'; self.config.mkdir()
        (self.config / '.credentials.json').write_text('DO NOT READ RESEARCH SECRET', encoding='utf-8')
        self.exe = self.base / 'claude.exe'; self.exe.write_text('fake executable', encoding='utf-8')
        self.config_patch = patch.object(C, 'RESEARCH_CONFIG', self.config); self.config_patch.start()
        self.addCleanup(self.config_patch.stop)
        self.runner = Mock(return_value=subprocess.CompletedProcess([], 0, envelope(), ''))
        self.client = C.ClaudeSubscription(self.exe, self.config, runner=self.runner)

    def permit(self, model=MODEL):
        return {'purpose': 'FIXED_SYNTHETIC_PREFLIGHT', 'model': model,
                'payload_sha256': S.hash_text(C.SYNTHETIC_TEXT), 'schema_sha256': digest(C.SYNTHETIC_SCHEMA)}

    def invoke(self, **kwargs):
        return self.client.invoke(C.SYNTHETIC_TEXT, C.SYNTHETIC_SCHEMA, MODEL, permit=self.permit(), **kwargs)

    def test_account_env_is_child_only_and_drops_all_credential_provider_and_ide_overrides(self):
        supplied = {'ANTHROPIC_API_KEY': 'private', 'CLAUDE_CODE_OAUTH_TOKEN': 'private',
                    'CLAUDE_CONFIG_DIR': 'development', 'CLAUDE_CODE_EFFORT_LEVEL': 'max',
                    'ANTHROPIC_BASE_URL': 'https://other.invalid', 'CLAUDE_CODE_USE_BEDROCK': '1',
                    'VSCODE_IPC_HOOK': 'private', 'AWS_SECRET_ACCESS_KEY': 'private'}
        with patch.dict(os.environ, supplied):
            before = os.environ.copy(); env = C.child_environment(self.config)
            self.assertEqual(os.environ.copy(), before)
            self.assertEqual(env['CLAUDE_CONFIG_DIR'], str(self.config.resolve()))
            self.assertEqual(env['CLAUDE_CODE_EFFORT_LEVEL'], 'medium')
            for key in supplied.keys() - {'CLAUDE_CONFIG_DIR', 'CLAUDE_CODE_EFFORT_LEVEL'}: self.assertNotIn(key, env)

    def test_development_account_and_missing_research_auth_are_refused(self):
        development = self.base / '.claude'; development.mkdir()
        (development / '.credentials.json').write_text('UNCHANGED', encoding='utf-8')
        with self.assertRaises(S.ScoutError): C.child_environment(development)
        (self.config / '.credentials.json').unlink()
        with self.assertRaises(S.ScoutError): C.child_environment(self.config)
        self.assertEqual((development / '.credentials.json').read_text(), 'UNCHANGED')

    def test_windows_discovery_finds_known_winget_path_without_shell_alias(self):
        target = self.base / C.WINGET; target.parent.mkdir(parents=True); target.write_text('stub')
        with patch.object(C.shutil, 'which', return_value=None), patch.dict(os.environ, {'LOCALAPPDATA': str(self.base)}):
            self.assertEqual(C.discover(), target.resolve())
        with self.assertRaises(S.ScoutError): C.discover(self.base / 'missing.exe')

    def test_managed_policy_presence_fails_before_subprocess(self):
        (self.config / 'managed-settings.json').write_text('{}')
        with self.assertRaises(S.ScoutError): C.ClaudeSubscription(self.exe, self.config, runner=self.runner)
        self.runner.assert_not_called()

    def test_actual_argv_fresh_context_medium_tools_and_machine_output(self):
        first, second = self.invoke(), self.invoke()
        calls = self.runner.call_args_list
        for call in calls:
            args = call.args[0]; kwargs = call.kwargs
            self.assertFalse(kwargs['shell']); self.assertEqual(kwargs['input'], C.SYNTHETIC_TEXT)
            self.assertEqual(args[args.index('--model') + 1], MODEL)
            self.assertEqual(args[args.index('--effort') + 1], 'medium')
            self.assertEqual(args[args.index('--tools') + 1], '')
            self.assertEqual(args[args.index('--setting-sources') + 1], '')
            for flag in ('--no-session-persistence', '--safe-mode', '--restricted', '--disable-slash-commands'): self.assertIn(flag, args)
            for flag in ('--bare', '--resume', '--continue', '--fallback-model', '--add-dir'): self.assertNotIn(flag, args)
            self.assertFalse(Path(kwargs['cwd']).is_relative_to(C.ROOT))
        self.assertNotEqual(calls[0].kwargs['cwd'], calls[1].kwargs['cwd'])
        self.assertNotEqual(first['context_id'], second['context_id'])
        self.assertTrue(first['isolation_verified']); self.assertIsNone(first['error'])
        self.assertEqual(first['stdout'], envelope())

    def test_usage_includes_cached_inputs_and_cost_is_not_subscription_charge(self):
        result = self.invoke()
        self.assertEqual(result['usage'], {'input_tokens': 60, 'output_tokens': 70, 'cost': S.UNKNOWN, 'currency': S.UNKNOWN})
        self.assertEqual(result['thinking_tokens'], 5)
        self.assertEqual(result['cli_list_price_estimate_usd'], 99.5)
        self.assertEqual(result['underlying_provider_requests'], S.UNKNOWN)
        self.assertEqual(result['effort_observed'], S.UNKNOWN)

    def test_unknown_usage_stays_unknown(self):
        self.runner.return_value.stdout = envelope(usage=False)
        r = self.invoke(); self.assertEqual(r['usage']['input_tokens'], S.UNKNOWN)
        self.assertEqual(r['usage']['output_tokens'], S.UNKNOWN)

    def test_elapsed_time_uses_monotonic_clock(self):
        with patch.object(C.time, 'monotonic', side_effect=[100.0, 112.25]): result = self.invoke()
        self.assertEqual(result['wall_seconds'], 12.25)
        self.assertLessEqual(S.timestamp(result['invoked_at']), S.timestamp(result['completed_at']))

    def test_invalid_json_duplicate_keys_and_timeout_keep_failures_without_retry(self):
        for raw in ('not json', '{"type":"result","type":"assistant"}', '[]'):
            self.runner.reset_mock(); self.runner.return_value.stdout = raw
            self.assertEqual(self.invoke()['error'], 'INVALID_CLI_ENVELOPE_NO_RETRY')
            self.runner.assert_called_once()
        self.runner.reset_mock(); self.runner.side_effect = subprocess.TimeoutExpired(['claude'], 1, output=b'partial', stderr=b'')
        r = self.invoke(timeout=1)
        self.assertEqual(r['error'], 'TIMEOUT_NO_RETRY'); self.assertEqual(r['stdout'], 'partial')
        self.runner.assert_called_once()

    def test_rate_limit_auth_and_process_failure_never_fall_back(self):
        for text, expected in [('HTTP 429 rate limit', 'RATE_LIMIT_NO_RETRY'), ('401 login needed', 'AUTHENTICATION_FAILED_NO_RETRY')]:
            self.runner.reset_mock(); self.runner.return_value = subprocess.CompletedProcess([], 1, '', text)
            self.assertEqual(self.invoke()['error'], expected); self.runner.assert_called_once()
        self.runner.side_effect = FileNotFoundError()
        self.assertEqual(self.invoke()['cli_invocations_started'], 0)

    def test_model_mismatch_or_second_model_is_rejected(self):
        self.runner.return_value.stdout = envelope(model='claude-sonnet-99')
        self.assertEqual(self.invoke()['error'], 'MODEL_MISMATCH_NO_RETRY')
        rows = [json.loads(x) for x in envelope().splitlines()]
        rows[-1]['modelUsage']['claude-sonnet-99'] = {}
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        self.assertEqual(self.invoke()['error'], 'MODEL_MISMATCH_NO_RETRY')

    def test_observed_effort_override_and_changed_structured_output_are_rejected(self):
        rows = [json.loads(x) for x in envelope().splitlines()]; rows[0]['effort'] = 'high'
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        self.assertEqual(self.invoke()['error'], 'EFFORT_MISMATCH_NO_RETRY')
        rows[0].pop('effort'); rows[-1]['structured_output'] = {'extra_deposit_units': 999}
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        self.assertEqual(self.invoke()['error'], 'STRUCTURED_OUTPUT_DIFFERS_FROM_MODEL_NO_RETRY')

    def test_repository_tool_mcp_skill_and_agent_leaks_fail_isolation(self):
        for key, value in [('tools', ['Read']), ('mcp_servers', ['private']), ('skills', ['private']), ('apiKeySource', 'apiKey')]:
            rows = [json.loads(x) for x in envelope().splitlines()]; rows[0][key] = value
            self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
            self.assertEqual(self.invoke()['error'], 'ISOLATION_NOT_ESTABLISHED_NO_RETRY')
        rows[-1]['subagent_stats']['spawned'] = 1
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        self.assertEqual(self.invoke()['error'], 'ISOLATION_NOT_ESTABLISHED_NO_RETRY')

    def test_credentials_are_withheld_from_failure_artifacts(self):
        self.runner.return_value.stderr = 'Authorization: Bearer sk-ant-private'
        r = self.invoke()
        self.assertNotIn('sk-ant-private', json.dumps(r)); self.assertNotIn('Bearer', r['stderr'])
        self.assertEqual(r['error'], 'CREDENTIAL_OUTPUT_WITHHELD_NO_RETRY')

    def test_no_transmission_without_payload_specific_consent(self):
        with self.assertRaises(S.ScoutError):
            self.client.invoke(C.SYNTHETIC_TEXT, C.SYNTHETIC_SCHEMA, MODEL, permit=None)
        text = 'Private research must not be sent.'
        permit = self.permit(); permit['payload_sha256'] = S.hash_text(text)
        with self.assertRaises(S.ScoutError): self.client.invoke(text, C.SYNTHETIC_SCHEMA, MODEL, permit=permit)
        self.runner.assert_not_called()

    def test_additional_visible_generation_or_repair_is_rejected(self):
        rows = [json.loads(x) for x in envelope().splitlines()]
        rows.insert(2, copy.deepcopy(rows[1]))
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        self.assertEqual(self.invoke()['error'], 'ISOLATION_NOT_ESTABLISHED_NO_RETRY')

    def test_thinking_and_output_chunks_with_same_message_id_are_one_generation(self):
        rows = [json.loads(x) for x in envelope().splitlines()]
        thinking = copy.deepcopy(rows[1]); thinking['message']['content'] = [{'type': 'thinking', 'thinking': ''}]
        rows.insert(1, thinking)
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        result = self.invoke()
        self.assertIsNone(result['error']); self.assertEqual(result['visible_assistant_message_ids'], ['msg_FICTIONAL_001'])
        rows[1]['message']['id'] = 'msg_FICTIONAL_DIFFERENT_GENERATION'
        self.runner.return_value.stdout = '\n'.join(json.dumps(x) for x in rows)
        self.assertEqual(self.invoke()['error'], 'ISOLATION_NOT_ESTABLISHED_NO_RETRY')

    def test_fixed_synthetic_preflight_resolves_and_checks_explicit_identity(self):
        auth = {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty', 'subscriptionType': 'pro'}
        self.runner.side_effect = [subprocess.CompletedProcess([], 0, '2.1.TEST', ''),
            subprocess.CompletedProcess([], 0, ' '.join(C.REQUIRED_FLAGS), ''),
            subprocess.CompletedProcess([], 0, json.dumps(auth), ''),
            subprocess.CompletedProcess([], 0, envelope(), ''),
            subprocess.CompletedProcess([], 0, envelope(), '')]
        result = C.synthetic_preflight(self.client)
        self.assertTrue(result['passed']); self.assertEqual(result['canonical_model'], MODEL)
        calls = self.runner.call_args_list[-2:]
        self.assertEqual(calls[0].args[0][calls[0].args[0].index('--model') + 1], 'opus')
        self.assertEqual(calls[1].args[0][calls[1].args[0].index('--model') + 1], MODEL)
        self.assertEqual(result['real_comparison_attempts_consumed'], 0)

    def test_inspection_requires_supported_flags_and_subscription_not_api_auth(self):
        help_text = ' '.join(C.REQUIRED_FLAGS)
        def inspect(auth, help_value=help_text):
            self.runner.side_effect = [subprocess.CompletedProcess([], 0, '2.1.TEST', ''),
                subprocess.CompletedProcess([], 0, help_value, ''),
                subprocess.CompletedProcess([], 0, json.dumps(auth), '')]
            return self.client.inspect()
        auth = {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty', 'subscriptionType': 'pro', 'email': 'NEVER_LOG'}
        self.assertNotIn('NEVER_LOG', json.dumps(inspect(auth)))
        with self.assertRaises(S.ScoutError): inspect({**auth, 'authMethod': 'api_key'})
        with self.assertRaises(S.ScoutError): inspect(auth, '--print')


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.base = Path(cls.temp.name)
        cls.package = cls.base / 'fictional-v002'; fictional_package(cls.package)
        invocations = []
        for model in ('opus', MODEL):
            record = {'schema': 'SCOUT_CLAUDE_INVOCATION_V003', 'error': None,
                'requested_model': model, 'actual_model': MODEL, 'isolation_verified': True,
                'payload_sha256': S.hash_text(C.SYNTHETIC_TEXT), 'response_schema_sha256': digest(C.SYNTHETIC_SCHEMA),
                'stdout': envelope(), 'stdout_sha256': S.hash_text(envelope()),
                'parameters': C.controls(), 'returncode': 0,
                'usage': {'input_tokens': S.UNKNOWN, 'output_tokens': S.UNKNOWN, 'cost': S.UNKNOWN, 'currency': S.UNKNOWN}}
            C.ClaudeSubscription._parse(record, record['stdout'], model)
            invocations.append(record)
        cls.preflight = {'schema': 'SCOUT_CLAUDE_PREFLIGHT_V003', 'passed': True,
            'development_account_files_unchanged': True,
            'research_inputs_transmitted': False, 'real_comparison_attempts_consumed': 0,
            'canonical_model': MODEL, 'inspection': {'controls': C.controls()},
            'invocations': invocations}
        cls.preflight_file = cls.base / 'preflight.json'; cls.preflight_file.write_bytes(canonical(cls.preflight))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.temp_run = tempfile.TemporaryDirectory(dir=self.base); self.addCleanup(self.temp_run.cleanup)
        self.store = Path(self.temp_run.name) / 'v003'
        self.originals = {n: p.read_bytes() for p in self.package.iterdir() for n in [p.name]}
        V3.prepare(self.store, self.preflight_file, self.package)

    def approve_fixture(self):
        value = V3.consent_template(self.store)
        value.update(owner_approved=True, approving_owner='SYNTHETIC_OWNER_FIXTURE', approved_at=S.utc_now(), accept_canonical_model_id_limit=True)
        path = Path(self.temp_run.name) / 'synthetic-owner.json'; path.write_bytes(canonical(value))
        V3.authorise(self.store, path)
        return value

    def client(self, failure=None):
        client = Mock(); client.inspect.return_value = self.preflight['inspection']
        def invoke(text, response_schema, model, **kw):
            prompt = S.json_loads(text); lane = prompt['lane']
            ideas = [idea(lane=lane, variant=j) for j in range(2)]
            if lane == 'GAP':
                for i in ideas: i['historical_refs'][0]['investigation'] = 'HIST-SYNTHETIC'
            return {'schema': 'SCOUT_CLAUDE_INVOCATION_V003', 'context_id': kw['context_id'],
                'actual_model': model, 'invoked_at': S.utc_now(), 'completed_at': S.utc_now(),
                'parameters': C.controls(), 'usage': {'input_tokens': 200, 'output_tokens': 1000, 'cost': S.UNKNOWN, 'currency': S.UNKNOWN},
                'wall_seconds': 5, 'error': failure, 'isolation_verified': failure is None,
                'thinking_tokens': S.UNKNOWN, 'cli_invocations_started': 1, 'visible_generation_attempts': 1,
                'underlying_provider_requests': S.UNKNOWN, 'output': canonical({'ideas': ideas}).decode()}
        client.invoke.side_effect = invoke
        return client

    def run_mock(self, client):
        with patch.object(V3, 'ClaudeSubscription', return_value=client): return V3.execute(self.store)

    def test_prospective_package_preserves_source_bytes_and_allocation(self):
        result = V3.status(self.store)
        self.assertEqual(result['generation_status'], 'NOT_RUN'); self.assertEqual(result['reserved_visible_attempts'], 12)
        self.assertFalse(result['hosted_owner_authorisation_valid'])
        for name, raw in self.originals.items(): self.assertEqual((self.package / name).read_bytes(), raw)
        _, manifest, _, states = V3.load(self.store)
        self.assertEqual(len(manifest['requests']), 12)
        for c, state in states.items():
            self.assertEqual([state.prompts[a['prompt_id']]['lane'] for a in state.attempts.values()], V.protocol('V003')['allocation'][c])
        with self.assertRaises(S.ScoutError): V3.prepare(self.store, self.preflight_file, self.package)

    def test_execution_without_consent_cannot_construct_a_client(self):
        with patch.object(V3, 'ClaudeSubscription') as client:
            with self.assertRaises(S.ScoutError): V3.execute(self.store)
            client.assert_not_called()

    def test_template_false_approval_wrong_model_changed_files_and_future_dates_are_refused(self):
        template = V3.consent_template(self.store)
        with self.assertRaises(S.ScoutError): V3.validate_consent(self.store, template)
        good = {**template, 'owner_approved': True, 'approving_owner': 'SYNTHETIC_OWNER',
                'approved_at': S.utc_now(), 'accept_canonical_model_id_limit': True}
        for k, v in [('model', 'opus'), ('approving_owner', S.UNKNOWN), ('approved_at', '2099-01-01T00:00:00Z'),
                     ('accept_canonical_model_id_limit', False), ('privacy_and_limitations', 'omit'), ('requests', [])]:
            with self.assertRaises(S.ScoutError): V3.validate_consent(self.store, {**good, k: v})
        path = self.store / 'exports/PLAIN-ATT-0001-request-v003.json'
        path.write_text('{}')
        with self.assertRaises(S.ScoutError): V3.validate_consent(self.store, good)

    def test_twelve_mocked_attempts_have_fresh_frozen_inputs_and_no_redispatch(self):
        self.approve_fixture(); client = self.client(); result = self.run_mock(client)
        self.assertEqual(client.invoke.call_count, 12); self.assertEqual(result['recorded_results'], 12)
        _, _, _, states = V3.load(self.store)
        self.assertEqual({len(s.cards) for s in states.values()}, {6})
        self.assertEqual(len({c.kwargs['context_id'] for c in client.invoke.call_args_list}), 12)
        for call in client.invoke.call_args_list:
            prompt = S.json_loads(call.args[0]); self.assertFalse(prompt['contains_generated_ideas'])
            self.assertNotIn('SYNTHETIC Industrial repair services mechanism control', call.args[0])
        self.assertFalse(result['fairness']['comparative_eligible'])  # Human minutes honestly UNKNOWN.
        with self.assertRaises(S.ScoutError): self.run_mock(client)
        self.assertEqual(client.invoke.call_count, 12)

    def test_failed_attempt_is_consumed_durably_stops_and_never_retries(self):
        self.approve_fixture(); client = self.client('RATE_LIMIT_NO_RETRY')
        result = self.run_mock(client)
        self.assertEqual(result['durable_dispatches'], 1); self.assertEqual(result['recorded_results'], 1)
        client.invoke.assert_called_once()
        self.assertEqual(Archive(self.store / 'PLAIN').load().attempts['ATT-0001']['result']['status'], 'ERROR')
        with self.assertRaises(S.ScoutError): self.run_mock(client)
        client.invoke.assert_called_once()

    def test_invalid_json_and_surplus_cards_are_retained_and_reviewed_without_replacement(self):
        self.approve_fixture(); client = self.client()
        invoke = client.invoke.side_effect
        def invalid(*args, **kwargs):
            record = invoke(*args, **kwargs)
            value = S.json_loads(record['output']); value['ideas'].append(copy.deepcopy(value['ideas'][0]))
            record['output'] = canonical(value).decode()
            return record
        client.invoke.side_effect = invalid
        result = self.run_mock(client)
        self.assertEqual(result['durable_dispatches'], 1); client.invoke.assert_called_once()
        state = Archive(self.store / 'PLAIN').load()
        self.assertEqual(state.attempts['ATT-0001']['result']['status'], 'INVALID')
        packet_paths = V3.blind(self.store, 'SYNTHETIC_PRIVATE_SALT_FOR_TEST_12345')
        packet = input_json(packet_paths['packet'])
        self.assertEqual(len(packet['cards']), 25)
        self.assertEqual(sum(not r['missing_card'] for r in packet['cards']), 3)
        self.assertFalse(packet['comparative_eligible'])

    def test_raw_malformed_output_is_private_but_failed_slots_stay_visible(self):
        self.approve_fixture(); client = self.client()
        invoke = client.invoke.side_effect
        def invalid(*args, **kwargs):
            record = invoke(*args, **kwargs); record['output'] = 'broken JSON with private model log'
            return record
        client.invoke.side_effect = invalid; self.run_mock(client)
        packet = input_json(V3.blind(self.store, 'SYNTHETIC_PRIVATE_SALT_FOR_TEST_12345')['packet'])
        self.assertEqual(len(packet['cards']), 24)
        self.assertTrue(all(row['missing_card'] for row in packet['cards']))
        self.assertNotIn('private model log', json.dumps(packet))

    def test_interrupted_subprocess_blocks_resumption_before_second_dispatch(self):
        self.approve_fixture(); client = self.client(); client.invoke.side_effect = RuntimeError('simulated power loss')
        with self.assertRaises(RuntimeError): self.run_mock(client)
        status = V3.status(self.store)
        self.assertEqual(status['durable_dispatches'], 1); self.assertEqual(status['recorded_results'], 0)
        self.assertEqual(len(status['missing_receipts']), 1)
        with self.assertRaises(S.ScoutError): self.run_mock(client)
        client.invoke.assert_called_once()

    def test_preflight_drift_refuses_model_dispatch(self):
        self.approve_fixture(); client = self.client(); client.inspect.return_value = {'controls': {}, 'cli_version': 'changed'}
        with self.assertRaises(S.ScoutError): self.run_mock(client)
        client.invoke.assert_not_called()

    def test_preflight_success_flags_cannot_hide_tampered_original_envelope(self):
        preflight = copy.deepcopy(self.preflight)
        preflight['invocations'][1]['stdout'] = envelope(model='claude-sonnet-99')
        preflight['invocations'][1]['stdout_sha256'] = S.hash_text(preflight['invocations'][1]['stdout'])
        with self.assertRaises(S.ScoutError): V3.verify_preflight(preflight)

    def test_v003_human_review_contract_requires_independence_and_keeps_fixture_labels_separate(self):
        self.approve_fixture(); self.run_mock(self.client())
        paths = V3.blind(self.store, 'SYNTHETIC_PRIVATE_SALT_FOR_TEST_12345')
        packet = input_json(paths['packet']); key = input_json(paths['private_key'])
        reviews = [{'blind_id': r['blind_id'], 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'FICTIONAL_REVIEW_TEST'},
            'independent_of_generation': True, 'coherent': 'UNKNOWN', 'falsifiable': 'UNKNOWN',
            'research_worthy': 'UNKNOWN', 'evidence_integrity': 'UNKNOWN', 'minutes': 1,
            'notes': 'SYNTHETIC software test only; no actual human assessment.',
            'atomic_answers': {q: 'unsure' for q in QUESTIONS}} for r in packet['cards']]
        result = V.evaluate_blind(packet, key, reviews)
        self.assertTrue(result['complete']); self.assertFalse(result['comparative_eligible'])
        self.assertEqual(result['fixture'], 'SYNTHETIC')
        for invalid in ({k: v for k, v in reviews[0].items() if k != 'independent_of_generation'},
                        {**reviews[0], 'reviewer': {'kind': 'HUMAN', 'id': 'UNSUPPORTED'}}):
            with self.assertRaises(S.ScoutError): V.evaluate_blind(packet, key, [invalid])

    def test_blinding_reviews_all_cards_with_no_metadata_or_fabricated_human_labels(self):
        self.approve_fixture(); self.run_mock(self.client())
        result = V3.blind(self.store, 'SYNTHETIC_PRIVATE_SALT_FOR_TEST_12345')
        packet = input_json(result['packet']); self.assertEqual(len(packet['cards']), 24)
        for row in packet['cards']:
            self.assertEqual(set(row), {'blind_id', 'idea', 'source_passages', 'format_valid', 'missing_card'})
            self.assertNotIn('historical_refs', row['idea']); self.assertNotIn('seed_ids', row['idea'])
        judgments = Path(self.temp_run.name) / 'judgments.json'; judgments.write_text('[]')
        report = V3.evaluate(self.store, judgments)
        self.assertEqual(report['reviewed'], 0); self.assertEqual(len(report['missing']), 24)
        self.assertFalse(report['human_labels_invented']); self.assertIsNone(report['composite_score'])

    def test_receipt_tampering_and_recomputed_chain_rule_bypass_fail(self):
        self.approve_fixture(); self.run_mock(self.client())
        path = self.store / 'exports/PLAIN-ATT-0001-invocation-v003.json'
        path.write_bytes(canonical({'changed': True}))
        with self.assertRaises(S.ScoutError): V3.status(self.store)
        archive = Archive(self.store / 'PLAIN')
        event = next(e for e in archive.load().events if e['type'] == 'v003_dispatch')
        with self.assertRaises(S.ScoutError): archive.append('v003_dispatch', event['record'], recorded_at=event['recorded_at'])


if __name__ == '__main__': unittest.main()
