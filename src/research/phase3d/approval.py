"""Verify a recorded owner modeling decision; does not activate an eligibility view."""
import json
from pathlib import Path
from src.research.spec import digest
from .proof import file_hash


def approved_pilot(docs):
    docs=Path(docs)
    path=docs/'availability_policy_v002_approved.json'
    if not path.exists(): return None
    approval=json.loads(path.read_bytes())
    prior=json.loads((docs/'phase3c_evidence.json').read_bytes())
    policy=prior['policy']
    decision_path=docs/'decisions/availability_v002_owner_reply_001.json'
    packet_path=docs/'decisions/availability_v002_review_packet_001.md'
    if (approval.get('status')!='OWNER_APPROVED_MODELED_POLICY'
            or approval.get('policy_sha256')!=digest(policy) or digest(policy)!=prior['policy_sha256']
            or approval.get('scope')!=policy['scope'] or approval['scope']!=['2015-01-01','2021-12-31']
            or approval.get('source_evidence_sha256')!=file_hash(docs/'phase3c_evidence.json')
            or approval.get('timing_snapshot_sha256')!=digest(prior['timing'])
            or approval.get('calendar_source_sha256')!=policy['calendar_source_sha256']
            or approval.get('acceptance_evidence_sha256')!=policy['acceptance_evidence_sha256']
            or approval.get('owner_reply_sha256')!=file_hash(decision_path)
            or approval.get('review_packet_sha256')!=file_hash(packet_path)):
        raise ValueError('Owner policy approval lineage or scope changed')
    decision=json.loads(decision_path.read_bytes())
    if (decision.get('answer')!='Approve the exact pilot policy and modeled timing uncertainty'
            or decision.get('questionItemId')!='["request_user_input_async","call_bf60c7eb73dd45eda0eb907a508d17f0",0]'
            or decision.get('source_role')!='user' or decision.get('policy_sha256')!=approval['policy_sha256']
            or decision.get('review_packet_sha256')!=approval['review_packet_sha256']
            or approval.get('exact_public_availability')!='UNKNOWN' or approval.get('activation_status')!='NOT_ACTIVATED'
            or approval.get('modeled_timing_uncertainty_accepted') is not True):
        raise ValueError('Owner decision absent or observed/modelled clock promoted')
    return approval
