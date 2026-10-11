"""Generate an allowlisted support package from existing receipts, offline only."""
import argparse
import hashlib
import json
from pathlib import Path

from src.research.capabilities import ROOT
from src.research.extraction import decode_page


REQUEST_FIELDS = {'tool', 'portfolio', 'args', 'name', 'initialValue', 'cash', 'buyingPower',
                  'strategies', 'condition', 'type', 'conditions', 'lhs', 'rhs', 'comparison',
                  'indicators', 'value', 'action', 'universe', 'source', 'assets', 'symbol',
                  'pipeline', 'customIndicatorId', 'weightIndicator', 'deploymentPercent',
                  'allowShorts', 'orderExecution', 'supportsFractionalShares', 'dividendPolicy',
                  'start_date', 'end_date', 'interval', 'initial_value', 'generate_events',
                  'fee_config', 'Stock', 'amount', 'dividend_policy'}


def allowed_request(value):
    if isinstance(value, dict):
        return {k: allowed_request(v) for k, v in value.items() if k in REQUEST_FIELDS}
    if isinstance(value, list):
        return [allowed_request(v) for v in value]
    return value


def build(root=ROOT):
    root = Path(root)
    audit_path = root/'experiments/EXP004/research/publication_runtime_audit.json'
    audit = json.loads(audit_path.read_bytes())
    for receipt in audit['receipt_index']:
        if hashlib.sha256((root/receipt['path']).read_bytes()).hexdigest() != receipt['sha256']:
            raise ValueError('Existing private receipt hash differs: ' + receipt['path'])
    directory = root/'data/raw/EXP004/streams_v002/transport_execution_diagnostic'
    request = json.loads((directory/'request.json').read_bytes())
    fixture = json.loads((root/'data/raw/EXP004/streams_v002/transport_diagnostic/mcp_response.json').read_bytes())['request']
    page = json.loads((directory/'events_00001.json').read_bytes())
    rows, more, total = decode_page(page['response'], 'events', 1)
    if more or len(rows) != total:
        raise ValueError('Existing diagnostic event page is incomplete')
    observations = []
    def walk(value):
        if isinstance(value, dict):
            if 'dynamicAudit' in value:
                a = value['dynamicAudit']
                observations.append({'universe_size': a['universeSize'],
                                     'passed_symbols': sorted({p[0] for stage in a['pipelineStages'] for p in stage['passedAssets']})})
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(rows)
    requested = [r['symbol'] for r in request['portfolio']['strategies'][0]['action']['universe']['assets']]
    if not observations:
        raise ValueError('No existing dynamic population audit')
    receipts = [{**r} for r in audit['receipt_index'] if r['path'].endswith(('/transport_execution_diagnostic/request.json', '/transport_execution_diagnostic/events_00001.json', '/transport_diagnostic/mcp_response.json'))]
    # Only explicitly allowed fields leave private storage; no raw event objects,
    # account/user IDs, performance summaries, credentials or market bars.
    return {'evidence': 'Derived allowlisted summary; private originals unchanged',
            'audit_sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
            'verified_private_receipts': len(audit['receipt_index']), 'source_receipts': receipts,
            'run_id': audit['transport_diagnostic']['run_id'], 'requested_symbols': requested,
            'runtime_observations': observations, 'event_rows': total, 'event_pages': 1,
            'dataset_promotion_fixture': {key: value for key, value in audit['dataset_promotion_fixture'].items()
                                          if key in ('dataset_id', 'custom_indicator_id', 'ready', 'points', 'result')},
            'synthetic_points': [{key: point[key] for key in ('ticker', 'timestamp', 'availableAt', 'value')} for point in fixture['rows']],
            'uploads': {name: {key: r[key] for key in ('custom_indicator_id', 'upload_job_id', 'total_rows', 'accepted_rows', 'rejected_rows', 'failure_columns')}
                        for name, r in audit['uploads'].items()},
            'synthetic_reproduction_request': allowed_request(request),
            'execution_authorized': False,
            'certification': 'FAIL_POPULATION_PRUNING' if any(o['universe_size'] != len(requested) or set(o['passed_symbols']) != set(requested) for o in observations)
                             else 'UNRESOLVED_ROUTE_NOT_CERTIFIED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT/'docs/acceleration/nexus_support/evidence.json'
    data = (json.dumps(build(), indent=2, sort_keys=True) + '\n').encode()
    if args.check:
        if path.read_bytes() != data: raise ValueError('Support evidence differs; inspect originals before regenerating')
    else:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    print('PASS offline support evidence; zero Nexus calls')


if __name__ == '__main__': main()
