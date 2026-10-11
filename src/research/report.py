"""Future-experiment cards and figures from validated session-close evidence."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.metrics.performance import daily_performance
from src.research.analysis import stress_matrix, surface, validate_folds
from src.research.spec import NY, digest, enforce_range


def compute(spec, runs, *, test_authorized=False):
    results = {}
    for name, run in runs.items():
        stage = run["stage"]
        rows = run["closes"]
        dates, values = [], []
        for row in rows:
            timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("Timezone required")
            local = timestamp.astimezone(NY)
            day = local.date().isoformat()
            if day != row["date"] or local.strftime("%H:%M:%S") not in ("16:00:00", "13:00:00"):
                raise ValueError("Not a true regular/evidenced early session close")
            if row["close_evidence_timestamp"] != row["timestamp"]:
                raise ValueError("Close must match saved market-event or exchange-calendar evidence")
            enforce_range(spec, stage, day, day, test_authorized=test_authorized)
            dates.append(day)
            values.append(float(row["portfolio_value"]))
        results[name] = daily_performance(values, dates, initial_value=spec["costs"]["initial_value"])
    return results


def write(root, spec, state, bundle, trials):
    root = Path(root)
    results = compute(spec, bundle.get("runs", {}), test_authorized="TEST" in json.loads(state["approvals"]))
    metrics = {"experiment": spec["experiment_id"], "spec_hash": digest(spec), "candidate_hash": state["candidate_hash"],
               "metrics": results, "stress": stress_matrix(spec["stress_scenarios"], bundle.get("stress", {})),
               "limitations": bundle["limitations"], "interpretation": bundle["interpretation"],
               "evidence_class": spec["historical_evidence_class"], "trials": trials}
    metrics['benchmark_comparisons']={}
    for pair in bundle.get('comparisons',[]):
        candidate,benchmark=pair['candidate'],pair['benchmark']
        a,b=bundle['runs'][candidate],bundle['runs'][benchmark]
        if [r['date'] for r in a['closes']]!=[r['date'] for r in b['closes']] or a['stage']!=b['stage']:
            raise ValueError('Explicit benchmark comparison must have aligned dates and the same stage')
        differences={}
        for field in ('total_return','sharpe','sortino','annualized_volatility','maximum_drawdown'):
            left,right=results[candidate][field],results[benchmark][field]
            differences[field]=left-right if left is not None and right is not None else None
        metrics['benchmark_comparisons'][candidate+' minus '+benchmark]=differences
    if bundle.get("surface"):
        metrics["optimizer_stability"] = surface(bundle["surface"], spec["optimization_ranges"])
    if bundle.get("folds"):
        metrics["walk_forward"] = validate_folds(bundle["folds"], spec["windows"]["development"])
    output = root / "data/processed/research_os" / spec["experiment_id"]
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    assets = root / "docs/assets/research_os" / spec["experiment_id"]
    assets.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for kind in ("equity", "drawdown"):
        fig, ax = plt.subplots(figsize=(9,4.5), layout="constrained")
        for name, run in bundle.get("runs", {}).items():
            values = [float(r["portfolio_value"]) for r in run["closes"]]
            dates = [datetime.fromisoformat(r["date"]) for r in run["closes"]]
            if kind == "drawdown":
                peak, tape = values[0], []
                for v in values:
                    peak=max(peak,v);tape.append(100*(v/peak-1))
                values=tape
            ax.plot(dates,values,label=name,linewidth=1.5)
        ax.set_title(f"{spec['experiment_id']} · {kind.title()} · historical simulation")
        ax.set_xlabel("New York session date");ax.set_ylabel("Portfolio value (USD)" if kind=="equity" else "Drawdown (%)")
        if kind=="equity":ax.set_ylim(bottom=0)
        ax.grid(axis="y",alpha=.2)
        if results:ax.legend(frameon=False)
        else:ax.text(.5,.5,"Not run",transform=ax.transAxes,ha="center")
        fig.savefig(assets/f"{kind}.png",metadata={"Software":"Research OS"});plt.close(fig)
    if "optimizer_stability" in metrics:
        fig, ax = plt.subplots(figsize=(8,4),layout="constrained")
        ax.plot(range(len(bundle["surface"])),[r["score"] for r in bundle["surface"]],marker="o")
        ax.set_title("Declared optimizer surface · no silent winner substitution")
        ax.set_xlabel("Parameter cell index (full coordinates in metrics.json)");ax.set_ylabel(spec["selection"]["primary_metric"])
        fig.savefig(assets/"optimizer_surface.png",metadata={"Software":"Research OS"});plt.close(fig)
    lines = [f"# {spec['experiment_id']}: {spec['title']}", "", spec["hypothesis"], "",
             f"Stage: {state['stage']}. Evidence: workflow-held-out historical simulation; not prospective.", "",
             "## Independent results", "", "| Run | Return | Volatility | Sharpe RF=0 | Sortino | Max DD |",
             "|---|---:|---:|---:|---:|---:|"]
    for name,m in results.items():
        ratio=lambda v:f"{v:.3f}" if v is not None else "undefined"
        percent=lambda v:f"{v:.2%}" if v is not None else 'undefined'
        lines.append(f"| {name} | {percent(m['total_return'])} | {percent(m['annualized_volatility'])} | {ratio(m['sharpe'])} | {ratio(m['sortino'])} | {percent(m['maximum_drawdown'])} |")
    lines += ["", "## Candidate and trial ledger", "", "| Candidate | Stage | Run | Status / result | Eligible |", "|---|---|---|---|---|"]
    for t in trials:
        lines.append(f"| {t['candidate']} | {t['stage']} | {t.get('run_id') or 'unresolved'} | {t['result'].get('status','recorded')} | {t.get('eligibility')} |")
    lines += ["", "## Stress matrix", "", "| Scenario | Status |", "|---|---|"]
    lines += [f"| {name} | {row['status']} |" for name,row in metrics["stress"].items()]
    lines += ["", "## Walk-forward and stability", "",
              "Full fold definitions, selected parameters, and surface diagnostics are retained in the machine-readable results when provided. Missing studies are not inferred.", "",
              "## Benchmark comparison", "", bundle.get("benchmark_comparison", "Not evaluated; explicit benchmark run required."), "",
              "## Limitations", "", *[f"- {item}" for item in bundle["limitations"]], "",
              "## Interpretation", "", bundle["interpretation"], "",
              f"![Equity](../docs/assets/research_os/{spec['experiment_id']}/equity.png)", "",
              f"![Drawdown](../docs/assets/research_os/{spec['experiment_id']}/drawdown.png)", ""]
    reports=root/"reports";reports.mkdir(exist_ok=True)
    (reports/f"{spec['experiment_id']}_report.md").write_text("\n".join(lines),encoding="utf-8")
    card={"experiment":spec["experiment_id"],"title":spec["title"],"stage":state["stage"],
          "asset_universe":spec["asset_universe"],"windows":spec["windows"],"finding":bundle["interpretation"],
          "report":f"reports/{spec['experiment_id']}_report.md"}
    directory=root/"experiments"/spec["experiment_id"];directory.mkdir(parents=True,exist_ok=True)
    (directory/"card.json").write_text(json.dumps(card,indent=2)+"\n")
    if state['stage']=='TEST_COMPLETE':
        review={'spec_hash':digest(spec),'candidate_hash':state['candidate_hash'],
                'review_complete':bundle.get('review_complete',False),'metrics_hash':digest(metrics)}
        (directory/'final_review.json').write_text(json.dumps(review,indent=2)+'\n')
    if state["stage"] in ("TEST_COMPLETE", "PAPER_AUTHORIZED", "PAPER"):
        registry_path=root/"experiments/registry.json"
        registry=json.loads(registry_path.read_text()) if registry_path.exists() else []
        registry=[x for x in registry if x["experiment"]!=spec["experiment_id"]]+[card]
        registry_path.write_text(json.dumps(sorted(registry,key=lambda x:x['experiment']),indent=2)+"\n")
    return metrics
