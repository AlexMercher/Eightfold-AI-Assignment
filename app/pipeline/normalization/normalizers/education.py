import re
from typing import List
from app.models.canonical import Education
from ..base import BaseNormalizer, NormalizationResult, ValidationState, load_aliases

class EducationNormalizer(BaseNormalizer):
    def __init__(self, config_path: str = "config/normalization/education_aliases.yaml"):
        self.aliases = load_aliases(config_path)
        
    def _normalize_degree(self, degree: str) -> str:
        if not degree: return degree
        degree = degree.strip()
        degree = re.sub(r'\s+', ' ', degree)
        lookup = degree.lower()
        # Remove common punctuation for lookup matching (e.g. B.S. -> bs)
        lookup_no_punct = re.sub(r'[^a-z0-9]', '', lookup)
        
        if lookup in self.aliases:
            return self.aliases[lookup]
        if lookup_no_punct in self.aliases:
            return self.aliases[lookup_no_punct]
            
        return degree
        
    def normalize(self, educations: List[Education]) -> NormalizationResult[List[Education]]:
        state = ValidationState.VALID
        
        for edu in educations:
            if edu.degree:
                edu.degree = self._normalize_degree(edu.degree)
                lookup = re.sub(r'[^a-z0-9]', '', edu.degree.lower())
                if edu.degree.lower() not in self.aliases and lookup not in self.aliases:
                    state = ValidationState.UNKNOWN
                    
        return NormalizationResult(educations, state)
