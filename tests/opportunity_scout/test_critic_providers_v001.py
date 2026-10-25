"""Critic provider adapters V001: offline only. Fictional Codex JSONL streams and Gemini responses in each provider's
own documented vocabulary; no process, network, credential or real account directory is touched."""
import email.message
import io
import json
import unittest
import urllib.parse
import urllib.request
import urllib.response

from src.research.opportunity_scout import claude_subscription as CS, schema as S
from src.research.opportunity_scout.automation_v001 import credentials as CR, providers as V
from src.research.opportunity_scout.storage import ROOT

REPLY = 'Preface.\n\n```json\n{"schema": "SCOUT_CRITIC_OUTPUT_V002"}\n```\n'
MODEL = 'gpt-6-sol'


def codex_stream(*, items=None, usage=None, extra=(), model=None, terminal='turn.completed'):
    usage = usage if usage is not None else {'input_tokens': 7000, 'cached_input_tokens': 0, 'output_tokens': 2500, 'reasoning_output_tokens': 900}
    items = items if items is not None else [{'id': 'item_0', 'type': 'reasoning', 'text': 'fictional'},
                                             {'id': 'item_1', 'type': 'agent_message', 'text': REPLY}]
    events = [{'type': 'thread.started', 'thread_id': 'thread-fictional', **({'model': model} if model else {})}, {'type': 'turn.started'}]
    for it in items:events += [{'type': 'item.started', 'item': it}, {'type': 'item.completed', 'item': it}]
    events += list(extra) + [{'type': terminal, **({'usage': usage} if terminal == 'turn.completed' else {'error': {'message': 'x'}})}]
    return ''.join(json.dumps(e) + '\n' for e in events).encode('utf-8')


def gemini_body(*, text=REPLY, finish='STOP', model='gemini-4-argon-001', parts=None, candidates=1, usage=None, extra=None):
    usage = usage if usage is not None else {'promptTokenCount': 7000, 'candidatesTokenCount': 2500, 'thoughtsTokenCount': 1500, 'totalTokenCount': 11000}
    c = {'content': {'role': 'model', 'parts': parts if parts is not None else [{'text': text}]}, 'finishReason': finish}
    body = {'candidates': [c] * candidates, 'usageMetadata': usage, 'modelVersion': model, 'responseId': 'resp-fictional', **(extra or {})}
    return json.dumps(body).encode('utf-8')


PRICES = {'input_usd_per_million': 2.0, 'output_usd_per_million': 10.0, 'source': 'fixture', 'as_of': '2026-10-24'}


class CodexTests(unittest.TestCase):
    def review(self, data, **kw):
        return V.codex_review(data, b'', kw.pop('code', 0), kw.pop('timed_out', False), MODEL, **kw)

    def test_single_agent_message_with_accepted_requested_identity_is_returned_unchanged(self):
        reply, facts = self.review(codex_stream(), accept_requested_identity=True)
        self.assertEqual(reply, REPLY.encode('utf-8'))
        self.assertEqual((facts['faults'], facts['model_identity_basis'], facts['billing_path']), ([], 'REQUESTED_ONLY', 'CHATGPT_SUBSCRIPTION'))
        self.assertEqual(facts['usage']['reasoning_output_tokens'], 900)

    def test_unobserved_model_identity_is_a_fault_by_default(self):
        reply, facts = self.review(codex_stream())
        self.assertIsNone(reply); self.assertIn('MODEL_IDENTITY_NOT_OBSERVED', facts['faults'])
        reply, facts = self.review(codex_stream(model=MODEL))
        self.assertEqual((facts['faults'], facts['model_identity_basis']), ([], 'OBSERVED_IN_STREAM'))

    def test_tool_search_file_and_plan_items_and_stream_deviations_fail_closed(self):
        msg = {'id': 'item_9', 'type': 'agent_message', 'text': REPLY}
        cases = {
            'shell command': ([{'id': 'i', 'type': 'command_execution', 'command': 'dir'}, msg], {}, 'PROHIBITED_OR_UNKNOWN_ITEM:command_execution'),
            'web search': ([{'id': 'i', 'type': 'web_search', 'query': 'x'}, msg], {}, 'PROHIBITED_OR_UNKNOWN_ITEM:web_search'),
            'file change': ([{'id': 'i', 'type': 'file_change'}, msg], {}, 'PROHIBITED_OR_UNKNOWN_ITEM:file_change'),
            'mcp call': ([{'id': 'i', 'type': 'mcp_tool_call'}, msg], {}, 'PROHIBITED_OR_UNKNOWN_ITEM:mcp_tool_call'),
            'plan': ([{'id': 'i', 'type': 'todo_list'}, msg], {}, 'PROHIBITED_OR_UNKNOWN_ITEM:todo_list'),
            'two messages': ([msg, {**msg, 'id': 'item_10'}], {}, 'NOT_EXACTLY_ONE_AGENT_MESSAGE'),
            'same message ID completed twice': ([msg, {**msg, 'text': 'replacement'}], {}, 'DUPLICATE_ITEM_COMPLETION'),
            'no message': ([{'id': 'i', 'type': 'reasoning', 'text': 'x'}], {}, 'NOT_EXACTLY_ONE_AGENT_MESSAGE'),
            'second turn': (None, {'extra': [{'type': 'turn.started'}]}, 'NOT_EXACTLY_ONE_TURN'),
            'failed turn': (None, {'terminal': 'turn.failed'}, 'PROVIDER_ERROR_EVENT'),
            'unknown event': (None, {'extra': [{'type': 'session.compacted'}]}, 'UNRECOGNISED_EVENT'),
            'usage missing': (None, {'usage': {}}, 'USAGE_UNKNOWN'),
            'model fallback': (None, {'model': 'gpt-5.5'}, 'MODEL_MISMATCH')}
        for name, (items, kw, code) in cases.items():
            with self.subTest(case=name):
                reply, facts = self.review(codex_stream(items=items, **kw), accept_requested_identity=True)
                self.assertIsNone(reply); self.assertIn(code, facts['faults'])

    def test_duplicate_completion_of_one_agent_message_id_never_passes(self):
        first = {'id': 'item_1', 'type': 'agent_message', 'text': REPLY}
        for second in (first, {**first, 'text': 'a different final text'}):
            with self.subTest(same_text=second is first):
                reply, facts = self.review(codex_stream(items=[first, second], model=MODEL), accept_requested_identity=True)
                self.assertIsNone(reply)
                self.assertTrue({'DUPLICATE_ITEM_COMPLETION', 'NOT_EXACTLY_ONE_AGENT_MESSAGE'} <= set(facts['faults']))
                self.assertEqual(facts['agent_messages'], 2)

    def test_process_outcomes_and_raw_secrets_fail_closed(self):
        for kw, code in (({'timed_out': True}, 'TIMEOUT'), ({'code': 1}, 'NONZERO_EXIT')):
            with self.subTest(code=code):
                self.assertIn(code, self.review(codex_stream(), accept_requested_identity=True, **kw)[1]['faults'])
        leak = codex_stream(items=[{'id': 'm', 'type': 'agent_message', 'text': REPLY + ' Bearer abc123'}])
        self.assertIn('CREDENTIAL_LIKE_PATTERN_IN_RAW_STREAM', self.review(leak, accept_requested_identity=True)[1]['faults'])
        self.assertIn('INVALID_STREAM_ENVELOPE', self.review(b'not json\n', accept_requested_identity=True)[1]['faults'])

    def test_environment_arguments_and_preflight(self):
        env = V.codex_environment({'PATH': '/bin', 'OPENAI_API_KEY': 'sk-fictional', 'CODEX_API_KEY': 'x'}, '/codex-home')
        self.assertEqual(env, {'PATH': '/bin', 'CODEX_HOME': '/codex-home'})
        args = V.codex_arguments('codex.exe', MODEL, 'xhigh', '/tmp/empty')
        self.assertEqual(args[1:3], ['exec', '--json']); self.assertIn('web_search="disabled"', args)
        self.assertNotIn('--output-schema', args); self.assertEqual(args[-2:], ['--cd', '/tmp/empty'])  # no positional prompt: stdin
        for bad in ('gpt', 'GPT-6', 'claude-opus-5-5'):
            with self.subTest(model=bad), self.assertRaises(S.ScoutError):V.codex_arguments('codex.exe', bad, 'xhigh', '/t')
        help_text = ' '.join(V.CODEX_FLAGS)
        def admin(login):return lambda a: {'--version': 'codex-cli 0.164.0\n', 'login': login, 'exec': help_text}[a[0]]
        self.assertEqual(V.codex_preflight(admin('Logged in using ChatGPT\n'), 'a' * 64, 'a' * 64)['auth'], 'CHATGPT_LOGIN')
        for login, sha in (('Logged in using an API key - sk-...\n', 'a' * 64), ('Not logged in\n', 'a' * 64), ('Logged in using ChatGPT\n', 'b' * 64)):
            with self.subTest(login=login, sha=sha[0]), self.assertRaises(S.ScoutError):V.codex_preflight(admin(login), 'a' * 64, sha)


class GeminiTests(unittest.TestCase):
    def review(self, body, status=200):return V.gemini_review(status, body, 'gemini-4-argon', PRICES)

    def test_single_stop_candidate_is_returned_with_observed_identity_and_cost_estimate(self):
        reply, facts = self.review(gemini_body())
        self.assertEqual((reply, facts['faults']), (REPLY.encode('utf-8'), []))
        self.assertEqual((facts['model_returned'], facts['model_identity_basis']), ('gemini-4-argon-001', 'OBSERVED_IN_RESPONSE'))
        self.assertAlmostEqual(facts['cost_estimate_usd_documented_prices'], (7000 * 2 + 4000 * 10) / 1e6)
        self.assertEqual(facts['charge'], S.UNKNOWN)

    def test_deviations_fail_closed(self):
        cases = {'max tokens': (gemini_body(finish='MAX_TOKENS'), 200, 'UNFINISHED_OR_STOPPED:MAX_TOKENS'),
                 'safety stop': (gemini_body(finish='SAFETY'), 200, 'UNFINISHED_OR_STOPPED:SAFETY'),
                 'function call': (gemini_body(parts=[{'functionCall': {'name': 'x'}}]), 200, 'PROHIBITED_OR_UNKNOWN_PART'),
                 'thought part': (gemini_body(parts=[{'text': 'hidden', 'thought': True}, {'text': REPLY}]), 200, 'PROHIBITED_OR_UNKNOWN_PART'),
                 'two candidates': (gemini_body(candidates=2), 200, 'NOT_EXACTLY_ONE_CANDIDATE'),
                 'no candidate': (gemini_body(candidates=0), 200, 'NOT_EXACTLY_ONE_CANDIDATE'),
                 'other model': (gemini_body(model='gemini-3.8-flash'), 200, 'MODEL_MISMATCH_OR_UNKNOWN'),
                 'blocked': (gemini_body(extra={'promptFeedback': {'blockReason': 'SAFETY'}}), 200, 'PROMPT_BLOCKED'),
                 'usage unknown': (gemini_body(usage={}), 200, 'USAGE_UNKNOWN'),
                 'credits exhausted': (b'{"error": {"code": 402}}', 402, 'HTTP_402'),
                 'rate limited': (b'{"error": {"code": 429}}', 429, 'HTTP_429'),
                 'not json': (b'<html>', 200, 'INVALID_RESPONSE_ENVELOPE')}
        for name, (body, status, code) in cases.items():
            with self.subTest(case=name):
                reply, facts = self.review(body, status)
                self.assertIsNone(reply); self.assertIn(code, facts['faults'])

    def test_absent_thinking_count_is_unknown_not_zero(self):
        reply, facts = self.review(gemini_body(usage={'promptTokenCount': 7000, 'candidatesTokenCount': 2500, 'totalTokenCount': 9500}))
        self.assertEqual((facts['usage']['thoughtsTokenCount'], facts['cost_estimate_usd_documented_prices']), (S.UNKNOWN, S.UNKNOWN))

    def test_request_shape_and_worst_case_bound(self):
        body = V.gemini_request('prompt', max_output_tokens=8192, thinking_level='high')
        self.assertEqual(body['generationConfig'], {'maxOutputTokens': 8192, 'thinkingConfig': {'thinkingLevel': 'high'}})
        self.assertNotIn('candidateCount', json.dumps(body))  # the Argon guide says remove it; unset defaults to one
        self.assertEqual(body['contents'], [{'role': 'user', 'parts': [{'text': 'prompt'}]}])  # one user turn, the prompt only
        self.assertNotIn('tools', body); self.assertNotIn('systemInstruction', body)
        self.assertAlmostEqual(V.worst_case_cost(25000, 8192, PRICES), (25000 * 2 + 8192 * 10) / 1e6)


ATTACKER = 'https://attacker.invalid/collect'
KEY = 'AIzaFICTIONAL-redirect-test-key'


class FakeOrigins(urllib.request.HTTPSHandler):
    """Offline origin simulator: no socket. The documented host answers ``code`` (a redirect to another origin unless
    None); every other origin answers 200. Records each request's host and headers."""
    def __init__(self, code=302, location=ATTACKER):
        super().__init__()
        self.code, self.location, self.seen = code, location, []

    def https_open(self, req):
        host = urllib.parse.urlsplit(req.full_url).hostname
        self.seen.append((host, {k.lower(): v for k, v in req.header_items()}))
        headers = email.message.Message()
        if host == V.GEMINI_HOST and self.code:headers['Location'] = self.location; code, body = self.code, b''
        else:code, body = 200, gemini_body()
        response = urllib.response.addinfourl(io.BytesIO(body), headers, req.full_url, code)
        response.msg = 'fixture'
        return response


class TransportTests(unittest.TestCase):
    URL = V.GEMINI_ENDPOINT.format(model='gemini-4-argon')

    def send(self, origins, url=None):
        return V.https_transport(url or self.URL, {'Content-Type': 'application/json', 'x-goog-api-key': KEY}, b'{}', 5, handlers=(origins,))

    def test_plain_urllib_would_forward_the_key_to_a_cross_origin_redirect(self):
        """Control: shows the threat is real, so the refusal below is meaningful."""
        origins = FakeOrigins()
        request = urllib.request.Request(self.URL, data=b'{}', headers={'x-goog-api-key': KEY}, method='POST')
        with urllib.request.build_opener(origins).open(request, timeout=5) as response:self.assertEqual(response.status, 200)
        self.assertEqual([h for h, _ in origins.seen], [V.GEMINI_HOST, 'attacker.invalid'])
        self.assertEqual(origins.seen[1][1].get('x-goog-api-key'), KEY)

    def test_every_redirect_is_refused_before_any_cross_origin_request(self):
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                origins = FakeOrigins(code)
                with self.assertRaises(S.ScoutError) as caught:self.send(origins)
                self.assertEqual(str(caught.exception), f'GEMINI_REDIRECT_REFUSED:HTTP_{code}')
                self.assertEqual([h for h, _ in origins.seen], [V.GEMINI_HOST])  # attacker.invalid never contacted
                self.assertFalse(any(KEY in str(headers) for host, headers in origins.seen if host != V.GEMINI_HOST))
        origins = FakeOrigins(302, location='https://generativelanguage.googleapis.com/v1beta/other')
        with self.assertRaises(S.ScoutError):self.send(origins)  # same-origin redirects are refused too
        self.assertEqual(len(origins.seen), 1)

    def test_only_the_documented_https_host_is_sent_the_key(self):
        for url in (ATTACKER, 'http://generativelanguage.googleapis.com/v1beta/models/x:generateContent',
                    'https://generativelanguage.googleapis.com.attacker.invalid/x', 'https://user@generativelanguage.googleapis.com/x',
                    'https://generativelanguage.googleapis.com:8443/x'):
            with self.subTest(url=url):
                origins = FakeOrigins(None)
                with self.assertRaises(S.ScoutError):self.send(origins, url)
                self.assertEqual(origins.seen, [])
        origins = FakeOrigins(None)
        self.assertEqual(self.send(origins), (200, gemini_body()))
        self.assertEqual(len(origins.seen), 1)


class RoleTests(unittest.TestCase):
    def test_roles_bind_provider_family_model_and_billing(self):
        codex = {'provider': 'CODEX_CLI', 'family': 'openai', 'model': MODEL, 'effort': 'xhigh', 'accept_requested_identity': False, 'executable_sha256': 'a' * 64}
        gemini = {'provider': 'GEMINI_API', 'family': 'google', 'model': 'gemini-4-argon', 'prices': PRICES, 'api_key_env': 'GEMINI_API_KEY',
                  'max_output_tokens': 8192, 'thinking_level': 'high'}
        for role in (codex, gemini, {'provider': 'ANTIGRAVITY_CONSUMER', 'family': 'google'}):V.validate_role(role)
        bad = [{**codex, 'family': 'anthropic'}, {**codex, 'model': 'claude-opus-5-5'}, {**codex, 'accept_requested_identity': 'yes'},
               {**gemini, 'prices': {}}, {**gemini, 'api_key_env': 'AIza-not-a-variable-name'}, {'provider': 'BROWSER'}]
        for role in bad:
            with self.subTest(role=role), self.assertRaises(S.ScoutError):V.validate_role(role)


# Fictional credential shapes, assembled at runtime so no key-shaped literal is committed.
FAKE_JWT = '.'.join(['eyJhbGciOiJIUzI1NiJ9', 'eyJzdWIiOiJmaWN0aW9uYWwifQ', 'FICTIONALsignature'])
FAKE_GOOGLE = 'AIza' + 'FICTIONALfictional_key-' + 'x' * 12
FAKE_OPENAI = 'sk-' + 'proj-' + 'FICTIONALfictionalFICTIONAL'
PROSE = ('The cost bearer remains the contractor.', 'An identifiable economic bearer exists that could in principle be linked.',
         'No bearer of the consequence could be linked to any investable exposure.', 'The risk-bearer counter-intuitively shifts.',
         'The economic bearer UNKNOWN in the card.', 'BEARER OF RISK: the processor', 'the final\tbearer\nremains unclear',
         'Bearers of cost vary.', 'Authorization: the owner must approve it.', 'Authorisation: PENDING_APPROVAL.')


class CredentialScreenTests(unittest.TestCase):
    """Screen V002 (Forge Pilot 001 correction): ordinary prose about economic bearers passes; credentials still fail."""
    def gemini(self, text):return V.gemini_review(200, gemini_body(text=REPLY + text), 'gemini-4-argon', PRICES)

    def test_economic_bearer_prose_and_the_frozen_rubrics_pass_where_v001_rejected_them(self):
        rubrics = [p.read_text(encoding='utf-8') for p in sorted((ROOT / 'src/research/opportunity_scout/critic_v1/resources').glob('*.md'))]
        self.assertTrue(any(CS.safe_output(r) != r for r in rubrics))  # the V001 defect: the frozen economic rubric itself matched
        for text in PROSE + tuple(rubrics):
            with self.subTest(text=text[:40]):
                self.assertEqual(CR.screen(text), [])
                reply, facts = self.gemini(text)
                self.assertEqual((facts['faults'], facts['credential_screen']), ([], {'version': CR.VERSION, 'categories': []}))
                self.assertIsNotNone(reply)

    def test_token_shaped_bearer_values_are_credentials_without_requiring_digits(self):
        cases = ['Bearer abcDEFghiJKL', 'bearer FICTIONALtokenValue', 'BEARER ' + FAKE_JWT, 'Bearer  \tZmljdGlvbmFsLXRva2Vu==',
                 'bearer\nxyzzyplughfictionalwordtoken', 'Bearer abc123', 'Bearer "QuotedFICTIONALtoken"', 'bearer `ya29.FICTIONAL`',
                 'the cost-bearer ab/cd+ef', 'BeArEr Abcdefghijklmnopqrstuvwxyz']
        for text in cases:
            with self.subTest(text=text):
                self.assertIn('BEARER_TOKEN', CR.screen(text))
                reply, facts = self.gemini(text)
                self.assertIsNone(reply); self.assertIn('CREDENTIAL_LIKE_PATTERN_IN_RAW_RESPONSE', facts['faults'])
        self.assertFalse(any(c.isdigit() for c in cases[0] + cases[1]))  # flagged without any digit

    def test_authorization_headers_json_credential_keys_and_provider_key_shapes_are_credentials(self):
        cases = {'Authorization: Basic RklDVElPTkFMOmZpY3Rpb25hbA==': 'AUTHORIZATION_HEADER',
                 'proxy-authorization:Token FICTIONALtoken42': 'AUTHORIZATION_HEADER',
                 'AUTHORIZATION: abcDEFfictional': 'AUTHORIZATION_HEADER',
                 'Authorization: Bearer ' + FAKE_JWT: 'BEARER_TOKEN',
                 '{"access_token": "x"}': 'CREDENTIAL_JSON_KEY', '{"API_KEY" : 1}': 'CREDENTIAL_JSON_KEY',
                 '"x-goog-api-key":"y"': 'CREDENTIAL_JSON_KEY', '"Authorization": "z"': 'CREDENTIAL_JSON_KEY',
                 'token sk-ant-fictional': 'ANTHROPIC_KEY_PREFIX', 'SK-ANT-FICTIONAL': 'ANTHROPIC_KEY_PREFIX',
                 'key ' + FAKE_OPENAI: 'OPENAI_STYLE_KEY', 'key=' + FAKE_GOOGLE: 'GOOGLE_API_KEY'}
        for text, label in cases.items():
            with self.subTest(label=label, text=text[:30]):
                self.assertIn(label, CR.screen(text))
                self.assertIn('CREDENTIAL_LIKE_PATTERN_IN_RAW_RESPONSE', self.gemini(text)[1]['faults'])
        for text in ('a task-based desk review', 'the AIza prefix alone', 'Authorization: Basic', 'the "authorisation": field'):
            with self.subTest(benign=text):self.assertEqual(CR.screen(text), [])

    def test_json_escaped_values_are_screened_decoded_and_records_never_hold_a_value(self):
        escaped = gemini_body(text=REPLY + 'Echoed config {"api_key": "FICTIONALvalue"}')
        self.assertNotIn(b'"api_key":', escaped)  # only its JSON-escaped form is in the raw body
        reply, facts = V.gemini_review(200, escaped, 'gemini-4-argon', PRICES)
        self.assertIsNone(reply); self.assertEqual(facts['credential_screen']['categories'], ['CREDENTIAL_JSON_KEY'])
        secret = 'FICTIONALtokenNeverRecorded'
        for facts in (self.gemini('Bearer ' + secret)[1],
                      V.codex_review(codex_stream(items=[{'id': 'm', 'type': 'agent_message', 'text': REPLY + 'Bearer ' + secret}]),
                                     b'', 0, False, MODEL, accept_requested_identity=True)[1]):
            self.assertEqual(facts['credential_screen'], {'version': CR.VERSION, 'categories': ['BEARER_TOKEN']})
            self.assertNotIn(secret, json.dumps(facts))
        deep = ('[' * 5000) + (']' * 5000)  # nesting beyond the JSON parser's limit is screened raw, never a crash
        self.assertEqual(CR.screen(deep), [])
        self.assertEqual(CR.screen(json.dumps({'a': [[[{'b': 'Bearer ' + secret}]]]})), ['BEARER_TOKEN'])
