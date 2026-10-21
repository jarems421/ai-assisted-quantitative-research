"""Competent structured-ledger search: the comparison baseline for Graph v1.

This is what a careful analyst can do with Discovery Lab ledgers and the historical catalogue
*without* the graph projection: load ledgers through Discovery Lab's own validated loader, use
latest versions, match exact identifiers (never substrings), content-evidence hashes and exact
requirement tags, follow a claim's recorded references, apply relationship validity periods, and
refuse name-only or ticker-only joins. It does not raise identity questions, explain paths,
group shared blockers or suppress hubs; those are the graph's claimed increments.
"""
from __future__ import annotations

from pathlib import Path

from src.research.discovery.ledger import Ledger
from src.research.discovery.review import covered
from src.research.discovery import records as R
from src.research.graph import model as M
from src.research.graph.project import parse_time, state_at

CONTENT_ROLES = ('evidence',)


def unjoinable(identifier):
    return identifier.startswith(('NAME:', 'TICKER:'))


def content_hashes(record, kind):
    if kind == 'relationship':
        items = record['evidence'] + record['quantity_transfer']['evidence']
    elif kind == 'candidate':
        items = record['outcome']['evidence'] + record['closest_substitute']['evidence']
    else:
        items = record['evidence']
    return {ev['sha256'] for ev in items if ev.get('sha256')}


def load_states(ledgers, known_at=None):
    cutoff = parse_time(known_at) if known_at else None
    states = {}
    for path in ledgers:
        s = state_at(Ledger(path).load(), cutoff)
        if s is not None:states[s.campaign['id']] = s
    return states


def target_terms(s, oid):
    o = s.latest('observation', oid)
    text = ' '.join([o['statement'], o['why_informative'], *o['missing_evidence']])
    tags = {v for k, v in M.TAG.findall(text) if k == 'MEASURES'}
    return o, o['entity']['id'], content_hashes(o, 'observation'), tags


def structured_search(ledgers, campaign, oid, catalogue=None, known_at=None):
    """Claims and context in other campaigns (and historical catalogue entries) connected by exact structure."""
    states = load_states(ledgers, known_at)
    if campaign not in states:raise ValueError(f'{campaign} is not recorded at the known-at time')
    o, ident, hashes, tags = target_terms(states[campaign], oid)
    moment = R.when(o['clocks']['economic_occurrence']['value'], 'occurrence')
    result = {'observation': f'{campaign}/{oid}', 'claims': {}, 'contexts': [], 'excluded_contexts': [], 'catalogue': {},
              'identity_join_refused': unjoinable(ident)}
    for cid, s in sorted(states.items()):
        if cid == campaign:continue
        hit_records = {}
        for rid, versions in s.versions['observation'].items():
            x = versions[-1]; bases = set()
            if not unjoinable(ident) and x['entity']['id'] == ident:bases.add('EXACT_ENTITY_ID')
            if hashes & content_hashes(x, 'observation'):bases.add('EXACT_DOCUMENT_HASH')
            if bases:hit_records[rid] = bases; result['contexts'].append({'record': f'{cid}/{rid}', 'bases': sorted(bases)})
        for rid, versions in s.versions['relationship'].items():
            x = versions[-1]; bases = set()
            if not unjoinable(ident) and ident in (x['source_entity']['id'], x['target_entity']['id']):bases.add('EXACT_ENTITY_ID')
            if hashes & content_hashes(x, 'relationship'):bases.add('EXACT_DOCUMENT_HASH')
            if not bases:continue
            inside = covered(x['period'], moment) if moment else None
            if inside is not True:
                result['excluded_contexts'].append({'record': f'{cid}/{rid}', 'reason': 'PERIOD_INCOMPATIBLE' if inside is False else 'PERIOD_UNRESOLVED'})
                continue
            if x['status'] == 'VERIFIED' and x['basis'] == 'DOCUMENTED':bases.add('DOCUMENTED_RELATIONSHIP_COMPATIBLE_PERIOD')
            hit_records[rid] = bases; result['contexts'].append({'record': f'{cid}/{rid}', 'bases': sorted(bases), 'period': x['period']})
        for rid, versions in s.versions['candidate'].items():
            c = versions[-1]; bases = set(); via = []
            refs = c['predictor']['observation_ids'] + c['outcome']['derived_from_observations'] + c['exposure']['relationship_ids']
            for ref in refs:
                if ref in hit_records:bases |= hit_records[ref]; via.append(ref)
            if not unjoinable(ident) and c['exposure']['company']['id'] == ident:bases.add('EXACT_ENTITY_ID'); via.append('exposure.company')
            if hashes & content_hashes(c, 'candidate'):bases.add('EXACT_DOCUMENT_HASH')
            for t in tags:
                if any(f'[REQ:{t}]' in v for v in c['missing_variables']):bases.add('AUTHOR_TAG_CANDIDATE'); via.append(f'[REQ:{t}]')
            if bases:
                status = next((d['decision'] for d in reversed(s.dispositions) if d['candidate_id'] == rid), 'NO_DISPOSITION')
                result['claims'][f'{cid}/{rid}'] = {'bases': sorted(bases), 'via': sorted(set(via)), 'status': status}
    if catalogue:
        for inv in catalogue['investigations']:
            bases = set()
            if not unjoinable(ident) and any(e['id'] == ident for e in inv['entities']):bases.add('EXACT_ENTITY_ID')
            if hashes & {d['sha256'] for d in inv['documents']}:bases.add('EXACT_DOCUMENT_HASH')
            if tags & {f['requirement'] for f in inv['findings'] if f['requirement']}:bases.add('AUTHOR_TAG_CANDIDATE')
            if bases:result['catalogue'][inv['id']] = {'bases': sorted(bases), 'verdict': inv['verdict']['text']}
    return result


def naive_text_search(ledgers, campaign, oid):
    """Reference lower bound only: identifier, tag and keyword substrings in other ledgers' candidate records."""
    import json
    events = {Path(p).name: [json.loads(line) for line in Path(p).read_bytes().splitlines()] for p in ledgers}
    own = next(n for n, ev in events.items() if ev[0]['record']['id'] == campaign)
    o = next(e['record'] for e in reversed(events[own]) if e['type'] == 'observation' and e['record']['id'] == oid)
    terms = {o['entity']['id']} | {ev['sha256'] for ev in o['evidence'] if ev['sha256']}
    terms |= {v for _, v in M.TAG.findall(' '.join([o['statement'], o['why_informative']]))}
    words = M.keywords(o['statement'])
    claims = {}
    for name, evs in events.items():
        if name == own:continue
        cid = evs[0]['record']['id']
        for e in evs:
            if e['type'] != 'candidate':continue
            text = json.dumps(e['record'], ensure_ascii=False)
            hit = sorted({t for t in terms if t in text} | {w for w in words if w in text.lower()})
            if hit:claims.setdefault(f"{cid}/{e['record']['id']}", set()).update(hit)
    return {k: sorted(v) for k, v in claims.items()}
