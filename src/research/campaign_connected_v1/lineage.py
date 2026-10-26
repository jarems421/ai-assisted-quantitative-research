"""References only: native Source, custody, Quarry, operator and Discovery remain authoritative.

No acquisition, import, operator invocation, repair or replay occurs in this module.
"""
from pathlib import Path

from src.research.campaign_v1 import records as R, native as N
from src.research.campaign_evidence_v1.continuity import Companion, observe_source, implementation as companion_binding
from src.research.campaign_evidence_v1.checkpoint import operator_view
from src.research.operator import adapters
from src.research.operator.guard import offline
from src.research.source_v1 import store as S
from src.research.quarry_v1 import evidence as Q
from src.research.jev_navigation_v1 import workspace as J
from src.research.opportunity_scout.storage import Archive
from . import VERSION


def custody_api():
    # PR #46 is a required native dependency, never replaced by a portable-package guess.
    try:
        from src.research.source_custody_v1 import custody
    except ModuleNotFoundError as error:
        if error.name != 'src.research.source_custody_v1':
            raise
        raise ValueError('NATIVE_CUSTODY_DEPENDENCY_MISSING') from error
    return custody


def implementation():
    x = custody_api()
    return {'connected': R.digest({p.name: N.sha(p.read_bytes().replace(b'\r\n', b'\n'))
                                   for p in sorted(Path(__file__).parent.glob('*.py'))}),
            'companion': companion_binding(),
            'custody': R.digest({p.name: N.sha(p.read_bytes().replace(b'\r\n', b'\n'))
                                 for p in sorted(Path(x.__file__).parent.glob('*.py'))})}


def file_ref(path):
    path = R.path(path)
    return {'path': str(path), 'sha256': N.sha(R.read(path))}


def inspect(selection):
    """Reconstruct the exact chain using native verifiers, without choosing another activity.

    Selection is an explicit reference to retained activities, not a request/result schema
    for source discovery, an authority record or an instruction to run anything.
    """
    R.need(set(selection) == {'campaign', 'branch', 'source_activity', 'url', 'package', 'export', 'operator_activity'},
           'exact lineage selection fields required')
    companion = Companion(selection['campaign'])
    # Public status owns its offline context; never nest the operator's global guard.
    campaign = companion.campaign.status()
    with offline([]):
        manifest, events, branches, _, attached = companion.load(mutable=True)
        R.need(not campaign['implementation_changed'] and not (companion.root / 'companion.lock').exists(),
               'campaign/companion requires reconciliation')
        branch = branches[selection['branch']]
        ref = attached[selection['source_activity']]
        R.need(ref['branch_id'] == branch['branch_id'], 'source activity belongs to another branch')
        current, result = observe_source(ref['source_base'], ref['attempt_id'], branch, campaign['campaign_id'])
        R.need(current == ref, 'attached source reference changed')
        # This integration does not promote partial/uncertain results into a complete chain.
        # Native custody can retain them independently; they remain legitimate negative records.
        R.need(result['status'] == 'COMPLETE' and not result['interrupted'], 'COMPLETE_RETRIEVAL_REQUIRED')
        x = custody_api()
        ctx = x.preflight(ref['source_base'], ref['attempt_id'], selection['url'])
        R.need((ctx['request_sha256'], ctx['result_sha256']) == (ref['request_sha256'], ref['result_sha256'])
               and any(r['sha256'] == ctx['receipt_sha256'] for r in ref['receipts']), 'source receipt identity mismatch')
        receipt = ctx['receipt']
        R.need(receipt['coverage'] == 'COMPLETE', 'COMPLETE_BODY_REQUIRED')
        status = x.status(ref['source_base'], ctx['receipt_sha256'])
        R.need(status['state'] == 'CUSTODY_COMPLETE' and status['consistent'], 'NATIVE_CUSTODY_COMPLETION_REQUIRED')
        package, export = R.path(selection['package']), R.path(selection['export'])
        R.need(R.path(status['custody_claim']['package']) == package, 'custody claim names another package')
        stored = Q.load(package)
        R.need(stored['route'] == ctx['route'] and (package / 'registry.json').read_bytes() == ctx['registry_raw'],
               'custody registry differs from native approved source scope')
        retrieval = stored['supply']['system_retrieval']
        R.need(retrieval['transfer_coverage'] == 'COMPLETE' and stored['supply']['coverage'] == 'COMPLETE_CLAIMED',
               'complete custody coverage required')
        R.need((retrieval['attempt_id'], retrieval['request_sha256'], retrieval['result_sha256'], retrieval['receipt_sha256'],
                retrieval['requested_url'], retrieval['body_sha256'], retrieval['body_bytes']) ==
               (ref['attempt_id'], ctx['request_sha256'], ctx['result_sha256'], ctx['receipt_sha256'], selection['url'],
                N.sha(ctx['body']), len(ctx['body'])), 'custody/source identity mismatch')
        R.need((package / 'original.bin').read_bytes() == ctx['body'], 'custody original differs from native body')
        checked = Q.validate_export(export)
        # Matching a URL or a supplied original hash is insufficient: the portable package,
        # all retained provenance, native completion and subject must agree.
        exported = Q.load(export / 'source')
        R.need({k: v for k, v in exported.items() if k != 'root'} == {k: v for k, v in stored.items() if k != 'root'}
               and checked['provenance']['supply'] == stored['supply'], 'wrong Quarry export/package')
        card = Archive(branch['archive']).load().latest(branch['idea_id'])
        subject, _ = adapters.subject(card)
        data = R.loads(R.read(export / 'input.json'))
        R.need(data['subject'] == subject, 'export Scout subject/version mismatch')
        R.need(data['documents'] and all(d['original_sha256'] == N.sha(ctx['body']) for d in data['documents']),
               'export original identity mismatch')
        row = next(r for r in campaign['branches'] if r['branch_id'] == branch['branch_id'])
        R.need(companion.campaign.load()[1][-1]['hash'] == campaign['journal_head'], 'campaign changed during inspection')
        activity = next(a for a in row['activities'] if a['activity_id'] == selection['operator_activity'])
        R.need(activity['state']['execution_state'] != 'RECONCILIATION_REQUIRED', 'operator reference requires reconciliation')
        view = operator_view(activity, branch)
        exports = [s['summary'] for n, s in view['stages'].items() if n.startswith('QUARRY_EXPORT:') and s['status'] == 'COMPLETE']
        # One export makes lineage of this rehearsal unambiguous. Multi-export collections
        # require a future explicitly reviewed binding rather than an inferred membership.
        R.need(len(exports) == 1 and R.path(exports[0]['export']) == export
               and exports[0]['manifest_sha256'] == file_ref(export / 'manifest.json')['sha256'],
               'operator did not consume this exact single export')
        jev = view['stages'].get('JEV_EVIDENCE', {})
        R.need(jev.get('status') == 'COMPLETE', 'native Jev evidence stage incomplete')
        _, bundle = J.load(jev['summary']['workspace'])
        R.need(R.path(bundle['input_file']) == export / 'input.json', 'Jev consumed another evidence input')
        R.need(jev['summary']['model_status'] == 'NOT_IMPORTED_DETERMINISTIC_ONLY', 'hosted/model result outside scope')
        claim = x.custody_root(ref['source_base']) / 'receipts' / (ctx['receipt_sha256'] + '.json')
        completion = x.completion_path(ref['source_base'], ctx['receipt_sha256'])
        return {'schema': VERSION, 'selection': selection, 'implementation': implementation(),
                'fixture': branch['fixture'], 'assurance': 'NATIVE_RECORD_INTEGRITY_ONLY_NOT_SOURCE_OR_MEASUREMENT_VALIDITY',
                'branch_execution_state': row['execution_state'],
                'branch_summary_authority': 'UNCHANGED; this checkpoint selects an activity, never a winning branch run',
                'campaign': manifest['campaign'], 'campaign_journal_head': campaign['journal_head'],
                'companion_journal_head': events[-1]['hash'], 'hypothesis': ref['hypothesis'],
                'source_reference': ref, 'source_consumption': result['consumption'],
                'receipt': {'sha256': ctx['receipt_sha256'], 'body_sha256': N.sha(ctx['body']), 'body_bytes': len(ctx['body']),
                            'coverage': receipt['coverage'], 'limitations': receipt['limitations']},
                'custody': {'claim': file_ref(claim), 'completion': file_ref(completion),
                            'package_manifest': file_ref(package / 'manifest.json'), 'claims_sha256': retrieval['claims_sha256']},
                'quarry_export_manifest': file_ref(export / 'manifest.json'),
                'limitations': stored['supply']['limitations'], 'missing_fields': stored['supply']['missing_fields'],
                'publication_authenticity': retrieval['publication_authenticity'],
                'dataset_completeness': retrieval['dataset_completeness'], 'scientific_meaning': retrieval['scientific_meaning'],
                'operator_reference': activity, 'native_anvil_checkpoint': view,
                'research_outcome': None, 'downstream': 'NOT_AUTHORISED_STOP_AT_ANVIL', 'authorises': []}


def seal(selection, out):
    out = R.path(out)
    R.need(not out.exists(), 'new checkpoint directory required; never overwrite')
    root = Companion(selection['campaign']).root
    R.need(out.parent == root or not any((p / '.git').exists() for p in (out, *out.parents)),
           'checkpoints belong directly in companion storage or outside Git checkouts')
    value = inspect(selection)
    with offline([out]):
        out.mkdir(parents=True, exist_ok=False)
        S.write_new(out / 'checkpoint.json', value)
        S.write_new(out / 'seal.json', {'schema': VERSION + '_SEAL', 'checkpoint_sha256': file_ref(out / 'checkpoint.json')['sha256'],
                                      'authorises': []})
    verify(out)
    return value


def verify(out):
    """Read-only revalidation: failures require new observation, never native replay."""
    out = R.path(out)
    with offline([]):
        seal_record = R.loads(R.read(out / 'seal.json'))
        value = R.loads(R.read(out / 'checkpoint.json'))
        R.need(seal_record == {'schema': VERSION + '_SEAL', 'checkpoint_sha256': file_ref(out / 'checkpoint.json')['sha256'],
                               'authorises': []}, 'checkpoint seal mismatch')
    R.need(inspect(value['selection']) == value, 'retained chain/code changed; read-only reconciliation required')
    return value
