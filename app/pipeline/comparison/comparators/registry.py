from typing import Dict
from .base import BaseComparator
import threading

class ComparatorRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseComparator] = {}
        self._lock = threading.RLock()
        
    def register(self, name: str, comparator: BaseComparator):
        with self._lock:
            self._registry[name] = comparator
            
    def get(self, name: str) -> BaseComparator:
        with self._lock:
            if name not in self._registry:
                raise KeyError(f"Comparator '{name}' not found in registry.")
            return self._registry[name]
