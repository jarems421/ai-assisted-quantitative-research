import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import json
from src.research.item202_identity import Transport
from src.research.item202_identity import source_state, allowed_pool, coverage, cover_observations
from src.research.item202_population import resolve_class, certification_query

class IdentityTests(unittest.TestCase):
    def test_unknown_excluded_symmetrically(self):
        for status in ('UNKNOWN','SOURCE_REMOVED_OR_UNAVAILABLE'):
            r={'form':'8-K','event_state':status}
            self.assertEqual(source_state(r),'UNKNOWN_ITEM_STATUS')
            self.assertFalse(allowed_pool(r,'event'));self.assertFalse(allowed_pool(r,'control'))

    def test_only_confirmed_events_and_controls(self):
        self.assertTrue(allowed_pool({'form':'8-K','event_state':'ORIGINAL_SIGNAL_EVENT'},'event'))
        self.assertFalse(allowed_pool({'form':'8-K','event_state':'ORIGINAL_SIGNAL_EVENT'},'control'))
        self.assertTrue(allowed_pool({'form':'8-K','event_state':'NON_ITEM202'},'control'))

    def test_amendment_never_signal_or_control(self):
        r={'form':'8-K/A','event_state':'ORIGINAL_SIGNAL_EVENT'}
        self.assertFalse(allowed_pool(r,'event'));self.assertFalse(allowed_pool(r,'control'))

    def test_cover_point_is_not_a_span(self):
        body=b'<ix:nonNumeric name="dei:TradingSymbol">OLD</ix:nonNumeric>'
        obs=cover_observations(body)
        self.assertEqual(obs['TradingSymbol'][0]['value'],'OLD')
        self.assertEqual(resolve_class([{'historical_ticker':'OLD'}],'2015-01-01')['status'],'UNRESOLVED')

    def test_coverage_year_denominators_and_ambiguity(self):
        rows=[{'filing_date':'2015-01-01','status':'FULLY_RESOLVED'},
              {'filing_date':'2015-02-01','status':'AMBIGUOUS'},
              {'filing_date':'2016-01-01','status':'UNRESOLVED'}]
        c=coverage(rows)
        self.assertEqual(c['by_year']['2015']['coverage_percent'],50)
        self.assertEqual(c['by_year']['2016']['coverage_percent'],0)
        self.assertEqual(c['ambiguous'],1); self.assertEqual(c['unresolved'],1)

    def test_confirmation_and_post_event_unreachable(self):
        with self.assertRaises(ValueError):certification_query('2015-01-01T00:00:00+00:00','2015-01-03T00:00:00+00:00','2015-01-02T00:00:00+00:00')
        with self.assertRaises(ValueError):certification_query('2021-01-01T00:00:00+00:00','2021-01-02T00:00:00+00:00','2021-01-03T00:00:00+00:00')

    def test_identity_transport_denial_is_immutable_no_retry(self):
        url='https://www.sec.gov/Archives/edgar/data/1/fixture.htm'
        with tempfile.TemporaryDirectory() as tmp,patch('src.research.item202_identity.RAW',Path(tmp)),patch('src.research.item202_identity.identity',return_value='local test identity'),patch('src.research.item202_identity.SourceHTTP._transport',return_value=(403,{},b'denied',url)) as transport:
            http=Transport('SEC',{url})
            with self.assertRaises(ValueError):http.fetch(url)
            with self.assertRaises(ValueError):http.fetch(url)
            self.assertEqual(transport.call_count,1)
            receipt=json.loads(next((Path(tmp)/'SEC/receipts').glob('*.json')).read_bytes())
            self.assertEqual(receipt['status'],403)
            self.assertNotIn('local test identity',json.dumps(receipt))

    def test_provider_price_route_refused_before_transport(self):
        url='https://api.tiingo.com/tiingo/daily/OLD/prices'
        with tempfile.TemporaryDirectory() as tmp,patch('src.research.item202_identity.RAW',Path(tmp)),patch('src.research.item202_identity.SourceHTTP._transport') as transport:
            http=Transport('Tiingo',{url})
            with self.assertRaises(ValueError):http.fetch(url)
            transport.assert_not_called()

    def test_historical_receipt_preserved_with_separate_correction(self):
        import hashlib
        from src.research.item202_identity import DOCS
        c=json.loads((DOCS/'exp006_population_duplicate_correction_v001.json').read_bytes())
        old=(DOCS/'exp006_historical_population_reconciliation.json').read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(),c['prior_receipt_sha256'])
        self.assertEqual((c['daily_equivalent_extra_rows'],c['quarterly_equivalent_extra_rows']),(111,0))
