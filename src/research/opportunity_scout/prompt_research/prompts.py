"""Explicit A/B research interface; V001 defaults, schema and ledgers untouched."""
import copy
from pathlib import Path

from src.research.spec import canonical, digest
from .. import engine as E, prompts as baseline, schema as S
from ..storage import ROOT
from ..v004_package import dependencies, PROMPT_FIELDS
from ..v004_r3 import package as frozen

A = 'SCOUT_PROMPTS_V002A_ABSTRACT_DIVERGENCE'
B = 'SCOUT_PROMPTS_V002B_STRUCTURED_RECOMBINATION'
VERSIONS = (baseline.VERSION, A, B)
HERE = Path(__file__).resolve().parent
RESOURCES = HERE / 'resources'
FILES = ('abstract_divergence.txt', 'structured_recombination.txt', 'common.txt', 'lanes.json')


def text(path):
    return path.read_bytes().replace(b'\r\n', b'\n').decode('utf-8')


def resource_manifest():
    value = S.json_loads(text(RESOURCES / 'manifest.json'))
    expected = {'schema': 'SCOUT_PROMPT_RESEARCH_RESOURCES_V002', 'versions': [A, B],
                'files': {name: S.hash_text(text(RESOURCES / name)) for name in FILES},
                'baseline_prompts_sha256_lf': S.hash_text(text(ROOT / 'src/research/opportunity_scout/prompts.py')),
                'unchanged_generation_schema_sha256': digest(S.GENERATION),
                'hosted_authorised': False, 'scientific_dispatch_authorised': False}
    if value != expected:
        raise S.ScoutError('versioned prompt resources/baseline/schema changed; no silent refresh')
    return value


def implementation():
    # A separate closure: never add V002 to the old scientific inventories.
    names = set(frozen.implementation()) | {p.relative_to(ROOT).as_posix() for p in HERE.rglob('*')
                                          if p.is_file() and p.suffix in ('.py', '.txt', '.json')}
    names.update(('docs/opportunity_scout/prompt_research_sources_v002.json',
                  'docs/opportunity_scout/prompt_evaluation_v001.json'))
    return {name: S.hash_text(text(ROOT / name)) if (ROOT / name).exists() else 'ABSENT_NAMESPACE_PACKAGE'
            for name in sorted(names)}


def instructions(version, lane, count):
    if version not in (A, B) or lane not in ('RADAR', 'FORGE', 'GAP'):
        raise S.ScoutError('V002 needs an explicit A/B variant and specialised lane; PLAIN stays frozen V001')
    lanes = S.json_loads(text(RESOURCES / 'lanes.json'))
    creative = 'abstract_divergence.txt' if version == A else 'structured_recombination.txt'
    # Evidence/memory grounding precedes the search objective for RADAR/GAP.
    return (f'Opportunity Scout {version}. Exactly {count} final JSON ideas.\n\n'
            + lanes[lane] + '\n\n' + text(RESOURCES / creative).strip() + '\n\n'
            + text(RESOURCES / 'common.txt').strip())


def make_prompt(state, lane, count, prompt_id, *, version):
    if version == baseline.VERSION:
        return baseline.make_prompt(state, lane, count, prompt_id)
    manifest = resource_manifest()
    if version not in (A, B) or lane == 'PLAIN':
        raise S.ScoutError('explicit prospective A/B only; PLAIN must select V001')
    # Reuse frozen lane access, prefix, clock/cutoff and count/schema logic.
    original = baseline.make_prompt(state, lane, count, prompt_id)
    core = {k: copy.deepcopy(v) for k, v in original.items() if k not in ('sha256', 'max_output_tokens')}
    core.update(prompt_version=version, instructions=instructions(version, lane, count),
                resource_manifest_sha256=digest(manifest), implementation=implementation(),
                construction_dependencies=dependencies(),
                baseline_projection_sha256=original['sha256'],
                eligible_seed_pool_sha256=digest(state.seeds), eligible_memory_pool_sha256=digest(state.batch['memory']),
                status='PROSPECTIVE_PROMPT_RESEARCH_NOT_AUTHORISED', hosted_authorised=False,
                scientific_dispatch_authorised=False,
                inherited_legacy_output_cap_removed=True)
    projected = {k: core[k] for k in PROMPT_FIELDS}
    core['transmitted_payload_sha256'] = digest(projected)
    core['known_payload_bytes'] = len(canonical(projected))
    # Runtime/resource authority is separate. Do not transmit the legacy batch
    # constructor's obsolete 6000 output cap or adopt a new runtime implicitly.
    if len(canonical(core)) > 240000:
        raise S.ScoutError('prospective prompt exceeds local IO bound; no silent trimming')
    return {**core, 'sha256': digest(core)}


def check_prompt(prompt):
    core = {k: v for k, v in prompt.items() if k != 'sha256'}
    if digest(core) != prompt.get('sha256') or prompt.get('prompt_version') not in (A, B):
        raise S.ScoutError('not an intact explicit prospective prompt')
    if (prompt.get('status') != 'PROSPECTIVE_PROMPT_RESEARCH_NOT_AUTHORISED' or
            prompt.get('hosted_authorised') is not False or prompt.get('scientific_dispatch_authorised') is not False or
            prompt.get('contains_generated_ideas') is not False or prompt.get('inherited_legacy_output_cap_removed') is not True):
        raise S.ScoutError('research envelope cannot grant execution authority or admit generated context')
    if prompt['instructions'] != instructions(prompt['prompt_version'], prompt['lane'], prompt['count']):
        raise S.ScoutError('instructions differ from versioned resource')
    if prompt['resource_manifest_sha256'] != digest(resource_manifest()) or prompt['implementation'] != implementation():
        raise S.ScoutError('resource/source provenance changed')
    if prompt['construction_dependencies'] != dependencies():
        raise S.ScoutError('prompt construction runtime changed')
    expected = copy.deepcopy(S.GENERATION)
    expected['properties']['ideas'].update(minItems=prompt['count'], maxItems=prompt['count'])
    if prompt['response_schema'] != expected:
        raise S.ScoutError('full response schema changed')
    projected = {k: prompt[k] for k in PROMPT_FIELDS}
    if digest(projected) != prompt['transmitted_payload_sha256'] or len(canonical(projected)) != prompt['known_payload_bytes']:
        raise S.ScoutError('exact prospective payload projection changed')


def payload_bytes(prompt):
    """Exact canonical input projection, without source/audit metadata or a cap.

    No dispatch or system/runtime authority is supplied by these bytes.
    """
    check_prompt(prompt)
    return canonical({k: prompt[k] for k in PROMPT_FIELDS})


def validate_response(prompt, raw):
    """Full frozen schema/lane/citation checks on the unmodified response.

    No normalisation/repair, provider call, ledger append or scientific finding.
    """
    check_prompt(prompt)
    state = E.State()
    state.seeds = copy.deepcopy(prompt['context']['seeds'])
    state.prompts = {prompt['id']: copy.deepcopy(prompt)}
    return E.parse_result(state, {'prompt_id': prompt['id']}, raw)
