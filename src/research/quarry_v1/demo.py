"""Fictional original -> custody -> Jev scripted ranking -> pending human inspection."""
from . import io, evidence as E
from src.research.jev_navigation_v1 import demo as D, workspace as W


def fixtures(root):
    route = {'id': 'SYN-TERMINAL', 'version': '1', 'locator': 'https://documents.example.org/order-1',
             'publisher': 'FICTIONAL harbour authority', 'expected_fields': ['asset', 'daily limit', 'units'],
             'question': 'Does F1 loading capacity precede independently recorded shipments?',
             'access_restrictions': [], 'originality_claim': 'ORIGINAL', 'expected_source_identity': 'order-1',
             'expected_asset': 'F1', 'availability_uncertainties': ['Fictional source; no historical availability'], 'stops': []}
    supplied = {'schema': 'QUARRY_SUPPLY_V001', 'route_id': route['id'], 'route_version': '1', 'fixture': 'SYNTHETIC',
                'data_classification': 'SYNTHETIC', 'title': 'Fictional order with unrelated asset appendix',
                'source_identity_claim': 'order-1', 'asset_claim': 'F1', 'source_version_claim': 'fictional-1',
                'retrieved_at_claim': 'UNKNOWN', 'retrieval_method_claim': 'synthetic test fixture',
                'historical_availability_claim': 'UNKNOWN', 'expected_original_sha256': 'UNKNOWN',
                'coverage': 'PARTIAL', 'limitations': ['Not a real document; no outcome or economic result'], 'missing_fields': ['independent shipments']}
    passages = [('A_WRONG_ASSET', 'Appendix: F2 terminal loading capacity shipments order: 900 tonnes/day.'),
                ('B_F1_ORDER', 'Order: F1 terminal loading permitted daily limit is reduced to 100 tonnes/day.'),
                ('C_AMBIGUOUS', 'Capacity: UNKNOWN. Units: UNKNOWN.')]
    raw = '\n'.join(t for _, t in passages).encode()
    io.write(root / 'original.txt', raw, raw=True)
    io.write(root / 'registry.json', {'schema': 'QUARRY_ROUTE_REGISTRY_V001', 'routes': [route]})
    io.write(root / 'supply.json', supplied)
    io.write(root / 'subject.json', D.subject())
    excerpts = []
    for key, passage in passages:
        start = raw.index(passage.encode())
        excerpts.append({'id': key, 'location': 'fictional section ' + key, 'start_byte': start,
                         'end_byte': start + len(passage.encode()), 'quote': passage})
    io.write(root / 'inspection.json', {'schema': 'QUARRY_INSPECTION_V001', 'mode': 'ORIGINAL_UTF8',
                                      'extraction_method_claim': 'exact UTF8 byte ranges', 'excerpts': excerpts})
    return route, supplied


def run(out):
    root = io.new_directory(out)
    fixtures(root)
    E.import_file(root / 'registry.json', root / 'supply.json', root / 'original.txt', root / 'custody')
    E.export(root / 'custody', root / 'inspection.json', root / 'subject.json', root / 'handoff')
    checked = E.validate_export(root / 'handoff')
    nav = io.ROOT / '.research' / ('jev-navigation-v1-' + root.name) if root.is_relative_to(io.ROOT) else root / 'navigation'
    W.prepare(checked['input'], nav)
    bundle = W.load(nav)[1]
    io.write(root / 'scripted.json', D.synthetic_response(bundle, {'B_F1_ORDER': {'predictor': 'yes', 'units': 'yes'},
                                                                 'C_AMBIGUOUS': {'predictor': 'unsure', 'units': 'unsure'}}))
    W.import_response(nav, root / 'scripted.json')
    report = W.report(nav)
    io.write(root / 'navigation-report.json', report)
    return {'fixture': 'SYNTHETIC_NOT_JEV_PERFORMANCE', 'package': str(root / 'handoff'),
            'order': [r['id'] for r in report['inspection_queue']], 'human_review': 'PENDING',
            'ready': False, 'external_requests_started': 0, 'authorises': []}
