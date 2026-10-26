"""One owner-authorised exploratory FORGE generation through the Claude Code CLI.

Separate from N1, the frozen V004 comparison and every scientific slot. ``plan`` creates the archive, the reserved
attempt and an authorisation template; it never starts a process. ``run`` refuses without a completed owner
authorisation bound to the exact payload, binary, model and limits. It consumes the single attempt durably before
any CLI command, preserves raw bytes before parsing and imports through the unchanged Scout importer. There is no
retry, repair, continuation or second generation: any deviation closes the attempt as ERROR without cards.

The child environment is allowlist-built, so an inherited API key, OAuth token, base URL or provider switch never
reaches the CLI (an API key silently overrides the subscription in print mode). Account selection is checked
from ``auth status`` categories and the init event, never from credential contents."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import threading
import time
from typing import Callable
import uuid

from src.research.spec import canonical, digest
from .. import claude_subscription as CS, schema as S, v004_runtime as RT, workflow as W
from ..evaluation import report
from ..post_generation.review import ASSISTANT
from ..storage import Archive, ROOT, input_json, unlinked
from ..v004_transport import classify_terminal

VERSION = 'SCOUT_EXPLORATORY_RUNNER_V001'
PLAN_V, AUTH_V, RECEIPT_V = 'SCOUT_EXPLORATORY_PLAN_V001', 'SCOUT_EXPLORATORY_AUTHORISATION_V001', 'SCOUT_EXPLORATORY_RECEIPT_V001'
ADDENDUM = Path(__file__).resolve().parent / 'resources/forge_format_addendum_v001.txt'
ADDENDUM_SHA256 = '360f9354f07382973425476a3300a7fb1024ff227ebde3177bb78ecca0dba4c3'
EFFORTS = ('low', 'medium', 'high')
SUBSCRIPTIONS = ('pro', 'max')
MAX_CARDS, MAX_REQUEST_TOKENS, MAX_TIMEOUT, ADMIN_TIMEOUT = 4, 32768, 600, 30
ADMIN = (('--version',), ('--help',), ('auth', 'status', '--json'))
# Variables that select another credential, account, endpoint or provider. The allowlist already excludes them;
# this list is checked again on the exact child mapping.
FORBIDDEN_ENV = ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'ANTHROPIC_BASE_URL',
                 'ANTHROPIC_PROFILE', 'ANTHROPIC_CONFIG_DIR', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX',
                 'CLAUDE_CODE_USE_FOUNDRY', 'CLAUDE_CODE_USE_MANTLE', 'CLAUDE_CODE_USE_ANTHROPIC_AWS')
IDENTITY_KEYS = ('email', 'emailAddress', 'orgId', 'organizationId', 'orgName', 'organizationName', 'accountUuid')
DEVELOPMENT = ('.claude.json', '.claude/settings.json', '.claude/.credentials.json')
SYSTEM_EVENTS = ('init', 'ui_invalidate', 'thinking_tokens')  # observed in a real 2.1.302 stream; others fail closed
SESSION_EVENTS = ('system', 'rate_limit_event', 'assistant', 'result')
# Rate-limit review V002 (2026-10-26): V001 accepted only status 'allowed'. Campaign 30 scan 01 showed a served,
# non-overage request reported as 'allowed_warning' (seven-day window). V002 also accepts that status, and only with
# isUsingOverage exactly False; every other status, a missing field or overage still fails closed.
STREAM_REVIEW = 'SCOUT_EXPLORATORY_STREAM_REVIEW_V002'
RATE_LIMIT_STATUSES = ('allowed', 'allowed_warning')
# Capture goes straight to files, never into memory, and is enforced while it happens: the process tree is stopped
# once combined stdout+stderr pass the bound (an IO limit, not a token certificate); a cap of 32,768 output tokens
# plus thinking estimates is far below it. At most one CHUNK per channel beyond the bound is ever kept.
MAX_STREAM_BYTES, MAX_ADMIN_BYTES, CHUNK = 8 * 1024 * 1024, 1024 * 1024, 64 * 1024
STOP_GRACE = 5


class CaptureFailed(subprocess.SubprocessError):
    """A pump thread could not read a pipe or write its sink; the process tree was stopped and nothing more kept."""
    def __init__(self, cmd, failures, tree):
        super().__init__(f'capture worker failed: {",".join(failures)} ({tree})')
        self.cmd, self.failures, self.tree = cmd, failures, tree


class OutputLimitExceeded(subprocess.SubprocessError):
    """Combined output passed its bound; the process tree was stopped (``tree`` says whether that was confirmed)."""
    def __init__(self, cmd, captured, tree):
        super().__init__(f'output passed its limit after {captured} bytes ({tree})')
        self.cmd, self.captured, self.tree = cmd, captured, tree


def stop_tree(proc):
    """Kill the CLI and its descendants: ``taskkill /T`` from System32 on Windows, the CLI's own session elsewhere."""
    try:
        if os.name == 'nt':
            taskkill = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'taskkill.exe'
            subprocess.run([str(taskkill), '/F', '/T', '/PID', str(proc.pid)], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=STOP_GRACE, check=True)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        killed = True
    except (OSError, subprocess.SubprocessError):
        killed = False
    try:proc.kill()
    except OSError:pass
    return killed


def capture(args, *, stdout, stderr, limit, timeout, input=None, cwd=None, env=None, shell=False, on_start=None):
    """``subprocess.run`` with bounded capture. Both pipes are copied in CHUNK reads into the given binary sinks while
    counting; once the combined count passes ``limit`` nothing more is kept (later bytes are drained and discarded)
    and the process tree is stopped, as it is at the timeout. The stop is confirmed only when the kill succeeded, the
    process exited and both pipes reached end of file (no descendant still holds them) within STOP_GRACE. A read or
    sink failure in a pump thread is reported to this supervising thread: nothing more is kept on either channel, the
    tree is stopped and ``CaptureFailed`` is raised, so the result is never returned as complete.

    ``on_start(pid)`` runs only once ``Popen`` has returned, so it is the evidence that a process exists; an
    ``OSError`` raised before it means the OS refused to create one. If it fails, the new process tree is stopped."""
    if shell:raise ValueError('shell is never used')
    proc = subprocess.Popen(args, stdin=subprocess.DEVNULL if input is None else subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd=cwd, env=env, shell=False, start_new_session=os.name != 'nt')
    if on_start:
        try:on_start(proc.pid)
        except BaseException:
            stop_tree(proc); raise
    lock, halt, kept, failures, ended = threading.Lock(), threading.Event(), {'bytes': 0, 'open': True}, [], set()
    def pump(name, pipe, sink):
        try:
            while chunk := pipe.read1(CHUNK):
                with lock:
                    if failures or kept['bytes'] > limit or not kept['open']:continue  # drained, never kept
                    try:sink.write(chunk)
                    except BaseException as error:failures.append(f'{name}:WRITE:{type(error).__name__}'); halt.set(); continue
                    kept['bytes'] += len(chunk)
                    if kept['bytes'] > limit:halt.set()
            ended.add(name)
        except BaseException as error:
            with lock:failures.append(f'{name}:READ:{type(error).__name__}')
            halt.set()
    def feed():
        try:proc.stdin.write(input)
        except OSError:pass  # the child stopped reading or was stopped
        try:proc.stdin.close()
        except OSError:pass
    readers = [threading.Thread(target=pump, args=('stdout', proc.stdout, stdout), daemon=True),
               threading.Thread(target=pump, args=('stderr', proc.stderr, stderr), daemon=True)]
    workers = readers + ([threading.Thread(target=feed, daemon=True)] if input is not None else [])
    for w in workers:w.start()
    deadline = time.monotonic() + timeout
    while not halt.is_set() and time.monotonic() < deadline and (proc.poll() is None or any(r.is_alive() for r in readers)):
        halt.wait(0.05)
    stopping = halt.is_set() or proc.poll() is None or any(r.is_alive() for r in readers)
    killed = stop_tree(proc) if stopping else True
    for w in workers:w.join(STOP_GRACE if stopping else None)
    with lock:kept['open'] = False  # a reader left behind by a surviving descendant never writes again
    try:proc.wait(STOP_GRACE)
    except subprocess.TimeoutExpired:killed = False
    drained = ended == {'stdout', 'stderr'}  # both pipes reached end of file
    if not any(r.is_alive() for r in readers):proc.stdout.close(); proc.stderr.close()
    tree = 'PROCESS_TREE_STOPPED' if killed and drained else 'PROCESS_TREE_STOP_UNCONFIRMED'
    if failures:raise CaptureFailed(args, list(failures), tree)
    if kept['bytes'] > limit:raise OutputLimitExceeded(args, kept['bytes'], tree)
    if stopping:
        expired = subprocess.TimeoutExpired(args, timeout); expired.tree = tree
        raise expired
    return subprocess.CompletedProcess(args, proc.returncode, None, None)


@dataclass
class Host:
    """Everything the runner touches outside the archive, injectable for offline tests."""
    home: Path = field(default_factory=Path.home)
    runner: Callable = capture
    environ: dict = field(default_factory=lambda: dict(os.environ))
    policy_check: Callable = CS.reject_managed_policy
    now: Callable = S.utc_now
    monotonic: Callable = time.monotonic

    @property
    def config(self):
        return Path(self.home).absolute() / '.claude-research'


def addendum():
    data = unlinked(ADDENDUM).read_bytes()
    if hashlib.sha256(data).hexdigest() != ADDENDUM_SHA256:raise S.ScoutError('frozen format addendum changed; a new version is required')
    return data


def payload(prompt):
    """The exact bytes sent: the prompt object with sorted keys (as read back from the canonical export in pilot ATT-0001,
    so independent of in-memory key order) plus the format-only addendum."""
    return json.dumps(prompt, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8') + b'\n\n' + addendum()


def environment(host, effort, cap):
    env = RT.child_environment(host.environ, host.config, host.home)
    env.update(CLAUDE_CODE_EFFORT_LEVEL=effort, CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(cap), CLAUDE_CODE_MAX_TURNS='1')
    if any(k.upper() in FORBIDDEN_ENV for k in env):raise S.ScoutError('credential, endpoint or provider override in the child environment')
    return env


def controls(env):
    return {k: v for k, v in sorted(env.items()) if k.startswith('CLAUDE_')}


def arguments(executable, model, effort, session_id):
    """Raw JSON text, all tools off, one turn. No --json-schema: structured output can reprompt (a second generation)."""
    return [str(executable), '--print', '--model', model, '--effort', effort, '--output-format', 'stream-json', '--verbose',
            '--input-format', 'text', '--tools', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
            '--safe-mode', '--restricted', '--setting-sources', '', '--no-session-persistence', '--permission-mode', 'dontAsk',
            '--permission-prompts', 'none', '--disable-slash-commands', '--no-chrome', '--max-turns', '1',
            '--system-prompt', RT.SYSTEM_PROMPT, '--session-id', session_id]


FLAGS = sorted({a for a in arguments('x', 'm', 'low', 's') if a.startswith('--')})
# Documented in the official CLI reference but not listed by `--help` (2.1.302 omits it; the reference says `--help`
# does not list every flag, and 2.1.302 parses it as a known option). It is still always passed, CLAUDE_CODE_MAX_TURNS
# stays 1 and the review still requires exactly one reported turn; if a CLI rejected it, it would exit at option
# parsing, before any request, and the attempt would close as ERROR. Every other flag must appear in `--help`.
UNLISTED_DOCUMENTED_FLAGS = ('--max-turns',)


def bindings(plan):
    return {k: plan[k] for k in ('plan_sha256', 'archive', 'attempt_id', 'payload_sha256', 'model', 'effort',
                                 'max_output_tokens_per_request', 'timeout_seconds', 'executable', 'binary_sha256',
                                 'config_directory', 'controls')}


def plan(store, *, title, model, count, effort, max_output_tokens_per_request, timeout_seconds, executable, host=None):
    """Create the archive and its single reserved FORGE attempt. Starts no process and reads no account file."""
    host = host or Host()
    RT.model_id(model)
    if effort not in EFFORTS:raise S.ScoutError(f'effort is one of {EFFORTS}')
    if not 1 <= count <= MAX_CARDS:raise S.ScoutError(f'count is 1..{MAX_CARDS}')
    if type(max_output_tokens_per_request) is not int or not 1000 <= max_output_tokens_per_request <= MAX_REQUEST_TOKENS:
        raise S.ScoutError(f'per-request output cap is 1000..{MAX_REQUEST_TOKENS}')
    if type(timeout_seconds) is not int or not 30 <= timeout_seconds <= MAX_TIMEOUT:raise S.ScoutError(f'timeout is 30..{MAX_TIMEOUT} seconds')
    archive = Archive(store)
    if archive.path.exists() and any(archive.path.iterdir()):raise S.ScoutError('an exploratory run needs a new empty archive')
    exe = CS.discover(executable)
    env = environment(host, effort, max_output_tokens_per_request)
    W.initialise(archive, title, with_memory=False, max_cards=count, max_attempts=1)
    aid, prompt = W.prepare(archive, 'FORGE', count, model)
    body = {'schema': PLAN_V, 'runner': VERSION, 'archive': str(archive.path), 'attempt_id': aid, 'prompt_id': prompt['id'],
            'prompt_sha256': prompt['sha256'], 'payload_sha256': hashlib.sha256(payload(prompt)).hexdigest(),
            'addendum_sha256': ADDENDUM_SHA256, 'model': model, 'effort': effort, 'count': count,
            'max_output_tokens_per_request': max_output_tokens_per_request, 'batch_output_budget': archive.load().batch['max_output_tokens'],
            'timeout_seconds': timeout_seconds, 'executable': str(exe), 'binary_sha256': CS.file_hash(exe),
            'config_directory': str(host.config), 'controls': controls(env), 'argument_flags': FLAGS,
            'system_prompt_sha256': S.hash_text(RT.SYSTEM_PROMPT), 'administrative_commands': [' '.join(a) for a in ADMIN],
            'model_invocations_maximum': 1, 'created_at': host.now(), 'hosted_authorised': False}
    record = {**body, 'plan_sha256': digest(body)}
    archive.export(f'exploratory-plan-{aid}.json', record)
    template = {'schema': AUTH_V, **bindings(record), 'allowed_subscription_types': [], 'account_fingerprint_sha256': 'NOT_PINNED',
                'administrative_commands_authorised': record['administrative_commands'] + ['auth status --json (after)'],
                'model_invocations_maximum': 1, 'hosted_transmission_approved': False, 'owner': '', 'approved_at': ''}
    path = archive.export(f'exploratory-authorisation-TEMPLATE-{aid}.json', template)
    return {'attempt_id': aid, 'plan_sha256': record['plan_sha256'], 'payload_sha256': record['payload_sha256'],
            'authorisation_template': str(path), 'model_calls_made': 0, 'cli_commands_run': 0,
            'next': 'The owner completes a copy of the template outside the archive, then: run STORE --authorisation FILE.'}


def load_plan(archive, state):
    pending = [a for a in state.attempts.values() if 'result' not in a]
    if len(state.attempts) != 1 or len(pending) != 1:raise S.ScoutError('the single exploratory attempt is not pending; no second run')
    aid = pending[0]['id']
    p = input_json(archive.path / 'exports' / f'exploratory-plan-{aid}.json')
    if p.get('schema') != PLAN_V or p['plan_sha256'] != digest({k: v for k, v in p.items() if k != 'plan_sha256'}):
        raise S.ScoutError('plan changed after it was written')
    prompt = state.prompts[pending[0]['prompt_id']]
    if (p['attempt_id'], p['prompt_sha256'], p['model']) != (aid, prompt['sha256'], pending[0]['requested_model']) \
            or hashlib.sha256(payload(prompt)).hexdigest() != p['payload_sha256'] or p['archive'] != str(archive.path):
        raise S.ScoutError('plan no longer matches the archived prompt, attempt or payload')
    return p, prompt


def check_authorisation(value, p):
    if not isinstance(value, dict) or value.get('schema') != AUTH_V:raise S.ScoutError('owner authorisation required')
    if any(value.get(k) != v for k, v in bindings(p).items()):raise S.ScoutError('authorisation does not bind this exact plan')
    if value.get('hosted_transmission_approved') is not True or value.get('model_invocations_maximum') != 1:
        raise S.ScoutError('explicit approval of exactly one model invocation required')
    if value.get('administrative_commands_authorised') != p['administrative_commands'] + ['auth status --json (after)']:
        raise S.ScoutError('the administrative commands must be authorised exactly')
    subs = value.get('allowed_subscription_types')
    if not isinstance(subs, list) or not subs or any(s not in SUBSCRIPTIONS for s in subs):
        raise S.ScoutError(f'name the allowed subscription types from {SUBSCRIPTIONS}; API billing is never allowed')
    fp = value.get('account_fingerprint_sha256')
    if fp != 'NOT_PINNED':S.validate(S.HASH, fp, 'account fingerprint')
    owner = value.get('owner')
    if not isinstance(owner, str) or not owner.strip() or ASSISTANT.search(owner) or owner.strip().upper() in ('UNKNOWN', 'OWNER'):
        raise S.ScoutError('the authorising owner is a named human, not an assistant or model')
    try:moment = datetime.fromisoformat(value.get('approved_at', ''))
    except (TypeError, ValueError) as error:raise S.ScoutError('approved_at must be an ISO time') from error
    if moment.utcoffset() is None:raise S.ScoutError('approved_at needs a timezone')
    return digest(value)


def account_files(host):
    """Stat only: never open development settings or credential contents."""
    out = {}
    for name in DEVELOPMENT:
        p = Path(host.home) / name
        try:st = p.lstat(); out[name] = {'size': st.st_size, 'mtime_ns': st.st_mtime_ns}
        except FileNotFoundError:out[name] = None
    return out


def fingerprint(auth):
    present = {k: auth[k] for k in IDENTITY_KEYS if isinstance(auth.get(k), str) and auth[k]}
    return digest(present) if present else S.UNKNOWN


def admin(host, exe, env, args):
    """Bounded in memory while captured (1 MiB combined plus at most a chunk per channel); never stored."""
    out, err = io.BytesIO(), io.BytesIO()
    with tempfile.TemporaryDirectory(prefix='scout-explore-admin-') as cwd:
        if Path(cwd).resolve().is_relative_to(ROOT):raise S.ScoutError('CLI working directory must be outside the repository')
        try:p = host.runner([str(exe), *args], env=env.copy(), cwd=cwd, stdout=out, stderr=err, limit=MAX_ADMIN_BYTES,
                            timeout=ADMIN_TIMEOUT, shell=False)
        except OutputLimitExceeded as error:raise S.ScoutError(f'ADMIN_OUTPUT_TOO_LARGE:{args[0]}:{error.tree}') from None
        except CaptureFailed as error:raise S.ScoutError(f'ADMIN_CAPTURE_FAILED:{args[0]}:{error.tree}') from None
        except subprocess.TimeoutExpired as error:
            raise S.ScoutError(f'ADMIN_TIMEOUT:{args[0]}:{getattr(error, "tree", S.UNKNOWN)}') from None
    if p.returncode:raise S.ScoutError('ADMIN_COMMAND_FAILED:' + args[0])
    if out.tell() + err.tell() > MAX_ADMIN_BYTES:raise S.ScoutError('ADMIN_OUTPUT_TOO_LARGE:' + args[0])
    # Decoded as text mode did (strict UTF-8, universal newlines), so help hashes are unchanged.
    return out.getvalue().decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')


def account(host, exe, env, auth_value, label):
    """Allowlisted auth categories only; raw auth output is never stored."""
    try:raw = admin(host, exe, env, ADMIN[2])
    except S.ScoutError as error:  # admin codes name only the command and stop status, never output
        if str(error).startswith(('ADMIN_OUTPUT_TOO_LARGE:', 'ADMIN_TIMEOUT:', 'ADMIN_CAPTURE_FAILED:')):raise S.ScoutError(f'{label}_{error}') from None
        raise S.ScoutError(f'{label}_AUTH_STATUS_UNREADABLE') from error
    try:auth = S.json_loads(raw)
    except S.ScoutError as error:raise S.ScoutError(f'{label}_AUTH_STATUS_UNREADABLE') from error
    categories = {k: auth.get(k, S.UNKNOWN) for k in ('loggedIn', 'authMethod', 'apiProvider', 'subscriptionType', 'configDirectory')}
    if categories['loggedIn'] is not True or categories['authMethod'] != 'claude.ai' or categories['apiProvider'] != 'firstParty':
        raise S.ScoutError(f'{label}_NOT_FIRST_PARTY_SUBSCRIPTION_LOGIN')
    if categories['subscriptionType'] not in auth_value['allowed_subscription_types']:raise S.ScoutError(f'{label}_SUBSCRIPTION_TYPE_NOT_AUTHORISED')
    if categories['configDirectory'] == S.UNKNOWN or Path(categories['configDirectory']).absolute() != host.config:
        raise S.ScoutError(f'{label}_CONFIG_DIRECTORY_NOT_RESEARCH')
    fp = fingerprint(auth)
    if auth_value['account_fingerprint_sha256'] not in ('NOT_PINNED', fp):raise S.ScoutError(f'{label}_ACCOUNT_FINGERPRINT_CHANGED')
    return {**categories, 'account_fingerprint_sha256': fp}


def preflight(host, p, auth_value, exe, env):
    config = host.config
    if not config.is_dir() or not (config / '.credentials.json').is_file():raise S.ScoutError('RESEARCH_CONFIG_OR_CREDENTIAL_STORE_ABSENT')
    if (config / 'remote-settings.json').exists():raise S.ScoutError('SERVER_MANAGED_SETTINGS_CACHE_PRESENT')
    try:host.policy_check(config)
    except S.ScoutError as error:raise S.ScoutError('MANAGED_POLICY_PRESENT_OR_UNKNOWN') from error
    if CS.file_hash(exe) != p['binary_sha256']:raise S.ScoutError('EXECUTABLE_CHANGED')
    if controls(env) != p['controls']:raise S.ScoutError('CHILD_ENVIRONMENT_CONTROLS_CHANGED')
    version = admin(host, exe, env, ADMIN[0]).strip()
    help_text = admin(host, exe, env, ADMIN[1])
    missing = [f for f in FLAGS if f not in help_text and f not in UNLISTED_DOCUMENTED_FLAGS]
    if missing:raise S.ScoutError('UNSUPPORTED_FLAGS:' + ','.join(missing))
    return {'cli_version': version, 'help_sha256': S.hash_text(help_text), 'account': account(host, exe, env, auth_value, 'PREFLIGHT')}


def review(stdout, stderr, returncode, timed_out, model, session_id):
    """Fail-closed review of one recorded stream. Never trims, extracts or repairs. Returns allowlisted facts."""
    faults, events = [], []
    def fault(code):
        if code not in faults:faults.append(code)
    raw_text = stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')
    if CS.safe_output(raw_text) != raw_text:fault('CREDENTIAL_LIKE_PATTERN_IN_RAW_STREAM')  # kept privately, never repaired
    try:
        text, err = stdout.decode('utf-8'), stderr.decode('utf-8', errors='replace')
        for line in text.splitlines():
            if line.strip():
                e = S.json_loads(line)
                if not isinstance(e, dict):raise S.ScoutError('event object required')
                events.append(e)
    except (UnicodeError, S.ScoutError):
        fault('INVALID_STREAM_ENVELOPE'); err = ''
    inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    results = [e for e in events if e.get('type') == 'result']
    init, result = (inits[0] if len(inits) == 1 else {}), (results[0] if len(results) == 1 else {})
    if len(inits) != 1:fault('INITIALISATION_NOT_ESTABLISHED')
    if len(results) != 1 or not events or events[-1] is not result:fault('TERMINAL_NOT_ESTABLISHED')
    plugins = init.get('plugins', [])
    if (init.get('tools') != [] or init.get('mcp_servers') != [] or init.get('skills') != [] or init.get('permissionMode') != 'dontAsk'
            or not isinstance(plugins, list) or any(not isinstance(x, dict) or x.get('path') != 'builtin' for x in plugins)):
        fault('ENVIRONMENT_NOT_ESTABLISHED')
    if init.get('apiKeySource') != 'none':fault('API_KEY_SOURCE_NOT_NONE')
    if init.get('model') != model:fault('MODEL_MISMATCH')
    messages, requests, texts, overage, limits = [], set(), [], [], []
    for e in events:
        kind = e.get('type')
        # An absent session identifier is never a match: every accepted event kind carried one in the real stream.
        if kind in SESSION_EVENTS and e.get('session_id') != session_id:fault('SESSION_ID_MISSING_OR_CHANGED')
        if kind == 'system':
            if e.get('subtype') not in SYSTEM_EVENTS:fault('UNRECOGNISED_SYSTEM_EVENT')
        elif kind == 'rate_limit_event':
            info = e.get('rate_limit_info')
            if not isinstance(info, dict) or info.get('isUsingOverage') is not False or info.get('status') not in RATE_LIMIT_STATUSES:
                fault('OVERAGE_OR_RATE_LIMIT')
            overage.append(info.get('overageStatus', S.UNKNOWN) if isinstance(info, dict) else S.UNKNOWN)
            # Metadata only: the reported status and window, each kept only when it is a short plain label.
            limits.append({k: (v if isinstance(v, str) and re.fullmatch(r'[a-z_]{1,40}', v) else S.UNKNOWN)
                           for k, v in (('status', info.get('status')), ('window', info.get('rateLimitType')))} if isinstance(info, dict)
                          else {'status': S.UNKNOWN, 'window': S.UNKNOWN})
        elif kind == 'assistant':
            msg = e.get('message')
            if not isinstance(msg, dict) or not isinstance(msg.get('id'), str) or not isinstance(e.get('request_id'), str):
                fault('MESSAGE_OR_REQUEST_ID_UNKNOWN'); continue
            if msg['id'] not in messages:messages.append(msg['id'])
            requests.add(e['request_id'])
            if msg.get('model') != model:fault('MODEL_MISMATCH')
            for block in (msg.get('content') if isinstance(msg.get('content'), list) else [None]):
                if isinstance(block, dict) and block.get('type') == 'text' and isinstance(block.get('text'), str):texts.append(block['text'])
                elif not (isinstance(block, dict) and block.get('type') in ('thinking', 'redacted_thinking')):fault('PROHIBITED_TOOL_OR_CONTENT')
        elif kind == 'user':fault('CONTINUATION_OR_TOOL_RESULT')  # an output-limit continuation appears as a synthetic user event
        elif kind != 'result':fault('UNRECOGNISED_EVENT')
    if len(messages) != 1 or len(requests) != 1:fault('NOT_EXACTLY_ONE_GENERATION')
    # Absence of a rate-limit event is not evidence that overage was off: require at least one affirmative record.
    if not overage:fault('NON_OVERAGE_NOT_EVIDENCED')
    turns = result.get('num_turns')
    if type(turns) is not int or turns != 1:fault('TURN_COUNT_NOT_ONE')  # missing, zero, several or boolean all fail
    assembly = ''.join(texts)
    termination = 'TIMEOUT' if timed_out else classify_terminal(events, returncode, err, timed_out)
    if termination != 'SUCCESS':fault(termination)
    if result.get('stop_reason') != 'end_turn':fault('UNFINISHED_GENERATION')
    if not isinstance(result.get('result'), str) or result['result'] != assembly:fault('TERMINAL_ASSEMBLY_MISMATCH')
    stats = result.get('subagent_stats')
    if 'structured_output' in result or result.get('permission_denials') != [] or not isinstance(stats, dict) or stats.get('spawned') != 0:
        fault('ENVIRONMENT_OR_FORMATTER_DEVIATION')
    usage, models = result.get('usage') if isinstance(result.get('usage'), dict) else {}, result.get('modelUsage')
    if not isinstance(models, dict) or set(models) != {model} or not isinstance(models[model], dict) or models[model].get('provider') != 'firstParty':
        fault('MODEL_USAGE_IDENTITY_OR_PROVIDER')
    tools = usage.get('server_tool_use', {}) if isinstance(usage.get('server_tool_use', {}), dict) else {'x': 1}
    if any(v for v in tools.values()):fault('UNEXPECTED_SERVER_TOOL')
    def count(v):return type(v) is int and v >= 0
    parts = [usage.get(k) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')]
    tokens = {'input_tokens': sum(parts) if all(count(x) for x in parts) else S.UNKNOWN,
              'output_tokens': usage['output_tokens'] if count(usage.get('output_tokens')) else S.UNKNOWN}
    if tokens['output_tokens'] == S.UNKNOWN:fault('USAGE_UNKNOWN')
    if CS.safe_output(assembly) != assembly:fault('CREDENTIAL_LIKE_OUTPUT_WITHHELD')
    details = usage.get('output_tokens_details') if isinstance(usage.get('output_tokens_details'), dict) else {}
    return {'faults': faults, 'text': assembly if 'CREDENTIAL_LIKE_OUTPUT_WITHHELD' not in faults else '', 'termination': termination,
            'tokens': tokens, 'thinking_tokens': details.get('thinking_tokens', S.UNKNOWN), 'visible_generations': len(messages),
            'visible_request_ids': len(requests), 'reported_turns': result.get('num_turns', S.UNKNOWN),
            'cli_version_init': init.get('claude_code_version', S.UNKNOWN), 'overage_status': sorted(set(overage)),
            'stream_review': STREAM_REVIEW, 'rate_limit_states': limits,
            'cli_list_price_estimate_usd': result.get('total_cost_usd', S.UNKNOWN), 'underlying_provider_requests': S.UNKNOWN}


def provenance(p, auth_value, facts, *, invoked, completed, model, error=None):
    """Recorded through the frozen generic importer. Its provider enum has no automated-Claude label (a hosted label
    needs a V003 comparison binding), so the transport is named explicitly in the parameters."""
    params = {'transport': VERSION, 'surface': 'Claude Code CLI --print stream-json raw JSON', 'effort_requested': p['effort'],
              'max_output_tokens_per_request': p['max_output_tokens_per_request'], 'payload_sha256': p['payload_sha256'],
              'addendum_sha256': ADDENDUM_SHA256, 'plan_sha256': p['plan_sha256'], 'authorisation_sha256': facts.get('authorisation_sha256', S.UNKNOWN),
              'binary_sha256': p['binary_sha256'], 'cli_version': facts.get('cli_version', S.UNKNOWN),
              'session_id': facts.get('session_id', S.UNKNOWN), 'stdout_sha256': facts.get('stdout_sha256', S.UNKNOWN),
              'visible_generations': facts.get('visible_generations', 0), 'cli_list_price_estimate_usd_not_a_charge': facts.get('cli_list_price_estimate_usd', S.UNKNOWN),
              'timestamps_basis': 'RUNNER_WALL_CLOCK_AROUND_CLI_PROCESS'}
    tokens = facts.get('tokens', {'input_tokens': S.UNKNOWN, 'output_tokens': S.UNKNOWN})
    return {'model': model, 'provider': 'OPERATOR_ASSISTED', 'invoked_at': invoked, 'completed_at': completed, 'parameters': params,
            'seed': S.UNKNOWN, 'usage': {**tokens, 'cost': S.UNKNOWN, 'currency': S.UNKNOWN},
            'context_declaration': ('Owner-authorised exploratory runner: one fresh Claude Code print-mode session, research subscription '
                'configuration, no tools/MCP/skills/settings/persistence, seedless memory-free FORGE prompt plus format-only addendum. '
                'Not a V004 comparison or scientific slot. ' + (f'Stopped: {error[:1500]}' if error else 'Exactly one visible generation.')),
            'operator': f'{auth_value["owner"].strip()} (owner) via {VERSION}'}


CLOSE = (S.ScoutError, OSError, subprocess.SubprocessError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError)


# Process start: NOT_STARTED (no launch), START_ATTEMPTED (Popen raised OSError, so no process exists), STARTED
# (Popen returned) or UNKNOWN (launch in flight when it failed or was interrupted). A started process is not
# evidence that a request reached the provider; only a request ID in the reviewed stream is.
INVOCATION = {'NOT_SENT': 'NOT_INVOKED', 'VISIBLE_REQUEST_ID': 'INVOKED', S.UNKNOWN: S.UNKNOWN}
MARKER_STARTS = {'NONE': ('NOT_STARTED',), 'DISPATCHED': ('START_ATTEMPTED', S.UNKNOWN, 'STARTED'), 'STARTED': ('STARTED',)}
START_INVOCATIONS = {'NOT_STARTED': ('NOT_INVOKED',), 'START_ATTEMPTED': ('NOT_INVOKED',), S.UNKNOWN: (S.UNKNOWN,),
                     'STARTED': ('INVOKED', S.UNKNOWN)}


def provider_request(process, review_facts):
    if process in ('NOT_STARTED', 'START_ATTEMPTED'):return 'NOT_SENT'
    seen = review_facts.get('visible_request_ids', 0)
    return 'VISIBLE_REQUEST_ID' if process == 'STARTED' and type(seen) is int and seen >= 1 else S.UNKNOWN


def seal(handles):
    """Flush, fsync and close every raw handle. Each step is attempted exactly once, a failure never skips the
    remaining steps or handles, and every failure is named: this runs in a ``finally`` and must never raise."""
    failures = []
    for c, h in handles.items():
        for step, act in (('FLUSH', h.flush), ('FSYNC', lambda: os.fsync(h.fileno())), ('CLOSE', h.close)):
            try:act()
            except Exception as error:failures.append(f'{c}:{step}:{type(error).__name__}')
    return failures


def run(store, authorisation, *, host=None):
    """Execute the one authorised generation. Every outcome is final and recorded; nothing is retried."""
    host = host or Host()
    log, real = [], host.runner
    def counted(args, **kwargs):
        log.append('MODEL' if '--print' in args else 'ADMIN')
        return real(args, **kwargs)
    host = replace(host, runner=counted)
    archive = Archive(store); state = archive.load()
    p, prompt = load_plan(archive, state)
    auth_value = input_json(authorisation)
    facts = {'authorisation_sha256': check_authorisation(auth_value, p), 'session_id': str(uuid.uuid4())}
    aid, exe = p['attempt_id'], CS.discover(p['executable'])
    env = environment(host, p['effort'], p['max_output_tokens_per_request'])
    # Consumed before ANY CLI command: a crash after this point can never be re-run.
    if (archive.path / 'exports' / f'exploratory-claim-{aid}.json').exists():
        raise S.ScoutError('attempt already claimed (interrupted run); never resumed or re-dispatched')
    archive.export(f'exploratory-claim-{aid}.json', {'schema': VERSION, 'attempt_id': aid, 'plan_sha256': p['plan_sha256'],
                   'authorisation_sha256': facts['authorisation_sha256'], 'session_id': facts['session_id'], 'claimed_at': host.now()})
    invoked = completed = host.now(); stopped, review_facts, start = None, {}, {'process': 'NOT_STARTED'}
    before = account_files(host)
    try:
        facts.update(preflight(host, p, auth_value, exe, env))
    except CLOSE as error:
        stopped = 'PREFLIGHT_STOP:' + (str(error) if isinstance(error, S.ScoutError) else type(error).__name__)
    if stopped is None:
        args = arguments(exe, p['model'], p['effort'], facts['session_id'])
        code, timed_out, tree = S.UNKNOWN, False, None
        # The CLI writes straight into exclusive raw files: bytes are durable before any parsing and never buffered.
        # The size bound is enforced during capture: past it the process tree is stopped and nothing more is kept.
        targets = {c: unlinked(archive.path / 'exports' / f'exploratory-{aid}-{c}.bin') for c in ('stdout', 'stderr')}
        handles = {}
        def started(pid):  # Popen returned: a process exists, whether or not its marker can be written
            start['process'] = 'STARTED'
            archive.export(f'exploratory-started-{aid}.json', {'schema': VERSION, 'attempt_id': aid, 'pid': pid, 'started_at': host.now()})
        invoked, clock = host.now(), host.monotonic()
        try:
            for c, t in targets.items():handles[c] = t.open('xb')
            with tempfile.TemporaryDirectory(prefix='scout-explore-') as cwd:
                if Path(cwd).resolve().is_relative_to(ROOT):raise S.ScoutError('CLI working directory must be outside the repository')
                # Durable before the launch: an interruption from here on is never read as "not started".
                archive.export(f'exploratory-dispatch-{aid}.json', {'schema': VERSION, 'attempt_id': aid, 'dispatched_at': host.now()})
                start['process'] = S.UNKNOWN  # until Popen's own outcome is known
                proc = host.runner(args, input=payload(prompt), cwd=cwd, env=env.copy(), stdout=handles['stdout'],
                                   stderr=handles['stderr'], limit=MAX_STREAM_BYTES, timeout=p['timeout_seconds'], shell=False,
                                   on_start=started)
                code = proc.returncode
        except subprocess.TimeoutExpired as error:
            timed_out, tree = True, getattr(error, 'tree', None)
        except OutputLimitExceeded as error:  # kept bytes are hashed below and never loaded or parsed
            stopped = 'RUN_STOP:RECORDING_SIZE_LIMIT:' + error.tree
        except CaptureFailed as error:  # likewise: a worker failure is never read as a complete stream
            stopped = 'RUN_STOP:RAW_CAPTURE_WORKER_FAILED:' + ','.join(error.failures) + ':' + error.tree
        except CLOSE as error:
            if start['process'] == S.UNKNOWN and isinstance(error, OSError):
                start['process'] = 'START_ATTEMPTED'  # Popen raised before returning: the OS created no process
            stopped = {'NOT_STARTED': 'RAW_CAPTURE_SETUP_FAILED' if len(handles) != len(targets) else 'INVOCATION_SETUP_FAILED:' + type(error).__name__,
                       'START_ATTEMPTED': 'PROCESS_START_FAILED', S.UNKNOWN: 'PROCESS_START_UNKNOWN:' + type(error).__name__,
                       'STARTED': 'DISPATCH_FAILED_AFTER_START:' + type(error).__name__}[start['process']]
        finally:
            sealed = seal(handles)
        if sealed:  # bytes may be partial or not durable: never parsed, whatever the process reported
            stopped = ';'.join(x for x in (stopped, 'TIMEOUT' if timed_out else None, 'RAW_CAPTURE_FINALISE_FAILED:' + ','.join(sealed)) if x)
        completed, facts['wall_seconds'] = host.now(), round(host.monotonic() - clock, 3)
        sizes = {c: t.stat().st_size for c, t in targets.items() if t.is_file()}
        for c, t in targets.items():
            if c not in sizes:continue
            digest_ = hashlib.sha256()
            with t.open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):digest_.update(chunk)
            facts[f'{c}_sha256'], facts[f'{c}_bytes'] = digest_.hexdigest(), sizes[c]
        if stopped is None and sum(sizes.values()) > MAX_STREAM_BYTES:  # backstop for a runner that did not enforce it
            stopped = 'RUN_STOP:RECORDING_SIZE_LIMIT'  # preserved on disk, never loaded or parsed
        if stopped is None:
            out, err = targets['stdout'].read_bytes(), targets['stderr'].read_bytes()
            try:review_facts = review(out, err, code, timed_out, p['model'], facts['session_id'])
            except CLOSE:review_facts = {'faults': ['MALFORMED_STREAM_STRUCTURE'], 'text': ''}
            facts.update({k: review_facts[k] for k in ('tokens', 'visible_generations', 'cli_list_price_estimate_usd') if k in review_facts})
            post = []
            try:
                if account(host, exe, env, auth_value, 'POSTFLIGHT') != facts['account']:post.append('ACCOUNT_CATEGORIES_CHANGED')
            except CLOSE as error:post.append(str(error) if isinstance(error, S.ScoutError) else 'POSTFLIGHT_' + type(error).__name__)
            if CS.file_hash(exe) != p['binary_sha256']:post.append('EXECUTABLE_CHANGED_DURING_RUN')
            if account_files(host) != before:post.append('DEVELOPMENT_ACCOUNT_METADATA_CHANGED')
            if (host.config / 'remote-settings.json').exists():post.append('SERVER_MANAGED_SETTINGS_CACHE_APPEARED')
            faults = review_facts['faults'] + post + (['PROCESS_TREE_STOP_UNCONFIRMED'] if tree == 'PROCESS_TREE_STOP_UNCONFIRMED' else [])
            if faults:stopped = 'RUN_STOP:' + ','.join(faults)
    error = stopped[:4000] if stopped else None
    model = p['model'] if not review_facts or 'MODEL_MISMATCH' not in review_facts['faults'] else 'UNKNOWN_OR_MISMATCHED (requested ' + p['model'] + ')'
    prov = provenance(p, auth_value, facts, invoked=invoked, completed=completed, model=model, error=error)
    state = W.finish(archive, aid, '' if error else review_facts['text'], prov, error=error)
    status = state.attempts[aid]['result']['status']
    process = start['process']; request = provider_request(process, review_facts)
    archive.append('generation_effort', {'attempt_id': aid, 'actor': {'kind': 'HUMAN', 'id': f'{auth_value["owner"].strip()} (authorised runner)'},
        'human_minutes': S.UNKNOWN, 'wall_seconds': facts.get('wall_seconds', S.UNKNOWN), 'context_id': facts['session_id'],
        'fresh_context': 'YES' if process == 'STARTED' else 'UNKNOWN', 'invocation_status': INVOCATION[request],
        'no_prior_generated_cards': 'YES', 'description': f'{VERSION}: {status}. Process start {process}; provider request {request}. '
        + (error or 'One visible generation imported.')[:3000]})
    if status == 'VALID':W.triage(archive)
    archive.export(f'exploratory-report-{aid}.json', report(archive.load()))
    # model_invocations counts CLI processes started (UNKNOWN when the launch outcome is); it never counts provider requests.
    receipt = {'schema': RECEIPT_V, 'attempt_id': aid, 'status': status, 'error': error,
               'model_invocations': {'STARTED': 1, S.UNKNOWN: S.UNKNOWN}.get(process, 0), 'process_start': process,
               'process_start_attempts': log.count('MODEL'), 'provider_request': request, 'invocation_status': INVOCATION[request],
               'administrative_commands_run': log.count('ADMIN'),
               'cards': [c for c in state.cards], 'review': {k: v for k, v in review_facts.items() if k != 'text'},
               'preflight': {k: facts[k] for k in ('cli_version', 'help_sha256', 'account') if k in facts},
               'plan_sha256': p['plan_sha256'], 'authorisation_sha256': facts['authorisation_sha256'],
               'stdout_sha256': facts.get('stdout_sha256', S.UNKNOWN), 'stderr_sha256': facts.get('stderr_sha256', S.UNKNOWN),
               'stdout_bytes': facts.get('stdout_bytes', S.UNKNOWN), 'stderr_bytes': facts.get('stderr_bytes', S.UNKNOWN),
               'raw_stream_sensitivity': 'PRIVATE: contains model thinking, local paths and session metadata; never commit or publish',
               'actual_subscription_charge': S.UNKNOWN, 'routing_authority': 'NONE', 'retried': False}
    try:archive.export(f'exploratory-receipt-{aid}.json', receipt)
    except CLOSE as problem:  # the claim stays and status reports the attempt interrupted; it is never re-run
        raise S.ScoutError(f'INTERRUPTED: receipt not written ({type(problem).__name__}); attempt {aid} recorded {status}, '
                           'claim retained and never re-run') from problem
    return receipt


def status(store):
    archive = Archive(store); state = archive.load()
    exports = sorted(x.name for x in (archive.path / 'exports').glob('exploratory-*')) if (archive.path / 'exports').is_dir() else []
    attempts = {a['id']: a.get('result', {}).get('status', 'PENDING') for a in state.attempts.values()}
    claimed = any(n.startswith('exploratory-claim-') for n in exports)
    finished = any(n.startswith('exploratory-receipt-') for n in exports)
    markers = ('STARTED' if any(n.startswith('exploratory-started-') for n in exports) else
               'DISPATCHED' if any(n.startswith('exploratory-dispatch-') for n in exports) else 'NONE')
    receipt = next((input_json(archive.path / 'exports' / n) for n in exports if n.startswith('exploratory-receipt-')), None)
    effort = next((r['invocation_status'] for r in reversed(state.efforts) if r.get('attempt_id') in state.attempts), None)
    # Without a receipt only the markers speak: a dispatch without a start marker is UNKNOWN, never "not started".
    process = receipt['process_start'] if receipt else {'NONE': 'NOT_STARTED', 'DISPATCHED': S.UNKNOWN, 'STARTED': 'STARTED'}[markers]
    invocation = effort or (receipt or {}).get('invocation_status') or ('NOT_INVOKED' if process == 'NOT_STARTED' else S.UNKNOWN)
    disagreements = [m for m, bad in (
        ('process start contradicts dispatch markers', process not in MARKER_STARTS[markers]),
        ('invocation status contradicts process start', invocation not in START_INVOCATIONS.get(process, ())),
        ('receipt and generation-effort invocation status differ', bool(receipt and effort and receipt.get('invocation_status') != effort)))
        if claimed and bad]
    return {'attempts': attempts, 'cards': list(state.cards), 'claimed': claimed, 'receipt': finished,
            'interrupted': claimed and not finished, 'process_start': process if claimed else 'NOT_STARTED',
            'invocation_status': invocation, 'accounting_agrees': not disagreements, 'disagreements': disagreements, 'exports': exports,
            'note': 'An interrupted run (claim without receipt) is never resumed; review its raw bytes manually.'}
