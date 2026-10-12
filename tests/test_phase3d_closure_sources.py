import unittest
from src.research.phase3d.closure.text import LocatedText
from src.research.phase3d.closure.lifecycle import within_cutoff
from src.research.phase3d.closure.accounting import packet


class ClosureSourceTests(unittest.TestCase):
    def test_entity_span_preserves_original_encoded_length(self):
        html='<p>A&amp;B &#xA9;</p>'
        text=LocatedText(html)
        locator=text.hits('©',before=0,after=0)[0]
        self.assertEqual(html[locator['decoded_start']:locator['decoded_end']],'&#xA9;')

    def test_markup_split_heading_and_original_locator(self):
        html='<p>CONSOLIDATED <b>STATEMENTS</b> OF OPERATIONS</p><script>not evidence</script>'
        located=LocatedText(html)
        hits=located.hits(r'CONSOLIDATED\s+STATEMENTS\s+OF\s+OPERATIONS')
        self.assertEqual(len(hits),1); self.assertNotIn('not evidence',located.text)
        hit=hits[0]; self.assertIn('CONSOLIDATED',html[hit['decoded_start']:hit['decoded_end']])
        self.assertIn('STATEMENTS',html[hit['decoded_start']:hit['decoded_end']])
        hidden=LocatedText('<ix:header>acquisition contexts</ix:header><div style="display:none">hidden facts</div><p>Revenue note</p>')
        self.assertEqual(hidden.text,'Revenue note ')

    def test_lifecycle_cutoff_rejects_future_bodies_without_losing_cases(self):
        self.assertTrue(within_cutoff('0000000999-21-000001'))
        self.assertFalse(within_cutoff('0000000999-22-000001'))
        self.assertFalse(within_cutoff('0000000999-26-000001'))
        with self.assertRaises(ValueError): within_cutoff('bad-accession')

    def test_missing_sources_generate_unavailable_packet_not_review_receipt(self):
        filing={'accessionNumber':'0000000999-20-000001','issuer_cik':'0000000999','reportDate':'2020-12-31','sources':{}}
        result=packet(filing,None,None)
        self.assertEqual(result['reason'],'MISSING_STATEMENT_EVIDENCE')
        self.assertEqual(result['observations'],[])
        self.assertEqual(result['review_status'],'NEEDS_ADDITIONAL_EVIDENCE')
