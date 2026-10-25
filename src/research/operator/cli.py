"""Research OS operator: one deterministic local coordinator for the offline Forge -> Quarry -> Jev -> Anvil -> Armoury
profile. Workflow automation only: it never records a human judgment, acquires a source, calls a model or provider,
opens credentials or promotes research. ``plan``, ``status`` and ``report`` start nothing and write nothing to a run.

  python -m src.research.operator doctor
  python -m src.research.operator subjects
  python -m src.research.operator plan --subject hypothesis-b
  python -m src.research.operator run --archive <scout archive> --idea IDEA-...
  python -m src.research.operator status OPR-...
  python -m src.research.operator continue OPR-... --evidence <evidence.json>
  python -m src.research.operator report OPR-... [--json]
  python -m src.research.operator demo
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import tempfile

from src.research.opportunity_scout.automation_v001.pipeline import workspace_path
from src.research.opportunity_scout.readiness import identifiable
from . import BANNER, PROFILE, VERSION
from .guard import offline
from .journal import Journal, JournalError
from .report import markdown, render
from .runs import (DEFAULT_BASE, ROOT, SCOPE, Layout, OperatorError, check_base, create, current_stages, drift, evidence_spec, invoke, ledger_spec,
                   locate, provenance, request_value, stage_state, tree)

SUBJECTS = 'RESEARCH_OS_OPERATOR_SUBJECTS_V001'
SKILL = ROOT / '.claude/skills/research-os/SKILL.md'
PLAN = [('PREFLIGHT', 'CHECK', 'dependency and location checks'),
        ('FORGE_CUSTODY', 'ONE_SHOT', 'hash the original archive and critic workspace; byte-identical working copy'),
        ('FORGE_RECORDS', 'CHECK', 'opportunity_scout validate/card; critic_v1 status; automation_v001 status/report (read-only)'),
        ('FORGE_READINESS', 'CHECK', 'opportunity_scout handoff on the copy: exports only after a human READY review'),
        ('QUARRY_IMPORT:<label>', 'ONE_SHOT', 'quarry_v1 import-file/status of owner-supplied originals'),
        ('QUARRY_EXPORT:<label>', 'ONE_SHOT', 'quarry_v1 export/validate-export with a human-authored inspection record'),
        ('QUARRY_EVIDENCE', 'CHECK', 'summary of supplied evidence'),
        ('JEV_EVIDENCE', 'ONE_SHOT', 'jev_navigation_integration_v1 compose-quarry; jev_navigation_v1 prepare/report (deterministic)'),
        ('JEV_MEMORY', 'ONE_SHOT', 'jev_navigation_v1 MEMORY_NAVIGATOR over the Graph memory catalogue (deterministic)'),
        ('ARMOURY_GRAPH', 'CHECK', 'graph same-gap per card requirement; graph search for explicit terms'),
        ('ANVIL_DRAFTS', 'CHECK', 'draft Discovery candidate and Source Passports with a field-level mapping audit'),
        ('ANVIL_CHECKS', 'CHECK/ONE_SHOT', 'discovery validate/checklist/source, Jev WORKFLOW_NAVIGATOR, graph trace: on a supplied ledger only with a '
                                            'human crosswalk binding it to the card (else UNLINKED), or on a synthetic preview'),
        ('DOWNSTREAM', 'CHECK', 'records the NOT_AUTHORISED / NOT_IMPLEMENTED boundaries'),
        ('INTEGRITY', 'CHECK', 're-hash every original after each invocation')]


def emit(value):
    print(json.dumps({'banner': BANNER, **value}, ensure_ascii=False, indent=2, allow_nan=False))


def subjects(base):
    path = check_base(base) / 'operator-v1' / 'subjects.json'
    if not path.is_file():
        return path, {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('schema') != SUBJECTS or not isinstance(value.get('subjects'), dict):
        raise OperatorError(f'{path}: schema {SUBJECTS} with a subjects object required')
    return path, value['subjects']


def resolve_request(a, base):
    name = getattr(a, 'subject', None)
    if name:
        if a.archive or a.idea:
            raise OperatorError('use either --subject or --archive/--idea')
        path, known = subjects(base)
        if name not in known:
            raise OperatorError(f'unknown subject {name!r}; known: {sorted(known)} (from {path})')
        s = known[name]
        archive, idea, critic = s['archive'], s['idea_id'], s.get('critic_workspace')
    else:
        archive, idea, critic = a.archive, a.idea, a.critic_workspace
        if not archive:
            raise OperatorError('--subject or --archive is required')
    evidence = evidence_spec(json.loads(Path(a.evidence).read_text(encoding='utf-8')), Path(a.evidence).absolute().parent) if a.evidence else None
    return {'archive': archive, 'idea_id': idea, 'critic_workspace': critic, 'evidence': evidence, 'search_terms': a.search or [],
            'ledger': ledger_spec(a.ledger, a.candidate, a.candidate_version, a.crosswalk), 'subject_name': name}


def doctor(base, self_test=True):
    checks = {'python': sys.version.split()[0], 'python_supported': sys.version_info >= (3, 11)}
    from .profile import MODULES, REQUIRED
    for m in MODULES:
        try:
            importlib.import_module(m); checks[m] = 'IMPORTED'
        except Exception as error:  # reported, never raised
            checks[m] = f'FAILED {type(error).__name__}: {error}'
    for f in REQUIRED:
        checks[f] = 'PRESENT' if (ROOT / f).is_file() else 'MISSING'
    checks['.research ignored'] = '.research/' in (ROOT / '.gitignore').read_text(encoding='utf-8').split()
    try:
        checks['workspace_base'] = str(check_base(base))
    except OperatorError as error:
        checks['workspace_base'] = f'REFUSED: {error}'
    if self_test:
        import socket
        denied = []
        with tempfile.TemporaryDirectory() as td, offline([td]):
            for probe in (lambda: socket.getaddrinfo('localhost', None), lambda: (Path(td).parent / 'operator-boundary-probe').write_bytes(b'')):
                try:
                    probe(); denied.append(False)
                except BaseException as error:  # BoundaryViolation is a BaseException by design
                    denied.append(type(error).__name__ == 'BoundaryViolation')
        checks['boundary_self_test'] = 'PASS' if all(denied) else 'FAIL'
    ok = checks['python_supported'] and checks['.research ignored'] and not any(str(v).startswith(('FAILED', 'MISSING', 'REFUSED', 'FAIL'))
                                                                             for v in checks.values())
    return {'schema': 'RESEARCH_OS_OPERATOR_DOCTOR_V001', 'ok': ok, 'checks': checks, 'execution': provenance(),
            'integrations': {'claude_code_skill': 'PRESENT' if SKILL.is_file() else 'ABSENT', 'jev_provider': 'DISABLED_NOT_AUTHORISED',
                             'quarry_acquisition': 'NOT_IMPLEMENTED', 'model_generation_or_critics': 'NOT_INVOKED_BY_OPERATOR'},
            'profiles': [PROFILE], 'authorises': []}


def plan(request, base):
    """Inspect a proposed run from a temporary copy of the Scout ledger only: nothing is written to a run."""
    archive = Path(request['archive'])
    facts = tree(archive)
    if 'scout.jsonl' not in facts['files']:
        raise OperatorError(f'{archive} is not a Scout archive (no scout.jsonl)')
    critic = Path(request['critic_workspace']) if request['critic_workspace'] else workspace_path(archive)
    from src.research.opportunity_scout.storage import Archive
    with tempfile.TemporaryDirectory() as td, offline([td]):
        target = Path(td) / 'scout'; target.mkdir()
        (target / 'scout.jsonl').write_bytes((archive / 'scout.jsonl').read_bytes())
        state = Archive(target).load()
    synthetic = state.batch.get('fixture') == 'SYNTHETIC'
    cards = []
    for iid, versions in state.cards.items():
        c = versions[-1]; review = state.current_review(c)
        cards.append({'idea_id': iid, 'version': c['version'], 'title': c['idea']['title'], 'lane': c['lane'], 'route': state.route(c),
                      'ready_review': bool(review and review['decision'] == 'READY' and review['approved_handoff']),
                      'identifiable_routes': sum(identifiable(r, synthetic) for r in c['idea']['source_routes'])})
    chosen = next((c for c in cards if c['idea_id'] == request['idea_id']), None)
    blockers = []
    if request['idea_id'] and not chosen:
        blockers.append(f"{request['idea_id']} is not in this archive")
    if chosen:
        if not chosen['identifiable_routes']:
            blockers.append('FORGE_READINESS: no identifiable source route, so READY is impossible without an owner revision (WAITING_FOR_HUMAN)')
        if not chosen['ready_review']:
            blockers.append('FORGE_READINESS: no human READY review for the current version (WAITING_FOR_HUMAN)')
        if not (request['evidence'] or {}).get('routes') and not (request['evidence'] or {}).get('exports'):
            blockers.append('QUARRY_EVIDENCE / JEV_EVIDENCE: no owner-supplied Quarry inputs (WAITING_FOR_EVIDENCE)')
        if not request['ledger'] and not synthetic:
            blockers.append('ANVIL_CHECKS: no Discovery ledger; a LIVE campaign needs owner authority (WAITING_FOR_HUMAN)')
    return {'schema': 'RESEARCH_OS_OPERATOR_PLAN_V001', 'profile': PROFILE, 'operator_version': VERSION, 'request': request,
            'archive': {'path': str(archive), 'files': facts['count'], 'bytes': facts['bytes'], 'digest': facts['digest'],
                        'fixture': state.batch.get('fixture'), 'events': len(state.events), 'head': state.events[-1]['hash'] if state.events else None},
            'critic_workspace': str(critic) if critic.is_dir() else None, 'cards': cards,
            'selected': chosen, 'stages': [{'stage': s, 'kind': k, 'delegates': d} for s, k, d in PLAN],
            'limits': SCOPE, 'predicted_blockers': blockers, 'layout': Layout(check_base(base), 'OPR-<new>').value(),
            'note': 'A plan predicts; only run records what happened. Choose --idea from cards when none is selected.', 'authorises': []}


def status(layout):
    events = Journal(layout.run).load()
    stages, (_, _, invocations) = current_stages(events), stage_state(events)
    rep = render(events)
    return {'schema': 'RESEARCH_OS_OPERATOR_STATUS_V001', 'run_id': layout.run_id, 'profile': events[0]['record']['profile'],
            'outcome': rep['outcome'], 'first_boundary': rep['first_boundary'], 'locked': (layout.run / 'journal.lock').exists(),
            'invocations': len(invocations), 'finished': bool(invocations) and invocations[-1]['finished'] is not None,
            'implementation_drift': (lambda d: None if d is None else {'run_bound_to': d[0], 'current_code': d[1],
                                     'continue': 'REFUSED_UNTIL_A_FRESH_RUN_OR_EXPLICIT_OWNER_ACCEPTANCE'})(drift(events)),
            'stages': {n: s['status'] for n, s in stages.items()}, 'journal_head': events[-1]['hash'], 'workspace': str(layout.run),
            'authorises': []}


def parser():
    p = argparse.ArgumentParser(prog='python -m src.research.operator', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--base', default=str(DEFAULT_BASE), help='workspace base (default: the ignored .research/ directory)')
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('doctor', help='installation, dependencies, required files, boundary self-test')
    x.add_argument('--no-self-test', action='store_true')
    sub.add_parser('subjects', help='named subjects from the private .research/operator-v1/subjects.json')
    def inputs(x, subject=True):
        if subject:
            x.add_argument('--subject', help='a name from subjects'); x.add_argument('--archive'); x.add_argument('--idea')
            x.add_argument('--critic-workspace')
        x.add_argument('--evidence', help='RESEARCH_OS_OPERATOR_EVIDENCE_V001 JSON of owner-supplied Quarry inputs')
        x.add_argument('--search', action='append', help='explicit Armoury search term (repeatable)')
        x.add_argument('--ledger', help='an existing Discovery ledger to check read-only'); x.add_argument('--candidate')
        x.add_argument('--candidate-version', type=int)
        x.add_argument('--crosswalk', help='human-authored RESEARCH_OS_OPERATOR_CROSSWALK_V001 binding the candidate to the Scout card')
    inputs(sub.add_parser('plan', help='permitted stages, inputs, limits and predicted blockers; starts nothing'))
    x = sub.add_parser('run', help='create a run and execute every eligible authorised local stage'); inputs(x)
    x.add_argument('--run-id', help='explicit OPR-... identifier (default: generated)')
    x = sub.add_parser('status', help='persisted state of a run'); x.add_argument('run_id')
    x = sub.add_parser('continue', help='resume orchestration with explicitly supplied inputs; never replays one-shot stages')
    x.add_argument('run_id'); inputs(x, subject=False)
    x.add_argument('--accept-implementation-drift', metavar='DIGEST',
                   help="owner's explicit acceptance of the current implementation digest for a run created under other code")
    x = sub.add_parser('report', help='the consolidated report, rendered from the run journal'); x.add_argument('run_id')
    x.add_argument('--json', action='store_true')
    x = sub.add_parser('demo', help='SYNTHETIC end-to-end demonstration in a new directory outside any Git checkout')
    x.add_argument('--out', help='new directory (default: a fresh temporary directory)')
    return p


def main(argv=None):
    if not sys.stdout.isatty() and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # card text is UTF-8; a piped Windows stdout would otherwise be the ANSI codepage
    a = parser().parse_args(argv)
    try:
        if a.command == 'doctor':
            out = doctor(a.base, self_test=not a.no_self_test); emit(out); return 0 if out['ok'] else 1
        if a.command == 'demo':
            from .demo import run as demo
            emit(demo(a.out or Path(tempfile.mkdtemp(prefix='research-os-operator-demo-')) / 'demo')); return 0
        if a.command == 'subjects':
            path, known = subjects(a.base); emit({'file': str(path), 'subjects': known}); return 0
        if a.command in ('plan', 'run'):
            r = resolve_request(a, a.base)
            request = request_value(r['archive'], r['idea_id'], r['critic_workspace'], r['evidence'], r['search_terms'], r['ledger'], r['subject_name'],
                                    listing=a.command == 'plan')
            if a.command == 'plan':
                emit(plan(request, a.base)); return 0
            layout = create(request, base=a.base, run_id=a.run_id)
            rep, paths = invoke(layout, 'run')
        elif a.command == 'continue':
            layout = locate(a.run_id, a.base)
            evidence = evidence_spec(json.loads(Path(a.evidence).read_text(encoding='utf-8')), Path(a.evidence).absolute().parent) if a.evidence else None
            supplied = {'evidence': evidence or {'routes': [], 'exports': []}, 'search_terms': a.search or [],
                        'ledger': ledger_spec(a.ledger, a.candidate, a.candidate_version, a.crosswalk)}
            rep, paths = invoke(layout, 'continue', supplied=supplied if (evidence or a.search or a.ledger) else None,
                                accept_drift=a.accept_implementation_drift)
        elif a.command == 'status':
            emit(status(locate(a.run_id, a.base))); return 0
        else:
            rep = render(Journal(locate(a.run_id, a.base).run).load())
            if a.json:
                emit(rep)
            else:
                sys.stdout.write(markdown(rep))
            return 0
        sys.stdout.write(markdown(rep))
        sys.stdout.write(f"\nRun records: {layout.run}\nReport files: {', '.join(str(p) for p in paths)}\n")
        return 0
    except (OperatorError, JournalError, ValueError, OSError, KeyError) as error:
        print(f'Research OS operator: {error}', file=sys.stderr)
        return 2
