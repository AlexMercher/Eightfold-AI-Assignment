from pathlib import Path
from typing import List, Dict

from app.models.canonical import Candidate
from .base import BaseSourceAdapter
from .detector import SourceTypeDetector, SourceType

class SourceRouter:
    """Routes files to their appropriate adapter based on detected source type."""
    
    def __init__(self):
        self._registry: Dict[SourceType, BaseSourceAdapter] = {}
        
    def register_adapter(self, source_type: SourceType, adapter: BaseSourceAdapter):
        """Registers a new adapter for a specific source type."""
        self._registry[source_type] = adapter
        
    def process(self, source: Path) -> List[Candidate]:
        """Detects source type and delegates processing to the registered adapter."""
        source_type = SourceTypeDetector.detect(source)
        
        if source_type == SourceType.UNKNOWN:
            raise ValueError(f"Unsupported or unknown file format for: {source}")
            
        adapter = self._registry.get(source_type)
        if not adapter:
            raise NotImplementedError(f"No adapter registered for source type: {source_type.value}")
            
        return adapter.process(source)
