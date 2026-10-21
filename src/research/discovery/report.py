"""Readable campaign summaries and descriptive cross-method comparison.

The comparison reports counts with their denominators and keeps unknown costs unknown. It never
combines metrics into a score, ranks methods or attaches statistical confidence to small campaigns.
"""
from __future__ import annotations

from src.research.discovery import records as R
from src.research.discovery.ledger import totals
from src.research.discovery.review import checklist, source_next

BANNERS = {'SYNTHETIC': '> **Synthetic fixture.** Fabricated records that exercise the workflow; nothing here is real-world evidence.',
           'RETROSPECTIVE_INSPECTED': '> **Retrospective, previously inspected.** Existing repository evidence at its recorded depth; '
                                      'unsuitable for untouched validation and not a re-adjudication of the original decision.',
           'LIVE': '> **Live campaign.** Records must cite real, authorised evidence.'}


def cell(value):
    return str(value).replace('|', '/').replace('\n', ' ')


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows]
    return '\n'.join(out)


def cost(t):
    if not t['entries']:return 'UNKNOWN (no effort recorded)'
    return f"{t['known']}" + (f" + {t['unknown_entries']} UNKNOWN" if t['unknown_entries'] else '')


def original_latest(s, cid):
    """Latest version of the original claim lineage; material reformulations are counted separately."""
    found = [v for v in s.versions['candidate'][cid] if s.derived[('candidate', cid, v['version'])]['claim_class'] == 'ORIGINAL']
    return found[-1] if found else None


def latest_disposition(s, cid, version=None):
    found = [d for d in s.dispositions if d['candidate_id'] == cid and (version is None or d['version'] == version)]
    return found[-1] if found else None


def promoted(s):
    used = set()
    for versions in s.versions['candidate'].values():
        for c in versions:used.update(c['predictor']['observation_ids'] + c['outcome']['derived_from_observations'])
    return used


def first_public(o):
    v = o['clocks']['first_public']['value']
    return v if v != R.UNKNOWN else 'UNKNOWN'


def summary(s):
    c = s.campaign; t = totals(s.efforts); b = c['budget']; used = promoted(s)
    lines = [f"# {c['id']}: {c['title']}", '', BANNERS[c['fixture']], '',
             f"**Method:** {c['method']}; **authority:** {c['authority']}; **acquisition authorised:** {c['acquisition_authorized']}", '',
             f"**Question:** {c['question']}", '',
             table(['Budget', 'Allowed', 'Recorded'], [
                 ['Analyst minutes', b['analyst_hours'] * 60, cost(t['analyst_minutes'])],
                 ['Source starts', b['source_starts'], cost(t['source_starts'])],
                 ['External bytes', b['external_bytes'], cost(t['bytes'])]]), '']
    if s.versions['source']:
        lines += ['## Source passports', '', table(['Source', 'Access', 'Next evidence rung', 'Why'], [
            [f"{p['id']} v{p['version']}", p['access']['status'], *source_next(p)] for p in (v[-1] for v in s.versions['source'].values())]), '']
    if s.versions['observation']:
        lines += ['## Observations', '', table(['Observation', 'Kind', 'Depth', 'As-of status', 'Value', 'Units', 'First public', 'Used by a claim'], [
            [f"{o['id']} v{o['version']}", o['kind'], o['depth'], o['as_of_status'], o['value'], o['units'], first_public(o),
             'yes' if o['id'] in used else 'no (observation only)'] for o in (v[-1] for v in s.versions['observation'].values())]), '']
    if s.versions['relationship']:
        lines += ['## Relationships', '', table(['Relationship', 'Type', 'Basis', 'Status', 'Quantity transfer'], [
            [f"{r['id']} v{r['version']}", r['type'], r['basis'], r['status'], f"{r['quantity_transfer']['status']} ({r['quantity_transfer']['method']})"]
            for r in (v[-1] for v in s.versions['relationship'].values())]), '']
    if s.versions['candidate']:
        rows = []
        for cid, versions in s.versions['candidate'].items():
            for v in versions:
                d = s.derived[('candidate', cid, v['version'])]; ck = checklist(s, cid, v['version'])
                blocked = [k for k, r in ck['requirements'].items() if r['blockers']]
                disp = latest_disposition(s, cid, v['version'])
                rows.append([f"{cid} v{v['version']}", d['revision_kind'], d['claim_class'] + (' / post-outcome' if d['post_outcome'] else ''),
                             'yes' if ck['frozen'] else 'no', ', '.join(blocked) or 'none (human judgment still required)',
                             ck['h_human_judgment'], disp['decision'] if disp else 'NONE'])
        lines += ['## Candidate claims', '', table(['Claim', 'Revision', 'Class', 'Frozen', 'Requirements with mechanical blockers',
                                                    'Human H', 'Disposition'], rows), '']
        for cid in s.versions['candidate']:
            ck = checklist(s, cid); nxt = ck['next']
            lines += [f"**{cid} v{ck['version']} next step:** {nxt['requirement'] or 'review'}: `{nxt['blocker']}`. {nxt['instruction']}", '']
    if s.reviews:
        lines += ['## Reviews', '', table(['Review', 'Claim', 'Kind', 'Reviewer', 'Result', 'Not checked'], [
            [r['id'], f"{r['candidate_id']} v{r['version']}", r['kind'] + (f"/{r['role']}" if r['role'] else ''), r['reviewer']['kind'],
             review_result(r), ', '.join(sorted({n['category'] for n in r['not_checked']})) or '-'] for r in s.reviews]), '']
    if s.dispositions:
        lines += ['## Human dispositions', '', table(['Disposition', 'Claim', 'Decision', 'Reason type', 'Scope'], [
            [d['id'], f"{d['candidate_id']} v{d['version']}", d['decision'], d['reason_type'], d['scope']] for d in s.dispositions]), '']
        for d in s.dispositions:
            if d['verify']:lines += [f"**{d['id']} proposed check (not authorised):** {d['verify']['proposed_check']}", '']
    observed = len(s.versions['observation']); claims = len(s.versions['candidate'])
    stopped = sum(1 for cid in s.versions['candidate'] if (latest_disposition(s, cid) or {}).get('decision') in ('REJECT', 'HOLD'))
    lines += ['## Denominators', '', f"- Observations recorded: {observed}; used by a claim: {len(used & set(s.versions['observation']))}.",
              f"- Candidate claims: {claims}; claim versions: {sum(len(v) for v in s.versions['candidate'].values())}; "
              f"stopped (REJECT/HOLD): {stopped}; without any disposition: {sum(1 for cid in s.versions['candidate'] if not latest_disposition(s, cid))}.",
              f"- Effort entries: {len(s.efforts)}; unknown costs are shown as UNKNOWN, never as zero.", '']
    return '\n'.join(lines)


def review_result(r):
    if r['kind'] == 'M':return ', '.join(f"{k}={v['judgment']}" for k, v in r['judgments'].items())
    if r['kind'] == 'H':return r['judgments']['judgment']
    return r['judgments']['verdict']


def metrics(s):
    """Descriptive counts for one campaign. Each value is an integer count or a cost with unknown entries."""
    originals = {cid: original_latest(s, cid) for cid in s.versions['candidate']}
    latest = [c for c in originals.values() if c]
    lists = {cid: checklist(s, cid, c['version']) for cid, c in originals.items() if c}
    disp = {cid: latest_disposition(s, cid) for cid in s.versions['candidate']}
    m_passed = [d for d in s.dispositions if d['decision'] == 'M_PASSED']
    m_class = lambda d: s.derived[('candidate', d['candidate_id'], d['version'])]['claim_class']
    stopped_ids = {cid for cid, d in disp.items() if d and d['reason_type'] in ('OBSERVATION', 'ACCESS')}
    duplicated = {d['candidate_id'] for d in s.dispositions if d['reason_type'] == 'COMPETITION'}
    duplicated |= {r['candidate_id'] for r in s.reviews if r['role'] == 'information' and r['judgments']['verdict'] == 'FATAL_TO_CLAIM'}
    return {
        'campaigns': 1,
        'observations recorded': len(s.versions['observation']),
        'distinctive predictors observed in an original field': sum(1 for v in s.versions['observation'].values() if v[-1]['depth'] == 'VERIFIED_ORIGINAL_FIELD'),
        'documented relationships verified': sum(1 for v in s.versions['relationship'].values() if v[-1]['status'] == 'VERIFIED'),
        'candidate claims formed': len(s.versions['candidate']),
        'material reformulations': sum(1 for k, d in s.derived.items() if k[0] == 'candidate' and d['revision_kind'] == 'MATERIAL_REVISION'),
        'original claims with an observed independent outcome': sum(1 for c in latest if c['outcome']['status'] == 'OBSERVED_VALUE'),
        'original claims with no mechanical M blocker': sum(1 for ck in lists.values() if not any(r['blockers'] for r in ck['requirements'].values())),
        'human M reviews evidencing all six': sum(1 for r in s.reviews if r['kind'] == 'M' and R.human_equivalent(r['reviewer']['kind'], s.fixture)
                                                  and all(j['judgment'] == 'EVIDENCED' for j in r['judgments'].values())),
        'M PASSED (original claims)': sum(1 for d in m_passed if m_class(d) == 'ORIGINAL'),
        'M PASSED (reformulations)': sum(1 for d in m_passed if m_class(d) == 'REFORMULATION'),
        'H judged plausible by a human': sum(1 for r in s.reviews if r['kind'] == 'H' and R.human_equivalent(r['reviewer']['kind'], s.fixture)
                                             and r['judgments']['judgment'] == 'PLAUSIBLE'),
        'claims duplicating an existing interpretation': len(duplicated),
        'claims stopped (REJECT/HOLD)': sum(1 for d in disp.values() if d and d['decision'] in ('REJECT', 'HOLD')),
        'VERIFY proposals recorded': sum(1 for d in s.dispositions if d['decision'] == 'VERIFY'),
        'claims without a disposition': sum(1 for d in disp.values() if not d),
        'analyst minutes': totals(s.efforts)['analyst_minutes'],
        'source starts': totals(s.efforts)['source_starts'],
        'external bytes': totals(s.efforts)['bytes'],
        'analyst minutes on claims stopped for missing observations or access': dict(
            totals([e for e in s.efforts if e['candidate_id'] in stopped_ids])['analyst_minutes'], entries=len(s.efforts)),
    }


def combine(rows):
    out = {}
    for row in rows:
        for k, v in row.items():
            if isinstance(v, dict):
                prev = out.get(k, {'known': 0, 'unknown_entries': 0, 'entries': 0})
                out[k] = {f: prev[f] + v[f] for f in prev}
            else:out[k] = out.get(k, 0) + v
    return out


def per_pass(m):
    passes, minutes = m['M PASSED (original claims)'], m['analyst minutes']
    if passes == 0:return 'undefined (0 original M passes)'
    if not minutes['entries']:return 'UNKNOWN (no effort recorded)'
    if minutes['unknown_entries']:return f"UNKNOWN ({minutes['unknown_entries']} effort entries without time)"
    return f"{minutes['known'] / passes:g}"


def compare(states):
    """Descriptive comparison grouped by fixture class; fixtures are never mixed in one table."""
    lines = ['# Discovery method comparison', '',
             'Descriptive counts with denominators. No composite score, ranking or statistical inference is computed: '
             'small exploratory campaigns cannot establish a difference between methods. A method comparison needs equal '
             'starting budgets and a separately authorised live campaign set.', '']
    for fixture in R.FIXTURES:
        group = [s for s in states if s.fixture == fixture]
        if not group:continue
        methods = [m for m in R.METHODS if any(s.campaign['method'] == m for s in group)]
        budgets = {(s.campaign['budget']['analyst_hours'], s.campaign['budget']['source_starts'], s.campaign['budget']['external_bytes']) for s in group}
        by_method = {m: combine(metrics(s) for s in group if s.campaign['method'] == m) for m in methods}
        lines += [f'## {fixture} campaigns', '', BANNERS[fixture], '',
                  f"Starting budgets {'are equal' if len(budgets) == 1 else 'DIFFER; rows are not like-for-like'}: "
                  + '; '.join(f'{h} analyst hours / {n} starts / {x} bytes' for h, n, x in sorted(budgets)) + '.', '']
        keys = list(next(iter(by_method.values())))
        rows = [[k, *[cost(by_method[m][k]) if isinstance(by_method[m][k], dict) else by_method[m][k] for m in methods]] for k in keys]
        rows.append(['analyst minutes per original M pass', *[per_pass(by_method[m]) for m in methods]])
        lines += [table(['Count', *methods], rows), '']
        claims = ', '.join(f"{m} {by_method[m]['candidate claims formed']}" for m in methods)
        lines += [f'Claims per method: {claims}. Exploratory description only; any difference is an anecdote until a '
                  'pre-registered comparison with equal budgets and untouched live campaigns is separately authorised.', '']
    return '\n'.join(lines)
