from typing import List
from app.models.canonical import Candidate
from .base import BaseBlockingStrategy

class NameCompanyBlockingStrategy(BaseBlockingStrategy):
    def generate_keys(self, candidate: Candidate) -> List[str]:
        keys = []
        
        # Get name (first name usually sufficient for blocking, or whole name lowercased)
        if not candidate.personal_info or not candidate.personal_info.name:
            return keys
            
        name = candidate.personal_info.name.strip().lower()
        
        # Get companies
        companies = set()
        if candidate.professional_info:
            if candidate.professional_info.current_company:
                companies.add(candidate.professional_info.current_company.lower())
            for exp in candidate.professional_info.experiences:
                if exp.company:
                    companies.add(exp.company.lower())
                    
        for company in companies:
            keys.append(f"{self.name}:{name}|{company}")
                
        return keys
