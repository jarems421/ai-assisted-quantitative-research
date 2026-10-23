"""Jev shadow review after generation: a non-comparative blinded human-label packet and a descriptive Jev comparison.

This is separate from the frozen four-condition comparison (``evaluation.blind``/``comparison.blind_package``), which
refuses incomplete or unequal conditions and is unchanged. Here every current card in the supplied archives is labelled,
whatever was generated, and nothing is ever comparative between conditions or methods.

* ``label_packet``: cards with generator metadata removed and the frozen atomic questions, never Jev output, plus a
  private key mapping blind ids to archive, idea and version. The key seals the hash of the whole reviewer-facing packet
  (everything except ``key_sha256`` itself), and the non-card text must equal its frozen derivation.
* ``import_response``: a saved System One response file, unchanged, against the request hash frozen at export. A
  separate write-once provenance record keeps the response file's byte hash and the operator's attestation; the
  provider verifies nothing.
* ``validate_labels``: independent labels, one per reviewer and item, declaring that the reviewer saw no Jev output and
  is independent of generation. Real batches accept HUMAN reviewers only; synthetic packets only SYNTHETIC_FIXTURE.
* ``compare``: Jev against those labels. Agreement, abstention, confusion, disagreement types, binary Brier where the
  label is yes/no, human-human agreement, problem flags beyond the mechanical checks, model identity, usage, unknown
  cost and every missing record. Descriptive only: Jev never routes, rejects, certifies or authorises anything.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import hmac
import re

from src.research.spec import canonical, digest
from .. import schema as S
from ..providers import JEV_MODEL, QUESTIONS, shadow_request

PACKET_V1, LABELS_V1, COMPARISON_V1 = 'SCOUT_SHADOW_LABEL_PACKET_V002', 'SCOUT_SHADOW_LABEL_V001', 'SCOUT_JEV_SHADOW_COMPARISON_V001'
PROVENANCE_V1 = 'SCOUT_JEV_RESPONSE_PROVENANCE_V001'
PROVENANCE_STATEMENT = ('The named operator attests that this response file is unchanged and answers the request with this hash. '
                        'The provider has not signed, returned or verified this binding.')
CHOICES = ('yes', 'no', 'unsure')
# The answer that indicates a problem with the card, per frozen question.
PROBLEM = {'explicit_mechanism': 'no', 'evidence_supported': 'no', 'falsifiable': 'no', 'next_check_addresses_gap': 'no',
           'certainty_exceeds_evidence': 'yes'}
ASSISTANT = re.compile(r'\b(claude|assistant|codex|chatgpt|gpt|copilot|gemini|llm|jev|typesafe|ai agent|bot)\b', re.I)
LABEL_RECORD = S.obj({'schema': {'const': LABELS_V1}, 'blind_id': S.LABEL,
    'reviewer': S.obj({'kind': S.enum(('HUMAN', 'SYNTHETIC_FIXTURE')), 'id': S.LABEL}),
    'saw_jev_output': {'const': False}, 'independent_of_generation': {'const': True},
    'atomic_answers': S.obj({q: S.enum(CHOICES) for q in QUESTIONS}), 'minutes': S.NUMBER, 'labelled_at': S.TEXT, 'notes': S.TEXT})
INTERPRETATION = [
    'Jev is a shadow reviewer. Its answers never change routing, reject a hypothesis, certify evidence or economic truth, or grant authority.',
    'Agreement with independent labels describes consistency on these cards only; it is not calibration, accuracy in general or significance.',
    'Binary Brier uses P(yes) only where the label is yes or no; unsure labels are abstentions, not outcomes. A constant 0.5 forecast scores 0.25.',
    'Problem flags beyond the mechanical checks are descriptive counts on a small, non-random set, not a measured research benefit.',
    'This packet is not the frozen four-condition comparison: no condition or method comparison may be drawn from it.']


def current_cards(states):
    return [(name, versions[-1]) for name, state in sorted(states.items()) for versions in state.cards.values()]


def label_packet(states, salt):
    """Every current card in ``states`` ({archive name: State}), blinded for independent labelling. Never contains Jev output."""
    if not states:raise S.ScoutError('at least one archive is required')
    if not isinstance(salt, str) or len(salt) < 20:raise S.ScoutError('use a private blinding salt of at least 20 characters')
    fixtures = {s.batch['fixture'] for s in states.values()}
    if len(fixtures) != 1:raise S.ScoutError('synthetic and exploratory archives cannot share a label packet')
    rows, assignments = [], {}
    for name, card in current_cards(states):
        state = states[name]
        bid = 'LABEL-' + hmac.new(salt.encode(), canonical([name, card['id'], card['version']]), hashlib.sha256).hexdigest()[:16]
        rows.append({'blind_id': bid, 'idea': {k: v for k, v in card['idea'].items() if k not in ('seed_ids', 'historical_refs')},
                     'source_passages': [{'text': state.seeds[s]['text'][:8000], 'depth': state.seeds[s]['depth'],
                                          'limitations': state.seeds[s]['limitations']} for s in card['idea']['seed_ids']]})
        assignments[bid] = {'archive': name, 'idea_id': card['id'], 'version': card['version'], 'card_sha256': digest(card)}
    rows.sort(key=lambda r: r['blind_id'])
    fixture = fixtures.pop()
    body = {'schema': PACKET_V1, 'fixture': fixture, 'cards': rows, **reviewer_text()}
    sealed = {'schema': PACKET_V1 + '_KEY', 'fixture': fixture, 'assignments': assignments, 'salt_sha256': S.hash_text(salt), 'public_cards_sha256': digest(rows),
              'reviewer_facing_sha256': digest(body), 'archive_heads': {n: (s.events[-1]['hash'] if s.events else None) for n, s in sorted(states.items())}}
    return {**body, 'key_sha256': digest(sealed)}, sealed


def reviewer_text():
    """Every non-card reviewer-facing field, derived only from the frozen questions: the same for every packet."""
    return {'questions': {q: {'text': t, 'choices': list(CHOICES)} for q, t in QUESTIONS.items()},
            'label_template': {'schema': LABELS_V1, 'blind_id': '<blind_id>', 'reviewer': {'kind': 'HUMAN', 'id': '<your name>'},
                               'saw_jev_output': False, 'independent_of_generation': True,
                               'atomic_answers': {q: '<yes | no | unsure>' for q in QUESTIONS}, 'minutes': '<number or UNKNOWN>',
                               'labelled_at': '<ISO time with zone>', 'notes': '<short reason>'},
            'instructions': 'Answer each question from the card and passages only. Do not look at any Jev output, other reviewers or '
                            'the private key. Unsure is a legitimate answer. Record your real minutes or UNKNOWN.',
            'blinding': 'PARTIAL_PROCEDURAL', 'comparative_eligible': False, 'jev_output_included': False, 'authorises': []}


def check_packet(packet, sealed):
    """The key seals the whole reviewer-facing packet (not recursive: ``key_sha256`` is the only field left out), and its
    non-card text must be the frozen derivation, so a consistently re-sealed pair with altered wording still fails."""
    if not isinstance(packet, dict) or packet.get('schema') != PACKET_V1:
        raise S.ScoutError(f'not a {PACKET_V1} packet (V001 packets did not seal their questions, instructions or template)')
    body = {k: v for k, v in packet.items() if k != 'key_sha256'}
    if packet.get('key_sha256') != digest(sealed) or packet.get('fixture') != sealed.get('fixture'):raise S.ScoutError('label packet and key do not match')
    if digest(body) != sealed.get('reviewer_facing_sha256'):raise S.ScoutError('reviewer-facing packet content changed after freeze')
    if {k: v for k, v in body.items() if k not in ('schema', 'fixture', 'cards')} != reviewer_text():
        raise S.ScoutError('packet questions, choices, instructions or template differ from the frozen wording')
    if digest(packet['cards']) != sealed.get('public_cards_sha256') or {r['blind_id'] for r in packet['cards']} != set(sealed['assignments']):
        raise S.ScoutError('label packet cards or assignments changed after freeze')


def validate_labels(packet, sealed, labels):
    """Independent labels: refuses fixture/real mixing, assistant reviewers, Jev exposure, unknown items and duplicates."""
    check_packet(packet, sealed)
    if not isinstance(labels, list):raise S.ScoutError('labels are a list of label records')
    kind = 'SYNTHETIC_FIXTURE' if packet['fixture'] == 'SYNTHETIC' else 'HUMAN'
    seen = set()
    for n, r in enumerate(labels, 1):
        S.validate(LABEL_RECORD, r, f'label {n}')
        if r['reviewer']['kind'] != kind:raise S.ScoutError(f'label {n}: this packet accepts {kind} labels only')
        if ASSISTANT.search(r['reviewer']['id']):raise S.ScoutError(f'label {n}: an assistant or model is never an independent human label')
        if r['blind_id'] not in sealed['assignments']:raise S.ScoutError(f'label {n}: unknown blind id')
        if (r['blind_id'], r['reviewer']['id']) in seen:raise S.ScoutError(f'label {n}: one label per reviewer and item')
        seen.add((r['blind_id'], r['reviewer']['id'])); S.timestamp(r['labelled_at'])
    return labels


def mechanical_problem(question, card):
    """The only existing mechanical check of a frozen question: a falsifier structural warning. None where no check exists."""
    if question != 'falsifiable':return None
    return any('FALSIF' in x for x in S.structural_checks(card['idea'])['checks'])


def compare(states, packet, sealed, labels, provenance=None):
    """Descriptive Jev-versus-independent-label report for the labelled cards. Missing records stay in the denominators.
    ``provenance``: {archive name: [provenance records]} from that archive's exports; absent records are reported as MISSING."""
    labels = validate_labels(packet, sealed, labels)
    if {s.batch['fixture'] for s in states.values()} != {sealed['fixture']}:raise S.ScoutError('archives are not the fixture class the packet was frozen from')
    items, missing_shadow, other_version_only, repeated, stale = {}, [], [], [], []
    for bid, m in sorted(sealed['assignments'].items()):
        state = states.get(m['archive'])
        if state is None or m['idea_id'] not in state.cards or len(state.cards[m['idea_id']]) < m['version']:
            raise S.ScoutError(f'archive {m["archive"]} no longer holds labelled card {m["idea_id"]} v{m["version"]}')
        card = state.cards[m['idea_id']][m['version'] - 1]
        if digest(card) != m['card_sha256']:raise S.ScoutError('a labelled card changed after the packet was frozen')
        if state.latest(m['idea_id'])['version'] != m['version']:stale.append(bid)
        exact = [r for r in state.shadows if r['idea_id'] == card['id'] and r['version'] == card['version']]
        if len(exact) > 1:repeated.append(bid)
        if not exact:
            missing_shadow.append(bid)
            if any(r['idea_id'] == card['id'] for r in state.shadows):other_version_only.append(bid)
        # The earliest record is used, so a later re-run cannot replace an inconvenient answer.
        items[bid] = {'card': card, 'shadow': exact[0] if exact else None,
                      'provenance': provenance_status(state, exact[0], (provenance or {}).get(m['archive'], [])) if exact else None}
    by_item = {}
    for r in labels:by_item.setdefault(r['blind_id'], []).append(r)
    questions = {}
    for q in QUESTIONS:
        confusion = {j: {h: 0 for h in CHOICES} for j in CHOICES}
        brier, jev_choices, human_choices = [], Counter(), Counter()
        problems = {'human_flagged': 0, 'jev_also_flagged': 0, 'jev_missed': 0, 'jev_flagged_human_opposite': 0,
                    'jev_flagged_human_unsure': 0, 'jev_also_flagged_where_mechanical_check_did_not': 0 if q == 'falsifiable' else None,
                    'mechanical_check_exists': q == 'falsifiable'}
        for bid, it in items.items():
            if it['shadow']:jev_choices[it['shadow']['response']['answers'][q]['choice']] += 1
            for r in by_item.get(bid, []):
                h = r['atomic_answers'][q]; human_choices[h] += 1
                if not it['shadow']:continue
                a = it['shadow']['response']['answers'][q]; j = a['choice']; confusion[j][h] += 1
                if h in ('yes', 'no'):brier.append((a['probabilities']['yes'] - (h == 'yes')) ** 2)
                bad = PROBLEM[q]; opposite = 'yes' if bad == 'no' else 'no'
                if h == bad:
                    problems['human_flagged'] += 1
                    if j == bad:
                        problems['jev_also_flagged'] += 1
                        if mechanical_problem(q, it['card']) is False:problems['jev_also_flagged_where_mechanical_check_did_not'] += 1
                    else:problems['jev_missed'] += 1
                elif j == bad:problems['jev_flagged_human_opposite' if h == opposite else 'jev_flagged_human_unsure'] += 1
        pairs = sum(sum(row.values()) for row in confusion.values())
        agreed = sum(confusion[c][c] for c in CHOICES)
        decisive = sum(confusion[j][h] for j in ('yes', 'no') for h in ('yes', 'no'))
        questions[q] = {
            'pairs_compared': pairs, 'agreed': agreed, 'agreement': agreed / pairs if pairs else None,
            'decisive_pairs': decisive, 'decisive_agreement': (confusion['yes']['yes'] + confusion['no']['no']) / decisive if decisive else None,
            'disagreement': {'opposite_decisions': confusion['yes']['no'] + confusion['no']['yes'],
                             'jev_abstained_human_decided': confusion['unsure']['yes'] + confusion['unsure']['no'],
                             'human_abstained_jev_decided': confusion['yes']['unsure'] + confusion['no']['unsure']},
            'confusion_jev_by_label': confusion,
            'jev_abstention_rate': jev_choices['unsure'] / sum(jev_choices.values()) if jev_choices else None,
            'label_abstention_rate': human_choices['unsure'] / sum(human_choices.values()) if human_choices else None,
            'binary_yes_brier': sum(brier) / len(brier) if brier else None, 'binary_label_count': len(brier),
            'constant_half_reference_brier': 0.25 if brier else None,
            'problem_flags': problems, 'human_human': human_agreement(by_item, q)}
    used = [it['shadow'] for it in items.values() if it['shadow']]
    usage = {'shadow_records_used': len(used), 'requested_model': JEV_MODEL,
             'returned_models': dict(Counter(r['response']['model'] for r in used)),
             'returned_model_differs': sum(r['response']['model'] != JEV_MODEL for r in used),
             'input_tokens': sum(r['response']['usage']['input_tokens'] for r in used),
             'output_tokens': sum(r['response']['usage']['output_tokens'] for r in used),
             'known_cost': sum(r['cost'] for r in used if r['cost'] != S.UNKNOWN),
             'unknown_cost_records': sum(r['cost'] == S.UNKNOWN for r in used),
             'currencies': sorted({r['currency'] for r in used}), 'transports': dict(Counter(r['transport'] for r in used)),
             'note': 'System One documents token usage but no price or currency; cost stays UNKNOWN unless separately evidenced.'}
    prov = Counter(it['provenance'] for it in items.values() if it['shadow'])
    usage['response_provenance'] = {'operator_attested': prov['OPERATOR_ATTESTED'], 'missing': prov['MISSING'], 'mismatched': prov['MISMATCHED'],
        'provider_verified': 0, 'items_without_attested_provenance': sorted(b for b, it in items.items() if it['shadow'] and it['provenance'] != 'OPERATOR_ATTESTED'),
        'basis': 'Operator attestation binds a saved response file to a frozen request hash. The provider verifies nothing.'}
    minutes = [r['minutes'] for r in labels]
    return {'schema': COMPARISON_V1, 'fixture': packet['fixture'], 'packet_key_sha256': packet['key_sha256'],
            'items': len(items), 'labelled_items': len(by_item), 'labels': len(labels),
            'reviewers': sorted({r['reviewer']['id'] for r in labels}),
            'questions': questions, 'usage_and_cost': usage,
            'label_effort': {'known_minutes': sum(m for m in minutes if m != S.UNKNOWN), 'unknown_entries': sum(m == S.UNKNOWN for m in minutes)},
            'missing': {'items_without_shadow': missing_shadow, 'items_without_labels': sorted(set(items) - set(by_item)),
                        'items_with_repeated_shadow_records': repeated, 'items_with_shadow_for_another_version_only': other_version_only,
                        'items_superseded_since_packet': stale},
            'interpretation': INTERPRETATION, 'comparative_eligible': False, 'shadow_only': True, 'routing_changed': False,
            'calibration_established': False, 'statistical_significance': 'NOT_CLAIMED', 'human_labels_invented': False,
            'authorises': []}


def human_agreement(by_item, q):
    pairs = agreed = 0
    for rows in by_item.values():
        answers = [r['atomic_answers'][q] for r in rows]
        for i in range(len(answers)):
            for k in range(i + 1, len(answers)):pairs += 1; agreed += answers[i] == answers[k]
    return {'pairs': pairs, 'agreement': agreed / pairs if pairs else None}


def shadow_record(state, idea_id, version, request_sha256, response, *, cost=S.UNKNOWN, currency=S.UNKNOWN, transport='IMPORTED_NOT_CALLED', now=None):
    """The shadow record for a response to the frozen request ``request_sha256`` for exactly ``idea_id`` v``version``.

    The hash is the operator's, from the request actually sent (``shadow-request`` prints it as ``payload_sha256``). It must
    equal the request for that exact version, which must still be current: a response to an older version is refused."""
    card = state.latest(idea_id)
    if version != card['version']:raise S.ScoutError(f'the request was frozen for v{version}; {idea_id} is now v{card["version"]}, so it cannot be imported')
    if not isinstance(request_sha256, str) or request_sha256 != digest(shadow_request(state, idea_id)):
        raise S.ScoutError('the supplied request hash is not the frozen request for this exact card version')
    return {'idea_id': idea_id, 'version': version, 'request_sha256': request_sha256, 'response': response,
            'imported_at': now or S.utc_now(), 'cost': cost, 'currency': currency, 'shadow_only': True, 'transport': transport}


def import_response(archive, idea_id, version, request_sha256, response_path, by, *, request_path=None, cost=S.UNKNOWN,
                    currency=S.UNKNOWN, transport='IMPORTED_NOT_CALLED', now=None):
    """Import a saved response file unchanged and write its provenance record (write-once, operator attestation)."""
    from ..storage import input_json, unlinked
    if not isinstance(by, str) or not by.strip() or ASSISTANT.search(by):raise S.ScoutError('the attestation is a named human operator, not an assistant or model')
    response = input_json(response_path); raw = unlinked(response_path).read_bytes()  # bytes hashed as stored; the file is never written
    if digest(S.json_loads(raw.decode('utf-8'))) != digest(response):raise S.ScoutError('the response file changed while it was being read')
    request_file = None
    if request_path is not None:
        request_raw = unlinked(request_path).read_bytes()
        if digest(input_json(request_path)) != request_sha256:raise S.ScoutError('the request file is not the request with the supplied hash')
        request_file = {'sha256': hashlib.sha256(request_raw).hexdigest(), 'bytes': len(request_raw)}
    record = shadow_record(archive.load(), idea_id, version, request_sha256, response, cost=cost, currency=currency, transport=transport, now=now)
    event = archive.append('shadow', record).events[-1]
    provenance = {'schema': PROVENANCE_V1, 'idea_id': idea_id, 'version': version, 'request_sha256': request_sha256, 'request_file': request_file,
                  'response_file': {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}, 'response_json_sha256': digest(response),
                  'shadow_event': {'seq': event['seq'], 'hash': event['hash']}, 'imported_at': record['imported_at'],
                  'attested_by': by, 'basis': 'OPERATOR_ATTESTATION', 'provider_verified': False, 'statement': PROVENANCE_STATEMENT}
    path = archive.export(f'jev-provenance-e{event["seq"]:04d}.json', provenance)
    return record, provenance, path


def provenance_status(state, shadow, records):
    """``OPERATOR_ATTESTED`` when a provenance record names this shadow's exact event and response; else MISSING or MISMATCHED.
    Never ``PROVIDER_VERIFIED``: System One returns nothing that binds a response to a request."""
    events = [e for e in state.events if e['type'] == 'shadow']
    event = next((e for e in events if e['record'] is shadow or e['record'] == shadow), None)
    matches = [r for r in records if event and r.get('shadow_event', {}).get('hash') == event['hash']]
    if not matches:return 'MISSING'
    r = matches[0]
    ok = (len(matches) == 1 and r.get('schema') == PROVENANCE_V1 and r.get('basis') == 'OPERATOR_ATTESTATION' and r.get('provider_verified') is False
          and r.get('statement') == PROVENANCE_STATEMENT and (r['idea_id'], r['version'], r['request_sha256']) ==
          (shadow['idea_id'], shadow['version'], shadow['request_sha256']) and r['response_json_sha256'] == digest(shadow['response']))
    return 'OPERATOR_ATTESTED' if ok else 'MISMATCHED'
