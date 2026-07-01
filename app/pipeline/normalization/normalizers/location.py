import yaml
import re
from pathlib import Path
from typing import Dict
from ..base import BaseNormalizer, NormalizationResult, ValidationState, load_aliases

class StructuredLocation:
    def __init__(self, city: str = "", state: str = "", country: str = "", is_remote: bool = False):
        self.city = city
        self.state_prov = state
        self.country = country
        self.is_remote = is_remote

class LocationParser:
    @staticmethod
    def parse(raw: str) -> StructuredLocation:
        if not raw:
            return StructuredLocation()
            
        raw = raw.strip()
        is_remote = False
        
        if "remote" in raw.lower():
            is_remote = True
            raw = re.sub(r'(?i)\(?\b(remote|work from home)\b\)?', '', raw).strip(' ,-')
            
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        
        if not parts:
            return StructuredLocation(is_remote=is_remote)
            
        if len(parts) == 1:
            return StructuredLocation(city=parts[0], is_remote=is_remote)
            
        if len(parts) == 2:
            return StructuredLocation(city=parts[0], country=parts[1], is_remote=is_remote)
            
        return StructuredLocation(city=parts[0], state=parts[1], country=parts[-1], is_remote=is_remote)

class LocationNormalizer(BaseNormalizer):
    def __init__(self, config_path: str = "config/normalization/location_aliases.yaml"):
        self.aliases = load_aliases(config_path)
                
    def normalize(self, location_str: str) -> NormalizationResult[str]:
        if not location_str or not location_str.strip():
            return NormalizationResult(location_str, ValidationState.UNPARSEABLE)
            
        parsed = LocationParser.parse(location_str)
        
        state = ValidationState.VALID
        
        if parsed.city:
            lookup = parsed.city.lower()
            if lookup in self.aliases:
                parsed.city = self.aliases[lookup]
            else:
                state = ValidationState.UNKNOWN
                
        # Reconstruct string for Canonical
        parts = []
        if parsed.city: parts.append(parsed.city)
        if parsed.state_prov: parts.append(parsed.state_prov)
        if parsed.country: parts.append(parsed.country)
        
        final_str = ", ".join(parts)
        if parsed.is_remote:
            final_str = f"Remote{', ' + final_str if final_str else ''}"
            
        return NormalizationResult(final_str, state)
