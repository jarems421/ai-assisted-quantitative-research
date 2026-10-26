"""Append-only source references beside, never inside, the original campaign ledger."""
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

from src.research.campaign_v1 import campaign as C, native as N, records as R
from src.research.operator.guard import offline
from src.research.source_v1 import retrieve as source, store as S, contracts as K
from . import VERSION, REFERENCE


def implementation():
    return {'companion': R.digest({p.name: N.sha(p.read_bytes().replace(b'\r\n', b'\n'))
                                   for p in sorted(Path(__file__).parent.glob('*.py'))}),
            'campaign': N.implementation(), 'source_verifier': S.implementation()}


def anchor(campaign):
    m, events, branches, activities = campaign.load()
    return {'root': str(campaign.root), 'campaign_id': m['campaign_id'],
            'manifest_sha256': N.sha(R.read(campaign.root / 'campaign.json')),
            'creation_hash': events[0]['hash']}, branches, activities


def guarded(write=False):
    def decorate(fn):
        @wraps(fn)
        def call(self, *args, **kwargs):
            with offline([self.root.parent if write == 'create' else self.root] if write else []):
                return fn(self, *args, **kwargs)
        return call
    return decorate


def observe_source(base, attempt_id, branch, campaign_id):
    """Native verification owns receipt/body/result integrity; no acquisition API is called."""
    base, attempt_id = R.path(base), R.identifier(attempt_id)
    root, attempt = source.directories(base, attempt_id)
    R.path(attempt)
    names = ['request.json', 'journal.jsonl']
    if (attempt / 'finalisation.json').exists():
        names.append('finalisation.json')
    before = {n: N.sha(R.read(attempt / n)) for n in names}
    state, result, notes = source.verify(base, attempt_id)
    R.need(state in K.STATUSES and result is not None and not notes, f'source state {state}: verified finalisation/result required')
    names.append('result.json')
    before['result.json'] = N.sha(R.read(attempt / 'result.json'))
    R.need(not (attempt / 'attempt.lock').exists() or 'finalisation.json' in names,
           'source attempt locked without verified finalisation')
    request = K.parse(R.read(attempt / 'request.json'), 'request')
    current = N.branch_current(branch)
    subject = {'archive_sha256': N.sha(R.read(Path(branch['archive']) / 'scout.jsonl')),
               'card_id': branch['idea_id'], 'card_version': branch['version'], 'card_sha256': branch['card_sha256']}
    R.need(request['campaign_id'] == campaign_id and request['branch_id'] == branch['branch_id'], 'source belongs to another campaign/branch')
    R.need(request['subject'] == subject, 'source Scout archive/card/version/hash mismatch')
    R.need(result['implementation_sha256'] == S.implementation(), 'SOURCE_IMPLEMENTATION_CHANGED_OR_UNBOUND')
    R.need(result['request_sha256'] == before['request.json'] and result['status'] == state and result['authorises'] == [],
           'source result identity mismatch')
    events, tail = S.Journal(attempt / 'journal.jsonl').prefix()
    receipts = []
    for index, sha, receipt in source.receipts_of(attempt, events):
        receipts.append({'path': f'receipts/{index:03d}.json', 'sha256': sha,
                         'body_sha256': receipt['body_sha256'], 'coverage': receipt['coverage'],
                         'started_at': receipt['started_at'], 'finished_at': receipt['finished_at'],
                         'termination': receipt['termination'], 'limitations': receipt['limitations']})
    # Re-verify after reading metadata, then recheck the exact native anchors.
    R.need(source.verify(base, attempt_id) == (state, result, notes), 'source changed during inspection')
    R.need(before == {n: N.sha(R.read(attempt / n)) for n in names}, 'source anchors changed during inspection')
    return {'schema': REFERENCE, 'campaign_id': campaign_id, 'branch_id': branch['branch_id'],
            'hypothesis': {'archive': branch['archive'], **subject, 'scout_head': current['scout_head']},
            'source_base': str(base), 'request_id': request['request_id'], 'attempt_id': attempt_id,
            'request_sha256': before['request.json'], 'result_sha256': before['result.json'],
            'implementation_sha256': result['implementation_sha256'], 'status': state,
            'scope_sha256': result['scope_sha256'],
            'reservation_ref': {'request_sha256': before['request.json'], 'field': 'resources.reservation'},
            'journal': {'sha256': before['journal.jsonl'], 'events': len(events),
                        'head': events[-1]['hash'] if events else None, 'incomplete_tail': bool(tail),
                        'last_recorded_at': events[-1]['at'] if events else None},
            'finalisation_sha256': before.get('finalisation.json'), 'receipts': receipts, 'authorises': []}, result


class Companion:
    def __init__(self, campaign_root):
        self.campaign = C.Campaign(campaign_root)
        self.root = R.path(self.campaign.root.parent.parent / 'campaign-evidence-v1' / self.campaign.root.name)
        self.journal = S.Journal(self.root / 'events.jsonl')

    @contextmanager
    def writer(self):
        self.root.mkdir(parents=True, exist_ok=True)
        lock = self.root / 'companion.lock'
        R.need(S.acquire(lock, {'campaign': self.campaign.root.name}), 'companion locked; owner reconciliation required')
        try:
            yield
        finally:
            S.release(lock)

    @guarded(write='create')
    def create(self):
        R.need(not self.root.exists(), 'companion already exists; never repair/recreate')
        self.campaign.mutable()
        a, _, _ = anchor(self.campaign)
        manifest = {'schema': VERSION, 'campaign': a, 'binding': implementation(), 'authorises': []}
        with self.writer():
            S.write_new(self.root / 'companion.json', manifest)
            self.journal.append('CREATED', {'manifest_sha256': R.digest(manifest)})
        return self

    def load(self, mutable=False):
        R.need(not self.root.is_symlink(), 'linked companion refused')
        raw = R.read(self.journal.file)
        R.need(raw.endswith(b'\n'), 'incomplete companion journal; never repair')
        events = self.journal.load()
        R.need(raw == R.read(self.journal.file), 'companion changed during inspection')
        manifest = R.loads(R.read(self.root / 'companion.json'))
        a, branches, native = anchor(self.campaign)
        R.need(manifest['schema'] == VERSION and manifest['campaign'] == a and manifest['authorises'] == []
               and events and events[0]['type'] == 'CREATED'
               and events[0]['record'] == {'manifest_sha256': R.digest(manifest)}, 'companion/campaign identity changed')
        attached = {}
        for e in events[1:]:
            r = e['record']
            R.need(e['type'] == 'SOURCE_ATTACHED' and set(r) == {'activity_id', 'reference'}, 'invalid companion event')
            aid, ref = R.identifier(r['activity_id']), r['reference']
            R.need(aid not in attached and ref['schema'] == REFERENCE and ref['campaign_id'] == a['campaign_id']
                   and ref['branch_id'] in branches and ref['authorises'] == [], 'invalid source attachment')
            R.need(not any(x['attempt_id'] == ref['attempt_id']
                           for x in attached.values()), 'duplicate native source identity')
            attached[aid] = ref
        if mutable:
            self.campaign.mutable()
            R.need(manifest['binding'] == implementation(), 'IMPLEMENTATION_CHANGED; pinned companion required')
        return manifest, events, branches, native, attached

    @guarded(write=True)
    def attach(self, branch_id, activity_id, source_base, attempt_id):
        R.identifier(activity_id)
        R.need(self.root.is_dir(), 'companion not created')
        with self.writer():
            _, _, branches, native, attached = self.load(mutable=True)
            R.need(branch_id in branches and activity_id not in native, 'unknown branch or native activity identity conflict')
            ref, _ = observe_source(source_base, attempt_id, branches[branch_id], self.campaign.root.name)
            if activity_id in attached:
                R.need(attached[activity_id] == ref, 'source activity identity/content conflict')
                return False
            R.need(len(attached) < 128, 'source reference ceiling reached')
            R.need(not any(x['attempt_id'] == ref['attempt_id']
                           for x in attached.values()), 'source attempt already attached')
            self.journal.append('SOURCE_ATTACHED', {'activity_id': activity_id, 'reference': ref})
        return True

    def checkpoint(self):
        from .checkpoint import render
        # The original public method owns its own offline context; never nest it.
        campaign = self.campaign.status()
        with offline([]):
            return render(self, campaign)

    @guarded()
    def check_source(self, branch_id, source_base, attempt_id):
        """Read-only admission diagnostic, including unattachable interrupted attempts."""
        _, _, branches, _, _ = self.load(mutable=True)
        R.need(branch_id in branches, 'unknown branch')
        native = source.status(R.path(source_base), R.identifier(attempt_id))
        try:
            ref, _ = observe_source(source_base, attempt_id, branches[branch_id], self.campaign.root.name)
            return {'attachment_eligible': True, 'reference': ref, 'native': native, 'dispatch_eligible': False, 'authorises': []}
        except (ValueError, OSError, KeyError, TypeError) as error:
            return {'attachment_eligible': False, 'native': native, 'problem': str(error), 'dispatch_eligible': False, 'authorises': []}
