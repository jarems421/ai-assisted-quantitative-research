"""Read-only V003 diagnostics and fixed fictional V004 probes.

No real-generation command exists here. Frozen V003 modules/records are never
patched. Published summaries contain allowlisted counts/codes, never stream text.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

from jsonschema import Draft202012Validator
from src.research.spec import canonical, digest
from . import schema as S
from .claude_subscription import (ClaudeSubscription, SYSTEM_PROMPT, file_hash,
                                  safe_output, development_account_metadata)
from .storage import Archive, input_json

INPUT_CAP = 30000
OUTPUT_CAP = 6000
PROBES = (('STRUCTURED_ONE_TURN', True, 1), ('STRUCTURED_TWO_TURNS_DIAGNOSTIC', True, 2),
          ('RAW_JSON_ONE_TURN', False, 1))


def events_from(stdout):
    events = [S.json_loads(line) for line in stdout.splitlines() if line.strip()]
    if any(not isinstance(e, dict) for e in events): raise S.ScoutError('invalid CLI event object')
    return events


def termination(events, returncode, stderr=''):
    """Structured terminal evidence wins; arbitrary stdout is never an auth test."""
    terminal = [e for e in events if e.get('type') == 'result']
    if len(terminal) > 1: return 'AMBIGUOUS_TERMINAL_RESULTS'
    result = terminal[0] if terminal else {}
    subtype = result.get('subtype')
    known = {'error_max_turns': 'CLI_MAX_TURNS',
             'error_max_structured_output_retries': 'CLI_STRUCTURED_OUTPUT_RETRIES_EXHAUSTED',
             'error_max_budget_usd': 'CLI_BUDGET_STOP'}
    if subtype in known: return known[subtype]
    if result.get('api_error_status') == 401: return 'AUTHENTICATION_FAILED'
    if result.get('api_error_status') == 429: return 'RATE_LIMIT'
    # Only designated structured error fields count. UUIDs, generated prose,
    # plugin names, prompt text and general result.errors strings cannot do so.
    for event in events:
        error = event.get('error')
        if isinstance(error, dict):
            if error.get('type') == 'authentication_error' or error.get('status') == 401:
                return 'AUTHENTICATION_FAILED'
            if error.get('type') == 'rate_limit_error' or error.get('status') == 429:
                return 'RATE_LIMIT'
    if subtype == 'success' and result.get('is_error') is False and returncode == 0: return 'SUCCESS'
    # Narrow fallback for a pre-envelope CLI failure, using stderr only.
    if not terminal and re.fullmatch(r'\s*(?:Error:\s*)?(?:Authentication failed|Not logged in|HTTP 401 Unauthorized)[.!]?\s*', stderr, re.I):
        return 'AUTHENTICATION_FAILED'
    return 'CLI_FAILED' if returncode else 'MISSING_OR_FAILED_TERMINAL_RESULT'


def count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def usage_summary(terminal):
    usage = terminal.get('usage', {})
    parts = {k: usage.get(k, S.UNKNOWN) for k in
             ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')}
    total = sum(parts.values()) if all(count(v) for v in parts.values()) else S.UNKNOWN
    output = usage.get('output_tokens', S.UNKNOWN)
    output = output if count(output) else S.UNKNOWN
    return {'input_components': parts, 'input_total': total, 'output_total': output,
            'thinking_tokens': usage.get('output_tokens_details', {}).get('thinking_tokens', S.UNKNOWN),
            'input_cap': INPUT_CAP, 'output_cap': OUTPUT_CAP,
            'input_excess': max(0, total - INPUT_CAP) if total != S.UNKNOWN else S.UNKNOWN,
            'output_excess': max(0, output - OUTPUT_CAP) if output != S.UNKNOWN else S.UNKNOWN}


def analyse(stdout, returncode, response_schema, *, structured=True, expected_model=None, stderr=''):
    events = events_from(stdout)
    terminals = [e for e in events if e.get('type') == 'result']
    terminal = terminals[0] if len(terminals) == 1 else {}
    initial = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    init = initial[0] if len(initial) == 1 else {}
    assistants = [e for e in events if e.get('type') == 'assistant']
    mids = {e.get('message', {}).get('id') for e in assistants} - {None}
    request_ids = {e.get('request_id') for e in assistants} - {None}
    tools = [b for e in assistants for b in e.get('message', {}).get('content', []) if b.get('type') == 'tool_use']
    synthetic = [e for e in events if e.get('type') == 'user' and e.get('isSynthetic') is True]
    output_limit_notifications = sum(all(re.search(word, ' '.join(b.get('text', '') for b in
        e.get('message', {}).get('content', []) if isinstance(b, dict)), re.I)
        for word in ('output', 'token', 'limit')) for e in synthetic)
    tool_errors = [b for e in events if e.get('type') == 'user'
                   for b in e.get('message', {}).get('content', [])
                   if b.get('type') == 'tool_result' and b.get('is_error') is True]
    schema_errors = []
    for tool in tools:
        for error in Draft202012Validator(response_schema).iter_errors(tool.get('input')):
            # No error.message, instance, generated value, quote or tool text.
            schema_errors.append({'validator': error.validator, 'path': list(error.path)})
    seen = {init.get('model')} | set(terminal.get('modelUsage', {})) | {
        e.get('message', {}).get('model') for e in assistants}
    seen.discard(None)
    allowed = {'StructuredOutput'} if structured else set()
    environment = (len(initial) == 1 and set(init.get('tools', [])) <= allowed and 'tools' in init
        and init.get('skills') == [] and init.get('mcp_servers') == []
        and init.get('permissionMode') == 'dontAsk' and init.get('apiKeySource') == 'none'
        and not terminal.get('permission_denials')
        and terminal.get('subagent_stats', {}).get('spawned', 0) == 0
        and all(t.get('name') in allowed for t in tools))
    usage = usage_summary(terminal)
    reason = termination(events, returncode, stderr)
    deviations = []
    if len(mids) != 1: deviations.append('ONE_VISIBLE_GENERATION_NOT_ESTABLISHED')
    if len(request_ids) > 1: deviations.append('MULTIPLE_VISIBLE_REQUEST_IDS')
    if synthetic: deviations.append('CLI_SYNTHETIC_REPROMPT_OBSERVED')
    if output_limit_notifications: deviations.append('CLI_OUTPUT_LIMIT_CONTINUATION_OBSERVED')
    if not environment: deviations.append('ENVIRONMENT_ISOLATION_NOT_ESTABLISHED')
    if expected_model and seen != {expected_model}: deviations.append('MODEL_MISMATCH')
    if init.get('effort', S.UNKNOWN) not in (S.UNKNOWN, 'medium'): deviations.append('EFFORT_MISMATCH')
    if len(tools) > (1 if structured else 0): deviations.append('ADDITIONAL_FORMATTING_OR_TOOL_CALL')
    if tool_errors or schema_errors: deviations.append('STRUCTURED_OUTPUT_VALIDATION_FAILED')
    for kind in ('input', 'output'):
        if usage[kind + '_total'] == S.UNKNOWN: deviations.append(kind.upper() + '_USAGE_UNKNOWN')
        elif usage[kind + '_excess']: deviations.append(kind.upper() + '_TOKEN_CEILING_EXCEEDED')
    output = terminal.get('structured_output') if structured else None
    if not structured:
        try: output = S.json_loads(terminal.get('result', ''))
        except (S.ScoutError, TypeError): pass
        original_text = ''.join(b.get('text', '') for e in assistants
            for b in e.get('message', {}).get('content', []) if b.get('type') == 'text')
        if original_text != terminal.get('result', ''):
            deviations.append('TERMINAL_OUTPUT_DIFFERS_FROM_ORIGINAL_TEXT')
    output_valid = output is not None and not list(Draft202012Validator(response_schema).iter_errors(output))
    if structured and tools and output != tools[0].get('input'):
        deviations.append('TERMINAL_OUTPUT_DIFFERS_FROM_FORMATTING_INPUT')
    if not output_valid: deviations.append('TERMINAL_SCHEMA_NOT_SATISFIED')
    return {'schema': 'SCOUT_CLI_DIAGNOSTICS_V004', 'termination': reason,
            'terminal_subtype': terminal.get('subtype', S.UNKNOWN), 'returncode': returncode,
            'reported_agentic_turns': terminal.get('num_turns', S.UNKNOWN),
            'assistant_stream_events': len(assistants), 'distinct_visible_assistant_messages': len(mids),
            'distinct_visible_request_ids': len(request_ids), 'underlying_provider_requests': S.UNKNOWN,
            'formatting_tool_calls': sum(t.get('name') == 'StructuredOutput' for t in tools),
            'failed_tool_results': len(tool_errors), 'formatting_schema_errors': schema_errors,
            'synthetic_output_limit_notifications': output_limit_notifications,
            'environment_isolation_verified': environment,
            'single_visible_generation_verified': len(mids) == 1 and len(request_ids) <= 1 and not synthetic,
            'usage': usage, 'terminal_schema_valid': output_valid, 'deviations': deviations,
            'candidate_one_generation_pass': reason == 'SUCCESS' and not deviations,
            'real_generation_authorised': False}


def fictional_input():
    """Real Scout schema; ALL source/context/instructions are created fictionally.

    No V003 request, seed pool, prompt definition, catalogue or prior response is read.
    """
    schema = copy.deepcopy(S.GENERATION)
    schema['properties']['ideas']['minItems'] = 2
    schema['properties']['ideas']['maxItems'] = 2
    # Roughly the retained prompt's byte scale, with fabricated evidence and
    # memory. This is a load probe, not a representative economic experiment.
    evidence = [{'id': 'SEED-FICTIONAL-' + str(i), 'company': 'Aster Crates / Lumen Packers',
        'text': ('FICTIONAL ONLY. Aster has twelve inspection shifts per week. Lumen uses refundable crates. '
                 'Bookings, allocations, contracts, prices and public clocks are UNKNOWN. ') * 7}
                for i in range(10)]
    memory = [{'id': 'HIST-FICTIONAL-' + str(i), 'verdict': 'FICTIONAL_NOT_CHECKED',
        'missing_requirement': 'REQ_DOCUMENTED_ALLOCATION',
        'description': ('FICTIONAL ONLY. Named customer allocations are missing. '
                        'No original relationship or listed exposure is established. ') * 3}
              for i in range(12)]
    payload = {'fixture': 'SYNTHETIC_ONLY_V004_DIAGNOSTIC',
        'instructions': 'Create exactly two concise, fictional economic hypothesis cards matching response_schema. '
        'Use only fictional Aster Crates, Lumen Packers or invented companies. '
        'Fill every required field. seed_ids and historical_refs may be empty. '
        'Keep four ordered links UNVERIFIED with empty evidence. Do not invent verified sources. '
        'Use canonical requirement REQ_DOCUMENTED_ALLOCATION. '
        'Use one CAPACITY_COMPETITION and one WORKING_CAPITAL mechanism. '
        'Keep every free-text field short, normally under 18 words. '
        'Return one raw JSON object, no Markdown, no explanation, no followup, no tools other than the supplied output formatter if present. '
        'Do not stringify the ideas array. All content here is fictional; no research task is requested.',
        'response_schema': schema, 'fictional_evidence': evidence, 'fictional_memory': memory}
    return canonical(payload).decode(), schema


def synthetic_probe(directory, *, client=None, runner=subprocess.run):
    """Exactly three prospective diagnostic slots, no retry, no real-input option."""
    root = Archive(directory)
    if root.path.exists() and any(root.path.iterdir()): raise S.ScoutError('new empty synthetic probe directory required')
    text, schema = fictional_input()
    plan = {'schema': 'SCOUT_V004_FIXED_FICTIONAL_PROBE_PLAN', 'probes': [
        {'id': name, 'structured_output': structured, 'max_agentic_turns': turns}
        for name, structured, turns in PROBES], 'payload_sha256': S.hash_text(text),
        'response_schema_sha256': digest(schema), 'payload_bytes': len(text.encode()),
        'request_timeout_seconds': 150, 'cli_invocation_ceiling': 3,
        'input_cap': INPUT_CAP, 'output_cap': OUTPUT_CAP, 'real_generation_authorised': False,
        'diagnostic_implementation_sha256': file_hash(__file__),
        'purpose': 'Compare formatter behavior, turns and aggregate budgets on fixed fictional full-schema load. Two-turn probe is diagnostic only; it does not relax the one-generation rule.'}
    # Immutable pre-dispatch reservation before even local auth inspection.
    root.export('fictional-probe-plan-v004.json', plan)
    client = client or ClaudeSubscription()
    before = development_account_metadata()
    account_unchanged = True
    inspection = client.inspect()
    model = 'claude-opus-5-5'
    rows = []
    for name, structured, turns in PROBES:
        cid = str(uuid.uuid4())
        root.export(name + '-started.json', {'context_id': cid, 'started_at': S.utc_now(),
                    'plan_sha256': digest(plan), 'slot_consumed': True})
        args = client.arguments(model, schema, cid)
        if not structured:
            index = args.index('--json-schema'); del args[index:index + 2]
        env = client.env.copy(); env['CLAUDE_CODE_MAX_TURNS'] = str(turns)
        started = time.monotonic(); invoked = S.utc_now()
        try:
            with tempfile.TemporaryDirectory(prefix='scout-v004-fictional-') as cwd:
                p = runner(args, input=text, env=env, cwd=cwd, shell=False,
                           capture_output=True, text=True, encoding='utf-8', timeout=150)
            raw, stderr, code = p.stdout, p.stderr, p.returncode
            # The diagnostics accept no private prompt parameter. Captures still
            # stay private, and apparent credentials are withheld before writing.
            safe_raw, safe_stderr = safe_output(raw), safe_output(stderr)
            if raw != safe_raw or stderr != safe_stderr:
                summary = {'termination': 'CREDENTIAL_OUTPUT_WITHHELD', 'candidate_one_generation_pass': False}
            else:
                try: summary = analyse(raw, code, schema, structured=structured, expected_model=model, stderr=stderr)
                except (S.ScoutError, KeyError, TypeError):
                    summary = {'termination': 'INVALID_CLI_ENVELOPE', 'candidate_one_generation_pass': False}
            receipt = {'id': name, 'invoked_at': invoked, 'completed_at': S.utc_now(),
                'wall_seconds': round(time.monotonic() - started, 6), 'context_id': cid,
                'returncode': code, 'stdout': safe_raw, 'stderr': safe_stderr,
                'stdout_sha256': S.hash_text(raw), 'stderr_sha256': S.hash_text(stderr),
                'arguments': args[1:], 'environment_controls': {k: v for k, v in env.items() if k.startswith('CLAUDE_')},
                'diagnostics': summary}
        except (subprocess.TimeoutExpired, OSError) as problem:
            receipt = {'id': name, 'context_id': cid, 'invoked_at': invoked, 'completed_at': S.utc_now(),
                'wall_seconds': round(time.monotonic() - started, 6),
                'diagnostics': {'termination': 'TIMEOUT' if isinstance(problem, subprocess.TimeoutExpired) else 'PROCESS_START_FAILED',
                                'candidate_one_generation_pass': False}}
        after = development_account_metadata()
        account_unchanged = account_unchanged and before == after
        receipt['development_metadata_before'] = before
        receipt['development_metadata_after'] = after
        receipt['development_account_metadata_unchanged'] = before == after
        root.export(name + '-receipt.json', receipt)
        rows.append({'id': name, 'receipt_sha256': digest(receipt), 'wall_seconds': receipt['wall_seconds'],
                     'diagnostics': receipt['diagnostics']})
        if not account_unchanged or receipt['diagnostics']['termination'] in ('AUTHENTICATION_FAILED', 'RATE_LIMIT', 'TIMEOUT',
                                                      'PROCESS_START_FAILED', 'CREDENTIAL_OUTPUT_WITHHELD'):
            break
    result = {'schema': 'SCOUT_V004_FICTIONAL_PROBE_SUMMARY', 'plan_sha256': digest(plan),
              'inspection': inspection, 'probes': rows,
              'development_account_metadata_unchanged': account_unchanged and before == development_account_metadata(),
              'real_inputs_transmitted': False, 'real_generation_authorised': False,
              'hard_provider_request_cap_verified': False}
    root.export('fictional-probe-summary-v004.json', result)
    return result


def replay_fictional(directory):
    """Offline revalidation; preserve original plan, receipts and failed guard."""
    root = Archive(directory)
    original = input_json(root.path / 'exports/fictional-probe-summary-v004.json')
    _, schema = fictional_input()
    rows = []
    for row in original['probes']:
        receipt = input_json(root.path / 'exports' / (row['id'] + '-receipt.json'))
        if digest(receipt) != row['receipt_sha256']: raise S.ScoutError('fictional receipt hash mismatch')
        if 'stdout' in receipt:
            if S.hash_text(receipt['stdout']) != receipt['stdout_sha256']:
                raise S.ScoutError('fictional stdout hash mismatch or withheld output')
            summary = analyse(receipt['stdout'], receipt['returncode'], schema,
                structured=row['id'] != 'RAW_JSON_ONE_TURN', expected_model='claude-opus-5-5', stderr=receipt['stderr'])
        else: summary = receipt['diagnostics']
        rows.append({'id': row['id'], 'receipt_sha256': row['receipt_sha256'], 'diagnostics': summary})
    return {'schema': 'SCOUT_V004_OFFLINE_FICTIONAL_REPLAY', 'original_summary_sha256': digest(original),
            'analyser_sha256': file_hash(__file__), 'probes': rows,
            'development_account_metadata_unchanged': original['development_account_metadata_unchanged'],
            'validation_complete': original['development_account_metadata_unchanged']
                and all(r['diagnostics']['candidate_one_generation_pass'] for r in rows),
            'new_cli_invocations': 0, 'real_generation_authorised': False,
            'hard_provider_request_cap_verified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    x = sub.add_parser('analyse-retained'); x.add_argument('--receipt', required=True); x.add_argument('--request', required=True)
    x = sub.add_parser('fictional-probes'); x.add_argument('--store', required=True)
    x = sub.add_parser('replay-fictional'); x.add_argument('--store', required=True)
    args = parser.parse_args(argv)
    if args.command == 'analyse-retained':
        receipt, request = input_json(args.receipt), input_json(args.request)
        result = analyse(receipt['stdout'], receipt['returncode'], request['response_schema'],
                         expected_model=receipt['requested_model'], stderr=receipt['stderr'])
    elif args.command == 'fictional-probes': result = synthetic_probe(args.store)
    else: result = replay_fictional(args.store)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__': main()
