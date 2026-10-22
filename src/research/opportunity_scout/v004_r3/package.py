"""Freeze newly versioned R3 packages without changing or importing old runs."""
from pathlib import Path
from src.research.spec import canonical, digest
from .. import schema as S, v004_package as legacy, v004_runtime as old_runtime
from . import runtime, policy

VERSION = 'SCOUT_V004_OFFLINE_PACKAGE_R3'
REQUEST_VERSION = 'SCOUT_V004_RAW_JSON_REQUEST_R3'
CONDITIONS, ALLOCATION, order = legacy.CONDITIONS, legacy.ALLOCATION, legacy.order
destination, write_bytes, read_bytes, byte_hash = legacy.destination, legacy.write_bytes, legacy.read_bytes, legacy.byte_hash
ROOT = legacy.ROOT
AMENDMENT = ROOT / 'docs/opportunity_scout/v004_resource_governance_r3_proposed.json'


def implementation():
    hashes = legacy.implementation()
    for p in sorted(Path(__file__).parent.glob('*.py')) + [AMENDMENT]:
        hashes[p.relative_to(ROOT).as_posix()] = byte_hash(read_bytes(p))
    return hashes


def assemble(blueprints, settings, mode):
    runtime.validate(settings)
    # Reuse the frozen scientific projection/validation recipe, not an R2
    # receipt or run. Replace the runtime before writing ANY new package bytes.
    old_settings = old_runtime.description(settings['model'], settings['binary_sha256'], settings['cli_version'])
    _, files, requests = legacy.assemble(blueprints, old_settings, mode)
    for slot, request in requests.items():
        request.update(schema=REQUEST_VERSION, resource_policy_sha256=policy.policy_hash(),
                       runtime_sha256=digest(settings))
        files[f'requests/{slot}.json'] = canonical(request) + b'\n'
    protocol = {'schema': 'SCOUT_V004_RESOLVED_OFFLINE_PROTOCOL_R3', 'conditions': list(CONDITIONS),
                'allocation': ALLOCATION, 'order': order(), 'intended_attempts': 12, 'intended_cards': 24,
                'full_card_schema_sha256': byte_hash(files['schema.json']),
                'scientific_projection_sha256': byte_hash(files['projection.json']),
                'resource_policy': policy.description(), 'ordinary_format_failure': 'CONSUMED_NO_REPAIR_ADVANCE_ONCE',
                'generation_rule': 'ONE_PARENT_MAX_TWO_VISIBLE_ONLY_EVIDENCED_APPEND_ONLY_CONTINUATION',
                'independent_human_review_required': True, 'hosted_authorised': False, 'authorises': []}
    files['runtime.json'] = canonical(settings) + b'\n'
    files['resource-policy.json'] = canonical(policy.description()) + b'\n'
    files['resource-amendment.json'] = canonical(S.json_loads(read_bytes(AMENDMENT).decode('utf-8'))) + b'\n'
    files['protocol.json'] = canonical(protocol) + b'\n'
    manifest = {'schema': VERSION, 'mode': mode, 'files': {k: byte_hash(v) for k,v in files.items()},
                'implementation': implementation(), 'dependencies': legacy.dependencies(),
                'order': order(), 'runtime': settings, 'resource_policy_sha256': policy.policy_hash(),
                'protocol_sha256': byte_hash(files['protocol.json']), 'generation_status': 'NOT_RUN',
                'hosted_authorised': False, 'source_acquisition_authorised': False, 'authorises': []}
    return manifest, files, requests


def build(directory, blueprints, settings, *, mode='PROSPECTIVE_LOCAL_ONLY'):
    manifest, files, _ = assemble(blueprints, settings, mode)
    root = destination(directory); root.mkdir(parents=True, exist_ok=False)
    for name,data in files.items():
        target=root/name; target.parent.mkdir(exist_ok=True); write_bytes(target,data)
    write_bytes(root/'manifest.json',canonical(manifest)+b'\n')
    return manifest


def load(directory):
    from ..storage import unlinked
    root=unlinked(directory)
    manifest=S.json_loads(read_bytes(root/'manifest.json').decode('utf-8'))
    if manifest.get('schema') != VERSION: raise S.ScoutError('R3 package required; old packages are never migrated')
    blueprints={c:S.json_loads(read_bytes(root/f'inputs/{c}.json').decode('utf-8')) for c in CONDITIONS}
    expected,files,requests=assemble(blueprints,manifest['runtime'],manifest['mode'])
    names={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if manifest != expected or names != set(files)|{'manifest.json'}:
        raise S.ScoutError('R3 policy/package/implementation/dependencies or file set changed')
    for name,data in files.items():
        if read_bytes(root/name) != data: raise S.ScoutError('R3 frozen package bytes changed')
    return manifest,requests
