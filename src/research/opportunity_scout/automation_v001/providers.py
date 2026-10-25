"""Critic provider adapters V001: one frozen critic prompt in, the model's final reply bytes out, nothing else.

Each provider has its own environment, preflight and fail-closed response review; no Claude stream assumption is
reused. An adapter never repairs, retries, continues, falls back or substitutes a model. It returns the reply bytes
unchanged plus allowlisted facts; the AI Critic V1 importer (unchanged) then judges the reply. Faults mean the reply
is never imported. Every raw stream or body passes the credential screen (``credentials``, V002 since Forge Pilot 001;
its version and category labels are recorded, never a value). Nothing here runs on import, and offline tests inject
every process and transport.

* CODEX_CLI (OpenAI Codex CLI ``codex exec``): ChatGPT-login subscription only; API-key variables never reach it.
  Read-only sandbox, ephemeral session, user config and rules ignored, web search disabled; any command, file,
  MCP, web-search or plan item is a fault. The ``--json`` event profile is the documented one and has not been
  observed live here: unknown events fail closed, and a model identity the stream does not report is a fault unless
  the owner explicitly accepted requested-only identity.
* GEMINI_API (Gemini API ``generateContent``): one HTTPS request, never redirected, no tools, one candidate. Paid billing only, under
  an owner spend cap checked before dispatch against documented prices; the key is read from the named environment
  variable at dispatch and never stored.
* ANTIGRAVITY_CONSUMER: Google's consumer FAQ does not support wrapping ``agy`` in third-party applications, so this
  route always returns PROVIDER_UNAVAILABLE_OR_NOT_AUTHORISED and is never launched."""
from __future__ import annotations

import json
import math
import re

from src.research.spec import digest
from .. import schema as S
from ..v004_runtime import OS_ENV
from . import credentials as CR

VERSION = 'SCOUT_CRITIC_PROVIDERS_V002'  # V002: credential screen V002 replaces safe_output (Forge Pilot 001 correction)
CODEX, GEMINI, ANTIGRAVITY = 'CODEX_CLI', 'GEMINI_API', 'ANTIGRAVITY_CONSUMER'
PROVIDERS = (CODEX, GEMINI, ANTIGRAVITY)
UNAVAILABLE = 'PROVIDER_UNAVAILABLE_OR_NOT_AUTHORISED'
FAMILIES = {CODEX: 'openai', GEMINI: 'google', ANTIGRAVITY: 'google'}
MAX_REPLY_BYTES = 1024 * 1024  # the critic importer's own raw ceiling
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


def fault_list():
    faults = []
    def fault(code):
        if code not in faults:faults.append(code)
    return faults, fault


def credential_screen(fault, code, *blobs):
    """Screen V002 over the raw bytes; a hit is a fault. The record carries the version and labels, never a value."""
    found = CR.screen(*blobs)
    if found:fault(code)
    return {'version': CR.VERSION, 'categories': found}


# ----------------------------------------------------------------------------------------------- Codex CLI

CODEX_FORBIDDEN_ENV = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_ORG_ID', 'OPENAI_ORGANIZATION',
                       'OPENAI_PROJECT', 'AZURE_OPENAI_API_KEY', 'CODEX_ACCESS_TOKEN')
CODEX_EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max', 'ultra')
CODEX_LOGIN = 'Logged in using ChatGPT'
CODEX_ITEMS = ('agent_message', 'reasoning')  # anything else (command_execution, file_change, mcp_tool_call, web_search, todo_list, error, unknown) is a fault
CODEX_EVENTS = ('thread.started', 'turn.started', 'item.started', 'item.updated', 'item.completed', 'turn.completed')


def codex_model(model):
    if not isinstance(model, str) or not re.fullmatch(r'gpt-[0-9][0-9a-z.\-]*', model):
        raise S.ScoutError('bind an explicit Codex catalogue slug (e.g. gpt-6-sol), never an alias or display name')
    return model


def codex_environment(environ, codex_home):
    """Allowlisted OS variables plus CODEX_HOME. API keys, base URLs and org/project selectors are never passed."""
    env = {k: v for k, v in environ.items() if k.upper() in OS_ENV}
    env['CODEX_HOME'] = str(codex_home)
    if any(k.upper() in CODEX_FORBIDDEN_ENV for k in env):raise S.ScoutError('API-key or endpoint variable in the Codex environment')
    return env


def codex_arguments(executable, model, effort, cwd):
    """The prompt is piped on stdin (no positional prompt), so the frozen bytes are sent exactly and never hit the
    Windows command-line length limit. --output-schema is not used: the critic contract extracts its own fenced block."""
    if effort not in CODEX_EFFORTS:raise S.ScoutError(f'Codex effort is one of {CODEX_EFFORTS}')
    return [str(executable), 'exec', '--json', '--ephemeral', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check',
            '--sandbox', 'read-only', '--model', codex_model(model), '--config', f'model_reasoning_effort="{effort}"',
            '--config', 'web_search="disabled"', '--cd', str(cwd)]


CODEX_FLAGS = ('--json', '--ephemeral', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--sandbox', '--model', '--config', '--cd')


def codex_preflight(run_admin, executable_sha256, actual_sha256):
    """``run_admin(args) -> stdout text`` runs one local command. No prompt is ever sent here."""
    if actual_sha256 != executable_sha256:raise S.ScoutError('CODEX_EXECUTABLE_CHANGED')
    version = run_admin(['--version']).strip()
    if not version.startswith('codex-cli '):raise S.ScoutError('CODEX_VERSION_UNRECOGNISED')
    login = [line.strip() for line in run_admin(['login', 'status']).splitlines() if line.strip()]
    if login != [CODEX_LOGIN]:raise S.ScoutError('CODEX_NOT_CHATGPT_SUBSCRIPTION_LOGIN')  # API-key auth or unknown means STOP
    help_text = run_admin(['exec', '--help'])
    missing = [f for f in CODEX_FLAGS if f not in help_text]
    if missing:raise S.ScoutError('CODEX_UNSUPPORTED_FLAGS:' + ','.join(missing))
    return {'cli_version': version, 'auth': 'CHATGPT_LOGIN', 'help_sha256': S.hash_text(help_text)}


def codex_review(stdout, stderr, returncode, timed_out, model, *, accept_requested_identity=False):
    """Review one ``codex exec --json`` JSONL stream. Returns (reply bytes or None, facts)."""
    faults, fault = fault_list()
    screened = credential_screen(fault, 'CREDENTIAL_LIKE_PATTERN_IN_RAW_STREAM', stdout, stderr)
    events = []
    try:
        for line in stdout.decode('utf-8').splitlines():
            if line.strip():
                e = S.json_loads(line)
                if not isinstance(e, dict):raise S.ScoutError('event object required')
                events.append(e)
    except (UnicodeError, S.ScoutError):
        fault('INVALID_STREAM_ENVELOPE')
    kinds = [e.get('type') for e in events]
    if not events or kinds[0] != 'thread.started' or not isinstance(events[0].get('thread_id'), str) or not events[0]['thread_id']:
        fault('THREAD_NOT_ESTABLISHED')
    if kinds.count('thread.started') != 1 or kinds.count('turn.started') != 1 or kinds.count('turn.completed') != 1:
        fault('NOT_EXACTLY_ONE_TURN')
    if not events or kinds[-1] != 'turn.completed':fault('TERMINAL_NOT_ESTABLISHED')
    messages, completed, models = [], set(), set()  # every completion event counts: a repeated ID never collapses into one
    for e in events:
        kind = e.get('type')
        if kind in ('turn.failed', 'error'):fault('PROVIDER_ERROR_EVENT')
        elif kind not in CODEX_EVENTS:fault('UNRECOGNISED_EVENT')
        for key in ('model', 'model_slug'):
            if isinstance(e.get(key), str):models.add(e[key])
        if kind.startswith('item.') if isinstance(kind, str) else False:
            item = e.get('item')
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or item.get('type') not in CODEX_ITEMS:
                fault('PROHIBITED_OR_UNKNOWN_ITEM:' + str(item.get('type') if isinstance(item, dict) else None)[:40]); continue
            if kind == 'item.completed':
                if item['id'] in completed:fault('DUPLICATE_ITEM_COMPLETION')
                completed.add(item['id'])
            if item['type'] == 'agent_message':
                if not isinstance(item.get('text'), str):fault('AGENT_MESSAGE_WITHOUT_TEXT'); continue
                if kind == 'item.completed':messages.append(item['text'])
    if len(messages) != 1:fault('NOT_EXACTLY_ONE_AGENT_MESSAGE')
    usage = events[-1].get('usage') if events and kinds[-1] == 'turn.completed' else None
    keys = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in keys):fault('USAGE_UNKNOWN'); usage = {}
    if models and models != {model}:fault('MODEL_MISMATCH')
    basis = 'OBSERVED_IN_STREAM' if models == {model} else 'REQUESTED_ONLY'
    if basis == 'REQUESTED_ONLY' and not accept_requested_identity:fault('MODEL_IDENTITY_NOT_OBSERVED')
    if timed_out:fault('TIMEOUT')
    elif returncode != 0:fault('NONZERO_EXIT')
    text = messages[0] if len(messages) == 1 else ''
    reply = text.encode('utf-8')
    if len(reply) > MAX_REPLY_BYTES:fault('REPLY_TOO_LARGE')
    facts = {'provider': CODEX, 'faults': faults, 'model_requested': model, 'model_identity_basis': basis,
             'models_reported': sorted(models), 'thread_id_sha256': digest(events[0].get('thread_id')) if events and kinds[0] == 'thread.started' else S.UNKNOWN,
             'usage': {k: usage.get(k, S.UNKNOWN) for k in keys}, 'agent_messages': len(messages),
             'events': len(events), 'billing_path': 'CHATGPT_SUBSCRIPTION', 'charge': S.UNKNOWN,
             'underlying_provider_requests': S.UNKNOWN, 'reply_sha256': S.hash_text(text) if text else S.UNKNOWN,
             'credential_screen': screened}
    return (reply if not faults else None), facts


# ----------------------------------------------------------------------------------------------- Gemini API

GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
GEMINI_LEVELS = ('low', 'medium', 'high')


def gemini_model(model):
    if not isinstance(model, str) or not re.fullmatch(r'gemini-[0-9][0-9a-z.\-]*', model):
        raise S.ScoutError('bind an explicit Gemini API model ID (e.g. gemini-4-argon), never an alias or display name')
    return model


def gemini_request(prompt_text, *, max_output_tokens, thinking_level=None):
    """One user turn, no tools, no system instruction beyond the frozen critic prompt itself. ``candidateCount`` is not
    sent: it defaults to 1 when unset (API reference) and the Gemini 4 Argon guide says to remove it. The review still
    requires exactly one candidate."""
    if type(max_output_tokens) is not int or not 1000 <= max_output_tokens <= 65536:raise S.ScoutError('Gemini max_output_tokens is 1000..65536')
    config = {'maxOutputTokens': max_output_tokens}
    if thinking_level is not None:
        if thinking_level not in GEMINI_LEVELS:raise S.ScoutError(f'thinking level is one of {GEMINI_LEVELS}')
        config['thinkingConfig'] = {'thinkingLevel': thinking_level}
    return {'contents': [{'role': 'user', 'parts': [{'text': prompt_text}]}], 'generationConfig': config}


def worst_case_cost(prompt_bytes, max_output_tokens, prices):
    """Pre-dispatch bound in USD from documented per-1M prices. Input tokens are bounded by the byte count (a token
    is at least one byte), so the bound is conservative; it is a planning ceiling, never a charge."""
    return (prompt_bytes * prices['input_usd_per_million'] + max_output_tokens * prices['output_usd_per_million']) / 1e6


def gemini_review(status, body, model, prices):
    """Review one generateContent response. Returns (reply bytes or None, facts)."""
    faults, fault = fault_list()
    screened = credential_screen(fault, 'CREDENTIAL_LIKE_PATTERN_IN_RAW_RESPONSE', body)
    if status != 200:fault(f'HTTP_{status}')
    try:value = S.json_loads(body.decode('utf-8'))
    except (UnicodeError, S.ScoutError):value = None; fault('INVALID_RESPONSE_ENVELOPE')
    value = value if isinstance(value, dict) else {}
    if value.get('promptFeedback', {}).get('blockReason') if isinstance(value.get('promptFeedback'), dict) else False:fault('PROMPT_BLOCKED')
    candidates = value.get('candidates')
    text = ''
    if not isinstance(candidates, list) or len(candidates) != 1 or not isinstance(candidates[0], dict):fault('NOT_EXACTLY_ONE_CANDIDATE')
    else:
        c = candidates[0]
        if c.get('finishReason') != 'STOP':fault('UNFINISHED_OR_STOPPED:' + str(c.get('finishReason'))[:30])
        parts = c.get('content', {}).get('parts') if isinstance(c.get('content'), dict) else None
        if not isinstance(parts, list) or not parts:fault('NO_CONTENT_PARTS')
        else:
            for p in parts:  # text only: a function call, code execution, inline data or thought part is a fault
                if not isinstance(p, dict) or set(p) - {'text', 'thoughtSignature'} or not isinstance(p.get('text'), str) or p.get('thought'):
                    fault('PROHIBITED_OR_UNKNOWN_PART'); continue
                text += p['text']
    returned = value.get('modelVersion')
    if not isinstance(returned, str) or not (returned == model or returned.startswith(model + '-')):fault('MODEL_MISMATCH_OR_UNKNOWN')
    u = value.get('usageMetadata') if isinstance(value.get('usageMetadata'), dict) else {}
    def count(k):return u[k] if type(u.get(k)) is int and u[k] >= 0 else S.UNKNOWN  # absent is unknown, never zero
    usage = {k: count(k) for k in ('promptTokenCount', 'candidatesTokenCount', 'thoughtsTokenCount', 'totalTokenCount')}
    if S.UNKNOWN in (usage['promptTokenCount'], usage['candidatesTokenCount']):fault('USAGE_UNKNOWN')
    if u.get('toolUsePromptTokenCount'):fault('TOOL_USE_REPORTED')
    estimate = S.UNKNOWN
    if S.UNKNOWN not in usage.values():
        estimate = round((usage['promptTokenCount'] * prices['input_usd_per_million']
                          + (usage['candidatesTokenCount'] + usage['thoughtsTokenCount']) * prices['output_usd_per_million']) / 1e6, 6)
    reply = text.encode('utf-8')
    if len(reply) > MAX_REPLY_BYTES:fault('REPLY_TOO_LARGE')
    facts = {'provider': GEMINI, 'faults': faults, 'model_requested': model, 'model_returned': returned if isinstance(returned, str) else S.UNKNOWN,
             'model_identity_basis': 'OBSERVED_IN_RESPONSE' if 'MODEL_MISMATCH_OR_UNKNOWN' not in faults else S.UNKNOWN,
             'response_id_sha256': digest(value['responseId']) if isinstance(value.get('responseId'), str) else S.UNKNOWN,
             'usage': usage, 'billing_path': 'GEMINI_API_PAID', 'cost_estimate_usd_documented_prices': estimate,
             'charge': S.UNKNOWN, 'underlying_provider_requests': 1, 'reply_sha256': S.hash_text(text) if text else S.UNKNOWN,
             'credential_screen': screened}
    return (reply if not faults else None), facts


GEMINI_HOST = 'generativelanguage.googleapis.com'


def https_transport(url, headers, body, timeout, limit=MAX_RESPONSE_BYTES, *, handlers=()):
    """Default Gemini transport: one POST to the documented host, no retries, no redirects, bounded read. Returns
    (status, bytes). Never logs headers. urllib's default redirect handler copies every non-content header, the API
    key included, onto a follow-up request to any origin; here every redirect is refused before a follow-up request
    exists. ``handlers`` is an offline test seam only (a fake HTTPS handler)."""
    import urllib.error, urllib.parse, urllib.request
    target = urllib.parse.urlsplit(url)
    if target.scheme != 'https' or target.hostname != GEMINI_HOST or target.port not in (None, 443) or target.username or target.password:
        raise S.ScoutError('GEMINI_ENDPOINT_NOT_DOCUMENTED_HOST')

    class RefuseRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            fp.close()
            raise S.ScoutError(f'GEMINI_REDIRECT_REFUSED:HTTP_{code}')

    opener = urllib.request.build_opener(RefuseRedirects, *handlers)
    request = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with opener.open(request, timeout=timeout) as response:
            data = response.read(limit + 1); status = response.status
    except urllib.error.HTTPError as error:  # includes a 3xx without a Location header: reviewed as HTTP_3xx, never followed
        data, status = error.read(limit + 1), error.code
    if len(data) > limit:raise S.ScoutError('GEMINI_RESPONSE_TOO_LARGE')
    return status, data


def validate_role(role):
    """A critic role configuration as bound in an owner authorisation."""
    if not isinstance(role, dict) or role.get('provider') not in PROVIDERS:raise S.ScoutError(f'provider is one of {PROVIDERS}')
    p = role['provider']
    if role.get('family') != FAMILIES[p]:raise S.ScoutError(f'{p} has model family {FAMILIES[p]}')
    if p == CODEX:
        codex_model(role.get('model'))
        if role.get('effort') not in CODEX_EFFORTS or type(role.get('accept_requested_identity')) is not bool:
            raise S.ScoutError('Codex role needs effort and an explicit accept_requested_identity decision')
        S.validate(S.HASH, role.get('executable_sha256'), 'Codex executable hash')
    elif p == GEMINI:
        gemini_model(role.get('model'))
        prices = role.get('prices')
        if not isinstance(prices, dict) or set(prices) != {'input_usd_per_million', 'output_usd_per_million', 'source', 'as_of'} \
                or not all(type(prices[k]) in (int, float) and math.isfinite(prices[k]) and prices[k] > 0 for k in ('input_usd_per_million', 'output_usd_per_million')):
            raise S.ScoutError('Gemini role needs documented positive per-1M prices with source and date')
        if not isinstance(role.get('api_key_env'), str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{2,63}', role['api_key_env']):
            raise S.ScoutError('name the environment variable holding the key; the key itself is never written')
        gemini_request('x', max_output_tokens=role.get('max_output_tokens'), thinking_level=role.get('thinking_level'))
    return role
