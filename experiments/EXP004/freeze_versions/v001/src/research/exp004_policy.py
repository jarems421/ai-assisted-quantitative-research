"""Frozen-candidate proposal for price-only EXP004; local declarations only."""
import math
import statistics
from datetime import date, datetime, timedelta
from itertools import product

from src.research.exp002_contracts import split_safe_ratio

RANGES = {'momentum_lookback_calendar_days': [180, 365], 'number_of_holdings': [20, 40]}
FOLD_YEARS = (2017, 2018, 2019, 2020)


def cells():
    return [dict(zip(RANGES, values)) for values in product(*RANGES.values())]


def momentum(bars, splits, prior_session, decision, horizon):
    """Completed nominal bars, locally adjusted only for effective splits.

    Caller supplies one audited security identity. Unknown availability is an
    error, not an invented timestamp. This design implementation is not a
    generated production panel. Dividends remain cash, outside price momentum.
    """
    if horizon not in (180, 365) or decision.tzinfo is None:
        raise ValueError('Declared horizon and timezone-aware decision required')
    if prior_session > date(2020, 12, 31) or decision.date() > date(2020, 12, 31):
        raise ValueError('Design implementation is Development bounded')
    boundary = prior_session - timedelta(days=horizon)
    usable = []
    for b in bars:
        day = date.fromisoformat(b['date'])
        at = datetime.fromisoformat(b['availableAt'].replace('Z', '+00:00'))
        if at.tzinfo is None:
            raise ValueError('Unknown price availability timezone')
        if boundary <= day <= prior_session and at <= decision:
            usable.append(b)
    usable.sort(key=lambda b: b['date'])
    if not usable or usable[-1]['date'] != prior_session.isoformat():
        raise ValueError('Missing completed endpoint')
    if len({b['date'] for b in usable}) != len(usable):
        raise ValueError('Duplicate completed price sessions')
    known_splits = []
    for s in splits:
        if s['executionDate'] > prior_session.isoformat():
            continue
        at = datetime.fromisoformat(s['availableAt'].replace('Z', '+00:00'))
        if at.tzinfo is None or at > decision:
            raise ValueError('Effective split not certified available at decision')
        known_splits.append(s)
    return split_safe_ratio(usable[0]['unadjustedClose'], usable[-1]['unadjustedClose'],
                           date.fromisoformat(usable[0]['date']), prior_session, known_splits) - 1


def ranked_targets(values, holdings):
    """Stable-ID ties; no increase in deployment when holdings are short."""
    if holdings not in (20, 40) or any(not math.isfinite(v) for v in values.values()):
        raise ValueError('Invalid grid or numeric momentum')
    chosen = sorted(values, key=lambda security: (-values[security], security))[:holdings]
    return {security: 95 / holdings for security in chosen}


def paired_eligibility(evidence):
    try:
        folds = evidence['paired_folds']
        if ([f['year'] for f in folds] != list(FOLD_YEARS)
                or evidence['primary_benchmark'] != 'equal_weight_eligible_universe'
                or not all(evidence[k] is True for k in
                           ('comparison_audited', 'critical_rules_pass', 'same_dates_universe_costs'))):
            return False
        effects = [evidence['pooled_mean_daily_excess'], evidence['pooled_sharpe_difference']]
        if any(not math.isfinite(v) or v <= 0 for v in effects):
            return False
        for f in folds:
            scheduled, participated = f['scheduled_decisions'], f['participating_decisions']
            if (type(scheduled) is not int or type(participated) is not int
                    or not 0 <= participated <= scheduled or scheduled <= 0
                    or participated / scheduled < .90
                    or not all(math.isfinite(f[k]) for k in ('mean_daily_excess', 'sharpe_difference'))):
                return False
        return (statistics.median(f['mean_daily_excess'] for f in folds) > 0
                and sum(f['mean_daily_excess'] > 0 for f in folds) >= 3)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def neighbors(parameters):
    if parameters not in cells():
        raise ValueError('Outside four-cell surface')
    return [p for p in cells() if sum(p[k] != parameters[k] for k in RANGES) == 1]


def select(candidates):
    observed = [c['parameters'] for c in candidates]
    if len(observed) != 4 or any(observed.count(p) != 1 for p in cells()):
        raise ValueError('Complete four-cell surface including failures required')
    eligible = [c for c in candidates if paired_eligibility(c)]
    if not eligible:
        return None
    def key(c):
        adjacent = [n for n in candidates if n['parameters'] in neighbors(c['parameters'])]
        # Missing/failed neighbors imply unknown sensitivity. They never get
        # an artificial zero dispersion or favorable sensitivity tie-break.
        values = [n.get('pooled_mean_daily_excess') for n in adjacent]
        sensitivity = (statistics.pstdev(values) if all(
            isinstance(v, (int, float)) and math.isfinite(v) for v in values) else math.inf)
        turnover = c['mean_traded_notional_fraction']
        if not math.isfinite(turnover) or turnover < 0:
            raise ValueError('Audited nonnegative turnover required')
        p = c['parameters']
        return (-statistics.median(f['mean_daily_excess'] for f in c['paired_folds']),
                sensitivity, turnover, p['momentum_lookback_calendar_days'], p['number_of_holdings'])
    return min(eligible, key=key)


def compile_templates():
    """SDK-only binding check. Fixture symbols/IDs cannot be submitted."""
    import nexustrade as nt
    current = nt.Year()*10000 + nt.Month()*100 + nt.Date()
    key = nt.CustomIndicator(nt.CANDIDATE, 'EXP004_SESSION_UNPUBLISHED')
    valid = nt.CustomIndicator(nt.CANDIDATE, 'EXP004_VALIDITY_UNPUBLISHED')
    score = nt.CustomIndicator(nt.CANDIDATE, 'EXP004_MOMENTUM_UNPUBLISHED')
    order = nt.CustomIndicator(nt.CANDIDATE, 'EXP004_STABLE_ORDER_UNPUBLISHED')
    guard = ((nt.CurrentTimeHours() == 9.5)
             & (nt.CustomIndicator('SPY', 'EXP004_SCHEDULE_UNPUBLISHED') == current))
    base = [nt.filter((valid == 1) & (key == current) & (score >= -1e30))]
    universe = nt.universe('SPECIFIC_ASSETS', ['AAPL', 'MSFT'])
    def portfolio(name, action):
        return nt.portfolio(name, [nt.strategy('Exact monthly session open', guard, action)],
                            initial_value=25000, dividend_policy='cash',
                            supports_fractional_shares=True)._authoring_payload()
    candidates = []
    for p in cells():
        # Stable order is locally computed from momentum descending then ID;
        # selecting this integer removes unspecified native tie ordering.
        action = nt.dynamic_rebalance(universe, base + [nt.select_top(order, p['number_of_holdings'])],
                                      nt.Value(1), limit=p['number_of_holdings'], allow_shorts=False,
                                      deployment_percent=nt.CustomIndicator('SPY', 'EXP004_DEPLOYMENT_UNPUBLISHED'))
        candidates.append({'parameters': p, 'portfolio': portfolio('EXP004 momentum template', action)})
    ew = portfolio('EXP004 equal-weight eligible universe', nt.dynamic_rebalance(
        universe, base, nt.Value(1), deployment_percent=nt.Value(95), allow_shorts=False))
    # Exact inception key prevents rejected initial orders silently entering
    # on a later day. A failure is logged; not an automatic retry.
    spy_guard = ((nt.CurrentTimeHours() == 9.5) & (current == 20150102)
                 & (nt.PositionValue('SPY') < 1))
    spy = nt.portfolio('EXP004 explicit SPY buy-and-hold', [nt.strategy(
        'Permitted inception open', spy_guard, nt.buy('SPY', 95, 'percent of portfolio'))],
        initial_value=25000, dividend_policy='cash', supports_fractional_shares=True)._authoring_payload()
    return {'status': 'SDK_COMPILED_FIXTURES_NOT_EXECUTABLE', 'remote_calls': 0,
            'candidates': candidates, 'equal_weight_eligible_universe': ew, 'explicit_SPY': spy,
            'fee_contract': {'Stock': {'amount': .1, 'type': 'percent'}},
            'binding_contract': 'Each run substitutes its permitted inception key; binds its own immutable momentum, stable-order, validity, full-session-key, monthly schedule and shortfall-deployment streams. Fixture assets are replaced with historical ticker transport superset, never membership. The same maximum-365-day eligible population applies to both horizons and EW. No source omissions become numeric zero. Reject any unpublished IDs before submission.'}
