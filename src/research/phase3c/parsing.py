"""Offline original-element SEC parsing; separate from immutable Phase2 parser."""
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html import unescape
from html.parser import HTMLParser
import re
import hashlib
from pathlib import Path

from src.research.sec_pilot.parsing import offline, digest
from src.research.sec_pilot.certification import unit_name

PARSER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class InlineFacts(HTMLParser):
    """Pure Phase3A rendering contract, without importing its research orchestrator."""
    def __init__(self):
        super().__init__(convert_charrefs=True); self.rows = []; self.stack = []; self.namespaces = {}
    def handle_starttag(self, tag, attrs):
        self.namespaces.update({k.split(':', 1)[1]: v for k, v in attrs if k.startswith('xmlns:')})
        if tag == 'ix:nonfraction':
            if self.stack: self.stack[-1]['nested_numeric'] = True
            self.stack.append({'attributes': dict(attrs), 'text': '', 'position': self.getpos(),
                               'namespaces': dict(self.namespaces), 'nested_numeric': False})
    def handle_data(self, text):
        for row in self.stack: row['text'] += text
    def handle_endtag(self, tag):
        if tag == 'ix:nonfraction' and self.stack: self.rows.append(self.stack.pop())


def reconcile_inline(selected, inline):
    if not selected['contributors']: return dict(selected, primary_reconciliation='UNAVAILABLE')
    original = selected['contributors'][0]; matches = []
    for node in inline.rows:
        if node['nested_numeric']: continue
        attrs = node['attributes']; name = attrs.get('name', '').split(':')
        if (len(name) != 2 or name[1] != original['concept'] or node['namespaces'].get(name[0]) != original['namespace']
                or attrs.get('contextref') != original['context_ref'] or attrs.get('unitref') != original['unit_ref']): continue
        try:
            form = attrs.get('format', '').split(':')[-1].lower()
            if form not in ('', 'numdotdecimal', 'num-dot-decimal', 'numcommadot'): continue
            number = Decimal(node['text'].strip().replace(',', '')) * (Decimal(10) ** int(attrs.get('scale', '0')))
            if attrs.get('sign') == '-': number = -number
            if number != Decimal(original['exact_value']): continue
            matches.append({'line': node['position'][0], 'column': node['position'][1], 'element_id': attrs.get('id'),
                            'scale': attrs.get('scale', '0'), 'sign': attrs.get('sign'), 'format': attrs.get('format'), 'normalized_value': str(number)})
        except (InvalidOperation, ValueError): continue
    return dict(selected, primary_reconciliation='PASS' if len(matches) >= len(selected['contributors']) else 'BLOCKED_INLINE_CONTEXT_UNIT_SCALE_MATCH',
                primary_locators=matches)


class Cover(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.stack = []; self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag == 'ix:nonnumeric':
            a = dict(attrs)
            self.stack.append({'concept': a.get('name', '').split(':')[-1], 'context': a.get('contextref'),
                               'text': '', 'locator': {'line': self.getpos()[0], 'column': self.getpos()[1], 'id': a.get('id')}})
    def handle_data(self, text):
        for row in self.stack: row['text'] += text
    def handle_endtag(self, tag):
        if tag == 'ix:nonnumeric' and self.stack: self.rows.append(self.stack.pop())


class DocumentIndex(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.cells = None; self.cell = None; self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.cells = []; self.links = []
        elif tag == 'td' and self.cells is not None: self.cell = ''
        elif tag == 'a' and self.cells is not None: self.links += [v for k,v in attrs if k == 'href']
    def handle_data(self, text):
        if self.cell is not None: self.cell += text
    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None: self.cells.append(self.cell.strip()); self.cell = None
        elif tag == 'tr' and self.cells is not None: self.rows.append((self.cells, self.links)); self.cells = None


def parse_original(filing, bodies):
    from lxml import etree as ET
    from importlib.metadata import version
    if version('edgartools') != '5.62.0': raise ValueError('Pinned parser version required')
    concept = 'RevenueFromContractWithCustomerExcludingAssessedTax'
    if not all(k in bodies for k in ('primary', 'instance', 'header')):
        return {'status': 'UNAVAILABLE_MISSING_ORIGINAL', 'accession': filing['accessionNumber']}
    header = unescape(bodies['header'].decode('utf-8', errors='strict'))
    accepted = re.search(r'ACCEPTANCE-DATETIME[>\s:]+(\d{14})', header)
    form = re.search(r'CONFORMED SUBMISSION TYPE:\s*([^\s<]+)', header)
    period = re.search(r'CONFORMED PERIOD OF REPORT:\s*(\d{8})', header)
    issuer_mentions = re.findall(r'CENTRAL INDEX KEY:\s*(\d+)', header)
    if not accepted or not form or form[1] != '10-K' or not period:
        return {'status': 'UNAVAILABLE_RESTATEMENT_OR_VERSION', 'accession': filing['accessionNumber']}
    end = datetime.strptime(period[1], '%Y%m%d').date().isoformat()
    if not any(int(c) == int(filing['issuer_cik']) for c in issuer_mentions): raise ValueError('Original header issuer mismatch')
    if end != filing['reportDate'] or filing['filingDate'] > '2021-12-31': raise ValueError('Filing chronology/period mismatch')
    data = bodies['instance']
    index = DocumentIndex(); index.feed(bodies['index'].decode('utf-8'))
    instance_name = filing['sources']['instance']['url'].rsplit('/',1)[-1]
    issuer_instance = any(len(cells) >= 4 and cells[3] == 'EX-101.INS' and any(link.rsplit('/',1)[-1] == instance_name for link in links)
                          for cells, links in index.rows)
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper(): raise ValueError('Unsafe XML')
    root = ET.fromstring(data, ET.XMLParser(recover=False, resolve_entities=False, no_network=True))
    ns = {'x': 'http://www.xbrl.org/2003/instance'}; contexts = {}; units = {}
    for node in root.findall('x:context', ns):
        identifier = node.find('x:entity/x:identifier', ns); p = node.find('x:period', ns)
        if identifier is None or p is None: raise ValueError('Incomplete original context')
        dims = node.findall('.//{http://xbrl.org/2006/xbrldi}explicitMember') + node.findall('.//{http://xbrl.org/2006/xbrldi}typedMember')
        if not node.get('id') or node.get('id') in contexts: raise ValueError('Duplicate/missing context identity')
        contexts[node.get('id')] = {'entity_cik': identifier.text.zfill(10), 'entity_scheme': identifier.get('scheme'),
                                    'dimensions': [ET.tostring(n).decode() for n in dims],
                                    'period': {ET.QName(n).localname: n.text for n in p}}
    for node in root.findall('x:unit', ns):
        if not node.get('id') or node.get('id') in units: raise ValueError('Duplicate/missing unit identity')
        units[node.get('id')] = ET.tostring(node).decode()
    with offline():
        from edgar.xbrl import XBRL
        x = XBRL(); x.parser.parse_instance_content(data.decode('utf-8'))
        parser_values = Counter((root.nsmap.get(f.element_id.split(':')[0], '') if ':' in f.element_id else '',
                                 f.element_id.split(':')[-1], f.context_ref, f.value.strip(), f.unit_ref) for f in x.parser.facts.values())
    original_values = Counter((ET.QName(n).namespace, ET.QName(n).localname, n.get('contextRef'), ''.join(n.itertext()).strip(), n.get('unitRef')) for n in root if n.get('contextRef'))
    if original_values != parser_values: raise ValueError('Pinned parser differs from original elements')
    observations = []
    for node in root:
        if not isinstance(node.tag, str): continue
        q = ET.QName(node)
        if q.localname != concept or not re.fullmatch(r'http://fasb.org/us-gaap/20\d{2}(?:-\d{2}-\d{2})?', q.namespace or '') or not node.get('contextRef'): continue
        if node.get('{http://www.w3.org/2001/XMLSchema-instance}nil') in ('true','1'): continue
        ctx = contexts[node.get('contextRef')]; unit = unit_name(units.get(node.get('unitRef')))
        if ctx['dimensions'] or ctx['entity_cik'] != filing['issuer_cik'] or ctx['entity_scheme'] != 'http://www.sec.gov/CIK' or unit != 'USD': continue
        p = ctx['period']
        if set(p) != {'startDate', 'endDate'}: continue
        duration = (datetime.fromisoformat(p['endDate']) - datetime.fromisoformat(p['startDate'])).days + 1
        if not 350 <= duration <= 380: continue
        value = ''.join(node.itertext()).strip()
        try:
            if not Decimal(value).is_finite(): continue
        except Exception: continue
        observations.append({'concept': concept, 'namespace': q.namespace, 'entity_cik': ctx['entity_cik'],
                             'dimensions': [], 'unit': unit, 'value': value, 'decimals': node.get('decimals'),
                             'start': p['startDate'], 'end': p['endDate'], 'context_ref': node.get('contextRef'),
                             'unit_ref': node.get('unitRef'), 'unit_xml': units[node.get('unitRef')],
                             'locator': root.getroottree().getpath(node)})
    primary = bodies['primary'].decode('utf-8', errors='strict'); inline = InlineFacts(); inline.feed(primary)
    cover = Cover(); cover.feed(primary)
    current = [r for r in observations if r['end'] == end]
    def select(values):
        distinct = {(r['value'], r['decimals'], r['start'], r['end']) for r in values}
        if len(distinct) != 1: return None
        first = values[0]
        # Build the established inline reconciliation input; no new rendering heuristics.
        selected = {'contributors': [{'concept': concept, 'namespace': r['namespace'], 'context_ref': r['context_ref'],
                                      'unit_ref': r['unit_ref'], 'exact_value': r['value']} for r in values]}
        check = reconcile_inline(selected, inline)
        # Non-inline2018 originals require direct primary-statement reconciliation not implemented here.
        direct_original = issuer_instance and not inline.rows
        return dict(first, duplicate_count=len(values), original_element_reconciled=check.get('primary_reconciliation') == 'PASS' or direct_original,
                    primary_statement_reconciliation='PASS_INLINE' if check.get('primary_reconciliation') == 'PASS' else 'NOT_CERTIFIED_NON_INLINE',
                    instance_role='ORIGINAL_ISSUER_EX101_INSTANCE' if issuer_instance else 'SEC_EXTRACTED_INLINE_INSTANCE',
                    primary_locators=check.get('primary_locators', []))
    revenue = select(current)
    alternatives = sorted({r['end'] for r in observations if r['end'] < end}, reverse=True)
    comparable = select([r for r in observations if alternatives and r['end'] == alternatives[0]])
    source_hash = filing['sources']['instance']['body']['sha256']
    return {'issuer_cik': filing['issuer_cik'], 'accession': filing['accessionNumber'], 'form': '10-K', 'version': 'ORIGINAL',
            'filing_date': filing['filingDate'], 'acceptance_raw': accepted[1], 'period_end': end,
            'period_start': revenue['start'] if revenue else end, 'revenue': revenue, 'comparative': comparable,
            'source_sha256': source_hash, 'source_hashes': {k: v['body']['sha256'] for k, v in filing['sources'].items()},
            'all_exact_concept_observation_count': len(observations), 'taxonomy_versions': sorted({r['namespace'] for r in observations}),
            'accounting_basis_status': 'UNRESOLVED', 'entity_scope_status': 'UNRESOLVED',
            'basis_evidence': None, 'scope_evidence': None,
            'cover_observations': [r for r in cover.rows if r['concept'] in ('Security12bTitle', 'TradingSymbol', 'SecurityExchangeName')],
            'parser_original_reconciliation': 'PASS', 'public_available_at_utc': None,
            'status': 'PARSED_ORIGINAL_ONLY_NOT_CHAIN_CERTIFIED'}


def main():
    import json, sys
    from pathlib import Path
    import hashlib
    job = json.loads(Path(sys.argv[1]).read_bytes()); bodies = {}
    if job.get('parser_source_sha256') != PARSER_SHA256: raise ValueError('Parser changed since source job was pinned')
    for key, receipt in job['sources'].items():
        path = Path(job['raw_root']) / receipt['body']['path']; raw = path.read_bytes()
        if not path.resolve().is_relative_to(Path(job['raw_root']).resolve()) or hashlib.sha256(raw).hexdigest() != receipt['body']['sha256']:
            raise ValueError('Original byte provenance failure')
        bodies[key] = raw
    result = parse_original(job, bodies)
    result['config'] = {'external_network': False, 'parser': 'edgartools5.62.0', 'revenue_concept_fallback': False}
    result['code_sha256'] = PARSER_SHA256
    result['code_git_sha'] = job.get('code_git_sha')
    from src.research.phase3c.sources import put
    put(Path(sys.argv[2]), result)


if __name__ == '__main__': main()
