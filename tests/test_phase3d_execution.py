import copy
from decimal import Decimal
import unittest
from src.research.phase3d.execution import LocalReferenceAdapter, NexusAdapter, reconcile_outputs
from src.research.phase3d.fixtures import tiny, event, cases
from src.research.spec import digest


class ExecutionTests(unittest.TestCase):
    def run_fixture(self,data): return LocalReferenceAdapter().execute(data)

    def test_ordinary_buy_hold_sell_hand_accounting(self):
        out=self.run_fixture(cases()['ordinary'])
        self.assertEqual([Decimal(r['nav']) for r in out['nav']],[Decimal(1000),Decimal(1100),Decimal(1050)])
        self.assertEqual([r['quantity'] for r in out['fills']],['50.0','-50.0'])
        self.assertEqual(out['positions'][-1]['holdings'],{})

    def test_dividend_receivable_payment_no_double_credit(self):
        out=self.run_fixture(cases()['dividend'])
        self.assertEqual(Decimal(out['nav'][1]['nav']),1150)
        self.assertEqual(Decimal(out['nav'][1]['receivables']),50)
        self.assertEqual(Decimal(out['nav'][-1]['cash']),550)
        self.assertEqual(Decimal(out['nav'][-1]['receivables']),0)

    def test_split_keeps_economic_value(self):
        out=self.run_fixture(cases()['split'])
        self.assertEqual(Decimal(out['positions'][1]['holdings']['EXP999-A']),100)
        self.assertEqual(Decimal(out['nav'][1]['nav']),1000)

    def test_rename_keeps_stable_identity_and_population(self):
        out=self.run_fixture(cases()['rename'])
        self.assertEqual(out['populations'][1]['identities'],[('EXP999-A','NEW')])
        self.assertEqual(Decimal(out['nav'][-1]['nav']),1050)

    def test_cash_acquisition_no_disappearance(self):
        out=self.run_fixture(cases()['cash_acquisition'])
        self.assertEqual(Decimal(out['nav'][1]['nav']),1250)
        self.assertEqual(out['positions'][1]['holdings'],{})
        self.assertEqual(out['populations'][1]['identities'],[])

    def test_stock_conversion_and_explicit_cancellation(self):
        data=cases()['cash_acquisition']; successor=dict(data['bindings'][0],security_id='EXP999-B',ticker='B',issuer_cik='998',effective_from='2020-01-03T00:00:00Z',effective_to='2021-01-01T00:00:00Z')
        data['bindings'].append(successor)
        for s in data['sessions'][1:]: s['prices']={'EXP999-B':{'open':'30','close':'30'}}
        data['events']=[event('stock_merger',successor_security_id='EXP999-B',ratio='0.5')]
        out=self.run_fixture(data); self.assertEqual(Decimal(out['nav'][-1]['nav']),1250)
        self.assertEqual(Decimal(out['positions'][1]['holdings']['EXP999-B']),25)
        cancel=cases()['cash_acquisition']; cancel['events']=[event('cancellation',explicit_zero_recovery_evidence='synthetic court order')]
        self.assertEqual(Decimal(self.run_fixture(cancel)['nav'][1]['nav']),500)
        cancel['events'][0].pop('explicit_zero_recovery_evidence')
        with self.assertRaises(ValueError): self.run_fixture(cancel)

    def test_disappearance_even_unheld_and_unknown_terminal_fail(self):
        for exposure in ('0','0.5'):
            data=cases()['cash_acquisition']; data['rebalances'][0]['exposure']=exposure; data['events']=[]
            with self.assertRaises(ValueError): self.run_fixture(data)
        data=cases()['cash_acquisition']; data['events'][0]['status']='UNRESOLVED'
        with self.assertRaises(ValueError): self.run_fixture(data)

    def test_actual_turnover_fees_and_cash_no_hidden_scale(self):
        data=tiny(); data['fee_bps']='30'
        out=self.run_fixture(data); self.assertEqual(Decimal(out['nav'][0]['cash']),Decimal('498.5'))
        self.assertEqual(Decimal(out['fills'][0]['fee']),Decimal('1.5'))
        data['rebalances'][0]['exposure']='1'
        with self.assertRaises(ValueError): self.run_fixture(data)

    def test_future_signal_missing_price_substitution_and_overlap_fail(self):
        for mutate in (lambda d:d['rebalances'][0]['observations'][0].update(available_at='2020-01-03T00:00:00Z'),
                       lambda d:d['sessions'][1]['prices'].clear(),
                       lambda d:d['rebalances'][0]['observations'][0].update(security_id='SUBSTITUTE'),
                       lambda d:d['bindings'].append(copy.deepcopy(d['bindings'][0])),
                       lambda d:d['sessions'][1].update(open_at=d['sessions'][0]['close_at'])):
            data=tiny(); mutate(data)
            with self.assertRaises(ValueError): self.run_fixture(data)

    def test_action_order_and_receivable_unknowns_fail(self):
        for mutate in (lambda d:d['events'][0].update(pay_session='2030-01-01'),
                       lambda d:d['events'][0].update(share_basis='UNKNOWN'),
                       lambda d:d['events'].append(event('split',ratio='2'))):
            data=cases()['dividend']; mutate(data)
            with self.assertRaises(ValueError): self.run_fixture(data)

    def test_receipt_reconciliation_catches_equal_count_changes(self):
        out=self.run_fixture(tiny()); other=copy.deepcopy(out)
        self.assertEqual(reconcile_outputs(out,other)['status'],'PASS_EXACT_SEMANTIC_LEDGER')
        other['populations'][0]['identities']=[('SUBSTITUTE','OLD')]
        other['receipt_sha256']=digest({k:v for k,v in other.items() if k!='receipt_sha256'})
        with self.assertRaises(ValueError): reconcile_outputs(out,other)

    def test_real_execution_and_nexus_disabled(self):
        data=tiny(); data['experiment_id']='EXP005'
        with self.assertRaises(ValueError): self.run_fixture(data)
        with self.assertRaises(ValueError): NexusAdapter().execute(tiny())
