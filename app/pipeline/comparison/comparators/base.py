from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel

class ComparisonResult(BaseModel):
    matched: bool
    score: int
    comparator_name: str
    algorithm_used: str
    missing_data: bool = False

class BaseComparator(ABC):
    def __init__(self, name: str, algorithm: str, threshold: int = 100):
        self.name = name
        self.algorithm = algorithm
        self.threshold = threshold
        
    @abstractmethod
    def matches(self, candidate_a: Any, candidate_b: Any) -> ComparisonResult:
        """
        Takes two Candidates (or specific sub-models if the engine delegates it so)
        and compares them using the configured algorithm and threshold.
        Returns a ComparisonResult.
        """
        pass
