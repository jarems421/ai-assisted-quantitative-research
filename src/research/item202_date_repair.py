"""Bounded EXP006 source-only date repair. Remote acquisition requires --execute.

No market loader, strategy engine, Store registration or confirmation adapter.
Old v001/v002 receipts and reports are never rewritten by this module.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, date
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urljoin

from src.research.spec import ROOT, digest
from src.research.phase3c.sources import put, SourceHTTP
from src.research.sec_pilot.acquisition import Archive, identity, now
from src.research.procurement_pilot import PilotHTTP, contract
from src.research.item202_availability import calendar_sessions, parse_header
from src.research.item202_date_bound import NY, RULE, envelope, compare, confusion, primary_item202

DOCS = ROOT / 'docs/acceleration'
RAW = ROOT / 'data/raw/item202_date_repair_v001'
OLD = ROOT / 'data/raw/item202_remedy_v001'
MANIFEST = DOCS / 'exp006_date_repair_manifest.json'
SAMPLE = DOCS / 'exp006_date_validation_sample_v003.json'
EVIDENCE = DOCS / 'exp006_date_validation_v003.json'
PRESERVE = ('exp006_freeze_review.md', 'exp006_bulk_clock_validation.json',
            'exp006_bulk_bound_sensitivity.json', 'exp006_availability_contract_v002.json',
            'exp006_chronology_validation_v002.json', 'exp006_source_coverage.json')


def write_public(name, value):
    put(DOCS / name, value)


def load_inputs():
    data = json.loads((OLD / 'source_closure/bulk_labels.json').read_bytes())
    if digest(data['rows']) != data['stats']['rows_sha256']:
        raise ValueError('Existing bulk derivative changed')
    return data['rows']


def stress(row):
    iso = row['metadata']['acceptance_representation']
    instant = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    lexical = datetime.fromisoformat(iso[:19])
    ny = instant.astimezone(NY)
    tags = []
    if lexical.hour in (23, 0, 1): tags.append('NEAR_UTC_LEXICAL_MIDNIGHT')
    if ny.hour in (23, 0, 1): tags.append('NEAR_NEW_YORK_MIDNIGHT')
    tags.append('PRE_MARKET' if ny.hour < 9 or (ny.hour == 9 and ny.minute < 30)
                else 'REGULAR_CLOCK' if ny.hour < 16 else 'AFTER_MARKET')
    if lexical.weekday() == 4: tags.append('FRIDAY')
    if (lexical.month == 3 and 1 <= lexical.day <= 16) or (lexical.month == 11 and lexical.day <= 10):
        tags.append('DST_TRANSITION_WINDOW')
    # Selection proxies, not inferred true serialization classes. Observed offsets
    # are computed only after acquiring originals; unsupported classes stay absent.
    if lexical.hour in range(6, 11): tags.append('LEXICAL_RAW_LIKE_HOUR_PROXY')
    if lexical.hour in range(11, 17): tags.append('LEXICAL_UTC_CONVERSION_HOUR_PROXY')
    if lexical.hour in range(17, 23): tags.append('PLUS_4_5_HOUR_STRESS_PROXY')
    if lexical.hour in range(0, 6): tags.append('MINUS_4_5_HOUR_STRESS_PROXY')
    return tags


def freeze():
    if MANIFEST.exists():
        verify_freeze()
        return {'status': 'EXISTING_FROZEN_DISPATCH', 'sample': len(json.loads(SAMPLE.read_bytes())['records'])}
    owner = ROOT / 'docs/acceleration/owner_item202_date_repair_2026-10-13.md'
    if not owner.exists(): raise ValueError('Archive exact owner instruction first')
    previous = json.loads((DOCS / 'exp006_chronology_validation_v002.json').read_bytes())['records']
    excluded = {r['accession'] for r in previous}
    groups = defaultdict(list)
    rows = load_inputs()
    unsupported = 0
    for r in rows:
        if r['accession'] in excluded or not r['metadata']: continue
        try:
            e = envelope(r['metadata']['acceptance_representation'], r['filing_date'])
            tags = stress(r)
        except (ValueError, TypeError):
            unsupported += 1
            continue
        d = date.fromisoformat(r['filing_date'])
        key = (d.year, (d.month - 1)//3 + 1, r['form'])
        groups[key].append((r, e, tags))
    chosen = []
    used = set(excluded)
    rotation = ['PRE_MARKET', 'REGULAR_CLOCK', 'AFTER_MARKET', 'FRIDAY',
                'LEXICAL_RAW_LIKE_HOUR_PROXY', 'LEXICAL_UTC_CONVERSION_HOUR_PROXY',
                'PLUS_4_5_HOUR_STRESS_PROXY', 'MINUS_4_5_HOUR_STRESS_PROXY']
    for i, key in enumerate(sorted(groups)):
        targets = ['NEAR_UTC_LEXICAL_MIDNIGHT', 'NEAR_NEW_YORK_MIDNIGHT',
                   'DST_TRANSITION_WINDOW', rotation[i % len(rotation)], 'FRIDAY']
        ordered = sorted(groups[key], key=lambda x: (digest({'CIK': x[0]['CIK'], 'accession': x[0]['accession']}), x[0]['CIK']))
        for target in targets:
            pool = [x for x in ordered if x[0]['accession'] not in used and target in x[2]]
            fallback = not pool
            if fallback: pool = [x for x in ordered if x[0]['accession'] not in used]
            if not pool: raise ValueError('Cannot fill declared source cell')
            r, e, tags = pool[0]
            used.add(r['accession'])
            chosen.append({'CIK': r['CIK'], 'accession': r['accession'], 'form': r['form'],
                           'filed_date': r['filing_date'], 'year': key[0], 'quarter': key[1],
                           'bulk_acceptanceDateTime': r['metadata']['acceptance_representation'],
                           'bulk_metadata_sha256': digest(r['metadata']), 'envelope': e,
                           'selection_target': target, 'target_fallback': fallback, 'stress_tags': tags,
                           'header_url': f"https://www.sec.gov/Archives/edgar/data/{int(r['CIK'])}/{r['accession'].replace('-', '')}/{r['accession']}-index-headers.html"})
    if len(chosen) != 240: raise ValueError('48 year/quarter/form cells required')
    sample = {'version': 'EXP006_date_validation_sample_v003', 'frozen_at_utc': now(),
              'records': chosen, 'records_sha256': digest(chosen), 'prior48_excluded': True,
              'unsupported_bulk_values_retained_in_census': unsupported,
              'selection': 'Five unique new accessions per year/quarter/form cell; hash-ordered selection within fixed timestamp-stress strata. No issuer fame/ticker/Item/outcome/price selection.',
              'representation_classes': 'Pre-acquisition hour proxies only; actual raw-like/conversion/offset classes reported after originals, never guessed for unsampled rows.'}
    calendar = json.loads((DOCS / 'exp006_calendar_certificate_v002.json').read_bytes())
    policy = {'version': 'EXP006_item202_availability_v003', 'rule': RULE,
              'status': 'OWNER_APPROVED_MODELED_TRANSFORM_PENDING_VALIDATION',
              'scope': ['2015-01-01', '2020-12-31'], 'owner_sha256': hashlib.sha256(owner.read_bytes()).hexdigest(),
              'exact_public_availability': 'UNKNOWN', 'exact_raw_clock_reconstruction': False,
              'timing_class': 'MODELED_CONSERVATIVE_BULK_DATE_ENVELOPE', 'policy_activated': False,
              'conservative_later_eligibility_accepted': True, 'calendar_sha256': digest(calendar),
              'invalid_conflicting_or_out_of_scope_input': 'UNAVAILABLE; never repair individual offsets',
              'validation_requirement': 'Every new sampled original must be available, identity-consistent, and show envelope >= every raw candidate date and open >= every raw candidate policy open. Unknowns prevent pass.',
              'new_midnight_semantics': 'Preserve both raw candidate dates; v003 explicitly uses conservative maximum rather than asserting v002 invariance. Report prior-v002 non-invariant cases separately.',
              'implementation_sha256': hashlib.sha256((ROOT / 'src/research/item202_date_bound.py').read_bytes()).hexdigest()}
    manifest = {'version': 'EXP006_date_repair_dispatch_v001',
                'starting_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'expected_head': '6ac5d8987117778f8e7a60bf808a2300ef03254f',
                'head_difference': 'Subsequent README-only employer presentation commit cafb8e9; research checkpoint unchanged',
                'owner_sha256': policy['owner_sha256'], 'sample_sha256': digest(sample), 'policy_sha256': digest(policy),
                'preserved_artifacts': {('docs/acceleration/' + n): hashlib.sha256((DOCS/n).read_bytes()).hexdigest() for n in PRESERVE},
                'workers': 1, 'minimum_start_seconds': .6, 'retries': 0,
                'header_start_ceiling': 240, 'archive_filing_day_GET_ceiling': 12,
                'archive_discovery_start_ceiling': 14, 'primary_body_start_ceiling': 96,
                'classification_header_start_ceiling': 0,
                'classification_selection': '96 records from the new 240 timing sample, two per year/quarter/form cell: one bulk Item2.02 positive and one negative where available, otherwise next hash-ordered unchosen record; retain imbalanced/missing cells.',
                'classification_pass': 'Zero FP/FN and no UNKNOWN in 96 original primary validations; otherwise source-label certificate remains blocked. No sample extrapolation to historical deletion completeness.',
                'archive_selection': 'Two earliest distinct census filed days represented in sample per year (12 days); test official Oldloads directory first; independently declared Feed directory if unavailable. No denied-route retries, redirects or mirror.',
                'archive_roots': ['https://www.sec.gov/Archives/edgar/Oldloads/', 'https://www.sec.gov/Archives/edgar/Feed/'],
                'archive_byte_limits': {'compressed_per_response': 256*1024*1024, 'uncompressed_per_day': 1024*1024*1024},
                'classification_body_byte_limit': 64*1024*1024,
                'data_selection_boundary': 'Only exact census-bound 2015-2020 metadata already archived; no current company/ticker fields or confirmation outcomes.',
                'continuation': 'If timing passes proceed to primary/PAC then identity/provider/execution/matching/inference gates. Stop at the first specific scientific blocker; no performance before pushed certified freeze.'}
    write_public(SAMPLE.name, sample)
    write_public('exp006_availability_contract_v003.json', policy)
    write_public(MANIFEST.name, manifest)
    return {'status': 'FROZEN_BEFORE_REQUESTS', 'sample': len(chosen), 'sample_sha256': digest(sample)}


def verify_freeze():
    m = json.loads(MANIFEST.read_bytes())
    sample = json.loads(SAMPLE.read_bytes())
    policy = json.loads((DOCS / 'exp006_availability_contract_v003.json').read_bytes())
    if digest(sample) != m['sample_sha256'] or digest(sample['records']) != sample['records_sha256'] or digest(policy) != m['policy_sha256']:
        raise ValueError('Frozen dispatch changed')
    if hashlib.sha256((ROOT/'src/research/item202_date_bound.py').read_bytes()).hexdigest() != policy['implementation_sha256']:
        raise ValueError('Frozen transform changed')
    for name, h in m['preserved_artifacts'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != h: raise ValueError('Historical artifact changed: ' + name)
    return m, sample, policy


def client(group, urls, ceiling):
    ua = identity()  # Value exists only in local request headers, never in receipts.
    def transport(url, headers, payload):
        return SourceHTTP._transport(url, dict(headers, **{'User-Agent': ua}), payload)
    h = PilotHTTP(contract(), root=RAW/group, transport=transport)
    h.allowed = set(urls)
    h.m = dict(contract(), version='EXP006_date_repair_' + group, request_ceiling=ceiling,
               dispatch_sha256=digest(json.loads(MANIFEST.read_bytes())),
               retry={'transient_statuses': []})
    return h


def acquire_headers():
    _, sample, _ = verify_freeze()
    if EVIDENCE.exists(): return {'status': 'EXISTING_VALIDATION_NO_REQUESTS'}
    h = client('headers', [x['header_url'] for x in sample['records']], 240)
    for i, r in enumerate(sample['records']):
        receipt, body = h.fetch(r['header_url'], purpose='FROZEN_DATE_ENVELOPE_ORIGINAL_HEADER_VALIDATION')
        print('Header', i+1, '/', len(sample['records']), 'HTTP', receipt['status'], flush=True)
        if receipt['status'] != 200: break
    return validate_headers()


def validate_headers():
    _, sample, policy = verify_freeze()
    calendar = json.loads((DOCS / 'exp006_calendar_certificate_v002.json').read_bytes())
    sessions = calendar_sessions(calendar)
    evidence_hash = json.loads((DOCS / 'exp006_availability_contract_v002.json').read_bytes())['evidence'][0]['sha256']
    records = []
    for row in sample['records']:
        cache = RAW/'headers/completed'/(digest({'url': row['header_url']}) + '.json')
        result = dict(row, status='UNAVAILABLE_NOT_VISITED', raw_acceptance=None)
        if cache.exists():
            receipt = json.loads(cache.read_bytes())
            body = Archive(RAW/'headers').read(receipt['body'])
            result['receipt'] = {k: receipt[k] for k in ('url', 'status', 'request_started_at_utc', 'retrieved_at_utc', 'body')}
            if receipt['status'] == 200:
                header = parse_header(body, cik=row['CIK'], accession=row['accession'], form=row['form'])
                result.update(raw_acceptance=header['acceptance_raw'], original_header=header)
                result.update(compare(row['bulk_acceptanceDateTime'], row['filed_date'], header['acceptance_raw'],
                                      header['FILED_AS_OF_DATE'], sessions, evidence_sha256=evidence_hash,
                                      contradictory=header['source_chronology_contradictory']))
                if result.get('raw_candidate_utc'):
                    bulk = datetime.fromisoformat(row['bulk_acceptanceDateTime'].replace('Z', '+00:00'))
                    result['literal_minus_seasonal_hours'] = (bulk-datetime.fromisoformat(result['raw_candidate_utc'][0])).total_seconds()/3600
                    result['lexical_clock_equals_original_raw'] = re.sub(r'\D', '', row['bulk_acceptanceDateTime'][:19]) == header['acceptance_raw']
            else: result['status'] = 'UNAVAILABLE_HTTP_' + str(receipt['status'])
        records.append(result)
    complete = all(r['status'] == 'PASS_DATE_DOMINANCE' for r in records)
    summary = {'version': 'EXP006_date_dominance_validation_v003', 'status': 'SCALABLE_ACCEPTANCE_DATE_BOUND_READY' if complete else 'DATE_BOUND_VALIDATION_BLOCKED',
               'policy_sha256': digest(policy), 'sample_sha256': digest(sample), 'sample_size': len(records),
               'status_counts': dict(Counter(r['status'] for r in records)),
               'raw_date_dominance_failures': sum(r.get('raw_date_later_than_envelope', False) for r in records),
               'earlier_eligible_opens': sum(r.get('earlier_eligible_open', False) for r in records),
               'same_eligible_opens': sum(r.get('eligible_open_relation') == 'SAME' for r in records),
               'later_eligible_opens': sum(r.get('eligible_open_relation') == 'LATER' for r in records),
               'same_day_envelope': sum(r.get('envelope_date') == max(r.get('raw_candidate_civil_dates', ['UNAVAILABLE'])) for r in records),
               'later_day_envelope': sum(bool(r.get('raw_candidate_civil_dates')) and r['envelope_date'] > max(r['raw_candidate_civil_dates']) for r in records),
               'delay_distribution': dict(Counter(str(r['delay_sessions']) for r in records if 'delay_sessions' in r)),
               'prior_v002_non_invariant_count': sum(r.get('raw_v002_invariant') is False for r in records),
               'year_quarter_form': dict(Counter(f"{r['year']}-Q{r['quarter']}-{r['form']}" for r in records)),
               'clock_stress_distribution': dict(Counter(t for r in records for t in r['stress_tags'])),
               'observed_offset_hours': dict(Counter(str(r['literal_minus_seasonal_hours']) for r in records if 'literal_minus_seasonal_hours' in r)),
               'exact_public_availability': 'UNKNOWN', 'policy_activated': False,
               'scope_limit': 'Expanded mechanical stress validation, not a proof that every unsampled bulk value is error-free; exact clock provenance stays unresolved. Census invalid/missing inputs remain unavailable.',
               'performance_evaluations': 0, 'confirmation_accesses': 0, 'records': records}
    write_public(EVIDENCE.name, summary)
    return {k: summary[k] for k in ('status','sample_size','raw_date_dominance_failures','same_eligible_opens','later_eligible_opens','earlier_eligible_opens','delay_distribution')}


def freeze_classification():
    if json.loads(EVIDENCE.read_bytes())['status'] != 'SCALABLE_ACCEPTANCE_DATE_BOUND_READY':
        raise ValueError('Timing gate not passed')
    m, sample, _ = verify_freeze()
    lookup = {(x['CIK'], x['accession']): x for x in load_inputs()}
    groups = defaultdict(list)
    for r in sample['records']: groups[(r['year'], r['quarter'], r['form'])].append(r)
    chosen = []
    for key, candidates in sorted(groups.items()):
        used = set()
        for positive in (True, False):
            ranked = sorted(candidates, key=lambda x: digest({'CIK': x['CIK'], 'accession': x['accession']}))
            matching = [r for r in ranked if r['accession'] not in used and (lookup[(r['CIK'],r['accession'])]['state']=='PRESENT_METADATA') == positive]
            fallback = not matching
            if fallback: matching = [r for r in ranked if r['accession'] not in used]
            r = matching[0]; used.add(r['accession'])
            label = lookup[(r['CIK'],r['accession'])]; meta = label['metadata']; name = meta['primary_document']
            if not name or '..' in name or not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:htm|html|txt)', name):
                url = None
            else: url = f"https://www.sec.gov/Archives/edgar/data/{int(r['CIK'])}/{r['accession'].replace('-', '')}/{name}"
            chosen.append(dict(r, target_bulk_positive=positive, target_label_fallback=fallback,
                               bulk_present=True if label['state']=='PRESENT_METADATA' else False if label['state']=='NOT_DECLARED_METADATA' else None,
                               primary_document=name, primary_url=url))
    dispatch = {'version': 'EXP006_primary_classification_sample_v003', 'frozen_at_utc': now(),
                'selection': m['classification_selection'], 'pass_condition': m['classification_pass'],
                'records': chosen, 'records_sha256': digest(chosen), 'body_start_ceiling': 96}
    write_public('exp006_primary_validation_sample_v003.json', dispatch)
    return dispatch


def acquire_classification():
    p = DOCS/'exp006_primary_validation_sample_v003.json'
    dispatch = json.loads(p.read_bytes())
    if digest(dispatch['records']) != dispatch['records_sha256']: raise ValueError('Primary sample changed')
    if (DOCS/'exp006_primary_validation_v003.json').exists(): return {'status': 'EXISTING_NO_REQUESTS'}
    h = client('primary', [r['primary_url'] for r in dispatch['records'] if r['primary_url']], 96)
    for i, r in enumerate(dispatch['records']):
        if not r['primary_url']: continue
        receipt, body = h.fetch(r['primary_url'], purpose='FROZEN_PRIMARY_ITEM202_CLASSIFICATION')
        print('Primary', i+1, '/', len(dispatch['records']), 'HTTP', receipt['status'], flush=True)
        if receipt['status'] != 200: break
    return validate_classification()


def validate_classification():
    p = DOCS/'exp006_primary_validation_sample_v003.json'
    dispatch = json.loads(p.read_bytes())
    headers = {(r['CIK'],r['accession']): r for r in json.loads(EVIDENCE.read_bytes())['records']}
    results = []
    for r in dispatch['records']:
        item = dict(CIK=r['CIK'], accession=r['accession'], form=r['form'], year=r['year'], quarter=r['quarter'],
                    bulk_present=r['bulk_present'], primary_present=None, status='UNAVAILABLE_NOT_VISITED')
        cache = RAW/'primary/completed'/(digest({'url': r['primary_url']}) + '.json')
        if r['primary_url'] and cache.exists():
            receipt = json.loads(cache.read_bytes()); body = Archive(RAW/'primary').read(receipt['body'])
            item['receipt'] = {k: receipt[k] for k in ('url','status','body','request_started_at_utc','retrieved_at_utc')}
            if receipt['status'] == 200:
                try: observation = primary_item202(body)
                except (UnicodeError, ValueError): observation = {'present': None, 'reason': 'Unsupported primary encoding/parser'}
                header = headers[(r['CIK'],r['accession'])]['original_header']
                header_present = '2.02' in header['source_items']
                item.update(primary_observation=observation, header_present=header_present,
                            header_sha256=header['source_sha256'], primary_present=observation['present'],
                            status='CLASSIFIED' if observation['present'] is not None else 'UNKNOWN_PRIMARY')
                if item['primary_present'] is not None and header_present != item['primary_present']:
                    item['status']='HEADER_PRIMARY_DISAGREEMENT'; item['primary_present']=None
            else: item['status']='UNAVAILABLE_HTTP_'+str(receipt['status'])
        results.append(item)
    counts = confusion(results)
    passed = counts['FP']==counts['FN']==counts['UNKNOWN']==0 and counts['sample_size']==96
    output = {'version': 'EXP006_primary_semantic_validation_v003', 'status': 'SCOPED_ITEM202_CLASSIFICATION_PASS' if passed else 'ITEM202_CLASSIFICATION_BLOCKED',
              'sample_sha256': digest(dispatch), 'pass_condition': dispatch['pass_condition'], **counts,
              'records': results, 'full_population_certified_Item202_count': None,
              'full_population_unknown_classification_count': 438666,
              'performance_evaluations': 0, 'confirmation_accesses': 0}
    write_public('exp006_primary_validation_v003.json', output)
    return {k: output[k] for k in ('status','TP','TN','FP','FN','UNKNOWN','coverage')}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('freeze','headers','validate','classify-freeze','classify','classify-validate'))
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    if a.mode in ('headers','classify') and not a.execute: p.error('Remote requests require --execute')
    functions = {'freeze': freeze, 'headers': acquire_headers, 'validate': validate_headers,
                 'classify-freeze': freeze_classification, 'classify': acquire_classification,
                 'classify-validate': validate_classification}
    print(functions[a.mode]())


if __name__ == '__main__': main()
