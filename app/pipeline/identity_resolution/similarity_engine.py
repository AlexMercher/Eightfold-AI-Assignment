import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from .models import EvidenceBundle, SimilarityResult, SimilarityExplanation

class SimilarityEngine:
    def __init__(self, config_path: str = "config/identity_resolution/weights.yaml"):
        self.weights: Dict[str, int] = {}
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.weights = data.get("weights", {})
        
    def calculate(self, evidence: EvidenceBundle) -> SimilarityResult:
        total_weight = 0
        total_score_sum = 0
        
        field_scores: Dict[str, int] = {}
        weighted_breakdown: Dict[str, int] = {}
        contributing = []
        ignored = []
        
        for comp_name, res in evidence.comparison_results.items():
            weight = self.weights.get(comp_name, 0)
            if weight == 0:
                continue
                
            is_missing = getattr(res, 'missing_data', False)
            
            if is_missing:
                ignored.append(comp_name)
                continue
                
            contributing.append(comp_name)
            total_weight += weight
            field_scores[comp_name] = res.score
            weighted_contribution = res.score * weight
            total_score_sum += weighted_contribution
            weighted_breakdown[comp_name] = weighted_contribution
            
        overall_score = (total_score_sum // total_weight) if total_weight > 0 else 0
        
        expl = SimilarityExplanation(
            contributing_fields=contributing,
            ignored_fields=ignored,
            weighted_score_breakdown=weighted_breakdown
        )
        
        return SimilarityResult(
            overall_score=overall_score,
            field_scores=field_scores,
            explanation=expl
        )
