"""Exploratory FORGE runner V001: offline only. A fake CLI replays the real 2.1.302 stream vocabulary
(ui_invalidate, init with built-in plugins, thinking_tokens, rate_limit_event, null message stop_reason).
No process, network, credential or real home directory is touched."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from src.research.opportunity_scout import schema as S, v004_package
from src.research.opportunity_scout.exploratory_v001 import runner as X
from src.research.opportunity_scout.exploratory_v001.__main__ import main
from src.research.opportunity_scout.storage import Archive, ROOT
from src.research.opportunity_scout.v004_r3 import package as R3

MODEL = 'claude-opus-5-5'
IDEA = json.loads((ROOT / 'docs/opportunity_scout/operator_example/forge-response.json').read_text(encoding='utf-8'))['output']['ideas'][0]
TEXT = json.dumps({'ideas': [IDEA]})


def stream(session, text=TEXT, *, model=MODEL, output_tokens=2500, extra=(), init=None, result=None, rate=None, blocks=None):
    events = [{'type': 'system', 'subtype': 'ui_invalidate', 'session_id': session},
              {'type': 'system', 'subtype': 'init', 'session_id': session, 'tools': [], 'mcp_servers': [], 'skills': [],
               'plugins': [{'name': 'cc-plugin-agents-md', 'path': 'builtin', 'source': 'cc-plugin-agents-md@builtin'}],
               'permissionMode': 'dontAsk', 'apiKeySource': 'none', 'model': model, 'claude_code_version': '2.1.302', **(init or {})},
              {'type': 'system', 'subtype': 'thinking_tokens', 'session_id': session, 'estimated_tokens': 300},
              {'type': 'rate_limit_event', 'session_id': session,
               'rate_limit_info': {'status': 'allowed', 'isUsingOverage': False, 'overageStatus': 'rejected', **(rate or {})}},
              {'type': 'assistant', 'session_id': session, 'request_id': 'req_A',
               'message': {'id': 'msg_A', 'model': model, 'content': [{'type': 'thinking', 'thinking': 'fictional'}], 'stop_reason': None}},
              {'type': 'assistant', 'session_id': session, 'request_id': 'req_A',
               'message': {'id': 'msg_A', 'model': model, 'content': blocks or [{'type': 'text', 'text': text}], 'stop_reason': None}},
              *extra,
              {'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': session, 'result': text, 'stop_reason': 'end_turn',
               'num_turns': 1, 'permission_denials': [], 'subagent_stats': {'spawned': 0}, 'total_cost_usd': 0.12,
               'usage': {'input_tokens': 4, 'cache_read_input_tokens': 900, 'cache_creation_input_tokens': 6000, 'output_tokens': output_tokens,
                         'output_tokens_details': {'thinking_tokens': 600}, 'server_tool_use': {'web_search_requests': 0, 'web_fetch_requests': 0}},
               'modelUsage': {model: {'provider': 'firstParty', 'costBasis': 'list'}}, **(result or {})}]
    return ''.join(json.dumps(e) + '\n' for e in events).encode('utf-8')


def mutated(change):
    """A real-vocabulary stream with one deliberate change applied to its decoded events."""
    def make(session):
        events = [json.loads(line) for line in stream(session).decode('utf-8').splitlines()]
        change(events, session)
        return ''.join(json.dumps(e) + '\n' for e in events).encode('utf-8')
    return make


class FakeCLI:
    """Answers the three administrative commands and one print-mode call. Never starts a process."""
    def __init__(self, test, *, auth=None, auth_after=None, help_text=None, model_stream=None, timeout=False, on_model=None, code=0):
        self.t, self.calls, self.auth_calls = test, [], 0
        self.auth = {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty', 'subscriptionType': 'max',
                     'configDirectory': str(test.host.config), 'email': 'fictional@example.invalid', **(auth or {})}
        self.auth_after = auth_after
        self.help = help_text if help_text is not None else ' '.join(X.FLAGS)
        self.model_stream, self.timeout, self.on_model, self.code = model_stream, timeout, on_model, code

    def __call__(self, args, **kwargs):
        self.calls.append((list(args), kwargs))
        if '--print' in args:  # the runner hands the CLI exclusive raw files; nothing is captured in memory
            session = args[args.index('--session-id') + 1]
            if self.on_model:self.on_model()
            if self.timeout:
                kwargs['stdout'].write(b'{"type":"system"'); raise subprocess.TimeoutExpired(args, 1)
            kwargs['stdout'].write(self.model_stream(session) if callable(self.model_stream) else stream(session))
            return subprocess.CompletedProcess(args, self.code, None, None)
        if args[1:] == ['--version']:return subprocess.CompletedProcess(args, 0, '2.1.302 (Claude Code)\n', '')
        if args[1:] == ['--help']:return subprocess.CompletedProcess(args, 0, self.help, '')
        if args[1:] == ['auth', 'status', '--json']:
            self.auth_calls += 1
            value = self.auth if self.auth_calls == 1 or self.auth_after is None else {**self.auth, **self.auth_after}
            return subprocess.CompletedProcess(args, 0, json.dumps(value), '')
        raise AssertionError('unexpected command ' + repr(args))

    def kinds(self):
        return ['MODEL' if '--print' in a else 'ADMIN' for a, _ in self.calls]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); base = Path(self.tmp.name)
        home = base / 'home'; (home / '.claude-research').mkdir(parents=True)
        (home / '.claude-research' / '.credentials.json').write_bytes(b'')
        (home / '.claude').mkdir(); (home / '.claude.json').write_bytes(b'{}')
        self.exe = base / 'bin' / 'claude.exe'; self.exe.parent.mkdir(); self.exe.write_bytes(b'fictional executable bytes')
        self.store = base / 'archive'
        self.host = X.Host(home=home, runner=self.refuse, environ={'PATH': '/bin', 'ANTHROPIC_API_KEY': 'sk-fictional',
                           'CLAUDE_CODE_OAUTH_TOKEN': 'fictional', 'ANTHROPIC_BASE_URL': 'https://fictional.invalid'},
                           policy_check=lambda config: None)
        self.base = base

    def tearDown(self):self.tmp.cleanup()

    @staticmethod
    def refuse(*a, **k):raise AssertionError('no process may start during planning')

    def planned(self, **overrides):
        args = dict(title='Fixture exploratory run', model=MODEL, count=1, effort='low', max_output_tokens_per_request=16000,
                    timeout_seconds=300, executable=str(self.exe), host=self.host)
        args.update(overrides)
        return X.plan(self.store, **args)

    def authorise(self, plan_result, **changes):
        template = json.loads(Path(plan_result['authorisation_template']).read_text(encoding='utf-8'))
        value = {**template, 'allowed_subscription_types': ['max'], 'hosted_transmission_approved': True,
                 'owner': 'Fixture Owner', 'approved_at': '2026-10-24T09:00:00+01:00', **changes}
        path = self.base / f'authorisation-{len(list(self.base.glob("authorisation-*")))}.json'
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def execute(self, cli, **auth_changes):
        result = self.planned()
        self.host.runner = cli
        return X.run(self.store, self.authorise(result, **auth_changes), host=self.host)

    def state(self):return Archive(self.store).load()

    def fresh(self):
        self.tearDown(); self.setUp()


class PlanTests(Base):
    def test_plan_starts_no_process_and_binds_exact_payload(self):
        result = self.planned()
        state = self.state()
        self.assertEqual((result['model_calls_made'], result['cli_commands_run'], len(state.attempts)), (0, 0, 1))
        self.assertEqual(state.batch['memory']['mapping_review'], 'NO_MEMORY_INCLUDED')
        prompt = next(iter(state.prompts.values()))
        self.assertEqual((prompt['lane'], prompt['context']), ('FORGE', {'seeds': {}, 'memory': {}}))
        import hashlib
        self.assertEqual(result['payload_sha256'], hashlib.sha256(X.payload(prompt)).hexdigest())
        self.assertTrue(X.payload(prompt).endswith(X.addendum()))
        plan = json.loads((self.store / 'exports/exploratory-plan-ATT-0001.json').read_text(encoding='utf-8'))
        self.assertNotIn('ANTHROPIC_API_KEY', json.dumps(plan)); self.assertEqual(plan['controls']['CLAUDE_CODE_MAX_TURNS'], '1')
        with self.assertRaises(S.ScoutError):self.planned()  # a second plan needs a new archive

    def test_plan_refuses_aliases_and_unbounded_limits(self):
        for bad in ({'model': 'opus'}, {'effort': 'max'}, {'count': 5}, {'max_output_tokens_per_request': 64000}, {'timeout_seconds': 3600}):
            with self.subTest(bad=bad), self.assertRaises(S.ScoutError):self.planned(**bad)
        self.assertFalse(self.store.exists() and any(self.store.iterdir()))

    def test_frozen_addendum_matches_the_pilot_bytes(self):
        import hashlib
        self.assertEqual(hashlib.sha256(X.addendum()).hexdigest(), X.ADDENDUM_SHA256)
        self.assertIn('REQ_OTHER', X.addendum().decode('utf-8'))


class AuthorisationTests(Base):
    def test_refuses_incomplete_or_altered_authorisation_and_consumes_nothing(self):
        result = self.planned(); cli = FakeCLI(self); self.host.runner = cli
        template = Path(result['authorisation_template'])
        cases = {'template as written': None, 'assistant owner': {'owner': 'Claude'}, 'no timezone': {'approved_at': '2026-10-24T09:00:00'},
                 'payload changed': {'payload_sha256': '0' * 64}, 'api billing': {'allowed_subscription_types': ['api']},
                 'two invocations': {'model_invocations_maximum': 2}, 'not approved': {'hosted_transmission_approved': False}}
        for name, change in cases.items():
            path = template if change is None else self.authorise(result, **change)
            with self.subTest(case=name), self.assertRaises(S.ScoutError):X.run(self.store, path, host=self.host)
        self.assertEqual(cli.calls, [])
        self.assertFalse(X.status(self.store)['claimed'])
        self.assertEqual(self.state().attempts['ATT-0001'].get('result'), None)


class RunTests(Base):
    def test_valid_run_invokes_once_imports_triages_and_reports(self):
        cli = FakeCLI(self)
        receipt = self.execute(cli)
        self.assertEqual((receipt['status'], receipt['model_invocations'], receipt['administrative_commands_run']), ('VALID', 1, 4))
        self.assertEqual(cli.kinds(), ['ADMIN', 'ADMIN', 'ADMIN', 'MODEL', 'ADMIN'])
        args, kwargs = next(c for c in cli.calls if '--print' in c[0])
        self.assertNotIn('--json-schema', args)
        self.assertEqual(args[args.index('--tools') + 1], '')
        env = kwargs['env']
        self.assertEqual(env['CLAUDE_CONFIG_DIR'], str(self.host.config))
        for key in ('ANTHROPIC_API_KEY', 'CLAUDE_CODE_OAUTH_TOKEN', 'ANTHROPIC_BASE_URL'):self.assertNotIn(key, env)
        self.assertEqual(kwargs['input'], X.payload(next(iter(self.state().prompts.values()))))
        state = self.state()
        self.assertEqual(len(state.cards), 1)
        result = state.attempts['ATT-0001']['result']
        self.assertEqual(result['provider']['parameters']['transport'], X.VERSION)
        self.assertEqual(result['provider']['usage']['output_tokens'], 2500)
        self.assertEqual(state.efforts[-1]['invocation_status'], 'INVOKED')
        self.assertTrue(state.assessments)
        for name in ('stdout.bin', 'stderr.bin'):self.assertTrue((self.store / f'exports/exploratory-ATT-0001-{name}').is_file())
        self.assertTrue((self.store / 'exports/exploratory-report-ATT-0001.json').is_file())
        self.assertNotIn('fictional@example.invalid', json.dumps(receipt))
        self.assertEqual(receipt['preflight']['account']['configDirectory'], str(self.host.config))
        st = X.status(self.store); self.assertEqual((st['claimed'], st['receipt'], st['interrupted']), (True, True, False))

    def test_second_run_is_refused_without_any_process(self):
        cli = FakeCLI(self); self.execute(cli); before = len(cli.calls)
        auth = sorted(self.base.glob('authorisation-*.json'))[-1]
        with self.assertRaises(S.ScoutError):X.run(self.store, auth, host=self.host)
        self.assertEqual(len(cli.calls), before)

    def test_preflight_failures_close_the_attempt_without_a_model_call(self):
        cases = {'api key auth': {'auth': {'authMethod': 'api_key'}}, 'development config': {'auth': {'configDirectory': '/elsewhere/.claude'}},
                 'team plan': {'auth': {'subscriptionType': 'team'}}, 'logged out': {'auth': {'loggedIn': False}},
                 'missing flag': {'help_text': '--print --model'}}
        for name, kwargs in cases.items():
            with self.subTest(case=name):
                self.fresh()
                cli = FakeCLI(self, **kwargs); receipt = self.execute(cli)
                self.assertEqual((receipt['status'], receipt['model_invocations'], self.state().cards), ('ERROR', 0, {}))
                self.assertTrue(receipt['error'].startswith('PREFLIGHT_STOP:'))
                self.assertEqual(self.state().efforts[-1]['invocation_status'], 'NOT_INVOKED')

    def test_policy_remote_settings_and_executable_change_stop_before_the_model(self):
        def policy(config):raise S.ScoutError('managed policy present')
        cases = {'managed policy': lambda: setattr(self.host, 'policy_check', policy),
                 'server settings cache': lambda: (self.host.config / 'remote-settings.json').write_bytes(b'{}'),
                 'executable changed': lambda: self.exe.write_bytes(b'updated executable bytes')}
        for name, arrange in cases.items():
            with self.subTest(case=name):
                self.fresh()
                result = self.planned(); arrange(); cli = FakeCLI(self); self.host.runner = cli
                receipt = X.run(self.store, self.authorise(result), host=self.host)
                self.assertEqual((receipt['status'], receipt['model_invocations']), ('ERROR', 0))
                self.assertNotIn('MODEL', cli.kinds())


class StreamTests(Base):
    def stopped(self, model_stream=None, auth_changes=None, **kwargs):
        cli = FakeCLI(self, model_stream=model_stream, **kwargs)
        receipt = self.execute(cli, **(auth_changes or {}))
        self.assertEqual((receipt['status'], receipt['model_invocations'], len(self.state().cards)), ('ERROR', 1, 0))
        self.assertTrue((self.store / 'exports/exploratory-ATT-0001-stdout.bin').is_file())
        return receipt['error']

    def test_deviations_stop_without_cards_or_retry(self):
        second = {'type': 'assistant', 'request_id': 'req_B', 'message': {'id': 'msg_B', 'model': MODEL, 'content': [{'type': 'text', 'text': 'more'}]}}
        notice = {'type': 'user', 'isSynthetic': True, 'message': {'role': 'user', 'content': [{'type': 'text', 'text': 'Output token limit reached.'}]}}
        tool = [{'type': 'tool_use', 'name': 'Bash', 'input': {}}]
        cases = {
            'continuation': (lambda s: stream(s, extra=[{**notice, 'session_id': s}, {**second, 'session_id': s}]), 'CONTINUATION_OR_TOOL_RESULT'),
            'second generation': (lambda s: stream(s, extra=[{**second, 'session_id': s}]), 'NOT_EXACTLY_ONE_GENERATION'),
            'overage': (lambda s: stream(s, rate={'isUsingOverage': True}), 'OVERAGE_OR_RATE_LIMIT'),
            'api key source': (lambda s: stream(s, init={'apiKeySource': 'ANTHROPIC_API_KEY'}), 'API_KEY_SOURCE_NOT_NONE'),
            'model mismatch': (lambda s: stream(s, init={'model': 'claude-sonnet-5-5'}), 'MODEL_MISMATCH'),
            'tool use': (lambda s: stream(s, blocks=tool), 'PROHIBITED_TOOL_OR_CONTENT'),
            'max turns': (lambda s: stream(s, result={'subtype': 'error_max_turns', 'is_error': True}), 'CLI_MAX_TURNS'),
            'unknown system event': (lambda s: stream(s, extra=[{'type': 'system', 'subtype': 'compact_boundary', 'session_id': s}]), 'UNRECOGNISED_SYSTEM_EVENT'),
            'tools present': (lambda s: stream(s, init={'tools': ['Bash']}), 'ENVIRONMENT_NOT_ESTABLISHED'),
            'third-party provider': (lambda s: stream(s, result={'modelUsage': {MODEL: {'provider': 'bedrock'}}}), 'MODEL_USAGE_IDENTITY_OR_PROVIDER'),
            'not a stream': (lambda s: b'not json\n', 'INVALID_STREAM_ENVELOPE')}
        for name, (make, code) in cases.items():
            with self.subTest(case=name):
                self.fresh(); self.assertIn(code, self.stopped(make))

    def test_timeout_and_post_run_drift_are_final(self):
        with self.subTest(case='timeout'):
            self.fresh(); self.assertIn('TIMEOUT', self.stopped(timeout=True))
        with self.subTest(case='development account touched'):
            self.fresh()
            self.assertIn('DEVELOPMENT_ACCOUNT_METADATA_CHANGED', self.stopped(on_model=lambda: (self.host.home / '.claude.json').write_bytes(b'{"x":1}')))
        with self.subTest(case='account categories changed'):
            self.fresh()
            self.assertIn('ACCOUNT_CATEGORIES_CHANGED', self.stopped(auth_after={'subscriptionType': 'pro'},
                                                                     auth_changes={'allowed_subscription_types': ['max', 'pro']}))
        with self.subTest(case='unauthorised subscription after the call'):
            self.fresh()
            self.assertIn('POSTFLIGHT_SUBSCRIPTION_TYPE_NOT_AUTHORISED', self.stopped(auth_after={'subscriptionType': 'pro'}))

    def test_unusable_answer_is_kept_invalid_and_budget_overrun_is_honest(self):
        fenced = '```json\n' + TEXT + '\n```'
        receipt = self.execute(FakeCLI(self, model_stream=lambda s: stream(s, fenced)))
        self.assertEqual((receipt['status'], len(self.state().cards)), ('INVALID', 0))
        self.assertEqual(self.state().attempts['ATT-0001']['result']['raw_response'], fenced)
        self.fresh()
        receipt = self.execute(FakeCLI(self, model_stream=lambda s: stream(s, output_tokens=7000)))
        self.assertEqual((receipt['status'], len(self.state().cards)), ('ERROR', 0))
        self.assertIn('output-token budget', self.state().attempts['ATT-0001']['result']['error'])


class ReviewFindingTests(Base):
    """Regressions for the independent review of 4509736: each gap must fail closed."""
    def stopped(self, make, auth_changes=None):
        receipt = self.execute(FakeCLI(self, model_stream=make), **(auth_changes or {}))
        self.assertEqual((receipt['status'], len(self.state().cards)), ('ERROR', 0))
        return receipt['error']

    def test_missing_rate_limit_event_is_not_evidence_of_no_overage(self):
        drop = mutated(lambda ev, s: ev.__setitem__(slice(None), [e for e in ev if e['type'] != 'rate_limit_event']))
        self.assertIn('NON_OVERAGE_NOT_EVIDENCED', self.stopped(drop))

    def test_reported_turn_count_must_be_exactly_one(self):
        def turns(value):
            def change(ev, s):
                if value is None:del ev[-1]['num_turns']
                else:ev[-1]['num_turns'] = value
            return mutated(change)
        for value in (None, 0, 2, True, '1'):
            with self.subTest(num_turns=value):
                self.fresh(); self.assertIn('TURN_COUNT_NOT_ONE', self.stopped(turns(value)))

    def test_session_identifiers_must_be_present_and_match(self):
        def strip(kind, value=None):
            def change(ev, s):
                for e in ev:
                    if e['type'] == kind or (kind == 'init' and e.get('subtype') == 'init'):
                        e.pop('session_id', None)
                        if value is not None:e['session_id'] = value
            return mutated(change)
        cases = {'init missing': strip('init'), 'assistant missing': strip('assistant'), 'result missing': strip('result'),
                 'rate event missing': strip('rate_limit_event'), 'assistant from another session': strip('assistant', 'other-session')}
        for name, make in cases.items():
            with self.subTest(case=name):
                self.fresh(); self.assertIn('SESSION_ID_MISSING_OR_CHANGED', self.stopped(make))

    def test_oversized_stream_is_preserved_but_never_parsed(self):
        from unittest.mock import patch
        with patch.object(X, 'MAX_STREAM_BYTES', 1000), patch.object(X, 'review', side_effect=AssertionError('must not parse')):
            receipt = self.execute(FakeCLI(self))
        self.assertEqual((receipt['status'], receipt['error']), ('ERROR', 'RUN_STOP:RECORDING_SIZE_LIMIT'))
        raw = self.store / 'exports/exploratory-ATT-0001-stdout.bin'
        self.assertGreater(raw.stat().st_size, 1000); self.assertEqual(receipt['stdout_bytes'], raw.stat().st_size)

    def test_credential_like_raw_stream_stops_and_stays_private(self):
        leak = mutated(lambda ev, s: ev[4]['message']['content'][0].__setitem__('thinking', 'fictional sk-ant-0000 in thinking'))
        self.assertIn('CREDENTIAL_LIKE_PATTERN_IN_RAW_STREAM', self.stopped(leak))
        self.assertIn(b'sk-ant-0000', (self.store / 'exports/exploratory-ATT-0001-stdout.bin').read_bytes())  # preserved, not repaired
        self.assertNotIn('sk-ant-0000', json.dumps(json.loads((self.store / 'exports/exploratory-receipt-ATT-0001.json').read_text(encoding='utf-8'))))

    def test_raw_capture_setup_failure_closes_the_attempt_without_a_model_call(self):
        result = self.planned(); cli = FakeCLI(self); self.host.runner = cli
        (self.store / 'exports/exploratory-ATT-0001-stderr.bin').write_bytes(b'')  # exclusive create must then fail
        receipt = X.run(self.store, self.authorise(result), host=self.host)
        self.assertEqual((receipt['status'], receipt['error'], receipt['model_invocations']), ('ERROR', 'RAW_CAPTURE_SETUP_FAILED', 0))
        self.assertTrue(X.status(self.store)['receipt'])

    def test_model_output_is_written_to_files_not_buffered(self):
        cli = FakeCLI(self); self.execute(cli)
        _, kwargs = next(c for c in cli.calls if '--print' in c[0])
        self.assertNotIn('capture_output', kwargs)
        for channel in ('stdout', 'stderr'):self.assertTrue(hasattr(kwargs[channel], 'fileno'))


class BoundaryTests(unittest.TestCase):
    def test_runner_is_outside_the_frozen_v004_and_r3_closures(self):
        for closure in (v004_package.implementation(), R3.implementation()):
            self.assertFalse([p for p in closure if 'exploratory_v001' in p])

    def test_cli_status_and_bad_plan_start_no_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / 'archive'
            self.assertEqual(main(['plan', str(store), '--title', 't', '--model', 'opus', '--executable', str(Path(tmp) / 'none.exe')]), 2)
            self.assertFalse(store.exists() and any(store.iterdir()))
