"""Local operational controls and identity reconciliation; never call Nexus."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require_remote_enabled(root, experiment):
    """Operational status is separate from immutable scientific stage."""
    path = Path(root) / 'config/operational_pauses.json'
    pauses = json.loads(path.read_bytes()) if path.exists() else {}
    pause = pauses.get(experiment)
    if pause is not None:
        raise ValueError(f'{experiment} operationally paused: {pause["reason"]}')


def reconcile_population(requested, observed, *, complete, binding_verified):
    """Compare exhaustive (stable security ID, historical ticker) bindings.

    Counts, allocations, and post-selection lists cannot certify a population.
    Caller evidence must establish completeness and dated binding independently.
    A passing result is one component of a route certificate, not authorization.
    """
    def bindings(rows):
        result = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('Invalid historical identity record')
            pair = (row.get('security_id'), row.get('ticker'))
            if any(not isinstance(value, str) or not value.strip() for value in pair):
                raise ValueError('Missing historical identity or ticker')
            result.append(pair)
        if (len(result) != len(set(result)) or len(result) != len({p[0] for p in result})
                or len(result) != len({p[1] for p in result})):
            raise ValueError('Duplicate or ambiguous historical identity')
        return set(result)

    expected, actual = bindings(requested), bindings(observed)
    missing, unexpected = sorted(expected - actual), sorted(actual - expected)
    reasons = []
    if complete is not True:
        reasons.append('INCOMPLETE_RUNTIME_POPULATION_EVIDENCE')
    if binding_verified is not True:
        reasons.append('UNVERIFIED_HISTORICAL_BINDING')
    if missing or unexpected:
        reasons.append('POPULATION_MISMATCH')
    return {'status': 'FAIL' if reasons else 'PASS', 'reasons': reasons,
            'requested_count': len(expected), 'observed_count': len(actual),
            'missing': missing, 'unexpected': unexpected}


def require_population(requested, observed, *, complete, binding_verified):
    result = reconcile_population(requested, observed, complete=complete,
                                  binding_verified=binding_verified)
    if result['status'] != 'PASS':
        raise ValueError('Uncertified historical population: ' + json.dumps(result, sort_keys=True))
    return result
