from typing import List
from app.models.canonical import Candidate
from .base import BaseBlockingStrategy

class NameUniversityBlockingStrategy(BaseBlockingStrategy):
    def generate_keys(self, candidate: Candidate) -> List[str]:
        keys = []
        
        if not candidate.personal_info or not candidate.personal_info.name:
            return keys
            
        name = candidate.personal_info.name.strip().lower()
        
        if candidate.education:
            for edu in candidate.education:
                if edu.institution:
                    uni = edu.institution.strip().lower()
                    keys.append(f"{self.name}:{name}|{uni}")
                    
        return keys
