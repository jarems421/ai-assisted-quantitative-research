"""Synthetic rehearsal foundation. No source dispatcher or human authorisation records."""
from pathlib import Path

from src.research.operator import demo, runs
from src.research.operator.guard import offline
from src.research.campaign_v1 import campaign as C, native as N, records as R
from src.research.source_v1 import retrieve as source, store as S, contracts as K
from src.research.opportunity_scout.storage import Archive
from .continuity import Companion


def refused_source(base, branch, campaign_id, *, attempt_id='SYNTHETIC-NOT-STARTED'):
    """An expressly synthetic clean refusal, constructed using native record primitives.

    No scope/attestation is authored and no claim or dispatch is made. This fixture
    cannot demonstrate retrieval or authority. Native verify re-derives its result.
    """
    request = {'schema': K.REQUEST, 'campaign_id': campaign_id, 'branch_id': branch['branch_id'],
               'subject': {'archive_sha256': N.sha(R.read(Path(branch['archive']) / 'scout.jsonl')),
                           'card_id': branch['idea_id'], 'card_version': branch['version'], 'card_sha256': branch['card_sha256']},
               'request_id': 'SYNTHETIC-REQUEST', 'attempt_id': attempt_id,
               'question': {'text': 'SYNTHETIC refusal fixture; no investigation', 'requirements': [
                   {'id': 'ER-1', 'role': 'CONTEXT', 'quantity': 'UNKNOWN', 'unit': 'UNKNOWN', 'denominator': 'UNKNOWN',
                    'population': 'UNKNOWN', 'period': 'UNKNOWN', 'join': 'UNKNOWN'}]},
               'authority': {'scope': {'path': str(Path(base) / 'ABSENT-owner-scope.json'), 'sha256': '0' * 64},
                             'operations': ['RETRIEVE_EXACT_URL'], 'transmission': 'NONE',
                             'tier_a': {'exact_urls': ['https://synthetic.example.org/absent'], 'hosts': ['synthetic.example.org']},
                             'tier_b_classes': [], 'host_amendments': []},
               'stops': {'snapshot': {'path': str(Path(base) / 'ABSENT-stop-snapshot.json'), 'sha256': '0' * 64}},
               'resources': {'campaign_allocation_ref': None, 'reservation': {'requests': 2, 'total_bytes': 1024,
                   'per_response_bytes': 1024, 'wall_seconds': 1, 'searches': 0, 'model_calls': 0, 'metered_micro_usd': 0}},
               'caller_ref': 'SYNTHETIC_ENGINEERING_FIXTURE_NO_AUTHORITY'}
    K.request(request)
    _, attempt = source.directories(base, attempt_id)
    sha = source.create(attempt, S.encode(request))
    refusal = {'reason': 'SYNTHETIC_OFFLINE_REFUSAL_NO_SCOPE_OR_DISPATCH', 'implementation_sha256': S.implementation()}
    result = source.derive(attempt, request, sha, [], [], 'REFUSED', source.readonly(base), refused=refusal)
    S.Journal(attempt / 'journal.jsonl', clock=lambda: demo.MOMENT).append('ATTEMPT_REFUSED',
                            {**refusal, 'result_sha256': S.sha(S.encode(result))})
    S.write_new(attempt / 'result.json', result)
    return attempt_id


def rehearse(out):
    out = R.path(out)
    R.need(not out.exists() and not any((p / '.git').exists() for p in (out, *out.parents)),
           'rehearsal requires a new directory outside Git checkouts')
    with offline([out]):
        f = demo.fixtures(out / 'native')
    ids = [f['ready_idea'], f['unreviewed_idea']]
    c = C.create(f['base'], 'CMP-SYNTHETIC-CHECKPOINT')
    for i, idea in enumerate(ids):
        c.add_branch(f'B{i}', f['archive'], idea, 1, R.digest(Archive(f['archive']).load().latest(idea)))
        layout = runs.create(runs.request_value(f['archive'], idea, None, None, [], None),
                             base=f['base'], run_id=f'OPR-SYNTHETIC-CHECKPOINT-{i}')
        runs.invoke(layout, 'run')
        if i == 0:
            spec = runs.evidence_spec(R.loads(R.read(f['evidence'])), Path(f['evidence']).parent)
            runs.invoke(layout, 'continue', supplied={'evidence': spec, 'search_terms': [], 'ledger': None})
        c.attach(f'B{i}', f'OPERATOR-{i}', layout.run)
    companion = Companion(c.root).create()
    branch = c.load()[2]['B0']
    with offline([out]):
        attempt = refused_source(f['base'], branch, c.root.name)
    companion.attach('B0', 'SOURCE-0', f['base'], attempt)
    report = companion.checkpoint()
    result = {'fixture': 'SYNTHETIC_NOT_RESEARCH', 'outcome': 'FOUNDATION_ONLY_CUSTODY_BRIDGE_NOT_CONNECTED',
              'checkpoint': report, 'model_calls': 0, 'external_requests': 0, 'authorises': []}
    with offline([out]):
        S.write_new(out / 'checkpoint.json', result)
    return result
