"""
Regression tests for INVALID cluster enforcement in ResolutionCoordinator.

Verifies:
- VALID clusters still merge (single merged candidate, merged_ ID)
- WARNING clusters still merge (single merged candidate, merged_ ID)
- INVALID clusters NEVER merge (one output per source candidate)
- Original candidate IDs are preserved for INVALID clusters
- Provenance is still generated for INVALID clusters
- Confidence still executes for INVALID clusters
- Projection still works for INVALID clusters
- ClusterStatus is correctly reported in all cluster types
"""
import pytest
from unittest.mock import patch

from app.models.canonical import Candidate, PersonalInfo, ContactInfo, ProfessionalInfo
from app.pipeline.comparison.blocking.base import CandidatePair
from app.pipeline.identity_resolution.models import (
    IdentityResolutionResult, DecisionType, DecisionResult,
    DecisionExplanation, DecisionSource,
)
from app.pipeline.resolution.coordinator import ResolutionCoordinator
from app.pipeline.resolution.models import (
    ClusterStatus, ValidatedCluster, MergeResult,
)
from app.pipeline.resolution.merge_engine import MergeEngine
from app.pipeline.resolution.conflict_resolver import ConflictResolver
from app.pipeline.comparison.blocking.base import CandidatePair


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_candidate(cid: str, name: str = None) -> Candidate:
    return Candidate(
        candidate_id=cid,
        personal_info=PersonalInfo(name=name or cid),
    )


def _make_match(a_id: str, b_id: str) -> IdentityResolutionResult:
    pair = CandidatePair(
        candidate_a_id=a_id,
        candidate_b_id=b_id,
        blocking_keys_that_generated_this_pair=[],
    )
    return IdentityResolutionResult(
        candidate_pair=pair,
        decision=DecisionType.MATCH,
        rule_result=None,
        similarity_result=None,
        decision_result=DecisionResult(
            decision=DecisionType.MATCH,
            explanation=DecisionExplanation(
                final_decision=DecisionType.MATCH,
                decision_source=DecisionSource.RULE,
                message="",
            ),
        ),
    )


def _coordinator() -> ResolutionCoordinator:
    return ResolutionCoordinator()


# ─── VALID cluster tests ──────────────────────────────────────────────────────

def test_valid_cluster_merges_to_single_output():
    """Two candidates that MATCH → exactly one merged output."""
    coord = _coordinator()
    c1 = _make_candidate("cand_1", "Alice Smith")
    c2 = _make_candidate("cand_2", "Alice Smith")
    results = coord.coordinate([c1, c2], [_make_match("cand_1", "cand_2")])
    assert len(results) == 1
    proj, cluster = results[0]
    assert cluster.status == ClusterStatus.VALID


def test_valid_cluster_produces_merged_id():
    """Merged output for VALID cluster carries a merged_ prefixed ID."""
    coord = _coordinator()
    c1 = _make_candidate("cand_1", "Alice Smith")
    c2 = _make_candidate("cand_2", "Alice Smith")
    results = coord.coordinate([c1, c2], [_make_match("cand_1", "cand_2")])
    proj, cluster = results[0]
    candidate_id = proj.dictionary_view.get("candidate_id", "")
    assert candidate_id.startswith("merged_"), (
        f"VALID cluster must produce a merged_ ID, got: {candidate_id!r}"
    )


# ─── WARNING cluster tests ────────────────────────────────────────────────────

def test_warning_cluster_merges_to_single_output():
    """A WARNING cluster (e.g. minor contradictions) still merges into one output."""
    coord = _coordinator()
    c1 = _make_candidate("cand_w1", "Bob Jones")
    c2 = _make_candidate("cand_w2", "Bob Jones")

    # Force the validator to return WARNING by patching
    from app.pipeline.resolution.models import ValidatedCluster
    warning_cluster = ValidatedCluster(
        candidates=[c1, c2], edges=[], status=ClusterStatus.WARNING, contradictions=[]
    )
    with patch.object(coord.validator, "validate", return_value=warning_cluster):
        results = coord.coordinate([c1, c2], [_make_match("cand_w1", "cand_w2")])

    assert len(results) == 1
    _, cluster = results[0]
    assert cluster.status == ClusterStatus.WARNING


def test_warning_cluster_produces_merged_id():
    """WARNING cluster still uses MergeEngine, so carries a merged_ ID."""
    coord = _coordinator()
    c1 = _make_candidate("cand_w1", "Bob Jones")
    c2 = _make_candidate("cand_w2", "Bob Jones")

    from app.pipeline.resolution.models import ValidatedCluster
    warning_cluster = ValidatedCluster(
        candidates=[c1, c2], edges=[], status=ClusterStatus.WARNING, contradictions=[]
    )
    with patch.object(coord.validator, "validate", return_value=warning_cluster):
        results = coord.coordinate([c1, c2], [_make_match("cand_w1", "cand_w2")])

    proj, _ = results[0]
    candidate_id = proj.dictionary_view.get("candidate_id", "")
    assert candidate_id.startswith("merged_"), (
        f"WARNING cluster must still produce a merged_ ID, got: {candidate_id!r}"
    )


# ─── INVALID cluster tests ────────────────────────────────────────────────────

def test_invalid_cluster_never_merges():
    """An INVALID cluster must produce one output per source candidate, never one merged output."""
    coord = _coordinator()
    c1 = _make_candidate("cand_x", "Himanshu Ranjan")
    c2 = _make_candidate("cand_y", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["Contradictory email addresses"],
    )
    with patch.object(coord.validator, "validate", return_value=invalid_cluster):
        results = coord.coordinate([c1, c2], [_make_match("cand_x", "cand_y")])

    # Must produce 2 independent outputs, not 1 merged one
    assert len(results) == 2, (
        f"INVALID cluster must produce 2 independent outputs, got {len(results)}"
    )


def test_invalid_cluster_preserves_original_ids():
    """IDs in INVALID cluster output must match original candidate IDs exactly."""
    coord = _coordinator()
    c1 = _make_candidate("himanshu_01", "Himanshu Ranjan")
    c2 = _make_candidate("madhusudan_02", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["Contradictory email addresses"],
    )
    with patch.object(coord.validator, "validate", return_value=invalid_cluster):
        results = coord.coordinate([c1, c2], [_make_match("himanshu_01", "madhusudan_02")])

    output_ids = {r[0].dictionary_view.get("candidate_id") for r in results}
    assert "himanshu_01" in output_ids, "Original ID himanshu_01 must be preserved"
    assert "madhusudan_02" in output_ids, "Original ID madhusudan_02 must be preserved"


def test_invalid_cluster_no_merged_prefix():
    """No output from an INVALID cluster should carry a merged_ prefix."""
    coord = _coordinator()
    c1 = _make_candidate("cand_x", "Himanshu Ranjan")
    c2 = _make_candidate("cand_y", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["Contradictory phones"],
    )
    with patch.object(coord.validator, "validate", return_value=invalid_cluster):
        results = coord.coordinate([c1, c2], [_make_match("cand_x", "cand_y")])

    for proj, _ in results:
        cid = proj.dictionary_view.get("candidate_id", "")
        assert not cid.startswith("merged_"), (
            f"INVALID cluster must NOT produce a merged_ ID, got: {cid!r}"
        )


def test_invalid_cluster_provenance_generated():
    """Each standalone output from an INVALID cluster must carry provenance."""
    coord = _coordinator()
    c1 = _make_candidate("cand_x", "Himanshu Ranjan")
    c2 = _make_candidate("cand_y", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["Contradictory phones"],
    )
    # Use default projection config which does NOT include provenance in the
    # dictionary_view, so we test provenance via the MergeResult directly.
    wrap_calls = []
    original_wrap = coord.merge_engine.wrap_single
    def capturing_wrap(candidate):
        result = original_wrap(candidate)
        wrap_calls.append(result)
        return result

    with patch.object(coord.validator, "validate", return_value=invalid_cluster), \
         patch.object(coord.merge_engine, "wrap_single", side_effect=capturing_wrap):
        coord.coordinate([c1, c2], [_make_match("cand_x", "cand_y")])

    assert len(wrap_calls) == 2, "wrap_single must be called once per source candidate"
    for mr in wrap_calls:
        assert mr.provenance, "MergeResult provenance must not be empty for INVALID clusters"
        for prov in mr.provenance.values():
            assert prov.source_candidates, "Provenance must list source candidate IDs"


def test_invalid_cluster_confidence_executes():
    """ConfidenceEngine must still execute for each INVALID cluster output."""
    coord = _coordinator()
    c1 = _make_candidate("cand_x", "Himanshu Ranjan")
    c2 = _make_candidate("cand_y", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["contradiction"],
    )

    confidence_calls = []
    original_evaluate = coord.confidence_engine.evaluate
    def capturing_evaluate(merge_result, cluster_size):
        result = original_evaluate(merge_result, cluster_size)
        confidence_calls.append(result)
        return result

    with patch.object(coord.validator, "validate", return_value=invalid_cluster), \
         patch.object(coord.confidence_engine, "evaluate", side_effect=capturing_evaluate):
        coord.coordinate([c1, c2], [_make_match("cand_x", "cand_y")])

    assert len(confidence_calls) == 2, "ConfidenceEngine must run for every INVALID candidate"


def test_invalid_cluster_projection_executes():
    """ProjectionEngine must still execute for each INVALID cluster output."""
    coord = _coordinator()
    c1 = _make_candidate("cand_x", "Himanshu Ranjan")
    c2 = _make_candidate("cand_y", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["contradiction"],
    )

    projection_calls = []
    original_project = coord.projection_engine.project
    def capturing_project(merge_result, confidence_result=None):
        result = original_project(merge_result, confidence_result)
        projection_calls.append(result)
        return result

    with patch.object(coord.validator, "validate", return_value=invalid_cluster), \
         patch.object(coord.projection_engine, "project", side_effect=capturing_project):
        coord.coordinate([c1, c2], [_make_match("cand_x", "cand_y")])

    assert len(projection_calls) == 2, "ProjectionEngine must run for every INVALID candidate"


def test_invalid_cluster_status_preserved_in_output():
    """The ValidatedCluster bound to each INVALID projection must still report INVALID."""
    coord = _coordinator()
    c1 = _make_candidate("cand_x", "Himanshu Ranjan")
    c2 = _make_candidate("cand_y", "Madhusudan G")

    from app.pipeline.resolution.models import ValidatedCluster
    invalid_cluster = ValidatedCluster(
        candidates=[c1, c2],
        edges=[],
        status=ClusterStatus.INVALID,
        contradictions=["contradiction"],
    )
    with patch.object(coord.validator, "validate", return_value=invalid_cluster):
        results = coord.coordinate([c1, c2], [_make_match("cand_x", "cand_y")])

    for _, cluster in results:
        assert cluster.status == ClusterStatus.INVALID


# ─── MergeEngine unit tests ───────────────────────────────────────────────────

def test_wrap_single_preserves_candidate_id():
    engine = MergeEngine(ConflictResolver())
    cand = _make_candidate("original_id", "Test Person")
    result = engine.wrap_single(cand)
    assert result.candidate.candidate_id == "original_id"


def test_wrap_single_no_merged_prefix():
    engine = MergeEngine(ConflictResolver())
    cand = _make_candidate("original_id", "Test Person")
    result = engine.wrap_single(cand)
    assert not result.candidate.candidate_id.startswith("merged_")


def test_wrap_single_no_conflicts():
    engine = MergeEngine(ConflictResolver())
    cand = _make_candidate("original_id")
    result = engine.wrap_single(cand)
    assert result.conflicts == {}


def test_wrap_single_provenance_present():
    engine = MergeEngine(ConflictResolver())
    cand = _make_candidate("original_id")
    result = engine.wrap_single(cand)
    assert result.provenance
    source_ids = list(result.provenance.values())[0].source_candidates
    assert "original_id" in source_ids


def test_wrap_single_identity_preserving_path_recorded():
    engine = MergeEngine(ConflictResolver())
    cand = _make_candidate("original_id")
    result = engine.wrap_single(cand)
    for prov in result.provenance.values():
        assert "identity-preserving" in prov.merge_decision_path.lower()
