"""Offline utility check: ordinary ledger search versus graph operators on identical records.

The task set and its ground truth were written with the synthetic fixtures, before either system
was run. Synthetic results show operational behaviour only, never research superiority. This
module also defines the suggestion export and adjudication-log format for a later, separately
authorised prospective pilot; it runs no pilot.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from src.research.graph import model as M
from src.research.graph import operators as O
from src.research.graph.project import build
from src.research.graph.rules import View

TASKS = (
    {'id': 'T1', 'observation': 'DLC-GSYN-B/OBS-GB-1', 'truth': 'CONNECTED',
     'why': 'Same identified facility; a documented take-or-pay relationship covers the date; the claim is blocked by exactly this quantity.'},
    {'id': 'T2', 'observation': 'DLC-GSYN-C/OBS-GC-1', 'truth': 'NOT_CONNECTED', 'why': 'A different facility (T-7B) with a similar name.'},
    {'id': 'T3', 'observation': 'DLC-GSYN-C/OBS-GC-2', 'truth': 'IDENTITY_UNPROVEN', 'why': 'Company named only; no identifier proves it is Echo.'},
    {'id': 'T4', 'observation': 'DLC-GSYN-C/OBS-GC-3', 'truth': 'NOT_CONNECTED', 'why': 'Echo operates Terminal Nine only from 2010; the observation is from 2000.'},
    {'id': 'T5', 'observation': 'DLC-GSYN-C/OBS-GC-4', 'truth': 'IDENTITY_UNPROVEN', 'why': 'Identified only by a ticker.'},
)
TARGET_CLAIM = 'DLC-GSYN-A/CAND-GA-1'
TARGET_REQUIREMENT = 'REQ_REALISED_ACTIVITY'


def read_ledger(path):
    return [json.loads(line) for line in Path(path).read_bytes().splitlines()]


def observation_terms(events, oid):
    o = next(e['record'] for e in reversed(events) if e['type'] == 'observation' and e['record']['id'] == oid)
    ids = {o['entity']['id']} | {ev['sha256'] for ev in o['evidence'] if ev['sha256']}
    tags = {v for _, v in M.TAG.findall(' '.join([o['statement'], o['why_informative']]))}
    return o, ids, tags, M.keywords(o['statement'])


def baseline(ledgers, campaign, oid, keywords=True):
    """Ordinary search. With keywords: identifier, tag and word matches in other ledgers' candidate records.
    Without: exact identifiers/tags anywhere in other ledgers, joined to claims that reference the hit record."""
    data = {Path(p).name: read_ledger(p) for p in ledgers}
    own = next(n for n, ev in data.items() if ev[0]['record']['id'] == campaign)
    o, ids, tags, words = observation_terms(data[own], oid)
    claims, contexts = {}, []
    for name, events in data.items():
        if name == own:continue
        cid = events[0]['record']['id']
        candidates = [e['record'] for e in events if e['type'] == 'candidate']
        for e in events:
            text = json.dumps(e['record'], ensure_ascii=False)
            hit = sorted({t for t in ids | tags if t in text})
            if keywords and e['type'] == 'candidate':hit += sorted(w for w in words if w in text.lower())
            if not hit:continue
            r = e['record']
            if e['type'] == 'candidate':claims.setdefault(f"{cid}/{r['id']}", set()).update(hit); continue
            if keywords:continue
            if e['type'] == 'relationship':contexts.append({'record': f"{cid}/{r['id']}", 'period': r['period'], 'matched': hit})
            for c in candidates:
                if r.get('id') in c['predictor']['observation_ids'] + c['exposure']['relationship_ids'] + c['outcome']['derived_from_observations']:
                    claims.setdefault(f"{cid}/{c['id']}", set()).update(hit)
    return {k: sorted(v) for k, v in claims.items()}, contexts


def graph_answer(g, oid):
    """Claims suggested for an observation, identity questions surfaced and period-incompatible contexts returned."""
    view = View()
    rev = O.revisit(g, oid, view); comp = O.complements(g, oid, view)
    claims = {r['match'].split(':', 1)[1].rsplit('@', 1)[0]: r['match_bases'] for r in rev['results'] if r['match'].startswith('claim:')}
    identity_flags = [x for x in rev['rejected'] + comp.get('rejected', []) if x['code'] == 'ONLY_NAME_SIMILARITY']
    abstained_identity = any(a['code'] == 'NO_VERIFIED_IDENTITY' for a in comp['abstentions'])
    period_contexts = [r for r in comp['results'] if r['match'].startswith('relationship:')]
    complete = all(r['match_bases'] and r.get('via') for r in rev['results'])
    return claims, bool(identity_flags) or abstained_identity, period_contexts, complete, rev


def score(task, connected, identity_flagged=False):
    truth = task['truth']
    if truth == 'CONNECTED':return 'RECOVERED' if connected else 'MISSED'
    if truth == 'NOT_CONNECTED':return 'FALSE_CONNECTION' if connected else 'CORRECTLY_ABSENT'
    return 'PREMATURE_IDENTITY_JOIN' if connected else ('WITHHELD_AND_FLAGGED' if identity_flagged else 'WITHHELD')


def run(paths, timing=False):
    """Compare the three approaches on the fixed task set. Runtime is reported only when requested (non-deterministic)."""
    ledgers = [paths['A'], paths['B'], paths['C']]
    started = time.perf_counter(); g = build(ledgers, mode='synthetic', with_memory=False); built = time.perf_counter() - started
    rows, totals = [], {s: {} for s in ('text_search', 'identifier_search', 'graph')}
    for task in TASKS:
        campaign, oid = task['observation'].split('/')
        text_claims, _ = baseline(ledgers, campaign, oid, keywords=True)
        id_claims, id_contexts = baseline(ledgers, campaign, oid, keywords=False)
        graph_claims, flagged, contexts, complete, rev = graph_answer(g, task['observation'])
        outcome = {'text_search': score(task, TARGET_CLAIM in text_claims), 'identifier_search': score(task, TARGET_CLAIM in id_claims),
                   'graph': score(task, TARGET_CLAIM in graph_claims, flagged)}
        for system, value in outcome.items():totals[system][value] = totals[system].get(value, 0) + 1
        incompatible_id = [c for c in id_contexts if task['truth'] == 'NOT_CONNECTED' and c['period']['start'] > '2000-12-31']
        rows.append({'task': task['id'], 'observation': task['observation'], 'truth': task['truth'], 'why': task['why'], **outcome,
                     'text_search_matched_terms': text_claims.get(TARGET_CLAIM, []), 'identifier_search_matched_terms': id_claims.get(TARGET_CLAIM, []),
                     'graph_match_bases': graph_claims.get(TARGET_CLAIM, []), 'graph_identity_flagged': flagged,
                     'identifier_search_period_incompatible_context': len(incompatible_id), 'graph_period_incompatible_context': len(contexts) if task['truth'] == 'NOT_CONNECTED' else 0,
                     'graph_provenance_complete': complete,
                     'requirement_identified': {'text_search': TARGET_REQUIREMENT in ' '.join(text_claims.get(TARGET_CLAIM, [])),
                                                'identifier_search': TARGET_REQUIREMENT in ' '.join(id_claims.get(TARGET_CLAIM, [])),
                                                'graph': any(f'requirement:{TARGET_REQUIREMENT}' in r.get('via', []) for r in rev['results'])}})
    report = {'banner': M.BANNER, 'scope': 'SYNTHETIC_FIXTURE_FUNCTIONAL_CHECK', 'tasks': rows, 'totals': totals,
              'interpretation': ['Synthetic look-alikes were constructed to exercise identity and period rules; this shows behaviour, not research superiority.',
                                 'All three approaches can recover the true connection; differences here are in false or premature joins, period checks and explanations.',
                                 'No empirical gain is claimed; a prospective pilot must separate graph benefit from extra analyst time.']}
    if timing:report['runtime_seconds'] = {'graph_build': round(built, 4)}
    return report


def markdown(report):
    lines = ['| Task | Truth | Text search | Identifier search | Graph | Graph bases |', '|---|---|---|---|---|---|']
    for r in report['tasks']:
        lines.append(f"| {r['task']} | {r['truth']} | {r['text_search']} | {r['identifier_search']} | {r['graph']} | {', '.join(r['graph_match_bases']) or '-'} |")
    lines += ['', '| Outcome counts | Text search | Identifier search | Graph |', '|---|---|---|---|']
    keys = sorted({k for t in report['totals'].values() for k in t})
    for k in keys:lines.append(f"| {k} | {report['totals']['text_search'].get(k, 0)} | {report['totals']['identifier_search'].get(k, 0)} | {report['totals']['graph'].get(k, 0)} |")
    period = sum(r['identifier_search_period_incompatible_context'] for r in report['tasks'])
    lines += ['', f'Period-incompatible relationship context returned: identifier search {period}; graph '
                  f"{sum(r['graph_period_incompatible_context'] for r in report['tasks'])} (the graph rejects it as PERIOD_INCOMPATIBLE).",
              f"Requirement {TARGET_REQUIREMENT} identified for T1: " + ', '.join(f'{k} {v}' for k, v in report['tasks'][0]['requirement_identified'].items()) + '.']
    lines += ['', *[f'- {x}' for x in report['interpretation']]]
    return '\n'.join(lines)


# -- prospective pilot hooks (no pilot is run) ----------------------------------------------------

FOUND_VIA = ('GRAPH_ONLY', 'BASELINE_SEARCH_DISCOVERABLE', 'ANALYST_EXTRA_TIME', 'BOTH')
OUTCOMES = ('CONFIRMED_AGAINST_ORIGINALS', 'PLAUSIBLE_UNVERIFIED', 'REJECTED_FALSE', 'REJECTED_TRIVIAL', 'NOT_REVIEWED')
LOG_KEYS = ('suggestion_id', 'operator', 'found_via', 'outcome', 'analyst_minutes', 'arm_time_budget_minutes', 'adjudicator', 'recorded_at_utc',
            'discovery_lab_record', 'notes')


def export_suggestions(g, target, ledgers):
    """revisit/complements suggestions for a target, each flagged with whether ordinary search would also find it."""
    view, out = View(), []
    node = O.resolve(g, target)
    obs = O.records_of(g, node) if g.nodes[node]['kind'] == 'campaign' else [node]
    for o in [x for x in obs if g.nodes[x]['kind'] == 'observation']:
        campaign, oid = o.split(':', 1)[1].rsplit('@', 1)[0].split('/')
        text_claims, _ = baseline(ledgers, campaign, oid, True); id_claims, _ = baseline(ledgers, campaign, oid, False)
        for r in O.revisit(g, o, view)['results'] + O.complements(g, o, view)['results']:
            key = r['match'].split(':', 1)[1].rsplit('@', 1)[0]
            out.append({'suggestion_id': r['suggestion_id'], 'operator': 'revisit' if 'previous_status' in r else 'complements',
                        'target': r['target'], 'match': r['match'], 'match_bases': r['match_bases'],
                        'baseline_text_discoverable': key in text_claims, 'baseline_identifier_discoverable': key in id_claims})
    return out


def validate_log(path):
    """Validate an adjudication log (JSONL). Returns counts; raises ValueError on an invalid line."""
    counts = {}
    for n, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        r = json.loads(line)
        if tuple(sorted(r)) != tuple(sorted(LOG_KEYS)):raise ValueError(f'line {n}: fields must be exactly {LOG_KEYS}')
        if not re.fullmatch(r'SUG-[0-9a-f]{12}', r['suggestion_id']):raise ValueError(f'line {n}: invalid suggestion id')
        if r['found_via'] not in FOUND_VIA or r['outcome'] not in OUTCOMES:raise ValueError(f'line {n}: invalid found_via/outcome')
        if r['analyst_minutes'] != 'UNKNOWN' and (not isinstance(r['analyst_minutes'], (int, float)) or r['analyst_minutes'] < 0):
            raise ValueError(f'line {n}: analyst_minutes must be a non-negative number or UNKNOWN')
        if r['outcome'] == 'CONFIRMED_AGAINST_ORIGINALS' and not r['discovery_lab_record']:
            raise ValueError(f'line {n}: a confirmed connection must cite the Discovery Lab record that now holds it')
        if not r['adjudicator'] or r['adjudicator'].lower().startswith(('claude', 'assistant')):
            raise ValueError(f'line {n}: adjudication is a human decision')
        counts[r['outcome']] = counts.get(r['outcome'], 0) + 1
    return counts
