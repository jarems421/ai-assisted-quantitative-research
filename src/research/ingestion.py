"""Explicit normalized sweep-cell ingestion from saved complete engine evidence."""
import itertools
import json

from src.research.report import compute
from src.research.spec import digest, canonical


def eligible(spec, metrics, evidence):
    if spec['selection']['primary_metric']=='paired_mean_daily_excess':
        if spec['selection'].get('paired_policy') == 'exp004_momentum_ew_v1':
            from src.research.exp004_policy import paired_eligibility
        elif spec['selection'].get('paired_policy') == 'exp003_mean_sharpe_v1':
            from src.research.exp003_policy import paired_eligibility
        else:
            raise ValueError('Unknown paired selection policy')
        return paired_eligibility(evidence)
    return (metrics['maximum_drawdown']<=spec['selection']['eligibility']['max_drawdown']
            and evidence['completed_trades']>=spec['selection']['eligibility']['minimum_trades']
            and evidence['participation']>=spec['selection']['minimum_participation']
            and evidence['breadth']>=spec['selection']['minimum_breadth'])


def sweep_cells(store, spec, parent_key, normalized):
    store.verify(spec)
    parent=store.db.execute('SELECT * FROM jobs WHERE key=? AND experiment=?',(parent_key,spec['experiment_id'])).fetchone()
    if parent is None or parent['kind']!='sweep' or parent['stage']!='DEVELOPMENT' or parent['status'] not in ('COMPLETE','COMPLETED'):
        raise ValueError('Complete Development sweep required')
    response=json.loads(parent['response'])
    if normalized['source_sha256']!=digest(response) or not normalized.get('normalization_audited'):
        raise ValueError('Normalization must reference the complete saved engine response and be audited')
    axes=sorted(spec['optimization_ranges'])
    expected=set(itertools.product(*(spec['optimization_ranges'][a] for a in axes)))
    rows=normalized['cells']
    seen={tuple(row['parameters'][a] for a in axes) for row in rows}
    if seen!=expected or len(rows)!=len(expected):raise ValueError('Keep every declared cell, including failed/ugly trials')
    original=json.loads(parent['request'])
    exported=[]
    for row in rows:
        key='cell-'+digest({'parent':parent_key,'parameters':row['parameters']})
        status=row['status']
        if status not in ('COMPLETE','FAILED','UNRESOLVED'):raise ValueError('Invalid cell status')
        metric=None;is_eligible=False
        if status=='COMPLETE':
            if not row.get('portfolio') or not row.get('run_id'):raise ValueError('Successful cell lacks portfolio/run provenance')
            metric=compute(spec,{'candidate':{'stage':'DEVELOPMENT','closes':row['closes']}})['candidate']
            is_eligible=eligible(spec,metric,row)
        payload=dict(original['payload'],portfolio=row.get('portfolio') or original['payload']['portfolio'])
        request={'kind':'imported_sweep_cell','payload':payload,'spec_hash':digest(spec),'stage':'DEVELOPMENT',
                 'family':original['family'],'candidate':row.get('name',key),'parameters':row['parameters'],
                 'parent_key':parent_key,'normalization_hash':digest(normalized),'budget':{'planned_evaluations':0,'estimated_tokens':0}}
        prior=store.db.execute('SELECT request FROM jobs WHERE key=?',(key,)).fetchone()
        if prior and prior[0]!=canonical(request).decode():raise ValueError('Cannot rewrite an ingested cell')
        with store.db:
            store.db.execute('INSERT OR IGNORE INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                             (key,spec['experiment_id'],'imported_sweep_cell','DEVELOPMENT',canonical(request).decode(),status,row.get('run_id'),canonical(row).decode(),None))
        store.record_trial(key,spec['experiment_id'],original['family'],row.get('name',key),row['parameters'],'DEVELOPMENT',
                           {'status':status,'metrics':metric,'evaluations':0,'parent_key':parent_key,'counts_in_parent_evaluations':True},
                           run_id=row.get('run_id'),eligibility=is_eligible)
        exported.append(key)
    return {'parent_key':parent_key,'cell_trial_keys':exported,'failed_cells_preserved':True,'evaluation_count':len(rows)}
