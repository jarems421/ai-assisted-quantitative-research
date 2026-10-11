"""Predeclared descriptive paired uncertainty; no inferential p-values.

Bootstrap distributions are not null distributions. This module never labels
percentile intervals as a significance test or adjusts them with Holm.
"""
import math
import random
import statistics
from src.metrics.performance import quantile

BLOCK_LENGTH=20
DRAWS=10000
SEED=2002001


def sharpe_zero_rf(values):
    sd=statistics.stdev(values)
    return math.sqrt(252)*statistics.fmean(values)/sd if sd>0 else None


def paired_uncertainty(strategy, benchmark, *, block_length=BLOCK_LENGTH, draws=DRAWS, seed=SEED):
    n=len(strategy)
    if n!=len(benchmark) or n<max(2,block_length) or block_length<1 or draws<20:
        raise ValueError("Aligned returns and valid bootstrap settings required")
    if any(not math.isfinite(v) for v in [*strategy,*benchmark]):
        raise ValueError("Nonfinite returns")
    a,b=sharpe_zero_rf(strategy),sharpe_zero_rf(benchmark)
    if a is None or b is None:raise ValueError("Undefined original Sharpe")
    rng=random.Random(seed);means=[];sharpes=[];invalid=0
    for _ in range(draws):
        indices=[]
        while len(indices)<n:
            start=rng.randrange(n-block_length+1)
            indices.extend(range(start,start+block_length))
        indices=indices[:n];x=[strategy[i] for i in indices];y=[benchmark[i] for i in indices]
        means.append(statistics.fmean(u-v for u,v in zip(x,y)))
        sa,sb=sharpe_zero_rf(x),sharpe_zero_rf(y)
        if sa is None or sb is None:invalid+=1
        else:sharpes.append(sa-sb)
    return {"mean_daily_excess":statistics.fmean(u-v for u,v in zip(strategy,benchmark)),
            "sharpe_difference":a-b,"mean_ci_95":[quantile(means,.025),quantile(means,.975)],
            "sharpe_ci_95":[quantile(sharpes,.025),quantile(sharpes,.975)] if not invalid else None,
            "undefined_sharpe_draws":invalid,"block_length":block_length,"draws":draws,"seed":seed,
            "method":"paired noncircular moving-block percentile bootstrap",
            "inference":"descriptive uncertainty only; no p-value or significance claim",
            "holm_applied":False,"selection_bias_adjusted":False}


def implementation_costs(fills, bps):
    if bps not in (10,20):raise ValueError("Undeclared cost stress")
    result=[]
    for fill in fills:
        notional=abs(fill["quantity"]*fill["price"])
        if not math.isfinite(notional):raise ValueError("Nonfinite fill notional")
        result.append(notional*bps/10000)
    return result
