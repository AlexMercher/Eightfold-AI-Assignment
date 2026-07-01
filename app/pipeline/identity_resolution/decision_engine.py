import yaml
from pathlib import Path
from .models import RuleResult, SimilarityResult, DecisionResult, DecisionType, DecisionSource, DecisionExplanation

class DecisionEngine:
    def __init__(self, config_path: str = "config/identity_resolution/thresholds.yaml"):
        self.thresholds = {}
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.thresholds = data.get("thresholds", {})
        
    def decide(self, rule_result: RuleResult, sim_result: SimilarityResult) -> DecisionResult:
        # 1. Check if Rule Engine produced a terminating decision
        if rule_result.terminating and rule_result.decision:
            expl = DecisionExplanation(
                final_decision=rule_result.decision,
                decision_source=DecisionSource.RULE,
                message=f"Terminated by hard rule: {rule_result.rule_id}"
            )
            return DecisionResult(decision=rule_result.decision, explanation=expl)
            
        # 2. Check Similarity Engine Thresholds
        if not sim_result:
            expl = DecisionExplanation(
                final_decision=DecisionType.NO_MATCH,
                decision_source=DecisionSource.SIMILARITY,
                message="No similarity result provided and no terminating rule."
            )
            return DecisionResult(decision=DecisionType.NO_MATCH, explanation=expl)
            
        score = sim_result.overall_score
        match_thresh = self.thresholds.get("match", 85)
        review_thresh = self.thresholds.get("review", 75)
        
        if score >= match_thresh:
            expl = DecisionExplanation(
                final_decision=DecisionType.MATCH,
                decision_source=DecisionSource.THRESHOLD,
                message=f"Similarity score {score} >= {match_thresh} (MATCH threshold)"
            )
            return DecisionResult(decision=DecisionType.MATCH, explanation=expl)
            
        elif score >= review_thresh:
            expl = DecisionExplanation(
                final_decision=DecisionType.REVIEW,
                decision_source=DecisionSource.THRESHOLD,
                message=f"Similarity score {score} >= {review_thresh} (REVIEW threshold)"
            )
            return DecisionResult(decision=DecisionType.REVIEW, explanation=expl)
            
        else:
            expl = DecisionExplanation(
                final_decision=DecisionType.NO_MATCH,
                decision_source=DecisionSource.THRESHOLD,
                message=f"Similarity score {score} < {review_thresh} (NO_MATCH threshold)"
            )
            return DecisionResult(decision=DecisionType.NO_MATCH, explanation=expl)
