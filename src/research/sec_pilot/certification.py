"""Versioned source interpretation only; never approve policies or mutate Phase 2."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from io import StringIO
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

from src.research.sec_pilot.parsing import digest
from src.research.sec_pilot.provenance import instant

NY = ZoneInfo('America/New_York')
CONCEPTS = {
    'Revenue': ('RevenueFromContractWithCustomerExcludingAssessedTax', 'USD'),
    'Net income': ('NetIncomeLoss', 'USD'),
    'Diluted EPS': ('EarningsPerShareDiluted', 'USD/share'),
    'Weighted-average diluted shares': ('WeightedAverageNumberOfDilutedSharesOutstanding', 'shares'),
    'Operating cash flow': ('NetCashProvidedByUsedInOperatingActivities', 'USD'),
}


def local_time(raw):
    if not re.fullmatch(r'\d{14}', raw): raise ValueError('Invalid acceptance representation')
    naive = datetime.strptime(raw, '%Y%m%d%H%M%S')
    candidates = {naive.replace(tzinfo=NY, fold=f).astimezone(timezone.utc) for f in (0, 1)
                  if naive.replace(tzinfo=NY, fold=f).astimezone(timezone.utc).astimezone(NY).replace(tzinfo=None) == naive}
    if len(candidates) != 1: raise ValueError('Ambiguous or nonexistent Eastern wall time')
    return naive, next(iter(candidates))


def acceptance(raw, *, evidence_sha256):
    if not re.fullmatch(r'[0-9a-f]{64}', evidence_sha256 or ''): raise ValueError('Missing authoritative interpretation evidence hash')
    naive, eastern = local_time(raw)
    fixed = naive.replace(tzinfo=timezone(timedelta(hours=-5))).astimezone(timezone.utc)
    same = fixed == eastern
    return {'raw': raw, 'status': 'CERTIFIED' if same else 'PARTIAL',
            'accepted_at_utc': eastern.isoformat() if same else None,
            'candidate_eastern_utc': eastern.isoformat(), 'candidate_literal_est_utc': fixed.isoformat(),
            'interpretation': 'EST_AND_ET_CONVERGE' if same else 'UNRESOLVED_EST_LABEL_VS_DST_BEHAVIOR',
            'evidence_sha256': evidence_sha256, 'public_available_at_utc': None}


def proposed_bound(accepted_raw, filed_date, sessions):
    naive, _ = local_time(accepted_raw)
    filed = date.fromisoformat(filed_date)
    if not date(2015, 1, 1) <= naive.date() <= filed <= date(2020, 12, 31):
        raise ValueError('Unsupported source chronology/cutoff')
    ordered = sorted(set(sessions))
    if len(ordered) != len(sessions): raise ValueError('Duplicate calendar sessions')
    later = [d for d in ordered if d > max(naive.date(), filed)]
    if len(later) < 2: raise ValueError('Calendar coverage insufficient')
    return datetime.combine(later[1], datetime.min.time(), NY).replace(hour=9, minute=30).astimezone(timezone.utc).isoformat()


def policy_view(facts, decision, *, snapshot_sha256, policy, approval=None):
    """Trusted owner approval receipt must be supplied separately; this code creates none.

    Public timestamps remain original/nullable even when a future approved model
    supplies a separate decision bound. No real approval exists in Phase 3A.
    """
    if digest(facts) != snapshot_sha256: raise ValueError('Pinned interpretation snapshot changed')
    authorised = (isinstance(approval, dict) and approval.get('status') == 'OWNER_APPROVED'
                  and approval.get('policy_sha256') == digest(policy)
                  and approval.get('snapshot_sha256') == snapshot_sha256
                  and re.fullmatch(r'[0-9a-f]{64}', approval.get('authority_artifact_sha256', '')))
    at = instant(decision); usable = []; unavailable = []
    for fact in facts:
        reason = None
        contributors = fact.get('contributors') or []
        if not authorised: reason = 'POLICY_NOT_APPROVED'
        elif fact.get('semantic_status') != 'CERTIFIED_FOR_SCOPED_FACTS': reason = 'SEMANTIC_UNAVAILABLE'
        elif fact.get('identity_status') != 'CERTIFIED' or not fact.get('security_id'): reason = 'IDENTITY_UNAVAILABLE'
        elif not contributors: reason = 'MISSING_CONTRIBUTOR_EVIDENCE'
        else:
            for c in contributors:
                if (c.get('acceptance_status') != 'CERTIFIED' or not c.get('source_sha256')
                        or c.get('policy_sha256') != digest(policy) or not c.get('proposed_eligibility_at_utc')):
                    reason = 'CONTRIBUTOR_NOT_CERTIFIED'; break
                bound = instant(c['proposed_eligibility_at_utc'])
                if not c.get('accepted_at_utc') or bound < instant(c['accepted_at_utc']):
                    reason = 'INVALID_CONTRIBUTOR_CHRONOLOGY'; break
                if bound > at: reason = 'FUTURE_CONTRIBUTOR'; break
                if c.get('public_available_at_utc') and instant(c['public_available_at_utc']) > at:
                    reason = 'CONTRADICTORY_PUBLIC_EVIDENCE'; break
        if reason: unavailable.append({'fact_key': fact.get('fact_key'), 'reason': reason})
        else: usable.append(dict(fact, eligibility_basis='MODELED_OWNER_APPROVED_BOUND'))
    return {'snapshot_sha256': snapshot_sha256, 'policy_sha256': digest(policy),
            'usable': usable, 'unavailable': unavailable, 'approval_supplied': bool(authorised)}


def resolve_class(rows, issuer, class_name, at):
    decision = instant(at)
    seen = []
    for row in rows:
        if row.get('issuer_cik') != issuer or row.get('class') != class_name: continue
        if not row.get('start') or not row.get('end') or instant(row['start']) >= instant(row['end']):
            return {'status': 'UNAVAILABLE', 'reason': 'INVALID_OR_UNBOUNDED_SEGMENT'}
        if instant(row['start']) <= decision < instant(row['end']): seen.append(row)
    if len(seen) != 1: return {'status': 'UNAVAILABLE', 'reason': 'MISSING_OR_OVERLAPPING_SEGMENTS'}
    row = seen[0]
    if (row.get('status') != 'CERTIFIED' or not row.get('source_sha256') or not row.get('security_id')
            or not row.get('ticker') or row.get('corporate_action_unresolved')):
        return {'status': 'UNAVAILABLE', 'reason': 'UNCERTIFIED_CLASS_OR_CORPORATE_ACTION'}
    return {'status': 'CERTIFIED', 'security_id': row['security_id'], 'ticker': row['ticker']}


def unit_name(xml):
    if not xml: return None
    namespaces = dict(value for _, value in ET.iterparse(StringIO(xml), events=['start-ns']))
    def measure_name(text):
        if not text or ':' not in text: return None
        prefix, name = text.split(':', 1)
        uri = namespaces.get(prefix)
        if name == 'USD' and uri == 'http://www.xbrl.org/2003/iso4217': return 'USD'
        if name == 'shares' and uri == 'http://www.xbrl.org/2003/instance': return 'shares'
        return None
    root = ET.fromstring(xml); ns = {'i': 'http://www.xbrl.org/2003/instance'}
    divide = root.find('i:divide', ns)
    if divide is not None:
        numerator = divide.find('i:unitNumerator/i:measure', ns)
        denominator = divide.find('i:unitDenominator/i:measure', ns)
        if numerator is None or denominator is None: return None
        if measure_name(numerator.text) == 'USD' and measure_name(denominator.text) == 'shares': return 'USD/share'
        return None
    measures = root.findall('i:measure', ns)
    if len(measures) != 1: return None
    return measure_name(measures[0].text)


def semantic(snapshot, family):
    concept, unit = CONCEPTS[family]
    end = datetime.strptime(snapshot['report_period_raw'], '%Y%m%d').date().isoformat()
    alternatives = [f for f in snapshot['facts'] if f['concept'] == concept]
    eligible = []
    for f in alternatives:
        context = f['context']; period = context['period']
        if (not f['namespace'].startswith('http://fasb.org/us-gaap/') or context['dimensions']
                or period.get('type') != 'duration' or period.get('endDate') != end
                or context['entity'].get('identifier', '').lstrip('0') != snapshot['fixture']['issuer_cik'].lstrip('0')):
            continue
        length = (date.fromisoformat(end)-date.fromisoformat(period['startDate'])).days+1
        if not 350 <= length <= 380: continue  # Annual fiscal flows only; never infer a calendar quarter.
        if unit_name(f.get('unit_xml')) != unit or f.get('nil') or f.get('status') != 'OBSERVED_SOURCE': continue
        try:
            value = Decimal(f['exact_value'].strip())
            if not value.is_finite(): continue
        except InvalidOperation: continue
        eligible.append(f)
    # Equivalent repeated original elements are retained, not rewritten.
    identities = {digest({k: f[k] for k in ('namespace', 'exact_value', 'decimals', 'unit_xml')} |
                         {'entity': f['context']['entity'], 'period': f['context']['period']}) for f in eligible}
    status = 'SELECTED_PENDING_PRIMARY_RECONCILIATION' if len(identities) == 1 else 'AMBIGUOUS' if identities else 'UNAVAILABLE'
    return {'family': family, 'status': status, 'unit': unit, 'alternatives_count': len(alternatives),
            'candidate_count': len(eligible), 'contributors': eligible if len(identities) == 1 else [],
            'all_alternative_locators': [f['fact_locator'] for f in alternatives],
            'transformation': 'NONE; original annual reported amounts; no split adjustment or YTD differencing',
            'selection_rule': 'same accession/current annual period/issuer/no dimensions/exact US-GAAP tag and unit; repeated equal elements retained'}
