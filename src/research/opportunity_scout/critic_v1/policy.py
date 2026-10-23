"""Deterministic recommendation policy over Layer A findings and validated critic answers. Recommendations only.

Rules, first match wins (every reason is still recorded):

* R0 Layer A INVALID_INPUT -> REVISION_REQUIRED (no critic reviews an invalid card).
* R1 instruction-like text in the card or passages, or a critic suspecting injection -> ESCALATE.
* R2 a first-pass answer (SCIENTIFIC, ECONOMIC) missing, invalid or refused -> ESCALATE. Unknown never becomes pass or fail.
* R3 any potentially fatal finding: without the adversarial review -> ESCALATE; the adversarial critic confirms the same
  dimension a first-pass critic raised and no first-pass critic PASSes it -> REJECT_RECOMMENDED; otherwise -> ESCALATE.
  No single critic, and no adversarial objection alone, can produce REJECT_RECOMMENDED.
* R4 a definitive Layer A defect, a non-fatal FAIL on a hard dimension or uncertainty, or a duplicate -> REVISION_REQUIRED.
  A soft PASS never overrides it.
* R5 every READY dimension PASSed by its owning critic and no blocking soft FAIL -> READY_CANDIDATE (research-worthy, not
  proven or authorised).
* R6 distinct and material on the economic critic's reading, but a hard dimension UNKNOWN -> ESCALATE.
* R7 otherwise INCUBATE, retained with the checks that would justify reconsideration.

Jev never enters this policy. Nothing here deletes, routes, approves or rejects a card: the human READY/handoff and owner
gates stay authoritative."""
from __future__ import annotations

from src.research.spec import digest
from .. import schema as S
from . import packages as P, rubric as K

POLICY, RECOMMENDATIONS_V = 'SCOUT_AI_CRITIC_POLICY_V001', 'SCOUT_CRITIC_RECOMMENDATIONS_V001'
ROUTING_MODE = 'RECOMMENDATION_ONLY_V001'
CLASSES = ('READY_CANDIDATE', 'INCUBATE', 'REVISION_REQUIRED', 'REJECT_RECOMMENDED', 'ESCALATE')
OWNERS = {'mechanism_coherence': 'SCIENTIFIC', 'falsifiability': 'SCIENTIFIC', 'evidence_integrity': 'SCIENTIFIC',
          'temporal_validity': 'SCIENTIFIC', 'measurement_feasibility': 'ECONOMIC', 'research_feasibility': 'ECONOMIC'}
REVISION_DIMENSIONS = K.HARD + ('uncertainty',)
BLOCKING_SOFT = ('internal_novelty', 'economic_significance', 'measurement_feasibility', 'research_feasibility')
SELECTION = ('UNCERTAIN_FATAL_DEFECT', 'CRITIC_DISAGREEMENT', 'UNUSUALLY_PROMISING', 'NOVEL_HIGH_UPSIDE', 'HIGH_CONSEQUENCE')
HUMAN_GATES = ['READY and handoff need a human SCOUT_READY_V002 review and feasibility record for the exact card version.',
               'A Discovery Lab campaign, source acquisition, hosted model use or spending needs a separate owner document.',
               'No AI recommendation deletes a card, changes its archived routing or substitutes for Measurement Gate M or H.']


def disagreements(views):
    out = []
    for d in K.DIMENSIONS:
        judged = {c: v[d] for c, v in sorted(views.items()) if v[d]['judgment'] != 'NOT_APPLICABLE'}
        kinds = {a['judgment'] for a in judged.values()}
        if {'PASS', 'FAIL'} <= kinds:
            out.append({'dimension': d, 'judgments': {c: a['judgment'] for c, a in judged.items()},
                        'fatal': any(a['potentially_fatal'] for a in judged.values()), 'hard': d in K.HARD})
    return out


def families(chosen):
    names = {c: a['provenance']['model_family'].casefold() for c, a in chosen.items()}
    first = [names[c] for c in K.FIRST_PASS if c in names]
    return names, ('SAME_MODEL_FAMILY' if len(first) == 2 and first[0] == first[1] else 'DIFFERENT_MODEL_FAMILIES' if len(first) == 2 else 'UNKNOWN')


def decide(layer_a, chosen, statuses):
    """One recommendation from a Layer A report, the usable attempt per critic and each critic's attempt status."""
    views = {c: K.assessments(a['output']) for c, a in chosen.items()}
    names, independence = families(chosen)
    r = {'classification': None, 'rule': None, 'reasons': [],
         'definitive_findings': sorted({f['code'] for f in layer_a['findings'] if f['definitive']}),
         'advisories': sorted({f['code'] for f in layer_a['findings'] if f['category'] == 'UNKNOWN'}),
         'missing_evidence': sorted({f['code'] for f in layer_a['findings'] if f['category'] == 'MISSING_EVIDENCE'}),
         'fatal': {'first_pass': [], 'adversarial': [], 'established': [], 'correlated_support': False},
         'disagreements': disagreements(views), 'unknown': {c: sorted(d for d, a in v.items() if a['judgment'] == 'UNKNOWN') for c, v in sorted(views.items())},
         'repairs': [], 'reconsider_when': [], 'critics': {c: {'status': statuses.get(c, 'NOT_REQUESTED'),
             **({'attempt': chosen[c]['attempt'], 'model': chosen[c]['provenance']['model'], 'model_family': names[c]} if c in chosen else {})} for c in K.CRITICS},
         'first_pass_independence': independence, 'adversarial': 'RUN' if 'ADVERSARIAL' in views else 'NOT_RUN',
         'adversarial_recommended': None, 'authority': 'RECOMMENDATION_ONLY', 'authorises': []}

    def done(classification, rule, *reasons):
        r.update(classification=classification, rule=rule); r['reasons'] += list(reasons); return r

    if not layer_a['reviewable']:
        r['repairs'] = sorted({f['repair'] or f['detail'] for f in layer_a['findings'] if f['category'] == 'INVALID_INPUT'})
        return done('REVISION_REQUIRED', 'R0_INVALID_INPUT', 'INPUT_INVALID_NOT_REVIEWED')
    if layer_a['injection_flags'] or any(a['output']['injection_suspected'] for a in chosen.values()):
        return done('ESCALATE', 'R1_INSTRUCTION_LIKE_TEXT', 'HUMAN_DISPOSITION_OF_INSTRUCTION_LIKE_TEXT_REQUIRED')
    missing = [c for c in K.FIRST_PASS if c not in views]
    if missing:return done('ESCALATE', 'R2_INCOMPLETE_REVIEW', *(f'{c}_{statuses.get(c, "MISSING")}' for c in missing))
    for c in K.CRITICS:
        for d, a in views.get(c, {}).items():
            if a['potentially_fatal']:
                r['fatal']['first_pass' if c in K.FIRST_PASS else 'adversarial'].append(
                    {'critic': c, 'dimension': d, 'failure_type': a['failure_type'], 'violated_requirement': a['fatal']['violated_requirement']})
    first = {x['dimension'] for x in r['fatal']['first_pass']}
    adverse = {x['dimension'] for x in r['fatal']['adversarial']}
    if first or adverse:
        if 'ADVERSARIAL' not in views:
            r['adversarial_recommended'] = 'UNCERTAIN_FATAL_DEFECT'
            return done('ESCALATE', 'R3_UNCERTAIN_FATAL_DEFECT', 'FATAL_CLAIM_AWAITS_ADVERSARIAL_REVIEW')
        contested = {d for d in first & adverse if any(views[c][d]['judgment'] == 'PASS' for c in K.FIRST_PASS)}
        established = sorted((first & adverse) - contested)
        if established:
            raisers = {names[x['critic']] for x in r['fatal']['first_pass'] if x['dimension'] in established}
            r['fatal'].update(established=established, correlated_support=names['ADVERSARIAL'] in raisers)
            r['repairs'] = sorted({views['ADVERSARIAL'][d]['fatal']['overturning_observation'] for d in established})
            return done('REJECT_RECOMMENDED', 'R3_FATAL_DEFECT_CONFIRMED', *(f'FATAL_{d.upper()}' for d in established))
        return done('ESCALATE', 'R3_FATAL_DEFECT_DISPUTED', *(['ADVERSARIAL_DID_NOT_CONFIRM'] if first - adverse else []),
                    *(['FATAL_RAISED_ONLY_BY_ADVERSARIAL'] if adverse - first else []), *(['FATAL_CONTESTED_BY_FIRST_PASS_PASS'] if contested else []))
    defects = [f for f in layer_a['findings'] if f['definitive']]
    fails = [a for v in views.values() for a in v.values() if a['judgment'] == 'FAIL'
             and (a['dimension'] in REVISION_DIMENSIONS or a['failure_type'] == 'DUPLICATE_OF_REFERENCE')]
    if defects or fails:
        r['repairs'] = sorted({f['repair'] or f['detail'] for f in defects} | {a['next_check'] for a in fails})
        if 'ADVERSARIAL' not in views and any(x['hard'] for x in r['disagreements']):r['adversarial_recommended'] = 'CRITIC_DISAGREEMENT'
        return done('REVISION_REQUIRED', 'R4_REPAIRABLE_DEFECT', *(f'LAYER_A_{f["code"]}' for f in defects),
                    *sorted({f'{a["dimension"].upper()}_{a["failure_type"]}' for a in fails}))
    soft_fail = sorted({(d, a['failure_type']) for v in views.values() for d in BLOCKING_SOFT for a in [v[d]] if a['judgment'] == 'FAIL'})
    economic = views['ECONOMIC']
    distinct = economic['internal_novelty']['judgment'] == 'PASS' and economic['economic_significance']['judgment'] == 'PASS'
    if all(views[c][d]['judgment'] == 'PASS' for d, c in OWNERS.items()) and not soft_fail:
        if distinct and 'ADVERSARIAL' not in views:r['adversarial_recommended'] = 'UNUSUALLY_PROMISING'
        return done('READY_CANDIDATE', 'R5_RESEARCH_WORTHY', 'COHERENT_FALSIFIABLE_WITH_MEASUREMENT_ROUTE')
    r['reconsider_when'] = sorted({f'{d}: {a["next_check"]}' for v in views.values() for d, a in v.items()
                                   if a['judgment'] in ('UNKNOWN', 'FAIL') and a['next_check'].strip()})
    hard_unknown = [d for d in K.HARD if views[OWNERS[d]][d]['judgment'] == 'UNKNOWN']
    if distinct and hard_unknown and not any(d in ('internal_novelty', 'economic_significance') for d, _ in soft_fail):
        if 'ADVERSARIAL' not in views:r['adversarial_recommended'] = 'NOVEL_HIGH_UPSIDE'
        return done('ESCALATE', 'R6_NOVEL_HIGH_UPSIDE_UNRESOLVED', *(f'{d.upper()}_UNKNOWN' for d in hard_unknown))
    return done('INCUBATE', 'R7_RETAIN_PENDING_EVIDENCE', *(f'{d.upper()}_{t}' for d, t in soft_fail),
                *(f'{d.upper()}_UNKNOWN' for d, c in OWNERS.items() if views[c][d]['judgment'] == 'UNKNOWN'))


def statuses_for(key, requests, history):
    out = {}
    for r in requests:
        if r['subject_key'] != key:continue
        attempts = history.get(r['request_id'], [])
        out[r['critic']] = ('VALID' if any(a['status'] == 'VALID' for a in attempts) else 'MISSING' if not attempts
                            else 'ATTEMPTS_EXHAUSTED' if len(attempts) >= P.MAX_ATTEMPTS else attempts[-1]['status'])
    return out


def evaluate_workspace(ws):
    """{subject key: recommendation} from the current workspace contents; nothing is written."""
    manifest, (chosen, history), requests = ws.manifest(), P.usable(ws), ws.requests()
    out = {}
    for key, entry in sorted(manifest['subjects'].items()):
        d = decide(entry['layer_a'], chosen.get(key, {}), statuses_for(key, requests, history))
        out[key] = {**d, 'lane': entry['lane'], 'family': entry['family'], 'sector': entry['sector'],
                    'variant_of': entry['variant_of'], 'variant': entry['variant'], 'analyst_minutes_estimate': entry['analyst_minutes_estimate']}
    return out


def recommend(ws, now=None):
    """Write the next write-once recommendation file. Earlier files are never replaced."""
    subjects = evaluate_workspace(ws)
    record = {'schema': RECOMMENDATIONS_V, 'policy': POLICY, 'routing_mode': ROUTING_MODE, 'fixture': ws.manifest()['fixture'],
              'split': ws.manifest()['split'], 'workspace_manifest_sha256': digest(ws.manifest()),
              'attempts_sha256': digest(sorted(a['raw_sha256'] + a['attempt'] for a in ws.attempts())),
              'subjects': subjects, 'counts': {c: sum(s['classification'] == c for s in subjects.values()) for c in CLASSES},
              'created_at': now or S.utc_now(), 'routing_changed': False, 'human_gates_authoritative': True,
              'human_gates': HUMAN_GATES, 'jev_used': False, 'authorises': []}
    with ws.locked():
        path = ws.write(f'recommendations/REC-{len(ws.files("recommendations")) + 1:04d}.json', record)
    return record, path


def challenges(chosen, reason):
    """First-pass propositions for the adversarial critic, stripped of critic identity, judgment, severity and model."""
    rows, seen = [], set()
    for c in K.FIRST_PASS:
        for a in chosen[c]['output']['assessments'] if c in chosen else []:
            favourable = (reason in ('UNUSUALLY_PROMISING', 'NOVEL_HIGH_UPSIDE') and a['judgment'] == 'PASS'
                          and a['dimension'] in ('internal_novelty', 'economic_significance'))
            if a['judgment'] != 'FAIL' and not favourable:continue
            claim = a['proposition'].strip() or a['justification']
            if (a['dimension'], claim) in seen:continue
            seen.add((a['dimension'], claim))
            rows.append({'dimension': a['dimension'], 'claim_type': 'FAVOURABLE' if favourable else 'ADVERSE', 'claim': claim, 'anchors': a['anchors']})
    return [{'challenge_id': f'CH-{n:02d}', **row} for n, row in enumerate(rows[:20], 1)]


def request_adversarial(ws, key, reason, note=''):
    """Freeze one adversarial request for a subject. The reason must follow from the policy, except an operator's
    HIGH_CONSEQUENCE reason, which needs a written note."""
    entry = ws.manifest()['subjects'].get(key)
    if entry is None or entry['input_sha256'] is None:raise S.ScoutError('no reviewable subject with that key')
    if reason not in SELECTION:raise S.ScoutError(f'selection reasons are {SELECTION}')
    requests = ws.requests()
    if any(r['subject_key'] == key and r['critic'] == 'ADVERSARIAL' for r in requests):raise S.ScoutError('this subject already has its one adversarial request')
    chosen, history = P.usable(ws)
    first = {c: a for c, a in chosen.get(key, {}).items() if c in K.FIRST_PASS}
    if reason == 'HIGH_CONSEQUENCE':
        if len(note.split()) < 5:raise S.ScoutError('a HIGH_CONSEQUENCE selection records the operator\'s concrete reason')
    elif decide(entry['layer_a'], first, statuses_for(key, requests, history))['adversarial_recommended'] != reason:
        raise S.ScoutError('the policy does not select this subject for that reason; adversarial review is selective')
    base = ws.request(entry['requests']['SCIENTIFIC'])['input']
    payload = {**base, 'challenges': K.clean(challenges(first, reason))}
    request = P.make_request('ADVERSARIAL', key, payload, selection={'reason': reason, 'note': note,
                             'first_pass_attempts': sorted(a['attempt'] for a in first.values())})
    with ws.locked():
        ws.write(f'requests/{request["request_id"]}.json', request)
        ws.write(f'requests/{request["request_id"]}.md', K.render('ADVERSARIAL', payload).encode('utf-8'))
    return request
