"""Post-generation Jev shadow review: label packet, independent labels and descriptive comparison.

Every card, Jev answer and label here is a SYNTHETIC_FIXTURE written by the test. Nothing is a real model output, a real
human judgment or a performance result."""
from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from src.research.spec import canonical, digest
from src.research.opportunity_scout import engine as E, evaluation as V, schema as S, workflow as W
from src.research.opportunity_scout.post_generation import review as SR
from src.research.opportunity_scout.post_generation.cli import main
from src.research.opportunity_scout.fixtures import MOMENT, STORIES, feasibility, idea, provenance
from src.research.opportunity_scout.providers import QUESTIONS, shadow_request
from src.research.opportunity_scout.storage import Archive

SALT = 'SYNTHETIC_PRIVATE_TEST_SALT_12345'


def answer(choice, p):
    return {'type': 'choice', 'choice': choice, 'probabilities': dict(zip(('yes', 'no', 'unsure'), p)), 'confidence': max(p)}


def response(choice='yes', p=(.8, .1, .1), model='jev-1.13.0'):
    return {'model': model, 'usage': {'input_tokens': 100, 'output_tokens': 20}, 'answers': {q: answer(choice, p) for q in QUESTIONS}}


def label(bid, values, reviewer='SYNTHETIC_LABELLER_1', kind='SYNTHETIC_FIXTURE', minutes=3):
    return {'schema': SR.LABELS_V1, 'blind_id': bid, 'reviewer': {'kind': kind, 'id': reviewer}, 'saw_jev_output': False,
            'independent_of_generation': True, 'atomic_answers': {q: values for q in QUESTIONS} if isinstance(values, str) else values,
            'minutes': minutes, 'labelled_at': MOMENT, 'notes': 'SYNTHETIC FIXTURE label: not a human judgment.'}


class ShadowReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        families = list(STORIES)
        # Two incomplete archives (3 and 1 cards): the frozen four-condition blind() refuses this, the label packet does not.
        self.archives = {}
        for name, n in (('A', 3), ('B', 1)):
            archive = Archive(Path(self.temp.name) / name)
            W.initialise(archive, 'SYNTHETIC post-generation batch', fixture='SYNTHETIC', with_memory=False, max_cards=6, moment=MOMENT)
            for k in range(n):
                aid, _ = W.prepare(archive, 'FORGE', 1, 'SYNTHETIC_GENERATOR', 'SYNTHETIC_FIXTURE', moment=MOMENT)
                W.finish(archive, aid, canonical({'ideas': [idea(families[k + (3 if name == 'B' else 0)], 'FORGE', k)]}).decode(), provenance(), moment=MOMENT)
            W.triage(archive); self.archives[name] = archive
        self.ids = {n: list(a.load().cards) for n, a in self.archives.items()}

    def states(self):
        return {n: a.load() for n, a in self.archives.items()}

    def shadow(self, name, iid, resp):
        archive = self.archives[name]
        archive.append('shadow', SR.import_response(archive.load(), iid, resp, transport='SYNTHETIC_FIXTURE', now=MOMENT))

    def bid(self, sealed, name, iid):
        return next(b for b, m in sealed['assignments'].items() if m['archive'] == name and m['idea_id'] == iid)

    def test_packet_covers_incomplete_generation_and_hides_jev_and_generator(self):
        self.shadow('A', self.ids['A'][0], response())
        with self.assertRaises(S.ScoutError):V.blind({'PLAIN': self.archives['A'].load()}, SALT)  # the frozen comparison refuses this
        packet, sealed = SR.label_packet(self.states(), SALT)
        self.assertEqual(len(packet['cards']), 4)  # every current card, with or without a Jev answer
        for row in packet['cards']:
            self.assertEqual(set(row), {'blind_id', 'idea', 'source_passages'}); self.assertNotIn('seed_ids', row['idea'])
        text = json.dumps(packet)
        for hidden in ('jev-1.13.0', 'probabilities', 'SYNTHETIC_GENERATOR', '"lane"', 'IDEA-'):self.assertNotIn(hidden, text)
        self.assertEqual((packet['comparative_eligible'], packet['jev_output_included'], packet['authorises']), (False, False, []))
        self.assertEqual(set(packet['questions']), set(QUESTIONS))

    def test_mixed_fixtures_short_salt_and_tampering_are_refused(self):
        with self.assertRaises(S.ScoutError):SR.label_packet(self.states(), 'short')
        states = self.states(); states['B'].batch['fixture'] = 'SCOUT_EXPLORATORY'
        with self.assertRaises(S.ScoutError):SR.label_packet(states, SALT)
        packet, sealed = SR.label_packet(self.states(), SALT)
        for mutate in (lambda p, k:p['cards'][0]['idea'].update(title='Rewritten after labelling'),
                       lambda p, k:p.update(fixture='SCOUT_EXPLORATORY'),  # would let HUMAN labels into a synthetic packet
                       lambda p, k:next(iter(k['assignments'].values())).update(version=2)):
            p, k = copy.deepcopy(packet), copy.deepcopy(sealed); mutate(p, k)
            with self.assertRaises(S.ScoutError):SR.validate_labels(p, k, [])

    def test_labels_need_honest_independent_provenance(self):
        packet, sealed = SR.label_packet(self.states(), SALT); bid = packet['cards'][0]['blind_id']
        SR.validate_labels(packet, sealed, [label(bid, 'yes'), label(bid, 'no', reviewer='SYNTHETIC_LABELLER_2')])
        bad = [([label(bid, 'yes', kind='HUMAN', reviewer='Not a real person')], 'SYNTHETIC_FIXTURE labels only'),
               ([label(bid, 'yes', reviewer='Claude labeller')], 'assistant'), ([label(bid, 'yes', reviewer='Jev')], 'assistant'),
               ([{**label(bid, 'yes'), 'saw_jev_output': True}], 'saw_jev_output'),
               ([{**label(bid, 'yes'), 'independent_of_generation': False}], 'independent_of_generation'),
               ([label(bid, 'yes'), label(bid, 'no')], 'one label per reviewer'), ([label('LABEL-unknown', 'yes')], 'unknown blind id'),
               ([label(bid, {q: 'yes' for q in list(QUESTIONS)[:-1]})], 'atomic_answers'), ([label(bid, 'maybe')], 'atomic_answers')]
        for labels, message in bad:
            with self.assertRaisesRegex(S.ScoutError, message):SR.validate_labels(packet, sealed, labels)

    def test_without_labels_only_missing_records_are_reported(self):
        self.shadow('A', self.ids['A'][0], response())
        packet, sealed = SR.label_packet(self.states(), SALT); rep = SR.compare(self.states(), packet, sealed, [])
        for q in rep['questions'].values():
            self.assertEqual(q['pairs_compared'], 0); self.assertIsNone(q['agreement']); self.assertIsNone(q['binary_yes_brier'])
        self.assertEqual(len(rep['missing']['items_without_labels']), 4); self.assertEqual(len(rep['missing']['items_without_shadow']), 3)
        self.assertEqual((rep['human_labels_invented'], rep['calibration_established'], rep['comparative_eligible']), (False, False, False))

    def test_metrics_separate_agreement_abstention_disagreement_and_brier(self):
        a1, a2, a3 = self.ids['A']; b1 = self.ids['B'][0]
        self.shadow('A', a1, response('yes', (.8, .1, .1)))
        self.shadow('A', a2, response('no', (.1, .8, .1), model='jev-latest'))
        self.shadow('A', a3, response('unsure', (.3, .2, .5)))
        packet, sealed = SR.label_packet(self.states(), SALT); bid = lambda iid, n='A':self.bid(sealed, n, iid)
        labels = [label(bid(a1), 'yes'), label(bid(a1), 'no', reviewer='SYNTHETIC_LABELLER_2'), label(bid(a2), 'yes'),
                  label(bid(a3), 'no'), label(bid(b1, 'B'), 'yes', minutes='UNKNOWN')]
        rep = SR.compare(self.states(), packet, sealed, labels); f = rep['questions']['falsifiable']
        self.assertEqual((f['pairs_compared'], f['agreed'], f['decisive_pairs']), (4, 1, 3))
        self.assertAlmostEqual(f['agreement'], .25); self.assertAlmostEqual(f['decisive_agreement'], 1 / 3)
        self.assertEqual(f['disagreement'], {'opposite_decisions': 2, 'jev_abstained_human_decided': 1, 'human_abstained_jev_decided': 0})
        self.assertAlmostEqual(f['jev_abstention_rate'], 1 / 3); self.assertEqual(f['label_abstention_rate'], 0)
        self.assertAlmostEqual(f['binary_yes_brier'], (.04 + .64 + .81 + .09) / 4); self.assertEqual(f['binary_label_count'], 4)
        self.assertEqual(f['constant_half_reference_brier'], .25)
        self.assertEqual(f['confusion_jev_by_label']['unsure'], {'yes': 0, 'no': 1, 'unsure': 0})
        self.assertEqual(f['human_human'], {'pairs': 1, 'agreement': 0})
        # falsifiable: 'no' is the problem answer. Labels flag a1 (labeller 2) and a3; Jev flags neither, and flags a2 where the label is yes.
        self.assertEqual(f['problem_flags'], {'human_flagged': 2, 'jev_also_flagged': 0, 'jev_missed': 2, 'jev_flagged_human_opposite': 1,
                                              'jev_flagged_human_unsure': 0, 'jev_also_flagged_where_mechanical_check_did_not': 0,
                                              'mechanical_check_exists': True})
        c = rep['questions']['certainty_exceeds_evidence']['problem_flags']  # 'yes' is the problem answer; no mechanical check exists
        self.assertEqual((c['human_flagged'], c['jev_also_flagged'], c['jev_also_flagged_where_mechanical_check_did_not']), (2, 1, None))
        u = rep['usage_and_cost']
        self.assertEqual((u['shadow_records_used'], u['returned_model_differs'], u['input_tokens'], u['unknown_cost_records']), (3, 1, 300, 3))
        self.assertEqual(u['returned_models'], {'jev-1.13.0': 2, 'jev-latest': 1})
        self.assertEqual(rep['label_effort'], {'known_minutes': 12, 'unknown_entries': 1})
        self.assertEqual(rep['missing']['items_without_shadow'], [bid(b1, 'B')])

    def test_earliest_shadow_is_used_and_revisions_are_reported(self):
        a1 = self.ids['A'][0]; self.shadow('A', a1, response('yes', (.9, .05, .05))); self.shadow('A', a1, response('no', (.05, .9, .05)))
        packet, sealed = SR.label_packet(self.states(), SALT); b = self.bid(sealed, 'A', a1)
        old = self.archives['A'].load().latest(a1)
        new = copy.deepcopy(old['idea']); new['title'] = 'SYNTHETIC clarified title after labelling'
        self.archives['A'].append('revision', {'idea_id': a1, 'from_version': 1, 'idea': new, 'reason': 'Synthetic clarification of the card title.',
                                               'actor': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_EDITOR'}, 'after_outcome_known': False})
        rep = SR.compare(self.states(), packet, sealed, [label(b, 'yes')])
        self.assertEqual(rep['questions']['explicit_mechanism']['agreed'], 1)  # the earliest answer (yes), not the later re-run (no)
        self.assertEqual(rep['missing']['items_with_repeated_shadow_records'], [b]); self.assertEqual(rep['missing']['items_superseded_since_packet'], [b])

    def test_jev_never_changes_routing_or_grants_authority(self):
        before = {i: self.archives['A'].load().route(self.archives['A'].load().latest(i)) for i in self.ids['A']}
        for i in self.ids['A']:self.shadow('A', i, response('no', (.01, .98, .01)))
        packet, sealed = SR.label_packet(self.states(), SALT)
        rep = SR.compare(self.states(), packet, sealed, [label(r['blind_id'], 'yes') for r in packet['cards']])
        state = self.archives['A'].load()
        self.assertEqual({i: state.route(state.latest(i)) for i in self.ids['A']}, before)
        self.assertEqual(len(state.cards), 3)  # nothing deleted or rejected
        self.assertEqual((rep['shadow_only'], rep['routing_changed'], rep['authorises'], rep['statistical_significance']), (True, False, [], 'NOT_CLAIMED'))

    def run_cli(self, args, code=0):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):self.assertEqual(main(args), code, err.getvalue())
        return json.loads(out.getvalue()) if code == 0 else err.getvalue()

    def test_cli_imports_a_saved_response_unchanged_and_never_repairs_it(self):
        store, iid = str(self.archives['A'].path), self.ids['A'][0]; f = Path(self.temp.name) / 'jev-response.json'
        f.write_text(json.dumps(response()), encoding='utf-8')
        out = self.run_cli(['import-response', store, iid, str(f), '--synthetic-fixture'])
        self.assertEqual((out['routing_changed'], out['authorises']), (False, []))
        recorded = self.archives['A'].load().shadows[-1]
        self.assertEqual(recorded['response'], json.loads(f.read_text(encoding='utf-8')))
        self.assertEqual(recorded['request_sha256'], digest(shadow_request(self.archives['A'].load(), iid)))
        self.assertEqual((recorded['cost'], recorded['currency']), ('UNKNOWN', 'UNKNOWN'))
        for mutate in (lambda r:r.update(id='resp-1'), lambda r:r['answers'].pop('falsifiable'),
                       lambda r:r['answers']['falsifiable'].update(choice='no')):  # extra field, missing question, choice not the argmax
            bad = response(); mutate(bad); f.write_text(json.dumps(bad), encoding='utf-8')
            self.run_cli(['import-response', store, iid, str(f), '--synthetic-fixture'], code=2)
        self.assertEqual(len(self.archives['A'].load().shadows), 1)  # refused responses leave the archive unchanged
        f.write_text(json.dumps(response()), encoding='utf-8'); store, iid = self.exploratory()
        self.assertIn('synthetic shadow response in real batch', self.run_cli(['import-response', store, iid, str(f), '--synthetic-fixture'], code=2))

    def exploratory(self):
        archive = Archive(Path(self.temp.name) / 'exploratory')
        W.initialise(archive, 'Exploratory archive for a refusal test', fixture='SCOUT_EXPLORATORY', with_memory=False, moment=MOMENT)
        aid, _ = W.prepare(archive, 'FORGE', 1, 'operator-model', 'OPERATOR_ASSISTED', moment=MOMENT)
        p = provenance(model='operator-model', provider='OPERATOR_ASSISTED'); p['operator'] = 'Test operator'
        p['context_declaration'] = 'Software test archive: no model was invoked.'
        W.finish(archive, aid, canonical({'ideas': [idea()]}).decode(), p, moment=MOMENT)
        return str(archive.path), next(iter(archive.load().cards))

    def test_cli_label_packet_and_compare_round_trip(self):
        self.shadow('A', self.ids['A'][0], response())
        salt = Path(self.temp.name) / 'salt.json'; salt.write_text(json.dumps({'salt': SALT}), encoding='utf-8')
        stores = ['--store', f'A={self.archives["A"].path}', '--store', f'B={self.archives["B"].path}']
        out_dir = Path(self.temp.name) / 'labelling'
        res = self.run_cli(['label-packet', *stores, '--salt-file', str(salt), '--out', str(out_dir)])
        self.assertEqual((res['cards'], res['comparative_eligible']), (4, False))
        self.run_cli(['label-packet', *stores, '--salt-file', str(salt), '--out', str(out_dir)], code=2)  # written once
        packet = json.loads(Path(res['packet']).read_text(encoding='utf-8'))
        labels = Path(self.temp.name) / 'labels.json'; labels.write_text(json.dumps([label(packet['cards'][0]['blind_id'], 'unsure')]), encoding='utf-8')
        rep = self.run_cli(['compare', *stores, '--packet', res['packet'], '--key', res['private_key'], '--labels', str(labels)])
        self.assertEqual((rep['schema'], rep['labels'], rep['items']), (SR.COMPARISON_V1, 1, 4))
        self.run_cli(['compare', '--store', f'A={self.archives["A"].path}', '--packet', res['packet'], '--key', res['private_key']], code=2)

    def test_trace_from_generation_to_handoff_with_jev_in_shadow(self):
        """Generation, validation, duplicate check, feasibility, READY, shortlist, handoff: Jev alongside, never in the path."""
        archive = self.archives['B']; iid = self.ids['B'][0]; state = archive.load(); card = state.latest(iid)
        self.assertEqual(E.assess(state, card)['checks']['checks'], [])  # validation: no structural warning
        self.assertFalse(any(m['kind'] == 'EXACT_CORE_DUPLICATE' for m in E.proximity(state, card)))  # duplicate review input
        self.shadow('B', iid, response('no', (.05, .9, .05)))  # a negative Jev answer cannot block the human path
        with self.assertRaises(S.ScoutError):E.handoff(archive.load(), iid)  # no human READY yet
        archive.append('feasibility', feasibility(card))
        archive.append('review', {'readiness_version': 'SCOUT_READY_V002', 'idea_id': iid, 'version': 1, 'decision': 'READY', 'reason_type': 'RESEARCHABLE',
                                  'reason': 'SYNTHETIC workflow decision only; no real human judgment.', 'uncertainties': ['Synthetic assumptions.'],
                                  'reviewer': {'kind': 'SYNTHETIC_FIXTURE', 'id': 'SYNTHETIC_REVIEWER'}, 'minutes': S.UNKNOWN, 'approved_handoff': True,
                                  'reconsider_when': 'A dated original must resolve the declared allocation.', 'authorises_acquisition': False})
        selection = archive.append('selection', E.select(archive.load())).selections[-1]
        self.assertIn(iid, [x['idea_id'] for x in selection['selected']])
        proposal = E.handoff(archive.load(), iid)
        self.assertEqual((proposal['schema'], proposal['status'], proposal['creates_campaign'], proposal['certifies_M']),
                         ('DISCOVERY_LAB_STARTING_PROPOSAL_V001', 'PROPOSAL_ONLY', False, False))
        self.assertNotIn('shadow', json.dumps(proposal).lower())  # Jev output is not part of the handoff


if __name__ == '__main__':unittest.main()
