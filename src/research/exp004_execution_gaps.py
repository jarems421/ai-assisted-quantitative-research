"""Pre-performance evidence gates for exactly the EXP004 execution-gap pass."""
from decimal import Decimal

VERDICTS=('RECOVERED_EXECUTION_BAR','CERTIFIED_NO_TRADING',
          'CERTIFIED_CORPORATE_OR_LISTING_INTERRUPTION','UNRESOLVED_VENDOR_GAP',
          'IDENTITY_OR_SHARE_UNIT_CONFLICT')
RECOVERY=('security_identity_verified','exact_date_verified','actual_session_bar_verified',
          'timing_contract_verified','raw_unadjusted_contract_verified','share_unit_verified',
          'provenance_archived','positive_prices')


def request_room(records,category,key,allocation,ceiling=40):
    return (category in allocation and len(records)<ceiling
            and sum(r['category']==category for r in records)<allocation[category]
            and not any(r['key']==key for r in records))


def price_scope(rows,start,end):
    if not '2015-01-02'<=start<=end<='2020-12-31':raise ValueError('Sealed/outside case date bound')
    if any(not start<=r.get('date','')[:10]<=end for r in rows):raise ValueError('Out-of-case/held-out provider row')


def classify(evidence):
    if evidence.get('positive_identity_or_unit_conflict'):return VERDICTS[4]
    if all(evidence.get(k) is True for k in RECOVERY):return VERDICTS[0]
    if evidence.get('authoritative_exact_interruption') and evidence.get('complete_execution_interpretation'):return VERDICTS[2]
    if evidence.get('authoritative_exact_no_trading'):return VERDICTS[1]
    return VERDICTS[3]


def scale_screen(source_close,frozen_close):
    a,b=Decimal(str(source_close)),Decimal(str(frozen_close))
    if not a.is_finite() or not b.is_finite() or a<=0 or b<=0:return False
    return Decimal('.98')<=a/b<=Decimal('1.02')


def amendment_ready(rows):
    if len(rows)!=26 or len({(r['required_session'],r['ticker'],r['frozen_security_id']) for r in rows})!=26:raise ValueError('Exact 26-case denominator required')
    for r in rows:
        if r['verdict'] not in VERDICTS:raise ValueError('Unknown case verdict')
    return all(r['verdict'] in VERDICTS[:3] and (r['verdict']!=VERDICTS[2] or r.get('complete_execution_interpretation')) for r in rows)
