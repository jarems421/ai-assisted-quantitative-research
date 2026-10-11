"""Bounded resumable MCP extraction, with raw fields untouched and events first."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from src.research.spec import NY, enforce_range, utc_bounds, stage_window

EVENT_HEADER = re.compile(r"\n\[\d{4}-\d\d-\d\d [^\]]+\] [^\n]+ \(raw\)\n")


def decode_page(response, kind, page):
    if response.get("isError"):
        raise ValueError("MCP response reports an error")
    text = "\n".join(c["text"] for c in response.get("content", []) if c["type"] == "text")
    heading = re.search(r"page (\d+)/(\d+), (\d+) (?:points|matching)", text)
    open_heading = re.search(r"page (\d+)\+, at least (\d+) matching", text)
    if not heading and not open_heading:
        raise ValueError("Unrecognized pagination metadata; do not assume exhaustion")
    if int((heading or open_heading)[1]) != page:
        raise ValueError("Returned page number mismatch")
    if kind == "history":
        rows = []
        for line in text.splitlines():
            if re.match(r"^\d{4}-\d\d-\d\dT", line):
                fields = line.split(", ")
                if len(fields) != 6:
                    raise ValueError("History schema changed")
                rows.append(dict(zip(("time", "value", "cash", "positionValue", "comparisonValue", "reservedCollateral"), fields)))
    else:
        rows = []
        decoder = json.JSONDecoder()
        for chunk in EVENT_HEADER.split(text)[1:]:
            row, _ = decoder.raw_decode(chunk.lstrip())
            rows.append(row)
    more = page < int(heading[2]) if heading else True
    total = int(heading[3]) if heading else None
    if more and not rows:
        raise ValueError("Empty nonterminal page")
    return rows, more, total


def simulated_timestamp(row, kind):
    value = row.get("time") if kind == "history" else row.get("event", {}).get("timestamp", row.get("timestamp"))
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, timezone.utc)
    if not isinstance(value, str):
        raise ValueError("Missing simulated timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp has no timezone")
    return parsed


def extract(store, call, spec, stage, run_id, *, events_required, test_authorized=False, max_pages=100000):
    window = stage_window(spec, stage)
    enforce_range(spec, stage, window["start"], window["end"], test_authorized=test_authorized)
    start, end = utc_bounds(window["start"], window["end"])
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Unsafe run ID")
    summaries = {}
    for kind in (["events", "history"] if events_required else ["history"]):
        pages, times, hashes, declared = [], [], [], None
        for page in range(1, max_pages + 1):
            request = {"backtest_id": run_id, "start_date": start, "end_date": end,
                       "page": page, "page_size": 50 if kind == "events" else 5000}
            if kind == "events":
                request.update(raw=True, include_noise_events=True, include_condition_audit=True, collapse_repeats=False)
            relative = f"{spec['experiment_id']}/{run_id}/{kind}_{page:06}.json"
            if (store.root / relative).exists():
                saved = store.read(relative)
                if saved["request"] != request:
                    raise ValueError("Saved page request mismatch")
            else:
                saved = {"request": request, "response": call(f"query_backtest_{kind}", request)}
                store.write(relative, saved)
            hashes.append(store.write(relative, saved))
            rows, more, total = decode_page(saved["response"], kind, page)
            if total is not None:
                if declared is not None and declared != total:
                    raise ValueError("Pagination total changed during extraction")
                declared = total
            for row in rows:
                timestamp = simulated_timestamp(row, kind)
                if not window["start"] <= timestamp.astimezone(NY).date().isoformat() <= window["end"]:
                    raise ValueError("Simulated observation outside authorized window")
                times.append(timestamp.astimezone(timezone.utc).isoformat())
            pages.append(saved)
            if not more:
                break
        else:
            raise ValueError("Pagination safety ceiling reached before exhaustion")
        if declared is None or declared != len(times):
            raise ValueError("Final declared row count disagrees with extracted rows")
        if events_required and kind == "events" and not times:
            raise ValueError("Required events unavailable; retention/audit unresolved")
        store.write(f"{spec['experiment_id']}/{run_id}/{kind}.json", {"run_id": run_id, "pages": pages})
        summaries[kind] = {"rows": len(times), "pages": len(pages), "minimum_simulated_timestamp": min(times) if times else None,
                           "maximum_simulated_timestamp": max(times) if times else None, "page_hashes": hashes}
    report = {"run_id": run_id, "window": window, "query_utc_window": [start, end], "files": summaries,
              "simulated_dates_within_window": True,
              "administrative_and_corporate_action_dates": "Preserved in raw fields; excluded from simulated date checks",
              "events_requested": events_required}
    store.write(f"{spec['experiment_id']}/{run_id}/integrity.json", report)
    return report
