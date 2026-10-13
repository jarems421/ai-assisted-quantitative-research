import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from src.research.source_first import contract,validate,ProbeHTTP,DIMENSIONS,HARD_GATES,dimension,assess,neutral_sample,timing,mechanism_allowed,denominator_gate,frozen
from src.research.fda_pilot import missing_record
from src.research.phase3c.sources import put
from src.research.spec import digest


class SourceFirstTests(unittest.TestCase):
    def test_exact_surface_cap_and_no_expansion(self):
        m=contract();validate(m);self.assertLessEqual(len(m['surfaces']),6)
        for k,v in [('request_ceiling',37),('performance_authorized',True),('family_pilot_candidate4',True),('Phase4B_4C_authorized',True)]:
            bad=copy.deepcopy(m);bad[k]=v
            with self.assertRaises(ValueError):validate(bad)
        bad=copy.deepcopy(m);bad['surfaces']*=3
        with self.assertRaises(ValueError):validate(bad)

    def test_global_ceiling_across_per_surface_ledgers(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(36):put(Path(tmp)/'SEC/reservations'/f'{i}.json',{'request_started_at_utc':'2000-01-01T00:00:00+00:00'})
            m=contract();http=ProbeHTTP(m,m['surfaces'][1],root=tmp,transport=lambda *a:self.fail('37th start'))
            with self.assertRaises(ValueError):http.fetch(m['surfaces'][1]['primary'])
            self.assertEqual(len(http.starts()),36)

    def test_freeze_route_before_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);m=contract();put(root/'phase4a_source_probe_manifest.json',m)
            put(root/'phase4a_source_probe_freeze.json',{'manifest_sha256':digest(m)})
            with patch('src.research.source_first.DOCS',root):self.assertEqual(frozen(),m)
            bad=copy.deepcopy(m);bad['surfaces'][0]['primary']='https://example.invalid/'
            (root/'phase4a_source_probe_manifest.json').write_text(json.dumps(bad))
            with patch('src.research.source_first.DOCS',root):
                with self.assertRaises(ValueError):frozen()

    def test_surface_failure_does_not_reset_global_budget_or_retry_denial(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=contract()
            def fake(url,*a):return 403,{},b'original failure',url
            a=ProbeHTTP(m,m['surfaces'][0],root=tmp,transport=fake,sleep=lambda _:None)
            receipt,body=a.fetch(m['surfaces'][0]['primary']);self.assertEqual(a.archive.read(receipt['body']),body)
            with self.assertRaises(ValueError):a.fetch(m['surfaces'][0]['probes'][1]['url'])
            b=ProbeHTTP(m,m['surfaces'][1],root=tmp,transport=lambda u,*a:(200,{},b'{"results":[]}',u),sleep=lambda _:None)
            b.fetch(m['surfaces'][1]['primary']);self.assertEqual(len(b.starts()),2)

    def test_no_mechanism_before_access_and_hard_gate_evidence(self):
        row={'access_attempted':False,'dimensions':{k:dimension('PASS_BOUNDED_PROBE','synthetic','fixture') for k in DIMENSIONS}}
        with self.assertRaises(ValueError):assess(row)
        row['access_attempted']=True;self.assertTrue(assess(row))
        for k in HARD_GATES:
            bad=copy.deepcopy(row);bad['dimensions'][k]=dimension('UNKNOWN','unknown','fixture')
            with self.assertRaises(ValueError):mechanism_allowed(bad,'PREDICTIVE')

    def test_neutral_sample_preserves_source_order_and_missingness(self):
        a={'id':'a','outcome':None};b={'id':'b','outcome':'negative'}
        self.assertEqual(neutral_sample(json.dumps({'results':[a,b]}).encode(),'FR'),[a,b])
        with self.assertRaises(ValueError):neutral_sample(b'{"studies":[1,2,3]}','CT')
        self.assertNotEqual(missing_record('UNKNOWN'),missing_record('UNAVAILABLE'))

    def test_outcome_and_current_state_blocks_are_distinct(self):
        self.assertEqual(denominator_gate(success_selected=True,current_state_only=False),'BLOCKED_OUTCOME_SELECTION')
        self.assertEqual(denominator_gate(success_selected=False,current_state_only=True),'BLOCKED_HISTORICAL_PIT')

    def test_timing_never_approves_or_activates_policy(self):
        for kind in ('OBSERVED_DATE_ONLY','MODELED_BOUND_PLAUSIBLE','PRESENT_DAY_DATABASE_ONLY','UNKNOWN'):
            row=timing(kind);self.assertFalse(row['policy_approved']);self.assertFalse(row['trading_eligibility_activated'])
        with self.assertRaises(ValueError):timing('ACCEPTANCE_EQUALS_PUBLIC')

    def test_predictive_is_not_a_causal_certificate(self):
        row={'access_attempted':True,'dimensions':{k:dimension('PASS_BOUNDED_PROBE','synthetic','fixture') for k in DIMENSIONS}}
        for kind in ('PREDICTIVE','CAUSAL_CANDIDATE'):
            self.assertFalse(mechanism_allowed(row,kind)['causal_identification_certified'])
        with self.assertRaises(ValueError):mechanism_allowed(row,'ALPHA_PROVEN')

    def test_no_performance_or_old_pilot_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=contract();http=ProbeHTTP(m,m['surfaces'][0],root=tmp,transport=lambda *a:self.fail('Forbidden transport'))
            for url in ('https://api.tiingo.com/tiingo/daily/A/prices','https://www.ftc.gov/legal-library/browse/cases-proceedings','https://api.nexustrade.io/backtest'):
                with self.assertRaises(ValueError):http.fetch(url)
            self.assertEqual(len(http.starts()),0)
