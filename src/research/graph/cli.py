"""Economic Knowledge Graph v1 command line.

A derived, read-only research view over replay-validated Discovery Lab ledgers and the
historical-memory catalogue. Local files only: no network, no acquisition, no writes to ledgers.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.research.graph import demo, evaluate as E, operators as O, pilot as P, render as RN
from src.research.graph import model as M
from src.research.graph.catalogue import CATALOGUE_PATH
from src.research.graph.fixtures import build_all
from src.research.graph.project import GraphError, LEDGER_ROOT, build, discover_ledgers
from src.research.graph.rules import View

EXAMPLES = """examples:
  python -m src.research.graph build --check
  python -m src.research.graph search "spare capacity"
  python -m src.research.graph trace HIST-EF06
  python -m src.research.graph same-gap REQ_AVAILABLE_CAPACITY
  python -m src.research.graph explain HIST-SH09 CIK:0000093410
  python -m src.research.graph revisit DLC-NEW --ledgers docs/strategy/discovery/new.jsonl
  python -m src.research.graph export neighbourhood HIST-F01 --format mermaid --out view.mmd
  python -m src.research.graph demo --check
  python -m src.research.graph revisit OBS-1 --snapshot P1/snapshot.json --arm G --query-at 2026-11-02T10:15:00Z
  python -m src.research.graph pilot dry-run --check
"""


def common():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--mode', choices=M.MODES, help='memory (default): live + retrospective + historical memory; '
                   'prospective: live ledgers only; synthetic: synthetic ledgers only')
    p.add_argument('--ledgers', nargs='*', help=f'ledger files (default: every *.jsonl under {LEDGER_ROOT.relative_to(demo.ROOT)})')
    p.add_argument('--catalogue', help=f'historical-memory catalogue (default {CATALOGUE_PATH.relative_to(demo.ROOT)})')
    p.add_argument('--snapshot', help='pilot packet snapshot: frozen prior inputs plus the --arm ledger as of --query-at (replaces '
                   '--ledgers/--known-at/--catalogue/--mode)')
    p.add_argument('--arm', choices=('S', 'G'), help='pilot arm whose own ledger is visible (S may use baseline-search only)')
    p.add_argument('--query-at', help='pilot query time (default now; never in the future)')
    p.add_argument('--no-memory', action='store_true', help='synthetic mode without historical memory')
    p.add_argument('--known-at', help='only knowledge appended to Research OS records by this time (ISO date or datetime)')
    p.add_argument('--as-of', help='only relationships valid and observations occurred by this economic date')
    p.add_argument('--verified-only', action='store_true', help='hide unverified assertions and retrospective/historical memory')
    p.add_argument('--history', action='store_true', help='include superseded versions')
    p.add_argument('--exclude-retrospective', action='store_true', help='hide retrospective ledgers and historical memory')
    p.add_argument('--json', action='store_true', help='print the structured result instead of text')
    return p


def pilot_scope(a):
    """Snapshot mode takes every input from the frozen snapshot; mixing in other inputs is refused."""
    if not getattr(a, 'snapshot', None):
        if getattr(a, 'arm', None) or getattr(a, 'query_at', None):raise ValueError('--arm and --query-at need --snapshot')
        if hasattr(a, 'mode'):a.mode, a.catalogue = a.mode or 'memory', a.catalogue or str(CATALOGUE_PATH)
        return
    if not a.arm:raise ValueError('--snapshot needs --arm S or G')
    mixed = [f for f in ('ledgers', 'known_at', 'catalogue', 'mode', 'as_of') if getattr(a, f) is not None] + (['no_memory'] if a.no_memory else [])
    if mixed:raise ValueError(f'snapshot inputs are fixed; remove {mixed}')
    if a.arm == 'S' and a.command != 'baseline-search':raise ValueError('the structured arm uses no graph operator; use baseline-search')


def graph_for(a):
    if a.snapshot:
        g, view = P.arm_graph(a.snapshot, a.arm, a.query_at); a.visibility = view['receipt']; a.view = view
        return g
    ledgers = a.ledgers if a.ledgers is not None else None
    return build(ledgers=ledgers, catalogue_path=a.catalogue, mode=a.mode, known_at=a.known_at, with_memory=not a.no_memory)


def view_for(a):
    return View(as_of=a.as_of, verified_only=a.verified_only, history=a.history, exclude_retrospective=a.exclude_retrospective)


def emit(a, res):
    if getattr(a, 'visibility', None):res = {**res, 'visibility': a.visibility}
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str) if a.json else RN.text(res), end='' if not a.json else '\n')


def pilot_parser(sub):
    c = sub.add_parser('pilot', help='proposed pilot tooling: snapshots, isolation checks, blinding, accounting, paired report (no acquisition)')
    ps = c.add_subparsers(dest='pilot_command', required=True)
    x = ps.add_parser('snapshot', help='freeze a packet: pin its ledger prefix, the catalogue hash and the bundle hashes')
    x.add_argument('out'); x.add_argument('--packet', required=True); x.add_argument('--packet-ledger', required=True)
    x.add_argument('--arm-ledger', nargs=3, action='append', metavar=('ARM', 'LEDGER', 'CAMPAIGN'), required=True)
    x.add_argument('--bundle'); x.add_argument('--frozen-at'); x.add_argument('--catalogue', default=str(CATALOGUE_PATH))
    x = ps.add_parser('verify', help='verify a snapshot (and a bundle copy); both arms must print the same summary')
    x.add_argument('snapshot'); x.add_argument('--bundle')
    x = ps.add_parser('connections', help='validate an arm connection log (V1, or prospective V2 with suggestion origins)'); x.add_argument('log'); x.add_argument('--arm', choices=P.ARMS, required=True)
    x.add_argument('--suggestions', help='an exported suggestions JSON; V2 origins must match it exactly')
    x = ps.add_parser('blind', help='prepare the shuffled, arm-hidden adjudication export and its sealed key')
    x.add_argument('snapshot'); x.add_argument('--log', nargs=2, action='append', metavar=('ARM', 'LOG'), required=True)
    x.add_argument('--salt', required=True); x.add_argument('--out', required=True); x.add_argument('--key', required=True)
    x = ps.add_parser('adjudications', help='validate a blinded adjudication log'); x.add_argument('blind'); x.add_argument('log')
    x = ps.add_parser('account', help='effort of one arm by category against the campaign ceilings')
    x.add_argument('snapshot'); x.add_argument('--arm', choices=P.ARMS, required=True)
    x = ps.add_parser('report', help='paired per-packet report after unblinding'); x.add_argument('packets', nargs='+'); x.add_argument('--json', action='store_true')
    x.add_argument('--export', default='blind.json', help='presentation the adjudicator used (blind_v2.json for an aliased export)')
    x = ps.add_parser('realias', help='derive the versioned aliased presentation (V2) of an unchanged V001 export; refuses if any leak remains')
    x.add_argument('blind'); x.add_argument('--out', required=True); x.add_argument('--alias-key', required=True)
    x = ps.add_parser('sheet', help='render a readable adjudication sheet from an export'); x.add_argument('blind'); x.add_argument('--out', required=True)
    x = ps.add_parser('leak-scan', help='recursively scan exports (JSON) or sheets (text) for arm-identifying strings')
    x.add_argument('files', nargs='+'); x.add_argument('--own-from', help='a V001 export whose current-arm record ids also count as leaks')
    x = ps.add_parser('dry-run', help='synthetic end-to-end rehearsal through this CLI')
    g_ = x.add_mutually_exclusive_group(); g_.add_argument('--write', action='store_true'); g_.add_argument('--check', action='store_true')


def run_pilot(a):
    out = lambda value: print(json.dumps(value, indent=2, ensure_ascii=False, default=str))
    if a.pilot_command == 'snapshot':
        arms = {arm: (path, cid) for arm, path, cid in a.arm_ledger}
        snap, digest_ = P.make_snapshot(a.out, a.packet, a.packet_ledger, arms, a.bundle, a.catalogue, a.frozen_at)
        out({'written': a.out, 'snapshot_sha256': digest_, 'frozen_at_utc': snap['frozen_at_utc'], 'prior': snap['prior']['packet_ledger']})
    elif a.pilot_command == 'verify':out(P.verify_summary(a.snapshot, a.bundle))
    elif a.pilot_command == 'connections':
        exported = json.loads(Path(a.suggestions).read_text(encoding='utf-8'))['suggestions'] if a.suggestions else None
        out({'log': a.log, 'arm': a.arm, 'entries': len(P.validate_connections(a.log, a.arm, exported)), 'format': 'PASS'})
    elif a.pilot_command == 'blind':
        export = P.blind(a.snapshot, dict(a.log), a.salt, a.out, a.key)
        out({'written': a.out, 'items': len(export['items']), 'key_written': a.key, 'key_sha256': export['key_sha256']})
    elif a.pilot_command == 'adjudications':
        rows = P.validate_adjudications(a.blind, a.log); counts = {}
        for r in rows.values():counts[r['outcome']] = counts.get(r['outcome'], 0) + 1
        out({'adjudicated': len(rows), 'outcomes': dict(sorted(counts.items())), 'format': 'PASS'})
    elif a.pilot_command == 'account':
        v = P.load_snapshot(a.snapshot); out(P.account(v['base'] / v['snapshot']['arms'][a.arm]['ledger'], a.arm))
    elif a.pilot_command == 'report':
        rep = P.report(a.packets, export_name=a.export); print(json.dumps(rep, indent=2, default=str) if a.json else M.BANNER + '\n' + P.markdown(rep))
    elif a.pilot_command == 'realias':
        v2 = P.alias_export(a.blind, a.out, a.alias_key)
        out({'written': a.out, 'items': len(v2['items']), 'alias_key_written': a.alias_key, 'alias_key_sha256': v2['alias_key_sha256'], 'leaks': 0})
    elif a.pilot_command == 'sheet':
        Path(a.out).write_text(P.sheet(json.loads(Path(a.blind).read_text(encoding='utf-8'))), encoding='utf-8', newline='\n'); out({'written': a.out})
    elif a.pilot_command == 'leak-scan':
        own = P.own_records(json.loads(Path(a.own_from).read_text(encoding='utf-8'))) if a.own_from else ()
        results = {}
        for f in a.files:
            text = Path(f).read_text(encoding='utf-8')
            value = json.loads(text) if f.endswith('.json') else text
            results[f] = P.scan_leaks(value['items'] if isinstance(value, dict) and 'items' in value else value, own)
        out({f: {'findings': len(r), 'first': r[:10]} for f, r in results.items()})
        if any(results.values()):raise SystemExit(2)
    elif a.pilot_command == 'dry-run':
        from src.research.graph import pilot_dryrun as DR
        if a.check:out(DR.check())
        elif a.write:DR.RECORD.write_text(DR.generate(), encoding='utf-8', newline='\n'); out({'written': str(DR.RECORD.relative_to(demo.ROOT))})
        else:print(DR.generate(), end='')


def main(argv=None):
    parent = common()
    p = argparse.ArgumentParser(prog='python -m src.research.graph', description=__doc__, epilog=EXAMPLES,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    add = lambda name, help_: sub.add_parser(name, parents=[parent], help=help_, description=help_)
    c = add('build', 'build the projection and print counts, inputs, exclusions and its canonical digest'); c.add_argument('--check', action='store_true')
    c = add('search', 'find nodes containing every query term'); c.add_argument('text')
    c = add('show', 'one node with its attributes, evidence references and incident edges'); c.add_argument('node')
    c = add('neighbourhood', 'a bounded neighbourhood (hubs are not expanded)'); c.add_argument('node'); c.add_argument('--semantic', type=int, default=1)
    c = add('explain', 'bounded paths between two nodes, each with its first unsupported economic leap')
    c.add_argument('a'); c.add_argument('b'); c.add_argument('--semantic', type=int, default=M.DEFAULT_SEMANTIC_HOPS)
    c = add('trace', 'claim lineage or historical investigation memory'); c.add_argument('node')
    c = add('shared', 'other campaigns/investigations sharing a document hash or identified entity'); c.add_argument('node')
    c = add('complements', 'independent records that may complete an observation'); c.add_argument('node')
    c = add('same-gap', 'claims blocked by the same requirement or blocker'); c.add_argument('node')
    c = add('gaps', 'the specific unverified links of a claim'); c.add_argument('node')
    c = add('revisit', 'earlier claims a new observation or campaign might inform (never reopens them)'); c.add_argument('node')
    add('changes', 'changed, conflicting, superseded or stale knowledge')
    add('failures', 'stopped or held claims and historical verdicts, with scope')
    add('orphans', 'observations retained without a claim or relationship')
    add('next', 'reusable decisive checks across open claims (proposal only)')
    c = add('export', 'focused Mermaid or DOT view of a neighbourhood, explanation or trace')
    c.add_argument('kind', choices=('neighbourhood', 'explain', 'trace')); c.add_argument('nodes', nargs='+')
    c.add_argument('--format', choices=('mermaid', 'dot'), default='mermaid'); c.add_argument('--out'); c.add_argument('--semantic', type=int, default=1)
    c = sub.add_parser('demo', help='offline synthetic and historical walkthrough')
    g_ = c.add_mutually_exclusive_group(); g_.add_argument('--write', action='store_true'); g_.add_argument('--check', action='store_true')
    c = sub.add_parser('quality', help='Graph v1.1 discovery-quality regression on synthetic fixtures (v1 vs v1.1 vs structured search)')
    g_ = c.add_mutually_exclusive_group(); g_.add_argument('--write', action='store_true'); g_.add_argument('--check', action='store_true')
    c = sub.add_parser('evaluate', help='offline ordinary-search versus graph comparison on synthetic fixtures')
    c.add_argument('--timing', action='store_true', help='also report (non-deterministic) build runtime')
    c = add('suggestions', 'export suggestions for a target with baseline-discoverability flags (pilot hook)'); c.add_argument('node')
    c = add('baseline-search', 'competent structured-ledger search WITHOUT the graph (the pilot baseline arm tool)')
    c.add_argument('campaign'); c.add_argument('observation')
    pilot_parser(sub)
    a = p.parse_args(argv)
    try:
        if a.command == 'pilot':run_pilot(a); return
        pilot_scope(a)
        if a.command == 'demo':
            if a.check:print(json.dumps(demo.check()))
            elif a.write:demo.WALKTHROUGH.write_text(demo.generate(), encoding='utf-8', newline='\n'); print(f'written {demo.WALKTHROUGH.relative_to(demo.ROOT)}')
            else:print(demo.generate(), end='')
            return
        if a.command == 'quality':
            from src.research.graph import quality as Q
            if a.check:print(json.dumps(Q.check()))
            elif a.write:Q.RECORD.write_text(Q.generate(), encoding='utf-8', newline='\n'); print(f'written {Q.RECORD.relative_to(demo.ROOT)}')
            else:print(Q.generate(), end='')
            return
        if a.command == 'evaluate':
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:report = E.run(build_all(tmp), timing=a.timing)
            print(M.BANNER); print(E.markdown(report))
            if a.timing:print(f"runtime (not deterministic): {report['runtime_seconds']}")
            return
        if a.command == 'baseline-search':
            from src.research.graph import baseline as B
            from src.research.graph import catalogue as Cat
            if a.snapshot:
                view = P.arm_view(a.snapshot, a.arm, a.query_at)
                res = B.structured_search(view['ledgers'], a.campaign, a.observation, Cat.load(view['catalogue'])[0], None, view['cuts'])
                res = {'visibility': view['receipt'], **res}
            else:
                ledgers = a.ledgers if a.ledgers is not None else discover_ledgers()
                memory = Cat.load(a.catalogue)[0] if a.mode == 'memory' and not a.exclude_retrospective else None
                res = B.structured_search(ledgers, a.campaign, a.observation, memory, a.known_at)
            print(json.dumps({'note': 'Structured-ledger baseline; no graph projection used.', **res}, indent=2, default=str)); return
        g, view = graph_for(a), view_for(a)
        if a.command == 'build':
            kinds = {}
            for n in g.nodes.values():kinds[n['kind']] = kinds.get(n['kind'], 0) + 1
            info = {'banner': M.BANNER, 'mode': g.mode, 'known_at': a.known_at, 'nodes': len(g.nodes), 'edges': len(g.edges), 'by_kind': kinds,
                    'inputs': g.inputs, 'excluded': g.excluded, 'catalogue': g.catalogue, 'issues': len(g.issues), 'digest': g.digest()}
            if a.snapshot:info['visibility'] = a.visibility
            if a.check and a.snapshot:info['rebuild_identical'] = P.arm_graph(a.snapshot, a.arm, a.visibility['query_at_utc'])[0].digest() == info['digest']
            elif a.check:info['rebuild_identical'] = build(ledgers=a.ledgers, catalogue_path=a.catalogue, mode=a.mode, known_at=a.known_at,
                                                           with_memory=not a.no_memory).digest() == info['digest']
            print(json.dumps(info, indent=2))
            if a.check and not info['rebuild_identical']:raise SystemExit(1)
            return
        ops = {'search': lambda: O.search(g, a.text, view), 'show': lambda: O.show(g, a.node, view),
               'neighbourhood': lambda: O.neighbourhood(g, a.node, view, a.semantic), 'explain': lambda: O.explain(g, a.a, a.b, view, a.semantic),
               'trace': lambda: O.trace(g, a.node, view), 'shared': lambda: O.shared(g, a.node, view), 'complements': lambda: O.complements(g, a.node, view),
               'same-gap': lambda: O.same_gap(g, a.node, view), 'gaps': lambda: O.gaps(g, a.node, view), 'revisit': lambda: O.revisit(g, a.node, view),
               'changes': lambda: O.changes(g, view), 'failures': lambda: O.failures(g, view), 'orphans': lambda: O.orphans(g, view),
               'next': lambda: O.next_questions(g, view)}
        if a.command in ops:emit(a, ops[a.command]()); return
        if a.command == 'suggestions':
            from src.research.graph import catalogue as Cat
            if a.snapshot:
                found = E.export_suggestions(g, a.node, a.view['ledgers'], Cat.load(a.view['catalogue'])[0], None, a.view['cuts'])
                print(json.dumps({'banner': M.BANNER, 'visibility': a.visibility, 'suggestions': found}, indent=2)); return
            ledgers = a.ledgers if a.ledgers is not None else discover_ledgers()
            memory = Cat.load(a.catalogue)[0] if g.catalogue else None
            print(json.dumps({'banner': M.BANNER, 'suggestions': E.export_suggestions(g, a.node, ledgers, memory, a.known_at)}, indent=2)); return
        if a.command == 'export':
            res = {'neighbourhood': lambda: O.neighbourhood(g, a.nodes[0], view, a.semantic), 'trace': lambda: O.trace(g, a.nodes[0], view),
                   'explain': lambda: O.explain(g, a.nodes[0], a.nodes[1], view, a.semantic)}[a.kind]()
            text = (RN.mermaid if a.format == 'mermaid' else RN.dot)(g, res)
            if a.out:Path(a.out).write_text(text, encoding='utf-8', newline='\n'); print(f'written {a.out}')
            else:print(text, end='')
    except (GraphError, O.NotFound, ValueError) as error:
        print(f'refused: {error}', file=sys.stderr); raise SystemExit(2)


if __name__ == '__main__':
    main()
