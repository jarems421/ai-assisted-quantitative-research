"""Proposed paired inference; pure numerical functions, calibrated synthetically only."""
import math
import numpy as np

from src.research.analysis import holm

BLOCKS = (252, 126, 504)
SEED = 3003001


def aligned(windows):
    if len(windows) != 2: raise ValueError('Two independently funded confirmation windows required')
    pairs = []; previous = None
    for w in windows:
        dates = w['dates']; a = np.asarray(w['strategy'], dtype=float); b = np.asarray(w['control'], dtype=float)
        if len(dates) != len(a) or len(a) != len(b) or len(a) < 504:
            raise ValueError('Incomplete aligned window or too few observations')
        if dates != sorted(set(dates)) or (previous is not None and dates[0] <= previous):
            raise ValueError('Duplicate, unordered or overlapping dates')
        if not np.isfinite(a).all() or not np.isfinite(b).all(): raise ValueError('Invalid/missing NAV-derived input')
        previous = dates[-1]; pairs.append(a - b)
    return pairs


def resampled_means(parts, block, draws, seed):
    """Same noncircular starts for each pair; blocks never cross funding boundaries."""
    if block not in BLOCKS or draws < 100: raise ValueError('Undeclared inference configuration')
    rng = np.random.default_rng(seed); totals = np.zeros(draws)
    for x in parts:
        n = len(x)
        if n < block: raise ValueError('Insufficient block coverage')
        prefix = np.r_[0., np.cumsum(x)]; full, remainder = divmod(n, block)
        starts = rng.integers(0, n - block + 1, size=(draws, full + bool(remainder)))
        totals += (prefix[starts[:, :full] + block] - prefix[starts[:, :full]]).sum(axis=1)
        if remainder:
            s = starts[:, -1]; totals += prefix[s + remainder] - prefix[s]
    return totals / sum(len(x) for x in parts)


def hac_effective(parts, lag):
    if lag not in (252, 504): raise ValueError('Undeclared HAC lag')
    n = sum(len(x) for x in parts); mean = sum(float(x.sum()) for x in parts) / n
    centered = [x - mean for x in parts]
    variance = sum(float(x @ x) for x in centered) / (n - 1)
    lrv = sum(float(x @ x) for x in centered) / n
    for h in range(1, lag + 1):
        if not all(len(x) > h for x in centered): raise ValueError('Inadequate within-window lag pairs')
        gamma = sum(float(x[h:] @ x[:-h]) for x in centered) / n
        lrv += 2 * (1 - h / (lag + 1)) * gamma
    if variance <= 0 or lrv <= 0 or not math.isfinite(lrv):
        return {'lag': lag, 'status': 'UNAVAILABLE_VARIANCE', 'effective_n': None}
    return {'lag': lag, 'status': 'ESTIMATED_NOT_POWER_CERTIFICATE', 'effective_n': min(n, n * variance / lrv),
            'long_run_variance': lrv, 'sample_variance': variance}


def paired_test(windows, *, block=252, draws=10000, seed=SEED):
    parts = aligned(windows); n = sum(len(x) for x in parts)
    observed = sum(float(x.sum()) for x in parts) / n
    if np.var(np.concatenate(parts)) <= 0: raise ValueError('Zero-variance paired difference')
    # Center pooled mean, not each separate mean: retain regime/window contrast.
    null = resampled_means([x - observed for x in parts], block, draws, seed)
    uncentered = resampled_means(parts, block, draws, seed)
    p = (1 + int(np.count_nonzero(null >= observed))) / (draws + 1)
    diagnostics = [hac_effective(parts, lag) for lag in (252, 504)]
    block_counts = [len(x) // 252 for x in parts]
    admissible = min(block_counts) >= 3 and sum(block_counts) >= 6 and all(
        r['effective_n'] is not None and r['effective_n'] >= 20 for r in diagnostics)
    return {'observed_daily_difference': observed, 'annualized_mean_difference': observed * 252,
            'one_sided_null_p': p, 'descriptive_mean_ci_95': (np.quantile(uncentered, [.025, .975]) * 252).tolist(),
            'block': block, 'draws': draws, 'seed': seed, 'annual_block_equivalents': block_counts,
            'hac': diagnostics, 'sample_gate_pass': admissible,
            'certification': 'PROPOSED_METHOD_NOT_CERTIFIED_BY_FUNCTION_SUCCESS'}


def four_effect_family(results):
    expected = {'base', 'double_cost', 'delay1', 'delay5'}
    if set(results) != expected: raise ValueError('Exactly four declared effects, including failures, required')
    values = {}
    for name, result in results.items():
        if result is None or result.get('status') in ('FAILED', 'UNRESOLVED') or not result.get('sample_gate_pass'):
            values[name] = 1.
        else: values[name] = result['one_sided_null_p']
    return holm(values, alpha=.05)


def synthetic_windows(values):
    """Synthetic indexed dates; no market observations, files or experiment state."""
    split = len(values) // 2
    return [{'dates': [f'{i:08d}' for i in range(start, end)], 'strategy': values[start:end].tolist(),
             'control': np.zeros(end - start).tolist()} for start, end in ((0, split), (split, len(values)))]


def calibration(*, replicates=200, draws=10000):
    if replicates < 100 or draws != 10000: raise ValueError('Final calibration protocol requires>=100replicates/10000draws')
    n = 1512; rng = np.random.default_rng(SEED); output = []
    for family in ('iid_null', 'positive', 'negative', 'ar1', 'persistent', 'annual_shock', 'overlap', 'window_shift', 'heteroskedastic'):
        rejections = {b: 0 for b in BLOCKS}; gates = 0; family_rejections = 0
        for rep in range(replicates):
            noise = rng.normal(0, .01, n); values = noise.copy()
            if family in ('ar1', 'persistent'):
                rho = .5 if family == 'ar1' else .98
                for i in range(1, n): values[i] = rho * values[i - 1] + noise[i]
            elif family == 'annual_shock': values += np.repeat(rng.normal(0, .004, 6), 252)
            elif family == 'overlap': values = np.convolve(noise, np.ones(21) / 21, mode='full')[:n]
            elif family == 'window_shift': values += np.r_[np.full(756, -.003), np.full(756, .003)]
            elif family == 'heteroskedastic': values[756:] *= 3
            elif family == 'positive': values += .001
            elif family == 'negative': values -= .001
            results = {b: paired_test(synthetic_windows(values), block=b, draws=draws, seed=SEED + rep) for b in BLOCKS}
            for b in BLOCKS: rejections[b] += results[b]['one_sided_null_p'] <= .05
            result = results[252]; gates += result['sample_gate_pass']
            # Fully correlated four-effect null family; retain failures separately in unit tests.
            adjustment = four_effect_family({k: result for k in ('base', 'double_cost', 'delay1', 'delay5')})
            family_rejections += any(v['reject'] for v in adjustment.values())
        rate = rejections[252] / replicates
        # Wilson95%MonteCarlo interval; preregistered acceptance requires upper<=.10 for each null family.
        z = 1.96; denom = 1 + z*z/replicates
        center = (rate + z*z/(2*replicates))/denom
        half = z * math.sqrt(rate*(1-rate)/replicates + z*z/(4*replicates*replicates))/denom
        output.append({'family': family, 'replicates': replicates, 'draws_per_replication': draws,
                       'rejection_fraction_raw_alpha05': rate, 'wilson95': [center-half, center+half],
                       'block_rejection_fractions': {str(b): rejections[b]/replicates for b in BLOCKS},
                       'fully_correlated_four_effect_holm_any_rejection_fraction': family_rejections/replicates,
                       'sample_gate_pass_fraction': gates/replicates,
                       'null_calibration_pass': center+half <= .10 if family not in ('positive', 'negative') else None})
    null_pass = all(r['null_calibration_pass'] for r in output if r['null_calibration_pass'] is not None)
    return {'protocol': 'phase3c_synthetic_calibration_v002', 'seed': SEED, 'block': 252, 'sensitivity_blocks': [126, 504],
            'null_acceptance_upper_wilson95': .10, 'families': output,
            'verdict': 'PARTIAL' if null_pass else 'BLOCKED',
            'limitations': 'Synthetic calibration only; family calibration covers fully correlated effects, not every joint dependence structure; sensitivity lengths cannot replace failed primary; no real performance input'}
