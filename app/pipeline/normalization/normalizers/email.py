import re
from app.models.canonical import ContactInfo
from ..base import BaseNormalizer, NormalizationResult, ValidationState

class EmailNormalizer(BaseNormalizer):
    def normalize(self, contact_info: ContactInfo) -> NormalizationResult[ContactInfo]:
        new_info = contact_info.model_copy(deep=True)
        valid_emails = []
        
        # simple email validation regex
        email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        
        state = ValidationState.VALID
        has_unparseable = False
        
        for email in new_info.emails:
            email = email.strip().lower()
            if email_regex.match(email):
                if email not in valid_emails:
                    valid_emails.append(email)
            else:
                has_unparseable = True
                
        new_info.emails = valid_emails
        if has_unparseable and not valid_emails:
            state = ValidationState.UNPARSEABLE
        elif has_unparseable:
            state = ValidationState.UNKNOWN
            
        return NormalizationResult(new_info, state)
