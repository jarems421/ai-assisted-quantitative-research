"""Reconcile independent immutable stream uploads; never recreate uncertain IDs."""
import json
from concurrent.futures import ThreadPoolExecutor

from src.research.exp004_inputs import ROOT, save, client_for
from src.research.capabilities import require_remote_enabled
from src.research.exp004_streams import OUT
from src.research.prepare_exp004 import verify_freeze
from src.research.spec import digest


def one(name):
    require_remote_enabled(ROOT, 'EXP004')
    m=json.loads((OUT/'manifest.json').read_bytes());s=m['streams'][name];d=OUT/name
    if (d/'publication.json').exists():return json.loads((d/'publication.json').read_bytes())
    client=client_for(d)
    if not (d/'intent.json').exists():
        points=json.loads((d/'points.json').read_bytes())
        if digest(points)!=s['points_sha256']:raise ValueError('Points changed')
        key='exp004-v002-'+digest({'stream':name,'points':s['points_sha256'],'freeze':m['freeze_specification_sha256']})
        save(d/'intent.json',{'idempotency_key':key,'points_sha256':s['points_sha256']})
        r=client.create_custom_indicator({'name':'EXP004 v002 '+name,'scope':'asset','point_kind':'disclosed',
            'description':'Frozen Development-only decision values; no observations after2020; immutable version',
            'points':points},idempotency_key=key)
    else:
        # Independently recorded create/upload responses establish the actual IDs.
        responses=[json.loads(p.read_bytes()) for p in sorted(d.glob('wire_response_*.json'))]
        indicators=[r['indicator'] for r in responses if 'indicator' in r]
        tickets=[r['ticket'] for r in responses if 'ticket' in r]
        if not indicators:raise ValueError('Uncertain create without ID; no resubmission')
        indicator_id=indicators[0]['customIndicatorId']
        if tickets:
            upload=client.wait_for_custom_indicator_upload(indicator_id,tickets[0]['jobId'],timeout_seconds=40)
            r=dict(client.get_custom_indicator(indicator_id),upload=upload)
        else:r=client.get_custom_indicator(indicator_id)
    if not r.get('ready') or r.get('pointCount')!=s['rows']:
        raise ValueError('Publication not fully validated or row count differs')
    save(d/'publication.json',r)
    print('Validated',name,s['rows'],r['customIndicatorId'],flush=True)
    return r


def remaining():
    require_remote_enabled(ROOT, 'EXP004')
    verify_freeze()
    m=json.loads((OUT/'manifest.json').read_bytes())
    # Separate indicators have no shared mutation state or ordering dependency.
    # The original first upload remains with its original worker; no double polling.
    names=[n for n in m['streams'] if n!='momentum180']
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={n:pool.submit(one,n) for n in names}
        for n,f in futures.items():f.result()


if __name__=='__main__':remaining()
