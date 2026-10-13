from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from src.research.sec_pilot.provenance import instant

class EvidenceTier(str,Enum):
    PRIMARY_ORIGINAL='PRIMARY_ORIGINAL'
    PRIMARY_INDEX_OR_METADATA='PRIMARY_INDEX_OR_METADATA'
    PRIMARY_DERIVED='PRIMARY_DERIVED'
    AUDITED_EXTERNAL_DERIVED='AUDITED_EXTERNAL_DERIVED'
    DISCOVERY_ONLY='DISCOVERY_ONLY'
    UNVERIFIED_EXTERNAL='UNVERIFIED_EXTERNAL'

@dataclass(frozen=True)
class ProviderResult:
    source_provider:str
    evidence_tier:EvidenceTier
    source_url:str
    source_sha256:str|None
    upstream_version:str
    upstream_commit_or_snapshot:str
    retrieved_at:str
    available_at_claim:str|None
    available_at_status:str
    revision_status:str
    canonical_for_what:str
    query_contract:dict
    provider_metadata:dict
    rows:tuple
    def __post_init__(self):
        if not isinstance(self.evidence_tier,EvidenceTier):raise ValueError('Explicit evidence tier required')
        instant(self.retrieved_at)
        if self.available_at_claim:instant(self.available_at_claim)
        if not self.source_url or not self.upstream_version or not self.canonical_for_what:raise ValueError('Source provenance incomplete')
    def require_original(self):
        if self.evidence_tier!=EvidenceTier.PRIMARY_ORIGINAL or not self.source_sha256:raise ValueError('External/derived results cannot satisfy PRIMARY_ORIGINAL')
        return self

class ResearchSurfaceAdapter(Protocol):
    surface_id:str
    evidence_tier:EvidenceTier
    def access_contract(self)->dict:...
    def probe_manifest(self)->dict:...
    def normalize_probe(self,rows)->ProviderResult:...
    def capabilities(self)->dict:...
