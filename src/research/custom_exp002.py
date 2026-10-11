"""Reproduce bounded EXP002 transport diagnostics locally; never submits jobs.

These are visibility and order-allocation checks, never performance metrics.
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json

from src.research.custom_signals import digest, export_dataset
from src.research.extraction import decode_page, simulated_timestamp
from src.research.pit_signals import NY, instant, decision_for_session, insider_score, institutional_score

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/EXP002/audit/raw/custom_pit_20261011"


def visible_value(points, at):
    eligible = [p for p in points if instant(p["timestamp"]) <= at and instant(p["availableAt"]) <= at]
    if not eligible:
        return None
    latest = max(instant(p["timestamp"]) for p in eligible)
    values = {p["value"] for p in eligible if instant(p["timestamp"]) == latest}
    if len(values) != 1:
        raise ValueError("Ambiguous disclosed point")
    return values.pop()


def runtime_summary(raw=RAW):
    points = json.loads((raw / "artificial_disclosed_v001/points.json").read_text())
    summary = {"kind": "VISIBILITY_AND_ALLOCATION_ONLY", "candidate_performance": False,
               "cutoff": "2020-12-31", "runs": {}, "lag_composition_certified": False}
    for name in ("normal", "holiday", "early", "dst", "deployment"):
        rows = []
        pages = sorted((raw / name).glob("events_*.json"))
        for n, path in enumerate(pages, 1):
            page, more, total = decode_page(json.loads(path.read_text()), "events", n)
            rows.extend(page)
        if not pages or more or len(rows) != total:
            raise ValueError("Incomplete event extraction")
        audits, fills = [], []
        for row in sorted(rows, key=lambda r: simulated_timestamp(r, "events")):
            at = simulated_timestamp(row, "events")
            local = at.astimezone(NY)
            if local.date() > date(2020, 12, 31):
                raise ValueError("Post-cutoff simulated event")
            event = row["event"]
            if event.get("status") == "Filled":
                if (local.hour, local.minute) != (9, 30):
                    raise ValueError("Unexpected fill time")
                fills.append({"asset": event["symbol"], "time": local.isoformat(),
                              "notional": event["quantity"] * event["filledAtPrice"], "fees": event["fees"]})
            if name != "deployment" and (local.hour, local.minute) == (9, 30):
                decision = decision_for_session(local.date())
                for signal in event.get("signals", []):
                    audit = signal.get("audit", {}).get("results", {}).get("0.1")
                    if audit is None:
                        continue
                    mode = "cutoff_lag" if "hours ago" in signal["conditionName"] else "direct"
                    expected_cutoff = visible_value(points, instant(decision))
                    expected_runtime = visible_value(points, at)
                    observed = audit.get("lhsValue") if not audit.get("lhsError") else None
                    audits.append({"session": local.date().isoformat(), "mode": mode,
                                   "decision": decision.isoformat(), "observed": observed,
                                   "error": audit.get("lhsError"), "expected_at_cutoff": expected_cutoff,
                                   "expected_at_runtime": expected_runtime,
                                   "matches_cutoff": observed == expected_cutoff,
                                   "matches_runtime": observed == expected_runtime})
        summary["runs"][name] = {"id": json.loads((raw/name/"submission.json").read_text())["id"],
                                  "event_rows": len(rows), "pages": len(pages), "audits": audits,
                                  "fills": fills, "min_simulated": min(simulated_timestamp(r,"events") for r in rows).isoformat(),
                                  "max_simulated": max(simulated_timestamp(r,"events") for r in rows).isoformat()}
    return summary


def export_unavailable_drafts(raw=RAW, *, git_sha, version="unavailable_v002", generated_at=None):
    """Daily as-of gap ledger, NOT a populated/certified Development dataset.

    Two bounded source-sample tickers only. Calendar days are audit decisions,
    not a trading calendar. Never invent certified zeros from partial extracts.
    """
    source = raw / "owner_sample_short/rows.json"
    original = json.loads(source.read_text())
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    hashes = {"owner_sample_short": __import__("hashlib").sha256(source.read_bytes()).hexdigest()}
    manifests = {}
    for name in ("insider_30", "insider_90", "institutional"):
        rows = []
        day = date(2015, 1, 1)
        while day <= date(2020, 12, 31):
            decision = decision_for_session(day)
            for ticker in ("AAPL", "MSFT"):
                if name.startswith("insider"):
                    row = insider_score(original, ticker, decision, int(name.split("_")[1]), coverage_certified=False)
                else:
                    row = institutional_score([], ticker, decision, source_certified=False)
                row.update(ticker=ticker, identity_certified=False, decision_timestamp=decision.isoformat())
                rows.append(row)
            day += timedelta(days=1)
        directory = raw / (name + "_" + version)
        manifests[name] = export_dataset(directory,version=version,name=name,rows=rows,
                                        source_hashes=hashes,methodology={"purpose":"gap ledger only", "certified":False},
                                        git_sha=git_sha,generated_at=generated_at,diagnostic_only=False)
    return manifests


if __name__ == "__main__":
    result = runtime_summary()
    target = ROOT / "experiments/EXP002/research/custom_runtime_summary.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Local runtime audit reproduced; no Nexus calls or performance metrics")
