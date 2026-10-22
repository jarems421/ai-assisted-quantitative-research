"""R3 candidate description; identical environment, no execution capability."""
from src.research.spec import digest
from .. import v004_runtime as legacy
from . import policy

VERSION = 'SCOUT_V004_RAW_JSON_RUNTIME_R3'
SYSTEM_PROMPT = legacy.SYSTEM_PROMPT
child_environment = legacy.child_environment


def description(model, binary_sha256, cli_version):
    result = legacy.description(model, binary_sha256, cli_version)
    del result['combined_allowance']
    result.update(schema=VERSION, resource_policy=policy.description(),
                  resource_policy_sha256=policy.policy_hash(),
                  resource_enforcement='OFFLINE_DECISIONS_ONLY_NOT_ACTIVATED',
                  native_live_usage_support='UNKNOWN')
    return result


def validate(value):
    from ..schema import ScoutError
    if not isinstance(value, dict) or not all(k in value for k in ('model', 'binary_sha256', 'cli_version')):
        raise ScoutError('complete R3 runtime required')
    if value != description(value['model'], value['binary_sha256'], value['cli_version']):
        raise ScoutError('R3 runtime/policy differs from the frozen candidate')
    return digest(value)
