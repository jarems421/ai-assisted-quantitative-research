"""Append-only, hash-chained Discovery Lab campaign ledger: one JSONL file per campaign.

Records are never rewritten. A changed source, observation, relationship or candidate is a new
version that names what it supersedes and why. Every event stores the hash of its predecessor, and
``load`` replays the whole file through the same rules used at append time, so a hand-edited line,
a silently changed frozen claim or a rule bypass is detected rather than trusted.

Each event replays under the rules version that admitted it. A campaign records its creation
rules; a later event admitted under newer rules carries ``derived.rules``. Untagged events of a
V001 ledger therefore keep V001 semantics, while every new append uses the current rules.
"""
from __future__ import annotations

import copy
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.research.spec import canonical, digest
from src.research.discovery import records as R
from src.research.discovery import review as V

RULES = V.RULES_V002
KNOWN_RULES = (V.RULES_V001, V.RULES_V002)  # oldest first; replay never moves backwards
GENESIS = '0' * 64
ROOT = Path(__file__).resolve().parents[3]


class LedgerError(ValueError):
    """An append or replay that would violate Discovery Lab rules."""


class WriterLockNotReleased(LedgerError):
    """The event IS committed, but its writer lock could not be removed. Never retry the append."""

    def __init__(self, path, lock, event, cause):
        self.path, self.lock, self.seq, self.hash = str(path), str(lock), event['seq'], event['hash']
        super().__init__(f"{Path(path).name}: event {event['seq']} ({event['type']}, hash {event['hash']}) WAS appended, "
                         f'but the writer lock {Path(lock).name} could not be removed ({type(cause).__name__}). '
                         'Do not retry: confirm the ledger head is this hash, then reconcile and remove the lock.')


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class State:
    """Replayed ledger contents. Versioned records keep every version in order."""

    def __init__(self):
        self.campaign = None
        self.versions = {k: {} for k in R.VERSIONED}
        self.derived = {}
        self.freezes = {}
        self.reviews, self.dispositions, self.efforts, self.events = [], [], [], []
        self.entities, self.name_variants = {}, {}
        self.rules, self.admitted = None, {}  # campaign rules; rules that admitted each later event

    @property
    def fixture(self):
        return self.campaign['fixture']

    def latest(self, kind, rid):
        found = self.versions[kind].get(rid)
        return found[-1] if found else None

    def version(self, kind, rid, version=None):
        found = self.versions[kind].get(rid) or []
        if version is None:return found[-1] if found else None
        return found[version - 1] if 0 < version <= len(found) else None

    def frozen(self, cid, version):
        return self.freezes.get((cid, version))

    def latest_rules(self):
        return max([self.rules, *self.admitted.values()], key=KNOWN_RULES.index)

    def ids(self, kind):
        if kind in R.VERSIONED:return set(self.versions[kind])
        return {r['id'] for r in {'review': self.reviews, 'disposition': self.dispositions, 'effort': self.efforts}[kind]}


def core(candidate):
    """Distinguishing claim content. A change here after freezing is a material revision."""
    p = candidate['predictor']
    return {'predictor': {'observation_ids': sorted(p['observation_ids']), 'quantity': p['quantity'], 'units': p['units'],
                          'transformation': p['transformation']},
            'population': candidate['population'], 'mechanism': candidate['mechanism'],
            'outcome': {k: candidate['outcome'][k] for k in ('quantity', 'units')},
            'company': candidate['exposure']['company']['id'], 'claim_basis': candidate['exposure']['claim_basis']}


def entity_conflict(s, e, where):
    known = s.entities.get(e['id'])
    if known and known['type'] != e['type']:
        raise LedgerError(f"{where}: entity {e['id']} already recorded as {known['type']}, not {e['type']}")


def register(s, e):
    known = s.entities.setdefault(e['id'], {'type': e['type'], 'name': e['name']})
    if known['name'] != e['name']:s.name_variants.setdefault(e['id'], {known['name']}).add(e['name'])


def must_exist(s, kind, rid, where):
    if s.latest(kind, rid) is None:raise LedgerError(f'{where}: unknown {kind} {rid}')


def check_versioned(kind, r, s):
    existing = s.versions[kind].get(r['id'], [])
    if r['version'] != len(existing) + 1:
        raise LedgerError(f"{kind} {r['id']}: next version must be {len(existing) + 1}; records are never overwritten")


def check_observation(r, s):
    w = f"observation {r['id']}"; must_exist(s, 'source', r['source_id'], w)
    for rid in r['related']:
        if rid != r['id']:must_exist(s, 'observation', rid, w)
    entity_conflict(s, r['entity'], w)
    return {}


def check_relationship(r, s):
    w = f"relationship {r['id']}"
    for e in (r['source_entity'], r['target_entity']):entity_conflict(s, e, w)
    return {}


def check_candidate(r, s):
    w = f"candidate {r['id']}"
    if r['method'] != s.campaign['method']:raise LedgerError(f"{w}: method must equal the campaign method {s.campaign['method']}")
    for oid in r['predictor']['observation_ids'] + r['outcome']['derived_from_observations']:must_exist(s, 'observation', oid, w)
    for rid in r['exposure']['relationship_ids']:must_exist(s, 'relationship', rid, w)
    if r['outcome']['source_id'] != R.UNKNOWN:must_exist(s, 'source', r['outcome']['source_id'], w)
    entity_conflict(s, r['exposure']['company'], w)
    previous = s.latest('candidate', r['id'])
    if previous is None:
        shared = sorted(cid for cid, versions in s.versions['candidate'].items()
                        if any(set(v['predictor']['observation_ids']) & set(r['predictor']['observation_ids']) for v in versions))
        unlisted = [cid for cid in shared if cid not in r['selection']['prior_related_claims']]
        if unlisted:
            raise LedgerError(f'{w}: {unlisted} share predictor observations; list them in selection.prior_related_claims '
                              '(a renamed claim is a new version, not a fresh idea)')
        entry, method = r['entry_record'], r['method']
        rule = {'OBSERVATION_FIRST': ('observation', r['predictor']['observation_ids']),
                'EVENT_FIRST': ('observation', r['predictor']['observation_ids'] + r['outcome']['derived_from_observations']),
                'RELATIONSHIP_FIRST': ('relationship', r['exposure']['relationship_ids'])}.get(method)
        if rule is None:
            if entry is not None:raise LedgerError(f'{w}: a hypothesis-first candidate starts from its mechanism; entry_record must be null')
        else:
            kind, linked = rule
            if entry is None or s.latest(kind, entry) is None:raise LedgerError(f'{w}: {method} must start from a recorded {kind}')
            if entry not in linked:raise LedgerError(f'{w}: the entry {kind} {entry} must be part of the claim')
            if method == 'EVENT_FIRST' and s.latest('observation', entry)['kind'] != 'EVENT':
                raise LedgerError(f'{w}: an event-first candidate starts from an EVENT observation')
        kind_of_revision = 'ORIGINAL'
    else:
        if r['entry_record'] != previous['entry_record']:raise LedgerError(f'{w}: the discovery entry record cannot change between versions')
        if not s.frozen(r['id'], previous['version']):kind_of_revision = 'PRE_FREEZE_REVISION'
        elif digest(core(r)) != digest(core(previous)):kind_of_revision = 'MATERIAL_REVISION'
        else:kind_of_revision = 'CLARIFICATION'
    lineage = [s.derived[('candidate', r['id'], v['version'])] for v in s.versions['candidate'].get(r['id'], [])]
    material = kind_of_revision == 'MATERIAL_REVISION' or any(d['revision_kind'] == 'MATERIAL_REVISION' for d in lineage)
    post_outcome = r['after_outcome_seen'] or any(d['post_outcome'] for d in lineage)
    return {'core_digest': digest(core(r)), 'revision_kind': kind_of_revision,
            'claim_class': 'REFORMULATION' if material else 'ORIGINAL', 'post_outcome': post_outcome}


def check_freeze(r, s):
    if set(r) != {'candidate_id', 'version'}:raise LedgerError('freeze: exactly candidate_id and version')
    c = s.version('candidate', r['candidate_id'], r['version'])
    if c is None:raise LedgerError(f"freeze: unknown candidate {r['candidate_id']} v{r['version']}")
    if c is not s.latest('candidate', r['candidate_id']):raise LedgerError('freeze: only the latest candidate version can be frozen')
    if s.frozen(r['candidate_id'], r['version']):raise LedgerError('freeze: this version is already frozen')
    refs = {oid: s.latest('observation', oid)['version'] for oid in c['predictor']['observation_ids'] + c['outcome']['derived_from_observations']}
    refs.update({rid: s.latest('relationship', rid)['version'] for rid in c['exposure']['relationship_ids']})
    sel = c['selection']; d = s.derived[('candidate', c['id'], c['version'])]
    untouched = (s.fixture == 'LIVE' and sel['outcome_inspected_before_freeze'] is False and not sel['famous_case']
                 and not sel['purposive_control'] and not d['post_outcome'])
    return {'core_digest': digest(core(c)), 'record_digest': digest(c), 'references': dict(sorted(refs.items())),
            'outcome_inspected_before_freeze': sel['outcome_inspected_before_freeze'], 'untouched_evaluation_eligible': untouched}


def candidate_for(r, s, w):
    c = s.version('candidate', r['candidate_id'], r['version'])
    if c is None:raise LedgerError(f"{w}: unknown candidate {r['candidate_id']} v{r['version']}")
    return c


def admitted_key(kind, record):
    if kind == 'freeze':return ('freeze', record['candidate_id'], record['version'])
    return (kind, record['id'], record['version'] if kind in R.VERSIONED else None)


def check_review(r, s, rules=RULES):
    w = f"review {r['id']}"; c = candidate_for(r, s, w); frozen = bool(s.frozen(c['id'], c['version']))
    refs = [ref for j in (r['judgments'].values() if r['kind'] == 'M' else []) for ref in j['evidence_refs']]
    refs += [ref for item in r['checked'] for ref in item['evidence_refs']]
    for ref in refs:
        kind = {'SRC-': 'source', 'OBS-': 'observation', 'REL-': 'relationship', 'CAND-': 'candidate'}.get(ref[:ref.find('-') + 1])
        if kind:must_exist(s, kind, ref, w)
    if r['kind'] == 'M' and not frozen:raise LedgerError(f'{w}: freeze the claim before its Measurement Gate M review')
    acknowledged = {n['category'] for n in r['not_checked']}
    missing = sorted(V.required_acknowledgements(s, c) - acknowledged)
    if missing:raise LedgerError(f'{w}: acknowledge what was not checked: {missing}')
    found = V.checklist(s, c['id'], c['version'], rules)
    if r['kind'] == 'M':
        for req, j in r['judgments'].items():
            if j['judgment'] == 'EVIDENCED' and found['requirements'][req]['blockers']:
                raise LedgerError(f"{w}: {req} cannot be EVIDENCED while mechanical blockers remain: {found['requirements'][req]['blockers']}")
    return {'version_frozen': frozen, 'blockers': {k: len(v['blockers']) for k, v in found['requirements'].items()},
            'all_six_evidenced': r['kind'] == 'M' and all(j['judgment'] == 'EVIDENCED' for j in r['judgments'].values()),
            'human_equivalent': R.human_equivalent(r['reviewer']['kind'], s.fixture)}


def latest_review(s, cid, version, kind, human=True):
    found = [r for r in s.reviews if r['candidate_id'] == cid and r['version'] == version and r['kind'] == kind
             and (not human or R.human_equivalent(r['reviewer']['kind'], s.fixture))]
    return found[-1] if found else None


def check_disposition(r, s, rules=RULES):
    w = f"disposition {r['id']}"; c = candidate_for(r, s, w); d = s.derived[('candidate', c['id'], c['version'])]
    if r['decision'] in ('M_PASSED', 'LEVEL_A_DESIGN_CANDIDATE'):
        if not s.frozen(c['id'], c['version']):raise LedgerError(f"{w}: {r['decision']} requires a frozen claim")
        blockers = {k: v['blockers'] for k, v in V.checklist(s, c['id'], c['version'], rules)['requirements'].items() if v['blockers']}
        if blockers:raise LedgerError(f'{w}: mechanical blockers remain {blockers}')
        m = latest_review(s, c['id'], c['version'], 'M')
        if m is None or not all(j['judgment'] == 'EVIDENCED' for j in m['judgments'].values()):
            raise LedgerError(f'{w}: M PASSED needs a human Measurement Gate M review evidencing all six requirements')
        admitted = s.admitted[admitted_key('review', m)]
        if rules != V.RULES_V001 and admitted != rules:
            # A review admitted under older rules never saw the newer blockers; it is not re-certified here.
            raise LedgerError(f"{w}: M review {m['id']} was admitted under {admitted}; record a new human M review under {rules}")
    if r['decision'] == 'LEVEL_A_DESIGN_CANDIDATE':
        if not any(x['candidate_id'] == c['id'] and x['version'] == c['version'] and x['decision'] == 'M_PASSED'
                   and (rules == V.RULES_V001 or s.admitted[admitted_key('disposition', x)] == rules) for x in s.dispositions):
            raise LedgerError(f'{w}: record M_PASSED for this version first' + ('' if rules == V.RULES_V001 else f' under {rules}'))
        if latest_review(s, c['id'], c['version'], 'H') is None:raise LedgerError(f'{w}: a separate human H assessment is required')
        if any(c['propositions'][p]['statement'] == R.UNKNOWN for p in R.PROPOSITIONS):
            raise LedgerError(f'{w}: state the economic, informational and residual-investment propositions separately')
    return {'claim_class': d['claim_class'], 'post_outcome': d['post_outcome'],
            'requires_separate_owner_approval': r['decision'] in ('VERIFY', 'LEVEL_A_DESIGN_CANDIDATE')}


def totals(efforts):
    """Known sums plus a count of UNKNOWN entries; unknown costs are never treated as zero."""
    out = {}
    for field in ('analyst_minutes', 'source_starts', 'bytes'):
        values = [e[field] for e in efforts]
        out[field] = {'known': sum(v for v in values if v != R.UNKNOWN), 'unknown_entries': sum(v == R.UNKNOWN for v in values),
                      'entries': len(values)}
    return out


def check_effort(r, s):
    w = f"effort {r['id']}"
    if r['candidate_id'] is not None:must_exist(s, 'candidate', r['candidate_id'], w)
    if not s.campaign['acquisition_authorized'] and (r['source_starts'] not in (0, R.UNKNOWN) or r['kind'] == 'SOURCE_START'
                                                     or (r['bytes'] not in (0, R.UNKNOWN))):
        raise LedgerError(f'{w}: this campaign has no acquisition authority; record no source starts or acquired bytes')
    if not s.campaign['acquisition_authorized'] and r['bytes'] == R.UNKNOWN and r['kind'] != 'SEARCH':
        raise LedgerError(f'{w}: unknown acquired bytes are possible only for searches in a campaign without acquisition authority')
    t = totals(s.efforts + [r]); budget = s.campaign['budget']
    for field, limit in (('analyst_minutes', budget['analyst_hours'] * 60), ('source_starts', budget['source_starts']),
                         ('bytes', budget['external_bytes'])):
        if t[field]['known'] > limit:raise LedgerError(f'{w}: {field} would exceed the campaign budget; separate authority is required')
    return {}


CHECKS = {'observation': check_observation, 'relationship': check_relationship, 'candidate': check_candidate,
          'source': lambda r, s: {}, 'review': check_review, 'disposition': check_disposition, 'effort': check_effort}


def check(kind, record, s, rules=None):
    """Validate one event under ``rules`` (default: current) and return its stored derived fields."""
    rules = RULES if rules is None else rules
    if rules not in KNOWN_RULES:raise LedgerError(f'unknown Discovery Lab rules {rules}')
    if kind == 'campaign':
        if s.campaign is not None:raise LedgerError('one campaign per ledger')
        R.validate(kind, record, record.get('fixture') if isinstance(record, dict) else None)
        if record['fixture'] == 'LIVE' and not (ROOT / record['authority'].split()[0]).is_file():
            raise LedgerError('a live campaign must cite an existing repository authority document as the first word of authority')
        return {'rules': rules}
    if s.campaign is None:raise LedgerError('a ledger begins with its campaign record')
    if KNOWN_RULES.index(rules) < KNOWN_RULES.index(s.latest_rules()):
        raise LedgerError(f'{kind}: rules {rules} are older than rules already applied in this ledger')
    if kind == 'freeze':derived = check_freeze(record, s)
    else:
        R.validate(kind, record, s.fixture)
        if kind in R.VERSIONED:check_versioned(kind, record, s)
        elif record['id'] in s.ids(kind):raise LedgerError(f"duplicate {kind} id {record['id']}")
        derived = CHECKS[kind](record, s, rules) if kind in ('review', 'disposition') else CHECKS[kind](record, s)
    # Tag only events admitted under rules newer than the campaign's, so V001 history replays unchanged.
    return derived if rules == s.rules else {**derived, 'rules': rules}


def fold(kind, record, derived, s):
    if kind != 'campaign':
        s.admitted[admitted_key(kind, record)] = derived.get('rules', s.rules)
        derived = {k: v for k, v in derived.items() if k != 'rules'}
    if kind == 'campaign':s.campaign, s.rules = record, derived['rules']
    elif kind == 'freeze':s.freezes[(record['candidate_id'], record['version'])] = derived
    elif kind in R.VERSIONED:
        s.versions[kind].setdefault(record['id'], []).append(record); s.derived[(kind, record['id'], record['version'])] = derived
        for e in {'observation': lambda: [record['entity']], 'relationship': lambda: [record['source_entity'], record['target_entity']],
                  'candidate': lambda: [record['exposure']['company']]}.get(kind, lambda: [])():
            register(s, e)
    else:
        getattr(s, kind + 's').append(record); s.derived[(kind, record['id'], None)] = derived


class Ledger:
    def __init__(self, path, clock=utc_now):
        self.path, self.clock = Path(path), clock

    @classmethod
    def create(cls, path, campaign, clock=utc_now):
        ledger = cls(path, clock)
        derived = check('campaign', campaign, State())
        with ledger._writer() as claim:
            if ledger.path.exists():raise LedgerError(f'{ledger.path} already exists; ledgers are never overwritten')
            claim['event'] = ledger._write(State(), 'campaign', campaign, derived, mode='xb')
        return ledger

    def load(self):
        """Verify the hash chain and replay every event through the append-time rules."""
        s, prev = State(), GENESIS
        raw = self.path.read_bytes()
        if raw and not raw.endswith(b'\n'):
            raise LedgerError(f'{self.path.name}: missing final newline; retain the incomplete ledger, do not append or repair it')
        for n, line in enumerate(raw.splitlines()):
            event = json.loads(line); stored = event.pop('hash', None)
            if event.get('seq') != n or event.get('prev') != prev or digest(event) != stored:
                raise LedgerError(f'{self.path.name}: hash chain broken at event {n}; the ledger was edited or truncated')
            rules = event['derived'].get('rules', s.rules) if isinstance(event.get('derived'), dict) else s.rules
            try:derived = check(event['type'], event['record'], s, rules)
            except ValueError as error:raise LedgerError(f'replay of event {n} fails current rules for its admitting version {rules}: {error}') from error
            if derived != event['derived']:raise LedgerError(f'event {n}: stored derived fields differ from replay ({rules})')
            event['hash'] = stored; fold(event['type'], event['record'], derived, s); s.events.append(event); prev = stored
        if s.campaign is None:raise LedgerError('empty ledger')
        return s

    def append(self, kind, record):
        with self._writer() as claim:
            s = self.load(); record = copy.deepcopy(record)
            derived = check(kind, record, s)
            claim['event'] = self._write(s, kind, record, derived)
            return claim['event']

    def freeze(self, cid, version=None):
        with self._writer() as claim:
            s = self.load(); latest = s.latest('candidate', cid)
            if latest is None:raise LedgerError(f'unknown candidate {cid}')
            record = {'candidate_id': cid, 'version': latest['version'] if version is None else version}
            claim['event'] = self._write(s, 'freeze', record, check('freeze', record, s))
            return claim['event']

    @contextmanager
    def _writer(self):
        """Exclude cooperating writers; an interrupted claim needs explicit operator reconciliation.

        A lock that cannot be removed never masks the outcome: an earlier error propagates unchanged
        (with a note), and a committed event raises WriterLockNotReleased naming its seq and hash.
        """
        target = self.path.resolve()
        lock = target.with_name(target.name + '.writer.lock')
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            handle = lock.open('xb')
        except FileExistsError as error:
            raise LedgerError(f'{self.path.name}: writer lock exists; another writer or an interrupted claim must be reconciled') from error
        claim = {}
        try:
            with handle:
                yield claim
        except BaseException as error:
            try:lock.unlink()
            except OSError as cleanup:error.add_note(f'writer lock {lock.name} was also left in place: {cleanup!r}')
            raise
        try:lock.unlink()
        except OSError as cleanup:
            if 'event' not in claim:raise
            raise WriterLockNotReleased(self.path, lock, claim['event'], cleanup) from cleanup

    def _write(self, s, kind, record, derived, mode='ab'):
        event = {'seq': len(s.events), 'type': kind, 'recorded_at_utc': self.clock(), 'record': record, 'derived': derived,
                 'prev': s.events[-1]['hash'] if s.events else GENESIS}
        event['hash'] = digest(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open(mode) as f:
            f.write(canonical(event) + b'\n'); f.flush(); os.fsync(f.fileno())
        return event
