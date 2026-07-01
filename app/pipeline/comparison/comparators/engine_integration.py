import yaml
from pathlib import Path
from .registry import ComparatorRegistry
from .name import NameComparator
from .company import CompanyComparator
from .job_title import JobTitleComparator
from .location import LocationComparator
from .email import EmailComparator
from .phone import PhoneComparator
from .github import GithubComparator
from .linkedin import LinkedinComparator
from .portfolio import PortfolioComparator
from .education import EducationComparator
from .skill import SkillComparator

def load_comparators(config_path: str = "config/comparison/comparators.yaml") -> ComparatorRegistry:
    registry = ComparatorRegistry()
    
    path = Path(config_path)
    if not path.exists():
        # Register defaults if no config
        registry.register("name", NameComparator("name", "rapidfuzz_ratio", 85))
        registry.register("email", EmailComparator("email", "exact", 100))
        return registry
        
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
        
    # Map of names to classes
    class_map = {
        "name": NameComparator,
        "company": CompanyComparator,
        "job_title": JobTitleComparator,
        "location": LocationComparator,
        "email": EmailComparator,
        "phone": PhoneComparator,
        "github": GithubComparator,
        "linkedin": LinkedinComparator,
        "portfolio": PortfolioComparator,
        "education": EducationComparator,
        "skill": SkillComparator
    }
    
    for name, cls in class_map.items():
        if name in data:
            conf = data[name]
            algo = conf.get("algorithm", "exact")
            thresh = conf.get("threshold", 100)
            registry.register(name, cls(name, algo, thresh))
            
    return registry
