"""Public, hand-verifiable fixtures; no actual filing, prices or experiment state."""
from copy import deepcopy
from pathlib import Path
import json
from src.research.spec import digest
from .proof import ROLES, GATES, file_hash

HASH = digest({'evidence':'synthetic EXP999 only'})


def tiny():
    sessions=[]
    for day,price in [('02','10'),('03','12'),('06','11')]:
        sessions.append({'session':f'2020-01-{day}','open_at':f'2020-01-{day}T14:30:00Z',
                         'close_at':f'2020-01-{day}T21:00:00Z','prices':{'EXP999-A':{'open':price,'close':price}}})
    binding={'issuer_cik':'999','class':'A','security_id':'EXP999-A','ticker':'OLD','exchange':'SYNTHETIC',
             'effective_from':'2020-01-01T00:00:00Z','effective_to':'2021-01-01T00:00:00Z','source_sha256':HASH}
    obs={'security_id':'EXP999-A','ticker':'OLD','value':'1','available_at':'2020-01-01T00:00:00Z','source_sha256':HASH}
    rebalance={'session':'2020-01-02','decision_at':'2020-01-02T01:00:00Z','observations':[obs],'top_k':1,'exposure':'0.5'}
    return {'experiment_id':'EXP999','mode':'SYNTHETIC_INFRASTRUCTURE','contract_version':'execution_v001',
            'starting_cash':'1000','fee_bps':'0','sessions':sessions,'bindings':[binding],'events':[],
            'rebalances':[rebalance]}


def event(kind, **terms):
    return {'event_id':'EXP999-event','session':'2020-01-03','sequence':1,'security_id':'EXP999-A',
            'kind':kind,'available_at':'2020-01-02T01:00:00Z','source_sha256':HASH,
            'status':'CERTIFIED_SYNTHETIC_FIXTURE',**terms}


def cases():
    ordinary=tiny()
    sale=deepcopy(ordinary['rebalances'][0]); sale.update(session='2020-01-06',decision_at='2020-01-06T01:00:00Z',top_k=0,exposure='0')
    ordinary['rebalances'].append(sale)
    div=tiny(); div['events']=[event('dividend',cash_per_share='1',currency='USD',share_basis='CURRENT_AFTER_PRIOR_SEQUENCED_ACTIONS',pay_session='2020-01-06')]
    split=tiny(); split['events']=[event('split',ratio='2')]
    for row in split['sessions'][1:]: row['prices']['EXP999-A']={'open':'5','close':'5'}
    rename=tiny(); old=rename['bindings'][0]; old['effective_to']='2020-01-03T00:00:00Z'
    rename['bindings'].append(dict(old,ticker='NEW',effective_from=old['effective_to'],effective_to='2021-01-01T00:00:00Z'))
    cash=tiny(); cash['bindings'][0]['effective_to']='2020-01-03T00:00:00Z'
    cash['events']=[event('cash_merger',cash_per_share='15',currency='USD',pay_session='2020-01-03')]
    for row in cash['sessions'][1:]: row['prices']={}
    return {'ordinary':ordinary,'dividend':div,'split':split,'rename':rename,'cash_acquisition':cash}


def proof_fixture(root):
    root=Path(root)
    snapshot=root/'snapshot.bin'; snapshot.write_bytes(b'Synthetic EXP999 source bytes\n')
    source_hash=file_hash(snapshot)
    contracts={r:{'status':'CERTIFIED_SYNTHETIC_FIXTURE','synthetic':True} for r in ROLES}
    contracts['population'].update(security_ids=['EXP999-A'])
    contracts['identity'].update(security_ids=['EXP999-A'])
    contracts['availability'].update(status='APPROVED_SYNTHETIC_FIXTURE',approval_sha256=HASH,public_available_at_utc=None)
    contracts['execution'].update(unresolved_terminal_events=[])
    contracts['trial_family'].update(evaluation_ceiling=1,performance_authorized=False)
    contracts['source_contract'].update(snapshot_hashes=[source_hash])
    refs={}
    for role,value in contracts.items():
        p=root/f'{role}.json'; p.write_text(json.dumps(value,sort_keys=True),encoding='utf-8')
        refs[role]={'path':p.name,'sha256':file_hash(p)}
    gate_hashes={g:digest({'gate':g,'evidence':'SYNTHETIC_FIXTURE'}) for g in GATES}
    spec={'schema_version':'proof_experiment_v001','experiment_id':'EXP999','mode':'SYNTHETIC_INFRASTRUCTURE',
          'hypothesis':'Synthetic infrastructure receipt, not alpha','research_stage':'DRAFT','research_cutoff':'2020-12-31',
          'sealed_stage_rules':'existing_store_owner_test_and_paper_gates','contracts':refs,
          'gates':{g:{'status':'CERTIFIED','receipt_sha256':h} for g,h in gate_hashes.items()},
          'source_snapshots':[{'path':snapshot.name,'sha256':source_hash,'source_end':'2020-01-01'}]}
    authority={'scope':'SYNTHETIC_EXP999','stage':'DRAFT','approval_sha256':HASH,'gate_hashes':gate_hashes}
    return spec,authority
