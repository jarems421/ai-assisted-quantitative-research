"""Read-only native adapters. Never import a provider, invoke a CLI, or continue a run.

The operator's INVOCATION_FINISHED event plus its reproducible retained report form
the native completion reference. The operator does not have a separate run receipt.
Only explicit operator artifact references are hashed; model/raw directories are not read.
"""
import hashlib
from pathlib import Path

from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout import engine as scout
from src.research.operator import PROFILE, runs, report
from src.research.operator.journal import Journal
from src.research.spec import canonical, digest
from .records import need, path, read, loads


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def implementation():
    files = {p.name: sha(p.read_bytes().replace(b'\r\n', b'\n')) for p in sorted(Path(__file__).parent.glob('*.py'))}
    return {'campaign': digest(files), 'native': runs.binding(runs.provenance())}


def scout_record(archive, idea_id, version, expected_hash, anchor=None):
    archive = path(archive)
    need(not (archive / '.append.lock').exists(), 'Scout writer active or interrupted')
    raw = read(archive / 'scout.jsonl')  # checks before native replay
    s = Archive(archive).load()
    need(raw == read(archive / 'scout.jsonl'), 'Scout changed during inspection')
    if anchor:
        n = anchor['scout_events']
        need(len(s.events) >= n and s.events[n - 1]['hash'] == anchor['scout_head'], 'Scout history replaced')
    cards = s.cards.get(idea_id, [])
    c = next((c for c in cards if c['version'] == version), None)
    need(c is not None and digest(c) == expected_hash, 'Scout card version/hash mismatch')
    need(cards[-1]['version'] == version, 'STALE_CARD_VERSION: register the reformulation separately')
    try:
        scout.handoff(s, idea_id)
        eligible = True
    except ValueError:
        eligible = False
    return {'archive': str(archive), 'idea_id': idea_id, 'version': version, 'card_sha256': expected_hash,
            'fixture': s.batch['fixture'], 'batch_id': s.batch['id'], 'batch_sha256': digest(s.batch),
            'scout_events': len(s.events), 'scout_head': s.events[-1]['hash'],
            'route': s.route(c), 'handoff_eligible': eligible}


def branch_current(branch):
    return scout_record(branch['archive'], branch['idea_id'], branch['version'], branch['card_sha256'], anchor=branch)


def artifact_refs(value, root):
    """Native operator profile.artifact records resolve only within this run's artifacts/."""
    refs = {}
    def visit(v):
        if isinstance(v, dict):
            if set(v) == {'path', 'sha256'}:
                rel = Path(v['path'])
                if not rel.is_absolute():
                    need(rel.parts and rel.parts[0] == 'artifacts' and '..' not in rel.parts, 'native artifact escapes run')
                    p = path(root / rel)
                    need(p.is_relative_to(root), 'native artifact escapes run')
                    need(sha(read(p)) == v['sha256'], 'native artifact changed: ' + rel.as_posix())
                    refs[rel.as_posix()] = v['sha256']
            for item in v.values():
                visit(item)
        elif isinstance(v, list):
            for item in v:
                visit(item)
    visit(value)
    return [{'path': k, 'sha256': v} for k, v in sorted(refs.items())]


def observe(root, branch, previous=None):
    root = path(root)
    need(not (root / 'journal.lock').exists(), 'native run locked; reconcile natively')
    journal_raw = read(root / 'journal.jsonl')
    events = Journal(root).load()
    if previous:
        n = previous['journal_events']
        need(len(events) >= n and events[n - 1]['hash'] == previous['journal_head'], 'native history replaced')
        for ref in previous['artifacts']:
            need(sha(read(root / ref['path'])) == ref['sha256'], 'previous native artifact changed')
    need(events[-1]['type'] == 'INVOCATION_FINISHED', 'native activity interrupted or not finished; never replay')
    created = events[0]['record']
    need(created['profile'] == PROFILE, 'unsupported native profile')
    need(created['run_id'] == root.name, 'native run identity mismatch')
    req = created['request']
    need(path(req['archive']) == path(branch['archive']) and req['idea_id'] == branch['idea_id'], 'native run belongs to another branch')
    stages = runs.current_stages(events)
    rec = stages.get('FORGE_RECORDS', {}).get('summary') or {}
    h = rec.get('hypothesis') or {}
    need(h.get('idea_id') == branch['idea_id'] and h.get('version') == branch['version']
         and rec.get('card_sha256') == branch['card_sha256'], 'native card identity mismatch')
    need((rec.get('archive') or {}).get('head') == branch_current(branch)['scout_head'],
         'STALE_NATIVE_SCOUT_RECORDS: current Scout records supersede this native view; no approval inherited')
    need((stages.get('INTEGRITY', {}).get('status') == 'COMPLETE'), 'native integrity check incomplete')
    refs = artifact_refs(events, root)
    head = events[-1]['hash']
    candidates = [root / 'reports' / f'report-{head[:16]}{suffix}.json' for suffix in ('-v002', '')]
    saved = next((p for p in candidates if p.is_file()), None)
    need(saved is not None, 'native report not finalised; reconcile natively, never regenerate here')
    raw = read(saved); retained = loads(raw)
    derived = report.render(events, schema=retained['schema'])
    need(canonical(retained) == canonical(derived), 'native report differs from journal')
    refs.append({'path': saved.relative_to(root).as_posix(), 'sha256': sha(raw)})
    need(journal_raw == read(root / 'journal.jsonl') and not (root / 'journal.lock').exists(), 'native run changed during inspection')
    return {'run': str(root), 'run_id': created['run_id'], 'journal_events': len(events), 'journal_head': head,
            'receipt': {'event': 'INVOCATION_FINISHED', 'seq': events[-1]['seq'], 'hash': head},
            'artifacts': refs, 'binding': runs.bound(events)}, derived
