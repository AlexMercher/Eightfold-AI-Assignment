import re
from app.models.canonical import PersonalInfo
from ..base import BaseNormalizer, NormalizationResult, ValidationState

class NameNormalizer(BaseNormalizer):
    def normalize(self, personal_info: PersonalInfo) -> NormalizationResult[PersonalInfo]:
        new_info = personal_info.model_copy(deep=True)
        name = new_info.name
        if not name or not name.strip():
            return NormalizationResult(new_info, ValidationState.UNPARSEABLE)
            
        # Trim whitespace
        name = name.strip()
        
        # Collapse repeated whitespace
        name = re.sub(r'\s+', ' ', name)
        
        # Proper capitalization (title case while preserving punctuation)
        # python's .title() breaks on apostrophes (O'Connor -> O'connor), so we use a smarter regex
        def capitalize_word(match):
            word = match.group(0)
            if word.lower() in ["and", "of", "the", "de", "von"]:
                return word.lower()
            return word.capitalize()
            
        name = re.sub(r'[A-Za-z]+', capitalize_word, name)
        
        new_info.name = name
        return NormalizationResult(new_info, ValidationState.VALID)
