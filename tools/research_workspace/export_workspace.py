"""Offline, deterministic presentation export. No discovery, pilot or acquisition commands.

Every input is a fixed tracked public file. Crucially, build(ledgers=[]) never discovers
campaigns: active pilot arms, snapshots, keys and private archives are outside this adapter.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

APP = Path(__file__).resolve().parent
ROOT = APP.parents[1]
sys.path.insert(0, str(ROOT))

CATALOGUE = 'docs/strategy/graph/research_memory_catalogue_v002.json'
OLD_CATALOGUE = 'docs/strategy/graph/research_memory_catalogue.json'
REPORTS = frozenset({
    'docs/strategy/discovery_bottleneck_receipt.json',
    'docs/strategy/discovery_bottleneck_report.md',
    'docs/strategy/frontier_selection_ii_receipt.json',
    'docs/strategy/frontier_selection_ii_report.md',
    'docs/strategy/measurement_gate_campaign_cards.md',
    'docs/strategy/measurement_gate_campaign_ledger.json',
    'docs/strategy/measurement_gate_campaign_report.md',
    'docs/strategy/salmon_verification_final_report.md',
    'docs/strategy/salmon_verification_receipt_v002.json',
    'docs/strategy/sh09_verification_receipt.json',
    'docs/strategy/sh09_verification_report.md',
})
EXPERIMENT_DOCS = (
    ('EXP001', 'reports/EXP001_final_report.md'),
    ('EXP002', 'experiments/EXP002/research/final_freeze_review.md'),
    ('EXP003', 'experiments/EXP003/research/final_freeze_review.md'),
    ('EXP004', 'docs/acceleration/exp004_execution_gap_report.md'),
    ('EXP005', 'docs/acceleration/phase3_final_report.md'),
    ('EXP006', 'docs/acceleration/exp006_cover_identity_report.md'),
    ('EXP007', 'docs/acceleration/exp007_house_repair_report.md'),
)
EXTRA = frozenset(p for _, p in EXPERIMENT_DOCS) | {'docs/strategy/graph_v1_review_validation.json'}
ALLOWED = REPORTS | EXTRA | {CATALOGUE, OLD_CATALOGUE}


def file_hash(data):
    return hashlib.sha256(data).hexdigest()


def safe_read(relative, root=ROOT):
    """Exact allowlist, tracked regular file, no symlink/reparse escape, bounded size."""
    if relative not in ALLOWED:
        raise ValueError('Input is outside the fixed public-file allowlist')
    root = root.resolve()
    path = root / relative
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked input paths are refused')
    if not path.resolve().is_relative_to(root) or not path.is_file() or path.stat().st_size > 3_000_000:
        raise ValueError('Input must be a bounded regular file within this checkout')
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', relative], cwd=root,
                             capture_output=True, check=False)
    if tracked.returncode:
        raise ValueError('Input must be tracked')
    return path.read_bytes()


def make_export():
    # Validate all paths before the existing catalogue loader can read its citations.
    raw = {p: safe_read(p) for p in sorted(ALLOWED)}
    catalogue = json.loads(raw[CATALOGUE])
    if set(catalogue.get('report_hashes', {})) != REPORTS or catalogue.get('supersedes', {}).get('path') != OLD_CATALOGUE:
        raise ValueError('Catalogue input contract changed: review the fixed allowlist before export')
    def citations(value):
        if isinstance(value, dict):
            if 'path' in value and value['path'] not in REPORTS | {OLD_CATALOGUE}:
                raise ValueError('Unapproved citation path')
            for child in value.values(): citations(child)
        elif isinstance(value, list):
            for child in value: citations(child)
    citations(catalogue)

    from src.research.graph.catalogue import load
    from src.research.graph.project import build
    from src.research.graph import model as M, operators as O
    from src.research.graph.rules import View

    cat, issues = load(ROOT / CATALOGUE, root=ROOT)
    g = build(ledgers=[], catalogue_path=ROOT / CATALOGUE, mode='memory')
    view = View(history=True)
    investigations = []
    for inv in cat['investigations']:
        nid = 'history:' + inv['id']
        investigations.append({**inv, 'node': nid, 'citation_status': cat['_citation_status'][inv['id']],
                               'trace': O.trace(g, nid, view), 'gaps': O.gaps(g, nid, view),
                               'shared': O.shared(g, nid, view)})

    nodes = {nid: {**n, 'search_text': O.searchable(n)} for nid, n in sorted(g.nodes.items())}
    neighbourhoods = {nid: {str(limit): O.neighbourhood(g, nid, view, limit=limit)
                           for limit in (8, 16, 30)} for nid in nodes}
    # Explanations are bounded Graph v1 operator outputs, never frontend inference.
    explanations = {}
    for inv in investigations:
        nid = inv['node']
        targets = neighbourhoods[nid]['30']['results'][0]['nodes']
        for target in targets:
            if target != nid:
                explanations[nid + '\n' + target] = O.explain(g, nid, target, view)
    for e in g.edges:
        key = e['src'] + '\n' + e['dst']
        if key not in explanations:
            explanations[key] = O.explain(g, e['src'], e['dst'], view)

    documents = {p: {'path': p, 'sha256': file_hash(raw[p]), 'text': raw[p].decode('utf-8'),
                     'expected_sha256': cat['report_hashes'].get(p),
                     'status': ('CURRENT' if file_hash(raw[p]) == cat['report_hashes'][p] else 'HASH_CHANGED')
                     if p in cat['report_hashes'] else 'TRACKED_DOCUMENT'}
                 for p in sorted(REPORTS | EXTRA)}
    validation = json.loads(raw['docs/strategy/graph_v1_review_validation.json'])
    return {
        'schema': 'RESEARCH_WORKSPACE_V1', 'banner': M.BANNER,
        'scope': 'HISTORICAL_MEMORY_ONLY',
        'catalogue': {'version': cat['version'], 'recorded_at_utc': cat['recorded_at_utc'],
                      'path': CATALOGUE, 'sha256': file_hash(raw[CATALOGUE]),
                      'mapping_review': cat['mapping_review']},
        'graph_digest': g.digest(), 'nodes': nodes, 'edges': g.edges,
        'investigations': investigations, 'requirements': cat['requirements'],
        'neighbourhoods': neighbourhoods, 'explanations': explanations,
        'same_gap': {r['id']: O.same_gap(g, r['id'], view) for r in cat['requirements']},
        'operators': {'changes': O.changes(g, view), 'next': O.next_questions(g, view),
                      'failures': O.failures(g, view), 'orphans': O.orphans(g, view)},
        'documents': documents, 'issues': issues + g.issues,
        'experiments': [{'id': eid, 'path': path} for eid, path in EXPERIMENT_DOCS],
        'campaigns': [], 'pilot': None,
        'software_validation': {'status': validation['status'], 'graph_tests': validation['graph_tests'],
                                'recorded_at_utc': validation['recorded_at_utc'],
                                'path': 'docs/strategy/graph_v1_review_validation.json'},
        'input_hashes': {p: file_hash(data) for p, data in sorted(raw.items())},
        'limits': ['No campaign ledgers, packet snapshots, blind keys or arm-specific records were read.',
                   'Live and synthetic scopes are empty in this export; no claim about other branches is made.',
                   'Historical memory creates no original observations or verified economic relationships.',
                   'Requirement mappings remain pending human review.'],
    }


def write_export():
    public = APP / 'public'
    if public.is_symlink() or (hasattr(public, 'is_junction') and public.is_junction()):
        raise ValueError('Linked output directory refused')
    public.mkdir(exist_ok=True)
    target = public / 'workspace.json'
    if target.is_symlink() or (hasattr(target, 'is_junction') and target.is_junction()):
        raise ValueError('Linked output file refused')
    data = make_export()
    # Replace atomically: an existing hardlink is unlinked, never overwritten through.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=public, suffix='.tmp', delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        except BaseException:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Exported {len(data['investigations'])} investigations, {len(data['nodes'])} nodes; no ledgers read.")


if __name__ == '__main__':
    write_export()
