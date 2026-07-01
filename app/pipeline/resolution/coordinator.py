from typing import List, Tuple
from app.models.canonical import Candidate
from app.pipeline.identity_resolution.models import IdentityResolutionResult
from .models import ProjectionResult, ValidatedCluster
from .graph import CandidateGraph
from .validator import ClusterValidator
from .conflict_resolver import ConflictResolver
from .merge_engine import MergeEngine
from .confidence_engine import ConfidenceEngine
from .projection_engine import ProjectionEngine

class ResolutionCoordinator:
    def __init__(self, projection_config_path: str = "config/projection/default.yaml"):
        self.graph = CandidateGraph()
        self.validator = ClusterValidator()
        self.conflict_resolver = ConflictResolver()
        self.merge_engine = MergeEngine(self.conflict_resolver)
        self.confidence_engine = ConfidenceEngine()
        self.projection_engine = ProjectionEngine(projection_config_path)
        
    def coordinate(self, candidates: List[Candidate], resolutions: List[IdentityResolutionResult]) -> List[Tuple[ProjectionResult, ValidatedCluster]]:
        """
        Coordinates the entire Final Resolution pipeline without performing merges directly.
        Returns a list of tuples containing the final projection and the annotated cluster.
        """
        results = []
        
        # 1. Build a fresh Graph & Extract Components (fresh graph per call for statelessness)
        graph = CandidateGraph()
        graph.build(candidates, resolutions)
        components = graph.get_connected_components()
        
        for comp_cands, comp_edges in components:
            # 2. Validate Cluster (detect contradictions)
            validated_cluster = self.validator.validate(comp_cands, comp_edges)
            
            if validated_cluster.status == "INVALID" or getattr(validated_cluster.status, "value", None) == "INVALID":
                # Do not merge contradictory clusters. Emit independent profiles,
                # preserving original candidate IDs.
                for c in comp_cands:
                    merge_result = self.merge_engine.wrap_single(c)
                    confidence_result = self.confidence_engine.evaluate(merge_result, 1)
                    projection = self.projection_engine.project(merge_result, confidence_result)
                    # Bind projection to the ORIGINAL cluster object to preserve structural graph knowledge
                    results.append((projection, validated_cluster))
            else:
                # 3. Merge Engine (resolves conflicts and generates field-level provenance)
                merge_result = self.merge_engine.merge(validated_cluster)
                
                # 4. Compute Confidence
                confidence_result = self.confidence_engine.evaluate(merge_result, len(comp_cands))
                
                # 5. Project to dynamic schema
                projection = self.projection_engine.project(merge_result, confidence_result)
                
                results.append((projection, validated_cluster))
            
        return results
