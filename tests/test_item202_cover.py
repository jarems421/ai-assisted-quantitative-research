import unittest
from datetime import date,timedelta
from src.research.item202_cover import (parse_cover,choose_class,class_kind,provider_bridge,path_certificate,event_scope,pool_eligible)
from src.research.item202_cover import parse_cover_v2,parse_cover_v4,choose_class_v2

def document(rows):
    return ('<html><table><tr><td>Title of each class</td><td>Trading Symbol(s)</td><td>Name of each exchange on which registered</td></tr>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in r)+'</tr>' for r in rows)+'</table><p>Item 2.02 Results of Operations</p></html>').encode()

class CoverTests(unittest.TestCase):
    def test_no_outcomes_without_pushed_scientific_freeze(self):
        from src.research.item202_date_bound import freeze_before_performance
        with self.assertRaises(ValueError):
            freeze_before_performance({'status':'SCIENTIFICALLY_READY_FOR_FREEZE'},freeze_commit_pushed=False,stage='development')
        with self.assertRaises(ValueError):
            freeze_before_performance({'status':'ABANDON_EXP006_SOURCE_FEASIBILITY'},freeze_commit_pushed=True,stage='development')

    def test_header_synonyms_and_explicit_prose(self):
        b=document([['Common Stock','ABC','NYSE']]).replace(b'Title of each class',b'Title of Class')
        self.assertEqual(parse_cover_v4(b)['rows'][0]['trading_symbol'],'ABC')
        prose=b'<p>Common Stock, Par Value $0.01 Per Share; Common stock traded on the New York Stock Exchange; trading symbol ABC.</p><p>Item 2.02</p>'
        self.assertEqual(parse_cover_v4(prose)['rows'][0]['trading_symbol'],'ABC')
    def test_labels_below_values_and_quoted_symbol(self):
        b=document([['Common Stock','"ABC"','NYSE']])
        self.assertEqual(parse_cover_v2(b)['rows'][0]['trading_symbol'],'ABC')
        header='<tr><td>Title of each class</td><td>Trading Symbol(s)</td><td>Name of each exchange on which registered</td></tr>'
        data='<tr><td>Common Stock</td><td>ABC</td><td>NYSE</td></tr>'
        self.assertEqual(parse_cover_v2(('<table>'+data+header+'</table><p>Item 2.02</p>').encode())['rows'][0]['trading_symbol'],'ABC')

    def test_standalone_common_is_a_source_class_title(self):
        p=parse_cover_v2(document([['Common','ABC','NYSE']]))
        self.assertEqual(choose_class_v2(p['rows'])['status'],'SINGLE_COMMON_CANDIDATE')
        self.assertEqual(choose_class(p['rows'])['status'],'NO_ELIGIBLE_COMMON_CLASS')
    def test_plain_html_without_inline(self):
        p=parse_cover(document([['Common Stock, $0.01 par value','OLD','New York Stock Exchange']]))
        self.assertEqual(p['rows'][0]['trading_symbol'],'OLD')
        self.assertFalse(p['inline_required']);self.assertTrue(p['rows'][0]['source_locator']['field_character_spans'])

    def test_whitespace_unicode_and_spacers(self):
        p=parse_cover(document([['Common\u00a0Stock','ABC.B','NYSE']]))
        self.assertEqual(p['rows'][0]['class_title'],'Common Stock')
        b=document([['Common Stock','OLD','NYSE']]).replace(b'</td><td>',b'</td><td>&nbsp;</td><td>')
        self.assertEqual(parse_cover(b)['rows'][0]['trading_symbol'],'OLD')

    def test_multi_security_and_different_exchanges_retained(self):
        p=parse_cover(document([['Common Stock','OLD','NYSE'],['Preferred Stock','PRF','Nasdaq']]))
        self.assertEqual(len(p['rows']),2);self.assertEqual(choose_class(p['rows'])['common_count'],1)

    def test_multiple_common_no_selection(self):
        p=parse_cover(document([['Class A Common Stock','AA','NYSE'],['Class B Common Stock','BB','NYSE']]))
        self.assertEqual(choose_class(p['rows'])['status'],'MULTIPLE_ELIGIBLE_CLASSES')
        self.assertIsNone(choose_class(p['rows'])['row'])

    def test_non_common_classes_excluded(self):
        for title in ('Preferred Stock','Common Stock Purchase Warrants','Depositary Shares','Units','Convertible Notes','Rights','ETF fund shares'):
            self.assertEqual(class_kind(title),'EXCLUDED_NON_COMMON')

    def test_formatted_text(self):
        p=parse_cover(b'Title of each class   Trading Symbol(s)   Name of exchange\nCommon Stock   ABC   Nasdaq\nItem 2.02\n')
        self.assertEqual(p['rows'][0]['source_locator']['representation'],'FORMATTED_TEXT')

    def test_body_table_cannot_repair_missing_cover(self):
        b=b'<p>Item 2.02</p>'+document([['Common Stock','ABC','NYSE']])
        self.assertEqual(parse_cover(b)['rows'],[])

    def test_current_figi_does_not_establish_historical_bridge(self):
        self.assertNotEqual(provider_bridge({},[{'figi':'id'}])['status'],'MAPPED')
        self.assertEqual(provider_bridge({},[{'figi':'a'},{'figi':'b'}])['status'],'AMBIGUOUS_PROVIDER_MAPPING')

    def sessions(self):return [(date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(21)]
    def observations(self):return [{'date':d,'open_available':True} for d in self.sessions()]

    def test_continuous_path_needs_no_full_history(self):
        c=path_certificate(self.sessions(),self.observations(),[],identity_continuity=True)
        self.assertEqual(c['status'],'PATH_CERTIFIED')

    def test_rename_split_dividend_evidence(self):
        for kind in ('rename','split','dividend','exchange_change'):
            a={'date':self.sessions()[2],'type':kind,'evidence_sha256':'a'*64}
            self.assertEqual(path_certificate(self.sessions(),self.observations(),[a],identity_continuity=True)['status'],'PATH_CERTIFIED')
            del a['evidence_sha256']
            self.assertEqual(path_certificate(self.sessions(),self.observations(),[a],identity_continuity=True)['status'],'ACTION_LINEAGE_UNRESOLVED')

    def test_terminal_path_not_dropped(self):
        for kind in ('merger','delisting','cancellation','conversion'):
            a={'date':self.sessions()[2],'type':kind}
            self.assertEqual(path_certificate(self.sessions(),self.observations(),[a],identity_continuity=True)['status'],'TERMINAL_PATH_UNRESOLVED')

    def test_lifecycle_after_exit_not_required(self):
        self.assertEqual(path_certificate(self.sessions(),self.observations(),[{'date':'2021-01-01','type':'merger'}],identity_continuity=True)['status'],'PATH_CERTIFIED')

    def test_missing_session_open_fails(self):
        self.assertEqual(path_certificate(self.sessions(),self.observations()[:-1],[],identity_continuity=True)['status'],'MISSING_SESSION_OR_OPEN')
        self.assertEqual(path_certificate(self.sessions(),self.observations(),[])['status'],'IDENTITY_CONTINUITY_UNRESOLVED')

    def test_inception_and_symmetric_control_identity(self):
        self.assertFalse(event_scope('2019-05-01'));self.assertTrue(event_scope('2019-05-02'))
        self.assertFalse(event_scope('2021-01-01'))
        r={'form':'8-K','filing_date':'2019-05-02','event_state':'NON_ITEM202'}
        self.assertFalse(pool_eligible(r,'control',identity_status='UNRESOLVED'))
        self.assertTrue(pool_eligible(r,'control',identity_status='FULLY_RESOLVED'))
        r['event_state']='UNKNOWN'
        for pool in ('event','control'):self.assertFalse(pool_eligible(r,pool,identity_status='FULLY_RESOLVED'))
