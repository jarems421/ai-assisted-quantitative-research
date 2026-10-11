"""Pre-performance EXP003 policies. No remote calls or production evidence."""
import math
import statistics
from datetime import date

from src.research.pit_signals import instant, insider_score


def coverage_certified(certificate, security_id, decision, days):
    """Absence becomes zero only under an audited, window-complete contract.

    Receiving an event, seeing null coverageUnverifiedAt, or downloading a
    complete SQL result cannot substitute for the issuer/window certificate.
    """
    from datetime import timedelta
    if not certificate:
        return False
    required=('evidence_sha256','identity_evidence_sha256','complete_event_versions',
              'amendments_reconciled','audited','security_id','start','end')
    if not all(certificate.get(k) for k in required):
        return False
    return (certificate['security_id']==security_id
            and instant(certificate['start'])<=instant(decision)-timedelta(days=days)
            and instant(certificate['end'])>=instant(decision))


def certified_insider(rows, security_id, decision, days, certificate=None):
    return insider_score(rows,security_id,decision,days,
                         coverage_certified=coverage_certified(certificate,security_id,decision,days))


def shortfall_allocation(count, target, nominal=95):
    if type(count) is not int or count<0 or target not in (20,40):
        raise ValueError('Invalid declared holding count')
    selected=min(count,target)
    return {'holdings':selected,'nominal_deployment_percent':nominal*selected/target,
            'nominal_percent_per_security':nominal/target if selected else 0,
            'nominal_cash_percent':100-nominal*selected/target,
            'engine_reserve_note':'Targets before the inherited empirical engine reserve; do not claim exact effective fills.'}


def paired_eligibility(evidence):
    """Reject incomplete, misaligned or standalone-Sharpe-only evidence."""
    try:
        folds=evidence['paired_folds']
        if not folds or not evidence['comparison_audited'] or not evidence['critical_rules_pass']:
            return False
        if not evidence['same_control_horizon_holdings'] or not evidence['same_dates_universe_costs']:
            return False
        mean=evidence['pooled_mean_daily_excess']
        sharpe=evidence['pooled_sharpe_difference']
        if any(not math.isfinite(v) for v in (mean,sharpe)) or mean<=0 or sharpe<=0:
            return False
        for f in folds:
            if (f['scheduled_decisions']<=0 or f['participating_decisions']/f['scheduled_decisions']<.90
                    or not math.isfinite(f['mean_daily_excess']) or not math.isfinite(f['sharpe_difference'])):
                return False
        return statistics.median(f['mean_daily_excess'] for f in folds)>0
    except (KeyError,TypeError,ZeroDivisionError):
        return False


def select_composite(cells):
    from itertools import product
    from src.research.design_exp003 import RANGES
    axes=tuple(RANGES)
    expected=set(product(*(RANGES[a] for a in axes)))
    observed=[tuple(c['parameters'][a] for a in axes) for c in cells]
    if len(observed)!=8 or set(observed)!=expected:
        raise ValueError('Complete eight-cell surface, including failures, required')
    eligible=[c for c in cells if paired_eligibility(c)]
    if not eligible:
        return None
    def key(c):
        sensitivity=c['neighbor_mean_effect_dispersion']
        turnover=c['mean_traded_notional_fraction']
        if not all(math.isfinite(x) and x>=0 for x in (sensitivity,turnover)):
            raise ValueError('Complete audited sensitivity/turnover required')
        params=c['parameters']
        return (-statistics.median(f['mean_daily_excess'] for f in c['paired_folds']),
                sensitivity,turnover,params['momentum_lookback_calendar_days'],
                params['insider_lookback_calendar_days'],params['number_of_holdings'])
    return min(eligible,key=key)


def neighbors(parameters):
    from src.research.design_exp003 import RANGES
    if set(parameters)!=set(RANGES) or any(parameters[k] not in RANGES[k] for k in RANGES):
        raise ValueError('Outside fixed grid')
    result=[]
    for axis,values in RANGES.items():
        p=dict(parameters);p[axis]=next(v for v in values if v!=p[axis]);result.append(p)
    return result


def compile_templates():
    """Actual SDK authoring structures, with explicitly unresolved stream IDs.

    SPECIFIC_ASSETS is a historical ticker transport superset, not membership.
    Validity/session-key streams are mandatory for every pipeline candidate.
    No client, remote portfolio creation or backtest is invoked here.
    """
    import nexustrade as nt
    key=nt.CustomIndicator(nt.CANDIDATE,'EXP003_SESSION_KEY_UNPUBLISHED')
    valid=nt.CustomIndicator(nt.CANDIDATE,'EXP003_VALIDITY_UNPUBLISHED')
    rank=nt.CustomIndicator(nt.CANDIDATE,'EXP003_RANK_UNPUBLISHED')
    current=nt.Year()*10000+nt.Month()*100+nt.Date()
    guard=(nt.CurrentTimeHours()==9.5)&(nt.CustomIndicator('SPY','EXP003_SCHEDULE_UNPUBLISHED')==current)
    pipeline=[nt.filter((valid==1)&(key==current)),nt.select_top(rank,20)]
    action=nt.dynamic_rebalance(nt.universe('SPECIFIC_ASSETS',['AAPL','MSFT']),pipeline,nt.Value(1),
                                limit=20,deployment_percent=nt.CustomIndicator('SPY','EXP003_DEPLOYMENT_UNPUBLISHED'),allow_shorts=False)
    momentum=nt.portfolio('EXP003 matched momentum template',[nt.strategy('Monthly exact-session rebalance',guard,action)],
                          initial_value=25000,dividend_policy='cash',supports_fractional_shares=True)._authoring_payload()
    ew=nt.dynamic_rebalance(nt.universe('SPECIFIC_ASSETS',['AAPL','MSFT']),pipeline[:1],nt.Value(1),
                            deployment_percent=nt.Value(95),allow_shorts=False)
    universe=nt.portfolio('EXP003 equal-weight eligible template',[nt.strategy('Monthly exact-session rebalance',guard,ew)],
                         initial_value=25000,dividend_policy='cash',supports_fractional_shares=True)._authoring_payload()
    spy=nt.portfolio('EXP003 explicit SPY buy-and-hold',[
        nt.strategy('First eligible session open only',(nt.CurrentTimeHours()==9.5)&(nt.PositionValue('SPY')<1),
                    nt.buy('SPY',95,'percent of portfolio'))],initial_value=25000,dividend_policy='cash',supports_fractional_shares=True)._authoring_payload()
    return {'status':'SDK_COMPILED_TEMPLATES_NOT_RUNTIME_CERTIFIED','sdk_version':'1.42.0',
            'matched_momentum':momentum,'explicit_SPY':spy,'equal_weight_eligible_universe':universe,
            'fee_contract':{'Stock':{'amount':.1,'type':'percent'}},
            'unresolved':'Historical ticker superset, certified rank/validity/session/schedule/deployment production streams not available. AAPL/MSFT and unpublished IDs are compilation fixtures, never production universe or published IDs.',
            'remote_calls':0}
