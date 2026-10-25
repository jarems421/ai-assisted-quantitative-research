"""Research OS operator V001 on SYNTHETIC fixtures only: temporary archives, fictional Quarry inputs, no network,
process, model, credential or human judgment. Real Pilot 001 coverage is the separate local-only module."""
import contextlib
import copy
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import fixtures as F
from src.research.opportunity_scout.automation_v001 import execution as X
from src.research.opportunity_scout.storage import Archive
from src.research.operator import adapters as A, cli, delegate as D, demo, profile, report as RP, runs
from src.research.operator.guard import Boundary, BoundaryViolation, resolved
from src.research.operator.journal import Journal, JournalError

REVISION = {'commit': 'UNKNOWN', 'ref': 'UNKNOWN', 'basis': 'TEST_FIXTURE', 'reason': 'git metadata is not read in tests'}


def read_tree(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in sorted(Path(path).rglob('*')) if p.is_file()}


class OperatorTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.f = demo.fixtures(self.root)
        p = patch.object(X, 'revision', return_value=REVISION); p.start(); self.addCleanup(p.stop)

    def evidence(self, value=None, name='evidence.json'):
        path = self.root / 'inputs' / 'quarry' / name
        if value is not None:
            path.write_bytes(canonical(value))
        return runs.evidence_spec(json.loads(path.read_text(encoding='utf-8')), path.parent)

    def start(self, idea=None, evidence=None, run_id='OPR-TEST', **kw):
        request = runs.request_value(self.f['archive'], idea or self.f['ready_idea'], None, evidence, kw.get('search', []), kw.get('ledger'))
        layout = runs.create(request, base=self.f['base'], run_id=run_id)
        rep, _ = runs.invoke(layout, 'run')
        return layout, rep

    def more(self, layout, evidence=None, ledger=None):
        supplied = {'evidence': evidence or {'routes': [], 'exports': []}, 'search_terms': [], 'ledger': ledger} if evidence or ledger else None
        return runs.invoke(layout, 'continue', supplied=supplied)[0]

    def stages(self, layout):
        return runs.current_stages(Journal(layout.run).load())

    def started(self, layout):
        return [e['record']['key'] for e in Journal(layout.run).load() if e['type'] == 'STAGE_STARTED']

    def test_refused_handoff_is_preserved_without_any_human_record(self):
        before = read_tree(self.f['archive'])
        layout, rep = self.start(self.f['unreviewed_idea'])
        s = self.stages(layout)
        self.assertEqual(s['FORGE_READINESS']['status'], 'WAITING_FOR_HUMAN')
        self.assertEqual(s['FORGE_READINESS']['summary']['refusal'],
                         'Opportunity Scout: handoff needs an explicit human READY review approving this exact version')
        self.assertFalse(list((layout.scout / 'exports').glob('*handoff*')) if (layout.scout / 'exports').exists() else [])
        self.assertEqual(s['ANVIL_DRAFTS']['summary']['candidate']['status'], 'NOT_DRAFTED')
        self.assertEqual(rep['outcome'], 'STOPPED_AT_BOUNDARY')
        self.assertEqual(rep['first_boundary']['stage'], 'FORGE_READINESS')
        events = Archive(layout.scout).load().events
        self.assertEqual([e['type'] for e in events], [e['type'] for e in Archive(self.f['archive']).load().events])
        self.assertEqual(read_tree(self.f['archive']), before)
        self.assertTrue(any(a.startswith('HUMAN') for a in rep['human_decisions']))
        self.assertEqual(rep['authorises'], [])

    def test_original_archive_unchanged_and_working_copy_byte_identical(self):
        before = read_tree(self.f['archive'])
        layout, rep = self.start(evidence=self.evidence())
        self.assertEqual(read_tree(self.f['archive']), before)
        self.assertEqual(read_tree(layout.scout)['scout.jsonl'], before['scout.jsonl'])
        s = self.stages(layout)
        self.assertTrue(s['FORGE_CUSTODY']['summary']['byte_identical'])
        self.assertEqual(s['INTEGRITY']['summary']['checks']['original archive'], 'UNCHANGED')
        self.assertEqual(rep['integrity']['original archive'], 'UNCHANGED')
        for name in ('original-R1.txt', 'registry.json', 'inspection-R1.json'):
            self.assertTrue((self.root / 'inputs' / 'quarry' / name).is_file())
        self.assertTrue(all(Path(p).is_relative_to(self.f['base']) for p in layout.value().values()))

    def test_complete_synthetic_chain_stops_at_human_gates(self):
        layout, first = self.start()
        self.assertEqual(first['first_boundary']['stage'], 'QUARRY_EVIDENCE')
        self.assertEqual(first['first_boundary']['status'], 'WAITING_FOR_EVIDENCE')
        rep = self.more(layout, self.evidence())
        s = self.stages(layout)
        for name in ('FORGE_READINESS', 'QUARRY_IMPORT:R1', 'QUARRY_EXPORT:R1', 'QUARRY_IMPORT:R2', 'QUARRY_EXPORT:R2', 'JEV_EVIDENCE', 'JEV_MEMORY', 'ARMOURY_GRAPH'):
            self.assertEqual(s[name]['status'], 'COMPLETE', name)
        self.assertEqual(s['ANVIL_DRAFTS']['status'], 'WAITING_FOR_HUMAN')
        self.assertEqual(s['ANVIL_CHECKS']['status'], 'BLOCKED')
        self.assertEqual(s['DOWNSTREAM']['status'], 'NOT_AUTHORISED')
        self.assertEqual(rep['outcome'], 'STOPPED_AT_BOUNDARY')
        self.assertNotIn(rep['outcome'], ('COMPLETE', 'SUCCESS'))
        queue = s['JEV_EVIDENCE']['summary']['queue']
        self.assertEqual({q['id']: q['availability'] for q in queue}, {'R1_ALLOCATION': 'SUPPLIED_COPY', 'R1_INVOICE': 'SUPPLIED_COPY', 'R2_UNAVAILABLE': 'STOPPED'})
        self.assertEqual(s['JEV_EVIDENCE']['summary']['model_status'], 'NOT_IMPORTED_DETERMINISTIC_ONLY')
        check = s['ANVIL_CHECKS']['summary']
        self.assertEqual(check['preview'], 'SYNTHETIC_FIXTURE_ONLY_NOT_RESEARCH_EVIDENCE')
        self.assertIn('NO_PREDICTOR_OBSERVATION', check['checklist']['distinctive_predictor']['blockers'])
        self.assertIn('UNKNOWN_UNITS:predictor', check['checklist']['meaning_and_units']['blockers'])
        self.assertIn('NO_INDEPENDENT_OUTCOME', check['checklist']['separate_outcome']['blockers'])
        self.assertTrue(all(r['mechanical'] == 'BLOCKED' for r in check['checklist'].values()))
        self.assertEqual(check['sources']['SRC-SYN-INVOICES'], 'STOP_ROUTE')
        self.assertEqual(check['sources']['SRC-SYN-REGISTER'], 'OBTAIN_ONE_ORIGINAL_RECORD')
        self.assertEqual(check['workflow']['model_can_override_deterministic'], False)
        self.assertEqual(rep['accounting']['boundary_denials'], 0)
        self.assertEqual(rep['accounting']['operator_model_or_provider_calls'], 0)

    def test_synthetic_approval_is_never_promoted_to_a_human_decision(self):
        layout, _ = self.start(evidence=self.evidence())
        s = self.stages(layout)
        self.assertEqual(s['FORGE_RECORDS']['summary']['fixture_class'], 'SYNTHETIC')
        self.assertEqual(s['FORGE_READINESS']['summary']['approval_class'], 'SYNTHETIC_FIXTURE_NOT_A_HUMAN_DECISION')
        drafts = s['ANVIL_DRAFTS']['summary']
        draft = json.loads((layout.run / drafts['candidate']['draft']['path']).read_bytes())
        self.assertEqual((draft['fixture'], draft['appended'], draft['authorises']), ('SYNTHETIC', False, []))
        self.assertIn('SYNTHETIC FIXTURE RUN', RP.markdown(RP.render(Journal(layout.run).load())))
        # The coordinator's own check: a non-human approval in a real-class archive is never READY.
        layout2 = runs.create(runs.request_value(self.f['archive'], self.f['ready_idea'], None, None, [], None), base=self.f['base'], run_id='OPR-TEST-REAL')
        real = lambda ctx: False
        with patch.object(profile, 'synthetic', real):
            runs.invoke(layout2, 'run')
        r = self.stages(layout2)['FORGE_READINESS']
        self.assertEqual(r['status'], 'FAILED')
        self.assertIn("a non-human approval ['SYNTHETIC_FIXTURE'] in a real archive is never treated as READY", r['software_findings'])

    def test_continue_never_replays_one_shot_stages(self):
        layout, _ = self.start(evidence=self.evidence())
        keys = self.started(layout)
        imports = sorted(p.name for p in layout.quarry.iterdir())
        copy_bytes = read_tree(layout.scout)
        self.more(layout)
        self.more(layout, self.evidence())  # the same inputs again
        later = [e['record'] for e in Journal(layout.run).load() if e['type'] == 'STAGE_STARTED'][len(keys):]
        self.assertEqual([r['key'] for r in later if r['kind'] == 'ONE_SHOT'], [])
        # Only per-invocation checks and one re-verification of the export written by the first invocation.
        self.assertEqual({r['stage'] for r in later} - {'PREFLIGHT', 'CUSTODY_CHECK', 'INTEGRITY', 'FORGE_READINESS'}, set())
        self.assertEqual(sorted(p.name for p in layout.quarry.iterdir()), imports)
        self.assertEqual(read_tree(layout.scout), copy_bytes)
        one_shot = [k for k in keys if k.split('@')[0] in ('FORGE_CUSTODY', 'JEV_EVIDENCE', 'JEV_MEMORY') or k.startswith('QUARRY_')]
        self.assertEqual(len(one_shot), len(set(one_shot)))

    def test_interrupted_one_shot_stage_is_never_retried(self):
        layout = runs.create(runs.request_value(self.f['archive'], self.f['ready_idea'], None, self.evidence(), [], None), base=self.f['base'], run_id='OPR-TEST-CRASH')
        real = D.call
        def crash(module, argv, **kw):
            if argv[0] == 'import-file':
                raise KeyboardInterrupt('simulated crash after the claim')
            return real(module, argv, **kw)
        with patch.object(D, 'call', crash), self.assertRaises(KeyboardInterrupt):
            runs.invoke(layout, 'run')
        self.assertEqual(cli.status(layout)['outcome'], 'INTERRUPTED')
        calls = []
        def spy(module, argv, **kw):
            calls.append([str(x) for x in argv]); return real(module, argv, **kw)
        with patch.object(D, 'call', spy):
            rep = self.more(layout)
        imports = [c for c in calls if c[0] == 'import-file']
        self.assertEqual(len(imports), 1)  # R2's first import; R1's interrupted claim is never retried
        self.assertTrue(imports[0][2].endswith('supply-R2.json'))
        s = self.stages(layout)
        self.assertEqual(s['QUARRY_IMPORT:R1']['status'], 'INTERRUPTED')
        self.assertIn(s['QUARRY_EXPORT:R1']['status'], ('SKIPPED',))
        self.assertEqual(rep['outcome'], 'INTERRUPTED')

    def test_missing_input_and_invalid_evidence_fabricate_nothing(self):
        bad = json.loads((self.root / 'inputs/quarry/evidence.json').read_text(encoding='utf-8'))
        bad['routes'][0]['original'] = 'missing-original.txt'
        layout, rep = self.start(evidence=self.evidence(bad, 'missing.json'), run_id='OPR-TEST-MISSING')
        s = self.stages(layout)
        self.assertEqual(s['QUARRY_IMPORT:R1']['status'], 'WAITING_FOR_EVIDENCE')
        self.assertFalse(any(p.name.startswith('R1-') for p in layout.quarry.iterdir()))
        self.assertNotIn('R1', s['ANVIL_DRAFTS']['summary']['source_passports'])
        # Off-by-one excerpt: Quarry's own refusal is preserved and nothing is exported.
        inspection = json.loads((self.root / 'inputs/quarry/inspection-R1.json').read_text(encoding='utf-8'))
        inspection['excerpts'][0]['end_byte'] += 1
        (self.root / 'inputs/quarry/inspection-R1-bad.json').write_bytes(canonical(inspection))
        ev = json.loads((self.root / 'inputs/quarry/evidence.json').read_text(encoding='utf-8'))
        ev['routes'][0]['inspection'] = 'inspection-R1-bad.json'
        layout, rep = self.start(evidence=self.evidence(ev, 'bad-inspection.json'), run_id='OPR-TEST-BAD')
        s = self.stages(layout)
        self.assertEqual(s['QUARRY_EXPORT:R1']['status'], 'BLOCKED')
        self.assertIn('excerpt must reproduce exact retained UTF-8 byte range', s['QUARRY_EXPORT:R1']['summary']['refusal'])
        self.assertFalse(any(p.name.startswith('R1-') and p.name.endswith('-export') for p in layout.quarry.iterdir()))
        self.assertEqual([q['id'] for q in s['JEV_EVIDENCE']['summary']['queue']], ['R2_UNAVAILABLE'])
        # Wrong asset claim: identity flag blocks export.
        supply = json.loads((self.root / 'inputs/quarry/supply-R1.json').read_text(encoding='utf-8'))
        (self.root / 'inputs/quarry/supply-R1-wrong.json').write_bytes(canonical({**supply, 'asset_claim': 'another asset'}))
        ev = json.loads((self.root / 'inputs/quarry/evidence.json').read_text(encoding='utf-8'))
        ev['routes'] = [{**ev['routes'][0], 'supply': 'supply-R1-wrong.json'}]
        layout, _ = self.start(evidence=self.evidence(ev, 'wrong.json'), run_id='OPR-TEST-WRONG')
        s = self.stages(layout)
        self.assertEqual(s['QUARRY_EXPORT:R1']['summary']['identity_flags'], ['WRONG_ASSET_CLAIM_MISMATCH'])
        self.assertEqual(s['JEV_EVIDENCE']['status'], 'BLOCKED')
        # Real-class evidence in a synthetic run is refused before custody.
        (self.root / 'inputs/quarry/supply-R1-real.json').write_bytes(canonical({**supply, 'fixture': 'OWNER_SUPPLIED', 'data_classification': 'LOCAL_PRIVATE'}))
        ev['routes'] = [{**ev['routes'][0], 'supply': 'supply-R1-real.json'}]
        layout, _ = self.start(evidence=self.evidence(ev, 'real.json'), run_id='OPR-TEST-MIX')
        self.assertEqual(self.stages(layout)['QUARRY_IMPORT:R1']['status'], 'BLOCKED')
        self.assertFalse(layout.quarry.exists())
        # Unknown idea: Forge records fail, everything downstream is skipped, nothing is drafted.
        layout, rep = self.start('IDEA-doesnotexist', run_id='OPR-TEST-UNKNOWN')
        s = self.stages(layout)
        self.assertEqual(s['FORGE_RECORDS']['status'], 'FAILED')
        self.assertEqual({s[n]['status'] for n in ('FORGE_READINESS', 'JEV_MEMORY', 'ANVIL_DRAFTS')}, {'SKIPPED'})
        self.assertEqual(rep['outcome'], 'FAILED')

    def test_observation_first_preview_refusal_is_preserved(self):
        archive = Archive(self.f['archive'])
        radar = archive.load().latest(self.f['unreviewed_idea'])
        archive.append('feasibility', F.feasibility(radar), recorded_at=F.MOMENT)
        review = {'readiness_version': 'SCOUT_READY_V002', 'idea_id': radar['id'], 'version': 1, 'decision': 'READY', 'reason_type': 'RESEARCHABLE',
                  'reason': 'SYNTHETIC ONLY; no real human review.', 'uncertainties': ['Fictional.'], 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'},
                  'minutes': 'UNKNOWN', 'approved_handoff': True, 'reconsider_when': 'Never real.', 'authorises_acquisition': False}
        archive.append('review', review, recorded_at=F.MOMENT)
        layout, _ = self.start(self.f['unreviewed_idea'], run_id='OPR-TEST-RADAR')
        r = self.stages(layout)['ANVIL_CHECKS']
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertIn('OBSERVATION_FIRST must start from a recorded observation', r['research_findings'][0])

    def test_draft_mapping_never_removes_a_mechanical_blocker(self):
        layout, _ = self.start(evidence=self.evidence())
        d = self.stages(layout)['ANVIL_DRAFTS']['summary']
        cand = json.loads((layout.run / d['candidate']['draft']['path']).read_bytes())['record']
        audit = json.loads((layout.run / d['candidate']['audit']['path']).read_bytes())
        for path in (('predictor', 'units'), ('outcome', 'units'), ('outcome', 'route'), ('public_time_route',), ('horizon',), ('information_event', 'description')):
            value = cand
            for k in path:
                value = value[k]
            self.assertEqual(value, 'UNKNOWN', path)
        self.assertTrue(cand['exposure']['allocation_required'])
        self.assertEqual({j['status'] for j in cand['joins'].values()}, {'UNVERIFIED'})
        self.assertEqual(cand['predictor']['observation_ids'], [])
        rows = {r['field']: r for r in audit['rows']}
        self.assertEqual(rows['predictor.units']['source_value'], 'inspection shifts')
        self.assertEqual(rows['predictor.units']['class'], 'UNRESOLVED')
        self.assertEqual(set(audit['counts']), set(A.CLASSES))
        source = json.loads((layout.run / d['source_passports']['R1']['draft']['path']).read_bytes())['record']
        self.assertEqual({q['depth'] for q in source['quantities']}, {'UNVERIFIED'})
        self.assertEqual({q['units'] for q in source['quantities']}, {'UNKNOWN'})
        self.assertEqual(source['quantities'][0]['evidence'][0]['depth'], 'UNVERIFIED')
        stopped = json.loads((layout.run / d['source_passports']['R2']['draft']['path']).read_bytes())['record']
        self.assertEqual(stopped['access']['status'], 'BLOCKED')
        self.assertTrue(any(o.startswith('STOP SYN-STOP-1') for o in stopped['omissions']))
        with self.assertRaisesRegex(ValueError, 'mapping drift'):
            A.Audit('X', {}).copied('f', 's', 'a', 'b')

    def test_report_is_deterministic_from_retained_records(self):
        layout, rep = self.start(evidence=self.evidence())
        events = Journal(layout.run).load()
        self.assertEqual(canonical(RP.render(events)), canonical(RP.render(copy.deepcopy(events))))
        self.assertEqual(canonical(rep), canonical(RP.render(events)))
        moved = self.root / 'moved'
        shutil.copytree(layout.run, moved)
        self.assertEqual(RP.markdown(RP.render(Journal(moved).load())), RP.markdown(rep))
        saved = layout.reports / f"report-{rep['journal_head'][:16]}.md"
        self.assertEqual(saved.read_bytes(), RP.markdown(rep).encode('utf-8'))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(['--base', str(self.f['base']), 'report', layout.run_id, '--json'])
        self.assertEqual(json.loads(out.getvalue())['journal_head'], rep['journal_head'])

    def test_journal_tamper_and_lock_are_refused(self):
        layout, _ = self.start()
        (layout.run / 'journal.lock').write_bytes(b'')
        with self.assertRaisesRegex(JournalError, 'run is locked'):
            runs.invoke(layout, 'continue')
        (layout.run / 'journal.lock').unlink()
        raw = (layout.run / 'journal.jsonl').read_bytes()
        (layout.run / 'journal.jsonl').write_bytes(raw.replace(b'"COMPLETE"', b'"FAILED"', 1))
        with self.assertRaisesRegex(JournalError, 'chain broken'):
            Journal(layout.run).load()
        with self.assertRaisesRegex(runs.OperatorError, 'already exists'):
            runs.create(runs.request_value(self.f['archive'], self.f['ready_idea'], None, None, [], None), base=self.f['base'], run_id='OPR-TEST')

    # ---------------------------------------------------------------------------------- Forge-to-Anvil binding

    def unrelated_ledger(self):
        from src.research.discovery import records as R
        from src.research.discovery.ledger import Ledger
        campaign = {'id': 'DLC-UNRELATED', 'title': 'SYNTHETIC unrelated campaign', 'method': 'HYPOTHESIS_FIRST', 'fixture': 'SYNTHETIC',
                    'question': 'An unrelated fictional question?', 'authority': 'SYNTHETIC', 'acquisition_authorized': False,
                    'budget': {'analyst_hours': 0, 'source_starts': 0, 'external_bytes': 0}, 'notes': []}
        cand = R.template('candidate')
        cand.update(id='CAND-UNRELATED', method='HYPOTHESIS_FIRST', population='Unrelated fictional cohort', mechanism='Unrelated fictional mechanism',
                    falsification='Unrelated fictional falsifier.')
        cand['predictor']['quantity'], cand['outcome']['quantity'] = 'Unrelated fictional predictor', 'Unrelated fictional outcome'
        path = self.root / 'inputs' / 'unrelated.jsonl'
        Ledger.create(path, campaign).append('candidate', cand)
        return path

    def crosswalk(self, layout, name='crosswalk.json', **override):
        template = json.loads(next(layout.artifacts.glob('anvil-ledger-*/crosswalk-template.json')).read_bytes())
        value = {**template, 'mapping_status': 'HUMAN_REVIEWED_SAME_CLAIM', 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'name': 'SYNTHETIC_REVIEWER'},
                 'reviewed_at': F.MOMENT, 'notes': 'SYNTHETIC fixture binding; no real human judgment.', **override}
        path = self.root / 'inputs' / name
        path.write_bytes(canonical(value))
        return path

    def test_supplied_ledger_needs_a_human_crosswalk_to_the_forge_card(self):
        first, _ = self.start(evidence=self.evidence(), run_id='OPR-TEST-PREVIEW')
        ledger = self.root / 'inputs' / 'ledger.jsonl'
        shutil.copyfile(next(first.artifacts.glob('anvil-preview-*')) / 'ledger.jsonl', ledger)
        before, cid = ledger.read_bytes(), 'CAND-' + self.f['ready_idea']
        layout, _ = self.start(evidence=self.evidence(), run_id='OPR-TEST-LEDGER', ledger=runs.ledger_spec(ledger, cid, None))
        r = self.stages(layout)['ANVIL_CHECKS']
        self.assertEqual((r['status'], r['summary']['link']), ('WAITING_FOR_HUMAN', 'UNLINKED'))
        self.assertNotIn('checklist', r['summary'])
        self.assertEqual(set(r['summary']['claim_text_comparison'].values()), {'IDENTICAL_TEXT'})
        self.assertIn('Identical wording on every claim field is still not economic identity', r['research_findings'][0])
        template = json.loads((layout.run / r['summary']['crosswalk_template']['path']).read_bytes())
        self.assertEqual((template['mapping_status'], template['reviewer']), ('PENDING_HUMAN_REVIEW', {'kind': 'PENDING', 'name': 'PENDING'}))
        rep = self.more(layout, ledger=runs.ledger_spec(ledger, cid, None, self.crosswalk(layout)))
        r = self.stages(layout)['ANVIL_CHECKS']
        self.assertEqual(r['status'], 'BLOCKED')  # checklist blockers, now presented as this card's continuation
        self.assertEqual(r['summary']['link']['status'], 'SYNTHETIC_CROSSWALK_FIXTURE')
        self.assertIn('NO_PREDICTOR_OBSERVATION', r['summary']['checklist']['distinctive_predictor']['blockers'])
        self.assertTrue(Path(r['summary']['ledger']).is_relative_to(layout.artifacts))
        self.assertEqual(ledger.read_bytes(), before)
        self.assertEqual(rep['integrity']['supplied ledger'], 'UNCHANGED')

    def test_unrelated_candidate_is_unlinked_and_a_wrong_crosswalk_is_refused(self):
        ledger = self.unrelated_ledger()
        layout, _ = self.start(run_id='OPR-TEST-UNRELATED', ledger=runs.ledger_spec(ledger, 'CAND-UNRELATED', None))
        r = self.stages(layout)['ANVIL_CHECKS']
        self.assertEqual((r['status'], r['summary']['link']), ('WAITING_FOR_HUMAN', 'UNLINKED'))
        self.assertEqual(set(r['summary']['claim_text_comparison'].values()), {'DIFFERENT_TEXT'})
        self.assertNotIn('checklist', r['summary'])
        cases = {'wrong-card': {'scout': {**r['summary']['binding']['scout'], 'card_sha256': '0' * 64}},
                 'assistant': {'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'name': 'Claude'}},
                 'human-in-synthetic': {'reviewer': {'kind': 'HUMAN', 'name': 'Fictional Person'}},
                 'pending': {'mapping_status': 'PENDING_HUMAN_REVIEW'}}
        for name, override in cases.items():
            self.more(layout, ledger=runs.ledger_spec(ledger, 'CAND-UNRELATED', None, self.crosswalk(layout, name + '.json', **override)))
            r = self.stages(layout)['ANVIL_CHECKS']
            self.assertEqual((r['status'], r['summary']['link']), ('BLOCKED', 'CROSSWALK_INVALID'), name)
            self.assertNotIn('checklist', r['summary'], name)

    def test_unready_card_never_links_a_supplied_ledger_even_with_a_valid_crosswalk(self):
        ledger = self.unrelated_ledger()
        from src.research.discovery.ledger import Ledger
        cand = Ledger(ledger).load().latest('candidate', 'CAND-UNRELATED')
        current = Archive(self.f['archive']).load().latest(self.f['unreviewed_idea'])
        value = {'schema': profile.CROSSWALK,
                 'scout': {'idea_id': current['id'], 'version': current['version'], 'card_sha256': digest(current), 'handoff_sha256': None},
                 'discovery': {'ledger_sha256': runs.sha_file(ledger), 'candidate_id': cand['id'], 'candidate_version': cand['version'],
                               'candidate_sha256': digest(cand)},
                 'mapping_status': 'HUMAN_REVIEWED_REFORMULATION', 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'name': 'SYNTHETIC_REVIEWER'},
                 'reviewed_at': F.MOMENT, 'notes': 'SYNTHETIC structurally valid crosswalk with a null handoff binding.'}
        crosswalk = self.root / 'inputs' / 'null-handoff-crosswalk.json'
        crosswalk.write_bytes(canonical(value))
        layout, rep = self.start(self.f['unreviewed_idea'], run_id='OPR-TEST-UNREADY-LINK', ledger=runs.ledger_spec(ledger, cand['id'], None, crosswalk))
        s = self.stages(layout)
        self.assertEqual(s['FORGE_READINESS']['status'], 'WAITING_FOR_HUMAN')
        r = s['ANVIL_CHECKS']
        self.assertEqual((r['status'], r['summary']['link']), ('WAITING_FOR_HUMAN', 'UNLINKED_NO_CURRENT_HANDOFF'))
        self.assertNotIn('checklist', r['summary'])
        self.assertFalse(list(layout.artifacts.glob('anvil-ledger-*/crosswalk-template.json')))
        self.assertFalse((layout.scout / 'exports').exists() and list((layout.scout / 'exports').glob('*handoff*')))
        self.assertEqual(rep['first_boundary']['stage'], 'FORGE_READINESS')

    # ---------------------------------------------------------------------------------- original drift before continue

    def custody_drift(self, mutate, run_id):
        critic = self.f['archive'].parent / f"critic-v1-{self.f['archive'].name}"
        critic.mkdir(exist_ok=True)
        (critic / 'notes.json').write_bytes(b'{"synthetic": true}\n')
        layout, _ = self.start(run_id=run_id)
        recorded = self.stages(layout)['FORGE_CUSTODY']['summary']
        keys, copy_before = self.started(layout), read_tree(layout.scout)
        mutate(critic)
        rep = self.more(layout)
        s = self.stages(layout)
        check = s['CUSTODY_CHECK']
        self.assertEqual(check['status'], 'FAILED')
        self.assertEqual({s[n]['status'] for n in ('FORGE_RECORDS', 'FORGE_READINESS', 'JEV_MEMORY', 'ARMOURY_GRAPH', 'ANVIL_DRAFTS', 'ANVIL_CHECKS')}, {'SKIPPED'})
        later = [e['record'] for e in Journal(layout.run).load() if e['type'] == 'STAGE_STARTED'][len(keys):]
        self.assertEqual({r['stage'] for r in later}, {'PREFLIGHT', 'CUSTODY_CHECK', 'INTEGRITY'})  # nothing recopied or replayed
        self.assertEqual(read_tree(layout.scout), copy_before)
        self.assertEqual(rep['outcome'], 'FAILED')
        self.assertEqual(rep['first_boundary']['stage'], 'CUSTODY_CHECK')
        return check['summary'], recorded

    def test_changed_original_scout_ledger_blocks_continue_before_research_stages(self):
        archive = self.f['archive']
        summary, recorded = self.custody_drift(lambda critic: (archive / 'scout.jsonl').write_bytes((archive / 'scout.jsonl').read_bytes() + b'\n'),
                                               'OPR-TEST-ORIGINAL-DRIFT')
        self.assertEqual(summary['archive']['recorded_digest'], recorded['original']['digest'])
        self.assertNotEqual(summary['archive']['current_digest'], recorded['original']['digest'])
        self.assertEqual(summary['critic_workspace']['state'], 'UNCHANGED')

    def test_changed_original_critic_workspace_blocks_continue_before_research_stages(self):
        summary, recorded = self.custody_drift(lambda critic: (critic / 'notes.json').write_bytes(b'{"synthetic": false}\n'), 'OPR-TEST-CRITIC-DRIFT')
        self.assertEqual(summary['archive']['state'], 'UNCHANGED')
        self.assertEqual(summary['critic_workspace']['recorded_digest'], recorded['critic']['digest'])
        self.assertEqual(summary['critic_workspace']['state'], 'CHANGED')

    def test_plan_separates_a_recorded_ready_review_from_current_handoff_eligibility(self):
        archive = Archive(self.f['archive'])
        current = archive.load().latest(self.f['ready_idea'])
        def plan():
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.main(['--base', str(self.f['base']), 'plan', '--archive', str(self.f['archive'])]), 0)
            return {c['idea_id']: c for c in json.loads(out.getvalue())['cards']}
        cards = plan()
        self.assertEqual((cards[self.f['ready_idea']]['ready_review'], cards[self.f['ready_idea']]['handoff_eligible']), (True, True))
        self.assertEqual((cards[self.f['unreviewed_idea']]['ready_review'], cards[self.f['unreviewed_idea']]['handoff_eligible']), (False, False))
        archive.append('feasibility', {**F.feasibility(current), 'conclusion': 'NOT_FEASIBLE', 'assessment': 'SYNTHETIC later assessment: not feasible.'},
                       recorded_at='2026-10-22T00:00:00+00:00')
        card = plan()[self.f['ready_idea']]
        self.assertEqual((card['ready_review'], card['handoff_eligible']), (True, False))  # an obsolete READY flag is not eligibility
        self.assertIn('READY needs an identifiable publisher URL', card['handoff_refusal'])

    # ---------------------------------------------------------------------------------- stale Scout handoff

    def append_to_copy(self, layout, kind, record):
        Archive(layout.scout).append(kind, record, recorded_at='2026-10-22T00:00:00+00:00')

    def ready_run(self, run_id):
        layout, _ = self.start(run_id=run_id)
        r = self.stages(layout)['FORGE_READINESS']
        self.assertEqual(r['status'], 'COMPLETE')
        export = layout.scout / 'exports' / f"{self.f['ready_idea']}-v1-handoff.json"
        return layout, export, export.read_bytes()

    def test_withdrawn_ready_review_refuses_the_old_export(self):
        layout, export, saved = self.ready_run('OPR-TEST-WITHDRAWN')
        self.append_to_copy(layout, 'review', {'readiness_version': 'SCOUT_READY_V002', 'idea_id': self.f['ready_idea'], 'version': 1,
                                                'decision': 'HUMAN_REVIEW', 'reason_type': 'UNRESOLVED', 'reason': 'SYNTHETIC later review withdraws the earlier READY decision.',
                                                'uncertainties': ['Fictional.'], 'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'},
                                                'minutes': 'UNKNOWN', 'approved_handoff': False, 'reconsider_when': 'Never real.', 'authorises_acquisition': False})
        rep = self.more(layout)
        r = self.stages(layout)['FORGE_READINESS']
        self.assertEqual(r['status'], 'WAITING_FOR_HUMAN')
        self.assertTrue(r['summary']['stale_export'])
        self.assertIn('no longer authorises it', ' '.join(r['research_findings']))
        self.assertEqual(export.read_bytes(), saved)
        self.assertEqual(self.stages(layout)['ANVIL_DRAFTS']['summary']['candidate']['status'], 'NOT_DRAFTED')
        self.assertEqual(rep['first_boundary']['stage'], 'FORGE_READINESS')

    def test_changed_feasibility_refuses_the_old_export(self):
        layout, export, _ = self.ready_run('OPR-TEST-FEASIBILITY')
        current = Archive(layout.scout).load().latest(self.f['ready_idea'])
        self.append_to_copy(layout, 'feasibility', {**F.feasibility(current), 'conclusion': 'NOT_FEASIBLE',
                                                     'assessment': 'SYNTHETIC later assessment: the fictional register is not feasible.'})
        self.more(layout)
        r = self.stages(layout)['FORGE_READINESS']
        self.assertEqual((r['status'], r['summary']['handoff'], r['summary']['stale_export']), ('WAITING_FOR_HUMAN', 'REFUSED', True))
        self.assertIn('READY needs an identifiable publisher URL', r['summary']['refusal'])

    def test_stale_export_that_differs_from_current_authority_is_never_used(self):
        layout, export, saved = self.ready_run('OPR-TEST-STALE')
        current = Archive(layout.scout).load().latest(self.f['ready_idea'])
        self.append_to_copy(layout, 'feasibility', {**F.feasibility(current), 'assessment': 'SYNTHETIC ONLY: a later and different assessment '
                                                     'of the same fictional register, still researchable as a proposal.'})
        self.more(layout)
        r = self.stages(layout)['FORGE_READINESS']
        self.assertEqual((r['status'], r['summary']['handoff']), ('BLOCKED', 'STALE_EXPORT'))
        self.assertEqual(export.read_bytes(), saved)
        self.assertEqual(self.stages(layout)['ANVIL_DRAFTS']['summary']['candidate']['status'], 'NOT_DRAFTED')
        layout2, export2, _ = self.ready_run('OPR-TEST-EDITED')
        self.more(layout2)
        self.assertEqual(self.stages(layout2)['FORGE_READINESS']['summary']['handoff'], 'EXPORT_VERIFIED_AGAINST_CURRENT_STATE')
        export2.write_bytes(export2.read_bytes().replace(b'"PROPOSAL_ONLY"', b'"PROPOSAL_ONLY" ', 1))  # an edited export
        self.more(layout2)
        self.assertEqual(self.stages(layout2)['FORGE_READINESS']['summary']['handoff'], 'STALE_EXPORT')

    # ---------------------------------------------------------------------------------- command boundary

    def test_discovery_writes_are_limited_to_the_synthetic_preview(self):
        layout, _ = self.start(evidence=self.evidence(), run_id='OPR-TEST-PREVIEWONLY')
        preview = next(layout.artifacts.glob('anvil-preview-*'))
        ledger, record = preview / 'ledger.jsonl', preview / 'candidate.json'
        foreign = self.unrelated_ledger()
        (preview / 'live-campaign.json').write_bytes(canonical({**json.loads((preview / 'campaign.json').read_bytes()), 'fixture': 'LIVE'}))
        other = layout.artifacts / 'elsewhere'; other.mkdir()
        attempts = [(D.call, (profile.DISCOVERY, ['add', ledger, 'candidate', record])), (D.call, (profile.DISCOVERY, ['init', other / 'ledger.jsonl', record])),
                    (D.call, (profile.DISCOVERY, ['add', ledger, 'review', record]))]
        for kind in ('review', 'disposition', 'observation', 'relationship', 'effort', 'campaign', 'freeze'):
            attempts.append((D.preview, (layout.artifacts, ['add', ledger, kind, record])))
        attempts += [(D.preview, (layout.artifacts, ['add', foreign, 'candidate', record])),
                     (D.preview, (layout.artifacts, ['init', other / 'ledger.jsonl', record])),
                     (D.preview, (layout.artifacts, ['init', preview.parent / 'anvil-preview-new' / 'ledger.jsonl', preview / 'live-campaign.json'])),
                     (D.preview, (layout.artifacts, ['init', ledger, preview / 'campaign.json'])),
                     (D.preview, (layout.artifacts, ['add', ledger, 'candidate', foreign])),
                     (D.preview, (layout.artifacts, ['add', ledger, 'candidate', record, '--extra'])),
                     (D.preview, (self.root, ['add', ledger, 'candidate', record])),
                     (D.call, (profile.QUARRY, ['import-file', 'r', 's', '--out', self.root / 'outside'], [layout.run])),
                     (D.call, (profile.JEV, ['prepare', 'i', '--out', self.root / 'outside'], [layout.run])),
                     (D.call, (profile.SCOUT, ['handoff', self.f['archive'], self.f['ready_idea']], [layout.run])),
                     (D.call, (profile.JEV, ['prepare', 'i', '--out', layout.run / 'x'], None))]
        with patch('src.research.discovery.cli.main', side_effect=AssertionError('reached Discovery')), \
                patch('src.research.quarry_v1.__main__.main', side_effect=AssertionError('reached Quarry')):
            for fn, args in attempts:
                with self.assertRaises(D.NotPermitted, msg=repr(args)[:160]):
                    fn(*args)
        self.assertEqual(json.loads(foreign.read_bytes().splitlines()[0])['record']['id'], 'DLC-UNRELATED')

    # ---------------------------------------------------------------------------------- preflight and drift

    def test_failed_preflight_prevents_custody_and_every_research_stage(self):
        for name, patcher in (('dependency', patch.object(profile, 'MODULES', profile.MODULES + ('src.research.no_such_module',))),
                              ('missing required repository file', patch.object(profile, 'REQUIRED', profile.REQUIRED + ('docs/no_such_file.json',))),
                              ('not git-ignored', patch.multiple(profile, ROOT=self.root, research_ignored=lambda: False))):
            with patcher:
                layout, rep = self.start(run_id='OPR-TEST-PRE-' + name.split()[0].upper().replace('-', ''))
            s = self.stages(layout)
            self.assertEqual(s['PREFLIGHT']['status'], 'FAILED', name)
            self.assertTrue(any(name in f for f in s['PREFLIGHT']['software_findings']), name)
            self.assertEqual(s['FORGE_CUSTODY']['status'], 'SKIPPED', name)
            self.assertFalse(layout.scout.exists(), name)
            self.assertEqual({s[n]['status'] for n in ('FORGE_RECORDS', 'JEV_MEMORY', 'ARMOURY_GRAPH', 'ANVIL_CHECKS')}, {'SKIPPED'}, name)
            self.assertFalse([c for st in s.values() for c in st.get('calls') or []], name)
            self.assertEqual((rep['outcome'], rep['first_boundary']['stage']), ('FAILED', 'PREFLIGHT'), name)
        with self.assertRaisesRegex(runs.OperatorError, 'overlap'):
            runs.create(runs.request_value(self.f['archive'], self.f['ready_idea'], None, None, [], None), base=self.f['archive'] / 'ws', run_id='OPR-TEST-INSIDE')
        self.assertFalse((self.f['archive'] / 'ws').exists())

    def test_implementation_drift_blocks_continue_until_explicit_acceptance(self):
        layout, _ = self.start(evidence=self.evidence(), run_id='OPR-TEST-DRIFT')
        journal = (layout.run / 'journal.jsonl').read_bytes()
        keys = self.started(layout)
        changed = {**runs.implementation(), 'digest': 'd' * 64}
        with patch.object(runs, 'implementation', return_value=changed):
            with self.assertRaisesRegex(runs.OperatorError, 'implementation drift'):
                runs.invoke(layout, 'continue')
            with self.assertRaisesRegex(runs.OperatorError, 'implementation drift'):
                runs.invoke(layout, 'continue', accept_drift='e' * 64)
            self.assertEqual((layout.run / 'journal.jsonl').read_bytes(), journal)  # refusals write nothing
            self.assertEqual(cli.status(layout)['implementation_drift']['current_code']['implementation'], 'd' * 64)
            runs.invoke(layout, 'continue', accept_drift='d' * 64)
        events = Journal(layout.run).load()
        self.assertEqual([e['record']['to']['implementation'] for e in events if e['type'] == 'DRIFT_ACCEPTED'], ['d' * 64])
        rerun = {k.split('@')[0] for k in self.started(layout)[len(keys):]}
        self.assertIn('FORGE_RECORDS', rerun)
        self.assertFalse(rerun & {'FORGE_CUSTODY', 'QUARRY_IMPORT:R1', 'QUARRY_EXPORT:R1', 'JEV_EVIDENCE', 'JEV_MEMORY', 'ANVIL_CHECKS'})
        self.assertEqual(self.stages(layout)['ANVIL_DRAFTS']['status'], 'WAITING_FOR_HUMAN')
        with self.assertRaisesRegex(runs.OperatorError, 'implementation drift'):
            runs.invoke(layout, 'continue')  # bound to the accepted digest now; the real code differs again
        with self.assertRaisesRegex(runs.OperatorError, 'nothing to accept'):
            runs.invoke(self.start(run_id='OPR-TEST-NODRIFT')[0], 'continue', accept_drift='d' * 64)

    # ---------------------------------------------------------------------------------- adversarial inputs

    def test_input_changed_after_its_hash_was_recorded_is_never_consumed(self):
        spec = self.evidence()
        original = self.root / 'inputs' / 'quarry' / 'original-R1.txt'
        original.write_bytes(original.read_bytes() + b'appended later\n')
        layout, rep = self.start(evidence=spec, run_id='OPR-TEST-TOCTOU')
        s = self.stages(layout)
        self.assertEqual(s['QUARRY_IMPORT:R1']['status'], 'BLOCKED')
        self.assertEqual(s['QUARRY_IMPORT:R1']['summary']['changed_since_supplied'], ['original'])
        self.assertFalse(any(p.name.startswith('R1-') for p in layout.quarry.iterdir()))
        self.assertEqual(s['INTEGRITY']['summary']['checks']['R1 original'], 'CHANGED')
        self.assertEqual(rep['outcome'], 'FAILED')
        ledger = self.unrelated_ledger(); spec = runs.ledger_spec(ledger, 'CAND-UNRELATED', None)
        with ledger.open('ab') as handle:
            handle.write(b'{}\n')
        layout, _ = self.start(run_id='OPR-TEST-TOCTOU-LEDGER', ledger=spec)
        self.assertIn('changed or disappeared after being supplied', self.stages(layout)['ANVIL_CHECKS']['research_findings'][0])

    def test_boundary_violation_leaves_a_truthful_readable_status(self):
        escape = self.root / 'escape.json'
        def hostile(argv):
            escape.write_bytes(b'{}')
        with patch('src.research.graph.cli.main', side_effect=hostile):
            layout, rep = self.start(run_id='OPR-TEST-VIOLATION')
        self.assertFalse(escape.exists())
        s = self.stages(layout)
        self.assertEqual(s['ARMOURY_GRAPH']['status'], 'FAILED')
        self.assertIn('BOUNDARY_VIOLATION', s['ARMOURY_GRAPH']['software_findings'][0])
        self.assertEqual({s[n]['status'] for n in ('ANVIL_DRAFTS', 'ANVIL_CHECKS', 'DOWNSTREAM')}, {'SKIPPED'})
        self.assertEqual(s['INTEGRITY']['status'], 'COMPLETE')
        self.assertEqual(rep['integrity']['original archive'], 'UNCHANGED')
        self.assertEqual((rep['outcome'], rep['accounting']['boundary_denials']), ('FAILED', 1))
        status = cli.status(layout)
        self.assertEqual((status['outcome'], status['locked'], status['finished']), ('FAILED', False, True))

    def test_missing_referenced_run_artifact_fails_closed(self):
        layout, _ = self.start(run_id='OPR-TEST-MISSING-ARTIFACT')
        ref = self.stages(layout)['FORGE_RECORDS']['summary']['card_artifact']
        (layout.run / ref['path']).unlink()
        rep = self.more(layout)
        s = self.stages(layout)
        self.assertEqual(s['ARMOURY_GRAPH']['status'], 'FAILED')
        self.assertIn('COORDINATOR_FAULT', s['ARMOURY_GRAPH']['software_findings'][0])
        self.assertEqual(rep['outcome'], 'FAILED')
        self.assertTrue(cli.status(layout)['finished'])

    def test_only_permitted_component_commands_are_callable(self):
        for module, argv in ((profile.SCOUT, ['review', 'x', 'y']), (profile.SCOUT, ['revise', 'x', 'y']), (profile.SCOUT, ['feasibility', 'x', 'y']),
                             (profile.PIPELINE, ['run', 'x', '--authorisation', 'y']), (profile.CRITIC, ['import-response', 'w', 'r', 'f']),
                             (profile.JEV, ['import-response', 'w', 'r']), (profile.JEVI, ['prepare', 'w']), (profile.QUARRY, ['plan-acquisition', 'r', 's']),
                             (profile.DISCOVERY, ['disposition']), ('src.research.opportunity_scout.exploratory_v001', ['run'])):
            with self.assertRaises(D.NotPermitted, msg=f'{module} {argv[0]}'):
                D.call(module, argv)

    def test_boundary_denies_network_processes_credentials_and_foreign_writes(self):
        b = Boundary(); b.roots = (resolved(self.root / 'run'),); b.active = True  # the guard compares resolved paths (8.3 names expand)
        inside, outside = self.root / 'run' / 'x.json', self.root / 'elsewhere.json'
        b.audit('open', (str(inside), 'xb', os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        b.audit('open', (str(outside), 'rb', os.O_RDONLY))
        for event, args in (('socket.connect', (None, ('example.org', 443))), ('socket.getaddrinfo', ('example.org', 443, 0, 0, 0, 0)),
                            ('subprocess.Popen', ('claude', ['claude'], None, None)), ('os.system', ('codex',)),
                            ('open', (str(outside), 'wb', os.O_WRONLY | os.O_CREAT)), ('os.remove', (str(outside), None)),
                            ('open', (str(self.root / '.env'), 'rb', os.O_RDONLY)), ('os.symlink', (str(inside), str(outside), None))):
            with self.assertRaises(BoundaryViolation, msg=event):
                b.audit(event, args)
        b.active = False
        b.audit('socket.connect', (None, None))  # inert outside the context
        self.assertEqual(len(b.denials), 8)

    def test_changed_run_artifact_fails_the_stage_without_crashing_the_invocation(self):
        layout, _ = self.start()
        ref = self.stages(layout)['FORGE_RECORDS']['summary']['card_artifact']
        target = layout.run / ref['path']
        target.write_bytes(target.read_bytes().replace(b'"version":1', b'"version":2', 1))
        rep = self.more(layout)
        s = self.stages(layout)
        self.assertEqual(s['FORGE_RECORDS']['status'], 'COMPLETE')  # recorded result reused, never recomputed
        self.assertEqual(s['ARMOURY_GRAPH']['status'], 'FAILED')
        self.assertIn('run artifact changed since it was recorded', s['ARMOURY_GRAPH']['software_findings'][0])
        self.assertEqual(rep['outcome'], 'FAILED')
        self.assertTrue(cli.status(layout)['finished'])

    def test_plan_lists_cards_when_no_idea_is_named(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(['--base', str(self.f['base']), 'plan', '--archive', str(self.f['archive'])]), 0)
        plan = json.loads(out.getvalue())
        self.assertIsNone(plan['selected'])
        self.assertEqual({c['idea_id']: c['ready_review'] for c in plan['cards']}, {self.f['ready_idea']: True, self.f['unreviewed_idea']: False})

    def test_cli_plan_status_and_refusals(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(['--base', str(self.f['base']), 'plan', '--archive', str(self.f['archive']), '--idea', self.f['unreviewed_idea']])
        plan = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertFalse(plan['selected']['ready_review'])
        self.assertTrue(any('READY' in b for b in plan['predicted_blockers']))
        self.assertFalse((self.f['base'] / 'operator-v1').exists())  # plan writes nothing to a run
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(['--base', str(self.f['base']), 'status', 'OPR-NOPE']), 2)
            self.assertEqual(cli.main(['--base', str(self.f['base']), 'run', '--subject', 'x', '--archive', 'y']), 2)
        subjects = self.f['base'] / 'operator-v1' / 'subjects.json'
        subjects.parent.mkdir(parents=True)
        subjects.write_bytes(canonical({'schema': cli.SUBJECTS, 'subjects': {'demo-b': {'archive': str(self.f['archive']), 'idea_id': self.f['ready_idea']}}}))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(['--base', str(self.f['base']), 'run', '--subject', 'demo-b', '--run-id', 'OPR-TEST-CLI']), 0)
        self.assertIn('# Research OS run report: OPR-TEST-CLI (STOPPED_AT_BOUNDARY)', out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(['--base', str(self.f['base']), 'status', 'OPR-TEST-CLI'])
        status = json.loads(out.getvalue())
        self.assertEqual((status['outcome'], status['locked'], status['finished']), ('STOPPED_AT_BOUNDARY', False, True))
        self.assertEqual(cli.doctor(self.f['base'], self_test=False)['checks']['workspace_base'], str(self.f['base']))


if __name__ == '__main__':
    unittest.main()
