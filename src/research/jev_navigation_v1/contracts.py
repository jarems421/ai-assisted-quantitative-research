"""Three bounded input contracts and the documented System One Choice response shape.

Local saved-response envelopes are synthetic fixtures, not provider attestations.
Nothing in this package imports the retired Jev critic or implements a transport.
"""
from __future__ import annotations

import json
import math
from jsonschema import Draft202012Validator

INPUT = 'JEV_NAVIGATION_INPUT_V001'
REQUEST = 'JEV_NAVIGATION_REQUEST_V001'
SAVED = 'JEV_NAVIGATION_SYNTHETIC_RESPONSE_V001'
REPORT = 'JEV_NAVIGATION_REPORT_V001'
CHOICES = ('yes', 'no', 'unsure')
M_ORDER = ('distinctive_predictor', 'meaning_and_units', 'separate_outcome', 'valid_join', 'financial_bridge', 'public_time_route')
EVIDENCE = {
    'predictor': ('distinctive_predictor', 'a passage about the specified distinctive predictor'),
    'outcome': ('separate_outcome', 'a separately recorded realised outcome, not a formula or forecast derived from the predictor'),
    'units': ('meaning_and_units', 'units, denominator or scope of the specified measurement'),
    'relationship': ('valid_join', 'the specified entity or a historical relationship needed for the join'),
    'exposure': ('financial_bridge', 'the specified listed-company financial exposure, with gross and net kept separate'),
    'public_version': ('public_time_route', 'publication timing or the historical version of the supplied measurement'),
    'falsifier': (None, 'an observation that could contradict the stated economic question'),
    'background': (None, 'background context only, rather than a measurement or falsifier'),
}
MEMORY = {
    'mechanism': 'a possible similarity in the underlying economic mechanism, beyond shared words',
    'source_lead': 'a named earlier source potentially worth inspecting in the already retained records',
    'blocker_lesson': 'a documented earlier measurement or source-access blocker relevant to the current question',
    'falsification_lesson': 'a recorded economic falsification relevant to the question; an access failure is not an economic falsification',
}
WORKFLOW = {
    'predictor_missing': 'a missing original predictor measurement',
    'outcome_missing': 'a missing independently measured outcome',
    'units_unresolved': 'unresolved measurement units or denominator',
    'join_missing': 'an unresolved entity, cohort or historical join',
    'exposure_unverified': 'unverified listed-company financial exposure',
    'public_time_unresolved': 'an unresolved historical public-time or version route',
    'competing_explanation': 'an unanswered competing explanation',
    'human_judgment_missing': 'a missing required human judgment',
    'explicit_stop': 'an explicit source-access, campaign or experiment stop',
    'insufficient_information': 'insufficient supplied information to identify a bottleneck',
}
TASKS = ('EVIDENCE_PROSPECTOR', 'MEMORY_NAVIGATOR', 'WORKFLOW_NAVIGATOR')
TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 12000}
HASH = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
LABEL = {'type': 'string', 'pattern': '^[A-Za-z0-9_.:-]{1,100}$'}


class NavigationError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise NavigationError(message)


def obj(fields):
    return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}


def array(item, maximum=64):
    return {'type': 'array', 'items': item, 'maxItems': maximum, 'uniqueItems': True}


REF = obj({'base': {'enum': ['INPUT', 'REPOSITORY']}, 'path': TEXT, 'sha256': HASH})
CITATION = obj({'artifact': REF, 'location': TEXT, 'quote': TEXT})
SUBJECT = obj({'id': LABEL, 'version': {'type': 'integer', 'minimum': 1}, 'question': TEXT,
               'predictor': TEXT, 'outcome': TEXT, 'unresolved_m': array({'enum': list(M_ORDER)}, 6),
               'concept_terms': array(TEXT, 16), 'entity_ids': array(TEXT), 'document_sha256': array(HASH),
               'requirement_ids': array(TEXT)})
DOCUMENT = obj({'id': LABEL, 'version': TEXT, 'title': TEXT, 'source_id': LABEL, 'citation': CITATION,
                'availability': {'enum': ['SUPPLIED_COPY', 'SUPPLIED_EXCERPT', 'UNAVAILABLE', 'STOPPED']},
                'original_sha256': {'anyOf': [HASH, {'const': 'UNKNOWN'}]}, 'limitations': array(TEXT)})
WORKFLOW_CONTEXT = obj({'ledger': {'anyOf': [REF, {'type': 'null'}]}, 'candidate_id': {'anyOf': [LABEL, {'type': 'null'}]},
                        'candidate_version': {'anyOf': [{'type': 'integer', 'minimum': 1}, {'type': 'null'}]},
                        'experiment_id': {'anyOf': [LABEL, {'type': 'null'}]},
                        'stops': array(obj({'id': LABEL, 'scope': TEXT, 'citation': CITATION})),
                        'context_files': array(REF)})


def input_schema(task):
    fields = {'schema': {'const': INPUT}, 'task': {'const': task},
              'data_classification': {'enum': ['SYNTHETIC', 'PUBLIC_REPOSITORY', 'LOCAL_PRIVATE']}, 'subject': SUBJECT}
    fields.update({'documents': {**array(DOCUMENT, 32), 'minItems': 1}} if task == TASKS[0] else
                  {'catalogue': REF} if task == TASKS[1] else {'context': WORKFLOW_CONTEXT})
    return obj(fields)


def validate(schema, value):
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise NavigationError(str(errors[0].message))
    return value


def loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(NavigationError('nonfinite JSON value')))


def answer_set(request, response):
    """Validate exact keys/types, finite distributions, argmax and documented confidence.

    Tied maxima become an effective abstention, while retaining the supplied answer.
    No confidence threshold or probability-weighted scientific decision is used.
    """
    number = {'type': 'number', 'minimum': 0, 'maximum': 1}
    answer = obj({'type': {'const': 'choice'}, 'choice': {'enum': list(CHOICES)},
                  'probabilities': obj({x: number for x in CHOICES}), 'confidence': number})
    schema = obj({'model': {'const': 'SYNTHETIC_SCRIPTED_NOT_JEV'},
                  'answers': obj({q: answer for q in request['questions']}),
                  'usage': obj({'input_tokens': {'type': 'integer', 'minimum': 0}, 'output_tokens': {'type': 'integer', 'minimum': 0}})})
    validate(schema, response)
    need(all(type(v) is int for v in response['usage'].values()), 'usage must contain integers, not booleans or floats')
    result = {}
    for key, a in response['answers'].items():
        probabilities = list(a['probabilities'].values())
        need(all(type(v) in (int, float) and math.isfinite(v) for v in [*probabilities, a['confidence']]), 'finite numeric probabilities required')
        need(abs(sum(probabilities) - 1) <= 1e-6, 'probabilities must sum to one')
        largest = max(probabilities)
        need(abs(a['probabilities'][a['choice']] - largest) <= 1e-6, 'choice must be an argmax')
        need(abs(a['confidence'] - (largest - 1 / 3) / (1 - 1 / 3)) <= 1e-5, 'confidence inconsistent with documented Choice statistic')
        tied = sum(abs(p - largest) <= 1e-6 for p in probabilities) > 1
        result[key] = {'raw': a, 'effective_choice': 'unsure' if tied else a['choice'],
                       'abstention': 'TIED_MAXIMUM' if tied else 'EXPLICIT_UNSURE' if a['choice'] == 'unsure' else None}
    return result
