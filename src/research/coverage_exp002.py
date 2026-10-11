"""Local EXP002 source-coverage diagnostics; never performance or native PIT proof."""
from __future__ import annotations

import bisect
import calendar
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

CUTOFF = date(2020, 12, 31)
NY = ZoneInfo("America/New_York")


def timestamp(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result


def summarize(prices, ownership, spans):
    """Count source presence separately from usable, revision-safe native signals."""
    by_ticker = defaultdict(list)
    for span in spans:
        lo, hi = (date.fromisoformat(span[k]) for k in
                  ("bounded_from_date", "bounded_to_date"))
        if hi > CUTOFF or lo > hi:
            raise ValueError("Invalid/cross-cutoff security span")
        by_ticker[span["ticker"]].append((lo, hi, span["security_id"]))
    source = defaultdict(list)
    issues = Counter()
    for row in ownership:
        available = timestamp(row["last_availableAt"])
        if available.date() > CUTOFF:
            raise ValueError("Post-cutoff ownership observation")
        local_day = available.astimezone(NY).date()
        identities = {sid for lo, hi, sid in by_ticker[row["ticker"]]
                      if lo <= local_day <= hi and sid}
        if len(identities) != 1:
            issues["unresolved_or_ambiguous_ownership_identity_rows"] += 1
            continue
        source[(row["dataset"], next(iter(identities)))].append(available)
    for dates in source.values():
        dates.sort()
    grouped = defaultdict(list)
    for row in prices:
        day = date.fromisoformat(row["day"])
        if day > CUTOFF:
            raise ValueError("Post-cutoff price observation")
        if day >= date(2015, 1, 1):
            grouped[(day.year, day.month)].append(row)
    yearly = defaultdict(lambda: defaultdict(set))
    monthly = []
    for (year, month), rows in sorted(grouped.items()):
        last = max(row["day"] for row in rows)
        decision = datetime(year, month, calendar.monthrange(year, month)[1],
                            23, 59, 59, 999000, tzinfo=NY).astimezone(timezone.utc)
        active = [row for row in rows if row["day"] == last]
        issues["excluded_earlier_last_price_security_months"] += len(rows) - len(active)
        identities = [row["security_id"] for row in active]
        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate security in monthly price snapshot")
        counts = Counter()
        for row in active:
            sid = row["security_id"]
            counts["common_stock_price_ids"] += 1
            yearly[year]["common_stock_price_ids"].add(sid)
            flags = {
                "market_cap_present_ids": bool(row["cap_present"]),
                "cap_lineage_ids": bool(row["cap_lineage"]),
                "sufficient_252_price_bars_ids": row["prior_price_bars"] == 252,
                "sufficient_20_volume_bars_ids": row["prior_volume_bars"] == 20,
            }
            liquid = bool(row["price_threshold"] and flags["sufficient_252_price_bars_ids"]
                          and flags["sufficient_20_volume_bars_ids"]
                          and row["proposed_adv"] is not None
                          and row["proposed_adv"] >= 10_000_000)
            flags["proposed_price_liquid_ids"] = liquid
            flags["proposed_cap_filtered_ids"] = bool(liquid and row["cap_threshold"]
                                                      and row["cap_lineage"])
            for dataset, window in (("insider", 90), ("institutional", 365)):
                dates = source.get((dataset, sid), [])
                index = bisect.bisect_right(dates, decision) - 1
                flags[dataset + "_source_presence_ids"] = bool(
                    index >= 0 and (decision - dates[index]).total_seconds() <= window * 86400)
            both = flags["insider_source_presence_ids"] and flags["institutional_source_presence_ids"]
            flags["proposed_liquid_insider_source_presence_ids"] = bool(
                liquid and flags["insider_source_presence_ids"])
            flags["proposed_liquid_institutional_source_presence_ids"] = bool(
                liquid and flags["institutional_source_presence_ids"])
            flags["joint_source_presence_ids"] = bool(
                both and row["cap_present"] and flags["sufficient_252_price_bars_ids"]
                and flags["sufficient_20_volume_bars_ids"])
            flags["proposed_liquid_joint_source_presence_ids"] = bool(liquid and both)
            for field, present in flags.items():
                if present:
                    counts[field] += 1
                    yearly[year][field].add(sid)
        denominator = counts["common_stock_price_ids"]
        monthly.append({"year": year, "month": month, "last_price_date": last,
                        "availability_decision_time": decision.isoformat(),
                        "source_counts": dict(counts),
                        "source_presence_percentages": {
                            k: 100 * counts[k] / denominator for k in
                            ("insider_source_presence_ids", "institutional_source_presence_ids",
                             "joint_source_presence_ids")},
                        "proposed_liquid_source_presence_percentages": {
                            k: 100 * counts[k] / counts["proposed_price_liquid_ids"]
                            if counts["proposed_price_liquid_ids"] else None for k in
                            ("proposed_liquid_insider_source_presence_ids",
                             "proposed_liquid_institutional_source_presence_ids",
                             "proposed_liquid_joint_source_presence_ids")},
                        "verified_usable_joint_count": None})
    annual = []
    for year, sets in sorted(yearly.items()):
        counts = {key: len(value) for key, value in sets.items()}
        denominator = counts["common_stock_price_ids"]
        annual.append({"year": year, "annual_union_of_month_end_ids": counts,
                       "source_presence_percentages": {
                           k: 100 * counts.get(k, 0) / denominator for k in
                           ("insider_source_presence_ids", "institutional_source_presence_ids",
                            "joint_source_presence_ids")},
                       "proposed_liquid_source_presence_percentages": {
                           k: 100 * counts.get(k, 0) / counts["proposed_price_liquid_ids"]
                           if counts.get("proposed_price_liquid_ids") else None for k in
                           ("proposed_liquid_insider_source_presence_ids",
                            "proposed_liquid_institutional_source_presence_ids",
                            "proposed_liquid_joint_source_presence_ids")},
                       "verified_usable_joint_count": None})
    return {"yearly_coverage": annual, "monthly_coverage": monthly,
            "identity_and_snapshot_issues": dict(issues)}


def main():
    root = Path(__file__).resolve().parents[2]
    raw = root / "data/raw/EXP002/audit/raw/runtime_20261011"
    read = lambda path: json.loads((raw / path).read_text(encoding="utf-8"))
    result = summarize(read("price_panel_unadjusted/rows.json"),
                       read("ownership_equity_panel/rows.json"), read("security_spans/rows.json"))
    summary_path = root / "experiments/EXP002/research/coverage_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(result)
    summary["identity_policy"] = "Unique security segment at disclosure's New York availability date; ambiguous/unresolved mappings excluded, ticker renames joined by stable ID."
    summary["source_presence_warning"] = "Nonderivative insider legs and SH non-option institutional rows only. Any row is not complete native coverage, revision safety or a genuine zero. Calendar month-end availability is used; ownership history starts in 2015, so early rolling windows are left-censored. UTC cutoff conservatively excludes December 31 NY end-of-day filings represented on January 1 UTC."
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
