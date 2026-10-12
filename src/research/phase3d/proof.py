"""Declarative manifests and exact input replay; never register or execute research."""
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator
from src.research.spec import canonical, digest
from src.research.phase3c.sources import put
from src.research.inference_feasibility import require_inference_design

ROOT = Path(__file__).resolve().parents[3]
ROLES = ('population', 'identity', 'availability', 'signal', 'execution', 'costs', 'inference', 'trial_family', 'source_contract')
GATES = ('accounting', 'identity', 'availability', 'terminal', 'universe', 'inference', 'execution')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contained(root, name):
    root = Path(root).resolve(); path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root or Path(name).is_absolute():
        raise ValueError('Reference escapes manifest root')
    return path


def environment():
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'platform': platform.platform(), 'packages': {p: importlib.metadata.version(p) for p in ('numpy', 'jsonschema')}}


def code_state():
    names = [*sorted((ROOT / 'src/research/phase3d').glob('*.py')),
             ROOT / 'src/research/spec.py', ROOT / 'src/research/capabilities.py',
             ROOT / 'src/research/inference_feasibility.py',
             ROOT / 'src/research/analysis.py', ROOT / 'src/research/phase3c/sources.py',
             ROOT / 'src/research/phase3c/quality.py', ROOT / 'src/research/phase3c/inference.py',
             ROOT / 'src/research/sec_pilot/acquisition.py', ROOT / 'src/research/sec_pilot/parsing.py',
             ROOT / 'src/research/sec_pilot/provenance.py',
             ROOT / 'docs/acceleration/phase3d_experiment.schema.json']
    return {p.relative_to(ROOT).as_posix(): file_hash(p) for p in names}


def compile_manifest(spec, root, output, *, authority):
    """Authority is separately supplied by the caller; this scope permits EXP999 only.

    Future real experiments still need the existing Store/stage/owner adapters.
    A manifest is provenance, not a security boundary against filesystem owners.
    """
    canonical(spec)
    schema = json.loads((ROOT / 'docs/acceleration/phase3d_experiment.schema.json').read_bytes())
    Draft202012Validator(schema).validate(spec)
    date.fromisoformat(spec['research_cutoff'])
    for snapshot in spec['source_snapshots']: date.fromisoformat(snapshot['source_end'])
    if spec['experiment_id'] != 'EXP999' or spec['mode'] != 'SYNTHETIC_INFRASTRUCTURE':
        raise ValueError('Real compilation not authorized or integrated in Phase 3D')
    if spec['research_stage'] != 'DRAFT' or authority.get('stage') != 'DRAFT':
        raise ValueError('Illegal stage advancement')
    if authority.get('scope') != 'SYNTHETIC_EXP999': raise ValueError('Independent scope evidence missing')
    if set(spec['contracts']) != set(ROLES) or set(spec['gates']) != set(GATES):
        raise ValueError('Mandatory contract/gate missing')
    references = [*spec['contracts'].values(), *spec['source_snapshots']]
    if not spec['source_snapshots']: raise ValueError('Source snapshots required')
    paths = [r['path'] for r in references]
    if len(paths) != len(set(paths)): raise ValueError('Duplicate contract/snapshot reference')
    for ref in references:
        path = contained(root, ref['path'])
        if not path.is_file() or file_hash(path) != ref['sha256']: raise ValueError('Missing or mutated reference')
    for gate, ref in spec['gates'].items():
        if ref['status'] != 'CERTIFIED' or authority.get('gate_hashes', {}).get(gate) != ref['receipt_sha256']:
            raise ValueError('Mandatory gate unresolved or certificate not trusted')
    contracts = {k: json.loads(contained(root, r['path']).read_bytes()) for k, r in spec['contracts'].items()}
    policy = contracts['availability']
    if (policy.get('status') != 'APPROVED_SYNTHETIC_FIXTURE' or policy.get('public_available_at_utc') is not None
            or policy.get('approval_sha256') != authority.get('approval_sha256') or not policy.get('approval_sha256')):
        raise ValueError('Unapproved policy or synthetic clock misrepresented')
    if contracts['inference'].get('status') != 'CERTIFIED_SYNTHETIC_FIXTURE':
        raise ValueError('Inference uncertified')
    require_inference_design(contracts['inference'].get('design_feasibility',{}))
    if contracts['execution'].get('unresolved_terminal_events') != []:
        raise ValueError('Unresolved mandatory terminal event')
    population = contracts['population'].get('security_ids', [])
    if not population or len(population) != len(set(population)) or set(population) != set(contracts['identity'].get('security_ids', [])):
        raise ValueError('Population/identity mismatch')
    source_contract = contracts['source_contract']
    if source_contract.get('snapshot_hashes') != [r['sha256'] for r in spec['source_snapshots']]:
        raise ValueError('Snapshot contract mismatch')
    if any(r['source_end'] > spec['research_cutoff'] for r in spec['source_snapshots']):
        raise ValueError('Future source beyond declared cutoff')
    trial = contracts['trial_family']
    if (not isinstance(trial.get('evaluation_ceiling'), int) or trial['evaluation_ceiling'] <= 0
            or trial.get('performance_authorized') is not False):
        raise ValueError('Trial ceiling or performance boundary invalid')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    payload = {'manifest_version': 'proof_manifest_v001', 'spec': spec,
               'authority_sha256': digest(authority), 'code_commit': revision,
               'code_hashes': code_state(), 'environment': environment(),
               'execution_receipt': None, 'statistical_receipt': None,
               'replay_level': 'EXACT_INPUT_BYTES_ONLY', 'performance_executed': False}
    manifest = dict(payload, manifest_sha256=digest(payload))
    path = Path(output) / (manifest['manifest_sha256'] + '.json')
    put(path, manifest)
    return manifest, path


def replay(manifest_path, root, *, authority, strict_environment=True):
    manifest = json.loads(Path(manifest_path).read_bytes())
    payload = {k:v for k,v in manifest.items() if k != 'manifest_sha256'}
    if digest(payload) != manifest.get('manifest_sha256'): raise ValueError('Manifest changed')
    if digest(authority) != manifest['authority_sha256']: raise ValueError('Authority changed')
    # Revalidate all gates and contracts as well as hashes; produces no output.
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        compile_manifest(manifest['spec'], root, temp, authority=authority)
    if manifest['code_hashes'] != code_state(): raise ValueError('Code compatibility changed')
    compatible = manifest['environment'] == environment()
    if strict_environment and not compatible: raise ValueError('Environment compatibility changed')
    return {'status': 'PASS_EXACT_INPUT_REPLAY', 'manifest_sha256': manifest['manifest_sha256'],
            'git_commit_exact':manifest['code_commit']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'relevant_code_hashes_exact':True,
            'environment_exact': compatible, 'output_bit_reproducibility_certified': False}
