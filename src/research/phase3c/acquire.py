"""Explicit Phase3C source commands, bounded to one fixed metadata stress frame."""
import argparse
import json
import re

from src.research.phase3c.sources import DOCS, RAW, SourceHTTP, freeze_cohort, put, secret, require_cohort
from src.research.sec_pilot.parsing import digest

REVENUE = [
    ('AAPL', 320193), ('FB', 1326801), ('MSFT', 789019), ('AMZN', 1018724),
    ('GOOGL', 1652044), ('BRK.B', 1067983), ('INTC', 50863), ('CSCO', 858877),
    ('ORCL', 1341439), ('IBM', 51143), ('NVDA', 1045810), ('ADBE', 796343),
    ('CRM', 1108524), ('PEP', 77476), ('KO', 21344), ('PG', 80424), ('JNJ', 200406),
    ('MRK', 310158), ('PFE', 78003), ('WMT', 104169), ('HD', 354950), ('COST', 909832),
    ('MA', 1141391), ('V', 1403161), ('AXP', 4962), ('UNH', 731766),
    ('NKE', 320187), ('SBUX', 829224), ('TGT', 27419), ('QCOM', 804328)]
LIFECYCLE = [
    ('TWTR', 1418091, 'cash_acquisition'), ('ATVI', 718877, 'cash_acquisition'),
    ('XLNX', 743988, 'stock_acquisition'), ('CELG', 816284, 'mixed_acquisition'),
    ('ALXN', 899866, 'mixed_acquisition'), ('DUNK', 1357204, 'cash_acquisition'),
    ('WFM', 865436, 'cash_acquisition'), ('TIF', 98246, 'cash_acquisition'),
    ('YHOO', 1011006, 'rename_restructuring'), ('BBBY', 886158, 'bankruptcy_ending'),
    ('SHLD', 1310067, 'bankruptcy_ending'), ('HTZ', 1657853, 'bankruptcy_class_transition'),
    ('SUNE', 1563922, 'bankruptcy_ending'), ('DF', 931336, 'bankruptcy_ending'),
    ('PCG', 1004980, 'bankruptcy_restructuring'), ('JCP', 1166126, 'bankruptcy_ending'),
    ('KODK', 31235, 'bankruptcy_class_transition'), ('LB', 701985, 'rename_spinoff'),
    ('GE', 40545, 'spinoffs'), ('UTX', 101829, 'merger_rename_spinoff'),
    ('DD', 1666700, 'spinoff'), ('DOW', 1751788, 'spinoff_new_listing'),
    ('CBS', 813828, 'merger_rename'), ('VIAB', 1339947, 'merger_class_transition'),
    ('DIS', 1744489, 'new_parent_merger'), ('GOOG', 1652044, 'multiple_classes'),
    ('BRK.A', 1067983, 'multiple_classes'), ('BF.A', 14693, 'multiple_classes'),
    ('NWSA', 1564708, 'multiple_classes_exchange'), ('FOXA', 1754301, 'spinoff_multiple_classes')]

DOCUMENTS = {
    'OpenFIGI': ['https://www.openfigi.com/api/documentation', 'https://www.openfigi.com/about/terms'],
    'Tiingo': ['https://www.tiingo.com/documentation/end-of-day', 'https://www.tiingo.com/about/pricing',
               'https://www.tiingo.com/documentation/general/connecting', 'https://app.tiingo.com/tos/'],
    'FMP': ['https://site.financialmodelingprep.com/developer/docs/pricing',
            'https://site.financialmodelingprep.com/developer/docs/stable/delisted-companies']}


def rows():
    result = []
    for ticker, cik in REVENUE:
        result.append({'case_key': f'{cik:010d}|{ticker}', 'issuer_cik': f'{cik:010d}',
                       'historical_symbol_candidate': ticker, 'revenue_candidate': True,
                       'category': 'annual_original_chain', 'category_status': 'METADATA_STRESS_TARGET_NOT_CERTIFIED',
                       'reason': 'Named annual chain and exact-concept stress; no performance criterion',
                       'source': f'https://data.sec.gov/submissions/CIK{cik:010d}.json'})
    for ticker, cik, category in LIFECYCLE:
        result.append({'case_key': f'{cik:010d}|{ticker}', 'issuer_cik': f'{cik:010d}',
                       'historical_symbol_candidate': ticker, 'revenue_candidate': False,
                       'category': category, 'category_status': 'METADATA_STRESS_TARGET_NOT_CERTIFIED',
                       'reason': 'Named lifecycle challenge, to verify against original SEC evidence; no outcome-based replacement',
                       'source': f'https://data.sec.gov/submissions/CIK{cik:010d}.json'})
    return result


def discovery():
    frame = rows(); urls = {r['source'] for r in frame}
    http = SourceHTTP(urls | {u for urls in DOCUMENTS.values() for u in urls})
    # Freeze seed frame before source results; failing cases may never be replaced.
    put(RAW / 'seed_frame.json', {'rows': sorted(frame, key=lambda r: r['case_key']), 'price_access': False})
    docs = []; hashes = []; discovered = []
    for name, urls in DOCUMENTS.items():
        for url in urls:
            try:
                receipt, _ = http.fetch('Documentation', url)
                docs.append({'source': name, 'url': url, 'status': receipt['status'],
                             'source_sha256': receipt['body']['sha256'], 'bytes': receipt['body']['bytes'],
                             'retrieved_at_utc': receipt['retrieved_at_utc']})
            except ValueError:
                docs.append({'source': name, 'url': url, 'status': 'TRANSPORT_BLOCKED'})
    put(RAW / 'documentation_summary.json', docs)
    stopped = False
    for row in sorted(frame, key=lambda r: r['case_key']):
        evidence = []
        if not stopped:
            try:
                receipt, body = http.fetch('SEC', row['source'])
                if receipt['status'] != 200: raise ValueError('Discovery unavailable')
                metadata = json.loads(body)
                if int(metadata['cik']) != int(row['issuer_cik']): raise ValueError('CIK contradiction')
                evidence.append(receipt['body']['sha256']); hashes.extend(evidence)
            except (ValueError, KeyError, json.JSONDecodeError):
                stopped = (RAW / 'SEC_stop.json').exists()
        discovered.append(dict(row, discovery_hashes=evidence,
                               discovery_status='ACQUIRED_DISCOVERY_ONLY' if evidence else 'SOURCE_RETRIEVAL_FAILED'))
        print('Discovery cases examined:', len(discovered), flush=True)
    cohort = freeze_cohort(discovered, metadata_hashes=hashes)
    print('Frozen cases:', len(cohort['cases']), 'hash:', cohort['cohort_sha256'])


def filing_rows(data):
    return [{k: values[i] for k, values in data.items() if isinstance(values, list) and len(values) == len(data.get('accessionNumber', []))}
            for i in range(len(data.get('accessionNumber', [])))]


def sec_sources(*, compact=False, version='v002'):
    cohort = json.loads((DOCS / 'phase3c_pilot_cohort.json').read_bytes()); require_cohort(cohort)
    http = SourceHTTP({r['source'] for r in cohort['cases']})
    plans = []; seen = set()
    for original_row in cohort['cases']:
        row = dict(original_row)
        # GOOG/GOOGL and BRK.A/BRK.B share issuers but distinct class cases.
        row['revenue_candidate'] = any(r['revenue_candidate'] and r['issuer_cik'] == row['issuer_cik'] for r in cohort['cases'])
        cik = row['issuer_cik']
        if cik in seen: continue
        seen.add(cik)
        try:
            receipt, body = http.fetch('SEC', row['source']); data = json.loads(body)
            candidates = filing_rows(data['filings']['recent'])
            for part in data['filings'].get('files', []):
                # Only historical metadata parts intersecting required2018–2021.
                if part['filingTo'] >= '2018-01-01' and part['filingFrom'] <= '2021-12-31':
                    name = part['name']
                    if not re.fullmatch(r'CIK\d{10}-submissions-\d+\.json', name): raise ValueError('Unsafe discovery part')
                    url = 'https://data.sec.gov/submissions/' + name; http.allow(url)
                    _, content = http.fetch('SEC', url); candidates += filing_rows(json.loads(content))
            originals = []
            if row['revenue_candidate']:
                for year in ('2018', '2019', '2020'):
                    eligible = [r for r in candidates if r.get('form') == '10-K'
                                and r.get('reportDate', '').startswith(year) and r.get('filingDate', '') <= '2021-12-31']
                    if eligible: originals.append(min(eligible, key=lambda r: (r['filingDate'], r['accessionNumber'])))
            life = [r for r in candidates if r.get('form') in ('25', '25-NSE', '8-A', '8-A12B')
                    and r.get('filingDate', '') <= '2026-10-12']
            selected = originals + (sorted(life, key=lambda r: (r['filingDate'], r['accessionNumber']), reverse=True)[:1])
            plan = {'issuer_cik': cik, 'discovery_hash': receipt['body']['sha256'], 'originals': originals,
                    'lifecycle_documents': [r for r in selected if r not in originals]}
            for filing in selected:
                accession = filing['accessionNumber']
                if not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession): raise ValueError('Unsafe accession')
                base = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/'
                name = filing['primaryDocument']
                if not re.fullmatch(r'[A-Za-z0-9_.-]+', name): raise ValueError('Unsafe primary')
                sources = {}
                # Whole submission preserves acceptance and any original XBRL.
                roles = [('index', base + accession + '-index.htm')]
                roles += [('header', base + accession + '-index-headers.html')] if compact else [('submission', base + accession + '.txt')]
                for role, url in roles:
                    http.allow(url); rec, content = http.fetch('SEC', url)
                    sources[role] = rec
                    if rec['status'] != 200: break
                filing['sources'] = sources
                if filing['form'] == '10-K' and len(sources) == 2 and all(r['status'] == 200 for r in sources.values()):
                    from src.research.sec_pilot.acquisition import Boundary
                    from src.research.sec_pilot.__main__ import documents
                    boundary = Boundary({'accession': accession, 'index_url': base + accession + '-index.htm'})
                    try:
                        urls = documents(http.archive.read(sources['index']['body']), boundary)
                        # Primary/instance are exact names certified by archived index.
                        for role, url in urls.items():
                            http.allow(url); rec, _ = http.fetch('SEC', url); sources[role] = rec
                    except ValueError:
                        filing['document_resolution'] = 'UNAVAILABLE_REQUIRED_INSTANCE_OR_PRIMARY'
                put(RAW / ('filings_' + version if compact else 'filings') / (accession + '.json'), {'issuer_cik': cik, **filing})
            plans.append(plan)
            put(RAW / ('discovery_plans_' + version if compact else 'discovery_plans') / (cik + '.json'), plan)
            print('SEC issuer plans completed:', len(plans), flush=True)
        except Exception as error:
            plans.append({'issuer_cik': cik, 'status': 'SOURCE_RETRIEVAL_FAILED', 'error_type': type(error).__name__})
            if (RAW / 'SEC_stop.json').exists() and not compact: break
            if list((RAW / 'stops/SEC').glob('*.json')): break
    put(RAW / ('source_plan_summary_' + version + '.json' if compact else 'source_plan_summary.json'), plans)


def reviewed_compact_sources():
    stop = json.loads((RAW / 'SEC_stop.json').read_bytes())
    if stop.get('error_type') != 'ValueError' or stop.get('request_key') != '789768d4ebc9f2ba1426527d0efdc14d098c3513e560ec1c57884ad6e14c2bb3':
        raise ValueError('Different stop condition; review required')
    put(RAW / 'SEC_stop_review_v001.json', {
        'reviewed_stop_sha256': digest(stop), 'mode': 'INDEX_HEADER_PRIMARY_INSTANCE_ONLY',
        'reason': 'Original transport ValueError local64MiB byte ceiling on Intel full submission; preserve stop and forbid retry of original request',
        'limitation': 'Initial oversized response prefix was not retained by old transport; that attempt is unavailable, not a valid original-byte source',
        'scope': 'Same frozen cohort/filings, exact archived-index document names; no whole submission download;<=600SECstarts total'})
    sec_sources(compact=True, version='v003')


def openfigi():
    cohort = json.loads((DOCS / 'phase3c_pilot_cohort.json').read_bytes()); require_cohort(cohort)
    url = 'https://api.openfigi.com/v3/mapping'; http = SourceHTTP({url})
    token = secret('OPENFIGI_API_KEY'); headers = {'Content-Type': 'application/json'}
    if token: headers['X-OPENFIGI-APIKEY'] = token
    # Official docs disagree5vs10 jobs; use conservative5, max20requests/minute.
    records = []
    for start in range(0, len(cohort['cases']), 5):
        cases = cohort['cases'][start:start + 5]
        jobs = [{'idType': 'TICKER', 'idValue': r['historical_symbol_candidate'], 'exchCode': 'US',
                 'marketSecDes': 'Equity', 'includeUnlistedEquities': True} for r in cases]
        try:
            receipt, body = http.fetch('OpenFIGI', url, payload=jobs, headers=headers)
            result = json.loads(body)
            if receipt['status'] != 200 or not isinstance(result, list) or len(result) != len(cases):
                raise ValueError('OpenFIGI response shape or access failure')
            records.extend({'case_key': case['case_key'], 'result': item, 'source_sha256': receipt['body']['sha256']}
                           for case, item in zip(cases, result, strict=True))
        except ValueError:
            records.extend({'case_key': r['case_key'], 'status': 'SOURCE_RETRIEVAL_FAILED'} for r in cases)
            break
    put(RAW / 'openfigi_summary.json', records)
    print('OpenFIGI cases with retained results:', len(records))


def lifecycle_documents():
    cohort = json.loads((DOCS/'phase3c_pilot_cohort.json').read_bytes()); require_cohort(cohort)
    filings = [json.loads(p.read_bytes()) for p in (RAW/'filings_v003').glob('*.json')]
    http = SourceHTTP(set()); evidence = []
    for f in filings:
        if f['form'] == '10-K': continue
        name = f['primaryDocument']; accession = f['accessionNumber']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:xml|htm|html|pdf)',name): continue
        url = f'https://www.sec.gov/Archives/edgar/data/{int(f["issuer_cik"])}/{accession.replace("-", "")}/{name}'
        http.allow(url)
        try:
            receipt,_ = http.fetch('SEC',url)
            evidence.append({'issuer_cik':f['issuer_cik'],'accession':accession,'form':f['form'],
                             'filing_date':f['filingDate'],'source':receipt,'scope':'PRIMARY_LIFECYCLE_DOCUMENT_NOT_AUTOMATIC_TERMINAL_CERTIFICATE'})
        except ValueError:
            evidence.append({'issuer_cik':f['issuer_cik'],'accession':accession,'status':'SOURCE_RETRIEVAL_FAILED'})
            if list((RAW/'stops/SEC').glob('*.json')): break
    put(RAW/'lifecycle_primary_summary.json',evidence)
    print('Lifecycle primary documents examined:',len(evidence))


def merger_documents():
    """Ten named metadata event-date hypotheses; dates/terms need original verification."""
    from datetime import date
    targets = {'0001418091':'2022-10-27','0000718877':'2023-10-13','0000743988':'2022-02-14',
               '0000816284':'2019-11-20','0000899866':'2021-07-21','0001357204':'2020-12-15',
               '0000865436':'2017-08-28','0000098246':'2021-01-07','0000813828':'2019-12-04','0001339947':'2019-12-04'}
    cohort = json.loads((DOCS/'phase3c_pilot_cohort.json').read_bytes()); require_cohort(cohort)
    http = SourceHTTP(set()); outcomes = []
    for cik, hypothesized_date in targets.items():
        cases = [r for r in cohort['cases'] if r['issuer_cik']==cik]
        if not cases: raise ValueError('Lifecycle target outside frozen cohort')
        url=cases[0]['source']; http.allow(url); _,body=http.fetch('SEC',url); metadata=json.loads(body)
        rows_all=filing_rows(metadata['filings']['recent'])
        for part in metadata['filings'].get('files',[]):
            if part['filingFrom'] <= hypothesized_date <= part['filingTo']:
                u='https://data.sec.gov/submissions/'+part['name']; http.allow(u)
                rec,b=http.fetch('SEC',u); rows_all+=filing_rows(json.loads(b))
        target=date.fromisoformat(hypothesized_date)
        candidates=[r for r in rows_all if r['form']=='8-K' and '2.01' in r.get('items','') and
                    abs((date.fromisoformat(r['filingDate'])-target).days)<=14]
        if not candidates:
            outcomes.append({'issuer_cik':cik,'hypothesized_date':hypothesized_date,'status':'UNAVAILABLE_RELEVANT_PRIMARY'});continue
        f=min(candidates,key=lambda r:(abs((date.fromisoformat(r['filingDate'])-target).days),r['accessionNumber']))
        accession=f['accessionNumber']; base=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/'
        name=f['primaryDocument']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:htm|html|xml)',name):
            outcomes.append({'issuer_cik':cik,'status':'UNAVAILABLE_DOCUMENT_FORMAT'});continue
        refs={}
        for role,u in [('primary',base+name),('header',base+accession+'-index-headers.html')]:
            http.allow(u)
            try: refs[role],_=http.fetch('SEC',u)
            except ValueError: break
        outcomes.append({'issuer_cik':cik,'hypothesized_date':hypothesized_date,'accession':accession,
                         'filing_date':f['filingDate'],'status':'PRIMARY_EVENT_RETRIEVED_NOT_TERMINAL_CERTIFIED','sources':refs})
    put(RAW/'merger_primary_summary.json',outcomes)
    print('Bounded merger cases examined:',len(outcomes))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=('discovery', 'sec', 'sec-compact-reviewed', 'openfigi', 'lifecycle', 'mergers'))
    parser.add_argument('--execute', action='store_true'); args = parser.parse_args()
    if not args.execute: raise ValueError('Explicit source acquisition opt-in required')
    {'discovery': discovery, 'sec': sec_sources, 'sec-compact-reviewed': reviewed_compact_sources, 'openfigi': openfigi, 'lifecycle': lifecycle_documents, 'mergers': merger_documents}[args.command]()


if __name__ == '__main__': main()
