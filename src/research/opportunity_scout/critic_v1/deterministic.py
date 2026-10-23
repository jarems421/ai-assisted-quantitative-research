"""Layer A: deterministic validation. Reuses the frozen Scout checks and never reaches an economic conclusion.

Only INVALID_INPUT, STRUCTURAL_DEFECT and DOCUMENTED_CONTRADICTION findings are definitive, and each is verifiable from
the card and supplied passages alone. MISSING_EVIDENCE and UNKNOWN findings are information for the critics and humans:
they never count against a card, so a speculative card without source passages is not penalised for that absence."""
from __future__ import annotations

import re
from types import SimpleNamespace

from src.research.discovery import records as R
from .. import engine as E, schema as S

LAYER_A_V = 'SCOUT_CRITIC_DETERMINISTIC_V001'
CATEGORIES = ('INVALID_INPUT', 'STRUCTURAL_DEFECT', 'DOCUMENTED_CONTRADICTION', 'MISSING_EVIDENCE', 'UNKNOWN')
DEFINITIVE = CATEGORIES[:3]
STRUCTURAL = {  # existing structural_checks code -> card field
    'FALSIFIER_NEEDS_REVIEW': '/card/falsifier/observation', 'NEXT_QUESTION_NEEDS_REVIEW': '/card/next_step/question',
    'DISTINCTIVE_PREDICTOR_NEEDS_REVIEW': '/card/predictor/distinctiveness', 'UNFALSIFIABLE_LANGUAGE': '/card/falsifier/observation',
    'PREDICTOR_REPEATED_AS_OUTCOME': '/card/outcome/quantity',
    'UNSUPPORTED_INFORMATION_ADVANTAGE_LANGUAGE': '/card/overlooked_hypothesis/statement'}
CERTAINTY = re.compile(r'\b(?:certainly|definitely|undoubtedly|will always|cannot fail|beyond (?:any )?doubt|inevitabl[ey])\b', re.I)
_W = r'(?:all |any |the |your |these |those |previous |prior |above )*'
INJECTION = (  # matched on cleaned text; the text is flagged, never removed
    # Not "rules": "operators ignore the rules" is an ordinary economic mechanism, not an instruction to the critic.
    ('OVERRIDE_INSTRUCTIONS', re.compile(r'\b(?:ignore|disregard|forget|override|bypass)\s' + _W + r'(?:instructions?|rubric|guidance|prompts?)\b', re.I)),
    ('DIRECT_JUDGMENT_REQUEST', re.compile(r'\b(?:mark|label|rate|score|classify|grade|judge|treat|assess)\s(?:this|the|these|each)\s'
                                          r'(?:card|hypothesis|idea|items?|answer)\s(?:as|with|at)\b|\b(?:assign|give)\s(?:it\s|this\s(?:card|idea)\s)?(?:a\s)?(?:perfect|maximum|top|high|full)\s(?:score|marks?|rating)\b', re.I)),
    ('ADDRESSES_THE_EVALUATOR', re.compile(r'\b(?:you are (?:now )?(?:an? )?(?:ai|language model|assistant|evaluator|critic|reviewer)|'
                                          r'(?:note|message|instructions?) (?:to|for) (?:the |any )?(?:ai|model|llm|reviewer|critic|evaluator)s?)\b', re.I)),
    ('ASSERTS_CORRECT_ANSWER', re.compile(r'\b(?:the )?correct (?:judgment|answer|verdict|rating|classification|score) (?:is|would be|should be)\b|'
                                         r'\b(?:evaluators?|reviewers?|critics?|models?)\s(?:should|must)\s(?:answer|mark|rate|output|return|pass|approve|accept)\b', re.I)),
    ('FORGED_INPUT_BOUNDARY', re.compile(r'<<<\s*(?:END_)?UNTRUSTED_INPUT|OUTPUT_SCHEMA', re.I)),
    ('ROLE_TAGS', re.compile(r'</?\s*(?:system|assistant|user|developer)\s*>|\[/?(?:INST|SYS)\]|<\|(?:im_start|im_end|system|assistant|user)\|>', re.I)))


def finding(code, category, field, detail, repair=''):
    return {'code': code, 'category': category, 'definitive': category in DEFINITIVE, 'field': field, 'detail': detail,
            'repair': repair, 'injection': code.startswith('INSTRUCTION_LIKE_TEXT')}


def strings(value, path=''):
    if isinstance(value, str):yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():yield from strings(v, f'{path}/{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):yield from strings(v, f'{path}/{i}')


def scan(path, text):
    clean = ' '.join(text.split())
    return [finding('INSTRUCTION_LIKE_TEXT_' + code, 'UNKNOWN', path, 'Evaluator-directed or role-tag text in untrusted data; flagged, never removed.',
                    'A human disposes of the flag before any AI recommendation is relied on.') for code, pattern in INJECTION if pattern.search(clean)]


def words(text):
    return set(re.findall(r'[a-z]+', text.casefold())) - {'the', 'a', 'an', 'of', 'in', 'at', 'to', 'and', 'or', 'for', 'per', 'on'}


def check(subject, references=()):
    """``subject``: {'id', 'idea', 'lane', 'seeds': {id: seed}, 'memory': {investigation id: record}, 'knowledge_cutoff'}.
    ``references``: other current cards ({'id', 'version', 'idea'}) for duplicate detection."""
    idea, lane, seeds, memory = subject['idea'], subject['lane'], subject['seeds'], subject['memory']
    out = []
    try:S.validate(S.IDEA, idea, 'idea')
    except S.ScoutError as error:return report([finding('SCHEMA_INVALID', 'INVALID_INPUT', '/card', str(error), 'Correct the card to the frozen idea schema.')], idea)
    for sid, seed in sorted(seeds.items()):
        try:S.validate_seed(seed)
        except S.ScoutError as error:out.append(finding('SEED_INVALID', 'INVALID_INPUT', f'/seeds/{sid}', str(error)))
    if idea['requirement']['id'] not in S.REQS or any(r not in S.REQS for r in idea['reconsider_when']['requirements']):
        out.append(finding('NONCANONICAL_REQUIREMENT', 'INVALID_INPUT', '/card/requirement/id', 'Requirement IDs must be canonical or REQ_OTHER.'))
    if lane == 'FORGE' and (idea['seed_ids'] or idea['historical_refs']):
        out.append(finding('FORGE_CLAIMS_UNSEEN_INPUTS', 'INVALID_INPUT', '/card', 'Forge is independent and cannot cite seeds or memory.'))
    if lane == 'RADAR' and not idea['seed_ids']:out.append(finding('RADAR_WITHOUT_SEED', 'INVALID_INPUT', '/card', 'Evidence Radar requires an approved seed.'))
    if lane == 'GAP' and not idea['historical_refs']:out.append(finding('GAP_WITHOUT_OBSTACLE', 'INVALID_INPUT', '/card', 'Gap Explorer requires a cited historical obstacle.'))
    if len(set(idea['seed_ids'])) != len(idea['seed_ids']) or any(s not in seeds for s in idea['seed_ids']):
        out.append(finding('UNKNOWN_SEED_REFERENCE', 'INVALID_INPUT', '/card', 'A declared seed is unknown or repeated.'))
    speculative, cited = 0, set()
    for i, link in enumerate(idea['mechanism']['links']):
        where = f'/card/mechanism/links/{i}'
        if (link['from'], link['to']) != (S.STAGES[i], S.STAGES[i + 1]):
            out.append(finding('BROKEN_STAGE_ORDER', 'STRUCTURAL_DEFECT', where, 'Links must run trigger, operations, transmission, party, consequence.', 'Restate the link in stage order.'))
        if link['basis'] == 'DOCUMENTED' and not link['evidence']:
            out.append(finding('DOCUMENTED_LINK_WITHOUT_CITATION', 'STRUCTURAL_DEFECT', where, 'A link labelled DOCUMENTED cites no passage.', 'Cite the exact passage or relabel the link UNVERIFIED.'))
        if link['basis'] != 'DOCUMENTED' and not link['evidence']:speculative += 1
        for ref in link['evidence']:
            cited.add(ref['seed'])
            try:S.check_ref(ref, seeds)
            except S.ScoutError:
                out.append(finding('FABRICATED_OR_INEXACT_CITATION', 'DOCUMENTED_CONTRADICTION', where, 'The cited passage does not occur in the supplied source.', 'Quote the source exactly or remove the citation.'))
                continue
            if ref['seed'] not in idea['seed_ids']:
                out.append(finding('CITATION_OUTSIDE_DECLARED_SEEDS', 'STRUCTURAL_DEFECT', where, 'Cited source is not among the declared seed inputs.', 'Declare the seed or remove the citation.'))
            if link['basis'] == 'DOCUMENTED':
                seed = seeds[ref['seed']]
                if S.seed_state(seed) == 'CONTRADICTED':
                    out.append(finding('CONTRADICTED_SOURCE_USED_AS_SUPPORT', 'DOCUMENTED_CONTRADICTION', where, 'The supplied observation records this source as contradicted.', 'Remove the support claim.'))
                elif seed['depth'] not in R.ORIGINAL or link['statement'] != ref['quote']:
                    out.append(finding('DOCUMENTED_BASIS_OVERCLAIMED', 'STRUCTURAL_DEFECT', where, 'A DOCUMENTED link needs an original-depth exact assertion; this one is metadata or a new inference.', 'Relabel the link INFERRED or UNVERIFIED.'))
    if speculative:
        out.append(finding('SPECULATIVE_LINKS', 'MISSING_EVIDENCE', '/card/mechanism/links', f'{speculative} of 4 links are declared speculation without a passage. Allowed; not a defect.'))
    if not idea['seed_ids']:out.append(finding('NO_SOURCE_PASSAGES', 'MISSING_EVIDENCE', '/source_passages', 'No supplied evidence. A speculative card is still reviewable.'))
    for ref in idea['historical_refs']:
        match = memory.get(ref['investigation'])
        if memory and (not match or ref['requirement'] not in match['requirements']):
            out.append(finding('UNKNOWN_HISTORICAL_MAPPING', 'INVALID_INPUT', '/card/historical_refs', 'Unknown historical investigation or requirement.'))
    for i, route in enumerate(idea['source_routes']):
        where = f'/card/source_routes/{i}'
        if route['state'] == 'DOCUMENTED_ROUTE' and not route['evidence']:
            out.append(finding('DOCUMENTED_ROUTE_WITHOUT_PASSAGE', 'STRUCTURAL_DEFECT', where, 'A documented route needs a source passage.', 'Cite it or mark the route UNTESTED.'))
        for ref in route['evidence']:
            cited.add(ref['seed'])
            try:S.check_ref(ref, seeds)
            except S.ScoutError:out.append(finding('FABRICATED_OR_INEXACT_CITATION', 'DOCUMENTED_CONTRADICTION', where, 'The cited route passage does not occur in the supplied source.', 'Quote exactly or remove.'))
        for seed in seeds.values():
            if seed['locator'] == route['locator'] and seed['access'] in ('STOPPED', 'INACCESSIBLE') and route['state'] != seed['access']:
                out.append(finding('REOPENED_SOURCE_STOP', 'DOCUMENTED_CONTRADICTION', where, 'A recorded source stop or denial is silently reopened.', 'Restore the recorded access state.'))
    for code in S.structural_checks(idea)['checks']:
        out.append(finding(code, 'STRUCTURAL_DEFECT', STRUCTURAL[code], 'Existing Scout structural check (blocks READY in the frozen engine).', 'Revise the named field.'))
    cutoff = S.timestamp(subject['knowledge_cutoff'])
    for sid in sorted(cited & set(seeds)):
        first = seeds[sid]['clocks']['first_public']
        if first['value'] == S.UNKNOWN:
            out.append(finding('CITED_SOURCE_PUBLIC_TIME_UNKNOWN', 'MISSING_EVIDENCE', f'/seeds/{sid}', 'First-public time of a cited source is unknown; timing is unverified, not wrong.'))
        elif S.timestamp(first['value']) > cutoff:
            out.append(finding('CITED_SOURCE_PUBLIC_AFTER_CUTOFF', 'DOCUMENTED_CONTRADICTION', f'/seeds/{sid}', 'The certified first-public time of a cited source is after the card knowledge cutoff.', 'Remove the source or move the hypothesis to a later cutoff.'))
    p, o = idea['predictor']['quantity'], idea['outcome']['quantity']
    a, b = words(p), words(o)
    if p.casefold() != o.casefold() and a and b and len(a & b) / len(a | b) >= .6:
        out.append(finding('POSSIBLE_PREDICTOR_OUTCOME_OVERLAP', 'UNKNOWN', '/card/outcome/quantity', 'Predictor and outcome share most of their wording; circularity needs judgment.'))
    if references:
        state = SimpleNamespace(cards={r['id']: [r] for r in references if r['id'] != subject['id']})
        for m in E.proximity(state, {'id': subject['id'], 'idea': idea}):
            if m['kind'] == 'EXACT_CORE_DUPLICATE':
                out.append(finding('EXACT_CORE_DUPLICATE', 'STRUCTURAL_DEFECT', '/card', f'Identical economic core to {m["idea_id"]} v{m["version"]}.', 'Merge with, or state the difference from, the earlier card.'))
            elif m['kind'] == 'POSSIBLE_MECHANISM_DUPLICATE':
                out.append(finding('POSSIBLE_MECHANISM_DUPLICATE', 'UNKNOWN', '/card/mechanism', f'Same mechanism family as {m["idea_id"]}, overlapping role or wording (similarity {m["text_similarity"]}).'))
    for path, text in strings(idea, '/card'):
        if path != '/card/overlooked_hypothesis/statement' and R.UNSUPPORTED_NOVELTY.search(text):
            out.append(finding('UNSUPPORTED_NOVELTY_OR_CERTAINTY_LANGUAGE', 'UNKNOWN', path, 'Language claiming an unshared advantage or guaranteed result.'))
        if CERTAINTY.search(text):out.append(finding('CERTAINTY_LANGUAGE', 'UNKNOWN', path, 'Certainty wording; checked against the declared evidence by the critics.'))
        out.extend(scan(path, text))
    for sid, seed in sorted(seeds.items()):
        out.extend(scan(f'/seeds/{sid}/text', seed['text']))
    try:S.validate_idea(idea, lane, seeds, memory)
    except S.ScoutError as error:
        if not any(f['definitive'] for f in out):out.append(finding('FROZEN_IMPORT_VALIDATION', 'INVALID_INPUT', '/card', str(error)))
    return report(out, idea)


def report(findings, idea):
    findings = sorted(findings, key=lambda f: (CATEGORIES.index(f['category']), f['field'], f['code']))
    counts = {c: sum(f['category'] == c for f in findings) for c in CATEGORIES}
    return {'schema': LAYER_A_V, 'reviewable': counts['INVALID_INPUT'] == 0, 'findings': findings, 'counts': counts,
            'definitive_failures': sum(f['definitive'] for f in findings), 'injection_flags': sum(f['injection'] for f in findings),
            'speculative': isinstance(idea, dict) and not idea.get('seed_ids'),
            'economic_conclusion': 'NONE', 'authority': 'NONE'}
