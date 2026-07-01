from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult
from .utils import compare_strings

class JobTitleComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        titles_a = []
        if candidate_a.professional_info:
            if candidate_a.professional_info.current_title:
                titles_a.append(candidate_a.professional_info.current_title)
            for exp in candidate_a.professional_info.experiences:
                if exp.title: titles_a.append(exp.title)
                
        titles_b = []
        if candidate_b.professional_info:
            if candidate_b.professional_info.current_title:
                titles_b.append(candidate_b.professional_info.current_title)
            for exp in candidate_b.professional_info.experiences:
                if exp.title: titles_b.append(exp.title)
                
        best_score = 0
        for ta in titles_a:
            for tb in titles_b:
                score = compare_strings(ta, tb, self.algorithm)
                if score > best_score:
                    best_score = score
                    
        return ComparisonResult(
            matched=best_score >= self.threshold,
            score=best_score,
            comparator_name=self.name,
            algorithm_used=self.algorithm
        )
