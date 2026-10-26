"""Exploratory FORGE runner V001: offline only. A fake CLI replays the real 2.1.302 stream vocabulary
(ui_invalidate, init with built-in plugins, thinking_tokens, rate_limit_event, null message stop_reason).
No process, network, credential or real home directory is touched."""
import copy
import json
from pathlib import Path
import re
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
            kwargs['on_start'](4242)  # as capture() does once Popen has returned
            if self.on_model:self.on_model()
            if self.timeout:
                kwargs['stdout'].write(b'{"type":"system"'); raise subprocess.TimeoutExpired(args, 1)
            kwargs['stdout'].write(self.model_stream(session) if callable(self.model_stream) else stream(session))
            return subprocess.CompletedProcess(args, self.code, None, None)
        if args[1:] == ['--version']:text = '2.1.302 (Claude Code)\n'
        elif args[1:] == ['--help']:text = self.help
        elif args[1:] == ['auth', 'status', '--json']:
            self.auth_calls += 1
            text = json.dumps(self.auth if self.auth_calls == 1 or self.auth_after is None else {**self.auth, **self.auth_after})
        else:raise AssertionError('unexpected command ' + repr(args))
        kwargs['stdout'].write(text.encode('utf-8'))  # administrative output also goes to the runner's bounded sinks
        return subprocess.CompletedProcess(args, 0, None, None)

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

    def test_real_2_1_302_help_without_max_turns_still_runs_exactly_one_turn(self):
        """The real 2.1.302 --help omits the documented --max-turns; every other runner flag must still be listed."""
        cli = FakeCLI(self, help_text=' '.join(f for f in X.FLAGS if f != '--max-turns')); receipt = self.execute(cli)
        self.assertEqual((receipt['status'], receipt['model_invocations']), ('VALID', 1))
        args, kwargs = next(c for c in cli.calls if '--print' in c[0])
        self.assertEqual((args[args.index('--max-turns') + 1], kwargs['env']['CLAUDE_CODE_MAX_TURNS']), ('1', '1'))
        for absent in ('--tools', '--safe-mode', '--restricted', '--no-session-persistence'):
            with self.subTest(absent=absent):
                self.fresh()
                cli = FakeCLI(self, help_text=' '.join(f for f in X.FLAGS if f not in ('--max-turns', absent))); receipt = self.execute(cli)
                self.assertEqual((receipt['status'], receipt['model_invocations']), ('ERROR', 0))
                self.assertIn('UNSUPPORTED_FLAGS:' + absent, receipt['error']); self.assertNotIn('MODEL', cli.kinds())

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


class RateLimitReviewV002Tests(Base):
    """Stream review V002: 'allowed_warning' is accepted only without overage; everything else still fails closed."""
    def receipt(self, make):
        return self.execute(FakeCLI(self, model_stream=make))

    def test_allowed_warning_without_overage_is_accepted_and_recorded(self):
        # The exact combination observed in campaign 30 scan 01.
        receipt = self.receipt(lambda s: stream(s, rate={'status': 'allowed_warning', 'rateLimitType': 'seven_day'}))
        self.assertEqual((receipt['status'], len(self.state().cards)), ('VALID', 1))
        self.assertEqual(receipt['review']['stream_review'], X.STREAM_REVIEW)
        self.assertEqual(receipt['review']['rate_limit_states'], [{'status': 'allowed_warning', 'window': 'seven_day'}])
        self.assertEqual(receipt['review']['overage_status'], ['rejected'])

    def test_allowed_is_still_accepted_and_recorded(self):
        receipt = self.receipt(lambda s: stream(s))
        self.assertEqual(receipt['status'], 'VALID')
        self.assertEqual(receipt['review']['rate_limit_states'], [{'status': 'allowed', 'window': 'UNKNOWN'}])

    def test_overage_rejection_missing_and_unknown_states_fail_closed(self):
        def without(key):
            return mutated(lambda ev, s: next(e for e in ev if e['type'] == 'rate_limit_event')['rate_limit_info'].pop(key))
        cases = {
            'warning with overage': lambda s: stream(s, rate={'status': 'allowed_warning', 'isUsingOverage': True}),
            'allowed with overage': lambda s: stream(s, rate={'isUsingOverage': True}),
            'rejected': lambda s: stream(s, rate={'status': 'rejected'}),
            'unknown status': lambda s: stream(s, rate={'status': 'allowed_soon'}),
            'status not a plain label': lambda s: stream(s, rate={'status': 'Allowed Warning'}),
            'overage flag not a boolean': lambda s: stream(s, rate={'status': 'allowed_warning', 'isUsingOverage': 'false'}),
            'overage flag null': lambda s: stream(s, rate={'isUsingOverage': None}),
            'status missing': without('status'),
            'overage flag missing': without('isUsingOverage'),
            'info not an object': mutated(lambda ev, s: next(e for e in ev if e['type'] == 'rate_limit_event').__setitem__('rate_limit_info', 'allowed')),
        }
        for name, make in cases.items():
            with self.subTest(case=name):
                self.fresh()
                receipt = self.receipt(make)
                self.assertEqual((receipt['status'], len(self.state().cards)), ('ERROR', 0))
                self.assertIn('OVERAGE_OR_RATE_LIMIT', receipt['error'])
                for state in receipt['review']['rate_limit_states']:
                    self.assertTrue(all(v == 'UNKNOWN' or re.fullmatch(r'[a-z_]{1,40}', v) for v in state.values()))

    def test_absent_rate_limit_event_still_fails_closed(self):
        drop = mutated(lambda ev, s: ev.__setitem__(slice(None), [e for e in ev if e['type'] != 'rate_limit_event']))
        receipt = self.receipt(drop)
        self.assertEqual((receipt['status'], len(self.state().cards)), ('ERROR', 0))
        self.assertIn('NON_OVERAGE_NOT_EVIDENCED', receipt['error'])
        self.assertEqual(receipt['review']['rate_limit_states'], [])

    def test_one_warning_event_cannot_mask_a_later_overage_event(self):
        later = {'type': 'rate_limit_event', 'rate_limit_info': {'status': 'allowed', 'isUsingOverage': True, 'overageStatus': 'allowed'}}
        receipt = self.receipt(lambda s: stream(s, rate={'status': 'allowed_warning'}, extra=[{**later, 'session_id': s}]))
        self.assertEqual((receipt['status'], len(self.state().cards)), ('ERROR', 0))
        self.assertIn('OVERAGE_OR_RATE_LIMIT', receipt['error'])


class Faulty:
    """A raw handle whose flush or close raises once (fault injection); writes still reach the real file."""
    def __init__(self, real, steps):self.real, self.steps = real, steps
    def write(self, data):return self.real.write(data)
    def fileno(self):return self.real.fileno()
    def flush(self):
        if 'flush' in self.steps:raise OSError(28, 'fictional: no space left on device')
        self.real.flush()
    def close(self):
        self.real.close()  # the real descriptor is released, then the injected failure is reported
        if 'close' in self.steps:raise OSError(5, 'fictional: input/output error')


class RawCaptureFinaliseTests(Base):
    """Flush, fsync and close of the raw stdout file can fail after the one model invocation."""
    def finalise(self, *steps, receipt_fails=False):
        from unittest.mock import patch
        real_unlinked, real_fsync, opened = X.unlinked, X.os.fsync, {}
        class FaultyPath(type(Path())):
            def open(self, mode='r', *a, **k):
                real = super().open(mode, *a, **k)
                if 'x' not in mode or not self.name.endswith('-stdout.bin'):return real
                opened['stdout'] = real; return Faulty(real, steps)
        def fsync(fd):
            if 'fsync' in steps and 'stdout' in opened and not opened['stdout'].closed and fd == opened['stdout'].fileno():
                raise OSError(5, 'fictional: fsync failed')
            return real_fsync(fd)
        real_export = Archive.export
        def export(archive, name, value):
            if receipt_fails and name.startswith('exploratory-receipt-'):raise OSError(28, 'fictional: no space left on device')
            return real_export(archive, name, value)
        cli = FakeCLI(self)
        with patch.object(X, 'unlinked', lambda path: FaultyPath(real_unlinked(path))), patch.object(X.os, 'fsync', fsync),                 patch.object(X, 'review', side_effect=AssertionError('unverified raw output must never be parsed')),                 patch.object(Archive, 'export', export):
            try:return self.execute(cli), cli
            except S.ScoutError as error:return error, cli

    def assert_closed_error(self, receipt, cli, expected):
        self.assertEqual(cli.kinds().count('MODEL'), 1)  # never redispatched after a capture failure
        self.assertEqual((receipt['status'], receipt['model_invocations'], receipt['retried'], receipt['cards']), ('ERROR', 1, False, []))
        self.assertEqual(receipt['error'], 'RAW_CAPTURE_FINALISE_FAILED:' + expected)
        state = self.state()
        self.assertEqual((state.attempts['ATT-0001']['result']['status'], len(state.cards)), ('ERROR', 0))
        # Started, but the unparsed stream is no evidence that a request reached the provider.
        self.assertEqual((state.efforts[-1]['invocation_status'], receipt['process_start'], receipt['provider_request']), ('UNKNOWN', 'STARTED', 'UNKNOWN'))
        self.assertEqual(receipt['stdout_bytes'], (self.store / 'exports/exploratory-ATT-0001-stdout.bin').stat().st_size)
        st = X.status(self.store); self.assertEqual((st['claimed'], st['receipt'], st['interrupted']), (True, True, False))

    def test_flush_failure_records_error_without_parsing(self):
        self.assert_closed_error(*self.finalise('flush'), 'stdout:FLUSH:OSError')

    def test_fsync_failure_records_error_without_parsing(self):
        self.assert_closed_error(*self.finalise('fsync'), 'stdout:FSYNC:OSError')

    def test_close_failure_records_error_without_parsing(self):
        self.assert_closed_error(*self.finalise('close'), 'stdout:CLOSE:OSError')

    def test_every_step_is_attempted_once_and_all_failures_are_named(self):
        self.assert_closed_error(*self.finalise('flush', 'fsync', 'close'), 'stdout:FLUSH:OSError,stdout:FSYNC:OSError,stdout:CLOSE:OSError')

    def test_unwritable_receipt_keeps_the_claim_and_reports_interrupted(self):
        error, cli = self.finalise('fsync', receipt_fails=True)
        self.assertIsInstance(error, S.ScoutError); self.assertTrue(str(error).startswith('INTERRUPTED: receipt not written'))
        self.assertEqual(cli.kinds().count('MODEL'), 1)
        st = X.status(self.store)
        self.assertEqual((st['claimed'], st['receipt'], st['interrupted'], st['attempts'], st['cards']), (True, False, True, {'ATT-0001': 'ERROR'}, []))
        auth = sorted(self.base.glob('authorisation-*.json'))[-1]
        with self.assertRaises(S.ScoutError):X.run(self.store, auth, host=self.host)  # an interrupted claim is never resumed
        self.assertEqual(cli.kinds().count('MODEL'), 1)


class OutputLimitTests(Base):
    """The real bounded capture runs against local children in tests/test_scout_exploratory_capture_process_assurance.py."""
    def test_unconfirmed_tree_stop_is_recorded_as_such(self):
        def runner(args, **kwargs):
            if '--print' not in args:return fake(args, **kwargs)
            kwargs['stdout'].write(b'x' * 10); raise X.OutputLimitExceeded(args, 10, 'PROCESS_TREE_STOP_UNCONFIRMED')
        fake = FakeCLI(self); result = self.planned(); self.host.runner = runner
        receipt = X.run(self.store, self.authorise(result), host=self.host)
        self.assertEqual((receipt['status'], receipt['error'], receipt['stdout_bytes']),
                         ('ERROR', 'RUN_STOP:RECORDING_SIZE_LIMIT:PROCESS_TREE_STOP_UNCONFIRMED', 10))

    def test_stderr_sink_failure_fails_closed_even_with_a_valid_stream(self):
        """The real capture() pumps over a fake Popen (no process): stdout carries a fully valid stream, the stderr
        raw file refuses writes. The worker failure must reach the supervisor and nothing may be admitted."""
        import hashlib, io
        from unittest.mock import patch
        class Proc:
            pid, returncode = 4242, 0
            def __init__(self, args, **kwargs):
                session = args[args.index('--session-id') + 1]
                self.stdout, self.stderr = io.BufferedReader(io.BytesIO(stream(session))), io.BufferedReader(io.BytesIO(b'fictional warning'))
                self.stdin = io.BytesIO()
            def poll(self):return 0
            def wait(self, timeout=None):return 0
            def kill(self):pass
        class Refusing:
            def __init__(self, real):self.real = real
            def write(self, data):raise OSError(28, 'fictional: no space left on device')
            def __getattr__(self, name):return getattr(self.real, name)
        stops, fake = [], FakeCLI(self)
        def runner(args, **kwargs):
            if '--print' not in args:return fake(args, **kwargs)
            fake.calls.append((list(args), kwargs))
            return X.capture(args, **{**kwargs, 'stderr': Refusing(kwargs['stderr'])})
        result = self.planned(); self.host.runner = runner
        with patch.object(X.subprocess, 'Popen', Proc), patch.object(X, 'stop_tree', lambda proc: stops.append(proc.pid) or True), \
                patch.object(X, 'review', side_effect=AssertionError('a failed capture must never be parsed')):
            receipt = X.run(self.store, self.authorise(result), host=self.host)
        self.assertEqual((receipt['status'], receipt['error'], receipt['cards']),
                         ('ERROR', 'RUN_STOP:RAW_CAPTURE_WORKER_FAILED:stderr:WRITE:OSError:PROCESS_TREE_STOPPED', []))
        self.assertEqual((stops, len(self.state().cards), self.state().attempts['ATT-0001']['result']['status']), ([4242], 0, 'ERROR'))
        raw = self.store / 'exports/exploratory-ATT-0001-stdout.bin'  # bytes written before the failure are retained
        self.assertEqual((receipt['stdout_bytes'], receipt['stdout_sha256']), (raw.stat().st_size, hashlib.sha256(raw.read_bytes()).hexdigest()))
        self.assertEqual(receipt['stderr_bytes'], 0)
        auth = sorted(self.base.glob('authorisation-*.json'))[-1]
        with self.assertRaises(S.ScoutError):X.run(self.store, auth, host=self.host)  # consumed, never retried
        self.assertEqual(fake.kinds().count('MODEL'), 1)


class ProcessStartAccountingTests(Base):
    """A launch attempt is not a model invocation: receipt, effort record and status agree on what is evidenced."""
    def launch(self, behave):
        """Run with a model call replaced by ``behave(args, kwargs)``; returns (receipt or exception, cli)."""
        cli = FakeCLI(self)
        def runner(args, **kwargs):
            if '--print' not in args:return cli(args, **kwargs)
            cli.calls.append((list(args), kwargs)); return behave(args, kwargs)
        result = self.planned(); self.host.runner = runner
        try:return X.run(self.store, self.authorise(result), host=self.host), cli
        except BaseException as error:return error, cli

    def agree(self, receipt, process, request, invocation, models):
        self.assertEqual((receipt['process_start'], receipt['provider_request'], receipt['invocation_status'], receipt['model_invocations'],
                          receipt['process_start_attempts']), (process, request, invocation, models, 1))
        effort = self.state().efforts[-1]
        self.assertEqual(effort['invocation_status'], invocation); self.assertIn(f'Process start {process}', effort['description'])
        st = X.status(self.store)
        self.assertEqual((st['process_start'], st['invocation_status'], st['accounting_agrees'], st['interrupted']), (process, invocation, True, False))

    def assert_consumed(self, cli):
        auth = sorted(self.base.glob('authorisation-*.json'))[-1]
        with self.assertRaises(S.ScoutError):X.run(self.store, auth, host=self.host)
        self.assertEqual(cli.kinds().count('MODEL'), 1)

    def test_failed_process_creation_is_not_an_invocation(self):
        receipt, cli = self.launch(lambda a, k: (_ for _ in ()).throw(FileNotFoundError(2, 'fictional: no such executable')))
        self.assertEqual((receipt['status'], receipt['error']), ('ERROR', 'PROCESS_START_FAILED'))
        self.agree(receipt, 'START_ATTEMPTED', 'NOT_SENT', 'NOT_INVOKED', 0)
        self.assertTrue((self.store / 'exports/exploratory-dispatch-ATT-0001.json').is_file())
        self.assertFalse((self.store / 'exports/exploratory-started-ATT-0001.json').exists())
        self.assert_consumed(cli)

    def test_successful_launch_with_request_evidence_is_invoked(self):
        receipt = self.execute(FakeCLI(self))
        self.assertEqual(receipt['status'], 'VALID')
        self.agree(receipt, 'STARTED', 'VISIBLE_REQUEST_ID', 'INVOKED', 1)
        marker = json.loads((self.store / 'exports/exploratory-started-ATT-0001.json').read_text(encoding='utf-8'))
        self.assertEqual(marker['pid'], 4242)

    def test_started_process_without_request_evidence_stays_unknown(self):
        receipt = self.execute(FakeCLI(self, model_stream=lambda s: b'not json\n'))
        self.assertEqual(receipt['status'], 'ERROR')
        self.agree(receipt, 'STARTED', 'UNKNOWN', 'UNKNOWN', 1)

    def test_timeout_after_start_is_final_and_provider_reach_unknown(self):
        def hang(args, kwargs):
            kwargs['on_start'](4242); kwargs['stdout'].write(b'{"type":"system"'); raise subprocess.TimeoutExpired(args, 1)
        receipt, cli = self.launch(hang)
        self.assertEqual(receipt['status'], 'ERROR'); self.assertIn('TIMEOUT', receipt['error'])
        self.agree(receipt, 'STARTED', 'UNKNOWN', 'UNKNOWN', 1)
        self.assert_consumed(cli)

    def test_ambiguous_launch_failure_is_unknown_and_consumed(self):
        receipt, cli = self.launch(lambda a, k: (_ for _ in ()).throw(subprocess.SubprocessError('fictional: child setup')))
        self.assertEqual((receipt['status'], receipt['error']), ('ERROR', 'PROCESS_START_UNKNOWN:SubprocessError'))
        self.agree(receipt, 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN')
        self.assert_consumed(cli)

    def test_interruption_during_launch_reports_unknown_without_a_receipt(self):
        error, cli = self.launch(lambda a, k: (_ for _ in ()).throw(KeyboardInterrupt()))
        self.assertIsInstance(error, KeyboardInterrupt)
        st = X.status(self.store)
        self.assertEqual((st['claimed'], st['receipt'], st['interrupted'], st['process_start'], st['invocation_status'], st['accounting_agrees']),
                         (True, False, True, 'UNKNOWN', 'UNKNOWN', True))
        self.assert_consumed(cli)

    def test_interruption_after_start_reports_started_without_a_receipt(self):
        def interrupted(args, kwargs):kwargs['on_start'](4242); raise KeyboardInterrupt()
        error, cli = self.launch(interrupted)
        self.assertIsInstance(error, KeyboardInterrupt)
        st = X.status(self.store)
        self.assertEqual((st['interrupted'], st['process_start'], st['invocation_status'], st['accounting_agrees']), (True, 'STARTED', 'UNKNOWN', True))
        self.assert_consumed(cli)

    def test_unwritable_start_marker_stops_the_new_process_tree(self):
        from unittest.mock import patch
        killed, real_export = [], Archive.export
        class Proc:
            pid = 4242
            def kill(self):pass
        def export(archive, name, value):
            if name.startswith('exploratory-started-'):raise OSError(28, 'fictional: no space left on device')
            return real_export(archive, name, value)
        with patch.object(X.subprocess, 'Popen', lambda *a, **k: Proc()), patch.object(X, 'stop_tree', killed.append), \
                patch.object(Archive, 'export', export):
            receipt, cli = self.launch(lambda args, kwargs: X.capture(args, **kwargs))
        self.assertEqual(len(killed), 1)
        self.assertEqual(receipt['error'], 'DISPATCH_FAILED_AFTER_START:OSError')
        self.assertEqual((receipt['process_start'], receipt['invocation_status']), ('STARTED', 'UNKNOWN'))
        st = X.status(self.store); self.assertEqual((st['process_start'], st['accounting_agrees']), ('STARTED', True))  # dispatch marker only

    def test_status_flags_records_that_disagree(self):
        self.execute(FakeCLI(self))
        (self.store / 'exports/exploratory-started-ATT-0001.json').unlink()
        (self.store / 'exports/exploratory-dispatch-ATT-0001.json').unlink()
        st = X.status(self.store)
        self.assertFalse(st['accounting_agrees']); self.assertIn('process start contradicts dispatch markers', st['disagreements'])

    def test_unclaimed_archive_reports_not_started(self):
        self.planned()
        st = X.status(self.store)
        self.assertEqual((st['process_start'], st['invocation_status'], st['accounting_agrees']), ('NOT_STARTED', 'NOT_INVOKED', True))


class BoundaryTests(unittest.TestCase):
    def test_runner_is_outside_the_frozen_v004_and_r3_closures(self):
        for closure in (v004_package.implementation(), R3.implementation()):
            self.assertFalse([p for p in closure if 'exploratory_v001' in p])

    def test_cli_status_and_bad_plan_start_no_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / 'archive'
            self.assertEqual(main(['plan', str(store), '--title', 't', '--model', 'opus', '--executable', str(Path(tmp) / 'none.exe')]), 2)
            self.assertFalse(store.exists() and any(store.iterdir()))
