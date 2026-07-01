from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from app.models.canonical import Candidate

class CandidatePair(BaseModel):
    candidate_a_id: str
    candidate_b_id: str
    blocking_keys_that_generated_this_pair: List[str]
    
    def __hash__(self):
        # Sort IDs to ensure (A, B) is treated same as (B, A) in sets
        a, b = sorted([self.candidate_a_id, self.candidate_b_id])
        return hash((a, b))
        
    def __eq__(self, other):
        if not isinstance(other, CandidatePair):
            return False
        a1, b1 = sorted([self.candidate_a_id, self.candidate_b_id])
        a2, b2 = sorted([other.candidate_a_id, other.candidate_b_id])
        return a1 == a2 and b1 == b2

class BaseBlockingStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    def generate_keys(self, candidate: Candidate) -> List[str]:
        """
        Generates deterministic blocking keys for a candidate.
        Format typically looks like 'strategy_name:key_value'.
        """
        pass
