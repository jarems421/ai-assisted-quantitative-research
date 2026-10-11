"""Fail-closed Development input preparation; never submits remote jobs."""
import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path

from src.research.design_exp004 import price_coverage
from src.research.spec import canonical, digest
from src.research.exp004_policy import momentum, ranked_targets

ROOT = Path(__file__).resolve().parents[2]


def verify_freeze(root=ROOT):
    directory = root/'experiments/EXP004'
    original = json.loads((directory/'freeze_receipt.json').read_text(encoding='utf-8'))
    active = directory/'freeze_versions/v002/receipt.json'
    freeze = json.loads(active.read_bytes()) if active.exists() else original
    if active.exists():
        archive = directory/'freeze_versions/v001'
        for name, expected in original['frozen_artifacts'].items():
            if hashlib.sha256((archive/name).read_bytes()).hexdigest() != expected:
                raise ValueError('Original freeze archive changed: '+name)
        if hashlib.sha256((directory/'freeze_receipt.json').read_bytes()).hexdigest() != freeze['original_receipt_byte_sha256']:
            raise ValueError('Original freeze receipt changed')
    spec = json.loads((directory/'spec.json').read_text(encoding='utf-8'))
    if digest(spec) != freeze['frozen_specification_sha256']:
        raise ValueError('Frozen specification changed')
    for name, expected in freeze['frozen_artifacts'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen methodology changed: '+name)
    if digest(freeze['frozen_artifacts']) != freeze['frozen_methodology_sha256']:
        raise ValueError('Methodology manifest changed')
    return freeze


def check_numeric_input(rows, expected_identities, *, session, prior_session, decision,
                        expected_sessions):
    """No history-count receipt can substitute for a numeric rank input.

    Full immutable bar/split lineage and actual availability instants remain
    mandatory. This gate intentionally rejects incomplete endpoint-only data.
    It is an input gate, not permission to reconstruct an absent source.
    """
    if not rows:
        return {'status': 'FAIL', 'reason': 'MISSING_NUMERIC_PRICE_SPLIT_INPUT',
                'ranking_values': None, 'selected_top_K': None}
    ids = [r.get('security_id') for r in rows]
    if set(ids) != set(expected_identities) or len(ids) != len(set(ids)) or None in ids:
        return {'status': 'FAIL', 'reason': 'INCOMPLETE_OR_DUPLICATE_IDENTITY_PANEL',
                'ranking_values': None, 'selected_top_K': None}
    try:
        prior = date.fromisoformat(prior_session)
        at = datetime.fromisoformat(decision.replace('Z', '+00:00'))
        if session > '2020-12-31' or prior_session >= session or at.tzinfo is None:
            raise ValueError('Invalid completed-session boundary')
        values = {180: {}, 365: {}}
        for r in rows:
            if (r['identity_audited'] is not True or r['ambiguous'] is not False
                    or r['asset_type'] != 'CS' or not r['source_sha256']):
                raise ValueError('Uncertified historical identity/source')
            bars = r['bars']
            days = [b['date'] for b in bars]
            if len(days) != len(set(days)) or set(days) != set(expected_sessions):
                raise ValueError('Missing/duplicate/extra completed sessions')
            for b in bars:
                published = datetime.fromisoformat(b['availableAt'].replace('Z', '+00:00'))
                if (b['date'] > prior_session or published.tzinfo is None or published > at
                        or not math.isfinite(b['unadjustedClose']) or b['unadjustedClose'] <= 0):
                    raise ValueError('Unavailable/future/invalid numeric bar')
            for horizon in values:
                values[horizon][r['security_id']] = momentum(bars, r['splits'], prior, at, horizon)
        return {'status': 'PASS_LOCAL_NUMERIC_QA', 'session': session,
                'ranking_values': values,
                'selected_top_K': {f'M{h}_K{k}': ranked_targets(v, k)
                                   for h, v in values.items() for k in (20, 40)},
                'numeric_source_sha256': digest(rows),
                'boundary': 'Source audit declarations require independently archived evidence; local QA is not vendor-vintage certification.'}
    except (KeyError, TypeError, ValueError):
        return {'status': 'FAIL', 'reason': 'NUMERIC_SOURCE_LINEAGE_OR_ASOF_QA_FAILURE',
                'ranking_values': None, 'selected_top_K': None}


def prepare():
    freeze = verify_freeze()
    if freeze.get('version') == 2:
        # Preserve subsequent runtime dispositions: legacy preparation must not
        # overwrite the amended QA manifest or its publication-failure evidence.
        manifest = json.loads((ROOT/'experiments/EXP004/development_input_manifest.json').read_bytes())
        expected = manifest['input_manifest_sha256']
        if digest({k:v for k,v in manifest.items() if k!='input_manifest_sha256'}) != expected:
            raise ValueError('Amended input manifest changed without its integrity hash')
        return manifest
    coverage = price_coverage()
    decisions = []
    for m in coverage['monthly']:
        decisions.append(dict(m, numeric_momentum_available=False,
                              exact_rank_values=None, selected_K20=None, selected_K40=None,
                              qa_status='FAIL_MISSING_NUMERIC_INPUT', submit_allowed=False))
    plan = json.loads((ROOT/'experiments/EXP004/evaluation_plan.json').read_text(encoding='utf-8'))
    manifest = {'status': 'BLOCKED_INPUT_QA_NO_RUNS_SUBMITTED',
                'frozen_specification_sha256': freeze['frozen_specification_sha256'],
                'frozen_methodology_sha256': freeze['frozen_methodology_sha256'],
                'source_receipts': coverage['source_artifacts'],
                'development': {'start': '2015-01-02', 'end': '2020-12-31'},
                'decisions': decisions, 'folds': plan['folds'],
                'scheduled_fold_jobs': 24, 'actual_jobs': 0, 'run_ids': [],
                'cells': plan['parameter_cells'],
                'affected_runs': 'All four momentum cells and matched equal-weight universe: cannot certify shared numeric-signal eligibility or rankings. SPY withheld to avoid a partial unmatched programme.',
                'qa_failure': 'Existing full-universe receipts contain completed-price counts, identities and endpoints, but no full numeric unadjustedClose/split lineage from which exact 180/365-day momentum can be generated. Bounded AAPL/MSFT and other diagnostic samples cannot replace the frozen universe.',
                'required_input': 'Immutable Development-only nominal completed price bars and effective splits with certified as-of availability, historical stable-ID/ticker mapping and expected-session reconciliation; include pre-2015 warmup only as frozen prerequisites. No 2021+ observations.',
                'cost_boundary': 'Reviewed specification budgets remain zero. Existing priced daily stock backtests estimate zero; this does not establish the cost of additional Lake source extraction or custom publication. No standing EXP002/EXP003 audit allowance carries into EXP004.',
                'operations': {'nexus_calls': 0, 'backtests': 0, 'publications': 0, 'held_out_reads': 0}}
    manifest['input_manifest_sha256'] = digest(manifest)
    path = ROOT/'experiments/EXP004/development_input_manifest.json'
    path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8', newline='\n')
    private = ROOT/'data/raw/EXP004/development_preparation_v001'
    private.mkdir(parents=True, exist_ok=True)
    destination = private/'input_qa_manifest.json'
    encoded = canonical(manifest)
    if destination.exists() and destination.read_bytes() != encoded:
        raise ValueError('Immutable private preparation receipt differs')
    if not destination.exists():
        with destination.open('xb') as handle: handle.write(encoded)
    return manifest


if __name__ == '__main__':
    result = prepare()
    print(json.dumps({'status': result['status'], 'decisions': len(result['decisions']),
                      'actual_jobs': result['actual_jobs'],
                      'input_manifest_sha256': result['input_manifest_sha256']}, indent=2))
