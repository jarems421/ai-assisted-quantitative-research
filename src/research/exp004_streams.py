"""Immutable Development-only stream binding for the amended frozen contract."""
import argparse
import hashlib
import json
from datetime import datetime

from src.research.exp004_inputs import ROOT, RAW, save, client_for
from src.research.prepare_exp004 import verify_freeze
from src.research.spec import digest
from src.research.capabilities import require_remote_enabled

OUT = ROOT/'data/raw/EXP004/streams_v002'


def generate():
    f=verify_freeze()
    if f.get('version') != 2: raise ValueError('Amended freeze required')
    panels=[]
    for year in range(2015,2021):
        p=RAW/f'compiled_{year}_v002'
        q=json.loads((p/'qa_summary.json').read_bytes())
        if q['status']!='PASS_LOCAL_NUMERIC':raise ValueError('Input QA incomplete')
        rows=json.loads((p/'decision_inputs.json').read_bytes())
        if hashlib.sha256((p/'decision_inputs.json').read_bytes()).hexdigest()!=q['private_input_sha256']:
            raise ValueError('Numeric inputs changed')
        panels.extend(rows)
    names=('momentum180','momentum365','ordinal180','ordinal365','validity','session','schedule')
    streams={n:[] for n in names};assets=set()
    for p in panels:
        d=p['decision'];day=d['session'];stamp=datetime.fromisoformat(d['decision_utc']).isoformat()+'Z'
        if not '2015-01-02'<=day<='2020-12-31':raise ValueError('Not Development')
        key=int(day.replace('-',''));ids=set(p['ticker_byid'])
        if ids!=set(p['momentum']['180']) or ids!=set(p['momentum']['365']):raise ValueError('Different populations')
        if len(ids)!=len(set(p['ticker_byid'].values())):raise ValueError('Duplicate ticker binding')
        def point(ticker,value):return {'ticker':ticker,'timestamp':stamp,'availableAt':stamp,'value':value}
        for sid,ticker in sorted(p['ticker_byid'].items()):
            assets.add(ticker);streams['validity'].append(point(ticker,1));streams['session'].append(point(ticker,key))
            for h in (180,365):streams[f'momentum{h}'].append(point(ticker,p['momentum'][str(h)][sid]))
        for h in (180,365):
            order=p['ranking'][str(h)]
            for i,sid in enumerate(order):streams[f'ordinal{h}'].append(point(p['ticker_byid'][sid],len(order)-i))
        streams['schedule'].append(point('SPY',key))
    # Missing session keys cannot equal today's full date; carried numeric values
    # therefore cannot revive a removed security. Validity is an additional guard.
    summaries={}
    for name,points in streams.items():
        points.sort(key=lambda r:(r['timestamp'],r['ticker']))
        save(OUT/name/'points.json',points)
        summaries[name]={'rows':len(points),'points_sha256':digest(points),
                         'minimum':min(p['timestamp'] for p in points),'maximum':max(p['timestamp'] for p in points)}
    manifest={'status':'QA_PASSED_READY_TO_PUBLISH','freeze_specification_sha256':f['frozen_specification_sha256'],
              'methodology_sha256':f['frozen_methodology_sha256'],'streams':summaries,
              'historical_ticker_transport_superset':sorted(assets),'decisions':len(panels),
              'missingness':'Omitted current-date keys fail exact-date guard; no zero momentum or broader universe',
              'all_four_cells_and_EW_share_population':True,'generated_by_sha256':hashlib.sha256(__file__.encode()).hexdigest()}
    manifest['generated_by_sha256']=hashlib.sha256(open(__file__,'rb').read()).hexdigest()
    save(OUT/'manifest.json',manifest)
    return manifest


def publish():
    require_remote_enabled(ROOT, 'EXP004')
    m=generate();published={}
    for name,summary in m['streams'].items():
        d=OUT/name;response=d/'publication.json'
        if response.exists():r=json.loads(response.read_bytes())
        else:
            if (d/'intent.json').exists():raise ValueError('Uncertain publication: reconcile original key/ID before retry')
            key='exp004-v002-'+digest({'stream':name,'points':summary['points_sha256'],'freeze':m['freeze_specification_sha256']})
            save(d/'intent.json',{'idempotency_key':key,'points_sha256':summary['points_sha256']})
            client=client_for(d)
            r=client.create_custom_indicator({'name':'EXP004 v002 '+name,'scope':'asset','point_kind':'disclosed',
                'description':'Frozen Development-only decision values; no observations after2020; immutable version',
                'points':json.loads((d/'points.json').read_bytes())},idempotency_key=key)
            save(response,r)
        if not r.get('customIndicatorId'):raise ValueError('Publication ID absent')
        published[name]={'custom_indicator_id':r['customIndicatorId'],**summary}
        print('Published',name,summary['rows'],r['customIndicatorId'],flush=True)
    save(OUT/'published_manifest.json',{'freeze_specification_sha256':m['freeze_specification_sha256'],
                                      'streams':published,'assets':m['historical_ticker_transport_superset']})
    return published


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true')
    args=parser.parse_args();result=publish() if args.publish else generate()
    print(json.dumps({'status':'PUBLISHED' if args.publish else result['status']}))
