import uuid
from typing import Any

from app.models.canonical import (
    Candidate, PersonalInfo, ContactInfo, ProfessionalInfo, 
    Experience, Skill, Education, Project, Certification, SocialProfile
)
from .base_mapper import BaseMapper

class CsvMapper(BaseMapper):
    """Maps a raw CSV row (e.g. from Master.csv) to the Canonical Candidate model."""
    
    def map_to_canonical(self, source_data: Any) -> Candidate:
        # source_data is expected to be a pandas Series or dict
        row = source_data
        
        # Helper to safely extract string values
        def get_val(key: str) -> str:
            val = row.get(key, "")
            return str(val).strip() if pd.notna(val) and val != "" else ""

        import pandas as pd
        
        # Extract Contact
        emails = []
        if get_val("Email"): emails.append(get_val("Email"))
        
        phones = []
        if get_val("Phone"): phones.append(get_val("Phone"))
        
        # Extract Experience
        experiences = []
        company = get_val("CurrentCompany")
        title = get_val("CurrentJobTitle")
        if company or title:
            experiences.append(Experience(
                company=company or "Unknown",
                title=title or "Unknown"
            ))
            
        # Extract Skills
        skills = []
        raw_skills = get_val("Skills")
        if raw_skills:
            for s in raw_skills.split(","):
                if s.strip():
                    skills.append(Skill(name=s.strip()))
                    
        # Extract Education
        educations = []
        degree = get_val("Education")
        uni = get_val("University")
        grad_year = get_val("GraduationYear")
        if degree or uni:
            educations.append(Education(
                institution=uni or "Unknown",
                degree=degree or "Unknown",
                graduation_year=grad_year if grad_year else None
            ))
            
        # Extract Projects
        projects = []
        raw_projs = get_val("Projects")
        if raw_projs:
            for p in raw_projs.split(";"):
                if p.strip():
                    projects.append(Project(name=p.strip()))
                    
        # Extract Certifications
        certs = []
        raw_certs = get_val("Certifications")
        if raw_certs:
            for c in raw_certs.split(";"):
                if c.strip():
                    certs.append(Certification(name=c.strip(), issuing_organization="Unknown"))
                    
        # Extract Social
        socials = []
        github = get_val("GitHub")
        linkedin = get_val("LinkedIn")
        portfolio = get_val("Portfolio")
        if github: socials.append(SocialProfile(platform="GitHub", url=github))
        if linkedin: socials.append(SocialProfile(platform="LinkedIn", url=linkedin))
        if portfolio: socials.append(SocialProfile(platform="Portfolio", url=portfolio))
        
        exp_years_str = get_val("TotalExperienceYears")
        total_exp = None
        if exp_years_str:
            try:
                total_exp = float(exp_years_str)
            except ValueError:
                pass
                
        candidate_id = get_val("CandidateID")
        if not candidate_id:
            candidate_id = str(uuid.uuid4())

        return Candidate(
            candidate_id=candidate_id,
            personal_info=PersonalInfo(
                name=get_val("FullName"),
                location=get_val("Location") or None
            ),
            contact_info=ContactInfo(
                emails=emails,
                phone_numbers=phones
            ),
            professional_info=ProfessionalInfo(
                current_company=company or None,
                current_title=title or None,
                total_experience_years=total_exp,
                experiences=experiences,
                skills=skills
            ),
            education=educations,
            projects=projects,
            certifications=certs,
            social_profiles=socials
        )
