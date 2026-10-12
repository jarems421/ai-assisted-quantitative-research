"""Offline calendar-only planning probe; creates no policy, signal or approval."""
from datetime import date, datetime, time, timezone

from src.research.sec_pilot.certification import NY, acceptance, proposed_bound


def ambiguity_probe(raw, filed_date, sessions, *, evidence_sha256):
    """Require identical buffered opens under both interpretations, including date rollover.

    Equality demonstrates calendar mechanics, never actual public availability.
    Candidate instants are mapped back into the exchange's seasonal civil clock
    before independently applying the buffer; using the raw date twice would
    conceal near-midnight counterexamples.
    """
    interpretation = acceptance(raw, evidence_sha256=evidence_sha256)
    baseline = proposed_bound(raw, filed_date, sessions)
    candidates = [interpretation[k] for k in
                  ('candidate_eastern_utc', 'candidate_literal_est_utc')]
    bounds = []
    chronology_valid = True
    for candidate in candidates:
        instant = datetime.fromisoformat(candidate)
        civil_date = instant.astimezone(NY).date()
        filed = date.fromisoformat(filed_date)
        chronology_valid = chronology_valid and civil_date <= filed
        # Independent date-buffer calculation must expose rollover even when
        # that candidate contradicts the source filing date. Such a row fails.
        later = sorted(d for d in sessions if d > max(civil_date, filed))
        if len(later) < 2:
            raise ValueError('Calendar coverage insufficient for candidate')
        bounds.append(datetime.combine(later[1], time(9, 30), tzinfo=NY)
                      .astimezone(timezone.utc).isoformat())
    later_than_all = all(datetime.fromisoformat(baseline) > datetime.fromisoformat(c)
                         for c in candidates)
    return {'raw': raw, 'filed_date': filed_date, 'candidate_instants_utc': candidates,
            'raw_rule_bound_utc': baseline, 'candidate_bounds_utc': bounds,
            'calendar_invariant': len(set([baseline, *bounds])) == 1 and later_than_all and chronology_valid,
            'candidate_chronology_valid': chronology_valid,
            'acceptance_status': interpretation['status'],
            'certified_acceptance_utc': interpretation['accepted_at_utc'],
            'public_available_at_utc': None, 'policy_approved': False,
            'interpretation_evidence_sha256': evidence_sha256,
            'scope': 'CALENDAR_MECHANICS_ONLY_NOT_PUBLIC_AVAILABILITY_CERTIFICATION'}
