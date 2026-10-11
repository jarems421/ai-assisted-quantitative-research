"""Specification validation and conservative point-in-time access policy."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
NY = ZoneInfo("America/New_York")
STAGES = ("DRAFT", "HYPOTHESIS_FROZEN", "DEVELOPMENT", "CANDIDATE_FROZEN",
          "VALIDATION", "WALK_FORWARD", "ROBUSTNESS", "TEST_AUTHORIZED",
          "TEST_COMPLETE", "PAPER_AUTHORIZED", "PAPER")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def experiment_id(value):
    if not re.fullmatch(r"EXP[0-9]{3,}", value) or value == "EXP001":
        raise ValueError("Use a new EXP identifier; EXP001 is immutable")
    return value


def validate(spec):
    canonical(spec)  # Reject non-JSON NaN/Infinity before schema comparisons.
    schema = json.loads((ROOT / "experiments/_template/spec.schema.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(spec)
    experiment_id(spec["experiment_id"])
    windows = spec["windows"]
    for name, w in windows.items():
        if w is not None and date.fromisoformat(w["start"]) > date.fromisoformat(w["end"]):
            raise ValueError(f"Reversed {name} window")
    dev, outer, test = (windows[n] for n in ("development", "outer_validation", "test"))
    if dev["end"] >= outer["start"] or test and outer["end"] >= test["start"]:
        raise ValueError("Development, outer Validation, and Test must not overlap")
    inner = windows["inner_validation"]
    if inner and not dev["start"] <= inner["start"] <= inner["end"] <= dev["end"]:
        raise ValueError("Inner Validation must be contained within Development")
    if test and not any(s["start"] <= test["start"] and s["end"] >= test["end"]
                        for s in spec["sealed_ranges"]):
        raise ValueError("Test must be explicitly sealed")
    if spec["research_cutoff"] > dev["end"]:
        raise ValueError("Candidate-formation corpus cutoff cannot exceed Development")
    for source in spec["data_sources"]:
        if not source["point_in_time_verified"] or not source["availability_timestamp"]:
            raise ValueError(f"Point-in-time availability unestablished: {source['name']}")
    if not spec["dynamic_universe"]["point_in_time_verified"]:
        raise ValueError("Universe membership must be point-in-time")
    fees=spec['costs']['fee_contract']
    if set(fees)-{'Stock','Cryptocurrency','Option','OptionSlippageFraction'}:
        raise ValueError('Unknown asset fee contract')
    for asset,contract in fees.items():
        if asset=='OptionSlippageFraction':
            if not isinstance(contract,(int,float)) or not 0<=contract<=1:raise ValueError('Invalid option slippage')
        elif (set(contract)!= {'amount','type'} or contract['type'] not in ('percent','dollars')
              or type(contract['amount']) not in (int,float) or contract['amount']<0):
            raise ValueError('Invalid explicit fee contract')
    if fees.get('Stock',{}).get('type')=='percent' and fees['Stock']['amount']!=spec['costs']['fee_percent']:
        raise ValueError('Stock fee percentage and explicit contract disagree')
    if spec['execution']['requires_events'] and not spec['execution']['event_rationale'].strip():
        raise ValueError('Event-heavy execution requires rationale')
    return spec


def stage_window(spec, stage):
    name = ("development" if stage in ("DRAFT", "HYPOTHESIS_FROZEN", "DEVELOPMENT",
                                      "WALK_FORWARD", "ROBUSTNESS") else
            "outer_validation" if stage in ("CANDIDATE_FROZEN", "VALIDATION") else
            "test" if stage in ("TEST_AUTHORIZED", "TEST_COMPLETE") else None)
    if name is None or spec["windows"][name] is None:
        raise ValueError("No historical data access allowed for this stage")
    return spec["windows"][name]


def enforce_range(spec, stage, start, end, *, test_authorized=False):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    allowed = stage_window(spec, stage)
    if not date.fromisoformat(allowed["start"]) <= start <= end <= date.fromisoformat(allowed["end"]):
        raise ValueError("Requested data crosses the stage's permitted window")
    for sealed in spec["sealed_ranges"]:
        overlaps = start <= date.fromisoformat(sealed["end"]) and end >= date.fromisoformat(sealed["start"])
        if overlaps and not (test_authorized and stage in ("TEST_AUTHORIZED", "TEST_COMPLETE")
                             and spec["windows"]["test"] == sealed):
            raise ValueError("Sealed data access denied")
    return allowed


def utc_bounds(start, end):
    """Closed New York date range, preserving the end-of-session UTC boundary."""
    first = datetime.combine(date.fromisoformat(start), time(), NY)
    last = datetime.combine(date.fromisoformat(end) + timedelta(days=1), time(), NY) - timedelta(milliseconds=1)
    return first.astimezone(timezone.utc).isoformat(), last.astimezone(timezone.utc).isoformat()


def audit_availability(rows, decision_time):
    decision = datetime.fromisoformat(decision_time.replace("Z", "+00:00"))
    if decision.tzinfo is None:
        raise ValueError("Timezone required")
    for row in rows:
        published = datetime.fromisoformat(row["available_at"].replace("Z", "+00:00"))
        if published.tzinfo is None or published > decision:
            raise ValueError("Signal is not known at the decision time")
    return {"rows": len(rows), "usable_at": decision_time}
