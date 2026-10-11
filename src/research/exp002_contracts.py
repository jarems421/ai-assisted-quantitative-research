"""EXP002 source normalization and precomputed decision transport contracts.

No network access. Certification covers declared source semantics, not perfect
vendor completeness or immutable historical database vintages.
"""
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite, prod
from src.research.pit_signals import NY, LIMIT, instant, validate_decision, decision_for_session


def sec_filing_availability(value, filing_date):
    """Certify naive UTC by matching the documented New York filing-date EOD.

    Never attach UTC to an arbitrary naive timestamp merely because it parses.
    """
    day = date.fromisoformat(str(filing_date)[:10])
    expected = datetime.combine(day+timedelta(days=1), time(), NY).astimezone(timezone.utc)-timedelta(milliseconds=1)
    observed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if observed.tzinfo is None:
        if observed != expected.replace(tzinfo=None):
            raise ValueError("Source timestamp does not certify naive UTC")
        observed = observed.replace(tzinfo=timezone.utc)
    if observed.astimezone(timezone.utc) != expected:
        raise ValueError("Source availability does not match filing-date EOD")
    return expected


def session_key(day):
    return int(day.strftime("%Y%m%d"))


def decision_points(day, value, *, valid):
    """Atomic sidecar bundle. Numeric missingness is NEVER a zero alpha value."""
    if day > LIMIT:
        raise ValueError("Post-cutoff execution session")
    at = validate_decision(decision_for_session(day)).isoformat()
    result = {"validity": {"timestamp": at, "availableAt": at, "value": int(valid)},
              "session_key": {"timestamp": at, "availableAt": at, "value": session_key(day)}}
    if valid:
        if value is None or not isfinite(value):
            raise ValueError("Valid decision requires finite numeric signal")
        result["signal"] = {"timestamp": at, "availableAt": at, "value": value}
    return result


def execution_signal(day, value, validity, freshness):
    """Mirror the audited native quality==1 and YYYYMMDD freshness guard."""
    if validity != 1 or freshness != session_key(day):
        return None
    if value is None or not isfinite(value):
        return None
    return value


def native_decision_condition(sdk, asset, signal_id, validity_id, session_id):
    """The native composition verified in artificial monthly event traces.

    SDK injected explicitly. Builds declarations only; performs no remote call.
    """
    value = sdk.CustomIndicator(asset, signal_id)
    valid = sdk.CustomIndicator(asset, validity_id)
    key = sdk.CustomIndicator(asset, session_id)
    return ((sdk.CurrentTimeHours() == 9.5) & (valid == 1)
            & (key == (sdk.Year()*10000 + sdk.Month()*100 + sdk.Date()))
            & (value >= -1e30))


def split_safe_ratio(prior_nominal, current_nominal, prior_day, current_day, splits):
    """Momentum price ratio using ONLY splits effective within completed bars.

    No future split/dividend back-adjustment; cash dividends are not alpha price
    points and are never added to this price ratio.
    """
    if not 0 < prior_nominal < float("inf") or not 0 < current_nominal < float("inf") or prior_day >= current_day:
        raise ValueError("Positive nominal prices and chronological sessions required")
    factors = []
    for row in splits:
        when = date.fromisoformat(str(row["executionDate"])[:10])
        if prior_day < when <= current_day:
            before, after = row["splitFrom"], row["splitTo"]
            if not isfinite(before) or not isfinite(after) or before <= 0 or after <= 0:
                raise ValueError("Invalid effective split")
            factors.append(after/before)
    return current_nominal * prod(factors) / prior_nominal
