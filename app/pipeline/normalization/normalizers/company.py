import re
from app.models.canonical import ProfessionalInfo
from ..base import BaseNormalizer, NormalizationResult, ValidationState, load_aliases

class CompanyNormalizer(BaseNormalizer):
    def __init__(self, config_path: str = "config/normalization/company_aliases.yaml"):
        self.aliases = load_aliases(config_path)
        
    def _normalize_name(self, name: str) -> str:
        if not name: return name
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        lookup = name.lower()
        if lookup in self.aliases:
            return self.aliases[lookup]
        return name
        
    def normalize(self, prof_info: ProfessionalInfo) -> NormalizationResult[ProfessionalInfo]:
        state = ValidationState.VALID
        
        if prof_info.current_company:
            orig = prof_info.current_company
            prof_info.current_company = self._normalize_name(orig)
            if prof_info.current_company.lower() not in self.aliases:
                state = ValidationState.UNKNOWN
                
        for exp in prof_info.experiences:
            if exp.company:
                exp.company = self._normalize_name(exp.company)
                if exp.company.lower() not in self.aliases:
                    state = ValidationState.UNKNOWN
                    
        return NormalizationResult(prof_info, state)
