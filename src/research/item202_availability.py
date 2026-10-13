"""EXP006-specific acceptance-buffered policy; metadata only, no performance path."""
from datetime import date, datetime, time, timezone, timedelta
from html import unescape
import hashlib
import re
from zoneinfo import ZoneInfo

from src.research.sec_pilot.certification import acceptance
from src.research.spec import digest

NY = ZoneInfo('America/New_York')
RULE = '09:30 America/New_York on second regular NYSE session strictly after later of FILED AS OF DATE and each retained acceptance candidate civil date; require identical candidate opens'


def calendar_sessions(certificate):
    start, end = map(date.fromisoformat, certificate['scope'])
    if certificate.get('status') != 'CERTIFIED_SCOPED_NYSE_REGULAR_OPEN_CALENDAR':
        raise ValueError('Calendar certificate required')
    closed = {date.fromisoformat(d) for d in certificate['full_day_closures']}
    days = [start + timedelta(days=i) for i in range((end-start).days+1)]
    sessions = [d for d in days if d.weekday()<5 and d not in closed]
    if len(sessions) != certificate['session_count'] or digest([d.isoformat() for d in sessions]) != certificate['sessions_sha256']:
        raise ValueError('Calendar hash/count mismatch')
    return sessions


def parse_header(body, *, cik, accession, form):
    text = unescape(body.decode('utf-8', errors='strict'))
    def unique(pattern):
        values = set(re.findall(pattern, text, re.M))
        return next(iter(values)) if len(values) == 1 else None
    raw = unique(r'ACCEPTANCE-DATETIME[>\s:]+(\d{14})')
    filed = unique(r'FILED AS OF DATE[>\s:]+(\d{8})')
    acc = unique(r'ACCESSION NUMBER[>\s:]+(\d{10}-\d{2}-\d{6})')
    typ = unique(r'CONFORMED SUBMISSION TYPE[>\s:]+([^\s<]+)')
    ciks = {int(c) for c in re.findall(r'CENTRAL INDEX KEY[>\s:]+(\d+)', text)}
    contradictory = (acc != accession or typ != form or int(cik) not in ciks
                     or len(set(re.findall(r'ACCEPTANCE-DATETIME[>\s:]+(\d{14})', text))) > 1)
    return {'acceptance_raw': raw, 'FILED_AS_OF_DATE': filed,
            'source_chronology_contradictory': contradictory,
            'source_sha256': hashlib.sha256(body).hexdigest(),
            'source_acceptance_locator': 'ACCEPTANCE-DATETIME in archived accession SGML header',
            'header_CIKs': sorted(ciks), 'source_items': sorted(set(re.findall(r'<ITEMS>([0-9]+\.[0-9]+)', text)))}


def probe(raw, filed, sessions, *, evidence_sha256, scope=('2015-01-01', '2020-12-31'),
          contradictory=False, public_observed_utc=None):
    result = {'raw_acceptance': raw, 'FILED_AS_OF_DATE': filed, 'candidate_interpretations': [],
              'candidate_opens_utc': [], 'modeled_eligible_open_utc': None,
              'exact_public_available_at_utc': None, 'exact_public_availability': 'UNKNOWN',
              'timing_class': 'MODELED_ACCEPTANCE_BUFFERED_ELIGIBILITY', 'policy_activated': False,
              'trading_identity_certified': False}
    def unavailable(status):
        return dict(result, status=status, invariant=False)
    if raw is None or raw == '':
        return unavailable('UNAVAILABLE_ACCEPTANCE_MISSING')
    if contradictory:
        return unavailable('UNAVAILABLE_SOURCE_CHRONOLOGY')
    try:
        f = datetime.strptime(filed, '%Y%m%d').date() if '-' not in filed else date.fromisoformat(filed)
        start, end = map(date.fromisoformat, scope)
        a = acceptance(raw, evidence_sha256=evidence_sha256)
        result['acceptance_timezone_status'] = a['status']
        result['certified_acceptance_utc'] = a['accepted_at_utc']
        raw_date = datetime.strptime(raw, '%Y%m%d%H%M%S').date()
        if not start <= raw_date <= end or not start <= f <= end:
            return unavailable('UNAVAILABLE_SOURCE_CHRONOLOGY')
        # Earlier official filed date is permitted: the acceptance anchor dominates it.
        result['filed_precedes_raw_acceptance_date'] = f < raw_date
        for label, key in (('SEASONAL_EASTERN', 'candidate_eastern_utc'), ('LITERAL_EST', 'candidate_literal_est_utc')):
            at = datetime.fromisoformat(a[key]); civil = at.astimezone(NY).date()
            result['candidate_interpretations'].append({'interpretation': label, 'utc': at.isoformat(),
                                                       'civil_date_New_York': civil.isoformat()})
        days = [date.fromisoformat(s) if isinstance(s, str) else s for s in sessions]
        if not days or days != sorted(set(days)) or any(d.weekday() > 4 for d in days):
            return unavailable('UNAVAILABLE_CALENDAR')
        for candidate in result['candidate_interpretations']:
            anchor = max(f, date.fromisoformat(candidate['civil_date_New_York']))
            later = [d for d in days if d > anchor]
            if len(later) < 2:
                return unavailable('UNAVAILABLE_CALENDAR')
            result['candidate_opens_utc'].append(datetime.combine(later[1], time(9, 30), NY).astimezone(timezone.utc).isoformat())
        if len(set(result['candidate_opens_utc'])) != 1:
            return unavailable('UNAVAILABLE_TIMING_AMBIGUOUS')
        bound = datetime.fromisoformat(result['candidate_opens_utc'][0])
        if not all(bound > datetime.fromisoformat(c['utc']) for c in result['candidate_interpretations']):
            return unavailable('UNAVAILABLE_SOURCE_CHRONOLOGY')
        if public_observed_utc and datetime.fromisoformat(public_observed_utc) > bound:
            return unavailable('UNAVAILABLE_SOURCE_CHRONOLOGY')
        if bound.astimezone(NY).date() > end:
            return unavailable('UNAVAILABLE_CALENDAR')
        return dict(result, status='INVARIANT_MODELED_BOUND', invariant=True,
                    modeled_eligible_open_utc=bound.isoformat())
    except (ValueError, TypeError):
        return unavailable('UNAVAILABLE_SOURCE_CHRONOLOGY')
