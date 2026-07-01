from typing import List
from app.models.canonical import Candidate
from .base import BaseBlockingStrategy

class PhoneBlockingStrategy(BaseBlockingStrategy):
    def generate_keys(self, candidate: Candidate) -> List[str]:
        keys = []
        if candidate.contact_info:
            for phone in candidate.contact_info.phone_numbers:
                if phone.strip():
                    keys.append(f"{self.name}:{phone.strip()}")
        return keys
