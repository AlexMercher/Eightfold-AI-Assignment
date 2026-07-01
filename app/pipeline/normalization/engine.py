from typing import List, Optional
from app.models.canonical import Candidate
from .registry import NormalizerRegistry
from .base import ValidationState

class NormalizationEngine:
    def __init__(self):
        self.registry = NormalizerRegistry()
        self._register_all()
        
    def _register_all(self):
        # We will import them lazily or directly.
        from .normalizers.name import NameNormalizer
        from .normalizers.email import EmailNormalizer
        from .normalizers.phone import PhoneNormalizer
        from .normalizers.skill import SkillNormalizer
        from .normalizers.company import CompanyNormalizer
        from .normalizers.job_title import JobTitleNormalizer
        from .normalizers.education import EducationNormalizer
        from .normalizers.location import LocationNormalizer
        from .normalizers.date import DateNormalizer
        from .normalizers.url import UrlNormalizer
        
        self.registry.register("name", NameNormalizer())
        self.registry.register("email", EmailNormalizer())
        self.registry.register("phone", PhoneNormalizer())
        self.registry.register("skill", SkillNormalizer())
        self.registry.register("company", CompanyNormalizer())
        self.registry.register("job_title", JobTitleNormalizer())
        self.registry.register("education", EducationNormalizer())
        self.registry.register("location", LocationNormalizer())
        self.registry.register("date", DateNormalizer())
        self.registry.register("url", UrlNormalizer())
        
    def normalize(self, raw_candidate: Candidate) -> Candidate:
        # 1. Clone to ensure original is immutable
        candidate = raw_candidate.model_copy(deep=True)
        
        # 2. Name
        if candidate.personal_info:
            res = self.registry.get("name").normalize(candidate.personal_info)
            if res.state != ValidationState.UNPARSEABLE:
                candidate.personal_info = res.data
                
        # 3. Location
        if candidate.personal_info and candidate.personal_info.location:
            res = self.registry.get("location").normalize(candidate.personal_info.location)
            if res.state != ValidationState.UNPARSEABLE:
                candidate.personal_info.location = res.data
            else:
                candidate.personal_info.location = None
                
        # 4. Emails
        if candidate.contact_info:
            res = self.registry.get("email").normalize(candidate.contact_info)
            if res.state != ValidationState.UNPARSEABLE:
                candidate.contact_info = res.data
                
        # 5. Phones
        if candidate.contact_info:
            res = self.registry.get("phone").normalize(candidate.contact_info)
            if res.state != ValidationState.UNPARSEABLE:
                candidate.contact_info = res.data
                
        # 6. Skills
        if candidate.professional_info and candidate.professional_info.skills:
            res = self.registry.get("skill").normalize(candidate.professional_info.skills)
            candidate.professional_info.skills = res.data
            
        # 7. Company & Job Title
        if candidate.professional_info:
            res = self.registry.get("company").normalize(candidate.professional_info)
            candidate.professional_info = res.data
            
            res = self.registry.get("job_title").normalize(candidate.professional_info)
            candidate.professional_info = res.data
            
        # 8. Education
        if candidate.education:
            res = self.registry.get("education").normalize(candidate.education)
            candidate.education = res.data
            
        # 9. Dates (Pipeline orchestrates passing only specific date fields)
        date_norm = self.registry.get("date")
        
        def _norm_date(date_str: Optional[str]) -> Optional[str]:
            if not date_str: return None
            dr = date_norm.normalize(date_str)
            return dr.data if dr.state != ValidationState.UNPARSEABLE else None
            
        if candidate.professional_info:
            for exp in candidate.professional_info.experiences:
                exp.start_date = _norm_date(exp.start_date)
                exp.end_date = _norm_date(exp.end_date)
                
        for edu in candidate.education:
            edu.graduation_year = _norm_date(edu.graduation_year)
            
        for proj in candidate.projects:
            # wait, Project in canonical doesn't have dates in the current version? Let me check
            pass
            
        for cert in candidate.certifications:
            cert.issue_date = _norm_date(cert.issue_date)
            
        # 10. URL (Social Profiles)
        if candidate.social_profiles:
            res = self.registry.get("url").normalize(candidate.social_profiles)
            candidate.social_profiles = res.data
            
        return candidate
