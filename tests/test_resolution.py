import pytest
from app.models.canonical import Candidate, PersonalInfo
from app.pipeline.comparison.blocking.base import CandidatePair
from app.pipeline.identity_resolution.models import IdentityResolutionResult, DecisionType, DecisionResult, DecisionExplanation, DecisionSource
from app.pipeline.resolution.coordinator import ResolutionCoordinator

def test_coordinator_builds_graph_correctly():
    coord = ResolutionCoordinator()
    
    c1 = Candidate(candidate_id="A", personal_info=PersonalInfo(name="Alice"))
    c2 = Candidate(candidate_id="B", personal_info=PersonalInfo(name="Alice"))
    c3 = Candidate(candidate_id="C", personal_info=PersonalInfo(name="Alice"))
    
    # A matches B, B matches C
    pair_ab = CandidatePair(candidate_a_id="A", candidate_b_id="B", blocking_keys_that_generated_this_pair=[])
    pair_bc = CandidatePair(candidate_a_id="B", candidate_b_id="C", blocking_keys_that_generated_this_pair=[])
    
    res_ab = IdentityResolutionResult(
        candidate_pair=pair_ab, decision=DecisionType.MATCH, rule_result=None, similarity_result=None,
        decision_result=DecisionResult(decision=DecisionType.MATCH, explanation=DecisionExplanation(final_decision=DecisionType.MATCH, decision_source=DecisionSource.RULE, message=""))
    )
    res_bc = IdentityResolutionResult(
        candidate_pair=pair_bc, decision=DecisionType.MATCH, rule_result=None, similarity_result=None,
        decision_result=DecisionResult(decision=DecisionType.MATCH, explanation=DecisionExplanation(final_decision=DecisionType.MATCH, decision_source=DecisionSource.RULE, message=""))
    )
    
    results = coord.coordinate([c1, c2, c3], [res_ab, res_bc])
    assert len(results) == 1
    proj, cluster = results[0]
    assert len(cluster.candidates) == 3

def test_conflict_resolver_priority():
    from app.pipeline.resolution.conflict_resolver import ConflictResolver
    resolver = ConflictResolver()
    resolver.source_priorities = ["source_a", "source_b"]
    
    res = resolver.resolve_scalar(["val1", "val2"], ["source_b", "source_a"])
    assert res.winning_value == "val2"
    
def test_conflict_resolver_frequency():
    from app.pipeline.resolution.conflict_resolver import ConflictResolver
    resolver = ConflictResolver()
    res = resolver.resolve_scalar(["val1", "val2", "val1"], ["s1", "s2", "s3"])
    assert res.winning_value == "val1"
