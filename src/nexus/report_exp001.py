"""Render the final EXP001 report from locally computed, frozen-definition results."""

from pathlib import Path


def write_report(workspace: Path, results: dict) -> None:
    m = results["metrics"]
    costs = results["stored_transaction_cost_observations"]
    selection = results["development_selection"]
    lines = ["# EXP001 final report", "",
             "## 1. Experimental design", "",
             "EXP001 compares five AI-proposed SPY trading candidates, selects one using Development only, and evaluates that frozen strategy against an explicit SPY buy-and-hold portfolio in two subsequent periods. Each reporting period is funded independently with $25,000; period returns are not chained. All reported performance below is independent zero-risk-free-rate performance from session-close equity, after the simulated fees reflected in the histories.", "",
             "| Period | Window | Purpose |", "|---|---|---|",
             "| Development | 2015-01-01–2021-12-31 | Eligibility and candidate selection |",
             "| Validation | 2022-01-01–2024-12-31 | Frozen A versus explicit SPY; no selection or pass/fail tuning |",
             "| Held-out Test | 2025-01-01–2026-10-08 | Final frozen A versus explicit SPY |", "",
             "According to the experiment record, the 2025–2026 Test was opened exactly once after the strategy and processing methodology were frozen. The extraction audit records pre-Test hashes of the metric module, processor, and Development/Validation results. This task read the two existing Test runs locally and made no Nexus calls or new backtests. The manifest's historical `SEALED` marker remains untouched; explicit authorization opened Test extraction and processing.", "",
             "## 2. Five Development candidates", "",
             "| Candidate | Recorded strategy family |", "|---|---|",
             "| A | SMA20/50 trend selection |", "| B | Donchian breakout |", "| C | RSI2 mean reversion |",
             "| D | MACD + SMA100 |", "| E | SMA100 + ATR filter |", "",
             "These are experiment-record labels, not reconstructed full strategy snapshots. A's raw signal audits record buying when position market value is below 1 and the prior-day SMA20 exceeds SMA50, and selling when invested and SMA20 is at or below SMA50. Entry allocation is 99.5% of buying power; the stock fee setting is 0.10% of notional per fill.", "",
             "## 3. Development selection rule", "",
             "A candidate must have maximum drawdown at most 25% and at least 20 recorded completed round trips. Among eligible Development candidates, select the highest independently calculated zero-RF Sharpe. The recorded round-trip counts are used unchanged; no Validation or Test observation enters this decision.", "",
             "## 4. Independent zero-RF Development results", "",
             "| Candidate | Return | Ann. volatility | Sharpe | Sortino | Max DD | Round trips | Eligible |",
             "|---|---:|---:|---:|---:|---:|---:|---|"]
    for n in ("dev_A", "dev_B", "dev_C", "dev_D", "dev_E"):
        x, s = m[n], selection["candidates"][n]
        lines.append(f"| {n[-1]} | {x['total_return']:.3%} | {x['annualized_volatility']:.3%} | {x['sharpe']:.6f} | {x['sortino']:.6f} | {x['maximum_drawdown']:.3%} | {s['completed_round_trips']} | {'Yes' if s['eligible'] else 'No'} |")
    lines += ["", "## 5. Why Candidate A was selected", "",
              f"Candidate A's Development Sharpe was {m['dev_A']['sharpe']:.6f}, the highest among the eligible candidates. Its drawdown was {m['dev_A']['maximum_drawdown']:.3%}, with 46 recorded round trips. C was ineligible because its drawdown exceeded 25%. A's selection remains exactly the frozen Development result; later periods did not replace or retune it.", ""]
    for section, title, a, b in ((6, "Validation results versus explicit SPY", "val_A", "val_SPY"),
                                 (7, "Final held-out Test results versus explicit SPY", "test_A", "test_SPY")):
        lines += [f"## {section}. {title}", "",
                  "| Portfolio | Sessions | Ending value | Return | Ann. volatility | Sharpe | Sortino | Max DD |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name, label in ((a, "Candidate A"), (b, "SPY buy-and-hold")):
            x = m[name]
            lines.append(f"| {label} | {x['daily_row_count']} | ${x['ending_value']:,.2f} | {x['total_return']:.3%} | {x['annualized_volatility']:.3%} | {x['sharpe']:.6f} | {x['sortino']:.6f} | {x['maximum_drawdown']:.3%} |")
        comparison = results["validation_comparison" if section == 6 else "test_comparison"]["differences"]
        lines += ["", "| Candidate A minus SPY | Difference |", "|---|---:|"]
        for key, label in (("total_return", "Total return"), ("sharpe", "Sharpe"), ("sortino", "Sortino"),
                           ("annualized_volatility", "Annualized volatility"), ("maximum_drawdown", "Maximum drawdown")):
            d = comparison[key]
            value = f"{d['difference_percentage_points']:+.6f} pp" if "difference_percentage_points" in d else f"{d['candidate_minus_spy']:+.6f}"
            lines.append(f"| {label} | {value} |")
        lines += ["", "No retrospective pass/fail criterion or strategy selection is applied to this period.", ""]
        if section == 7:
            lines += ["Each Test portfolio contributes 443 closes and 442 adjacent-close returns: 440 regular 16:00 closes and three event-backed 13:00 early closes. The calendar excludes copied holiday records on 2025-01-09 and 2026-04-03. The last selected observation is October 8, 2026 at 16:00 New York; the raw query ceiling of 2026-10-09T03:59:59.999Z is October 8 at 23:59:59.999 New York, not October 9 market data.", "",
                      "| Test portfolio | Drawdown peak | Trough | Recovery |", "|---|---|---|---|"]
            for name, label in ((a, "Candidate A"), (b, "SPY buy-and-hold")):
                x = m[name]
                lines.append(f"| {label} | {x['maximum_drawdown_peak_date']} | {x['maximum_drawdown_trough_date']} | {x['maximum_drawdown_recovery_date'] or 'Not recovered within period'} |")
            lines.append("")
    lines += ["## 8. Development → Validation → Test", "",
              "| Candidate A metric | Development | Validation | Test |", "|---|---:|---:|---:|"]
    for key, label in (("total_return", "Return"), ("annualized_volatility", "Annualized volatility"),
                       ("sharpe", "Sharpe (RF=0)"), ("sortino", "Sortino"), ("maximum_drawdown", "Max drawdown")):
        vals = [f"{m[n][key]:.3%}" if key in ("total_return", "annualized_volatility", "maximum_drawdown") else f"{m[n][key]:.6f}"
                for n in ("dev_A", "val_A", "test_A")]
        lines.append(f"| {label} | {' | '.join(vals)} |")
    lines += ["", "| SPY metric | Validation | Test |", "|---|---:|---:|"]
    for key, label in (("total_return", "Return"), ("annualized_volatility", "Annualized volatility"),
                       ("sharpe", "Sharpe (RF=0)"), ("sortino", "Sortino"), ("maximum_drawdown", "Max drawdown")):
        vals = [f"{m[n][key]:.3%}" if key in ("total_return", "annualized_volatility", "maximum_drawdown") else f"{m[n][key]:.6f}"
                for n in ("val_SPY", "test_SPY")]
        lines.append(f"| {label} | {' | '.join(vals)} |")
    lines += ["", "The windows have different lengths. Total returns are period totals, not annualized returns, so their levels should not be interpreted as equal-duration growth rates.", "",
              "## 9. Drawdown/volatility versus return trade-off", ""]
    for prefix, label in (("val", "Validation"), ("test", "Test")):
        a, b = m[prefix + "_A"], m[prefix + "_SPY"]
        lines.append(f"{label}: Candidate A reduced annualized volatility by {(b['annualized_volatility']-a['annualized_volatility'])*100:.3f} percentage points and maximum drawdown by {(b['maximum_drawdown']-a['maximum_drawdown'])*100:.3f} percentage points, while trailing SPY total return by {(b['total_return']-a['total_return'])*100:.3f} percentage points.")
        lines.append("")
    lines += ["These are separate observations: lower realized drawdown and volatility do not themselves establish outperformance or alpha. Candidate A also had lower independent zero-RF Sharpe and Sortino than SPY in both out-of-sample periods, so the observed risk reduction did not improve these return-to-risk ratios relative to the benchmark.", "",
              "## 10. Transaction-cost observations", "",
              "| Run | Stored total fees | Fees / initial funding | Stored dividends | Recorded closed trades |",
              "|---|---:|---:|---:|---:|"]
    for name, c in costs.items():
        lines.append(f"| {name} | ${c['totalFees']:,.2f} | {c['totalFees']/25000:.3%} | ${c['totalDividends']:,.2f} | {c['closedTradeCount']} |")
    lines += ["", "Fees are already reflected in equity; they are not subtracted a second time. Candidate A pays more than buy-and-hold in both out-of-sample windows. The table scales fees by initial funding for description only, not as an attribution of return loss. Dividends are stored cash-flow observations, not additional returns to add to equity. No fee-free counterfactual was run, so the return gap cannot be attributed solely to transaction costs. The stored `closedTradeCount` is retained under the engine's convention and is not independently rederived.", "",
              "## 11. Nexus engine metric differences and risk-free-rate caveat", "",
              "| Test run | Independent return | Stored engine return | Difference (pp) | Independent max DD | Stored engine max DD | Difference (pp) |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name in ("test_A", "test_SPY"):
        r = results["reconciliation"][name]
        ret, dd = r["comparisons"]["total_return"], r["comparisons"]["maximum_drawdown"]
        lines.append(f"| {name} | {ret['independent_percent']:.6f}% | {ret['nexus_percent']:.6f}% | {ret['difference_percentage_points']:+.9f} | {dd['independent_percent']:.6f}% | {dd['nexus_percent']:.6f}% | {dd['difference_percentage_points']:+.6f} |")
    lines += ["", "| Test run | Engine Sharpe | Engine Sortino | Stored riskFreeRate | All-tick DD residual versus engine (pp) |",
              "|---|---:|---:|---:|---:|"]
    for name in ("test_A", "test_SPY"):
        r = results["reconciliation"][name]
        lines.append(f"| {name} | {r['stored_sharpe']:.6f} | {r['stored_sortino']:.6f} | {r['stored_risk_free_rate']:.10f} | {r['all_tick_drawdown_diagnostic']['difference_from_nexus_percentage_points']:+.6f} |")
    lines += ["", "The Test risk-free-rate field is approximately 4.3600001335; its scale and engine conversion are not established by the extracted metadata. It must not be silently reinterpreted as a particular annual fraction. The engine Sharpe/Sortino therefore are not directly comparable to the independent RF=0 ratios. Development and Validation stored RF fields were approximately 0.02 and 0.08. RF conventions do not explain discrepancies in equity total return or maximum drawdown.", "",
              "The frozen reconciliation materiality threshold is 0.01 percentage points. Four-decimal history precision causes tiny rounding differences; larger drawdown differences can reflect session-close versus intraday observations or source-engine conventions. All-tick diagnostics are supplementary and never replace daily metrics or selection. Any residual remaining against all available raw ticks is unresolved, not forced to match. Earlier material daily-DD differences in Development B/C and Validation A/SPY remain recorded unchanged in metrics.json.", "",
              "For both Test portfolios, all-tick maximum drawdown reproduces the stored engine drawdown within less than 0.000001 percentage points. This supports intraday sampling as the explanation for the material daily-close drawdown differences. Both Test total returns also reconcile within less than 0.000001 percentage points.", "",
              "## 12. Methodological limitations", "",
              "- The five-candidate Development search creates selection bias; its best Sharpe is not an unbiased forecast. No broader strategy-search history is available in this bounded experiment.",
              "- Only SPY and these specific historical windows were studied. No statistical significance test, beta/factor regression, or proof of persistent alpha was performed.",
              "- The processing calendar is an offline extension of the same session rules. It includes the 2018-12-05 and 2025-01-09 mourning closures. Raw holiday artifacts are excluded before returns, using calendar membership and timestamp-matched event evidence, not observed performance.",
              "- Market records with complete OHLCV identify regular and evidenced 13:00 early closes. Additional 09:00/13:00 history ticks and stale 16:00 early-close rows are not selected by row position.",
              "- Nexus history numbers are already rounded to four decimal places. Full run configuration and full strategy snapshots were not exposed by the extracted status tool; initial funding comes from the manifest. Dividend policy and detailed execution assumptions cannot all be independently verified.",
              "- Simulated fills and fees are not a guarantee of executable live results. Cash-flow, slippage, liquidity, tax, and financing conventions may affect real implementation. No new execution or robustness study was run.",
              "- Returns use adjacent daily closes; the first session has no close-to-close return. Total return includes inception-day equity change by dividing final equity by $25,000. Maximum drawdown resets to each period's own daily running peak, without an earlier period or synthetic funding row.",
              "- Sortino uses sqrt(mean(min(r,0)^2)) over all returns with MAR=0. Volatility uses sample SD and sqrt(252). Skew/kurtosis use the original corrected sample formulas, and quantiles retain linear interpolation. All these definitions were frozen before Test.",
              "- Explicit SPY is the saved buy-and-hold portfolio, not the history's separate comparison-value series. No explicit Development SPY run was supplied, so none is invented.",
              "- The one-time Test-opening claim follows the supplied experiment record. Local run IDs and freeze hashes corroborate the processing sequence, but these files are not an independent audit of all possible account activity.", "",
              "## 13. Final interpretation", ""]
    a, b = m["test_A"], m["test_SPY"]
    lines += [f"EXP001 does not establish that the AI discovered alpha. The selected SMA strategy had the highest eligible Development zero-RF Sharpe, but its total return trailed explicit SPY in both out-of-sample periods: {m['val_A']['total_return']:.3%} versus {m['val_SPY']['total_return']:.3%} in Validation, and {a['total_return']:.3%} versus {b['total_return']:.3%} in Test.", "",
              "The supported finding is that the AI-selected SMA trend strategy repeatedly reduced equity-market drawdowns and volatility, while failing to preserve enough upside to outperform passive SPY on cumulative return out of sample. This is a historical risk/return trade-off, not evidence of market-beating excess return or a causal effect uniquely attributable to AI.", "",
              f"Test zero-RF Sharpe was {a['sharpe']:.6f} for A versus {b['sharpe']:.6f} for SPY, and Sortino was {a['sortino']:.6f} versus {b['sortino']:.6f}. These ratios must be considered alongside the absolute-return gap; neither lower risk nor a favorable ratio alone proves alpha. The experiment identifies and measures a familiar moving-average timing behavior; it does not show that the AI invented a new predictive signal.", "",
              "EXP001 is complete. No strategy revision, new pass/fail rule, additional Test backtest, or Experiment 002 was initiated.", "",
              "Reproduce locally with `python -m src.nexus.process_exp001`; validate with `python -m unittest discover -s tests -v`. Full distribution statistics, drawdown dates, source hashes, and session diagnostics are in [metrics.json](../data/processed/EXP001_SPY_AI_SELECTION/metrics.json). The original regression baseline is [exp001_frozen_baseline.json](../tests/fixtures/exp001_frozen_baseline.json).", ""]
    report = workspace / "reports" / "EXP001_final_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
