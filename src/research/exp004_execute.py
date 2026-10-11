"""Exact frozen Development bindings and durable independent-job submission."""
import argparse
import importlib
import json
from pathlib import Path

from src.research.exp004_inputs import ROOT, save, client_for
from src.research.exp004_streams import OUT
from src.research.prepare_exp004 import verify_freeze
from src.research.nexus import Jobs, SDK
from src.research.spec import digest
from src.research.store import Store

RUNS = ROOT/'data/raw/EXP004/development_v002'
NAMES = ('M180_K20','M180_K40','M365_K20','M365_K40','EW','SPY')


def binding(name, start, end):
    import nexustrade as nt
    if name not in NAMES or not '2015-01-02'<=start<=end<='2020-12-31':
        raise ValueError('Frozen Development cells/range only')
    m=json.loads((OUT/'published_manifest.json').read_bytes());f=verify_freeze()
    if m.get('runtime_population_preservation_certified') is not True:
        raise ValueError('Historical universe transport is not certified; native symbol pruning is prohibited')
    if m['freeze_specification_sha256']!=f['frozen_specification_sha256']:raise ValueError('Publication uses another freeze')
    ids={n:s['custom_indicator_id'] for n,s in m['streams'].items()}
    current=nt.Year()*10000+nt.Month()*100+nt.Date()
    # All run inception dates are audited first trading sessions.
    guard=(nt.CurrentTimeHours()==9.5)&(nt.CustomIndicator('SPY',ids['schedule'])==current)
    if name=='SPY':
        guard=(nt.CurrentTimeHours()==9.5)&(current==int(start.replace('-','')))&(nt.PositionValue('SPY')<1)
        action=nt.buy('SPY',95,'percent of portfolio')
    else:
        h=int(name.split('_')[0][1:]) if name!='EW' else 180
        valid=nt.CustomIndicator(nt.CANDIDATE,ids['validity'])
        key=nt.CustomIndicator(nt.CANDIDATE,ids['session'])
        score=nt.CustomIndicator(nt.CANDIDATE,ids[f'momentum{h}'])
        pipeline=[nt.filter((valid==1)&(key==current)&(score>=-1e30))]
        options={'deployment_percent':nt.Value(95),'allow_shorts':False}
        if name!='EW':
            k=int(name.split('_')[1][1:]);options['limit']=k
            pipeline.append(nt.select_top(nt.CustomIndicator(nt.CANDIDATE,ids[f'ordinal{h}']),k))
        action=nt.dynamic_rebalance(nt.universe('SPECIFIC_ASSETS',m['assets']),pipeline,nt.Value(1),**options)
    return nt.portfolio('EXP004 '+name+' '+start+' '+end,
                        [nt.strategy('Frozen monthly session-open evaluation',guard,action)],
                        initial_value=25000,dividend_policy='cash',supports_fractional_shares=True)._authoring_payload()


def submit(name,year):
    f=verify_freeze();directory=ROOT/'experiments/EXP004'
    if year not in (2017,2018,2019,2020,0):raise ValueError('Frozen folds/full Development only')
    from src.research.exp004_compile import calendar
    days=[d.isoformat() for d in calendar() if d.year==year] if year else []
    start=days[0] if year else '2015-01-02';end=f'{year}-12-31' if year else '2020-12-31'
    label=f'{name}_'+(str(year) if year else 'full')
    d=RUNS/label;d.mkdir(parents=True,exist_ok=True)
    spec=json.loads((directory/'spec.json').read_bytes())
    portfolio=binding(name,start,end)
    payload=importlib.import_module('nexustrade.portfolio').backtest(portfolio,
              start_date=start,end_date=end,interval='Day',initial_value=25000,generate_events=True,
              fee_config=spec['costs']['fee_contract'],dividend_policy='cash')
    save(d/'compiled_payload.json',payload)
    pricing=json.loads((ROOT/'config/research_pricing.json').read_bytes());pricing['max_evaluations']=59
    store=Store(ROOT)
    try:
        state=store.verify(spec)
        if state['stage']=='HYPOTHESIS_FROZEN':store.transition(spec,'DEVELOPMENT')
        if store.state('EXP004')['stage']!='DEVELOPMENT':raise ValueError('Development stage required')
        def bridge(name,args):raise ValueError('Extraction performed through active Codex MCP orchestration; do not substitute endpoints')
        family='momentum' if name.startswith('M') else name
        parameters={'fold_year':year,'name':name}
        if name.startswith('M'):
            parameters.update(momentum_lookback_calendar_days=int(name.split('_')[0][1:]),number_of_holdings=int(name.split('_')[1][1:]))
        jobs=Jobs(store,SDK(api_key=None,client=client_for(d)),mcp=bridge)
        row=jobs.submit(spec,'backtest',payload,pricing,family=family,candidate=label,
                        parameters=parameters,assets=len(json.loads((OUT/'published_manifest.json').read_bytes())['assets']) if name!='SPY' else 1,
                        evaluations=1,folds=1,execute=True)
        save(d/'job.json',{'key':row['key'],'id':row['operation_id'],'label':label,'start':start,'end':end})
        print(json.dumps({'label':label,'id':row['operation_id'],'status':row['status']}),flush=True)
    finally:store.close()


def poll(label):
    d=RUNS/label;j=json.loads((d/'job.json').read_bytes())
    r=client_for(d).get_backtest(j['id'])
    n=len(list(d.glob('status_*.json')))
    save(d/f'status_{n:04}.json',r)
    status=str(r.get('status','')).upper()
    if status in ('COMPLETE','COMPLETED','FAILED','ERROR','CANCELED','CANCELLED'):
        save(d/'terminal_metadata.json',r)
    print(json.dumps({'label':label,'status':status,'id':j['id'],'result_keys':list(r.get('result',{}))}),flush=True)
    return r


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='operation',required=True)
    s=sub.add_parser('submit');s.add_argument('name',choices=NAMES);s.add_argument('year',type=int)
    p=sub.add_parser('poll');p.add_argument('label')
    a=parser.parse_args()
    if a.operation=='submit':submit(a.name,a.year)
    else:poll(a.label)
