import unittest
from src.research.sec_pilot.phase3a import InlineFacts, reconcile_inline


class InlineTests(unittest.TestCase):
    def fixture(self):
        return {'contributors': [{'concept': 'Revenue', 'namespace': 'https://example.invalid/EXP999', 'context_ref': 'annual',
                                  'unit_ref': 'usd', 'exact_value': '123000000'}], 'status': 'SELECTED_PENDING_PRIMARY_RECONCILIATION'}

    def parse(self, value='123', scale='6', context='annual', nested=False):
        html = '<html xmlns:s="https://example.invalid/EXP999"><ix:nonFraction name="s:Revenue" contextRef="'+context+'" unitRef="usd" scale="'+scale+'">'
        if nested: html += '<ix:nonFraction name="s:Other" contextRef="annual" unitRef="usd">5</ix:nonFraction>'
        html += value+'</ix:nonFraction></html>'
        p = InlineFacts(); p.feed(html); return p

    def test_explicit_scale_original_position_and_determinism(self):
        result = reconcile_inline(self.fixture(), self.parse())
        self.assertEqual(result['status'], 'CERTIFIED_FOR_SCOPED_FACTS')
        self.assertEqual(result['primary_locators'][0]['scale'], '6')
        self.assertEqual(reconcile_inline(self.fixture(), self.parse()), result)

    def test_wrong_context_wrong_scale_and_nested_rendering_not_certified(self):
        for parsed in (self.parse(scale='3'), self.parse(context='segment'), self.parse(nested=True)):
            self.assertEqual(reconcile_inline(self.fixture(), parsed)['status'], 'PARTIAL')
