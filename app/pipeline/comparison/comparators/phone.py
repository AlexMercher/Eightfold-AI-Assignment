from app.models.canonical import Candidate
from .base import BaseComparator, ComparisonResult

class PhoneComparator(BaseComparator):
    def matches(self, candidate_a: Candidate, candidate_b: Candidate) -> ComparisonResult:
        phones_a = set()
        if candidate_a.contact_info:
            phones_a = {p for p in candidate_a.contact_info.phone_numbers}
            
        phones_b = set()
        if candidate_b.contact_info:
            phones_b = {p for p in candidate_b.contact_info.phone_numbers}
            
        overlap = phones_a.intersection(phones_b)
        matched = len(overlap) > 0
        
        return ComparisonResult(
            matched=matched,
            score=100 if matched else 0,
            comparator_name=self.name,
            algorithm_used=self.algorithm
        )
