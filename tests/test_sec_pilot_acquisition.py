import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from src.research.sec_pilot.acquisition import Archive, Boundary, Acquire

FIXTURE = {'accession': '0000000999-20-000001', 'index_url': 'https://www.sec.gov/Archives/edgar/data/999/000000099920000001/0000000999-20-000001-index.htm'}


class ArchiveTests(unittest.TestCase):
    def test_concurrent_idempotence_and_changed_versions(self):
        with tempfile.TemporaryDirectory(prefix='EXP999-sec-') as d:
            a = Archive(d)
            with ThreadPoolExecutor(max_workers=4) as pool:
                rows = list(pool.map(lambda _: a.body(FIXTURE['accession'], b'original\r\nbytes'), range(8)))
            self.assertTrue(all(r == rows[0] for r in rows))
            other = a.body(FIXTURE['accession'], b'changed')
            self.assertNotEqual(rows[0]['sha256'], other['sha256'])
            self.assertEqual(a.read(rows[0]), b'original\r\nbytes')
            Path(d, rows[0]['path']).write_bytes(b'tampered')
            with self.assertRaises(ValueError): a.read(rows[0])

    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): Archive(d).body('../escape', b'bad')
            with self.assertRaises(ValueError): Archive(d).read({'path': '../escape'})


class TransportTests(unittest.TestCase):
    def test_exact_allowlist_before_transport_and_redirects(self):
        b = Boundary(FIXTURE); calls = []
        with tempfile.TemporaryDirectory() as d:
            def transport(url, _):
                calls.append(url); return 302, {'Location': 'https://data.sec.gov/submissions/CIK999.json'}, b'error'
            a = Acquire(b, Archive(d), transport=transport, sleep=lambda _: None)
            for url in ('https://data.sec.gov/submissions/CIK999.json', b.base+'unapproved.xml', b.base+'%2e%2e/x', FIXTURE['index_url']+'?query=x'):
                with self.assertRaises(ValueError): a.get(url)
            self.assertEqual(calls, [])
            with self.assertRaises(ValueError): a.get(FIXTURE['index_url'])
            self.assertEqual(len(calls), 1)

    def test_bounded_restriction_receipts_and_redaction(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []; sleeps = []
            def transport(url, identity):
                calls.append(url); return 403, {'Content-Type': 'text/html'}, b'blocked'
            a = Acquire(Boundary(FIXTURE), Archive(d), transport=transport,
                        request_identity='PRIVATE_SENTINEL', sleep=sleeps.append, clock=lambda: 0)
            with self.assertRaisesRegex(ValueError, 'Persistent'): a.get(FIXTURE['index_url'])
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(list(Path(d).rglob('attempts/*.json'))), 3)
            self.assertFalse(any('PRIVATE_SENTINEL' in p.read_text() for p in Path(d).rglob('*.json')))
            self.assertIn(.5, sleeps)

    def test_short_body_and_interrupted_requests_never_succeed(self):
        for transport in (lambda *_: (200, {'Content-Length': '10'}, b'short'),
                          lambda *_: (_ for _ in ()).throw(KeyboardInterrupt())):
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises((ValueError, KeyboardInterrupt)):
                    Acquire(Boundary(FIXTURE), Archive(d), transport=transport).get(FIXTURE['index_url'])
                self.assertEqual(len(list(Path(d).rglob('errors/*.json'))), 1)
