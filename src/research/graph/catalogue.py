"""Validation of the non-authoritative historical-memory catalogue.

The catalogue cites historical reports verbatim, records their original verdicts and maps recorded
gaps to a small requirement vocabulary. It asserts no new economic fact. Structural corruption
refuses the build; a changed or missing cited report is flagged so stale memory is never shown as
current.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOGUE_PATH = ROOT / 'docs/strategy/graph/research_memory_catalogue.json'
VERSION = 'GRAPH_MEMORY_CATALOGUE_V001'
STATUS_CLASSES = ('STOPPED', 'HOLD', 'REJECTED', 'NOT_ADVANCED')
FINDING_KINDS = ('MEASUREMENT_GAP', 'SOURCE_FIELD_PRESENT', 'SOURCE_OMISSION', 'ACCESS_BLOCKED', 'ACCESS_NOTE', 'RETROSPECTIVE_ONLY',
                 'IDENTITY_LIMIT', 'SCOPE_LIMIT', 'INFORMATION_LIMIT', 'RESTRICTED_M_PASS', 'EVIDENCE_TO_CHANGE')
IDENTITY_BASES = ('SEC_ARCHIVE_PATH_IN_RECORDED_LOCATOR', 'RECORDED_IDENTIFIER', 'NAME_ONLY')
FINANCIAL_BASES = ('GROSS', 'NET', 'RETAINED_NET', 'NOT_ESTABLISHED')


class CatalogueError(ValueError):
    """The catalogue is structurally corrupted; the graph refuses to build from it."""


def need(cond, message):
    if not cond:raise CatalogueError(message)


def safe_path(path):
    p = str(path)
    need(p.startswith('docs/') and '..' not in p and not p.startswith('docs/../'), f'citation path must be a tracked docs/ path: {p}')
    return p


def load(path=CATALOGUE_PATH, root=ROOT):
    """Return (catalogue, issues). Raises CatalogueError on structural corruption."""
    try:cat = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:raise CatalogueError(f'unreadable catalogue: {error}') from error
    need(isinstance(cat, dict) and cat.get('version') == VERSION, 'unknown catalogue version')
    need(cat.get('status') == 'NON_AUTHORITATIVE_RESEARCH_MEMORY', 'catalogue must declare itself non-authoritative')
    for key in ('recorded_at_utc', 'report_hashes', 'requirements', 'blocker_requirements', 'claim_mappings', 'investigations'):
        need(key in cat, f'catalogue missing {key}')
    reqs = [r['id'] for r in cat['requirements']]
    need(len(reqs) == len(set(reqs)) and all(re.fullmatch(r'REQ_[A-Z0-9_]+', r) for r in reqs), 'invalid requirement vocabulary')
    for r in cat['requirements']:
        need(r.get('definition') and isinstance(r.get('does_not_mean'), list), f"requirement {r['id']} needs definition and does_not_mean")
    need(all(v in reqs for v in cat['blocker_requirements'].values()), 'blocker mapping to unknown requirement')
    for m in cat['claim_mappings']:
        need(set(m) == {'claim', 'requirement', 'basis', 'note'} and m['requirement'] in reqs, f'invalid claim mapping {m}')
    texts, issues, statuses = {}, [], {}
    for p, digest in cat['report_hashes'].items():
        safe_path(p); file = root / p
        if not file.is_file():
            issues.append({'code': 'MISSING_SOURCE_DOCUMENT', 'path': p}); continue
        data = file.read_bytes(); texts[p] = data.decode('utf-8')
        statuses[p] = 'CURRENT' if hashlib.sha256(data).hexdigest() == digest else 'HASH_CHANGED'

    def cite(c, where):
        need(isinstance(c, dict) and set(c) == {'path', 'quote'} and c['quote'], f'{where}: citation needs path and quote')
        p = safe_path(c['path']); need(p in cat['report_hashes'], f'{where}: cited path missing from report_hashes')
        if p not in texts:return 'MISSING'
        if c['quote'] not in texts[p]:
            issues.append({'code': 'STALE_CITATION', 'path': p, 'where': where}); return 'STALE'
        if statuses[p] == 'HASH_CHANGED':
            issues.append({'code': 'CITATION_HASH_CHANGED', 'path': p, 'where': where}); return 'HASH_CHANGED_QUOTE_PRESENT'
        return 'CURRENT'

    ids = set()
    for inv in cat['investigations']:
        iid = inv.get('id', '?'); need(re.fullmatch(r'HIST-[A-Z0-9]+', iid) and iid not in ids, f'invalid or duplicate investigation {iid}')
        ids.add(iid)
        for key in ('family', 'title', 'report', 'historical_closure', 'verdict', 'claims', 'findings', 'entities', 'documents', 'related'):
            need(key in inv, f'{iid}: missing {key}')
        need(safe_path(inv['report']) in cat['report_hashes'], f'{iid}: report not hashed')
        v = inv['verdict']; need(v.get('status_class') in STATUS_CLASSES and v.get('text'), f'{iid}: invalid verdict')
        states = [cite(v['citation'], f'{iid}.verdict'), cite(v['scope_citation'], f'{iid}.verdict.scope')]
        claims = {c['id'] for c in inv['claims']}
        need(len(claims) == len(inv['claims']), f'{iid}: duplicate claim id')
        for c in inv['claims']:
            need(c.get('financial_basis') in FINANCIAL_BASES and isinstance(c.get('counts_as_original'), bool), f'{iid}.{c.get("id")}: invalid claim')
            need(c['reformulates'] is None or c['reformulates'] in claims, f'{iid}.{c["id"]}: unknown reformulated claim')
            need(not (c['reformulates'] and c['counts_as_original']), f'{iid}.{c["id"]}: a reformulation cannot count as an original claim')
            states += [cite(s['citation'], f'{iid}.{c["id"]}.status') for s in c['recorded_status']]
        fids = set()
        for f in inv['findings']:
            need(f['id'] not in fids and f['kind'] in FINDING_KINDS, f'{iid}.{f["id"]}: invalid finding')
            need(f['requirement'] is None or f['requirement'] in reqs, f'{iid}.{f["id"]}: unknown requirement {f["requirement"]}')
            need(f['claim'] is None or f['claim'] in claims, f'{iid}.{f["id"]}: unknown claim'); fids.add(f['id'])
            states.append(cite(f['citation'], f'{iid}.{f["id"]}'))
        locators = {d['locator'] for d in inv['documents']}
        for e in inv['entities']:
            need(e.get('identity_basis') in IDENTITY_BASES and e.get('type') and e.get('name'), f'{iid}: invalid entity {e.get("id")}')
            if e['identity_basis'] == 'NAME_ONLY':need(e['id'].startswith('NAME:'), f'{iid}: name-only entity must use NAME:')
            else:need(not e['id'].startswith('NAME:'), f'{iid}: identified entity cannot use NAME:')
            if e['identity_basis'] == 'SEC_ARCHIVE_PATH_IN_RECORDED_LOCATOR':
                m = re.fullmatch(r'CIK:(\d{10})', e['id']); need(m and e.get('locator') in locators, f'{iid}: SEC identity needs a recorded document locator')
                need(f'/edgar/data/{int(m.group(1))}/' in e['locator'], f'{iid}: CIK does not match the recorded archive path')
            else:states.append(cite(e['citation'], f'{iid}.entity.{e["id"]}'))
        for d in inv['documents']:
            need(re.fullmatch(r'[0-9a-f]{64}', d.get('sha256', '')), f'{iid}: document needs a sha256')
            r = safe_path(d['receipt']); need(r in cat['report_hashes'], f'{iid}: receipt not hashed')
            if r in texts:
                need(d['sha256'] in texts[r] and d['locator'] in texts[r], f'{iid}: document hash/locator not found in its receipt')
        need(all(x in {i['id'] for i in cat['investigations']} for x in inv['related']), f'{iid}: unknown related investigation')
        statuses[iid] = ('MISSING' if 'MISSING' in states else 'STALE' if 'STALE' in states
                         else 'HASH_CHANGED_QUOTE_PRESENT' if 'HASH_CHANGED_QUOTE_PRESENT' in states else 'CURRENT')
    cat['_citation_status'] = {i['id']: statuses[i['id']] for i in cat['investigations']}
    return cat, issues


def requirement_ids(cat):
    return [r['id'] for r in cat['requirements']]
