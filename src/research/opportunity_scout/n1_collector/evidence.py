"""One N1 capture reservation, witnessed journal and read-only byte audit.

This is not a scientific-attempt journal. No resume, reset, lock recovery or
evidence repair exists. Local hashes detect inconsistency, not coordinated rollback.
"""
import json
import os
from pathlib import Path
import time

from src.research.spec import canonical
from .. import v004_package as P
from .binding import VERSION, require, sha, prepare


def sync_directory(path):
    # File fsync is available on Windows; portable directory fsync is not.
    # Do not describe Windows namespace persistence as a power-loss certificate.
    if os.name != 'nt':
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def exclusive(path, data):
    P.write_bytes(path, data)
    sync_directory(path.parent)


class Capture:
    def __init__(self, binding, approval):
        self.root = Path(binding['capture_path'])
        self.registry = Path(binding['audit_root'])
        self.registry.mkdir(parents=True, exist_ok=True)
        sync_directory(self.registry.parent)
        self.lock = self.registry / '.lock'
        # Never remove another process's lock, even if its PID appears dead.
        exclusive(self.lock, canonical({'pid': os.getpid(), 'created_ns': time.time_ns()}))
        self.files = {}
        self.closed, self.ended, self.poisoned = False, False, False
        self.seq, self.head = 0, '0' * 64
        try:
            claim = {'version': VERSION, 'type': 'CONSUMED_BEFORE_LAUNCH',
                     'capture_path': str(self.root), 'reservation_id': binding['reservation_id'],
                     'binding_sha256': sha(canonical(binding)), 'approval_sha256': sha(canonical(approval)),
                     'created_ns': time.time_ns(), 'launch_after_crash': 'UNKNOWN_NO_RETRY'}
            exclusive(self.registry / (binding['reservation_id'] + '.json'), canonical(claim))
            self.root.mkdir(exist_ok=False)
            sync_directory(self.root.parent)
            (self.root / 'witnesses').mkdir()
            sync_directory(self.root)
            exclusive(self.root / 'binding.json', canonical(binding))
            exclusive(self.root / 'approval.json', canonical(approval))
            exclusive(self.root / 'claim.json', canonical(claim))
            for name in ('stdout', 'stderr'):
                self.files[name] = (self.root / (name + '.bin')).open('xb')
                self.files[name].flush()
                os.fsync(self.files[name].fileno())
            self.log = (self.root / 'journal.jsonl').open('xb')
            self.log.flush()
            os.fsync(self.log.fileno())
            sync_directory(self.root)
            self.event('CONSUMED', claim)
        except BaseException:
            self.abandon()  # Stale lock/claim deliberately remain.
            raise

    def event(self, kind, record):
        require(not self.closed and not self.ended and not self.poisoned, 'closed/ended/interrupted journal cannot append')
        self.poisoned = True
        core = {'seq': self.seq + 1, 'previous': self.head, 'type': kind,
                'monotonic_ns': time.monotonic_ns(), 'utc_ns': time.time_ns(), 'record': record}
        row = {**core, 'sha256': sha(canonical(core))}
        encoded = canonical(row) + b'\n'
        exclusive(self.root / 'witnesses' / f'{row["seq"]:08d}.json', encoded)
        self.log.write(encoded)
        self.log.flush()
        os.fsync(self.log.fileno())
        self.seq, self.head = row['seq'], row['sha256']
        self.ended = kind == 'CAPTURE_END'
        self.poisoned = False

    def chunk(self, channel, data, received_ns, after_raw=None):
        stream = self.files[channel]
        offset = stream.tell()
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
        if after_raw is not None:
            after_raw()  # Private offline crash-injection seam, never a parser.
        self.event('CHUNK', {'channel': channel, 'offset': offset, 'length': len(data),
                             'sha256': sha(data), 'received_monotonic_ns': received_ns})

    def seal(self, receipt):
        self.event('CAPTURE_END', receipt)
        # A crash between the witnessed end and receipt remains incomplete.
        exclusive(self.root / 'receipt.json', canonical({'head': self.head, 'receipt': receipt}))
        self.abandon()
        require(audit(self.root)['status'] == 'SEALED_BYTES_VERIFIED', 'unreconciled capture cannot release registry')
        # A STOP never releases the registry for another command. Incomplete
        # cleanup requires operator review, not merely an archived receipt.
        if receipt['outcome'] == 'LOCAL_CAPTURE_COMPLETE' and receipt['drain_complete']:
            self.lock.unlink()
            sync_directory(self.registry)

    def abandon(self):
        for stream in list(self.files.values()) + ([self.log] if hasattr(self, 'log') else []):
            stream.close()
        self.closed = True


def audit(directory):
    """Never rewrites an interrupted tail, missing receipt, witness or lock."""
    root = Path(directory)
    binding = json.loads(P.read_bytes(root / 'binding.json'))
    approval = json.loads(P.read_bytes(root / 'approval.json'))
    claim = json.loads(P.read_bytes(root / 'claim.json'))
    require(str(root.absolute()) == binding['capture_path'] == claim['capture_path'], 'capture moved/cloned')
    require(claim['binding_sha256'] == sha(canonical(binding)) and claim['approval_sha256'] == sha(canonical(approval)), 'claim binding changed')
    require(P.read_bytes(Path(binding['audit_root']) / (binding['reservation_id'] + '.json')) == canonical(claim), 'external reservation witness changed')
    raw = {c: P.read_bytes(root / (c + '.bin')) for c in ('stdout', 'stderr')}
    journal = P.read_bytes(root / 'journal.jsonl')
    offsets = {'stdout': 0, 'stderr': 0}
    from .admission import Window, VERSION as MONITOR_VERSION
    monitor = Window(binding) if 'admission_contract' in binding else None
    monitor_failed = False
    eof, head, rows = set(), '0' * 64, []
    kinds = set(('CONSUMED', 'LAUNCH_INTENT', 'SPAWN_FAILED', 'SPAWNED', 'CHUNK',
                 'EOF', 'OS_EXIT', 'READ_ERROR', 'STOP_TRIGGER', 'CANCEL', 'CAPTURE_END', 'INTERRUPTED', 'MONITOR'))
    counts = {}
    lines = journal.splitlines(keepends=True)
    partial = bool(journal and not journal.endswith(b'\n'))
    for line in lines[:-1] if partial else lines:
        row = json.loads(line)
        core = {k: v for k, v in row.items() if k != 'sha256'}
        require(row['seq'] == len(rows) + 1 and row['previous'] == head and row['sha256'] == sha(canonical(core)), 'journal chain changed')
        require(P.read_bytes(root / 'witnesses' / f'{row["seq"]:08d}.json') == line, 'journal witness changed')
        require(row['type'] in kinds and not counts.get('CAPTURE_END'), 'unsupported journal state')
        counts[row['type']] = counts.get(row['type'], 0) + 1
        if row['type'] in ('CONSUMED', 'LAUNCH_INTENT', 'SPAWNED', 'SPAWN_FAILED', 'OS_EXIT'):
            require(counts[row['type']] == 1, 'duplicate launch/consumption/exit')
        if not rows:
            require(row['type'] == 'CONSUMED' and row['record'] == claim, 'consumed intent missing')
        kind = row['type']
        if kind == 'MONITOR':
            require(monitor is not None, 'unbound monitoring evidence')
            r = row['record']
            require(set(r) == {'schema', 'kind', 'now', 'data'} and r['schema'] == MONITOR_VERSION, 'monitor journal scope')
            if r['kind'] == 'ATTACH':
                spawned = next((x['record'] for x in rows if x['type'] == 'SPAWNED'), None)
                require(spawned is not None and r['data'] == spawned, 'monitor process differs from collector')
            if r['kind'] == 'ADMIT':
                require(counts.get('LAUNCH_INTENT') == 1 and not counts.get('SPAWNED'), 'monitor admission order')
            if r['kind'] == 'DRAINED':
                require(counts.get('OS_EXIT') == 1 and eof == set(offsets), 'monitor cooldown before exit/EOF')
            if r['kind'] == 'SAMPLE':
                require(r['data'].get('local_exit_observed') is bool(counts.get('OS_EXIT')), 'monitor exit contradicts OS evidence')
            try:
                monitor.step(r['kind'], r['now'], r['data'])
            except Exception:
                monitor_failed = True  # Invalid observations are retained, and can seal only a STOP.
        if kind in ('SPAWNED', 'SPAWN_FAILED'):
            require(counts.get('LAUNCH_INTENT') == 1 and not (counts.get('SPAWNED') and counts.get('SPAWN_FAILED')), 'spawn has no unique launch intent')
        if kind in ('CHUNK', 'EOF', 'OS_EXIT', 'READ_ERROR', 'STOP_TRIGGER', 'CANCEL'):
            require(counts.get('SPAWNED') == 1, 'process evidence before spawn')
        if row['type'] == 'CHUNK':
            r = row['record']; c = r['channel']
            require(c in offsets and c not in eof and r['offset'] == offsets[c] and r['length'] > 0, 'chunk sequence/offset invalid')
            require(r['length'] <= binding['limits']['maximum_read_chunk_bytes'], 'read chunk bound exceeded')
            data = raw[c][r['offset']:r['offset'] + r['length']]
            require(len(data) == r['length'] and sha(data) == r['sha256'], 'original bytes changed/truncated')
            offsets[c] += len(data)
        if row['type'] == 'EOF':
            require(row['record']['channel'] in offsets and row['record']['channel'] not in eof, 'invalid/duplicate EOF')
            eof.add(row['record']['channel'])
        head = row['sha256']; rows.append(row)
    require(rows, 'no durable consumed journal; reservation still cannot be retried')
    witnesses = {p.name for p in (root / 'witnesses').iterdir()}
    expected = {f'{i:08d}.json' for i in range(1, len(rows) + 1)}
    tails = {c: len(raw[c]) - offsets[c] for c in offsets}
    incomplete = partial or witnesses != expected or any(tails.values()) or not (root / 'receipt.json').exists()
    receipt = None
    if not incomplete:
        envelope = json.loads(P.read_bytes(root / 'receipt.json'))
        require(rows[-1]['type'] == 'CAPTURE_END' and envelope == {'head': head, 'receipt': rows[-1]['record']}, 'receipt/journal mismatch')
        receipt = envelope['receipt']
        if monitor is not None:
            require(receipt.get('monitor') == {'schema': MONITOR_VERSION, 'fixture': True,
                    'window_id': binding['admission_contract']['window_id'],
                    'complete': receipt['outcome'] == 'LOCAL_CAPTURE_COMPLETE', 'native_launch_enabled': False},
                    'monitor receipt differs')
            if receipt['outcome'] == 'LOCAL_CAPTURE_COMPLETE':
                require(not monitor_failed and monitor.phase == 'COMPLETE', 'false complete observation window')
        require(receipt['raw_sha256'] == {c: sha(raw[c]) for c in raw} and receipt['recorded_bytes'] == {c: len(raw[c]) for c in raw}, 'receipt/raw mismatch')
        require(receipt['eof'] == {c: c in eof for c in raw}, 'receipt EOF mismatch')
        require(counts.get('LAUNCH_INTENT') == 1 and receipt['spawn_attempts'] == 1, 'receipt missing unique launch intent')
        spawned = next((r['record'] for r in rows if r['type'] == 'SPAWNED'), None)
        exit_record = next((r['record'] for r in rows if r['type'] == 'OS_EXIT'), None)
        require(receipt['process'] == spawned, 'receipt process identity mismatch')
        if exit_record:
            require(receipt['returncode'] == exit_record['returncode'], 'receipt exit mismatch')
        if receipt['outcome'] == 'LOCAL_CAPTURE_COMPLETE':
            require(spawned is not None and exit_record is not None and eof == set(offsets), 'false complete process/EOF state')
            expected_stdin = (prepare.HERE / 'request.json').read_bytes()
            require(binding['stdin_sha256'] == sha(expected_stdin) and receipt['stdin'] == {
                'completed': True, 'bytes_written': len(expected_stdin), 'error': None}, 'false complete stdin state')
            require(receipt['drain_complete'] is True and receipt['truncated'] is False and
                    not receipt['stop_reasons'] and not counts.get('STOP_TRIGGER') and not counts.get('INTERRUPTED') and
                    not receipt['read_errors'] and not any(receipt['discarded_after_io_trigger_bytes'].values()), 'false complete cleanup state')
            require(not counts.get('CANCEL') and not receipt['cancellations'] and
                    0 <= receipt['observed_wall_seconds_through_receipt'] <= binding['limits']['watchdog_seconds'] and
                    sum(len(v) for v in raw.values()) < binding['limits']['combined_recording_io_trigger_bytes'], 'false complete resource state')
        else:
            require(receipt['outcome'] == 'STOP_EVIDENCE_RETAINED' and receipt['stop_reasons'], 'unknown/unsupported capture outcome')
    return {'status': 'INTERRUPTED_EVIDENCE_RETAINED' if incomplete else 'SEALED_BYTES_VERIFIED',
            'head': head, 'unindexed_tail_bytes': tails, 'receipt': receipt,
            'registry_lock_present': (Path(binding['audit_root']) / '.lock').exists(),
            'reservation_consumed': True, 'native_semantics': 'UNKNOWN', 'provider_requests': 'UNKNOWN'}
