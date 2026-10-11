"""Local, pre-cutoff filing-coverage diagnostics; never strategy performance.

The retrospective 365-day denominator is a coverage diagnostic only. It must
never be used to decide historical portfolio membership or cohort eligibility.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo
import hashlib
import json

NY = ZoneInfo("America/New_York")
CUTOFF = date(2020, 12, 31)
OFFSETS = (30, 45, 50, 60, 90, 120)


def public_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def asof_versions(rows: list[dict], decision: datetime) -> list[dict]:
    """Filter before reconstruction; later amendments cannot affect this view."""
    if decision.tzinfo is None or decision.astimezone(NY).date() > CUTOFF:
        raise ValueError("A timezone-aware pre-cutoff decision is required")
    if any(not r.get("availableAt") for r in rows):
        raise ValueError("Missing availability is not a usable version")
    return [r for r in rows if public_time(r["availableAt"]) <= decision]


def institutional_state(rows: list[dict], decision: datetime) -> dict:
    """Proposed version mechanics for ONE unambiguously linked manager/quarter.

    Input holdings map stable security IDs to shares; a complete original or
    restatement is required. Real source-chain completeness must be certified
    separately. Unknown amendment types and duplicate public timestamps fail.
    """
    visible = sorted(asof_versions(rows, decision), key=lambda r: public_time(r["availableAt"]))
    state = None
    seen = set()
    for row in visible:
        timestamp = public_time(row["availableAt"])
        if timestamp in seen:
            raise ValueError("Ambiguous same-time filing chain")
        seen.add(timestamp)
        kind = row["kind"]
        if kind in ("ORIGINAL", "RESTATEMENT"):
            if kind == "ORIGINAL" and state is not None:
                raise ValueError("Multiple originals need explicit chain resolution")
            state = dict(row["holdings"])
        elif kind == "NEW HOLDINGS" and state is not None:
            if set(state).intersection(row["holdings"]):
                raise ValueError("Overlapping additions need source reconciliation")
            state.update(row["holdings"])
        else:
            raise ValueError("Unknown amendment or missing original")
    if state is None:
        raise ValueError("No usable public filing; not numerical zero")
    return state


def cohort_coverage(rows: list[dict], *, issuer: bool = False) -> dict:
    groups = defaultdict(dict)
    invalid = 0
    amendments = defaultdict(list)
    for row in rows:
        value = row.get("first_availableAt") if issuer else row.get("availableAt")
        if not value:
            invalid += 1
            continue
        available = public_time(value).astimezone(NY).date()
        if available > CUTOFF:
            raise ValueError("Post-cutoff source observation")
        period = date.fromisoformat(row["periodOfReport"])
        delay = (available - period).days
        if delay < 0 or not row.get("cik"):
            invalid += 1
            continue
        if not issuer and row.get("submissionType") == "13F-HR/A":
            amendments[str(period)].append(delay)
            continue
        if not issuer and row.get("submissionType") != "13F-HR":
            continue
        # Only fully matured coverage cohorts; never pretend Q4 2020 is complete.
        if period > date(2019, 12, 31) or (period.month, period.day) not in ((3, 31), (6, 30), (9, 30), (12, 31)):
            continue
        key = str(period) + (":" + row["ticker"] if issuer else "")
        groups[key][row["cik"]] = min(delay, groups[key].get(row["cik"], delay))
    quarters = []
    for key, managers in sorted(groups.items()):
        denominator = sum(d <= 365 for d in managers.values())
        if not denominator:
            continue
        counts = {str(n): sum(d <= n for d in managers.values()) for n in OFFSETS}
        quarters.append({"cohort": key, "original_managers_public_within_365_days": denominator,
                         "managers_later_than_365_days": sum(d > 365 for d in managers.values()),
                         "counts": counts, "fractions": {n: v / denominator for n, v in counts.items()}})
    summary = {}
    for n in OFFSETS:
        values = [q["fractions"][str(n)] for q in quarters]
        summary[str(n)] = {"minimum": min(values), "median": median(values), "maximum": max(values)} if values else None
    return {"status": "VERIFIED_SOURCE_COVERAGE_ONLY", "denominator": "distinct original managers first public within 365 calendar days; retrospective diagnostic, not an eligibility input",
            "invalid_rows_excluded": invalid, "cohorts": quarters, "offset_summary": summary,
            "amendment_delays": {k: {"count": len(v), "min": min(v), "median": median(v), "max": max(v)} for k, v in sorted(amendments.items())}}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    raw = root / "data/raw/EXP002/audit/raw/revision_20261011"
    files = {"manager": raw / "cohort_filings/rows.json", "issuer": raw / "issuer_cohorts/rows.json"}
    result = {"experiment_id": "EXP002", "cutoff": str(CUTOFF), "uses_performance": False,
              "manager": cohort_coverage(json.loads(files["manager"].read_text(encoding="utf-8"))),
              "issuer_sample": cohort_coverage(json.loads(files["issuer"].read_text(encoding="utf-8")), issuer=True),
              "source_sha256": {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in files.items()}}
    output = root / "experiments/EXP002/research/cohort_summary.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Saved cohort coverage only; no performance or eligibility inferred")


if __name__ == "__main__":
    main()
