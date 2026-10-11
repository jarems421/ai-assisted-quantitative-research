"""Enumerate the proposed EXP002 design without generating or submitting jobs."""
from itertools import product

FAMILIES = {
    "momentum": ("momentum_lookback_calendar_days", "number_of_holdings"),
    "insider": ("insider_lookback_calendar_days", "number_of_holdings"),
    "institutional": ("number_of_holdings",),
    "momentum_insider": ("momentum_lookback_calendar_days", "insider_lookback_calendar_days", "number_of_holdings"),
    "momentum_institutional": ("momentum_lookback_calendar_days", "number_of_holdings"),
    "insider_institutional": ("insider_lookback_calendar_days", "number_of_holdings"),
    "full_composite": ("momentum_lookback_calendar_days", "insider_lookback_calendar_days", "number_of_holdings"),
}


def evaluation_plan(ranges: dict, folds: int = 5, failure_reserve: int = 20,
                    robustness_scenarios: int = 6) -> dict:
    permitted = set(FAMILIES["full_composite"])
    if set(ranges) != permitted or folds < 1 or failure_reserve < 0 or robustness_scenarios < 0:
        raise ValueError("Unexpected design axis or invalid evaluation budget")
    if any(not values or len(values) != len(set(values)) for values in ranges.values()):
        raise ValueError("Empty or duplicate grid values")
    counts = {}
    for family, axes in FAMILIES.items():
        counts[family] = len(list(product(*(ranges[axis] for axis in axes))))
    families_with_benchmarks = 9
    parts = {"development_grid_folds": (sum(counts.values()) + 2) * folds,
             "development_selected_family_replays": families_with_benchmarks,
             ("six_development_robustness_scenarios" if robustness_scenarios == 6 else "development_robustness_scenarios"): robustness_scenarios * families_with_benchmarks,
             "outer_validation": families_with_benchmarks,
             "eventual_test": families_with_benchmarks,
             "failed_unresolved_reserve": failure_reserve}
    return {"status": "PROPOSED_NOT_AUTHORIZED", "family_cells": counts,
            "benchmarks_per_fold": 2, "fold_count": folds, "components": parts,
            "projected_ceiling_with_reserve": sum(parts.values()),
            "server_preview": False, "actual_candidate_evaluations": 0,
            "limits": f"Conditional on {folds} coverage-supported folds and successful primary implementation. Reconcile all nested/server amplification before freeze. Reserve is a hard planning allocation, not permission to omit failed trials."}
