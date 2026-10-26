"""Source custody V001: verified Source Retrieval bytes into native Quarry custody, export and Jev input.

Fictional hosts, injected fake transports and fictional human records only; network, DNS and processes are
denied. Passing fixtures establish no source truth, field meaning, authority or research progress.
"""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from src.research.spec import canonical, digest
from src.research.quarry_v1 import contracts as K, demo as QD, evidence as E, io as QIO
from src.research.jev_navigation_v1 import demo as JD, workspace as W
from src.research.source_custody_v1 import __main__ as CLI, custody as X
from src.research.source_v1 import retrieve as R, store as S
import tests.test_source_retrieval_v1 as SR

TEXT = ('Fictional order 1.\nOrder: F1 terminal loading permitted daily limit is reduced to 100 tonnes/day.\n'
        'Appendix: F2 terminal loading capacity shipments order: 900 tonnes/day.\n').encode('utf-8')
PASSAGE = 'Order: F1 terminal loading permitted daily limit is reduced to 100 tonnes/day.'


class CustodyTests(unittest.TestCase):
    # The Source Retrieval fixtures: fake transport and clock, fictional owner scope and attested stop snapshot.
    # Borrowed as functions (no TestCase class is imported into this module, so its tests are not collected twice).
    setUp, put, build, request, transport, dispatch, attempt = (getattr(SR.SourceRetrievalTests, n) for n in
                                                                 ('setUp', 'put', 'build', 'request', 'transport', 'dispatch', 'attempt'))

    def retrieve(self, responses=None, attempt='A1'):
        responses = {SR.URL1: {'body': TEXT, 'headers': [('Content-Type', 'text/plain; charset=utf-8')]}, **(responses or {})}
        self.fake = self.transport(responses)
        return self.dispatch(self.request(attempt), self.fake)

    def claims(self, attempt='A1', url=SR.URL1, name='claims.json', **changes):
        ctx = X.preflight(self.base, attempt, url)
        value = {'schema': X.CLAIMS, 'attested_by': SR.OWNER, 'attested_at': '2026-10-26T13:00:00+00:00', 'attempt_id': attempt,
                 'receipt_sha256': ctx['receipt_sha256'], 'body_sha256': ctx['receipt']['body_sha256'],
                 'title': 'Fictional order 1', 'source_identity_claim': 'doc-0', 'asset_claim': 'F1',
                 'source_version_claim': 'as retrieved', 'historical_availability_claim': 'UNKNOWN', 'data_classification': 'SYNTHETIC',
                 'limitations': ['Fictional fixture; no outcome or economic result.'], 'missing_fields': ['independent shipments'],
                 'statement': X.STATEMENT, **changes}
        return self.put(name, value)['path']

    def custody(self, name='pkg', **kw):
        return X.import_receipt(self.base, kw.pop('attempt', 'A1'), kw.pop('url', SR.URL1), kw.pop('claims', None) or self.claims(),
                                self.root / 'custody' / name, clock=self.clock.now)

    def inspection(self, text, quote=PASSAGE, mode='ORIGINAL_UTF8', start=None):
        start = text.index(quote.encode()) if start is None else start
        return self.put('inspection.json', {'schema': 'QUARRY_INSPECTION_V001', 'mode': mode, 'extraction_method_claim': 'exact UTF-8 byte ranges',
                                            'excerpts': [{'id': 'B_F1_ORDER', 'location': 'fictional order line 2', 'start_byte': start,
                                                          'end_byte': start + len(quote.encode()), 'quote': quote}]})['path']

    def export(self, package, text=TEXT, extracted=None, **kw):
        subject = self.put('subject.json', JD.subject())['path']
        return E.export(package, self.inspection(text, **kw), subject, self.root / 'export', extracted_path=extracted)

    # ---- end to end -----------------------------------------------------------------------------------------
    def test_verified_target_becomes_quarry_package_export_and_jev_input(self):
        self.retrieve()
        out = self.custody()
        self.assertEqual((out['coverage'], out['external_requests_started']), ('COMPLETE_CLAIMED', 0))
        package = E.load(out['package'])
        self.assertEqual((Path(out['package']) / 'original.bin').read_bytes(), TEXT)  # Immutable original bytes.
        supplied, retrieval = package['supply'], package['supply']['system_retrieval']
        ctx = X.preflight(self.base, 'A1', SR.URL1)
        self.assertEqual((supplied['schema'], supplied['fixture'], supplied['route_id'], supplied['route_version']),
                         ('QUARRY_SUPPLY_V002', 'SYSTEM_RETRIEVED', 'R0', '1'))
        self.assertEqual((retrieval['receipt_sha256'], retrieval['result_sha256'], retrieval['body_sha256'], retrieval['body_bytes']),
                         (ctx['receipt_sha256'], ctx['result_sha256'], S.sha(TEXT), len(TEXT)))
        self.assertEqual((retrieval['publication_authenticity'], retrieval['dataset_completeness'], retrieval['scientific_meaning']),
                         ('UNKNOWN', 'UNKNOWN', 'NOT_ESTABLISHED'))
        self.assertEqual((package['receipt']['identity_flags'], package['receipt']['authenticity']), ([], 'UNKNOWN'))
        self.assertTrue(E.status(out['package'])['inspection_usable'])
        manifest = self.export(out['package'])
        checked = E.validate_export(self.root / 'export')
        self.assertEqual(checked['provenance']['supply']['system_retrieval'], retrieval)
        document = json.loads(Path(checked['input']).read_bytes())['documents'][0]
        self.assertEqual((document['availability'], document['original_sha256'], document['citation']['quote']),
                         ('SUPPLIED_COPY', S.sha(TEXT), PASSAGE))
        limits = document['limitations']
        self.assertIn('Coverage: COMPLETE_CLAIMED', limits)
        self.assertTrue(any('publication authenticity, dataset completeness and scientific meaning are not established' in x for x in limits))
        self.assertTrue(any(ctx['receipt_sha256'] in x for x in limits))
        self.assertIn('Missing fields: independent shipments', limits)
        W.prepare(checked['input'], self.root / 'nav')  # The existing Jev workspace, unchanged.
        report = W.report(self.root / 'nav')
        self.assertEqual([r['id'] for r in report['inspection_queue']], ['B_F1_ORDER'])
        human = json.loads((self.root / 'export' / 'human-inspection.json').read_bytes())
        self.assertEqual((human['prospective_anvil']['status'], human['evidence_inspection']['accuracy']),
                         ('PENDING_HUMAN_INSPECTION', 'EXACT_UTF8_RANGES_ONLY'))
        self.assertEqual(manifest['authorises'], [])
        self.assertEqual(len(self.fake.opened), 3)  # Custody, export and Jev made no further transport call.

    def test_pdf_bytes_need_an_explicitly_supplied_extraction(self):
        pdf = b'%PDF-1.4 fictional scanned page \x00\xff\xfe'
        self.retrieve({SR.URL1: {'body': pdf}})
        out = self.custody()
        with self.assertRaises(ValueError):  # No silent text conversion or OCR of binary originals.
            self.export(out['package'])
        extracted = self.put('extracted.txt', TEXT)['path']
        self.export(out['package'], extracted=extracted, mode='SUPPLIED_EXTRACTION')
        human = json.loads((self.root / 'export' / 'human-inspection.json').read_bytes())
        self.assertEqual(human['evidence_inspection']['accuracy'], 'UNVERIFIED_AGAINST_ORIGINAL')

    def test_incorrect_extraction_byte_ranges_are_refused(self):
        self.retrieve()
        out = self.custody()
        with self.assertRaisesRegex(ValueError, 'exact retained UTF-8 byte range'):
            self.export(out['package'], start=TEXT.index(PASSAGE.encode()) + 1)

    # ---- coverage ---------------------------------------------------------------------------------------------
    def test_partial_and_unverified_transfers_keep_their_limits(self):
        cases = [('prefix', {'body': b'p' * 300000, 'declared': False, 'chunk': 65536}, 'PREFIX', 'PARTIAL', 'Only a prefix'),
                 ('unframed', {'body': TEXT, 'declared': False}, 'UNVERIFIED', 'UNKNOWN', 'no length framing')]
        for i, (name, spec, transfer, coverage, note) in enumerate(cases):
            with self.subTest(name):
                self.base = self.root / f'records-{name}'
                self.build()
                self.retrieve({SR.URL1: spec})
                out = self.custody(name=name)
                supplied = E.load(out['package'])['supply']
                self.assertEqual((supplied['system_retrieval']['transfer_coverage'], supplied['coverage']), (transfer, coverage))
                self.assertTrue(any(note in x for x in supplied['limitations']))
                for forged in ('COMPLETE_CLAIMED',):  # A partial transfer can never be represented as complete.
                    with self.assertRaisesRegex(ValueError, 'never COMPLETE'):
                        K.supply({**supplied, 'coverage': forged})
                with self.assertRaisesRegex(ValueError, 'never COMPLETE'):
                    K.supply({**supplied, 'system_retrieval': {**supplied['system_retrieval'], 'transfer_coverage': 'COMPLETE'}})

    # ---- refusals ---------------------------------------------------------------------------------------------
    def test_failed_denied_and_robots_responses_never_become_documents(self):
        cases = [('403', {SR.URL1: {'status': 403, 'body': b'<html>denied</html>'}}, SR.URL1),
                 ('206', {SR.URL1: {'status': 206, 'body': b'part'}}, SR.URL1),
                 ('gzip', {SR.URL1: {'body': b'\x1f\x8b', 'headers': [('Content-Encoding', 'gzip')]}}, SR.URL1),
                 ('robots', {}, SR.ROBOTS),
                 ('never retrieved', {SR.URL1: {'status': 403, 'body': b'denied'}}, SR.URL2)]
        for name, responses, url in cases:
            with self.subTest(name):
                self.base = self.root / f'records-{name}'
                self.build()
                self.retrieve(responses)
                with self.assertRaisesRegex(ValueError, 'NOT_CUSTODY_ELIGIBLE'):
                    X.preflight(self.base, 'A1', url)

    def test_interrupted_not_started_unanchored_and_inconsistent_attempts_are_refused(self):
        self.build(attest=False)
        self.retrieve()
        with self.assertRaisesRegex(ValueError, 'SOURCE_NOT_ELIGIBLE'):
            X.preflight(self.base, 'A1', SR.URL1)  # NOT_STARTED
        self.base = self.root / 'records-int'
        self.build()
        with self.assertRaises(KeyboardInterrupt):
            self.retrieve({SR.URL2: {'body': b'i' * 5000, 'chunk': 1000, 'interrupt_after': 2000}})
        with self.assertRaisesRegex(ValueError, 'SOURCE_NOT_FINISHED: the attempt is INTERRUPTED'):
            X.preflight(self.base, 'A1', SR.URL1)
        R.finalise_interrupted(self.base, 'A1', no_attempt_running=True, clock=self.clock.now)
        with self.assertRaisesRegex(ValueError, 'SOURCE_NOT_ELIGIBLE: a UNKNOWN attempt \\(interrupted\\)'):
            X.preflight(self.base, 'A1', SR.URL1)  # Even URL1's complete receipt: the attempt's effect is unknown.
        self.base = self.root / 'records-anchor'
        self.build()
        self.retrieve()
        result = self.attempt() / 'result.json'
        data = result.read_bytes()
        result.unlink()
        with self.assertRaisesRegex(ValueError, 'SOURCE_NOT_FINISHED: the attempt is RESULT_PENDING'):
            X.preflight(self.base, 'A1', SR.URL1)
        result.write_bytes(data.replace(b'"COMPLETE"', b'"PARTIAL"', 1))
        with self.assertRaisesRegex(ValueError, 'SOURCE_INCONSISTENT'):
            X.preflight(self.base, 'A1', SR.URL1)
        result.write_bytes(data)
        self.assertEqual(X.preflight(self.base, 'A1', SR.URL1)['route']['id'], 'R0')

    def test_altered_receipts_bodies_scopes_and_mismatched_identity_are_refused(self):
        self.retrieve()
        claims = self.claims()
        a = self.attempt()
        for target in ('raw/002.body', 'receipts/002.json', 'inputs/quarry-registry.json'):
            with self.subTest(target):
                path = a / target
                original = path.read_bytes()
                path.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValueError, 'SOURCE_INCONSISTENT|SCOPE_MISMATCH'):
                    X.preflight(self.base, 'A1', SR.URL1)
                path.write_bytes(original)
        for name, change, code in (('attempt', {'attempt_id': 'A9'}, 'CLAIMS_MISMATCH'), ('receipt', {'receipt_sha256': 'f' * 64}, 'CLAIMS_MISMATCH'),
                                   ('body', {'body_sha256': 'e' * 64}, 'CLAIMS_MISMATCH'), ('assistant', {'attested_by': 'Claude'}, 'named human')):
            with self.subTest(name):
                with self.assertRaisesRegex(ValueError, code):
                    self.custody(name=name, claims=self.claims(name=f'claims-{name}.json', **change))
        self.assertFalse((self.root / 'custody').exists())
        # The Quarry contract itself refuses a supply moved to another route, version or URL.
        ctx = X.preflight(self.base, 'A1', SR.URL1)
        value = X.supply(ctx, S.sha(Path(claims).read_bytes()), json.loads(Path(claims).read_bytes()))
        registry = json.loads(ctx['registry_raw'])
        for name, supply, routes, message in (
                ('version', {**value, 'route_version': '2'}, registry, 'route/version|NATIVE_MISMATCH'),
                ('route', {**value, 'route_id': 'R1'}, registry, 'route locator|retained receipt, result or claims'),
                ('url', value, {**registry, 'routes': [{**registry['routes'][0], 'locator': SR.URL2}, registry['routes'][1]]}, 'route locator|NATIVE_MISMATCH')):
            with self.subTest(name):
                retained = dict(zip(K.RETAINED, (ctx['receipt_raw'], ctx['result_raw'], Path(claims).read_bytes())))
                with self.assertRaisesRegex(ValueError, message):
                    E.import_retrieved(self.put('r.json', routes)['path'], self.put('s.json', supply)['path'],
                                       self.put('o.bin', TEXT)['path'], self.root / f'direct-{name}', retained, source_base=self.base)

    def test_custody_output_is_create_only_and_one_package_per_receipt(self):
        self.retrieve()
        first = self.custody()
        with self.assertRaisesRegex(ValueError, 'OUTPUT_EXISTS'):
            self.custody()
        with self.assertRaisesRegex(ValueError, 'REUSED_CUSTODY'):
            self.custody(name='again')
        with self.assertRaisesRegex(ValueError, 'INCONSISTENT_DUPLICATE'):
            self.custody(name='other', claims=self.claims(name='claims-2.json', title='A different title'))
        self.assertFalse((self.root / 'custody' / 'again').exists() or (self.root / 'custody' / 'other').exists())
        receipt = X.preflight(self.base, 'A1', SR.URL1)['receipt_sha256']
        state = X.status(self.base, receipt)
        self.assertTrue(state['consistent'])
        self.assertEqual(state['custody_claim']['package'], first['package'])

    def test_source_changed_after_preflight_imports_nothing(self):
        self.retrieve()
        claims = self.claims()
        real = X.preflight
        calls = []
        def preflight(*args):
            ctx = real(*args)
            if not calls:  # Between the first preflight and the import, the retained body changes.
                body = self.attempt() / 'raw' / '002.body'
                body.write_bytes(body.read_bytes() + b'!')
            calls.append(1)
            return ctx
        with patch.object(X, 'preflight', side_effect=preflight), self.assertRaisesRegex(ValueError, 'SOURCE_INCONSISTENT|SOURCE_CHANGED'):
            self.custody(claims=claims)
        self.assertFalse((self.root / 'custody' / 'pkg').exists())
        self.assertFalse(X.custody_root(self.base).exists())

    def test_existing_v001_supplies_imports_and_exports_are_unchanged(self):
        result = QD.run(self.root / 'quarry-demo')
        self.assertEqual(result['order'][0], 'B_F1_ORDER')
        E.validate_export(self.root / 'quarry-demo' / 'handoff')
        supplied = json.loads((self.root / 'quarry-demo' / 'supply.json').read_bytes())
        self.assertEqual(K.supply(supplied), supplied)
        for name, change in (('V001 cannot claim system retrieval', {'fixture': 'SYSTEM_RETRIEVED'}),
                             ('V001 has no retrieval binding', {'system_retrieval': {}}),
                             ('V002 needs a binding', {'schema': 'QUARRY_SUPPLY_V002', 'fixture': 'SYSTEM_RETRIEVED'})):
            with self.subTest(name), self.assertRaises(ValueError):
                K.supply({**supplied, **change})

    # ---- PR #46 review reproductions -----------------------------------------------------------------------
    def forged_supply(self, body):
        """A self-consistent V002 supply whose receipt, result and claims hashes name no native record."""
        retrieval = {'source_component': 'SOURCE_RETRIEVAL_V001', 'attempt_id': 'FORGED', 'request_sha256': 'a' * 64,
                     'result_sha256': 'b' * 64, 'receipt_sha256': 'c' * 64, 'requested_url': SR.URL1, 'http_status': 200,
                     'termination': 'COMPLETE', 'transfer_coverage': 'COMPLETE', 'body_sha256': S.sha(body), 'body_bytes': len(body),
                     'started_at': '2026-10-26T12:00:00+00:00', 'finished_at': '2026-10-26T12:00:01+00:00',
                     'implementation_sha256': 'd' * 64, 'claims_sha256': 'e' * 64, 'publication_authenticity': 'UNKNOWN',
                     'dataset_completeness': 'UNKNOWN', 'scientific_meaning': 'NOT_ESTABLISHED'}
        return {'schema': K.SUPPLY_V002, 'route_id': 'R0', 'route_version': '1', 'fixture': 'SYSTEM_RETRIEVED',
                'data_classification': 'SYNTHETIC', 'title': 'Forged', 'source_identity_claim': 'doc-0', 'asset_claim': 'F1',
                'source_version_claim': 'x', 'retrieved_at_claim': retrieval['finished_at'],
                'retrieval_method_claim': K.RETRIEVAL_METHOD + retrieval['receipt_sha256'], 'historical_availability_claim': 'UNKNOWN',
                'expected_original_sha256': S.sha(body), 'coverage': 'COMPLETE_CLAIMED',
                'limitations': K.transfer_limitations(retrieval), 'missing_fields': [], 'system_retrieval': retrieval}

    def test_review_1_direct_quarry_import_cannot_claim_system_retrieved_custody(self):
        registry = self.put('forged-registry.json', json.loads(Path(self.registry['path']).read_bytes()))['path']
        supply = self.put('forged-supply.json', self.forged_supply(TEXT))['path']
        original = self.put('forged.txt', TEXT)['path']
        with self.assertRaisesRegex(ValueError, 'source custody'):
            E.import_file(registry, supply, original, self.root / 'forged-package')
        out = []
        with patch('builtins.print', side_effect=lambda text: out.append(text)):
            from src.research.quarry_v1 import __main__ as QCLI
            self.assertNotEqual(QCLI.main(['import-file', registry, supply, '--file', original, '--out', str(self.root / 'forged-cli')]), 0)
        self.assertFalse((self.root / 'forged-package').exists() or (self.root / 'forged-cli').exists())
        invented = {name: b'{}' for name in K.RETAINED}  # Made-up native records do not match the supply binding.
        with self.assertRaisesRegex(ValueError, 'retained native records differ'):
            E.import_retrieved(registry, supply, original, self.root / 'forged-direct', invented, source_base=self.base)
        self.assertFalse((self.root / 'forged-direct').exists())
        # A legitimate package keeps its retained native records and stays portable.
        self.retrieve()
        package = Path(self.custody()['package'])
        moved = self.root / 'moved-package'
        moved.mkdir()
        for p in package.iterdir():
            (moved / p.name).write_bytes(p.read_bytes())
        self.assertEqual(E.load(moved)['supply']['fixture'], 'SYSTEM_RETRIEVED')
        self.export(moved)
        E.validate_export(self.root / 'export')

    def test_review_2_custody_status_detects_marker_changes_and_incomplete_imports(self):
        self.retrieve()
        out = self.custody()
        marker = Path(out['custody_claim'])
        receipt = marker.stem
        self.assertEqual(X.status(self.base, receipt)['state'], 'CUSTODY_COMPLETE')
        original = marker.read_bytes()
        for field, value in (('attempt_id', 'A9'), ('receipt_sha256', 'f' * 64), ('url', SR.URL2), ('claims_sha256', 'e' * 64),
                             ('supply_sha256', 'd' * 64), ('package', str(self.root / 'elsewhere')), ('schema', 'OTHER')):
            with self.subTest(field):
                changed = json.loads(original)
                changed[field] = value
                marker.write_bytes(canonical(changed) + b'\n')
                state = X.status(self.base, receipt)
                self.assertEqual((state['state'], state['consistent']), ('INCONSISTENT', False))
        marker.write_bytes(original)
        self.assertEqual(X.status(self.base, receipt)['state'], 'CUSTODY_COMPLETE')
        # Interruption after the create-only claim: before, and during, package creation.
        for i, (target, state) in enumerate((('src.research.quarry_v1.io.new_directory', 'CLAIM_WITHOUT_PACKAGE'),
                                             ('src.research.quarry_v1.io.seal', 'PACKAGE_INCOMPLETE'))):
            with self.subTest(state):
                self.base = self.root / f'records-int-{i}'
                self.build()
                self.retrieve()
                claims = self.claims()
                with patch(target, side_effect=OSError('interrupted')), self.assertRaises(OSError):
                    self.custody(name=f'int-{i}', claims=claims)
                receipt = X.preflight(self.base, 'A1', SR.URL1)['receipt_sha256']
                report = X.status(self.base, receipt)
                self.assertEqual((report['state'], report['consistent']), (state, False))
                with self.assertRaisesRegex(ValueError, 'CUSTODY_INCOMPLETE'):  # Never retried or replaced.
                    self.custody(name=f'int-{i}-again', claims=claims)
                self.assertTrue((X.custody_root(self.base) / 'receipts' / f'{receipt}.json').exists())

    def test_review_3_exact_claims_record_survives_in_package_and_export(self):
        self.retrieve()
        claims = self.claims()
        out = self.custody(claims=claims)
        retained = Path(out['package']) / 'retrieval-claims.json'
        self.assertEqual(retained.read_bytes(), Path(claims).read_bytes())
        self.export(out['package'])
        self.assertEqual((self.root / 'export' / 'source' / 'retrieval-claims.json').read_bytes(), Path(claims).read_bytes())
        E.validate_export(self.root / 'export')
        package = E.load(out['package'])
        self.assertEqual(package['supply']['system_retrieval']['claims_sha256'], S.sha(retained.read_bytes()))
        # Edited claims, even with a re-sealed manifest, no longer match the supply's binding.
        root = Path(out['package'])
        edited = json.loads(retained.read_bytes()); edited['asset_claim'] = 'F2'
        retained.write_bytes(canonical(edited))
        manifest = json.loads((root / 'manifest.json').read_bytes())
        manifest['files']['retrieval-claims.json'] = S.sha(retained.read_bytes())
        (root / 'manifest.json').write_bytes(canonical(manifest))
        with self.assertRaisesRegex(ValueError, 'retained native records differ'):
            E.load(root)

    # ---- PR #46 final trust boundary ----------------------------------------------------------------------
    def invented(self, body=TEXT, attempt='INVENTED', **claims_changes):
        """A fully self-consistent native-looking record set with correct hashes, but no native attempt."""
        receipt = {'schema': 'SOURCE_RETRIEVAL_RECEIPT_V001', 'attempt_id': attempt, 'request_index': 2, 'role': 'TARGET',
                   'requested_url': SR.URL1, 'host': SR.HOST, 'http_status': 200, 'termination': 'COMPLETE', 'coverage': 'COMPLETE',
                   'body_path': 'raw/002.body', 'body_sha256': S.sha(body), 'bytes_received': len(body),
                   'started_at': '2026-10-26T12:00:00+00:00', 'finished_at': '2026-10-26T12:00:01+00:00', 'implementation_sha256': 'd' * 64}
        receipt_raw = canonical(receipt) + b'\n'
        handoff = {'receipt_sha256': S.sha(receipt_raw), 'requested_url': SR.URL1, 'quarry_route_id': 'R0', 'body_path': 'raw/002.body',
                   'body_sha256': S.sha(body), 'bytes': len(body), 'coverage': 'COMPLETE'}
        result_raw = canonical({'schema': 'SOURCE_ACTIVITY_RESULT_V001', 'attempt_id': attempt, 'request_sha256': 'a' * 64, 'status': 'COMPLETE',
                                'interrupted': False, 'receipts': [S.sha(receipt_raw)], 'custody_handoff': [handoff]}) + b'\n'
        claims = {'schema': X.CLAIMS, 'attested_by': SR.OWNER, 'attested_at': '2026-10-26T13:00:00+00:00', 'attempt_id': attempt,
                  'receipt_sha256': S.sha(receipt_raw), 'body_sha256': S.sha(body), 'title': 'Invented', 'source_identity_claim': 'doc-0',
                  'asset_claim': 'F1', 'source_version_claim': 'x', 'historical_availability_claim': 'UNKNOWN', 'data_classification': 'SYNTHETIC',
                  'limitations': [], 'missing_fields': [], 'statement': X.STATEMENT, **claims_changes}
        claims_raw = canonical(claims) + b'\n'
        retrieval = {'source_component': 'SOURCE_RETRIEVAL_V001', 'attempt_id': attempt, 'request_sha256': 'a' * 64,
                     'result_sha256': S.sha(result_raw), 'receipt_sha256': S.sha(receipt_raw), 'requested_url': SR.URL1, 'http_status': 200,
                     'termination': 'COMPLETE', 'transfer_coverage': 'COMPLETE', 'body_sha256': S.sha(body), 'body_bytes': len(body),
                     'started_at': receipt['started_at'], 'finished_at': receipt['finished_at'], 'implementation_sha256': 'd' * 64,
                     'claims_sha256': S.sha(claims_raw), 'publication_authenticity': 'UNKNOWN', 'dataset_completeness': 'UNKNOWN',
                     'scientific_meaning': 'NOT_ESTABLISHED'}
        supply = {'schema': K.SUPPLY_V002, 'route_id': 'R0', 'route_version': '1', 'fixture': 'SYSTEM_RETRIEVED',
                  'data_classification': claims['data_classification'], 'title': claims['title'], 'source_identity_claim': 'doc-0',
                  'asset_claim': 'F1', 'source_version_claim': 'x', 'retrieved_at_claim': receipt['finished_at'],
                  'retrieval_method_claim': K.RETRIEVAL_METHOD + S.sha(receipt_raw), 'historical_availability_claim': 'UNKNOWN',
                  'expected_original_sha256': S.sha(body), 'coverage': 'COMPLETE_CLAIMED', 'limitations': K.transfer_limitations(retrieval),
                  'missing_fields': [], 'system_retrieval': retrieval}
        paths = (self.put('inv-registry.json', json.loads(Path(self.registry['path']).read_bytes()))['path'],
                 self.put('inv-supply.json', supply)['path'], self.put('inv-original.txt', body)['path'])
        return paths, dict(zip(K.RETAINED, (receipt_raw, result_raw, claims_raw)))

    def test_final_invented_native_records_cannot_create_v002_custody(self):
        (registry, supply, original), retained = self.invented()
        K.retained(json.loads(Path(supply).read_bytes()), retained, S.sha(TEXT), len(TEXT))  # Portable consistency alone passes.
        with self.assertRaisesRegex(ValueError, 'SOURCE_INCONSISTENT|SOURCE_NOT|unknown attempt'):
            E.import_retrieved(registry, supply, original, self.root / 'invented', retained, source_base=self.base)
        self.assertFalse((self.root / 'invented').exists())
        with self.assertRaises(TypeError):  # Creation cannot be requested without naming the native records to verify.
            E.import_retrieved(registry, supply, original, self.root / 'invented', retained)
        # A real attempt with the same id: the invented records still differ from its native bytes.
        self.retrieve()
        (registry, supply, original), retained = self.invented(attempt='A1')
        with self.assertRaisesRegex(ValueError, 'NATIVE_MISMATCH'):
            E.import_retrieved(registry, supply, original, self.root / 'invented-a1', retained, source_base=self.base)
        self.assertFalse((self.root / 'invented-a1').exists())

    def test_final_portable_claims_are_schema_and_field_validated(self):
        for name, change in (('assistant attester', {'attested_by': 'Claude (assistant)'}), ('placeholder attester', {'attested_by': 'UNKNOWN'}),
                             ('no timezone', {'attested_at': '2026-10-26T13:00:00'}), ('wrong statement', {'statement': 'verified facts'}),
                             ('extra field', {'verified': True})):
            with self.subTest(name):
                (_, supply, _), retained = self.invented(**change)
                with self.assertRaisesRegex(ValueError, 'claims'):
                    K.retained(json.loads(Path(supply).read_bytes()), retained, S.sha(TEXT), len(TEXT))

    def test_final_imported_registry_must_be_the_native_approved_registry(self):
        self.retrieve()
        claims = self.claims()
        ctx = X.preflight(self.base, 'A1', SR.URL1)
        ctx['claims_raw'] = Path(claims).read_bytes()
        value = X.supply(ctx, S.sha(ctx['claims_raw']), json.loads(ctx['claims_raw']))
        supply, original = self.put('reg-supply.json', value)['path'], self.put('reg-original.txt', TEXT)['path']
        retained = dict(zip(K.RETAINED, (ctx['receipt_raw'], ctx['result_raw'], ctx['claims_raw'])))
        approved = json.loads(ctx['registry_raw'])
        stop = {'id': 'S-ADDED', 'scope': 'host', 'reason': 'fictional', 'citation': 'fictional', 'citation_sha256': 'UNKNOWN'}
        for name, change in (('restrictions', {'access_restrictions': []}), ('restrictions added', {'access_restrictions': ['owner-only']}),
                             ('stops', {'stops': [stop]}), ('expected fields', {'expected_fields': ['something else']})):
            with self.subTest(name):
                registry = json.loads(ctx['registry_raw'])
                registry['routes'][0].update(change)  # Same route id, version and exact URL.
                self.assertEqual((registry['routes'][0]['id'], registry['routes'][0]['version'], registry['routes'][0]['locator']),
                                 (approved['routes'][0]['id'], approved['routes'][0]['version'], SR.URL1))
                if registry == approved:
                    registry['routes'][0]['question'] = 'changed question'
                path = self.put(f'reg-{len(name)}.json', registry)['path']
                with self.assertRaisesRegex(ValueError, 'NATIVE_MISMATCH'):
                    E.import_retrieved(path, supply, original, self.root / f'reg-{len(name)}', retained, source_base=self.base)
                self.assertFalse((self.root / f'reg-{len(name)}').exists())
        exact = self.put('reg-exact.json', ctx['registry_raw'])['path']  # The exact approved bytes are accepted.
        E.import_retrieved(exact, supply, original, self.root / 'reg-exact', retained, source_base=self.base)
        self.assertEqual(E.load(self.root / 'reg-exact')['route'], approved['routes'][0])

    def test_cli_reports_preflight_and_refusals_without_network(self):
        self.retrieve()
        out = []
        with patch('builtins.print', side_effect=lambda text: out.append(text)):
            self.assertEqual(CLI.main(['--base', str(self.base), 'preflight', 'A1', SR.URL1]), 0)
            self.assertEqual(CLI.main(['--base', str(self.base), 'preflight', 'A1', SR.ROBOTS]), 1)
        self.assertTrue(json.loads(out[0])['eligible'])
        self.assertIn('NOT_CUSTODY_ELIGIBLE', json.loads(out[1])['message'])
        self.assertEqual(len(self.fake.opened), 3)


if __name__ == '__main__':
    unittest.main()
