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


if __name__=="__main__":unittest.main()
