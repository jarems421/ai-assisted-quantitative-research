"""Graph Pilot R4 AI-review variant (PROPOSED, not registered): two independent model reviews, two cross-reviews, reconciliation.

A separate, prospective path beside the human Phase B design. It never writes, reads as human, or substitutes for the
human logs (``adjudications-<R>.jsonl``, ``warning-usefulness-<R>.jsonl``) and their seals, and nothing here makes a
packet conform to the human dual-review rule. Every output is labelled as model output.

* **Package.** ``build_package`` turns a leak-scanned aliased export (``blind_v2.json``) and a content-addressed evidence
  folder (files named ``<sha256>``) into one neutral package: the items exactly as exported (arm fields were already
  hidden), copies of the cited evidence verified by hash, the three frozen reviewer texts and their hashes, a readable
  ``items.md`` and an answer template. Missing evidence is recorded as missing, never invented. The items and the frozen
  texts must pass the export leak scan; instruction-like text in items or evidence is flagged, never removed.
* **Stage A (primary).** Each model (slot A, slot B) answers the identical package. The operator stores the model's JSON
  answer verbatim under ``review`` with operator-recorded provenance (product, model identifier, mode, prompt hashes,
  run times, usage, resources, raw-output hash, the human who ran it). A validated answer is sealed by hash, once.
  Answers that fail validation are preserved as failed attempts; model output is never edited to pass.
* **Stage B (cross-review).** Only after both primary seals: each model audits both frozen answers against the evidence.
  An audit carries no labels of its own and is never counted as a review. It is sealed the same way.
* **Order.** In git, each answer must first appear strictly after the other slot's seal for that stage, and each
  cross-review strictly after both primary answers.
* **Stage C (reconciliation).** Deterministic: quotes are checked against the evidence files, and only character-exact
  quotes verify (normalised matches are reported separately); an outcome counts only where both answers agree; any
  difference is ``AI_UNRESOLVED_DISAGREEMENT``. Audits add findings and a robustness flag; they never change a label.
  Confidence is reported, never used. Scientific (conforming) counts are withheld unless the stage order is VERIFIED,
  both cross-reviews exist, the two model identities are known and distinct, nothing was consulted outside the package
  and no evidence is missing; diagnostic counts are always reported separately.
* **Adjudication, not discovery.** Reviewers and auditors judge the given items against the given evidence only. A
  browsing run, or one declaring outside sources, is never a conforming adjudication.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

from src.research.graph import adjudication as AD
from src.research.graph import pilot as P

ROOT = Path(__file__).resolve().parents[3]
TEXTS_DIR = ROOT / 'docs/strategy/graph_pilot_r4_ai_review'
TEXTS = {'checklist': 'review_checklist_v001.md', 'primary': 'stage_a_reviewer_prompt_v001.md', 'cross': 'stage_b_cross_review_prompt_v001.md'}
PACKAGE_V1, PRIMARY_V1, CROSS_V1 = 'GRAPH_AI_REVIEW_PACKAGE_V1', 'GRAPH_AI_PRIMARY_REVIEW_V1', 'GRAPH_AI_CROSS_REVIEW_V1'
ANSWER_V1, CROSS_ANSWER_V1 = 'GRAPH_AI_REVIEW_ANSWER_V1', 'GRAPH_AI_CROSS_ANSWER_V1'
SEAL_V1, RECONCILIATION_V1 = 'GRAPH_AI_REVIEW_SEAL_V1', 'GRAPH_AI_RECONCILIATION_V1'
SLOTS, STAGES = ('A', 'B'), ('primary', 'cross')
BANNER = 'AI-ADJUDICATED: model outputs, not human judgments. Not a conforming human dual review.'
SEAL_STATEMENT = 'This file is a model output recorded unchanged by the named operator. It is not a human judgment.'

OUTCOMES = ('CONFIRMED', 'FALSE', 'TRIVIAL', 'PLAUSIBLE_UNVERIFIED', 'UNKNOWN')
EVIDENCE_OUTCOMES = ('CONFIRMED', 'FALSE')
MEANING, USEFULNESS = P.MEANING, AD.USEFULNESS
CONFIDENCE, YES_NO = ('HIGH', 'MEDIUM', 'LOW'), ('YES', 'NO')
MODES = ('EVIDENCE_PACK_ONLY', 'BROWSING_ALLOWED')
SUPPORT_CHECKS = ('SUPPORTED', 'PARTLY_SUPPORTED', 'UNSUPPORTED', 'CANNOT_CHECK')
ISSUES = ('FACTUAL_ERROR', 'MISQUOTE', 'UNSUPPORTED_CONCLUSION', 'MISSED_EVIDENCE', 'INVENTED_CONTENT', 'METHOD_DIFFERENCE', 'OTHER')
SERIOUS_ISSUES = ('FACTUAL_ERROR', 'MISQUOTE', 'UNSUPPORTED_CONCLUSION', 'INVENTED_CONTENT')
NATURES = ('NO_DISAGREEMENT', 'GENUINE_EVIDENTIAL', 'METHODOLOGICAL', 'ONE_SIDE_UNSUPPORTED', 'BOTH_UNSUPPORTED', 'CANNOT_DETERMINE')

ITEM_KEYS = ('blind_id', 'kind', 'outcome', 'economic_meaning', 'usefulness', 'avoided_action', 'support', 'rationale',
             'missing_or_contradicting_evidence', 'confidence', 'uncertainty', 'sources_outside_package')
SUPPORT_KEYS = ('evidence_sha256', 'location', 'quote')
DECLARATION_KEYS = ('used_only_package_files', 'sources_outside_package', 'integrity_notes', 'general_limitations')
ANSWER_KEYS = ('template_version', 'reviewer_declaration', 'items')
CROSS_ITEM_KEYS = ('blind_id', 'review_A', 'review_B', 'disagreement_nature', 'missed_evidence', 'notes')
CROSS_SIDE_KEYS = ('support_check', 'issues')
MISSED_KEYS = ('evidence_sha256', 'location', 'quote', 'note')
AUDITOR_KEYS = ('used_only_package_files', 'sources_outside_package', 'integrity_notes')
CROSS_ANSWER_KEYS = ('template_version', 'auditor_declaration', 'items', 'systematic_differences', 'limitations')
PROVENANCE_KEYS = ('reviewer_kind', 'product', 'model_identifier', 'mode', 'prompt_sha256', 'run_started_utc', 'run_finished_utc',
                   'usage', 'resources', 'conversation_reference', 'raw_output_sha256', 'run_by')
DOC_KEYS = {'primary': ('version', 'slot', 'package_sha256', 'provenance', 'review'),
            'cross': ('version', 'slot', 'package_sha256', 'reviewed', 'provenance', 'review')}
INJECTION = re.compile(r'ignore (?:all |any )?(?:previous|prior|above) instructions|disregard (?:the|this) checklist|system prompt|'
                       r'you are (?:an? )?(?:ai|language model|assistant)|(?:mark|label|rate) (?:this|the) (?:item|connection) as|'
                       r'\b(?:reviewer|auditor)s?:\s', re.I)
FORMATS = ((b'%PDF', 'pdf'), (b'PK\x03\x04', 'zip'), (b'\x89PNG', 'png'), (b'\xff\xd8\xff', 'jpg'), (b'GIF8', 'gif'))


def fail(message):
    raise P.PilotError(message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sniff(data):
    """A file extension from content (never from a name): binary signatures, then JSON, HTML or plain text."""
    for magic, ext in FORMATS:
        if data.startswith(magic):return ext
    head = data[:2048].lstrip().lower()
    try:data.decode('utf-8')
    except UnicodeDecodeError:return 'bin'
    if head[:1] in (b'{', b'['):
        try:json.loads(data.decode('utf-8')); return 'json'
        except ValueError:pass
    return 'html' if head.startswith((b'<!doctype html', b'<html')) or b'<body' in head else 'txt'


def normalise(text):
    return ' '.join(html.unescape(text).replace(' ', ' ').split()).casefold()


def evidence_text(path):
    """Searchable text of an evidence file, or None when its format cannot be checked mechanically (PDF, archives, images)."""
    data = Path(path).read_bytes(); kind = sniff(data)
    if kind not in ('json', 'html', 'txt'):return None
    text = data.decode('utf-8')
    if kind == 'html':text = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', text); text = re.sub(r'(?s)<[^>]+>', ' ', text)
    return text


def item_evidence(item):
    return sorted({e['sha256'] for end in ('from', 'to') for e in item[end]['evidence'] if e.get('sha256')})


def frozen_texts(texts_dir=TEXTS_DIR):
    d = Path(texts_dir); out = {}
    for role, name in TEXTS.items():
        f = d / name
        if not f.is_file():fail(f'frozen reviewer text missing: {f}')
        out[role] = {'name': name, 'sha256': P.sha256(f), 'text': f.read_text(encoding='utf-8')}
    return out


def template_item(item):
    connection = item['kind'] in AD.ECONOMIC_KINDS
    return {'blind_id': item['blind_id'], 'kind': item['kind'],
            'outcome': '<one of ' + ' | '.join(OUTCOMES) + '>' if connection else None,
            'economic_meaning': '<one of ' + ' | '.join(MEANING) + '>' if connection else None,
            'usefulness': None if connection else '<one of ' + ' | '.join(USEFULNESS) + '>',
            'avoided_action': None, 'support': [{'evidence_sha256': '<a sha256 cited by this item>', 'location': '', 'quote': ''}],
            'rationale': '', 'missing_or_contradicting_evidence': '', 'confidence': '<HIGH | MEDIUM | LOW>', 'uncertainty': '',
            'sources_outside_package': []}


def answer_template(items):
    return {'template_version': ANSWER_V1,
            'reviewer_declaration': {'used_only_package_files': '<YES | NO>', 'sources_outside_package': [], 'integrity_notes': '',
                                     'general_limitations': ''},
            'items': [template_item(i) for i in items]}


def cross_template(items):
    side = {'support_check': '<one of ' + ' | '.join(SUPPORT_CHECKS) + '>', 'issues': []}
    return {'template_version': CROSS_ANSWER_V1,
            'auditor_declaration': {'used_only_package_files': '<YES | NO>', 'sources_outside_package': [], 'integrity_notes': ''},
            'items': [{'blind_id': i['blind_id'], 'review_A': dict(side), 'review_B': dict(side),
                       'disagreement_nature': '<one of ' + ' | '.join(NATURES) + '>', 'missed_evidence': [], 'notes': ''} for i in items],
            'systematic_differences': '', 'limitations': ''}


def render_items(package):
    L = ['# Review items', '', f"{len(package['items'])} items. Evidence files are in `evidence/`; each is named by its sha256.", '']
    for n, i in enumerate(package['items'], 1):
        L += [f"## {n}. `{i['blind_id']}` ({i['kind']})", '']
        if i.get('avoided_action'):L += [f"Stated avoided action: {i['avoided_action']}", '']
        for end in ('from', 'to'):
            e = i[end]; L.append(f"**{end}** ({e['kind']}, {e['campaign']}, record `{e['record']}`): {e.get('text', '')}")
            for k in ('value', 'units', 'occurred', 'type', 'period', 'basis', 'status', 'depth'):
                if e.get(k) not in (None, '', []):L.append(f'- {k}: {e[k]}')
            if e.get('entities'):L.append('- entities: ' + '; '.join(f"{x.get('id')} ({x.get('name')})" for x in e['entities']))
            if e.get('tags'):L.append('- tags: ' + ', '.join(e['tags']))
            for x in e['evidence']:
                f = package['evidence'].get(x['sha256'], {}).get('file', 'MISSING_FROM_PACKAGE')
                L.append(f"- evidence: `{f}` (locator {x['locator']}, depth {x.get('depth')})")
            L.append('')
        L += ['Shared structure: ' + json.dumps(i['shared_structure'], ensure_ascii=False, sort_keys=True), '']
    return '\n'.join(L) + '\n'


def build_package(export_path, evidence_dir, out_dir, own_from=None, texts_dir=TEXTS_DIR):
    """The neutral review package. Refuses an unscanned export, any leak in items or frozen texts, or a hash mismatch."""
    export = json.loads(Path(export_path).read_text(encoding='utf-8'))
    if export.get('version') != P.ALIAS_VERSION or export.get('leak_scan', {}).get('findings') != 0:
        fail('the package is built only from a leak-scanned aliased export (blind_v2.json)')
    own = P.own_records(json.loads(Path(own_from).read_text(encoding='utf-8'))) if own_from else ()
    items = [{k: i[k] for k in ('blind_id', 'kind', 'from', 'to', 'shared_structure', 'avoided_action') if k in i} for i in export['items']]
    texts = frozen_texts(texts_dir)
    leaks = P.scan_leaks(items, own) + [x for t in texts.values() for x in P.scan_leaks(t['text'])]
    if leaks:fail(f'the package would leak arm-identifying text: {leaks[:5]}')
    out = Path(out_dir)
    if out.exists():fail(f'{out} exists; a package is built once')
    evidence, flags, blobs = {}, [], {}
    for h in sorted({h for i in items for h in item_evidence(i)}):
        src = Path(evidence_dir) / h
        if not src.is_file():evidence[h] = {'file': 'MISSING_FROM_PACKAGE', 'bytes': None, 'format': None, 'machine_checkable': False}; continue
        data = src.read_bytes()
        if sha256_bytes(data) != h:fail(f'evidence file {h} does not match its hash')
        ext = sniff(data); name = f'evidence/{h}.{ext}'; blobs[name] = data
        text = evidence_text(src) if ext in ('json', 'html', 'txt') else None
        evidence[h] = {'file': name, 'bytes': len(data), 'format': ext, 'machine_checkable': text is not None}
        if text is not None and INJECTION.search(text):flags.append({'where': name, 'flag': 'INSTRUCTION_LIKE_TEXT_IN_EVIDENCE'})
    for i in items:
        if INJECTION.search(json.dumps(i, ensure_ascii=False)):flags.append({'where': i['blind_id'], 'flag': 'INSTRUCTION_LIKE_TEXT_IN_ITEM'})
    package = {'version': PACKAGE_V1, 'packet': export['packet'], 'fixture': export.get('fixture'),
               'export': {'name': Path(export_path).name, 'sha256': P.sha256(export_path)},
               'texts': {role: {'file': f"texts/{t['name']}", 'sha256': t['sha256']} for role, t in texts.items()},
               'items': items, 'evidence': evidence, 'integrity_flags': flags}
    rendered = render_items(package)
    if P.scan_leaks(rendered, own):fail('the rendered items would leak arm-identifying text')
    (out / 'evidence').mkdir(parents=True); (out / 'texts').mkdir()
    for name, data in blobs.items():(out / name).write_bytes(data)
    for role, t in texts.items():(out / 'texts' / t['name']).write_text(t['text'], encoding='utf-8', newline='\n')
    P.write_new(out / 'package.json', package)
    (out / 'items.md').write_text(rendered, encoding='utf-8', newline='\n')
    P.write_new(out / 'response_template.json', answer_template(items))
    P.write_new(out / 'cross_review_template.json', cross_template(items))
    return package


def load_package(package_dir):
    d = Path(package_dir); pkg = json.loads((d / 'package.json').read_text(encoding='utf-8'))
    if pkg.get('version') != PACKAGE_V1:fail('not a GRAPH_AI_REVIEW_PACKAGE_V1 package')
    for role, t in pkg['texts'].items():
        if P.sha256(d / t['file']) != t['sha256']:fail(f'frozen {role} text in the package changed')
    for h, e in pkg['evidence'].items():
        if e['file'] != 'MISSING_FROM_PACKAGE' and P.sha256(d / e['file']) != h:fail(f'evidence {h} in the package changed')
    return pkg, P.sha256(d / 'package.json')


def check_support(s, allowed, pkg, d, where):
    """One support entry, checked against its evidence file; refuses an entry citing evidence the item does not cite.

    ``EXACT``: the quote occurs character for character in the file's text (HTML: tags removed, entities decoded, whitespace
    untouched), as the checklist requires. ``NORMALISED_ONLY``: it occurs only after collapsing whitespace and case, which is
    reported but never counts as exact verification. ``LOCATION_RESOLVES``: no quote, and a JSON-pointer location exists
    (not a check of what it says). ``NOT_FOUND``: checkable but absent. ``UNVERIFIABLE``: missing file or a format that
    cannot be checked mechanically."""
    if not isinstance(s, dict) or tuple(sorted(s)) != tuple(sorted(SUPPORT_KEYS)):fail(f'{where}: support entries have exactly {SUPPORT_KEYS}')
    if s['evidence_sha256'] not in allowed:fail(f'{where}: support cites {s["evidence_sha256"]!r}, which this item does not cite')
    if not isinstance(s['quote'], str) or not isinstance(s['location'], str):fail(f'{where}: quote and location are text')
    if not s['quote'].strip() and not s['location'].strip():fail(f'{where}: a support entry gives an exact quote or an exact location')
    e = pkg['evidence'].get(s['evidence_sha256'])
    if not e or e['file'] == 'MISSING_FROM_PACKAGE':return 'UNVERIFIABLE'
    if s['quote'].strip():
        text = evidence_text(Path(d) / e['file'])
        if text is None:return 'UNVERIFIABLE'
        if s['quote'] in (html.unescape(text) if e['format'] == 'html' else text):return 'EXACT'
        return 'NORMALISED_ONLY' if normalise(s['quote']) in normalise(text) else 'NOT_FOUND'
    if s['location'].startswith('/') and e['format'] == 'json':
        try:resolve_pointer(json.loads((Path(d) / e['file']).read_text(encoding='utf-8')), s['location']); return 'LOCATION_RESOLVES'
        except (KeyError, IndexError, ValueError):return 'NOT_FOUND'
    return 'UNVERIFIABLE'


def resolve_pointer(doc, pointer):
    for part in pointer.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        doc = doc[int(part)] if isinstance(doc, list) else doc[part]
    return doc


def verification(statuses):
    """VERIFIED_EXACT only when every quote is character-exact; NORMALISED_ONLY and NOT_MACHINE_VERIFIED never count as verified."""
    if not statuses:return 'NO_SUPPORT'
    if 'NOT_FOUND' in statuses:return 'NOT_FOUND'
    if all(s == 'EXACT' for s in statuses):return 'VERIFIED_EXACT'
    return 'NORMALISED_ONLY' if all(s in ('EXACT', 'NORMALISED_ONLY') for s in statuses) else 'NOT_MACHINE_VERIFIED'


def evidence_suffix(v):
    """The label suffix for an agreed evidence-bearing label whose quotes are not both character-exact."""
    if 'NOT_FOUND' in v:return '_QUOTE_NOT_FOUND'
    if v == ('VERIFIED_EXACT', 'VERIFIED_EXACT'):return ''
    return '_NORMALISED_MATCH_ONLY' if set(v) <= {'VERIFIED_EXACT', 'NORMALISED_ONLY'} else '_NOT_MACHINE_VERIFIED'


def check_provenance(p, stage, pkg_texts, where):
    if not isinstance(p, dict) or tuple(sorted(p)) != tuple(sorted(PROVENANCE_KEYS)):fail(f'{where}: provenance has exactly {PROVENANCE_KEYS}')
    if p['reviewer_kind'] != 'AI_MODEL':fail(f'{where}: reviewer_kind is AI_MODEL; this path never records human judgments')
    if p['mode'] not in MODES:fail(f'{where}: mode is one of {MODES}')
    for k in ('product', 'model_identifier', 'run_by'):
        if not isinstance(p[k], str) or not p[k].strip():fail(f'{where}: provenance.{k} is required (UNKNOWN where truly unknown)')
    if P.ASSISTANT_NAME.search(p['run_by']):fail(f'{where}: run_by is the human who ran the model and stored its answer, not an assistant')
    want = {r: pkg_texts[r]['sha256'] for r in ('checklist', stage)}
    if p['prompt_sha256'] != want:fail(f'{where}: prompt_sha256 must equal the frozen texts in the package {want}')
    if not re.fullmatch(r'[0-9a-f]{64}', str(p['raw_output_sha256'])):fail(f'{where}: raw_output_sha256 is the sha256 of the saved raw model output')
    start, end = P.parse_time(p['run_started_utc']), P.parse_time(p['run_finished_utc'])
    if end < start:fail(f'{where}: the run finished before it started')
    for k in ('usage', 'resources', 'conversation_reference'):
        if not (isinstance(p[k], (str, dict)) and p[k]):fail(f'{where}: provenance.{k} is recorded, or "UNKNOWN"')


def check_text(v, where, field):
    if not isinstance(v, str):fail(f'{where}: {field} is text (may be empty)')


def check_sources(v, where):
    if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):fail(f'{where}: sources_outside_package is a list of sources')


def validate_primary(package_dir, path):
    """One primary answer: every item once, checklist labels only, support from the item's own evidence; quotes checked."""
    d = Path(package_dir); pkg, pkg_sha = load_package(d); w = Path(path).name
    doc = json.loads(Path(path).read_text(encoding='utf-8'))
    if tuple(sorted(doc)) != tuple(sorted(DOC_KEYS['primary'])) or doc['version'] != PRIMARY_V1:fail(f'{w}: a {PRIMARY_V1} document has exactly {DOC_KEYS["primary"]}')
    if doc['slot'] not in SLOTS or doc['package_sha256'] != pkg_sha:fail(f'{w}: slot A or B, answering this exact package')
    check_provenance(doc['provenance'], 'primary', pkg['texts'], w)
    ans = doc['review']
    if not isinstance(ans, dict) or tuple(sorted(ans)) != tuple(sorted(ANSWER_KEYS)) or ans['template_version'] != ANSWER_V1:
        fail(f'{w}: review is the model answer in the template ({ANSWER_KEYS})')
    dec = ans['reviewer_declaration']
    if not isinstance(dec, dict) or tuple(sorted(dec)) != tuple(sorted(DECLARATION_KEYS)) or dec['used_only_package_files'] not in YES_NO:
        fail(f'{w}: reviewer_declaration has exactly {DECLARATION_KEYS}')
    check_sources(dec['sources_outside_package'], w); check_text(dec['integrity_notes'], w, 'integrity_notes'); check_text(dec['general_limitations'], w, 'general_limitations')
    items = {i['blind_id']: i for i in pkg['items']}; out = {}
    for n, r in enumerate(ans['items'], 1):
        iw = f'{w} item {n}'
        if not isinstance(r, dict) or tuple(sorted(r)) != tuple(sorted(ITEM_KEYS)):fail(f'{iw}: fields must be exactly {ITEM_KEYS}')
        if r['blind_id'] not in items or r['blind_id'] in out:fail(f'{iw}: {r["blind_id"]!r} is not an unanswered package item')
        item = items[r['blind_id']]
        if r['kind'] != item['kind']:fail(f'{iw}: kind must stay {item["kind"]}')
        if item['kind'] in AD.ECONOMIC_KINDS:
            if r['outcome'] not in OUTCOMES or r['economic_meaning'] not in MEANING:fail(f'{iw}: outcome is one of {OUTCOMES}; economic_meaning one of {MEANING}')
            if r['usefulness'] is not None or r['avoided_action'] is not None:fail(f'{iw}: a CONNECTION item has no usefulness or avoided_action')
        else:
            if r['outcome'] is not None or r['economic_meaning'] is not None:fail(f'{iw}: a warning or avoided repeat is never an economic outcome')
            if r['usefulness'] not in USEFULNESS:fail(f'{iw}: usefulness is one of {USEFULNESS}')
            if r['avoided_action'] is not None and not isinstance(r['avoided_action'], str):fail(f'{iw}: avoided_action is text or null')
        if r['confidence'] not in CONFIDENCE:fail(f'{iw}: confidence is one of {CONFIDENCE}')
        for k in ('rationale', 'missing_or_contradicting_evidence', 'uncertainty'):check_text(r[k], iw, k)
        check_sources(r['sources_outside_package'], iw)
        if not isinstance(r['support'], list):fail(f'{iw}: support is a list')
        statuses = [check_support(s, set(item_evidence(item)), pkg, d, iw) for s in r['support']]
        label = r['outcome'] or r['usefulness']
        if label in EVIDENCE_OUTCOMES + ('USEFUL_LESSON_REUSED',) and not statuses:fail(f'{iw}: {label} needs at least one support entry')
        if label == 'USEFUL_LESSON_REUSED' and not (r['avoided_action'] or '').strip():fail(f'{iw}: USEFUL_LESSON_REUSED states the avoided action')
        if label in ('UNKNOWN', 'PLAUSIBLE_UNVERIFIED', 'CANNOT_ASSESS') and not r['missing_or_contradicting_evidence'].strip():
            fail(f'{iw}: {label} says what is missing or prevented assessment')
        if label in ('TRIVIAL', 'NOT_USEFUL') and not r['rationale'].strip():fail(f'{iw}: {label} explains why in rationale')
        out[r['blind_id']] = {**r, 'support_status': statuses, 'verification': verification(statuses)}
    if set(out) != set(items):fail(f'{w}: {len(set(items) - set(out))} package items are not answered')
    external = doc['provenance']['mode'] == 'BROWSING_ALLOWED' or dec['used_only_package_files'] == 'NO' or bool(dec['sources_outside_package']) \
        or any(r['sources_outside_package'] for r in out.values())
    return {'slot': doc['slot'], 'provenance': doc['provenance'], 'declaration': dec, 'items': out, 'external_access': external}


def files(package_dir, stage, slot):
    d = Path(package_dir); stem = 'ai-review' if stage == 'primary' else 'ai-cross-review'
    return {'answer': d / f'{stem}-{slot}.json', 'seal': d / f'{stem}-seal-{slot}.json'}


def validate_cross(package_dir, path, primaries=None):
    """One cross-review: both frozen answers, every item once, no labels of its own, missed evidence quoted from the item."""
    d = Path(package_dir); pkg, pkg_sha = load_package(d); w = Path(path).name
    primaries = primaries or {s: validate_primary(d, files(d, 'primary', s)['answer']) for s in SLOTS}
    doc = json.loads(Path(path).read_text(encoding='utf-8'))
    if tuple(sorted(doc)) != tuple(sorted(DOC_KEYS['cross'])) or doc['version'] != CROSS_V1:fail(f'{w}: a {CROSS_V1} document has exactly {DOC_KEYS["cross"]}')
    if doc['slot'] not in SLOTS or doc['package_sha256'] != pkg_sha:fail(f'{w}: slot A or B, auditing this exact package')
    want = {s: P.sha256(files(d, 'primary', s)['answer']) for s in SLOTS}
    if doc['reviewed'] != want:fail(f'{w}: reviewed must name the two sealed primary answers {want}')
    check_provenance(doc['provenance'], 'cross', pkg['texts'], w)
    ans = doc['review']
    if not isinstance(ans, dict) or tuple(sorted(ans)) != tuple(sorted(CROSS_ANSWER_KEYS)) or ans['template_version'] != CROSS_ANSWER_V1:
        fail(f'{w}: review is the audit in the template ({CROSS_ANSWER_KEYS})')
    dec = ans['auditor_declaration']
    if not isinstance(dec, dict) or tuple(sorted(dec)) != tuple(sorted(AUDITOR_KEYS)) or dec['used_only_package_files'] not in YES_NO:
        fail(f'{w}: auditor_declaration has exactly {AUDITOR_KEYS}')
    check_sources(dec['sources_outside_package'], w); check_text(dec['integrity_notes'], w, 'integrity_notes')
    for k in ('systematic_differences', 'limitations'):check_text(ans[k], w, k)
    items = {i['blind_id']: i for i in pkg['items']}; out = {}
    for n, r in enumerate(ans['items'], 1):
        iw = f'{w} item {n}'
        if not isinstance(r, dict) or tuple(sorted(r)) != tuple(sorted(CROSS_ITEM_KEYS)):fail(f'{iw}: fields must be exactly {CROSS_ITEM_KEYS} (an audit never relabels)')
        if r['blind_id'] not in items or r['blind_id'] in out:fail(f'{iw}: {r["blind_id"]!r} is not an unaudited package item')
        for side in ('review_A', 'review_B'):
            v = r[side]
            if not isinstance(v, dict) or tuple(sorted(v)) != tuple(sorted(CROSS_SIDE_KEYS)) or v['support_check'] not in SUPPORT_CHECKS:
                fail(f'{iw}: {side} has exactly {CROSS_SIDE_KEYS}, support_check one of {SUPPORT_CHECKS}')
            if not isinstance(v['issues'], list) or any(not isinstance(x, dict) or tuple(sorted(x)) != ('description', 'type') or x['type'] not in ISSUES
                                                        or not isinstance(x['description'], str) for x in v['issues']):
                fail(f'{iw}: {side}.issues are {{type, description}} with type one of {ISSUES}')
        same = labels(primaries['A']['items'][r['blind_id']]) == labels(primaries['B']['items'][r['blind_id']])
        if r['disagreement_nature'] not in NATURES or (r['disagreement_nature'] == 'NO_DISAGREEMENT') != same:
            fail(f'{iw}: disagreement_nature is NO_DISAGREEMENT exactly when both answers give the same labels')
        if not isinstance(r['missed_evidence'], list):fail(f'{iw}: missed_evidence is a list')
        statuses = []
        for m in r['missed_evidence']:
            if not isinstance(m, dict) or tuple(sorted(m)) != tuple(sorted(MISSED_KEYS)):fail(f'{iw}: missed_evidence entries have exactly {MISSED_KEYS}')
            statuses.append(check_support({k: m[k] for k in SUPPORT_KEYS}, set(item_evidence(items[r['blind_id']])), pkg, d, iw))
        check_text(r['notes'], iw, 'notes')
        out[r['blind_id']] = {**r, 'missed_evidence_status': statuses}
    if set(out) != set(items):fail(f'{w}: {len(set(items) - set(out))} package items are not audited')
    external = doc['provenance']['mode'] == 'BROWSING_ALLOWED' or dec['used_only_package_files'] == 'NO' or bool(dec['sources_outside_package'])
    return {'slot': doc['slot'], 'provenance': doc['provenance'], 'declaration': dec, 'items': out, 'external_access': external,
            'systematic_differences': ans['systematic_differences'], 'limitations': ans['limitations']}


def labels(r):
    return (r['outcome'], r['economic_meaning'], r['usefulness'])


def seal(package_dir, stage, slot, by, now=None):
    """The operator's once-only seal over a validated answer. Cross seals need both primary seals first."""
    if stage not in STAGES or slot not in SLOTS:fail(f'stage is one of {STAGES}; slot one of {SLOTS}')
    if not isinstance(by, str) or not by.strip() or P.ASSISTANT_NAME.search(by):fail('the seal is recorded by the human operator who stored the answer')
    d = Path(package_dir); f = files(d, stage, slot)
    if stage == 'cross':
        for s in SLOTS:load_seal(d, 'primary', s)
        v = validate_cross(d, f['answer'])
    else:v = validate_primary(d, f['answer'])
    if v['slot'] != slot:fail(f'{f["answer"].name} answers slot {v["slot"]}, not {slot}')
    if v['provenance']['run_by'].strip() != by.strip():fail('the seal is recorded by the operator named in the provenance')
    _, pkg_sha = load_package(d)
    doc = {'version': SEAL_V1, 'stage': stage, 'slot': slot, 'package_sha256': pkg_sha, 'answer': {'path': f['answer'].name, 'sha256': P.sha256(f['answer'])},
           'product': v['provenance']['product'], 'model_identifier': v['provenance']['model_identifier'], 'mode': v['provenance']['mode'],
           'recorded_by': by, 'sealed_at_utc': P.utc(now).isoformat(), 'statement': SEAL_STATEMENT}
    if P.parse_time(doc['sealed_at_utc']) < P.parse_time(v['provenance']['run_finished_utc']):fail('a seal cannot precede the end of the run it seals')
    try:P.write_new(f['seal'], doc)
    except FileExistsError as error:raise P.PilotError(f'{stage} answer {slot} is already sealed; a seal is immutable') from error
    return doc


def load_seal(package_dir, stage, slot):
    d = Path(package_dir); f = files(d, stage, slot)
    if not f['seal'].is_file():fail(f'{f["seal"].name} is missing: stage {stage} slot {slot} is not sealed')
    s = json.loads(f['seal'].read_text(encoding='utf-8'))
    if s.get('version') != SEAL_V1 or s.get('stage') != stage or s.get('slot') != slot or s.get('statement') != SEAL_STATEMENT:fail(f'{f["seal"].name}: not a {SEAL_V1} seal')
    if s['package_sha256'] != load_package(d)[1]:fail(f'{f["seal"].name}: sealed against a different package')
    if not f['answer'].is_file() or P.sha256(f['answer']) != s['answer']['sha256']:fail(f'{f["seal"].name}: the sealed answer changed or is missing')
    return s


def write_cross_inputs(package_dir, out_dir):
    """After both primary seals: the two frozen answers as auditors receive them (model answers only; provenance withheld)."""
    d = Path(package_dir); out = Path(out_dir); out.mkdir(parents=True, exist_ok=False)
    for s in SLOTS:
        load_seal(d, 'primary', s)
        answer = json.loads(files(d, 'primary', s)['answer'].read_text(encoding='utf-8'))['review']
        P.write_new(out / f'review_{s}.json', answer)
    return sorted(p.name for p in out.iterdir())


def stage_order(package_dir):
    """VERIFIED when each answer first appears strictly after the other slot's seal for its stage, and each cross-review
    strictly after both primary answers; otherwise NOT_COMMITTED or VIOLATED (with the reason)."""
    d = Path(package_dir).resolve(); top = AD.git(d, 'rev-parse', '--show-toplevel')
    if top.returncode != 0:return {'status': 'NOT_COMMITTED', 'detail': 'package is not in a git repository'}
    root = Path(top.stdout.strip()); first = {}
    for stage in STAGES:
        for s in SLOTS:
            for k, p in files(d, stage, s).items():
                if not p.is_file():return {'status': 'NOT_COMMITTED', 'detail': f'{p.name} is missing'}
                c, state = AD.content_first_commit(root, p.resolve().relative_to(root).as_posix(), p)
                if state != 'OK':return {'status': 'VIOLATED' if state == 'CHANGED' else 'NOT_COMMITTED', 'detail': f'{p.name}: {state}'}
                first[(stage, s, k)] = c
    after = lambda earlier, later: earlier != later and AD.git(root, 'merge-base', '--is-ancestor', earlier, later).returncode == 0
    for stage in STAGES:
        for s, other in (('A', 'B'), ('B', 'A')):
            if not after(first[(stage, other, 'seal')], first[(stage, s, 'answer')]):
                return {'status': 'VIOLATED', 'detail': f'{stage} answer {s} was not committed strictly after the {other} seal'}
    for s in SLOTS:
        for p in SLOTS:
            if not after(first[('primary', p, 'answer')], first[('cross', s, 'answer')]):
                return {'status': 'VIOLATED', 'detail': f'cross-review {s} was not committed strictly after primary answer {p}'}
    return {'status': 'VERIFIED', 'detail': 'answers revealed only after both seals; cross-reviews only after both primary answers'}


def economic_label(a, b):
    if a['outcome'] != b['outcome']:return 'AI_UNRESOLVED_DISAGREEMENT'
    o = a['outcome']; v = (a['verification'], b['verification'])
    if 'NOT_FOUND' in v:return f'AI_AGREED_{o}_QUOTE_NOT_FOUND'
    return f'AI_AGREED_{o}' + (evidence_suffix(v) if o in EVIDENCE_OUTCOMES else '')


def usefulness_label(a, b):
    if a['usefulness'] != b['usefulness']:return 'AI_UNRESOLVED_DISAGREEMENT'
    u = a['usefulness']; v = (a['verification'], b['verification'])
    if 'NOT_FOUND' in v:return f'AI_AGREED_{u}_QUOTE_NOT_FOUND'
    return f'AI_AGREED_{u}' + (evidence_suffix(v) if u == 'USEFUL_LESSON_REUSED' else '')


def nonconformance(order, cross, prim, pkg, distinct):
    """Every reason the package result is not a conforming AI-adjudicated result; empty only when all conditions hold."""
    reasons = [] if order['status'] == 'VERIFIED' else [f"STAGE_ORDER_{order['status']}"]
    for s in SLOTS:
        if s not in cross:reasons.append(f'CROSS_REVIEW_{s}_UNAVAILABLE')
        if prim[s]['provenance']['model_identifier'].strip().upper() in ('', 'UNKNOWN'):reasons.append(f'MODEL_IDENTITY_UNKNOWN_{s}')
        if prim[s]['external_access']:reasons.append(f'EXTERNAL_ACCESS_PRIMARY_{s}')
        if s in cross and cross[s]['external_access']:reasons.append(f'EXTERNAL_ACCESS_CROSS_{s}')
    if not distinct:reasons.append('MODEL_IDENTITY_NOT_DISTINCT')
    if any(e['file'] == 'MISSING_FROM_PACKAGE' for e in pkg['evidence'].values()):reasons.append('EVIDENCE_MISSING_FROM_PACKAGE')
    return reasons


def reconcile(package_dir):
    """Stage C: deterministic item-level reconciliation of two sealed answers, with sealed cross-review findings attached.

    Item labels and ``diagnostic_counts`` are always reported. ``conforming_counts`` (the only counts that may enter any
    scientific comparison) and item ``robust`` require a conforming package: verified stage order, both cross-reviews,
    two known and distinct model identities, no access outside the package and no missing evidence. Otherwise they are
    withheld, with every reason listed."""
    d = Path(package_dir); pkg, pkg_sha = load_package(d)
    seals = {s: load_seal(d, 'primary', s) for s in SLOTS}
    prim = {s: validate_primary(d, files(d, 'primary', s)['answer']) for s in SLOTS}
    cross, notes = {}, []
    for s in SLOTS:
        try:load_seal(d, 'cross', s); cross[s] = validate_cross(d, files(d, 'cross', s)['answer'], prim)
        except P.PilotError as error:notes.append(f'cross-review {s} unavailable: {error}')
    distinct = prim['A']['provenance']['model_identifier'].strip().casefold() != prim['B']['provenance']['model_identifier'].strip().casefold()
    if not distinct:notes.append('Both primary answers name the same model identifier: they are not independent reviews.')
    for s in SLOTS:
        if prim[s]['external_access']:notes.append(f'Primary {s} had or declared access outside the package: its answers are potentially unblinded (the repository is public).')
    order = stage_order(d); reasons = nonconformance(order, cross, prim, pkg, distinct); conforming = not reasons
    rows = []
    for i in pkg['items']:
        b = i['blind_id']; a_, b_ = prim['A']['items'][b], prim['B']['items'][b]
        economic = i['kind'] in AD.ECONOMIC_KINDS
        label = economic_label(a_, b_) if economic else usefulness_label(a_, b_)
        meaning = (f"AI_AGREED_{a_['economic_meaning']}" if a_['economic_meaning'] == b_['economic_meaning'] else 'AI_UNRESOLVED_DISAGREEMENT') if economic else None
        findings = {}
        for auditor, c in cross.items():
            r = c['items'][b]
            findings[auditor] = {side: {'support_check': r[f'review_{side}']['support_check'], 'issues': sorted({x['type'] for x in r[f'review_{side}']['issues']}),
                                        'self_audit': side == auditor} for side in SLOTS}
            findings[auditor]['disagreement_nature'] = r['disagreement_nature']
            findings[auditor]['missed_evidence_exact'] = r['missed_evidence_status'].count('EXACT')
            findings[auditor]['missed_evidence_normalised_only'] = r['missed_evidence_status'].count('NORMALISED_ONLY')
        contested = any(set(findings[a][side]['issues']) & set(SERIOUS_ISSUES) or findings[a][side]['support_check'] == 'UNSUPPORTED'
                        for a in findings for side in SLOTS)
        verified_connection = economic and label == 'AI_AGREED_CONFIRMED' and meaning == 'AI_AGREED_MEANINGFUL'
        item_robust = verified_connection and len(findings) == len(SLOTS) and not contested
        rows.append({'blind_id': b, 'kind': i['kind'],
                     'A': {k: a_[k] for k in ('outcome', 'economic_meaning', 'usefulness', 'confidence', 'verification')},
                     'B': {k: b_[k] for k in ('outcome', 'economic_meaning', 'usefulness', 'confidence', 'verification')},
                     'ai_label': label, 'ai_meaning': meaning, 'ai_verified_economic_connection': verified_connection,
                     'cross_review': findings, 'cross_review_complete': len(findings) == len(SLOTS),
                     'robust_item_conditions': item_robust, 'robust': item_robust and conforming})
    count = lambda pred: sum(1 for r in rows if pred(r))
    econ = [r for r in rows if r['kind'] in AD.ECONOMIC_KINDS]
    diagnostic = {'items': len(rows), 'connection_items': len(econ), 'warning_items': len(rows) - len(econ),
                  'agreed_labels': count(lambda r: r['ai_label'].startswith('AI_AGREED_')),
                  'unresolved_disagreements': count(lambda r: r['ai_label'] == 'AI_UNRESOLVED_DISAGREEMENT'),
                  'quote_not_found': count(lambda r: 'NOT_FOUND' in (r['A']['verification'], r['B']['verification'])),
                  'normalised_match_only': count(lambda r: 'NORMALISED_ONLY' in (r['A']['verification'], r['B']['verification'])),
                  'ai_verified_economic_connections': count(lambda r: r['ai_verified_economic_connection']),
                  'robust_item_conditions_met': count(lambda r: r['robust_item_conditions'])}
    scientific = {'ai_verified_economic_connections': diagnostic['ai_verified_economic_connections'],
                  'robust_ai_verified_economic_connections': count(lambda r: r['robust'])} if conforming else None
    return {'version': RECONCILIATION_V1, 'banner': BANNER, 'packet': pkg['packet'], 'package_sha256': pkg_sha,
            'reviewers': {s: {k: prim[s]['provenance'][k] for k in ('product', 'model_identifier', 'mode', 'run_by')} | {'external_access': prim[s]['external_access'],
                              'sealed_at_utc': seals[s]['sealed_at_utc']} for s in SLOTS},
            'reviewers_distinct': distinct, 'stage_order': order, 'integrity_flags': pkg['integrity_flags'],
            'conforming': conforming, 'nonconformance': reasons,
            'diagnostic_counts': diagnostic, 'conforming_counts': scientific,
            'items': rows, 'notes': notes}


def markdown(rec):
    L = [f"# AI review reconciliation: packet {rec['packet']}", '', f"> **{rec['banner']}**", '',
         f"Stage order: **{rec['stage_order']['status']}** ({rec['stage_order']['detail']}). Reviewers distinct: **{rec['reviewers_distinct']}**.", '',
         '| Slot | Product | Model identifier | Mode | External access |', '|---|---|---|---|---|']
    L += [f"| {s} | {v['product']} | `{v['model_identifier']}` | {v['mode']} | {v['external_access']} |" for s, v in rec['reviewers'].items()]
    L += ['', f"Conforming: **{rec['conforming']}**" + (f" (withheld: {', '.join(rec['nonconformance'])})" if rec['nonconformance'] else ''), '']
    L += ['| Diagnostic count | Value |', '|---|---|'] + [f'| {k} | {v} |' for k, v in rec['diagnostic_counts'].items()]
    L += ['', '| Conforming count | Value |', '|---|---|'] + ([f'| {k} | {v} |' for k, v in rec['conforming_counts'].items()] if rec['conforming_counts']
                                                           else ['| (withheld) | not a conforming result |'])
    L += ['', '| Item | Kind | A | B | AI label | Meaning | Quotes A/B | Robust |', '|---|---|---|---|---|---|---|---|']
    for r in rec['items']:
        lab = lambda x: x['outcome'] or x['usefulness']
        L.append(f"| `{r['blind_id']}` | {r['kind']} | {lab(r['A'])} ({r['A']['confidence']}) | {lab(r['B'])} ({r['B']['confidence']}) | {r['ai_label']} | "
                 f"{r['ai_meaning'] or ''} | {r['A']['verification']}/{r['B']['verification']} | {r['robust']} |")
    if rec['notes']:L += ['', '**Notes**', ''] + [f'- {n}' for n in rec['notes']]
    L += ['', 'Confidence is shown for information only and plays no part in any label. Cross-review findings never change a label.']
    return '\n'.join(L) + '\n'
