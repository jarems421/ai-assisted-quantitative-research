"""Offline packaging from synthetic receipts in a temporary EXP999 workspace."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.research.support_case import build


class SupportCaseTests(unittest.TestCase):
    def fixture(self, root, *, heading='page 1/1, 1 matching'):
        base = 'data/raw/EXP004/streams_v002/'
        # Directory names match archived parser contract; all content is synthetic.
        request = {'tool': 'backtest_portfolio', 'portfolio': {'userId': 'PRIVATE_SENTINEL', 'strategies': [{'action': {'universe': {
            'assets': [{'symbol': 'SYNTHETIC_OLD'}, {'symbol': 'SYNTHETIC_KEPT'}]}}}]}, 'args': {}}
        row = {'event': {'dynamicAudit': {'universeSize': 1, 'pipelineStages': [
            {'passedAssets': [['SYNTHETIC_KEPT', 1]]}]}}, 'userId': 'PRIVATE_SENTINEL', 'price': 999}
        points = {'request': {'rows': [{'ticker': 'SYNTHETIC_OLD', 'timestamp': '2015-01-02T02:00:00Z',
                                      'availableAt': '2015-01-02T02:00:00Z', 'value': 1, 'userId': 'PRIVATE_SENTINEL'}]}}
        page = {'response': {'content': [{'type': 'text', 'text':
                f'## Backtest Events ({heading})\n\n[2015-01-02 14:30:00] RebalanceSignal (raw)\n'+json.dumps(row)}]}}
        receipts = []
        for name, data in [('transport_execution_diagnostic/request.json', request),
                           ('transport_execution_diagnostic/events_00001.json', page),
                           ('transport_diagnostic/mcp_response.json', points)]:
            path = root/(base+name); path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
            receipts.append({'path': base+name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        audit = root/'experiments/EXP004/research/publication_runtime_audit.json'
        audit.parent.mkdir(parents=True)
        audit.write_text(json.dumps({'receipt_index': receipts, 'transport_diagnostic': {'run_id': 'synthetic'},
                                    'dataset_promotion_fixture': {}, 'uploads': {}}))

    def test_complete_population_failure_and_allowlist(self):
        with tempfile.TemporaryDirectory(prefix='EXP999-support-') as d:
            root = Path(d); self.fixture(root); result = build(root)
            self.assertEqual(result['certification'], 'FAIL_POPULATION_PRUNING')
            self.assertEqual(result['event_rows'], 1)
            self.assertNotIn('PRIVATE_SENTINEL', json.dumps(result))
            self.assertNotIn('price', json.dumps(result))
            self.assertFalse(result['execution_authorized'])
            self.assertEqual(build(root), result)

    def test_hash_tampering_and_incomplete_pages_fail(self):
        with tempfile.TemporaryDirectory(prefix='EXP999-support-') as d:
            root = Path(d); self.fixture(root)
            (root/'data/raw/EXP004/streams_v002/transport_execution_diagnostic/request.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'hash differs'): build(root)
        with tempfile.TemporaryDirectory(prefix='EXP999-support-') as d:
            root = Path(d); self.fixture(root, heading='page 1/2, 2 matching')
            with self.assertRaisesRegex(ValueError, 'incomplete'): build(root)
