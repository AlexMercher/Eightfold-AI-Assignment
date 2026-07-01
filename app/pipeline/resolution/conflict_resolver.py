import yaml
from pathlib import Path
from typing import List, Any, Dict
from .models import ConflictResult

class ConflictResolver:
    def __init__(self, config_path: str = "config/resolution/conflict.yaml"):
        self.source_priorities: List[str] = []
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.source_priorities = data.get("source_priorities", [])
        
    def resolve_scalar(self, values: List[Any], sources: List[str] = None) -> ConflictResult:
        """
        Deterministically picks a winning value from a list of conflicting scalars.
        Strategy:
        1. Exclude None/Empty
        2. Frequency (most common)
        3. Configured Source Priority (if provided)
        4. Alphabetical sort
        """
        # Pair values with their sources (if available)
        valid_pairs = []
        for i, v in enumerate(values):
            if v is not None and str(v).strip() != "":
                s = sources[i] if sources and i < len(sources) else "unknown"
                valid_pairs.append((v, s))
                
        if not valid_pairs:
            return ConflictResult(winning_value=None, rejected_values=[], reason="All values empty")
            
        cleaned_values = [p[0] for p in valid_pairs]
        if len(set(cleaned_values)) == 1:
            return ConflictResult(winning_value=cleaned_values[0], rejected_values=[], reason="Unanimous agreement")
            
        # 2. Frequency
        freq: Dict[Any, int] = {}
        for v in cleaned_values:
            freq[v] = freq.get(v, 0) + 1
            
        max_freq = max(freq.values())
        most_frequent = [k for k, v in freq.items() if v == max_freq]
        
        if len(most_frequent) == 1:
            winner = most_frequent[0]
            rejected = [v for v in set(cleaned_values) if v != winner]
            return ConflictResult(winning_value=winner, rejected_values=rejected, reason="Highest frequency")
            
        # 3. Configured Source Priority
        # Find the best priority rank among the tied values
        # Lower index in self.source_priorities = better priority
        best_priority = float('inf')
        priority_winner = None
        
        for val in most_frequent:
            # Find all sources that provided this tied value
            val_sources = [s for v, s in valid_pairs if v == val]
            for src in val_sources:
                if src in self.source_priorities:
                    rank = self.source_priorities.index(src)
                    if rank < best_priority:
                        best_priority = rank
                        priority_winner = val
                        
        if priority_winner is not None:
            rejected = [v for v in set(cleaned_values) if v != priority_winner]
            return ConflictResult(winning_value=priority_winner, rejected_values=rejected, reason="Source priority tie-breaker")
            
        # 4. Alphabetical tie-breaker
        winner = sorted(most_frequent, key=lambda x: str(x))[0]
        rejected = [v for v in set(cleaned_values) if v != winner]
        return ConflictResult(winning_value=winner, rejected_values=rejected, reason="Alphabetical tie-breaker")
