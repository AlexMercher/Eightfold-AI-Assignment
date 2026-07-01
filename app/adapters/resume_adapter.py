from pathlib import Path
from typing import List

from app.models.canonical import Candidate
from .base import BaseSourceAdapter
from .mappers.resume_mapper import ResumeMapper

class ResumeSourceAdapter(BaseSourceAdapter):
    """Adapter for processing PDF Resumes via the ExtractionPipeline and mapping to Canonical."""
    
    def __init__(self):
        self.mapper = ResumeMapper()
        self.pipeline = None
        
    def _get_pipeline(self):
        if self.pipeline is None:
            from app.core.pipeline import ExtractionPipeline
            self.pipeline = ExtractionPipeline()
        return self.pipeline
        
    def process(self, source: Path) -> List[Candidate]:
        if not source.exists():
            raise FileNotFoundError(f"Resume file not found: {source}")
            
        try:
            # We bypass security for internal adapter testing if needed, but run is standard
            result = self._get_pipeline().run(file_path=source, skip_security=True)
        except Exception as e:
            raise ValueError(f"ExtractionPipeline failed for {source}: {e}")
            
        schema = result.get("schema")
        if not schema:
            raise ValueError(f"No ExtractedResumeSchema returned for {source}")
            
        # Map the single extracted resume to a canonical candidate
        try:
            candidate = self.mapper.map_to_canonical(schema)
        except Exception as e:
            raise ValueError(f"Failed to map resume extraction to Candidate: {e}")
            
        return [candidate]
