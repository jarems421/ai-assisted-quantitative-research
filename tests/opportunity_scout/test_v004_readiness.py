"""Offline E2E: fictional streams, no account reads or hosted invocation."""
import ast
from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import schema as S, v004_package as P, v004_transport as T
from src.research.opportunity_scout import v004_replay as J, v004_runtime as R, v004_isolation as I
from tests.opportunity_scout import v004_fixtures as F


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.package = self.base / 'package'
        self.blueprints = F.blueprints()
        P.build(self.package, self.blueprints, F.runtime(), mode='SYNTHETIC')
        self.run = J.OfflineRun.create(self.base / 'run', self.package)

    def start(self):
        consumed = self.run.start()
        request = P.load(self.package)[1][consumed['slot']]
        return consumed, request

    def finish(self, edit=None, *, continuation=False, raw=None, usage=None, window=None, **record):
        consumed, request = self.start()
        events = F.events(request, consumed['session_id'], raw=raw, continuation=continuation, usage=usage)
        if edit: edit(events)
        window = F.window(consumed['session_id'], consumed['slot']) if window is None else window
        window['session_id'] = consumed['session_id']
        result = self.run.finish(T.Recording(F.encode(events), **record), window)
        self.assertEqual(self.run.status()['recorded_attempts'], 1)
        return result

    def assertStopped(self, result, code=None):
        self.assertEqual(result['outcome'], 'RUN_STOP')
        if code: self.assertIn(code, result['faults'])
        with self.assertRaises(S.ScoutError): self.run.start()
        with self.assertRaises(S.ScoutError): self.run.finish(T.Recording(b''), F.window())
        status = self.run.status(); self.assertEqual(status['consumed_attempts'], 1)
        self.assertEqual(status['undispatched'], 11); self.assertFalse(status['complete_scientific_comparison'])

    def test_success_preserves_exact_bytes_schema_and_unknown_provider_billing(self):
        r = self.finish(); self.assertEqual(r['outcome'], 'VALID')
        self.assertEqual(r['budget']['reported_combined_total'], 15000)
        self.assertEqual(r['underlying_provider_requests'], S.UNKNOWN)
        self.assertEqual(r['actual_subscription_charge'], S.UNKNOWN)
        self.assertEqual(r['cli_list_price_estimate_usd'], 9.99)
        folder = next((self.run.root / 'attempts').iterdir())
        self.assertEqual((folder/'output.bin').read_bytes(), r['exact_output'].encode())
        self.assertEqual(P.byte_hash((folder/'stdout.bin').read_bytes()), r['stdout_sha256'])

    def test_all_twelve_and_lane_validations_keep_fixed_denominators(self):
        for _ in range(12):
            consumed, request = self.start()
            r = self.run.finish(T.Recording(F.encode(F.events(request, consumed['session_id']))), F.window(consumed['session_id'], consumed['slot']))
            self.assertEqual(r['outcome'], 'VALID', r['faults'])
        status = self.run.status(); self.assertTrue(status['workflow_complete'])
        self.assertFalse(status['complete_scientific_comparison'])
        self.assertEqual(status['intended_card_denominator'], 24)
        with self.assertRaises(S.ScoutError): self.run.start()

    def test_malformed_format_consumes_and_can_only_advance_to_next_frozen_slot(self):
        r = self.finish(raw='```json\n{"ideas":[]}\n```')
        self.assertEqual(r['outcome'], 'FORMAT_FAILURE')
        self.assertEqual(r['exact_output'], '```json\n{"ideas":[]}\n```')
        next_slot = self.run.start()['slot']; self.assertEqual(next_slot, P.order()[1]['slot'])
        status = self.run.status(); self.assertEqual(status['consumed_attempts'], 2)
        self.assertFalse(status['workflow_complete'])

    def test_exact_append_only_output_limit_continuation(self):
        r = self.finish(continuation=True)
        self.assertEqual(r['outcome'], 'VALID'); self.assertEqual(r['visible_generations'], 2)
        self.assertEqual(r['continuations'], 1)

    def test_same_message_thinking_and_text_are_fragments_not_new_generation(self):
        def edit(es):
            first = copy.deepcopy(es[1]); first['message'].pop('stop_reason')
            first['message']['content'] = [{'type': 'thinking', 'thinking': 'FICTIONAL reasoning'}]
            es.insert(1, first)
        r = self.finish(edit); self.assertEqual(r['outcome'], 'VALID'); self.assertEqual(r['visible_generations'], 1)

    def test_third_generation(self):
        def edit(es):
            third = copy.deepcopy(es[-2]); third['request_id'] = 'FICTIONAL-third'
            third['message']['id'] = 'FICTIONAL-third'; es.insert(-1, third)
        self.assertStopped(self.finish(edit, continuation=True), 'THIRD_VISIBLE_GENERATION')

    def test_second_generation_without_notice(self):
        self.assertStopped(self.finish(lambda es: es.pop(2), continuation=True), 'UNVERIFIED_CONTINUATION')

    def test_notice_after_complete_candidate_cannot_be_repair_or_replacement(self):
        def edit(es):
            es[1]['message']['content'][0]['text'] = es[-1]['result']
        self.assertStopped(self.finish(edit, continuation=True), 'COMPLETE_ANSWER_REPLACEMENT')

    def test_regeneration_instead_of_append_does_not_match_terminal(self):
        def edit(es): es[-2]['message']['content'][0]['text'] = es[-1]['result']
        self.assertStopped(self.finish(edit, continuation=True), 'TERMINAL_ASSEMBLY_MISMATCH')

    def test_unknown_notice_or_task_change_is_not_accepted_as_output_recovery(self):
        def edit(es): es[2]['message']['content'][0]['text'] = 'Repair the schema and try again.'
        self.assertStopped(self.finish(edit, continuation=True), 'UNVERIFIED_CONTINUATION_NOTICE')

    def test_changed_model(self):
        self.assertStopped(self.finish(lambda es: es[1]['message'].update(model='claude-opus-99-2')), 'MODEL_MISMATCH')

    def test_changed_session_context(self):
        self.assertStopped(self.finish(lambda es: es[1].update(session_id='another-session')), 'CONTEXT_CHANGED_OR_UNKNOWN')

    def test_unexplained_request_id(self):
        self.assertStopped(self.finish(lambda es: es[-1].update(request_id='unexplained')), 'UNEXPLAINED_REQUEST_ID')

    def test_missing_request_id(self):
        self.assertStopped(self.finish(lambda es: es[1].pop('request_id')), 'MESSAGE_OR_REQUEST_ID_UNKNOWN')

    def test_rewritten_snapshot_or_changed_request_same_message(self):
        def edit(es):
            duplicate = copy.deepcopy(es[1]); duplicate['request_id'] = 'new-request'; es.insert(2, duplicate)
        self.assertStopped(self.finish(edit), 'REORDERED_OR_REWRITTEN_GENERATION')

    def test_tool_schema_repair_is_prohibited(self):
        def edit(es): es[1]['message']['content'] = [{'type': 'tool_use', 'name': 'StructuredOutput', 'input': {}}]
        self.assertStopped(self.finish(edit), 'PROHIBITED_TOOL_OR_CONTENT')

    def test_60000_inclusive_and_output_guide_not_cap(self):
        r = self.finish(usage=dict(zip(T.COMPONENTS, (10000, 10000, 10000, 30000))))
        self.assertEqual(r['outcome'], 'VALID'); self.assertEqual(r['budget']['reported_combined_total'], 60000)

    def test_combined_cached_budget_excess_stops(self):
        self.assertStopped(self.finish(usage=dict(zip(T.COMPONENTS, (0, 10000, 30000, 20001)))), 'COMBINED_ALLOWANCE_EXCEEDED')

    def test_usage_unknown_never_compliant(self):
        usage = dict(zip(T.COMPONENTS, (1000, 1000, 1000, 10000))); usage.pop('cache_read_input_tokens')
        self.assertStopped(self.finish(usage=usage), 'USAGE_UNKNOWN')

    def test_terminal_model_usage_conflict(self):
        def edit(es): es[-1]['modelUsage'][F.MODEL]['outputTokens'] += 1
        self.assertStopped(self.finish(edit), 'USAGE_CONFLICT')

    def test_thinking_is_not_added_again(self):
        usage = dict(zip(T.COMPONENTS, (10000, 10000, 10000, 30000)))
        usage['output_tokens_details'] = {'thinking_tokens': 10000}
        self.assertEqual(self.finish(usage=usage)['budget']['reported_combined_total'], 60000)

    def test_timeout_retains_partial_stream_and_all_simultaneous_faults(self):
        r = self.finish(raw='{"ideas": [', timed_out=True, returncode=1)
        self.assertStopped(r, 'TIMEOUT'); self.assertTrue(r['format_faults'])

    def test_designated_auth_failure_stops(self):
        def edit(es): es[-1].update(subtype='error_during_execution', is_error=True, api_error_status=401)
        self.assertStopped(self.finish(edit, returncode=1), 'AUTHENTICATION_FAILED')

    def test_rate_limit_stops(self):
        def edit(es): es[-1].update(subtype='error_during_execution', is_error=True, api_error_status=429)
        self.assertStopped(self.finish(edit, returncode=1), 'RATE_LIMIT')

    def test_auth_words_and_uuid_substrings_are_not_auth_errors(self):
        def edit(es): es[0]['plugins'] = [{'name': 'plugin-authoring-401-login'}]
        self.assertEqual(self.finish(edit)['termination'], 'SUCCESS')

    def test_contaminated_account_metadata_window_stops_without_leakage_claim(self):
        w = F.window(); w['samples'][-1]['files']['.claude.json'] = {'state': 'REGULAR_FILE', 'size': 42}
        r = self.finish(window=w); self.assertStopped(r, 'ACCOUNT_MONITORING_WINDOW_FAILED')
        self.assertEqual(r['account_monitoring']['historical_writer'], S.UNKNOWN)
        self.assertEqual(r['account_monitoring']['credential_leakage'], 'NOT_ESTABLISHED')

    def test_concurrent_development_process_stops(self):
        w = F.window(); w['process_samples'][13]['processes'].append({'pid': 777, 'parent_pid': 666,
            'started_at': '2026-10-22T11:00:00+00:00'})
        self.assertStopped(self.finish(window=w), 'ACCOUNT_MONITORING_WINDOW_FAILED')

    def test_unknown_observation_or_short_idle_window_stops(self):
        w = F.window(); w['process_samples'][0]['observable'] = False
        self.assertStopped(self.finish(window=w), 'ACCOUNT_MONITORING_WINDOW_FAILED')

    def test_no_research_account_fallback(self):
        w = F.window(); w['observed_config_dir'] = str(Path(w['home'])/'.claude')
        self.assertStopped(self.finish(window=w), 'ACCOUNT_MONITORING_WINDOW_FAILED')

    def test_crash_after_durable_marker_cannot_resume_or_reset(self):
        self.start(); reopened = J.OfflineRun(self.run.root)
        self.assertTrue(reopened.status()['pending_requires_owner_review'])
        with self.assertRaises(S.ScoutError): reopened.start()
        with self.assertRaises(S.ScoutError): reopened.finish(T.Recording(b''), F.window())
        with self.assertRaises(FileExistsError): J.OfflineRun.create(self.run.root, self.package)

    def test_lock_contention_does_not_consume(self):
        (self.run.root/'.lock').write_text('other writer')
        with self.assertRaises(S.ScoutError): self.run.start()
        self.assertEqual(self.run.status()['consumed_attempts'], 0)

    def test_journal_tampering_is_rejected(self):
        self.finish(); p = self.run.root/'journal.jsonl'; raw = p.read_bytes()
        p.write_bytes(raw.replace(b'"VALID"', b'"BROKEN"') + b' ')
        with self.assertRaises(S.ScoutError): self.run.status()

    def test_receipt_or_original_stream_tampering_is_rejected(self):
        self.finish(); folder = next((self.run.root/'attempts').iterdir())
        (folder/'stdout.bin').write_bytes(b'changed')
        with self.assertRaises(S.ScoutError): self.run.status()

    def test_package_implementation_or_payload_changes_fail_closed(self):
        p = next((self.package/'requests').iterdir()); p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(S.ScoutError): self.run.start()

    def test_package_preserves_full_schema_and_exact_scientific_projection(self):
        manifest, requests = P.load(self.package)
        for request in requests.values():
            payload = S.json_loads(request['transmitted_text'])
            for key in P.PROMPT_FIELDS: self.assertEqual(payload[key], request['source_prompt'][key])
            self.assertNotIn('max_output_tokens', payload)
            self.assertEqual(payload['response_schema']['properties']['ideas']['maxItems'], 2)
            self.assertEqual(payload['response_schema']['properties']['ideas']['items'], S.IDEA)
            self.assertEqual(request['complete_input_bound'], S.UNKNOWN)
        self.assertFalse(manifest['hosted_authorised'])

    def test_real_package_can_be_frozen_but_cannot_enter_offline_run(self):
        package = self.base/'real-local-only'
        P.build(package, self.blueprints, F.runtime(), mode='PROSPECTIVE_LOCAL_ONLY')
        with self.assertRaises(S.ScoutError): J.OfflineRun.create(self.base/'forbidden', package)
        consumed, request = self.start()
        with self.assertRaises(S.ScoutError): self.run.finish(T.Recording(b'', fictional=False), F.window())
        self.assertEqual(self.run.status()['consumed_attempts'], 1)

    def test_generated_blueprint_input_is_refused(self):
        bp = copy.deepcopy(self.blueprints); bp['PLAIN']['events'].append({'type': 'card', 'record': {}, 'recorded_at': F.MOMENT})
        with self.assertRaises(S.ScoutError): P.build(self.base/'bad', bp, F.runtime())

    def test_package_rejects_extra_file_and_cannot_overwrite(self):
        with self.assertRaises(FileExistsError): P.build(self.package, self.blueprints, F.runtime())
        (self.package/'extra').write_text('unexpected')
        with self.assertRaises(S.ScoutError): P.load(self.package)

    def test_frozen_order_balance_and_residual_carryover_are_explicit(self):
        rows = P.order(); sequence = [r['condition'] for r in rows]
        for i in (0, 4, 8): self.assertEqual(set(sequence[i:i+4]), set(P.CONDITIONS))
        sums = [sum(r['position'] for r in rows if r['condition'] == c) for c in P.CONDITIONS]
        self.assertEqual(sums, [20,19,19,20]); self.assertEqual(max(sums)-min(sums), 1)
        self.assertTrue(all(a!=b for a,b in zip(sequence,sequence[1:])))
        self.assertLess(len(set(zip(sequence,sequence[1:]))), 11) # not a fully balanced crossover

    def test_child_env_drops_credentials_ide_and_provider_overrides_without_modification(self):
        home = self.base/'home'; inherited = {'ANTHROPIC_API_KEY': 'FAKE', 'CLAUDE_CONFIG_DIR': 'development',
            'VSCODE_IPC_HOOK': 'FAKE', 'AWS_SECRET_ACCESS_KEY': 'FAKE', 'SYSTEMROOT': 'Windows'}
        original = copy.deepcopy(inherited)
        child = R.child_environment(inherited, home/'.claude-research', home)
        self.assertEqual(inherited, original)
        self.assertNotIn('ANTHROPIC_API_KEY', child); self.assertNotIn('VSCODE_IPC_HOOK', child)
        self.assertEqual(child['CLAUDE_CODE_MAX_OUTPUT_TOKENS'], '32768')
        with self.assertRaises(S.ScoutError): R.child_environment(inherited, home/'.claude', home)

    def test_source_boundary_no_process_or_network_runner(self):
        for module in (T, J, P, I, R):
            tree = ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
            imports = [n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
            names = [n.module if isinstance(n,ast.ImportFrom) else n.names[0].name for n in imports]
            self.assertFalse(any(n and n.split('.')[0] in ('subprocess','socket','requests','urllib','anthropic') for n in names))

    def test_clean_window_from_a_different_attempt_cannot_be_reused(self):
        self.finish()
        consumed, request = self.start()
        stale_window = F.window(consumed['session_id']) # Relabelled, but still the first slot's times.
        result = self.run.finish(T.Recording(F.encode(F.events(request, consumed['session_id']))), stale_window)
        self.assertEqual(result['outcome'], 'RUN_STOP')
        self.assertIn('REUSED_OR_OVERLAPPING_MONITORING_WINDOW', result['account_monitoring']['faults'])
        with self.assertRaises(S.ScoutError): self.run.start()
        self.assertEqual(self.run.status()['consumed_attempts'], 2)

    def test_monitoring_context_must_match_consumed_stream_context(self):
        consumed, request = self.start()
        result = self.run.finish(T.Recording(F.encode(F.events(request, consumed['session_id']))), F.window())
        self.assertEqual(result['outcome'], 'RUN_STOP')
        self.assertIn('MONITORING_SESSION_MISMATCH', result['account_monitoring']['faults'])


class RecordedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.requests = P.assemble(F.blueprints(), F.runtime(), 'SYNTHETIC')[2]

    def review(self, *, slot='PLAIN-ATT-0001', edit=None, raw=None, data=None, **meta):
        request = copy.deepcopy(self.requests[slot])
        es = F.events(request, 'FICTIONAL-session', raw=raw)
        if edit: edit(es)
        return T.review(T.Recording(F.encode(es) if data is None else data, **meta), request, 'FICTIONAL-session')

    def test_malformed_envelope_types_never_escape_without_a_failure(self):
        for raw in (b'not JSON\n', b'[]\n', b'\xff\n', b'{"type":"result","type":"assistant"}\n'):
            with self.subTest(raw=raw):
                r = self.review(data=raw); self.assertEqual(r['outcome'], 'RUN_STOP')
                self.assertEqual(r['budget']['budget_status'], 'UNKNOWN')
        for edit in (lambda es: es[-1].update(subagent_stats=None), lambda es: es[1].update(message=[]),
                     lambda es: es[-1].update(subtype=[]), lambda es: es[-1].update(usage=[])):
            self.assertEqual(self.review(edit=edit)['outcome'], 'RUN_STOP')

    def test_multiple_or_missing_terminal_is_run_stop(self):
        self.assertEqual(self.review(edit=lambda es: es.append(copy.deepcopy(es[-1])))['outcome'], 'RUN_STOP')
        self.assertEqual(self.review(edit=lambda es: es.pop())['outcome'], 'RUN_STOP')

    def test_auth_fallback_is_stderr_only_before_envelope(self):
        self.assertEqual(self.review(data=b'', stderr=b'Authentication failed', returncode=1)['termination'], 'AUTHENTICATION_FAILED')
        self.assertNotEqual(self.review(data=b'author login 401\n', stderr=b'', returncode=1)['termination'], 'AUTHENTICATION_FAILED')

    def test_max_turns_does_not_become_auth_due_to_data(self):
        def edit(es): es[-1].update(subtype='error_max_turns', is_error=True, errors=['author login 401'])
        self.assertEqual(self.review(edit=edit, returncode=1)['termination'], 'CLI_MAX_TURNS')

    def test_unknown_usage_and_numeric_bool_are_not_compliant(self):
        for bad in (None, True, -1, 1.5, 'UNKNOWN'):
            def edit(es): es[-1]['usage']['cache_creation_input_tokens'] = bad
            r = self.review(edit=edit); self.assertEqual(r['outcome'], 'RUN_STOP')
            self.assertEqual(r['budget']['budget_status'], 'UNKNOWN')

    def test_conflict_does_not_leave_budget_within_allowance_label(self):
        def edit(es): es[-1]['modelUsage'][F.MODEL]['outputTokens'] = 1
        self.assertEqual(self.review(edit=edit)['budget']['budget_status'], 'UNKNOWN')

    def test_lane_semantic_and_citation_validation_not_just_json_schema(self):
        for slot in ('EVIDENCE_ONLY-ATT-0001', 'MECHANISM_ONLY-ATT-0001', 'HYBRID-ATT-0003'):
            request = self.requests[slot]; value = F.output(request)
            if request['lane'] == 'RADAR': value['ideas'][0]['seed_ids'] = []
            elif request['lane'] == 'FORGE': value['ideas'][0]['seed_ids'] = ['SEED-UNSEEN']
            else: value['ideas'][0]['historical_refs'][0]['investigation'] = 'UNKNOWN-HISTORY'
            self.assertEqual(self.review(slot=slot, raw=json.dumps(value))['outcome'], 'FORMAT_FAILURE')
        value = F.output(self.requests['EVIDENCE_ONLY-ATT-0001'])
        value['ideas'][0]['mechanism']['links'][0]['evidence'] = [{'seed': value['ideas'][0]['seed_ids'][0], 'quote': 'FICTIONAL fabricated quotation'}]
        self.assertEqual(self.review(slot='EVIDENCE_ONLY-ATT-0001', raw=json.dumps(value))['outcome'], 'FORMAT_FAILURE')

    def test_surplus_stringified_and_duplicate_key_output_is_not_normalised(self):
        value = F.output(self.requests['PLAIN-ATT-0001']); value['ideas'].append(copy.deepcopy(value['ideas'][0]))
        for raw in (json.dumps(value), '{"ideas": "[]"}', '{"ideas":[],"ideas":[]}'):
            r = self.review(raw=raw); self.assertEqual(r['outcome'], 'FORMAT_FAILURE')
            self.assertEqual(r['exact_output'], raw)
        self.assertEqual(len(self.review(raw=json.dumps(value))['value']['ideas']), 3)

    def test_monitoring_gap_short_window_missing_parent_and_file_fields_fail(self):
        edits = (
            lambda w: w['samples'][1].update(sampled_at='2026-10-22T12:00:30+00:00'),
            lambda w: w['phases'].__setitem__(12, 'active'),
            lambda w: w.update(parent_pid=None),
            lambda w: w['samples'][0]['files'].__setitem__('.claude.json', {'state':'REGULAR_FILE','size':1}),
            lambda w: w['process_samples'][13].update(processes=[]))
        for edit in edits:
            w = F.window(); edit(w)
            self.assertFalse(I.review(w)['sampled_window_clean'])

    def test_old_frozen_directories_refused_for_new_output(self):
        for name in ('real-comparison-v003', 'v004-investigation', 'v004-feasibility'):
            with self.assertRaises(S.ScoutError): P.destination(P.ROOT/'.research/opportunity_scout'/name/'new')


if __name__ == '__main__': unittest.main()
