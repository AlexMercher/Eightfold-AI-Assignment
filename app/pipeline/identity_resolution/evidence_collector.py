from typing import Dict
from app.models.canonical import Candidate
from app.pipeline.comparison.blocking.base import CandidatePair
from app.pipeline.comparison.comparators.registry import ComparatorRegistry
from app.pipeline.comparison.comparators.base import ComparisonResult
from .models import EvidenceBundle

class EvidenceCollector:
    def __init__(self, comparator_registry: ComparatorRegistry):
        self.registry = comparator_registry
        
    def collect(self, candidate_a: Candidate, candidate_b: Candidate, candidate_pair: CandidatePair) -> EvidenceBundle:
        """
        Executes ALL comparators exactly once and creates an immutable EvidenceBundle.
        """
        results: Dict[str, ComparisonResult] = {}
        
        # Iterate over all registered comparators to gather total evidence
        # (This is safe and avoids O(n^2) because we are only running this on 
        # the small subset of pairs that passed blocking and eligibility).
        with self.registry._lock:
            comparators = list(self.registry._registry.values())
            
        for comp in comparators:
            res = comp.matches(candidate_a, candidate_b)
            results[comp.name] = res
            
        return EvidenceBundle(
            candidate_pair=candidate_pair,
            comparison_results=results
        )
