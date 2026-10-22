"""Graph Pilot R4 AI-review variant (PROPOSED, not registered): two independent model reviews, two cross-reviews, reconciliation.

A separate, prospective path beside the human Phase B design. It never writes, reads as human, or substitutes for the
human logs (``adjudications-<R>.jsonl``, ``warning-usefulness-<R>.jsonl``) and their seals, and nothing here makes a
packet conform to the human dual-review rule. Every output is labelled as model output.

Version 2 (assurance hardening; V1 packages, answers and seals are refused, never reinterpreted: none was ever made):

* **Package.** ``build_package`` turns a leak-scanned aliased export (``blind_v2.json``) and a content-addressed evidence
  folder (files named ``<sha256>``) into one neutral package: the items exactly as exported, copies of the cited evidence
  verified by hash, the three frozen reviewer texts, a readable ``items.md`` and the two answer templates. Missing
  evidence is recorded as missing, never invented. ``package_manifest.json`` (operator-side, never sent to a model) binds
  the bytes of every reviewer-facing artifact and the exact Stage A and Stage B input lists; the package identity is the
  manifest's hash, so nothing hashes itself. ``load_package`` re-derives ``items.md`` and both templates from
  ``package.json``, so a consistently re-hashed edit still fails.
* **Input bundles.** Before each run the operator records exactly what the model received (``ai-bundle-<stage>-<slot>.json``):
  the hash of every supplied file, compared by content with the manifest (Stage B also with the bytes derived from the
  two sealed primary answers). Both primary bundles must be the same frozen Stage A package. A mismatch is recorded and
  makes the result non-conforming; it is never repaired.
* **Raw responses.** ``record_raw`` keeps every attempt's original bytes unchanged in a private content-addressed store
  (refused if git would track it) and writes a public metadata record (hash, size, extraction status; no content).
  ``extract_answer`` is the one deterministic extraction rule: exactly one fenced JSON block, at the end, parsed strictly.
  A stored ``review`` must equal that extraction; a seal requires the raw bytes to verify. Failed attempts are kept.
* **Stage A (primary), Stage B (cross-review), order.** As in V1: each model answers the identical package; after both
  primary seals each model audits both frozen answers; in git each answer first appears strictly after the other slot's
  seal, each cross-review strictly after both primary answers, and any prompt-injection disposition strictly before
  both primary answers. Cross-review slot X must be run by the same model (product and identifier) as primary slot X.
* **Prompt injection.** Instruction-like text in items or evidence is flagged (``INSTRUCTION_ATTEMPT_SUSPECTED`` or
  ``AMBIGUOUS_INSTRUCTION_LIKE_TEXT``), never removed. A named human records a disposition for each flag before Stage A;
  an undisposed, unresolved or confirmed attempt withholds conformance. Pattern matching cannot detect every injection.
* **Stage C (reconciliation).** Deterministic: only character-exact quotes verify; an outcome counts only where both
  answers agree; any difference is ``AI_UNRESOLVED_DISAGREEMENT``. Audits never change a label. Each item reports six
  separate dimensions, from file and quote integrity to independent real-world validation (which this instrument never
  provides). ``ai_audit_supported`` needs both auditors to find both answers ``SUPPORTED``. Scientific (conforming)
  counts are withheld unless every condition in ``nonconformance`` holds; diagnostic counts are always reported.
* **Adjudication, not discovery.** Reviewers and auditors judge the given items against the given evidence only. A
  browsing run, or one declaring outside sources, is never a conforming adjudication.

Operator-recorded identities, run times and bundles remain the operator's attestation unless corroborated by provider
evidence; this module checks their consistency, not their truth.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

from src.research.graph import adjudication as AD
from src.research.graph import pilot as P

ROOT = Path(__file__).resolve().parents[3]
TEXTS_DIR = ROOT / 'docs/strategy/graph_pilot_r4_ai_review'
TEXTS = {'checklist': 'review_checklist_v001.md', 'primary': 'stage_a_reviewer_prompt_v001.md', 'cross': 'stage_b_cross_review_prompt_v001.md'}
PACKAGE_V2, MANIFEST_V1, PRIMARY_V2, CROSS_V2 = 'GRAPH_AI_REVIEW_PACKAGE_V2', 'GRAPH_AI_REVIEW_MANIFEST_V1', 'GRAPH_AI_PRIMARY_REVIEW_V2', 'GRAPH_AI_CROSS_REVIEW_V2'
ANSWER_V1, CROSS_ANSWER_V1 = 'GRAPH_AI_REVIEW_ANSWER_V1', 'GRAPH_AI_CROSS_ANSWER_V1'  # model-facing templates: unchanged
SEAL_V2, RECONCILIATION_V2 = 'GRAPH_AI_REVIEW_SEAL_V2', 'GRAPH_AI_RECONCILIATION_V2'
BUNDLE_V1, RAW_RECORD_V1, DISPOSITION_V1 = 'GRAPH_AI_REVIEW_INPUT_BUNDLE_V1', 'GRAPH_AI_RAW_RESPONSE_RECORD_V1', 'GRAPH_AI_INJECTION_DISPOSITION_V1'
EXTRACTION_V1 = 'SINGLE_FENCED_JSON_BLOCK_AT_END_V1'
LEGACY = ('GRAPH_AI_REVIEW_PACKAGE_V1', 'GRAPH_AI_PRIMARY_REVIEW_V1', 'GRAPH_AI_CROSS_REVIEW_V1', 'GRAPH_AI_REVIEW_SEAL_V1')
SLOTS, STAGES = ('A', 'B'), ('primary', 'cross')
BANNER = 'AI-ADJUDICATED: model outputs, not human judgments. Not a conforming human dual review.'
SYNTHETIC_BANNER = 'SYNTHETIC FIXTURE PROVENANCE: these answers are not real model evidence.'
SEAL_STATEMENT = 'This file is a model output recorded unchanged by the named operator. It is not a human judgment.'
BUNDLE_STATEMENT = 'The named operator records the exact files supplied to the model for this run.'
DISPOSITION_STATEMENT = 'The named human disposes of each integrity flag before any primary answer is revealed.'
INTERPRETATION = ('Agreement between two AI models, with exact quotations, is AI agreement: not human certification, not established '
                  'economic truth, not a causal or economic-mechanism finding and not a trading signal. No dimension here is '
                  'independent real-world validation.')

OUTCOMES = ('CONFIRMED', 'FALSE', 'TRIVIAL', 'PLAUSIBLE_UNVERIFIED', 'UNKNOWN')
EVIDENCE_OUTCOMES = ('CONFIRMED', 'FALSE')
MEANING, USEFULNESS = P.MEANING, AD.USEFULNESS
CONFIDENCE, YES_NO = ('HIGH', 'MEDIUM', 'LOW'), ('YES', 'NO')
MODES = ('EVIDENCE_PACK_ONLY', 'BROWSING_ALLOWED')
PROVENANCE_CLASSES = ('REAL_MODEL_RUN', 'SYNTHETIC_FIXTURE')
SUPPORT_CHECKS = ('SUPPORTED', 'PARTLY_SUPPORTED', 'UNSUPPORTED', 'CANNOT_CHECK')
ISSUES = ('FACTUAL_ERROR', 'MISQUOTE', 'UNSUPPORTED_CONCLUSION', 'MISSED_EVIDENCE', 'INVENTED_CONTENT', 'METHOD_DIFFERENCE', 'OTHER')
SERIOUS_ISSUES = ('FACTUAL_ERROR', 'MISQUOTE', 'UNSUPPORTED_CONCLUSION', 'INVENTED_CONTENT')
NATURES = ('NO_DISAGREEMENT', 'GENUINE_EVIDENTIAL', 'METHODOLOGICAL', 'ONE_SIDE_UNSUPPORTED', 'BOTH_UNSUPPORTED', 'CANNOT_DETERMINE')
DISPOSITIONS = ('HARMLESS_QUOTED_EXAMPLE', 'NOT_AN_INSTRUCTION', 'INSTRUCTION_ATTEMPT_CONFIRMED', 'UNRESOLVED')

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
PROVENANCE_KEYS = ('reviewer_kind', 'provenance_class', 'product', 'model_identifier', 'mode', 'prompt_sha256', 'input_bundle_sha256',
                   'run_started_utc', 'run_finished_utc', 'usage', 'resources', 'conversation_reference', 'raw_output_sha256',
                   'raw_attempt', 'run_by')
DOC_KEYS = {'primary': ('version', 'slot', 'manifest_sha256', 'provenance', 'review'),
            'cross': ('version', 'slot', 'manifest_sha256', 'reviewed', 'provenance', 'review')}
DERIVED_CROSS_INPUTS = ('review_A.json', 'review_B.json')
ZERO_WIDTH = dict.fromkeys(map(ord, '­​‌‍⁠﻿'), None)
_W = r'(?:all |any |the |your |these |those |earlier |previous |prior |above |preceding )*'
INJECTION_PATTERNS = (  # matched on NFKC text with zero-width characters removed and whitespace collapsed
    ('OVERRIDE_INSTRUCTIONS', 'INSTRUCTION_ATTEMPT_SUSPECTED',
     re.compile(r'\b(?:ignore|disregard|forget|override|bypass)\s' + _W + r'(?:instructions?|rules|checklist|guidance|prompts?|directions)\b', re.I)),
    ('DIRECT_LABEL_REQUEST', 'INSTRUCTION_ATTEMPT_SUSPECTED',
     re.compile(r'\b(?:mark|label|rate|classify|score|treat|record|assess)\s(?:this|the|these|each|every)\s(?:items?|connections?|relationships?|entr(?:y|ies)|evidence|documents?|links?)\sas\b', re.I)),
    ('ADDRESSES_THE_MODEL', 'INSTRUCTION_ATTEMPT_SUSPECTED',
     re.compile(r'\b(?:you are (?:now )?(?:an? )?(?:ai|language model|assistant|chatbot|evaluator|assessor)|'
                r'(?:note|message|instructions?) (?:to|for) (?:the |any )?(?:ai|model|llm|reviewer|auditor|assessor|evaluator)s?)\b', re.I)),
    ('ASSERTS_CORRECT_LABEL', 'INSTRUCTION_ATTEMPT_SUSPECTED',
     re.compile(r'\b(?:the )?correct (?:label|classification|answer|outcome|verdict|rating) (?:here )?(?:is|would be|should be)\b|'
                r'\b(?:reviewers?|auditors?|assessors?|evaluators?|models?)\s(?:should|must)\s(?:mark|label|answer|classify|confirm|treat|output|return|rate)\b', re.I)),
    ('MENTIONS_PROMPTS', 'AMBIGUOUS_INSTRUCTION_LIKE_TEXT', re.compile(r'\b(?:system prompt|prompt injection|jailbreak)\b', re.I)),
    ('ROLE_PREFIX', 'AMBIGUOUS_INSTRUCTION_LIKE_TEXT', re.compile(r'\b(?:reviewer|auditor|assistant|system)s?:\s', re.I)))
FORMATS = ((b'%PDF', 'pdf'), (b'PK\x03\x04', 'zip'), (b'\x89PNG', 'png'), (b'\xff\xd8\xff', 'jpg'), (b'GIF8', 'gif'))


def fail(message):
    raise P.PilotError(message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    """The one serialisation of a written JSON artefact (as ``P.write_new``), so derived inputs are byte-reproducible."""
    return (json.dumps(value, indent=1, ensure_ascii=False) + '\n').encode('utf-8')


def canonical_sha256(value):
    return sha256_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def human(by, what):
    if not isinstance(by, str) or not by.strip() or P.ASSISTANT_NAME.search(by):fail(f'{what} is recorded by a named human, not an assistant')


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
    return ' '.join(html.unescape(text).replace('\xa0', ' ').split()).casefold()


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
        data = f.read_bytes(); out[role] = {'name': name, 'sha256': sha256_bytes(data), 'bytes': data, 'text': data.decode('utf-8')}
    return out


# -- prompt-injection flags -------------------------------------------------------------------------
def injection_text(text):
    return ' '.join(unicodedata.normalize('NFKC', text).translate(ZERO_WIDTH).split())


def scan_injection(where, text):
    """One flag per (location, pattern) with its match count; the text itself is never changed or removed."""
    t = injection_text(text); out = []
    for code, severity, pat in INJECTION_PATTERNS:
        n = len(pat.findall(t))
        if n:out.append({'id': sha256_bytes(f'{where}|{code}'.encode('utf-8'))[:16], 'where': where, 'code': code, 'severity': severity, 'matches': n})
    return out


def flag_excerpts(package_dir):
    """For the human disposing of flags: each flag with its matched passages (normalised text, 60 characters of context)."""
    d = Path(package_dir); pkg, _ = load_package(d); items = {i['blind_id']: i for i in pkg['items']}; out = []
    for f in pkg['integrity_flags']:
        text = ' '.join(s for _, s in P.strings(items[f['where']])) if f['where'] in items else (d / f['where']).read_bytes().decode('utf-8', 'replace')
        t = injection_text(text); pat = next(p for c, _, p in INJECTION_PATTERNS if c == f['code'])
        out.append({**f, 'excerpts': [t[max(0, m.start() - 60):m.end() + 60] for m in pat.finditer(t)][:10]})
    return out


# -- package ----------------------------------------------------------------------------------------
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


def derived_files(package, texts):
    """Every generated reviewer-facing artifact, as exact bytes, from package.json and the frozen texts alone."""
    out = {'package.json': json_bytes(package), 'items.md': render_items(package).encode('utf-8'),
           'response_template.json': json_bytes(answer_template(package['items'])),
           'cross_review_template.json': json_bytes(cross_template(package['items']))}
    for t in texts.values():out[f"texts/{t['name']}"] = t['bytes']
    return out


def stage_files(package, stage):
    """The exact package files supplied at a stage. Stage B also receives the two derived sealed answers (not listed here)."""
    texts = [package['texts']['checklist']['file'], package['texts'][stage]['file']]
    template = 'response_template.json' if stage == 'primary' else 'cross_review_template.json'
    return sorted(['package.json', 'items.md', template, *texts, *(e['file'] for e in package['evidence'].values() if e['file'] != 'MISSING_FROM_PACKAGE')])


def build_package(export_path, evidence_dir, out_dir, own_from=None, texts_dir=TEXTS_DIR):
    """The neutral review package and its manifest. Refuses an unscanned export, any leak in items or frozen texts, or a hash mismatch."""
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
    evidence, flags, blobs, unscanned = {}, [], {}, []
    for h in sorted({h for i in items for h in item_evidence(i)}):
        src = Path(evidence_dir) / h
        if not src.is_file():evidence[h] = {'file': 'MISSING_FROM_PACKAGE', 'bytes': None, 'format': None, 'machine_checkable': False}; continue
        data = src.read_bytes()
        if sha256_bytes(data) != h:fail(f'evidence file {h} does not match its hash')
        ext = sniff(data); name = f'evidence/{h}.{ext}'; blobs[name] = data
        text = evidence_text(src) if ext in ('json', 'html', 'txt') else None
        evidence[h] = {'file': name, 'bytes': len(data), 'format': ext, 'machine_checkable': text is not None}
        if text is None:unscanned.append(name)
        else:flags += scan_injection(name, data.decode('utf-8'))  # raw text, so comments and attributes are scanned too
    for i in items:flags += scan_injection(i['blind_id'], ' '.join(s for _, s in P.strings(i)))
    package = {'version': PACKAGE_V2, 'packet': export['packet'], 'fixture': export.get('fixture'),
               'export': {'name': Path(export_path).name, 'sha256': P.sha256(export_path)},
               'texts': {role: {'file': f"texts/{t['name']}", 'sha256': t['sha256']} for role, t in texts.items()},
               'items': items, 'evidence': evidence, 'integrity_flags': flags, 'unscanned_evidence': unscanned}
    generated = derived_files(package, texts)
    if P.scan_leaks(generated['items.md'].decode('utf-8'), own):fail('the rendered items would leak arm-identifying text')
    artifacts = {**generated, **blobs}
    manifest = {'version': MANIFEST_V1, 'package_version': PACKAGE_V2, 'packet': export['packet'],
                'files': {rel: {'sha256': sha256_bytes(b), 'bytes': len(b)} for rel, b in sorted(artifacts.items())},
                'stage_inputs': {s: stage_files(package, s) for s in STAGES}, 'cross_derived_inputs': list(DERIVED_CROSS_INPUTS),
                'note': 'Operator-side. Never supplied to a model. The package identity is the sha256 of this file.'}
    for rel, data in artifacts.items():
        f = out / rel; f.parent.mkdir(parents=True, exist_ok=True)
        with f.open('xb') as h_:h_.write(data)
    P.write_new(out / 'package_manifest.json', manifest)
    return package


def load_package(package_dir):
    """The package and its identity (the manifest hash). Every listed artifact must hold its manifest bytes, the list must be
    exactly the package's artifacts, and the generated files must be the deterministic rendering of package.json."""
    d = Path(package_dir); mf = d / 'package_manifest.json'
    pj = d / 'package.json'
    if pj.is_file() and json.loads(pj.read_text(encoding='utf-8')).get('version') in LEGACY:
        fail('a GRAPH_AI_REVIEW_PACKAGE_V1 package has no artifact manifest and cannot be used under V2; build a new package')
    if not mf.is_file():fail('package_manifest.json is missing: the package artifacts are not bound')
    manifest = json.loads(mf.read_text(encoding='utf-8'))
    if manifest.get('version') != MANIFEST_V1 or manifest.get('package_version') != PACKAGE_V2:fail(f'not a {MANIFEST_V1} manifest of a {PACKAGE_V2} package')
    for rel, e in manifest['files'].items():
        f = d / rel
        if not f.is_file():fail(f'package artifact {rel} is missing')
        if P.sha256(f) != e['sha256']:fail(f'package artifact {rel} changed (its bytes differ from the manifest)')
    pkg = json.loads(pj.read_text(encoding='utf-8'))
    if pkg.get('version') != PACKAGE_V2 or pkg.get('packet') != manifest['packet']:fail(f'package.json is not the {PACKAGE_V2} package this manifest binds')
    texts = {}
    for role, t in pkg['texts'].items():
        f = d / t['file']
        if P.sha256(f) != t['sha256']:fail(f'frozen {role} text in the package changed')
        texts[role] = {'name': Path(t['file']).name, 'bytes': f.read_bytes()}
    for h, e in pkg['evidence'].items():
        if e['file'] != 'MISSING_FROM_PACKAGE' and P.sha256(d / e['file']) != h:fail(f'evidence {h} in the package changed')
    expected = {*derived_files(pkg, texts), *(e['file'] for e in pkg['evidence'].values() if e['file'] != 'MISSING_FROM_PACKAGE')}
    if set(manifest['files']) != expected:fail(f'the manifest does not list exactly the package artifacts: {sorted(expected ^ set(manifest["files"]))}')
    for rel, data in derived_files(pkg, texts).items():
        if sha256_bytes(data) != manifest['files'][rel]['sha256']:fail(f'{rel} is not the deterministic rendering of package.json (stale or altered)')
    if manifest['stage_inputs'] != {s: stage_files(pkg, s) for s in STAGES} or manifest['cross_derived_inputs'] != list(DERIVED_CROSS_INPUTS):
        fail('the manifest stage input lists are not the deterministic lists for this package')
    return pkg, P.sha256(mf)


# -- support checks ---------------------------------------------------------------------------------
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


# -- file layout ------------------------------------------------------------------------------------
def files(package_dir, stage, slot):
    d = Path(package_dir); stem = 'ai-review' if stage == 'primary' else 'ai-cross-review'
    return {'answer': d / f'{stem}-{slot}.json', 'seal': d / f'{stem}-seal-{slot}.json', 'bundle': d / f'ai-bundle-{stage}-{slot}.json'}


def raw_record_path(package_dir, stage, slot, attempt):
    return Path(package_dir) / f'ai-raw-{stage}-{slot}-{attempt:03d}.json'


def raw_records(package_dir, stage, slot):
    """All attempt records for a stage and slot, in order; numbering must be contiguous from 1."""
    found = sorted(Path(package_dir).glob(f'ai-raw-{stage}-{slot}-*.json'))
    recs = [json.loads(f.read_text(encoding='utf-8')) for f in found]
    if [r.get('attempt') for r in recs] != list(range(1, len(recs) + 1)) or [f.name for f in found] != [raw_record_path(package_dir, stage, slot, n).name for n in range(1, len(recs) + 1)]:
        fail(f'raw attempt records for {stage} {slot} are not numbered contiguously from 1 (an attempt record is missing or renamed)')
    return recs


DISPOSITION_FILE = 'injection_dispositions.json'


# -- raw model responses ----------------------------------------------------------------------------
def _strict_object(pairs):
    out = {}
    for k, v in pairs:
        if k in out:raise ValueError(f'duplicate key {k!r}')
        out[k] = v
    return out


def _no_constant(name):
    raise ValueError(f'non-standard JSON constant {name}')


def extract_answer(data):
    """The one extraction rule (``SINGLE_FENCED_JSON_BLOCK_AT_END_V1``) from raw response bytes: (status, object or None).

    The bytes must be UTF-8 and contain exactly one fenced code block (an opening line starting with three backticks and
    an optional ``json`` info string, a closing line of three backticks), followed only by whitespace. Its content is parsed
    as strict JSON (no duplicate keys, no NaN or Infinity) and must be an object. Nothing is repaired, trimmed or rewritten."""
    if not data.strip():return 'EMPTY', None
    try:text = data.decode('utf-8')
    except UnicodeDecodeError:return 'NOT_UTF8', None
    lines = text.splitlines(keepends=True); blocks, cur, info, close = [], None, None, None
    for n, line in enumerate(lines):
        bare = line.rstrip('\r\n')
        if cur is None and bare.startswith('```'):cur, info = [], bare[3:].strip()
        elif cur is not None and bare.rstrip() == '```':blocks.append((info, ''.join(cur))); cur, close = None, n
        elif cur is not None:cur.append(line)
    if cur is not None:return 'UNCLOSED_CODE_BLOCK', None
    if not blocks:return 'NO_CODE_BLOCK', None
    if len(blocks) > 1:return 'MULTIPLE_CODE_BLOCKS', None
    if blocks[0][0].casefold() not in ('', 'json'):return 'NOT_A_JSON_BLOCK', None
    if ''.join(lines[close + 1:]).strip():return 'BLOCK_NOT_AT_END', None
    try:obj = json.loads(blocks[0][1], object_pairs_hook=_strict_object, parse_constant=_no_constant)
    except ValueError:return 'INVALID_JSON', None
    return ('EXTRACTED', obj) if isinstance(obj, dict) else ('NOT_AN_OBJECT', None)


def check_private_store(store):
    """The raw store must not be tracked by git: outside any repository, or ignored by the one containing it (a path inside
    the store is probed, so a directory pattern such as ``raw/`` counts before the store exists)."""
    store = Path(store).resolve(); probe = store
    while not probe.exists():probe = probe.parent
    top = AD.git(probe if probe.is_dir() else probe.parent, 'rev-parse', '--show-toplevel')
    if top.returncode == 0 and (AD.git(top.stdout.strip(), 'check-ignore', '-q', str(store / 'raw-response')).returncode != 0
                                or AD.git(top.stdout.strip(), 'ls-files', '--', str(store)).stdout.strip()):
        fail(f'raw store {store} is inside a git working tree and not ignored: private model transcripts must never be committed')
    return store


def record_raw(package_dir, stage, slot, raw_path, raw_store, by, received_at=None, now=None):
    """Keep one attempt's raw response bytes unchanged in the private store and write its public metadata record (no content).

    Every attempt is recorded, including empty, truncated and unparseable ones; records are numbered and never overwritten."""
    if stage not in STAGES or slot not in SLOTS:fail(f'stage is one of {STAGES}; slot one of {SLOTS}')
    human(by, 'a raw response record'); d = Path(package_dir); _, msha = load_package(d); store = check_private_store(raw_store)
    data = Path(raw_path).read_bytes(); h = sha256_bytes(data); store.mkdir(parents=True, exist_ok=True); kept = store / h
    if kept.exists():
        if sha256_bytes(kept.read_bytes()) != h:fail(f'the raw store holds different bytes under {h}: the store was altered')
    else:
        with kept.open('xb') as f:f.write(data)
    status, obj = extract_answer(data); n = len(raw_records(d, stage, slot)) + 1
    rec = {'version': RAW_RECORD_V1, 'stage': stage, 'slot': slot, 'attempt': n, 'manifest_sha256': msha, 'raw_sha256': h, 'raw_bytes': len(data),
           'extraction_rule': EXTRACTION_V1, 'extraction_status': status, 'extracted_sha256': canonical_sha256(obj) if obj is not None else None,
           'received_at_utc': P.utc(received_at).isoformat() if received_at else 'UNKNOWN', 'recorded_by': by, 'recorded_at_utc': P.utc(now).isoformat(),
           'storage': 'raw bytes kept privately, content-addressed by raw_sha256; never in this repository'}
    P.write_new(raw_record_path(d, stage, slot, n), rec)
    return rec


def raw_status(package_dir, stage, slot, provenance, review, msha, raw_store=None):
    """Whether a stored answer is the deterministic extraction of the retained raw bytes it cites, and its attempt history.

    ``VERIFIED`` only when the cited record is this stage and slot's latest attempt, its raw bytes are in the store with that
    hash, and re-extraction gives exactly the stored review. ``attempts`` is ``CONFLICTING`` when an earlier attempt also
    yielded an extractable answer (a re-run that was not a technical failure)."""
    try:recs = raw_records(package_dir, stage, slot)
    except P.PilotError as error:return {'status': 'RECORDS_NOT_CONTIGUOUS', 'attempts': 'UNKNOWN', 'detail': str(error)}
    n = provenance.get('raw_attempt')
    attempts = 'CONFLICTING' if any(r['extraction_status'] == 'EXTRACTED' for r in recs[:-1]) else ('SINGLE' if len(recs) == 1 else 'TECHNICAL_RETRIES_ONLY')
    st = lambda status, detail='': {'status': status, 'attempts': attempts if recs else 'NONE', 'detail': detail}
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= len(recs):return st('RECORD_MISSING', f'no raw record for attempt {n!r}')
    rec = recs[n - 1]
    if (rec.get('version'), rec.get('stage'), rec.get('slot'), rec.get('raw_sha256'), rec.get('manifest_sha256')) != \
            (RAW_RECORD_V1, stage, slot, provenance.get('raw_output_sha256'), msha):return st('RECORD_MISMATCH', 'record and answer cite different raw bytes or package')
    if n != len(recs):return st('NOT_LATEST_ATTEMPT', f'attempt {n} of {len(recs)}')
    if raw_store is None:return st('RAW_NOT_AVAILABLE', 'no private raw store supplied')
    f = Path(raw_store) / rec['raw_sha256']
    if not f.is_file():return st('RAW_NOT_AVAILABLE', 'raw bytes absent from the store')
    data = f.read_bytes()
    if sha256_bytes(data) != rec['raw_sha256']:return st('RAW_HASH_MISMATCH', 'stored bytes do not have the recorded hash')
    status, obj = extract_answer(data)
    if status != rec['extraction_status'] or (obj is not None and canonical_sha256(obj) != rec['extracted_sha256']):
        return st('EXTRACTION_CHANGED', 're-extraction differs from the record')
    if status != 'EXTRACTED':return st('EXTRACTION_FAILED', status)
    if canonical_sha256(obj) != canonical_sha256(review):return st('REVIEW_DIFFERS_FROM_RAW', 'the stored review is not the extracted answer')
    return st('VERIFIED')


# -- input bundles ----------------------------------------------------------------------------------
def cross_input_bytes(package_dir, slot):
    """The exact bytes of review_<slot>.json as auditors receive it: the sealed model answer only, provenance withheld."""
    d = Path(package_dir); load_seal(d, 'primary', slot)
    return json_bytes(json.loads(files(d, 'primary', slot)['answer'].read_text(encoding='utf-8'))['review'])


def expected_inputs(package_dir, stage):
    """{published name: bytes} a model must receive at a stage; Stage B requires both primary seals."""
    d = Path(package_dir); pkg, _ = load_package(d)
    out = {rel: (d / rel).read_bytes() for rel in stage_files(pkg, stage)}
    if stage == 'cross':out.update({f'review_{s}.json': cross_input_bytes(d, s) for s in SLOTS})
    return out


def tree_hashes(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): {'sha256': P.sha256(p), 'bytes': p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()}


def bundle_differences(supplied, expected):
    """Content comparison: each expected file must be supplied with identical bytes, and nothing else may be supplied."""
    out = [{'path': rel, 'problem': 'MISSING'} for rel in sorted(set(expected) - set(supplied))]
    out += [{'path': rel, 'problem': 'EXTRA_FILE_SUPPLIED'} for rel in sorted(set(supplied) - set(expected))]
    out += [{'path': rel, 'problem': 'BYTES_DIFFER'} for rel in sorted(set(supplied) & set(expected)) if supplied[rel] != expected[rel]]
    return out


def record_bundle(package_dir, stage, slot, supplied_dir, by, write=False, now=None):
    """Record the exact files supplied to a model before its run (once). With ``write``, first create ``supplied_dir`` from
    the package. The record hashes what is actually in ``supplied_dir``; differences are kept, never corrected."""
    if stage not in STAGES or slot not in SLOTS:fail(f'stage is one of {STAGES}; slot one of {SLOTS}')
    human(by, 'an input bundle'); d = Path(package_dir); _, msha = load_package(d); want = expected_inputs(d, stage)
    src = Path(supplied_dir)
    if write:
        if src.exists():fail(f'{src} exists; a bundle folder is written once')
        for rel, data in want.items():
            f = src / rel; f.parent.mkdir(parents=True, exist_ok=True)
            with f.open('xb') as h:h.write(data)
    if not src.is_dir():fail(f'{src} is not a folder of supplied files')
    supplied = tree_hashes(src)
    doc = {'version': BUNDLE_V1, 'stage': stage, 'slot': slot, 'manifest_sha256': msha, 'supplied': supplied,
           'differences_at_record': bundle_differences({k: v['sha256'] for k, v in supplied.items()}, {k: sha256_bytes(v) for k, v in want.items()}),
           'recorded_by': by, 'recorded_at_utc': P.utc(now).isoformat(), 'statement': BUNDLE_STATEMENT}
    try:P.write_new(files(d, stage, slot)['bundle'], doc)
    except FileExistsError as error:raise P.PilotError(f'the {stage} {slot} input bundle is already recorded; a bundle record is immutable') from error
    return doc


def bundle_status(package_dir, stage, slot, cited, msha, run_started):
    """``VERIFIED`` when the cited record exists, binds this package, was recorded no later than the run started and its
    supplied files equal the expected inputs by content; otherwise the reason, with any differences. ``supplied_digest``
    identifies the supplied file set, so two primary bundles can be compared."""
    f = files(package_dir, stage, slot)['bundle']
    doc = json.loads(f.read_text(encoding='utf-8')) if f.is_file() else {}
    digest = canonical_sha256({k: v['sha256'] for k, v in doc['supplied'].items()}) if isinstance(doc.get('supplied'), dict) else None
    return {**bundle_check(package_dir, stage, slot, cited, msha, run_started), 'supplied_digest': digest}


def bundle_check(package_dir, stage, slot, cited, msha, run_started):
    f = files(package_dir, stage, slot)['bundle']
    if not f.is_file():return {'status': 'MISSING', 'differences': []}
    if P.sha256(f) != cited:return {'status': 'NOT_CITED', 'differences': []}
    doc = json.loads(f.read_text(encoding='utf-8'))
    if (doc.get('version'), doc.get('stage'), doc.get('slot'), doc.get('manifest_sha256')) != (BUNDLE_V1, stage, slot, msha):
        return {'status': 'MISMATCH', 'differences': [{'path': '-', 'problem': 'RECORD_FOR_ANOTHER_PACKAGE_STAGE_OR_SLOT'}]}
    try:want = {k: sha256_bytes(v) for k, v in expected_inputs(package_dir, stage).items()}
    except P.PilotError as error:return {'status': 'MISMATCH', 'differences': [{'path': '-', 'problem': str(error)}]}
    diff = bundle_differences({k: v['sha256'] for k, v in doc['supplied'].items()}, want)
    if diff:return {'status': 'MISMATCH', 'differences': diff}
    if P.parse_time(doc['recorded_at_utc']) > P.parse_time(run_started):return {'status': 'RECORDED_AFTER_RUN_START', 'differences': []}
    return {'status': 'VERIFIED', 'differences': []}


# -- answers ----------------------------------------------------------------------------------------
def check_provenance(p, stage, pkg_texts, where):
    if not isinstance(p, dict) or tuple(sorted(p)) != tuple(sorted(PROVENANCE_KEYS)):fail(f'{where}: provenance has exactly {PROVENANCE_KEYS}')
    if p['reviewer_kind'] != 'AI_MODEL':fail(f'{where}: reviewer_kind is AI_MODEL; this path never records human judgments')
    if p['provenance_class'] not in PROVENANCE_CLASSES:fail(f'{where}: provenance_class is one of {PROVENANCE_CLASSES}')
    if p['mode'] not in MODES:fail(f'{where}: mode is one of {MODES}')
    for k in ('product', 'model_identifier', 'run_by'):
        if not isinstance(p[k], str) or not p[k].strip():fail(f'{where}: provenance.{k} is required (UNKNOWN where truly unknown)')
    if P.ASSISTANT_NAME.search(p['run_by']):fail(f'{where}: run_by is the human who ran the model and stored its answer, not an assistant')
    want = {r: pkg_texts[r]['sha256'] for r in ('checklist', stage)}
    if p['prompt_sha256'] != want:fail(f'{where}: prompt_sha256 must equal the frozen texts in the package {want}')
    for k in ('raw_output_sha256', 'input_bundle_sha256'):
        if not re.fullmatch(r'[0-9a-f]{64}', str(p[k])):fail(f'{where}: {k} is a sha256')
    if not isinstance(p['raw_attempt'], int) or isinstance(p['raw_attempt'], bool) or p['raw_attempt'] < 1:fail(f'{where}: raw_attempt is the cited attempt number')
    if not (p['conversation_reference'] == 'UNKNOWN' or re.fullmatch(r'sha256:[0-9a-f]{64}', str(p['conversation_reference']))):
        fail(f'{where}: conversation_reference is "UNKNOWN" or "sha256:<hash>" of the private reference (never the reference itself)')
    start, end = P.parse_time(p['run_started_utc']), P.parse_time(p['run_finished_utc'])
    if end < start:fail(f'{where}: the run finished before it started')
    for k in ('usage', 'resources'):
        if not (isinstance(p[k], (str, dict)) and p[k]):fail(f'{where}: provenance.{k} is recorded, or "UNKNOWN"')


def check_text(v, where, field):
    if not isinstance(v, str):fail(f'{where}: {field} is text (may be empty)')


def check_sources(v, where):
    if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):fail(f'{where}: sources_outside_package is a list of sources')


def load_doc(path, stage, msha):
    w = Path(path).name; doc = json.loads(Path(path).read_text(encoding='utf-8'))
    version = PRIMARY_V2 if stage == 'primary' else CROSS_V2
    if doc.get('version') in LEGACY:fail(f'{w}: a V1 answer document is not accepted under V2; it carries no raw-response or bundle provenance')
    if not isinstance(doc, dict) or tuple(sorted(doc)) != tuple(sorted(DOC_KEYS[stage])) or doc['version'] != version:fail(f'{w}: a {version} document has exactly {DOC_KEYS[stage]}')
    if doc['slot'] not in SLOTS or doc['manifest_sha256'] != msha:fail(f'{w}: slot A or B, answering this exact package (manifest_sha256)')
    return doc, w


def validate_primary(package_dir, path, raw_store=None):
    """One primary answer: every item once, checklist labels only, support from the item's own evidence; quotes checked.
    Raw-response and input-bundle provenance are reported as statuses (they decide conformance, not validity)."""
    d = Path(package_dir); pkg, msha = load_package(d); doc, w = load_doc(path, 'primary', msha)
    check_provenance(doc['provenance'], 'primary', pkg['texts'], w)
    ans = doc['review']
    if not isinstance(ans, dict) or tuple(sorted(ans)) != tuple(sorted(ANSWER_KEYS)) or ans['template_version'] != ANSWER_V1:
        fail(f'{w}: review is the model answer in the template ({ANSWER_KEYS})')
    dec = ans['reviewer_declaration']
    if not isinstance(dec, dict) or tuple(sorted(dec)) != tuple(sorted(DECLARATION_KEYS)) or dec['used_only_package_files'] not in YES_NO:
        fail(f'{w}: reviewer_declaration has exactly {DECLARATION_KEYS}')
    check_sources(dec['sources_outside_package'], w); check_text(dec['integrity_notes'], w, 'integrity_notes'); check_text(dec['general_limitations'], w, 'general_limitations')
    if not isinstance(ans['items'], list):fail(f'{w}: items is a list')
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
    p = doc['provenance']
    external = p['mode'] == 'BROWSING_ALLOWED' or dec['used_only_package_files'] == 'NO' or bool(dec['sources_outside_package']) \
        or any(r['sources_outside_package'] for r in out.values())
    return {'slot': doc['slot'], 'provenance': p, 'declaration': dec, 'items': out, 'external_access': external,
            'raw': raw_status(d, 'primary', doc['slot'], p, ans, msha, raw_store),
            'bundle': bundle_status(d, 'primary', doc['slot'], p['input_bundle_sha256'], msha, p['run_started_utc'])}


def validate_cross(package_dir, path, primaries=None, raw_store=None):
    """One cross-review: both frozen answers, every item once, no labels of its own, missed evidence quoted from the item."""
    d = Path(package_dir); pkg, msha = load_package(d)
    primaries = primaries or {s: validate_primary(d, files(d, 'primary', s)['answer']) for s in SLOTS}
    doc, w = load_doc(path, 'cross', msha)
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
    if not isinstance(ans['items'], list):fail(f'{w}: items is a list')
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
    p = doc['provenance']
    external = p['mode'] == 'BROWSING_ALLOWED' or dec['used_only_package_files'] == 'NO' or bool(dec['sources_outside_package'])
    return {'slot': doc['slot'], 'provenance': p, 'declaration': dec, 'items': out, 'external_access': external,
            'systematic_differences': ans['systematic_differences'], 'limitations': ans['limitations'],
            'raw': raw_status(d, 'cross', doc['slot'], p, ans, msha, raw_store),
            'bundle': bundle_status(d, 'cross', doc['slot'], p['input_bundle_sha256'], msha, p['run_started_utc'])}


def labels(r):
    return (r['outcome'], r['economic_meaning'], r['usefulness'])


# -- seals ------------------------------------------------------------------------------------------
def seal(package_dir, stage, slot, by, raw_store, now=None):
    """The operator's once-only seal over a validated answer whose raw response verifies. Cross seals need both primary seals.
    A bundle or identity problem does not stop a seal (it is recorded and withholds conformance); an unverified raw response does."""
    if stage not in STAGES or slot not in SLOTS:fail(f'stage is one of {STAGES}; slot one of {SLOTS}')
    human(by, 'the seal')
    d = Path(package_dir); f = files(d, stage, slot)
    if stage == 'cross':
        for s in SLOTS:load_seal(d, 'primary', s)
        v = validate_cross(d, f['answer'], raw_store=raw_store)
    else:v = validate_primary(d, f['answer'], raw_store=raw_store)
    if v['slot'] != slot:fail(f'{f["answer"].name} answers slot {v["slot"]}, not {slot}')
    if v['provenance']['run_by'].strip() != by.strip():fail('the seal is recorded by the operator named in the provenance')
    if v['raw']['status'] != 'VERIFIED':fail(f'{f["answer"].name}: raw response provenance is {v["raw"]["status"]} ({v["raw"]["detail"]}); only an answer extracted unchanged from retained raw bytes is sealed')
    _, msha = load_package(d); p = v['provenance']
    doc = {'version': SEAL_V2, 'stage': stage, 'slot': slot, 'manifest_sha256': msha, 'answer': {'path': f['answer'].name, 'sha256': P.sha256(f['answer'])},
           'provenance_class': p['provenance_class'], 'product': p['product'], 'model_identifier': p['model_identifier'], 'mode': p['mode'],
           'raw_output_sha256': p['raw_output_sha256'], 'raw_attempt': p['raw_attempt'], 'input_bundle_sha256': p['input_bundle_sha256'],
           'recorded_by': by, 'sealed_at_utc': P.utc(now).isoformat(), 'statement': SEAL_STATEMENT}
    if P.parse_time(doc['sealed_at_utc']) < P.parse_time(p['run_finished_utc']):fail('a seal cannot precede the end of the run it seals')
    try:P.write_new(f['seal'], doc)
    except FileExistsError as error:raise P.PilotError(f'{stage} answer {slot} is already sealed; a seal is immutable') from error
    return doc


def load_seal(package_dir, stage, slot):
    d = Path(package_dir); f = files(d, stage, slot)
    if not f['seal'].is_file():fail(f'{f["seal"].name} is missing: stage {stage} slot {slot} is not sealed')
    s = json.loads(f['seal'].read_text(encoding='utf-8'))
    if s.get('version') != SEAL_V2 or s.get('stage') != stage or s.get('slot') != slot or s.get('statement') != SEAL_STATEMENT:fail(f'{f["seal"].name}: not a {SEAL_V2} seal')
    if s['manifest_sha256'] != load_package(d)[1]:fail(f'{f["seal"].name}: sealed against a different package')
    if not f['answer'].is_file() or P.sha256(f['answer']) != s['answer']['sha256']:fail(f'{f["seal"].name}: the sealed answer changed or is missing')
    return s


def write_cross_inputs(package_dir, out_dir):
    """After both primary seals: the two frozen answers as auditors receive them (model answers only; provenance withheld)."""
    d = Path(package_dir); data = {s: cross_input_bytes(d, s) for s in SLOTS}; out = Path(out_dir); out.mkdir(parents=True, exist_ok=False)
    for s, b in data.items():
        with (out / f'review_{s}.json').open('xb') as f:f.write(b)
    return sorted(p.name for p in out.iterdir())


# -- prompt-injection dispositions ------------------------------------------------------------------
def record_dispositions(package_dir, decisions, by, now=None):
    """A named human's once-only disposition of the package's integrity flags, made before any primary answer is revealed.
    ``decisions``: {flag id: (disposition, note)}. Evidence and items are never changed."""
    human(by, 'an injection disposition'); d = Path(package_dir); pkg, msha = load_package(d); ids = {f['id'] for f in pkg['integrity_flags']}
    for k, (disp, note) in decisions.items():
        if k not in ids:fail(f'{k} is not an integrity flag of this package')
        if disp not in DISPOSITIONS:fail(f'disposition is one of {DISPOSITIONS}')
        if not isinstance(note, str) or not note.strip():fail(f'flag {k}: a disposition states its reason')
    doc = {'version': DISPOSITION_V1, 'manifest_sha256': msha, 'dispositions': {k: {'disposition': v[0], 'note': v[1]} for k, v in sorted(decisions.items())},
           'recorded_by': by, 'recorded_at_utc': P.utc(now).isoformat(), 'statement': DISPOSITION_STATEMENT}
    try:P.write_new(d / DISPOSITION_FILE, doc)
    except FileExistsError as error:raise P.PilotError('injection dispositions are already recorded; the record is immutable') from error
    return doc


def injection_status(package_dir, pkg, msha):
    """``CLEAR`` (no flag), ``DISPOSED`` (every flag disposed as harmless or not an instruction), else ``UNRESOLVED`` or
    ``CONFIRMED`` with the flags concerned. Detection is by pattern only and never complete."""
    flags = pkg['integrity_flags']
    if not flags:return {'status': 'CLEAR', 'flags': []}
    f = Path(package_dir) / DISPOSITION_FILE
    doc = json.loads(f.read_text(encoding='utf-8')) if f.is_file() else None
    if doc and (doc.get('version'), doc.get('manifest_sha256'), doc.get('statement')) != (DISPOSITION_V1, msha, DISPOSITION_STATEMENT):doc = None
    disp = (doc or {}).get('dispositions', {}); rows = []
    for x in flags:
        rows.append({**x, 'disposition': disp.get(x['id'], {}).get('disposition', 'NOT_DISPOSED')})
    if any(r['disposition'] == 'INSTRUCTION_ATTEMPT_CONFIRMED' for r in rows):status = 'CONFIRMED'
    elif any(r['disposition'] in ('UNRESOLVED', 'NOT_DISPOSED') for r in rows):status = 'UNRESOLVED'
    else:status = 'DISPOSED'
    return {'status': status, 'flags': rows}


# -- order ------------------------------------------------------------------------------------------
def stage_order(package_dir):
    """VERIFIED when each answer first appears strictly after the other slot's seal for its stage, each cross-review strictly
    after both primary answers and any injection disposition strictly before both primary answers; else NOT_COMMITTED or
    VIOLATED (with the reason). Each first commit must hold the current bytes."""
    d = Path(package_dir).resolve(); top = AD.git(d, 'rev-parse', '--show-toplevel')
    if top.returncode != 0:return {'status': 'NOT_COMMITTED', 'detail': 'package is not in a git repository'}
    root = Path(top.stdout.strip()); first = {}
    paths = [((stage, s, k), p) for stage in STAGES for s in SLOTS for k, p in files(d, stage, s).items() if k != 'bundle']
    if (d / DISPOSITION_FILE).is_file():paths.append((('disposition',), d / DISPOSITION_FILE))
    for key, p in paths:
        if not p.is_file():return {'status': 'NOT_COMMITTED', 'detail': f'{p.name} is missing'}
        c, state = AD.content_first_commit(root, p.resolve().relative_to(root).as_posix(), p)
        if state != 'OK':return {'status': 'VIOLATED' if state == 'CHANGED' else 'NOT_COMMITTED', 'detail': f'{p.name}: {state}'}
        first[key] = c
    after = lambda earlier, later: earlier != later and AD.git(root, 'merge-base', '--is-ancestor', earlier, later).returncode == 0
    for stage in STAGES:
        for s, other in (('A', 'B'), ('B', 'A')):
            if not after(first[(stage, other, 'seal')], first[(stage, s, 'answer')]):
                return {'status': 'VIOLATED', 'detail': f'{stage} answer {s} was not committed strictly after the {other} seal'}
    for s in SLOTS:
        for p in SLOTS:
            if not after(first[('primary', p, 'answer')], first[('cross', s, 'answer')]):
                return {'status': 'VIOLATED', 'detail': f'cross-review {s} was not committed strictly after primary answer {p}'}
        if ('disposition',) in first and not after(first[('disposition',)], first[('primary', s, 'answer')]):
            return {'status': 'VIOLATED', 'detail': f'the injection disposition was not committed strictly before primary answer {s}'}
    return {'status': 'VERIFIED', 'detail': 'dispositions before answers; answers revealed only after both seals; cross-reviews only after both primary answers'}


# -- reconciliation ---------------------------------------------------------------------------------
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


def unknown(value):
    return not isinstance(value, str) or value.strip().upper() in ('', 'UNKNOWN')


def identities(prim, cross):
    """Each slot's primary identity (product, model identifier) and whether its cross-review was run by the same model."""
    out = {}
    for s in SLOTS:
        p = prim[s]['provenance']; c = cross[s]['provenance'] if s in cross else None
        out[s] = {'primary': {'product': p['product'], 'model_identifier': p['model_identifier']},
                  'cross': {'product': c['product'], 'model_identifier': c['model_identifier']} if c else None,
                  'binding': 'UNAVAILABLE' if c is None else ('MATCHED' if (c['product'].strip(), c['model_identifier'].strip()) ==
                                                              (p['product'].strip(), p['model_identifier'].strip()) else 'MISMATCHED'),
                  'basis': 'OPERATOR_ATTESTATION (not provider-corroborated)'}
    return out


def nonconformance(order, cross, prim, pkg, ids, distinct, injection):
    """Every reason the package result is not a conforming AI-adjudicated result; empty only when all conditions hold."""
    reasons = [] if order['status'] == 'VERIFIED' else [f"STAGE_ORDER_{order['status']}"]
    for s in SLOTS:
        if s not in cross:reasons.append(f'CROSS_REVIEW_{s}_UNAVAILABLE')
        for stage, v in (('PRIMARY', prim[s]), ('CROSS', cross.get(s))):
            if v is None:continue
            p = v['provenance']
            if unknown(p['model_identifier']) or unknown(p['product']):reasons.append(f'MODEL_IDENTITY_UNKNOWN_{stage}_{s}')
            if v['external_access']:reasons.append(f'EXTERNAL_ACCESS_{stage}_{s}')
            if v['raw']['status'] != 'VERIFIED':reasons.append(f"RAW_OUTPUT_{v['raw']['status']}_{stage}_{s}")
            if v['raw']['attempts'] == 'CONFLICTING':reasons.append(f'RAW_ATTEMPTS_CONFLICTING_{stage}_{s}')
            if v['bundle']['status'] != 'VERIFIED':reasons.append(f"INPUT_BUNDLE_{v['bundle']['status']}_{stage}_{s}")
            if p['provenance_class'] == 'SYNTHETIC_FIXTURE' and pkg.get('fixture') != 'SYNTHETIC':reasons.append(f'SYNTHETIC_PROVENANCE_IN_LIVE_PACKAGE_{stage}_{s}')
        if ids[s]['binding'] == 'MISMATCHED':reasons.append(f'CROSS_IDENTITY_MISMATCH_{s}')
    if not distinct:reasons.append('MODEL_IDENTITY_NOT_DISTINCT')
    if len({prim[s]['bundle']['supplied_digest'] for s in SLOTS}) != 1:reasons.append('PRIMARY_BUNDLES_DIFFER')
    if any(e['file'] == 'MISSING_FROM_PACKAGE' for e in pkg['evidence'].values()):reasons.append('EVIDENCE_MISSING_FROM_PACKAGE')
    if injection['status'] in ('UNRESOLVED', 'CONFIRMED'):reasons.append(f"PROMPT_INJECTION_{injection['status']}")
    return reasons


def join_support(item):
    """What the export itself declares about the identity and period join (dimension 2). The AI review does not check it."""
    ss = item.get('shared_structure', {})
    dated = all(item[end].get('occurred') or item[end].get('period') for end in ('from', 'to'))
    return {'basis': [k for k in ('shared_document_hashes', 'same_identified_entity') if ss.get(k)],
            'name_or_ticker_only': bool(ss.get('name_or_ticker_only_entities')), 'period': 'BOTH_ENDS_DATED' if dated else 'NOT_BOTH_ENDS_DATED',
            'status': 'DECLARED_BY_EXPORT_NOT_CHECKED_BY_AI_REVIEW'}


def reconcile(package_dir, raw_store=None):
    """Stage C: deterministic item-level reconciliation of two sealed answers, with sealed cross-review findings attached.

    Item labels, the six assessment dimensions and ``diagnostic_counts`` are always reported. ``conforming_counts`` (the
    only counts that may enter any scientific comparison) and item ``ai_audit_supported`` require a conforming package
    (every condition in ``nonconformance``); otherwise they are withheld, with every reason listed. Without ``raw_store``
    the raw responses cannot be verified, so the result is never conforming."""
    d = Path(package_dir); pkg, msha = load_package(d)
    seals = {s: load_seal(d, 'primary', s) for s in SLOTS}
    prim = {s: validate_primary(d, files(d, 'primary', s)['answer'], raw_store) for s in SLOTS}
    cross, notes = {}, []
    for s in SLOTS:
        try:load_seal(d, 'cross', s); cross[s] = validate_cross(d, files(d, 'cross', s)['answer'], prim, raw_store)
        except P.PilotError as error:notes.append(f'cross-review {s} unavailable: {error}')
    ids = identities(prim, cross)
    distinct = prim['A']['provenance']['model_identifier'].strip().casefold() != prim['B']['provenance']['model_identifier'].strip().casefold()
    if not distinct:notes.append('Both primary answers name the same model identifier: they are not independent reviews.')
    for s in SLOTS:
        if prim[s]['external_access']:notes.append(f'Primary {s} had or declared access outside the package: its answers are potentially unblinded (the repository is public).')
        if ids[s]['binding'] == 'MISMATCHED':notes.append(f'Cross-review {s} names a different model from primary {s}: {ids[s]["cross"]} versus {ids[s]["primary"]}.')
    injection = injection_status(d, pkg, msha); order = stage_order(d)
    reasons = nonconformance(order, cross, prim, pkg, ids, distinct, injection); conforming = not reasons
    synthetic = any(v['provenance']['provenance_class'] == 'SYNTHETIC_FIXTURE' for v in [*prim.values(), *cross.values()])
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
        complete = len(findings) == len(SLOTS)
        all_supported = complete and all(findings[a][side]['support_check'] == 'SUPPORTED' and not set(findings[a][side]['issues']) & set(SERIOUS_ISSUES)
                                         for a in SLOTS for side in SLOTS)
        files_present = all(pkg['evidence'][h]['file'] != 'MISSING_FROM_PACKAGE' for h in item_evidence(i))
        documented = economic and label == 'AI_AGREED_CONFIRMED' and meaning == 'AI_AGREED_MEANINGFUL'
        conditions = documented and all_supported and files_present
        support = ('NOT_APPLICABLE' if not economic else 'AI_UNRESOLVED_DISAGREEMENT' if label == 'AI_UNRESOLVED_DISAGREEMENT'
                   else 'AI_AGREED_SUPPORTED_WITH_EXACT_QUOTES' if label == 'AI_AGREED_CONFIRMED'
                   else 'AI_AGREED_CONTRADICTED_WITH_EXACT_QUOTES' if label == 'AI_AGREED_FALSE' else 'NOT_ESTABLISHED')
        assessment = {
            '1_file_and_quote_integrity': {'original_files': 'ALL_PRESENT' if files_present else 'MISSING', 'quotes_A': a_['verification'],
                                           'quotes_B': b_['verification'], 'both_character_exact': (a_['verification'], b_['verification']) == ('VERIFIED_EXACT',) * 2},
            '2_identity_and_period_join': join_support(i),
            '3_documentary_support': {'models': support, 'audits': 'ALL_FOUR_SUPPORTED' if all_supported else 'NOT_ALL_SUPPORTED' if complete else 'INCOMPLETE'},
            '4_model_agreement_on_economic_meaning': meaning if economic else 'NOT_APPLICABLE',
            '5_economic_mechanism_or_causal_inference': 'NOT_ASSESSED_BY_THIS_INSTRUMENT',
            '6_independent_real_world_validation': 'NONE'}
        rows.append({'blind_id': b, 'kind': i['kind'],
                     'A': {k: a_[k] for k in ('outcome', 'economic_meaning', 'usefulness', 'confidence', 'verification')},
                     'B': {k: b_[k] for k in ('outcome', 'economic_meaning', 'usefulness', 'confidence', 'verification')},
                     'ai_label': label, 'ai_meaning': meaning, 'assessment': assessment, 'ai_agreed_documented_connection': documented,
                     'cross_review': findings, 'cross_review_complete': complete,
                     'audit_supported_conditions': conditions, 'ai_audit_supported': conditions and conforming})
    count = lambda pred: sum(1 for r in rows if pred(r))
    econ = [r for r in rows if r['kind'] in AD.ECONOMIC_KINDS]
    diagnostic = {'items': len(rows), 'connection_items': len(econ), 'warning_items': len(rows) - len(econ),
                  'agreed_labels': count(lambda r: r['ai_label'].startswith('AI_AGREED_')),
                  'unresolved_disagreements': count(lambda r: r['ai_label'] == 'AI_UNRESOLVED_DISAGREEMENT'),
                  'quote_not_found': count(lambda r: 'NOT_FOUND' in (r['A']['verification'], r['B']['verification'])),
                  'normalised_match_only': count(lambda r: 'NORMALISED_ONLY' in (r['A']['verification'], r['B']['verification'])),
                  'ai_agreed_documented_connections': count(lambda r: r['ai_agreed_documented_connection']),
                  'audit_supported_conditions_met': count(lambda r: r['audit_supported_conditions'])}
    scientific = {'ai_agreed_documented_connections': diagnostic['ai_agreed_documented_connections'],
                  'ai_audit_supported_connections': count(lambda r: r['ai_audit_supported'])} if conforming else None
    stage_docs = {'primary': prim, 'cross': cross}
    return {'version': RECONCILIATION_V2, 'banner': BANNER, 'synthetic_banner': SYNTHETIC_BANNER if synthetic else None,
            'evidence_class': 'SYNTHETIC_FIXTURE_ANSWERS' if synthetic else 'REAL_MODEL_RUN_ANSWERS', 'package_fixture': pkg.get('fixture'),
            'interpretation': INTERPRETATION, 'packet': pkg['packet'], 'manifest_sha256': msha,
            'reviewers': {s: {k: prim[s]['provenance'][k] for k in ('product', 'model_identifier', 'mode', 'run_by', 'provenance_class')}
                          | {'external_access': prim[s]['external_access'], 'sealed_at_utc': seals[s]['sealed_at_utc']} for s in SLOTS},
            'reviewers_distinct': distinct, 'identities': ids, 'stage_order': order,
            'raw_provenance': {st: {s: v['raw'] for s, v in docs.items()} for st, docs in stage_docs.items()},
            'input_bundles': {st: {s: {k: v['bundle'][k] for k in ('status', 'differences')} for s, v in docs.items()} for st, docs in stage_docs.items()},
            'integrity': {'injection': injection, 'unscanned_evidence': pkg['unscanned_evidence'],
                          'model_integrity_notes': {f'{st}_{s}': v['declaration']['integrity_notes'] for st, docs in stage_docs.items()
                                                    for s, v in docs.items() if v['declaration']['integrity_notes'].strip()}},
            'conforming': conforming, 'nonconformance': reasons,
            'diagnostic_counts': diagnostic, 'conforming_counts': scientific,
            'label_versions': {'ai_verified_economic_connection (V1)': 'ai_agreed_documented_connection (V2): same conditions, renamed',
                               'robust (V1)': 'ai_audit_supported (V2): stricter; both auditors find both answers SUPPORTED'},
            'items': rows, 'notes': notes}


def markdown(rec):
    L = [f"# AI review reconciliation: packet {rec['packet']}", '', f"> **{rec['banner']}**", '']
    if rec['synthetic_banner']:L += [f"> **{rec['synthetic_banner']}**", '']
    L += [f"> {rec['interpretation']}", '',
          f"Stage order: **{rec['stage_order']['status']}** ({rec['stage_order']['detail']}). Reviewers distinct: **{rec['reviewers_distinct']}**. "
          f"Prompt-injection flags: **{rec['integrity']['injection']['status']}**.", '',
          '| Slot | Product | Model identifier | Mode | External access | Cross-review identity | Raw primary / cross | Bundle primary / cross |',
          '|---|---|---|---|---|---|---|---|']
    raw, bun = rec['raw_provenance'], rec['input_bundles']
    for s, v in rec['reviewers'].items():
        L.append(f"| {s} | {v['product']} | `{v['model_identifier']}` | {v['mode']} | {v['external_access']} | {rec['identities'][s]['binding']} | "
                 f"{raw['primary'][s]['status']} / {raw['cross'].get(s, {}).get('status', '-')} | "
                 f"{bun['primary'][s]['status']} / {bun['cross'].get(s, {}).get('status', '-')} |")
    L += ['', f"Conforming: **{rec['conforming']}**" + (f" (withheld: {', '.join(rec['nonconformance'])})" if rec['nonconformance'] else ''), '']
    L += ['| Diagnostic count | Value |', '|---|---|'] + [f'| {k} | {v} |' for k, v in rec['diagnostic_counts'].items()]
    L += ['', '| Conforming count | Value |', '|---|---|'] + ([f'| {k} | {v} |' for k, v in rec['conforming_counts'].items()] if rec['conforming_counts']
                                                           else ['| (withheld) | not a conforming result |'])
    L += ['', '| Item | Kind | A | B | AI label | Meaning | Quotes A/B | Audits | Audit-supported |', '|---|---|---|---|---|---|---|---|---|']
    for r in rec['items']:
        lab = lambda x: x['outcome'] or x['usefulness']
        L.append(f"| `{r['blind_id']}` | {r['kind']} | {lab(r['A'])} ({r['A']['confidence']}) | {lab(r['B'])} ({r['B']['confidence']}) | {r['ai_label']} | "
                 f"{r['ai_meaning'] or ''} | {r['A']['verification']}/{r['B']['verification']} | {r['assessment']['3_documentary_support']['audits']} | {r['ai_audit_supported']} |")
    if rec['notes']:L += ['', '**Notes**', ''] + [f'- {n}' for n in rec['notes']]
    L += ['', 'Confidence is shown for information only and plays no part in any label. Cross-review findings never change a label. '
          'Identity and period joins, economic mechanism and real-world validation are not established by this instrument.']
    return '\n'.join(L) + '\n'
