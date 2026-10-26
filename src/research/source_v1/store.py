"""Create-only records, exclusive locks and hash-chained append-only journals under <base>/source-v1/.

Assumes a trusted local filesystem and reviewed code; this is not an OS sandbox. Interrupted writes and
leftover locks are refused and reported, never repaired or removed by software.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from src.research.spec import canonical, digest
from src.research.quarry_v1 import io as Q
from .contracts import need, parse

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE = ROOT / '.research'
GENESIS = '0' * 64
MAX_RECORD = 16 * 1024 * 1024
# Code whose behaviour an owner scope binds by hash, in addition to this package.
DEPENDENCIES = ('src/research/quarry_v1/acquisition.py', 'src/research/quarry_v1/contracts.py', 'src/research/quarry_v1/io.py',
                'src/research/jev_navigation_v1/contracts.py', 'src/research/spec.py')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def implementation():
    files = sorted((ROOT / 'src/research/source_v1').glob('*.py')) + [ROOT / name for name in DEPENDENCIES]
    return digest({p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in files})


def records(base=None):
    """The source-v1 directory: inside this checkout only under ignored .research/, never in another checkout."""
    root = Q.safe_path(base if base is not None else DEFAULT_BASE)
    if root.is_relative_to(ROOT):
        need(root.relative_to(ROOT).parts[:1] == ('.research',), 'inside the repository, source records live only under .research/')
    else:
        need(not any((p / '.git').exists() for p in (root, *root.parents)), 'source records cannot be written into another Git checkout')
    return root / 'source-v1'


def read(path, maximum=MAX_RECORD):
    return Q.read(path, maximum)


def load(path, what, maximum=1024 * 1024):
    raw = read(path, maximum)
    return raw, parse(raw, what)


def encode(value):
    return canonical(value) + b'\n'


def write_new(path, value):
    """Create-only, flushed and fsynced. Returns the SHA-256 of the exact bytes written."""
    data = value if isinstance(value, bytes) else encode(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with Q.safe_path(path).open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return sha(data)


def acquire(path, holder):
    """Exclusive lock file naming its holder. False if it already exists; never waits or steals."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(Q.safe_path(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, 'wb') as handle:
        handle.write(encode(holder))
        handle.flush()
        os.fsync(handle.fileno())
    return True


def release(path):
    Path(path).unlink()


def holder(path):
    path = Path(path)
    if not path.exists():
        return None
    try:
        return parse(read(path, 4096), 'lock')
    except ValueError:
        return {'unreadable': True}


class Journal:
    """Single-writer append-only JSONL; the caller holds the governing lock."""

    def __init__(self, file, clock=now):
        self.file, self.clock = Path(file), clock

    def bytes(self):
        return read(self.file) if self.file.exists() else b''

    def load(self):
        events, tail = self.prefix()
        need(not tail, 'incomplete journal tail: retain the bytes and reconcile by hand; never repair')
        return events

    def prefix(self):
        """Verified events of every complete line, plus any incomplete tail bytes (left by an interruption)."""
        if not self.file.exists():
            return [], b''
        raw = read(self.file)
        complete, _, tail = raw.rpartition(b'\n')
        events, previous = [], GENESIS
        for seq, line in enumerate(complete.split(b'\n') if complete else []):
            e = parse(line, 'journal event')
            need(isinstance(e, dict) and set(e) == {'seq', 'type', 'at', 'previous', 'record', 'hash'}, 'invalid journal envelope')
            need(e['seq'] == seq and e['previous'] == previous
                 and digest({k: v for k, v in e.items() if k != 'hash'}) == e['hash'], 'journal chain changed')
            need(not events or e['at'] >= events[-1]['at'], 'journal time moved backwards')
            previous = e['hash']
            events.append(e)
        return events, tail

    def append(self, kind, record):
        events = self.load()
        at = self.clock()
        need(not events or at >= events[-1]['at'], 'clock moved backwards; refusing to append')
        core = {'seq': len(events), 'type': kind, 'at': at, 'previous': events[-1]['hash'] if events else GENESIS, 'record': record}
        event = {**core, 'hash': digest(core)}
        data = encode(event)
        need((self.file.stat().st_size if self.file.exists() else 0) + len(data) <= MAX_RECORD, 'journal full')
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with Q.safe_path(self.file).open('ab') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        return event
