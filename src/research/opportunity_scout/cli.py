"""Local proposal CLI. No scientific fetch, pilot, experiment or trading commands."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.research.spec import canonical, digest
from . import BANNER
from . import engine as E, schema as S, workflow as W
from .storage import Archive, input_json, unlinked


def emit(value):
    import json
    print(json.dumps({'banner': BANNER, **value} if isinstance(value, dict) else {'banner': BANNER, 'results': value},
                     ensure_ascii=False, indent=2, allow_nan=False))


def response_import(archive, filename):
    bundle = input_json(filename)
    S.validate(S.obj({'attempt_id': S.LABEL, 'provenance': S.PROVIDER, 'output': {'type': ['object', 'string']}}), bundle)
    raw = bundle['output'] if isinstance(bundle['output'], str) else canonical(bundle['output']).decode()
    return W.finish(archive, bundle['attempt_id'], raw, bundle['provenance'],
                    raw_import=Path(filename).read_text(encoding='utf-8'))


def export_prompt(archive, lane, count, model, provider='OPERATOR_ASSISTED'):
    aid, prompt = W.prepare(archive, lane, count, model, provider)
    path = archive.export(aid + '-prompt.json', {'attempt_id': aid, 'prompt': prompt,
        'response_import_format': {'attempt_id': aid, 'provenance_schema': S.PROVIDER, 'output_schema': prompt['response_schema']},
        'instructions': 'Supply this prompt in a fresh model session. Save model identity, invocation timestamps and known/unknown usage. '
            'Do not fill unsupported fields or use fixtures as generated results. Run Forge before viewing Radar ideas.',
        'hosted_transmission_authorised': False})
    return {'attempt_id': aid, 'path': str(path), 'prompt_sha256': prompt['sha256'], 'status': 'AWAITING_REAL_MODEL_OUTPUT'}


def learning(state):
    return {'schema': 'SCOUT_FUTURE_LEARNING_V001', 'policy': E.POLICY, 'training_performed': False,
        'records': [{'idea_id': iid, 'initial_card': versions[0], 'initial_card_sha256': digest(versions[0]),
            'immutable_versions': versions, 'current_route': state.route(versions[-1]),
            'all_selection_records': [x for selection in state.selections for x in selection['all_candidates'] if x['idea_id'] == iid],
            'reviews': [r for r in state.reviews if r['idea_id'] == iid],
            'later_outcome_references': [o for o in state.outcomes if o['idea_id'] == iid],
            'investigation_status': next((o['label'] for o in reversed(state.outcomes) if o['idea_id'] == iid), 'NOT_INVESTIGATED'),
            'outcome_reference_only': True,
            'uninvestigated_is_failure': False} for iid, versions in state.cards.items()],
        'attempts_including_errors': list(state.attempts.values()), 'efforts': state.efforts,
        'selection_missingness': 'Selection is non-random. Uninvestigated, source blocked and economically falsified are different labels.',
        'no_learning_or_policy_updates': True}


def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog=BANNER)
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('init'); x.add_argument('store'); x.add_argument('--title', required=True)
    x.add_argument('--synthetic', action='store_true'); x.add_argument('--no-memory', action='store_true')
    x.add_argument('--max-cards', type=int, default=24); x.add_argument('--max-attempts', type=int, default=9)
    x.add_argument('--knowledge-cutoff', help='timezone-aware common cutoff for a separately planned comparison')
    x = sub.add_parser('seed'); x.add_argument('store'); x.add_argument('input')
    x = sub.add_parser('prepare'); x.add_argument('store'); x.add_argument('--lane', choices=S.LANES, required=True)
    x.add_argument('--count', type=int, default=2); x.add_argument('--model', required=True)
    x = sub.add_parser('prepare-batch'); x.add_argument('store'); x.add_argument('--per-lane', type=int, default=2); x.add_argument('--model', required=True)
    x = sub.add_parser('import-response'); x.add_argument('store'); x.add_argument('input')
    x = sub.add_parser('run'); x.add_argument('store'); x.add_argument('--responses', nargs='+')
    x.add_argument('--local-model'); x.add_argument('--per-lane', type=int, default=2)
    for name in ('triage', 'list', 'shortlist', 'incubator', 'report', 'quality-audit', 'validate', 'learning-export'):
        x = sub.add_parser(name); x.add_argument('store')
    x = sub.add_parser('card'); x.add_argument('store'); x.add_argument('idea')
    for name in ('review', 'revise', 'novelty', 'feasibility', 'critic-import', 'shadow-import', 'outcome', 'effort', 'generation-effort'):
        x = sub.add_parser(name); x.add_argument('store'); x.add_argument('input')
    for name in ('handoff', 'shadow-request', 'critic-request'):
        x = sub.add_parser(name); x.add_argument('store'); x.add_argument('idea')
    x = sub.add_parser('reconsider'); x.add_argument('store'); x.add_argument('--seed', required=True)
    x.add_argument('--requirement', action='append', default=[]); x.add_argument('--identifier', action='append', default=[])
    x = sub.add_parser('schema'); x.add_argument('kind', choices=('idea', 'seed', 'provenance', 'review', 'novelty', 'feasibility', 'critic', 'outcome', 'effort', 'generation-effort'))
    x = sub.add_parser('demo'); x.add_argument('--out'); x.add_argument('--write', action='store_true')
    x = sub.add_parser('evaluate-blind'); x.add_argument('packet'); x.add_argument('key'); x.add_argument('--judgments')
    x.add_argument('--states', help='optional local JSON mapping the four conditions to scout archives for shadow comparisons')
    x = sub.add_parser('blind'); x.add_argument('store');
    for name in ('plain', 'evidence', 'mechanism', 'hybrid'): x.add_argument('--' + name, required=True)
    x.add_argument('--salt-file', required=True, help='local JSON {"salt": ...}; never publish the salt or key')
    x = sub.add_parser('freeze-evaluation'); x.add_argument('store'); x.add_argument('--seeds', required=True)
    x = sub.add_parser('install-evaluation'); x.add_argument('store'); x.add_argument('--package', required=True)
    x = sub.add_parser('bind-evaluation'); x.add_argument('store'); x.add_argument('--model', required=True)
    x.add_argument('--parameters', required=True, help='local JSON object with identical sampling settings')
    for name in ('evaluation-status', 'evaluation-requests'):
        x = sub.add_parser(name); x.add_argument('store')
    x = sub.add_parser('run-evaluation'); x.add_argument('store'); x.add_argument('--local-model', required=True)
    x = sub.add_parser('blind-evaluation'); x.add_argument('store'); x.add_argument('--salt-file', required=True)
    return p


def dispatch(a):
    if a.command == 'schema':
        from .reviews import NOVELTY, FEASIBILITY_V002, CRITIC, OUTCOME, EFFORT, GENERATION_EFFORT
        from .readiness import REVIEW
        return {'schema': {'idea': S.IDEA, 'seed': S.SEED, 'provenance': S.PROVIDER, 'review': REVIEW,
            'novelty': NOVELTY, 'feasibility': FEASIBILITY_V002, 'critic': CRITIC, 'outcome': OUTCOME,
            'effort': EFFORT, 'generation-effort': GENERATION_EFFORT}[a.kind]}
    if a.command in ('freeze-evaluation', 'install-evaluation', 'bind-evaluation', 'evaluation-status', 'evaluation-requests', 'run-evaluation', 'blind-evaluation'):
        from . import comparison as C
        if a.command == 'freeze-evaluation': return C.freeze(a.store, a.seeds)
        if a.command == 'install-evaluation': return C.install(a.store, a.package)
        if a.command == 'bind-evaluation': return C.bind(a.store, a.model, input_json(a.parameters))
        if a.command == 'evaluation-status': return C.status(a.store)
        if a.command == 'evaluation-requests': return C.requests(a.store)
        if a.command == 'run-evaluation': return C.run_local(a.store, a.local_model)
        return C.blind_package(a.store, input_json(a.salt_file)['salt'])
    if a.command == 'demo':
        from .demo import run
        return run(a.out, write=a.write)
    if a.command == 'evaluate-blind':
        from .evaluation import evaluate_blind, shadow_metrics
        packet, key = input_json(a.packet), input_json(a.key)
        judgments = input_json(a.judgments) if a.judgments else []
        result = evaluate_blind(packet, key, judgments)
        if a.states:
            paths = input_json(a.states)
            E.exact(paths, ('PLAIN', 'EVIDENCE_ONLY', 'MECHANISM_ONLY', 'HYBRID'))
            result['jev_shadow'] = shadow_metrics({k: Archive(p).load() for k, p in paths.items()}, key, judgments)
        return result
    archive = Archive(a.store)
    if a.command == 'init':
        state = W.initialise(archive, a.title, fixture='SYNTHETIC' if a.synthetic else 'SCOUT_EXPLORATORY',
            with_memory=not a.no_memory, max_cards=a.max_cards, max_attempts=a.max_attempts, cutoff=a.knowledge_cutoff)
        return {'batch': state.batch, 'archive': str(archive.file)}
    if a.command == 'seed':
        bundle = input_json(a.input)
        S.validate(S.obj({'seeds': S.array(S.SEED, 20, 1)}), bundle)
        state = archive.append_many([('seed', seed) for seed in bundle['seeds']])
        return {'seeds': list(state.seeds), 'source_requests': 0}
    if a.command == 'prepare': return export_prompt(archive, a.lane, a.count, a.model)
    if a.command == 'prepare-batch': return {'requests': [export_prompt(archive, lane, a.per_lane, a.model) for lane in ('FORGE', 'RADAR', 'GAP')]}
    if a.command == 'import-response':
        state = response_import(archive, a.input)
        return {'attempt_statuses': {aid: r.get('result', {}).get('status', 'PENDING') for aid, r in state.attempts.items()},
                'cards': list(state.cards)}
    if a.command == 'run':
        if bool(a.responses) == bool(a.local_model): raise S.ScoutError('choose supplied operator responses OR a configured local model')
        if a.responses:
            for filename in a.responses: response_import(archive, filename)
        else:
            for lane in ('FORGE', 'RADAR', 'GAP'): W.run_local(archive, lane, a.per_lane, a.local_model)
        W.triage(archive)
        return archive.append('selection', E.select(archive.load())).selections[-1]
    if a.command in ('review', 'revise', 'novelty', 'feasibility', 'critic-import', 'shadow-import', 'outcome', 'effort', 'generation-effort'):
        kind = {'revise': 'revision', 'critic-import': 'critic', 'shadow-import': 'shadow', 'generation-effort': 'generation_effort'}.get(a.command, a.command)
        state = archive.append(kind, input_json(a.input))
        return {'recorded': kind, 'events': len(state.events), 'acquisition_authorised': False}
    if a.command == 'triage': return {'assessments': list(W.triage(archive).assessments.values())}
    state = archive.load()
    if not state.batch: raise S.ScoutError('initialise a batch first')
    if a.command == 'validate': return {'valid': True, 'events': len(state.events), 'head': state.events[-1]['hash']}
    if a.command == 'list': return [{'id': c['id'], 'version': c['version'], 'title': c['idea']['title'], 'lane': c['lane'], 'route': state.route(c)} for c in [v[-1] for v in state.cards.values()]]
    if a.command == 'card': return W.inspect_card(state, a.idea)
    if a.command == 'shortlist': return archive.append('selection', E.select(state)).selections[-1]
    if a.command == 'incubator': return [{'card': v[-1], 'reconsider_when': v[-1]['idea']['reconsider_when']} for v in state.cards.values() if state.route(v[-1]) == 'INCUBATE']
    if a.command == 'report':
        from .evaluation import report
        return report(state)
    if a.command == 'quality-audit':
        from .evaluation import quality_audit
        return quality_audit(state)
    if a.command == 'learning-export': return learning(state)
    if a.command == 'reconsider':
        from .reviews import reconsider
        record = reconsider(state, a.seed, a.requirement, a.identifier)
        archive.append('reconsideration', record); return record
    if a.command in ('handoff', 'shadow-request', 'critic-request'):
        if a.command == 'handoff': payload = E.handoff(state, a.idea)
        elif a.command == 'critic-request': payload = W.critic_request(state, a.idea)
        else:
            from .providers import shadow_request
            payload = shadow_request(state, a.idea)
        filename = f'{a.idea}-v{state.latest(a.idea)["version"]}-{a.command}.json'
        return {'path': str(archive.export(filename, payload)), 'payload_sha256': digest(payload), 'authorises': []}
    if a.command == 'blind':
        from .evaluation import blind
        states = {k: Archive(v).load() for k, v in zip(('PLAIN', 'EVIDENCE_ONLY', 'MECHANISM_ONLY', 'HYBRID'), (a.plain, a.evidence, a.mechanism, a.hybrid))}
        packet, key = blind(states, input_json(a.salt_file)['salt'])
        key_path = archive.export('blinding-key-private.json', key)
        packet_path = archive.export('blinded-review.json', packet)
        return {'packet': str(packet_path), 'key': str(key_path), 'blinding': 'PARTIAL_PROCEDURAL', 'warning': 'Reviewer receives only the packet, never the sealed key.'}
    raise S.ScoutError('unsupported command')


def main(argv=None):
    try: emit(dispatch(parser().parse_args(argv)))
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'Opportunity Scout: {error}', file=sys.stderr)
        return 2
    return 0
