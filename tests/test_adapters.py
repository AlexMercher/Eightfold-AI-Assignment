import os
import pytest
from pathlib import Path
from app.adapters.router import SourceRouter
from app.adapters.csv_adapter import CsvSourceAdapter

def test_csv_adapter_registration():
    router = SourceRouter()
    from app.adapters.detector import SourceType
    router.register_adapter(SourceType.CSV, CsvSourceAdapter())
    
    # We just want to ensure it registers and routing works mentally
    assert SourceType.CSV in router._registry
    
def test_csv_adapter_processing():
    if not os.path.exists("Master.csv"):
        pytest.skip("Master.csv not found")
        
    adapter = CsvSourceAdapter()
    candidates = adapter.process(Path("Master.csv"))
    
    assert len(candidates) > 0
    assert candidates[0].candidate_id
