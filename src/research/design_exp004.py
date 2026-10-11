"""Reproduce EXP004 price-only design evidence locally; no Nexus client."""
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from src.research.design_exp003 import eligible_identity
from src.research.exp004_policy import cells, compile_templates
from src.research.readiness_exp003 import decisions

ROOT = Path(__file__).resolve().parents[2]


def receipt(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def price_coverage():
    """Project only price/identity fields from existing bounded receipts.

    No ownership fields influence EXP004. Reuse the accepted identity rule
    and completed-history prerequisites; this is not another source audit.
    """
    path = ROOT/'data/raw/EXP002/audit/raw/two_gate_20261011/historical_security_spans/rows.json'
    spans = defaultdict(list)
    for row in json.loads(path.read_bytes()):
        spans[row['ticker']].append(row)
    sources = [receipt(path)]
    monthly = []
    columns = ('session', 'prior_session', 'decision_utc', 'expected_sessions',
               'security_id', 'ticker', 'aliases', 'days_365', 'rows_365', 'first_bar', 'last_bar')
    for year in range(2015, 2021):
        version = 'v003' if year in (2017, 2018) else 'v002'
        path = ROOT/f'data/raw/EXP003/final_readiness_20261011/{year}_{version}/rows.json'
        sources.append(receipt(path))
        grouped = defaultdict(list)
        for original in json.loads(path.read_bytes()):
            row = {k: original[k] for k in columns}
            if row['session'] > '2020-12-31' or row['last_bar'] > row['prior_session']:
                raise ValueError('Receipt exceeds design cutoff or completed endpoint')
            grouped[row['session']].append(row)
        for decision in decisions(year):
            rows = grouped[decision['session']]
            if not rows or len({r['security_id'] for r in rows}) != len(rows):
                raise ValueError('Missing or duplicate decision identity')
            universe = [r for r in rows if r['aliases'] == 1
                        and eligible_identity(spans[r['ticker']], r['ticker'], r['prior_session']) == r['security_id']
                        and eligible_identity(spans[r['ticker']], r['ticker'], r['session']) == r['security_id']]
            valid = [r for r in universe if r['days_365'] == r['expected_sessions'] == decision['expected_365_sessions']
                     and r['rows_365'] == r['days_365'] and r['last_bar'] == r['prior_session']]
            if any(r['prior_session'] != decision['prior_session'] for r in rows):
                raise ValueError('Calendar binding mismatch')
            monthly.append(dict(decision, source_universe_count=len(universe),
                                maximum_horizon_price_prerequisite_count=len(valid),
                                shortfall_K20=len(valid)<20, shortfall_K40=len(valid)<40))
    if len(monthly) != 72 or monthly[0]['session'] != '2015-01-02':
        raise ValueError('Existing price-only inception not supported')
    return {'status': 'VERIFIED_SCOPED_EXISTING_PRICE_PREREQUISITES',
            'development_inception': monthly[0]['session'], 'monthly': monthly,
            'source_artifacts': sources, 'monthly_decisions': len(monthly),
            'source_security_decisions': sum(m['source_universe_count'] for m in monthly),
            'price_prerequisite_security_decisions': sum(m['maximum_horizon_price_prerequisite_count'] for m in monthly),
            'minimum_eligible_prerequisite_count': min(m['maximum_horizon_price_prerequisite_count'] for m in monthly),
            'annual': [{'year': y, 'mean_price_prerequisite_count': statistics.fmean(
                m['maximum_horizon_price_prerequisite_count'] for m in monthly if m['session'].startswith(str(y)))}
                for y in range(2015, 2021)],
            'limits': 'Counts support inception and fixed K20/K40 feasibility, not published numeric momentum, immutable vendor vintages or universal source completeness. Require per-run immutable numeric-input QA before authorized submissions; no ownership eligibility.'}


def evaluation_plan():
    return {'status': 'PREDECLARED_PROPOSAL_NO_RUN_AUTHORIZATION', 'parameter_cells': cells(),
            'folds': [{'train_start': '2015-01-02', 'train_end': f'{y-1}-12-31',
                       'evaluate_start': f'{y}-01-01', 'evaluate_end': f'{y}-12-31'} for y in range(2017, 2021)],
            'independent_runs': {'development_folds': 24, 'full_development_surface_and_benchmarks': 6,
                                 'selected_plus_benchmarks_extra_session_delay': 3,
                                 'outer_validation_selected_plus_benchmarks': 3,
                                 'test_selected_plus_benchmarks': 3, 'failed_unresolved_reserve': 20},
            'future_remote_evaluation_ceiling': 59, 'attempted_exp004_remote_jobs': 0,
            'local_cost_analyses': 12,
            'accounting': 'Four fixed cells plus two benchmarks per fold, four folds; six full Development replays. Three chosen-strategy/benchmark delayed runs, three outer, three owner-opened Test. No fitted model or hidden training jobs. Any retry/internal amplification consumes reserve or requires redesign before performance. Local 10/20bps stresses on six full-Development fill tapes are not new remote evaluations.',
            'pricing': {'nominal_daily_nonoptions_rate': 0, 'source': 'config/research_pricing.json',
                        'actual_account_debit': None, 'execution_authorized': False,
                        'requirement': 'Revalidate dated price metadata, per-run plans and account limits before separately authorized execution. No optimizer/sweep/walk-forward submission.'}}


def main():
    directory = ROOT/'experiments/EXP004'
    directory.mkdir(parents=True, exist_ok=True)
    for relative, value in [('research/price_coverage.json', price_coverage()),
                            ('evaluation_plan.json', evaluation_plan()),
                            ('compiled_templates.json', compile_templates())]:
        path = directory/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
