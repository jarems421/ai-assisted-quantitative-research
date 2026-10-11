import json
import tempfile
import unittest
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from src.research.sec_pilot.reconcile import reconcile
from src.research.sec_pilot.__main__ import documents
from src.research.sec_pilot.acquisition import Boundary
from test_sec_pilot_acquisition import FIXTURE


class ReconciliationTests(unittest.TestCase):
    def test_exact_cross_store_and_count_preserving_substitution(self):
        snapshot = {'facts': [{'concept': 'EXP999', 'exact_value': '0'}], 'text_sections': [],
                    'security_bindings': [], 'asof_views': []}
        with tempfile.TemporaryDirectory(prefix='EXP999-reconcile-') as d:
            result = reconcile(snapshot, {'sources': {}}, d)
            self.assertEqual(result['facts']['rows'], 1)
            self.assertEqual(reconcile(snapshot, {'sources': {}}, d), result)
            pq.write_table(pa.table({'key': ['substitution'], 'payload': ['{}']}), Path(d)/'facts.parquet')
            with self.assertRaisesRegex(ValueError, 'exact key/value'): reconcile(snapshot, {'sources': {}}, d)

    def test_index_selects_only_primary_and_instance_and_rejects_escape(self):
        def html(prefix=''):
            return ('<table><tr><td>1</td><td>annual</td><td><a href="'+prefix+'synthetic.htm">file</a></td><td>10-K</td></tr>'
                    '<tr><td>2</td><td>instance</td><td><a href="synthetic.xml">file</a></td><td>XML</td></tr></table>').encode()
        self.assertEqual(set(documents(html(), Boundary(FIXTURE))), {'primary', 'instance'})
        with self.assertRaises(ValueError): documents(html('https://evil.invalid/'), Boundary(FIXTURE))
