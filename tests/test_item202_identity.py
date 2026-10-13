import unittest
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
