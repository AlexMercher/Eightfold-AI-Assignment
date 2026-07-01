import re
import pandas as pd
from ..base import BaseNormalizer, NormalizationResult, ValidationState

class DateNormalizer(BaseNormalizer):
    def normalize(self, date_str: str) -> NormalizationResult[str]:
        if not date_str or not str(date_str).strip():
            return NormalizationResult(date_str, ValidationState.UNPARSEABLE)
            
        date_str = str(date_str).strip()
        
        if date_str.lower() in ["present", "current", "now"]:
            return NormalizationResult("Present", ValidationState.VALID)
            
        # Detect year-only (e.g. 2022)
        if re.match(r'^\d{4}$', date_str):
            return NormalizationResult(date_str, ValidationState.VALID)
            
        try:
            # Parse using pandas to handle many formats gracefully
            dt = pd.to_datetime(date_str)
            # If original string didn't have a day, only format YYYY-MM
            has_day = bool(re.search(r'\b\d{1,2}(st|nd|rd|th|/|-|\s|,)+\d{4}', date_str) or re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', date_str))
            
            if not has_day:
                formatted = dt.strftime('%Y-%m')
            else:
                formatted = dt.strftime('%Y-%m-%d')
                
            return NormalizationResult(formatted, ValidationState.VALID)
        except Exception:
            return NormalizationResult(date_str, ValidationState.UNPARSEABLE)
