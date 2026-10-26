"""Bounded, create-only metadata and a single-writer, fsynced event journal.

Trusted local filesystem / reviewed code, like the offline operator; not an OS sandbox.
Interrupted writes and leftover locks are refused, never silently repaired or removed.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from src.research.operator.runs import check_base
from src.research.spec import canonical, digest
from . import VERSION

MAX_BYTES = 16 * 1024 * 1024
EVENTS = {'CREATED', 'BRANCH_ADDED', 'ACTIVITY_ATTACHED', 'ACTIVITY_OBSERVED'}


class CampaignError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise CampaignError(message)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def identifier(value):
    need(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value), 'invalid identifier')
    return value


def path(value):
    p = Path(value).absolute()
    need('..' not in p.parts, 'path traversal refused')
    need(not str(p).startswith(('\\\\', '//')), 'network paths refused')
    for part in (p, *p.parents):
        need(not part.is_symlink() and not (hasattr(part, 'is_junction') and part.is_junction()), 'linked path refused')
    blocked = {'.git', '.env', '.ssh', '.aws', '.azure', '.claude', '.claude-research', '.codex', '.config', '.netrc', 'keys', 'raw'}
    need(not any(x.lower() in blocked or x.lower().startswith(('.env.', '.claude.')) for x in p.parts), 'private/raw path refused')
    return p


def read(value):
    p = path(value)
    need(p.is_file() and p.stat().st_nlink == 1 and p.stat().st_size <= MAX_BYTES, 'missing, linked or oversized record')
    need(p.suffix in ('.json', '.jsonl', '.md', '.txt'), 'metadata files only')
    return p.read_bytes()


def loads(raw):
    def pairs(items):
        d = {}
        for k, v in items:
            need(k not in d, 'duplicate JSON key')
            d[k] = v
        return d
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: need(False, 'nonfinite JSON'))


class Journal:
    def __init__(self, directory, clock=now):
        self.root, self.clock = path(directory), clock
        self.file = self.root / 'events.jsonl'
        self.lock = self.root / 'campaign.lock'

    @contextmanager
    def writer(self):
        path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path(self.lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise CampaignError('campaign locked; interrupted writer requires owner reconciliation') from error
        try:
            yield
        finally:
            os.close(fd)
            self.lock.unlink()

    def load(self):
        raw = read(self.file)
        need(raw.endswith(b'\n'), 'incomplete journal: retain bytes and reconcile; never repair')
        events, previous = [], '0' * 64
        for seq, line in enumerate(raw.splitlines()):
            e = loads(line)
            need(set(e) == {'seq', 'type', 'at', 'previous', 'record', 'hash'}, 'invalid event envelope')
            need(e['seq'] == seq and e['type'] in EVENTS and e['previous'] == previous
                 and digest({k: v for k, v in e.items() if k != 'hash'}) == e['hash'], 'campaign chain changed')
            need(not events or e['at'] >= events[-1]['at'], 'campaign time moved backwards')
            previous = e['hash']; events.append(e)
        need(events and events[0]['type'] == 'CREATED', 'missing campaign creation')
        return events

    def append(self, kind, record, *, create=False):
        events = [] if create else self.load()
        need(kind in EVENTS, 'unknown event')
        moment = self.clock()
        need(not events or moment >= events[-1]['at'], 'campaign time moved backwards')
        core = {'seq': len(events), 'type': kind, 'at': moment,
                'previous': events[-1]['hash'] if events else '0' * 64, 'record': record}
        data = canonical({**core, 'hash': digest(core)}) + b'\n'
        need(len(data) + (self.file.stat().st_size if self.file.exists() else 0) <= MAX_BYTES, 'campaign journal full')
        with path(self.file).open('xb' if create else 'ab') as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())


def locate(base, campaign_id):
    return path(check_base(path(base)) / 'campaign-v1' / identifier(campaign_id))


def create(base, campaign_id, api_cap_micro_usd=None):
    from .native import implementation
    need(api_cap_micro_usd is None or type(api_cap_micro_usd) is int and api_cap_micro_usd >= 0, 'invalid campaign allocation')
    root = locate(base, campaign_id)
    need(not root.exists(), 'campaign already exists; never overwrite')
    j = Journal(root)
    manifest = {'schema': VERSION, 'campaign_id': campaign_id, 'api_allocation_micro_usd': api_cap_micro_usd,
                'scope': 'OFFLINE_NATIVE_REFERENCE_CONTINUITY_ONLY', 'binding': implementation(), 'authorises': []}
    with j.writer():
        with (root / 'campaign.json').open('xb') as handle:
            handle.write(canonical(manifest) + b'\n'); handle.flush(); os.fsync(handle.fileno())
        j.append('CREATED', {'manifest_sha256': digest(manifest)}, create=True)
    return root
