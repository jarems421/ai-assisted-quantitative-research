"""R3 versioned offline raw-JSON recorded-stream adapter. No hosted dispatch exists.

The synthetic notice profile is deliberately NOT certified as a Claude wire
contract. Unknown real continuation forms must fail closed in a future adapter.
All diagnostics are allowlisted codes; raw bytes belong in the private journal.
"""
from dataclasses import dataclass
import math
import re

from src.research.spec import digest
from .. import schema as S
from . import policy
from .package import REQUEST_VERSION
COMPONENTS = policy.COMPONENTS

VERSION = 'SCOUT_V004_RECORDED_RAW_JSON_R3'
NOTICE = 'Output token limit reached. Continue the same unfinished response without rewriting.'
MAX_RECORDING_BYTES = 12 * 1024 * 1024  # IO bound only, never a token certificate.


@dataclass(frozen=True)
class Recording:
    stdout: bytes
    stderr: bytes = b''
    returncode: int = 0
    timed_out: bool = False
    wall_seconds: float = 1.0
    fictional: bool = True
    live_usage_samples: tuple = ()


def classify_terminal(events, returncode, stderr, timed_out):
    if timed_out: return 'TIMEOUT'
    terminals = [e for e in events if e.get('type') == 'result']
    t = terminals[0] if len(terminals) == 1 else {}
    known = {'error_max_turns': 'CLI_MAX_TURNS', 'error_max_budget_usd': 'CLI_BUDGET_STOP',
             'error_max_structured_output_retries': 'PROHIBITED_SCHEMA_REPAIR'}
    if isinstance(t.get('subtype'), str) and t['subtype'] in known: return known[t['subtype']]
    for e in events:
        error = e.get('error', {})
        if not isinstance(error, dict): continue
        status = e.get('api_error_status', error.get('status'))
        if status == 401 or error.get('type') == 'authentication_error': return 'AUTHENTICATION_FAILED'
        if status == 429 or error.get('type') == 'rate_limit_error': return 'RATE_LIMIT'
    if not terminals and re.fullmatch(r'\s*(?:Error:\s*)?(?:Authentication failed|Not logged in|HTTP 401 Unauthorized)[.!]?\s*', stderr, re.I):
        return 'AUTHENTICATION_FAILED'
    if len(terminals) == 1 and returncode == 0 and t.get('subtype') == 'success' and t.get('is_error') is False:
        return 'SUCCESS'
    return 'CLI_FAILED'


def _review(recording, request, session_id):
    """Review exact immutable recorded bytes. Never trims/extracts/repairs JSON.

    Assistant events in the retained fictional profile carry disjoint, ordered text fragments;
    repeated snapshots, duplicate blocks, missing IDs and unknown events fail.
    A future live CLI adapter must independently demonstrate this profile.
    """
    if not isinstance(recording, Recording) or recording.fictional is not True:
        raise S.ScoutError('this adapter accepts fictional recordings only')
    if not isinstance(recording.stdout, bytes) or not isinstance(recording.stderr, bytes):
        raise S.ScoutError('original bytes required')
    faults, format_faults, events, assembly = [], [], [], ''
    def fault(code):
        if code not in faults: faults.append(code)
    if len(recording.stdout) + len(recording.stderr) > MAX_RECORDING_BYTES: fault('RECORDING_IO_LIMIT')
    try:
        raw = recording.stdout.decode('utf-8'); stderr = recording.stderr.decode('utf-8')
        for line in raw.splitlines():
            if line.strip():
                e = S.json_loads(line)
                if not isinstance(e, dict): raise S.ScoutError('event object required')
                events.append(e)
    except (UnicodeError, S.ScoutError):
        fault('INVALID_STREAM_ENVELOPE'); stderr = ''
    inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    terminals = [e for e in events if e.get('type') == 'result']
    init = inits[0] if len(inits) == 1 else {}
    terminal = terminals[0] if len(terminals) == 1 else {}
    if len(inits) != 1 or not events or events[0] != init: fault('INITIALISATION_NOT_ESTABLISHED')
    if len(terminals) != 1 or not events or events[-1] != terminal: fault('TERMINAL_NOT_ESTABLISHED')
    if (init.get('tools') != [] or init.get('skills') != [] or init.get('mcp_servers') != [] or init.get('plugins', []) != []
            or init.get('permissionMode') != 'dontAsk' or init.get('apiKeySource') != 'none'):
        fault('ENVIRONMENT_NOT_ESTABLISHED')
    subagents = terminal.get('subagent_stats')
    if (terminal.get('permission_denials') != [] or not isinstance(subagents, dict) or subagents.get('spawned') != 0
            or 'structured_output' in terminal): fault('ENVIRONMENT_OR_FORMATTER_DEVIATION')
    model = request['model']; ids, request_ids, texts, stops = [], {}, {}, {}
    last_id, notice_pending, notices = None, False, 0
    for e in events:
        if e.get('session_id') != session_id: fault('CONTEXT_CHANGED_OR_UNKNOWN')
        kind = e.get('type')
        if kind == 'system':
            if e is not init: fault('UNEXPECTED_SYSTEM_EVENT')
            if e.get('model') != model: fault('MODEL_MISMATCH')
        elif kind == 'assistant':
            msg = e.get('message', {})
            if not isinstance(msg, dict): fault('MALFORMED_ASSISTANT'); continue
            mid, rid = msg.get('id'), e.get('request_id')
            if not isinstance(mid, str) or not mid or not isinstance(rid, str) or not rid:
                fault('MESSAGE_OR_REQUEST_ID_UNKNOWN'); continue
            if msg.get('model') != model: fault('MODEL_MISMATCH')
            if mid not in ids:
                if ids:
                    # A second visible generation must append to an unfinished
                    # first one; a complete/merely schema-invalid answer cannot
                    # be replaced under the label "continuation".
                    if not notice_pending or stops.get(last_id) != 'max_tokens': fault('UNVERIFIED_CONTINUATION')
                    try: S.json_loads(''.join(texts.values())); fault('COMPLETE_ANSWER_REPLACEMENT')
                    except S.ScoutError: pass
                if rid in request_ids.values(): fault('REQUEST_ID_REUSED')
                ids.append(mid); request_ids[mid] = rid; texts[mid] = ''
                if len(ids) > 2: fault('THIRD_VISIBLE_GENERATION')
                notice_pending = False
            elif mid != last_id or request_ids[mid] != rid or mid in stops:
                fault('REORDERED_OR_REWRITTEN_GENERATION')
            last_id = mid
            content = msg.get('content')
            if not isinstance(content, list): fault('MALFORMED_ASSISTANT'); continue
            for block in content:
                if not isinstance(block, dict): fault('MALFORMED_CONTENT'); continue
                if block.get('type') == 'text' and isinstance(block.get('text'), str):
                    texts[mid] += block['text']
                elif block.get('type') not in ('thinking', 'redacted_thinking'):
                    fault('PROHIBITED_TOOL_OR_CONTENT')
            stop = msg.get('stop_reason')
            if stop is not None:
                if stop not in ('end_turn', 'max_tokens'): fault('PROHIBITED_STOP_REASON')
                stops[mid] = stop
        elif kind == 'user':
            expected = {'role': 'user', 'content': [{'type': 'text', 'text': NOTICE}]}
            if (e.get('isSynthetic') is not True or e.get('message') != expected
                    or len(ids) != 1 or stops.get(last_id) != 'max_tokens' or notice_pending):
                fault('UNVERIFIED_CONTINUATION_NOTICE')
            notice_pending = True; notices += 1
        elif kind == 'result':
            if e is not terminal: fault('MULTIPLE_TERMINAL_RESULTS')
        elif kind == 'error': fault('STRUCTURED_ERROR_OBSERVED')
        else: fault('UNRECOGNISED_EVENT')
        if 'request_id' in e and kind != 'assistant': fault('UNEXPLAINED_REQUEST_ID')
    assembly = ''.join(texts.values())
    if not ids or notice_pending or notices != len(ids) - 1: fault('GENERATION_FLOW_NOT_ESTABLISHED')
    if ids and stops.get(last_id) != 'end_turn': fault('UNFINISHED_GENERATION')
    if not isinstance(terminal.get('result'), str) or terminal['result'] != assembly:
        fault('TERMINAL_ASSEMBLY_MISMATCH')
    reason = classify_terminal(events, recording.returncode, stderr, recording.timed_out)
    if reason != 'SUCCESS': fault(reason)
    models = terminal.get('modelUsage')
    if not isinstance(models, dict) or set(models) != {model}: fault('MODEL_USAGE_IDENTITY_UNKNOWN_OR_CHANGED')
    resource = policy.assess_final_usage(terminal.get('usage'),
                  models.get(model) if isinstance(models, dict) else None, has_output=bool(assembly))
    live = policy.review_live_samples(recording.live_usage_samples, session_id)
    resource = policy.reconcile(resource, live)
    if (not isinstance(recording.wall_seconds, (int, float)) or isinstance(recording.wall_seconds, bool)
            or not math.isfinite(recording.wall_seconds) or not 0 <= recording.wall_seconds <= 600):
        fault('WALL_USAGE_UNKNOWN_OR_EXCEEDED')
    integrity_faults = list(faults)
    for code in resource['stop_reasons']: fault(code)
    value = None
    try:
        value = S.json_loads(assembly)
        S.validate(request['response_schema'], value)
        for idea in value['ideas']:
            S.validate_idea(idea, request['lane'], request['context']['seeds'], request['context']['memory'])
    except (S.ScoutError, KeyError, TypeError):
        # Never publish error.message: it can embed private generated text.
        format_faults.append('JSON_SCHEMA_OR_LANE_SEMANTIC_FAILURE')
    outcome = 'RUN_STOP' if faults else 'FORMAT_FAILURE' if format_faults else 'VALID'
    return {'schema': VERSION, 'outcome': outcome, 'faults': faults, 'format_faults': format_faults,
            'termination': reason, 'resource': resource, 'integrity_faults': integrity_faults,
            'content_status': 'INVALID' if format_faults else 'VALID', 'visible_generations': len(ids),
            'visible_request_ids': len(set(request_ids.values())), 'continuations': notices,
            'reported_agentic_turns': terminal.get('num_turns', S.UNKNOWN),
            'underlying_provider_requests': S.UNKNOWN, 'exact_output': assembly,
            'output_sha256': S.hash_text(assembly), 'value': value,
            'cli_list_price_estimate_usd': terminal.get('total_cost_usd', S.UNKNOWN),
            'actual_subscription_charge': S.UNKNOWN, 'wall_seconds': recording.wall_seconds,
            'generation_trace_sha256': digest({'messages': ids, 'requests': request_ids}),
            'hosted_authorised': False}


def review(recording, request, session_id):
    """Malformed envelopes remain consumed failures, never uncaught repairs."""
    if not isinstance(recording, Recording) or recording.fictional is not True:
        raise S.ScoutError('fictional recorded invocation required')
    if not isinstance(recording.stdout, bytes) or not isinstance(recording.stderr, bytes):
        raise S.ScoutError('original bytes required')
    if request.get('schema') != REQUEST_VERSION or request.get('resource_policy_sha256') != policy.policy_hash():
        raise S.ScoutError('new R3 request/policy required; no old receipt or request migration')
    try: return _review(recording, request, session_id)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError):
        resource = policy.reconcile(policy.assess_final_usage(None), policy.review_live_samples(recording.live_usage_samples, session_id))
        return {'schema': VERSION, 'outcome': 'RUN_STOP', 'faults': ['MALFORMED_STREAM_STRUCTURE', *resource['stop_reasons']],
                'integrity_faults': ['MALFORMED_STREAM_STRUCTURE'], 'content_status': 'UNDETERMINED',
                'format_faults': [], 'termination': 'UNKNOWN_MALFORMED_STREAM',
                'resource': resource, 'visible_generations': S.UNKNOWN,
                'visible_request_ids': S.UNKNOWN, 'continuations': S.UNKNOWN,
                'reported_agentic_turns': S.UNKNOWN, 'underlying_provider_requests': S.UNKNOWN,
                'exact_output': '', 'output_sha256': S.hash_text(''), 'value': None,
                'cli_list_price_estimate_usd': S.UNKNOWN, 'actual_subscription_charge': S.UNKNOWN,
                'wall_seconds': recording.wall_seconds, 'generation_trace_sha256': S.UNKNOWN,
                'hosted_authorised': False}
