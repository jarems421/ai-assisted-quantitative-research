"""Economic Knowledge Graph v1 command line.

A derived, read-only research view over replay-validated Discovery Lab ledgers and the
historical-memory catalogue. Local files only: no network, no acquisition, no writes to ledgers.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.research.graph import demo, evaluate as E, operators as O, render as RN
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
"""


def common():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--mode', choices=M.MODES, default='memory', help='memory (default): live + retrospective + historical memory; '
                   'prospective: live ledgers only; synthetic: synthetic ledgers only')
    p.add_argument('--ledgers', nargs='*', help=f'ledger files (default: every *.jsonl under {LEDGER_ROOT.relative_to(demo.ROOT)})')
    p.add_argument('--catalogue', default=str(CATALOGUE_PATH), help='historical-memory catalogue')
    p.add_argument('--no-memory', action='store_true', help='synthetic mode without historical memory')
    p.add_argument('--known-at', help='only knowledge appended to Research OS records by this time (ISO date or datetime)')
    p.add_argument('--as-of', help='only relationships valid and observations occurred by this economic date')
    p.add_argument('--verified-only', action='store_true', help='hide unverified assertions and retrospective/historical memory')
    p.add_argument('--history', action='store_true', help='include superseded versions')
    p.add_argument('--exclude-retrospective', action='store_true', help='hide retrospective ledgers and historical memory')
    p.add_argument('--json', action='store_true', help='print the structured result instead of text')
    return p


def graph_for(a):
    ledgers = a.ledgers if a.ledgers is not None else None
    return build(ledgers=ledgers, catalogue_path=a.catalogue, mode=a.mode, known_at=a.known_at, with_memory=not a.no_memory)


def view_for(a):
    return View(as_of=a.as_of, verified_only=a.verified_only, history=a.history, exclude_retrospective=a.exclude_retrospective)


def emit(a, res):
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str) if a.json else RN.text(res), end='' if not a.json else '\n')


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
    c = sub.add_parser('evaluate', help='offline ordinary-search versus graph comparison on synthetic fixtures')
    c.add_argument('--timing', action='store_true', help='also report (non-deterministic) build runtime')
    c = add('suggestions', 'export suggestions for a target with baseline-discoverability flags (pilot hook)'); c.add_argument('node')
    c = add('baseline-search', 'competent structured-ledger search WITHOUT the graph (the pilot baseline arm tool)')
    c.add_argument('campaign'); c.add_argument('observation')
    c = sub.add_parser('adjudications', help='validate a prospective-pilot adjudication log'); c.add_argument('file')
    a = p.parse_args(argv)
    try:
        if a.command == 'demo':
            if a.check:print(json.dumps(demo.check()))
            elif a.write:demo.WALKTHROUGH.write_text(demo.generate(), encoding='utf-8', newline='\n'); print(f'written {demo.WALKTHROUGH.relative_to(demo.ROOT)}')
            else:print(demo.generate(), end='')
            return
        if a.command == 'evaluate':
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:report = E.run(build_all(tmp), timing=a.timing)
            print(M.BANNER); print(E.markdown(report))
            if a.timing:print(f"runtime (not deterministic): {report['runtime_seconds']}")
            return
        if a.command == 'adjudications':print(json.dumps(E.validate_log(a.file))); return
        if a.command == 'baseline-search':
            from src.research.graph import baseline as B
            from src.research.graph import catalogue as Cat
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
            if a.check:info['rebuild_identical'] = build(ledgers=a.ledgers, catalogue_path=a.catalogue, mode=a.mode, known_at=a.known_at,
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
