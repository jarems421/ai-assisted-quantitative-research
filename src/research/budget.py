"""Dated, replaceable token estimates; ceilings count all reserved evaluations."""
import math
from datetime import date


def plan(spec, operation, pricing, *, assets, evaluations=1, folds=1, aurora_quote=None,
         now=None, used_tokens=0, server_preview=None, window=None):
    today = now or date.today()
    if today > date.fromisoformat(pricing["expires_on"]):
        raise ValueError("Pricing metadata expired; refresh or supply a current server preview")
    if any(type(v) is not int or v < 1 for v in (assets, evaluations, folds)):
        raise ValueError("Positive integer assets/evaluations/folds required")
    total = evaluations * folds
    if total > pricing["max_evaluations"]:
        raise ValueError("Planned evaluations exceed the hard search ceiling")
    key = spec["execution"]["interval"] + ("_options" if spec["execution"]["options"] else "_stock")
    category = {"backtest": "candidate_backtests", "sweep": "parameter_sweeps",
                "walk_forward": "walk_forward", "aurora": "aurora"}[operation]
    if spec["execution"]["interval"] == "Minute" and operation == "backtest":
        category = "intraday_confirmation"
    if operation == "aurora":
        if aurora_quote is None:
            raise ValueError("Aurora needs an explicit current token quote; model cost is not inferred")
        tokens = float(aurora_quote) * total
    elif operation in ("sweep", "walk_forward"):
        factor = min(1, max(.15, math.sqrt(assets / 500)))
        tokens = max(pricing["optimizer_minimum"] * folds,
                     total * pricing["optimizer_per_evaluation"][key] * factor)
    else:
        w = window or spec["windows"]["development"]
        days = (date.fromisoformat(w["end"]) - date.fromisoformat(w["start"])).days + 1
        if spec["execution"]["interval"] == "Minute" and days + spec["execution"]["warmup_days"] > 730:
            raise ValueError("Minute span plus warmup exceeds the observed 730-day cap")
        tokens = total * days * pricing["backtest_per_calendar_day"][key]
    if spec["execution"]["requires_events"]:
        tokens *= pricing["event_multiplier"]
    if server_preview is not None:
        if server_preview["planned_evaluations"] != total:
            raise ValueError("Preview and local evaluation count disagree")
        tokens = float(server_preview["estimated_tokens"])
    if not math.isfinite(tokens) or tokens < 0 or used_tokens < 0:
        raise ValueError("Invalid token quote")
    ceiling = spec["budget"][category]
    if tokens + used_tokens > ceiling:
        raise ValueError(f"{category} ceiling exceeded ({tokens + used_tokens:g} > {ceiling:g})")
    return {"category": category, "planned_evaluations": total, "estimated_tokens": tokens,
            "reserved_tokens": used_tokens, "ceiling": ceiling, "pricing_observed_on": pricing["observed_on"],
            "source": "server_preview" if server_preview else "dated_documentation_estimate",
            "not_an_invoice": True}
