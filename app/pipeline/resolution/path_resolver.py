from typing import Any, List, Union
from pydantic import BaseModel
import re

class _Missing:
    pass

MISSING = _Missing()

class PathResolver:
    """
    A purely deterministic, strictly read-only path resolver.
    Only supports exact dot notation (e.g. `personal_info.name`) 
    and exact list indexing (e.g. `emails[0]`).
    Does NOT support query languages, slices, or evaluation.
    """
    
    def __init__(self):
        # Match tokens like `emails` or `[0]`
        self.token_pattern = re.compile(r'([^[\]]+)|\[(\d+)\]')

    def resolve(self, obj: Any, path: str) -> Any:
        if not path:
            return MISSING
            
        # Split by dot first
        segments = path.split('.')
        
        current = obj
        for segment in segments:
            # Parse `field[0][1]` inside segment
            tokens = self.token_pattern.findall(segment)
            for key, index_str in tokens:
                if key:
                    current = self._resolve_key(current, key)
                elif index_str:
                    current = self._resolve_index(current, int(index_str))
                
                if current is MISSING:
                    return MISSING
        
        return current

    def _resolve_key(self, obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, MISSING)
        elif isinstance(obj, BaseModel):
            if hasattr(obj, key):
                return getattr(obj, key)
            return MISSING
        else:
            if hasattr(obj, key) and not key.startswith('_'):
                return getattr(obj, key)
            return MISSING

    def _resolve_index(self, obj: Any, index: int) -> Any:
        if isinstance(obj, list) or isinstance(obj, tuple):
            if 0 <= index < len(obj):
                return obj[index]
        return MISSING
