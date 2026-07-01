from app.models.canonical import Candidate, PersonalInfo
from app.pipeline.normalization.engine import NormalizationEngine

def test_normalization_engine():
    engine = NormalizationEngine()
    
    # Test Name normalization
    c = Candidate(candidate_id="1", personal_info=PersonalInfo(name="   john   DOE "))
    c = engine.normalize(c)
    
    assert c.personal_info.name == "John Doe"
