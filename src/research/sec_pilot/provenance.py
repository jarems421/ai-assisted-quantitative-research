"""Snapshot-pinned eligibility and dated identity; no modeling policy approval."""
from datetime import datetime, timezone
from src.research.sec_pilot.parsing import digest


def instant(value):
    at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if at.tzinfo is None: raise ValueError('Explicit timestamp timezone required')
    return at.astimezone(timezone.utc)


def binding(rows, issuer_cik, decision):
    at = instant(decision)
    valid = [r for r in rows if r.get('issuer_cik') == issuer_cik and r.get('evidence_sha256')
             and r.get('status') == 'VERIFIED' and instant(r['effective_from']) <= at
             and (not r.get('effective_to') or at < instant(r['effective_to']))]
    identities = {(r.get('security_id'), r.get('ticker')) for r in valid}
    if len(identities) != 1 or any(not sid or not ticker for sid, ticker in identities):
        return {'status': 'UNAVAILABLE', 'reason': 'MISSING_OR_AMBIGUOUS_CLASS_IDENTITY'}
    sid, ticker = next(iter(identities))
    return {'status': 'VERIFIED', 'security_id': sid, 'ticker': ticker}


def asof(snapshot, decision, *, snapshot_sha256):
    payload = {k: v for k, v in snapshot.items() if k != 'snapshot_sha256'}
    if digest(payload) != snapshot_sha256 or snapshot.get('snapshot_sha256') != snapshot_sha256:
        raise ValueError('Pinned source snapshot changed')
    at = instant(decision); usable = []; unavailable = []
    for fact in snapshot['facts']:
        reason = None
        public = fact.get('public_available_at_utc')
        bound = fact.get('approved_eligibility_at_utc')
        if fact.get('status') != 'OBSERVED_SOURCE': reason = 'MISSING_OR_AMBIGUOUS_FACT'
        elif not public or fact.get('availability_status') != 'VERIFIED': reason = 'PUBLIC_AVAILABILITY_UNKNOWN'
        elif instant(public) > at: reason = 'FUTURE_SOURCE'
        elif not bound or not fact.get('eligibility_policy_sha256'): reason = 'NO_APPROVED_ELIGIBILITY_POLICY'
        elif instant(bound) < instant(public): reason = 'ELIGIBILITY_PRECEDES_PUBLIC_SOURCE'
        elif instant(bound) > at: reason = 'FUTURE_ELIGIBILITY'
        elif fact.get('identity_status') != 'VERIFIED' or not fact.get('security_id'): reason = 'UNRESOLVED_SECURITY_IDENTITY'
        elif not fact.get('source_sha256'): reason = 'MISSING_SOURCE_LINEAGE'
        if reason: unavailable.append({'fact_locator': fact['fact_locator'], 'reason': reason})
        else: usable.append(fact)
    return {'snapshot_sha256': snapshot_sha256, 'decision_utc': at.isoformat(),
            'usable': usable, 'unavailable': unavailable}
