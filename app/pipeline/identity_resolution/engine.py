from app.models.canonical import Candidate
from app.pipeline.comparison.blocking.base import CandidatePair
from app.pipeline.comparison.comparators.registry import ComparatorRegistry
from .models import IdentityResolutionResult
from .evidence_collector import EvidenceCollector
from .rule_engine import RuleEngine
from .similarity_engine import SimilarityEngine
from .decision_engine import DecisionEngine

class IdentityResolutionEngine:
    def __init__(self, comparator_registry: ComparatorRegistry):
        self.evidence_collector = EvidenceCollector(comparator_registry)
        self.rule_engine = RuleEngine()
        self.similarity_engine = SimilarityEngine()
        self.decision_engine = DecisionEngine()
        
    def resolve(self, candidate_a: Candidate, candidate_b: Candidate, pair: CandidatePair) -> IdentityResolutionResult:
        # 1. Collect Evidence exactly once
        bundle = self.evidence_collector.collect(candidate_a, candidate_b, pair)
        
        # 2. Evaluate hard rules
        rule_result = self.rule_engine.evaluate(bundle)
        
        # 3. Calculate Similarity (skipped if rule terminates pipeline)
        sim_result = None
        if not rule_result.terminating:
            sim_result = self.similarity_engine.calculate(bundle)
            
        # 4. Make final Decision
        decision_result = self.decision_engine.decide(rule_result, sim_result)
        
        # 5. Package Immutable IdentityResolutionResult
        return IdentityResolutionResult(
            candidate_pair=pair,
            decision=decision_result.decision,
            rule_result=rule_result,
            similarity_result=sim_result,
            decision_result=decision_result
        )
