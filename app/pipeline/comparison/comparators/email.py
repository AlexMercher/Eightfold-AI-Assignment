from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult

class EmailComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        emails_a = set()
        if candidate_a.contact_info:
            emails_a = {e.lower() for e in candidate_a.contact_info.emails}
            
        emails_b = set()
        if candidate_b.contact_info:
            emails_b = {e.lower() for e in candidate_b.contact_info.emails}
            
        overlap = emails_a.intersection(emails_b)
        matched = len(overlap) > 0
        
        missing_data = not emails_a or not emails_b
        return ComparisonResult(
            matched=matched,
            score=100 if matched else 0,
            comparator_name=self.name,
            algorithm_used=self.algorithm,
            missing_data=missing_data
        )
