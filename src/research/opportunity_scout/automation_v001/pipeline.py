"""Research OS pipeline V001: one owner authorisation carries one run from FORGE generation through both first-pass
critics to the deterministic recommendation and one report. It coordinates existing components and adds no
generation, rubric, archive or policy logic of its own:

  generation      exploratory_v001.runner.plan/run (unchanged; its own authorisation is nested in the pipeline one)
  critic inputs   critic_v1.packages.prepare (Layer A, blinded frozen requests; TUNING split)
  critic replies  automation_v001.providers (one dispatch per request) -> critic_v1.packages.import_response
  recommendation  critic_v1.policy.recommend (advisory, write-once)
  report          evaluation.report for the archive plus this module's consolidated JSON/Markdown

One attempt per request is enforced here by an exclusive claim before dispatch, stricter than the critic contract's
two. A whole run is claimed before any process starts and is never resumed: a crash leaves a truthful partial
record and ``report`` renders it. Adversarial criticism is never dispatched by V001; a policy recommendation for it
is recorded PENDING_APPROVAL. Nothing here changes Scout routing."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace
from typing import Callable

from src.research.spec import canonical, digest
from .. import claude_subscription as CS, schema as S
from ..critic_v1 import packages as P, policy as Q, rubric as K
from ..exploratory_v001 import runner as X
from ..post_generation.review import ASSISTANT
from ..storage import Archive, ROOT, input_json, unlinked
from . import providers as V

VERSION = 'SCOUT_RESEARCH_PIPELINE_V001'
PLAN_V, AUTH_V, RECEIPT_V, REPORT_V = (VERSION.replace('V001', s) for s in ('PLAN_V001', 'AUTHORISATION_V001', 'RECEIPT_V001', 'REPORT_V001'))
ROLES = ('SCIENTIFIC', 'ECONOMIC')
STAGES = ('GENERATION', 'CRITIC_PREPARATION', 'FIRST_PASS_CRITICS', 'RECOMMENDATION', 'REPORT')
RETENTION = 'PRIVATE_LOCAL_RAW_IN_GIT_IGNORED_ARCHIVE'
CRITIC_LIMIT = 8 * 1024 * 1024
CLOSE = X.CLOSE


@dataclass
class Host:
    """Everything outside the archive and workspace, injectable for offline tests."""
    generation: X.Host = field(default_factory=X.Host)
    codex_runner: Callable = X.capture          # bounded capture with process-tree stop (merged PR #26), every Codex process
    transport: Callable = V.https_transport   # Gemini HTTPS POST
    environ: dict = field(default_factory=lambda: dict(os.environ))
    now: Callable = S.utc_now
    monotonic: Callable = time.monotonic


def codex_admin(host, tally):
    """Codex administrative commands through the merged runner's bounded ``admin``: stdout and stderr together are
    limited to MAX_ADMIN_BYTES while capturing, and the process tree is stopped past the limit, at ADMIN_TIMEOUT or on
    a capture failure, each a named stop. Every launch and every confirmed start (``on_start``) is counted."""
    def runner(args, **kwargs):
        tally['launches'] += 1
        def started(pid):tally['started'] += 1
        return host.codex_runner(args, on_start=started, **kwargs)
    bounded = SimpleNamespace(runner=runner)
    return lambda executable, env, args: X.admin(bounded, executable, env, args)


def reservation_micro_usd(prompt_bytes, max_output_tokens, prices):
    """The worst-case bound in whole micro-USD, computed exactly and rounded up, so cumulative reservations never
    drift below the true bound. Prices are per 1M tokens, so tokens x price is already micro-USD."""
    return math.ceil(Fraction(prompt_bytes) * Fraction(prices['input_usd_per_million'])
                     + Fraction(max_output_tokens) * Fraction(prices['output_usd_per_million']))


def workspace_path(store):
    store = Path(store)
    return store.parent / f'critic-v1-{store.name}'


def complete_role(role):
    """Fill the executable hash for a Codex role from its path; validate every role."""
    role = dict(role)
    if role.get('provider') == V.CODEX:
        exe = CS.discover(role.get('executable'))
        role.update(executable=str(exe), executable_sha256=CS.file_hash(exe))
    return V.validate_role(role)


def plan(store, *, title, generator, scientific, economic, spend_cap_usd, codex_home=None, critic_timeout_seconds=600, host=None):
    """Plan only: creates the archive, the reserved generation attempt and the authorisation templates. No process."""
    host = host or Host()
    roles = {'SCIENTIFIC': complete_role(scientific), 'ECONOMIC': complete_role(economic)}
    if any(r['family'] == 'anthropic' for r in roles.values()):raise S.ScoutError('a critic never shares the Anthropic generator family')
    if type(critic_timeout_seconds) is not int or not 30 <= critic_timeout_seconds <= 1800:raise S.ScoutError('critic timeout is 30..1800 seconds')
    if type(spend_cap_usd) not in (int, float) or spend_cap_usd < 0 or spend_cap_usd > 50:raise S.ScoutError('spend cap is 0..50 USD')
    if any(r['provider'] == V.CODEX for r in roles.values()) and not codex_home:raise S.ScoutError('name CODEX_HOME explicitly (e.g. the user ~/.codex)')
    ws = workspace_path(store)
    if ws.exists():raise S.ScoutError('the critic workspace path already exists; a run needs new directories')
    gen = X.plan(store, title=title, host=host.generation, **generator)
    archive = Archive(store)
    template = input_json(Path(gen['authorisation_template']))
    body = {'schema': PLAN_V, 'pipeline': VERSION, 'archive': str(archive.path), 'critic_workspace': str(ws),
            'generation_plan_sha256': gen['plan_sha256'], 'generation_authorisation_template': template,
            'roles': roles, 'codex_home': str(codex_home) if codex_home else None, 'critic_timeout_seconds': critic_timeout_seconds,
            'spend_cap_usd': spend_cap_usd, 'critic_resources_sha256': digest(K.resource_manifest()), 'critic_split': 'TUNING',
            'critic_requests_maximum': 2 * generator['count'], 'attempts_per_request': 1, 'stages': list(STAGES),
            'adversarial': 'NEVER_DISPATCHED_V001_PENDING_APPROVAL', 'raw_retention': RETENTION,
            'first_pass_same_family': roles['SCIENTIFIC']['family'] == roles['ECONOMIC']['family'], 'created_at': host.now()}
    record = {**body, 'plan_sha256': digest(body)}
    archive.export('pipeline-plan.json', record)
    auth = {'schema': AUTH_V, 'pipeline_plan_sha256': record['plan_sha256'], 'generation': template, 'roles': roles,
            'spend_cap_usd': spend_cap_usd, 'critic_requests_maximum': record['critic_requests_maximum'], 'attempts_per_request': 1,
            'stages': list(STAGES), 'adversarial_permitted': False, 'raw_retention': RETENTION,
            'gemini_prepaid_auto_reload_disabled': False, 'hosted_transmission_approved': False, 'owner': '', 'approved_at': ''}
    path = archive.export('pipeline-authorisation-TEMPLATE.json', auth)
    unavailable = [k for k, r in roles.items() if r['provider'] == V.ANTIGRAVITY]
    return {'pipeline_plan_sha256': record['plan_sha256'], 'generation_plan_sha256': gen['plan_sha256'], 'authorisation_template': str(path),
            'critic_workspace': str(ws), 'unavailable_roles': unavailable, 'model_calls_made': 0, 'cli_commands_run': 0,
            'next': ('Complete the template outside the archive (pipeline and nested generation owner fields), then run.'
                     + (f' Roles {unavailable} are {V.UNAVAILABLE}: the run will stop before criticism.' if unavailable else ''))}


def load_plan(archive):
    p = input_json(archive.path / 'exports' / 'pipeline-plan.json')
    if p.get('schema') != PLAN_V or p['plan_sha256'] != digest({k: v for k, v in p.items() if k != 'plan_sha256'}):
        raise S.ScoutError('pipeline plan changed after it was written')
    if p['archive'] != str(archive.path) or p['critic_resources_sha256'] != digest(K.resource_manifest()):
        raise S.ScoutError('pipeline plan no longer matches the archive or the frozen critic texts')
    return p


def check_authorisation(value, p):
    if not isinstance(value, dict) or value.get('schema') != AUTH_V or value.get('pipeline_plan_sha256') != p['plan_sha256']:
        raise S.ScoutError('a pipeline authorisation for this exact plan is required')
    fixed = {'roles': p['roles'], 'spend_cap_usd': p['spend_cap_usd'], 'critic_requests_maximum': p['critic_requests_maximum'],
             'attempts_per_request': 1, 'stages': list(STAGES), 'adversarial_permitted': False, 'raw_retention': RETENTION}
    if any(value.get(k) != v for k, v in fixed.items()):raise S.ScoutError('authorisation does not bind the planned roles, limits and stages exactly')
    if value.get('hosted_transmission_approved') is not True:raise S.ScoutError('hosted transmission is not approved')
    owner = value.get('owner')
    if not isinstance(owner, str) or not owner.strip() or ASSISTANT.search(owner) or owner.strip().upper() in ('UNKNOWN', 'OWNER'):
        raise S.ScoutError('the authorising owner is a named human, not an assistant or model')
    try:moment = datetime.fromisoformat(value.get('approved_at', ''))
    except (TypeError, ValueError) as error:raise S.ScoutError('approved_at must be an ISO time') from error
    if moment.utcoffset() is None:raise S.ScoutError('approved_at needs a timezone')
    gen = value.get('generation')
    if not isinstance(gen, dict) or any(gen.get(k) != v for k, v in X.bindings(p['generation_authorisation_template']).items()) \
            or str(gen.get('owner', '')).strip() != owner.strip():
        raise S.ScoutError('the nested generation authorisation must bind the planned generation and name the same owner')
    if any(r['provider'] == V.GEMINI for r in p['roles'].values()):
        if value.get('gemini_prepaid_auto_reload_disabled') is not True or p['spend_cap_usd'] <= 0:
            raise S.ScoutError('Gemini needs a positive spend cap and the owner attestation that prepaid auto-reload is disabled')
    return digest(value)


class Run:
    """Write-once pipeline records inside the archive's exports, plus raw critic bytes beside them."""
    def __init__(self, archive, host):self.archive, self.host = archive, host

    def put(self, name, value):return self.archive.export(f'pipeline-{name}.json', value)

    def raw(self, name):return unlinked(self.archive.path / 'exports' / f'pipeline-{name}.bin')

    def stage(self, name, status, **facts):return self.put(f'stage-{name}', {'schema': VERSION, 'stage': name, 'status': status,
                                                                         'recorded_at': self.host.now(), **facts})


def file_facts(path):
    if not path.is_file():return {'bytes': S.UNKNOWN, 'sha256': S.UNKNOWN}
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):h.update(chunk)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def dispatch_codex(run, rid, role, p, prompt, codex_state):
    """One codex exec process. Returns (reply bytes or None, facts)."""
    host = run.host
    env = V.codex_environment(host.environ, p['codex_home'])
    if 'preflight' not in codex_state:
        tally = {'launches': 0, 'started': 0}
        run.put('codex-preflight-claim', {'request_id': rid, 'commands': ['--version', 'login status', 'exec --help'], 'claimed_at': host.now()})
        admin = codex_admin(host, tally)
        try:codex_state['preflight'] = V.codex_preflight(lambda a: admin(role['executable'], env, a), role['executable_sha256'], CS.file_hash(Path(role['executable'])))
        except CLOSE as error:codex_state['preflight'] = {'stop': str(error) if isinstance(error, S.ScoutError) else type(error).__name__}
        run.put('codex-preflight', {**codex_state['preflight'], 'administrative_launches': tally['launches'],
                                    'processes_started': tally['started'], 'recorded_at': host.now()})
    if 'stop' in codex_state['preflight']:return None, {'faults': ['PREFLIGHT_STOP:' + codex_state['preflight']['stop']], 'dispatched': False}
    targets = {c: run.raw(f'{rid}-{c}') for c in ('stdout', 'stderr')}
    handles, facts, start = {}, {'preflight': codex_state['preflight'], 'dispatched': True}, {'process': 'NOT_STARTED'}
    code, timed_out, faults = S.UNKNOWN, False, []
    def started(pid):start['process'] = 'STARTED'; run.put(f'started-{rid}', {'request_id': rid, 'pid': pid, 'started_at': host.now()})
    clock = host.monotonic()
    try:
        for c, t in targets.items():handles[c] = t.open('xb')
        with tempfile.TemporaryDirectory(prefix='scout-codex-') as cwd:
            if Path(cwd).resolve().is_relative_to(ROOT):raise S.ScoutError('Codex working directory must be outside the repository')
            run.put(f'dispatch-{rid}', {'request_id': rid, 'dispatched_at': host.now()})
            start['process'] = S.UNKNOWN
            proc = host.codex_runner(V.codex_arguments(role['executable'], role['model'], role['effort'], cwd), input=prompt, cwd=cwd,
                                     env=env.copy(), stdout=handles['stdout'], stderr=handles['stderr'], limit=CRITIC_LIMIT,
                                     timeout=p['critic_timeout_seconds'], shell=False, on_start=started)
            code = proc.returncode
    except subprocess.TimeoutExpired:timed_out = True
    except X.OutputLimitExceeded as error:faults.append('RECORDING_SIZE_LIMIT:' + error.tree)
    except X.CaptureFailed as error:faults.append('RAW_CAPTURE_WORKER_FAILED:' + error.tree)
    except CLOSE as error:faults.append(('PROCESS_START_FAILED' if isinstance(error, OSError) and start['process'] != 'STARTED' else 'DISPATCH_FAILED:') + type(error).__name__)
    finally:faults += ['RAW_CAPTURE_FINALISE_FAILED:' + x for x in X.seal(handles)]
    facts.update(process_start=start['process'], wall_seconds=round(host.monotonic() - clock, 3),
                 raw={c: file_facts(t) for c, t in targets.items()})
    if CS.file_hash(Path(role['executable'])) != role['executable_sha256']:faults.append('EXECUTABLE_CHANGED_DURING_RUN')
    if faults or start['process'] != 'STARTED':
        return None, {**facts, 'faults': faults or ['PROCESS_NOT_STARTED']}
    reply, review = V.codex_review(targets['stdout'].read_bytes(), targets['stderr'].read_bytes(), code, timed_out, role['model'],
                                   accept_requested_identity=role['accept_requested_identity'])
    return reply, {**facts, **review}


def dispatch_gemini(run, rid, role, prompt, budget, timeout):
    """One generateContent request. Its full worst-case cost is reserved against the owner cap before sending and is
    never released: not for a lower usage estimate, missing usage, a transport failure, a refused redirect or a
    crash. A usage estimate is recorded beside the reservation and never subtracted from it."""
    host = run.host
    key = host.environ.get(role['api_key_env'])
    if not key:return None, {'faults': ['API_KEY_ABSENT'], 'dispatched': False}
    reserve = reservation_micro_usd(len(prompt), role['max_output_tokens'], role['prices'])
    if budget['reserved_micro_usd'] + reserve > budget['cap_micro_usd']:
        return None, {'faults': ['SPEND_CAP_WOULD_BE_EXCEEDED'], 'dispatched': False, 'worst_case_usd': reserve / 1e6}
    body = json.dumps(V.gemini_request(prompt.decode('utf-8'), max_output_tokens=role['max_output_tokens'],
                                       thinking_level=role.get('thinking_level'))).encode('utf-8')
    url = V.GEMINI_ENDPOINT.format(model=role['model'])
    budget['reserved_micro_usd'] += reserve  # consumed before the dispatch record or the request exists; never released
    run.put(f'dispatch-{rid}', {'request_id': rid, 'dispatched_at': host.now(), 'worst_case_micro_usd': reserve,
                                'reserved_micro_usd_total': budget['reserved_micro_usd']})
    clock, target = host.monotonic(), run.raw(f'{rid}-response')
    spend = {'dispatched': True, 'worst_case_usd': reserve / 1e6, 'reservation_released': False}
    try:status, data = host.transport(url, {'Content-Type': 'application/json', 'x-goog-api-key': key}, body, timeout)
    except CLOSE as error:
        return None, {**spend, 'faults': ['TRANSPORT_FAILED:' + (str(error)[:200] if isinstance(error, S.ScoutError) else type(error).__name__)]}
    finally:key = None
    with target.open('xb') as f:f.write(data); f.flush(); os.fsync(f.fileno())
    reply, review = V.gemini_review(status, data, role['model'], role['prices'])
    return reply, {**spend, 'wall_seconds': round(host.monotonic() - clock, 3), 'raw': {'response': file_facts(target)}, **review}


def critic_provenance(role, facts, owner, now):
    basis = facts.get('model_identity_basis', S.UNKNOWN)
    label = f"{role['model']} via {role['provider']} (identity {basis})"[:200]
    u = facts.get('usage', {})
    if role['provider'] == V.CODEX:tokens = u.get('input_tokens', S.UNKNOWN), u.get('output_tokens', S.UNKNOWN)
    else:
        parts = (u.get('candidatesTokenCount'), u.get('thoughtsTokenCount'))
        tokens = u.get('promptTokenCount', S.UNKNOWN), (sum(parts) if all(type(x) is int for x in parts) else S.UNKNOWN)
    wall = facts.get('wall_seconds')
    return P.provenance(label, role['family'], 'OPERATOR_ASSISTED', owner, fresh_context='YES', received_at=now,
                        input_tokens=tokens[0], output_tokens=tokens[1], latency_ms=round(wall * 1000) if type(wall) in (int, float) else S.UNKNOWN)


def run(store, authorisation, *, host=None):
    """The one authorised run. Every stage outcome is recorded; nothing is retried, resumed or substituted."""
    host = host or Host()
    archive = Archive(store); p = load_plan(archive)
    value = input_json(authorisation)
    auth_sha = check_authorisation(value, p)
    if (archive.path / 'exports' / 'pipeline-claim.json').exists():raise S.ScoutError('this pipeline run was already claimed; it is never resumed or re-run')
    r = Run(archive, host)
    r.put('claim', {'schema': VERSION, 'plan_sha256': p['plan_sha256'], 'authorisation_sha256': auth_sha, 'claimed_at': host.now()})
    owner = value['owner'].strip()
    # Stage 1: generation through the merged exploratory runner, with the nested owner authorisation.
    path = r.put('generation-authorisation', value['generation'])
    try:
        gen = X.run(store, path, host=host.generation)
        r.stage('GENERATION', gen['status'], receipt_status=gen['status'], cards=gen['cards'], error=gen['error'])
    except CLOSE as error:
        r.stage('GENERATION', 'ERROR', error=(str(error) if isinstance(error, S.ScoutError) else type(error).__name__)[:2000])
        return finish(r, p, auth_sha, 'GENERATION_FAILED')
    if gen['status'] != 'VALID' or not gen['cards']:return finish(r, p, auth_sha, 'NO_ADMITTED_CARDS')
    unavailable = [k for k, role in p['roles'].items() if role['provider'] == V.ANTIGRAVITY]
    # Stage 2: the existing critic preparation (Layer A, blinded frozen requests).
    try:
        ws, manifest = P.prepare({'RUN': archive.load()}, p['critic_workspace'], split='TUNING')
        requests = {k: e['requests'] for k, e in sorted(manifest['subjects'].items()) if e['input_sha256'] is not None}
        r.stage('CRITIC_PREPARATION', 'COMPLETE', workspace=str(ws.path), reviewable_subjects=len(requests),
                not_reviewable=sorted(k for k, e in manifest['subjects'].items() if e['input_sha256'] is None))
    except CLOSE as error:
        r.stage('CRITIC_PREPARATION', 'ERROR', error=str(error)[:2000]); return finish(r, p, auth_sha, 'CRITIC_PREPARATION_FAILED')
    if sum(len(x) for x in requests.values()) > p['critic_requests_maximum']:
        r.stage('FIRST_PASS_CRITICS', 'NOT_RUN', reason='MORE_REQUESTS_THAN_AUTHORISED'); return finish(r, p, auth_sha, 'REQUEST_CEILING')
    # Stage 3: one independent dispatch per frozen first-pass request, in a fixed order; critics never see each other.
    budget = {'cap_micro_usd': math.floor(Fraction(p['spend_cap_usd']) * 10 ** 6), 'reserved_micro_usd': 0}
    codex_state, outcomes = {}, {}
    for key, pair in requests.items():
        for critic in ROLES:
            rid, role = pair[critic], p['roles'][critic]
            req = ws.request(rid)
            prompt = (ws.path / 'requests' / f'{rid}.md').read_bytes()
            if S.hash_text(prompt.decode('utf-8')) != req['rendered_prompt_sha256']:raise S.ScoutError('frozen prompt bytes changed')
            if role['provider'] == V.ANTIGRAVITY:
                outcome = {'outcome': V.UNAVAILABLE, 'dispatched': False}
            else:
                r.put(f'claim-{rid}', {'request_id': rid, 'critic': critic, 'subject_key': key, 'claimed_at': host.now()})  # one attempt, ever
                try:
                    reply, facts = (dispatch_codex(r, rid, role, p, prompt, codex_state) if role['provider'] == V.CODEX
                                    else dispatch_gemini(r, rid, role, prompt, budget, p['critic_timeout_seconds']))
                except CLOSE as error:reply, facts = None, {'faults': ['ADAPTER_FAILED:' + type(error).__name__], 'dispatched': S.UNKNOWN}
                outcome = {'outcome': 'PROVIDER_FAULT', **facts}
                if reply is not None:
                    attempt = P.import_response(ws, rid, reply, critic_provenance(role, facts, owner, host.now()))
                    outcome.update(outcome='IMPORTED', attempt=attempt['attempt'], status=attempt['status'], problems=attempt['problems'][:10],
                                   refusals=attempt['refusals'])
            outcomes[rid] = outcome
            r.put(f'critic-{rid}', {'request_id': rid, 'critic': critic, 'subject_key': key, 'role': {k: role.get(k) for k in ('provider', 'model', 'family')},
                                    'spend_reserved_worst_case_usd_total': budget['reserved_micro_usd'] / 1e6,
                                    'spend_unreserved_usd': (budget['cap_micro_usd'] - budget['reserved_micro_usd']) / 1e6, **outcome})
    imported = sum(o['outcome'] == 'IMPORTED' and o.get('status') == 'VALID' for o in outcomes.values())
    r.stage('FIRST_PASS_CRITICS', 'COMPLETE' if imported == len(outcomes) else 'INCOMPLETE', valid=imported, requests=len(outcomes),
            unavailable_roles=unavailable)
    # Stage 4: the existing deterministic policy; adversarial review is only ever recorded as pending.
    record, rec_path = Q.recommend(ws)
    pending = {k: s['adversarial_recommended'] for k, s in record['subjects'].items() if s.get('adversarial_recommended')}
    r.stage('RECOMMENDATION', 'COMPLETE', file=rec_path.name, counts=record['counts'],
            adversarial={k: {'reason': v, 'status': 'PENDING_APPROVAL'} for k, v in pending.items()})
    return finish(r, p, auth_sha, 'COMPLETE' if imported == len(outcomes) else 'INCOMPLETE_CRITICS')


def finish(r, p, auth_sha, outcome):
    rep = build(r.archive.path)
    r.put('report', rep)
    target = unlinked(r.archive.path / 'exports' / 'pipeline-report.md')
    with target.open('x', encoding='utf-8', newline='\n') as f:f.write(markdown(rep))
    r.stage('REPORT', 'COMPLETE', files=['pipeline-report.json', 'pipeline-report.md'])
    receipt = {'schema': RECEIPT_V, 'outcome': outcome, 'plan_sha256': p['plan_sha256'], 'authorisation_sha256': auth_sha,
               'stages': {s: stage_status(r.archive.path, s) for s in STAGES}, 'retried': False, 'resumed': False,
               'routing_authority': 'NONE', 'adversarial_dispatched': 0, 'completed_at': r.host.now()}
    r.put('receipt', receipt)
    return receipt


# --------------------------------------------------------------------------------------------- status and report

def read(path):
    return input_json(path) if path.is_file() else None


def stage_status(store_path, name):
    s = read(Path(store_path) / 'exports' / f'pipeline-stage-{name}.json')
    return s['status'] if s else 'NOT_RECORDED'


# Accounting from recorded files only. Every count is {'at_least': n, 'exact': n or UNKNOWN}; exact zero needs
# evidence (each marker is written before the launch or request it names, so its absence establishes zero). A CLI
# process is never counted as one provider request: Codex and Claude CLI request counts stay UNKNOWN once started.
ZERO = {'at_least': 0, 'exact': 0}
UNSEEN = {'at_least': 0, 'exact': S.UNKNOWN}
MEASURES = ('model_cli_processes_started', 'administrative_cli_launches', 'dispatches_attempted', 'provider_requests')


def count(at_least, exact=None):
    return {'at_least': at_least, 'exact': at_least if exact is None else exact}


def total(parts):
    exact = [x['exact'] for x in parts]
    return {'at_least': sum(x['at_least'] for x in parts), 'exact': S.UNKNOWN if S.UNKNOWN in exact else sum(exact)}


def generation_accounting(store):
    g, ex = X.status(store), Archive(store).path / 'exports'
    receipt = next((read(x) for x in sorted(ex.glob('exploratory-receipt-*.json'))), None)
    admin = count(receipt['administrative_commands_run']) if receipt and type(receipt.get('administrative_commands_run')) is int \
        else UNSEEN if g['claimed'] else ZERO
    return {'process_start': g['process_start'], 'invocation_status': g['invocation_status'],
            'model_cli_processes_started': {'STARTED': count(1), 'NOT_STARTED': ZERO, 'START_ATTEMPTED': ZERO}.get(g['process_start'], UNSEEN),
            'administrative_cli_launches': admin,
            'dispatches_attempted': count(1) if any(n.startswith('exploratory-dispatch-') for n in g['exports']) else ZERO,
            # A visible request ID shows at least one provider request; the CLI's own request count is never visible.
            'provider_requests': {'NOT_INVOKED': ZERO, 'INVOKED': count(1, S.UNKNOWN)}.get(g['invocation_status'], UNSEEN)}


def tolerant(path):
    """A record that a crash may have left partial (exports are not written atomically): None if absent or unreadable."""
    try:return read(path)
    except CLOSE:return None


def critic_accounting(ex, roles):
    claims = {x.name[len('pipeline-claim-'):-5] for x in ex.glob('pipeline-claim-CRQ-*.json')}
    rows = {}
    for rid in sorted(claims | {x.name[len('pipeline-dispatch-'):-5] for x in ex.glob('pipeline-dispatch-*.json')}):
        claim = tolerant(ex / f'pipeline-claim-{rid}.json') or {}
        provider = (roles.get(claim.get('critic')) or {}).get('provider', S.UNKNOWN)
        dispatched = (ex / f'pipeline-dispatch-{rid}.json').exists()
        record = tolerant(ex / f'pipeline-critic-{rid}.json')
        row = {'critic': claim.get('critic', S.UNKNOWN), 'provider': provider, 'claimed': rid in claims, 'outcome_recorded': record is not None,
               'dispatches_attempted': count(int(dispatched)), 'model_cli_processes_started': ZERO, 'provider_requests': ZERO}
        if provider == V.CODEX:
            started = (ex / f'pipeline-started-{rid}.json').exists()
            row['model_cli_processes_started'] = count(1) if started else UNSEEN if dispatched else ZERO
            message = started and isinstance(record, dict) and type(record.get('agent_messages')) is int and record['agent_messages'] >= 1
            row['provider_requests'] = count(int(message), S.UNKNOWN) if dispatched else ZERO  # a model-authored message shows at least one
        elif provider == V.GEMINI:  # no redirects or retries: a recorded response is exactly one HTTP request
            row['provider_requests'] = (count(1) if (ex / f'pipeline-{rid}-response.bin').exists() else UNSEEN) if dispatched else ZERO
        elif dispatched or row['claimed']:
            row.update(model_cli_processes_started=UNSEEN, provider_requests=UNSEEN)  # unreadable claim: nothing established
        rows[rid] = row
    return rows


def preflight_accounting(ex):
    claimed, rec = (ex / 'pipeline-codex-preflight-claim.json').exists(), tolerant(ex / 'pipeline-codex-preflight.json')
    if rec and all(type(rec.get(k)) is int for k in ('administrative_launches', 'processes_started')):
        return {'administrative_cli_launches': count(rec['administrative_launches']), 'processes_started': count(rec['processes_started']),
                'stop': rec.get('stop')}
    return {'administrative_cli_launches': UNSEEN if claimed else ZERO, 'processes_started': UNSEEN if claimed else ZERO, 'stop': None}


def accounting(store):
    """CLI processes started, launches, dispatches and provider requests, each from evidence; never inferred zero."""
    archive = Archive(store); ex = archive.path / 'exports'
    p = read(ex / 'pipeline-plan.json') or {}
    gen, critics, pre = generation_accounting(store), critic_accounting(ex, p.get('roles', {})), preflight_accounting(ex)
    parts = {'model_cli_processes_started': [gen['model_cli_processes_started']] + [r['model_cli_processes_started'] for r in critics.values()],
             'administrative_cli_launches': [gen['administrative_cli_launches'], pre['administrative_cli_launches']],
             'dispatches_attempted': [gen['dispatches_attempted']] + [r['dispatches_attempted'] for r in critics.values()],
             'provider_requests': [gen['provider_requests']] + [r['provider_requests'] for r in critics.values()]}
    return {'totals': {m: total(parts[m]) for m in MEASURES}, 'generation': gen, 'codex_preflight': pre, 'critic_requests': critics,
            'note': 'Counts come from recorded files only; exact zero only where the absence of a pre-launch marker '
                    'establishes it. A started CLI process is not one provider request; their number stays UNKNOWN. '
                    'Administrative launches send no prompt. Charges are never inferred.'}


def status(store):
    """Files only: never invokes a model or a CLI."""
    archive = Archive(store); ex = archive.path / 'exports'
    claimed, receipt = (ex / 'pipeline-claim.json').is_file(), read(ex / 'pipeline-receipt.json')
    names = sorted(x.name for x in ex.glob('pipeline-*')) if ex.is_dir() else []
    return {'planned': (ex / 'pipeline-plan.json').is_file(), 'claimed': claimed, 'finished': receipt is not None,
            'interrupted': claimed and receipt is None, 'outcome': receipt['outcome'] if receipt else ('NOT_STARTED' if not claimed else 'INTERRUPTED'),
            'stages': {s: stage_status(archive.path, s) for s in STAGES},
            'critic_claims': sum(n.startswith('pipeline-claim-CRQ-') for n in names),
            'critic_records': sum(n.startswith('pipeline-critic-') for n in names), 'accounting': accounting(store),
            'note': 'A claimed run is never resumed. An interrupted claim without a critic record means that request was '
                    'claimed but its outcome is unknown; it is never re-dispatched.'}


def spend(ex, p):
    """Gemini reservations from the dispatch records (never released) and the estimate total (UNKNOWN unless every
    dispatched request has one). Actual charges are never inferred."""
    reserved, estimates, unreadable = 0, [], False
    for x in sorted(ex.glob('pipeline-dispatch-*.json')):
        d = tolerant(x)
        if d is None:unreadable = True; continue
        if type(d.get('worst_case_micro_usd')) is int:
            reserved += d['worst_case_micro_usd']
            rec = tolerant(ex / f"pipeline-critic-{d.get('request_id')}.json") or {}
            estimates.append(rec.get('cost_estimate_usd_documented_prices', S.UNKNOWN))
    known = not unreadable and all(type(e) in (int, float) for e in estimates)
    return {'cap_usd': p.get('spend_cap_usd'), 'gemini_requests_reserved': S.UNKNOWN if unreadable else len(estimates),
            'worst_case_reserved_usd': S.UNKNOWN if unreadable else reserved / 1e6, 'reservations_released_usd': 0,
            'cost_estimate_usd_documented_prices': round(sum(estimates), 6) if known else S.UNKNOWN, 'actual_charges': S.UNKNOWN}


def build(store):
    """Consolidated report from the recorded files only. Missing pieces are reported, never inferred."""
    archive = Archive(store); ex = archive.path / 'exports'; state = archive.load()
    p = read(ex / 'pipeline-plan.json') or {}
    gen_receipt = next((read(x) for x in sorted(ex.glob('exploratory-receipt-*.json'))), None)
    attempt = next(iter(state.attempts.values()), {})
    critic = {x.name[len('pipeline-critic-'):-5]: read(x) for x in sorted(ex.glob('pipeline-critic-*.json'))}
    claims = {x.name[len('pipeline-claim-'):-5] for x in ex.glob('pipeline-claim-CRQ-*.json')}
    ws_path = Path(p.get('critic_workspace', '')) if p else None
    subjects, rec_file = {}, None
    if ws_path and (ws_path / 'manifest.json').is_file():
        ws = P.Workspace(ws_path); manifest = ws.manifest()
        attempts = {a['attempt']: a for a in ws.attempts()}
        recs = ws.files('recommendations'); rec = ws.read(recs[-1]) if recs else None; rec_file = recs[-1] if recs else None
        for key, e in sorted(manifest['subjects'].items()):
            row = {'idea_id': e['idea_id'], 'version': e['version'], 'layer_a': {k: e['layer_a'][k] for k in ('reviewable', 'counts', 'injection_flags')},
                   'critics': {}}
            for c, rid in e['requests'].items():
                rec_c = critic.get(rid)
                a = attempts.get(rec_c.get('attempt')) if rec_c else None
                row['critics'][c] = {'request_id': rid, 'outcome': (rec_c or {}).get('outcome', 'CLAIMED_OUTCOME_UNKNOWN' if rid in claims else 'NOT_DISPATCHED'),
                                     'status': a['status'] if a else None, 'model': (rec_c or {}).get('role'),
                                     'model_identity_basis': (rec_c or {}).get('model_identity_basis', S.UNKNOWN),
                                     'faults': (rec_c or {}).get('faults', []), 'usage': (rec_c or {}).get('usage', S.UNKNOWN),
                                     'cost_estimate_usd': (rec_c or {}).get('cost_estimate_usd_documented_prices', S.UNKNOWN),
                                     'judgments': {x['dimension']: {'judgment': x['judgment'], 'failure_type': x['failure_type'], 'severity': x['severity'],
                                                                    'potentially_fatal': x['potentially_fatal'], 'next_check': x['next_check']}
                                                   for x in a['output']['assessments']} if a and a['status'] == 'VALID' else None,
                                     'unresolved_assumptions': a['output']['unresolved_assumptions'] if a and a['status'] == 'VALID' else []}
            s = (rec or {}).get('subjects', {}).get(key)
            if s:row['recommendation'] = {k: s.get(k) for k in ('classification', 'rule', 'reasons', 'disagreements', 'fatal', 'repairs',
                                                                  'reconsider_when', 'unknown', 'first_pass_independence', 'adversarial_recommended')}
            row['adversarial'] = ('PENDING_APPROVAL' if s and s.get('adversarial_recommended') else 'NOT_RECOMMENDED' if s else 'NOT_EVALUATED')
            subjects[key] = row
    cards = {iid: {'title': v[-1]['idea']['title'], 'route': state.route(v[-1]), 'falsifier': v[-1]['idea']['falsifier'],
                   'next_step': v[-1]['idea']['next_step'], 'main_uncertainty': v[-1]['idea']['main_uncertainty']} for iid, v in state.cards.items()}
    return {'schema': REPORT_V, 'archive_head': state.events[-1]['hash'] if state.events else None,
            'stages': {s: stage_status(archive.path, s) for s in STAGES},
            'outcome': (read(ex / 'pipeline-receipt.json') or {}).get('outcome', 'INTERRUPTED_OR_NOT_FINISHED'),
            'generation': {'status': attempt.get('result', {}).get('status', 'PENDING'), 'model': attempt.get('requested_model'),
                           'error': attempt.get('result', {}).get('error'), 'receipt': {k: gen_receipt.get(k) for k in
                           ('process_start', 'provider_request', 'model_invocations', 'administrative_commands_run', 'review')} if gen_receipt else None},
            'cards': cards, 'subjects': subjects, 'recommendation_file': rec_file, 'accounting': accounting(store), 'spend': spend(ex, p),
            'roles': {k: {x: r.get(x) for x in ('provider', 'model', 'family', 'effort', 'accept_requested_identity')} for k, r in p.get('roles', {}).items()},
            'spend_cap_usd': p.get('spend_cap_usd'), 'actual_charges': S.UNKNOWN,
            'limits': ['AI recommendations are advisory: no Scout routing, READY, investment validation, causal claim or trading authority.',
                       'Calibration is not established; first-pass critics of different families are still not statistically independent.',
                       'Cost figures are estimates from documented prices; actual subscription or API charges are UNKNOWN.'],
            'authority': 'NONE'}


def markdown(rep):
    out = [f"# Research OS run report ({rep['outcome']})", '',
           '> Advisory AI criticism only. No Scout routing, READY approval, investment validation or trading authority.', '',
           '| Stage | Status |', '|---|---|'] + [f'| {s} | {v} |' for s, v in rep['stages'].items()]
    g = rep['generation']
    out += ['', f"**Generation:** {g['status']} ({g['model']})" + (f"; error: `{g['error'][:300]}`" if g.get('error') else ''), '']
    for key, row in rep['subjects'].items() or ():
        card = rep['cards'].get(row['idea_id'], {})
        out += [f"## {card.get('title', row['idea_id'])}", '', f"`{row['idea_id']}` v{row['version']} · Scout route {card.get('route')}", '']
        rec = row.get('recommendation')
        if rec:
            out += [f"**Recommendation:** {rec['classification']} ({rec['rule']}); adversarial review: {row['adversarial']}"
                    + (f" ({rec['adversarial_recommended']})" if rec.get('adversarial_recommended') else '')]
            for d in rec.get('disagreements') or []:out.append(f"- Disagreement on `{d['dimension']}`: {d['judgments']}")
            fatal = rec.get('fatal') or {}
            out.append(f"- Fatal claims: {len(fatal.get('first_pass', []))} first-pass, {len(fatal.get('established', []))} established")
            for x in (rec.get('repairs') or [])[:5]:out.append(f'- Repair: {x}')
            for x in (rec.get('reconsider_when') or [])[:5]:out.append(f'- Next check: {x}')
        out += ['', '| Dimension | Scientific | Economic |', '|---|---|---|']
        dims = K.DIMENSIONS
        def cell(c, d):
            j = (row['critics'].get(c) or {}).get('judgments')
            return '—' if not j else j[d]['judgment'] + (f" ({j[d]['failure_type']})" if j[d]['failure_type'] else '')
        out += [f'| {d} | {cell("SCIENTIFIC", d)} | {cell("ECONOMIC", d)} |' for d in dims]
        for c, info in row['critics'].items():
            out.append(f"- {c}: {info['outcome']} / {info['status']} · {info['model']} · identity {info['model_identity_basis']}"
                       + (f" · faults {info['faults']}" if info['faults'] else '') + f" · cost estimate {info['cost_estimate_usd']}")
        out += ['', f"Falsifier: {card.get('falsifier', {}).get('observation', '')}", '']
    out += ['## Accounting', '', '| Measure | At least | Exact |', '|---|---|---|']
    out += [f"| {m.replace('_', ' ')} | {v['at_least']} | {v['exact']} |" for m, v in rep['accounting']['totals'].items()]
    sp = rep['spend']
    out += ['', f"Gemini worst-case reserved {sp['worst_case_reserved_usd']} USD over {sp['gemini_requests_reserved']} request(s), "
            f"never released; documented-price estimate {sp['cost_estimate_usd_documented_prices']} USD.",
            '', f"_{rep['accounting']['note']}_", '']
    out += ['## Limits', ''] + [f'- {x}' for x in rep['limits']] + [f"- Spend cap {rep['spend_cap_usd']} USD; actual charges {rep['actual_charges']}."]
    return '\n'.join(out) + '\n'
