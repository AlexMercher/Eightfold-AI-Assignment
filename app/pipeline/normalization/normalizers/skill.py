import yaml
from typing import List, Dict
from app.models.canonical import Skill
from ..base import BaseNormalizer, NormalizationResult, ValidationState, load_aliases

class SkillNormalizer(BaseNormalizer):
    def __init__(self, config_path: str = "config/normalization/skills_aliases.yaml"):
        self.aliases: Dict[str, str] = load_aliases(config_path)
                
    def normalize(self, skills: List[Skill]) -> NormalizationResult[List[Skill]]:
        state = ValidationState.VALID
        seen = set()
        unique_skills = []
        
        for skill in skills:
            if not skill.name or not skill.name.strip():
                continue
                
            raw = skill.name.strip()
            lookup = raw.lower()
            
            if lookup in self.aliases:
                skill.normalized_name = self.aliases[lookup]
            else:
                skill.normalized_name = raw
                state = ValidationState.UNKNOWN
                
            # Prevent duplicates based on normalized name
            if skill.normalized_name.lower() not in seen:
                seen.add(skill.normalized_name.lower())
                unique_skills.append(skill)
                
        return NormalizationResult(unique_skills, state)
