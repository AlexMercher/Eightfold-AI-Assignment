from typing import List
from app.models.canonical import Candidate
from .base import BaseBlockingStrategy

class LinkedinBlockingStrategy(BaseBlockingStrategy):
    def generate_keys(self, candidate: Candidate) -> List[str]:
        keys = []
        if candidate.social_profiles:
            for profile in candidate.social_profiles:
                if profile.platform.lower() == "linkedin" and profile.url:
                    keys.append(f"{self.name}:{profile.url.strip().lower()}")
        return keys
