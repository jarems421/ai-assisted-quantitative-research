"""Reproducible synthetic rehearsal; static fixtures are never described as AI generation."""
from __future__ import annotations

from pathlib import Path
import tempfile

from src.research.spec import canonical, digest
from . import engine as E, schema as S, workflow as W
from .fixtures import MOMENT, idea, seed, provenance, negative_controls, feasibility
from .storage import Archive, ROOT
from .evaluation import report, protocol


def control_results():
    rows = []
    for case in negative_controls():
        error = None
        try:
            if 'seed' in case: S.validate_seed(case['seed'])
            else: S.validate_idea(case['idea'], case['lane'], {}, {})
        except (ValueError, TypeError) as problem: error = str(problem)
        rows.append({'id': case['id'], 'valid': error is None, 'expected_schema_valid': case['schema_expected_valid'],
            'structural_warnings': S.structural_checks(case['idea'])['checks'] if 'idea' in case else [],
            'error': error, 'human_judgment': 'NOT_PROVIDED', 'fixture': 'SYNTHETIC'})
        if case['id'] == 'PARAPHRASED_DUPLICATE':
            state = E.State(); state.cards = {'IDEA-BASE': [{'id': 'IDEA-BASE', 'version': 1, 'idea': idea()}]}
            rows[-1]['proximity'] = E.proximity(state, {'id': 'IDEA-CONTROL', 'version': 1, 'idea': case['idea']})
    return rows


def run(out=None, *, write=False):
    with tempfile.TemporaryDirectory() as td:
        archive = Archive(Path(td) / 'synthetic-scout')
        W.initialise(archive, 'SYNTHETIC end-to-end rehearsal', fixture='SYNTHETIC', with_memory=True, moment=MOMENT)
        archive.append('seed', seed(), recorded_at=MOMENT)
        lanes = [('FORGE', ['WORKING_CAPITAL', 'COMPLEMENT_DEMAND']),
                 ('RADAR', ['CAPACITY_COMPETITION', 'LIABILITY_TRANSFER']),
                 ('GAP', ['REGULATORY_ASYMMETRY', 'MAINTENANCE_OBLIGATION'])]
        # All prompts are prepared before fixture output exists. Forge receives no source or memory context.
        requests = [(lane, families, W.prepare(archive, lane, 2, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)) for lane, families in lanes]
        for lane, families, (aid, prompt) in requests:
            raw = canonical({'ideas': [idea(family, lane, index) for index, family in enumerate(families)]}).decode()
            W.finish(archive, aid, raw, provenance(), raw_import=raw, moment=MOMENT)
        state = archive.load()
        for card in [v[-1] for v in state.cards.values()]:
            archive.append('assessment', E.assess(archive.load(), card), recorded_at=MOMENT)
        ready = next(v[-1] for v in state.cards.values() if v[-1]['lane'] == 'RADAR')
        archive.append('feasibility', feasibility(ready), recorded_at=MOMENT)
        review = {'readiness_version': 'SCOUT_READY_V002', 'idea_id': ready['id'], 'version': 1, 'decision': 'READY', 'reason_type': 'RESEARCHABLE',
            'reason': 'SYNTHETIC WORKFLOW DEMONSTRATION ONLY; no real human review or scientific outcome.',
            'uncertainties': ['All economic premises and sources are fictional.'],
            'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'}, 'minutes': S.UNKNOWN,
            'approved_handoff': True, 'reconsider_when': 'Real review would need real evidence and separate owner authority.',
            'authorises_acquisition': False}
        archive.append('review', review, recorded_at=MOMENT)
        state = archive.load(); archive.append('selection', E.select(state), recorded_at=MOMENT)
        state = archive.load()
        handoff = E.handoff(state, ready['id'])
        result = {'schema': 'SCOUT_SYNTHETIC_DEMONSTRATION_V001', 'fixture': 'SYNTHETIC',
            'model_calls': 0, 'scientific_source_requests': 0, 'real_human_reviews': 0,
            'protocol_sha256': digest(protocol()), 'report': report(state),
            'cards': [v[-1] for v in state.cards.values()], 'handoff': handoff,
            'negative_controls': control_results(), 'ledger_sha256': digest(state.events),
            'authority': 'NONE; synthetic software rehearsal only'}
        if out:
            target = Archive(out)
            if target.file.exists(): raise S.ScoutError('demo output archive already exists; choose a new directory')
            target.path.mkdir(parents=True, exist_ok=True)
            with target.file.open('xb') as handle: handle.write(archive.file.read_bytes())
            target.export('synthetic-report.json', result)
        if write:
            target = ROOT / 'docs/opportunity_scout/synthetic_demo.json'
            target.write_bytes(canonical(result) + b'\n')
        return result
