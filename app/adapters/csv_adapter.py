import pandas as pd
from pathlib import Path
from typing import List

from app.models.canonical import Candidate
from .base import BaseSourceAdapter
from .mappers.csv_mapper import CsvMapper

class CsvSourceAdapter(BaseSourceAdapter):
    """Adapter for reading Candidate CSV files and mapping to Canonical."""
    
    def __init__(self):
        self.mapper = CsvMapper()
        
    def process(self, source: Path) -> List[Candidate]:
        if not source.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")
            
        try:
            # Load CSV and treat all columns as strings by default to prevent type warnings
            df = pd.read_csv(source, dtype=str)
            # Replace NaNs with empty strings safely
            df = df.fillna("")
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {source}")
        except Exception as e:
            raise ValueError(f"Failed to parse CSV {source}: {e}")
            
        candidates = []
        for _, row in df.iterrows():
            try:
                candidate = self.mapper.map_to_canonical(row)
                candidates.append(candidate)
            except Exception as e:
                # We could log this and continue, but fail fast is safer for architecture validation
                raise ValueError(f"Failed to map CSV row to Candidate: {e}")
                
        return candidates
