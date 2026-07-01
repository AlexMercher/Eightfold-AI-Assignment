from enum import Enum

class DegreeLevel(str, Enum):
    BACHELORS = "BACHELORS"
    MASTERS = "MASTERS"
    PHD = "PHD"
    ASSOCIATES = "ASSOCIATES"
    HIGH_SCHOOL = "HIGH_SCHOOL"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class SourceType(str, Enum):
    RESUME = "RESUME"
    LINKEDIN = "LINKEDIN"
    GITHUB = "GITHUB"
    ATS = "ATS"
    OTHER = "OTHER"
