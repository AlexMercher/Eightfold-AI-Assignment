from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult
from .utils import compare_strings

class NameComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        name_a = candidate_a.personal_info.name if candidate_a.personal_info else ""
        name_b = candidate_b.personal_info.name if candidate_b.personal_info else ""
        
        score = compare_strings(name_a, name_b, self.algorithm)
        matched = score >= self.threshold
        missing_data = not name_a or not name_b
        
        return ComparisonResult(
            matched=matched,
            score=score,
            comparator_name=self.name,
            algorithm_used=self.algorithm,
            missing_data=missing_data
        )
