from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.pipeline.comparison.blocking.base import CandidatePair
from app.pipeline.comparison.comparators.base import ComparisonResult

class DecisionType(str, Enum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    REVIEW = "REVIEW"

class DecisionSource(str, Enum):
    RULE = "RULE"
    SIMILARITY = "SIMILARITY"
    THRESHOLD = "THRESHOLD"
    
class EvidenceBundle(BaseModel):
    candidate_pair: CandidatePair
    comparison_results: Dict[str, ComparisonResult]
    
class RuleExplanation(BaseModel):
    rule_id: str
    outcome: str
    supporting_comparators: List[str]
    message: str

class RuleResult(BaseModel):
    triggered: bool
    rule_id: str
    terminating: bool
    decision: Optional[DecisionType]
    explanation: Optional[RuleExplanation]

class SimilarityExplanation(BaseModel):
    contributing_fields: List[str]
    ignored_fields: List[str]
    weighted_score_breakdown: Dict[str, int]

class SimilarityResult(BaseModel):
    overall_score: int
    field_scores: Dict[str, int]
    explanation: SimilarityExplanation

class DecisionExplanation(BaseModel):
    final_decision: DecisionType
    decision_source: DecisionSource
    message: str

class DecisionResult(BaseModel):
    decision: DecisionType
    explanation: DecisionExplanation

class IdentityResolutionResult(BaseModel):
    candidate_pair: CandidatePair
    decision: DecisionType
    rule_result: Optional[RuleResult]
    similarity_result: Optional[SimilarityResult]
    decision_result: DecisionResult
