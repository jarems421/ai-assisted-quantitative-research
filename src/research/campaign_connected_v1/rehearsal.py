"""One connected synthetic chain, with actual native custody; never a live runtime."""
import tempfile

from src.research.operator import demo, runs, adapters
from src.research.operator.guard import offline
from src.research.campaign_v1 import campaign as C, records as R
from src.research.campaign_evidence_v1.continuity import Companion
from src.research.source_v1 import retrieve as source
from src.research.quarry_v1 import evidence as Q
from . import fixtures as F, lineage as L


def rehearse(out):
    out = R.path(out)
    R.need(not out.exists() and not any((p / '.git').exists() for p in (out, *out.parents)),
           'new standalone directory outside Git checkouts required')
    x = L.custody_api()  # Missing dependency refuses before writing anything.
    with offline([out]):
        archive, ready, _ = demo.scout_archive(out / 'synthetic-forge')
    card = archive.load().latest(ready)
    base = out / 'workspace'
    campaign = C.create(base, 'CMP-SYNTHETIC-CONNECTED')
    campaign.add_branch('B0', archive.path, ready, card['version'], R.digest(card))
    companion = Companion(campaign.root).create()
    branch = campaign.load()[2]['B0']
    clock, fake = F.Clock(), F.FakeTransport()
    with offline([out]):
        request = F.request(out / 'inputs', base, branch, campaign.root.name, clock)
        result = source.run(request, base, transport=fake, clock=clock.now, ticks=clock.ticks, sleep=clock.sleep)
        R.need(result['status'] == 'COMPLETE' and fake.opened == [F.ROBOTS, F.URL], 'synthetic retrieval did not complete exactly')
    companion.attach('B0', 'SOURCE-0', base, result['attempt_id'])
    with offline([out]):
        ctx = x.preflight(base, result['attempt_id'], F.URL)
        claims = F.claims(out / 'inputs', ctx, x)
        # Keep the native bridge's staging inside this rehearsal. Retain it as a
        # diagnostic fixture: Linux TemporaryDirectory cleanup uses fd-relative
        # unlink, which the unchanged operator guard deliberately cannot admit.
        # Do not relax that guard or permit writes across system TEMP.
        # This serial fixture command is not a concurrent campaign service.
        scratch = out / 'native-scratch'
        scratch.mkdir()
        temporary_directory = tempfile.TemporaryDirectory
        try:
            tempfile.TemporaryDirectory = lambda **kw: temporary_directory(dir=str(scratch), delete=False, **kw)
            x.import_receipt(base, result['attempt_id'], F.URL, claims, out / 'custody', clock=clock.now)
        finally:
            tempfile.TemporaryDirectory = temporary_directory
        subject = F.put(out / 'inputs', 'subject.json', adapters.subject(card)[0])['path']
        Q.export(out / 'custody', F.inspection(out / 'inputs'), subject, out / 'export')
        evidence = runs.evidence_spec({'schema': 'RESEARCH_OS_OPERATOR_EVIDENCE_V001', 'routes': [],
                                      'exports': [{'label': 'SYN', 'path': str(out / 'export')}]}, out)
    layout = runs.create(runs.request_value(archive.path, ready, None, evidence, [], None),
                         base=base, run_id='OPR-SYNTHETIC-CONNECTED')
    runs.invoke(layout, 'run')
    campaign.attach('B0', 'OPERATOR-0', layout.run)
    selection = {'campaign': str(campaign.root), 'branch': 'B0', 'source_activity': 'SOURCE-0', 'url': F.URL,
                 'package': str(out / 'custody'), 'export': str(out / 'export'), 'operator_activity': 'OPERATOR-0'}
    report = L.seal(selection, out / 'connected-checkpoint')
    checks = report['native_anvil_checkpoint']
    R.need(checks['discovery'] is not None and checks['discovery']['fixture'] == 'SYNTHETIC', 'native Discovery preview required')
    R.need(all(r['human_judgment'] == 'NOT_REVIEWED' for r in checks['discovery']['requirements'].values()),
           'unexpected scientific judgment in synthetic preview')
    R.need(fake.opened == [F.ROBOTS, F.URL], 'unexpected repeat of fake retrieval')
    return {'fixture': 'SYNTHETIC_NOT_RESEARCH', 'outcome': 'CONNECTED_CUSTODY_TO_ANVIL_HUMAN_GATES_REMAIN',
            'checkpoint': str(out / 'connected-checkpoint' / 'checkpoint.json'),
            'checkpoint_sha256': L.file_ref(out / 'connected-checkpoint' / 'checkpoint.json')['sha256'],
            'anvil_status': checks['stages']['ANVIL_CHECKS']['status'], 'research_outcome': None,
            'fake_transport_requests': len(fake.opened), 'external_requests': 0, 'model_calls': 0, 'authorises': []}
