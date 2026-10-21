"""Text, Mermaid and DOT rendering. Every rendering carries the non-authority banner."""
from __future__ import annotations

import json

from src.research.graph import model as M

CATEGORIES = {
    'verified': ('Verified assertion (original field / documented relationship)', 'fill:#e6f4ea,stroke:#1e7a34,stroke-width:2px'),
    'unverified': ('Recorded but unverified assertion', 'fill:#fff8e1,stroke:#b07d00,stroke-dasharray:5 3'),
    'contradicted': ('Contradicted record', 'fill:#fdecea,stroke:#b3261e,stroke-width:3px'),
    'superseded': ('Superseded version', 'fill:#eeeeee,stroke:#888888,stroke-dasharray:2 2'),
    'historical': ('Historical memory (cited verbatim)', 'fill:#f3e8fd,stroke:#6a3d9a'),
    'claim': ('Claim / hypothesis record', 'fill:#e8f0fe,stroke:#1a56b0'),
    'missing': ('Requirement or blocker (missing evidence)', 'fill:#fdecea,stroke:#b3261e,stroke-dasharray:4 2'),
    'object': ('Economic object / document (neutral)', 'fill:#ffffff,stroke:#444444'),
}


def pretty(value, indent=0):
    pad = ' ' * indent; out = []
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)) and v and not (isinstance(v, list) and all(not isinstance(x, (dict, list)) for x in v) and len(str(v)) < 110):
                out.append(f'{pad}{k}:'); out += pretty(v, indent + 2)
            else:out.append(f'{pad}{k}: {short(v)}')
    elif isinstance(value, list):
        for v in value:
            if isinstance(v, (dict, list)):
                sub = pretty(v, indent + 2)
                out.append(pad + '- ' + sub[0].lstrip() if sub else pad + '-'); out += sub[1:]
            else:out.append(f'{pad}- {short(v)}')
    else:out.append(pad + short(value))
    return out


def short(v):
    if isinstance(v, list):return ', '.join(str(x) for x in v) if v else '[]'
    return str(v)


def text(res):
    lines = [res['banner'], f"{res['operator']}: {res['input']}  (mode={res['mode']}" + (f", known_at={res['known_at']}" if res['known_at'] else '') + ')']
    view = res.get('view') or {}
    active = {k: v for k, v in view.items() if v}
    if active:lines.append(f'view filters: {active}')
    for key in ('definition', 'does_not_mean', 'bounds'):
        if res.get(key):lines.append(f'{key}: {short(res[key]) if not isinstance(res[key], dict) else res[key]}')
    for i, r in enumerate(res['results'], 1):
        lines.append(f'[{i}]'); lines += pretty(r, 2)
    for key in ('leads', 'rejected', 'excluded_inputs'):
        if res.get(key):
            lines.append(f'{key}:'); lines += pretty(res[key], 2)
    for a in res['abstentions']:lines.append(f"ABSTAIN {a['code']}: {a['reason']}")
    for n in res['notes']:lines.append(f'note: {n}')
    return '\n'.join(lines) + '\n'


def category(g, nid):
    n, s = g.nodes[nid], g.display_status(nid)
    if s == M.SUPERSEDED:return 'superseded'
    if s == M.CONTRADICTED:return 'contradicted'
    if n['kind'] in M.ASSERTION_KINDS:return 'verified' if s in M.VERIFIED_ASSERTIONS else 'unverified'
    if n['kind'].startswith('history'):return 'historical'
    if n['kind'] == 'claim':return 'claim'
    if n['kind'] in ('requirement', 'blocker'):return 'missing'
    return 'object'


def label(g, nid, width=48):
    n = g.nodes[nid]; text_ = n['label'] if len(n['label']) <= width else n['label'][:width - 3] + '...'
    tag = '[SYNTHETIC] ' if n['fixture'] == 'SYNTHETIC' else ''
    status = g.display_status(nid) or ''
    return f"{tag}{n['kind']}: {text_}" + (f"<br/>{status}" if status else '')


def subgraph(g, res):
    """Nodes and edge indexes to draw for a neighbourhood, explanation or trace result."""
    nodes, edges = set(), set()
    if res['operator'] == 'neighbourhood':
        r = res['results'][0]; nodes |= set(r['nodes']); edges |= set(r['edges'])
    elif res['operator'] == 'explain':
        for p in res['results'][:3]:
            nodes |= set(p['nodes'])
            for k in range(len(p['nodes']) - 1):
                a, b = p['nodes'][k], p['nodes'][k + 1]
                edges |= {i for i in g.adj[a] if {g.edges[i]['src'], g.edges[i]['dst']} == {a, b}}
    elif res['operator'] == 'trace':
        anchors = [r.get('claim') or r.get('investigation') for r in res['results']]
        for a in anchors:
            nodes.add(a)
            for i in g.adj[a]:
                e = g.edges[i]; other = e['dst'] if e['src'] == a else e['src']
                if g.nodes[other]['kind'] in ('campaign', 'document'):continue
                nodes.add(other); edges.add(i)
    else:raise ValueError('export supports neighbourhood, explain and trace results')
    nodes = sorted(nodes)[:M.MAX_NODES]; keep = set(nodes)
    return nodes, sorted(i for i in edges if g.edges[i]['src'] in keep and g.edges[i]['dst'] in keep)


def mermaid(g, res):
    nodes, edges = subgraph(g, res)
    ids = {n: f'n{i}' for i, n in enumerate(nodes)}
    out = [f'%% {M.BANNER}', f"%% {res['operator']}: {res['input']} (mode={res['mode']})", 'flowchart LR',
           f'  banner["{M.BANNER}"]:::missing']
    for n in nodes:out.append(f'  {ids[n]}["{label(g, n).replace(chr(34), chr(39))}"]:::{category(g, n)}')
    for i in edges:
        e = g.edges[i]; arrow = '-->' if e['kind'] in ('SUBJECT', 'OBJECT') else '-.->'
        out.append(f"  {ids[e['src']]} {arrow}|{e['kind']}| {ids[e['dst']]}")
    out.append('  subgraph legend [Legend]')
    for key, (text_, _) in CATEGORIES.items():out.append(f'    legend_{key}["{text_}"]:::{key}')
    out.append('  end')
    out += [f'  classDef {key} {style}' for key, (_, style) in CATEGORIES.items()]
    out.append('  %% Solid arrows: relationship subject/object (semantic). Dotted: structural links.')
    return '\n'.join(out) + '\n'


def dot(g, res):
    nodes, edges = subgraph(g, res)
    colours = {'verified': '#1e7a34', 'unverified': '#b07d00', 'contradicted': '#b3261e', 'superseded': '#888888', 'historical': '#6a3d9a',
               'claim': '#1a56b0', 'missing': '#b3261e', 'object': '#444444'}
    out = [f'// {M.BANNER}', 'digraph research_view {', '  rankdir=LR; node [shape=box, fontsize=10];',
           f'  label="{M.BANNER}"; labelloc=t;']
    for n in nodes:
        c = category(g, n); style = 'dashed' if c in ('unverified', 'superseded', 'missing') else 'solid'
        out.append(f'  "{n}" [label={json.dumps(label(g, n).replace("<br/>", " | "))}, color="{colours[c]}", style={style}];')
    for i in edges:
        e = g.edges[i]; style = 'solid' if e['kind'] in ('SUBJECT', 'OBJECT') else 'dotted'
        out.append(f'  "{e["src"]}" -> "{e["dst"]}" [label="{e["kind"]}", style={style}];')
    out.append('}')
    return '\n'.join(out) + '\n'
