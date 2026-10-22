"""Durable single-use OFFLINE rehearsal, not a real or callable model runner.

No execution callback, process launcher, network or credential reader exists.
Only SYNTHETIC packages and immutable Recording values are admitted. A pending
consumption marker is terminal on reopening: failure cannot be reset/retried.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import uuid

from src.research.spec import canonical, digest
from . import schema as S, v004_package as P, v004_transport as T, v004_isolation as I
from .storage import unlinked

VERSION = 'SCOUT_V004_OFFLINE_JOURNAL_R1'
GENESIS = '0' * 64


@contextmanager
def locked(root):
    lock = unlinked(root / '.lock')
    try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error: raise S.ScoutError('journal locked; never remove another writer lock') from error
    try: yield
    finally: os.close(fd); lock.unlink()


class OfflineRun:
    def __init__(self, directory):
        self.root = P.destination(directory)
        self._pending = None  # Only the creating handle may finish its marker.

    @classmethod
    def create(cls, directory, package):
        manifest, _ = P.load(package)
        if manifest['mode'] != 'SYNTHETIC': raise S.ScoutError('real packages cannot be rehearsed as model attempts')
        run = cls(directory)
        if run.root.resolve().is_relative_to(Path(package).resolve()): raise S.ScoutError('journal cannot modify frozen package')
        run.root.mkdir(parents=True, exist_ok=False)
        binding = {'schema': VERSION, 'package': str(Path(package).absolute()),
                   'manifest_sha256': digest(manifest), 'fictional': True, 'hosted_authorised': False}
        P.write_bytes(run.root / 'run.json', canonical(binding) + b'\n')
        with locked(run.root): run._append([], 'CREATED', {'binding_sha256': digest(binding)})
        return run

    def _append(self, events, kind, record):
        core = {'seq': len(events) + 1, 'previous': events[-1]['hash'] if events else GENESIS,
                'recorded_at': S.utc_now(), 'type': kind, 'record': record}
        event = {**core, 'hash': digest(core)}
        p = unlinked(self.root / 'journal.jsonl')
        with p.open('ab') as stream:
            stream.write(canonical(event) + b'\n'); stream.flush(); os.fsync(stream.fileno())
        return event

    def _load(self):
        binding = S.json_loads(P.read_bytes(self.root / 'run.json').decode('utf-8'))
        manifest, requests = P.load(binding['package'])
        expected_binding = {'schema': VERSION, 'package': binding['package'], 'manifest_sha256': digest(manifest),
                            'fictional': True, 'hosted_authorised': False}
        if binding != expected_binding or manifest['mode'] != 'SYNTHETIC': raise S.ScoutError('run/package binding changed')
        path = unlinked(self.root / 'journal.jsonl')
        if path.stat().st_size > 32 * 1024 * 1024 or path.stat().st_nlink != 1: raise S.ScoutError('unsafe journal')
        raw = P.read_bytes(path)
        if not raw.endswith(b'\n'): raise S.ScoutError('interrupted journal; no resume/reset')
        events, consumed, results, pending, stopped, sessions, cwds = [], [], {}, None, False, set(), set()
        for line in raw.splitlines():
            event = S.json_loads(line.decode('utf-8'))
            if set(event) != {'seq', 'previous', 'recorded_at', 'type', 'record', 'hash'}: raise S.ScoutError('journal envelope changed')
            core = {k: v for k, v in event.items() if k != 'hash'}
            if event['seq'] != len(events) + 1 or event['previous'] != (events[-1]['hash'] if events else GENESIS) or digest(core) != event['hash']:
                raise S.ScoutError('journal hash chain mismatch')
            if events and S.timestamp(event['recorded_at']) < S.timestamp(events[-1]['recorded_at']): raise S.ScoutError('journal time reversed')
            kind, r = event['type'], event['record']
            if not events:
                if kind != 'CREATED' or r != {'binding_sha256': digest(binding)}: raise S.ScoutError('missing run genesis')
            elif kind == 'CONSUMED':
                if stopped or pending or len(consumed) >= 12: raise S.ScoutError('dispatch after stop/pending/end')
                expected_slot = manifest['order'][len(consumed)]['slot']
                if (set(r) != {'slot', 'request_sha256', 'runtime_sha256', 'session_id', 'sterile_directory', 'parent_invocations'}
                        or r['slot'] != expected_slot or r['request_sha256'] != digest(requests[expected_slot])
                        or r['runtime_sha256'] != digest(manifest['runtime']) or r['parent_invocations'] != 1
                        or r['session_id'] in sessions or r['sterile_directory'] in cwds):
                    raise S.ScoutError('consumption slot/context binding violated')
                uuid.UUID(r['session_id'])
                pending = r; consumed.append(r); sessions.add(r['session_id']); cwds.add(r['sterile_directory'])
            elif kind == 'RESULT':
                if stopped or pending is None or set(r) != {'slot', 'receipt_sha256', 'receipt_file'} or r['slot'] != pending['slot']:
                    raise S.ScoutError('result has no unique consumed attempt')
                previous_end = list(results.values())[-1]['account_monitoring']['window_end'] if results else None
                receipt = self._read_receipt(r, requests[pending['slot']], pending, previous_end)
                results[pending['slot']] = receipt; pending = None
                if receipt['outcome'] == 'RUN_STOP': stopped = True
            else: raise S.ScoutError('unsupported/duplicate journal event')
            events.append(event)
        return binding, manifest, requests, events, consumed, results, pending, stopped

    def _read_receipt(self, result, request, consumed, previous_window_end):
        # Derive all names, never use receipt-supplied paths outside the journal.
        slot = consumed['slot']; folder = unlinked(self.root / 'attempts' / slot)
        if result['receipt_file'] != f'attempts/{slot}/receipt.json': raise S.ScoutError('receipt path changed')
        receipt = S.json_loads(P.read_bytes(folder / 'receipt.json').decode('utf-8'))
        if digest(receipt) != result['receipt_sha256']: raise S.ScoutError('receipt changed')
        stdout = P.read_bytes(folder / 'stdout.bin'); stderr = P.read_bytes(folder / 'stderr.bin')
        monitoring = S.json_loads(P.read_bytes(folder / 'monitoring.json').decode('utf-8'))
        if (P.byte_hash(stdout) != receipt['stdout_sha256'] or P.byte_hash(stderr) != receipt['stderr_sha256']
                or digest(monitoring) != receipt['monitoring_sha256']): raise S.ScoutError('original evidence changed')
        recording = T.Recording(stdout, stderr, **receipt['recording_metadata'])
        expected = evaluate(recording, request, consumed['session_id'], monitoring, previous_window_end)
        expected.update({'stdout_sha256': P.byte_hash(stdout), 'stderr_sha256': P.byte_hash(stderr),
                         'monitoring_sha256': digest(monitoring), 'recording_metadata': receipt['recording_metadata']})
        if expected != receipt or P.read_bytes(folder / 'output.bin') != receipt['exact_output'].encode('utf-8'):
            raise S.ScoutError('receipt replay/output assembly mismatch')
        return receipt

    def start(self):
        """Durably consume the next slot before reading its fictional result."""
        if self._pending: raise S.ScoutError('this handle already consumed a slot')
        with locked(self.root):
            _, manifest, requests, events, consumed, _, pending, stopped = self._load()
            if pending or stopped or len(consumed) >= 12: raise S.ScoutError('stopped, interrupted or finished run; no resume/retry')
            slot = manifest['order'][len(consumed)]['slot']; session = str(uuid.uuid4())
            record = {'slot': slot, 'request_sha256': digest(requests[slot]),
                      'runtime_sha256': digest(manifest['runtime']), 'session_id': session,
                      'sterile_directory': 'FICTIONAL-STERILE-' + session, 'parent_invocations': 1}
            self._append(events, 'CONSUMED', record); self._pending = record
            return dict(record)

    def finish(self, recording, monitoring):
        """At most one immutable result, no callbacks or further parent calls."""
        if not self._pending: raise S.ScoutError('no locally owned pending marker')
        with locked(self.root):
            _, _, requests, events, _, results, pending, stopped = self._load()
            if stopped or pending != self._pending: raise S.ScoutError('pending ownership changed')
            slot = pending['slot']; request = requests[slot]
            previous_end = list(results.values())[-1]['account_monitoring']['window_end'] if results else None
            receipt = evaluate(recording, request, pending['session_id'], monitoring, previous_end)
            # Three reserved attempts * at most 600 reported seconds implies
            # the unchanged 1800-second condition ceiling. UNKNOWN/excess wall
            # time already stops; no inferred human-time compliance is granted.
            folder = self.root / 'attempts' / slot; folder.mkdir(parents=True, exist_ok=False)
            metadata = {k: getattr(recording, k) for k in ('returncode', 'timed_out', 'wall_seconds', 'fictional')}
            receipt.update({'stdout_sha256': P.byte_hash(recording.stdout), 'stderr_sha256': P.byte_hash(recording.stderr),
                            'monitoring_sha256': digest(monitoring), 'recording_metadata': metadata})
            for name, data in (('stdout.bin', recording.stdout), ('stderr.bin', recording.stderr),
                               ('output.bin', receipt['exact_output'].encode('utf-8')),
                               ('monitoring.json', canonical(monitoring) + b'\n'),
                               ('receipt.json', canonical(receipt) + b'\n')):
                P.write_bytes(folder / name, data)
            self._append(events, 'RESULT', {'slot': slot, 'receipt_sha256': digest(receipt),
                                           'receipt_file': f'attempts/{slot}/receipt.json'})
            self._pending = None
            return receipt

    def status(self):
        _, manifest, _, _, consumed, results, pending, stopped = self._load()
        rows = []
        for slot in manifest['order']:
            result = results.get(slot['slot'])
            rows.append({**slot, 'status': result['outcome'] if result else
                         'CONSUMED_INTERRUPTED' if any(c['slot'] == slot['slot'] for c in consumed) else 'NOT_RUN',
                         'intended_card_slots': 2, 'budget': result['budget'] if result else S.UNKNOWN,
                         'review_required_even_if_invalid': True})
        return {'schema': VERSION, 'fictional': True, 'consumed_attempts': len(consumed),
                'recorded_attempts': len(results), 'undispatched': 12 - len(consumed),
                'stopped': stopped or pending is not None, 'pending_requires_owner_review': pending is not None,
                'workflow_complete': len(results) == 12 and not stopped and pending is None,
                'complete_scientific_comparison': False, 'independent_human_reviews': S.UNKNOWN,
                'human_effort': S.UNKNOWN, 'intended_attempt_denominator': 12,
                'intended_card_denominator': 24, 'slots': rows,
                'hosted_authorised': False, 'authorises': []}


def evaluate(recording, request, session_id, monitoring, previous_window_end=None):
    receipt = T.review(recording, request, session_id)
    isolation = I.review(monitoring, session_id=session_id, previous_window_end=previous_window_end)
    receipt['account_monitoring'] = isolation
    if not isolation['sampled_window_clean']:
        receipt['faults'] += ['ACCOUNT_MONITORING_WINDOW_FAILED']; receipt['outcome'] = 'RUN_STOP'
    return receipt
