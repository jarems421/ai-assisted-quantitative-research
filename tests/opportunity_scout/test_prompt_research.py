"""Fictional schema/provenance fixtures, never hosted ideas or human scores."""
import copy
import json
import unittest
from collections import Counter
from unittest.mock import patch

from src.research.spec import canonical, digest
from src.research.opportunity_scout import engine as E, prompts as baseline, schema as S
from src.research.opportunity_scout.prompt_research import prompts as P, evaluation as V
from src.research.opportunity_scout.v004_r3 import package as frozen, runtime, policy
from tests.opportunity_scout import v004_fixtures as F


def state():
    result = E.State()
    for row in F.blueprints()['HYBRID']['events']:
        E.apply(result, row['type'], row['record'], row['recorded_at'], replay=True)
    return result


class PromptResearchTests(unittest.TestCase):
    def test_explicit_versions_and_frozen_plain_default(self):
        s = state()
        for lane in S.LANES:
            self.assertEqual(P.make_prompt(s, lane, 2, 'PROMPT-BASE', version=baseline.VERSION),
                             baseline.make_prompt(s, lane, 2, 'PROMPT-BASE'))
        with self.assertRaises(TypeError):
            P.make_prompt(s, 'FORGE', 2, 'PROMPT-X')
        for version in (P.A, P.B):
            with self.assertRaises(S.ScoutError):
                P.make_prompt(s, 'PLAIN', 2, 'PROMPT-X', version=version)
        self.assertIs(E.make_prompt, baseline.make_prompt)

    def test_same_lane_inputs_cutoff_and_full_schema_without_runtime_cap(self):
        s = state(); before = digest(s.__dict__); schema = copy.deepcopy(S.GENERATION)
        for version in (P.A, P.B):
            for lane in ('FORGE', 'RADAR', 'GAP'):
                actual = P.make_prompt(s, lane, 2, 'PROMPT-NEW', version=version)
                original = baseline.make_prompt(s, lane, 2, 'PROMPT-NEW')
                for k in ('context', 'knowledge_cutoff', 'response_schema', 'contains_generated_ideas'):
                    self.assertEqual(actual[k], original[k])
                self.assertNotIn('max_output_tokens', actual)
                self.assertFalse(actual['hosted_authorised'])
                self.assertFalse(actual['scientific_dispatch_authorised'])
                self.assertEqual(actual['baseline_projection_sha256'], original['sha256'])
                projected = S.json_loads(P.payload_bytes(actual))
                self.assertEqual(set(projected), {'lane', 'count', 'knowledge_cutoff', 'instructions', 'response_schema', 'context'})
                self.assertNotIn('implementation', projected)
                self.assertEqual(len(P.payload_bytes(actual)), actual['known_payload_bytes'])
                self.assertEqual(actual, P.make_prompt(s, lane, 2, 'PROMPT-NEW', version=version))
        self.assertEqual(digest(s.__dict__), before)
        self.assertEqual(S.GENERATION, schema)

    def test_creative_objectives_and_truthful_unchanged_enum_contract(self):
        s = state()
        a = P.make_prompt(s, 'FORGE', 2, 'PROMPT-A', version=P.A)
        b = P.make_prompt(s, 'FORGE', 2, 'PROMPT-B', version=P.B)
        self.assertLess(len(a['instructions']), len(b['instructions']))
        for name in ('INVERT_CONSTRAINT', 'TRANSFER_ECONOMIC_ROLE', 'TRACE_OBLIGATION', 'STATIC_TO_DYNAMIC',
                     'CHANGE_MEASUREMENT_AXIS', 'ABSENCE_AS_SIGNAL', 'CROSS_DOMAIN_RELATIONAL_ANALOGY',
                     'SECOND_ORDER', 'THIRD_ORDER', 'COUNTERFACTUAL_SYMMETRY'):
            self.assertIn(name, b['instructions'])
        self.assertIn('rather than company', a['instructions'])
        self.assertIn('ordinary competing explanation', a['instructions'])
        self.assertIn('unreported or unobserved event is not a verified absence', b['instructions'])
        self.assertEqual(b['response_schema'], a['response_schema'])

    def test_generated_cards_never_leak_and_lane_access_stays_isolated(self):
        s = state()
        marker = 'GENERATED_PRIVATE_CARD_MUST_NOT_ENTER_OTHER_CONTEXT'
        s.cards['FAKE'] = [{'idea': marker}]
        s.attempts['FAKE'] = {'result': {'raw_response': marker}}
        for version in (P.A, P.B):
            prompts = {lane: P.make_prompt(s, lane, 2, 'PROMPT-X', version=version) for lane in ('FORGE', 'RADAR', 'GAP')}
            self.assertEqual(prompts['FORGE']['context'], {'seeds': {}, 'memory': {}})
            self.assertEqual(prompts['RADAR']['context']['memory'], {})
            self.assertTrue(prompts['GAP']['context']['memory'])
            self.assertNotIn(marker, canonical(prompts).decode())

    def test_valid_fictional_outputs_use_original_semantic_validator(self):
        s = state()
        for version in (P.A, P.B):
            for lane in ('FORGE', 'RADAR', 'GAP'):
                prompt = P.make_prompt(s, lane, 2, 'PROMPT-X', version=version)
                output = F.output(prompt)
                self.assertEqual(P.validate_response(prompt, json.dumps(output)), output['ideas'])

    def test_reject_malformed_repair_extra_fields_and_new_enum(self):
        p = P.make_prompt(state(), 'FORGE', 2, 'PROMPT-X', version=P.B)
        output = F.output(p)
        values = ['not JSON', json.dumps(output) + ' repaired', json.dumps({'ideas': output['ideas'][:1]}),
                  json.dumps({**output, 'brainstorm': []})]
        wrong = copy.deepcopy(output); wrong['ideas'][0]['mechanism']['transformation'] = 'STATIC_TO_DYNAMIC'
        values.append(json.dumps(wrong))
        for raw in values:
            with self.assertRaises(S.ScoutError):
                P.validate_response(p, raw)

    def test_lane_and_citation_fabrication_are_rejected(self):
        s = state()
        for lane in ('FORGE', 'RADAR', 'GAP'):
            p = P.make_prompt(s, lane, 2, 'PROMPT-X', version=P.B)
            wrong = F.output(p)
            if lane == 'FORGE': wrong['ideas'][0]['seed_ids'] = ['SEED-INVENTED']
            if lane == 'RADAR': wrong['ideas'][0]['mechanism']['links'][0].update(
                basis='DOCUMENTED', evidence=[{'seed': next(iter(s.seeds)), 'quote': 'invented original field'}])
            if lane == 'GAP': wrong['ideas'][0]['historical_refs'] = []
            with self.assertRaises(S.ScoutError):
                P.validate_response(p, json.dumps(wrong))

    def test_prefixes_stops_and_clock_rules_are_preserved(self):
        s = state(); seed = next(iter(s.seeds.values()))
        seed['text'] = 'A' * 8000 + 'UNSEEN_SOURCE_SUFFIX'; seed['sha256'] = S.hash_text(seed['text'])
        p = P.make_prompt(s, 'RADAR', 2, 'PROMPT-X', version=P.A)
        self.assertNotIn('UNSEEN_SOURCE_SUFFIX', p['context']['seeds'][seed['id']]['text'])
        wrong = F.output(p); wrong['ideas'][0]['mechanism']['links'][0]['evidence'] = [{'seed': seed['id'], 'quote': 'UNSEEN_SOURCE_SUFFIX'}]
        with self.assertRaises(S.ScoutError): P.validate_response(p, json.dumps(wrong))
        seed['access'] = 'STOPPED'
        p = P.make_prompt(s, 'RADAR', 2, 'PROMPT-X', version=P.B)
        wrong = F.output(p); wrong['ideas'][0]['source_routes'][0]['locator'] = seed['locator']
        with self.assertRaises(S.ScoutError): P.validate_response(p, json.dumps(wrong))
        seed['clocks']['retrieval'] = '2099-01-01T00:00:00+00:00'
        with self.assertRaises(S.ScoutError): P.make_prompt(s, 'RADAR', 2, 'PROMPT-X', version=P.A)

    def test_hash_and_full_schema_tampering_rejected(self):
        p = P.make_prompt(state(), 'FORGE', 2, 'PROMPT-X', version=P.A)
        wrong = copy.deepcopy(p); wrong['instructions'] += 'changed'
        with self.assertRaises(S.ScoutError): P.validate_response(wrong, json.dumps(F.output(p)))
        wrong = copy.deepcopy(p); wrong['response_schema']['properties']['ideas']['minItems'] = 1
        wrong['sha256'] = digest({k: v for k, v in wrong.items() if k != 'sha256'})
        with self.assertRaisesRegex(S.ScoutError, 'full response schema'):
            P.validate_response(wrong, json.dumps(F.output(p)))
        wrong = copy.deepcopy(p); wrong['construction_dependencies'] = {}
        wrong['sha256'] = digest({k: v for k, v in wrong.items() if k != 'sha256'})
        with self.assertRaisesRegex(S.ScoutError, 'runtime changed'):
            P.payload_bytes(wrong)
        for key in ('hosted_authorised', 'scientific_dispatch_authorised', 'contains_generated_ideas'):
            wrong = copy.deepcopy(p); wrong[key] = True
            wrong['sha256'] = digest({k: v for k, v in wrong.items() if k != 'sha256'})
            with self.assertRaisesRegex(S.ScoutError, 'cannot grant'):
                P.payload_bytes(wrong)

    def test_changed_versioned_resource_fails_without_affecting_baseline(self):
        original = P.text
        with patch.object(P, 'text', side_effect=lambda path: original(path) + ('changed' if path.name == 'common.txt' else '')):
            with self.assertRaises(S.ScoutError): P.resource_manifest()
            s = state()
            self.assertEqual(P.make_prompt(s, 'PLAIN', 2, 'PROMPT-BASE', version=baseline.VERSION),
                             baseline.make_prompt(s, 'PLAIN', 2, 'PROMPT-BASE'))

    def test_v004_packages_and_default_prompt_inputs_remain_unchanged(self):
        blueprints = F.blueprints(); rt = runtime.description(F.MODEL, 'a' * 64, 'FICTIONAL-2.1.302')
        before = frozen.assemble(blueprints, rt, 'SYNTHETIC')
        for version in (P.A, P.B):
            P.make_prompt(state(), 'FORGE', 2, 'PROMPT-X', version=version)
        self.assertEqual(before, frozen.assemble(blueprints, rt, 'SYNTHETIC'))
        self.assertTrue(all('prompt_research' not in name for name in frozen.implementation()))

    def test_legacy_engine_refuses_v002_instead_of_implicitly_activating_it(self):
        s = E.State()
        for row in F.blueprints()['HYBRID']['events'][:2]:
            E.apply(s, row['type'], row['record'], row['recorded_at'], replay=True)
        p = P.make_prompt(s, 'FORGE', 2, 'PROMPT-EXPLICIT', version=P.B)
        with self.assertRaises(S.ScoutError):
            E.apply(s, 'prompt', p, s.batch['knowledge_cutoff'])
        self.assertEqual(s.prompts, {})


class EvaluationResearchTests(unittest.TestCase):
    def record(self, status='VALID', total_output=12000):
        return {'slot': V.order()[0]['slot'], 'status': status, 'cards_returned': 2,
                'usage': dict(zip(policy.COMPONENTS, (1000, 1000, 1000, total_output))), 'model_usage': None,
                'generation_seconds': 20, 'generation_human_minutes': 2, 'review_minutes': S.UNKNOWN,
                'cli_list_price_usd': 9.99, 'subscription_charge': S.UNKNOWN, 'subscription_currency': S.UNKNOWN}

    def test_balanced_frozen_order_and_fixed_denominators(self):
        rows = V.order(); self.assertEqual(len(rows), 18)
        self.assertEqual(len({r['slot'] for r in rows}), 18)
        for arm in V.ARMS:
            self.assertEqual(Counter(r['position_in_block'] for r in rows if r['arm'] == arm), {1: 2, 2: 2, 3: 2})
        report = V.inventory([])
        self.assertEqual(report['intended_card_slots'], 36)
        self.assertEqual(len(report['slots']), 18)
        self.assertFalse(report['complete_comparison'])
        self.assertTrue(all(r['status'] == 'UNDISPATCHED' for r in report['slots']))
        self.assertTrue(all(r['reported_token_total'] == S.UNKNOWN for r in report['arms'].values()))

    def test_invalid_surplus_failures_and_unknown_effort_are_not_dropped(self):
        r = self.record('INVALID'); r['cards_returned'] = 3
        report = V.inventory([r]); arm = report['arms'][V.ARMS[0]]
        self.assertEqual(arm['returned_cards_including_invalid_surplus'], 3)
        self.assertEqual(arm['undispatched_attempts'], 5)
        self.assertEqual(arm['intended_card_slots'], 12)
        self.assertEqual(arm['total_human_minutes'], S.UNKNOWN)
        self.assertEqual(arm['M_investigation_worthy_count'], S.UNKNOWN)
        self.assertFalse(report['complete_comparison'])
        with self.assertRaises(S.ScoutError): V.inventory([r, r])

    def test_inclusive_resource_components_conflicts_and_billing_are_separate(self):
        r = self.record(total_output=119304)  # 122304 inclusive; permitted numerically, elevated.
        report = V.inventory([r]); resource = report['slots'][0]['resource']
        self.assertEqual(resource['reported_combined_total'], 122304)
        self.assertEqual(resource['classification'], 'ELEVATED_USAGE_RECORDED')
        self.assertEqual(report['arms'][V.ARMS[0]]['subscription_charge'], S.UNKNOWN)
        r['usage']['output_tokens_details'] = {'thinking_tokens': 4000}
        self.assertEqual(V.inventory([r])['slots'][0]['resource']['reported_combined_total'], 122304)
        r['model_usage'] = dict(zip(policy.MODEL_COMPONENTS, (1000, 1000, 1000, 1)))
        self.assertEqual(V.inventory([r])['slots'][0]['resource']['reported_combined_total'], S.UNKNOWN)
        r['usage'] = {}; r['model_usage'] = None
        self.assertEqual(V.inventory([r])['arms'][V.ARMS[0]]['reported_token_total'], S.UNKNOWN)

    def test_duplicate_flags_are_not_scientific_novelty_or_M_decisions(self):
        p = P.make_prompt(state(), 'FORGE', 2, 'PROMPT-X', version=P.B)
        idea = F.output(p)['ideas'][0]
        flags = V.duplicate_flags([idea, copy.deepcopy(idea)])
        self.assertEqual(flags['warnings'][0]['kind'], 'EXACT_CORE_DUPLICATE')
        self.assertFalse(flags['economic_identity_established'])
        self.assertFalse(flags['M_or_H_certified'])
        self.assertEqual(flags['external_novelty'], 'NOT_CHECKED')

    def test_stop_deviations_preserved_but_format_failure_is_separate(self):
        r = self.record('INVALID')
        later = copy.deepcopy(r); later['slot'] = V.order()[1]['slot']
        normal = V.inventory([r, later])
        self.assertEqual(normal['recorded_stop_conditions'], [])
        r['usage'] = {}
        bad = V.inventory([r, later])
        self.assertEqual(bad['recorded_activity_after_stop'], [later['slot']])
        self.assertEqual(bad['intended_card_slots'], 36)
        self.assertEqual(bad['slots'][0]['status'], 'INVALID')
