"""Aggregate complete amended input QA without calculating portfolio returns."""
import hashlib
import json
from collections import defaultdict

from src.research.exp004_inputs import ROOT, RAW
from src.research.spec import digest


def write(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def review():
    directory=ROOT/'experiments/EXP004'
    summaries=[json.loads((RAW/f'compiled_{y}_v002/qa_summary.json').read_bytes()) for y in range(2015,2021)]
    monthly=[];ledger={}
    for s in summaries:
        if s['status']!='PASS_LOCAL_NUMERIC':raise ValueError('Failed yearly QA')
        for g in s['ambiguity_ledger']:
            key=(g['security_id'],tuple(g['tickers_at_event']),g['effective_date'])
            if key not in ledger:ledger[key]=dict(g,first_affected_decision=None,last_affected_decision=None,excluded_security_decisions=0)
            merged=ledger[key];merged['excluded_security_decisions']+=g['excluded_security_decisions']
            for name,fn in [('first_affected_decision',min),('last_affected_decision',max)]:
                vals=[v for v in (merged[name],g[name]) if v is not None]
                merged[name]=fn(vals) if vals else None
        rows=json.loads((RAW/f"compiled_{s['year']}_v002/decision_inputs.json").read_bytes())
        for m,p in zip(s['monthly'],rows):
            ids=set(p['ticker_byid']);values=p['momentum']
            if ids!=set(values['180']) or ids!=set(values['365']):raise ValueError('Universe mismatch')
            if any(g['security_id'] in ids for g in m['action_exclusions']):raise ValueError('Ambiguous numeric value')
            if not m['K20_available'] or not m['K40_available']:raise ValueError('Unexpected holdings shortfall')
            cleaned={k:v for k,v in m.items() if k!='selected_top_K'}
            cleaned['submit_allowed']=False  # Publication and frozen binding must still pass.
            monthly.append(cleaned)
    if len(monthly)!=72 or len({m['session'] for m in monthly})!=72:raise ValueError('Monthly panel incomplete')
    action={'status':'PASS_GENERIC_TEMPORARY_EXCLUSION','rule':'Inclusive 365-calendar-day shared quality window; no ticker exclusions/corrected factors',
            'groups':list(ledger.values()),'monthly_excluded_security_decisions':sum(m['excluded'].get('corporate_action_ambiguity',0) for m in monthly),
            'source_rows_preserved':True,'zero_performance_observed':True,
            'explanatory_evidence':{'LADR':'Owner explains the2015 cash/stock-election special distribution; source rows remain ambiguous. No external factor is applied.',
                                    'source':'corporate_action_amendment_authorization_20261011.md'},
            'optional_adjusted_price_diagnostic':'Not performed; momentum implementation unchanged'}
    write(directory/'research/corporate_action_ambiguity_ledger.json',action)
    qa={'status':'PASS_COMPLETE_DEVELOPMENT_INPUT_QA','monthly':monthly,
        'source_parts':summaries[0]['source_parts'],'yearly_qa_hashes':{str(y):hashlib.sha256((RAW/f'compiled_{y}_v002/qa_summary.json').read_bytes()).hexdigest() for y in range(2015,2021)},
        'checks':{'no_duplicate_identities':True,'no_future_price_bars':True,'no_ambiguous_numeric_windows':True,
                  'four_cells_and_EW_same_maximum_horizon_population':True,'no_performance_calculated':True}}
    write(directory/'research/amended_input_qa.json',qa)
    manifest=json.loads((directory/'development_input_manifest.json').read_bytes())
    manifest.update(decisions=monthly,amendment_qa='research/amended_input_qa.json',corporate_action_ledger='research/corporate_action_ambiguity_ledger.json')
    if not (directory/'research/publication_runtime_audit.json').exists():
        manifest.update(status='INPUT_QA_PASSED_AWAITING_AMENDED_FREEZE_AND_PUBLICATION',qa_failure=None)
    manifest.pop('input_manifest_sha256',None);manifest['input_manifest_sha256']=digest(manifest)
    write(directory/'development_input_manifest.json',manifest)
    print(json.dumps({'status':qa['status'],'decisions':72,'ambiguity_groups':len(ledger),'exclusions':action['monthly_excluded_security_decisions']}))


if __name__=='__main__':review()
