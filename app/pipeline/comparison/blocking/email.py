from typing import List
from app.models.canonical import Candidate
from .base import BaseBlockingStrategy

class EmailBlockingStrategy(BaseBlockingStrategy):
    def generate_keys(self, candidate: Candidate) -> List[str]:
        keys = []
        if candidate.contact_info:
            for email in candidate.contact_info.emails:
                if email.strip():
                    keys.append(f"{self.name}:{email.strip().lower()}")
        return keys
