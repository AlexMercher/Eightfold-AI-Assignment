from typing import Dict, Type
from .base import BaseNormalizer

class NormalizerRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseNormalizer] = {}
        
    def register(self, name: str, normalizer: BaseNormalizer):
        self._registry[name] = normalizer
        
    def get(self, name: str) -> BaseNormalizer:
        if name not in self._registry:
            raise KeyError(f"Normalizer {name} not found in registry.")
        return self._registry[name]
        
    def get_all(self) -> Dict[str, BaseNormalizer]:
        return dict(self._registry)
