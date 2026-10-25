"""Additive campaign projection over references, never a second scientific ledger."""
from functools import wraps

from src.research.operator.guard import offline
from . import VERSION, SOURCE_REQUEST, BANNER
from . import native as N, records as R


def guarded(write=False):
    def decorate(fn):
        @wraps(fn)
        def call(self, *args, **kwargs):
            R.path(self.root)
            with offline([self.root] if write else []):
                return fn(self, *args, **kwargs)
        return call
    return decorate


def create(base, campaign_id, api_cap_micro_usd=None):
    root = R.locate(base, campaign_id)
    with offline([R.path(base)]):
        R.create(base, campaign_id, api_cap_micro_usd)
    return Campaign(root)


class Campaign:
    def __init__(self, root):
        self.root = R.path(root)
        R.need(self.root.parent.name == 'campaign-v1', 'expected a campaign-v1 directory')
        R.identifier(self.root.name)
        self.journal = R.Journal(self.root)

    def load(self):
        events = self.journal.load()
        m = R.loads(R.read(self.root / 'campaign.json'))
        R.need(m['schema'] == VERSION and m['campaign_id'] == self.root.name
               and R.digest(m) == events[0]['record']['manifest_sha256'] and m['authorises'] == [], 'campaign manifest changed')
        branches, activities = {}, {}
        for e in events[1:]:
            r = e['record']
            if e['type'] == 'BRANCH_ADDED':
                bid = R.identifier(r['branch_id'])
                R.need(bid not in branches, 'duplicate branch event')
                R.need(not any((b['archive'], b['idea_id'], b['version']) == (r['archive'], r['idea_id'], r['version'])
                               for b in branches.values()), 'same card registered twice')
                branches[bid] = r
            elif e['type'] == 'ACTIVITY_ATTACHED':
                aid = R.identifier(r['activity_id'])
                R.need(r['branch_id'] in branches and aid not in activities, 'duplicate activity or unknown branch')
                R.need(not any(a['observation']['run_id'] == r['observation']['run_id'] for a in activities.values()), 'native run already attached')
                activities[aid] = r
            elif e['type'] == 'ACTIVITY_OBSERVED':
                old = activities.get(r['activity_id'])
                R.need(old is not None and old['branch_id'] == r['branch_id']
                       and old['observation']['run'] == r['observation']['run']
                       and old['observation']['journal_events'] < r['observation']['journal_events'], 'invalid observation transition')
                activities[r['activity_id']] = r
            else:
                raise R.CampaignError('invalid campaign event ordering')
        return m, events, branches, activities

    def mutable(self):
        state = self.load()
        R.need(state[0]['binding'] == N.implementation(), 'IMPLEMENTATION_CHANGED: use pinned code; no drift acceptance or replay here')
        return state

    @guarded(write=True)
    def add_branch(self, branch_id, archive, idea_id, version, card_sha256):
        R.identifier(branch_id)
        R.need(type(version) is int and version > 0, 'positive exact card version required')
        with self.journal.writer():
            _, _, branches, _ = self.mutable()
            record = {'branch_id': branch_id, **N.scout_record(archive, idea_id, version, card_sha256)}
            if branch_id in branches:
                old = branches[branch_id]
                R.need(all(old[k] == record[k] for k in ('archive', 'idea_id', 'version', 'card_sha256')), 'branch identity is immutable')
                return False
            R.need(len(branches) < 128, 'campaign branch ceiling reached')
            R.need(not any(b['batch_id'] == record['batch_id'] and b['batch_sha256'] != record['batch_sha256']
                           for b in branches.values()), 'conflicting shared batch identity')
            R.need(not any((b['archive'], b['idea_id'], b['version']) == (record['archive'], idea_id, version)
                           for b in branches.values()), 'same card already registered')
            self.journal.append('BRANCH_ADDED', record)
        return True

    @guarded(write=True)
    def attach(self, branch_id, activity_id, run):
        R.identifier(activity_id)
        with self.journal.writer():
            manifest, _, branches, activities = self.mutable()
            R.need(branch_id in branches, 'unknown branch')
            branch = branches[branch_id]; N.branch_current(branch)
            if activity_id in activities:
                a = activities[activity_id]
                R.need(a['branch_id'] == branch_id and R.path(a['observation']['run']) == R.path(run), 'activity identity conflict')
                observation, _ = N.observe(run, branch, a['observation'])
                R.need(observation == a['observation'], 'native run advanced; use reconcile')
                return False
            observation, _ = N.observe(run, branch)
            R.need(observation['binding'] == manifest['binding']['native'], 'NATIVE_IMPLEMENTATION_CHANGED: use pinned native code')
            R.need(not any(a['observation']['run_id'] == observation['run_id'] for a in activities.values()), 'native run already attached')
            self.journal.append('ACTIVITY_ATTACHED', {'branch_id': branch_id, 'activity_id': activity_id, 'observation': observation})
        return True

    @guarded(write=True)
    def reconcile(self, branch_id=None):
        """Observe new completed native invocations. No native execution, receipt repair or lock removal."""
        results = {}
        with self.journal.writer():
            manifest, _, branches, activities = self.mutable()
            R.need(branch_id is None or branch_id in branches, 'unknown branch')
            for aid, a in sorted(activities.items()):
                if branch_id is not None and branch_id != a['branch_id']:
                    continue
                try:
                    branch = branches[a['branch_id']]; N.branch_current(branch)
                    observation, _ = N.observe(a['observation']['run'], branch, a['observation'])
                    R.need(observation['binding'] == manifest['binding']['native'], 'NATIVE_IMPLEMENTATION_CHANGED: use pinned native code')
                    if observation != a['observation']:
                        R.need(observation['journal_events'] > a['observation']['journal_events'], 'native reference changed without append')
                        self.journal.append('ACTIVITY_OBSERVED', {'branch_id': a['branch_id'], 'activity_id': aid, 'observation': observation})
                        results[aid] = 'OBSERVED_EXISTING_COMPLETION'
                    else:
                        results[aid] = 'UNCHANGED'
                except (ValueError, OSError, KeyError, TypeError) as error:
                    results[aid] = 'RECONCILIATION_REQUIRED: ' + str(error)
        return results

    @guarded()
    def status(self):
        m, events, branches, activities = self.load()
        binding = N.implementation()
        code_changed = binding != m['binding']
        rows = []; batches = {}
        for bid, b in sorted(branches.items()):
            row = {'branch_id': bid, 'hypothesis': {k: b[k] for k in ('archive', 'idea_id', 'version', 'card_sha256', 'fixture')},
                   'stage': 'FORGE', 'execution_state': 'WAITING_FOR_NATIVE_REFERENCE', 'research_outcome': None,
                   'blockers': [], 'pending_decisions': [],
                   'activities': [{'activity_id': aid, **a['observation']} for aid, a in activities.items() if a['branch_id'] == bid],
                   'next_eligible_action': 'ATTACH_COMPLETED_OFFLINE_RUN', 'authorises': []}
            batch = batches.setdefault(b['batch_id'], {'batch_id': b['batch_id'], 'batch_sha256': b['batch_sha256'], 'branches': [], 'archives': []})
            R.need(batch['batch_sha256'] == b['batch_sha256'], 'conflicting shared batch identity')
            batch['branches'].append(bid)
            if b['archive'] not in batch['archives']:
                batch['archives'].append(b['archive'])
            try:
                current = N.branch_current(b)
                row['scout_route'], row['scout_handoff_eligible'] = current['route'], current['handoff_eligible']
                for aid, a in activities.items():
                    if a['branch_id'] != bid:
                        continue
                    old = a['observation']
                    observed, rep = N.observe(old['run'], b, old)
                    if observed != old:
                        raise R.CampaignError('native run advanced; reconcile retained completion')
                    boundary = rep['first_boundary']
                    row.update(stage=boundary['stage'] if boundary else 'OFFLINE_BOUNDARY', execution_state=rep['outcome'],
                               blockers=rep['research_blockers'] + rep['software_blockers'],
                               pending_decisions=rep.get('human_action_groups', rep.get('human_decisions', [])),
                               next_eligible_action='SUPPLY_NATIVE_INPUT_OR_REVIEW' if boundary else 'NO_AUTHORISED_DOWNSTREAM_ACTION')
                    if old['binding'] != binding['native']:
                        raise R.CampaignError('NATIVE_IMPLEMENTATION_CHANGED: retain original native records and use pinned interpreter')
            except (ValueError, OSError, KeyError, TypeError) as error:
                row.update(execution_state='RECONCILIATION_REQUIRED', next_eligible_action='RECONCILE_RETAINED_REFERENCE')
                row['blockers'].append(str(error))
            if code_changed:
                row.update(execution_state='IMPLEMENTATION_CHANGED', next_eligible_action='REVIEW_PINNED_IMPLEMENTATION')
                row['blockers'].append('Campaign implementation binding changed; mutations refused.')
            row['provisional_source'] = {'request_contract': SOURCE_REQUEST, 'implemented': False, 'dispatch_eligible': False,
                                         'requires_scout_ready': False, 'next': 'REQUEST_SEPARATE_PROVISIONAL_SOURCE_AUTHORITY',
                                         'required': ['EXACT_CARD_AND_DECISIVE_QUESTION', 'OWNER_SCOPE', 'HISTORICAL_STOPS', 'COMPONENT_RESERVATION']}
            rows.append(row)
        return {'schema': VERSION + '_STATUS', 'banner': BANNER, 'campaign_id': m['campaign_id'],
                'journal_head': events[-1]['hash'], 'journal_events': len(events), 'locked': self.journal.lock.exists(),
                'implementation_changed': code_changed, 'branches': rows,
                'budgets': {'campaign_api_allocation_micro_usd': m['api_allocation_micro_usd'], 'campaign_external_dispatches': 0,
                            'component_actual_charges': 'UNKNOWN', 'component_batches': sorted(batches.values(), key=lambda b: b['batch_id']),
                            'rule': 'Shared Forge batches referenced once. Allocation is not component spending; no costs summed or reservations released.'},
                'authorises': []}


def markdown(rep):
    out = [f"# Campaign {rep['campaign_id']}", '', f"> {BANNER}", '',
           f"Journal `{rep['journal_head']}` ({rep['journal_events']} events).", '',
           '| Branch | Exact card | Stage | Execution state | Research outcome |', '|---|---|---|---|---|']
    for b in rep['branches']:
        h = b['hypothesis']
        out.append(f"| {b['branch_id']} | {h['idea_id']} v{h['version']} | {b['stage']} | {b['execution_state']} | NOT_ESTABLISHED |")
    for b in rep['branches']:
        out += ['', f"## {b['branch_id']}", '', f"Card SHA-256: `{b['hypothesis']['card_sha256']}`.", '',
                f"Next: {b['next_eligible_action']}.", '']
        out += [f'- Blocker: {x}' for x in b['blockers']]
        out += [f'- Pending human action group: {x}' for x in b['pending_decisions']]
        out += ['- Provisional source investigation is not implemented or authorised; Scout READY is not fabricated.']
    out += ['', 'Campaign allocation and native component budgets remain separate. Shared Forge batches: '
            + str(len(rep['budgets']['component_batches'])) + '. Actual component charges: UNKNOWN.', '',
            'This final view does not close a campaign, approve research or establish an empirical result.', '']
    return '\n'.join(out)
