"""One direct documented HTTPS POST. No SDK retries, proxies, redirects or fallback."""
from __future__ import annotations

import http.client
import math
from src.research.jev_navigation_v1 import contracts as K

HOST = 'api.typesafe.ai'
PATH = '/v1/systemone'
MODELS = ('jev-1.13.0', 'jev-1.14.0')
MAX_RESPONSE = 1024 * 1024
SOCKET_INACTIVITY_SECONDS = 30
USAGE = K.obj({'input_tokens': {'type': 'integer', 'minimum': 0, 'maximum': 65536},
               'output_tokens': {'type': 'integer', 'minimum': 0, 'maximum': 2147483647}})
# Reviewed default-context upper reservation, using 64 Ki tokens conservatively.
# At 42 USD / billion input tokens, output free: ceil(65536*42/1000) micro-USD.
RESERVATION_MICRO_USD = 2753


def capture(payload, key, emit):
    # An inactivity timeout, not a strict total deadline: a trickling peer can extend it.
    connection = http.client.HTTPSConnection(HOST, timeout=SOCKET_INACTIVITY_SECONDS)
    try:
        connection.request('POST', PATH, body=payload,
                           headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        response = connection.getresponse()
        # http.client does not follow Location; error/redirect bodies remain raw evidence.
        while True:
            try:
                chunk = response.read(65536)
            except http.client.IncompleteRead as error:
                # Preserve received bytes privately, without copying exception text into metadata.
                if error.partial:
                    emit(error.partial)
                raise
            if not chunk:
                break
            emit(chunk)
        return response.status
    finally:
        connection.close()


def metadata(response):
    """Whitelist-only public metadata; all other values remain in private raw capture.

    A recognised provider-reported version is not verified runtime identity. Usage is
    a bounded provider claim, never independently verified cost or token accounting.
    """
    result = {'model_returned': 'UNKNOWN', 'usage': 'UNKNOWN', 'metadata_faults': [],
              'runtime_identity': 'UNVERIFIED'}
    if not isinstance(response, dict):
        result['metadata_faults'] = ['MODEL_METADATA_INVALID', 'USAGE_METADATA_INVALID']
        return result
    model = response.get('model')
    if type(model) is str and model in MODELS:
        result['model_returned'] = model
    else:
        result['metadata_faults'].append('MODEL_METADATA_INVALID')
    usage = response.get('usage')
    try:
        K.validate(USAGE, usage)
        K.need(all(type(v) is int for v in usage.values()), 'integer usage required')
    except (ValueError, TypeError):
        result['metadata_faults'].append('USAGE_METADATA_INVALID')
    else:
        result['usage'] = usage
    return result


def answers(request, response, requested_model):
    """Same Choice semantics as V001, strict real model identity instead of its fixture-only envelope."""
    number = {'type': 'number', 'minimum': 0, 'maximum': 1}
    answer = K.obj({'type': {'const': 'choice'}, 'choice': {'enum': list(K.CHOICES)},
                    'probabilities': K.obj({c: number for c in K.CHOICES}), 'confidence': number})
    schema = K.obj({'model': {'const': requested_model},
                    'answers': K.obj({q: answer for q in request['questions']}),
                    'usage': USAGE})
    K.validate(schema, response)
    K.need(all(type(v) is int for v in response['usage'].values()), 'integer usage required')
    K.need(response['usage']['input_tokens'] <= 65536, 'usage exceeds reviewed context/spend reservation')
    result = {}
    for name, a in response['answers'].items():
        probabilities = list(a['probabilities'].values())
        K.need(all(type(v) in (int, float) and math.isfinite(v) for v in [*probabilities, a['confidence']]), 'finite numeric probabilities required')
        K.need(abs(sum(probabilities) - 1) <= 1e-6, 'probabilities must sum to one')
        largest = max(probabilities)
        K.need(abs(a['probabilities'][a['choice']] - largest) <= 1e-6, 'choice must be an argmax')
        K.need(abs(a['confidence'] - (largest - 1 / 3) / (1 - 1 / 3)) <= 1e-5, 'confidence inconsistent with documented Choice statistic')
        tied = sum(abs(p - largest) <= 1e-6 for p in probabilities) > 1
        result[name] = {'raw': a, 'effective_choice': 'unsure' if tied else a['choice'],
                        'abstention': 'TIED_MAXIMUM' if tied else 'EXPLICIT_UNSURE' if a['choice'] == 'unsure' else None}
    return result
