"""Offline source review with content-addressed derivatives and public summaries."""
from collections import Counter
from datetime import date, datetime, time, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from src.research.phase3c.sources import RAW, DOCS, PYTHON, ROOT, put
from src.research.phase3c.quality import revenue_chain, figi_gate, market_quality, completeness
from src.research.sec_pilot.acquisition import Archive
from src.research.sec_pilot.parsing import digest
from src.research.sec_pilot.planning import ambiguity_probe
from src.research.sec_pilot.certification import acceptance, NY
from src.nexus.process_exp001 import session_dates


def originals():
    parser_hash = hashlib.sha256((ROOT / 'src/research/phase3c/parsing.py').read_bytes()).hexdigest()
    directory = RAW / 'parsed' / parser_hash; directory.mkdir(parents=True, exist_ok=True)
    records = []
    for source in sorted((RAW / 'filings_v003').glob('*.json')):
        filing = json.loads(source.read_bytes())
        if filing['form'] != '10-K': continue
        out = directory / (filing['accessionNumber'] + '.json')
        job = dict(filing, raw_root=str(RAW), parser_source_sha256=parser_hash,
                   code_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
        job_path = directory / (digest(job) + '_job.json'); put(job_path, job)
        if not out.exists():
            result = subprocess.run([str(PYTHON), '-m', 'src.research.phase3c.parsing', str(job_path), str(out)],
                                    cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                # Exception output can include source facts; retained privately only.
                put(directory / (filing['accessionNumber'] + '_error.json'),
                    {'returncode': result.returncode, 'stderr': result.stderr, 'job_sha256': digest(job)})
        record = json.loads(out.read_bytes()) if out.exists() else {'status': 'UNAVAILABLE_OTHER_EXPLICIT_REASON',
                    'reason': 'OFFLINE_PARSER_RECONCILIATION_FAILED', 'accession': filing['accessionNumber'],
                    'issuer_cik': filing['issuer_cik']}
        if out.exists() and record.get('code_sha256') != parser_hash: raise ValueError('Pinned parser snapshot code mismatch')
        records.append(record)
        print('Offline filing records examined:', len(records), flush=True)
    return records


def build():
    cohort = json.loads((DOCS / 'phase3c_pilot_cohort.json').read_bytes()); archive = Archive(RAW)
    records = originals(); index = {r['accession']: r for r in records}; chains = []
    plans = json.loads((RAW / 'source_plan_summary_v003.json').read_bytes())
    source_files = [json.loads(p.read_bytes()) for p in sorted((RAW/'filings_v003').glob('*.json'))]
    for case in [r for r in cohort['cases'] if r['revenue_candidate']]:
        plan = next((p for p in plans if p['issuer_cik'] == case['issuer_cik']), {})
        # A later lifecycle-document error must not conceal already acquired originals.
        selected_sources = [f for f in source_files if f['form'] == '10-K' and f['issuer_cik'] == case['issuer_cik']]
        selected = [index[f['accessionNumber']] for f in selected_sources]
        usable = [r for r in selected if r.get('status') == 'PARSED_ORIGINAL_ONLY_NOT_CHAIN_CERTIFIED']
        result = revenue_chain(usable)
        if len(selected_sources) == 3 and len(usable) < 3:
            result = {'status': 'UNAVAILABLE_OTHER_EXPLICIT_REASON', 'reason': 'ORIGINAL_DOCUMENT_OR_PARSER_RECONCILIATION_INCOMPLETE',
                      'source_hashes': [r.get('source_sha256') for r in selected]}
        exact = len(usable) == 3 and all(r.get('revenue') for r in usable)
        chains.append({'case_key': case['case_key'], 'issuer_cik': case['issuer_cik'],
                       'selected_originals': len(selected_sources), 'offline_parsed': len(usable),
                       'exact_concept_three': exact, 'result': result,
                       'filing_accessions': [r['accession'] for r in selected]})
    phase3a = json.loads((DOCS / 'phase3a_evidence.json').read_bytes())
    acceptance_hash = phase3a['acceptance_interpretations'][0]['evidence_sha256']
    calendar = sorted(session_dates(date(2015, 1, 1), date(2021, 12, 31)))
    # Existing policy itself still covers2015–2020. Mechanical2021 calendar extension is a probe, never activation.
    timing = []
    policy = {'version': 'phase3c_ambiguity_buffer_v002', 'status': 'PROPOSED_NOT_APPROVED', 'approval': None,
              'rule': '09:30NewYork second session strictly after later of filing date and each candidate acceptance civil date; require same raw-rule open for all candidates',
              'scope': ['2015-01-01', '2021-12-31'], 'exact_public_availability': 'UNKNOWN',
              'calendar_source_sha256': hashlib.sha256((ROOT/'src/nexus/process_exp001.py').read_bytes()).hexdigest(),
              'acceptance_evidence_sha256': acceptance_hash,
              'limitations': 'Calendar mechanics only; observed public availability and full listing/execution calendar not certified; separate owner approval required'}
    for filing in [f for f in source_files if f['form'] == '10-K']:
        import re
        from html import unescape
        raw = None
        source = filing.get('sources', {}).get('header')
        if source:
            text = unescape(archive.read(source['body']).decode('utf-8'))
            match = re.search(r'ACCEPTANCE-DATETIME[>\s:]+(\d{14})', text)
            if match: raw = match[1]
        record = {'accession': filing['accessionNumber'], 'filing_date': filing['filingDate'], 'acceptance_raw': raw}
        try:
            if not raw: raise ValueError('Missing acceptance source')
            interpretation = acceptance(raw, evidence_sha256=acceptance_hash)
            candidates = [interpretation['candidate_eastern_utc'], interpretation['candidate_literal_est_utc']]
            dates = [datetime.strptime(raw, '%Y%m%d%H%M%S').date()] + [datetime.fromisoformat(s).astimezone(NY).date() for s in candidates]
            filed = date.fromisoformat(record['filing_date']); bounds = []
            for d in dates:
                if not date(2015,1,1) <= d <= filed <= date(2021,12,31): raise ValueError('Candidate chronology/scope conflict')
                later = [s for s in calendar if s > max(d, filed)]
                if len(later) < 2: raise ValueError('Calendar coverage')
                bounds.append(datetime.combine(later[1], time(9,30), tzinfo=NY).astimezone(timezone.utc).isoformat())
            invariant = len(set(bounds)) == 1 and all(datetime.fromisoformat(bounds[0]) > datetime.fromisoformat(s) for s in candidates)
            timing.append({'accession': record['accession'], 'status': 'INVARIANT' if invariant else 'NON_INVARIANT',
                           'raw': raw, 'filing_date': record['filing_date'], 'candidate_bounds_utc': bounds,
                           'candidate_instants_utc': candidates, 'acceptance_status': interpretation['status'],
                           'public_available_at_utc': None, 'policy_approved': False,
                           'near_midnight': int(raw[8:10]) >= 23, 'weekend': dates[0].weekday() >= 5,
                           'non_session_date': dates[0] not in calendar,
                           'weekday_holiday': dates[0].weekday() < 5 and dates[0] not in calendar,
                           'dst_transition_week': len({datetime.fromisoformat(s).astimezone(NY).utcoffset() for s in
                               [bounds[0], candidates[0]]}) > 1})
        except ValueError:
            timing.append({'accession': record['accession'], 'status': 'CALENDAR_FAILURE', 'raw': record['acceptance_raw']})
    figi_records = json.loads((RAW / 'openfigi_summary.json').read_bytes()); figis = {r['case_key']: r for r in figi_records}
    merger_path = RAW/'merger_primary_summary.json'
    merger_receipts = json.loads(merger_path.read_bytes()) if merger_path.exists() else []
    # Original event documents are partial evidence, not complete class/position contracts.
    merger_index = {r['issuer_cik']: r for r in merger_receipts if r.get('sources',{}).get('primary',{}).get('status') == 200}
    market = []
    tiingo = {r['case_key']: r for p in (RAW/'tiingo_cases').glob('*.json') for r in [json.loads(p.read_bytes())]}
    identities = []; statuses = []
    for case in cohort['cases']:
        original = [r for r in records if r.get('issuer_cik') == case['issuer_cik']]
        observed = [dict(o, accession=r['accession'], filing_date=r.get('filing_date'), source_sha256=r.get('source_hashes', {}).get('primary'))
                    for r in original for o in r.get('cover_observations', [])]
        f = figis.get(case['case_key'], {}); gate = figi_gate(f.get('result', {}))
        found = f.get('result', {}).get('data', [])
        cover_groups = {}
        for o in observed:
            key = (o['accession'], o['context'])
            cover_groups.setdefault(key, {}).setdefault(o['concept'], set()).add(o['text'].strip())
        matching_groups = [g for g in cover_groups.values() if case['historical_symbol_candidate'] in g.get('TradingSymbol', set())]
        class_point = any(len(g.get('Security12bTitle', set())) == 1 for g in matching_groups)
        ticker_exchange_point = any(len(g.get('SecurityExchangeName', set())) == 1 for g in matching_groups)
        identity = {'case_key': case['case_key'], 'status': 'AMBIGUOUS' if gate == 'AMBIGUOUS' else 'PROVISIONAL' if observed or found else 'UNRESOLVED',
                    'figi_status': gate, 'figi_response_sha256': f.get('source_sha256'), 'current_identifier_candidates': found,
                    'historical_cover_observations': observed, 'effective_from': None, 'effective_to': None,
                    'class_point_identified': class_point, 'ticker_exchange_point_identified': ticker_exchange_point,
                    'single_share_class_identifier_candidate': gate == 'IDENTIFIER_ONLY_NOT_HISTORICAL_INTERVAL',
                    'span_status': 'UNRESOLVED_NO_LISTING_INTERVAL_CERTIFICATE',
                    'terminal_status': 'TERMINAL_EVENT_PARTIAL' if case['issuer_cik'] in merger_index else 'TERMINAL_EVENT_UNRESOLVED',
                    'partial_event_accession': merger_index.get(case['issuer_cik'],{}).get('accession')}
        identities.append(identity)
        source = tiingo.get(case['case_key'], {}); refs = source.get('sources', {})
        meta = None; qa = None
        source_status = source.get('status', 'ACQUIRED_RESPONSES' if refs else 'NOT_ACQUIRED')
        failures = [r.get('status') for r in refs.values() if r.get('status') != 200]
        if failures: source_status = 'PROVIDER_HTTP_' + '_'.join(str(v) for v in failures)
        if refs.get('metadata', {}).get('status') == 200:
            meta = json.loads(archive.read(refs['metadata']['body']))
        if refs.get('prices', {}).get('status') == 200:
            rows = json.loads(archive.read(refs['prices']['body']))
            if isinstance(rows, list):
                # Full calendar scope is diagnostic only while listing spans uncertified;
                # no missing session becomes a delisting/holiday assumption.
                expected = sorted(d.isoformat() for d in session_dates(date(2019, 1, 1), date(2020, 12, 31)))
                qa = market_quality(rows, expected)
        market.append({'case_key': case['case_key'], 'source_status': source_status,
                       'metadata': meta, 'qa': qa, 'source_hashes': {k:r['body']['sha256'] for k,r in refs.items() if 'body' in r},
                       'listing_expected_session_status': 'UNRESOLVED_LISTING_INTERVAL', 'certified': False})
        flags = ['IDENTITY_UNRESOLVED']
        if failures or not source: flags.append('SOURCE_RETRIEVAL_FAILED')
        if not qa or qa['session_status'] != 'PASS': flags.append('PRICE_UNRESOLVED')
        if identity['terminal_status'] != 'TERMINAL_EVENT_CERTIFIED': flags.append('TERMINAL_EVENT_UNRESOLVED')
        statuses.append({'case_key': case['case_key'], 'state': 'SOURCE_RETRIEVAL_FAILED' if failures or not source else 'IDENTITY_UNRESOLVED',
                         'flags': flags, 'reason': 'No effective-dated class bridge; HTTP404/empty coverage is not observed absence; successful prices do not certify identity'})
    calibrations = [json.loads(p.read_bytes()) for p in (RAW/'calibration').glob('*.json')]
    attempts = []
    for p in (RAW / 'attempts').rglob('*.json'):
        r = json.loads(p.read_bytes()); attempts.append(r)
    unique = {(r['provider'], r['request_started_at_utc'], r['request_key'], r['attempt']): r for r in attempts}
    frozen = datetime.fromisoformat(cohort['frozen_at_utc'])
    if any(datetime.fromisoformat(r['request_started_at_utc']) < frozen for r in unique.values() if r['provider'] == 'Tiingo'):
        raise ValueError('Market acquisition preceded cohort freeze')
    body_receipts = []
    for r in unique.values():
        if 'body' in r:
            archive.read(r['body']); body_receipts.append({'provider': r['provider'], 'url': r['url'],
                   'status': r.get('status'), 'sha256': r['body']['sha256'], 'bytes': r['body']['bytes'],
                   'retrieved_at_utc': r['retrieved_at_utc']})
    counter = Counter(r['provider'] for r in unique.values())
    summary = {'version': 'phase3c_evidence_v001', 'cohort_sha256': cohort['cohort_sha256'], 'cases': len(cohort['cases']),
               'chains': chains, 'identity': identities, 'market': market, 'timing': timing,
               'policy': policy, 'policy_sha256': digest(policy),
               'original_filing_records': [{k:v for k,v in r.items() if k not in ('cover_observations',)} for r in records],
               'taxonomy_versions': sorted({ns for r in records for ns in r.get('taxonomy_versions', [])}),
               'filing_year_counts': dict(sorted(Counter(r.get('filing_date', 'UNKNOWN')[:4] for r in records).items())),
               'completeness': completeness(cohort['cases'], statuses), 'calibration': calibrations,
               'request_counts': dict(counter), 'body_receipts': body_receipts,
               'market_requests_after_freeze_verified': True,
               'nexus_calls': 0, 'strategy_performance_computed': False, 'real_signal_series_computed': False,
               'prior_stop_retained': True, 'oversized_initial_prefix_retention_gap': True}
    lifecycle_path = RAW/'lifecycle_primary_summary.json'
    summary['lifecycle_primary_receipts'] = json.loads(lifecycle_path.read_bytes()) if lifecycle_path.exists() else []
    summary['merger_primary_receipts'] = merger_receipts
    # Financial SEC observations are public; vendor response candidates/price metadata stay private.
    put(RAW / 'reviews' / (digest(summary) + '.json'), summary)
    return summary


if __name__ == '__main__':
    summary = build()
    print('Offline review retained:', digest(summary))
