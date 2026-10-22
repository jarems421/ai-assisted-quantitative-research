"""Small end-to-end operations shared by the CLI and tests."""
from __future__ import annotations

from src.research.spec import canonical, digest
from . import schema as S
from . import engine as E
from .prompts import make_prompt
from .providers import UNKNOWN_USAGE

BASE = '5f3b7ef91cfca8e7d13661a577a67751165c65cd'


def empty_memory(moment):
    return {'schema': 'SCOUT_MEMORY_V001', 'catalogue_sha256': '0' * 64, 'recorded_at': moment,
            'graph_digest': '0' * 64, 'investigations': {}, 'same_gap': {}, 'mapping_review': 'NO_MEMORY_INCLUDED',
            'ledgers_read': [], 'creates_original_observations': False}


def initialise(archive, title, *, fixture='SCOUT_EXPLORATORY', with_memory=True, max_cards=24,
               max_attempts=9, cutoff=None, moment=None):
    moment = moment or S.utc_now()
    if with_memory:
        from .memory import snapshot
        memory = snapshot()
    else: memory = empty_memory(moment)
    record = {'id': 'SCOUT-' + digest({'title': title, 'created': moment})[:12], 'title': title,
        'fixture': fixture, 'base_commit': BASE, 'knowledge_cutoff': cutoff or moment,
        'max_cards': max_cards, 'max_attempts': max_attempts, 'max_output_tokens': 6000,
        'shortlist_slots': 4, 'policy': E.POLICY, 'memory': memory, 'acquisition_authorised': False}
    return archive.append('batch', record, recorded_at=moment)


def prepare(archive, lane, count, model, provider='OPERATOR_ASSISTED', *, moment=None):
    state = archive.load()
    pid = f'PROMPT-{len(state.prompts) + 1:04d}'
    prompt = make_prompt(state, lane, count, pid)
    aid = f'ATT-{len(state.attempts) + 1:04d}'
    start = {'id': aid, 'prompt_id': pid, 'requested_model': model, 'provider': provider,
             'started_at': moment or S.utc_now()}
    archive.append_many([('prompt', prompt), ('attempt_start', start)], recorded_at=moment)
    return aid, prompt


def finish(archive, attempt_id, raw, provider, *, raw_import='', error=None, moment=None):
    state = archive.load()
    attempt = state.attempts.get(attempt_id)
    if not attempt or 'result' in attempt: raise S.ScoutError('attempt not pending')
    E.provider_check(provider, state)
    if provider['usage']['output_tokens'] != S.UNKNOWN and provider['usage']['output_tokens'] > state.batch['max_output_tokens']:
        error = 'generation exceeded the frozen output-token budget'
    status, ideas = 'ERROR' if error else 'VALID', []
    if not error:
        try:
            ideas = E.parse_result(state, attempt, raw)
            if len(state.cards) + len(ideas) > state.batch['max_cards']: raise S.ScoutError('card budget exceeded')
        except (ValueError, TypeError, KeyError) as problem:
            status, error = 'INVALID', str(problem)[:4000]
    result = {'attempt_id': attempt_id, 'raw_response': raw, 'raw_import': raw_import,
              'provider': provider, 'status': status, 'error': error}
    moment = moment or S.utc_now()
    records = [('attempt_result', result)]
    E.apply(state, 'attempt_result', result, moment)
    if status == 'VALID':
        # Precompute the full set against one result; append validation replays every card.
        for index in range(len(ideas)):
            card = E.card_from(state, attempt_id, index, moment)
            E.apply(state, 'card', card, moment)
            records.append(('card', card))
    return archive.append_many(records, recorded_at=moment)


def triage(archive):
    state = archive.load()
    return archive.append_many([('assessment', E.assess(state, versions[-1])) for versions in state.cards.values()])


def run_local(archive, lane, count, model, seed=0):
    from .providers import OllamaProvider
    aid, prompt = prepare(archive, lane, count, model, 'OLLAMA_LOCAL')
    try:
        raw, provenance, raw_import = OllamaProvider(model).generate(prompt, seed)
        return finish(archive, aid, raw, provenance, raw_import=raw_import)
    except Exception as error:
        # No retry; the reserved attempt survives connection failure or malformed output.
        now = S.utc_now()
        provenance = {'model': model, 'provider': 'OLLAMA_LOCAL', 'invoked_at': now, 'completed_at': now,
            'parameters': {'seed': seed}, 'seed': seed, 'usage': dict(UNKNOWN_USAGE),
            'context_declaration': 'Failed local request; no successful generation is claimed.', 'operator': 'LOCAL_CLI'}
        return finish(archive, aid, '', provenance, error=f'{type(error).__name__}: local generation failed; no automatic retry')


def inspect_card(state, idea_id):
    card = state.latest(idea_id)
    return {'card': card, 'card_sha256': digest(card), 'current_route': state.route(card),
            'assessment': state.assessments.get((card['id'], card['version'])),
            'reviews': [r for r in state.reviews if r['idea_id'] == card['id']],
            'novelty': [r for r in state.novelty if r['idea_id'] == card['id']],
            'feasibility': [r for r in state.feasibility if r['idea_id'] == card['id']],
            'criticism': [r for r in state.critics if r['idea_id'] == card['id']],
            'outcome_references': [r for r in state.outcomes if r['idea_id'] == card['id']],
            'history': state.cards[idea_id], 'new_research_authority': False}


def critic_request(state, idea_id):
    card = state.latest(idea_id)
    return {'schema': 'SCOUT_INDEPENDENT_CRITIC_REQUEST_V001', 'idea_id': idea_id, 'version': card['version'],
            'card': card['idea'], 'seed_evidence': [state.seeds[s] for s in card['idea']['seed_ids']],
            'instructions': 'Independently challenge unsupported steps, competing explanations, generic interpretations, '
                'economic significance, observation requirements, identity and timing. State the decisive falsifier. '
                'Do not certify evidence, novelty, M/H, alpha or routing. Use a different model from the generator.',
            'response_schema': __import__('src.research.opportunity_scout.reviews', fromlist=['CRITIC']).CRITIC,
            'hosted_transmission_approved': False}
