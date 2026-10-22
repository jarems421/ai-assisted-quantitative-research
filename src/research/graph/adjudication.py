"""Graph Pilot R4 Phase B: independent dual human adjudication, exposure declarations, warning usefulness, conformance.

* **Two reviewers.** R1 and R2 are different humans. Each writes two logs against the same aliased export:
  ``adjudications-<R>.jsonl`` (economic confirmation of CONNECTION items only) and ``warning-usefulness-<R>.jsonl``
  (avoided-repetition usefulness of METHODOLOGICAL_WARNING and AVOIDED_REPEAT items only). The two questions are never
  mixed: a warning is not adjudicated as an economic connection, and usefulness is never an economic discovery.
* **Exposure.** Every row declares what the reviewer had seen (``exposure``) and whether they operated or attested an
  arm. Each item becomes CLEAN, POTENTIALLY_UNBLINDED (saw arm-identifying material), NOT_INDEPENDENT (saw the other
  reviewer's judgments or an AI assessment) or CONFLICTED (operated or attested an arm, declared or matched by name).
* **Sealing.** Each reviewer seals both logs by hash (``adjudication-seal-<R>.json``, written once) and declares that they
  had no access to the other reviewer's judgments. Logs changed after sealing are refused. In a git repository the
  reveal order is checked: each reviewer's logs must first appear in a commit strictly after the other reviewer's seal.
* **Consensus (proposed registered rule).** An item's outcome counts only where both reviewers agree; any disagreement is
  ``UNRESOLVED_DISAGREEMENT``, reported and never resolved by an AI, an operator or a third reading in this tool.
* **Conformance.** A prospective (V2) packet enters the primary comparison only if its snapshot conforms to the registered
  R4 configuration, it has two valid sealed logs, no item is CONFLICTED or NOT_INDEPENDENT, and (for live packets) the
  reveal order is verified. Owner deviation records are preserved and listed, but never admit a packet to the primary
  comparison.

What stays procedural: whether reviewers really worked without seeing each other's judgments (the seal and reveal order
are evidence, not proof), and whether a declared exposure is complete.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.research.discovery import records as R
from src.research.graph import pilot as P

ADJUDICATION_V2 = 'GRAPH_PILOT_ADJUDICATION_V2'
USEFULNESS_V1 = 'GRAPH_PILOT_WARNING_USEFULNESS_V1'
# V002 adds a mandatory reviewer-level exposure declaration, which also makes a zero-item packet auditable: a reviewer with
# no items to judge still declares their identity and exposure in the seal over their (explicitly empty) logs.
SEAL_VERSION = 'GRAPH_PILOT_ADJUDICATION_SEAL_V002'
DEVIATION_VERSION = 'GRAPH_PILOT_DEVIATION_V001'
REVIEWERS = ('R1', 'R2')
EXPOSURE_SOURCES = ('ARM_LEDGER', 'CONNECTION_LOG', 'ARM_SESSION', 'BLINDING_KEY', 'ALIAS_KEY', 'SUGGESTION_EXPORT', 'V001_EXPORT',
                    'OTHER_ADJUDICATION', 'AI_ASSESSMENT', 'OTHER')
ARM_IDENTIFYING = ('ARM_LEDGER', 'CONNECTION_LOG', 'ARM_SESSION', 'BLINDING_KEY', 'ALIAS_KEY', 'SUGGESTION_EXPORT', 'V001_EXPORT')
INDEPENDENCE_BREAKING = ('OTHER_ADJUDICATION', 'AI_ASSESSMENT')
EXPOSURE_KEYS = ('saw_arm_info', 'seen', 'operated_or_attested_arm', 'note')
ECONOMIC_KEYS = P.ADJUDICATION_KEYS + ('log_version', 'reviewer', 'exposure')
USEFULNESS = ('USEFUL_LESSON_REUSED', 'USEFUL_NOT_USED', 'NOT_USEFUL', 'CANNOT_ASSESS')
USEFULNESS_KEYS = ('blind_id', 'usefulness', 'avoided_action', 'checked_evidence', 'adjudicator', 'adjudicator_kind', 'adjudicator_minutes',
                   'recorded_at_utc', 'notes', 'log_version', 'reviewer', 'exposure')
ECONOMIC_KINDS, USEFULNESS_KINDS = ('CONNECTION',), ('METHODOLOGICAL_WARNING', 'AVOIDED_REPEAT')
UNRESOLVED = 'UNRESOLVED_DISAGREEMENT'
STATUS_ORDER = ('CLEAN', 'POTENTIALLY_UNBLINDED', 'NOT_INDEPENDENT', 'CONFLICTED')
SEAL_KEYS = ('version', 'packet', 'reviewer', 'adjudicator', 'reviewer_exposure', 'export', 'logs', 'sealed_at_utc', 'statement')
DEVIATION_KEYS = ('version', 'packet', 'kind', 'reason', 'decided_by', 'decided_at_utc', 'treatment')
DEVIATION_TREATMENTS = ('EXCLUDED_FROM_PRIMARY', 'SECONDARY_DESCRIPTIVE_ONLY')
SEAL_STATEMENT = ("I made these judgments myself, without access to the other reviewer's judgments or any AI assessment, and without "
                  'arm-identifying material except as declared on each item.')


def files(packet_dir, reviewer):
    d = Path(packet_dir)
    return {'economic': d / f'adjudications-{reviewer}.jsonl', 'usefulness': d / f'warning-usefulness-{reviewer}.jsonl',
            'seal': d / f'adjudication-seal-{reviewer}.json'}


def person(name):
    return ' '.join(str(name).lower().split())


def check_person(name, kind, fixture, where):
    allowed = ('HUMAN', 'SYNTHETIC_FIXTURE') if fixture == 'SYNTHETIC' else ('HUMAN',)
    if kind not in allowed or not name or not str(name).strip():raise P.PilotError(f'{where}: adjudication is a human decision')
    if P.ASSISTANT_NAME.search(str(name)):raise P.PilotError(f'{where}: an assistant cannot adjudicate ({name!r})')


def attesters(packet_dir):
    """Names of everyone who attested an arm session in this packet: they may not adjudicate it."""
    out = set()
    for f in sorted(Path(packet_dir).glob('session-*-*.json')):
        try:out.add(person(json.loads(f.read_text(encoding='utf-8'))['recorded_by']['name']))
        except (KeyError, ValueError):continue
    return out


def exposure_status(e, name, conflicts, where):
    if not isinstance(e, dict) or tuple(sorted(e)) != tuple(sorted(EXPOSURE_KEYS)):raise P.PilotError(f'{where}: exposure must have exactly {EXPOSURE_KEYS}')
    if e['saw_arm_info'] not in ('YES', 'NO') or e['operated_or_attested_arm'] not in ('YES', 'NO'):raise P.PilotError(f'{where}: exposure answers are YES or NO')
    seen = e['seen']
    if not isinstance(seen, list) or seen != sorted(set(seen)) or not set(seen) <= set(EXPOSURE_SOURCES):
        raise P.PilotError(f'{where}: exposure.seen is a sorted list drawn from {EXPOSURE_SOURCES}')
    if (e['saw_arm_info'] == 'YES') != bool(set(seen) & set(ARM_IDENTIFYING)):
        raise P.PilotError(f'{where}: saw_arm_info must be YES exactly when arm-identifying material is listed as seen')
    if not isinstance(e['note'], str):raise P.PilotError(f'{where}: exposure.note is text (may be empty)')
    if e['operated_or_attested_arm'] == 'YES' or person(name) in conflicts:return 'CONFLICTED'
    if set(seen) & set(INDEPENDENCE_BREAKING):return 'NOT_INDEPENDENT'
    return 'POTENTIALLY_UNBLINDED' if e['saw_arm_info'] == 'YES' else 'CLEAN'


def partition(export):
    items = {i['blind_id']: i for i in export['items']}
    economic = {b for b, i in items.items() if i['kind'] in ECONOMIC_KINDS}
    usefulness = {b for b, i in items.items() if i['kind'] in USEFULNESS_KINDS}
    if economic | usefulness != set(items):raise P.PilotError('every blinded item is either an economic or a usefulness item')
    return items, economic, usefulness


def evidence_of(item):
    return {x for end in (item['from'], item['to']) for e in end['evidence'] for x in (e['sha256'], e['locator']) if x}


def common_row(r, w, reviewer, name_seen, fixture, log_version):
    if r['log_version'] != log_version or r['reviewer'] != reviewer:raise P.PilotError(f'{w}: log_version {log_version} and reviewer {reviewer} required')
    check_person(r['adjudicator'], r['adjudicator_kind'], fixture, w)
    if name_seen and person(r['adjudicator']) != name_seen:raise P.PilotError(f'{w}: one reviewer is one person throughout their logs')
    if not (r['adjudicator_minutes'] == R.UNKNOWN or (isinstance(r['adjudicator_minutes'], (int, float)) and r['adjudicator_minutes'] >= 0)):
        raise P.PilotError(f'{w}: adjudicator_minutes must be a non-negative number or UNKNOWN')
    P.parse_time(r['recorded_at_utc'])
    return person(r['adjudicator'])


def validate_reviewer(packet_dir, export_name, reviewer, fixture):
    """One reviewer's economic and usefulness logs: complete, partitioned, human, exposure-declared."""
    if reviewer not in REVIEWERS:raise P.PilotError(f'reviewer is one of {REVIEWERS}')
    d = Path(packet_dir); export = json.loads((d / export_name).read_text(encoding='utf-8'))
    items, economic, usefulness = partition(export)
    conflicts, f, name, status = attesters(d), files(d, reviewer), None, {}
    for k in ('economic', 'usefulness'):
        if not f[k].is_file():raise P.PilotError(f'{f[k].name}: each reviewer writes both logs, explicitly empty when there are no such items')
    econ = {}
    for n, r in enumerate(P.read_jsonl(f['economic']), 1):
        w = f"{f['economic'].name} line {n}"
        if tuple(sorted(r)) != tuple(sorted(ECONOMIC_KEYS)):raise P.PilotError(f'{w}: fields must be exactly {ECONOMIC_KEYS}')
        name = common_row(r, w, reviewer, name, fixture, ADJUDICATION_V2)
        if r['blind_id'] not in economic or r['blind_id'] in econ:
            raise P.PilotError(f'{w}: {r["blind_id"]} is not an unadjudicated CONNECTION item (warnings and avoided repeats go to the usefulness log)')
        if r['outcome'] not in P.OUTCOMES or r['economic_meaning'] not in P.MEANING:raise P.PilotError(f'{w}: invalid outcome or economic_meaning')
        if r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS' and (not r['checked_evidence'] or not set(r['checked_evidence']) <= evidence_of(items[r['blind_id']])):
            raise P.PilotError(f'{w}: a confirmation lists the cited evidence it was checked against')
        status[r['blind_id']] = exposure_status(r['exposure'], r['adjudicator'], conflicts, w); econ[r['blind_id']] = r
    if set(econ) != economic:raise P.PilotError(f"{f['economic'].name}: {len(economic - set(econ))} CONNECTION items are not adjudicated")
    use = {}
    for n, r in enumerate(P.read_jsonl(f['usefulness']), 1):
        w = f"{f['usefulness'].name} line {n}"
        if tuple(sorted(r)) != tuple(sorted(USEFULNESS_KEYS)):raise P.PilotError(f'{w}: fields must be exactly {USEFULNESS_KEYS}')
        name = common_row(r, w, reviewer, name, fixture, USEFULNESS_V1)
        if r['blind_id'] not in usefulness or r['blind_id'] in use:raise P.PilotError(f'{w}: {r["blind_id"]} is not an unassessed warning or avoided-repeat item')
        if r['usefulness'] not in USEFULNESS:raise P.PilotError(f'{w}: usefulness is one of {USEFULNESS}')
        if r['usefulness'] == 'USEFUL_LESSON_REUSED':
            if not isinstance(r['avoided_action'], str) or not r['avoided_action'].strip():
                raise P.PilotError(f'{w}: USEFUL_LESSON_REUSED states the action the lesson changed or avoided')
            if not r['checked_evidence'] or not set(r['checked_evidence']) <= evidence_of(items[r['blind_id']]):
                raise P.PilotError(f'{w}: USEFUL_LESSON_REUSED lists the cited evidence of the lesson it checked')
        elif r['avoided_action'] is not None and not isinstance(r['avoided_action'], str):raise P.PilotError(f'{w}: avoided_action is text or null')
        status[r['blind_id']] = exposure_status(r['exposure'], r['adjudicator'], conflicts, w); use[r['blind_id']] = r
    if set(use) != usefulness:raise P.PilotError(f"{f['usefulness'].name}: {len(usefulness - set(use))} warning or avoided-repeat items are not assessed")
    return {'reviewer': reviewer, 'adjudicator': name, 'economic': econ, 'usefulness': use, 'status': status}


def seal(packet_dir, export_name, reviewer, name, exposure, kind='HUMAN', now=None):
    """The reviewer's own immutable seal over both of their logs (hashes), written when they finish.

    ``exposure`` is the reviewer's own declaration over the whole review (same fields as an item's). With zero items to
    judge, the logs are explicitly empty files and the seal alone carries the reviewer's identity and exposure: no
    judgment, usefulness score or effort is invented."""
    d = Path(packet_dir); snap = P.load_snapshot(d / 'snapshot.json')['snapshot']
    check_person(name, kind, snap['fixture'], f'seal {reviewer}')
    v = validate_reviewer(d, export_name, reviewer, snap['fixture'])
    if v['adjudicator'] is not None and v['adjudicator'] != person(name):raise P.PilotError('the seal is written by the reviewer whose logs it seals')
    exposure_status(exposure, name, attesters(d), f'seal {reviewer}')
    f = files(d, reviewer)
    logs = {k: {'path': f[k].name, 'sha256': P.sha256(f[k]), 'items': len(v[k])} for k in ('economic', 'usefulness')}
    doc = {'version': SEAL_VERSION, 'packet': snap['packet'], 'reviewer': reviewer, 'adjudicator': {'name': name, 'kind': kind},
           'reviewer_exposure': exposure,
           'export': {'name': export_name, 'sha256': P.sha256(d / export_name)}, 'logs': logs, 'sealed_at_utc': P.utc(now).isoformat(),
           'statement': SEAL_STATEMENT}
    try:P.write_new(f['seal'], doc)
    except FileExistsError as error:raise P.PilotError(f'reviewer {reviewer} has already sealed; a seal is immutable') from error
    return doc


def load_seal(packet_dir, reviewer, export_name, logs_checked):
    f = files(packet_dir, reviewer); s = json.loads(f['seal'].read_text(encoding='utf-8')); w = f['seal'].name
    if tuple(sorted(s)) != tuple(sorted(SEAL_KEYS)) or s['version'] != SEAL_VERSION or s['reviewer'] != reviewer:raise P.PilotError(f'{w}: not a {SEAL_VERSION} seal for {reviewer}')
    if s['export'] != {'name': export_name, 'sha256': P.sha256(Path(packet_dir) / export_name)}:raise P.PilotError(f'{w}: sealed against a different export')
    for k in ('economic', 'usefulness'):
        now = P.sha256(f[k]) if f[k].is_file() else None
        if now != s['logs'][k]['sha256']:raise P.PilotError(f'{w}: the {k} log changed after sealing')
    if s['statement'] != SEAL_STATEMENT:raise P.PilotError(f'{w}: the seal carries the independence statement')
    fixture = P.load_snapshot(Path(packet_dir) / 'snapshot.json')['snapshot']['fixture']
    check_person(s['adjudicator'].get('name'), s['adjudicator'].get('kind'), fixture, w)
    judged = list(logs_checked['economic'].values()) + list(logs_checked['usefulness'].values())
    if s['logs']['economic']['items'] != len(logs_checked['economic']) or s['logs']['usefulness']['items'] != len(logs_checked['usefulness']):
        raise P.PilotError(f'{w}: sealed item counts differ from the logs')
    if judged:  # with zero items there is no judgment for the seal to follow
        if P.parse_time(s['sealed_at_utc']) < max(P.parse_time(r['recorded_at_utc']) for r in judged):raise P.PilotError(f'{w}: sealed before the last judgment it seals')
        if person(s['adjudicator']['name']) != logs_checked['adjudicator']:raise P.PilotError(f'{w}: sealed by someone other than the reviewer')
    s['reviewer_status'] = exposure_status(s['reviewer_exposure'], s['adjudicator']['name'], attesters(packet_dir), w)
    return s


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=60)


def content_first_commit(root, rel, current):
    """The first commit holding the CURRENT bytes of a sealed file, or why there is none.

    Every commit reachable from HEAD that touches the path must hold exactly the current bytes (``git hash-object
    --no-filters``): a placeholder committed first, a later change, a deletion or a re-addition is CHANGED. So the commit
    used for ordering always contains the content actually sealed and validated, not merely a file of that name."""
    want = git(root, 'hash-object', '--no-filters', str(current)).stdout.strip()
    commits = git(root, 'log', '--format=%H', '--reverse', '--', rel).stdout.split()
    if not commits:return None, 'NOT_COMMITTED'
    for c in commits:
        blob = git(root, 'rev-parse', '--verify', '--quiet', f'{c}:{rel}')
        if blob.returncode != 0 or blob.stdout.strip() != want:return None, 'CHANGED'
    return commits[0], 'OK'


def reveal_order(packet_dir):
    """VERIFIED when, in git, each reviewer's logs first appear in a commit strictly after the other reviewer's seal commit."""
    d = Path(packet_dir).resolve()
    top = git(d, 'rev-parse', '--show-toplevel')
    if top.returncode != 0:return {'status': 'NOT_COMMITTED', 'detail': 'packet is not in a git repository'}
    root = Path(top.stdout.strip()); rel = lambda p: Path(p).resolve().relative_to(root).as_posix()
    commits = {}
    for rv in REVIEWERS:
        f, commits[rv] = files(d, rv), {}
        for k in ('economic', 'usefulness', 'seal'):
            if not f[k].is_file():return {'status': 'NOT_COMMITTED', 'detail': f'{rv} {k} file is missing'}
            first, state = content_first_commit(root, rel(f[k]), f[k])
            if state == 'CHANGED':return {'status': 'VIOLATED', 'detail': f'{rv} {k} file: committed history does not hold only the sealed content'}
            if state == 'NOT_COMMITTED':return {'status': 'NOT_COMMITTED', 'detail': f'{rv} {k} file is not committed'}
            commits[rv][k] = first
    for rv, other in (('R1', 'R2'), ('R2', 'R1')):
        for k in ('economic', 'usefulness'):
            if k not in commits[rv]:continue
            seal_c, log_c = commits[other]['seal'], commits[rv][k]
            # Strict ancestry: the other reviewer's seal must be in an EARLIER commit. git's --is-ancestor also succeeds when the
            # two commits are the same, which would let a seal and the judgments it should precede be revealed together.
            if seal_c == log_c:return {'status': 'VIOLATED', 'detail': f'{rv} {k} log first appears in the same commit as the {other} seal'}
            if git(root, 'merge-base', '--is-ancestor', seal_c, log_c).returncode != 0:
                return {'status': 'VIOLATED', 'detail': f'{rv} {k} log was committed before {other} sealed'}
    return {'status': 'VERIFIED', 'detail': "each log first appears strictly after the other reviewer's seal"}


def agreement(a, b):
    """Raw agreement and Cohen's kappa over items both reviewers judged, with the confusion matrix and disagreements."""
    ids = sorted(set(a) & set(b)); n = len(ids)
    if not n:return {'items': 0, 'agreements': 0, 'raw_agreement': P.ratio(0, 0), 'kappa': 'UNDEFINED_ZERO_DENOMINATOR', 'confusion': {}, 'disagreements': []}
    agree = sum(a[i] == b[i] for i in ids); cats = sorted({a[i] for i in ids} | {b[i] for i in ids})
    pe = sum((sum(a[i] == c for i in ids) / n) * (sum(b[i] == c for i in ids) / n) for c in cats); po = agree / n
    kappa = round((po - pe) / (1 - pe), 4) if pe < 1 else 'UNDEFINED_NO_VARIATION'
    confusion = {f'{x} | {y}': sum(a[i] == x and b[i] == y for i in ids) for x in cats for y in cats if any(a[i] == x and b[i] == y for i in ids)}
    return {'items': n, 'agreements': agree, 'raw_agreement': P.ratio(agree, n), 'kappa': kappa, 'confusion': confusion,
            'disagreements': [{'blind_id': i, 'R1': a[i], 'R2': b[i]} for i in ids if a[i] != b[i]]}


def worst(*statuses):
    return max(statuses, key=STATUS_ORDER.index)


def minutes(*values):
    return R.UNKNOWN if R.UNKNOWN in values else sum(values)


def dual(packet_dir, export_name='blind_v2.json'):
    """Validate both sealed reviewers and build the consensus adjudications, agreement report and independence status."""
    d = Path(packet_dir)
    missing = [rv for rv in REVIEWERS if not files(d, rv)['seal'].is_file()]
    if missing:return {'status': 'ADJUDICATION_NOT_DUAL', 'missing_seals': missing}
    fixture = P.load_snapshot(d / 'snapshot.json')['snapshot']['fixture']
    v = {rv: validate_reviewer(d, export_name, rv, fixture) for rv in REVIEWERS}
    seals = {rv: load_seal(d, rv, export_name, v[rv]) for rv in REVIEWERS}
    who = {rv: v[rv]['adjudicator'] or person(seals[rv]['adjudicator']['name']) for rv in REVIEWERS}  # zero items: the seal names the reviewer
    if who['R1'] == who['R2']:raise P.PilotError('R1 and R2 must be two different humans')
    items = partition(json.loads((d / export_name).read_text(encoding='utf-8')))[0]
    status = {b: worst(v['R1']['status'][b], v['R2']['status'][b]) for b in items}
    adjudications = {}
    for b in items:
        e1, e2 = v['R1']['economic'].get(b), v['R2']['economic'].get(b)
        if e1:
            adjudications[b] = {'outcome': e1['outcome'] if e1['outcome'] == e2['outcome'] else UNRESOLVED,
                                'economic_meaning': e1['economic_meaning'] if e1['economic_meaning'] == e2['economic_meaning'] else UNRESOLVED,
                                'adjudicator_minutes': minutes(e1['adjudicator_minutes'], e2['adjudicator_minutes']), 'usefulness': None}
        else:
            u1, u2 = v['R1']['usefulness'][b], v['R2']['usefulness'][b]
            adjudications[b] = {'outcome': 'NOT_ECONOMICALLY_ADJUDICATED', 'economic_meaning': 'NOT_APPLICABLE',
                                'adjudicator_minutes': minutes(u1['adjudicator_minutes'], u2['adjudicator_minutes']),
                                'usefulness': u1['usefulness'] if u1['usefulness'] == u2['usefulness'] else UNRESOLVED}
    field = lambda rv, log, k: {b: r[k] for b, r in v[rv][log].items()}
    report = {'outcome': agreement(field('R1', 'economic', 'outcome'), field('R2', 'economic', 'outcome')),
              'economic_meaning': agreement(field('R1', 'economic', 'economic_meaning'), field('R2', 'economic', 'economic_meaning')),
              'usefulness': agreement(field('R1', 'usefulness', 'usefulness'), field('R2', 'usefulness', 'usefulness'))}
    counts = {s: sum(x == s for x in status.values()) for s in STATUS_ORDER}
    reviewer_status = {rv: seals[rv]['reviewer_status'] for rv in REVIEWERS}
    return {'status': 'DUAL_SEALED', 'adjudications': adjudications, 'agreement': report, 'item_status': counts, 'reviewer_status': reviewer_status,
            'items': len(items),
            'potentially_unblinded': counts['POTENTIALLY_UNBLINDED'] > 0 or 'POTENTIALLY_UNBLINDED' in reviewer_status.values(), 'reveal_order': reveal_order(d),
            'reviewers': {rv: {'sealed_at_utc': seals[rv]['sealed_at_utc'], 'economic_items': len(v[rv]['economic']),
                               'usefulness_items': len(v[rv]['usefulness'])} for rv in REVIEWERS},
            'consensus_rule': 'an outcome counts only where both reviewers agree; otherwise UNRESOLVED_DISAGREEMENT, never resolved by an AI or operator'}


def deviations(packet_dir, fixture):
    """Owner deviation records (``deviation-*.json``): preserved and listed; none can admit a packet to the primary comparison."""
    out = []
    for f in sorted(Path(packet_dir).glob('deviation-*.json')):
        r = json.loads(f.read_text(encoding='utf-8')); w = f.name
        if tuple(sorted(r)) != tuple(sorted(DEVIATION_KEYS)) or r['version'] != DEVIATION_VERSION:raise P.PilotError(f'{w}: fields must be exactly {DEVIATION_KEYS}')
        if r['treatment'] not in DEVIATION_TREATMENTS:raise P.PilotError(f'{w}: a deviation is {DEVIATION_TREATMENTS}; it can never enter the primary comparison')
        if r['decided_by'].get('kind') not in (('HUMAN', 'SYNTHETIC_FIXTURE') if fixture == 'SYNTHETIC' else ('HUMAN',)):
            raise P.PilotError(f'{w}: a deviation is an owner decision')
        if P.ASSISTANT_NAME.search(str(r['decided_by'].get('name'))):raise P.PilotError(f'{w}: an assistant cannot decide a deviation')
        if not str(r['reason']).strip():raise P.PilotError(f'{w}: a deviation states the owner\'s reason')
        out.append({'file': w, 'sha256': P.sha256(f), **{k: r[k] for k in ('kind', 'reason', 'decided_by', 'decided_at_utc', 'treatment')}})
    return out


def conformance(packet_dir, snap, dual_result):
    """CONFORMING only when every primary-comparison requirement holds; reasons are listed, deviations preserved."""
    problems = []
    cfg = snap.get('r4_configuration')
    if not cfg or cfg.get('conforms') is not True:problems.append('NON_CONFORMING_CONFIGURATION')
    if dual_result['status'] != 'DUAL_SEALED':problems.append('ADJUDICATION_NOT_DUAL')
    else:
        reviewer = set(dual_result.get('reviewer_status', {}).values())
        if dual_result['item_status']['CONFLICTED'] or 'CONFLICTED' in reviewer:problems.append('ADJUDICATOR_CONFLICT')
        if dual_result['item_status']['NOT_INDEPENDENT'] or 'NOT_INDEPENDENT' in reviewer:problems.append('ADJUDICATION_NOT_INDEPENDENT')
        reveal = dual_result['reveal_order']['status']
        if reveal == 'VIOLATED':problems.append('REVEAL_ORDER_VIOLATED')
        elif reveal != 'VERIFIED' and snap['fixture'] != 'SYNTHETIC':problems.append('REVEAL_ORDER_UNVERIFIED')
    return {'status': 'NON_CONFORMING' if problems else 'CONFORMING', 'problems': problems, 'deviations': deviations(packet_dir, snap['fixture']),
            'potentially_unblinded': dual_result.get('potentially_unblinded', False)}
