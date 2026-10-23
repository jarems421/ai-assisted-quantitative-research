"""Offline evidence binding and a FIXTURE-ONLY collector STOP connection.

There is no live observation source here. Supplied records test the receiving
contract, not Windows coverage, account ownership or native runtime semantics.
Native launch remains unconditionally disabled in readiness.launch_native.
"""
import copy
import math
from pathlib import Path
import uuid

from src.research.spec import canonical
from ..schema import json_loads
from ..v004_monitoring import ACCOUNT_PATHS, compare_metadata
from ..n1_preflight import monitor as M
from . import binding as B, readiness as R

VERSION = 'SCOUT_N1_ADMISSION_STOP_V001'
ARTIFACTS = ('receipt', 'events', 'metadata', 'preparation_review', 'account_review',
             'runtime_review', 'observation_plan')
COVERAGE = {'inventory': True, 'starts': True, 'ancestry': True, 'loss_detected': False}


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def metadata_scope(value):
    B.require(isinstance(value, dict) and set(value) == {'schema', 'sampled_at', 'files',
              'credential_contents_accessed', 'probe_authorised'} and
              value['schema'] == 'SCOUT_ACCOUNT_METADATA_V004_REVIEW' and
              value['credential_contents_accessed'] is False and value['probe_authorised'] is False,
              'metadata scope/contents boundary')
    files = value['files']
    B.require(isinstance(files, dict) and set(files) == set(ACCOUNT_PATHS), 'fixed metadata watch set required')
    for item in files.values():
        B.require(isinstance(item, dict), 'invalid metadata')
        keys = {'state'} if item.get('state') == 'ABSENT' else {'state', 'size', 'mtime_ns', 'ctime_ns', 'file_id', 'device'}
        B.require(set(item) == keys and item.get('state') in ('ABSENT', 'REGULAR_FILE') and
                  all(type(v) is int for k, v in item.items() if k != 'state'), 'unobservable/incomplete metadata')


def source_hashes():
    prefix = 'src/research/opportunity_scout/'
    names = [prefix + name for name in ('n1_preflight/monitor.py', 'n1_preflight/watch.ps1',
             'n1_preflight/queue.ps1', 'v004_monitoring.py')]
    names.append('tests/fixtures/scout_n1_observer_child.py')
    return {name: B.sha((B.ROOT / name).read_bytes()) for name in names}


def preparation(artifacts, fixture):
    """Reconcile supplied original bytes. Human review remains an attestation."""
    B.require(set(artifacts) == set(ARTIFACTS) and all(type(v) is bytes for v in artifacts.values()),
              'exact evidence bytes required')
    B.require(all(len(v) <= M.MAX_BYTES for v in artifacts.values()), 'evidence size limit')
    receipt = json_loads(artifacts['receipt'].decode('utf-8'))
    expected = {**M.reader_receipt(), 'status': 'LOCAL_OBSERVER_PREPARATION_COMPLETE_NOT_AUTH_OR_N1'}
    B.require(set(receipt) == set(expected) | {'observer_head', 'observer_records', 'observer_bytes', 'observed_wall_seconds',
              'sentinel_start_exit_parent_observed', 'metadata_unchanged_observed', 'metadata_samples', 'metadata_log_sha256'},
              'V003 receipt fields changed')
    B.require(all(receipt.get(k) == v and type(receipt.get(k)) is type(v) for k, v in expected.items()),
              'V003 preparation is not successful or claims admission/coverage')
    stream = M.Stream(); stream.feed(artifacts['events'])
    B.require(stream.ended and not stream.tail, 'incomplete preparation events')
    audit = {'head': stream.previous, 'records': stream.seq, 'bytes': stream.total}
    B.require(audit == {'head': receipt.get('observer_head'), 'records': receipt.get('observer_records'),
                        'bytes': receipt.get('observer_bytes')}, 'preparation receipt/audit mismatch')
    raw = artifacts['metadata']
    B.require(raw.endswith(b'\n') and B.sha(raw) == receipt.get('metadata_log_sha256'), 'preparation metadata hash')
    rows = [json_loads(line.decode('utf-8')) for line in raw.splitlines()]
    B.require(len(rows) == receipt.get('metadata_samples') and len(rows) >= 25, 'preparation metadata count')
    previous = None
    for i, row in enumerate(rows):
        B.require(set(row) == {'seq', 'elapsed_seconds', 'metadata'} and type(row['seq']) is int and
                  row['seq'] == i + 1 and number(row['elapsed_seconds']), 'preparation metadata sequence/time')
        if previous is not None:
            B.require(0 < row['elapsed_seconds'] - previous <= 5, 'preparation metadata gap')
        metadata_scope(row['metadata'])
        B.require(compare_metadata(rows[0]['metadata'], row['metadata'])['unchanged_observed_metadata'],
                  'preparation metadata drift/unknown')
        previous = row['elapsed_seconds']
    B.require(previous - rows[0]['elapsed_seconds'] >= 120 and
              number(receipt.get('observed_wall_seconds')) and receipt['observed_wall_seconds'] >= previous and
              receipt.get('sentinel_start_exit_parent_observed') is True and receipt.get('metadata_unchanged_observed') is True,
              'preparation timing/sentinel evidence missing')
    review = json_loads(artifacts['preparation_review'].decode('utf-8'))
    B.require(set(review) == {'schema', 'fixture', 'reviewer', 'basis', 'hashes', 'audit', 'sources', 'checks', 'sentinel'},
              'preparation review fields')
    B.require(review['schema'] == VERSION and review['fixture'] is fixture and
              review['basis'] == ('FICTIONAL_REVIEW_NOT_AUTHORITY' if fixture else 'INDEPENDENT_HUMAN_REVIEW'),
              'independent preparation review required')
    B.require(isinstance(review['reviewer'], str) and bool(review['reviewer'].strip()) and
              review['reviewer'].strip().lower() not in ('unknown', 'claude', 'codex', 'chatgpt'), 'named independent reviewer required')
    B.require(review['hashes'] == {k: B.sha(artifacts[k]) for k in ('receipt', 'events', 'metadata')} and
              review['audit'] == audit and review['sources'] == source_hashes(), 'preparation review identity mismatch')
    B.require(canonical(review['checks']) == canonical({'independent_of_operator': True, 'sentinel_verified': True,
              'baseline_at_least_60_seconds': True, 'cooldown_at_least_60_seconds': True}), 'independent timing/sentinel review missing')
    sentinel = review['sentinel']
    B.require(isinstance(sentinel, dict) and set(sentinel) == {'pid', 'parent_pid', 'name', 'earliest_filetime'} and
              all(type(sentinel[k]) is int and sentinel[k] > 0 for k in ('pid', 'parent_pid', 'earliest_filetime')) and
              isinstance(sentinel['name'], str), 'independently reviewed sentinel identity required')
    stream.proof(sentinel['pid'], sentinel['parent_pid'], sentinel['name'], sentinel['earliest_filetime'])
    return audit


def review_contract(binding, approval, payload, artifacts):
    """Read-only consistency, NEVER admission. Registers/observes nothing."""
    B.validate(binding, approval, payload)
    fixture = binding['mode'] == 'LOCAL_FIXTURE'
    audit = preparation(artifacts, fixture)
    contract = binding.get('admission_contract')
    B.require(isinstance(contract, dict) and set(contract) == {'schema', 'window_id', 'artifacts', 'managed_policy_scope_sha256', 'preparation_audit'},
              'complete admission contract required')
    B.require(contract['schema'] == VERSION and contract['artifacts'] == {k: B.sha(artifacts[k]) for k in ARTIFACTS} and
              contract['preparation_audit'] == audit,
              'admission artifact hashes differ from consent')
    B.require(str(uuid.UUID(contract['window_id'])) == contract['window_id'] and
              contract['window_id'] not in (binding['session_id'], binding['reservation_id']), 'fresh observation identity required')
    account = json_loads(artifacts['account_review'].decode('utf-8'))
    B.require(set(account) == {'schema', 'fixture', 'basis', 'environment_sha256', 'identity', 'managed_policy', 'scope_sha256'} and
              account['schema'] == VERSION and account['fixture'] is fixture and
              account['basis'] == ('FICTIONAL_REVIEW_NOT_AUTHORITY' if fixture else 'OWNER_ACCOUNT_REVIEW') and
              account['environment_sha256'] == B.sha(canonical(binding['environment'])) and
              account['identity'] == 'RESEARCH_SUBSCRIPTION_REVIEWED' and account['managed_policy'] == 'ABSENT' and
              account['scope_sha256'] == contract['managed_policy_scope_sha256'], 'account/policy review missing or unsupported')
    scope = contract['managed_policy_scope_sha256']
    B.require(isinstance(scope, str) and len(scope) == 64 and all(c in '0123456789abcdef' for c in scope), 'policy scope hash required')
    verification = json_loads(artifacts['runtime_review'].decode('utf-8'))
    observations = json_loads(artifacts['observation_plan'].decode('utf-8'))
    if fixture:
        B.require(verification == {'schema': VERSION, 'fixture': True, 'basis': 'FICTIONAL_REVIEW_NOT_AUTHORITY',
                  'binary_sha256': binding['binary_sha256'], 'controls_supported': {k: True for k in R.CONTROLS}},
                  'fixture runtime controls missing/unsupported')
        R.observation_plan(binding, observations)
    else:
        R.review_plan(binding, approval, payload, verification, observations)
        B.require(binding['account_review_sha256'] == B.sha(artifacts['account_review']), 'account review not bound')
        B.require(binding['quiet_window_review_sha256'] == B.sha(artifacts['preparation_review']), 'preparation review not bound')
    registry = Path(binding['audit_root'])
    B.require(not (registry / '.lock').exists() and not (registry / (binding['reservation_id'] + '.json')).exists(),
              'stale/held/consumed reservation; no recovery')
    return {'schema': VERSION, 'status': 'OFFLINE_CONSISTENCY_ONLY_NOT_ADMISSION', 'fixture': fixture,
            'binding_sha256': B.sha(canonical(binding)), 'owner_registration_sha256': B.sha(canonical(approval)),
            'preparation_audit': audit, 'native_launch_enabled': False, 'authorises': []}


class Window:
    """Replayable receiver for fictional observations; never a live monitor.

    processes/starts must cover ALL Claude activity plus the exact fixture child.
    Coverage and separately queried creation identity are source obligations;
    V003 does not supply this active-window contract and is never relabelled.
    """
    def __init__(self, binding):
        B.require(binding.get('mode') == 'LOCAL_FIXTURE', 'native observation source not implemented')
        self.binding = copy.deepcopy(binding)
        self.phase, self.last, self.first, self.seq = 'BASELINE', None, None, 0
        self.baseline, self.expected, self.cooldown_at = None, None, None
        self.start_verified, self.bytes = False, 0

    def check(self, now):
        B.require(self.phase != 'STOP', 'monitor already stopped; no recovery')
        B.require(number(now) and (self.last is None or 0 <= now - self.last <= 5), 'monitor gap/stale evidence')

    def step(self, kind, now, data):
        try:
            self.check(now)
            if kind == 'SAMPLE':
                self._sample(now, data)
            elif kind == 'ADMIT':
                B.require(data is None and self.phase == 'BASELINE' and self.first is not None and now - self.first >= 60,
                          'fresh 60-second baseline missing')
                self.phase = 'SPAWNING'
            elif kind == 'ATTACH':
                B.require(self.phase == 'SPAWNING', 'unique collector-owned spawn required')
                self.expected = {'pid': data['pid'], 'parent_pid': data['collector_pid'],
                                 'creation_filetime': data['created_windows_filetime'],
                                 'name': Path(self.binding['binary']).name.lower()}
                self._process(self.expected)
                B.require(data['child_parent_basis'] == 'DIRECT_POPEN_CHILD', 'collector parentage unknown')
                self.phase = 'ACTIVE'
            elif kind == 'DRAINED':
                B.require(self.phase == 'ACTIVE' and self.start_verified and data is True, 'cleanup/start coverage unknown')
                self.phase, self.cooldown_at = 'COOLDOWN', now
            else:
                raise B.Refused('unknown monitor transition')
        except BaseException:
            self.phase = 'STOP'
            raise

    @staticmethod
    def _process(process):
        B.require(isinstance(process, dict) and set(process) == {'pid', 'parent_pid', 'creation_filetime', 'name'}, 'process identity scope')
        B.require(all(type(process[k]) is int and process[k] > 0 for k in ('pid', 'parent_pid', 'creation_filetime')) and
                  isinstance(process['name'], str) and process['name'] == process['name'].lower(), 'process identity/start/parent unknown')

    def _sample(self, now, record):
        B.require(self.phase in ('BASELINE', 'ACTIVE', 'COOLDOWN'), 'unexpected observation phase')
        B.require(isinstance(record, dict) and set(record) == {'frame', 'local_exit_observed'}, 'observation envelope')
        frame, exited = record['frame'], record['local_exit_observed']
        B.require(type(exited) is bool, 'local exit unknown')
        B.require(isinstance(frame, dict) and set(frame) == {'schema', 'fixture', 'window_id', 'binding_sha256', 'seq',
                  'monotonic_seconds', 'coverage', 'account_review_sha256', 'runtime_review_sha256', 'managed_policy',
                  'metadata', 'processes', 'starts', 'descendants_absent'}, 'incomplete/extra observation fields')
        self.bytes += len(canonical(frame))
        B.require(self.bytes <= M.MAX_BYTES, 'monitor recording limit')
        contract = self.binding['admission_contract']
        B.require(frame['schema'] == VERSION and frame['fixture'] is True and frame['window_id'] == contract['window_id'] and
                  frame['binding_sha256'] == B.sha(canonical(self.binding)), 'wrong observation provenance/reservation')
        B.require(type(frame['seq']) is int and frame['seq'] == self.seq + 1 and number(frame['monotonic_seconds']) and
                  0 <= now - frame['monotonic_seconds'] <= 5 and
                  (self.last is None or frame['monotonic_seconds'] > self.last), 'stale/replayed/future observation')
        B.require(canonical(frame['coverage']) == canonical(COVERAGE), 'monitor coverage lost/unknown')
        B.require(frame['account_review_sha256'] == contract['artifacts']['account_review'] and
                  frame['runtime_review_sha256'] == contract['artifacts']['runtime_review'] and
                  frame['managed_policy'] == {'state': 'ABSENT', 'scope_sha256': contract['managed_policy_scope_sha256']},
                  'account/runtime/policy changed or unsupported')
        metadata_scope(frame['metadata'])
        baseline = self.baseline if self.baseline is not None else frame['metadata']
        B.require(compare_metadata(baseline, frame['metadata'])['unchanged_observed_metadata'], 'account metadata drift')
        B.require(type(frame['processes']) is list and type(frame['starts']) is list and type(frame['descendants_absent']) is bool,
                  'process inventory/start/cleanup missing')
        for process in frame['processes'] + frame['starts']:
            self._process(process)
        if self.phase == 'ACTIVE':
            B.require(frame['processes'] == ([] if exited else [self.expected]), 'unrelated/mismatched/contradictory process')
            B.require(frame['starts'] == ([] if self.start_verified else [self.expected]), 'owned start missing/unrelated/transient start')
            self.start_verified = True
        else:
            B.require(exited is (self.phase == 'COOLDOWN') and not frame['processes'] and
                      not frame['starts'] and frame['descendants_absent'] is True,
                      'Claude/child activity outside active window or failed cleanup')
        self.baseline = copy.deepcopy(baseline)
        self.first = now if self.first is None else self.first
        self.last, self.seq = frame['monotonic_seconds'], frame['seq']
        if self.phase == 'COOLDOWN' and now - self.cooldown_at >= 60:
            self.phase = 'COMPLETE'


class FixtureGate:
    """Connect only fixed Python fixtures to supplied fictional observations.

    Baseline records are retained in the existing Capture journal after its claim.
    The callback must return promptly; blocking-source isolation is NOT provided.
    A separately reviewed real source/transport is a prerequisite for native use.
    """
    def __init__(self, binding, approval, payload, artifacts, source):
        B.require(binding.get('mode') == 'LOCAL_FIXTURE', 'native launch/source disabled')
        self.review = review_contract(binding, approval, payload, artifacts)
        self.window, self.source, self.pending, self.sink = Window(binding), source, [], None

    def emit(self, kind, now, data):
        if kind == 'SAMPLE' and len(canonical(data)) > B.LIMITS['maximum_read_chunk_bytes']:
            self.window.phase = 'STOP'
            raise B.Refused('observation frame too large')
        row = {'schema': VERSION, 'kind': kind, 'now': now, 'data': copy.deepcopy(data)}
        if self.sink is None:
            self.pending.append(row)
        else:
            self.sink('MONITOR', row)
        self.window.step(kind, now, data)

    def poll(self, now, exited=False):
        try:
            self.window.check(now)
            frame = self.source(self.window.phase, copy.deepcopy(self.window.expected), now, exited)
            if frame is not None:
                self.emit('SAMPLE', now, {'frame': frame, 'local_exit_observed': exited})
            self.window.check(now)
        except BaseException:
            self.window.phase = 'STOP'
            raise

    def prelaunch(self, binding, approval, now):
        try:
            B.require(self.review['binding_sha256'] == B.sha(canonical(binding)) and
                      self.review['owner_registration_sha256'] == B.sha(canonical(approval)), 'monitor rebound to another reservation/consent')
            self.poll(now)
            B.require(self.window.phase == 'BASELINE' and self.window.first is not None and now - self.window.first >= 60,
                      'preparation alone is not a fresh baseline')
        except BaseException:
            self.window.phase = 'STOP'
            raise

    def attach_journal(self, sink):
        B.require(self.sink is None, 'monitor already consumed')
        self.sink = sink
        for row in self.pending:
            sink('MONITOR', row)
        self.pending.clear()
