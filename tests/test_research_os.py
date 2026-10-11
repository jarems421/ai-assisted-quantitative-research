"""Synthetic-only Research OS tests. No SDK transport or Nexus tool is invoked."""
import copy
import json
import math
import tempfile
import unittest
from datetime import date
from pathlib import Path

from jsonschema import ValidationError
from src.research.spec import ROOT, validate, enforce_range, utc_bounds, digest, audit_availability
from src.research.store import Store, RawStore
from src.research.budget import plan
from src.research.analysis import controls, surface, rank_stability, paired_bootstrap, holm, validate_folds, regime_metrics
from src.research.aurora import launch, prompts, quality, DIMENSIONS, corpus_evidence
from src.research.dynamic import build, turnover_gate
from src.research.nexus import Jobs, retry_read, SDK
from src.research.extraction import extract, decode_page
from src.research.demo import FakeSDK, fake_mcp, payload, demo
from src.research.report import compute


def fixture():
    return json.loads((ROOT / "tests/fixtures/research_os/EXP999.json").read_text())


class SchemaTests(unittest.TestCase):
    def test_complete_spec(self):
        self.assertEqual(validate(fixture())["experiment_id"], "EXP999")

    def test_missing_field_and_unknown_field(self):
        for change in (lambda s:s.pop("hypothesis"), lambda s:s.update(invented=True)):
            s=fixture();change(s)
            with self.assertRaises(ValidationError):validate(s)

    def test_overlap_reversed_inner_and_test_seal(self):
        for section, start, end in (("outer_validation","2020-01-01","2021-01-01"),
                                    ("development","2020-01-01","2015-01-01"),
                                    ("inner_validation","2021-01-01","2021-12-31")):
            s=fixture();s["windows"][section]={"start":start,"end":end}
            with self.assertRaises(ValueError):validate(s)
        s=fixture();s["sealed_ranges"]=[]
        with self.assertRaises(ValueError):validate(s)

    def test_point_in_time_and_immutable_exp001(self):
        s=fixture();s["data_sources"][0]["point_in_time_verified"]=False
        with self.assertRaises(ValueError):validate(s)
        s=fixture();s["experiment_id"]="EXP001"
        with self.assertRaises(ValueError):validate(s)

    def test_development_cannot_see_validation_or_test(self):
        for start,end in (("2021-01-01","2021-02-01"),("2023-01-01","2023-01-02")):
            with self.assertRaises(ValueError):enforce_range(fixture(),"DEVELOPMENT",start,end)
        self.assertTrue(enforce_range(fixture(),"DEVELOPMENT","2015-01-01","2020-12-31"))

    def test_validation_cannot_see_test(self):
        with self.assertRaises(ValueError):enforce_range(fixture(),"VALIDATION","2023-01-01","2023-01-02")

    def test_sealed_requires_specific_authorization(self):
        with self.assertRaises(ValueError):enforce_range(fixture(),"TEST_AUTHORIZED","2023-01-01","2024-12-31")
        self.assertTrue(enforce_range(fixture(),"TEST_AUTHORIZED","2023-01-01","2024-12-31",test_authorized=True))

    def test_new_york_session_boundary(self):
        first,last=utc_bounds("2026-10-08","2026-10-08")
        self.assertEqual(first,"2026-10-08T04:00:00+00:00")
        self.assertEqual(last,"2026-10-09T03:59:59.999000+00:00")

    def test_availability_not_trade_date(self):
        with self.assertRaises(ValueError):audit_availability([{"available_at":"2020-01-02T15:00:00Z"}],"2020-01-02T14:00:00Z")
        self.assertEqual(audit_availability([{"available_at":"2020-01-02T13:00:00Z"}],"2020-01-02T14:00:00Z")["rows"],1)

    def test_nonfinite_json_and_inconsistent_fees_rejected(self):
        s=fixture();s['costs']['fee_percent']=float('nan')
        with self.assertRaises(ValueError):validate(s)
        s=fixture();s['costs']['fee_contract']['Stock']['amount']=.2
        with self.assertRaises(ValueError):validate(s)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name));self.spec=fixture();self.store.register(self.spec)

    def tearDown(self):
        self.store.close();self.tmp.cleanup()

    def test_sequential_transition_and_freeze_hash(self):
        with self.assertRaises(ValueError):self.store.transition(self.spec,"VALIDATION")
        self.store.transition(self.spec,"HYPOTHESIS_FROZEN")
        self.spec["hypothesis"]="Changed after freeze"
        with self.assertRaises(ValueError):self.store.verify(self.spec)

    def test_candidate_freeze_requires_eligible_trial(self):
        self.store.transition(self.spec,"HYPOTHESIS_FROZEN");self.store.transition(self.spec,"DEVELOPMENT")
        with self.assertRaises(ValueError):self.store.transition(self.spec,"CANDIDATE_FROZEN",candidate={"portfolio":{},"controls":[]})

    def test_live_stage_never_exists(self):
        with self.assertRaises(ValueError):self.store.transition(self.spec,"LIVE")

    def test_trials_keep_failed_results(self):
        self.store.record_trial("failed", "EXP999", "f", "c",{},"DEVELOPMENT",{"status":"FAILED"},eligibility=False)
        self.store.record_trial("ugly", "EXP999", "f", "d",{},"DEVELOPMENT",{"status":"COMPLETE","return":-.8},eligibility=False)
        trials=json.loads((Path(self.tmp.name)/"experiments/EXP999/trials.json").read_text())
        self.assertEqual(len(trials),2)
        self.assertEqual(trials[0]["result"]["status"],"FAILED")

    def test_assessed_metrics_and_provenance_cannot_be_rewritten(self):
        self.store.record_trial('k','EXP999','f','c',{},'DEVELOPMENT',{'status':'COMPLETE','metrics':{'sharpe':1}},eligibility=True)
        with self.assertRaises(ValueError):self.store.record_trial('k','EXP999','f','c',{},'DEVELOPMENT',{'status':'COMPLETE','metrics':{'sharpe':2}})
        with self.assertRaises(ValueError):self.store.record_trial('k','EXP999','f','different',{},'DEVELOPMENT',{'status':'COMPLETE'})
        self.store.record_trial('k','EXP999','f','c',{},'DEVELOPMENT',{'status':'COMPLETE'})
        row=json.loads(self.store.db.execute('SELECT result FROM trials').fetchone()[0])
        self.assertEqual(row['metrics']['sharpe'],1);self.assertEqual(len(row['history']),1)

    def test_raw_immutable_and_path_safe(self):
        raw=RawStore(Path(self.tmp.name)/"raw")
        first=raw.write("run/page.json",{"all":{"fields":True}})
        self.assertEqual(first,raw.write("run/page.json",{"all":{"fields":True}}))
        with self.assertRaises(ValueError):raw.write("run/page.json",{"changed":True})
        with self.assertRaises(ValueError):raw.write("../outside.json",{})


class BudgetTests(unittest.TestCase):
    def setUp(self):self.pricing=json.loads((ROOT/"config/research_pricing.json").read_text());self.spec=fixture()

    def test_daily_screen_and_optimizer_asset_factor(self):
        self.assertEqual(plan(self.spec,"backtest",self.pricing,assets=500,now=date(2026,10,11))["estimated_tokens"],0)
        self.assertEqual(plan(self.spec,"sweep",self.pricing,assets=500,evaluations=200,now=date(2026,10,11))["estimated_tokens"],4)

    def test_expired_huge_and_reserved_budget(self):
        for kwargs in ({"now":date(2030,1,1)},{"evaluations":1001,"now":date(2026,10,11)},
                       {"used_tokens":19,"evaluations":200,"now":date(2026,10,11)}):
            with self.assertRaises(ValueError):plan(self.spec,"sweep",self.pricing,assets=500,**kwargs)

    def test_walk_forward_fold_multiplier_and_aurora_quote(self):
        self.assertEqual(plan(self.spec,"walk_forward",self.pricing,assets=500,evaluations=100,folds=3,now=date(2026,10,11))["estimated_tokens"],6)
        with self.assertRaises(ValueError):plan(self.spec,"aurora",self.pricing,assets=1,now=date(2026,10,11))


class AnalysisTests(unittest.TestCase):
    def test_controls_and_ablations(self):
        variants=controls(["momentum","insider","institutional"])
        self.assertEqual(len(variants),8)
        self.assertIn({"signals":[],"kind":"benchmark"},variants)

    def test_isolated_optimum_and_flat_plateau(self):
        ranges={"x":[0,1,2]}
        sharp=surface([{"parameters":{"x":x},"score":10 if x==1 else 0} for x in range(3)],ranges)
        self.assertTrue(sharp["isolated_optimum_warning"])
        flat=surface([{"parameters":{"x":x},"score":1} for x in range(3)],ranges)
        self.assertEqual(flat["broad_plateau_score"],1)
        with self.assertRaises(ValueError):surface([],ranges)

    def test_rank_stability(self):
        r=rank_stability([{"a":1,"b":2,"c":3},{"a":3,"b":2,"c":1}])
        self.assertAlmostEqual(r["adjacent_fold_spearman"][0],-1)

    def test_paired_bootstrap_deterministic_and_pair_preserving(self):
        data=[.01,-.01,.02,.01,-.02,.02]
        first=paired_bootstrap(data,data,block_length=2,draws=50,seed=8)
        self.assertEqual(first["ci_95"],[0,0])
        self.assertEqual(first,paired_bootstrap(data,data,block_length=2,draws=50,seed=8))

    def test_holm_includes_unsuccessful_trials(self):
        result=holm({"a":.01,"b":.03,"failed":1})
        self.assertAlmostEqual(result["a"]["adjusted_p"],.03)
        self.assertAlmostEqual(result["b"]["adjusted_p"],.06)
        self.assertFalse(result["b"]["reject"])

    def test_walk_forward_no_later_fold_leakage(self):
        f={"training":{"start":"2015-01-01","end":"2016-12-31"},"held_out":{"start":"2017-01-02","end":"2017-12-31"},"selected_parameters":{},"metrics":{}}
        self.assertEqual(validate_folds([f],fixture()["windows"]["development"],embargo_days=1)["fold_count"],1)
        f["training"]["end"]="2017-06-01"
        with self.assertRaises(ValueError):validate_folds([f],fixture()["windows"]["development"])

    def test_regimes_do_not_stitch_nonadjacent_closes(self):
        r=regime_metrics(["a","b","c","d"],[100,110,99,108.9],{"b":"bull","d":"bull","c":"bear"},initial_value=100)
        self.assertAlmostEqual(r["bull"]["mean_daily_return"],.1)

    def test_aurora_roles_blocked_and_quality_not_return(self):
        self.assertEqual(len(prompts(fixture())),5)
        with self.assertRaises(PermissionError):launch()
        self.assertEqual(quality({name:3 for name in DIMENSIONS},"Reasoned feedback")["mean_score"],3)

    def test_corpus_cutoff(self):
        with self.assertRaises(ValueError):corpus_evidence(fixture(),"recorded SQL",[{"end_date":"2021-01-01"}])

    def test_actual_dynamic_builder_and_cost_gate(self):
        import importlib
        p=importlib.import_module("nexustrade.portfolio")
        node=build(rank_indicator=p.Value(1),max_holdings=10,percentile=20)
        self.assertEqual(node["type"],"DynamicRebalance")
        self.assertEqual([x["type"] for x in node["pipeline"]],["SelectPercentile","SelectTop"])
        self.assertFalse(turnover_gate({},max_turnover=.2,max_cost=2,min_net_benefit=0)["eligible"])


class JobTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.spec=fixture();self.spec['execution']['requires_events']=True
        self.store=Store(self.root);self.store.register(self.spec)
        self.store.transition(self.spec,'HYPOTHESIS_FROZEN');self.store.transition(self.spec,'DEVELOPMENT')
        self.sdk=FakeSDK();self.calls=[]
        def bridge(name,args):self.calls.append((name,args));return fake_mcp(name,args)
        self.jobs=Jobs(self.store,self.sdk,mcp=bridge,sleep=lambda _:None)
        self.price=json.loads((ROOT/'config/research_pricing.json').read_text());self.price['expires_on']='2999-01-01'
        self.kw=dict(family='synthetic',candidate='candidate',parameters={},assets=1)

    def tearDown(self):self.store.close();self.tmp.cleanup()

    def submit(self,**options):return self.jobs.submit(self.spec,'backtest',payload(self.spec),self.price,**self.kw,**options)

    def force_stage(self,stage):
        # Fixture-only injection to isolate specific guard tests; no production bypass API.
        candidate={'portfolio':payload(self.spec)['portfolio'],'signals':['synthetic'],'signal_count':1,'controls':[],
                   'benchmarks':{'SYNTHETIC_BENCHMARK':{'name':'benchmark','strategies':[]}}}
        with self.store.db:self.store.db.execute('UPDATE experiments SET stage=?,candidate=?,candidate_hash=? WHERE id=?',
            (stage,json.dumps(candidate),digest(candidate),'EXP999'))
        return candidate

    def test_dry_run_no_job_or_trial_or_network(self):
        result=self.submit()
        self.assertTrue(result['dry_run']);self.assertEqual(self.sdk.submissions,0)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],0)

    def test_idempotent_submission_and_events_first(self):
        first=self.submit(execute=True);self.jobs.poll(self.spec,first['key'])
        second=self.submit(execute=True)
        self.assertEqual(first['key'],second['key']);self.assertEqual(self.sdk.submissions,1)
        self.assertEqual(self.calls[0][0],'query_backtest_events')
        self.assertEqual([c[1]['page'] for c in self.calls if c[0]=='query_backtest_events'],[1,2])
        integrity=self.jobs.raw.read('EXP999/synthetic_run/integrity.json')
        self.assertEqual(integrity['files']['events']['rows'],2)

    def test_unacknowledged_submission_never_retried(self):
        def uncertain(*a):self.sdk.submissions+=1;raise TimeoutError('Response lost')
        self.sdk.submit=uncertain
        with self.assertRaises(TimeoutError):self.submit(execute=True)
        with self.assertRaises(ValueError):self.submit(execute=True)
        self.assertEqual(self.sdk.submissions,1)
        self.assertEqual(self.store.db.execute('SELECT status FROM jobs').fetchone()[0],'UNKNOWN')

    def test_interrupted_extraction_resumes_saved_pages(self):
        raw=self.jobs.raw;calls=[]
        def interrupted(name,args):
            calls.append((name,args['page']))
            if name=='query_backtest_events' and args['page']==2:raise TimeoutError()
            return fake_mcp(name,args)
        with self.assertRaises(TimeoutError):extract(raw,interrupted,self.spec,'DEVELOPMENT','run',events_required=True)
        calls.clear()
        def resumed(name,args):calls.append((name,args['page']));return fake_mcp(name,args)
        result=extract(raw,resumed,self.spec,'DEVELOPMENT','run',events_required=True)
        self.assertNotIn(('query_backtest_events',1),calls)
        self.assertEqual(result['files']['events']['pages'],2)

    def test_unknown_schema_does_not_silently_end_pagination(self):
        with self.assertRaises(ValueError):decode_page({'content':[{'type':'text','text':'empty result'}]},'events',1)

    def test_out_of_range_simulation_but_admin_dates_preserved(self):
        raw=self.jobs.raw
        result=extract(raw,fake_mcp,self.spec,'DEVELOPMENT','ok',events_required=True)
        self.assertTrue(result['simulated_dates_within_window'])
        saved=raw.read('EXP999/ok/events_000001.json')
        self.assertIn('2030-01-01',saved['response']['content'][0]['text'])
        def leaked(name,args):return json.loads(json.dumps(fake_mcp(name,args)).replace('2015-01-02T21:00:00Z','2023-01-02T21:00:00Z'))
        with self.assertRaises(ValueError):extract(raw,leaked,self.spec,'DEVELOPMENT','bad',events_required=True)

    def test_read_transient_retry_and_permanent_no_retry(self):
        class Error(Exception):
            def __init__(self,status):self.status=status
        calls=[]
        def transient():
            calls.append(1)
            if len(calls)==1:raise Error(429)
            return 'ok'
        waits=[];self.assertEqual(retry_read(transient,sleep=waits.append),'ok');self.assertEqual(waits,[1])
        calls.clear()
        def permanent():calls.append(1);raise Error(400)
        with self.assertRaises(Error):retry_read(permanent,sleep=waits.append)
        self.assertEqual(len(calls),1)

    def test_range_and_fee_contract_before_network(self):
        for field,value in [('end_date','2024-12-31'),('fee_config',{}),('generate_events',False)]:
            p=payload(self.spec);p['args'][field]=value
            with self.assertRaises(ValueError):self.jobs.submit(self.spec,'backtest',p,self.price,execute=True,**self.kw)
        self.assertEqual(self.sdk.submissions,0)

    def test_validation_cannot_change_candidate(self):
        self.force_stage('VALIDATION');p=payload(self.spec)
        p['args'].update(start_date='2021-01-01',end_date='2022-12-31');p['portfolio']['name']='Altered'
        with self.assertRaises(ValueError):self.jobs.submit(self.spec,'backtest',p,self.price,execute=True,**self.kw)

    def test_missing_bridge_blocks_submission(self):
        self.jobs.mcp=None
        with self.assertRaises(ValueError):self.submit(execute=True)
        self.assertEqual(self.sdk.submissions,0)

    def test_test_and_paper_need_separate_human_approval(self):
        state=self.force_stage('ROBUSTNESS')
        directory=self.root/'experiments/EXP999'
        for filename in ['robustness.json','final_review.json']:
            (directory/filename).write_text(json.dumps({'spec_hash':digest(self.spec),'candidate_hash':digest(state),'review_complete':True}))
        with self.assertRaises(ValueError):self.store.transition(self.spec,'TEST_AUTHORIZED',confirmation='OPEN EXP999 TEST',human=False)
        with self.assertRaises(ValueError):self.store.transition(self.spec,'TEST_AUTHORIZED',confirmation='OPEN EXP998 TEST',human=True)
        self.store.transition(self.spec,'TEST_AUTHORIZED',confirmation='OPEN EXP999 TEST',human=True)
        self.assertNotIn('PAPER',json.loads(self.store.state('EXP999')['approvals']))
        with self.assertRaises(ValueError):self.jobs.deploy_paper(self.spec,'draft',execute=True)

    def test_no_skipping_failed_validation_job(self):
        self.force_stage('VALIDATION')
        with self.assertRaises(ValueError):self.store.transition(self.spec,'WALK_FORWARD')

    def test_sdk_missing_key_and_live_operation_rejected(self):
        with self.assertRaises(ValueError):SDK(api_key=None)
        with self.assertRaises(ValueError):SDK(api_key=None,client=object()).submit('live',{},'key')

    def test_cumulative_eval_ceiling_counts_prior_jobs(self):
        self.price['max_evaluations']=1
        self.submit(execute=True)
        p=payload(self.spec);p['portfolio']['name']='Second variant'
        with self.assertRaises(ValueError):self.jobs.submit(self.spec,'backtest',p,self.price,execute=True,**self.kw)

    def test_frozen_candidate_can_select_explicit_benchmark(self):
        frozen=self.force_stage('VALIDATION');p=payload(self.spec)
        p['portfolio']=frozen['benchmarks']['SYNTHETIC_BENCHMARK']
        p['args'].update(start_date='2021-01-01',end_date='2022-12-31')
        self.assertTrue(self.jobs.submit(self.spec,'backtest',p,self.price,**self.kw)['dry_run'])

    def test_successful_assessed_candidate_freeze_and_frozen_hash(self):
        from src.research.analysis import controls
        first=self.submit(execute=True);self.jobs.poll(self.spec,first['key'])
        self.store.record_trial(first['key'],'EXP999','synthetic','candidate',{},'DEVELOPMENT',{'status':'COMPLETE','metrics':{'sharpe':1}},run_id='synthetic_run',eligibility=True)
        candidate={'portfolio':payload(self.spec)['portfolio'],'trial_key':first['key'],'signals':['synthetic'],'signal_count':1,
                   'controls':controls(['synthetic']),'control_evidence':[],
                   'benchmarks':{'SYNTHETIC_BENCHMARK':{'name':'benchmark','strategies':[]}}}
        state=self.store.transition(self.spec,'CANDIDATE_FROZEN',candidate=candidate)
        self.assertEqual(state['candidate_hash'],digest(candidate))
        self.assertEqual(self.store.candidate(self.spec),candidate)
        with self.assertRaises(ValueError):self.store.transition(self.spec,'CANDIDATE_FROZEN',candidate=candidate)

    def test_all_optimizer_cells_count_in_ledger(self):
        from src.research.ingestion import sweep_cells
        source={'id':'sweep','status':'completed','result':{'opaque_surface':'saved in full'}}
        request={'family':'synthetic','candidate':'seed','payload':payload(self.spec)}
        with self.store.db:self.store.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
            ('parent','EXP999','sweep','DEVELOPMENT',json.dumps(request),'COMPLETED','sweep',json.dumps(source),None))
        cells=[{'parameters':{'lookback':a,'threshold':b},'status':'FAILED'} for a in [10,20,30] for b in [0,1,2]]
        normalized={'source_sha256':digest(source),'normalization_audited':True,'cells':cells}
        result=sweep_cells(self.store,self.spec,'parent',normalized)
        self.assertEqual(len(result['cell_trial_keys']),9)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM trials').fetchone()[0],9)
        self.assertTrue(all(json.loads(row[0])['status']=='FAILED' for row in self.store.db.execute('SELECT result FROM trials')))
        normalized['cells'].pop()
        with self.assertRaises(ValueError):sweep_cells(self.store,self.spec,'parent',normalized)


class ReportingTests(unittest.TestCase):
    def test_metrics_use_existing_frozen_definitions_and_are_deterministic(self):
        rows=[{'date':d,'timestamp':d+'T21:00:00Z','close_evidence_timestamp':d+'T21:00:00Z','portfolio_value':v}
              for d,v in [('2015-01-02',25000),('2015-01-05',25100),('2015-01-06',25050)]]
        runs={'candidate':{'stage':'DEVELOPMENT','closes':rows}}
        first=compute(fixture(),runs)
        self.assertEqual(first,compute(fixture(),runs));self.assertAlmostEqual(first['candidate']['total_return'],.002)
        rows[1]['date']=rows[0]['date']
        with self.assertRaises(ValueError):compute(fixture(),runs)

    def test_demo_no_real_nexus_or_workspace_mutation(self):
        result=demo();self.assertEqual(result['real_nexus_jobs'],0)
        self.assertTrue(result['idempotency_verified']);self.assertEqual(result['persistent_workspace_changes'],0)

    def test_report_cards_charts_and_benchmark_differences(self):
        from src.research.report import write
        rows=[{'date':d,'timestamp':d+'T21:00:00Z','close_evidence_timestamp':d+'T21:00:00Z','portfolio_value':v}
              for d,v in [('2015-01-02',25000),('2015-01-05',25100),('2015-01-06',25050)]]
        bundle={'runs':{'candidate':{'stage':'DEVELOPMENT','closes':rows},'benchmark':{'stage':'DEVELOPMENT','closes':copy.deepcopy(rows)}},
                'comparisons':[{'candidate':'candidate','benchmark':'benchmark'}],
                'limitations':['Synthetic only'],'interpretation':'No research claim; infrastructure fixture only.'}
        with tempfile.TemporaryDirectory() as directory:
            state={'stage':'DEVELOPMENT','candidate_hash':None,'approvals':'{}'}
            result=write(Path(directory),fixture(),state,bundle,[])
            self.assertEqual(result['benchmark_comparisons']['candidate minus benchmark']['total_return'],0)
            self.assertTrue((Path(directory)/'reports/EXP999_report.md').exists())
            self.assertTrue((Path(directory)/'docs/assets/research_os/EXP999/equity.png').exists())

    def test_cli_dry_propose_and_invalid_authorization_leave_no_files(self):
        from unittest.mock import patch
        from src.research.cli import main
        import io,contextlib
        with tempfile.TemporaryDirectory() as directory:
            with patch('src.research.cli.ROOT',Path(directory)):
                output=io.StringIO()
                with contextlib.redirect_stdout(output):main(['propose','EXP999','--dry-run'])
                self.assertIn('would_create',output.getvalue())
                self.assertEqual(list(Path(directory).iterdir()),[])

    def test_wrong_close_and_missing_values_rejected(self):
        rows=[{'date':d,'timestamp':d+'T21:00:00Z','close_evidence_timestamp':d+'T21:00:00Z','portfolio_value':25000}
              for d in ['2015-01-02','2015-01-05']]
        rows[0]['close_evidence_timestamp']='2015-01-02T14:30:00Z'
        with self.assertRaises(ValueError):compute(fixture(),{'candidate':{'stage':'DEVELOPMENT','closes':rows}})

    def test_optimizer_understated_config_and_paper_without_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory));spec=fixture();store.register(spec)
            try:
                store.transition(spec,'HYPOTHESIS_FROZEN');store.transition(spec,'DEVELOPMENT')
                price=json.loads((ROOT/'config/research_pricing.json').read_text());price['expires_on']='2999-01-01'
                job=payload(spec);job['args'].update(search_mode='Exhaustive',sweep_config={'genes':[{'field':'lookback','values':[1,2,3,4]}]},num_windows=1)
                with self.assertRaises(ValueError):Jobs(store,FakeSDK()).submit(spec,'sweep',job,price,family='f',candidate='c',parameters={},evaluations=9,assets=500)
                with store.db:store.db.execute("UPDATE experiments SET stage='PAPER_AUTHORIZED' WHERE id='EXP999'")
                with self.assertRaises(ValueError):store.transition(spec,'PAPER')
            finally:store.close()


if __name__=="__main__":unittest.main()
