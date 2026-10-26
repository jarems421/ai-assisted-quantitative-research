"""Read-only Anvil view; all scientific checks remain native and independently gated."""
from pathlib import Path

from src.research.campaign_v1 import native as N, records as R
from src.research.operator import runs
from src.research.operator.journal import Journal
from src.research.discovery.ledger import Ledger
from src.research.discovery.review import checklist
from src.research.quarry_v1.evidence import validate_export
from src.research.jev_navigation_v1 import workspace as JW, navigation as JN
from . import VERSION
from .continuity import observe_source, implementation

SEAM = {'status': 'NOT_IMPLEMENTED_WAITING_FOR_NATIVE_CUSTODY_BRIDGE', 'dispatch_eligible': False,
        'existing_operator_input': 'RESEARCH_OS_OPERATOR_EVIDENCE_V001.exports: label + existing validated export path',
        'missing': ['VERIFIED_SOURCE_ATTEMPT_RESULT_TO_RECEIPT_BODY_LINK', 'VERIFIED_NATIVE_CUSTODY_RECEIPT',
                    'QUARRY_EXPORT_MANIFEST_AND_EXACT_SCOUT_SUBJECT_BINDING', 'RECONCILED_BRIDGE_INTERFACE'],
        'meaning': 'Export validation alone does not bind it to an attached Source Retrieval attempt.', 'authorises': []}


def operator_view(activity, branch):
    old = {k: v for k, v in activity.items() if k not in ('activity_id', 'state')}
    observed, report = N.observe(old['run'], branch, old)
    R.need(observed == old, 'native operator completion advanced; reconcile through Campaign V001')
    stages = runs.current_stages(Journal(Path(old['run'])).load())
    selected = {k: {'status': v['status'], 'summary': v['summary'], 'blockers': v.get('blockers', [])}
                for k, v in stages.items() if k.startswith(('FORGE_READINESS', 'QUARRY_', 'JEV_EVIDENCE', 'ANVIL_'))}
    for name, s in selected.items():
        if name.startswith('QUARRY_EXPORT:') and s['status'] == 'COMPLETE':
            path = R.path(s['summary']['export'])
            R.need(N.sha(R.read(path / 'manifest.json')) == s['summary']['manifest_sha256'], 'Quarry export changed')
            validate_export(path)
    jev = selected.get('JEV_EVIDENCE', {})
    if jev.get('status') == 'COMPLETE':
        ws = R.path(jev['summary']['workspace'])
        R.need(not (ws / 'response.raw').exists(), 'provider responses are outside this offline checkpoint')
        _, bundle = JW.load(ws)
        rep = JN.report(bundle)
        R.need(rep['request_sha256'] == jev['summary']['request_sha256'], 'Jev evidence binding changed')
    checks = selected.get('ANVIL_CHECKS', {}).get('summary') or {}
    discovery = None
    if checks.get('ledger') and 'checklist' in checks:
        ledger = R.path(checks['ledger'])
        R.need(ledger.is_relative_to(R.path(old['run']) / 'artifacts'), 'Discovery ledger escapes native artifacts')
        workflow = R.loads(R.read(ledger.parent / 'workflow-input.json'))
        context = workflow['context']
        R.need(context['ledger']['path'] == ledger.name and context['ledger']['sha256'] == N.sha(R.read(ledger)),
               'Discovery ledger differs from native workflow input')
        layout = runs.Layout(Path(old['run']).parent.parent, old['run_id'])
        ws = R.path(layout.jev / ('workflow-' + R.digest(workflow)[:8]))
        R.need(not (ws / 'response.raw').exists(), 'workflow provider response refused')
        JW.load(ws)
        state = Ledger(ledger).load()
        discovery = checklist(state, context['candidate_id'], context['candidate_version'])
        R.need({k: {n: v[n] for n in ('mechanical', 'blockers')} for k, v in discovery['requirements'].items()}
               == checks['checklist'], 'Discovery checks changed; native re-evaluation required')
        discovery = {'ledger_sha256': context['ledger']['sha256'], 'fixture': state.fixture, **discovery}
    return {'integrity': 'VERIFIED_NATIVE_COMPLETION', 'state': activity['state'], 'stages': selected,
            'discovery': discovery, 'human_action_groups': report.get('human_action_groups', report.get('human_decisions', [])),
            'scope': 'Existing native outputs; no source-to-Quarry lineage inferred', 'authorises': []}


def render(companion, campaign):
    manifest, events, branches, native, attached = companion.load()
    R.need(companion.campaign.load()[1][-1]['hash'] == campaign['journal_head'], 'campaign changed during checkpoint')
    changed = manifest['binding'] != implementation()
    out = []
    for row in campaign['branches']:
        bid, branch = row['branch_id'], branches[row['branch_id']]
        sources, operators = [], []
        for aid, ref in sorted(attached.items()):
            if ref['branch_id'] != bid:
                continue
            record = {'activity_id': aid, 'reference': ref, 'integrity': 'RECONCILIATION_REQUIRED',
                      'status': ref['status'], 'custody': 'NOT_ESTABLISHED', 'authorises': []}
            try:
                R.need(aid not in native, 'native/source activity identity conflict')
                current, result = observe_source(ref['source_base'], ref['attempt_id'], branch, campaign['campaign_id'])
                R.need(current == ref, 'attached native source reference changed; never overwrite or reattach')
                R.need(not changed, 'IMPLEMENTATION_CHANGED; use pinned companion')
                record.update(integrity='VERIFIED_NATIVE_RESULT', status=result['status'], reason=result['reason'],
                              interrupted=result['interrupted'], consumption=result['consumption'],
                              retained=result['retained'], custody_handoff=result['custody_handoff'],
                              unfinished_requests=result['unfinished_requests'], stop_findings=result['stop_findings'],
                              custody='AWAITING_NATIVE_QUARRY_CUSTODY' if result['custody_handoff'] else 'NO_ELIGIBLE_HANDOFF_RECORDED')
            except (ValueError, OSError, KeyError, TypeError) as error:
                record['problem'] = str(error)
            sources.append(record)
        for activity in row['activities']:
            record = {'activity_id': activity['activity_id'], 'integrity': 'RECONCILIATION_REQUIRED'}
            try:
                R.need(activity['state']['execution_state'] != 'RECONCILIATION_REQUIRED'
                       and not campaign['implementation_changed'], 'native campaign reference requires reconciliation')
                record.update(operator_view(activity, branch))
            except (ValueError, OSError, KeyError, TypeError) as error:
                record['problem'] = str(error)
            operators.append(record)
        needs = ['FIELD_CONFIRMATION_NOT_ESTABLISHED_BY_CUSTODY_OR_NAVIGATION']
        reviews = [o['discovery'] for o in operators if o.get('discovery')]
        if not reviews or any(all(r['human_judgment'] == 'NOT_REVIEWED' for r in d['requirements'].values()) for d in reviews):
            needs.append('HUMAN_M_REVIEW_NOT_RECORDED_IN_LINKED_NATIVE_CHECKLIST')
        readiness = [o['stages'].get('FORGE_READINESS', {}).get('status') for o in operators if 'stages' in o]
        if (readiness and any(s != 'COMPLETE' for s in readiness)) or (not readiness and not row.get('scout_handoff_eligible')):
            needs.append('CURRENT_SCOUT_READY_HANDOFF_REQUIRED_FOR_APPROVED_CONTINUATION')
        links = [o.get('stages', {}).get('ANVIL_CHECKS', {}).get('summary', {}).get('link') for o in operators]
        if not links or not all(isinstance(link, dict) and link.get('status')
                               in ('HUMAN_CROSSWALK_RECORDED', 'SYNTHETIC_CROSSWALK_FIXTURE') for link in links):
            needs.append('HUMAN_CROSSWALK_FOR_SUPPLIED_LEDGER; NOT_REQUIRED_FOR_UNADMITTED_SYNTHETIC_PREVIEW')
        out.append({'branch_id': bid, 'campaign_state': row, 'source_activities': sources, 'operator_checkpoints': operators,
                    'proposed_sources': 'NOT_REGISTERED_BY_THIS_COMPANION; original request descriptor remains disabled',
                    'source_authority': 'NO_CAMPAIGN_AUTHORITY_INFERRED; consult native scope/attempt records',
                    'pending_native_gates': needs, 'source_to_quarry': SEAM, 'research_outcome': None,
                    'next': 'RECONCILE_RETAINED_REFERENCES' if changed or any(r['integrity'] == 'RECONCILIATION_REQUIRED'
                            for r in sources + operators) else 'REVIEW_NATIVE_BLOCKERS_AND_MISSING_CUSTODY_SEAM', 'authorises': []})
    return {'schema': VERSION + '_ANVIL_CHECKPOINT', 'campaign': manifest['campaign'],
            'companion_journal_head': events[-1]['hash'], 'companion_journal_events': len(events),
            'locked': (companion.root / 'companion.lock').exists(), 'implementation_changed': changed,
            'branches': out, 'budgets': {**campaign['budgets'], 'source_costs_aggregated': False,
                'rule': 'Source consumption is quoted per native result; component reservations are never added to campaign allocations.'},
            'downstream': 'NOT_AUTHORISED_STOP_AT_ANVIL', 'authorises': []}
