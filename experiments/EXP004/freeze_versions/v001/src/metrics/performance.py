"""Deterministic daily-equity statistics. Returns are fractions, not percentages.

Daily returns use adjacent session closes (the first close has no daily return).
Total return uses the separately supplied initial funding value. Downside
deviation is sqrt(mean(min(return, 0)**2)) over ALL daily returns, with MAR=0.
Drawdown uses only this period's daily closes and its own running peak.
Undefined ratios/moments are None, so JSON never contains NaN or Infinity.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence


def quantile(values: Sequence[float], probability: float) -> float:
    """Linear interpolation at (n - 1) * p, equivalent to quantile type 7."""
    if not values or not 0 <= probability <= 1:
        raise ValueError("Quantiles require observations and 0 <= p <= 1")
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def drawdown(values: Sequence[float], dates: Sequence[str]) -> dict:
    """Positive drawdown magnitude; latest preceding tied peak wins."""
    if not values or len(values) != len(dates):
        raise ValueError("Aligned nonempty equity values and dates required")
    peak = values[0]
    peak_index = 0
    worst = 0.0
    worst_peak = worst_trough = None
    for index, value in enumerate(values):
        if value >= peak:
            peak, peak_index = value, index
        loss = 1 - value / peak
        if loss > worst:
            worst, worst_peak, worst_trough = loss, peak_index, index
    recovery = None
    if worst_trough is not None:
        recovery = next(
            (dates[i] for i in range(worst_trough + 1, len(values))
             if values[i] >= values[worst_peak]),
            None,
        )
    return {
        "maximum_drawdown": worst,
        "maximum_drawdown_peak_date": dates[worst_peak] if worst_peak is not None else None,
        "maximum_drawdown_trough_date": dates[worst_trough] if worst_trough is not None else None,
        "maximum_drawdown_recovery_date": recovery,
    }


def daily_performance(
    values: Sequence[float], dates: Sequence[str], *, initial_value: float,
    trading_days_per_year: int = 252, risk_free_rate: float = 0.0,
) -> dict:
    if len(values) < 2 or len(values) != len(dates):
        raise ValueError("At least two aligned daily closes are required")
    if any(a >= b for a, b in zip(dates, dates[1:])):
        raise ValueError("Dates must be strictly increasing")
    if not math.isfinite(initial_value) or initial_value <= 0:
        raise ValueError("Initial funding must be finite and positive")
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Equity must be finite and positive")
    if risk_free_rate != 0 or trading_days_per_year <= 0:
        raise ValueError("This implementation requires zero RF and positive annualization")
    returns = [current / previous - 1 for previous, current in zip(values, values[1:])]
    n = len(returns)
    mean = statistics.fmean(returns)
    sd = statistics.stdev(returns) if n >= 2 else None
    annualizer = math.sqrt(trading_days_per_year)
    downside = math.sqrt(statistics.fmean(min(r, 0.0) ** 2 for r in returns))
    skew = kurtosis = None
    if sd is not None and sd > 0:
        centered = [(r - mean) / sd for r in returns]
        if n >= 3:
            skew = n / ((n - 1) * (n - 2)) * math.fsum(z ** 3 for z in centered)
        if n >= 4:
            kurtosis = (
                n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
                * math.fsum(z ** 4 for z in centered)
                - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
            )
    result = {
        "daily_row_count": len(values), "daily_return_count": n,
        "first_date": dates[0], "last_date": dates[-1],
        "initial_funding_value": initial_value, "first_close_value": values[0],
        "ending_value": values[-1], "total_return": values[-1] / initial_value - 1,
        "close_to_close_total_return": values[-1] / values[0] - 1,
        "mean_daily_return": mean, "median_daily_return": statistics.median(returns),
        "sample_daily_standard_deviation": sd,
        "annualized_volatility": sd * annualizer if sd is not None else None,
        "sharpe": annualizer * mean / sd if sd is not None and sd > 0 else None,
        "sortino": annualizer * mean / downside if downside > 0 else None,
        "daily_downside_deviation": downside,
        "skew": skew, "excess_kurtosis": kurtosis,
        "daily_return_quantiles": {
            f"{percent}%": quantile(returns, percent / 100)
            for percent in (1, 5, 25, 50, 75, 95, 99)
        },
    }
    for threshold, label in ((-0.02, "minus_2pct"), (-0.05, "minus_5pct")):
        count = sum(r < threshold for r in returns)
        result[f"days_below_{label}"] = count
        result[f"percentage_days_below_{label}"] = count / n * 100
    result.update(drawdown(values, dates))
    return result
