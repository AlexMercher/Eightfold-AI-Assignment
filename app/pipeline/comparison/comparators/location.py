from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult
from .utils import compare_strings

class LocationComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        loc_a = candidate_a.personal_info.location if candidate_a.personal_info else ""
        loc_b = candidate_b.personal_info.location if candidate_b.personal_info else ""
        
        score = compare_strings(loc_a, loc_b, self.algorithm)
        matched = score >= self.threshold
        
        return ComparisonResult(
            matched=matched,
            score=score,
            comparator_name=self.name,
            algorithm_used=self.algorithm
        )
