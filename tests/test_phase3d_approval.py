import json
from pathlib import Path
import shutil
import tempfile
import unittest
from src.research.phase3d.approval import approved_pilot


class PilotApprovalTests(unittest.TestCase):
    def fixture(self,root):
        docs=Path('docs/acceleration'); root=Path(root); (root/'decisions').mkdir()
        for name in ('phase3c_evidence.json','availability_policy_v002_approved.json',
                     'decisions/availability_v002_owner_reply_001.json','decisions/availability_v002_review_packet_001.md'):
            shutil.copyfile(docs/name,root/name)
        return root

    def test_exact_owner_scope_accepted_without_clock_or_activation_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=approved_pilot(self.fixture(tmp))
            self.assertEqual(result['scope'],['2015-01-01','2021-12-31'])
            self.assertEqual(result['exact_public_availability'],'UNKNOWN')
            self.assertEqual(result['activation_status'],'NOT_ACTIVATED')

    def test_missing_decision_unapproved_and_changed_policy_lineage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(approved_pilot(tmp))
        for key,value in (('scope',['2015-01-01','2032-12-31']),('policy_sha256','0'*64),
                          ('activation_status','ACTIVATED'),('exact_public_availability','CERTIFIED')):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as tmp:
                root=self.fixture(tmp); path=root/'availability_policy_v002_approved.json'
                approval=json.loads(path.read_bytes()); approval[key]=value; path.write_text(json.dumps(approval))
                with self.assertRaises(ValueError): approved_pilot(root)

    def test_owner_reply_and_original_review_packet_cannot_change(self):
        for name in ('decisions/availability_v002_owner_reply_001.json','decisions/availability_v002_review_packet_001.md','phase3c_evidence.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=self.fixture(tmp); path=root/name; path.write_bytes(path.read_bytes()+b' ')
                with self.assertRaises(ValueError): approved_pilot(root)
