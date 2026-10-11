"""Locally controlled disclosure reconstruction. No Nexus calls or performance.

Source completeness and historical identity certification are caller evidence,
never inferred from an absence of rows. Missing states stay missing.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from math import isfinite
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
LIMIT = date(2020, 12, 31)


def instant(value: str | datetime) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Explicit timezone required")
    return result.astimezone(timezone.utc)


def decision_for_session(day: date) -> datetime:
    return datetime.combine(day - timedelta(days=1), datetime.min.time(), NY).replace(hour=21)


def validate_decision(value: str | datetime) -> datetime:
    result = instant(value)
    if result.astimezone(NY).date() > LIMIT:
        raise ValueError("Post-cutoff decision")
    return result


def resolve_identity(ticker: str, at: datetime, segments: list[dict]) -> str | None:
    """Caller supplies historical effective spans, never a current symbol map."""
    day = at.astimezone(NY).date().isoformat()
    ids = {r["security_id"] for r in segments if r.get("ticker") == ticker
           and r.get("security_id") and r["start"] <= day <= r["end"]}
    return next(iter(ids)) if len(ids) == 1 else None


def missing(reason: str, **audit) -> dict:
    return {"value": None, "status": "UNAVAILABLE", "reason": reason, "contributors": [], **audit}


def assert_pit(result: dict, decision: datetime) -> None:
    """Core invariant: every contributing version is public by its decision."""
    decision = validate_decision(decision)
    for row in result["contributors"]:
        if instant(row["availableAt"]) > decision:
            raise ValueError("Contributor exceeds decision cutoff")


def insider_score(rows: list[dict], security_id: str, decision: datetime, window_days: int,
                  *, coverage_certified: bool) -> dict:
    decision = validate_decision(decision)
    if window_days not in (30, 90):
        raise ValueError("Undeclared insider window")
    if not coverage_certified:
        return missing("vendor_coverage_not_certified")
    groups = defaultdict(list)
    exclusions = CounterLike()
    for row in rows:
        # Filter future versions before reading their attributes or identities.
        if not row.get("availableAt"):
            return missing("missing_public_availability")
        if instant(row["availableAt"]) > decision:
            continue
        if row.get("security_id") != security_id:
            continue
        if not all(row.get(k) for k in ("eventId", "ownerCik", "versionAccession", "firstAvailableAt")):
            return missing("unresolved_event_or_owner_identity")
        first = instant(row["firstAvailableAt"])
        if not decision - timedelta(days=window_days) < first <= decision:
            continue
        if first > instant(row["availableAt"]):
            return missing("invalid_version_chronology")
        # Future terminal timestamps do not invalidate the prior public state.
        if row.get("supersededAt") and decision >= instant(row["supersededAt"]):
            continue
        if row.get("coverageUnverifiedAt") and decision >= instant(row["coverageUnverifiedAt"]):
            return missing("ambiguous_correction_chain")
        visible_row = dict(row)
        for terminal in ("supersededAt", "coverageUnverifiedAt"):
            if visible_row.get(terminal) and instant(visible_row[terminal]) > decision:
                visible_row[terminal] = None
        groups[(row["eventId"], row["ownerCik"])].append(visible_row)
    qualified = []
    for candidates in groups.values():
        # Identical duplicate legs collapse; conflicting active versions fail.
        unique = {repr(sorted(r.items())): r for r in candidates}
        if len(unique) != 1:
            return missing("ambiguous_active_versions")
        row = next(iter(unique.values()))
        if row.get("rowKind") == "nonderiv" and row.get("transactionCode") == "P" and row.get("acquiredDisposed") == "A" and row.get("shares") is not None and row["shares"] > 0:
            qualified.append(row)
        else:
            exclusions.add("nonqualifying_leg")
    result = {"value": len({r["ownerCik"] for r in qualified}), "status": "USABLE",
              "qualifying_transaction_count": len({r["eventId"] for r in qualified}),
              "contributors": [{"id": r["eventId"], "owner_cik": r["ownerCik"], "version": r["versionAccession"], "availableAt": r["availableAt"]} for r in qualified],
              "exclusions": dict(exclusions), "zero_basis": "certified covered feed with no qualifying public active purchases" if not qualified else None}
    assert_pit(result, decision)
    return result


class CounterLike(dict):
    def add(self, reason):
        self[reason] = self.get(reason, 0) + 1


def quarter_pair(decision: datetime, buffer_days: int = 60) -> tuple[str, str]:
    day = validate_decision(decision).astimezone(NY).date()
    eligible = []
    for year in range(day.year - 2, day.year + 1):
        for month, d in ((3, 31), (6, 30), (9, 30), (12, 31)):
            q = date(year, month, d)
            # The buffer day must have fully ended before eligibility.
            if q + timedelta(days=buffer_days) < day:
                eligible.append(q)
    latest = sorted(eligible)[-2:]
    return latest[0].isoformat(), latest[1].isoformat()


def filing_state(rows: list[dict], decision: datetime) -> dict:
    visible = [r for r in rows if r.get("availableAt") and instant(r["availableAt"]) <= decision]
    visible.sort(key=lambda r: (instant(r["availableAt"]), r.get("accession", "")))
    holdings = None
    contributors = []
    seen = set()
    for row in visible:
        at = instant(row["availableAt"])
        if at in seen or not row.get("complete") or not row.get("identity_certified"):
            raise ValueError("ambiguous_or_incomplete_filing")
        seen.add(at)
        kind = row.get("kind")
        if kind == "ORIGINAL":
            if holdings is not None:
                raise ValueError("multiple_originals")
            holdings = dict(row["holdings"])
        elif kind == "RESTATEMENT" and holdings is not None:
            holdings = dict(row["holdings"])
        elif kind == "NEW HOLDINGS" and holdings is not None and not set(holdings).intersection(row["holdings"]):
            holdings.update(row["holdings"])
        else:
            raise ValueError("unresolved_amendment_chain")
        if any(not isfinite(v) or v < 0 for v in holdings.values()):
            raise ValueError("invalid_position")
        contributors.append({"id": row["accession"], "availableAt": row["availableAt"], "kind": kind})
    if holdings is None:
        raise ValueError("no_public_filing")
    return {"holdings": holdings, "contributors": contributors, "last_public": max(instant(r["availableAt"]) for r in contributors)}


def institutional_score(rows: list[dict], security_id: str, decision: datetime,
                        *, source_certified: bool, minimum_managers: int = 20,
                        minimum_coverage: float = .95) -> dict:
    decision = validate_decision(decision)
    if not source_certified:
        return missing("source_completeness_not_certified")
    prior, current = quarter_pair(decision)
    groups = defaultdict(list)
    for row in rows:
        if not row.get("availableAt"):
            return missing("missing_availability")
        if instant(row["availableAt"]) <= decision and row.get("quarter") in (prior, current):
            if not row.get("manager_cik"):
                return missing("missing_manager_identity")
            groups[(row["manager_cik"], row["quarter"])].append(row)
    # Denominator consists ONLY of managers known publicly in these two quarters.
    managers = sorted({m for m, q in groups})
    excluded = {}
    matched = []
    contributors = []
    score = 0
    stale = []
    for manager in managers:
        try:
            before = filing_state(groups[(manager, prior)], decision)
            after = filing_state(groups[(manager, current)], decision)
        except ValueError as error:
            excluded[manager] = str(error)
            continue
        matched.append(manager)
        score += int(after["holdings"].get(security_id, 0) > 0) - int(before["holdings"].get(security_id, 0) > 0)
        contributors.extend(before["contributors"] + after["contributors"])
        stale.append((decision - after["last_public"]).total_seconds() / 86400)
    coverage = len(matched) / len(managers) if managers else None
    audit = {"quarters": [prior, current], "excluded_managers": excluded, "matched_manager_count": len(matched), "known_manager_count": len(managers), "cohort_coverage": coverage, "maximum_stale_days": max(stale) if stale else None, "amendment_states": [r["kind"] for r in contributors]}
    if len(matched) < minimum_managers or coverage is None or coverage < minimum_coverage:
        return missing("insufficient_matched_cohort", **audit)
    result = {"value": score, "status": "USABLE", "contributors": contributors, **audit}
    assert_pit(result, decision)
    return result
