"""Durable runs: unique IDs, private workspaces, a hash-chained journal and a small explicit stage state machine.

A stage is evaluated under a key derived from its inputs. A ONE_SHOT stage (custody copy, Quarry import/export, Jev
prepare, synthetic preview ledger) is claimed in the journal before it acts and is never re-run for the same key:
``continue`` reuses its recorded result, and an unfinished claim stays INTERRUPTED for human reconciliation. A CHECK
stage is read-only (or create-only into the run directory) and is re-evaluated only when its inputs change. New
inputs produce new keys and new create-only output directories; nothing earlier is overwritten.

Implementation drift fails closed. A run is bound to the implementation digest and contract versions recorded when
it was created. ``continue`` under different code is refused unless the owner explicitly accepts that exact digest;
acceptance is journalled, CHECK stages then re-run under the new code, and ONE_SHOT results are kept, never re-run.
Old records are never migrated."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform
import re
import secrets
import time

from src.research.spec import canonical, digest
from src.research.opportunity_scout.automation_v001 import execution as X
from . import BANNER, PROFILE, VERSION, delegate as D
from .guard import BoundaryViolation, offline, resolved
from .journal import Journal, JournalError, utc_now

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE = ROOT / '.research'
RUN_ID = re.compile(r'OPR-[A-Za-z0-9-]{1,64}')
LABEL = re.compile(r'[A-Za-z0-9_-]{1,32}')
STATUSES = ('COMPLETE', 'FAILED', 'BLOCKED', 'WAITING_FOR_HUMAN', 'WAITING_FOR_EVIDENCE', 'NOT_AUTHORISED', 'NOT_IMPLEMENTED',
            'SKIPPED', 'INTERRUPTED')
SCOPE = {'network': 'DENIED', 'process_creation': 'DENIED', 'model_or_provider_calls': 'NONE', 'source_acquisition': 'NONE',
         'writes': 'RUN_DIRECTORIES_ONLY', 'original_archive': 'READ_AND_HASH_ONLY', 'human_records': 'NEVER_CREATED',
         'discovery_ledgers': 'READ_ONLY_OR_SYNTHETIC_PREVIEW', 'jev': 'DETERMINISTIC_ONLY_NO_RESPONSE_IMPORT',
         'downstream_promotion': 'NOT_AUTHORISED', 'credentials': 'NEVER_OPENED'}
MAX_TREE_FILES, MAX_TREE_BYTES = 4096, 256 * 1024 * 1024


class OperatorError(ValueError):
    pass


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def unlinked(path):
    p = Path(path).absolute()
    for part in (p, *p.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise OperatorError('symlink/junction paths are refused: ' + str(part))
    return p


def tree(directory):
    """Every regular file under a directory, by relative POSIX path: SHA-256 and size. Links are refused."""
    root = unlinked(directory)
    if not root.is_dir():
        raise OperatorError(f'not a directory: {root}')
    files, total = {}, 0
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise OperatorError('linked file refused: ' + str(p))
        if p.is_file():
            size = p.stat().st_size; total += size
            if len(files) >= MAX_TREE_FILES or total > MAX_TREE_BYTES:
                raise OperatorError('archive exceeds the operator copy ceiling')
            files[p.relative_to(root).as_posix()] = {'sha256': sha_file(p), 'bytes': size}
    return {'files': files, 'count': len(files), 'bytes': total, 'digest': digest(files)}


def is_link(p):
    return p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())


def links(paths, stop=None):
    """Every symlink or junction at or below the given paths, and among their ancestors below ``stop``; missing paths skipped."""
    found = []
    for root in map(Path, paths):
        above = [a for a in (root, *root.parents) if stop is None or Path(a).is_relative_to(stop) and Path(a) != Path(stop)]
        found += [str(a) for a in above if a.exists() and is_link(a)]
        if root.is_dir() and not is_link(root):
            found += [str(x) for x in root.rglob('*') if is_link(x)]
    return sorted(set(found))


def overlaps(a, b):
    a, b = resolved(a), resolved(b)
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


_IMPORTS = {}  # (path, content hash) -> parsed import names; the digest itself is always taken from current bytes


def implementation():
    """Static src.* import closure of this package and of every delegated command line (CRLF normalised)."""
    todo = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'src/research/operator').glob('*.py'))
    todo += [f.relative_to(ROOT).as_posix() for entry, _ in D.ENTRY.values() for f in X.module_files(ROOT, entry)]
    files = {}
    while todo:
        rel = todo.pop()
        if rel in files:
            continue
        data = (ROOT / rel).read_bytes()
        files[rel] = hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()
        if (rel, files[rel]) not in _IMPORTS:
            _IMPORTS[(rel, files[rel])] = list(X.imports(rel, data.decode('utf-8')))
        for name in _IMPORTS[(rel, files[rel])]:
            if name.split('.')[0] == 'src':
                todo += [f.relative_to(ROOT).as_posix() for f in X.module_files(ROOT, name)]
    return {'boundary': 'static src.* import closure of src/research/operator and the delegated command lines', 'files': len(files),
            'digest': digest(dict(sorted(files.items())))}


def provenance():
    return {'revision': X.revision(ROOT), 'worktree_clean': 'UNKNOWN', 'worktree_clean_reason': X.CLEAN_REASON,
            'implementation': implementation(), 'python': platform.python_version(),
            'contract': {'operator_version': VERSION, 'profile': PROFILE}}


def binding(execution):
    """What a run's cached results depend on. Runs created before contracts were recorded never match."""
    contract = execution.get('contract') or {}
    return {'implementation': execution['implementation']['digest'], 'operator_version': contract.get('operator_version', 'UNRECORDED'),
            'profile': contract.get('profile', 'UNRECORDED')}


def bound(events):
    accepted = [e['record']['to'] for e in events if e['type'] == 'DRIFT_ACCEPTED']
    return accepted[-1] if accepted else binding(events[0]['record']['execution'])


class Layout:
    """Run directories. Each satisfies the delegated component's own location guard when ``base`` is .research/."""
    def __init__(self, base, run_id):
        self.base, self.run_id = Path(base).absolute(), run_id
        name = run_id.lower()
        self.run = self.base / 'operator-v1' / run_id
        self.artifacts, self.reports = self.run / 'artifacts', self.run / 'reports'
        self.scout = self.base / 'opportunity_scout' / f'{name}-forge'
        self.critic = self.base / 'opportunity_scout' / f'critic-v1-{name}-forge'
        self.quarry = self.base / f'quarry-v1-{name}'
        self.jev_provider = self.base / f'jev-provider-v1-{name}'
        self.jev = self.base / f'jev-navigation-v1-{name}'

    def roots(self):
        return [self.run, self.scout, self.critic, self.quarry, self.jev_provider, self.jev]

    def value(self):
        return {k: str(getattr(self, k)) for k in ('run', 'scout', 'critic', 'quarry', 'jev_provider', 'jev')}


def check_base(base):
    base = unlinked(base)
    if base.is_relative_to(ROOT):
        rel = base.relative_to(ROOT).as_posix()
        if rel != '.research' and not rel.startswith('.research/'):
            raise OperatorError('inside the repository, operator runs live only under the ignored .research/ directory')
    elif any((p / '.git').exists() for p in (base, *base.parents)):
        raise OperatorError('operator runs cannot be written into another Git checkout or worktree')
    return base


def new_run_id(clock=utc_now):
    moment = datetime.fromisoformat(clock()).astimezone(timezone.utc)
    return 'OPR-' + moment.strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(3)


def write_once(path, value):
    """Create-only artifact write; an identical existing file is accepted, a different one is never overwritten."""
    path = Path(path); data = value if isinstance(value, bytes) else canonical(value) + b'\n'
    if path.exists():
        if path.read_bytes() != data:
            raise OperatorError(f'artifact already exists with different content: {path}')
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)
    return path


# ------------------------------------------------------------------------------------------------- inputs

def evidence_spec(value, base_dir, where='evidence'):
    """Normalise explicitly supplied Quarry inputs; every file is hashed now so later drift is detectable."""
    if not isinstance(value, dict) or value.get('schema') != 'RESEARCH_OS_OPERATOR_EVIDENCE_V001':
        raise OperatorError(f'{where}: schema RESEARCH_OS_OPERATOR_EVIDENCE_V001 required')
    if set(value) - {'schema', 'routes', 'exports'}:
        raise OperatorError(f'{where}: unexpected fields {sorted(set(value) - {"schema", "routes", "exports"})}')
    def resolve(x):
        if x is None:
            return None
        p = unlinked(Path(base_dir) / x)
        return {'path': str(p), 'sha256': sha_file(p) if p.is_file() else 'MISSING'}
    routes, exports = [], []
    for r in value.get('routes', []):
        if not isinstance(r, dict) or not LABEL.fullmatch(str(r.get('label'))) or set(r) - {'label', 'registry', 'supply', 'original', 'inspection', 'extracted_file'}:
            raise OperatorError(f'{where}: each route needs a label [A-Za-z0-9_-] and only registry/supply/original/inspection/extracted_file')
        if not r.get('registry') or not r.get('supply') or 'original' not in r:
            raise OperatorError(f'{where}: route {r["label"]} needs registry, supply and an explicit original (null when UNAVAILABLE)')
        routes.append({'label': r['label'], **{k: resolve(r.get(k)) for k in ('registry', 'supply', 'original', 'inspection', 'extracted_file')}})
    for e in value.get('exports', []):
        if not isinstance(e, dict) or set(e) != {'label', 'path'} or not LABEL.fullmatch(str(e['label'])):
            raise OperatorError(f'{where}: each export needs exactly a label and a path')
        exports.append({'label': e['label'], 'path': str(unlinked(Path(base_dir) / e['path']))})
    labels = [x['label'] for x in routes + exports]
    if len(labels) != len(set(labels)):
        raise OperatorError(f'{where}: labels must be distinct')
    return {'routes': routes, 'exports': exports}


def effective_inputs(events):
    """Request merged with every later INPUTS_SUPPLIED record. A later route or export replaces an earlier same label."""
    request = events[0]['record']['request']
    routes = {r['label']: r for r in request['evidence']['routes']}
    exports = {e['label']: e for e in request['evidence']['exports']}
    terms, ledger = list(request['search_terms']), request['ledger']
    for e in events:
        if e['type'] == 'INPUTS_SUPPLIED':
            r = e['record']
            routes.update({x['label']: x for x in r['evidence']['routes']}); exports.update({x['label']: x for x in r['evidence']['exports']})
            terms += [t for t in r['search_terms'] if t not in terms]
            ledger = r['ledger'] or ledger
    return {**request, 'routes': [routes[k] for k in sorted(routes)], 'exports': [exports[k] for k in sorted(exports)],
            'search_terms': terms, 'ledger': ledger}


# ------------------------------------------------------------------------------------------------- state

def stage_state(events):
    """Per key: the claim and the result. Per invocation: the stage keys it used."""
    claims, results, invocations = {}, {}, []
    for e in events:
        r = e['record']
        if e['type'] == 'STAGE_STARTED':
            claims[r['key']] = e
        elif e['type'] == 'STAGE_FINISHED':
            results[r['key']] = {**r['result'], 'at': e['at']}
        elif e['type'] == 'INVOCATION_STARTED':
            invocations.append({'started': e, 'finished': None})
        elif e['type'] == 'INVOCATION_FINISHED':
            invocations[-1]['finished'] = e
    return claims, results, invocations


def interrupted(key, claim):
    return {'status': 'INTERRUPTED', 'key': key, 'stage_kind': claim['record']['kind'], 'summary': {'claimed_at': claim['at']},
            'research_findings': [], 'calls': [],
            'software_findings': ['Stage claimed but no result was recorded; the invocation was interrupted.'],
            'next_actions': ['Inspect the stage output directory and reconcile by hand; a ONE_SHOT stage is never re-run.']}


def current_stages(events):
    """Stage name -> result used by the latest invocation, in profile order; an unfinished claim is INTERRUPTED."""
    claims, results, invocations = stage_state(events)
    last = next((i['finished'] for i in reversed(invocations) if i['finished']), None)
    keys = dict(last['record']['stages']) if last else {}
    if invocations and not invocations[-1]['finished']:  # crashed invocation: its claims and results are newer
        for e in events[invocations[-1]['started']['seq']:]:
            if e['type'] in ('STAGE_STARTED', 'STAGE_FINISHED'):
                keys[e['record']['stage']] = e['record']['key']
    return {name: {**results[key], 'key': key} if key in results else interrupted(key, claims[key])
            for name, key in keys.items() if key in results or key in claims}


class Context:
    def __init__(self, journal, layout, events, clock):
        self.journal, self.layout, self.clock = journal, layout, clock
        self.events = events
        self.created = events[0]['record']
        self.inputs = effective_inputs(events)
        self.claims, self.results, _ = stage_state(events)
        self.current, self.used, self.calls, self.call_log = {}, {}, None, []
        self.invocation_seq = sum(e['type'] == 'INVOCATION_STARTED' for e in events)
        self.execution, self.seq, self.stop = None, None, False
        self.epoch = bound(events)

    def call(self, module, argv, preview=False):
        result = D.preview(self.layout.artifacts, argv) if preview else D.call(module, argv, roots=self.layout.roots())
        index = len(self.calls)
        out = write_once(self.layout.artifacts / 'calls' / f'{self.seq:05d}-{index:02d}.json',
                         {'command': result['command'], 'json': result['json'], 'text': result['text'], 'stderr': result['stderr']})
        record = {k: result[k] for k in ('command', 'exit_code', 'fault', 'stdout_sha256', 'stderr', 'elapsed_seconds')}
        record['output'] = out.relative_to(self.layout.run).as_posix()
        self.calls.append(record); self.call_log.append(record)
        return result

    def append(self, kind, record):
        event = self.journal.append(kind, record)
        self.events.append(event)
        return event


def result(status, summary=None, *, research=(), software=(), next_actions=(), blockers=None):
    """A stage outcome. ``blockers`` are what stops research here (default: the findings of a stopped stage)."""
    assert status in STATUSES
    stopped = status in ('BLOCKED', 'WAITING_FOR_HUMAN', 'WAITING_FOR_EVIDENCE')
    return {'status': status, 'summary': summary or {}, 'research_findings': list(research), 'software_findings': list(software),
            'blockers': list(blockers) if blockers is not None else list(research) if stopped else [], 'next_actions': list(next_actions)}


def run_stage(ctx, name, kind, step):
    """step: (inputs, action) where action() returns a result, or (inputs, result) for a decision needing no action."""
    inputs, action = step
    # CHECK results are valid only under the code that produced them; ONE_SHOT results are never redone.
    key = f"{name}@{digest(inputs if kind == 'ONE_SHOT' else {**inputs, 'binding': ctx.epoch})[:16]}"
    ctx.used[name] = key
    if key in ctx.results:
        ctx.current[name] = {**ctx.results[key], 'key': key}
        return ctx.current[name]
    if key in ctx.claims and kind == 'ONE_SHOT':  # claimed, never finished: never re-run
        ctx.current[name] = interrupted(key, ctx.claims[key])
        return ctx.current[name]
    if isinstance(action, dict):  # a decision without side effects: recorded once per distinct input
        res = {**action, 'calls': [], 'stage_kind': 'DECISION'}
        ctx.append('STAGE_FINISHED', {'stage': name, 'key': key, 'kind': 'DECISION', 'result': res})
    else:
        started = ctx.append('STAGE_STARTED', {'stage': name, 'key': key, 'kind': kind, 'inputs': inputs})
        ctx.seq, ctx.calls, t0 = started['seq'], [], time.perf_counter()
        try:
            res = action()
        except BoundaryViolation as error:
            res = result('FAILED', software=[f'BOUNDARY_VIOLATION: {error}'], next_actions=['Investigate the refused operation; nothing further ran in this invocation.'])
            ctx.stop = True
        except (OperatorError, JournalError, ValueError, OSError, KeyError, TypeError) as error:
            res = result('FAILED', software=[f'COORDINATOR_FAULT {type(error).__name__}: {error}'])
        res = {**res, 'calls': ctx.calls, 'stage_kind': kind, 'elapsed_seconds': round(time.perf_counter() - t0, 3)}
        ctx.append('STAGE_FINISHED', {'stage': name, 'key': key, 'kind': kind, 'result': res})
        ctx.calls = None
    ctx.results[key] = {**res, 'at': ctx.events[-1]['at']}
    ctx.current[name] = {**ctx.results[key], 'key': key}
    return ctx.current[name]


# ------------------------------------------------------------------------------------------------- invocations

def request_value(archive, idea_id, critic_workspace, evidence, search_terms, ledger, subject_name=None, *, listing=False):
    if not (listing and idea_id is None) and not re.fullmatch(r'IDEA-[A-Za-z0-9]{1,64}', str(idea_id)):
        raise OperatorError('an explicit Scout idea identifier (IDEA-...) is required')
    for t in search_terms:
        if not isinstance(t, str) or not t.strip() or len(t) > 200:
            raise OperatorError('search terms must be non-empty text')
    return {'profile': PROFILE, 'subject_name': subject_name, 'archive': str(unlinked(archive)), 'idea_id': idea_id,
            'critic_workspace': str(unlinked(critic_workspace)) if critic_workspace else None,
            'evidence': evidence or {'routes': [], 'exports': []}, 'search_terms': list(search_terms), 'ledger': ledger}


def ledger_spec(path, candidate, version, crosswalk=None):
    if path is None:
        if candidate or version or crosswalk:
            raise OperatorError('--candidate and --crosswalk need --ledger')
        return None
    if not candidate or not re.fullmatch(r'CAND-[A-Za-z0-9_.-]+', candidate):
        raise OperatorError('--ledger needs --candidate CAND-...')
    p = unlinked(path)
    c = unlinked(crosswalk) if crosswalk else None
    return {'path': str(p), 'sha256': sha_file(p) if p.is_file() else 'MISSING', 'candidate_id': candidate, 'candidate_version': version,
            'crosswalk': {'path': str(c), 'sha256': sha_file(c) if c.is_file() else 'MISSING'} if c else None}


def create(request, *, base=DEFAULT_BASE, run_id=None, clock=utc_now):
    base = check_base(base)
    run_id = run_id or new_run_id(clock)
    if not RUN_ID.fullmatch(run_id):
        raise OperatorError('run IDs look like OPR-<letters, digits, hyphens>')
    layout = Layout(base, run_id)
    archive = Path(request['archive'])
    if any(overlaps(o, base) for o in (archive, request['critic_workspace'] or archive.parent / f'critic-v1-{archive.name}')):
        raise OperatorError('the workspace base and an original archive overlap; originals are never written, so runs must live elsewhere')
    if any(p.exists() for p in layout.roots()):
        raise OperatorError(f'run {run_id} already exists; runs are never overwritten')
    for p in (layout.run, layout.scout.parent):
        p.mkdir(parents=True, exist_ok=True)
    journal = Journal(layout.run, clock)
    with journal.writer():
        journal.append('RUN_CREATED', {'schema': VERSION, 'banner': BANNER, 'run_id': run_id, 'profile': PROFILE, 'request': request,
                                       'scope': SCOPE, 'execution': provenance(), 'layout': layout.value()}, create=True)
    return layout


def locate(run_id, base=DEFAULT_BASE):
    if not RUN_ID.fullmatch(str(run_id)):
        raise OperatorError('unknown run ID format')
    layout = Layout(check_base(base), run_id)
    if not (layout.run / 'journal.jsonl').is_file():
        raise OperatorError(f'no run {run_id} under {layout.base}')
    return layout


def drift(events, current=None):
    """None when the current code matches the run's binding, else (bound, current)."""
    now, then = binding(current or provenance()), bound(events)
    return None if now == then else (then, now)


def invoke(layout, command, *, supplied=None, clock=utc_now, accept_drift=None):
    """One run or continue invocation over the profile's stages, entirely inside the operator boundary."""
    from . import profile
    from .report import render, write
    journal = Journal(layout.run, clock)
    with journal.writer(), offline(layout.roots()) as boundary:
        events = journal.load()
        execution = provenance()  # once per invocation: the drift check and the execution record use the same reading
        changed = drift(events, execution)
        if changed and (command != 'continue' or accept_drift != changed[1]['implementation']):
            raise OperatorError(f'implementation drift: run bound to {changed[0]}, current code is {changed[1]}. Nothing was run. '
                                'Start a fresh run, or have the owner reconcile explicitly with '
                                f"--accept-implementation-drift {changed[1]['implementation']} (CHECK stages then re-run; ONE_SHOT results are kept)")
        if accept_drift and not changed:
            raise OperatorError('--accept-implementation-drift was given, but the code matches the run; nothing to accept')
        if changed:
            journal.append('DRIFT_ACCEPTED', {'from': changed[0], 'to': changed[1], 'basis': 'EXPLICIT_OWNER_FLAG_ON_CONTINUE',
                                              'one_shot_results': 'KEPT_NEVER_RERUN', 'check_results': 'REEVALUATED'})
            events = journal.load()
        ctx = Context(journal, layout, events, clock)
        if supplied:
            ctx.append('INPUTS_SUPPLIED', supplied)
            ctx.inputs = effective_inputs(ctx.events)
        ctx.execution = execution
        start = ctx.append('INVOCATION_STARTED', {'command': command, 'invocation': ctx.invocation_seq + 1, 'operator_version': VERSION,
                                                  'execution': ctx.execution})
        ctx.invocation_seq += 1
        t0 = time.perf_counter()
        for name, kind, plan in profile.stages(ctx):
            if ctx.stop and name != 'INTEGRITY':  # after a boundary violation only the read-only integrity check runs
                run_stage(ctx, name, kind, ({'stopped': True}, result('SKIPPED', {'reason': 'invocation stopped after a boundary violation'})))
                continue
            try:
                step = plan(ctx)
            except BoundaryViolation as error:
                step, ctx.stop = ({'plan_fault': str(error)}, result('FAILED', software=[f'BOUNDARY_VIOLATION: {error}'])), True
            except (OperatorError, JournalError, ValueError, OSError, KeyError, TypeError) as error:  # before any claim
                step = ({'plan_fault': f'{type(error).__name__}: {error}'}, result('FAILED', software=[f'COORDINATOR_FAULT {type(error).__name__}: {error}']))
            run_stage(ctx, name, kind, step)
        ctx.append('INVOCATION_FINISHED', {'command': command, 'started_seq': start['seq'], 'stages': [[n, k] for n, k in ctx.used.items()],
                                           'delegated_calls': len(ctx.call_log), 'boundary_denials': list(boundary.denials),
                                           'elapsed_seconds': round(time.perf_counter() - t0, 3)})
        report = render(journal.load())  # from the retained records alone, never from in-memory state
        paths = write(layout, report)
    return report, paths
