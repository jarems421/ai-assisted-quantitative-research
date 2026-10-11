"""Local EXP003 identity feasibility and bounded planning; no remote client."""
from collections import Counter, defaultdict
from datetime import date
from itertools import product

CUTOFF = date(2020, 12, 31)
RANGES = {"momentum_lookback_calendar_days": [180, 365],
          "insider_lookback_calendar_days": [30, 90],
          "number_of_holdings": [20, 40]}


def eligible_identity(spans, ticker, day):
    """Require a unique identity AND CS classification at the historical date.

    All types participate in ambiguity detection; current/canonical symbols
    never determine membership. End dates are inclusive.
    """
    day = date.fromisoformat(day)
    if day > CUTOFF:
        raise ValueError("Post-cutoff identity observation")
    active = [s for s in spans if s['ticker'] == ticker
              and date.fromisoformat(s['from_date']) <= day
              <= date.fromisoformat(s['to_date'] or '2020-12-31')]
    if not active or any(not s['security_id'] for s in active):
        return None
    ids = {s['security_id'] for s in active}
    if len(ids) != 1 or any(s['asset_type'] != 'CS' for s in active):
        return None
    return next(iter(ids))


def universe_summary(spans, snapshots):
    """Identity feasibility only: snapshots are aggregates, not daily prices.

    Prior row counts, ADV, cap and threshold flags are deliberately unused.
    This cannot certify completed-bar momentum or joint insider inception.
    """
    by_ticker = defaultdict(list)
    for span in spans:
        by_ticker[span['ticker']].append(span)
    monthly = defaultdict(list)
    for row in snapshots:
        day = date.fromisoformat(row['day'])
        if day > CUTOFF:
            raise ValueError('Post-cutoff price snapshot')
        monthly[row['day'][:7]].append(row)
    totals = Counter()
    annual = defaultdict(set)
    result = []
    ended_ids = {s['security_id'] for s in spans if s['asset_type'] == 'CS'
                 and s['to_date'] and s['to_date'] < '2020-12-31'}
    retained_ended = set()
    for month, rows in sorted(monthly.items()):
        last = max(r['day'] for r in rows)
        counts = Counter()
        candidates = []
        for row in rows:
            if row['day'] != last:
                counts['stale_month_endpoint'] += 1
                continue
            sid = eligible_identity(by_ticker[row['ticker']], row['ticker'], row['day'])
            if sid is None or sid != row['security_id']:
                counts['identity_or_type_exclusion'] += 1
                continue
            candidates.append(sid)
        duplicated = {sid for sid, n in Counter(candidates).items() if n > 1}
        ids = set(candidates) - duplicated
        counts['duplicate_security_exclusion_rows'] = sum(Counter(candidates)[s] for s in duplicated)
        counts['identity_supported_snapshot_ids'] = len(ids)
        retained_ended.update(ids & ended_ids)
        annual[month[:4]].update(ids)
        totals.update(counts)
        result.append({'month': month, 'snapshot_date': last, **dict(counts)})
    return {'status': 'VERIFIED_SCOPED_IDENTITY_FEASIBILITY',
            'source_spans': len(spans), 'source_price_snapshot_rows': len(snapshots),
            'source_types': dict(sorted(Counter(str(s['asset_type']) for s in spans).items())),
            'monthly': result, 'totals': dict(totals),
            'annual_union_ids': {y: len(ids) for y, ids in sorted(annual.items())},
            'retained_ids_with_a_pre_cutoff_ended_CS_span': len(retained_ended),
            'ended_span_warning': 'Ended spans include renames; not a verified delisting count.',
            'joint_development_inception': None,
            'limits': 'Month-end source snapshots only; no daily/session-complete, insider completeness, exchange/OTC, or whole-market coverage certification.'}


def evaluation_plan(folds=4, remote_stresses=3, reserve=20):
    if type(folds) is not int or folds < 1 or remote_stresses < 0 or reserve < 0:
        raise ValueError('Invalid conditional planning count')
    axes = {'momentum_only': ('momentum_lookback_calendar_days', 'number_of_holdings'),
            'insider_only': ('insider_lookback_calendar_days', 'number_of_holdings'),
            'momentum_insider': tuple(RANGES)}
    cells = {family: [dict(zip(names, values)) for values in product(*(RANGES[n] for n in names))]
             for family, names in axes.items()}
    components = {'development_grid_folds': (sum(map(len, cells.values())) + 2) * folds,
                  'selected_family_development_replays': 5,
                  'development_remote_stresses': remote_stresses * 5,
                  'outer_validation': 5, 'eventual_test': 5,
                  'failed_unresolved_reserve': reserve}
    return {'status': 'PROPOSED_NOT_AUTHORIZED', 'family_cells': cells,
            'family_cell_counts': {k: len(v) for k, v in cells.items()},
            'benchmark_count': 2, 'conditional_fold_count': folds,
            'components': components, 'conditional_remote_ceiling': sum(components.values()),
            'local_cost_stress_analyses': 10, 'actual_EXP003_jobs': 0,
            'token_quote': None, 'spend_authorized': False,
            'limits': 'Four folds and two benchmarks are planning assumptions, not approved chronology. Counts require coverage-supported dates and benchmark implementations. No server amplification preview; extra jobs count against reserve or require pre-performance redesign.'}


def main():
    import hashlib
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    directory = root / 'experiments/EXP003'
    provenance = json.loads((directory / 'provenance.json').read_text(encoding='utf-8'))
    sources = provenance['source_artifacts'][:2]
    rows = []
    for source in sources:
        payload = (root / source['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != source['sha256']:
            raise ValueError('Preserved source hash mismatch')
        rows.append(json.loads(payload))
    for name, value in [('research/universe_summary.json', universe_summary(*rows)),
                        ('evaluation_plan.json', evaluation_plan())]:
        (directory / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('EXP003 local identity feasibility and conditional plan reproduced; no Nexus calls.')


if __name__ == '__main__':
    main()
