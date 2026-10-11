"""Local-only EXP001 processing. Run: python -m src.nexus.process_exp001.

No network clients are imported. Only the seven original runs and two authorized
Final Test runs are read. Original processing remains restricted to 2015-2024;
the explicit Test extension allows 2025-01-01 through 2026-10-08 in New York.
Actual close times come from raw SPY Market OHLCV events, including early closes;
the calendar filters provider holiday artifacts, not history-row positions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.metrics.performance import daily_performance, drawdown

EXPERIMENT = "EXP001_SPY_AI_SELECTION"
NY = ZoneInfo("America/New_York")
SEALED_BOUNDARY = datetime(2025, 1, 1, tzinfo=timezone.utc)
ROUND_TRIPS = {"dev_A": 46, "dev_B": 98, "dev_C": 432, "dev_D": 246, "dev_E": 92}
HISTORY_SCHEMA = "time, value, cash, positionValue, comparisonValue, reservedCollateral"
CSV_FIELDS = ["date", "timestamp", "portfolio_value", "cash", "position_value",
              "comparison_value", "reserved_collateral"]
EVENT_HEADER = re.compile(r"\n\[\d{4}-\d\d-\d\d [^\]]+\] [^\n]+ \(raw\)\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def response_text(response: dict) -> str:
    if response.get("isError"):
        raise ValueError("Saved Nexus response reports an error")
    return "\n".join(c["text"] for c in response["content"] if c["type"] == "text")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def allowed_timestamp(timestamp: datetime, start: date, end: date, *, allow_test: bool = False) -> None:
    if allow_test:
        if (start, end) != (date(2025, 1, 1), date(2026, 10, 8)):
            raise ValueError("Test authorization is limited to the exact frozen Test window")
        # October 8 ends at 2026-10-09 03:59:59.999 UTC, not UTC midnight.
        if not start <= timestamp.astimezone(NY).date() <= end:
            raise ValueError("Test simulated timestamp outside authorized New York window")
        return
    if timestamp >= SEALED_BOUNDARY or not start <= timestamp.date() <= end:
        raise ValueError(f"Simulated timestamp outside allowed period: {timestamp}")
    if not start <= timestamp.astimezone(NY).date() <= end:
        raise ValueError("New York session date outside allowed period")


def easter(year: int) -> date:
    """Gregorian computus, used for the Good Friday closure."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (occurrence - 1))


def observed(day: date) -> date:
    return day + timedelta(days=-1 if day.weekday() == 5 else 1 if day.weekday() == 6 else 0)


def session_dates(start: date, end: date, *, allow_test: bool = False) -> set[date]:
    """Offline NYSE full-day closures, with an explicit authorized Test extension.

    Saturday New Year's Day has no preceding-Friday NYSE observance. Juneteenth
    begins in 2022. The 2018-12-05 presidential mourning closure is included.
    Early-close times are determined separately from saved Market events.
    """
    if allow_test and (start, end) != (date(2025, 1, 1), date(2026, 10, 8)):
        raise ValueError("Test calendar is limited to the exact authorized Test period")
    calendar_end = date(2026, 10, 8) if allow_test else date(2024, 12, 31)
    if start < date(2015, 1, 1) or end > calendar_end or end < start:
        raise ValueError("Offline session calendar supports only 2015-2024")
    holidays = {date(2018, 12, 5)}
    if allow_test:
        # Carter mourning closure: a calendar extension, not a metric change.
        holidays.add(date(2025, 1, 9))
    for year in range(start.year, end.year + 1):
        new_year = date(year, 1, 1)
        if new_year.weekday() != 5:
            holidays.add(observed(new_year))
        holidays.update({
            nth_weekday(year, 1, 0, 3), nth_weekday(year, 2, 0, 3),
            easter(year) - timedelta(days=2),
            date(year, 6, 1) - timedelta(days=(date(year, 6, 1).weekday() - 0) % 7 or 7),
            observed(date(year, 7, 4)), nth_weekday(year, 9, 0, 1),
            nth_weekday(year, 11, 3, 4), observed(date(year, 12, 25)),
        })
        if year >= 2022:
            holidays.add(observed(date(year, 6, 19)))
    return {start + timedelta(days=i) for i in range((end - start).days + 1)
            if (start + timedelta(days=i)).weekday() < 5
            and start + timedelta(days=i) not in holidays}


def parse_history(payload: dict, backtest_id: str, start: date, end: date, *, allow_test: bool = False) -> list[dict]:
    if payload["backtest_id"] != backtest_id:
        raise ValueError("History run ID mismatch")
    rows = []
    pages = payload["pages"]
    declared_total = None
    for number, page in enumerate(pages, 1):
        request = page["request"]
        validate_request(request, backtest_id, start, end, number, allow_test=allow_test)
        text = response_text(page["response"])
        heading = re.search(r"page (\d+)/(\d+), (\d+) points", text)
        if not heading or int(heading[1]) != number or int(heading[2]) != len(pages):
            raise ValueError("History pagination mismatch")
        declared_total = int(heading[3])
        if HISTORY_SCHEMA not in text:
            raise ValueError("Unexpected raw history schema")
        for line in text.splitlines():
            if not re.match(r"^\d{4}-\d\d-\d\dT", line):
                continue
            fields = next(csv.reader([line], skipinitialspace=True))
            if len(fields) != 6:
                raise ValueError("History row does not have six fields")
            timestamp = parse_timestamp(fields[0])
            allowed_timestamp(timestamp, start, end, allow_test=allow_test)
            numbers = [None if v == "null" else float(v) for v in fields[1:]]
            if any(v is None or not math.isfinite(v) for v in numbers[:4]):
                raise ValueError("Missing/nonfinite equity fields")
            if numbers[4] is not None and not math.isfinite(numbers[4]):
                raise ValueError("Nonfinite collateral")
            row = dict(zip(CSV_FIELDS[2:], numbers))
            row.update(date=timestamp.astimezone(NY).date().isoformat(),
                       timestamp=fields[0], _datetime=timestamp)
            rows.append(row)
    if len(rows) != declared_total:
        raise ValueError("History row total mismatch")
    if any(a["_datetime"] >= b["_datetime"] for a, b in zip(rows, rows[1:])):
        raise ValueError("Raw history timestamps must be strictly ascending")
    return rows


def validate_request(request: dict, backtest_id: str, start: date, end: date, page: int, *, allow_test: bool = False) -> None:
    if allow_test:
        expected_start = datetime.combine(start, time.min, NY).astimezone(timezone.utc)
        expected_end = (datetime.combine(end + timedelta(days=1), time.min, NY)
                        .astimezone(timezone.utc) - timedelta(milliseconds=1))
        if (request["backtest_id"] != backtest_id or request["page"] != page
                or parse_timestamp(request["start_date"]) != expected_start
                or parse_timestamp(request["end_date"]) != expected_end):
            raise ValueError("Test raw page request differs from authorized New York period")
        return
    if (request["backtest_id"] != backtest_id or request["page"] != page
            or request["start_date"] != start.isoformat()
            or request["end_date"] != end.isoformat()):
        raise ValueError("Raw page request differs from preregistered run/period")


def market_close_evidence(payload: dict, backtest_id: str, start: date, end: date, *, allow_test: bool = False) -> dict:
    if payload["backtest_id"] != backtest_id:
        raise ValueError("Events run ID mismatch")
    closes = {}
    for number, page in enumerate(payload["pages"], 1):
        validate_request(page["request"], backtest_id, start, end, number, allow_test=allow_test)
        for part in EVENT_HEADER.split(response_text(page["response"]))[1:]:
            # Decode locally but never use administrative dates, dividend schedules,
            # or other future-dated ancillary fields as observations or metrics.
            event = json.loads(part.split("\n\n---", 1)[0])
            timestamp = datetime.fromtimestamp(event["timestamp"] / 1000, timezone.utc)
            allowed_timestamp(timestamp, start, end, allow_test=allow_test)
            if event["eventType"] != "Market":
                continue
            prices = event["event"].get("prices", {}).get("SPY Stock", {})
            if not all(k in prices for k in ("price", "volume", "open", "high", "low")):
                continue
            if parse_timestamp(event["event"]["timestamp"]) != timestamp:
                raise ValueError("Inner/outer event timestamp mismatch")
            local = timestamp.astimezone(NY)
            if local.time() not in (time(13), time(16)):
                raise ValueError("Unexpected close-like Market event time")
            if local.date() in closes:
                raise ValueError("Multiple close-like Market events on one date")
            closes[local.date()] = {"timestamp": timestamp, "ohlcv": prices}
    return closes


def select_session_closes(history: list[dict], evidence: dict, start: date, end: date, *, allow_test: bool = False) -> tuple[list[dict], dict]:
    expected = session_dates(start, end, allow_test=allow_test)
    missing = expected - evidence.keys()
    if missing:
        raise ValueError(f"Missing Market-close evidence for sessions: {sorted(missing)}")
    by_timestamp = {row["_datetime"]: row for row in history}
    selected = []
    for day in sorted(expected):
        timestamp = evidence[day]["timestamp"]
        if timestamp not in by_timestamp:
            raise ValueError(f"Session close has no exact history observation: {day}")
        row = by_timestamp[timestamp]
        if row["date"] != day.isoformat():
            raise ValueError("Local close date mismatch")
        selected.append(row)
    validate_daily(selected, expected, start, end, allow_test=allow_test)
    history_days = {date.fromisoformat(row["date"]) for row in history}
    holidays = sorted(set(evidence) - expected)
    copied = []
    for day in holidays:
        previous = max((d for d in expected if d < day), default=None)
        copied.append({"excluded_date": day.isoformat(),
                       "previous_session_date": previous.isoformat() if previous else None,
                       "ohlcv_identical_to_previous_session": previous is not None
                       and evidence[day]["ohlcv"] == evidence[previous]["ohlcv"]})
    diagnostics = {
        "raw_history_rows": len(history), "daily_close_rows": len(selected),
        "expected_session_rows": len(expected),
        "close_time_counts_new_york": dict(sorted(Counter(
            row["_datetime"].astimezone(NY).strftime("%H:%M") for row in selected).items())),
        "excluded_non_session_history_dates": [d.isoformat() for d in sorted(history_days - expected)],
        "excluded_non_session_close_events": copied,
        "all_validation_checks_passed": True,
    }
    return selected, diagnostics


def validate_daily(rows: list[dict], expected: set[date], start: date, end: date, *, allow_test: bool = False) -> None:
    dates = [date.fromisoformat(row["date"]) for row in rows]
    if dates != sorted(expected) or len(dates) != len(set(dates)):
        raise ValueError("Expected exactly one close for each trading date")
    for row in rows:
        allowed_timestamp(row["_datetime"], start, end, allow_test=allow_test)
        if row["portfolio_value"] is None or not math.isfinite(row["portfolio_value"]):
            raise ValueError("Missing portfolio value")


def stored_metadata(payload: dict, backtest_id: str) -> dict:
    status = next(p for p in payload["requests"] if p["operation"] == "query_backtest_status")
    match = re.search(r"```json\n([\s\S]*?)\n```", response_text(status["response"]))
    if not match:
        raise ValueError("Stored status has no structured backtest data")
    backtest = json.loads(match[1])["backtest"]
    if backtest["id"] != backtest_id:
        raise ValueError("Stored metadata run ID mismatch")
    return {"statistics": backtest["statistics"], "warnings": backtest["warnings"],
            "feeConfig": backtest["feeConfig"], "interval": backtest["interval"]}


def development_selection(metrics: dict, rules: dict) -> dict:
    candidates = {}
    for name, count in ROUND_TRIPS.items():
        m = metrics[name]
        eligible = (m["maximum_drawdown"] * 100 <= rules["maximum_drawdown_percent"]
                    and count >= rules["minimum_completed_round_trips"])
        candidates[name] = {"completed_round_trips": count, "maximum_drawdown_percent": m["maximum_drawdown"] * 100,
                            "sharpe": m["sharpe"], "eligible": eligible}
    eligible = [name for name in candidates if candidates[name]["eligible"]
                and candidates[name]["sharpe"] is not None]
    if not eligible:
        raise ValueError("No eligible Development candidate with defined Sharpe")
    highest = max(candidates[name]["sharpe"] for name in eligible)
    winners = [name for name in eligible if candidates[name]["sharpe"] == highest]
    if len(winners) != 1:
        raise ValueError("Preregistration has no tie-break rule for identical Sharpe")
    return {"candidates": candidates, "winner": winners[0],
            "candidate_A_remains_development_winner": winners[0] == "dev_A",
            "selection_uses_validation": False}


def reconciliation(independent: dict, stored: dict, all_tick_drawdown: float | None = None) -> dict:
    stats = stored["statistics"]
    differences = {}
    # Absolute percentage-point threshold, specified before viewing outcomes.
    threshold_pp = 0.01
    for metric, nexus_field in (("total_return", "percentChange"), ("maximum_drawdown", "maxDrawdown")):
        existing = stats.get(nexus_field)
        independent_pp = independent[metric] * 100
        delta = independent_pp - existing if existing is not None else None
        differences[metric] = {"independent_percent": independent_pp, "nexus_percent": existing,
                               "difference_percentage_points": delta,
                               "material_discrepancy": abs(delta) > threshold_pp if delta is not None else None}
    all_tick_check = None
    if all_tick_drawdown is not None and stats.get("maxDrawdown") is not None:
        residual = all_tick_drawdown * 100 - stats["maxDrawdown"]
        all_tick_check = {
            "diagnostic_only_not_used_for_selection": True,
            "all_history_ticks_maximum_drawdown_percent": all_tick_drawdown * 100,
            "difference_from_nexus_percentage_points": residual,
            "residual_material_discrepancy": abs(residual) > threshold_pp,
            "interpretation": (
                "All-tick drawdown reconciles with stored drawdown within tolerance; session-close sampling explains the daily difference."
                if abs(residual) <= threshold_pp else
                "Residual remains after checking all available history ticks. Source-engine convention or unexposed observations may differ; cause is not established."
            ),
        }
    return {"materiality_threshold_percentage_points": threshold_pp, "comparisons": differences,
            "all_tick_drawdown_diagnostic": all_tick_check,
            "stored_risk_free_rate": stats.get("riskFreeRate"),
            "stored_sharpe": stats.get("sharpeRatio"), "stored_sortino": stats.get("sortinoRatio"),
            "possible_causes": ["Nexus history rounds values to four decimals.",
                                "Independent drawdown uses daily session closes; Nexus may use intraday ticks.",
                                "Provider holiday artifacts are excluded from independent daily series.",
                                "Nexus has different stored risk-free rates and may use different metric conventions; RF affects Sharpe/Sortino, not equity total return or drawdown."]}


def process_development_validation(workspace: Path, *, write_outputs: bool = True) -> dict:
    manifest_path = workspace / "experiments" / EXPERIMENT / "manifest.json"
    raw = workspace / "data" / "raw" / EXPERIMENT
    output = workspace / "data" / "processed" / EXPERIMENT
    manifest = load_json(manifest_path)
    audit = load_json(raw / "integrity_report.json")
    if sha256(manifest_path) != audit["manifest_sha256"]:
        raise ValueError("Manifest differs from extraction audit")
    if manifest["test"]["status"] != "SEALED":
        raise ValueError("Expected sealed Test definition")
    definitions = manifest["independent_statistics"]
    if definitions != {"risk_free_rate": 0.0, "trading_days_per_year": 252,
                       "return_definition": "simple daily return", "standard_deviation": "sample"}:
        raise ValueError("Preregistered statistics definitions changed")
    runs = {"dev_" + key[0]: (value, manifest["development"])
            for key, value in manifest["development"]["backtests"].items()}
    runs.update(val_A=(manifest["validation"]["candidate_A_backtest"], manifest["validation"]),
                val_SPY=(manifest["validation"]["spy_buy_hold_backtest"], manifest["validation"]))
    audited_hashes = {f["name"]: f["sha256"] for f in audit["files"]}
    protected_paths = [manifest_path, raw / "integrity_report.json"] + [
        raw / f"{name}_{kind}.json" for name in runs for kind in ("history", "events", "metadata")]
    before = {str(p.relative_to(workspace)): sha256(p) for p in protected_paths}
    for p in protected_paths[2:]:
        if before[str(p.relative_to(workspace))] != audited_hashes[p.name]:
            raise ValueError(f"Raw hash differs from extraction audit: {p.name}")
    metrics, diagnostics, stored, csvs, all_tick_drawdowns = {}, {}, {}, {}, {}
    for name, (backtest_id, period) in runs.items():
        start, end = date.fromisoformat(period["start"]), date.fromisoformat(period["end"])
        if end >= date(2025, 1, 1):
            raise ValueError("Period would access sealed Test data")
        history = parse_history(load_json(raw / f"{name}_history.json"), backtest_id, start, end)
        evidence = market_close_evidence(load_json(raw / f"{name}_events.json"), backtest_id, start, end)
        daily, diagnostics[name] = select_session_closes(history, evidence, start, end)
        all_tick_drawdowns[name] = drawdown(
            [r["portfolio_value"] for r in history], [r["timestamp"] for r in history]
        )["maximum_drawdown"]
        metrics[name] = daily_performance([r["portfolio_value"] for r in daily], [r["date"] for r in daily],
                                         initial_value=manifest["starting_cash"], **{
                                             k: definitions[k] for k in ("risk_free_rate", "trading_days_per_year")})
        stored[name] = stored_metadata(load_json(raw / f"{name}_metadata.json"), backtest_id)
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(daily)
        csvs[name] = buffer.getvalue()
    # Selection is a function of Development metrics and preregistered counts only.
    selection = development_selection({n: metrics[n] for n in ROUND_TRIPS}, manifest["development"]["eligibility"])
    validation = {"frozen_development_winner": selection["winner"], "pass_fail_rule_created": False}
    if selection["winner"] != "dev_A":
        validation.update(status="unavailable", reason="Only Candidate A has a saved candidate Validation run. No substitution, new selection, or Nexus run was performed.")
    else:
        differences = {}
        for key in ("total_return", "sharpe", "sortino", "annualized_volatility", "maximum_drawdown"):
            a, b = metrics["val_A"][key], metrics["val_SPY"][key]
            delta = a - b if a is not None and b is not None else None
            differences[key] = {"candidate_minus_spy": delta}
            if key in ("total_return", "annualized_volatility", "maximum_drawdown"):
                differences[key]["difference_percentage_points"] = delta * 100 if delta is not None else None
        validation.update(status="available", candidate_run="val_A", benchmark_run="val_SPY", differences=differences)
    after = {str(p.relative_to(workspace)): sha256(p) for p in protected_paths}
    if before != after:
        raise ValueError("Raw inputs or manifest changed during processing")
    result = {
        "experiment_id": EXPERIMENT, "pipeline_version": 1,
        "definitions": {**definitions, "return_units": "fraction unless field explicitly says percent",
                        "daily_returns": "Adjacent selected session closes; first session has no daily return.",
                        "total_return": "Ending close / manifest starting_cash - 1; includes inception-day change.",
                        "maximum_drawdown": "Positive loss magnitude from this period's daily running peak; no prior-period peak or synthetic initial-equity row.",
                        "sortino": "sqrt(252) * mean(return) / sqrt(mean(min(return,0)^2)), over all returns; daily MAR=0.",
                        "skew": "Adjusted Fisher-Pearson sample skewness.",
                        "excess_kurtosis": "Bias-corrected Fisher excess kurtosis.",
                        "quantiles": "Linear interpolation, type 7.",
                        "tail_days": "Strictly below -2% / -5%; denominator is available daily returns.",
                        "session_close": "Exact timestamp match to SPY Market OHLCV event on an offline NYSE session date; 16:00 regular / 13:00 early close.",
                        "offline_calendar": "2015-2024 weekday/NYSE holiday rules, Juneteenth from 2022, 2018-12-05 mourning closure, no Friday observance of Saturday New Year.",
                        "undefined_statistics": "null; no NaN/Infinity emitted"},
        "metrics": metrics, "session_diagnostics": diagnostics,
        "development_selection": selection, "validation_comparison": validation,
        "reconciliation": {name: reconciliation(metrics[name], stored[name], all_tick_drawdowns[name]) for name in runs},
        "source_sha256": before,
        "integrity": {"raw_and_manifest_unchanged": True, "no_nexus_calls": True,
                      "no_processed_timestamp_on_or_after_2025_01_01": True,
                      "all_runs_have_one_close_per_expected_session": True,
                      "sealed_test_not_processed": True},
        "precision_limitations": ["Nexus history response values were already rounded to four decimal places.",
                                 "Initial funding uses manifest starting_cash; Nexus status did not expose this configuration field.",
                                 "Stored round-trip counts are used exactly as instructed; they are not recalculated from events.",
                                 "Administrative timestamps and dividend schedules in raw envelopes are not processed as observations."],
    }
    if write_outputs:
        output.mkdir(parents=True, exist_ok=True)
        for name, content in csvs.items():
            (output / f"{name}_daily.csv").write_text(content, encoding="utf-8", newline="")
        (output / "metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def process(workspace: Path) -> dict:
    """Append authorized Test results without changing the frozen original results."""
    raw = workspace / "data" / "raw" / EXPERIMENT
    output = workspace / "data" / "processed" / EXPERIMENT
    fixture_path = workspace / "tests" / "fixtures" / "exp001_frozen_baseline.json"
    fixture = load_json(fixture_path)
    audit = load_json(raw / "test_integrity_report.json")
    baseline_text = json.dumps(fixture["frozen_metrics"], indent=2, allow_nan=False) + "\n"
    # The original Windows write_text used native CRLF; the fixture preserves
    # parsed values. Accept only the original serialized bytes in LF or CRLF.
    baseline_hashes = {hashlib.sha256(s.encode("utf-8")).hexdigest()
                       for s in (baseline_text, baseline_text.replace("\n", "\r\n"))}
    if audit["protected_sha256"][f"data/processed/{EXPERIMENT}/metrics.json"] not in baseline_hashes:
        raise ValueError("Regression baseline does not match the pre-Test extraction freeze hash")
    manifest_path = workspace / "experiments" / EXPERIMENT / "manifest.json"
    manifest = load_json(manifest_path)
    start, end = date.fromisoformat(manifest["test"]["start"]), date.fromisoformat(manifest["test"]["end"])
    if (start, end) != (date(2025, 1, 1), date(2026, 10, 8)):
        raise ValueError("Final Test period differs from explicit authorization")
    metric_module = workspace / "src" / "metrics" / "performance.py"
    metric_hash = sha256(metric_module)
    if (metric_hash != fixture["performance_module_sha256"]
            or metric_hash != audit["protected_sha256"]["src/metrics/performance.py"]):
        raise ValueError("Frozen metric implementation changed")
    expected_runs = {"test_A": "6acaf3498c2f7fb888b371d9", "test_SPY": "6acaf3498c2f7fb888b371d8"}
    if audit["authorized_run_ids"] != expected_runs:
        raise ValueError("Final Test run IDs differ from authorized extraction")
    if audit["authorized_new_york_window"] != {
        "start_date": start.isoformat(), "end_date": end.isoformat(), "timezone": "America/New_York"
    }:
        raise ValueError("Final Test audit period differs from manifest")
    legacy_csv_hashes = {filename: sha256(output / filename) for filename in fixture["daily_csv_sha256"]}
    if legacy_csv_hashes != fixture["daily_csv_sha256"]:
        raise ValueError("Existing Development/Validation CSV differs from frozen baseline")
    # Recalculate the original seven runs with default pre-Test guards, without
    # writing those CSVs or the old metrics.json. Require exact baseline equality.
    result = process_development_validation(workspace, write_outputs=False)
    if result != fixture["frozen_metrics"]:
        raise ValueError("Development/Validation results or definitions differ from frozen baseline")
    existing = load_json(output / "metrics.json")
    for section in ("definitions", "development_selection", "validation_comparison"):
        if existing[section] != result[section]:
            raise ValueError(f"Existing frozen section changed: {section}")
    for section in ("metrics", "session_diagnostics", "reconciliation"):
        for name, value in result[section].items():
            if existing[section][name] != value:
                raise ValueError(f"Existing frozen values changed: {section}/{name}")
    if result["development_selection"]["winner"] != "dev_A":
        raise ValueError("Frozen selected strategy is not Candidate A")
    source_paths = [manifest_path, raw / "test_integrity_report.json", metric_module, fixture_path] + [
        raw / f"{name}_{kind}.json" for name in expected_runs for kind in ("history", "events", "metadata")]
    before = {str(p.relative_to(workspace)): sha256(p) for p in source_paths}
    audited_hashes = {f["name"]: f["sha256"] for f in audit["files"]}
    for name in expected_runs:
        for kind in ("history", "events", "metadata"):
            filename = f"{name}_{kind}.json"
            if sha256(raw / filename) != audited_hashes[filename]:
                raise ValueError(f"Test raw input changed: {filename}")
    csvs = {}
    for name, backtest_id in expected_runs.items():
        history = parse_history(load_json(raw / f"{name}_history.json"), backtest_id, start, end, allow_test=True)
        evidence = market_close_evidence(load_json(raw / f"{name}_events.json"), backtest_id, start, end, allow_test=True)
        daily, diagnostic = select_session_closes(history, evidence, start, end, allow_test=True)
        metrics = daily_performance(
            [r["portfolio_value"] for r in daily], [r["date"] for r in daily],
            initial_value=manifest["starting_cash"], risk_free_rate=0.0, trading_days_per_year=252,
        )
        metadata = stored_metadata(load_json(raw / f"{name}_metadata.json"), backtest_id)
        all_tick = drawdown([r["portfolio_value"] for r in history], [r["timestamp"] for r in history])
        result["metrics"][name] = metrics
        result["session_diagnostics"][name] = diagnostic
        result["reconciliation"][name] = reconciliation(metrics, metadata, all_tick["maximum_drawdown"])
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(daily)
        csvs[name] = buffer.getvalue()
    differences = {}
    for key in ("total_return", "sharpe", "sortino", "annualized_volatility", "maximum_drawdown"):
        a, b = result["metrics"]["test_A"][key], result["metrics"]["test_SPY"][key]
        delta = a - b if a is not None and b is not None else None
        differences[key] = {"candidate_minus_spy": delta}
        if key in ("total_return", "annualized_volatility", "maximum_drawdown"):
            differences[key]["difference_percentage_points"] = delta * 100 if delta is not None else None
    result["test_comparison"] = {
        "frozen_development_winner": "dev_A", "candidate_run": "test_A", "benchmark_run": "test_SPY",
        "pass_fail_rule_created": False, "differences": differences,
    }
    result["pipeline_version"] = 2
    result["test_extension"] = {
        "authorized_run_ids": expected_runs, "period_start": start.isoformat(), "period_end": end.isoformat(),
        "pre_test_metrics_sha256": audit["protected_sha256"][f"data/processed/{EXPERIMENT}/metrics.json"],
        "pre_test_processor_sha256": audit["protected_sha256"]["src/nexus/process_exp001.py"],
        "frozen_metric_module_sha256": metric_hash,
        "calendar_extension": "Existing rules through 2026-10-08, plus 2025-01-09 mourning closure; no change to pre-2025 calendar.",
        "definitions_scope": "Existing definitions remain verbatim for all periods; offline_calendar's original 2015-2024 description refers to Development/Validation, with the Test horizon extended here.",
        "development_validation_csv_sha256": legacy_csv_hashes,
        "development_validation_values_unchanged": True,
        "protocol": "Per experiment record, the held-out Test was opened once after strategy and processing-methodology freeze. This processing uses only the two existing extracted runs.",
    }
    result["source_sha256"].update(before)
    result["integrity"].update(
        no_processed_timestamp_on_or_after_2025_01_01=False,
        sealed_test_not_processed=False,
        no_development_validation_timestamp_on_or_after_2025_01_01=True,
        no_test_new_york_market_date_after_2026_10_08=True,
        authorized_final_test_processed=True,
        development_validation_outputs_unchanged=True,
    )
    # These are stored engine observations, not counterfactual fee-free results.
    costs = {}
    for name in result["metrics"]:
        if name in expected_runs:
            backtest_id = expected_runs[name]
        elif name.startswith("dev_"):
            backtest_id = next(v for k, v in manifest["development"]["backtests"].items() if k[0] == name[-1])
        else:
            backtest_id = manifest["validation"]["candidate_A_backtest" if name == "val_A" else "spy_buy_hold_backtest"]
        statistics = stored_metadata(load_json(raw / f"{name}_metadata.json"), backtest_id)["statistics"]
        costs[name] = {k: statistics.get(k) for k in ("totalFees", "totalDividends", "closedTradeCount", "riskFreeRate")}
    result["stored_transaction_cost_observations"] = costs
    after = {str(p.relative_to(workspace)): sha256(p) for p in source_paths}
    if before != after or legacy_csv_hashes != {f: sha256(output / f) for f in legacy_csv_hashes}:
        raise ValueError("Protected inputs or original CSVs changed")
    for name, content in csvs.items():
        (output / f"{name}_daily.csv").write_text(content, encoding="utf-8", newline="")
    (output / "metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    from src.nexus.report_exp001 import write_report
    write_report(workspace, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = process(args.workspace.resolve())
    for name, m in result["metrics"].items():
        print(f"{name}: {m['daily_row_count']} closes; return={m['total_return']:.6%}; "
              f"Sharpe={m['sharpe']:.6f}; MDD={m['maximum_drawdown']:.6%}")
    print("Development winner:", result["development_selection"]["winner"])


if __name__ == "__main__":
    main()
