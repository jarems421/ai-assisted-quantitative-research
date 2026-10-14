import copy,json,tempfile,unittest
from decimal import Decimal
from pathlib import Path
from src.research.exp004_local_execution import LocalEXP004Adapter,targets,exact_population,schema_gate,bounded

def fixture(cell='EW'):
    ids=['A','B'] if cell!='SPY' else ['SPY-ID']
    bindings=[{'security_id':s,'ticker':s,'asset_type':'CS','source_sha256':'fake'} for s in ids]
    return {'experiment_id':'EXP999','mode':'SYNTHETIC_INFRASTRUCTURE','cell':cell,
        'sessions':[{'day':day,'open_at':day+'T14:30:00Z','close_at':day+'T21:00:00Z','bindings':copy.deepcopy(bindings),
                     'prices':{s:{'open':'10','close':'10'} for s in ids}} for day in ('2017-01-03','2017-01-04','2017-02-01')],
        'rebalances':[{'day':'2017-01-03','decision_at':'2017-01-03T02:00:00Z','eligible_ids':ids,'executable_ids':ids,'values':{s:'1' for s in ids}}],
        'actions':[]}

def action(kind,**kw):
    return dict(event_id='fake',day='2017-01-04',sequence=0,security_id='A',kind=kind,
                source_sha256='fake',certified=True,available_at='2017-01-04T00:00:00Z',**kw)

class LocalEXP004Tests(unittest.TestCase):
    def run_fixture(self,data):return LocalEXP004Adapter().execute_fixture(data)
    def test_rank_ties_and_top20_40_and_shortfall(self):
        values={f'{i:02}':'1' for i in range(45)}
        for k in (20,40):
            t=targets(f'M180_K{k}',values);self.assertEqual(len(t),k);self.assertEqual(list(t),sorted(values)[:k]);self.assertEqual(sum(t.values()),Decimal('.95'))
        self.assertEqual(sum(targets('M365_K20',{'A':'-1','B':'-1'}).values()),Decimal('.095'))
    def test_fractional_95percent_funding_fee_cash_manual(self):
        d=fixture();d['sessions'][0]['prices']['A']['open']='12'
        out=self.run_fixture(d);a=next(f for f in out['fills'] if f['security_id']=='A')
        self.assertEqual(Decimal(a['fee']),Decimal('11.875'))
        self.assertAlmostEqual(float(a['quantity']),11875/12)
        self.assertEqual(Decimal(out['cash'][0]),Decimal('1226.25'))
    def test_EW_and_SPY_once_and_initial_NAV(self):
        for cell in ('EW','SPY'):
            out=self.run_fixture(fixture(cell));self.assertEqual(Decimal(out['nav'][0]),Decimal('24976.25'))
            self.assertEqual(sum(Decimal(f['fee']) for f in out['fills']),Decimal('23.75'))
        d=fixture('SPY');d['rebalances'].append(dict(d['rebalances'][0],day='2017-02-01'))
        with self.assertRaises(ValueError):self.run_fixture(d)
    def test_monthly_sell_before_buy_and_empty_cash(self):
        d=fixture();r=dict(d['rebalances'][0],day='2017-02-01',decision_at='2017-02-01T02:00:00Z',eligible_ids=['B'],executable_ids=['B'],values={'B':'1'})
        d['rebalances'].append(r);out=self.run_fixture(d)
        fills=[f for f in out['fills'] if f['day']=='2017-02-01'];self.assertEqual(fills[0]['security_id'],'A');self.assertLess(Decimal(fills[0]['quantity']),0)
        d['rebalances'][-1].update(eligible_ids=[],executable_ids=[],values={});out=self.run_fixture(d)
        self.assertEqual(Decimal(out['cash'][-1]),Decimal('24952.50000'));self.assertEqual(out['cash'][-1],out['nav'][-1])
    def test_split_preserves_value(self):
        d=fixture();d['actions']=[action('split',ratio='2')]
        for s in d['sessions'][1:]:s['prices']['A']={'open':'5','close':'5'}
        out=self.run_fixture(d);self.assertEqual(Decimal(out['nav'][1]),Decimal('24976.25'))
    def test_cash_dividend_entitlement_then_payment(self):
        d=fixture();d['actions']=[action('dividend',currency='USD',share_basis='CURRENT_AFTER_PRIOR_SEQUENCED_ACTIONS',cash_per_share='1',pay_day='2017-02-01')]
        out=self.run_fixture(d);self.assertEqual(Decimal(out['nav'][1]),Decimal('26163.75'))
        self.assertEqual(Decimal(out['cash'][1]),Decimal('1226.25'));self.assertEqual(Decimal(out['cash'][2]),Decimal('2413.75'))
    def test_rename_keeps_identity(self):
        d=fixture()
        for s in d['sessions'][1:]:s['bindings'][0]['ticker']='RENAMED'
        out=self.run_fixture(d);self.assertEqual(Decimal(out['nav'][-1]),Decimal('24976.25'))
    def terminal_fixture(self,kind,**kw):
        d=fixture();d['actions']=[action(kind,**kw)]
        for s in d['sessions'][1:]:s['bindings']=[b for b in s['bindings'] if b['security_id']!='A'];s['prices'].pop('A')
        return d
    def test_cash_merger_manual_proceeds(self):
        out=self.run_fixture(self.terminal_fixture('cash_merger',currency='USD',cash_per_share='15',pay_day='2017-01-04'))
        self.assertEqual(Decimal(out['nav'][1]),Decimal('30913.75'))
    def test_stock_merger_evidenced_successor(self):
        d=self.terminal_fixture('stock_merger',successor_security_id='C',ratio='0.5')
        for s in d['sessions'][1:]:s['bindings'].append(dict(security_id='C',ticker='C',asset_type='CS',source_sha256='fake'));s['prices']['C']={'open':'20','close':'20'}
        out=self.run_fixture(d);self.assertEqual(Decimal(out['nav'][1]),Decimal('24976.25'))
    def test_cancellation_recovery_cannot_be_invented(self):
        d=self.terminal_fixture('cancellation',currency='USD',cash_per_share='0',pay_day='2017-01-04')
        with self.assertRaisesRegex(ValueError,'recovery'):self.run_fixture(d)
        d['actions'][0]['recovery_evidence']='fake court order';self.assertEqual(Decimal(self.run_fixture(d)['nav'][1]),Decimal('13101.25'))
    def test_ended_held_security_cannot_forward_fill(self):
        d=self.terminal_fixture('cash_merger',currency='USD',cash_per_share='15',pay_day='2017-01-04');d['actions']=[]
        with self.assertRaisesRegex(ValueError,'disappears'):self.run_fixture(d)
    def test_missing_price_ambiguous_identity_and_substitution_fail(self):
        for mutation in (lambda d:d['sessions'][0]['prices'].pop('A'),lambda d:d['sessions'][0]['bindings'].append(copy.deepcopy(d['sessions'][0]['bindings'][0])),
                         lambda d:d['rebalances'][0].update(executable_ids=['A','SUBSTITUTE'])):
            d=fixture();mutation(d)
            with self.assertRaises(ValueError):self.run_fixture(d)
        with self.assertRaises(ValueError):exact_population(['A','B'],['A','C'])
        with self.assertRaises(ValueError):exact_population(['A'],['A','B'])
    def test_close_only_schema_never_supplies_open(self):
        self.assertEqual(schema_gate(['ticker','day','security_id','unadjustedClose'])['missing_fields'],['unadjustedOpen'])
    def test_no_real_fixture_or_later_sessions_or_unpushed_certificate(self):
        d=fixture();d['experiment_id']='EXP004'
        with self.assertRaises(ValueError):self.run_fixture(d)
        for day in ('2014-12-31','2021-01-01','2024-01-01','2026-01-01'):
            with self.assertRaises(ValueError):bounded(day)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'certificate.json';p.write_text(json.dumps({'status':'LOCAL_EXECUTION_BLOCKED'}))
            with self.assertRaisesRegex(ValueError,'has not passed'):LocalEXP004Adapter().execute({},p)
        from src.research.exp004_local_execution import ledger
        with self.assertRaisesRegex(ValueError,'certificate'):ledger({'experiment_id':'EXP004'})
    def test_receipt_is_repeatable_and_synthetic_reference_unchanged(self):
        a=self.run_fixture(fixture());b=self.run_fixture(fixture());self.assertEqual(a,b)
        self.assertEqual(a['receipt_sha256'],__import__('src.research.spec',fromlist=['digest']).digest({k:v for k,v in a.items() if k!='receipt_sha256'}))
    def test_unpaid_entitlement_cannot_fund_buys_and_no_leverage(self):
        d=fixture();s=copy.deepcopy(d['sessions'][-1]);s.update(day='2017-02-02',open_at='2017-02-02T14:30:00Z',close_at='2017-02-02T21:00:00Z');d['sessions'].append(s)
        d['actions']=[action('dividend',currency='USD',share_basis='CURRENT_AFTER_PRIOR_SEQUENCED_ACTIONS',cash_per_share='100',pay_day='2017-02-02')]
        d['rebalances'].append(dict(d['rebalances'][0],day='2017-02-01',decision_at='2017-02-01T02:00:00Z'))
        with self.assertRaisesRegex(ValueError,'Insufficient cash'):self.run_fixture(d)
    def test_extra_in_month_and_wrong_open_rejected(self):
        d=fixture();d['rebalances'].append(dict(d['rebalances'][0],day='2017-01-04'))
        with self.assertRaisesRegex(ValueError,'monthly'):self.run_fixture(d)
        d=fixture();d['sessions'][0]['open_at']='2017-01-03T15:30:00Z'
        with self.assertRaisesRegex(ValueError,'OPEN'):self.run_fixture(d)
