from app.models.canonical import Candidate, PersonalInfo, ContactInfo
from app.pipeline.comparison.comparators.name import NameComparator
from app.pipeline.comparison.blocking.engine import BlockingEngine

def test_name_comparator():
    comp = NameComparator("name_comp", "exact", 100)
    
    c1 = Candidate(candidate_id="1", personal_info=PersonalInfo(name="John Doe"))
    c2 = Candidate(candidate_id="2", personal_info=PersonalInfo(name="John Doe"))
    c3 = Candidate(candidate_id="3", personal_info=PersonalInfo(name="Jane Smith"))
    
    res1 = comp.matches(c1, c2)
    assert res1.matched
    assert res1.score == 100
    
    res2 = comp.matches(c1, c3)
    assert not res2.matched

def test_blocking_engine():
    engine = BlockingEngine()
    assert engine.active_strategies is not None
