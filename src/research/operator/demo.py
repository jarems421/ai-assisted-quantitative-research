"""UNMISTAKABLY SYNTHETIC end-to-end demonstration of the operator. No real archive, evidence, approval or result.

A fictional Scout archive holds one READY FORGE card (synthetic fixture reviewer, never a human decision) and one
RADAR card without review. Fictional Quarry inputs supply one retained text original and one UNAVAILABLE route with a recorded
stop. The run first stops waiting for evidence; ``continue`` then carries the chain through Quarry, deterministic Jev,
draft Anvil mappings and a SYNTHETIC preview checklist, and still stops at human gates."""
from __future__ import annotations

import json
from pathlib import Path

from src.research.spec import canonical
from src.research.opportunity_scout import engine as E, fixtures as F, workflow as W
from src.research.opportunity_scout.storage import Archive

MOMENT = F.MOMENT


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else canonical(value))
    return path


def scout_archive(target):
    """Synthetic Scout batch: a READY FORGE card and an unreviewed RADAR card. Returns (archive, ready_id, unreviewed_id)."""
    archive = Archive(target)
    W.initialise(archive, 'SYNTHETIC operator demonstration', fixture='SYNTHETIC', with_memory=False, moment=MOMENT)
    archive.append('seed', F.seed(), recorded_at=MOMENT)
    for lane, family in (('FORGE', 'CAPACITY_COMPETITION'), ('RADAR', 'WORKING_CAPITAL')):
        aid, _ = W.prepare(archive, lane, 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
        raw = canonical({'ideas': [F.idea(family, lane, 0)]}).decode()
        W.finish(archive, aid, raw, F.provenance(), raw_import=raw, moment=MOMENT)
    state = archive.load()
    for card in [v[-1] for v in state.cards.values()]:
        archive.append('assessment', E.assess(archive.load(), card), recorded_at=MOMENT)
    ready = next(v[-1] for v in state.cards.values() if v[-1]['lane'] == 'FORGE')
    other = next(v[-1] for v in state.cards.values() if v[-1]['lane'] == 'RADAR')
    archive.append('feasibility', F.feasibility(ready), recorded_at=MOMENT)
    archive.append('review', {'readiness_version': 'SCOUT_READY_V002', 'idea_id': ready['id'], 'version': 1, 'decision': 'READY',
                              'reason_type': 'RESEARCHABLE', 'reason': 'SYNTHETIC WORKFLOW DEMONSTRATION ONLY; no real human review.',
                              'uncertainties': ['All economic premises and sources are fictional.'],
                              'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'}, 'minutes': 'UNKNOWN',
                              'approved_handoff': True, 'reconsider_when': 'A real review needs real evidence and owner authority.',
                              'authorises_acquisition': False}, recorded_at=MOMENT)
    return archive, ready['id'], other['id']


def quarry_inputs(root, card):
    """Fictional registry, supplies, one UTF-8 original, inspections and the evidence file naming them."""
    root = Path(root)
    route = card['idea']['source_routes'][0]
    text = ('SYNTHETIC REGISTER. Entry 1: dated allocation of 12 inspection shifts per week to customer C-1.\n'
            'Entry 2: independent invoice total for customer C-2 in the next cycle: UNKNOWN.\n').encode('utf-8')
    passages = [('R1_ALLOCATION', 'dated allocation of 12 inspection shifts per week to customer C-1'),
                ('R1_INVOICE', 'independent invoice total for customer C-2 in the next cycle: UNKNOWN')]
    common = {'publisher': route['publisher'], 'expected_fields': route['fields'], 'question': card['idea']['next_step']['question'],
              'access_restrictions': [], 'originality_claim': 'ORIGINAL', 'expected_asset': 'allocation register',
              'availability_uncertainties': ['Fictional source; no historical availability.']}
    routes = [{**common, 'id': 'SYN-REGISTER', 'version': '1', 'locator': route['locator'], 'expected_source_identity': 'register-1', 'stops': []},
              {**common, 'id': 'SYN-INVOICES', 'version': '1', 'locator': 'https://records.synthetic.invalid/invoices/next-cycle',
               'expected_source_identity': 'invoices-1',
               'stops': [{'id': 'SYN-STOP-1', 'scope': 'host', 'reason': 'Fictional recorded access stop', 'citation': 'synthetic fixture', 'citation_sha256': 'UNKNOWN'}]}]
    write(root / 'registry.json', {'schema': 'QUARRY_ROUTE_REGISTRY_V001', 'routes': routes})
    supply = {'schema': 'QUARRY_SUPPLY_V001', 'route_version': '1', 'fixture': 'SYNTHETIC', 'data_classification': 'SYNTHETIC',
              'asset_claim': 'allocation register', 'source_version_claim': 'fictional-1', 'retrieved_at_claim': 'UNKNOWN',
              'retrieval_method_claim': 'synthetic test fixture', 'historical_availability_claim': 'UNKNOWN', 'expected_original_sha256': 'UNKNOWN'}
    write(root / 'supply-R1.json', {**supply, 'route_id': 'SYN-REGISTER', 'title': 'Fictional allocation register', 'source_identity_claim': 'register-1',
                                    'coverage': 'PARTIAL', 'limitations': ['Not a real document.'], 'missing_fields': ['independent invoice values']})
    write(root / 'supply-R2.json', {**supply, 'route_id': 'SYN-INVOICES', 'title': 'Fictional invoice ledger', 'source_identity_claim': 'invoices-1',
                                    'coverage': 'UNAVAILABLE', 'limitations': ['The fictional owner could not supply it.'], 'missing_fields': ['invoice totals']})
    write(root / 'original-R1.txt', text)
    negative = 'Fictional invoice ledger\nUNAVAILABLE\nThe fictional owner could not supply it.\ninvoice totals'.encode('utf-8')
    for label, raw, cut in (('R1', text, passages), ('R2', negative, [('R2_UNAVAILABLE', 'UNAVAILABLE')])):
        excerpts = []
        for key, passage in cut:
            start = raw.index(passage.encode('utf-8'))
            excerpts.append({'id': key, 'location': 'synthetic ' + key, 'start_byte': start, 'end_byte': start + len(passage.encode('utf-8')), 'quote': passage})
        write(root / f'inspection-{label}.json', {'schema': 'QUARRY_INSPECTION_V001', 'mode': 'ORIGINAL_UTF8',
                                                   'extraction_method_claim': 'exact UTF-8 byte ranges (synthetic fixture)', 'excerpts': excerpts})
    evidence = {'schema': 'RESEARCH_OS_OPERATOR_EVIDENCE_V001', 'routes': [
        {'label': 'R1', 'registry': 'registry.json', 'supply': 'supply-R1.json', 'original': 'original-R1.txt', 'inspection': 'inspection-R1.json'},
        {'label': 'R2', 'registry': 'registry.json', 'supply': 'supply-R2.json', 'original': None, 'inspection': 'inspection-R2.json'}]}
    return write(root / 'evidence.json', evidence)


def fixtures(root):
    """Everything the demonstration needs, under ``root`` (which must not be inside a Git checkout)."""
    root = Path(root)
    archive, ready, other = scout_archive(root / 'inputs' / 'synthetic-forge')
    card = archive.load().latest(ready)
    evidence = quarry_inputs(root / 'inputs' / 'quarry', card)
    return {'archive': archive.path, 'ready_idea': ready, 'unreviewed_idea': other, 'evidence': evidence, 'base': root / 'workspace'}


def run(out):
    from .runs import create, evidence_spec, invoke, request_value
    out = Path(out)
    if out.exists():
        raise ValueError('demonstration output directory already exists; choose a new directory')
    f = fixtures(out)
    layout = create(request_value(f['archive'], f['ready_idea'], None, None, [], None), base=f['base'], run_id='OPR-SYNTHETIC-DEMO')
    first, _ = invoke(layout, 'run')
    spec = evidence_spec(json.loads(Path(f['evidence']).read_text(encoding='utf-8')), Path(f['evidence']).parent)
    second, paths = invoke(layout, 'continue', supplied={'evidence': spec, 'search_terms': [], 'ledger': None})
    return {'fixture': 'SYNTHETIC_NOT_RESEARCH', 'run_id': layout.run_id, 'workspace': str(layout.run),
            'first_invocation': {'outcome': first['outcome'], 'first_boundary': first['first_boundary']},
            'after_evidence': {'outcome': second['outcome'], 'first_boundary': second['first_boundary'],
                               'stages': {r['stage']: r['status'] for r in second['stages']}},
            'report': [str(p) for p in paths], 'model_calls': 0, 'external_requests': 0, 'authorises': []}
