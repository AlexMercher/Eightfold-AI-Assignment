from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from app.models.canonical import Candidate

class BaseSourceAdapter(ABC):
    """Common interface for all source adapters."""
    
    @abstractmethod
    def process(self, source: Path) -> List[Candidate]:
        """Reads a source and returns a list of Canonical Candidates."""
        pass
