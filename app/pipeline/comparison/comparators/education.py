from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult

class EducationComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        edu_a = {e.degree.lower() for e in candidate_a.education if e.degree}
        edu_b = {e.degree.lower() for e in candidate_b.education if e.degree}
            
        overlap = edu_a.intersection(edu_b)
        matched = len(overlap) > 0
        
        return ComparisonResult(
            matched=matched,
            score=100 if matched else 0,
            comparator_name=self.name,
            algorithm_used=self.algorithm
        )
