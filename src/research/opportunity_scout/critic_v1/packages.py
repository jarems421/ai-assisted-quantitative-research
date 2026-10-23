"""Blinded review inputs, critic requests and a write-once workspace; raw answers stored by hash, never repaired.

A critic input contains the card (whitespace-normalised, seed identifiers replaced by passage aliases), its supplied
passages, and a frozen reference set of other cards and historical memory for internal novelty. It never contains the
lane, the generator, provenance, Layer A findings, routing, or another critic's output. The operator-side manifest keeps
those for the policy and the evaluation. Each request is answered at most once validly (at most two attempts, the second
only after an unusable first), so a different answer cannot be shopped for."""
from __future__ import annotations

from contextlib import contextmanager
import copy
from difflib import SequenceMatcher
import hashlib
import os

from src.research.spec import canonical, digest
from .. import engine as E, schema as S
from ..post_generation.review import ASSISTANT
from ..storage import ROOT, unlinked
from . import deterministic as D, rubric as K

WORKSPACE_V, ATTEMPT_V = 'SCOUT_CRITIC_WORKSPACE_V001', 'SCOUT_CRITIC_ATTEMPT_V001'
PROVIDERS = ('OPERATOR_ASSISTED', 'LOCAL_MODEL', 'SYNTHETIC_FIXTURE')
SPLITS = ('TUNING', 'HOLDOUT')
MAX_ATTEMPTS, MAX_REFERENCES, MAX_PASSAGE, MAX_RAW, MAX_JSON = 2, 30, 8000, 1024 * 1024, 16 * 1024 * 1024
REFERENCE_SCOPE = 'Internal Research OS cards and historical memory supplied here only; not a literature, market or private-use search.'
def neutral_padding(idea):
    """Irrelevant context only: a substantive judgment should not change."""
    return {**idea, 'main_uncertainty': idea['main_uncertainty'][:3900] + ' This card uses the standard review format.'}


def confident_framing(idea):
    """Unsupported confidence only: no judgment should improve."""
    hypothesis = idea['overlooked_hypothesis']
    return {**idea, 'overlooked_hypothesis': {**hypothesis, 'statement': 'It is highly likely and important that ' + hypothesis['statement'][:3900]}}


VARIANTS = {'NEUTRAL_PADDING': neutral_padding, 'CONFIDENT_FRAMING': confident_framing}  # metamorphic stability probes


def subjects_from(states):
    """Every current card in ``states`` ({archive name: State}) as (subject, operator-side metadata), by subject key."""
    if not states:raise S.ScoutError('at least one archive is required')
    fixtures = {s.batch['fixture'] for s in states.values()}
    if len(fixtures) != 1:raise S.ScoutError('synthetic and exploratory archives cannot share a critic workspace')
    out = {}
    for name, state in sorted(states.items()):
        for versions in state.cards.values():
            card = versions[-1]
            key = 'SUBJ-' + digest([name, card['id'], card['version']])[:16]
            out[key] = ({'id': card['id'], 'idea': card['idea'], 'lane': card['lane'], 'seeds': dict(state.seeds),
                         'memory': state.batch['memory']['investigations'], 'knowledge_cutoff': card['knowledge_cutoff']},
                        {'archive': name, 'idea_id': card['id'], 'version': card['version'], 'card_sha256': digest(card),
                         'lane': card['lane'], 'generator_model': card['provenance']['model'],
                         'family': card['idea']['mechanism']['family'], 'sector': card['idea']['sector'],
                         'analyst_minutes_estimate': card['idea']['next_step']['analyst_minutes_estimate']})
    return fixtures.pop(), out


def reference_items(subject, references):
    me = {'idea': subject['idea']}
    rows = sorted((r for r in references if r['id'] != subject['id']),
                  key=lambda r: (-round(SequenceMatcher(None, E.normal_text(me), E.normal_text(r)).ratio(), 6), digest(E.core(r['idea']))))
    items, ids = [], {}
    for n, r in enumerate(rows[:MAX_REFERENCES], 1):
        m, i = r['idea']['mechanism'], r['idea']
        ids[f'REF-{n:02d}'] = {'idea_id': r['id'], 'version': r['version']}
        items.append({'ref_id': f'REF-{n:02d}', 'family': m['family'], 'transformation': m['transformation'], 'economic_role': i['economic_role'],
                      'sector': i['sector'], **{k: m[k] for k in ('trigger', 'operational_effect', 'transmission', 'affected_party', 'consequence')},
                      'predictor': i['predictor']['quantity'], 'outcome': i['outcome']['quantity']})
    return items, ids


def blind_input(subject, references):
    """(critic input, operator-side reference-id map). Deterministic for the same card, passages and references."""
    idea, seeds = subject['idea'], subject['seeds']
    declared = sorted(idea['seed_ids'], key=lambda s: (seeds[s]['sha256'], s))
    alias = {sid: f'P{n:02d}' for n, sid in enumerate(declared, 1)}
    card = {k: copy.deepcopy(v) for k, v in idea.items() if k != 'seed_ids'}
    for part in card['mechanism']['links'] + card['source_routes']:
        part['evidence'] = [{'passage': alias.get(r['seed'], 'NOT_SUPPLIED'), 'quote': r['quote']} for r in part['evidence']]
    passages = [{'passage_id': alias[s], 'publisher': seeds[s]['publisher'], 'source_version': seeds[s]['version'], 'depth': seeds[s]['depth'],
                 'evidence_kind': seeds[s]['evidence_kind'], 'access': seeds[s]['access'],
                 'first_public': seeds[s]['clocks']['first_public']['value'], 'limitations': seeds[s]['limitations'],
                 'text': seeds[s]['text'][:MAX_PASSAGE], 'truncated': len(seeds[s]['text']) > MAX_PASSAGE} for s in declared]
    items, ids = reference_items(subject, references)
    history = [{'ref_id': f'HIST-{n:02d}', 'title': v.get('title', ''), 'verdict': v.get('verdict', ''), 'requirements': sorted(v.get('requirements', []))}
               for n, v in enumerate((subject['memory'][k] for k in sorted(subject['memory'])), 1)]
    payload = K.clean({'schema': K.INPUT_V, 'card': card, 'source_passages': passages,
                       'reference_set': {'scope': REFERENCE_SCOPE, 'items': items, 'historical': history}})
    return payload, ids


def make_request(critic, subject_key, payload, selection=None):
    body = {'schema': K.REQUEST_V, 'critic': critic, 'subject_key': subject_key, 'input': payload, 'input_sha256': digest(payload),
            'prompt_sha256': S.hash_text(K.prompt_text(critic)), 'resources_sha256': digest(K.resource_manifest()),
            'rendered_prompt_sha256': S.hash_text(K.render(critic, payload)), 'extraction_rule': K.EXTRACTION,
            'selection': selection, 'model_calls_made': 0, 'authorises': []}
    return {**body, 'request_id': 'CRQ-' + digest(body)[:16]}


def check_request(request):
    body = {k: v for k, v in request.items() if k != 'request_id'}
    if request.get('schema') != K.REQUEST_V or request['request_id'] != 'CRQ-' + digest(body)[:16] or request['input_sha256'] != digest(request['input']):
        raise S.ScoutError('critic request changed after it was frozen')
    if request['prompt_sha256'] != S.hash_text(K.prompt_text(request['critic'])) or request['rendered_prompt_sha256'] != S.hash_text(K.render(request['critic'], request['input'])):
        raise S.ScoutError('critic request was frozen under different critic texts: a new version needs a new workspace')
    return request


def guarded(path):
    p = unlinked(path)
    if any(x.name.startswith('.claude') for x in (p, *p.parents)):raise S.ScoutError('account directories cannot hold critic workspaces')
    nearest = next((x for x in (p, *p.parents) if (x / '.git').exists()), None)
    if nearest is not None and nearest.resolve() != ROOT:raise S.ScoutError('other repository or worktree writes are refused')
    if p.resolve().is_relative_to(ROOT):
        rel = p.resolve().relative_to(ROOT).parts
        if len(rel) < 3 or rel[:2] != ('.research', 'opportunity_scout') or not rel[2].startswith('critic-v1-'):
            raise S.ScoutError('inside the repository a critic workspace lives in .research/opportunity_scout/critic-v1-*')
    return p


class Workspace:
    """Write-once files: manifest, requests, raw answers by hash, attempt records, recommendations, queues."""
    def __init__(self, path):self.path, self._manifest = guarded(path), None

    def write(self, rel, value):
        target = unlinked(self.path / rel); target.parent.mkdir(parents=True, exist_ok=True)
        data = value if isinstance(value, bytes) else canonical(value) + b'\n'
        with target.open('xb') as handle:handle.write(data); handle.flush(); os.fsync(handle.fileno())
        return target

    def read(self, rel):
        p = unlinked(self.path / rel)
        if not p.is_file() or p.stat().st_size > MAX_JSON:raise S.ScoutError(f'missing or oversized workspace file: {rel}')
        return S.json_loads(p.read_bytes().decode('utf-8'))

    def files(self, folder, pattern='*.json'):
        d = unlinked(self.path / folder)
        return sorted(p.relative_to(self.path).as_posix() for p in d.glob(pattern)) if d.is_dir() else []

    @contextmanager
    def locked(self):
        lock = unlinked(self.path / '.write.lock')
        try:fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:raise S.ScoutError('workspace locked; do not remove another writer\'s lock') from error
        try:yield
        finally:os.close(fd); lock.unlink()

    def manifest(self):
        if self._manifest is None:  # write-once, so one read per instance
            m = self.read('manifest.json')
            if m.get('schema') != WORKSPACE_V:raise S.ScoutError('not a critic V001 workspace')
            self._manifest = m
        return self._manifest  # callers never mutate it

    def request(self, request_id):
        if not isinstance(request_id, str) or not request_id.startswith('CRQ-') or not request_id[4:].isalnum():raise S.ScoutError('unknown request id')
        r = check_request(self.read(f'requests/{request_id}.json'))
        if r['subject_key'] not in self.manifest()['subjects']:raise S.ScoutError('request names an unknown subject')
        return r

    def requests(self):
        return [self.request(f.split('/')[-1][:-5]) for f in self.files('requests')]

    def raw(self, sha):
        p = unlinked(self.path / 'raw' / f'{sha}.bin'); data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha:raise S.ScoutError('stored raw answer no longer matches its hash')
        return data

    def attempts(self):
        """Every attempt record, re-derived from its raw bytes and provenance: a record that no longer follows is refused."""
        out = []
        for f in self.files('attempts'):
            a = self.read(f); req = self.request(a['request_id'])
            refused = refusals(self.manifest()['subjects'][req['subject_key']], req, a['provenance'])
            if (a['request_id'], a['critic'], a['subject_key']) != (req['request_id'], req['critic'], req['subject_key']) or a['refusals'] != refused \
                    or (a['status'], a['problems'], a['output']) != judge(req, self.raw(a['raw_sha256']), refused):
                raise S.ScoutError(f'{f} does not follow from its stored raw answer and provenance')
            out.append(a)
        return out


def prepare(states, out, *, split, variants=(), now=None):
    """Freeze Layer A, blinded inputs and first-pass requests for every current card. No model is called."""
    if split not in SPLITS:raise S.ScoutError('declare the split: TUNING (prompts may change) or HOLDOUT (evaluation only)')
    if any(v not in VARIANTS for v in variants):raise S.ScoutError(f'variants are {sorted(VARIANTS)}')
    fixture, subjects = subjects_from(states)
    ws = Workspace(out)
    if ws.path.exists() and any(ws.path.iterdir()):raise S.ScoutError('a critic workspace needs a new empty directory')
    references = [{'id': m['idea_id'], 'version': m['version'], 'idea': s['idea']} for s, m in subjects.values()]
    entries, requests = {}, []
    for key, (subject, meta) in sorted(subjects.items()):
        rows = [(key, subject, {**meta, 'variant_of': None, 'variant': None})]
        for name in variants:
            rows.append((key + '-' + name, {**subject, 'idea': VARIANTS[name](subject['idea'])}, {**meta, 'variant_of': key, 'variant': name}))
        for k, s, m in rows:
            layer_a = D.check(s, references)
            entry = {**m, 'layer_a': layer_a, 'requests': {}, 'reference_ids': {}, 'input_sha256': None}
            if layer_a['reviewable']:
                payload, ids = blind_input(s, references)
                entry.update(input_sha256=digest(payload), reference_ids=ids)
                for critic in K.FIRST_PASS:
                    r = make_request(critic, k, payload); requests.append(r); entry['requests'][critic] = r['request_id']
            entries[k] = entry
    for r in requests:
        ws.write(f'requests/{r["request_id"]}.json', r); ws.write(f'requests/{r["request_id"]}.md', K.render(r['critic'], r['input']).encode('utf-8'))
    manifest = {'schema': WORKSPACE_V, 'version': K.VERSION, 'fixture': fixture, 'split': split, 'subjects': entries,
                'resources_sha256': digest(K.resource_manifest()), 'variants': list(variants),
                'archive_heads': {n: (s.events[-1]['hash'] if s.events else None) for n, s in sorted(states.items())},
                'created_at': now or S.utc_now(), 'model_calls_made': 0, 'routing_authority': 'NONE', 'authorises': []}
    ws.write('manifest.json', manifest)
    return ws, manifest


def refusals(subject, request, prov):
    """Independence refusals, derived from the operator-side manifest and the attested provenance."""
    out = []
    if prov['model'].casefold() == subject['generator_model'].casefold():out.append('the generator model cannot review its own card')
    if prov['saw_other_critic_outputs'] and request['critic'] in K.FIRST_PASS:out.append('a first-pass review must not have seen another critic output')
    return out


def judge(request, raw, refusals):
    """(status, problems, output) for raw answer bytes. The same function decides at import and on every reload."""
    status, output = K.extract(raw)
    problems = [] if status == 'EXTRACTED' else [f'extraction {K.EXTRACTION}: {status}']
    if output is not None:problems += K.problems(output, request)
    return ('REFUSED' if refusals else 'INVALID' if problems else 'VALID'), problems, output


def provenance(model, model_family, provider, operator, *, fresh_context='UNKNOWN', saw_other_critic_outputs=False,
               received_at=S.UNKNOWN, input_tokens=S.UNKNOWN, output_tokens=S.UNKNOWN, cost=S.UNKNOWN, currency=S.UNKNOWN, latency_ms=S.UNKNOWN):
    record = {'model': model, 'model_family': model_family, 'provider': provider, 'operator': operator, 'fresh_context': fresh_context,
              'saw_other_critic_outputs': saw_other_critic_outputs, 'received_at': received_at,
              'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'cost': cost, 'currency': currency, 'latency_ms': latency_ms}}
    S.validate(S.obj({'model': S.LABEL, 'model_family': S.LABEL, 'provider': S.enum(PROVIDERS), 'operator': S.LABEL,
                      'fresh_context': S.enum(('YES', 'NO', 'UNKNOWN')), 'saw_other_critic_outputs': {'type': 'boolean'}, 'received_at': S.TEXT,
                      'usage': S.obj({'input_tokens': S.NUMBER, 'output_tokens': S.NUMBER, 'cost': S.NUMBER,
                                      'currency': S.enum(('USD', S.UNKNOWN)), 'latency_ms': S.NUMBER})}), record, 'critic provenance')
    if ASSISTANT.search(operator):raise S.ScoutError('the operator attesting a raw answer is a named human, not an assistant or model')
    if received_at != S.UNKNOWN:S.timestamp(received_at)
    return record


def import_response(ws, request_id, raw, prov, *, now=None):
    """Store raw answer bytes unchanged and append one attempt record. Invalid and refused attempts are kept."""
    manifest, req = ws.manifest(), ws.request(request_id)
    subject = manifest['subjects'][req['subject_key']]
    if (manifest['fixture'] == 'SYNTHETIC') != (prov['provider'] == 'SYNTHETIC_FIXTURE'):
        raise S.ScoutError('synthetic fixture answers and real model answers cannot share a workspace')
    if not isinstance(raw, bytes) or len(raw) > MAX_RAW:raise S.ScoutError('raw answer must be at most 1 MiB of bytes')
    refused = refusals(subject, req, prov)
    with ws.locked():
        previous = [a for a in ws.attempts() if a['request_id'] == request_id]
        if any(a['status'] == 'VALID' for a in previous):raise S.ScoutError('this request already has a valid answer; it is never re-run for a different one')
        if len(previous) >= MAX_ATTEMPTS:raise S.ScoutError(f'attempt ceiling reached ({MAX_ATTEMPTS}); the request stays unanswered')
        sha = hashlib.sha256(raw).hexdigest()
        if not (ws.path / 'raw' / f'{sha}.bin').exists():ws.write(f'raw/{sha}.bin', raw)
        status, problems, output = judge(req, raw, refused)
        seq = len(ws.files('attempts')) + 1
        record = {'schema': ATTEMPT_V, 'attempt': f'ATT-{seq:04d}', 'request_id': request_id, 'critic': req['critic'],
                  'subject_key': req['subject_key'], 'raw_sha256': sha, 'raw_bytes': len(raw), 'status': status, 'problems': problems,
                  'refusals': refused, 'output': output, 'provenance': prov, 'imported_at': now or S.utc_now(),
                  'basis': 'OPERATOR_ATTESTATION', 'provider_verified': False, 'routing_authority': 'NONE'}
        ws.write(f'attempts/ATT-{seq:04d}.json', record)
    return record


def usable(ws):
    """{subject key: {critic: earliest VALID attempt}} and every request's attempt history."""
    by_request = {}
    for a in ws.attempts():by_request.setdefault(a['request_id'], []).append(a)
    chosen = {}
    for r in ws.requests():
        valid = [a for a in by_request.get(r['request_id'], []) if a['status'] == 'VALID']
        if valid:chosen.setdefault(r['subject_key'], {})[r['critic']] = valid[0]
    return chosen, by_request
