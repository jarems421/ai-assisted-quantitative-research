"""Offline source-certification audit of existing Phase 2 snapshots only."""
import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from src.research.sec_pilot.acquisition import ROOT, RAW, Archive
from src.research.sec_pilot.parsing import digest, canonical
from src.research.sec_pilot.certification import acceptance, proposed_bound, semantic, CONCEPTS, policy_view
from src.nexus.process_exp001 import session_dates
from src.research.store import RawStore

DOCS = ROOT/'docs/acceleration'
INTERPRETATIONS = ROOT/'data/raw/sec_source_certification/interpretations_v001'
DOCUMENTATION = ROOT/'data/raw/sec_source_certification/documentation_v001'
EVIDENCE = DOCS/'phase3a_evidence.json'
POLICY = {
    'version': 'sec_later_session_v001', 'status': 'PROPOSED_NOT_APPROVED',
    'source_cutoff': '2020-12-31', 'calendar_scope': ['2015-01-01', '2020-12-31'],
    'calendar': 'Existing frozen offline NYSE full-day session calendar; metadata only, no market observations',
    'calendar_source_sha256': hashlib.sha256((ROOT/'src/nexus/process_exp001.py').read_bytes()).hexdigest(),
    'rule': '09:30 America/New_York on the second exchange session strictly after max(acceptance wall-clock date, official SEC filing date)',
    'buffer': 'One complete subsequent exchange session before the eligible open, in addition to any SEC filing-date delay',
    'approval': None, 'public_available_at_utc': None,
    'activation_conditions': ['Explicit owner artifact matching policy and interpretation snapshot hashes',
                              'Certified acceptance conversion and consistent SEC filing date',
                              'Complete supported session calendar', 'Certified historical class binding for every contributor',
                              'Explicit acknowledgement of modeled public-availability uncertainty; required source evidence complete and no contradictions; all contributing versions pass'],
    'limitations': 'A modeled delay is not an observed public timestamp or guaranteed upper bound. SEC website lag has no guarantee. No real policy is approved.'}


class InlineFacts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.rows = []; self.stack = []; self.namespaces = {}
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.namespaces.update({k.split(':', 1)[1]: v for k, v in attrs if k.startswith('xmlns:')})
        if tag == 'ix:nonfraction':
            if self.stack: self.stack[-1]['nested_numeric'] = True
            self.stack.append({'attributes': attributes, 'text': '', 'position': self.getpos(),
                               'namespaces': dict(self.namespaces), 'nested_numeric': False})
    def handle_data(self, text):
        for row in self.stack: row['text'] += text
    def handle_endtag(self, tag):
        if tag == 'ix:nonfraction' and self.stack:
            self.rows.append(self.stack.pop())


def reconcile_inline(selected, inline):
    if not selected['contributors']: return dict(selected, primary_reconciliation='UNAVAILABLE')
    original = selected['contributors'][0]; matches = []
    for node in inline.rows:
        if node['nested_numeric']: continue  # An enclosing numeric rendering is not independently interpreted.
        attrs = node['attributes']; name = attrs.get('name', '').split(':')
        if (len(name) != 2 or name[1] != original['concept'] or node['namespaces'].get(name[0]) != original['namespace']
                or attrs.get('contextref') != original['context_ref'] or attrs.get('unitref') != original['unit_ref']): continue
        try:
            # Explicit Inline XBRL scale/sign; unsupported transformations fail rather than guess.
            form = attrs.get('format', '').split(':')[-1].lower()
            if form not in ('', 'numdotdecimal', 'num-dot-decimal', 'numcommadot'): continue
            raw = node['text'].strip().replace(',', '')
            number = Decimal(raw) * (Decimal(10) ** int(attrs.get('scale', '0')))
            if attrs.get('sign') == '-': number = -number
            if number != Decimal(original['exact_value']): continue
            matches.append({'line': node['position'][0], 'column': node['position'][1],
                            'element_id': attrs.get('id'), 'scale': attrs.get('scale', '0'),
                            'sign': attrs.get('sign'), 'format': attrs.get('format'), 'normalized_value': str(number)})
        except (InvalidOperation, ValueError): continue
    ok = len(matches) >= len(selected['contributors'])
    return dict(selected, status='CERTIFIED_FOR_SCOPED_FACTS' if ok else 'PARTIAL',
                primary_reconciliation='PASS' if ok else 'BLOCKED_INLINE_CONTEXT_UNIT_SCALE_MATCH',
                primary_locators=matches)


def text_probe(jobs):
    python = ROOT/'.research/sec-pilot-venv/Scripts/python.exe'
    code = '''import json,sys,hashlib
from pathlib import Path
from src.research.sec_pilot.parsing import offline
jobs=json.loads(sys.stdin.read()); result=[]
with offline():
 from edgar.documents import parse_html,ParserConfig
 for job in jobs:
  data=Path(job['path']).read_bytes()
  assert hashlib.sha256(data).hexdigest()==job['sha256']
  doc=parse_html(data.decode('utf-8'),ParserConfig(form='10-K'))
  items=[]
  for item in ('1','1A','7','8'):
   section=doc.sections.get_item(item)
   if section is None:items.append({'item':item,'status':'MISSING'});continue
   text=section.text()
   items.append({'item':item,'status':'CANDIDATE_ONLY','characters':len(text),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'replacement_characters':text.count(chr(65533))})
  result.append({'accession':job['accession'],'primary_sha256':job['sha256'],'config':{'form':'10-K'},'items':items,'status':'DEFERRED','reason':'Original-source start/end anchors and TOC exclusion not independently certified'})
print(json.dumps(result))'''
    result = subprocess.run([str(python), '-c', code], input=json.dumps(jobs), cwd=ROOT, capture_output=True, text=True)
    if result.returncode: raise ValueError('Pinned offline section assessment failed')
    return json.loads(result.stdout)


def identity_samples():
    import duckdb
    source_root = RAW.parent/'EXP004/production_inputs_v001'
    parts = sorted([p for year in (2019, 2020) for p in source_root.glob(f'bars_{year}*/parts/**/part-*.parquet')])
    if len(parts) != 8: return {'status': 'UNAVAILABLE', 'reason': 'Expected eight existing 2019/2020 source parts missing'}
    receipts = []
    for p in parts:
        hashes = json.loads((p.parents[2]/'part_hashes.json').read_bytes())
        match = [r for r in hashes if r['path'] == p.relative_to(ROOT).as_posix()]
        if len(match) != 1 or hashlib.sha256(p.read_bytes()).hexdigest() != match[0]['sha256']:
            raise ValueError('Existing identity source part hash mismatch')
        receipts.append(match[0])
    query = "SELECT ticker,security_id,min(day),max(day),count(*) FROM read_parquet(?) WHERE ticker IN ('AAPL','FB') GROUP BY ALL ORDER BY ticker,security_id"
    with duckdb.connect() as c: rows = c.execute(query, [[str(p) for p in parts]]).fetchall()
    return {'status': 'SOURCE_OBSERVED_NOT_CLASS_CERTIFIED', 'query': query, 'source_parts': receipts,
            'rows': [{'ticker': r[0], 'source_security_id': r[1], 'first_observed': str(r[2]), 'last_observed': str(r[3]), 'dated_observations': r[4]} for r in rows],
            'boundary': 'Only identifier/date counts inspected, no price values or returns; observed dates are not listing-effective spans. FIGI level and class mapping remain uncertified.'}


def build():
    p2 = json.loads((DOCS/'phase2_summary.json').read_bytes()); archive = Archive(RAW)
    docs = json.loads((DOCUMENTATION/'manifest.json').read_bytes())
    for source in docs:
        if source['status'] != 200 or hashlib.sha256((DOCUMENTATION/source['path']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Documentation hash/status mismatch')
    evidence_hash = digest([{k: r[k] for k in ('url', 'sha256')} for r in docs])
    financial = []; clocks = []; bindings = []; probe_jobs = []; all_views = []; comparatives = []
    private = RawStore(INTERPRETATIONS)
    for f in p2['filings']:
        accession = f['accession']; directory = RAW/accession
        job = json.loads((directory/'job.json').read_bytes())
        for source in job['sources'].values(): archive.read(source['body'])
        snapshot = json.loads((directory/'parsers'/f['parser_source_sha256']/'parsed.json').read_bytes())
        if digest({k: v for k, v in snapshot.items() if k != 'snapshot_sha256'}) != f['snapshot_sha256']:
            raise ValueError('Phase 2 snapshot changed')
        interpreted = acceptance(snapshot['acceptance_raw'], evidence_sha256=evidence_hash)
        filed = datetime.strptime(snapshot['filing_date_raw'], '%Y%m%d').date()
        sessions = sorted(session_dates(filed, min(filed+timedelta(days=20), date(2020, 12, 31))))
        interpreted.update(accession=accession, phase2_snapshot_sha256=f['snapshot_sha256'],
                           proposed_eligibility_at_utc=proposed_bound(snapshot['acceptance_raw'], filed.isoformat(), sessions),
                           eligibility_status='PROPOSED_NOT_APPROVED', filing_date=filed.isoformat())
        clocks.append(interpreted)
        primary = archive.read(job['sources']['primary']['body'])
        inline = InlineFacts(); inline.feed(primary.decode('utf-8'))
        rows = [reconcile_inline(semantic(snapshot, family), inline) for family in CONCEPTS]
        if snapshot['fixture']['issuer_cik'] == '0000320193':
            for fact in snapshot['facts']:
                if (fact['concept'] == 'EarningsPerShareDiluted' and not fact['context']['dimensions']
                        and fact['context']['period'].get('endDate') == '2019-09-28'):
                    candidate = {'accession': accession, 'period_end': '2019-09-28', 'value': fact['exact_value'],
                                 'source_sha256': fact['source_sha256'], 'context_ref': fact['context_ref']}
                    if candidate not in comparatives: comparatives.append(candidate)
        # Full alternative facts remain in the original snapshot; new interpretation never rewrites them.
        receipt = {'version': 'phase3a_v001', 'source_snapshot_sha256': f['snapshot_sha256'],
                   'acceptance': interpreted, 'semantic_results': rows, 'policy_sha256': digest(POLICY),
                   'code_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), Path(__file__).with_name('certification.py'))}}
        interpretation_hash = digest(receipt)
        private.write(accession+'/'+interpretation_hash+'.json', receipt)
        candidates = []
        for row in rows:
            first = row['contributors'][0] if row['contributors'] else None
            result = {'accession': accession, 'family': row['family'], 'status': row['status'], 'unit': row['unit'],
                      'alternatives_count': row['alternatives_count'], 'selected_duplicate_elements': row['candidate_count'],
                      'primary_sha256': job['sources']['primary']['body']['sha256'],
                      'primary_reconciliation': row['primary_reconciliation'], 'primary_locators': row.get('primary_locators', []),
                      'interpretation_sha256': interpretation_hash, 'transformation': row['transformation']}
            if first:
                result.update({k: first[k] for k in ('concept', 'namespace', 'context_ref', 'source_sha256', 'exact_value', 'decimals')})
                result.update(entity=first['context']['entity'], dimensions=first['context']['dimensions'], period=first['context']['period'],
                              instance_locators=[c['fact_locator'] for c in row['contributors']], comparative=False,
                              consolidated_status='Non-dimensional current annual issuer fact; reconciled primary inline elements')
            financial.append(result)
            candidates.append({'fact_key': accession+'/'+row['family'], 'semantic_status': row['status'],
                               'identity_status': 'PARTIAL', 'security_id': None, 'public_available_at_utc': None,
                               'contributors': [{'acceptance_status': interpreted['status'], 'accepted_at_utc': interpreted['accepted_at_utc'],
                                                'source_sha256': first['source_sha256'] if first else None, 'policy_sha256': digest(POLICY),
                                                'proposed_eligibility_at_utc': interpreted['proposed_eligibility_at_utc'], 'public_available_at_utc': None}]})
        all_views.append(policy_view(candidates, '2020-12-31T23:59:59Z', snapshot_sha256=digest(candidates), policy=POLICY))
        groups = defaultdict(dict)
        for fact in snapshot['facts']:
            if fact['concept'] in ('Security12bTitle', 'TradingSymbol', 'SecurityExchangeName'):
                groups[fact['context_ref']][fact['concept']] = fact
        for context, fields in groups.items():
            if 'Security12bTitle' not in fields or 'Common Stock' not in fields['Security12bTitle']['exact_value']: continue
            bindings.append({'accession': accession, 'issuer_cik': snapshot['fixture']['issuer_cik'], 'submitting_cik': None,
                             'class': fields['Security12bTitle']['exact_value'],
                             'historical_symbol': fields.get('TradingSymbol', {}).get('exact_value'),
                             'exchange': fields.get('SecurityExchangeName', {}).get('exact_value'),
                             'context_ref': context, 'effective_from': None, 'effective_to': None,
                             'evidence_filing_date': filed.isoformat(), 'source_sha256': fields['Security12bTitle']['source_sha256'],
                             'source_locator': fields['Security12bTitle']['fact_locator'],
                             'status': 'PROVISIONAL', 'coverage': 'Contemporaneous cover-page class/symbol disclosure only; no dated lifecycle bridge'})
        probe_jobs.append({'accession': accession, 'path': str(RAW/job['sources']['primary']['body']['path']), 'sha256': job['sources']['primary']['body']['sha256']})
    samples = identity_samples()
    for b in bindings:
        ids = [r for r in samples.get('rows', []) if r['ticker'] == b['historical_symbol']]
        b['source_observed_security_id'] = ids[0]['source_security_id'] if len(ids) == 1 else None
        b['identifier_status'] = 'VENDOR_OBSERVED_LEVEL_AND_CLASS_UNCERTIFIED'
    b_fact = next((f for f in snapshot['facts'] if f['concept'] == 'CommonStockSharesOutstanding' and any('ClassB' in v for v in f['context']['dimensions'].values())), None)
    bindings.append({'issuer_cik': '0001326801', 'class': 'Class B Common Stock (financial dimension)', 'historical_symbol': None,
                     'exchange': None, 'effective_from': None, 'effective_to': None, 'status': 'UNRESOLVED',
                     'source_observed_security_id': None, 'source_sha256': b_fact['source_sha256'] if b_fact else None,
                     'source_locator': b_fact['fact_locator'] if b_fact else None,
                     'coverage': 'Multiple classes source-observed; no Class B ticker/listing bridge supplied; Class A cannot be assigned to Class B'})
    text = text_probe(probe_jobs)
    return {'version': 'phase3a_v001', 'as_of': '2026-10-12', 'baseline_git_sha': subprocess.check_output(['git', 'rev-parse', '5570caa'], cwd=ROOT, text=True).strip(),
            'phase2_artifact_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (DOCS/'phase2_summary.json', DOCS/'phase2_report.md', DOCS/'phase2_validation.json')},
            'documentation': [{k: d[k] for k in ('id', 'url', 'sha256', 'bytes', 'retrieved_at_utc')} for d in docs],
            'acceptance_interpretations': clocks, 'policy': POLICY, 'policy_sha256': digest(POLICY),
            'financial_results': financial, 'apple_2019_eps_presentations': comparatives,
            'historical_identity_matrix': bindings, 'existing_identity_source_audit': samples,
            'text_assessment': text, 'unapproved_policy_views': all_views,
            'gates': {'Acceptance timestamp interpretation': 'PARTIAL', 'Exact public availability': 'UNKNOWN',
                      'Conservative eligibility policy': 'PROPOSED_NOT_APPROVED', 'Historical class identity': 'PARTIAL',
                      'Financial semantic interpretation': 'CERTIFIED_FOR_SCOPED_FACTS' if all(f['status'] == 'CERTIFIED_FOR_SCOPED_FACTS' for f in financial) else 'PARTIAL',
                      'Text segmentation': 'DEFERRED', 'Nexus historical execution': 'BLOCKED',
                      'Phase 3B design readiness': 'READY_FOR_CONDITIONAL_DESIGN'},
            'new_sec_filings_acquired': 0, 'nexus_operations': 0, 'performance_queries': 0, 'real_policy_approved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true')
    parser.add_argument('--report-only', action='store_true'); args = parser.parse_args()
    result = json.loads(EVIDENCE.read_bytes()) if args.report_only else build(); data = canonical(result)+b'\n'
    if not args.report_only:
        if args.check:
            if EVIDENCE.read_bytes() != data: raise ValueError('Phase 3A evidence differs')
        else: EVIDENCE.write_bytes(data)
    from src.research.sec_pilot.phase3a_report import render
    for name, content in render(result).items():
        path = DOCS/name
        if args.check:
            if path.read_text(encoding='utf-8') != content: raise ValueError('Phase 3A report differs: '+name)
        else: path.write_text(content, encoding='utf-8')
    print(json.dumps({'gates': result['gates'], 'scoped_facts': len(result['financial_results']), 'real_policy_approved': False}))


if __name__ == '__main__': main()
