"""Research roles, complete provenance, and process grading; agents fail closed."""
from src.research.spec import digest, enforce_range

ROLES = {
    "researcher": "Investigate economic rationale and empirical evidence. State a falsifiable hypothesis; do not search for high backtest returns.",
    "data_auditor": "Audit availability timestamps, filing dates, revisions, survivorship, missing coverage, leakage, and universe membership.",
    "strategy_architect": "Propose simple testable rules using permitted data, explicit benchmark, complexity limits, and ablations.",
    "skeptic": "Try to falsify the hypothesis; enumerate confounders, selection effects, leakage, and likely overfitting mechanisms.",
    "execution_reviewer": "Review turnover, liquidity, fees, slippage, execution delay, and implementation realism.",
}
DIMENSIONS = ("hypothesis_clarity", "data_validity", "point_in_time_safety", "simplicity",
              "falsifiability", "benchmark_quality", "confounder_awareness", "execution_realism",
              "novelty", "ablation_control")


def prompts(spec):
    boundary = spec["research_cutoff"]
    context = {k: spec[k] for k in ("hypothesis", "rationale", "expected_effect", "confounders", "data_sources",
                                  "dynamic_universe", "benchmarks", "permitted_indicators", "maximum_complexity")}
    import json
    return {role: {"prompt": f"{instruction}\nResearch evidence cutoff: {boundary}. No performance search, portfolio creation, backtest, optimization, deployment, or trades. Never request or reveal sealed performance data. Modern AI may know historical events; this is not genuinely forward-unseen evidence.\nSpecification: {json.dumps(context,sort_keys=True)}",
                   "spec_hash": digest(spec), "research_cutoff": boundary,
                   "execution_status": "blocked_without_server_side_tool_and_date_isolation"}
            for role, instruction in ROLES.items()}


def launch(*args, **kwargs):
    # Neither a prompt nor semi-automated plan approval constrains read-only tools.
    raise PermissionError("Aurora execution disabled until an audited server-side tool/date allowlist exists")


def evaluation_plan(agent_id):
    return {"tool": "run_agent_run_evaluator", "arguments": {"agent_id": agent_id,
            "additional_context": "Grade research process on " + ", ".join(DIMENSIONS)
            + ". Use scores 0..5 and explanatory feedback. Do not reward backtest return or prettier results."},
            "requires_current_cost_quote": True, "not_executed": True}


def quality(scores, feedback):
    if set(scores) != set(DIMENSIONS) or any(type(v) not in (int,float) or not 0 <= v <= 5 for v in scores.values()):
        raise ValueError("All ten process dimensions require scores in 0..5")
    if not feedback:
        raise ValueError("Explanatory evaluator feedback required")
    return {"scores": scores, "feedback": feedback, "mean_score": sum(scores.values())/len(scores),
            "objective": "research process, not backtest return"}


def corpus_evidence(spec, query, rows, *, cutoff_column="end_date"):
    # Never submit arbitrary SQL automatically: metadata cannot prove a query is bounded.
    if not query or any(not row.get(cutoff_column) or row[cutoff_column] > spec["research_cutoff"] for row in rows):
        raise ValueError("Corpus research includes later or unestablished backtest end dates")
    return {"query": query, "cutoff": spec["research_cutoff"], "rows": rows,
            "purpose": "hypothesis generation only; never historical top-Sharpe proof of alpha"}


def ingest_trajectory(raw, spec, role, trajectory):
    if role not in ROLES:
        raise ValueError("Unknown research role")
    if not trajectory.get("requests_audited"):
        raise ValueError("Trajectory request scope needs human audit; prompt compliance is not proof")
    return raw.write(f"{spec['experiment_id']}/aurora/{role}_{digest(trajectory)}.json",
                     {"prompt": prompts(spec)[role], "trajectory": trajectory})
