from typing import List
from app.models.canonical import Candidate
from .base import BaseBlockingStrategy
from app.pipeline.normalization.normalizers.location import LocationParser

class CompanyCityBlockingStrategy(BaseBlockingStrategy):
    def generate_keys(self, candidate: Candidate) -> List[str]:
        keys = []
        
        # Get location city
        cities = set()
        if candidate.personal_info and candidate.personal_info.location:
            parsed = LocationParser.parse(candidate.personal_info.location)
            if parsed.city:
                cities.add(parsed.city.lower())
                
        if not cities:
            return keys
            
        # Get companies
        companies = set()
        if candidate.professional_info:
            if candidate.professional_info.current_company:
                companies.add(candidate.professional_info.current_company.lower())
            for exp in candidate.professional_info.experiences:
                if exp.company:
                    companies.add(exp.company.lower())
                    
        for company in companies:
            for city in cities:
                keys.append(f"{self.name}:{company}|{city}")
                
        return keys
