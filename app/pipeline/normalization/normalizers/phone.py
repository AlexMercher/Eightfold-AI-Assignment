import phonenumbers
from app.models.canonical import ContactInfo
from ..base import BaseNormalizer, NormalizationResult, ValidationState

class PhoneNormalizer(BaseNormalizer):
    def __init__(self, default_region: str = "US"):
        self.default_region = default_region
        
    def normalize(self, contact_info: ContactInfo) -> NormalizationResult[ContactInfo]:
        new_info = contact_info.model_copy(deep=True)
        valid_phones = []
        has_unparseable = False
        state = ValidationState.VALID
        
        for phone in new_info.phone_numbers:
            try:
                parsed = phonenumbers.parse(phone, self.default_region)
                if phonenumbers.is_valid_number(parsed):
                    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                    if formatted not in valid_phones:
                        valid_phones.append(formatted)
                else:
                    has_unparseable = True
            except phonenumbers.NumberParseException:
                has_unparseable = True
                
        new_info.phone_numbers = valid_phones
        
        if has_unparseable and not valid_phones:
            state = ValidationState.UNPARSEABLE
        elif has_unparseable:
            state = ValidationState.UNKNOWN
            
        return NormalizationResult(new_info, state)
