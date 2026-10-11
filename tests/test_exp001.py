"""Run with python -m unittest discover -s tests -v. No Nexus/network access."""

import math
import csv
import json
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from src.metrics.performance import daily_performance, drawdown, quantile
from src.nexus.process_exp001 import (
    development_selection, parse_history, select_session_closes, session_dates,
    validate_daily, reconciliation,
    process, parse_timestamp, market_close_evidence, NY, allowed_timestamp, sha256,
)


class PerformanceTests(unittest.TestCase):
    def test_sample_sd_sharpe_and_all_observation_downside(self):
        m = daily_performance([100, 110, 99, 108.9],
                              ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"],
                              initial_value=100)
        self.assertEqual(m["daily_return_count"], 3)
        self.assertAlmostEqual(m["mean_daily_return"], 1 / 30)
        self.assertAlmostEqual(m["sample_daily_standard_deviation"], math.sqrt(1 / 75))
        self.assertAlmostEqual(m["daily_downside_deviation"], math.sqrt(1 / 300))
        self.assertAlmostEqual(m["sharpe"], math.sqrt(21))
        self.assertAlmostEqual(m["sortino"], math.sqrt(84))
        self.assertAlmostEqual(m["total_return"], .089)
        self.assertAlmostEqual(m["skew"], -math.sqrt(3))

    def test_drawdown_peak_trough_recovery_and_period_reset(self):
        dates = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07", "2020-01-08"]
        result = drawdown([100, 120, 90, 110, 120], dates)
        self.assertEqual(result["maximum_drawdown"], .25)
        self.assertEqual(result["maximum_drawdown_peak_date"], dates[1])
        self.assertEqual(result["maximum_drawdown_trough_date"], dates[2])
        self.assertEqual(result["maximum_drawdown_recovery_date"], dates[4])
        self.assertIsNone(drawdown([100, 80], dates[:2])["maximum_drawdown_recovery_date"])
        self.assertAlmostEqual(drawdown([80, 72], dates[:2])["maximum_drawdown"], .1)

    def test_tied_peak_dates_use_latest_peak(self):
        d = drawdown([100, 100, 80], ["a", "b", "c"])
        self.assertEqual(d["maximum_drawdown_peak_date"], "b")

    def test_zero_volatility_and_no_losses_are_null(self):
        m = daily_performance([100, 100, 100], ["a", "b", "c"], initial_value=100)
        self.assertIsNone(m["sharpe"])
        self.assertIsNone(m["sortino"])
        self.assertIsNone(m["skew"])
        self.assertIsNone(m["maximum_drawdown_peak_date"])

    def test_linear_quantiles_and_corrected_kurtosis(self):
        self.assertEqual(quantile([4, 1, 3, 2], .25), 1.75)
        m = daily_performance([100, 101, 103.02, 106.1106, 110.355024],
                              ["a", "b", "c", "d", "e"], initial_value=100)
        self.assertAlmostEqual(m["skew"], 0)
        self.assertAlmostEqual(m["excess_kurtosis"], -1.2)

    def test_total_return_uses_funding_daily_returns_start_at_second_close(self):
        m = daily_performance([90, 99, 108.9], ["a", "b", "c"], initial_value=100)
        self.assertAlmostEqual(m["total_return"], .089)
        self.assertAlmostEqual(m["close_to_close_total_return"], .21)
        self.assertEqual(m["daily_return_count"], 2)

    def test_tail_counts_use_daily_returns_denominator(self):
        m = daily_performance([100, 97, 91.18, 100.298],
                              ["a", "b", "c", "d"], initial_value=100)
        self.assertEqual(m["days_below_minus_2pct"], 2)
        self.assertEqual(m["days_below_minus_5pct"], 1)
        self.assertAlmostEqual(m["percentage_days_below_minus_2pct"], 200 / 3)

    def test_invalid_values_and_dates_fail(self):
        for values, dates in (([100, float("nan")], ["a", "b"]),
                              ([100, 0], ["a", "b"]), ([100, 101], ["b", "a"])):
            with self.assertRaises(ValueError):
                daily_performance(values, dates, initial_value=100)


class SessionTests(unittest.TestCase):
    def test_offline_calendar_boundaries_and_exceptional_closures(self):
        dev = session_dates(date(2015, 1, 1), date(2021, 12, 31))
        val = session_dates(date(2022, 1, 1), date(2024, 12, 31))
        self.assertEqual(len(dev), 1763)
        self.assertEqual(len(val), 753)
        self.assertNotIn(date(2015, 4, 3), dev)
        self.assertNotIn(date(2018, 12, 5), dev)
        self.assertIn(date(2021, 12, 31), dev)
        self.assertNotIn(date(2022, 6, 20), val)
        self.assertNotIn(date(2023, 4, 7), val)
        self.assertIn(date(2021, 6, 18), dev)
        with self.assertRaises(ValueError):
            session_dates(date(2024, 1, 1), date(2025, 1, 1))

    def test_event_backed_early_close_precedes_stale_1600_tick(self):
        day = date(2015, 11, 27)
        def row(hour, value):
            t = datetime(2015, 11, 27, hour, tzinfo=timezone.utc)
            return {"date": str(day), "timestamp": t.isoformat(), "_datetime": t,
                    "portfolio_value": value}
        history = [row(14, 100), row(18, 105), row(21, 106)]
        daily, _ = select_session_closes(history, {day: {"timestamp": history[1]["_datetime"], "ohlcv": {}}}, day, day)
        self.assertEqual(daily[0]["portfolio_value"], 105)

    def test_missing_session_evidence_fails_without_fallback(self):
        with self.assertRaises(ValueError):
            select_session_closes([], {}, date(2015, 1, 2), date(2015, 1, 2))

    def test_raw_parser_preserves_null_collateral_and_rejects_future(self):
        def payload(day):
            return {"backtest_id": "x", "pages": [{"request": {
                "backtest_id": "x", "page": 1, "start_date": "2024-01-02", "end_date": "2024-01-02"},
                "response": {"content": [{"type": "text", "text":
                    "page 1/1, 1 points\ntime, value, cash, positionValue, comparisonValue, reservedCollateral\n"
                    + day + "T21:00:00.000Z, 100.0000, 5.0000, 95.0000, 100.0000, null"}]}}]}
        rows = parse_history(payload("2024-01-02"), "x", date(2024, 1, 2), date(2024, 1, 2))
        self.assertIsNone(rows[0]["reserved_collateral"])
        with self.assertRaises(ValueError):
            parse_history(payload("2025-01-02"), "x", date(2024, 1, 2), date(2024, 1, 2))

    def test_duplicate_missing_equity_and_out_of_period_rows_fail(self):
        day = date(2024, 1, 2)
        row = {"date": str(day), "_datetime": datetime(2024, 1, 2, 21, tzinfo=timezone.utc),
               "portfolio_value": 100}
        with self.assertRaises(ValueError):
            validate_daily([row, row], {day}, day, day)
        with self.assertRaises(ValueError):
            validate_daily([{**row, "portfolio_value": None}], {day}, day, day)
        with self.assertRaises(ValueError):
            validate_daily([{**row, "_datetime": datetime(2025, 1, 2, tzinfo=timezone.utc)}], {day}, day, day)


class SelectionAndReconciliationTests(unittest.TestCase):
    def test_development_only_rules_disqualify_high_sharpe_bad_drawdown(self):
        m = {"dev_" + c: {"sharpe": i, "maximum_drawdown": .1}
             for i, c in enumerate("ABCDE")}
        m["dev_E"]["maximum_drawdown"] = .251
        result = development_selection(m, {"maximum_drawdown_percent": 25, "minimum_completed_round_trips": 20})
        self.assertEqual(result["winner"], "dev_D")
        self.assertFalse(result["candidates"]["dev_E"]["eligible"])
        self.assertFalse(result["selection_uses_validation"])

    def test_reconciliation_flags_material_delta_without_changing_numbers(self):
        m = {"total_return": .10, "maximum_drawdown": .05}
        stored = {"statistics": {"percentChange": 10, "maxDrawdown": 6}}
        result = reconciliation(m, stored)
        self.assertFalse(result["comparisons"]["total_return"]["material_discrepancy"])
        self.assertTrue(result["comparisons"]["maximum_drawdown"]["material_discrepancy"])
        self.assertEqual(m["maximum_drawdown"], .05)


class FinalTestIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = Path(__file__).resolve().parents[1]
        cls.output = cls.workspace / "data" / "processed" / "EXP001_SPY_AI_SELECTION"
        cls.raw = cls.workspace / "data" / "raw" / "EXP001_SPY_AI_SELECTION"
        cls.fixture = json.loads((cls.workspace / "tests" / "fixtures" / "exp001_frozen_baseline.json").read_text())
        cls.result = process(cls.workspace)
        cls.rows = {}
        for name in ("test_A", "test_SPY"):
            with (cls.output / f"{name}_daily.csv").open(newline="", encoding="utf-8") as handle:
                cls.rows[name] = list(csv.DictReader(handle))

    def test_exactly_one_event_backed_close_for_each_test_session(self):
        start, end = date(2025, 1, 1), date(2026, 10, 8)
        expected = sorted(session_dates(start, end, allow_test=True))
        self.assertEqual(len(expected), 443)
        self.assertNotIn(date(2025, 1, 9), expected)
        self.assertNotIn(date(2026, 4, 3), expected)
        for name, rows in self.rows.items():
            payload = json.loads((self.raw / f"{name}_events.json").read_text())
            evidence = market_close_evidence(payload, payload["backtest_id"], start, end, allow_test=True)
            self.assertEqual([date.fromisoformat(r["date"]) for r in rows], expected)
            for row in rows:
                day = date.fromisoformat(row["date"])
                self.assertEqual(parse_timestamp(row["timestamp"]), evidence[day]["timestamp"])
            self.assertEqual(self.result["session_diagnostics"][name]["close_time_counts_new_york"],
                             {"13:00": 3, "16:00": 440})

    def test_no_duplicate_test_dates(self):
        for rows in self.rows.values():
            dates = [r["date"] for r in rows]
            self.assertEqual(len(dates), len(set(dates)))

    def test_strictly_increasing_test_dates(self):
        for rows in self.rows.values():
            dates = [r["date"] for r in rows]
            self.assertTrue(all(a < b for a, b in zip(dates, dates[1:])))

    def test_no_missing_or_nonfinite_test_equity(self):
        for rows in self.rows.values():
            self.assertTrue(all(r["portfolio_value"] and math.isfinite(float(r["portfolio_value"])) for r in rows))

    def test_no_test_market_date_after_authorized_october_8(self):
        for rows in self.rows.values():
            for row in rows:
                timestamp = parse_timestamp(row["timestamp"])
                self.assertLessEqual(timestamp.astimezone(NY).date(), date(2026, 10, 8))
                self.assertGreaterEqual(timestamp.astimezone(NY).date(), date(2025, 1, 1))
                self.assertEqual(timestamp.astimezone(NY).date().isoformat(), row["date"])

    def test_new_york_boundary_not_utc_midnight_and_default_test_seal(self):
        start, end = date(2025, 1, 1), date(2026, 10, 8)
        allowed_timestamp(parse_timestamp("2026-10-09T03:59:59.999Z"), start, end, allow_test=True)
        with self.assertRaises(ValueError):
            allowed_timestamp(parse_timestamp("2026-10-09T04:00:00.000Z"), start, end, allow_test=True)
        with self.assertRaises(ValueError):
            allowed_timestamp(parse_timestamp("2026-10-08T20:00:00.000Z"), start, end)

    def test_existing_development_validation_outputs_and_definitions_unchanged(self):
        for filename, expected in self.fixture["daily_csv_sha256"].items():
            self.assertEqual(sha256(self.output / filename), expected)
        frozen = self.fixture["frozen_metrics"]
        for section in ("definitions", "development_selection", "validation_comparison"):
            self.assertEqual(self.result[section], frozen[section])
        for section in ("metrics", "session_diagnostics", "reconciliation"):
            for name, value in frozen[section].items():
                self.assertEqual(self.result[section][name], value)
        self.assertEqual(sha256(self.workspace / "src" / "metrics" / "performance.py"),
                         self.fixture["performance_module_sha256"])

    def test_raw_inputs_and_manifest_unchanged(self):
        for relative, expected in self.result["source_sha256"].items():
            self.assertEqual(sha256(self.workspace / relative), expected)

    def test_rerunning_processor_and_report_is_byte_deterministic(self):
        paths = list(self.output.glob("*.csv")) + [self.output / "metrics.json",
                 self.workspace / "reports" / "EXP001_final_report.md"]
        before = {str(p): sha256(p) for p in paths}
        again = process(self.workspace)
        self.assertEqual(again, self.result)
        self.assertEqual({str(p): sha256(p) for p in paths}, before)


if __name__ == "__main__":
    unittest.main()
