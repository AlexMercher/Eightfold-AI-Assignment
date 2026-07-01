from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult

class PortfolioComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        urls_a = {p.url for p in candidate_a.social_profiles if p.platform.lower() == "portfolio"}
        urls_b = {p.url for p in candidate_b.social_profiles if p.platform.lower() == "portfolio"}
            
        overlap = urls_a.intersection(urls_b)
        matched = len(overlap) > 0
        
        return ComparisonResult(
            matched=matched,
            score=100 if matched else 0,
            comparator_name=self.name,
            algorithm_used=self.algorithm
        )
