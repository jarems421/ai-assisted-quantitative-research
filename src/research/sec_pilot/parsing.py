"""Pinned offline parser with original-element reconciliation; isolated interpreter."""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import socket
from unittest.mock import patch


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


@contextmanager
def offline():
    original = socket.socket.connect
    def connect(sock, address):
        # Windows asyncio uses internal loopback socket pairs on import.
        if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
            return original(sock, address)
        raise ValueError('External network prohibited in offline parser')
    with patch.object(socket.socket, 'connect', connect), patch.object(socket, 'create_connection', side_effect=ValueError('Network prohibited')):
        yield


def parse(fixture, sources, *, code_git_sha):
    with offline():
        from lxml import etree as ET
        from edgar.sgml.sgml_common import FilingSGML
        from edgar.xbrl import XBRL
        from edgar.documents import parse_html
        if importlib.metadata.version('edgartools') != '5.62.0': raise ValueError('Pinned parser version required')
        sgml = FilingSGML.from_text(sources['submission'].decode('utf-8', errors='strict'))
        if (sgml.header.accession_number != fixture['accession'] or sgml.header.form != fixture['form']
                or sgml.header.cik is None or int(sgml.header.cik) != int(fixture['issuer_cik'])):
            raise ValueError('SGML issuer/accession/form mismatch')
        text = sources['submission'].decode('utf-8')
        accepted = re.search(r'<ACCEPTANCE-DATETIME>(\d{14})', text)
        if not accepted: raise ValueError('Missing SEC acceptance timestamp')
        # Preserve representation; UTC remains unknown until header/index timezone is reconciled.
        acceptance_raw = accepted[1]
        local_acceptance = datetime.strptime(acceptance_raw, '%Y%m%d%H%M%S')
        if local_acceptance.date().isoformat() > '2020-12-31': raise ValueError('Post-cutoff filing')
        instance = sources['instance']
        if b'<!DOCTYPE' in instance.upper() or b'<!ENTITY' in instance.upper():
            raise ValueError('External DTD/entity input prohibited')
        root = ET.fromstring(instance, ET.XMLParser(recover=False, resolve_entities=False, no_network=True))
        x = XBRL()
        x.parser.parse_instance_content(instance.decode('utf-8', errors='strict'))
        contexts = {}
        for node in root.findall('{http://www.xbrl.org/2003/instance}context'):
            key = node.get('id')
            if not key or key in contexts: raise ValueError('Duplicate/missing context ID')
            if key not in x.contexts: raise ValueError('Library omitted context')
            model = x.contexts[key]
            ns = {'i': 'http://www.xbrl.org/2003/instance'}
            identifier = node.find('.//i:identifier', ns)
            period_node = node.find('i:period', ns)
            if identifier is None or period_node is None: raise ValueError('Missing original entity/period')
            original_entity = {'scheme': identifier.get('scheme', ''), 'identifier': identifier.text}
            end = period_node.find('i:instant', ns)
            if end is not None:
                original_period = {'type': 'instant', 'instant': end.text}
            else:
                start = period_node.find('i:startDate', ns); end = period_node.find('i:endDate', ns)
                if start is None or end is None: raise ValueError('Unsupported original period')
                original_period = {'type': 'duration', 'startDate': start.text, 'endDate': end.text}
            if model.entity != original_entity or model.period != original_period:
                raise ValueError('Original entity/period differs from EdgarTools')
            contexts[key] = {'entity': model.entity, 'period': model.period, 'dimensions': model.dimensions,
                             'original_context_xml': ET.tostring(node, encoding='unicode'),
                             'locator': root.getroottree().getpath(node)}
        units = {}
        for node in root.findall('{http://www.xbrl.org/2003/instance}unit'):
            if node.get('id') in units: raise ValueError('Duplicate unit ID')
            units[node.get('id')] = ET.tostring(node, encoding='unicode')
        rows = []; groups = defaultdict(list)
        for node in root.iter():
            if not isinstance(node.tag, str) or not node.get('contextRef'): continue
            namespace, concept = (node.tag[1:].split('}', 1) if node.tag.startswith('{') else ('', node.tag))
            context = node.get('contextRef'); unit = node.get('unitRef')
            if context not in contexts or unit and unit not in units: raise ValueError('Missing fact context/unit')
            exact = ''.join(node.itertext())
            numeric = None
            nil = node.get('{http://www.w3.org/2001/XMLSchema-instance}nil') in ('true', '1')
            if unit and not nil:
                try:
                    n = Decimal(exact.strip())
                    if not n.is_finite(): raise ValueError('Nonfinite financial fact')
                    numeric = str(n)
                except InvalidOperation: pass
            locator = root.getroottree().getpath(node)
            row = {'accession': fixture['accession'], 'issuer_cik': fixture['issuer_cik'],
                   'source_sha256': hashlib.sha256(instance).hexdigest(), 'fact_locator': locator,
                   'namespace': namespace, 'concept': concept, 'context_ref': context,
                   'context': contexts[context], 'unit_ref': unit, 'unit_xml': units.get(unit),
                   'decimals': node.get('decimals'), 'exact_value': exact, 'numeric_value': numeric,
                   'nil': nil, 'status': 'UNAVAILABLE' if nil else 'OBSERVED_SOURCE',
                   'public_available_at_utc': None, 'availability_status': 'UNKNOWN',
                   'approved_eligibility_at_utc': None, 'identity_status': 'UNRESOLVED',
                   'security_id': None, 'historically_reconstructed': True}
            rows.append(row); groups[(namespace, concept, context, unit)].append(row)
        # Independently enumerate original elements; do not certify convenience aggregates.
        expected = Counter((r['namespace'], r['concept'], r['context_ref'], r['exact_value'].strip(), r['unit_ref']) for r in rows)
        observed = Counter((root.nsmap.get(f.element_id.split(':')[0], '') if ':' in f.element_id else '',
                            f.element_id.split(':')[-1], f.context_ref, f.value, f.unit_ref) for f in x.parser.facts.values())
        if expected != observed: raise ValueError('Original element / EdgarTools fact mismatch')
        for group in groups.values():
            if len({(r['exact_value'], r['decimals'], r['nil']) for r in group}) > 1:
                for r in group: r['status'] = 'AMBIGUOUS'
        primary_text = parse_html(sources['primary'].decode('utf-8', errors='strict')).text(
            include_tables=True, table_max_col_width=None)
        period = re.search(r'CONFORMED PERIOD OF REPORT:\s*(\d{8})', text)
        filed = re.search(r'FILED AS OF DATE:\s*(\d{8})', text)
        result = {'fixture': fixture, 'parser_version': '5.62.0', 'code_git_sha': code_git_sha,
                  'parser_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'config': {'encoding': 'utf-8-strict', 'xml_recovery': False, 'external_network': False,
                             'primary_text': 'edgartools.parse_html/full-document-tables-untruncated'},
                  'source_hashes': {k: hashlib.sha256(v).hexdigest() for k, v in sorted(sources.items())},
                  'acceptance_raw': acceptance_raw, 'accepted_at_utc': None,
                  'acceptance_timezone_status': 'UNRESOLVED_HEADER_INDEX_TIMEZONE',
                  'filing_date_raw': filed[1] if filed else None, 'report_period_raw': period[1] if period else None,
                  'submitting_cik': None, 'submitting_cik_status': 'UNKNOWN_NOT_INFERRED_FROM_ACCESSION',
                  'public_available_at_utc': None, 'availability_status': 'UNKNOWN',
                  'historically_reconstructed': True, 'facts': rows,
                  'security_bindings': [], 'asof_views': [],
                  'text_sections': [{'label': 'Full primary document; item segmentation not certified',
                    'source_sha256': hashlib.sha256(sources['primary']).hexdigest(), 'source_locator': 'entire_document',
                    'text_status': 'EXTRACTED_FULL_DOCUMENT', 'text': primary_text,
                    'normalized_text_sha256': hashlib.sha256(primary_text.encode()).hexdigest()}]}
        result['config_sha256'] = digest(result['config'])
        result['snapshot_sha256'] = digest(result)
        return result


def main():
    p = argparse.ArgumentParser(); p.add_argument('job'); p.add_argument('output'); a = p.parse_args()
    job = json.loads(Path(a.job).read_bytes()); sources = {}
    for name, record in job['sources'].items():
        path = Path(job['raw_root'])/record['body']['path']
        if not path.resolve().is_relative_to(Path(job['raw_root']).resolve()): raise ValueError('Parser path escape')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != record['body']['sha256'] or len(data) != record['body']['bytes']:
            raise ValueError('Parser input hash mismatch')
        sources[name] = data
    result = parse(job['fixture'], sources, code_git_sha=job['code_git_sha'])
    data = canonical(result)
    path = Path(a.output)
    if path.exists():
        if path.read_bytes() != data: raise ValueError('Immutable parser output differs')
    else:
        with path.open('xb') as f: f.write(data)
    print('PASS pinned offline parser; facts='+str(len(result['facts'])))


if __name__ == '__main__': main()
