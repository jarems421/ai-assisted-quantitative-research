"""Frozen-cohort source QA acquisition only; respects rolling free-tier quotas."""
from datetime import datetime, timezone
import json
import time

from src.research.phase3c.sources import DOCS, RAW, SourceHTTP, require_cohort, put, secret


def acquire():
    token = secret('TIINGO_API_KEY')
    if not token: raise ValueError('Tiingo token unavailable; value never printed')
    cohort = json.loads((DOCS / 'phase3c_pilot_cohort.json').read_bytes()); require_cohort(cohort)
    plans = []
    for row in cohort['cases']:
        symbol = row['historical_symbol_candidate']
        base = 'https://api.tiingo.com/tiingo/daily/' + symbol
        plans.append((row, base, base + '/prices?startDate=2019-01-01&endDate=2020-12-31'))
    http = SourceHTTP({u for _, a, b in plans for u in (a, b)})
    results = []; headers = {'Authorization': 'Token ' + token, 'Content-Type': 'application/json'}
    for row, metadata, prices in plans:
        entry = {'case_key': row['case_key'], 'cohort_sha256': cohort['cohort_sha256'], 'sources': {}}
        for role, url in [('metadata', metadata), ('prices', prices)]:
            # Persisted rolling request starts, not an assumed per-run allowance.
            while True:
                receipts = [json.loads(p.read_bytes()) for p in (RAW/'attempts/Tiingo').glob('*.json')]
                starts = sorted({datetime.fromisoformat(r['request_started_at_utc']).timestamp() for r in receipts})
                at = datetime.now(timezone.utc).timestamp(); recent = [s for s in starts if s > at - 3600]
                if len([s for s in starts if s > at - 86400]) >= 1000: raise ValueError('Tiingo daily free ceiling')
                if sum(r.get('body', {}).get('bytes', 0) for r in receipts) >= 1024**3: raise ValueError('Tiingo monthly byte ceiling')
                if len(recent) < 50: break
                # Wait in<=60second chunks; orchestration can report progress.
                time.sleep(min(60, max(.5, recent[0] + 3601 - at)))
            try:
                receipt, body = http.fetch('Tiingo', url, headers=headers)
                entry['sources'][role] = receipt
                if receipt['status'] != 200: break
                parsed = json.loads(body)
                if role == 'metadata' and (not isinstance(parsed, dict) or not parsed.get('ticker')):
                    entry['schema_status'] = 'UNAVAILABLE_METADATA_SCHEMA'; break
                if role == 'prices' and not isinstance(parsed, list): entry['schema_status'] = 'UNAVAILABLE_PRICE_SCHEMA'
            except ValueError:
                entry['status'] = 'SOURCE_RETRIEVAL_FAILED'; break
        results.append(entry)
        put(RAW/'tiingo_cases'/ (row['case_key'].replace('|', '_') + '.json'), entry)
        print('Tiingo source cases completed:', len(results), flush=True)
        if (RAW/'Tiingo_stop.json').exists(): break
    put(RAW/'tiingo_summary.json', results)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--execute', action='store_true'); a = p.parse_args()
    if not a.execute: raise ValueError('Explicit source-only acquisition opt-in required')
    acquire()
