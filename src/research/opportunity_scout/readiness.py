"""Proposal feasibility, not evidence certification or Measurement Gate M."""
from urllib.parse import urlsplit
import re

from . import schema as S

VERSION = 'SCOUT_READY_V002'
REVIEW = S.obj({**S.REVIEW['properties'], 'readiness_version': {'const': VERSION}})


def identifiable(route, synthetic=False):
    """A syntactically identifiable collection/record; existence is a human question."""
    publisher, locator = route['publisher'].strip(), route['locator'].strip()
    if re.search(r'unknown|proposal.only|some original|tbd|placeholder|proposed .*publisher', publisher + ' ' + locator, re.I):
        return False
    try:
        url = urlsplit(locator)
        host = url.hostname or ''
        return bool(publisher and url.scheme in ('http', 'https') and '.' in host
                    and not url.username and not url.password and not url.fragment
                    and url.path.strip('/') and not re.search(r'[<>{}\s]', locator)
                    and (synthetic or not (host.endswith(('.invalid', '.example', '.test'))
                                           or host in ('example.com', 'example.org', 'example.net'))))
    except ValueError:
        return False


def feasibility_for(state, card):
    from .engine import source_restrictions
    stopped = {r['locator'] for r in source_restrictions(state, card)}
    for route in card['idea']['source_routes']:
        if route['locator'] in stopped or not identifiable(route, state.batch['fixture'] == 'SYNTHETIC'):
            continue
        current = next((r for r in reversed(state.feasibility) if r['idea_id'] == card['id']
                        and r['version'] == card['version'] and r['locator'] == route['locator']), None)
        if (current and current.get('readiness_version') == VERSION
                and current['reviewer']['kind'] in ('HUMAN', 'SYNTHETIC_FIXTURE')
                and current['publisher'] == route['publisher']
                and current['state'] in ('UNTESTED', 'DOCUMENTED_ROUTE')
                and route['state'] in ('UNTESTED', 'DOCUMENTED_ROUTE')
                and current['conclusion'] == 'RESEARCHABLE_PROPOSAL'
                and current['measurement_question'] == card['idea']['next_step']['question']):
            return current
    return None


def require_ready(state, card):
    from .engine import assess
    if assess(state, card)['checks']['checks']:
        raise S.ScoutError('unresolved structural warnings need correction before READY')
    finding = feasibility_for(state, card)
    if not finding:
        raise S.ScoutError('READY needs an identifiable publisher URL and a separate current-version human '
                           'feasibility assessment of the exact decisive next-step question')
    return finding
