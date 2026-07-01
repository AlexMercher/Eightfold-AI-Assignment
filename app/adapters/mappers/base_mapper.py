from abc import ABC, abstractmethod
from app.models.canonical import Candidate

class BaseMapper(ABC):
    """Common interface for all source-to-canonical mappers."""
    
    @abstractmethod
    def map_to_canonical(self, source_data) -> Candidate:
        """Converts source-specific data into the Canonical Candidate model."""
        pass
