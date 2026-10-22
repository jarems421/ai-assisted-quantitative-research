"""Fictional R3 end-to-end evidence; no provider, account or private artifacts.

The tabular oracle states outcomes independently of production classification.
All consumption numbers and cards are fictional, including the 122304 trace.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import schema as S
from src.research.opportunity_scout import v004_package as OLD_P, v004_replay as OLD_J, v004_transport as OLD_T
from src.research.opportunity_scout.v004_r3 import package as P, runtime as R, policy as G, replay as J, transport as T
from tests.opportunity_scout import v004_fixtures as F


BOUNDARIES = ((60000, 'ORDINARY_USAGE_VARIATION', 'VALID'),
              (60001, 'ORDINARY_USAGE_VARIATION', 'VALID'),
              (119999, 'ORDINARY_USAGE_VARIATION', 'VALID'),
              (120000, 'ELEVATED_USAGE_RECORDED', 'VALID'),
              (122304, 'ELEVATED_USAGE_RECORDED', 'VALID'),
              (199999, 'ELEVATED_USAGE_RECORDED', 'VALID'),
              (200000, 'RESOURCE_EMERGENCY_STOP', 'RUN_STOP'),
              (200001, 'RESOURCE_EMERGENCY_STOP', 'RUN_STOP'))


def usage(total):
    return dict(zip(G.COMPONENTS, (total - 14000, 1000, 1000, 12000)))


def settings(): return R.description(F.MODEL, 'a' * 64, 'FICTIONAL-2.1.302')


def sample(session, sequence, values):
    return {'source': 'FICTIONAL_CUMULATIVE_ATTEMPT_USAGE_V1', 'session_id': session,
            'sequence': sequence, 'usage': dict(values)}


class R3RecordedStreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.requests = P.assemble(F.blueprints(), settings(), 'SYNTHETIC')

    def review(self, *, total=60001, raw=None, continuation=False, change=None, **metadata):
        request = self.requests['PLAIN-ATT-0001']
        events = F.events(request, 'FICTIONAL-session', raw=raw, continuation=continuation, usage=usage(total))
        if change: change(events)
        recording = T.Recording(F.encode(events), **metadata)
        return T.review(recording, request, 'FICTIONAL-session'), recording

    def test_boundary_oracle_through_complete_transport(self):
        for total, classification, outcome in BOUNDARIES:
            with self.subTest(total=total):
                result, _ = self.review(total=total)
                self.assertEqual(result['outcome'], outcome)
                self.assertEqual(result['resource']['reported_combined_total'], total)
                self.assertEqual(result['resource']['classification'], classification)
                self.assertEqual(result['content_status'], 'VALID')
                self.assertEqual(result['integrity_faults'], [])
                self.assertEqual(result['resource']['difference_from_planning_reference'], total - 60000)
                # Independent statement: annotation from 120000, emergency from 200000.
                self.assertEqual(result['resource']['elevated_usage_flag'], total >= 120000)
                self.assertEqual(result['resource']['emergency_detected'], total >= 200000)
                self.assertEqual(result['resource']['stop_reasons'],
                                 ['RESOURCE_EMERGENCY_STOP'] if total >= 200000 else [])

    def test_122304_append_only_continuation_permitted_without_shortening(self):
        expected = dict(zip(G.COMPONENTS, (12000, 32768, 12000, 65536)))
        result, recording = self.review(total=122304, continuation=True,
                                        change=lambda e: self.replace_usage(e, expected))
        self.assertEqual(result['outcome'], 'VALID')
        self.assertEqual(result['visible_generations'], 2)
        self.assertEqual(result['continuations'], 1)
        self.assertEqual(result['resource']['reported_combined_total'], 122304)
        self.assertEqual(result['resource']['reported_output_total'], 65536)
        terminal = S.json_loads(recording.stdout.decode().splitlines()[-1])
        self.assertEqual(result['exact_output'], terminal['result'])
        self.assertFalse(result['resource']['stop_reasons'])

    @staticmethod
    def replace_usage(events, counts):
        events[-1]['usage'] = counts
        events[-1]['modelUsage'][F.MODEL] = dict(zip(G.MODEL_COMPONENTS, (counts.get(k, S.UNKNOWN) for k in G.COMPONENTS)))

    def test_all_cache_components_once_thinking_and_model_totals_not_added(self):
        counts = {'input_tokens': 7001, 'cache_creation_input_tokens': 20000,
                  'cache_read_input_tokens': 30000, 'output_tokens': 20000,
                  'output_tokens_details': {'thinking_tokens': 15000},
                  'cache_creation': {'ephemeral_5m_input_tokens': 20000}}
        result, _ = self.review(change=lambda e: self.replace_usage(e, counts))
        resource = result['resource']
        self.assertEqual(resource['reported_combined_total'], 77001)
        self.assertEqual(resource['reported_input_total'], 57001)
        self.assertEqual(resource['reported_thinking_subcount'], 15000)
        self.assertEqual(result['cli_list_price_estimate_usd'], 9.99)
        self.assertEqual(result['actual_subscription_charge'], S.UNKNOWN)
        self.assertEqual(result['underlying_provider_requests'], S.UNKNOWN)

    def test_missing_negative_boolean_float_and_conflicting_final_usage_stop(self):
        mutations = [lambda e: e[-1].pop('usage'),
                     lambda e: e[-1]['usage'].pop('cache_read_input_tokens'),
                     lambda e: e[-1]['usage'].update(output_tokens=-1),
                     lambda e: e[-1]['usage'].update(input_tokens=True),
                     lambda e: e[-1]['usage'].update(input_tokens=60000.0),
                     lambda e: e[-1]['modelUsage'][F.MODEL].update(inputTokens=1),
                     lambda e: e[-1]['usage'].update(output_tokens_details={'thinking_tokens': 12001}),
                     lambda e: e[-1]['usage'].update(output_tokens=0)]
        for mutation in mutations:
            result, _ = self.review(change=mutation)
            self.assertEqual(result['outcome'], 'RUN_STOP')
            self.assertEqual(result['content_status'], 'VALID')
            self.assertEqual(result['resource']['classification'], 'MEASUREMENT_INTEGRITY_STOP')
            self.assertEqual(result['resource']['reported_combined_total'], S.UNKNOWN)
            self.assertIn('MEASUREMENT_INTEGRITY_STOP', result['faults'])

    def test_format_failure_separate_from_elevated_and_emergency_usage(self):
        result, _ = self.review(total=120000, raw='{"ideas":')
        self.assertEqual((result['outcome'], result['content_status']), ('FORMAT_FAILURE', 'INVALID'))
        self.assertEqual(result['resource']['classification'], 'ELEVATED_USAGE_RECORDED')
        result, _ = self.review(total=200000, raw='{"ideas":')
        self.assertEqual((result['outcome'], result['content_status']), ('RUN_STOP', 'INVALID'))
        self.assertTrue(result['format_faults'])
        self.assertIn('RESOURCE_EMERGENCY_STOP', result['faults'])

    def test_final_conflict_does_not_erase_simultaneously_reported_emergency(self):
        result, _ = self.review(total=200000,
                               change=lambda e: e[-1]['modelUsage'][F.MODEL].update(inputTokens=1))
        self.assertEqual(result['resource']['reported_combined_total'], S.UNKNOWN)
        self.assertEqual(result['resource']['unreconciled_reported_component_total'], 200000)
        self.assertEqual(result['resource']['stop_reasons'], ['MEASUREMENT_INTEGRITY_STOP', 'RESOURCE_EMERGENCY_STOP'])

    def test_third_generation_is_integrity_stop_at_both_resource_levels(self):
        def third(events):
            extra = copy.deepcopy(events[-2])
            extra['message']['id'] = 'FICTIONAL-message-3'; extra['request_id'] = 'FICTIONAL-request-3'
            extra['message']['content'] = [{'type': 'text', 'text': ''}]
            events.insert(-1, extra)
        for total in (15000, 200000):
            result, _ = self.review(total=total, continuation=True, change=third)
            self.assertEqual(result['outcome'], 'RUN_STOP')
            self.assertIn('THIRD_VISIBLE_GENERATION', result['integrity_faults'])
            self.assertEqual(result['visible_generations'], 3)
            if total == 200000: self.assertIn('RESOURCE_EMERGENCY_STOP', result['faults'])

    def test_repairs_replacements_request_context_and_model_changes_always_stop(self):
        def tool_repair(e):
            e[1]['message']['content'].append({'type': 'tool_use', 'name': 'StructuredOutput', 'input': {}})
        def replacement(e):
            e[1]['message']['content'][0]['text'] = json.dumps(F.output(self.requests['PLAIN-ATT-0001']))
        cases = [(tool_repair, False, 'PROHIBITED_TOOL_OR_CONTENT'),
                 (replacement, True, 'COMPLETE_ANSWER_REPLACEMENT'),
                 (lambda e: e[-1].update(request_id='unexplained'), False, 'UNEXPLAINED_REQUEST_ID'),
                 (lambda e: e[1].update(session_id='different'), False, 'CONTEXT_CHANGED_OR_UNKNOWN'),
                 (lambda e: e[1]['message'].update(model='other-model'), False, 'MODEL_MISMATCH'),
                 (lambda e: e[2]['message']['content'][0].update(text='Please fix the JSON'), True,
                  'UNVERIFIED_CONTINUATION_NOTICE')]
        for mutate, continuation, fault in cases:
            with self.subTest(fault=fault):
                result, _ = self.review(total=15000, continuation=continuation, change=mutate)
                self.assertEqual(result['outcome'], 'RUN_STOP')
                self.assertIn(fault, result['integrity_faults'])

    def test_timeout_auth_and_failed_terminal_keep_resource_and_content_separate(self):
        result, _ = self.review(timed_out=True, returncode=1)
        self.assertEqual(result['termination'], 'TIMEOUT')
        self.assertEqual(result['content_status'], 'VALID')
        self.assertEqual(result['outcome'], 'RUN_STOP')
        def auth(e):
            e.insert(-1, {'type': 'error', 'session_id': 'FICTIONAL-session', 'api_error_status': 401,
                          'error': {'type': 'authentication_error'}})
        result, _ = self.review(change=auth, returncode=1)
        self.assertEqual(result['termination'], 'AUTHENTICATION_FAILED')
        result, _ = self.review(change=lambda e: e[-1].update(subtype='error_max_turns', is_error=True), returncode=1)
        self.assertEqual(result['termination'], 'CLI_MAX_TURNS')

    def test_auth_words_in_stdout_are_not_auth_failure(self):
        result, _ = self.review(raw='401 auth login 429')
        self.assertEqual(result['termination'], 'SUCCESS')
        self.assertEqual(result['outcome'], 'FORMAT_FAILURE')

    def test_unchanged_full_schema_and_lane_citation_semantics_enforced(self):
        for condition in P.CONDITIONS:
            for request in (r for r in self.requests.values() if r['condition'] == condition):
                events = F.events(request, 'FICTIONAL-session', usage=usage(60001))
                result = T.review(T.Recording(F.encode(events)), request, 'FICTIONAL-session')
                self.assertEqual(result['outcome'], 'VALID')
        request = next(r for r in self.requests.values() if r['lane'] == 'RADAR')
        value = F.output(request); value['ideas'][0]['seed_ids'] = ['NONEXISTENT']
        result = T.review(T.Recording(F.encode(F.events(request, 's', raw=json.dumps(value)))), request, 's')
        self.assertEqual(result['outcome'], 'FORMAT_FAILURE')
        self.assertTrue(result['format_faults'])


class R3TelemetryTests(unittest.TestCase):
    def test_no_live_meter_is_not_zero_or_measurement_failure(self):
        live = G.review_live_samples((), 'session')
        self.assertEqual(live['reported_cumulative_lower_bound'], S.UNKNOWN)
        self.assertEqual(live['native_cli_support'], S.UNKNOWN)
        result = G.reconcile(G.assess_final_usage(usage(60001)), live)
        self.assertFalse(result['stop_reasons'])

    def test_duplicate_samples_not_summed_and_emergency_is_decision_only(self):
        s1 = sample('s', 1, usage(120000)); s2 = sample('s', 2, usage(200000))
        live = G.review_live_samples([s1, copy.deepcopy(s1), s2, copy.deepcopy(s2)], 's')
        self.assertEqual(live['reported_cumulative_lower_bound'], 200000)
        self.assertEqual(live['deduplicated_repeats'], 2)
        self.assertEqual(live['cancellation_signal'], 'CANCEL_IF_SUPPORTED')
        self.assertFalse(live['cancellation_performed'])
        self.assertFalse(live['guaranteed_limit'])
        result = G.reconcile(G.assess_final_usage(usage(200000)), live)
        self.assertEqual(result['classification'], 'RESOURCE_EMERGENCY_STOP')

    def test_untrusted_source_or_changed_session_cannot_issue_numeric_cancellation(self):
        for field, value in [('source', 'NATIVE_UNVERIFIED'), ('session_id', 'different')]:
            s = sample('s', 1, usage(999999)); s[field] = value
            live = G.review_live_samples([s], 's')
            self.assertEqual(live['cancellation_signal'], 'NONE')
            self.assertEqual(live['reported_cumulative_lower_bound'], S.UNKNOWN)
            result = G.reconcile(G.assess_final_usage(usage(60001)), live)
            self.assertEqual(result['classification'], 'MEASUREMENT_INTEGRITY_STOP')

    def test_conflicting_nonmonotone_or_malformed_supplied_counters_fail_closed(self):
        s1 = sample('s', 1, usage(120000)); s2 = sample('s', 2, usage(60001))
        changed = copy.deepcopy(s1); changed['usage']['input_tokens'] += 1
        for samples in ([s1, s2], [s1, changed], [None], {'input_tokens': 200000}):
            live = G.review_live_samples(samples, 's')
            self.assertTrue(live['issues'])
            result = G.reconcile(G.assess_final_usage(usage(120000)), live)
            self.assertEqual(result['reported_combined_total'], S.UNKNOWN)
            self.assertIn('MEASUREMENT_INTEGRITY_STOP', result['stop_reasons'])

    def test_emergency_evidence_survives_later_conflict_and_final_below_live(self):
        s1 = sample('s', 1, usage(200000)); s2 = sample('s', 2, usage(60001))
        for samples in ([s1], [s1, s2]):
            result = G.reconcile(G.assess_final_usage(usage(60001)), G.review_live_samples(samples, 's'))
            self.assertEqual(result['classification'], 'MEASUREMENT_INTEGRITY_STOP')
            self.assertEqual(result['reported_combined_total'], S.UNKNOWN)
            self.assertEqual(result['stop_reasons'], ['MEASUREMENT_INTEGRITY_STOP', 'RESOURCE_EMERGENCY_STOP'])


class R3JournalPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.package = self.base / 'package'
        self.manifest = P.build(self.package, F.blueprints(), settings(), mode='SYNTHETIC')
        self.requests = P.load(self.package)[1]
        self.run = J.OfflineRun.create(self.base / 'run', self.package)

    def finish(self, total=60001, *, change=None, raw=None, continuation=False, contaminated=False, live=False):
        consumed = self.run.start(); request = self.requests[consumed['slot']]
        events = F.events(request, consumed['session_id'], raw=raw, continuation=continuation, usage=usage(total))
        if change: change(events)
        window = F.window(consumed['session_id'], consumed['slot'])
        if contaminated: window['samples'][13]['files']['.claude.json'] = {'state': 'PRESENT'}
        telemetry = (sample(consumed['session_id'], 1, usage(total)),) if live else ()
        recording = T.Recording(F.encode(events), live_usage_samples=telemetry)
        receipt = self.run.finish(recording, window)
        return receipt, recording, consumed

    def test_package_policy_runtime_requests_schema_projection_all_bound(self):
        manifest, files, requests = P.assemble(F.blueprints(), settings(), 'SYNTHETIC')
        _, old_files, old_requests = OLD_P.assemble(F.blueprints(), F.runtime(), 'SYNTHETIC')
        self.assertNotIn('combined_allowance', manifest['runtime'])
        self.assertEqual(manifest['runtime']['resource_policy'], G.description())
        self.assertEqual(manifest['resource_policy_sha256'], digest(G.description()))
        self.assertEqual(files['schema.json'], old_files['schema.json'])
        self.assertEqual(files['projection.json'], old_files['projection.json'])
        protocol = S.json_loads(files['protocol.json'].decode())
        self.assertEqual(protocol['resource_policy'], G.description())
        self.assertEqual(protocol['intended_attempts'], 12)
        self.assertEqual(protocol['intended_cards'], 24)
        self.assertFalse(protocol['hosted_authorised'])
        self.assertEqual(manifest['order'], OLD_P.order())
        self.assertEqual(len(requests), 12)
        for slot, request in requests.items():
            self.assertEqual(request['resource_policy_sha256'], G.policy_hash())
            self.assertEqual(request['runtime_sha256'], digest(settings()))
            payload = S.json_loads(request['transmitted_text'])
            old_payload = S.json_loads(old_requests[slot]['transmitted_text'])
            self.assertEqual(set(payload), set(OLD_P.PROMPT_FIELDS))
            for key in OLD_P.PROMPT_FIELDS: self.assertEqual(payload[key], old_payload[key])
        self.assertTrue(any('/v004_r3/' in name for name in manifest['implementation']))

    def test_elevated_format_failure_consumed_then_next_frozen_slot(self):
        first, recording, consumed = self.finish(120000, raw='{"ideas":')
        self.assertEqual(first['outcome'], 'FORMAT_FAILURE')
        folder = self.run.root / 'attempts' / consumed['slot']
        self.assertEqual((folder / 'stdout.bin').read_bytes(), recording.stdout)
        self.assertEqual((folder / 'output.bin').read_bytes(), b'{"ideas":')
        with self.assertRaises(S.ScoutError): self.run.finish(recording, F.window())
        self.assertEqual(self.run.start()['slot'], self.manifest['order'][1]['slot'])
        status = self.run.status()
        self.assertEqual(status['actual_usage_outcome']['reported_combined_total'], S.UNKNOWN)
        self.assertEqual(status['actual_usage_outcome']['known_combined_subtotal'], 120000)

    def test_emergency_receipt_preserves_valid_content_and_all_denominators(self):
        receipt, recording, consumed = self.finish(200000, live=True)
        self.assertEqual(receipt['content_status'], 'VALID')
        self.assertEqual(receipt['resource']['live_telemetry']['cancellation_signal'], 'CANCEL_IF_SUPPORTED')
        status = J.OfflineRun(self.run.root).status()
        self.assertTrue(status['stopped']); self.assertFalse(status['workflow_complete'])
        self.assertEqual(status['intended_attempt_denominator'], 12)
        self.assertEqual(status['intended_card_denominator'], 24)
        self.assertEqual((status['consumed_attempts'], status['recorded_attempts'], status['undispatched']), (1, 1, 11))
        self.assertEqual(len(status['slots']), 12)
        self.assertEqual(sum(s['intended_card_slots'] for s in status['slots']), 24)
        self.assertEqual([s['status'] for s in status['slots'][1:]], ['NOT_RUN'] * 11)
        self.assertFalse(status['complete_scientific_comparison'])
        with self.assertRaises(S.ScoutError): self.run.start()
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()
        folder = self.run.root / 'attempts' / consumed['slot']
        self.assertEqual((folder / 'stdout.bin').read_bytes(), recording.stdout)
        self.assertEqual(json.loads((folder / 'receipt.json').read_bytes())['resource'], receipt['resource'])

    def test_unknown_usage_and_contaminated_windows_stop_independently(self):
        receipt, _, _ = self.finish(change=lambda e: e[-1].pop('usage'), contaminated=True)
        self.assertEqual(receipt['outcome'], 'RUN_STOP')
        self.assertIn('MEASUREMENT_INTEGRITY_STOP', receipt['faults'])
        self.assertIn('ACCOUNT_MONITORING_WINDOW_FAILED', receipt['integrity_faults'])
        status = self.run.status()
        self.assertEqual(status['actual_usage_outcome']['reported_combined_total'], S.UNKNOWN)
        self.assertEqual(status['actual_usage_outcome']['unknown_combined_entries'], 1)
        with self.assertRaises(S.ScoutError): self.run.start()

    def test_interruption_is_unknown_consumption_not_zero_and_cannot_resume(self):
        self.run.start(); status = J.OfflineRun(self.run.root).status()
        self.assertTrue(status['pending_requires_owner_review'])
        self.assertEqual(status['actual_usage_outcome']['reported_combined_total'], S.UNKNOWN)
        self.assertEqual(status['actual_usage_outcome']['unrecorded_consumed_attempts'], 1)
        self.assertEqual([s['status'] for s in status['slots']], ['CONSUMED_INTERRUPTED'] + ['NOT_RUN'] * 11)
        self.assertEqual(sum(s['intended_card_slots'] for s in status['slots']), 24)
        self.assertEqual(status['undispatched'], 11)
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()

    def test_low_usage_third_generation_stops_later_dispatch_and_keeps_denominators(self):
        def third(events):
            extra = copy.deepcopy(events[-2])
            extra['message']['id'] = 'FICTIONAL-message-3'; extra['request_id'] = 'FICTIONAL-request-3'
            extra['message']['content'] = [{'type': 'text', 'text': ''}]
            events.insert(-1, extra)
        self.finish(60001)
        receipt, _, _ = self.finish(15000, continuation=True, change=third)
        self.assertEqual(receipt['outcome'], 'RUN_STOP')
        self.assertEqual(receipt['resource']['classification'], 'ORDINARY_USAGE_VARIATION')
        self.assertIn('THIRD_VISIBLE_GENERATION', receipt['integrity_faults'])
        status = J.OfflineRun(self.run.root).status()
        self.assertTrue(status['stopped'])
        self.assertEqual([s['status'] for s in status['slots']], ['VALID', 'RUN_STOP'] + ['NOT_RUN'] * 10)
        self.assertEqual((len(status['slots']), status['intended_card_denominator'], status['undispatched']), (12, 24, 10))
        self.assertEqual(status['actual_usage_outcome']['emergency_events'], 0)
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()

    def test_complete_fictional_schedule_independent_component_and_condition_oracle(self):
        values = (60001, 120000, 199999, 122304, 60001, 120000, 199999, 122304, 60001, 120000, 199999, 122304)
        expected_conditions = {c: 0 for c in P.CONDITIONS}
        for index, total in enumerate(values):
            receipt, _, consumed = self.finish(total, continuation=(total == 122304))
            self.assertEqual(receipt['outcome'], 'VALID')
            expected_conditions[self.manifest['order'][index]['condition']] += total
        status = self.run.status()
        self.assertTrue(status['workflow_complete']); self.assertTrue(status['all_scheduled_slots_recorded'])
        self.assertFalse(status['complete_scientific_comparison'])
        self.assertEqual(status['actual_usage_outcome']['reported_combined_total'], sum(values))
        self.assertEqual(status['actual_usage_outcome']['elevated_annotations'], 9)
        for condition, expected in expected_conditions.items():
            self.assertEqual(status['per_condition_usage'][condition]['reported_combined_total'], expected)
        for checkpoint in status['block_checkpoints']:
            self.assertTrue(checkpoint['checkpoint_reached'])
            self.assertEqual(checkpoint['usage']['reported_combined_total'], sum(values[:checkpoint['after_position']]))
        for index, row in enumerate(status['slots']):
            self.assertEqual(row['cumulative_attempt_usage']['reported_combined_total'], sum(values[:index + 1]))
            self.assertEqual(row['visible_generations'], 2 if values[index] == 122304 else 1)
            self.assertEqual(row['actual_subscription_charge'], S.UNKNOWN)
        with self.assertRaises(S.ScoutError): self.run.start()

    def test_final_slot_emergency_retains_all_records_without_event_free_completion(self):
        for _ in range(11): self.finish(60001)
        self.finish(200000)
        status = self.run.status()
        self.assertEqual(status['undispatched'], 0)
        self.assertTrue(status['all_scheduled_slots_recorded'])
        self.assertTrue(status['data_complete_with_governance_event'])
        self.assertFalse(status['workflow_complete'])
        self.assertEqual(len(status['run_events']), 1)

    def test_package_changes_and_extra_files_fail_closed(self):
        target = self.package / 'resource-policy.json'
        original = target.read_bytes()
        changed = G.description(); changed['emergency_trigger_at_tokens'] = 300000
        target.write_bytes(canonical(changed) + b'\n')
        with self.assertRaises(S.ScoutError): self.run.start()
        target.write_bytes(original)
        (self.package / 'extra.json').write_bytes(b'{}')
        with self.assertRaises(S.ScoutError): self.run.start()

    def test_witness_suffix_rollback_and_raw_evidence_tamper_detected(self):
        self.finish(); journal = self.run.root / 'journal.jsonl'; original = journal.read_bytes()
        journal.write_bytes(b'\n'.join(original.splitlines()[:-1]) + b'\n')
        with self.assertRaises(S.ScoutError): self.run.status()
        journal.write_bytes(original)
        raw = self.run.root / 'attempts' / 'PLAIN-ATT-0001' / 'stdout.bin'
        raw.write_bytes(raw.read_bytes() + b'\n')
        with self.assertRaises(S.ScoutError): self.run.status()

    def test_failed_finish_preserves_consumption_and_cannot_choose_another_answer(self):
        consumed = self.run.start(); request = self.requests[consumed['slot']]
        recording = T.Recording(F.encode(F.events(request, consumed['session_id'])))
        with patch.object(J, 'evaluate', side_effect=RuntimeError('fictional interruption')):
            with self.assertRaises(RuntimeError): self.run.finish(recording, F.window(consumed['session_id']))
        self.assertEqual((self.run.root / 'attempts' / consumed['slot'] / 'stdout.bin').read_bytes(), recording.stdout)
        with self.assertRaises(S.ScoutError): self.run.finish(recording, F.window(consumed['session_id']))
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()

    def test_unencodable_counter_metadata_preserves_raw_bytes_and_interrupted_consumption(self):
        consumed = self.run.start(); request = self.requests[consumed['slot']]
        recording = T.Recording(F.encode(F.events(request, consumed['session_id'])), stderr=b'fictional stderr',
                                live_usage_samples={object()})
        with self.assertRaises(TypeError): self.run.finish(recording, F.window(consumed['session_id']))
        folder = self.run.root / 'attempts' / consumed['slot']
        self.assertEqual((folder / 'stdout.bin').read_bytes(), recording.stdout)
        self.assertEqual((folder / 'stderr.bin').read_bytes(), recording.stderr)
        self.assertEqual(self.run.status()['actual_usage_outcome']['reported_combined_total'], S.UNKNOWN)
        with self.assertRaises(S.ScoutError): self.run.finish(recording, F.window(consumed['session_id']))
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()

    def test_legacy_r2_result_and_source_inventory_preserved_not_reinterpreted(self):
        before = OLD_P.implementation()
        old_package = self.base / 'old-package'; old_run_path = self.base / 'old-run'
        OLD_P.build(old_package, F.blueprints(), F.runtime(), mode='SYNTHETIC')
        old = OLD_J.OfflineRun.create(old_run_path, old_package); consumed = old.start()
        old_request = OLD_P.load(old_package)[1][consumed['slot']]
        old_recording = OLD_T.Recording(F.encode(F.events(old_request, consumed['session_id'], usage=usage(60001))))
        receipt = old.finish(old_recording, F.window(consumed['session_id']))
        self.assertEqual(receipt['outcome'], 'RUN_STOP')
        prior = {p: p.read_bytes() for p in old_run_path.rglob('*') if p.is_file()}
        result, _, _ = self.finish(60001)
        self.assertEqual(result['outcome'], 'VALID')
        self.assertEqual(OLD_P.implementation(), before)
        self.assertEqual(prior, {p: p.read_bytes() for p in old_run_path.rglob('*') if p.is_file()})
        with self.assertRaises(S.ScoutError): J.OfflineRun.create(self.base / 'reject-old', old_package)
        with self.assertRaises(S.ScoutError): OLD_P.load(self.package)
        with self.assertRaises(S.ScoutError): P.build(self.base / 'reject-runtime', F.blueprints(), F.runtime())

    def test_non_synthetic_package_is_never_dispatchable(self):
        prospective = self.base / 'prospective'
        P.build(prospective, F.blueprints(), settings(), mode='PROSPECTIVE_LOCAL_ONLY')
        with self.assertRaises(S.ScoutError): J.OfflineRun.create(self.base / 'forbidden', prospective)


if __name__ == '__main__': unittest.main()
