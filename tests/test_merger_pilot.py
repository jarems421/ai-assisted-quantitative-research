import copy
import tempfile
import unittest
from pathlib import Path
from src.research.merger_pilot import contract,validate,FrameHTTP,frame_gate,gate2_authority,PASS_REQUIREMENTS,party_record,screen_state,missing_record
from src.research.phase3c.sources import put


class MergerPilotTests(unittest.TestCase):
    def test_exact_manifest_ceiling_filters_and_months(self):
        m=contract();validate(m);self.assertEqual(len(m['conditional_gate2_slots']),12)
        self.assertEqual(m['gate2_selection'],'FIRST_ELIGIBLE_PENDING_MERGER_FROM_PRE_OUTCOME_FRAME_NOT_FIRST_ENFORCEMENT_ACTION')
        for k,v in [('request_ceiling',13),('total_pilot_ceiling',73),('month_substitution',True),('performance_authorized',True)]:
            bad=copy.deepcopy(m);bad[k]=v
            with self.assertRaises(ValueError):validate(bad)
        for k in ('challenged_only','completed_only','current_survivor','public_acquirer','price'):
            bad=copy.deepcopy(m);bad['filters'][k]=True
            with self.assertRaises(ValueError):validate(bad)

    def test_complete_predecision_evidence_before_gate2(self):
        evidence={k:True for k in PASS_REQUIREMENTS};evidence['review_receipt_sha256']='a'*64
        self.assertEqual(frame_gate(evidence),'PRE_DECISION_RISK_SET_PLAUSIBLE')
        self.assertEqual(gate2_authority(evidence,total_starts=12,event_manifest_frozen=True),'SOURCE_ONLY_NO_PERFORMANCE')
        for key in (*PASS_REQUIREMENTS,'review_receipt_sha256'):
            bad=evidence.copy();bad.pop(key)
            with self.assertRaises(ValueError):gate2_authority(bad,total_starts=12,event_manifest_frozen=True)
        with self.assertRaises(ValueError):gate2_authority(evidence,total_starts=12,event_manifest_frozen=False)
        with self.assertRaises(ValueError):gate2_authority(evidence,total_starts=72,event_manifest_frozen=True)

    def test_treatment_only_is_not_repaired_by_unknown_alternative(self):
        self.assertEqual(frame_gate({'enforcement_selected':True,'alternative_risk_set':False}),'TREATMENT_SELECTED_SOURCE_FRAME')
        self.assertEqual(frame_gate({'enforcement_selected':True}),'DENOMINATOR_UNCERTIFIED')
        self.assertEqual(frame_gate({'access_blocked':True}),'SOURCE_ACCESS_BLOCKED')

    def test_twelfth_start_ceiling_persists_before_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(12):put(Path(tmp)/'reservations'/f'{i}.json',{'request_started_at_utc':'2000-01-01T00:00:00+00:00'})
            h=FrameHTTP(contract(),root=tmp,transport=lambda *a:self.fail('Thirteenth start'))
            with self.assertRaises(ValueError):h.fetch(contract()['official_documentation'][0]['url'])
            self.assertEqual(len(h.starts()),12)

    def test_error_bytes_immutable_cached_and_stop_not_reviewed_away(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(url,*args):return 403,{'Content-Type':'text/html'},b'original merger denial',url
            h=FrameHTTP(contract(),root=tmp,transport=fake,sleep=lambda _:None);pages=contract()['official_documentation']
            receipt,body=h.fetch(pages[0]['url']);self.assertEqual(h.archive.read(receipt['body']),body)
            h.fetch(pages[0]['url']);self.assertEqual(len(h.starts()),1)
            self.assertFalse(h.reviewed_stop_allows(pages[1]['url']))
            with self.assertRaises(ValueError):h.fetch(pages[1]['url'])
            path=Path(tmp)/receipt['body']['path'];path.write_bytes(b'altered')
            with self.assertRaises(ValueError):h.archive.read(receipt['body'])

    def test_redirect_retained_without_substitution(self):
        with tempfile.TemporaryDirectory() as tmp:
            h=FrameHTTP(contract(),root=tmp,transport=lambda url,*a:(302,{},b'redirect',url),sleep=lambda _:None)
            with self.assertRaises(ValueError):h.fetch(contract()['official_documentation'][0]['url'])
            self.assertEqual(len(h.starts()),1);self.assertTrue((Path(tmp)/'publication_stop.json').exists())

    def test_target_acquirer_lifecycle_and_unknown_separate(self):
        r=party_record('synthetic');r['target']['status']='ENDED_TARGET_UNRESOLVED'
        self.assertEqual(r['acquirer']['status'],'UNKNOWN');self.assertEqual(r['lifecycle_status'],'UNAVAILABLE')
        self.assertIsNone(r['consideration']);self.assertIsNone(r['observed_public_at']);self.assertFalse(r['timing_policy_approved'])
        self.assertNotEqual(missing_record('UNKNOWN'),missing_record('UNAVAILABLE'))

    def test_no_prices_or_registration_or_old_family_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            h=FrameHTTP(contract(),root=tmp,transport=lambda *a:self.fail('Forbidden route'))
            for url in ('https://api.tiingo.com/tiingo/daily/A/prices','https://api.nexustrade.io/backtest','https://open.fda.gov/apis/drug/drugsfda/','https://www.defense.gov/News/Contracts/'):
                with self.assertRaises(ValueError):h.fetch(url)
            self.assertEqual(len(h.starts()),0)

    def test_three_family_exhaustion_never_launches_candidate_four(self):
        state=screen_state('MERGER_FAMILY_REJECT');self.assertEqual(state['family_screen'],'THREE_PREDECLARED_FAMILIES_EXHAUSTED')
        self.assertEqual(state['next_experiment'],'NONE_SELECTED');self.assertFalse(state['automatic_next_family'])
        for verdict in ('MERGER_FAMILY_ADVANCE','MERGER_FAMILY_REDESIGN'):
            self.assertFalse(screen_state(verdict)['performance_authorized']);self.assertFalse(screen_state(verdict)['automatic_next_family'])
        with self.assertRaises(ValueError):screen_state('SELECT_FOURTH_FAMILY')
