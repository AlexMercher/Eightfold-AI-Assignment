import yaml
from pathlib import Path
from .models import MergeResult, ConfidenceResult, ConfidenceLevel

class ConfidenceEngine:
    def __init__(self, config_path: str = "config/resolution/confidence.yaml"):
        self.thresholds = {}
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.thresholds = data.get("thresholds", {})
        
    def evaluate(self, merge_result: MergeResult, cluster_size: int) -> ConfidenceResult:
        # Confidence depends purely on: source_count, conflict_count, etc.
        # It does NOT use similarity score.
        conflict_count = len(merge_result.conflicts)
        
        # We can extract rule-decisions from evidence bundle in the future, 
        # but for now we'll stick to conflicts and source counts.
        
        high = self.thresholds.get("high", {"max_conflicts": 1, "min_sources": 2})
        med = self.thresholds.get("medium", {"max_conflicts": 3, "min_sources": 1})
        
        level = ConfidenceLevel.LOW
        reasoning = "High conflicts or low source agreement."
        
        if conflict_count <= high.get("max_conflicts", 1) and cluster_size >= high.get("min_sources", 2):
            level = ConfidenceLevel.HIGH
            reasoning = "Multi-source corroboration with low conflicts."
        elif conflict_count <= med.get("max_conflicts", 3) and cluster_size >= med.get("min_sources", 1):
            level = ConfidenceLevel.MEDIUM
            reasoning = "Moderate conflicts or single source."
            
        return ConfidenceResult(
            level=level,
            conflict_count=conflict_count,
            source_count=cluster_size,
            reasoning=reasoning
        )
