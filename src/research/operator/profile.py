"""FORGE_TO_ANVIL_OFFLINE_V001: the first cross-stage profile (Forge -> Quarry -> Jev -> Anvil drafts -> Armoury).

Every stage delegates to an existing command and records its exact refusal when it refuses. The coordinator adds
only custody copies, dependency ordering, draft mappings and reporting. A stage returns ``(inputs, action)`` where
the action runs only when no result exists for those inputs, or ``(inputs, decision)`` when nothing needs doing."""
from __future__ import annotations

from functools import partial
import hashlib
import importlib
import json
from pathlib import Path

from src.research.spec import canonical, digest
from src.research.discovery.ledger import Ledger
from src.research.graph import catalogue as C
from src.research.jev_navigation_v1 import contracts as J
from src.research.opportunity_scout import engine as E, schema as S
from src.research.opportunity_scout.automation_v001.pipeline import workspace_path
from src.research.opportunity_scout.critic_v1 import packages as P
from src.research.opportunity_scout.post_generation.review import ASSISTANT
from src.research.opportunity_scout.readiness import identifiable
from src.research.opportunity_scout.storage import Archive
from src.research.quarry_v1 import io as QIO
from . import VERSION, adapters as A, delegate as D
from .runs import ROOT, OperatorError, links, overlaps, result, sha_file, tree, write_once

SCOUT, CRITIC, PIPELINE, QUARRY, JEV, JEVI, DISCOVERY, GRAPH = D.SCOUT, D.CRITIC, D.PIPELINE, D.QUARRY, D.JEV, D.JEVI, D.DISCOVERY, D.GRAPH
MODULES = (SCOUT + '.cli', CRITIC + '.cli', PIPELINE + '.pipeline', QUARRY + '.evidence', JEV + '.navigation', JEVI + '.quarry',
           DISCOVERY + '.cli', GRAPH + '.cli', 'jsonschema')
REQUIRED = ('docs/strategy/graph/research_memory_catalogue_v002.json', 'config/operational_pauses.json', '.gitignore')
WAITING = ('WAITING_FOR_HUMAN', 'WAITING_FOR_EVIDENCE', 'BLOCKED', 'NOT_AUTHORISED', 'NOT_IMPLEMENTED')
HANDOFF_FLAGS = ('creates_campaign', 'writes_ledger', 'certifies_M', 'certifies_H', 'acquisition_authorised', 'is_discovery_candidate_record')
CROSSWALK = 'RESEARCH_OS_OPERATOR_CROSSWALK_V001'
CROSSWALK_KEYS = {'schema', 'scout', 'discovery', 'mapping_status', 'reviewer', 'reviewed_at', 'notes'}
MAPPINGS = ('HUMAN_REVIEWED_SAME_CLAIM', 'HUMAN_REVIEWED_REFORMULATION')


def stages(ctx):
    yield 'PREFLIGHT', 'CHECK', preflight
    yield 'FORGE_CUSTODY', 'ONE_SHOT', custody
    yield 'CUSTODY_CHECK', 'CHECK', custody_check
    yield 'FORGE_RECORDS', 'CHECK', records
    yield 'FORGE_READINESS', 'CHECK', readiness
    for route in ctx.inputs['routes']:
        yield f"QUARRY_IMPORT:{route['label']}", 'ONE_SHOT', partial(quarry_import, route)
        yield f"QUARRY_EXPORT:{route['label']}", 'ONE_SHOT', partial(quarry_export, route)
    for export in ctx.inputs['exports']:
        yield f"QUARRY_EXPORT:{export['label']}", 'CHECK', partial(supplied_export, export)
    yield 'QUARRY_EVIDENCE', 'CHECK', quarry_summary
    yield 'JEV_EVIDENCE', 'ONE_SHOT', jev_evidence
    yield 'JEV_MEMORY', 'ONE_SHOT', jev_memory
    yield 'ARMOURY_GRAPH', 'CHECK', armoury
    yield 'ANVIL_DRAFTS', 'CHECK', drafts
    yield 'ANVIL_CHECKS', 'CHECK' if ctx.inputs['ledger'] else 'ONE_SHOT', anvil_checks
    yield 'DOWNSTREAM', 'CHECK', downstream
    yield 'INTEGRITY', 'CHECK', integrity


# ------------------------------------------------------------------------------------------------- helpers

def upstream(ctx, name, inputs):
    """None when ``name`` is COMPLETE; otherwise a decision that propagates its waiting state or SKIPs after a failure."""
    r = ctx.current.get(name)
    if r and r['status'] == 'COMPLETE':
        return None
    status = r['status'] if r else 'NOT_RUN'
    decided = result(status if status in WAITING else 'SKIPPED', {'depends_on': name, 'upstream_status': status},
                     next_actions=[f'Resolve {name} ({status}) first.'])
    return {**inputs, 'depends_on': name, 'upstream': (r or {}).get('key')}, decided


def refused(call):
    text = D.refusal(call)
    try:
        body = json.loads(text)
        return body.get('error') or body.get('reason') or text
    except ValueError:
        return text


def artifact(ctx, rel, value):
    path = write_once(ctx.layout.artifacts / rel, value)
    return {'path': path.relative_to(ctx.layout.run).as_posix(), 'sha256': sha_file(path)}


def load_artifact(ctx, ref):
    path = ctx.layout.run / ref['path']
    if sha_file(path) != ref['sha256']:
        raise OperatorError('run artifact changed since it was recorded: ' + ref['path'])
    return json.loads(path.read_bytes())


def unchanged(spec):
    """True when a supplied file still has the hash recorded when it was supplied."""
    return spec is None or (Path(spec['path']).is_file() and sha_file(spec['path']) == spec['sha256'])


def research_ignored():
    return '.research/' in (ROOT / '.gitignore').read_text(encoding='utf-8').split()


def card(ctx):
    return load_artifact(ctx, ctx.current['FORGE_RECORDS']['summary']['card_artifact'])


def synthetic(ctx):
    return ctx.current['FORGE_RECORDS']['summary']['fixture_class'] == 'SYNTHETIC'


def subject(ctx):
    value, audit = A.subject(card(ctx))
    return value, artifact(ctx, f"subject-{digest(value)[:12]}.json", value), artifact(ctx, f"subject-{digest(value)[:12]}.audit.json", audit)


def exports(ctx):
    rows = [(n.split(':', 1)[1], r) for n, r in sorted(ctx.current.items()) if n.startswith('QUARRY_EXPORT:') and r['status'] == 'COMPLETE']
    return [(label, r['summary']['export'], r['summary']['manifest_sha256']) for label, r in rows]


# ------------------------------------------------------------------------------------------------- Forge

def preflight(ctx):
    """A real prerequisite, re-checked every invocation: nothing is copied or delegated after a failure."""
    inputs = {'implementation': ctx.execution['implementation']['digest'], 'python': ctx.execution['python'], 'base': str(ctx.layout.base),
              'invocation': ctx.invocation_seq}
    def act():
        problems, modules = [], {}
        for m in MODULES:
            try:
                importlib.import_module(m); modules[m] = 'IMPORTED'
            except Exception as error:  # dependency fault, recorded as a software blocker
                modules[m] = 'FAILED'; problems.append(f'dependency {m}: {type(error).__name__}: {error}')
        problems += [f'missing required repository file {f}' for f in REQUIRED if not (ROOT / f).is_file()]
        if ctx.layout.base.is_relative_to(ROOT) and not research_ignored():
            problems.append('unsafe output configuration: .research/ is not git-ignored, so private run records could be committed')
        found = links([ctx.layout.base, *ctx.layout.roots()], stop=ctx.layout.base.parent)
        if found:
            problems.append(f'unsafe output configuration: links in the run directories are refused: {found}')
        for name in ('archive', 'critic_workspace'):
            if ctx.inputs[name] and overlaps(ctx.inputs[name], ctx.layout.base):
                problems.append(f'unsafe output configuration: the {name} and the workspace base overlap')
        return result('FAILED' if problems else 'COMPLETE', {'modules': modules, 'execution': ctx.execution}, software=problems,
                      blockers=problems, next_actions=['Fix the listed software blockers, then continue; no archive copy or delegated stage ran.'] if problems else [])
    return inputs, act


def custody(ctx):
    archive = Path(ctx.inputs['archive'])
    explicit = ctx.inputs['critic_workspace']
    critic = Path(explicit) if explicit else workspace_path(archive)
    basis = 'EXPLICIT' if explicit else 'SCOUT_SIBLING_CONVENTION' if critic.is_dir() else 'NONE_FOUND'
    critic = critic if basis != 'NONE_FOUND' else None
    inputs = {'archive': str(archive), 'critic_workspace': str(critic) if critic else None}
    up = upstream(ctx, 'PREFLIGHT', inputs)
    if up:
        return up
    def copy(source, target, manifest):
        target.mkdir(parents=False, exist_ok=False)
        for rel, meta in manifest['files'].items():
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as handle:
                handle.write((source / rel).read_bytes())
            if sha_file(dest) != meta['sha256']:
                raise OperatorError('copy differs from the original: ' + rel)
        copied = tree(target)
        if copied['digest'] != manifest['digest']:
            raise OperatorError('working copy is not byte-identical to the original')
        return copied
    def act():
        original = tree(archive)
        if 'scout.jsonl' not in original['files']:
            return result('FAILED', research=[f'{archive} is not a Scout archive (no scout.jsonl).'])
        locks = [n for n in original['files'] if n.endswith('.lock')]
        critic_tree = tree(critic) if critic else None
        if critic_tree:
            locks += [n for n in critic_tree['files'] if n.endswith('.lock')]
        if locks:
            return result('FAILED', research=[f'Original holds writer locks {locks}; an active or interrupted writer must be reconciled first.'])
        copied = copy(archive, ctx.layout.scout, original)
        critic_copy = copy(critic, ctx.layout.critic, critic_tree) if critic else None
        manifest = artifact(ctx, 'custody-manifest.json', {'archive': original, 'critic_workspace': critic_tree})
        return result('COMPLETE', {'original': {'path': str(archive), 'files': original['count'], 'bytes': original['bytes'], 'digest': original['digest']},
                                   'copy': {'path': str(ctx.layout.scout), 'digest': copied['digest']},
                                   'critic': {'path': str(critic), 'basis': basis, 'files': critic_tree['count'], 'digest': critic_tree['digest'],
                                              'copy': str(ctx.layout.critic), 'copy_digest': critic_copy['digest']} if critic else {'basis': basis},
                                   'byte_identical': True, 'manifest': manifest},
                      software=[] if critic else ['No critic workspace was supplied or found beside the archive; criticism records are limited to the archive.'])
    return inputs, act


def drift_state(path, recorded):
    try:
        current = tree(path)['digest']
    except (OperatorError, OSError) as error:
        current = f'UNREADABLE: {error}'
    return {'path': path, 'recorded_digest': recorded, 'current_digest': current, 'state': 'UNCHANGED' if current == recorded else 'CHANGED'}


def custody_check(ctx):
    """Every invocation, before any dependent stage: the originals must still match their retained custody manifests.
    A change blocks the run; the working copy is never recopied and recorded one-shot stages are never re-run."""
    inputs = {'invocation': ctx.invocation_seq}
    up = upstream(ctx, 'FORGE_CUSTODY', inputs)
    if up:
        return up
    s = ctx.current['FORGE_CUSTODY']['summary']
    def act():
        rows = {'archive': drift_state(s['original']['path'], s['original']['digest'])}
        if s['critic'].get('digest'):
            rows['critic_workspace'] = drift_state(s['critic']['path'], s['critic']['digest'])
        changed = [k for k, v in rows.items() if v['state'] != 'UNCHANGED']
        found = [f"Original {k} changed since custody: recorded digest {rows[k]['recorded_digest']}, current {rows[k]['current_digest']}." for k in changed]
        return result('FAILED' if changed else 'COMPLETE', rows, software=found, blockers=found,
                      next_actions=['Reconcile the change to the original by hand, or start a fresh run. The working copy is never recopied, '
                                    'and recorded one-shot stages are never re-run.'] if changed else [])
    return inputs, act


def critic_records(ctx, idea):
    """Advisory criticism recorded for this idea: request statuses, pipeline outcomes and the latest recommendation."""
    if not ctx.layout.critic.is_dir():
        return {'available': False}, []
    status = ctx.call(CRITIC, ['status', ctx.layout.critic])
    ws = P.Workspace(ctx.layout.critic)
    subjects = {k: e for k, e in ws.manifest()['subjects'].items() if e['idea_id'] == idea}
    if not D.ok(status) or not subjects:
        return {'available': True, 'status_refusal': None if D.ok(status) else refused(status), 'subject': None}, []
    key, entry = sorted(subjects.items())[-1]
    rows = (status['json']['subjects'].get(key) or {}).get('requests', {})
    recs = ws.files('recommendations')
    rec = (ws.read(recs[-1])['subjects'].get(key) or {}) if recs else {}
    out = {'available': True, 'subject': key, 'version': entry['version'], 'requests': {}, 'recommendation': None}
    findings = []
    for critic, rid in sorted(entry['requests'].items()):
        attempts = [a['status'] for a in (rows.get(critic) or {}).get('attempts', [])]
        pipeline = ctx.layout.scout / 'exports' / f'pipeline-critic-{rid}.json'
        record = json.loads(pipeline.read_bytes()) if pipeline.is_file() else {}
        out['requests'][critic] = {'request_id': rid, 'attempts': attempts, 'pipeline_outcome': record.get('outcome', 'NOT_RECORDED'),
                                   'fault_labels': record.get('faults', [])}
        findings.append(f"{critic.title()} critique {rid}: imported attempts {attempts or 'none'}; pipeline outcome "
                        f"{record.get('outcome', 'NOT_RECORDED')}" + (f" ({', '.join(record['faults'])}); no judgment exists" if record.get('faults') else '') + '.')
    if rec:
        out['recommendation'] = {'file': recs[-1], 'classification': rec.get('classification'), 'rule': rec.get('rule'),
                                 'adversarial_recommended': rec.get('adversarial_recommended')}
        findings.append(f"Advisory critic recommendation {rec.get('classification')} ({rec.get('rule')}); it never changes Scout routing.")
    return out, findings


def pipeline_records(ctx, critic):
    """Read-only Research OS pipeline status and saved report of the archived run, when the archive has one."""
    if not (ctx.layout.scout / 'exports' / 'pipeline-plan.json').is_file():
        return {'pipeline_run': False}, []
    s, r = ctx.call(PIPELINE, ['status', ctx.layout.scout]), ctx.call(PIPELINE, ['report', ctx.layout.scout, '--json'])
    out, software = {'pipeline_run': True}, []
    if D.ok(s):
        j = s['json']
        out.update(outcome=j['outcome'], stages=j['stages'], finalisation=j['finalisation'], accounting_totals=j['accounting']['totals'])
        f = j['finalisation']
        if not f.get('consistent'):
            software.append(f"Archived pipeline finalisation {f['state']} (consistent: false): saved report "
                            f"{f.get('saved_report_outcome', 'UNKNOWN')} versus receipt {f.get('receipt_outcome', 'UNKNOWN')}. Recorded, never repaired.")
    else:
        out['status_refusal'] = refused(s)
    if D.ok(r):
        out['report_outcome'], out['report_subjects'] = r['json']['outcome'], len(r['json']['subjects'])
        if critic.get('subject') and not r['json']['subjects']:
            plan = json.loads((ctx.layout.scout / 'exports' / 'pipeline-plan.json').read_bytes())
            software.append(f"Pipeline report has no critic subjects for its recorded workspace ({plan.get('critic_workspace')}); "
                             'criticism was read from the copied workspace instead. No historical record was changed.')
    else:
        out['report_refusal'] = refused(r)
        software.append('Archived pipeline report refused on the copy: ' + out['report_refusal'])
    return out, software


def records(ctx):
    up = upstream(ctx, 'CUSTODY_CHECK', {})
    if up:
        return up
    critic_manifest = ctx.layout.critic / 'manifest.json'
    inputs = {'scout': sha_file(ctx.layout.scout / 'scout.jsonl'), 'idea': ctx.inputs['idea_id'],
              'critic': sha_file(critic_manifest) if critic_manifest.is_file() else None}
    def act():
        v = ctx.call(SCOUT, ['validate', ctx.layout.scout])
        if not D.ok(v):
            return result('FAILED', research=['Scout refused the archive copy: ' + refused(v)])
        c = ctx.call(SCOUT, ['card', ctx.layout.scout, ctx.inputs['idea_id']])
        if not D.ok(c):
            return result('FAILED', research=[f"Scout card {ctx.inputs['idea_id']} refused: " + refused(c)],
                          next_actions=['Check the idea identifier with `python -m src.research.operator plan`.'])
        view = c['json']; current = view['card']; i = current['idea']
        reviews = [r for r in view['reviews'] if r['version'] == current['version']]
        try:
            critic, critic_findings = critic_records(ctx, current['id'])
        except ValueError as error:  # e.g. a V001 critic workspace, which critic_v1 refuses rather than reinterprets
            critic, critic_findings = {'available': True, 'refusal': str(error)}, []
            software_extra = [f'Critic workspace copy refused by critic_v1: {error}']
        else:
            software_extra = []
        pipeline, software = pipeline_records(ctx, critic)
        software = software_extra + software
        fixture = 'SYNTHETIC' if current['fixture'] == 'SYNTHETIC' else 'REAL'
        hypothesis = {'idea_id': current['id'], 'version': current['version'], 'versions': len(view['history']), 'title': i['title'],
                      'lane': current['lane'], 'route': view['current_route'], 'question': i['next_step']['question'],
                      'predictor': {k: i['predictor'][k] for k in ('quantity', 'units', 'denominator')},
                      'outcome': {k: i['outcome'][k] for k in ('quantity', 'units', 'independent_measurement')},
                      'falsifier': i['falsifier']['observation'], 'main_uncertainty': i['main_uncertainty'],
                      'requirement_ids': A.requirements(i), 'source_routes': len(i['source_routes'])}
        research = [f"Scout card {current['id']} v{current['version']} ({current['lane']}, route {view['current_route']}): {i['title']}.",
                    f"{len(reviews)} human/fixture review(s), {len([f for f in view['feasibility'] if f['version'] == current['version']])} feasibility "
                    f"record(s) and {len(view['criticism'])} Scout critic record(s) for this version.", *critic_findings]
        return result('COMPLETE', {'fixture_class': fixture, 'scout_legacy_critic_records': len(view['criticism']),
                                   'archive': {'events': v['json']['events'], 'head': v['json']['head']},
                                   'hypothesis': hypothesis, 'card_sha256': view['card_sha256'],
                                   'card_artifact': artifact(ctx, f"card-{current['id']}-v{current['version']}.json", current),
                                   'reviews': [{'decision': r['decision'], 'reviewer_kind': r['reviewer']['kind'], 'approved_handoff': r['approved_handoff']} for r in reviews],
                                   'criticism': critic, 'pipeline': pipeline},
                      research=research, software=software)
    return inputs, act


def readiness(ctx):
    up = upstream(ctx, 'FORGE_RECORDS', {})
    if up:
        return up
    rec = ctx.current['FORGE_RECORDS']['summary']
    h = rec['hypothesis']
    export = ctx.layout.scout / 'exports' / f"{h['idea_id']}-v{h['version']}-handoff.json"
    # Any change to the Scout ledger or to an existing export re-runs this check against current authority.
    inputs = {'scout': sha_file(ctx.layout.scout / 'scout.jsonl'), 'card': rec['card_sha256'], 'export': sha_file(export) if export.is_file() else None}
    def act():
        current, synth = card(ctx), synthetic(ctx)
        routes = [{'publisher': r['publisher'], 'locator': r['locator'], 'state': r['state'], 'identifiable': identifiable(r, synth)}
                  for r in current['idea']['source_routes']]
        name = f"{current['id']}-v{current['version']}-handoff.json"
        path = ctx.layout.scout / 'exports' / name
        # Scout's own current-state authority (latest card, current review, feasibility and source stops), recomputed
        # every time. An earlier export is evidence of nothing unless it equals this result byte for byte.
        try:
            authoritative, recomputed_refusal = E.handoff(Archive(ctx.layout.scout).load(), current['id']), None
        except S.ScoutError as error:
            authoritative, recomputed_refusal = None, str(error)
        exported = path.is_file()
        call = ctx.call(SCOUT, ['handoff', ctx.layout.scout, current['id']]) if authoritative is None or not exported else None
        if authoritative is None:
            if call is not None and D.ok(call):
                return result('FAILED', {'handoff': 'INCONSISTENT'}, software=['Scout recomputation refused the handoff but the handoff command exported one; it is not trusted.'])
            text = refused(call) if call is not None else 'Opportunity Scout: ' + recomputed_refusal
            research = [f'Scout handoff refused: "{text}"']
            if exported:
                research.append(f'An earlier export {name} exists, but the current Scout state no longer authorises it (a later review, feasibility '
                                'record or stop); it is ignored and never used.')
            actions = []
            if not any(r['identifiable'] for r in routes):
                research.append(f"Card v{current['version']} has no identifiable source route (locator: "
                                + '; '.join(repr(r['locator']) for r in routes) + '), so READY is mechanically impossible for this version. Designed stop.')
                actions.append('OWNER decision: whether to revise the card. If so, the owner authors revision.json and personally runs '
                               f'`python -m src.research.opportunity_scout revise "{ctx.layout.scout}" revision.json` (the software decides the revision kind).')
            actions.append('HUMAN: record a SCOUT_READY_V002 feasibility assessment of the exact next-step question for an identifiable route, '
                           f'then a READY review with approved_handoff true, using `python -m src.research.opportunity_scout feasibility|review "{ctx.layout.scout}" <file>`.')
            actions.append(f'Then: `python -m src.research.operator continue {ctx.layout.run_id}`. The operator never drafts or records these.')
            return result('WAITING_FOR_HUMAN', {'handoff': 'REFUSED', 'refusal': text, 'stale_export': exported, 'routes': routes, 'reviews': rec['reviews']},
                          research=research, next_actions=actions)
        if call is not None and not D.ok(call):
            return result('FAILED', {'handoff': 'INCONSISTENT'}, software=['Scout recomputation authorises the handoff but the handoff command refused: ' + refused(call)])
        if path.read_bytes() != canonical(authoritative) + b'\n':
            return result('BLOCKED', {'handoff': 'STALE_EXPORT', 'export': name, 'authoritative_sha256': digest(authoritative)},
                          research=[f'The exported {name} differs from the handoff the current Scout state authorises (a later review, feasibility record '
                                    'or stop changed it). Scout exports are create-only and cannot be replaced; the stale file is never used.'],
                          next_actions=['HUMAN: reconcile the stale export with the later Scout records by hand, for example by recording a new card version.'])
        envelope = authoritative
        problems = [] if envelope.get('schema') == 'DISCOVERY_LAB_STARTING_PROPOSAL_V001' and envelope.get('status') == 'PROPOSAL_ONLY' \
            and envelope.get('authorises') == [] and not any(envelope.get(f) for f in HANDOFF_FLAGS) else ['handoff envelope is not a proposal-only V001 envelope']
        if envelope.get('opportunity_card_sha256') != digest(current):
            problems.append('handoff envelope is not bound to the current card version')
        kinds = {envelope['human_scout_review']['reviewer']['kind'], envelope['human_source_feasibility']['reviewer']['kind']}
        if not synth and kinds != {'HUMAN'}:
            problems.append(f'a non-human approval {sorted(kinds)} in a real archive is never treated as READY')
        if problems:
            return result('FAILED', {'handoff': 'INVALID'}, software=problems)
        approval = 'SYNTHETIC_FIXTURE_NOT_A_HUMAN_DECISION' if synth else 'HUMAN_READY_REVIEW_RECORDED_IN_SCOUT'
        return result('COMPLETE', {'handoff': 'EXPORTED' if call else 'EXPORT_VERIFIED_AGAINST_CURRENT_STATE', 'approval_class': approval, 'routes': routes,
                                   'envelope': artifact(ctx, name, envelope), 'discovery_method_proposed': envelope['discovery_method_proposed']},
                      research=[f"Scout handoff {name} matches the current Scout authority (PROPOSAL_ONLY; approval class {approval}). "
                                'It creates no campaign and authorises nothing.'])
    return inputs, act


# ------------------------------------------------------------------------------------------------- Quarry

def file_sha(spec):
    return spec['sha256'] if spec else None


def quarry_import(route, ctx):
    label = route['label']
    inputs = {'label': label, **{k: file_sha(route[k]) for k in ('registry', 'supply', 'original')}}
    up = upstream(ctx, 'FORGE_RECORDS', inputs)
    if up:
        return up
    missing = [k for k in ('registry', 'supply', 'original') if route[k] and route[k]['sha256'] == 'MISSING']
    if missing:
        return inputs, result('WAITING_FOR_EVIDENCE', {'label': label, 'missing': missing},
                              research=[f'Route {label}: supplied file(s) not found: {missing}. Nothing was imported.'])
    try:
        fixture = json.loads(Path(route['supply']['path']).read_bytes()).get('fixture')
    except (OSError, ValueError, AttributeError):
        fixture = None  # Quarry reports the malformed record itself
    if fixture is not None and (fixture == 'SYNTHETIC') != synthetic(ctx):
        return inputs, result('BLOCKED', {'label': label, 'supply_fixture': fixture},
                              research=[f'Route {label}: supply fixture {fixture} does not match this {"synthetic" if synthetic(ctx) else "real"} run; '
                                        'synthetic and real evidence are never mixed.'])
    out = ctx.layout.quarry / f'{label}-{digest(inputs)[:8]}-import'
    def act():
        changed = [k for k in ('registry', 'supply', 'original') if not unchanged(route[k])]
        if changed:
            return result('BLOCKED', {'label': label, 'changed_since_supplied': changed},
                          research=[f'Route {label}: {changed} changed or disappeared after being supplied; nothing was imported.'],
                          next_actions=['OWNER: supply the inputs again; a file is never consumed under an earlier hash.'])
        argv = ['import-file', route['registry']['path'], route['supply']['path'], *(['--file', route['original']['path']] if route['original'] else []), '--out', out]
        r = ctx.call(QUARRY, argv)
        if not D.ok(r):
            return result('BLOCKED', {'label': label, 'package': str(out), 'refusal': refused(r)},
                          research=[f'Quarry refused the import for route {label}: {refused(r)}'],
                          next_actions=['Correct the owner-supplied route or supply record and supply it again; a refused import is never retried with the same inputs.'])
        s = ctx.call(QUARRY, ['status', out])
        if not D.ok(s):
            return result('FAILED', {'label': label, 'package': str(out)}, software=['A fresh Quarry package failed its own status check: ' + refused(s)])
        j = s['json']
        changed = [k for k in ('registry', 'supply', 'original') if not unchanged(route[k])]
        if changed or (route['original'] and j['original_sha256'] != route['original']['sha256']):
            return result('BLOCKED', {'label': label, 'package': str(out), 'changed_during_import': changed or ['original']},
                          research=[f'Route {label}: the retained package does not correspond to the supplied hashes; it is kept but never exported.'])
        return result('COMPLETE', {'label': label, 'package': str(out), 'receipt': {k: j[k] for k in ('status', 'original_sha256', 'bytes', 'identity_flags', 'authenticity', 'historical_availability')},
                                   'inspection_usable': j['inspection_usable'], 'negative_record_inspectable': j['negative_record_inspectable'],
                                   'inspection_scope': j['inspection_scope'], 'source_access': j['source_access']},
                      research=[f"Route {label}: Quarry custody {j['status']} ({j['bytes']} bytes); authenticity and historical availability UNKNOWN."])
    return inputs, act


def quarry_export(route, ctx):
    label = route['label']
    up = upstream(ctx, f'QUARRY_IMPORT:{label}', {'label': label})
    if up:
        return up
    imp = ctx.current[f'QUARRY_IMPORT:{label}']; s = imp['summary']
    value, subject_ref, audit_ref = subject(ctx)
    inputs = {'label': label, 'import': imp['key'], 'inspection': file_sha(route['inspection']), 'extracted': file_sha(route['extracted_file']),
              'subject': subject_ref['sha256']}
    if s['receipt']['identity_flags']:
        return inputs, result('BLOCKED', {'label': label, 'identity_flags': s['receipt']['identity_flags']},
                              research=[f"Route {label}: identity flags {s['receipt']['identity_flags']} block export until a human reconciles the retained original."])
    if not route['inspection']:
        return inputs, result('WAITING_FOR_HUMAN', {'label': label, 'package': s['package']},
                              research=[f'Route {label}: custody complete; no human inspection record has been supplied.'],
                              next_actions=[f"HUMAN: read the retained original ({s['package']}) and write inspection.json (QUARRY_INSPECTION_V001) with exact "
                                            'byte ranges and quotes (SUPPLIED_EXTRACTION plus an extracted file for PDFs). The operator never drafts excerpts. '
                                            f'Then supply it with `python -m src.research.operator continue {ctx.layout.run_id} --evidence <file>`.'])
    if 'MISSING' in (file_sha(route['inspection']), file_sha(route['extracted_file'])):
        return inputs, result('WAITING_FOR_EVIDENCE', {'label': label}, research=[f'Route {label}: a supplied inspection or extraction file was not found.'])
    out = ctx.layout.quarry / f'{label}-{digest(inputs)[:8]}-export'
    def act():
        if not (unchanged(route['inspection']) and unchanged(route['extracted_file'])):
            return result('BLOCKED', {'label': label}, research=[f'Route {label}: the inspection or extraction changed after being supplied; nothing was exported.'])
        argv = ['export', s['package'], route['inspection']['path'], ctx.layout.run / subject_ref['path'],
                *(['--extracted-file', route['extracted_file']['path']] if route['extracted_file'] else []), '--out', out]
        r = ctx.call(QUARRY, argv)
        if not D.ok(r):
            return result('BLOCKED', {'label': label, 'refusal': refused(r)}, research=[f'Quarry refused the inspection export for route {label}: {refused(r)}'],
                          next_actions=['Correct the human-authored inspection record; invalid evidence is never exported.'])
        return validated(ctx, label, out, {'subject': subject_ref, 'subject_audit': audit_ref})
    return inputs, act


def validated(ctx, label, out, extra=None):
    v = ctx.call(QUARRY, ['validate-export', out])
    if not D.ok(v):
        return result('BLOCKED', {'label': label, 'export': str(out), 'refusal': refused(v)},
                      research=[f'Quarry export for {label} failed validation: {refused(v)}'])
    human = QIO.json_file(Path(out) / 'human-inspection.json')
    data = QIO.json_file(Path(out) / 'input.json')
    accuracy = human.get('evidence_inspection', {}).get('accuracy', 'V001_NOT_RECORDED')
    return result('COMPLETE', {'label': label, 'export': str(out), 'manifest_sha256': sha_file(Path(out) / 'manifest.json'),
                               'accuracy': accuracy, 'prospective_anvil': human['prospective_anvil'], 'excerpts': len(data['documents']),
                               'data_classification': data['data_classification'], 'subject_sha256': digest(data['subject']), **(extra or {})},
                  research=[f'Route {label}: inspection package VALID ({len(data["documents"])} excerpt(s), accuracy {accuracy}); human inspection PENDING, ready false.'])


def supplied_export(export, ctx):
    label, path = export['label'], Path(export['path'])
    manifest = path / 'manifest.json'
    inputs = {'label': label, 'path': str(path), 'manifest': sha_file(manifest) if manifest.is_file() else 'MISSING'}
    up = upstream(ctx, 'FORGE_RECORDS', inputs)
    if up:
        return up
    if inputs['manifest'] == 'MISSING':
        return inputs, result('WAITING_FOR_EVIDENCE', {'label': label}, research=[f'Supplied export {label} has no manifest at {path}.'])
    def act():
        r = validated(ctx, label, path)
        expected = digest(subject(ctx)[0])
        if r['status'] == 'COMPLETE' and r['summary']['subject_sha256'] != expected:
            return result('BLOCKED', r['summary'], research=[f"Supplied export {label} was prepared for a different subject than card "
                                                            f"{ctx.inputs['idea_id']}'s current version; Jev collections need one exact question."])
        return r
    return inputs, act


def quarry_summary(ctx):
    rows = {n: r['status'] for n, r in sorted(ctx.current.items()) if n.startswith('QUARRY_')}
    inputs = {'stages': {n: ctx.current[n]['key'] for n in rows}}
    if not rows:
        up = upstream(ctx, 'FORGE_RECORDS', inputs)
        if up:
            return up
        routes = A.source_requirements(card(ctx), synthetic(ctx))
        return inputs, result('WAITING_FOR_EVIDENCE', {'supplied_routes': 0, 'card_source_routes': routes},
                              research=['No owner-supplied Quarry evidence for this run. Quarry has no acquisition dispatcher; originals come only from the owner under separate authority.'],
                              next_actions=['OWNER: supply evidence (RESEARCH_OS_OPERATOR_EVIDENCE_V001: QUARRY_ROUTE_REGISTRY_V001 registry, QUARRY_SUPPLY_V001 supply record, '
                                            'the original file or null for an UNAVAILABLE route) with '
                                            f'`python -m src.research.operator continue {ctx.layout.run_id} --evidence <file>`.'])
    statuses = set(rows.values())
    done = [n for n, s in rows.items() if n.startswith('QUARRY_EXPORT:') and s == 'COMPLETE']
    pending = [s for s in ('FAILED', 'INTERRUPTED', 'WAITING_FOR_HUMAN', 'WAITING_FOR_EVIDENCE', 'BLOCKED') if s in statuses]
    status = 'COMPLETE' if done and not pending else 'FAILED' if 'FAILED' in pending or 'INTERRUPTED' in pending else pending[0] if pending else 'BLOCKED'
    return inputs, result(status, {'stages': rows, 'validated_exports': len(done)})


# ------------------------------------------------------------------------------------------------- Jev and Armoury

def jev_checks(prep, first, second, records):
    problems = []
    if prep['json'].get('provider_activated') is not False or prep['json'].get('authorises') != []:
        problems.append('Jev prepare did not report provider_activated false and authorises []')
    rep = first['json']
    if first['json'] != second['json']:
        problems.append('two Jev reports of the same pinned bundle differ (non-deterministic)')
    if [r['id'] for r in rep['inspection_queue']] != rep['baseline_order'] and rep['model_status'] == 'NOT_IMPORTED_DETERMINISTIC_ONLY':
        problems.append('deterministic inspection queue differs from the keyword baseline order')
    if rep['model_status'] != 'NOT_IMPORTED_DETERMINISTIC_ONLY' or rep['authorises'] != [] or rep['discarded_records'] != []:
        problems.append('Jev report imported a response, discarded records or claimed authority')
    if records is not None and len(rep['inspection_queue']) != records:
        problems.append(f'Jev queue holds {len(rep["inspection_queue"])} records, expected {records}')
    return problems


def jev_evidence(ctx):
    found = exports(ctx)
    inputs = {'exports': [[label, sha] for label, _, sha in found]}
    if not found:
        r = ctx.current.get('QUARRY_EVIDENCE')
        status = r['status'] if r and r['status'] in WAITING else 'WAITING_FOR_EVIDENCE'
        return inputs, result(status, {'depends_on': 'QUARRY_EVIDENCE'}, research=['No validated Quarry inspection package to navigate.'])
    fp = digest(inputs)[:8]
    def act():
        if len(found) == 1:
            source = Path(found[0][1]) / 'input.json'
        else:
            collection = ctx.layout.jev_provider / f'collection-{fp}'
            c = ctx.call(JEVI, ['compose-quarry', *[e for _, e, _ in found], '--out', collection])
            if not D.ok(c):
                return result('BLOCKED', {'refusal': refused(c)}, research=['Jev refused to combine the Quarry exports: ' + refused(c)])
            source = collection / 'input.json'
        ws = ctx.layout.jev / f'evidence-{fp}'
        prep = ctx.call(JEV, ['prepare', source, '--out', ws])
        if not D.ok(prep):
            return result('BLOCKED', {'refusal': refused(prep)}, research=['Jev refused the evidence bundle: ' + refused(prep)])
        first, second = ctx.call(JEV, ['report', ws]), ctx.call(JEV, ['report', ws])
        if not (D.ok(first) and D.ok(second)):
            return result('FAILED', software=['Jev report refused a freshly prepared bundle: ' + refused(first if not D.ok(first) else second)])
        total = sum(ctx.current[f'QUARRY_EXPORT:{label}']['summary']['excerpts'] for label, _, _ in found)
        problems = jev_checks(prep, first, second, total)
        queue = [{'id': r['id'], 'source_id': r['source_id'], 'availability': r['availability'], 'relevance': r['relevance_summary'],
                  'keyword_overlap': r['ordering_basis']['keyword_overlap'], 'location': r['citation']['location']} for r in first['json']['inspection_queue']]
        return result('FAILED' if problems else 'COMPLETE', {'workspace': str(ws), 'request_sha256': first['json']['request_sha256'],
                                                             'model_status': first['json']['model_status'], 'queue': queue},
                      research=[f"Jev deterministic evidence queue ({len(queue)} records, keyword baseline, no provider): "
                                + ', '.join(f"{q['id']} [{q['availability']}]" for q in queue)], software=problems,
                      next_actions=['HUMAN: inspect each queued location in the retained copy; relevance is a navigation lead, not a measurement.'])
    return inputs, act


def jev_memory(ctx):
    up = upstream(ctx, 'FORGE_RECORDS', {})
    if up:
        return up
    value, subject_ref, _ = subject(ctx)
    cls = 'SYNTHETIC' if synthetic(ctx) else 'LOCAL_PRIVATE'
    inputs = {'subject': subject_ref['sha256'], 'catalogue': sha_file(C.CATALOGUE_PATH), 'classification': cls}
    fp = digest(inputs)[:8]
    def act():
        cat, issues = C.load(C.CATALOGUE_PATH, root=ROOT)
        if issues:
            return result('FAILED', software=[f'Memory catalogue has {len(issues)} citation issue(s); retrieval refused.'])
        memory_subject, dropped = A.memory_subject(value, set(C.requirement_ids(cat)))
        data = {'schema': J.INPUT, 'task': 'MEMORY_NAVIGATOR', 'data_classification': cls, 'subject': memory_subject,
                'catalogue': {'base': 'REPOSITORY', 'path': C.CATALOGUE_PATH.relative_to(ROOT).as_posix(), 'sha256': sha_file(C.CATALOGUE_PATH)}}
        ref = artifact(ctx, f'jev-memory-{fp}/input.json', data)
        ws = ctx.layout.jev / f'memory-{fp}'
        prep = ctx.call(JEV, ['prepare', ctx.layout.run / ref['path'], '--out', ws])
        if not D.ok(prep):
            return result('BLOCKED', {'refusal': refused(prep)}, research=['Jev memory navigation refused: ' + refused(prep)])
        first, second = ctx.call(JEV, ['report', ws]), ctx.call(JEV, ['report', ws])
        if not (D.ok(first) and D.ok(second)):
            return result('FAILED', software=['Jev memory report refused a freshly prepared bundle.'])
        problems = jev_checks(prep, first, second, None)
        rows = [{'id': r['id'], 'title': r['title'], 'connection': r['connection'], 'shared_requirements': r['shared_requirements'],
                 'exact_references': len(r['exact_document_references']) + len(r['exact_entity_references']),
                 'keyword_overlap': r['ordering_basis']['keyword_overlap']} for r in first['json']['inspection_queue']]
        related = [r for r in rows if r['connection'] != 'UNSUPPORTED_ASSOCIATION']
        research = [f"Armoury memory (catalogue {cat['version']}): " + ('; '.join(f"{r['id']} {r['connection']} {r['shared_requirements']}" for r in related)
                                                                       if related else 'no shared requirement or exact reference.')
                    + ' Connectivity only: never economic transmission or corroboration.']
        if dropped:
            research.append(f'Requirement identifiers not defined in the memory catalogue were left out of memory retrieval: {dropped}.')
        return result('FAILED' if problems else 'COMPLETE', {'workspace': str(ws), 'catalogue_version': cat['version'], 'records': rows,
                                                             'dropped_requirement_ids': dropped}, research=research, software=problems)
    return inputs, act


def armoury(ctx):
    up = upstream(ctx, 'FORGE_RECORDS', {})
    if up:
        return up
    reqs, terms = A.requirements(card(ctx)['idea']), ctx.inputs['search_terms']
    inputs = {'requirements': reqs, 'terms': terms, 'catalogue': sha_file(C.CATALOGUE_PATH)}
    def act():
        out, research, software = {'same_gap': {}, 'search': {}}, [], []
        for req in reqs:
            r = ctx.call(GRAPH, ['same-gap', f'requirement:{req}', '--json'])
            if not D.ok(r) or not isinstance(r['json'], dict):
                out['same_gap'][req] = {'refusal': refused(r)}; research.append(f'Graph same-gap {req}: {refused(r)}'); continue
            j = r['json']
            if j.get('banner') != 'DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY':
                software.append(f'Graph output for {req} lacks the derived-view banner')
            matches = sorted({x['origin'] for x in j['results']})
            out['same_gap'][req] = {'results': len(j['results']), 'connection_summary': j['connection_summary'], 'origins': matches}
            cs = j['connection_summary']
            research.append(f"Armoury same-gap {req}: {cs['methodological_warnings']} methodological warning(s) {matches}, "
                            f"{cs['economic_connection_candidates']} economic connection candidate(s).")
        for term in terms:
            r = ctx.call(GRAPH, ['search', term, '--json'])
            out['search'][term] = {'results': len(r['json']['results']), 'abstentions': r['json']['abstentions']} if D.ok(r) and isinstance(r['json'], dict) else {'refusal': refused(r)}
        return result('COMPLETE', out, research=research, software=software)
    return inputs, act


# ------------------------------------------------------------------------------------------------- Anvil

def drafts(ctx):
    up = upstream(ctx, 'FORGE_RECORDS', {})
    if up:
        return up
    ready = ctx.current.get('FORGE_READINESS') or {}
    envelope = ready['summary']['envelope'] if ready.get('status') == 'COMPLETE' else None
    found = exports(ctx)
    fixture = 'SYNTHETIC' if synthetic(ctx) else 'LIVE'
    inputs = {'handoff': envelope['sha256'] if envelope else None, 'exports': [[label, sha] for label, _, sha in found], 'fixture': fixture}
    fp = digest({**inputs, 'binding': ctx.epoch})[:8]  # a re-evaluation under accepted new code writes new drafts
    def act():
        parts, research = {'candidate': None, 'source_passports': {}}, []
        if envelope:
            env = load_artifact(ctx, envelope)
            draft, audit = A.candidate(env, fixture)
            parts['candidate'] = {'draft': artifact(ctx, f'drafts-{fp}/candidate.draft.json', draft), 'audit': artifact(ctx, f'drafts-{fp}/candidate.audit.json', audit),
                                  'source_requirements': artifact(ctx, f'drafts-{fp}/source-requirements.json', A.source_requirements(env['opportunity_card'], fixture == 'SYNTHETIC')),
                                  'validation': draft['validation'], 'audit_counts': audit['counts'], 'record_id': draft['record']['id']}
            research.append(f"Candidate draft {draft['record']['id']}: single-record contract {draft['validation']['single_record_contract']}; "
                            f"mapping {audit['counts']}.")
        else:
            parts['candidate'] = {'status': 'NOT_DRAFTED', 'reason': 'No approved Scout handoff: drafting a Discovery candidate without READY would bypass the handoff gate.'}
            research.append('No candidate draft: the Scout handoff gate has not passed.')
        for label, export, sha in found:
            prov, insp = QIO.json_file(Path(export) / 'provenance.json'), QIO.json_file(Path(export) / 'inspection.json')
            draft, audit = A.passport(prov, insp, sha, fixture)
            parts['source_passports'][label] = {'draft': artifact(ctx, f'drafts-{fp}/source-{label}.draft.json', draft),
                                                'audit': artifact(ctx, f'drafts-{fp}/source-{label}.audit.json', audit),
                                                'validation': draft['validation'], 'audit_counts': audit['counts'], 'record_id': draft['record']['id']}
            research.append(f"Source Passport draft {draft['record']['id']} from route {label}: contract {draft['validation']['single_record_contract']}; mapping {audit['counts']}.")
        actions = ['HUMAN: inspect every draft field against its audit (COPIED, TRANSFORMED, MISSING, UNRESOLVED); drafts are never appended by the operator.',
                   'OWNER: a LIVE Discovery campaign needs a committed owner authority document (docs/strategy/owner_<...>.md) before any record is added.']
        drafted = bool(envelope) + len(found)
        return result('WAITING_FOR_HUMAN', parts, research=research, next_actions=actions if drafted else [],
                      blockers=[f'{drafted} draft mapping(s) await human inspection; none is a ledger record.'] if drafted
                      else ['No candidate draft: the Scout handoff gate has not passed.'])
    return inputs, act


def ledger_checks(ctx, ledger, candidate, version, classification, label):
    """Discovery validate/checklist/source, Jev workflow navigation and Graph trace over one pinned ledger copy."""
    out, research, software = {'ledger': str(ledger), 'label': label}, [], []
    v = ctx.call(DISCOVERY, ['validate', ledger])
    if not D.ok(v):
        return result('BLOCKED', out, research=[f'Discovery refused the {label} ledger: {refused(v)}'])
    state = Ledger(ledger).load()
    c = ctx.call(DISCOVERY, ['checklist', ledger, candidate, *(['--version', version] if version else [])])
    if not D.ok(c):
        return result('BLOCKED', out, research=[f'Discovery checklist refused: {refused(c)}'])
    check = c['json']
    if check.get('software_certifies_M') is not False:
        return result('FAILED', out, software=['checklist did not report software_certifies_M false'])
    out['checklist'] = {k: {'mechanical': r['mechanical'], 'blockers': r['blockers']} for k, r in check['requirements'].items()}
    out.update(gaps=check['gaps'], h_gaps=check['h_gaps'], next=check['next'], frozen=check['frozen'])
    out['sources'] = {}
    for sid in sorted(state.versions['source'])[:16]:
        s = ctx.call(DISCOVERY, ['source', ledger, sid])
        out['sources'][sid] = s['json']['next_rung'] if D.ok(s) else refused(s)
    latest = state.latest('candidate', candidate)
    value, _, _ = subject(ctx)
    workflow = {'schema': J.INPUT, 'task': 'WORKFLOW_NAVIGATOR', 'data_classification': classification, 'subject': value,
                'context': {'ledger': {'base': 'INPUT', 'path': ledger.name, 'sha256': sha_file(ledger)}, 'candidate_id': candidate,
                            'candidate_version': latest['version'], 'experiment_id': None, 'stops': [], 'context_files': []}}
    ref = write_once(ledger.parent / 'workflow-input.json', workflow)
    ws = ctx.layout.jev / f"workflow-{digest(workflow)[:8]}"
    prep = ctx.call(JEV, ['prepare', ref, '--out', ws]) if not ws.exists() else {'fault': None, 'exit_code': 0}  # create-only; report re-verifies it
    if D.ok(prep):
        rep = ctx.call(JEV, ['report', ws])
        if D.ok(rep):
            out['workflow'] = {'effective_bottleneck': rep['json']['effective_bottleneck'], 'next_question': rep['json']['next_question'],
                               'model_can_override_deterministic': rep['json']['model_can_override_deterministic']}
    else:
        software.append('Jev workflow navigation refused the ledger: ' + refused(prep))
    mode = 'synthetic' if state.fixture == 'SYNTHETIC' else 'prospective' if state.fixture == 'LIVE' else 'memory'
    t = ctx.call(GRAPH, ['trace', candidate, '--mode', mode, '--ledgers', ledger, '--json'])
    out['graph_trace'] = {'mode': mode, 'banner': t['json'].get('banner') if D.ok(t) and isinstance(t['json'], dict) else None,
                          'refusal': None if D.ok(t) else refused(t)}
    blocked = {k: r['blockers'] for k, r in out['checklist'].items() if r['blockers']}
    research.append(f"Discovery checklist ({label}): " + ('; '.join(f'{k}: {", ".join(b)}' for k, b in blocked.items()) if blocked else
                                                          'no mechanical blocker; a human M review is required') + '. Software never certifies M.')
    if out.get('workflow'):
        research.append(f"Jev workflow bottleneck: {out['workflow']['effective_bottleneck']} - {out['workflow']['next_question']}")
    return result('BLOCKED' if blocked else 'WAITING_FOR_HUMAN', out, research=research, software=software, blockers=research[:1],
                  next_actions=[f"Next evidence: {check['next']['requirement']} / {check['next']['blocker']}.",
                                'HUMAN: Measurement Gate M and H reviews and every disposition are human records only.'])


def claim_comparison(current, candidate):
    """Mechanical text comparison of claim-defining fields. Identical wording is never economic identity."""
    i = current['idea']
    pairs = {'predictor': (i['predictor']['quantity'], candidate['predictor']['quantity']), 'outcome': (i['outcome']['quantity'], candidate['outcome']['quantity']),
             'population': (i['entity_class'], candidate['population']), 'mechanism': (A.mechanism_text(i['mechanism']), candidate['mechanism'])}
    return {k: 'IDENTICAL_TEXT' if a == b else 'DIFFERENT_TEXT' for k, (a, b) in pairs.items()}


def identity(ctx, ledger_sha, candidate):
    current, ready = card(ctx), ctx.current.get('FORGE_READINESS') or {}
    return {'scout': {'idea_id': current['id'], 'version': current['version'], 'card_sha256': digest(current),
                      'handoff_sha256': ready['summary']['envelope']['sha256'] if ready.get('status') == 'COMPLETE' else None},
            'discovery': {'ledger_sha256': ledger_sha, 'candidate_id': candidate['id'], 'candidate_version': candidate['version'],
                          'candidate_sha256': digest(candidate)}}


def crosswalk_problems(value, expected, synth):
    """A human-authored binding is checked mechanically for identities and form; its judgment is the human's."""
    if not isinstance(value, dict) or set(value) != CROSSWALK_KEYS or value.get('schema') != CROSSWALK:
        return [f'not a {CROSSWALK} record with exactly the fields {sorted(CROSSWALK_KEYS)}']
    problems = [f'{side} binding differs from this run: expected {expected[side]}' for side in ('scout', 'discovery') if value[side] != expected[side]]
    if not (isinstance(value['scout'], dict) and value['scout'].get('handoff_sha256') and expected['scout']['handoff_sha256']):
        problems.append('a crosswalk must bind a current Scout handoff (handoff_sha256), never null')
    if value['mapping_status'] not in MAPPINGS:
        problems.append(f'mapping_status must be one of {MAPPINGS}')
    reviewer = value['reviewer'] if isinstance(value['reviewer'], dict) else {}
    if set(reviewer) != {'kind', 'name'} or reviewer.get('kind') != ('SYNTHETIC_FIXTURE' if synth else 'HUMAN'):
        problems.append('a crosswalk is a human record (reviewer kind HUMAN; SYNTHETIC_FIXTURE only in synthetic runs)')
    name = reviewer.get('name')
    if not isinstance(name, str) or not name.strip() or name.strip().upper() == 'PENDING' or ASSISTANT.search(name):
        problems.append('the reviewer must be a named person, never PENDING, an assistant or a model')
    if not isinstance(value['reviewed_at'], str) or not value['reviewed_at'].strip() or value['reviewed_at'] == 'PENDING':
        problems.append('reviewed_at is required')
    return problems


def supplied_checks(ctx, supplied):
    cross, synth = supplied.get('crosswalk'), synthetic(ctx)
    ready = ctx.current.get('FORGE_READINESS') or {}
    inputs = {'ledger': supplied['sha256'], 'candidate': supplied['candidate_id'], 'version': supplied['candidate_version'],
              'crosswalk': cross['sha256'] if cross else None, 'card': ctx.current['FORGE_RECORDS']['summary']['card_sha256'],
              'handoff': ready['summary']['envelope']['sha256'] if ready.get('status') == 'COMPLETE' else None}
    if ready.get('status') != 'COMPLETE':
        status = ready.get('status', 'NOT_RUN')
        return inputs, result('WAITING_FOR_HUMAN', {'link': 'UNLINKED_NO_CURRENT_HANDOFF', 'readiness': status},
                              research=[f'A supplied Discovery candidate is never admitted as a continuation of this Forge idea without a currently '
                                        f'valid Scout handoff; FORGE_READINESS is {status}. The ledger was not linked and no crosswalk was evaluated.'],
                              next_actions=['Pass the Scout READY gate first (see FORGE_READINESS); a crosswalk must then bind the exported handoff by hash.'])
    if supplied['sha256'] == 'MISSING' or (cross and cross['sha256'] == 'MISSING'):
        return inputs, result('WAITING_FOR_EVIDENCE', research=['The supplied ledger or crosswalk file was not found.'])
    fp = digest(inputs)[:8]
    def act():
        data = Path(supplied['path']).read_bytes() if Path(supplied['path']).is_file() else None
        if data is None or hashlib.sha256(data).hexdigest() != supplied['sha256']:
            return result('BLOCKED', {'link': 'NOT_EVALUATED'}, research=['The supplied ledger changed or disappeared after being supplied; it was not read.'])
        copy = write_once(ctx.layout.artifacts / f'anvil-ledger-{fp}' / 'ledger.jsonl', data)
        try:
            state = Ledger(copy).load()
        except ValueError as error:
            return result('BLOCKED', {'link': 'NOT_EVALUATED'}, research=[f'Discovery refused the supplied ledger: {error}'])
        if (state.fixture == 'SYNTHETIC') != synth:
            return result('BLOCKED', {'link': 'NOT_EVALUATED'}, research=[f'Supplied ledger fixture {state.fixture} does not match this run; synthetic and real classes are never mixed.'])
        cand = state.version('candidate', supplied['candidate_id'], supplied['candidate_version'])
        if cand is None:
            return result('BLOCKED', {'link': 'NOT_EVALUATED'}, research=[f"Candidate {supplied['candidate_id']} is not in the supplied ledger."])
        expected, comparison = identity(ctx, supplied['sha256'], cand), claim_comparison(card(ctx), cand)
        if not cross:
            template = artifact(ctx, f'anvil-ledger-{fp}/crosswalk-template.json',
                                {'schema': CROSSWALK, **expected, 'mapping_status': 'PENDING_HUMAN_REVIEW', 'reviewer': {'kind': 'PENDING', 'name': 'PENDING'},
                                 'reviewed_at': 'PENDING', 'notes': 'PENDING'})
            same = all(v == 'IDENTICAL_TEXT' for v in comparison.values())
            return result('WAITING_FOR_HUMAN', {'link': 'UNLINKED', 'binding': expected, 'claim_text_comparison': comparison, 'crosswalk_template': template},
                          research=[f"Supplied candidate {cand['id']} v{cand['version']} is UNLINKED to Scout card {expected['scout']['idea_id']} "
                                    f"v{expected['scout']['version']}: no human crosswalk binds them, so its checklist is not presented as a continuation "
                                    'of this Forge idea.' + (' Identical wording on every claim field is still not economic identity.' if same else '')],
                          next_actions=['HUMAN: compare the card with the candidate. If they are the same claim or a reformulation, author a '
                                        f'{CROSSWALK} record yourself (the template in the run artifacts holds only the mechanical identities), then '
                                        f'`python -m src.research.operator continue {ctx.layout.run_id} --ledger <ledger> --candidate {cand["id"]} --crosswalk <file>`.'])
        raw = Path(cross['path']).read_bytes() if Path(cross['path']).is_file() else None
        if raw is None or hashlib.sha256(raw).hexdigest() != cross['sha256']:
            return result('BLOCKED', {'link': 'NOT_EVALUATED'}, research=['The supplied crosswalk changed or disappeared after being supplied; it was not read.'])
        try:
            problems = crosswalk_problems(json.loads(raw), expected, synth)
        except ValueError as error:
            problems = [f'crosswalk is not valid JSON: {error}']
        if problems:
            return result('BLOCKED', {'link': 'CROSSWALK_INVALID', 'problems': problems, 'binding': expected},
                          research=['The supplied crosswalk does not bind this Forge card to this candidate: ' + '; '.join(problems)])
        r = ledger_checks(ctx, copy, cand['id'], supplied['candidate_version'], 'SYNTHETIC' if synth else 'LOCAL_PRIVATE', 'supplied (pinned copy)')
        r['summary']['link'] = {'status': 'SYNTHETIC_CROSSWALK_FIXTURE' if synth else 'HUMAN_CROSSWALK_RECORDED', 'binding': expected,
                                'mapping_status': json.loads(raw)['mapping_status'], 'crosswalk_sha256': cross['sha256'], 'claim_text_comparison': comparison,
                                'meaning': 'A named human asserts the binding; the operator verified only identities, hashes and form.'}
        return r
    return inputs, act


def anvil_checks(ctx):
    supplied = ctx.inputs['ledger']
    up = upstream(ctx, 'FORGE_RECORDS', {'ledger': supplied['sha256'] if supplied else None})
    if up:
        return up
    if supplied:
        return supplied_checks(ctx, supplied)
    d = ctx.current.get('ANVIL_DRAFTS') or {}
    cand = (d.get('summary') or {}).get('candidate') or {}
    summary = d.get('summary') or {}
    # Content, never an upstream CHECK key: a re-evaluated but unchanged draft never re-runs this ONE_SHOT preview.
    inputs = {'candidate': (cand.get('draft') or {}).get('sha256'), 'synthetic': synthetic(ctx), 'status': d.get('status'),
              'sources': {k: v['draft']['sha256'] for k, v in sorted((summary.get('source_passports') or {}).items())}}
    if not synthetic(ctx):
        return inputs, result('WAITING_FOR_HUMAN', {'ledger': None, 'link': 'NO_LEDGER'},
                              research=['No Discovery ledger exists for this hypothesis. The operator never creates a LIVE campaign or appends records.'],
                              next_actions=['OWNER: commit a campaign authority document; a human authors the campaign, source, observation and candidate records '
                                            'and a crosswalk binding the candidate to this card, then supply them with '
                                            f'`python -m src.research.operator continue {ctx.layout.run_id} --ledger <file> --candidate CAND-... --crosswalk <file>`.'])
    if not cand.get('draft') or cand['validation']['single_record_contract'] != 'VALID':
        return inputs, result('WAITING_FOR_HUMAN', {'ledger': None}, research=['No valid candidate draft to preview.'])
    def act():
        root = ctx.layout.artifacts / f"anvil-preview-{digest(inputs)[:8]}"
        draft = load_artifact(ctx, cand['draft'])
        campaign = A.preview_campaign(ctx.layout.run_id, draft['record']['method'], card(ctx)['idea']['next_step']['question'])
        ledger = root / 'ledger.jsonl'
        steps = [['init', ledger, write_once(root / 'campaign.json', campaign)]]
        for label, p in sorted(d['summary']['source_passports'].items()):
            if p['validation']['single_record_contract'] == 'VALID':
                steps.append(['add', ledger, 'source', write_once(root / f'source-{label}.json', load_artifact(ctx, p['draft'])['record'])])
        steps.append(['add', ledger, 'candidate', write_once(root / 'candidate.json', draft['record'])])
        for argv in steps:
            r = ctx.call(DISCOVERY, argv, preview=True)
            if not D.ok(r):
                return result('BLOCKED', research=['Synthetic preview refused by Discovery: ' + refused(r)])
        r = ledger_checks(ctx, ledger, draft['record']['id'], None, 'SYNTHETIC', 'SYNTHETIC preview')
        r['summary']['preview'] = 'SYNTHETIC_FIXTURE_ONLY_NOT_RESEARCH_EVIDENCE'
        r['summary']['link'] = {'status': 'MECHANICAL_DRAFT_FROM_HANDOFF', 'handoff_sha256': (ctx.current['FORGE_READINESS']['summary']['envelope'] or {}).get('sha256'),
                                'card_sha256': ctx.current['FORGE_RECORDS']['summary']['card_sha256'], 'candidate_id': draft['record']['id']}
        return r
    return inputs, act


# ------------------------------------------------------------------------------------------------- boundaries

BOUNDARIES = {'Crucible, Whetstone, Temper or Battle promotion': 'NOT_AUTHORISED', 'Backtests, paper or live trading': 'NOT_AUTHORISED',
              'Live Jev provider (TypeSafe)': 'NOT_AUTHORISED', 'Hosted or paid model calls (generation, critics)': 'NOT_AUTHORISED',
              'Quarry acquisition dispatcher': 'NOT_IMPLEMENTED', 'PDF/OCR extraction': 'NOT_IMPLEMENTED',
              'Level A analysis runner': 'NOT_IMPLEMENTED', 'Automatic Armoury ingestion of run records': 'NOT_IMPLEMENTED'}


def downstream(ctx):
    return {'version': VERSION}, result('NOT_AUTHORISED', {'boundaries': BOUNDARIES},
                                        software=[f'{k}: {v}' for k, v in BOUNDARIES.items() if v == 'NOT_IMPLEMENTED'],
                                        research=['Nothing is promoted beyond Anvil drafts and checks by this profile.'])


def integrity(ctx):
    """Read-only diagnostic, run every invocation (even after a failure or boundary violation)."""
    inputs = {'invocation': ctx.invocation_seq}
    def act():
        checks = {}
        custody = next((r for k, r in ctx.results.items() if k.startswith('FORGE_CUSTODY@') and r['status'] == 'COMPLETE'), None)
        s = (custody or {}).get('summary') or {}
        if s.get('original'):
            checks['original archive'] = 'UNCHANGED' if tree(s['original']['path'])['digest'] == s['original']['digest'] else 'CHANGED'
        if s.get('critic', {}).get('digest'):
            checks['original critic workspace'] = 'UNCHANGED' if tree(s['critic']['path'])['digest'] == s['critic']['digest'] else 'CHANGED'
        for route in ctx.inputs['routes']:
            for k in ('registry', 'supply', 'original', 'inspection', 'extracted_file'):
                if route[k] and route[k]['sha256'] != 'MISSING':
                    checks[f"{route['label']} {k}"] = 'UNCHANGED' if unchanged(route[k]) else 'CHANGED'
        supplied = ctx.inputs['ledger']
        for k, spec in (('supplied ledger', supplied), ('supplied crosswalk', (supplied or {}).get('crosswalk'))):
            if spec and spec['sha256'] != 'MISSING':
                checks[k] = 'UNCHANGED' if unchanged(spec) else 'CHANGED'
        changed = sorted(k for k, v in checks.items() if v != 'UNCHANGED')
        return result('FAILED' if changed else 'COMPLETE', {'checks': checks, 'custody_recorded': custody is not None},
                      software=[f'Supplied original changed during the run: {changed}'] if changed else [])
    return inputs, act


