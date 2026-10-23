"""Observe metadata and one harmless child; never launch Claude or auth commands.

Administrator watch.ps1 is a separate, bounded producer. This reader is normal-user
only. Success is local observer preparation, never N1 admission/account approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ..storage import ROOT, unlinked
from ..v004_monitoring import account_metadata, compare_metadata
from ..schema import json_loads

VERSION = 'SCOUT_N1_PROCESS_OBSERVER_V003'
DIRECTORY = ROOT / '.research/opportunity_scout/n1-admin-observer-v003'
CHILD = ROOT / 'tests/fixtures/scout_n1_observer_child.py'
MAX_BYTES = 2 * 1024 * 1024
IS_WINDOWS = os.name == 'nt'


class Refused(ValueError):
    pass


def require(value, message):
    if not value:
        raise Refused(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Stream:
    """Checks exact producer bytes/sequence and detects visible contamination.

    No provider IDs, ancestry guarantees or WMI losslessness are invented. Event
    TIME_CREATED is an event timestamp, not a queried process creation identity.
    """
    def __init__(self):
        self.tail = b''
        self.total = 0
        self.seq = 0
        self.previous = '0' * 64
        self.elapsed = 0
        self.heartbeat = None
        self.snapshot = False
        self.ended = False
        self.starts = {}
        self.exits = set()
        self.pending_ack = None

    def feed(self, data):
        require(not self.ended or not data, 'trailing bytes after END')
        self.total += len(data)
        require(self.total <= MAX_BYTES, 'observer recording limit')
        self.tail += data
        while b'\n' in self.tail:
            line, self.tail = self.tail.split(b'\n', 1)
            require(not self.ended, 'trailing record after END')
            try:
                frame = json_loads(line.decode('utf-8'))
                require(set(frame) == {'record', 'sha256'} and isinstance(frame['record'], str), 'invalid frame')
                digest = sha(frame['record'].encode('utf-8'))
                require(frame['sha256'] == digest, 'changed observer bytes')
                record = json_loads(frame['record'])
                require(set(record) == {'seq', 'previous', 'elapsed_ms', 'kind', 'data'}, 'invalid record')
                require(type(record['seq']) is int and record['seq'] == self.seq + 1 and record['previous'] == self.previous, 'observer sequence/hash chain')
                require(type(record['elapsed_ms']) is int and record['elapsed_ms'] >= self.elapsed, 'observer time reversed')
                self._record(record)
                self.seq, self.previous, self.elapsed = record['seq'], digest, record['elapsed_ms']
            except Refused:
                raise
            except (ValueError, TypeError, KeyError) as error:
                raise Refused('invalid/contaminated observer record') from error

    def _record(self, record):
        kind, data = record['kind'], record['data']
        require(isinstance(data, dict), 'invalid event data')
        if self.pending_ack is not None:
            require(kind == 'QUEUE_ACK', 'persisted event missing exact acknowledgement')
        if kind == 'QUEUE_ACK':
            require(self.pending_ack is not None and data == self.pending_ack, 'unmatched queue acknowledgement')
            self.pending_ack = None
            return
        if not self.seq:
            require(kind == 'HEADER' and data.get('schema') == VERSION and data.get('claude_invocations') == 0, 'observer header required')
            return
        if kind == 'SNAPSHOT':
            require(not self.snapshot and isinstance(data.get('processes'), list), 'initial snapshot required once')
            for process in data['processes']:
                self._process(process, initial=True)
            self.snapshot = True
        elif kind == 'START':
            require(self.snapshot, 'snapshot missing')
            self._process(data)
            key = (data['pid'], data['event_filetime'])
            require(key not in self.starts, 'duplicate process start')
            self.starts[key] = data
            self.pending_ack = {'record_seq': record['seq'], 'queue_event_identifier': data['queue_event_identifier']}
        elif kind == 'EXIT':
            require(self.snapshot, 'snapshot missing')
            self._process(data, exiting=True)
            self.exits.add((data['pid'], data['event_filetime'], data['name'].lower()))
            self.pending_ack = {'record_seq': record['seq'], 'queue_event_identifier': data['queue_event_identifier']}
        elif kind == 'HEARTBEAT':
            require(self.snapshot and data == {'subscriptions_present': True}, 'lost subscriptions/snapshot')
            require(self.heartbeat is None or record['elapsed_ms'] - self.heartbeat <= 5000, 'producer heartbeat gap')
            self.heartbeat = record['elapsed_ms']
        elif kind == 'END':
            require(self.snapshot and self.heartbeat is not None and data == {'reason': 'STOP_REQUEST', 'coverage_certified': False}, 'incomplete observer stop')
            self.ended = True
        else:
            raise Refused('unknown/error observer event')

    @staticmethod
    def _process(data, initial=False, exiting=False):
        keys = {'pid', 'name', 'creation_filetime' if initial else 'event_filetime'}
        if not initial:
            keys.add('queue_event_identifier')
        if not exiting:
            keys.add('parent_pid')
        require(isinstance(data, dict) and set(data) == keys, 'process metadata field scope')
        require(type(data['pid']) is int and data['pid'] >= 0, 'process id')
        require(initial or data['pid'] > 0, 'event process id')
        if not exiting:
            require(type(data['parent_pid']) is int and data['parent_pid'] >= 0, 'parent process id')
        require(isinstance(data['name'], str) and len(data['name']) <= 260, 'process name')
        if not initial:
            require(isinstance(data['event_filetime'], str) and data['event_filetime'].isdigit() and int(data['event_filetime']) > 0, 'event timestamp')
            require(type(data['queue_event_identifier']) is int and data['queue_event_identifier'] >= 0, 'local queue identifier')
        require(data['name'].lower() not in ('claude.exe', 'claude'), 'Claude process contaminates window')

    def proof(self, pid, parent, name, earliest_filetime):
        matches = [r for r in self.starts.values() if r['pid'] == pid and r['parent_pid'] == parent and r['name'].lower() == name.lower() and int(r['event_filetime']) >= earliest_filetime]
        require(len(matches) == 1, 'sentinel start/parent/time not independently observed')
        require(any(p == pid and n == name.lower() and int(t) >= int(matches[0]['event_filetime']) for p, t, n in self.exits), 'sentinel exit not independently observed')


def exclusive(path, data):
    with unlinked(path).open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def audit(path):
    stream = Stream()
    path = unlinked(path)
    require(path.is_file() and path.stat().st_size <= MAX_BYTES and path.stat().st_nlink == 1, 'unsafe observer audit input')
    with path.open('rb') as handle:
        while chunk := handle.read(65536):
            stream.feed(chunk)
    require(stream.ended and not stream.tail, 'observer stream incomplete')
    return {'head': stream.previous, 'records': stream.seq, 'bytes': stream.total}


def reader_receipt():
    return {'schema': VERSION, 'status': 'STOP', 'claude_invocations': 0,
            'auth_status_invocations': 0, 'scientific_slots_consumed': 0,
            'account_identity': 'UNKNOWN', 'historical_writer': 'UNKNOWN',
            'N1_admission': False, 'continuous_coverage_certified': False,
            'provider_requests': 'UNKNOWN', 'credential_contents_read': False}


def require_normal_user():
    import ctypes
    require(not ctypes.windll.shell32.IsUserAnAdmin(), 'reader/sentinel must be normal-user, never administrator')


def observe(directory=DIRECTORY):
    """Fixed metadata-only live check. No alternative executable/argv accepted."""
    require(IS_WINDOWS, 'Windows observer only')
    require_normal_user()
    directory = unlinked(directory)
    require(directory == DIRECTORY, 'only the sole fixed observer directory is supported')
    require(directory.is_dir(), 'start the administrator observer first')
    source = unlinked(directory / 'events.jsonl')
    require(source.is_file() and source.stat().st_nlink == 1, 'missing/unsafe observer stream')
    source_identity = (source.stat().st_dev, source.stat().st_ino)
    exclusive(directory / 'reader.claim', b'METADATA_ONLY_NO_CLAUDE_NO_RETRY')
    stream = Stream()
    previous_size = 0
    child = None
    result = reader_receipt()
    started = time.monotonic()
    last_record = started
    last_heartbeat = None
    proof_pid = None
    proof_at = None
    quiet_start = None
    last_tick = started
    metadata_log = None
    metadata_path = unlinked(directory / 'metadata-samples.jsonl')
    metadata_digest = hashlib.sha256()
    metadata_count = 0

    def sample():
        nonlocal metadata_count
        value = account_metadata()
        raw = json.dumps({'seq': metadata_count + 1, 'elapsed_seconds': time.monotonic() - started,
                          'metadata': value}, sort_keys=True).encode('utf-8') + b'\n'
        metadata_log.write(raw)
        metadata_log.flush()
        os.fsync(metadata_log.fileno())
        metadata_digest.update(raw)
        metadata_count += 1
        return value

    try:
        metadata_log = metadata_path.open('xb')
        first = sample()
        with source.open('rb') as handle:
            while time.monotonic() - started < 160:
                tick = time.monotonic()
                require(tick - last_tick <= 5, 'reader sampling gap')
                last_tick = tick
                unlinked(source)
                require(source.stat().st_nlink == 1, 'observer stream links changed')
                require((source.stat().st_dev, source.stat().st_ino) == source_identity, 'observer stream replaced')
                require(source.stat().st_size >= previous_size, 'observer stream truncated')
                require(source.stat().st_size <= MAX_BYTES, 'observer stream oversized')
                chunk = handle.read(65536)
                previous_size = max(previous_size, handle.tell())
                seq = stream.seq
                stream.feed(chunk)
                if stream.seq != seq:
                    last_record = tick
                if stream.heartbeat != last_heartbeat:
                    last_heartbeat = stream.heartbeat
                    heartbeat_seen = tick
                require(tick - last_record <= 5, 'observer stalled/missing records')
                require(not stream.ended, 'observer ended before reader stop')
                if stream.heartbeat is not None:
                    require(tick - heartbeat_seen <= 5, 'observer heartbeat stalled')
                    if quiet_start is None:
                        require(stream.elapsed <= 180000, 'observer startup too old; preserve run and stop')
                        quiet_start = tick
                current = sample()
                require(compare_metadata(first, current)['unchanged_observed_metadata'], 'account metadata drift/unknown; no writer attribution')
                require(time.monotonic() - tick <= 5, 'reader sample gap')
                if quiet_start is not None and tick - quiet_start >= 60 and proof_pid is None:
                    unlinked(CHILD)
                    require(CHILD.read_bytes().replace(b'\r\n', b'\n') == b'"""Fixed, harmless process-start/exit sentinel. No IO, networking or arguments."""\npass\n', 'sentinel bytes changed')
                    proof_at = int((time.time() + 11644473600) * 10000000)
                    env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR') if k in os.environ}
                    child = subprocess.Popen([sys.executable, '-I', str(CHILD)], stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), shell=False)
                    proof_pid = child.pid
                    child.wait(timeout=2)
                    proof_started = tick
                if proof_pid is not None and tick - proof_started >= 5:
                    stream.proof(proof_pid, os.getpid(), Path(sys.executable).name, proof_at)
                    if tick - proof_started >= 60:
                        result['status'] = 'LOCAL_OBSERVER_PREPARATION_COMPLETE_NOT_AUTH_OR_N1'
                        break
                require(not stream.tail or len(stream.tail) <= 512 * 1024, 'incomplete observer line oversized')
                time.sleep(.25)
            else:
                raise Refused('observer preparation watchdog')
            exclusive(directory / 'stop.request', b'STOP_METADATA_OBSERVER')
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not stream.ended:
                stream.feed(handle.read(65536))
                time.sleep(.1)
            require(stream.ended and not stream.tail and not handle.read(1), 'missing END/trailing observer bytes')
        require(compare_metadata(first, sample())['unchanged_observed_metadata'], 'final metadata drift')
        rechecked = audit(source)
        require(rechecked == {'head': stream.previous, 'records': stream.seq, 'bytes': stream.total}, 'observer readback differs')
        result.update(observer_head=stream.previous, observer_records=stream.seq,
                      observer_bytes=stream.total, observed_wall_seconds=time.monotonic() - started,
                      sentinel_start_exit_parent_observed=True, metadata_unchanged_observed=True)
    except BaseException as error:
        result.update(status='STOP', reason=type(error).__name__ + ': ' + str(error) if isinstance(error, Refused) else type(error).__name__)
        if not (directory / 'stop.request').exists():
            exclusive(directory / 'stop.request', b'STOP_METADATA_OBSERVER')
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=2)
    finally:
        if metadata_log is not None:
            metadata_log.close()
            result.update(metadata_samples=metadata_count, metadata_log_sha256=metadata_digest.hexdigest())
            if sha(metadata_path.read_bytes()) != metadata_digest.hexdigest():
                result.update(status='STOP', reason='metadata evidence readback differs')
        # Original event bytes remain untouched. No raw auth output exists.
        exclusive(directory / 'receipt.json', json.dumps(result, sort_keys=True).encode('utf-8'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe-only', action='store_true', required=True)
    parser.parse_args()
    result = observe()
    print(json.dumps(result))
    if result['status'] == 'STOP':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
