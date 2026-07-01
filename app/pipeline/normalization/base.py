from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar

class ValidationState(str, Enum):
    VALID = "VALID"
    UNKNOWN = "UNKNOWN"
    UNPARSEABLE = "UNPARSEABLE"

T = TypeVar("T")

class NormalizationResult(Generic[T]):
    def __init__(self, data: T, state: ValidationState):
        self.data = data
        self.state = state

class BaseNormalizer(ABC):
    """
    Common interface for all normalizers. 
    Each normalizer operates on a specific field/sub-object of the Canonical Candidate.
    It returns a NormalizationResult containing a new, immutable normalized object 
    and its validation state.
    """
    @abstractmethod
    def normalize(self, source_data: Any) -> NormalizationResult[Any]:
        pass

def load_aliases(config_path: str) -> dict:
    """Helper to load canonical mappings from YAML configuration."""
    from pathlib import Path
    import yaml
    
    aliases = {}
    path = Path(config_path)
    if not path.exists():
        return aliases
        
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
        
    for canonical, aliases_list in data.items():
        aliases[canonical.lower()] = canonical
        for alias in aliases_list:
            aliases[alias.lower()] = canonical
            
    return aliases
