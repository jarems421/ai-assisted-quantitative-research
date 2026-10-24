"""Research OS pipeline V001: offline end-to-end. Fake Claude CLI (real 2.1.302 vocabulary), fake Codex JSONL, fake
Gemini transport and SYNTHETIC FIXTURE critic answers; the real archive, importer, Layer A, critic importer, policy
and report run unchanged. No process, network, credential, real account directory or paid call is used."""
import copy
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

from src.research.opportunity_scout import schema as S, v004_package
from src.research.opportunity_scout.automation_v001 import pipeline as R, providers as V
from src.research.opportunity_scout.automation_v001.__main__ import main
from src.research.opportunity_scout.critic_v1 import benchmark as B, packages as P, rubric as K
from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout.v004_r3 import package as R3
from tests.opportunity_scout import test_critic_providers_v001 as PV, test_exploratory_runner_v001 as T

IDEA2 = copy.deepcopy(T.IDEA)
IDEA2.update(title='Fictional cold-chain insurance repricing may shift refrigerated storage demand', sector='Fictional cold-chain logistics',
             economic_role='INSURER')
IDEA2['mechanism'] = {**IDEA2['mechanism'], 'family': 'LIABILITY_TRANSFER', 'trigger': 'A fictional insurer reprices spoilage cover for refrigerated warehouses.',
                      'consequence': 'Fictional warehouse operators shift towards contracted cold storage capacity.'}
TEXT2 = json.dumps({'ideas': [T.IDEA, IDEA2]})
KEY = 'AIzaFICTIONAL-test-key-never-sent'
PRICES = PV.PRICES


class Base(T.Base):
    def setUp(self):
        super().setUp()
        self.codex = self.base / 'bin' / 'codex.exe'; self.codex.write_bytes(b'fictional codex bytes')
        self.specs, self.codex_calls, self.gemini_calls, self.admin_calls, self.admin_login = {}, [], [], [], 'Logged in using ChatGPT\n'
        self.codex_mode, self.gemini_mode = {}, {}
        self.scientific = {'provider': 'CODEX_CLI', 'family': 'openai', 'model': 'gpt-6-sol', 'effort': 'xhigh',
                           'accept_requested_identity': True, 'executable': str(self.codex)}
        self.economic = {'provider': 'GEMINI_API', 'family': 'google', 'model': 'gemini-4-argon', 'prices': PRICES,
                         'api_key_env': 'GEMINI_API_KEY', 'max_output_tokens': 8192, 'thinking_level': 'high'}
        self.host.runner = T.FakeCLI(self, model_stream=lambda s: T.stream(s, TEXT2))
        self.pipe = R.Host(generation=self.host, codex_runner=self.fake_codex, codex_admin=self.fake_admin, transport=self.fake_gemini,
                           environ={'PATH': '/bin', 'GEMINI_API_KEY': KEY, 'OPENAI_API_KEY': 'sk-fictional-must-not-pass'})

    # ---- fakes --------------------------------------------------------------------------------------------
    def request_for(self, prompt):
        ws = P.Workspace(R.workspace_path(self.store))
        return next(r for r in ws.requests() if (ws.path / 'requests' / f'{r["request_id"]}.md').read_bytes() == prompt)

    def answer(self, request):
        idea = P.Workspace(R.workspace_path(self.store)).manifest()['subjects'][request['subject_key']]['idea_id']
        return B.answer(request['critic'], request, self.specs.get((request['critic'], idea), {}))

    def fake_admin(self, exe, env, args):
        self.admin_calls.append(args)
        return {'--version': 'codex-cli 0.164.0-alpha.11.1\n', 'login': self.admin_login, 'exec': ' '.join(V.CODEX_FLAGS)}[args[0]]

    def fake_codex(self, args, *, input, stdout, stderr, limit, timeout, cwd, env, shell, on_start):
        self.codex_calls.append({'args': args, 'env': env, 'prompt': input})
        on_start(4321)
        mode = self.codex_mode
        if mode.get('crash'):raise KeyboardInterrupt('fictional crash after start')
        reply = self.answer(self.request_for(input)).decode('utf-8')
        items = mode.get('items') or [{'id': 'r', 'type': 'reasoning', 'text': 'fictional'}, {'id': 'm', 'type': 'agent_message', 'text': reply}]
        stdout.write(PV.codex_stream(items=items, model=mode.get('model'), usage=mode.get('usage')))
        if mode.get('timeout'):raise subprocess.TimeoutExpired(args, timeout)
        return subprocess.CompletedProcess(args, 0, None, None)

    def fake_gemini(self, url, headers, body, timeout):
        self.gemini_calls.append({'url': url, 'headers': dict(headers), 'body': json.loads(body)})
        mode = self.gemini_mode
        if mode.get('error'):raise mode['error']
        prompt = self.gemini_calls[-1]['body']['contents'][0]['parts'][0]['text'].encode('utf-8')
        text = mode.get('text') or self.answer(self.request_for(prompt)).decode('utf-8')
        return mode.get('status', 200), PV.gemini_body(text=text, model=mode.get('model', 'gemini-4-argon-001'))

    # ---- helpers ------------------------------------------------------------------------------------------
    def planned(self, **overrides):
        args = dict(title='Fixture pipeline run', scientific=self.scientific, economic=self.economic, spend_cap_usd=1.0,
                    codex_home=str(self.base / 'codex-home'), host=self.pipe,
                    generator=dict(model=T.MODEL, count=2, effort='low', max_output_tokens_per_request=16000, timeout_seconds=300,
                                   executable=str(self.exe)))
        args.update(overrides)
        return R.plan(self.store, **args)

    def authorise(self, result, **changes):
        t = json.loads(Path(result['authorisation_template']).read_text(encoding='utf-8'))
        gen = {**t['generation'], 'allowed_subscription_types': ['max'], 'hosted_transmission_approved': True,
               'owner': 'Fixture Owner', 'approved_at': '2026-10-24T09:00:00+01:00', **changes.pop('generation', {})}
        value = {**t, 'generation': gen, 'hosted_transmission_approved': True, 'gemini_prepaid_auto_reload_disabled': True,
                 'owner': 'Fixture Owner', 'approved_at': '2026-10-24T09:00:00+01:00', **changes}
        path = self.base / f'pipeline-auth-{len(list(self.base.glob("pipeline-auth-*")))}.json'
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def execute(self, **plan_overrides):
        result = self.planned(**plan_overrides)
        return R.run(self.store, self.authorise(result), host=self.pipe)

    def report(self):return R.build(self.store)

    def critic(self, rep, idea, critic):
        return next(s for s in rep['subjects'].values() if s['idea_id'] == idea)['critics'][critic]

    def ideas(self):return list(Archive(self.store).load().cards)


class EndToEndTests(Base):
    def test_one_authorised_run_generates_critiques_recommends_and_reports(self):
        receipt = self.execute()
        self.assertEqual((receipt['outcome'], receipt['adversarial_dispatched'], receipt['retried']), ('COMPLETE', 0, False))
        self.assertEqual(set(receipt['stages'].values()) - {'NOT_RECORDED'}, {'VALID', 'COMPLETE'})
        self.assertEqual((len(self.ideas()), len(self.codex_calls), len(self.gemini_calls)), (2, 2, 2))  # one dispatch per request
        rep = self.report()
        self.assertEqual(len(rep['subjects']), 2)
        for row in rep['subjects'].values():
            self.assertEqual({c['status'] for c in row['critics'].values()}, {'VALID'})
            self.assertEqual(row['recommendation']['classification'], 'READY_CANDIDATE')
            self.assertEqual(row['adversarial'], 'NOT_RECOMMENDED')
        md = (self.store / 'exports/pipeline-report.md').read_text(encoding='utf-8')
        self.assertIn('Advisory AI criticism only', md); self.assertIn(IDEA2['title'], md)
        routes = {c['route'] for c in rep['cards'].values()}
        self.assertEqual(routes, {'INCUBATE'})  # AI recommendations never change Scout routing

    def test_each_critic_receives_only_its_own_frozen_blinded_request(self):
        self.execute()
        ws = P.Workspace(R.workspace_path(self.store))
        frozen = {(ws.path / 'requests' / f'{r["request_id"]}.md').read_bytes() for r in ws.requests()}
        sent = [c['prompt'] for c in self.codex_calls] + [c['body']['contents'][0]['parts'][0]['text'].encode('utf-8') for c in self.gemini_calls]
        self.assertEqual(sorted(sent), sorted(frozen))  # each frozen request exactly once, byte-identical
        for prompt in sent:  # the untrusted input block carries no generator, lane, routing or critic identity
            data = prompt.split(b'<<<UNTRUSTED_INPUT ', 1)[1].split(b'<<<END_UNTRUSTED_INPUT', 1)[0].lower()
            for word in (b'claude', b'opus', b'incubate', b'forge', b'gpt-6', b'gemini', b'provenance', b'layer_a', b'att-0001'):
                self.assertNotIn(word, data)
        for call in self.codex_calls:
            self.assertNotIn('OPENAI_API_KEY', call['env']); self.assertIn('web_search="disabled"', call['args'])
        for call in self.gemini_calls:self.assertNotIn('tools', call['body'])

    def test_disagreement_is_recommended_for_revision_and_adversarial_stays_pending(self):
        result = self.planned()
        # Script the fixture critics once ideas exist: they are created by the run itself.
        original = self.answer
        def scripted(request):
            idea = P.Workspace(R.workspace_path(self.store)).manifest()['subjects'][request['subject_key']]['idea_id']
            first = sorted(Archive(self.store).load().cards)[0]
            if idea == first:
                self.specs[('SCIENTIFIC', idea)] = {'mechanism_coherence': B.fail('CONFOUNDED', '/card/predictor/quantity')}
                self.specs[('ECONOMIC', idea)] = {'mechanism_coherence': 'PASS'}
            return original(request)
        self.answer = scripted
        R.run(self.store, self.authorise(result), host=self.pipe)
        rep = self.report(); first = sorted(self.ideas())[0]
        row = next(s for s in rep['subjects'].values() if s['idea_id'] == first)
        self.assertEqual(row['recommendation']['classification'], 'REVISION_REQUIRED')
        self.assertEqual((row['adversarial'], row['recommendation']['adversarial_recommended']), ('PENDING_APPROVAL', 'CRITIC_DISAGREEMENT'))
        self.assertEqual(row['recommendation']['disagreements'][0]['judgments'], {'ECONOMIC': 'PASS', 'SCIENTIFIC': 'FAIL'})
        stage = json.loads((self.store / 'exports/pipeline-stage-RECOMMENDATION.json').read_text(encoding='utf-8'))
        self.assertTrue(all(v['status'] == 'PENDING_APPROVAL' for v in stage['adversarial'].values()))
        self.assertEqual(len(self.codex_calls) + len(self.gemini_calls), 4)  # no adversarial dispatch

    def test_invalid_reply_is_kept_and_provider_fault_is_never_imported(self):
        self.gemini_mode['text'] = 'No fenced block at all.'
        self.codex_mode['items'] = [{'id': 'm1', 'type': 'agent_message', 'text': 'one'}, {'id': 'm2', 'type': 'agent_message', 'text': 'two'}]
        receipt = self.execute()
        self.assertEqual(receipt['outcome'], 'INCOMPLETE_CRITICS')
        rep = self.report()
        for idea in self.ideas():
            econ, sci = self.critic(rep, idea, 'ECONOMIC'), self.critic(rep, idea, 'SCIENTIFIC')
            self.assertEqual((econ['outcome'], econ['status']), ('IMPORTED', 'INVALID'))  # kept, never repaired
            self.assertEqual((sci['outcome'], sci['status']), ('PROVIDER_FAULT', None))
            self.assertIn('NOT_EXACTLY_ONE_AGENT_MESSAGE', sci['faults'])
        self.assertEqual({s['recommendation']['classification'] for s in rep['subjects'].values()}, {'ESCALATE'})
        self.assertEqual(len(self.codex_calls) + len(self.gemini_calls), 4)  # no second attempt despite the contract allowing one

    def test_model_fallback_is_a_fault_for_both_providers(self):
        self.codex_mode['model'] = 'gpt-5.5'; self.gemini_mode['model'] = 'gemini-3.8-flash'
        self.execute(); rep = self.report()
        for idea in self.ideas():
            self.assertIn('MODEL_MISMATCH', self.critic(rep, idea, 'SCIENTIFIC')['faults'])
            self.assertIn('MODEL_MISMATCH_OR_UNKNOWN', self.critic(rep, idea, 'ECONOMIC')['faults'])

    def test_unobserved_identity_and_unknown_usage_are_not_promoted(self):
        self.scientific = {**self.scientific, 'accept_requested_identity': False}
        self.execute(); rep = self.report()
        for idea in self.ideas():self.assertIn('MODEL_IDENTITY_NOT_OBSERVED', self.critic(rep, idea, 'SCIENTIFIC')['faults'])
        self.tearDown(); self.setUp()
        self.codex_mode['usage'] = {}
        self.execute(); rep = self.report()
        for idea in self.ideas():self.assertIn('USAGE_UNKNOWN', self.critic(rep, idea, 'SCIENTIFIC')['faults'])


class BoundaryTests(Base):
    def test_generator_family_self_review_and_unsupported_routes_are_refused_at_plan(self):
        for role in ({**self.scientific, 'family': 'anthropic'}, {**self.scientific, 'model': 'claude-opus-5-5'},
                     {'provider': 'BROWSER_AUTOMATION', 'family': 'google'}):
            with self.subTest(role=role), self.assertRaises(S.ScoutError):self.planned(scientific=role)
        self.assertFalse((self.store / 'exports/pipeline-plan.json').exists())

    def test_api_key_login_and_unattested_billing_stop_before_dispatch(self):
        self.admin_login = 'Logged in using an API key - sk-...\n'
        self.execute(); rep = self.report()
        for idea in self.ideas():self.assertTrue(self.critic(rep, idea, 'SCIENTIFIC')['faults'][0].startswith('PREFLIGHT_STOP:CODEX_NOT_CHATGPT'))
        self.assertEqual(self.codex_calls, [])
        self.tearDown(); self.setUp()
        result = self.planned()
        with self.assertRaises(S.ScoutError):R.run(self.store, self.authorise(result, gemini_prepaid_auto_reload_disabled=False), host=self.pipe)
        self.tearDown(); self.setUp()
        self.execute(spend_cap_usd=0.01); rep = self.report()  # below the worst-case bound of one request
        for idea in self.ideas():self.assertEqual(self.critic(rep, idea, 'ECONOMIC')['faults'], ['SPEND_CAP_WOULD_BE_EXCEEDED'])
        self.assertEqual(self.gemini_calls, [])

    def test_unavailable_provider_and_authentication_failure_are_reported_never_substituted(self):
        receipt = self.execute(economic={'provider': 'ANTIGRAVITY_CONSUMER', 'family': 'google'})
        rep = self.report()
        self.assertEqual(receipt['outcome'], 'INCOMPLETE_CRITICS')
        for idea in self.ideas():self.assertEqual(self.critic(rep, idea, 'ECONOMIC')['outcome'], V.UNAVAILABLE)
        self.assertEqual(self.gemini_calls, [])  # nothing substituted for the unavailable role
        self.tearDown(); self.setUp()
        self.gemini_mode['status'] = 401; self.gemini_mode['text'] = 'unauthorised'
        self.execute(); rep = self.report()
        for idea in self.ideas():self.assertIn('HTTP_401', self.critic(rep, idea, 'ECONOMIC')['faults'])
        self.tearDown(); self.setUp()
        self.pipe.environ.pop('GEMINI_API_KEY')
        self.execute(); rep = self.report()
        for idea in self.ideas():self.assertEqual(self.critic(rep, idea, 'ECONOMIC')['faults'], ['API_KEY_ABSENT'])

    def test_timeout_and_transport_failure_are_final(self):
        self.codex_mode['timeout'] = True; self.gemini_mode['error'] = OSError('fictional connection reset')
        self.execute(); rep = self.report()
        for idea in self.ideas():
            self.assertIn('TIMEOUT', self.critic(rep, idea, 'SCIENTIFIC')['faults'])
            self.assertIn('TRANSPORT_FAILED:OSError', self.critic(rep, idea, 'ECONOMIC')['faults'])
        self.assertEqual(len(self.codex_calls) + len(self.gemini_calls), 4)

    def test_crash_leaves_a_truthful_partial_report_and_is_never_redispatched(self):
        self.codex_mode['crash'] = True
        result = self.planned(); auth = self.authorise(result)
        with self.assertRaises(KeyboardInterrupt):R.run(self.store, auth, host=self.pipe)
        self.assertEqual(len(self.codex_calls), 1)
        st = R.status(self.store)
        self.assertEqual((st['interrupted'], st['outcome'], st['critic_claims'], st['critic_records']), (True, 'INTERRUPTED', 1, 0))
        with self.assertRaises(S.ScoutError):R.run(self.store, auth, host=self.pipe)  # duplicate run refused
        self.assertEqual((len(self.codex_calls), len(self.gemini_calls)), (1, 0))  # no second dispatch
        rep = self.report()
        self.assertEqual(rep['outcome'], 'INTERRUPTED_OR_NOT_FINISHED')
        outcomes = sorted(c['outcome'] for s in rep['subjects'].values() for c in s['critics'].values())
        self.assertEqual(outcomes, ['CLAIMED_OUTCOME_UNKNOWN', 'NOT_DISPATCHED', 'NOT_DISPATCHED', 'NOT_DISPATCHED'])
        self.assertIn('INTERRUPTED_OR_NOT_FINISHED', R.markdown(rep))

    def test_authorisation_must_bind_the_exact_plan_and_one_owner(self):
        result = self.planned()
        cases = {'template': None, 'assistant owner': {'owner': 'GPT helper'}, 'other generation owner': {'generation': {'owner': 'Someone Else'}},
                 'adversarial': {'adversarial_permitted': True}, 'two attempts': {'attempts_per_request': 2},
                 'other model': {'roles': {**json.loads(Path(result['authorisation_template']).read_text(encoding='utf-8'))['roles'],
                                           'SCIENTIFIC': {**self.scientific, 'model': 'gpt-6-astra'}}}}
        for name, change in cases.items():
            path = Path(result['authorisation_template']) if change is None else self.authorise(result, **change)
            with self.subTest(case=name), self.assertRaises(S.ScoutError):R.run(self.store, path, host=self.pipe)
        self.assertFalse((self.store / 'exports/pipeline-claim.json').exists())
        self.assertEqual((self.host.runner.calls, self.codex_calls, self.gemini_calls), ([], [], []))

    def test_plan_status_and_report_start_nothing_and_frozen_boundaries_hold(self):
        def forbid(*a, **k):raise AssertionError('no process or request during plan/status/report')
        self.pipe = R.Host(generation=self.host, codex_runner=forbid, codex_admin=forbid, transport=forbid, environ={})
        self.host.runner = forbid
        self.planned(); R.status(self.store); R.markdown(R.build(self.store))
        self.assertEqual(main(['status', str(self.store)]), 0)
        for closure in (v004_package.implementation(), R3.implementation()):self.assertFalse([p for p in closure if 'automation_v001' in p])
        self.assertEqual(K.resource_manifest()['schema'], K.resource_manifest()['schema'])  # frozen critic texts load unchanged

    def test_full_offline_run_uses_no_socket_process_or_written_secret(self):
        def deny(*a, **k):raise AssertionError('network or process use in an offline test')
        with patch.object(socket, 'socket', deny), patch.object(subprocess, 'Popen', deny):
            self.assertEqual(self.execute()['outcome'], 'COMPLETE')
        for f in list((self.store / 'exports').iterdir()) + list(R.workspace_path(self.store).rglob('*')):
            if f.is_file():self.assertNotIn(KEY.encode(), f.read_bytes(), f.name)
        self.assertEqual({c['headers']['x-goog-api-key'] for c in self.gemini_calls}, {KEY})
