from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult

class SkillComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        skills_a = set()
        if candidate_a.professional_info:
            skills_a = {s.normalized_name.lower() if s.normalized_name else s.name.lower() 
                        for s in candidate_a.professional_info.skills}
                        
        skills_b = set()
        if candidate_b.professional_info:
            skills_b = {s.normalized_name.lower() if s.normalized_name else s.name.lower() 
                        for s in candidate_b.professional_info.skills}
                        
        if not skills_a or not skills_b:
            return ComparisonResult(
                matched=False,
                score=0,
                comparator_name=self.name,
                algorithm_used=self.algorithm
            )
            
        overlap = skills_a.intersection(skills_b)
        min_len = min(len(skills_a), len(skills_b))
        
        # Calculate overlap percentage (Jaccard-like, or overlap / min(A,B))
        score = int((len(overlap) / min_len) * 100) if min_len > 0 else 0
        
        return ComparisonResult(
            matched=score >= self.threshold,
            score=score,
            comparator_name=self.name,
            algorithm_used=self.algorithm
        )
