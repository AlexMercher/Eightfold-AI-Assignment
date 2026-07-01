import yaml
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from app.models.canonical import Candidate
from .base import CandidatePair
from .registry import BlockingRegistry
from .email import EmailBlockingStrategy
from .phone import PhoneBlockingStrategy
from .github import GithubBlockingStrategy
from .linkedin import LinkedinBlockingStrategy
from .company_city import CompanyCityBlockingStrategy
from .name_company import NameCompanyBlockingStrategy
from .name_university import NameUniversityBlockingStrategy

class BlockingEngine:
    def __init__(self, config_path: str = "config/comparison/blocking.yaml"):
        self.registry = BlockingRegistry()
        self.active_strategies = []
        self._register_default_strategies()
        self._load_config(config_path)
        
    def _register_default_strategies(self):
        self.registry.register("email", EmailBlockingStrategy("email"))
        self.registry.register("phone", PhoneBlockingStrategy("phone"))
        self.registry.register("github", GithubBlockingStrategy("github"))
        self.registry.register("linkedin", LinkedinBlockingStrategy("linkedin"))
        self.registry.register("company_city", CompanyCityBlockingStrategy("company_city"))
        self.registry.register("name_company", NameCompanyBlockingStrategy("name_company"))
        self.registry.register("name_university", NameUniversityBlockingStrategy("name_university"))
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            
        strategy_names = data.get("strategies", [])
        for name in strategy_names:
            try:
                self.active_strategies.append(self.registry.get(name))
            except KeyError:
                pass # Graceful fallback for missing config strategy
                
    def block(self, candidates: List[Candidate]) -> Set[CandidatePair]:
        """
        Groups candidates by blocking keys and returns unique candidate pairs.
        Uses O(n) inverted index to avoid O(n^2) comparisons.
        """
        # Map: key -> set of candidate IDs
        inverted_index: Dict[str, Set[str]] = defaultdict(set)
        
        # O(n) pass: generate keys and populate inverted index
        for candidate in candidates:
            for strategy in self.active_strategies:
                keys = strategy.generate_keys(candidate)
                for key in keys:
                    inverted_index[key].add(candidate.candidate_id)
                    
        # Extract pairs from buckets
        pairs: Dict[tuple, List[str]] = {}
        
        for key, candidate_ids in inverted_index.items():
            ids_list = list(candidate_ids)
            # Only generate pairs within buckets that have at least 2 candidates
            if len(ids_list) > 1:
                for i in range(len(ids_list)):
                    for j in range(i + 1, len(ids_list)):
                        # Use sorted tuple to ensure order independence and avoid object churn
                        a, b = sorted([ids_list[i], ids_list[j]])
                        pair_tuple = (a, b)
                        
                        if pair_tuple not in pairs:
                            pairs[pair_tuple] = []
                        pairs[pair_tuple].append(key)
                        
        # Finalize CandidatePair objects with provenance
        final_pool = set()
        for (a, b), keys in pairs.items():
            pair = CandidatePair(
                candidate_a_id=a,
                candidate_b_id=b,
                blocking_keys_that_generated_this_pair=keys
            )
            final_pool.add(pair)
            
        return final_pool
