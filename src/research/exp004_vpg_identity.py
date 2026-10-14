"""Bounded VPG identity comparison; no suffix-derived alias or performance."""
OLD_ID='ticker:VSHw@2010-06-24'
NEW_ID=OLD_ID+'#2'
FIELDS=('ticker','cik','asset_type','share_class_figi','from_date','to_date')


def verdict(frozen,current):
    old=[r for r in frozen if r.get('ticker')=='VPG']
    new=[r for r in current if r.get('ticker')=='VPG']
    result={'verdict':'VPG_IDENTITY_UNRESOLVED','same_issuer':False,'same_common_class':False,
            'same_historical_span':False,'no_competing_class':False,'namespace_collision_evidenced':False}
    if len(old)!=1 or len(new)!=1:
        result['verdict']='VPG_DISTINCT_OR_AMBIGUOUS_SECURITY';return result
    a,b=old[0],new[0]
    result['same_issuer']=bool(a.get('cik')) and a['cik']==b.get('cik')
    result['same_common_class']=a.get('asset_type')==b.get('asset_type')=='CS' and bool(a.get('share_class_figi')) and a['share_class_figi']==b.get('share_class_figi')
    result['same_historical_span']=all(a.get(k)==b.get(k) for k in ('from_date','to_date'))
    competing=[r for r in current if r.get('security_id')==OLD_ID]
    # A namespace collision is evidenced by an independently distinguished,
    # nonoverlapping old base-ID row, not by requiring it to be the same class.
    collision=[r for r in competing if r.get('ticker')=='VSHw' and r.get('cik') and r.get('cik')!=a.get('cik')
               and r.get('asset_type')=='CS'
               and r.get('to_date') and r['to_date']<a['from_date']]
    overlaps=[r for r in current if r.get('ticker')!='VPG' and r.get('security_id') in (OLD_ID,NEW_ID)
              and r.get('from_date')<=a['to_date'] and (not r.get('to_date') or r['to_date']>=a['from_date'])]
    result['no_competing_class']=len(competing)==len(collision)==1 and not overlaps
    result['namespace_collision_evidenced']=a.get('security_id')==OLD_ID and b.get('security_id')==NEW_ID and bool(collision)
    if all(result[k] for k in result if k!='verdict'):result['verdict']='VPG_SAME_SECURITY_NAMESPACE_DRIFT'
    elif not result['same_issuer'] or not result['same_common_class'] or not result['no_competing_class']:
        result['verdict']='VPG_DISTINCT_OR_AMBIGUOUS_SECURITY'
    return result
