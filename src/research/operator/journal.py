"""Append-only, hash-chained run journal: one JSONL file per run and one exclusive coordinator per invocation.

Events are never rewritten. ``load`` verifies the whole chain, so a hand-edited or truncated journal is refused
rather than trusted. A lock left by an interrupted invocation is never removed automatically: it must be reconciled
by a human, exactly like the Scout and Discovery writer locks."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from src.research.spec import canonical, digest

GENESIS = '0' * 64
EVENTS = ('RUN_CREATED', 'INVOCATION_STARTED', 'INPUTS_SUPPLIED', 'STAGE_STARTED', 'STAGE_FINISHED', 'INVOCATION_FINISHED')
MAX_BYTES = 64 * 1024 * 1024


class JournalError(ValueError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


class Journal:
    def __init__(self, directory, clock=utc_now):
        self.dir, self.clock = Path(directory), clock
        self.file, self.lock = self.dir / 'journal.jsonl', self.dir / 'journal.lock'

    def load(self):
        if not self.file.is_file():
            raise JournalError(f'no run journal at {self.dir}')
        raw = self.file.read_bytes()
        if len(raw) > MAX_BYTES:
            raise JournalError('run journal exceeds its size ceiling')
        if raw and not raw.endswith(b'\n'):
            raise JournalError('incomplete final journal event; retain it and reconcile, never repair')
        events, previous = [], GENESIS
        for index, line in enumerate(raw.splitlines()):
            event = json.loads(line)
            if set(event) != {'seq', 'type', 'at', 'previous', 'record', 'hash'}:
                raise JournalError('invalid journal event envelope')
            core = {k: v for k, v in event.items() if k != 'hash'}
            if event['seq'] != index or event['previous'] != previous or digest(core) != event['hash'] or event['type'] not in EVENTS:
                raise JournalError(f'run journal chain broken at event {index}; it was edited or truncated')
            events.append(event)
            previous = event['hash']
        if not events or events[0]['type'] != 'RUN_CREATED':
            raise JournalError('a run journal begins with RUN_CREATED')
        return events

    @contextmanager
    def writer(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise JournalError('run is locked: another coordinator is active, or an interrupted invocation must be '
                               'reconciled by a human before its lock is removed') from error
        try:
            yield self
        finally:
            os.close(fd)
            self.lock.unlink()

    def append(self, kind, record, *, create=False):
        if kind not in EVENTS:
            raise JournalError('unknown journal event ' + kind)
        events = [] if create else self.load()
        if create and self.file.exists():
            raise JournalError('run journal already exists; runs are never overwritten')
        core = {'seq': len(events), 'type': kind, 'at': self.clock(),
                'previous': events[-1]['hash'] if events else GENESIS, 'record': record}
        event = {**core, 'hash': digest(core)}
        with self.file.open('xb' if create else 'ab') as handle:
            handle.write(canonical(event) + b'\n')
            handle.flush()
            os.fsync(handle.fileno())
        return event
