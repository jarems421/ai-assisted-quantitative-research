"""Opportunity Scout AI Critic V001: offline preparation, import, validation, recommendation and reporting.

No command calls a model, opens a network connection or reads a credential. An operator gives each frozen prompt
(requests/<id>.md) to a separately authorised model session, saves the raw reply, and imports it unchanged."""
from __future__ import annotations

import argparse
import sys

from src.research.spec import canonical
from .. import schema as S
from ..cli import emit
from ..storage import Archive, input_json, unlinked
from . import benchmark as B, evaluation as V, jev as J, packages as P, policy as Q, rubric as K

CRITIC_BANNER = 'AI CRITIC RECOMMENDATION ONLY - NOT A HUMAN JUDGMENT - NO ROUTING OR RESEARCH AUTHORITY'


def store_paths(values):
    out = dict(x.split('=', 1) for x in values)
    if len(out) != len(values) or any(not k or not v for k, v in out.items()):raise S.ScoutError('--store is NAME=PATH with distinct names')
    return out


def read_raw(path):
    p = unlinked(path); lowered = [x.lower() for x in p.parts]
    if any(x in ('.git', 'keys') or x.startswith('.env') for x in lowered) or any(a == 'data' and b == 'raw' for a, b in zip(lowered, lowered[1:])):
        raise S.ScoutError('private raw archives, keys and repository internals are never read')
    if not p.is_file() or p.stat().st_size > P.MAX_RAW:raise S.ScoutError('the raw answer must be a regular file of at most 1 MiB')
    return p.read_bytes()


def numbered(ws, folder, prefix, value):
    with ws.locked():
        return ws.write(f'{folder}/{prefix}-{len(ws.files(folder)) + 1:04d}.json', value)


def latest(ws, folder, name=None):
    files = ws.files(folder)
    if not files:raise S.ScoutError(f'no {folder} file yet')
    chosen = f'{folder}/{name}.json' if name else files[-1]
    if chosen not in files:raise S.ScoutError(f'unknown {folder} file {name}')
    return ws.read(chosen)


def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog=CRITIC_BANNER)
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('prepare', help='freeze Layer A, blinded inputs and first-pass requests for every current card')
    x.add_argument('--store', action='append', required=True, metavar='NAME=PATH'); x.add_argument('--out', required=True)
    x.add_argument('--split', choices=P.SPLITS, required=True); x.add_argument('--variants', default='', help='comma list of ' + ','.join(P.VARIANTS))
    x = sub.add_parser('status', help='requests, attempts and what is missing'); x.add_argument('workspace')
    x = sub.add_parser('import-response', help='import a saved raw model reply unchanged (operator attestation)')
    x.add_argument('workspace'); x.add_argument('request_id'); x.add_argument('raw')
    x.add_argument('--model', required=True, help='exact model identity, never a floating alias for calibrated runs')
    x.add_argument('--model-family', required=True, help='provider/model family, used to flag correlated reviews')
    x.add_argument('--provider', choices=P.PROVIDERS, required=True); x.add_argument('--by', required=True, help='your own name')
    x.add_argument('--fresh-context', choices=('YES', 'NO', 'UNKNOWN'), default='UNKNOWN')
    x.add_argument('--saw-other-critic-outputs', action='store_true'); x.add_argument('--received-at', default=S.UNKNOWN)
    for name in ('input-tokens', 'output-tokens', 'cost', 'latency-ms'):x.add_argument('--' + name, default=S.UNKNOWN)
    x.add_argument('--currency', choices=('USD', S.UNKNOWN), default=S.UNKNOWN)
    x = sub.add_parser('adversarial', help='freeze one selective adversarial request for a subject')
    x.add_argument('workspace'); x.add_argument('subject'); x.add_argument('--reason', choices=Q.SELECTION, required=True); x.add_argument('--note', default='')
    x = sub.add_parser('recommend', help='write the next deterministic recommendation file'); x.add_argument('workspace')
    x = sub.add_parser('jev-compare', help='LEGACY_RETIRED: archived Jev/critic comparison, explicit historical replay only')
    x.add_argument('workspace'); x.add_argument('--store', action='append', required=True, metavar='NAME=PATH')
    x.add_argument('--legacy-replay', action='store_true', help='acknowledge historical replay only; never a candidate future Jev role')
    x = sub.add_parser('anchor-packet', help='blinded packet for independent human anchors (no AI or Jev output)')
    x.add_argument('workspace'); x.add_argument('--salt-file', required=True); x.add_argument('--out', required=True)
    x = sub.add_parser('evaluate', help='calibration report; with anchors, against independent human labels')
    x.add_argument('workspace'); x.add_argument('--packet'); x.add_argument('--key'); x.add_argument('--anchors')
    x = sub.add_parser('queue', help='reproducible human review queue from a frozen recommendation file and a recorded seed')
    x.add_argument('workspace'); x.add_argument('--seed', required=True); x.add_argument('--mode', choices=('CALIBRATION_ALL', 'SELECTIVE_PROPOSED'), default='CALIBRATION_ALL')
    x.add_argument('--recommendations', help='e.g. REC-0001; default the latest')
    x = sub.add_parser('admission', help='could this evaluation be put to the owner? Never activates routing')
    x.add_argument('workspace'); x.add_argument('--evaluation', help='e.g. EVAL-0001; default the latest')
    x = sub.add_parser('benchmark', help='synthetic adversarial benchmark'); g = x.add_mutually_exclusive_group()
    g.add_argument('--write', action='store_true'); g.add_argument('--check', action='store_true')
    x = sub.add_parser('sample-size', help='labelled cases needed for a one-sided lower bound')
    x.add_argument('--target', type=float, default=.95); x.add_argument('--failures', type=int, default=0)
    x = sub.add_parser('schema', help='print an exact contract'); x.add_argument('kind', choices=('output', 'anchor'))
    return p


def number(value):
    return value if value == S.UNKNOWN else float(value)


def dispatch(a):
    if a.command == 'jev-compare' and not a.legacy_replay:
        raise S.ScoutError('LEGACY_RETIRED — NOT ACTIVE: Jev is research navigation, not a Forge critic. Historical comparison requires --legacy-replay.')
    if a.command == 'schema':return {'schema': K.OUTPUT if a.kind == 'output' else V.ANCHOR}
    if a.command == 'sample-size':
        return {'target': a.target, 'failures_allowed': a.failures, 'required_independent_cases': V.required_n(a.target, .05, a.failures),
                'basis': 'exact one-sided 95% Clopper-Pearson lower bound; per generation context, independent human anchors only'}
    if a.command == 'benchmark':
        if a.write:return {'written': str(B.write()), 'note': 'Review the diff: a changed record is a changed benchmark.'}
        if a.check:return B.check()
        r = B.report()
        return {'profiles': {k: {'passes_benchmark': v['passes_benchmark'], 'invalid_answers': v['invalid_answers'], 'summary': v['summary']['ALL'],
                                 'stability': v['stability']} for k, v in r['profiles'].items()}, 'interpretation': r['interpretation']}
    if a.command == 'prepare':
        states = {k: Archive(v).load() for k, v in store_paths(a.store).items()}
        variants = tuple(v for v in a.variants.split(',') if v)
        ws, manifest = P.prepare(states, a.out, split=a.split, variants=variants)
        subjects = manifest['subjects']
        return {'workspace': str(ws.path), 'subjects': len(subjects), 'reviewable': sum(e['input_sha256'] is not None for e in subjects.values()),
                'requests': sorted(r for e in subjects.values() for r in e['requests'].values()), 'model_calls_made': 0,
                'next': 'Give each requests/<id>.md to a separately authorised model session, then import-response the raw reply.'}
    ws = P.Workspace(a.workspace)
    if a.command == 'status':
        manifest, (chosen, history) = ws.manifest(), P.usable(ws)
        rows = {}
        for r in ws.requests():
            rows.setdefault(r['subject_key'], {})[r['critic']] = {'request_id': r['request_id'],
                'attempts': [{'attempt': x['attempt'], 'status': x['status'], 'problems': x['problems'][:5]} for x in history.get(r['request_id'], [])]}
        return {'fixture': manifest['fixture'], 'split': manifest['split'], 'subjects': {k: {'lane': e['lane'], 'reviewable': e['input_sha256'] is not None,
                'requests': rows.get(k, {})} for k, e in sorted(manifest['subjects'].items())}}
    if a.command == 'import-response':
        prov = P.provenance(a.model, a.model_family, a.provider, a.by, fresh_context=a.fresh_context, saw_other_critic_outputs=a.saw_other_critic_outputs,
                            received_at=a.received_at, input_tokens=number(a.input_tokens), output_tokens=number(a.output_tokens),
                            cost=number(a.cost), currency=a.currency, latency_ms=number(a.latency_ms))
        record = P.import_response(ws, a.request_id, read_raw(a.raw), prov)
        return {'attempt': record['attempt'], 'status': record['status'], 'problems': record['problems'], 'refusals': record['refusals'],
                'raw_sha256': record['raw_sha256'], 'basis': record['basis'], 'provider_verified': False, 'routing_changed': False}
    if a.command == 'adversarial':
        r = Q.request_adversarial(ws, a.subject, a.reason, a.note)
        return {'request_id': r['request_id'], 'prompt_file': f'requests/{r["request_id"]}.md', 'challenges': len(r['input']['challenges'])}
    if a.command == 'recommend':
        record, path = Q.recommend(ws)
        return {'file': str(path), 'counts': record['counts'], 'routing_changed': False, 'human_gates': record['human_gates']}
    if a.command == 'jev-compare':
        paths = store_paths(a.store)
        provenance = {k: [input_json(f) for f in sorted((Archive(v).path / 'exports').glob('jev-provenance-e*.json'))] for k, v in paths.items()}
        report = J.compare(ws, {k: Archive(v).load() for k, v in paths.items()}, provenance)
        return {'file': str(numbered(ws, 'jev', 'JEV', report)), **{k: report[k] for k in ('subjects_compared', 'missing', 'interpretation')},
                'legacy_status': 'LEGACY_RETIRED — NOT ACTIVE', 'historical_replay_only': True, 'authorises': []}
    if a.command == 'anchor-packet':
        packet, key = V.anchor_packet(ws, input_json(a.salt_file)['salt'])
        out = unlinked(a.out); out.mkdir(parents=True, exist_ok=False)
        for name, value in (('critic-anchor-packet.json', packet), ('critic-anchor-key-private.json', key)):(out / name).write_bytes(canonical(value))
        return {'packet': str(out / 'critic-anchor-packet.json'), 'private_key': str(out / 'critic-anchor-key-private.json'), 'items': len(packet['items']),
                'warning': 'Labellers receive only the packet: never the key, the workspace, recommendations or any AI or Jev output.'}
    if a.command == 'evaluate':
        if bool(a.packet) != bool(a.key) or bool(a.anchors) and not a.packet:raise S.ScoutError('anchors need both --packet and --key')
        report = V.evaluate(ws, input_json(a.packet) if a.packet else None, input_json(a.key) if a.key else None, input_json(a.anchors) if a.anchors else [])
        return {'file': str(numbered(ws, 'evaluations', 'EVAL', report)), 'labels': report['labels'], 'sample_plan': report['sample_plan'],
                'contexts': {k: {m: v[m] for m in ('subjects', 'research_worthy_retained_recall', 'fatal_detected', 'false_acceptance_rate')}
                             for k, v in report['contexts'].items()}, 'calibration_established': False}
    if a.command == 'queue':
        seed = int(a.seed) if a.seed.lstrip('-').isdigit() else a.seed
        q = V.queue(latest(ws, 'recommendations', a.recommendations), seed, a.mode)
        return {'file': str(numbered(ws, 'queues', 'QUEUE', q)), 'mode': q['mode'], 'active': q['active'], 'items': len(q['items']),
                'projected_human_fraction': q['projected_human_fraction']}
    if a.command == 'admission':
        return V.admission(latest(ws, 'evaluations', a.evaluation), B.check()['reference_passes'])
    raise S.ScoutError('unknown command')


def main(argv=None):
    try:
        out = dispatch(parser().parse_args(argv))
        emit({'critic_banner': CRITIC_BANNER, **out})
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'Opportunity Scout AI critic: {error}', file=sys.stderr)
        return 2
    return 0
