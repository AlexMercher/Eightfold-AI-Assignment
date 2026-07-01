import re
from app.models.canonical import ProfessionalInfo
from ..base import BaseNormalizer, NormalizationResult, ValidationState, load_aliases

class JobTitleNormalizer(BaseNormalizer):
    def __init__(self, config_path: str = "config/normalization/job_title_aliases.yaml"):
        self.aliases = load_aliases(config_path)
        
    def _normalize_title(self, title: str) -> str:
        if not title: return title
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)
        lookup = title.lower()
        if lookup in self.aliases:
            return self.aliases[lookup]
        return title
        
    def normalize(self, prof_info: ProfessionalInfo) -> NormalizationResult[ProfessionalInfo]:
        state = ValidationState.VALID
        
        if prof_info.current_title:
            prof_info.current_title = self._normalize_title(prof_info.current_title)
            if prof_info.current_title.lower() not in self.aliases:
                state = ValidationState.UNKNOWN
                
        for exp in prof_info.experiences:
            if exp.title:
                exp.title = self._normalize_title(exp.title)
                if exp.title.lower() not in self.aliases:
                    state = ValidationState.UNKNOWN
                    
        return NormalizationResult(prof_info, state)
