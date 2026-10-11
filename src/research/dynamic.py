"""Actual SDK DynamicRebalance builders; no server operation."""
import importlib


def build(*, rank_indicator, filters=(), max_holdings=20, percentile=None,
          weight_indicator=None, deployment_percent=95, source="ALL_US_STOCKS"):
    if max_holdings < 1 or not 0 < deployment_percent <= 100:
        raise ValueError("Invalid holding/deployment limits")
    p = importlib.import_module("nexustrade.portfolio")
    pipeline = [p.filter(condition) for condition in filters]
    if percentile is not None:
        if not 0 < percentile <= 100:
            raise ValueError("Percentile must be in (0,100]")
        pipeline.append(p.select_percentile(rank_indicator, percentile))
    pipeline.append(p.select_top(rank_indicator, max_holdings))
    return p.dynamic_rebalance(universe=p.universe(source), pipeline=pipeline,
                               weight_indicator=weight_indicator if weight_indicator is not None else p.Value(1),
                               limit=max_holdings, deployment_percent=p.Value(deployment_percent))


def turnover_gate(metrics, *, max_turnover, max_cost, min_net_benefit):
    required = ("planned_turnover", "estimated_cost", "net_benefit")
    if any(name not in metrics for name in required):
        return {"eligible": False, "reason": "prospective metrics unavailable; no guessed cost gate"}
    return {"eligible": metrics["planned_turnover"] <= max_turnover
            and metrics["estimated_cost"] <= max_cost and metrics["net_benefit"] >= min_net_benefit,
            "observed": metrics}
