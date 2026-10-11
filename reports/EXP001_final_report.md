# EXP001 final report

## 1. Experimental design

EXP001 compares five AI-proposed SPY trading candidates, selects one using Development only, and evaluates that frozen strategy against an explicit SPY buy-and-hold portfolio in two subsequent periods. Each reporting period is funded independently with $25,000; period returns are not chained. All reported performance below is independent zero-risk-free-rate performance from session-close equity, after the simulated fees reflected in the histories.

| Period | Window | Purpose |
|---|---|---|
| Development | 2015-01-01–2021-12-31 | Eligibility and candidate selection |
| Validation | 2022-01-01–2024-12-31 | Frozen A versus explicit SPY; no selection or pass/fail tuning |
| Held-out Test | 2025-01-01–2026-10-08 | Final frozen A versus explicit SPY |

According to the experiment record, the 2025–2026 Test was opened exactly once after the strategy and processing methodology were frozen. The extraction audit records pre-Test hashes of the metric module, processor, and Development/Validation results. This task read the two existing Test runs locally and made no Nexus calls or new backtests. The manifest's historical `SEALED` marker remains untouched; explicit authorization opened Test extraction and processing.

## 2. Five Development candidates

| Candidate | Recorded strategy family |
|---|---|
| A | SMA20/50 trend selection |
| B | Donchian breakout |
| C | RSI2 mean reversion |
| D | MACD + SMA100 |
| E | SMA100 + ATR filter |

These are experiment-record labels, not reconstructed full strategy snapshots. A's raw signal audits record buying when position market value is below 1 and the prior-day SMA20 exceeds SMA50, and selling when invested and SMA20 is at or below SMA50. Entry allocation is 99.5% of buying power; the stock fee setting is 0.10% of notional per fill.

## 3. Development selection rule

A candidate must have maximum drawdown at most 25% and at least 20 recorded completed round trips. Among eligible Development candidates, select the highest independently calculated zero-RF Sharpe. The recorded round-trip counts are used unchanged; no Validation or Test observation enters this decision.

## 4. Independent zero-RF Development results

| Candidate | Return | Ann. volatility | Sharpe | Sortino | Max DD | Round trips | Eligible |
|---|---:|---:|---:|---:|---:|---:|---|
| A | 80.179% | 10.880% | 0.828772 | 1.121108 | 14.858% | 46 | Yes |
| B | 32.906% | 7.897% | 0.554909 | 0.757195 | 21.239% | 98 | Yes |
| C | -39.355% | 11.098% | -0.581589 | -0.780344 | 46.205% | 432 | No |
| D | 28.212% | 6.615% | 0.570547 | 0.790188 | 12.942% | 246 | Yes |
| E | 5.618% | 8.511% | 0.136270 | 0.177628 | 16.085% | 92 | Yes |

## 5. Why Candidate A was selected

Candidate A's Development Sharpe was 0.828772, the highest among the eligible candidates. Its drawdown was 14.858%, with 46 recorded round trips. C was ineligible because its drawdown exceeded 25%. A's selection remains exactly the frozen Development result; later periods did not replace or retune it.

## 6. Validation results versus explicit SPY

| Portfolio | Sessions | Ending value | Return | Ann. volatility | Sharpe | Sortino | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Candidate A | 753 | $25,679.03 | 2.716% | 11.508% | 0.129792 | 0.183183 | 17.813% |
| SPY buy-and-hold | 753 | $31,651.32 | 26.605% | 17.275% | 0.540247 | 0.769795 | 24.646% |

| Candidate A minus SPY | Difference |
|---|---:|
| Total return | -23.889150 pp |
| Sharpe | -0.410455 |
| Sortino | -0.586612 |
| Annualized volatility | -5.766732 pp |
| Maximum drawdown | -6.832550 pp |

No retrospective pass/fail criterion or strategy selection is applied to this period.

## 7. Final held-out Test results versus explicit SPY

| Portfolio | Sessions | Ending value | Return | Ann. volatility | Sharpe | Sortino | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Candidate A | 443 | $29,110.93 | 16.444% | 9.885% | 0.927527 | 1.344627 | 5.862% |
| SPY buy-and-hold | 443 | $33,227.05 | 32.908% | 16.865% | 1.076116 | 1.627980 | 18.926% |

| Candidate A minus SPY | Difference |
|---|---:|
| Total return | -16.464452 pp |
| Sharpe | -0.148589 |
| Sortino | -0.283353 |
| Annualized volatility | -6.979595 pp |
| Maximum drawdown | -13.064051 pp |

No retrospective pass/fail criterion or strategy selection is applied to this period.

Each Test portfolio contributes 443 closes and 442 adjacent-close returns: 440 regular 16:00 closes and three event-backed 13:00 early closes. The calendar excludes copied holiday records on 2025-01-09 and 2026-04-03. The last selected observation is October 8, 2026 at 16:00 New York; the raw query ceiling of 2026-10-09T03:59:59.999Z is October 8 at 23:59:59.999 New York, not October 9 market data.

| Test portfolio | Drawdown peak | Trough | Recovery |
|---|---|---|---|
| Candidate A | 2025-02-19 | 2025-03-04 | 2025-06-03 |
| SPY buy-and-hold | 2025-02-19 | 2025-04-08 | 2025-06-26 |

## 8. Development → Validation → Test

| Candidate A metric | Development | Validation | Test |
|---|---:|---:|---:|
| Return | 80.179% | 2.716% | 16.444% |
| Annualized volatility | 10.880% | 11.508% | 9.885% |
| Sharpe (RF=0) | 0.828772 | 0.129792 | 0.927527 |
| Sortino | 1.121108 | 0.183183 | 1.344627 |
| Max drawdown | 14.858% | 17.813% | 5.862% |

| SPY metric | Validation | Test |
|---|---:|---:|
| Return | 26.605% | 32.908% |
| Annualized volatility | 17.275% | 16.865% |
| Sharpe (RF=0) | 0.540247 | 1.076116 |
| Sortino | 0.769795 | 1.627980 |
| Max drawdown | 24.646% | 18.926% |

The windows have different lengths. Total returns are period totals, not annualized returns, so their levels should not be interpreted as equal-duration growth rates.

## 9. Drawdown/volatility versus return trade-off

Validation: Candidate A reduced annualized volatility by 5.767 percentage points and maximum drawdown by 6.833 percentage points, while trailing SPY total return by 23.889 percentage points.

Test: Candidate A reduced annualized volatility by 6.980 percentage points and maximum drawdown by 13.064 percentage points, while trailing SPY total return by 16.464 percentage points.

These are separate observations: lower realized drawdown and volatility do not themselves establish outperformance or alpha. Candidate A also had lower independent zero-RF Sharpe and Sortino than SPY in both out-of-sample periods, so the observed risk reduction did not improve these return-to-risk ratios relative to the benchmark.

## 10. Transaction-cost observations

| Run | Stored total fees | Fees / initial funding | Stored dividends | Recorded closed trades |
|---|---:|---:|---:|---:|
| dev_A | $1,378.13 | 5.513% | $2,843.06 | 46 |
| dev_B | $2,790.81 | 11.163% | $1,688.78 | 98 |
| dev_C | $7,995.51 | 31.982% | $344.97 | 432 |
| dev_D | $6,252.60 | 25.010% | $1,276.84 | 246 |
| dev_E | $2,164.77 | 8.659% | $1,896.13 | 92 |
| val_A | $454.82 | 1.819% | $518.90 | 19 |
| val_SPY | $24.88 | 0.100% | $942.88 | 0 |
| test_A | $361.06 | 1.444% | $309.25 | 12 |
| test_SPY | $24.88 | 0.100% | $463.48 | 0 |

Fees are already reflected in equity; they are not subtracted a second time. Candidate A pays more than buy-and-hold in both out-of-sample windows. The table scales fees by initial funding for description only, not as an attribution of return loss. Dividends are stored cash-flow observations, not additional returns to add to equity. No fee-free counterfactual was run, so the return gap cannot be attributed solely to transaction costs. The stored `closedTradeCount` is retained under the engine's convention and is not independently rederived.

## 11. Nexus engine metric differences and risk-free-rate caveat

| Test run | Independent return | Stored engine return | Difference (pp) | Independent max DD | Stored engine max DD | Difference (pp) |
|---|---:|---:|---:|---:|---:|---:|
| test_A | 16.443736% | 16.443736% | -0.000000017 | 5.861601% | 5.939888% | -0.078287 |
| test_SPY | 32.908187% | 32.908187% | +0.000000063 | 18.925652% | 20.110436% | -1.184785 |

| Test run | Engine Sharpe | Engine Sortino | Stored riskFreeRate | All-tick DD residual versus engine (pp) |
|---|---:|---:|---:|---:|
| test_A | 0.479036 | 0.647368 | 4.3600001335 | +0.000000 |
| test_SPY | 0.753570 | 1.148832 | 4.3600001335 | +0.000000 |

The Test risk-free-rate field is approximately 4.3600001335; its scale and engine conversion are not established by the extracted metadata. It must not be silently reinterpreted as a particular annual fraction. The engine Sharpe/Sortino therefore are not directly comparable to the independent RF=0 ratios. Development and Validation stored RF fields were approximately 0.02 and 0.08. RF conventions do not explain discrepancies in equity total return or maximum drawdown.

The frozen reconciliation materiality threshold is 0.01 percentage points. Four-decimal history precision causes tiny rounding differences; larger drawdown differences can reflect session-close versus intraday observations or source-engine conventions. All-tick diagnostics are supplementary and never replace daily metrics or selection. Any residual remaining against all available raw ticks is unresolved, not forced to match. Earlier material daily-DD differences in Development B/C and Validation A/SPY remain recorded unchanged in metrics.json.

For both Test portfolios, all-tick maximum drawdown reproduces the stored engine drawdown within less than 0.000001 percentage points. This supports intraday sampling as the explanation for the material daily-close drawdown differences. Both Test total returns also reconcile within less than 0.000001 percentage points.

## 12. Methodological limitations

- The five-candidate Development search creates selection bias; its best Sharpe is not an unbiased forecast. No broader strategy-search history is available in this bounded experiment.
- Only SPY and these specific historical windows were studied. No statistical significance test, beta/factor regression, or proof of persistent alpha was performed.
- The processing calendar is an offline extension of the same session rules. It includes the 2018-12-05 and 2025-01-09 mourning closures. Raw holiday artifacts are excluded before returns, using calendar membership and timestamp-matched event evidence, not observed performance.
- Market records with complete OHLCV identify regular and evidenced 13:00 early closes. Additional 09:00/13:00 history ticks and stale 16:00 early-close rows are not selected by row position.
- Nexus history numbers are already rounded to four decimal places. Full run configuration and full strategy snapshots were not exposed by the extracted status tool; initial funding comes from the manifest. Dividend policy and detailed execution assumptions cannot all be independently verified.
- Simulated fills and fees are not a guarantee of executable live results. Cash-flow, slippage, liquidity, tax, and financing conventions may affect real implementation. No new execution or robustness study was run.
- Returns use adjacent daily closes; the first session has no close-to-close return. Total return includes inception-day equity change by dividing final equity by $25,000. Maximum drawdown resets to each period's own daily running peak, without an earlier period or synthetic funding row.
- Sortino uses sqrt(mean(min(r,0)^2)) over all returns with MAR=0. Volatility uses sample SD and sqrt(252). Skew/kurtosis use the original corrected sample formulas, and quantiles retain linear interpolation. All these definitions were frozen before Test.
- Explicit SPY is the saved buy-and-hold portfolio, not the history's separate comparison-value series. No explicit Development SPY run was supplied, so none is invented.
- The one-time Test-opening claim follows the supplied experiment record. Local run IDs and freeze hashes corroborate the processing sequence, but these files are not an independent audit of all possible account activity.

## 13. Final interpretation

EXP001 does not establish that the AI discovered alpha. The selected SMA strategy had the highest eligible Development zero-RF Sharpe, but its total return trailed explicit SPY in both out-of-sample periods: 2.716% versus 26.605% in Validation, and 16.444% versus 32.908% in Test.

The supported finding is that the AI-selected SMA trend strategy repeatedly reduced equity-market drawdowns and volatility, while failing to preserve enough upside to outperform passive SPY on cumulative return out of sample. This is a historical risk/return trade-off, not evidence of market-beating excess return or a causal effect uniquely attributable to AI.

Test zero-RF Sharpe was 0.927527 for A versus 1.076116 for SPY, and Sortino was 1.344627 versus 1.627980. These ratios must be considered alongside the absolute-return gap; neither lower risk nor a favorable ratio alone proves alpha. The experiment identifies and measures a familiar moving-average timing behavior; it does not show that the AI invented a new predictive signal.

EXP001 is complete. No strategy revision, new pass/fail rule, additional Test backtest, or Experiment 002 was initiated.

Reproduce locally with `python -m src.nexus.process_exp001`; validate with `python -m unittest discover -s tests -v`. Full distribution statistics, drawdown dates, source hashes, and session diagnostics are in [metrics.json](../data/processed/EXP001_SPY_AI_SELECTION/metrics.json). The original regression baseline is [exp001_frozen_baseline.json](../tests/fixtures/exp001_frozen_baseline.json).
