from typing import Dict
from .base import BaseBlockingStrategy
import threading

class BlockingRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseBlockingStrategy] = {}
        self._lock = threading.RLock()
        
    def register(self, name: str, strategy: BaseBlockingStrategy):
        with self._lock:
            self._registry[name] = strategy
            
    def get(self, name: str) -> BaseBlockingStrategy:
        with self._lock:
            if name not in self._registry:
                raise KeyError(f"Blocking strategy '{name}' not found in registry.")
            return self._registry[name]
