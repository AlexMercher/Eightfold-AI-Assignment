import uuid
from typing import Any

from app.models.canonical import (
    Candidate, PersonalInfo, ContactInfo, ProfessionalInfo, 
    Experience, Skill, Education, Project, Certification, SocialProfile
)
from app.models.schemas.extracted_data import ExtractedResumeSchema
from .base_mapper import BaseMapper

class ResumeMapper(BaseMapper):
    """Maps the existing ExtractedResumeSchema to the Canonical Candidate model."""
    
    def map_to_canonical(self, source_data: Any) -> Candidate:
        if not isinstance(source_data, ExtractedResumeSchema):
            raise TypeError("ResumeMapper expects an ExtractedResumeSchema")
            
        schema: ExtractedResumeSchema = source_data
        
        # Extract Contact
        emails = []
        if schema.contact.email: emails.append(schema.contact.email)
            
        phones = []
        if schema.contact.phone: phones.append(schema.contact.phone)
            
        socials = []
        if schema.contact.linkedin:
            socials.append(SocialProfile(platform="LinkedIn", url=schema.contact.linkedin))
        if schema.contact.github:
            socials.append(SocialProfile(platform="GitHub", url=schema.contact.github))
        if schema.contact.website:
            socials.append(SocialProfile(platform="Website", url=schema.contact.website))
            
        # Extract Experience
        experiences = []
        curr_company = None
        curr_title = None
        
        for exp in schema.experience:
            experiences.append(Experience(
                company=exp.company or "Unknown",
                title=exp.job_title or "Unknown",
                start_date=exp.start_date,
                end_date=exp.end_date,
                description=exp.description
            ))
            if exp.is_current and not curr_company:
                curr_company = exp.company
                curr_title = exp.job_title
                
        # If none marked current, pick the first one as current heuristic
        if not curr_company and experiences:
            curr_company = experiences[0].company
            curr_title = experiences[0].title
            
        # Extract Skills
        skills = []
        if schema.skills and schema.skills.all:
            for s in schema.skills.all:
                if s.strip():
                    skills.append(Skill(name=s.strip()))
                    
        # Extract Education
        educations = []
        for edu in schema.education:
            educations.append(Education(
                institution=edu.institution or "Unknown",
                degree=edu.degree or "Unknown",
                field_of_study=edu.field_of_study,
                graduation_year=edu.graduation_date
            ))
            
        # Extract Projects
        projects = []
        for proj in schema.projects:
            projects.append(Project(
                name=proj.name or "Unknown",
                description=proj.description,
                technologies=proj.technologies
            ))
            
        # Extract Certifications
        certs = []
        for cert in schema.certifications:
            certs.append(Certification(
                name=cert.name or "Unknown",
                issuing_organization=cert.issuer or "Unknown",
                issue_date=cert.date
            ))
            
        # Create Canonical Candidate
        candidate_id = str(uuid.uuid4())
        
        # Calculate total experience if available
        total_exp = 0.0
        for exp in schema.experience:
            if exp.duration_years:
                total_exp += exp.duration_years
                
        return Candidate(
            candidate_id=candidate_id,
            personal_info=PersonalInfo(
                name=schema.contact.full_name or "",
                location=schema.contact.city or schema.contact.address
            ),
            contact_info=ContactInfo(
                emails=emails,
                phone_numbers=phones,
                website=schema.contact.website
            ),
            professional_info=ProfessionalInfo(
                current_company=curr_company,
                current_title=curr_title,
                total_experience_years=total_exp if total_exp > 0 else None,
                experiences=experiences,
                skills=skills
            ),
            education=educations,
            projects=projects,
            certifications=certs,
            social_profiles=socials
        )
