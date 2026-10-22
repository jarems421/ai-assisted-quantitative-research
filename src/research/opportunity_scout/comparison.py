"""Frozen, offline four-condition packages. No model installation or source fetching."""
from pathlib import Path
import time
import uuid

from src.research.spec import canonical, digest
from . import schema as S, workflow as W
from .evaluation import CONDITIONS, protocol, blind
from .accounting import fairness
from .storage import Archive, input_json

MANIFEST = 'comparison-manifest.json'
RUNTIME = 'comparison-runtime.json'


def freeze(directory, seed_file, *, moment=None):
    root = Archive(directory)
    if root.path.exists() and any(root.path.iterdir()): raise S.ScoutError('choose an empty comparison directory')
    seeds = input_json(seed_file)
    S.validate(S.obj({'seeds': S.array(S.SEED, 20, 1)}), seeds)
    moment = moment or S.utc_now()
    files = {}
    for condition in CONDITIONS:
        archive = Archive(root.path / condition)
        W.initialise(archive, 'First prospective V002 comparison / ' + condition, max_cards=6,
                     max_attempts=3, cutoff=moment, moment=moment)
        archive.append_many([('seed', s) for s in seeds['seeds']], recorded_at=moment)
        for lane in protocol('V002')['allocation'][condition]:
            W.prepare(archive, lane, 2, 'MODEL_BOUND_BEFORE_GENERATION', moment=moment)
        state = archive.load()
        blueprint = {'events': [{'type': e['type'], 'record': e['record'], 'recorded_at': e['recorded_at']} for e in state.events]}
        name = condition + '-blueprint.json'
        root.export(name, blueprint); files[name] = digest(blueprint)
    manifest = {'schema': 'SCOUT_COMPARISON_PACKAGE_V002', 'protocol_sha256': digest(protocol('V002')),
        'created_at': moment, 'files': files, 'generation_status': 'NOT_RUN',
        'model_binding': 'REQUIRED_BEFORE_FIRST_INVOCATION',
        'archived_generated_cards_included': False, 'hosted_transmission_authorised': False,
        'scientific_source_requests': 0, 'human_judgments': 'NOT_PROVIDED', 'authorises': []}
    root.export(MANIFEST, manifest)
    return {'package': str(root.path / 'exports'), 'manifest_sha256': digest(manifest), 'generation_status': 'NOT_RUN'}


def install(directory, package):
    root = Archive(directory)
    if root.path.exists() and any(root.path.iterdir()): raise S.ScoutError('install into an empty comparison directory')
    source = Path(package)
    manifest = input_json(source / MANIFEST)
    if manifest['schema'] != 'SCOUT_COMPARISON_PACKAGE_V002' or manifest['protocol_sha256'] != digest(protocol('V002')):
        raise S.ScoutError('comparison package/protocol mismatch')
    if set(manifest['files']) != {c + '-blueprint.json' for c in CONDITIONS}: raise S.ScoutError('unexpected package files')
    # Read and verify all blueprints before writing any archive.
    blueprints = {name: input_json(source / name) for name in manifest['files']}
    for name, data in blueprints.items():
        if digest(data) != manifest['files'][name]: raise S.ScoutError('frozen blueprint changed')
        if any(e['type'] not in ('batch', 'seed', 'prompt', 'attempt_start') for e in data['events']):
            raise S.ScoutError('generation outputs are forbidden in a new comparison package')
    for name, data in blueprints.items():
        archive = Archive(root.path / name.removesuffix('-blueprint.json'))
        for event in data['events']: archive.append(event['type'], event['record'], recorded_at=event['recorded_at'])
        root.export(name, data)
    root.export(MANIFEST, manifest)
    load(directory)
    return {'manifest_sha256': digest(manifest), 'generation_status': 'NOT_RUN', 'store': str(root.path)}


def load(directory):
    root = Archive(directory)
    manifest = input_json(root.path / 'exports' / MANIFEST)
    if manifest['protocol_sha256'] != digest(protocol('V002')): raise S.ScoutError('prospective protocol changed')
    states = {}
    for condition in CONDITIONS:
        name = condition + '-blueprint.json'
        blueprint = input_json(root.path / 'exports' / name)
        if digest(blueprint) != manifest['files'][name]: raise S.ScoutError('blueprint hash mismatch')
        state = Archive(root.path / condition).load()
        prefix = [{'type': e['type'], 'record': e['record'], 'recorded_at': e['recorded_at']}
                  for e in state.events[:len(blueprint['events'])]]
        if prefix != blueprint['events'] or len(state.attempts) != 3 or len(state.prompts) != 3:
            raise S.ScoutError('archive differs from frozen prompts/attempt plan')
        if any(e['type'] in ('seed', 'batch', 'prompt', 'attempt_start') for e in state.events[len(prefix):]):
            raise S.ScoutError('comparison inputs/attempts changed after freeze')
        states[condition] = state
    return root, manifest, states


def bind(directory, model, parameters, provider='OPERATOR_ASSISTED'):
    root, manifest, states = load(directory)
    if not model.strip() or model in (S.UNKNOWN, 'MODEL_BOUND_BEFORE_GENERATION'):
        raise S.ScoutError('pin an actual model identity before generation')
    if provider not in ('OPERATOR_ASSISTED', 'OLLAMA_LOCAL'): raise S.ScoutError('only approved operator/local generation is supported')
    if any('result' in a for s in states.values() for a in s.attempts.values()):
        raise S.ScoutError('runtime must be frozen before any imported generation')
    if any(s.comparison_binding for s in states.values()) or (root.path / 'exports' / RUNTIME).exists():
        raise S.ScoutError('runtime is already bound; it cannot be silently replaced')
    S.validate({'type': 'object', 'maxProperties': 15}, parameters)
    # Reuse the provenance credential-key guard without inspecting any credentials.
    from .engine import provider_check
    p = {'model': model, 'provider': provider, 'invoked_at': S.UNKNOWN, 'completed_at': S.UNKNOWN,
         'parameters': parameters, 'seed': parameters.get('seed', S.UNKNOWN),
         'usage': {'input_tokens': S.UNKNOWN, 'output_tokens': S.UNKNOWN, 'cost': S.UNKNOWN, 'currency': S.UNKNOWN},
         'context_declaration': 'One independent fresh context per frozen request.', 'operator': 'COMPARISON_OPERATOR'}
    provider_check(p, states['PLAIN'])
    runtime = {'schema': 'SCOUT_COMPARISON_RUNTIME_V002', 'manifest_sha256': digest(manifest),
        'model': model, 'provider': provider, 'parameters': parameters, 'bound_at': S.utc_now(),
        'hosted_transmission_authorised': False}
    for condition in CONDITIONS:
        Archive(root.path / condition).append('comparison_binding', runtime, recorded_at=runtime['bound_at'])
    root.export(RUNTIME, runtime)
    return runtime


def status(directory):
    root, manifest, states = load(directory)
    audit = fairness(states, protocol('V002')['budget_per_condition'])
    path = root.path / 'exports' / RUNTIME
    runtime = input_json(path) if path.exists() else None
    if not runtime:
        audit['incomplete_records'].append('model/provider/settings not bound before generation')
    else:
        if runtime['manifest_sha256'] != digest(manifest): raise S.ScoutError('runtime/package mismatch')
        for condition, state in states.items():
            if state.comparison_binding != runtime: raise S.ScoutError('runtime differs from the immutable pre-generation binding')
            for attempt in state.attempts.values():
                if 'result' not in attempt: continue
                provenance = attempt['result']['provider']
                if any(provenance[k] != runtime[k] for k in ('model', 'provider', 'parameters')):
                    audit['deviations'].append(condition + '/' + attempt['id'] + ': differs from bound runtime')
                result_event = next(e for e in state.events if e['type'] == 'attempt_result' and e['record']['attempt_id'] == attempt['id'])
                if S.timestamp(runtime['bound_at']) > S.timestamp(result_event['recorded_at']) or (provenance['invoked_at'] != S.UNKNOWN and S.timestamp(runtime['bound_at']) > S.timestamp(provenance['invoked_at'])):
                    audit['deviations'].append(condition + '/' + attempt['id'] + ': runtime bound after invocation/result')
    audit['comparative_eligible'] = not audit['deviations'] and not audit['incomplete_records']
    return {'schema': 'SCOUT_COMPARISON_STATUS_V002', 'manifest_sha256': digest(manifest), 'runtime': runtime,
        'generation_status': 'NOT_RUN' if not any('result' in a for s in states.values() for a in s.attempts.values()) and not any(s.efforts for s in states.values()) else 'RECORDED',
            'fairness': audit, 'human_review': 'NOT_PROVIDED', 'scientific_source_requests': 0}


def requests(directory):
    root, manifest, states = load(directory)
    result = []
    for condition, state in states.items():
        archive = Archive(root.path / condition)
        for aid, attempt in state.attempts.items():
            name = aid + '-evaluation-request.json'
            payload = {'attempt_id': aid, 'prompt': state.prompts[attempt['prompt_id']],
                'provenance_schema': S.PROVIDER,
                'instructions': 'Use ONLY this prompt in a new context. No previous cards or other requests. Return exactly two cards once. No repairs/retries. Import through import-response, then record generation-effort. Bind the SAME actual model/provider/settings before any invocation. UNKNOWN usage stays UNKNOWN. No hosted transmission is authorised.'}
            path = archive.path / 'exports' / name
            if not path.exists(): archive.export(name, payload)
            elif input_json(path) != payload: raise S.ScoutError('request export differs from freeze')
            result.append({'condition': condition, 'attempt_id': aid, 'path': str(path)})
    return {'requests': result, 'manifest_sha256': digest(manifest), 'generation_status': status(directory)['generation_status']}


def run_local(directory, model):
    from .providers import OllamaProvider, UNKNOWN_USAGE
    root, _, states = load(directory)
    path = root.path / 'exports' / RUNTIME
    params = {'seed': 0, 'temperature': 0.8, 'num_predict': 6000}
    if not path.exists(): bind(directory, model, params, 'OLLAMA_LOCAL')
    runtime = input_json(path)
    if (runtime['model'], runtime['provider'], runtime['parameters']) != (model, 'OLLAMA_LOCAL', params):
        raise S.ScoutError('local model/settings differ from the frozen runtime')
    if any('result' in a for s in states.values() for a in s.attempts.values()):
        raise S.ScoutError('no automatic continuation or re-dispatch after a recorded comparison attempt')
    for condition, state in states.items():
        archive = Archive(root.path / condition)
        for aid, attempt in state.attempts.items():
            started = time.monotonic()
            error = None; raw = original = ''
            try: raw, provenance, original = OllamaProvider(model).generate(state.prompts[attempt['prompt_id']], 0)
            except Exception as problem:
                error = type(problem).__name__ + ': local request failed; no retry'
                provenance = {'model': model, 'provider': 'OLLAMA_LOCAL', 'invoked_at': S.UNKNOWN,
                    'completed_at': S.UNKNOWN, 'parameters': params, 'seed': 0, 'usage': dict(UNKNOWN_USAGE),
                    'context_declaration': 'Failed independent stateless request.', 'operator': 'LOCAL_CLI'}
            W.finish(archive, aid, raw, provenance, raw_import=original, error=error)
            archive.append('generation_effort', {'attempt_id': aid, 'actor': {'kind': 'ASSISTANT', 'id': 'LOCAL_CLI'},
                'human_minutes': S.UNKNOWN, 'wall_seconds': round(time.monotonic() - started, 6),
                'invocation_status': 'UNKNOWN' if error else 'INVOKED',
                'context_id': str(uuid.uuid4()), 'fresh_context': 'YES', 'no_prior_generated_cards': 'YES',
                'description': 'Stateless local request; operator must record setup/monitoring effort separately. Human time UNKNOWN.'})
    return status(directory)


def blind_package(directory, salt):
    root, manifest, states = load(directory)
    audit = status(directory)
    packet, key = blind(states, salt, version='V002', binding={'manifest_sha256': digest(manifest),
                        'runtime_sha256': digest(audit['runtime']) if audit['runtime'] else S.UNKNOWN})
    key['accounting'] = audit['fairness']
    packet['comparative_eligible'] = audit['fairness']['comparative_eligible']
    packet['key_sha256'] = digest(key)
    return {'packet': str(root.export('blinded-review.json', packet)),
            'private_key': str(root.export('blinding-key-private.json', key)),
            'comparative_eligible': packet['comparative_eligible'], 'blinding': 'PARTIAL_PROCEDURAL'}
