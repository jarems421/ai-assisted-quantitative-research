"""Bounded local IO and immutable, hash-chained scout records. No authority writes."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path

from src.research.spec import canonical, digest
from .schema import ScoutError, json_loads, utc_now

ROOT = Path(__file__).resolve().parents[3]
MAX_BYTES = 12 * 1024 * 1024
MAX_INPUT = 1024 * 1024
GENESIS = '0' * 64


def unlinked(path):
    p = Path(path).absolute()
    for part in (p, *p.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ScoutError('symlink/junction paths are refused')
    return p


def input_json(path):
    p = unlinked(path)
    lowered = [x.lower() for x in p.parts]
    if p.suffix.lower() != '.json' or any(x in ('.git', 'keys') or x.startswith(('.env', 'graph_pilot')) for x in lowered):
        raise ScoutError('only explicit safe local JSON inputs are accepted; pilot/private paths are forbidden')
    if any(a == 'data' and b == 'raw' for a, b in zip(lowered, lowered[1:])):
        raise ScoutError('private raw archives are never opened by Scout')
    if not p.is_file() or p.stat().st_size > MAX_INPUT: raise ScoutError('input must be a regular JSON file at most 1 MiB')
    return json_loads(p.read_text(encoding='utf-8'))


class Archive:
    def __init__(self, directory):
        self.path = unlinked(directory)
        nearest_repo = next((p for p in (self.path, *self.path.parents) if (p / '.git').exists()), None)
        if nearest_repo is not None and nearest_repo.resolve() != ROOT:
            raise ScoutError('Scout cannot read/write an archive inside another repository or worktree')
        if self.path.resolve().is_relative_to(ROOT):
            rel = self.path.resolve().relative_to(ROOT).as_posix()
            if not (rel == '.research/opportunity_scout' or rel.startswith('.research/opportunity_scout/')):
                raise ScoutError('within the repository, Scout writes only under .research/opportunity_scout/')
        self.file = self.path / 'scout.jsonl'

    @contextmanager
    def locked(self):
        unlinked(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        lock = self.path / '.append.lock'
        try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error: raise ScoutError('archive locked; do not remove another writer\'s lock') from error
        try: yield
        finally:
            os.close(fd)
            lock.unlink()

    def load(self):
        from .engine import State, apply
        s = State()
        unlinked(self.file)
        if not self.file.exists(): return s
        if self.file.stat().st_size > MAX_BYTES or self.file.stat().st_nlink != 1: raise ScoutError('unsafe or oversized archive')
        previous = GENESIS
        text = self.file.read_text(encoding='utf-8')
        if text and not text.endswith('\n'): raise ScoutError('incomplete final event; refuse append until reviewed')
        for index, line in enumerate(text.splitlines()):
            if index >= 2000: raise ScoutError('archive event ceiling reached')
            event = json_loads(line)
            if set(event) != {'seq', 'type', 'recorded_at', 'previous', 'record', 'hash'}: raise ScoutError('invalid event envelope')
            core = {k: v for k, v in event.items() if k != 'hash'}
            if event['seq'] != index + 1 or event['previous'] != previous or digest(core) != event['hash']:
                raise ScoutError('archive chain mismatch')
            if s.events and event['recorded_at'] < s.events[-1]['recorded_at']: raise ScoutError('recording time cannot move backwards')
            apply(s, event['type'], event['record'], event['recorded_at'])
            s.events.append(event); previous = event['hash']
        return s

    def append(self, kind, record, *, recorded_at=None):
        return self.append_many([(kind, record)], recorded_at=recorded_at)

    def append_many(self, records, *, recorded_at=None):
        from .engine import apply
        with self.locked():
            s = self.load()
            lines = []
            for kind, record in records:
                moment = recorded_at or utc_now()
                if s.events and moment < s.events[-1]['recorded_at']: raise ScoutError('recording time cannot move backwards')
                apply(s, kind, record, moment)
                core = {'seq': len(s.events) + 1, 'type': kind, 'recorded_at': moment,
                        'previous': s.events[-1]['hash'] if s.events else GENESIS, 'record': record}
                event = {**core, 'hash': digest(core)}
                s.events.append(event); lines.append(canonical(event) + b'\n')
            if len(s.events) > 2000 or sum(map(len, lines)) + (self.file.stat().st_size if self.file.exists() else 0) > MAX_BYTES:
                raise ScoutError('archive ceiling reached')
            with self.file.open('ab') as handle:
                for line in lines: handle.write(line)
                handle.flush(); os.fsync(handle.fileno())
        return s

    def export(self, name, value):
        if not name.endswith('.json') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. ' for c in name):
            raise ScoutError('export name must be a simple .json filename')
        target = unlinked(self.path / 'exports' / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle: handle.write(canonical(value) + b'\n')
        return target
