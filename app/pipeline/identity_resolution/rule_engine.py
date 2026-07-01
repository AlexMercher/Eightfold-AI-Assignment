import yaml
from pathlib import Path
from typing import Dict, Any, List
from .models import EvidenceBundle, RuleResult, DecisionType, RuleExplanation

class RuleEngine:
    def __init__(self, config_path: str = "config/identity_resolution/rules.yaml"):
        self.rules: List[Dict[str, Any]] = []
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.rules = data.get("rules", [])
        
    def evaluate(self, evidence: EvidenceBundle) -> RuleResult:
        for rule in self.rules:
            rule_id = rule.get("id", "unknown")
            condition = rule.get("condition", "AND").upper()
            required = rule.get("required_comparators", [])
            terminating = rule.get("terminating", False)
            decision_str = rule.get("decision")
            
            decision_type = DecisionType(decision_str) if decision_str else None
            
            if not required:
                continue
                
            matched = []
            failed = []
            
            for comp in required:
                res = evidence.comparison_results.get(comp)
                if res and res.matched:
                    matched.append(comp)
                else:
                    failed.append(comp)
                    
            if condition == "AND" and len(matched) == len(required):
                expl = RuleExplanation(
                    rule_id=rule_id,
                    outcome="SATISFIED",
                    supporting_comparators=matched,
                    message=f"Rule {rule_id} triggered via strict AND match on {matched}."
                )
                return RuleResult(
                    triggered=True,
                    rule_id=rule_id,
                    terminating=terminating,
                    decision=decision_type,
                    explanation=expl
                )
            elif condition == "OR" and len(matched) > 0:
                expl = RuleExplanation(
                    rule_id=rule_id,
                    outcome="SATISFIED",
                    supporting_comparators=matched,
                    message=f"Rule {rule_id} triggered via OR match on {matched}."
                )
                return RuleResult(
                    triggered=True,
                    rule_id=rule_id,
                    terminating=terminating,
                    decision=decision_type,
                    explanation=expl
                )
                
        # No rule triggered
        return RuleResult(
            triggered=False,
            rule_id="",
            terminating=False,
            decision=None,
            explanation=None
        )
