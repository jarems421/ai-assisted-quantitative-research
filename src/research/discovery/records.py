"""Discovery Lab record vocabulary and single-record validation.

Every field is always present; an unknown fact is the explicit string UNKNOWN. Validation refuses
forbidden or internally inconsistent states (for example a first-public date inferred from a web
cache). Missing evidence is not an error here: the checklist reports it later as a blocker or gap.
"""
from __future__ import annotations

import re
from datetime import date, datetime

UNKNOWN = 'UNKNOWN'
METHODS = ('OBSERVATION_FIRST', 'RELATIONSHIP_FIRST', 'EVENT_FIRST', 'HYPOTHESIS_FIRST')
FIXTURES = ('SYNTHETIC', 'RETROSPECTIVE_INSPECTED', 'LIVE')
DEPTHS = ('VERIFIED_ORIGINAL_FIELD', 'VERIFIED_ORIGINAL_RECORD', 'INDEXED_DESCRIPTION_ONLY', 'SCHEMA_ONLY',
          'RETROSPECTIVE_DESCRIPTION', 'UNVERIFIED', 'ACCESS_BLOCKED')
ORIGINAL = DEPTHS[:2]
EVIDENCE_KINDS = ('ORIGINAL_DOCUMENT', 'PUBLICATION_RECORD', 'DATASET_ROW', 'NAME_MATCH', 'INDEX_ENTRY', 'SCHEMA',
                  'RETROSPECTIVE_ACCOUNT', 'SECONDARY_ANALYSIS')
ORIGINAL_KINDS = EVIDENCE_KINDS[:3]
ENTITY_TYPES = ('LISTED_COMPANY', 'LEGAL_ENTITY', 'FACILITY', 'ASSET', 'LEASE', 'CONTRACT', 'PRODUCT', 'PERMIT',
                'LICENCE', 'INFRASTRUCTURE', 'REGULATOR', 'COHORT', 'GEOGRAPHY', 'OTHER')
CLOCKS = ('economic_occurrence', 'first_public', 'source_version', 'retrieval')
CLOCK_BASES = ('PUBLICATION_RECORD', 'DOCUMENT_DATE', 'DATASET_VERSION', 'HTTP_HEADER', 'WEB_CACHE', 'FILENAME',
               'SEARCH_INDEX', 'RETRIEVAL_RECEIPT', 'RETROSPECTIVE_ACCOUNT', UNKNOWN)
AS_OF = ('VERIFIED_AS_OF', 'VERIFIED_ONLY_RETROSPECTIVELY', 'UNVERIFIED', 'CONTRADICTED')
OBSERVATION_KINDS = ('STATE_CHANGE', 'QUANTITY', 'EVENT', 'CONSTRAINT', 'MISMATCH', 'RIGHT_OR_OBLIGATION', 'OTHER')
RELATIONSHIP_TYPES = ('OWNERSHIP', 'OPERATION', 'SUPPLIER_CUSTOMER', 'LENDER_BORROWER', 'INSURER_INSURED',
                      'REGULATOR_LICENSEE', 'ASSET_OPERATOR', 'PREDECESSOR_OBLIGATION', 'INFRASTRUCTURE_DEPENDENCE',
                      'CONTRACT_COUNTERPARTY', 'SUBSTITUTE_CAPACITY', 'GUARANTEE', 'OTHER')
RELATIONSHIP_BASES = ('DOCUMENTED', 'NAME_MATCH_ONLY', 'INFERRED')
DOCUMENTED_ALLOCATION = ('DOCUMENTED_SHARE', 'CONTRACTUAL_AMOUNT', 'DIRECT_MEASUREMENT')
ASSUMED_ALLOCATION = ('PROPORTIONAL_ASSUMPTION', 'EQUAL_SPLIT', 'AGGREGATE_AS_COHORT')
ACCESS = ('OPEN', 'RESTRICTED', 'PAID', 'AUTHENTICATED', 'BLOCKED', UNKNOWN)
JOIN_DIMENSIONS = ('legal_entity', 'cohort', 'geography', 'period', 'accounting_basis')
OUTCOME_STATUS = ('OBSERVED_VALUE', 'ROUTE_ONLY', 'UNVERIFIED')
PROPOSITION_STATUS = ('UNTESTED', 'UNVERIFIED', 'SUPPORTED_BY_EVIDENCE', 'CONTRADICTED')
PROPOSITIONS = ('economic_effect', 'informational_advantage', 'residual_investment_value')
RECOMMENDATIONS = ('REQUEST_M_REVIEW', 'STOP', 'HOLD', 'VERIFY', 'OBSERVE_ONLY')
M_REQUIREMENTS = ('distinctive_predictor', 'meaning_and_units', 'separate_outcome', 'valid_join', 'public_time_route',
                  'financial_bridge')
JUDGMENTS = ('EVIDENCED', 'NOT_EVIDENCED', 'UNCERTAIN')
H_JUDGMENTS = ('PLAUSIBLE', 'NOT_ESTABLISHED', 'UNCONVINCING', 'UNCERTAIN')
SCEPTICS = ('measurement', 'economic', 'information', 'timing', 'selection', 'investment')
SCEPTIC_VERDICTS = ('CHALLENGE_UNRESOLVED', 'CHALLENGE_ANSWERED', 'FATAL_TO_CLAIM')
REVIEWERS = ('HUMAN', 'ASSISTANT', 'SYNTHETIC_FIXTURE')
NOT_CHECKED = ('COMPETITOR', 'HISTORICAL_SOURCE', 'OUTCOME', 'PUBLIC_TIME', 'OTHER')
DECISIONS = ('REJECT', 'HOLD', 'VERIFY', 'M_PASSED', 'LEVEL_A_DESIGN_CANDIDATE')
REASON_TYPES = ('ECONOMIC', 'OBSERVATION', 'COMPETITION', 'STRUCTURAL', 'HORIZON', 'TIMING', 'ACCESS', 'UNRESOLVED',
                'EVIDENCE_COMPLETE')
REJECT_REASONS = ('ECONOMIC', 'OBSERVATION', 'COMPETITION', 'STRUCTURAL', 'HORIZON', 'TIMING')
EFFORT_KINDS = ('ANALYST_TIME', 'SEARCH', 'SOURCE_START', 'DOCUMENT_REUSE')
EFFORT_OUTCOMES = ('SUCCESS', 'ERROR', 'ACCESS_DENIED', 'NOT_FOUND', 'PARTIAL', 'NOT_APPLICABLE')
PREFIX = {'campaign': 'DLC-', 'source': 'SRC-', 'observation': 'OBS-', 'relationship': 'REL-', 'candidate': 'CAND-',
          'review': 'REV-', 'disposition': 'DSP-', 'effort': 'EFF-'}
VERSIONED = ('source', 'observation', 'relationship', 'candidate')

# Claims about other investors' knowledge need checked evidence, never assertion.
UNSUPPORTED_NOVELTY = re.compile(
    r"\bno(?:body|\s+one)(?:\s+else)?\s+(?:has|knows|uses|discovered|noticed|tracks)\b|"
    r"\binstitutions?\s+(?:overlook|ignore|miss)|\bunknown\s+to\s+(?:the\s+)?(?:market|institutions|investors)\b|"
    r"\bproprietary\s+(?:edge|advantage)\b|\bfirst\s+to\s+(?:discover|find|identify)\b|\bguaranteed\b|"
    r"\brisk[- ]free\s+(?:profit|return)", re.I)

KEYS = {
    'campaign': ('id', 'title', 'method', 'fixture', 'question', 'authority', 'acquisition_authorized', 'budget', 'notes'),
    'source': ('id', 'version', 'supersedes', 'revision_reason', 'name', 'publisher', 'locator', 'family', 'domain',
               'formats', 'quantities', 'granularity', 'identifiers', 'history', 'revision_policy', 'publication_clock',
               'access', 'exposure_links', 'omissions', 'misleading_proxies', 'next_observation'),
    'observation': ('id', 'version', 'supersedes', 'revision_reason', 'source_id', 'kind', 'statement', 'value', 'units',
                    'denominator', 'entity', 'depth', 'evidence', 'clocks', 'as_of_status', 'why_informative',
                    'alternative_explanations', 'prior_disclosure', 'outcome_independent', 'related', 'missing_evidence'),
    'relationship': ('id', 'version', 'supersedes', 'revision_reason', 'source_entity', 'target_entity', 'type',
                     'direction', 'scope', 'period', 'basis', 'status', 'evidence', 'quantity_transfer', 'limitations',
                     'alternatives'),
    'candidate': ('id', 'version', 'supersedes', 'revision_reason', 'after_outcome_seen', 'method', 'entry_record',
                  'population', 'predictor', 'exposure', 'mechanism', 'outcome', 'joins', 'information_event',
                  'public_time_route', 'horizon', 'closest_substitute', 'increment', 'falsification',
                  'missing_variables', 'selection', 'propositions', 'recommendation'),
    'review': ('id', 'candidate_id', 'version', 'kind', 'role', 'reviewer', 'judgments', 'checked', 'not_checked',
               'conclusion'),
    'disposition': ('id', 'candidate_id', 'version', 'decision', 'reason_type', 'reason', 'scope', 'decided_by',
                    'verify', 'authorizes'),
    'effort': ('id', 'candidate_id', 'kind', 'description', 'analyst_minutes', 'source_starts', 'bytes', 'outcome',
               'receipt', 'targeted_variable'),
}
EVIDENCE_KEYS = ('locator', 'kind', 'depth', 'passage', 'sha256', 'archive', 'synthetic', 'reused_from')


class RecordError(ValueError):
    """A record that must not enter the ledger."""


def fail(where, message):
    raise RecordError(f'{where}: {message}')


def exact(value, keys, where):
    if not isinstance(value, dict):fail(where, 'expected an object')
    missing = [k for k in keys if k not in value]; extra = [k for k in value if k not in keys]
    if missing or extra:fail(where, f'missing {missing} / unexpected {extra}; use UNKNOWN rather than omitting')


def text(value, where, allow_unknown=True):
    if not isinstance(value, str) or not value.strip():fail(where, 'non-empty text required')
    if value == UNKNOWN and not allow_unknown:fail(where, 'cannot be UNKNOWN')
    return value


def choice(value, options, where):
    if value not in options:fail(where, f'{value!r} not in {options}')
    return value


def texts(value, where):
    if not isinstance(value, list):fail(where, 'list required (may be empty)')
    for i, item in enumerate(value):text(item, f'{where}[{i}]')
    return value


def boolean(value, where, allow_unknown=False):
    if value is True or value is False or (allow_unknown and value == UNKNOWN):return value
    fail(where, 'true/false required' + (' or UNKNOWN' if allow_unknown else ''))


def number(value, where, allow_unknown=True, integer=False):
    if allow_unknown and value == UNKNOWN:return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or (integer and not isinstance(value, int)):
        fail(where, 'non-negative ' + ('integer' if integer else 'number') + (' or UNKNOWN' if allow_unknown else ''))
    return value


def when(value, where):
    """ISO date or timezone-aware datetime, or UNKNOWN. Returns a sortable key or None."""
    if value == UNKNOWN:return None
    if not isinstance(value, str):fail(where, 'ISO date/datetime or UNKNOWN required')
    try:
        if len(value) == 10:return date.fromisoformat(value).isoformat()
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        fail(where, f'unparseable date {value!r}')
    if parsed.tzinfo is None:fail(where, 'datetime must carry a timezone')
    return parsed.isoformat()


def before(a, b):
    """a <= b at the coarsest shared granularity; None if either is unknown."""
    if a is None or b is None:return None
    if len(a) == 10 or len(b) == 10:return a[:10] <= b[:10]
    return datetime.fromisoformat(a) <= datetime.fromisoformat(b)


def evidence(items, where, fixture):
    if not isinstance(items, list):fail(where, 'evidence list required (may be empty)')
    for i, e in enumerate(items):
        w = f'{where}[{i}]'; exact(e, EVIDENCE_KEYS, w); text(e['locator'], w + '.locator', False)
        choice(e['kind'], EVIDENCE_KINDS, w + '.kind'); choice(e['depth'], DEPTHS, w + '.depth'); text(e['passage'], w + '.passage')
        boolean(e['synthetic'], w + '.synthetic')
        if e['sha256'] is not None and not re.fullmatch(r'[0-9a-f]{64}', str(e['sha256'])):fail(w, 'sha256 must be 64 lowercase hex or null')
        if e['depth'] in ORIGINAL:
            if e['kind'] not in ORIGINAL_KINDS:fail(w, f"{e['kind']} cannot be original-depth evidence")
            if not e['sha256'] and not e['archive']:fail(w, 'original-depth evidence needs a sha256 or archive pointer')
        if fixture == 'SYNTHETIC' and not e['synthetic']:fail(w, 'synthetic campaigns may contain only synthetic evidence')
        if fixture != 'SYNTHETIC' and e['synthetic']:fail(w, 'synthetic evidence is forbidden outside synthetic campaigns')
        if fixture == 'RETROSPECTIVE_INSPECTED' and not e['reused_from']:fail(w, 'retrospective evidence must cite the repository record it reuses')
    return items


def supported(depth, items):
    """True when a declared original depth is backed by original evidence."""
    return depth not in ORIGINAL or any(e['depth'] in ORIGINAL for e in items)


def depth_claim(value, where, fixture, extra=()):
    exact(value, ('depth', 'evidence', *extra), where); choice(value['depth'], DEPTHS, where + '.depth')
    evidence(value['evidence'], where + '.evidence', fixture)
    if not supported(value['depth'], value['evidence']):fail(where, 'original depth declared without original evidence')


def entity(value, where):
    exact(value, ('type', 'id', 'name'), where); choice(value['type'], ENTITY_TYPES, where + '.type')
    if not isinstance(value['id'], str) or not re.fullmatch(r'[A-Z][A-Z0-9_]*:\S.*', value['id']):
        fail(where + '.id', 'use SCHEME:value (NAME:... marks a name-only, unidentified entity)')
    text(value['name'], where + '.name')


def named_only(e):
    return e['id'].startswith('NAME:')


def quantity(value, where):
    """Number, text state, {from,to} change or UNKNOWN."""
    if value == UNKNOWN or (isinstance(value, str) and value.strip()):return
    if isinstance(value, (int, float)) and not isinstance(value, bool):return
    if isinstance(value, dict) and set(value) == {'from', 'to'}:
        for k in ('from', 'to'):quantity(value[k], f'{where}.{k}')
        return
    fail(where, 'number, text, {from,to} or UNKNOWN required')


def numeric(value):
    if isinstance(value, dict):return any(numeric(v) for v in value.values())
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def versioning(r, where):
    if type(r['version']) is not int or r['version'] < 1:fail(where, 'version must be a positive integer')
    if r['version'] == 1:
        if r['supersedes'] is not None or r['revision_reason'] is not None:fail(where, 'version 1 has no supersedes/revision_reason')
    elif r['supersedes'] != r['version'] - 1 or not isinstance(r['revision_reason'], str) or not r['revision_reason'].strip():
        fail(where, 'a new version must supersede the previous version and state why it changed')


def strings(value):
    if isinstance(value, str):yield value
    elif isinstance(value, dict):
        for v in value.values():yield from strings(v)
    elif isinstance(value, list):
        for v in value:yield from strings(v)


def no_novelty_claims(record, where):
    for s in strings(record):
        if UNSUPPORTED_NOVELTY.search(s):
            fail(where, f'unsupported novelty/competition claim {s[:80]!r}; state what was checked and keep private use UNKNOWN')


def campaign(r, fixture=None):
    w = 'campaign'; exact(r, KEYS['campaign'], w)
    for k in ('title', 'question', 'authority'):text(r[k], f'{w}.{k}', False)
    choice(r['method'], METHODS, w + '.method'); choice(r['fixture'], FIXTURES, w + '.fixture')
    boolean(r['acquisition_authorized'], w + '.acquisition_authorized'); texts(r['notes'], w + '.notes')
    exact(r['budget'], ('analyst_hours', 'source_starts', 'external_bytes'), w + '.budget')
    number(r['budget']['analyst_hours'], w + '.budget.analyst_hours', False)
    for k in ('source_starts', 'external_bytes'):number(r['budget'][k], f'{w}.budget.{k}', False, True)
    if r['fixture'] != 'LIVE' and (r['acquisition_authorized'] or r['budget']['source_starts'] or r['budget']['external_bytes']):
        fail(w, 'synthetic or retrospective campaigns cannot authorise acquisition')
    if not r['acquisition_authorized'] and (r['budget']['source_starts'] or r['budget']['external_bytes']):
        fail(w, 'an acquisition budget requires acquisition_authorized with a cited owner authority')


def source(r, fixture):
    w = f"source {r.get('id')}"; exact(r, KEYS['source'], w); versioning(r, w)
    for k in ('name', 'publisher', 'locator', 'family', 'domain', 'granularity', 'next_observation'):text(r[k], f'{w}.{k}')
    for k in ('formats', 'exposure_links', 'omissions', 'misleading_proxies'):texts(r[k], f'{w}.{k}')
    if not isinstance(r['quantities'], list):fail(w, 'quantities list required')
    for i, q in enumerate(r['quantities']):
        qw = f'{w}.quantities[{i}]'; depth_claim(q, qw, fixture, ('field', 'meaning', 'units', 'denominator'))
        for k in ('field', 'meaning', 'units', 'denominator'):text(q[k], f'{qw}.{k}')
    if not isinstance(r['identifiers'], list):fail(w, 'identifiers list required')
    for i, q in enumerate(r['identifiers']):
        qw = f'{w}.identifiers[{i}]'; depth_claim(q, qw, fixture, ('scheme', 'object_type'))
        text(q['scheme'], qw + '.scheme'); choice(q['object_type'], ENTITY_TYPES, qw + '.object_type')
    depth_claim(r['history'], w + '.history', fixture, ('coverage',)); text(r['history']['coverage'], w + '.history.coverage')
    depth_claim(r['revision_policy'], w + '.revision_policy', fixture, ('description',))
    text(r['revision_policy']['description'], w + '.revision_policy.description')
    depth_claim(r['publication_clock'], w + '.publication_clock', fixture, ('description', 'frequency', 'release_lag'))
    for k in ('description', 'frequency', 'release_lag'):text(r['publication_clock'][k], f'{w}.publication_clock.{k}')
    exact(r['access'], ('status', 'permitted_use', 'evidence'), w + '.access'); choice(r['access']['status'], ACCESS, w + '.access.status')
    text(r['access']['permitted_use'], w + '.access.permitted_use'); evidence(r['access']['evidence'], w + '.access.evidence', fixture)
    no_novelty_claims(r, w)


def clock(name, value, where, fixture):
    exact(value, ('value', 'basis', 'evidence'), where); key = when(value['value'], where + '.value')
    choice(value['basis'], CLOCK_BASES, where + '.basis'); evidence(value['evidence'], where + '.evidence', fixture)
    if (key is None) != (value['basis'] == UNKNOWN):fail(where, 'basis must be UNKNOWN exactly when the value is UNKNOWN')
    if name == 'first_public' and key is not None:
        if value['basis'] != 'PUBLICATION_RECORD':
            fail(where, f"first-public time cannot be inferred from {value['basis']}; keep it UNKNOWN")
        if not any(e['kind'] == 'PUBLICATION_RECORD' and e['depth'] in ORIGINAL for e in value['evidence']):
            fail(where, 'a first-public time needs an original publication-record certificate')
    if name == 'retrieval' and key is not None and value['basis'] != 'RETRIEVAL_RECEIPT':
        fail(where, 'a retrieval time must come from a retrieval receipt')
    return key


def observation(r, fixture):
    w = f"observation {r.get('id')}"; exact(r, KEYS['observation'], w); versioning(r, w)
    text(r['source_id'], w + '.source_id', False); choice(r['kind'], OBSERVATION_KINDS, w + '.kind')
    for k in ('statement', 'why_informative', 'prior_disclosure', 'denominator'):text(r[k], f'{w}.{k}')
    quantity(r['value'], w + '.value'); text(r['units'], w + '.units')  # UNKNOWN units are a checklist blocker
    entity(r['entity'], w + '.entity'); choice(r['depth'], DEPTHS, w + '.depth'); evidence(r['evidence'], w + '.evidence', fixture)
    if not supported(r['depth'], r['evidence']):fail(w, 'original depth declared without original, provenance-bearing evidence')
    exact(r['clocks'], CLOCKS, w + '.clocks')
    keys = {name: clock(name, r['clocks'][name], f'{w}.clocks.{name}', fixture) for name in CLOCKS}
    if before(keys['first_public'], keys['retrieval']) is False:fail(w, 'first public time cannot follow our retrieval')
    if before(keys['source_version'], keys['retrieval']) is False:fail(w, 'source version cannot follow our retrieval')
    choice(r['as_of_status'], AS_OF, w + '.as_of_status')
    if r['as_of_status'] == 'VERIFIED_AS_OF' and keys['first_public'] is None:
        fail(w, 'VERIFIED_AS_OF requires a certified first-public time; use VERIFIED_ONLY_RETROSPECTIVELY or UNVERIFIED')
    if r['as_of_status'] in ('VERIFIED_AS_OF', 'VERIFIED_ONLY_RETROSPECTIVELY') and r['depth'] not in ORIGINAL:
        fail(w, f"{r['as_of_status']} requires original-depth evidence")
    for k in ('alternative_explanations', 'related', 'missing_evidence'):texts(r[k], f'{w}.{k}')
    boolean(r['outcome_independent'], w + '.outcome_independent', True); no_novelty_claims(r, w)


def relationship(r, fixture):
    w = f"relationship {r.get('id')}"; exact(r, KEYS['relationship'], w); versioning(r, w)
    entity(r['source_entity'], w + '.source_entity'); entity(r['target_entity'], w + '.target_entity')
    choice(r['type'], RELATIONSHIP_TYPES, w + '.type'); text(r['direction'], w + '.direction')
    exact(r['scope'], ('asset', 'contract', 'product', 'geography'), w + '.scope')
    for k, v in r['scope'].items():text(v, f'{w}.scope.{k}')
    exact(r['period'], ('start', 'end'), w + '.period'); start = when(r['period']['start'], w + '.period.start')
    end = None if r['period']['end'] == 'OPEN' else when(r['period']['end'], w + '.period.end')
    if before(start, end) is False:fail(w, 'relationship period ends before it starts')
    choice(r['basis'], RELATIONSHIP_BASES, w + '.basis'); choice(r['status'], ('VERIFIED', 'UNVERIFIED', 'CONTRADICTED'), w + '.status')
    evidence(r['evidence'], w + '.evidence', fixture)
    if r['status'] == 'VERIFIED':
        if r['basis'] != 'DOCUMENTED':fail(w, f"a {r['basis']} relationship cannot be VERIFIED; coincident names establish nothing")
        if not any(e['depth'] in ORIGINAL and e['kind'] in ORIGINAL_KINDS for e in r['evidence']):
            fail(w, 'VERIFIED needs original documentary evidence of the relationship itself')
        if named_only(r['source_entity']) or named_only(r['target_entity']):fail(w, 'VERIFIED needs identified (non-NAME:) entities')
    q = r['quantity_transfer']; exact(q, ('status', 'method', 'evidence', 'note'), w + '.quantity_transfer')
    choice(q['status'], ('VERIFIED', 'UNVERIFIED', 'NOT_APPLICABLE'), w + '.quantity_transfer.status')
    choice(q['method'], (*DOCUMENTED_ALLOCATION, *ASSUMED_ALLOCATION, 'NONE'), w + '.quantity_transfer.method')
    evidence(q['evidence'], w + '.quantity_transfer.evidence', fixture); text(q['note'], w + '.quantity_transfer.note')
    if q['status'] == 'VERIFIED' and (q['method'] not in DOCUMENTED_ALLOCATION or not any(e['depth'] in ORIGINAL for e in q['evidence'])):
        fail(w, 'an allocation is VERIFIED only by documented original evidence; assumed/proportional splits stay UNVERIFIED')
    for k in ('limitations', 'alternatives'):texts(r[k], f'{w}.{k}')
    no_novelty_claims(r, w)


def amount(value, where):
    if value == UNKNOWN:return
    exact(value, ('value', 'units'), where); number(value['value'], where + '.value', False); text(value['units'], where + '.units', False)


def candidate(r, fixture):
    w = f"candidate {r.get('id')}"; exact(r, KEYS['candidate'], w); versioning(r, w)
    boolean(r['after_outcome_seen'], w + '.after_outcome_seen'); choice(r['method'], METHODS, w + '.method')
    if r['entry_record'] is not None:text(r['entry_record'], w + '.entry_record', False)
    for k in ('population', 'mechanism', 'public_time_route', 'horizon', 'increment', 'falsification'):text(r[k], f'{w}.{k}')
    p = r['predictor']; exact(p, ('observation_ids', 'quantity', 'units', 'transformation'), w + '.predictor')
    texts(p['observation_ids'], w + '.predictor.observation_ids')
    for k in ('quantity', 'units', 'transformation'):text(p[k], f'{w}.predictor.{k}')
    x = r['exposure']; exact(x, ('company', 'relationship_ids', 'claim_basis', 'allocation_required', 'gross', 'net', 'materiality'), w + '.exposure')
    entity(x['company'], w + '.exposure.company'); texts(x['relationship_ids'], w + '.exposure.relationship_ids')
    choice(x['claim_basis'], ('GROSS', 'NET', 'NOT_MONETARY'), w + '.exposure.claim_basis')
    boolean(x['allocation_required'], w + '.exposure.allocation_required')
    amount(x['gross'], w + '.exposure.gross'); amount(x['net'], w + '.exposure.net'); text(x['materiality'], w + '.exposure.materiality')
    o = r['outcome']; exact(o, ('quantity', 'units', 'route', 'source_id', 'status', 'value', 'derived_from_observations', 'evidence', 'independence'), w + '.outcome')
    for k in ('quantity', 'units', 'route', 'source_id', 'independence'):text(o[k], f'{w}.outcome.{k}')
    choice(o['status'], OUTCOME_STATUS, w + '.outcome.status'); quantity(o['value'], w + '.outcome.value')
    texts(o['derived_from_observations'], w + '.outcome.derived_from_observations'); evidence(o['evidence'], w + '.outcome.evidence', fixture)
    if o['status'] == 'OBSERVED_VALUE' and (o['value'] == UNKNOWN or not any(e['depth'] in ORIGINAL for e in o['evidence'])):
        fail(w, 'OBSERVED_VALUE needs a recorded value and original evidence')
    copied = set(o['derived_from_observations']) & set(p['observation_ids'])
    if copied:fail(w, f'outcome is derived from predictor observations {sorted(copied)}; it is not independent')
    if UNKNOWN not in (o['quantity'], p['quantity']) and norm(o['quantity']) == norm(p['quantity']):
        fail(w, 'outcome repeats the predictor quantity; name a separately recorded consequence')
    exact(r['joins'], JOIN_DIMENSIONS, w + '.joins')
    for k, j in r['joins'].items():
        jw = f'{w}.joins.{k}'; exact(j, ('status', 'evidence', 'note'), jw)
        choice(j['status'], ('VERIFIED', 'UNVERIFIED', 'NOT_REQUIRED'), jw + '.status'); evidence(j['evidence'], jw + '.evidence', fixture); text(j['note'], jw + '.note')
        if j['status'] == 'VERIFIED' and not any(e['depth'] in ORIGINAL for e in j['evidence']):fail(jw, 'a VERIFIED join needs original evidence')
    i = r['information_event']; exact(i, ('description', 'decision_time', 'basis'), w + '.information_event')
    text(i['description'], w + '.information_event.description'); when(i['decision_time'], w + '.information_event.decision_time')
    text(i['basis'], w + '.information_event.basis')
    c = r['closest_substitute']; exact(c, ('description', 'checked', 'evidence', 'not_checked_reason'), w + '.closest_substitute')
    text(c['description'], w + '.closest_substitute.description'); boolean(c['checked'], w + '.closest_substitute.checked')
    evidence(c['evidence'], w + '.closest_substitute.evidence', fixture)
    if c['checked'] and not c['evidence']:fail(w, 'a checked substitute must cite what was checked')
    if not c['checked'] and not (isinstance(c['not_checked_reason'], str) and c['not_checked_reason'].strip()):
        fail(w, 'state explicitly why the closest substitute was not checked')
    texts(r['missing_variables'], w + '.missing_variables')
    s = r['selection']; exact(s, ('famous_case', 'purposive_control', 'outcome_inspected_before_freeze', 'returns_inspected', 'prior_related_claims', 'notes'), w + '.selection')
    boolean(s['famous_case'], w + '.selection.famous_case'); boolean(s['purposive_control'], w + '.selection.purposive_control')
    boolean(s['outcome_inspected_before_freeze'], w + '.selection.outcome_inspected_before_freeze', True)
    if s['returns_inspected'] is not False:fail(w, 'discovery never inspects security returns; returns_inspected must be false')
    texts(s['prior_related_claims'], w + '.selection.prior_related_claims'); text(s['notes'], w + '.selection.notes')
    exact(r['propositions'], PROPOSITIONS, w + '.propositions')
    for k, v in r['propositions'].items():
        exact(v, ('statement', 'status'), f'{w}.propositions.{k}'); text(v['statement'], f'{w}.propositions.{k}.statement')
        choice(v['status'], PROPOSITION_STATUS, f'{w}.propositions.{k}.status')
    exact(r['recommendation'], ('action', 'reason'), w + '.recommendation')
    choice(r['recommendation']['action'], RECOMMENDATIONS, w + '.recommendation.action'); text(r['recommendation']['reason'], w + '.recommendation.reason')
    no_novelty_claims(r, w)


def norm(value):
    return re.sub(r'\W+', ' ', value.lower()).strip()


def review(r, fixture):
    w = f"review {r.get('id')}"; exact(r, KEYS['review'], w); text(r['candidate_id'], w + '.candidate_id', False)
    if type(r['version']) is not int or r['version'] < 1:fail(w, 'version must be a positive integer')
    choice(r['kind'], ('M', 'H', 'SCEPTIC'), w + '.kind')
    exact(r['reviewer'], ('name', 'kind'), w + '.reviewer'); text(r['reviewer']['name'], w + '.reviewer.name', False)
    choice(r['reviewer']['kind'], REVIEWERS, w + '.reviewer.kind'); reviewer_allowed(r['reviewer']['kind'], fixture, w)
    j = r['judgments']
    if r['kind'] == 'M':
        if r['role'] is not None:fail(w, 'M reviews have no sceptic role')
        exact(j, M_REQUIREMENTS, w + '.judgments')
        for k, v in j.items():
            exact(v, ('judgment', 'reason', 'evidence_refs'), f'{w}.judgments.{k}'); choice(v['judgment'], JUDGMENTS, f'{w}.judgments.{k}.judgment')
            text(v['reason'], f'{w}.judgments.{k}.reason', False); texts(v['evidence_refs'], f'{w}.judgments.{k}.evidence_refs')
            if v['judgment'] == 'EVIDENCED' and not v['evidence_refs']:fail(w, f'{k}: EVIDENCED must cite evidence')
    elif r['kind'] == 'H':
        if r['role'] is not None:fail(w, 'H reviews have no sceptic role')
        exact(j, ('judgment', 'information_event', 'expectation_mechanism', 'reason'), w + '.judgments')
        choice(j['judgment'], H_JUDGMENTS, w + '.judgments.judgment')
        for k in ('information_event', 'expectation_mechanism', 'reason'):text(j[k], f'{w}.judgments.{k}')
    else:
        choice(r['role'], SCEPTICS, w + '.role'); exact(j, ('challenges', 'verdict', 'reason'), w + '.judgments')
        texts(j['challenges'], w + '.judgments.challenges'); choice(j['verdict'], SCEPTIC_VERDICTS, w + '.judgments.verdict')
        text(j['reason'], w + '.judgments.reason', False)
    if not isinstance(r['checked'], list):fail(w, 'checked list required')
    for i, c in enumerate(r['checked']):
        exact(c, ('item', 'evidence_refs'), f'{w}.checked[{i}]'); text(c['item'], f'{w}.checked[{i}].item', False); texts(c['evidence_refs'], f'{w}.checked[{i}].evidence_refs')
    if not isinstance(r['not_checked'], list):fail(w, 'not_checked list required')
    for i, c in enumerate(r['not_checked']):
        exact(c, ('category', 'note'), f'{w}.not_checked[{i}]'); choice(c['category'], NOT_CHECKED, f'{w}.not_checked[{i}].category'); text(c['note'], f'{w}.not_checked[{i}].note', False)
    text(r['conclusion'], w + '.conclusion', False); no_novelty_claims(r, w)


def reviewer_allowed(kind, fixture, where):
    if kind == 'SYNTHETIC_FIXTURE' and fixture != 'SYNTHETIC':fail(where, 'synthetic reviewers exist only in synthetic campaigns')
    if fixture == 'SYNTHETIC' and kind == 'HUMAN':fail(where, 'synthetic campaigns use SYNTHETIC_FIXTURE stand-ins, never real human decisions')


def human_equivalent(kind, fixture):
    return kind == ('SYNTHETIC_FIXTURE' if fixture == 'SYNTHETIC' else 'HUMAN')


def disposition(r, fixture):
    w = f"disposition {r.get('id')}"; exact(r, KEYS['disposition'], w); text(r['candidate_id'], w + '.candidate_id', False)
    if type(r['version']) is not int or r['version'] < 1:fail(w, 'version must be a positive integer')
    choice(r['decision'], DECISIONS, w + '.decision'); choice(r['reason_type'], REASON_TYPES, w + '.reason_type')
    text(r['reason'], w + '.reason', False); text(r['scope'], w + '.scope', False)
    exact(r['decided_by'], ('name', 'kind'), w + '.decided_by'); text(r['decided_by']['name'], w + '.decided_by.name', False)
    choice(r['decided_by']['kind'], REVIEWERS, w + '.decided_by.kind'); reviewer_allowed(r['decided_by']['kind'], fixture, w)
    if not human_equivalent(r['decided_by']['kind'], fixture):fail(w, 'dispositions are human decisions; an assistant may only recommend')
    if r['authorizes'] != []:fail(w, 'a discovery disposition authorises nothing; authorizes must be []')
    if r['decision'] == 'REJECT' and r['reason_type'] not in REJECT_REASONS:
        fail(w, 'access limits or unresolved questions are HOLD, not REJECT')
    if r['decision'] == 'VERIFY':
        v = r['verify']; exact(v, ('decisive_question', 'proposed_check', 'cost', 'authority'), w + '.verify')
        text(v['decisive_question'], w + '.verify.decisive_question', False); text(v['proposed_check'], w + '.verify.proposed_check', False)
        exact(v['cost'], ('analyst_hours', 'source_starts', 'bytes'), w + '.verify.cost')
        for k in ('analyst_hours', 'source_starts', 'bytes'):number(v['cost'][k], f'{w}.verify.cost.{k}')
        if v['authority'] != 'PROPOSAL_ONLY':fail(w, 'a VERIFY check is a proposal; separate authority is required to run it')
    elif r['verify'] is not None:fail(w, 'only VERIFY carries a verify proposal')
    no_novelty_claims(r, w)


def effort(r, fixture):
    w = f"effort {r.get('id')}"; exact(r, KEYS['effort'], w)
    if r['candidate_id'] is not None:text(r['candidate_id'], w + '.candidate_id', False)
    choice(r['kind'], EFFORT_KINDS, w + '.kind'); text(r['description'], w + '.description', False)
    number(r['analyst_minutes'], w + '.analyst_minutes'); number(r['source_starts'], w + '.source_starts', True, True)
    number(r['bytes'], w + '.bytes', True, True); choice(r['outcome'], EFFORT_OUTCOMES, w + '.outcome')
    if r['receipt'] is not None:text(r['receipt'], w + '.receipt', False)
    if r['targeted_variable'] is not None:text(r['targeted_variable'], w + '.targeted_variable', False)
    if r['kind'] == 'SOURCE_START' and (r['source_starts'] in (0, UNKNOWN) or r['receipt'] is None):
        fail(w, 'a source start records its count and points to its acquisition receipt')
    if r['kind'] != 'SOURCE_START' and r['source_starts'] not in (0, UNKNOWN):fail(w, 'only SOURCE_START efforts count source starts')
    if r['kind'] == 'DOCUMENT_REUSE' and (r['bytes'] != 0 or r['receipt'] is None):
        fail(w, 'reused repository evidence acquires no bytes and cites its existing receipt')


VALIDATORS = {'campaign': campaign, 'source': source, 'observation': observation, 'relationship': relationship,
              'candidate': candidate, 'review': review, 'disposition': disposition, 'effort': effort}


def validate(kind, record, fixture):
    """Single-record validation; cross-record rules live in the ledger."""
    if kind not in VALIDATORS:fail('record', f'unknown record type {kind!r}')
    if not isinstance(record, dict) or not isinstance(record.get('id'), str) or not record['id'].startswith(PREFIX[kind]):
        fail(kind, f'id must start with {PREFIX[kind]}')
    if not re.fullmatch(r'[A-Z]+-[A-Za-z0-9_.-]+', record['id']):fail(kind, 'id may contain only letters, digits, _ . -')
    VALIDATORS[kind](record, fixture)


def template(kind):
    """A blank record whose every field must be completed or left explicitly UNKNOWN."""
    ev = {'locator': 'UNKNOWN', 'kind': 'ORIGINAL_DOCUMENT', 'depth': 'UNVERIFIED', 'passage': 'UNKNOWN', 'sha256': None,
          'archive': None, 'synthetic': False, 'reused_from': None}
    unknown_clock = {'value': UNKNOWN, 'basis': UNKNOWN, 'evidence': []}
    claim = lambda **extra: {'depth': 'UNVERIFIED', 'evidence': [], **extra}
    blank = {
        'campaign': {'id': 'DLC-', 'title': '', 'method': 'OBSERVATION_FIRST', 'fixture': 'LIVE', 'question': '',
                     'authority': 'docs/strategy/owner_...md', 'acquisition_authorized': False,
                     'budget': {'analyst_hours': 0, 'source_starts': 0, 'external_bytes': 0}, 'notes': []},
        'source': {'id': 'SRC-', 'version': 1, 'supersedes': None, 'revision_reason': None, 'name': UNKNOWN,
                   'publisher': UNKNOWN, 'locator': UNKNOWN, 'family': UNKNOWN, 'domain': UNKNOWN, 'formats': [],
                   'quantities': [claim(field=UNKNOWN, meaning=UNKNOWN, units=UNKNOWN, denominator=UNKNOWN)],
                   'granularity': UNKNOWN, 'identifiers': [], 'history': claim(coverage=UNKNOWN),
                   'revision_policy': claim(description=UNKNOWN),
                   'publication_clock': claim(description=UNKNOWN, frequency=UNKNOWN, release_lag=UNKNOWN),
                   'access': {'status': UNKNOWN, 'permitted_use': UNKNOWN, 'evidence': []}, 'exposure_links': [],
                   'omissions': [], 'misleading_proxies': [], 'next_observation': UNKNOWN},
        'observation': {'id': 'OBS-', 'version': 1, 'supersedes': None, 'revision_reason': None, 'source_id': 'SRC-',
                        'kind': 'QUANTITY', 'statement': UNKNOWN, 'value': UNKNOWN, 'units': UNKNOWN,
                        'denominator': UNKNOWN, 'entity': {'type': 'OTHER', 'id': 'NAME:unidentified', 'name': UNKNOWN},
                        'depth': 'UNVERIFIED', 'evidence': [ev], 'clocks': {c: dict(unknown_clock) for c in CLOCKS},
                        'as_of_status': 'UNVERIFIED', 'why_informative': UNKNOWN, 'alternative_explanations': [],
                        'prior_disclosure': UNKNOWN, 'outcome_independent': UNKNOWN, 'related': [], 'missing_evidence': []},
        'relationship': {'id': 'REL-', 'version': 1, 'supersedes': None, 'revision_reason': None,
                         'source_entity': {'type': 'OTHER', 'id': 'NAME:unidentified', 'name': UNKNOWN},
                         'target_entity': {'type': 'LISTED_COMPANY', 'id': 'NAME:unidentified', 'name': UNKNOWN},
                         'type': 'OTHER', 'direction': UNKNOWN,
                         'scope': {'asset': UNKNOWN, 'contract': UNKNOWN, 'product': UNKNOWN, 'geography': UNKNOWN},
                         'period': {'start': UNKNOWN, 'end': UNKNOWN}, 'basis': 'INFERRED', 'status': 'UNVERIFIED',
                         'evidence': [], 'quantity_transfer': {'status': 'UNVERIFIED', 'method': 'NONE', 'evidence': [], 'note': UNKNOWN},
                         'limitations': [], 'alternatives': []},
        'candidate': {'id': 'CAND-', 'version': 1, 'supersedes': None, 'revision_reason': None, 'after_outcome_seen': False,
                      'method': 'OBSERVATION_FIRST', 'entry_record': None, 'population': UNKNOWN,
                      'predictor': {'observation_ids': [], 'quantity': UNKNOWN, 'units': UNKNOWN, 'transformation': 'NONE'},
                      'exposure': {'company': {'type': 'LISTED_COMPANY', 'id': 'NAME:unidentified', 'name': UNKNOWN},
                                   'relationship_ids': [], 'claim_basis': 'GROSS', 'allocation_required': False,
                                   'gross': UNKNOWN, 'net': UNKNOWN, 'materiality': UNKNOWN},
                      'mechanism': UNKNOWN,
                      'outcome': {'quantity': UNKNOWN, 'units': UNKNOWN, 'route': UNKNOWN, 'source_id': UNKNOWN,
                                  'status': 'UNVERIFIED', 'value': UNKNOWN, 'derived_from_observations': [], 'evidence': [],
                                  'independence': UNKNOWN},
                      'joins': {d: {'status': 'UNVERIFIED', 'evidence': [], 'note': UNKNOWN} for d in JOIN_DIMENSIONS},
                      'information_event': {'description': UNKNOWN, 'decision_time': UNKNOWN, 'basis': UNKNOWN},
                      'public_time_route': UNKNOWN, 'horizon': UNKNOWN,
                      'closest_substitute': {'description': UNKNOWN, 'checked': False, 'evidence': [], 'not_checked_reason': 'Not yet checked.'},
                      'increment': UNKNOWN, 'falsification': UNKNOWN, 'missing_variables': [],
                      'selection': {'famous_case': False, 'purposive_control': False, 'outcome_inspected_before_freeze': UNKNOWN,
                                    'returns_inspected': False, 'prior_related_claims': [], 'notes': UNKNOWN},
                      'propositions': {p: {'statement': UNKNOWN, 'status': 'UNTESTED'} for p in PROPOSITIONS},
                      'recommendation': {'action': 'HOLD', 'reason': UNKNOWN}},
        'review': {'id': 'REV-', 'candidate_id': 'CAND-', 'version': 1, 'kind': 'M', 'role': None,
                   'reviewer': {'name': '', 'kind': 'HUMAN'},
                   'judgments': {m: {'judgment': 'UNCERTAIN', 'reason': '', 'evidence_refs': []} for m in M_REQUIREMENTS},
                   'checked': [], 'not_checked': [], 'conclusion': ''},
        'disposition': {'id': 'DSP-', 'candidate_id': 'CAND-', 'version': 1, 'decision': 'HOLD', 'reason_type': 'UNRESOLVED',
                        'reason': '', 'scope': '', 'decided_by': {'name': '', 'kind': 'HUMAN'}, 'verify': None, 'authorizes': []},
        'effort': {'id': 'EFF-', 'candidate_id': None, 'kind': 'ANALYST_TIME', 'description': '', 'analyst_minutes': UNKNOWN,
                   'source_starts': 0, 'bytes': 0, 'outcome': 'NOT_APPLICABLE', 'receipt': None, 'targeted_variable': None},
    }
    if kind not in blank:fail('template', f'unknown record type {kind!r}')
    return blank[kind]
