"""Real design-only manifests: hash validation and blockers, no Store/engine imports."""
import hashlib,json,importlib.metadata,platform
from datetime import date
from pathlib import Path
from src.research.spec import digest
from src.research.phase3c.sources import put
ROLES=('population','source_surface','source_snapshot','availability','identity','feature_contract','benchmark_contract','execution_contract','inference_contract','trial_family','cost_contract')
def environment():return {'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ('numpy','duckdb','pyarrow','nexustrade','jsonschema')}}
def compile_design(spec,root,output):
    if spec.get('mode')!='DESIGN_ONLY' or spec.get('estimand_type')!='PREDICTIVE':raise ValueError('Design-only predictive contract required')
    for key in ('performance_authorized','performance_executed','experiment_registered'):
        if spec.get(key) is not False:raise ValueError('No performance or registration authority')
    if set(spec['contracts'])!=set(ROLES):raise ValueError('Every design role required')
    root=Path(root).resolve();records={}
    for role,ref in spec['contracts'].items():
        path=(root/ref['path']).resolve()
        if Path(ref['path']).is_absolute() or not path.is_relative_to(root):raise ValueError('Reference escape')
        body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=ref['sha256']:raise ValueError('Contract hash mismatch')
        records[role]=json.loads(body)
    source=records['source_snapshot']
    if date.fromisoformat(source['source_end'])>date.fromisoformat(spec['research_cutoff']):raise ValueError('Source crosses cutoff')
    if source['evidence_tier'] not in ('PRIMARY_ORIGINAL','PRIMARY_INDEX_OR_METADATA','AUDITED_EXTERNAL_DERIVED'):raise ValueError('Unsupported evidence tier')
    if source['evidence_tier']=='AUDITED_EXTERNAL_DERIVED' and not source.get('owner_acceptance_receipt_sha256'):raise ValueError('Derived snapshot requires separate owner acceptance for real design use')
    if not source.get('upstream_version') or not source.get('source_sha256s'):raise ValueError('Pinned source version/hashes missing')
    if records['availability'].get('status') not in ('ACCEPTANCE_OBSERVED','DATE_ONLY','MODELED_BOUND_PLAUSIBLE','PUBLIC_TIMESTAMP_UNKNOWN'):raise ValueError('Unclassified/contradictory timing')
    if not records['identity'].get('required'):raise ValueError('Historical identity requirements missing')
    for role in ('feature_contract','benchmark_contract','execution_contract','cost_contract'):
        if not records[role]:raise ValueError('Empty design contract: '+role)
    if type(records['trial_family'].get('ceiling')) is not int or records['trial_family']['ceiling']<1:raise ValueError('Trial ceiling missing')
    if records['population'].get('status')!='SOURCE_CONTRACT_READY_FOR_DESIGN':raise ValueError('Denominator contract not ready')
    if records['inference_contract'].get('obviously_impossible') is not False:raise ValueError('Inference geometry unresolved/impossible')
    blockers=spec.get('known_blockers',[])
    result={'version':'proof_design_v002','status':'STRUCTURALLY_READY_FOR_EXPERIMENT_FREEZE_REVIEW','spec_sha256':digest(spec),
     'contracts':spec['contracts'],'research_cutoff':spec['research_cutoff'],'source_adapter_version':records['source_surface']['version'],
     'upstream_version':source['upstream_version'],'timing_status':records['availability']['status'],'identity_requirements':records['identity'],
     'inference_geometry':records['inference_contract'],'trial_ceiling':records['trial_family']['ceiling'],'known_blockers':blockers,
     'scientifically_certified':False,'performance_authorized':False,'performance_executed':False,'experiment_registered':False,
     'environment':environment(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
     'code_fingerprints':{str(p.relative_to(Path(__file__).resolve().parents[2])):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ('surfaces','integrations','signals') for p in sorted((Path(__file__).parent/directory).glob('*.py'))}}
    put(Path(output)/(digest(result)+'.json'),result)
    return result
