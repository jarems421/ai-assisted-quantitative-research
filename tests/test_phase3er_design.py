from datetime import date
import unittest
from src.research.phase3er.calendar import sessions,clock_probe
from src.research.phase3er.sources import validate_url,header_url


class RedesignBoundaryTests(unittest.TestCase):
    def test_calendar_extension_is_separate_and_elapsed_only(self):
        s=sessions(date(2025,1,1),date(2025,12,31))
        self.assertEqual(len(s),250);self.assertNotIn(date(2025,1,9),s)
        self.assertNotIn(date(2026,7,3),sessions(date(2026,1,1),date(2026,9,30)))
        with self.assertRaises(ValueError):sessions(date(2025,1,1),date(2026,12,31))
    def test_dst_rollover_contradiction_and_cutoff_are_unavailable(self):
        k={'scope':['2018-02-01','2026-09-30'],'evidence_sha256':'a'*64}
        winter=clock_probe('20200129211214','2020-01-29',**k)
        self.assertEqual(winter['status'],'INVARIANT');self.assertFalse(winter['policy_approved'])
        summer=clock_probe('20201029180625','2020-10-29',**k)
        self.assertEqual(summer['status'],'INVARIANT');self.assertEqual(summer['acceptance_certification'],'PARTIAL')
        self.assertEqual(clock_probe('20200501235959','2020-05-01',**k)['status'],'UNAVAILABLE_CLOCK_CALENDAR_OR_SCOPE')
        self.assertEqual(clock_probe('20200501235959','2020-05-04',**k)['status'],'INVARIANT')
        self.assertEqual(clock_probe('20260930190000','2026-09-30',**k)['status'],'BOUND_OUTSIDE_SCOPE')
        self.assertEqual(clock_probe('20201029180625','2020-10-29',contradictory_public_utc='2020-11-05T17:00:00+00:00',**k)['status'],'NON_INVARIANT')
    def test_source_route_rejects_prices_full_submissions_and_company_facts(self):
        validate_url('SEC',header_url('0000320193','0000320193-20-000096'))
        for url in ['https://api.tiingo.com/tiingo/daily/aapl/prices','https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json',
                    header_url('0000320193','0000320193-20-000096').replace('-index-headers.html','.txt')]:
            with self.assertRaises(ValueError):validate_url('SEC',url)
