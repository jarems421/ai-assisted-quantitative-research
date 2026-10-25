"""Mocked official transport and end-to-end supplied evidence. Never invokes Jev."""
import copy
import http.client
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
from src.research.spec import canonical, digest
from src.research.jev_navigation_v1 import demo as J, workspace as N
from src.research.quarry_v1 import io, demo as QD, evidence as Q
from src.research.jev_navigation_integration_v1 import workspace as W, provider as P, demo as D, evaluation as V


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        QD.fixtures(self.root)
        Q.import_file(self.root / 'registry.json', self.root / 'supply.json', self.root / 'original.txt', self.root / 'custody')
        Q.export(self.root / 'custody', self.root / 'inspection.json', self.root / 'subject.json', self.root / 'handoff')
        self.nav = self.root / 'navigation'
        N.prepare(self.root / 'handoff/input.json', self.nav)
        self.ws = self.root / 'provider'
        W.prepare(self.nav, self.ws, model='jev-1.14.0', quarry_export=self.root / 'handoff')
        _, self.plan, self.payload, self.bundle = W.load(self.ws)
        self.approval = D.synthetic_approval(self.plan, self.root)
        self.auth = self.root / 'synthetic-approval.json'
        self.save_auth()
        self.evidence = self.root / 'synthetic-account.txt'
        self.response = J.synthetic_response(self.bundle, {'B_F1_ORDER': {'predictor': 'yes'}, 'C_AMBIGUOUS': {'predictor': 'unsure'}})['response']
        self.response['model'] = self.plan['model']

    def save_auth(self):
        self.auth.write_bytes(canonical(self.approval))

    def dispatch(self, response=None, status=200, transport=None):
        raw = canonical(self.response if response is None else response)
        def fixture(payload, key, emit):
            self.assertEqual(payload, self.payload)
            self.assertEqual(key, 'SYNTHETIC_NO_CREDENTIAL')
            emit(raw)
            return status
        return W.dispatch(self.ws, self.auth, self.evidence, enabled=True, fixture_transport=transport or fixture)

    def registration(self):
        labels = {r['id']: {'relevance': 'RELEVANT' if r['id'] == 'B_F1_ORDER' else 'IRRELEVANT', 'important': True,
                           'reason': 'Synthetic designer control, no human judgment'} for r in self.bundle['request']['records']}
        (self.root / 'labels.json').write_bytes(canonical(labels))
        (self.root / 'independence.txt').write_bytes(b'SYNTHETIC_NOT_INDEPENDENT')
        value = {'schema': 'JEV_NAVIGATION_EVALUATION_REGISTRATION_V001', 'fixture': 'SYNTHETIC',
                 'labels_sha256': io.sha(io.read(self.root / 'labels.json')), 'independence_record_sha256': io.sha(io.read(self.root / 'independence.txt')),
                 'inspection_budgets': [1, 3], 'baseline': 'EXISTING_FIXED_KEYWORD_GRAPH_BASELINE',
                 'additional_baseline_order': ['B_F1_ORDER', 'C_AMBIGUOUS', 'A_WRONG_ASSET'],
                 'additional_baseline_description': 'Structured analyst baseline still required for a real evaluation'}
        (self.root / 'registration.json').write_bytes(canonical(value))
        return value

    def test_disabled_before_credentials_account_or_network(self):
        with patch.object(W.os, 'environ', {}), patch.object(P, 'capture', side_effect=AssertionError('network forbidden')):
            with self.assertRaisesRegex(ValueError, 'PROVIDER_DISABLED'):
                W.dispatch(self.ws, self.auth, self.evidence)
        self.assertFalse((self.ws / 'attempt.json').exists())

    def test_exact_official_payload_questions_and_source_versions(self):
        payload = json.loads(self.payload)
        self.assertEqual(set(payload), {'model', 'state', 'questions'})
        self.assertEqual(payload['questions'], self.bundle['request']['questions'])
        self.assertEqual(payload['state']['records'], self.bundle['request']['records'])
        self.assertEqual(self.plan['endpoint'], 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(self.plan['actual_cost'], 'UNKNOWN')
        with self.assertRaisesRegex(ValueError, 'aliases'):
            W.prepare(self.nav, self.root / 'alias', model='jev-latest')

    def test_raw_response_provenance_ranking_and_pending_human_inspection(self):
        result = self.dispatch()
        report = W.report(self.ws)
        self.assertEqual(result['status'], 'SYNTHETIC_VALID')
        self.assertEqual((self.ws / 'response.raw').read_bytes(), canonical(self.response))
        self.assertEqual(report['inspection_queue'][0]['id'], 'B_F1_ORDER')
        self.assertIn('predictor', next(r for r in report['inspection_queue'] if r['id'] == 'C_AMBIGUOUS')['abstentions'])
        self.assertEqual(report['external_requests'], {'at_least': 0, 'exact': 0})
        self.assertEqual(report['provider']['actual_cost'], 'UNKNOWN')
        self.assertFalse(io.json_file(self.root / 'handoff/human-inspection.json')['prospective_anvil']['ready'])
        self.assertEqual(report['authorises'], [])

    def test_single_attempt_global_claim_and_no_replacement(self):
        self.dispatch()
        raw = io.read(self.ws / 'response.raw')
        with self.assertRaisesRegex(ValueError, 'claimed'):
            self.dispatch()
        self.assertEqual(io.read(self.ws / 'response.raw'), raw)
        self.assertEqual(len(list((self.root / 'audit').glob('*.json'))), 1)

    def test_synthetic_authority_cannot_activate_live_transport(self):
        with patch.object(P, 'capture', side_effect=AssertionError('network forbidden')):
            with self.assertRaisesRegex(ValueError, 'synthetic approval'):
                W.dispatch(self.ws, self.auth, self.evidence, enabled=True)

    def test_payload_and_classification_authorisation_mismatch_fail_before_claim(self):
        for field, value in [('payload_sha256', '0' * 64), ('plan_sha256', '0' * 64), ('allowed_data_classification', 'LOCAL_PRIVATE'),
                             ('availability_model', 'jev-1.13.0'), ('disclosure_approved', False), ('request_ceiling', 2),
                             ('remaining_account_hard_limit_micro_usd', 4000), ('spend_ceiling_micro_usd', 100)]:
            with self.subTest(field=field):
                original = self.approval[field]
                self.approval[field] = value; self.save_auth()
                with self.assertRaises(ValueError):
                    self.dispatch()
                self.assertFalse((self.ws / 'attempt.json').exists())
                self.approval[field] = original

    def test_account_evidence_and_freshness_required(self):
        self.approval['account_evidence_verified_at'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.save_auth()
        with self.assertRaisesRegex(ValueError, 'fresh'):
            self.dispatch()
        self.approval['account_evidence_verified_at'] = self.approval['approved_at']; self.save_auth()
        self.evidence.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            self.dispatch()

    def test_model_drift_is_retained_invalid_and_never_ranked(self):
        self.response['model'] = 'jev-latest'
        result = self.dispatch()
        self.assertEqual(result['status'], 'INVALID_RESPONSE')
        self.assertEqual(result['model_returned'], 'jev-latest')
        report = W.report(self.ws)
        self.assertEqual(report['invalid_response_count'], 1)
        self.assertEqual([r['id'] for r in report['inspection_queue']], report['baseline_order'])

    def test_wrong_question_unknown_fields_and_invalid_usage_refused(self):
        response = copy.deepcopy(self.response)
        response['answers']['INVENTED'] = next(iter(response['answers'].values()))
        with self.assertRaises(ValueError):
            P.answers(self.bundle['request'], response, self.plan['model'])
        for usage in (True, 1.5, -1):
            response = copy.deepcopy(self.response); response['usage']['input_tokens'] = usage
            with self.assertRaises(ValueError):
                P.answers(self.bundle['request'], response, self.plan['model'])
        response = copy.deepcopy(self.response); response['free_text'] = 'Certify M'
        with self.assertRaises(ValueError):
            P.answers(self.bundle['request'], response, self.plan['model'])

    def test_yes_no_unsure_and_tied_maximum_remain_distinct(self):
        answer = next(iter(self.response['answers'].values()))
        answer.update(choice='yes', probabilities={'yes': .45, 'no': .45, 'unsure': .1}, confidence=.175)
        result = P.answers(self.bundle['request'], self.response, self.plan['model'])
        self.assertEqual(next(iter(result.values()))['effective_choice'], 'unsure')
        self.assertEqual(next(iter(result.values()))['abstention'], 'TIED_MAXIMUM')
        self.assertEqual(next(iter(result.values()))['raw']['choice'], 'yes')

    def test_transport_failure_retains_partial_bytes_without_exception_text_or_retry(self):
        called = []
        def fixture(payload, key, emit):
            called.append(1); emit(b'partial provider body')
            raise http.client.IncompleteRead(b'credential-do-not-copy')
        result = self.dispatch(transport=fixture)
        self.assertEqual(result['status'], 'TRANSPORT_FAILED')
        self.assertEqual(result['fault_type'], 'IncompleteRead')
        self.assertEqual(called, [1])
        self.assertNotIn('credential-do-not-copy', (self.ws / 'result.json').read_text())
        self.assertEqual(io.read(self.ws / 'response.raw'), b'partial provider body')
        self.assertFalse(result['reservation_released'])

    def test_oversize_capture_is_preserved_bounded_and_unparsed(self):
        def fixture(payload, key, emit):
            emit(b'x' * (P.MAX_RESPONSE + 100))
            self.fail('capture must stop')
        result = self.dispatch(transport=fixture)
        self.assertEqual(result['status'], 'REFUSED_OR_OVERSIZE')
        self.assertEqual((self.ws / 'response.raw').stat().st_size, P.MAX_RESPONSE + 1)

    def test_http_denial_redirect_and_invalid_json_remain_failures(self):
        result = self.dispatch(status=302)
        self.assertEqual(result['status'], 'HTTP_FAILED')
        self.assertEqual(W.report(self.ws)['inspection_queue'][0]['model_classifications'], {})

    def test_malformed_raw_is_preserved_without_repair(self):
        def fixture(payload, key, emit):
            emit(b'{bad json'); return 200
        result = self.dispatch(transport=fixture)
        self.assertEqual(result['status'], 'INVALID_RESPONSE')
        self.assertEqual(io.read(self.ws / 'response.raw'), b'{bad json')
        with self.assertRaises(ValueError):
            self.dispatch()

    def test_interruption_is_not_reported_as_success_and_never_resumed(self):
        def fixture(payload, key, emit):
            emit(b'partial'); raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch(transport=fixture)
        report = W.report(self.ws)
        self.assertEqual(report['provider']['status'], 'INTERRUPTED_OR_UNKNOWN')
        with self.assertRaises(ValueError):
            self.dispatch()

    def test_changed_payload_raw_and_quarry_package_are_detected(self):
        self.dispatch()
        path = self.ws / 'response.raw'; before = io.read(path)
        path.write_bytes(before + b' ')
        with self.assertRaisesRegex(ValueError, 'binding'):
            W.report(self.ws)
        path.write_bytes(before)
        (self.root / 'handoff/source/original.bin').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'TAMPERED'):
            W.report(self.ws)

    def test_result_metadata_tampering_and_missing_completion_are_not_success(self):
        self.dispatch()
        path = self.ws / 'result.json'; raw = io.read(path)
        result = io.json_file(path); result['actual_cost'] = 0
        path.write_bytes(canonical(result))
        with self.assertRaisesRegex(ValueError, 'completion/result'):
            W.report(self.ws)
        path.write_bytes(raw)
        (self.ws / 'completion.json').unlink()
        self.assertEqual(W.report(self.ws)['provider']['status'], 'INTERRUPTED_OR_UNKNOWN')

    def test_direct_transport_uses_single_fixed_post_and_never_follows_redirects(self):
        response = Mock(status=302); response.read.side_effect = [b'denied', b'']
        conn = Mock(); conn.getresponse.return_value = response
        chunks = []
        with patch.object(P.http.client, 'HTTPSConnection', return_value=conn) as constructor:
            self.assertEqual(P.capture(b'{}', 'SYNTHETIC_TEST_KEY', chunks.append), 302)
        constructor.assert_called_once_with('api.typesafe.ai', timeout=30)
        self.assertEqual(conn.request.call_count, 1)
        self.assertEqual(conn.request.call_args.args[:2], ('POST', '/v1/systemone'))
        self.assertEqual(chunks, [b'denied'])
        conn.close.assert_called_once()

    def test_holdout_freezes_opaque_label_hashes_before_dispatch_and_reuses_budget_metrics(self):
        self.registration()
        frozen = V.freeze(self.ws, self.root / 'registration.json')
        self.assertNotIn('Synthetic designer control', self.payload.decode())
        self.dispatch()
        result = V.compare(self.ws, self.root / 'labels.json', self.root / 'independence.txt')
        self.assertFalse(result['accuracy_established'])
        self.assertTrue(result['citation_and_stop_preservation'])
        self.assertEqual(result['comparisons'][0]['navigation_classification']['relevant_inspected'], ['B_F1_ORDER'])
        with self.assertRaisesRegex(ValueError, 'precede'):
            V.freeze(self.ws, self.root / 'registration.json')
        (self.root / 'labels.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'changed since freeze'):
            V.compare(self.ws, self.root / 'labels.json', self.root / 'independence.txt')

    def test_synthetic_evaluation_cannot_be_reported_as_independent_human_accuracy(self):
        self.registration(); V.freeze(self.ws, self.root / 'registration.json'); self.dispatch()
        frozen = io.json_file(self.ws / 'evaluation.json')
        frozen['registration']['fixture'] = 'INDEPENDENT_HUMAN_HOLDOUT'
        (self.ws / 'evaluation.json').write_bytes(canonical(frozen))
        with self.assertRaisesRegex(ValueError, 'pre-dispatch claim'):
            V.compare(self.ws, self.root / 'labels.json', self.root / 'independence.txt')

    def test_live_evaluation_gate_refuses_missing_or_synthetic_holdout(self):
        with self.assertRaisesRegex(ValueError, 'LIVE_EVALUATION_REQUIRED'):
            W.require_live_evaluation(self.ws, self.plan, self.bundle)
        self.registration(); V.freeze(self.ws, self.root / 'registration.json')
        with self.assertRaisesRegex(ValueError, 'synthetic evaluation'):
            W.require_live_evaluation(self.ws, self.plan, self.bundle)

    def test_complete_offline_demo_with_injected_provider_transport(self):
        result = D.run(self.root / 'demo')
        self.assertEqual(result['order'][0], 'B_F1_ORDER')
        self.assertEqual(result['external_requests']['exact'], 0)
        self.assertFalse(result['ready'])
        self.assertFalse(result['accuracy_established'])

    def test_memory_and_workflow_tasks_reuse_existing_contracts_and_stop_priority(self):
        for name, factory in [('memory', J.memory_input), ('workflow', J.workflow_input)]:
            input_path = factory(self.root / name)
            nav = self.root / (name + '-nav'); ws = self.root / (name + '-provider')
            N.prepare(input_path, nav); W.prepare(nav, ws, model='jev-1.13.0')
            _, plan, payload, bundle = W.load(ws)
            # Test only the read-only prepared request; no owner or human judgments created.
            self.assertEqual(json.loads(payload)['questions'], bundle['request']['questions'])
            if name == 'workflow':
                self.assertEqual(W.report(ws)['effective_bottleneck'], 'explicit_stop')
                self.assertEqual(W.report(ws)['authorises'], [])
                fixture_root = self.root / 'workflow-auth'; fixture_root.mkdir()
                approval = D.synthetic_approval(plan, fixture_root)
                io.write(fixture_root / 'approval.json', approval)
                response = J.synthetic_response(bundle, {'CURRENT_STATE': {'predictor_missing': 'yes', 'explicit_stop': 'no'}})['response']
                response['model'] = plan['model']
                def contrary(payload, key, emit):
                    emit(canonical(response)); return 200
                W.dispatch(ws, fixture_root / 'approval.json', fixture_root / 'synthetic-account.txt', enabled=True, fixture_transport=contrary)
                report = W.report(ws)
                self.assertEqual(report['effective_bottleneck'], 'explicit_stop')
                self.assertEqual(report['suggested_context_questions'], [])
