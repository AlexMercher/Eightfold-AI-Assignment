from typing import Any, List, Optional
from pydantic import BaseModel, Field

class PersonalInfo(BaseModel):
    name: str = Field(default="", description="The candidate's full name.")
    location: Optional[str] = Field(default=None, description="The candidate's primary location.")

class ContactInfo(BaseModel):
    emails: List[str] = Field(default_factory=list, description="List of email addresses.")
    phone_numbers: List[str] = Field(default_factory=list, description="List of phone numbers.")
    website: Optional[str] = Field(default=None, description="Personal website URL.")

class Skill(BaseModel):
    name: str = Field(..., description="The raw skill name.")
    category: Optional[str] = Field(default=None, description="Category of the skill.")
    normalized_name: Optional[str] = Field(default=None, description="Normalized skill name.")

class Experience(BaseModel):
    company: str = Field(..., description="Name of the company.")
    title: str = Field(..., description="Job title.")
    start_date: Optional[str] = Field(default=None, description="Start date of employment.")
    end_date: Optional[str] = Field(default=None, description="End date of employment.")
    description: Optional[str] = Field(default=None, description="Description of responsibilities and achievements.")

class ProfessionalInfo(BaseModel):
    headline: Optional[str] = Field(default=None, description="Candidate's professional headline or bio.")
    current_company: Optional[str] = Field(default=None, description="Current or most recent company.")
    current_title: Optional[str] = Field(default=None, description="Current or most recent job title.")
    total_experience_years: Optional[float] = Field(default=None, description="Total years of professional experience.")
    experiences: List[Experience] = Field(default_factory=list, description="Employment history.")
    skills: List[Skill] = Field(default_factory=list, description="List of skills.")

class ProvenanceEntry(BaseModel):
    field: str
    source: str
    method: str
    value: Any

class Education(BaseModel):
    institution: str = Field(..., description="Name of the educational institution.")
    degree: str = Field(..., description="Degree obtained or pursued.")
    field_of_study: Optional[str] = Field(default=None, description="Major or field of study.")
    graduation_year: Optional[str] = Field(default=None, description="Year of graduation.")

class Project(BaseModel):
    name: str = Field(..., description="Name of the project.")
    description: Optional[str] = Field(default=None, description="Description of the project.")
    technologies: List[str] = Field(default_factory=list, description="List of technologies used.")

class Certification(BaseModel):
    name: str = Field(..., description="Name of the certification.")
    issuing_organization: str = Field(..., description="Organization that issued the certification.")
    issue_date: Optional[str] = Field(default=None, description="Date the certification was issued.")

class SocialProfile(BaseModel):
    platform: str = Field(..., description="Name of the platform (e.g., LinkedIn, GitHub).")
    url: str = Field(..., description="URL to the profile.")
