"""Owner-authorized single pre-performance source-QA amendment, not redesign."""
import hashlib
import json
from pathlib import Path

from src.research.exp004_inputs import ROOT, RAW, save
from src.research.spec import digest, validate
from src.research.store import Store

RULE = (' Corporate-action QA amendment: at every decision inspect the inclusive '
        'prior-completed-session-minus365-calendar-days through prior-session window. '
        'A stable-security/effective-date group is ambiguous if multiple distinct '
        'adjustment factors lack composition lineage, version/revision is unresolved, '
        'or a positive finite unique economically applicable factor cannot be determined. '
        'Ordinary unique source splits are not ambiguous merely for imperfect vendor '
        'revision history. Identical economic factors normalize once, preserving all '
        'raw rows. A crossing ambiguity makes that security temporarily unavailable '
        'in the common population for all four cells and the equal-weight benchmark; '
        'reentry requires the event to age out of the maximum window and all other '
        'requirements to pass. No guessed/composed/averaged or ticker-corrected factor.')


def allowed_amendment(old, new):
    expected = json.loads(json.dumps(old))
    expected['dynamic_universe']['definition'] += RULE
    if new != expected: raise ValueError('Amendment changes more than the authorized source-QA rule')
    validate(new)


def freeze_amendment():
    p = ROOT/'experiments/EXP004'
    if (p/'freeze_versions/v002/receipt.json').exists():
        from src.research.prepare_exp004 import verify_freeze
        return verify_freeze()
    old = json.loads((p/'freeze_versions/v001/experiments/EXP004/spec.json').read_bytes())
    new = json.loads(json.dumps(old));new['dynamic_universe']['definition'] += RULE
    allowed_amendment(old,new)
    summaries = [json.loads((RAW/f'compiled_{y}_v002/qa_summary.json').read_bytes()) for y in range(2015,2021)]
    if any(s['status'] != 'PASS_LOCAL_NUMERIC' for s in summaries): raise ValueError('Complete input QA required')
    original = json.loads((p/'freeze_receipt.json').read_bytes())
    if json.loads((p/'spec.json').read_bytes()) != old: raise ValueError('Original specification changed before amendment')
    store = Store(ROOT)
    try:
        with store.db:
            store.db.execute('BEGIN IMMEDIATE')
            state = store.verify(old)
            if state['stage'] != 'HYPOTHESIS_FROZEN' or state['candidate']:
                raise ValueError('Amendment must precede Development/candidate formation')
            counts = {table: store.db.execute(f'SELECT COUNT(*) FROM {table} WHERE experiment=?',('EXP004',)).fetchone()[0]
                      for table in ('jobs','trials')}
            if any(counts.values()): raise ValueError('Zero jobs and trials required before amendment')
            # Input extraction receipts may exist; no strategy submission receipt may exist.
            if list((ROOT/'data/raw/research_os/EXP004').rglob('response.json')):
                raise ValueError('Existing strategy receipts require explicit review')
            encoded = (json.dumps(new,indent=2)+'\n').encode()
            artifacts = dict(original['frozen_artifacts'])
            artifacts['experiments/EXP004/spec.json'] = hashlib.sha256(encoded).hexdigest()
            for name in ('src/research/exp004_actions.py','src/research/exp004_compile.py'):
                artifacts[name] = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            receipt = {'status':'HYPOTHESIS_FROZEN','version':2,
                       'supersedes':'SUPERSEDED_PRE_PERFORMANCE_BY_SOURCE_QA',
                       'original_receipt_byte_sha256':hashlib.sha256((p/'freeze_receipt.json').read_bytes()).hexdigest(),
                       'old_specification_sha256':digest(old),'old_methodology_sha256':original['frozen_methodology_sha256'],
                       'frozen_specification_sha256':digest(new),'frozen_methodology_sha256':digest(artifacts),
                       'frozen_artifacts':artifacts,
                       'exact_diff':{'/dynamic_universe/definition':{'old':old['dynamic_universe']['definition'],'new':new['dynamic_universe']['definition']}},
                       'reason':'Generic temporary information-quality exclusion discovered in production QA before performance',
                       'zero_performance_proof':{'local_store_counts':counts,'candidate':None,'owner_assertion':True,
                           'strategy_receipts':0,'boundary':'Local ledgers and owner declaration, not account-wide independent audit'},
                       'input_qa_hashes':[hashlib.sha256((RAW/f"compiled_{s['year']}_v002/qa_summary.json").read_bytes()).hexdigest() for s in summaries],
                       'authorization_sha256':hashlib.sha256((p/'research/corporate_action_amendment_authorization_20261011.md').read_bytes()).hexdigest()}
            save(p/'freeze_versions/v002/spec.json',new)
            save(p/'freeze_versions/v002/receipt.json',receipt)
            (p/'spec.json').write_bytes(encoded)
            store.db.execute('UPDATE experiments SET spec_hash=? WHERE id=?',(digest(new),'EXP004'))
        store.export('EXP004')
        return receipt
    finally:store.close()


if __name__=='__main__':
    f=freeze_amendment();print(json.dumps({'version':2,'specification_sha256':f['frozen_specification_sha256'],'methodology_sha256':f['frozen_methodology_sha256']}))
