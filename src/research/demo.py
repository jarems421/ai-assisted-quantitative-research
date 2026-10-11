"""EXP999 end-to-end smoke demonstration using in-process fake transports only."""
import copy
import json
import tempfile
from pathlib import Path

from src.research.nexus import Jobs
from src.research.spec import ROOT
from src.research.store import Store


class FakeSDK:
    def __init__(self):self.submissions=0;self.reads=0
    def submit(self,kind,payload,key):
        self.submissions+=1
        return {'id':'synthetic_run','status':'queued','idempotencyKey':key,'warnings':['Synthetic fixture only']}
    def read(self,kind,operation_id):
        self.reads+=1
        return {'id':operation_id,'status':'completed','result':{'backtestId':'synthetic_run'},'warnings':[]}


def fake_mcp(name,request):
    page=request['page']
    if name=='query_backtest_events':
        ts='2015-01-02T21:00:00Z' if page==1 else '2015-01-05T21:00:00Z'
        heading='page 1+, at least 1 matching' if page==1 else 'page 2/2, 2 matching'
        row={'event':{'timestamp':ts,'eventType':'Market','ticker':'SYNTHETIC','audit':{'nested':True}},
             'createdAt':'2030-01-01T00:00:00Z','dividend':{'payDate':'2030-02-01'}}
        text=f"## Backtest Events ({heading})\n\n[{ts[:10]} 21:00:00] Market (raw)\n"+json.dumps(row)
    elif name=='query_backtest_history':
        text='## Backtest History (page 1/1, 2 points)\ntime, value, cash, positionValue, comparisonValue, reservedCollateral\n2015-01-02T21:00:00Z, 25000, 25000, 0, 25000, 0\n2015-01-05T21:00:00Z, 25010, 25010, 0, 25000, 0'
    else:raise ValueError('Unexpected fake operation')
    return {'content':[{'type':'text','text':text}]}


def payload(spec):
    w=spec['windows']['development']
    return {'tool':'backtest_portfolio','portfolio':{'name':'Synthetic only','strategies':[]},
            'args':{'start_date':w['start'],'end_date':w['end'],'interval':'Day','initial_value':spec['costs']['initial_value'],
                    'dividend_policy':'cash','generate_events':spec['execution']['requires_events'],
                    'fee_config':{'Stock':{'amount':.1,'type':'percent'}},'baseline_symbol':'SYNTHETIC_BENCHMARK'}}


def demo():
    spec=json.loads((ROOT/'tests/fixtures/research_os/EXP999.json').read_text())
    spec['execution']['requires_events']=True
    pricing=json.loads((ROOT/'config/research_pricing.json').read_text())
    pricing['expires_on']='2999-01-01'  # Synthetic quote only; never used with a real transport.
    calls=[]
    with tempfile.TemporaryDirectory(prefix='research-exp999-') as directory:
        store=Store(Path(directory));store.register(spec)
        try:
            store.transition(spec,'HYPOTHESIS_FROZEN');store.transition(spec,'DEVELOPMENT')
            sdk=FakeSDK()
            def bridge(name,args):calls.append(name);return fake_mcp(name,args)
            jobs=Jobs(store,sdk,mcp=bridge,sleep=lambda _:None)
            arguments=dict(family='synthetic',candidate='smoke',parameters={},assets=1)
            planned=jobs.submit(spec,'backtest',payload(spec),pricing,**arguments)
            if sdk.submissions:raise AssertionError('Dry-run submitted a job')
            submitted=jobs.submit(spec,'backtest',payload(spec),pricing,execute=True,**arguments)
            jobs.poll(spec,submitted['key'])
            duplicate=jobs.submit(spec,'backtest',payload(spec),pricing,execute=True,**arguments)
            if sdk.submissions!=1:raise AssertionError('Duplicate fake submission')
            audit=jobs.raw.read('EXP999/synthetic_run/integrity.json')
            return {'experiment':'EXP999','mode':'synthetic in-process transports; no Nexus calls',
                    'real_nexus_jobs':0,'fake_submissions':sdk.submissions,'idempotency_verified':duplicate['key']==submitted['key'],
                    'events_extracted_first':calls[0]=='query_backtest_events','integrity':audit,
                    'budget':planned['request']['budget'],'persistent_workspace_changes':0,
                    'held_out_test_opened':False,'paper_deployed':False}
        finally:store.close()
