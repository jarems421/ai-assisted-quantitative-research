"""Boundary and contract checks against the real public catalogue, never fixtures or live ledgers."""
import copy
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import export_workspace as E


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = E.make_export()

    def test_actual_repository_records_and_operator_outputs(self):
        d = self.data
        self.assertEqual({i['family'] for i in d['investigations']}, {'F01', 'F03', 'F09', 'F19', 'SH09', 'EF03', 'EF06'})
        self.assertEqual(len(d['nodes']), 99)
        self.assertEqual(len(d['edges']), 121)
        self.assertEqual(sum(len(i['findings']) for i in d['investigations']), 39)
        self.assertTrue(all(x['operator'] == 'same-gap' for x in d['same_gap'].values()))
        for n, sizes in d['neighbourhoods'].items():
            for bound, result in sizes.items():
                self.assertLessEqual(len(result['results'][0]['nodes']), int(bound))
                self.assertIn(n, result['results'][0]['nodes'])

    def test_no_discovery_or_private_or_network_reads(self):
        from src.research.discovery.ledger import Ledger
        original = Path.open
        opened = []
        def checked_open(path, *args, **kwargs):
            resolved = path.resolve()
            if resolved.is_relative_to(E.ROOT):
                relative = resolved.relative_to(E.ROOT).as_posix()
                self.assertIn(relative, E.ALLOWED, f'unapproved read: {relative}')
                self.assertNotIn('w', args[0] if args else kwargs.get('mode', 'r'))
                opened.append(relative)
            return original(path, *args, **kwargs)
        with patch('src.research.graph.project.discover_ledgers', side_effect=AssertionError('ledger discovery forbidden')), \
             patch.object(Ledger, 'load', side_effect=AssertionError('ledger read forbidden')), \
             patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), \
             patch.object(Path, 'open', checked_open):
            self.assertEqual(E.make_export(), self.data)
        self.assertEqual(set(opened), E.ALLOWED)

    def test_inputs_are_byte_identical_and_export_is_deterministic(self):
        before = {p: E.file_hash(E.safe_read(p)) for p in E.ALLOWED}
        first, second = E.make_export(), E.make_export()
        self.assertEqual(first, second)
        self.assertEqual(before, {p: E.file_hash(E.safe_read(p)) for p in E.ALLOWED})
        self.assertEqual(first['input_hashes'], before)

    def test_scopes_and_unknowns_are_honest(self):
        d = self.data
        self.assertEqual(d['campaigns'], [])
        self.assertIsNone(d['pilot'])
        self.assertNotIn('observation', {n['kind'] for n in d['nodes'].values()})
        self.assertNotIn('relationship', {n['kind'] for n in d['nodes'].values()})
        self.assertTrue(all(n['fixture'] in (None, 'HISTORICAL_MEMORY') for n in d['nodes'].values()))
        f19 = next(i for i in d['investigations'] if i['family'] == 'F19')
        self.assertEqual(f19['verdict']['status_class'], 'HOLD')
        self.assertTrue(any(c['financial_basis'] == 'NOT_ESTABLISHED'
                            for inv in d['investigations'] for c in inv['claims']))

    def test_claim_versions_and_partial_retrievals_are_preserved(self):
        ef06 = next(i for i in self.data['investigations'] if i['family'] == 'EF06')
        self.assertEqual([c['version'] for c in ef06['claims']], [1, 2])
        self.assertIsNotNone(ef06['claims'][1]['reformulates'])
        self.assertFalse(ef06['claims'][1]['counts_as_original'])
        for family in ('F19', 'F03'):
            inv = next(i for i in self.data['investigations'] if i['family'] == family)
            prefix = [f for f in inv['findings'] if f['kind'] == 'ACQUISITION_LIMIT']
            self.assertTrue(prefix)
            self.assertTrue(all(f['requirement'] is None for f in prefix))

    def test_citations_are_exact_and_hashes_match(self):
        for inv in self.data['investigations']:
            self.assertEqual(inv['citation_status'], 'CURRENT')
            for f in inv['findings']:
                document = self.data['documents'][f['citation']['path']]
                self.assertIn(f['citation']['quote'], document['text'])
                self.assertEqual(document['sha256'], document['expected_sha256'])
        for report in self.data['explanations'].values():
            for path in report['results']:
                self.assertFalse(path['exposure_certified'])
                self.assertTrue(path['connectivity_only'])
                self.assertIn('first_unsupported_leap', path)

    def test_unsafe_and_private_paths_rejected_before_open(self):
        for path in ('../.env', '.env', 'data/raw/test.json', 'docs/../.env', 'C:/secret', '//server/file',
                     'docs/strategy/discovery/arm-G.jsonl', 'snapshots/blind-key.json', E.CATALOGUE + ':secret'):
            with self.subTest(path=path), patch.object(Path, 'read_bytes', side_effect=AssertionError('must not read')):
                with self.assertRaises(ValueError): E.safe_read(path)

    def test_untracked_and_linked_inputs_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / E.CATALOGUE
            path.parent.mkdir(parents=True)
            path.write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError): E.safe_read(E.CATALOGUE, root=root)
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaises(ValueError): E.safe_read(E.CATALOGUE)

    def test_catalogue_path_changes_fail_closed(self):
        raw = {p: E.safe_read(p) for p in E.ALLOWED}
        cat = json.loads(raw[E.CATALOGUE])
        cat['investigations'][0]['findings'][0]['citation']['path'] = 'data/raw/private.md'
        raw[E.CATALOGUE] = json.dumps(cat).encode()
        with patch.object(E, 'safe_read', side_effect=lambda path: raw[path]):
            with self.assertRaisesRegex(ValueError, 'Unapproved citation'): E.make_export()

    def test_output_links_refused_before_export(self):
        with tempfile.TemporaryDirectory() as td, patch.object(E, 'APP', Path(td)), \
             patch.object(Path, 'is_symlink', return_value=True), \
             patch.object(E, 'make_export', side_effect=AssertionError('must not export')):
            with self.assertRaises(ValueError): E.write_export()

    def test_atomic_output_does_not_write_through_a_hardlink(self):
        with tempfile.TemporaryDirectory() as td, patch.object(E, 'APP', Path(td)), \
             patch.object(E, 'make_export', return_value={'investigations': [], 'nodes': {}}):
            root = Path(td)
            sentinel = root / 'untouched.txt'
            sentinel.write_bytes(b'original bytes')
            (root / 'public').mkdir()
            os.link(sentinel, root / 'public/workspace.json')
            E.write_export()
            self.assertEqual(sentinel.read_bytes(), b'original bytes')
            self.assertEqual(json.loads((root / 'public/workspace.json').read_text()), {'investigations': [], 'nodes': {}})


if __name__ == '__main__': unittest.main()
