"""Pilot-only plan/acquire/parse/replay/audit/report. No experiment CLI calls."""
import argparse
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

from src.research.sec_pilot.acquisition import ROOT, RAW, fixtures, identity, Boundary, Archive, Acquire, now
from src.research.sec_pilot.parsing import canonical, digest
from src.research.sec_pilot.reconcile import reconcile
from src.research.sec_pilot.provenance import asof

PYTHON = ROOT/'.research/sec-pilot-venv/Scripts/python.exe'
SUMMARY = ROOT/'docs/acceleration/phase2_summary.json'


class Index(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.cells = None; self.cell = None; self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.cells = []; self.hrefs = []
        elif tag == 'td' and self.cells is not None: self.cell = ''
        elif tag == 'a' and self.cells is not None:
            self.hrefs += [v for k, v in attrs if k == 'href']
    def handle_data(self, text):
        if self.cell is not None: self.cell += text
    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.cells.append(self.cell.strip()); self.cell = None
        elif tag == 'tr' and self.cells is not None:
            self.rows.append((self.cells, self.hrefs)); self.cells = None


def documents(data, boundary):
    index = Index(); index.feed(data.decode('utf-8', errors='strict')); result = {}
    for cells, links in index.rows:
        if len(cells) < 4: continue
        kind = cells[3]
        role = 'primary' if kind == '10-K' else 'instance' if kind in ('XML', 'EX-101.INS') else None
        if role is None: continue
        if len(links) != 1: raise ValueError('Ambiguous required document link')
        link = links[0]
        # SEC inline-viewer links may wrap a path; no viewer endpoint is fetched.
        if link.startswith('/ix?doc='): link = link[len('/ix?doc='):]
        name = link.rsplit('/', 1)[-1]
        candidate = boundary.add_document(name)
        if link not in (name, candidate, candidate.removeprefix('https://www.sec.gov')):
            raise ValueError('Index document outside frozen accession')
        if role in result: raise ValueError('Ambiguous primary/instance document')
        result[role] = candidate
    if set(result) != {'primary', 'instance'}: raise ValueError('Required primary/instance document unresolved')
    return result


def plan():
    return {'status': 'OFFLINE_PLAN', 'fixtures': fixtures(), 'maximum_requests_per_second': 2,
            'workers': 1, 'maximum_attempts_per_document': 3, 'maximum_response_bytes': 64*1024*1024,
            'seeds': {r['accession']: sorted(Boundary(r).allowed) for r in fixtures()},
            'nexus_calls': 0, 'public_availability_policy_approved': False}


def acquire():
    request_identity = identity(); archive = Archive(RAW)
    if (RAW/'acquisition_stop.json').exists():
        raise ValueError('Prior acquisition stop exists; inspect existing evidence before any retry')
    session = Acquire(Boundary(fixtures()[0]), archive, request_identity=request_identity)
    for fixture in fixtures():
        accession = fixture['accession']; directory = RAW/accession; directory.mkdir(parents=True, exist_ok=True)
        if (directory/'job.json').exists():
            job = json.loads((directory/'job.json').read_bytes())
            for source in job['sources'].values(): archive.read(source['body'])
            continue  # Explicit cache hit: no new network receipt or ingestion time.
        session.boundary = Boundary(fixture); sources = {}
        try:
            for role, url in [('index', fixture['index_url']),
                              ('header', session.boundary.base+accession+'-index-headers.html'),
                              ('submission', session.boundary.base+accession+'.txt')]:
                sources[role] = session.get(url)
            required = documents(archive.read(sources['index']['body']), session.boundary)
            archive.receipts.write(accession+'/document_plan.json',
                {'fixture': fixture, 'required': required, 'allowed_urls': sorted(session.boundary.allowed),
                 'index_sha256': sources['index']['body']['sha256']})
            for role, url in required.items(): sources[role] = session.get(url)
            job = {'fixture': fixture, 'raw_root': str(RAW), 'sources': sources,
                   'code_git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   'retrieved_at_utc': now(), 'historically_reconstructed': True}
            archive.receipts.write(accession+'/job.json', job)
            print('Archived fixed accession '+accession, flush=True)
        except (Exception, KeyboardInterrupt) as error:
            archive.receipts.write('acquisition_stop.json', {'accession': accession, 'error_type': type(error).__name__,
                'stop_time_utc': now(), 'successfully_acquired_roles': sorted(sources), 'remote_retry_authorized': False})
            raise ValueError('Acquisition stopped; existing private evidence retained; '+type(error).__name__) from None


def process(*, replay=False):
    summary = []
    archive = Archive(RAW)
    for fixture in fixtures():
        accession = fixture['accession']; directory = RAW/accession
        if not (directory/'job.json').exists():
            summary.append({'accession': accession, 'acquisition': 'NOT_COMPLETE', 'parsing': 'NOT_RUN'})
            continue
        job = json.loads((directory/'job.json').read_bytes())
        for record in job['sources'].values(): archive.read(record['body'])
        parser_hash = hashlib.sha256((Path(__file__).with_name('parsing.py')).read_bytes()).hexdigest()
        run = directory/'parsers'/parser_hash; run.mkdir(parents=True, exist_ok=True)
        if not (run/'job.json').exists():
            if replay: raise ValueError('This parser version has no recorded ingestion; replay cannot create one')
            job = dict(job, code_git_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
            archive.receipts.write((run/'job.json').relative_to(RAW).as_posix(), job)
        else: job = json.loads((run/'job.json').read_bytes())
        output = run/'parsed.json'
        result = subprocess.run([str(PYTHON), '-m', 'src.research.sec_pilot.parsing', str(run/'job.json'), str(output)],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            archive.receipts.write(accession+'/parser_failure_'+uuid.uuid4().hex+'.json',
                                    {'time_utc': now(), 'status': 'BLOCKED_PINNED_OFFLINE_PARSER', 'stderr': result.stderr})
            raise ValueError('Pinned offline parser failed for '+accession+'; private failure receipt retained')
        snapshot = json.loads(output.read_bytes())
        if not (run/'ingestion.json').exists() and not replay:
            archive.receipts.write((run/'ingestion.json').relative_to(RAW).as_posix(), {'ingested_at_utc': now(), 'snapshot_sha256': snapshot['snapshot_sha256']})
        else:
            ingestion = json.loads((run/'ingestion.json').read_bytes())
            if ingestion['snapshot_sha256'] != snapshot['snapshot_sha256']: raise ValueError('Ingestion snapshot mismatch')
        checks = reconcile(snapshot, job, run/'tables')
        view = asof(snapshot, '2020-12-31T23:59:59Z', snapshot_sha256=snapshot['snapshot_sha256'])
        summary.append({'accession': accession, 'acquisition': 'PASS', 'parsing': 'PASS_OFFLINE',
                        'source_documents': [{ 'role': role, 'sha256': record['body']['sha256'], 'bytes': record['body']['bytes']}
                                             for role, record in sorted(job['sources'].items())],
                        'snapshot_sha256': snapshot['snapshot_sha256'], 'facts': len(snapshot['facts']),
                        'parser_source_sha256': parser_hash, 'code_git_sha': snapshot['code_git_sha'],
                        'retrieved_at_utc': job['retrieved_at_utc'],
                        'ingested_at_utc': json.loads((run/'ingestion.json').read_bytes())['ingested_at_utc'],
                        'normalized_text_sha256': snapshot['text_sections'][0]['normalized_text_sha256'],
                        'reconciliation': checks, 'accepted_raw': snapshot['acceptance_raw'],
                        'accepted_at_utc': snapshot['accepted_at_utc'], 'public_availability': 'UNKNOWN',
                        'identity': 'UNRESOLVED', 'trading_eligible_facts': len(view['usable']),
                        'examples': [{k: f[k] for k in ('concept', 'namespace', 'exact_value', 'context_ref', 'fact_locator', 'source_sha256')}
                                     for f in snapshot['facts'] if f['concept'] in ('Assets', 'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax')][:3]})
    stop = json.loads((RAW/'acquisition_stop.json').read_bytes()) if (RAW/'acquisition_stop.json').exists() else None
    attempts = []
    for path in RAW.glob('*/attempts/*.json'):
        receipt = json.loads(path.read_bytes())
        attempts.append({'accession': path.parts[-3], 'status': receipt['status'], 'url': receipt['request_url'],
                         'body_sha256': receipt['body']['sha256'], 'body_bytes': receipt['body']['bytes']})
    document = {'as_of': '2026-10-12', 'scope': 'Three fixed SEC filings only', 'filings': summary,
                'network_attempts': sorted(attempts, key=lambda r: (r['url'], r['body_sha256'])),
                'acquisition_stop': stop, 'source_fidelity': 'PARTIAL' if all(r['acquisition'] == 'PASS' for r in summary) else 'BLOCKED',
                'trading_eligibility': 'BLOCKED', 'execution_compatibility': 'BLOCKED_NEXUS_UNCERTIFIED',
                'nexus_calls': 0, 'performance_queries': 0, 'exp005_created': False}
    if replay:
        if json.loads(SUMMARY.read_bytes()) != document: raise ValueError('Offline replay summary differs')
    else: SUMMARY.write_bytes(canonical(document)+b'\n')
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('plan', 'acquire', 'parse', 'replay', 'audit', 'report'))
    parser.add_argument('--execute', action='store_true'); args = parser.parse_args()
    if args.operation == 'plan': print(json.dumps(plan(), indent=2)); return
    if args.operation == 'acquire':
        if not args.execute: raise ValueError('Acquisition requires --execute and existing owner authorization')
        acquire(); return
    result = process(replay=args.operation in ('replay', 'audit'))
    print(json.dumps({'source_fidelity': result['source_fidelity'], 'filings': len(result['filings']), 'nexus_calls': 0}))


if __name__ == '__main__':
    try: main()
    except ValueError as error:
        print(str(error), file=sys.stderr); sys.exit(1)
