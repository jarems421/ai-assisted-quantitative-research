import copy
from pathlib import Path
import tempfile
import unittest
from src.research.fda_pilot import contract,validate,FrameHTTP,gate2_authority,outcome_gate,missing_record,retain_identity,scope_findings
from src.research.phase3c.sources import put


class FDAFrameTests(unittest.TestCase):
    def test_freeze_filters_and_fixed_conditional_months(self):
        m=contract();validate(m);self.assertEqual(len(m['conditional_gate2_slots']),12)
        for key in ('approval','issuer','current_public','therapeutic_area','price'):
            bad=copy.deepcopy(m);bad['filters'][key]=True
            with self.assertRaises(ValueError):validate(bad)
        for key,value in [('request_ceiling',11),('total_pilot_ceiling',61),('month_substitution',True),('performance_authorized',True)]:
            bad=copy.deepcopy(m);bad[key]=value
            with self.assertRaises(ValueError):validate(bad)

    def test_gate1_and_event_freeze_precede_gate2(self):
        passing={'gate1':'PASS','outcome_independent_frame':True,'negative_unresolved_coverage':True,'review_receipt_sha256':'a'*64}
        self.assertEqual(gate2_authority(passing,total_starts=10,event_manifest_frozen=True),'CONDITIONAL_SOURCE_ONLY_NO_PERFORMANCE')
        for field in ('gate1','outcome_independent_frame','negative_unresolved_coverage','review_receipt_sha256'):
            bad=copy.deepcopy(passing);bad.pop(field)
            with self.assertRaises(ValueError):gate2_authority(bad,total_starts=10,event_manifest_frozen=True)
        with self.assertRaises(ValueError):gate2_authority(passing,total_starts=60,event_manifest_frozen=True)
        with self.assertRaises(ValueError):gate2_authority(passing,total_starts=10,event_manifest_frozen=False)

    def test_gate1_request_ceiling_including_retry_reservations(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(10):put(Path(tmp)/'reservations'/f'{i}.json',{'request_started_at_utc':'2000-01-01T00:00:00+00:00'})
            http=FrameHTTP(contract(),root=tmp,transport=lambda *a:self.fail('No eleventh start'))
            with self.assertRaises(ValueError):http.fetch(contract()['FDA_documentation'][0]['url'])
            self.assertEqual(len(http.starts()),10)

    def test_approval_selection_is_not_repaired_by_unknown_alternative(self):
        self.assertEqual(outcome_gate(approved_scope=True,alternative_complete=False,access_blocked=False),'OUTCOME_SELECTED_SOURCE_FRAME')
        self.assertEqual(outcome_gate(approved_scope=True,alternative_complete=None,access_blocked=False),'FRAME_UNCERTIFIED')
        self.assertEqual(outcome_gate(approved_scope=True,alternative_complete=None,access_blocked=True),'SOURCE_FRAME_AUDIT_INCOMPLETE_ACCESS_STOP')

    def test_original_bytes_and_access_stop_use_existing_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(url,headers,payload):return 403,{'Content-Type':'text/html'},b'FDA original denial',url
            http=FrameHTTP(contract(),root=tmp,transport=fake,sleep=lambda _:None)
            r,b=http.fetch(contract()['FDA_documentation'][0]['url'])
            self.assertEqual(http.archive.read(r['body']),b'FDA original denial')
            with self.assertRaises(ValueError):http.fetch(contract()['FDA_documentation'][1]['url'])
            self.assertEqual(len(http.starts()),1)

    def test_document_scope_locators_do_not_become_denominator_certificate(self):
        b=b'<h1>Drugs@FDA</h1><p>Drugs@FDA includes most of the drug products approved since 1939.</p><script>complete response letters</script>'
        result=scope_findings(b,'a'*64)
        self.assertEqual(len(result['locators']['approved_product_scope']),1)
        self.assertEqual(result['locators']['negative_document_reference'],[])
        self.assertIn('does not certify',result['locator_scope'])

    def test_missingness_private_applicants_and_rights_ambiguity_retained(self):
        self.assertNotEqual(missing_record('UNKNOWN'),missing_record('UNAVAILABLE'))
        self.assertIsNone(missing_record('NOT_APPLICABLE')['value'])
        records=[{'id':'A','status':'PRIVATE_APPLICANT'},{'id':'B','status':'RIGHTS_HOLDER_AMBIGUOUS'}]
        self.assertEqual(retain_identity(records),records)
        with self.assertRaises(ValueError):missing_record('zero')

    def test_procurement_price_and_registration_routes_not_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            http=FrameHTTP(contract(),root=tmp,transport=lambda *a:self.fail('Network boundary violated'))
            for url in ('https://www.defense.gov/News/Contracts/','https://api.tiingo.com/tiingo/daily/A/prices','https://api.nexustrade.io/backtest','https://www.sec.gov/Archives/edgar/data/1/file.html'):
                with self.assertRaises(ValueError):http.fetch(url)
            self.assertEqual(len(http.starts()),0)
