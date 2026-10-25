"""Offline custody and handoff regressions; no source truth or effectiveness claims."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.research.spec import canonical
from src.research.quarry_v1 import evidence as E, io, demo as D
from src.research.quarry_v1.acquisition import plan, public_locator
from src.research.jev_navigation_v1 import workspace as W


class QuarryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.route, self.supplied = D.fixtures(self.root)
        self.custody = self.root / 'custody'

    def change(self, name, value):
        (self.root / name).write_bytes(canonical(value))

    def ingest(self, file='original.txt'):
        return E.import_file(self.root / 'registry.json', self.root / 'supply.json',
                             self.root / file if file else None, self.custody)

    def handoff(self):
        self.ingest()
        root = self.root / 'export'
        E.export(self.custody, self.root / 'inspection.json', self.root / 'subject.json', root)
        return root

    def test_preserved_original_and_unknown_authenticity(self):
        before = (self.root / 'original.txt').read_bytes()
        receipt = self.ingest()
        self.assertEqual((self.custody / 'original.bin').read_bytes(), before)
        self.assertEqual(receipt['original_sha256'], io.sha(before))
        self.assertEqual(receipt['authenticity'], 'UNKNOWN')
        self.assertEqual(receipt['historical_availability'], 'UNKNOWN')
        status = E.status(self.custody)
        self.assertTrue(status['inspection_usable'])
        self.assertFalse(status['acquisition_permitted'])
        (self.root / 'original.txt').write_bytes(b'owner later changed supplied path')
        self.assertEqual(E.load(self.custody)['receipt'], receipt)
        with self.assertRaises(ValueError):
            self.ingest()
        self.assertEqual((self.custody / 'original.bin').read_bytes(), before)

    def test_original_and_metadata_tamper_are_detected(self):
        self.ingest()
        for name in ('original.bin', 'supply.json', 'registry.json', 'receipt.json'):
            path = self.custody / name
            raw = path.read_bytes()
            path.write_bytes(raw + b' ')
            with self.assertRaisesRegex(ValueError, 'TAMPERED'):
                E.load(self.custody)
            path.write_bytes(raw)

    def test_wrong_source_asset_and_hash_are_retained_but_not_exported(self):
        self.supplied.update(source_identity_claim='wrong-document', asset_claim='F2', expected_original_sha256='0' * 64)
        self.change('supply.json', self.supplied)
        receipt = self.ingest()
        self.assertEqual(receipt['identity_flags'], ['WRONG_SOURCE_CLAIM_MISMATCH', 'WRONG_ASSET_CLAIM_MISMATCH', 'WRONG_ORIGINAL_HASH'])
        self.assertFalse(E.status(self.custody)['inspection_usable'])
        self.assertEqual(E.status(self.custody)['inspection_scope'], 'IDENTITY_RECONCILIATION_REQUIRED')
        with self.assertRaisesRegex(ValueError, 'wrong or unknown'):
            E.export(self.custody, self.root / 'inspection.json', self.root / 'subject.json', self.root / 'bad')

    def test_missing_metadata_fails_before_claim_and_unknown_stays_unknown(self):
        bad = copy.deepcopy(self.supplied); del bad['retrieved_at_claim']
        self.change('supply.json', bad)
        with self.assertRaises(ValueError):
            self.ingest()
        self.assertFalse(self.custody.exists())
        self.change('supply.json', self.supplied)
        self.ingest()
        self.assertEqual(E.load(self.custody)['supply']['retrieved_at_claim'], 'UNKNOWN')

    def test_failed_import_is_partial_and_cannot_be_retried(self):
        with self.assertRaises(ValueError):
            self.ingest('missing.txt')
        self.assertEqual(E.status(self.custody)['status'], 'PARTIAL_OR_INTERRUPTED')
        with self.assertRaises(ValueError):
            self.ingest()

    def test_unavailable_is_negative_record_not_falsification(self):
        self.supplied.update(coverage='UNAVAILABLE', limitations=['ordinary access failed; no economic conclusion'])
        self.change('supply.json', self.supplied)
        self.ingest(None)
        self.assertEqual(E.status(self.custody)['status'], 'UNAVAILABLE')
        self.assertFalse(E.status(self.custody)['inspection_usable'])
        self.assertTrue(E.status(self.custody)['negative_record_inspectable'])
        self.assertFalse(E.status(self.custody)['acquisition_permitted'])
        text = (self.supplied['title'] + '\nUNAVAILABLE\n' + '\n'.join(self.supplied['limitations'] + self.supplied['missing_fields'])).encode()
        inspection = {'schema': 'QUARRY_INSPECTION_V001', 'mode': 'ORIGINAL_UTF8', 'extraction_method_claim': 'negative metadata only',
                      'excerpts': [{'id': 'NEGATIVE', 'location': 'retained access limitation', 'start_byte': 0, 'end_byte': len(text), 'quote': text.decode()}]}
        self.change('inspection.json', inspection)
        E.export(self.custody, self.root / 'inspection.json', self.root / 'subject.json', self.root / 'export')
        checked = E.validate_export(self.root / 'export')
        self.assertEqual(checked['bundle']['request']['records'][0]['availability'], 'UNAVAILABLE')

    def test_stopped_route_copy_remains_stopped_through_jev(self):
        stop = {'id': 'STOP-1', 'scope': 'host-wide', 'reason': 'retained denial; no retries',
                'citation': 'synthetic stop receipt', 'citation_sha256': 'UNKNOWN'}
        self.route['stops'] = [stop]
        self.change('registry.json', {'schema': 'QUARRY_ROUTE_REGISTRY_V001', 'routes': [self.route]})
        out = self.handoff()
        checked = E.validate_export(out)
        status = E.status(self.custody)
        self.assertTrue(status['inspection_usable'])
        self.assertFalse(status['acquisition_permitted'])
        self.assertEqual(status['source_access']['stops'], [stop])
        W.prepare(checked['input'], self.root / 'nav')
        report = W.report(self.root / 'nav')
        self.assertTrue(all(r['availability'] == 'STOPPED' for r in report['inspection_queue']))
        self.assertIn('do not fetch', report['inspection_queue'][0]['inspection_task'])
        self.assertEqual(checked['provenance']['route']['stops'], [stop])
        self.assertEqual(report['authorises'], [])

    def test_export_is_portable_and_originals_distinct_from_excerpts(self):
        out = self.handoff()
        E.validate_export(out)
        self.assertTrue((out / 'source/original.bin').exists())
        self.assertNotEqual((out / 'source/original.bin'), out / 'text.txt')
        human = io.json_file(out / 'human-inspection.json')
        self.assertFalse(human['prospective_anvil']['ready'])
        self.assertEqual(human['fixture'], 'SYNTHETIC')
        # Changing the initial custody path cannot affect the portable copied package.
        (self.custody / 'original.bin').write_bytes(b'bad')
        E.validate_export(out)

    def test_resealed_restriction_removal_and_wrong_source_are_refused(self):
        out = self.handoff()
        data = io.json_file(out / 'input.json')
        data['documents'][0]['limitations'] = []
        (out / 'input.json').write_bytes(canonical(data))
        manifest = io.json_file(out / 'manifest.json')
        manifest['files']['input.json'] = io.sha((out / 'input.json').read_bytes())
        (out / 'manifest.json').write_bytes(canonical(manifest))
        with self.assertRaisesRegex(ValueError, 'restriction binding'):
            E.validate_export(out)

    def test_exact_excerpt_offsets_and_locations_required(self):
        self.ingest()
        inspection = io.json_file(self.root / 'inspection.json')
        inspection['excerpts'][0]['start_byte'] += 1
        self.change('inspection.json', inspection)
        with self.assertRaisesRegex(ValueError, 'byte range'):
            E.export(self.custody, self.root / 'inspection.json', self.root / 'subject.json', self.root / 'export')

    def test_human_passport_and_manifest_membership_are_rederived(self):
        out = self.handoff()
        human = io.json_file(out / 'human-inspection.json')
        human['source_passport']['locator'] = 'https://wrong.example.org/unrelated'
        (out / 'human-inspection.json').write_bytes(canonical(human))
        manifest = io.json_file(out / 'manifest.json')
        manifest['files']['human-inspection.json'] = io.sha(io.read(out / 'human-inspection.json'))
        (out / 'manifest.json').write_bytes(canonical(manifest))
        with self.assertRaisesRegex(ValueError, 'passport metadata changed'):
            E.validate_export(out)
        del manifest['files']['human-inspection.json']
        (out / 'manifest.json').write_bytes(canonical(manifest))
        with self.assertRaisesRegex(ValueError, 'export files'):
            E.validate_export(out)

    def test_binary_original_with_explicit_unverified_text_extraction(self):
        (self.root / 'binary.pdf').write_bytes(b'%PDF-fixture-not-real\x00\xff')
        self.ingest('binary.pdf')
        inspection = io.json_file(self.root / 'inspection.json')
        inspection.update(mode='SUPPLIED_EXTRACTION', extraction_method_claim='owner supplied text, page claims unverified')
        inspection['excerpts'][0]['location'] = 'page 7, table 3 (owner claim, not independently verified)'
        self.change('inspection.json', inspection)
        E.export(self.custody, self.root / 'inspection.json', self.root / 'subject.json', self.root / 'export', extracted_path=self.root / 'original.txt')
        value = E.validate_export(self.root / 'export')
        self.assertEqual(value['bundle']['request']['records'][0]['availability'], 'SUPPLIED_EXCERPT')
        self.assertEqual((self.root / 'export/source/original.bin').read_bytes(), b'%PDF-fixture-not-real\x00\xff')
        handoff = io.json_file(self.root / 'export/human-inspection.json')
        self.assertEqual(handoff['schema'], 'QUARRY_HUMAN_INSPECTION_V002')
        info = handoff['evidence_inspection']
        self.assertEqual(info['accuracy'], 'UNVERIFIED_AGAINST_ORIGINAL')
        self.assertEqual(info['original']['sha256'], io.sha(b'%PDF-fixture-not-real\x00\xff'))
        self.assertEqual(info['supplied_text']['sha256'], io.sha(io.read(self.root / 'original.txt')))
        self.assertEqual(info['extraction_method_claim'], inspection['extraction_method_claim'])
        self.assertEqual(info['source_authenticity'], 'UNKNOWN')
        self.assertEqual(info['coverage'], self.supplied['coverage'])
        self.assertEqual(info['source_location_claims'][0]['location'], inspection['excerpts'][0]['location'])

    def test_historical_v001_handoff_is_still_valid_without_new_assurances(self):
        out = self.handoff()
        historical = E.human_inspection(E.load(out / 'source'))
        (out / 'human-inspection.json').write_bytes(canonical(historical))
        manifest = io.json_file(out / 'manifest.json')
        manifest['files']['human-inspection.json'] = io.sha(io.read(out / 'human-inspection.json'))
        (out / 'manifest.json').write_bytes(canonical(manifest))
        E.validate_export(out)
        self.assertNotIn('evidence_inspection', io.json_file(out / 'human-inspection.json'))

    def test_escape_private_paths_and_network_paths_are_refused_before_read(self):
        for name in ('../outside', 'C:/outside', '\\\\host\\share\\file'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                io.child(self.root, name)
        for name in ('.ssh/key', '.env', '.codex/auth.json'):
            with self.assertRaisesRegex(ValueError, 'credential'):
                io.read(self.root / name)

    def test_oversize_owner_file_is_refused_without_reading_payload(self):
        path = self.root / 'big.bin'
        with path.open('wb') as handle:
            handle.truncate(io.MAX_FILE + 1)
        with self.assertRaisesRegex(ValueError, 'bounded'):
            io.read(path)

    def test_full_offline_flow_ranks_supplied_records_and_keeps_authority_pending(self):
        result = D.run(self.root / 'demo')
        self.assertEqual(result['order'][0], 'B_F1_ORDER')
        self.assertEqual(result['external_requests_started'], 0)
        self.assertFalse(result['ready'])
        self.assertEqual(result['authorises'], [])

    def scope(self):
        return {'schema': 'QUARRY_ACQUISITION_SCOPE_V001', 'route_ids': [self.route['id']],
                'exact_urls': [self.route['locator']], 'allowed_hosts': ['documents.example.org'],
                'request_ceiling': 1, 'total_byte_ceiling': 1000, 'per_response_byte_ceiling': 1000,
                'minimum_interval_seconds': 1, 'timeout_seconds': 10}

    def test_acquisition_plan_is_disabled_and_exact_with_no_dispatcher(self):
        self.change('scope.json', self.scope())
        value = plan(self.root / 'registry.json', self.root / 'scope.json')
        self.assertEqual(value['status'], 'DISABLED_DESIGN_ONLY')
        self.assertEqual(value['external_requests_started'], 0)
        self.assertEqual(value['authorises'], [])
        self.assertEqual(value['historical_stop_reconciliation'], 'NOT_PERFORMED_REQUIRED_BEFORE_FUTURE_ACTIVATION')
        self.assertFalse(value['new_route_id_reopens_stopped_host'])

    def test_stops_and_restrictions_cannot_be_overridden_by_scope(self):
        self.route['access_restrictions'] = ['STOP pending exact source terms review']
        self.change('registry.json', {'schema': 'QUARRY_ROUTE_REGISTRY_V001', 'routes': [self.route]})
        self.change('scope.json', self.scope())
        with self.assertRaisesRegex(ValueError, 'access'):
            plan(self.root / 'registry.json', self.root / 'scope.json')

    def test_unrelated_private_or_expanded_acquisition_routes_are_refused(self):
        for url in ('http://example.org/x', 'https://127.0.0.1/x', 'https://a.internal/x', 'https://localhost/x',
                    'https://user:password@example.org/x', 'https://example.org:444/x', 'https://[::1]/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                public_locator(url)
        scope = self.scope(); scope['exact_urls'].append('https://other.example.org/expanded')
        self.change('scope.json', scope)
        with self.assertRaisesRegex(ValueError, 'expansion'):
            plan(self.root / 'registry.json', self.root / 'scope.json')
