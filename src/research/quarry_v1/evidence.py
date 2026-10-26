"""Portable custody packages, reproducible excerpts and non-authoritative handoffs."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from src.research.spec import digest
from src.research.jev_navigation_v1 import contracts as J, navigation as N
from . import contracts as K, io

PACKAGE = 'QUARRY_PACKAGE_MANIFEST_V001'
EXPORT = 'QUARRY_EXPORT_MANIFEST_V001'
BANNER = 'SUPPLIED COPY / INSPECTION ONLY — AUTHENTICITY, M AND READINESS NOT ESTABLISHED'


def import_file(registry_path, supply_path, original_path, out):
    supplied = K.supply(io.json_file(supply_path))
    K.need(supplied['schema'] != K.SUPPLY_V002, 'QUARRY_SUPPLY_V002 enters Quarry only through source custody '
           '(python -m src.research.source_custody_v1 import), which verifies the native retrieval records')
    return _import(registry_path, supplied, original_path, out, {})


def import_retrieved(registry_path, supply_path, original_path, out, retained, *, source_base):
    """The only V002 creation API. Native verification at creation, not just portable consistency.

    It re-runs Source Retrieval's verification of the named attempt under source_base (through the custody
    bridge's read-only preflight) and requires the retained receipt, result and original to be byte-identical
    to the native records. A later load can re-check only the portable consistency of what was retained.
    Within trusted Python this is a procedural boundary: code that rewrites a whole native attempt directory,
    or calls _import directly, is outside it.
    """
    supplied = K.supply(io.json_file(supply_path))
    K.need(supplied['schema'] == K.SUPPLY_V002, 'import_retrieved accepts only QUARRY_SUPPLY_V002')
    raw = io.read(original_path)
    K.retained(supplied, retained, io.sha(raw), len(raw))
    from src.research.source_custody_v1 import custody  # Native verification lives with the custody bridge.
    r = supplied['system_retrieval']
    native = custody.preflight(source_base, r['attempt_id'], r['requested_url'])
    K.need((native['receipt_raw'], native['result_raw'], native['body'], native['registry_raw'], native['route']['id'], native['route']['version'])
           == (retained['retrieval-receipt.json'], retained['retrieval-result.json'], raw, io.read(registry_path),
               supplied['route_id'], supplied['route_version']),
           'NATIVE_MISMATCH: retained records or registry differ from the verified native Source Retrieval records')
    return _import(registry_path, supplied, original_path, out, retained)


def _import(registry_path, supplied, original_path, out, retained):
    registry = K.registry(io.json_file(registry_path))
    route = next((r for r in registry['routes'] if r['id'] == supplied['route_id']), None)
    K.need(route is not None and route['version'] == supplied['route_version'], 'wrong source route/version')
    K.binding(route, supplied)
    K.need((original_path is None) == (supplied['coverage'] == 'UNAVAILABLE'), 'unavailable source must have no original; other imports require a file')
    # Validate paths and metadata first. A failure after the claim leaves an explicit interrupted state.
    if original_path is not None:
        io.safe_path(original_path)
    root = io.new_directory(out)
    claim = {'schema': 'QUARRY_IMPORT_CLAIM_V001', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
             'registry_sha256': digest(registry), 'supply_sha256': digest(supplied), 'authorises': []}
    io.write(root / 'claim.json', claim)
    io.write(root / 'registry.json', registry)
    io.write(root / 'supply.json', supplied)
    names = ['claim.json', 'registry.json', 'supply.json']
    original_hash, size = None, 0
    try:
        if original_path is not None:
            raw = io.read(original_path)
            io.write(root / 'original.bin', raw, raw=True)
            names.append('original.bin')
            original_hash, size = io.sha(raw), len(raw)
        for name in sorted(retained):
            io.write(root / name, retained[name], raw=True)
            names.append(name)
        flags = identification(route, supplied, original_hash)
        receipt = {'schema': 'QUARRY_RECEIPT_V001', 'status': 'UNAVAILABLE' if original_path is None else 'RETAINED_COPY',
                   'original_sha256': original_hash, 'bytes': size, 'identity_flags': flags,
                   'authenticity': 'UNKNOWN', 'historical_availability': 'UNKNOWN', 'banner': BANNER, 'authorises': []}
        io.write(root / 'receipt.json', receipt)
        names.append('receipt.json')
        io.seal(root, names, PACKAGE)
        return receipt
    except (OSError, ValueError, TypeError) as error:
        io.write(root / 'failure.json', {'status': 'PARTIAL_OR_INTERRUPTED', 'fault_type': type(error).__name__, 'authorises': []})
        raise


def identification(route, supplied, original_hash):
    flags = []
    for expected, actual, code in [('expected_source_identity', 'source_identity_claim', 'WRONG_SOURCE'),
                                   ('expected_asset', 'asset_claim', 'WRONG_ASSET')]:
        if 'UNKNOWN' in (route[expected], supplied[actual]):
            flags.append(code + '_UNKNOWN')
        elif route[expected] != supplied[actual]:
            flags.append(code + '_CLAIM_MISMATCH')
    expected = supplied['expected_original_sha256']
    if original_hash is not None and expected != 'UNKNOWN' and original_hash != expected:
        flags.append('WRONG_ORIGINAL_HASH')
    return flags


def load(root):
    root = io.safe_path(root)
    manifest = io.verify_seal(root, PACKAGE)
    registry = K.registry(io.json_file(root / 'registry.json'))
    supplied = K.supply(io.json_file(root / 'supply.json'))
    route = next(r for r in registry['routes'] if r['id'] == supplied['route_id'])
    K.need(route['version'] == supplied['route_version'], 'source version changed')
    K.binding(route, supplied)
    receipt = io.json_file(root / 'receipt.json')
    original_hash = io.sha(io.read(root / 'original.bin')) if 'original.bin' in manifest['files'] else None
    retained = set(K.RETAINED) if supplied['schema'] == K.SUPPLY_V002 else set()
    expected_names = {'claim.json', 'registry.json', 'supply.json', 'receipt.json'} | ({'original.bin'} if original_hash else set()) | retained
    K.need(set(manifest['files']) == expected_names, 'incomplete or unexpected package files')
    K.need((supplied['coverage'] == 'UNAVAILABLE') == (original_hash is None), 'original presence mismatch')
    if retained:
        K.retained(supplied, {n: io.read(root / n) for n in K.RETAINED}, original_hash, len(io.read(root / 'original.bin')))
    K.need(receipt == {'schema': 'QUARRY_RECEIPT_V001', 'status': 'UNAVAILABLE' if original_hash is None else 'RETAINED_COPY',
                       'original_sha256': original_hash, 'bytes': len(io.read(root / 'original.bin')) if original_hash else 0,
                       'identity_flags': identification(route, supplied, original_hash), 'authenticity': 'UNKNOWN',
                       'historical_availability': 'UNKNOWN', 'banner': BANNER, 'authorises': []}, 'receipt inconsistent with preserved bytes')
    claim = io.json_file(root / 'claim.json')
    K.need(claim['registry_sha256'] == digest(registry) and claim['supply_sha256'] == digest(supplied), 'metadata binding changed')
    return {'root': root, 'manifest': manifest, 'route': route, 'supply': supplied, 'receipt': receipt}


def status(root):
    root = io.safe_path(root)
    if not (root / 'manifest.json').exists():
        K.need((root / 'claim.json').is_file(), 'not a Quarry import')
        return {'status': 'PARTIAL_OR_INTERRUPTED', 'usable': False,
                'usable_semantics': 'LEGACY_IDENTITY_CHECK_ONLY_NOT_ACCESS_PERMISSION',
                'inspection_usable': False, 'inspection_scope': 'INCOMPLETE_IMPORT',
                'negative_record_inspectable': False, 'source_access': 'UNKNOWN_INCOMPLETE_IMPORT',
                'acquisition_permitted': False, 'acquisition_dispatcher': 'NOT_IMPLEMENTED', 'authorises': []}
    package = load(root)
    no_flags = not package['receipt']['identity_flags']
    present = package['receipt']['original_sha256'] is not None
    return {**package['receipt'], 'usable': no_flags,
            'usable_semantics': 'LEGACY_IDENTITY_CHECK_ONLY_NOT_ACCESS_PERMISSION',
            'inspection_usable': present and no_flags,
            'inspection_scope': 'IDENTITY_RECONCILIATION_REQUIRED' if not no_flags else 'RETAINED_COPY_ONLY' if present else 'NEGATIVE_METADATA_ONLY',
            'negative_record_inspectable': not present and no_flags,
            'source_access': {'stops': package['route']['stops'], 'restrictions': package['route']['access_restrictions'],
                              'historical_stops_reconciled': False},
            'acquisition_permitted': False, 'acquisition_dispatcher': 'NOT_IMPLEMENTED'}


def documents_for(package, inspection, text):
    route, supplied, receipt = (package[k] for k in ('route', 'supply', 'receipt'))
    extracted_path = inspection['mode'] == 'SUPPLIED_EXTRACTION'
    availability = 'STOPPED' if route['stops'] else 'UNAVAILABLE' if supplied['coverage'] == 'UNAVAILABLE' else 'SUPPLIED_EXCERPT' if extracted_path else 'SUPPLIED_COPY'
    limits = [*supplied['limitations'], *route['access_restrictions'], *route['availability_uncertainties'],
              'Extraction and identity are supplied assertions; not verified measurements.',
              'Coverage: ' + supplied['coverage'], 'Missing fields: ' + ', '.join(supplied['missing_fields']),
              'Quarry original source version claim: ' + supplied['source_version_claim'],
              *['STOP ' + s['id'] + ': ' + s['scope'] + ' — ' + s['reason'] + ' — ' + s['citation'] for s in route['stops']]]
    documents = [{'id': e['id'], 'version': supplied['source_version_claim'], 'title': supplied['title'], 'source_id': route['id'],
                  'citation': {'artifact': {'base': 'INPUT', 'path': 'text.txt', 'sha256': io.sha(text)},
                               'location': e['location'] + f"; UTF8 bytes [{e['start_byte']},{e['end_byte']})", 'quote': e['quote']},
                  'availability': availability, 'original_sha256': receipt['original_sha256'] or 'UNKNOWN', 'limitations': limits}
                 for e in inspection['excerpts']]
    return documents


def human_inspection(package):
    """Original V001 handoff constructor, retained for historical package validation."""
    route, supplied = package['route'], package['supply']
    return {'schema': 'QUARRY_HUMAN_INSPECTION_V001', 'fixture': supplied['fixture'],
                                          'source_passport': {'route_id': route['id'], 'route_version': route['version'], 'locator': route['locator'],
                                                              'publisher': route['publisher'], 'access_restrictions': route['access_restrictions'],
                                                              'missing_fields': supplied['missing_fields'], 'stops': route['stops']},
                                          'prospective_anvil': {'status': 'PENDING_HUMAN_INSPECTION', 'ready': False,
                                                               'required_next': 'Inspect originals, exact study, Discovery V002 M/dispositions and independent owner-controlled trust through study_readiness_v1. No study or human review is created here.'},
                                          'banner': BANNER, 'authorises': []}


def human_inspection_v2(package, inspection, text):
    """Explicit extraction scope; offsets verify supplied text, not a PDF-to-text claim."""
    supplied, receipt = package['supply'], package['receipt']
    return {**human_inspection(package), 'schema': 'QUARRY_HUMAN_INSPECTION_V002',
            'evidence_inspection': {
                'original': {'path': 'source/original.bin' if receipt['original_sha256'] else None,
                             'sha256': receipt['original_sha256'] or 'UNKNOWN'},
                'supplied_text': {'path': 'text.txt', 'sha256': io.sha(text)},
                'mode': inspection['mode'], 'extraction_method_claim': inspection['extraction_method_claim'],
                'source_location_claims': [{'id': e['id'], 'location': e['location'],
                                           'start_byte': e['start_byte'], 'end_byte': e['end_byte']} for e in inspection['excerpts']],
                'accuracy': 'NO_ORIGINAL_METADATA_ONLY' if not receipt['original_sha256'] else 'UNVERIFIED_AGAINST_ORIGINAL' if inspection['mode'] == 'SUPPLIED_EXTRACTION' else 'EXACT_UTF8_RANGES_ONLY',
                'verified_scope': 'Excerpt byte ranges match retained text only; source meaning and measurement validity are not verified.',
                'source_authenticity': 'UNKNOWN', 'historical_availability': 'UNKNOWN',
                'coverage': supplied['coverage'], 'missing_fields': supplied['missing_fields'],
                'limitations': supplied['limitations'], 'access_restrictions': package['route']['access_restrictions'],
                'acquisition_permitted': False}}


def export(package_path, inspection_path, subject_path, out, *, extracted_path=None):
    package = load(package_path)
    route, supplied, receipt = (package[k] for k in ('route', 'supply', 'receipt'))
    K.need(not receipt['identity_flags'], 'wrong or unknown source/asset/hash; inspect retained original before any export')
    inspection = io.json_file(inspection_path)
    K.validate(K.INSPECTION, inspection)
    K.need(len({e['id'] for e in inspection['excerpts']}) == len(inspection['excerpts']), 'duplicate excerpt ID')
    K.need((extracted_path is not None) == (inspection['mode'] == 'SUPPLIED_EXTRACTION'), 'explicit extraction source required only in extraction mode')
    subject = io.json_file(subject_path)
    K.validate(J.SUBJECT, subject)
    if extracted_path is not None:
        K.need(receipt['original_sha256'] is not None, 'extraction requires retained original')
        text = io.read(extracted_path, 4 * 1024 * 1024)
    elif receipt['original_sha256'] is not None:
        text = io.read(package['root'] / 'original.bin', 4 * 1024 * 1024)
    else:
        # An unavailable route remains an inspectable negative record, never invented evidence.
        text = (supplied['title'] + '\nUNAVAILABLE\n' + '\n'.join(supplied['limitations'] + supplied['missing_fields'])).encode('utf-8')
    text.decode('utf-8')
    for excerpt in inspection['excerpts']:
        K.need(type(excerpt['start_byte']) is int and type(excerpt['end_byte']) is int
               and text[excerpt['start_byte']:excerpt['end_byte']] == excerpt['quote'].encode('utf-8'), 'excerpt must reproduce exact retained UTF-8 byte range')
    root = io.new_directory(out)
    io.write(root / 'claim.json', {'schema': 'QUARRY_EXPORT_CLAIM_V001', 'package_sha256': digest(package['manifest']), 'authorises': []})
    files = ['claim.json', 'inspection.json', 'text.txt', 'provenance.json', 'input.json', 'human-inspection.json']
    # Copy the entire bounded source package; handoffs do not depend on the import directory surviving.
    (root / 'source').mkdir()
    for name in [*package['manifest']['files'], 'manifest.json']:
        io.write(root / 'source' / name, io.read(package['root'] / name), raw=True)
        files.append('source/' + name)
    io.write(root / 'inspection.json', inspection)
    io.write(root / 'text.txt', text, raw=True)
    documents = documents_for(package, inspection, text)
    data = {'schema': J.INPUT, 'task': 'EVIDENCE_PROSPECTOR', 'data_classification': supplied['data_classification'],
            'subject': subject, 'documents': documents}
    K.validate(J.input_schema('EVIDENCE_PROSPECTOR'), data)
    io.write(root / 'input.json', data)
    io.write(root / 'provenance.json', {'schema': 'QUARRY_HANDOFF_V001', 'route': route, 'supply': supplied, 'receipt': receipt,
                                     'source_manifest_sha256': digest(package['manifest']), 'extraction_sha256': io.sha(text),
                                     'inspection_sha256': digest(inspection), 'banner': BANNER, 'authorises': []})
    io.write(root / 'human-inspection.json', human_inspection_v2(package, inspection, text))
    # Existing Jev contract and citation loader, no duplicated navigation or policy logic.
    N.derive(root / 'input.json')
    return io.seal(root, files, EXPORT)


def validate_export(root):
    root = io.safe_path(root)
    manifest = io.verify_seal(root, EXPORT)
    package = load(root / 'source')
    expected_files = {'claim.json', 'inspection.json', 'text.txt', 'provenance.json', 'input.json', 'human-inspection.json', 'source/manifest.json'} | {'source/' + name for name in package['manifest']['files']}
    K.need(set(manifest['files']) == expected_files, 'incomplete or unexpected export files')
    K.need(io.json_file(root / 'claim.json') == {'schema': 'QUARRY_EXPORT_CLAIM_V001', 'package_sha256': digest(package['manifest']), 'authorises': []}, 'export claim mismatch')
    provenance = io.json_file(root / 'provenance.json')
    K.need(provenance == {'schema': 'QUARRY_HANDOFF_V001', 'route': package['route'], 'supply': package['supply'], 'receipt': package['receipt'],
                         'source_manifest_sha256': digest(package['manifest']), 'extraction_sha256': io.sha(io.read(root / 'text.txt')),
                         'inspection_sha256': digest(io.json_file(root / 'inspection.json')), 'banner': BANNER, 'authorises': []}, 'handoff provenance mismatch')
    inspection = io.json_file(root / 'inspection.json')
    K.validate(K.INSPECTION, inspection)
    text = io.read(root / 'text.txt')
    if inspection['mode'] == 'ORIGINAL_UTF8' and package['receipt']['original_sha256']:
        K.need(text == io.read(root / 'source/original.bin'), 'original/excerpt separation violated')
    if package['receipt']['original_sha256'] is None:
        supplied = package['supply']
        negative_text = (supplied['title'] + '\nUNAVAILABLE\n' + '\n'.join(supplied['limitations'] + supplied['missing_fields'])).encode('utf-8')
        K.need(inspection['mode'] == 'ORIGINAL_UTF8' and text == negative_text, 'unavailable metadata cannot be invented evidence')
    for e in inspection['excerpts']:
        K.need(text[e['start_byte']:e['end_byte']] == e['quote'].encode(), 'excerpt offsets changed')
    bundle = N.derive(root / 'input.json')
    K.need(not package['receipt']['identity_flags'], 'wrong source/asset')
    expected_docs = sorted(documents_for(package, inspection, text), key=lambda d: d['id'])
    actual_docs = io.json_file(root / 'input.json')['documents']
    K.need(sorted(actual_docs, key=lambda d: d['id']) == expected_docs, 'source/citation/restriction binding changed')
    K.need(bundle['request']['data_classification'] == package['supply']['data_classification'], 'disclosure classification changed')
    human = io.json_file(root / 'human-inspection.json')
    expected_human = human_inspection(package) if human.get('schema') == 'QUARRY_HUMAN_INSPECTION_V001' else human_inspection_v2(package, inspection, text)
    K.need(human == expected_human, 'human inspection/passport metadata changed')
    return {'manifest': manifest, 'provenance': provenance, 'input': root / 'input.json', 'bundle': bundle, 'authorises': []}
