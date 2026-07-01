import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.canonical import Candidate
from .comparators.registry import ComparatorRegistry

class EligibilityResult(BaseModel):
    eligible: bool
    matched_rule_id: str
    satisfied_comparators: List[str]
    rejected_comparators: List[str]

class EligibilityEngine:
    def __init__(self, comparator_registry: ComparatorRegistry, 
                 config_path: str = "config/comparison/eligibility.yaml"):
        self.registry = comparator_registry
        self.rules = []
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            
        self.rules = data.get("rules", [])
        
    def _evaluate_rule(self, rule: Dict[str, Any], candidate_a: Candidate, candidate_b: Candidate) -> EligibilityResult:
        rule_id = rule.get("id", "unknown_rule")
        condition = rule.get("condition", "AND").upper()
        comparators = rule.get("comparators", [])
        
        satisfied = []
        rejected = []
        
        if not comparators:
            return EligibilityResult(eligible=False, matched_rule_id=rule_id, satisfied_comparators=[], rejected_comparators=[])
            
        for comp_name in comparators:
            try:
                comparator = self.registry.get(comp_name)
                result = comparator.matches(candidate_a, candidate_b)
                if result.matched:
                    satisfied.append(comp_name)
                    # Short-circuit OR
                    if condition == "OR":
                        return EligibilityResult(eligible=True, matched_rule_id=rule_id, 
                                                 satisfied_comparators=satisfied, rejected_comparators=rejected)
                else:
                    rejected.append(comp_name)
                    # Short-circuit AND
                    if condition == "AND":
                        return EligibilityResult(eligible=False, matched_rule_id=rule_id, 
                                                 satisfied_comparators=satisfied, rejected_comparators=rejected)
            except KeyError:
                # Missing comparator acts as failure for that clause
                rejected.append(comp_name)
                if condition == "AND":
                    return EligibilityResult(eligible=False, matched_rule_id=rule_id, 
                                             satisfied_comparators=satisfied, rejected_comparators=rejected)
                                             
        if condition == "AND":
            # If it didn't short-circuit, all matched
            return EligibilityResult(eligible=True, matched_rule_id=rule_id, 
                                     satisfied_comparators=satisfied, rejected_comparators=rejected)
        else:
            # If it didn't short-circuit in OR, none matched
            return EligibilityResult(eligible=False, matched_rule_id=rule_id, 
                                     satisfied_comparators=satisfied, rejected_comparators=rejected)
                                     
    def is_eligible(self, candidate_a: Candidate, candidate_b: Candidate) -> EligibilityResult:
        """
        Evaluates rules sequentially. Returns the first eligible result,
        or a default failure result if no rule makes the pair eligible.
        """
        for rule in self.rules:
            result = self._evaluate_rule(rule, candidate_a, candidate_b)
            if result.eligible:
                return result
                
        return EligibilityResult(
            eligible=False,
            matched_rule_id="",
            satisfied_comparators=[],
            rejected_comparators=[]
        )
