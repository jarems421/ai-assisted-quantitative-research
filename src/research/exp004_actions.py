"""Generic pre-performance corporate-action quality rule; no corrected factors."""
import math
from collections import defaultdict
from datetime import date, timedelta


def classify_groups(rows, identity):
    """Group by historical stable identity/effective day, including noneligible rows.

    Identical economic factors are one adjustment, not sequential legs. Multiple
    distinct factors have no composition evidence in this source declaration.
    Raw rows remain in the immutable source; this is a derived quality ledger.
    """
    groups = defaultdict(list)
    for row in rows:
        day = row['executionDate']
        day = day.date() if hasattr(day, 'date') else date.fromisoformat(str(day)[:10])
        sid = identity(row['ticker'], day.isoformat())
        groups[(sid, None if sid else row['ticker'], day)].append(row)
    result = []
    for (sid, unresolved_ticker, day), legs in groups.items():
        factors = set(); invalid = False
        for r in legs:
            try:
                factor = float(r['splitTo']) / float(r['splitFrom'])
                if not math.isfinite(factor) or factor <= 0: raise ValueError()
                factors.add(factor)
            except (ValueError, TypeError, ZeroDivisionError): invalid = True
        reason = ('INVALID_ADJUSTMENT_OPERAND' if invalid else
                  'DISTINCT_FACTORS_WITHOUT_COMPOSITION_LINEAGE' if len(factors) > 1 else None)
        # Explicit source flags, when present, cannot be made unique by deduplication.
        if any(r.get('revisionUnresolved') is True or r.get('lineageAmbiguous') is True for r in legs):
            reason = 'UNRESOLVED_SOURCE_VERSION_OR_LINEAGE'
        result.append({'security_id': sid, 'tickers_at_event': sorted({r['ticker'] for r in legs}),
                       'effective_date': day.isoformat(), 'distinct_factors': sorted(factors),
                       'source_row_count': len(legs), 'ambiguity_reason': reason,
                       'factor': next(iter(factors)) if reason is None else None,
                       'identity_status': 'RESOLVED_CS' if sid else 'NOT_UNAMBIGUOUS_CS',
                       'first_affected_decision': None, 'last_affected_decision': None,
                       'excluded_security_decisions': 0})
    return sorted(result, key=lambda r: (r['security_id'] or '', r['tickers_at_event'], r['effective_date']))


def crossing(groups, prior):
    """Complete inclusive maximum-horizon quality window, shared by all cells/EW."""
    if isinstance(prior, str): prior = date.fromisoformat(prior)
    start = (prior - timedelta(days=365)).isoformat()
    end = prior.isoformat()
    return [g for g in groups if g['ambiguity_reason'] and start <= g['effective_date'] <= end]
