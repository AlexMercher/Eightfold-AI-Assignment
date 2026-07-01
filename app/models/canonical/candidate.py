from typing import List
from pydantic import BaseModel, Field

from .components import (
    PersonalInfo,
    ContactInfo,
    ProfessionalInfo,
    Education,
    Project,
    Certification,
    SocialProfile,
    ProvenanceEntry,
)

class Candidate(BaseModel):
    """
    The Canonical Candidate Model.
    This serves as the single source of truth for the entire pipeline.
    """
    candidate_id: str = Field(..., description="Unique identifier for the candidate.")
    
    personal_info: PersonalInfo = Field(
        default_factory=PersonalInfo, 
        description="Candidate's personal details."
    )
    
    contact_info: ContactInfo = Field(
        default_factory=ContactInfo, 
        description="Candidate's contact information."
    )
    
    professional_info: ProfessionalInfo = Field(
        default_factory=ProfessionalInfo, 
        description="Candidate's professional background and skills."
    )
    
    education: List[Education] = Field(
        default_factory=list, 
        description="List of educational qualifications."
    )
    
    projects: List[Project] = Field(
        default_factory=list, 
        description="List of projects worked on."
    )
    
    certifications: List[Certification] = Field(
        default_factory=list, 
        description="List of certifications obtained."
    )
    
    social_profiles: List[SocialProfile] = Field(
        default_factory=list, 
        description="List of social profiles (e.g., LinkedIn, GitHub)."
    )

    provenance: List[ProvenanceEntry] = Field(
        default_factory=list,
        description="Field-level provenance records for enriched candidate data."
    )
