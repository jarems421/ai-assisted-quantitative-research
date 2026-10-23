"""AI Critic V001 contracts: dimensions, judgments, frozen critic texts by hash, strict answer checks.

Nothing here calls a model. A critic answer is data: it must answer the exact request (same critic, same input hash),
every adverse finding must anchor to the exact input it was given, and an invalid answer is recorded as invalid, never
repaired. A soft dimension can never be fatal, and a missing-evidence argument has no failure type: it is UNKNOWN."""
from __future__ import annotations

import json
from pathlib import Path
import unicodedata

from src.research.spec import canonical, digest
from .. import schema as S

VERSION = 'SCOUT_AI_CRITIC_V001'
REQUEST_V, INPUT_V, OUTPUT_V = 'SCOUT_CRITIC_REQUEST_V001', 'SCOUT_CRITIC_INPUT_V001', 'SCOUT_CRITIC_OUTPUT_V001'
RESOURCES_V = 'SCOUT_AI_CRITIC_RESOURCES_V001'
EXTRACTION = 'SINGLE_FENCED_JSON_BLOCK_AT_END_V1'  # the Graph R4 rule, mirrored so Scout never imports the paused study
CRITICS = ('SCIENTIFIC', 'ECONOMIC', 'ADVERSARIAL')
FIRST_PASS = CRITICS[:2]
DIMENSIONS = ('mechanism_coherence', 'falsifiability', 'evidence_integrity', 'temporal_validity', 'internal_novelty',
              'economic_significance', 'measurement_feasibility', 'research_feasibility', 'investment_applicability',
              'uncertainty')
HARD = DIMENSIONS[:4]   # requirements: a verified failure here outranks any soft assessment
SOFT = DIMENSIONS[4:9]  # estimates: never fatal, never override a hard failure
JUDGMENTS = ('PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE')
SEVERITIES = ('NONE', 'MINOR', 'MAJOR', 'CRITICAL')
# Failure type -> (dimensions where it may be used, may be marked potentially fatal).
FAILURES = {
    'INCOHERENT_MECHANISM': (('mechanism_coherence',), True),
    'BROKEN_CHAIN': (('mechanism_coherence',), False),
    'CONFOUNDED': (('mechanism_coherence', 'falsifiability'), False),
    'UNSUPPORTED_INFERENCE': (('mechanism_coherence', 'evidence_integrity'), False),
    'AMBIGUOUS_DEFINITION': (('mechanism_coherence', 'falsifiability', 'temporal_validity', 'measurement_feasibility'), False),
    'CIRCULAR_PREDICTION': (('falsifiability',), True),
    'UNFALSIFIABLE': (('falsifiability',), True),
    'WEAK_FALSIFIER': (('falsifiability',), False),
    'IMPOSSIBLE_TIMING': (('temporal_validity',), True),
    'LEAKAGE_RISK': (('temporal_validity',), False),
    'CONTRADICTED_BY_SUPPLIED_EVIDENCE': (('evidence_integrity',), True),
    'OVERCLAIMED_EVIDENCE': (('evidence_integrity', 'uncertainty'), False),
    'DUPLICATE_OF_REFERENCE': (('internal_novelty',), False),
    'GENERIC_MECHANISM': (('internal_novelty',), False),
    'TRIVIAL_MAGNITUDE': (('economic_significance',), False),
    'NOT_MEASURABLE_AS_STATED': (('measurement_feasibility',), False),
    'DATA_UNAVAILABLE_OR_UNTIMED': (('measurement_feasibility', 'research_feasibility'), False),
    'NO_CREDIBLE_ROUTE': (('research_feasibility',), False),
    'NO_INVESTMENT_LINK': (('investment_applicability',), False),
}
FATAL_TYPES = tuple(k for k, (_, fatal) in FAILURES.items() if fatal)
PRIMARY = {'SCIENTIFIC': HARD + ('uncertainty',), 'ECONOMIC': SOFT + ('uncertainty',),
           'ADVERSARIAL': HARD + ('uncertainty',)}
VERDICTS = ('FATAL_DEFECT_ESTABLISHED', 'NO_FATAL_DEFECT_ESTABLISHED', 'INSUFFICIENT_INFORMATION')
TEXTS = {'common': 'common_v001.md', 'SCIENTIFIC': 'scientific_v001.md', 'ECONOMIC': 'economic_v001.md',
         'ADVERSARIAL': 'adversarial_v001.md'}
RESOURCES = Path(__file__).resolve().parent / 'resources'
MIN_QUOTE = 8
ZERO_WIDTH = dict.fromkeys(map(ord, '\u00ad\u200b\u200c\u200d\u2060\ufeff'), None)

TEXT = {'type': 'string', 'maxLength': 2000}
NONEMPTY = {'type': 'string', 'minLength': 1, 'maxLength': 2000}
ANCHOR = S.obj({'field': {'type': 'string', 'pattern': '^/', 'maxLength': 300}, 'kind': S.enum(('QUOTE', 'ABSENCE')),
                'quote': {'type': 'string', 'maxLength': 1000}})
FATAL = S.obj({'violated_requirement': NONEMPTY, 'why_fatal_not_unresolved': NONEMPTY, 'overturning_observation': NONEMPTY})
ASSESSMENT = S.obj({'dimension': S.enum(DIMENSIONS), 'judgment': S.enum(JUDGMENTS),
    'failure_type': {'anyOf': [S.enum(FAILURES), {'type': 'null'}]}, 'severity': S.enum(SEVERITIES),
    'potentially_fatal': {'type': 'boolean'}, 'proposition': TEXT, 'anchors': S.array(ANCHOR, 6),
    'justification': NONEMPTY, 'assumptions': S.array(NONEMPTY, 8), 'next_check': TEXT,
    'fatal': {'anyOf': [FATAL, {'type': 'null'}]}})
ADVERSARIAL = S.obj({'verdict': S.enum(VERDICTS), 'strongest_counterexample': TEXT,
    'alternative_explanations': S.array(NONEMPTY, 8), 'simpler_existing_explanation': TEXT,
    'falsifier_discriminates': S.enum(('YES', 'NO', 'UNKNOWN')),
    'examined_challenges': S.array(S.obj({'challenge_id': S.LABEL, 'outcome': S.enum(('UPHELD', 'NOT_UPHELD', 'CANNOT_DETERMINE')),
                                          'reason': NONEMPTY}), 20)})
OUTPUT = S.obj({'schema': {'const': OUTPUT_V}, 'critic': S.enum(CRITICS), 'input_sha256': S.HASH,
    'assessments': S.array(ASSESSMENT, 10, 10), 'unresolved_assumptions': S.array(NONEMPTY, 12),
    'injection_suspected': {'type': 'boolean'}, 'injection_notes': TEXT,
    'subjective_confidence': S.enum(('LOW', 'MEDIUM', 'HIGH', 'UNSTATED')),
    'adversarial': {'anyOf': [ADVERSARIAL, {'type': 'null'}]}})


def lf(path):
    return Path(path).read_bytes().replace(b'\r\n', b'\n').decode('utf-8')


def resource_manifest():
    """The frozen critic texts. A changed text is a new version, never a silent refresh."""
    value = S.json_loads(lf(RESOURCES / 'manifest.json'))
    expected = {'schema': RESOURCES_V, 'version': VERSION, 'files': {n: S.hash_text(lf(RESOURCES / n)) for n in sorted(set(TEXTS.values()))},
                'output_schema_sha256': digest(OUTPUT), 'extraction_rule': EXTRACTION,
                'model_calls_authorised': False, 'hosted_transmission_authorised': False}
    if value != expected:raise S.ScoutError('critic texts, output schema or extraction rule changed; publish a new version instead')
    return value


def prompt_text(critic):
    resource_manifest()
    return lf(RESOURCES / TEXTS['common']) + '\n' + lf(RESOURCES / TEXTS[critic])


def clean(value):
    """The one presentation normalisation of critic inputs: NFKC, zero-width characters removed, whitespace collapsed.
    Whitespace-only and zero-width edits therefore give byte-identical inputs. The archived card is never changed."""
    if isinstance(value, str):return ' '.join(unicodedata.normalize('NFKC', value).translate(ZERO_WIDTH).split())
    if isinstance(value, list):return [clean(v) for v in value]
    if isinstance(value, dict):return {k: clean(v) for k, v in value.items()}
    return value


def render(critic, payload):
    """The exact text an operator gives the model. Markers carry the input hash, so data cannot forge the end marker."""
    h = digest(payload)
    return (prompt_text(critic) + '\n## OUTPUT_SCHEMA\n\n```json\n' + json.dumps(OUTPUT, indent=1, sort_keys=True) + '\n```\n\n'
            f'<<<UNTRUSTED_INPUT {h}>>>\n' + canonical(payload).decode('ascii') + f'\n<<<END_UNTRUSTED_INPUT {h}>>>\n')


def _strict(pairs):
    out = {}
    for k, v in pairs:
        if k in out:raise ValueError(f'duplicate key {k!r}')
        out[k] = v
    return out


def _constant(name):
    raise ValueError(f'non-standard JSON constant {name}')


def extract(data):
    """``SINGLE_FENCED_JSON_BLOCK_AT_END_V1`` on raw bytes: (status, object or None). Nothing is repaired or trimmed."""
    if not data.strip():return 'EMPTY', None
    try:text = data.decode('utf-8')
    except UnicodeDecodeError:return 'NOT_UTF8', None
    lines = text.splitlines(keepends=True); blocks, cur, info, close = [], None, None, None
    for n, line in enumerate(lines):
        bare = line.rstrip('\r\n')
        if cur is None and bare.startswith('```'):cur, info = [], bare[3:].strip()
        elif cur is not None and bare.rstrip() == '```':blocks.append((info, ''.join(cur))); cur, close = None, n
        elif cur is not None:cur.append(line)
    if cur is not None:return 'UNCLOSED_CODE_BLOCK', None
    if not blocks:return 'NO_CODE_BLOCK', None
    if len(blocks) > 1:return 'MULTIPLE_CODE_BLOCKS', None
    if blocks[0][0].casefold() not in ('', 'json'):return 'NOT_A_JSON_BLOCK', None
    if ''.join(lines[close + 1:]).strip():return 'BLOCK_NOT_AT_END', None
    try:value = json.loads(blocks[0][1], object_pairs_hook=_strict, parse_constant=_constant)
    except (ValueError, RecursionError):return 'INVALID_JSON', None
    return ('EXTRACTED', value) if isinstance(value, dict) else ('NOT_AN_OBJECT', None)


def resolve(document, pointer):
    """RFC 6901 pointer into the critic input; raises KeyError when it does not resolve."""
    node = document
    for part in pointer.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(node, dict) and part in node:node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):node = node[int(part)]
        else:raise KeyError(pointer)
    return node


def anchor_problem(document, anchor):
    if anchor['field'].startswith('/challenges'):return 'anchors cite the card, passages or references, never an earlier review\'s challenge text'
    try:value = resolve(document, anchor['field'])
    except KeyError:return f'anchor field {anchor["field"]} does not exist in the input'
    if anchor['kind'] == 'ABSENCE':
        return None if anchor['quote'] == '' else 'an ABSENCE anchor carries an empty quote'
    quote = ' '.join(anchor['quote'].split())
    if not isinstance(value, str):return f'QUOTE anchor {anchor["field"]} is not a text field'
    if not quote or (len(quote) < MIN_QUOTE and quote != value):return f'quote at {anchor["field"]} is too short to be checkable'
    return None if quote in value else f'quote not found in {anchor["field"]}: invented or altered text'


def problems(output, request):
    """Every reason this answer cannot be used for ``request``. Empty means VALID. Never repairs anything."""
    try:S.validate(OUTPUT, output, 'critic answer')
    except S.ScoutError as error:return [str(error)]
    out, critic, payload = [], request['critic'], request['input']
    if output['critic'] != critic:out.append(f'answer is for {output["critic"]}, request is for {critic}')
    if output['input_sha256'] != request['input_sha256']:out.append('answer names a different input hash')
    dims = [a['dimension'] for a in output['assessments']]
    if sorted(dims) != sorted(DIMENSIONS):out.append('each of the ten dimensions must appear exactly once')
    for a in output['assessments']:
        d, j, where = a['dimension'], a['judgment'], f'{a["dimension"]}: '
        if j == 'NOT_APPLICABLE' and d in PRIMARY[critic]:out.append(where + 'a primary dimension cannot be NOT_APPLICABLE')
        if j == 'FAIL':
            allowed, _ = FAILURES.get(a['failure_type'], ((), False))
            if d not in allowed:out.append(where + f'failure type {a["failure_type"]} does not apply to this dimension')
            if a['severity'] == 'NONE':out.append(where + 'a FAIL needs a severity')
            if not a['anchors']:out.append(where + 'a FAIL needs at least one anchor')
            if not a['proposition'].strip() or not a['next_check'].strip():out.append(where + 'a FAIL names its proposition and a next check')
        else:
            if a['failure_type'] is not None or a['severity'] != 'NONE':out.append(where + f'{j} carries no failure type or severity')
        if j == 'UNKNOWN' and (not a['proposition'].strip() or not a['next_check'].strip()):
            out.append(where + 'an UNKNOWN names the unresolved proposition and a discriminating next check')
        if a['potentially_fatal']:
            if j != 'FAIL' or d not in HARD or a['failure_type'] not in FATAL_TYPES:
                out.append(where + 'only a hard-dimension FAIL of a fatal-eligible type can be potentially fatal')
            if a['severity'] != 'CRITICAL':out.append(where + 'a potentially fatal FAIL is CRITICAL')
            if a['fatal'] is None:out.append(where + 'a potentially fatal FAIL needs the violated requirement, why it is fatal and what would overturn it')
        elif a['fatal'] is not None:out.append(where + 'the fatal block is only for potentially fatal findings')
        for anchor in a['anchors']:
            problem = anchor_problem(payload, anchor)
            if problem:out.append(where + problem)
    adv = output['adversarial']
    if (critic == 'ADVERSARIAL') != (adv is not None):out.append('the adversarial block is required for, and only for, the adversarial critic')
    if adv is not None:
        fatal = any(a['potentially_fatal'] for a in output['assessments'])
        hard_unknown = any(a['judgment'] == 'UNKNOWN' for a in output['assessments'] if a['dimension'] in HARD)
        if fatal != (adv['verdict'] == 'FATAL_DEFECT_ESTABLISHED'):out.append('verdict FATAL_DEFECT_ESTABLISHED if and only if an assessment is potentially fatal')
        if adv['verdict'] == 'INSUFFICIENT_INFORMATION' and not hard_unknown:out.append('INSUFFICIENT_INFORMATION needs an UNKNOWN hard dimension')
        expected = sorted(c['challenge_id'] for c in payload.get('challenges', []))
        if sorted(c['challenge_id'] for c in adv['examined_challenges']) != expected:out.append('every supplied challenge is examined exactly once')
    return out


def assessments(output):
    return {a['dimension']: a for a in output['assessments']}
