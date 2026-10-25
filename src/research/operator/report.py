"""One consolidated run report, rendered deterministically from the retained journal alone (no clock, no file reads).

The outcome is never COMPLETE: this profile ends at human Anvil gates. A finished invocation with blocked stages is
STOPPED_AT_BOUNDARY, not success. Costs are what the operator itself incurred (none: no model or network access is
possible inside its boundary); archived costs from earlier runs are quoted from their records and stay UNKNOWN where
those records say so."""
from __future__ import annotations

from src.research.spec import canonical
from . import BANNER, VERSION
from .runs import current_stages, stage_state, write_once

LEGACY_REPORT = 'RESEARCH_OS_OPERATOR_REPORT_V001'
REPORT = 'RESEARCH_OS_OPERATOR_REPORT_V002'
ORDER = ('FAILED', 'INTERRUPTED', 'BLOCKED', 'WAITING_FOR_HUMAN', 'WAITING_FOR_EVIDENCE')
BOUNDARY = ('BLOCKED', 'WAITING_FOR_HUMAN', 'WAITING_FOR_EVIDENCE')
STOP_STAGES = ('DOWNSTREAM',)


def unique(items):
    return list(dict.fromkeys(items))


def _render_v1(events):
    created = events[0]['record']
    stages = current_stages(events)
    _, _, invocations = stage_state(events)
    names = list(stages)  # profile order, as the latest invocation evaluated them
    rows = [{'stage': n, 'status': stages[n]['status'], 'kind': stages[n].get('stage_kind'), 'key': stages[n]['key'],
             'delegated_calls': len(stages[n].get('calls') or []), 'elapsed_seconds': stages[n].get('elapsed_seconds')} for n in names]
    finished = bool(invocations) and invocations[-1]['finished'] is not None
    statuses = {r['status'] for r in rows}
    outcome = 'INTERRUPTED' if not finished or 'INTERRUPTED' in statuses else 'FAILED' if 'FAILED' in statuses else 'STOPPED_AT_BOUNDARY'
    first = next((r for r in rows if r['status'] in ORDER and r['stage'] not in STOP_STAGES), None)
    records = stages.get('FORGE_RECORDS', {}).get('summary') or {}
    research = unique(f for n in names for f in stages[n].get('research_findings') or [])
    software = unique(f for n in names for f in stages[n].get('software_findings') or [])
    actions = unique(a for n in names for a in stages[n].get('next_actions') or [])
    calls = [c for n in names for c in stages[n].get('calls') or []]
    custody = stages.get('FORGE_CUSTODY', {}).get('summary') or {}
    pipeline = records.get('pipeline') or {}
    run = created['run_id']
    next_steps = []
    if outcome == 'INTERRUPTED':
        next_steps.append('Reconcile the interrupted invocation by hand (inspect the journal and any stage output); ONE_SHOT stages are never re-run.')
    elif first:
        next_steps.append(f"Blocked first at {first['stage']} ({first['status']}). After the listed human or evidence input exists: "
                          f'`python -m src.research.operator continue {run}` (add `--evidence <file>` for owner-supplied Quarry inputs).')
    next_steps.append(f'Re-read this report at any time: `python -m src.research.operator report {run}`.')
    report = {
        'schema': LEGACY_REPORT, 'banner': BANNER, 'operator_version': VERSION, 'run_id': run, 'profile': created['profile'],
        'fixture_class': records.get('fixture_class', 'UNKNOWN'), 'journal_head': events[-1]['hash'], 'journal_events': len(events),
        'scope': created['scope'],
        'outcome': outcome,
        'first_boundary': {'stage': first['stage'], 'status': first['status'],
                           'reason': (stages[first['stage']].get('blockers') or stages[first['stage']].get('research_findings')
                                      or stages[first['stage']].get('software_findings') or ['UNKNOWN'])[0]} if first else None,
        'hypothesis': records.get('hypothesis'),
        'stages': rows,
        'evidence': {'original_archive': custody.get('original'), 'critic_workspace': custody.get('critic'),
                     'working_copy_byte_identical': custody.get('byte_identical', False),
                     'criticism': records.get('criticism'),
                     'quarry_packages': {n.split(':', 1)[1]: {'status': stages[n]['status'], **{k: stages[n]['summary'].get(k) for k in ('accuracy', 'excerpts', 'export')}}
                                         for n in names if n.startswith('QUARRY_EXPORT:')},
                     'unavailable': [f for n in names if stages[n]['status'] == 'WAITING_FOR_EVIDENCE' for f in stages[n].get('research_findings') or []]},
        'research_blockers': unique(f for n in names if stages[n]['status'] in BOUNDARY for f in stages[n].get('blockers') or []),
        'software_blockers': unique([f for n in names if stages[n]['status'] in ('FAILED', 'INTERRUPTED') for f in stages[n].get('software_findings') or [f'{n} {stages[n]["status"]}']]
                                    + [f for n in names for f in stages[n].get('software_findings') or [] if 'NOT_IMPLEMENTED' in f]),
        'human_decisions': [a for a in actions if a.startswith(('OWNER', 'HUMAN'))],
        'research_findings': research, 'software_findings': software,
        'integrity': (stages.get('INTEGRITY', {}).get('summary') or {}).get('checks'),
        'accounting': {
            'operator_model_or_provider_calls': 0, 'operator_network_requests': 0, 'operator_processes_started': 0,
            'enforcement': 'audit-hook boundary denies sockets and process creation for the whole invocation',
            'boundary_denials': sum(len(i['finished']['record']['boundary_denials']) for i in invocations if i['finished']),
            'delegated_commands': len(calls), 'operator_cost': 'NONE_INCURRED_BY_THIS_RUN',
            'invocations': [{'command': i['started']['record']['command'], 'started_at': i['started']['at'],
                             'commit': i['started']['record']['execution']['revision']['commit'],
                             'implementation_digest': i['started']['record']['execution']['implementation']['digest'],
                             'finished_at': i['finished']['at'] if i['finished'] else None,
                             'elapsed_seconds': i['finished']['record']['elapsed_seconds'] if i['finished'] else None} for i in invocations],
            'drift_acceptances': [{'at': e['at'], 'from': e['record']['from']['implementation'], 'to': e['record']['to']['implementation']}
                                  for e in events if e['type'] == 'DRIFT_ACCEPTED'],
            'archived_run_accounting': pipeline.get('accounting_totals'), 'archived_actual_charges': 'UNKNOWN',
            'note': 'Archived counts are quoted from the earlier run records ({at_least, exact}); exact UNKNOWN stays UNKNOWN. No cost is inferred.'},
        'friction': {'commands_run_for_the_owner': len(calls), 'hand_authored_inputs_requested': sum(a.startswith(('OWNER', 'HUMAN')) for a in actions),
                     'stages_waiting_for_human': sum(r['status'] == 'WAITING_FOR_HUMAN' for r in rows),
                     'stages_waiting_for_evidence': sum(r['status'] == 'WAITING_FOR_EVIDENCE' for r in rows)},
        'next': next_steps,
        'debug_commands': unique(c['command'] for c in calls),
        'authorises': []}
    return report


def render(events, *, schema=REPORT):
    """V002 is a derived view; V001 remains byte-reproducible and its saved files are never replaced."""
    if schema not in (REPORT, LEGACY_REPORT):
        raise ValueError('unknown operator report schema')
    rep = _render_v1(events)
    if schema == LEGACY_REPORT:
        return rep
    stages = current_stages(events)
    calls = [c for e in events if e['type'] == 'STAGE_FINISHED' for c in e['record']['result'].get('calls', [])]
    rep['schema'] = REPORT
    rep['debug_commands'] = unique(c['command'] for c in calls)
    accounting = rep['accounting']
    accounting.pop('delegated_commands')
    accounting.update(delegated_invocations=len(calls), distinct_commands=len(rep['debug_commands']))
    accounting['delegation_scope'] = 'All retained invocation records; repeated calls count separately. Stage rows show latest results.'
    rep['human_action_groups'] = rep.pop('human_decisions')
    friction = rep['friction']
    friction.pop('commands_run_for_the_owner')
    friction['human_action_groups_requested'] = friction.pop('hand_authored_inputs_requested')
    friction['individual_records'] = 'NOT_EXHAUSTIVELY_COUNTED'
    friction['definition'] = 'Each OWNER/HUMAN action string is one group; a group may require multiple conditional records or files.'
    rep['stage_kinds'] = {
        'CHECK': 'Internal check cached by inputs and implementation binding.',
        'ONE_SHOT': 'Internal action claimed once per input key; interrupted claims are never retried.',
        'DECISION': 'Internal no-action gate result; never a human judgment or research approval.'}
    records = stages.get('FORGE_RECORDS', {}).get('summary') or {}
    evidence = rep['evidence']
    evidence['scout_legacy_critic_records'] = records.get('scout_legacy_critic_records', 'UNKNOWN')
    evidence['critic_v1'] = evidence.pop('criticism')
    searches = (stages.get('ARMOURY_GRAPH', {}).get('summary') or {}).get('search', {})
    rep['armoury_searches'] = searches
    rep['research_findings'] = unique(rep['research_findings'] + [
        f'Armoury search {term!r}: {canonical(value).decode("utf-8")}' for term, value in sorted(searches.items())])
    return rep


def markdown(rep):
    legacy = rep['schema'] == LEGACY_REPORT
    h = rep['hypothesis'] or {}
    out = [f"# Research OS run report: {rep['run_id']} ({rep['outcome']})", '', f"> {rep['banner']}", '']
    if rep['fixture_class'] == 'SYNTHETIC':
        out += ['> **SYNTHETIC FIXTURE RUN.** No real approval, evidence or research result exists in it.', '']
    b = rep['first_boundary']
    out += [f"Profile `{rep['profile']}` | journal `{rep['journal_head'][:16]}` ({rep['journal_events']} events) | fixture class {rep['fixture_class']}", '']
    if b:
        out += [f"**Stopped at {b['stage']} ({b['status']}).** {b['reason']}", '']
    out += ['## Hypothesis under investigation', '']
    if h:
        out += [f"**{h['title']}**", '', f"`{h['idea_id']}` v{h['version']} ({h['versions']} version(s)) | lane {h['lane']} | Scout route {h['route']}", '',
                f"- Question: {h['question']}", f"- Predictor: {h['predictor']['quantity']} ({h['predictor']['units']})",
                f"- Outcome: {h['outcome']['quantity']} ({h['outcome']['units']})", f"- Falsifier: {h['falsifier']}",
                f"- Main uncertainty: {h['main_uncertainty']}", f"- Requirements: {', '.join(h['requirement_ids'])}", '']
    else:
        out += ['Not established (the Forge records stage did not complete).', '']
    out += ['## Stages', '', '| Stage | Status | Kind | Delegated commands |' if legacy else
            '| Stage | Status | Internal execution kind | Calls in latest result |', '|---|---|---|---:|']
    out += [f"| {r['stage']} | {r['status']} | {r['kind']} | {r['delegated_calls']} |" for r in rep['stages']]
    if not legacy:
        out += [''] + [f'- {kind}: {meaning}' for kind, meaning in rep['stage_kinds'].items()]
    sections = (('Research blockers', rep['research_blockers']), ('Software and integration blockers', rep['software_blockers']),
                (('Remaining human decisions', rep['human_decisions']) if legacy else ('Remaining human action groups', rep['human_action_groups'])), ('Research findings', rep['research_findings']),
                ('Software findings', rep['software_findings']))
    for title, items in sections:
        out += ['', f'## {title}', ''] + ([f'- {x}' for x in items] or ['- None recorded.'])
    e = rep['evidence']
    out += ['', '## Evidence inspected or unavailable', '']
    if e['original_archive']:
        o = e['original_archive']
        out.append(f"- Original archive {o['path']}: {o['files']} files, {o['bytes']} bytes, digest `{o['digest'][:16]}`; "
                   f"working copy byte-identical: {e['working_copy_byte_identical']}. The original was never a command target.")
    if (e['critic_workspace'] or {}).get('files'):
        out.append(f"- Critic workspace ({e['critic_workspace']['basis']}): {e['critic_workspace']['files']} files hashed and copied; raw replies are copied byte-for-byte, never parsed or shown.")
    if not legacy:
        out.append(f"- Legacy Scout critic records: {e['scout_legacy_critic_records']}. These are separate from critic-v1 results.")
        critic = e['critic_v1'] or {}
        out.append(f"- critic-v1 selected subject: {critic.get('subject', 'NOT_AVAILABLE')}; imported attempt statuses by request: "
                   + canonical({role: row['attempts'] for role, row in critic.get('requests', {}).items()}).decode('utf-8')
                   + '. No imported attempt means no imported judgment; VALID is response-contract validity, not research approval.')
    for label, q in e['quarry_packages'].items():
        out.append(f"- Quarry {label}: {q['status']}" + (f", {q['excerpts']} excerpt(s), accuracy {q['accuracy']}" if q.get('excerpts') else ''))
    out += [f'- Unavailable: {x}' for x in e['unavailable']]
    if rep['integrity']:
        out.append('- Integrity: ' + ', '.join(f'{k} {v}' for k, v in sorted(rep['integrity'].items())))
    a, f = rep['accounting'], rep['friction']
    out += ['', '## Cost and execution accounting', '',
            '- Approved execution scope: ' + ', '.join(f'{k.replace("_", " ")} {v}' for k, v in sorted(rep['scope'].items())) + '.',
            f"- This run: {a['operator_model_or_provider_calls']} model/provider calls, {a['operator_network_requests']} network requests, "
            f"{a['operator_processes_started']} processes ({a['enforcement']}); boundary denials {a['boundary_denials']}; cost {a['operator_cost']}."]
    if legacy:
        out += [f"- Delegated commands run in-process for the owner: {a['delegated_commands']}; hand-authored inputs still requested: {f['hand_authored_inputs_requested']}."]
    else:
        out += [f"- Total delegated invocations: {a['delegated_invocations']}; distinct commands: {a['distinct_commands']}. {a['delegation_scope']}",
                f"- Human action groups requested: {f['human_action_groups_requested']}. {f['definition']} Individual records have not been exhaustively counted."]
    out += [f"- Invocation `{i['command']}`: {i['started_at']} to {i['finished_at'] or 'NOT FINISHED'} ({i['elapsed_seconds']} s); "
            f"commit `{i['commit'][:12]}`, implementation `{i['implementation_digest'][:12]}`" for i in a['invocations']]
    out += [f"- Implementation drift accepted by the owner at {d['at']}: `{d['from'][:12]}` to `{d['to'][:12]}`; CHECK stages re-ran, ONE_SHOT results kept."
            for d in a['drift_acceptances']]
    if a['archived_run_accounting']:
        out.append('- Archived pipeline run (quoted, not re-measured): ' + ', '.join(f"{k} at least {v['at_least']}, exact {v['exact']}"
                                                                                     for k, v in a['archived_run_accounting'].items()) + f"; actual charges {a['archived_actual_charges']}.")
    out += ['', '## What Research OS can do next', ''] + [f'- {x}' for x in rep['next']]
    title = 'Delegated commands (for debugging)' if legacy else 'Distinct delegated commands (for debugging)'
    out += ['', f'<details><summary>{title}</summary>', '', '```text', *rep['debug_commands'], '```', '', '</details>', '']
    return '\n'.join(out)


def write(layout, rep):
    suffix = '-v002' if rep['schema'] == REPORT else ''
    stem = layout.reports / f"report-{rep['journal_head'][:16]}{suffix}"
    return [write_once(stem.with_suffix('.json'), rep), write_once(stem.with_suffix('.md'), markdown(rep).encode('utf-8'))]


def text(rep):
    return canonical(rep).decode('utf-8')
