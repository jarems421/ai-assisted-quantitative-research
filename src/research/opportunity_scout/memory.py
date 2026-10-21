"""Fixed public historical memory only. Explicit empty ledger list excludes every pilot arm."""
from pathlib import Path

from src.research.spec import digest
from .schema import ScoutError, json_loads
from .storage import ROOT, unlinked

CATALOGUE = 'docs/strategy/graph/research_memory_catalogue_v002.json'
REPORTS = frozenset('''discovery_bottleneck_receipt.json discovery_bottleneck_report.md
frontier_selection_ii_receipt.json frontier_selection_ii_report.md measurement_gate_campaign_cards.md
measurement_gate_campaign_ledger.json measurement_gate_campaign_report.md salmon_verification_final_report.md
salmon_verification_receipt_v002.json sh09_verification_receipt.json sh09_verification_report.md'''.split())


def snapshot():
    from src.research.graph.catalogue import load
    from src.research.graph.project import build
    from src.research.graph.operators import same_gap
    from src.research.graph.rules import View
    path = unlinked(ROOT / CATALOGUE)
    raw = json_loads(path.read_text(encoding='utf-8'))
    allowed = {f'docs/strategy/{name}' for name in REPORTS}
    if set(raw['report_hashes']) != allowed: raise ScoutError('historical memory path contract changed; review required')
    for relative in allowed | {raw['supersedes']['path']}:
        if relative != 'docs/strategy/graph/research_memory_catalogue.json' and relative not in allowed:
            raise ScoutError('unapproved catalogue path')
        unlinked(ROOT / relative)
    cat, issues = load(path)
    if issues or any(s != 'CURRENT' for s in cat['_citation_status'].values()):
        raise ScoutError('historical citations changed; do not silently refresh them')
    graph = build(ledgers=[], catalogue_path=path, mode='memory')
    investigations = {}
    for inv in cat['investigations']:
        findings = [f for f in inv['findings'] if f['requirement']]
        investigations[inv['id']] = {'id': inv['id'], 'title': inv['title'], 'verdict': inv['verdict'],
            'requirements': sorted({f['requirement'] for f in findings}), 'findings': findings,
            'claims': inv['claims'],
            'closed_source_routes': [{'locator': d['locator'], 'http_status': d['http_status'], 'receipt': d['receipt'],
                                      'scope': 'CLOSED_HISTORICAL_INVESTIGATION_NO_REOPENING_AUTHORITY'} for d in inv['documents']],
            'report_sha256': cat['report_hashes'][inv['report']], 'report': inv['report'],
            'citation_status': cat['_citation_status'][inv['id']], 'authority': 'HISTORICAL_MEMORY_ONLY'}
    return {'schema': 'SCOUT_MEMORY_V001', 'catalogue_sha256': __import__('hashlib').sha256(path.read_bytes()).hexdigest(),
            'recorded_at': cat['recorded_at_utc'], 'graph_digest': graph.digest(), 'investigations': investigations,
            'same_gap': {r['id']: same_gap(graph, r['id'], View()) for r in cat['requirements']},
            'mapping_review': cat['mapping_review'], 'ledgers_read': [], 'creates_original_observations': False}
