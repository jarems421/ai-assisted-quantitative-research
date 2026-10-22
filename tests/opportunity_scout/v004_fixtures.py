"""Fictional recorded stream profile; never copies a real prompt/receipt."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.research.spec import digest
from src.research.opportunity_scout import engine as E, prompts, schema as S, workflow as W
from src.research.opportunity_scout import v004_package as P, v004_runtime as R, v004_isolation as I
from src.research.opportunity_scout import v004_monitoring as M, v004_transport as T
from src.research.opportunity_scout.fixtures import MOMENT, seed, idea

MODEL = 'claude-opus-99-1'


def blueprints():
    memory = W.empty_memory(MOMENT)
    memory['investigations'] = {'HIST-SYNTHETIC': {'id': 'HIST-SYNTHETIC', 'title': 'Fictional depot inspection',
        'requirements': ['REQ_AVAILABLE_CAPACITY'], 'findings': [], 'verdict': 'FICTIONAL_NOT_CHECKED', 'closed_source_routes': []}}
    out = {}
    for condition in P.CONDITIONS:
        events = []; state = E.State()
        def append(kind, record):
            E.apply(state, kind, record, MOMENT)
            events.append({'type': kind, 'record': copy.deepcopy(record), 'recorded_at': MOMENT})
        append('batch', {'id': 'SCOUT-SYNTHETIC-' + condition, 'title': 'SYNTHETIC ' + condition,
            'fixture': 'SYNTHETIC', 'base_commit': '0' * 40, 'knowledge_cutoff': MOMENT,
            'max_cards': 6, 'max_attempts': 3, 'max_output_tokens': 6000, 'shortlist_slots': 4,
            'policy': E.POLICY, 'memory': memory, 'acquisition_authorised': False})
        append('seed', seed())
        for i, lane in enumerate(P.ALLOCATION[condition], 1):
            prompt = prompts.make_prompt(state, lane, 2, f'PROMPT-{i:04d}')
            append('prompt', prompt)
            append('attempt_start', {'id': f'ATT-{i:04d}', 'prompt_id': prompt['id'],
                'requested_model': 'MODEL_BOUND_BEFORE_GENERATION', 'provider': 'OPERATOR_ASSISTED', 'started_at': MOMENT})
        out[condition] = {'events': events}
    return out


def runtime(): return R.description(MODEL, 'a' * 64, 'FICTIONAL-2.1.302')


def output(request):
    ideas = [idea(variant=i) for i in range(2)]
    for card in ideas:
        if request['lane'] == 'RADAR': card['seed_ids'] = list(request['context']['seeds'])[:1]
        if request['lane'] == 'GAP':
            card['historical_refs'] = [{'investigation': 'HIST-SYNTHETIC', 'requirement': 'REQ_AVAILABLE_CAPACITY',
                'changed_domain': 'Fictional irrigation controllers', 'measurement_difference': 'A separate hypothetical scheduling register.'}]
    return {'ideas': ideas}


def encode(events): return ('\n'.join(json.dumps(e, ensure_ascii=False) for e in events) + '\n').encode('utf-8')


def events(request, session, *, raw=None, continuation=False, usage=None):
    text = json.dumps(output(request), ensure_ascii=False) if raw is None else raw
    usage = usage if usage is not None else dict(zip(T.COMPONENTS, (1000, 1000, 1000, 12000)))
    init = {'type': 'system', 'subtype': 'init', 'session_id': session, 'model': MODEL,
            'tools': [], 'skills': [], 'mcp_servers': [], 'permissionMode': 'dontAsk', 'apiKeySource': 'none'}
    def assistant(i, fragment, stop):
        return {'type': 'assistant', 'session_id': session, 'request_id': f'FICTIONAL-request-{i}',
                'message': {'id': f'FICTIONAL-message-{i}', 'model': MODEL,
                            'content': [{'type': 'text', 'text': fragment}], 'stop_reason': stop}}
    result = {'type': 'result', 'session_id': session, 'subtype': 'success', 'is_error': False,
              'result': text, 'usage': usage, 'modelUsage': {MODEL: dict(zip(
                  ('inputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens'),
                  (usage.get(k, S.UNKNOWN) for k in T.COMPONENTS)))},
              'permission_denials': [], 'subagent_stats': {'spawned': 0}, 'num_turns': 1,
              'total_cost_usd': 9.99}
    if not continuation: return [init, assistant(1, text, 'end_turn'), result]
    point = len(text) // 2
    result['num_turns'] = 2
    return [init, assistant(1, text[:point], 'max_tokens'),
            {'type': 'user', 'session_id': session, 'isSynthetic': True,
             'message': {'role': 'user', 'content': [{'type': 'text', 'text': T.NOTICE}]}},
            assistant(2, text[point:], 'end_turn'), result]


def window(session='FICTIONAL-session', slot='PLAIN-ATT-0001'):
    position = next(r['position'] for r in P.order() if r['slot'] == slot)
    start = datetime(2026, 10, 22, 12, tzinfo=timezone.utc) + timedelta(seconds=180 * (position - 1))
    probe = {'pid': 900, 'parent_pid': 800, 'started_at': (start + timedelta(seconds=65)).isoformat()}
    samples, processes, phases = [], [], []
    for i in range(28):
        phase = 'baseline' if i <= 12 else 'active' if i == 13 else 'cooldown'
        moment = (start + timedelta(seconds=5*i)).isoformat()
        samples.append({'sampled_at': moment, 'files': {p: {'state': 'ABSENT'} for p in M.ACCOUNT_PATHS}})
        processes.append({'sampled_at': moment, 'observable': True, 'processes': [probe] if phase == 'active' else []})
        phases.append(phase)
    home = str(Path('FICTIONAL-HOME').absolute()); config = str(Path(home) / '.claude-research')
    return {'schema': I.VERSION, 'session_id': session, 'samples': samples, 'process_samples': processes, 'phases': phases,
            'probe': probe, 'parent_pid': 800, 'home': home, 'requested_config_dir': config,
            'observed_config_dir': config, 'config_observation': 'RECORDED_FICTIONAL', 'account_source': 'subscription'}
