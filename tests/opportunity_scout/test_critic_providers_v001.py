"""Critic provider adapters V001: offline only. Fictional Codex JSONL streams and Gemini responses in each provider's
own documented vocabulary; no process, network, credential or real account directory is touched."""
import json
import unittest

from src.research.opportunity_scout import schema as S
from src.research.opportunity_scout.automation_v001 import providers as V

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
        self.assertEqual(body['generationConfig'], {'candidateCount': 1, 'maxOutputTokens': 8192, 'thinkingConfig': {'thinkingLevel': 'high'}})
        self.assertNotIn('tools', body); self.assertNotIn('systemInstruction', body)
        self.assertAlmostEqual(V.worst_case_cost(25000, 8192, PRICES), (25000 * 2 + 8192 * 10) / 1e6)


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
