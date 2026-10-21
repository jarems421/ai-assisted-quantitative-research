"""Reproducible offline Graph v1 walkthrough (demos A-F plus the utility check).

Demos A-C read the real historical-memory catalogue. Demos D-F and the hypothetical part of A use
fully synthetic ledgers, isolated in synthetic mode. Runs under the repository network guard with a
fixed synthetic clock, so the walkthrough regenerates byte-for-byte.
"""
from __future__ import annotations

import hashlib
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from src.research.discovery.demo import Clock
from src.research.graph import evaluate as E
from src.research.graph import model as M
from src.research.graph import operators as O
from src.research.graph import render as RN
from src.research.graph.fixtures import build_all
from src.research.graph.project import build
from src.research.graph.rules import View
from src.research.sec_pilot.parsing import offline

ROOT = Path(__file__).resolve().parents[3]
WALKTHROUGH = ROOT / 'docs/strategy/graph_v1_walkthrough.md'
V = View()


def bullets(items):
    return [f'- {x}' for x in items] or ['- (none)']


def demo_a(memory, synthetic_memory):
    lines = ['## Demo A: F01 salmon treatment capacity (historical memory)', '']
    t = O.trace(memory, 'HIST-F01')['results'][0]
    lines += [f"Recorded verdict: **{t['verdict']['text']}** ({t['verdict']['status_class']}); citation status {t['citation_status']}.",
              f"Scope: {t['verdict']['scope']}", '', 'Recorded findings (cited verbatim; the graph adds none):', '']
    for c in t['claims']:
        lines += bullets(f"{f['kind']}: {f['text']} -> {f['requirement'] or 'no requirement mapping'}" for f in c['findings'])
    salmon_obs = [k for k, n in memory.nodes.items() if n['kind'] == 'observation' and 'F01' in str(n['origin'])]
    lines += ['', f'Observation records attributed to F01 in the graph: {len(salmon_obs)}. Historical memory is not converted into '
                  'treatment, capacity or allocation observations; vessel visits remain recorded visits.', '']
    gap = O.same_gap(memory, 'REQ_AVAILABLE_CAPACITY', V)
    lines += ['`same-gap REQ_AVAILABLE_CAPACITY` (shared missing measurement, not an economic link):', '']
    lines += bullets(f"{r['claim']} [{r['status']}] via {', '.join(r['link_bases'])}: {'; '.join(r['why_blocked'])}" for r in gap['results'])
    rev = O.revisit(synthetic_memory, 'DLC-GSYN-S', V)
    lines += ['', 'Hypothetical future observation (**synthetic**, `DLC-GSYN-S`): a booking register tagged as measuring available capacity.',
              '`revisit DLC-GSYN-S` in synthetic mode with historical memory loaded:', '']
    for r in rev['results']:
        lines += [f"- {r['match']}: strength **{r['strength']}**, candidate only {r['candidate_only']}, identity {r['identity']}, "
                  f"previous status stands: `{r['previous_status']}`", f"  - not yet verified: {'; '.join(r['not_yet_verified'])}"]
    lines += ['', 'The lead is a requirement-category candidate only. It does not show the register measures F01 capacity, shares any '
                  'identifier with F01 records, or existed historically; F01 is not reopened and no work is authorised.', '']
    return lines


def demo_b(memory):
    lines = ['## Demo B: SH09 offshore predecessor obligations (historical memory)', '']
    t = O.trace(memory, 'HIST-SH09')['results'][0]
    lines += [f"Recorded verdict: **{t['verdict']['text']}** ({t['verdict']['status_class']}).", '', 'Documents recorded by hash, with receipt status:', '']
    for d in t['documents']:
        n = memory.nodes[d]['attrs']
        lines.append(f"- `{d.split(':')[-1][:16]}...` {n['locators'][0][:90]} ({', '.join(n.get('receipt_status', []))})")
    lines += ['', '`gaps history:HIST-SH09/claim-v1` (missing links shown as recorded; none filled):', '']
    lines += bullets(f"{r['state']}: {r['link']} -> {r['requirement'] or '-'}" for r in O.gaps(memory, 'history:HIST-SH09/claim-v1')['results'])
    ex = O.explain(memory, 'HIST-SH09', 'CIK:0000093410', V)
    p = ex['results'][0]
    lines += ['', '`explain HIST-SH09 CIK:0000093410`:', '',
              f"- path: {' -> '.join(p['nodes'])} ({p['semantic_hops']} semantic hops, {p['structural_edges']} structural edge)",
              f"- first unsupported leap: **{p['first_unsupported_leap']['code']}**: {p['first_unsupported_leap']['detail']}",
              f"- connectivity only: {p['connectivity_only']}; exposure certified: {p['exposure_certified']}", '',
              'No lease list, security allocation or predecessor-obligation assertion exists anywhere in the graph, so there is no path that '
              'could demonstrate Chevron exposure. The recorded access denials (HTTP 403) remain stops.', '']
    return lines


def demo_c(memory):
    lines = ['## Demo C: EF06 claim versioning (historical memory)', '']
    t = O.trace(memory, 'HIST-EF06')['results'][0]
    lines += [f"Recorded verdict: **{t['verdict']['text']}**", '', '| Version | Economic object | Basis | Reformulates | Counts as original | Recorded status |',
              '|---|---|---|---|---|---|']
    for c in t['claims']:
        lines.append(f"| v{c['version']} | {c['object']} | {c['financial_basis']} | {c['reformulates'] or '-'} | {c['counts_as_original']} | "
                     f"{'; '.join(s['text'] for s in c['recorded_status'])} |")
    fails = [r for r in O.failures(memory, V)['results'] if r['node'] == 'history:HIST-EF06']
    lines += ['', f"`failures` lists EF06 as: {fails[0]['decision']} (requirements {', '.join(fails[0]['requirements'])}).",
              'v2 is a post-observation reformulation of a gross group object; its restricted M pass is never an original v1 success, and the '
              'recorded investment limitation (issuer already explains the book) is preserved verbatim.', '']
    return lines


def demo_d(g):
    lines = ['## Demo D: cross-campaign synthetic discovery', '',
             'Campaign A (relationship-first) records a documented take-or-pay dependency between `SYN_LISTED:ECHO` and `SYN_FACILITY:T-7` and '
             'holds a claim blocked by current-period throughput. Campaign B, recorded later, observes Terminal Seven throughput. '
             'The query names only campaign B.', '', '```text', RN.text(O.revisit(g, 'DLC-GSYN-B', V)).rstrip(), '```', '']
    comp = O.complements(g, 'OBS-GB-1', V)
    for r in comp['results'][:2]:
        lines += [f"`complements OBS-GB-1` -> {r['match']} ({', '.join(r['match_bases'])}): still required: {'; '.join(r['still_required'])}"]
    ex = O.explain(g, 'OBS-GB-1', 'SYN_LISTED:ECHO', V)
    p = ex['results'][0]
    lines += ['', '`explain OBS-GB-1 SYN_LISTED:ECHO` (best path):', '']
    lines += bullets(f"{s['edge']} ({s['connection']}) -> {s['to']}: {s['establishes']}" for s in p['steps'])
    lines += [f"- first unsupported leap: **{p['first_unsupported_leap']['code']}**: {p['first_unsupported_leap']['detail']}", '',
              'Focused Mermaid export of that explanation:', '', '```mermaid', RN.mermaid(g, ex).rstrip(), '```', '']
    return lines


def demo_e(g):
    lines = ['## Demo E: false-positive rejection', '']
    rev = O.revisit(g, 'DLC-GSYN-C', V)
    lines += [f"`revisit DLC-GSYN-C`: {len(rev['results'])} suggestions; abstention {rev['abstentions'][0]['code'] if rev['abstentions'] else '-'}.", '', 'Rejected candidates:', '']
    lines += bullets(f"{x['code']}: {x.get('node')} " + (f"(words {', '.join(x['shared_words'])})" if x.get('shared_words') else x.get('tag', ''))
                     + (f" for {x['observation'].split('/')[-1]}" if x.get('observation') else '') for x in rev['rejected'])
    for oid in ('OBS-GC-2', 'OBS-GC-3', 'OBS-GC-4'):
        c = O.complements(g, oid, V)
        lines.append(f"- `complements {oid}`: " + '; '.join([f"{a['code']}: {a['reason']}" for a in c['abstentions']]
                                                            + [f"{x['code']}: {x['node']}" for x in c.get('rejected', []) if x['code'] != 'ONLY_SHARED_KEYWORD']))
    issues = sorted({i['code'] for i in g.issues})
    lines += ['', f"Build issues surfaced (never auto-resolved): {', '.join(issues)}.", '']
    return lines


def demo_f(paths):
    lines = ['## Demo F: growth over time', '']
    ledgers = [paths['A'], paths['C']]
    before_bytes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()}
    g1 = build(ledgers, mode='synthetic', with_memory=False)
    g2 = build(ledgers + [paths['B']], mode='synthetic', with_memory=False)
    g2b = build(ledgers + [paths['B']], mode='synthetic', with_memory=False)
    preserved = all(g2.nodes.get(k) == n for k, n in g1.nodes.items() if 'DLC-GSYN-A' in str(n['origin']))
    docs = [k for k in g2.nodes if k.startswith('document:')]
    cites = sum(1 for e in g2.edges if e['kind'] == 'CITES')
    appended = g2.nodes['campaign:DLC-GSYN-B']['origin']['appended_at_utc']
    cutoff = (datetime.fromisoformat(appended) - timedelta(seconds=1)).isoformat()
    earlier = build(ledgers + [paths['B']], mode='synthetic', with_memory=False, known_at=cutoff)
    after_bytes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()}
    new = O.revisit(g2, 'DLC-GSYN-B', V)['results']
    lines += ['| Build | Nodes | Edges | Digest |', '|---|---|---|---|',
              f'| Campaigns A and C | {len(g1.nodes)} | {len(g1.edges)} | `{g1.digest()[:16]}` |',
              f'| After campaign B becomes available | {len(g2.nodes)} | {len(g2.edges)} | `{g2.digest()[:16]}` |', '',
              f'- Existing campaign A nodes identical before and after: {preserved}.',
              f'- New observation discoverable and useful: {len(new)} suggestion(s); first match {new[0]["match"]} ({new[0]["strength"]}).',
              f'- {cites} evidence citations resolve to {len(docs)} document nodes keyed by content hash; ledgers are read, never copied or rewritten.',
              f'- Deterministic rebuild: identical digest {g2.digest() == g2b.digest()}.',
              f'- Authoritative ledgers unchanged by building and querying: {before_bytes == after_bytes}.',
              f"- Known-at filter: campaign B was appended at {appended}. A build known at {cutoff} includes "
              f"{[x['campaign'] for x in earlier.inputs]} and excludes {[x['campaign'] for x in earlier.excluded]} "
              '(campaign C was also appended later). Transcription or append time is never backdated.', '']
    return lines


def demo_hub(paths):
    g = build([paths['H']], mode='synthetic', with_memory=False)
    ex = O.explain(g, 'OBS-GH-00', 'OBS-GH-01', V)
    nb = O.neighbourhood(g, 'OBS-GH-00', V)['results'][0]
    return ['## Hub suppression', '',
            f"Thirty routine notices about one regulator: `explain OBS-GH-00 OBS-GH-01` -> {ex['abstentions'][0]['code'] if ex['abstentions'] else 'path found'}; "
            f"the neighbourhood of one notice shows {len(nb['nodes'])} nodes and does not expand these as bridges: "
            f"{', '.join(sorted({c['node'].split(':')[0] + ':' + c['node'].split(':')[-1][:12] + ' (' + c['reason'] + ')' for c in nb['collapsed']}))}. "
            'Sharing a busy regulator or a common clock document is not a discovery.', '']


def run(directory):
    directory = Path(directory)
    with offline():
        paths = build_all(directory, Clock())
        memory = build(ledgers=[])
        synthetic_memory = build([paths['S']], mode='synthetic', with_memory=True)
        g = build([paths['A'], paths['B'], paths['C']], mode='synthetic', with_memory=False)
        report = E.run(paths)
        lines = ['# Graph v1 offline walkthrough', '', f'> {M.BANNER}', '',
                 'Generated by `python -m src.research.graph demo --write`; verified by `demo --check`. A fixed synthetic clock makes it '
                 'byte-reproducible, and everything runs under the repository network guard. Demos A-C read the historical-memory catalogue '
                 '(cited reports, verbatim verdicts). Demos D-F and the hypothetical lead in A use fully synthetic ledgers in synthetic mode. '
                 f"Memory-mode graph: {len(memory.nodes)} nodes, {len(memory.edges)} edges, digest `{memory.digest()[:16]}`. "
                 'See the [guide](graph_v1_guide.md) and [design](graph_v1_design.md).', '']
        lines += demo_a(memory, synthetic_memory) + demo_b(memory) + demo_c(memory) + demo_d(g) + demo_e(g) + demo_f(paths) + demo_hub(paths)
        lines += ['## Utility check: ordinary search versus the graph', '', E.markdown(report), '']
    return '\n'.join(lines).rstrip() + '\n'


def generate():
    with tempfile.TemporaryDirectory() as tmp:return run(tmp)


def check():
    if not WALKTHROUGH.exists() or WALKTHROUGH.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/graph_v1_walkthrough.md differs from the generated walkthrough; run demo --write')
    return {'walkthrough': 'PASS', 'network': 'blocked', 'acquisition': 0}
