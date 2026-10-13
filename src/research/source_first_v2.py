"""Frozen lexicographic SEC/Congress selection; no performance criterion."""
from src.research.spec import digest
GATES=('SOURCE_ACCESS','DENOMINATOR','POINT_IN_TIME','HISTORICAL_DEPTH','REPRODUCIBILITY')
def selection_contract():
    return {'version':'selection_v002','surfaces':['SEC','CONGRESS'],'hard_gates':list(GATES),
     'eligibility':'No BLOCKED hard gate; UNKNOWN never counts as proof',
     'order':['more_PROVEN_or_PASS','fewer_PARTIAL','fewer_derived_dependencies','simpler_identity_burden','higher_plausible_independent_frequency','SEC_tie'],
     'performance_authorized':False,'comparison_ceiling':24,'SEC_prototype_ceiling':32,'neutral_sample_ceiling':12,'Congress_original_ceiling':18}
def select(rows):
    if len(rows)!=2 or {r['id'] for r in rows}!={'SEC','CONGRESS'}:raise ValueError('Exact two-surface comparison required')
    eligible=[r for r in rows if all(r['gates'][k]!='BLOCKED' for k in GATES)]
    if not eligible:raise ValueError('No eligible research surface')
    def key(r):
        values=[r['gates'][k] for k in GATES]
        if any(v not in ('PROVEN_FROM_EXISTING_EVIDENCE','PASS_BOUNDED_PROBE','PARTIAL','UNKNOWN','BLOCKED') for v in values):raise ValueError('Unknown gate label')
        return (sum(v in ('PROVEN_FROM_EXISTING_EVIDENCE','PASS_BOUNDED_PROBE') for v in values),-values.count('PARTIAL'),-r['derived_dependencies'],-r['identity_burden'],r['plausible_independent_frequency'],r['id']=='SEC')
    winner=max(eligible,key=key)
    return {'winner':winner['id'],'selection_rule_sha256':digest(selection_contract()),'keys':{r['id']:key(r) for r in eligible},'rows':rows,'performance_used':False}
