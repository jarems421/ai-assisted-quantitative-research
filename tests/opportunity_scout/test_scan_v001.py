"""Opportunity Scout scan V001: the operator command around the merged pipeline, offline. Reuses the pipeline's fake
Claude CLI, fake Codex JSONL and fake Gemini transport; no process, network, credential, account directory or paid call."""
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

from src.research.opportunity_scout import schema as S, v004_package
from src.research.opportunity_scout.automation_v001 import pipeline as R
from src.research.opportunity_scout.exploratory_v001 import runner as X
from src.research.opportunity_scout.scan_v001 import __main__ as M, scan as N
from src.research.opportunity_scout.storage import Archive
from src.research.opportunity_scout.v004_r3 import package as R3
from tests.opportunity_scout import test_research_pipeline_v001 as RP

TODAY = date(2026, 10, 25)
SIGNED = datetime(2026, 10, 25, 14, 30, tzinfo=timezone.utc)


class Base(RP.Base):
    def setUp(self):
        super().setUp()
        self.reviewed = self.planned()  # the reviewed plan the configuration is copied from (stands in for Pilot 002)
        self.config = self.base / 'scan-config.json'
        N.configure(self.config, owner='Fixture Owner', from_plan=self.store, prices_valid_until='2026-11-30',
                    allowed_subscription_types=['max'], quiet_seconds=0)
        self.cfg = N.load_config(self.config)
        self.root, self.records = self.base / 'scans', self.base / 'records'

    def prepare(self, minute=0, **kwargs):
        return N.prepare(self.cfg, root=self.root, host=self.pipe, now=lambda: datetime(2026, 10, 25, 12, minute, tzinfo=timezone.utc), **kwargs)

    def check(self, store, **kwargs):
        return N.check(store, self.cfg, host=self.pipe, sleep=kwargs.pop('sleep', lambda s: None), today=kwargs.pop('today', TODAY), **kwargs)

    def run_scan(self, store, confirm, **kwargs):
        return N.run(store, self.cfg, confirm, channel='COMMAND_ARGUMENT', host=self.pipe, records=self.records,
                     now=lambda: SIGNED, sleep=lambda s: None, today=TODAY, **kwargs)

    def model_calls(self):
        return sum(k == 'MODEL' for k in self.host.runner.kinds()) + len(self.codex_calls) + len(self.gemini_calls)

    def claims(self, store):
        return sorted(x.name for x in (Path(store) / 'exports').glob('*claim*'))

    def written(self):
        return [f for d in (self.base,) for f in d.rglob('*') if f.is_file()]


class ScanTests(Base):
    def test_configuration_holds_no_secret_and_needs_a_named_human(self):
        text = self.config.read_text(encoding='utf-8')
        self.assertNotIn(RP.KEY, text); self.assertNotIn('executable_sha256', text)
        self.assertEqual(self.cfg['economic']['api_key_env'], 'GEMINI_API_KEY')
        with self.assertRaises(FileExistsError):
            N.configure(self.config, owner='Fixture Owner', from_plan=self.store, prices_valid_until='2026-11-30')
        for owner in ('Claude', 'OWNER', ''):
            with self.assertRaises(S.ScoutError):
                N.configure(self.base / f'other-{len(owner)}.json', owner=owner, from_plan=self.store, prices_valid_until='2026-11-30')
            self.assertFalse((self.base / f'other-{len(owner)}.json').exists())

    def test_each_scan_gets_a_new_plan_and_never_overwrites(self):
        first = self.prepare(0)
        with self.assertRaises(S.ScoutError):self.prepare(0)
        second = self.prepare(1, count=1, spend_cap_usd=0.5)
        a, b = R.load_plan(Archive(first)), R.load_plan(Archive(second))
        self.assertNotEqual(a['plan_sha256'], b['plan_sha256'])
        self.assertEqual((a['critic_requests_maximum'], b['critic_requests_maximum'], b['spend_cap_usd']), (4, 2, 0.5))
        self.assertEqual(self.model_calls(), 0)

    def test_check_starts_only_administrative_commands_and_summarises_the_exact_plan(self):
        store = self.prepare()
        events = len(Archive(store).load().events)
        result = self.check(store)
        self.assertTrue(result['ready'], result['blockers'])
        s = result['summary']
        self.assertEqual(s['plan_sha256'], R.load_plan(Archive(store))['plan_sha256'])
        self.assertEqual(s['requests'], {'generation_cli_processes': 1, 'critic_requests_maximum': 4, 'gemini_requests_maximum': 2,
                                         'attempts_per_request': 1, 'adversarial': 'never dispatched'})
        self.assertEqual(s['critics']['SCIENTIFIC']['auth'], 'CHATGPT_LOGIN'); self.assertTrue(s['critics']['ECONOMIC']['key_present'])
        self.assertEqual(s['generator']['account']['subscriptionType'], 'max')
        self.assertNotIn(RP.KEY, json.dumps(result)); self.assertNotIn('fictional@example.invalid', json.dumps(result))
        self.assertEqual(self.model_calls(), 0); self.assertEqual(self.claims(store), [])
        self.assertEqual(len(Archive(store).load().events), events)
        self.assertIn('ADMIN', self.host.runner.kinds()); self.assertTrue(self.admin_calls)

    def test_blockers_stop_before_anything_is_claimed(self):
        store = self.prepare()
        plan = R.load_plan(Archive(store))['plan_sha256']
        home_file = self.host.home / '.claude.json'
        cases = {
            'KEY_ABSENT': dict(setup=lambda: self.pipe.environ.pop('GEMINI_API_KEY'), undo=lambda: self.pipe.environ.update(GEMINI_API_KEY=RP.KEY)),
            'GEMINI_PRICES_EXPIRED': dict(today=date(2026, 12, 1)),
            'DEVELOPMENT_ACCOUNT_FILES_CHANGING': dict(sleep=lambda s: home_file.write_bytes(b'{"changed": true}')),
            'CLAUDE_EXECUTABLE_CHANGED': dict(setup=lambda: self.exe.write_bytes(b'updated'), undo=lambda: self.exe.write_bytes(b'fictional executable bytes')),
        }
        for code, case in cases.items():
            with self.subTest(code):
                case.get('setup', lambda: None)()
                kwargs = {k: case[k] for k in ('today', 'sleep') if k in case}
                result = self.check(store, **kwargs)
                self.assertFalse(result['ready']); self.assertTrue(any(code in b for b in result['blockers']), result['blockers'])
                with self.assertRaises(S.ScoutError):
                    N.run(store, self.cfg, plan, channel='COMMAND_ARGUMENT', host=self.pipe, records=self.records,
                          now=lambda: SIGNED, sleep=kwargs.get('sleep', lambda s: None), today=kwargs.get('today', TODAY))
                case.get('undo', lambda: None)()
        low = self.prepare(5, spend_cap_usd=0.1)  # fixture output cap 8,192 tokens: about USD 0.13 per request
        self.assertTrue(any('SPEND_CAP_TOO_LOW' in b for b in self.check(low)['blockers']))
        self.assertEqual(self.model_calls(), 0); self.assertEqual(self.claims(store), []); self.assertFalse(self.records.exists())

    def test_wrong_or_missing_confirmation_starts_nothing(self):
        store = self.prepare()
        plan = R.load_plan(Archive(store))['plan_sha256']
        for wrong in ('0' * 64, plan[:12], ''):
            with self.assertRaises(S.ScoutError):self.run_scan(store, wrong)
        self.assertEqual(M.ask(plan, read=lambda prompt: f'RUN {plan[:12]}'), plan)
        for typed in ('yes', 'RUN', f'run {plan[:12]}', plan):self.assertIsNone(M.ask(plan, read=lambda prompt: typed))
        self.assertEqual(self.model_calls(), 0); self.assertEqual(self.claims(store), []); self.assertFalse(self.records.exists())

    def test_confirmed_run_authorises_with_the_owner_and_actual_time_then_runs_once(self):
        store = self.store = self.prepare()  # the pipeline's fake critics answer for self.store
        plan = R.load_plan(Archive(store))
        out = self.run_scan(store, plan['plan_sha256'])
        self.assertEqual((out['outcome'], out['error']), ('COMPLETE', None))
        folder = self.records / store.name
        auth = json.loads((folder / 'authorisation.json').read_text(encoding='utf-8'))
        R.check_authorisation(auth, plan)
        self.assertEqual((auth['owner'], auth['approved_at'], auth['generation']['owner']), ('Fixture Owner', '2026-10-25T14:30:00+00:00', 'Fixture Owner'))
        self.assertTrue(auth['gemini_prepaid_auto_reload_disabled'] and auth['hosted_transmission_approved'])
        confirmation = json.loads((folder / 'confirmation.json').read_text(encoding='utf-8'))
        self.assertEqual((confirmation['channel'], confirmation['plan_sha256']), ('COMMAND_ARGUMENT', plan['plan_sha256']))
        result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
        self.assertEqual((result['pipeline_outcome'], result['claimed'], result['finished']), ('COMPLETE', True, True))
        self.assertEqual((sum(k == 'MODEL' for k in self.host.runner.kinds()), len(self.codex_calls), len(self.gemini_calls)), (1, 2, 2))
        calls = self.model_calls()
        with self.assertRaises(S.ScoutError):self.run_scan(store, plan['plan_sha256'])  # claimed: never a second run
        self.assertEqual(self.model_calls(), calls)
        self.assertFalse([f for f in self.written() if RP.KEY.encode() in f.read_bytes()])

    def test_existing_plan_like_pilot_002_runs_unchanged(self):
        before = hashlib.sha256((self.store / 'exports' / 'pipeline-plan.json').read_bytes()).hexdigest()
        result = self.check(self.store)
        self.assertEqual(result['summary']['plan_sha256'], self.reviewed['pipeline_plan_sha256'])
        out = self.run_scan(self.store, self.reviewed['pipeline_plan_sha256'])
        self.assertEqual(out['outcome'], 'COMPLETE')
        self.assertEqual(hashlib.sha256((self.store / 'exports' / 'pipeline-plan.json').read_bytes()).hexdigest(), before)
        self.assertFalse(self.root.exists())  # no replacement plan was created
        self.assertEqual(M.main(['--config', str(self.config), 'scan', '--archive', str(self.store), '--count', '2']), 2)

    def test_generation_budget_risk_is_reported_and_frozen_boundaries_hold(self):
        self.assertFalse(self.check(self.prepare(0))['warnings'])
        self.assertTrue(any('GENERATION_BUDGET_RISK' in w for w in self.check(self.prepare(1, count=3))['warnings']))
        for closure in (v004_package.implementation(), R3.implementation()):self.assertFalse([p for p in closure if 'scan_v001' in p])
        self.assertEqual(X.MAX_CARDS, 4); self.assertEqual(Archive(self.prepare(2)).load().batch['max_output_tokens'], 6000)
