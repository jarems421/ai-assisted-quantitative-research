"""Research OS pipeline V001: offline end-to-end. Fake Claude CLI (real 2.1.302 vocabulary), fake Codex JSONL, fake
Gemini transport and SYNTHETIC FIXTURE critic answers; the real archive, importer, Layer A, critic importer, policy
and report run unchanged. No process, network, credential, real account directory or paid call is used."""
import copy
import email.message
import hashlib
import http.client
import io
import json
from pathlib import Path
import shutil
import socket
import subprocess
import unittest
from unittest.mock import patch

from src.research.opportunity_scout import schema as S, v004_package
from src.research.opportunity_scout.automation_v001 import pipeline as R, providers as V
from src.research.opportunity_scout.automation_v001.__main__ import main
from src.research.opportunity_scout.critic_v1 import benchmark as B, packages as P, rubric as K
from src.research.opportunity_scout.exploratory_v001 import runner as X
from src.research.opportunity_scout.storage import Archive, ROOT
from src.research.opportunity_scout.v004_r3 import package as R3
from tests.opportunity_scout import test_critic_providers_v001 as PV, test_exploratory_runner_v001 as T

IDEA2 = copy.deepcopy(T.IDEA)
IDEA2.update(title='Fictional cold-chain insurance repricing may shift refrigerated storage demand', sector='Fictional cold-chain logistics',
             economic_role='INSURER')
IDEA2['mechanism'] = {**IDEA2['mechanism'], 'family': 'LIABILITY_TRANSFER', 'trigger': 'A fictional insurer reprices spoilage cover for refrigerated warehouses.',
                      'consequence': 'Fictional warehouse operators shift towards contracted cold storage capacity.'}
TEXT2 = json.dumps({'ideas': [T.IDEA, IDEA2]})
KEY = 'AIzaFICTIONAL-test-key-never-sent'
SECRET = 'FICTIONAL-PARTIAL-RESPONSE-BODY-never-persisted'
PRICES = PV.PRICES


class Base(T.Base):
    def setUp(self):
        super().setUp()
        self.codex = self.base / 'bin' / 'codex.exe'; self.codex.write_bytes(b'fictional codex bytes')
        self.specs, self.codex_calls, self.gemini_calls, self.admin_calls, self.admin_login = {}, [], [], [], 'Logged in using ChatGPT\n'
        self.codex_mode, self.gemini_mode, self.admin_mode, self.events = {}, {}, {}, []
        self.scientific = {'provider': 'CODEX_CLI', 'family': 'openai', 'model': 'gpt-6-sol', 'effort': 'xhigh',
                           'accept_requested_identity': True, 'executable': str(self.codex)}
        self.economic = {'provider': 'GEMINI_API', 'family': 'google', 'model': 'gemini-4-argon', 'prices': PRICES,
                         'api_key_env': 'GEMINI_API_KEY', 'max_output_tokens': 8192, 'thinking_level': 'high'}
        self.host.runner = T.FakeCLI(self, model_stream=lambda s: T.stream(s, TEXT2))
        self.pipe = R.Host(generation=self.host, codex_runner=self.fake_codex, transport=self.fake_gemini,
                           environ={'PATH': '/bin', 'GEMINI_API_KEY': KEY, 'OPENAI_API_KEY': 'sk-fictional-must-not-pass'})

    # ---- fakes --------------------------------------------------------------------------------------------
    def request_for(self, prompt):
        ws = P.Workspace(R.workspace_path(self.store))
        return next(r for r in ws.requests() if (ws.path / 'requests' / f'{r["request_id"]}.md').read_bytes() == prompt)

    def answer(self, request):
        idea = P.Workspace(R.workspace_path(self.store)).manifest()['subjects'][request['subject_key']]['idea_id']
        return B.answer(request['critic'], request, self.specs.get((request['critic'], idea), {}))

    def fake_admin(self, args, *, exe, stdout, stderr, limit, timeout, cwd, on_start, input):
        """Administrative commands arrive through the bounded capture path; ``admin_mode`` scripts its stops, keyed by
        command or by (executable, command)."""
        self.admin_calls.append({'args': args, 'exe': exe, 'limit': limit, 'timeout': timeout, 'cwd': cwd, 'input': input})
        self.events.append(('admin', exe))
        mode = self.admin_mode.get((exe, args[0]), self.admin_mode.get(args[0]))
        if mode == 'refused':raise OSError('fictional launch refusal')  # Popen failed: no process exists
        on_start(9876)
        if mode == 'flood':raise X.OutputLimitExceeded(args, limit + 1, 'PROCESS_TREE_STOPPED')
        if mode == 'capture':raise X.CaptureFailed(args, ['stdout:READ:OSError'], 'PROCESS_TREE_STOPPED')
        if mode == 'hang':
            error = subprocess.TimeoutExpired(args, timeout); error.tree = 'PROCESS_TREE_STOPPED'; raise error
        if args[0] == 'login':  # codex 0.164 prints the login result on stderr, with stdout empty
            out, err = {'api_key_login': ('', 'Logged in using an API key - sk-...\n'), 'login_on_stdout': (self.admin_login, ''),
                        'login_conflict': ('Logged in using an API key - sk-...\n', 'Logged in using ChatGPT\n'),
                        'login_duplicate': ('Logged in using ChatGPT', 'Logged in using ChatGPT\n'), 'not_logged_in': ('', 'Not logged in\n'),
                        'login_silent': ('', ''), 'login_extra_line': ('', 'Logged in using ChatGPT\nUsing a custom endpoint\n')}.get(mode, ('', self.admin_login))
            stdout.write(out.encode('utf-8')); stderr.write(err.encode('utf-8'))
        else:stdout.write({'--version': 'codex-cli 0.164.0-alpha.11.1\n', 'exec': ' '.join(V.CODEX_FLAGS)}[args[0]].encode('utf-8'))
        if mode == 'unbounded':stderr.write(b'e' * limit)  # a runner that returned without enforcing: the combined check still stops
        return subprocess.CompletedProcess(args, 3 if mode == 'exit' else 0, None, None)

    def fake_codex(self, args, *, stdout, stderr, limit, timeout, cwd, env, shell, on_start, input=None):
        if '--json' not in args:return self.fake_admin(args[1:], exe=args[0], stdout=stdout, stderr=stderr, limit=limit, timeout=timeout,
                                                        cwd=cwd, on_start=on_start, input=input)
        self.codex_calls.append({'args': args, 'exe': args[0], 'env': env, 'prompt': input})
        self.events.append(('critic', args[0]))
        on_start(4321)
        mode = self.codex_mode
        if mode.get('crash'):raise KeyboardInterrupt('fictional crash after start')
        if mode.get('replace_executable'):Path(args[0]).write_bytes(b'fictional codex bytes, silently updated')
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
        text = mode.get('text') or mode.get('prefix', '') + self.answer(self.request_for(prompt)).decode('utf-8')
        return mode.get('status', 200), PV.gemini_body(text=text, model=mode.get('model', 'gemini-4-argon-001'), usage=mode.get('usage'))

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

    def preflights(self):
        return [json.loads(x.read_text(encoding='utf-8')) for x in sorted((self.store / 'exports').glob('pipeline-codex-preflight-record-*.json'))]

    def persisted(self):
        return [f for f in list((self.store / 'exports').iterdir()) + list(R.workspace_path(self.store).rglob('*')) if f.is_file()]

    def both_codex(self, other=True):
        """The economic critic also on Codex: a second, different executable, or the same one."""
        exe = self.codex
        if other:exe = self.base / 'bin' / 'codex-other.exe'; exe.write_bytes(b'other fictional codex bytes')
        self.economic = {**self.scientific, 'executable': str(exe), 'model': 'gpt-6-astra'}
        return str(exe.resolve())


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
        gemini = [r for r in rep['accounting']['critic_requests'].values() if r['provider'] == V.GEMINI]
        self.assertEqual([r['provider_requests'] for r in gemini], [R.UNSEEN] * 2)  # a failed send is unknown, never zero
        self.assertEqual(rep['accounting']['totals']['provider_requests']['exact'], S.UNKNOWN)

    def test_a_redirect_never_carries_the_key_off_the_documented_host(self):
        origins = PV.FakeOrigins(302)  # the documented host answers with a redirect to attacker.invalid
        self.pipe.transport = lambda url, headers, body, timeout: V.https_transport(url, headers, body, timeout, handlers=(origins,))
        self.execute(); rep = self.report()
        for idea in self.ideas():
            self.assertEqual(self.critic(rep, idea, 'ECONOMIC')['faults'], ['TRANSPORT_FAILED:GEMINI_REDIRECT_REFUSED:HTTP_302'])
        self.assertEqual([h for h, _ in origins.seen], [V.GEMINI_HOST] * 2)  # one request per critic, never a follow-up
        self.assertEqual((rep['spend']['reservations_released_usd'], rep['spend']['cost_estimate_usd_documented_prices']), (0, S.UNKNOWN))

    def test_worst_case_reservations_are_never_released_for_estimates_missing_usage_or_failures(self):
        self.assertEqual(R.reservation_micro_usd(25000, 8192, PRICES), 25000 * 2 + 8192 * 10)
        self.assertEqual(R.reservation_micro_usd(1, 1, {'input_usd_per_million': 0.1, 'output_usd_per_million': 0.2}), 1)  # rounded up
        big = {**self.economic, 'max_output_tokens': 65536}  # worst case about 0.70 USD each; a usage estimate about 0.054 USD
        for name, mode in (('low estimate', {}), ('missing usage', {'usage': {}}), ('transport failure', {'error': OSError('fictional reset')})):
            with self.subTest(case=name):
                self.tearDown(); self.setUp(); self.gemini_mode.update(mode)
                self.execute(economic=big, spend_cap_usd=1.0); rep = self.report()
                self.assertEqual(len(self.gemini_calls), 1)  # after one reservation the second worst case no longer fits
                econ = sorted((self.critic(rep, i, 'ECONOMIC') for i in self.ideas()), key=lambda c: c['faults'] == ['SPEND_CAP_WOULD_BE_EXCEEDED'])
                self.assertEqual(econ[1]['faults'], ['SPEND_CAP_WOULD_BE_EXCEEDED'])
                records = [json.loads(x.read_text(encoding='utf-8')) for x in sorted((self.store / 'exports').glob('pipeline-critic-*.json'))]
                sent = next(r for r in records if r.get('dispatched') is True and r['critic'] == 'ECONOMIC')
                self.assertFalse(sent['reservation_released'])
                self.assertEqual(sent['spend_reserved_worst_case_usd_total'], sent['worst_case_usd'])
                sp = rep['spend']
                self.assertEqual((sp['gemini_requests_reserved'], sp['worst_case_reserved_usd'], sp['reservations_released_usd']),
                                 (1, sent['worst_case_usd'], 0))
                estimate = sp['cost_estimate_usd_documented_prices']
                self.assertEqual(estimate == S.UNKNOWN, name != 'low estimate')
                if name == 'low estimate':self.assertLess(estimate, sent['worst_case_usd'] / 10)  # recorded, never subtracted

    def test_codex_admin_commands_use_the_bounded_capture_and_every_stop_is_named(self):
        self.execute()
        self.assertEqual([c['args'][0] for c in self.admin_calls], ['--version', 'login', 'exec'])
        for c in self.admin_calls:
            self.assertEqual((c['limit'], c['timeout'], c['input']), (X.MAX_ADMIN_BYTES, X.ADMIN_TIMEOUT, None))  # combined, no stdin
            self.assertFalse(Path(c['cwd']).resolve().is_relative_to(ROOT))
        [rec] = self.preflights()
        self.assertEqual((rec['administrative_launches'], rec['processes_started'], rec['auth']), (3, 3, 'CHATGPT_LOGIN'))
        cases = {('--version', 'flood'): ('ADMIN_OUTPUT_TOO_LARGE:--version:PROCESS_TREE_STOPPED', 1, 1),
                 ('login', 'hang'): ('ADMIN_TIMEOUT:login:PROCESS_TREE_STOPPED', 2, 2),
                 ('exec', 'capture'): ('ADMIN_CAPTURE_FAILED:exec:PROCESS_TREE_STOPPED', 3, 3),
                 ('--version', 'unbounded'): ('ADMIN_OUTPUT_TOO_LARGE:--version', 1, 1),
                 ('login', 'exit'): ('ADMIN_COMMAND_FAILED:login', 2, 2),
                 ('--version', 'refused'): ('OSError', 1, 0)}
        for (command, mode), (stop, launches, started) in cases.items():
            with self.subTest(command=command, mode=mode):
                self.tearDown(); self.setUp(); self.admin_mode[command] = mode
                self.execute(); rep = self.report()
                for idea in self.ideas():self.assertEqual(self.critic(rep, idea, 'SCIENTIFIC')['faults'], ['PREFLIGHT_STOP:' + stop])
                self.assertEqual(self.codex_calls, [])  # no critic process after a stopped preflight
                [rec] = self.preflights()
                self.assertEqual((rec['stop'], rec['administrative_launches'], rec['processes_started']), (stop, launches, started))
                self.assertEqual(rep['accounting']['codex_preflight']['administrative_cli_launches'], {'at_least': launches, 'exact': launches})

    def test_codex_login_is_read_from_stderr_and_ambiguous_results_fail_closed(self):
        accepted = {None: 'stderr only (real 0.164 behaviour)', 'login_on_stdout': 'stdout only'}
        refused = {'api_key_login': 'API-key login', 'login_conflict': 'API key on stdout, ChatGPT on stderr',
                   'login_duplicate': 'ChatGPT on both channels', 'not_logged_in': 'not logged in', 'login_silent': 'no output',
                   'login_extra_line': 'an extra line after the login line'}
        for mode, name in {**accepted, **refused}.items():
            with self.subTest(case=name):
                self.tearDown(); self.setUp()
                if mode:self.admin_mode['login'] = mode
                self.execute(); rep = self.report()
                faults = {tuple(self.critic(rep, i, 'SCIENTIFIC')['faults']) for i in self.ideas()}
                if mode in accepted:
                    self.assertEqual((faults, len(self.codex_calls)), ({()}, 2))
                    self.assertEqual(self.preflights()[0]['auth'], 'CHATGPT_LOGIN')
                else:
                    self.assertEqual((faults, self.codex_calls), ({('PREFLIGHT_STOP:CODEX_NOT_CHATGPT_SUBSCRIPTION_LOGIN',)}, []))

    def test_status_and_report_accounting_never_report_zero_without_evidence(self):
        result = self.planned()
        st = R.status(self.store)
        self.assertNotIn('model_calls_made_by_status', st)
        self.assertEqual(list(st['accounting']['totals'].values()), [R.ZERO] * 4)  # nothing claimed: zero is established
        R.run(self.store, self.authorise(result), host=self.pipe)
        acc = R.status(self.store)['accounting']; t = acc['totals']
        gen_admin = acc['generation']['administrative_cli_launches']['exact']
        self.assertEqual(type(gen_admin), int)
        self.assertEqual(t['model_cli_processes_started'], {'at_least': 3, 'exact': 3})  # one Claude CLI, two Codex critic processes
        self.assertEqual(t['administrative_cli_launches'], {'at_least': gen_admin + 3, 'exact': gen_admin + 3})
        self.assertEqual(t['dispatches_attempted'], {'at_least': 5, 'exact': 5})
        self.assertEqual(t['provider_requests'], {'at_least': 5, 'exact': S.UNKNOWN})  # CLI request counts are never visible
        rows = acc['critic_requests'].values()
        self.assertEqual(sorted(json.dumps(r['provider_requests'], sort_keys=True) for r in rows),
                         sorted([json.dumps({'at_least': 1, 'exact': 1}, sort_keys=True)] * 2 + [json.dumps({'at_least': 1, 'exact': S.UNKNOWN}, sort_keys=True)] * 2))
        md = (self.store / 'exports/pipeline-report.md').read_text(encoding='utf-8')
        self.assertIn('| provider requests | 5 | UNKNOWN |', md)

    def test_crash_leaves_a_truthful_partial_report_and_is_never_redispatched(self):
        self.codex_mode['crash'] = True
        result = self.planned(); auth = self.authorise(result)
        with self.assertRaises(KeyboardInterrupt):R.run(self.store, auth, host=self.pipe)
        self.assertEqual(len(self.codex_calls), 1)
        st = R.status(self.store)
        self.assertEqual((st['interrupted'], st['outcome'], st['critic_claims'], st['critic_records']), (True, 'INTERRUPTED', 1, 0))
        t, crashed = st['accounting']['totals'], next(iter(st['accounting']['critic_requests'].values()))
        self.assertEqual(t['model_cli_processes_started'], {'at_least': 2, 'exact': 2})  # the crashed Codex process did start
        self.assertEqual(t['provider_requests']['exact'], S.UNKNOWN)
        self.assertEqual((crashed['outcome_recorded'], crashed['provider_requests']), (False, R.UNSEEN))
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
        self.pipe = R.Host(generation=self.host, codex_runner=forbid, transport=forbid, environ={})
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


class FinalisationTests(Base):
    """Receipt/report V002 (Forge Pilot 001 corrections): finalisation order, execution provenance, credential screen."""
    def fresh(self, name, **cli):
        self.store = self.base / name
        self.host.runner = T.FakeCLI(self, **{'model_stream': lambda s: T.stream(s, TEXT2), **cli})

    def assert_finalised(self, receipt):
        ex = self.store / 'exports'
        saved = json.loads((ex / 'pipeline-report.json').read_text(encoding='utf-8'))
        md = (ex / 'pipeline-report.md').read_text(encoding='utf-8')
        st = R.status(self.store)
        self.assertEqual((receipt['schema'], receipt['stages']['REPORT']), (R.RECEIPT_V, 'COMPLETE'))
        self.assertEqual({saved['outcome'], st['outcome'], R.markdown_outcome(ex / 'pipeline-report.md')}, {receipt['outcome']})
        self.assertEqual(saved['stages'], receipt['stages']); self.assertEqual(st['stages'], receipt['stages'])
        f = st['finalisation']
        self.assertEqual({k: f[k] for k in ('state', 'receipt', 'report_files', 'saved_report_outcome', 'markdown_outcome', 'receipt_outcome', 'consistent')},
                         {'state': 'VERIFIED', 'receipt': 'PRESENT', 'report_files': 'PRESENT', 'saved_report_outcome': receipt['outcome'],
                          'markdown_outcome': receipt['outcome'], 'receipt_outcome': receipt['outcome'], 'consistent': True})
        self.assertEqual(set(f['checks'].values()), {'MATCH'})
        self.assertTrue({*R.REPORT_FILES, 'pipeline-execution.json', 'REPORT stage hashes', *(f'stage {s}' for s in R.STAGES)} <= set(f['checks']))
        self.assertEqual(receipt['report_sha256'], {n: R.file_facts(ex / n)['sha256'] for n in R.REPORT_FILES})
        self.assertEqual(R.build(self.store), saved)  # the live read-only report renders exactly the committed one
        self.assertEqual(R.markdown(R.build(self.store)), md)
        self.assertNotIn(R.UNFINISHED, md); self.assertIn(R.COMMIT_RULE, md)

    def test_complete_run_report_files_receipt_and_status_agree(self):
        receipt = self.execute()
        self.assertEqual(receipt['outcome'], 'COMPLETE')
        self.assert_finalised(receipt)

    def test_incomplete_critics_run_is_finalised_with_the_same_outcome_everywhere(self):
        self.gemini_mode['prefix'] = 'Bearer FICTIONALtokenValue\n\n'  # a token-shaped value: still a provider fault under V002
        receipt = self.execute()
        self.assertEqual(receipt['outcome'], 'INCOMPLETE_CRITICS')
        self.assert_finalised(receipt)
        econ = {self.critic(self.report(), i, 'ECONOMIC')['faults'][0] for i in self.ideas()}
        self.assertEqual(econ, {'CREDENTIAL_LIKE_PATTERN_IN_RAW_RESPONSE'})

    def test_generation_failure_is_finalised_with_the_same_outcome_everywhere(self):
        self.host.runner = T.FakeCLI(self, model_stream=lambda s: T.stream(s, 'not a JSON idea batch'))
        receipt = self.execute()
        self.assertIn(receipt['outcome'], ('NO_ADMITTED_CARDS', 'GENERATION_FAILED'))
        self.assertNotEqual(receipt['stages']['GENERATION'], 'VALID')
        self.assertEqual([receipt['stages'][s] for s in R.STAGES[1:4]], ['NOT_RECORDED'] * 3)
        self.assertEqual((self.codex_calls, self.gemini_calls), ([], []))
        self.assert_finalised(receipt)

    def test_interrupted_finalisation_is_never_reported_as_finished(self):
        original = R.Run.put
        for point, (name, after) in {'after report JSON': ('report', True), 'after Markdown': ('stage-REPORT', False),
                                     'after REPORT stage': ('receipt', False)}.items():
            with self.subTest(point=point):
                self.fresh('archive-' + name)
                def put(run, n, value, name=name, after=after):
                    if n == name and not after:raise KeyboardInterrupt('fictional crash during finalisation')
                    path = original(run, n, value)
                    if n == name:raise KeyboardInterrupt('fictional crash during finalisation')
                    return path
                result = self.planned(); auth = self.authorise(result)
                with patch.object(R.Run, 'put', put), self.assertRaises(KeyboardInterrupt):R.run(self.store, auth, host=self.pipe)
                ex = self.store / 'exports'
                self.assertFalse((ex / 'pipeline-receipt.json').exists())
                st = R.status(self.store)
                self.assertEqual((st['interrupted'], st['finished'], st['outcome']), (True, False, 'INTERRUPTED'))
                self.assertEqual(st['finalisation'], {'state': 'NOT_FINALISED', 'report_files': 'UNCOMMITTED', 'consistent': False})
                self.assertEqual(R.build(self.store)['outcome'], R.UNFINISHED)
                self.assertIn(R.COMMIT_RULE, json.loads((ex / 'pipeline-report.json').read_text(encoding='utf-8'))['commit_rule'])
                with self.assertRaises(S.ScoutError):R.run(self.store, auth, host=self.pipe)  # never resumed

    def test_every_receipt_bound_artifact_is_verified_and_no_change_or_absence_reads_as_consistent(self):
        receipt = self.execute(); self.assert_finalised(receipt)
        source = self.store
        def rewrite_json(rel, change):
            def apply(ex):
                v = json.loads((ex / rel).read_text(encoding='utf-8')); change(v)
                (ex / rel).write_text(json.dumps(v), encoding='utf-8')
            return apply
        def append(rel):return lambda ex: (ex / rel).write_bytes((ex / rel).read_bytes() + b' ')
        def remove(rel):return lambda ex: (ex / rel).unlink()
        def corrupt(rel):return lambda ex: (ex / rel).write_bytes(b'{not json')
        stage = 'pipeline-stage-REPORT.json'
        cases = {  # mutation -> (state, the check that must name it)
            'report JSON changed': (append('pipeline-report.json'), 'MISMATCH', 'pipeline-report.json'),
            'report JSON removed': (remove('pipeline-report.json'), 'UNVERIFIED', 'pipeline-report.json'),
            'report Markdown changed': (append('pipeline-report.md'), 'MISMATCH', 'pipeline-report.md'),
            'report Markdown removed': (remove('pipeline-report.md'), 'UNVERIFIED', 'pipeline-report.md'),
            'execution record changed': (append('pipeline-execution.json'), 'MISMATCH', 'pipeline-execution.json'),
            'execution record removed': (remove('pipeline-execution.json'), 'UNVERIFIED', 'pipeline-execution.json'),
            'receipt execution hash changed': (rewrite_json('pipeline-receipt.json', lambda v: v.update(execution_sha256='0' * 64)), 'MISMATCH', 'pipeline-execution.json'),
            'receipt execution hash missing': (rewrite_json('pipeline-receipt.json', lambda v: v.pop('execution_sha256')), 'MISMATCH', 'pipeline-execution.json'),
            'REPORT stage hash changed': (rewrite_json(stage, lambda v: v['sha256'].update({'pipeline-report.md': '0' * 64})), 'MISMATCH', 'REPORT stage hashes'),
            'REPORT stage removed': (remove(stage), 'UNVERIFIED', 'REPORT stage hashes'),
            'REPORT stage unreadable': (corrupt(stage), 'UNVERIFIED', 'REPORT stage hashes'),
            'stage status changed': (rewrite_json('pipeline-stage-FIRST_PASS_CRITICS.json', lambda v: v.update(status='INCOMPLETE')), 'MISMATCH', 'stage FIRST_PASS_CRITICS'),
            'stage record removed': (remove('pipeline-stage-RECOMMENDATION.json'), 'UNVERIFIED', 'stage RECOMMENDATION'),
            'stage record unreadable': (corrupt('pipeline-stage-GENERATION.json'), 'UNVERIFIED', 'stage GENERATION'),
            'receipt stage contradicts records': (rewrite_json('pipeline-receipt.json', lambda v: v['stages'].update(RECOMMENDATION='ERROR')), 'MISMATCH', 'stage RECOMMENDATION'),
            'receipt stage set changed': (rewrite_json('pipeline-receipt.json', lambda v: v['stages'].pop('REPORT')), 'MISMATCH', 'receipt stage set'),
            'receipt report binding changed': (rewrite_json('pipeline-receipt.json', lambda v: v['report_sha256'].update({'pipeline-report.json': 'x'})), 'MISMATCH', 'pipeline-report.json'),
            'receipt unreadable': (corrupt('pipeline-receipt.json'), 'UNVERIFIED', 'receipt'),
        }
        for name, (mutate, state, check) in cases.items():
            with self.subTest(mutation=name):
                self.store = self.base / ('fixture-' + name.replace(' ', '-'))
                shutil.copytree(source, self.store)  # an isolated synthetic copy; the source run is never touched
                ex = self.store / 'exports'; mutate(ex)
                before = {p.name: p.read_bytes() for p in ex.iterdir()}
                st = R.status(self.store)
                f = st['finalisation']
                self.assertEqual((f['state'], f['consistent']), (state, False))
                self.assertNotEqual(f['checks'][check], 'MATCH')  # the changed or missing artifact is named
                self.assertTrue(st['finished'])  # the receipt file exists: finished, but not verified
                self.assertEqual({p.name: p.read_bytes() for p in ex.iterdir()}, before)  # read-only: nothing repaired
        self.store = source; self.assert_finalised(receipt)  # the unmutated run still verifies

    def test_a_v001_receipt_and_report_are_read_as_legacy_and_never_rewritten(self):
        self.execute(); ex = self.store / 'exports'
        for n in R.REPORT_FILES + ('pipeline-receipt.json', 'pipeline-execution.json'):(ex / n).unlink()  # fixture: a V001-shaped run
        legacy = {'schema': 'SCOUT_RESEARCH_PIPELINE_RECEIPT_V001', 'outcome': 'INCOMPLETE_CRITICS', 'stages': {s: 'COMPLETE' for s in R.STAGES}}
        (ex / 'pipeline-receipt.json').write_text(json.dumps(legacy), encoding='utf-8')
        (ex / 'pipeline-report.json').write_text(json.dumps({'outcome': R.UNFINISHED, 'stages': {}}), encoding='utf-8')
        (ex / 'pipeline-report.md').write_text(f'# Research OS run report ({R.UNFINISHED})\n', encoding='utf-8')
        before = {n: (ex / n).read_bytes() for n in R.REPORT_FILES}
        st = R.status(self.store)
        self.assertEqual((st['outcome'], st['execution']), ('INCOMPLETE_CRITICS', 'NOT_RECORDED'))
        self.assertEqual({k: st['finalisation'][k] for k in ('state', 'saved_report_outcome', 'consistent')},
                         {'state': 'LEGACY_RECEIPT_UNBOUND', 'saved_report_outcome': R.UNFINISHED, 'consistent': False})
        self.assertEqual(R.build(self.store)['outcome'], 'INCOMPLETE_CRITICS')
        self.assertEqual({n: (ex / n).read_bytes() for n in R.REPORT_FILES}, before)  # read-only

    def test_execution_provenance_is_recorded_from_files_before_any_process_and_bound_by_the_receipt(self):
        cli, seen = self.host.runner, []
        def first(args, **kw):seen.append((self.store / 'exports/pipeline-execution.json').is_file()); return cli(args, **kw)
        self.host.runner = first
        def deny(*a, **k):raise AssertionError('provenance never launches a process')
        with patch.object(subprocess, 'Popen', deny):receipt = self.execute()
        self.assertTrue(seen and all(seen))  # written before the first administrative or model command
        ex = self.store / 'exports'; e = json.loads((ex / 'pipeline-execution.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['execution_sha256'], R.file_facts(ex / 'pipeline-execution.json')['sha256'])
        self.assertEqual((e['schema'], e['worktree_clean']), (R.E.VERSION, S.UNKNOWN))
        self.assertEqual(e['scout_batch_base_commit']['meaning'], R.E.BASE_MEANING)
        commit = e['revision']['commit']
        self.assertTrue(commit == S.UNKNOWN or R.E.HEX.fullmatch(commit))
        files = e['implementation']['files']
        for rel in ('automation_v001/pipeline.py', 'automation_v001/credentials.py', 'critic_v1/policy.py', 'exploratory_v001/runner.py'):
            path = 'src/research/opportunity_scout/' + rel
            self.assertEqual(files[path], hashlib.sha256((ROOT / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest())
        self.assertEqual(R.status(self.store)['execution']['implementation_digest'], e['implementation']['digest'])
        self.assertIn('## Executing code', (ex / 'pipeline-report.md').read_text(encoding='utf-8'))

    def test_git_revision_is_read_from_metadata_files_and_unknown_is_never_inferred(self):
        sha, other = 'a' * 40, 'b' * 40
        def repo(name, files):
            root = self.base / 'git' / name
            for rel, text in files.items():(root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text(text, encoding='utf-8')
            return root
        common = repo('common', {'.git/HEAD': 'ref: refs/heads/main\n', '.git/packed-refs': f'# pack-refs\n{other} refs/heads/other\n{sha} refs/heads/main\n',
                                 '.git/worktrees/w/HEAD': 'ref: refs/heads/other\n', '.git/worktrees/w/commondir': '../..\n'})
        worktree = repo('worktree', {'.git': f'gitdir: {common / ".git/worktrees/w"}\n'})
        cases = {'packed ref': (common, sha, 'refs/heads/main'), 'worktree through commondir': (worktree, other, 'refs/heads/other'),
                 'loose ref': (repo('loose', {'.git/HEAD': 'ref: refs/heads/x\n', '.git/refs/heads/x': sha + '\n'}), sha, 'refs/heads/x'),
                 'detached': (repo('detached', {'.git/HEAD': other + '\n'}), other, 'DETACHED')}
        for name, (root, commit, ref) in cases.items():
            with self.subTest(case=name):self.assertEqual({k: R.E.revision(root)[k] for k in ('commit', 'ref')}, {'commit': commit, 'ref': ref})
        unknown = {'NO_GIT_METADATA': self.base / 'git' / 'none', 'UNRECOGNISED_GIT_FILE': repo('file', {'.git': 'not a pointer\n'}),
                   'UNRECOGNISED_HEAD': repo('escape', {'.git/HEAD': 'ref: refs/../../secret\n'}),
                   'REF_NOT_RESOLVED': repo('missing', {'.git/HEAD': 'ref: refs/heads/gone\n'}),
                   'GIT_METADATA_UNREADABLE': repo('dangling', {'.git': 'gitdir: does/not/exist\n'})}
        for reason, root in unknown.items():
            with self.subTest(reason=reason):
                r = R.E.revision(root)
                self.assertEqual((r['commit'], r['reason']), (S.UNKNOWN, reason))

    def test_economic_bearer_prose_critique_is_imported_end_to_end(self):
        self.gemini_mode['prefix'] = 'The cost bearer remains the contractor; an identifiable economic bearer exists.\n\n'
        receipt = self.execute()
        self.assertEqual(receipt['outcome'], 'COMPLETE')
        for i in self.ideas():
            econ = self.critic(self.report(), i, 'ECONOMIC')
            self.assertEqual((econ['outcome'], econ['status'], econ['faults']), ('IMPORTED', 'VALID', []))
        records = [json.loads(x.read_text(encoding='utf-8')) for x in (self.store / 'exports').glob('pipeline-critic-*.json')]
        self.assertEqual({r['credential_screen']['version'] for r in records}, {V.CR.VERSION})


class TruncatedOrigin(PV.FakeOrigins):
    """The documented host answers 200 and then the body breaks off: reading it raises IncompleteRead."""
    class Body(io.BytesIO):
        def read(self, *args):raise http.client.IncompleteRead(SECRET.encode('utf-8'), 4096)

    def https_open(self, req):
        self.seen.append((V.GEMINI_HOST, {}))
        from urllib.response import addinfourl
        response = addinfourl(self.Body(), email.message.Message(), req.full_url, 200); response.msg = 'fixture'
        return response


class HardeningTests(Base):
    """Uncaught HTTP protocol errors (Gemini) and preflight scope across Codex executables."""
    def assert_nothing_sensitive_persisted(self):
        for f in self.persisted():
            data = f.read_bytes()
            self.assertNotIn(KEY.encode(), data, f.name); self.assertNotIn(SECRET.encode(), data, f.name)

    def test_http_protocol_errors_become_recorded_transport_faults(self):
        cases = {'IncompleteRead': http.client.IncompleteRead((SECRET + KEY).encode('utf-8'), 4096),
                 'HTTPException': http.client.HTTPException(SECRET + ' ' + KEY),
                 'BadStatusLine': http.client.BadStatusLine(SECRET),
                 'ScoutError': S.ScoutError(SECRET)}  # only the transport's own fixed codes are ever recorded verbatim
        for name, error in cases.items():
            with self.subTest(error=name):
                self.tearDown(); self.setUp(); self.gemini_mode['error'] = error
                receipt = self.execute()  # recorded, never an unhandled pipeline exception
                rep = self.report()
                self.assertEqual(receipt['outcome'], 'INCOMPLETE_CRITICS')
                for idea in self.ideas():
                    econ = self.critic(rep, idea, 'ECONOMIC')
                    self.assertEqual((econ['outcome'], econ['status'], econ['faults']), ('PROVIDER_FAULT', None, ['TRANSPORT_FAILED:' + name]))
                prompts = [c['body']['contents'][0]['parts'][0]['text'] for c in self.gemini_calls]
                self.assertEqual((len(prompts), len(set(prompts))), (2, 2))  # one dispatch per request, never a second attempt
                gemini = [r for r in rep['accounting']['critic_requests'].values() if r['provider'] == V.GEMINI]
                self.assertEqual([r['provider_requests'] for r in gemini], [R.UNSEEN] * 2)  # sent maybe; no complete response
                self.assertEqual((rep['spend']['cost_estimate_usd_documented_prices'], rep['spend']['actual_charges']), (S.UNKNOWN, S.UNKNOWN))
                self.assertFalse(list((self.store / 'exports').glob('pipeline-*-response.bin')))  # no partial body kept as a reply
                self.assert_nothing_sensitive_persisted()

    def test_a_truncated_body_through_the_real_transport_keeps_the_reservation_and_is_never_retried(self):
        origin = TruncatedOrigin(None)
        self.pipe.transport = lambda url, headers, body, timeout: V.https_transport(url, headers, body, timeout, handlers=(origin,))
        big = {**self.economic, 'max_output_tokens': 65536}  # worst case about 0.70 USD: a $1 cap holds one reservation
        receipt = self.execute(economic=big, spend_cap_usd=1.0); rep = self.report()
        self.assertEqual(receipt['outcome'], 'INCOMPLETE_CRITICS')
        faults = sorted(self.critic(rep, i, 'ECONOMIC')['faults'] for i in self.ideas())
        self.assertEqual(faults, [['SPEND_CAP_WOULD_BE_EXCEEDED'], ['TRANSPORT_FAILED:IncompleteRead']])
        self.assertEqual(len(origin.seen), 1)  # the failed request is not resent; the next does not fit the cap
        sent = next(json.loads(x.read_text(encoding='utf-8')) for x in sorted((self.store / 'exports').glob('pipeline-critic-*.json'))
                    if json.loads(x.read_text(encoding='utf-8')).get('faults') == ['TRANSPORT_FAILED:IncompleteRead'])
        self.assertEqual((sent['reservation_released'], sent['spend_reserved_worst_case_usd_total']), (False, sent['worst_case_usd']))
        self.assertEqual((rep['spend']['worst_case_reserved_usd'], rep['spend']['reservations_released_usd']), (sent['worst_case_usd'], 0))
        self.assert_nothing_sensitive_persisted()

    def test_first_executable_passing_never_authorises_a_failing_second(self):
        other = self.both_codex()
        for mode, stop in (('api_key_login', 'CODEX_NOT_CHATGPT_SUBSCRIPTION_LOGIN'), ('exit', 'ADMIN_COMMAND_FAILED:login')):
            with self.subTest(mode=mode):
                self.tearDown(); self.setUp(); other = self.both_codex(); self.admin_mode[(other, 'login')] = mode
                self.execute(); rep = self.report()
                for idea in self.ideas():
                    self.assertEqual(self.critic(rep, idea, 'ECONOMIC')['faults'], ['PREFLIGHT_STOP:' + stop])
                    self.assertEqual(self.critic(rep, idea, 'SCIENTIFIC')['status'], 'VALID')
                self.assertEqual(sorted({c['exe'] for c in self.codex_calls}), [str(self.codex.resolve())])  # the failed one never starts
                self.assertEqual(len(self.codex_calls), 2)
                rows = [r for r in rep['accounting']['critic_requests'].values() if r['critic'] == 'ECONOMIC']
                self.assertEqual([r['model_cli_processes_started'] for r in rows], [R.ZERO] * 2)

    def test_distinct_executables_each_pass_their_own_preflight_before_first_use(self):
        other = self.both_codex(); first = str(self.codex.resolve())
        self.execute(); rep = self.report()
        for exe in (first, other):  # every preflight command of an executable precedes its first critic process
            admin = [i for i, e in enumerate(self.events) if e == ('admin', exe)]
            critic = [i for i, e in enumerate(self.events) if e == ('critic', exe)]
            self.assertEqual((len(admin), len(critic)), (3, 2)); self.assertLess(max(admin), min(critic))
        recs = self.preflights()
        self.assertEqual(sorted((r['executable'], r['administrative_launches'], r['processes_started']) for r in recs),
                         sorted([(first, 3, 3), (other, 3, 3)]))
        self.assertEqual({r['executable_sha256'] for r in recs}, {R.CS.file_hash(Path(first)), R.CS.file_hash(Path(other))})
        acc = rep['accounting']
        self.assertEqual(acc['codex_preflight']['administrative_cli_launches'], {'at_least': 6, 'exact': 6})
        gen = acc['generation']['administrative_cli_launches']['exact']
        self.assertEqual(acc['totals']['administrative_cli_launches'], {'at_least': gen + 6, 'exact': gen + 6})
        self.assertEqual({s for row in rep['subjects'].values() for s in (c['status'] for c in row['critics'].values())}, {'VALID'})

    def test_identical_configuration_reuses_one_successful_preflight(self):
        self.both_codex(other=False)
        self.execute(); rep = self.report()
        self.assertEqual((len(self.admin_calls), len(self.codex_calls), len(self.preflights())), (3, 4, 1))
        self.assertEqual(rep['accounting']['codex_preflight']['administrative_cli_launches'], {'at_least': 3, 'exact': 3})
        self.assertEqual({c['status'] for row in rep['subjects'].values() for c in row['critics'].values()}, {'VALID'})

    def test_a_changed_executable_blocks_dispatch(self):
        other = self.both_codex(); result = self.planned()
        Path(other).write_bytes(b'tampered after the plan pinned its hash')
        R.run(self.store, self.authorise(result), host=self.pipe); rep = self.report()
        for idea in self.ideas():self.assertEqual(self.critic(rep, idea, 'ECONOMIC')['faults'], ['PREFLIGHT_STOP:CODEX_EXECUTABLE_CHANGED'])
        self.assertNotIn(other, {c['exe'] for c in self.admin_calls + self.codex_calls})  # no command of any kind from it
        self.tearDown(); self.setUp()
        self.codex_mode['replace_executable'] = True  # the one Codex executable changes while its first critic runs
        self.execute(); rep = self.report()
        faults = sorted(self.critic(rep, i, 'SCIENTIFIC')['faults'][-1] for i in self.ideas())
        self.assertEqual(faults, ['EXECUTABLE_CHANGED_BEFORE_DISPATCH', 'EXECUTABLE_CHANGED_DURING_RUN'])
        self.assertEqual(len(self.codex_calls), 1)  # the cached preflight never launches a changed binary
