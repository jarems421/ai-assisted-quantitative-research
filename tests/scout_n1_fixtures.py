"""Simulated local bindings, never an execution approval or hosted consent."""
import copy
from pathlib import Path
import sys
import uuid

from docs.opportunity_scout.hosted_acceptance_v001 import prepare
from src.research.spec import canonical
from src.research.opportunity_scout import v004_package as P
from src.research.opportunity_scout.n1_collector import binding as B


def plan(root, case='bytes', **limits):
    root = Path(root).absolute()
    cwd = root / ('cwd-' + str(uuid.uuid4()))
    cwd.mkdir()
    system = root / ('system-' + str(uuid.uuid4()) + '.txt')
    system.write_bytes((prepare.HERE / 'system-prompt.txt').read_bytes())
    binary = str(Path(sys.executable).absolute())
    payload = (prepare.HERE / 'request.json').read_bytes()
    b = {'version': B.VERSION, 'mode': 'LOCAL_FIXTURE', 'proposal': B.proposal(),
         'implementation': B.implementation(), 'dependencies': P.dependencies(),
         'stdin_sha256': B.sha(payload), 'system_sha256': B.sha(system.read_bytes()),
         'system_file': str(system), 'reservation_id': str(uuid.uuid4()), 'session_id': str(uuid.uuid4()),
         'capture_path': str(root / ('capture-' + str(uuid.uuid4()))), 'audit_root': str(root / 'registry'),
         'cwd': str(cwd), 'binary': binary, 'binary_sha256': B.sha(Path(binary).read_bytes()),
         'argv': [binary, '-I', str(B.FIXTURE), case], 'fixture_sha256': B.sha(B.FIXTURE.read_bytes()),
         'environment': B.fixture_environment(), 'runtime': 'LOCAL_PYTHON_NOT_A_MODEL', 'case': case,
         'limits': {**B.LIMITS, 'watchdog_seconds': 30, 'cancel_escalation_after_seconds': .1,
                    **limits}}
    return b, consent(b), payload


def consent(b):
    return {'version': B.VERSION, 'mode': b['mode'], 'owner': 'LOCAL_FIXTURE_NOT_OWNER_CONSENT',
            'registered_at': '2000-01-01T00:00:00+00:00', 'approved': True,
            'binding_sha256': B.sha(canonical(b)), 'seeds': B.seeds(),
            'retained_seed_hosting_flags': False, 'N1_only_exception': True,
            'single_invocation_only': True, 'trusted_local_filesystem_accepted': True,
            'privacy_resource_retention_accepted': True}


def changed(b, **fields):
    b = copy.deepcopy(b)
    b.update(fields)
    return b, consent(b)
