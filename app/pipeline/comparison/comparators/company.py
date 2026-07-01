from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult
from .utils import compare_strings

class CompanyComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        companies_a = []
        if candidate_a.professional_info:
            if candidate_a.professional_info.current_company:
                companies_a.append(candidate_a.professional_info.current_company)
            for exp in candidate_a.professional_info.experiences:
                if exp.company: companies_a.append(exp.company)
                
        companies_b = []
        if candidate_b.professional_info:
            if candidate_b.professional_info.current_company:
                companies_b.append(candidate_b.professional_info.current_company)
            for exp in candidate_b.professional_info.experiences:
                if exp.company: companies_b.append(exp.company)
                
        best_score = 0
        for ca in companies_a:
            for cb in companies_b:
                score = compare_strings(ca, cb, self.algorithm)
                if score > best_score:
                    best_score = score
                    
        missing_data = not companies_a or not companies_b
        return ComparisonResult(
            matched=best_score >= self.threshold,
            score=best_score,
            comparator_name=self.name,
            algorithm_used=self.algorithm,
            missing_data=missing_data
        )
