"""Observed SDK adapter, durable job journal, and safe polling. No live methods."""
from __future__ import annotations

import json
import time
from pathlib import Path

from src.research.budget import plan
from src.research.extraction import extract
from src.research.spec import canonical, digest, enforce_range, stage_window
from src.research.store import RawStore

SUBMISSIONS = {"backtest": "create_backtest", "sweep": "create_systematic_sweep", "walk_forward": "create_walk_forward"}
READERS = {"backtest": "get_backtest", "sweep": "get_systematic_sweep", "walk_forward": "get_walk_forward"}


def retry_read(action, *, sleep=time.sleep, attempts=4):
    for attempt in range(attempts):
        try:
            return action()
        except Exception as error:
            status = getattr(error, "status", None)
            if not (isinstance(error, (TimeoutError, ConnectionError)) or status in (429, 502, 503, 504)) or attempt + 1 == attempts:
                raise
            retry_after=getattr(error,'retry_after',None)
            delay=float(retry_after) if retry_after is not None else min(30, 2 ** attempt)
            sleep(min(60,max(0,delay)))


class SDK:
    def __init__(self, *, api_key, client=None):
        if not api_key and client is None:
            raise ValueError("Registered API key required; anonymous workspace creation is disabled")
        if client is None:
            from nexustrade.client import NexusTradeClient
            client = NexusTradeClient(api_key=api_key)
        self.client = client

    def submit(self, kind, payload, key):
        if kind not in SUBMISSIONS:
            raise ValueError("Unsupported or prohibited Nexus operation")
        return getattr(self.client, SUBMISSIONS[kind])(payload, idempotency_key=key)

    def read(self, kind, operation_id):
        return getattr(self.client, READERS[kind])(operation_id)

    def paper(self, portfolio_id):
        # Observed SDK deploy is paper-only. It has no idempotency key.
        return self.client.deploy(portfolio_id)


class Jobs:
    def __init__(self, store, sdk, *, mcp=None, sleep=time.sleep):
        self.store, self.sdk, self.mcp, self.sleep = store, sdk, mcp, sleep
        self.raw = RawStore(store.root / "data/raw/research_os")

    def read_mcp(self,name,arguments):
        self.sleep(.5)  # Conservative two requests/second, plus transient backoff.
        return retry_read(lambda:self.mcp(name,arguments),sleep=self.sleep)

    def submit(self, *args, **kwargs):
        # Serialize quota checks and durable reservation across local processes.
        with self.store.db:
            self.store.db.execute("BEGIN IMMEDIATE")
            return self._submit(*args, **kwargs)

    def _submit(self, spec, kind, payload, pricing, *, family, candidate, parameters,
               assets=1, evaluations=1, folds=1, execute=False):
        state = self.store.verify(spec)
        stage = state["stage"]
        allowed = {"backtest": {"DEVELOPMENT", "VALIDATION", "TEST_AUTHORIZED", "ROBUSTNESS"},
                   "sweep": {"DEVELOPMENT"}, "walk_forward": {"WALK_FORWARD"}}
        if kind not in allowed or stage not in allowed[kind]:
            raise ValueError("Job prohibited at this research stage")
        args = payload.get("args", {})
        permitted_args = {"start_date", "end_date", "global_start_date", "global_end_date", "interval",
                          "initial_value", "dividend_policy", "generate_events", "fee_config", "baseline_symbol",
                          "sweep_config", "selection_policy", "search_mode", "fold_count", "engine_kind",
                          "walk_forward_mode", "embargo_days", "training_percent", "validation_percent",
                          "preview_only", "auto_run", "inner_mode", "genes", "num_windows"}
        if set(args) - permitted_args or "portfolioId" in payload or "portfolio_id" in payload:
            raise ValueError("Unreviewed job arguments or mutable portfolio references prohibited")
        if "baseline_symbol" in args and args["baseline_symbol"] not in spec["benchmarks"]:
            raise ValueError("Benchmark not declared")
        start = args.get("start_date", args.get("global_start_date"))
        end = args.get("end_date", args.get("global_end_date"))
        if not start or not end:
            raise ValueError("Explicit date range required")
        approved = "TEST" in json.loads(state["approvals"])
        window = enforce_range(spec, stage, start, end, test_authorized=approved)
        if stage != "DEVELOPMENT":
            frozen=self.store.candidate(spec)
            permitted=[frozen['portfolio'],*frozen.get('benchmarks',{}).values()]
            if digest(payload["portfolio"]) not in [digest(p) for p in permitted]:
                raise ValueError("Frozen candidate or benchmark changed")
        if args.get("interval", "Day") != spec["execution"]["interval"]:
            raise ValueError("Interval differs from the frozen specification")
        if kind == "backtest" and (args.get("initial_value") != spec["costs"]["initial_value"]
                or args.get("dividend_policy") != spec["costs"]["dividend_policy"]
                or args.get("generate_events", False) != spec["execution"]["requires_events"]):
            raise ValueError("Funding, dividend, or event configuration differs from specification")
        expected_fee = spec["costs"]["fee_contract"]
        if args.get("fee_config") != expected_fee:
            raise ValueError("Explicit frozen fee contract required")
        request = {"kind": kind, "payload": payload, "spec_hash": digest(spec), "stage": stage,
                   "family": family, "candidate": candidate, "parameters": parameters}
        key = "research-" + digest(request)
        existing = self.store.db.execute("SELECT * FROM jobs WHERE key=?", (key,)).fetchone()
        if existing:
            if existing["status"] in ("SUBMITTING", "UNKNOWN"):
                raise ValueError("Uncertain submission: reconcile the persisted key; do not blindly resubmit")
            return dict(existing)
        families = {r[0] for r in self.store.db.execute("SELECT family FROM trials WHERE experiment=? AND stage='DEVELOPMENT'", (spec["experiment_id"],))}
        if stage == "DEVELOPMENT" and len(families | {family}) > spec["candidate_family_budget"]:
            raise ValueError("Declared family budget exceeded, including failed trials")
        if kind == "sweep":
            import math
            planned = math.prod(len(values) for values in spec["optimization_ranges"].values())
            if evaluations != planned or args.get("search_mode") != "Exhaustive":
                raise ValueError("Sweep execution requires the full declared exhaustive grid estimate")
        if kind in ('sweep','walk_forward') and args.get('inner_mode')!='backtest_only':
            genes=args.get('genes') or args.get('sweep_config',{}).get('genes')
            if not isinstance(genes,list) or not genes:
                raise ValueError('Explicit typed compiled gene list required; unknown config shapes fail closed')
            axes={g.get('field'):g.get('values') for g in genes}
            if len(axes)!=len(genes) or axes!=spec['optimization_ranges']:
                raise ValueError('Actual compiled genes differ from the frozen parameter grid')
            import math
            if evaluations!=math.prod(len(v) for v in axes.values()):
                raise ValueError('Estimated evaluation count differs from actual declared genes')
            # Avoid hidden rolling-window amplification or unbounded generational defaults.
            if args.get('search_mode') not in ('Exhaustive','exhaustive') or args.get('num_windows')!=1:
                raise ValueError('Use a bounded exhaustive plan; multi-window amplification requires a reviewed planner extension')
        if kind == "walk_forward" and args.get("fold_count") != folds:
            raise ValueError("Fold estimate differs from actual request")
        prior_evaluations = sum(json.loads(r[0]).get("budget", {}).get("planned_evaluations", 0)
                                for r in self.store.db.execute("SELECT request FROM jobs WHERE experiment=?", (spec["experiment_id"],)))
        if prior_evaluations + evaluations*folds > pricing["max_evaluations"]:
            raise ValueError("Cumulative evaluation ceiling exceeded, including unresolved jobs")
        used = 0
        for row in self.store.db.execute("SELECT request FROM jobs WHERE experiment=?", (spec["experiment_id"],)):
            prior = json.loads(row[0]).get("budget", {})
            category = {"backtest": "intraday_confirmation" if args.get("interval") == "Minute" else "candidate_backtests",
                        "sweep": "parameter_sweeps", "walk_forward": "walk_forward"}[kind]
            if prior.get("category") == category:
                used += prior["estimated_tokens"]
        preview=payload.get('server_preview')
        if preview is not None and preview.get('payload_hash')!=digest({'portfolio':payload['portfolio'],'args':args}):
            raise ValueError('Server preview receipt refers to a different configuration')
        if execute and kind in ('sweep','walk_forward') and preview is None:
            raise ValueError('Current normalized server preview receipt required before optimizer/study execution')
        estimate = plan(spec, kind, pricing, assets=assets, evaluations=evaluations, folds=folds,
                        used_tokens=used, window={"start": start, "end": end},server_preview=preview)
        request["budget"] = estimate
        if not execute:
            return {"dry_run": True, "idempotency_key": key, "request": request}
        if self.mcp is None:
            raise ValueError("MCP extraction bridge required before submitting any job")
        with self.store.db:
            self.store.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,'SUBMITTING',NULL,NULL,NULL)",
                                  (key, spec["experiment_id"], kind, stage, canonical(request).decode()))
        # Record before transport; failures, billing uncertainty, and ugly outcomes survive.
        self.store.record_trial(key, spec["experiment_id"], family, candidate, parameters, stage, {"status": "SUBMITTING", "evaluations": evaluations*folds})
        self.raw.write(f"{spec['experiment_id']}/{key}/request.json", request)
        try:
            response = self.sdk.submit(kind, payload, key)
            operation_id = response.get("id")
            if not isinstance(operation_id, str) or not operation_id:
                raise ValueError("Operation response lacks observed id field")
            self.raw.write(f"{spec['experiment_id']}/{key}/submission.json", response)
            with self.store.db:
                self.store.db.execute("UPDATE jobs SET status='SUBMITTED',operation_id=?,response=? WHERE key=?",
                                      (operation_id, canonical(response).decode(), key))
            self.store.record_trial(key, spec["experiment_id"], family, candidate, parameters, stage,
                                    {"status": "SUBMITTED", "evaluations": evaluations*folds}, run_id=operation_id)
        except Exception as error:
            with self.store.db:
                self.store.db.execute("UPDATE jobs SET status='UNKNOWN',error=? WHERE key=?", (type(error).__name__, key))
            self.store.record_trial(key, spec["experiment_id"], family, candidate, parameters, stage,
                                    {"status": "UNKNOWN", "error_type": type(error).__name__, "evaluations": evaluations*folds})
            raise
        return dict(self.store.db.execute("SELECT * FROM jobs WHERE key=?", (key,)).fetchone())

    def poll(self, spec, key, *, attempts=100, interval=3):
        self.store.verify(spec)
        row = self.store.db.execute("SELECT * FROM jobs WHERE key=? AND experiment=?", (key, spec["experiment_id"])).fetchone()
        if row is None or row["operation_id"] is None:
            raise ValueError("Cannot poll an unacknowledged operation")
        request = json.loads(row["request"])
        for tick in range(attempts):
            result = retry_read(lambda: self.sdk.read(row["kind"], row["operation_id"]), sleep=self.sleep)
            self.raw.write(f"{spec['experiment_id']}/{key}/poll_{len(list((self.raw.root/spec['experiment_id']/key).glob('poll_*.json'))):06}.json", result)
            status = str(result.get("status", "")).upper()
            if status in ("COMPLETE", "COMPLETED", "FAILED", "ERROR", "CANCELED", "CANCELLED"):
                break
            if tick + 1 < attempts:
                self.sleep(interval)
        else:
            raise TimeoutError("Polling ceiling reached; resume same operation ID")
        if status in ("COMPLETE", "COMPLETED"):
            if row["kind"] == "backtest":
                # Some SDK operations wrap backtest IDs in result; fail closed if absent.
                backtest_id = result.get("result", {}).get("backtestId") or result.get("backtestId") or row["operation_id"]
                if not backtest_id:
                    raise ValueError("Complete operation lacks backtestId; raw status saved for reconciliation")
                extract(self.raw, self.read_mcp, spec, row["stage"], backtest_id,
                        events_required=spec["execution"]["requires_events"], test_authorized=row["stage"]=="TEST_AUTHORIZED")
            else:
                # Full sweep/WF raw surface is saved; no constituent trace completeness is implied.
                self.raw.write(f"{spec['experiment_id']}/{key}/full_result.json", result)
        with self.store.db:
            self.store.db.execute("UPDATE jobs SET status=?,response=? WHERE key=?", (status, canonical(result).decode(), key))
        self.store.record_trial(key, spec["experiment_id"], request["family"], request["candidate"], request["parameters"], row["stage"],
                                {"status": status, "evaluations": request["budget"]["planned_evaluations"],
                                 "warnings": result.get("warnings", [])}, run_id=row["operation_id"])
        return result

    def reconcile(self, spec, key, operation_id):
        """Attach an independently confirmed operation ID; never issue another POST."""
        self.store.verify(spec)
        row = self.store.db.execute("SELECT * FROM jobs WHERE key=? AND experiment=?",(key,spec['experiment_id'])).fetchone()
        if row is None or row['status'] not in ('UNKNOWN','SUBMITTING'):
            raise ValueError("Only an uncertain known submission can be reconciled")
        response = retry_read(lambda:self.sdk.read(row['kind'],operation_id),sleep=self.sleep)
        # Require independently returned provenance to match the submitted key.
        if response.get('idempotencyKey') != key:
            raise ValueError("Server response does not establish submission-key identity; reconcile manually")
        self.raw.write(f"{spec['experiment_id']}/{key}/reconciled.json",response)
        with self.store.db:
            self.store.db.execute("UPDATE jobs SET status='SUBMITTED',operation_id=? WHERE key=?",(operation_id,key))
        return dict(self.store.db.execute("SELECT * FROM jobs WHERE key=?",(key,)).fetchone())

    def deploy_paper(self, spec, portfolio_id, *, execute=False):
        state=self.store.verify(spec)
        if state['stage']!='PAPER_AUTHORIZED' or 'PAPER' not in json.loads(state['approvals']):
            raise ValueError('Paper deployment requires separate human authorization')
        candidate=self.store.candidate(spec)
        if not execute:
            return {'dry_run':True,'operation':'SDK.deploy (paper only)','portfolio_id':portfolio_id}
        current=dict(self.sdk.client.get_portfolio(portfolio_id))
        if digest(current)!=digest(candidate['portfolio']):
            raise ValueError('Saved paper draft does not exactly match frozen portfolio; review server-added fields explicitly')
        marker=f"{spec['experiment_id']}/paper/submission.json"
        if (self.raw.root/marker).exists():
            raise ValueError('Prior paper submission exists; uncertain non-idempotent deploy must be reconciled manually')
        self.raw.write(marker,{'portfolio_id':portfolio_id,'candidate_hash':state['candidate_hash'],'status':'SUBMITTING'})
        result=self.sdk.paper(portfolio_id)  # Deliberately no automatic retry.
        self.raw.write(f"{spec['experiment_id']}/paper/response.json",result)
        self.store.transition(spec,'PAPER')
        return result
