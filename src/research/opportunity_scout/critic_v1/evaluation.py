"""Calibration against independent human anchors, a reproducible review queue, and the autonomy-admission check.

Human anchors are a new versioned instrument (the frozen five-question Jev label packet is unchanged). Labellers see
exactly the blinded input a critic saw, and never any AI or Jev output. Every rate carries its count and a Wilson 95%
interval; recall targets use an exact one-sided Clopper-Pearson bound. Metrics are separated by generation context.
Nothing here can activate AI routing: ``admission`` reports eligibility for an owner decision and always ``activated: False``."""
from __future__ import annotations

from collections import Counter
import hashlib
import hmac
import math

from src.research.spec import digest
from .. import schema as S
from ..post_generation.review import ASSISTANT
from . import packages as P, policy as Q, rubric as K

ANCHOR_PACKET_V, ANCHOR_V, EVALUATION_V = 'SCOUT_CRITIC_ANCHOR_PACKET_V001', 'SCOUT_CRITIC_HUMAN_ANCHOR_V001', 'SCOUT_CRITIC_EVALUATION_V001'
QUEUE_V, ADMISSION_V = 'SCOUT_CRITIC_REVIEW_QUEUE_V001', 'SCOUT_CRITIC_AUTONOMY_ADMISSION_V001'
FUTURE_MODE = 'AI_ROUTINE_TRIAGE_V002_PROPOSED_NOT_ACTIVE'
CONTEXTS = {'FORGE': ('FORGE',), 'EVIDENCE_LED': ('RADAR',), 'OTHER': ('GAP', 'PLAIN')}
ANSWERS = ('yes', 'no', 'unsure')
QUESTIONS = {
    'research_worthy': 'Is this a coherent, falsifiable economic hypothesis worth one bounded next research check? Missing evidence or '
                       'difficult data alone is not a reason for no. Answer yes, no or unsure.',
    'fatal_defect': 'Does the card contain a defect that no reasonable revision could fix without abandoning its mechanism: an incoherent '
                    'mechanism, a circular prediction, an unfalsifiable claim, impossible timing, or a premise contradicted by the supplied '
                    'passages? Answer yes, no or unsure.',
    'fatal_dimension': 'If yes, which requirement: mechanism_coherence, falsifiability, evidence_integrity or temporal_validity. If no, NONE. If unsure, UNSURE or your best guess.',
    'preferred_classification': 'Which disposition would you choose? One of the five definitions below, or UNSURE.'}
DEFINITIONS = {
    'READY_CANDIDATE': 'Coherent and falsifiable, with a clear measurement question and a credible investigation route. Research-worthy, not proven.',
    'INCUBATE': 'Coherent or potentially valuable, but evidence, feasibility or a non-fatal assumption is unresolved. Keep it.',
    'REVISION_REQUIRED': 'A repairable defect, for example an ambiguous variable, a weak falsifier, an overclaim or a duplicate to merge.',
    'REJECT_RECOMMENDED': 'A specific fatal flaw: incoherent mechanism, impossible timing or demonstrably circular prediction.',
    'ESCALATE': 'You cannot responsibly decide, or it needs an expert: a disputed fatal flaw or a novel, high-upside mechanism.'}
ANCHOR = S.obj({'schema': {'const': ANCHOR_V}, 'blind_id': S.LABEL,
    'reviewer': S.obj({'kind': S.enum(('HUMAN', 'SYNTHETIC_FIXTURE')), 'id': S.LABEL}),
    'saw_ai_critic_output': {'const': False}, 'saw_jev_output': {'const': False}, 'independent_of_generation': {'const': True},
    'research_worthy': S.enum(ANSWERS), 'fatal_defect': S.enum(ANSWERS), 'fatal_dimension': S.enum(K.HARD + ('NONE', 'UNSURE')),
    'preferred_classification': S.enum(Q.CLASSES + ('UNSURE',)), 'minutes': S.NUMBER, 'labelled_at': S.TEXT, 'notes': S.TEXT})
PROPOSED_TARGETS = {'confidence': .95, 'retained_recall_lower_bound': .95, 'fatal_detection_lower_bound': .95,
                    'false_acceptance_upper_bound': .10, 'human_human_pairs': 30, 'neutral_variant_groups': 20,
                    'neutral_stability': .95, 'invalid_attempt_rate': .05, 'contexts_required': ('FORGE', 'EVIDENCE_LED')}
AUDIT_RATES_PROPOSED = {'READY_CANDIDATE': 1.0, 'ESCALATE': 1.0, 'REJECT_RECOMMENDED': 1.0, 'REVISION_REQUIRED': .2, 'INCUBATE': .2}
RESOURCE_MINUTES = 240


def wilson(k, n, z=1.959963984540054):
    if not n:return None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(max(0.0, (c - m) / d), 6), round(min(1.0, (c + m) / d), 6)]


def at_least(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def lower_bound(k, n, alpha=.05):
    """Exact one-sided Clopper-Pearson lower bound for a success rate with k successes in n."""
    if not n or not k:return 0.0 if n else None
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if at_least(k, n, mid) < alpha else (lo, mid)
    return round(lo, 6)


def required_n(target=.95, alpha=.05, failures=0):
    """Smallest number of independently labelled cases whose lower bound reaches ``target`` with ``failures`` misses."""
    return next(n for n in range(failures + 1, 20000) if lower_bound(n - failures, n, alpha) >= target)


def proportion(k, n, bound=False):
    out = {'k': k, 'n': n, 'rate': round(k / n, 6) if n else None, 'wilson95': wilson(k, n)}
    if bound:out['one_sided_lower95'] = lower_bound(k, n)
    return out


def draw(seed, key):
    return int(hmac.new(str(seed).encode(), key.encode(), hashlib.sha256).hexdigest()[:16], 16) / 2 ** 64


def originals(ws):
    return {k: e for k, e in ws.manifest()['subjects'].items() if not e['variant_of'] and e['input_sha256']}


def anchor_packet(ws, salt):
    """Blinded items for independent human anchors: each subject's exact critic input, no AI or Jev output."""
    if not isinstance(salt, str) or len(salt) < 20:raise S.ScoutError('use a private blinding salt of at least 20 characters')
    manifest, assignments, rows = ws.manifest(), {}, []
    for key, entry in sorted(originals(ws).items()):
        bid = 'ANCHOR-' + hmac.new(salt.encode(), key.encode(), hashlib.sha256).hexdigest()[:16]
        assignments[bid] = key
        rows.append({'blind_id': bid, 'input': ws.request(entry['requests']['SCIENTIFIC'])['input']})
    rows.sort(key=lambda r: r['blind_id'])
    body = {'schema': ANCHOR_PACKET_V, 'fixture': manifest['fixture'], 'items': rows, **reviewer_text()}
    key = {'schema': ANCHOR_PACKET_V + '_KEY', 'fixture': manifest['fixture'], 'assignments': assignments, 'salt_sha256': S.hash_text(salt),
           'reviewer_facing_sha256': digest(body), 'workspace_manifest_sha256': digest(manifest)}
    return {**body, 'key_sha256': digest(key)}, key


def reviewer_text():
    return {'questions': QUESTIONS, 'definitions': DEFINITIONS,
            'label_template': {'schema': ANCHOR_V, 'blind_id': '<blind_id>', 'reviewer': {'kind': 'HUMAN', 'id': '<your name>'},
                               'saw_ai_critic_output': False, 'saw_jev_output': False, 'independent_of_generation': True,
                               'research_worthy': '<yes | no | unsure>', 'fatal_defect': '<yes | no | unsure>',
                               'fatal_dimension': '<requirement | NONE | UNSURE>', 'preferred_classification': '<class | UNSURE>',
                               'minutes': '<number or UNKNOWN>', 'labelled_at': '<ISO time with zone>', 'notes': '<short reason>'},
            'instructions': 'Judge each card from its input only. Do not look at any AI critic output, Jev output, recommendation, '
                            'other labeller or the private key. Unsure is a legitimate answer. Record your real minutes or UNKNOWN.',
            'blinding': 'PARTIAL_PROCEDURAL', 'ai_output_included': False, 'jev_output_included': False, 'authorises': []}


def check_anchors(packet, key, anchors):
    if not isinstance(packet, dict) or packet.get('schema') != ANCHOR_PACKET_V:raise S.ScoutError('not a critic anchor packet')
    body = {k: v for k, v in packet.items() if k != 'key_sha256'}
    if packet['key_sha256'] != digest(key) or digest(body) != key.get('reviewer_facing_sha256'):raise S.ScoutError('anchor packet or key changed after freeze')
    if {k: v for k, v in body.items() if k not in ('schema', 'fixture', 'items')} != reviewer_text():raise S.ScoutError('anchor questions or instructions differ from the frozen wording')
    if not isinstance(anchors, list):raise S.ScoutError('anchors are a list of label records')
    kind, seen = 'SYNTHETIC_FIXTURE' if packet['fixture'] == 'SYNTHETIC' else 'HUMAN', set()
    for n, a in enumerate(anchors, 1):
        S.validate(ANCHOR, a, f'anchor {n}')
        if a['reviewer']['kind'] != kind:raise S.ScoutError(f'anchor {n}: this packet accepts {kind} anchors only; AI opinions are never relabelled as human')
        if ASSISTANT.search(a['reviewer']['id']):raise S.ScoutError(f'anchor {n}: an assistant or model is never an independent human anchor')
        if a['blind_id'] not in key['assignments'] or (a['blind_id'], a['reviewer']['id']) in seen:raise S.ScoutError(f'anchor {n}: unknown item or duplicate label')
        if (a['fatal_defect'] == 'yes') != (a['fatal_dimension'] in K.HARD) and a['fatal_defect'] != 'unsure':
            raise S.ScoutError(f'anchor {n}: a fatal defect names its requirement; no defect is NONE')
        seen.add((a['blind_id'], a['reviewer']['id'])); S.timestamp(a['labelled_at'])
    return anchors


def consensus(values):
    decisive = {v for v in values if v not in ('unsure', 'UNSURE')}
    return 'UNLABELLED' if not values else 'UNSURE' if not decisive else decisive.pop() if len(decisive) == 1 else 'DISPUTED'


def label_metrics(rows):
    rw = [r for r in rows if r['research_worthy'] == 'yes']
    fatal = [r for r in rows if r['fatal_defect'] == 'yes']
    weak = [r for r in rows if r['research_worthy'] == 'no' or r['fatal_defect'] == 'yes']
    claims = [r for r in rows if r['rec']['fatal']['first_pass'] or r['rec']['fatal']['adversarial']]
    judged = [r for r in claims if r['fatal_defect'] in ('yes', 'no')]
    preferred = [r for r in rows if r['preferred'] in Q.CLASSES]
    c = lambda r: r['rec']['classification']
    return {'subjects': len(rows), 'classification_distribution': {x: sum(c(r) == x for r in rows) for x in Q.CLASSES},
        'research_worthy_retained_recall': proportion(sum(c(r) != 'REJECT_RECOMMENDED' for r in rw), len(rw), True),
        'research_worthy_advanced_recall': proportion(sum(c(r) in ('READY_CANDIDATE', 'ESCALATE') for r in rw), len(rw), True),
        'false_rejection_rate': proportion(sum(c(r) == 'REJECT_RECOMMENDED' for r in rw), len(rw)),
        'fatal_detected': proportion(sum(c(r) == 'REJECT_RECOMMENDED' or (c(r) == 'ESCALATE' and r['rec']['rule'].startswith('R3')) for r in fatal), len(fatal), True),
        'fatal_rejected': proportion(sum(c(r) == 'REJECT_RECOMMENDED' for r in fatal), len(fatal)),
        'false_acceptance_rate': proportion(sum(c(r) == 'READY_CANDIDATE' for r in weak), len(weak)),
        'alleged_fatal_precision': proportion(sum(r['fatal_defect'] == 'yes' for r in judged), len(judged)),
        'alleged_fatal_without_decisive_label': len(claims) - len(judged),
        'escalation_rate': proportion(sum(c(r) == 'ESCALATE' for r in rows), len(rows)),
        'agreement_with_human_preferred_class': proportion(sum(c(r) == r['preferred'] for r in preferred), len(preferred)),
        'labels_disputed_or_unsure': sum(r['research_worthy'] in ('DISPUTED', 'UNSURE') for r in rows)}


def kappa(pairs):
    if not pairs:return None
    n, labels = len(pairs), sorted({x for p in pairs for x in p})
    observed = sum(a == b for a, b in pairs) / n
    expected = sum((sum(a == l for a, _ in pairs) / n) * (sum(b == l for _, b in pairs) / n) for l in labels)
    return round((observed - expected) / (1 - expected), 6) if expected < 1 else None


def critic_metrics(ws, recs):
    chosen, history = P.usable(ws)
    attempts = [a for rows in history.values() for a in rows]
    per = {}
    for critic in K.CRITICS:
        outs = [v[critic]['output'] for v in chosen.values() if critic in v]
        per[critic] = {'answers': len(outs), 'judgments': {d: dict(Counter(K.assessments(o)[d]['judgment'] for o in outs)) for d in K.DIMENSIONS},
                       'potentially_fatal': sum(a['potentially_fatal'] for o in outs for a in o['assessments'])}
    agreement = {}
    for d in K.DIMENSIONS:
        pairs = [(K.assessments(v['SCIENTIFIC']['output'])[d]['judgment'], K.assessments(v['ECONOMIC']['output'])[d]['judgment'])
                 for v in chosen.values() if 'SCIENTIFIC' in v and 'ECONOMIC' in v]
        pairs = [p for p in pairs if 'NOT_APPLICABLE' not in p]
        agreement[d] = {'pairs': len(pairs), 'agreement': proportion(sum(a == b for a, b in pairs), len(pairs)), 'cohen_kappa': kappa(pairs)}
    groups = {'NEUTRAL_PADDING': [], 'CONFIDENT_FRAMING': []}
    for key, r in recs.items():
        if r['variant']:groups[r['variant']].append((recs[r['variant_of']], r))
    order = {'REJECT_RECOMMENDED': 0, 'REVISION_REQUIRED': 1, 'INCUBATE': 2, 'ESCALATE': 2, 'READY_CANDIDATE': 3}
    usage = {}
    for field in ('input_tokens', 'output_tokens', 'cost', 'latency_ms'):
        values = [a['provenance']['usage'][field] for a in attempts]
        usage[field] = S.UNKNOWN if not values or S.UNKNOWN in values else sum(values)  # never a partial sum
    status = Counter(a['status'] for a in attempts)
    return {'per_critic': per, 'inter_critic_agreement_scientific_vs_economic': agreement,
            'stability': {'neutral_padding_same_classification': proportion(sum(o['classification'] == v['classification'] for o, v in groups['NEUTRAL_PADDING']), len(groups['NEUTRAL_PADDING'])),
                          'confident_framing_not_improved': proportion(sum(order[v['classification']] <= order[o['classification']] for o, v in groups['CONFIDENT_FRAMING']), len(groups['CONFIDENT_FRAMING']))},
            'attempts': {'total': len(attempts), **{s: status[s] for s in ('VALID', 'INVALID', 'REFUSED')},
                         'invalid_or_refused_rate': proportion(status['INVALID'] + status['REFUSED'], len(attempts))},
            'usage_totals': usage, 'subjects_with_valid_first_pass': sum(all(c in v for c in K.FIRST_PASS) for v in chosen.values())}


def diversity(rows):
    def spread(items):return {'families': len({r['family'] for r in items}), 'sectors': len({r['sector'] for r in items}), 'subjects': len(items)}
    return {'all': spread(rows), 'retained_not_reject': spread([r for r in rows if r['classification'] != 'REJECT_RECOMMENDED']),
            'ready_or_escalated': spread([r for r in rows if r['classification'] in ('READY_CANDIDATE', 'ESCALATE')])}


def evaluate(ws, packet=None, key=None, anchors=()):
    """Descriptive calibration report. Without anchors only the AI-side measurements are reported."""
    manifest, recs = ws.manifest(), Q.evaluate_workspace(ws)
    main = {k: r for k, r in recs.items() if not r['variant']}
    rows, labels = [], []
    if packet is not None:
        labels = check_anchors(packet, key, list(anchors))
        if key['workspace_manifest_sha256'] != digest(manifest):raise S.ScoutError('anchor packet was frozen from a different workspace')
    by_key = {}
    for a in labels:by_key.setdefault(key['assignments'][a['blind_id']], []).append(a)
    for k, r in sorted(main.items()):
        given = by_key.get(k, [])
        rows.append({'key': k, 'rec': r, 'lane': r['lane'], 'research_worthy': consensus([a['research_worthy'] for a in given]),
                     'fatal_defect': consensus([a['fatal_defect'] for a in given]), 'preferred': consensus([a['preferred_classification'] for a in given])})
    hh = {}
    for q in ('research_worthy', 'fatal_defect', 'preferred_classification'):
        pairs = [(x[q], y[q]) for rs in by_key.values() for i, x in enumerate(rs) for y in rs[i + 1:]]
        hh[q] = {'pairs': len(pairs), 'agreement': proportion(sum(a == b for a, b in pairs), len(pairs)), 'cohen_kappa': kappa(pairs)}
    minutes = [a['minutes'] for a in labels]
    known = S.UNKNOWN if not minutes or S.UNKNOWN in minutes else sum(minutes)
    useful = sum(r['rec']['classification'] == 'READY_CANDIDATE' and r['research_worthy'] == 'yes' for r in rows)
    minimum = required_n(PROPOSED_TARGETS['retained_recall_lower_bound'])
    contexts = {name: label_metrics([r for r in rows if r['lane'] in lanes]) for name, lanes in CONTEXTS.items()}
    contexts['ALL'] = label_metrics(rows)
    return {'schema': EVALUATION_V, 'fixture': manifest['fixture'], 'split': manifest['split'], 'labels': 'NONE' if not labels else labels[0]['reviewer']['kind'],
            'workspace_manifest_sha256': digest(manifest), 'policy': Q.POLICY, 'contexts': contexts, 'critics': critic_metrics(ws, recs),
            'diversity': diversity([{'classification': r['classification'], 'family': r['family'], 'sector': r['sector']} for r in main.values()]),
            'human_human': hh, 'human_effort': {'anchor_minutes': known, 'anchors': len(labels)},
            'useful_ready_per_human_hour': S.UNKNOWN if known == S.UNKNOWN or not known else round(useful / (known / 60), 6),
            'sample_plan': {'per_context_minimum_research_worthy': minimum, 'per_context_minimum_fatal': minimum,
                            'basis': f'zero misses in {minimum} gives a one-sided 95% lower bound of at least 0.95 (exact binomial)',
                            'with_one_miss': required_n(failures=1), 'with_two_misses': required_n(failures=2),
                            'status': {name: ('SUFFICIENT' if m['research_worthy_retained_recall']['n'] >= minimum and m['fatal_detected']['n'] >= minimum
                                              else 'INSUFFICIENT_SAMPLE') for name, m in contexts.items()}},
            'targets_are_proposed_not_validated': PROPOSED_TARGETS, 'calibration_established': False,
            'interpretation': ['Agreement with independent human anchors on these cards describes these cards only.',
                               'Synthetic fixtures establish software behaviour, never real-world calibration.',
                               'A model\'s stated confidence is never used as a probability of being correct.'], 'authorises': []}


def queue(recommendations, seed, mode='CALIBRATION_ALL'):
    """Reproducible review queue from a frozen recommendation file and a recorded seed. CALIBRATION_ALL (active in V001):
    every original card goes to independent human labelling. SELECTIVE_PROPOSED: the steady-state design, computed so its
    workload can be studied, never active in V001."""
    if mode not in ('CALIBRATION_ALL', 'SELECTIVE_PROPOSED'):raise S.ScoutError('mode is CALIBRATION_ALL or SELECTIVE_PROPOSED')
    if recommendations.get('schema') != Q.RECOMMENDATIONS_V:raise S.ScoutError('a frozen recommendation file is required')
    if not isinstance(seed, (int, str)) or isinstance(seed, bool) or str(seed) == '':raise S.ScoutError('record an explicit sampling seed')
    subjects = {k: r for k, r in recommendations['subjects'].items() if not r['variant']}
    items, skipped = [], []
    for k, r in sorted(subjects.items()):
        cls, reasons = r['classification'], []
        if mode == 'CALIBRATION_ALL':reasons = ['CALIBRATION_LABEL_REQUIRED']
        else:
            if cls == 'ESCALATE':reasons.append('ESCALATED_' + r['rule'])
            if cls == 'READY_CANDIDATE':reasons.append('HUMAN_READY_GATE')
            if cls == 'REJECT_RECOMMENDED':reasons.append('REJECT_AUDIT' + ('_CORRELATED_SUPPORT' if r['fatal']['correlated_support'] else ''))
            if cls in ('INCUBATE', 'REVISION_REQUIRED') and r['adversarial_recommended'] in ('NOVEL_HIGH_UPSIDE', 'UNUSUALLY_PROMISING'):
                reasons.append('POSSIBLE_VALUABLE_FALSE_NEGATIVE')
            if cls in ('READY_CANDIDATE', 'ESCALATE') and (r['analyst_minutes_estimate'] == S.UNKNOWN or r['analyst_minutes_estimate'] >= RESOURCE_MINUTES):
                reasons.append('SIGNIFICANT_OR_UNKNOWN_RESEARCH_RESOURCES')
            if not reasons and draw(seed, k) < AUDIT_RATES_PROPOSED[cls]:reasons.append('RANDOM_AUDIT')
        tier = 1 if any(x.startswith(('ESCALATED_R1', 'ESCALATED_R3')) for x in reasons) else 2 if any(x.startswith('ESCALATED') or x.startswith('POSSIBLE') for x in reasons) \
            else 3 if any(x.startswith('REJECT') for x in reasons) else 4 if 'HUMAN_READY_GATE' in reasons else 5
        row = {'subject_key': k, 'classification': cls, 'lane': r['lane'], 'reasons': reasons, 'tier': tier, 'draw': round(draw(seed, k), 12)}
        (items if reasons else skipped).append(row)
    items.sort(key=lambda x: (x['tier'], x['draw'], x['subject_key']))
    return {'schema': QUEUE_V, 'mode': mode, 'active': mode == 'CALIBRATION_ALL', 'seed': seed,
            'recommendations_sha256': digest(recommendations), 'items': items, 'not_queued': [x['subject_key'] for x in skipped],
            'projected_human_fraction': round(len(items) / len(subjects), 6) if subjects else None,
            'audit_rates_proposed': AUDIT_RATES_PROPOSED, 'resource_minutes_threshold': RESOURCE_MINUTES,
            'note': 'Random audits of incubated, revised and rejected cards keep false negatives visible. Jev plays no part.', 'authorises': []}


def admission(evaluation, benchmark_passes):
    """Whether calibration evidence could be put to the owner for the future routing mode. Never activates anything."""
    if evaluation.get('schema') != EVALUATION_V:raise S.ScoutError('admission reads a critic evaluation report')
    t, reasons = PROPOSED_TARGETS, []
    if evaluation['fixture'] == 'SYNTHETIC' or evaluation['labels'] != 'HUMAN':reasons.append('only independent human anchors on real cards can count; synthetic evidence never admits routing')
    if evaluation['split'] != 'HOLDOUT':reasons.append('admission is judged on an untouched HOLDOUT workspace, never on tuning data')
    if not benchmark_passes:reasons.append('the frozen synthetic adversarial benchmark must still pass')
    for name in t['contexts_required']:
        m = evaluation['contexts'][name]
        if (m['research_worthy_retained_recall']['one_sided_lower95'] or 0) < t['retained_recall_lower_bound']:reasons.append(f'{name}: research-worthy retention lower bound below {t["retained_recall_lower_bound"]}')
        if (m['fatal_detected']['one_sided_lower95'] or 0) < t['fatal_detection_lower_bound']:reasons.append(f'{name}: fatal-defect detection lower bound below {t["fatal_detection_lower_bound"]}')
        upper = (m['false_acceptance_rate']['wilson95'] or [0, 1])[1]
        if upper > t['false_acceptance_upper_bound']:reasons.append(f'{name}: false-acceptance upper bound above {t["false_acceptance_upper_bound"]}')
    if evaluation['human_human']['research_worthy']['pairs'] < t['human_human_pairs']:reasons.append('human-human agreement baseline too small')
    stab = evaluation['critics']['stability']['neutral_padding_same_classification']
    if stab['n'] < t['neutral_variant_groups'] or (stab['rate'] or 0) < t['neutral_stability']:reasons.append('stability under neutral variants not demonstrated')
    bad = evaluation['critics']['attempts']['invalid_or_refused_rate']
    if bad['n'] == 0 or bad['rate'] > t['invalid_attempt_rate']:reasons.append('invalid-answer rate not demonstrated low enough')
    return {'schema': ADMISSION_V, 'mode_considered': FUTURE_MODE, 'eligible_for_owner_consideration': not reasons, 'reasons': reasons,
            'targets_are_proposed_not_validated': t, 'activated': False,
            'activation_path': 'NONE: V001 contains no AI routing code. A future version needs this evidence and an explicit owner decision.',
            'consequential_gates_unchanged': Q.HUMAN_GATES, 'authorises': []}
