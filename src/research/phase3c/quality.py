"""Source-only chain, identity, session and completeness gates; no alpha series."""
from datetime import date
from decimal import Decimal, InvalidOperation
import math

from src.research.sec_pilot.parsing import digest

STATES = {'KNOWN_ELIGIBLE', 'KNOWN_INELIGIBLE', 'KNOWN_NO_REQUIRED_FILING', 'KNOWN_FILING_MISSING',
          'SOURCE_RETRIEVAL_FAILED', 'IDENTITY_UNRESOLVED', 'PRICE_UNRESOLVED',
          'TERMINAL_EVENT_UNRESOLVED', 'OTHER_EXPLICIT_STATE'}


def completeness(population, evidence):
    keys = [r['case_key'] for r in population]
    if len(keys) != len(set(keys)) or not keys: raise ValueError('Independent unique denominator required')
    if len(evidence) != len({r['case_key'] for r in evidence}): raise ValueError('Duplicate evidence identity')
    index = {r['case_key']: r for r in evidence}
    if set(index) - set(keys): raise ValueError('Count-preserving substitution outside population')
    rows = []
    for key in keys:
        row = index.get(key, {'case_key': key, 'state': 'SOURCE_RETRIEVAL_FAILED', 'reason': 'Omitted source candidate'})
        if row['state'] not in STATES: raise ValueError('Unknown completeness state')
        if row['state'].startswith('KNOWN_') and not row.get('evidence_sha256'):
            raise ValueError('Known absence/eligibility requires source evidence')
        rows.append(row)
    resolved = sum(r['state'].startswith('KNOWN_') for r in rows)
    return {'population_sha256': digest(population), 'denominator': len(keys), 'resolved_count': resolved,
            'resolved_fraction': resolved / len(keys), 'rows': rows}


def rounding(value, decimals):
    v = Decimal(value)
    if not v.is_finite(): raise ValueError('Nonfinite source value')
    if decimals == 'INF': return v, v
    if decimals is None: raise ValueError('Unknown rounding precision')
    try: half = Decimal(10) ** (-int(decimals)) / 2
    except (ValueError, InvalidOperation): raise ValueError('Invalid decimals') from None
    return v - half, v + half


def compatible(a, b):
    x, y = rounding(a['value'], a['decimals']), rounding(b['value'], b['decimals'])
    return max(x[0], y[0]) <= min(x[1], y[1])


def revenue_chain(filings):
    def unavailable(reason): return {'status': 'UNAVAILABLE_' + reason, 'source_hashes': [r.get('source_sha256') for r in filings]}
    if len(filings) != 3: return unavailable('MISSING_ORIGINAL')
    if len({f['issuer_cik'] for f in filings}) != 1 or any(f.get('form') != '10-K' or f.get('version') != 'ORIGINAL' for f in filings):
        return unavailable('RESTATEMENT_OR_VERSION')
    ordered = sorted(filings, key=lambda r: r['period_end'])
    if len({r['accession'] for r in ordered}) != 3: return unavailable('RESTATEMENT_OR_VERSION')
    previous = None
    for f in ordered:
        r = f.get('revenue')
        if not r or r.get('concept') != 'RevenueFromContractWithCustomerExcludingAssessedTax' or not r.get('namespace', '').startswith('http://fasb.org/us-gaap/'):
            return unavailable('CONCEPT')
        if (r.get('dimensions') or r.get('unit') != 'USD' or r.get('entity_cik') != f['issuer_cik']
                or not r.get('locator') or not f.get('source_sha256') or not r.get('original_element_reconciled')
                or r.get('conflicting_duplicates')): return unavailable('CONTEXT')
        try:
            start, end = date.fromisoformat(f['period_start']), date.fromisoformat(f['period_end'])
            number = Decimal(r['value'])
            if not 350 <= (end - start).days + 1 <= 380 or not number.is_finite() or number <= 0:
                return unavailable('CONTEXT')
            if previous:
                if (start - date.fromisoformat(previous['period_end'])).days != 1 or not 350 <= (end - date.fromisoformat(previous['period_end'])).days <= 380:
                    return unavailable('OTHER_EXPLICIT_REASON')
                comparative = f.get('comparative')
                if not comparative or not compatible(previous['revenue'], comparative):
                    return unavailable('ROUNDING_COMPARABILITY')
                if (comparative.get('end') != previous['period_end'] or comparative.get('start') != previous['period_start']
                        or comparative.get('unit') != 'USD' or comparative.get('entity_cik') != f['issuer_cik']
                        or comparative.get('dimensions') or comparative.get('concept') != r['concept']
                        or not comparative.get('original_element_reconciled')):
                    return unavailable('CONTEXT')
            previous = f
        except (ValueError, InvalidOperation): return unavailable('CONTEXT')
    numeric = {'numeric_comparability': 'PASS', 'source_hashes': [r['source_sha256'] for r in ordered]}
    if any(r.get('accounting_basis_status') != 'CERTIFIED' or not r.get('basis_evidence') for r in ordered):
        return dict(numeric, status='UNAVAILABLE_ACCOUNTING_BASIS')
    if any(r.get('entity_scope_status') != 'CERTIFIED' or not r.get('scope_evidence') for r in ordered):
        return dict(numeric, status='UNAVAILABLE_ENTITY_SCOPE')
    return dict(numeric, status='CERTIFIED_CHAIN')


def identity_gate(row):
    contradictions = row.get('contradictions', [])
    if contradictions: return 'AMBIGUOUS'
    if not row.get('class') or not row.get('ticker') or not row.get('exchange'): return 'UNRESOLVED'
    if not row.get('stable_id') or not row.get('identifier_level'): return 'PROVISIONAL'
    if not all(row.get(k) for k in ('effective_from', 'effective_to', 'start_evidence', 'end_evidence')):
        return 'PROVISIONAL'
    if row['effective_from'] >= row['effective_to'] or row.get('overlap'): return 'AMBIGUOUS'
    if row.get('ended') and row.get('terminal_status') != 'TERMINAL_EVENT_CERTIFIED': return 'PROVISIONAL'
    return 'CERTIFIED_FOR_PILOT'


def terminal_gate(event):
    if not event or not event.get('source_sha256') or not event.get('effective_at'):
        return 'TERMINAL_EVENT_UNRESOLVED'
    kind = event.get('kind')
    required = {'cash_merger': ('cash_per_share', 'currency'), 'stock_merger': ('successor_security_id', 'exchange_ratio'),
                'cancellation': ('explicit_zero_recovery_evidence',), 'spinoff': ('successor_security_id', 'distribution_ratio')}
    if kind not in required or not all(event.get(k) is not None for k in required[kind]):
        return 'TERMINAL_EVENT_PARTIAL'
    return 'TERMINAL_EVENT_CERTIFIED' if event.get('class_and_position_terms_certified') else 'TERMINAL_EVENT_PARTIAL'


def figi_gate(response):
    data = response.get('data', [])
    # Multiple exchange instruments with same share-class ID can be retained,
    # but distinct share-class results cannot be selected by first match.
    ids = {r.get('shareClassFIGI') for r in data if r.get('shareClassFIGI')}
    if response.get('error') or len(ids) > 1: return 'AMBIGUOUS'
    if len(ids) == 1: return 'IDENTIFIER_ONLY_NOT_HISTORICAL_INTERVAL'
    return 'UNRESOLVED'


def market_quality(rows, expected_sessions):
    dates = [r['date'][:10] for r in rows]
    expected = set(expected_sessions)
    invalid = 0; split_checks = 0; dividend_checks = 0; transform_failed = 0
    for r in rows:
        fields = [r.get(k) for k in ('open', 'high', 'low', 'close', 'volume', 'splitFactor', 'divCash')]
        try:
            if any(v is None or not math.isfinite(float(v)) for v in fields): invalid += 1; continue
            o, h, l, c, vol, split, div = map(float, fields)
        except (ValueError, TypeError, OverflowError): invalid += 1; continue
        if min(o, h, l, c, split) <= 0 or vol < 0 or not vol.is_integer() or div < 0 or not l <= min(o, c) <= max(o, c) <= h: invalid += 1
    for prev, current in zip(rows, rows[1:]):
        try:
            factor_ratio = (current['adjClose'] / current['close']) / (prev['adjClose'] / prev['close'])
            split = current['splitFactor']; div = current['divCash']
            expected_ratio = split / (1 - div * split / prev['close'])
            ok = math.isclose(factor_ratio, expected_ratio, rel_tol=1e-6, abs_tol=1e-8)
            if split != 1: split_checks += ok
            if div != 0: dividend_checks += ok
            if (split != 1 or div != 0) and not ok: transform_failed += 1
        except (KeyError, ZeroDivisionError, TypeError): transform_failed += 1
    return {'expected_sessions': len(expected), 'received_sessions': len(rows),
            'missing_sessions': sorted(expected - set(dates)), 'extra_sessions': sorted(set(dates) - expected),
            'duplicate_sessions': len(dates) - len(set(dates)), 'invalid_rows': invalid,
            'ordered_dates': dates == sorted(dates),
            'split_event_rows': sum(r.get('splitFactor') not in (None,1) for r in rows),
            'dividend_event_rows': sum(r.get('divCash') not in (None,0) for r in rows),
            'split_reconciliation_candidates_passed': split_checks, 'dividend_reconciliation_candidates_passed': dividend_checks,
            'action_transform_failed_or_missing': transform_failed,
            'transform_status': 'PROPOSED_FORMULA_REQUIRES_PROVIDER_CONVENTION_CERTIFICATION',
            'session_status': 'PASS' if set(dates) == expected and len(dates) == len(set(dates)) and dates == sorted(dates) and not invalid else 'UNRESOLVED'}


def stage_receipt(record, *, context):
    required = ('source_hash', 'policy_hash', 'identity_snapshot_hash', 'execution_engine_hash',
                'stage', 'trial_key', 'control_relationship', 'scenario', 'status', 'cost_scenario', 'result_hash')
    if any(k not in record for k in required): raise ValueError('Incomplete stage/source receipt')
    for k in required:
        if k.endswith('hash') and (not isinstance(record[k], str) or len(record[k]) != 64
                                   or any(c not in '0123456789abcdef' for c in record[k])):
            raise ValueError('Invalid provenance hash')
    if record['stage'] != context['active_stage'] or record['stage'] not in ('DEVELOPMENT', 'VALIDATION', 'TEST_AUTHORIZED'):
        raise ValueError('Sealed or mismatched stage')
    if record['stage'] == 'TEST_AUTHORIZED' and not context.get('trusted_owner_test_receipt_hash'):
        raise ValueError('Owner-only Test evidence missing')
    if record['source_hash'] not in context['allowed_source_hashes'] or record['policy_hash'] != context['approved_policy_hash']:
        raise ValueError('Unapproved source/policy scope')
    if context.get('source_end') > context['window_end']: raise ValueError('Future source access')
    if record['identity_snapshot_hash'] != context['identity_snapshot_hash'] or record['execution_engine_hash'] != context['execution_engine_hash']:
        raise ValueError('Changed identity or execution certificate')
    relation = record['control_relationship']
    if (not isinstance(relation, dict) or not relation.get('trial_key') or
            relation.get('population_hash') != context['population_hash'] or
            relation.get('calendar_hash') != context['calendar_hash']):
        raise ValueError('Unmatched control population/calendar')
    if record['status'] not in ('PLANNED', 'COMPLETE', 'FAILED', 'UNRESOLVED'):
        raise ValueError('Unrecognized ledger status')
    if record['scenario'] not in ('base', 'double_cost', 'delay1', 'delay5', 'no_information', 'universe_ew'):
        raise ValueError('Unregistered scenario')
    return dict(record, receipt_sha256=digest(record), provenance_scope='VALIDATION_COMPONENT_NOT_AUTHORIZATION')
