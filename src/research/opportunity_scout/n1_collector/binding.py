"""Exact-content review gates; only fixed Python fixtures are launchable here.

An external approval is an assertion from the registering human, not a signature.
No approval is generated or registered by this module. Native review never grants
launch permission and does not inspect an account or execute a CLI.
"""
import json
from datetime import datetime
import os
from pathlib import Path
import sys
import uuid

from docs.opportunity_scout.hosted_acceptance_v001 import prepare
from src.research.spec import canonical
from .. import v004_package as P
from ..storage import ROOT, unlinked
from ..v004_r3 import runtime

VERSION = 'SCOUT_N1_BYTE_COLLECTOR_V001'
FIXTURE = ROOT / 'tests/fixtures/scout_n1_child.py'
CASES = ('bytes', 'flood', 'split', 'delayed', 'trailing', 'nonzero', 'sleep', 'threshold')
LIMITS = {'watchdog_seconds': 600, 'combined_recording_io_trigger_bytes': 12 * 1024 * 1024,
          'maximum_read_chunk_bytes': 65536, 'cancel_escalation_after_seconds': 5,
          'drain_grace_maximum_seconds': 30}


class Refused(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise Refused(reason)


def sha(value):
    return P.byte_hash(value)


def implementation():
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
            for p in sorted(Path(__file__).parent.glob('*.py'))}


def proposal():
    prepare.check()  # Including original source closure and unchanged schema.
    return {name: sha((prepare.HERE / name).read_bytes()) for name in
            ('manifest.json', 'protocol.json', 'request.json', 'system-prompt.txt', 'runtime-template.json')}


def seeds():
    rows = prepare.request()['context']['seeds']
    require(all(s['approved_for_hosted_use'] is False for s in rows.values()), 'seed metadata changed')
    return {k: v['sha256'] for k, v in rows.items()}


def exact_path(value):
    require(isinstance(value, str) and Path(value).is_absolute(), 'absolute bound path required')
    p = unlinked(value)
    require(str(p) == value and '..' not in Path(value).parts, 'noncanonical path')
    return p


def validate(binding, approval, payload):
    """Common bindings, rechecked immediately before consumption/launch.

    LOCAL_FIXTURE approvals are simulated permissions only, never hosted consent.
    NATIVE_REVIEW_ONLY verifies a proposed external registration, but the native
    launch boundary remains disabled in this version regardless of its contents.
    """
    require(isinstance(binding, dict) and binding.get('version') == VERSION, 'unbound template')
    mode = binding.get('mode')
    require(mode in ('LOCAL_FIXTURE', 'NATIVE_REVIEW_ONLY'), 'unknown binding mode')
    require(binding.get('proposal') == proposal(), 'N1 proposal hash mismatch')
    require(binding.get('implementation') == implementation(), 'collector implementation mismatch')
    require(binding.get('dependencies') == P.dependencies(), 'runtime dependency mismatch')
    expected = (prepare.HERE / 'request.json').read_bytes()
    require(isinstance(payload, bytes) and payload == expected, 'exact N1 stdin required')
    require(binding.get('stdin_sha256') == sha(payload), 'stdin hash mismatch')
    require(binding.get('system_sha256') == sha((prepare.HERE / 'system-prompt.txt').read_bytes()), 'system hash mismatch')
    system = P.destination(exact_path(binding.get('system_file')))
    require(P.read_bytes(system) == (prepare.HERE / 'system-prompt.txt').read_bytes(), 'bound system bytes mismatch')
    for key in ('reservation_id', 'session_id'):
        require(str(uuid.UUID(binding[key])) == binding[key], 'canonical UUID required')
    capture = P.destination(exact_path(binding['capture_path']))
    audit = P.destination(exact_path(binding['audit_root']))
    cwd = P.destination(exact_path(binding['cwd']))
    require(not capture.exists(), 'capture already exists; no reuse')
    require(not audit.is_relative_to(capture) and not capture.is_relative_to(audit), 'independent reservation registry required')
    require(cwd.is_dir() and not any(cwd.iterdir()), 'sterile directory required')
    require(not cwd.is_relative_to(capture) and not capture.is_relative_to(cwd), 'capture/cwd overlap')
    require(not cwd.is_relative_to(audit) and not audit.is_relative_to(cwd), 'registry/cwd overlap')
    require(not system.is_relative_to(capture) and not system.is_relative_to(audit), 'system file overlaps mutable evidence')
    binary = P.destination(exact_path(binding['binary']))
    require(binary.is_file() and sha(binary.read_bytes()) == binding.get('binary_sha256'), 'executable identity mismatch')
    require(isinstance(binding.get('environment'), dict), 'explicit child-only environment required')
    limits = binding.get('limits')
    require(isinstance(limits, dict) and set(limits) == set(LIMITS), 'complete resource controls required')
    require(all(type(limits[k]) in (int, float) and 0 < limits[k] <= v for k, v in LIMITS.items()), 'invalid resource controls')
    require(type(limits['maximum_read_chunk_bytes']) is int and type(limits['combined_recording_io_trigger_bytes']) is int, 'integer byte controls required')
    require(isinstance(approval, dict), 'missing explicit approval')
    require(approval.get('version') == VERSION and approval.get('mode') == mode, 'approval scope mismatch')
    require(approval.get('binding_sha256') == sha(canonical(binding)), 'approval does not bind full package/runtime/reservation')
    require(approval.get('approved') is True and approval.get('seeds') == seeds(), 'missing explicit seed/content consent')
    require(approval.get('retained_seed_hosting_flags') is False and approval.get('N1_only_exception') is True, 'retained-false exception not explicitly adopted')
    require(approval.get('single_invocation_only') is True and approval.get('trusted_local_filesystem_accepted') is True, 'reservation/rollback scope not accepted')
    require(approval.get('privacy_resource_retention_accepted') is True, 'privacy/resource/retention decision missing')
    require(isinstance(approval.get('owner'), str) and bool(approval['owner'].strip()) and
            isinstance(approval.get('registered_at'), str) and bool(approval['registered_at'].strip()), 'owner identity/date required')
    try:
        date = datetime.fromisoformat(approval['registered_at'])
    except ValueError as error:
        raise Refused('invalid consent date') from error
    require(date.utcoffset() is not None and approval['owner'].strip() not in ('UNKNOWN', 'UNBOUND'), 'bound identity and timezone date required')
    if mode == 'LOCAL_FIXTURE':
        require(approval['owner'] == 'LOCAL_FIXTURE_NOT_OWNER_CONSENT', 'fixture approval cannot impersonate owner')
        require(binary == Path(sys.executable).absolute(), 'fixtures require this Python binary')
        require(binding.get('fixture_sha256') == sha(FIXTURE.read_bytes()), 'fixture source mismatch')
        require(binding.get('case') in CASES and binding.get('argv') == [str(binary), '-I', str(FIXTURE), binding['case']], 'only fixed harmless fixture argv allowed')
        require(binding['environment'] == fixture_environment(), 'fixture environment mismatch')
        require(binding.get('runtime') == 'LOCAL_PYTHON_NOT_A_MODEL', 'fixture is not native approval')
    else:
        require(limits == LIMITS, 'native limits must be unchanged')
        require(binding.get('provider') == 'ANTHROPIC_CLAUDE_CODE_SUBSCRIPTION', 'subscription provider must be explicit')
        r = binding.get('runtime', {})
        require(isinstance(r, dict), 'complete bound native runtime required')
        require(r == runtime.description(r.get('model'), binding['binary_sha256'], r.get('cli_version')), 'runtime differs from R3')
        require(isinstance(r.get('model'), str) and r['model'].startswith('claude-opus-') and '99-' not in r['model'], 'actual pinned model required')
        require(r.get('cli_version') not in (None, '', 'UNKNOWN') and 'UNBOUND' not in r['cli_version'], 'actual CLI version required')
        proto = json.loads((prepare.HERE / 'protocol.json').read_text())
        replacements = {'<BOUND_ABSOLUTE_BINARY>': str(binary), '<BOUND_CANONICAL_OPUS_ID>': r['model'],
                        '<BOUND_FRESH_UUID>': binding['session_id'], '<BOUND_SYSTEM_FILE>': str(system)}
        require(binding.get('argv') == [replacements.get(x, x) for x in proto['candidate_argv_review_only']], 'argv mismatch')
        require(binding.get('environment') == runtime.child_environment(binding.get('os_environment', {}),
                binding.get('research_config_path'), binding.get('home_path')), 'separate allowlisted research environment required')
        for key in ('private_access_policy', 'private_retention_policy'):
            require(isinstance(binding.get(key), str) and binding[key].strip() not in ('', 'UNKNOWN'), 'private evidence policy missing')
        # Review evidence references only. No account/process sampler is invoked.
        for key in ('account_review_sha256', 'quiet_window_review_sha256'):
            value = binding.get(key)
            require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'account/quiet-window review bindings missing')
        require(binding.get('native_environment_review_sha256') == sha(canonical(binding['environment'])), 'environment review missing')
    return {'binding_sha256': sha(canonical(binding)), 'approval_sha256': sha(canonical(approval)),
            'native_launch_enabled': False, 'native_semantics': 'UNKNOWN', 'mode': mode}


def fixture_environment():
    # No inherited credential/provider/IDE variables, even for harmless fixtures.
    return {k: os.environ[k] for k in ('SystemRoot', 'WINDIR') if k in os.environ}


def review_native(binding, approval, payload):
    require(binding.get('mode') == 'NATIVE_REVIEW_ONLY', 'not a native review binding')
    return validate(binding, approval, payload)
