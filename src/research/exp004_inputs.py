"""Authorized bounded EXP004 source extraction. No strategy submissions."""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from src.research.prepare_exp004 import verify_freeze

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'data/raw/EXP004/production_inputs_v001'


def save(path, value):
    data = (json.dumps(value, indent=2, default=str, allow_nan=False)+'\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Immutable source receipt differs: '+str(path))
    else:
        with path.open('xb') as handle: handle.write(data)


def client_for(directory):
    from nexustrade.client import NexusTradeClient
    settings = {}
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1); settings[k.strip()] = v.strip().strip('"').strip("'")
    client = NexusTradeClient(api_key=settings['NEXUSTRADE_API_KEY'],
                             base_url=settings['NEXUSTRADE_API_BASE_URL'])
    original = client._transport.request
    sequence = len(list(directory.glob('wire_request_*.json')))
    def capture(method, path, **kw):
        nonlocal sequence
        sequence += 1
        save(directory/f'wire_request_{sequence:04d}.json',
             {'method': method, 'path': path, 'body': kw.get('body'),
              'idempotency_key': kw.get('idempotency_key')})
        try: response = original(method, path, **kw)
        except Exception as error:
            save(directory/f'wire_error_{sequence:04d}.json',
                 {'type': type(error).__name__, 'message': str(error)})
            raise
        if not isinstance(response, bytes): save(directory/f'wire_response_{sequence:04d}.json', response)
        return response
    client._transport.request = capture
    return client


def bar_request(start,end):
    if not start or not end or not '2013-12-31'<=start<=end<='2020-12-31':
        raise ValueError('Exact frozen warmup/Development bounds required')
    # Parse dates as well as enforcing bounds; untrusted strings are parameters.
    date.fromisoformat(start); date.fromisoformat(end)
    return {'query': """SELECT o.ticker,CAST(o.date AS DATE) AS day,s.security_id,o.unadjustedClose
        FROM lake.sec_daily_ohlc o JOIN lake.security_segments s ON o.ticker=s.ticker
         AND CAST(o.date AS DATE) BETWEEN s.from_date AND COALESCE(s.to_date,DATE '2020-12-31')
        WHERE CAST(o.date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
         AND s.asset_type='CS' AND s.security_id IS NOT NULL
        ORDER BY s.security_id,o.date""",'params':[start,end]}


def extract(name, request):
    verify_freeze()
    from nexustrade.lake import get, LakeQueryResult
    directory = RAW/name; directory.mkdir(parents=True, exist_ok=True)
    prior_request = directory/'request.json'
    if prior_request.exists():
        stored = json.loads(prior_request.read_text())
        if (stored['params'] != request['params']
                or ' '.join(stored['query'].split()) != ' '.join(request['query'].split())):
            raise ValueError('Changed request requires a new immutable attempt directory')
        request = stored  # Retain exact original body/key on harmless formatting changes.
    save(directory/'request.json', request)
    client = client_for(directory)
    if not (directory/'submission.json').exists():
        if (directory/'intent.json').exists():
            raise ValueError('Uncertain prior submission: reconcile existing ID, never blindly retry')
        key = 'exp004-input-'+hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
        save(directory/'intent.json', {'idempotency_key': key, 'request': request})
        save(directory/'submission.json', client.create_lake_query(request,idempotency_key=key))
    op = json.loads((directory/'submission.json').read_text())
    print('Source query',name,op['id'],flush=True)
    handle = get(op['id'],client=client)
    if not isinstance(handle,LakeQueryResult): handle = handle.wait(timeout_seconds=40)
    save(directory/'result_receipt.json', {'id': handle.id, 'row_count': handle.row_count, 'result': handle.result})
    parts = handle.download(directory/'parts')
    manifest = []
    for part in sorted(parts.glob('part-*.parquet')):
        manifest.append({'path': part.relative_to(ROOT).as_posix(),
                         'sha256': hashlib.sha256(part.read_bytes()).hexdigest(), 'bytes': part.stat().st_size})
    save(directory/'part_hashes.json',manifest)
    print('Downloaded',handle.row_count,'rows',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['bars','splits','metadata'])
    parser.add_argument('--start'); parser.add_argument('--end')
    args=parser.parse_args()
    if args.operation=='bars':
        extract('bars_'+args.start+'_'+args.end,bar_request(args.start,args.end))
    elif args.operation=='splits':
        extract('splits',{'query':"SELECT * FROM lake.stock_splits WHERE CAST(executionDate AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)", 'params':['2013-12-31','2020-12-31']})
    else:
        directory=RAW/'metadata'; directory.mkdir(parents=True,exist_ok=True)
        client=client_for(directory)
        save(directory/'stock_splits.json',client.describe_lake_table('stock_splits'))
