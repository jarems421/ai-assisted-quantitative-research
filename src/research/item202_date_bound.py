"""Predeclared EXP006 civil-date envelope; no source, outcome or engine loader."""
from datetime import date, datetime, time, timezone
from html.parser import HTMLParser
import re
from zoneinfo import ZoneInfo

from src.research.sec_pilot.certification import acceptance

NY = ZoneInfo('America/New_York')
RULE = ('max(ISO lexical date, literal offset-aware ISO instant converted to '
        'America/New_York civil date, census filed date); second regular NYSE '
        'session strictly after envelope at 09:30 America/New_York')


def envelope(iso_value, filed_date, scope=('2015-01-01', '2020-12-31')):
    """Strict declared-offset parse; never infer a field's serialization mode."""
    if not isinstance(iso_value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', iso_value):
        raise ValueError('UNAVAILABLE_BULK_CLOCK')
    instant = datetime.fromisoformat(iso_value.replace('Z', '+00:00'))
    lexical = date.fromisoformat(iso_value[:10])
    civil = instant.astimezone(NY).date()
    filed = date.fromisoformat(filed_date)
    start, end = map(date.fromisoformat, scope)
    if not start <= filed <= end or not start <= lexical <= end:
        raise ValueError('UNAVAILABLE_OUTSIDE_DEVELOPMENT')
    result = max(lexical, civil, filed)
    if not start <= result <= end:
        raise ValueError('UNAVAILABLE_ENVELOPE_SCOPE')
    return {'lexical_date': lexical.isoformat(), 'literal_New_York_date': civil.isoformat(),
            'filed_date': filed.isoformat(), 'envelope_date': result.isoformat()}


def second_open(anchor, sessions, scope=('2015-01-01', '2020-12-31')):
    days = [date.fromisoformat(d) if isinstance(d, str) else d for d in sessions]
    if not days or days != sorted(set(days)) or any(d.weekday() > 4 for d in days):
        raise ValueError('UNAVAILABLE_CALENDAR')
    anchor = date.fromisoformat(anchor) if isinstance(anchor, str) else anchor
    if not date.fromisoformat(scope[0]) <= anchor <= date.fromisoformat(scope[1]):
        raise ValueError('UNAVAILABLE_OUTSIDE_DEVELOPMENT')
    if days[0] > anchor or days[-1] < anchor:
        raise ValueError('UNAVAILABLE_CALENDAR_COVERAGE')
    later = [d for d in days if d > anchor]
    if len(later) < 2 or later[1] > date.fromisoformat(scope[1]):
        raise ValueError('UNAVAILABLE_CALENDAR_END')
    return datetime.combine(later[1], time(9, 30), NY).astimezone(timezone.utc).isoformat()


def compare(iso_value, filed_date, raw, raw_filed, sessions, *, evidence_sha256,
            contradictory=False):
    result = {'status': 'UNAVAILABLE', 'exact_public_available_at_utc': None,
              'exact_public_availability': 'UNKNOWN', 'policy_activated': False,
              'timing_class': 'MODELED_CONSERVATIVE_BULK_DATE_ENVELOPE',
              'exact_clock_reconstructed': False, 'envelope_eligible_open': None}
    try:
        if contradictory or not raw or not raw_filed:
            raise ValueError('UNAVAILABLE_ORIGINAL_HEADER')
        raw_filed = datetime.strptime(raw_filed, '%Y%m%d').date()
        if raw_filed != date.fromisoformat(filed_date):
            raise ValueError('UNAVAILABLE_FILED_DATE_CONFLICT')
        raw_day = datetime.strptime(raw, '%Y%m%d%H%M%S').date()
        if not date(2015, 1, 1) <= raw_day <= date(2020, 12, 31):
            raise ValueError('UNAVAILABLE_OUTSIDE_DEVELOPMENT')
        e = envelope(iso_value, filed_date)
        a = acceptance(raw, evidence_sha256=evidence_sha256)
        instants = [datetime.fromisoformat(a[k]) for k in
                    ('candidate_eastern_utc', 'candidate_literal_est_utc')]
        raw_dates = [x.astimezone(NY).date() for x in instants]
        source_anchor = max(raw_filed, *raw_dates)
        result.update(e, raw_candidate_civil_dates=[d.isoformat() for d in raw_dates],
                      raw_candidate_utc=[d.isoformat() for d in instants],
                      raw_anchor_date=source_anchor.isoformat(),
                      raw_date_later_than_envelope=max(raw_dates) > date.fromisoformat(e['envelope_date']))
        new_open = second_open(e['envelope_date'], sessions)
        old_opens = [second_open(max(raw_filed, d), sessions) for d in raw_dates]
        old_latest = max(old_opens)
        result.update(envelope_eligible_open=new_open, raw_policy_candidate_opens=old_opens,
                      raw_v002_invariant=len(set(old_opens)) == 1,
                      earlier_eligible_open=new_open < old_latest)
        if result['raw_date_later_than_envelope'] or result['earlier_eligible_open']:
            return dict(result, status='FAIL_DATE_DOMINANCE')
        if not all(datetime.fromisoformat(new_open) > x for x in instants):
            return dict(result, status='FAIL_SOURCE_INSTANT_BOUND')
        local_old = datetime.fromisoformat(old_latest).astimezone(NY).date()
        local_new = datetime.fromisoformat(new_open).astimezone(NY).date()
        delay = sum(local_old < (date.fromisoformat(d) if isinstance(d, str) else d) <= local_new
                    for d in sessions)
        return dict(result, status='PASS_DATE_DOMINANCE', delay_sessions=delay,
                    eligible_open_relation='SAME' if delay == 0 else 'LATER')
    except (ValueError, TypeError, KeyError) as error:
        return dict(result, status='UNAVAILABLE', reason=str(error))


def freeze_before_performance(certificate, *, freeze_commit_pushed, stage):
    """No owner-held confirmation adapter, engine or stage-opening operation."""
    if stage != 'development':
        raise ValueError('Owner-held confirmation is inaccessible')
    if not freeze_commit_pushed or not certificate.get('all_mandatory_gates_passed'):
        raise ValueError('Pushed scientific freeze required before performance')


def confusion(rows):
    result = dict(TP=0, TN=0, FP=0, FN=0, UNKNOWN=0)
    for row in rows:
        prediction, truth = row['bulk_present'], row['primary_present']
        if prediction is None or truth is None:
            result['UNKNOWN'] += 1
        else:
            result[('T' if prediction == truth else 'F') + ('P' if prediction else 'N')] += 1
    result['sample_size'] = len(rows)
    result['coverage'] = (len(rows) - result['UNKNOWN']) / len(rows) if rows else 0
    return result


class FilingText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'tr', 'td', 'br'):
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def primary_item202(body):
    """Narrow item-title contract; cross references alone are not positives."""
    parser = FilingText()
    parser.feed(body.decode('utf-8', errors='strict'))
    text = re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()
    heading = re.search(r'\bItem\s*2\s*\.\s*02\s*[.\-:]?\s*'
                        r'Results\s+of\s+Operations\s+and\s+Financial\s+Condition\b', text, re.I)
    if heading:
        return {'present': True, 'locator': [heading.start(), heading.end()],
                'locator_basis': 'Normalized primary HTML text; source bytes hashed separately',
                'heading': heading.group()}
    if re.search(r'\bItem\s*2\s*\.\s*02\b', text, re.I):
        return {'present': None, 'reason': 'Item reference without certified title'}
    if re.search(r'\bItem\s*[1-9]\s*\.\s*\d{2}\b', text, re.I):
        return {'present': False, 'reason': 'Other item headings; no Item 2.02 reference'}
    return {'present': None, 'reason': 'No recognizable item structure'}


def exact_header_reconciliation(direct, recovered, *, cik, accession, form):
    from src.research.item202_availability import parse_header
    a = parse_header(direct, cik=cik, accession=accession, form=form)
    b = parse_header(recovered, cik=cik, accession=accession, form=form)
    fields = ('acceptance_raw', 'FILED_AS_OF_DATE', 'header_CIKs', 'source_items')
    return (not a['source_chronology_contradictory'] and not b['source_chronology_contradictory']
            and bool(a['acceptance_raw']) and all(a[k] == b[k] for k in fields))
