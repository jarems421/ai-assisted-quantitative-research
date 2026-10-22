"""Prospective raw-JSON package freeze/verification, without any dispatch path."""
from collections import Counter
import copy
import hashlib
import importlib.metadata
import platform
from pathlib import Path

from src.research.spec import canonical, digest
from . import engine as E, schema as S
from .storage import ROOT, unlinked
from .v004_runtime import description, SYSTEM_PROMPT

VERSION = 'SCOUT_V004_OFFLINE_PACKAGE_R1'
CONDITIONS = ('PLAIN', 'EVIDENCE_ONLY', 'MECHANISM_ONLY', 'HYBRID')
ALLOCATION = {'PLAIN': ['PLAIN'] * 3, 'EVIDENCE_ONLY': ['RADAR'] * 3,
              'MECHANISM_ONLY': ['FORGE'] * 3, 'HYBRID': ['FORGE', 'RADAR', 'GAP']}
# Frozen without experimental results. Three blocks, one of each condition per
# block, within-condition attempt order retained. Position sums 20,19,19,20.
ORDER = (0, 1, 2, 3, 1, 3, 2, 0, 2, 3, 0, 1)
PROMPT_FIELDS = ('lane', 'count', 'knowledge_cutoff', 'instructions', 'response_schema', 'context')


def byte_hash(value):
    return hashlib.sha256(value).hexdigest()


def write_bytes(path, value):
    """Exclusive create; caller holds a journal lock where applicable."""
    import os
    path = unlinked(path)
    with path.open('xb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())


def destination(path):
    path = unlinked(path)
    if path.resolve().is_relative_to(ROOT):
        rel = path.resolve().relative_to(ROOT).parts
        if len(rel) < 3 or rel[:2] != ('.research', 'opportunity_scout') or not rel[2].startswith('v004-offline-'):
            raise S.ScoutError('repository writes require a new .research/opportunity_scout/v004-offline-* directory')
    # Never treat an account, old experiment, or another repository as an output.
    if any(p.name.startswith('.claude') for p in (path, *path.parents)):
        raise S.ScoutError('account directories cannot hold Scout outputs')
    nearest = next((p for p in (path, *path.parents) if (p / '.git').exists()), None)
    if nearest is not None and nearest.resolve() != ROOT:
        raise S.ScoutError('other repository/worktree writes are refused')
    return path


def read_bytes(path, maximum=32 * 1024 * 1024):
    path = unlinked(path)
    if not path.is_file() or path.stat().st_nlink != 1 or path.stat().st_size > maximum:
        raise S.ScoutError('unsafe, linked or oversized evidence')
    return path.read_bytes()


def order():
    seen = Counter()
    rows = []
    for index, c in enumerate(ORDER, 1):
        condition = CONDITIONS[c]; seen[condition] += 1
        rows.append({'position': index, 'block': (index - 1) // 4 + 1, 'condition': condition,
                     'attempt_id': f'ATT-{seen[condition]:04d}',
                     'slot': f'{condition}-ATT-{seen[condition]:04d}'})
    return rows


def implementation():
    # Conservative Scout closure, including old modules reused for input replay
    # and schema checks; hashing is read-only and does not modify old freezes.
    paths = sorted(Path(__file__).parent.glob('*.py')) + [ROOT / p for p in (
        'src/research/spec.py', 'src/research/discovery/records.py', 'src/research/discovery/__init__.py',
        'src/research/sec_pilot/parsing.py', 'src/research/sec_pilot/__init__.py',
        'docs/opportunity_scout/proposed_protocol_v004.json',
        'docs/opportunity_scout/v004_exploratory_amendment_proposed.json')]
    hashes = {p.relative_to(ROOT).as_posix(): byte_hash(unlinked(p).read_bytes()) for p in paths}
    for name in ('src/__init__.py', 'src/research/__init__.py'):
        path = unlinked(ROOT / name)
        hashes[name] = byte_hash(path.read_bytes()) if path.exists() else 'ABSENT_NAMESPACE_PACKAGE'
    return hashes


def dependencies():
    return {'python': platform.python_version(),
            **{name: importlib.metadata.version(name) for name in ('jsonschema', 'referencing', 'jsonschema-specifications')}}


def assemble(blueprints, runtime, mode):
    if mode not in ('SYNTHETIC', 'PROSPECTIVE_LOCAL_ONLY') or set(blueprints) != set(CONDITIONS):
        raise S.ScoutError('four exact conditions and explicit local-only mode required')
    if runtime != description(runtime['model'], runtime['binary_sha256'], runtime['cli_version']):
        raise S.ScoutError('runtime differs from the versioned candidate')
    requests, files, states = {}, {}, {}
    for condition in CONDITIONS:
        data = blueprints[condition]
        if set(data) != {'events'}: raise S.ScoutError('input blueprint must contain only original events')
        state = E.State()
        for event in data['events']:
            if set(event) != {'type', 'record', 'recorded_at'} or event['type'] not in ('batch', 'seed', 'prompt', 'attempt_start'):
                raise S.ScoutError('generated results/bindings/dispatches are forbidden inputs')
            E.apply(state, event['type'], event['record'], event['recorded_at'], replay=True)
        if len(state.attempts) != 3 or len(state.prompts) != 3 or state.batch is None:
            raise S.ScoutError('three pristine reserved attempts required per condition')
        if mode == 'SYNTHETIC' and (state.batch['fixture'] != 'SYNTHETIC'
                or any(s['fixture'] != 'SYNTHETIC' for s in state.seeds.values())):
            raise S.ScoutError('offline replay never accepts real research inputs')
        prompts = [state.prompts[a['prompt_id']] for a in state.attempts.values()]
        if [p['lane'] for p in prompts] != ALLOCATION[condition]: raise S.ScoutError('lane allocation changed')
        states[condition] = state
        files[f'inputs/{condition}.json'] = canonical(data) + b'\n'
        for i, prompt in enumerate(prompts, 1):
            if prompt['count'] != 2: raise S.ScoutError('full two-card response required')
            expected_schema = copy.deepcopy(S.GENERATION)
            expected_schema['properties']['ideas'].update(minItems=2, maxItems=2)
            if prompt['response_schema'] != expected_schema: raise S.ScoutError('full card schema changed')
            slot = f'{condition}-ATT-{i:04d}'
            # Explicitly remove only audit IDs/hashes and obsolete output-cap
            # metadata. Full instructions/context/cutoff/schema are unchanged.
            payload = {k: copy.deepcopy(prompt[k]) for k in PROMPT_FIELDS}
            request = {'schema': 'SCOUT_V004_RAW_JSON_REQUEST_R1', 'slot': slot,
                       'condition': condition, 'lane': prompt['lane'], 'model': runtime['model'],
                       'context': payload['context'], 'response_schema': payload['response_schema'],
                       'system_prompt': SYSTEM_PROMPT, 'transmitted_text': canonical(payload).decode('utf-8'),
                       'source_prompt_sha256': digest(prompt), 'source_prompt': prompt,
                       'projection': {'retained_exact': list(PROMPT_FIELDS),
                                      'removed_audit_or_obsolete': sorted(set(prompt) - set(PROMPT_FIELDS))},
                       'known_payload_bytes': len(canonical(payload)),
                       'known_prompt_tokens': S.UNKNOWN, 'cli_scaffolding_tokens': S.UNKNOWN,
                       'provider_scaffolding_tokens': S.UNKNOWN, 'complete_input_bound': S.UNKNOWN,
                       'hosted_authorised': False}
            requests[slot] = request
            files[f'requests/{slot}.json'] = canonical(request) + b'\n'
    if len({digest(s.seeds) for s in states.values()}) != 1 or len({digest(s.batch['memory']) for s in states.values()}) != 1:
        raise S.ScoutError('eligible input pools differ')
    if len({s.batch['knowledge_cutoff'] for s in states.values()}) != 1:
        raise S.ScoutError('knowledge cutoff differs')
    files['runtime.json'] = canonical(runtime) + b'\n'
    files['schema.json'] = canonical(expected_schema) + b'\n'
    files['order.json'] = canonical(order()) + b'\n'
    files['projection.json'] = canonical({'retained_exact': list(PROMPT_FIELDS),
        'no_scientific_input_reduction': True, 'schema_transport_occurrences': 1,
        'source_seeds_already_prefix_limited': 'Existing prompt prefixes retained; full eligible sources separately inventoried.',
        'token_bound_from_bytes': False}) + b'\n'
    manifest = {'schema': VERSION, 'mode': mode, 'files': {k: byte_hash(v) for k, v in files.items()},
                'implementation': implementation(), 'dependencies': dependencies(), 'order': order(),
                'runtime': runtime, 'generation_status': 'NOT_RUN', 'hosted_authorised': False,
                'source_acquisition_authorised': False, 'authorises': []}
    return manifest, files, requests


def build(directory, blueprints, runtime, *, mode='PROSPECTIVE_LOCAL_ONLY'):
    manifest, files, _ = assemble(blueprints, runtime, mode)
    root = destination(directory)
    root.mkdir(parents=True, exist_ok=False)  # No reset, overwrite, migration.
    for name, data in files.items():
        p = root / name; p.parent.mkdir(exist_ok=True); write_bytes(p, data)
    write_bytes(root / 'manifest.json', canonical(manifest) + b'\n')
    return manifest


def load(directory):
    root = unlinked(directory)
    def read(name):
        return read_bytes(root / name, 12 * 1024 * 1024)
    manifest = S.json_loads(read('manifest.json').decode('utf-8'))
    if manifest.get('schema') != VERSION: raise S.ScoutError('not a V004 R1 package')
    blueprints = {c: S.json_loads(read(f'inputs/{c}.json').decode('utf-8')) for c in CONDITIONS}
    expected, files, requests = assemble(blueprints, manifest['runtime'], manifest['mode'])
    actual_names = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if manifest != expected or actual_names != set(files) | {'manifest.json'}:
        raise S.ScoutError('package, implementation, dependency, order or file set changed')
    for name, data in files.items():
        if read(name) != data: raise S.ScoutError('frozen package bytes changed')
    return manifest, requests
