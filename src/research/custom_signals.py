"""Immutable local export and explicit, create-only Nexus publication adapter."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math

from src.research.pit_signals import assert_pit, instant, validate_decision


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def export_dataset(directory: Path, *, version: str, name: str, rows: list[dict],
                   source_hashes: dict, methodology: dict, git_sha: str,
                   generated_at: str, diagnostic_only: bool) -> dict:
    if directory.exists():
        raise ValueError("Immutable version already exists")
    if not version or not source_hashes or not git_sha:
        raise ValueError("Version, code revision and source hashes required")
    points = []
    seen = set()
    source_times = []
    for row in rows:
        at = validate_decision(row["decision_timestamp"])
        assert_pit(row, at)
        source_times.extend(instant(c["availableAt"]) for c in row["contributors"])
        if row["value"] is None:
            continue  # Missingness audit is separate; no carry-forward or zero point.
        if not math.isfinite(row["value"]) or not row.get("identity_certified"):
            raise ValueError("Nonfinite value or uncertified identity")
        key = (row["ticker"], at)
        if key in seen:
            raise ValueError("Duplicate asset/decision point")
        seen.add(key)
        iso = at.isoformat().replace("+00:00", "Z")
        points.append({"ticker": row["ticker"], "timestamp": iso, "availableAt": iso, "value": row["value"]})
    points.sort(key=lambda r: (r["timestamp"], r["ticker"]))
    emitted = [p["timestamp"] for p in points]
    manifest = {"dataset_version": version, "name": name, "git_sha": git_sha,
                "generated_at": generated_at, "source_hashes": source_hashes,
                "methodology_sha256": digest(methodology), "row_count": len(points),
                "min_source_availableAt": min(source_times).isoformat() if source_times else None,
                "max_source_availableAt": max(source_times).isoformat() if source_times else None,
                "min_emitted_timestamp": min(emitted) if emitted else None,
                "max_emitted_timestamp": max(emitted) if emitted else None,
                "points_sha256": digest(points), "diagnostic_only": diagnostic_only,
                "production_ready": False, "missing_rows": sum(r["value"] is None for r in rows),
                "point_kind": "disclosed", "missingness_transport_certified": False}
    directory.mkdir(parents=True)
    for filename, value in [("points.json", points), ("audit.json", rows), ("manifest.json", manifest)]:
        (directory / filename).write_bytes(canonical(value) + b"\n")
    return manifest


def publish_new(client, directory: Path, *, authorize: bool = False) -> dict:
    """Explicit create-only operation. Never replace/append a published version.

    Caller must reconcile an uncertain create with the SAME content-derived key.
    Native missing-point carry-forward is unsafe until separately certified.
    """
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    points = json.loads((directory / "points.json").read_text(encoding="utf-8"))
    if not authorize or not points or digest(points) != manifest["points_sha256"]:
        raise ValueError("Publication unauthorized, empty or modified dataset")
    for point in points:
        validate_decision(point["timestamp"])
        validate_decision(point["availableAt"])
    if not manifest["diagnostic_only"] and not manifest["production_ready"]:
        raise ValueError("Production data-quality gates remain unresolved")
    return client.create_custom_indicator({"name": manifest["name"] + " " + manifest["dataset_version"],
                                          "scope": "asset", "point_kind": "disclosed", "points": points,
                                          "description": "Versioned EXP002 PIT audit data; no candidate execution authorized"},
                                         idempotency_key="exp002-custom-" + manifest["points_sha256"])
