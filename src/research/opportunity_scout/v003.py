"""Prospective V003 subscription comparison. Real dispatch requires owner consent.

Run ``python -m src.research.opportunity_scout.v003 --help``. This module never
changes V002 packages and never dispatches models during preparation or import.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import hmac
from pathlib import Path
import sys
import uuid

from src.research.spec import canonical, digest
from . import engine as E, evaluation as V, schema as S, workflow as W
from .accounting import fairness
from .claude_subscription import (ClaudeSubscription, PROVIDER, SYSTEM_PROMPT,
                                  SYNTHETIC_TEXT, SYNTHETIC_SCHEMA,
                                  controls, exact_model, file_hash, synthetic_preflight)
from .storage import Archive, ROOT, input_json

MANIFEST = 'comparison-manifest-v003.json'
BINDING = 'comparison-runtime-v003.json'
DEFAULT_PACKAGE = ROOT / 'docs/opportunity_scout/first_comparison_v002'
IMPLEMENTATION = ('v003.py', 'claude_subscription.py', 'schema.py', 'engine.py',
                  'evaluation.py', 'workflow.py', 'accounting.py', 'prompts.py', 'storage.py')
PRIVACY = ('Anthropic receives the exact frozen user prompts, response schemas and system prompt, '
           'plus CLI authentication/routing and service metadata. Consumer subscription data use '
           'and retention depend on the account settings and applicable terms; no zero retention '
           'or no-training guarantee is established. CLI list-price estimates are not subscription '
           'charges. Canonical model ID pinning cannot certify immutable weights or a server build. '
           'Provider requests and internal service activity are not independently observable. '
           'CLI isolation is not an OS sandbox. No source acquisition, M/H approval, trading, '
           'Jev, OpenRouter or other hosted provider is authorised.')


def write_once(root, name, value):
    return root.export(name, value)


def validate_binding(value):
    S.validate(S.obj({'schema': {'const': 'SCOUT_COMPARISON_RUNTIME_V003'},
        'manifest_sha256': S.HASH, 'model': S.LABEL, 'provider': {'const': PROVIDER},
        'parameters': {'const': controls()}, 'bound_at': S.TEXT,
        'preflight_sha256': S.HASH, 'inspection': {'type': 'object'},
        'hosted_transmission_authorised': {'const': False}}), value)
    exact_model(value['model']); S.timestamp(value['bound_at'])


def request_name(condition, aid):
    return condition + '-' + aid + '-request-v003.json'


def verify_preflight(preflight):
    if (preflight.get('schema') != 'SCOUT_CLAUDE_PREFLIGHT_V003' or preflight.get('passed') is not True
            or preflight.get('research_inputs_transmitted') is not False
            or preflight.get('development_account_files_unchanged') is not True
            or preflight.get('real_comparison_attempts_consumed') != 0
            or len(preflight.get('invocations', [])) != 2):
        raise S.ScoutError('a passing, fixed synthetic CLI preflight is required')
    exact_model(preflight['canonical_model'])
    for index, row in enumerate(preflight['invocations']):
        if row['error'] or not row['isolation_verified'] or row['actual_model'] != preflight['canonical_model']:
            raise S.ScoutError('synthetic preflight isolation/model check failed')
        if (row.get('schema') != 'SCOUT_CLAUDE_INVOCATION_V003'
                or row['requested_model'] != ('opus' if index == 0 else preflight['canonical_model'])
                or row['payload_sha256'] != S.hash_text(SYNTHETIC_TEXT)
                or row['response_schema_sha256'] != digest(SYNTHETIC_SCHEMA)
                or row['stdout_sha256'] != S.hash_text(row['stdout'])
                or row['parameters'] != controls() or row['returncode'] != 0):
            raise S.ScoutError('synthetic preflight receipt does not match fixed input and controls')
        # Replay CLI envelope checks rather than trusting a stored success flag.
        replay = copy.deepcopy(row); replay['error'] = None
        ClaudeSubscription._parse(replay, row['stdout'], row['requested_model'])
        if replay['error'] or not replay['isolation_verified'] or replay['actual_model'] != preflight['canonical_model']:
            raise S.ScoutError('synthetic preflight envelope replay failed')
        S.validate(SYNTHETIC_SCHEMA, S.json_loads(replay['output']))
    if preflight['inspection']['controls'] != controls(): raise S.ScoutError('preflight controls changed')


def prepare(directory, preflight_file, package=DEFAULT_PACKAGE):
    root = Archive(directory)
    if root.path.exists() and any(root.path.iterdir()): raise S.ScoutError('prepare in a new empty V003 directory')
    preflight = input_json(preflight_file); verify_preflight(preflight)
    source = Path(package)
    old_manifest = input_json(source / 'comparison-manifest.json')
    if (old_manifest.get('schema') != 'SCOUT_COMPARISON_PACKAGE_V002'
            or old_manifest['protocol_sha256'] != digest(V.protocol('V002'))
            or old_manifest['generation_status'] != 'NOT_RUN'
            or old_manifest['hosted_transmission_authorised'] is not False
            or set(old_manifest['files']) != {c + '-blueprint.json' for c in V.CONDITIONS}):
        raise S.ScoutError('need the frozen NOT_RUN local-only V002 source package')
    blueprints = {n: input_json(source / n) for n in old_manifest['files']}
    for name, data in blueprints.items():
        if digest(data) != old_manifest['files'][name]: raise S.ScoutError('V002 source blueprint hash mismatch')
        if any(e['type'] not in ('batch', 'seed', 'prompt', 'attempt_start') for e in data['events']):
            raise S.ScoutError('generated results are forbidden in the input pool')
    # Replay byte-preserved V002 inputs locally; no catalogue refresh, API or model call.
    files, requests, states = {}, [], {}
    source_files = {n: file_hash(source / n) for n in ['comparison-manifest.json', *blueprints]}
    for condition in V.CONDITIONS:
        name = condition + '-blueprint.json'; data = blueprints[name]
        archive = Archive(root.path / condition)
        for event in data['events']:
            archive.append(event['type'], event['record'], recorded_at=event['recorded_at'])
        write_once(root, name, data)
        files[name] = file_hash(root.path / 'exports' / name)
        state = archive.load(); states[condition] = state
        if [state.prompts[a['prompt_id']]['lane'] for a in state.attempts.values()] != V.protocol('V003')['allocation'][condition]:
            raise S.ScoutError('input allocation differs from frozen design')
        for aid, attempt in state.attempts.items():
            prompt = state.prompts[attempt['prompt_id']]
            payload = {'schema': 'SCOUT_HOSTED_REQUEST_V003', 'condition': condition,
                'attempt_id': aid, 'prompt': prompt, 'transmitted_text': canonical(prompt).decode(),
                'response_schema': prompt['response_schema'], 'system_prompt': SYSTEM_PROMPT}
            n = request_name(condition, aid); write_once(root, n, payload)
            files[n] = file_hash(root.path / 'exports' / n)
            requests.append({'condition': condition, 'attempt_id': aid, 'file': n,
                'payload_sha256': S.hash_text(payload['transmitted_text']),
                'response_schema_sha256': digest(payload['response_schema']), 'cards': 2})
    if len(requests) != 12: raise S.ScoutError('the comparison requires exactly 12 frozen requests')
    if (len({digest(s.seeds) for s in states.values()}) != 1
            or len({digest(s.batch['memory']) for s in states.values()}) != 1
            or len({s.batch['knowledge_cutoff'] for s in states.values()}) != 1):
        raise S.ScoutError('eligible evidence/memory pool or knowledge cutoff differs')
    write_once(root, 'evaluation-protocol-v003.json', V.protocol('V003'))
    files['evaluation-protocol-v003.json'] = file_hash(root.path / 'exports/evaluation-protocol-v003.json')
    write_once(root, 'synthetic-preflight-v003.json', preflight)
    files['synthetic-preflight-v003.json'] = file_hash(root.path / 'exports/synthetic-preflight-v003.json')
    manifest = {'schema': 'SCOUT_COMPARISON_PACKAGE_V003', 'created_at': S.utc_now(),
        'protocol_sha256': digest(V.protocol('V003')), 'source_v002_manifest_sha256': digest(old_manifest),
        'source_files_sha256': source_files, 'files_sha256': files, 'requests': requests,
        'implementation_files_sha256': {n: file_hash(Path(__file__).with_name(n)) for n in IMPLEMENTATION},
        'provider': PROVIDER, 'model': preflight['canonical_model'], 'parameters': controls(),
        'generation_status': 'NOT_RUN', 'hosted_transmission_authorised': False,
        'source_acquisition_authorised': False, 'authorises': []}
    write_once(root, MANIFEST, manifest)
    binding = {'schema': 'SCOUT_COMPARISON_RUNTIME_V003', 'manifest_sha256': digest(manifest),
        'model': manifest['model'], 'provider': PROVIDER, 'parameters': controls(),
        'bound_at': S.utc_now(), 'preflight_sha256': digest(preflight),
        'inspection': preflight['inspection'], 'hosted_transmission_authorised': False}
    for condition in V.CONDITIONS:
        Archive(root.path / condition).append('comparison_binding', binding, recorded_at=binding['bound_at'])
    write_once(root, BINDING, binding)
    return status(directory)


def load(directory):
    root = Archive(directory)
    manifest = input_json(root.path / 'exports' / MANIFEST)
    binding = input_json(root.path / 'exports' / BINDING)
    validate_binding(binding)
    if (manifest.get('schema') != 'SCOUT_COMPARISON_PACKAGE_V003'
            or manifest['protocol_sha256'] != digest(V.protocol('V003'))
            or binding['manifest_sha256'] != digest(manifest)
            or (manifest['model'], manifest['provider'], manifest['parameters']) !=
               (binding['model'], binding['provider'], binding['parameters'])):
        raise S.ScoutError('V003 manifest/protocol/runtime mismatch')
    if manifest.get('implementation_files_sha256') != {n: file_hash(Path(__file__).with_name(n)) for n in IMPLEMENTATION}:
        raise S.ScoutError('V003 implementation changed after freeze; no dispatch')
    expected = {c + '-blueprint.json' for c in V.CONDITIONS} | {
        request_name(c, 'ATT-' + str(i).zfill(4)) for c in V.CONDITIONS for i in (1, 2, 3)} | {
        'evaluation-protocol-v003.json', 'synthetic-preflight-v003.json'}
    if set(manifest['files_sha256']) != expected: raise S.ScoutError('unexpected V003 package file set')
    for name, sha in manifest['files_sha256'].items():
        if file_hash(root.path / 'exports' / name) != sha: raise S.ScoutError('frozen V003 file changed: ' + name)
    preflight = input_json(root.path / 'exports/synthetic-preflight-v003.json'); verify_preflight(preflight)
    if binding['preflight_sha256'] != digest(preflight) or binding['inspection'] != preflight['inspection']:
        raise S.ScoutError('preflight differs from immutable runtime binding')
    states, expected_requests = {}, []
    for condition in V.CONDITIONS:
        blueprint = input_json(root.path / 'exports' / (condition + '-blueprint.json'))
        state = Archive(root.path / condition).load()
        prefix = [{'type': e['type'], 'record': e['record'], 'recorded_at': e['recorded_at']}
                  for e in state.events[:len(blueprint['events'])]]
        if prefix != blueprint['events'] or state.comparison_binding != binding:
            raise S.ScoutError('ledger input prefix/binding differs from freeze')
        if any(e['type'] not in ('comparison_binding', 'v003_dispatch', 'attempt_result', 'card', 'generation_effort')
               for e in state.events[len(prefix):]):
            raise S.ScoutError('V003 inputs/cards may not be repaired, replaced or reallocated')
        if len(state.attempts) != 3 or len(state.prompts) != 3: raise S.ScoutError('V003 attempt allocation changed')
        for aid, attempt in state.attempts.items():
            prompt = state.prompts[attempt['prompt_id']]
            n = request_name(condition, aid); request = input_json(root.path / 'exports' / n)
            if (request['prompt'] != prompt or request['transmitted_text'] != canonical(prompt).decode()
                    or request['response_schema'] != prompt['response_schema'] or request['system_prompt'] != SYSTEM_PROMPT
                    or request['condition'] != condition or request['attempt_id'] != aid):
                raise S.ScoutError('transmission differs from frozen prompt')
            expected_requests.append({'condition': condition, 'attempt_id': aid, 'file': n,
                'payload_sha256': S.hash_text(request['transmitted_text']),
                'response_schema_sha256': digest(request['response_schema']), 'cards': 2})
        states[condition] = state
    if manifest['requests'] != expected_requests: raise S.ScoutError('request set/order differs from freeze')
    return root, manifest, binding, states


def consent_template(directory):
    root, manifest, binding, _ = load(directory)
    return {'schema': 'SCOUT_HOSTED_AUTHORISATION_V003', 'owner_approved': False,
        'approving_owner': S.UNKNOWN, 'approved_at': S.UNKNOWN,
        'manifest_sha256': digest(manifest), 'binding_sha256': digest(binding),
        'protocol_version': 'SCOUT_EVALUATION_PROTOCOL_V003', 'protocol_sha256': manifest['protocol_sha256'],
        'provider': PROVIDER, 'model': binding['model'], 'effort': 'medium',
        'files_sha256': manifest['files_sha256'], 'source_files_sha256': manifest['source_files_sha256'],
        'implementation_files_sha256': manifest['implementation_files_sha256'],
        'requests': manifest['requests'], 'privacy_and_limitations': PRIVACY,
        'accept_canonical_model_id_limit': False,
        'transmission_scope': 'Only each request transmitted_text, its response_schema and system_prompt; no repository, previous responses, catalogue refresh or source fetching.',
        'owner_statement': 'I authorise these exact 12 frozen V003 requests to Anthropic using my research Claude subscription, acknowledge the stated data-handling and canonical-model limitations, and approve execution once without retries or replacements.'}


def validate_consent(directory, value):
    template = consent_template(directory)
    if not isinstance(value, dict) or set(value) != set(template): raise S.ScoutError('owner authorisation record has unexpected/missing fields')
    mutable = {'owner_approved', 'approving_owner', 'approved_at', 'accept_canonical_model_id_limit'}
    if any(value[k] != v for k, v in template.items() if k not in mutable):
        raise S.ScoutError('owner authorisation does not cover these exact files/model/requests/privacy limits')
    if value['owner_approved'] is not True or value['accept_canonical_model_id_limit'] is not True:
        raise S.ScoutError('explicit owner hosted-data consent and model-pinning decision remain outstanding')
    S.validate(S.LABEL, value['approving_owner'])
    if value['approving_owner'].strip() in ('', S.UNKNOWN): raise S.ScoutError('actual approving owner identity required')
    approved = S.timestamp(value['approved_at'])
    _, _, binding, _ = load(directory)
    if not S.timestamp(binding['bound_at']) <= approved <= S.timestamp(S.utc_now()):
        raise S.ScoutError('owner approval must follow freeze and cannot be future-dated')
    return value


def authorise(directory, owner_file):
    value = validate_consent(directory, input_json(owner_file))
    root = Archive(directory)
    path = write_once(root, 'owner-authorisation-v003.json', value)
    return {'authorisation': str(path), 'sha256': digest(value), 'generation_status': 'NOT_RUN'}


def execute(directory, executable=None, config=None):
    # Validate everything before inspecting auth, constructing the client or invoking a model.
    root, manifest, binding, states = load(directory)
    approval = validate_consent(directory, input_json(root.path / 'exports/owner-authorisation-v003.json'))
    if any(s.v003_dispatches or any('result' in a for a in s.attempts.values()) for s in states.values()):
        raise S.ScoutError('V003 execution already started; no redispatch, continuation, retry or replacement')
    options = {} if config is None else {'config': config}
    client = ClaudeSubscription(executable, **options)
    inspection = client.inspect()
    if inspection != binding['inspection']: raise S.ScoutError('CLI binary/version/auth/config/controls differ from preflight; no dispatch')
    # Whole-run exclusive lock plus a durable per-attempt marker before subprocess.
    # A crash consumes the marker's slot and blocks automatic resumption.
    with root.locked():
        _, _, _, current = load(directory)
        if any(s.v003_dispatches for s in current.values()): raise S.ScoutError('comparison already dispatched')
        for row in manifest['requests']:
            archive = Archive(root.path / row['condition'])
            state = archive.load()
            spent = sum(e['wall_seconds'] for e in state.efforts if e.get('kind') == 'GENERATION_ATTEMPT'
                        and e['wall_seconds'] != S.UNKNOWN)
            remaining = V.protocol('V003')['budget_per_condition']['generation_wall_seconds'] - spent
            if remaining <= 0: break
            payload = input_json(root.path / 'exports' / row['file'])
            context_id = str(uuid.uuid4()); moment = S.utc_now()
            archive.append('v003_dispatch', {'attempt_id': row['attempt_id'], 'context_id': context_id,
                'request_sha256': row['payload_sha256'], 'authorisation_sha256': digest(approval),
                'started_at': moment}, recorded_at=moment)
            permit = {'purpose': 'OWNER_AUTHORISED_V003', 'payload_sha256': row['payload_sha256'],
                      'schema_sha256': row['response_schema_sha256'], 'model': binding['model']}
            result = client.invoke(payload['transmitted_text'], payload['response_schema'], binding['model'],
                                   permit=permit, timeout=min(600, remaining), context_id=context_id)
            name = row['condition'] + '-' + row['attempt_id'] + '-invocation-v003.json'
            receipt = write_once(root, name, result)
            provenance = {'model': result['actual_model'], 'provider': PROVIDER,
                'invoked_at': result['invoked_at'], 'completed_at': result['completed_at'],
                'parameters': binding['parameters'], 'seed': S.UNKNOWN, 'usage': result['usage'],
                'context_declaration': 'New CLI process, UUID, sterile temporary directory; no prior cards. See immutable invocation receipt.',
                'operator': 'V003_CLAUDE_CLI'}
            failure = result['error']
            usage = result['usage']; caps = V.protocol('V003')['budget_per_condition']
            if usage['input_tokens'] != S.UNKNOWN and usage['input_tokens'] > caps['max_input_tokens_per_attempt']:
                failure = failure or 'INPUT_TOKEN_CAP_EXCEEDED_NO_RETRY'
            W.finish(archive, row['attempt_id'], result['output'], provenance,
                     raw_import=canonical({'receipt': receipt.name, 'sha256': file_hash(receipt)}).decode(), error=failure)
            archive.append('generation_effort', {'attempt_id': row['attempt_id'],
                'actor': {'kind': 'SYNTHETIC_FIXTURE' if state.batch['fixture'] == 'SYNTHETIC' else 'ASSISTANT', 'id': 'V003_CLAUDE_CLI'},
                'human_minutes': S.UNKNOWN, 'wall_seconds': result['wall_seconds'],
                'invocation_status': 'NOT_INVOKED' if result['cli_invocations_started'] == 0 else
                    ('UNKNOWN' if result['error'] in ('TIMEOUT_NO_RETRY', 'INVALID_CLI_ENVELOPE_NO_RETRY') else 'INVOKED'),
                'context_id': context_id, 'fresh_context': 'YES' if result['isolation_verified'] else S.UNKNOWN,
                'no_prior_generated_cards': 'YES',
                'description': 'Measured CLI wall time; setup/monitoring human time remains UNKNOWN. No retries; provider request count UNKNOWN.'})
            # Any failed/invalid attempt stops dispatch for owner inspection; slots stay consumed.
            if failure or archive.load().attempts[row['attempt_id']]['result']['status'] != 'VALID': break
    return status(directory)


def status(directory):
    root, manifest, binding, states = load(directory)
    audit = fairness(states, V.protocol('V003')['budget_per_condition'])
    dispatches = sum(len(s.v003_dispatches) for s in states.values())
    results = sum('result' in a for s in states.values() for a in s.attempts.values())
    receipts, missing_receipts = [], []
    auth_path = root.path / 'exports/owner-authorisation-v003.json'
    approval = validate_consent(directory, input_json(auth_path)) if auth_path.exists() else None
    for row in manifest['requests']:
        state = states[row['condition']]
        if row['attempt_id'] not in state.v003_dispatches: continue
        dispatch = state.v003_dispatches[row['attempt_id']]
        if (approval is None or dispatch['authorisation_sha256'] != digest(approval)
                or dispatch['request_sha256'] != row['payload_sha256']):
            raise S.ScoutError('dispatch no longer matches frozen request/owner authorisation')
        path = root.path / 'exports' / (row['condition'] + '-' + row['attempt_id'] + '-invocation-v003.json')
        if not path.exists(): missing_receipts.append(row['condition'] + '/' + row['attempt_id']); continue
        receipt = input_json(path)
        if receipt.get('context_id') != dispatch['context_id']: raise S.ScoutError('receipt context differs from dispatch')
        attempt = state.attempts[row['attempt_id']]
        if 'result' in attempt:
            reference = S.json_loads(attempt['result']['raw_import'])
            if reference != {'receipt': path.name, 'sha256': file_hash(path)}: raise S.ScoutError('invocation receipt changed')
        receipts.append({k: receipt[k] for k in ('context_id', 'actual_model', 'error', 'wall_seconds', 'usage',
            'thinking_tokens', 'cli_invocations_started', 'visible_generation_attempts', 'underlying_provider_requests')})
    approved = approval is not None
    if missing_receipts or dispatches != results:
        audit['incomplete_records'].append('Interrupted dispatch: consumed slots have missing receipts/results; never redispatch')
        audit['comparative_eligible'] = False
    return {'schema': 'SCOUT_COMPARISON_STATUS_V003', 'manifest_sha256': digest(manifest),
        'binding': binding, 'generation_status': 'NOT_RUN' if dispatches == results == 0 else 'RECORDED',
        'reserved_visible_attempts': 12, 'durable_dispatches': dispatches, 'recorded_results': results,
        'invocations': receipts, 'missing_receipts': missing_receipts,
        'hosted_owner_authorisation_valid': approved, 'fairness': audit,
        'human_review': 'NOT_PROVIDED', 'scientific_source_requests': 0, 'authorises': []}


def blind(directory, salt):
    root, manifest, binding, states = load(directory)
    audit = status(directory)['fairness']
    if not isinstance(salt, str) or len(salt) < 20: raise S.ScoutError('private salt needs at least 20 characters')
    public, assignments = [], {}
    for row in manifest['requests']:
        state = states[row['condition']]; attempt = state.attempts[row['attempt_id']]
        # A stopped run still exposes every original card and all missing reserved
        # slots. No invented terminal result is appended for an untouched attempt.
        result = attempt.get('result', {'raw_response': '', 'status': 'PENDING'})
        prompt = state.prompts[attempt['prompt_id']]
        try: original_ideas = S.json_loads(result['raw_response']).get('ideas', [])
        except (S.ScoutError, AttributeError): original_ideas = []
        # Surplus returned cards are invalid but still reviewed, never shortlisted
        # or silently dropped to manufacture the expected 24-card denominator.
        for index in range(max(2, len(original_ideas) if isinstance(original_ideas, list) else 0)):
            bid = 'BLIND-' + hmac.new(salt.encode(), canonical([row['condition'], row['attempt_id'], index]), hashlib.sha256).hexdigest()[:16]
            idea = original_ideas[index] if isinstance(original_ideas, list) and index < len(original_ideas) else None
            valid_shape = isinstance(idea, dict)
            content = {k: copy.deepcopy(v) for k, v in idea.items() if k in S.IDEA['properties'] and k not in ('seed_ids', 'historical_refs')} if valid_shape else None
            # Do not give the reviewer prompts, envelopes, model IDs, errors or logs.
            # A malformed body stays in the private archive; its missing slots stay visible.
            declared_seeds = idea.get('seed_ids', []) if valid_shape else []
            declared_seeds = declared_seeds if isinstance(declared_seeds, list) else []
            public.append({'blind_id': bid, 'idea': content,
                'source_passages': [{'text': seed['text'], 'depth': seed['depth'], 'limitations': seed['limitations']}
                                    for sid, seed in prompt['context']['seeds'].items()
                                    if sid in declared_seeds],
                'format_valid': result['status'] == 'VALID',
                'missing_card': not valid_shape})
            assignments[bid] = {'condition': row['condition'], 'attempt_id': row['attempt_id'],
                                'response_index': index, 'original_result_sha256': digest(result)}
    public.sort(key=lambda r: r['blind_id'])
    sealed = {'assignments': assignments, 'salt_sha256': S.hash_text(salt), 'public_cards_sha256': digest(public),
              'accounting': audit, 'binding': binding}
    packet = {'schema': 'SCOUT_BLINDED_REVIEW_V003', 'protocol_version': 'V003',
        'protocol_sha256': digest(V.protocol('V003')), 'comparative_eligible': audit['comparative_eligible'],
        'cards': public, 'key_sha256': digest(sealed), 'fixture': states['PLAIN'].batch['fixture'],
        'blinding': 'PARTIAL_PROCEDURAL', 'reviewer_labels': [], 'missing_reviewer_judgments': len(public)}
    key_path = write_once(root, 'blinding-key-private-v003.json', sealed)
    packet_path = write_once(root, 'blinded-review-v003.json', packet)
    return {'packet': str(packet_path), 'private_key': str(key_path),
            'reviewer_receives': 'ONLY blinded-review-v003.json; no generation logs, key, condition or model metadata'}


def evaluate(directory, judgment_file):
    root, _, _, _ = load(directory)
    packet = input_json(root.path / 'exports/blinded-review-v003.json')
    sealed = input_json(root.path / 'exports/blinding-key-private-v003.json')
    judgments = input_json(judgment_file)
    result = V.evaluate_blind(packet, sealed, judgments)
    result['schema'] = 'SCOUT_DESCRIPTIVE_COMPARISON_V003'
    result['dimensions'] = {c: {d: dict(Counter(r[d] for r in result['judgments'] if r['condition'] == c))
        for d in ('coherent', 'falsifiable', 'research_worthy', 'evidence_integrity')} for c in V.CONDITIONS}
    result.update(substantive_mechanism_diversity='NOT_CHECKED_REQUIRES_SEPARATE_HUMAN_COMPARISON',
                  external_novelty='NOT_CHECKED', investment_edge='NOT_ESTABLISHED',
                  discovery_lab_M_H='NOT_ASSESSED', jev='NOT_RUN', composite_score=None)
    name = 'human-comparison-' + digest(judgments)[:16] + '-v003.json'
    write_once(root, name, {'original_judgments': judgments, 'original_file_sha256': file_hash(judgment_file), 'report': result})
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    for name in ('inspect', 'synthetic-preflight'):
        x = commands.add_parser(name); x.add_argument('--executable'); x.add_argument('--config')
        if name == 'synthetic-preflight': x.add_argument('--store', required=True)
    x = commands.add_parser('prepare'); x.add_argument('store'); x.add_argument('--preflight', required=True)
    x.add_argument('--package', default=str(DEFAULT_PACKAGE))
    for name in ('status', 'consent-template', 'authorise', 'execute', 'blind', 'evaluate'):
        x = commands.add_parser(name); x.add_argument('store')
        if name == 'authorise': x.add_argument('--owner-record', required=True)
        if name == 'execute': x.add_argument('--executable'); x.add_argument('--config')
        if name == 'blind': x.add_argument('--salt-file', required=True)
        if name == 'evaluate': x.add_argument('--judgments', required=True)
    a = p.parse_args(argv)
    try:
        if a.command in ('inspect', 'synthetic-preflight'):
            kwargs = {} if a.config is None else {'config': a.config}
            client = ClaudeSubscription(a.executable, **kwargs)
            if a.command == 'inspect': result = client.inspect()
            else:
                root = Archive(a.store)
                if root.path.exists() and any(root.path.iterdir()): raise S.ScoutError('synthetic preflight needs a new empty directory')
                result = synthetic_preflight(client)
                write_once(root, 'synthetic-preflight-v003.json', result)
                from .cli import emit
                emit(result)
                return 0 if result['passed'] else 2
        elif a.command == 'prepare': result = prepare(a.store, a.preflight, a.package)
        elif a.command == 'status': result = status(a.store)
        elif a.command == 'consent-template':
            root = Archive(a.store)
            value = consent_template(a.store)
            result = {'template': str(write_once(root, 'UNAPPROVED-owner-template-v003.json', value)), 'owner_approved': False}
        elif a.command == 'authorise': result = authorise(a.store, a.owner_record)
        elif a.command == 'execute': result = execute(a.store, a.executable, a.config)
        elif a.command == 'blind': result = blind(a.store, input_json(a.salt_file)['salt'])
        else: result = evaluate(a.store, a.judgments)
        from .cli import emit
        emit(result); return 0
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print('Opportunity Scout V003: ' + str(error), file=sys.stderr); return 2


if __name__ == '__main__': sys.exit(main())
