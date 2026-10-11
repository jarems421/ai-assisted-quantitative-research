import copy
from datetime import datetime, timezone
import json
import unittest

from src.research.exp003_policy import certified_insider, shortfall_allocation, paired_eligibility, select_composite, neighbors, compile_templates
from src.research.ingestion import eligible
from src.research.readiness_exp003 import decisions, request
from src.research.spec import ROOT, validate


def evidence():
    return {'comparison_audited':True,'critical_rules_pass':True,
            'same_control_horizon_holdings':True,'same_dates_universe_costs':True,
            'pooled_mean_daily_excess':.001,'pooled_sharpe_difference':.1,
            'paired_folds':[{'scheduled_decisions':12,'participating_decisions':11,
                             'mean_daily_excess':.001,'sharpe_difference':.1} for _ in range(4)],
            'neighbor_mean_effect_dispersion':.0001,'mean_traded_notional_fraction':.1,
            'parameters':{'momentum_lookback_calendar_days':180,'insider_lookback_calendar_days':30,'number_of_holdings':20}}


class EXP003ReadinessTests(unittest.TestCase):
    def test_absent_events_without_certificate_never_zero(self):
        r=certified_insider([], 'stable',datetime(2016,1,1,tzinfo=timezone.utc),90)
        self.assertEqual(r['status'],'UNAVAILABLE');self.assertIsNone(r['value'])

    def test_audited_window_and_identity_required_for_zero(self):
        at=datetime(2016,1,1,tzinfo=timezone.utc)
        cert={'security_id':'stable','evidence_sha256':'evidence','identity_evidence_sha256':'identity',
              'complete_event_versions':True,'amendments_reconciled':True,'audited':True,
              'start':'2015-01-01T00:00:00Z','end':'2016-01-01T00:00:00Z'}
        self.assertEqual(certified_insider([], 'stable',at,90,cert)['value'],0)
        for change in ({'security_id':'different'},{'start':'2015-12-01T00:00:00Z'},
                       {'amendments_reconciled':False},{'end':'2015-12-31T23:59:59Z'}):
            self.assertIsNone(certified_insider([], 'stable',at,90,dict(cert,**change))['value'])

    def test_shortfall_does_not_inflate_remaining_positions(self):
        r=shortfall_allocation(10,20)
        self.assertEqual(r['nominal_deployment_percent'],47.5)
        self.assertEqual(r['nominal_percent_per_security'],4.75)
        self.assertEqual(shortfall_allocation(0,40)['nominal_cash_percent'],100)
        self.assertEqual(shortfall_allocation(60,40)['holdings'],40)

    def test_standalone_high_sharpe_cannot_qualify(self):
        spec=json.loads((ROOT/'experiments/EXP003/spec.json').read_text(encoding='utf-8'))
        self.assertFalse(eligible(spec,{'sharpe':100}, {'participation':1,'breadth':100,'completed_trades':1000}))
        self.assertTrue(eligible(spec,{},evidence()))

    def test_both_effects_and_every_fold_participation_required(self):
        for change in ({'pooled_mean_daily_excess':0},{'pooled_sharpe_difference':-1},
                       {'critical_rules_pass':False},{'same_dates_universe_costs':False},
                       {'pooled_mean_daily_excess':float('nan')}):
            self.assertFalse(paired_eligibility(dict(evidence(),**change)))
        e=evidence();e['paired_folds'][0]['participating_decisions']=10
        self.assertFalse(paired_eligibility(e))

    def test_selection_fixed_sensitivity_then_turnover_ties(self):
        from src.research.design_exp003 import evaluation_plan
        cells=[]
        for parameters in evaluation_plan()['family_cells']['momentum_insider']:
            c=evidence();c['parameters']=parameters;c['pooled_mean_daily_excess']=-1;cells.append(c)
        a,b=cells[:2]
        a['pooled_mean_daily_excess']=b['pooled_mean_daily_excess']=.001
        b['neighbor_mean_effect_dispersion']=.00005
        self.assertIs(select_composite(cells),b)
        a['neighbor_mean_effect_dispersion']=b['neighbor_mean_effect_dispersion'];a['mean_traded_notional_fraction']=.01
        self.assertIs(select_composite(cells),a)
        self.assertEqual(len(neighbors(a['parameters'])),3)
        with self.assertRaisesRegex(ValueError,'Complete eight-cell surface'):select_composite(cells[:2])

    def test_calendar_first_sessions_and_cutoff(self):
        ds=decisions(2015)
        self.assertEqual(len(ds),12);self.assertEqual(ds[0]['prior_session'],'2014-12-31')
        self.assertEqual(ds[0]['session'],'2015-01-02')
        self.assertEqual(decisions(2018)[8]['session'],'2018-09-04')
        self.assertEqual(request(2017)['params'][0],'2015-12-31')
        self.assertEqual(request(2018)['params'][0],'2016-12-29')
        with self.assertRaises(ValueError):request(2021)
        for y in range(2015,2021):
            self.assertLessEqual(request(y)['params'][1],'2020-12-31')

    def test_benchmarks_are_sdk_structures_not_remote_portfolios(self):
        r=compile_templates()
        self.assertEqual(r['remote_calls'],0)
        self.assertIn('UNPUBLISHED',json.dumps(r['matched_momentum']))
        self.assertEqual(r['explicit_SPY']['initialValue'],25000)
        self.assertNotIn('portfolioId',r['explicit_SPY'])

    def test_new_policy_does_not_bypass_source_gate(self):
        s=json.loads((ROOT/'experiments/EXP003/spec.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError,'Point-in-time availability unestablished'):
            validate(s)
        s['data_sources'][1]['point_in_time_verified']=True
        s['selection']['minimum_participation']=.35
        with self.assertRaisesRegex(ValueError,'scheduled 90% participation'):validate(s)


if __name__=='__main__':unittest.main()
