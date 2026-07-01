from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict
from app.models.canonical import Candidate
from app.pipeline.identity_resolution.models import IdentityResolutionResult

class ClusterStatus(str, Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"

class ValidatedCluster(BaseModel):
    candidates: List[Candidate]
    edges: List[IdentityResolutionResult]
    status: ClusterStatus
    contradictions: List[str]

class ConflictResult(BaseModel):
    winning_value: Any
    rejected_values: List[Any]
    reason: str

class ProvenanceRecord(BaseModel):
    source_candidates: List[str]
    merge_decision_path: str

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ConfidenceResult(BaseModel):
    level: ConfidenceLevel
    conflict_count: int
    source_count: int
    reasoning: str

class MergeResult(BaseModel):
    candidate: Candidate
    conflicts: Dict[str, ConflictResult]
    provenance: Dict[str, ProvenanceRecord]

class ProjectedCandidate(BaseModel):
    id: str
    name: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    company: Optional[str] = None
    skills: List[Any] = []
    education: List[Any] = []
    social_profiles: List[Any] = []

class ProjectionResult(BaseModel):
    dictionary_view: Dict[str, Any]
    projected: Optional[ProjectedCandidate] = None
