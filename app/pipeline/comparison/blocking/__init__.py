from .base import BaseBlockingStrategy, CandidatePair
from .registry import BlockingRegistry
from .email import EmailBlockingStrategy
from .phone import PhoneBlockingStrategy
from .github import GithubBlockingStrategy
from .linkedin import LinkedinBlockingStrategy
from .company_city import CompanyCityBlockingStrategy
from .name_company import NameCompanyBlockingStrategy
from .name_university import NameUniversityBlockingStrategy
from .engine import BlockingEngine

__all__ = [
    "BaseBlockingStrategy",
    "CandidatePair",
    "BlockingRegistry",
    "EmailBlockingStrategy",
    "PhoneBlockingStrategy",
    "GithubBlockingStrategy",
    "LinkedinBlockingStrategy",
    "CompanyCityBlockingStrategy",
    "NameCompanyBlockingStrategy",
    "NameUniversityBlockingStrategy",
    "BlockingEngine"
]
