import unittest
from datetime import date,timedelta
from src.research.congress_sprint import classify,resolution,eligible_open,consolidate,stage_guard,contributor_asof

class CongressSprintTests(unittest.TestCase):
    def test_purchase_sale_unknown_and_asset_missingness(self):
        self.assertEqual(classify({'action':'purchase','asset_type_code':'ST'})['status'],'COMMON_EQUITY_CANDIDATE')
        self.assertEqual(classify({'action':'sale','asset_type_code':'ST'})['status'],'EXCLUDED_NON_PURCHASE')
        self.assertEqual(classify({'action':'unmarked'})['status'],'UNKNOWN_TRANSACTION')
        self.assertEqual(classify({'action':'purchase'})['status'],'UNKNOWN_ASSET_CLASS')
        for code in ('OP','PS','ET','CS'):
            self.assertNotEqual(classify({'action':'purchase','asset_type_code':code})['status'],'COMMON_EQUITY_CANDIDATE')

    def test_printed_and_resolved_never_conflated(self):
        r=resolution({'printed_ticker':'OLD','resolved_ticker':'NEW','resolution_status':'resolved','resolution_reason':'source-derived'})
        self.assertEqual((r['printed_ticker'],r['resolved_ticker']),('OLD','NEW'));self.assertFalse(r['printed_equals_resolved'])
        self.assertEqual(resolution({'printed_ticker':'OLD','resolution_status':'unresolved'})['status'],'UNRESOLVED_SECURITY')

    def test_second_later_open_after_modeled_eod_weekend_holiday_dst(self):
        sessions=[date(2020,3,6),date(2020,3,9),date(2020,3,10),date(2020,3,11)]
        e={'first_available_at':'2020-03-07T04:59:59.999Z','available_at':'2020-03-07T04:59:59.999Z'}
        r=eligible_open(e,sessions)
        self.assertEqual(r['entry_utc'],'2020-03-10T13:30:00+00:00');self.assertEqual(r['exact_public_availability'],'UNKNOWN')
        e['available_at']='2020-03-10T03:59:59.999Z'
        self.assertEqual(eligible_open(e,sessions)['entry_utc'],'2020-03-11T13:30:00+00:00')

    def test_future_version_supersession_no_old_entry(self):
        e={'first_available_at':'2020-03-07T04:59:59.999Z','available_at':'2020-03-07T04:59:59.999Z','superseded_at':'2020-03-10T00:00:00Z'}
        self.assertEqual(eligible_open(e,[date(2020,3,6),date(2020,3,9),date(2020,3,10)])['status'],'SUPERSEDED_BEFORE_ENTRY')

    def test_same_security_entry_dedup_later_date_retained(self):
        a=dict(stable_security_id='id',entry_date='2020-03-10',event_id='a',version=1,member_id='m')
        b=dict(a,event_id='b',member_id='n');c=dict(a,event_id='c',entry_date='2020-03-11')
        groups=consolidate([a,b,c]);self.assertEqual(len(groups),2);self.assertEqual(groups[0]['disclosures'],2)

    def test_future_contributor_is_descriptive_only_and_filtered(self):
        e={'first_available_at':'2020-01-01T00:00:00Z','available_at':'2020-01-01T00:00:00Z','chamber':'house','contributor_row_ids':'["D:0","L:0"]'}
        t=[dict(chamber='house',doc_id='D',row_index=0,available_at='2020-01-01T00:00:00Z'),dict(chamber='house',doc_id='L',row_index=0,available_at='2020-02-01T00:00:00Z')]
        r=contributor_asof(e,t);self.assertEqual(r['asof_contributors'],['D:0']);self.assertEqual(r['future_contributors_not_used'],['L:0'])

    def test_confirmation_and_unfrozen_outcomes_denied(self):
        dev=['2014-01-01','2021-12-31'];held=['2022-01-01','2025-12-31']
        with self.assertRaises(ValueError):stage_guard('2022-01-01',dev,held)
        with self.assertRaises(ValueError):stage_guard('2020-01-01',dev,held,outcome=True)
        self.assertTrue(stage_guard('2020-01-01',dev,held))
