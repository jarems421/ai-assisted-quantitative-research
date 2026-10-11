"""Local robustness and parameter-stability tools. No metric-definition changes."""
from __future__ import annotations

import itertools
import math
import random
import statistics
from datetime import date, timedelta

from src.metrics.performance import daily_performance, quantile


def controls(signals):
    signals = sorted(set(signals))
    if not signals:
        raise ValueError("At least one signal required")
    # Benchmark, every singleton, full composite, and leave-one-out ablations.
    variants = {(), tuple(signals), *[(s,) for s in signals]}
    if len(signals) > 2:
        variants.update(tuple(s for s in signals if s != excluded) for excluded in signals)
    return [{"signals": list(v), "kind": "benchmark" if not v else "control" if len(v) == 1 else "composite"}
            for v in sorted(variants, key=lambda x: (len(x), x))]


def surface(cells, ranges, *, higher_is_better=True):
    axes = sorted(ranges)
    expected = list(itertools.product(*(ranges[a] for a in axes)))
    lookup = {tuple(row["parameters"][a] for a in axes): float(row["score"]) for row in cells}
    if len(lookup) != len(cells) or set(lookup) != set(expected) or any(not math.isfinite(v) for v in lookup.values()):
        raise ValueError("Require a complete unique finite parameter surface")
    sign = 1 if higher_is_better else -1
    best = max(lookup, key=lambda p: (sign * lookup[p], p))
    peers = []
    for point in expected:
        distance = sum(abs(ranges[a].index(x) - ranges[a].index(y)) for a, x, y in zip(axes, point, best))
        if distance == 1:
            peers.append({"parameters": dict(zip(axes, point)), "score": lookup[point]})
    spread = max(lookup.values()) - min(lookup.values())
    near = [v for v in lookup.values() if sign * (lookup[best] - v) <= .1 * spread]
    average = statistics.fmean(p["score"] for p in peers) if peers else lookup[best]
    normalized_gap = sign * (lookup[best] - average) / spread if spread else 0
    return {"best_parameters": dict(zip(axes, best)), "best_score": lookup[best],
            "neighbours": peers, "neighbour_mean": average,
            "neighbour_gap_fraction_of_surface_range": normalized_gap,
            "broad_plateau_score": len(near) / len(cells),
            "isolated_optimum_warning": normalized_gap > .5,
            "perturbations": "one adjacent predeclared grid step on each axis; not arbitrary percent changes",
            "full_surface": cells}


def rank_stability(scores_by_fold):
    if len(scores_by_fold)<2:raise ValueError('At least two folds required')
    keys = sorted(scores_by_fold[0])
    if len(scores_by_fold) < 2 or len(keys) < 2 or any(sorted(s) != keys for s in scores_by_fold):
        raise ValueError("Aligned candidates in at least two folds required")
    def ranks(scores):
        values = [scores[k] for k in keys]
        return [1 + sum(v < x for v in values) + (sum(v == x for v in values) - 1) / 2 for x in values]
    def corr(a, b):
        am, bm = statistics.fmean(a), statistics.fmean(b)
        numerator = sum((x-am)*(y-bm) for x, y in zip(a, b))
        denominator = math.sqrt(sum((x-am)**2 for x in a) * sum((y-bm)**2 for y in b))
        return numerator / denominator if denominator else None
    ranks_by_fold = [ranks(s) for s in scores_by_fold]
    return {"adjacent_fold_spearman": [corr(a, b) for a, b in zip(ranks_by_fold, ranks_by_fold[1:])]}


def paired_bootstrap(strategy, benchmark, *, block_length=5, draws=1000, seed=0):
    if len(strategy) != len(benchmark) or len(strategy) < block_length or block_length < 1 or draws < 20:
        raise ValueError("Aligned series, valid block length, and >=20 draws required")
    if any(not math.isfinite(x) for x in [*strategy, *benchmark]):
        raise ValueError("Nonfinite bootstrap input")
    rng, n = random.Random(seed), len(strategy)
    samples = []
    for _ in range(draws):
        indices = []
        while len(indices) < n:
            start = rng.randrange(n - block_length + 1)
            indices.extend(range(start, start + block_length))
        samples.append(statistics.fmean(strategy[j] - benchmark[j] for j in indices[:n]))
    return {"mean_daily_excess": statistics.fmean(a-b for a,b in zip(strategy,benchmark)),
            "ci_95": [quantile(samples,.025),quantile(samples,.975)],
            "method": "paired moving-block percentile bootstrap; no wraparound",
            "block_length": block_length, "draws": draws, "seed": seed,
            "caveat": "Conditional historical uncertainty; no guarantee of future profitability"}


def holm(pvalues, *, alpha=.05):
    if not pvalues or not 0 < alpha < 1 or any(not math.isfinite(p) or not 0 <= p <= 1 for p in pvalues.values()):
        raise ValueError("Finite valid p-values required; failed/unresolved tests must remain in the family")
    count = len(pvalues)
    previous, result = 0, {}
    for i, (key, p) in enumerate(sorted(pvalues.items(), key=lambda x: (x[1], x[0]))):
        adjusted = min(1, max(previous, (count-i)*p))
        previous = adjusted
        result[key] = {"raw_p": p, "adjusted_p": adjusted, "reject": adjusted <= alpha}
    return result


def validate_folds(folds, permitted, *, embargo_days=0):
    previous_end = None
    for fold in folds:
        train, held = fold["training"], fold["held_out"]
        if (not permitted["start"] <= train["start"] <= train["end"] < held["start"] <= held["end"] <= permitted["end"]
                or (date.fromisoformat(held["start"])-date.fromisoformat(train["end"])).days <= embargo_days
                or previous_end and held["start"] <= previous_end):
            raise ValueError("Fold leakage, embargo violation, or overlapping held-out periods")
        if not all(k in fold for k in ("selected_parameters", "metrics")):
            raise ValueError("Missing fold provenance")
        previous_end = held["end"]
    if not folds:
        raise ValueError("No folds")
    return {"fold_count": len(folds), "folds": folds,
            "aggregate": "Use the chronological held-out return tape; do not average fold Sharpe ratios"}


def stress_matrix(scenarios, observations):
    """Ingest genuine predeclared rerun outputs; never invent execution counterfactuals."""
    unknown = set(observations) - set(scenarios)
    if unknown:
        raise ValueError("Undeclared stress scenarios")
    return {name: {"status": "observed" if name in observations else "not_run",
                   "evidence": observations.get(name)} for name in scenarios}


def regime_metrics(dates, values, regimes, *, initial_value):
    """Regime summaries retain adjacency; nonconsecutive days are never stitched."""
    if len(dates) != len(values) or any(a >= b for a,b in zip(dates,dates[1:])):
        raise ValueError("Aligned increasing dates required")
    returns = [(dates[i], values[i]/values[i-1]-1) for i in range(1,len(values))]
    result = {}
    for label in sorted(set(regimes.values())):
        selected = [r for d,r in returns if regimes.get(d)==label]
        result[label] = {"daily_return_count": len(selected),
                         "mean_daily_return": statistics.fmean(selected) if selected else None,
                         "sample_daily_sd": statistics.stdev(selected) if len(selected)>1 else None,
                         "caveat": "Regime-conditioned returns; no stitched equity or regime drawdown"}
    return result
