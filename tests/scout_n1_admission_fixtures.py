"""Fictional observations/reviews. Never a live observer or owner registration."""
import copy
from pathlib import Path
import time
from types import SimpleNamespace
import uuid

from src.research.spec import canonical
from src.research.opportunity_scout.n1_collector import admission as A, binding as B, readiness as R
from src.research.opportunity_scout.n1_preflight import monitor as M
from src.research.opportunity_scout.v004_monitoring import ACCOUNT_PATHS
from tests.opportunity_scout.test_n1_preflight_monitor import Records
from tests.scout_n1_fixtures import plan, consent


def metadata():
    return {'schema': 'SCOUT_ACCOUNT_METADATA_V004_REVIEW', 'sampled_at': '2000-01-01T00:00:00+00:00',
            'credential_contents_accessed': False, 'probe_authorised': False,
            'files': {name: {'state': 'ABSENT'} for name in ACCOUNT_PATHS}}


def package(root, case='bytes'):
    b, _, payload = plan(root, case, watchdog_seconds=120)
    r = Records(); events = r.prefix()
    for elapsed in range(5000, 120001, 5000):
        if elapsed == 60000:
            events += r.row('START', {'pid': 55, 'parent_pid': 10, 'name': 'python.exe', 'event_filetime': '100'}, elapsed)
            events += r.row('EXIT', {'pid': 55, 'name': 'python.exe', 'event_filetime': '101'}, elapsed)
        events += r.row('HEARTBEAT', {'subscriptions_present': True}, elapsed)
    events += r.row('END', {'reason': 'STOP_REQUEST', 'coverage_certified': False}, 120000)
    raw = b''.join(canonical({'seq': i + 1, 'elapsed_seconds': i * 5, 'metadata': metadata()}) + b'\n' for i in range(25))
    receipt = {**M.reader_receipt(), 'status': 'LOCAL_OBSERVER_PREPARATION_COMPLETE_NOT_AUTH_OR_N1',
               'observer_head': r.previous, 'observer_records': r.seq, 'observer_bytes': len(events),
               'observed_wall_seconds': 120, 'sentinel_start_exit_parent_observed': True,
               'metadata_unchanged_observed': True, 'metadata_samples': 25, 'metadata_log_sha256': B.sha(raw)}
    artifacts = {'receipt': canonical(receipt), 'events': events, 'metadata': raw}
    review = {'schema': A.VERSION, 'fixture': True, 'reviewer': 'FICTIONAL_INDEPENDENT_REVIEWER',
              'basis': 'FICTIONAL_REVIEW_NOT_AUTHORITY', 'hashes': {k: B.sha(v) for k, v in artifacts.items()},
              'audit': {'head': r.previous, 'records': r.seq, 'bytes': len(events)}, 'sources': A.source_hashes(),
              'sentinel': {'pid': 55, 'parent_pid': 10, 'name': 'python.exe', 'earliest_filetime': 100},
              'checks': {'independent_of_operator': True, 'sentinel_verified': True,
                         'baseline_at_least_60_seconds': True, 'cooldown_at_least_60_seconds': True}}
    scope = B.sha(b'FICTIONAL presence-only managed policy scope, no actual observation')
    artifacts.update(preparation_review=canonical(review),
        account_review=canonical({'schema': A.VERSION, 'fixture': True, 'basis': 'FICTIONAL_REVIEW_NOT_AUTHORITY',
            'environment_sha256': B.sha(canonical(b['environment'])), 'identity': 'RESEARCH_SUBSCRIPTION_REVIEWED',
            'managed_policy': 'ABSENT', 'scope_sha256': scope}),
        runtime_review=canonical({'schema': A.VERSION, 'fixture': True, 'basis': 'FICTIONAL_REVIEW_NOT_AUTHORITY',
            'binary_sha256': b['binary_sha256'], 'controls_supported': {k: True for k in R.CONTROLS}}),
        observation_plan=canonical({'schema': R.VERSION, 'kind': 'PROSPECTIVE_OBSERVATION_PLAN',
            'session_id': b['session_id'], 'capture_path': b['capture_path'], 'account_paths': list(ACCOUNT_PATHS),
            'baseline_seconds': 60, 'cooldown_seconds': 60, 'maximum_sample_gap_seconds': 5,
            'managed_policy_presence_check': True, 'process_start_ancestry_coverage': True,
            'stop_on_any_metadata_drift': True, 'stop_on_development_process': True,
            'credential_content_reads': False, 'historical_writer': 'UNKNOWN',
            'baseline_observed': False, 'active_window_observed': False}))
    b['admission_contract'] = {'schema': A.VERSION, 'window_id': str(uuid.uuid4()),
                              'preparation_audit': review['audit'],
                              'artifacts': {k: B.sha(v) for k, v in artifacts.items()}, 'managed_policy_scope_sha256': scope}
    return b, consent(b), payload, artifacts


def frame(b, seq, now, phase='BASELINE', expected=None, *, first=False, exited=False):
    c = b['admission_contract']
    return {'schema': A.VERSION, 'fixture': True, 'window_id': c['window_id'],
            'binding_sha256': B.sha(canonical(b)), 'seq': seq, 'monotonic_seconds': now,
            'coverage': copy.deepcopy(A.COVERAGE), 'account_review_sha256': c['artifacts']['account_review'],
            'runtime_review_sha256': c['artifacts']['runtime_review'],
            'managed_policy': {'state': 'ABSENT', 'scope_sha256': c['managed_policy_scope_sha256']},
            'metadata': metadata(), 'processes': [expected] if phase == 'ACTIVE' and not exited else [],
            'starts': [expected] if phase == 'ACTIVE' and first else [], 'descendants_absent': phase != 'ACTIVE'}


def baseline(window, b, end=60):
    for i in range(13):
        when = end - 60 + i * 5
        window.step('SAMPLE', when, {'frame': frame(b, i + 1, when), 'local_exit_observed': False})


def process_identity():
    return {'pid': 55, 'collector_pid': 10, 'created_windows_filetime': 100,
            'child_parent_basis': 'DIRECT_POPEN_CHILD'}


def monitored(root, case='sleep', fault=None):
    """Real fixed Python child; all observation identity/coverage claims fictional.

    Only collector.clock is virtualised to avoid a real 60-second fixture wait.
    No OS sampler, WMI, account access or native process is supplied.
    """
    b, a, data, artifacts = package(root, case)
    offset = SimpleNamespace(value=0.0)
    clock = lambda: time.monotonic() + offset.value
    state = SimpleNamespace(seq=0, first=True, cooldown=False)

    def source(phase, expected, now, exited):
        state.seq += 1
        row = frame(b, state.seq, now, phase, expected, first=phase == 'ACTIVE' and state.first, exited=exited)
        if phase == 'ACTIVE':
            state.first = False
            raw = Path(b['capture_path']) / 'stdout.bin'
            if raw.exists() and raw.stat().st_size:
                if fault == 'coverage': row['coverage']['starts'] = False
                if fault == 'identity' and row['processes']: row['processes'][0]['creation_filetime'] += 1
                if fault == 'stale': row['monotonic_seconds'] -= 6
                if fault == 'drift': row['metadata']['files']['.claude-research.json'] = {'state': 'UNOBSERVABLE'}
                if fault == 'source_error': raise OSError('fictional observation transport failure')
        if phase == 'COOLDOWN':
            if fault == 'cleanup': row['descendants_absent'] = False
            if fault == 'late_return' and now - gate.window.cooldown_at >= 60:
                offset.value += 6  # A late final callback must not yield a successful receipt.
        return row

    gate = A.FixtureGate(b, a, data, artifacts, source)
    end = clock() - .01
    for i in range(13):
        when = end - 60 + i * 5
        state.seq += 1
        gate.emit('SAMPLE', when, {'frame': frame(b, state.seq, when), 'local_exit_observed': False})
    def sleep(seconds):
        if gate.window.phase == 'COOLDOWN':
            offset.value += 4  # Advance BETWEEN samples; callback latency stays separately measurable.
        time.sleep(seconds)
    return b, a, data, gate, SimpleNamespace(monotonic=clock, monotonic_ns=time.monotonic_ns, sleep=sleep)
