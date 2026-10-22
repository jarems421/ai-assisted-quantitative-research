"""Offline utility check: naive text search, competent structured-ledger search and Graph v1 on identical records.

Inputs are declared and isolated: three synthetic ledgers plus a fixture requirement vocabulary. No
historical catalogue, report or discovered ledger is read, and the report records the declared
inputs' hashes. The task set and ground truth were written with the fixtures, before any system
ran. Synthetic results show operational behaviour only, never research superiority. This module
also holds the suggestion export used by a later, separately authorised prospective pilot; it runs
no pilot.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

from src.research.graph import baseline as B
from src.research.graph import connections as K
from src.research.graph import model as M
from src.research.graph import operators as O
from src.research.graph.fixtures import REQUIREMENTS
from src.research.graph.project import build
from src.research.graph.rules import View
from src.research.spec import digest

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
SYSTEMS = ('naive_text', 'structured_search', 'graph')


def declared(paths):
    ledgers = [paths['A'], paths['B'], paths['C']]
    return ledgers, {'ledgers': {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ledgers},
                     'requirement_vocabulary_digest': digest(REQUIREMENTS), 'catalogue': None, 'discovered_ledgers': None}


def isolated_graph(ledgers):
    g = build(ledgers, catalogue_path=None, mode='synthetic', with_memory=False, requirements=REQUIREMENTS)
    leaked = [k for k, n in g.nodes.items() if n['kind'].startswith('history') or n['fixture'] not in ('SYNTHETIC', None)]
    if leaked or g.catalogue or g.excluded or len(g.inputs) != len(ledgers):
        raise ValueError(f'evaluation isolation violated: {leaked[:3]} {g.excluded}')
    return g


def graph_answer(g, oid):
    view = View()
    rev = O.revisit(g, oid, view); comp = O.complements(g, oid, view)
    claims = {r['match'].split(':', 1)[1].rsplit('@', 1)[0]: r['match_bases'] for r in rev['results'] if r['match'].startswith('claim:')}
    flagged = any(x['code'] == 'ONLY_NAME_SIMILARITY' for x in rev['rejected'] + comp.get('rejected', [])) or \
        any(a['code'] == 'NO_VERIFIED_IDENTITY' for a in comp['abstentions'])
    contexts = [r for r in comp['results'] if r['match'].startswith('relationship:')]
    return {'claims': claims, 'identity_flagged': flagged, 'contexts': contexts, 'review_items': len(rev['results']) + len(comp['results']),
            'provenance': all(r['match_bases'] and r.get('via') for r in rev['results']), 'rev': rev}


def score(task, connected, flagged=False):
    truth = task['truth']
    if truth == 'CONNECTED':return 'RECOVERED' if connected else 'MISSED'
    if truth == 'NOT_CONNECTED':return 'FALSE_CONNECTION' if connected else 'CORRECTLY_ABSENT'
    return 'PREMATURE_IDENTITY_JOIN' if connected else ('WITHHELD_AND_FLAGGED' if flagged else 'WITHHELD')


def run(paths, timing=False):
    """Compare the systems on the fixed task set. Runtime is reported only when requested (non-deterministic)."""
    ledgers, inputs = declared(paths)
    t0 = time.perf_counter(); g = isolated_graph(ledgers); t_build = time.perf_counter() - t0
    rows, totals, t_graph, t_struct = [], {s: {} for s in SYSTEMS}, 0.0, 0.0
    for task in TASKS:
        campaign, oid = task['observation'].split('/')
        naive = B.naive_text_search(ledgers, campaign, oid)
        t0 = time.perf_counter(); struct = B.structured_search(ledgers, campaign, oid); t_struct += time.perf_counter() - t0
        t0 = time.perf_counter(); graph = graph_answer(g, task['observation']); t_graph += time.perf_counter() - t0
        outcome = {'naive_text': score(task, TARGET_CLAIM in naive), 'structured_search': score(task, TARGET_CLAIM in struct['claims']),
                   'graph': score(task, TARGET_CLAIM in graph['claims'], graph['identity_flagged'])}
        for system, value in outcome.items():totals[system][value] = totals[system].get(value, 0) + 1
        rows.append({'task': task['id'], 'observation': task['observation'], 'truth': task['truth'], 'why': task['why'], **outcome,
                     'naive_matched_terms': naive.get(TARGET_CLAIM, []),
                     'structured_bases': struct['claims'].get(TARGET_CLAIM, {}).get('bases', []),
                     'graph_bases': graph['claims'].get(TARGET_CLAIM, []),
                     'structured_excluded_contexts': struct['excluded_contexts'], 'graph_identity_flagged': graph['identity_flagged'],
                     'review_items': {'naive_text': len(naive), 'structured_search': len(struct['claims']) + len(struct['contexts']),
                                      'graph': graph['review_items']},
                     'requirement_identified': {'naive_text': TARGET_REQUIREMENT in ' '.join(naive.get(TARGET_CLAIM, [])),
                                                'structured_search': 'AUTHOR_TAG_CANDIDATE' in struct['claims'].get(TARGET_CLAIM, {}).get('bases', []),
                                                'graph': any(f'requirement:{TARGET_REQUIREMENT}' in r.get('via', []) for r in graph['rev']['results'])}})
    report = {'banner': M.BANNER, 'scope': 'SYNTHETIC_FIXTURE_FUNCTIONAL_CHECK', 'declared_inputs': inputs,
              'isolation': {'history_nodes': 0, 'catalogue_loaded': False, 'excluded_inputs': 0, 'ledger_discovery': False},
              'tasks': rows, 'totals': totals,
              'provenance_returned': {'naive_text': 'matched substrings only', 'structured_search': 'bases, referenced records, period check',
                                      'graph': 'bases, records, period check, identity status, explanation and first unsupported leap'},
              'interpretation': [
                  'Synthetic look-alikes were constructed to exercise identity and period rules; this shows behaviour, not research superiority.',
                  'A competent structured search matches the graph on every claim connection here; the graph adds identity questions and explanations, not recall.',
                  'No empirical gain is claimed; a prospective pilot must separate graph benefit from extra analyst time.']}
    if timing:report['runtime_seconds'] = {'graph_build': round(t_build, 4), 'graph_queries': round(t_graph, 4), 'structured_search': round(t_struct, 4)}
    return report


def markdown(report):
    lines = ['| Task | Truth | Naive text | Structured search | Graph |', '|---|---|---|---|---|']
    for r in report['tasks']:
        lines.append(f"| {r['task']} | {r['truth']} | {r['naive_text']} | {r['structured_search']} | {r['graph']} |")
    lines += ['', '| Outcome counts | Naive text | Structured search | Graph |', '|---|---|---|---|']
    for k in sorted({k for t in report['totals'].values() for k in t}):
        lines.append(f"| {k} | " + ' | '.join(str(report['totals'][s].get(k, 0)) for s in SYSTEMS) + ' |')
    burden = {s: sum(r['review_items'][s] for r in report['tasks']) for s in SYSTEMS}
    excluded = sum(len(r['structured_excluded_contexts']) for r in report['tasks'])
    lines += ['', f"Items returned for review across tasks: naive text {burden['naive_text']}, structured search {burden['structured_search']}, graph {burden['graph']}.",
              f'Period-incompatible or unresolved relationship contexts excluded by structured search: {excluded}; the graph rejects the same as PERIOD_INCOMPATIBLE.',
              f"Requirement {TARGET_REQUIREMENT} identified for T1: " + ', '.join(f'{k} {v}' for k, v in report['tasks'][0]['requirement_identified'].items()) + '.',
              'Declared inputs only: three synthetic ledgers and a fixture requirement vocabulary; no catalogue, report or discovered ledger.',
              '', *[f'- {x}' for x in report['interpretation']]]
    return '\n'.join(lines)


# -- prospective pilot hook (no pilot is run; see pilot.py for snapshots, logs and blinding) ---------------


def export_suggestions(g, target, ledgers, catalogue=None, known_at=None, cuts=None):
    """Graph suggestions for a target, each flagged with whether competent structured search over the SAME
    knowledge (the same ledgers, plus the same catalogue when the graph includes memory) would also find it."""
    view, out = View(), []
    node = O.resolve(g, target)
    obs = O.records_of(g, node) if g.nodes[node]['kind'] == 'campaign' else [node]
    for o in [x for x in obs if g.nodes[x]['kind'] == 'observation']:
        campaign, oid = o.split(':', 1)[1].rsplit('@', 1)[0].split('/')
        found = B.structured_search(ledgers, campaign, oid, catalogue if g.catalogue else None, known_at, cuts)
        discoverable = set(found['claims']) | {c['record'] for c in found['contexts']} | {f'HIST:{k}' for k in found['catalogue']}
        for r in O.revisit(g, o, view)['results'] + O.complements(g, o, view)['results']:
            key = r['match'].split(':', 1)[1].rsplit('@', 1)[0]
            hist = r['match'].split(':', 1)[1].split('/')[0] if r['match'].startswith('history:') else None
            out.append({'suggestion_id': r['suggestion_id'], 'operator': 'revisit' if 'previous_status' in r else 'complements',
                        'target': r['target'], 'match': r['match'], 'match_bases': r['match_bases'],
                        'baseline_structured_discoverable': key in discoverable or (hist is not None and f'HIST:{hist}' in discoverable),
                        'connection_class': r['connection_class'], 'grounded_explanation_complete': K.provenance_complete(r)})
    return out
