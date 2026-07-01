from typing import List, Tuple
from app.models.canonical import Candidate
from app.pipeline.identity_resolution.models import IdentityResolutionResult
from .models import ValidatedCluster, ClusterStatus

class ClusterValidator:
    def validate(self, candidates: List[Candidate], edges: List[IdentityResolutionResult]) -> ValidatedCluster:
        """
        Validates the component for transitively induced contradictions.
        NEVER mutates graph topology. Only annotates.
        """
        contradictions = []
        status = ClusterStatus.VALID
        
        # Deterministic check: Contradictory primary contact info
        # If any two candidates in the cluster have NON-EMPTY completely disjoint emails or phones, 
        # it is a strong indication of a transitive graph contradiction (A=B, B=C, but A != C).
        
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                c1 = candidates[i]
                c2 = candidates[j]
                
                # Check disjoint emails
                if c1.contact_info and c1.contact_info.emails and c2.contact_info and c2.contact_info.emails:
                    e1 = {e.lower() for e in c1.contact_info.emails}
                    e2 = {e.lower() for e in c2.contact_info.emails}
                    if not e1.intersection(e2):
                        contradictions.append(f"Disjoint emails between {c1.candidate_id} and {c2.candidate_id}")
                        status = ClusterStatus.INVALID
                        
                # Check disjoint phones
                if c1.contact_info and c1.contact_info.phone_numbers and c2.contact_info and c2.contact_info.phone_numbers:
                    p1 = {p for p in c1.contact_info.phone_numbers}
                    p2 = {p for p in c2.contact_info.phone_numbers}
                    if not p1.intersection(p2):
                        contradictions.append(f"Disjoint phones between {c1.candidate_id} and {c2.candidate_id}")
                        status = ClusterStatus.INVALID
            
        return ValidatedCluster(
            candidates=candidates,
            edges=edges,
            status=status,
            contradictions=contradictions
        )
